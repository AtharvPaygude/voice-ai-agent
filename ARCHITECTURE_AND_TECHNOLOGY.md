# Aura Voice AI: Features and Technology Overview

## 1. Product Summary

Aura Voice AI is a multilingual voice-agent platform for sales and customer service. It lets a business configure an AI agent, handle live voice conversations, execute business actions, inspect transcripts and sentiment, and review operational analytics.

The current application is a phase-one implementation. Some screens already connect to the backend and database, while some dashboard values and CRM integrations are still demo or mock data.

## 2. Main Application Areas

### Live Monitor

Live Monitor is the real-time operations dashboard for active calls.

What it provides:

- Live call queue with caller IDs, call state, and elapsed time.
- Active AI-agent status.
- Central 3D AI orb showing the current voice pipeline state.
- Start, mute, and end voice-call controls.
- Manual language selection for English, Hindi, Marathi, and Hinglish.
- Browser and server voice-engine selection.
- Live transcript of caller and agent messages.
- Real-time sentiment and lead-score display.
- Runtime metrics such as latency, tokens per second, and active streams.
- One-click multilingual demonstration flow.

Technology used:

- React and TypeScript for the dashboard components.
- Zustand for call-session state, including call status, language, transcript, metrics, and orb state.
- React Three Fiber and Three.js for the animated AI orb.
- WebSocket for low-latency call events, transcripts, state changes, tool results, and audio.
- Browser Web Speech APIs for the browser voice path.
- FastAPI WebSocket endpoint for the server voice path.
- SQLAlchemy models for persisted calls and messages.
- faster-whisper for server-side speech-to-text.
- edge-tts for server-side text-to-speech.

Important implementation note: the browser path uses the browser's native SpeechRecognition and SpeechSynthesis where supported. The server path records audio, sends it to the backend, transcribes it with faster-whisper, and returns generated audio from edge-tts.

### Agent Studio

Agent Studio is the configuration workspace for defining how the voice agent behaves.

What it provides:

- Primary language selection.
- Automatic language switching with a confidence threshold and stability count.
- Persona selection: Professional, Friendly, or Energetic.
- Editable system prompt.
- Voice preview using the browser SpeechSynthesis API.
- Test-call action.
- Save-configuration action.
- Deployment-oriented controls for the active agent profile.

Technology used:

- React and TypeScript for the configuration form.
- Local React state for editable prompt, auto-switch toggle, and voice-preview state.
- Zustand for shared persona and language values used by the live monitor.
- Browser SpeechSynthesis for the immediate voice preview.
- FastAPI configuration routes for reading and updating agent configuration.
- Pydantic models for validating configuration data on the backend.

The main agent settings include language, persona, system prompt, and text-to-speech voice mapping. In production, these settings should be persisted per workspace or agent instead of being held only in process memory.

### Analytics

Analytics is the reporting and observability area for understanding conversations and agent performance.

What it provides:

- Total call volume.
- Average conversation duration.
- Resolution rate.
- Dominant language or dialect.
- Language and regional distribution.
- Origin and routing view.
- Sentiment trajectory.
- Intent-resolution view.
- Time-range selector for one hour, twenty-four hours, or seven days.

Technology used:

- React and TypeScript for the analytics interface.
- Reusable dashboard components and CSS utility classes for cards, charts, and status indicators.
- FastAPI analytics routes for overview, language, sentiment, and tool statistics.
- SQLAlchemy queries over calls, messages, leads, tickets, and appointments.
- JSON API responses consumed by the frontend.

Current status: the analytics page contains designed dashboard values and visualizations for the phase-one experience. The backend has analytics endpoints that can provide persisted data, but the frontend should be connected to those endpoints wherever a live metric is required.

### Integrations

Integrations is the connectivity and infrastructure settings area.

What it provides:

- Local API or gateway-token display.
- Live WebSocket endpoint display.
- Local Ollama model connection details.
- Business-tool status.
- CRM adapter status.
- Copy-to-clipboard behavior for the displayed token.

