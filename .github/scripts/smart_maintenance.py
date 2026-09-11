from __future__ import annotations

import os
import sys
import json
import subprocess
import hashlib
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone

from groq import Groq


# ============================================================
# CONFIG
# ============================================================

ROOT = Path.cwd().resolve()

STATE_DIR = ROOT / ".groq-repair"
BACKUP_DIR = STATE_DIR / "backup"

STATE_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

API_KEY = os.environ.get("GROQ_API_KEY")

if not API_KEY:
    raise SystemExit(
        "ERROR: GROQ_API_KEY environment variable is missing."
    )

REQUESTED_MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

MAX_ROUNDS = int(
    os.environ.get("GROQ_MAX_ROUNDS", "6")
)

COMMAND_TIMEOUT = int(
    os.environ.get("GROQ_COMMAND_TIMEOUT", "180")
)

MAX_FILE_SIZE = 400_000


IGNORED_DIRS = {
    ".git",
    ".groq-repair",
    "node_modules",
    "bin",
    "obj",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".next",
    "dist",
    "build",
    "target",
    ".idea",
    ".vs",
}


client = Groq(api_key=API_KEY)


# ============================================================
# LOGGING
# ============================================================

def log(message: str) -> None:

    line = (
        f"[{datetime.now(timezone.utc).isoformat()}] "
        f"{message}"
    )

    print(line, flush=True)

    with (STATE_DIR / "repair.log").open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(line + "\n")


# ============================================================
# PATH SAFETY
# ============================================================

def relative_path(path: Path) -> str:

    return str(
        path.relative_to(ROOT)
    ).replace("\\", "/")


def safe_path(relative: str) -> Path:

    path = (ROOT / relative).resolve()

    if path != ROOT and ROOT not in path.parents:
        raise ValueError(
            "Path escapes repository root."
        )

    return path


def is_ignored(path: Path) -> bool:

    return any(
        part in IGNORED_DIRS
        for part in path.parts
    )


# ============================================================
# PROJECT STRUCTURE
# ============================================================

def project_structure() -> str:

    files = []

    for path in sorted(ROOT.rglob("*")):

        if is_ignored(path):
            continue

        if not path.is_file():
            continue

        files.append(
            relative_path(path)
        )

        if len(files) >= 6000:

            files.append(
                "... STRUCTURE TRUNCATED ..."
            )

            break

    return "\n".join(files)


# ============================================================
# FILE READING
# ============================================================

def read_file(path_string: str) -> str:

    path = safe_path(path_string)

    if not path.is_file():

        return (
            f"ERROR: not a file: "
            f"{path_string}"
        )

    if path.stat().st_size > MAX_FILE_SIZE:

        return (
            f"ERROR: file exceeds "
            f"{MAX_FILE_SIZE} bytes: "
            f"{path_string}"
        )

    return path.read_text(
        encoding="utf-8",
        errors="replace"
    )


# ============================================================
# CODE SEARCH
# ============================================================

def search_codebase(pattern: str) -> str:

    matches = []

    query = pattern.lower()

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if is_ignored(path):
            continue

        try:

            if path.stat().st_size > MAX_FILE_SIZE:
                continue

            text = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if query in text.lower():

                matches.append(
                    relative_path(path)
                )

                if len(matches) >= 300:
                    break

        except Exception:
            continue

    if not matches:

        return "NO_MATCHES"

    return "\n".join(matches)


# ============================================================
# COMMAND EXECUTION
# ============================================================

