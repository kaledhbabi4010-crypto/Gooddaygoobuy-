#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
dotnet --info > evidence/diagnose.txt 2>&1 || true
echo "DIAGNOSE_OK"
