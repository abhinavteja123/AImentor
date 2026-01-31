# 🚀 AI LIFE MENTOR - COMPLETE PHASE-BY-PHASE IMPLEMENTATION GUIDE

> **Professional Career Mentorship Platform with AI-Powered Learning Roadmaps**

---

## 📋 EXECUTIVE SUMMARY

**Product**: AI Life Mentor  
**Tagline**: Your Personal AI Career Coach - Remembers, Guides, Grows with You  
**Duration**: 24-hour Hackathon Implementation Plan  
**Tech Stack**: Next.js 14 + FastAPI + PostgreSQL + MongoDB + AI/ML

---

## 🎯 PROBLEM & SOLUTION

### The Problem
Students and early-career professionals struggle with:
- ❌ Fragmented learning tools (courses, chatbots, resume builders work in isolation)
- ❌ No personalized learning paths based on individual skills and goals
- ❌ Lack of progress tracking and adaptive guidance
- ❌ Static resumes that don't reflect continuous learning

### Our Solution
A unified AI mentor that:
- ✅ Maintains deep user context and memory
- ✅ Generates personalized learning roadmaps
- ✅ Tracks progress and adapts guidance
- ✅ Auto-evolves professional profile
- ✅ Provides contextual mentorship 24/7

---

## 🛠 TECHNOLOGY STACK

### Frontend
```
- Next.js 14+ (App Router, TypeScript)
- Tailwind CSS + shadcn/ui
- Framer Motion (animations)
- Recharts (data visualization)
- React Query (server state)
- Zustand (client state)
```

### Backend
```
- Python 3.11+ FastAPI
- SQLAlchemy (ORM)
- Pydantic (validation)
- Celery (background tasks)
```

### Databases
```
- PostgreSQL (relational data)
- MongoDB (conversations)
- Redis (caching/sessions)
- ChromaDB (vector search)
```

### AI/ML
```
- OpenAI GPT-4 or Anthropic Claude
- LangChain (orchestration)
- Sentence-Transformers (embeddings)
```

### Deployment
```
- Frontend: Vercel
- Backend: Railway/Render
- Databases: Supabase + MongoDB Atlas + Upstash
```

---

## 🗄 DATABASE SCHEMA

### PostgreSQL Tables

```sql
-- Core user table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- User profiles
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    goal_role VARCHAR,
    experience_level VARCHAR,
    time_per_day INTEGER,
    preferred_learning_style VARCHAR
);

-- Skills master database
CREATE TABLE skills_master (
    id UUID PRIMARY KEY,
    skill_name VARCHAR UNIQUE,
    category VARCHAR,
    difficulty_level INTEGER,
    market_demand_score DECIMAL
);

-- User skills
CREATE TABLE user_skills (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    skill_id UUID REFERENCES skills_master(id),
    proficiency_level INTEGER,
    acquired_date DATE
);

-- Learning roadmaps
CREATE TABLE roadmaps (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR,
    total_weeks INTEGER,
    start_date DATE,
    completion_percentage DECIMAL,
    status VARCHAR
);

-- Roadmap tasks
CREATE TABLE roadmap_tasks (
    id UUID PRIMARY KEY,
    roadmap_id UUID REFERENCES roadmaps(id),
    week_number INTEGER,
    day_number INTEGER,
    task_title VARCHAR,
    task_description TEXT,
    task_type VARCHAR,
    estimated_duration INTEGER,
    resources JSONB,
    status VARCHAR
);

-- Progress tracking
CREATE TABLE progress_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    task_id UUID REFERENCES roadmap_tasks(id),
    time_spent INTEGER,
    difficulty_rating INTEGER,
    confidence_rating INTEGER,
    created_at TIMESTAMP
);

-- Resumes
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    version INTEGER,
    summary TEXT,
    skills_section JSONB,
    projects_section JSONB,
    is_active BOOLEAN
);
```

---

## 🔌 API ENDPOINTS

### Authentication
```
POST   /api/v1/auth/register     - Register new user
POST   /api/v1/auth/login        - Login user
POST   /api/v1/auth/refresh      - Refresh access token
POST   /api/v1/auth/logout       - Logout user
GET    /api/v1/auth/me           - Get current user
```

### Profile
```
POST   /api/v1/profile/onboarding  - Complete onboarding
GET    /api/v1/profile/me          - Get user profile
PUT    /api/v1/profile/update      - Update profile
POST   /api/v1/profile/skills      - Add user skill
```

### Skills & Analysis
```
POST   /api/v1/skills/analyze-gap  - Analyze skill gaps
GET    /api/v1/skills/master       - Get skills database
```

### Roadmap
```
POST   /api/v1/roadmap/generate       - Generate roadmap
GET    /api/v1/roadmap/current        - Get current roadmap
GET    /api/v1/roadmap/{id}/week/{n}  - Get specific week
PUT    /api/v1/roadmap/regenerate     - Regenerate with feedback
```

### Progress
```
POST   /api/v1/progress/task/complete  - Mark task complete
POST   /api/v1/progress/task/skip      - Skip task
GET    /api/v1/progress/stats          - Get progress stats
```

### Mentor Chat
```
POST   /api/v1/mentor/chat         - Send message to mentor
GET    /api/v1/mentor/sessions     - Get chat sessions
GET    /api/v1/mentor/session/{id} - Get conversation history
```

### Resume
```
GET    /api/v1/resume/current      - Get current resume
POST   /api/v1/resume/generate     - Generate resume
POST   /api/v1/resume/tailor       - Tailor to job description
GET    /api/v1/resume/export       - Export as PDF/DOCX
```

