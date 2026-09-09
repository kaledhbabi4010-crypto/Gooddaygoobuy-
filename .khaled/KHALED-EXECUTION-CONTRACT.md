# KHALED X — EXECUTION CONTRACT

KHALED never treats AI text as proof.

## Real success requires

1. Gradle build exit code = 0
2. Unit test exit code = 0
3. APK exists
4. APK SHA256 exists
5. verified.txt contains:
   KHALED_VERIFIED_BUILD=true

## Repair cycle

REAL BUILD
   ↓
REAL TEST
   ↓
REAL FAILURE LOG
   ↓
GEMINI
   ↓
SAFE SOURCE PATCH
   ↓
DIFF CHECK
   ↓
COMMIT
   ↓
PUSH
   ↓
BUILD AGAIN

Maximum rounds are bounded.

## Secrets

The workflow references only:

secrets.GEMINI_API_KEY
secrets.BROWSERSTACK_USERNAME
secrets.BROWSERSTACK_ACCESS_KEY

Values are never written to repository files.

## Protected infrastructure

AI cannot modify:

.git/
.github/
.khaled/

## Truth rule

No verified evidence = no success.
