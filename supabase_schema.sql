-- ============================================================
-- AImentor — Supabase / PostgreSQL Schema
-- ============================================================
-- Paste this entire file into the Supabase SQL editor and run.
-- Safe to re-run: uses CREATE TABLE IF NOT EXISTS + CREATE INDEX
-- IF NOT EXISTS throughout.
--
-- Tables (12):
--   users, user_profiles, skills_master, role_templates,
--   user_skills, roadmaps, roadmap_tasks, resumes,
--   chat_sessions, progress_logs, achievements, user_streaks
--
-- Note: MongoDB was used only for chat_sessions in an earlier
-- version of this project.  That data now lives in the
-- chat_sessions table below (messages stored as JSONB).
-- There is NO MongoDB dependency in the current codebase.
-- ============================================================

-- Required for gen_random_uuid() in older Postgres versions.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    email               VARCHAR(255)    NOT NULL,
    password_hash       VARCHAR(255)    NOT NULL,
    full_name           VARCHAR(255)    NOT NULL,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    is_verified         BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    last_login          TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);


-- ============================================================
-- TABLE: user_profiles
-- One row per user (enforced by UNIQUE on user_id).
-- All structured resume data (education, experience, projects,
-- certifications, extracurricular, technical_skills) is stored
-- as JSONB arrays in *_data columns.  The resume table mirrors
-- these into *_section columns for the PDF renderer.
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id                              UUID            NOT NULL DEFAULT gen_random_uuid(),
    user_id                         UUID            NOT NULL,
    goal_role                       VARCHAR(255),
    experience_level                VARCHAR(50),        -- beginner | intermediate | advanced
    current_education               VARCHAR(255),
    graduation_year                 INTEGER,
    time_per_day                    INTEGER         DEFAULT 60,     -- minutes/day
    preferred_learning_style        VARCHAR(50),        -- visual | reading | hands-on | mixed
    onboarding_completed            TIMESTAMP,
    profile_completion_percentage   INTEGER         DEFAULT 0,
    bio                             TEXT,
    linkedin_url                    VARCHAR(255),
    github_url                      VARCHAR(255),
    portfolio_url                   VARCHAR(255),
    phone                           VARCHAR(50),
    location                        VARCHAR(255),
    website_url                     VARCHAR(255),
    -- Structured resume data (arrays of objects)
    education_data                  JSONB,          -- [{institution, degree, field_of_study, start_year, end_year, cgpa, location}]
    experience_data                 JSONB,          -- [{company, role, location, start_date, end_date, bullet_points[]}]
    projects_data                   JSONB,          -- [{title, description, technologies[], highlights[], github_url, demo_url}]
    certifications_data             JSONB,          -- [{name, issuer, date_obtained, credential_url}]
    extracurricular_data            JSONB,          -- [{organization, role, start_date, end_date, location, achievements[]}]
    technical_skills_data           JSONB,          -- {languages[], frameworks_and_tools[], databases[], cloud_platforms[], other[]}
    created_at                      TIMESTAMP       DEFAULT NOW(),
    updated_at                      TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE (user_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_user_profiles_user_id ON user_profiles (user_id);


-- ============================================================
-- TABLE: skills_master
-- Global skill library seeded from backend/scripts/seed_skills.py
-- ============================================================
CREATE TABLE IF NOT EXISTS skills_master (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    skill_name          VARCHAR(255)    NOT NULL,
    category            VARCHAR(100)    NOT NULL,   -- frontend | backend | database | devops | ml | mobile …
    subcategory         VARCHAR(100),
    description         TEXT,
    difficulty_level    INTEGER         DEFAULT 1,  -- 1-5
    market_demand_score FLOAT           DEFAULT 0.5,-- 0.0-1.0
    related_skills      VARCHAR[],
    learning_resources  JSONB,                      -- [{title, url, type, duration_hours}]
    created_at          TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_skills_master_skill_name ON skills_master (skill_name);
CREATE INDEX IF NOT EXISTS ix_skills_master_category ON skills_master (category);


-- ============================================================
-- TABLE: role_templates
-- Pre-defined role skill requirements used by skill-gap analysis.
-- ============================================================
CREATE TABLE IF NOT EXISTS role_templates (
    id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
    role_name               VARCHAR(255)    NOT NULL,
    level                   VARCHAR(50),            -- junior | mid | senior
    description             TEXT,
    required_skills         JSONB           NOT NULL,  -- [{skill_id, min_proficiency}]
    preferred_skills        JSONB,
    responsibilities        VARCHAR[],
    average_salary_range    VARCHAR(100),
    demand_score            FLOAT           DEFAULT 0.5,
    created_at              TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_role_templates_role_name ON role_templates (role_name);


-- ============================================================
-- TABLE: user_skills
-- Junction: which skills a user has, at what proficiency.
-- ============================================================
CREATE TABLE IF NOT EXISTS user_skills (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    user_id             UUID            NOT NULL,
    skill_id            UUID            NOT NULL,
    proficiency_level   INTEGER         DEFAULT 1,  -- 1-5
    target_proficiency  INTEGER         DEFAULT 3,
    acquired_date       DATE,
    last_practiced      TIMESTAMP,
    practice_hours      FLOAT           DEFAULT 0,
    confidence_rating   INTEGER         DEFAULT 1,  -- 1-5
    notes               TEXT,
    created_at          TIMESTAMP       DEFAULT NOW(),
    updated_at          TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id)  REFERENCES users (id)         ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills_master (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_user_skills_user_id  ON user_skills (user_id);
CREATE INDEX IF NOT EXISTS ix_user_skills_skill_id ON user_skills (skill_id);


-- ============================================================
-- TABLE: roadmaps
-- One active roadmap per user at a time.
-- ============================================================
CREATE TABLE IF NOT EXISTS roadmaps (
    id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
    user_id                 UUID            NOT NULL,
    title                   VARCHAR(255)    NOT NULL,
    description             TEXT,
    target_role             VARCHAR(255),
    total_weeks             INTEGER         DEFAULT 12,
    start_date              DATE,
    end_date                DATE,
    completion_percentage   FLOAT           DEFAULT 0,
    status                  VARCHAR(50)     DEFAULT 'active', -- active | paused | completed | abandoned
    milestones              JSONB,          -- [{week, title, description}]
    generation_params       JSONB,          -- LLM params used for generation
    created_at              TIMESTAMP       DEFAULT NOW(),
    updated_at              TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_roadmaps_user_id ON roadmaps (user_id);
CREATE INDEX IF NOT EXISTS ix_roadmaps_status  ON roadmaps (status);


-- ============================================================
-- TABLE: roadmap_tasks
-- Individual learning tasks within a roadmap.
-- ============================================================
CREATE TABLE IF NOT EXISTS roadmap_tasks (
    id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
    roadmap_id              UUID            NOT NULL,
    week_number             INTEGER         NOT NULL,
    day_number              INTEGER         NOT NULL,   -- 1-7
    order_in_day            INTEGER         DEFAULT 1,
    task_title              VARCHAR(255)    NOT NULL,
    task_description        TEXT,
    task_type               VARCHAR(50)     DEFAULT 'reading', -- reading | coding | project | video | quiz
    estimated_duration      INTEGER         DEFAULT 60,        -- minutes
    difficulty              INTEGER         DEFAULT 1,         -- 1-5
    learning_objectives     VARCHAR[],
    success_criteria        TEXT,
    prerequisites           VARCHAR[],
    resources               JSONB,          -- [{title, url, type, duration_hours}]
    status                  VARCHAR(50)     DEFAULT 'pending', -- pending | in_progress | completed | skipped
    completed_at            TIMESTAMP,
    skipped_reason          VARCHAR(255),
    notes                   TEXT,
    is_favorite             BOOLEAN         DEFAULT FALSE,
    created_at              TIMESTAMP       DEFAULT NOW(),
    updated_at              TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (roadmap_id) REFERENCES roadmaps (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_roadmap_tasks_roadmap_id   ON roadmap_tasks (roadmap_id);
CREATE INDEX IF NOT EXISTS ix_roadmap_tasks_week_number  ON roadmap_tasks (week_number);
CREATE INDEX IF NOT EXISTS ix_roadmap_tasks_status       ON roadmap_tasks (status);


-- ============================================================
-- TABLE: resumes
-- Multi-version resume store.  Each version has full JSONB
-- sections mirrored from user_profiles.*_data by the backend
-- sync service.  The PDF renderer reads from this table only.
--
-- Previously chat sessions lived in MongoDB — they are now
-- in the chat_sessions table.  This table has always been
-- PostgreSQL only.
-- ============================================================
CREATE TABLE IF NOT EXISTS resumes (
    id                          UUID            NOT NULL DEFAULT gen_random_uuid(),
    user_id                     UUID            NOT NULL,
    version                     INTEGER         DEFAULT 1,
    is_active                   BOOLEAN         DEFAULT TRUE,
    draft_name                  VARCHAR(255),               -- e.g. "Google SWE Application"
    parent_version_id           UUID,                       -- cloned from this version
    is_base_version             BOOLEAN         DEFAULT TRUE,
    job_description             TEXT,                       -- JD this version was tailored for
    summary                     TEXT,
    skills_section              JSONB,          -- {category: [{name, proficiency}]}
    coursework_section          JSONB,
    projects_section            JSONB,          -- [{title, description, technologies[], highlights[], github_url, demo_url}]
    experience_section          JSONB,          -- [{company, role, location, start_date, end_date, bullet_points[]}]
    education_section           JSONB,          -- [{institution, degree, field_of_study, start_year, end_year, cgpa, location}]
    certifications_section      JSONB,          -- [{name, issuer, date_obtained, credential_url}]
    extracurricular_section     JSONB,          -- [{organization, role, start_date, end_date, location, achievements[]}]
    technical_skills_section    JSONB,          -- {languages[], frameworks_and_tools[], databases[], cloud_platforms[], other[]}
    contact_info                JSONB,          -- {name, email, phone, location, linkedin_url, github_url, portfolio_url}
    tailored_for                VARCHAR(255),               -- job title if tailored
    match_score                 INTEGER,                    -- 0-100 ATS match score
    created_at                  TIMESTAMP       DEFAULT NOW(),
    updated_at                  TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_resumes_user_id   ON resumes (user_id);
CREATE INDEX IF NOT EXISTS ix_resumes_is_active ON resumes (is_active);


-- ============================================================
-- TABLE: chat_sessions
-- Stores AI mentor conversations.
-- MIGRATION NOTE: This table replaces the former MongoDB
-- `chat_sessions` collection.  Messages are stored in a single
-- JSONB column (array of {role, content, timestamp} objects).
-- Memory is a JSONB object containing extracted context/facts.
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          UUID            NOT NULL DEFAULT gen_random_uuid(),
    user_id     UUID            NOT NULL,
    title       VARCHAR(255),                   -- auto-generated from first message
    messages    JSONB           NOT NULL DEFAULT '[]'::jsonb,
                                                -- [{role: "user"|"assistant", content: "...", timestamp: "..."}]
    memory      JSONB,                          -- {facts: [], preferences: [], goals: []}
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP       NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id    ON chat_sessions (user_id);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_updated_at ON chat_sessions (updated_at DESC);


-- ============================================================
-- TABLE: progress_logs
-- Each row is a task-completion or task-skip event.
-- ============================================================
CREATE TABLE IF NOT EXISTS progress_logs (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL,
    task_id             UUID,                   -- NULL if logging time without a specific task
    time_spent          INTEGER     DEFAULT 0,  -- minutes
    started_at          TIMESTAMP,
    ended_at            TIMESTAMP,
    difficulty_rating   INTEGER,                -- 1-5
    confidence_rating   INTEGER,                -- 1-5
    enjoyment_rating    INTEGER,                -- 1-5
    notes               TEXT,
    struggles           TEXT,
    created_at          TIMESTAMP   DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)          ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES roadmap_tasks (id)  ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_progress_logs_user_id    ON progress_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_progress_logs_task_id    ON progress_logs (task_id);
CREATE INDEX IF NOT EXISTS ix_progress_logs_created_at ON progress_logs (created_at DESC);


-- ============================================================
-- TABLE: achievements
-- Badges and milestones earned by a user.
-- ============================================================
CREATE TABLE IF NOT EXISTS achievements (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    user_id             UUID            NOT NULL,
    achievement_type    VARCHAR(100)    NOT NULL,   -- streak | skill | milestone | completion
    achievement_name    VARCHAR(255)    NOT NULL,
    description         TEXT,
    icon                VARCHAR(100),
    achievement_data    JSONB,                      -- arbitrary metadata for the achievement
    earned_at           TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_achievements_user_id ON achievements (user_id);


-- ============================================================
-- TABLE: user_streaks
-- One row per user; updated on every task completion.
-- ============================================================
CREATE TABLE IF NOT EXISTS user_streaks (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL,
    current_streak      INTEGER     DEFAULT 0,
    longest_streak      INTEGER     DEFAULT 0,
    last_activity_date  TIMESTAMP,
    tasks_this_week     INTEGER     DEFAULT 0,
    time_this_week      INTEGER     DEFAULT 0,  -- minutes
    updated_at          TIMESTAMP   DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE (user_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_user_streaks_user_id ON user_streaks (user_id);


-- ============================================================
-- OPTIONAL: Row-Level Security (Supabase Auth)
-- Uncomment these once you wire up Supabase Auth so that
-- users can only read/write their own data.
-- ============================================================
-- ALTER TABLE user_profiles         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE resumes                ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE roadmaps               ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE roadmap_tasks          ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_skills            ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_sessions          ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE progress_logs          ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE achievements           ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_streaks           ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "own_profiles"   ON user_profiles   FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_resumes"    ON resumes          FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_roadmaps"   ON roadmaps         FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_tasks"      ON roadmap_tasks    FOR ALL USING (roadmap_id IN (SELECT id FROM roadmaps WHERE user_id = auth.uid()));
-- CREATE POLICY "own_skills"     ON user_skills      FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_chats"      ON chat_sessions    FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_progress"   ON progress_logs    FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_achieve"    ON achievements     FOR ALL USING (user_id = auth.uid());
-- CREATE POLICY "own_streaks"    ON user_streaks     FOR ALL USING (user_id = auth.uid());

-- Public read on skill library and role templates:
-- ALTER TABLE skills_master  ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE role_templates ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "public_skills"    ON skills_master   FOR SELECT USING (TRUE);
-- CREATE POLICY "public_roles"     ON role_templates  FOR SELECT USING (TRUE);
