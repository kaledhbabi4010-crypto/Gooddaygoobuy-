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
import pathlib
import subprocess
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


# ============================================================
# _KHALED_GEMINI_RETRY_ENGINE
# REAL GEMINI RETRY FOR TEMPORARY API FAILURES
# ============================================================

def _khaled_gemini_retry(provider, *args, **kwargs):

    max_attempts = 5
    delays = [3, 8, 15, 30, 45]

    for attempt in range(1, max_attempts + 1):

        print("GEMINI_API_ATTEMPT=" + str(attempt))

        try:

            result = provider.complete(
                *args,
                **kwargs
            )

            if result is None:
                raise RuntimeError(
                    "Gemini returned no response"
                )

            print("GEMINI_API_CALL=SUCCESS")
            print(
                "GEMINI_RESPONSE_LENGTH="
                + str(len(str(result)))
            )

            return result

        except Exception as exc:

            error = str(exc)

            print(
                "GEMINI_API_ERROR="
                + error[:2000]
            )

            transient = (
                "503" in error
                or "UNAVAILABLE" in error
                or "429" in error
                or "RESOURCE_EXHAUSTED" in error
                or "500" in error
                or "502" in error
                or "504" in error
            )

            if not transient:
                raise

            if attempt >= max_attempts:
                print(
                    "GEMINI_RETRY_EXHAUSTED=TRUE"
                )
                raise

            wait_time = delays[attempt - 1]

            print(
                "GEMINI_RETRY_WAIT="
                + str(wait_time)
            )

            import time
            time.sleep(wait_time)


_KHALED_GEMINI_RETRY_ENGINE = True


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
    """Extract only a structurally valid unified git diff."""
    if not response:
        return ""

    text = str(response).strip()

    # Remove markdown fences without trusting surrounding prose.
    lines = text.splitlines()

    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    text = "\n".join(lines).strip()

    # Prefer a complete git diff.
    start = text.find("diff --git ")
    if start >= 0:
        patch = text[start:].strip()
    else:
        # Fallback to unified diff headers.
        start = text.find("--- ")
        if start < 0:
            return ""
        patch = text[start:].strip()

    lines = patch.splitlines()

    # Mandatory unified-diff headers.
    old_headers = [
        line for line in lines
        if line.startswith("--- ")
    ]

    new_headers = [
        line for line in lines
        if line.startswith("+++ ")
    ]

    if not old_headers or not new_headers:
        return ""

    # A normal text patch must contain at least one hunk.
    has_hunk = any(line.startswith("@@ ") for line in lines)

    # Binary patches are allowed only when explicitly represented.
    has_binary = any(
        line.startswith("Binary files ")
        for line in lines
    )

    if not has_hunk and not has_binary:
        return ""

    # Reject obvious natural-language contamination.
    bad_prefixes = (
        "Here is",
        "Here’s",
        "Sure",
        "The fix",
        "Explanation:",
        "I fixed",
        "I have fixed",
        "```",
    )

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(bad_prefixes):
            return ""

    # A normal text unified diff should have at least one
    # addition/deletion/context line after a hunk.
    if has_hunk:
        hunk_index = next(
            i for i, line in enumerate(lines)
            if line.startswith("@@ ")
        )

        hunk_lines = lines[hunk_index + 1:]

        meaningful = [
            line for line in hunk_lines
            if (
                line.startswith("+")
                or line.startswith("-")
                or line.startswith(" ")
                or line.startswith("\\")
            )
        ]

        if not meaningful:
            return ""

    return patch + "\n"

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


