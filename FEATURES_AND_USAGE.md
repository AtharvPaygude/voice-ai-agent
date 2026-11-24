# Aura Voice AI — Features and Usage Guide

## Project Overview

Aura Voice AI is a multilingual AI voice agent designed for sales and customer support workflows. It combines a real-time voice interface, multilingual conversation handling, business tool execution, and a modern dashboard for monitoring calls and analytics.

The project includes:

- Frontend dashboard built with React, Vite, TypeScript, and Tailwind
- Backend API built with FastAPI
- Real-time voice communication using WebSockets
- Browser-based and server-based voice processing support
- Multilingual AI conversation flow
- Business tools for appointments, CRM-style actions, and knowledge retrieval
- Analytics and state monitoring for live calls

---

## Core Features

### 1. Multilingual Voice AI

- Supports English, Hindi, Marathi, and Hinglish
- Can switch language during a live conversation without restarting the session
- Uses conversation context to preserve continuity across language changes
- Designed for multilingual sales and service use cases

### 2. Real-Time Voice Interaction

- Live microphone-based voice capture
- Real-time transcript updates
- WebSocket-based voice session communication
- Browser voice engine support via SpeechRecognition and SpeechSynthesis
- Server-side voice processing support with STT/TTS integration options

### 3. AI Agent Behavior

- Conversation orchestration for sales and service flows
- Fallback response logic when external AI services are unavailable
- LLM integration support for Ollama or Gemini-style backends
- Business workflow handling with tool calls and safety checks

### 4. Business Tool Calling

The system is built around actions such as:

- Booking appointments
- Checking product prices
- Looking up order information
- Creating leads
- Creating support tickets
- Sending emails
- Escalating to a human agent

These are designed as structured tool actions that the AI can invoke during a conversation.

### 5. Dashboard and Monitoring

The frontend includes:

- Dashboard overview
- live call queue
- AI orb visual state panel
- transcript panel
- analytics panel
- integrations and configuration area
- studio settings for prompts and persona controls

### 6. Analytics and Conversation Insights

- Session tracking
- Sentiment analysis panels
- Multilingual transcript display
- Operational metrics view
- Workflow monitoring for live conversations

### 7. Local Backend Architecture

- FastAPI server
- SQLite database support by default
- API routes for calls, analytics, knowledge, tools, and configuration
- WebSocket endpoint for live voice connections
- Health check endpoint

---

## Project Structure

```text
final_project/
├── README.md
├── SETUP.md
├── FEATURES_AND_USAGE.md
├── MANUAL_ADDITIONS.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   └── .venv/ (after setup)
├── frontend/
│   ├── package.json
│   ├── src/
│   ├── public/
│   └── dist/ (after build)
└── .env.example
```

---

## How to Use the Project

### 1. Install the required tools

Make sure these are installed on your machine:

- Python 3.11 or newer
- Node.js 20 or newer
- npm
- Git (optional, if cloning the project)
- Modern browser such as Chrome or Edge

### 2. Set up the backend

From the backend folder:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then start the server:

```powershell
python main.py
```

The backend will run on:

- http://localhost:8000
- http://localhost:8000/health
- http://localhost:8000/docs

### 3. Set up the frontend

From the frontend folder:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
npm install
npm run dev
```

The frontend is usually served at:

- http://localhost:5173

### 4. Open the app in the browser

- Open the frontend URL in Chrome or Edge
- Allow microphone access when prompted
- Use the dashboard to begin a live call

### 5. Use the voice workflow

Typical usage:

1. Start the backend and frontend
2. Open the dashboard
3. Select or start a voice session
4. Speak in English, Hindi, Marathi, or Hinglish
5. Observe the transcript and orb state updates
6. Confirm tool-driven actions like appointment booking or lead creation
7. End the session when done

---

## Example Use Cases

### Sales agent

- Answer product questions
- Handle multilingual customer requests
- Book appointments
- Create leads
- Escalate to a human if needed

### Customer support agent

- Track order status
- Answer FAQs
- Create support tickets
- Resolve customer queries in the user’s language

### Demo / pitch environment

- Show live multilingual AI interaction
- Present AI call handling in a real dashboard
- Demonstrate response switching between languages

---

## Troubleshooting Basics

### Frontend issue

If Vite or TypeScript is missing:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\frontend"
npm install
```

### Backend issue

If Python modules are missing:

```powershell
cd "C:\Users\Atharv Paygude\Downloads\AI_VOICE_AGENT_phase1_2\final_project\backend"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Browser access issue

Make sure:

- The backend is running
- The browser is using localhost or HTTPS
- Microphone access is allowed

---

## Notes

This project is a local demo and production-ready architecture foundation. Some features are ready for use out of the box, while others depend on additional services such as Ollama, Gemini, or external APIs.
