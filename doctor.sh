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

# DWIE FORMY, NIE JEDNA — 6.D98. Do 10.09.2026 jedna para funkcji obsługiwała oba
# kształty drugiego argumentu przez `eval`, czyli przez parsowanie napisu DRUGI RAZ.
# Zmierzone tego dnia: jedenaście wywołań, z czego **sześć** uruchamia program
# (`"$DOTNET" --version`), a **pięć** sprawdza warunek powłoki
# (`[ "$HAVE_SDK_MAJOR" -ge "$REQUIRED_TFM" ]`).
#
# 6.D81 zamknęło OBJAW: ścieżka ze spacją rozpadała się przy drugim parsowaniu na dwa
# słowa i doctor meldował brak SDK, którego przed chwilą użył. Zacytowanie ścieżek
# i bramka na cytowanie tamten przypadek naprawiły, ale zostawiły potrzebę PAMIĘTANIA
# o cudzysłowach przy każdym nowym wywołaniu — bramka umie taki błąd zgłosić, nie umie
# go uczynić niemożliwym.
#
# Forma programowa nie ma już `eval` i bierze argumenty jako TABLICĘ (`"$@"`), więc
# spacja w ścieżce jest zwykłym znakiem. Forma wyrażeniowa `eval` zostaje — wyrażenie
# powłoki nie jest tablicą słów — i nazywa się tak, żeby było widać, że to ona.
chk_prog_required() {
  nazwa="$1"; podpowiedz="$2"; shift 2
  if "$@" >/dev/null 2>&1; then echo "  ok    $nazwa"
  else echo "  BRAK  $nazwa  -> $podpowiedz"; required_bad=$((required_bad + 1)); fi
}
chk_prog_optional() {
  nazwa="$1"; podpowiedz="$2"; shift 2
  if "$@" >/dev/null 2>&1; then echo "  ok    $nazwa"
  else echo "  WARN  $nazwa  -> $podpowiedz"; optional_bad=$((optional_bad + 1)); fi
}
chk_expr_required() {
  if eval "$2" >/dev/null 2>&1; then echo "  ok    $1"; else echo "  BRAK  $1  -> $3"; required_bad=$((required_bad + 1)); fi
}
chk_expr_optional() {
  if eval "$2" >/dev/null 2>&1; then echo "  ok    $1"; else echo "  WARN  $1  -> $3"; optional_bad=$((optional_bad + 1)); fi
}

echo ""
echo "METRO BXL — kontrola środowiska"
echo "--------------------------------------------------"
echo "Wymagane dla bazy:"
chk_prog_required "python3" "zainstaluj Pythona 3.11+" python3 --version
chk_prog_required "git" "zainstaluj git" git --version

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

# Wymagana wersja NIE jest tu wpisana z ręki: czyta się ją z `<TargetFramework>`
# w `src/Sim/Sim.csproj`, czyli z jedynego miejsca, które o niej decyduje. Stoi
# TUTAJ, przed pierwszym sprawdzeniem, bo od 6.D57 potrzebuje jej także szukanie
# SDK na dysku — a to musi się wykonać niezależnie od tego, czy `dotnet` jest
# w `PATH`.
REQUIRED_TFM="$(sed -n 's/.*<TargetFramework>net\([0-9]*\)\..*/\1/p' src/Sim/Sim.csproj 2>/dev/null | head -1)"

# SZUKANIE SDK NA DYSKU — wykonywane ZAWSZE, nie tylko gdy w `PATH` stoi SDK za
# stare. To jest cała treść 6.D57.
#
# **Zmierzone 08.09.2026 na kontenerze sesji, przed poprawką:** `/root/.dotnet/dotnet`
# zgłasza `10.0.400`, a `doctor.sh` melduje `BRAK dotnet SDK -> zainstaluj .NET SDK
# 10.0+` i kończy kodem 1. Przyczyna była w kodzie, nie w środowisku: przejście po
# katalogach kandydatów stało wewnątrz `if [ -n "$HAVE_SDK_MAJOR" ]`, a ta zmienna
# bierze się z `$DOTNET --version`. Bez `dotnet` w `PATH` była pusta, więc cały blok
# się nie wykonywał — podpowiedź o katalogach działała WYŁĄCZNIE wtedy, gdy w `PATH`
# stało SDK za stare, i nigdy gdy nie stało żadne.
#
# Komentarz dwadzieścia wierszy wyżej opisywał tę usterkę od 04.09.2026 („Kazał więc
# pobrać SDK, które już było na dysku, i to jest gorsze niż milczenie: brzmi jak brak,
# a jest ślepotą") — i mimo to poprawka objęła tylko przypadek SDK za starego.
# Zdanie w prozie nie jest bramką; pilnuje tego dziś `tools/tests/test_doctor_dotnet.py`.
SDK_NA_DYSKU=""
if [ -n "$REQUIRED_TFM" ]; then
  # Lista kandydatów jest ta sama, co przed 6.D57, i CELOWO bez ścieżki
  # bezwzględnej do katalogu domowego roota. Pierwsza wersja tej poprawki dopisała
  # tu `/root/.dotnet/dotnet` — redundantnie, bo `$HOME` w tym środowisku JEST
  # `/root`, i szkodliwie, bo ścieżka bezwzględna przebija podstawiony `HOME`
  # w piaskownicy bramek z `tools/tests/test_dotnet_version.py`. Zaczerwieniły się
  # wtedy CZTERY istniejące testy naraz i to one wymusiły cofnięcie dopisku.
  for candidate in "$HOME/.dotnet/dotnet" /usr/local/share/dotnet/dotnet \
                   /usr/share/dotnet/dotnet /opt/dotnet/dotnet; do
    [ -x "$candidate" ] || continue
    [ "$candidate" = "$(command -v "$DOTNET" 2>/dev/null)" ] && continue
    cand_major="$("$candidate" --version 2>/dev/null | cut -d. -f1)"
    [ -n "$cand_major" ] || continue
    if [ "$cand_major" -ge "$REQUIRED_TFM" ] 2>/dev/null; then
      SDK_NA_DYSKU="$candidate"
      break
    fi
  done
