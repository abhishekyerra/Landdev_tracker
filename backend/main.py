"""
Land Development Project Tracker - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import List, Optional
import os
import logging
import uuid

logger = logging.getLogger(__name__)

from models import User, Project, ProjectPhase, Task
from database import engine, SessionLocal, Base
from auth import create_access_token, verify_password, get_password_hash, get_current_user
from weather_service import weather_service
from ai_agent import ai_agent
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

@app.put("/api/phases/{phase_id}", response_model=schemas.PhaseResponse)
async def update_phase(
    phase_id: str,
    phase: schemas.PhaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update phase details"""
    db_phase = db.query(models.ProjectPhase).filter(models.ProjectPhase.phase_id == phase_id).first()
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
    summary = db.execute(
        """
        SELECT * FROM v_project_budget_summary 
        WHERE project_id = :project_id
        """,
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
    
    db_expense = models.Expense(**expense.dict(), project_id=to_uuid(project_id))
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

@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_update: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a task (e.g., status, completion)"""
    task = db.query(models.Task).filter(models.Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    for key, value in task_update.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task

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
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

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
        
        # 3. Process with AI if available
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if anthropic_api_key:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_api_key)
            
            # Get active phase details
            active_phase = next((p for p in phases if p.status == 'in_progress'), None)
            active_tasks = [t for t in tasks if t.status in ['in_progress', 'todo']]
            completed_tasks = [t for t in tasks if t.status == 'completed']
            
            # Build comprehensive context
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

            # Call Claude API
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            ai_response = message.content[0].text
            
            # Parse AI response
            try:
                # Clean markdown code blocks if present
                if "```json" in ai_response:
                    ai_response = ai_response.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_response:
                    ai_response = ai_response.split("```")[1].split("```")[0].strip()
                
                ai_analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                ai_analysis = {
                    "progress_assessment": "Analysis completed",
                    "strategic_guidance": ai_response,
                    "next_actions": ["Review AI response for detailed recommendations"]
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
            
            # 5. Auto-update tasks based on AI analysis of daily notes
            notes_lower = update.notes.lower()
            
            if active_phase:
                phase_tasks = db.query(Task).filter(Task.phase_id == active_phase.phase_id).all()
                
                for task in phase_tasks:
                    task_name_lower = task.task_name.lower()
                    task_keywords = task_name_lower.split()
                    
                    # Check if task is mentioned as completed
                    completed_keywords = ['completed', 'complete', 'finished', 'done', 'wrapped up', 'finalized']
                    task_mentioned = any(kw in notes_lower for kw in task_keywords if len(kw) > 4)
                    task_completed = task_mentioned and any(kw in notes_lower for kw in completed_keywords)
                    
                    # Check if task has issues/blockers - mark as critical
                    issue_keywords = ['issue', 'problem', 'blocked', 'delay', 'stuck', 'failed', 'error', 'concern', 'risk']
                    task_has_issue = task_mentioned and any(kw in notes_lower for kw in issue_keywords)
                    
                    if task_completed and task.status != 'completed':
                        task.status = 'completed'
                    elif task_has_issue and task.priority != 'critical':
                        task.priority = 'critical'
                    elif task_mentioned and task.status == 'todo':
                        task.status = 'in_progress'
                
                # Recalculate phase completion percentage
                all_phase_tasks = db.query(Task).filter(Task.phase_id == active_phase.phase_id).all()
                if all_phase_tasks:
                    completed_count = len([t for t in all_phase_tasks if t.status == 'completed'])
                    new_completion = int((completed_count / len(all_phase_tasks)) * 100)
                    # Also consider AI-reported progress if higher
                    active_phase.completion_percentage = max(new_completion, active_phase.completion_percentage)
            
            db.commit()
            
            return {
                "status": "success",
                "message": "Daily update processed with AI analysis ✅",
                "analysis": ai_analysis,
                "updated_progress": {
                    "phase": active_phase.phase_name if active_phase else None,
                    "completion": active_phase.completion_percentage if active_phase else 0
                }
            }
        else:
            # Fallback without AI
            db.execute(text("""
                INSERT INTO daily_updates (
                    project_id, user_id, update_date, notes, blockers, 
                    weather_impact, crew_size, equipment_available
                ) VALUES (
                    :project_id, :user_id, :update_date, :notes, :blockers,
                    :weather_impact, :crew_size, :equipment_available
                )
            """), {
                "project_id": project_id,
                "user_id": current_user.user_id,
                "update_date": datetime.now().date(),
                "notes": update.notes,
                "blockers": update.blockers,
                "weather_impact": update.weather_impact,
                "crew_size": update.crew_size,
                "equipment_available": update.equipment_available
            })
            db.commit()
            
            return {
                "status": "success",
                "message": "Daily update saved (AI analysis requires ANTHROPIC_API_KEY)",
                "analysis": {
                    "strategic_guidance": "Update saved successfully. Enable AI analysis by adding ANTHROPIC_API_KEY to environment variables."
                }
            }
            
    except Exception as e:
        logger.error(f"Error processing daily update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function for weather integration
async def get_weather_for_location(location: str):
    """Get weather data for project location"""
    try:
        # Use your existing weather service
        weather_data = await weather_service.get_weather("columbia-tn")
        return weather_data
    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return None
# ============================================
# FILE UPLOAD & AI TASK GENERATION ENDPOINT
# Add this to backend/main.py
# ============================================

from fastapi import UploadFile, File, Form
from typing import List, Optional
import os
from pathlib import Path
import shutil

# File storage configuration
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/api/projects/{project_id}/upload-files")
async def upload_project_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    auto_generate_tasks: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload files to project and optionally auto-generate tasks using AI
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create project folder
        project_folder = UPLOAD_DIR / project_id
        project_folder.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        generated_tasks = []
        
        for file in files:
            try:
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{file.filename}"
                file_path = project_folder / safe_filename
                
                # Save file
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                file_size = len(content)
                
                # Record in database
                document_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO documents (
                        document_id, project_id, document_name, 
                        file_path, file_type, file_size, uploaded_by, created_at
                    ) VALUES (
                        :doc_id, :proj_id, :filename, :filepath, 
                        :filetype, :filesize, :user_id, NOW()
                    )
                """), {
                    "doc_id": document_id,
                    "proj_id": project_id,
                    "filename": file.filename,
                    "filepath": str(file_path),
                    "filetype": file.content_type or "application/octet-stream",
                    "filesize": file_size,
                    "user_id": current_user.user_id
                })
                
                uploaded_files.append({
                    "filename": file.filename,
                    "size": file_size,
                    "type": file.content_type
                })
                
                # AI Task Generation
                if auto_generate_tasks and os.getenv("ANTHROPIC_API_KEY"):
                    try:
                        tasks = await generate_tasks_from_file(
                            file_path, 
                            file.filename, 
                            project_id, 
                            content,
                            db
                        )
                        generated_tasks.extend(tasks)
                    except Exception as e:
                        logger.error(f"AI task generation failed for {file.filename}: {e}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                continue
        
        db.commit()
        
        return {
            "status": "success",
            "files_uploaded": len(uploaded_files),
            "uploaded_files": uploaded_files,
            "tasks_generated": len(generated_tasks),
            "generated_tasks": generated_tasks
        }
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def generate_tasks_from_file(
    file_path: Path, 
    filename: str, 
    project_id: str, 
    file_content: bytes,
    db: Session
):
    """
    Use Claude AI to extract tasks from uploaded documents
    """
    try:
        # Extract text based on file type
        file_text = ""
        
        if filename.lower().endswith('.pdf'):
            # PDF extraction
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages[:10]:  # First 10 pages
                        file_text += page.extract_text() + "\n"
            except:
                file_text = "[PDF text extraction failed]"
        
        elif filename.lower().endswith(('.xlsx', '.xls')):
            # Excel extraction
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path)
                for sheet in wb.worksheets[:3]:  # First 3 sheets
                    for row in list(sheet.iter_rows(values_only=True))[:100]:  # First 100 rows
                        file_text += " ".join([str(cell) for cell in row if cell]) + "\n"
            except:
                file_text = "[Excel text extraction failed]"
        
        elif filename.lower().endswith(('.txt', '.csv')):
            # Text file
            try:
                file_text = file_content.decode('utf-8', errors='ignore')[:5000]
            except:
                file_text = "[Text extraction failed]"
        
        else:
            return []  # Unsupported file type
        
        if len(file_text.strip()) < 50:
            return []  # Not enough content
        
        # Get project context
        project = db.query(Project).filter(Project.project_id == project_id).first()
        phases_result = db.execute(text("""
            SELECT phase_id, phase_name, phase_order, description
            FROM project_phases
            WHERE project_id = :project_id
            ORDER BY phase_order
        """), {"project_id": project_id})
        
        phases = []
        for row in phases_result:
            phases.append({
                "phase_id": str(row[0]),
                "phase_name": row[1],
                "phase_order": row[2],
                "description": row[3]
            })
        
        if not phases:
            return []
        
        # Call Claude API
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        prompt = f"""Analyze this document uploaded to the "{project.project_name}" project and extract actionable construction tasks.

Document: {filename}
Content (first 3000 characters):
{file_text[:3000]}

Available Project Phases:
{chr(10).join([f"{p['phase_order']}. {p['phase_name']}" for p in phases])}

Extract up to 15 specific, actionable tasks from this document. For each task:
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
    "estimated_hours": 40
  }}
]"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Parse JSON
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            response_text = json_match.group(0)
        
        tasks_data = json.loads(response_text)
        
        # Insert tasks
        inserted_tasks = []
        for task_info in tasks_data[:15]:  # Max 15 tasks
            try:
                # Find matching phase
                phase_num = task_info.get('phase_number', 1)
                phase = next((p for p in phases if p['phase_order'] == phase_num), phases[0])
                
                task_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO tasks (
                        task_id, phase_id, project_id, task_name, description,
                        status, priority, estimated_hours, created_at
                    ) VALUES (
                        :task_id, :phase_id, :project_id, :task_name, :description,
                        'todo', :priority, :hours, NOW()
                    )
                """), {
                    "task_id": task_id,
                    "phase_id": phase['phase_id'],
                    "project_id": project_id,
                    "task_name": task_info['task_name'][:255],
                    "description": task_info.get('description', ''),
                    "priority": task_info.get('priority', 'medium'),
                    "hours": task_info.get('estimated_hours', 0)
                })
                
                inserted_tasks.append({
                    "task_name": task_info['task_name'],
                    "phase": phase['phase_name'],
                    "priority": task_info.get('priority', 'medium')
                })
            except Exception as e:
                logger.error(f"Error inserting task: {e}")
                continue
        
        return inserted_tasks
        
    except Exception as e:
        logger.error(f"AI task generation error: {e}")
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
                d.file_type,
                d.file_size,
                d.created_at,
                u.first_name,
                u.last_name
            FROM documents d
            LEFT JOIN users u ON d.uploaded_by = u.user_id
            WHERE d.project_id = :project_id
            ORDER BY d.created_at DESC
        """), {"project_id": project_id})
        
        files = []
        for row in result:
            files.append({
                "document_id": str(row[0]),
                "filename": row[1],
                "file_type": row[2],
                "file_size": row[3],
                "uploaded_at": row[4].isoformat() if row[4] else None,
                "uploaded_by": f"{row[5]} {row[6]}" if row[5] else "Unknown"
            })
        
        return files
        
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}/files/{document_id}")
async def delete_project_file(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project file"""
    try:
        # Get file path
        result = db.execute(text("""
            SELECT file_path 
            FROM documents 
            WHERE document_id = :doc_id AND project_id = :project_id
        """), {"doc_id": document_id, "project_id": project_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file from disk
        file_path = Path(row[0])
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        db.execute(text("""
            DELETE FROM documents WHERE document_id = :doc_id
        """), {"doc_id": document_id})
        
        db.commit()
        
        return {"status": "success", "message": "File deleted"}
        
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
