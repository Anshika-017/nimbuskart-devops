# Design Note — Cost Janitor Production Hardening

## Multi-Cloud Reality

To support GCP and later Azure without rewriting the core, the Janitor would be restructured around a provider abstraction pattern:
janitor/
core/
base_scanner.py      # Abstract base class with scan(), report() interface
report.py            # Shared report schema and output logic
constants.py         # Shared pricing constants
providers/
aws/
scanner.py         # AWS implementation using boto3
auth.py            # AWS credential handling
gcp/
scanner.py         # GCP implementation using google-cloud SDK
auth.py            # GCP service account handling
azure/
scanner.py         # Azure implementation using azure-sdk
auth.py            # Azure managed identity handling
main.py                # Entry point, loads provider based on --cloud flag

Each provider implements the same interface: `scan_unattached_volumes()`, `scan_stopped_instances()`, `scan_unassociated_ips()`, `scan_untagged_resources()`. The core report generation and CLI logic never changes when adding a new cloud.

## Permissions

**Dry-run mode** requires read-only access only:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostJanitorReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeInstances",
        "ec2:DescribeAddresses",
        "ec2:DescribeTags",
        "s3:ListAllMyBuckets",
        "s3:GetBucketTagging",
        "tag:GetResources"
      ],
      "Resource": "*"
    }
  ]
}
```

**Delete mode** adds these actions on top of the above:
- `ec2:DeleteVolume`
- `ec2:TerminateInstances`
- `ec2:ReleaseAddress`

Delete mode should use a separate IAM role that requires MFA or role assumption, never the same credentials as dry-run.

## Safety Net — Two Failure Modes

**1. Deleting a volume that looks unattached but is needed**
A volume can be in "available" state temporarily during an instance replacement (e.g. blue/green deployment detaches old volume before new one attaches). Naively deleting it causes data loss. Guardrail: only delete volumes that have been unattached for more than N days (configurable, default 7), checked via the volume's `CreateTime` and attachment history in CloudTrail.

**2. Terminating a stopped instance that is intentionally kept**
A stopped instance may hold an Elastic IP, contain important data, or be a bastion host kept off to save costs. Terminating it causes outage. Guardrails: (a) never auto-delete without `Protected=false` explicitly set, (b) require two-step confirmation in delete mode, (c) send a Slack/email notification 24 hours before deletion with a cancellation link.

## Observability

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| `janitor.orphans.total` | report.json summary | > 10 orphans triggers Slack alert |
| `janitor.waste.monthly_usd` | report.json summary | > $500/month triggers PagerDuty |
| `janitor.scan.duration_seconds` | Script timing | > 300s means API throttling |
| `janitor.deletions.count` | Delete mode logs | > 5 deletions/run requires manual approval |
| `janitor.errors.count` | Exception handler | Any error triggers immediate alert |

Metrics would be published to CloudWatch (AWS), with a Grafana dashboard pulling from CloudWatch Metrics. Alerts route to Slack for informational and PagerDuty for critical.

## What I Did Not Build

I deliberately left out several things due to time constraints: multi-account AWS support (would require assuming roles across accounts via AWS Organizations), GCP and Azure provider implementations (the abstractions are in place but not implemented), a web dashboard for the FinOps team to view trends over time, snapshot and RDS orphan detection (common sources of waste but more complex to safely delete), cost anomaly detection using historical baselines (vs. static thresholds), and Terraform state-aware deletion (cross-referencing tfstate before deleting to avoid removing managed resources). These would be the first priorities in a production engagement.
