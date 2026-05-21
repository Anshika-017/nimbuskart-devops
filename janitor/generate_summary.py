import json
import sys

with open("report.json") as f:
    report = json.load(f)

lines = []
lines.append("# Cost Janitor Report")
lines.append("**Scan Time:** " + report["scan_timestamp"])
lines.append("**Account:** " + report["account_id"])
lines.append("**Region:** " + report["region"])
lines.append("## Summary")
lines.append("- **Total Orphans:** " + str(report["summary"]["total_orphans"]))
lines.append("- **Estimated Monthly Waste:** $" + str(report["summary"]["estimated_monthly_waste_usd"]))
lines.append("## Findings")
for f in report["findings"]:
    lines.append("### " + f["resource_type"] + " - " + f["resource_id"])
    lines.append("- **Reason:** " + f["reason"])
    lines.append("- **Age:** " + str(f["age_days"]) + " days")
    lines.append("- **Monthly Cost:** $" + str(f["estimated_monthly_cost_usd"]))
    lines.append("- **Suggested Action:** " + f["suggested_action"])

with open("summary.md", "w") as f:
    f.write("\n".join(lines))
print("Summary generated!")
