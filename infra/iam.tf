# ---------------------------------------------------------------------------
# App Runner ECR access role – used by App Runner to pull the image from ECR.
# Trust: build.apprunner.amazonaws.com (required for ECR AuthenticationConfiguration).
# Permissions: AWS managed policy AWSAppRunnerServicePolicyForECRAccess.
# ---------------------------------------------------------------------------
resource "aws_iam_role" "apprunner_ecr_access" {
  name = "${var.project}-apprunner-ecr-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  tags = local.common_tags
}

# ECR pull: GetAuthorizationToken (account-level) + BatchGetImage etc. on this repo.
resource "aws_iam_role_policy" "apprunner_ecr_pull" {
  name   = "ecr-pull"
  role   = aws_iam_role.apprunner_ecr_access.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = aws_ecr_repository.backend.arn
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# App Runner instance role – assumed by the running task (runtime).
# Trust: tasks.apprunner.amazonaws.com.
# Used for Bedrock InvokeModel (Nova inference).
# ---------------------------------------------------------------------------
resource "aws_iam_role" "apprunner_instance" {
  name = "${var.project}-apprunner-instance"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy" "apprunner_bedrock" {
  name   = "bedrock-invoke"
  role   = aws_iam_role.apprunner_instance.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      }
    ]
  })
}

# Nova Act: workflow definitions + agent execution (cloud browser automation)
resource "aws_iam_role_policy" "apprunner_nova_act" {
  name   = "nova-act"
  role   = aws_iam_role.apprunner_instance.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "nova-act:*"
        Resource = "*"
      }
    ]
  })
}
