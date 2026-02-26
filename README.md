# Land Development Project Tracker

A comprehensive web application for tracking land development projects, managing phases, milestones, and budgets. Built specifically for land developers and project managers.

## 🎯 Key Features

### Phase & Milestone Tracking
- **10 Standard Development Phases**: From Land Acquisition to Project Closeout
- **Milestone Management**: Track critical milestones within each phase
- **Progress Monitoring**: Visual progress indicators and completion percentages
- **Dependencies**: Define task and milestone dependencies
- **Status Tracking**: Real-time status updates for phases and milestones

### Budget Management
- **Hierarchical Budget Categories**: Organize budgets by major categories and subcategories
- **Budget Allocation**: Assign budgets by project phase and category
- **Contingency Planning**: Automatic contingency calculations
- **Expense Tracking**: Record and track actual expenses against budget
- **Budget vs Actual**: Real-time budget utilization and variance reporting
- **Financial Dashboards**: Comprehensive budget summaries and analytics

### Project Management
- **Project Dashboard**: Overview of all projects with key metrics
- **Project Details**: Track location, zoning, acreage, and project type
- **Team Management**: Assign team members and vendors to projects
- **Document Management**: Store and organize project documents
- **Timeline Tracking**: Monitor planned vs actual dates

## 🏗️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Documentation**: Auto-generated with OpenAPI/Swagger

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **State Management**: Zustand + React Query
- **UI Components**: Headless UI + Tailwind CSS
- **Charts**: Recharts
- **Build Tool**: Vite

### Infrastructure
- **Cloud Platform**: Google Cloud Platform (GCP)
- **Database**: Cloud SQL (PostgreSQL)
- **Backend Hosting**: Cloud Run
- **Frontend Hosting**: Cloud Run
- **File Storage**: Cloud Storage
- **Containerization**: Docker

## 📁 Project Structure

```
land-dev-tracker/
├── backend/                    # FastAPI backend application
│   ├── main.py                # Application entry point
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Pydantic schemas for validation
│   ├── database.py            # Database configuration
│   ├── auth.py                # Authentication utilities
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend Docker configuration
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── App.jsx           # Main application component
│   │   ├── components/       # Reusable React components
│   │   ├── pages/            # Page components
│   │   ├── store/            # State management
│   │   └── utils/            # Utility functions
│   ├── package.json          # Node.js dependencies
│   └── Dockerfile           # Frontend Docker configuration
├── database/                  # Database schemas and migrations
│   ├── schema.sql            # Complete database schema
│   └── seed_data.sql         # Initial seed data
├── deployment/               # Deployment configurations
│   └── gcp-cloud-run.yaml   # GCP Cloud Run configuration
├── docs/                     # Documentation
│   └── GCP_DEPLOYMENT_GUIDE.md
├── docker-compose.yml        # Local development environment
└── README.md                # This file
```

## 🚀 Quick Start

### Option 1: Local Development with Docker (Recommended for Database Professionals)

```bash
# Clone the repository
git clone <repository-url>
cd land-dev-tracker

# Start all services with Docker Compose
docker-compose up -d

# The application will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - PostgreSQL: localhost:5432
```

**Default Login Credentials:**
- Email: `admin@landdev.com`
- Password: `Password123!`

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cat > .env << EOF
DATABASE_URL=postgresql://landdev_user:landdev_password@localhost:5432/landdev_tracker
SECRET_KEY=your-secret-key-here
EOF

# Run the backend
uvicorn main:app --reload --port 8000
```

#### Database Setup

```bash
# Create PostgreSQL database
createdb landdev_tracker

# Run schema
psql landdev_tracker < ../database/schema.sql

# Run seed data
psql landdev_tracker < ../database/seed_data.sql
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cat > .env << EOF
VITE_API_URL=http://localhost:8000
EOF

