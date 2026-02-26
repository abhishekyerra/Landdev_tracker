#!/bin/bash

# 🚀 Quick GCP Cloud Run Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 Land Development Tracker - GCP Deployment"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Install it with: brew install --cask google-cloud-sdk"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI found${NC}"

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to gcloud${NC}"
    echo "Logging in..."
    gcloud auth login
fi

echo ""
echo "📝 Project Configuration"
echo "========================"

# Get or create project ID
read -p "Enter your GCP Project ID (or press Enter to create new): " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID="landdev-tracker-$(date +%s)"
    echo "Creating new project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID --name="Land Development Tracker"
fi

# Set project
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Set region
REGION="us-central1"
echo "Region: $REGION"

echo ""
echo "🔧 Enabling APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  --quiet

echo -e "${GREEN}✅ APIs enabled${NC}"

echo ""
echo "🗄️  Database Setup"
echo "=================="

# Database configuration
DB_INSTANCE_NAME="landdev-db"
DB_NAME="landdev_tracker"
DB_USER="landdev_user"
DB_PASSWORD=$(openssl rand -base64 32)

echo "Database Instance: $DB_INSTANCE_NAME"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo -e "${YELLOW}⚠️  Database Password: $DB_PASSWORD${NC}"
echo "$DB_PASSWORD" > db-password.txt
echo "Password saved to: db-password.txt"

# Check if database already exists
if gcloud sql instances describe $DB_INSTANCE_NAME &> /dev/null; then
    echo -e "${YELLOW}⚠️  Database instance already exists, skipping creation${NC}"
else
    echo ""
    read -p "Create Cloud SQL instance? This takes 5-10 minutes and costs ~\$10/month (y/n): " CREATE_DB
    
    if [ "$CREATE_DB" = "y" ]; then
        echo "Creating Cloud SQL instance..."
        gcloud sql instances create $DB_INSTANCE_NAME \
          --database-version=POSTGRES_14 \
          --tier=db-f1-micro \
          --region=$REGION \
          --root-password=$DB_PASSWORD \
          --quiet
        
        echo "Creating database..."
        gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME
        
        echo "Creating user..."
        gcloud sql users create $DB_USER \
          --instance=$DB_INSTANCE_NAME \
          --password=$DB_PASSWORD
        
        echo -e "${GREEN}✅ Database created${NC}"
    fi
fi

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME --format='value(connectionName)')
echo "Connection Name: $CONNECTION_NAME"

echo ""
echo "🔐 Setting up secrets..."

# Create secrets
echo -n "$(openssl rand -base64 32)" | gcloud secrets create jwt-secret-key --data-file=- --quiet 2>/dev/null || echo "jwt-secret-key already exists"

echo -n "postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME" | \
  gcloud secrets create database-url --data-file=- --quiet 2>/dev/null || echo "database-url already exists"

# Anthropic API key
read -p "Enter your Anthropic API Key (or press Enter to skip): " ANTHROPIC_KEY
if [ ! -z "$ANTHROPIC_KEY" ]; then
    echo -n "$ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key --data-file=- --quiet 2>/dev/null || echo "anthropic-api-key already exists"
    echo -e "${GREEN}✅ Anthropic API key stored${NC}"
fi

echo ""
echo "🐳 Building Backend..."
cd backend

gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/landdev-backend \
  --timeout=20m \
  --quiet

echo -e "${GREEN}✅ Backend built${NC}"

echo ""
echo "🚀 Deploying Backend to Cloud Run..."

gcloud run deploy landdev-backend \
  --image gcr.io/$PROJECT_ID/landdev-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $CONNECTION_NAME \
  --set-secrets DATABASE_URL=database-url:latest,SECRET_KEY=jwt-secret-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --port 8080 \
  --quiet

BACKEND_URL=$(gcloud run services describe landdev-backend --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Backend deployed: $BACKEND_URL${NC}"

cd ..

echo ""
echo "🎨 Building Frontend..."
cd frontend

# Build with backend URL
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/landdev-frontend \
  --timeout=20m \
  --substitutions=_VITE_API_URL=$BACKEND_URL \
  --quiet

echo -e "${GREEN}✅ Frontend built${NC}"

echo ""
echo "🚀 Deploying Frontend to Cloud Run..."

gcloud run deploy landdev-frontend \
  --image gcr.io/$PROJECT_ID/landdev-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --max-instances 10 \
  --port 8080 \
  --quiet

FRONTEND_URL=$(gcloud run services describe landdev-frontend --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Frontend deployed: $FRONTEND_URL${NC}"

cd ..

echo ""
echo "=============================================="
echo "🎉 Deployment Complete!"
echo "=============================================="
echo ""
echo "📝 Deployment Information:"
echo "--------------------------"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "🌐 URLs:"
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "🗄️  Database:"
echo "Instance: $DB_INSTANCE_NAME"
echo "Connection: $CONNECTION_NAME"
echo "Password saved to: db-password.txt"
echo ""
echo "👤 Login:"
echo "Email: admin@landdev.com"
echo "Password: Password123!"
echo ""
echo "💰 Estimated Monthly Cost: \$15-25"
echo ""
echo "📚 Next Steps:"
echo "1. Open $FRONTEND_URL in your browser"
echo "2. Login with the credentials above"
echo "3. Load database schema (see GCP_DEPLOYMENT_GUIDE.md)"
echo "4. Add your team members"
echo "5. Set up budget alerts"
echo ""
echo "📖 Full documentation: GCP_DEPLOYMENT_GUIDE.md"
echo "=============================================="

# Save deployment info
cat > deployment-info.txt << EOF
GCP Deployment Information
==========================

Project ID: $PROJECT_ID
Region: $REGION

URLs:
  Frontend: $FRONTEND_URL
  Backend: $BACKEND_URL

Database:
  Instance: $DB_INSTANCE_NAME
  Connection: $CONNECTION_NAME
  Database: $DB_NAME
  User: $DB_USER
  Password: (see db-password.txt)

Login:
  Email: admin@landdev.com
  Password: Password123!

Deployment Date: $(date)

Monthly Cost Estimate: \$15-25
- Cloud SQL (db-f1-micro): \$7-10
- Backend Cloud Run: \$3-5
- Frontend Cloud Run: \$2-3
- Misc (storage, build): \$1-2
EOF

echo "💾 Deployment info saved to: deployment-info.txt"
