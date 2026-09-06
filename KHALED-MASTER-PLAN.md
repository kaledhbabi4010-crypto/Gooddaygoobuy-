writing{variant="document" title="KHALED-MASTER-PLAN.md" id="58321"}

KHALED-MASTER-PLAN

1. Mission

Build goodbay220 as a professional, deterministic, AI-assisted deployment, verification, repair, upgrade and recovery system, with KHALED as the one-shot deployment/maintenance engine and REVO AI as the Autodesk runtime add-in architecture.

The repository must be self-building from this document and must never claim success without actual build/test/verification evidence.

2. Non-negotiable rules

Do not depend on GitHub Codespaces.

Do not require a paid AI service or paid AI agent.

AI providers are optional and replaceable.

Prefer local/open-source AI when available.

Never fabricate a test, build, browser action, server action, integration, or result.

Never treat an AI statement as proof of success.

Every successful stage must have deterministic evidence.

Never allow an AI agent unrestricted destructive shell access.

Use an allowlist for files/directories an AI repair may modify.

Keep secrets out of source code and logs.

Do not create Windows services, startup entries, resident daemons, polling loops, permanent sockets, tray processes, or permanent AI connections for KHALED.

KHALED starts only for install/verify/status/upgrade/repair/uninstall operations and terminates afterward.

Preserve rollback and recovery capability.

If an error cannot be repaired safely, stop and report it with evidence instead of pretending it was fixed.


3. Required repository result

The workflow must create the actual project structure automatically. Do not require the user to manually create dozens of files.

Target architecture:

goodbay220/
├── KHALED-X.csproj
├── Program.cs
├── src/
│   ├── Core/
│   ├── AI/
│   ├── Browser/
│   ├── Execution/
│   ├── Validation/
│   ├── Verification/
│   ├── Recovery/
│   ├── Security/
│   └── Autodesk/
├── tests/
│   ├── Unit/
│   ├── Integration/
│   └── Browser/
├── ai/
│   ├── agents/
│   ├── prompts/
│   └── orchestrator/
├── browser/
│   ├── playwright/
│   └── mcp/
├── docs/
├── artifacts/
└── .github/
    └── workflows/

The implementation may adjust this structure when technically necessary, but must document the reason.

4. KHALED responsibilities

KHALED is the deployment/lifecycle engine.

Required commands:

install

verify

status

upgrade

repair

uninstall


Execution pipeline:

Intent
  ↓
Preflight
  ↓
Discover
  ↓
Plan
  ↓
Policy
  ↓
Risk Assessment
  ↓
Execution Gate
  ↓
Execute
  ↓
Verify
  ↓
Evidence
  ↓
Recovery / Rollback if required
  ↓
Exit

KHALED must be deterministic wherever deterministic logic is possible.

5. REVO AI architecture

REVO AI is the runtime add-in architecture for Autodesk applications.

Autodesk-specific code must be isolated behind adapters and contracts.

Required conceptual components:

Intent Engine

Context Engine

Planning Engine

Command Normalizer

Validation Engine

Policy Engine

Risk Engine

Execution Gate

Adapter Router

Verification Engine

Recovery Engine


AI must never bypass the Execution Gate.

6. Autodesk compatibility

Design version-aware adapters for the intended compatibility range:

Revit 2016–2027

AutoCAD 2016–2027


Do not claim that a version works until that version is actually compiled/tested in an appropriate environment.

The compatibility layer must expose capabilities rather than assuming every API feature exists in every version.

7. Free AI agent architecture

The system must not require a paid AI agent.

Use this hierarchy:

1. Deterministic tools first.


2. Local open-source model/runtime when available.


3. Optional free-tier provider only when explicitly configured and currently available.


4. No paid provider is a mandatory dependency.



AI roles:

PlannerAgent — converts the master plan into structured tasks.

ResearchAgent — analyzes permitted project evidence and documentation.

CodingAgent — proposes code changes.

BuildAgent — analyzes build failures.

