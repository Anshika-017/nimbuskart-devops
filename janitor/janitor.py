#!/usr/bin/env python3
"""
Cost Janitor - Detects orphaned AWS resources and estimates waste.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import boto3

from constants import (
    DEFAULT_STOPPED_DAYS,
    DEFAULT_EBS_SIZE_GB,
    EBS_GP3_COST_PER_GB_MONTH,
    EC2_T3_MICRO_COST_PER_HOUR,
    HOURS_PER_MONTH,
    EIP_COST_PER_HOUR,
)

REQUIRED_TAGS = ["Project", "Environment", "Owner"]
LOCALSTACK_ENDPOINT = "http://localhost:4566"


def get_boto3_client(service):
    return boto3.client(
        service,
        region_name="us-east-1",
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def age_in_days(dt):
    if dt is None:
        return 0
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).days


def check_missing_tags(tags_list):
    tags = {t["Key"]: t["Value"] for t in (tags_list or [])}
    missing = [t for t in REQUIRED_TAGS if not tags.get(t)]
    return tags, missing


def is_protected(tags_dict):
    return tags_dict.get("Protected", "").lower() == "true"


def scan_ebs_volumes(ec2):
    findings = []
    response = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
    for vol in response.get("Volumes", []):
        tags_dict, missing = check_missing_tags(vol.get("Tags", []))
        size = vol.get("Size", DEFAULT_EBS_SIZE_GB)
        cost = round(size * EBS_GP3_COST_PER_GB_MONTH, 2)
        create_time = vol.get("CreateTime")
        findings.append({
            "resource_id": vol["VolumeId"],
            "resource_type": "ebs_volume",
            "reason": "unattached",
            "age_days": age_in_days(create_time),
            "estimated_monthly_cost_usd": cost,
            "tags": {t: tags_dict.get(t) for t in REQUIRED_TAGS},
            "suggested_action": "delete",
            "safe_to_auto_delete": not is_protected(tags_dict) and not missing,
            "_protected": is_protected(tags_dict),
        })
    return findings


def scan_stopped_instances(ec2, stopped_days):
    findings = []
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    )
    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            tags_dict, missing = check_missing_tags(inst.get("Tags", []))
            launch_time = inst.get("LaunchTime")
            days = age_in_days(launch_time)
            if days < stopped_days:
                continue
            cost = round(EC2_T3_MICRO_COST_PER_HOUR * HOURS_PER_MONTH, 2)
            findings.append({
                "resource_id": inst["InstanceId"],
                "resource_type": "ec2_instance",
                "reason": f"stopped for {days} days",
                "age_days": days,
                "estimated_monthly_cost_usd": cost,
                "tags": {t: tags_dict.get(t) for t in REQUIRED_TAGS},
                "suggested_action": "terminate",
                "safe_to_auto_delete": not is_protected(tags_dict) and not missing,
                "_protected": is_protected(tags_dict),
            })
    return findings


def scan_unattached_eips(ec2):
    findings = []
    response = ec2.describe_addresses()
    for addr in response.get("Addresses", []):
        if addr.get("AssociationId"):
            continue
        tags_dict, missing = check_missing_tags(addr.get("Tags", []))
        cost = round(EIP_COST_PER_HOUR * HOURS_PER_MONTH, 2)
        findings.append({
            "resource_id": addr.get("AllocationId", addr.get("PublicIp", "unknown")),
            "resource_type": "elastic_ip",
            "reason": "not associated with any instance",
            "age_days": 0,
            "estimated_monthly_cost_usd": cost,
            "tags": {t: tags_dict.get(t) for t in REQUIRED_TAGS},
            "suggested_action": "release",
            "safe_to_auto_delete": not is_protected(tags_dict),
            "_protected": is_protected(tags_dict),
        })
    return findings


def scan_untagged_resources(ec2):
    findings = []
    response = ec2.describe_instances()
    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            if inst.get("State", {}).get("Name") == "terminated":
                continue
            tags_dict, missing = check_missing_tags(inst.get("Tags", []))
            if missing:
                findings.append({
                    "resource_id": inst["InstanceId"],
                    "resource_type": "ec2_instance",
                    "reason": f"missing tags: {', '.join(missing)}",
                    "age_days": age_in_days(inst.get("LaunchTime")),
                    "estimated_monthly_cost_usd": 0.0,
                    "tags": {t: tags_dict.get(t) for t in REQUIRED_TAGS},
                    "suggested_action": "tag",
                    "safe_to_auto_delete": False,
                    "_protected": is_protected(tags_dict),
                })
    return findings


def delete_resources(ec2, findings):
    for f in findings:
        if f.get("_protected"):
            print(f"  SKIPPING protected resource: {f['resource_id']}")
            continue
        rid = f["resource_id"]
        rtype = f["resource_type"]
        try:
            if rtype == "ebs_volume" and f["reason"] == "unattached":
                ec2.delete_volume(VolumeId=rid)
                print(f"  DELETED EBS volume: {rid}")
            elif rtype == "elastic_ip":
                ec2.release_address(AllocationId=rid)
                print(f"  RELEASED Elastic IP: {rid}")
            elif rtype == "ec2_instance" and "stopped" in f["reason"]:
                ec2.terminate_instances(InstanceIds=[rid])
                print(f"  TERMINATED EC2 instance: {rid}")
        except Exception as e:
            print(f"  ERROR deleting {rid}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Cost Janitor - Find orphaned AWS resources")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only, no deletions")
    parser.add_argument("--delete", action="store_true", default=False, help="Delete orphaned resources")
    parser.add_argument("--stopped-days", type=int, default=DEFAULT_STOPPED_DAYS)
    parser.add_argument("--output", default="report.json", help="Output file path")
    args = parser.parse_args()

    delete_mode = args.delete and not args.dry_run

    ec2 = get_boto3_client("ec2")

    print("Scanning EBS volumes...")
    findings = scan_ebs_volumes(ec2)

    print("Scanning stopped EC2 instances...")
    findings += scan_stopped_instances(ec2, args.stopped_days)

    print("Scanning unattached Elastic IPs...")
    findings += scan_unattached_eips(ec2)

    print("Scanning untagged resources...")
    findings += scan_untagged_resources(ec2)

    # Deduplicate by resource_id
    seen = set()
    unique_findings = []
    for f in findings:
        if f["resource_id"] not in seen:
            seen.add(f["resource_id"])
            unique_findings.append(f)
    findings = unique_findings

    # Remove internal fields before output
    clean_findings = [{k: v for k, v in f.items() if not k.startswith("_")} for f in findings]

    total_waste = round(sum(f["estimated_monthly_cost_usd"] for f in clean_findings), 2)

    report = {
        "scan_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account_id": "000000000000",
        "region": "us-east-1",
        "summary": {
            "total_orphans": len(clean_findings),
            "estimated_monthly_waste_usd": total_waste,
        },
        "findings": clean_findings,
    }

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nReport saved to {args.output}")
    print(f"Total orphans found: {len(clean_findings)}")
    print(f"Estimated monthly waste: ${total_waste}")

    if delete_mode:
        print("\nRunning in DELETE mode...")
        delete_resources(ec2, findings)

    if clean_findings:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
