# Database Schema Documentation

## Overview
This document provides detailed information about the Land Development Tracker database schema, designed specifically for tracking land development projects with emphasis on phase/milestone tracking and budget management.

## Database Design Principles

1. **UUID Primary Keys**: All tables use UUID primary keys for distributed scalability
2. **Soft Deletes**: Some tables support soft deletes via `is_active` flags
3. **Audit Trail**: Timestamps (`created_at`, `updated_at`) on all major tables
4. **Referential Integrity**: Comprehensive foreign key relationships
5. **Performance**: Strategic indexes on frequently queried columns
6. **Data Validation**: Check constraints for enum-like columns

## Entity Relationship Overview

```
projects (1) ────< (many) project_phases (1) ────< (many) milestones
    │                        │
    │                        │
    ├────< project_budgets <─┤
    │            │
    │            │
    └────< expenses ─────────┘
```

## Core Tables

### users
Stores user authentication and profile information.

**Key Columns:**
- `user_id` (UUID, PK): Unique user identifier
- `email` (VARCHAR, UNIQUE): User email address
- `password_hash` (VARCHAR): Bcrypt hashed password
- `role` (VARCHAR): User role (admin, project_manager, developer, contractor, viewer)
- `is_active` (BOOLEAN): Account status

**Indexes:**
- Primary key on `user_id`
- Unique index on `email`

**Usage Example:**
```sql
-- Create a new user
INSERT INTO users (email, password_hash, first_name, last_name, role)
VALUES ('user@example.com', '$2b$12$...', 'John', 'Doe', 'project_manager');
```

---

### projects
Main table for land development projects.

**Key Columns:**
- `project_id` (UUID, PK): Unique project identifier
- `project_name` (VARCHAR): Project name
- `project_code` (VARCHAR, UNIQUE): Short project code
- `project_type` (VARCHAR): Type (residential, commercial, mixed_use, industrial, infrastructure)
- `status` (VARCHAR): Current status (planning, permitting, in_progress, on_hold, completed, cancelled)
- `total_acres` (DECIMAL): Total land area
- `start_date`, `target_completion_date`, `actual_completion_date` (DATE): Timeline tracking

**Relationships:**
- One-to-Many with `project_phases`
- One-to-Many with `project_budgets`
- One-to-Many with `expenses`
- Many-to-One with `users` (created_by)

**Indexes:**
- Primary key on `project_id`
- Index on `status`
- Index on `created_by`
- Index on `project_type`

**Usage Example:**
```sql
-- Create a new project
INSERT INTO projects (project_name, project_code, project_type, total_acres, status)
VALUES ('Riverside Development', 'RSD-001', 'residential', 45.5, 'planning');

-- Get all active projects
SELECT * FROM projects WHERE status IN ('planning', 'permitting', 'in_progress');
```

---

### phase_templates
Master templates for development phases.

**Key Columns:**
- `phase_template_id` (UUID, PK): Template identifier
- `phase_name` (VARCHAR): Phase name
- `phase_order` (INTEGER): Order sequence
- `typical_duration_days` (INTEGER): Estimated duration

**Standard Phases:**
1. Land Acquisition (90 days)
2. Due Diligence & Feasibility (60 days)
3. Planning & Design (120 days)
4. Permitting & Approvals (180 days)
5. Site Preparation (45 days)
6. Infrastructure Development (90 days)
7. Vertical Construction (240 days)
8. Finishing & Landscaping (60 days)
9. Inspections & Final Approvals (30 days)
10. Project Closeout (30 days)

---

### project_phases
Actual development phases for each project.

**Key Columns:**
- `phase_id` (UUID, PK): Phase identifier
- `project_id` (UUID, FK): Reference to project
- `phase_name` (VARCHAR): Phase name
- `phase_order` (INTEGER): Sequence order
- `status` (VARCHAR): Current status (not_started, in_progress, completed, on_hold, cancelled)
- `completion_percentage` (INTEGER): Progress (0-100)
- `planned_start_date`, `planned_end_date` (DATE): Planned timeline
- `actual_start_date`, `actual_end_date` (DATE): Actual timeline

**Relationships:**
- Many-to-One with `projects`
- One-to-Many with `milestones`
- One-to-Many with `project_budgets`

**Indexes:**
- Primary key on `phase_id`
- Index on `project_id`
- Index on `status`
- Composite index on `(planned_start_date, planned_end_date)`

**Usage Example:**
```sql
-- Add phases to a project
INSERT INTO project_phases (project_id, phase_name, phase_order, planned_start_date, planned_end_date)
SELECT 
    'project-uuid',
    phase_name,
    phase_order,
    CURRENT_DATE + (phase_order * 30),
    CURRENT_DATE + ((phase_order + 1) * 30)
FROM phase_templates
WHERE is_active = true
ORDER BY phase_order;

-- Update phase completion
UPDATE project_phases 
SET completion_percentage = 75, 
    status = 'in_progress'
WHERE phase_id = 'phase-uuid';
```

---

### milestones
Critical milestones within project phases.