TestAgent — analyzes test failures.

DebugAgent — diagnoses root causes.

RepairAgent — creates bounded repair patches.

BrowserAgent — performs permitted browser tasks through the browser abstraction.

SecurityAgent — checks dangerous changes and secrets.

VerificationAgent — independently checks results.

ReviewerAgent — performs final consistency review.


Agents must exchange structured data, not uncontrolled free-form shell commands.

8. Autonomous repair loop

For every implementation/build/test failure:

1. Capture the real error.


2. Sanitize logs and secrets.


3. Classify the failure.


4. Collect relevant source/configuration/test context.


5. Ask the available AI to diagnose it.


6. Generate a structured repair proposal.


7. Check allowed paths and operations.


8. Validate the proposed patch.


9. Apply only an approved safe patch.


10. Build.


11. Test.


12. Verify.


13. Repeat only within a bounded repair budget.



Default maximum: 5 repair attempts per failure class.

If still failing:

preserve logs,

preserve attempted patches,

produce a machine-readable failure report,

mark the workflow unsuccessful,

never fabricate success.


9. Browser engine

Do not hard-code the project to Browser Use.

Create a BrowserEngine abstraction capable of using open-source execution components such as:

Playwright

Playwright MCP

agent-browser


The browser layer should prefer:

accessibility/semantic tree information,

deterministic selectors,

DOM inspection,

network/state inspection when permitted,

screenshots/vision only when necessary.


Browser automation must remain behind an explicit execution policy.

The browser agent must not bypass authentication, security controls, CAPTCHAs, access restrictions, or other protections.

10. Build and verification

The workflow must:

discover the project/solution instead of assuming a fixed path,

restore dependencies,

build,

run tests,

run static validation,

publish the executable,

generate checksums,

store logs and evidence as artifacts.


Do not assume a fixed framework output path unless the project configuration confirms it.

The build must fail if required tests fail.

11. Security

Implement:

secret redaction,

safe environment-variable handling,

path allowlists,

command allowlists,

patch validation,

no arbitrary destructive commands from AI,

no credential storage in the repository,

no secret values in generated artifacts,

clear separation between planning and execution.


12. Evidence

Every workflow must produce evidence including, where applicable:

build result,

test result,

compiler errors/warnings,

generated artifact path,

SHA-256 checksum,

repair attempts,

verification result,

unresolved failures.


An AI response saying “success” is never evidence.

13. GitHub Actions strategy

Codespaces must not be required.

The workflow should perform the build/test/repair pipeline on GitHub Actions where the required runner/tooling is available.

Do not assume unlimited free compute. Respect the repository/account Actions quota.

The workflow must work without an AI API key by running deterministic build/test/verification and explicitly reporting that AI repair is unavailable.

If a local AI runtime is available on a self-hosted runner, it may be used without a paid API.

14. Two-file bootstrap rule

The repository starts with only:

KHALED-MASTER-PLAN.md

.github/workflows/build.yml


The workflow itself must bootstrap the implementation from this plan.

It may create all required source files, tests, configuration, documentation and helper scripts automatically.

The workflow must not silently rewrite unrelated repository content.

Generated changes should be committed only when explicitly configured to do so.

15. Implementation phases

Phase 1 — Bootstrap

Read and validate KHALED-MASTER-PLAN.md.

Discover repository contents.

Create the required project structure.


Phase 2 — Project skeleton

Create the .NET project.

Create the core interfaces.

Create initial executable entry point.

Create test infrastructure.


Phase 3 — KHALED Core

Implement:

command parser,

lifecycle manager,

discovery,

preflight,

planning,

policy,

risk assessment,

execution gate.


Phase 4 — Validation / Verification / Recovery

Implement:

deterministic validation,

post-action verification,

evidence generation,

rollback,

recovery,

transaction boundaries.


Phase 5 — AI orchestration

Implement:

agent contracts,

planner,

diagnostics,

repair proposals,

bounded repair loop,

provider abstraction,

local/free-provider fallback.


