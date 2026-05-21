# NimbusKart DevOps — Cost Hygiene & Automation

## Overview

This repository implements a cloud cost hygiene foundation for NimbusKart, an e-commerce startup whose AWS bill grew from $400/month to $2,100/month due to orphaned resources. It includes a Terraform stack for baseline infrastructure on LocalStack, a Python "Cost Janitor" script that detects wasteful resources, and a GitHub Actions pipeline that runs the janitor on every PR.

## How to run locally

### Prerequisites
- Docker Desktop
- WSL2 (Ubuntu)
- Python 3.10+
- Terraform

### Setup

```bash
git clone https://github.com/Anshika-017/nimbuskart-devops
cd nimbuskart-devops
pip install boto3 awscli-local terraform-local
```

### Start LocalStack

```bash
docker run -d -p 4566:4566 --name localstack localstack/localstack:3.0.0
sleep 20
curl http://localhost:4566/_localstack/health
```

### Apply Terraform

```bash
cd terraform
tflocal init
tflocal apply -auto-approve
```

### Run Cost Janitor

```bash
cd janitor
python3 janitor.py --dry-run
cat report.json
```

### Delete orphans (skips Protected=true resources)

```bash
python3 janitor.py --delete
```

## Architecture
.
+-- terraform/                  # Part A: Infrastructure as Code
|   +-- main.tf                 # VPC, EC2, S3, EBS, Security Group
|   +-- variables.tf            # Input variables with defaults
|   +-- outputs.tf              # VPC ID, subnet IDs, bucket name
|   +-- modules/
|       +-- network/            # Reusable VPC + subnet module
+-- janitor/                    # Part B: Cost Janitor
|   +-- janitor.py              # Main script
|   +-- constants.py            # Pricing constants with sources
|   +-- generate_summary.py     # Markdown report generator
|   +-- requirements.txt
+-- .github/workflows/
|   +-- cost-janitor.yml        # CI/CD pipeline
+-- DESIGN.md                   # Part C: Production design note
+-- samples/                    # Example report output
## Decisions & deviations

- **SSH CIDR changed from 0.0.0.0/0 to 10.0.0.0/8**: Opening port 22 to the entire internet is a critical security risk. Changed to private network range by default with a configurable variable.
- **S3 lifecycle resource removed**: LocalStack 3.0.0 does not support aws_s3_bucket_lifecycle_configuration reliably — it times out after 3 minutes. Documented as a known LocalStack limitation.
- **Orphan EBS volume intentionally created**: As required by the spec, an unattached EBS volume is created to serve as a known orphan for the janitor to detect.
- **LocalStack version pinned to 3.0.0**: Latest LocalStack requires a paid license. Version 3.0.0 is the last free version.
- **tflocal used instead of raw terraform**: tflocal automatically redirects AWS API calls to LocalStack endpoints without modifying provider config manually.

## Trade-offs

With one more week I would add: multi-account AWS support using AWS Organizations and role assumption, GCP provider implementation using the google-cloud Python SDK, a proper test suite using moto for unit testing without needing LocalStack running, Slack notifications when the janitor finds orphans above a cost threshold, and a small web dashboard showing waste trends over time.

## AI usage disclosure

- Used Claude to help structure Terraform modules and debug LocalStack compatibility issues.
- Claude incorrectly suggested using aws_s3_bucket_lifecycle_configuration which times out on LocalStack 3.0.0 — discovered this through actual testing and removed it.
- Wrote the janitor.py core scanning logic manually to ensure I understood every AWS API call being made.
