output "alb_dns_name" {
  description = "Public DNS of the ALB — point the frontend's API_BASE_URL here (or a CNAME)."
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "ECR repo for the backend image (used by CI)."
  value       = aws_ecr_repository.backend.repository_url
}

output "aurora_cluster_endpoint" {
  description = "Aurora writer endpoint — use for MIGRATION_DATABASE_URL (owner DDL only)."
  value       = aws_rds_cluster.main.endpoint
}

output "aurora_reader_endpoint" {
  description = "Aurora reader endpoint (unused until a reader instance is added)."
  value       = aws_rds_cluster.main.reader_endpoint
}

output "rds_proxy_endpoint" {
  description = "RDS Proxy endpoint — use for DATABASE_URL (app_user, pooled)."
  value       = aws_db_proxy.main.endpoint
}

output "aurora_master_secret_arn" {
  description = "Secrets Manager ARN holding the Aurora master password."
  value       = aws_rds_cluster.main.master_user_secret[0].secret_arn
}

output "app_user_secret_arn" {
  description = "Secrets Manager ARN holding app_user credentials (password synced to proxy)."
  value       = aws_secretsmanager_secret.app_user.arn
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