Phase 6 — Browser engine

Implement the abstraction and adapters for:

Playwright,

Playwright MCP,

agent-browser.


Do not make any single browser implementation mandatory when another compatible implementation is available.

Phase 7 — Autodesk adapter architecture

Implement:

adapter contracts,

capability detection,

version routing,

compatibility boundaries,

Revit integration layer,

AutoCAD integration layer.


Do not falsely mark unsupported versions as supported.

Phase 8 — Tests

Create:

unit tests,

integration tests,

browser tests where applicable,

failure/recovery tests,

security tests,

configuration tests.


Phase 9 — Build / Publish / Evidence

Perform:

restore,

build,

test,

validation,

publish,

checksum,

evidence generation.


Phase 10 — Final verification

Verify the actual generated artifacts and test results.

Only after successful gates may the workflow report a successful build.

16. AI implementation rules

AI must:

inspect the actual repository before proposing changes,

use the actual compiler/test errors,

make the smallest safe change that addresses the root cause,

preserve existing valid functionality,

avoid unnecessary rewrites,

avoid deleting tests,

avoid weakening security,

avoid disabling warnings/tests merely to obtain success,

explain machine-readably what it changed,

verify its changes through deterministic tools.


AI must not:

invent files that it did not create,

claim tests ran when they did not,

claim external services were used when they were not,

claim Autodesk versions were tested when they were not,

expose secrets,

modify files outside the allowed repair scope,

execute unrestricted destructive commands.


17. Browser agent implementation rules

The BrowserAgent must operate through the BrowserEngine abstraction.

Preferred sequence:

Observe
  ↓
Understand
  ↓
Plan
  ↓
Act
  ↓
Observe
  ↓
Validate

For each important action, record:

intended action,

actual action,

result,

verification status.


Browser actions that affect external systems must require explicit policy approval where appropriate.

18. Repository integrity

Before applying an AI-generated repair:

1. Check repository status.


2. Identify changed files.


3. Validate the patch.


4. Confirm paths are allowed.


5. Reject unexpected binary or credential changes.


6. Apply the patch.


7. Build/test.


8. Keep evidence.



A repair must be reversible.

19. Deterministic-first principle

Before calling AI, attempt deterministic solutions such as:

dependency restoration,

correct project discovery,

standard compiler diagnostics,

known configuration fixes,

test execution,

static analysis,

generated-file cleanup where safe.


AI is used when reasoning is actually required.

This reduces AI usage, cost, complexity and false repairs.

20. Provider abstraction

Create an interface similar to:

IAIProvider
├── IsAvailable()
├── Analyze()
├── Plan()
├── GeneratePatch()
└── Review()

Possible implementations:

LocalAIProvider
FreeTierAIProvider
DisabledAIProvider

DisabledAIProvider is required so that the project remains buildable when no AI service is configured.

Never hard-code a paid provider as a mandatory dependency.

21. No-credit / no-Codespaces mode

The project must remain usable when:

Codespaces quota is exhausted,

AI API keys are absent,

optional AI services are unavailable,

browser services are unavailable.


In these cases:

deterministic stages continue where possible,

optional AI stages report unavailable,

no fake result is generated,

the workflow preserves evidence.


22. Logging

Use structured logs.

Every important operation should record:

timestamp,

operation,

component,

input summary,

result,

error if any,

verification status.


Secrets must be redacted.

Logs must not contain API keys, passwords, tokens, cookies, or private credentials.

23. Configuration

Use configuration files/environment variables rather than hard-coded secrets.

Examples:

AI_PROVIDER
AI_MODEL
AI_ENDPOINT
MAX_REPAIR_ATTEMPTS
BROWSER_ENGINE
BUILD_CONFIGURATION

Do not place secret values inside the repository.

24. Artifact requirements

A successful workflow should produce:

artifacts/
├── publish/
├── BUILD-EVIDENCE.txt
├── SHA256SUMS.txt
├── test-results/
├── logs/
├── verification/
└── repair/