fi

# PODPOWIEDŹ NAZYWA `DOTNET_ROOT` RAZEM Z `PATH`, A NIE `DOTNET_BIN`, i to jest
# wynik pomiaru, nie gust. Zmierzone 09.09.2026, ten sam skrypt, Godot osiągalny:
#
#   DOTNET_BIN=/root/.dotnet/dotnet   ->  ok dotnet SDK, ale WARN godot .NET hostfxr
#   DOTNET_ROOT=/root/.dotnet + PATH  ->  ok dotnet SDK, ok godot .NET hostfxr
#
# Powód stoi w kontroli `hostfxr` niżej: `HOSTFXR_OK` bierze się z `DOTNET_ROOT`
# albo z GOŁEGO `command -v dotnet`, a nie z `$DOTNET_BIN`. Podpowiedź radząca
# `DOTNET_BIN` zdejmowała więc jeden komunikat i zostawiała drugi — a ten drugi
# mówi o awarii, która objawia się natychmiastową śmiercią procesu (log: signal 11,
# powłoka: kod 134) — patrz komentarz przy samej kontroli `hostfxr` niżej.
if [ -n "$SDK_NA_DYSKU" ]; then
  BRAK_SDK_PODPOWIEDZ="SDK JEST na dysku: $SDK_NA_DYSKU (wersja $(\
    "$SDK_NA_DYSKU" --version 2>/dev/null)) — nie instaluj, tylko uruchom: export DOTNET_ROOT=$(dirname "$SDK_NA_DYSKU"); export PATH=\"\$DOTNET_ROOT:\$PATH\"   (samo DOTNET_BIN zdejmuje ten komunikat, ale ZOSTAWIA WARN godot .NET hostfxr — zmierzone)"
else
  BRAK_SDK_PODPOWIEDZ="zainstaluj .NET SDK 10.0+ (https://dotnet.microsoft.com/download)"
fi
# ŚCIEŻKA JEST CYTOWANA WEWNĄTRZ NAPISU, I TO NIE JEST OZDOBA — 6.D81.
# `chk_required` wykonuje swój drugi argument przez `eval`, czyli parsuje go DRUGI
# RAZ. Bez tych cudzysłowów ścieżka ze spacją rozpada się na dwa słowa i doctor
# melduje brak SDK, którego przed chwilą użył. Zmierzone 10.09.2026 atrapą w katalogu
# `sdk with space` (bez instalowania czegokolwiek):
#
#   DOTNET_BIN="…/sdk with space/dotnet"  ->  BRAK  dotnet SDK
#   DOTNET_BIN="…/sdk_no_space/dotnet"    ->  ok    dotnet SDK  (ta sama atrapa)
#
# Kilkadziesiąt wierszy niżej `dotnet test` woła TĘ SAMĄ ścieżkę cytowaną poprawnie,
# więc pełny przebieg meldował brak SDK w sekcji środowiska i `ok` w sekcji testów —
# wewnętrzna sprzeczność jednego raportu, a `CLAUDE.md` §2 każe czytać go przed
# KAŻDYM zadaniem. Wiersz z Blenderem obok był cytowany od początku i to on jest tu
# wzorcem. Pilnuje tego `tools/tests/test_dotnet_version.py`.
# 6.D96: STAN ROZPOZNANY PRZED KONTROLAMI, po KODZIE WYJŚCIA, nie po treści stdout.
# Do 10.09.2026 przy niespełnialnym pinie doctor wypisywał NARAZ dwa zdania o tym
# samym SDK — `BRAK dotnet SDK -> zainstaluj` (bo `--version` kończy kodem 155)
# i `ok dotnet SDK >= 10 (jest 10)` (bo `cut -d. -f1` brał pierwszą liczbę z listy
# SDK, którą to samo polecenie wypisuje na stdout, PADAJĄC). Jedno z tych zdań radzi
# zainstalować coś, co leży na dysku; drugie melduje sprawdzenie zrobione na wyjściu
# polecenia, które się nie powiodło.
#
# `--list-sdks` odpowiada na pytanie „czy jakiekolwiek SDK jest", a `--version`
# na „czy któreś spełnia pin z global.json" — jedyną różnicą między nimi jest to,
# że drugie czyta `global.json`. Rozstrzyga KOD WYJŚCIA obu, nie ich stdout.
PIN_SDK="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([0-9.]*\)".*/\1/p' \
           global.json 2>/dev/null | head -n 1)"
