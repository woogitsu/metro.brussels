#!/usr/bin/env bash
# T-010: real headless Blender smoke test on CI Linux.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

mkdir -p build/t010 build renders
REPORT="build/t010/report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
SECONDS=0

fail() {
  echo "BŁĄD: $*" >&2
  exit 1
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "BŁĄD: wymagane polecenie '$cmd' nie jest dostępne w PATH" >&2
    return 127
  fi
}

echo "T-010 Blender headless smoke"
echo "============================================================"
date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
echo "repo: $ROOT"
echo "commit: ${GITHUB_SHA:-local}"

echo
echo "[ENV] Linux runner"
uname -a
if [ -r /etc/os-release ]; then cat /etc/os-release; fi

echo
echo "[ENV] toolchain"
require_command python3 || exit $?
require_command blender || exit $?
python3 --version
blender --version | sed -n '1,4p'

if command -v lscpu >/dev/null 2>&1; then
  lscpu | grep -E 'Model name|CPU\(s\)|Thread|Core|Socket' || true
fi
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[ENV] nvidia-smi:"
  nvidia-smi -L || true
else
  echo "[ENV] nvidia-smi unavailable; treat this as a CPU/software headless render path"
fi
if command -v glxinfo >/dev/null 2>&1; then
  echo "[ENV] glxinfo -B:"
  glxinfo -B || true
fi

echo
echo "[VERIFY] project doctor"
bash doctor.sh

echo
echo "[NEGATIVE] missing Blender gives a readable error"
MISSING_LOG="build/t010/missing-blender.log"
if require_command __metro_bxl_missing_blender__ >"$MISSING_LOG" 2>&1; then
  fail "missing-Blender negative test unexpectedly succeeded"
fi
grep -q "BŁĄD: wymagane polecenie" "$MISSING_LOG" || fail "missing-Blender error was not readable"
cat "$MISSING_LOG"

echo
# Syntetyczna oś idzie do build/, nie do data/. `data/` jest tylko do odczytu
# (CLAUDE.md reguła 6), a plik wygenerowany w trakcie przebiegu CI nie jest danymi
# o sieci — jest artefaktem. Zapisywany do data/track/ mieszał się z sześcioma
# prawdziwymi osiami i potrafił przewrócić test, który je przelicza.
echo "[GENERATE] deterministic synthetic centerline"
rm -f build/t010/TEST.json build/TEST.glb renders/TEST_iso.png renders/TEST_side.png renders/TEST_inside.png
python3 tools/track/make_test_track.py --out build/t010/TEST.json
test -s build/t010/TEST.json || fail "build/t010/TEST.json is empty"

echo
echo "[BLENDER] generate GLB"
blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline build/t010/TEST.json \
  --profile box_double \
  --out build/TEST.glb

test -s build/TEST.glb || fail "build/TEST.glb is empty"

echo
echo "[BLENDER] render the exported GLB"
blender --background --python-exit-code 7 --python tools/blender/render_check.py -- \
  --in build/TEST.glb \
  --centerline build/t010/TEST.json \
  --out renders/TEST

python3 - <<'PY'
from pathlib import Path

checks = {
    Path('build/TEST.glb'): b'glTF',
    Path('renders/TEST_iso.png'): b'\x89PNG\r\n\x1a\n',
    Path('renders/TEST_side.png'): b'\x89PNG\r\n\x1a\n',
    Path('renders/TEST_inside.png'): b'\x89PNG\r\n\x1a\n',
}
for path, magic in checks.items():
    if not path.is_file():
        raise SystemExit(f'BŁĄD: brak artefaktu {path}')
    size = path.stat().st_size
    if size <= 1024:
        raise SystemExit(f'BŁĄD: artefakt {path} jest podejrzanie mały: {size} B')
    with path.open('rb') as f:
        got = f.read(len(magic))
    if got != magic:
        raise SystemExit(f'BŁĄD: artefakt {path} ma zły magic header: {got!r}')
    print(f'[ARTIFACT] {path}: {size} B, magic OK')
PY

echo
echo "[NEGATIVE] nonexistent centerline must fail"
rm -f build/t010/negative-missing.glb
if blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline build/t010/does-not-exist.json --profile box_double --out build/t010/negative-missing.glb \
  >build/t010/negative-missing.log 2>&1; then
  fail "nonexistent-centerline negative test unexpectedly succeeded"
fi
test ! -e build/t010/negative-missing.glb || fail "nonexistent centerline created an output GLB"
grep -Eq 'FileNotFoundError|No such file or directory' build/t010/negative-missing.log || fail "missing-centerline diagnostic not found"
tail -n 12 build/t010/negative-missing.log || true

echo
echo "[NEGATIVE] malformed JSON must fail"
printf '{broken json\n' > build/t010/broken.json
rm -f build/t010/negative-broken.glb
if blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline build/t010/broken.json --profile box_double --out build/t010/negative-broken.glb \
  >build/t010/negative-broken.log 2>&1; then
  fail "malformed-JSON negative test unexpectedly succeeded"
fi
test ! -e build/t010/negative-broken.glb || fail "malformed JSON created an output GLB"
grep -Eq 'JSONDecodeError|Expecting property name' build/t010/negative-broken.log || fail "malformed-JSON diagnostic not found"
tail -n 12 build/t010/negative-broken.log || true

echo
echo "[NEGATIVE] unknown tunnel profile must fail"
rm -f build/t010/negative-profile.glb
if blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline build/t010/TEST.json --profile definitely_not_a_profile --out build/t010/negative-profile.glb \
  >build/t010/negative-profile.log 2>&1; then
  fail "unknown-profile negative test unexpectedly succeeded"
fi
test ! -e build/t010/negative-profile.glb || fail "unknown profile created an output GLB"
grep -Eq 'invalid choice|definitely_not_a_profile' build/t010/negative-profile.log || fail "unknown-profile diagnostic not found"
tail -n 12 build/t010/negative-profile.log || true

echo
echo "[VERIFY] Python tool suite"
python3 tools/tests/test_all.py

echo
echo "============================================================"
echo "[RESULT] T-010 automated smoke completed in ${SECONDS}s"
echo "[RESULT] manual visual inspection is STILL REQUIRED for:"
echo "[RESULT]   renders/TEST_iso.png"
echo "[RESULT]   renders/TEST_side.png"
echo "[RESULT]   renders/TEST_inside.png"
echo "[RESULT] Do not close T-010 until those exact PNG files are downloaded and inspected."
