"""
Server-side Text-to-Speech using edge-tts (Microsoft neural voices).
Supports sentence-level synthesis, per-style prosody (rate, pitch, volume),
and gender-selectable neural voices for all major languages worldwide.
"""
import logging
import re
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Gender-specific voice choices per language — edge-tts neural voices
NEURAL_VOICES: Dict[str, Dict[str, str]] = {
    "female": {
        # Indian (All 22 Scheduled Languages + Hinglish)
        "en": "en-US-JennyNeural",
        "hi": "hi-IN-SwaraNeural",
        "mr": "mr-IN-AarohiNeural",
        "hinglish": "hi-IN-SwaraNeural",
        "gu": "gu-IN-DhwaniNeural",
        "ta": "ta-IN-PallaviNeural",
        "te": "te-IN-ShrutiNeural",
        "kn": "kn-IN-SapnaNeural",
        "ml": "ml-IN-SobhanaNeural",
        "pa": "pa-IN-OjaswiNeural",
        "bn": "bn-IN-TanishaaNeural",
        "ur": "ur-PK-UzmaNeural",
        "ne": "ne-NP-HemkalaNeural",
        "as": "bn-IN-TanishaaNeural",
        "or": "bn-IN-TanishaaNeural",
        "sa": "hi-IN-SwaraNeural",
        "mai": "hi-IN-SwaraNeural",
        "sat": "hi-IN-SwaraNeural",
        "ks": "ur-PK-UzmaNeural",
        "kok": "mr-IN-AarohiNeural",
        "sd": "ur-PK-UzmaNeural",
        "doi": "hi-IN-SwaraNeural",
        "mni": "bn-IN-TanishaaNeural",
        "brx": "bn-IN-TanishaaNeural",
        "mwr": "hi-IN-SwaraNeural",
        "marvadi": "hi-IN-SwaraNeural",
        "marwari": "hi-IN-SwaraNeural",
        "raj": "hi-IN-SwaraNeural",
        "rajasthani": "hi-IN-SwaraNeural",
        # Asian
        "ja": "ja-JP-NanamiNeural",
        "zh": "zh-CN-XiaoxiaoNeural",
        "ko": "ko-KR-SunHiNeural",
        "th": "th-TH-PremwadeeNeural",
        "vi": "vi-VN-HoaiMyNeural",
        "id": "id-ID-GadisNeural",
        "ms": "ms-MY-YasminNeural",
        # European
        "fr": "fr-FR-DeniseNeural",
        "de": "de-DE-KatjaNeural",
        "es": "es-ES-ElviraNeural",
        "pt": "pt-BR-FranciscaNeural",
        "it": "it-IT-ElsaNeural",
        "ru": "ru-RU-SvetlanaNeural",
        "nl": "nl-NL-FennaNeural",
        "pl": "pl-PL-ZofiaNeural",
        "tr": "tr-TR-EmelNeural",
        # Middle East / Africa
        "ar": "ar-SA-ZariyahNeural",
        "fa": "fa-IR-DilaraNeural",
        "sw": "sw-TZ-RehemaNeural",
    },
    "male": {
        # Indian (All 22 Scheduled Languages + Hinglish)
        "en": "en-US-GuyNeural",
        "hi": "hi-IN-MadhurNeural",
        "mr": "mr-IN-ManoharNeural",
        "hinglish": "hi-IN-MadhurNeural",
        "gu": "gu-IN-NiranjanNeural",
        "ta": "ta-IN-ValluvarNeural",
        "te": "te-IN-MohanNeural",
        "kn": "kn-IN-GaganNeural",
        "ml": "ml-IN-MidhunNeural",
        "pa": "pa-IN-GurpreetNeural",
        "bn": "bn-IN-BashkarNeural",
        "ur": "ur-PK-AsadNeural",
        "ne": "ne-NP-SagarNeural",
        "as": "bn-IN-BashkarNeural",
        "or": "bn-IN-BashkarNeural",
        "sa": "hi-IN-MadhurNeural",
        "mai": "hi-IN-MadhurNeural",
        "sat": "hi-IN-MadhurNeural",
        "ks": "ur-PK-AsadNeural",
        "kok": "mr-IN-ManoharNeural",
        "sd": "ur-PK-AsadNeural",
        "doi": "hi-IN-MadhurNeural",
        "mni": "bn-IN-BashkarNeural",
        "brx": "bn-IN-BashkarNeural",
        "mwr": "hi-IN-MadhurNeural",
        "marvadi": "hi-IN-MadhurNeural",
        "marwari": "hi-IN-MadhurNeural",
        "raj": "hi-IN-MadhurNeural",
        "rajasthani": "hi-IN-MadhurNeural",
        # Asian
        "ja": "ja-JP-KeitaNeural",
        "zh": "zh-CN-YunxiNeural",
        "ko": "ko-KR-InJoonNeural",
        "th": "th-TH-NiwatNeural",
        "vi": "vi-VN-NamMinhNeural",
        "id": "id-ID-ArdiNeural",
        "ms": "ms-MY-OsmanNeural",
        # European
        "fr": "fr-FR-HenriNeural",
        "de": "de-DE-ConradNeural",
        "es": "es-ES-AlvaroNeural",
        "pt": "pt-BR-AntonioNeural",
        "it": "it-IT-DiegoNeural",
        "ru": "ru-RU-DmitryNeural",
        "nl": "nl-NL-MaartenNeural",
        "pl": "pl-PL-MarekNeural",
        "tr": "tr-TR-AhmetNeural",
        # Middle East / Africa
        "ar": "ar-SA-HamedNeural",
        "fa": "fa-IR-FaridNeural",
        "sw": "sw-KE-RafikiNeural",
    },
}

