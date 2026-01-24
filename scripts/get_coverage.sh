#!/bin/bash
# Script to extract test coverage percentages for README badges

set -e

echo "Extracting test coverage..."

# Backend coverage
if command -v uv &> /dev/null; then
  BACKEND_COV=$(uv run pytest --cov=src/xrayradar_server --cov-report=term --quiet 2>&1 | grep -E "^TOTAL" | awk '{print $NF}' | sed 's/%//' || echo "0")
else
  BACKEND_COV="0"
fi

# Frontend coverage
if [ -d "xrayradar-web" ] && command -v npm &> /dev/null; then
  cd xrayradar-web
  FRONTEND_COV=$(npm run test:coverage -- --run 2>&1 | grep -E "^All files" | awk '{print $4}' | sed 's/%//' || echo "0")
  cd ..
else
  FRONTEND_COV="0"
fi

echo "Backend: ${BACKEND_COV}%"
echo "Frontend: ${FRONTEND_COV}%"

# Generate badge colors
if (( $(echo "$BACKEND_COV >= 90" | bc -l) )); then
  BACKEND_COLOR="brightgreen"
elif (( $(echo "$BACKEND_COV >= 75" | bc -l) )); then
  BACKEND_COLOR="green"
elif (( $(echo "$BACKEND_COV >= 50" | bc -l) )); then
  BACKEND_COLOR="yellow"
else
  BACKEND_COLOR="red"
fi

if (( $(echo "$FRONTEND_COV >= 90" | bc -l) )); then
  FRONTEND_COLOR="brightgreen"
elif (( $(echo "$FRONTEND_COV >= 75" | bc -l) )); then
  FRONTEND_COLOR="green"
elif (( $(echo "$FRONTEND_COV >= 50" | bc -l) )); then
  FRONTEND_COLOR="yellow"
else
  FRONTEND_COLOR="red"
fi

echo ""
echo "Badge URLs:"
echo "![Backend Coverage](https://img.shields.io/badge/backend%20coverage-${BACKEND_COV}%25-${BACKEND_COLOR}?style=flat-square)"
echo "![Frontend Coverage](https://img.shields.io/badge/frontend%20coverage-${FRONTEND_COV}%25-${FRONTEND_COLOR}?style=flat-square)"
