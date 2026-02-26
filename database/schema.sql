-- Land Development Project Tracking System
-- PostgreSQL Database Schema
-- Optimized for phase/milestone tracking and budget management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CORE TABLES
-- ============================================

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'project_manager', 'developer', 'contractor', 'viewer')),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255) NOT NULL,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    location_address TEXT,
    location_city VARCHAR(100),
    location_state VARCHAR(50),
    location_zip VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    total_acres DECIMAL(10, 2),
    zoning_classification VARCHAR(100),
    project_type VARCHAR(100) CHECK (project_type IN ('residential', 'commercial', 'mixed_use', 'industrial', 'infrastructure')),
    status VARCHAR(50) DEFAULT 'planning' CHECK (status IN ('planning', 'permitting', 'in_progress', 'on_hold', 'completed', 'cancelled')),
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PHASE & MILESTONE TRACKING
-- ============================================

-- Development Phases (master template)
CREATE TABLE phase_templates (
    phase_template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase_name VARCHAR(255) NOT NULL,
    phase_order INTEGER NOT NULL,
    description TEXT,
    typical_duration_days INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Phases (actual phases for each project)
CREATE TABLE project_phases (
    phase_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    phase_template_id UUID REFERENCES phase_templates(phase_template_id),
    phase_name VARCHAR(255) NOT NULL,
    phase_order INTEGER NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'on_hold', 'cancelled')),
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, phase_order)
);

