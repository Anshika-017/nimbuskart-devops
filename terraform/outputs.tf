output "vpc_id" {
  description = "ID of the VPC"
  value       = module.network.vpc_id
}

output "subnet_a_id" {
  description = "ID of public subnet A"
  value       = module.network.subnet_a_id
}

output "subnet_b_id" {
  description = "ID of public subnet B"
  value       = module.network.subnet_b_id
}

output "bucket_name" {
  description = "Name of the S3 logs bucket"
  value       = aws_s3_bucket.logs.bucket
}
