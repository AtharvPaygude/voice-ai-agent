"""
Universal Multilingual Registry & Capability System for Aura Voice AI.

Provides scalable language registration, capability tracking (STT, TTS, LLM),
and intelligent language detection supporting all Indian languages and worldwide languages.
"""
import re
from typing import Dict, List, Optional
from pydantic import BaseModel


class LanguageCapability(BaseModel):
    code: str
    name: str
    native_name: str
    region: str
    stt: bool
    tts: bool
    llm: bool
    status: str  # "supported", "partially_supported", "experimental", "unavailable"
    default_voice: str
    flag: str
    type: str = "standard"  # "standard", "code_switched"


# Comprehensive Language Capability Registry
LANGUAGE_REGISTRY: Dict[str, LanguageCapability] = {
    # --- CORE MUST-HAVE LANGUAGES (Fully Supported & Tested) ---
    "en": LanguageCapability(
        code="en",
        name="English",
        native_name="English",
        region="Global",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="en-US-GuyNeural",
        flag="🇬🇧",
    ),
    "hi": LanguageCapability(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),
    "mr": LanguageCapability(
        code="mr",
        name="Marathi",
        native_name="मराठी",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="mr-IN-ManoharNeural",
        flag="🇮🇳",
    ),
    "hinglish": LanguageCapability(
        code="hinglish",
        name="Hinglish",
        native_name="Hinglish",
        region="India",
        type="code_switched",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳🇬🇧",
    ),

    # --- INDIAN LANGUAGE EXPANSION ---
    "bn": LanguageCapability(
        code="bn",
        name="Bengali",
        native_name="বাংলা",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="bn-IN-BashkarNeural",
        flag="🇮🇳",
    ),
    "gu": LanguageCapability(
        code="gu",
        name="Gujarati",
        native_name="ગુજરાતી",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="gu-IN-NiranjanNeural",
        flag="🇮🇳",
    ),
    "pa": LanguageCapability(
        code="pa",
        name="Punjabi",
        native_name="ਪੰਜਾਬੀ",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="pa-IN-GurpreetNeural",
        flag="🇮🇳",
    ),
    "ta": LanguageCapability(
        code="ta",
        name="Tamil",
        native_name="தமிழ்",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ta-IN-ValluvarNeural",
        flag="🇮🇳",
    ),
    "te": LanguageCapability(
        code="te",
        name="Telugu",
        native_name="తెలుగు",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="te-IN-MohanNeural",
        flag="🇮🇳",
    ),
    "kn": LanguageCapability(
        code="kn",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="kn-IN-GaganNeural",
        flag="🇮🇳",
    ),
    "ml": LanguageCapability(
        code="ml",
        name="Malayalam",
        native_name="മലയാളം",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ml-IN-MidhunNeural",
        flag="🇮🇳",
    ),
    "ur": LanguageCapability(
        code="ur",
        name="Urdu",
        native_name="اردو",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ur-IN-SalmanNeural",
        flag="🇮🇳",
    ),
    "or": LanguageCapability(
        code="or",
        name="Odia",
        native_name="ଓଡ଼ିଆ",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="bn-IN-BashkarNeural",
        flag="🇮🇳",
    ),
    "as": LanguageCapability(
        code="as",
        name="Assamese",
        native_name="অসমীয়া",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="bn-IN-BashkarNeural",
        flag="🇮🇳",
    ),
    "ne": LanguageCapability(
        code="ne",
        name="Nepali",
        native_name="नेपाली",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="ne-NP-SagarNeural",
        flag="🇳🇵",
    ),
    "sa": LanguageCapability(
        code="sa",
        name="Sanskrit",
        native_name="संस्कृतम्",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),
    "mai": LanguageCapability(
        code="mai",
        name="Maithili",
        native_name="मैथिली",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="hi-IN-SwaraNeural",
        flag="🇮🇳",
    ),
    "sat": LanguageCapability(
        code="sat",
        name="Santali",
        native_name="ᱥᱟᱱᱛᱟᱲᱤ",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="hi-IN-SwaraNeural",
        flag="🇮🇳",
    ),
    "ks": LanguageCapability(
        code="ks",
        name="Kashmiri",
        native_name="کٲشُر",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="ur-PK-UzmaNeural",
        flag="🇮🇳",
    ),
    "kok": LanguageCapability(
        code="kok",
        name="Konkani",
        native_name="कोंकणी",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="mr-IN-ManoharNeural",
        flag="🇮🇳",
    ),
    "sd": LanguageCapability(
        code="sd",
        name="Sindhi",
        native_name="سنڌي",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="ur-PK-AsadNeural",
        flag="🇮🇳",
    ),
    "doi": LanguageCapability(
        code="doi",
        name="Dogri",
        native_name="डोगरी",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),
    "mni": LanguageCapability(
        code="mni",
        name="Manipuri (Meitei)",
        native_name="মৈতৈলোন্",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="bn-IN-TanishaaNeural",
        flag="🇮🇳",
    ),
    "brx": LanguageCapability(
        code="brx",
        name="Bodo",
        native_name="बड़ो",
        region="India",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="bn-IN-BashkarNeural",
        flag="🇮🇳",
    ),
    "mwr": LanguageCapability(
        code="mwr",
        name="Marvadi",
        native_name="मारवाड़ी",
        region="India (Rajasthan)",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),
    "marvadi": LanguageCapability(
        code="marvadi",
        name="Marvadi",
        native_name="मारवाड़ी",
        region="India (Rajasthan)",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),
    "raj": LanguageCapability(
        code="raj",
        name="Rajasthani",
        native_name="राजस्थानी",
        region="India (Rajasthan)",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),
    "rajasthani": LanguageCapability(
        code="rajasthani",
        name="Rajasthani",
        native_name="राजस्थानी",
        region="India (Rajasthan)",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="hi-IN-MadhurNeural",
        flag="🇮🇳",
    ),

    # --- WORLDWIDE GLOBAL LANGUAGES ---
    "es": LanguageCapability(
        code="es",
        name="Spanish",
        native_name="Español",
        region="Americas / Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="es-ES-AlvaroNeural",
        flag="🇪🇸",
    ),
    "fr": LanguageCapability(
        code="fr",
        name="French",
        native_name="Français",
        region="Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="fr-FR-HenriNeural",
        flag="🇫🇷",
    ),
    "de": LanguageCapability(
        code="de",
        name="German",
        native_name="Deutsch",
        region="Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="de-DE-ConradNeural",
        flag="🇩🇪",
    ),
    "pt": LanguageCapability(
        code="pt",
        name="Portuguese",
        native_name="Português",
        region="Americas / Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="pt-BR-AntonioNeural",
        flag="🇧🇷",
    ),
    "it": LanguageCapability(
        code="it",
        name="Italian",
        native_name="Italiano",
        region="Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="it-IT-DiegoNeural",
        flag="🇮🇹",
    ),
    "nl": LanguageCapability(
        code="nl",
        name="Dutch",
        native_name="Nederlands",
        region="Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="nl-NL-MaartenNeural",
        flag="🇳🇱",
    ),
    "ru": LanguageCapability(
        code="ru",
        name="Russian",
        native_name="Русский",
        region="Europe / Asia",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ru-RU-DmitryNeural",
        flag="🇷🇺",
    ),
    "ar": LanguageCapability(
        code="ar",
        name="Arabic",
        native_name="العربية",
        region="Middle East",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ar-SA-HamedNeural",
        flag="🇸🇦",
    ),
    "ja": LanguageCapability(
        code="ja",
        name="Japanese",
        native_name="日本語",
        region="Asia-Pacific",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ja-JP-KeitaNeural",
        flag="🇯🇵",
    ),
    "zh": LanguageCapability(
        code="zh",
        name="Mandarin Chinese",
        native_name="中文",
        region="Asia-Pacific",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="zh-CN-YunxiNeural",
        flag="🇨🇳",
    ),
    "ko": LanguageCapability(
        code="ko",
        name="Korean",
        native_name="한국어",
        region="Asia-Pacific",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="ko-KR-InJoonNeural",
        flag="🇰🇷",
    ),
    "tr": LanguageCapability(
        code="tr",
        name="Turkish",
        native_name="Türkçe",
        region="Middle East / Europe",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="tr-TR-AhmetNeural",
        flag="🇹🇷",
    ),
    "vi": LanguageCapability(
        code="vi",
        name="Vietnamese",
        native_name="Tiếng Việt",
        region="Asia-Pacific",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="vi-VN-NamMinhNeural",
        flag="🇻🇳",
    ),
    "id": LanguageCapability(
        code="id",
        name="Indonesian",
        native_name="Bahasa Indonesia",
        region="Asia-Pacific",
        stt=True,
        tts=True,
        llm=True,
        status="supported",
        default_voice="id-ID-ArdiNeural",
        flag="🇮🇩",
    ),
    "sw": LanguageCapability(
        code="sw",
        name="Swahili",
        native_name="Kiswahili",
        region="Africa",
        stt=True,
        tts=True,
        llm=True,
        status="partially_supported",
        default_voice="sw-KE-RafikiNeural",
        flag="🇰🇪",
    ),
}