# Liczy się NIEPUSTE wyjście, nie sam kod zero. `dotnet --list-sdks` na maszynie
# z zainstalowanym runtime'em, ale bez ani jednego SDK, kończy ZEREM i nie wypisuje
# nic — a to jest stan „nie ma czego pinować", nie „pin niespełniony". Bramka
# `test_brak_jakiegokolwiek_sdk_nadal_kaze_instalowac` złapała tę różnicę na
# pierwszej wersji tego bloku, która patrzyła na sam kod wyjścia.
#
# 6.D128: JEDNO wywołanie `--list-sdks` na cały blok, a jego WYJŚCIE niesie zmienna
# — bo pyta o nie dwóch rozmówców: sonda `SDK_NA_LISCIE` i wypis listy na ekran
# w gałęzi „pin niespełniony". Zmierzone 11.09.2026 dziennikiem atrapy: pin
# niespełniony **2**, pin spełniony **1**, brak SDK **1**.
#
# Powód jest ten sam co przy `--version` w 6.D112 i nie jest nim czas: dwa wywołania
# to dwie okazje do rozjazdu. Doctor wypisywałby wtedy „SDK SĄ na dysku" na podstawie
# pierwszego odczytu, a listę „na dysku:" z drugiego — czyli zdanie o jednym stanie
# maszyny obok listy z innego.
#
# `printf '%s\n'` zamiast gołego podstawienia, bo `$(...)` obcina KOŃCOWE nowe
# wiersze. **Zdanie o skutku jest tu przepisane 11.09.2026 przy 6.D129, bo pierwsza
# wersja, z 6.D128, była NIEPRAWDZIWA.** Mówiła, że „`sed` bez nich nie zobaczyłby
# ostatniego wiersza listy", a GNU `sed` wypisuje ostatni wiersz niepełny — zmierzone:
# `printf '%s' "$V" | sed` daje `X: a` i `X: b`, tyle że bez zakończenia.
#
# Prawdziwy skutek jest mniejszy i wciąż wart tej linijki: brakujące zakończenie
# zjada PUSTY WIERSZ oddzielający listę od następnej sekcji doctora, więc nagłówek
# „Wymagane dopiero przez konkretne zadania:" przykleja się pod ostatnim SDK.
# Zmierzone na dwóch SDK: `…[/atrapa/sdk]\nWymagane…` zamiast `…[/atrapa/sdk]\n\nWymagane…`.
#
# Przy pustej liście ta gałąź i tak się nie wykonuje: wymaga `SDK_NA_LISCIE = tak`.
SDK_LISTA="$("$DOTNET" --list-sdks 2>/dev/null)"
SDK_NA_LISCIE="nie"
if [ -n "$SDK_LISTA" ]; then SDK_NA_LISCIE="tak"; fi
# 6.D112: JEDNO wywołanie `--version` na cały blok, a jego WYNIK — stdout i kod
# wyjścia — niosą dwie zmienne. Zmierzone 10.09.2026 przed zmianą, atrapą liczącą
# swoje wywołania: pin niespełniony **2**, pin spełniony **4**, brak SDK **3**.
# Wpis kolejki mówił o trzech; trzy to liczba MIEJSC w kodzie, a nie wywołań
# w przebiegu, i ani w jednym z trzech stanów nie wychodziła.
#
# To nie jest oszczędność czasu. Cztery wywołania to cztery okazje do rozjazdu:
# gdyby między nimi zmienił się `global.json` albo `PATH` — a `doctor.sh` bywa
# wołany ze skryptu, który to robi — doctor wypisałby zdania opisujące DWA różne
# stany jako jeden. Ta sama rodzina co usterka zamknięta przez 6.D96, tylko
# rozłożona w czasie zamiast w potoku.
#
# `--list-sdks` NIE jest tu łączone z `--version` i to jest wybór, nie przeoczenie:
# to dwa różne pytania i cała 6.D96 na tej różnicy stoi.
DOTNET_WERSJA="$("$DOTNET" --version 2>/dev/null)"
DOTNET_WERSJA_KOD=$?
PIN_NIESPELNIONY="nie"
if [ "$SDK_NA_LISCIE" = "tak" ] && [ "$DOTNET_WERSJA_KOD" -ne 0 ]; then
  PIN_NIESPELNIONY="tak"
fi

if [ "$PIN_NIESPELNIONY" = "tak" ]; then
  # JEDNO zdanie zamiast dwóch sprzecznych. Kontrola jest WYMAGANA, bo w tym stanie
  # `dotnet build` też nie ruszy — środowisko naprawdę nie nadaje się do pracy,
  # tylko przyczyna jest inna niż brak SDK.
  chk_expr_required "dotnet SDK vs pin z global.json ($PIN_SDK)" "false" \
    "SDK SĄ na dysku, ale ŻADNE nie spełnia pinu $PIN_SDK z global.json; \`dotnet --version\` kończy błędem — zmień pin albo doinstaluj tę wersję, NIE instaluj SDK od nowa"
  printf '%s\n' "$SDK_LISTA" | sed 's/^/        na dysku: /'
else
  # Forma WYRAŻENIOWA, bo wynik jest już zapamiętany — `chk_prog_required` wołałby
  # `--version` drugi raz. Obie funkcje wypisują ten sam kształt wiersza
  # (`  ok    <nazwa>` / `  BRAK  <nazwa>  -> <podpowiedź>`), więc wypis nie drgnął.
  chk_expr_required "dotnet SDK" "[ \"$DOTNET_WERSJA_KOD\" -eq 0 ]" "$BRAK_SDK_PODPOWIEDZ"
fi

