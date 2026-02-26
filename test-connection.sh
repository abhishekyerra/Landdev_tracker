#!/bin/bash
# Simple connection test

echo "Testing Backend Connection..."
echo ""

# Test 1: Can we reach the backend from the host?
echo "1. Testing from your computer to backend:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health | grep -q "200"; then
    echo "   ✓ SUCCESS - Backend is accessible at http://localhost:8000"
    echo "   Response:"
    curl -s http://localhost:8000/api/health
    echo ""
else
    echo "   ✗ FAILED - Backend is not accessible"
    echo "   This means the backend container is not running or not responding"
    echo ""
    echo "   Checking if backend container is running..."
    if docker-compose ps backend | grep -q "Up"; then
        echo "   Container is running but not responding. Check logs:"
        echo "   docker-compose logs backend"
    else
        echo "   Container is not running. Start it:"
        echo "   docker-compose up -d backend"
    fi
    exit 1
fi
echo ""

# Test 2: Can the frontend container reach the backend?
echo "2. Testing from frontend container to backend:"
if docker-compose exec -T frontend sh -c "wget -q -O - http://backend:8000/api/health" > /dev/null 2>&1; then
    echo "   ✓ SUCCESS - Frontend can reach backend internally"
else
    echo "   ⚠️  Frontend cannot reach backend (but this is okay if using localhost)"
fi
echo ""

# Test 3: Test login endpoint
echo "3. Testing login endpoint:"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@landdev.com&password=Password123!" \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ SUCCESS - Login works!"
    echo "   Token received: ${RESPONSE_BODY:0:50}..."
else
    echo "   ✗ FAILED - Login failed with HTTP code: $HTTP_CODE"
    echo "   Response: $RESPONSE_BODY"
    echo ""
    echo "   This might mean:"
    echo "   - Database is not initialized (run: ./init-db.sh)"
    echo "   - User table is empty"
fi
echo ""

echo "=================================================="
echo "Summary:"
echo "=================================================="

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ All tests passed!"
    echo ""
    echo "Your backend is working correctly."
    echo "If the frontend still shows 'unable to connect':"
    echo ""
    echo "1. Open browser console (F12)"
    echo "2. Look for the actual error message"
    echo "3. Run: docker-compose restart frontend"
    echo "4. Hard reload the page: Ctrl+Shift+R"
else
    echo "✗ Backend has issues"
    echo ""
    echo "To fix:"
    echo "1. Make sure database is initialized: ./init-db.sh"
    echo "2. Check backend logs: docker-compose logs backend"
    echo "3. Restart backend: docker-compose restart backend"
fi
echo "=================================================="
