variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ontorag"
}

variable "instance_type" {
  description = "EC2 instance type (t2.micro = free tier)"
  type        = string
  default     = "t2.micro"
}

variable "key_pair_name" {
  description = "Name of the SSH key pair (must exist in AWS)"
  type        = string
}

variable "my_ip" {
  description = "Your public IP for SSH access (x.x.x.x/32)"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "cerebras_api_key" {
  description = "Cerebras API key"
  type        = string
  sensitive   = true
}

variable "neo4j_password" {
  description = "Neo4j database password"
  type        = string
  sensitive   = true
  default     = "ontorag-secure-2024"
}