Technology used:

- React and TypeScript for the settings interface.
- Vite environment variables for configurable API and WebSocket URLs.
- FastAPI for REST and WebSocket services.
- Ollama for local LLM inference.
- HTTPX for outbound calls to Ollama and the optional Gemini API.
- Backend tool routes for appointments, product information, orders, leads, tickets, email, SMS, customer lookup, and human transfer.

Current status: the business tools and CRM cards are labeled as mock or plug-and-play. They are application extension points, not proof that a real CRM, telephony provider, email provider, or SMS provider is connected. Production integrations should use environment-managed secrets and provider-specific adapters.

## 3. Frontend Technology

Location: `final_project/frontend`

Core stack:

- React 19: component-based user interface.
- TypeScript: typed components, state, and API contracts.
- Vite: development server and production bundler.
- React Router: navigation between Live Monitor, Agent Studio, Analytics, and Integrations.
- Zustand: lightweight shared application state for calls and agent configuration.
- Tailwind CSS: utility styling and responsive layouts.
- Framer Motion: interface animation support.
- Three.js with React Three Fiber and Drei: 3D AI orb and visual voice experience.
- Lucide React and Material Symbols: interface icons.
- Oxlint: frontend linting.

Frontend responsibilities:

1. Render the operator interface.
2. Start and control a call session.
3. Maintain temporary call UI state.
4. Open a WebSocket connection for live conversation events.
5. Display transcripts, tool actions, language changes, sentiment, and metrics.
6. Send configuration changes to the backend.
7. Provide browser-side audio capture and playback when the browser voice mode is selected.

The frontend should never own business truth. Calls, messages, agent configuration, analytics, and tool results should ultimately come from or be persisted by the backend.

## 4. Backend Technology

Location: `final_project/backend`

Core stack:

- Python 3: backend implementation language.
- FastAPI: REST API and WebSocket framework.
- Uvicorn: ASGI server used to run the application.
- Pydantic and pydantic-settings: request validation and environment configuration.
- SQLAlchemy 2: ORM and database access layer.
- aiosqlite: asynchronous SQLite driver used by the current local database setup.
- WebSockets: real-time voice and event transport.
- HTTPX: asynchronous HTTP client for external LLM calls.
- faster-whisper: local speech-to-text model.
- edge-tts: neural text-to-speech service.
- Ollama: local LLM runtime using `llama3.1:8b` by default.
- Gemini API: optional cloud LLM fallback when `GEMINI_API_KEY` is configured.

Backend API areas:

- `GET /health`: service health check.
- `WS /ws/voice/{call_id}`: live voice and conversation stream.
- `/api/calls`: call summaries, call details, messages, and summaries.
- `/api/analytics`: overview, language, sentiment, and tool statistics.
- `/api/config`: current configuration, update, personas, and languages.
- `/api/knowledge`: knowledge documents, search, and upload.
- `/api/tools`: execute and list business tools.

Conversation processing flow:

1. The frontend opens a WebSocket for a call ID.
2. The caller provides text or recorded audio.
3. Server audio is transcribed by faster-whisper when server voice mode is active.
4. The backend detects or confirms the current language.
5. The LLM generates a response using conversation history and the system prompt.
6. If required, the LLM emits a structured tool-call block.
7. The backend executes the requested business tool.
8. The backend sends transcript, state, response, and tool-result events to the frontend.
9. Server voice mode synthesizes the response with edge-tts.
10. Calls and messages are persisted in the database.

## 5. Database and Data Storage

### What is used now

The current backend uses SQLite with async SQLAlchemy:

- Default URL: `sqlite:///./aura_voice.db`.
- The backend converts it to `sqlite+aiosqlite:///./aura_voice.db`.
- Tables are created automatically during application startup.
- The database is suitable for local development, demos, and a single-machine phase-one deployment.

Current ORM tables:

