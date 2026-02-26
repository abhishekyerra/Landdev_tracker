"""
AI Agent Service for Construction Project Management
Uses Claude API to provide intelligent recommendations
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import json
from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)

class AIAgentService:
    """
    AI Agent that analyzes project status, weather, and constraints
    to provide intelligent task recommendations and guidance
    """
    
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if api_key:
            self.client = Anthropic(api_key=api_key)
            self.enabled = True
        else:
            logger.warning("ANTHROPIC_API_KEY not set - AI Agent will be disabled")
            self.enabled = False
    
    def get_project_recommendations(
        self,
        project_data: Dict,
        phases: List[Dict],
        current_phase_tasks: List[Dict],
        weather_data: Optional[Dict],
        budget_summary: Dict
    ) -> Dict:
        """
        Get AI-powered recommendations for the project
        
        Args:
            project_data: Project information
            phases: List of project phases with progress
            current_phase_tasks: Tasks in the current phase
            weather_data: Weather forecast and alerts
            budget_summary: Budget vs actual spending
            
        Returns:
            Dict with recommendations, reasoning, and priority tasks
        """
        
        if not self.enabled:
            return self._fallback_recommendations(current_phase_tasks, weather_data)
        
        try:
            # Build context for Claude
            context = self._build_context(
                project_data, phases, current_phase_tasks, 
                weather_data, budget_summary
            )
            
            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.7,
                system=self._get_system_prompt(),
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            # Parse response
            response_text = message.content[0].text
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                    recommendations = json.loads(json_str)
                else:
                    # If no JSON, structure the text response
                    recommendations = {
                        "recommendations": [{"task": "Review project status", "reasoning": response_text[:500]}],
                        "overall_guidance": response_text,
                        "priority_level": "medium"
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text
                recommendations = {
                    "recommendations": self._extract_recommendations_from_text(response_text),
                    "overall_guidance": response_text,
                    "priority_level": "medium"
                }
            
            # Add metadata
            recommendations['generated_at'] = datetime.utcnow().isoformat()
            recommendations['ai_powered'] = True
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self._fallback_recommendations(current_phase_tasks, weather_data)
    
    def _get_system_prompt(self) -> str:
        """System prompt for Claude defining its role as construction project advisor"""
        return """You are an expert construction project manager and advisor specializing in residential land development. Your role is to analyze project status, weather conditions, budget constraints, and timeline to provide actionable recommendations.

Your recommendations should:
1. Prioritize safety and quality
2. Consider weather impacts on construction activities
3. Balance budget constraints with timeline goals
4. Identify critical path items and dependencies
5. Suggest specific, actionable next steps
6. Explain your reasoning clearly

Respond in JSON format with this structure:
{
  "priority_tasks": [
    {
      "task_name": "Specific task to do next",
      "reasoning": "Why this task should be prioritized now",
      "estimated_duration": "Expected time to complete",
      "weather_dependency": "How weather affects this task",
      "budget_impact": "Cost implications"
    }
  ],
  "weather_considerations": "How current weather forecast affects work schedule",
  "budget_alert": "Any budget concerns or opportunities",
  "timeline_analysis": "Are we on track? Any concerns?",
  "overall_guidance": "High-level strategic guidance for the next week",
  "risks": ["List of current risks to address"],
  "opportunities": ["List of opportunities to leverage"]
}

Be specific, actionable, and focused on helping the team succeed."""
    
    def _build_context(
        self,
        project_data: Dict,
        phases: List[Dict],
        tasks: List[Dict],
        weather_data: Optional[Dict],
        budget_summary: Dict
    ) -> str:
        """Build context string for Claude"""
        
        # Get current phase
        current_phase = next((p for p in phases if p.get('status') == 'in_progress'), phases[0] if phases else None)
        
        # Get task status counts
        task_statuses = {}
        for task in tasks:
            status = task.get('status', 'unknown')
            task_statuses[status] = task_statuses.get(status, 0) + 1
        
        # Get overdue tasks
        overdue_tasks = []
        today = date.today()
        for task in tasks:
            if task.get('status') not in ['completed'] and task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(str(task['due_date'])).date()
                    if due_date < today:
                        overdue_tasks.append(task)
                except:
                    pass
        
        context = f"""# Project Analysis Request

## Project Overview
- **Project**: {project_data.get('project_name', 'Unknown')}
- **Location**: {project_data.get('location_city', '')}, {project_data.get('location_state', '')}
- **Total Scope**: {project_data.get('total_acres', 0)} acres, {project_data.get('description', '')}
- **Current Date**: {datetime.now().strftime('%Y-%m-%d')}

## Current Phase Status
- **Active Phase**: {current_phase.get('phase_name') if current_phase else 'None'}
- **Phase Progress**: {current_phase.get('completion_percentage', 0) if current_phase else 0}%
- **Planned End Date**: {current_phase.get('planned_end_date') if current_phase else 'N/A'}