def get_all_languages() -> List[dict]:
    """Return all registered languages as dictionary list."""
    return [cap.model_dump() for cap in LANGUAGE_REGISTRY.values()]


def get_language_capability(code: str) -> Optional[LanguageCapability]:
    """Lookup capability by code."""
    res = LANGUAGE_REGISTRY.get(code.lower())
    if res is None:
        return LanguageCapability(
            code=code.lower(),
            name=code.upper(),
            native_name=code.upper(),
            region="Global",
            stt=False,
            tts=False,
            llm=True,
            status="experimental",
            default_voice="",
            flag="🌐",
        )
    return res


# Keyword sets for Indic & Code-Switch detection
MARATHI_KEYWORDS = [
    "aahe", "nahi", "karu", "tumhi", "mahiti", "nako", "aala", "aali",
    "aata", "dupari", "nakki", "kiti", "kuthe", "kashala", "mala", "honar", "madhe"
]
HINDI_KEYWORDS = [
    "hai", "kya", "batao", "karna", "aap", "meri", "mujhse",
    "gaya", "iska", "kitna", "chahiye", "hoga", "hain", "accha", "acha"
]
DEVANAGARI_MARATHI_WORDS = ["आहे", "नाही", "करू", "तुम्ही", "माहिती", "नको", "नक्की", "दुपारी", "हो", "होणार"]


