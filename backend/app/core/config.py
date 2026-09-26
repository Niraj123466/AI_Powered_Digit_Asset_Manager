from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    # Media Storage
    media_root: Path = Field(default=Path("./data/media"), alias="MEDIA_ROOT")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://dam:dam@localhost:5432/dam", alias="DATABASE_URL"
    )

    # Vector Database (Qdrant)
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection_prefix: str = Field(default="dam_", alias="QDRANT_COLLECTION_PREFIX")

    # Embedding Provider
    embedding_provider: str = Field(default="sentence_transformers", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="clip-ViT-B-32", alias="EMBEDDING_MODEL")
    embedding_device: str = Field(default="auto", alias="EMBEDDING_DEVICE")
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")

    # Vision Provider
    vision_provider: str = Field(default="ollama", alias="VISION_PROVIDER")
    vision_model: str = Field(default="llava:7b", alias="VISION_MODEL")
    vision_base_url: str = Field(default="http://localhost:11434", alias="VISION_BASE_URL")
    vision_timeout: int = Field(default=120, alias="VISION_TIMEOUT")

    # OCR Provider
    ocr_provider: str = Field(default="tesseract", alias="OCR_PROVIDER")
    ocr_languages: str = Field(default="eng", alias="OCR_LANGUAGES")
    ocr_dpi: int = Field(default=300, alias="OCR_DPI")
    enable_ocr: bool = Field(default=True, alias="ENABLE_OCR")

    # Transcription Provider
    transcription_provider: str = Field(default="faster_whisper", alias="TRANSCRIPTION_PROVIDER")
    transcription_model: str = Field(default="base", alias="TRANSCRIPTION_MODEL")
    transcription_device: str = Field(default="auto", alias="TRANSCRIPTION_DEVICE")
    transcription_compute_type: str = Field(default="auto", alias="TRANSCRIPTION_COMPUTE_TYPE")
    enable_video_transcription: bool = Field(default=False, alias="ENABLE_VIDEO_TRANSCRIPTION")

    # LLM Provider
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str = Field(default="llama3.1:8b", alias="LLM_MODEL")
    llm_base_url: str = Field(default="http://localhost:11434", alias="LLM_BASE_URL")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")

    # Reranker
    reranker_provider: str = Field(default="none", alias="RERANKER_PROVIDER")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RERANKER_MODEL")

    # Video Processing
    video_max_frames: int = Field(default=64, alias="VIDEO_MAX_FRAMES")
    video_sample_interval_seconds: int = Field(default=5, alias="VIDEO_SAMPLE_INTERVAL_SECONDS")
    video_ffmpeg_path: str = Field(default="ffmpeg", alias="VIDEO_FFMPEG_PATH")

    # PDF Processing
    pdf_ocr_threshold_chars_per_page: int = Field(default=100, alias="PDF_OCR_THRESHOLD_CHARS_PER_PAGE")
    pdf_max_pages_per_chunk: int = Field(default=1, alias="PDF_MAX_PAGES_PER_CHUNK")

    # Ingestion Pipeline
    ingestion_workers: int = Field(default=2, alias="INGESTION_WORKERS")
    ingestion_batch_size: int = Field(default=10, alias="INGESTION_BATCH_SIZE")
    ingestion_max_retries: int = Field(default=3, alias="INGESTION_MAX_RETRIES")
    ingestion_retry_base_delay: int = Field(default=60, alias="INGESTION_RETRY_BASE_DELAY")

    # Search Configuration
    semantic_weight: float = Field(default=0.60, alias="SEMANTIC_WEIGHT")
    lexical_weight: float = Field(default=0.20, alias="LEXICAL_WEIGHT")
    modality_weight: float = Field(default=0.10, alias="MODALITY_WEIGHT")
    metadata_weight: float = Field(default=0.10, alias="METADATA_WEIGHT")
    search_default_limit: int = Field(default=20, alias="SEARCH_DEFAULT_LIMIT")
    search_max_limit: int = Field(default=100, alias="SEARCH_MAX_LIMIT")
    search_rrf_k: int = Field(default=60, alias="SEARCH_RRF_K")

    # Modality Detection Keywords (stored as comma-separated strings in .env)
    modality_video_keywords: str = Field(default="video,clip,footage,movie,film", alias="MODALITY_VIDEO_KEYWORDS")
    modality_image_keywords: str = Field(default="image,photo,picture,snapshot,pic", alias="MODALITY_IMAGE_KEYWORDS")
    modality_document_keywords: str = Field(default="document,pdf,brochure,floor plan,plan,report", alias="MODALITY_DOCUMENT_KEYWORDS")

    # Hardware
    auto_detect_hardware: bool = Field(default=True, alias="AUTO_DETECT_HARDWARE")
    force_cpu: bool = Field(default=False, alias="FORCE_CPU")

    # File Extensions (comma-separated strings in .env)
    supported_image_exts: str = Field(default="jpg,jpeg,png,webp", alias="SUPPORTED_IMAGE_EXTS")
    supported_video_exts: str = Field(default="mp4,mov,mkv,avi,webm", alias="SUPPORTED_VIDEO_EXTS")
    supported_doc_exts: str = Field(default="pdf", alias="SUPPORTED_DOC_EXTS")

    # Ignore Patterns (comma-separated strings in .env)
    ignore_patterns: str = Field(default="*.tmp,*.temp,*.DS_Store,Thumbs.db,.git/*,__pycache__/*,node_modules/*,*.log", alias="IGNORE_PATTERNS")

    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    next_public_api_url: str = Field(default="http://localhost:8000", alias="NEXT_PUBLIC_API_URL")

    @field_validator("media_root", mode="before")
    @classmethod
    def resolve_media_root(cls, v: str | Path) -> Path:
        path = Path(v).expanduser()
        if not path.is_absolute():
            # Use project root (3 levels up from config.py: config.py -> core -> app -> backend -> project_root)
            backend_dir = Path(__file__).parent.parent.parent
            project_root = backend_dir.parent
            path = project_root / path
        return path.resolve()

    @property
    def modality_video_keywords_list(self) -> List[str]:
        return [k.strip().lower() for k in self.modality_video_keywords.split(",") if k.strip()]

    @property
    def modality_image_keywords_list(self) -> List[str]:
        return [k.strip().lower() for k in self.modality_image_keywords.split(",") if k.strip()]

    @property
    def modality_document_keywords_list(self) -> List[str]:
        return [k.strip().lower() for k in self.modality_document_keywords.split(",") if k.strip()]

    @property
    def supported_image_exts_list(self) -> List[str]:
        return [ext.strip().lower().lstrip(".") for ext in self.supported_image_exts.split(",") if ext.strip()]

    @property
    def supported_video_exts_list(self) -> List[str]:
        return [ext.strip().lower().lstrip(".") for ext in self.supported_video_exts.split(",") if ext.strip()]

    @property
    def supported_doc_exts_list(self) -> List[str]:
        return [ext.strip().lower().lstrip(".") for ext in self.supported_doc_exts.split(",") if ext.strip()]

    @property
    def ignore_patterns_list(self) -> List[str]:
        return [p.strip() for p in self.ignore_patterns.split(",") if p.strip()]

    @property
    def all_supported_extensions(self) -> List[str]:
        return self.supported_image_exts_list + self.supported_video_exts_list + self.supported_doc_exts_list

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


settings = Settings()