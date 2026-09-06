writing{variant="document" id="58321" title="KHALED-MASTER-PLAN — خطة التنفيذ والإصلاح الجذري الشاملة"}

KHALED-MASTER-PLAN

خطة التنفيذ والإصلاح الجذري الشاملة لمشروع Gooddaygoobuy / KHALED / REVO AI

الإصدار: Final Execution Architecture
التاريخ: 2026-09-06
الحالة: Execution-Ready Specification
المبدأ الأساسي: لا نجاح بدون دليل حقيقي قابل للتحقق.


---

1. الهدف

تحويل مستودع Gooddaygoobuy- من مجرد وثيقة مواصفات وWorkflow غير صالح إلى نظام برمجي حقيقي قابل للبناء والاختبار والتحقق والإصلاح الذاتي الآمن.

يجب أن يستطيع النظام:

1. قراءة KHALED-MASTER-PLAN.md.


2. فحص حالة المستودع والبيئة.


3. إنشاء البنية البرمجية الناقصة.


4. إنشاء KHALED Core.


5. إنشاء الاختبارات.


6. تنفيذ Build حقيقي.


7. تنفيذ Tests حقيقية.


8. اكتشاف الأخطاء الحقيقية.


9. تشخيص الأخطاء.


10. اقتراح إصلاحات آمنة.


11. تطبيق الإصلاحات المسموح بها فقط.


12. إعادة Build/Test.


13. التراجع عن الإصلاح الفاشل.


14. تنفيذ Verification مستقل.


15. إنشاء Evidence حقيقي.


16. إنشاء Artifacts.


17. عدم إعلان النجاح إلا إذا أثبتت الأدلة النجاح.


18. العمل بدون Codespaces.


19. عدم الاعتماد على AI مدفوع.


20. جعل AI اختياريًا وليس نقطة فشل أساسية.




---

2. قاعدة الحقيقة المطلقة

يُمنع على النظام وعلى أي Agent داخله:

اختلاق نتائج.

إعلان Build ناجحًا دون Exit Code ناجح.

إعلان Tests ناجحة دون تشغيلها.

إعلان دعم Revit/AutoCAD دون اختبار فعلي.

إعلان EXE صالح دون وجوده والتحقق منه.

الادعاء باستخدام خادم أو خدمة لم يتم استخدامها.

الادعاء بإصلاح خطأ لم تتم إعادة اختباره.

تحويل NOT VERIFIED إلى VERIFIED بدون Evidence.

حذف الاختبارات لتجنب الفشل.

تعطيل Security Controls لإجبار Build على النجاح.

إخفاء Errors.

استخدام بيانات أو مفاتيح سرية داخل Repository أو Logs.


كل نتيجة يجب أن تكون واحدة من:

VERIFIED
FAILED
NOT_VERIFIED
NOT_APPLICABLE
BLOCKED

ولا توجد حالة خامسة تعني نجاحًا غير مثبت.


---

3. البنية الصحيحة للمستودع

يجب أن تصبح البنية تدريجيًا:

Gooddaygoobuy-/
│
├── KHALED-MASTER-PLAN.md
│
├── bootstrap/
│   ├── bootstrap.sh
│   ├── manifest.json
│   └── schema/
│
├── scripts/
│   ├── validate-plan.sh
│   ├── bootstrap.sh
│   ├── discover.sh
│   ├── build.sh
│   ├── test.sh
│   ├── diagnose.sh
│   ├── verify.sh
│   ├── evidence.sh
│   └── publish.sh
│
├── src/
│   └── KHALED/
│       ├── KHALED.csproj
│       ├── Program.cs
│       │
│       ├── Core/
│       ├── AI/
│       ├── Browser/
│       ├── Execution/
│       ├── Validation/
│       ├── Verification/
│       ├── Recovery/
│       ├── Security/
│       └── Autodesk/
│
├── tests/
│   ├── Unit/
│   ├── Integration/
│   ├── Security/
│   ├── Recovery/
│   ├── Repair/
│   ├── Browser/
│   └── Compatibility/
│
├── ai/
│   ├── agents/
│   ├── providers/
│   ├── prompts/
│   └── orchestrator/
│
├── browser/
│   ├── abstractions/
│   ├── playwright/
│   ├── playwright-mcp/
│   └── agent-browser/
│
├── Autodesk/
│   ├── Revit/
│   └── AutoCAD/
│
├── artifacts/
│
├── docs/
│
└── .github/
    └── workflows/
        └── build.yml

لا يجب إنشاء جميع الملفات دفعة واحدة بلا تحقق.

يجب إنشاؤها على مراحل، وكل مرحلة يجب أن تمر بالتحقق قبل الانتقال إلى المرحلة التالية.


---

4. مبدأ Bootstrap

الـ Workflow يجب ألا يفترض أن المشروع موجود.

عند البداية:

CHECKOUT
↓
VALIDATE PLAN
↓
PREFLIGHT
↓
DISCOVER
↓
BOOTSTRAP

يجب أن يكتشف:

هل الخطة موجودة؟

هل الخطة فارغة؟

هل Repository صالح؟

هل Git متاح؟

هل .NET متاح؟

ما إصدار .NET؟

هل توجد Solution؟

هل توجد Projects؟

هل توجد Tests؟

هل توجد Scripts؟

هل توجد ملفات KHALED؟

هل توجد تغييرات يدوية؟

هل توجد ملفات مجهولة؟

هل توجد أسرار مكشوفة؟



---

5. عدم تدمير العمل الموجود

Bootstrap يجب أن يكون Idempotent.

أي:

تشغيل أول
→ إنشاء الناقص

تشغيل ثاني
→ لا يعيد إنشاء الموجود بلا سبب

تشغيل ثالث
→ لا يحذف العمل السابق

يجب عدم استخدام:

delete everything
recreate everything

إلا في بيئة اختبار صريحة.

كل ملف يتم إنشاؤه أو تعديله يجب أن يكون معروفًا في Manifest.


---

6. Manifest

يجب إنشاء:

bootstrap/manifest.json

ليحتوي على:

إصدار الخطة.

إصدار Schema.

الملفات المنشأة.

الملفات المعدلة.

الملفات المتحقق منها.

Build state.

Test state.

Repair attempts.

Verification state.

Artifact hashes.

آخر Failure Fingerprints.


مثال:

{
  "schemaVersion": 1,
  "project": "Gooddaygoobuy",
  "engine": "KHALED",
  "plan": "KHALED-MASTER-PLAN.md",
  "build": "NOT_VERIFIED",
  "tests": "NOT_VERIFIED",
  "verification": "NOT_VERIFIED",
  "repairAttempts": 0
}


---

7. KHALED Core

KHALED هو Deployment/Lifecycle Engine وليس Resident Runtime.

الأوامر الأساسية:

install
verify
status
upgrade
repair
uninstall

Pipeline:

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
Risk
↓
Execution Gate
↓
Execute
↓
Verify
↓
Evidence
↓
Recovery/Rollback
↓
Exit


---

8. KHALED يجب ألا يكون Resident

يُمنع:

Windows Service دائم.

Startup Entry.

Tray Process.

Daemon.

Permanent Background Process.

Permanent Socket.

Polling Loop دائم.

Permanent AI Connection.

Deployment Monitor دائم.

Resident Installer.


KHALED يعمل فقط عند طلب:

install
verify
status
upgrade
repair
uninstall

ثم ينتهي.


---

9. REVO AI

REVO AI هو Runtime Add-in/AI Integration Architecture.

يجب فصل:

KHALED

عن:

REVO AI

بحيث:

KHALED
=
Deployment / Lifecycle / Recovery

REVO AI
=
Runtime Autodesk Add-in


---

10. REVO AI Core

المكونات:

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

Pipeline:

User Intent
↓
Intent Engine
↓
Context
↓
Planning
↓
Normalization
↓
Validation
↓
Policy
↓
Risk
↓
Execution Gate
↓
Adapter Router
↓
Autodesk Execution
↓
Verification
↓
Evidence


---

11. AI Architecture

AI ليس شرطًا لتشغيل KHALED.

يجب تعريف:

IAIProvider

ثم:

DisabledAIProvider
LocalAIProvider
OptionalFreeProvider

الترتيب:

Deterministic Logic
↓
Local Open-Source AI
↓
Configured Free Provider
↓
No AI

إذا لم يوجد AI:

النظام لا يتوقف لمجرد عدم وجود AI.


---

12. Multi-Agent Architecture

الوكلاء:

PlannerAgent
ResearchAgent
CodingAgent
BuildAgent
TestAgent
DebugAgent
RepairAgent
BrowserAgent
SecurityAgent
VerificationAgent
ReviewerAgent

لكن لا يسمح لأي Agent بالعمل خارج صلاحياته.


---

13. فصل التخطيط عن التنفيذ

AI يستطيع:

Observe
Analyze
Plan
Propose

لكن لا ينفذ مباشرة.

يجب أن يمر كل تنفيذ عبر:

Policy Engine
↓
Risk Engine
↓
Execution Gate