# Sama obecność `dotnet` nie wystarczy i to jest zmierzone, nie przewidywane.
# Po podniesieniu rdzenia na `net10.0` (04.09.2026) doctor na SDK 8.0.130 wypisywał
# `ok dotnet SDK`, a dwadzieścia wierszy niżej `BLAD dotnet test nie przechodzi`
# z błędem NETSDK1045 — czyli mówił „ok" o tym samym SDK, przez które przed chwilą
# padł. Podpowiedź obiecywała „10.0+", ale nikt tego nie sprawdzał.
#
# Wymagana wersja NIE jest tu wpisana z ręki: czyta się ją z `<TargetFramework>`
# w `src/Sim/Sim.csproj`, czyli z jedynego miejsca, które o niej decyduje. Wpisanie
# jej drugi raz dałoby dwa źródła prawdy i rozjazd przy następnym podniesieniu.
# 6.D96: liczba WYŁĄCZNIE z polecenia, które się powiodło. Potok `--version | cut`
# nie widzi kodu wyjścia pierwszego członu, więc przy niespełnialnym pinie brał `10`
# z pierwszego wiersza WYPISANEJ LISTY SDK i meldował `ok dotnet SDK >= 10 (jest 10)`
# obok `BRAK dotnet SDK` dwa wiersze wyżej.
HAVE_SDK_MAJOR=""
if [ "$DOTNET_WERSJA_KOD" -eq 0 ] && [ -n "$DOTNET_WERSJA" ]; then
  HAVE_SDK_MAJOR="$(printf '%s\n' "$DOTNET_WERSJA" | cut -d. -f1)"
fi
if [ -n "$REQUIRED_TFM" ] && [ -n "$HAVE_SDK_MAJOR" ]; then
  chk_expr_required "dotnet SDK >= $REQUIRED_TFM (jest $HAVE_SDK_MAJOR)" \
    "[ \"$HAVE_SDK_MAJOR\" -ge \"$REQUIRED_TFM\" ]" \
    "src/Sim/Sim.csproj celuje w net${REQUIRED_TFM}.0, a to SDK tego nie zbuduje (NETSDK1045); pobierz nowsze z https://dotnet.microsoft.com/download"

  # Zanim każe cokolwiek pobierać, doctor SZUKA. Podpowiedź wypisuje się wyłącznie
  # wtedy, gdy znaleziony `dotnet` naprawdę zgłasza wersję dostatecznie wysoką —
  # nie na samą obecność pliku. Podpowiedź o SDK, którego tam nie ma, byłaby
  # dokładnie tym samym błędem, tylko w drugą stronę.
  if [ "$HAVE_SDK_MAJOR" -lt "$REQUIRED_TFM" ] && [ -n "$SDK_NA_DYSKU" ] 2>/dev/null; then
    echo "        na dysku JEST nowsze SDK: $SDK_NA_DYSKU"
    echo "        uruchom: export DOTNET_ROOT=$(dirname "$SDK_NA_DYSKU"); export PATH=\"\$DOTNET_ROOT:\$PATH\""
  fi
fi

# PIN Z `global.json`, czyli to samo źródło, z którego bierze wersję `dotnet build`
# — 6.D79. Wersji nie wpisujemy tu z ręki drugi raz: czytana jest z pliku, tak samo
# jak `REQUIRED_TFM` czyta się z `src/Sim/Sim.csproj`.
#
# ZMIERZONE 10.09.2026 na kontenerze tej sesji (jedno SDK: 10.0.401), przez
# podstawianie pinu i czytanie KODU WYJŚCIA `dotnet --version`:
#
#   pin 10.0.401  -> kod 0
#   pin 10.0.402  -> kod 155      (nowsza łatka, której NIE MA na dysku)
#   pin 10.0.301  -> kod 155      (starsze pasmo funkcji)
#   pin 11.0.100  -> kod 155
#
# Dwie rzeczy z tego wynikają i obie były przeze mnie najpierw założone błędnie.
# PIERWSZA: `rollForward: latestPatch` NIE znaczy „każda łatka przejdzie". Znaczy
# „ta wersja albo wyższa łatka W TYM SAMYM paśmie funkcji" — SDK STARSZE od pinu
# jest odrzucane w całości, nie tolerowane.
# DRUGA: przy niespełnialnym pinie `dotnet --version` KOŃCZY BŁĘDEM i wypisuje na
# stdout listę zainstalowanych SDK (`10.0.401 [/root/.dotnet/sdk]`). Kontrola wyżej
# widzi wtedy niezerowy kod i melduje `BRAK dotnet SDK -> zainstaluj` — a SDK JEST,
# nie zgadza się wyłącznie wersja. Ten blok nazywa więc prawdziwą przyczynę, zamiast
# zostawić czytelnika z instrukcją instalowania czegoś, co ma.
# 6.D96: `PIN_SDK` czytany JEST WYŻEJ, przed kontrolami — bo to on rozstrzyga, którą
# z nich w ogóle wypisać. Tutaj zostaje wyłącznie pytanie o łatkę przy pinie
# SPEŁNIONYM; przypadek niespełniony obsługuje jedna kontrola wymagana wyżej,
# zamiast dwóch sprzecznych zdań i WARN-a pod nimi.
if [ -n "$PIN_SDK" ] && [ "$PIN_NIESPELNIONY" = "nie" ]; then
  if [ "$DOTNET_WERSJA_KOD" -eq 0 ] && [ -n "$DOTNET_WERSJA" ]; then
    HAVE_SDK="$DOTNET_WERSJA"
    # `dotnet` wystartował, czyli pin JEST spełniony. Zostaje pytanie, czy tą samą
    # łatką, co CI. Kontrola jest OPCJONALNA, bo wyższa łatka w tym samym paśmie
    # buduje projekt poprawnie — a różne łatki na dwóch maszynach puli to dokładnie
    # to, czego pozycja 6.D79 dotyczy, więc warto je POKAZAĆ.
    chk_expr_optional "dotnet SDK == pin z global.json ($PIN_SDK)" \
      "[ \"$HAVE_SDK\" = \"$PIN_SDK\" ]" \
      "masz $HAVE_SDK, a global.json pinuje $PIN_SDK — wyższa łatka w tym samym paśmie zbuduje projekt, ale CI stoi na $PIN_SDK"
  fi
