terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
    iam = "http://localhost:4566"
  }
}

module "network" {
  source      = "./modules/network"
  project     = var.project
  environment = var.environment
  owner       = var.owner
}

resource "aws_security_group" "web" {
  name        = "${var.project}-web-sg"
  description = "Security group for web tier"
  vpc_id      = module.network.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project}-web-sg"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "web" {
  count         = 2
  ami           = "ami-00000000"
  instance_type = "t3.micro"
  subnet_id     = count.index == 0 ? module.network.subnet_a_id : module.network.subnet_b_id

  tags = {
    Name        = "${var.project}-web-${count.index + 1}"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    Tier        = "web"
  }
}

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs-${var.environment}"

  tags = {
    Name        = "${var.project}-logs"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}


resource "aws_ebs_volume" "orphan" {
  availability_zone = "us-east-1a"
  size              = 10

  tags = {
    Name        = "${var.project}-orphan-vol"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}