The exact structure may evolve, but evidence must remain easy to inspect.

25. Acceptance criteria

The project is complete only when actual evidence demonstrates:

source generated successfully,

dependencies restore successfully,

project builds successfully,

required tests pass,

static/security validation passes,

executable is published,

checksum exists,

verification passes,

no mandatory unresolved gate remains.


Autodesk compatibility is reported individually according to actual SDK/build/test evidence.

26. Failure policy

Never hide failures.

Never replace a failing test with a fake test.

Never delete a failing test merely to obtain a green workflow.

Never weaken validation merely to pass CI.

Never report an untested Autodesk version as supported.

Never report an unavailable AI provider as active.

When blocked:

1. preserve the exact failure,


2. preserve relevant logs,


3. preserve attempted repairs,


4. identify the blocking dependency,


5. mark the result unresolved,


6. continue only with safe independent tasks.



27. Final verification report

At the end of execution, produce a machine-readable report containing at least:

repository
commit
build_status
test_status
verification_status
artifact_status
checksum_status
ai_status
repair_attempts
unresolved_failures
supported_autodesk_versions
unsupported_or_untested_versions

Every field must reflect actual observed state.

28. Final engineering principle

The AI is an engineering assistant and repair system, not the source of truth.

The source of truth is:

Actual source
+
Deterministic build
+
Actual tests
+
Actual verification
+
Evidence

The final executable must be produced only after those gates pass.

No simulation may be presented as a real execution.

No unsupported capability may be presented as verified.

The system should maximize autonomous problem solving while remaining deterministic, auditable, reversible, secure, and truthful.

writing{variant="document" title="KHALED-MASTER-PLAN.md" id="58321"}
# KHALED-MASTER-PLAN

## 1. Mission

Build `goodbay220` as a professional, deterministic, AI-assisted deployment, verification, repair, upgrade and recovery system, with `KHALED` as the one-shot deployment/maintenance engine and `REVO AI` as the Autodesk runtime add-in architecture.

The repository must be self-building from this document and must never claim success without actual build/test/verification evidence.

## 2. Non-negotiable rules

- Do not depend on GitHub Codespaces.
- Do not require a paid AI service or paid AI agent.
- AI providers are optional and replaceable.
- Prefer local/open-source AI when available.
- Never fabricate a test, build, browser action, server action, integration, or result.
- Never treat an AI statement as proof of success.
- Every successful stage must have deterministic evidence.
- Never allow an AI agent unrestricted destructive shell access.
- Use an allowlist for files/directories an AI repair may modify.
- Keep secrets out of source code and logs.
- Do not create Windows services, startup entries, resident daemons, polling loops, permanent sockets, tray processes, or permanent AI connections for KHALED.
- KHALED starts only for install/verify/status/upgrade/repair/uninstall operations and terminates afterward.
- Preserve rollback and recovery capability.
- If an error cannot be repaired safely, stop and report it with evidence instead of pretending it was fixed.

## 3. Required repository result

The workflow must create the actual project structure automatically. Do not require the user to manually create dozens of files.

Target architecture:

```text
goodbay220/
├── KHALED-X.csproj
├── Program.cs
├── src/
│   ├── Core/
│   ├── AI/
│   ├── Browser/
│   ├── Execution/
│   ├── Validation/
│   ├── Verification/
│   ├── Recovery/
│   ├── Security/
│   └── Autodesk/
├── tests/
│   ├── Unit/
│   ├── Integration/
│   └── Browser/
├── ai/
│   ├── agents/
│   ├── prompts/
│   └── orchestrator/
├── browser/
│   ├── playwright/
│   └── mcp/
├── docs/
├── artifacts/
└── .github/
    └── workflows/
```

The implementation may adjust this structure when technically necessary, but must document the reason.

## 4. KHALED responsibilities

KHALED is the deployment/lifecycle engine.

Required commands:

- `install`
- `verify`
- `status`
- `upgrade`
- `repair`
- `uninstall`