**Key Columns:**
- `milestone_id` (UUID, PK): Milestone identifier
- `phase_id` (UUID, FK): Reference to phase
- `project_id` (UUID, FK): Reference to project
- `milestone_name` (VARCHAR): Milestone name
- `milestone_type` (VARCHAR): Type (permit, inspection, payment, delivery, approval, other)
- `status` (VARCHAR): Status (pending, in_progress, completed, failed, waived)
- `priority` (VARCHAR): Priority level (low, medium, high, critical)
- `due_date`, `completed_date` (DATE): Timeline
- `assigned_to` (UUID, FK): Assigned user
- `dependencies` (TEXT): JSON array of dependent milestone IDs

**Indexes:**
- Primary key on `milestone_id`
- Index on `phase_id`
- Index on `project_id`
- Index on `status`
- Index on `due_date`
- Index on `assigned_to`

**Usage Example:**
```sql
-- Create a milestone
INSERT INTO milestones (phase_id, project_id, milestone_name, milestone_type, due_date, priority)
VALUES ('phase-uuid', 'project-uuid', 'Obtain Building Permit', 'permit', '2024-06-30', 'critical');

-- Find overdue milestones
SELECT m.*, p.project_name, ph.phase_name
FROM milestones m
JOIN projects p ON m.project_id = p.project_id
JOIN project_phases ph ON m.phase_id = ph.phase_id
WHERE m.status != 'completed' 
  AND m.due_date < CURRENT_DATE
ORDER BY m.priority DESC, m.due_date;
```

---

## Budget Management Tables

### budget_categories
Hierarchical budget categories.

**Key Columns:**
- `category_id` (UUID, PK): Category identifier
- `category_name` (VARCHAR): Category name
- `parent_category_id` (UUID, FK): Parent category (for hierarchy)
- `is_active` (BOOLEAN): Active status

**Hierarchy:**
- Level 1: Main categories (Land Costs, Professional Fees, Site Work, etc.)
- Level 2: Sub-categories (Architecture, Civil Engineering, Grading, etc.)

**Usage Example:**
```sql
-- Get all top-level categories
SELECT * FROM budget_categories 
WHERE parent_category_id IS NULL 
  AND is_active = true;

-- Get category hierarchy
WITH RECURSIVE category_tree AS (
    SELECT category_id, category_name, parent_category_id, 0 as level
    FROM budget_categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, c.category_name, c.parent_category_id, ct.level + 1
    FROM budget_categories c
    JOIN category_tree ct ON c.parent_category_id = ct.category_id
)
SELECT * FROM category_tree ORDER BY level, category_name;
```

---

### project_budgets
Budget allocations for projects.

**Key Columns:**
- `budget_id` (UUID, PK): Budget identifier
- `project_id` (UUID, FK): Reference to project
- `category_id` (UUID, FK): Budget category
- `phase_id` (UUID, FK): Associated phase
- `budget_name` (VARCHAR): Budget line name
- `budgeted_amount` (DECIMAL): Allocated amount
- `contingency_percentage` (DECIMAL): Contingency percentage (default 10%)
- `contingency_amount` (DECIMAL, GENERATED): Calculated contingency
- `total_budget` (DECIMAL, GENERATED): Total with contingency

**Generated Columns:**
```sql
contingency_amount = budgeted_amount * contingency_percentage / 100
total_budget = budgeted_amount + contingency_amount
```

**Indexes:**
- Primary key on `budget_id`
- Index on `project_id`
- Index on `phase_id`
- Index on `category_id`

**Usage Example:**
```sql
-- Create budget allocation
INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount)
VALUES ('project-uuid', 'category-uuid', 'phase-uuid', 'Site Grading', 150000.00);

-- Get total project budget
SELECT 
    project_id,
    SUM(total_budget) as total_project_budget
FROM project_budgets
WHERE project_id = 'project-uuid'
GROUP BY project_id;
```

---

### expenses
Actual expense tracking.

**Key Columns:**
- `expense_id` (UUID, PK): Expense identifier
- `project_id` (UUID, FK): Reference to project
- `budget_id` (UUID, FK): Associated budget
- `vendor_id` (UUID, FK): Vendor/contractor
- `expense_date` (DATE): Date of expense
- `amount` (DECIMAL): Expense amount
- `payment_status` (VARCHAR): Status (pending, approved, paid, rejected)
- `invoice_number` (VARCHAR): Invoice reference

**Indexes:**
- Primary key on `expense_id`
- Index on `project_id`
- Index on `budget_id`
- Index on `expense_date`
- Index on `payment_status`

**Usage Example:**
```sql
-- Record an expense
INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_status)
VALUES ('project-uuid', 'budget-uuid', CURRENT_DATE, 'Grading work - Invoice #1234', 25000.00, 'pending');

-- Get expenses by month
SELECT 
    DATE_TRUNC('month', expense_date) as month,
    COUNT(*) as expense_count,
    SUM(amount) as total_amount
FROM expenses
WHERE project_id = 'project-uuid'
GROUP BY DATE_TRUNC('month', expense_date)
ORDER BY month DESC;
```

