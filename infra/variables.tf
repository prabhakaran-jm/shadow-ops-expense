variable "region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name for tagging."
  type        = string
  default     = "shadow-ops-expense"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = "prabhakaran"
}

variable "apprunner_service_name" {
  description = "App Runner service name."
  type        = string
  default     = "shadow-ops-backend"
}

variable "ecr_repo_name" {
  description = "ECR repository name for backend image."
  type        = string
  default     = "shadow-ops-backend"
}

# Set to true only after pushing the backend image to ECR (avoids App Runner CREATE_FAILED).
variable "create_apprunner" {
  description = "Create App Runner service. Set to true after pushing the backend image to ECR (see infra/README.md)."
  type        = bool
  default     = false
}

locals {
  common_tags = {
    project = var.project
    owner   = var.owner
  }
}
