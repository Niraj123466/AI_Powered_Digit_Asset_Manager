import asyncio
import os
from typing import Optional
from app.ai.base import TranscriptionProvider, TranscriptResult
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FasterWhisperTranscriptionProvider(TranscriptionProvider):
    def __init__(
        self,
        model: str = None,
        device: str = None,
        compute_type: str = None,
    ):
        self._model_name = model or settings.transcription_model
        self._device = device or settings.transcription_device
        self._compute_type = compute_type or settings.transcription_compute_type
        self._model = None
        self._model_version: Optional[str] = None

    def _resolve_device(self) -> str:
        if self._device == "auto":
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
            except ImportError:
                pass
            return "cpu"
        return self._device

    def _load_model(self) -> None:
        if self._model is None:
            from faster_whisper import WhisperModel

            device = self._resolve_device()
            logger.info(
                "Loading Whisper model",
                model=self._model_name,
                device=device,
                compute_type=self._compute_type,
            )
            self._model = WhisperModel(
                self._model_name,
                device=device,
                compute_type=self._compute_type,
            )
            self._model_version = "faster-whisper"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> Optional[str]:
        return self._model_version

    async def transcribe(self, audio_path: str) -> TranscriptResult:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()
        loop = asyncio.get_event_loop()

        def _transcribe():
            segments, info = self._model.transcribe(
                audio_path,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            segment_list = []
            full_text_parts = []

            for segment in segments:
                segment_list.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                    }
                )
                full_text_parts.append(segment.text.strip())

            return TranscriptResult(
                full_text=" ".join(full_text_parts),
                segments=segment_list,
                language=info.language,
            )

        try:
            return await loop.run_in_executor(None, _transcribe)
        except Exception as e:
            logger.error("Transcription failed", error=str(e), audio_path=audio_path)
            raise


class DummyTranscriptionProvider(TranscriptionProvider):
    """Fallback provider for testing without transcription."""

    def __init__(self):
        self._model_name = "dummy"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> Optional[str]:
        return "0.0.0"

    async def transcribe(self, audio_path: str) -> TranscriptResult:
        return TranscriptResult(full_text="", segments=[], language="unknown")