---

## 📁 PROJECT STRUCTURE

### Frontend (Next.js)
```
app/
├── (auth)/
│   ├── login/page.tsx
│   └── register/page.tsx
├── (dashboard)/
│   ├── dashboard/page.tsx
│   ├── roadmap/page.tsx
│   ├── mentor/page.tsx
│   ├── progress/page.tsx
│   └── resume/page.tsx
├── onboarding/page.tsx
└── layout.tsx

components/
├── ui/                    # shadcn components
├── layout/
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── DashboardLayout.tsx
├── dashboard/
│   ├── StatsCard.tsx
│   └── ProgressChart.tsx
├── roadmap/
│   ├── WeeklyTimeline.tsx
│   └── TaskCard.tsx
├── mentor/
│   ├── ChatInterface.tsx
│   └── MessageBubble.tsx
└── resume/
    └── ResumePreview.tsx

lib/
├── api/                  # API client functions
├── hooks/               # React Query hooks
├── stores/              # Zustand stores
└── types/               # TypeScript types
```

### Backend (FastAPI)
```
app/
├── main.py
├── config.py
├── api/v1/
│   ├── auth.py
│   ├── profile.py
│   ├── skills.py
│   ├── roadmap.py
│   ├── progress.py
│   ├── mentor.py
│   └── resume.py
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/
│   ├── auth_service.py
│   ├── skill_service.py
│   ├── roadmap_service.py
│   └── ai/
│       ├── llm_client.py
│       ├── skill_analyzer.py
│       ├── roadmap_generator.py
│       └── chat_engine.py
└── database/
    ├── postgres.py
    ├── mongodb.py
    └── redis_client.py
```

---

# 🚀 PHASE-BY-PHASE IMPLEMENTATION

---

## PHASE 1: SETUP & INFRASTRUCTURE (Hours 1-3)

### Objective
Set up complete development environment and initialize databases.

### Backend Setup Prompt

```
Create a FastAPI backend with:

1. Project structure with modular architecture
2. PostgreSQL connection using SQLAlchemy
3. MongoDB connection using Motor
4. Redis for caching
5. Environment configuration with Pydantic Settings

Required files:
- app/main.py: FastAPI app with CORS, routers, health check
- app/config.py: Environment variables and settings
- app/database/postgres.py: SQLAlchemy async setup
- app/database/mongodb.py: Motor async client
- app/database/redis_client.py: Redis connection pool
- requirements.txt: All dependencies

Include:
- Proper error handling
- Logging configuration
- Database connection management
- Alembic for migrations

Generate production-ready code with type hints and docstrings.
```

### Frontend Setup Prompt

```
Create a Next.js 14 application with:

1. TypeScript configuration (strict mode)
2. Tailwind CSS with custom theme
3. shadcn/ui component library
4. React Query for server state
5. Zustand for client state
6. NextAuth for authentication

Project structure:
- app/ directory with App Router
- components/ui/ for shadcn components
- components/layout/ for Header, Sidebar
- lib/api/ for API client
- lib/stores/ for Zustand stores
- lib/hooks/ for custom hooks

Configure:
- Path aliases (@/components, @/lib)
- ESLint and Prettier
- Tailwind with custom colors and animations
- axios instance with interceptors

Install these components from shadcn/ui:
- button, card, input, dialog, progress, tabs, toast

Generate all files with modern React patterns and TypeScript types.
```

### Database Initialization Prompt

```
Create database setup scripts:

1. Alembic migration with all tables:
   - users, user_profiles, skills_master, user_skills
   - role_templates, roadmaps, roadmap_tasks
   - progress_logs, resumes, achievements

2. Seed data script (scripts/seed_database.py):
   - 100+ skills across categories:
     * Frontend: React, Vue, Next.js, Tailwind, etc.
     * Backend: Node.js, Python, FastAPI, Django, etc.
     * Database: PostgreSQL, MongoDB, Redis, etc.
     * DevOps: Docker, Kubernetes, CI/CD, etc.
   - 5+ role templates with required skills:
     * Full Stack Developer (Junior/Mid/Senior)
     * Frontend Developer
     * Backend Developer
     * Data Scientist
     * DevOps Engineer

Each skill should have:
- Name, category, difficulty (1-5)
- Market demand score (0-1)
- Related skills array

Each role template should specify:
- Required skills with min proficiency
- Preferred skills
- Typical responsibilities

Generate production-ready SQL and Python code.
```

### Deliverables Checklist
- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:3000
- [ ] PostgreSQL connected with tables created
- [ ] MongoDB connected
- [ ] Redis connected
- [ ] Seed data loaded
- [ ] Health check endpoint responding

---

## PHASE 2: AUTHENTICATION & PROFILES (Hours 4-6)

### Objective
Implement secure authentication and user onboarding flow.

### Authentication Backend Prompt

```
Implement complete authentication system:

1. app/services/auth_service.py:
   - register_user(email, password, full_name)
     * Validate email format
     * Hash password with bcrypt (cost factor 12)
     * Create user in database
     * Generate JWT tokens (access + refresh)
   
   - login_user(email, password)
     * Verify credentials
     * Update last_login
     * Generate tokens
   
   - refresh_access_token(refresh_token)
   - get_current_user(token)
   - logout_user(user_id, token)

2. app/utils/security.py:
   - hash_password, verify_password
   - create_access_token (24h expiry)
   - create_refresh_token (30d expiry)
   - decode_token with validation

3. app/schemas/user.py:
   - UserRegister: email, password, full_name
   - UserLogin: email, password
   - UserResponse: exclude password
   - TokenResponse: access_token, refresh_token

4. app/api/v1/auth.py:
   - POST /auth/register: Create user
   - POST /auth/login: Authenticate
   - POST /auth/refresh: Get new token
   - POST /auth/logout: Invalidate token
   - GET /auth/me: Get current user

Security requirements:
- Password validation (min 8 chars, 1 upper, 1 lower, 1 number)
- JWT with proper expiry
- Token blacklist in Redis
- Rate limiting (5 attempts/minute)

Include comprehensive error handling and logging.
```

