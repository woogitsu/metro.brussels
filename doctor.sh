#!/usr/bin/env bash
# Sprawdza bazowe wymagania i narzędzia opcjonalne dla kolejnych zadań.
set -u
required_bad=0
optional_bad=0

# `--no-tests` pomija OBA zestawy i sprawdza wyłącznie środowisko.
#
# Dwa powody, oba praktyczne. Pierwszy: `CLAUDE.md` §2 każe uruchomić doctora przed
# KAŻDYM zadaniem, a pełny przebieg to oba zestawy — czyli dokładnie to, co i tak
# uruchamia się osobno w pętli weryfikacji z §5. Drugi: bramka, która sprawdza
# ZACHOWANIE doctora, musi go uruchomić, a doctor uruchamia `test_all.py` — więc bez
# tej flagi test wewnątrz zestawu odpalałby cały zestaw jeszcze raz, cztery razy pod
# rząd. Pierwsza wersja tej bramki tak właśnie robiła i przekroczyła limit czasu.
RUN_TESTS=1
for arg in "$@"; do
  case "$arg" in
    --no-tests) RUN_TESTS=0 ;;
    -h|--help)
      echo "użycie: bash doctor.sh [--no-tests]"
      echo "  --no-tests   sprawdź tylko środowisko, nie uruchamiaj zestawów testów"
      echo ""
      echo "zmienne: DOTNET_BIN, BLENDER_BIN, GODOT_BIN — ścieżki do narzędzi,"
      echo "         gdy leżą poza PATH (ta sama konwencja co w tools/ci/)"
      exit 0 ;;
    *) echo "nieznany argument: $arg (patrz --help)" >&2; exit 2 ;;
  esac
done

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

# `${DOTNET_BIN:-dotnet}` — ta sama konwencja, co `${BLENDER_BIN:-blender}` w sześciu
# skryptach `tools/ci/` i co `GODOT_BIN`, i z tego samego powodu: SDK potrafi leżeć
# POZA `PATH`. W CI nie potrafi, bo `DOTNET_INSTALL_DIR` sprawia, że `setup-dotnet`
# kładzie je na `PATH` (`sim-tests.yml`) — ale na maszynie, na której ktoś zainstalował
# SDK do katalogu domowego, `dotnet` z `PATH` jest tym STARYM z pakietu systemowego.
# Zmierzone w tym środowisku 04.09.2026: `dotnet --version` daje 8.0.130, a obok stoi
# 10.0.400 w `$HOME/.dotnet`, którego doctor nie widział. Kazał więc pobrać SDK, które
# już było na dysku, i to jest gorsze niż milczenie: brzmi jak brak, a jest ślepotą.
DOTNET="${DOTNET_BIN:-dotnet}"
chk_required "dotnet SDK" "$DOTNET --version" "zainstaluj .NET SDK 10.0+ (https://dotnet.microsoft.com/download)"

# Sama obecność `dotnet` nie wystarczy i to jest zmierzone, nie przewidywane.
# Po podniesieniu rdzenia na `net10.0` (04.09.2026) doctor na SDK 8.0.130 wypisywał
# `ok dotnet SDK`, a dwadzieścia wierszy niżej `BLAD dotnet test nie przechodzi`
# z błędem NETSDK1045 — czyli mówił „ok" o tym samym SDK, przez które przed chwilą
# padł. Podpowiedź obiecywała „10.0+", ale nikt tego nie sprawdzał.
#
# Wymagana wersja NIE jest tu wpisana z ręki: czyta się ją z `<TargetFramework>`
# w `src/Sim/Sim.csproj`, czyli z jedynego miejsca, które o niej decyduje. Wpisanie
# jej drugi raz dałoby dwa źródła prawdy i rozjazd przy następnym podniesieniu.
REQUIRED_TFM="$(sed -n 's/.*<TargetFramework>net\([0-9]*\)\..*/\1/p' src/Sim/Sim.csproj 2>/dev/null | head -1)"
HAVE_SDK_MAJOR="$($DOTNET --version 2>/dev/null | cut -d. -f1)"
if [ -n "$REQUIRED_TFM" ] && [ -n "$HAVE_SDK_MAJOR" ]; then
  chk_required "dotnet SDK >= $REQUIRED_TFM (jest $HAVE_SDK_MAJOR)" \
    "[ \"$HAVE_SDK_MAJOR\" -ge \"$REQUIRED_TFM\" ]" \
    "src/Sim/Sim.csproj celuje w net${REQUIRED_TFM}.0, a to SDK tego nie zbuduje (NETSDK1045); pobierz nowsze z https://dotnet.microsoft.com/download"

  # Zanim każe cokolwiek pobierać, doctor SZUKA. Podpowiedź wypisuje się wyłącznie
  # wtedy, gdy znaleziony `dotnet` naprawdę zgłasza wersję dostatecznie wysoką —
  # nie na samą obecność pliku. Podpowiedź o SDK, którego tam nie ma, byłaby
  # dokładnie tym samym błędem, tylko w drugą stronę.
  if [ "$HAVE_SDK_MAJOR" -lt "$REQUIRED_TFM" ] 2>/dev/null; then
    for candidate in "$HOME/.dotnet/dotnet" /usr/local/share/dotnet/dotnet \
                     /usr/share/dotnet/dotnet /opt/dotnet/dotnet; do
      [ -x "$candidate" ] || continue
      [ "$candidate" = "$(command -v "$DOTNET" 2>/dev/null)" ] && continue
      cand_major="$("$candidate" --version 2>/dev/null | cut -d. -f1)"
      [ -n "$cand_major" ] || continue
      if [ "$cand_major" -ge "$REQUIRED_TFM" ] 2>/dev/null; then
        echo "        na dysku JEST nowsze SDK: $candidate (wersja ${cand_major}.x)"
        echo "        uruchom: DOTNET_BIN=$candidate bash doctor.sh"
        break
      fi
    done
  fi
fi

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

# STRAŻNIK REKURENCJI, i nie jest hipotetyczny.
#
# Doctor uruchamia `tools/tests/test_all.py`, a ten zestaw zawiera testy, które
# uruchamiają doctora (bramki `test_dotnet_version.py`). Dopóki te bramki podają
# `--no-tests`, pętla jest przerwana — ale zależy to od jednej gałęzi `case`.
# Zmierzone 04.09.2026: mutacja `--no-tests) RUN_TESTS=1` zamieniła to w rekurencję
# wykładniczą i zostawiła w systemie 174 procesy `test_all.py`, zanim je wyłapałem.
#
# Marker w środowisku zamyka całą tę klasę, a nie jedną mutację: zagnieżdżony doctor
# pomija zestawy bez względu na argumenty, jakie dostał.
if [ "${MBXL_DOCTOR_RUNNING:-0}" = "1" ]; then
  RUN_TESTS=0
  echo ""
  echo "Testy: pomijam — doctor jest już uruchomiony wyżej (MBXL_DOCTOR_RUNNING)."
fi
export MBXL_DOCTOR_RUNNING=1

if [ "$RUN_TESTS" -eq 1 ]; then
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
if command -v "${DOTNET_BIN:-dotnet}" >/dev/null 2>&1; then
  sim_log="${TMPDIR:-/tmp}/mbxl_sim_tests.log"
  if "${DOTNET_BIN:-dotnet}" test tests/Sim.Tests --nologo -v q >"$sim_log" 2>&1; then
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
