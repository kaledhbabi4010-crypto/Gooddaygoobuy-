#!/usr/bin/env bash
set -euo pipefail
KHALED_ROOT="$(pwd)" dotnet run --project src/KHALED/KHALED.csproj -c Release --no-build -- verify
