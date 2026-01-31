# AI Life Mentor - Setup & Running Guide

A full-stack AI-powered career mentorship platform with personalized learning roadmaps, skill gap analysis, and 24/7 AI chat support.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/) or use [Supabase](https://supabase.com/)
4. **MongoDB** - [Download](https://www.mongodb.com/try/download/community) or use [MongoDB Atlas](https://www.mongodb.com/atlas)
5. **Redis** - [Download](https://redis.io/download/) or use [Upstash](https://upstash.com/)
6. **DeepSeek API Key** - [Get one here](https://platform.deepseek.com/)

---

## 📦 Backend Setup

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
# DeepSeek AI
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# PostgreSQL (use your local or cloud database URL)
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ai_mentor

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=ai_mentor

# Redis
REDIS_URL=redis://localhost:6379

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your_super_secret_key_change_this_in_production
```

### 5. Create PostgreSQL database

```sql
CREATE DATABASE ai_mentor;
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

## 🗄️ Database Options

### Option A: Local Databases (Development)

1. **PostgreSQL**: Install locally and create database
2. **MongoDB**: Install locally or use Docker
3. **Redis**: Install locally or use Docker

Docker compose for local databases:

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_mentor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  mongo_data:
```

Run with: `docker-compose up -d`

### Option B: Cloud Databases (Recommended for Production)

1. **Supabase** (PostgreSQL): Free tier with 500MB
   - Create project at https://supabase.com/
   - Get connection string from Settings → Database

2. **MongoDB Atlas**: Free tier with 512MB
   - Create cluster at https://cloud.mongodb.com/
   - Get connection string from Connect → Drivers

3. **Upstash** (Redis): Free tier with 10K commands/day
   - Create database at https://upstash.com/
   - Get connection URL from database details

---

## 🔑 Getting DeepSeek API Key

1. Go to https://platform.deepseek.com/
2. Create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

---

## 📁 Project Structure

```
AImentor/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── database/        # Database connections
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   │   └── ai/          # AI services (DeepSeek)
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

- ✅ User authentication (JWT)
- ✅ Multi-step onboarding flow
- ✅ AI-powered skill gap analysis
- ✅ Personalized learning roadmap generation
- ✅ Progress tracking with streaks
- ✅ 24/7 AI mentor chat (DeepSeek)
- ✅ Resume generation and tailoring
- ✅ Beautiful dark mode UI

---

## 🐛 Troubleshooting

### Database connection errors
- Ensure PostgreSQL, MongoDB, and Redis are running
- Check connection strings in `.env`

### DeepSeek API errors
- Verify API key is valid
- Check API rate limits

### Frontend not connecting to backend
- Ensure backend is running on port 8000
- Check CORS settings in backend

---

## 📝 License

MIT License - Free for personal and commercial use