-- Milestones within phases
CREATE TABLE milestones (
    milestone_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase_id UUID REFERENCES project_phases(phase_id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    milestone_name VARCHAR(255) NOT NULL,
    description TEXT,
    milestone_type VARCHAR(100) CHECK (milestone_type IN ('permit', 'inspection', 'payment', 'delivery', 'approval', 'other')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'waived')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    due_date DATE,
    completed_date DATE,
    assigned_to UUID REFERENCES users(user_id),
    dependencies TEXT, -- JSON array of milestone_ids
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- BUDGET MANAGEMENT
-- ============================================

-- Budget Categories
CREATE TABLE budget_categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name VARCHAR(255) NOT NULL,
    parent_category_id UUID REFERENCES budget_categories(category_id),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Budget (overall budget allocation)
CREATE TABLE project_budgets (
    budget_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    category_id UUID REFERENCES budget_categories(category_id),
    phase_id UUID REFERENCES project_phases(phase_id) ON DELETE CASCADE,
    budget_name VARCHAR(255) NOT NULL,
    budgeted_amount DECIMAL(15, 2) NOT NULL,
    contingency_percentage DECIMAL(5, 2) DEFAULT 10.00,
    contingency_amount DECIMAL(15, 2) GENERATED ALWAYS AS (budgeted_amount * contingency_percentage / 100) STORED,
    total_budget DECIMAL(15, 2) GENERATED ALWAYS AS (budgeted_amount + (budgeted_amount * contingency_percentage / 100)) STORED,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Budget Line Items (detailed budget breakdown)
CREATE TABLE budget_line_items (
    line_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id UUID REFERENCES project_budgets(budget_id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    quantity DECIMAL(10, 2),
    unit_of_measure VARCHAR(50),
    unit_cost DECIMAL(15, 2),
    estimated_amount DECIMAL(15, 2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Actual Expenses (tracking real costs)
CREATE TABLE expenses (
    expense_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    budget_id UUID REFERENCES project_budgets(budget_id),
    line_item_id UUID REFERENCES budget_line_items(line_item_id),
    phase_id UUID REFERENCES project_phases(phase_id),
    vendor_id UUID REFERENCES vendors(vendor_id),
    expense_date DATE NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    payment_method VARCHAR(50) CHECK (payment_method IN ('check', 'wire', 'credit_card', 'ach', 'cash')),
    invoice_number VARCHAR(100),
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'approved', 'paid', 'rejected')),
    payment_date DATE,
    approved_by UUID REFERENCES users(user_id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TASKS & ACTIVITIES
-- ============================================

-- Tasks (detailed work items)
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(phase_id),
    milestone_id UUID REFERENCES milestones(milestone_id),
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'review', 'completed', 'blocked', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assigned_to UUID REFERENCES users(user_id),
    due_date DATE,
    completed_date DATE,
    estimated_hours DECIMAL(6, 2),
    actual_hours DECIMAL(6, 2),
    dependencies TEXT, -- JSON array of task_ids
    notes TEXT,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- STAKEHOLDERS & VENDORS
-- ============================================

-- Vendors/Contractors
CREATE TABLE vendors (
    vendor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(100) CHECK (vendor_type IN ('contractor', 'consultant', 'supplier', 'engineer', 'architect', 'legal', 'other')),
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    tax_id VARCHAR(50),
    license_number VARCHAR(100),
    insurance_expiry DATE,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Team Members (linking users to projects)
CREATE TABLE project_team (
    team_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id),
    role VARCHAR(100) NOT NULL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);

-- ============================================
-- DOCUMENTS & FILES
-- ============================================

-- Documents/Files
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(phase_id),
    milestone_id UUID REFERENCES milestones(milestone_id),
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) CHECK (document_type IN ('permit', 'plan', 'contract', 'report', 'survey', 'photo', 'other')),
    file_path VARCHAR(500) NOT NULL, -- GCS bucket path
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    version INTEGER DEFAULT 1,
    uploaded_by UUID REFERENCES users(user_id),
    description TEXT,
    tags TEXT[], -- PostgreSQL array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PERMITS & APPROVALS
-- ============================================

-- Permits
CREATE TABLE permits (
    permit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(phase_id),
    permit_type VARCHAR(100) NOT NULL,
    permit_number VARCHAR(100),
    issuing_authority VARCHAR(255),
    application_date DATE,
    approval_date DATE,
    expiration_date DATE,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'under_review', 'approved', 'denied', 'expired')),
    cost DECIMAL(15, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CHANGE ORDERS & REVISIONS
-- ============================================

-- Change Orders
CREATE TABLE change_orders (
    change_order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    change_order_number VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    reason TEXT,
    impact_cost DECIMAL(15, 2) DEFAULT 0,
    impact_schedule_days INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'implemented')),
    requested_by UUID REFERENCES users(user_id),
    approved_by UUID REFERENCES users(user_id),
    requested_date DATE,
    approved_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ACTIVITY LOG
-- ============================================

-- Activity Log (audit trail)
CREATE TABLE activity_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id),
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'project', 'phase', 'milestone', 'budget', etc.
    entity_id UUID NOT NULL,
    old_value JSONB,
    new_value JSONB,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Projects
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_type ON projects(project_type);

-- Project Phases
CREATE INDEX idx_phases_project ON project_phases(project_id);
CREATE INDEX idx_phases_status ON project_phases(status);
CREATE INDEX idx_phases_dates ON project_phases(planned_start_date, planned_end_date);

-- Milestones
CREATE INDEX idx_milestones_phase ON milestones(phase_id);
CREATE INDEX idx_milestones_project ON milestones(project_id);
CREATE INDEX idx_milestones_status ON milestones(status);
CREATE INDEX idx_milestones_due_date ON milestones(due_date);
CREATE INDEX idx_milestones_assigned ON milestones(assigned_to);

-- Budget
CREATE INDEX idx_budget_project ON project_budgets(project_id);
CREATE INDEX idx_budget_phase ON project_budgets(phase_id);
CREATE INDEX idx_budget_category ON project_budgets(category_id);

-- Expenses
CREATE INDEX idx_expenses_project ON expenses(project_id);
CREATE INDEX idx_expenses_budget ON expenses(budget_id);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_status ON expenses(payment_status);

-- Tasks
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_phase ON tasks(phase_id);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Documents
CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_phase ON documents(phase_id);
CREATE INDEX idx_documents_type ON documents(document_type);

-- Activity Log
CREATE INDEX idx_activity_project ON activity_log(project_id);
CREATE INDEX idx_activity_user ON activity_log(user_id);
CREATE INDEX idx_activity_created ON activity_log(created_at);
CREATE INDEX idx_activity_entity ON activity_log(entity_type, entity_id);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Budget Summary by Project
CREATE VIEW v_project_budget_summary AS
SELECT 
    p.project_id,
    p.project_name,
    COALESCE(SUM(pb.total_budget), 0) as total_budgeted,
    COALESCE(SUM(e.amount), 0) as total_spent,
    COALESCE(SUM(pb.total_budget), 0) - COALESCE(SUM(e.amount), 0) as remaining_budget,
    CASE 
        WHEN COALESCE(SUM(pb.total_budget), 0) > 0 
        THEN ROUND((COALESCE(SUM(e.amount), 0) / SUM(pb.total_budget) * 100)::numeric, 2)
        ELSE 0 
    END as budget_utilization_percentage
FROM projects p
LEFT JOIN project_budgets pb ON p.project_id = pb.project_id
LEFT JOIN expenses e ON p.project_id = e.project_id AND e.payment_status IN ('approved', 'paid')
GROUP BY p.project_id, p.project_name;

-- Phase Progress by Project
CREATE VIEW v_project_phase_progress AS
SELECT 
    p.project_id,
    p.project_name,
    pp.phase_id,
    pp.phase_name,
    pp.status,
    pp.completion_percentage,
    COUNT(DISTINCT m.milestone_id) as total_milestones,
    COUNT(DISTINCT CASE WHEN m.status = 'completed' THEN m.milestone_id END) as completed_milestones,
    CASE 
        WHEN COUNT(DISTINCT m.milestone_id) > 0 
        THEN ROUND((COUNT(DISTINCT CASE WHEN m.status = 'completed' THEN m.milestone_id END)::numeric / COUNT(DISTINCT m.milestone_id) * 100), 2)
        ELSE 0 
    END as milestone_completion_percentage
FROM projects p
INNER JOIN project_phases pp ON p.project_id = pp.project_id
LEFT JOIN milestones m ON pp.phase_id = m.phase_id
GROUP BY p.project_id, p.project_name, pp.phase_id, pp.phase_name, pp.status, pp.completion_percentage;

-- Overall Project Health Dashboard
CREATE VIEW v_project_dashboard AS
SELECT 
    p.project_id,
    p.project_name,
    p.project_code,
    p.status,
    p.start_date,
    p.target_completion_date,
    CASE 
        WHEN p.target_completion_date < CURRENT_DATE AND p.status != 'completed' THEN 'overdue'
        WHEN p.target_completion_date <= CURRENT_DATE + INTERVAL '30 days' AND p.status != 'completed' THEN 'at_risk'
        ELSE 'on_track'
    END as schedule_status,
    bs.total_budgeted,
    bs.total_spent,
    bs.remaining_budget,
    bs.budget_utilization_percentage,
    ROUND(AVG(pp.completion_percentage), 2) as overall_completion_percentage,
    COUNT(DISTINCT pp.phase_id) as total_phases,
    COUNT(DISTINCT CASE WHEN pp.status = 'completed' THEN pp.phase_id END) as completed_phases,
    COUNT(DISTINCT m.milestone_id) FILTER (WHERE m.status = 'pending' AND m.due_date < CURRENT_DATE) as overdue_milestones
FROM projects p
LEFT JOIN v_project_budget_summary bs ON p.project_id = bs.project_id
LEFT JOIN project_phases pp ON p.project_id = pp.project_id
LEFT JOIN milestones m ON p.project_id = m.project_id
GROUP BY p.project_id, p.project_name, p.project_code, p.status, p.start_date, 
         p.target_completion_date, bs.total_budgeted, bs.total_spent, 
         bs.remaining_budget, bs.budget_utilization_percentage;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at timestamps
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_phases_updated_at BEFORE UPDATE ON project_phases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_budgets_updated_at BEFORE UPDATE ON project_budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expenses_updated_at BEFORE UPDATE ON expenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE projects IS 'Main project table containing all land development projects';
COMMENT ON TABLE project_phases IS 'Development phases for each project with timeline tracking';
COMMENT ON TABLE milestones IS 'Key milestones within each phase';
COMMENT ON TABLE project_budgets IS 'Budget allocation by category and phase';
COMMENT ON TABLE expenses IS 'Actual expenses tracked against budget';
COMMENT ON VIEW v_project_dashboard IS 'Comprehensive project health dashboard view';
