-- Sample Land Development Project: Riverside Estates
-- 60 lots on 30 acres with complete phases, milestones, budgets, and tasks

-- Insert the main project
INSERT INTO projects (
    project_name, 
    project_code, 
    description, 
    location_address,
    location_city,
    location_state,
    location_zip,
    total_acres,
    zoning_classification,
    project_type,
    status,
    start_date,
    target_completion_date,
    created_by
) VALUES (
    'Riverside Estates Development',
    'RSD-001',
    '60-lot residential subdivision on 30 acres with community amenities including park, walking trails, and detention pond',
    '1234 County Road 500',
    'Franklin',
    'Tennessee',
    '37064',
    30.00,
    'R-20 Residential',
    'residential',
    'in_progress',
    '2024-01-15',
    '2025-12-31',
    (SELECT user_id FROM users WHERE email = 'admin@landdev.com')
) RETURNING project_id \gset

-- Store project_id for later use
\set proj_id :project_id

-- Create all phases for the project
INSERT INTO project_phases (
    project_id,
    phase_template_id,
    phase_name,
    phase_order,
    description,
    status,
    planned_start_date,
    planned_end_date,
    actual_start_date,
    completion_percentage
)
SELECT 
    :'proj_id'::uuid,
    phase_template_id,
    phase_name,
    phase_order,
    description,
    CASE 
        WHEN phase_order = 1 THEN 'completed'
        WHEN phase_order = 2 THEN 'completed'
        WHEN phase_order = 3 THEN 'completed'
        WHEN phase_order = 4 THEN 'in_progress'
        ELSE 'not_started'
    END,
    '2024-01-15'::date + (phase_order - 1) * 60,
    '2024-01-15'::date + phase_order * 60,
    CASE 
        WHEN phase_order <= 3 THEN '2024-01-15'::date + (phase_order - 1) * 60
        WHEN phase_order = 4 THEN '2024-06-01'::date
        ELSE NULL
    END,
    CASE 
        WHEN phase_order = 1 THEN 100
        WHEN phase_order = 2 THEN 100
        WHEN phase_order = 3 THEN 100
        WHEN phase_order = 4 THEN 65
        ELSE 0
    END
FROM phase_templates
WHERE is_active = true
ORDER BY phase_order;

-- Get phase IDs for adding milestones
\set phase1_id (SELECT phase_id FROM project_phases WHERE project_id = :'proj_id'::uuid AND phase_order = 1)
\set phase2_id (SELECT phase_id FROM project_phases WHERE project_id = :'proj_id'::uuid AND phase_order = 2)
\set phase3_id (SELECT phase_id FROM project_phases WHERE project_id = :'proj_id'::uuid AND phase_order = 3)
\set phase4_id (SELECT phase_id FROM project_phases WHERE project_id = :'proj_id'::uuid AND phase_order = 4)
\set phase5_id (SELECT phase_id FROM project_phases WHERE project_id = :'proj_id'::uuid AND phase_order = 5)
\set phase6_id (SELECT phase_id FROM project_phases WHERE project_id = :'proj_id'::uuid AND phase_order = 6)

-- Add detailed tasks for each phase

-- PHASE 1: Land Acquisition (Completed)
INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
(:'proj_id'::uuid, :'phase1_id'::uuid, 'Execute Purchase Agreement', 'Finalize and sign land purchase contract', 'completed', 'critical', '2024-01-20', '2024-01-18', 40, 38),
(:'proj_id'::uuid, :'phase1_id'::uuid, 'Title Search & Insurance', 'Complete title search and obtain title insurance policy', 'completed', 'critical', '2024-01-25', '2024-01-24', 20, 22),
(:'proj_id'::uuid, :'phase1_id'::uuid, 'Survey Property Boundaries', 'Professional boundary survey of 30-acre parcel', 'completed', 'high', '2024-02-01', '2024-01-31', 60, 65),
(:'proj_id'::uuid, :'phase1_id'::uuid, 'Close on Property', 'Complete closing and transfer ownership', 'completed', 'critical', '2024-02-15', '2024-02-15', 16, 16);

