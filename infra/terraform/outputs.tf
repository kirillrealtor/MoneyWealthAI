output "alb_dns_name" {
  description = "Public DNS of the ALB — point the frontend's API_BASE_URL here (or a CNAME)."
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "ECR repo for the backend image (used by CI)."
  value       = aws_ecr_repository.backend.repository_url
}

output "rds_endpoint" {
  description = "RDS endpoint:port."
  value       = "${aws_db_instance.main.address}:${aws_db_instance.main.port}"
}

output "rds_master_secret_arn" {
  description = "Secrets Manager ARN holding the RDS-managed master password."
  value       = aws_db_instance.main.master_user_secret[0].secret_arn
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service" {
  value = aws_ecs_service.backend.name
}

output "alerts_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