### Authentication Frontend Prompt

```
Create authentication UI:

1. lib/api/auth.ts:
   - register, login, logout, refreshToken, getCurrentUser

2. lib/stores/authStore.ts (Zustand):
   - State: user, accessToken, isAuthenticated
   - Actions: login, register, logout, checkAuth
   - Persist tokens in localStorage

3. lib/hooks/useAuth.ts:
   - Custom hook with auto token refresh
   - Handle redirects

4. app/(auth)/register/page.tsx:
   Components:
   - Email input with validation
   - Password input with strength meter
   - Confirm password input
   - Full name input
   - Register button with loading state

   Functionality:
   - React Hook Form + Zod validation
   - Show validation errors inline
   - Password strength indicator
   - On success: redirect to /onboarding
   - Toast notifications for errors

5. app/(auth)/login/page.tsx:
   Components:
   - Email and password inputs
   - Remember me checkbox
   - Login button
   - Forgot password link
   - Register link

   Functionality:
   - Form validation
   - On success: redirect to /dashboard
   - Loading states

6. middleware.ts:
   - Protect routes (dashboard/*, onboarding, etc.)
   - Redirect logic for auth/unauth users

7. lib/api/client.ts:
   - Axios instance with auth interceptors
   - Auto refresh on 401
   - Retry failed requests

Design:
- Centered card layout
- Gradient background
- Smooth animations
- Accessible forms

Generate beautiful, accessible components with proper error handling.
```

### Onboarding System Prompt

```
Create multi-step onboarding:

BACKEND:

1. app/services/profile_service.py:
   - create_profile(user_id, profile_data)
   - get_profile(user_id)
   - update_profile(user_id, updates)
   - add_user_skill(user_id, skill_name, proficiency)

2. app/schemas/profile.py:
   - ProfileCreate: goal_role, experience_level, education,
     graduation_year, time_per_day, learning_style, current_skills
   - ProfileUpdate: all fields optional
   - ProfileResponse: include completion_percentage

3. app/api/v1/profile.py:
   - POST /profile/onboarding
   - GET /profile/me
   - PUT /profile/update

FRONTEND:

app/onboarding/page.tsx - Multi-step wizard:

Step 1: Goal Setting
- "What role are you aiming for?"
- Searchable dropdown with role templates
- Custom role input option

Step 2: Experience Level
- Three cards: Beginner / Intermediate / Advanced
- Description for each
- Selection highlights card

Step 3: Education & Timeline
- Current education/degree input
- Graduation year (if student)

Step 4: Time Commitment
- Slider: 15 min to 4 hours
- Visual representation
- Show estimated milestones

Step 5: Current Skills
- Multi-select autocomplete
- Search from skills_master API
- Proficiency rating (1-5 stars) for each
- Skip option

Step 6: Learning Style
- Visual / Reading / Hands-on / Mixed
- Multiple choice cards

Design:
- Progress indicator (Step X of 6)
- Smooth transitions between steps
- Back/Next navigation
- Can jump to completed steps
- Form validation on each step
- Summary on last step before submit
- On submit: POST to /profile/onboarding
- Redirect to /dashboard with welcome message

Components needed:
- StepIndicator.tsx (progress stepper)
- SkillSelector.tsx (autocomplete with chips)
- ProficiencyRating.tsx (star rating)

Generate engaging onboarding with smooth UX.
```

### Deliverables Checklist
- [ ] User registration working
- [ ] Login with JWT tokens
- [ ] Token refresh working
- [ ] Protected routes
- [ ] 6-step onboarding flow
- [ ] Profile creation
- [ ] Skills added with proficiency
- [ ] Mobile responsive

---

## PHASE 3: SKILL ANALYSIS & ROADMAP (Hours 7-10)

### Objective
Implement AI-powered skill gap analysis and roadmap generation.

### AI Services Setup Prompt

```
Set up AI infrastructure:

1. app/services/ai/llm_client.py:
   class LLMClient:
     - __init__: Initialize OpenAI or Anthropic client
     - async generate_completion(system_prompt, user_prompt, 
       temperature, max_tokens, response_format)
     - async generate_with_context(prompt, context)
     - async embed_text(text) using sentence-transformers

2. app/services/ai/embeddings.py:
   class EmbeddingService:
     - __init__: Load sentence-transformers model
     - encode_skill(skill_name, description) -> vector
     - encode_batch(texts) -> vectors
     - find_similar_skills(query, top_k=5)

3. app/database/vector_db.py:
   class VectorDatabase (ChromaDB):
     - add_skill_embedding(skill_id, embedding, metadata)
     - search_similar_skills(query_embedding, top_k, filter)
     - bulk_add_skills(skills_data)

4. scripts/populate_embeddings.py:
   - Fetch all skills from skills_master
   - Generate embeddings
   - Store in ChromaDB
   - Progress bar and error handling

Configuration:
- Support OpenAI and Anthropic
- Retry logic for API calls
- Error handling for rate limits
- Logging all AI interactions

Generate robust production code.
```