---

## Analytical Views

### v_project_budget_summary
Comprehensive budget summary by project.

**Columns:**
- `project_id`, `project_name`
- `total_budgeted`: Sum of all budgets
- `total_spent`: Sum of approved/paid expenses
- `remaining_budget`: Budget - Spent
- `budget_utilization_percentage`: (Spent / Budget) * 100

**Usage:**
```sql
-- Get budget status for all projects
SELECT * FROM v_project_budget_summary
ORDER BY budget_utilization_percentage DESC;

-- Projects over budget
SELECT * FROM v_project_budget_summary
WHERE budget_utilization_percentage > 100;
```

---

### v_project_phase_progress
Phase completion tracking.

**Columns:**
- `project_id`, `project_name`
- `phase_id`, `phase_name`, `status`
- `completion_percentage`
- `total_milestones`, `completed_milestones`
- `milestone_completion_percentage`

**Usage:**
```sql
-- Get phase progress for a project
SELECT * FROM v_project_phase_progress
WHERE project_id = 'project-uuid'
ORDER BY phase_order;
```

---

### v_project_dashboard
Overall project health metrics.

**Columns:**
- Project details
- Budget metrics
- Schedule status (on_track, at_risk, overdue)
- Completion percentages
- Overdue milestone count

**Usage:**
```sql
-- Get dashboard for all projects
SELECT * FROM v_project_dashboard
ORDER BY project_name;

-- Projects at risk
SELECT * FROM v_project_dashboard
WHERE schedule_status IN ('at_risk', 'overdue')
   OR budget_utilization_percentage > 90;
```

---

## Performance Optimization

### Recommended Indexes (Already Created)

1. **Foreign Keys**: All foreign keys are indexed
2. **Status Fields**: Indexes on frequently filtered status columns
3. **Date Ranges**: Composite indexes on date columns
4. **User Lookups**: Indexes on assigned_to columns

### Query Optimization Tips

```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE
SELECT * FROM v_project_dashboard WHERE status = 'in_progress';

-- Create additional indexes if needed
CREATE INDEX idx_custom ON table_name (column1, column2);

-- Vacuum and analyze regularly
VACUUM ANALYZE;
```

---

## Backup and Maintenance

### Backup Strategy

```sql
-- Full database backup
pg_dump landdev_tracker > backup_$(date +%Y%m%d).sql

-- Backup specific tables
pg_dump -t projects -t project_phases landdev_tracker > critical_tables.sql
```

### Regular Maintenance

```sql
-- Update statistics
ANALYZE;

-- Rebuild indexes
REINDEX DATABASE landdev_tracker;

-- Check for bloat
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Common Queries

### Project Status Report
```sql
SELECT 
    p.project_name,
    p.status,
    COUNT(DISTINCT ph.phase_id) as total_phases,
    COUNT(DISTINCT CASE WHEN ph.status = 'completed' THEN ph.phase_id END) as completed_phases,
    ROUND(AVG(ph.completion_percentage), 2) as avg_completion,
    bs.total_budgeted,
    bs.total_spent,
    bs.budget_utilization_percentage
FROM projects p
LEFT JOIN project_phases ph ON p.project_id = ph.project_id
LEFT JOIN v_project_budget_summary bs ON p.project_id = bs.project_id
GROUP BY p.project_id, p.project_name, p.status, bs.total_budgeted, bs.total_spent, bs.budget_utilization_percentage
ORDER BY p.project_name;
```

### Budget Variance by Category
```sql
SELECT 
    bc.category_name,
    SUM(pb.total_budget) as budgeted,
    COALESCE(SUM(e.amount), 0) as spent,
    SUM(pb.total_budget) - COALESCE(SUM(e.amount), 0) as variance
FROM budget_categories bc
LEFT JOIN project_budgets pb ON bc.category_id = pb.category_id
LEFT JOIN expenses e ON pb.budget_id = e.budget_id AND e.payment_status IN ('approved', 'paid')
WHERE pb.project_id = 'project-uuid'
GROUP BY bc.category_id, bc.category_name
ORDER BY variance;
```

### Critical Path Analysis
```sql
SELECT 
    p.project_name,
    ph.phase_name,
    m.milestone_name,
    m.due_date,
    m.priority,
    CASE 
        WHEN m.due_date < CURRENT_DATE AND m.status != 'completed' THEN 'OVERDUE'
        WHEN m.due_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'DUE SOON'
        ELSE 'ON TRACK'
    END as urgency
FROM milestones m
JOIN project_phases ph ON m.phase_id = ph.phase_id
JOIN projects p ON m.project_id = p.project_id
WHERE m.status != 'completed'
  AND m.priority IN ('high', 'critical')
ORDER BY m.due_date, m.priority DESC;
```

---

## Data Dictionary

For a complete list of all columns, data types, and constraints, refer to the `schema.sql` file.

## Support

For database-related questions or optimization needs, consult with your database administrator or refer to the PostgreSQL documentation at https://www.postgresql.org/docs/
