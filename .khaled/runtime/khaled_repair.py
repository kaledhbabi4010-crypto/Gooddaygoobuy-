
#!/usr/bin/env python3

import argparse
import asyncio
import inspect
import json
import os
import pathlib
import re
import subprocess
import traceback

ROOT = pathlib.Path(".").resolve()

PROTECTED = (
    ".git/",
    ".github/",
    ".khaled/",
)

EXTENSIONS = {
    ".kt",
    ".java",
    ".xml",
    ".gradle",
    ".kts",
    ".properties",
    ".json",
}

def get_text(path, limit):
    try:
        return pathlib.Path(path).read_text(
            encoding="utf-8",
            errors="replace"
        )[-limit:]
    except Exception:
        return ""

def extract_paths(text):

    result = []

    patterns = [
        r'(app/src/[A-Za-z0-9_./-]+\.(?:kt|java|xml))',
        r'([A-Za-z0-9_.-]+/src/[A-Za-z0-9_./-]+\.(?:kt|java|xml))',
        r'([A-Za-z0-9_./-]+\.gradle(?:\.kts)?)',
    ]

    for pattern in patterns:

        for item in re.findall(pattern, text):

            item = item.replace("\\", "/")

            if item not in result:
                result.append(item)

    return result[:50]

def collect_source_context(build_log, test_log):

    build = get_text(build_log, 50000)
    tests = get_text(test_log, 40000)

    paths = extract_paths(
        build + "\n" + tests
    )

    files = []

    for rel in paths:

        p = ROOT / rel

        if not p.exists() or not p.is_file():
            continue

        try:

            content = p.read_text(
                encoding="utf-8",
                errors="replace"
            )

            files.append(
                "\n===== REAL FILE =====\n"
                f"PATH: {rel}\n"
                f"{content[:45000]}"
            )

        except Exception:
            pass

    if not files:

        candidates = []

        for p in ROOT.rglob("*"):

            if not p.is_file():
                continue

            rel = str(
                p.relative_to(ROOT)
            ).replace("\\", "/")

            if any(
                rel.startswith(x)
                for x in PROTECTED
            ):
                continue

            if p.suffix.lower() not in EXTENSIONS:
                continue

            candidates.append(p)

        for p in candidates[:25]:

            try:

                content = p.read_text(
                    encoding="utf-8",
                    errors="replace"
                )

                files.append(
                    "\n===== SOURCE FILE =====\n"
                    f"PATH: {p.relative_to(ROOT)}\n"
                    f"{content[:15000]}"
                )

            except Exception:
                pass

    return (
        "\n===== BUILD EVIDENCE =====\n"
        + build
        + "\n\n===== TEST EVIDENCE =====\n"
        + tests
        + "\n\n===== SOURCE =====\n"
        + "\n".join(files)
    )

def normalize(result):

    if inspect.isawaitable(result):
        result = asyncio.run(result)

    if isinstance(result, dict):
        return result

    if hasattr(result, "content"):
        result = result.content

    if hasattr(result, "text"):
        result = result.text

    text = str(result)

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.I
    )

    text = text.replace("```", "").strip()

    match = re.search(
        r"\{.*\}",
        text,
        re.S
    )

    if not match:
        raise RuntimeError(
            "AI returned no JSON."
        )

    return json.loads(
        match.group(0)
    )

def create_provider():

    from src.providers.factory import get_provider

    key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY not injected by GitHub Actions."
        )

    model = os.environ.get(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    )

    sig = inspect.signature(
        get_provider
    )

    params = sig.parameters

    kwargs = {}

    if "provider" in params:
        kwargs["provider"] = "google"

    if "model" in params:
        kwargs["model"] = model

    if "api_key" in params:
        kwargs["api_key"] = key

    if "api_base_url" in params:
        kwargs["api_base_url"] = ""

    try:

        return get_provider(
            **kwargs
        )

    except Exception as first_error:

        attempts = [
            ("google", model, key),
            ("google", model),
            ("google",),
        ]

        for args in attempts:

            try:
                return get_provider(
                    *args
                )
            except Exception:
                pass

        raise RuntimeError(
            "REAL provider initialization failed: "
            + repr(first_error)
        )

def ask(provider, prompt):

    for method_name in [
        "generate",
        "complete",
        "chat",
        "invoke",
    ]:

        if not hasattr(
            provider,
            method_name
        ):
            continue

        method = getattr(
            provider,
            method_name
        )

        try:

            result = method(
                prompt
            )

        except TypeError:

            try:

                result = method(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ]
                )

            except TypeError:
                continue

        return normalize(
            result
        )

    raise RuntimeError(
        "No supported generation method found."
    )

async def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo",
        required=True
    )

    parser.add_argument(
        "--round",
        required=True
    )

    parser.add_argument(
        "--build-log",
        required=True
    )

    parser.add_argument(
        "--test-log",
        required=True
    )

    args = parser.parse_args()

    context = collect_source_context(
        args.build_log,
        args.test_log
    )

    prompt = f"""
You are KHALED's autonomous Android repair engine.

Repository:
{args.repo}

Round:
{args.round}

Use ONLY the real evidence supplied below.

TASK:
Find the actual build/test failure and make the smallest
safe source-code correction.

RULES:

- Never invent evidence.
- Never claim success.
- Never modify .github/.
- Never modify .khaled/.
- Never modify .git/.
- Never disable tests.
- Never weaken assertions merely to pass.
- Never delete functionality just to hide a failure.
- Do not change unrelated files.
- Prefer minimal corrections.
- Return complete replacement file contents.

JSON ONLY:

{{
  "diagnosis": "actual evidence-based diagnosis",
  "files": [
    {{
      "path": "relative/path",
      "content": "complete file content"
    }}
  ]
}}

If there is no safe evidence-based repair:

{{
  "diagnosis": "NO_SAFE_REPAIR",
  "files": []
}}

REAL EVIDENCE:
{context}
"""

    provider = create_provider()

    result = ask(
        provider,
        prompt
    )

    files = result.get(
        "files",
        []
    )

    if not isinstance(
        files,
        list
    ):
        raise RuntimeError(
            "Invalid AI files response."
        )

    changed = []

    for item in files:

        if not isinstance(
            item,
            dict
        ):
            continue

        rel = item.get("path")
        content = item.get("content")

        if not rel:
            continue

        if not isinstance(
            content,
            str
        ):
            continue

        rel = str(rel).replace(
            "\\",
            "/"
        )

        if rel.startswith("/"):
            raise RuntimeError(
                "Absolute path rejected."
            )

        if any(
            rel == x.rstrip("/")
            or rel.startswith(x)
            for x in PROTECTED
        ):
            raise RuntimeError(
                "Protected path rejected: "
                + rel
            )

        target = (
            ROOT / rel
        ).resolve()

        if not str(target).startswith(
            str(ROOT) + os.sep
        ):
            raise RuntimeError(
                "Path escape rejected."
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        old = None

        if target.exists():

            old = target.read_text(
                encoding="utf-8",
                errors="replace"
            )

        if old != content:

            target.write_text(
                content,
                encoding="utf-8"
            )

            changed.append(
                rel
            )

    print(
        json.dumps(
            {
                "real_ai_response": True,
                "diagnosis": result.get(
                    "diagnosis"
                ),
                "changed_files": changed,
            },
            indent=2
        )
    )

    if not changed:
        return 12

    return 0

if __name__ == "__main__":

    try:
        raise SystemExit(
            asyncio.run(
                main()
            )
        )

    except Exception as exc:

        print(
            "REPAIR_ENGINE_ERROR:",
            repr(exc)
        )

        traceback.print_exc()

        raise
