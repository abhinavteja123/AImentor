# AI Life Mentor 🎓

> An intelligent career mentorship platform powered by AI that provides personalized learning paths, skill gap analysis, and 24/7 mentorship support.

[![Tech Stack](https://img.shields.io/badge/Stack-Python%20%7C%20FastAPI%20%7C%20Next.js%20%7C%20AI-blue)](#-tech-stack)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents
- [Problem Statement](#-problem-statement)
- [Architecture](#-architecture-diagram)
- [Tech Stack](#-tech-stack)
- [AI Tools & Strategy](#-ai-tools--prompt-strategy)
- [Features](#-features)
- [Setup Instructions](#-setup-instructions)
- [Build Reproducibility](#-build-reproducibility-instructions)
- [Final Output](#-final-output--demo)
- [Project Structure](#-project-structure)
- [Source Code Overview](#-source-code-documentation)
- [API Documentation](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)
- [Additional Documentation](#-additional-documentation)

---

## 🎯 Problem Statement

In today's rapidly evolving job market, professionals and students face several critical challenges:

1. **Skill Gap Identification**: Difficulty in identifying gaps between current skills and target career requirements
2. **Personalized Learning Paths**: Lack of customized, step-by-step learning roadmaps aligned with career goals
3. **Continuous Mentorship**: Limited access to 24/7 guidance and mentorship due to time and cost constraints
4. **Progress Tracking**: No centralized system to track learning progress and maintain consistency
5. **Resume Optimization**: Challenge in crafting targeted resumes that align with specific job roles

**AI Life Mentor** solves these problems by leveraging artificial intelligence to provide:
- Intelligent skill gap analysis comparing current skills with target job requirements
- AI-generated personalized learning roadmaps with structured milestones
- 24/7 conversational AI mentor for guidance and support
- Automated progress tracking with gamification (streaks, achievements)
- AI-powered resume generation and optimization

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │   Next.js 14 Frontend (React + TypeScript)             │    │
│  │   - App Router  - TailwindCSS  - Zustand State Mgmt   │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────▼─────────────────────────────────────┐
│                         API LAYER                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         FastAPI Backend (Python 3.11)                  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │    │
│  │  │   Auth   │  │  Skills  │  │  Roadmap │           │    │
│  │  │ Service  │  │ Service  │  │ Service  │  ...      │    │
│  │  └──────────┘  └──────────┘  └──────────┘           │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│   PostgreSQL   │  │   MongoDB    │  │     Redis      │
│  (Structured)  │  │ (Documents)  │  │    (Cache)     │
│  - Users       │  │  - Roadmaps  │  │  - Sessions    │
│  - Progress    │  │  - Chat Logs │  │  - Rate Limit  │
│  - Skills      │  │  - Resumes   │  │                │
└────────────────┘  └──────────────┘  └────────────────┘
                            │
                    ┌───────▼───────┐
                    │   AI Layer    │
                    │ ┌───────────┐ │
                    │ │  Google   │ │
                    │ │  Gemini   │ │
                    │ │    API    │ │
                    │ └───────────┘ │
                    │  - Chat       │
                    │  - Analysis   │
                    │  - Generation │
                    └───────────────┘
```

**Data Flow**:
1. User interacts with Next.js frontend
2. Frontend makes REST API calls to FastAPI backend
3. Backend processes requests using service layer
4. Services interact with databases (PostgreSQL/MongoDB/Redis)
5. AI services call Google Gemini API for intelligent features
6. Results flow back through the layers to the user

---

## 🛠️ Tech Stack

### **Frontend**
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **UI Components**: Custom components with Radix UI primitives

### **Backend**
- **Framework**: FastAPI (Python 3.11)
- **API Documentation**: OpenAPI/Swagger (auto-generated)
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Async Runtime**: uvicorn with uvloop

### **Databases**
- **Relational DB**: PostgreSQL 15+ (user data, skills, progress)
- **Document DB**: MongoDB (roadmaps, chat history, resumes)
- **Cache/Session**: Redis (sessions, rate limiting)

### **AI/ML**
- **LLM**: Google Gemini 2.0 Flash
- **Use Cases**: 
  - Skill gap analysis
  - Learning roadmap generation
  - Conversational mentoring
  - Resume generation and optimization

### **Deployment**
- **Platform**: Vercel (Frontend & Backend)
- **Databases**: 
  - Neon (PostgreSQL)
  - MongoDB Atlas
  - Upstash Redis

---

## 🤖 AI Tools & Prompt Strategy

### **AI Tools Used**

1. **Google Gemini 2.0 Flash API**
   - Purpose: Primary LLM for all AI-powered features
   - Models: `gemini-2.0-flash`, `gemini-2.5-flash`
   - Integration: Python `google-generativeai` SDK

2. **GitHub Copilot** (Development Assistant)
   - Code generation and completion
   - Documentation writing
   - Test case generation

### **Prompt Strategy Summary**

Our AI system uses **structured prompt engineering** with the following strategies:

#### 1. **Skill Gap Analysis Prompts**
```
Strategy: Role-based + Structured Output
- Define AI role as "Career Development Expert"
- Provide context: user's current skills + target job role
- Request structured JSON output with gap analysis
- Include examples for consistency
```

#### 2. **Roadmap Generation Prompts**
```
Strategy: Template-based + Iterative Refinement
- Use predefined roadmap structure (phases, milestones, resources)
- Include user's skill level and learning pace
- Request milestone-based breakdown with timeframes
- Specify output format (markdown with structured sections)
```

#### 3. **AI Mentor Chat Prompts**
```
Strategy: Conversational + Context-Aware
- Maintain conversation history (last 10 messages)
- System prompt defines mentor personality and boundaries
- User context injection (current goals, skill level)
- Safety filters for inappropriate requests
```

#### 4. **Resume Generation Prompts**
```
Strategy: Data-driven + Template Filling
- Extract structured data from user profile
- Apply industry-specific formatting templates
- Optimize for ATS (Applicant Tracking Systems)
- Include action verbs and quantifiable achievements
```

**Common Techniques**:
- ✅ Few-shot learning (providing examples)
- ✅ Chain-of-thought reasoning
- ✅ Temperature control (0.7 for creative, 0.3 for factual)
- ✅ Token limit management
- ✅ Streaming responses for better UX

---

## 🚀 Quick Start

### Prerequisites

**Option A: Docker (Recommended - Easiest)**
1. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
2. **Google Gemini API Key** - [Get one here](https://aistudio.google.com/)

**Option B: Manual Setup**
1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/) or use [Neon](https://neon.tech/)
4. **MongoDB** - [Download](https://www.mongodb.com/try/download/community) or use [MongoDB Atlas](https://www.mongodb.com/atlas)
5. **Redis** - [Download](https://redis.io/download/) or use [Upstash](https://upstash.com/)
6. **Google Gemini API Key** - [Get one here](https://aistudio.google.com/)

---

## 🐳 Quick Start with Docker (Recommended)

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd AImentor
```

### 2. Configure environment variables

Create `.env` file in the `backend` directory:

```env
# Google Gemini AI
GOOGLE_API_KEY=your_gemini_api_key_here

# PostgreSQL Database (Docker service name)
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@postgres:5432/ai_mentor

# MongoDB (Docker service name)
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB=ai_mentor

# Redis (Docker service name)
REDIS_URL=redis://redis:6379

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_32_character_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Server Settings
DEBUG=True
CORS_ORIGINS=http://localhost:3000
```

Create `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
Local (no Docker) path:
  # backend  (from repo root)
  cd backend && venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

  # frontend  (separate terminal)
  cd frontend && npm run dev

  Frontend on http://localhost:3000, backend on http://localhost:8000.
  

### 3. Start all services with Docker

```bash
# Build and start all services (backend, frontend, databases)
docker-compose up -d

# View logs
docker-compose logs -f

# Check services are running
docker-compose ps
```

### 4. Initialize the database (first time only)

```bash
# Run database seeding
docker-compose exec backend python -m scripts.seed_database
docker-compose exec backend python -m scripts.seed_skills
```

### 5. Access the application

✅ **Frontend**: http://localhost:3000  
✅ **Backend API**: http://localhost:8000  
✅ **API Docs**: http://localhost:8000/docs

### Stop the application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 📦 Manual Setup (Alternative)

### Backend Setup

### 1. Navigate to backend directory

```bash
cd backend
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Edit the `.env` file with your actual values:

```env
# Google Gemini AI
GOOGLE_API_KEY=your_gemini_api_key_here

# PostgreSQL (use your local or cloud database URL)
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/aimentor

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=aimentor

# Redis
REDIS_URL=redis://localhost:6379

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your_super_secret_key_change_this_in_production
```

### 5. Create PostgreSQL database

```sql
CREATE DATABASE aimentor;
```

### 6. Run the backend server

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. Seed the database (optional but recommended)

```bash
python -m scripts.seed_database
```

The backend will be running at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 🎨 Frontend Setup

### 1. Navigate to frontend directory

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run the development server

```bash
npm run dev
```

The frontend will be running at `http://localhost:3000`

---

## 🗄️ Cloud Database Setup (Production)

For production or if you prefer cloud databases over Docker:

1. **Neon** (PostgreSQL): Free tier with 500MB
   - Create project at https://neon.tech/
   - Get connection string from dashboard

2. **MongoDB Atlas**: Free tier with 512MB
   - Create cluster at https://cloud.mongodb.com/
   - Get connection string from Connect → Drivers

3. **Upstash** (Redis): Free tier with 10K commands/day
   - Create database at https://upstash.com/
   - Get connection URL from database details

---

## 🔑 Getting Google Gemini API Key

1. Go to https://aistudio.google.com/
2. Sign in with your Google account
3. Click "Get API Key" in the left sidebar
4. Create a new API key or use existing one
5. Copy the key to your `.env` file

**Note**: Free tier has quota limits. See [GEMINI-QUOTA-SOLUTION.md](docs/GEMINI-QUOTA-SOLUTION.md) for details.

---

## 📁 Project Structure

```
AImentor/
├── backend/                          # Python FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── config.py                 # Configuration and environment variables
│   │   ├── requirements.txt          # Python dependencies
│   │   ├── api/                      # API endpoints
│   │   │   └── v1/
│   │   │       ├── auth.py          # Authentication endpoints
│   │   │       ├── profile.py       # User profile endpoints
│   │   │       ├── skills.py        # Skills management
│   │   │       ├── roadmap.py       # Learning roadmap endpoints
│   │   │       ├── mentor.py        # AI mentor chat
│   │   │       ├── progress.py      # Progress tracking
│   │   │       └── resume.py        # Resume generation
│   │   ├── database/                 # Database connections
│   │   │   ├── mongodb.py           # MongoDB connection
│   │   │   ├── postgres.py          # PostgreSQL connection
│   │   │   └── redis_client.py      # Redis connection
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── user.py              # User model
│   │   │   ├── skill.py             # Skill model
│   │   │   ├── progress.py          # Progress model
│   │   │   ├── profile.py           # Profile model
│   │   │   ├── roadmap.py           # Roadmap model
│   │   │   └── resume.py            # Resume model
│   │   ├── schemas/                  # Pydantic schemas (DTOs)
│   │   │   ├── user.py
│   │   │   ├── skill.py
│   │   │   ├── roadmap.py
│   │   │   ├── mentor.py
│   │   │   └── resume.py
│   │   ├── services/                 # Business logic layer
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── skill_service.py     # Skills analysis
│   │   │   ├── roadmap_service.py   # Roadmap generation
│   │   │   ├── progress_service.py  # Progress tracking
│   │   │   ├── resume_service.py    # Resume operations
│   │   │   └── ai/                  # AI services
│   │   │       ├── gemini_service.py # Google Gemini integration
│   │   │       ├── chat_service.py   # AI chat functionality
│   │   │       └── prompts.py        # Prompt templates
│   │   └── utils/                    # Utility functions
│   │       ├── security.py           # Security helpers
│   │       └── validators.py         # Input validators
│   ├── scripts/                      # Database scripts
│   │   ├── seed_database.py         # Database seeding
│   │   ├── seed_skills.py           # Skills data seeding
│   │   └── init.sql                 # Initial schema
│   ├── tests/                        # Test suite
│   ├── Dockerfile                    # Docker configuration
│   ├── .env                          # Environment variables
│   └── vercel.json                   # Vercel deployment config
│
├── frontend/                         # Next.js Frontend
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Landing page
│   │   ├── globals.css              # Global styles
│   │   ├── login/                   # Login page
│   │   ├── register/                # Registration page
│   │   ├── onboarding/              # Onboarding flow
│   │   └── dashboard/               # Protected dashboard
│   │       ├── page.tsx             # Dashboard home
│   │       ├── profile/             # Profile management
│   │       ├── skills/              # Skills analysis
│   │       ├── roadmap/             # Learning roadmaps
│   │       ├── chat/                # AI mentor chat
│   │       ├── progress/            # Progress tracking
│   │       └── resume/              # Resume builder
│   ├── components/                   # React components
│   │   ├── layout/
│   │   │   └── DashboardLayout.tsx  # Dashboard layout
│   │   ├── resume/
│   │   │   ├── ResumeDataForm.tsx
│   │   │   ├── EditResumeForm.tsx
│   │   │   └── VersionManager.tsx
│   │   ├── ui/                      # Reusable UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── progress.tsx
│   │   └── providers.tsx            # Context providers
│   ├── lib/                          # Utilities and configurations
│   │   ├── api.ts                   # API client
│   │   ├── store.ts                 # Zustand state management
│   │   └── utils.ts                 # Helper functions
│   ├── public/                       # Static assets
│   ├── Dockerfile                    # Docker configuration
│   ├── next.config.js               # Next.js configuration
│   ├── tailwind.config.ts           # TailwindCSS configuration
│   ├── tsconfig.json                # TypeScript configuration
│   ├── package.json                 # Node dependencies
│   └── vercel.json                  # Vercel deployment config
│
├── docs/                             # Documentation
│   ├── screenshots/                 # Application screenshots
│   ├── AI-MENTOR-IMPLEMENTATION-GUIDE.md
│   ├── MIGRATION-GUIDE.md
│   ├── RESUME-IMPLEMENTATION.md
│   ├── VERCEL-DEPLOYMENT-GUIDE.md
│   └── VERCEL-ENV-GUIDE.md
│
├── scripts/                          # Deployment scripts
│   ├── deploy-vercel.sh
│   ├── deploy-vercel.bat
│   └── setup-vercel-env.sh
│
├── docker-compose.yml               # Docker Compose configuration
├── docker-compose.override.yml      # Local development overrides
├── .gitignore
├── LICENSE
└── README.md                        # This file
```

---

## 🌐 API Endpoints

### Authentication
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/auth/register` | POST | Register new user | No |
| `/api/v1/auth/login` | POST | Login user | No |
| `/api/v1/auth/refresh` | POST | Refresh access token | Yes |
| `/api/v1/auth/logout` | POST | Logout user | Yes |

### Profile
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/profile/onboarding` | POST | Complete user onboarding | Yes |
| `/api/v1/profile/me` | GET | Get current user profile | Yes |
| `/api/v1/profile/update` | PUT | Update user profile | Yes |

### Skills
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/skills/analyze` | POST | Analyze skill gaps | Yes |
| `/api/v1/skills/list` | GET | List available skills | Yes |
| `/api/v1/skills/user` | GET | Get user skills | Yes |

### Roadmap
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/roadmap/generate` | POST | Generate learning roadmap | Yes |
| `/api/v1/roadmap/list` | GET | List user roadmaps | Yes |
| `/api/v1/roadmap/{id}` | GET | Get specific roadmap | Yes |
| `/api/v1/roadmap/{id}/update` | PUT | Update roadmap progress | Yes |

### AI Mentor
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/mentor/chat` | POST | Chat with AI mentor | Yes |
| `/api/v1/mentor/history` | GET | Get chat history | Yes |

### Progress
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/progress/track` | POST | Track milestone completion | Yes |
| `/api/v1/progress/stats` | GET | Get progress statistics | Yes |
| `/api/v1/progress/streak` | GET | Get learning streak | Yes |

### Resume
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/resume/generate` | POST | Generate AI resume | Yes |
| `/api/v1/resume/list` | GET | List user resumes | Yes |
| `/api/v1/resume/{id}` | GET | Get specific resume | Yes |
| `/api/v1/resume/{id}/update` | PUT | Update resume | Yes |
| `/api/v1/resume/{id}/export` | GET | Export resume to PDF | Yes |

📚 **Full API Documentation**: Available at `http://localhost:8000/docs` when running locally

---

## 📖 Source Code Documentation

For detailed information about the source code organization, architecture patterns, and implementation details:

📘 **[Source Code Overview](docs/SOURCE-CODE-OVERVIEW.md)** - Comprehensive guide to:
- Backend architecture and code organization
- Frontend structure and component hierarchy
- Key technologies and design patterns
- Data flow examples
- Security implementation details
- Testing strategy

---

## 📚 Additional Documentation

- 📋 **[Build Reproducibility Guide](docs/BUILD-REPRODUCIBILITY.md)** - Step-by-step checklist for reproducible builds
- 🚀 **[Vercel Deployment Guide](VERCEL-DEPLOYMENT-GUIDE.md)** - Deploy to production on Vercel
- 🔧 **[Implementation Guide](AI-MENTOR-IMPLEMENTATION-GUIDE.md)** - Detailed feature implementation
- 📝 **[Resume Implementation](RESUME-IMPLEMENTATION.md)** - Resume builder documentation
- 🔄 **[Migration Guide](MIGRATION-GUIDE.md)** - Database migration instructions

---
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── database/        # Database connections
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   └── ai/          # AI services (Google Gemini)
│   │   └── utils/           # Utilities
│   ├── scripts/             # Database scripts
│   ├── .env                 # Environment variables
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── app/                 # Next.js app router
│   │   ├── dashboard/       # Dashboard pages
│   │   ├── login/           # Auth pages
│   │   └── onboarding/      # Onboarding flow
│   ├── components/          # React components
│   ├── lib/                 # Utilities, API, stores
│   └── package.json         # Node dependencies
│
└── AI-MENTOR-IMPLEMENTATION-GUIDE.md
```

---

## 🧪 Running Tests

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login user |
| `/api/v1/profile/onboarding` | POST | Complete onboarding |
| `/api/v1/skills/analyze` | POST | Skill gap analysis |
| `/api/v1/roadmap/generate` | POST | Generate roadmap |
| `/api/v1/mentor/chat` | POST | Chat with AI mentor |
| `/api/v1/resume/generate` | POST | Generate resume |

Full API docs at: `http://localhost:8000/docs`

---

## 🎯 Features

- ✅ **User Authentication**: Secure JWT-based authentication with refresh tokens
- ✅ **Smart Onboarding**: Multi-step onboarding to capture user goals and skills
- ✅ **AI Skill Analysis**: Intelligent skill gap analysis comparing current vs. target skills
- ✅ **Personalized Roadmaps**: AI-generated learning paths with milestones and resources
- ✅ **Progress Tracking**: Track completion with streaks and gamification
- ✅ **24/7 AI Mentor**: Conversational AI assistant for career guidance
- ✅ **Resume Builder**: AI-powered resume generation and optimization
- ✅ **Dark Mode UI**: Beautiful, responsive interface with dark theme

---

## 📦 Setup Instructions

### Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/) or use [Neon](https://neon.tech/)
4. **MongoDB** - [Download](https://www.mongodb.com/try/download/community) or use [MongoDB Atlas](https://www.mongodb.com/atlas)
5. **Redis** - [Download](https://redis.io/download/) or use [Upstash](https://upstash.com/)
6. **Google Gemini API Key** - [Get one here](https://aistudio.google.com/)

### 🔧 Backend Setup

**Step 1**: Navigate to backend directory
```bash
cd backend
```

**Step 2**: Create and activate virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

**Step 3**: Install Python dependencies
```bash
pip install -r requirements.txt
```

**Step 4**: Configure environment variables

Create/edit `.env` file in the `backend` directory:

```env
# Google Gemini AI
GOOGLE_API_KEY=your_gemini_api_key_here

# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/database_name

# MongoDB
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB=aimentor

# Redis
REDIS_URL=redis://default:password@host:6379

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_32_character_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Server Settings
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

**Step 5**: Initialize PostgreSQL database
```sql
-- Connect to PostgreSQL and create database
CREATE DATABASE aimentor;
```

**Step 6**: Run database migrations (optional seed data)
```bash
# Seed database with initial data
python -m scripts.seed_database

# Seed skills library
python -m scripts.seed_skills
```

**Step 7**: Start the backend server
```bash
# Development mode with hot reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

✅ Backend running at: `http://localhost:8000`  
📚 API Docs available at: `http://localhost:8000/docs`

---

### 🎨 Frontend Setup

**Step 1**: Navigate to frontend directory
```bash
cd frontend
```

**Step 2**: Install Node.js dependencies
```bash
npm install
# or
yarn install
```

**Step 3**: Configure environment variables

Create `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Step 4**: Start the development server
```bash
npm run dev
# or
yarn dev
```

✅ Frontend running at: `http://localhost:3000`

---

### 🐳 Docker Setup (Alternative)

Run the entire stack using Docker Compose:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This will start:
- Backend API on port 8000
- Frontend on port 3000
- PostgreSQL on port 5432
- MongoDB on port 27017
- Redis on port 6379

---

## 🔄 Build Reproducibility Instructions

### **Building from Source**

#### **Backend Build**

1. **Clone the repository**
```bash
git clone <repository-url>
cd AImentor/backend
```

2. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. **Install exact dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Verify installation**
```bash
python -c "import fastapi; import sqlalchemy; print('Backend dependencies OK')"
```

6. **Run tests (if available)**
```bash
pytest tests/ -v
```

#### **Frontend Build**

1. **Navigate to frontend**
```bash
cd frontend
```

2. **Install dependencies with lock file**
```bash
npm ci  # Uses package-lock.json for reproducible builds
```

3. **Build for production**
```bash
npm run build
```

4. **Verify build**
```bash
npm run start  # Runs production build locally
```

### **Environment Variables Checklist**

Ensure these variables are set before building:

**Backend** (.env):
- [x] `GOOGLE_API_KEY` - Get from [Google AI Studio](https://aistudio.google.com/)
- [x] `DATABASE_URL` - PostgreSQL connection string
- [x] `MONGODB_URL` - MongoDB connection string
- [x] `REDIS_URL` - Redis connection string
- [x] `JWT_SECRET_KEY` - Generate using: `openssl rand -hex 32`

**Frontend** (.env.local):
- [x] `NEXT_PUBLIC_API_URL` - Backend API URL

### **Database Initialization**

```bash
# 1. Create PostgreSQL database
createdb aimentor

# 2. Run migrations (if using Alembic)
alembic upgrade head

# 3. Seed initial data
python -m scripts.seed_database
python -m scripts.seed_skills
```

### **Deployment Build**

#### **Vercel Deployment**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy backend
cd backend
vercel --prod

# Deploy frontend
cd frontend
vercel --prod
```

See [VERCEL-DEPLOYMENT-GUIDE.md](VERCEL-DEPLOYMENT-GUIDE.md) for detailed instructions.

### **Docker Production Build**

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Run in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Verification Steps**

After building, verify the application:

1. **Backend Health Check**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

2. **Frontend Access**
```bash
curl http://localhost:3000
# Should return HTML
```

3. **Database Connectivity**
```bash
# Run backend test
python backend/scripts/test_connections.py
```

4. **API Functionality**
```bash
# Test registration endpoint
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'
```

---

## 📸 Final Output & Demo

### **Landing Page**
![Landing Page](docs/screenshots/landing.png)
- Clean, modern interface with call-to-action
- Features overview and benefits

### **User Registration & Authentication**
![Authentication](docs/screenshots/auth.png)
- Secure JWT-based authentication
- Form validation and error handling

### **Onboarding Flow**
![Onboarding](docs/screenshots/onboarding.png)
- Multi-step wizard to capture user information
- Career goals, current skills, and target role selection

### **Dashboard Overview**
![Dashboard](docs/screenshots/dashboard.png)
- Personalized learning progress
- Active roadmaps and milestones
- Streak tracking and achievements

### **AI Skill Gap Analysis**
![Skill Analysis](docs/screenshots/skills.png)
- Visual representation of skill gaps
- AI-powered recommendations
- Industry-standard skill benchmarks

### **Personalized Learning Roadmap**
![Roadmap](docs/screenshots/roadmap.png)
- Phase-based learning path
- Milestones with resources
- Estimated timelines and difficulty levels

### **AI Mentor Chat**
![AI Chat](docs/screenshots/chat.png)
- 24/7 conversational AI support
- Context-aware responses
- Career guidance and learning tips

### **Resume Builder**
![Resume](docs/screenshots/resume.png)
- AI-generated resumes based on profile
- Multiple templates and formats
- Export to PDF

### **Live Demo**
🔗 **Frontend**: [https://ai-mentor-eta-weld.vercel.app](https://ai-mentor-eta-weld.vercel.app)  
🔗 **API Docs**: [https://ai-mentor-backend.vercel.app/docs](https://ai-mentor-backend.vercel.app/docs)

**Test Credentials** (if demo account available):
```
Email: demo@aimentor.com
Password: Demo123!
```

---

## 🎯 Features

## 🐛 Troubleshooting

### Common Issues and Solutions

#### **Backend Issues**

**1. Database Connection Errors**
```bash
# Error: "could not connect to server"
Solution:
- Ensure PostgreSQL/MongoDB/Redis services are running
- Check connection strings in .env file
- Verify network connectivity to cloud databases
- Test connection: python -c "import asyncpg; print('OK')"
```

**2. Google Gemini API Errors**
```bash
# Error: "quota exceeded" or "invalid API key"
Solution:
- Verify API key is valid at https://aistudio.google.com/
- Check API quota limits
- Test API key: python backend/test_api_key.py
- Wait for quota reset (usually daily) or get new key
```

**3. Module Import Errors**
```bash
# Error: "ModuleNotFoundError"
Solution:
- Ensure virtual environment is activated
- Reinstall dependencies: pip install -r requirements.txt
- Check Python version: python --version (requires 3.10+)
```

**4. Port Already in Use**
```bash
# Error: "Address already in use"
Solution:
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

#### **Frontend Issues**

**1. API Connection Failed**
```bash
# Error: "Network Error" or CORS error
Solution:
- Ensure backend is running on port 8000
- Check NEXT_PUBLIC_API_URL in .env.local
- Verify CORS_ORIGINS in backend .env includes frontend URL
- Clear browser cache and cookies
```

**2. Build Errors**
```bash
# Error: Type errors or module not found
Solution:
- Delete node_modules and package-lock.json
- Run: npm install
- Clear Next.js cache: rm -rf .next
- Rebuild: npm run build
```

**3. Environment Variables Not Loading**
```bash
# Variables showing as undefined
Solution:
- Restart dev server after .env.local changes
- Ensure variables start with NEXT_PUBLIC_ for client-side
- Check file is named .env.local (not .env)
```

#### **Docker Issues**

**1. Container Won't Start**
```bash
Solution:
- Check logs: docker-compose logs backend
- Verify environment variables in docker-compose.yml
- Rebuild images: docker-compose build --no-cache
- Check ports aren't in use: docker ps
```

**2. Database Connection in Docker**
```bash
# Error: "Connection refused"
Solution:
- Use service names instead of localhost
- DATABASE_URL=postgresql://postgres:password@postgres:5432/aimentor
- Wait for database to be ready (use depends_on with healthcheck)
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - Free for personal and commercial use.

---

## 👥 Authors & Contributors

- **Development Team** - *Initial work and ongoing development*

---

## 🙏 Acknowledgments

- **Google Gemini API** for powering AI capabilities
- **FastAPI** framework for robust backend architecture
- **Next.js** for modern, performant frontend
- **Vercel** for seamless deployment and hosting
- **Open Source Community** for amazing libraries and tools

---

## 📞 Support & Contact

For issues, questions, or suggestions:

- 🐛 **Issues**: Report bugs or request features via GitHub Issues
- 💬 **Discussions**: Join community discussions on GitHub
- 📧 **Email**: Contact the development team
- 📚 **Documentation**: See additional guides in `/docs` folder

---

## 🗺️ Future Roadmap

- [ ] **Mobile Application**: React Native apps for iOS/Android
- [ ] **LinkedIn Integration**: Import profile data and sync achievements
- [ ] **Video Courses**: Curated video learning resources
- [ ] **Peer Mentorship**: Connect with human mentors and peers
- [ ] **Certification Tracking**: Track and showcase completed certifications
- [ ] **Job Board Integration**: Apply to jobs matching your roadmap
- [ ] **Multi-language Support**: Internationalization (i18n)
- [ ] **Voice Assistant**: Voice-based AI mentor interaction
- [ ] **Gamification**: Badges, leaderboards, and competitions
- [ ] **Company Dashboard**: Tools for HR and L&D teams

---

**Built with ❤️ using AI-powered development tools**

*Last Updated: February 2026*
