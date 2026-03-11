"""
Daily Update Endpoint with AI Processing
Add this code to your main.py file
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import json
from rel_gpt import rel_gpt_client

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
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        phases = db.query(ProjectPhase).filter(ProjectPhase.project_id == project_id).all()
        tasks = db.query(Task).join(ProjectPhase).filter(ProjectPhase.project_id == project_id).all()
        
        # 2. Get current weather
        try:
            weather_response = await get_weather_for_location("Columbia, TN")
            weather_data = weather_response if weather_response else {}
        except:
            weather_data = {}
        
        # 3. Process with AI if available
        rel_gpt_api_key = os.getenv("REL_GPT_API_KEY")
        
        if rel_gpt_api_key:
            
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
Contractor: {current_user.get('first_name', '')} {current_user.get('last_name', '')}
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

            ai_response = rel_gpt_client.generate_text(
                user_prompt=context,
                max_tokens=2000,
            ) or ""
            
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
                "user_id": current_user['user_id'],
                "update_date": datetime.now().date(),
                "notes": update.notes,
                "blockers": update.blockers,
                "weather_impact": update.weather_impact,
                "crew_size": update.crew_size,
                "equipment_available": update.equipment_available,
                "ai_analysis": json.dumps(ai_analysis),
                "ai_recommendations": json.dumps(ai_analysis)
            })
            
            # 5. Auto-update phase progress based on task completion
            if active_phase:
                phase_tasks = [t for t in tasks if t.phase_id == active_phase.phase_id]
                if phase_tasks:
                    completed_count = len([t for t in phase_tasks if t.status == 'completed'])
                    new_completion = int((completed_count / len(phase_tasks)) * 100)
                    active_phase.completion_percentage = new_completion
            
            db.commit()
            
            return {
                "status": "success",
                "message": "Daily update processed with AI analysis",
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
                "user_id": current_user['user_id'],
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
                "message": "Daily update saved (AI analysis requires REL_GPT_API_KEY)",
                "analysis": {
                    "strategic_guidance": "Update saved successfully. Enable AI analysis by adding REL_GPT_API_KEY to environment variables."
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
