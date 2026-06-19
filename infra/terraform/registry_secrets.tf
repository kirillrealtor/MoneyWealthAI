resource "aws_ecr_repository" "backend" {
  name                 = "${var.name}-backend"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  tags = { Name = "${var.name}-backend" }
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 15 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 15 }
      action       = { type = "expire" }
    }]
  })
}

# SecureString parameters for app secrets. Terraform owns the resource; the
# VALUE is injected out-of-band (CI / `aws ssm put-parameter`) and ignored here
# so plaintext secrets never enter Terraform state.
resource "aws_ssm_parameter" "secret" {
  for_each = toset(var.secret_names)
  name     = "/${var.name}/${each.value}"
  type     = "SecureString"
  value    = "PLACEHOLDER_SET_OUT_OF_BAND"

  lifecycle {
    ignore_changes = [value]
  }
  tags = { Name = "/${var.name}/${each.value}" }
}
