# 🔥 RunCost — GitHub Actions Cost Burn Analyzer

Stop bleeding money on GitHub Actions. RunCost scans your workflow files,
estimates monthly costs, and finds optimization opportunities automatically.

## 🚀 Quick Start

```bash
pip install -r requirements.txt

# Scan default .github/workflows/ directory
python main.py

# Scan a specific file with JSON output
python main.py .github/workflows/ci.yml -f json

# Export SARIF for GitHub Code Scanning
python main.py -f sarif -o runcost.sarif
```

## 📊 Why Pay for RunCost?

Teams with 10+ repos typically spend **$500–$5,000/mo** on GitHub Actions without realizing it.
RunCost finds **30–60% savings** in the first scan:

| Before RunCost | After RunCost |
|---|---|
| No visibility into CI spend | Per-workflow cost breakdown |
| Runaway jobs burn credits overnight | Timeout rules catch every job |
| Cache misses add 5-10 min/run | Cache rules save ~$15/mo per workflow |
| Duplicate runs on push+PR | Concurrency groups cut 30% waste |

## 🔍 Built-in Rules

| Rule | Severity | Description | Est. Savings |
|------|----------|-------------|-------------|
| RC001 | 🟠 High | Missing dependency cache (npm/pip/go) | ~$15/mo |
| RC002 | 🔴 Critical | No `timeout-minutes` — runaway job risk | ~$50/mo |
| RC003 | 🟡 Medium | No concurrency group on push+PR triggers | ~$30/mo |
| RC004 | 🟡 Medium | macOS runner (10x cost vs Linux) | ~$40/mo |
| RC005 | 🔵 Low | Full git clone (`fetch-depth: 0`) | ~$5/mo |

## 💰 Pricing

| Feature | Free | Pro $49/mo | Team $149/mo | Enterprise $249/mo |
|---------|------|-----------|-------------|-------------------|
| Workflow scanning | 3 files | Unlimited | Unlimited | Unlimited |
| Built-in rules (5) | ✅ | ✅ | ✅ | ✅ |
| Text output | ✅ | ✅ | ✅ | ✅ |
| JSON / SARIF export | ❌ | ✅ | ✅ | ✅ |
| Auto-fix PR generation | ❌ | ✅ | ✅ | ✅ |
| Slack / Teams alerts | ❌ | ✅ | ✅ | ✅ |
| Multi-repo dashboard | ❌ | ❌ | ✅ | ✅ |
| Cost trend tracking | ❌ | ❌ | ✅ | ✅ |
| Budget threshold alerts | ❌ | ❌ | ✅ | ✅ |
| Custom rules engine | ❌ | ❌ | ❌ | ✅ |
| SSO + audit logs | ❌ | ❌ | ❌ | ✅ |
| Dedicated support | ❌ | ❌ | ❌ | ✅ |

## 🏗️ CI Integration

```yaml
# Add to your workflow
- name: RunCost Analysis
  run: |
    pip install pyyaml click
    python main.py .github/workflows -f sarif -o runcost.sarif
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: runcost.sarif
```

## License

MIT — Free core, paid plans for advanced features.
