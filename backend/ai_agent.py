"""
AI Agent Service for Construction Project Management.
Uses Rel GPT to provide intelligent recommendations.
"""

from datetime import date, datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

from rel_gpt import rel_gpt_client

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    AI Agent that analyzes project status, weather, and constraints
    to provide intelligent task recommendations and guidance.
    """

    def __init__(self):
        self.enabled = rel_gpt_client.enabled

    def get_project_recommendations(
        self,
        project_data: Dict,
        phases: List[Dict],
        current_phase_tasks: List[Dict],
        weather_data: Optional[Dict],
        budget_summary: Dict,
    ) -> Dict:
        """Get AI-powered recommendations for the project."""
        if not self.enabled:
            return self._fallback_recommendations(current_phase_tasks)

        context = self._build_context(
            project_data, phases, current_phase_tasks, weather_data, budget_summary
        )

        response = rel_gpt_client.generate_json(
            user_prompt=context,
            system_prompt=self._get_system_prompt(),
            max_tokens=2000,
            temperature=0.4,
        )

        if not response:
            return self._fallback_recommendations(current_phase_tasks)

        if isinstance(response, list):
            recommendations = {
                "priority_tasks": response[:5],
                "overall_guidance": "Rel GPT returned task-focused recommendations.",
            }
        else:
            recommendations = response

        recommendations["generated_at"] = datetime.utcnow().isoformat()
        recommendations["ai_powered"] = True
        recommendations["provider"] = "rel-gpt"
        return recommendations

    def _get_system_prompt(self) -> str:
        return """You are an expert construction project manager and advisor specializing in residential land development.

Prioritize safety, weather-aware planning, budget control, and timeline risk reduction.
Respond in strict JSON with:
{
  "priority_tasks": [
    {
      "task_name": "Specific task to do next",
      "reasoning": "Why this should be prioritized",
      "estimated_duration": "Expected time to complete",
      "weather_dependency": "How weather affects this task",
      "budget_impact": "Cost implications"
    }
  ],
  "resource_plan": {
    "recommended_crew_size": "Suggested crew size for next 3-7 days",
    "next_equipment_needed": ["List of next equipment needed"],
    "upcoming_tasks_budget_estimate": "Approximate budget for upcoming tasks"
  },
  "upcoming_tasks": [
    {
      "task_name": "Task to execute soon",
      "target_phase": "Phase name",
      "budget_estimate": "Approximate cost"
    }
  ],
  "weather_considerations": "How weather affects schedule",
  "budget_alert": "Budget concerns or opportunities",
  "timeline_analysis": "Timeline status and concerns",
  "overall_guidance": "Strategic guidance for next week",
  "risks": ["List of risks"],
  "opportunities": ["List of opportunities"]
}"""

    def _build_context(
        self,
        project_data: Dict,
        phases: List[Dict],
        tasks: List[Dict],
        weather_data: Optional[Dict],
        budget_summary: Dict,
    ) -> str:
        current_phase = next(
            (p for p in phases if p.get("status") == "in_progress"),
            phases[0] if phases else None,
        )

        task_statuses = {}
        for task in tasks:
            status = task.get("status", "unknown")
            task_statuses[status] = task_statuses.get(status, 0) + 1

        overdue_tasks = []
        today = date.today()
        for task in tasks:
            if task.get("status") == "completed" or not task.get("due_date"):
                continue
            try:
                due_date = datetime.fromisoformat(str(task["due_date"])).date()
                if due_date < today:
                    overdue_tasks.append(task)
            except Exception:
                continue

        context = f"""# Project Analysis Request

## Project Overview
- Project: {project_data.get('project_name', 'Unknown')}
- Location: {project_data.get('location_city', '')}, {project_data.get('location_state', '')}
- Total Scope: {project_data.get('total_acres', 0)} acres
- Current Date: {datetime.now().strftime('%Y-%m-%d')}

## Current Phase Status
- Active Phase: {current_phase.get('phase_name') if current_phase else 'None'}
- Phase Progress: {current_phase.get('completion_percentage', 0) if current_phase else 0}%
- Planned End Date: {current_phase.get('planned_end_date') if current_phase else 'N/A'}

