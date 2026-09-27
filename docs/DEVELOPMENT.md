# Development Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+ with uv
- Node.js 18+ with pnpm
- Git

## Initial Setup

```bash
# 1. Clone repository
git clone <repo>
cd AI-Powered_Digital_Asset_Manager

# 2. Configure environment
cp .env.example .env
# Edit .env as needed

# 3. Start infrastructure
make infra-up

# 4. Run migrations
make migrate

# 5. Install dependencies
make install
```

## Running Locally

### Backend Only
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Only
```bash
cd frontend
pnpm dev
```

### Both (Recommended)
```bash
make dev
```

## Code Quality

### Linting
```bash
make lint
# Or individually:
cd backend && uv run ruff check .
cd frontend && pnpm lint
```

### Formatting
```bash
make format
# Or individually:
cd backend && uv run ruff format .
cd frontend && pnpm format
```

### Type Checking
```bash
cd backend && uv run mypy app/
cd frontend && pnpm tsc --noEmit
```

## Testing

### Backend Tests
```bash
cd backend
uv run pytest -v              # All tests
uv run pytest tests/test_scanner.py -v  # Specific test
uv run pytest --cov=app       # With coverage
```

### Frontend Tests
```bash
cd frontend
pnpm test                     # All tests
pnpm test --watch             # Watch mode
```

## Database Operations

### Create Migration
```bash
cd backend
uv run alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
make migrate
# Or:
cd backend && uv run alembic upgrade head
```

### Rollback Migration
```bash
cd backend && uv run alembic downgrade -1
```

### Reset Database
```bash
docker compose down -v
make infra-up
make migrate
```

## Adding New AI Providers

### 1. Implement Interface
Create new provider in `app/ai/<category>/`:
```python
from app.ai.base import EmbeddingProvider

class MyEmbeddingProvider(EmbeddingProvider):
    async def embed_text(self, texts: list[str]) -> list[list[float]]: ...
    # ... implement all methods
```

### 2. Register in Factory
Add to `app/ai/factory.py`:
```python
if provider == "my_provider":
    return MyEmbeddingProvider()
```

### 3. Add Configuration
Add env vars to `.env.example` and `app/core/config.py`

## Adding New Modality

### 1. Create Processor
```python
# app/processors/audio/processor.py
class AudioProcessor(BaseProcessor):
    async def process(self, asset: Asset, job: ProcessingJob): ...
```

### 2. Register in Orchestrator
```python
orchestrator.register_processors(
    audio_processor=AudioProcessor(...).process,
    # ...
)
```

### 3. Add Database Models
Add tables for audio analysis, segments, etc.

### 4. Update Scanner
Add audio extensions to supported types.

### 5. Update Search
Add audio collection to vector store and retrieval.

## Debugging Tips

### Backend Logs
```bash
# Structured logs in console
# Set APP_LOG_LEVEL=DEBUG for verbose output
```

### Database Inspection
```bash
docker exec -it dam-postgres psql -U dam -d dam
```

### Qdrant Inspection
```bash
curl http://localhost:6333/collections
curl http://localhost:6333/collections/dam_assets_image/points
```

### Profile Ingestion
```bash
python scripts/benchmark_ingestion.py
```

## Common Issues

### Port Conflicts
- Backend: 8000
- Frontend: 3000
- PostgreSQL: 5432
- Qdrant: 6333/6334
- Ollama: 11434

Change in `.env` and `docker-compose.yml` if needed.

### GPU Not Detected
```bash
# Check CUDA
nvidia-smi
# Check PyTorch
python -c "import torch; print(torch.cuda.is_available())"
```

### Model Download Issues
```bash
# Pre-download models
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32')"
docker exec dam-ollama ollama pull llava:7b
```

## IDE Setup

### VS Code Extensions
- Python (Microsoft)
- Pylance
- Ruff
- TypeScript/ESLint
- Tailwind CSS IntelliSense

### Recommended Settings
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": "explicit"
  }
}
```