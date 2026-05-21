variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "nimbuskart"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "nimbuskart-team"
}

variable "ssh_cidr" {
  description = "CIDR block allowed for SSH access on port 22"
  type        = string
  default     = "10.0.0.0/8"
}
