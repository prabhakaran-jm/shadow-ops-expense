# Shadow Ops – Deploy backend + frontend to AWS (PowerShell)
# Prerequisites: Terraform, AWS CLI, Docker. Run from repo root.
# Usage: .\infra\deploy.ps1   or   cd infra; .\deploy.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = if ($PSScriptRoot) { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path } else { (Get-Location).Path }
$InfraDir = Join-Path $RepoRoot "infra"
$Region = "us-east-1"

Write-Host "Repo root: $RepoRoot" -ForegroundColor Cyan
Set-Location $RepoRoot

# --- Phase 1: Terraform (ECR, S3, CloudFront; optionally App Runner) ---
Write-Host "`n[1/6] Terraform init..." -ForegroundColor Yellow
Set-Location $InfraDir
terraform init -input=false
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[2/6] Terraform apply (ECR, S3, CloudFront)..." -ForegroundColor Yellow
terraform apply -input=false -auto-approve
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$EcrUrl = terraform output -raw ecr_repo_url
$S3Bucket = terraform output -raw s3_bucket_name
$CfId = terraform output -raw cloudfront_distribution_id

# --- Phase 2: Backend image build and push ---
Write-Host "`n[3/6] Docker build and push backend..." -ForegroundColor Yellow
Set-Location $RepoRoot
$EcrHost = ($EcrUrl -split "/")[0]
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $EcrHost
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker build -t shadow-ops-backend ./backend
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker tag shadow-ops-backend:latest "${EcrUrl}:latest"
docker push "${EcrUrl}:latest"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# --- Create or update App Runner (image now in ECR) ---
Write-Host "`n[4/6] Terraform apply (App Runner)..." -ForegroundColor Yellow
Set-Location $InfraDir
terraform apply -input=false -auto-approve -var="create_apprunner=true"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$AppRunnerUrl = terraform output -raw app_runner_url
Write-Host "App Runner URL: $AppRunnerUrl" -ForegroundColor Green

# --- Frontend build with backend URL ---
Write-Host "`n[5/6] Frontend build (VITE_API_BASE=$AppRunnerUrl)..." -ForegroundColor Yellow
Set-Location $RepoRoot
$env:VITE_API_BASE = $AppRunnerUrl
Set-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# --- S3 upload and CloudFront invalidation ---
Write-Host "`n[6/6] S3 sync and CloudFront invalidation..." -ForegroundColor Yellow
aws s3 sync dist "s3://$S3Bucket" --delete
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

aws cloudfront create-invalidation --distribution-id $CfId --paths "/*"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Set-Location $InfraDir
$CfUrl = terraform output -raw cloudfront_url
Set-Location $RepoRoot
Write-Host "`nDeploy complete." -ForegroundColor Green
Write-Host "  Frontend: $CfUrl" -ForegroundColor Green
Write-Host "  Backend:  $AppRunnerUrl" -ForegroundColor Green
Write-Host "  (CORS is set to CloudFront origin in App Runner.)" -ForegroundColor Gray