def detect_multilingual_language(text: str, default_lang: str = "en") -> str:
    """
    Intelligent language detection handling Devanagari, scripts, and code-switching.
    Preserves context without flipping on a single isolated token.
    """
    if not text:
        return default_lang

    text_lower = text.lower()

    # 1. Check explicit user preference requests
    if re.search(r"\b(speak|talk in|switch to|explain in)\s+marathi\b", text_lower) or "marathi madhe" in text_lower:
        return "mr"
    if re.search(r"\b(speak|talk in|switch to|explain in)\s+(marvadi|marwari|rajasthani)\b", text_lower) or "marvadi mein" in text_lower or "marwari mein" in text_lower or "rajasthani mein" in text_lower:
        return "raj"
    if re.search(r"\b(speak|talk in|switch to|explain in)\s+hindi\b", text_lower) or "hindi mein" in text_lower:
        return "hi"
    if re.search(r"\b(speak|talk in|switch to|explain in)\s+english\b", text_lower) or "english madhe" in text_lower:
        return "en"
    if re.search(r"\b(speak|talk in|switch to)\s+spanish\b", text_lower):
        return "es"
    if re.search(r"\b(speak|talk in|switch to)\s+french\b", text_lower):
        return "fr"
    if re.search(r"\b(speak|talk in|switch to)\s+german\b", text_lower):
        return "de"

    # 2. Check Unicode Script Blocks
    has_devanagari = any('\u0900' <= char <= '\u097f' for char in text)
    if has_devanagari:
        if any(w in text for w in DEVANAGARI_MARATHI_WORDS):
            return "mr"
        return "hi"

    # Bengali script
    if any('\u0980' <= char <= '\u09ff' for char in text):
        return "bn"
    # Gujarati script
    if any('\u0a80' <= char <= '\u0aff' for char in text):
        return "gu"
    # Tamil script
    if any('\u0b80' <= char <= '\u0bff' for char in text):
        return "ta"
    # Telugu script
    if any('\u0c00' <= char <= '\u0c7f' for char in text):
        return "te"
    # Kannada script
    if any('\u0c80' <= char <= '\u0cff' for char in text):
        return "kn"
    # Malayalam script
    if any('\u0d00' <= char <= '\u0d7f' for char in text):
        return "ml"
    # Arabic / Urdu script
    if any('\u0600' <= char <= '\u06ff' for char in text):
        return "ar"
    # Japanese Hiragana/Katakana — check BEFORE CJK because Japanese text
    # contains CJK kanji characters which would otherwise be misidentified as Chinese
    if any('\u3040' <= char <= '\u30ff' for char in text):
        return "ja"
    # CJK Unified — only return zh if no kana detected above
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return "zh"
    # Korean Hangul
    if any('\uac00' <= char <= '\ud7af' for char in text):
        return "ko"
    # Japanese — also catch full-width katakana extended block
    if any('\u31f0' <= char <= '\u31ff' for char in text):
        return "ja"

    # 3. Spanish keywords
    if any(re.search(rf"\b{w}\b", text_lower) for w in ["hola", "gracias", "por favor", "precio", "cita", "cuanto", "cuesta"]):
        return "es"
    # French keywords
    if any(re.search(rf"\b{w}\b", text_lower) for w in ["bonjour", "merci", "rendez-vous", "combien", "s'il vous plaît"]):
        return "fr"
    # German keywords
    if any(re.search(rf"\b{w}\b", text_lower) for w in ["guten tag", "hallo", "danke", "termin", "buchen", "wieviel"]):
        return "de"

    # 4. Latin-script Indic & Hinglish detection
    mr_match_count = sum(1 for w in MARATHI_KEYWORDS if re.search(rf"\b{w}\b", text_lower))
    hi_match_count = sum(1 for w in HINDI_KEYWORDS if re.search(rf"\b{w}\b", text_lower))

    if mr_match_count >= 1:
        return "mr"
    if hi_match_count >= 1:
        return "hinglish"

    return default_lang
