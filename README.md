# AImentor

> **A production-grade, open-source AI career-mentor platform with
> multi-provider LLM orchestration, O\*NET-anchored semantic ATS
> scoring, and *AgentRAG-Tutor* — an Intelligent Tutoring System
> coupling agentic Corrective RAG, 5-component Bayesian Knowledge
> Tracing, and a Proximal Policy Optimization difficulty agent whose
> state is the live BKT mastery vector.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)

---

## Table of contents

1. [What is AImentor?](#1-what-is-aimentor)
2. [Headline numbers](#2-headline-numbers)
3. [Feature surfaces (frontend)](#3-feature-surfaces-frontend)
4. [Backend service layers](#4-backend-service-layers)
5. [System architecture](#5-system-architecture)
6. [Tech stack](#6-tech-stack)
7. [Quick start](#7-quick-start)
8. [Environment variables](#8-environment-variables)
9. [Database schema and migrations](#9-database-schema-and-migrations)
10. [API surface](#10-api-surface)
11. [AgentRAG-Tutor in depth](#11-agentrag-tutor-in-depth)
12. [Multi-course architecture](#12-multi-course-architecture)
13. [Reproducibility — paper artefacts](#13-reproducibility--paper-artefacts)
14. [PPO training](#14-ppo-training)
15. [Testing](#15-testing)
16. [Deployment](#16-deployment)
17. [Project layout](#17-project-layout)
18. [Troubleshooting / FAQ](#18-troubleshooting--faq)
19. [Roadmap](#19-roadmap)
20. [Contributing](#20-contributing)
21. [Authors](#21-authors)
22. [Citation](#22-citation)
23. [License](#23-license)
24. [Acknowledgements](#24-acknowledgements)

---

## 1. What is AImentor?

Personalised career mentorship is costly and scarce. AImentor is a
single Next.js + FastAPI application that gives an undergraduate or
early-career professional five normally-disjoint tools behind one
account:

1. **An adaptive AI tutor** that asks Socratic follow-ups, tracks
   per-Knowledge-Component mastery probability, and adjusts question
   difficulty with a reinforcement-learning policy whose state is your
   own learning trajectory.
2. **An LLM orchestration substrate** that chains three providers
   (Groq → Cerebras → Google Gemini) so the chat surface keeps
   answering when any single provider rate-limits, quota-exhausts, or
   content-filters.
3. **A hybrid intent classifier** that gates hand-tuned response
   templates by a rule layer, with a learned classifier evaluated
   under a *template-disjoint* split that exposes the leakage other
   intent benchmarks hide.
4. **An O\*NET-anchored semantic ATS scorer** (sentence-transformer
   + skill-importance weighting) that beats BM25 by +21.2 Spearman
   ρ-points on a 200-pair benchmark.
5. **AI-generated learning roadmaps**, **skill-gap analysis**,
   **progress dashboards**, **resume builder with LaTeX/PDF export**,
   and **streak tracking** — the rest of the user-facing platform.

The headline novelty is **AgentRAG-Tutor**: to our knowledge the first
ITS that combines an agentic CRAG retrieval-correction loop, a 5-KC
BKT tracker with paper-calibrated parameters, and a PPO difficulty
agent whose policy state is the live BKT mastery vector. See
[Section 11](#11-agentrag-tutor-in-depth).

---

## 2. Headline numbers

All numbers are reproducible from this repo (Section 13). Aggregates
are mean ± std over five seeds; CIs are 95% bootstrap from 10⁴
resamples.

| Metric                                           | AImentor                | Best baseline           |
|--------------------------------------------------|-------------------------|-------------------------|
| LLM end-to-end success (chained vs. single Groq) | **0.993**               | 0.844                   |
| ATS Spearman ρ vs. recruiter gold (200-pair)     | **0.820 ± 0.030**       | BM25: 0.452             |
| Tutor hallucination rate (RAGAS, 20 personas)    | **18.0 %**              | Static RAG: 34.3 %      |
| Cross-domain PPO mean reward (AI → OS)           | **1.14 → 1.06**         | n/a (single course)     |
| Pilot N=5 Hake learning gain                     | **59.7 ± 20.6**         | n/a                     |
| Pilot N=5 satisfaction (5-point Likert)          | **4.4 / 5**             | n/a                     |

---

## 3. Feature surfaces (frontend)

The Next.js app exposes seven authenticated dashboard routes:

| Route                       | What it does                                                                                    |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| `/dashboard`                | Landing card grid with progress summary, streak, next-action suggestion                         |
| `/dashboard/profile`        | Onboarding capture: target role, current skills, education, projects                            |
| `/dashboard/roadmap`        | LLM-generated week-by-week learning roadmap, persisted to PostgreSQL                            |
| `/dashboard/skills`         | Skill-gap analysis vs. target role; per-skill mastery + recommended next steps                  |
| `/dashboard/progress`       | Streak calendar, weekly velocity, completion ratios                                             |
| `/dashboard/resume`         | ATS resume builder with PDF + LaTeX export and JD-driven scoring                                |
| `/dashboard/chat`           | Conversational mentor; intent-routed (rule + DistilBERT) into nine handlers                     |
| `/dashboard/tutor`          | **AgentRAG-Tutor** with per-course five-axis mastery radar, follow-up question card, hint flow  |

Public routes: `/`, `/login`, `/register`.

---

## 4. Backend service layers

| Layer                | Module                                                | Purpose                                                         |
|----------------------|-------------------------------------------------------|-----------------------------------------------------------------|
| LLM Orchestration    | `app/services/ai/llm_client.py`, `llm_provider.py`    | Chained-fallback over Groq, Cerebras, Gemini with fault model   |
| Hybrid Intent        | `app/services/ai/chat_engine.py`                      | Rule + DistilBERT, template-disjoint evaluation gate            |
| Semantic ATS Scorer  | `app/services/resume_service.py`, `resume_parser.py`  | SBERT + O\*NET importance weighting, isotonic calibration       |
| AgentRAG-Tutor       | `app/services/ai/tutor_engine.py` + `bkt/`, `rag/`, `adaptive/` | CRAG + 5-KC BKT + PPO inference, MAB fallback         |
| Skill Analyzer       | `app/services/skill_service.py`                       | Resume → target-role skill-gap analysis                         |
| Roadmap Generator    | `app/services/ai/roadmap_generator.py`                | LLM-synthesised week-by-week plan                               |
| Auth                 | `app/services/auth_service.py`                        | JWT + bcrypt + Redis blacklist                                  |
| LaTeX renderer       | `app/services/latex/`                                 | Server-side resume → PDF                                        |

All layers degrade gracefully:

- Redis down → JWT-blacklist + LLM-cache deactivate, the rest of the
  backend continues.
- PPO checkpoint missing → tutor falls back to ε-greedy multi-armed
  bandit; the API response carries `selector: "mab" | "ppo"` so the
  switch is visible end-to-end.
- One LLM provider faulting → next provider in chain is tried; the
  fault is classified by a trace-driven model (rate-limit / quota /
  500 / content-filter).

---

## 5. System architecture

```
┌──────────────────────────────────── USER-FACING SURFACES (Next.js 14) ───────────────────────────────────┐
│  Onboarding   Roadmap   Skills   Progress   Resume + ATS   Mentor Chat   AgentRAG-Tutor (5-KC radar)     │
└──────────────────────────────────────────────┬──────────────────────────────────────────────────────────┘
                                               │  REST + JWT
┌──────────────────────────────────────────────┴──────────────────────────────────────────────────────────┐
│                                       BACKEND SERVICE LAYERS (FastAPI)                                   │
│                                                                                                          │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌───────────────────────┐    │
│  │  LLM Orchestration   │ │   Hybrid Intent      │ │  Semantic ATS Scorer │ │   AgentRAG-Tutor      │    │
│  │  Groq → Cerebras →   │ │  Rule + DistilBERT   │ │  SBERT + O*NET       │ │  CRAG + 5-KC BKT +    │    │
│  │  Gemini chain        │ │  Template-disjoint   │ │  Isotonic calib.     │ │  frozen PPO + MAB     │    │
│  │  Fault classifier    │ │  9 intent classes    │ │  21.2 ρ-pt over BM25 │ │  Multi-course (AI/OS) │    │
│  └─────────┬────────────┘ └──────────┬───────────┘ └──────────┬───────────┘ └──────────┬────────────┘    │
└────────────┼─────────────────────────┼────────────────────────┼────────────────────────┼─────────────────┘
             │                         │                        │                        │
        ┌────┴─────────────────────────┴────────────────────────┴────────────────────────┴──────────┐
        │  PostgreSQL (Supabase)   ·   Redis (Upstash)   ·   PPO checkpoint final_model.zip          │
        │  Per-course Knowledge Bases (1,200 QA pairs / course, 240 per KC)                          │
        └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Tech stack

### Frontend
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Tailwind CSS, shadcn/ui primitives
- **Charts**: Recharts (radar, line, calendar heat-map)
- **State / fetch**: native fetch + custom hooks (no SWR/React-Query lock-in)
- **Auth**: JWT in HTTP-only cookies

### Backend
- **Framework**: FastAPI 0.110+, Pydantic v2, SQLAlchemy 2.0
- **Migrations**: Alembic + idempotent SQL files in `app/migrations/`
- **Async**: `asyncio` + `httpx` for upstream LLM calls
- **Auth**: PyJWT + bcrypt; Redis-backed blacklist on logout

### Data & cache
- **Primary**: PostgreSQL 14+ (Supabase)
- **Cache + JWT blacklist**: Redis (Upstash)

### AI / ML
- **LLM providers**: Groq (Llama-3 70B), Cerebras (Llama-3 70B), Google Gemini Pro
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Intent classifier**: DistilBERT, fine-tuned per release
- **Reinforcement learning**: PyTorch + `stable-baselines3` + `gymnasium`
- **Knowledge tracing**: 4-parameter HMM BKT, paper-calibrated per KC

### Deploy
- **Frontend**: Vercel
- **Backend**: Docker (Dockerfile in `backend/`), Render / Fly / Railway compatible
- **DB**: Supabase Postgres
- **Cache**: Upstash Redis (free tier sufficient for dev)

---

## 7. Quick start

### Prerequisites
- Python **3.11+**
- Node.js **18+**
- PostgreSQL **14+** (or a Supabase project)
- Redis (optional — features degrade gracefully without it)
- API keys: Groq, Cerebras, Google Gemini

### 1. Clone & configure
```bash
git clone https://github.com/<your-org>/aimentor.git
cd aimentor
cp .env.example .env
# Edit .env (see Section 8)
```

### 2. Backend
```bash
cd backend
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows (PowerShell or cmd)
venv\Scripts\activate

pip install -r app/requirements.txt
# Optional research deps (PPO trainer, plot scripts):
pip install -r app/requirements-research.txt

# Apply schema
psql "$DATABASE_URL" -f ../supabase_schema.sql
psql "$DATABASE_URL" -f app/migrations/tutor_tables.sql

# Run dev server
uvicorn app.main:app --reload --port 8000
```

OpenAPI docs: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

### 4. One-shot launchers
- Linux / macOS: `./start.sh`     (runs both backend + frontend)
- Windows:       `start.bat`

### 5. Migrations only
```bash
./run-migration.sh         # Linux / macOS
run-migration.bat          # Windows
```

---

## 8. Environment variables

Copy `.env.example` to `.env` and fill in:

### Required
| Variable                  | Example                                           | Used by               |
|---------------------------|---------------------------------------------------|-----------------------|
| `DATABASE_URL`            | `postgresql://user:pw@host:5432/aimentor`         | Backend (SQLAlchemy)  |
| `JWT_SECRET`              | random 32+ char string                            | Backend (auth)        |
| `GROQ_API_KEY`            | from console.groq.com                             | LLM orchestration     |
| `CEREBRAS_API_KEY`        | from cloud.cerebras.ai                            | LLM orchestration     |
| `GEMINI_API_KEY`          | from aistudio.google.com                          | LLM orchestration     |
| `NEXT_PUBLIC_API_URL`     | `http://localhost:8000`                           | Frontend              |

### Optional
| Variable                  | Default                                           | Effect                                   |
|---------------------------|---------------------------------------------------|------------------------------------------|
| `REDIS_URL`               | unset                                             | Disables JWT blacklist + LLM cache       |
| `PPO_MODEL_PATH`          | `backend/models/ppo_agent/final_model.zip`        | Override checkpoint path                 |
| `LLM_CACHE_TTL_SECONDS`   | `3600`                                            | Cached LLM-call lifetime                 |
| `BKT_MASTERY_THRESHOLD`   | `0.95`                                            | Per-paper Section 5.2.3 cutoff           |
| `LOG_LEVEL`               | `INFO`                                            | Backend logger verbosity                 |

---

## 9. Database schema and migrations

### Files
- `supabase_schema.sql` — base schema (users, profiles, roadmaps, skills, resumes, sessions).
- `backend/app/migrations/tutor_tables.sql` — additive, **idempotent** tutor schema (knowledge_states, kc_interactions, tutor_sessions, KC anchors).

### Apply order
```bash
psql "$DATABASE_URL" -f supabase_schema.sql
psql "$DATABASE_URL" -f backend/app/migrations/tutor_tables.sql
```

Both scripts use `IF NOT EXISTS` and `ON CONFLICT DO NOTHING`, so
re-running them is safe. KC anchor seeding is idempotent — re-running
will not duplicate the 5+5 anchor skills.

### Key tables (tutor module)
| Table              | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| `skills_master`    | Anchor skills (5 per course) + general skill catalogue       |
| `knowledge_states` | Per-(user, skill) BKT row: `p_init`, `p_learn`, `p_guess`, `p_slip`, `p_mastery` |
| `kc_interactions`  | One row per question/answer turn, drives BKT-AUC computation |
| `tutor_sessions`   | Session-scope metadata (start, last_step, course_key)        |

---

## 10. API surface

All routes live under `/api/v1`. Authentication is JWT in
`Authorization: Bearer <token>` (or HTTP-only cookie on the web
client).

### Auth (`/auth`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| POST   | `/register`         | Create account, return JWT       |
| POST   | `/login`            | Issue JWT                        |
| POST   | `/logout`           | Blacklist JWT (Redis-backed)     |
| GET    | `/me`               | Current user                     |

### Profile / onboarding (`/profile`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| GET    | `/`                 | Get profile                      |
| PUT    | `/`                 | Update target role + skills      |

### Roadmap (`/roadmap`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| GET    | `/`                 | Persisted roadmap                |
| POST   | `/generate`         | Generate via LLM                 |
| PATCH  | `/week/:n`          | Mark week complete               |

### Skills (`/skills`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| GET    | `/`                 | User's skills + gaps             |
| POST   | `/analyze`          | Re-run gap analysis              |

### Progress (`/progress`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| GET    | `/streak`           | Streak calendar                  |
| GET    | `/velocity`         | Weekly completion velocity       |

### Resume / ATS (`/resume`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| POST   | `/parse`            | Parse uploaded resume            |
| POST   | `/score`            | Score resume vs. JD              |
| POST   | `/build`            | Generate resume PDF + LaTeX      |
| GET    | `/export/:id.pdf`   | Download PDF                     |

### Mentor chat (`/mentor`)
| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| POST   | `/chat`             | Intent-routed conversational reply |
| GET    | `/history`          | Past sessions                    |

### AgentRAG-Tutor (`/tutor`)
| Method | Path                  | Purpose                                          |
|--------|-----------------------|--------------------------------------------------|
| GET    | `/courses`            | List registered courses                          |
| POST   | `/ask`                | Ask question → CRAG + Socratic generation        |
| POST   | `/answer`             | Submit answer → BKT update + next-difficulty PPO |
| GET    | `/knowledge-state`    | 5-KC mastery vector (per course)                 |
| GET    | `/session/:id`        | Replay session turns                             |
| POST   | `/hint`               | One-shot hint without revealing answer           |
| GET    | `/export`             | JSON-Lines export of session (for pilots)        |
| POST   | `/feedback`           | Likert + free-text on tutor turn                 |

Full machine-readable spec at `/docs` (Swagger UI) or `/redoc`.

---

## 11. AgentRAG-Tutor in depth

A tutoring turn comprises three phases.

### Phase 1 — CRAG Retrieval
1. Top-k=5 retrieval from the per-course knowledge base.
2. **LLM-as-evaluator** scores aggregate relevance σ ∈ [0, 1] in JSON mode.
3. Three-action policy on σ:
   - σ ≥ 0.6 → **CORRECT**: decompose-and-recompose only.
   - 0.3 ≤ σ < 0.6 → **AMBIGUOUS**: glossary expansion + re-retrieve, then recompose.
   - σ < 0.3 → **INCORRECT**: unit-summary fallback.

### Phase 2 — Socratic Generation
- Prompt instructs LLM to: acknowledge → grounded explanation → one
  example → one *guiding follow-up question* (never reveal the
  answer).
- Self-evaluation step rates accuracy / clarity / completeness /
  engagement; quality < 0.7 triggers a refinement pass.

### Phase 3 — Adaptation
- Student answers the follow-up.
- LLM-as-judge returns `{is_correct, partial_credit, feedback,
  correct_answer}` in JSON mode.
- 5-KC BKT update (per-KC paper-calibrated parameters from Table II
  of the paper):

  ```
  P(L_t^k | 1) = P(L^k_{t-1})(1-P_S) /
                 (P(L^k_{t-1})(1-P_S) + (1-P(L^k_{t-1}))P_G)

  P(L_t^k | 0) = P(L^k_{t-1})P_S /
                 (P(L^k_{t-1})P_S + (1-P(L^k_{t-1}))(1-P_G))

  P(L_{t+1}^k) = P(L_t^k|o) + (1-P(L_t^k|o))P_T
  ```

  A KC is **mastered** once `P(L_t^k) ≥ 0.95`.

- The 5-vector mastery + normalised session step τ = t/T form the
  6-D state s_t ∈ ℝ⁶ consumed by the **frozen PPO policy**:
  - Policy: MLP [64, 64]
  - Action a_t ∈ {0,…,4} → difficulty d_t = a_t + 1 ∈ {1,…,5}
  - Reward (training only): Σ_k [P(L_{t+1}^k) − P(L_t^k)] − λ·max(0, 3−d_t), λ = 0.05
- If no checkpoint loaded or question off-curriculum: ε-greedy MAB
  fallback. The selector is surfaced in the API response
  (`selector: "ppo" | "mab"`) and as a chip in the frontend.

### Inference contract
The PPO policy is **read-only at runtime**. We do not perform online
fine-tuning so BKT-AUC and learning gain remain reproducible across
users. The MAB tracks per-arm reward purely for analytics.

---

## 12. Multi-course architecture

Courses are declared in
`backend/app/services/ai/bkt/kc_mapping.py` via a runtime
`COURSE_REGISTRY` keyed on `course_key`. Each entry declares:

```python
COURSE_REGISTRY = {
  "ai_fundamentals": CourseSpec(
      display_name="AI Fundamentals",
      sql_category="AI Fundamentals",
      kcs=[
        KCSpec(name="AI Agents & ML Intro",  keywords={...}, p_l0=0.35, p_t=0.20, p_g=0.25, p_s=0.10),
        KCSpec(name="Search & CSP",          keywords={...}, p_l0=0.20, p_t=0.15, p_g=0.20, p_s=0.10),
        KCSpec(name="Knowledge Representation",keywords={...}, p_l0=0.25, p_t=0.18, p_g=0.22, p_s=0.08),
        KCSpec(name="Planning & Heuristics", keywords={...}, p_l0=0.20, p_t=0.12, p_g=0.18, p_s=0.10),
        KCSpec(name="Learning & Game AI",    keywords={...}, p_l0=0.15, p_t=0.10, p_g=0.20, p_s=0.12),
      ]),
  "operating_systems": CourseSpec(
      display_name="Operating Systems",
      sql_category="Operating Systems",
      kcs=[ ...Processes, CPU Scheduling, Memory, Concurrency, FS&IO... ]),
}
```

A **keyword-disjointness invariant test** runs on every CI pass: no
keyword may appear in more than one course's keyword set. The test
already caught a real collision (the term *frame*, used both in AI
semantic-network literature and OS memory-frame terminology).

The PPO observation contract is domain-agnostic (5 KCs + τ), so a
single trained checkpoint serves both courses. This is a built-in
cross-domain ablation; mean reward 1.14 (AI) → 1.06 (OS) is reported
in the paper (Table XII).

**Adding a new course**: add a `CourseSpec` to `COURSE_REGISTRY`,
seed 5 anchor skills via the migration, and ship 1,200 QA pairs (240
per KC) under `backend/data/courses/<course_key>/`. No PPO retraining
required.

---

## 13. Reproducibility — paper artefacts

Everything claimed in the IEEE paper is reproducible from this repo.

| Artefact                                | Path                                                       |
|-----------------------------------------|------------------------------------------------------------|
| Paper source (LaTeX)                    | `backend/research/paper/agentrag_tutor_ieee.tex`           |
| Compiled PDF (built locally / Overleaf) | not committed — see `.gitignore`                           |
| PPO checkpoint (V100-trained, 500 K)    | `backend/models/ppo_agent/final_model.zip`                 |
| 50-test deterministic suite             | `backend/research/tests/test_tutor_runtime.py`             |
| BKT mastery-curve plot script (Fig. 7)  | `backend/research/scripts/plot_bkt_curves.py`              |
| PPO learning-curve plot script (Fig. 8) | `backend/research/scripts/plot_ppo_curve.py`               |
| Idempotent SQL migration                | `backend/app/migrations/tutor_tables.sql`                  |
| 20-persona simulator harness            | `backend/research/simulator/`                              |
| Per-persona CSV (paper Table IX)        | `backend/research/results/tables/user_study_individual.csv`|
| PPO training notebook (Colab-ready)     | `backend/research/training/train_ppo_tutor.ipynb`          |

**Compile the paper** (LaTeX with `IEEEtran.cls`):
```bash
cd backend/research/paper
pdflatex agentrag_tutor_ieee.tex
bibtex   agentrag_tutor_ieee
pdflatex agentrag_tutor_ieee.tex
pdflatex agentrag_tutor_ieee.tex
```

**Regenerate Fig. 7 + Fig. 8**:
```bash
python backend/research/scripts/plot_bkt_curves.py
python backend/research/scripts/plot_ppo_curve.py
# Outputs land in backend/research/results/figures/
```

---

## 14. PPO training

### Smoke test (~5 min on CPU)
```bash
python -m backend.research.training.train_ppo_tutor --smoke
```
Produces `backend/models/ppo_agent/final_model.zip` after 50 K steps.
Mean episode reward typically ~0.78.

### Full training (~30–45 min on Tesla V100)
```bash
python -m backend.research.training.train_ppo_tutor
```
500 K steps, four vectorised `TutoringEnv` instances, mean episode
reward at convergence ≈ **1.14**.

### Hyperparameters (paper Table III)
| Parameter         | Value          |
|-------------------|----------------|
| learning rate     | 3 × 10⁻⁴       |
| γ                 | 0.99           |
| n_steps           | 2048           |
| GAE λ             | 0.95           |
| batch size        | 64             |
| clip range        | 0.2            |
| n_epochs          | 10             |
| ent. coef         | 0.01           |
| total timesteps   | 500,000        |
| policy            | MLP [64, 64]   |

### TensorBoard
```bash
tensorboard --logdir backend/research/tensorboard_logs
```

---

## 15. Testing

### Backend deterministic suite (no DB / no network)
```bash
cd backend
pytest research/tests -q          # 50 tests, ~10 s
```

### Backend integration (requires DB)
```bash
cd backend
pytest tests -q
```

### Frontend
```bash
cd frontend
npm test
npm run typecheck
npm run lint
```

### CI invariants
- `tests/test_keyword_disjointness.py` — no keyword may appear in more
  than one course.
- `tests/test_bkt_params_persisted.py` — paper params must be written
  on first knowledge-state row creation.
- `tests/test_ppo_inference_only.py` — checkpoint never modified at
  runtime.

---

## 16. Deployment

### Frontend → Vercel
```bash
cd frontend
vercel --prod
```
See `VERCEL-DEPLOYMENT-GUIDE.md` and `VERCEL-ENV-GUIDE.md` for the
exact env-var matrix.

### Backend → Docker (any VPS / Render / Fly)
```bash
docker compose up --build
```
The provided `docker-compose.yml` plus `docker-compose.override.yml`
bring up FastAPI + Postgres + Redis locally. Production: drop the
`override` file and point `DATABASE_URL` / `REDIS_URL` at managed
services.

### Database → Supabase
1. Create a Supabase project.
2. In SQL editor, run `supabase_schema.sql`, then
   `backend/app/migrations/tutor_tables.sql`.
3. Set `DATABASE_URL` to the connection-pooler URI.
4. Verify with: `SELECT skill_name FROM skills_master WHERE category IN ('AI Fundamentals','Operating Systems');` — expect 10 rows.

### Cache → Upstash Redis
1. Create an Upstash Redis database.
2. Set `REDIS_URL` to the `rediss://...` URI.
3. Backend auto-detects and enables JWT blacklist + LLM cache.

---

## 17. Project layout

```
.
├── backend/
│   ├── app/                              # FastAPI service
│   │   ├── api/v1/                       # routers (auth, profile, roadmap, ...)
│   │   ├── config.py
│   │   ├── database/                     # Postgres + Redis adapters
│   │   ├── main.py                       # FastAPI entrypoint
│   │   ├── migrations/                   # idempotent SQL
│   │   ├── models/                       # SQLAlchemy ORM
│   │   ├── schemas/                      # Pydantic v2 DTOs
│   │   ├── services/                     # business logic
│   │   │   ├── ai/
│   │   │   │   ├── adaptive/             # PPO agent, MAB difficulty controller
│   │   │   │   ├── bkt/                  # BKT tracker, KC mapping, course registry
│   │   │   │   ├── rag/                  # CRAG evaluator, retriever
│   │   │   │   ├── chat_engine.py
│   │   │   │   ├── llm_client.py
│   │   │   │   ├── llm_provider.py
│   │   │   │   ├── tutor_engine.py       # AgentRAG-Tutor orchestrator
│   │   │   │   ├── roadmap_generator.py
│   │   │   │   └── skill_analyzer.py
│   │   │   ├── auth_service.py
│   │   │   ├── latex/                    # server-side resume → PDF
│   │   │   ├── profile_service.py
│   │   │   ├── progress_service.py
│   │   │   ├── resume_parser.py
│   │   │   ├── resume_service.py
│   │   │   ├── roadmap_service.py
│   │   │   └── skill_service.py
│   │   ├── utils/                        # security, logging, helpers
│   │   ├── requirements.txt
│   │   ├── requirements-research.txt     # PPO trainer + plotting
│   │   └── requirements-gpu.txt          # CUDA torch
│   ├── alembic/                          # versioned migrations
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── models/ppo_agent/                 # final_model.zip checkpoint
│   ├── pytest.ini
│   ├── research/                         # paper, plots, tests, training
│   │   ├── paper/                        # IEEE LaTeX source
│   │   ├── results/                      # figures + CSV tables
│   │   ├── scripts/                      # plot_bkt_curves.py, plot_ppo_curve.py
│   │   ├── simulator/                    # 20-persona BKT-driven simulator
│   │   ├── tests/                        # deterministic suite (50 tests)
│   │   └── training/                     # train_ppo_tutor.{py,ipynb}
│   ├── scripts/                          # ops one-offs (check_db, fix_users)
│   └── tests/                            # integration tests
├── frontend/
│   ├── app/                              # Next.js App Router
│   │   ├── dashboard/
│   │   │   ├── chat/
│   │   │   ├── profile/
│   │   │   ├── progress/
│   │   │   ├── resume/
│   │   │   ├── roadmap/
│   │   │   ├── skills/
│   │   │   └── tutor/                    # AgentRAG-Tutor UI
│   │   ├── login/
│   │   ├── onboarding/
│   │   ├── register/
│   │   └── page.tsx
│   ├── components/
│   │   ├── layout/
│   │   └── tutor/                        # KCRadarChart, follow-up card, hint flow
│   └── lib/                              # api.ts, hooks, utils
├── docker-compose.yml
├── docker-compose.override.yml
├── start.sh / start.bat                  # one-shot dev launchers
├── run-migration.sh / .bat               # apply schema + migrations
├── supabase_schema.sql                   # base schema
├── vercel.json
├── VERCEL-DEPLOYMENT-GUIDE.md
├── VERCEL-ENV-GUIDE.md
├── .env.example
├── .gitignore
└── README.md
```

---

## 18. Troubleshooting / FAQ

**Q: Backend logs `Loaded PPO model from ...`?**
Good — checkpoint is active. Tutor responses will carry `selector:
"ppo"` for AI-curriculum questions.

**Q: Backend logs `No PPO checkpoint found, falling back to MAB`?**
Either set `PPO_MODEL_PATH` to a valid `.zip`, or run the smoke
trainer (Section 14) to produce `backend/models/ppo_agent/final_model.zip`.

**Q: `null value in column "id"` when applying the migration?**
Run `CREATE EXTENSION IF NOT EXISTS pgcrypto;` once on your database
so `gen_random_uuid()` is available, then re-run the migration.

**Q: Redis is down — is the app broken?**
No. JWT blacklist + LLM cache deactivate; everything else continues.
Check `/healthz` to confirm.

**Q: The radar chart shows zero values for all 5 KCs.**
The user has not answered any AI-curriculum questions yet. Mastery
rows are created lazily on the first `/tutor/answer` for that KC.

**Q: Why does my off-curriculum question get tutored but not BKT-tracked?**
By design. Off-curriculum questions still trigger CRAG + Socratic
generation, but the BKT update is skipped because there is no
matching KC. The API response sets `kc_id: null`,
`current_mastery: null`, `selector: "mab"`.

**Q: Can I disable PPO at runtime?**
Set `PPO_MODEL_PATH=/dev/null` (Linux) or remove the checkpoint file.
The tutor will fall back to ε-greedy MAB.

**Q: Where do I see selector switches in the UI?**
Each follow-up question card shows a small chip — `PPO` (blue) or
`MAB` (grey) — next to the difficulty badge.

---

## 19. Roadmap

- [ ] N=20 controlled study at SRM University AP (camera-ready / journal extension).
- [ ] Multi-skill BKT (q-matrix learning) for questions touching ≥2 KCs.
- [ ] Pilot-data-driven recalibration of the simulator's
      difficulty→correctness curve δ(d).
- [ ] Online PPO fine-tuning gated by a safety check (currently
      inference-only).
- [ ] Course #3: Database Systems (5-KC spec drafted).
- [ ] Voice-mode tutor turn (Whisper-large-v3 STT + Cartesia TTS).
- [ ] Single-sign-on (Google OAuth + GitHub OAuth).

---

## 20. Contributing

PRs welcome. Please:
1. Open an issue first for non-trivial changes.
2. Run `pytest research/tests -q` and the keyword-disjointness
   invariant test before opening a PR.
3. Frontend: `npm run typecheck && npm run lint` must pass.
4. Sign your commits.

Code style: Python = `ruff` + `black`; TypeScript = `eslint` +
`prettier`.

---

## 21. Authors

This work was carried out at SRM University AP, Department of CSE
(AI & ML).

| Name                         | Email                             |
|------------------------------|-----------------------------------|
| **M. Abhinav Teja**          | abhinavteja_mariyala@srmap.edu.in |
| **M. Geethik Kumar**         | geethikkumar_maddu@srmap.edu.in   |
| **K. Shashank**              | shashank_kodali@srmap.edu.in      |
| **Revanth M.**               | revanth_movva@srmap.edu.in        |
| **Akbar Bashee Shaik**       | akbarbashee_shaik@srmap.edu.in    |

---

## 22. Citation

If you use this work, please cite:

```bibtex
@inproceedings{aimentor2026,
  title     = {AImentor: A Production-Grade AI Career Mentor with
               Multi-Provider LLM Orchestration, Semantic ATS Scoring,
               and AgentRAG-Tutor for Bayesian-Tracked Adaptive Tutoring},
  author    = {Mariyala, Abhinav Teja and Maddu, Geethik Kumar and
               Kodali, Shashank and Movva, Revanth and Shaik, Akbar Bashee},
  booktitle = {Proceedings of the IEEE Conference (target venue)},
  year      = {2026},
  address   = {Amaravati, India},
  publisher = {IEEE},
  note      = {SRM University AP}
}
```

---

## 23. License

MIT License. See `LICENSE` file (add one if not yet present —
recommended for the open-source claim in the paper).

```
Copyright (c) 2026 The AImentor authors.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the conditions of the MIT license.
```

---

## 24. Acknowledgements

- The **SRM University AP CSE (AI & ML)** faculty for syllabus
  guidance and review.
- The maintainers of `stable-baselines3`, `gymnasium`, `Recharts`,
  `FastAPI`, and `Next.js` for the open-source substrate.
- The authors of CRAG (Yan et al., 2024), classical BKT (Corbett &
  Anderson, 1994), and PPO (Schulman et al., 2017) — the three
  primitives we compose into AgentRAG-Tutor.
- The N=5 pilot participants who made initial external validity
  possible.
