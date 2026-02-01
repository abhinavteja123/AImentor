# Source Code Documentation

This document provides an overview of the AI Life Mentor source code organization and key components.

## 📂 Repository Structure

```
AImentor/
├── backend/          # Python FastAPI backend
├── frontend/         # Next.js React frontend  
├── docs/             # Documentation
├── scripts/          # Deployment scripts
└── docker-compose.yml
```

---

## 🔙 Backend Architecture

### Entry Point
**File**: `backend/app/main.py`

The main FastAPI application setup with middleware, CORS, and route registration.

```python
# Key components:
- FastAPI application instance
- CORS middleware configuration
- Database connection lifecycle
- API router registration (v1 endpoints)
- Health check endpoint
```

### Configuration
**File**: `backend/app/config.py`

Environment-based configuration using Pydantic Settings.

```python
# Key settings:
- Database URLs (PostgreSQL, MongoDB, Redis)
- API keys (Google Gemini)
- JWT configuration
- CORS origins
- Application settings
```

### Database Layer

#### PostgreSQL
**File**: `backend/app/database/postgres.py`
- SQLAlchemy async engine
- Session management
- Connection pooling

#### MongoDB
**File**: `backend/app/database/mongodb.py`
- Motor async client
- Database and collection access
- Document operations

#### Redis
**File**: `backend/app/database/redis_client.py`
- Async Redis connection
- Caching utilities
- Session storage

### Data Models (ORM)
**Directory**: `backend/app/models/`

SQLAlchemy models representing database tables:

- `user.py` - User accounts and authentication
- `profile.py` - User profiles and preferences
- `skill.py` - Skills library and user skills
- `progress.py` - Learning progress tracking
- `roadmap.py` - Learning roadmap structure (metadata)
- `resume.py` - Resume metadata and versions

### Schemas (DTOs)
**Directory**: `backend/app/schemas/`

Pydantic schemas for request/response validation:

- `user.py` - Registration, login, profile responses
- `skill.py` - Skill data structures
- `roadmap.py` - Roadmap request/response
- `mentor.py` - Chat message structures
- `resume.py` - Resume data structures

### API Endpoints
**Directory**: `backend/app/api/v1/`

RESTful API endpoints organized by feature:

#### Authentication (`auth.py`)
```python
POST /api/v1/auth/register  # User registration
POST /api/v1/auth/login     # User login
POST /api/v1/auth/refresh   # Refresh token
POST /api/v1/auth/logout    # User logout
```

#### Profile (`profile.py`)
```python
POST /api/v1/profile/onboarding  # Complete onboarding
GET  /api/v1/profile/me          # Get current user
PUT  /api/v1/profile/update      # Update profile
```

#### Skills (`skills.py`)
```python
POST /api/v1/skills/analyze  # AI skill gap analysis
GET  /api/v1/skills/list     # List available skills
GET  /api/v1/skills/user     # Get user's skills
```

#### Roadmap (`roadmap.py`)
```python
POST /api/v1/roadmap/generate    # Generate AI roadmap
GET  /api/v1/roadmap/list        # List user roadmaps
GET  /api/v1/roadmap/{id}        # Get specific roadmap
PUT  /api/v1/roadmap/{id}/update # Update progress
```

#### AI Mentor (`mentor.py`)
```python
POST /api/v1/mentor/chat     # Chat with AI
GET  /api/v1/mentor/history  # Get chat history
```

#### Resume (`resume.py`)
```python
POST /api/v1/resume/generate  # Generate AI resume
GET  /api/v1/resume/list      # List user resumes
GET  /api/v1/resume/{id}      # Get specific resume
PUT  /api/v1/resume/{id}      # Update resume
```

### Business Logic (Services)
**Directory**: `backend/app/services/`

Service layer containing business logic:

#### Auth Service (`auth_service.py`)
- User registration and validation
- Password hashing (bcrypt)
- JWT token generation/verification
- Session management

#### Skill Service (`skill_service.py`)
- Skill gap analysis using AI
- Skill matching algorithms
- User skill management
- Skill recommendations

