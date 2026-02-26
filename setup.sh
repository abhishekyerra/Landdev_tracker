#!/bin/bash

# Land Development Tracker - Quick Setup Script
# This script helps you get started quickly with local development

set -e

echo "=================================================="
echo "Land Development Tracker - Setup"
echo "=================================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "ℹ️  backend/.env already created"
else
    echo "✅ backend/.env exists"
fi

if [ ! -f "frontend/.env" ]; then
    echo "ℹ️  frontend/.env already created"
else
    echo "✅ frontend/.env exists"
fi

echo ""
echo "=================================================="
echo "Starting the application with Docker Compose..."
echo "=================================================="
echo ""

# Stop any existing containers
docker-compose down 2>/dev/null || true

# Start Docker Compose
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "=================================================="
    echo "✅ Services are starting!"
    echo "=================================================="
    echo ""
    
    # Initialize database
    echo "Initializing database..."
    chmod +x init-db.sh
    ./init-db.sh
    
else
    echo ""
    echo "❌ Some services failed to start. Checking logs..."
    docker-compose logs
    echo ""
    echo "Try running manually: docker-compose up"
fi
