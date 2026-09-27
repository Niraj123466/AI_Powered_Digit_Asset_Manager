# AI-Powered Digital Asset Management System

A local-first, modular Digital Asset Management (DAM) system that indexes images, videos, and PDF documents using multimodal AI understanding for semantic search.

## Features

- **Multimodal Ingestion**: Images, videos, and PDFs with content understanding
- **Semantic Search**: Natural language queries across all modalities
- **Hybrid Retrieval**: Vector similarity + lexical search + metadata filtering
- **Incremental Indexing**: Only processes new/changed files
- **Duplicate Detection**: SHA-256 based exact duplicate handling
- **Failure Resilience**: Per-file failure isolation with retry logic
- **Local-First**: Runs entirely on your machine (Docker for infra)
- **Modular Architecture**: Swappable AI providers, vector stores, databases

## Architecture

```mermaid
graph TB
    FS[Filesystem\nMEDIA_ROOT] --> Scanner
    Scanner --> Orchestrator[Ingestion Orchestrator]
    Orchestrator --> DupDetector[Duplicate Detector]
    DupDetector --> ImgProc[Image Processor]
    DupDetector --> VidProc[Video Processor]
    DupDetector --> PDFProc[PDF Processor]
    
    ImgProc --> Vision[Vision Provider]
    ImgProc --> OCR[OCR Provider]
    ImgProc --> Embeddings[Embedding Provider]
    
    VidProc --> Vision
    VidProc --> Transcription[Transcription Provider]
    VidProc --> Embeddings
    
    PDFProc --> OCR
    VidProc --> Embeddings
    PDFProc --> LLM[LLM Provider]
    
    Embeddings --> Qdrant[(Qdrant Vector DB)]
    Vision --> PostgreSQL[(PostgreSQL)]
    OCR --> PostgreSQL
    Transcription --> PostgreSQL
    LLM --> PostgreSQL
    
    SearchAPI[FastAPI Search] --> Qdrant
    SearchAPI --> PostgreSQL
    SearchAPI --> Reranker[Optional Reranker]
    
    Frontend[Next.js UI] --> SearchAPI
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend API | FastAPI + Pydantic |
| Database | PostgreSQL (with pgvector) |
| Vector Search | Qdrant |
| Embeddings | CLIP (sentence-transformers) |
| Vision | LLaVA via Ollama |
| OCR | Tesseract |
| Transcription | faster-whisper |
| LLM | Llama 3.1 via Ollama |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Orchestration | Docker Compose |

## Requirements

- **Docker & Docker Compose** (for PostgreSQL, Qdrant)
- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- **uv** (Python package manager) - `pip install uv`
- **pnpm** (Node package manager) - `npm install -g pnpm`
- **Optional**: NVIDIA GPU with CUDA for faster AI inference
- **Optional**: Ollama for local LLM/Vision models

## Quick Start

### 1. Clone and Configure

```bash
git clone <repo>
cd AI-Powered_Digital_Asset_Manager

# Copy environment template
cp .env.example .env

# Edit .env to set MEDIA_ROOT and other settings
```

### 2. Start Infrastructure

```bash
make infra-up
# or: docker compose up -d
```

This starts PostgreSQL and Qdrant.

### 3. Initialize Database

```bash
make migrate
# or: cd backend && uv run alembic upgrade head
```

### 4. Install Dependencies

```bash
make install
# or manually:
cd backend && uv pip install -e .[dev]
cd frontend && pnpm install
```

### 5. Add Media Files

Place your media files under `data/media/` (or your configured `MEDIA_ROOT`):

```
data/media/
├── images/
│   ├── photo1.jpg
│   └── ...
├── videos/
│   ├── clip1.mp4
│   └── ...
└── documents/
    ├── brochure1.pdf
    └── ...
```

### 6. Start Development Servers

```bash
make dev
# This starts both backend (port 8000) and frontend (port 3000)
```

### 7. Access the UI

Open http://localhost:3000 in your browser.

- **Dashboard**: Overview of indexed assets
- **Search**: Natural language search across all assets
- **Indexing**: Monitor and control indexing process

### 8. Run Indexing

Click "Start Indexing" on the Indexing page, or via API:

```bash
curl -X POST http://localhost:8000/api/index/start
```

## Usage Examples

### Search Queries

```
"modern living room interior"
"construction workers on site"
"customer testimonial video"
"residential project brochure"
"apartment floor plan"
"luxury bedroom design"
"building construction activity"
"office workspace"
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "modern living room", "limit": 10}'

