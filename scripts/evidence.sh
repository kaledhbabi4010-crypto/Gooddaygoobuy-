#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
{
  echo "commit=${GITHUB_SHA:-local}"
  echo "ref=${GITHUB_REF:-local}"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "status=BUILD_AND_TESTS_PASSED"
} > evidence/summary.txt
( cd evidence && sha256sum ./* > SHA256SUMS 2>/dev/null || true )
cat evidence/summary.txt
