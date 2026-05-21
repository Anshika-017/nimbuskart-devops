# Submission — DevOps Engineer Assignment

**Candidate name:** Anshika
**Email:** 2024uch0005@iitjammu.ac.in
**Date submitted:** 2026-05-21
**Hours spent (approximate):** 8

## Deliverables checklist

- [x] Part A: Terraform code under /terraform applies cleanly on LocalStack
- [x] Part A: `terraform validate` and `terraform fmt -check` both pass
- [x] Part B: Janitor script runs in --dry-run mode and produces report.json
- [x] Part B: GitHub Actions workflow runs green on a fresh PR
- [x] Part B: --delete mode respects Protected=true tag
- [x] Part C: DESIGN.md is present and within 2 pages
- [ ] Walkthrough video link below is accessible (unlisted is fine)

## Walkthrough video

Link: (to be added)
Length: max 5 minutes

## Sample report

Path to a sample report.json produced by your script: samples/report.example.json

## Known limitations

- S3 lifecycle configuration removed due to LocalStack 3.0.0 timeout bug
- Latest LocalStack requires paid license so pinned to 3.0.0
- Stopped EC2 instances show age_days=0 in LocalStack as LaunchTime is not tracked realistically
- GCP and Azure providers not implemented (architecture designed for it)
- No unit tests yet (would use moto library)

## AI usage disclosure

- Used Claude to help structure Terraform modules, debug LocalStack issues, and write boilerplate
- Claude incorrectly suggested aws_s3_bucket_lifecycle_configuration which times out on LocalStack 3.0.0
- Wrote the core janitor scanning logic (scan_ebs_volumes, scan_stopped_instances etc.) manually to ensure full understanding of boto3 API calls
