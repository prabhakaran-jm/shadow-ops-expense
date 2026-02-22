# App Runner service: pulls backend image from ECR, exposes HTTPS URL.
# Create only after the image exists in ECR (set create_apprunner = true after push).
resource "aws_apprunner_service" "backend" {
  count        = var.create_apprunner ? 1 : 0
  service_name = var.apprunner_service_name

  source_configuration {
    image_repository {
      image_identifier     = "${aws_ecr_repository.backend.repository_url}:latest"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          NOVA_MODE              = "real"
          NOVA_ACT_MODE          = "real"
          NOVA_ACT_STARTING_PAGE = "https://${aws_cloudfront_distribution.frontend.domain_name}/expense-form.html"
          NOVA_ACT_HEADLESS      = "true"
          AWS_REGION             = var.region
          BEDROCK_REGION         = var.region
          NOVA_MODEL_ID_LITE     = "global.amazon.nova-2-lite-v1:0"
          CORS_ALLOW_ORIGINS     = "https://${aws_cloudfront_distribution.frontend.domain_name}"
        }
      }
    }
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }
    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu               = "1024"
    memory            = "4096"
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/api/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  tags = local.common_tags
}