def run_command(command: str) -> str:

    lowered = command.lower()

    blocked_commands = (
        "rm -rf /",
        "rm -rf *",
        "mkfs",
        "diskpart",
        "format c:",
        "shutdown",
        "reboot",
        "git push --force",
        "git reset --hard",
        "git clean -fd",
        "del /s /q c:\\",
    )

    for blocked in blocked_commands:

        if blocked in lowered:

            return (
                "BLOCKED: destructive command "
                "is not permitted."
            )

    try:

        process = subprocess.run(
            command,
            cwd=ROOT,
            shell=True,
            text=True,
            capture_output=True,
            timeout=COMMAND_TIMEOUT,
        )

        output = (
            process.stdout or ""
        ) + (
            process.stderr or ""
        )

        if len(output) > 50_000:

            output = output[-50_000:]

        return (
            f"EXIT_CODE={process.returncode}\n"
            f"{output}"
        )

    except subprocess.TimeoutExpired:

        return (
            f"TIMEOUT after "
            f"{COMMAND_TIMEOUT} seconds"
        )

    except Exception as exc:

        return (
            f"COMMAND_ERROR: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# BACKUP
# ============================================================

def backup_file(path_string: str) -> None:

    source = safe_path(path_string)

    if not source.is_file():
        return

    destination = (
        BACKUP_DIR / path_string
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        source,
        destination
    )


# ============================================================
# FILE WRITING
# ============================================================

def write_file(
    path_string: str,
    content: str
) -> str:

    path = safe_path(path_string)

    if path.exists():

        backup_file(path_string)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary = path.with_name(
        path.name + ".groq-tmp"
    )

    temporary.write_text(
        content,
        encoding="utf-8"
    )

    temporary.replace(path)

    return (
        f"WRITE_OK: {path_string}"
    )


# ============================================================
# GIT DIFF
# ============================================================

def git_diff() -> str:

    try:

        process = subprocess.run(
            [
                "git",
                "diff",
                "--",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )

        output = (
            process.stdout or ""
        ) + (
            process.stderr or ""
        )

        if len(output) > 80_000:

            output = output[-80_000:]

        return output

    except Exception as exc:

        return (
            f"GIT_DIFF_ERROR: {exc}"
        )


# ============================================================
# SNAPSHOT
# ============================================================

def snapshot() -> dict[str, str]:

    result = {}

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if is_ignored(path):
            continue

        try:

            digest = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

            result[
                relative_path(path)
            ] = digest

        except Exception:
            continue

    return result


# ============================================================
# SAFETY BRANCH
# ============================================================

def create_safety_branch() -> None:

    try:

        check = subprocess.run(
            [
                "git",
                "rev-parse",
                "--is-inside-work-tree",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )

        if check.returncode != 0:

            log(
                "Not a Git repository. "
                "Continuing without safety branch."
            )

            return

        branch_name = (
            "groq-root-repair-"
            + datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )
        )

        process = subprocess.run(
            [
                "git",
                "checkout",
                "-b",
                branch_name,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )

        if process.returncode == 0:

            log(
                f"SAFETY BRANCH CREATED: "
                f"{branch_name}"
            )

        else:

            log(
                "WARNING: safety branch "
                "could not be created."
            )

    except Exception as exc:

        log(
            f"Git safety branch error: {exc}"
        )


# ============================================================
# GROQ TOOLS
# ============================================================

TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "list_structure",
            "description": (
                "List repository files."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a text file inside "
                "the repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": (
                "Search repository files "
                "for a text pattern."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string"
                    }
                },
                "required": ["pattern"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a diagnostic, build, "
                "or test command."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string"
                    }
                },
                "required": ["command"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create or replace a repository "
                "text file. Existing files are "
                "backed up first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    },
                },
                "required": [
                    "path",
                    "content"
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": (
                "Show current Git changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# ============================================================
# SYSTEM CONTRACT
# ============================================================

SYSTEM_PROMPT = r"""
You are GROQ ROOT REPAIR ENGINE.

STRICT MODE: MINIMAL ISSUE REPAIR ONLY.

Your job is NOT to rebuild, redesign, refactor, or generally improve the repository.

You must work ONLY on the specific real problem provided by the user or execution evidence.

RULES:

1. Identify the exact reported error or failure first.
2. Use repository evidence to determine the root cause.
3. Do not invent errors.
4. Do not modify files until a real problem is supported by evidence.
5. Modify only the file or files directly responsible for the reported problem.
6. Make the smallest possible change that fixes the identified root cause.
7. Do not refactor unrelated code.
8. Do not redesign architecture.
9. Do not clean up unrelated code.
10. Do not upgrade dependencies unless the reported problem directly requires it.
11. Do not make broad dependency changes.
12. Do not modify configuration unrelated to the reported problem.
13. Do not perform a general repository cleanup.
14. Do not rebuild the entire project as part of the repair.
15. Do not run a full test suite as part of the repair.
16. Do not use build/test activity as a reason to modify unrelated files.
17. Verification must be narrow and directly related to the repaired problem whenever possible.
18. Create a backup before modifying a file.
19. Inspect the final diff after editing.
20. If the evidence does not prove that the repair is correct, report UNABLE_TO_VERIFY.
21. Never claim VERIFIED_FIXED without actual evidence.
22. If no real repair is justified, make no modification.
23. Never modify more files than necessary.

REPAIR PIPELINE:

REAL PROBLEM
-> EVIDENCE
-> ROOT CAUSE
-> SMALLEST POSSIBLE CHANGE
-> DIFF INSPECTION
-> TARGETED VERIFICATION
-> VERIFIED_FIXED or UNABLE_TO_VERIFY

IMPORTANT:

The existence of a build failure does NOT authorize broad changes.

The existence of warnings does NOT authorize cleanup.

The existence of old or imperfect code does NOT authorize refactoring.

Only the specific reported problem may be repaired.

The objective is a surgical repair, not a repository rebuild.
"""


# ============================================================
# MODEL DISCOVERY
# ============================================================

def select_model() -> str:

    try:

        available = client.models.list()

        model_ids = {
            model.id
            for model in available.data
        }

        if REQUESTED_MODEL in model_ids:

            return REQUESTED_MODEL

        fallbacks = (
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "qwen-2.5-coder-32b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
        )

        for candidate in fallbacks:

            if candidate in model_ids:

                log(
                    "Requested model unavailable. "
                    f"Using fallback: {candidate}"
                )

                return candidate

        raise RuntimeError(
            "No supported configured Groq model "
            "was found."
        )

    except Exception as exc:

        raise RuntimeError(
            "Could not verify Groq model availability: "
            f"{exc}"
        )


# ============================================================
# GROQ REQUEST
# ============================================================


# GROQ_CONTEXT_COMPACTED:
# Keep the model request below the free/on-demand TPM ceiling.
# Large historical tool outputs are not replayed indefinitely.
def _compact_messages_for_groq(messages, max_chars=24000):
    if not messages:
        return messages

    out = []
    total = 0

    # Always preserve system + current user/task context.
    for i, msg in enumerate(messages):
        m = dict(msg)
        content = m.get("content")

        if isinstance(content, str):
            # Keep individual tool/output messages bounded.
            if len(content) > 6000:
                content = content[:6000] + "\n[OUTPUT_COMPACTED]"
                m["content"] = content

        encoded = len(str(m))

        # Preserve first two messages and newest messages.
        if i < 2 or i >= len(messages) - 3:
            out.append(m)
            total += encoded
        elif total < max_chars:
            out.append(m)
            total += encoded

    return out

def compact_groq_messages(
    messages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Keep Groq request context bounded.
    Preserve system message and newest conversation/tool context.
    """
    MAX_MESSAGE_CHARS = 2200
    MAX_MESSAGES = 8

    if not messages:
        return messages

    def compact_message(message):
        if not isinstance(message, dict):
            return message

        out = dict(message)

        content = out.get("content")

        if isinstance(content, str) and len(content) > MAX_MESSAGE_CHARS:
            out["content"] = (
                content[:MAX_MESSAGE_CHARS]
                + "\n[CONTEXT_TRUNCATED_BY_GROQ_REPAIR_ENGINE]"
            )

        return out

    # Always preserve system message.
    system = []
    rest = messages

    if isinstance(messages[0], dict) and messages[0].get("role") == "system":
        system = [compact_message(messages[0])]
        rest = messages[1:]

    # Keep newest messages because they contain the current tool result/error.
    recent = rest[-MAX_MESSAGES:]

    return system + [
        compact_message(message)
        for message in recent
    ]


def ask_groq(
    model: str,
    messages: list[dict[str, Any]]
):

    max_tokens = int(
        os.environ.get(
            "GROQ_MAX_COMPLETION_TOKENS",
            "3000"
        )
    )

    for attempt in range(1, 4):
        try:
            compact_messages = compact_groq_messages(messages)

            return client.chat.completions.create(
                model=model,
                messages=compact_messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
                max_completion_tokens=max_tokens,
            )

        except Exception as exc:
            error_text = str(exc)

            if "429" not in error_text:
                raise

            wait_seconds = 10 * attempt

            log(
                f"GROQ_RATE_LIMIT_RETRY "
                f"{attempt}/3: waiting "
                f"{wait_seconds}s"
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        "Groq rate limit persisted after 3 retries."
    )


# ============================================================
# TOOL ROUTER
# ============================================================

def execute_tool(
    name: str,
    arguments: dict[str, Any]
) -> str:

    try:

        if name == "list_structure":

            return project_structure()

        if name == "read_file":

            return read_file(
                arguments["path"]
            )

        if name == "search_codebase":

            return search_codebase(
                arguments["pattern"]
            )

        if name == "run_command":

            command = arguments["command"]

            result = run_command(command)

            log(
                "COMMAND:\n"
                + command
                + "\n"
                + result
            )

            return result

        if name == "write_file":
            result = write_file(
                arguments["path"],
                arguments["content"]
            )

            log(result)

            return result

        if name == "git_diff":

            return git_diff()

        return (
            f"UNKNOWN_TOOL: {name}"
        )

    except Exception as exc:

        return (
            f"TOOL_ERROR: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# MAIN REPAIR ENGINE
# ============================================================

def main() -> None:

    print()
    print("=" * 72)
    print(" GROQ ROOT REPAIR ENGINE")
    print("=" * 72)
    print()

    model = select_model()

    log(
        f"Using Groq model: {model}"
    )

    create_safety_branch()

    issue = " ".join(
        sys.argv[1:]
    ).strip()

    if not issue:

        issue = (
            "Perform a comprehensive repository repair and health verification. "
            "Inspect all subprojects (Android gradle projects android_app and khaled_android, "
            "C# .NET solution KHALED.sln, Python engines and scripts). "
            "Find any build, compilation, test, or configuration failures across all repository files. "
            "Identify why any previous repairs failed, diagnose root causes using actual command evidence, "
            "and apply minimal targeted repairs to resolve all failures."
        )

    evidence = {

        "started": datetime.now(
            timezone.utc
        ).isoformat(),

        "model": model,

        "repository": str(ROOT),

        "reported_problem": issue,

        "initial_snapshot": snapshot(),

        "rounds": [],

        "final_status": (
            "UNABLE_TO_VERIFY"
        ),
    }

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },

        {
            "role": "user",
            "content": (
                f"Repository:\n{ROOT}\n\n"
                f"Reported problem:\n{issue}\n\n"
                "Repository structure:\n"
                f"{project_structure()}\n\n"
                "Begin with evidence. "
                "Do not guess."
            ),
        },
    ]

    successful_command_observed = False
    write_observed = False
    verification_after_write_observed = False

    explicit_verified = False

    write_observed = False

    for round_number in range(
        1,
        MAX_ROUNDS + 1
    ):

        log(
            f"========== ROUND "
            f"{round_number}/{MAX_ROUNDS} =========="
        )

        round_record = {

            "round": round_number,

            "tools": [],
        }

        try:

            response = ask_groq(
                model,
                messages
            )

            message = (
                response.choices[0].message
            )

            messages.append(message)

            if message.tool_calls:

                for tool_call in (
                    message.tool_calls
                ):

                    name = (
                        tool_call.function.name
                    )

                    try:

                        arguments = json.loads(
                            tool_call.function.arguments
                            or "{}"
                        )

                    except json.JSONDecodeError:

                        arguments = {}

                    log(
                        "TOOL CALL: "
                        f"{name}"
                    )

                    result = execute_tool(
                        name,
                        arguments
                    )

                    if name == "write_file" and "WRITE_OK" in result:
                        write_observed = True

                    if (
                        name == "run_command"
                        and write_observed
                        and "EXIT_CODE=0"
                        in result
                    ):
                        successful_command_observed = True
                        verification_after_write_observed = True

                    round_record[
                        "tools"
                    ].append({

                        "name": name,

                        "arguments": arguments,

                        "result": result[
                            -20_000:
                        ],
                    })

                    messages.append({

                        "role": "tool",

                        "tool_call_id":
                            tool_call.id,

                        "name": name,

                        "content": result,
                    })

                evidence[
                    "rounds"
                ].append(
                    round_record
                )

                messages.append({

                    "role": "user",

                    "content": (
                        "Continue using actual "
                        "tool evidence. "
                        "If code was changed, "
                        "run the relevant "
                        "verification now. "
                        "Do not infer success."
                    ),
                })

                continue

            text = (
                message.content or ""
            )

            round_record[
                "assistant"
            ] = text

            evidence[
                "rounds"
            ].append(
                round_record
            )

            print()
            print(text)

            lowered = text.lower()

            if (
                "final_status:"
                in lowered
                and
                "verified_fixed"
                in lowered
            ):

                explicit_verified = True

            if not successful_command_observed:

                messages.append({

                    "role": "user",

                    "content": (
                        "Your response did not "
                        "provide sufficient "
                        "executable evidence. "
                        "Continue using tools "
                        "and run the appropriate "
                        "build/test/verification "
                        "command."
                    ),
                })

            else:

                messages.append({

                    "role": "user",

                    "content": (
                        "Perform one final "
                        "independent verification "
                        "of the reported issue. "
                        "Do not claim success "
                        "unless the executable "
                        "evidence proves it."
                    ),
                })

        except Exception as exc:

            error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            log(error)

            round_record[
                "error"
            ] = error

            evidence[
                "rounds"
            ].append(
                round_record
            )

            break

    evidence[
        "final_snapshot"
    ] = snapshot()

    evidence[
        "git_diff"
    ] = git_diff()

    if (
        write_observed
        and verification_after_write_observed
        and successful_command_observed
    ):
        evidence[
            "final_status"
        ] = "VERIFIED_FIXED"


    report = (
        STATE_DIR / "evidence.json"
    )

    report.write_text(
        json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 72)
    print(" FINAL STATUS")
    print("=" * 72)
    print(
        evidence["final_status"]
    )
    print()
    print(
        "Evidence:",
        report
    )
    if (
        evidence["final_status"] == "VERIFIED_FIXED"
        and os.environ.get("GITHUB_ACTIONS") == "true"
    ):
        try:
            print("VERIFIED FIX: Committing and pushing changes...")
            subprocess.run(["git", "config", "user.name", "KHALED Groq Repair Bot"], cwd=ROOT, check=False)
            subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=ROOT, check=False)
            subprocess.run(["git", "add", "-A"], cwd=ROOT, check=False)
            subprocess.run(["git", "commit", "-m", "fix: autonomous repair by KHALED Groq Repair"], cwd=ROOT, check=False)
            ref_name = os.environ.get("GITHUB_REF_NAME", "main")
            subprocess.run(["git", "push", "origin", f"HEAD:{ref_name}"], cwd=ROOT, check=False)
            print("AUTOMATIC COMMIT AND PUSH: SUCCESS")
        except Exception as push_err:
            print(f"AUTOMATIC COMMIT/PUSH ERROR: {push_err}")
    else:
        print("No automatic commit or push was performed.")


if __name__ == "__main__":

    main()
