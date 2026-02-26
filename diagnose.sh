#!/bin/bash
# Diagnostic script to check all services

echo "=================================================="
echo "Land Development Tracker - Diagnostics"
echo "=================================================="
echo ""

echo "1. Checking Docker containers..."
docker-compose ps
echo ""

echo "2. Testing Backend Health Endpoint..."
echo "   URL: http://localhost:8000/api/health"
curl -s http://localhost:8000/api/health || echo "❌ Backend not responding"
echo ""
echo ""

echo "3. Testing Backend from inside Docker network..."
docker-compose exec -T frontend sh -c "curl -s http://backend:8000/api/health" || echo "❌ Backend not accessible from frontend container"
echo ""
echo ""

echo "4. Checking Backend Logs (last 20 lines)..."
docker-compose logs --tail=20 backend
echo ""

echo "5. Checking Frontend Environment..."
docker-compose exec -T frontend sh -c "env | grep VITE" || echo "No VITE env vars found"
echo ""

echo "6. Testing Database Connection..."
docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker -c "SELECT COUNT(*) FROM users;" || echo "❌ Database not accessible"
echo ""

echo "=================================================="
echo "Open these URLs in your browser:"
echo "=================================================="
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000/docs"
echo "Health:    http://localhost:8000/api/health"
echo "=================================================="