# Get stats
curl http://localhost:8000/api/stats

# Indexing status
curl http://localhost:8000/api/index/status

# List assets
curl http://localhost:8000/api/assets?modality=image&limit=20
```

## Configuration

Key environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `MEDIA_ROOT` | Root directory for media files | `./data/media` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://dam:dam@localhost:5432/dam` |
| `QDRANT_URL` | Qdrant connection URL | `http://localhost:6333` |
| `EMBEDDING_MODEL` | CLIP model name | `clip-ViT-B-32` |
| `VISION_MODEL` | Ollama vision model | `llava:7b` |
| `ENABLE_OCR` | Enable OCR for images/PDFs | `true` |
| `ENABLE_VIDEO_TRANSCRIPTION` | Enable audio transcription | `false` |
| `INGESTION_WORKERS` | Parallel processing workers | `2` |
| `VIDEO_MAX_FRAMES` | Max frames per video | `64` |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Config, logging, exceptions
│   │   ├── db/            # SQLAlchemy models, repositories
│   │   ├── domain/        # Business logic (indexing, search)
│   │   ├── processors/    # Modality processors (image, video, pdf)
│   │   ├── ai/            # AI provider abstractions
│   │   └── search/        # Search pipeline
│   ├── tests/             # Unit & integration tests
│   └── migrations/        # Alembic migrations
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── components/        # React components
│   └── lib/               # API client, types, utils
├── data/
│   └── media/             # Your media files (not in git)
├── docs/                  # Documentation
├── evaluation/            # Search evaluation queries
├── scripts/               # Utility scripts
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture and components
- [Data Flow](docs/DATA_FLOW.md) - Detailed data flow diagrams
- [Decisions](docs/DECISIONS.md) - Technical decision records
- [Dataset](docs/DATASET.md) - Dataset requirements and sources
- [Video Processing](docs/VIDEO_PROCESSING.md) - Video pipeline details
- [Failure Handling](docs/FAILURE_HANDLING.md) - Error handling strategies
- [Evaluation](docs/EVALUATION.md) - Search evaluation methodology
- [Production Improvements](docs/PRODUCTION_IMPROVEMENTS.md) - Scaling roadmap

## Testing

```bash
# Backend tests
cd backend && uv run pytest -v

# Frontend tests
cd frontend && pnpm test

# All tests
make test
```

## Evaluation

```bash
# Run search evaluation
python scripts/evaluate_search.py

# Benchmark ingestion
python scripts/benchmark_ingestion.py
```

## Troubleshooting

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker compose ps
docker compose logs postgres
```

### Qdrant Connection Failed
```bash
docker compose logs qdrant
```

### Out of Memory During Indexing
- Reduce `INGESTION_WORKERS` in `.env`
- Reduce `VIDEO_MAX_FRAMES`
- Disable `ENABLE_VIDEO_TRANSCRIPTION`
- Ensure swap is configured

### Vision/Transcription Models Not Found
```bash
# Pull Ollama models
docker exec -it dam-ollama ollama pull llava:7b
docker exec -it dam-ollama ollama pull llama3.1:8b
```

## Limitations

- Local-only deployment (no distributed clustering)
- Single-user (no authentication/authorization)
- CPU inference by default (GPU optional via CUDA)
- English-centric models
- No real-time collaboration features

## Production Improvements

See [PRODUCTION_IMPROVEMENTS.md](docs/PRODUCTION_IMPROVEMENTS.md) for:
- Object storage (S3/MinIO)
- Distributed workers (Celery/Kubernetes)
- GPU inference servers
- Cloud vector databases
- Authentication & multi-tenancy
- CDN for asset delivery

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run linting: `make lint`
5. Submit a PR

## Acknowledgments

- [CLIP](https://github.com/openai/CLIP) for multimodal embeddings
- [LLaVA](https://github.com/haotian-liu/LLaVA) for vision-language understanding
- [Qdrant](https://qdrant.tech/) for vector search
- [Ollama](https://ollama.ai/) for local LLM hosting
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Next.js](https://nextjs.org/) for the frontend framework