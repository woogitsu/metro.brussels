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
echo "Wymagane dla rdzenia symulacji (T-310 jest zrobione, src/Sim istnieje):"
chk_required "dotnet SDK" "dotnet --version" "zainstaluj .NET SDK 8.0+ (https://dotnet.microsoft.com/download)"

echo ""
echo "Wymagane dopiero przez konkretne zadania:"
# Blender bywa instalowany poza PATH: `tools/ci/blender_install.sh` rozpakowuje
# przypiętą wersję do katalogu poza workspace, bo `git clean -ffdx` z checkoutu
# skasowałby ją przy każdym przebiegu. `BLENDER_BIN` jest tą samą zmienną, której
# używają skrypty CI, więc doctor pyta o to samo co CI, a nie o coś innego.
BLENDER_CMD="${BLENDER_BIN:-blender}"
chk_optional "blender ($BLENDER_CMD)" "\"$BLENDER_CMD\" --version" \
  "wymagany od T-010/T-2xx; ustaw BLENDER_BIN albo uruchom tools/ci/blender_install.sh"
if "$BLENDER_CMD" --version >/dev/null 2>&1; then
  chk_optional "blender headless" "\"$BLENDER_CMD\" --background --python-expr 'pass'" \
    "napraw tryb headless przed T-010"
  # Wersja NIE jest drobiazgiem informacyjnym. Rozstrzyga, która generacja EEVEE stoi
  # za nazwą `BLENDER_EEVEE`, a rendery z legacy i z Next nie są porównywalne. Doctor
  # porównuje z pinem z `tools/ci/blender-version.txt`, czyli z tym samym numerem,
  # którego wymaga CI — inaczej „ok" u siebie i czerwona bramka w CI to ten sam stan.
  PINNED_BLENDER="$(sed -n 's/^version=//p' tools/ci/blender-version.txt 2>/dev/null)"
  HAVE_BLENDER="$("$BLENDER_CMD" --version 2>/dev/null | sed -n '1s/^Blender \([0-9.]*\).*/\1/p')"
  if [ -n "$PINNED_BLENDER" ]; then
    chk_optional "blender w wersji z pinu ($PINNED_BLENDER, jest $HAVE_BLENDER)" \
      "[ \"$HAVE_BLENDER\" = \"$PINNED_BLENDER\" ]" \
      "CI wymaga $PINNED_BLENDER; uruchom tools/ci/blender_install.sh i ustaw BLENDER_BIN"
  fi
fi
# Godot bywa instalowany poza PATH (dystrybucje nie pakują wersji mono, a workflow
# `godot-first-run.yml` rozpakowuje ją do własnego katalogu). `GODOT_BIN` jest tą samą
# zmienną, której używa workflow, więc doctor pyta o to samo co CI, a nie o coś innego.
GODOT_CMD="${GODOT_BIN:-godot}"
chk_optional "godot ($GODOT_CMD)" "\"$GODOT_CMD\" --version" \
  "wymagany od T-400; ustaw GODOT_BIN, jeśli silnik jest poza PATH"

echo ""
echo "Struktura projektu:"
for d in CLAUDE.md docs docs/07-open-data-research.md data/network/lines.json data/network/sources.json data/vehicle/m7-spec.json tools/blender tools/track tools/tests .claude/skills src/Sim tests/Sim.Tests; do
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
echo "Testy rdzenia symulacji:"
# Rdzeń nie ma zależności NuGet, ale testy mają trzy pakiety — pierwsze uruchomienie
# na czystej maszynie wymaga sieci na czas `restore`. Później liczy się z cache.
if command -v dotnet >/dev/null 2>&1; then
  sim_log="${TMPDIR:-/tmp}/mbxl_sim_tests.log"
  if dotnet test tests/Sim.Tests --nologo -v q >"$sim_log" 2>&1; then
    sim_passed=$(grep -oE "Passed: +[0-9]+" "$sim_log" | tail -1 | grep -oE "[0-9]+")
    sim_total=$(grep -oE "Total( tests)?: +[0-9]+" "$sim_log" | tail -1 | grep -oE "[0-9]+")
    echo "  ok    ${sim_passed}/${sim_total} przeszło"
  else
    echo "  BLAD  dotnet test nie przechodzi — zobacz $sim_log"
    required_bad=$((required_bad + 1))
  fi
else
  echo "  pomijam — brak dotnet"
fi

echo ""
echo "--------------------------------------------------"
if [ "$required_bad" -eq 0 ]; then
  # Następne zadanie czytamy z rozpiski, a nie wpisujemy na sztywno. Wpisane na sztywno
  # przestaje być prawdą pierwszego dnia po zrobieniu tego zadania i wysyła kolejną sesję
  # do roboty, która już leży w main.
  next_task=""
  if [ -f docs/TASKS.md ]; then
    next_task=$(grep -E '^### \[ \]' docs/TASKS.md \
      | grep -v 'ZABLOKOWANE' | grep -v 'CZŁOWIEK' \
      | head -1 | sed -E 's/^### \[ \] //')
  fi
  if [ -n "$next_task" ]; then
    echo "  Baza projektu jest gotowa. Następne zadanie: $next_task"
  else
    echo "  Baza projektu jest gotowa. W rozpisce nie ma odblokowanego zadania —"
    echo "  patrz tabela Co blokuje co na końcu docs/TASKS.md."
  fi
  if [ "$optional_bad" -gt 0 ]; then echo "  $optional_bad narzędzi opcjonalnych brakuje; instaluj je dopiero przed zadaniem, które ich wymaga."; fi
else
  echo "  $required_bad wymaganych pozycji do naprawienia przed pracą."
fi
echo ""
exit "$required_bad"
