"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # asset table
    op.create_table(
        'asset',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('relative_path', sa.String(1024), nullable=False),
        sa.Column('absolute_path', sa.String(2048), nullable=False),
        sa.Column('extension', sa.String(16), nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('modified_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modality', sa.Enum('image', 'video', 'document', name='modality_enum'), nullable=False),
        sa.Column('state', sa.Enum('DISCOVERED', 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SKIPPED', 'DUPLICATE', 'DELETED', name='asset_state_enum'), nullable=False, server_default='DISCOVERED'),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('processing_stage', sa.Enum('VALIDATION', 'METADATA_EXTRACTION', 'AI_ANALYSIS', 'EMBEDDING_GENERATION', 'DB_WRITE', 'VECTOR_WRITE', 'TRANSCRIPTION', 'FRAME_EXTRACTION', 'OCR', name='processing_stage_enum'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_asset_sha256', 'asset', ['sha256'])
    op.create_index('ix_asset_relative_path', 'asset', ['relative_path'], unique=True)
    op.create_index('ix_asset_modality', 'asset', ['modality'])
    op.create_index('ix_asset_state', 'asset', ['state'])
    op.create_index('ix_asset_sha256_modality', 'asset', ['sha256', 'modality'])
    op.create_index('ix_asset_state_modality', 'asset', ['state', 'modality'])

    # asset_version table
    op.create_table(
        'asset_version',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('modified_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('state', sa.Enum('DISCOVERED', 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SKIPPED', 'DUPLICATE', 'DELETED', name='asset_state_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_asset_version', 'asset_version', ['asset_id', 'version'])
    op.create_index('ix_asset_version_asset_id', 'asset_version', ['asset_id'])

    # embedding table - MUST be before tables that reference it
    op.create_table(
        'embedding',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('modality', sa.Enum('image', 'video', 'document', name='modality_enum'), nullable=False),
        sa.Column('content_type', sa.String(64), nullable=False),
        sa.Column('content_ref', sa.String(128), nullable=True),
        sa.Column('vector_id', sa.String(64), nullable=False),
        sa.Column('model_name', sa.String(128), nullable=False),
        sa.Column('model_version', sa.String(64), nullable=True),
        sa.Column('dimensions', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_embedding_asset_id', 'embedding', ['asset_id'])
    op.create_index('ix_embedding_asset_modality', 'embedding', ['asset_id', 'modality'])
    op.create_index('ix_embedding_vector_id', 'embedding', ['vector_id'])

    # media_metadata table
    op.create_table(
        'media_metadata',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('width', sa.Integer, nullable=True),
        sa.Column('height', sa.Integer, nullable=True),
        sa.Column('format', sa.String(64), nullable=True),
        sa.Column('exif_data', JSONB, nullable=True),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('fps', sa.Float, nullable=True),
        sa.Column('codec', sa.String(64), nullable=True),
        sa.Column('bitrate', sa.BigInteger, nullable=True),
        sa.Column('audio_codec', sa.String(64), nullable=True),
        sa.Column('audio_channels', sa.Integer, nullable=True),
        sa.Column('audio_sample_rate', sa.Integer, nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('pdf_info', JSONB, nullable=True),
    )
    op.create_index('ix_media_metadata_asset_id', 'media_metadata', ['asset_id'])

    # image_analysis table
    op.create_table(
        'image_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('objects', JSONB, nullable=True),
        sa.Column('tags', JSONB, nullable=True),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('ocr_confidence', sa.Float, nullable=True),
        sa.Column('ocr_bboxes', JSONB, nullable=True),
        sa.Column('vision_model', sa.String(128), nullable=True),
        sa.Column('vision_model_version', sa.String(64), nullable=True),
        sa.Column('ocr_provider', sa.String(64), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_image_analysis_asset_id', 'image_analysis', ['asset_id'])

    # video_analysis table
    op.create_table(
        'video_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('frame_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('processed_frames', sa.Integer, nullable=False, server_default='0'),
        sa.Column('keyframes', JSONB, nullable=True),
        sa.Column('vision_model', sa.String(128), nullable=True),
        sa.Column('vision_model_version', sa.String(64), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_video_analysis_asset_id', 'video_analysis', ['asset_id'])

    # video_frame table
    op.create_table(
        'video_frame',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('frame_number', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.Float, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('objects', JSONB, nullable=True),
        sa.Column('embedding_id', UUID(as_uuid=True), sa.ForeignKey('embedding.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_unique_constraint('uq_video_frame', 'video_frame', ['asset_id', 'frame_number'])
    op.create_index('ix_video_frame_asset_id', 'video_frame', ['asset_id'])
    op.create_index('ix_video_frame_timestamp', 'video_frame', ['asset_id', 'timestamp'])

    # document_analysis table
    op.create_table(
        'document_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('total_chars', sa.Integer, nullable=False, server_default='0'),
        sa.Column('ocr_pages_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('native_text_pages', sa.Integer, nullable=False, server_default='0'),
        sa.Column('llm_model', sa.String(128), nullable=True),
        sa.Column('llm_model_version', sa.String(64), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_document_analysis_asset_id', 'document_analysis', ['asset_id'])

    # document_page table
    op.create_table(
        'document_page',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer, nullable=False),
        sa.Column('text', sa.Text, nullable=True),
        sa.Column('char_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_ocr', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('embedding_id', UUID(as_uuid=True), sa.ForeignKey('embedding.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_unique_constraint('uq_document_page', 'document_page', ['asset_id', 'page_number'])
    op.create_index('ix_document_page_asset_id', 'document_page', ['asset_id'])

    # transcript table
    op.create_table(
        'transcript',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_text', sa.Text, nullable=True),
        sa.Column('segments', JSONB, nullable=True),
        sa.Column('language', sa.String(16), nullable=True),
        sa.Column('transcription_model', sa.String(128), nullable=True),
        sa.Column('transcription_model_version', sa.String(64), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_transcript_asset_id', 'transcript', ['asset_id'])

    # processing_job table
    op.create_table(
        'processing_job',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('state', sa.Enum('DISCOVERED', 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SKIPPED', 'DUPLICATE', 'DELETED', name='asset_state_enum'), nullable=False, server_default='QUEUED'),
        sa.Column('stage', sa.Enum('VALIDATION', 'METADATA_EXTRACTION', 'AI_ANALYSIS', 'EMBEDDING_GENERATION', 'DB_WRITE', 'VECTOR_WRITE', 'TRANSCRIPTION', 'FRAME_EXTRACTION', 'OCR', name='processing_stage_enum'), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_processing_job_asset_id', 'processing_job', ['asset_id'])
    op.create_index('ix_processing_job_state', 'processing_job', ['state'])

    # duplicate_group table
    op.create_table(
        'duplicate_group',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('sha256', sa.String(64), nullable=False, unique=True),
        sa.Column('canonical_asset_id', UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reference_count', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_duplicate_group_sha256', 'duplicate_group', ['sha256'])
    op.create_index('ix_duplicate_group_canonical_asset', 'duplicate_group', ['canonical_asset_id'])

    # search_query table
    op.create_table(
        'search_query',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('modality_filter', sa.Enum('image', 'video', 'document', name='modality_enum'), nullable=True),
        sa.Column('filters', JSONB, nullable=True),
        sa.Column('result_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('result_ids', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_search_query_created_at', 'search_query', ['created_at'])

    # Full-text search indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_image_analysis_fts 
        ON image_analysis 
        USING gin(to_tsvector('english', coalesce(description, '') || ' ' || coalesce(ocr_text, '')))
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_video_analysis_fts 
        ON video_analysis 
        USING gin(to_tsvector('english', coalesce(summary, '')))
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_transcript_fts 
        ON transcript 
        USING gin(to_tsvector('english', coalesce(full_text, '')))
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_document_analysis_fts 
        ON document_analysis 
        USING gin(to_tsvector('english', coalesce(summary, '')))
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_document_page_fts 
        ON document_page 
        USING gin(to_tsvector('english', coalesce(text, '')))
    """)


def downgrade() -> None:
    op.drop_index('ix_search_query_created_at', table_name='search_query')
    op.drop_table('search_query')
    
    op.drop_index('ix_duplicate_group_canonical_asset', table_name='duplicate_group')
    op.drop_index('ix_duplicate_group_sha256', table_name='duplicate_group')
    op.drop_table('duplicate_group')
    
    op.drop_index('ix_processing_job_state', table_name='processing_job')
    op.drop_index('ix_processing_job_asset_id', table_name='processing_job')
    op.drop_table('processing_job')
    
    op.drop_index('ix_transcript_asset_id', table_name='transcript')
    op.drop_table('transcript')
    
    op.drop_index('ix_document_page_asset_id', table_name='document_page')
    op.drop_constraint('uq_document_page', 'document_page', type_='unique')
    op.drop_table('document_page')
    
    op.drop_index('ix_document_analysis_asset_id', table_name='document_analysis')
    op.drop_table('document_analysis')
    
    op.drop_index('ix_video_frame_timestamp', table_name='video_frame')
    op.drop_index('ix_video_frame_asset_id', table_name='video_frame')
    op.drop_constraint('uq_video_frame', 'video_frame', type_='unique')
    op.drop_table('video_frame')
    
    op.drop_index('ix_video_analysis_asset_id', table_name='video_analysis')
    op.drop_table('video_analysis')
    
    op.drop_index('ix_image_analysis_asset_id', table_name='image_analysis')
    op.drop_table('image_analysis')
    
    op.drop_index('ix_media_metadata_asset_id', table_name='media_metadata')
    op.drop_table('media_metadata')
    
    op.drop_index('ix_embedding_vector_id', table_name='embedding')
    op.drop_index('ix_embedding_asset_modality', table_name='embedding')
    op.drop_index('ix_embedding_asset_id', table_name='embedding')
    op.drop_table('embedding')
    
    op.drop_constraint('uq_asset_version', 'asset_version', type_='unique')
    op.drop_index('ix_asset_version_asset_id', table_name='asset_version')
    op.drop_table('asset_version')
    
    op.drop_index('ix_asset_state_modality', table_name='asset')
    op.drop_index('ix_asset_sha256_modality', table_name='asset')
    op.drop_index('ix_asset_state', table_name='asset')
    op.drop_index('ix_asset_modality', table_name='asset')
    op.drop_index('ix_asset_relative_path', table_name='asset')
    op.drop_index('ix_asset_sha256', table_name='asset')
    op.drop_table('asset')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS processing_stage_enum')
    op.execute('DROP TYPE IF EXISTS asset_state_enum')
    op.execute('DROP TYPE IF EXISTS modality_enum')