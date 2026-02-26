"""
Pydantic Schemas for API Request/Response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import uuid

# ============================================
# AUTHENTICATION SCHEMAS
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = Field(..., pattern="^(admin|project_manager|developer|contractor|viewer)$")
    phone: Optional[str] = None

class UserResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# PROJECT SCHEMAS
# ============================================

class ProjectCreate(BaseModel):
    project_name: str
    project_code: str
    description: Optional[str] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_zip: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    total_acres: Optional[Decimal] = None
    zoning_classification: Optional[str] = None
    project_type: Optional[str] = None
    status: str = 'planning'
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_zip: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    total_acres: Optional[Decimal] = None
    zoning_classification: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None

class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    project_code: str
    description: Optional[str]
    location_address: Optional[str]
    location_city: Optional[str]
    location_state: Optional[str]
    location_zip: Optional[str]
    total_acres: Optional[Decimal]
    zoning_classification: Optional[str]
    project_type: Optional[str]
    status: str
    start_date: Optional[date]
    target_completion_date: Optional[date]
    actual_completion_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# PHASE SCHEMAS
# ============================================

class PhaseCreate(BaseModel):
    phase_template_id: Optional[uuid.UUID] = None
    phase_name: str
    phase_order: int
    description: Optional[str] = None
    status: str = 'not_started'
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    completion_percentage: int = 0

class PhaseUpdate(BaseModel):
    phase_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None

class PhaseResponse(BaseModel):
    phase_id: uuid.UUID
    project_id: uuid.UUID
    phase_name: str
    phase_order: int
    description: Optional[str]
    status: str
    planned_start_date: Optional[date]
    planned_end_date: Optional[date]
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    completion_percentage: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# MILESTONE SCHEMAS
# ============================================

class MilestoneCreate(BaseModel):
    milestone_name: str
    description: Optional[str] = None
    milestone_type: Optional[str] = None
    status: str = 'pending'
    priority: str = 'medium'
    due_date: Optional[date] = None
    assigned_to: Optional[uuid.UUID] = None
    dependencies: Optional[str] = None
    notes: Optional[str] = None

class MilestoneUpdate(BaseModel):
    milestone_name: Optional[str] = None
    description: Optional[str] = None
    milestone_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    assigned_to: Optional[uuid.UUID] = None
    dependencies: Optional[str] = None
    notes: Optional[str] = None

class MilestoneResponse(BaseModel):
    milestone_id: uuid.UUID
    phase_id: uuid.UUID
    project_id: uuid.UUID
    milestone_name: str
    description: Optional[str]
    milestone_type: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    completed_date: Optional[date]
    assigned_to: Optional[uuid.UUID]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# BUDGET SCHEMAS
# ============================================

class BudgetCreate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    phase_id: Optional[uuid.UUID] = None
    budget_name: str
    budgeted_amount: Decimal
    contingency_percentage: Decimal = Decimal('10.00')
    notes: Optional[str] = None

class BudgetUpdate(BaseModel):
    budget_name: Optional[str] = None
    budgeted_amount: Optional[Decimal] = None
    contingency_percentage: Optional[Decimal] = None
    notes: Optional[str] = None

class BudgetResponse(BaseModel):
    budget_id: uuid.UUID
    project_id: uuid.UUID
    category_id: Optional[uuid.UUID]
    phase_id: Optional[uuid.UUID]
    budget_name: str
    budgeted_amount: Decimal
    contingency_percentage: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# EXPENSE SCHEMAS
# ============================================

class ExpenseCreate(BaseModel):
    budget_id: Optional[uuid.UUID] = None
    line_item_id: Optional[uuid.UUID] = None
    phase_id: Optional[uuid.UUID] = None
    vendor_id: Optional[uuid.UUID] = None
    expense_date: date
    description: str
    amount: Decimal
    payment_method: Optional[str] = None
    invoice_number: Optional[str] = None
    payment_status: str = 'pending'
    payment_date: Optional[date] = None
    approved_by: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class ExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    invoice_number: Optional[str] = None
    payment_status: Optional[str] = None
    payment_date: Optional[date] = None
    approved_by: Optional[uuid.UUID] = None
    notes: Optional[str] = None

class ExpenseResponse(BaseModel):
    expense_id: uuid.UUID
    project_id: uuid.UUID
    budget_id: Optional[uuid.UUID]
    vendor_id: Optional[uuid.UUID]
    expense_date: date
    description: str
    amount: Decimal
    payment_method: Optional[str]
    invoice_number: Optional[str]
    payment_status: str
    payment_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# VENDOR SCHEMAS
# ============================================

class VendorCreate(BaseModel):
    vendor_name: str
    vendor_type: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    license_number: Optional[str] = None
    insurance_expiry: Optional[date] = None
    notes: Optional[str] = None

class VendorResponse(BaseModel):
    vendor_id: uuid.UUID
    vendor_name: str
    vendor_type: Optional[str]
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    license_number: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