def _get_target_file_context(build_log):
    """
    Extract real repository files referenced by the build log.

    Handles:
    - android_app/...
    - khaled_android/...
    - absolute paths containing those repository paths
    - Gradle/Javac error formats
    """

    text = str(build_log)
    candidates = set()

    patterns = [
        r'(?:^|[\s"\'])(android_app/[^\s"\']+\.(?:java|kt|xml))',
        r'(?:^|[\s"\'])(khaled_android/[^\s"\']+\.(?:java|kt|xml))',
        r'/(android_app/[^\s"\']+\.(?:java|kt|xml))',
        r'/(khaled_android/[^\s"\']+\.(?:java|kt|xml))',
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            candidates.add(match)

    # Also inspect ordinary lines containing source-file extensions.
    for line in text.splitlines():
        for root in ("android_app/", "khaled_android/"):
            pos = line.find(root)
            if pos >= 0:
                tail = line[pos:].strip()

                # Remove common compiler separators.
                tail = re.split(r'[\s\'"]', tail, maxsplit=1)[0]

                # Keep only the actual repository-relative path.
                tail = re.split(r'(?=:\d+(?::\d+)?(?:\s|$))', tail)[0]

                if tail.endswith((".java", ".kt", ".xml")):
                    candidates.add(tail)

    output = []

    for rel in sorted(candidates):
        rel = rel.replace("\\", "/")

        # Security boundary: only repository source trees.
        if not (
            rel.startswith("android_app/")
            or rel.startswith("khaled_android/")
        ):
            continue

        path = Path(os.getcwd()) / rel

        if not path.is_file():
            output.append(
                "===== FILE NOT FOUND: "
                + rel
                + " ====="
            )
            continue

        try:
            data = path.read_text(
                encoding="utf-8",
                errors="replace"
            )

            output.append(
                "===== FILE: "
                + rel
                + " =====\n"
                + data[:50000]
                + "\n===== END FILE ====="
            )

        except Exception as exc:
            output.append(
                "FILE_READ_ERROR: "
                + rel
                + " "
                + str(exc)
            )

    if not output:
        return "NO_TARGET_FILE_FOUND_IN_BUILD_LOG"

    return "\n\n".join(output)




async def ask_gemini(build_log, failure_kind):
    import os
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("GEMINI_SECRET_MISSING=true")
        return ""

    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash").strip()
    print("GEMINI_MODEL_USED=", model)
    provider = load_google_provider()(api_key=key, model=model)

    target = _get_target_file_context(build_log)

    prompt = f"""
You are KHALED's REAL CODE REPAIR ENGINE.

A REAL build failed.

FAILURE KIND:
{failure_kind}

REAL BUILD EVIDENCE:
{build_log}

REAL CURRENT TARGET FILE:
{target}

TASK:
Repair the actual compiler error in the supplied current file.

CRITICAL:
- The supplied file content is authoritative.
- Do NOT use guessed line numbers.
- Do NOT return a unified diff.
- Return ONLY the COMPLETE corrected contents of the target source file.
- Preserve all existing valid code.
- Make the smallest necessary correction.
- Do not modify unrelated files.
- Do not add explanations.
- Do not use Markdown fences.
"""

    result = await _khaled_gemini_retry(provider, 
        [{"role": "user", "content": prompt}],
        max_tokens=12000
    )

    response = (
        getattr(result, "content", None)
        or getattr(result, "text", None)
        or ""
    )
    print("GEMINI_RESPONSE =", bool(response))
    print("GEMINI_RESPONSE_LENGTH =", len(response))
    return response



def repair(build_log, failure_kind):
    import os, re, subprocess

    print("KHALED_DIRECT_FILE_REPAIR=true")

    lines = str(build_log).splitlines()
    summary = [
        ln for ln in lines
        if ("error:" in ln or "e: " in ln[:3] or "FAILURE:" in ln
            or "What went wrong" in ln or "Execution failed" in ln
            or "Caused by:" in ln or "> " == ln[:2])
    ]
    print("----- REAL BUILD ERROR SUMMARY -----")
    for ln in summary[:120]:
        print(ln)
    print("----- END REAL BUILD ERROR SUMMARY -----")

    context = _get_target_file_context(build_log)

    m = re.search(r"===== FILE:\s*([^\s=]+)\s*=====", context)
    if not m:
        print("DIRECT_REPAIR_TARGET=NOT_FOUND")
        return 10

    target = m.group(1).strip()
    if not target.startswith(("android_app/","khaled_android/")):
        print("DIRECT_REPAIR_PROTECTED_TARGET=true")
        return 11

    if not os.path.isfile(target):
        print("DIRECT_REPAIR_FILE_MISSING=true")
        return 12

    original = open(target,encoding="utf-8").read()

    response = asyncio.run(ask_gemini(build_log,failure_kind))
    if not response:
        print("DIRECT_REPAIR_NO_GEMINI_RESPONSE=true")
        return 13

    # Remove accidental markdown fences only.
    corrected = response.strip()
    if corrected.startswith("```"):
        corrected = re.sub(r"^```[^\n]*\n","",corrected)
        corrected = re.sub(r"\n```$","",corrected).strip()

    if len(corrected) < 100:
        print("DIRECT_REPAIR_RESPONSE_TOO_SHORT=true")
        return 14

    # Safety: require substantial overlap with the real current file.
    old_lines=set(x.strip() for x in original.splitlines() if len(x.strip())>=12)
    new_lines=set(x.strip() for x in corrected.splitlines() if len(x.strip())>=12)
    overlap=len(old_lines & new_lines)

    print("DIRECT_REPAIR_TARGET=",target)
    print("DIRECT_REPAIR_OVERLAP_LINES=",overlap)

    if overlap < 3:
        print("DIRECT_REPAIR_OVERLAP_REJECTED=true")
        return 15

    with open(target,"w",encoding="utf-8",newline="\n") as f:
        f.write(corrected.rstrip()+"\n")

    print("DIRECT_FILE_REPLACED=true")

    # Immediate syntax/build validation.
    check=subprocess.run(
        ["bash","-lc","cd android_app && ./gradlew --no-daemon assembleDebug"],
        text=True,capture_output=True
    )

    print("DIRECT_REPAIR_BUILD_EXIT=",check.returncode)

    if check.returncode == 0:
        print("DIRECT_REPAIR_VERIFIED=true")
        print("REPAIR_RESULT=PATCH_APPLIED")
        return 0

    print("DIRECT_REPAIR_BUILD_FAILED=true")
    print((check.stdout+"\n"+check.stderr)[-12000:])
    print("REPAIR_RESULT=FAILED_FINAL_BUILD")
    return 16






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

    return repair(evidence, failure_kind)


if __name__ == "__main__":
    if "--rollback" in sys.argv:
        raise SystemExit(rollback_last_patch())
    raise SystemExit(main())
