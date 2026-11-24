"""Language capability registry for worldwide-ready voice configuration."""
from typing import Literal

from pydantic import BaseModel


LanguageStatus = Literal["supported", "partial", "experimental", "unavailable"]


class LanguageCapability(BaseModel):
    code: str
    name: str
    region: str
    status: LanguageStatus
    stt: bool
    tts: bool
    llm: bool
    voice: str | None = None
    type: str = "language"
    notes: str = ""


LANGUAGE_REGISTRY: dict[str, LanguageCapability] = {
    "en": LanguageCapability(code="en", name="English", region="Global", status="supported", stt=True, tts=True, llm=True, voice="en-US-GuyNeural"),
    "hi": LanguageCapability(code="hi", name="Hindi", region="India", status="supported", stt=True, tts=True, llm=True, voice="hi-IN-MadhurNeural"),
    "mr": LanguageCapability(code="mr", name="Marathi", region="India", status="supported", stt=True, tts=True, llm=True, voice="mr-IN-ManoharNeural"),
    "hinglish": LanguageCapability(code="hinglish", name="Hinglish", region="India", status="supported", stt=True, tts=True, llm=True, voice="hi-IN-MadhurNeural", type="code_switched"),
    "bn": LanguageCapability(code="bn", name="Bengali", region="India/Bangladesh", status="partial", stt=True, tts=False, llm=True),
    "gu": LanguageCapability(code="gu", name="Gujarati", region="India", status="partial", stt=True, tts=False, llm=True),
    "pa": LanguageCapability(code="pa", name="Punjabi", region="India/Pakistan", status="partial", stt=True, tts=False, llm=True),
    "ta": LanguageCapability(code="ta", name="Tamil", region="India/Sri Lanka", status="partial", stt=True, tts=False, llm=True),
    "te": LanguageCapability(code="te", name="Telugu", region="India", status="partial", stt=True, tts=False, llm=True),
    "kn": LanguageCapability(code="kn", name="Kannada", region="India", status="partial", stt=True, tts=False, llm=True),
    "ml": LanguageCapability(code="ml", name="Malayalam", region="India", status="partial", stt=True, tts=False, llm=True),
    "ur": LanguageCapability(code="ur", name="Urdu", region="India/Pakistan", status="partial", stt=True, tts=False, llm=True),
    "or": LanguageCapability(code="or", name="Odia", region="India", status="experimental", stt=False, tts=False, llm=True),
    "as": LanguageCapability(code="as", name="Assamese", region="India", status="experimental", stt=False, tts=False, llm=True),
    "ne": LanguageCapability(code="ne", name="Nepali", region="India/Nepal", status="experimental", stt=False, tts=False, llm=True),
    "kok": LanguageCapability(code="kok", name="Konkani", region="India", status="experimental", stt=False, tts=False, llm=True),
    "ks": LanguageCapability(code="ks", name="Kashmiri", region="India", status="experimental", stt=False, tts=False, llm=True),
    "mai": LanguageCapability(code="mai", name="Maithili", region="India/Nepal", status="experimental", stt=False, tts=False, llm=True),
    "sa": LanguageCapability(code="sa", name="Sanskrit", region="India", status="experimental", stt=False, tts=False, llm=True),
    "sd": LanguageCapability(code="sd", name="Sindhi", region="India/Pakistan", status="experimental", stt=False, tts=False, llm=True),
    "es": LanguageCapability(code="es", name="Spanish", region="Global", status="partial", stt=True, tts=False, llm=True),
    "fr": LanguageCapability(code="fr", name="French", region="Global", status="partial", stt=True, tts=False, llm=True),
    "de": LanguageCapability(code="de", name="German", region="Global", status="partial", stt=True, tts=False, llm=True),
    "pt": LanguageCapability(code="pt", name="Portuguese", region="Global", status="partial", stt=True, tts=False, llm=True),
    "it": LanguageCapability(code="it", name="Italian", region="Global", status="partial", stt=True, tts=False, llm=True),
    "nl": LanguageCapability(code="nl", name="Dutch", region="Global", status="partial", stt=True, tts=False, llm=True),
    "ru": LanguageCapability(code="ru", name="Russian", region="Global", status="partial", stt=True, tts=False, llm=True),
    "uk": LanguageCapability(code="uk", name="Ukrainian", region="Global", status="partial", stt=True, tts=False, llm=True),
    "pl": LanguageCapability(code="pl", name="Polish", region="Global", status="partial", stt=True, tts=False, llm=True),
    "tr": LanguageCapability(code="tr", name="Turkish", region="Global", status="partial", stt=True, tts=False, llm=True),
    "ar": LanguageCapability(code="ar", name="Arabic", region="Global", status="partial", stt=True, tts=False, llm=True),
    "he": LanguageCapability(code="he", name="Hebrew", region="Global", status="partial", stt=True, tts=False, llm=True),
    "fa": LanguageCapability(code="fa", name="Persian", region="Global", status="partial", stt=True, tts=False, llm=True),
    "zh": LanguageCapability(code="zh", name="Mandarin Chinese", region="Global", status="partial", stt=True, tts=False, llm=True),
    "yue": LanguageCapability(code="yue", name="Cantonese", region="Global", status="experimental", stt=False, tts=False, llm=True),
    "ja": LanguageCapability(code="ja", name="Japanese", region="Global", status="partial", stt=True, tts=False, llm=True),
    "ko": LanguageCapability(code="ko", name="Korean", region="Global", status="partial", stt=True, tts=False, llm=True),
    "vi": LanguageCapability(code="vi", name="Vietnamese", region="Global", status="partial", stt=True, tts=False, llm=True),
    "th": LanguageCapability(code="th", name="Thai", region="Global", status="partial", stt=True, tts=False, llm=True),
    "id": LanguageCapability(code="id", name="Indonesian", region="Global", status="partial", stt=True, tts=False, llm=True),
    "ms": LanguageCapability(code="ms", name="Malay", region="Global", status="partial", stt=True, tts=False, llm=True),
    "fil": LanguageCapability(code="fil", name="Filipino", region="Global", status="partial", stt=True, tts=False, llm=True),
    "sw": LanguageCapability(code="sw", name="Swahili", region="Global", status="experimental", stt=False, tts=False, llm=True),
}


def list_language_capabilities() -> list[LanguageCapability]:
    return sorted(LANGUAGE_REGISTRY.values(), key=lambda item: (item.status != "supported", item.region, item.name))


def get_tts_voice_map(codes: list[str]) -> dict[str, str]:
    return {
        code: capability.voice
        for code, capability in LANGUAGE_REGISTRY.items()
        if code in codes and capability.voice
    }
