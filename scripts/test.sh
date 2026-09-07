#!/usr/bin/env bash
set -euo pipefail
dotnet test KHALED.sln -c Release --no-build --nologo || exit 5
echo "TEST_OK"
