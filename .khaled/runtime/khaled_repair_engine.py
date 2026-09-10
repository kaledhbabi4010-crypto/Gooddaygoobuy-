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
    import hashlib

    key = os.environ.get("GOOGLE_API_KEY", "").strip()

    if not key:
        print("GEMINI_RESPONSE = False")
        print("GEMINI_ERROR = GOOGLE_API_KEY_MISSING")
        return ""

    model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    try:
        provider_class = load_google_provider()
        provider = provider_class(
            api_key=key,
            model=model
        )

        system = """You are the KHALED autonomous repair engine.

Return ONLY a valid unified git diff.

Rules:
1. Repair only the actual build failure shown in the evidence.
2. Make the smallest safe change possible.
3. Never modify .github/, .khaled/, .git/, gradle/wrapper/, gradlew, or gradlew.bat.
4. Never invent test results.
5. Never return explanations.
6. The diff must contain valid --- / +++ headers and @@ hunks.
7. If no safe repair can be produced, return exactly NO_SAFE_PATCH.
"""

        user = (
            "FAILURE_KIND:\n"
            + str(failure_kind)
            + "\n\n"
            "REAL_BUILD_EVIDENCE:\n"
            + str(build_log)
            + "\n\n"
            "REAL_REPOSITORY_STATUS:\n"
            + subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            ).stdout[-12000:]
            + "\n\n"
            "REAL_TARGET_FILE:\n"
            + _get_target_file_context(build_log)
            + "\n\n"
            "IMPORTANT: Analyze the actual repository state and the actual build error. "
            "Return a unified git diff that applies to the CURRENT files. "
            "Repair the real error; do not invent file contents."
        )

        result = await provider.complete(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0,
            max_tokens=8000,
            json_mode=False
        )

        content = getattr(result, "content", None)

        if content is None:
            content = str(result)

        content = str(content).strip()

        print("GEMINI_RESPONSE =", bool(content))
        print("GEMINI_RESPONSE_LENGTH =", len(content))
        print(
            "GEMINI_RESPONSE_SHA256 =",
            hashlib.sha256(
                content.encode("utf-8", errors="replace")
            ).hexdigest()
        )

        return content

    except Exception as exc:
        print("GEMINI_RESPONSE = False")
        print("GEMINI_ERROR_TYPE =", type(exc).__name__)
        print("GEMINI_ERROR =", str(exc)[:500])
        return ""

def repair(build_log, failure_kind):
    print("KHALED_REPAIR_START=true")

    # --------------------------------------------------------
    # ATTEMPT 1
    # --------------------------------------------------------
    print("GEMINI_REPAIR_ATTEMPT=1")

    response = asyncio.run(
        ask_gemini(build_log, failure_kind)
    )

    patch = extract_patch(response)

    print("PATCH_DETECTED=", bool(patch))

    if not patch:
        print("REPAIR_RESULT=NO_PATCH_ATTEMPT_1")
    else:
        if not protected_patch(patch):
            print("REPAIR_RESULT=PROTECTED_PATH_REJECTED")
            return 3

        print("PATCH_VALIDATION_START=true")
        print("PATCH_VALIDATION_ATTEMPT=1")

        check = run(
            [
                "git",
                "apply",
                "--check",
                "--whitespace=nowarn",
                "-"
            ],
            patch
        )

        print(
            "PATCH_CHECK_EXIT_ATTEMPT_1=",
            check.returncode
        )

        if check.returncode == 0:
            apply = run(
                [
                    "git",
                    "apply",
                    "--whitespace=nowarn",
                    "-"
                ],
                patch
            )

            print(
                "PATCH_APPLY_EXIT_ATTEMPT_1=",
                apply.returncode
            )

            if apply.returncode == 0:
                print("PATCH_APPLIED=true")
                print("REPAIR_RESULT=PATCH_APPLIED")
                return 0

            print("PATCH_APPLY_FAILED_ATTEMPT_1=true")

        else:
            print("PATCH_CHECK_FAILED_ATTEMPT_1=true")
            print(check.stdout[-10000:])

    # --------------------------------------------------------
    # ATTEMPT 2
    # Send Gemini the REAL current file context again,
    # plus the rejected patch and git error.
    # No patch has been applied if validation failed.
    # --------------------------------------------------------
    print("=" * 60)
    print("GEMINI_REPAIR_RETRY=true")
    print("=" * 60)

    retry_evidence = (
        str(build_log)
        + "\n\n"
        "KHALED_FIRST_ATTEMPT_RESULT:\n"
        + str(response)
        + "\n\n"
        "IMPORTANT_PATCH_RETRY:\n"
        "The previous Gemini patch was NOT applied.\n"
        "It failed KHALED git apply validation.\n"
        "Generate a NEW unified diff against the CURRENT "
        "REAL FILE CONTENT.\n"
        "Do not reuse line numbers blindly.\n"
        "The file content supplied by KHALED is authoritative.\n"
    )

    response2 = asyncio.run(
        ask_gemini(retry_evidence, failure_kind)
    )

    patch2 = extract_patch(response2)

    print("GEMINI_RETRY_RESPONSE =", bool(response2))
    print("PATCH_DETECTED_ATTEMPT_2 =", bool(patch2))

    if not patch2:
        print("REPAIR_RESULT=NO_PATCH_ATTEMPT_2")
        return 6

    if not protected_patch(patch2):
        print("REPAIR_RESULT=PROTECTED_PATH_REJECTED_ATTEMPT_2")
        return 7

    print("PATCH_VALIDATION_ATTEMPT=2")

    check2 = run(
        [
            "git",
            "apply",
            "--check",
            "--whitespace=nowarn",
            "-"
        ],
        patch2
    )

    print(
        "PATCH_CHECK_EXIT_ATTEMPT_2=",
        check2.returncode
    )

    if check2.returncode != 0:
        print("PATCH_CHECK_FAILED_ATTEMPT_2=true")
        print(check2.stdout[-12000:])
        print("REPAIR_RESULT=FAILED_AFTER_RETRY")
        return 8

    apply2 = run(
        [
            "git",
            "apply",
            "--whitespace=nowarn",
            "-"
        ],
        patch2
    )

    print(
        "PATCH_APPLY_EXIT_ATTEMPT_2=",
        apply2.returncode
    )

    if apply2.returncode != 0:
        print("PATCH_APPLY_FAILED_ATTEMPT_2=true")
        print(apply2.stdout[-12000:])
        return 9

    print("PATCH_APPLIED=true")
    print("REPAIR_RESULT=PATCH_APPLIED_ON_RETRY")
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

    return repair(evidence, failure_kind)


if __name__ == "__main__":
    if "--rollback" in sys.argv:
        raise SystemExit(rollback_last_patch())
    raise SystemExit(main())
