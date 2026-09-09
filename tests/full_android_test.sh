#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT="$ROOT/evidence/full_android_test.txt"
mkdir -p "$ROOT/evidence"

exec > >(tee "$REPORT") 2>&1

echo "======================================================================"
echo "GQS — ONE STAGE FULL ANDROID TEST"
echo "======================================================================"

FAIL=0

run() {
    echo
    echo ">>> $*"
    "$@" || FAIL=1
}

echo "[1] PROJECT DISCOVERY"
for P in android_app khaled_android; do
    if [ -d "$ROOT/$P" ]; then
        echo "$P : PRESENT"
    else
        echo "$P : MISSING"
        FAIL=1
    fi
done

echo
echo "[2] ANDROID BUILD"

for P in android_app khaled_android; do
    echo
    echo "=== BUILD: $P ==="

    cd "$ROOT/$P"

    if [ ! -f "./gradlew" ]; then
        echo "GRADLE WRAPPER: MISSING"
        FAIL=1
        continue
    fi

    chmod +x ./gradlew

    ./gradlew clean assembleDebug --no-daemon

    APK="$ROOT/$P/app/build/outputs/apk/debug/app-debug.apk"

    if [ -f "$APK" ]; then
        echo "APK: PRESENT"
        ls -lh "$APK"
    else
        echo "APK: MISSING"
        FAIL=1
    fi
done

echo
echo "[3] APK INTEGRITY"

python3 - "$ROOT" <<'PY'
import sys, zipfile
from pathlib import Path

root = Path(sys.argv[1])

for p in [
    root/"android_app/app/build/outputs/apk/debug/app-debug.apk",
    root/"khaled_android/app/build/outputs/apk/debug/app-debug.apk"
]:
    print("\nAPK:", p)

    if not p.exists():
        print("RESULT: MISSING")
        continue

    try:
        with zipfile.ZipFile(p) as z:
            bad = z.testzip()
            names = z.namelist()

        print("ZIP:", "OK" if bad is None else "BAD")
        print("ENTRIES:", len(names))
        print("MANIFEST:", "OK" if "AndroidManifest.xml" in names else "MISSING")
        print("SIZE:", p.stat().st_size)
    except Exception as e:
        print("RESULT: ERROR", e)
PY

echo
echo "[4] MANIFEST / PACKAGE ANALYSIS"

SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"

AAPT=""
if [ -n "$SDK" ]; then
    AAPT="$(find "$SDK/build-tools" -name aapt -type f 2>/dev/null | sort -V | tail -1)"
fi

if [ -n "$AAPT" ]; then
    for P in android_app khaled_android; do
        APK="$ROOT/$P/app/build/outputs/apk/debug/app-debug.apk"

        echo
        echo "=== $P ==="

        "$AAPT" dump badging "$APK" |
        grep -E "package:|launchable-activity:|sdkVersion:|targetSdkVersion:" || true
    done
else
    echo "AAPT: NOT AVAILABLE"
fi

echo
echo "[5] ANDROID RUNTIME"

ADB="${SDK:-}/platform-tools/adb"
EMU="${SDK:-}/emulator/emulator"

if [ ! -x "$ADB" ]; then
    echo "ADB: NOT AVAILABLE"
    echo "RUNTIME: NOT EXECUTED"
elif [ ! -x "$EMU" ]; then
    echo "EMULATOR: NOT AVAILABLE"
    echo "RUNTIME: NOT EXECUTED"
else

    AVD="GQS_FULL_TEST"

    echo "Creating/checking AVD..."

    if ! "$SDK/cmdline-tools/latest/bin/avdmanager" list avd 2>/dev/null |
       grep -q "Name: $AVD"; then

        echo "no" |
        "$SDK/cmdline-tools/latest/bin/avdmanager" create avd \
        -n "$AVD" \
        -k "system-images;android-35;google_apis;x86_64" \
        --force
    fi

    echo "Starting emulator..."

    "$EMU" \
        -avd "$AVD" \
        -no-window \
        -no-audio \
        -no-boot-anim \
        -gpu swiftshader_indirect \
        -accel off \
        >/tmp/gqs_emulator.log 2>&1 &

    EMU_PID=$!

    BOOT=0

    for i in $(seq 1 90); do
        sleep 2

        if "$ADB" shell getprop sys.boot_completed 2>/dev/null |
           grep -q "1"; then
            BOOT=1
            break
        fi
    done

    if [ "$BOOT" -eq 1 ]; then

        echo "EMULATOR BOOT: SUCCESS"

        for P in android_app khaled_android; do

            APK="$ROOT/$P/app/build/outputs/apk/debug/app-debug.apk"

            echo
            echo "=== REAL TEST: $P ==="

            "$ADB" install -r "$APK"

            if [ $? -ne 0 ]; then
                echo "INSTALL: FAIL"
                FAIL=1
                continue
            fi

            echo "INSTALL: PASS"

            "$ADB" shell am force-stop com.quickservice.giant
            "$ADB" logcat -c

            "$ADB" shell am start \
                -W \
                -n com.quickservice.giant/com.quickservice.giant.MainActivity

            sleep 8

            if "$ADB" shell pidof com.quickservice.giant >/dev/null 2>&1; then
                echo "PROCESS: RUNNING"
            else
                echo "PROCESS: NOT RUNNING"
                FAIL=1
            fi

            "$ADB" logcat -d > "$ROOT/evidence/${P}_logcat.txt"

            if grep -qE "FATAL EXCEPTION|AndroidRuntime.*FATAL|am_crash" \
                "$ROOT/evidence/${P}_logcat.txt"; then
                echo "CRASH: DETECTED"
                FAIL=1
            else
                echo "CRASH: NOT DETECTED"
            fi

            "$ADB" uninstall com.quickservice.giant >/dev/null 2>&1 || true
        done

        kill "$EMU_PID" >/dev/null 2>&1 || true

    else
        echo "EMULATOR BOOT: FAILED"
        echo "RUNTIME: NOT EXECUTED"
        echo
        echo "Emulator log:"
        tail -50 /tmp/gqs_emulator.log || true
    fi
fi

echo
echo "[6] HUAWEI COMPATIBILITY"

python3 - "$ROOT" <<'PY'
import sys, zipfile
from pathlib import Path

root = Path(sys.argv[1])

for p in [
    root/"android_app/app/build/outputs/apk/debug/app-debug.apk",
    root/"khaled_android/app/build/outputs/apk/debug/app-debug.apk"
]:
    print("\n", p.name)

    if not p.exists():
        print("APK: MISSING")
        continue

    with zipfile.ZipFile(p) as z:
        files = [x.lower() for x in z.namelist()]

    gms = [x for x in files if "com/google/android/gms" in x or "play-services" in x or "firebase" in x]
    hms = [x for x in files if "com/huawei" in x or "hms" in x]

    print("GMS INDICATORS:", len(gms))
    print("HMS INDICATORS:", len(hms))
    print("STATIC HUAWEI AUDIT: COMPLETE")
    print("REAL HUAWEI DEVICE: NOT TESTED")
PY

echo
echo "======================================================================"
echo "FINAL RESULT"
echo "======================================================================"

if [ "$FAIL" -eq 0 ]; then
    echo "STATUS: PASS"
else
    echo "STATUS: PARTIAL/FAIL"
fi

echo
echo "IMPORTANT:"
echo "PASS means only tests actually executed passed."
echo "Huawei physical-device testing is NOT claimed."
echo
echo "REPORT:"
echo "$REPORT"

echo "======================================================================"
