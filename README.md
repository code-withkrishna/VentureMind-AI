# VentureMind AI

**Your startup idea. Six AI analysts. A BUILD / CAUTION / REJECT verdict in 90 seconds.**

Founders don't need another idea validator that tells them their idea is "promising" — that's what every AI tool says. VentureMind runs your idea through six specialist agents that argue like an actual investment committee, then forces a deterministic score out the other end. No hedging. No "it depends." A verdict.

---

## The Problem

Most idea-validation tools are a single LLM call wearing a nice UI — ask a chatbot "is this a good idea?" and it will find a way to say yes. Founders walk away validated and unprepared, because the tool never actually modeled how an investor would push back.

**VentureMind is built to disagree with you.** It runs live market research, maps real competitors, and only reaches a verdict after a quality-gate agent has checked whether the evidence actually supports the conclusion — reflecting and re-researching if it doesn't.

---

## How It Thinks: The Six-Agent Committee

| # | Agent | Role |
|---|---|---|
| 01 | **Planner** | Breaks the idea into concrete research vectors — what actually needs to be checked |
| 02 | **Market** | Searches the live web for real demand and timing signals |
| 03 | **Competitor** | Maps the actual competitive landscape, not a generic list |
| 04 | **Evaluator** | The quality gate — if evidence is weak, it triggers a reflection loop and sends agents back to dig deeper |
| 05 | **Decision** | Deterministic scoring: `demand × 0.5 + competition × 0.3 + risk × 0.2` — same inputs always produce the same verdict |
| 06 | **Report** | Synthesizes SWOT, key findings, and a full investor memo |

**Why the Evaluator matters:** most "multi-agent" hackathon projects are really just several prompts chained in a fixed sequence — call A, feed to B, feed to C, done. VentureMind's pipeline isn't fixed-length: the Evaluator can reject its own committee's early findings and send research agents back for another pass before a verdict is allowed to form. That's a real feedback loop, not a relay race.

**Why deterministic scoring matters:** ask most AI tools the same startup idea twice and you'll get two different opinions with two different confidence levels. VentureMind's Decision agent applies a fixed formula on top of the researched inputs — the verdict is reproducible, defensible, and auditable, which is what an actual investment committee needs and what a "vibe check" tool can't offer.

---

## Architecture — One Product, Two Services

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 Frontend  (Vercel)                   │
│  Premium SaaS UI · shadcn/ui · TypeScript        │
│  → POST /api/analyze (proxied to backend)        │
└─────────────────────┬───────────────────────────┘
                      │ HTTP JSON
┌─────────────────────▼───────────────────────────┐
│  FastAPI Backend  (Render / Railway / VPS)       │
│  api_server.py → POST /analyze → ResearchRunResult│
│  6 Python agents · Groq LLM · Serper live search │
└───────────────────────────────────────────────────┘
```

**No backend? No problem.** If `NEXT_PUBLIC_API_URL` isn't set, the frontend runs in demo mode — the full UI, with illustrative analysis, so anyone can experience the product with zero setup and zero API keys. Judges never see a broken build.

A standalone Streamlit UI (`app.py`) ships alongside the Next.js frontend for anyone who wants the Python-only experience with no Node.js at all.

---

## Quick Start — Local Full Stack

**1. Clone and install**
```bash
git clone https://github.com/code-withkrishna/VentureMind-AI
cd VentureMind-AI

pip install -r requirements.txt   # Python backend
npm install                      # Next.js frontend
```

**2. Set API keys**
```bash
cp api.env.example api.env
# add GROQ_API_KEY and SERPER_API_KEY
```
- Groq (free): [console.groq.com](https://console.groq.com) — model `llama-3.3-70b-versatile`
- Serper (free, 2,500 searches/month): [serper.dev](https://serper.dev)

**3. Start the backend**
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
# → http://localhost:8000  (docs at /docs)
```

**4. Start the frontend**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/analyze npm run dev
# → http://localhost:3000
```

**Or, Python-only in 5 minutes, no Node.js:**
```bash
pip install -r requirements.txt
cp api.env.example api.env
streamlit run app.py
# → http://localhost:8501
```

---

## Production Deployment

**Backend → Render (free tier)**
1. [render.com](https://render.com) → New Web Service → connect this repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
4. Health check path: `/health`
5. Environment variables: `GROQ_API_KEY`, `SERPER_API_KEY`, `FRONTEND_URL`, `ENVIRONMENT=production`

**Frontend → Vercel (free tier)**
1. [vercel.com](https://vercel.com) → New Project → import repo (Next.js auto-detected)
2. Environment variable: `NEXT_PUBLIC_API_URL=<your-render-url>/analyze`
3. Deploy.

**Streamlit-only deployment**
1. Push to GitHub
2. [share.streamlit.io](https://share.streamlit.io) → New app → entry point `app.py`
3. Add secrets: `GROQ_API_KEY`, `SERPER_API_KEY`

---

## Project Structure

```
├── api_server.py          FastAPI server — entry point for the Next.js frontend
├── app.py                 Standalone Streamlit UI (no Node.js needed)
├── main.py                CLI runner
├── requirements.txt       Python dependencies (fastapi + uvicorn included)
├── agents/                The 6 specialist agents
├── core/                  Orchestrator, models, config, providers
├── memory/                SQLite run history
├── tools/                 Search and calculator tools
├── ui/                    Streamlit rendering module
├── utils/                 PDF generator, scenario engine
└── src/                   Next.js 14 frontend
    ├── app/
    │   ├── api/analyze/route.ts   Proxies to ANALYZE_API_URL
    │   └── page.tsx               Main UI + demo mode fallback
    ├── components/
    │   ├── ui/                    shadcn/ui primitives
    │   └── venturemind/           Product components
    └── lib/utils.ts               Mock generator + utilities
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Python backend | Groq LLM key |
| `SERPER_API_KEY` | ✅ Python backend | Live search key |
| `NEXT_PUBLIC_API_URL` | Next.js only | URL of the `api_server.py` analyze endpoint |
| `ANALYZE_API_KEY` | Optional | Bearer token if the backend is auth-protected |

---

## What's Next

- Scenario studio: run the same idea through 5 investor-persona lenses (already scaffolded via the scenario engine in `utils/`) and surface it in the main UI, not just the PDF export
- Expose the reflection-loop trace in the UI — show *which* agent rejected the first pass and why, turning the quality gate from a backend detail into a visible trust signal
- Persist run history (already stored in `memory/`) as a comparable dashboard, so a founder can re-run an idea after a pivot and see the verdict shift

---

*VentureMind is decision support for early-stage ideas — a fast, structured second opinion before you spend months and money finding out the hard way.*