## Task Status Summary
"""

        for status, count in task_statuses.items():
            context += f"- {status}: {count} tasks\n"

        if overdue_tasks:
            context += f"\nOverdue tasks ({len(overdue_tasks)}):\n"
            for task in overdue_tasks[:5]:
                context += f"- {task.get('task_name')} (due: {task.get('due_date')})\n"

        upcoming_tasks = [t for t in tasks if t.get("status") in ["todo", "in_progress"]][:10]
        if upcoming_tasks:
            context += "\n## Upcoming/In-Progress Tasks\n"
            for task in upcoming_tasks:
                context += (
                    f"- {task.get('task_name')} | {task.get('status')} | "
                    f"Priority: {task.get('priority')} | Due: {task.get('due_date')}\n"
                )

        context += f"""
## Budget Status
- Total Budget: ${budget_summary.get('total_budgeted', 0):,.2f}
- Spent to Date: ${budget_summary.get('total_spent', 0):,.2f}
- Remaining: ${budget_summary.get('remaining_budget', 0):,.2f}
- Budget Utilization: {budget_summary.get('budget_utilization_percentage', 0):.1f}%
"""

        if weather_data:
            context += "\n## Weather\n"
            if weather_data.get("current"):
                current = weather_data["current"]
                context += f"- Current: {current.get('temperature')}F, {current.get('conditions')}\n"

            if weather_data.get("alerts"):
                context += "- Alerts:\n"
                for alert in weather_data["alerts"][:3]:
                    context += f"  - {alert.get('message')}\n"

            if weather_data.get("forecast"):
                context += "- Forecast:\n"
                for day in weather_data["forecast"][:6]:
                    if day.get("is_daytime"):
                        context += (
                            f"  - {day.get('name')}: {day.get('temperature')}F, "
                            f"{day.get('short_forecast')}, {day.get('precipitation_probability', 0)}% rain\n"
                        )

        context += """
Provide specific, actionable recommendations for the next 3-7 days.
"""
        return context

    def _fallback_recommendations(self, tasks: List[Dict]) -> Dict:
        """Fallback recommendations when AI is unavailable."""
        priority_tasks = []
        today = date.today()

        for task in tasks:
            if task.get("status") == "completed":
                continue

            priority_score = 0
            if task.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(str(task["due_date"])).date()
                    if due_date < today:
                        priority_score += 10
                    elif due_date <= today + timedelta(days=7):
                        priority_score += 5
                except Exception:
                    pass

            if task.get("priority") == "critical":
                priority_score += 8
            elif task.get("priority") == "high":
                priority_score += 5

            if task.get("status") == "in_progress":
                priority_score += 3

            if priority_score > 0:
                priority_tasks.append({"task": task, "score": priority_score})

        priority_tasks.sort(key=lambda item: item["score"], reverse=True)
        recommendations = []
        for item in priority_tasks[:5]:
            task = item["task"]
            recommendations.append(
                {
                    "task_name": task.get("task_name"),
                    "reasoning": f"Priority: {task.get('priority')}, Status: {task.get('status')}",
                    "due_date": str(task.get("due_date")),
                    "priority": task.get("priority"),
                }
            )

        return {
            "priority_tasks": recommendations,
            "overall_guidance": "Focus on overdue and high-priority tasks; align outdoor work with weather windows.",
            "resource_plan": {
                "recommended_crew_size": "6-8 field crew + 1 supervisor",
                "next_equipment_needed": [
                    "Excavator",
                    "Skid steer",
                    "Compactor",
                    "Survey layout tools",
                ],
                "upcoming_tasks_budget_estimate": "Approx. $75,000-$150,000 for next 2 weeks (rule-based)",
            },
            "upcoming_tasks": [
                {
                    "task_name": t.get("task_name"),
                    "target_phase": "Current active phase",
                    "budget_estimate": "TBD - derive from budget line items",
                }
                for t in tasks[:5]
            ],
            "ai_powered": False,
            "generated_at": datetime.utcnow().isoformat(),
            "provider": "rule-based",
            "note": "Rel GPT not configured - showing rule-based recommendations",
        }


ai_agent = AIAgentService()
