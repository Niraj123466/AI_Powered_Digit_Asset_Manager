# Technical Decision Records

## 1. Framework: FastAPI
**Decision**: Use FastAPI for the backend API layer.
**Reason**: 
- Native async support for I/O-bound operations (database, vector DB, AI inference)
- Automatic OpenAPI documentation generation
- Pydantic integration for request/response validation
- Strong typing support with Python 3.11+
- Lightweight, no unnecessary abstractions

**Alternatives Considered**:
- Flask: Less async support, manual OpenAPI
- Django: Too heavy, ORM coupling
- Starlette: Lower level, more boilerplate

**Tradeoffs**: 
- Less mature ecosystem than Django
- Requires manual project structure decisions

---

## 2. Database: PostgreSQL
**Decision**: Use PostgreSQL as the primary relational database.
**Reason**:
- Robust ACID guarantees for metadata consistency
- Native JSONB support for flexible metadata
- Full-text search (tsvector) for lexical retrieval
- Mature ecosystem, excellent tooling
- Runs reliably in Docker for local development

**Alternatives Considered**:
- SQLite: Insufficient for concurrent access, no FTS parity
- MySQL: Weaker JSON support, less robust FTS
- MongoDB: No ACID transactions across documents, no native FTS

**Tradeoffs**:
- Requires separate Docker container
- Heavier than SQLite for trivial deployments

---

## 3. Vector Database: Qdrant
**Decision**: Use Qdrant for vector storage and similarity search.
**Reason**:
- Purpose-built for vector search with filtering
- Native payload support for metadata filtering
- Runs locally via Docker
- REST + gRPC APIs
- Good Python client
- Supports HNSW indexing, quantization

**Alternatives Considered**:
- FAISS: Library not service, no persistence, no filtering
- Weaviate: Heavier, GraphQL focus, more resources
- Chroma: Less mature filtering, scaling concerns
- pgvector: Good but less optimized for pure vector workloads

**Tradeoffs**:
- Additional infrastructure component
- Memory usage scales with index size

---

## 4. Storage: Local Filesystem
**Decision**: Assets remain on local filesystem; DB stores paths and metadata.
**Reason**:
- Simple for local development
- No object storage setup required
- Direct file access for preview/processing
- Configurable `MEDIA_ROOT` for portability

**Alternatives Considered**:
- MinIO/S3: Additional infrastructure, overkill for local
- Database BLOBs: Terrible for large files, backup issues

**Tradeoffs**:
- Not horizontally scalable
- Requires careful path validation for security

---

## 5. Embedding Model: CLIP (ViT-B/32) via sentence-transformers
**Decision**: Use CLIP for image/text embeddings initially.
**Reason**:
- Proven multimodal capability
- Runs locally on CPU/GPU
- Available via sentence-transformers (easy integration)
- Good baseline for semantic search
- 512-dim vectors balance quality/size

**Alternatives Considered**:
- SigLIP: Better zero-shot, but less ecosystem tooling
- BLIP-2: Requires more VRAM
- OpenCLIP: More variants, similar performance
- Commercial APIs: Violates local-only principle

**Tradeoffs**:
- 512-dim may limit fine-grained discrimination
- English-centric training data

---

## 6. Vision Model: LLaVA / Moondream via Ollama
**Decision**: Use local vision-language models via Ollama for image description.
**Reason**:
- Runs locally without API keys
- Ollama provides unified model management
- LLaVA-1.5-7B balances quality/speed on consumer GPUs
- Moondream2 as lightweight fallback for CPU-only

**Alternatives Considered**:
- BLIP-2: Captioning only, not VQA
- GPT-4V/Claude: Requires paid API, not local
- CogVLM: Higher VRAM requirements

**Tradeoffs**:
- Slower than pure classification models
- Quality varies with model size
- Requires ~8GB VRAM for 7B models

---

## 7. Video Frame Sampling: Adaptive Interval
**Decision**: Sample frames at configurable intervals with max frame cap.
**Reason**:
- Prevents explosion on long videos (2hr → thousands of frames)
- Short videos: dense sampling (every 2-5s)
- Long videos: bounded representative frames (max 64)
- Configurable via env vars

**Alternatives Considered**:
- Fixed FPS: Doesn't adapt to duration
- Keyframe only: Misses content between keyframes
- Scene detection: Adds complexity, FFmpeg dependency

**Tradeoffs**:
- May miss brief events between samples
- Heuristic, not content-aware

---

## 8. Transcription: Optional (faster-whisper)
**Decision**: Make transcription optional via feature flag.
**Reason**:
- Whisper models require significant CPU/GPU
- Not all deployments have resources
- Visual understanding often sufficient
- Can be enabled when hardware permits

**Alternatives Considered**:
- Whisper.cpp: Good but separate binary
- OpenAI Whisper API: Not local
- Vosk: Lower quality, smaller models

**Tradeoffs**:
- Feature parity depends on hardware
- Search misses audio-only content when disabled

---

## 9. PDF Processing: PyMuPDF + Tesseract OCR
**Decision**: Use PyMuPDF (fitz) for text extraction, Tesseract for OCR fallback.
**Reason**:
- PyMuPDF: Fast, reliable, handles most PDFs
- Tesseract: Mature OCR, runs locally
- Detects scanned pages via text density heuristic
- Page-level chunking preserves location info

