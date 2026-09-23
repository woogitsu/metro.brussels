# 6.D367 — paczka treningu na Windows x64

**Zmierzone 23.09.2026 na commicie:** `c4ef8a153b0ef768dd69c2a7f049904ece78d16d`

Zasoby wygenerowano skryptem
`tools/dev/prepare-playable.sh` z Blenderem 5.2.1 LTS. Eksport wykonano
Godotem 4.7.2 stable mono z szablonami tej samej wersji i SDK .NET 10.0.401.

## Wynik eksportu

`PACZKA_SYSTEM=windows bash tools/release/package-playable.sh build/paczka-win build/t400`
zakończyło się kodem 0. `file` podał:

```text
MetroBXL.exe: PE32+ executable for MS Windows 5.02 (GUI), x86-64 (stripped to external PDB), 12 sections
```

Paczka zajęła 191 MB, zawierała 189 plików `.dll` oraz 54 pliki zasobów.
W logu eksportu było 0 wierszy `WARNING` i 0 wierszy `ERROR`.
README paczki podawało `MetroBXL.exe` jako polecenie uruchomienia.

## Uruchomienie na Windows

Paczka została rozpakowana na Windows x64 bez środowiska developerskiego.
`MetroBXL.exe --headless --version` wypisał:

```text
4.7.2.stable.mono.official.ed1daf0bf
```

`MetroBXL.exe --headless -- --telemetry=smoke.csv --steps-per-frame=600`
zakończył się kodem 0 i zapisał 321 wierszy telemetrii, 32 757 bajtów.
Ostatni wiersz ma krok 38194, czas symulacji 318,2833 s i prędkość 0.
Ta sama komenda uruchomiona z domyślnej paczki Linux dała plik o identycznym
SHA-256:

```text
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4
```

## Test i granica odbioru

Na Linuksie `python3 tools/tests/test_all.py test_player_package.py test_backlog.py`
dało `43/43 przeszło`. Kontrola negatywna zmieniła nazwę pliku Windows z `.exe`
na `.bad`: test pakowania dał `5/6 przeszło`. Druga zmieniła nazwę presetu
`Windows Desktop`: także dała `5/6`. Po obu próbach pliki źródłowe wróciły do
poprzednich sum. Ręczny playtest z widocznym oknem, klawiaturą i oceną obrazu pozostaje
do wykonania — przebieg headless go nie zastępuje.
