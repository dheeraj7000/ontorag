output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.ontorag.id
}

output "public_ip" {
  description = "Public IP address (Elastic IP)"
  value       = aws_eip.ontorag.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.ontorag.public_ip}"
}

output "app_url" {
  description = "Application URL"
  value       = "http://${aws_eip.ontorag.public_ip}"
}

output "api_url" {
  description = "API health check URL"
  value       = "http://${aws_eip.ontorag.public_ip}/health"
}

output "neo4j_browser" {
  description = "Neo4j Browser URL (dev access only)"
  value       = "http://${aws_eip.ontorag.public_ip}:7474"
}

output "s3_bucket" {
  description = "S3 bucket name for document storage"
  value       = aws_s3_bucket.documents.bucket
}
