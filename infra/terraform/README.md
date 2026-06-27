# MoneyWealth AI — Infrastructure as Code (Terraform)

This is the **scalable target architecture** for the backend platform, as code.
It is intentionally *not* a mirror of the hand-built prototype (single Fargate
task, default VPC, public-IP task, no load balancer). It provisions the
production-grade stack the prototype was a stepping stone toward:

```
Internet ─► ALB (HTTPS) ─► ECS Fargate service (N tasks, autoscaling)
                                 │  private subnets, no public IP
                                 ├─► RDS Postgres (Multi-AZ, private)
                                 └─► Upstash Redis / Groq / Plaid (via NAT)
```

## What it creates
- **Network**: dedicated VPC, public + private subnets across `az_count` AZs,
  IGW, one NAT gateway per AZ.
- **Security**: 3-tier SGs — only `ALB:80/443` is public; tasks accept traffic
  *only* from the ALB; RDS accepts Postgres *only* from tasks.
- **Compute**: ECS Fargate cluster (Container Insights on), task definition,
  service in private subnets behind the ALB, with **target-tracking
  autoscaling** (CPU 65% / mem 75%, `min`..`max` tasks).
- **Edge**: Application Load Balancer; HTTPS listener when `acm_certificate_arn`
  is set (HTTP→HTTPS redirect), HTTP-only otherwise.
- **Data**: RDS Postgres 16, encrypted, **Multi-AZ**, 7-day backups, deletion
  protection in prod; master password managed by RDS in Secrets Manager.
- **Registry/secrets**: ECR repo (scan-on-push, lifecycle), SSM SecureString
  parameters (resource owned by TF, **values injected out-of-band**).
- **Observability**: CloudWatch log group + alarms (tasks-down, CPU, ALB 5xx,
  unhealthy targets, RDS CPU) → SNS email.

## Prerequisites
- Terraform ≥ 1.6, AWS credentials with admin-ish perms.
- **ELB enabled on the account** (new accounts are gated — open a Support case
  to lift the limit; the ALB will fail to create until then).
- For HTTPS: an ACM certificate in `us-east-1` for your domain.

## Usage
```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # then edit
terraform init
terraform plan
terraform apply
```

## Out-of-band steps (by design — keeps secrets out of TF state)
After `apply`:
1. **Create the app role + RLS isolation** (connect as the RDS master):
   ```sql
   CREATE ROLE app_user LOGIN PASSWORD '<strong>' NOBYPASSRLS;
   GRANT CONNECT ON DATABASE financial_advisor TO app_user;
   ALTER ROLE mwadmin BYPASSRLS;  -- for admin SECURITY DEFINER functions
   ```
2. **Set the secret values** in the SSM parameters TF created:
   ```bash
   aws ssm put-parameter --name /moneywealth/DATABASE_URL --type SecureString \
     --value 'postgresql://app_user:...@<rds_endpoint>/financial_advisor?sslmode=require' --overwrite
   aws ssm put-parameter --name /moneywealth/RESEND_API_KEY --type SecureString \
     --value 're_...' --overwrite
   # ...repeat for the other secret_names (see variables.tf)
   ```
3. **Run migrations**: `cd backend && MIGRATION_DATABASE_URL=... python -m scripts.migrate`
4. **First deploy**: push to `main` → the `deploy-backend` GitHub Action builds
   the image and rolls the service (or run it manually once).
5. Point the frontend's `API_BASE_URL` at the `alb_dns_name` output (or a CNAME).

## Follow-up to fully drop `TRUST_ANY_HOST`
The task currently runs `TRUST_ANY_HOST=true` so ALB HTTP health checks (whose
`Host` header is the task IP) pass. To enforce a strict allowlist, exempt the
`/health` routes from `TrustedHostMiddleware` in `backend/app/main.py`, then set
`ALLOWED_HOSTS` to your domain and remove `TRUST_ANY_HOST`.

## State
Local state by default. For a team, uncomment the S3 backend in `versions.tf`
(create the bucket + DynamoDB lock table first).