# Run the frontend
npm run dev
```

## 🗄️ Database Schema Highlights

### Core Tables
- **projects**: Main project information and metadata
- **project_phases**: Development phases with timeline tracking
- **milestones**: Critical milestones within phases
- **project_budgets**: Budget allocations by category and phase
- **expenses**: Actual expense tracking
- **budget_categories**: Hierarchical budget organization

### Key Views
- **v_project_budget_summary**: Budget vs actual spending by project
- **v_project_phase_progress**: Phase completion and milestone tracking
- **v_project_dashboard**: Comprehensive project health metrics

### Database Features
- UUID primary keys for distributed systems
- Comprehensive foreign key relationships
- Check constraints for data integrity
- Automatic timestamp updates via triggers
- Generated columns for calculations
- Full-text search capabilities
- Optimized indexes for performance

## 📊 Key Workflows

### Creating a New Project

1. **Create Project**: Define basic project information
2. **Set Up Phases**: Add standard or custom development phases
3. **Define Milestones**: Create key milestones for each phase
4. **Allocate Budget**: Set budgets by category and phase
5. **Track Progress**: Update phase status and milestone completion
6. **Record Expenses**: Log actual costs against budget

### Budget Management Workflow

1. **Create Budget Categories**: Organize spending categories
2. **Allocate Phase Budgets**: Assign budget to each phase
3. **Add Line Items**: Detail specific budget items
4. **Record Expenses**: Track actual spending
5. **Monitor Variance**: Review budget vs actual reports
6. **Adjust as Needed**: Create change orders for budget modifications

## 🎨 UI Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Live data updates with React Query
- **Interactive Charts**: Visual budget and progress tracking
- **Quick Actions**: Streamlined workflows for common tasks
- **Search & Filter**: Easy project and data discovery
- **Export Options**: Generate reports and export data

## 🔒 Security

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password encryption
- **Role-Based Access**: Multi-level user permissions
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **CORS Configuration**: Controlled cross-origin requests
- **Secrets Management**: Environment-based configuration

## 📈 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Phases
- `POST /api/projects/{id}/phases` - Create phase
- `GET /api/projects/{id}/phases` - List project phases
- `PUT /api/phases/{id}` - Update phase

### Milestones
- `POST /api/phases/{id}/milestones` - Create milestone
- `GET /api/phases/{id}/milestones` - List phase milestones
- `PUT /api/milestones/{id}` - Update milestone

### Budget
- `POST /api/projects/{id}/budgets` - Create budget
- `GET /api/projects/{id}/budgets` - List project budgets
- `GET /api/projects/{id}/budget-summary` - Get budget summary

### Expenses
- `POST /api/projects/{id}/expenses` - Record expense
- `GET /api/projects/{id}/expenses` - List project expenses

### Dashboard
- `GET /api/dashboard/overview` - Overall statistics
- `GET /api/dashboard/projects` - Project dashboard data

Full API documentation available at: `http://localhost:8000/docs`

## 🌐 Deployment to GCP

See the comprehensive [GCP Deployment Guide](docs/GCP_DEPLOYMENT_GUIDE.md) for step-by-step instructions.

### Quick Deploy

```bash
# Set your GCP project
export PROJECT_ID="your-project-id"

# Enable APIs
gcloud services enable sqladmin.googleapis.com run.googleapis.com

# Create database
gcloud sql instances create landdev-db --region=us-central1

# Build and deploy
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/landdev-backend
gcloud run deploy landdev-backend --image gcr.io/$PROJECT_ID/landdev-backend

cd ../frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/landdev-frontend
gcloud run deploy landdev-frontend --image gcr.io/$PROJECT_ID/landdev-frontend
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```

## 📝 Common Database Queries

### Get Project Budget Utilization
```sql
SELECT * FROM v_project_budget_summary 
WHERE project_id = 'your-project-id';
```

### Get Overdue Milestones
```sql
SELECT * FROM milestones 
WHERE status != 'completed' 
AND due_date < CURRENT_DATE 
ORDER BY due_date;
```

### Get Phase Progress
```sql
SELECT * FROM v_project_phase_progress 
WHERE project_id = 'your-project-id' 
ORDER BY phase_order;
```

## 🤝 Contributing

As a database professional, you can contribute by:
1. Optimizing database queries
2. Creating new analytical views
3. Adding database indexes
4. Suggesting schema improvements
5. Writing stored procedures for complex operations

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Review API documentation: `http://localhost:8000/docs`
3. Database access: `psql -h localhost -U landdev_user landdev_tracker`

## 🎯 Next Steps

1. ✅ Review the database schema
2. ✅ Start the application with Docker Compose
3. ✅ Login with default credentials
4. ✅ Create your first project
5. ✅ Set up phases and milestones
6. ✅ Allocate budget and track expenses
7. ✅ Deploy to GCP when ready

---

Built with ❤️ for land development professionals