### Skill Gap Analyzer Prompt

```
Implement skill gap analysis:

app/services/ai/skill_analyzer.py:

class SkillAnalyzer:
  async def analyze_skill_gap(user_id, target_role) -> Dict:
    """
    Returns:
    {
      "target_role": str,
      "required_skills": List[SkillGap],
      "current_skills": List[UserSkill],
      "missing_skills": List[SkillGap],
      "skills_to_improve": List[SkillGap],
      "strength_areas": List[str],
      "overall_readiness": float (0-100),
      "estimated_time_to_ready": int (weeks),
      "ai_insights": Dict
    }
    """
    
    Steps:
    1. Fetch user's current skills
    2. Get target role template with required skills
    3. Compare skills:
       - Categorize as missing or needs improvement
       - Calculate gap severity (critical/high/medium/low)
       - Estimate learning time for each skill
    4. Calculate overall readiness percentage
    5. Use LLM to generate insights:
       - Encouraging observations
       - Top 3 priority skills
       - Learning strategy recommendation
       - Timeline assessment

  Methods needed:
    - _compare_skills(user_skills, role_requirements)
    - _calculate_severity(current, required, importance)
    - _calculate_readiness(user_skills, required_skills)
    - _estimate_skill_time(skill, current_prof)
    - _generate_ai_insights(analysis) using LLM

LLM Prompt for insights:
"Analyze this skill gap and provide:
1. 2-3 encouraging observations
2. Top 3 priority skills with reasoning
3. Learning strategy recommendation
4. Realistic timeline
Return as JSON."

app/schemas/skill.py:
- SkillGapAnalysisRequest: target_role
- SkillGap: skill details, gap severity, estimated time
- SkillGapAnalysisResponse: complete analysis

app/api/v1/skills.py:
- POST /skills/analyze-gap
- Cache results in Redis (30 min TTL)

Generate intelligent analysis with actionable insights.
```

### Roadmap Generator Prompt

```
Implement AI roadmap generation:

app/services/ai/roadmap_generator.py:

class RoadmapGenerator:
  async def generate_roadmap(user_id, target_role, duration_weeks, intensity) -> Dict:
    """
    Generate personalized learning roadmap
    
    Steps:
    1. Gather context (profile, skill gap analysis)
    2. Generate roadmap structure using LLM
    3. Enrich with resources
    4. Save to database
    5. Return complete roadmap
    """
    
  async def _generate_structure(context, duration_weeks, intensity):
    """
    LLM Prompt:
    Generate {duration_weeks}-week roadmap for {target_role}.
    
    User:
    - Experience: {experience_level}
    - Daily time: {daily_minutes} minutes
    - Learning style: {learning_style}
    
    Skill Gaps:
    - Readiness: {overall_readiness}%
    - Missing: {missing_skills}
    - To improve: {skills_to_improve}
    
    Requirements:
    - Prioritize critical gaps first
    - Build foundational before advanced
    - Mix reading (30%), practice (50%), projects (20%)
    - Milestone projects every 2-3 weeks
    - Review days weekly
    - Realistic pacing
    
    Output JSON:
    {
      "roadmap_title": "...",
      "weekly_breakdown": [
        {
          "week_number": 1,
          "focus_area": "...",
          "learning_objectives": [...],
          "days": [
            {
              "day_number": 1,
              "tasks": [
                {
                  "title": "Specific task",
                  "description": "Detailed what and why",
                  "task_type": "reading|coding|project|video",
                  "estimated_duration": 90,
                  "difficulty": 3,
                  "success_criteria": "...",
                  "prerequisites": [...]
                }
              ]
            }
          ]
        }
      ],
      "milestones": [...]
    }
    """
  
  async def _add_resources(roadmap):
    """Add learning resources to each task"""
    - Find resources based on task type and skills
    - Max 3 resources per task
    - Include documentation, tutorials, practice sites
  
  async def _save_roadmap(user_id, roadmap_data):
    """Save roadmap and all tasks to database"""

app/api/v1/roadmap.py:
- POST /roadmap/generate
- GET /roadmap/current
- GET /roadmap/{id}/week/{n}
- PUT /roadmap/regenerate

Generate comprehensive, actionable roadmaps.
```

### Deliverables Checklist
- [ ] LLM client working
- [ ] Embeddings generated
- [ ] Skill gap analysis functional
- [ ] Readiness calculation accurate
- [ ] AI insights generated
- [ ] Roadmap generation working
- [ ] Tasks enriched with resources
- [ ] Roadmap saved correctly

---

## PHASE 4: ROADMAP & PROGRESS UI (Hours 11-13)

### Objective
Build beautiful interfaces for viewing roadmaps and tracking progress.

### Roadmap UI Prompt

