#!/bin/bash
# Comprehensive security audit script for XrayRadar
# Runs all security checks: bandit, pip-audit, npm audit

echo "========================================="
echo "Security Audit for XrayRadar"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

EXIT_CODE=0
REPORT_DIR="${HOME}/.xrayradar-security-reports"
mkdir -p "$REPORT_DIR"

# 1. Backend: Bandit static analysis
echo -e "${YELLOW}[1/3] Running Bandit static security scan...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    EXIT_CODE=1
elif ! uv run bandit --version &> /dev/null; then
    echo -e "${YELLOW}⚠ Bandit not installed. Installing...${NC}"
    uv pip install bandit &> /dev/null || true
fi

if command -v uv &> /dev/null; then
    BANDIT_REPORT="${REPORT_DIR}/bandit-report.json"
    if uv run bandit -r src -f json > "$BANDIT_REPORT" 2>&1; then
        echo -e "${GREEN}✓ Bandit scan completed${NC}"
        # Count issues by severity (bandit may exit with non-zero if issues found, but still produces valid JSON)
        if [ -f "$BANDIT_REPORT" ] && command -v jq &> /dev/null; then
            HIGH=$(jq -r '[.results[]? | select(.issue_severity=="HIGH")] | length' "$BANDIT_REPORT" 2>/dev/null || echo "0")
            MEDIUM=$(jq -r '[.results[]? | select(.issue_severity=="MEDIUM")] | length' "$BANDIT_REPORT" 2>/dev/null || echo "0")
            LOW=$(jq -r '[.results[]? | select(.issue_severity=="LOW")] | length' "$BANDIT_REPORT" 2>/dev/null || echo "0")
            
            if [ "$HIGH" != "0" ] || [ "$MEDIUM" != "0" ]; then
                echo -e "${RED}  Found: $HIGH HIGH, $MEDIUM MEDIUM, $LOW LOW severity issues${NC}"
                EXIT_CODE=1
            else
                echo -e "${GREEN}  Found: $HIGH HIGH, $MEDIUM MEDIUM, $LOW LOW severity issues${NC}"
            fi
        elif [ -f "$BANDIT_REPORT" ]; then
            echo -e "${YELLOW}  Report generated (install 'jq' for detailed summary)${NC}"
        fi
        echo "  Full report: $BANDIT_REPORT"
    else
        # Check if report was still generated (bandit exits non-zero on findings)
        if [ -f "$BANDIT_REPORT" ]; then
            echo -e "${GREEN}✓ Bandit scan completed (with findings)${NC}"
            if command -v jq &> /dev/null; then
                HIGH=$(jq -r '[.results[]? | select(.issue_severity=="HIGH")] | length' "$BANDIT_REPORT" 2>/dev/null || echo "0")
                MEDIUM=$(jq -r '[.results[]? | select(.issue_severity=="MEDIUM")] | length' "$BANDIT_REPORT" 2>/dev/null || echo "0")
                LOW=$(jq -r '[.results[]? | select(.issue_severity=="LOW")] | length' "$BANDIT_REPORT" 2>/dev/null || echo "0")
                
                if [ "$HIGH" != "0" ] || [ "$MEDIUM" != "0" ]; then
                    echo -e "${RED}  Found: $HIGH HIGH, $MEDIUM MEDIUM, $LOW LOW severity issues${NC}"
                    EXIT_CODE=1
                else
                    echo -e "${GREEN}  Found: $HIGH HIGH, $MEDIUM MEDIUM, $LOW LOW severity issues${NC}"
                fi
            fi
            echo "  Full report: $BANDIT_REPORT"
        else
            echo -e "${RED}✗ Bandit scan failed - check if bandit is installed: uv pip install bandit${NC}"
            EXIT_CODE=1
        fi
    fi
fi
echo ""

# 2. Backend: pip-audit dependency check
echo -e "${YELLOW}[2/3] Running pip-audit for Python dependencies...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv not found${NC}"
    EXIT_CODE=1
