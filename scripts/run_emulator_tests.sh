#!/usr/bin/env bash
set -euo pipefail

mkdir -p evidence
ADB="${ANDROID_HOME}/platform-tools/adb"

echo "=== DEVICE ==="
"$ADB" devices

echo "=== WAIT FOR BOOT ==="
BOOT_OK=0
for i in $(seq 1 60); do
  B=$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
  if [ "$B" = "1" ]; then
    BOOT_OK=1
    break
  fi
  sleep 5
done

if [ "$BOOT_OK" != "1" ]; then
  echo "BOOT: FAIL"
  "$ADB" shell getprop > evidence/getprop.txt || true
  "$ADB" logcat -d > evidence/logcat.txt || true
  exit 1
fi

echo "BOOT: PASS"

# Disable package verification
"$ADB" shell settings put global package_verifier_enable 0 2>/dev/null || true

for ITEM in android_app khaled_android; do
  APK="$GITHUB_WORKSPACE/$ITEM/app/build/outputs/apk/debug/app-debug.apk"
  if [ ! -f "$APK" ]; then
    echo "APK NOT FOUND: $APK"
    exit 1
  fi

  echo "=== TESTING $ITEM ==="
  "$ADB" install -r "$APK" || {
    echo "RETRY INSTALL $ITEM"
    sleep 3
    "$ADB" install -r "$APK"
  }

  "$ADB" logcat -c || true

  # Resolve & start main activity
  ACT="$("$ADB" shell cmd package resolve-activity --brief com.quickservice.giant | tail -1 | tr -d '\r' || true)"
  if [ -n "$ACT" ]; then
    "$ADB" shell am start -W -n "$ACT" || true
  else
    "$ADB" shell am start -W -n com.quickservice.giant/com.quickservice.giant.MainActivity || true
  fi

  sleep 10

  PID="$("$ADB" shell pidof com.quickservice.giant 2>/dev/null | tr -d '\r' || true)"
  "$ADB" logcat -d > "evidence/${ITEM}_logcat.txt"

  if grep -qE "FATAL EXCEPTION|AndroidRuntime.*FATAL|am_crash" "evidence/${ITEM}_logcat.txt"; then
    echo "CRASH DETECTED IN $ITEM"
    exit 1
  fi

  "$ADB" uninstall com.quickservice.giant 2>/dev/null || true
  echo "TEST PASS: $ITEM"
done

echo "REAL ANDROID TEST: PASS"