- `calls`: caller, languages, duration, intent, sentiment, lead score, summary, and status.
- `messages`: caller and agent transcript messages linked to calls.
- `appointments`: booked or cancelled appointments.
- `leads`: captured customer leads and scores.
- `tickets`: customer-support tickets and priorities.

Conversation history is also kept temporarily in backend memory by the LLM client. It is limited to the latest messages for context and should not be treated as permanent storage.

### What we should use for production

Use PostgreSQL as the primary production database, accessed through SQLAlchemy's asynchronous PostgreSQL driver such as `asyncpg`.

Recommended production storage:

- PostgreSQL for calls, messages, agent configuration, tools, appointments, leads, tickets, users, workspaces, and audit records.
- Redis for short-lived session state, WebSocket presence, rate limiting, background-job coordination, and frequently accessed metrics.
- Object storage such as Azure Blob Storage or Amazon S3 for audio recordings, exported reports, and large knowledge files.
- A vector database for knowledge retrieval embeddings. PostgreSQL with the pgvector extension is a good first choice because it keeps relational data and embeddings together. A managed vector service can be introduced later if search scale requires it.

Why PostgreSQL is the recommended database:

- Supports multiple backend instances and concurrent calls.
- Provides transactions and reliable relationships between calls, messages, leads, tickets, and appointments.
- Supports indexing and reporting queries better than a file-based SQLite database.
- Works well with JSON fields for flexible tool results while preserving structured columns for reporting.
- Supports pgvector for retrieval-augmented generation without introducing a separate vector database initially.
- Can be hosted as a managed service such as Azure Database for PostgreSQL.

Suggested production data separation:

| Data | Recommended storage |
| --- | --- |
| Users, workspaces, agents, configuration | PostgreSQL |
| Calls and call status | PostgreSQL |
| Transcript messages | PostgreSQL, with retention policies |
| Sentiment, intent, lead score | PostgreSQL |
| Appointments, leads, tickets | PostgreSQL |
| Active WebSocket/session state | Redis |
| Audio files and knowledge uploads | Azure Blob Storage or S3 |
| Knowledge chunks and embeddings | PostgreSQL + pgvector |
| Logs and traces | Application observability platform |

## 6. Security and Production Changes Needed

Before production use, the following should be implemented:

- Remove hardcoded or demo API-key values from the UI.
- Store secrets only in environment variables or a secret manager such as Azure Key Vault.
- Add authentication and workspace-level authorization.
- Validate WebSocket call ownership before accepting a call ID.
- Use HTTPS and secure WebSockets in deployed environments.
- Add database migrations with Alembic instead of relying only on `create_all`.
- Add indexes for call status, timestamps, language, sentiment, and foreign keys.
- Define transcript and audio retention policies.
- Redact or encrypt sensitive caller information.
- Add rate limiting for API, WebSocket, LLM, SMS, and email actions.
- Add structured logs, tracing, error monitoring, and usage monitoring.
- Replace mock CRM, email, SMS, and order adapters with authenticated provider integrations.

## 7. Recommended High-Level Architecture

```text
React + TypeScript + Vite frontend
        |
        | REST JSON APIs and secure WebSocket
        v
FastAPI backend
        |
        +-- Call and configuration services
        +-- LLM service: Ollama first, Gemini optional fallback
        +-- Voice service: faster-whisper STT and edge-tts TTS
        +-- Tool and integration adapters
        +-- Knowledge and retrieval service
        |
        +-- PostgreSQL + pgvector: durable application data
        +-- Redis: active sessions and cache
        +-- Blob storage: audio and uploaded documents
```

## 8. Short Technology Decision

For local development and phase-one demos, keep SQLite, aiosqlite, Ollama, browser audio APIs, faster-whisper, and edge-tts because they are inexpensive and easy to run.

For production, move durable data to managed PostgreSQL, use Redis for ephemeral real-time state, use blob storage for files and recordings, add pgvector for knowledge search, and secure all external integrations through a backend adapter layer.
