# Papersio - Terraform Deployment Guide

## Prerequisites

1. AWS account with appropriate permissions
2. Terraform CLI installed (v1.0+)
3. AWS CLI configured with credentials
4. Docker images published to GitHub Container Registry

## Quick Start

1) Configure variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:
- Update `backend_image` and `frontend_image` with your GitHub username
- Set `google_api_key` with your Gemini API key
- Optional: `default_model`, `hf_token`

2) Initialize Terraform

```bash
terraform init
```

3) Review plan

```bash
terraform plan
```

4) Apply infrastructure

```bash
terraform apply
```

5) Get application URL

```bash
terraform output application_url
```

## Cost Estimation

For accurate pricing, use the AWS Pricing Calculator and enter the exact stack inputs:
https://calculator.aws/

Use these settings for this infrastructure:
- Region: `eu-west-3`
- ECS Fargate:
  - 2 backend tasks: 1 vCPU / 2 GB each
  - 2 frontend tasks: 0.5 vCPU / 1 GB each
  - Linux/x86, on‑demand pricing
  - Ephemeral storage: default 20 GB per task
- Application Load Balancer:
  - 1 ALB, low LCU usage
  - Include public IPv4 charges for ALB
- RDS PostgreSQL:
  - `db.t3.micro`, single AZ
  - 20 GB gp3 storage
  - Automated backups disabled (free‑tier restriction)
- NAT Gateways:
  - 2 NAT gateways (one per AZ)
  - Include data processing and data transfer via NAT
- CloudWatch Logs:
  - Log ingestion and storage (low volume)
- Data transfer:
  - Internet egress from ALB (client traffic)
  - ECS outbound egress via NAT (LLM/API calls)

## Important Commands

View outputs:
```bash
terraform output
```

View sensitive outputs:
```bash
terraform output -json
```

Update infrastructure:
```bash
terraform apply
```

Destroy everything:
```bash
terraform destroy
```

View logs:
```bash
aws logs tail /ecs/papersio-backend --follow
aws logs tail /ecs/papersio-frontend --follow
```

4. Run:
```bash
terraform apply
```

5. Create Route 53 A record pointing to the ALB

## Troubleshooting

ECS tasks not starting:
- Check CloudWatch logs
- Verify secrets are configured correctly
- Ensure Docker images are accessible

Database connection errors:
- Check security group rules
- Verify DATABASE_URL format
- Check RDS instance status
- Ensure tables are created

Out of memory errors:
- Increase `backend_memory` in terraform.tfvars
- Run `terraform apply`

High costs:
- Check CloudWatch metrics for actual usage
- Consider reducing `desired_count`
- Review NAT Gateway usage

## Updates and Maintenance

Update Docker images:
1. Push new images to GHCR
2. Update ECS service:

```bash
aws ecs update-service --cluster papersio-cluster \
  --service papersio-backend --force-new-deployment
```

Database backups:
- Automatic backups are disabled to stay within free tier limits
- Manual snapshot: RDS Console > Snapshots > Take Snapshot

Scale up/down:
1. Update `desired_count` in terraform.tfvars
2. Run `terraform apply`

## Support

For issues with Terraform configuration, check:
- AWS documentation
- Terraform AWS provider docs
- Project GitHub Issues
