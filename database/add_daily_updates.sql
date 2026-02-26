-- Daily Updates Feature
-- Add this table to track contractor daily updates

CREATE TABLE IF NOT EXISTS daily_updates (
    update_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id),
    update_date DATE NOT NULL DEFAULT CURRENT_DATE,
    notes TEXT NOT NULL,
    blockers TEXT,
    weather_impact TEXT,
    crew_size INTEGER,
    equipment_available TEXT,
    ai_analysis TEXT,
    ai_recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_daily_updates_project ON daily_updates(project_id);
CREATE INDEX idx_daily_updates_date ON daily_updates(update_date);
CREATE INDEX idx_daily_updates_user ON daily_updates(user_id);

-- Update timestamp trigger
CREATE TRIGGER update_daily_updates_updated_at
    BEFORE UPDATE ON daily_updates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample query to view recent updates
-- SELECT du.update_date, u.first_name, u.last_name, du.notes, du.ai_analysis
-- FROM daily_updates du
-- JOIN users u ON du.user_id = u.user_id
-- WHERE du.project_id = 'YOUR_PROJECT_ID'
-- ORDER BY du.update_date DESC
-- LIMIT 10;
