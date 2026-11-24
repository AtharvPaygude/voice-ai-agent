# 🌐 Aura Voice AI — Multilingual Voice AI Agent for Sales & Service

> **Tagline:** *Speak any language. Connect every heart.*

A production-ready, futuristic real-time multilingual AI voice agent that handles sales calls, customer service, lead qualification, appointment booking, order tracking, FAQs, and human escalation with **zero-lag automatic language switching** (English ↔ Hindi ↔ Marathi ↔ Hinglish).

Built faithfully following the **Stitch "Neural Synth" Design System** (Cyber-Modern Dark, `#0d1322` midnight navy, electric cyan `#00f0ff`, luminous depth glassmorphism, and interactive 3D WebGL AI Orb).

---

## ⚡ Quick Start Commands

### 1. Start the Frontend (Vite + React + Three.js + Tailwind)

You can run directly from the root directory or inside `frontend`:

```powershell
# From root directory:
npm run dev

# Or inside the frontend directory:
cd frontend
npm run dev
```

Open your browser at: **[http://localhost:5173](http://localhost:5173)** (or `http://localhost:5174`)

---

### 2. Build for Production

```powershell
# From root directory:
npm run build

# Or inside the frontend directory:
cd frontend
npm run build
```

---

### 3. Start the Backend (FastAPI + WebSocket + Ollama LLM)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

FastAPI server runs at: **[http://localhost:8000](http://localhost:8000)**  
Swagger API Documentation: **[http://localhost:8000/docs](http://localhost:8000/docs)**  
Real-time Voice WebSocket: `ws://localhost:8000/ws/voice/{call_id}`

---

## 🚀 Key Features

1. **3D WebGL AI Orb (Three.js & React Three Fiber)**
   - 9 distinct state visual animations: *Idle, Listening, Thinking, Speaking, Language Switch, Tool Action, Success, Error, Human Transfer*.
   - Audio-reactive scale waveforms & glowing signal rings.

2. **Automatic Multilingual Switching & Code-Switching**
   - Natural, real-time language detection with hysteresis stability.
   - Preserves full conversation context across language transitions without restarting.
   - Native support for: **English 🇬🇧, Hindi 🇮🇳, Marathi 🇮🇳, Hinglish 🇮🇳🇬🇧** + architected for 100+ global languages.

3. **Profile-Scoped Business Tool Calling**
   - Generic tools such as `get_offering_price()`, `get_offering_details()`, `check_availability()`, `book_slot()`, `check_order()`, `create_lead()`, `create_ticket()`, `send_email()`, `send_sms()`, and `transfer_to_human()`.
   - Calls bind to the selected business profile, and backend permissions prevent disabled tools from executing.
   - Built-in confirmation checks for high-risk actions and healthcare safeguards for medical advice or emergency requests.

4. **Stitch Neural Synth Design System**
   - **Live AI Core Dashboard** (Call Queue, 3D Orb, Metrics, Sentiment, Live Multilingual Transcript).
   - **Multilingual Analytics Hub** (Bento grid stats, Origin vectors, Dialect distribution, Sentiment trajectory).
   - **Profiles** (create, search, activate, and reuse business-specific agent contexts).
   - **Global Agent Configuration / Studio** (business identity, agent identity, languages, tools, workflows, permissions, policies, persona, system prompt, and voice preview).
   - **Integration & API Settings** (API keys, WebSocket streaming endpoints, Local Ollama compute, CRM/calendar/order/email/SMS/telephony adapters).

---

## 📁 Repository Structure

```
c:/AI VOICE AGENT/
├── package.json              # Root npm script runner
├── README.md                 # Complete documentation & quickstart
├── .env.example              # Environment variables template
├── frontend/                 # React + Vite + TypeScript + Tailwind + Three.js
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/       # Sidebar (260px), Header, AppShell
│   │   │   ├── orb/          # 3D WebGL AI Orb with 9 state shaders
│   │   │   ├── call/         # Live Call Queue & Active Agents
│   │   │   ├── transcript/   # Live Multilingual Transcript with confidence
│   │   │   └── analytics/    # Real-time Sentiment & Dialect bars
│   │   ├── pages/            # Dashboard, Studio, Analytics, Integrations
│   │   ├── stores/           # Zustand call state & multilingual demo runner
│   │   ├── types/            # Full TypeScript interfaces
│   │   ├── index.css         # Neural Synth tokens & glassmorphic classes
│   │   └── App.tsx           # App Router & views
│   └── package.json
└── backend/                  # Python FastAPI Backend
    ├── main.py               # FastAPI entry point
    ├── requirements.txt      # Python dependencies
    └── app/
        ├── core/config.py    # Pydantic env settings
        └── api/
            ├── websocket.py  # Realtime voice streaming protocol
            └── routes/       # Calls, Analytics, Knowledge RAG, Tools, Config
```

---

## 🎙️ 1-Click Interactive Demo Flow

1. Open **[http://localhost:5173](http://localhost:5173)** in your browser.
2. In the left panel, click **"Run Multilingual Demo"**.
3. Watch the AI seamlessly transition:
   - **Caller speaks Marathi**: *"He plan madhe appointment booking available aahe ka?"*
   - **AI responds in Marathi**: *"Ho nakki! Tumhi appointment book karu shakta..."*
   - **Caller confirms in English**: *"Yes, please book the 3 PM slot for product demo."*
   - **AI executes Tool**: Calls `book_appointment()` and confirms with calendar invite.
4. You can also type or simulate custom speech in English, Hindi, Marathi, or Hinglish in the bottom transcript input bar!

---

## Operator Workflow

1. Start the backend and frontend.
2. Open **Profiles** and create at least two business profiles with different offerings, enabled tools, and policies.
3. Activate one profile before starting a call. New calls send that selected profile ID to the backend WebSocket.
4. Use **Studio** to fine-tune the active configuration and save it through the configuration API.
5. Use the dashboard call controls to verify that responses and tool results match the active profile.

The backend enforces active-profile tools and permissions, so a disabled tool cannot execute even if requested by the model. Optional webhook adapters can be configured through `CRM_ADAPTER_URL`, `CALENDAR_ADAPTER_URL`, `ORDER_ADAPTER_URL`, `EMAIL_ADAPTER_URL`, `SMS_ADAPTER_URL`, and `TELEPHONY_ADAPTER_URL`; when unset, local SQLite/mock behavior remains available.
