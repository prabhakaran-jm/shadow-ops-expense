# Shadow Ops – Infrastructure (Terraform)

Minimal AWS stack: ECR, App Runner (backend), S3 + CloudFront (frontend). Region: `us-east-1` by default.

**Important:** App Runner pulls the image from ECR at create time. If the image does not exist yet, the service goes to `CREATE_FAILED`. Use the two-phase flow below.

## Prerequisites

- Terraform >= 1.5
- AWS CLI configured (credentials or env)
- Docker (for building and pushing the backend image)

## Terraform (two-phase: ECR first, then App Runner)

**Phase 1 – Create ECR, IAM, S3, CloudFront (no App Runner yet):**

```bash
cd infra
terraform init
terraform plan
terraform apply
```

(`create_apprunner` defaults to `false`, so the App Runner service is not created. This avoids CREATE_FAILED when the ECR repo is still empty.)

**Phase 2 – Push the backend image, then create App Runner:**

```bash
# From repo root: build, authenticate ECR, tag, push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform -chdir=infra output -raw ecr_repo_url | cut -d/ -f1)
docker build -t shadow-ops-backend ./backend
docker tag shadow-ops-backend:latest $(terraform -chdir=infra output -raw ecr_repo_url):latest
docker push $(terraform -chdir=infra output -raw ecr_repo_url):latest

# Create App Runner (image now exists)
cd infra
terraform apply -var="create_apprunner=true"
```

After phase 2, `app_runner_url` will be set. Other outputs (`cloudfront_url`, `ecr_repo_url`, `s3_bucket_name`, `cloudfront_distribution_id`) are available after phase 1.

## If App Runner already failed (CREATE_FAILED)

If you ran apply with App Runner enabled before pushing the image, the service is in `CREATE_FAILED`. Fix it:

1. **Delete the failed service in AWS** (Console: App Runner → select service → Delete; or CLI: `aws apprunner delete-service --service-arn <arn>`).
2. **Remove it from Terraform state** (so Terraform can create it again):
   ```bash
   cd infra
   terraform state rm aws_apprunner_service.backend
   ```
3. **Push the image to ECR** (see Phase 2 above: docker build, login, tag, push).
4. **Re-apply with App Runner enabled:**
   ```bash
   terraform apply -var="create_apprunner=true"
   ```
   Terraform will create a new App Runner service; this time the image exists and the service should reach `RUNNING`.

## Frontend (S3 + CloudFront)

The frontend expects the API base URL at build time. It appends `/api` if the base does not already end with `/api`.

1. **Build with App Runner URL**

   Set `VITE_API_BASE` to the App Runner HTTPS URL (no trailing slash). Example (replace with your `app_runner_url`):

   **Linux/macOS:**
   ```bash
   cd frontend
   export VITE_API_BASE=https://xxxxx.us-east-1.awsapprunner.com
   npm run build
   ```

   **Windows (PowerShell):**
   ```powershell
   cd frontend
   $env:VITE_API_BASE="https://xxxxx.us-east-1.awsapprunner.com"
   npm run build
   ```

   **One-liner using Terraform output (from repo root, after App Runner is created):**
   ```bash
   cd frontend && export VITE_API_BASE=$(terraform -chdir=../infra output -raw app_runner_url) && npm run build
   ```
   The app normalizes the base and appends `/api` if needed; the backend is at `<app_runner_url>/api`.

2. **Upload `dist/` to S3**

   ```bash
   aws s3 sync frontend/dist s3://$(terraform -chdir=infra output -raw s3_bucket_name) --delete
   ```

3. **Invalidate CloudFront cache**

   ```bash
   aws cloudfront create-invalidation --distribution-id $(terraform -chdir=infra output -raw cloudfront_distribution_id) --paths "/*"
   ```

## CORS

Set the backend env var `CORS_ALLOW_ORIGINS` to your CloudFront (or custom) origin so the browser can call the API. In App Runner, add an environment variable:

- Key: `CORS_ALLOW_ORIGINS`
- Value: `https://d1234567890.cloudfront.net` (your CloudFront URL from `terraform output cloudfront_url`; use the domain from that output, e.g. `https://<distribution-domain>`)

Redeploy the App Runner service after changing env vars.

## Summary

| Step | Command / action |
|------|------------------|
| Phase 1 – provision ECR, IAM, S3, CF | `cd infra && terraform init && terraform apply` |
| Push backend image | `docker build`, ECR login, tag, push (see Phase 2 above) |
| Phase 2 – create App Runner | `terraform apply -var="create_apprunner=true"` |
| Frontend build | `cd frontend && VITE_API_BASE=<app_runner_url> npm run build` |
| Frontend upload | `aws s3 sync frontend/dist s3://<s3_bucket_name> --delete` |
| Invalidate | `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"` |
