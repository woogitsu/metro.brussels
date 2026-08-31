#!/usr/bin/env bash
# Sprawdza bazowe wymagania i narzędzia opcjonalne dla kolejnych zadań.
set -u
required_bad=0
optional_bad=0

chk_required() {
  if eval "$2" >/dev/null 2>&1; then echo "  ok    $1"; else echo "  BRAK  $1  -> $3"; required_bad=$((required_bad + 1)); fi
}
chk_optional() {
  if eval "$2" >/dev/null 2>&1; then echo "  ok    $1"; else echo "  WARN  $1  -> $3"; optional_bad=$((optional_bad + 1)); fi
}

echo ""
echo "METRO BXL — kontrola środowiska"
echo "--------------------------------------------------"
echo "Wymagane dla bazy:"
chk_required "python3" "python3 --version" "zainstaluj Pythona 3.11+"
chk_required "git" "git --version" "zainstaluj git"

echo ""
echo "Wymagane dopiero przez konkretne zadania:"
chk_optional "blender w PATH" "blender --version" "wymagany od T-010/T-2xx"
if command -v blender >/dev/null 2>&1; then
  chk_optional "blender headless" "blender --background --python-expr 'pass'" "napraw tryb headless przed T-010"
fi
chk_optional "dotnet" "dotnet --version" "wymagany od T-310"
chk_optional "godot w PATH" "godot --version" "wymagany od T-400"

echo ""
echo "Struktura projektu:"
for d in CLAUDE.md docs docs/07-open-data-research.md data/network/lines.json data/network/sources.json tools/blender tools/track tools/tests .claude/skills; do
  if [ -e "$d" ]; then echo "  ok    $d"; else echo "  BRAK  $d"; required_bad=$((required_bad + 1)); fi
done

echo ""
echo "Testy narzędzi:"
log_file="${TMPDIR:-/tmp}/mbxl_tests.log"
if python3 tools/tests/test_all.py >"$log_file" 2>&1; then
  echo "  ok    $(grep -o "[0-9]*/[0-9]* przeszło" "$log_file")"
else
  echo "  BLAD  testy nie przechodzą — zobacz $log_file"
  required_bad=$((required_bad + 1))
fi

echo ""
echo "--------------------------------------------------"
if [ "$required_bad" -eq 0 ]; then
  echo "  Baza projektu jest gotowa. Następne zadanie: T-010."
  if [ "$optional_bad" -gt 0 ]; then echo "  $optional_bad narzędzi opcjonalnych brakuje; instaluj je dopiero przed zadaniem, które ich wymaga."; fi
else
  echo "  $required_bad wymaganych pozycji do naprawienia przed pracą."
fi
echo ""
exit "$required_bad"