Execution pipeline:

```text
Intent
  ↓
Preflight
  ↓
Discover
  ↓
Plan
  ↓
Policy
  ↓
Risk Assessment
  ↓
Execution Gate
  ↓
Execute
  ↓
Verify
  ↓
Evidence
  ↓
Recovery / Rollback if required
  ↓
Exit
```

KHALED must be deterministic wherever deterministic logic is possible.

## 5. REVO AI architecture

REVO AI is the runtime add-in architecture for Autodesk applications.

Autodesk-specific code must be isolated behind adapters and contracts.

Required conceptual components:

- Intent Engine
- Context Engine
- Planning Engine
- Command Normalizer
- Validation Engine
- Policy Engine
- Risk Engine
- Execution Gate
- Adapter Router
- Verification Engine
- Recovery Engine

AI must never bypass the Execution Gate.

## 6. Autodesk compatibility

Design version-aware adapters for the intended compatibility range:

- Revit 2016–2027
- AutoCAD 2016–2027

Do not claim that a version works until that version is actually compiled/tested in an appropriate environment.

The compatibility layer must expose capabilities rather than assuming every API feature exists in every version.

## 7. Free AI agent architecture

The system must not require a paid AI agent.

Use this hierarchy:

1. Deterministic tools first.
2. Local open-source model/runtime when available.
3. Optional free-tier provider only when explicitly configured and currently available.
4. No paid provider is a mandatory dependency.

AI roles:

- `PlannerAgent` — converts the master plan into structured tasks.
- `ResearchAgent` — analyzes permitted project evidence and documentation.
- `CodingAgent` — proposes code changes.
- `BuildAgent` — analyzes build failures.
- `TestAgent` — analyzes test failures.
- `DebugAgent` — diagnoses root causes.
- `RepairAgent` — creates bounded repair patches.
- `BrowserAgent` — performs permitted browser tasks through the browser abstraction.
- `SecurityAgent` — checks dangerous changes and secrets.
- `VerificationAgent` — independently checks results.
- `ReviewerAgent` — performs final consistency review.

Agents must exchange structured data, not uncontrolled free-form shell commands.

## 8. Autonomous repair loop

For every implementation/build/test failure:

1. Capture the real error.
2. Sanitize logs and secrets.
3. Classify the failure.
4. Collect relevant source/configuration/test context.
5. Ask the available AI to diagnose it.
6. Generate a structured repair proposal.
7. Check allowed paths and operations.
8. Validate the proposed patch.
9. Apply only an approved safe patch.
10. Build.
11. Test.
12. Verify.
13. Repeat only within a bounded repair budget.

Default maximum: 5 repair attempts per failure class.

If still failing:

- preserve logs,
- preserve attempted patches,
- produce a machine-readable failure report,
- mark the workflow unsuccessful,
- never fabricate success.

## 9. Browser engine

Do not hard-code the project to Browser Use.

Create a `BrowserEngine` abstraction capable of using open-source execution components such as:

- Playwright
- Playwright MCP
- agent-browser

The browser layer should prefer:

- accessibility/semantic tree information,
- deterministic selectors,
- DOM inspection,
- network/state inspection when permitted,
- screenshots/vision only when necessary.

Browser automation must remain behind an explicit execution policy.

The browser agent must not bypass authentication, security controls, CAPTCHAs, access restrictions, or other protections.

## 10. Build and verification

The workflow must:

- discover the project/solution instead of assuming a fixed path,
- restore dependencies,
- build,
- run tests,
- run static validation,
- publish the executable,
- generate checksums,
- store logs and evidence as artifacts.

Do not assume a fixed framework output path unless the project configuration confirms it.

The build must fail if required tests fail.

## 11. Security

Implement:

- secret redaction,
- safe environment-variable handling,
- path allowlists,
- command allowlists,
- patch validation,
- no arbitrary destructive commands from AI,
- no credential storage in the repository,
- no secret values in generated artifacts,
- clear separation between planning and execution.

