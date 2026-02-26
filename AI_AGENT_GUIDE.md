# 🤖 AI Agent Installation Guide

## What You're Getting

Your app now has an **AI-powered project advisor** that analyzes:
- ✅ Current project progress
- ✅ Upcoming weather forecast  
- ✅ Budget status and constraints
- ✅ Timeline and schedule risks
- ✅ Task dependencies and priorities

And provides:
- 🎯 **Prioritized task recommendations**
- 💡 **Strategic guidance** for the next week
- ⚠️ **Risk identification** and mitigation
- ✨ **Opportunity detection**
- 🌤️ **Weather-aware scheduling**
- 💰 **Budget-conscious planning**

## 📦 Files to Update

### New Files:
- `backend/ai_agent.py` (NEW - AI Agent service)

### Updated Files:
- `backend/requirements.txt` (added anthropic SDK)
- `backend/main.py` (added AI endpoints)
- `backend/.env` (added ANTHROPIC_API_KEY)
- `frontend/src/App.jsx` (added AI recommendations widget)

## 🔑 Get Your API Key (Required for AI Features)

1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Go to API Keys section
4. Create a new key
5. Copy the key (starts with `sk-ant-...`)

## 🚀 Installation

### Step 1: Copy Files

```bash
# Copy new AI agent file
cp land-dev-tracker/backend/ai_agent.py /your/existing/backend/

# Update these files:
cp land-dev-tracker/backend/requirements.txt /your/existing/backend/
cp land-dev-tracker/backend/main.py /your/existing/backend/
cp land-dev-tracker/frontend/src/App.jsx /your/existing/frontend/src/
```

### Step 2: Add API Key

Edit `backend/.env`:
```bash
# Add this line with your actual API key:
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 3: Rebuild Backend

```bash
# Stop backend
docker-compose stop backend

# Rebuild with new dependencies (anthropic SDK)
docker-compose build --no-cache backend

# Start backend
docker-compose up -d backend
```

### Step 4: Restart Frontend

```bash
docker-compose restart frontend
```

### Step 5: Wait and Test

```bash
# Wait 30 seconds
sleep 30

# Check logs
docker-compose logs backend --tail=20
```

## 🎯 Using the AI Agent

### In the App:

1. Go to http://localhost:3000
2. Click on **Columbia 60-Lot Development**
3. Scroll down - you'll see the **🤖 AI Project Advisor** widget!

The AI will show:
- **Strategic Guidance** - High-level advice for the week
- **Recommended Next Tasks** - Specific tasks to prioritize
- **Weather Impact** - How weather affects your schedule
- **Budget Status** - Budget concerns or opportunities
- **Timeline Status** - Are you on track?
- **Risks** - Things to watch out for
- **Opportunities** - Things to leverage

### Example AI Output:

```
📋 Strategic Guidance:
"Focus on completing utility installations before the forecasted rain on Thursday. 
The grading work is ahead of schedule, which provides a buffer for weather delays. 
Consider accelerating road base installation while conditions are favorable."

⭐ Recommended Next Tasks:
1. Install Sewer Lines - Phase 1
   Reasoning: Critical path item, weather window available, budget allows
   Weather: Complete before Thursday rain
   Est: 3-4 days

2. Complete Water Service Laterals
   Reasoning: Dependent on sewer completion, required for final inspection
   Est: 2 days

3. Schedule Road Base Delivery
   Reasoning: Weather favorable next week, crew available
   Budget: On track
```

## 🔧 API Endpoints

### Get AI Recommendations
```
GET /api/ai/recommendations/{project_id}
Authorization: Bearer {token}
```

Returns comprehensive analysis and recommendations.

## 💡 AI Agent Features

### Context-Aware Analysis

The AI considers:
- **Your specific project** (Columbia 60-Lot Development)
- **Current phase status** (Phase 1 at 15%)
- **Task status** (overdue, in-progress, upcoming)
- **Weather forecast** (next 3-7 days)
- **Budget utilization** (spent vs remaining)
- **Timeline constraints** (planned vs actual dates)

### Intelligent Recommendations

The AI provides:
- **Specific tasks** to do next (not generic advice)
- **Reasoning** for each recommendation
- **Weather dependencies** for outdoor work
- **Budget implications** of decisions
- **Risk mitigation** strategies
- **Opportunity identification**

### Adaptive Guidance

The AI adapts to:
- **Project status** (different advice when behind vs ahead)
- **Weather changes** (rain → indoor work)
- **Budget constraints** (cost-saving suggestions when over budget)
- **Timeline pressure** (critical path focus when behind)

## 🔍 Without API Key

If you don't set ANTHROPIC_API_KEY, the agent falls back to:
- **Rule-based recommendations** (still useful!)
- Priority sorting by due date and priority level
- Weather-aware suggestions
- Overdue task highlighting

You'll see a note: "AI Agent not configured - showing rule-based recommendations"

## 💰 Cost Considerations

Anthropic Claude API pricing (as of Dec 2024):
- **Claude Sonnet**: ~$3 per million input tokens, ~$15 per million output tokens
- **Typical recommendation call**: ~1,500 input tokens + 800 output tokens
- **Cost per recommendation**: ~$0.01-0.02
- **Daily usage** (5-10 requests): ~$0.05-0.20/day
- **Monthly cost**: $1.50-6.00/month

Very affordable for the value!

## 🎨 Customization

### Adjust AI Behavior

Edit `backend/ai_agent.py`:

**Change System Prompt** (line 100):
Modify the instructions to change how the AI thinks about your project.

**Adjust Context** (line 150):
Change what information is sent to the AI.

**Modify Output Format** (line 90):
Change the JSON structure of recommendations.

### Add More Data Sources

You can enhance the AI by adding:
- Equipment availability
- Crew schedule
- Material delivery dates
- Inspection schedules
- Contractor performance metrics

## 🐛 Troubleshooting

### AI Not Showing?

```bash
# Check if ANTHROPIC_API_KEY is set
docker-compose exec backend printenv | grep ANTHROPIC

# If empty, add to backend/.env and restart:
docker-compose restart backend
```

### API Key Invalid?

Error: "Authentication error"
- Check that your API key starts with `sk-ant-`
- Verify no extra spaces in .env file
- Make sure you copied the full key

### AI Too Slow?

If AI responses take >10 seconds:
- Normal for first call (model loading)
- Subsequent calls should be 2-3 seconds
- Check your internet connection
- Consider caching recommendations

### Want Faster/Cheaper?

Change model in `ai_agent.py` line 115:
```python
model="claude-haiku-20240307",  # Faster, cheaper ($0.25/million tokens)
```

## 🚀 Next Steps

Now that you have AI recommendations, you can:

1. **Automated Scheduling** - Auto-update tasks based on AI suggestions
2. **Push Notifications** - Alert team when priorities change
3. **Learning System** - Train AI on your specific project patterns
4. **Multi-Project** - Compare AI recommendations across projects
5. **Integration** - Connect to Procore, Buildertrend, or other tools

Want me to build any of these? 🤖