fi

echo ""
echo "Wymagane dopiero przez konkretne zadania:"
# Blender bywa instalowany poza PATH: `tools/ci/blender_install.sh` rozpakowuje
# przypiętą wersję do katalogu poza workspace, bo `git clean -ffdx` z checkoutu
# skasowałby ją przy każdym przebiegu. `BLENDER_BIN` jest tą samą zmienną, której
# używają skrypty CI, więc doctor pyta o to samo co CI, a nie o coś innego.
BLENDER_CMD="${BLENDER_BIN:-blender}"
chk_prog_optional "blender ($BLENDER_CMD)" \
  "wymagany od T-010/T-2xx; ustaw BLENDER_BIN albo uruchom tools/ci/blender_install.sh" \
  "$BLENDER_CMD" --version
if "$BLENDER_CMD" --version >/dev/null 2>&1; then
  chk_prog_optional "blender headless" "napraw tryb headless przed T-010" \
    "$BLENDER_CMD" --background --python-expr pass
  # Wersja NIE jest drobiazgiem informacyjnym. Rozstrzyga, która generacja EEVEE stoi
  # za nazwą `BLENDER_EEVEE`, a rendery z legacy i z Next nie są porównywalne. Doctor
  # porównuje z pinem z `tools/ci/blender-version.txt`, czyli z tym samym numerem,
  # którego wymaga CI — inaczej „ok" u siebie i czerwona bramka w CI to ten sam stan.
  PINNED_BLENDER="$(sed -n 's/^version=//p' tools/ci/blender-version.txt 2>/dev/null)"
  HAVE_BLENDER="$("$BLENDER_CMD" --version 2>/dev/null | sed -n '1s/^Blender \([0-9.]*\).*/\1/p')"
  if [ -n "$PINNED_BLENDER" ]; then
    chk_expr_optional "blender w wersji z pinu ($PINNED_BLENDER, jest $HAVE_BLENDER)" \
      "[ \"$HAVE_BLENDER\" = \"$PINNED_BLENDER\" ]" \
      "CI wymaga $PINNED_BLENDER; uruchom tools/ci/blender_install.sh i ustaw BLENDER_BIN"
  fi
fi
# Godot bywa instalowany poza PATH (dystrybucje nie pakują wersji mono, a workflow
# `godot-first-run.yml` rozpakowuje ją do własnego katalogu). `GODOT_BIN` jest tą samą
# zmienną, której używa workflow, więc doctor pyta o to samo co CI, a nie o coś innego.
GODOT_CMD="${GODOT_BIN:-godot}"
chk_prog_optional "godot ($GODOT_CMD)" \
  "wymagany od T-400; ustaw GODOT_BIN, jeśli silnik jest poza PATH" \
  "$GODOT_CMD" --version

# `--version` NIE dotyka mono — kończy proces, zanim silnik sięgnie po .NET, więc
# przechodzi identycznie z `DOTNET_ROOT` i bez niego. Zmierzone 06.09.2026
# (docs/23-environment.md §4.1): bez `DOTNET_ROOT` i bez `dotnet` w PATH ten sam
# binarny plik, który przed chwilą podał wersję, przy `--path src/Game` pada
# w niecałą sekundę (`Failed to load hostfxr`, log mówi signal 11, powłoka daje
# kod 134). ZDANIE O ZAWIESZENIU BEZ WYPISU ZOSTAŁO STĄD ZDJĘTE 09.09.2026, a nie
# przepisane obok: 6.D21 próbowała odtworzyć je sześcioma wariantami brakującego
# zestawu, 6.D24 pięcioma wariantami brakującej biblioteki natywnej, i żaden
# z jedenastu nie zawiesił procesu ani nie zamilkł (0,19–2,69 s, wyjście za każdym
# razem). Sonda na SAMĄ obecność `--version` nic z tego nie łapie, więc
# to osobne sprawdzenie: `DOTNET_ROOT` wskazujący katalog z `host/fxr/*/libhostfxr.so`
# (dokładnie ten, który stawia `dotnet-install.sh`), albo `dotnet` osiągalny przez
# goły `command -v` — silnik próbuje TO jako drugie, dopiero gdy `DOTNET_ROOT` się
# nie zgadza, i awaria wygląda wtedy identycznie jak brak zmiennej w ogóle.
#
# TA KONTROLA JEST PRZEPISANA 09.09.2026 (6.D60), A NIE DOPISANA OBOK. Poprzednia
# pytała `find "$DOTNET_ROOT/host/fxr" -name 'libhostfxr.so'`, czyli o OBECNOŚĆ
# PLIKU O DANEJ NAZWIE, i mówiła `ok` przy CZTERECH z pięciu zepsuć, po których
# Godot pada kodem 134 w 0,19–0,35 s (6.D24, `reports/6d24-biblioteka-natywna.md`
# §5): `libhostfxr.so` obcięty do 200 B, `libcoreclr.so` usunięty, `libcoreclr.so`
# obcięty, `libhostpolicy.so` usunięty. Nazwa pliku nie mówi ani o jego
# kompletności, ani o dwóch pozostałych bibliotekach z komunikatu silnika.
# Dziś kontrolą jest PRAWDZIWE ŁADOWANIE wszystkich trzech (`dlopen` przez
# `tools/ci/dotnet_native_probe.py`) — bez progu, który trzeba by zgadnąć, bo
# obcięcie do 200 B zostawia poprawny nagłówek ELF.
if "$GODOT_CMD" --version >/dev/null 2>&1; then
  # Katalog, który spróbuje SILNIK, w jego kolejności: najpierw `DOTNET_ROOT`,
  # dopiero potem `dotnet` z gołego `command -v`.
  HOSTFXR_ROOT=""
  if [ -n "${DOTNET_ROOT:-}" ]; then
    HOSTFXR_ROOT="$DOTNET_ROOT"
  elif command -v dotnet >/dev/null 2>&1; then
    HOSTFXR_ROOT="$(dirname "$(readlink -f "$(command -v dotnet)")")"
  fi
  HOSTFXR_POWOD="$(python3 tools/ci/dotnet_native_probe.py "$HOSTFXR_ROOT" 2>&1)"
  HOSTFXR_OK=$?
  chk_expr_optional "godot .NET hostfxr" "[ $HOSTFXR_OK -eq 0 ]" \
    "$HOSTFXR_POWOD — ustaw DOTNET_ROOT na kompletny katalog SDK (np. \$HOME/.dotnet) albo dodaj dotnet do PATH, inaczej Godot mono pada przy starcie sceny z C# w niecałą sekundę: log pisze Failed to load hostfxr i signal 11, a powłoka widzi kod 134 (zmierzone 06.09 i 09.09.2026, 11 wariantów)"
