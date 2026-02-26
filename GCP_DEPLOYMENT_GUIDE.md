# 🚀 Deploy Land Development Tracker to GCP Cloud Run

## Complete Step-by-Step Guide

### Estimated Time: 45 minutes
### Estimated Cost: $15-25/month

---

## 📋 Part 1: Prerequisites (10 minutes)

### 1.1 Install Google Cloud SDK

```bash
# For macOS
brew install --cask google-cloud-sdk

# Verify installation
gcloud --version
```

### 1.2 Login to Google Cloud

```bash
# Login
gcloud auth login

# This will open a browser window - sign in with your Google account
```

### 1.3 Create a New GCP Project

```bash
# Set variables
export PROJECT_ID="landdev-tracker-$(date +%s)"
export REGION="us-central1"

# Create project
gcloud projects create $PROJECT_ID --name="Land Development Tracker"

# Set as default project
gcloud config set project $PROJECT_ID

# Enable billing (you'll need to link a billing account)
# Go to: https://console.cloud.google.com/billing
# Link your billing account to this project

echo "Your Project ID: $PROJECT_ID"
echo "Save this Project ID!"
```

### 1.4 Enable Required APIs

```bash
# Enable all required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  compute.googleapis.com \
  container.googleapis.com \
  secretmanager.googleapis.com

# This takes 2-3 minutes
```

---

## 🗄️ Part 2: Set Up Cloud SQL Database (15 minutes)

### 2.1 Create Cloud SQL Instance

```bash
# Set database variables
export DB_INSTANCE_NAME="landdev-db"
export DB_NAME="landdev_tracker"
export DB_USER="landdev_user"
export DB_PASSWORD="$(openssl rand -base64 32)"

# Save password (you'll need it)
echo "Database Password: $DB_PASSWORD" > ~/landdev-db-password.txt
echo "⚠️  Password saved to ~/landdev-db-password.txt"

# Create Cloud SQL PostgreSQL instance
gcloud sql instances create $DB_INSTANCE_NAME \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=$DB_PASSWORD

# This takes 5-10 minutes ⏳
```

### 2.2 Create Database and User

```bash
# Create database
gcloud sql databases create $DB_NAME \
  --instance=$DB_INSTANCE_NAME

# Create user
gcloud sql users create $DB_USER \
  --instance=$DB_INSTANCE_NAME \
  --password=$DB_PASSWORD

# Get connection name
export CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME \
  --format='value(connectionName)')

echo "Connection Name: $CONNECTION_NAME"
echo "Save this Connection Name!"
```

### 2.3 Initialize Database Schema

```bash
# Connect to Cloud SQL and run schema
gcloud sql connect $DB_INSTANCE_NAME --user=postgres --quiet

# At the PostgreSQL prompt, run these commands:
\c landdev_tracker
\i /path/to/your/database/schema.sql
\i /path/to/your/database/seed_data.sql
\q
```

**Alternative:** Use Cloud SQL Proxy (easier)

```bash
# Download Cloud SQL Proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
chmod +x cloud_sql_proxy

# Start proxy in a separate terminal
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5433

# In another terminal, load schema
psql "postgresql://$DB_USER:$DB_PASSWORD@127.0.0.1:5433/$DB_NAME" < database/schema.sql
psql "postgresql://$DB_USER:$DB_PASSWORD@127.0.0.1:5433/$DB_NAME" < database/seed_data.sql
psql "postgresql://$DB_USER:$DB_PASSWORD@127.0.0.1:5433/$DB_NAME" < database/columbia_60lot_project.sql
```

---

## 🔐 Part 3: Set Up Secrets (5 minutes)

### 3.1 Create Secrets in Secret Manager

```bash
# Create secret for JWT key
echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create jwt-secret-key --data-file=-

# Create secret for database URL
echo -n "postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME" | \
  gcloud secrets create database-url --data-file=-

# Create secret for Anthropic API key (if you have one)
echo -n "your-anthropic-api-key-here" | \
  gcloud secrets create anthropic-api-key --data-file=-
```

---

## 🐳 Part 4: Build and Deploy Backend (10 minutes)

### 4.1 Create Backend Dockerfile for Production

