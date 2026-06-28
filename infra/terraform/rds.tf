# Aurora PostgreSQL (Serverless v2) + RDS Proxy.
# Hackathon cost profile: 0.5–2 ACU writer only, no reader replica.
# App connects via proxy (DATABASE_URL); migrations hit the cluster writer directly.

resource "aws_db_subnet_group" "main" {
  name       = "${var.name}-db"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "${var.name}-db" }
}

resource "aws_rds_cluster" "main" {
  cluster_identifier = "${var.name}-aurora"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = var.aurora_engine_version
  database_name      = var.db_name
  master_username    = var.db_master_username
  # Master password in Secrets Manager — never in TF state.
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.aurora.id]

  storage_encrypted       = true
  backup_retention_period = 7
  deletion_protection     = var.environment == "prod"
  skip_final_snapshot     = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.name}-aurora-final" : null
  apply_immediately       = var.environment != "prod"

  serverlessv2_scaling_configuration {
    min_capacity = var.aurora_min_acu
    max_capacity = var.aurora_max_acu
  }

  tags = { Name = "${var.name}-aurora" }
}

resource "aws_rds_cluster_instance" "writer" {
  identifier         = "${var.name}-aurora-writer"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version
  publicly_accessible  = false

  performance_insights_enabled = true
  tags                         = { Name = "${var.name}-aurora-writer" }
}

# App role credentials — role itself is created out-of-band (see README).
resource "random_password" "app_user" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "app_user" {
  name                    = "${var.name}/app-user-db"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0
}

resource "aws_secretsmanager_secret_version" "app_user" {
  secret_id = aws_secretsmanager_secret.app_user.id
  secret_string = jsonencode({
    username = "app_user"
    password = random_password.app_user.result
  })
}

# ── RDS Proxy ───────────────────────────────────────────────────────────────

resource "aws_iam_role" "rds_proxy" {
  name = "${var.name}-rds-proxy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "rds.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "rds_proxy_secrets" {
  name = "secrets-read"
  role = aws_iam_role.rds_proxy.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
      ]
      Resource = [
        aws_rds_cluster.main.master_user_secret[0].secret_arn,
        aws_secretsmanager_secret.app_user.arn,
      ]
    }]
  })
}

resource "aws_db_proxy" "main" {
  name                   = "${var.name}-proxy"
  engine_family          = "POSTGRESQL"
  role_arn               = aws_iam_role.rds_proxy.arn
  vpc_subnet_ids         = aws_subnet.private[*].id
  vpc_security_group_ids = [aws_security_group.rds_proxy.id]
  require_tls            = true
  idle_client_timeout    = 1800

  auth {
    auth_scheme = "SECRETS"
    secret_arn  = aws_rds_cluster.main.master_user_secret[0].secret_arn
    iam_auth    = "DISABLED"
  }

  auth {
    auth_scheme = "SECRETS"
    secret_arn  = aws_secretsmanager_secret.app_user.arn
    iam_auth    = "DISABLED"
  }

  tags = { Name = "${var.name}-proxy" }
}

resource "aws_db_proxy_default_target_group" "main" {
  db_proxy_name = aws_db_proxy.main.name

  connection_pool_config {
    max_connections_percent      = 100
    max_idle_connections_percent = 50
    connection_borrow_timeout    = 120
  }
}

resource "aws_db_proxy_target" "main" {
  db_proxy_name         = aws_db_proxy.main.name
  target_group_name     = aws_db_proxy_default_target_group.main.name
  db_cluster_identifier = aws_rds_cluster.main.id
}
