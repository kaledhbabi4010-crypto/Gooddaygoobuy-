#!/usr/bin/env bash
set -euo pipefail
dotnet publish src/KHALED/KHALED.csproj -c Release -o artifacts/khaled --nologo
echo "PUBLISH_OK"
