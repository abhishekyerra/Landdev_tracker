-- Seed Data for Land Development Tracking System
-- Insert default phase templates and budget categories

-- ============================================
-- PHASE TEMPLATES (Standard Development Phases)
-- ============================================

INSERT INTO phase_templates (phase_name, phase_order, description, typical_duration_days) VALUES
('Land Acquisition', 1, 'Purchase and secure land ownership, conduct title searches, and complete due diligence', 90),
('Due Diligence & Feasibility', 2, 'Environmental studies, geotechnical surveys, market analysis, and financial feasibility', 60),
('Planning & Design', 3, 'Conceptual design, site planning, engineering drawings, and architectural plans', 120),
('Permitting & Approvals', 4, 'Obtain zoning approvals, building permits, environmental permits, and regulatory clearances', 180),
('Site Preparation', 5, 'Clearing, grading, demolition of existing structures, and initial earthwork', 45),
('Infrastructure Development', 6, 'Install utilities (water, sewer, electric, gas), roads, and drainage systems', 90),
('Vertical Construction', 7, 'Building construction, structural work, and major improvements', 240),
('Finishing & Landscaping', 8, 'Interior finishing, exterior improvements, landscaping, and amenities', 60),
('Inspections & Final Approvals', 9, 'Final inspections, certificate of occupancy, and regulatory sign-offs', 30),
('Project Closeout', 10, 'Documentation, warranty transfers, final payments, and project handover', 30);

-- ============================================
-- BUDGET CATEGORIES (Hierarchical)
-- ============================================

-- Level 1: Main Categories
INSERT INTO budget_categories (category_id, category_name, parent_category_id, description) VALUES
('11111111-1111-1111-1111-111111111111', 'Land Costs', NULL, 'All costs related to land acquisition'),
('22222222-2222-2222-2222-222222222222', 'Professional Fees', NULL, 'Consultants, architects, engineers, and legal fees'),
('33333333-3333-3333-3333-333333333333', 'Site Work', NULL, 'Site preparation, grading, and earthwork'),
('44444444-4444-4444-4444-444444444444', 'Infrastructure', NULL, 'Utilities and off-site improvements'),
('55555555-5555-5555-5555-555555555555', 'Construction', NULL, 'Building and structure construction costs'),
('66666666-6666-6666-6666-666666666666', 'Permits & Fees', NULL, 'Government permits, impact fees, and regulatory costs'),
('77777777-7777-7777-7777-777777777777', 'Financing Costs', NULL, 'Interest, loan fees, and financing charges'),
('88888888-8888-8888-8888-888888888888', 'Marketing & Sales', NULL, 'Marketing, advertising, and sales commissions'),
('99999999-9999-9999-9999-999999999999', 'Contingency', NULL, 'Reserve for unforeseen costs and changes');

-- Level 2: Land Costs Sub-categories
INSERT INTO budget_categories (category_name, parent_category_id, description) VALUES
('Land Purchase Price', '11111111-1111-1111-1111-111111111111', 'Cost of acquiring the land'),
('Title & Escrow', '11111111-1111-1111-1111-111111111111', 'Title insurance and escrow fees'),
('Survey & Boundary', '11111111-1111-1111-1111-111111111111', 'Land surveying and boundary determination');

-- Level 2: Professional Fees Sub-categories
INSERT INTO budget_categories (category_name, parent_category_id, description) VALUES
('Architecture', '22222222-2222-2222-2222-222222222222', 'Architectural design and planning'),
('Civil Engineering', '22222222-2222-2222-2222-222222222222', 'Civil and site engineering'),
('Structural Engineering', '22222222-2222-2222-2222-222222222222', 'Structural engineering services'),
('Geotechnical', '22222222-2222-2222-2222-222222222222', 'Soil studies and geotechnical reports'),
('Environmental', '22222222-2222-2222-2222-222222222222', 'Environmental impact studies and assessments'),
('Legal Fees', '22222222-2222-2222-2222-222222222222', 'Legal counsel and contract review'),
('Project Management', '22222222-2222-2222-2222-222222222222', 'Construction and project management fees');

-- Level 2: Site Work Sub-categories
INSERT INTO budget_categories (category_name, parent_category_id, description) VALUES
('Demolition', '33333333-3333-3333-3333-333333333333', 'Demolition of existing structures'),
('Clearing & Grubbing', '33333333-3333-3333-3333-333333333333', 'Site clearing and vegetation removal'),
('Grading & Excavation', '33333333-3333-3333-3333-333333333333', 'Earthwork and site grading'),
('Erosion Control', '33333333-3333-3333-3333-333333333333', 'Erosion and sediment control measures');