elif ! uv run pip-audit --version &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ pip-audit not installed. Installing...${NC}"
    uv pip install pip-audit &> /dev/null || true
fi

if command -v uv &> /dev/null; then
    PIP_AUDIT_REPORT="${REPORT_DIR}/pip-audit-report.json"
    # uv environments don't have pip by default, install it first
    echo -e "${YELLOW}  Installing pip in uv environment (required for pip-audit)...${NC}"
    uv pip install pip &> /dev/null || true
    
    # pip-audit may exit with non-zero if vulnerabilities found, but still produces valid output
    uv run pip-audit --format=json > "$PIP_AUDIT_REPORT" 2>&1 || true
    
    if [ -f "$PIP_AUDIT_REPORT" ] && [ -s "$PIP_AUDIT_REPORT" ]; then
        # Check if the report contains valid JSON or is an error
        if grep -q "^{" "$PIP_AUDIT_REPORT" 2>/dev/null; then
            echo -e "${GREEN}✓ pip-audit completed${NC}"
            if command -v jq &> /dev/null; then
                # Check if it's valid JSON and has vulnerabilities
                if jq -e '.dependencies' "$PIP_AUDIT_REPORT" &> /dev/null 2>&1; then
                    # Count actual vulnerabilities (not skipped packages)
                    VULNS=$(jq -r '[.dependencies[]?.vulns[]?] | length' "$PIP_AUDIT_REPORT" 2>/dev/null || echo "0")
                    SKIPPED=$(jq -r '[.dependencies[]? | select(.skip_reason != null)] | length' "$PIP_AUDIT_REPORT" 2>/dev/null || echo "0")
                    
                    if [ "$VULNS" != "0" ]; then
                        echo -e "${RED}  Found: $VULNS vulnerabilities${NC}"
                        EXIT_CODE=1
                    else
                        echo -e "${GREEN}  Found: $VULNS vulnerabilities${NC}"
                    fi
                    
                    # Note about skipped packages (like the local xrayradar-server package)
                    if [ "$SKIPPED" != "0" ]; then
                        echo -e "${YELLOW}  Note: $SKIPPED package(s) skipped (local/private packages, expected)${NC}"
                    fi
                else
                    # Check if it's an error message
                    if grep -qi "error\|traceback\|exception" "$PIP_AUDIT_REPORT"; then
                        echo -e "${YELLOW}  pip-audit encountered an error (check report)${NC}"
                        echo -e "${YELLOW}  Note: This may be due to uv environment configuration${NC}"
                        EXIT_CODE=1
                    else
                        echo -e "${GREEN}  No vulnerabilities found${NC}"
                    fi
                fi
            else
                echo -e "${YELLOW}  Report generated (install 'jq' for detailed summary)${NC}"
            fi
            echo "  Full report: $PIP_AUDIT_REPORT"
        else
            # Report is not valid JSON, likely an error
            if grep -qi "No module named pip\|pip.*not found" "$PIP_AUDIT_REPORT"; then
                echo -e "${YELLOW}⚠ pip-audit requires pip in uv environment${NC}"
                echo -e "${YELLOW}  Attempting to install pip and retry...${NC}"
                uv pip install pip &> /dev/null
                uv run pip-audit --format=json > "$PIP_AUDIT_REPORT" 2>&1 || true
                if grep -q "^{" "$PIP_AUDIT_REPORT" 2>/dev/null; then
                    echo -e "${GREEN}✓ pip-audit completed (after pip install)${NC}"
                else
                    echo -e "${YELLOW}⚠ pip-audit still having issues (check report)${NC}"
                    EXIT_CODE=1
                fi
            else
                echo -e "${YELLOW}⚠ pip-audit encountered an error (check report)${NC}"
                EXIT_CODE=1
            fi
            echo "  Full report: $PIP_AUDIT_REPORT"
        fi
    else
        echo -e "${RED}✗ pip-audit failed - check if pip-audit is installed: uv pip install pip-audit${NC}"
        EXIT_CODE=1
    fi
