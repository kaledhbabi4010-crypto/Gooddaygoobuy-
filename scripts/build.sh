#!/usr/bin/env bash
set -euo pipefail
dotnet build KHALED.sln -c Release --nologo || exit 4
echo "BUILD_OK"