ثم:

Execute


---

14. نظام إصلاح الأخطاء

عند Build Failure:

BUILD
↓
CAPTURE ERROR
↓
SANITIZE
↓
FINGERPRINT
↓
CLASSIFY
↓
COLLECT CONTEXT
↓
DIAGNOSE
↓
GENERATE PATCH
↓
VALIDATE PATCH
↓
SECURITY CHECK
↓
EXECUTION GATE
↓
APPLY PATCH
↓
BUILD
↓
TEST
↓
VERIFY

إذا نجح:

REPAIR VERIFIED

إذا فشل:

ROLLBACK

ثم محاولة أخرى محدودة.


---

15. الحد الأقصى للإصلاح

الافتراضي:

MAX_ATTEMPTS_PER_FAILURE_CLASS = 5

بعد 5 محاولات:

UNRESOLVED

ويجب التوقف بدل الدخول في Loop لا نهائي.


---

16. Error Fingerprint

يجب إنشاء بصمة للخطأ تعتمد على:

Error Type
Error Code
Compiler
File
Line
Column
Relevant Stack
Target Framework
OS
Project
Stage

بحيث يعرف النظام أن:

CS1002

هو نفس Failure Class حتى لو اختلفت بعض تفاصيل Log.


---

17. Patch Safety

كل Patch يجب أن يمر عبر:

Syntax Validation
↓
Path Validation
↓
Diff Validation
↓
Secret Scan
↓
Dangerous Operation Scan
↓
Scope Check
↓
Execution Gate

ويُرفض إذا:

خارج Workspace.

يحذف ملفات غير مصرح بها.

يغير Security Policy.

يزيل Tests.

يضيف Secrets.

ينفذ أمرًا خطيرًا.

يغير ملفات غير مرتبطة بالمشكلة.



---

18. Command Allowlist

AI لا يستطيع تشغيل أوامر عشوائية.

يجب وجود:

CommandAllowlist

و:

PathAllowlist

و:

EnvironmentAllowlist

أي Command غير معروف:

REJECTED


---

19. Secret Protection

يجب فحص:

GitHub Secrets
Environment Variables
Logs
AI prompts
Artifacts
Source Code

ويجب إزالة:

API Keys
Tokens
Passwords
Private Keys
Credentials
Cookies
Session Tokens

من Logs وEvidence.


---

20. Build Engine

Build Engine يجب أن يكتشف المشروع بدل افتراضه.

يبحث عن:

*.sln
*.slnx
*.csproj

ثم:

Discover
↓
Restore
↓
Build
↓
Test
↓
Publish

لا يجوز افتراض Output Path ثابت.


---

21. Test Engine

يكتشف مشاريع الاختبار تلقائيًا.

يجب تشغيل:

Unit Tests
Integration Tests
Security Tests
Recovery Tests
Repair Tests
Configuration Tests

إذا لم توجد Tests:

TESTS_NOT_AVAILABLE

ولا تسجل:

TESTS_PASSED


---

22. اختبارات الفشل

يجب اختبار النظام ضد:

Invalid YAML
Missing Project
Broken Project
Compilation Error
Test Failure
Invalid Patch
Unauthorized Path
Secret Leakage
Failed Repair
Rollback Failure
Missing Artifact
Corrupt Artifact
Unsupported Autodesk Version
Missing SDK


---

23. Recovery Engine

عند فشل Patch:

Restore Previous State
↓
Verify Repository
↓
Rebuild
↓
Retest

إذا فشل Recovery:

RECOVERY_FAILED

ولا يواصل النظام تعديلات عشوائية.


---

24. Verification Engine

Verification مستقل عن Build.

يتحقق من:

Project Exists
↓
Compilation
↓
Tests
↓
Expected Files
↓
Artifact Exists
↓
Artifact Integrity
↓
Hash
↓
Runtime Smoke Test
↓
Security


---

25. Evidence Engine

كل Run يجب أن ينتج:

artifacts/evidence/

ويتضمن:

build.json
tests.json
verification.json
environment.json
failure-report.json
repair-history.json
SHA256SUMS.txt

كل Evidence يجب أن يحتوي:

Timestamp
Commit
Workflow Run
Stage
Input
Action
Result
Exit Code
Evidence


---

26. Artifact Integrity

كل Artifact يتم حساب:

SHA-256

ويُحفظ في:

SHA256SUMS.txt

لا يكفي وجود EXE.

يجب التحقق من:

Exists
Readable
Expected Format
Expected Size > 0
Hash Generated


---

27. GitHub Actions

build.yml يجب أن يكون Workflow حقيقيًا.

لا يجب أن يحتوي على مخطط نصي مثل:

KHALED-MASTER-PLAN.md
↓
Build
↓
Test

بل يجب أن يحتوي على:

name:
on:
permissions:
jobs:
steps:

ويستدعي Scripts التنفيذ الفعلية.


---

28. Codespaces

Codespaces ليس Dependency.

إذا انتهى رصيد Codespaces:

النظام يستمر عبر GitHub Actions

ولا يتوقف المشروع بالكامل.


---

29. GitHub Actions Quota

يجب تقليل الاستهلاك عبر:

عدم تشغيل AI عند عدم الحاجة.

عدم تكرار Build بلا سبب.

Caching للـ .NET.

إصلاح Failure Class بدل إعادة نفس العملية.

Bounded retries.

عدم تشغيل Browser Tests إلا عند الحاجة.

عدم إعادة الاختبارات التي لم تتأثر بالتغيير إلا إذا كانت Integration/Critical.



---

30. AI Repair بدون تكلفة إجبارية

إذا لم توجد:

API Key

يجب أن يعمل:

Deterministic Diagnostics

وإذا توفر Local AI:

Local AI

وإذا تم تكوين Free Provider:

Free Provider

لكن لا يوجد:

Mandatory Paid API


---

31. Browser Engine

تعريف:

IBrowserEngine

مع Implementations:

Playwright
Playwright MCP
agent-browser

الأولوية:

DOM
↓
Accessibility Tree
↓
Semantic Interaction
↓
Screenshot/Vision

الرؤية تستخدم عند الحاجة فقط.


---

32. Browser Safety

Browser Agent ممنوع من:

تجاوز CAPTCHA.

تجاوز Authentication.

تجاوز Security Controls.

سرقة Credentials.

استخراج Session Tokens.

تنفيذ أعمال غير مصرح بها.


يجب تسجيل:

Intent
Observed State
Action
Expected Result
Actual Result
Verification


---

33. Autodesk Architecture

يجب تعريف:

IAutodeskAdapter

ثم:

RevitAdapter
AutoCADAdapter

مع Version/Capability routing.


---

34. Revit

الهدف المعماري:

Revit 2016
Revit 2017
...
Revit 2027

لكن:

لا يُعلن أي إصدار VERIFIED قبل اختباره فعليًا.

الحالة الأولية:

NOT_VERIFIED

حتى توجد بيئة فعلية ودليل.


---

35. AutoCAD

الهدف:

AutoCAD 2016
AutoCAD 2017
...
AutoCAD 2027

نفس القاعدة:

لا دعم مثبت بدون اختبار حقيقي.


---

36. Autodesk Compatibility Matrix

يجب إنشاء:

compatibility-matrix.json

مثال:

{
  "revit": {
    "2016": "NOT_VERIFIED",
    "2017": "NOT_VERIFIED",
    "2018": "NOT_VERIFIED",
    "2019": "NOT_VERIFIED",
    "2020": "NOT_VERIFIED",
    "2021": "NOT_VERIFIED",
    "2022": "NOT_VERIFIED",
    "2023": "NOT_VERIFIED",
    "2024": "NOT_VERIFIED",
    "2025": "NOT_VERIFIED",
    "2026": "NOT_VERIFIED",
    "2027": "NOT_VERIFIED"
  },
  "autocad": {
    "2016": "NOT_VERIFIED",
    "2017": "NOT_VERIFIED",
    "2018": "NOT_VERIFIED",
    "2019": "NOT_VERIFIED",
    "2020": "NOT_VERIFIED",
    "2021": "NOT_VERIFIED",
    "2022": "NOT_VERIFIED",
    "2023": "NOT_VERIFIED",
    "2024": "NOT_VERIFIED",
    "2025": "NOT_VERIFIED",
    "2026": "NOT_VERIFIED",
    "2027": "NOT_VERIFIED"
  }
}


---

37. Capability System

بدل الاعتماد فقط على Version:

Application
+
Version
+
Capability

مثال:

Revit
2024
ExternalCommand

ثم:

AdapterRouter

يحدد Adapter الصحيح.


---

38. Universal Contract

يجب أن يكون هناك Contract ثابت بين:

REVO AI Core

و:

Autodesk Adapters

يتضمن:

Request
Context
Capability
Command
Risk
Execution
Result
Verification
Evidence
Error


---

39. Configuration

يجب ألا تكون الإعدادات موزعة داخل الكود.

تعريف:

ConfigurationProvider

يدعم:

Environment
Config File
CLI
Defaults