Create `backend/Dockerfile.production`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 4.2 Build and Deploy Backend

```bash
# Navigate to backend directory
cd backend

# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/landdev-backend

# Deploy to Cloud Run
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
  --port 8080

# Get backend URL
export BACKEND_URL=$(gcloud run services describe landdev-backend \
  --region $REGION \
  --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"
echo "Save this URL!"

cd ..
```

---

## 🎨 Part 5: Build and Deploy Frontend (10 minutes)

### 5.1 Create Frontend Production Files

Create `frontend/Dockerfile.production`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build with production API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.prod.conf`:

```nginx
server {
    listen 8080;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 5.2 Build and Deploy Frontend

```bash
# Navigate to frontend
cd frontend

# Build with backend URL
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/landdev-frontend \
  --substitutions=_VITE_API_URL=$BACKEND_URL

# Deploy to Cloud Run
gcloud run deploy landdev-frontend \
  --image gcr.io/$PROJECT_ID/landdev-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --max-instances 10 \
  --port 8080

# Get frontend URL
export FRONTEND_URL=$(gcloud run services describe landdev-frontend \
  --region $REGION \
  --format 'value(status.url)')

echo "🎉 Frontend URL: $FRONTEND_URL"
echo "Your app is live!"

cd ..
```

---

## 🔧 Part 6: Configure CORS (5 minutes)

### 6.1 Update Backend CORS Settings

The backend needs to allow requests from your frontend domain.

Edit `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.run.app",  # Allow all Cloud Run domains
        "http://localhost:3000"  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Rebuild and redeploy backend:

```bash
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/landdev-backend
gcloud run deploy landdev-backend \
  --image gcr.io/$PROJECT_ID/landdev-backend \
  --platform managed \
  --region $REGION
cd ..
```

---

## ✅ Part 7: Test Your Deployment

### 7.1 Test Backend

```bash
# Test health endpoint
curl $BACKEND_URL/api/health

# Should return: {"status":"healthy",...}
```

### 7.2 Test Frontend

```bash
# Open in browser
open $FRONTEND_URL

# Or use Chrome
google-chrome $FRONTEND_URL
```

### 7.3 Login and Test

1. Go to your frontend URL
2. Login: admin@landdev.com / Password123!
3. Click "Columbia 60-Lot Development"
4. Verify:
   - ✅ Project loads
   - ✅ Tasks display
   - ✅ Weather shows
   - ✅ AI widget appears

---

## 💰 Part 8: Monitor Costs

### 8.1 Set Up Budget Alerts

```bash
# Create budget
gcloud billing budgets create \
  --billing-account=$(gcloud billing projects describe $PROJECT_ID --format="value(billingAccountName)") \
  --display-name="Land Dev Tracker Monthly Budget" \
  --budget-amount=50 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### 8.2 View Costs

```bash
# View current costs
gcloud billing projects describe $PROJECT_ID

# Or go to: https://console.cloud.google.com/billing
```

### Expected Monthly Costs:
- Cloud SQL (db-f1-micro): $7-10
- Backend Cloud Run: $3-5
- Frontend Cloud Run: $2-3
- Cloud Build: $1-2
- **Total: $13-20/month**

---

## 🎯 Part 9: Add Custom Domain (Optional)

### 9.1 Buy Domain (e.g., Namecheap, Google Domains)

Buy: `yourproject.com`

### 9.2 Map Domain to Cloud Run

```bash
# Map domain to frontend
gcloud beta run domain-mappings create \
  --service landdev-frontend \
  --domain yourproject.com \
  --region $REGION

# Map subdomain to backend
gcloud beta run domain-mappings create \
  --service landdev-backend \
  --domain api.yourproject.com \
  --region $REGION
```

### 9.3 Update DNS

Add these records to your domain:
- Type: CNAME, Name: @, Value: (provided by Cloud Run)
- Type: CNAME, Name: api, Value: (provided by Cloud Run)

---

## 👥 Part 10: Add Users for Your Team

### 10.1 Create Users via Database

```bash
# Connect to database
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5433 &

# Add contractor user
psql "postgresql://$DB_USER:$DB_PASSWORD@127.0.0.1:5433/$DB_NAME" << EOF
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active)
VALUES (
  'contractor@example.com',
  '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYnbkJ8l6Xe',
  'John',
  'Contractor',
  'contractor',
  true
);
EOF

# Password for all new users: Password123!
```

### 10.2 Share Access

Send your team:
- **URL**: $FRONTEND_URL
- **Username**: contractor@example.com
- **Password**: Password123!
- **Instructions**: "Change your password after first login"

---

## 🔒 Part 11: Security Hardening (Important!)

### 11.1 Change Default Passwords

```bash
# Update admin password in database
psql "postgresql://$DB_USER:$DB_PASSWORD@127.0.0.1:5433/$DB_NAME" << EOF
UPDATE users 
SET password_hash = '\$2b\$12\$NEW_HASH_HERE'
WHERE email = 'admin@landdev.com';
EOF
```

### 11.2 Enable Cloud Armor (Optional - adds $10/month)

```bash
# Create security policy
gcloud compute security-policies create landdev-security-policy \
  --description "Security policy for Land Dev Tracker"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy landdev-security-policy \
  --expression "origin.region_code == 'US'" \
  --action allow \
  --description "Allow US traffic"
```

---

## 📊 Part 12: Monitoring & Logs

### 12.1 View Logs

```bash
# Backend logs
gcloud run services logs read landdev-backend --region $REGION --limit 50

# Frontend logs
gcloud run services logs read landdev-frontend --region $REGION --limit 50
```

### 12.2 Set Up Alerts

```bash
# Create uptime check
gcloud monitoring uptime create \
  --display-name="Frontend Health Check" \
  --resource-type=uptime-url \
  --host=$FRONTEND_URL
```

---

## 🎉 Success Checklist

- [ ] Backend deployed and responding
- [ ] Frontend deployed and accessible
- [ ] Database connected and populated
- [ ] Can login with admin account
- [ ] Projects display correctly
- [ ] Weather widget works
- [ ] AI recommendations load
- [ ] Tasks can be updated
- [ ] Budget alerts configured
- [ ] Team members can access

---

## 🐛 Troubleshooting

### Backend won't start?
```bash
# Check logs
gcloud run services logs read landdev-backend --region $REGION --limit 100

# Common issues:
# 1. Database connection - check CONNECTION_NAME
# 2. Secrets not set - verify secrets exist
# 3. Port mismatch - should be 8080
```

### Frontend can't connect to backend?
```bash
# Check CORS settings in backend
# Verify VITE_API_URL was set during build
# Check browser console for errors
```

### Database connection failed?
```bash
# Verify Cloud SQL instance is running
gcloud sql instances list

# Check connection name
gcloud sql instances describe $DB_INSTANCE_NAME

# Test connection with proxy
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5433
psql -h 127.0.0.1 -p 5433 -U $DB_USER -d $DB_NAME
```

---

## 📝 Save These Values!

Create a file `deployment-info.txt`:

```bash
cat > deployment-info.txt << EOF
GCP Project ID: $PROJECT_ID
Region: $REGION

Database:
  Instance: $DB_INSTANCE_NAME
  Connection: $CONNECTION_NAME
  Database: $DB_NAME
  User: $DB_USER
  Password: (see ~/landdev-db-password.txt)

Services:
  Backend URL: $BACKEND_URL
  Frontend URL: $FRONTEND_URL

Login:
  Admin: admin@landdev.com
  Password: Password123!

Estimated Monthly Cost: \$15-25
EOF

cat deployment-info.txt
```

---

## 🔄 Future Updates

### To update backend:
```bash
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/landdev-backend
gcloud run deploy landdev-backend --image gcr.io/$PROJECT_ID/landdev-backend --region $REGION
cd ..
```

### To update frontend:
```bash
cd frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/landdev-frontend
gcloud run deploy landdev-frontend --image gcr.io/$PROJECT_ID/landdev-frontend --region $REGION
cd ..
```

---

## 🎯 Next Steps

1. ✅ Test with your team
2. ✅ Add more users
3. ✅ Set up custom domain
4. ✅ Configure backup strategy
5. ✅ Add monitoring alerts

**Your app is now live on GCP!** 🚀

Questions? Issues? Let me know!