fi

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

#: Ile wierszy `FAIL` wypisać z logu zestawu. Sufit, a nie wybór estetyczny:
#: przebieg, w którym padł JEDEN moduł, potrafi dać kilkadziesiąt wierszy `FAIL`,
#: a wypis ma zmieścić się w logu joba CI i w `build/t010/report.txt`.
WYCIAG_FAILI=${MBXL_WYCIAG_FAILI:-40}

# WYPIS ZAMIAST ODESŁANIA DO PLIKU, KTÓREGO NIKT NIE MA — 6.D241, 16.09.2026.
# Ten blok jest PRZEPISANY, a nie dopisany obok: poprzednia wersja kończyła się na
# `BLAD  testy nie przechodzą — zobacz $log_file` i to było zdanie prawdziwe wyłącznie
# na maszynie, na której się stało.
#
# W CI plik `$log_file` leży poza workspace i NIE JEST zbierany. Zmierzone 16.09.2026
# na dwóch przebiegach `blender-smoke` (joby 104696967107 i 104702701634, maszyna
# `docker-runner-04`, dwie RÓŻNE gałęzie): jedyny ślad po padniętym zestawie w całym
# logu joba to ten jeden wiersz, a artefakt ma "1 file uploaded" i 1393 / 1394 bajtów,
# czyli sam `report.txt`. Nazwy padającego testu nie da się stamtąd odzyskać niczym.
#
# To jest ta sama rodzina, którą ten projekt tropi od 6.D27: KOMUNIKAT NIE JEST
# WYNIKIEM. Doctor melduje porażkę i odsyła do dowodu, którego czytający nie ma.
#
# DLACZEGO WYCIĄG, A NIE `tail`. Zmierzone na zielonym przebiegu z tego samego dnia:
# log ma **2836 wierszy**, a wiersz `N/M przeszło` stoi na **2707**, czyli **129 od
# końca** — za nim idzie wyłącznie lista czasów 126 modułów. `tail -n 100` nie sięga
# więc nawet do podsumowania, a wiersze `FAIL` są rozrzucone po CAŁEJ długości, bo
# zestaw wypisuje je w trakcie pętli po modułach. Ogon jest tu złym przyrządem i to
# jest liczba, nie wrażenie.
wypisz_wyciag_z_logu() {
  plik="$1"
  # Bez potoku do `head`: `set -o pipefail` w doctorze nie stoi, ale ten sam wyścig
  # SIGPIPE opisany przy sondzie narzędzi (`.github/actions/probe-tools`) nie ma tu
  # po co powstawać. `grep` bez trafienia kończy kodem 1, stąd `|| true` — inaczej
  # podstawienie oddaje kod, którego nikt nie czyta, i cichy pusty napis.
  faile="$(grep -E '^[[:space:]]*FAIL ' "$plik" 2>/dev/null || true)"
  if [ -z "$faile" ]; then
    echo "        w logu nie ma ANI JEDNEGO wiersza FAIL — zestaw padł POZA ciałem testu"
    echo "        (błąd importu, bramka asercji albo przerwany przebieg); ogon logu:"
    tail -n 5 "$plik" 2>/dev/null | sed 's/^/        /'
  else
    echo "        wiersze FAIL ($(printf '%s\n' "$faile" | wc -l | tr -d ' ') szt., pierwsze $WYCIAG_FAILI):"
    printf '%s\n' "$faile" | sed -n "1,${WYCIAG_FAILI}p" | sed 's/^/        /'
  fi
  podsumowanie="$(grep -E '[0-9]+/[0-9]+ przeszło|^  RAZEM ' "$plik" 2>/dev/null || true)"
  if [ -n "$podsumowanie" ]; then
    echo "        podsumowanie:"
    printf '%s\n' "$podsumowanie" | sed 's/^/        /'
  else
    echo "        w logu nie ma wiersza 'N/M przeszło' ani 'RAZEM' — przebieg nie doszedł do końca"
  fi
}

