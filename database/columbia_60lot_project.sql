-- 60-Lot Development Project - Columbia TN 38401
-- Phase 1: Lots 1-20 (First Third Delivery)
-- Land: $2.2M | Development: $4M | Total: $6.2M
-- Timeline: 18 months total (6 months per phase)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$
DECLARE
    v_project_id UUID;
    v_user_id UUID;
    v_phase1_id UUID;
    v_phase2_id UUID;
    v_phase3_id UUID;
    
    -- Budget category IDs
    v_land_costs UUID;
    v_site_work UUID;
    v_infrastructure UUID;
    v_permits UUID;
    v_prof_fees UUID;
BEGIN
    -- Get admin user
    SELECT user_id INTO v_user_id FROM users WHERE email = 'admin@landdev.com' LIMIT 1;
    
    -- Get budget categories
    SELECT category_id INTO v_land_costs FROM budget_categories WHERE category_name = 'Land Costs' AND parent_category_id IS NULL;
    SELECT category_id INTO v_site_work FROM budget_categories WHERE category_name = 'Site Work' AND parent_category_id IS NULL;
    SELECT category_id INTO v_infrastructure FROM budget_categories WHERE category_name = 'Infrastructure' AND parent_category_id IS NULL;
    SELECT category_id INTO v_permits FROM budget_categories WHERE category_name = 'Permits & Fees' AND parent_category_id IS NULL;
    SELECT category_id INTO v_prof_fees FROM budget_categories WHERE category_name = 'Professional Fees' AND parent_category_id IS NULL;
    
    -- Generate project UUID
    v_project_id := uuid_generate_v4();
    
    -- ============================================
    -- CREATE MAIN PROJECT
    -- ============================================
    INSERT INTO projects (
        project_id, project_name, project_code, description,
        location_address, location_city, location_state, location_zip,
        total_acres, zoning_classification, project_type, status,
        start_date, target_completion_date, created_by
    ) VALUES (
        v_project_id,
        'Columbia 60-Lot Development',
        'COL-60-2024',
        '60-lot residential subdivision on 40 acres in Columbia TN. Phased delivery: 20 lots per phase to builder.',
        'TBD - Columbia Area',
        'Columbia',
        'Tennessee',
        '38401',
        40.00,
        'R-15 Residential',
        'residential',
        'in_progress',
        CURRENT_DATE,
        CURRENT_DATE + INTERVAL '18 months',
        v_user_id
    );
    
    -- ============================================
    -- CREATE 3 PHASES (6 months each)
    -- ============================================
    
    -- Phase 1: Lots 1-20 (Months 1-6)
    INSERT INTO project_phases (
        project_id, phase_name, phase_order, description,
        status, planned_start_date, planned_end_date, actual_start_date, completion_percentage
    ) VALUES (
        v_project_id,
        'Phase 1: Lots 1-20 Development',
        1,
        'Site prep, utilities, and infrastructure for first 20 lots. Deliver ready-to-build lots to builder.',
        'in_progress',
        CURRENT_DATE,
        CURRENT_DATE + INTERVAL '6 months',
        CURRENT_DATE,
        15
    ) RETURNING phase_id INTO v_phase1_id;
    
    -- Phase 2: Lots 21-40 (Months 7-12)
    INSERT INTO project_phases (
        project_id, phase_name, phase_order, description,
        status, planned_start_date, planned_end_date, completion_percentage
    ) VALUES (
        v_project_id,
        'Phase 2: Lots 21-40 Development',
        2,
        'Infrastructure and utilities for lots 21-40. Second delivery to builder.',
        'not_started',
        CURRENT_DATE + INTERVAL '6 months',
        CURRENT_DATE + INTERVAL '12 months',
        0
    ) RETURNING phase_id INTO v_phase2_id;
    
    -- Phase 3: Lots 41-60 (Months 13-18)
    INSERT INTO project_phases (
        project_id, phase_name, phase_order, description,
        status, planned_start_date, planned_end_date, completion_percentage
    ) VALUES (
        v_project_id,
        'Phase 3: Lots 41-60 Development',
        3,
        'Final phase infrastructure for lots 41-60. Final delivery to builder.',
        'not_started',
        CURRENT_DATE + INTERVAL '12 months',
        CURRENT_DATE + INTERVAL '18 months',
        0
    ) RETURNING phase_id INTO v_phase3_id;
    
    -- ============================================
    -- BUDGET ALLOCATION
    -- ============================================
    
    -- LAND COSTS (One-time, allocated to Phase 1)
    INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
        (v_project_id, v_land_costs, v_phase1_id, 'Land Purchase - 40 Acres', 2200000.00, 2.00),
        (v_project_id, v_land_costs, v_phase1_id, 'Closing Costs & Title', 50000.00, 5.00);
    
    -- PROFESSIONAL FEES (Spread across phases)
    INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
        (v_project_id, v_prof_fees, v_phase1_id, 'Civil Engineering - Phase 1', 80000.00, 10.00),
        (v_project_id, v_prof_fees, v_phase1_id, 'Surveying & Layout - Phase 1', 25000.00, 10.00),
        (v_project_id, v_prof_fees, v_phase2_id, 'Civil Engineering - Phase 2', 60000.00, 10.00),
        (v_project_id, v_prof_fees, v_phase3_id, 'Civil Engineering - Phase 3', 60000.00, 10.00);
    
    -- PERMITS & FEES
    INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
        (v_project_id, v_permits, v_phase1_id, 'Master Plan Approval', 35000.00, 10.00),
        (v_project_id, v_permits, v_phase1_id, 'Impact Fees - Phase 1 (20 lots)', 120000.00, 5.00),
        (v_project_id, v_permits, v_phase1_id, 'Utility Connection Fees - Phase 1', 90000.00, 10.00),
        (v_project_id, v_permits, v_phase2_id, 'Impact Fees - Phase 2 (20 lots)', 120000.00, 5.00),
        (v_project_id, v_permits, v_phase3_id, 'Impact Fees - Phase 3 (20 lots)', 120000.00, 5.00);
    
    -- SITE WORK
    INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
        (v_project_id, v_site_work, v_phase1_id, 'Mass Grading - Phase 1 Section', 180000.00, 15.00),
        (v_project_id, v_site_work, v_phase1_id, 'Clearing & Grubbing - Phase 1', 60000.00, 15.00),
        (v_project_id, v_site_work, v_phase1_id, 'Erosion Control - Phase 1', 25000.00, 10.00),
        (v_project_id, v_site_work, v_phase2_id, 'Mass Grading - Phase 2 Section', 160000.00, 15.00),
        (v_project_id, v_site_work, v_phase3_id, 'Mass Grading - Phase 3 Section', 160000.00, 15.00);
    
    -- INFRASTRUCTURE (Roads, Utilities)
    INSERT INTO project_budgets (project_id, category_id, phase_id, budget_name, budgeted_amount, contingency_percentage) VALUES
        (v_project_id, v_infrastructure, v_phase1_id, 'Water System - Phase 1 (20 lots)', 280000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase1_id, 'Sewer System - Phase 1 (20 lots)', 340000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase1_id, 'Storm Drainage - Phase 1', 220000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase1_id, 'Roads & Paving - Phase 1', 380000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase1_id, 'Electric/Gas/Telecom - Phase 1', 180000.00, 10.00),
        (v_project_id, v_infrastructure, v_phase2_id, 'Water System - Phase 2 (20 lots)', 260000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase2_id, 'Sewer System - Phase 2 (20 lots)', 320000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase2_id, 'Storm Drainage - Phase 2', 200000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase2_id, 'Roads & Paving - Phase 2', 360000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase2_id, 'Electric/Gas/Telecom - Phase 2', 170000.00, 10.00),
        (v_project_id, v_infrastructure, v_phase3_id, 'Water System - Phase 3 (20 lots)', 260000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase3_id, 'Sewer System - Phase 3 (20 lots)', 320000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase3_id, 'Storm Drainage - Phase 3', 200000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase3_id, 'Roads & Paving - Phase 3', 360000.00, 15.00),
        (v_project_id, v_infrastructure, v_phase3_id, 'Electric/Gas/Telecom - Phase 3', 170000.00, 10.00);
    
    -- ============================================
    -- PHASE 1 DETAILED TASKS (Current Focus)
    -- ============================================
    
    -- Month 1: Site Preparation & Permitting
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase1_id, 'Submit Master Development Plan', 'Submit plans for all 60 lots to planning commission', 'completed', 'critical', CURRENT_DATE + 5, 40),
        (v_project_id, v_phase1_id, 'Stake Property Boundaries', 'Survey and stake 40-acre boundary', 'completed', 'high', CURRENT_DATE + 7, 24),
        (v_project_id, v_phase1_id, 'Clear Phase 1 Section (Lots 1-20)', 'Clear trees and vegetation for lots 1-20', 'in_progress', 'critical', CURRENT_DATE + 20, 120),
        (v_project_id, v_phase1_id, 'Install Erosion Control', 'Silt fencing and erosion barriers', 'in_progress', 'critical', CURRENT_DATE + 15, 40),
        (v_project_id, v_phase1_id, 'Obtain Grading Permit - Phase 1', 'Mass grading permit for Phase 1 area', 'todo', 'critical', CURRENT_DATE + 25, 30);
    
    -- Month 2: Grading & Earthwork
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase1_id, 'Mass Grading - Lots 1-20', 'Grade lots 1-20 to design elevations', 'todo', 'critical', CURRENT_DATE + 45, 200),
        (v_project_id, v_phase1_id, 'Create Detention Pond - Phase 1', 'Excavate stormwater detention', 'todo', 'critical', CURRENT_DATE + 50, 80),
        (v_project_id, v_phase1_id, 'Rough Grade Roads - Phase 1', 'Rough grade for Phase 1 streets', 'todo', 'high', CURRENT_DATE + 55, 100);
    
    -- Month 3: Underground Utilities
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase1_id, 'Install Water Main - Phase 1', 'Install 8" water main for lots 1-20', 'todo', 'critical', CURRENT_DATE + 75, 160),
        (v_project_id, v_phase1_id, 'Install Sewer Lines - Phase 1', 'Install sanitary sewer for lots 1-20', 'todo', 'critical', CURRENT_DATE + 80, 180),
        (v_project_id, v_phase1_id, 'Install Storm Drains - Phase 1', 'Storm sewer system for lots 1-20', 'todo', 'critical', CURRENT_DATE + 85, 140),
        (v_project_id, v_phase1_id, 'Water Service Laterals - Lots 1-20', 'Stub water to each lot', 'todo', 'high', CURRENT_DATE + 90, 80),
        (v_project_id, v_phase1_id, 'Sewer Service Laterals - Lots 1-20', 'Stub sewer to each lot', 'todo', 'high', CURRENT_DATE + 90, 80);
    
    -- Month 4: Gas, Electric, Telecom
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase1_id, 'Install Gas Lines - Phase 1', 'Natural gas distribution', 'todo', 'high', CURRENT_DATE + 105, 100),
        (v_project_id, v_phase1_id, 'Install Underground Electric - Phase 1', 'Electric conduit and transformer pads', 'todo', 'critical', CURRENT_DATE + 110, 120),
        (v_project_id, v_phase1_id, 'Install Fiber/Telecom - Phase 1', 'Underground fiber and telecom', 'todo', 'medium', CURRENT_DATE + 115, 80);
    
    -- Month 5: Road Construction
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase1_id, 'Install Road Base - Phase 1', 'Aggregate base for Phase 1 streets', 'todo', 'critical', CURRENT_DATE + 135, 120),
        (v_project_id, v_phase1_id, 'Pave Roads - Phase 1', 'Asphalt paving for Phase 1', 'todo', 'critical', CURRENT_DATE + 145, 100),
        (v_project_id, v_phase1_id, 'Install Curb & Gutter - Phase 1', 'Concrete curbing', 'todo', 'high', CURRENT_DATE + 140, 80);
    
    -- Month 6: Final Touches & Inspection
    INSERT INTO tasks (project_id, phase_id, task_name, description, status, priority, due_date, estimated_hours) VALUES
        (v_project_id, v_phase1_id, 'Final Grade Lots 1-20', 'Fine grading and topsoil', 'todo', 'high', CURRENT_DATE + 160, 60),
        (v_project_id, v_phase1_id, 'Install Street Signs - Phase 1', 'Street name signs', 'todo', 'medium', CURRENT_DATE + 165, 16),
        (v_project_id, v_phase1_id, 'Seed/Sod Common Areas - Phase 1', 'Landscaping common areas', 'todo', 'medium', CURRENT_DATE + 170, 40),
        (v_project_id, v_phase1_id, 'Final Inspection - Lots 1-20', 'City final inspection for occupancy', 'todo', 'critical', CURRENT_DATE + 175, 24),
        (v_project_id, v_phase1_id, 'Deliver Lots 1-20 to Builder', 'Transfer ready-to-build lots', 'todo', 'critical', CURRENT_DATE + 180, 16);
    
    -- ============================================
    -- MILESTONES
    -- ============================================
    
    INSERT INTO milestones (project_id, phase_id, milestone_name, milestone_type, status, priority, due_date) VALUES
        (v_project_id, v_phase1_id, 'Master Plan Approved', 'approval', 'completed', 'critical', CURRENT_DATE + 10),
        (v_project_id, v_phase1_id, 'Phase 1 Grading Complete', 'inspection', 'pending', 'critical', CURRENT_DATE + 60),
        (v_project_id, v_phase1_id, 'All Utilities Installed - Phase 1', 'inspection', 'pending', 'critical', CURRENT_DATE + 120),
        (v_project_id, v_phase1_id, 'Roads Paved - Phase 1', 'inspection', 'pending', 'critical', CURRENT_DATE + 150),
        (v_project_id, v_phase1_id, 'Lots 1-20 Ready for Builder', 'delivery', 'pending', 'critical', CURRENT_DATE + 180),
        (v_project_id, v_phase2_id, 'Lots 21-40 Ready for Builder', 'delivery', 'pending', 'critical', CURRENT_DATE + 360),
        (v_project_id, v_phase3_id, 'Lots 41-60 Ready for Builder', 'delivery', 'pending', 'critical', CURRENT_DATE + 540);
    
    -- ============================================
    -- INITIAL EXPENSES (Land Purchase)
    -- ============================================
    
    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, payment_status)
    SELECT v_project_id, budget_id, CURRENT_DATE - 5, 'Land Purchase - 40 Acres in Columbia TN', 2200000.00, 'wire', 'paid'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name = 'Land Purchase - 40 Acres' LIMIT 1;
    
    INSERT INTO expenses (project_id, budget_id, expense_date, description, amount, payment_method, payment_status)
    SELECT v_project_id, budget_id, CURRENT_DATE - 5, 'Closing Costs and Title Insurance', 50000.00, 'check', 'paid'
    FROM project_budgets WHERE project_id = v_project_id AND budget_name = 'Closing Costs & Title' LIMIT 1;
    
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Columbia 60-Lot Development Created!';
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'Project: Columbia 60-Lot Development';
    RAISE NOTICE 'Code: COL-60-2024';
    RAISE NOTICE 'Location: Columbia, TN 38401';
    RAISE NOTICE '40 acres, 60 lots total';
    RAISE NOTICE '';
    RAISE NOTICE 'Budget:';
    RAISE NOTICE '  Land: $2.2M';
    RAISE NOTICE '  Development: $4.0M';
    RAISE NOTICE '  Total: $6.2M';
    RAISE NOTICE '';
    RAISE NOTICE 'Timeline: 18 months (6 months per phase)';
    RAISE NOTICE '  Phase 1: Lots 1-20 (In Progress - 15%%)';
    RAISE NOTICE '  Phase 2: Lots 21-40 (Not Started)';
    RAISE NOTICE '  Phase 3: Lots 41-60 (Not Started)';
    RAISE NOTICE '';
    RAISE NOTICE 'Phase 1 Tasks: 25 detailed tasks';
    RAISE NOTICE 'Current Status: Site prep and clearing underway';
    RAISE NOTICE '';
    RAISE NOTICE 'Login to http://localhost:3000 to view!';
    RAISE NOTICE '==================================================';
END $$;
