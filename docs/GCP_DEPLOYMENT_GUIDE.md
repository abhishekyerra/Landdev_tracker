# Land Development Tracker - Complete GCP Deployment Guide

## Overview
This guide will walk you through deploying the Land Development Tracker application to Google Cloud Platform (GCP). The application consists of:
- PostgreSQL database (Cloud SQL)
- FastAPI backend (Cloud Run)
- React frontend (Cloud Run)
- File storage (Cloud Storage)

## Prerequisites
- Google Cloud Platform account
- gcloud CLI installed and configured
- Docker installed locally
- Basic knowledge of GCP services

## Step 1: Set Up GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export DB_INSTANCE="landdev-db"
export DB_NAME="landdev_tracker"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## Step 2: Create Cloud SQL PostgreSQL Database

```bash
# Create Cloud SQL instance (PostgreSQL 16)
gcloud sql instances create $DB_INSTANCE \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=CHANGE_THIS_PASSWORD \
  --backup \
  --backup-start-time=03:00

# Create database
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE

# Create database user
gcloud sql users create landdev_user \
  --instance=$DB_INSTANCE \
  --password=CHANGE_THIS_PASSWORD

# Get the connection name
gcloud sql instances describe $DB_INSTANCE --format="value(connectionName)"
# Save this - you'll need it: PROJECT_ID:REGION:INSTANCE_NAME
```

## Step 3: Initialize Database Schema

```bash
# Connect to Cloud SQL using Cloud SQL Proxy
# Download and run the proxy in a separate terminal:
cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:5432

# In another terminal, run the schema and seed files:
psql "host=127.0.0.1 port=5432 dbname=landdev_tracker user=landdev_user" < database/schema.sql
psql "host=127.0.0.1 port=5432 dbname=landdev_tracker user=landdev_user" < database/seed_data.sql
```

## Step 4: Set Up Cloud Storage

```bash
# Create bucket for document storage
export BUCKET_NAME="${PROJECT_ID}-landdev-documents"
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME/

# Set up CORS for the bucket
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "POST", "PUT", "DELETE"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://$BUCKET_NAME/
```

## Step 5: Create Secrets

```bash
# Create database URL secret
echo -n "postgresql://landdev_user:YOUR_PASSWORD@/landdev_tracker?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME" | \
  gcloud secrets create database-url --data-file=-

# Create JWT secret key
echo -n "$(openssl rand -hex 32)" | \
  gcloud secrets create secret-key --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding secret-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 6: Build and Push Docker Images

### Backend

```bash
cd backend

# Build the image
docker build -t gcr.io/$PROJECT_ID/landdev-backend:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/landdev-backend:latest
```

### Frontend

```bash
cd ../frontend

# Build the image
docker build -t gcr.io/$PROJECT_ID/landdev-frontend:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/landdev-frontend:latest
```

## Step 7: Deploy to Cloud Run

### Deploy Backend

```bash
gcloud run deploy landdev-backend \
  --image gcr.io/$PROJECT_ID/landdev-backend:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE \
  --set-secrets="DATABASE_URL=database-url:latest,SECRET_KEY=secret-key:latest" \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 1 \
  --port 8000

# Get the backend URL
export BACKEND_URL=$(gcloud run services describe landdev-backend --platform managed --region $REGION --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

### Deploy Frontend

```bash
gcloud run deploy landdev-frontend \
  --image gcr.io/$PROJECT_ID/landdev-frontend:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="VITE_API_URL=$BACKEND_URL" \
  --memory 512Mi \
  --cpu 0.5 \
  --max-instances 5 \
  --min-instances 1 \
  --port 80

# Get the frontend URL
export FRONTEND_URL=$(gcloud run services describe landdev-frontend --platform managed --region $REGION --format 'value(status.url)')
echo "Frontend URL: $FRONTEND_URL"
```

## Step 8: Configure Custom Domain (Optional)

```bash
# Map custom domain to frontend
gcloud run domain-mappings create \
  --service landdev-frontend \
  --domain app.yourdomain.com \
  --region $REGION

# Map custom domain to backend API
gcloud run domain-mappings create \
  --service landdev-backend \
  --domain api.yourdomain.com \
  --region $REGION

# Update DNS records as shown in the output
```

## Step 9: Set Up CI/CD with Cloud Build (Optional)

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/landdev-backend:$COMMIT_SHA', './backend']
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/landdev-frontend:$COMMIT_SHA', './frontend']
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/landdev-backend:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/landdev-frontend:$COMMIT_SHA']
  
  # Deploy backend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'landdev-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/landdev-backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
  
  # Deploy frontend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'landdev-frontend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/landdev-frontend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

images:
  - 'gcr.io/$PROJECT_ID/landdev-backend:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/landdev-frontend:$COMMIT_SHA'
```

## Step 10: Monitoring and Logging

```bash
# View backend logs
gcloud run services logs tail landdev-backend --region=$REGION

# View frontend logs
gcloud run services logs tail landdev-frontend --region=$REGION

# Set up alerts (example)
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Backend Error Rate" \
  --condition-display-name="Error rate too high" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

## Cost Optimization Tips

1. **Use Cloud SQL Proxy** - Connect backend to Cloud SQL using Unix socket for better performance
2. **Set Min Instances to 0** - For development, set min instances to 0 to save costs
3. **Use Committed Use Discounts** - For production, consider committed use for Cloud SQL
4. **Enable Cloud CDN** - Cache frontend static assets
5. **Regular Backups** - Cloud SQL automated backups are included

## Security Best Practices

1. **Use Secret Manager** - Never hardcode credentials
2. **Enable IAM Authentication** - Use IAM for Cloud SQL connections in production
3. **Set Up VPC** - Use VPC for private communication between services
4. **Enable Cloud Armor** - Protect against DDoS attacks
5. **Regular Updates** - Keep dependencies updated

## Estimated Monthly Costs

For a small to medium deployment:
- Cloud SQL (db-f1-micro): ~$10/month
- Cloud Run Backend (minimal traffic): ~$5-20/month
- Cloud Run Frontend (minimal traffic): ~$5-15/month
- Cloud Storage: ~$1-5/month
- **Total: ~$21-50/month**

For production with higher traffic, costs scale based on usage.

## Troubleshooting

### Backend won't connect to database
```bash
# Check Cloud SQL instance status
gcloud sql instances describe $DB_INSTANCE

# Verify secrets are set
gcloud secrets versions access latest --secret=database-url

# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID
```

### Frontend can't reach backend
```bash
# Verify CORS settings in backend
# Check environment variable in frontend
gcloud run services describe landdev-frontend --region=$REGION
```

## Next Steps

1. Set up monitoring dashboards in Cloud Console
2. Configure alerting policies
3. Set up database backups schedule
4. Implement CI/CD pipeline
5. Add custom domain
6. Enable Cloud CDN for frontend
7. Set up staging environment

## Support

For issues or questions:
- Check Cloud Run logs
- Review Cloud SQL logs
- Consult GCP documentation
- Review application logs via Cloud Logging

## Local Development

To run locally while connected to Cloud SQL:

```bash
# Run Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:5432

# In another terminal, run backend
cd backend
DATABASE_URL="postgresql://landdev_user:PASSWORD@localhost:5432/landdev_tracker" \
  uvicorn main:app --reload

# In another terminal, run frontend
cd frontend
VITE_API_URL="http://localhost:8000" npm run dev
```
