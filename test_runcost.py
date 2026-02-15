"""RunCost test suite — 12 tests covering all 5 rules + output formats."""
import pytest
from runcost import analyze_workflow, to_json
from main import to_sarif

WF_BAD = """
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest
"""

WF_GOOD = """
name: CI
on: [push]
concurrency:
  group: ci-test
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/cache@v3
      - run: pip install -r requirements.txt
      - run: pytest
"""

WF_MACOS = """
name: macOS Build
on: [push]
jobs:
  build:
    runs-on: macos-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: echo hello
"""


def _rule_ids(content):
    return [f.rule_id for f in analyze_workflow(content).findings]


def test_rc001_missing_cache():
    assert "RC001" in _rule_ids(WF_BAD)


def test_rc002_no_timeout():
    assert "RC002" in _rule_ids(WF_BAD)


def test_rc003_no_concurrency_group():
    assert "RC003" in _rule_ids(WF_BAD)


def test_rc004_expensive_macos_runner():
    assert "RC004" in _rule_ids(WF_MACOS)


def test_rc005_deep_clone():
    assert "RC005" in _rule_ids(WF_MACOS)


def test_good_workflow_zero_findings():
    r = analyze_workflow(WF_GOOD)
    assert len(r.findings) == 0


def test_cost_estimation_positive():
    r = analyze_workflow(WF_BAD)
    assert r.cost > 0


def test_savings_equals_sum_of_findings():
    r = analyze_workflow(WF_BAD)
    assert r.savings == sum(f.savings for f in r.findings)


def test_json_output_structure():
    j = to_json(analyze_workflow(WF_BAD))
    assert j["findings_count"] > 0
    assert j["monthly_cost"] > 0
    assert all("rule_id" in f for f in j["findings"])


def test_sarif_output_structure():
    s = to_sarif(analyze_workflow(WF_BAD))
    assert s["version"] == "2.1.0"
    assert len(s["runs"][0]["results"]) > 0


def test_invalid_yaml_returns_empty_report():
    r = analyze_workflow(":::invalid yaml:::")
    assert len(r.findings) == 0 and r.cost == 0


@pytest.mark.parametrize("content", ["", "null", "42", "[]"])
def test_non_dict_yaml_returns_empty_report(content):
    r = analyze_workflow(content)
    assert isinstance(r.findings, list) and r.cost == 0
