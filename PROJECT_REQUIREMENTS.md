# Columbia 60-Lot Development Project - Requirements

## Project Overview
- **Location**: Columbia, TN 38401
- **Total Lots**: 60 residential lots
- **Total Acreage**: 40 acres
- **Delivery Model**: Phased delivery to builder (20 lots per phase)

## Budget
- **Land Cost**: $2,200,000
- **Development Cost**: $4,000,000
- **Total Budget**: $6,200,000

## Timeline
- **Total Duration**: 18 months
- **Phase Duration**: 6 months per phase

## Phase Structure

### Phase 1: Lots 1-20 (Months 1-6)
- Site preparation and clearing
- Mass grading
- Underground utilities (water, sewer, storm)
- Gas, electric, telecom installation
- Road construction and paving
- Final grading and landscaping
- **Deliverable**: 20 ready-to-build lots to builder

### Phase 2: Lots 21-40 (Months 7-12)
- Infrastructure for second 20 lots
- **Deliverable**: 20 ready-to-build lots to builder

### Phase 3: Lots 41-60 (Months 13-18)
- Infrastructure for final 20 lots
- **Deliverable**: 20 ready-to-build lots to builder

## Key Requirements

### Contractor Interface
- Daily task completion updates
- Progress tracking
- Status updates on each task

### Weather Integration
- Weather forecast for Columbia, TN 38401
- Weather-based task recommendations
- Optimal scheduling based on conditions

### AI Agent Features
- Analyze current project progress
- Consider weather forecast
- Generate next task recommendations
- Balance budget vs timeline
- Provide reasoning for suggestions
- Guide optimal project completion

### Lot Delivery Tracking
- Mark lots as "ready for builder"
- Track which lots are delivered
- Phase completion milestones
- Builder handoff documentation

## Current Status
- **Phase 1**: In Progress (15% complete)
- Land purchased
- Master plan submitted
- Site clearing underway
- Ready to begin full development

## Technology Stack
- Database: PostgreSQL
- Backend: Python FastAPI
- Frontend: React
- Deployment: Docker → GCP Cloud Run
- Weather API: To be integrated
- AI: Claude API for recommendations

## Next Steps
1. ✅ Load Phase 1 project data
2. Build contractor daily update interface
3. Integrate weather API for Columbia TN
4. Implement AI recommendation engine
5. Add lot delivery tracking
6. Deploy to GCP
