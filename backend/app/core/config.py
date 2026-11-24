"""
Core configuration — loads from environment variables.
"""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # App
    APP_NAME: str = "Aura AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    AGENT_NAME: str = "Aura AI"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database — must be explicitly configured in backend/.env
    DATABASE_URL: str = ""

    # LLM Provider Configuration
    LLM_PRIMARY: str = "ollama"  # "ollama" | "gemini"
    LLM_SECONDARY: str = "gemini"  # "gemini" | "ollama" | "none"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"

    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT: float = 30.0

    # STT (faster-whisper)
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # TTS
    TTS_ENGINE: str = "edge-tts"
    DEFAULT_SPEAKING_STYLE: str = "friendly"  # "friendly" | "professional" | "empathetic"

    # Language Detection
    LANGUAGE_SWITCH_CONFIDENCE_THRESHOLD: float = 0.7
    LANGUAGE_SWITCH_STABILITY_COUNT: int = 2

    # RAG / Knowledge Base
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Escalation
    ESCALATION_ENABLED: bool = True  # Kill-switch: set ESCALATION_ENABLED=false to disable all escalations
    SUPPORT_PHONE: str = ""
    SUPPORT_HOURS: str = "Mon-Sat 9:00-18:00 IST"
    PUBLIC_API_URL: str = "http://localhost:8000"

    # Integrations
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "notifications@aura.ai"
    CRM_WEBHOOK_URL: str = ""
    TELEPHONY_PROVIDER: str = ""  # twilio | exotel | generic
    TELEPHONY_ACCOUNT_SID: str = ""
    TELEPHONY_AUTH_TOKEN: str = ""
    TELEPHONY_PHONE_NUMBER: str = ""

    model_config = SettingsConfigDict(
        env_file=[
            str(BACKEND_DIR / ".env"),   # backend .env takes highest precedence
            str(ROOT_DIR / ".env"),      # root .env as fallback
        ],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
