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

for ITEM in android_app khaled_android; do
  APK="${GITHUB_WORKSPACE:-.}/$ITEM/app/build/outputs/apk/debug/app-debug.apk"
  test -f "$APK" || { echo "APK: FAIL $ITEM"; exit 1; }

  AAPT="$(find "${ANDROID_HOME:-/usr/local/lib/android/sdk}/build-tools" -type f -name aapt | sort -V | tail -1)"
  PKG="$("$AAPT" dump badging "$APK" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -1)"
  test -n "$PKG"

  "$ADB" install -r "$APK"
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
