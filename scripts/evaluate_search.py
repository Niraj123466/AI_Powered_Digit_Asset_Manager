#!/usr/bin/env python
"""Search evaluation script."""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db, async_session_factory
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.search.service import SearchService
from app.db.repositories import AssetRepository
from app.db.models import Modality

logger = get_logger(__name__)


async def load_evaluation_data(eval_dir: Path) -> tuple:
    """Load evaluation queries and relevance judgments."""
    queries_file = eval_dir / "queries.json"
    relevance_file = eval_dir / "relevance.json"
    
    if not queries_file.exists():
        raise FileNotFoundError(f"Queries file not found: {queries_file}")
    if not relevance_file.exists():
        raise FileNotFoundError(f"Relevance file not found: {relevance_file}")
    
    with open(queries_file) as f:
        queries = json.load(f)
    
    with open(relevance_file) as f:
        relevance = json.load(f)
    
    return queries, relevance


async def evaluate_query(
    search_service: SearchService,
    query: Dict[str, Any],
    relevant_asset_ids: List[str],
    k_values: List[int] = [5, 10],
) -> Dict[str, Any]:
    """Evaluate a single query."""
    query_text = query["query"]
    modality = query.get("modality")
    filters = query.get("filters")
    
    # Run search
    response = await search_service.search(
        query=query_text,
        modality_filter=Modality(modality) if modality else None,
        filters=filters,
        limit=max(k_values),
    )
    
    # Calculate metrics
    returned_ids = [str(r.asset_id) for r in response.results]
    relevant_set = {str(id) for id in relevant_asset_ids}
    
    metrics = {}
    for k in k_values:
        top_k = returned_ids[:k]
        relevant_in_top_k = sum(1 for id in top_k if id in relevant_set)
        precision = relevant_in_top_k / k if k > 0 else 0
        recall = relevant_in_top_k / len(relevant_set) if relevant_set else 0
        metrics[f"precision@{k}"] = precision
        metrics[f"recall@{k}"] = recall
    
    return {
        "query": query_text,
        "modality": modality,
        "returned_ids": returned_ids,
        "relevant_ids": relevant_asset_ids,
        "metrics": metrics,
        "latency_ms": response.latency_ms,
    }


async def main():
    setup_logging()
    
    eval_dir = Path(__file__).parent.parent / "evaluation"
    if not eval_dir.exists():
        print(f"Evaluation directory not found: {eval_dir}")
        print("Create evaluation/queries.json and evaluation/relevance.json")
        return
    
    queries, relevance = await load_evaluation_data(eval_dir)
    
    # Initialize services
    await init_db()
    
    vector_store = QdrantVectorStore()
    await vector_store.initialize()
    
    async with async_session_factory() as session:
        asset_repo = AssetRepository(session)
        search_service = SearchService(vector_store, async_session_factory, asset_repo)
        
        print(f"Evaluating {len(queries)} queries...")
        print("=" * 60)
        
        all_results = []
        total_metrics = {f"precision@{k}": 0.0 for k in [5, 10]}
        total_metrics.update({f"recall@{k}": 0.0 for k in [5, 10]})
        
        for query in queries:
            query_id = query["id"]
            relevant_ids = relevance.get(query_id, [])
            
            if not relevant_ids:
                print(f"Skipping query {query_id}: no relevance judgments")
                continue
            
            result = await evaluate_query(search_service, query, relevant_ids)
            all_results.append(result)
            
            print(f"\nQuery: {result['query']}")
            if result['modality']:
                print(f"Modality filter: {result['modality']}")
            print(f"Relevant assets: {len(result['relevant_ids'])}")
            print(f"Returned assets: {len(result['returned_ids'])}")
            print(f"Latency: {result['latency_ms']}ms")
            
            for k in [5, 10]:
                p = result['metrics'][f'precision@{k}']
                r = result['metrics'][f'recall@{k}']
                print(f"  P@{k}: {p:.3f}, R@{k}: {r:.3f}")
                total_metrics[f'precision@{k}'] += p
                total_metrics[f'recall@{k}'] += r
        
        # Print summary
        n = len(all_results)
        if n > 0:
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            for k in [5, 10]:
                avg_p = total_metrics[f'precision@{k}'] / n
                avg_r = total_metrics[f'recall@{k}'] / n
                print(f"Average P@{k}: {avg_p:.3f}")
                print(f"Average R@{k}: {avg_r:.3f}")
        
        # Save detailed results
        output_file = eval_dir / "results.json"
        with open(output_file, "w") as f:
            json.dump({
                "summary": {k: v/n for k, v in total_metrics.items()} if n > 0 else {},
                "results": all_results,
            }, f, indent=2, default=str)
        print(f"\nDetailed results saved to {output_file}")
    
    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(main())