```
Create interactive roadmap interface:

app/(dashboard)/roadmap/page.tsx:

Layout Components:

1. <RoadmapHeader>:
   - Title and overall progress bar
   - Current week indicator (Week 3 of 12)
   - Quick stats: tasks completed, time spent, streak
   - Actions: Regenerate, Export buttons

2. <WeeklyNavigator>:
   - Horizontal scrollable week cards
   - Each week shows:
     * Week number
     * Focus area
     * Completion percentage
     * Status badge (upcoming/current/completed)
   - Click to view week
   - Smooth scroll animation

3. <WeekView>:
   - Selected week details
   - Week objectives
   - Day-by-day timeline
   - Task cards for each day

4. <TaskCard> (most important component):
   Props: task, onComplete, onSkip
   
   Design:
   - Card with color-coded border (gray/blue/green/orange for pending/in-progress/completed/skipped)
   - Task title (bold)
   - Task type badge
   - Duration with clock icon
   - Difficulty stars (1-5)
   - Status indicator
   - Hover: quick actions
   - Click: open detail modal
   
   States:
   - Pending: gray, no checkmark
   - In Progress: blue, partial fill
   - Completed: green, checkmark
   - Skipped: orange, skip icon

5. <TaskDetailModal>:
   Opens on task click:
   - Full description
   - Success criteria
   - Prerequisites
   - Learning resources (clickable links)
   - Notes section (user can add)
   - Time tracking:
     * Start timer button
     * Manual time entry
     * Difficulty rating (1-5)
     * Confidence rating (1-5)
   - Actions:
     * Mark Complete button
     * Skip with reason dropdown
     * Add to favorites
   
6. <MilestoneMarker>:
   - Shows on timeline at milestone weeks
   - Trophy icon
   - Milestone title
   - What to build/demonstrate
   - Skills demonstrated
   - Completion status

API Hooks:
- useCurrentRoadmap() - React Query
- useWeekTasks(weekNumber)
- useCompleteTask() - Mutation
- useSkipTask() - Mutation
- Optimistic UI updates

State:
- Selected week number
- Task filters
- Modal open/closed

Animations:
- Week cards slide in
- Task completion celebration (confetti)
- Progress bar smooth fill
- Modal fade in/out

Mobile:
- Stack layout
- Swipe between weeks
- Bottom sheet for task details

Generate beautiful, interactive roadmap with smooth UX.
```

### Progress Dashboard Prompt

```
Create comprehensive progress tracking:

app/(dashboard)/progress/page.tsx:

Sections:

1. Overview Stats (4 Cards):
   <StatsCard>:
   - Total Learning Time (with trend)
   - Skills Acquired (with mini chart)
   - Tasks Completed (vs total)
   - Current Streak (with flame icon)
   
   Each card:
   - Large number display
   - Small trend indicator (+/- from last week)
   - Mini sparkline chart
   - Icon

2. Activity Chart:
   <TimeSeriesChart> using Recharts:
   - Line chart showing daily activity
   - Multiple series: time, tasks, skill practice
   - Tooltip on hover
   - Toggle: daily/weekly/monthly view
   - Responsive

3. Skill Progress:
   <SkillRadarChart>:
   - Radar/spider chart
   - Each axis: one skill
   - Shows current vs target proficiency
   - Color gradient fill
   
   <SkillProgressList>:
   - List of all user skills
   - Each skill:
     * Name and category
     * Progress bar (current/target)
     * Proficiency level (1-5)
     * Last practiced date
     * Trend arrow (up/down/stable)
   - Sort options: name, progress, recent

4. Achievements:
   <AchievementGrid>:
   - Grid of badges
   - Earned: color, with date
   - Locked: grayscale
   - Hover: details
   - Recent achievements highlighted

5. Weekly Summary:
   <WeeklySummaryCard>:
   - This week's performance
   - Tasks completed vs planned
   - Time vs goal
   - Skills practiced
   - AI insights:
     * Strengths this week
     * Areas needing attention
     * Suggestions for next week

6. Activity Heatmap:
   <ActivityHeatmap>:
   - GitHub-style contribution graph
   - Color intensity by activity level
   - Hover shows day details
   - Click to see tasks

Charts: Recharts library
- BarChart for comparisons
- LineChart for trends
- RadarChart for skills
- PieChart for time distribution

API Hooks:
- useProgressStats()
- useActivityData(range)
- useSkillGrowth()
- useAchievements()

Filters:
- Date range picker
- Skill category filter
- Chart type toggles

Export:
- Download as PDF
- Export data as CSV

Design:
- Card-based layout
- Consistent color scheme
- Smooth animations
- Interactive tooltips

Generate data-rich, insightful analytics dashboard.
```

### Main Dashboard Prompt

```
Create engaging main dashboard:

app/(dashboard)/dashboard/page.tsx:

Layout Grid:

1. <WelcomeHeader>:
   - Time-based greeting (Good morning/afternoon/evening)
   - User's name
   - Motivational message based on progress
   - Current streak badge
   - Date

2. <QuickStatsGrid> (4 cards):
   - Learning Streak (days + flame icon)
   - Weekly Progress (percentage + circular progress)
   - Skill Points (count + trophy icon)
   - Next Milestone (name + progress bar)

3. <TodaysFocus>:
   - "Your mission today" title
   - 2-3 priority tasks for today
   - Each with:
     * Task title
     * Estimated time
     * Start button
   - Total time estimate
   - Encouraging message

4. <CurrentProgressCard>:
   - Roadmap title
   - Overall progress bar
   - Current week indicator
   - Quick link to full roadmap
   - Mini weekly calendar with completion dots

5. <UpcomingTasksList>:
   - Next 5 tasks across days
   - Each shows:
     * Title
     * When (Tomorrow, In 2 days, etc.)
     * Duration
     * Quick complete checkbox
   - "View all" link

6. <WeekOverview>:
   - 7-day horizontal timeline
   - Each day:
     * Date
     * Tasks count
     * Completion ring
     * Click to see details

7. <ActivityFeed>:
   - Recent activities (last 10):
     * Task completed
     * Skill leveled up
     * Achievement earned
     * Milestone reached
   - Each activity:
     * Icon
     * Message
     * Timestamp
     * Link to details

8. <QuickActions> (Floating buttons):
   - Chat with Mentor
   - Add Manual Task
   - Update Skills
   - View Resume

Interactions:
- Hover animations on cards
- Smooth transitions
- Confetti on achievements
- Real-time progress updates

Mobile:
- Stack vertically
- Swipe between sections
- Bottom navigation

Empty States:
- No roadmap: Onboarding CTA
- No tasks today: Rest day celebration
- New user: Helpful tips

Notifications:
- Daily reminder
- Streak at risk
- New achievement
- Milestone approaching

Generate motivational dashboard that drives engagement.
```