مع أولوية واضحة.


---

40. Logging

يجب أن يكون Logging:

Structured
Machine-readable
Human-readable
Redacted
Timestamped

ويمنع تسجيل الأسرار.


---

41. CLI

يجب توفير:

khaled install
khaled verify
khaled status
khaled upgrade
khaled repair
khaled uninstall

ويجب أن تكون Exit Codes محددة.

مثال:

0 = SUCCESS
1 = GENERAL_FAILURE
2 = INVALID_ARGUMENT
3 = VALIDATION_FAILURE
4 = BUILD_FAILURE
5 = TEST_FAILURE
6 = VERIFICATION_FAILURE
7 = REPAIR_EXHAUSTED
8 = SECURITY_BLOCK
9 = RECOVERY_FAILURE


---

42. Transactional Installation

Installation:

Preflight
↓
Backup
↓
Stage
↓
Validate
↓
Commit
↓
Verify

إذا فشل قبل Commit:

Rollback


---

43. Upgrade

Upgrade:

Discover
↓
Compare
↓
Backup
↓
Stage
↓
Validate
↓
Apply
↓
Verify

إذا فشل:

Rollback


---

44. Uninstall

Uninstall يجب ألا يحذف ملفات غير مملوكة لـ KHALED.

يجب الاعتماد على:

Ownership Manifest

ولا يجوز:

Delete unknown files


---

45. Status

status يجب أن يكون Read-Only قدر الإمكان.

يعرض:

Installed
Version
Components
Integrity
Last Verification
AI Provider
Browser Provider
Autodesk Adapters
Failures


---

46. Repository Integrity

قبل أي Repair:

Git Status
↓
Tracked Files
↓
Manifest
↓
Allowed Scope

يجب ألا يلمس AI ملفات خارج النطاق.


---

47. Plan Validation

قبل Bootstrap يجب تحليل:

KHALED-MASTER-PLAN.md

لكن لا يجب أن يعتمد التنفيذ على فهم حر للغة الطبيعية فقط.

يجب استخراج:

Requirements
Modules
Commands
Constraints
Target Platforms
Verification Rules
Security Rules

ثم تحويلها إلى Machine-readable requirements.


---

48. Requirement Registry

إنشاء:

requirements.json

مثال:

{
  "id": "KHALED-001",
  "description": "No resident daemon",
  "category": "architecture",
  "mandatory": true,
  "verification": "static"
}

كل Requirement يجب أن يمتلك:

ID
Description
Priority
Verification Method
Status
Evidence


---

49. Traceability

يجب أن نستطيع تتبع:

Requirement
↓
Implementation
↓
Test
↓
Verification
↓
Evidence

مثال:

KHALED-001
↓
ResidentProcessGuard
↓
SecurityTest
↓
Verification
↓
evidence.json


---

50. Reviewer Agent

ReviewerAgent لا ينفذ.

دوره:

Review Plan
Review Code
Review Patch
Review Tests
Review Evidence

ويستطيع رفض:

False Success
Unsafe Patch
Missing Test
Missing Evidence
Scope Violation


---

51. Final Gate

قبل إعلان:

SUCCESS

يجب أن تمر:

Build
AND
Tests
AND
Security
AND
Verification
AND
Artifacts
AND
Evidence

إذا فشل أي شرط:

FAILED


---

52. لا يوجد "Success by Hope"

العبارات التالية ممنوعة:

probably works
should work
looks correct
assumed compatible
AI says fixed
build expected to pass

داخل Evidence.

يجب استخدام نتائج فعلية فقط.


---

53. مراحل التنفيذ

Phase 0 — Repository Recovery

فحص Git.

فحص الملفات.

فحص Workflow.

حفظ الحالة الحالية.

عدم حذف أي عمل.


الحالة:

RECOVERED


---

Phase 1 — Workflow Repair

استبدال build.yml غير الصالح بـ Workflow حقيقي.

الهدف:

GitHub Actions starts successfully


---

Phase 2 — Bootstrap

إنشاء:

bootstrap/
scripts/
src/
tests/

مع المحافظة على الملفات الموجودة.


---

Phase 3 — KHALED Core

إنشاء:

CLI
Lifecycle
Execution
Policy
Risk
Validation
Verification
Recovery
Security


---

Phase 4 — Deterministic Build

تحقيق:

Restore
Build
Test
Publish
Evidence

بدون AI.


---

Phase 5 — Diagnostics

إضافة:

Error Parser
Fingerprint
Classifier
Context Collector


---

Phase 6 — Repair Engine

إضافة:

Repair Planner
Patch Validator
Execution Gate
Rollback
Retry


---

Phase 7 — AI Layer

إضافة:

IAIProvider
DisabledAIProvider
Local Provider
Optional Free Provider
Agents


---

Phase 8 — Browser

إضافة:

IBrowserEngine
Playwright
Playwright MCP
agent-browser

مع Safety Layer.


---

Phase 9 — Autodesk

إضافة:

IAutodeskAdapter
RevitAdapter
AutoCADAdapter
Capability Router
Compatibility Matrix


---

Phase 10 — Testing

إضافة:

Unit
Integration
Security
Recovery
Repair
Browser
Compatibility


---

Phase 11 — Verification

إضافة:

Independent Verification
Evidence
Hashes
Artifact Validation


---

Phase 12 — Final Release

فقط بعد اجتياز جميع Gates:

Build
Test
Verify
Security
Evidence
Artifact


---

54. Recovery من GitHub Actions Failure

إذا فشل Workflow:

1. اقرأ Error الحقيقي.


2. لا تخمن.


3. حدد Stage.


4. استخرج Error Fingerprint.


5. افحص الملفات المتعلقة.


6. أصلح السبب الجذري.


7. تحقق من Patch.


8. أعد Build.


9. أعد Tests.


10. تحقق.


11. احتفظ بالدليل.




---

55. لا تستخدم Retry أعمى

ممنوع:

Run again
Run again
Run again

بدون تغيير السبب.

كل Retry يجب أن يكون مرتبطًا بـ:

New Diagnosis
+
New Validated Change


---

56. عدم تغيير الخطة تلقائيًا

AI لا يجوز له إعادة كتابة:

KHALED-MASTER-PLAN.md

لتجاوز Failure.

أي تغيير في المواصفات الأساسية يجب أن يكون:

Explicit
Auditable
Reviewed


---

57. Generated Code Policy

أي كود يولده AI:

Generated
↓
Static Validation
↓
Compile
↓
Test
↓
Security
↓
Review

ولا يُعتبر صحيحًا لمجرد أن AI كتبه.


---

58. Performance

النظام يجب أن يكون:

خفيفًا.

Modular.

Lazy-loaded.

بدون Resident Daemon.

بدون اتصال AI دائم.

بدون Browser دائم.

بدون Polling دائم.



---

59. Token Efficiency

AI Context Engine يجب أن يستخدم:

Delta Context
Relevant Files
Error Context
Dependency Context
Requirement Context

ولا يرسل Repository كاملًا في كل مرة.


---

60. Context Budget

لكل Agent:

Maximum Context
Relevant Files
Relevant Logs
Relevant Requirements

ويُمنع إرسال بيانات غير ضرورية.


---

61. AI Failure Handling

إذا فشل AI:

AI_FAILURE

لا يتحول المشروع إلى:

PROJECT_FAILURE

إذا كانت المهمة قابلة للتنفيذ بدون AI.


---

62. Local AI

إذا توفر Local Model:

Local AI

يُستخدم دون إرسال أسرار أو ملفات غير ضرورية للخارج.


---

63. Free Provider

أي Free Provider يجب اعتباره:

Optional
Current availability must be verified
Rate limits must be respected

ولا يجوز افتراض أن Free Tier دائم أو غير محدود.


---

64. Browser AI

Browser Agent يجب أن يتبع:

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

وكل Action يجب أن يكون قابلاً للتسجيل.


---

65. Security Gate

كل عملية خطرة:

Risk Assessment
↓
Policy
↓
Execution Gate

وإذا كانت غير مسموحة:

BLOCK


---

66. External Services

لا يجوز للنظام الادعاء باستخدام:

Server.

Cloud AI.

Database.

Browser.

Autodesk installation.

External API.


إلا إذا كانت موجودة ومتصلة بالفعل.


---

67. Network Failure

إذا انقطع الإنترنت:

Offline-capable tasks continue

أما المهام التي تتطلب Internet:

BLOCKED_EXTERNAL_DEPENDENCY

ولا تسجل نجاحًا.


---

68. Autodesk SDK Failure

إذا لم تتوفر Autodesk SDK:

AUTODESK_BUILD_BLOCKED

ولا يجوز إنشاء Fake SDK ثم إعلان نجاح حقيقي.

يمكن استخدام:

Interfaces
Mocks
Stubs
Contract Tests

للتطوير، لكن يجب تمييزها بوضوح عن الاختبار الحقيقي.


---

69. Revit/AutoCAD Verification

الاختبار الحقيقي يحتاج:

Actual Autodesk Installation
+
Correct Version
+
Actual Add-in Loading
+
Actual Command
+
Actual Result

وإلا:

NOT_VERIFIED


---

70. Release Policy

Artifact النهائي يجب ألا يُنشأ كـ:

official release

إلا إذا اجتاز:

Release Gate


---

71. Release Evidence

يجب أن يحتوي Release Evidence على:

Commit
Build ID
OS
.NET Version
Build Result
Test Result
Verification Result
Artifact
SHA256
Compatibility Matrix
Security Result


---

72. Self-Check

قبل كل Run يجب تنفيذ:

Plan Integrity
Workflow Integrity
Script Integrity
Manifest Integrity
Repository Integrity


---

73. Workflow Safety

GitHub Actions يجب أن يستخدم:

Least Privilege Permissions

ولا يحصل على صلاحيات غير ضرورية.


---

74. Pull Request Safety

عند استخدام Pull Requests:

Build
Test
Security
Verification

قبل Merge.


---

75. Main Branch

لا يُسمح لـ AI بتعديل main مباشرة بشكل غير مقيد.

الأفضل:

AI Repair
↓
Patch
↓
Validation
↓
Artifact
↓
Controlled Commit/PR


---

76. Automatic Commit

لا يتم Commit تلقائيًا إلا إذا كان ذلك مفعّلًا صراحة.

الوضع الافتراضي:

NO_AUTOMATIC_COMMIT


---

77. Failed Repair Artifact

عند الفشل:

failure-report.json
repair-history.json
patch.diff
logs/

تبقى محفوظة.


---

78. Final State Machine

الحالات الرسمية:

INIT
PREFLIGHT
DISCOVER
BOOTSTRAP
PLAN
GENERATE
VALIDATE
BUILD
TEST
DIAGNOSE
REPAIR
REBUILD
RETEST
VERIFY
EVIDENCE
PUBLISH
SUCCESS
FAILED
BLOCKED
UNRESOLVED
ROLLBACK


---

79. قاعدة الانتقال

لا يمكن الانتقال إلى:

SUCCESS

إلا إذا:

Build = VERIFIED
Tests = VERIFIED
Verification = VERIFIED
Security = VERIFIED
Artifact = VERIFIED


---

80. قاعدة الفشل

إذا:

Build Failed

لا يتم Publish.

إذا:

Tests Failed

لا يتم Publish.

إذا:

Verification Failed

لا يتم Publish.

إذا:

Security Failed

لا يتم Publish.


---

81. النتيجة النهائية المطلوبة

المشروع النهائي يجب أن يكون قادرًا على تنفيذ:

GitHub Actions
        ↓
Validate Plan
        ↓
Preflight
        ↓
Discover
        ↓
Bootstrap
        ↓
Generate
        ↓
Build
        ↓
Test
        ↓
Diagnose
        ↓
AI/Deterministic Repair
        ↓
Rebuild
        ↓
Retest
        ↓
Security
        ↓
Verification
        ↓
Evidence
        ↓
Publish


---

82. شرط النجاح النهائي

لا يعتبر Gooddaygoobuy / KHALED مكتملًا إلا عندما يثبت فعليًا:

[✓] Workflow valid
[✓] Repository valid
[✓] Bootstrap works
[✓] KHALED builds
[✓] Tests execute
[✓] Diagnostics execute
[✓] Repair pipeline works
[✓] Rollback works
[✓] Security gates work
[✓] Evidence generated
[✓] Artifact generated
[✓] SHA256 generated
[✓] Verification passes

أما:

Revit 2016–2027
AutoCAD 2016–2027

فتظل كل نسخة:

NOT_VERIFIED

حتى يتم اختبارها فعليًا.


---

83. المبدأ الهندسي النهائي

لا يتم بناء النظام حول:

AI

بل حول:

Deterministic Engineering
+
Validation
+
Verification
+
Recovery
+
Optional AI

ولا يكون AI مصدر الحقيقة.

مصدر الحقيقة هو:

Compiler
Tests
Runtime
Security Checks
Artifacts
Hashes
Evidence
Actual Autodesk Tests


---

84. تعليمات التنفيذ للوكيل

عند بدء التنفيذ:

1. افحص Repository الحالي بالكامل.


2. اقرأ KHALED-MASTER-PLAN.md بالكامل.


3. لا تفترض وجود أي ملف غير موجود.


4. لا تحذف الملفات الموجودة.


5. لا تعلن نجاح أي مرحلة قبل إثباتها.


6. أنشئ Bootstrap.


7. أصلح Workflow.


8. أنشئ المشروع.


9. أنشئ الاختبارات.


10. نفذ Build.


11. نفذ Tests.


12. إذا فشل، استخدم الخطأ الحقيقي.


13. لا تستخدم إصلاحًا عشوائيًا.


14. لا تجعل AI إلزاميًا.


15. طبّق Security Gates.


16. نفذ Verification.


17. أنشئ Evidence.


18. أنشئ Artifact.


19. احسب SHA256.


20. كرر فقط عند وجود سبب تقني واضح.


21. لا تتجاوز حد الإصلاح.


22. لا تضعف الاختبارات.


23. لا تحذف Security.


24. لا تدّعي دعم Autodesk بدون اختبار فعلي.


25. لا تستخدم Codespaces كاعتماد أساسي.


26. لا تعتمد على API مدفوع.


27. لا تنشئ Resident Process.


28. لا تخترع نتائج.


29. عند وجود Blocker حقيقي، سجله كـ BLOCKED مع الدليل.


30. لا تحول BLOCKED إلى SUCCESS.




---

85. قاعدة التنفيذ الأخيرة

لا تحاول جعل GitHub يعطي علامة خضراء بأي طريقة.

الهدف هو:

GREEN
=
REAL BUILD
+
REAL TESTS
+
REAL VERIFICATION
+
REAL SECURITY
+
REAL EVIDENCE

وليس:

GREEN
=
إخفاء الخطأ


---

86. معيار الحقيقة

إذا لم يتم تنفيذ شيء فعليًا:

NOT_EXECUTED

إذا تم تنفيذه وفشل:

FAILED

إذا تعذر تنفيذه بسبب اعتماد خارجي:

BLOCKED

إذا تم تنفيذه ونجح وتم التحقق منه:

VERIFIED

هذه القاعدة إلزامية على KHALED وجميع الوكلاء والـ Workflow والـ Reports.


---

87. النتيجة المعمارية النهائية

KHALED
                       │
          ┌────────────┴────────────┐
          │                         │
     Lifecycle                 Verification
          │                         │
 Install / Verify             Evidence
 Status / Upgrade             SHA256
 Repair / Uninstall           Release
          │
          ▼
      Execution Gate
          │
    ┌─────┴─────┐
    │           │
Deterministic   AI
    │           │
    │      Local / Free
    │           │
    └─────┬─────┘
          │
      REVO AI Core
          │
    Adapter Router
          │
    ┌─────┴─────┐
    │           │
   Revit      AutoCAD
    │           │
 Version      Version
 Adapter      Adapter
    │           │
    └─────┬─────┘
          │
       Verify
          │
       Evidence

هذه الوثيقة هي مصدر المواصفات.

build.yml هو المشغل.

bootstrap/ هو منشئ المشروع.

scripts/ هي طبقة التنفيذ الحتمي.

KHALED هو محرك Lifecycle/Deployment.

REVO AI هو Runtime AI/Autodesk Layer.

AI مساعد اختياري وليس مصدر الحقيقة.

Evidence هو الدليل.

Verification هي بوابة النجاح.

لا يُعلن النجاح إلا بالدليل الفعلي.

writing{variant="document" id="58321" title="KHALED-MASTER-PLAN — خطة التنفيذ والإصلاح الجذري الشاملة"}

# KHALED-MASTER-PLAN
## خطة التنفيذ والإصلاح الجذري الشاملة لمشروع Gooddaygoobuy / KHALED / REVO AI

**الإصدار:** Final Execution Architecture  
**التاريخ:** 2026-09-06  
**الحالة:** Execution-Ready Specification  
**المبدأ الأساسي:** لا نجاح بدون دليل حقيقي قابل للتحقق.

---

# 1. الهدف

تحويل مستودع `Gooddaygoobuy-` من مجرد وثيقة مواصفات وWorkflow غير صالح إلى نظام برمجي حقيقي قابل للبناء والاختبار والتحقق والإصلاح الذاتي الآمن.

يجب أن يستطيع النظام:

1. قراءة `KHALED-MASTER-PLAN.md`.
2. فحص حالة المستودع والبيئة.
3. إنشاء البنية البرمجية الناقصة.
4. إنشاء KHALED Core.
5. إنشاء الاختبارات.
6. تنفيذ Build حقيقي.
7. تنفيذ Tests حقيقية.
8. اكتشاف الأخطاء الحقيقية.
9. تشخيص الأخطاء.
10. اقتراح إصلاحات آمنة.
11. تطبيق الإصلاحات المسموح بها فقط.
12. إعادة Build/Test.
13. التراجع عن الإصلاح الفاشل.
14. تنفيذ Verification مستقل.
15. إنشاء Evidence حقيقي.
16. إنشاء Artifacts.
17. عدم إعلان النجاح إلا إذا أثبتت الأدلة النجاح.
18. العمل بدون Codespaces.
19. عدم الاعتماد على AI مدفوع.
20. جعل AI اختياريًا وليس نقطة فشل أساسية.

