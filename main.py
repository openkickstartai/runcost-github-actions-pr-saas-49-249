"""RunCost CLI — GitHub Actions cost analyzer & optimizer."""
import click
import json
import glob
import os
from runcost import analyze_workflow, to_json


def to_sarif(r):
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "RunCost", "version": "0.1.0",
                "rules": [{"id": f.rule_id, "shortDescription": {"text": f.message}}
                           for f in r.findings]}},
            "results": [
                {"ruleId": f.rule_id,
                 "level": "error" if f.severity == "critical" else "warning",
                 "message": {"text": f"{f.message}. Fix: {f.suggestion}"},
                 "locations": [{"physicalLocation": {
                     "artifactLocation": {"uri": r.path}}}]}
                for f in r.findings]}]}


@click.command()
@click.argument("path", default=".github/workflows")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["text", "json", "sarif"]), default="text")
@click.option("--output", "-o", type=click.Path(), default=None)
def main(path, fmt, output):
    """Analyze GitHub Actions workflows for cost optimization."""
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        files = glob.glob(os.path.join(path, "*.yml")) + \
                glob.glob(os.path.join(path, "*.yaml"))
    else:
        click.echo("No workflow files found."); return
    if not files:
        click.echo("No workflow files found."); return
    reports = []
    for fp in files:
        with open(fp) as fh:
            reports.append(analyze_workflow(fh.read(), fp))
    if fmt == "json":
        out = json.dumps([to_json(r) for r in reports], indent=2)
    elif fmt == "sarif":
        out = json.dumps(to_sarif(reports[0]) if reports else {}, indent=2)
    else:
        lines, tc, ts = [], 0.0, 0.0
        for r in reports:
            lines.append(f"\n📄 {r.path}")
            lines.append(f"   💰 Est. monthly cost: ${r.cost:.2f}")
            tc += r.cost
            ts += r.savings
            for finding in r.findings:
                icon = {"critical": "🔴", "high": "🟠",
                        "medium": "🟡", "low": "🔵"}.get(finding.severity, "⚪")
                lines.append(f"   {icon} [{finding.rule_id}] {finding.message}")
                lines.append(f"      → {finding.suggestion} (~${finding.savings:.0f}/mo)")
        lines.append(f"\n{'=' * 50}")
        lines.append(f"💰 Total: ${tc:.2f}/mo | 💡 Potential savings: ${ts:.2f}/mo")
        out = "\n".join(lines)
    if output:
        with open(output, "w") as fh:
            fh.write(out)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(out)


if __name__ == "__main__":
    main()