if [ "$RUN_TESTS" -eq 1 ]; then
echo ""
echo "Testy narzędzi:"
log_file="${TMPDIR:-/tmp}/mbxl_tests.log"
if python3 tools/tests/test_all.py >"$log_file" 2>&1; then
  echo "  ok    $(grep -o "[0-9]*/[0-9]* przeszło" "$log_file")"
else
  echo "  BLAD  testy nie przechodzą — wyciąg z $log_file:"
  wypisz_wyciag_z_logu "$log_file"
  required_bad=$((required_bad + 1))
fi

echo ""
echo "Testy rdzenia symulacji:"
# Rdzeń nie ma zależności NuGet, ale testy mają trzy pakiety — pierwsze uruchomienie
# na czystej maszynie wymaga sieci na czas `restore`. Później liczy się z cache.
# DOCTOR NIE MOŻE MÓWIĆ „testy nie przechodzą", KIEDY TESTY W OGÓLE NIE POBIEGŁY.
#
# Zmierzone 05.09.2026, dwa razy niezależnie: na maszynie, gdzie `dotnet` z `PATH`
# to 8.0.130, a 10.0.400 stoi obok w `$HOME/.dotnet`, doctor kończył twardym
# `BLAD  dotnet test nie przechodzi`. W logu nie było ani jednego niezaliczonego
# testu — było `NETSDK1045: The current .NET SDK does not support targeting
# .NET 10.0`. Testy nie padły; one się nie odbyły, bo nie było czym zbudować.
#
# To jest ta sama rodzina defektu, którą to repozytorium tropi w kodzie: KOMUNIKAT
# NIE JEST WYNIKIEM. „Testy nie przechodzą" wysyła czytającego w kod symulacji,
# a usterka leży w `PATH`. Dwa raporty z 05.09.2026 zgłosiły to jako blokadę
# środowiska; oba się myliły co do przyczyny właśnie przez ten komunikat.
#
# Rozstrzygnięcie: gdy SDK nie umie zbudować docelowej wersji, testy się NIE
# uruchamiają, a doctor mówi wprost, czego brakuje. Nadal liczy się to jako błąd
# wymagany — środowisko jest niesprawne — ale powód jest prawdziwy.
if ! command -v "${DOTNET_BIN:-dotnet}" >/dev/null 2>&1; then
  echo "  pomijam — brak dotnet"
elif [ -n "$REQUIRED_TFM" ] && [ -n "$HAVE_SDK_MAJOR" ] \
     && [ "$HAVE_SDK_MAJOR" -lt "$REQUIRED_TFM" ] 2>/dev/null; then
  echo "  BLAD  testy NIE URUCHOMIONE — SDK ${HAVE_SDK_MAJOR}.x nie zbuduje net${REQUIRED_TFM}.0 (NETSDK1045)"
  echo "        to nie jest niezaliczony test, tylko brak czym zbudować; patrz podpowiedź wyżej"
  required_bad=$((required_bad + 1))