---

# 2. قاعدة الحقيقة المطلقة

يُمنع على النظام وعلى أي Agent داخله:

- اختلاق نتائج.
- إعلان Build ناجحًا دون Exit Code ناجح.
- إعلان Tests ناجحة دون تشغيلها.
- إعلان دعم Revit/AutoCAD دون اختبار فعلي.
- إعلان EXE صالح دون وجوده والتحقق منه.
- الادعاء باستخدام خادم أو خدمة لم يتم استخدامها.
- الادعاء بإصلاح خطأ لم تتم إعادة اختباره.
- تحويل `NOT VERIFIED` إلى `VERIFIED` بدون Evidence.
- حذف الاختبارات لتجنب الفشل.
- تعطيل Security Controls لإجبار Build على النجاح.
- إخفاء Errors.
- استخدام بيانات أو مفاتيح سرية داخل Repository أو Logs.

كل نتيجة يجب أن تكون واحدة من:

```text
VERIFIED
FAILED
NOT_VERIFIED
NOT_APPLICABLE
BLOCKED
```

ولا توجد حالة خامسة تعني نجاحًا غير مثبت.

---

# 3. البنية الصحيحة للمستودع

يجب أن تصبح البنية تدريجيًا:

```text
Gooddaygoobuy-/
│
├── KHALED-MASTER-PLAN.md
│
├── bootstrap/
│   ├── bootstrap.sh
│   ├── manifest.json
│   └── schema/
│
├── scripts/
│   ├── validate-plan.sh
│   ├── bootstrap.sh
│   ├── discover.sh
│   ├── build.sh
│   ├── test.sh
│   ├── diagnose.sh
│   ├── verify.sh
│   ├── evidence.sh
│   └── publish.sh
│
├── src/
│   └── KHALED/
│       ├── KHALED.csproj
│       ├── Program.cs
│       │
│       ├── Core/
│       ├── AI/
│       ├── Browser/
│       ├── Execution/
│       ├── Validation/
│       ├── Verification/
│       ├── Recovery/
│       ├── Security/
│       └── Autodesk/
│
├── tests/
│   ├── Unit/
│   ├── Integration/
│   ├── Security/
│   ├── Recovery/
│   ├── Repair/
│   ├── Browser/
│   └── Compatibility/
│
├── ai/
│   ├── agents/
│   ├── providers/
│   ├── prompts/
│   └── orchestrator/
│
├── browser/
│   ├── abstractions/
│   ├── playwright/
│   ├── playwright-mcp/
│   └── agent-browser/
│
├── Autodesk/
│   ├── Revit/
│   └── AutoCAD/
│
├── artifacts/
│
├── docs/
│
└── .github/
    └── workflows/
        └── build.yml
```

لا يجب إنشاء جميع الملفات دفعة واحدة بلا تحقق.

يجب إنشاؤها على مراحل، وكل مرحلة يجب أن تمر بالتحقق قبل الانتقال إلى المرحلة التالية.

---

# 4. مبدأ Bootstrap

الـ Workflow يجب ألا يفترض أن المشروع موجود.

عند البداية:

```text
CHECKOUT
↓
VALIDATE PLAN
↓
PREFLIGHT
↓
DISCOVER
↓
BOOTSTRAP
```

يجب أن يكتشف:

- هل الخطة موجودة؟
- هل الخطة فارغة؟
- هل Repository صالح؟
- هل Git متاح؟
- هل .NET متاح؟
- ما إصدار .NET؟
- هل توجد Solution؟
- هل توجد Projects؟
- هل توجد Tests؟
- هل توجد Scripts؟
- هل توجد ملفات KHALED؟
- هل توجد تغييرات يدوية؟
- هل توجد ملفات مجهولة؟
- هل توجد أسرار مكشوفة؟

---

# 5. عدم تدمير العمل الموجود

Bootstrap يجب أن يكون Idempotent.

أي:

```text
تشغيل أول
→ إنشاء الناقص

تشغيل ثاني
→ لا يعيد إنشاء الموجود بلا سبب

تشغيل ثالث
→ لا يحذف العمل السابق
```

يجب عدم استخدام:

```text
delete everything
recreate everything
```

إلا في بيئة اختبار صريحة.

كل ملف يتم إنشاؤه أو تعديله يجب أن يكون معروفًا في Manifest.

---

# 6. Manifest

يجب إنشاء:

```text
bootstrap/manifest.json
```

ليحتوي على:

- إصدار الخطة.
- إصدار Schema.
- الملفات المنشأة.
- الملفات المعدلة.
- الملفات المتحقق منها.
- Build state.
- Test state.
- Repair attempts.
- Verification state.
- Artifact hashes.
- آخر Failure Fingerprints.

مثال:

```json
{
  "schemaVersion": 1,
  "project": "Gooddaygoobuy",
  "engine": "KHALED",
  "plan": "KHALED-MASTER-PLAN.md",
  "build": "NOT_VERIFIED",
  "tests": "NOT_VERIFIED",
  "verification": "NOT_VERIFIED",
  "repairAttempts": 0
}
```

---

# 7. KHALED Core

KHALED هو Deployment/Lifecycle Engine وليس Resident Runtime.

الأوامر الأساسية:

```text
install
verify
status
upgrade
repair
uninstall
```

Pipeline:

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
Risk
↓
Execution Gate
↓
Execute
↓
Verify
↓
Evidence
↓
Recovery/Rollback
↓
Exit
```

---

# 8. KHALED يجب ألا يكون Resident

يُمنع:

- Windows Service دائم.
- Startup Entry.
- Tray Process.
- Daemon.
- Permanent Background Process.
- Permanent Socket.
- Polling Loop دائم.
- Permanent AI Connection.
- Deployment Monitor دائم.
- Resident Installer.

KHALED يعمل فقط عند طلب:

```text
install
verify
status
upgrade
repair
uninstall
```

ثم ينتهي.

---

# 9. REVO AI

REVO AI هو Runtime Add-in/AI Integration Architecture.

يجب فصل:

```text
KHALED
```

عن:

```text
REVO AI
```

بحيث:

```text
KHALED
=
Deployment / Lifecycle / Recovery

