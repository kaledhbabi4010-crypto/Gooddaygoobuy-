#!/usr/bin/env bash
set -euo pipefail

mkdir -p evidence
ADB="${ANDROID_HOME:-/usr/local/lib/android/sdk}/platform-tools/adb"

echo "DEVICE"
"$ADB" devices

echo "BOOT"
BOOT="0"
for i in $(seq 1 60); do
  B=$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
  if [ "$B" = "1" ]; then
    BOOT="1"
    break
  fi
  sleep 5
done

if [ "$BOOT" != "1" ]; then
  echo "BOOT: FAIL"
  "$ADB" shell getprop > evidence/getprop.txt || true
  "$ADB" logcat -d > evidence/logcat.txt || true
  exit 1
fi

echo "BOOT: PASS"

echo "WAIT FOR PACKAGE MANAGER SERVICE"
for i in $(seq 1 30); do
  if "$ADB" shell pm path android 2>/dev/null | grep -q "package:" || "$ADB" shell pm list packages 2>/dev/null | grep -q "package:"; then
    echo "PM SERVICE: READY"
    break
  fi
  sleep 3
done

"$ADB" shell settings put global package_verifier_enable 0 2>/dev/null || true

for ITEM in android_app khaled_android; do
  APK="${GITHUB_WORKSPACE:-.}/$ITEM/app/build/outputs/apk/debug/app-debug.apk"
  test -f "$APK" || { echo "APK: FAIL $ITEM"; exit 1; }

  AAPT="$(find "${ANDROID_HOME:-/usr/local/lib/android/sdk}/build-tools" -type f -name aapt | sort -V | tail -1)"
  PKG="$("$AAPT" dump badging "$APK" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -1)"
  test -n "$PKG"

  INSTALLED="0"
  for attempt in $(seq 1 5); do
    if "$ADB" install -r "$APK"; then
      INSTALLED="1"
      break
    fi
    echo "INSTALL ATTEMPT $attempt FAILED, RETRYING..."
    "$ADB" shell pm list packages >/dev/null 2>&1 || true
    sleep 5
  done

  if [ "$INSTALLED" != "1" ]; then
    echo "INSTALL: FAIL $ITEM"
    "$ADB" logcat -d > "evidence/${ITEM}_install_fail_logcat.txt" || true
    exit 1
  fi

  "$ADB" logcat -c

  ACT="$("$ADB" shell cmd package resolve-activity --brief "$PKG" | tail -1 | tr -d '\r')"
  "$ADB" shell am start -W -n "$ACT"
  sleep 10

  PID="$("$ADB" shell pidof "$PKG" 2>/dev/null | tr -d '\r' || true)"
  "$ADB" logcat -d > "evidence/${ITEM}_logcat.txt"

  if [ -z "$PID" ]; then
    echo "PROCESS: FAIL $ITEM"
    exit 1
  fi

  if grep -qE "FATAL EXCEPTION|AndroidRuntime.*FATAL|am_crash" "evidence/${ITEM}_logcat.txt"; then
    echo "CRASH: DETECTED $ITEM"
    exit 1
  fi

  "$ADB" shell uninstall "$PKG" || true
  echo "TEST: PASS $ITEM"
done

echo "REAL ANDROID TEST: PASS"