_DEFAULT_VOICE_MAP = NEURAL_VOICES["female"]


def _clean_text_for_speech(text: str) -> str:
    """Clean internal tool-call markers and markdown formatting before TTS."""
    # Remove canonical tool-call markers
    clean = re.sub(r":::TOOL_CALL:::.*?:::END_TOOL_CALL:::", "", text, flags=re.DOTALL)
    # Remove double-colon variants like ::LOOKUP_CUSTOMER:: {json} ::END_TOOL_CALL::
    clean = re.sub(r"::(?:TOOL_CALL|END_TOOL_CALL|[A-Z_]{3,})::.*?(?:::END_TOOL_CALL::|$)", "", clean, flags=re.DOTALL)
    # Remove equals-sign variants like =GET_OFFERING_DETAILS= {json}
    clean = re.sub(r"=(?:TOOL_CALL|END_TOOL_CALL|[A-Z_]{3,})=.*?(?:=END_TOOL_CALL=|$)", "", clean, flags=re.DOTALL)
    # Remove bare JSON tool blocks
    clean = re.sub(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,.*?\}', "", clean, flags=re.DOTALL)
    # Strip markdown symbols
    clean = re.sub(r"[*_#`~\[\]]", "", clean)
    # Collapse extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


async def synthesize_speech(
    text: str,
    language: str = "en",
    voice_map: Optional[dict] = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    gender: str = "female",
) -> bytes:
    """
    Convert text to speech with edge-tts and return raw MP3 bytes.
    Applies style prosody (rate, pitch, volume).
    """
    clean = _clean_text_for_speech(text)
    if not clean:
        return b""

    try:
        import edge_tts
    except ImportError:
        logger.warning("edge-tts is not installed — run: pip install edge-tts")
        return b""

    active_map = voice_map or NEURAL_VOICES.get(gender, NEURAL_VOICES["female"])
    voice = active_map.get(language, active_map.get("en", "en-US-JennyNeural"))

    try:
        communicate = edge_tts.Communicate(
            text=clean,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        audio_chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.extend(chunk["data"])
        return bytes(audio_chunks)
    except Exception as e:
        logger.error(f"edge-tts synthesis failed: {e}")
        return b""
