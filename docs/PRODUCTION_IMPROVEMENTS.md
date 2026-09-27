# Production Improvements Roadmap

## Current State: Local Modular Monolith

The current implementation is a **local-first modular monolith** suitable for:
- Development and testing
- Single-user deployments
- Datasets up to ~50GB
- CPU/GPU inference on single machine

## Scaling Dimensions

| Dimension | Current | Target (100GB) | Target (1TB+) |
|-----------|---------|----------------|---------------|
| Storage | Local FS | MinIO/S3 | S3 + CDN |
| Database | Single PG | PG + Read Replicas | Sharded PG / CockroachDB |
| Vector DB | Single Qdrant | Qdrant Cluster | Managed (Pinecone/Weaviate) |
| Workers | In-process | Celery + Redis | K8s Jobs / Ray |
| Inference | Local Ollama | GPU Inference Server | Triton / vLLM |
| API | Single FastAPI | API Gateway + LB | Multi-region |
| Auth | None | OAuth2/OIDC | Enterprise SSO |

## Phase 1: Infrastructure Hardening (100GB)

### Object Storage
- Replace local `MEDIA_ROOT` with S3/MinIO
- Presigned URLs for secure asset access
- Lifecycle policies for temp files

```python
# New storage abstraction
class StorageProvider(Protocol):
    async def upload(self, key: str, data: bytes) -> str: ...
    async def download(self, key: str) -> bytes: ...
    async def generate_presigned_url(self, key: str, expiry: int) -> str: ...
```

### Job Queue
- Replace in-process orchestrator with Celery + Redis
- Persistent task queue with retries
- Horizontal worker scaling

```python
# Celery task
@celery.task(bind=True, max_retries=3)
def process_asset(self, asset_id: str):
    # Processing logic
```

### Database
- Connection pooling (PgBouncer)
- Read replicas for search queries
- Partitioned tables by date/modality

### Vector DB
- Qdrant cluster mode
- Sharding by modality
- Quantization for memory efficiency

## Phase 2: Inference Scaling (500GB)

### GPU Inference Server
- Replace local Ollama with dedicated inference servers
- NVIDIA Triton / vLLM for LLMs
- Batched inference for embeddings
- Model versioning and A/B testing

```yaml
# docker-compose.inference.yml
services:
  embedding-server:
    image: nvcr.io/nvidia/tritonserver
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Caching Layer
- Redis cache for frequent queries
- Embedding cache by content_hash + model_version
- Query result cache with TTL

### Async Processing
- Webhook callbacks for long-running jobs
- Server-Sent Events for real-time progress
- Priority queues for urgent reprocessing

## Phase 3: Enterprise Features (1TB+)

### Multi-tenancy
- Tenant isolation at database level
- Per-tenant vector collections
- Resource quotas and billing

### Access Control
- RBAC (Admin, Editor, Viewer)
- Asset-level permissions
- Audit logging

### Observability
- OpenTelemetry tracing
- Prometheus metrics + Grafana dashboards
- Structured logging to ELK/Loki
- Alerting on failure rates, latency, queue depth

### Disaster Recovery
- Automated backups (PG, Qdrant, S3)
- Cross-region replication
- Point-in-time recovery
- Chaos engineering tests

## Architecture Evolution

```
CURRENT (Local)          PHASE 1 (100GB)          PHASE 2 (500GB)         PHASE 3 (1TB+)
┌─────────────┐          ┌──────────────────┐     ┌──────────────────┐    ┌──────────────────┐
│  FastAPI    │          │  FastAPI +       │     │  API Gateway     │    │  API Gateway     │
│  (single)   │ ──────▶  │  Celery Workers  │ ──▶ │  + Load Balancer │ ─▶ │  + Rate Limit    │
└─────────────┘          └──────────────────┘     └──────────────────┘    └──────────────────┘
       │                        │                        │                       │
       ▼                        ▼                        ▼                       ▼