## Task Status Summary
"""
        
        for status, count in task_statuses.items():
            context += f"- {status}: {count} tasks\n"
        
        if overdue_tasks:
            context += f"\n⚠️ **{len(overdue_tasks)} OVERDUE TASKS:**\n"
            for task in overdue_tasks[:5]:  # Show first 5
                context += f"- {task.get('task_name')} (due: {task.get('due_date')})\n"
        
        # Add upcoming tasks
        upcoming_tasks = [t for t in tasks if t.get('status') in ['todo', 'in_progress']][:10]
        if upcoming_tasks:
            context += "\n## Upcoming/In-Progress Tasks (Next 10)\n"
            for task in upcoming_tasks:
                context += f"- {task.get('task_name')} - {task.get('status')} - Priority: {task.get('priority')} - Due: {task.get('due_date')}\n"
        
        # Add budget info
        context += f"""
## Budget Status
- **Total Budget**: ${budget_summary.get('total_budgeted', 0):,.2f}
- **Spent to Date**: ${budget_summary.get('total_spent', 0):,.2f}
- **Remaining**: ${budget_summary.get('remaining_budget', 0):,.2f}
- **Budget Utilization**: {budget_summary.get('budget_utilization_percentage', 0):.1f}%
"""
        
        # Add weather info
        if weather_data:
            context += "\n## Weather Forecast (Next 3 Days)\n"
            
            if weather_data.get('current'):
                current = weather_data['current']
                context += f"**Current**: {current.get('temperature')}°F, {current.get('conditions')}\n\n"
            
            if weather_data.get('alerts'):
                context += "**Weather Alerts:**\n"
                for alert in weather_data['alerts'][:3]:
                    context += f"- {alert.get('message')}\n"
                context += "\n"
            
            if weather_data.get('forecast'):
                context += "**Forecast:**\n"
                for day in weather_data['forecast'][:6]:  # 3 days (day + night)
                    if day.get('is_daytime'):
                        context += f"- {day.get('name')}: {day.get('temperature')}°F, {day.get('short_forecast')}, {day.get('precipitation_probability', 0)}% rain\n"
        
        context += """

## Your Task
Analyze this project status and provide specific, actionable recommendations for:
1. What tasks should be prioritized in the next 3-7 days
2. How weather will impact the schedule
3. Any budget concerns or timeline risks
4. Strategic guidance for keeping the project on track

Focus on being specific and actionable. Consider weather, budget, and timeline constraints."""
        
        return context
    
    def _extract_recommendations_from_text(self, text: str) -> List[Dict]:
        """Extract recommendations from free-form text response"""
        # Simple extraction - split by lines and look for actionable items
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                recommendations.append({
                    "task": line.lstrip('-•* '),
                    "reasoning": "AI analysis suggests this task",
                    "priority": "medium"
                })
        
        return recommendations[:5] if recommendations else [
            {"task": "Review current project status", "reasoning": text[:200], "priority": "medium"}
        ]
    
    def _fallback_recommendations(
        self, 
        tasks: List[Dict], 
        weather_data: Optional[Dict]
    ) -> Dict:
        """Fallback recommendations when AI is not available"""
        
        # Get overdue and high-priority tasks
        priority_tasks = []
        today = date.today()
        
        for task in tasks:
            if task.get('status') == 'completed':
                continue
                
            priority_score = 0
            
            # Check if overdue
            if task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(str(task['due_date'])).date()
                    if due_date < today:
                        priority_score += 10
                    elif due_date <= today + timedelta(days=7):
                        priority_score += 5
                except:
                    pass
            
            # Check priority
            if task.get('priority') == 'critical':
                priority_score += 8
            elif task.get('priority') == 'high':
                priority_score += 5
            
            # Check status
            if task.get('status') == 'in_progress':
                priority_score += 3
            
            if priority_score > 0:
                priority_tasks.append({
                    'task': task,
                    'score': priority_score
                })
        
        # Sort by priority score
        priority_tasks.sort(key=lambda x: x['score'], reverse=True)
        
        recommendations = []
        for item in priority_tasks[:5]:
            task = item['task']
            recommendations.append({
                "task_name": task.get('task_name'),
                "reasoning": f"Priority: {task.get('priority')}, Status: {task.get('status')}",
                "due_date": str(task.get('due_date')),
                "priority": task.get('priority')
            })
        
        return {
            "priority_tasks": recommendations,
            "overall_guidance": "Focus on completing overdue and high-priority tasks. Monitor weather conditions for outdoor work.",
            "ai_powered": False,
            "generated_at": datetime.utcnow().isoformat(),
            "note": "AI Agent not configured - showing rule-based recommendations"
        }

# Create singleton instance
ai_agent = AIAgentService()
