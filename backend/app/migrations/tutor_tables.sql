-- ============================================================
-- AgentRAG-Tutor — New Tables Migration
-- Run this in Supabase SQL editor after the base schema.
-- ============================================================

-- ============================================================
-- TABLE: knowledge_documents
-- Educational content stored for RAG retrieval.
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    topic               VARCHAR(255)    NOT NULL,
    subtopic            VARCHAR(255),
    content             TEXT            NOT NULL,
    chunk_index         INTEGER         DEFAULT 0,
    source              VARCHAR(500),
    difficulty_level    INTEGER         DEFAULT 1,
    metadata            JSONB,
    created_at          TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_knowledge_documents_topic ON knowledge_documents (topic);

-- ============================================================
-- TABLE: knowledge_states
-- BKT per-user per-skill mastery state.
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_states (
    id                      UUID    NOT NULL DEFAULT gen_random_uuid(),
    user_id                 UUID    NOT NULL,
    skill_id                UUID    NOT NULL,
    p_mastery               FLOAT   DEFAULT 0.1,
    p_init                  FLOAT   DEFAULT 0.1,
    p_learn                 FLOAT   DEFAULT 0.3,
    p_guess                 FLOAT   DEFAULT 0.25,
    p_slip                  FLOAT   DEFAULT 0.1,
    attempts                INTEGER DEFAULT 0,
    correct_count           INTEGER DEFAULT 0,
    consecutive_correct     INTEGER DEFAULT 0,
    consecutive_incorrect   INTEGER DEFAULT 0,
    last_updated            TIMESTAMP DEFAULT NOW(),
    created_at              TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id)  REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills_master (id) ON DELETE CASCADE,
    UNIQUE (user_id, skill_id)
);

CREATE INDEX IF NOT EXISTS ix_knowledge_states_user_id  ON knowledge_states (user_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_states_skill_id ON knowledge_states (skill_id);

-- ============================================================
-- TABLE: tutor_questions
-- Question bank for adaptive tutoring.
-- ============================================================
CREATE TABLE IF NOT EXISTS tutor_questions (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    skill_id            UUID,
    topic               VARCHAR(255)    NOT NULL,
    difficulty          INTEGER         DEFAULT 1,
    question_type       VARCHAR(50)     DEFAULT 'multiple_choice',
    question_text       TEXT            NOT NULL,
    correct_answer      TEXT            NOT NULL,
    distractors         JSONB,
    explanation         TEXT,
    hints               JSONB,
    tags                JSONB,
    is_ai_generated     BOOLEAN         DEFAULT FALSE,
    times_served        INTEGER         DEFAULT 0,
    avg_correct_rate    FLOAT,
    created_at          TIMESTAMP       DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (skill_id) REFERENCES skills_master (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_tutor_questions_topic      ON tutor_questions (topic);
CREATE INDEX IF NOT EXISTS ix_tutor_questions_difficulty  ON tutor_questions (difficulty);

-- ============================================================
-- TABLE: student_responses
-- Record of every student answer — feeds BKT updates.
-- ============================================================
CREATE TABLE IF NOT EXISTS student_responses (
    id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
    user_id                 UUID        NOT NULL,
    question_id             UUID,
    skill_id                UUID,
    session_id              UUID,
    student_answer          TEXT        NOT NULL,
    is_correct              BOOLEAN     NOT NULL,
    response_time_seconds   INTEGER,
    difficulty_at_time      INTEGER,
    bkt_mastery_before      FLOAT,
    bkt_mastery_after       FLOAT,
    evaluation_feedback     TEXT,
    partial_credit          FLOAT,
    created_at              TIMESTAMP   DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id)     REFERENCES users (id)            ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES tutor_questions (id)  ON DELETE SET NULL,
    FOREIGN KEY (skill_id)    REFERENCES skills_master (id)    ON DELETE CASCADE,
    FOREIGN KEY (session_id)  REFERENCES chat_sessions (id)    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_student_responses_user_id ON student_responses (user_id);
CREATE INDEX IF NOT EXISTS ix_student_responses_skill_id ON student_responses (skill_id);

-- ============================================================
-- TABLE: rl_policy_states
-- RL agent state per user (bandit arms + Q-table).
-- ============================================================
CREATE TABLE IF NOT EXISTS rl_policy_states (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL,
    bandit_state        JSONB       DEFAULT '{}',
    q_table             JSONB,
    epsilon             FLOAT       DEFAULT 0.3,
    total_interactions  INTEGER     DEFAULT 0,
    last_updated        TIMESTAMP   DEFAULT NOW(),
    created_at          TIMESTAMP   DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE (user_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_rl_policy_states_user_id ON rl_policy_states (user_id);

-- ============================================================
-- SEED: 5 KC anchor skills (Paper Section 5.2.2, Table 2).
-- The runtime resolver in app/services/ai/bkt/kc_mapping.py looks up these
-- rows by name. Idempotent — safe to re-run.
-- ============================================================
-- The legacy ``skills_master`` schema does not declare a DEFAULT on ``id``,
-- so we must supply the UUID explicitly here. ``pgcrypto`` provides
-- ``gen_random_uuid``; the extension is enabled on Supabase by default but
-- we ensure it idempotently for portability.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO skills_master (id, skill_name, category, difficulty_level, description)
VALUES
    (gen_random_uuid(), 'AI Agents & ML Intro',     'AI Fundamentals', 2, 'KC1 — Intelligent agents, PEAS, rational behaviour, ML introduction.'),
    (gen_random_uuid(), 'Search & CSP',             'AI Fundamentals', 3, 'KC2 — BFS/DFS, A*, heuristics, constraint satisfaction, minimax.'),
    (gen_random_uuid(), 'Knowledge Representation', 'AI Fundamentals', 3, 'KC3 — Propositional & first-order logic, Bayesian inference, ontologies.'),
    (gen_random_uuid(), 'Planning & Heuristics',    'AI Fundamentals', 4, 'KC4 — STRIPS/PDDL, graph-plan, partial-order planning, admissible heuristics.'),
    (gen_random_uuid(), 'Learning & Game AI',       'AI Fundamentals', 4, 'KC5 — Supervised/unsupervised/reinforcement learning, MCTS, game-playing AI.')
ON CONFLICT (skill_name) DO NOTHING;

-- ============================================================
-- SEED: 5 KC anchor skills for the second course (Operating Systems).
-- Path 1 — multi-domain validation for the IEEE paper. Idempotent.
-- ============================================================
INSERT INTO skills_master (id, skill_name, category, difficulty_level, description)
VALUES
    (gen_random_uuid(), 'Processes & Threads',           'Operating Systems', 2, 'OS-KC1 — Process model, threads, fork/exec, context switching, IPC.'),
    (gen_random_uuid(), 'CPU Scheduling',                'Operating Systems', 3, 'OS-KC2 — FCFS/SJF/RR/MLFQ, preemption, quantum, fairness metrics.'),
    (gen_random_uuid(), 'Memory Management',             'Operating Systems', 3, 'OS-KC3 — Paging, segmentation, virtual memory, TLB, page replacement.'),
    (gen_random_uuid(), 'Concurrency & Synchronization', 'Operating Systems', 4, 'OS-KC4 — Mutex/semaphore, deadlock, race conditions, monitors, banker''s.'),
    (gen_random_uuid(), 'File Systems & I/O',            'Operating Systems', 3, 'OS-KC5 — Inodes, journaling, disk scheduling, RAID, VFS, page cache.')
ON CONFLICT (skill_name) DO NOTHING;