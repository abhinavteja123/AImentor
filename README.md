# AI Life Mentor

**An AI-powered career mentorship platform for students and early-career professionals.**

Upload your resume once, define your target role, and the platform builds a personalized week-by-week learning roadmap, flags your skill gaps, keeps a 24/7 AI chat mentor in context, and generates an ATS-optimized PDF resume — all from a single profile.

---

## Table of Contents

1. [Why This Exists](#1-why-this-exists)
2. [Feature Overview](#2-feature-overview)
3. [Architecture](#3-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Getting Started](#6-getting-started)
   - [Docker (recommended)](#docker-recommended)
   - [Local (no Docker)](#local-no-docker)
7. [Environment Variables](#7-environment-variables)
8. [Database Setup](#8-database-setup)
9. [API Reference](#9-api-reference)
10. [Resume PDF System](#10-resume-pdf-system)
11. [LLM Provider Chain](#11-llm-provider-chain)
12. [Testing](#12-testing)
13. [Deployment](#13-deployment)
14. [Observability & Logs](#14-observability--logs)
15. [Troubleshooting](#15-troubleshooting)
16. [Contributing](#16-contributing)
17. [License](#17-license)

---

## 1. Why This Exists

Students and early-career professionals face three problems simultaneously:

| Problem | Impact |
|---|---|
| Fragmented tools (courses, chatbots, resume builders work in silos) | Lost time switching contexts; inconsistent progress |
| No personalized learning path based on *your* current skills | Generic content that doesn't close the right gaps |
| Resumes that don't reflect continuous learning | Missed opportunities with ATS-unfriendly, static documents |

**AI Life Mentor** addresses all three with one unified platform: your profile is the single source of truth, the roadmap adapts to your skills, the mentor remembers every conversation, and the resume auto-updates from your profile.

---

## 2. Feature Overview

### Profile Autofill from Resume
Upload any text-based PDF resume. The backend extracts 17 structured fields (education, experience, projects, certifications, skills, and contact info) via LLM. You review the suggestions, edit if needed, and confirm — no manual re-typing.

### AI-Generated Learning Roadmaps
After onboarding, the platform generates a phased week-by-week curriculum tailored to:
- Your **current skill set** (extracted from profile + self-assessed proficiency)
- Your **target role** (e.g., "Machine Learning Engineer", "Full Stack Developer")
- Your **timeline** (dynamic duration calculated by the LLM based on the gap)

Each task includes resource links. The roadmap uses a fallback chain: primary LLM → per-skill curriculum provider → hardcoded baseline plan.

### Skill Gap Analysis
AI-powered analysis that compares your current skills against a role's requirements. Returns:
- Missing skills with priority ranking
- Proficiency gap for skills you already have
- Recommended actions for each gap

### AI Chat Mentor
Persistent session-based chat mentor. Each conversation carries full session context so the AI remembers what you discussed, your goals, and your progress. Built on top of the same LLM fallback chain with structured system prompts per user profile.

### ATS Resume Builder
- Generates a resume directly from your profile data (education, experience, projects, skills, certifications, extracurriculars)
- Compiled to PDF via **pdflatex** (Jake's Resume LaTeX template) — produces genuinely ATS-compatible output
- Multi-version support: create tailored drafts per job application, each with its own PDF download
- One-click **Sync from Profile** keeps resume up to date as your profile evolves
- **Job tailoring**: paste a job description, get a tailored summary + match score + suggested improvements
- AI-powered ATS section optimizer for bullet points and summaries

### Progress Tracking
- Per-task completion state (complete / skip) with streak tracking
- Weekly activity view
- Achievements system
- Completion percentage per roadmap phase

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Browser (Client)                           │
│                    Next.js 14  ·  React 18  ·  TypeScript           │
│                                                                     │
│   /onboarding   /dashboard   /profile   /roadmap   /resume   /chat │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ REST + JSON  (Axios + JWT)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                            │
│                    Python 3.11  ·  SQLAlchemy 2  ·  Alembic         │
│                                                                     │
│  /api/v1/auth   /profile   /skills   /roadmap   /resume   /mentor  │
│                                                                     │
│   ┌─────────────┐   ┌──────────────┐   ┌───────────────────────┐  │
│   │ AuthService │   │ProfileService│   │    ResumeService       │  │
│   └─────────────┘   └──────────────┘   │  + LaTeXResumeGen     │  │
│   ┌─────────────────────────────────┐  └───────────────────────┘  │
│   │          LLMClient              │                              │
│   │  FallbackChain: Groq → Cerebras → Gemini                      │
│   └─────────────────────────────────┘                              │
└──────────┬───────────────────────────┬──────────────────────────────┘
           │                           │
           ▼                           ▼
   ┌───────────────┐         ┌──────────────────┐
   │  PostgreSQL   │         │  Redis           │
   │  (Supabase)   │         │  (Upstash)       │
   │  All app data │         │  Session cache   │
   └───────────────┘         └──────────────────┘
```

**Data flow — resume export:**
```
User clicks "Download PDF"
  → backend reads Resume row (JSONB fields)
  → _prepare_resume_data_for_export() normalises all list fields
  → LaTeXResumeGenerator.generate_complete_resume() produces .tex
  → pdflatex compiles .tex → .pdf
  → base64-encoded PDF returned to browser
  → browser triggers file download
```

---

## 4. Tech Stack

### Backend
| Component | Technology |
|---|---|
| Web framework | FastAPI 0.109 |
| Runtime | Python 3.11 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| LLM HTTP | httpx (direct REST, no heavy SDK for Groq/Cerebras) |
| LLM Google | google-generativeai |
| PDF parsing | pypdf |
| PDF generation | pdflatex (LaTeX) |
| Caching | Redis (aioredis) |
| Testing | pytest + pytest-asyncio |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| UI library | React 18 + TypeScript |
| Styling | TailwindCSS + Radix UI primitives |
| State | Zustand (auth + global) |
| Data fetching | Axios + React Query |
| Animations | Framer Motion |
| Charts | Recharts |
| Forms | React Hook Form + Zod |

### Infrastructure
| Component | Technology |
|---|---|
| Database | PostgreSQL 15 (Supabase for hosted) |
| Cache | Redis 7 (Upstash for hosted) |
| Containers | Docker + Docker Compose |
| Deployment | Vercel (frontend) + any Docker host (backend) |

---

## 5. Project Structure

```
AImentor/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, CORS, lifespan
│   │   ├── config.py                # Pydantic settings (reads from .env)
│   │   ├── database/
│   │   │   ├── postgres.py          # Async SQLAlchemy engine + session factory
│   │   │   └── redis_client.py      # Redis connection pool
│   │   ├── api/v1/
│   │   │   ├── auth.py              # Register, login, refresh, logout
│   │   │   ├── profile.py           # Onboarding, profile CRUD, resume-parse upload
│   │   │   ├── skills.py            # Skill master list, user skills, gap analysis
│   │   │   ├── roadmap.py           # Generate, fetch, weekly view, regenerate
│   │   │   ├── resume.py            # Resume CRUD, versioning, export, ATS tools
│   │   │   ├── mentor.py            # Chat sessions + history
│   │   │   └── progress.py          # Task completion, stats, achievements
│   │   ├── models/                  # SQLAlchemy declarative models
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── skill.py             # SkillMaster + UserSkill + RoleTemplate
│   │   │   ├── roadmap.py           # Roadmap + RoadmapTask
│   │   │   ├── resume.py            # Resume (JSONB columns per section)
│   │   │   ├── progress.py
│   │   │   └── chat_session.py
│   │   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── ai/
│   │   │   │   ├── llm_provider.py      # Groq/Cerebras/Gemini + FallbackChain
│   │   │   │   ├── llm_client.py        # Stable facade (generate_completion, chat_completion, …)
│   │   │   │   ├── skill_analyzer.py    # AI skill-gap analysis
│   │   │   │   ├── roadmap_generator.py # AI roadmap + curriculum generation
│   │   │   │   ├── curriculum_provider.py  # Per-skill curriculum with fallback
│   │   │   │   └── chat_engine.py       # Session-aware chat
│   │   │   ├── latex/
│   │   │   │   └── latex_compiler.py    # LaTeXResumeGenerator + LaTeXCompiler
│   │   │   ├── resume_parser.py         # PDF → profile JSON (LLM extraction)
│   │   │   ├── resume_service.py        # Resume CRUD, sync, export, versioning
│   │   │   ├── profile_service.py
│   │   │   ├── roadmap_service.py
│   │   │   ├── skill_service.py
│   │   │   ├── progress_service.py
│   │   │   └── auth_service.py
│   │   └── utils/
│   │       └── security.py          # JWT encode/decode, get_current_user
│   ├── alembic/                     # DB migration scripts
│   ├── tests/                       # pytest suite (unit + integration)
│   ├── scripts/                     # Seed data, migration helpers
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/
│   ├── app/                         # Next.js App Router
│   │   ├── page.tsx                 # Landing page
│   │   ├── login/
│   │   ├── register/
│   │   ├── onboarding/              # 6-step onboarding (goal, skills, education, …)
│   │   └── dashboard/
│   │       ├── page.tsx             # Dashboard home
│   │       ├── profile/             # Profile view/edit + resume upload
│   │       ├── roadmap/             # Weekly roadmap view + task management
│   │       ├── resume/              # Resume builder, versions, export
│   │       ├── skills/              # Skill library + gap analysis
│   │       ├── chat/                # AI chat mentor interface
│   │       └── progress/            # Progress stats + achievements
│   ├── components/
│   │   ├── resume/
│   │   │   ├── ResumePreview.tsx    # Read-only resume preview card
│   │   │   ├── EditResumeForm.tsx   # Full resume editor (accordion sections)
│   │   │   ├── ResumeDataForm.tsx   # Missing-data collection wizard
│   │   │   ├── VersionManager.tsx   # Draft/version switcher
│   │   │   └── JobTailoringPanel.tsx  # Job-description tailoring UI
│   │   ├── layout/                  # Sidebar, navbar, layout shell
│   │   └── ui/                      # shadcn/ui primitives
│   ├── lib/
│   │   ├── api.ts                   # Axios instance + resumeApi / profileApi / … namespaces
│   │   ├── store.ts                 # Zustand auth store
│   │   └── utils.ts                 # cn() helper
│   ├── package.json
│   ├── next.config.js
│   └── Dockerfile
│
├── docker-compose.yml               # postgres + redis + backend + frontend
├── docker-compose.override.yml      # Local dev overrides (hot reload)
├── .env.example                     # Root env template (Docker vars)
├── supabase_schema.sql              # Initial schema for Supabase-hosted Postgres
├── run-migration.sh / .bat          # Quick Alembic upgrade wrapper
├── start.sh / start.bat             # One-command local start
└── CLAUDE.md                        # AI tool instructions (code-review-graph MCP)
```

---

## 6. Getting Started

### Docker (recommended)

**Requires:** Docker ≥ 24 and Docker Compose v2.

```bash
# 1. Clone
git clone <repo-url>
cd AImentor

# 2. Create root env file
cp .env.example .env
# Edit .env — must set at minimum:
#   POSTGRES_PASSWORD=<strong-random>
#   (frontend will talk to backend at http://localhost:8000)

# 3. Create backend env file
cp backend/.env.example backend/.env
# Edit backend/.env — must set:
#   JWT_SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(64))">
#   DATABASE_URL=postgresql+asyncpg://postgres:<POSTGRES_PASSWORD>@postgres:5432/ai_mentor
#   REDIS_URL=redis://redis:6379
#   At least one LLM key: GROQ_API_KEY or CEREBRAS_API_KEY or GOOGLE_API_KEY

# 4. Build and start all services
docker-compose up --build

# Services:
#   Frontend  → http://localhost:3000
#   Backend   → http://localhost:8000
#   API docs  → http://localhost:8000/docs
#   Swagger   → http://localhost:8000/redoc
```

The backend container runs Alembic migrations on startup. PostgreSQL and Redis must be healthy before the backend starts (enforced by `depends_on` health checks).

---

### Local (no Docker)

**Requires:** Python 3.11, Node 18+, PostgreSQL 15 running locally, Redis 7 running locally.

#### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate          # Windows
# source venv/bin/activate            # Mac/Linux

# Install dependencies
pip install -r app/requirements.txt

# Set up .env
cp .env.example .env
# Edit .env with your local DB / Redis URLs and API keys

# Run database migrations
alembic upgrade head

# Start dev server (auto-reload)
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local (if needed for custom API URL)
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
# → http://localhost:3000
```

---

## 7. Environment Variables

### Root `.env` (consumed by `docker-compose.yml` only)

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `ai_mentor` | PostgreSQL database name |
| `POSTGRES_USER` | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | *(required)* | PostgreSQL password |
| `DEBUG` | `true` | Enable verbose logging |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

### `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:pass@host:port/db` |
| `REDIS_URL` | Yes | `redis://host:port` |
| `JWT_SECRET_KEY` | Yes | 64-byte random string — generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_ALGORITHM` | No | Default: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: `30` |
| `LLM_PROVIDER` | No | Primary provider: `groq` (default), `cerebras`, or `gemini` |
| `GROQ_API_KEY` | At least one | [console.groq.com](https://console.groq.com) |
| `CEREBRAS_API_KEY` | At least one | [cloud.cerebras.ai](https://cloud.cerebras.ai) |
| `GOOGLE_API_KEY` | At least one | Google AI Studio API key |
| `GROQ_MODEL` | No | Default: `llama-3.3-70b-versatile` |
| `CEREBRAS_MODEL` | No | Default: `llama3.1-70b` |
| `GEMINI_MODEL` | No | Default: `gemini-1.5-flash` |
| `USE_LLM_CURRICULUM` | No | `true` to generate roadmap curriculum via LLM (default on) |
| `CORS_ORIGINS` | No | Override for backend CORS (separate from root .env) |
| `DEBUG` | No | `true` for DEBUG-level logs |

---

## 8. Database Setup

The project uses **PostgreSQL** with **Alembic** for schema migrations.

### Using Docker
Migrations run automatically on container start. No manual action required.

### Using Supabase (hosted)
1. Run `supabase_schema.sql` in the Supabase SQL editor to create the initial schema.
2. Set `DATABASE_URL` to your Supabase connection string (`postgresql+asyncpg://...`).
3. Run `alembic upgrade head` locally to apply any subsequent migrations.

### Manual migration commands

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "add new column"

# Check current revision
alembic current

# Downgrade one step
alembic downgrade -1
```

### Using the quick-start scripts

```bash
# Windows
run-migration.bat

# Mac/Linux
chmod +x run-migration.sh && ./run-migration.sh
```

---

## 9. API Reference

Full interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

### Authentication — `/api/v1/auth`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Create account (email, password, full_name) |
| `POST` | `/login` | Get access + refresh tokens |
| `POST` | `/refresh` | Rotate access token using refresh token |
| `POST` | `/logout` | Invalidate session |
| `GET` | `/me` | Get current authenticated user |

All protected endpoints require `Authorization: Bearer <access_token>`.

### Profile — `/api/v1/profile`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/onboarding` | Save initial onboarding data |
| `GET` | `/me` | Fetch full profile |
| `PUT` | `/update` | Update any profile field |
| `POST` | `/parse-resume` | Upload PDF → get extracted profile JSON (stateless, no DB write) |
| `POST` | `/skills` | Add skills to profile |

### Skills — `/api/v1/skills`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/master` | All skills in the master library |
| `GET` | `/categories` | Skill categories |
| `GET` | `/user-skills` | Current user's skills with proficiency |
| `POST` | `/user-skills` | Add a skill |
| `POST` | `/user-skills/bulk` | Add multiple skills at once |
| `PUT` | `/user-skills/{id}` | Update proficiency |
| `DELETE` | `/user-skills/{id}` | Remove a skill |
| `POST` | `/user-skills/{id}/practice` | Log a practice session |
| `POST` | `/analyze-gap` | AI skill-gap analysis for a target role |
| `GET` | `/recommendations` | AI-recommended skills to learn next |
| `GET` | `/trending` | Trending skills in the market |
| `POST` | `/assess-proficiency` | AI proficiency self-assessment |
| `POST` | `/compare-roles` | Compare skill requirements across roles |

### Roadmap — `/api/v1/roadmap`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate` | Generate a new AI roadmap |
| `GET` | `/current` | Get active roadmap |
| `GET` | `/{roadmap_id}` | Get specific roadmap by ID |
| `GET` | `/{roadmap_id}/week/{week}` | Get a specific week's tasks |
| `PUT` | `/regenerate` | Regenerate roadmap (updates existing) |
| `GET` | `/all` | All roadmaps for the current user |

### Resume — `/api/v1/resume`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate` | Create/update resume from profile data |
| `GET` | `/current` | Get active resume (all sections) |
| `PUT` | `/update` | Update resume sections directly |
| `POST` | `/sync-from-profile` | Sync profile data into resume |
| `POST` | `/regenerate` | Regenerate resume (optionally from profile) |
| `POST` | `/tailor` | Tailor resume for a job description |
| `GET` | `/validate` | Check which sections are complete |
| `POST` | `/optimize-section` | ATS-optimize a section with AI |
| `GET` | `/versions` | All resume versions |
| `POST` | `/versions/create` | Create a new draft version |
| `GET` | `/versions/{id}` | Get a specific version |
| `PUT` | `/versions/{id}` | Update a version's sections |
| `PATCH` | `/versions/{id}/metadata` | Update draft name / job description |
| `POST` | `/versions/{id}/activate` | Set as active version |
| `DELETE` | `/versions/{id}` | Delete a version |
| `GET` | `/export/pdf` | Download compiled PDF |
| `GET` | `/export/latex` | Download raw LaTeX source |
| `POST` | `/validate-latex` | Check LaTeX for syntax errors |
| `GET` | `/export/preview` | Preview export metadata |

### Mentor (Chat) — `/api/v1/mentor`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Send a message, get AI reply |
| `GET` | `/sessions` | List all chat sessions |
| `GET` | `/session/{id}` | Get full session history |
| `DELETE` | `/session/{id}` | Delete a session |

### Progress — `/api/v1/progress`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/task/complete` | Mark a roadmap task as complete |
| `POST` | `/task/skip` | Skip a roadmap task |
| `GET` | `/stats` | Completion %, streaks, total tasks |
| `GET` | `/activity` | Weekly activity log |
| `GET` | `/achievements` | Earned achievements |

---

## 10. Resume PDF System

The PDF generation pipeline converts structured resume data stored in PostgreSQL JSONB columns into a professionally typeset PDF using LaTeX.

### Pipeline

```
Resume row (PostgreSQL JSONB)
  ↓ _prepare_resume_data_for_export()
  ↓   — normalises all list fields via _as_list() (handles string, list, list-of-chars)
  ↓
LaTeXResumeGenerator.generate_complete_resume(resume_data)
  ↓   — generates section-by-section LaTeX source
  ↓   — escapes all special characters (&, %, $, #, _, {, }, ~, ^, \)
  ↓
LaTeXCompiler._sync_compile_to_pdf(latex_source)
  ↓   — writes .tex to tempdir
  ↓   — runs pdflatex -interaction=nonstopmode twice (resolves cross-references)
  ↓   — reads .pdf bytes
  ↓
base64-encoded PDF → browser download
```

### LaTeX Template

Based on Jake's single-column resume template. Custom `\resumeItem`, `\resumeSubheading`, `\resumeProjectHeading` macros for consistent formatting across all sections.

### Sections rendered

| Section | Source field |
|---|---|
| Header / contact | `contact_info` |
| Summary | `summary` |
| Education | `education_section` |
| Experience | `experience_section` (bullets from `bullet_points`) |
| Projects | `projects_section` (bullets from `highlights`) |
| Technical Skills | `technical_skills_section` |
| Certifications | `certifications_section` |
| Extracurricular | `extracurricular_section` |

### Running pdflatex locally

The LaTeX compiler requires `pdflatex` to be on `PATH`. In Docker it is pre-installed. To run locally:

```bash
# Ubuntu / Debian
sudo apt-get install texlive-latex-extra texlive-fonts-recommended

# macOS (Homebrew)
brew install --cask mactex

# Windows
# Install MiKTeX from https://miktex.org/
```

---

## 11. LLM Provider Chain

The platform uses a **three-provider fallback chain** so that rate limits or outages on one provider automatically fall through to the next.

```
Request
  │
  ▼
┌──────────────┐   429 / 5xx / timeout
│  Groq        │ ─────────────────────────►
│  llama-3.3   │                           │
└──────────────┘                           │
                                           ▼
                               ┌──────────────────────┐   429 / 5xx / timeout
                               │  Cerebras            │ ─────────────────────►
                               │  llama3.1-70b        │                       │
                               └──────────────────────┘                       │
                                                                               ▼
                                                                   ┌────────────────────┐
                                                                   │  Gemini            │
                                                                   │  gemini-1.5-flash  │
                                                                   └────────────────────┘
```

- Hard 4xx errors (bad key, invalid request) surface immediately — no fallback.
- 429 / 5xx / network errors trigger the next provider.
- All attempts are logged as structured `llm.attempt` lines (see [Observability](#14-observability--logs)).

To configure which provider is primary, set `LLM_PROVIDER` in `backend/.env`. You must supply at least one API key.

---

## 12. Testing

```bash
cd backend

# Activate virtual environment
source venv/Scripts/activate   # Windows: venv\Scripts\activate

# Run full test suite (quiet mode)
python -m pytest tests/ -q

# Verbose output
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_llm_client_surface.py -v

# With coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database (via aiosqlite) and mocked LLM responses. No real API keys or external services are needed to run the test suite.

### Test files

| File | What it covers |
|---|---|
| `test_llm_client_surface.py` | LLM client interface contracts |
| `test_llm_provider.py` | Fallback chain logic, retry behaviour |
| `test_curriculum_provider.py` | Curriculum generation with fallback |
| `test_chat_engine.py` | Session-aware chat responses |
| `test_security.py` | JWT encode/decode, password hashing |
| `test_config.py` | Settings loading and defaults |

---

## 13. Deployment

### Vercel (Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel --prod
```

Set `NEXT_PUBLIC_API_URL` in your Vercel project environment variables to point at your deployed backend.

See `VERCEL-DEPLOYMENT-GUIDE.md` and `VERCEL-ENV-GUIDE.md` for detailed Vercel-specific steps.

### Backend on any Docker host (Railway, Fly.io, DigitalOcean, etc.)

```bash
# Build backend image
docker build -t ai-mentor-backend ./backend

# Run with env vars
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://..." \
  -e JWT_SECRET_KEY="..." \
  -e GROQ_API_KEY="..." \
  ai-mentor-backend
```

### Supabase + Upstash (recommended for production)

1. Create a Supabase project → copy the connection string as `DATABASE_URL`
2. Create an Upstash Redis instance → copy the URL as `REDIS_URL`
3. Run `supabase_schema.sql` in the Supabase SQL editor
4. Deploy backend container pointing at Supabase + Upstash

### PDF Generation on hosted backend

LaTeX must be installed in the backend container. The included `Dockerfile` already handles this. If you use a custom base image, add:

```dockerfile
RUN apt-get update && apt-get install -y texlive-latex-extra texlive-fonts-recommended
```

---

## 14. Observability & Logs

Every LLM call emits a single structured log line tagged `llm.attempt`:

```
llm.attempt provider=groq     method=complete  outcome=ok         latency_ms=842
llm.attempt provider=groq     method=complete  outcome=rate_limit latency_ms=120 err="..."
llm.attempt provider=cerebras method=complete  outcome=ok         latency_ms=540
llm.attempt provider=gemini   method=chat      outcome=transient  latency_ms=3200 err="..."
```

**Fields:**
- `provider` — which LLM was called
- `method` — `complete` or `chat`
- `outcome` — `ok`, `rate_limit`, `transient`, or `fatal`
- `latency_ms` — wall-clock time for the HTTP round trip
- `err` — first 160 chars of the error message (only present on failure)

**Useful commands:**

```bash
# Follow all LLM calls live
docker-compose logs -f backend | grep "llm.attempt"

# Count rate-limit hits by provider
docker-compose logs backend | grep "rate_limit" | awk '{print $3}' | sort | uniq -c

# Tail last 100 backend lines
docker-compose logs backend --tail=100
```

---

## 15. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| CORS error from `/api/v1/…` | Backend 500 masked as CORS | `docker-compose logs backend --tail=50` — the real error is there |
| Roadmap renders generic content | `USE_LLM_CURRICULUM` not set or no LLM key | Set `USE_LLM_CURRICULUM=true` and verify at least one API key is valid |
| Resume section blank in PDF | Profile data not synced to resume row | Open resume page → **Sync from Profile** |
| PDF compilation fails with LaTeX error | Special character in resume data not escaped | Check the LaTeX source via `/api/v1/resume/export/latex`; look for unescaped `&`, `%`, `#` |
| PDF compilation fails: pdflatex not found | Running locally without LaTeX | Install `texlive-latex-extra` (Linux), MiKTeX (Windows), MacTeX (macOS) |
| Scanned PDF upload returns 422 | pypdf extracts text only | Use a text-based PDF, or paste your resume content as text manually |
| `alembic upgrade head` fails on first run | DB not reachable or schema conflict | Check `DATABASE_URL` is correct and PostgreSQL is running |
| Frontend shows blank page after login | API URL misconfigured | Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` |
| Redis connection fails on startup | Redis not running | Backend starts without Redis (logs a warning); caching disabled but app still works |
| `JWT_SECRET_KEY must be set` error | Missing .env | Copy `backend/.env.example` to `backend/.env` and fill in values |

---

## 16. Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes — keep commits focused and descriptive
4. Run tests: `cd backend && python -m pytest tests/ -q`
5. Run frontend typecheck: `cd frontend && npx tsc --noEmit`
6. Open a pull request with a clear description of what changed and why

Code style:
- Backend: PEP 8, type hints on all public functions
- Frontend: ESLint + Prettier (configured in the repo)
- No new dependencies without justification

---

## 17. License

MIT — see [LICENSE](LICENSE) if present, or use freely with attribution.

---

*Built as a hackathon project — focused on fast iteration, real LLM integration, and production-grade PDF output.*