#### Roadmap Service (`roadmap_service.py`)
- AI-powered roadmap generation
- Milestone creation and management
- Progress tracking
- Resource recommendations

#### Progress Service (`progress_service.py`)
- Track milestone completion
- Calculate learning streaks
- Generate progress statistics
- Achievement system

#### Resume Service (`resume_service.py`)
- AI resume generation from profile
- Resume version management
- Template application
- PDF export

### AI Services
**Directory**: `backend/app/services/ai/`

AI integration layer:

#### Gemini Service (`gemini_service.py`)
```python
# Core AI functionality:
- Google Gemini API integration
- Model initialization and configuration
- Error handling and retries
- Token management
```

#### Chat Service (`chat_service.py`)
```python
# Conversational AI:
- Context-aware chat responses
- Conversation history management
- Streaming responses
- Safety filters
```

#### Prompts (`prompts.py`)
```python
# Prompt templates:
- Skill analysis prompts
- Roadmap generation prompts
- Chat system prompts
- Resume generation prompts
```

### Utilities
**Directory**: `backend/app/utils/`

Helper functions and utilities:

- `security.py` - Password hashing, token generation
- `validators.py` - Input validation helpers

### Database Scripts
**Directory**: `backend/scripts/`

Database management scripts:

- `seed_database.py` - Initial data seeding
- `seed_skills.py` - Populate skills library
- `init.sql` - Database schema initialization
- `migrate_*.py` - Data migration scripts

---

## 🎨 Frontend Architecture

### App Structure
**Directory**: `frontend/app/`

Next.js 14 App Router structure:

```
app/
├── layout.tsx           # Root layout (providers, fonts)
├── page.tsx             # Landing page
├── globals.css          # Global styles
├── login/               # Authentication
│   └── page.tsx
├── register/
│   └── page.tsx
├── onboarding/          # Multi-step onboarding
│   └── page.tsx
└── dashboard/           # Protected routes
    ├── page.tsx         # Dashboard home
    ├── profile/         # Profile management
    ├── skills/          # Skills analysis
    ├── roadmap/         # Learning roadmaps
    ├── chat/            # AI mentor chat
    ├── progress/        # Progress tracking
    └── resume/          # Resume builder
```

### Components
**Directory**: `frontend/components/`

Reusable React components:

#### Layout Components
- `DashboardLayout.tsx` - Dashboard shell with navigation

#### Resume Components
- `ResumeDataForm.tsx` - Resume data input form
- `EditResumeForm.tsx` - Resume editing interface
- `VersionManager.tsx` - Resume version control

#### UI Components (`ui/`)
Reusable UI primitives:
- `button.tsx` - Button component
- `card.tsx` - Card container
- `input.tsx` - Input field
- `label.tsx` - Form label
- `progress.tsx` - Progress bar

### Libraries
**Directory**: `frontend/lib/`

Core utilities and configurations:

#### API Client (`api.ts`)
```typescript
// HTTP client setup:
- Axios instance configuration
- Request/response interceptors
- Authentication token injection
- Error handling
```

#### State Management (`store.ts`)
```typescript
// Zustand stores:
- User authentication state
- Profile data
- Skills state
- Roadmap state
- UI state (modals, notifications)
```

#### Utilities (`utils.ts`)
```typescript
// Helper functions:
- Date formatting
- String manipulation
- Validation helpers
- Class name utilities
```

---

## 🔑 Key Technologies & Patterns

### Backend Patterns

**Dependency Injection**
```python
# FastAPI dependency injection for database sessions
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Usage in endpoints
@router.get("/")
async def endpoint(db: AsyncSession = Depends(get_db)):
    pass
```

**Async/Await**
```python
# All database and AI operations are async
async def get_user(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

**Error Handling**
```python
# Consistent HTTP exceptions
raise HTTPException(
    status_code=404,
    detail="User not found"
)
```

### Frontend Patterns

**Server Components (Default)**
```typescript
// app/page.tsx
export default async function Page() {
  // Runs on server
  const data = await fetchData();
  return <div>{data}</div>;
}
```

**Client Components (Interactive)**
```typescript
// components/InteractiveButton.tsx
'use client';
import { useState } from 'react';

