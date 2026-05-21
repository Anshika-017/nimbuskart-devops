output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "subnet_a_id" {
  description = "ID of public subnet A"
  value       = aws_subnet.public_a.id
}

output "subnet_b_id" {
  description = "ID of public subnet B"
  value       = aws_subnet.public_b.id
}

