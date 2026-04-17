-- AImentor — Supabase schema
-- Paste this into the Supabase SQL editor and run.
-- Generated from SQLAlchemy models; do not hand-edit. Regenerate with:
--   cd backend && python scripts/dump_supabase_schema.py

-- Required extension for gen_random_uuid() if you ever switch server-side UUID defaults.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- Table: role_templates
CREATE TABLE role_templates (
	id UUID NOT NULL, 
	role_name VARCHAR(255) NOT NULL, 
	level VARCHAR(50), 
	description TEXT, 
	required_skills JSONB NOT NULL, 
	preferred_skills JSONB, 
	responsibilities VARCHAR[], 
	average_salary_range VARCHAR(100), 
	demand_score FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_role_templates_role_name ON role_templates (role_name);

-- Table: skills_master
CREATE TABLE skills_master (
	id UUID NOT NULL, 
	skill_name VARCHAR(255) NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	subcategory VARCHAR(100), 
	description TEXT, 
	difficulty_level INTEGER, 
	market_demand_score FLOAT, 
	related_skills VARCHAR[], 
	learning_resources JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_skills_master_category ON skills_master (category);
CREATE UNIQUE INDEX ix_skills_master_skill_name ON skills_master (skill_name);

-- Table: users
CREATE TABLE users (
	id UUID NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	is_active BOOLEAN, 
	is_verified BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	last_login TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

-- Table: achievements
CREATE TABLE achievements (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	achievement_type VARCHAR(100) NOT NULL, 
	achievement_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	icon VARCHAR(100), 
	achievement_data JSONB, 
	earned_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: chat_sessions
CREATE TABLE chat_sessions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	title VARCHAR(255), 
	messages JSONB NOT NULL, 
	memory JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_chat_sessions_user_id ON chat_sessions (user_id);

-- Table: resumes
CREATE TABLE resumes (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	version INTEGER, 
	is_active BOOLEAN, 
	draft_name VARCHAR(255), 
	parent_version_id UUID, 
	is_base_version BOOLEAN, 
	job_description TEXT, 
	summary TEXT, 
	skills_section JSONB, 
	coursework_section JSONB, 
	projects_section JSONB, 
	experience_section JSONB, 
	education_section JSONB, 
	certifications_section JSONB, 
	extracurricular_section JSONB, 
	technical_skills_section JSONB, 
	contact_info JSONB, 
	tailored_for VARCHAR(255), 
	match_score INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: roadmaps
CREATE TABLE roadmaps (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	target_role VARCHAR(255), 
	total_weeks INTEGER, 
	start_date DATE, 
	end_date DATE, 
	completion_percentage FLOAT, 
	status VARCHAR(50), 
	milestones JSONB, 
	generation_params JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: user_profiles
CREATE TABLE user_profiles (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	goal_role VARCHAR(255), 
	experience_level VARCHAR(50), 
	current_education VARCHAR(255), 
	graduation_year INTEGER, 
	time_per_day INTEGER, 
	preferred_learning_style VARCHAR(50), 
	onboarding_completed TIMESTAMP WITHOUT TIME ZONE, 
	profile_completion_percentage INTEGER, 
	bio TEXT, 
	linkedin_url VARCHAR(255), 
	github_url VARCHAR(255), 
	portfolio_url VARCHAR(255), 
	phone VARCHAR(50), 
	location VARCHAR(255), 
	website_url VARCHAR(255), 
	education_data JSONB, 
	experience_data JSONB, 
	projects_data JSONB, 
	certifications_data JSONB, 
	extracurricular_data JSONB, 
	technical_skills_data JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: user_skills
CREATE TABLE user_skills (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	skill_id UUID NOT NULL, 
	proficiency_level INTEGER, 
	target_proficiency INTEGER, 
	acquired_date DATE, 
	last_practiced TIMESTAMP WITHOUT TIME ZONE, 
	practice_hours FLOAT, 
	confidence_rating INTEGER, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(skill_id) REFERENCES skills_master (id)
);


-- Table: user_streaks
CREATE TABLE user_streaks (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	current_streak INTEGER, 
	longest_streak INTEGER, 
	last_activity_date TIMESTAMP WITHOUT TIME ZONE, 
	tasks_this_week INTEGER, 
	time_this_week INTEGER, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: roadmap_tasks
CREATE TABLE roadmap_tasks (
	id UUID NOT NULL, 
	roadmap_id UUID NOT NULL, 
	week_number INTEGER NOT NULL, 
	day_number INTEGER NOT NULL, 
	order_in_day INTEGER, 
	task_title VARCHAR(255) NOT NULL, 
	task_description TEXT, 
	task_type VARCHAR(50), 
	estimated_duration INTEGER, 
	difficulty INTEGER, 
	learning_objectives VARCHAR[], 
	success_criteria TEXT, 
	prerequisites VARCHAR[], 
	resources JSONB, 
	status VARCHAR(50), 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	skipped_reason VARCHAR(255), 
	notes TEXT, 
	is_favorite BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(roadmap_id) REFERENCES roadmaps (id)
);


-- Table: progress_logs
CREATE TABLE progress_logs (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	task_id UUID, 
	time_spent INTEGER, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	ended_at TIMESTAMP WITHOUT TIME ZONE, 
	difficulty_rating INTEGER, 
	confidence_rating INTEGER, 
	enjoyment_rating INTEGER, 
	notes TEXT, 
	struggles TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(task_id) REFERENCES roadmap_tasks (id)
);



-- Optional: Row-Level Security examples (uncomment once Supabase Auth is wired).
-- ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "own_resumes" ON resumes FOR ALL USING (user_id = auth.uid());