-- PHASE 2: Due Diligence & Feasibility (Completed)
INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Geotechnical Survey', 'Soil testing and geotechnical analysis for 30 acres', 'completed', 'critical', '2024-02-28', '2024-02-27', 80, 85),
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Environmental Phase I Assessment', 'Environmental site assessment and reports', 'completed', 'critical', '2024-03-05', '2024-03-04', 60, 62),
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Wetlands Delineation', 'Identify and map any wetland areas', 'completed', 'high', '2024-03-10', '2024-03-08', 40, 38),
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Market Study & Feasibility', 'Analyze market demand for 60-lot subdivision', 'completed', 'high', '2024-03-15', '2024-03-14', 100, 105),
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Financial Pro Forma', 'Create detailed financial projections and ROI analysis', 'completed', 'high', '2024-03-20', '2024-03-19', 80, 82);

-- PHASE 3: Planning & Design (Completed)
INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
(:'proj_id'::uuid, :'phase3_id'::uuid, 'Preliminary Plat Design', 'Design lot layout for 60 lots with streets and utilities', 'completed', 'critical', '2024-04-15', '2024-04-12', 200, 215),
(:'proj_id'::uuid, :'phase3_id'::uuid, 'Civil Engineering Plans', 'Complete grading, drainage, and utility plans', 'completed', 'critical', '2024-05-01', '2024-04-28', 300, 320),
(:'proj_id'::uuid, :'phase3_id'::uuid, 'Traffic Impact Study', 'Analyze traffic impact and required road improvements', 'completed', 'high', '2024-04-20', '2024-04-18', 60, 58),
(:'proj_id'::uuid, :'phase3_id'::uuid, 'Stormwater Management Design', 'Design detention pond and drainage system', 'completed', 'critical', '2024-05-10', '2024-05-08', 120, 125),
(:'proj_id'::uuid, :'phase3_id'::uuid, 'Landscape & Amenities Plan', 'Design community park, trails, and entrance', 'completed', 'medium', '2024-05-15', '2024-05-14', 80, 78);

-- PHASE 4: Permitting & Approvals (In Progress - 65% complete)
INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Submit Preliminary Plat', 'Submit preliminary plat to planning commission', 'completed', 'critical', '2024-06-01', '2024-05-30', 40, 42),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Planning Commission Review', 'Present to planning commission and address comments', 'completed', 'critical', '2024-06-20', '2024-06-18', 60, 65),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Preliminary Plat Approval', 'Obtain preliminary plat approval', 'completed', 'critical', '2024-07-01', '2024-06-28', 20, 18),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Final Plat Preparation', 'Prepare final plat with all required signatures', 'completed', 'critical', '2024-07-15', '2024-07-12', 80, 85),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Grading Permit Application', 'Apply for mass grading permit', 'completed', 'critical', '2024-07-20', '2024-07-18', 40, 38),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Utility Permits (Water/Sewer)', 'Obtain water and sewer connection permits', 'in_progress', 'critical', '2024-08-15', NULL, 60, 45),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Stormwater Permit (NPDES)', 'Obtain stormwater management permit', 'in_progress', 'critical', '2024-08-20', NULL, 80, 52),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Road & Infrastructure Permit', 'Obtain permits for road construction', 'todo', 'critical', '2024-09-01', NULL, 40, 0),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Environmental Permits', 'Army Corps wetlands permit if required', 'todo', 'high', '2024-09-10', NULL, 60, 0);

-- PHASE 5: Site Preparation (Not Started)
INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
(:'proj_id'::uuid, :'phase5_id'::uuid, 'Clear & Grub 30 Acres', 'Remove trees, vegetation, and debris from site', 'todo', 'critical', '2024-10-15', 200),
(:'proj_id'::uuid, :'phase5_id'::uuid, 'Mass Grading', 'Grade entire site to design elevations', 'todo', 'critical', '2024-11-01', 300),
(:'proj_id'::uuid, :'phase5_id'::uuid, 'Install Erosion Control', 'Install silt fences and erosion control measures', 'todo', 'critical', '2024-10-20', 80),
(:'proj_id'::uuid, :'phase5_id'::uuid, 'Excavate Detention Pond', 'Excavate stormwater detention pond', 'todo', 'high', '2024-11-10', 120);

-- PHASE 6: Infrastructure Development (Not Started)
INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Install Water Lines', 'Install 8" water mains throughout subdivision', 'todo', 'critical', '2025-01-15', 400),
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Install Sewer Lines', 'Install sanitary sewer collection system', 'todo', 'critical', '2025-02-01', 450),
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Install Storm Drains', 'Install storm sewer and drainage system', 'todo', 'critical', '2025-02-15', 350),
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Road Base Construction', 'Construct road base for all subdivision streets', 'todo', 'critical', '2025-03-15', 500),
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Install Gas Lines', 'Install natural gas service', 'todo', 'high', '2025-03-01', 200),
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Install Electric & Telecom', 'Install underground electric and fiber', 'todo', 'high', '2025-03-20', 300);