REVO AI
=
Runtime Autodesk Add-in
```

---

# 10. REVO AI Core

المكونات:

```text
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
```

Pipeline:

```text
User Intent
↓
Intent Engine
↓
Context
↓
Planning
↓
Normalization
↓
Validation
↓
Policy
↓
Risk
↓
Execution Gate
↓
Adapter Router
↓
Autodesk Execution
↓
Verification
↓
Evidence
```

---

# 11. AI Architecture

AI ليس شرطًا لتشغيل KHALED.

يجب تعريف:

```text
IAIProvider
```

ثم:

```text
DisabledAIProvider
LocalAIProvider
OptionalFreeProvider
```

الترتيب:

```text
Deterministic Logic
↓
Local Open-Source AI
↓
Configured Free Provider
↓
No AI
```

إذا لم يوجد AI:

```text
النظام لا يتوقف لمجرد عدم وجود AI.
```

---

# 12. Multi-Agent Architecture

الوكلاء:

```text
PlannerAgent
ResearchAgent
CodingAgent
BuildAgent
TestAgent
DebugAgent
RepairAgent
BrowserAgent
SecurityAgent
VerificationAgent
ReviewerAgent
```

لكن لا يسمح لأي Agent بالعمل خارج صلاحياته.

---

# 13. فصل التخطيط عن التنفيذ

AI يستطيع:

```text
Observe
Analyze
Plan
Propose
```

لكن لا ينفذ مباشرة.

يجب أن يمر كل تنفيذ عبر:

```text
Policy Engine
↓
Risk Engine
↓
Execution Gate
```

ثم:

```text
Execute
```

---

# 14. نظام إصلاح الأخطاء

عند Build Failure:

```text
BUILD
↓
CAPTURE ERROR
↓
SANITIZE
↓
FINGERPRINT
↓
CLASSIFY
↓
COLLECT CONTEXT
↓
DIAGNOSE
↓
GENERATE PATCH
↓
VALIDATE PATCH
↓
SECURITY CHECK
↓
EXECUTION GATE
↓
APPLY PATCH
↓
BUILD
↓
TEST
↓
VERIFY
```

إذا نجح:

```text
REPAIR VERIFIED
```

إذا فشل:

```text
ROLLBACK
```

ثم محاولة أخرى محدودة.

---

# 15. الحد الأقصى للإصلاح

الافتراضي:

```text
MAX_ATTEMPTS_PER_FAILURE_CLASS = 5
```

بعد 5 محاولات:

```text
UNRESOLVED
```

ويجب التوقف بدل الدخول في Loop لا نهائي.

---

# 16. Error Fingerprint

يجب إنشاء بصمة للخطأ تعتمد على:

```text
Error Type
Error Code
Compiler
File
Line
Column
Relevant Stack
Target Framework
OS
Project
Stage
```

بحيث يعرف النظام أن:

```text
CS1002
```

هو نفس Failure Class حتى لو اختلفت بعض تفاصيل Log.

---

# 17. Patch Safety

كل Patch يجب أن يمر عبر:

```text
Syntax Validation
↓
Path Validation
↓
Diff Validation
↓
Secret Scan
↓
Dangerous Operation Scan
↓
Scope Check
↓
Execution Gate
```

ويُرفض إذا:

- خارج Workspace.
- يحذف ملفات غير مصرح بها.
- يغير Security Policy.
- يزيل Tests.
- يضيف Secrets.
- ينفذ أمرًا خطيرًا.
- يغير ملفات غير مرتبطة بالمشكلة.

---

# 18. Command Allowlist

AI لا يستطيع تشغيل أوامر عشوائية.

يجب وجود:

```text
CommandAllowlist
```

و:

```text
PathAllowlist
```

و:

```text
EnvironmentAllowlist
```

أي Command غير معروف:

```text
REJECTED
```

---

# 19. Secret Protection

يجب فحص:

```text
GitHub Secrets
Environment Variables
Logs
AI prompts
Artifacts
Source Code
```

ويجب إزالة:

```text
API Keys
Tokens
Passwords
Private Keys
Credentials
Cookies
Session Tokens
```

من Logs وEvidence.

---

# 20. Build Engine

Build Engine يجب أن يكتشف المشروع بدل افتراضه.

يبحث عن:

```text
*.sln
*.slnx
*.csproj
```

ثم:

```text
Discover
↓
Restore
↓
Build
↓
Test
↓
Publish
```

لا يجوز افتراض Output Path ثابت.

---

# 21. Test Engine

يكتشف مشاريع الاختبار تلقائيًا.

يجب تشغيل:

```text
Unit Tests
Integration Tests
Security Tests
Recovery Tests
Repair Tests
Configuration Tests
```

إذا لم توجد Tests:

```text
TESTS_NOT_AVAILABLE
```

ولا تسجل:

```text
TESTS_PASSED
```

---

# 22. اختبارات الفشل

يجب اختبار النظام ضد:

```text
Invalid YAML
Missing Project
Broken Project
Compilation Error
Test Failure
Invalid Patch
Unauthorized Path
Secret Leakage
Failed Repair
Rollback Failure
Missing Artifact
Corrupt Artifact
Unsupported Autodesk Version
Missing SDK
```

---

# 23. Recovery Engine

عند فشل Patch:

```text
Restore Previous State
↓
Verify Repository
↓
Rebuild
↓
Retest
```

إذا فشل Recovery:

```text
RECOVERY_FAILED
```

ولا يواصل النظام تعديلات عشوائية.

---

# 24. Verification Engine

Verification مستقل عن Build.

يتحقق من:

```text
Project Exists
↓
Compilation
↓
Tests
↓
Expected Files
↓
Artifact Exists
↓
Artifact Integrity
↓
Hash
↓
Runtime Smoke Test
↓
Security
```

---

# 25. Evidence Engine

كل Run يجب أن ينتج:

```text
artifacts/evidence/
```

ويتضمن:

```text
build.json
tests.json
verification.json
environment.json
failure-report.json
repair-history.json
SHA256SUMS.txt
```

كل Evidence يجب أن يحتوي:

```text
Timestamp
Commit
Workflow Run
Stage
Input
Action
Result
Exit Code
Evidence
```

---

# 26. Artifact Integrity

كل Artifact يتم حساب:

```text
SHA-256
```

ويُحفظ في:

```text
SHA256SUMS.txt
```

لا يكفي وجود EXE.

يجب التحقق من:

```text
Exists
Readable
Expected Format
Expected Size > 0
Hash Generated
```

---

# 27. GitHub Actions

`build.yml` يجب أن يكون Workflow حقيقيًا.

لا يجب أن يحتوي على مخطط نصي مثل:

```text
KHALED-MASTER-PLAN.md
↓
Build
↓
Test
```

بل يجب أن يحتوي على:

```yaml
name:
on:
permissions:
jobs:
steps:
```

ويستدعي Scripts التنفيذ الفعلية.

---

# 28. Codespaces

Codespaces ليس Dependency.

إذا انتهى رصيد Codespaces:

```text
النظام يستمر عبر GitHub Actions
```

ولا يتوقف المشروع بالكامل.

---

# 29. GitHub Actions Quota

يجب تقليل الاستهلاك عبر:

- عدم تشغيل AI عند عدم الحاجة.
- عدم تكرار Build بلا سبب.
- Caching للـ .NET.
- إصلاح Failure Class بدل إعادة نفس العملية.
- Bounded retries.
- عدم تشغيل Browser Tests إلا عند الحاجة.
- عدم إعادة الاختبارات التي لم تتأثر بالتغيير إلا إذا كانت Integration/Critical.

---

# 30. AI Repair بدون تكلفة إجبارية

إذا لم توجد:

```text
API Key
```

يجب أن يعمل:

```text
Deterministic Diagnostics
```

وإذا توفر Local AI:

```text
Local AI
```

وإذا تم تكوين Free Provider:

```text
Free Provider
```

لكن لا يوجد:

```text
Mandatory Paid API
```

---

# 31. Browser Engine

تعريف:

```text
IBrowserEngine
```

مع Implementations:

```text
Playwright
Playwright MCP
agent-browser
```

الأولوية:

```text
DOM
↓
Accessibility Tree
↓
Semantic Interaction
↓
Screenshot/Vision
```

الرؤية تستخدم عند الحاجة فقط.

---

# 32. Browser Safety

Browser Agent ممنوع من:

- تجاوز CAPTCHA.
- تجاوز Authentication.
- تجاوز Security Controls.
- سرقة Credentials.
- استخراج Session Tokens.
- تنفيذ أعمال غير مصرح بها.

يجب تسجيل:

```text
Intent
Observed State
Action
Expected Result
Actual Result
Verification
```

---

# 33. Autodesk Architecture

يجب تعريف:

```text
IAutodeskAdapter
```

ثم:

```text
RevitAdapter
AutoCADAdapter
```

مع Version/Capability routing.

---

# 34. Revit

الهدف المعماري:

```text
Revit 2016
Revit 2017
...
Revit 2027
```

لكن:

**لا يُعلن أي إصدار VERIFIED قبل اختباره فعليًا.**

الحالة الأولية:

```text
NOT_VERIFIED
```

حتى توجد بيئة فعلية ودليل.

---

# 35. AutoCAD

الهدف:

```text
AutoCAD 2016
AutoCAD 2017
...
AutoCAD 2027
```

نفس القاعدة:

```text
لا دعم مثبت بدون اختبار حقيقي.
```

---

# 36. Autodesk Compatibility Matrix

يجب إنشاء:

```text
compatibility-matrix.json
```

مثال:

```json
{
  "revit": {
    "2016": "NOT_VERIFIED",
    "2017": "NOT_VERIFIED",
    "2018": "NOT_VERIFIED",
    "2019": "NOT_VERIFIED",
    "2020": "NOT_VERIFIED",
    "2021": "NOT_VERIFIED",
    "2022": "NOT_VERIFIED",
    "2023": "NOT_VERIFIED",
    "2024": "NOT_VERIFIED",
    "2025": "NOT_VERIFIED",
    "2026": "NOT_VERIFIED",
    "2027": "NOT_VERIFIED"
  },
  "autocad": {
    "2016": "NOT_VERIFIED",
    "2017": "NOT_VERIFIED",
    "2018": "NOT_VERIFIED",
    "2019": "NOT_VERIFIED",
    "2020": "NOT_VERIFIED",
    "2021": "NOT_VERIFIED",
    "2022": "NOT_VERIFIED",
    "2023": "NOT_VERIFIED",
    "2024": "NOT_VERIFIED",
    "2025": "NOT_VERIFIED",
    "2026": "NOT_VERIFIED",
    "2027": "NOT_VERIFIED"
  }
}
```

---

# 37. Capability System

بدل الاعتماد فقط على Version:

```text
Application
+
Version
+
Capability
```

مثال:

```text
Revit
2024
ExternalCommand
```

ثم:

```text
AdapterRouter
```

يحدد Adapter الصحيح.

---

# 38. Universal Contract

يجب أن يكون هناك Contract ثابت بين:

```text
REVO AI Core
```

و:

```text
Autodesk Adapters
```

يتضمن:

```text
Request
Context
Capability
Command
Risk
Execution
Result
Verification
Evidence
Error
```

---

# 39. Configuration

يجب ألا تكون الإعدادات موزعة داخل الكود.

تعريف:

```text
ConfigurationProvider
```

يدعم:

```text
Environment
Config File
CLI
Defaults
```

مع أولوية واضحة.

---

# 40. Logging

يجب أن يكون Logging:

```text
Structured
Machine-readable
Human-readable
Redacted
Timestamped
```

ويمنع تسجيل الأسرار.

---

# 41. CLI

يجب توفير:

```text
khaled install
khaled verify
khaled status
khaled upgrade
khaled repair
khaled uninstall
```

ويجب أن تكون Exit Codes محددة.

مثال:

```text
0 = SUCCESS
1 = GENERAL_FAILURE
2 = INVALID_ARGUMENT
3 = VALIDATION_FAILURE
4 = BUILD_FAILURE
5 = TEST_FAILURE
6 = VERIFICATION_FAILURE
7 = REPAIR_EXHAUSTED
8 = SECURITY_BLOCK
9 = RECOVERY_FAILURE
```

---

# 42. Transactional Installation

Installation:

```text
Preflight
↓
Backup
↓
Stage
↓
Validate
↓
Commit
↓
Verify
```

إذا فشل قبل Commit:

```text
Rollback
```

---

# 43. Upgrade

Upgrade:

```text
Discover
↓
Compare
↓
Backup
↓
Stage
↓
Validate
↓
Apply
↓
Verify
```

إذا فشل:

```text
Rollback
```

---

# 44. Uninstall

Uninstall يجب ألا يحذف ملفات غير مملوكة لـ KHALED.

يجب الاعتماد على:

```text
Ownership Manifest
```

ولا يجوز:

```text
Delete unknown files
```

---

# 45. Status

`status` يجب أن يكون Read-Only قدر الإمكان.

يعرض:

```text
Installed
Version
Components
Integrity
Last Verification
AI Provider
Browser Provider
Autodesk Adapters
Failures
```

---

# 46. Repository Integrity

قبل أي Repair:

```text
Git Status
↓
Tracked Files
↓
Manifest
↓
Allowed Scope
```

يجب ألا يلمس AI ملفات خارج النطاق.

---

# 47. Plan Validation

قبل Bootstrap يجب تحليل:

```text
KHALED-MASTER-PLAN.md
```

لكن لا يجب أن يعتمد التنفيذ على فهم حر للغة الطبيعية فقط.

يجب استخراج:

```text
Requirements
Modules
Commands
Constraints
Target Platforms
Verification Rules
Security Rules
```

ثم تحويلها إلى Machine-readable requirements.

---

# 48. Requirement Registry

إنشاء:

```text
requirements.json
```

مثال:

```json
{
  "id": "KHALED-001",
  "description": "No resident daemon",
  "category": "architecture",
  "mandatory": true,
  "verification": "static"
}
```

كل Requirement يجب أن يمتلك:

```text
ID
Description
Priority
Verification Method
Status
Evidence
```

---

# 49. Traceability

يجب أن نستطيع تتبع:

```text
Requirement
↓
Implementation
↓
Test
↓
Verification
↓
Evidence
```

مثال:

```text
KHALED-001
↓
ResidentProcessGuard
↓
SecurityTest
↓
Verification
↓
evidence.json
```

---

# 50. Reviewer Agent

ReviewerAgent لا ينفذ.

دوره:

```text
Review Plan
Review Code
Review Patch
Review Tests
Review Evidence
```

ويستطيع رفض:

```text
False Success
Unsafe Patch
Missing Test
Missing Evidence
Scope Violation
```

---

# 51. Final Gate

قبل إعلان:

```text
SUCCESS
```

يجب أن تمر:

```text
Build
AND
Tests
AND
Security
AND
Verification
AND
Artifacts
AND
Evidence
```

إذا فشل أي شرط:

```text
FAILED
```

---

# 52. لا يوجد "Success by Hope"

العبارات التالية ممنوعة:

```text
probably works
should work
looks correct
assumed compatible
AI says fixed
build expected to pass
```

داخل Evidence.

يجب استخدام نتائج فعلية فقط.

---

# 53. مراحل التنفيذ

## Phase 0 — Repository Recovery

- فحص Git.
- فحص الملفات.
- فحص Workflow.
- حفظ الحالة الحالية.
- عدم حذف أي عمل.

الحالة:

```text
RECOVERED
```

---

## Phase 1 — Workflow Repair

استبدال `build.yml` غير الصالح بـ Workflow حقيقي.

الهدف:

```text
GitHub Actions starts successfully
```

---

## Phase 2 — Bootstrap

إنشاء:

```text
bootstrap/
scripts/
src/
tests/
```

مع المحافظة على الملفات الموجودة.

---

## Phase 3 — KHALED Core

إنشاء:

```text
CLI
Lifecycle
Execution
Policy
Risk
Validation
Verification
Recovery
Security
```

---

## Phase 4 — Deterministic Build

تحقيق:

```text
Restore
Build
Test
Publish
Evidence
```

بدون AI.

---

## Phase 5 — Diagnostics

إضافة:

```text
Error Parser
Fingerprint
Classifier
Context Collector
```

---

## Phase 6 — Repair Engine

إضافة:

```text
Repair Planner
Patch Validator
Execution Gate
Rollback
Retry
```

---

## Phase 7 — AI Layer

إضافة:

```text
IAIProvider
DisabledAIProvider
Local Provider
Optional Free Provider
Agents
```

---

## Phase 8 — Browser

إضافة:

```text
IBrowserEngine
Playwright
Playwright MCP
agent-browser
```

مع Safety Layer.

---

## Phase 9 — Autodesk

إضافة:

```text
IAutodeskAdapter
RevitAdapter
AutoCADAdapter
Capability Router
Compatibility Matrix
```

---

## Phase 10 — Testing

إضافة:

```text
Unit
Integration
Security
Recovery
Repair
Browser
Compatibility
```

---

## Phase 11 — Verification

إضافة:

```text
Independent Verification
Evidence
Hashes
Artifact Validation
```

---

## Phase 12 — Final Release

فقط بعد اجتياز جميع Gates:

```text
Build
Test
Verify
Security
Evidence
Artifact
```

---

# 54. Recovery من GitHub Actions Failure

إذا فشل Workflow:

1. اقرأ Error الحقيقي.
2. لا تخمن.
3. حدد Stage.
4. استخرج Error Fingerprint.
5. افحص الملفات المتعلقة.
6. أصلح السبب الجذري.
7. تحقق من Patch.
8. أعد Build.
9. أعد Tests.
10. تحقق.
11. احتفظ بالدليل.

---

# 55. لا تستخدم Retry أعمى

ممنوع:

```text
Run again
Run again
Run again
```

بدون تغيير السبب.

كل Retry يجب أن يكون مرتبطًا بـ:

```text
New Diagnosis
+
New Validated Change
```

---

# 56. عدم تغيير الخطة تلقائيًا

AI لا يجوز له إعادة كتابة:

```text
KHALED-MASTER-PLAN.md
```

لتجاوز Failure.

أي تغيير في المواصفات الأساسية يجب أن يكون:

```text
Explicit
Auditable
Reviewed
```

---

# 57. Generated Code Policy

أي كود يولده AI:

```text
Generated
↓
Static Validation
↓
Compile
↓
Test
↓
Security
↓
Review
```

ولا يُعتبر صحيحًا لمجرد أن AI كتبه.

---

# 58. Performance

النظام يجب أن يكون:

- خفيفًا.
- Modular.
- Lazy-loaded.
- بدون Resident Daemon.
- بدون اتصال AI دائم.
- بدون Browser دائم.
- بدون Polling دائم.

---

# 59. Token Efficiency

AI Context Engine يجب أن يستخدم:

```text
Delta Context
Relevant Files
Error Context
Dependency Context
Requirement Context
```

ولا يرسل Repository كاملًا في كل مرة.

---

# 60. Context Budget

لكل Agent:

```text
Maximum Context
Relevant Files
Relevant Logs
Relevant Requirements
```

ويُمنع إرسال بيانات غير ضرورية.

---

# 61. AI Failure Handling

إذا فشل AI:

```text
AI_FAILURE
```

لا يتحول المشروع إلى:

```text
PROJECT_FAILURE
```

إذا كانت المهمة قابلة للتنفيذ بدون AI.

---

# 62. Local AI

إذا توفر Local Model:

```text
Local AI
```

يُستخدم دون إرسال أسرار أو ملفات غير ضرورية للخارج.

---

# 63. Free Provider

أي Free Provider يجب اعتباره:

```text
Optional
Current availability must be verified
Rate limits must be respected
```

ولا يجوز افتراض أن Free Tier دائم أو غير محدود.

---

# 64. Browser AI

Browser Agent يجب أن يتبع:

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

وكل Action يجب أن يكون قابلاً للتسجيل.

---

# 65. Security Gate

كل عملية خطرة:

```text
Risk Assessment
↓
Policy
↓
Execution Gate
```

وإذا كانت غير مسموحة:

```text
BLOCK
```

---

# 66. External Services

لا يجوز للنظام الادعاء باستخدام:

- Server.
- Cloud AI.
- Database.
- Browser.
- Autodesk installation.
- External API.

إلا إذا كانت موجودة ومتصلة بالفعل.

---

# 67. Network Failure

إذا انقطع الإنترنت:

```text
Offline-capable tasks continue
```

أما المهام التي تتطلب Internet:

```text
BLOCKED_EXTERNAL_DEPENDENCY
```

ولا تسجل نجاحًا.

---

# 68. Autodesk SDK Failure

إذا لم تتوفر Autodesk SDK:

```text
AUTODESK_BUILD_BLOCKED
```

ولا يجوز إنشاء Fake SDK ثم إعلان نجاح حقيقي.

يمكن استخدام:

```text
Interfaces
Mocks
Stubs
Contract Tests
```

للتطوير، لكن يجب تمييزها بوضوح عن الاختبار الحقيقي.

---

# 69. Revit/AutoCAD Verification

الاختبار الحقيقي يحتاج:

```text
Actual Autodesk Installation
+
Correct Version
+
Actual Add-in Loading
+
Actual Command
+
Actual Result
```

وإلا:

```text
NOT_VERIFIED
```

---

# 70. Release Policy

Artifact النهائي يجب ألا يُنشأ كـ:

```text
official release
```

إلا إذا اجتاز:

```text
Release Gate
```

---

# 71. Release Evidence

يجب أن يحتوي Release Evidence على:

```text
Commit
Build ID
OS
.NET Version
Build Result
Test Result
Verification Result
Artifact
SHA256
Compatibility Matrix
Security Result
```

---

# 72. Self-Check

قبل كل Run يجب تنفيذ:

```text
Plan Integrity
Workflow Integrity
Script Integrity
Manifest Integrity
Repository Integrity
```

---

# 73. Workflow Safety

GitHub Actions يجب أن يستخدم:

```text
Least Privilege Permissions
```

ولا يحصل على صلاحيات غير ضرورية.

---

# 74. Pull Request Safety

عند استخدام Pull Requests:

```text
Build
Test
Security
Verification
```

قبل Merge.

---

# 75. Main Branch

لا يُسمح لـ AI بتعديل `main` مباشرة بشكل غير مقيد.

الأفضل:

```text
AI Repair
↓
Patch
↓
Validation
↓
Artifact
↓
Controlled Commit/PR
```

---

# 76. Automatic Commit

لا يتم Commit تلقائيًا إلا إذا كان ذلك مفعّلًا صراحة.

الوضع الافتراضي:

```text
NO_AUTOMATIC_COMMIT
```

---

# 77. Failed Repair Artifact

عند الفشل:

```text
failure-report.json
repair-history.json
patch.diff
logs/
```

تبقى محفوظة.

---

# 78. Final State Machine

الحالات الرسمية:

```text
INIT
PREFLIGHT
DISCOVER
BOOTSTRAP
PLAN
GENERATE
VALIDATE
BUILD
TEST
DIAGNOSE
REPAIR
REBUILD
RETEST
VERIFY
EVIDENCE
PUBLISH
SUCCESS
FAILED
BLOCKED
UNRESOLVED
ROLLBACK
```

---

# 79. قاعدة الانتقال

لا يمكن الانتقال إلى:

```text
SUCCESS
```

إلا إذا:

```text
Build = VERIFIED
Tests = VERIFIED
Verification = VERIFIED
Security = VERIFIED
Artifact = VERIFIED
```

---

# 80. قاعدة الفشل

إذا:

```text
Build Failed
```

لا يتم Publish.

إذا:

```text
Tests Failed
```

لا يتم Publish.

إذا:

```text
Verification Failed
```

لا يتم Publish.

إذا:

```text
Security Failed
```

لا يتم Publish.

---

# 81. النتيجة النهائية المطلوبة

المشروع النهائي يجب أن يكون قادرًا على تنفيذ:

```text
GitHub Actions
        ↓