## 12. Evidence

Every workflow must produce evidence including, where applicable:

- build result,
- test result,
- compiler errors/warnings,
- generated artifact path,
- SHA-256 checksum,
- repair attempts,
- verification result,
- unresolved failures.

An AI response saying “success” is never evidence.

## 13. GitHub Actions strategy

Codespaces must not be required.

The workflow should perform the build/test/repair pipeline on GitHub Actions where the required runner/tooling is available.

Do not assume unlimited free compute. Respect the repository/account Actions quota.

The workflow must work without an AI API key by running deterministic build/test/verification and explicitly reporting that AI repair is unavailable.

If a local AI runtime is available on a self-hosted runner, it may be used without a paid API.

## 14. Two-file bootstrap rule

The repository starts with only:

- `KHALED-MASTER-PLAN.md`
- `.github/workflows/build.yml`

The workflow itself must bootstrap the implementation from this plan.

It may create all required source files, tests, configuration, documentation and helper scripts automatically.

The workflow must not silently rewrite unrelated repository content.

Generated changes should be committed only when explicitly configured to do so.

## 15. Implementation phases

### Phase 1 — Bootstrap

- Read and validate `KHALED-MASTER-PLAN.md`.
- Discover repository contents.
- Create the required project structure.

### Phase 2 — Project skeleton

- Create the .NET project.
- Create the core interfaces.
- Create initial executable entry point.
- Create test infrastructure.

### Phase 3 — KHALED Core

Implement:

- command parser,
- lifecycle manager,
- discovery,
- preflight,
- planning,
- policy,
- risk assessment,
- execution gate.

### Phase 4 — Validation / Verification / Recovery

Implement:

- deterministic validation,
- post-action verification,
- evidence generation,
- rollback,
- recovery,
- transaction boundaries.

### Phase 5 — AI orchestration

Implement:

- agent contracts,
- planner,
- diagnostics,
- repair proposals,
- bounded repair loop,
- provider abstraction,
- local/free-provider fallback.

### Phase 6 — Browser engine

Implement the abstraction and adapters for:

- Playwright,
- Playwright MCP,
- agent-browser.

Do not make any single browser implementation mandatory when another compatible implementation is available.

### Phase 7 — Autodesk adapter architecture

Implement:

- adapter contracts,
- capability detection,
- version routing,
- compatibility boundaries,
- Revit integration layer,
- AutoCAD integration layer.

Do not falsely mark unsupported versions as supported.

### Phase 8 — Tests

Create:

- unit tests,
- integration tests,
- browser tests where applicable,
- failure/recovery tests,
- security tests,
- configuration tests.

### Phase 9 — Build / Publish / Evidence

Perform:

- restore,
- build,
- test,
- validation,
- publish,
- checksum,
- evidence generation.

### Phase 10 — Final verification

Verify the actual generated artifacts and test results.

Only after successful gates may the workflow report a successful build.

## 16. AI implementation rules

AI must:

- inspect the actual repository before proposing changes,
- use the actual compiler/test errors,
- make the smallest safe change that addresses the root cause,
- preserve existing valid functionality,
- avoid unnecessary rewrites,
- avoid deleting tests,
- avoid weakening security,
- avoid disabling warnings/tests merely to obtain success,
- explain machine-readably what it changed,
- verify its changes through deterministic tools.

AI must not:

- invent files that it did not create,
- claim tests ran when they did not,
- claim external services were used when they were not,
- claim Autodesk versions were tested when they were not,
- expose secrets,
- modify files outside the allowed repair scope,
- execute unrestricted destructive commands.

## 17. Browser agent implementation rules

The BrowserAgent must operate through the BrowserEngine abstraction.

Preferred sequence:

```text
Observe
  ↓
Understand
  ↓
Plan
  ↓
Act
  ↓
Observe
  ↓
Validate
```

For each important action, record:

- intended action,
- actual action,
- result,
- verification status.

Browser actions that affect external systems must require explicit policy approval where appropriate.