### Deliverables Checklist
- [ ] Roadmap page functional
- [ ] Week navigation smooth
- [ ] Task cards displaying
- [ ] Task modal complete
- [ ] Progress charts working
- [ ] Skill radar chart
- [ ] Activity heatmap
- [ ] Dashboard layout complete
- [ ] All animations smooth

---

## PHASE 5: AI MENTOR CHAT (Hours 14-16)

### Objective
Implement intelligent chat mentor with context awareness.

### Chat Backend Prompt

```
Build context-aware chat system:

app/services/ai/chat_engine.py:

class MentorChatEngine:
  async def chat(user_id, message, session_id=None) -> Dict:
    """
    Process message and generate response
    
    Returns:
    {
      "session_id": str,
      "response": {
        "message": str,
        "suggestions": List[Dict],
        "context_used": Dict
      }
    }
    """
    
    Steps:
    1. Get/create session
    2. Gather user context:
       - Profile (goal, experience, learning style)
       - Current roadmap (title, week, completion)
       - Recent activity (tasks, time, streak)
       - Current skills
       - Recent struggles
       - Achievements
       - Past conversation memories
    
    3. Analyze intent:
       - asking_for_help
       - requesting_explanation
       - seeking_motivation
       - reporting_struggle
       - asking_next_steps
       - requesting_resources
       
       Extract:
       - Mentioned skills/topics
       - Emotional tone
       - Specific question
    
    4. Generate response with LLM:
       System Prompt:
       "You are {user_name}'s personal AI career mentor.
       
       About your mentee:
       - Goal: {goal_role}
       - Experience: {experience_level}
       - Progress: {completion}%
       - Streak: {streak_days} days
       - Recent: Completed {tasks} tasks this week
       
       Your role:
       - Supportive, knowledgeable advisor
       - Know their entire journey
       - Specific, actionable guidance
       - Balance encouragement with honesty
       - Celebrate progress, empathize with struggles
       
       Communication:
       - Warm and approachable
       - Use their name: {name}
       - Reference specific journey details
       - Conversational, not robotic
       - Show enthusiasm
       "
       
       User Prompt:
       "Message: {message}
       
       Context: {context_summary}
       Intent: {detected_intent}
       Tone: {emotional_tone}
       
       Generate helpful, personalized response (2-4 paragraphs).
       Be encouraging, specific, and actionable."
    
    5. Generate suggestions:
       Based on intent:
       - Start next task
       - Find resources for mentioned skill
       - View progress
       - Practice struggling skill
       
       Max 3 suggestions
    
    6. Save conversation to MongoDB
    
    7. Update session metadata

  Methods:
    - _gather_user_context(user_id)
    - _analyze_intent(message, context)
    - _generate_response(message, history, context, intent)
    - _generate_suggestions(context, intent)
    - _save_conversation(session_id, messages, context)

MongoDB Schema:
{
  session_id: UUID,
  user_id: UUID,
  messages: [
    {
      role: "user" | "assistant",
      content: str,
      timestamp: datetime,
      context_used: {}
    }
  ],
  updated_at: datetime
}

app/api/v1/mentor.py:
- POST /mentor/chat
- GET /mentor/sessions
- GET /mentor/session/{id}
- DELETE /mentor/session/{id}

Generate intelligent, context-aware mentor.
```

### Chat UI Prompt

```
Create beautiful chat interface:

app/(dashboard)/mentor/page.tsx:

Layout:
- Sidebar (session history)
- Main chat area
- Bottom input

Components:

1. <ChatHeader>:
   - "Your AI Mentor" title
   - Online indicator (pulsing green dot)
   - Messages this week count
   - Menu: New chat, Settings, Export

2. <SessionSidebar>:
   - New conversation button
   - List of past sessions:
     * Auto-generated title
     * Date
     * Message preview
     * Count badge
   - Click to load
   - Delete on hover
   - Search sessions

3. <MessageList>:
   - Scrollable container
   - Auto-scroll to bottom
   - Messages grouped by date
   - Loading indicator
   - Typing indicator

4. <MessageBubble>:
   Props: message, role, timestamp
   
   User messages:
   - Right-aligned
   - Blue background
   - Rounded corners
   - User avatar (initials)
   - Timestamp below
   
   Assistant messages:
   - Left-aligned
   - Gray background
   - AI avatar icon
   - Timestamp
   - Markdown support
   - Code blocks with syntax highlighting
   - Clickable links
   - Fade-in animation
   
   Message actions (hover):
   - Copy text
   - Regenerate (AI only)
   - Like/helpful
   - Flag

5. <TypingIndicator>:
   - Three animated dots
   - "Mentor is typing..."
   - Assistant bubble style

6. <SuggestionCards>:
   - Horizontal scroll
   - 2-3 cards after AI response
   - Each card:
     * Icon
     * Title
     * Brief description
     * Click to execute action
   - Slide-in animation

7. <ChatInput>:
   - Auto-expanding textarea (1-5 lines)
   - Placeholder: "Ask your mentor anything..."
   - Send button (disabled while typing)
   - Shift+Enter for new line
   - Enter to send
   - Character count (optional)
   - File attach (future)
   - Voice input (future)

8. Quick Action Chips:
   Pre-written prompts:
   - "What should I focus on today?"
   - "How's my progress?"
   - "Help with current task"
   - "Suggest resources"

Features:
- Context indicators (small badges)
- Code highlighting (Prism.js)
- Link previews
- Keyboard shortcuts (Ctrl+K focus, Ctrl+N new chat)

API Hooks:
- useSendMessage() - Mutation
- useSessions()
- useSession(id)
- Auto-scroll
- Optimistic updates

State:
- Current session
- Messages array
- Is typing
- Suggestions

Animations:
- Messages fade in
- Suggestions slide
- Typing indicator pulse
- Smooth scrolling

Mobile:
- Full screen
- Swipe sidebar
- Bottom input
- One-hand friendly

Accessibility:
- ARIA labels
- Keyboard navigation
- Screen reader support

Generate delightful chat experience.
```