fi
echo ""

# 3. Frontend: npm audit
echo -e "${YELLOW}[3/3] Running npm audit for frontend dependencies...${NC}"
if [ ! -d "xrayradar-web" ]; then
    echo -e "${YELLOW}⚠ xrayradar-web directory not found, skipping${NC}"
elif ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}⚠ npm not found, skipping${NC}"
else
    cd xrayradar-web
    NPM_AUDIT_REPORT="${REPORT_DIR}/npm-audit-report.json"
    
    # npm audit may exit with non-zero if vulnerabilities found, but still produces valid JSON
    npm audit --json > "$NPM_AUDIT_REPORT" 2>&1 || true
    
    if [ -f "$NPM_AUDIT_REPORT" ] && [ -s "$NPM_AUDIT_REPORT" ]; then
        # Check if it's valid JSON (not an error message); treat clean report as success even without jq
        if grep -qE '"vulnerabilities":\s*\{\}' "$NPM_AUDIT_REPORT" 2>/dev/null && grep -qE '"total":\s*0' "$NPM_AUDIT_REPORT" 2>/dev/null; then
            echo -e "${GREEN}✓ npm audit completed${NC}"
            echo -e "${GREEN}  Found: 0 critical, 0 high, 0 moderate, 0 low${NC}"
            echo "  Full report: $NPM_AUDIT_REPORT"
        elif command -v jq &> /dev/null && jq -e '.metadata' "$NPM_AUDIT_REPORT" &> /dev/null 2>&1; then
            echo -e "${GREEN}✓ npm audit completed${NC}"
            CRITICAL=$(jq -r '.metadata.vulnerabilities.critical // 0' "$NPM_AUDIT_REPORT" 2>/dev/null || echo "0")
            HIGH=$(jq -r '.metadata.vulnerabilities.high // 0' "$NPM_AUDIT_REPORT" 2>/dev/null || echo "0")
            MODERATE=$(jq -r '.metadata.vulnerabilities.moderate // 0' "$NPM_AUDIT_REPORT" 2>/dev/null || echo "0")
            LOW=$(jq -r '.metadata.vulnerabilities.low // 0' "$NPM_AUDIT_REPORT" 2>/dev/null || echo "0")
            
            TOTAL=$((CRITICAL + HIGH + MODERATE + LOW))
            if [ "$TOTAL" != "0" ]; then
                echo -e "${RED}  Found: $CRITICAL critical, $HIGH high, $MODERATE moderate, $LOW low${NC}"
                EXIT_CODE=1
            else
                echo -e "${GREEN}  Found: $CRITICAL critical, $HIGH high, $MODERATE moderate, $LOW low${NC}"
            fi
            echo "  Full report: $NPM_AUDIT_REPORT"
        else
            # Check if it's a network error
            if grep -q "EAI_AGAIN\|getaddrinfo\|registry.npmjs.org" "$NPM_AUDIT_REPORT"; then
                echo -e "${YELLOW}⚠ npm audit requires network access (skipped in offline mode)${NC}"
                echo "  Note: Run 'npm audit' manually when online"
            else
                echo -e "${YELLOW}⚠ npm audit completed with warnings (check report)${NC}"
                echo "  Full report: $NPM_AUDIT_REPORT"
                EXIT_CODE=1
            fi
        fi
    else
        echo -e "${YELLOW}⚠ npm audit failed or requires network access${NC}"
        EXIT_CODE=1
    fi
    cd ..
fi
echo ""

# Summary
echo "========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}Security audit PASSED${NC}"
else
    echo -e "${YELLOW}Security audit completed with findings or warnings${NC}"
    echo -e "  Review reports in: ${REPORT_DIR}/"
fi
echo "========================================="
echo ""
echo "Reports saved to: $REPORT_DIR"

exit $EXIT_CODE
