import asyncio
import json
import os
import re
import subprocess
from pathlib import Path

from src.providers.google_provider import GoogleProvider

ROOT = Path(".").resolve()
MAX_ROUNDS = 5

PROTECTED = (
    ".github/",
    ".khaled/",
    ".git/",
    "gradle/wrapper/",
)


def run(cmd):
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.returncode, p.stdout


def get_build_command():
    code, output = run(
        ["./gradlew", "tasks", "--all", "--no-daemon"]
    )

    if code == 0 and re.search(
        r"(^|\s)assembleDebug(\s|$)", output
    ):
        return ["./gradlew", "assembleDebug", "--no-daemon"]

    return ["./gradlew", "assemble", "--no-daemon"]


def protected_patch(patch):
    for line in patch.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            path = line[4:].strip()

            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]

            for protected in PROTECTED:
                if path.startswith(protected):
                    return True, path

    return False, ""


def extract_patch(response):
    if not response:
        return ""

    response = response.strip()

    try:
        data = json.loads(response)

        patch = data.get("patch", "")

        if isinstance(patch, str):
            return patch.strip()

    except Exception:
        pass

    match = re.search(
        r"```(?:diff|patch)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    if "diff --git " in response:
        return response[
            response.index("diff --git "):
        ].strip()

    return ""


def collect_source():
    result = []

    extensions = {
        ".kt",
        ".java",
        ".gradle",
        ".xml",
        ".properties",
        ".json",
        ".toml",
    }

    excluded = (
        ".git/",
        ".github/",
        ".khaled/",
        "build/",
        ".gradle/",
    )

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(ROOT).as_posix()

        if any(rel.startswith(x) for x in excluded):
            continue

        if path.suffix.lower() not in extensions:
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        if len(text) > 10000:
            text = text[:10000]

        result.append(
            f"\n===== {rel} =====\n{text}"
        )

        if len(result) >= 50:
            break

    return "".join(result)


async def ask_gemini(build_log):
    key = os.environ.get("GOOGLE_API_KEY", "")

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not available."
        )

    model = os.environ.get(
        "GEMINI_MODEL",
        "gemini-3.6-flash",
    )

    provider = GoogleProvider(
        api_key=key,
        model=model,
    )

    source = collect_source()

    prompt = f"""
You are a conservative autonomous repair engine.

A REAL Gradle build has failed.

Use ONLY the supplied build evidence and source context.

Requirements:

1. Diagnose the actual failure.
2. Produce the smallest safe source change.
3. Return a unified git diff.
4. Never modify .github files.
5. Never modify .khaled files.
6. Never modify gradle/wrapper files.
7. Never invent build or test results.
8. If a safe fix cannot be determined, return an empty patch.

Return JSON only:

{{
  "diagnosis": "short explanation",
  "patch": "unified git diff"
}}

REAL BUILD LOG:
{build_log[-30000:]}

SOURCE:
{source}
"""

    result = await provider.complete(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a conservative software "
                    "repair engine."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        max_tokens=12000,
        reasoning_effort="minimal",
        json_mode=True,
    )

    return result.content or ""


def main():
    for round_no in range(1, MAX_ROUNDS + 1):

        print("")
        print("=" * 70)
        print(
            f"KHALED REPAIR ROUND "
            f"{round_no}/{MAX_ROUNDS}"
        )
        print("=" * 70)

        command = get_build_command()

        print(
            "BUILD COMMAND =",
            " ".join(command),
        )

        code, log = run(command)

        Path("/tmp/khaled-build.log").write_text(
            log,
            encoding="utf-8",
        )

        print("BUILD_EXIT_CODE =", code)

        if code == 0:
            print("REAL_BUILD_SUCCESS=TRUE")
            return True

        print("REAL_BUILD_SUCCESS=FALSE")
        print("CALLING_REAL_GEMINI=TRUE")

        response = asyncio.run(
            ask_gemini(log)
        )

        print(
            "GEMINI_RESPONSE_RECEIVED=TRUE"
        )

        try:
            data = json.loads(response)
            print(
                "DIAGNOSIS =",
                str(data.get("diagnosis", ""))[:1500],
            )
        except Exception:
            print(
                "GEMINI_JSON_PARSE_WARNING=TRUE"
            )

        patch = extract_patch(response)

        if not patch:
            print("PATCH_PRESENT=FALSE")
            print(
                "AUTONOMOUS_REPAIR_STOPPED=TRUE"
            )
            return False

        print("PATCH_PRESENT=TRUE")

        blocked, path = protected_patch(patch)

        if blocked:
            print(
                "PROTECTED_PATH_PATCH=REJECTED"
            )
            print("REJECTED_PATH =", path)
            return False

        check = subprocess.run(
            [
                "git",
                "apply",
                "--check",
                "--whitespace=nowarn",
                "-",
            ],
            input=patch,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        if check.returncode != 0:
            print("PATCH_CHECK=FAILED")
            print(check.stdout[-5000:])
            return False

        print("PATCH_CHECK=PASSED")

        apply = subprocess.run(
            [
                "git",
                "apply",
                "--whitespace=nowarn",
                "-",
            ],
            input=patch,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        if apply.returncode != 0:
            print("PATCH_APPLY=FAILED")
            print(apply.stdout[-5000:])
            return False

        print("PATCH_APPLY=PASSED")

    print("MAX_REPAIR_ROUNDS_REACHED=TRUE")
    return False


if __name__ == "__main__":
    success = main()

    if not success:
        print(
            "AI_SUCCESS_CLAIM=FORBIDDEN"
        )
        raise SystemExit(1)

    print(
        "AI_SUCCESS_CLAIM=FORBIDDEN"
    )