### Deliverables Checklist
- [ ] Chat backend complete
- [ ] Context gathering working
- [ ] Intent detection functional
- [ ] AI responses generated
- [ ] Conversations saved
- [ ] Chat UI functional
- [ ] Messages rendering
- [ ] Typing indicator
- [ ] Suggestions displaying
- [ ] Session management

---

## PHASE 6: RESUME & POLISH (Hours 17-20)

### Objective
Complete resume system and final polish.

### Resume System Prompt

```
Implement resume generation:

app/services/resume_service.py:

class ResumeService:
  async def generate_initial_resume(user_id):
    """Generate first resume from profile"""
    - Fetch profile and skills
    - Generate AI summary
    - Organize skills by category
    - Format education
    - Create resume record
  
  async def auto_update_resume(user_id, trigger_type, data):
    """
    Auto-update on:
    - skill_completed
    - project_completed
    - milestone_reached
    - proficiency_improved
    """
    - Get current resume
    - Apply updates based on trigger
    - Create new version
    - Save to database
  
  async def _generate_summary(profile, skills):
    """AI-generate professional summary"""
    LLM Prompt:
    "Generate resume summary (2-3 sentences).
    
    Profile:
    - Goal: {goal_role}
    - Experience: {experience_level}
    - Skills: {top_5_skills}
    
    Requirements:
    - Professional tone
    - Highlight strengths
    - Growth mindset
    - Career goal
    - 50-70 words
    "
  
  async def tailor_resume_to_job(user_id, job_description):
    """Tailor for specific job"""
    - Extract job requirements using AI
    - Match user skills to requirements
    - Generate tailored summary
    - Rank projects by relevance
    - Calculate match score (0-100)
    - Generate improvement suggestions
    
    Returns:
    {
      "tailored_summary": str,
      "matched_skills": List,
      "relevant_projects": List,
      "match_score": float,
      "suggestions": List
    }

app/api/v1/resume.py:
- GET /resume/current
- POST /resume/generate
- POST /resume/auto-update
- POST /resume/tailor
- GET /resume/export?format=pdf

Generate smart resume management.
```

### Resume UI Prompt

```
Create resume builder:

app/(dashboard)/resume/page.tsx:

Tabs: Preview | Edit | Tailor

TAB 1: PREVIEW

<ResumePreview>:
Professional layout:

1. Header:
   - Name (large, bold)
   - Contact (email, phone, LinkedIn, GitHub)
   - Location

2. Summary:
   - 2-3 sentences
   - Inline edit button

3. Skills:
   - Grouped by category
   - Visual proficiency dots
   - Tag chips

4. Projects:
   - Name, description
   - Technologies
   - Links (GitHub, demo)

5. Experience:
   - Company, role, dates
   - Bullet points

6. Education:
   - Degree, institution
   - Graduation year

Actions:
- Download PDF
- Download DOCX
- Copy text
- Share link
- Print

TAB 2: EDIT

<ResumeEditor>:
Editable sections:
- Each section: Add, Edit, Delete, Reorder
- Drag handles for reordering

<SectionEditor>:
Skills:
- Multi-select dropdown
- Proficiency sliders
- Category organization
- "Add from roadmap"

Projects:
- Title, description inputs
- Technology tags
- URLs (GitHub, demo)
- Dates

Experience:
- Company, role, dates
- Bullet point editor
- AI suggestion button

Education:
- Degree, institution
- Dates, GPA

Auto-save on change
Version indicator

TAB 3: TAILOR

<ResumeTailor>:
- Job description textarea
- "Analyze & Tailor" button

After analysis:

<MatchAnalysis>:
- Match score with visual
- Matched skills (green checks)
- Missing skills (suggestions)
- Highlighted relevant experience

<TailoredVersion>:
- Side-by-side comparison
- Highlighted changes
- "Apply changes"
- "Download tailored"

<ImprovementSuggestions>:
- AI suggestions list
- Click to apply

Components:
- SkillTags.tsx (chips with proficiency)
- BulletPointGenerator.tsx (AI-powered)

API:
- useResume()
- useUpdateSection()
- useTailorResume()
- useExport()

Design:
- Professional fonts
- Clean layout
- Print-optimized
- ATS-friendly

Generate comprehensive resume builder.
```

### Final Polish Prompt

