#!/usr/bin/env bash
set -euo pipefail
test -f KHALED-MASTER-PLAN.md || { echo "PLAN_MISSING"; exit 3; }
test -f bootstrap/manifest.json || { echo "MANIFEST_MISSING"; exit 3; }
echo "PLAN_OK"
