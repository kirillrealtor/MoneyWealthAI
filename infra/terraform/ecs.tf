locals {
  image = var.container_image != "" ? var.container_image : "${aws_ecr_repository.backend.repository_url}:latest"

  app_environment = [
    { name = "ENV", value = "production" },
    { name = "PORT", value = tostring(var.container_port) },
    { name = "PLAID_ENV", value = "sandbox" },
    { name = "PLAID_PRODUCTS", value = "transactions,liabilities,investments" },
    { name = "SYNC_WORKER_ENABLED", value = "true" },
    { name = "WEB_APP_URL", value = var.web_app_url },
    { name = "ALLOWED_HOSTS", value = aws_lb.main.dns_name },
    # TODO: flip to false once /health is exempted from the Host allowlist so
    # ALB health checks (Host = task IP) pass without trusting any host.
    { name = "TRUST_ANY_HOST", value = "true" },
  ]

  app_secrets = [
    for n in var.secret_names : { name = n, valueFrom = aws_ssm_parameter.secret[n].arn }
  ]
}

resource "aws_ecs_cluster" "main" {
  name = var.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.name}-backend"
  retention_in_days = 30
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name         = "backend"
    image        = local.image
    essential    = true
    portMappings = [{ containerPort = var.container_port, protocol = "tcp" }]
    environment  = local.app_environment
    secrets      = local.app_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])

  # CI overwrites the image each deploy; don't fight it on plan.
  lifecycle {
    ignore_changes = [container_definitions]
  }
}

resource "aws_ecs_service" "backend" {
  name            = "${var.name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.task.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = var.container_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.http]

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}
