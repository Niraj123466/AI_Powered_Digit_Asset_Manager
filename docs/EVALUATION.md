# Search Evaluation Documentation

## Overview

This document describes the search evaluation methodology, metrics, and tooling for the DAM system.

## Evaluation Framework

### Queries File (`evaluation/queries.json`)

```json
[
  {
    "id": "q1",
    "query": "modern living room interior",
    "modality": "image",
    "filters": {}
  },
  {
    "id": "q2",
    "query": "construction workers on site",
    "modality": "video",
    "filters": {}
  }
]
```

### Relevance Judgments (`evaluation/relevance.json`)

```json
{
  "q1": ["asset-uuid-1", "asset-uuid-2", "asset-uuid-3"],
  "q2": ["asset-uuid-4", "asset-uuid-5"]
}
```

Asset IDs must match actual indexed assets.

## Metrics

### Precision@K
Fraction of top-K results that are relevant:
```
Precision@K = |Relevant ∩ TopK| / K
```

### Recall@K
Fraction of relevant items retrieved in top-K:
```
Recall@K = |Relevant ∩ TopK| / |Relevant|
```

### Mean Average Precision (MAP)
Average precision across all queries.

### Latency
Query response time in milliseconds.

## Running Evaluation

```bash
# Ensure system is indexed
make index

# Run evaluation
python scripts/evaluate_search.py
```

Output:
- Per-query metrics (P@5, P@10, R@5, R@10)
- Average metrics across all queries
- Detailed results saved to `evaluation/results.json`

## Creating Evaluation Data

### 1. Index a representative dataset
```bash
# Add your test media to data/media/
make index
```

### 2. Run sample searches manually
Use the UI or API to find relevant assets for your test queries.

### 3. Record asset IDs
Note the `asset_id` values from search results.

### 4. Create evaluation files
```bash
mkdir -p evaluation
# Create queries.json and relevance.json
```

### 5. Run evaluation
```bash
python scripts/evaluate_search.py
```

## Interpreting Results

| Metric | Good | Needs Improvement |
|--------|------|-------------------|
| P@5 | > 0.7 | < 0.4 |
| P@10 | > 0.5 | < 0.3 |
| R@5 | > 0.5 | < 0.2 |
| Latency | < 500ms | > 2000ms |

## Failure Analysis

Common failure modes:

1. **Modality mismatch**: Query expects video, returns images
   - Fix: Improve modality detection keywords

2. **Semantic gap**: "modern" doesn't match "contemporary"
   - Fix: Better embedding model or query expansion

3. **Missing content**: OCR didn't capture text in image
   - Fix: Enable/improve OCR, check image quality

4. **Timestamp accuracy**: Video match at wrong time
   - Fix: Increase frame sampling rate

## Continuous Evaluation

Integrate into CI/CD:
```yaml
# GitHub Actions example
- name: Run Search Evaluation
  run: |
    make infra-up
    make migrate
    make index
    python scripts/evaluate_search.py
```

Track metrics over time to detect regressions.