"""
Agent configuration API routes for Aura AI.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.speaking_styles import SPEAKING_STYLES
from app.core.integrations import get_all_integration_statuses, test_integration

router = APIRouter()
logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent.parent / "agent_config.json"


class BusinessConfig(BaseModel):
    name: str = "Aura AI"
    industry: str = "service_business"
    description: str = "A configurable business serving customers through voice conversations."


class AgentIdentity(BaseModel):
    name: str = "Aura AI"
    role: str = "conversational AI agent"
    personality: str = "friendly professional"


class PolicyConfig(BaseModel):
    require_confirmation_for: List[str] = Field(default_factory=lambda: ["cancellation", "refund"])
    healthcare_safety: bool = True
    escalation_rules: List[str] = Field(default_factory=lambda: ["high-risk request", "caller asks for a human"])


class AgentConfig(BaseModel):
    business: BusinessConfig = Field(default_factory=BusinessConfig)
    agent: AgentIdentity = Field(default_factory=AgentIdentity)
    capabilities: List[str] = Field(default_factory=lambda: [
        "sales", "customer_support", "service", "appointment_booking", "faq",
        "rag", "human_handoff",
    ])
    knowledge_base: List[str] = Field(default_factory=lambda: ["business_info", "offerings", "policies"])
    tools: List[str] = Field(default_factory=lambda: [
        "get_offering_details", "get_offering_price", "check_availability", "book_slot",
        "check_order", "create_lead", "create_ticket", "transfer_to_human", "create_escalation_report"
    ])
    workflows: List[str] = Field(default_factory=lambda: ["general_inquiry", "booking", "support", "human_handoff"])
    permissions: Dict[str, bool] = Field(default_factory=lambda: {
        "read_knowledge": True,
        "execute_tools": True,
        "transfer_to_human": True,
    })
    policies: PolicyConfig = Field(default_factory=PolicyConfig)
    primary_language: str = "auto"
    auto_language_switch: bool = True
    persona: str = "professional"  # professional, friendly, energetic
    speaking_style: str = "friendly"  # friendly, professional, empathetic
    system_prompt: str = ""
    supported_languages: List[str] = ["en", "hi", "mr", "hinglish"]
    tts_voice_map: dict = {
        "en": "en-US-JennyNeural",
        "hi": "hi-IN-SwaraNeural",
        "mr": "mr-IN-AarohiNeural",
        "hinglish": "hi-IN-SwaraNeural",
    }
    confidence_threshold: float = 0.7
    stability_count: int = 2


def _load_persisted_config() -> AgentConfig:
    default_cfg = AgentConfig(
        business=BusinessConfig(
            name="Aura AI",
            industry="service_business",
            description="A business serving clients with bookings, inquiries, and customer service.",
        ),
        agent=AgentIdentity(name="Aura AI", role="conversational voice agent", personality="friendly professional"),
        system_prompt="""You are Aura AI, a skilled AI voice assistant speaking on behalf of the business.
RULES:
- Respond in the caller's language (English, Hindi, Marathi, Hinglish).
- Keep responses short and conversational (1-2 sentences).
- Never invent unverified details — use verified offerings, tools, or knowledge base.
- For high-risk actions, confirm details before proceeding.
- If unable to help, politely offer an escalation report or transfer to a human.
""",
    )

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AgentConfig(**data)
        except Exception as e:
            logger.warning(f"Failed to read agent_config.json: {e}")

    return default_cfg


current_config = _load_persisted_config()


@router.get("", response_model=AgentConfig)
async def get_config():
    """Get active agent configuration."""
    return current_config


@router.put("", response_model=AgentConfig)
async def update_config(config: AgentConfig):
    """Update agent configuration and persist to disk."""
    global current_config
    current_config = config
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))
    except Exception as e:
        logger.error(f"Failed to persist agent_config.json: {e}")
    return current_config


@router.get("/speaking-styles")
async def get_speaking_styles_metadata():
    """Get metadata for selectable speaking styles."""
    styles = []
    for k, v in SPEAKING_STYLES.items():
        styles.append({
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "prosody": v.get("prosody", {}),
            "sample_phrase": v["holding_lines"][0],
        })
    return styles


@router.get("/integrations/status")
async def get_integrations_status():
    """Get status of all integration adapters."""
    return await get_all_integration_statuses()


@router.post("/integrations/test/{service}")
async def test_integration_endpoint(service: str):
    """Test a specific external integration connection."""
    return await test_integration(service)