export default function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**Route Handlers (API Routes)**
```typescript
// app/api/example/route.ts
export async function GET(request: Request) {
  return Response.json({ message: 'Hello' });
}
```

---

## 🧪 Testing Strategy

### Backend Tests
```bash
# Location: backend/tests/
tests/
├── test_auth.py       # Authentication tests
├── test_skills.py     # Skills service tests
├── test_roadmap.py    # Roadmap generation tests
└── conftest.py        # Pytest fixtures
```

### Frontend Tests
```bash
# Location: frontend/__tests__/
__tests__/
├── components/        # Component tests
├── pages/             # Page tests
└── utils/             # Utility tests
```

---

## 🔐 Security Implementation

### Authentication Flow
1. User submits credentials
2. Backend validates and generates JWT
3. Frontend stores token in memory/cookie
4. Token included in subsequent requests
5. Backend validates token on protected routes

### Password Security
```python
# bcrypt for password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(plain_password)
verified = pwd_context.verify(plain_password, hashed)
```

### JWT Tokens
```python
# Access token (short-lived: 24h)
# Refresh token (long-lived: 30 days)

access_token = create_access_token(data={"sub": user.email})
refresh_token = create_refresh_token(data={"sub": user.email})
```

---

## 📊 Data Flow Examples

### User Registration Flow
```
1. POST /api/v1/auth/register
2. Validate input (Pydantic schema)
3. Check if email exists (PostgreSQL)
4. Hash password (bcrypt)
5. Create user record (SQLAlchemy)
6. Generate JWT tokens
7. Return user data + tokens
```

### AI Roadmap Generation Flow
```
1. POST /api/v1/roadmap/generate
2. Authenticate user (JWT)
3. Get user profile (PostgreSQL)
4. Get skill gap data (MongoDB)
5. Build prompt with user context
6. Call Google Gemini API
7. Parse AI response
8. Save roadmap (MongoDB)
9. Create progress tracking (PostgreSQL)
10. Return roadmap data
```

### Chat with AI Mentor Flow
```
1. POST /api/v1/mentor/chat
2. Authenticate user
3. Load conversation history (MongoDB, last 10 messages)
4. Build context-aware prompt
5. Call Gemini API (streaming)
6. Stream response to frontend
7. Save message pair to history
8. Return response
```

---

## 🚀 Performance Optimizations

### Backend
- ✅ Async database operations (SQLAlchemy async)
- ✅ Connection pooling (PostgreSQL, MongoDB)
- ✅ Redis caching for frequently accessed data
- ✅ Lazy loading of relationships
- ✅ Pagination for list endpoints

### Frontend
- ✅ Server-side rendering (Next.js)
- ✅ Static generation where possible
- ✅ Code splitting (automatic with Next.js)
- ✅ Image optimization (next/image)
- ✅ API response caching

---

## 📝 Code Style & Standards

### Backend (Python)
- Follow PEP 8 style guide
- Type hints for function signatures
- Docstrings for classes and functions
- Async/await for I/O operations

### Frontend (TypeScript)
- ESLint for code linting
- Prettier for code formatting
- TypeScript strict mode
- Consistent component structure

---

## 🔗 External Dependencies

### Backend Key Packages
```
fastapi - Web framework
sqlalchemy - ORM
pydantic - Data validation
google-generativeai - AI integration
python-jose - JWT handling
passlib - Password hashing
asyncpg - PostgreSQL async driver
motor - MongoDB async driver
redis - Redis client
```

### Frontend Key Packages
```
next - React framework
react - UI library
typescript - Type safety
tailwindcss - Styling
zustand - State management
axios - HTTP client
```

---

**For more details**, see:
- [README.md](../README.md) - Setup and usage
- [BUILD-REPRODUCIBILITY.md](BUILD-REPRODUCIBILITY.md) - Build instructions
- [VERCEL-DEPLOYMENT-GUIDE.md](../VERCEL-DEPLOYMENT-GUIDE.md) - Deployment guide
