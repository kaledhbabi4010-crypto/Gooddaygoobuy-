#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
ADB="${ANDROID_HOME}/platform-tools/adb"

echo "DEVICE"
"${ADB}" devices

echo "BOOT"
for i in $(seq 1 60); do
  B=$("${ADB}" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
  [ "${B}" = "1" ] && break
  sleep 5
done

[ "${B}" = "1" ] || {
  echo "BOOT: FAIL"
  "${ADB}" shell getprop > evidence/getprop.txt || true
  "${ADB}" logcat -d > evidence/logcat.txt || true
  exit 1
}

echo "BOOT: PASS"

echo "WAIT FOR PACKAGE MANAGER"
for i in $(seq 1 30); do
  P=$("${ADB}" shell pm path android 2>/dev/null | tr -d '\r' || true)
  [ -n "${P}" ] && break
  sleep 3
done

echo "DISABLE VERIFIER"
for i in $(seq 1 5); do
  "${ADB}" shell settings put global package_verifier_enable 0 2>/dev/null && break || sleep 2
done

for i in $(seq 1 5); do
  "${ADB}" shell settings put global verifier_verify_adb_installs 0 2>/dev/null && break || sleep 2
done

for i in $(seq 1 5); do
  "${ADB}" shell settings put global upload_apk_enable 0 2>/dev/null && break || sleep 2
done

for i in $(seq 1 5); do
  "${ADB}" shell settings put global package_verifier_user_consent -1 2>/dev/null && break || sleep 2
done

for ITEM in android_app khaled_android; do
  APK="${GITHUB_WORKSPACE}/${ITEM}/app/build/outputs/apk/debug/app-debug.apk"
  test -f "${APK}" || { echo "APK: FAIL ${ITEM}"; exit 1; }

  AAPT="$(find "${ANDROID_HOME}/build-tools" -type f -name aapt | sort -V | tail -1)"
  PKG="$("${AAPT}" dump badging "${APK}" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -1)"
  test -n "${PKG}"

  INSTALLED=0
  for attempt in 1 2 3 4; do
    echo "Checking package manager status before install (attempt ${attempt})..."
    if ! "${ADB}" shell pm list packages >/dev/null 2>&1; then
      echo "Package manager service unresponsive. Re-triggering package manager..."
      "${ADB}" shell settings put global package_verifier_enable 0 2>/dev/null || true
      sleep 3
    fi

    if "${ADB}" install -r -g -t --user 0 "${APK}"; then
      INSTALLED=1
      break
    fi
    echo "Install attempt ${attempt} failed for ${ITEM}, retrying..."
    sleep 5
  done

  [ "${INSTALLED}" = "1" ] || { echo "INSTALL: FAIL ${ITEM}"; exit 1; }
  "${ADB}" logcat -c

  ACT="$("${ADB}" shell cmd package resolve-activity --brief "${PKG}" | tail -1 | tr -d '\r')"
  "${ADB}" shell am start -W -n "${ACT}"
  sleep 10

  PID="$("${ADB}" shell pidof "${PKG}" 2>/dev/null | tr -d '\r' || true)"
  "${ADB}" logcat -d > "evidence/${ITEM}_logcat.txt"

  test -n "${PID}" || { echo "PROCESS: FAIL ${ITEM}"; exit 1; }
  ! grep -qE "FATAL EXCEPTION|AndroidRuntime.*FATAL|am_crash" "evidence/${ITEM}_logcat.txt"

  "${ADB}" shell uninstall "${PKG}" || true
  echo "TEST: PASS ${ITEM}"
done

echo "REAL ANDROID TEST: PASS"
