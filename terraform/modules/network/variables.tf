variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "project" {
  description = "Project name for tagging"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging"
  type        = string
  default     = "staging"
}

variable "owner" {
  description = "Owner name for tagging"
  type        = string
  default     = "nimbuskart-team"
}