## 18. Repository integrity

Before applying an AI-generated repair:

1. Check repository status.
2. Identify changed files.
3. Validate the patch.
4. Confirm paths are allowed.
5. Reject unexpected binary or credential changes.
6. Apply the patch.
7. Build/test.
8. Keep evidence.

A repair must be reversible.

## 19. Deterministic-first principle

Before calling AI, attempt deterministic solutions such as:

- dependency restoration,
- correct project discovery,
- standard compiler diagnostics,
- known configuration fixes,
- test execution,
- static analysis,
- generated-file cleanup where safe.

AI is used when reasoning is actually required.

This reduces AI usage, cost, complexity and false repairs.

## 20. Provider abstraction

Create an interface similar to:

```text
IAIProvider
├── IsAvailable()
├── Analyze()
├── Plan()
├── GeneratePatch()
└── Review()
```

Possible implementations:

```text
LocalAIProvider
FreeTierAIProvider
DisabledAIProvider
```

`DisabledAIProvider` is required so that the project remains buildable when no AI service is configured.

Never hard-code a paid provider as a mandatory dependency.

## 21. No-credit / no-Codespaces mode

The project must remain usable when:

- Codespaces quota is exhausted,
- AI API keys are absent,
- optional AI services are unavailable,
- browser services are unavailable.

In these cases:

- deterministic stages continue where possible,
- optional AI stages report unavailable,
- no fake result is generated,
- the workflow preserves evidence.

## 22. Logging

Use structured logs.

Every important operation should record:

- timestamp,
- operation,
- component,
- input summary,
- result,
- error if any,
- verification status.

Secrets must be redacted.

Logs must not contain API keys, passwords, tokens, cookies, or private credentials.

## 23. Configuration

Use configuration files/environment variables rather than hard-coded secrets.

Examples:

```text
AI_PROVIDER
AI_MODEL
AI_ENDPOINT
MAX_REPAIR_ATTEMPTS
BROWSER_ENGINE
BUILD_CONFIGURATION
```

Do not place secret values inside the repository.

## 24. Artifact requirements

A successful workflow should produce:

```text
artifacts/
├── publish/
├── BUILD-EVIDENCE.txt
├── SHA256SUMS.txt
├── test-results/
├── logs/
├── verification/
└── repair/
```

The exact structure may evolve, but evidence must remain easy to inspect.

## 25. Acceptance criteria

The project is complete only when actual evidence demonstrates:

- source generated successfully,
- dependencies restore successfully,
- project builds successfully,
- required tests pass,
- static/security validation passes,
- executable is published,
- checksum exists,
- verification passes,
- no mandatory unresolved gate remains.

Autodesk compatibility is reported individually according to actual SDK/build/test evidence.

## 26. Failure policy

Never hide failures.

Never replace a failing test with a fake test.

Never delete a failing test merely to obtain a green workflow.

Never weaken validation merely to pass CI.

Never report an untested Autodesk version as supported.

Never report an unavailable AI provider as active.

When blocked:

1. preserve the exact failure,
2. preserve relevant logs,
3. preserve attempted repairs,
4. identify the blocking dependency,
5. mark the result unresolved,
6. continue only with safe independent tasks.

## 27. Final verification report

At the end of execution, produce a machine-readable report containing at least:

```text
repository
commit
build_status
test_status
verification_status
artifact_status
checksum_status
ai_status
repair_attempts
unresolved_failures
supported_autodesk_versions
unsupported_or_untested_versions
```

Every field must reflect actual observed state.

## 28. Final engineering principle

The AI is an engineering assistant and repair system, not the source of truth.

The source of truth is:

```text
Actual source
+
Deterministic build
+
Actual tests
+
Actual verification
+
Evidence
```

The final executable must be produced only after those gates pass.

No simulation may be presented as a real execution.

No unsupported capability may be presented as verified.

The system should maximize autonomous problem solving while remaining deterministic, auditable, reversible, secure, and truthful.