-- Level 2: Infrastructure Sub-categories
INSERT INTO budget_categories (category_name, parent_category_id, description) VALUES
('Water & Sewer', '44444444-4444-4444-4444-444444444444', 'Water and sewer line installation'),
('Electrical', '44444444-4444-4444-4444-444444444444', 'Electrical infrastructure and connections'),
('Gas Lines', '44444444-4444-4444-4444-444444444444', 'Natural gas line installation'),
('Telecommunications', '44444444-4444-4444-4444-444444444444', 'Phone, cable, and fiber optic infrastructure'),
('Roads & Paving', '44444444-4444-4444-4444-444444444444', 'Road construction and paving'),
('Stormwater Management', '44444444-4444-4444-4444-444444444444', 'Drainage systems and retention ponds');

-- Level 2: Construction Sub-categories
INSERT INTO budget_categories (category_name, parent_category_id, description) VALUES
('Foundation', '55555555-5555-5555-5555-555555555555', 'Foundation and concrete work'),
('Framing', '55555555-5555-5555-5555-555555555555', 'Structural framing and roof'),
('Exterior Finishes', '55555555-5555-5555-5555-555555555555', 'Siding, windows, and exterior doors'),
('Roofing', '55555555-5555-5555-5555-555555555555', 'Roofing materials and installation'),
('Mechanical Systems', '55555555-5555-5555-5555-555555555555', 'HVAC systems'),
('Plumbing', '55555555-5555-5555-5555-555555555555', 'Interior plumbing systems'),
('Electrical Systems', '55555555-5555-5555-5555-555555555555', 'Interior electrical wiring and fixtures'),
('Interior Finishes', '55555555-5555-5555-5555-555555555555', 'Drywall, painting, flooring, and trim'),
('Landscaping', '55555555-5555-5555-5555-555555555555', 'Landscaping and outdoor amenities');

-- Level 2: Permits & Fees Sub-categories
INSERT INTO budget_categories (category_name, parent_category_id, description) VALUES
('Building Permits', '66666666-6666-6666-6666-666666666666', 'Building and construction permits'),
('Zoning & Planning', '66666666-6666-6666-6666-666666666666', 'Zoning applications and planning approvals'),
('Impact Fees', '66666666-6666-6666-6666-666666666666', 'School, traffic, and park impact fees'),
('Utility Connections', '66666666-6666-6666-6666-666666666666', 'Water, sewer, and utility tap fees'),
('Environmental Permits', '66666666-6666-6666-6666-666666666666', 'Wetlands, stormwater, and environmental permits');

-- ============================================
-- SAMPLE USERS (for testing)
-- ============================================

-- Password for all test users is 'Password123!' (you should hash this properly in production)
INSERT INTO users (email, password_hash, first_name, last_name, role, phone) VALUES
('admin@landdev.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYnbkJ8l6Xe', 'System', 'Administrator', 'admin', '555-0001'),
('pm@landdev.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYnbkJ8l6Xe', 'Project', 'Manager', 'project_manager', '555-0002'),
('developer@landdev.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYnbkJ8l6Xe', 'Site', 'Developer', 'developer', '555-0003'),
('contractor@landdev.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYnbkJ8l6Xe', 'General', 'Contractor', 'contractor', '555-0004');

-- ============================================
-- SAMPLE VENDORS
-- ============================================

INSERT INTO vendors (vendor_name, vendor_type, contact_name, email, phone, license_number) VALUES
('ABC Construction Co.', 'contractor', 'John Smith', 'john@abcconstruction.com', '555-1001', 'CON-123456'),
('Engineering Solutions LLC', 'consultant', 'Jane Doe', 'jane@engsolutions.com', '555-1002', 'ENG-789012'),
('Land Survey Pros', 'consultant', 'Bob Johnson', 'bob@landsurvey.com', '555-1003', 'SUR-345678'),
('Green Landscaping Inc.', 'contractor', 'Mary Wilson', 'mary@greenlandscape.com', '555-1004', 'LAN-901234'),
('Permit Express', 'consultant', 'Tom Brown', 'tom@permitexpress.com', '555-1005', 'CON-567890');

COMMIT;
