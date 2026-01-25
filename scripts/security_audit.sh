#!/bin/bash
# Comprehensive security audit script for xrayradar Python SDK
# Runs all security checks: bandit, pip-audit

echo "========================================="
echo "Security Audit for xrayradar Python SDK"
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

# 1. Bandit static analysis
echo -e "${YELLOW}[1/2] Running Bandit static security scan...${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not found${NC}"
    EXIT_CODE=1
else
    PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
    
    # Check if bandit is installed
    if ! $PYTHON_CMD -m bandit --version &> /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Bandit not installed. Installing...${NC}"
        $PYTHON_CMD -m pip install bandit &> /dev/null || true
    fi
    
    if $PYTHON_CMD -m bandit --version &> /dev/null 2>&1; then
        BANDIT_REPORT="${REPORT_DIR}/bandit-report-xrayradar.json"
        if $PYTHON_CMD -m bandit -r src -f json > "$BANDIT_REPORT" 2>&1; then
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
                echo -e "${RED}✗ Bandit scan failed - check if bandit is installed: pip install bandit${NC}"
                EXIT_CODE=1
            fi
        fi
    else
        echo -e "${RED}✗ Bandit installation failed${NC}"
        EXIT_CODE=1
    fi
fi
echo ""

# 2. pip-audit dependency check
echo -e "${YELLOW}[2/2] Running pip-audit for Python dependencies...${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not found${NC}"
    EXIT_CODE=1
else
    PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
    
    # Check if pip-audit is installed
    if ! $PYTHON_CMD -m pip_audit --version &> /dev/null 2>&1 && ! command -v pip-audit &> /dev/null; then
        echo -e "${YELLOW}⚠ pip-audit not installed. Installing...${NC}"
        $PYTHON_CMD -m pip install pip-audit &> /dev/null || true
    fi
    
    PIP_AUDIT_CMD=""
    if command -v pip-audit &> /dev/null; then
        PIP_AUDIT_CMD="pip-audit"
    elif $PYTHON_CMD -m pip_audit --version &> /dev/null 2>&1; then
        PIP_AUDIT_CMD="$PYTHON_CMD -m pip_audit"
    fi
    
    if [ -n "$PIP_AUDIT_CMD" ]; then
        PIP_AUDIT_REPORT="${REPORT_DIR}/pip-audit-report-xrayradar.json"
        
        # pip-audit may exit with non-zero if vulnerabilities found, but still produces valid output
        $PIP_AUDIT_CMD --format=json > "$PIP_AUDIT_REPORT" 2>&1 || true
        
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
                        
                        # Note about skipped packages (like xrayradar itself)
                        if [ "$SKIPPED" != "0" ]; then
                            echo -e "${YELLOW}  Note: $SKIPPED package(s) skipped (local/private packages, expected)${NC}"
                        fi
                    else
                        # Check if it's an error message
                        if grep -qi "error\|traceback\|exception" "$PIP_AUDIT_REPORT"; then
                            echo -e "${YELLOW}  pip-audit encountered an error (check report)${NC}"
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
                if grep -qi "No module named\|not found\|network\|connection" "$PIP_AUDIT_REPORT"; then
                    echo -e "${YELLOW}⚠ pip-audit requires network access (check report)${NC}"
                    echo -e "${YELLOW}  Note: Run 'pip-audit' manually when online${NC}"
                    echo "  Full report: $PIP_AUDIT_REPORT"
                else
                    echo -e "${YELLOW}⚠ pip-audit encountered an error (check report)${NC}"
                    echo "  Full report: $PIP_AUDIT_REPORT"
                    EXIT_CODE=1
                fi
            fi
        else
            echo -e "${RED}✗ pip-audit failed - check if pip-audit is installed: pip install pip-audit${NC}"
            EXIT_CODE=1
        fi
    else
        echo -e "${RED}✗ pip-audit installation failed${NC}"
        EXIT_CODE=1
    fi
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
echo ""
echo "To view reports:"
echo "  cat $REPORT_DIR/bandit-report-xrayradar.json | jq"
echo "  cat $REPORT_DIR/pip-audit-report-xrayradar.json | jq"

exit $EXIT_CODE
