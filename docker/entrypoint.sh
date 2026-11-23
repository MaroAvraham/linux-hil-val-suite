#!/usr/bin/env bash
set -euo pipefail

# יצירת תיקיות פלט במקרה שהן לא קיימות
mkdir -p /app/reports /app/logs

echo "=========================================="
echo " Starting Linux HIL Validation Suite"
echo " Args: ${*:-<default>}"
echo "=========================================="

# exec מחליף את תהליך ה-Bash ב-pytest כך שקוד היציאה של pytest
# הופך אוטומטית לקוד היציאה של הקונטיינר כולו.
exec pytest -v \
  --html=/app/reports/report.html \
  --self-contained-html \
  --junitxml=/app/reports/junit.xml \
  "$@"