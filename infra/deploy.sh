#!/usr/bin/env bash
# Shadow Ops – Deploy backend + frontend to AWS (Bash)
# Prerequisites: Terraform, AWS CLI, Docker. Run from repo root.
# Usage: ./infra/deploy.sh   or   cd infra && ./deploy.sh

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$REPO_ROOT/infra"
REGION="${AWS_REGION:-us-east-1}"

echo "Repo root: $REPO_ROOT"
cd "$REPO_ROOT"

# --- Phase 1: Terraform (ECR, S3, CloudFront) ---
echo ""
echo "[1/6] Terraform init..."
cd "$INFRA_DIR"
terraform init -input=false

echo ""
echo "[2/6] Terraform apply (ECR, S3, CloudFront)..."
terraform apply -input=false -auto-approve

ECR_URL=$(terraform output -raw ecr_repo_url)
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CF_ID=$(terraform output -raw cloudfront_distribution_id)

# --- Phase 2: Backend image build and push ---
echo ""
echo "[3/6] Docker build and push backend..."
cd "$REPO_ROOT"
ECR_HOST="${ECR_URL%%/*}"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_HOST"
docker build -t shadow-ops-backend ./backend
docker tag shadow-ops-backend:latest "${ECR_URL}:latest"
docker push "${ECR_URL}:latest"

# --- Create or update App Runner ---
echo ""
echo "[4/6] Terraform apply (App Runner)..."
cd "$INFRA_DIR"
terraform apply -input=false -auto-approve -var="create_apprunner=true"

APP_RUNNER_URL=$(terraform output -raw app_runner_url)
echo "App Runner URL: $APP_RUNNER_URL"

# --- Frontend build ---
echo ""
echo "[5/6] Frontend build (VITE_API_BASE=$APP_RUNNER_URL)..."
cd "$REPO_ROOT/frontend"
export VITE_API_BASE="$APP_RUNNER_URL"
npm run build

# --- S3 upload and CloudFront invalidation ---
echo ""
echo "[6/6] S3 sync and CloudFront invalidation..."
aws s3 sync dist "s3://$S3_BUCKET" --delete
aws cloudfront create-invalidation --distribution-id "$CF_ID" --paths "/*"

CF_URL=$(cd "$INFRA_DIR" && terraform output -raw cloudfront_url)
echo ""
echo "Deploy complete."
echo "  Frontend: $CF_URL"
echo "  Backend:  $APP_RUNNER_URL"
echo "  (CORS is set to CloudFront origin in App Runner.)"
