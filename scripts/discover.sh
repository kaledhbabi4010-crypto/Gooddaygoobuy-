#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
{
  echo "dotnet=$(dotnet --version)"
  echo "os=$(uname -s)"
  echo "projects=$(find . -name '*.csproj' | sort | tr '\n' ' ')"
} > evidence/discovery.txt
cat evidence/discovery.txt
