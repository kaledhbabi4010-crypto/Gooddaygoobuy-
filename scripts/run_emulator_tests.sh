#!/usr/bin/env bash
set -u

mkdir -p evidence
ADB="${ANDROID_HOME:-/usr/local/lib/android/sdk}/platform-tools/adb"

echo "DEVICE"
"$ADB" devices || true

echo "BOOT"
B=""
for i in $(seq 1 60); do
  B=$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
  [ "$B" = "1" ] && break
  sleep 5
done

if [ "$B" != "1" ]; then
  echo "BOOT: FAIL"
  "$ADB" shell getprop > evidence/getprop.txt 2>&1 || true
  "$ADB" logcat -d > evidence/logcat.txt 2>&1 || true
  exit 1
fi

echo "BOOT: PASS"

# Wait for Package Manager service readiness
echo "PM WAITING"
PM_READY=0
for i in $(seq 1 30); do
  if "$ADB" shell pm path android >/dev/null 2>&1; then
    PM_READY=1
    break
  fi
  sleep 3
done

if [ "$PM_READY" -ne 1 ]; then
  echo "PM SERVICE NOT READY"
  exit 1
fi
echo "PM SERVICE READY"

# Disable verification settings to prevent INSTALL_FAILED_VERIFICATION_FAILURE
"$ADB" shell settings put global package_verifier_enable 0 || true
"$ADB" shell settings put global verifier_verify_adb_installs 0 || true
"$ADB" shell settings put global upload_apk_enable 0 || true
"$ADB" shell settings put secure package_verifier_user_consent -1 || true

for ITEM in android_app khaled_android; do
  APK="${GITHUB_WORKSPACE:-$(pwd)}/$ITEM/app/build/outputs/apk/debug/app-debug.apk"
  if [ ! -f "$APK" ]; then
    echo "APK: FAIL $ITEM"
    exit 1
  fi

  AAPT_BIN=""
  if [ -d "${ANDROID_HOME:-}/build-tools" ]; then
    AAPT_BIN="$(find "${ANDROID_HOME}/build-tools" -type f -name aapt 2>/dev/null | sort -V | tail -1 || true)"
  fi

  PKG=""
  if [ -n "$AAPT_BIN" ] && [ -x "$AAPT_BIN" ]; then
    PKG="$("$AAPT_BIN" dump badging "$APK" 2>/dev/null | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -1 || true)"
  fi

  if [ -z "$PKG" ]; then
    PKG="com.quickservice.giant"
  fi

  echo "INSTALLING $ITEM ($PKG)..."
  INSTALLED=0
  for attempt in $(seq 1 5); do
    if "$ADB" install -r "$APK"; then
      INSTALLED=1
      break
    fi
    echo "Install attempt $attempt failed for $ITEM. Retrying..."
    sleep 5
  done

  if [ "$INSTALLED" -ne 1 ]; then
    echo "INSTALL: FAIL $ITEM"
    exit 1
  fi

  "$ADB" logcat -c || true

  ACT="$("$ADB" shell cmd package resolve-activity --brief "$PKG" 2>/dev/null | tail -1 | tr -d '\r' || true)"
  if [ -n "$ACT" ] && [ "$ACT" != "No activity found" ]; then
    "$ADB" shell am start -W -n "$ACT" || true
  else
    "$ADB" shell am start -W -n "$PKG/com.quickservice.giant.MainActivity" || true
  fi

  sleep 10

  PID="$("$ADB" shell pidof "$PKG" 2>/dev/null | tr -d '\r' || true)"
  "$ADB" logcat -d > "evidence/${ITEM}_logcat.txt" 2>&1 || true

  if [ -z "$PID" ]; then
    echo "PROCESS: FAIL $ITEM"
    exit 1
  fi

  if grep -qE "FATAL EXCEPTION|AndroidRuntime.*FATAL|am_crash" "evidence/${ITEM}_logcat.txt"; then
    echo "CRASH: FAIL $ITEM"
    exit 1
  fi

  "$ADB" shell uninstall "$PKG" || true
  echo "TEST: PASS $ITEM"
done

echo "REAL ANDROID TEST: PASS"