```
Production readiness tasks:

1. ERROR HANDLING:
   - Error boundary components
   - Global API error handler
   - User-friendly messages
   - Retry mechanisms
   - Fallback UI
   - Error logging

2. LOADING STATES:
   - Skeleton screens for pages
   - Spinners for actions
   - Progress bars
   - Optimistic updates
   - Prevent double submissions

3. RESPONSIVE DESIGN:
   - Test mobile/tablet/desktop
   - Touch-friendly (44px min)
   - Proper breakpoints
   - No horizontal scroll

4. ACCESSIBILITY:
   - ARIA labels
   - Keyboard navigation
   - Focus indicators
   - Screen reader support
   - WCAG AA contrast
   - Alt text

5. PERFORMANCE:
   - Code splitting
   - Lazy loading
   - Image optimization
   - API caching
   - Debounce inputs
   - Virtual scrolling
   - Memoization

6. SECURITY:
   - XSS protection
   - CSRF tokens
   - SQL injection prevention
   - Secure headers
   - Rate limiting
   - Input sanitization

7. TESTING:
   Backend:
   - pytest unit tests
   - API endpoint tests
   - Auth flow tests
   - Mock external APIs
   
   Frontend:
   - Jest + React Testing Library
   - Component tests
   - Integration tests
   - E2E with Playwright

8. DOCUMENTATION:
   - API docs (Swagger)
   - README setup
   - Environment vars
   - Architecture diagrams

9. DEPLOYMENT:
   - Environment configs
   - Migration scripts
   - Seed data
   - Health checks
   - Monitoring (Sentry)
   - CI/CD pipeline
   - Docker containers

Implement comprehensive QA.
```

### Deliverables Checklist
- [ ] Resume generation working
- [ ] Auto-update functional
- [ ] Resume preview
- [ ] Resume editor
- [ ] Job tailoring
- [ ] PDF export
- [ ] Error boundaries
- [ ] Loading states
- [ ] Mobile responsive
- [ ] Accessibility
- [ ] Performance optimized
- [ ] Tests passing
- [ ] Deployment ready

---

## PHASE 7: DEMO PREP (Hours 21-24)

### Demo Preparation Prompt

```
Prepare impressive demo:

1. DEMO DATA:
Create seed data for demo account:
- User: Alex Chen
- Goal: Full Stack Developer
- 40% through 12-week roadmap
- 5 skills acquired
- 2 projects completed
- 7-day streak
- Mix of completed/pending tasks
- Chat history
- Some achievements

2. DEMO FLOW (3-4 minutes):

Act 1 - Problem (30s):
- Show fragmented tools
- Pain points

Act 2 - Solution (30s):
- Introduce AI Life Mentor
- Value props

Act 3 - Features (2m):
- Onboarding (15s)
- Skill Gap (20s)
- Roadmap (30s)
- Progress (20s)
- Chat (30s)
- Resume (15s)

Act 4 - Impact (30s):
- Before/after
- Call to action

3. PRESENTATION SLIDES:
1. Title (app name, tagline, team)
2. Problem (stats, gaps)
3. Solution (key features)
4. Demo (live)
5. Technology (stack, AI)
6. Market (users, size)
7. Future (roadmap)
8. Team (bios, contact)

4. DEMO SCRIPT:
Write narration for each screen with timing

5. VISUAL POLISH:
- Smooth transitions
- Highlight features
- Consistent colors
- No lorem ipsum
- Professional imagery

6. BACKUP:
- Offline video
- Screenshots
- Q&A prep

7. PRACTICE:
- Rehearse timing
- Test transitions
- Prepare for questions

8. ENVIRONMENT:
- Clean browser
- Full screen
- Proper resolution
- Test on presentation screen
- Backup device
- Charger

Create compelling demo content.
```

### Final Checklist

**Pre-Demo:**
- [ ] All features working
- [ ] Demo account seeded
- [ ] Script memorized
- [ ] Slides ready
- [ ] Backup video
- [ ] App deployed
- [ ] No errors
- [ ] Fast loads
- [ ] Multi-browser tested
- [ ] Team roles assigned

**During Demo:**
- [ ] Confident delivery
- [ ] Show, don't tell
- [ ] Engage audience
- [ ] Highlight unique value
- [ ] Demonstrate AI
- [ ] Real-time interactions
- [ ] Strong CTA

**Post-Demo:**
- [ ] Answer clearly
- [ ] Collect feedback
- [ ] Share demo link
- [ ] Follow up
- [ ] Document learnings

---

## 🎯 SUCCESS METRICS

**Hackathon Judging:**
1. Innovation (25%) - Novel AI approach
2. Execution (25%) - Completeness, polish
3. Impact (25%) - Problem significance
4. Presentation (25%) - Clarity, engagement

**Your Advantages:**
✅ Real problem
✅ Sophisticated AI (not just API calls)
✅ Full-stack completeness
✅ Professional UX
✅ Deep personalization
✅ Multiple integrated features

---

## 🚀 POST-HACKATHON ROADMAP

**Immediate:**
- User feedback
- Bug fixes
- Performance tuning

**Short-term (1-3 months):**
- Mobile app
- Social features
- Gamification
- Platform integrations
- Advanced analytics

**Long-term (6-12 months):**
- Monetization
- Multi-language
- Voice interactions
- Employer partnerships
- Certification programs

---

## 📝 FINAL NOTES

**Remember:**
- Focus on MVP first
- Polish matters for demos
- Real value beats flashy features
- AI enhances, doesn't replace
- Good UX = competitive advantage
- Practice your pitch!

**Good luck! 🎉**

This project can make real impact on how people learn and grow. Execute well, present confidently, and you'll have a strong contender!
