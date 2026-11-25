"""
Aura AI — FastAPI Backend
Multilingual Voice AI Agent for Sales & Service
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.websocket import router as ws_router
from app.api.routes.calls import router as calls_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.tools import router as tools_router
from app.api.routes.config import router as config_router
from app.api.routes.business import router as business_router
from app.api.routes.auth import router as auth_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.onboarding import router as onboarding_router
from app.api.routes.escalations import router as escalations_router
from app.api.routes.records import router as records_router
from app.core.config import settings
from app.db.database import init_db

from app.core.scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title="Aura AI",
    description="Multilingual Voice AI Agent for Sales & Service",
    version="1.0.0",
)


@app.on_event("startup")
async def on_startup():
    # Initializes tables if needed
    await init_db()
    # Start APScheduler background jobs for reminders and outbound calls
    start_scheduler()
    # Pre-warm models asynchronously
    import asyncio
    from app.core.llm_client import prewarm_ollama
    from app.core.stt import prewarm_whisper
    asyncio.create_task(prewarm_ollama())
    asyncio.create_task(prewarm_whisper())


@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(calls_router, prefix="/api/calls", tags=["Calls"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(tools_router, prefix="/api/tools", tags=["Tools"])
app.include_router(config_router, prefix="/api/config", tags=["Config"])
app.include_router(business_router, prefix="/api/business", tags=["Business"])
app.include_router(discovery_router, prefix="/api/discovery", tags=["Discovery"])
app.include_router(onboarding_router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(escalations_router, prefix="/api/escalations", tags=["Escalations"])
app.include_router(records_router, prefix="/api/records", tags=["Records"])


@app.api_route("/", methods=["GET", "HEAD"])
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "Aura AI",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
