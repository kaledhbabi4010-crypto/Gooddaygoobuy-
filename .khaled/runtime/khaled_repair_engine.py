#!/usr/bin/env python3
"""
KHALED SELF-MAINTENANCE ENGINE V7

Purpose:
REAL BUILD FAILURE
    -> read evidence
    -> ask Gemini for MINIMAL unified diff
    -> validate patch
    -> apply patch
    -> stop safely

No fake success.
No runtime claim.
No broad file rewriting.
"""

import os
import sys
import re
import json
import asyncio
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEWER = Path(__file__).resolve().parents[1] / "ai-code-reviewer"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(REVIEWER) not in sys.path:
    sys.path.insert(0, str(REVIEWER))

GoogleProvider = None

def load_google_provider():
    global GoogleProvider

    if GoogleProvider is not None:
        return GoogleProvider

    reviewer = Path(__file__).resolve().parents[1] / "ai-code-reviewer"

    if not reviewer.exists():
        raise RuntimeError(
            "KHALED_REVIEWER_NOT_FOUND: " + str(reviewer)
        )

    if str(reviewer) not in sys.path:
        sys.path.insert(0, str(reviewer))

    from src.providers.google_provider import GoogleProvider as GP

    GoogleProvider = GP
    return GoogleProvider


MAX_LOG = 30000
MAX_RESPONSE = 30000


def run(cmd, input_text=None):
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def extract_patch(response):
    if not response:
        return ""

    text = str(response).strip()

    if text == "NO_SAFE_PATCH":
        return ""

    # Remove Markdown fences.
    text = re.sub(
        r"```(?:diff|patch)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = text.replace("```", "")

    # Prefer complete git diff.
    pos = text.find("diff --git ")
    if pos >= 0:
        return text[pos:].strip()

    # Standard unified diff.
    pos = text.find("--- ")
    if pos >= 0:
        candidate = text[pos:].strip()
        if "\n+++ " in candidate:
            return candidate

    return ""


def protected_patch(patch):
    if not patch:
        return False

    forbidden = [
        ".github/",
        ".khaled/",
        ".git/",
        "gradle/wrapper/",
        "gradlew",
        "gradlew.bat",
    ]

    for line in patch.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            for item in forbidden:
                if item in line:
                    return False

    return True


async def ask_gemini(build_log):
    key = os.environ.get("GOOGLE_API_KEY", "")

    if not key:
        raise RuntimeError("GOOGLE_API_KEY missing")

    model = os.environ.get(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    )

    provider_class = load_google_provider()

    provider = provider_class(
        api_key=key,
        model=model
    )

    prompt = """
You are KHALED SELF-MAINTENANCE ENGINE.

A REAL build failed.

Return ONLY a minimal unified git diff.

Rules:
- Fix only the demonstrated build failure.
- Change the smallest possible number of lines.
- Do not modify .github/
- Do not modify .khaled/
- Do not modify gradle/wrapper/
- Do not rewrite whole files.
- Do not invent test results.
- Do not explain anything.
- No Markdown fences.
- If no safe repair exists, return exactly:
NO_SAFE_PATCH

REAL BUILD LOG:
""" + build_log[-MAX_LOG:]

    result = await provider.complete(
        messages=[
            {
                "role": "system",
                "content": (
                    "Return only a valid minimal unified git diff."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=8000,
        json_mode=False
    )

    response = (result.content or "").strip()

    print("GEMINI_RESPONSE =", bool(response))
    print("GEMINI_RESPONSE_LENGTH =", len(response))

    return response[:MAX_RESPONSE]


def repair(build_log):
    print("KHALED_REPAIR_START=true")

    response = asyncio.run(
        ask_gemini(build_log)
    )

    patch = extract_patch(response)

    print(
        "PATCH_DETECTED=",
        bool(patch)
    )

    if not patch:
        print("REPAIR_RESULT=NO_PATCH")
        return 2

    if not protected_patch(patch):
        print("REPAIR_RESULT=PROTECTED_PATH_REJECTED")
        return 3

    print("PATCH_VALIDATION_START=true")

    check = run(
        ["git", "apply", "--check", "--whitespace=nowarn", "-"],
        patch
    )

    print(
        "PATCH_CHECK_EXIT=",
        check.returncode
    )

    if check.returncode != 0:
        print("PATCH_CHECK_FAILED=true")
        print(check.stdout[-10000:])
        return 4

    apply = run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        patch
    )

    print(
        "PATCH_APPLY_EXIT=",
        apply.returncode
    )

    if apply.returncode != 0:
        print("PATCH_APPLY_FAILED=true")
        print(apply.stdout[-10000:])
        return 5

    print("PATCH_APPLIED=true")
    print("REPAIR_RESULT=PATCH_APPLIED")
    return 0




def rollback_last_patch():
    print("KHALED_ROLLBACK_START=true")

    # Reverse only the currently applied working-tree patch.
    result = run(
        ["git", "diff", "--quiet"]
    )

    if result.returncode == 0:
        print("ROLLBACK_RESULT=NOTHING_TO_ROLLBACK")
        return 0

    reverse = run(
        ["git", "diff", "--binary"],
        ""
    )

    if reverse.returncode != 0 or not reverse.stdout.strip():
        print("ROLLBACK_RESULT=NO_WORKTREE_DIFF")
        return 1

    apply_reverse = run(
        ["git", "apply", "-R", "--whitespace=nowarn", "-"],
        reverse.stdout
    )

    print("ROLLBACK_EXIT=", apply_reverse.returncode)

    if apply_reverse.returncode != 0:
        print("ROLLBACK_RESULT=FAILED")
        print(apply_reverse.stdout[-10000:])
        return 2

    print("ROLLBACK_RESULT=SUCCESS")
    return 0


def main():
    if "--failure-kind" not in sys.argv:
        print("ERROR: --failure-kind required")
        return 10

    # Accept either --build-log or --evidence-file.
    log_file = None

    for flag in ("--build-log", "--evidence-file"):
        if flag in sys.argv:
            try:
                idx = sys.argv.index(flag) + 1
                log_file = sys.argv[idx]
                break
            except Exception:
                print("ERROR: evidence path missing")
                return 11

    if not log_file:
        print("ERROR: --build-log or --evidence-file required")
        return 11

    if not os.path.exists(log_file):
        print("ERROR: evidence file does not exist")
        return 12

    evidence = Path(log_file).read_text(
        encoding="utf-8",
        errors="replace"
    )

    failure_kind = sys.argv[
        sys.argv.index("--failure-kind") + 1
    ]

    print("FAILURE_KIND=", failure_kind)
    print("EVIDENCE_FILE=", log_file)
    print("EVIDENCE_BYTES=", len(evidence.encode()))

    if not evidence.strip():
        print("ERROR: evidence is empty")
        return 13

    return repair(evidence)


if __name__ == "__main__":
    if "--rollback" in sys.argv:
        raise SystemExit(rollback_last_patch())
    raise SystemExit(main())
