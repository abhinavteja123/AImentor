# AImentor

**An open-source AI career-mentor platform with multi-provider LLM
orchestration, semantic ATS scoring, and AgentRAG-Tutor for
Bayesian-tracked adaptive tutoring.**

AImentor unifies five capabilities behind a single Next.js + FastAPI
stack: (1) chained-fallback LLM orchestration over Groq, Cerebras, and
Google Gemini; (2) a hybrid intent classifier evaluated under a
template-disjoint split; (3) an O\*NET-anchored semantic ATS scorer;
(4) **AgentRAG-Tutor** --- the highlighted contribution --- coupling
agentic Corrective RAG, 5-component Bayesian Knowledge Tracing, and a
Proximal Policy Optimization difficulty agent whose state is the live
BKT mastery vector; and (5) a multi-course extension that runs *AI
Fundamentals* and *Operating Systems* concurrently with a shared PPO
checkpoint.

---

## Architecture

```
┌────────────────────────── Frontend (Next.js 14) ──────────────────────────┐
│  Onboarding · Roadmap · Skills · ATS Resume · Mentor Chat · AgentRAG      │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │  REST + JWT
┌──────────────────────────────────┴───────────────────────────────────────┐
│                          Backend (FastAPI)                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ LLM Orches.  │ │ Hybrid Intent│ │ Semantic ATS │ │  AgentRAG-Tutor  │ │
│  │ Groq+Cere+   │ │ Rule + Distil│ │ SBERT + O*NET│ │ CRAG + BKT + PPO │ │
│  │ Gemini chain │ │ BERT         │ │ taxonomy     │ │ (multi-course)   │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘ │
└─────────┼────────────────┼─────────────────┼──────────────────┼──────────┘
          │                │                 │                  │
   ┌──────┴────────────────┴─────────────────┴──────────────────┴───────┐
   │  PostgreSQL (Supabase)  ·  Redis (Upstash)  ·  PPO checkpoint .zip │
   └────────────────────────────────────────────────────────────────────┘
```

---

## Tech stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind, Recharts.
- **Backend**: FastAPI, SQLAlchemy, Alembic, Pydantic v2.
- **Data**: PostgreSQL (Supabase), Redis (Upstash) for JWT blacklist + LLM cache.
- **AI**: Groq, Cerebras, Google Gemini; sentence-transformers; PyTorch + stable-baselines3 + gymnasium for PPO.
- **Deploy**: Vercel (frontend), Render / Fly / Docker (backend).

---

## Quick start

### Prerequisites
- Node.js 18+, Python 3.11+, PostgreSQL 14+ (or Supabase project), Redis (optional).

### 1. Clone and configure
```bash
git clone https://github.com/<your-org>/aimentor.git
cd aimentor
cp .env.example .env
# Fill in: DATABASE_URL, REDIS_URL (optional), GROQ_API_KEY,
# CEREBRAS_API_KEY, GEMINI_API_KEY, JWT_SECRET, NEXT_PUBLIC_API_URL.
```

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r app/requirements.txt
psql "$DATABASE_URL" -f ../supabase_schema.sql
psql "$DATABASE_URL" -f app/migrations/tutor_tables.sql
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
```

### 4. One-shot dev launchers
- Linux/macOS: `./start.sh`
- Windows:     `start.bat`

---

## API surface

Backend listens on `:8000` under `/api/v1`. Key routes:

| Route                          | Purpose                                |
|--------------------------------|----------------------------------------|
| `POST /auth/register`          | Sign-up + JWT issue                    |
| `POST /auth/login`             | JWT issue                              |
| `POST /chat/message`           | Mentor chat (intent-routed)            |
| `POST /resume/score`           | Semantic ATS scoring vs. JD            |
| `POST /tutor/ask`              | AgentRAG-Tutor question (CRAG+BKT+PPO) |
| `POST /tutor/answer`           | Submit answer, drives BKT update       |
| `GET  /tutor/knowledge-state`  | Per-course 5-KC mastery vector         |
| `GET  /tutor/courses`          | Multi-course registry                  |
| `GET  /healthz`                | Liveness probe                         |

Full OpenAPI: `http://localhost:8000/docs`.

---

## Reproducibility

Everything reported in the IEEE paper is reproducible from this repo.

| Artefact                        | Path                                                         |
|---------------------------------|--------------------------------------------------------------|
| Paper source (LaTeX)            | `backend/research/paper/agentrag_tutor_ieee.tex`             |
| PPO checkpoint (V100-trained)   | `backend/models/ppo_agent/final_model.zip`                   |
| 50-test deterministic suite     | `backend/research/tests/test_tutor_runtime.py`               |
| BKT mastery-curve plot script   | `backend/research/scripts/plot_bkt_curves.py`                |
| PPO learning-curve plot script  | `backend/research/scripts/plot_ppo_curve.py`                 |
| Idempotent SQL migration        | `backend/app/migrations/tutor_tables.sql`                    |
| Simulator + 20-persona harness  | `backend/research/simulator/`                                |

Train PPO from scratch (≈30–45 min on a V100, ≈5 min smoke on CPU):
```bash
python -m backend.research.training.train_ppo_tutor --smoke      # smoke
python -m backend.research.training.train_ppo_tutor              # full 500K
```

Run the deterministic test suite (no DB / no network required):
```bash
cd backend && pytest research/tests -q
```

---

## Multi-course architecture

Course registry is keyed on `course_key`. Each course declares: display
name, SQL category, and five `KCSpec` entries (KC name, keyword set,
per-KC BKT parameters). A keyword-disjointness invariant test runs in
CI and rejects keyword collisions across courses (already caught
*frame* — used in both AI semantic-network literature and OS
memory-frame terminology). Adding a new course = ~30 lines in
`backend/app/services/ai/bkt/kc_mapping.py` + 5 anchor rows in the
migration.

---

## Deployment

- **Frontend (Vercel)**: see `VERCEL-DEPLOYMENT-GUIDE.md` and `VERCEL-ENV-GUIDE.md`.
- **Backend (Docker)**: `docker compose up --build`.
- **Database**: Supabase project, apply `supabase_schema.sql` then `backend/app/migrations/tutor_tables.sql`.

---

## Project layout

```
.
├── backend/
│   ├── app/                     # FastAPI service
│   │   ├── api/v1/              # routers
│   │   ├── services/ai/         # tutor_engine, BKT, CRAG, PPO
│   │   └── migrations/          # idempotent SQL
│   ├── research/                # paper, plots, tests, training
│   └── models/ppo_agent/        # checkpoint
├── frontend/                    # Next.js 14 app
│   ├── app/                     # routes (Tutor, Chat, ATS, ...)
│   └── components/tutor/        # KC radar chart
├── docker-compose.yml
├── supabase_schema.sql
└── README.md
```

---

## License

MIT (or replace per your venue's policy).

## Citation

```
@inproceedings{aimentor2026,
  title  = {AImentor: Multi-Provider LLM Orchestration, Semantic ATS Scoring,
            and AgentRAG-Tutor for Bayesian-Tracked Adaptive Tutoring},
  author = {Mariyala, Abhinav Teja and Maddu, Geethik Kumar and
            Kodali, Shashank and Movva, Revanth and Shaik, Akbar Bashee},
  year   = {2026},
  note   = {SRM University AP}
}
```