-- Add Milestones
INSERT INTO milestones (project_id, phase_id, milestone_name, description, milestone_type, status, priority, due_date, completed_date) VALUES
-- Phase 1 Milestones
(:'proj_id'::uuid, :'phase1_id'::uuid, 'Property Ownership Transfer', 'Legal transfer of property title', 'approval', 'completed', 'critical', '2024-02-15', '2024-02-15'),

-- Phase 2 Milestones
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Environmental Clearance', 'Phase I environmental assessment approved', 'approval', 'completed', 'critical', '2024-03-05', '2024-03-04'),
(:'proj_id'::uuid, :'phase2_id'::uuid, 'Geotechnical Report Approved', 'Soil analysis completed and approved', 'approval', 'completed', 'critical', '2024-02-28', '2024-02-27'),

-- Phase 3 Milestones
(:'proj_id'::uuid, :'phase3_id'::uuid, 'Preliminary Plans Complete', 'All preliminary engineering plans finished', 'delivery', 'completed', 'critical', '2024-05-15', '2024-05-14'),

-- Phase 4 Milestones (Some pending)
(:'proj_id'::uuid, :'phase4_id'::uuid, 'Preliminary Plat Approved', 'Planning commission preliminary approval', 'approval', 'completed', 'critical', '2024-07-01', '2024-06-28'),
(:'proj_id'::uuid, :'phase4_id'::uuid, 'All Permits Obtained', 'All required permits secured', 'permit', 'in_progress', 'critical', '2024-09-15', NULL),

-- Phase 5 Milestones
(:'proj_id'::uuid, :'phase5_id'::uuid, 'Site Grading Complete', 'Mass grading finished and approved', 'inspection', 'pending', 'critical', '2024-11-15', NULL),

-- Phase 6 Milestones
(:'proj_id'::uuid, :'phase6_id'::uuid, 'Utility Infrastructure Complete', 'All water, sewer, gas lines installed', 'inspection', 'pending', 'critical', '2025-03-30', NULL);

-- Create comprehensive budget for the project

-- Get category IDs
\set land_costs_cat (SELECT category_id FROM budget_categories WHERE category_name = 'Land Costs' AND parent_category_id IS NULL)
\set prof_fees_cat (SELECT category_id FROM budget_categories WHERE category_name = 'Professional Fees' AND parent_category_id IS NULL)
\set site_work_cat (SELECT category_id FROM budget_categories WHERE category_name = 'Site Work' AND parent_category_id IS NULL)
\set infrastructure_cat (SELECT category_id FROM budget_categories WHERE category_name = 'Infrastructure' AND parent_category_id IS NULL)
\set permits_cat (SELECT category_id FROM budget_categories WHERE category_name = 'Permits & Fees' AND parent_category_id IS NULL)

-- Insert budgets by phase and category
INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
-- Phase 1: Land Acquisition
(:'proj_id'::uuid, :'land_costs_cat'::uuid, :'phase1_id'::uuid, 'Land Purchase (30 acres @ $50k/acre)', 1500000.00, 5.00),
(:'proj_id'::uuid, :'land_costs_cat'::uuid, :'phase1_id'::uuid, 'Closing Costs & Title Insurance', 45000.00, 5.00),

-- Phase 2: Due Diligence
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase2_id'::uuid, 'Geotechnical Engineering', 35000.00, 10.00),
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase2_id'::uuid, 'Environmental Assessment', 25000.00, 10.00),
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase2_id'::uuid, 'Market & Feasibility Study', 20000.00, 10.00),

-- Phase 3: Planning & Design
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase3_id'::uuid, 'Civil Engineering (Complete Design)', 180000.00, 10.00),
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase3_id'::uuid, 'Land Planning & Surveying', 65000.00, 10.00),
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase3_id'::uuid, 'Landscape Architecture', 35000.00, 10.00),
(:'proj_id'::uuid, :'prof_fees_cat'::uuid, :'phase3_id'::uuid, 'Traffic Engineering Study', 15000.00, 10.00),

