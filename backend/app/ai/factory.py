from typing import Optional
from app.ai.base import (
    EmbeddingProvider,
    VisionProvider,
    OCRProvider,
    TranscriptionProvider,
    LLMProvider,
    Reranker,
)
from app.ai.embeddings.embedding_provider import (
    SentenceTransformersEmbeddingProvider,
    DummyEmbeddingProvider,
)
from app.ai.vision.vision_provider import OllamaVisionProvider, DummyVisionProvider
from app.ai.ocr.ocr_provider import TesseractOCRProvider, DummyOCRProvider
from app.ai.transcription.transcription_provider import (
    FasterWhisperTranscriptionProvider,
    DummyTranscriptionProvider,
)
from app.ai.llm.llm_provider import OllamaLLMProvider, DummyLLMProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIProviderFactory:
    _embedding_provider: Optional[EmbeddingProvider] = None
    _vision_provider: Optional[VisionProvider] = None
    _ocr_provider: Optional[OCRProvider] = None
    _transcription_provider: Optional[TranscriptionProvider] = None
    _llm_provider: Optional[LLMProvider] = None
    _reranker: Optional[Reranker] = None

    @classmethod
    def get_embedding_provider(cls) -> EmbeddingProvider:
        if cls._embedding_provider is None:
            cls._embedding_provider = cls._create_embedding_provider()
        return cls._embedding_provider

    @classmethod
    def get_vision_provider(cls) -> VisionProvider:
        if cls._vision_provider is None:
            cls._vision_provider = cls._create_vision_provider()
        return cls._vision_provider

    @classmethod
    def get_ocr_provider(cls) -> OCRProvider:
        if cls._ocr_provider is None:
            cls._ocr_provider = cls._create_ocr_provider()
        return cls._ocr_provider

    @classmethod
    def get_transcription_provider(cls) -> TranscriptionProvider:
        if cls._transcription_provider is None:
            cls._transcription_provider = cls._create_transcription_provider()
        return cls._transcription_provider

    @classmethod
    def get_llm_provider(cls) -> LLMProvider:
        if cls._llm_provider is None:
            cls._llm_provider = cls._create_llm_provider()
        return cls._llm_provider

    @classmethod
    def get_reranker(cls) -> Optional[Reranker]:
        if settings.reranker_provider != "none" and cls._reranker is None:
            cls._reranker = cls._create_reranker()
        return cls._reranker

    @classmethod
    def _create_embedding_provider(cls) -> EmbeddingProvider:
        provider = settings.embedding_provider.lower()

        if provider == "sentence_transformers":
            try:
                return SentenceTransformersEmbeddingProvider()
            except Exception as e:
                logger.warning(
                    "Failed to load SentenceTransformers embedding provider, using dummy",
                    error=str(e),
                )
                return DummyEmbeddingProvider()
        elif provider == "dummy":
            return DummyEmbeddingProvider()
        else:
            logger.warning(f"Unknown embedding provider: {provider}, using dummy")
            return DummyEmbeddingProvider()

    @classmethod
    def _create_vision_provider(cls) -> VisionProvider:
        provider = settings.vision_provider.lower()

        if provider == "ollama":
            try:
                return OllamaVisionProvider()
            except Exception as e:
                logger.warning("Failed to load Ollama vision provider, using dummy", error=str(e))
                return DummyVisionProvider()
        elif provider == "dummy":
            return DummyVisionProvider()
        else:
            logger.warning(f"Unknown vision provider: {provider}, using dummy")
            return DummyVisionProvider()

    @classmethod
    def _create_ocr_provider(cls) -> OCRProvider:
        if not settings.enable_ocr:
            return DummyOCRProvider()

        provider = settings.ocr_provider.lower()

        if provider == "tesseract":
            try:
                return TesseractOCRProvider()
            except Exception as e:
                logger.warning("Failed to load Tesseract OCR provider, using dummy", error=str(e))
                return DummyOCRProvider()
        elif provider == "dummy":
            return DummyOCRProvider()
        else:
            logger.warning(f"Unknown OCR provider: {provider}, using dummy")
            return DummyOCRProvider()

    @classmethod
    def _create_transcription_provider(cls) -> TranscriptionProvider:
        if not settings.enable_video_transcription:
            return DummyTranscriptionProvider()

        provider = settings.transcription_provider.lower()

        if provider == "faster_whisper":
            try:
                return FasterWhisperTranscriptionProvider()
            except Exception as e:
                logger.warning(
                    "Failed to load FasterWhisper transcription provider, using dummy", error=str(e)
                )
                return DummyTranscriptionProvider()
        elif provider == "dummy":
            return DummyTranscriptionProvider()
        else:
            logger.warning(f"Unknown transcription provider: {provider}, using dummy")
            return DummyTranscriptionProvider()

    @classmethod
    def _create_llm_provider(cls) -> LLMProvider:
        provider = settings.llm_provider.lower()

        if provider == "ollama":
            try:
                return OllamaLLMProvider()
            except Exception as e:
                logger.warning("Failed to load Ollama LLM provider, using dummy", error=str(e))
                return DummyLLMProvider()
        elif provider == "dummy":
            return DummyLLMProvider()
        else:
            logger.warning(f"Unknown LLM provider: {provider}, using dummy")
            return DummyLLMProvider()

    @classmethod
    def _create_reranker(cls) -> Optional[Reranker]:
        # TODO: Implement cross-encoder reranker
        return None

    @classmethod
    def reset(cls) -> None:
        cls._embedding_provider = None
        cls._vision_provider = None
        cls._ocr_provider = None
        cls._transcription_provider = None
        cls._llm_provider = None
        cls._reranker = None
