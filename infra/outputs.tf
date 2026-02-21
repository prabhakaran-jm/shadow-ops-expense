output "app_runner_url" {
  description = "App Runner service HTTPS URL (backend API). Set when create_apprunner is true."
  value       = var.create_apprunner ? "https://${aws_apprunner_service.backend[0].service_url}" : null
}

output "cloudfront_url" {
  description = "CloudFront distribution URL (frontend)."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "ecr_repo_url" {
  description = "ECR repository URL for backend image (use for docker tag/push)."
  value       = aws_ecr_repository.backend.repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend static build (upload dist/ here)."
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for invalidations)."
  value       = aws_cloudfront_distribution.frontend.id
}
