resource "aws_db_subnet_group" "main" {
  name       = "${var.name}-db"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "${var.name}-db" }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.name}-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_master_username
  # RDS manages the master password in Secrets Manager — never in TF state.
  manage_master_user_password = true

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 5
  storage_type          = "gp3"
  storage_encrypted     = true

  multi_az               = var.db_multi_az
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period   = 7
  deletion_protection       = var.environment == "prod"
  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.name}-final" : null
  apply_immediately         = var.environment != "prod"

  performance_insights_enabled = true
  tags                         = { Name = "${var.name}-db" }
}

# NOTE: the non-owner `app_user` role (NOBYPASSRLS) and the connection-string
# SSM parameters (DATABASE_URL / MIGRATION_DATABASE_URL) are provisioned
# out-of-band after the DB is up — see infra/terraform/README.md. They are not
# in Terraform state by design (least-privilege secret handling).
