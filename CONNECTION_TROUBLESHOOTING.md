# Fixing "Unable to Connect to Server" Error

## Quick Fix (Most Common Solution)

The frontend needs to be rebuilt after starting to pick up environment variables:

```bash
# Restart the frontend container
docker-compose restart frontend

# Wait 30 seconds, then reload http://localhost:3000
```

## Detailed Troubleshooting

### Step 1: Verify Backend is Running

```bash
# Check if backend is responding
curl http://localhost:8000/api/health

# Should return: {"status":"healthy","timestamp":"..."}
```

**If this fails:**
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Step 2: Check Browser Console

1. Open http://localhost:3000
2. Open browser developer tools (F12)
3. Go to Console tab
4. Look for errors like:
   - `Failed to fetch`
   - `CORS error`
   - `net::ERR_CONNECTION_REFUSED`

### Step 3: Test from Browser

Open http://localhost:8000/docs in your browser. If this loads, the backend is working.

### Step 4: Rebuild Frontend

The frontend might have cached the old API URL:

```bash
# Stop frontend
docker-compose stop frontend

# Rebuild without cache
docker-compose build --no-cache frontend

# Start frontend
docker-compose up -d frontend

# Wait 30 seconds
sleep 30

# Try again: http://localhost:3000
```

### Step 5: Check Environment Variables

```bash
# Check frontend environment
docker-compose exec frontend env | grep VITE

# Should show:
# VITE_API_URL=http://localhost:8000
```

**If missing or wrong:**
```bash
# Edit frontend/.env
nano frontend/.env

# Make sure it contains:
# VITE_API_URL=http://localhost:8000

# Then rebuild:
docker-compose restart frontend
```

### Step 6: Run Diagnostic Script

```bash
chmod +x diagnose.sh
./diagnose.sh
```

This will test all connections and show you exactly what's wrong.

## Common Issues

### Issue 1: Backend shows "offline" on login page

**Cause**: Backend isn't running or wrong port

**Fix**:
```bash
# Check what's running
docker-compose ps

# All 3 should show "Up"
# If backend is "Exit" or missing:
docker-compose up -d backend
docker-compose logs backend
```

### Issue 2: CORS error in browser console

**Cause**: Backend CORS not configured (but it should be)

**Fix**:
```bash
# Restart backend
docker-compose restart backend

# Check logs
docker-compose logs backend | grep CORS
```

### Issue 3: Wrong API URL

**Cause**: Frontend using wrong URL (cached)

**Fix**:
```bash
# Clear browser cache
# Hard reload: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

# Or rebuild frontend:
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Issue 4: Port 8000 not accessible

**Check**:
```bash
# See if backend is listening
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Test directly
curl http://localhost:8000/api/health
```

## Manual Test

Try logging in manually via curl:

```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@landdev.com&password=Password123!"

# Should return:
# {"access_token":"...","token_type":"bearer"}
```

If this works, the backend is fine - it's a frontend connection issue.

## Nuclear Option - Complete Restart

```bash
# Stop everything
docker-compose down

# Remove frontend node_modules volume
docker volume ls | grep node_modules
docker volume rm land-dev-tracker_frontend_node_modules

# Start fresh
docker-compose up --build

# Wait for all services
sleep 30

# Initialize database
./init-db.sh

# Try again
```

## Still Not Working?

Run the diagnostic and share the output:

```bash
./diagnose.sh > connection-debug.txt 2>&1

# Also check browser console:
# 1. Open http://localhost:3000
# 2. Press F12
# 3. Go to Console tab
# 4. Take a screenshot of any red errors
```

## Success Indicators

When everything works, you should see:

1. ✅ Login page shows "✓ Backend connected" (green badge)
2. ✅ http://localhost:8000/docs loads in browser
3. ✅ curl http://localhost:8000/api/health returns JSON
4. ✅ No errors in browser console
5. ✅ Login with admin@landdev.com works

Most connection issues are fixed by rebuilding the frontend container!
