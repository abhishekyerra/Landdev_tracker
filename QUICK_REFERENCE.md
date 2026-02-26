# Quick Reference Guide - Land Development Tracker

## 🚀 Getting Started in 3 Steps

### Step 1: Extract Files
```bash
# Extract the land-dev-tracker folder to your preferred location
cd /path/to/land-dev-tracker
```

### Step 2: Run Setup
```bash
# Make setup script executable (Mac/Linux)
chmod +x setup.sh

# Run setup
./setup.sh
```

### Step 3: Access Application
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Login**: admin@landdev.com / Password123!

## 📊 Key Files for Database Professionals

| File | Purpose |
|------|---------|
| `database/schema.sql` | Complete PostgreSQL schema with 15+ tables |
| `database/seed_data.sql` | Initial data (phases, categories, users) |
| `docs/DATABASE_DOCUMENTATION.md` | Comprehensive database guide |
| `backend/models.py` | SQLAlchemy ORM models |
| `docker-compose.yml` | Local development environment |

## 🗄️ Database Quick Commands

```bash
# Connect to database
docker-compose exec postgres psql -U landdev_user landdev_tracker

# View all tables
\dt

# Describe a table
\d+ projects

# Run a query
SELECT * FROM v_project_dashboard;

# Exit
\q
```

## 🔑 Important Tables

1. **projects** - Main project information
2. **project_phases** - Development phases with progress tracking
3. **milestones** - Critical milestones within phases
4. **project_budgets** - Budget allocations by phase/category
5. **expenses** - Actual expense tracking
6. **budget_categories** - Hierarchical budget categories

## 📈 Key Views (Pre-built Reports)

```sql
-- Budget summary
SELECT * FROM v_project_budget_summary;

-- Phase progress
SELECT * FROM v_project_phase_progress;

-- Project dashboard
SELECT * FROM v_project_dashboard;
```

## 🛠️ Common Operations

### View Logs
```bash
docker-compose logs -f
docker-compose logs backend
docker-compose logs postgres
```

### Stop/Start
```bash
docker-compose down        # Stop all services
docker-compose up -d       # Start all services
docker-compose restart     # Restart services
```

### Access Services
```bash
# Backend API shell
docker-compose exec backend bash

# Database shell
docker-compose exec postgres bash
```

## 📝 Default Users

| Email | Password | Role |
|-------|----------|------|
| admin@landdev.com | Password123! | admin |
| pm@landdev.com | Password123! | project_manager |
| developer@landdev.com | Password123! | developer |
| contractor@landdev.com | Password123! | contractor |

## 🌐 GCP Deployment

See `docs/GCP_DEPLOYMENT_GUIDE.md` for complete instructions.

Quick checklist:
1. ✅ Create GCP project
2. ✅ Enable APIs (Cloud Run, Cloud SQL, Cloud Storage)
3. ✅ Create Cloud SQL database
4. ✅ Build and push Docker images
5. ✅ Deploy to Cloud Run
6. ✅ Configure environment variables

## 📞 Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Clear Docker cache
docker-compose down -v
docker-compose up --build
```

### Database connection issues
```bash
# Check database logs
docker-compose logs postgres

# Verify database is running
docker-compose ps

# Restart database
docker-compose restart postgres
```

### Can't access frontend
- Check if http://localhost:3000 loads
- Check frontend logs: `docker-compose logs frontend`
- Verify backend is running: http://localhost:8000/api/health

## 🎯 Next Steps

1. ✅ Explore the database schema
2. ✅ Test the API at /docs endpoint
3. ✅ Create a test project in the UI
4. ✅ Review sample queries in documentation
5. ✅ Customize for your needs

## 📚 Documentation Index

- `README.md` - Complete project overview
- `PROJECT_SUMMARY.md` - What's included and how to use
- `docs/GCP_DEPLOYMENT_GUIDE.md` - Deploy to Google Cloud
- `docs/DATABASE_DOCUMENTATION.md` - Database guide
- `database/schema.sql` - Full schema with comments

## 💡 Pro Tips

1. **Learn the schema first** - Study `schema.sql` to understand relationships
2. **Use the views** - Pre-built analytical views save time
3. **Check the API docs** - Interactive docs at /docs endpoint
4. **Explore seed data** - See examples in `seed_data.sql`
5. **Monitor performance** - Use EXPLAIN ANALYZE for queries

## ✅ Verification Checklist

After setup, verify:
- [ ] Can access http://localhost:3000
- [ ] Can login with admin credentials
- [ ] Can access http://localhost:8000/docs
- [ ] Can connect to database via psql
- [ ] Can see default data (phase templates, categories)

If all checked, you're ready to go! 🎉
