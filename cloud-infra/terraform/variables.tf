variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "policy-analyzer"
}

variable "lambda_runtime" {
  description = "Python runtime version for Lambda"
  type        = string
  default     = "python3.12"
}

variable "openai_api_key" {
  description = "OpenAI API key for the Lambda function"
  type        = string
  sensitive   = true
}