Validate Plan
        ↓
Preflight
        ↓
Discover
        ↓
Bootstrap
        ↓
Generate
        ↓
Build
        ↓
Test
        ↓
Diagnose
        ↓
AI/Deterministic Repair
        ↓
Rebuild
        ↓
Retest
        ↓
Security
        ↓
Verification
        ↓
Evidence
        ↓
Publish
```

---

# 82. شرط النجاح النهائي

لا يعتبر Gooddaygoobuy / KHALED مكتملًا إلا عندما يثبت فعليًا:

```text
[✓] Workflow valid
[✓] Repository valid
[✓] Bootstrap works
[✓] KHALED builds
[✓] Tests execute
[✓] Diagnostics execute
[✓] Repair pipeline works
[✓] Rollback works
[✓] Security gates work
[✓] Evidence generated
[✓] Artifact generated
[✓] SHA256 generated
[✓] Verification passes
```

أما:

```text
Revit 2016–2027
AutoCAD 2016–2027
```

فتظل كل نسخة:

```text
NOT_VERIFIED
```

حتى يتم اختبارها فعليًا.

---

# 83. المبدأ الهندسي النهائي

لا يتم بناء النظام حول:

```text
AI
```

بل حول:

```text
Deterministic Engineering
+
Validation
+
Verification
+
Recovery
+
Optional AI
```

ولا يكون AI مصدر الحقيقة.

مصدر الحقيقة هو:

```text
Compiler
Tests
Runtime
Security Checks
Artifacts
Hashes
Evidence
Actual Autodesk Tests
```

---

# 84. تعليمات التنفيذ للوكيل

عند بدء التنفيذ:

1. افحص Repository الحالي بالكامل.
2. اقرأ `KHALED-MASTER-PLAN.md` بالكامل.
3. لا تفترض وجود أي ملف غير موجود.
4. لا تحذف الملفات الموجودة.
5. لا تعلن نجاح أي مرحلة قبل إثباتها.
6. أنشئ Bootstrap.
7. أصلح Workflow.
8. أنشئ المشروع.
9. أنشئ الاختبارات.
10. نفذ Build.
11. نفذ Tests.
12. إذا فشل، استخدم الخطأ الحقيقي.
13. لا تستخدم إصلاحًا عشوائيًا.
14. لا تجعل AI إلزاميًا.
15. طبّق Security Gates.
16. نفذ Verification.
17. أنشئ Evidence.
18. أنشئ Artifact.
19. احسب SHA256.
20. كرر فقط عند وجود سبب تقني واضح.
21. لا تتجاوز حد الإصلاح.
22. لا تضعف الاختبارات.
23. لا تحذف Security.
24. لا تدّعي دعم Autodesk بدون اختبار فعلي.
25. لا تستخدم Codespaces كاعتماد أساسي.
26. لا تعتمد على API مدفوع.
27. لا تنشئ Resident Process.
28. لا تخترع نتائج.
29. عند وجود Blocker حقيقي، سجله كـ `BLOCKED` مع الدليل.
30. لا تحول `BLOCKED` إلى `SUCCESS`.

---

# 85. قاعدة التنفيذ الأخيرة

**لا تحاول جعل GitHub يعطي علامة خضراء بأي طريقة.**

الهدف هو:

```text
GREEN
=
REAL BUILD
+
REAL TESTS
+
REAL VERIFICATION
+
REAL SECURITY
+
REAL EVIDENCE
```

وليس:

```text
GREEN
=
إخفاء الخطأ
```

---

# 86. معيار الحقيقة

إذا لم يتم تنفيذ شيء فعليًا:

```text
NOT_EXECUTED
```

إذا تم تنفيذه وفشل:

```text
FAILED
```

إذا تعذر تنفيذه بسبب اعتماد خارجي:

```text
BLOCKED
```

إذا تم تنفيذه ونجح وتم التحقق منه:

```text
VERIFIED
```

هذه القاعدة إلزامية على KHALED وجميع الوكلاء والـ Workflow والـ Reports.

---

# 87. النتيجة المعمارية النهائية

```text
                    KHALED
                       │
          ┌────────────┴────────────┐
          │                         │
     Lifecycle                 Verification
          │                         │
 Install / Verify             Evidence
 Status / Upgrade             SHA256
 Repair / Uninstall           Release
          │
          ▼
      Execution Gate
          │
    ┌─────┴─────┐
    │           │
Deterministic   AI
    │           │
    │      Local / Free
    │           │
    └─────┬─────┘
          │
      REVO AI Core
          │
    Adapter Router
          │
    ┌─────┴─────┐
    │           │
   Revit      AutoCAD
    │           │
 Version      Version
 Adapter      Adapter
    │           │
    └─────┬─────┘
          │
       Verify
          │
       Evidence
```

**هذه الوثيقة هي مصدر المواصفات.**

`build.yml` هو المشغل.

`bootstrap/` هو منشئ المشروع.

`scripts/` هي طبقة التنفيذ الحتمي.

`KHALED` هو محرك Lifecycle/Deployment.

`REVO AI` هو Runtime AI/Autodesk Layer.

`AI` مساعد اختياري وليس مصدر الحقيقة.

`Evidence` هو الدليل.

`Verification` هي بوابة النجاح.

**لا يُعلن النجاح إلا بالدليل الفعلي.**
