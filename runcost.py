"""RunCost — GitHub Actions cost analysis engine."""
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any

COST_PER_MIN = {"ubuntu": 0.008, "linux": 0.008, "windows": 0.016, "macos": 0.08}


@dataclass
class Finding:
    rule_id: str
    severity: str
    job: str
    message: str
    suggestion: str
    savings: float = 0.0


@dataclass
class Report:
    path: str
    findings: List[Finding] = field(default_factory=list)
    cost: float = 0.0
    savings: float = 0.0


def _runner_os(runs_on) -> str:
    label = str(runs_on[0] if isinstance(runs_on, list) else runs_on).lower()
    return next((k for k in COST_PER_MIN if k in label), "ubuntu")


def _check_job(name: str, job: dict, steps: list) -> List[Finding]:
    findings = []
    uses = " ".join(s.get("uses", "") for s in steps if isinstance(s, dict))
    runs = " ".join(s.get("run", "") for s in steps if isinstance(s, dict))
    has_cache = "actions/cache" in uses
    pkg_managers = {
        "npm": ["npm install", "npm ci"],
        "pip": ["pip install"],
        "go": ["go build", "go test"],
    }
    for mgr, keywords in pkg_managers.items():
        if any(kw in runs for kw in keywords) and not has_cache:
            findings.append(Finding(
                "RC001", "high", name,
                f"No cache configured for {mgr}",
                f"Add actions/cache for {mgr} dependencies", 15.0))
    if "timeout-minutes" not in job:
        findings.append(Finding(
            "RC002", "critical", name,
            "No timeout-minutes — runaway jobs burn unlimited credits",
            "Add 'timeout-minutes: 30'", 50.0))
    if "macos" in str(job.get("runs-on", "")).lower():
        findings.append(Finding(
            "RC004", "medium", name,
            "macOS runner costs 10x more than Linux",
            "Use ubuntu-latest if possible", 40.0))
    for s in steps:
        if not isinstance(s, dict):
            continue
        if "actions/checkout" in s.get("uses", ""):
            if s.get("with", {}).get("fetch-depth") == 0:
                findings.append(Finding(
                    "RC005", "low", name,
                    "Full git clone (fetch-depth: 0) wastes time",
                    "Use default shallow clone", 5.0))
    return findings


def analyze_workflow(content: str, path: str = "workflow.yml") -> Report:
    try:
        wf = yaml.safe_load(content)
    except yaml.YAMLError:
        return Report(path=path)
    if not isinstance(wf, dict):
        return Report(path=path)
    report = Report(path=path)
    on_val = wf.get("on", wf.get(True, {}))
    if isinstance(on_val, list):
        triggers = on_val
    elif isinstance(on_val, dict):
        triggers = list(on_val.keys())
    else:
        triggers = [str(on_val)]
    if "concurrency" not in wf and "push" in triggers and "pull_request" in triggers:
        report.findings.append(Finding(
            "RC003", "medium", "(workflow)",
            "No concurrency group — duplicate runs on push+PR",
            "Add concurrency group to cancel outdated runs", 30.0))
    for jname, job in wf.get("jobs", {}).items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps", [])
        ros = _runner_os(job.get("runs-on", "ubuntu-latest"))
        timeout = job.get("timeout-minutes", 30)
        matrix = job.get("strategy", {}).get("matrix", {})
        mult = 1
        for v in matrix.values():
            mult *= len(v) if isinstance(v, list) else 1
        report.cost += COST_PER_MIN.get(ros, 0.008) * min(timeout, 15) * 100 * mult
        report.findings.extend(_check_job(jname, job, steps))
    report.savings = sum(f.savings for f in report.findings)
    return report


def to_json(r: Report) -> dict:
    return {
        "file": r.path, "monthly_cost": round(r.cost, 2),
        "potential_savings": round(r.savings, 2),
        "findings_count": len(r.findings),
        "findings": [{"rule_id": f.rule_id, "severity": f.severity, "job": f.job,
                       "message": f.message, "suggestion": f.suggestion,
                       "savings": f.savings} for f in r.findings]}
