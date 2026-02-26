"""
SQLAlchemy Models for Land Development Tracker
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, ARRAY, DECIMAL, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(255), nullable=False)
    project_code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    location_address = Column(Text)
    location_city = Column(String(100))
    location_state = Column(String(50))
    location_zip = Column(String(20))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    total_acres = Column(DECIMAL(10, 2))
    zoning_classification = Column(String(100))
    project_type = Column(String(100))
    status = Column(String(50), default='planning')
    start_date = Column(Date)
    target_completion_date = Column(Date)
    actual_completion_date = Column(Date)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    budgets = relationship("ProjectBudget", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="project", cascade="all, delete-orphan")

class PhaseTemplate(Base):
    __tablename__ = "phase_templates"
    
    phase_template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase_name = Column(String(255), nullable=False)
    phase_order = Column(Integer, nullable=False)
    description = Column(Text)
    typical_duration_days = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProjectPhase(Base):
    __tablename__ = "project_phases"
    
    phase_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'))
    phase_template_id = Column(UUID(as_uuid=True), ForeignKey('phase_templates.phase_template_id'))
    phase_name = Column(String(255), nullable=False)
    phase_order = Column(Integer, nullable=False)
    description = Column(Text)
    status = Column(String(50), default='not_started')
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    completion_percentage = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="phases")
    milestones = relationship("Milestone", back_populates="phase", cascade="all, delete-orphan")

class Milestone(Base):
    __tablename__ = "milestones"
    
    milestone_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase_id = Column(UUID(as_uuid=True), ForeignKey('project_phases.phase_id', ondelete='CASCADE'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'))
    milestone_name = Column(String(255), nullable=False)
    description = Column(Text)
    milestone_type = Column(String(100))
    status = Column(String(50), default='pending')
    priority = Column(String(20), default='medium')
    due_date = Column(Date)
    completed_date = Column(Date)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    dependencies = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    phase = relationship("ProjectPhase", back_populates="milestones")

class BudgetCategory(Base):
    __tablename__ = "budget_categories"
    
    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = Column(String(255), nullable=False)
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey('budget_categories.category_id'))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProjectBudget(Base):
    __tablename__ = "project_budgets"
    
    budget_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'))
    category_id = Column(UUID(as_uuid=True), ForeignKey('budget_categories.category_id'))
    phase_id = Column(UUID(as_uuid=True), ForeignKey('project_phases.phase_id', ondelete='CASCADE'))
    budget_name = Column(String(255), nullable=False)
    budgeted_amount = Column(DECIMAL(15, 2), nullable=False)
    contingency_percentage = Column(DECIMAL(5, 2), default=10.00)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="budgets")
    line_items = relationship("BudgetLineItem", back_populates="budget", cascade="all, delete-orphan")

class BudgetLineItem(Base):
    __tablename__ = "budget_line_items"
    
    line_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey('project_budgets.budget_id', ondelete='CASCADE'))
    item_name = Column(String(255), nullable=False)
    description = Column(Text)
    quantity = Column(DECIMAL(10, 2))
    unit_of_measure = Column(String(50))
    unit_cost = Column(DECIMAL(15, 2))
    estimated_amount = Column(DECIMAL(15, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    budget = relationship("ProjectBudget", back_populates="line_items")

class Vendor(Base):
    __tablename__ = "vendors"
    
    vendor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_name = Column(String(255), nullable=False)
    vendor_type = Column(String(100))
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    tax_id = Column(String(50))
    license_number = Column(String(100))
    insurance_expiry = Column(Date)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Expense(Base):
    __tablename__ = "expenses"
    
    expense_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'))
    budget_id = Column(UUID(as_uuid=True), ForeignKey('project_budgets.budget_id'))
    line_item_id = Column(UUID(as_uuid=True), ForeignKey('budget_line_items.line_item_id'))
    phase_id = Column(UUID(as_uuid=True), ForeignKey('project_phases.phase_id'))
    vendor_id = Column(UUID(as_uuid=True), ForeignKey('vendors.vendor_id'))
    expense_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    payment_method = Column(String(50))
    invoice_number = Column(String(100))
    payment_status = Column(String(50), default='pending')
    payment_date = Column(Date)
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="expenses")

class Document(Base):
    __tablename__ = "documents"
    
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'))
    phase_id = Column(UUID(as_uuid=True), ForeignKey('project_phases.phase_id'))
    milestone_id = Column(UUID(as_uuid=True), ForeignKey('milestones.milestone_id'))
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(100))
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))
    version = Column(Integer, default=1)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    description = Column(Text)
    tags = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"
    
    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.project_id', ondelete='CASCADE'))
    phase_id = Column(UUID(as_uuid=True), ForeignKey('project_phases.phase_id'))
    milestone_id = Column(UUID(as_uuid=True), ForeignKey('milestones.milestone_id'))
    task_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='todo')
    priority = Column(String(20), default='medium')
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    due_date = Column(Date)
    completed_date = Column(Date)
    estimated_hours = Column(DECIMAL(6, 2))
    actual_hours = Column(DECIMAL(6, 2))
    dependencies = Column(Text)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
