import asyncio
import pytesseract
from PIL import Image
from typing import List, Optional
from app.ai.base import OCRProvider, OCRResult
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TesseractOCRProvider(OCRProvider):
    def __init__(
        self,
        languages: str = None,
        dpi: int = None,
    ):
        self._languages = languages or settings.ocr_languages
        self._dpi = dpi or settings.ocr_dpi
        self._model_name = "tesseract"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def extract_text(self, image: Image.Image) -> OCRResult:
        loop = asyncio.get_event_loop()

        def _extract():
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image,
                lang=self._languages,
                output_type=pytesseract.Output.DICT,
            )

            # Extract text
            texts = [text for text in data["text"] if text.strip()]
            full_text = " ".join(texts)

            # Calculate average confidence
            confidences = [int(c) for c in data["conf"] if c != "-1"]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Extract bounding boxes
            bboxes = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    bboxes.append(
                        {
                            "text": data["text"][i],
                            "confidence": int(data["conf"][i]) if data["conf"][i] != "-1" else 0,
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "width": data["width"][i],
                            "height": data["height"][i],
                        }
                    )

            return OCRResult(
                text=full_text,
                confidence=avg_confidence / 100.0,
                bboxes=bboxes,
            )

        try:
            return await loop.run_in_executor(None, _extract)
        except Exception as e:
            logger.error("OCR extraction failed", error=str(e))
            return OCRResult(text="", confidence=0.0, bboxes=[])


class DummyOCRProvider(OCRProvider):
    """Fallback provider for testing without OCR."""

    def __init__(self):
        self._model_name = "dummy"

    @property
    def model_name(self) -> str:
        return self._model_name

    async def extract_text(self, image: Image.Image) -> OCRResult:
        return OCRResult(text="", confidence=0.0, bboxes=[])
