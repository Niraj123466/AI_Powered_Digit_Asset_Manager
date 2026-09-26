import enum
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    BigInteger,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum as SQLEnum,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from app.db.session import Base


class AssetState(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    DUPLICATE = "DUPLICATE"
    DELETED = "DELETED"


class Modality(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class ProcessingStage(str, enum.Enum):
    VALIDATION = "VALIDATION"
    METADATA_EXTRACTION = "METADATA_EXTRACTION"
    AI_ANALYSIS = "AI_ANALYSIS"
    EMBEDDING_GENERATION = "EMBEDDING_GENERATION"
    DB_WRITE = "DB_WRITE"
    VECTOR_WRITE = "VECTOR_WRITE"
    TRANSCRIPTION = "TRANSCRIPTION"
    FRAME_EXTRACTION = "FRAME_EXTRACTION"
    OCR = "OCR"


class Asset(Base):
    __tablename__ = "asset"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    relative_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True, index=True
    )
    absolute_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    modified_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    modality: Mapped[Modality] = mapped_column(
        SQLEnum(Modality, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False,
        index=True,
    )
    state: Mapped[AssetState] = mapped_column(
        SQLEnum(AssetState, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False, default=AssetState.DISCOVERED, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_stage: Mapped[Optional[ProcessingStage]] = mapped_column(
        SQLEnum(ProcessingStage, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    media_metadata: Mapped[Optional["MediaMetadata"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    image_analysis: Mapped[Optional["ImageAnalysis"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    video_analysis: Mapped[Optional["VideoAnalysis"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    video_frames: Mapped[List["VideoFrame"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    document_analysis: Mapped[Optional["DocumentAnalysis"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    document_pages: Mapped[List["DocumentPage"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    transcript: Mapped[Optional["Transcript"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["Embedding"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    duplicate_group: Mapped[Optional["DuplicateGroup"]] = relationship(back_populates="assets")
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_asset_sha256_modality", "sha256", "modality"),
        Index("ix_asset_state_modality", "state", "modality"),
    )


class AssetVersion(Base):
    __tablename__ = "asset_version"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    modified_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[AssetState] = mapped_column(
        SQLEnum(AssetState, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    __table_args__ = (UniqueConstraint("asset_id", "version", name="uq_asset_version"),)


class MediaMetadata(Base):
    __tablename__ = "media_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Common
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Image specific
    exif_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Video specific
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    audio_codec: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    audio_channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    audio_sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Document specific
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pdf_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="media_metadata")


class ImageAnalysis(Base):
    __tablename__ = "image_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objects: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_bboxes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Model metadata
    vision_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    vision_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ocr_provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="image_analysis")


class VideoAnalysis(Base):
    __tablename__ = "video_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frame_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_frames: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    keyframes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Model metadata
    vision_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    vision_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="video_analysis")


class VideoFrame(Base):
    __tablename__ = "video_frame"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True
    )
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)  # seconds
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objects: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    embedding_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("embedding.id", ondelete="SET NULL"), nullable=True
    )

    asset: Mapped["Asset"] = relationship(back_populates="video_frames")

    __table_args__ = (
        UniqueConstraint("asset_id", "frame_number", name="uq_video_frame"),
        Index("ix_video_frame_timestamp", "asset_id", "timestamp"),
    )


class DocumentAnalysis(Base):
    __tablename__ = "document_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_chars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ocr_pages_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    native_text_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Model metadata
    llm_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    llm_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="document_analysis")


class DocumentPage(Base):
    __tablename__ = "document_page"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_ocr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("embedding.id", ondelete="SET NULL"), nullable=True
    )

    asset: Mapped["Asset"] = relationship(back_populates="document_pages")

    __table_args__ = (UniqueConstraint("asset_id", "page_number", name="uq_document_page"),)


class Transcript(Base):
    __tablename__ = "transcript"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    segments: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{"start": float, "end": float, "text": str}]
    language: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Model metadata
    transcription_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    transcription_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="transcript")


class Embedding(Base):
    __tablename__ = "embedding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True
    )
    modality: Mapped[Modality] = mapped_column(
        SQLEnum(Modality, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "image", "text", "frame", "page"
    content_ref: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )  # frame_number, page_number, etc.
    vector_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # Qdrant point ID
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="embeddings")

    __table_args__ = (
        Index("ix_embedding_asset_modality", "asset_id", "modality"),
        Index("ix_embedding_vector_id", "vector_id"),
    )


class ProcessingJob(Base):
    __tablename__ = "processing_job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True
    )
    state: Mapped[AssetState] = mapped_column(
        SQLEnum(AssetState, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False, default=AssetState.QUEUED, index=True
    )
    stage: Mapped[Optional[ProcessingStage]] = mapped_column(
        SQLEnum(ProcessingStage, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="processing_jobs")


class DuplicateGroup(Base):
    __tablename__ = "duplicate_group"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    canonical_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False
    )
    reference_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    assets: Mapped[List["Asset"]] = relationship(back_populates="duplicate_group")


class SearchQuery(Base):
    __tablename__ = "search_query"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    modality_filter: Mapped[Optional[Modality]] = mapped_column(
        SQLEnum(Modality, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=True,
    )
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )

    __table_args__ = (Index("ix_search_query_created_at", "created_at"),)