else
  sim_log="${TMPDIR:-/tmp}/mbxl_sim_tests.log"
  if "${DOTNET_BIN:-dotnet}" test tests/Sim.Tests --nologo -v q >"$sim_log" 2>&1; then
    sim_passed=$(grep -oE "Passed: +[0-9]+" "$sim_log" | tail -1 | grep -oE "[0-9]+")
    sim_total=$(grep -oE "Total( tests)?: +[0-9]+" "$sim_log" | tail -1 | grep -oE "[0-9]+")
    echo "  ok    ${sim_passed}/${sim_total} przeszło"
  elif grep -q "NETSDK1045" "$sim_log" 2>/dev/null; then
    # Sonda wersji wyżej mogła nie zadziałać (np. `dotnet --version` milczy),
    # a mimo to build padł dokładnie na tym. Log jest tu rozstrzygający.
    echo "  BLAD  testy NIE URUCHOMIONE — build padł na NETSDK1045, zobacz $sim_log"
    required_bad=$((required_bad + 1))
  else
    echo "  BLAD  dotnet test nie przechodzi — zobacz $sim_log"
    required_bad=$((required_bad + 1))
  fi
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
  # GDY NIE MA ODBLOKOWANEGO ZADANIA, DOCTOR MA WSKAZAĆ KOLEJKĘ, A NIE TABELĘ ZALEŻNOŚCI.
  #
  # `CLAUDE.md` §8 mówi wprost: „Zatrzymanie się z powodu pustej kolejki nie jest
  # poprawnym wynikiem […] agent bierze następną pozycję z fazy 5 lub 6". Poprzednia
  # wersja tej gałęzi odsyłała do tabeli „Co blokuje co", czyli do miejsca, które mówi,
  # CZEGO NIE DA SIĘ zrobić — dokładnie odwrotnie niż konstytucja.
  #
  # Zobaczyliśmy to dopiero 05.09.2026, po odhaczeniu T-212 (#240): do tego dnia zawsze
  # istniał jakiś wpis `### [ ]` i ta gałąź nigdy się nie wykonywała. Nie była martwym
  # kodem — była kodem, którego nikt nie widział, bo poprzedzał go stan nieaktualny.
  #
  # Pozycja jest brana z pierwszego wiersza kolejki faz 5 i 6, tym samym prefiksem
  # (`5.` albo `6.`), którego używa `tools/tests/test_backlog.py` jako `QUEUE_PREFIXES`.
  # WYBÓR IDZIE TYM SAMYM CZYTNIKIEM, KTÓRYM LICZY SIĘ ZAPAS — i to jest poprawka
  # z pomiaru (09.09.2026), nie porządki. Poprzednia wersja miała tu WŁASNY wzorzec
  # `^\| [56]\.[0-9]+ \|`, czyli drugą kopię reguły „co jest pozycją kolejki". Kopia
  # rozjechała się z oryginałem: wzorzec łapał **8 wierszy i ani jednej pozycji
  # otwartej**, bo wszystkie 34 otwarte mają w numerze literę (`6.D67`, `6.B5`), a te
  # osiem to prace domknięte. Gałąź była nieosiągalna, dopóki w rozpisce stał
  # niezablokowany wpis `### [ ]`; po jego zablokowaniu (T-112, 09.09.2026) doctor
  # zaczął wskazywać jako „następne zadanie" pozycję z adnotacją ZROBIONE.
  # To jest dokładnie ta klasa, dla której powstał `tools/tests/test_next_task.py`.
  queue_item=""
  if [ -f docs/TASKS.md ] && [ -f tools/tests/test_backlog.py ]; then
    queue_item=$(python3 -c 'import io, re, sys; sys.path.insert(0, "tools/tests"); import test_backlog as B; t = io.open("docs/TASKS.md", encoding="utf-8").read(); o = B.open_items(t); w = B.queue_row(t, o[0]) if o else ""; m = re.match(r"\| \S+ \| \*\*([^*]+)\*\*", w) if w else None; print(f"{o[0]} · {m.group(1).strip()}" if m else (o[0] if o else ""))' 2>/dev/null)
  fi
  # LICZBA POZYCJI KOLEJKI JEST LICZONA TUTAJ, A NIE PRZEPISANA DO PROZY.
  #
  # Do 09.09.2026 stała w `docs/TASKS.md` jako literał („trzymają 31 pozycji") i starzała
  # się po cichu: zmierzone na czterdziestu ostatnich commitach dotykających tego pliku
  # — licznik zmienił wartość w 27 z nich, a 7 z tych czterdziestu to wciągnięcia `main`
  # do równoległej gałęzi, czyli miejsca na konflikt semantyczny przy dwóch niezależnych
  # podniesieniach tej samej liczby. Pytanie „czy pracy jest dużo" ma więc odpowiedź
  # liczoną przy każdym uruchomieniu, z tego samego `open_items`, którego używa zapadka
  # zapasu — nie z drugiej kopii reguły. Pilnuje tego `tools/tests/test_next_task.py`.
  queue_count=""
  queue_free=""
  queue_blocked=""
  if [ -f docs/TASKS.md ] && [ -f tools/tests/test_backlog.py ]; then
    # 6.D95: TRZY liczby zamiast jednej, i wszystkie z pliku. Do 10.09.2026 stała tu
    # jedna, a obok niej napis STAŁY „żadna nie wymaga decyzji właściciela" — zdanie
    # o zbiorze wypowiadane bez zajrzenia do zbioru, w chwili gdy w policzonej kolejce
    # stała 6.D53 z polem „Zależy od" brzmiącym dosłownie „decyzji właściciela".
    # Ta sama rodzina co 6.D27: przyrząd meldujący sprawdzenie, którego nie zrobił.
    queue_count=$(python3 -c 'import io, sys; sys.path.insert(0, "tools/tests"); import test_backlog as B; print(len(B.open_items(io.open("docs/TASKS.md", encoding="utf-8").read())))' 2>/dev/null)
    queue_free=$(python3 -c 'import io, sys; sys.path.insert(0, "tools/tests"); import test_backlog as B; print(len(B.do_wziecia(io.open("docs/TASKS.md", encoding="utf-8").read())))' 2>/dev/null)
    queue_blocked=$(python3 -c 'import io, sys; sys.path.insert(0, "tools/tests"); import test_backlog as B; print(", ".join(B.czeka_na_wlasciciela(io.open("docs/TASKS.md", encoding="utf-8").read())))' 2>/dev/null)
  fi
  if [ -n "$next_task" ]; then
    echo "  Baza projektu jest gotowa. Następne zadanie: $next_task"
  elif [ -n "$queue_item" ]; then
    echo "  Baza projektu jest gotowa. Rozpiska nie ma odblokowanego zadania z numerem,"
    echo "  więc zgodnie z CLAUDE.md §8 bierzesz pierwszą pozycję z kolejki faz 5 i 6:"
    echo "    $queue_item"
  else
    echo "  Baza projektu jest gotowa, ale KOLEJKA JEST PUSTA — a to znaczy, że pierwszym"
    echo "  zadaniem jest jej uzupełnienie (CLAUDE.md §8), nie zatrzymanie się."
  fi
  if [ -n "$queue_count" ]; then
    if [ -n "$queue_blocked" ]; then
      echo "  Kolejka faz 5 i 6 ma $queue_count pozycji, z czego $queue_free do wzięcia od ręki."
      echo "  Na decyzję właściciela czeka: $queue_blocked — tej nie bierz."
    else
      echo "  Kolejka faz 5 i 6 ma $queue_count pozycji do wzięcia, żadna nie wymaga decyzji właściciela."
    fi
  fi
  if [ "$optional_bad" -gt 0 ]; then echo "  $optional_bad narzędzi opcjonalnych brakuje; instaluj je dopiero przed zadaniem, które ich wymaga."; fi
else
  echo "  $required_bad wymaganych pozycji do naprawienia przed pracą."
fi
echo ""
exit "$required_bad"
