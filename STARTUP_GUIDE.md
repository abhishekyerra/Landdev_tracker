# Step-by-Step Startup Guide

## Quick Start (2 Steps)

### Step 1: Start the Services

```bash
cd land-dev-tracker
docker-compose up -d
```

Wait about 15 seconds for all services to start.

### Step 2: Initialize the Database

```bash
chmod +x init-db.sh
./init-db.sh
```

That's it! Now access:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000/docs

**Login**: admin@landdev.com / Password123!

---

## Detailed Steps (If You Have Issues)

### 1. Clean Start (Recommended First Time)

```bash
# Remove any old containers and volumes
docker-compose down -v

# Remove old Docker images (optional)
docker system prune -f
```

### 2. Start PostgreSQL First

```bash
# Start only the database
docker-compose up -d postgres

# Wait for it to be ready (about 10 seconds)
sleep 10

# Check if it's running
docker-compose ps postgres
```

You should see:
```
NAME               STATUS          PORTS
landdev-postgres   Up 10 seconds   0.0.0.0:5432->5432/tcp
```

### 3. Verify Database is Accessible

```bash
# Try to connect
docker-compose exec postgres psql -U landdev_user -d landdev_tracker -c "SELECT version();"
```

If this works, you'll see PostgreSQL version info.

### 4. Start Backend

```bash
docker-compose up -d backend

# Check logs
docker-compose logs backend

# Should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

Test it: http://localhost:8000/api/health

### 5. Start Frontend

```bash
docker-compose up -d frontend

# Check logs
docker-compose logs frontend

# Should see:
# VITE ready in XXXms
# Local: http://localhost:3000/
```

Test it: http://localhost:3000

### 6. Initialize Database Schema

```bash
chmod +x init-db.sh
./init-db.sh
```

This will:
- Load the database schema (tables, views, indexes)
- Load seed data (phases, categories, sample users)

---

## Troubleshooting Specific Errors

### Error: "Container landdev-postgres exited (3)"

**Cause**: Database can't start, usually due to:
1. Port 5432 already in use
2. Corrupted data volume
3. Permission issues

**Solution**:

```bash
# 1. Check if port is in use
lsof -i :5432  # Mac/Linux
netstat -ano | findstr :5432  # Windows

# 2. Stop anything using port 5432
# Then try again with a clean slate:

docker-compose down -v
docker-compose up -d postgres

# 3. Check logs
docker-compose logs postgres
```

### Error: "failed to solve: process... exit code: 1" (Backend)

**Cause**: Python packages failed to install

**Solution**:

```bash
# Rebuild without cache
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Error: Frontend won't build

**Cause**: npm install failed

**Solution**:

```bash
# Rebuild without cache
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Error: "address already in use"

**Cause**: Ports 3000, 8000, or 5432 are being used

**Solution**:

```bash
# Find what's using the ports
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Stop the conflicting service
# OR edit docker-compose.yml to use different ports
```

---

## Manual Database Initialization

If the init-db.sh script doesn't work, do it manually:

```bash
# 1. Make sure postgres is running
docker-compose up -d postgres
sleep 10

# 2. Load schema
cat database/schema.sql | docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker

# 3. Load seed data
cat database/seed_data.sql | docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker

# 4. Verify tables were created
docker-compose exec postgres psql -U landdev_user -d landdev_tracker -c "\dt"
```

---

## Verification Checklist

After startup, verify everything is working:

```bash
# ✓ Check all containers are running
docker-compose ps

# Should see 3 containers with status "Up"

# ✓ Check database
docker-compose exec postgres psql -U landdev_user -d landdev_tracker -c "\dt"

# Should see list of tables

# ✓ Check backend
curl http://localhost:8000/api/health

# Should return: {"status":"healthy",...}

# ✓ Check frontend
curl http://localhost:3000

# Should return HTML

# ✓ Test login
# Open browser: http://localhost:3000
# Login with: admin@landdev.com / Password123!
```

---

## Common Issues and Solutions

### 1. "Cannot connect to Docker daemon"

```bash
# Start Docker Desktop (Mac/Windows)
# OR
sudo systemctl start docker  # Linux
```

### 2. Database won't start on Windows

```bash
# Use WSL2 for better compatibility
# OR
# Allocate more memory to Docker Desktop (Settings → Resources → Memory: 4GB+)
```

### 3. "permission denied" errors

```bash
# Make scripts executable
chmod +x setup.sh
chmod +x init-db.sh
```

### 4. Services start then immediately stop

```bash
# Check logs for specific errors
docker-compose logs

# Usually it's a configuration issue
# Verify .env files exist:
ls backend/.env
ls frontend/.env
```

---

## Complete Reset (Nuclear Option)

If nothing works, start completely fresh:

```bash
# 1. Stop everything
docker-compose down -v

# 2. Remove all Docker containers and images
docker system prune -a --volumes

# WARNING: This removes ALL Docker data, not just this project

# 3. Start fresh
docker-compose up --build
```

---

## Getting Help

If you're still stuck, run this diagnostic and share the output:

```bash
# Generate diagnostic report
echo "=== Docker Version ===" > diagnostic.txt
docker --version >> diagnostic.txt
docker-compose --version >> diagnostic.txt

echo "=== Container Status ===" >> diagnostic.txt
docker-compose ps >> diagnostic.txt

echo "=== PostgreSQL Logs ===" >> diagnostic.txt
docker-compose logs postgres >> diagnostic.txt

echo "=== Backend Logs ===" >> diagnostic.txt
docker-compose logs backend >> diagnostic.txt

echo "=== Frontend Logs ===" >> diagnostic.txt
docker-compose logs frontend >> diagnostic.txt

# Then share diagnostic.txt
```

---

## Success Indicators

When everything is working, you should see:

1. ✅ 3 containers running: `docker-compose ps`
2. ✅ Database tables exist: 15+ tables when you run `\dt` in psql
3. ✅ Backend responds: http://localhost:8000/api/health returns JSON
4. ✅ Frontend loads: http://localhost:3000 shows login page
5. ✅ Login works: Can log in with admin@landdev.com / Password123!

Good luck! 🚀
