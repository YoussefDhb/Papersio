variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-3"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "papersio"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

variable "backend_image" {
  description = "Docker image for backend"
  type        = string
  default     = "ghcr.io/your-username/papersio-backend:latest"
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
  default     = "ghcr.io/your-username/papersio-frontend:latest"
}

variable "backend_cpu" {
  description = "CPU units for backend container (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "backend_memory" {
  description = "Memory for backend container (MiB)"
  type        = number
  default     = 2048
}

variable "frontend_cpu" {
  description = "CPU units for frontend container"
  type        = number
  default     = 512
}

variable "frontend_memory" {
  description = "Memory for frontend container (MiB)"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "papersio"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "papersio"
  sensitive   = true
}

variable "google_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

variable "default_model" {
  description = "Default Gemini model"
  type        = string
  default     = "gemini-2.5-flash"
}

variable "hf_token" {
  description = "Hugging Face token (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional)"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch logs retention period"
  type        = number
  default     = 7
}

variable "min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 4
}

variable "cpu_threshold" {
  description = "CPU utilization threshold for scaling"
  type        = number
  default     = 70
}