**Alternatives Considered**:
- pdfplumber: Slower, similar capability
- Adobe PDF Extract API: Not local
- Marker: Newer, less battle-tested

**Tradeoffs**:
- Tesseract accuracy varies with scan quality
- Complex layouts (tables, columns) challenging

---

## 10. Search: Hybrid (Vector + Lexical + Metadata)
**Decision**: Implement hybrid retrieval with reciprocal rank fusion.
**Reason**:
- Vector: Semantic similarity ("modern living room" ≈ "contemporary interior")
- Lexical: Exact matches ("Project Alpha", model numbers)
- Metadata: Filters (type, date, size, path)
- RRF: Parameter-free fusion, robust

**Alternatives Considered**:
- Pure vector: Misses exact terms
- Pure BM25: Misses semantics
- Weighted sum: Requires tuning weights
- Learned fusion: Needs training data

**Tradeoffs**:
- More complex than single retrieval
- RRF assumes comparable score distributions

---

## 11. Ranking: Configurable Weighted + Optional Reranker
**Decision**: Weighted linear combination with cross-encoder reranker interface.
**Reason**:
- Transparent, explainable scoring
- Weights in config for experimentation
- Reranker pluggable for future quality gains
- Modality boosting for intent-aware results

**Alternatives Considered**:
- Learning to rank: Needs labeled data
- Pure vector score: Ignores other signals
- BM25 only: No semantic understanding

**Tradeoffs**:
- Linear combination is simplistic
- Reranker adds latency

---

## 12. Architecture: Modular Monolith
**Decision**: Single deployable backend with clear internal boundaries.
**Reason**:
- Simpler deployment (one service)
- Clear module boundaries via protocols/interfaces
- No distributed system complexity
- Easy to extract services later if needed
- Matches local development scope

**Alternatives Considered**:
- Microservices: Overhead unjustified for local tool
- Serverless: Cold starts, vendor lock-in
- Monolith without boundaries: Becomes unmaintainable

**Tradeoffs**:
- All components share process resources
- Scaling requires scaling entire app

---

## 13. Message Queue: None (Direct Orchestration)
**Decision**: No Kafka/RabbitMQ; use in-process job queue with persistence.
**Reason**:
- Local development: extra infrastructure burden
- SQLite/PostgreSQL-based job table sufficient for throughput
- Persistent state enables resumability
- Can add queue later if needed

**Alternatives Considered**:
- Celery + Redis: Extra infrastructure
- Dramatiq: Still needs broker
- Kafka: Massive overkill

**Tradeoffs**:
- No horizontal worker scaling (yet)
- Worker crash loses in-flight job (mitigated by state machine)

---

## 14. Frontend: Next.js 14 + TypeScript + Tailwind + shadcn/ui
**Decision**: Modern React stack with component library.
**Reason**:
- App Router for nested layouts
- TypeScript for type-safe API contracts
- Tailwind for rapid, consistent styling
- shadcn/ui: Accessible, customizable, copy-paste components
- Good developer experience

**Alternatives Considered**:
- Vite + React: No SSR, manual routing
- Remix: Smaller ecosystem
- SvelteKit: Less familiar team knowledge

**Tradeoffs**:
- Next.js complexity for simple UI
- Client-side bundle size

---

## 15. Package Management: uv (Python) / pnpm (Node)
**Decision**: Use uv for Python, pnpm for Node.js.
**Reason**:
- uv: Extremely fast, drop-in pip replacement, lockfile
- pnpm: Fast, disk-efficient, strict dependencies

**Alternatives Considered**:
- poetry: Slower, different lockfile format
- pip-tools: Manual workflow
- npm/yarn: Slower, hoisting issues

---

## 16. Linting/Format: ruff + mypy / eslint + prettier
**Decision**: Ruff (lint+format) + mypy for Python; ESLint + Prettier for TypeScript.
**Reason**:
- Ruff: Single tool, 100x faster than flake8+black
- mypy: Gradual typing, catches real bugs
- ESLint/Prettier: Standard TypeScript tooling

---

## 17. Testing: pytest / vitest
**Decision**: pytest for backend, vitest for frontend.
**Reason**:
- pytest: Rich ecosystem, fixtures, parametrization
- vitest: Vite-native, fast, Jest-compatible API

---

## 18. Containerization: Docker Compose
**Decision**: Docker Compose for local infrastructure (PostgreSQL, Qdrant).
**Reason**:
- Declarative, version-controlled infrastructure
- Consistent across machines
- Easy startup/teardown
- Production-like locally

---

## 19. Configuration: pydantic-settings (.env)
**Decision**: Pydantic Settings for type-safe configuration.
**Reason**:
- Type validation with defaults
- Environment variable + .env file support
- Nested settings for organization
- IDE autocomplete

---

## 20. Database Migrations: Alembic
**Decision**: Alembic for schema migrations.
**Reason**:
- Standard with SQLAlchemy
- Version control for schema
- Autogenerate from models
- Rollback support