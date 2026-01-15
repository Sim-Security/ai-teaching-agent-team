# Deployment Guide - AI Teaching Agent Team

This document covers deploying the AI Teaching Agent Team to Google Cloud Run with full CI/CD automation.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Manual Deployment](#manual-deployment)
5. [CI/CD with GitHub Actions](#cicd-with-github-actions)
6. [Environment Variables](#environment-variables)
7. [Health Checks](#health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)

---

## Architecture Overview

```
GitHub (main branch)
       |
       v
GitHub Actions (CI/CD)
       |
       +--> Lint & Test
       |
       +--> Build Docker Image
       |         |
       |         v
       |    Artifact Registry
       |
       +--> Deploy to Cloud Run
                  |
                  v
             Cloud Run Service
             (Port 8080, 2GB RAM)
```

---

## Prerequisites

### GCP Setup

1. **Create GCP Project** (if needed):
   ```bash
   gcloud projects create YOUR_PROJECT_ID
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Required APIs**:
   ```bash
   gcloud services enable \
     cloudbuild.googleapis.com \
     run.googleapis.com \
     artifactregistry.googleapis.com \
     containerregistry.googleapis.com
   ```

3. **Create Service Account for CI/CD**:
   ```bash
   # Create service account
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions CI/CD"

   # Grant required roles
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.writer"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"

   # Generate key file
   gcloud iam service-accounts keys create sa-key.json \
     --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Create Artifact Registry Repository**:
   ```bash
   gcloud artifacts repositories create cloud-run-images \
     --repository-format=docker \
     --location=us-central1 \
     --description="Cloud Run container images"
   ```

### GitHub Secrets

Add these secrets to your GitHub repository (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123456` |
| `GCP_SA_KEY` | Service account JSON key (entire content of sa-key.json) | `{"type": "service_account", ...}` |
| `GCP_REGION` | (Optional) Deployment region | `us-central1` |

---

## Local Development

### Run with Docker

```bash
# Build the image
docker build -t ai-teaching-agent-team .

# Run locally (create .env from .env.example first)
docker run -p 8080:8080 --env-file .env ai-teaching-agent-team
```

### Run without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run app.py --server.port=8080
```

Access the app at: `http://localhost:8080`

---

## Manual Deployment

### Option 1: Using Cloud Build

```bash
# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml

# View build logs
gcloud builds list --limit=5
```

### Option 2: Direct gcloud Deploy

```bash
# Build and push image
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/cloud-run-images/ai-teaching-agent-team:latest .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/cloud-run-images/ai-teaching-agent-team:latest

# Deploy to Cloud Run
gcloud run deploy ai-teaching-agent-team \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/cloud-run-images/ai-teaching-agent-team:latest \
  --region=us-central1 \
  --platform=managed \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --allow-unauthenticated
```

---

## CI/CD with GitHub Actions

The workflow (`.github/workflows/deploy.yml`) triggers on:
- **Push to `main`**: Full pipeline (test, build, deploy)
- **Pull requests to `main`**: Test only (no deployment)

### Workflow Jobs

1. **test**: Lint with Ruff, run pytest
2. **build**: Build Docker image, push to Artifact Registry
3. **deploy**: Deploy to Cloud Run, run health check

### Trigger Deployment

Simply push to main:
```bash
git checkout main
git merge feature/mlops-enhancement
git push origin main
```

---

## Environment Variables

### Required at Runtime

These should be set in Cloud Run or provided by users via the UI:

| Variable | Description | Set Via |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | UI Input |
| `COMPOSIO_API_KEY` | Composio API key | UI Input |
| `LANGSMITH_API_KEY` | LangSmith API key (optional) | UI Input |
| `SERPAPI_API_KEY` | SerpAPI key (optional) | UI Input |

### Set via Cloud Run Console

For secrets, use Cloud Run's Secret Manager integration:
```bash
gcloud run services update ai-teaching-agent-team \
  --set-secrets=OPENROUTER_API_KEY=openrouter-key:latest
```

### Streamlit Configuration (Auto-set in Dockerfile)

| Variable | Value |
|----------|-------|
| `STREAMLIT_SERVER_PORT` | `8080` |
| `STREAMLIT_SERVER_ADDRESS` | `0.0.0.0` |
| `STREAMLIT_SERVER_HEADLESS` | `true` |

---

## Health Checks

### Streamlit Health Endpoint

Streamlit exposes a health check at:
```
GET /_stcore/health
```

Returns: `ok` (200) when healthy

### Cloud Run Health Check

Cloud Run automatically performs health checks on port 8080. The Dockerfile includes a HEALTHCHECK instruction for local Docker health monitoring.

### Manual Health Check

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe ai-teaching-agent-team \
  --region=us-central1 --format='value(status.url)')

# Check health
curl -f "${SERVICE_URL}/_stcore/health"
```

---

## Troubleshooting

### Common Issues

#### 1. Build Fails - "Permission denied"
```bash
# Ensure Cloud Build has required permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

#### 2. Container Crashes on Startup
Check logs:
```bash
gcloud run services logs read ai-teaching-agent-team --region=us-central1 --limit=50
```

#### 3. "Port 8080 already allocated"
Ensure no other process is using port 8080 locally:
```bash
lsof -i :8080
```

#### 4. GitHub Actions Failing
- Verify secrets are correctly set
- Check the SA key is valid JSON (not base64 encoded - use raw JSON)
- Ensure service account has all required IAM roles

### View Logs

```bash
# Real-time logs
gcloud run services logs tail ai-teaching-agent-team --region=us-central1

# Historical logs
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=ai-teaching-agent-team" \
  --limit=100 --format="table(timestamp,severity,textPayload)"
```

---

## Security Considerations

### Container Security

- Multi-stage build minimizes attack surface
- Non-root user (`appuser`) runs the application
- No unnecessary packages in production image

### Secrets Management

- Never commit API keys to repository
- Use GitHub Secrets for CI/CD credentials
- Consider Cloud Run Secret Manager integration for runtime secrets:
  ```bash
  gcloud secrets create openrouter-key --data-file=- <<< "your-api-key"
  gcloud run services update ai-teaching-agent-team \
    --set-secrets=OPENROUTER_API_KEY=openrouter-key:latest
  ```

### Network Security

- XSRF protection enabled in Streamlit
- CORS disabled for security
- Consider adding Cloud Armor for DDoS protection
- Use VPC connector for internal service communication

### IAM Best Practices

- Use least-privilege service accounts
- Rotate service account keys regularly
- Enable audit logging for Cloud Run

---

## Cost Optimization

### Cloud Run Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| `min-instances` | 0 | Scale to zero when idle |
| `max-instances` | 10 | Prevent runaway costs |
| `memory` | 2Gi | LangChain/LLM calls need headroom |
| `cpu` | 2 | Parallel processing for agents |
| `timeout` | 300s | LLM calls can be slow |

### Estimated Costs

- Idle: ~$0/month (scale to zero)
- Light usage (1000 requests/day): ~$5-15/month
- Heavy usage: Monitor with Cloud Billing budgets

---

## Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
- [GitHub Actions for GCP](https://github.com/google-github-actions)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)

---

*Last updated: 2025-01-15*
