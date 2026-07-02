# VentureMind AI — AI Investment Committee

> **BUILD / CAUTION / REJECT** verdict on your startup idea in 90 seconds.
> Six AI agents. Deterministic scoring. 5-scenario investor studio.

---

## Architecture — One product, two services

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 Frontend  (Vercel / any static host) │
│  Premium SaaS UI · shadcn/ui · TypeScript        │
│  → calls POST /api/analyze (proxied to backend)  │
└─────────────────────┬───────────────────────────┘
                      │ HTTP JSON
┌─────────────────────▼───────────────────────────┐
│  FastAPI Backend  (Railway / Render / VPS)        │
│  api_server.py · POST /analyze → ResearchRunResult│
│  6 Python agents · Groq LLM · Serper search      │
└─────────────────────────────────────────────────┘
```

**Fallback**: If `NEXT_PUBLIC_API_URL` is not set, the frontend enters **demo mode** — it runs the full UI with illustrative analysis so judges can experience the product without a backend.

---

## Quick start — local full stack

### 1. Clone and install everything

```bash
git clone https://github.com/yourusername/venturemind-ai
cd venturemind-ai

# Python backend
pip install -r requirements.txt

# Node.js frontend
npm install
```

### 2. Set API keys

```bash
cp api.env.example api.env
# Edit api.env — add GROQ_API_KEY and SERPER_API_KEY
```

Get free keys:
- **Groq**: https://console.groq.com — use model `llama-3.3-70b-versatile`
- **Serper**: https://serper.dev — 2,500 free searches/month

### 3. Start the backend

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
# Backend live at: http://localhost:8000
# Docs at: http://localhost:8000/docs
```

### 4. Start the frontend

```bash
# In a new terminal:
NEXT_PUBLIC_API_URL=http://localhost:8000/analyze npm run dev
# Frontend live at: http://localhost:3000
```

---

## Production deployment (recommended: Vercel + Render)

### Backend → Render Web Service (free tier)

1. Go to https://render.com → New Web Service → Connect this repository
2. Set **Root Directory** to `/`
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
5. Set **Health Check Path**: `/health`
6. Add environment variables:
   ```
   GROQ_API_KEY=...
   SERPER_API_KEY=...
   FRONTEND_URL=https://venture-mind-ai-eight.vercel.app
   ENVIRONMENT=production
   ```
7. Deploy — Render gives you a URL like `https://venturemind-backend.onrender.com`

### Frontend → Vercel (free tier)

1. Go to https://vercel.com → New Project → Import repo
2. Framework: **Next.js** (auto-detected)
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://venturemind-backend.onrender.com/analyze
   ```
4. Deploy — done.

---

## Alternative: Streamlit only (5 min, no Node.js needed)

If you just want to run the Python UI:

```bash
pip install -r requirements.txt
cp api.env.example api.env  # add your keys
streamlit run app.py
# → http://localhost:8501
```

Deploy to Streamlit Community Cloud:
1. Push to GitHub
2. Go to https://share.streamlit.io → New app → select repo, entry: `app.py`
3. Add secrets: `GROQ_API_KEY` and `SERPER_API_KEY`

---

## Multi-agent pipeline

| # | Agent | Role |
|---|-------|------|
| 01 | **Planner** | Decomposes the idea into research vectors |
| 02 | **Market** | Searches live web for demand & timing signals |
| 03 | **Competitor** | Maps the competitive landscape |
| 04 | **Evaluator** | Quality gate — triggers reflection loops if evidence is weak |
| 05 | **Decision** | Deterministic score: demand×0.5 + competition×0.3 + risk×0.2 |
| 06 | **Report** | Synthesises SWOT, key findings, and investor memo |

---

## Project structure

```
├── api_server.py          ← FastAPI server (entry point for Next.js integration)
├── app.py                 ← Streamlit app (standalone UI, no Node.js needed)
├── main.py                ← CLI runner
├── requirements.txt       ← Python dependencies (includes fastapi + uvicorn)
├── agents/                ← 6 specialist agents
├── core/                  ← Orchestrator, models, config, providers
├── memory/                ← SQLite run history
├── tools/                 ← Search and calculator tools
├── ui/                    ← Streamlit rendering module
├── utils/                 ← PDF generator, scenario engine
└── src/                   ← Next.js 14 frontend
    ├── app/
    │   ├── api/analyze/route.ts   ← Proxies to ANALYZE_API_URL
    │   ├── layout.tsx
    │   └── page.tsx               ← Main UI + demo mode fallback
    ├── components/
    │   ├── ui/                    ← shadcn/ui primitives
    │   └── venturemind/           ← Product components
    └── lib/utils.ts               ← Mock generator + utilities
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Python backend | Groq LLM key |
| `SERPER_API_KEY` | ✅ Python backend | Live search key |
| `NEXT_PUBLIC_API_URL` | Next.js only | URL of `api_server.py` POST endpoint |
| `ANALYZE_API_KEY` | Optional | Bearer token if backend is auth-protected |

---

*Built for the Mind the Product: Everyone Ships Now hackathon · June 2026*
