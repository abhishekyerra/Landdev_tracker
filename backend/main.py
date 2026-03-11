"""
Land Development Project Tracker - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, date
from typing import List, Optional
from decimal import Decimal
from io import BytesIO
import os
import logging
import uuid
from urllib.parse import quote
import re

logger = logging.getLogger(__name__)

from models import User, Project, ProjectPhase, Task
from database import engine, SessionLocal, Base
from auth import create_access_token, verify_password, get_password_hash, get_current_user
from weather_service import weather_service
from ai_agent import ai_agent
from rel_gpt import rel_gpt_client
from storage_service import storage_service
import models
import schemas



# Create database tables
Base.metadata.create_all(bind=engine)

def to_uuid(value: str) -> uuid.UUID:
    """Convert string to UUID, raising 400 if invalid."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {value}")

app = FastAPI(
    title="Land Development Tracker API",
    description="API for tracking land development projects, phases, milestones, and budgets",
    version="1.0.0"
)


class ManualTaskCreateRequest(BaseModel):
    task_name: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None


class ManualTaskBulkCreateRequest(BaseModel):
    tasks: List[ManualTaskCreateRequest]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/api/auth/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint - returns JWT token"""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current logged-in user information"""
    return current_user

# ============================================
# PROJECT ENDPOINTS
# ============================================

@app.post("/api/projects", response_model=schemas.ProjectResponse)
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new project"""
    db_project = models.Project(**project.dict(), created_by=current_user.user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/api/projects", response_model=List[schemas.ProjectResponse])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all projects with optional filtering"""
    query = db.query(models.Project)
    if status:
        query = query.filter(models.Project.status == status)
    projects = query.offset(skip).limit(limit).all()
    return projects