┌─────────────┐          ┌──────────────────┐     ┌──────────────────┐    ┌──────────────────┐
│ PostgreSQL  │          │  PG + Replicas   │     │  Sharded PG      │    │  CockroachDB/    │
│ (single)    │ ──────▶  │  + PgBouncer     │ ──▶ │  + Partitioning  │ ─▶ │  Distributed SQL │
└─────────────┘          └──────────────────┘     └──────────────────┘    └──────────────────┘
       │                        │                        │                       │
       ▼                        ▼                        ▼                       ▼
┌─────────────┐          ┌──────────────────┐     ┌──────────────────┐    ┌──────────────────┐
│ Qdrant      │          │  Qdrant Cluster  │     │  Qdrant Cluster  │    │  Managed Vector  │
│ (single)    │ ──────▶  │  (3+ nodes)      │ ──▶ │  + Quantization  │ ─▶ │  DB (Pinecone)   │
└─────────────┘          └──────────────────┘     └──────────────────┘    └──────────────────┘
       │                        │                        │                       │
       ▼                        ▼                        ▼                       ▼
┌─────────────┐          ┌──────────────────┐     ┌──────────────────┐    ┌──────────────────┐
│ Local FS    │          │  MinIO/S3        │     │  S3 + CDN        │    │  Multi-region    │
│             │ ──────▶  │  + Presigned     │ ──▶ │  + Edge Cache    │ ─▶ │  S3 + Global CDN │
└─────────────┘          └──────────────────┘     └──────────────────┘    └──────────────────┘
       │                        │                        │                       │
       ▼                        ▼                        ▼                       ▼
┌─────────────┐          ┌──────────────────┐     ┌──────────────────┐    ┌──────────────────┐
│ Ollama      │          │  Ollama (GPU)    │     │  Triton/vLLM     │    │  Model Registry  │
│ (CPU/GPU)   │ ──────▶  │  + Batching      │ ──▶ │  + Auto-scaling  │ ─▶ │  + A/B Testing   │
└─────────────┘          └──────────────────┘     └──────────────────┘    └──────────────────┘
```

## Migration Strategy

### Database
1. Enable logical replication
2. Sync to new cluster
3. Switch traffic with zero-downtime

### Vector DB
1. Dual-write during transition
2. Backfill missing vectors
3. Switch read traffic

### Storage
1. Sync existing files to S3
2. Update asset paths in DB
3. Switch to presigned URLs

### Workers
1. Run both orchestrators in parallel
2. Drain in-process queue
3. Switch to Celery

## Cost Optimization

| Component | Optimization |
|-----------|--------------|
| Vector DB | Binary quantization, HNSW ef tuning |
| Inference | Batch requests, model distillation |
| Storage | Tiered storage (hot/warm/cold) |
| Compute | Spot instances for batch jobs |
| Network | CDN for asset delivery |

## Security Hardening

- TLS everywhere (mTLS for service-to-service)
- Secrets management (Vault/AWS Secrets Manager)
- Network policies (K8s NetworkPolicy)
- Regular security scanning (Trivy, Snyk)
- Penetration testing

## Compliance

- GDPR: Right to deletion, data portability
- SOC2: Audit logging, access controls
- HIPAA: Encryption at rest/in transit, BAA

## Team Structure

| Phase | Team Size | Roles |
|-------|-----------|-------|
| Current | 1-2 | Full-stack Engineer |
| 100GB | 3-5 | Backend, DevOps, ML Engineer |
| 500GB | 8-12 | Platform, ML Infra, Frontend, QA |
| 1TB+ | 15+ | Multiple squads + SRE |

## Decision Matrix

| Decision | Current | Future | Trigger |
|----------|---------|--------|---------|
| Job Queue | In-process | Celery | >100 concurrent jobs |
| Vector DB | Single Qdrant | Cluster | >10M vectors |
| Inference | Local | Triton | >50 req/s |
| Storage | Local FS | S3 | >500GB assets |
| Auth | None | OIDC | Multi-user |
| Multi-region | No | Yes | Global users |

## Implementation Priority

1. **Object Storage** - Enables all other scaling
2. **Job Queue** - Enables horizontal processing
3. **GPU Inference** - Reduces indexing time 10x
4. **Vector DB Cluster** - Handles vector growth
5. **Caching** - Improves search latency
6. **Auth/Multi-tenancy** - Business requirement
7. **Observability** - Operational requirement