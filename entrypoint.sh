#!/bin/bash
set -euo pipefail

sleep 3
echo "=== B17 monitor started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

python -u main.py
exit_code=$?

echo "=== B17 monitor finished with exit code ${exit_code} at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit "${exit_code}"