@app.get("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get specific project by ID"""
    project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(
    project_id: str,
    project: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update project details"""
    db_project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in project.dict(exclude_unset=True).items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a project"""
    db_project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted successfully"}

# ============================================
# PROJECT PHASE ENDPOINTS
# ============================================

@app.post("/api/projects/{project_id}/phases", response_model=schemas.PhaseResponse)
async def create_phase(
    project_id: str,
    phase: schemas.PhaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new phase for a project"""
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_phase = models.ProjectPhase(**phase.dict(), project_id=to_uuid(project_id))
    db.add(db_phase)
    db.commit()
    db.refresh(db_phase)
    return db_phase

@app.get("/api/projects/{project_id}/phases", response_model=List[schemas.PhaseResponse])
async def get_project_phases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all phases for a project"""
    phases = db.query(models.ProjectPhase)\
        .filter(models.ProjectPhase.project_id == to_uuid(project_id))\
        .order_by(models.ProjectPhase.phase_order)\
        .all()
    return phases


@app.post("/api/projects/{project_id}/plan/two-phase-generate", response_model=schemas.TwoPhasePlanResponse)
async def generate_two_phase_plan(
    project_id: str,
    payload: schemas.TwoPhasePlanRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate/update two-phase delivery plan:
    Phase I includes common site work + first phase lot delivery.
    Phase II closes remaining lots and developer exit.
    """
    project_uuid = to_uuid(project_id)
    project = db.query(models.Project).filter(models.Project.project_id == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    phase1_share = min(0.8, max(0.55, (payload.phase1_lots / payload.total_lots) + 0.15))
    phase1_budget = (payload.total_budget * Decimal(str(phase1_share))).quantize(Decimal("0.01"))
    phase2_budget = (payload.total_budget - phase1_budget).quantize(Decimal("0.01"))

    total_days = 450
    phase1_days = int(total_days * 0.63)
    phase2_days = total_days - phase1_days
    phase1_start = payload.start_date
    phase1_end = phase1_start + timedelta(days=phase1_days)
    phase2_start = phase1_end + timedelta(days=1)
    phase2_end = phase2_start + timedelta(days=phase2_days)

    phase1_name = f"Phase I - Common Site Work + First {payload.phase1_lots} Lots"
    phase2_name = "Phase II - Remaining Lots Closeout + Developer Exit"

    phase1 = db.query(models.ProjectPhase).filter(
        models.ProjectPhase.project_id == project_uuid,
        models.ProjectPhase.phase_order == 1,
    ).first()
    if not phase1:
        phase1 = models.ProjectPhase(
            project_id=project_uuid,
            phase_name=phase1_name,
            phase_order=1,
            description="Common site work, utilities, roads, and first lot delivery/close.",
            status="in_progress",
            planned_start_date=phase1_start,
            planned_end_date=phase1_end,
            completion_percentage=0,
        )
        db.add(phase1)
        db.flush()
    else:
        phase1.phase_name = phase1_name
        phase1.description = "Common site work, utilities, roads, and first lot delivery/close."
        phase1.planned_start_date = phase1_start
        phase1.planned_end_date = phase1_end

    phase2 = db.query(models.ProjectPhase).filter(
        models.ProjectPhase.project_id == project_uuid,
        models.ProjectPhase.phase_order == 2,
    ).first()
    if not phase2:
        phase2 = models.ProjectPhase(
            project_id=project_uuid,
            phase_name=phase2_name,
            phase_order=2,
            description="Remaining lot delivery, closeout, and developer exit.",
            status="not_started",
            planned_start_date=phase2_start,
            planned_end_date=phase2_end,
            completion_percentage=0,
        )
        db.add(phase2)
        db.flush()
    else:
        phase2.phase_name = phase2_name
        phase2.description = "Remaining lot delivery, closeout, and developer exit."
        phase2.planned_start_date = phase2_start
        phase2.planned_end_date = phase2_end

    # Upsert high-level budget buckets by phase.
    for phase_obj, budget_name, amount in [
        (phase1, f"{phase1_name} Budget", phase1_budget),
        (phase2, f"{phase2_name} Budget", phase2_budget),
    ]:
        existing_budget = db.query(models.ProjectBudget).filter(
            models.ProjectBudget.project_id == project_uuid,
            models.ProjectBudget.phase_id == phase_obj.phase_id,
            models.ProjectBudget.budget_name == budget_name,
        ).first()
        if not existing_budget:
            db.add(
                models.ProjectBudget(
                    project_id=project_uuid,
                    phase_id=phase_obj.phase_id,
                    budget_name=budget_name,
                    budgeted_amount=amount,
                    contingency_percentage=(payload.contingency_rate * Decimal("100")),
                    notes="Auto-generated from Two-Phase Plan Builder",
                )
            )
        else:
            existing_budget.budgeted_amount = amount
            existing_budget.contingency_percentage = payload.contingency_rate * Decimal("100")

    phase1_tasks, phase2_tasks = _generate_two_phase_task_templates(
        start_date=phase1_start, phase1_end=phase1_end, phase2_end=phase2_end
    )
    tasks_created = 0

    for phase_obj, task_templates, phase_start in [
        (phase1, phase1_tasks, phase1_start),
        (phase2, phase2_tasks, phase2_start),
    ]:
        for task in task_templates:
            exists = db.execute(text("""
                SELECT task_id FROM tasks
                WHERE project_id = :project_id
                  AND phase_id = :phase_id
                  AND LOWER(task_name) = LOWER(:task_name)
                LIMIT 1
            """), {
                "project_id": str(project_uuid),
                "phase_id": str(phase_obj.phase_id),
                "task_name": task["task_name"],
            }).fetchone()
            if exists:
                continue

            due_date = phase_start + timedelta(days=max(1, int(task["offset_days"])))
            db.add(
                models.Task(
                    project_id=project_uuid,
                    phase_id=phase_obj.phase_id,
                    task_name=task["task_name"],
                    description=f"Auto-generated by plan builder for {phase_obj.phase_name}",
                    status="todo",
                    priority=task["priority"],
                    estimated_hours=Decimal(str(task["estimated_hours"])),
                    due_date=due_date,
                    created_by=current_user.user_id,
                )
            )
            tasks_created += 1

    _recalculate_phase_completion(db, str(phase1.phase_id))
    _recalculate_phase_completion(db, str(phase2.phase_id))

    context_payload = {
        "project": project.project_name,
        "start_date": str(payload.start_date),
        "total_budget": float(payload.total_budget),
        "phase1": {"name": phase1_name, "lots": payload.phase1_lots, "budget": float(phase1_budget), "start": str(phase1_start), "end": str(phase1_end)},
        "phase2": {"name": phase2_name, "lots": payload.total_lots - payload.phase1_lots, "budget": float(phase2_budget), "start": str(phase2_start), "end": str(phase2_end)},
        "instruction": payload.ai_instruction or "",
    }

    agent_summary = {
        "cost_agent": _call_specialized_agent(
            "cost",
            "You are a construction cost estimator agent. Return concise JSON with cost risks and refinement suggestions.",
            context_payload,
        ),
        "schedule_agent": _call_specialized_agent(
            "schedule",
            "You are a construction schedule optimizer agent. Return concise JSON with milestone and sequencing recommendations.",
            context_payload,
        ),
        "resource_agent": _call_specialized_agent(
            "resource",
            "You are a field operations resource agent. Return concise JSON with crew size and equipment recommendations by phase.",
            context_payload,
        ),
        "risk_agent": _call_specialized_agent(
            "risk",
            "You are a development risk agent. Return concise JSON with top risks and mitigations.",
            context_payload,
        ),
        "task_agent": _call_specialized_agent(
            "task",
            "You are a task planning agent. Return concise JSON with missing tasks to consider by phase.",
            context_payload,
        ),
    }

    db.commit()

    return schemas.TwoPhasePlanResponse(
        project_id=project_uuid,
        start_date=payload.start_date,
        total_budget=payload.total_budget,
        phase1_budget=phase1_budget,
        phase2_budget=phase2_budget,
        phase1_start=phase1_start,
        phase1_end=phase1_end,
        phase2_start=phase2_start,
        phase2_end=phase2_end,
        tasks_created=tasks_created,
        ai_agent_summary=agent_summary,
    )

@app.put("/api/phases/{phase_id}", response_model=schemas.PhaseResponse)
async def update_phase(
    phase_id: str,
    phase: schemas.PhaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update phase details"""
    db_phase = db.query(models.ProjectPhase).filter(models.ProjectPhase.phase_id == to_uuid(phase_id)).first()
    if not db_phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    for key, value in phase.dict(exclude_unset=True).items():
        setattr(db_phase, key, value)
    
    db.commit()
    db.refresh(db_phase)
    return db_phase

# ============================================
# MILESTONE ENDPOINTS
# ============================================

@app.post("/api/phases/{phase_id}/milestones", response_model=schemas.MilestoneResponse)
async def create_milestone(
    phase_id: str,
    milestone: schemas.MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a milestone for a phase"""
    # Verify phase exists and get project_id
    phase = db.query(models.ProjectPhase).filter(models.ProjectPhase.phase_id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    db_milestone = models.Milestone(
        **milestone.dict(),
        phase_id=phase_id,
        project_id=phase.project_id
    )
    db.add(db_milestone)
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

@app.get("/api/phases/{phase_id}/milestones", response_model=List[schemas.MilestoneResponse])
async def get_phase_milestones(
    phase_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all milestones for a phase"""
    milestones = db.query(models.Milestone)\
        .filter(models.Milestone.phase_id == phase_id)\
        .all()
    return milestones

@app.put("/api/milestones/{milestone_id}", response_model=schemas.MilestoneResponse)
async def update_milestone(
    milestone_id: str,
    milestone: schemas.MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update milestone"""
    db_milestone = db.query(models.Milestone).filter(models.Milestone.milestone_id == milestone_id).first()
    if not db_milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    for key, value in milestone.dict(exclude_unset=True).items():
        setattr(db_milestone, key, value)
    
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

# ============================================
# BUDGET ENDPOINTS
# ============================================

@app.post("/api/projects/{project_id}/budgets", response_model=schemas.BudgetResponse)
async def create_budget(
    project_id: str,
    budget: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create budget for project"""
    project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_budget = models.ProjectBudget(**budget.dict(), project_id=to_uuid(project_id))
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.get("/api/projects/{project_id}/budgets", response_model=List[schemas.BudgetResponse])
async def get_project_budgets(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all budgets for a project"""
    budgets = db.query(models.ProjectBudget)\
        .filter(models.ProjectBudget.project_id == to_uuid(project_id))\
        .all()
    return budgets

@app.get("/api/projects/{project_id}/budget-summary")
async def get_budget_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get budget summary for a project"""
    summary = db.execute(text(
        """
        SELECT * FROM v_project_budget_summary 
        WHERE project_id = :project_id
        """
    ),
        {"project_id": project_id}
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": summary.project_id,
        "project_name": summary.project_name,
        "total_budgeted": float(summary.total_budgeted),
        "total_spent": float(summary.total_spent),
        "remaining_budget": float(summary.remaining_budget),
        "budget_utilization_percentage": float(summary.budget_utilization_percentage)
    }

# ============================================
# EXPENSE ENDPOINTS
# ============================================

@app.post("/api/projects/{project_id}/expenses", response_model=schemas.ExpenseResponse)
async def create_expense(
    project_id: str,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record a new expense"""
    project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    expense_data = expense.dict()
    expense_data["payment_status"] = _normalize_payment_status(expense_data.get("payment_status"))
    if expense_data["payment_status"] == "paid" and not expense_data.get("payment_date"):
        expense_data["payment_date"] = datetime.utcnow().date()

    db_expense = models.Expense(**expense_data, project_id=to_uuid(project_id))
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/api/projects/{project_id}/expenses", response_model=List[schemas.ExpenseResponse])
async def get_project_expenses(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all expenses for a project"""
    expenses = db.query(models.Expense)\
        .filter(models.Expense.project_id == to_uuid(project_id))\
        .order_by(models.Expense.expense_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return expenses


@app.patch("/api/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
async def update_expense(
    expense_id: str,
    expense_update: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update expense fields (including payment status)."""
    expense = db.query(models.Expense).filter(models.Expense.expense_id == to_uuid(expense_id)).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = expense_update.dict(exclude_unset=True)
    if "payment_status" in update_data:
        update_data["payment_status"] = _normalize_payment_status(update_data.get("payment_status"))
        if update_data["payment_status"] == "paid" and not update_data.get("payment_date"):
            update_data["payment_date"] = datetime.utcnow().date()

    for key, value in update_data.items():
        if hasattr(expense, key):
            setattr(expense, key, value)

    db.commit()
    db.refresh(expense)
    return expense

# ============================================
# DASHBOARD ENDPOINTS
# ============================================

@app.get("/api/dashboard/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get overall dashboard statistics"""
    result = db.execute(
        """
        SELECT 
            COUNT(DISTINCT project_id) as total_projects,
            COUNT(DISTINCT CASE WHEN status = 'in_progress' THEN project_id END) as active_projects,
            COUNT(DISTINCT CASE WHEN status = 'completed' THEN project_id END) as completed_projects,
            COALESCE(SUM((SELECT total_budgeted FROM v_project_budget_summary WHERE project_id = projects.project_id)), 0) as total_budget_all_projects,
            COALESCE(SUM((SELECT total_spent FROM v_project_budget_summary WHERE project_id = projects.project_id)), 0) as total_spent_all_projects
        FROM projects
        """
    ).first()
    
    return {
        "total_projects": result.total_projects,
        "active_projects": result.active_projects,
        "completed_projects": result.completed_projects,
        "total_budget_all_projects": float(result.total_budget_all_projects) if result.total_budget_all_projects else 0,
        "total_spent_all_projects": float(result.total_spent_all_projects) if result.total_spent_all_projects else 0
    }

@app.get("/api/dashboard/projects")
async def get_dashboard_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get project dashboard view"""
    projects = db.execute("SELECT * FROM v_project_dashboard ORDER BY project_name").fetchall()
    
    return [
        {
            "project_id": p.project_id,
            "project_name": p.project_name,
            "project_code": p.project_code,
            "status": p.status,
            "start_date": p.start_date,
            "target_completion_date": p.target_completion_date,
            "schedule_status": p.schedule_status,
            "total_budgeted": float(p.total_budgeted) if p.total_budgeted else 0,
            "total_spent": float(p.total_spent) if p.total_spent else 0,
            "remaining_budget": float(p.remaining_budget) if p.remaining_budget else 0,
            "budget_utilization_percentage": float(p.budget_utilization_percentage) if p.budget_utilization_percentage else 0,
            "overall_completion_percentage": float(p.overall_completion_percentage) if p.overall_completion_percentage else 0,
            "total_phases": p.total_phases,
            "completed_phases": p.completed_phases,
            "overdue_milestones": p.overdue_milestones
        }
        for p in projects
    ]

# ============================================
# TASK ENDPOINTS
# ============================================

@app.get("/api/phases/{phase_id}/tasks")
async def get_phase_tasks(
    phase_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for a specific phase"""
    tasks = db.query(models.Task).filter(models.Task.phase_id == phase_id).order_by(models.Task.due_date).all()
    return tasks


@app.post("/api/phases/{phase_id}/tasks")
async def create_phase_task(
    phase_id: str,
    payload: ManualTaskCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create one manual task for a phase."""
    phase = db.query(models.ProjectPhase).filter(models.ProjectPhase.phase_id == to_uuid(phase_id)).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    task = models.Task(
        phase_id=phase.phase_id,
        project_id=phase.project_id,
        task_name=payload.task_name.strip()[:255],
        description=(payload.description or "").strip()[:1800] or None,
        status=(payload.status or "todo"),
        priority=(payload.priority or "medium"),
        due_date=payload.due_date,
        estimated_hours=Decimal(str(payload.estimated_hours)) if payload.estimated_hours is not None else None,
        completion_percentage=min(100, max(0, int(payload.completion_percentage))) if payload.completion_percentage is not None else None,
        notes=(payload.notes or "").strip()[:1800] or None,
        created_by=current_user.user_id,
    )
    if task.completion_percentage is None:
        if task.status == "completed":
            task.completion_percentage = 100
        elif task.status == "in_progress":
            task.completion_percentage = 50
        else:
            task.completion_percentage = 0
    if task.status == "completed" and not task.completed_date:
        task.completed_date = datetime.utcnow().date()

    db.add(task)
    db.flush()
    _recalculate_phase_completion(db, str(phase.phase_id))
    db.commit()
    db.refresh(task)
    return task


@app.post("/api/phases/{phase_id}/tasks/bulk")
async def create_phase_tasks_bulk(
    phase_id: str,
    payload: ManualTaskBulkCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk-create manual tasks for a phase."""
    phase = db.query(models.ProjectPhase).filter(models.ProjectPhase.phase_id == to_uuid(phase_id)).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    if not payload.tasks:
        raise HTTPException(status_code=400, detail="No tasks provided")

    created = []
    for item in payload.tasks[:300]:
        name = (item.task_name or "").strip()
        if not name:
            continue
        task = models.Task(
            phase_id=phase.phase_id,
            project_id=phase.project_id,
            task_name=name[:255],
            description=(item.description or "").strip()[:1800] or None,
            status=(item.status or "todo"),
            priority=(item.priority or "medium"),
            due_date=item.due_date,
            estimated_hours=Decimal(str(item.estimated_hours)) if item.estimated_hours is not None else None,
            completion_percentage=min(100, max(0, int(item.completion_percentage))) if item.completion_percentage is not None else None,
            notes=(item.notes or "").strip()[:1800] or None,
            created_by=current_user.user_id,
        )
        if task.completion_percentage is None:
            if task.status == "completed":
                task.completion_percentage = 100
            elif task.status == "in_progress":
                task.completion_percentage = 50
            else:
                task.completion_percentage = 0
        if task.status == "completed" and not task.completed_date:
            task.completed_date = datetime.utcnow().date()
        db.add(task)
        created.append(task)

    db.flush()
    _recalculate_phase_completion(db, str(phase.phase_id))
    db.commit()
    return {"status": "success", "created_count": len(created)}


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_update: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a task (e.g., status, completion)"""
    task = db.query(models.Task).filter(models.Task.task_id == to_uuid(task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    for key, value in task_update.items():
        if hasattr(task, key):
            setattr(task, key, value)

    if "completion_percentage" in task_update:
        try:
            task.completion_percentage = min(100, max(0, int(task.completion_percentage or 0)))
        except Exception:
            task.completion_percentage = 0

    if task.completion_percentage is not None:
        if task.completion_percentage >= 100:
            task.status = "completed"
        elif task.completion_percentage > 0 and task.status in {"todo", "cancelled"}:
            task.status = "in_progress"

    if task.status == "completed":
        task.completion_percentage = 100
        if not task.completed_date:
            task.completed_date = datetime.utcnow().date()
    elif task.status in {"in_progress", "review"}:
        if task.completion_percentage is None:
            task.completion_percentage = 50
        task.completed_date = None
    else:
        if task.completion_percentage is None:
            task.completion_percentage = 0
        task.completed_date = None

    task.updated_at = datetime.utcnow()
    _recalculate_phase_completion(db, str(task.phase_id))
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task."""
    task = db.query(models.Task).filter(models.Task.task_id == to_uuid(task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    phase_id = str(task.phase_id)
    db.delete(task)
    db.flush()
    _recalculate_phase_completion(db, phase_id)
    db.commit()
    return {"status": "success", "message": "Task deleted"}


@app.post("/api/tasks/{task_id}/delete")
async def delete_task_post(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fallback delete endpoint for clients/environments that block HTTP DELETE."""
    return await delete_task(task_id=task_id, current_user=current_user, db=db)

# ============================================
# WEATHER ENDPOINTS
# ============================================

@app.get("/api/weather/columbia-tn")
async def get_weather(current_user: models.User = Depends(get_current_user)):
    """Get weather for Columbia, TN with work recommendations"""
    try:
        weather_data = weather_service.get_weather_summary()
        return weather_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")

@app.get("/api/weather/current")
async def get_current_weather(current_user: models.User = Depends(get_current_user)):
    """Get current weather conditions only"""
    try:
        current = weather_service.get_current_weather()
        if not current:
            raise HTTPException(status_code=503, detail="Weather service unavailable")
        return current
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")

@app.get("/api/weather/forecast")
async def get_forecast(current_user: models.User = Depends(get_current_user)):
    """Get 7-day forecast"""
    try:
        forecast = weather_service.get_forecast()
        if not forecast:
            raise HTTPException(status_code=503, detail="Weather service unavailable")
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")

# ============================================
# AI AGENT ENDPOINTS
# ============================================

@app.get("/api/ai/recommendations/{project_id}")
async def get_ai_recommendations(
    project_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered recommendations for project management
    Analyzes current status, weather, budget, and timeline
    """
    try:
        # Get project data
        project = db.query(models.Project).filter(models.Project.project_id == to_uuid(project_id)).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get phases
        phases = db.query(models.ProjectPhase).filter(
            models.ProjectPhase.project_id == to_uuid(project_id)
        ).order_by(models.ProjectPhase.phase_order).all()
        
        # Get current phase
        current_phase = next((p for p in phases if p.status == 'in_progress'), phases[0] if phases else None)
        
        # Get tasks for current phase
        tasks = []
        if current_phase:
            tasks = db.query(models.Task).filter(
                models.Task.phase_id == current_phase.phase_id
            ).order_by(models.Task.due_date).all()
        
        # Get budget summary
        budget_query = db.execute(text("""
            SELECT 
                COALESCE(SUM(budgeted_amount), 0) as total_budgeted,
                COALESCE(SUM(spent), 0) as total_spent,
                COALESCE(SUM(budgeted_amount) - SUM(spent), 0) as remaining_budget,
                CASE 
                    WHEN SUM(budgeted_amount) > 0 
                    THEN (SUM(spent) / SUM(budgeted_amount) * 100)
                    ELSE 0 
                END as budget_utilization_percentage
            FROM (
                SELECT 
                    pb.budgeted_amount,
                    COALESCE(SUM(e.amount), 0) as spent
                FROM project_budgets pb
                LEFT JOIN expenses e ON pb.budget_id = e.budget_id
                WHERE pb.project_id = :project_id
                GROUP BY pb.budget_id, pb.budgeted_amount
            ) sub
        """), {"project_id": project_id})
        
        budget_row = budget_query.fetchone()
        budget_summary = {
            'total_budgeted': float(budget_row[0]) if budget_row else 0,
            'total_spent': float(budget_row[1]) if budget_row else 0,
            'remaining_budget': float(budget_row[2]) if budget_row else 0,
            'budget_utilization_percentage': float(budget_row[3]) if budget_row else 0
        }
        
        # Get weather data
        weather_data = weather_service.get_weather_summary()
        
        # Convert SQLAlchemy objects to dicts
        project_dict = {
            'project_id': str(project.project_id),
            'project_name': project.project_name,
            'project_code': project.project_code,
            'location_city': project.location_city,
            'location_state': project.location_state,
            'total_acres': float(project.total_acres) if project.total_acres else 0,
            'description': project.description,
            'status': project.status
        }
        
        phases_list = [{
            'phase_id': str(p.phase_id),
            'phase_name': p.phase_name,
            'status': p.status,
            'completion_percentage': p.completion_percentage,
            'planned_end_date': str(p.planned_end_date) if p.planned_end_date else None
        } for p in phases]
        
        tasks_list = [{
            'task_id': str(t.task_id),
            'task_name': t.task_name,
            'status': t.status,
            'priority': t.priority,
            'due_date': str(t.due_date) if t.due_date else None,
            'estimated_hours': t.estimated_hours
        } for t in tasks]
        
        # Get AI recommendations
        recommendations = ai_agent.get_project_recommendations(
            project_data=project_dict,
            phases=phases_list,
            current_phase_tasks=tasks_list,
            weather_data=weather_data,
            budget_summary=budget_summary
        )

        # Normalize advisor output with resource/equipment/budget guidance.
        priority_tasks = recommendations.get("priority_tasks") or recommendations.get("recommended_tasks") or []
        if "resource_plan" not in recommendations:
            upcoming_budget = 0.0
            for t in priority_tasks[:5]:
                upcoming_budget += _estimate_budget_for_task(
                    t.get("task_name", "task"),
                    t.get("priority", "medium"),
                    float(t.get("estimated_hours") or 12),
                )
            recommendations["resource_plan"] = {
                "recommended_crew_size": "6-10 field crew + 1 PM",
                "next_equipment_needed": [
                    "Excavator",
                    "Skid steer",
                    "Compactor",
                    "Survey kit",
                ],
                "upcoming_tasks_budget_estimate": f"${upcoming_budget:,.0f} (approx.)",
            }
        if "upcoming_tasks" not in recommendations:
            recommendations["upcoming_tasks"] = [
                {
                    "task_name": t.get("task_name"),
                    "target_phase": current_phase.phase_name if current_phase else "Current phase",
                    "budget_estimate": f"${_estimate_budget_for_task(t.get('task_name', ''), t.get('priority', 'medium'), float(t.get('estimated_hours') or 12)):,.0f}",
                }
                for t in priority_tasks[:5]
            ]
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


def _format_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


class AnalyzeSelectedRequest(BaseModel):
    document_ids: List[str]
    ai_instruction: Optional[str] = None


class AnalyzeQueryRequest(BaseModel):
    filename_contains: Optional[str] = None
    uploaded_from: Optional[date] = None
    uploaded_to: Optional[date] = None
    ai_instruction: Optional[str] = None
    limit: int = 100


class InvoiceReviewRequest(BaseModel):
    document_ids: List[str]
    vendor_name: Optional[str] = None
    auto_record_expense: bool = False


class RebuildTasksFromFilesRequest(BaseModel):
    ai_instruction: Optional[str] = None
    clear_analysis_history: bool = True


def _recalculate_phase_completion(db: Session, phase_id: str) -> int:
    rows = db.execute(text("""
        SELECT status, priority, estimated_hours, actual_hours, completion_percentage
        FROM tasks
        WHERE phase_id = :phase_id
    """), {"phase_id": phase_id}).fetchall()

    if not rows:
        completion = 0
    else:
        priority_weight = {
            "critical": 1.6,
            "high": 1.3,
            "medium": 1.0,
            "low": 0.8,
        }
        status_progress = {
            "completed": 1.0,
            "review": 0.85,
            "in_progress": None,  # computed from actual vs estimated
            "blocked": 0.2,
            "cancelled": 0.0,
            "todo": 0.0,
        }

        total_weight = 0.0
        weighted_progress = 0.0
        for status, priority, estimated_hours, actual_hours, completion_percentage in rows:
            p = (priority or "medium").lower()
            base_weight = priority_weight.get(p, 1.0)
            est = float(estimated_hours or 1.0)
            if est <= 0:
                est = 1.0
            weight = base_weight * max(1.0, est)

            s = (status or "todo").lower()
            if completion_percentage is not None:
                progress = max(0.0, min(float(completion_percentage) / 100.0, 1.0))
            elif s == "in_progress":
                if actual_hours is not None and float(actual_hours or 0) > 0 and est > 0:
                    progress = min(float(actual_hours) / est, 0.9)
                else:
                    progress = 0.5
            else:
                progress = status_progress.get(s, 0.0)

            total_weight += weight
            weighted_progress += weight * progress

        completion = int((weighted_progress / total_weight) * 100) if total_weight > 0 else 0

    db.execute(text("""
        UPDATE project_phases
        SET completion_percentage = :completion, updated_at = NOW()
        WHERE phase_id = :phase_id
    """), {"completion": completion, "phase_id": phase_id})
    return completion


def _estimate_budget_for_task(task_name: str, priority: str, estimated_hours: float) -> float:
    labor_rate = 95.0
    equipment_factor = 1.0
    lowered = task_name.lower()
    if any(k in lowered for k in ["excavate", "grading", "paving", "utility", "storm", "sewer"]):
        equipment_factor = 1.8
    elif any(k in lowered for k in ["permit", "planning", "design", "survey"]):
        equipment_factor = 1.2
    priority_factor = {"critical": 1.25, "high": 1.15, "medium": 1.0, "low": 0.9}.get(priority or "medium", 1.0)
    hours = float(estimated_hours or 12)
    return round(hours * labor_rate * equipment_factor * priority_factor, 2)


def _extract_currency_values(text_blob: str) -> list[float]:
    values = []
    for m in re.findall(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})|\d+(?:\.\d{2}))", text_blob):
        try:
            amount = float(m.replace(",", ""))
            if amount >= 10:
                values.append(amount)
        except Exception:
            continue
    return values


def _normalize_payment_status(value: Optional[str]) -> str:
    normalized = (value or "pending").strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "to_be_paid": "pending",
        "pending": "pending",
        "approved": "approved",
        "paid": "paid",
        "rejected": "rejected",
    }
    return mapping.get(normalized, "pending")


def _auto_mark_paid_invoices(
    db: Session,
    project_id: str,
    text_blob: str,
    source_label: str,
) -> int:
    """
    Heuristically mark invoices as paid when bank/payment evidence appears in
    daily update notes or uploaded documents.
    """
    if not text_blob:
        return 0

    lowered = text_blob.lower()
    payment_keywords = [
        "paid",
        "payment sent",
        "payment made",
        "wire sent",
        "ach posted",
        "transaction posted",
        "bank transaction",
        "check cleared",
        "transfer completed",
    ]
    if not any(k in lowered for k in payment_keywords):
        return 0

    amounts = _extract_currency_values(text_blob)
    project_uuid = to_uuid(project_id)
    candidates = (
        db.query(models.Expense)
        .filter(models.Expense.project_id == project_uuid)
        .filter(models.Expense.payment_status != "paid")
        .all()
    )

    marked = 0
    compact_text = re.sub(r"[^a-z0-9]", "", lowered)
    for exp in candidates:
        invoice_raw = (exp.invoice_number or "").strip().lower()
        invoice_compact = re.sub(r"[^a-z0-9]", "", invoice_raw)

        invoice_match = bool(invoice_raw and invoice_raw in lowered)
        if not invoice_match and invoice_compact:
            invoice_match = invoice_compact in compact_text

        amount_match = False
        try:
            amount = float(exp.amount or 0)
            if amount > 0 and amounts:
                tolerance = max(5.0, amount * 0.01)
                amount_match = any(abs(a - amount) <= tolerance for a in amounts)
        except Exception:
            amount_match = False

        if not (invoice_match or amount_match):
            continue

        exp.payment_status = "paid"
        if not exp.payment_date:
            exp.payment_date = datetime.utcnow().date()
        note_prefix = f"[Auto-paid from {source_label}] "
        if exp.notes:
            if note_prefix not in exp.notes:
                exp.notes = f"{note_prefix}{exp.notes}"[:1800]
        else:
            exp.notes = note_prefix[:1800]
        marked += 1

    return marked


def _keyword_category_guess(source_text: str) -> str:
    lowered = (source_text or "").lower()
    mapping = [
        ("Utilities", ["utility", "water", "sewer", "storm", "drain", "manhole"]),
        ("Sitework", ["grading", "earthwork", "excavat", "paving", "asphalt", "road", "curb"]),
        ("Engineering", ["engineering", "design", "survey", "geotech", "civil"]),
        ("Permits & Fees", ["permit", "approval", "inspection", "impact fee", "application"]),
        ("Materials", ["material", "aggregate", "concrete", "pipe", "stone", "base course"]),
        ("Equipment", ["equipment", "rental", "dozer", "excavator", "loader", "compactor"]),
        ("Labor", ["labor", "crew", "man-hour", "installation services", "field services"]),
    ]
    for category, words in mapping:
        if any(w in lowered for w in words):
            return category
    return "General"


def _infer_phase_from_text(phases: list[models.ProjectPhase], source_text: str) -> Optional[models.ProjectPhase]:
    if not phases:
        return None
    lowered = (source_text or "").lower()
    phase_sorted = sorted(phases, key=lambda p: p.phase_order or 9999)

    if any(k in lowered for k in ["phase ii", "phase 2", "closeout", "final", "handover", "exit"]):
        return phase_sorted[-1]
    if any(k in lowered for k in ["phase i", "phase 1", "grading", "utility", "earthwork", "road", "paving", "storm"]):
        return phase_sorted[0]

    in_progress = next((p for p in phase_sorted if p.status == "in_progress"), None)
    return in_progress or phase_sorted[0]


def _find_or_create_budget_for_category(
    db: Session,
    project_uuid,
    phase_uuid,
    category_name: str,
    invoice_amount: float,
):
    budget = db.query(models.ProjectBudget).filter(
        models.ProjectBudget.project_id == project_uuid,
        models.ProjectBudget.phase_id == phase_uuid if phase_uuid else models.ProjectBudget.phase_id.is_(None),
        models.ProjectBudget.budget_name.ilike(f"%{category_name}%"),
    ).first()
    if budget:
        return budget

    fallback = db.query(models.ProjectBudget).filter(
        models.ProjectBudget.project_id == project_uuid,
        models.ProjectBudget.budget_name.ilike(f"%{category_name}%"),
    ).first()
    if fallback:
        return fallback

    category = db.query(models.BudgetCategory).filter(
        models.BudgetCategory.category_name.ilike(category_name)
    ).first()
    if not category:
        category = models.BudgetCategory(category_name=category_name, is_active=True)
        db.add(category)
        db.flush()

    seeded_amount = max(float(invoice_amount or 0), 1000.0)
    budget = models.ProjectBudget(
        project_id=project_uuid,
        phase_id=phase_uuid,
        category_id=category.category_id,
        budget_name=f"{category_name} - Auto",
        budgeted_amount=Decimal(str(round(seeded_amount * 3, 2))),
        contingency_percentage=Decimal("10.00"),
        notes="Auto-created from AI invoice categorization",
    )
    db.add(budget)
    db.flush()
    return budget


def _ensure_project_phases(db: Session, project_id: str) -> list[dict]:
    """
    Ensure a project has phases so document analysis can map tasks.
    Creates a default two-phase structure when none exists.
    """
    rows = db.execute(text("""
        SELECT phase_id, phase_name, phase_order, description
        FROM project_phases
        WHERE project_id = :project_id
        ORDER BY phase_order
    """), {"project_id": project_id}).fetchall()

    if rows:
        return [
            {"phase_id": str(r[0]), "phase_name": r[1], "phase_order": r[2], "description": r[3]}
            for r in rows
        ]

    defaults = [
        {
            "name": "Phase I - Common Site Work + First Lot Delivery",
            "order": 1,
            "description": "Civil/site work, utilities, roads, inspections, and first lot delivery.",
            "status": "in_progress",
        },
        {
            "name": "Phase II - Remaining Lots Closeout + Exit",
            "order": 2,
            "description": "Remaining lot completion, closeout, final turnover, and developer exit.",
            "status": "not_started",
        },
    ]

    created = []
    for phase in defaults:
        phase_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO project_phases (
                phase_id, project_id, phase_name, phase_order, description, status, completion_percentage, created_at, updated_at
            ) VALUES (
                :phase_id, :project_id, :phase_name, :phase_order, :description, :status, 0, NOW(), NOW()
            )
        """), {
            "phase_id": phase_id,
            "project_id": project_id,
            "phase_name": phase["name"],
            "phase_order": phase["order"],
            "description": phase["description"],
            "status": phase["status"],
        })
        created.append(
            {
                "phase_id": phase_id,
                "phase_name": phase["name"],
                "phase_order": phase["order"],
                "description": phase["description"],
            }
        )
    return created


def _call_specialized_agent(agent_name: str, system_prompt: str, payload: dict) -> dict:
    """Call one Rel GPT agent persona and return JSON output."""
    if not rel_gpt_client.enabled:
        return {}
    result = rel_gpt_client.generate_json(
        user_prompt=json.dumps(payload),
        system_prompt=system_prompt,
        max_tokens=1200,
        temperature=0.2,
    )
    if isinstance(result, dict):
        return result
    return {}


def _generate_two_phase_task_templates(start_date: date, phase1_end: date, phase2_end: date) -> tuple[list[dict], list[dict]]:
    """Baseline two-phase task templates with due dates."""
    phase1_tasks = [
        {"task_name": "Finalize common site work mobilization plan", "priority": "high", "estimated_hours": 24, "offset_days": 5},
        {"task_name": "Complete grading package for common site areas", "priority": "critical", "estimated_hours": 120, "offset_days": 20},
        {"task_name": "Install primary utilities backbone (water, sewer, storm)", "priority": "critical", "estimated_hours": 220, "offset_days": 45},
        {"task_name": "Construct internal roads for first 30 lots", "priority": "critical", "estimated_hours": 180, "offset_days": 75},
        {"task_name": "Coordinate inspections and approvals for first 30 lots", "priority": "high", "estimated_hours": 80, "offset_days": 105},
        {"task_name": "Close first 30 lots with builder", "priority": "critical", "estimated_hours": 40, "offset_days": (phase1_end - start_date).days - 5},
    ]
    phase2_tasks = [
        {"task_name": "Prepare remaining lots for transfer and closeout", "priority": "high", "estimated_hours": 90, "offset_days": 20},
        {"task_name": "Finish outstanding infrastructure punch list", "priority": "high", "estimated_hours": 100, "offset_days": 40},
        {"task_name": "Complete final permitting and jurisdiction closeouts", "priority": "high", "estimated_hours": 72, "offset_days": 60},
        {"task_name": "Execute final lot closings and developer exit prep", "priority": "critical", "estimated_hours": 64, "offset_days": (phase2_end - phase1_end).days - 15},
        {"task_name": "Finalize developer exit and handover package", "priority": "critical", "estimated_hours": 48, "offset_days": (phase2_end - phase1_end).days - 5},
    ]
    return phase1_tasks, phase2_tasks


def _generate_analysis_insight(title: str, payload: dict) -> Optional[str]:
    """Optional Rel GPT narrative insight."""
    if not rel_gpt_client.enabled:
        return None

    prompt = f"""Provide a concise, practical analysis for this {title}.
Focus on risks, assumptions, and next actions.
Data:
{payload}
"""
    return rel_gpt_client.generate_text(
        user_prompt=prompt,
        max_tokens=300,
        temperature=0.2,
    )


@app.post(
    "/api/analysis/construction-cost-estimate",
    response_model=schemas.ConstructionCostEstimateResponse,
)
async def estimate_construction_cost(
    request: schemas.ConstructionCostEstimateRequest,
    current_user: models.User = Depends(get_current_user),
):
    hard_cost_total = sum(
        (item.quantity * item.unit_cost for item in request.hard_cost_items), start=Decimal("0")
    )
    soft_cost_total = hard_cost_total * request.soft_cost_rate
    contingency_total = hard_cost_total * request.contingency_rate
    financing_total = (hard_cost_total + soft_cost_total) * request.financing_rate
    total_project_cost = hard_cost_total + soft_cost_total + contingency_total + financing_total

    payload = {
        "hard_cost_total": float(_format_money(hard_cost_total)),
        "soft_cost_rate": float(request.soft_cost_rate),
        "contingency_rate": float(request.contingency_rate),
        "financing_rate": float(request.financing_rate),
        "total_project_cost": float(_format_money(total_project_cost)),
    }

    return schemas.ConstructionCostEstimateResponse(
        hard_cost_total=_format_money(hard_cost_total),
        soft_cost_total=_format_money(soft_cost_total),
        contingency_total=_format_money(contingency_total),
        financing_total=_format_money(financing_total),
        total_project_cost=_format_money(total_project_cost),
        insight=_generate_analysis_insight("construction cost estimate", payload),
    )


@app.post(
    "/api/analysis/investment-return-predictor",
    response_model=schemas.InvestmentReturnResponse,
)
async def predict_investment_return(
    request: schemas.InvestmentReturnRequest,
    current_user: models.User = Depends(get_current_user),
):
    total_investment = request.land_price + request.development_cost
    annual_cash_flow = request.projected_annual_revenue - request.projected_annual_operating_cost

    terminal_value = request.projected_sale_price if request.projected_sale_price is not None else Decimal("0")
    projected_profit = (annual_cash_flow * request.holding_years) + terminal_value - total_investment
    roi_percent = (projected_profit / total_investment * Decimal("100")) if total_investment > 0 else Decimal("0")

    discount = Decimal("1") + request.discount_rate
    npv = -total_investment
    for year in range(1, request.holding_years + 1):
        npv += annual_cash_flow / (discount ** year)
    if terminal_value > 0:
        npv += terminal_value / (discount ** request.holding_years)

    payback_years = None
    if annual_cash_flow > 0:
        payback_years = total_investment / annual_cash_flow

    payload = {
        "total_investment": float(_format_money(total_investment)),
        "annual_cash_flow": float(_format_money(annual_cash_flow)),
        "projected_profit": float(_format_money(projected_profit)),
        "roi_percent": float(_format_money(roi_percent)),
        "npv": float(_format_money(npv)),
        "holding_years": request.holding_years,
    }

    return schemas.InvestmentReturnResponse(
        total_investment=_format_money(total_investment),
        projected_profit=_format_money(projected_profit),
        roi_percent=_format_money(roi_percent),
        annual_cash_flow=_format_money(annual_cash_flow),
        npv=_format_money(npv),
        payback_years=_format_money(payback_years) if payback_years is not None else None,
        insight=_generate_analysis_insight("investment return forecast", payload),
    )


@app.post("/api/analysis/land-feasibility-agent", response_model=schemas.LandFeasibilityResponse)
async def evaluate_land_feasibility(
    request: schemas.LandFeasibilityRequest,
    current_user: models.User = Depends(get_current_user),
):
    score = 100
    blockers = []
    recommendations = []

    if not request.zoning_permitted:
        score -= 35
        blockers.append("Current zoning does not permit the intended development.")
        recommendations.append("Pursue rezoning/variance before major pre-development spend.")
    if not request.utility_access:
        score -= 20
        blockers.append("Utility access is unavailable or uncertain.")
        recommendations.append("Confirm extension costs and schedule with utility providers.")
    if not request.road_access:
        score -= 15
        blockers.append("Road access constraints may delay permitting and construction.")
        recommendations.append("Secure legal access and verify frontage requirements.")
    if request.flood_zone:
        score -= 15
        blockers.append("Flood zone exposure can increase capex and insurance costs.")
        recommendations.append("Commission floodplain and drainage studies before final underwriting.")

    slope = float(request.slope_percent)
    if slope > 15:
        score -= 15
        recommendations.append("Steep slope likely increases grading and retaining structure costs.")
    elif slope > 8:
        score -= 7
        recommendations.append("Moderate slope requires careful grading and erosion controls.")

    risk_penalty = {"low": 0, "medium": 10, "high": 20}[request.environmental_risk]
    market_adjustment = {"low": -10, "medium": 0, "high": 8}[request.market_strength]
    score = score - risk_penalty + market_adjustment

    roi_gap = request.estimated_roi_percent - request.target_roi_percent
    if roi_gap < 0:
        score -= min(20, int(abs(roi_gap)))
        recommendations.append("Improve deal structure or reduce development costs to hit target ROI.")

    score = max(0, min(100, int(score)))
    if score >= 75:
        classification = "high"
    elif score >= 50:
        classification = "medium"
    else:
        classification = "low"

    payload = {
        "feasibility_score": score,
        "classification": classification,
        "blockers": blockers,
        "estimated_roi_percent": float(request.estimated_roi_percent),
        "target_roi_percent": float(request.target_roi_percent),
        "environmental_risk": request.environmental_risk,
        "market_strength": request.market_strength,
    }

    return schemas.LandFeasibilityResponse(
        feasibility_score=score,
        classification=classification,
        blockers=blockers,
        recommendations=recommendations,
        insight=_generate_analysis_insight("land feasibility", payload),
    )

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
Daily Update Endpoint with AI Processing
Add this code to your main.py file
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import json

# Add this Pydantic model near your other models
class DailyUpdateInput(BaseModel):
    notes: str
    blockers: Optional[str] = None
    weather_impact: Optional[str] = None
    crew_size: Optional[int] = None
    equipment_available: Optional[str] = None

# Add this endpoint to your FastAPI app
@app.post("/api/projects/{project_id}/daily-update")
async def submit_daily_update(
    project_id: str,
    update: DailyUpdateInput,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit daily update and get AI-powered analysis
    - Analyzes contractor notes
    - Updates task/phase progress
    - Generates strategic recommendations based on:
      * Daily progress
      * Weather conditions
      * Resource availability
      * Project timeline
    """
    try:
        # 1. Get project data
        project_uuid = to_uuid(project_id)
        project = db.query(Project).filter(Project.project_id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        phases = db.query(ProjectPhase).filter(ProjectPhase.project_id == project_uuid).all()
        tasks = db.query(Task).join(ProjectPhase).filter(ProjectPhase.project_id == project_uuid).all()
        
        # 2. Get current weather
        try:
            weather_response = await get_weather_for_location("Columbia, TN")
            weather_data = weather_response if weather_response else {}
        except:
            weather_data = {}
        
        # 3. Process with AI (Rel GPT -> OpenAI fallback) and always generate actionable tasks
        active_phase = next((p for p in phases if p.status == 'in_progress'), None)
        active_tasks = [t for t in tasks if t.status in ['in_progress', 'todo']]
        completed_tasks = [t for t in tasks if t.status == 'completed']

        context = f"""You are analyzing a daily construction update for a land development project.

PROJECT: {project.project_name} ({project.project_code})
Location: {project.location_city}, {project.location_state}

DAILY UPDATE FROM CONTRACTOR:
Date: {datetime.now().strftime('%Y-%m-%d')}
Contractor: {getattr(current_user, "first_name", "Unknown")} {getattr(current_user, "last_name", "")}
Notes: {update.notes}
Blockers: {update.blockers or 'None reported'}
Weather Impact: {update.weather_impact or 'None mentioned'}
Crew Size: {update.crew_size or 'Not specified'}
Equipment: {update.equipment_available or 'Not specified'}

CURRENT PROJECT STATUS:
Total Phases: {len(phases)}
Active Phase: {active_phase.phase_name if active_phase else 'None'}
Phase Progress: {active_phase.completion_percentage if active_phase else 0}%
Total Tasks: {len(tasks)}
Completed: {len(completed_tasks)} | In Progress: {len([t for t in tasks if t.status == 'in_progress'])} | Remaining: {len([t for t in tasks if t.status == 'todo'])}

NEXT 5 PRIORITY TASKS:
{chr(10).join([f"- {t.task_name} (Priority: {t.priority}, Due: {t.due_date})" for t in active_tasks[:5]])}

WEATHER FORECAST (Next 3 Days):
{json.dumps(weather_data.get('forecast', [])[:3], indent=2) if weather_data else 'Not available'}

Based on this daily update, provide a comprehensive analysis in the following JSON structure:
{{
  "progress_assessment": "Brief assessment of today's progress",
  "completed_work": ["List of work items that appear to have been completed"],
  "next_actions": ["Specific tasks recommended for tomorrow"],
  "risks": ["Identified risks or concerns"],
  "opportunities": ["Opportunities to accelerate or improve"],
  "resource_recommendations": "Suggestions for crew size, equipment, or materials",
  "weather_strategy": "How to leverage or mitigate weather conditions",
  "timeline_impact": "Assessment of impact on overall project timeline",
  "strategic_guidance": "Overall strategic advice for the next 2-3 days"
}}

Provide ONLY the JSON response, no additional text."""

        ai_analysis = rel_gpt_client.generate_json(
            user_prompt=context,
            max_tokens=2000,
            temperature=0.2,
        )
        if not ai_analysis:
            ai_analysis = {
                "progress_assessment": "Analysis completed with deterministic fallback.",
                "strategic_guidance": "Model output unavailable; generated rule-based micro tasks from daily notes.",
                "next_actions": ["Review generated micro tasks and assign owners/due dates."],
            }

        # 4. Save daily update to database
        db.execute(text("""
            INSERT INTO daily_updates (
                project_id, user_id, update_date, notes, blockers, 
                weather_impact, crew_size, equipment_available, 
                ai_analysis, ai_recommendations
            ) VALUES (
                :project_id, :user_id, :update_date, :notes, :blockers,
                :weather_impact, :crew_size, :equipment_available,
                :ai_analysis, :ai_recommendations
            )
        """), {
            "project_id": project_id,
            "user_id": current_user.user_id,
            "update_date": datetime.now().date(),
            "notes": update.notes,
            "blockers": update.blockers,
            "weather_impact": update.weather_impact,
            "crew_size": update.crew_size,
            "equipment_available": update.equipment_available,
            "ai_analysis": json.dumps(ai_analysis),
            "ai_recommendations": json.dumps(ai_analysis)
        })

        # 5. Auto-update existing tasks based on daily notes.
        notes_lower = update.notes.lower()
        if active_phase:
            phase_tasks = db.query(Task).filter(Task.phase_id == active_phase.phase_id).all()
            for task in phase_tasks:
                task_keywords = task.task_name.lower().split()
                completed_keywords = ['completed', 'complete', 'finished', 'done', 'wrapped up', 'finalized']
                issue_keywords = ['issue', 'problem', 'blocked', 'delay', 'stuck', 'failed', 'error', 'concern', 'risk']
                task_mentioned = any(kw in notes_lower for kw in task_keywords if len(kw) > 4)
                task_completed = task_mentioned and any(kw in notes_lower for kw in completed_keywords)
                task_has_issue = task_mentioned and any(kw in notes_lower for kw in issue_keywords)

                if task_completed and task.status != 'completed':
                    task.status = 'completed'
                    task.completion_percentage = 100
                elif task_has_issue and task.priority != 'critical':
                    task.priority = 'critical'
                elif task_mentioned and task.status == 'todo':
                    task.status = 'in_progress'
                    if task.completion_percentage is None or task.completion_percentage < 10:
                        task.completion_percentage = 50

        auto_paid_count = _auto_mark_paid_invoices(
            db=db,
            project_id=project_id,
            text_blob=update.notes,
            source_label="daily update",
        )

        # 6. Create micro tasks from AI next_actions with rule-based fallback.
        phase_count = max(1, len(phases))
        ai_task_candidates: list[dict] = []
        next_actions = ai_analysis.get("next_actions") if isinstance(ai_analysis, dict) else None
        if isinstance(next_actions, list):
            for action in next_actions:
                action_text = str(action).strip(" -")
                if not action_text:
                    continue
                ai_task_candidates.append(
                    {
                        "task_name": action_text[:255],
                        "description": "Derived from daily update AI next actions.",
                        "phase_number": 1,
                        "priority": "high" if any(k in action_text.lower() for k in ["permit", "inspection", "critical", "deadline"]) else "medium",
                        "estimated_hours": 4.0,
                        "due_date": None,
                    }
                )

        if not ai_task_candidates:
            ai_task_candidates = _daily_update_task_fallback(update.notes, phase_count=phase_count)

        generated_tasks = _upsert_generated_tasks(
            db=db,
            project_id=project_id,
            phases=[{"phase_id": str(p.phase_id), "phase_name": p.phase_name, "phase_order": p.phase_order} for p in phases],
            task_records=ai_task_candidates,
            source_label="Daily update",
        )

        # 7. Recalculate completion for touched/active phases.
        for phase in phases:
            _recalculate_phase_completion(db, str(phase.phase_id))

        active_phase = db.query(ProjectPhase).filter(ProjectPhase.phase_id == active_phase.phase_id).first() if active_phase else None
        db.commit()

        return {
            "status": "success",
            "message": "Daily update processed with AI analysis ✅",
            "analysis": ai_analysis,
            "tasks_generated": len(generated_tasks),
            "generated_tasks": generated_tasks[:20],
            "invoices_marked_paid": auto_paid_count,
            "updated_progress": {
                "phase": active_phase.phase_name if active_phase else None,
                "completion": active_phase.completion_percentage if active_phase else 0
            }
        }
            
    except Exception as e:
        logger.error(f"Error processing daily update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function for weather integration
async def get_weather_for_location(location: str):
    """Get weather data for project location"""
    try:
        # WeatherService exposes sync summary/current helpers.
        return weather_service.get_weather_summary()
    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return None
# ============================================
# FILE UPLOAD & AI TASK GENERATION ENDPOINT
# ============================================

@app.post("/api/projects/{project_id}/upload-files")
async def upload_project_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    auto_generate_tasks: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload files to project storage and optionally auto-generate tasks using AI.
    """
    try:
        project_uuid = to_uuid(project_id)
        project = db.query(Project).filter(Project.project_id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        uploaded_files = []
        generated_tasks = []
        analysis_failures = []
        invoices_marked_paid = 0

        for file in files:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{file.filename}"

                content = await file.read()
                file_size = len(content)

                stored_path = storage_service.upload_bytes(
                    project_id=project_id,
                    filename=safe_filename,
                    content=content,
                    content_type=file.content_type,
                )

                document_id = uuid.uuid4()
                db.execute(text("""
                    INSERT INTO documents (
                        document_id, project_id, document_name, 
                        file_path, mime_type, file_size_bytes, uploaded_by, created_at, document_type
                    ) VALUES (
                        :doc_id, :proj_id, :filename, :filepath, 
                        :mime_type, :filesize, :user_id, NOW(), :document_type
                    )
                """), {
                    "doc_id": document_id,
                    "proj_id": project_id,
                    "filename": file.filename,
                    "filepath": stored_path,
                    "mime_type": file.content_type or "application/octet-stream",
                    "filesize": file_size,
                    "user_id": current_user.user_id,
                    "document_type": _infer_document_type(file.filename),
                })

                uploaded_files.append({
                    "document_id": str(document_id),
                    "filename": file.filename,
                    "size": file_size,
                    "type": file.content_type,
                })

                try:
                    extracted_text = _extract_text_from_file(file.filename, content, max_chars=18000)
                    invoices_marked_paid += _auto_mark_paid_invoices(
                        db=db,
                        project_id=project_id,
                        text_blob=f"{file.filename}\n{extracted_text}",
                        source_label=f"uploaded file {file.filename}",
                    )
                except Exception as auto_paid_exc:
                    logger.error("Auto-paid check failed for %s: %s", file.filename, auto_paid_exc)

                if auto_generate_tasks:
                    try:
                        with db.begin_nested():
                            tasks = await analyze_document_and_generate_tasks(
                                db=db,
                                project_id=project_id,
                                document_id=str(document_id),
                                filename=file.filename,
                                file_content=content,
                                ai_instruction=None,
                            )
                        generated_tasks.extend(tasks)
                    except Exception as ai_exc:
                        logger.error("AI analysis failed for %s: %s", file.filename, ai_exc)
                        analysis_failures.append(
                            {"filename": file.filename, "error": str(ai_exc)[:300]}
                        )
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                continue

        db.commit()
        return {
            "status": "success",
            "files_uploaded": len(uploaded_files),
            "uploaded_files": uploaded_files,
            "tasks_generated": len(generated_tasks),
            "generated_tasks": generated_tasks,
            "invoices_marked_paid": invoices_marked_paid,
            "analysis_failures": analysis_failures,
            "storage": "gcs" if storage_service.using_gcs else "local",
        }

    except Exception as e:
        logger.error(f"File upload error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def _infer_document_type(filename: str) -> str:
    lowered = filename.lower()
    if "permit" in lowered:
        return "permit"
    if "plan" in lowered or lowered.endswith((".dwg", ".dxf")):
        return "plan"
    if "contract" in lowered:
        return "contract"
    if "report" in lowered or lowered.endswith(".pdf"):
        return "report"
    if "survey" in lowered:
        return "survey"
    if lowered.endswith((".jpg", ".jpeg", ".png")):
        return "photo"
    return "other"


def _extract_text_from_file(
    filename: str,
    file_content: bytes,
    max_chars: int = 12000,
) -> str:
    """Extract plaintext from uploaded file types."""
    lowered = filename.lower()

    if lowered.endswith(".pdf"):
        try:
            import PyPDF2

            reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = []
            for page in reader.pages[:12]:
                text.append(page.extract_text() or "")
            return "\n".join(text)[:max_chars]
        except Exception:
            return "[PDF text extraction failed]"

    if lowered.endswith((".xlsx", ".xls")):
        try:
            import openpyxl

            wb = openpyxl.load_workbook(BytesIO(file_content), read_only=True, data_only=True)
            rows = []
            for sheet in wb.worksheets[:4]:
                for row in list(sheet.iter_rows(values_only=True))[:120]:
                    rows.append(" ".join([str(cell) for cell in row if cell is not None]))
            return "\n".join(rows)[:max_chars]
        except Exception:
            return "[Excel text extraction failed]"

    if lowered.endswith((".txt", ".csv", ".md")):
        try:
            return file_content.decode("utf-8", errors="ignore")[:max_chars]
        except Exception:
            return "[Text extraction failed]"

    if lowered.endswith((".dwg", ".dxf")):
        # CAD binaries cannot be reliably text-extracted here.
        # Provide rich synthetic context so planning can still generate tasks.
        return (
            f"[CAD design file detected]\n"
            f"filename: {filename}\n"
            "assume this includes civil layout, grading, utility corridors, lot boundaries, "
            "road centerlines, drainage features, and staking references.\n"
            "generate implementation tasks for permitting, layout, earthwork, utilities, paving, "
            "inspection, and lot delivery sequencing.\n"
        )

    return ""


def _normalize_task_records(raw_tasks: list, phase_count: int) -> list[dict]:
    normalized = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            continue
        name = str(item.get("task_name") or item.get("name") or "").strip()
        if not name:
            continue
        phase_number = item.get("phase_number", 1)
        try:
            phase_number = max(1, min(int(phase_number), phase_count if phase_count > 0 else 1))
        except Exception:
            phase_number = 1
        priority = str(item.get("priority", "medium")).lower()
        if priority not in {"critical", "high", "medium", "low"}:
            priority = "medium"
        try:
            estimated_hours = float(item.get("estimated_hours", 12) or 12)
        except Exception:
            estimated_hours = 12.0
        normalized.append(
            {
                "task_name": name[:255],
                "description": str(item.get("description", ""))[:1500],
                "phase_number": phase_number,
                "priority": priority,
                "estimated_hours": max(1.0, estimated_hours),
                "due_date": item.get("due_date"),
            }
        )
    return normalized


def _deterministic_task_fallback(file_text: str, filename: str, phase_count: int) -> list[dict]:
    """Fallback rule-based task extraction when AI output is empty/invalid."""
    tasks = []
    lowered = file_text.lower()
    lines = [ln.strip(" -*\t") for ln in file_text.splitlines() if len(ln.strip()) > 12][:300]
    action_words = ("install", "complete", "submit", "review", "prepare", "coordinate", "schedule", "construct", "inspect", "close")

    for line in lines:
        l = line.lower()
        if len(tasks) >= 20:
            break
        if any(w in l for w in action_words):
            phase_number = 1
            if any(k in l for k in ["closeout", "delivery", "handover", "final"]):
                phase_number = min(phase_count, 2) if phase_count >= 2 else 1
            elif any(k in l for k in ["utility", "grading", "storm", "sewer", "road", "permit", "design"]):
                phase_number = 1
            priority = "high" if any(k in l for k in ["critical", "permit", "inspection", "deadline"]) else "medium"
            tasks.append(
                {
                    "task_name": line[:120],
                    "description": f"Extracted from {filename}",
                    "phase_number": phase_number,
                    "priority": priority,
                    "estimated_hours": 16.0,
                    "due_date": None,
                }
            )

    if tasks:
        return tasks

    # Granular guaranteed fallback for civil/land development packages.
    phase_two = 2 if phase_count >= 2 else 1
    return [
        {
            "task_name": "Validate boundary, lot layout, and utility alignments from uploaded plans",
            "description": f"Generated fallback task from {filename}",
            "phase_number": 1,
            "priority": "high",
            "estimated_hours": 14.0,
            "due_date": None,
        },
        {
            "task_name": "Build permit matrix for grading, stormwater, and utility approvals",
            "description": f"Generated fallback task from {filename}",
            "phase_number": 1,
            "priority": "critical",
            "estimated_hours": 12.0,
            "due_date": None,
        },
        {
            "task_name": "Stake primary control points and verify benchmark elevations",
            "description": f"Generated fallback task from {filename}",
            "phase_number": 1,
            "priority": "high",
            "estimated_hours": 10.0,
            "due_date": None,
        },
        {
            "task_name": "Execute rough grading sequence for Phase I lots and common areas",
            "description": f"Generated fallback task from {filename}",
            "phase_number": 1,
            "priority": "critical",
            "estimated_hours": 42.0,
            "due_date": None,
        },
        {
            "task_name": "Install underground water, sewer, and storm mains for first delivery lots",
            "description": f"Generated fallback task from {filename}",
            "phase_number": 1,
            "priority": "critical",
            "estimated_hours": 56.0,
            "due_date": None,
        },
        {
            "task_name": "Schedule utility and municipal inspections for first lot release",
            "description": f"Generated fallback task from {filename}",
            "phase_number": 1,
            "priority": "high",
            "estimated_hours": 16.0,
            "due_date": None,
        },
        {
            "task_name": "Close punch list and complete turnover package for first lot tranche",
            "description": f"Generated fallback task from {filename}",
            "phase_number": phase_two,
            "priority": "high",
            "estimated_hours": 18.0,
            "due_date": None,
        },
        {
            "task_name": "Finalize remaining lot closeout and developer exit documentation",
            "description": f"Generated fallback task from {filename}",
            "phase_number": phase_two,
            "priority": "critical",
            "estimated_hours": 24.0,
            "due_date": None,
        },
    ]


def _daily_update_task_fallback(notes: str, phase_count: int) -> list[dict]:
    """Create deterministic micro-tasks from contractor daily update notes."""
    notes_lower = (notes or "").lower()
    phase_two = 2 if phase_count >= 2 else 1
    tasks: list[dict] = []

    if any(token in notes_lower for token in ["permit", "approval", "matrix", "stormwater", "utility"]):
        tasks.extend(
            [
                {
                    "task_name": "Build permit matrix for grading, stormwater, and utility approvals",
                    "description": "Compile agencies, required documents, owner, target dates, and dependencies.",
                    "phase_number": 1,
                    "priority": "critical",
                    "estimated_hours": 8.0,
                    "due_date": None,
                },
                {
                    "task_name": "Draft grading permit package and supporting exhibits",
                    "description": "Prepare application forms, plan sheets, and engineering backups.",
                    "phase_number": 1,
                    "priority": "high",
                    "estimated_hours": 10.0,
                    "due_date": None,
                },
                {
                    "task_name": "Prepare stormwater/SWPPP approval submission checklist",
                    "description": "List required BMP details, calculations, and review agency comments workflow.",
                    "phase_number": 1,
                    "priority": "high",
                    "estimated_hours": 8.0,
                    "due_date": None,
                },
                {
                    "task_name": "Prepare utility approval package (water, sewer, power, telecom)",
                    "description": "Gather utility markups, capacity confirmations, and service agreement milestones.",
                    "phase_number": 1,
                    "priority": "high",
                    "estimated_hours": 8.0,
                    "due_date": None,
                },
                {
                    "task_name": "Break permitting sequence into weekly micro tasks with owners and due dates",
                    "description": "Convert major permit tracks into trackable execution tasks.",
                    "phase_number": 1,
                    "priority": "critical",
                    "estimated_hours": 6.0,
                    "due_date": None,
                },
            ]
        )

    if any(token in notes_lower for token in ["closeout", "turnover", "delivery", "exit"]):
        tasks.append(
            {
                "task_name": "Prepare phase closeout checklist and turnover artifact tracker",
                "description": "Create closeout package log for builder handoff and developer exit.",
                "phase_number": phase_two,
                "priority": "high",
                "estimated_hours": 6.0,
                "due_date": None,
            }
        )

    if tasks:
        return tasks

    return [
        {
            "task_name": "Convert contractor daily update into granular execution tasks",
            "description": "Create measurable tasks with owners, due dates, and dependencies from daily notes.",
            "phase_number": 1,
            "priority": "medium",
            "estimated_hours": 4.0,
            "due_date": None,
        }
    ]


def _upsert_generated_tasks(
    db: Session,
    project_id: str,
    phases: list[dict],
    task_records: list[dict],
    source_label: str,
) -> list[dict]:
    """Insert or update generated tasks and return a concise change list."""
    normalized = _normalize_task_records(task_records, phase_count=len(phases))
    if not normalized:
        return []

    results: list[dict] = []
    for task_info in normalized:
        phase_num = int(task_info.get("phase_number", 1))
        phase = next((p for p in phases if int(p["phase_order"]) == phase_num), phases[0])
        task_name = str(task_info.get("task_name", "Untitled task")).strip()

        existing = db.execute(
            text(
                """
                SELECT task_id, priority, estimated_hours
                FROM tasks
                WHERE project_id = :project_id
                  AND LOWER(task_name) = LOWER(:task_name)
                LIMIT 1
                """
            ),
            {"project_id": project_id, "task_name": task_name},
        ).fetchone()

        if existing:
            existing_priority = (existing[1] or "medium").lower()
            existing_hours = float(existing[2] or 0)
            new_priority = str(task_info.get("priority", "medium")).lower()
            rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            merged_priority = new_priority if rank.get(new_priority, 2) >= rank.get(existing_priority, 2) else existing_priority
            merged_hours = max(existing_hours, float(task_info.get("estimated_hours", 1) or 1))
            db.execute(
                text(
                    """
                    UPDATE tasks
                    SET
                        phase_id = :phase_id,
                        priority = :priority,
                        estimated_hours = :hours,
                        description = :description
                    WHERE task_id = :task_id
                    """
                ),
                {
                    "phase_id": phase["phase_id"],
                    "priority": merged_priority,
                    "hours": merged_hours,
                    "description": f"{task_info.get('description', '')}\n[Source: {source_label}]",
                    "task_id": str(existing[0]),
                },
            )
            results.append(
                {
                    "task_name": task_name,
                    "phase": phase["phase_name"],
                    "priority": merged_priority,
                    "action": "updated",
                }
            )
            continue

        db.execute(
            text(
                """
                INSERT INTO tasks (
                    task_id, phase_id, project_id, task_name, description,
                    status, priority, estimated_hours, due_date, created_at
                ) VALUES (
                    :task_id, :phase_id, :project_id, :task_name, :description,
                    'todo', :priority, :hours, :due_date, NOW()
                )
                """
            ),
            {
                "task_id": str(uuid.uuid4()),
                "phase_id": phase["phase_id"],
                "project_id": project_id,
                "task_name": task_name[:255],
                "description": f"{task_info.get('description', '')}\n[Source: {source_label}]",
                "priority": str(task_info.get("priority", "medium")).lower(),
                "hours": float(task_info.get("estimated_hours", 1) or 1),
                "due_date": task_info.get("due_date"),
            },
        )
        results.append(
            {
                "task_name": task_name,
                "phase": phase["phase_name"],
                "priority": str(task_info.get("priority", "medium")).lower(),
                "action": "created",
            }
        )
    return results


async def analyze_document_and_generate_tasks(
    db: Session,
    project_id: str,
    document_id: str,
    filename: str,
    file_content: bytes,
    ai_instruction: Optional[str],
) -> List[dict]:
    """Analyze one document and create tasks in mapped phases with robust fallback."""
    try:
        file_text = _extract_text_from_file(filename=filename, file_content=file_content)
        if len(file_text.strip()) < 20:
            file_text = f"Document: {filename}\nNo text extracted. Create inferred implementation tasks."
        _auto_mark_paid_invoices(
            db=db,
            project_id=project_id,
            text_blob=file_text,
            source_label=f"uploaded file {filename}",
        )

        project = db.query(Project).filter(Project.project_id == to_uuid(project_id)).first()
        phases = _ensure_project_phases(db, project_id)
        if not phases:
            return []

        instruction_line = ai_instruction.strip() if ai_instruction else "No special instruction."
        prompt = f"""Analyze this document uploaded to the "{project.project_name}" project and extract actionable construction tasks.

Document: {filename}
User instruction:
{instruction_line}

Content:
{file_text[:8000]}

Available Project Phases:
{chr(10).join([f"{p['phase_order']}. {p['phase_name']}" for p in phases])}

Extract up to 30 specific, actionable tasks from this document. For each task:
1. task_name: Clear, action-oriented name (e.g., "Install storm drain pipe", "Complete SWPPP plan")
2. description: Brief 1-2 sentence description
3. phase_number: Which phase (1, 2, or 3)
4. priority: critical, high, medium, or low
5. estimated_hours: Realistic hour estimate

Focus on:
- Specific work items mentioned
- Permit requirements
- Design/engineering tasks
- Critical warnings or requirements
- Items with deadlines or dependencies

Return ONLY a JSON array, no explanation:
[
  {{
    "task_name": "...",
    "description": "...",
    "phase_number": 1, 
    "priority": "high",
    "estimated_hours": 40,
    "due_date": "YYYY-MM-DD or null"
  }}
]"""
        tasks_data = rel_gpt_client.generate_json(user_prompt=prompt, max_tokens=2200, temperature=0.2)
        if isinstance(tasks_data, dict):
            tasks_data = tasks_data.get("tasks") or tasks_data.get("task_list") or []
        if not isinstance(tasks_data, list):
            tasks_data = []

        normalized_tasks = _normalize_task_records(tasks_data, phase_count=len(phases))
        if not normalized_tasks:
            # Retry with strict "JSON array only"
            retry_prompt = (
                prompt
                + "\nReturn STRICT JSON array only. No markdown. No explanation. At least 8 tasks if possible."
            )
            retry_data = rel_gpt_client.generate_json(user_prompt=retry_prompt, max_tokens=2000, temperature=0.1)
            if isinstance(retry_data, dict):
                retry_data = retry_data.get("tasks") or retry_data.get("task_list") or []
            if isinstance(retry_data, list):
                normalized_tasks = _normalize_task_records(retry_data, phase_count=len(phases))

        if not normalized_tasks:
            normalized_tasks = _deterministic_task_fallback(
                file_text=file_text,
                filename=filename,
                phase_count=len(phases),
            )

        analysis_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO document_ai_analysis (
                analysis_id, document_id, project_id, status, prompt, extracted_tasks_json, ai_instruction, created_at, updated_at
            ) VALUES (
                :analysis_id, :document_id, :project_id, :status, :prompt, CAST(:tasks_json AS jsonb), :ai_instruction, NOW(), NOW()
            )
        """), {
            "analysis_id": analysis_id,
            "document_id": document_id,
            "project_id": project_id,
            "status": "completed",
            "prompt": prompt[:12000],
            "tasks_json": json.dumps(normalized_tasks[:40]),
            "ai_instruction": ai_instruction,
        })

        inserted_tasks = []
        touched_phase_ids = set()
        for task_info in normalized_tasks[:40]:
            try:
                phase_num = int(task_info.get("phase_number", 1))
                phase = next((p for p in phases if int(p["phase_order"]) == phase_num), phases[0])
                normalized_task_name = str(task_info.get("task_name", "Untitled task")).strip()
                estimated_hours = float(task_info.get("estimated_hours", 0) or 0)
                task_priority = task_info.get("priority", "medium")
                budget_estimate = _estimate_budget_for_task(normalized_task_name, task_priority, estimated_hours)

                existing = db.execute(text("""
                    SELECT task_id, priority, estimated_hours, completion_percentage
                    FROM tasks
                    WHERE project_id = :project_id
                      AND LOWER(task_name) = LOWER(:task_name)
                    LIMIT 1
                """), {"project_id": project_id, "task_name": normalized_task_name}).fetchone()
                if existing:
                    existing_priority = (existing[1] or "medium").lower()
                    existing_hours = float(existing[2] or 0)
                    existing_completion = int(existing[3] or 0)
                    rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                    merged_priority = task_priority if rank.get(task_priority, 2) >= rank.get(existing_priority, 2) else existing_priority
                    merged_hours = max(existing_hours, estimated_hours)
                    merged_completion = max(existing_completion, int(task_info.get("completion_percentage") or 0))
                    db.execute(text("""
                        UPDATE tasks
                        SET
                            phase_id = :phase_id,
                            priority = :priority,
                            estimated_hours = :hours,
                            description = :description,
                            completion_percentage = :completion
                        WHERE task_id = :task_id
                    """), {
                        "phase_id": phase["phase_id"],
                        "priority": merged_priority,
                        "hours": merged_hours,
                        "completion": merged_completion,
                        "description": (
                            f"{str(task_info.get('description', ''))}\n"
                            f"[Source: {filename} | Estimated Budget: ${budget_estimate:,.0f}]"
                        )[:1800],
                        "task_id": str(existing[0]),
                    })
                    touched_phase_ids.add(phase["phase_id"])
                    inserted_tasks.append({
                        "task_name": normalized_task_name,
                        "phase": phase["phase_name"],
                        "priority": merged_priority,
                        "budget_estimate": budget_estimate,
                        "action": "updated",
                    })
                    continue

                task_id = str(uuid.uuid4())
                due_date = task_info.get("due_date")
                db.execute(text("""
                    INSERT INTO tasks (
                        task_id, phase_id, project_id, task_name, description,
                        status, priority, estimated_hours, due_date, completion_percentage, created_at
                    ) VALUES (
                        :task_id, :phase_id, :project_id, :task_name, :description,
                        'todo', :priority, :hours, :due_date, :completion, NOW()
                    )
                """), {
                    "task_id": task_id,
                    "phase_id": phase["phase_id"],
                    "project_id": project_id,
                    "task_name": normalized_task_name[:255],
                    "description": (
                        f"{str(task_info.get('description', ''))}\n"
                        f"[Source: {filename} | Estimated Budget: ${budget_estimate:,.0f}]"
                    )[:1800],
                    "priority": task_priority,
                    "hours": estimated_hours,
                    "due_date": due_date if due_date else None,
                    "completion": max(0, min(100, int(task_info.get("completion_percentage") or 0))),
                })
                touched_phase_ids.add(phase["phase_id"])

                inserted_tasks.append({
                    "task_name": normalized_task_name,
                    "phase": phase["phase_name"],
                    "priority": task_priority,
                    "budget_estimate": _estimate_budget_for_task(
                        normalized_task_name, task_priority, estimated_hours
                    ),
                    "action": "created",
                })
            except Exception as e:
                logger.error(f"Error inserting task: {e}")
                continue

        for phase_id in touched_phase_ids:
            _recalculate_phase_completion(db, phase_id)

        return inserted_tasks

    except Exception as e:
        logger.error(f"AI task generation error: {e}")
        try:
            db.execute(text("""
                INSERT INTO document_ai_analysis (
                    analysis_id, document_id, project_id, status, error, created_at, updated_at
                ) VALUES (
                    :analysis_id, :document_id, :project_id, :status, :error, NOW(), NOW()
                )
            """), {
                "analysis_id": str(uuid.uuid4()),
                "document_id": document_id,
                "project_id": project_id,
                "status": "failed",
                "error": str(e)[:3000],
            })
        except Exception as log_exc:
            logger.error("Could not save failed analysis record: %s", log_exc)
        return []


@app.get("/api/projects/{project_id}/files")
async def list_project_files(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all files for a project"""
    try:
        result = db.execute(text("""
            SELECT 
                d.document_id,
                d.document_name,
                d.document_type,
                d.mime_type,
                d.file_size_bytes,
                d.file_path,
                d.created_at,
                u.first_name,
                u.last_name,
                daa.status as ai_status,
                daa.updated_at as ai_updated_at
            FROM documents d
            LEFT JOIN users u ON d.uploaded_by = u.user_id
            LEFT JOIN LATERAL (
                SELECT status, updated_at
                FROM document_ai_analysis
                WHERE document_id = d.document_id
                ORDER BY updated_at DESC
                LIMIT 1
            ) daa ON true
            WHERE d.project_id = :project_id
            ORDER BY d.created_at ASC
        """), {"project_id": project_id})

        files = []
        for row in result:
            file_path = row[5]
            files.append({
                "document_id": str(row[0]),
                "filename": row[1],
                "file_type": row[2],
                "mime_type": row[3],
                "file_size": row[4],
                "file_path": file_path,
                "file_url": storage_service.get_read_url(file_path),
                "uploaded_at": row[6].isoformat() if row[6] else None,
                "uploaded_by": f"{row[7]} {row[8]}" if row[7] else "Unknown",
                "ai_status": row[9] or "not_analyzed",
                "ai_updated_at": row[10].isoformat() if row[10] else None,
            })

        return files

    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/documents/{document_id}/analyze")
async def analyze_single_document(
    project_id: str,
    document_id: str,
    ai_instruction: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze one uploaded document and generate tasks."""
    row = db.execute(text("""
        SELECT document_name, file_path
        FROM documents
        WHERE project_id = :project_id AND document_id = :document_id
    """), {"project_id": project_id, "document_id": document_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    file_name, file_path = row[0], row[1]
    content = storage_service.read_bytes(file_path)
    tasks = await analyze_document_and_generate_tasks(
        db=db,
        project_id=project_id,
        document_id=document_id,
        filename=file_name,
        file_content=content,
        ai_instruction=ai_instruction,
    )
    db.commit()
    return {"status": "success", "tasks_generated": len(tasks), "generated_tasks": tasks}


@app.post("/api/projects/{project_id}/documents/analyze-all")
async def analyze_all_project_documents(
    project_id: str,
    ai_instruction: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze all project documents and generate tasks from each analyzable file."""
    rows = db.execute(text("""
        SELECT document_id, document_name, file_path
        FROM documents
        WHERE project_id = :project_id
        ORDER BY created_at DESC
    """), {"project_id": project_id}).fetchall()

    generated = []
    analyzed_documents = 0
    for row in rows:
        document_id, document_name, file_path = str(row[0]), row[1], row[2]
        try:
            content = storage_service.read_bytes(file_path)
            tasks = await analyze_document_and_generate_tasks(
                db=db,
                project_id=project_id,
                document_id=document_id,
                filename=document_name,
                file_content=content,
                ai_instruction=ai_instruction,
            )
            analyzed_documents += 1
            generated.extend(tasks)
        except Exception as exc:
            logger.error("Analyze-all failed for %s: %s", document_name, exc)

    db.commit()
    return {
        "status": "success",
        "documents_analyzed": analyzed_documents,
        "tasks_generated": len(generated),
        "generated_tasks": generated,
    }


@app.post("/api/projects/{project_id}/tasks/rebuild-from-files")
async def rebuild_project_tasks_from_files(
    project_id: str,
    payload: RebuildTasksFromFilesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clear all project tasks and repopulate tasks from all uploaded project files.
    """
    project = db.query(Project).filter(Project.project_id == to_uuid(project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rows = db.execute(text("""
        SELECT document_id, document_name, file_path
        FROM documents
        WHERE project_id = :project_id
        ORDER BY created_at ASC
    """), {"project_id": project_id}).fetchall()

    if not rows:
        raise HTTPException(status_code=400, detail="No uploaded files found for this project")

    _ensure_project_phases(db, project_id)

    # 1) Clear tasks.
    deleted_tasks = db.execute(text("""
        DELETE FROM tasks
        WHERE project_id = :project_id
    """), {"project_id": project_id}).rowcount or 0

    # 2) Reset phase completion to zero.
    db.execute(text("""
        UPDATE project_phases
        SET completion_percentage = 0, updated_at = NOW()
        WHERE project_id = :project_id
    """), {"project_id": project_id})

    # 3) Optional: clear prior analysis history for a clean run.
    if payload.clear_analysis_history:
        db.execute(text("""
            DELETE FROM document_ai_analysis
            WHERE project_id = :project_id
        """), {"project_id": project_id})

    generated = []
    analyzed_documents = 0
    for row in rows:
        document_id, document_name, file_path = str(row[0]), row[1], row[2]
        try:
            content = storage_service.read_bytes(file_path)
            tasks = await analyze_document_and_generate_tasks(
                db=db,
                project_id=project_id,
                document_id=document_id,
                filename=document_name,
                file_content=content,
                ai_instruction=payload.ai_instruction,
            )
            analyzed_documents += 1
            generated.extend(tasks)
        except Exception as exc:
            logger.error("Rebuild-from-files failed for %s: %s", document_name, exc)

    db.commit()
    created_count = len([t for t in generated if t.get("action") == "created"])
    updated_count = len([t for t in generated if t.get("action") == "updated"])
    return {
        "status": "success",
        "tasks_deleted": int(deleted_tasks),
        "documents_analyzed": analyzed_documents,
        "tasks_generated": len(generated),
        "created_count": created_count,
        "updated_count": updated_count,
        "generated_tasks": generated,
    }


@app.post("/api/projects/{project_id}/documents/analyze-selected")
async def analyze_selected_project_documents(
    project_id: str,
    payload: AnalyzeSelectedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze only selected documents and generate tasks."""
    if not payload.document_ids:
        raise HTTPException(status_code=400, detail="No documents selected")

    selected_ids = {str(doc_id) for doc_id in payload.document_ids}
    rows = db.execute(text("""
        SELECT document_id, document_name, file_path
        FROM documents
        WHERE project_id = :project_id
        ORDER BY created_at ASC
    """), {"project_id": project_id}).fetchall()
    rows = [row for row in rows if str(row[0]) in selected_ids]

    generated = []
    analyzed_documents = 0
    for row in rows:
        document_id, document_name, file_path = str(row[0]), row[1], row[2]
        try:
            content = storage_service.read_bytes(file_path)
            tasks = await analyze_document_and_generate_tasks(
                db=db,
                project_id=project_id,
                document_id=document_id,
                filename=document_name,
                file_content=content,
                ai_instruction=payload.ai_instruction,
            )
            analyzed_documents += 1
            generated.extend(tasks)
        except Exception as exc:
            logger.error("Analyze-selected failed for %s: %s", document_name, exc)

    db.commit()
    return {
        "status": "success",
        "documents_analyzed": analyzed_documents,
        "tasks_generated": len(generated),
        "generated_tasks": generated,
    }


@app.post("/api/projects/{project_id}/documents/analyze-query")
async def analyze_documents_by_query(
    project_id: str,
    payload: AnalyzeQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze documents by conditions (filename/date filters)."""
    conditions = ["project_id = :project_id"]
    params = {"project_id": project_id, "limit": max(1, min(payload.limit, 300))}

    if payload.filename_contains:
        conditions.append("LOWER(document_name) LIKE :filename_contains")
        params["filename_contains"] = f"%{payload.filename_contains.lower()}%"
    if payload.uploaded_from:
        conditions.append("created_at >= :uploaded_from")
        params["uploaded_from"] = payload.uploaded_from
    if payload.uploaded_to:
        conditions.append("created_at < (:uploaded_to::date + INTERVAL '1 day')")
        params["uploaded_to"] = payload.uploaded_to

    query = f"""
        SELECT document_id, document_name, file_path
        FROM documents
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at ASC
        LIMIT :limit
    """
    rows = db.execute(text(query), params).fetchall()

    generated = []
    analyzed_documents = 0
    for row in rows:
        document_id, document_name, file_path = str(row[0]), row[1], row[2]
        try:
            content = storage_service.read_bytes(file_path)
            tasks = await analyze_document_and_generate_tasks(
                db=db,
                project_id=project_id,
                document_id=document_id,
                filename=document_name,
                file_content=content,
                ai_instruction=payload.ai_instruction,
            )
            analyzed_documents += 1
            generated.extend(tasks)
        except Exception as exc:
            logger.error("Analyze-query failed for %s: %s", document_name, exc)

    db.commit()
    return {
        "status": "success",
        "documents_analyzed": analyzed_documents,
        "tasks_generated": len(generated),
        "generated_tasks": generated,
    }


@app.get("/api/projects/{project_id}/files/{document_id}/open")
async def get_file_open_url(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a signed open URL for a document (when using GCS)."""
    row = db.execute(text("""
        SELECT file_path, document_name
        FROM documents
        WHERE project_id = :project_id AND document_id = :document_id
    """), {"project_id": project_id, "document_id": document_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path, document_name = row[0], row[1]
    url = storage_service.get_read_url(file_path)
    return {
        "document_id": document_id,
        "filename": document_name,
        "file_path": file_path,
        "open_url": url,
        "download_url": f"/api/projects/{project_id}/files/{document_id}/download",
        "storage": "gcs" if file_path.startswith("gs://") else "local",
    }


@app.get("/api/projects/{project_id}/files/{document_id}/download")
async def download_project_file(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream file bytes through API so clients can open files even when not publicly hosted."""
    row = db.execute(text("""
        SELECT document_name, mime_type, file_path
        FROM documents
        WHERE project_id = :project_id AND document_id = :document_id
    """), {"project_id": project_id, "document_id": document_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    document_name, mime_type, file_path = row[0], row[1], row[2]
    content = storage_service.read_bytes(file_path)
    safe_name = quote(document_name)
    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{safe_name}"}
    return Response(content=content, media_type=(mime_type or "application/octet-stream"), headers=headers)


@app.get("/api/projects/{project_id}/ai/tasks-from-docs")
async def get_document_ai_task_runs(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(text("""
        SELECT
            daa.analysis_id,
            daa.document_id,
            d.document_name,
            daa.status,
            daa.ai_instruction,
            daa.extracted_tasks_json,
            daa.error,
            daa.created_at,
            daa.updated_at
        FROM document_ai_analysis daa
        JOIN documents d ON d.document_id = daa.document_id
        WHERE daa.project_id = :project_id
        ORDER BY daa.updated_at DESC
    """), {"project_id": project_id})

    rows = []
    for row in result:
        tasks = row[5] or []
        rows.append(
            {
                "analysis_id": str(row[0]),
                "document_id": str(row[1]),
                "document_name": row[2],
                "status": row[3],
                "ai_instruction": row[4],
                "task_count": len(tasks) if isinstance(tasks, list) else 0,
                "tasks": tasks if isinstance(tasks, list) else [],
                "error": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "updated_at": row[8].isoformat() if row[8] else None,
            }
        )
    return rows


@app.post("/api/projects/{project_id}/invoices/review-selected")
async def review_selected_invoices(
    project_id: str,
    payload: InvoiceReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Parse selected invoice documents and flag potential overpayment risk."""
    if not payload.document_ids:
        raise HTTPException(status_code=400, detail="No invoice documents selected")

    selected_ids = {str(doc_id) for doc_id in payload.document_ids}
    rows = db.execute(text("""
        SELECT document_id, document_name, file_path, mime_type
        FROM documents
        WHERE project_id = :project_id
        ORDER BY created_at ASC
    """), {"project_id": project_id}).fetchall()
    rows = [row for row in rows if str(row[0]) in selected_ids]

    if not rows:
        return {"status": "success", "reviewed": 0, "invoices": []}

    history = db.execute(text("""
        SELECT amount
        FROM expenses
        WHERE project_id = :project_id
        ORDER BY expense_date DESC
        LIMIT 50
    """), {"project_id": project_id}).fetchall()
    recent_amounts = [float(r[0]) for r in history if r[0] is not None]
    baseline = (sum(recent_amounts) / len(recent_amounts)) if recent_amounts else 0.0

    project_uuid = to_uuid(project_id)
    project_phases = db.query(models.ProjectPhase).filter(
        models.ProjectPhase.project_id == project_uuid
    ).order_by(models.ProjectPhase.phase_order).all()

    reviewed = []
    invoices_marked_paid = 0
    for row in rows:
        document_id, document_name, file_path, mime_type = str(row[0]), row[1], row[2], row[3]
        content = storage_service.read_bytes(file_path)
        text_blob = _extract_text_from_file(document_name, content, max_chars=18000)
        amounts = _extract_currency_values(text_blob)
        invoice_amount = max(amounts) if amounts else 0.0
        source_text = f"{document_name}\n{text_blob[:4000]}"
        invoices_marked_paid += _auto_mark_paid_invoices(
            db=db,
            project_id=project_id,
            text_blob=source_text,
            source_label=f"invoice document {document_name}",
        )

        inferred_category = _keyword_category_guess(source_text)
        phase_obj = _infer_phase_from_text(project_phases, source_text)
        inferred_phase_id = str(phase_obj.phase_id) if phase_obj else None
        inferred_phase_name = phase_obj.phase_name if phase_obj else None

        overpay_risk = "low"
        risk_reason = "No anomaly detected"
        if baseline > 0 and invoice_amount > baseline * 1.25:
            overpay_risk = "high"
            risk_reason = f"Invoice amount ${invoice_amount:,.2f} is >25% above recent average ${baseline:,.2f}"
        elif baseline > 0 and invoice_amount > baseline * 1.10:
            overpay_risk = "medium"
            risk_reason = f"Invoice amount ${invoice_amount:,.2f} is >10% above recent average ${baseline:,.2f}"

        auto_budget_id = None
        if payload.auto_record_expense and invoice_amount > 0:
            budget_obj = _find_or_create_budget_for_category(
                db=db,
                project_uuid=project_uuid,
                phase_uuid=(phase_obj.phase_id if phase_obj else None),
                category_name=inferred_category,
                invoice_amount=invoice_amount,
            )
            auto_budget_id = str(budget_obj.budget_id)
            db.add(
                models.Expense(
                    project_id=project_uuid,
                    budget_id=budget_obj.budget_id if budget_obj else None,
                    phase_id=phase_obj.phase_id if phase_obj else None,
                    expense_date=datetime.utcnow().date(),
                    description=f"Invoice ingest: {document_name}",
                    amount=Decimal(str(invoice_amount)).quantize(Decimal("0.01")),
                    invoice_number=document_name[:90],
                    payment_status="pending",
                    notes=(
                        f"Invoice review risk={overpay_risk}; reason={risk_reason}; "
                        f"category={inferred_category}; phase={inferred_phase_name or 'n/a'}"
                    ),
                )
            )

        reviewed.append(
            {
                "document_id": document_id,
                "document_name": document_name,
                "mime_type": mime_type,
                "invoice_amount": invoice_amount,
                "inferred_category": inferred_category,
                "inferred_phase_id": inferred_phase_id,
                "inferred_phase_name": inferred_phase_name,
                "assigned_budget_id": auto_budget_id,
                "overpay_risk": overpay_risk,
                "risk_reason": risk_reason,
            }
        )

    db.commit()
    return {
        "status": "success",
        "reviewed": len(reviewed),
        "invoices_marked_paid": invoices_marked_paid,
        "invoices": reviewed,
    }


@app.get("/api/projects/{project_id}/phase-budget-dashboard")
async def get_phase_budget_dashboard(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_uuid = to_uuid(project_id)
    phases = db.query(models.ProjectPhase).filter(
        models.ProjectPhase.project_id == project_uuid
    ).order_by(models.ProjectPhase.phase_order).all()
    if not phases:
        return {"project_id": project_id, "phases": []}

    budgets = db.query(models.ProjectBudget).filter(
        models.ProjectBudget.project_id == project_uuid
    ).all()
    expenses = db.query(models.Expense).filter(
        models.Expense.project_id == project_uuid
    ).all()

    budget_by_phase = {}
    budget_phase_lookup = {}
    for b in budgets:
        if b.phase_id:
            pid = str(b.phase_id)
            budget_by_phase[pid] = budget_by_phase.get(pid, 0.0) + float(b.budgeted_amount or 0)
        budget_phase_lookup[str(b.budget_id)] = str(b.phase_id) if b.phase_id else None

    spent_by_phase = {}
    for e in expenses:
        phase_id = str(e.phase_id) if e.phase_id else budget_phase_lookup.get(str(e.budget_id)) if e.budget_id else None
        if not phase_id:
            continue
        spent_by_phase[phase_id] = spent_by_phase.get(phase_id, 0.0) + float(e.amount or 0)

    response_rows = []
    for p in phases:
        pid = str(p.phase_id)
        budgeted = float(budget_by_phase.get(pid, 0.0))
        spent = float(spent_by_phase.get(pid, 0.0))
        utilization = (spent / budgeted * 100.0) if budgeted > 0 else 0.0
        response_rows.append(
            {
                "phase_id": pid,
                "phase_name": p.phase_name,
                "phase_order": p.phase_order,
                "completion_percentage": float(p.completion_percentage or 0),
                "budgeted": budgeted,
                "spent": spent,
                "remaining": budgeted - spent,
                "budget_utilization_percentage": utilization,
            }
        )

    return {"project_id": project_id, "phases": response_rows}


@app.delete("/api/projects/{project_id}/files/{document_id}")
async def delete_project_file(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project file"""
    try:
        result = db.execute(text("""
            SELECT file_path 
            FROM documents 
            WHERE document_id = :doc_id AND project_id = :project_id
        """), {"doc_id": document_id, "project_id": project_id})

        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        storage_service.delete_path(row[0])
        db.execute(text("""
            DELETE FROM documents WHERE document_id = :doc_id
        """), {"doc_id": document_id})

        db.commit()

        return {"status": "success", "message": "File deleted"}

    except Exception as e:
        logger.error(f"Delete file error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
