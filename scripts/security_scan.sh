#!/usr/bin/env bash
# Run security scans for AERIS.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== AERIS Security Scan ==="
echo "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

FAILURES=0
REPORT="docs/SECURITY_SCAN_REPORT.md"
mkdir -p docs

cat > "$REPORT" << 'HEADER'
# AERIS Security Scan Report

> **Generated automatically. Not a certification or compliance attestation.**

HEADER

echo "## Scan Results" >> "$REPORT"
echo "" >> "$REPORT"
echo "| Tool | Status | Findings |" >> "$REPORT"
echo "|------|--------|----------|" >> "$REPORT"

# 1. Bandit (Python security linter)
echo "[1/6] Running bandit..."
if docker compose exec -T backend bandit -r app/ -f json -q 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
issues = len(data.get('results', []))
print(f'Bandit: {issues} issues')
sys.exit(1 if any(r['issue_severity'] == 'HIGH' for r in data.get('results', [])) else 0)
" 2>/dev/null; then
    echo "| Bandit | PASS | No high-severity issues |" >> "$REPORT"
else
    echo "| Bandit | REVIEW | See detailed output |" >> "$REPORT"
    FAILURES=$((FAILURES + 1))
fi

# 2. pip-audit
echo "[2/6] Running pip-audit..."
if docker compose exec -T backend pip-audit --format json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
vulns = len(data.get('dependencies', []))
print(f'pip-audit: {vulns} vulnerable packages')
sys.exit(1 if vulns > 0 else 0)
" 2>/dev/null; then
    echo "| pip-audit | PASS | No known vulnerabilities |" >> "$REPORT"
else
    echo "| pip-audit | REVIEW | See detailed output |" >> "$REPORT"
fi

# 3. ruff
echo "[3/6] Running ruff..."
if docker compose exec -T backend ruff check app/ 2>/dev/null; then
    echo "| ruff | PASS | No lint errors |" >> "$REPORT"
else
    echo "| ruff | REVIEW | Lint issues found |" >> "$REPORT"
fi

# 4. mypy
echo "[4/6] Running mypy..."
if docker compose exec -T backend mypy app/ --ignore-missing-imports 2>/dev/null; then
    echo "| mypy | PASS | Type checks pass |" >> "$REPORT"
else
    echo "| mypy | REVIEW | Type issues found |" >> "$REPORT"
fi

# 5. npm audit
echo "[5/6] Running npm audit..."
echo "| npm audit | SKIPPED | Frontend not yet built |" >> "$REPORT"

# 6. detect-secrets
echo "[6/6] Running detect-secrets..."
if docker compose exec -T backend detect-secrets scan --all-files 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
secrets = sum(len(v) for v in data.get('results', {}).values())
print(f'detect-secrets: {secrets} potential secrets')
sys.exit(1 if secrets > 0 else 0)
" 2>/dev/null; then
    echo "| detect-secrets | PASS | No secrets detected in code |" >> "$REPORT"
else
    echo "| detect-secrets | REVIEW | Potential secrets found |" >> "$REPORT"
fi

echo "" >> "$REPORT"
echo "---" >> "$REPORT"
echo "*Scan completed: $(date -u +"%Y-%m-%dT%H:%M:%SZ")*" >> "$REPORT"

echo ""
echo "[+] Security scan complete. Report: $REPORT"
echo "    Findings requiring review: $FAILURES"
