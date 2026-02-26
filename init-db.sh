#!/bin/bash
# Database Initialization Script
# Run this after docker-compose up to initialize the database

set -e

echo "=================================================="
echo "Initializing Land Development Tracker Database"
echo "=================================================="
echo ""

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Check if database is accessible
until docker-compose exec -T postgres pg_isready -U landdev_user -d landdev_tracker > /dev/null 2>&1; do
  echo "Waiting for database..."
  sleep 2
done

echo "✓ PostgreSQL is ready"
echo ""

# Check if tables already exist
TABLE_COUNT=$(docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [ "$TABLE_COUNT" -gt "0" ]; then
    echo "ℹ️  Database already initialized with $TABLE_COUNT tables"
    echo ""
    echo "To reinitialize, run:"
    echo "  docker-compose down -v"
    echo "  docker-compose up -d"
    echo "  ./init-db.sh"
    exit 0
fi

# Load schema
echo "Loading database schema..."
docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker < database/schema.sql

if [ $? -eq 0 ]; then
    echo "✓ Schema loaded successfully"
else
    echo "✗ Failed to load schema"
    exit 1
fi

# Load seed data
echo "Loading seed data..."
docker-compose exec -T postgres psql -U landdev_user -d landdev_tracker < database/seed_data.sql

if [ $? -eq 0 ]; then
    echo "✓ Seed data loaded successfully"
else
    echo "✗ Failed to load seed data"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Database initialized successfully!"
echo "=================================================="
echo ""
echo "You can now access:"
echo "  Frontend:  http://localhost:3000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Default login:"
echo "  Email:     admin@landdev.com"
echo "  Password:  Password123!"
echo ""
echo "To connect to database:"
echo "  docker-compose exec postgres psql -U landdev_user landdev_tracker"
echo "=================================================="
