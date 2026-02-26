#!/bin/bash
# Comprehensive fix for connection issues

echo "=================================================="
echo "Land Development Tracker - Connection Fix"
echo "=================================================="
echo ""

echo "Step 1: Checking container status..."
docker-compose ps
echo ""

echo "Step 2: Testing backend health..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✓ Backend is responding at http://localhost:8000"
    curl -s http://localhost:8000/api/health | jq . 2>/dev/null || curl -s http://localhost:8000/api/health
else
    echo "✗ Backend is NOT responding"
    echo ""
    echo "Checking backend logs..."
    docker-compose logs backend --tail=20
    echo ""
    echo "Restarting backend..."
    docker-compose restart backend
    echo "Waiting for backend to start..."
    sleep 10
fi
echo ""

echo "Step 3: Testing database..."
if docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ Database is accessible"
else
    echo "✗ Database is NOT accessible"
    echo "You may need to run: ./init-db.sh"
fi
echo ""

echo "Step 4: Checking frontend environment..."
docker-compose exec -T frontend sh -c "cat /app/.env | grep VITE_API_URL" 2>/dev/null || echo "⚠️  No .env file found in frontend container"
echo ""

echo "Step 5: Rebuilding frontend..."
docker-compose stop frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
echo "Waiting for frontend to start..."
sleep 15
echo ""

echo "=================================================="
echo "Testing connections..."
echo "=================================================="
echo ""

echo "Backend health check:"
curl -s http://localhost:8000/api/health && echo "" || echo "❌ Backend not responding"
echo ""

echo "Backend API docs:"
curl -s http://localhost:8000/docs > /dev/null && echo "✓ API docs accessible at http://localhost:8000/docs" || echo "❌ API docs not accessible"
echo ""

echo "=================================================="
echo "Now try accessing:"
echo "=================================================="
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000/docs"
echo ""
echo "The login page should show: ✓ Backend connected"
echo "=================================================="