-- Phase 4: Permitting
(:'proj_id'::uuid, :'permits_cat'::uuid, :'phase4_id'::uuid, 'Planning & Zoning Fees', 25000.00, 10.00),
(:'proj_id'::uuid, :'permits_cat'::uuid, :'phase4_id'::uuid, 'Grading & Building Permits', 45000.00, 15.00),
(:'proj_id'::uuid, :'permits_cat'::uuid, :'phase4_id'::uuid, 'Impact Fees (60 lots)', 240000.00, 5.00),
(:'proj_id'::uuid, :'permits_cat'::uuid, :'phase4_id'::uuid, 'Utility Connection Fees', 180000.00, 10.00),

-- Phase 5: Site Preparation
(:'proj_id'::uuid, :'site_work_cat'::uuid, :'phase5_id'::uuid, 'Clearing & Grubbing (30 acres)', 90000.00, 15.00),
(:'proj_id'::uuid, :'site_work_cat'::uuid, :'phase5_id'::uuid, 'Mass Grading & Earthwork', 450000.00, 20.00),
(:'proj_id'::uuid, :'site_work_cat'::uuid, :'phase5_id'::uuid, 'Erosion Control', 35000.00, 15.00),

-- Phase 6: Infrastructure
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Water System (mains & laterals)', 420000.00, 15.00),
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Sanitary Sewer System', 510000.00, 15.00),
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Storm Drainage System', 380000.00, 15.00),
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Roads & Paving', 720000.00, 15.00),
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Gas Distribution', 150000.00, 10.00),
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Electric & Telecom (Underground)', 240000.00, 10.00),
(:'proj_id'::uuid, :'infrastructure_cat'::uuid, :'phase6_id'::uuid, 'Street Lights & Signage', 90000.00, 10.00);

-- Add some actual expenses for completed work
INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date) VALUES
-- Land purchase expenses
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Land Purchase%'), 
 '2024-02-15', 'Land Purchase Payment - 30 acres', 1500000.00, 'wire', 'INV-2024-001', 'paid', '2024-02-15'),
 
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Closing Costs%'), 
 '2024-02-15', 'Title Insurance & Closing Costs', 45000.00, 'check', 'INV-2024-002', 'paid', '2024-02-20'),

-- Phase 2 expenses
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Geotechnical%'), 
 '2024-02-27', 'Geotechnical Survey & Soil Testing', 35000.00, 'check', 'INV-2024-010', 'paid', '2024-03-15'),
 
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Environmental%'), 
 '2024-03-04', 'Phase I Environmental Assessment', 25000.00, 'check', 'INV-2024-015', 'paid', '2024-03-20'),

-- Phase 3 expenses
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Civil Engineering%'), 
 '2024-05-14', 'Civil Engineering Design - Progress Payment 1', 90000.00, 'check', 'INV-2024-030', 'paid', '2024-05-30'),
 
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Civil Engineering%'), 
 '2024-06-15', 'Civil Engineering Design - Final Payment', 90000.00, 'check', 'INV-2024-042', 'paid', '2024-06-30'),

-- Phase 4 expenses (ongoing)
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Planning & Zoning%'), 
 '2024-06-01', 'Planning Commission Application Fees', 15000.00, 'check', 'INV-2024-050', 'paid', '2024-06-10'),
 
(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Grading & Building%'), 
 '2024-07-18', 'Mass Grading Permit', 25000.00, 'check', 'INV-2024-065', 'paid', '2024-07-25'),

(:'proj_id'::uuid, 
 (SELECT budget_id FROM project_budgets WHERE project_id = :'proj_id'::uuid AND budget_name LIKE 'Impact Fees%'), 
 '2024-08-01', 'Impact Fees - Partial Payment (30 lots)', 120000.00, 'wire', 'INV-2024-070', 'approved', NULL);

-- Success message
\echo '=================================================='
\echo 'Sample Project Created Successfully!'
\echo '=================================================='
\echo 'Project: Riverside Estates Development'
\echo 'Code: RSD-001'
\echo '60 lots on 30 acres'
\echo ''
\echo 'Phases: 10 (4 in progress/completed)'
\echo 'Tasks: 40+ detailed tasks'
\echo 'Budget: $5.4M+ total project budget'
\echo 'Expenses: $2.0M+ recorded'
\echo ''
\echo 'Login to http://localhost:3000 to view!'
\echo '=================================================='
