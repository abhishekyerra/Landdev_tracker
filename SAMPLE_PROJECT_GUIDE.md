# Adding the Sample 60-Lot Land Development Project

## Quick Start

### Step 1: Load the Sample Project

```bash
# Run this command from your land-dev-tracker directory
cat database/sample_project.sql | docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker
```

This creates **"Riverside Estates Development"** - a complete 60-lot, 30-acre residential subdivision with:

✅ **Complete Project Data**:
- Project name: Riverside Estates Development
- Code: RSD-001
- 60 residential lots on 30 acres
- Location: Franklin, Tennessee

✅ **10 Development Phases** (4 in progress):
1. Land Acquisition (100% complete)
2. Due Diligence & Feasibility (100% complete)
3. Planning & Design (100% complete)
4. Permitting & Approvals (65% in progress)
5. Site Preparation (not started)
6. Infrastructure Development (not started)
7-10. Future phases

✅ **40+ Detailed Tasks** including:
- Execute Purchase Agreement
- Geotechnical Survey
- Environmental Assessment
- Civil Engineering Plans
- Permit Applications
- Mass Grading
- Utility Installation
- And many more...

✅ **Complete Budget** ($5.4M+ total):
- Land Costs: $1.5M
- Professional Fees: $375K
- Site Work: $575K
- Infrastructure: $2.4M
- Permits & Fees: $490K

✅ **Expense Tracking** ($2.0M+ recorded):
- All completed work has expenses recorded
- Payment status tracking
- Invoice numbers

✅ **Milestones**:
- Property Ownership Transfer
- Environmental Clearance
- Preliminary Plat Approval
- And more...

### Step 2: Refresh the Frontend

After loading the sample project:

1. Go to http://localhost:3000
2. Click the "Refresh" button
3. You'll see "Riverside Estates Development"

### Step 3: Explore the Data

#### Via the Frontend:
- View project overview
- See status and progress

#### Via API Documentation:
1. Open http://localhost:8000/docs
2. Try these endpoints:
   - `GET /api/projects` - See all projects
   - `GET /api/projects/{project_id}/phases` - View phases
   - `GET /api/projects/{project_id}/budgets` - See budget
   - `GET /api/projects/{project_id}/expenses` - View expenses

#### Via Database (Your Strength!):
```bash
# Connect to database
docker-compose exec postgres psql -U landdev_user landdev_tracker

# View project dashboard
SELECT * FROM v_project_dashboard WHERE project_code = 'RSD-001';

# View all phases with progress
SELECT 
    phase_name,
    status,
    completion_percentage,
    planned_start_date,
    planned_end_date
FROM project_phases
WHERE project_id = (SELECT project_id FROM projects WHERE project_code = 'RSD-001')
ORDER BY phase_order;

# View budget summary
SELECT * FROM v_project_budget_summary 
WHERE project_code = 'RSD-001';

# View all tasks
SELECT 
    t.task_name,
    t.status,
    t.priority,
    t.due_date,
    t.estimated_hours,
    t.actual_hours,
    pp.phase_name
FROM tasks t
JOIN project_phases pp ON t.phase_id = pp.phase_id
WHERE t.project_id = (SELECT project_id FROM projects WHERE project_code = 'RSD-001')
ORDER BY pp.phase_order, t.due_date;

# Budget vs Actual
SELECT 
    bc.category_name,
    SUM(pb.total_budget) as budgeted,
    COALESCE(SUM(e.amount), 0) as spent,
    SUM(pb.total_budget) - COALESCE(SUM(e.amount), 0) as remaining
FROM project_budgets pb
JOIN budget_categories bc ON pb.category_id = bc.category_id
LEFT JOIN expenses e ON pb.budget_id = e.budget_id
WHERE pb.project_id = (SELECT project_id FROM projects WHERE project_code = 'RSD-001')
GROUP BY bc.category_name
ORDER BY budgeted DESC;
```

## What the Sample Project Shows You

### 1. **Realistic Timeline**
- Started: Jan 15, 2024
- Current status: In permitting phase (65% complete)
- Target completion: Dec 31, 2025

### 2. **Task Management**
- Tasks broken down by phase
- Status tracking (completed, in_progress, todo)
- Priority levels (critical, high, medium, low)
- Estimated vs actual hours
- Due dates

### 3. **Budget Management**
- Hierarchical categories
- Phase-based allocation
- Contingency percentages
- Actual expenses tracked
- Budget utilization

### 4. **Progress Tracking**
- Phase completion percentages
- Milestone status
- Overdue items identification
- Schedule vs actual dates

## Creating Your Own Projects

### Option 1: Via Database (Easiest for you!)

Use the sample project SQL as a template and modify it:

```sql
-- Copy sample_project.sql
-- Change project details
-- Adjust phases, tasks, budgets
-- Run your custom SQL
```

### Option 2: Via API

Use the Swagger UI at http://localhost:8000/docs:

1. Create project: `POST /api/projects`
2. Add phases: `POST /api/projects/{id}/phases`
3. Add tasks: (Use database for now, or I can add task endpoints)
4. Add budgets: `POST /api/projects/{id}/budgets`
5. Record expenses: `POST /api/projects/{id}/expenses`

### Option 3: Ask Claude

Tell me what project you want to add and I'll generate the SQL for you!

For example:
- "Add a 40-lot commercial development in Nashville"
- "Create a mixed-use project with 100 residential units and 20k sqft retail"
- "Add an infrastructure project for road widening"

## Useful Queries for Your Projects

### Track Progress
```sql
-- Overall project status
SELECT * FROM v_project_dashboard;

-- Phase progress
SELECT * FROM v_project_phase_progress WHERE project_code = 'YOUR-CODE';

-- Overdue items
SELECT task_name, due_date, status 
FROM tasks 
WHERE status != 'completed' AND due_date < CURRENT_DATE
ORDER BY due_date;
```

### Budget Analysis
```sql
-- Budget utilization
SELECT * FROM v_project_budget_summary WHERE project_code = 'YOUR-CODE';

-- Expenses by month
SELECT 
    DATE_TRUNC('month', expense_date) as month,
    SUM(amount) as total_spent
FROM expenses
WHERE project_id = (SELECT project_id FROM projects WHERE project_code = 'YOUR-CODE')
GROUP BY month
ORDER BY month;
```

### Task Management
```sql
-- Tasks by status
SELECT status, COUNT(*) as count
FROM tasks
WHERE project_id = (SELECT project_id FROM projects WHERE project_code = 'YOUR-CODE')
GROUP BY status;

-- Critical path items
SELECT task_name, due_date, assigned_to
FROM tasks
WHERE priority = 'critical' AND status != 'completed'
ORDER BY due_date;
```

## Need Help?

Just ask! I can:
- Generate SQL for new projects
- Create custom reports
- Add more phases/tasks/budgets
- Build additional features

Enjoy exploring your sample project! 🏗️
