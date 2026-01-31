-- Migration: Add new columns to resumes table for LaTeX template support
-- Date: 2026-02-01
-- Description: Adds coursework_section, extracurricular_section, and technical_skills_section columns

-- Add coursework_section column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'resumes' AND column_name = 'coursework_section'
    ) THEN
        ALTER TABLE resumes ADD COLUMN coursework_section JSONB;
    END IF;
END $$;

-- Add extracurricular_section column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'resumes' AND column_name = 'extracurricular_section'
    ) THEN
        ALTER TABLE resumes ADD COLUMN extracurricular_section JSONB;
    END IF;
END $$;

-- Add technical_skills_section column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'resumes' AND column_name = 'technical_skills_section'
    ) THEN
        ALTER TABLE resumes ADD COLUMN technical_skills_section JSONB;
    END IF;
END $$;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_resumes_coursework_section ON resumes USING gin(coursework_section);
CREATE INDEX IF NOT EXISTS idx_resumes_extracurricular_section ON resumes USING gin(extracurricular_section);
CREATE INDEX IF NOT EXISTS idx_resumes_technical_skills_section ON resumes USING gin(technical_skills_section);

-- Display confirmation
SELECT 'Migration completed successfully: Added coursework_section, extracurricular_section, and technical_skills_section columns' AS status;
