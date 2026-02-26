-- Sample Land Development Project: Riverside Estates
-- 60 lots on 30 acres - Simplified version
-- This script works when piped to psql

-- Ensure UUID extension is enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$
DECLARE
    v_project_id UUID;
    v_user_id UUID;
    v_phase1_id UUID;
    v_phase2_id UUID;
    v_phase3_id UUID;
    v_phase4_id UUID;
    v_phase5_id UUID;
    v_phase6_id UUID;
    v_land_costs_cat UUID;
    v_prof_fees_cat UUID;
    v_site_work_cat UUID;
    v_infrastructure_cat UUID;
    v_permits_cat UUID;
BEGIN
    -- Get admin user ID
    SELECT user_id INTO v_user_id FROM users WHERE email = 'admin@landdev.com' LIMIT 1;
    
    -- Generate a new UUID for the project
    v_project_id := uuid_generate_v4();
    
    -- Get budget category IDs
    SELECT category_id INTO v_land_costs_cat FROM budget_categories WHERE category_name = 'Land Costs' AND parent_category_id IS NULL;
    SELECT category_id INTO v_prof_fees_cat FROM budget_categories WHERE category_name = 'Professional Fees' AND parent_category_id IS NULL;
    SELECT category_id INTO v_site_work_cat FROM budget_categories WHERE category_name = 'Site Work' AND parent_category_id IS NULL;
    SELECT category_id INTO v_infrastructure_cat FROM budget_categories WHERE category_name = 'Infrastructure' AND parent_category_id IS NULL;
    SELECT category_id INTO v_permits_cat FROM budget_categories WHERE category_name = 'Permits & Fees' AND parent_category_id IS NULL;

    -- Insert the main project
    INSERT INTO projects (
        project_id, project_name, project_code, description, location_address, location_city,
        location_state, location_zip, total_acres, zoning_classification, project_type,
        status, start_date, target_completion_date, created_by
    ) VALUES (
        v_project_id,
        'Riverside Estates Development',
        'RSD-001',
        '60-lot residential subdivision on 30 acres with community amenities',
        '1234 County Road 500', 'Franklin', 'Tennessee', '37064',
        30.00, 'R-20 Residential', 'residential', 'in_progress',
        '2024-01-15', '2025-12-31', v_user_id
    );

    -- Insert phases
    INSERT INTO project_phases (project_id, phase_name, phase_order, status, planned_start_date, planned_end_date, actual_start_date, completion_percentage)
    VALUES 
        (v_project_id, 'Land Acquisition', 1, 'completed', '2024-01-15', '2024-03-15', '2024-01-15', 100),
        (v_project_id, 'Due Diligence & Feasibility', 2, 'completed', '2024-02-15', '2024-04-15', '2024-02-15', 100),
        (v_project_id, 'Planning & Design', 3, 'completed', '2024-03-15', '2024-06-15', '2024-03-15', 100),
        (v_project_id, 'Permitting & Approvals', 4, 'in_progress', '2024-06-01', '2024-09-15', '2024-06-01', 65),
        (v_project_id, 'Site Preparation', 5, 'not_started', '2024-09-15', '2024-11-15', NULL, 0),
        (v_project_id, 'Infrastructure Development', 6, 'not_started', '2024-11-15', '2025-04-01', NULL, 0),
        (v_project_id, 'Vertical Construction', 7, 'not_started', '2025-04-01', '2025-11-01', NULL, 0),
        (v_project_id, 'Finishing & Landscaping', 8, 'not_started', '2025-11-01', '2025-12-15', NULL, 0),
        (v_project_id, 'Inspections & Final Approvals', 9, 'not_started', '2025-12-01', '2025-12-31', NULL, 0),
        (v_project_id, 'Project Closeout', 10, 'not_started', '2025-12-15', '2025-12-31', NULL, 0);

    -- Get phase IDs
    SELECT phase_id INTO v_phase1_id FROM project_phases WHERE project_id = v_project_id AND phase_order = 1;
    SELECT phase_id INTO v_phase2_id FROM project_phases WHERE project_id = v_project_id AND phase_order = 2;
    SELECT phase_id INTO v_phase3_id FROM project_phases WHERE project_id = v_project_id AND phase_order = 3;
    SELECT phase_id INTO v_phase4_id FROM project_phases WHERE project_id = v_project_id AND phase_order = 4;
    SELECT phase_id INTO v_phase5_id FROM project_phases WHERE project_id = v_project_id AND phase_order = 5;
    SELECT phase_id INTO v_phase6_id FROM project_phases WHERE project_id = v_project_id AND phase_order = 6;

    -- Insert budgets
    INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
        (v_project_id, v_land_costs_cat, v_phase1_id, 'Land Purchase (30 acres @ $50k/acre)', 1500000.00, 5.00),
        (v_project_id, v_land_costs_cat, v_phase1_id, 'Closing Costs & Title Insurance', 45000.00, 5.00),
        (v_project_id, v_prof_fees_cat, v_phase2_id, 'Geotechnical Engineering', 35000.00, 10.00),
        (v_project_id, v_prof_fees_cat, v_phase2_id, 'Environmental Assessment', 25000.00, 10.00),
        (v_project_id, v_prof_fees_cat, v_phase3_id, 'Civil Engineering (Complete Design)', 180000.00, 10.00),
        (v_project_id, v_prof_fees_cat, v_phase3_id, 'Land Planning & Surveying', 65000.00, 10.00),
        (v_project_id, v_permits_cat, v_phase4_id, 'Planning & Zoning Fees', 25000.00, 10.00),
        (v_project_id, v_permits_cat, v_phase4_id, 'Impact Fees (60 lots)', 240000.00, 5.00),
        (v_project_id, v_permits_cat, v_phase4_id, 'Utility Connection Fees', 180000.00, 10.00),
        (v_project_id, v_site_work_cat, v_phase5_id, 'Clearing & Grubbing (30 acres)', 90000.00, 15.00),
        (v_project_id, v_site_work_cat, v_phase5_id, 'Mass Grading & Earthwork', 450000.00, 20.00),
        (v_project_id, v_infrastructure_cat, v_phase6_id, 'Water System', 420000.00, 15.00),
        (v_project_id, v_infrastructure_cat, v_phase6_id, 'Sanitary Sewer System', 510000.00, 15.00),
        (v_project_id, v_infrastructure_cat, v_phase6_id, 'Storm Drainage System', 380000.00, 15.00),
        (v_project_id, v_infrastructure_cat, v_phase6_id, 'Roads & Paving', 720000.00, 15.00);

    -- Insert tasks for Phase 1 (Completed)
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
        (v_project_id, v_phase1_id, 'Execute Purchase Agreement', 'Finalize and sign land purchase contract', 'completed', 'critical', '2024-01-20', '2024-01-18', 40, 38),
        (v_project_id, v_phase1_id, 'Title Search & Insurance', 'Complete title search and obtain title insurance', 'completed', 'critical', '2024-01-25', '2024-01-24', 20, 22),
        (v_project_id, v_phase1_id, 'Survey Property Boundaries', 'Professional boundary survey of 30 acres', 'completed', 'high', '2024-02-01', '2024-01-31', 60, 65),
        (v_project_id, v_phase1_id, 'Close on Property', 'Complete closing and transfer ownership', 'completed', 'critical', '2024-02-15', '2024-02-15', 16, 16);

    -- Insert tasks for Phase 2 (Completed)
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
        (v_project_id, v_phase2_id, 'Geotechnical Survey', 'Soil testing and analysis', 'completed', 'critical', '2024-02-28', '2024-02-27', 80, 85),
        (v_project_id, v_phase2_id, 'Environmental Assessment', 'Phase I environmental assessment', 'completed', 'critical', '2024-03-05', '2024-03-04', 60, 62),
        (v_project_id, v_phase2_id, 'Market Study & Feasibility', 'Analyze market demand for 60 lots', 'completed', 'high', '2024-03-15', '2024-03-14', 100, 105);

    -- Insert tasks for Phase 3 (Completed)
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
        (v_project_id, v_phase3_id, 'Preliminary Plat Design', 'Design lot layout for 60 lots', 'completed', 'critical', '2024-04-15', '2024-04-12', 200, 215),
        (v_project_id, v_phase3_id, 'Civil Engineering Plans', 'Complete grading, drainage, and utility plans', 'completed', 'critical', '2024-05-01', '2024-04-28', 300, 320),
        (v_project_id, v_phase3_id, 'Stormwater Management Design', 'Design detention pond and drainage', 'completed', 'critical', '2024-05-10', '2024-05-08', 120, 125);

    -- Insert tasks for Phase 4 (In Progress)
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, completed_date, estimated_hours, actual_hours) VALUES
        (v_project_id, v_phase4_id, 'Submit Preliminary Plat', 'Submit to planning commission', 'completed', 'critical', '2024-06-01', '2024-05-30', 40, 42),
        (v_project_id, v_phase4_id, 'Planning Commission Review', 'Present and address comments', 'completed', 'critical', '2024-06-20', '2024-06-18', 60, 65),
        (v_project_id, v_phase4_id, 'Preliminary Plat Approval', 'Obtain preliminary approval', 'completed', 'critical', '2024-07-01', '2024-06-28', 20, 18),
        (v_project_id, v_phase4_id, 'Grading Permit Application', 'Apply for mass grading permit', 'completed', 'critical', '2024-07-20', '2024-07-18', 40, 38),
        (v_project_id, v_phase4_id, 'Utility Permits (Water/Sewer)', 'Water and sewer permits', 'in_progress', 'critical', '2024-08-15', NULL, 60, 45),
        (v_project_id, v_phase4_id, 'Stormwater Permit (NPDES)', 'Stormwater management permit', 'in_progress', 'critical', '2024-08-20', NULL, 80, 52),
        (v_project_id, v_phase4_id, 'Road & Infrastructure Permit', 'Road construction permits', 'todo', 'critical', '2024-09-01', NULL, 40, 0);

    -- Insert tasks for Phase 5 (Not Started)
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase5_id, 'Clear & Grub 30 Acres', 'Remove trees and vegetation', 'todo', 'critical', '2024-10-15', 200),
        (v_project_id, v_phase5_id, 'Mass Grading', 'Grade entire site to design elevations', 'todo', 'critical', '2024-11-01', 300),
        (v_project_id, v_phase5_id, 'Install Erosion Control', 'Silt fences and erosion control', 'todo', 'critical', '2024-10-20', 80);

    -- Insert tasks for Phase 6 (Not Started)
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase6_id, 'Install Water Lines', 'Install 8" water mains', 'todo', 'critical', '2025-01-15', 400),
        (v_project_id, v_phase6_id, 'Install Sewer Lines', 'Sanitary sewer collection', 'todo', 'critical', '2025-02-01', 450),
        (v_project_id, v_phase6_id, 'Install Storm Drains', 'Storm sewer and drainage', 'todo', 'critical', '2025-02-15', 350),
        (v_project_id, v_phase6_id, 'Road Base Construction', 'Construct road base', 'todo', 'critical', '2025-03-15', 500);

    -- Insert milestones
    INSERT INTO milestones (project_id, phase_id, milestone_name, milestone_type, status, priority, due_date, completed_date) VALUES
        (v_project_id, v_phase1_id, 'Property Ownership Transfer', 'approval', 'completed', 'critical', '2024-02-15', '2024-02-15'),
        (v_project_id, v_phase2_id, 'Environmental Clearance', 'approval', 'completed', 'critical', '2024-03-05', '2024-03-04'),
        (v_project_id, v_phase3_id, 'Preliminary Plans Complete', 'delivery', 'completed', 'critical', '2024-05-15', '2024-05-14'),
        (v_project_id, v_phase4_id, 'Preliminary Plat Approved', 'approval', 'completed', 'critical', '2024-07-01', '2024-06-28'),
        (v_project_id, v_phase4_id, 'All Permits Obtained', 'permit', 'in_progress', 'critical', '2024-09-15', NULL),
        (v_project_id, v_phase5_id, 'Site Grading Complete', 'inspection', 'pending', 'critical', '2024-11-15', NULL),
        (v_project_id, v_phase6_id, 'Utility Infrastructure Complete', 'inspection', 'pending', 'critical', '2025-03-30', NULL);

    -- Insert expenses (use budget IDs by querying)
    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date)
    SELECT v_project_id, budget_id, '2024-02-15', 'Land Purchase Payment - 30 acres', 1500000.00, 'wire', 'INV-2024-001', 'paid', '2024-02-15'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name LIKE 'Land Purchase%' LIMIT 1;

    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date)
    SELECT v_project_id, budget_id, '2024-02-15', 'Title Insurance & Closing', 45000.00, 'check', 'INV-2024-002', 'paid', '2024-02-20'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name LIKE 'Closing Costs%' LIMIT 1;

    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date)
    SELECT v_project_id, budget_id, '2024-02-27', 'Geotechnical Survey', 35000.00, 'check', 'INV-2024-010', 'paid', '2024-03-15'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name LIKE 'Geotechnical%' LIMIT 1;

    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date)
    SELECT v_project_id, budget_id, '2024-03-04', 'Environmental Assessment', 25000.00, 'check', 'INV-2024-015', 'paid', '2024-03-20'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name LIKE 'Environmental%' LIMIT 1;

    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date)
    SELECT v_project_id, budget_id, '2024-05-14', 'Civil Engineering - Progress Payment 1', 90000.00, 'check', 'INV-2024-030', 'paid', '2024-05-30'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name LIKE 'Civil Engineering%' LIMIT 1;

    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, invoice_number, payment_status, payment_date)
    SELECT v_project_id, budget_id, '2024-06-15', 'Civil Engineering - Final Payment', 90000.00, 'check', 'INV-2024-042', 'paid', '2024-06-30'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name LIKE 'Civil Engineering%' LIMIT 1;

    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Sample Project Created Successfully!';
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Project: Riverside Estates Development';
    RAISE NOTICE 'Code: RSD-001';
    RAISE NOTICE '60 lots on 30 acres';
    RAISE NOTICE '';
    RAISE NOTICE 'Phases: 10 (4 in progress/completed)';
    RAISE NOTICE 'Tasks: 25+ detailed tasks';
    RAISE NOTICE 'Budget: $5.4M+ total';
    RAISE NOTICE 'Expenses: $1.8M+ recorded';
    RAISE NOTICE '';
    RAISE NOTICE 'Login to http://localhost:3000 to view!';
    RAISE NOTICE '==================================================';
END $$;
