"""
Server-side Speech-to-Text using faster-whisper.
Runs locally and offline. Supports pre-warming at server startup,
language hinting for Hindi/Marathi/English, and tuned VAD filtering.
"""
import logging
import tempfile
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazily load and cache the faster-whisper model."""
    global _model
    if _model is not None:
        return _model

    from faster_whisper import WhisperModel

    logger.info(
        f"Loading faster-whisper model '{settings.WHISPER_MODEL_SIZE}' "
        f"(device={settings.WHISPER_DEVICE}, compute_type={settings.WHISPER_COMPUTE_TYPE})..."
    )
    _model = WhisperModel(
        settings.WHISPER_MODEL_SIZE,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE,
    )
    return _model


async def prewarm_whisper() -> None:
    """Asynchronously pre-warm whisper model into RAM during server startup."""
    try:
        # Load model in a thread to avoid blocking the event loop
        import asyncio
        await asyncio.to_thread(_get_model)
        logger.info("faster-whisper model loaded and ready.")
    except Exception as e:
        logger.warning(f"Whisper pre-warm skipped or failed: {e}")


_LANG_MAP = {
    # 22 Scheduled Indian Languages + Regional
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "hinglish": "hi",
    "gu": "gu",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "pa": "pa",
    "bn": "bn",
    "or": "or",
    "ur": "ur",
    "as": "as",
    "ne": "ne",
    "sa": "sa",
    "sd": "sd",
    "mai": "hi",  # Maithili maps to closest Indo-Aryan Hindi model
    "sat": "hi",  # Santali maps to Hindi acoustic model
    "ks": "ur",   # Kashmiri maps to Urdu/Hindi model
    "kok": "mr",  # Konkani maps to Marathi model
    "doi": "hi",  # Dogri maps to Hindi/Punjabi model
    "mni": "bn",  # Manipuri (Meitei) maps to Bengali model
    "brx": "as",  # Bodo maps to Assamese model
    "mwr": "hi",  # Marvadi / Marwari maps to Hindi model
    "marvadi": "hi",
    "marwari": "hi",
    "raj": "hi",  # Rajasthani maps to Hindi model
    "rajasthani": "hi",
    # Key Foreign Languages
    "ja": "ja",
    "zh": "zh",
    "ko": "ko",
    "th": "th",
    "vi": "vi",
    "id": "id",
    "ms": "ms",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "pt": "pt",
    "it": "it",
    "ru": "ru",
    "nl": "nl",
    "pl": "pl",
    "tr": "tr",
    "ar": "ar",
    "fa": "fa",
    "sw": "sw",
}


def transcribe_audio_bytes(
    audio_bytes: bytes, hint_language: Optional[str] = None
) -> Tuple[str, str, float]:
    """
    Transcribe raw audio bytes (WebM/Opus or WAV/MP3) and return (text, detected_language, confidence).
    Uses language hinting when provided to reduce latency.
    """
    if not audio_bytes:
        return "", hint_language or "en", 0.0

    try:
        model = _get_model()
    except Exception as e:
        logger.error(f"Failed to load whisper model: {e}")
        return "", hint_language or "en", 0.0

    import os
    tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.flush()
        tmp.close()  # Close so whisper can open it on Windows

        whisper_lang = _LANG_MAP.get(hint_language) if hint_language else None
        segments, info = model.transcribe(
            tmp.name,
            language=whisper_lang,
            beam_size=1,
            best_of=1,
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        detected_lang = (
            _LANG_MAP.get(info.language, info.language)
            if info.language
            else (hint_language or "en")
        )
        confidence = float(getattr(info, "language_probability", 0.0) or 0.0)
        return text, detected_lang, confidence
    except Exception as e:
        logger.error(f"faster-whisper transcription failed: {e}")
        return "", hint_language or "en", 0.0
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
