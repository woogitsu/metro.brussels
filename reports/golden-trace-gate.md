# Wzorcowy ślad jako bramka CI — i liczba, która przestała być prawdą

**Zmierzone 06.09.2026 na commicie:** `51d324a`

Środowisko pomiaru: SDK .NET 10.0.400, runtime `Microsoft.NETCore.App` **10.0.11**.
Rozróżnienie nie jest pedanterią; §3 pokazuje, dlaczego.

## 1. Skąd wzięła się ta pozycja

Commit `90a8c31` („T-320: skład krokowany z zewnątrz, ślad identyczny co do bajtu")
udowodnił, że refaktor niczego nie zmienił, porównując ślad **co krok** na sześciu
osiach. Podał tabelę i sumę **453 107 wierszy**, i kontrolę negatywną metody: „próg
hamowania przesunięty o 0,1 % daje rozjazd **w wierszu 2910** pliku L1_A".

Porównanie zostało wykonane **raz, ręcznie**, i od tamtej pory nie chodziło. Liczb
453 107 i 2910 nie ma w żadnym pliku `reports/` ani `docs/` — stoją wyłącznie w treści
tamtego commita.

## 2. Pierwszy pomiar: liczba nie jest już prawdziwa

```
$ for AXIS in L1_A L1_B L2_E L5_C L5_D L6_F; do
      dotnet run --project src/Sim.Runner -c Release --no-build -- line \
          --axis "data/track/$AXIS.json" --limit-kmh 72 --exchange-s 20 \
          --trace "build/trace/$AXIS.csv"
  done
$ wc -l build/trace/*.csv
  101873 build/trace/L1_A.csv
   75442 build/trace/L1_B.csv
  144073 build/trace/L2_E.csv
   77256 build/trace/L5_C.csv
   56733 build/trace/L5_D.csv
   60430 build/trace/L6_F.csv
  515807 total
```

| oś | `90a8c31` | 06.09.2026 | Δ | stacji | Δ na postój |
|---|---:|---:|---:|---:|---:|
| L1_A | 89 333 | 101 873 | +12 540 | 12 | **1140** |
| L1_B | 66 322 | 75 442 | +9 120 | 9 | **1140** |
| L2_E | 125 833 | 144 073 | +18 240 | 17 | **1140** |
| L5_C | 68 136 | 77 256 | +9 120 | 9 | **1140** |
| L5_D | 49 893 | 56 733 | +6 840 | 7 | **1140** |
| L6_F | 53 590 | 60 430 | +6 840 | 7 | **1140** |
| **razem** | **453 107** | **515 807** | **+62 700** | | |

Różnica wynosi **dokładnie 1140 wierszy na każdy postój**, na wszystkich sześciu osiach,
bez ani jednego wyjątku. Przy kroku 1/120 s to **9,5 s na postój**. Regularność tej
klasy nie jest szumem zmiennoprzecinkowym — mówi, że zmienił się **kształt postoju**,
a odcinki jazdy zostały nietknięte.

Rozkład dzisiejszego postoju, odczytany z kolumny `door` śladu L5_D (6 postojów):

| faza drzwi | wierszy | sekund |
|---|---:|---:|
| `Unlocking` | 360 | 3,00 |
| `Opening` | 1440 | 12,00 |
| `Open` | 14 400 | 120,00 |
| `ClosingWarning` | 2160 | 18,00 |
| `Closing` | 1800 | 15,00 |
| `Checking` | 360 | 3,00 |
| **razem poza `Closed`** | **20 520** | **171,00** |

Czyli **28,5 s na postój** = 8,5 s faz drzwi (`DoorCycle.MinimumDwellSeconds`)
+ 20 s wymiany pasażerów. Tabela z `90a8c31` odpowiada postojowi **19,0 s**.

## 3. Drugi pomiar: to nie `src/Sim` się zmieniło

Zanim uznać różnicę za regres rdzenia, trzeba było sprawdzić rzecz najprostszą:
**co robi drzewo commita referencyjnego, uruchomione dzisiaj.**

```
$ git worktree add --detach /tmp/wt-bisect 90a8c31
$ cd /tmp/wt-bisect && dotnet build src/Sim.Runner -c Release
  … Microsoft.NETCore.App 8.0.0 nie jest zainstalowany
$ DOTNET_ROLL_FORWARD=LatestMajor dotnet run --project src/Sim.Runner -c Release \
      --no-build -- line --axis data/track/L5_D.json --limit-kmh 72 --exchange-s 20 \
      --trace build/trace/L5_D.csv
$ wc -l < build/trace/L5_D.csv
56733
```

**Drzewo `90a8c31` daje dziś 56 733 wiersze — tyle, co `main`, a nie 49 893 z własnej
tabeli.** Źródło się nie zmieniło. Zmieniło się środowisko uruchomieniowe: tamten
przebieg szedł na .NET 8, ten idzie na .NET 10.

Potwierdza to przegląd commitów między `90a8c31` a `main` dotykających `src/Sim/Train/`,
`src/Sim/Physics/` i `src/Sim.Runner/` — każdy zbudowany i uruchomiony na osi L5_D:

```
ba93903 56733  .NET 8 -> .NET 10 LTS, telemetria i zrzuty identyczne co do bajtu
8f2d118 BLAD-run  T-320: LineCore — wiele składów na jednym zegarze
dbd9456 56733  Merge remote-tracking branch 'origin/main' into w122
…            (osiemnaście dalszych commitów, każdy 56733)
914fb9f 56733  Kabina pod sygnalizacją: człowiek prowadzi, ATP naprawdę hamuje
```

Pierwszy commit po referencyjnym już daje dzisiejszą liczbę. Jego treść brzmi
„telemetria i zrzuty **identyczne co do bajtu**" — i dla `line --trace` to zdanie
nie było sprawdzone. Czego dotyczyło (telemetrii `drive`? zrzutów z silnika?), commit
nie mówi.

**Tego raportu to nie naprawia i nie ma prawa naprawiać** — pole „Poza zakresem"
pozycji 6.D1 zabrania zmian w `src/Sim`, a tu i tak nie ma czego zmieniać: różnica nie
pochodzi ze źródła. Zapisuję ją jako to, czym jest: **wniosek projektowy dla samej
bramki**, §5.

### 3a. Czego ten pomiar NIE rozstrzyga

`DOTNET_ROLL_FORWARD=LatestMajor` uruchamia **stary kod na nowym runtime**. Pokazuje
więc, że przy jednym runtime stare i nowe źródło dają to samo — czyli że różnicy nie
zrobiło źródło. **Nie pokazuje**, czy 49 893 dałoby się odtworzyć na .NET 8: do tego
trzeba runtime 8.0, którego w tym środowisku nie ma, a repozytorium jest przypięte
do .NET 10 (`tools/tests/test_dotnet_version.py`). Zostaje więc drugie wyjaśnienie,
którego nie umiem wykluczyć: **tamten przebieg mógł iść z innymi argumentami.**
Treść `90a8c31` **nie zapisuje polecenia**, którym powstała jego tabela — a postój
19,0 s wychodzi także przy `--exchange-s 10,5`.

I to jest najkrótszy możliwy argument za istnieniem tej bramki: **liczba referencyjna
bez zapisanego polecenia i bez zapisanego środowiska nie daje się sprawdzić.** Nie
dlatego, że ktoś się pomylił — dlatego, że nie ma czego z czym porównać.

## 4. Trzeci pomiar: gdzie mieszkają wzorce

Pole „Poza zakresem" pozycji zostawiało to do rozstrzygnięcia **pomiarem**:

```
$ du -cb build/trace/*.csv | tail -1
33556553   ->  32,0 MiB
```

`CLAUDE.md` §4.8 zabrania komitować plików > 10 MB, a sam L2_E ma 9 413 882 bajty —
pod limitem o włos, ale sześć plików to 32,0 MiB w repozytorium przy każdej zmianie
rdzenia. **Pełny wzorzec w repo odpada**, tak jak przewidywała pozycja.

Wzorzec jest więc **parą**, i obie części robią co innego:

| część | rola | rozmiar |
|---|---|---:|
| suma SHA-256 całego pliku, w manifeście | **WYKRYWA** rozjazd, co do bajtu | 6 sum |
| próbka co 100 wierszy, w `tests/data/golden-trace/` | **LOKALIZUJE** go | 332 KiB |

Sama próbka przepuściłaby rozjazd między swoimi wierszami. Sama suma nie powie, gdzie.
Dopiero para daje jedno i drugie, mieszcząc się w repozytorium: **515 807 wierszy
wobec 5167 wierszy próbki, stosunek 1:100**.

| oś | wierszy | bajtów | SHA-256 (16 znaków) | próbka |
|---|---:|---:|---|---:|
| L1_A | 101 873 | 6 610 778 | `11d298315379ba7f` | 1020 |
| L1_B | 75 442 | 4 910 123 | `b7f1d3f9fa81a5f5` | 756 |
| L2_E | 144 073 | 9 413 882 | `4118286112364004` | 1442 |
| L5_C | 77 256 | 5 021 362 | `a7687ee63b113db0` | 774 |
| L5_D | 56 733 | 3 686 193 | `c2fa6049d0ed688b` | 569 |
| L6_F | 60 430 | 3 914 215 | `a443e8507d59e174` | 606 |

**Czego bramka nie umie, zapisane, a nie przemilczane.** Gdy rozjazd wypadnie MIĘDZY
wierszami próbki, narzędzie poda **przedział** o długości 100 wierszy, a nie pojedynczy
numer. Dokładny numer daje `Sim.Runner compare` na dwóch pełnych plikach — i dlatego
workflow przy porażce wystawia świeże ślady jako **artefakt**. Bez tego „przedział
2903..3002" byłby końcem śledztwa zamiast jego początkiem.

### 4a. Koszt bramki

| krok | czas |
|---|---:|
| sześć przebiegów `line --trace` (bez budowania) | **12,7 s** |
| sprawdzenie sześciu śladów wobec wzorca | **0,17 s** |

## 5. Wersja runtime jest częścią wzorca, nie metadanymi

To jest wniosek z §3 i najważniejsza decyzja projektowa tej pozycji. Bramka, która
przybija bajty, a nie zapisuje środowiska, po następnej podmianie środowiska zaświeci
i **powie nieprawdę o przyczynie** — dokładnie tak, jak dzisiejszy rozjazd wygląda na
regres rdzenia, którym nie jest.

Manifest zapisuje więc runtime, a bramka porównuje **rodzinę** (`10.0`), nie łatkę:

- workflow pina `dotnet-version: '10.0.x'`, czyli **łatkę i tak puszcza**. Bramka
  żądająca zgodności co do łatki świeciłaby na czerwono przy pierwszej aktualizacji
  runtime na maszynie właściciela;
- rodzina łapie to, co się naprawdę zdarzyło (.NET 8 → .NET 10), i nie łapie tego,
  czego pin nie trzyma;
- gdy ślad **się rozjedzie**, a łatka jest inna, bramka **dopisuje to jako uwagę** —
  bo to pierwsza rzecz, o której trzeba wiedzieć, zamiast szukać w rdzeniu zmiany,
  której tam nie ma.

Mierzona jest wersja **runtime** (`dotnet --list-runtimes`), nie SDK (`dotnet --version`).
W tym środowisku pierwsza to **10.0.11**, druga **10.0.400** — dwie różne liczby,
a bajty produkuje pierwsza.

## 6. Kontrole negatywne — wykonane

### 6.1 Próg hamowania przesunięty o 0,1 %

To ta sama kontrola, którą wykonano ręcznie przy `90a8c31`. Mutacja w `LineDrive.cs`:
`_trigger = settings.BrakeUsageFraction * controller.ServiceBrakeMps2 * 1.001`,
przebieg sześciu osi, bramka:

```
[SLAD] ROZJAZD z wzorcem:
  L1_A: ślad rozjechał się z wzorcem
  wzorzec: 101873 wierszy, 6610778 bajtów, 11d298315379ba7f
  świeży:  101849 wierszy, 6606423 bajtów, 0febff49a2d79a95
  pierwszy rozjazd w przedziale wierszy 2903..3002 pliku; wiersz 3002 próbki:
    wzorzec: 25.008333333333333,328.806359975639,19.741047439231668,0.5812499999999989,0,0.9423705602288235,Closed
    świeży:  25.008333333333333,328.8082559029353,19.74588657358634,0.574999999999999,0,0.9428444323088443,Closed
  L1_B: … pierwszy rozjazd w przedziale wierszy 3003..3102
  L2_E: … pierwszy rozjazd w przedziale wierszy 3703..3802
  L5_C: … pierwszy rozjazd w przedziale wierszy 3703..3802
  L5_D: … pierwszy rozjazd w przedziale wierszy 3703..3802
kod wyjścia: 1
```

**Przedział `2903..3002` na osi L1_A zawiera wiersz 2910** — ten sam, który podała
kontrola ręczna przy `90a8c31`. Metoda i jej wynik przeżyły zmianę środowiska, która
przesunęła same liczby wierszy; rozjazd nadal zaczyna się w tym samym miejscu.

Mutacja cofnięta, `git diff --stat src/Sim/` pusty, przebieg powtórzony:
`[SLAD] sześć osi zgadza się z wzorcem co do bajtu`.

### 6.2 Jedno pole w jednym wierszu

Zmiana jednego znaku w wierszu 2910 pliku L5_D — czyli **między** wierszami próbki:

```
  L5_D: ślad rozjechał się z wzorcem
  wzorzec: 56733 wierszy, 3686193 bajtów, c2fa6049d0ed688b
  świeży:  56733 wierszy, 3686193 bajtów, 1daa7fbfe6cce1f3
  próbka co 100 wierszy się zgadza, więc rozjazd leży MIĘDZY jej wierszami — dokładny
  numer da `Sim.Runner compare` na pełnym pliku wystawionym przez workflow jako artefakt
kod wyjścia: 1
```

Ta sama liczba wierszy, ta sama liczba bajtów, **inna suma** — i bramka mówi wprost,
czego nie wie. To jest ta połowa wzorca, której próbka sama by nie dała.

### 6.3 Wzorzec z innej rodziny runtime

```
  runtime .NET to 10.0.11 (rodzina 10.0), a wzorzec powstał na 8.0.11 (rodzina 8.0) —
  rozjazd śladu po zmianie RODZINY środowiska NIE jest regresem rdzenia i bramka nie
  ma prawa udawać, że jest.
kod wyjścia: 1
```

### 6.4 Brak `dotnet` w PATH — i błąd, który ta kontrola znalazła

Pierwsza wersja narzędzia wstawiała w miejsce wersji **komunikat błędu**, więc brak
`dotnet` zgłaszał się jako „rozjazd RODZINY środowiska": zdanie formalnie prawdziwe
i **mylące co do przyczyny**. Znalazła to kontrola uruchomiona przypadkiem bez PATH.
Po poprawce:

```
  nie umiem odczytać wersji runtime .NET (`dotnet --list-runtimes`) — to NIE jest
  rozjazd śladu, to brak narzędzia. Wzorzec powstał na 10.0.11.
kod wyjścia: 1
```

Pilnuje tego `test_nieodczytana_wersja_runtime_nie_udaje_rozjazdu_rodziny`.

## 7. Testy bramki

`tools/tests/test_line_trace_gate.py` — 16 testów, zestaw narzędzi **1638 → 1654**.
Chodzą **bez .NET**: `check()` przyjmuje wersję runtime parametrem, bo `tools/tests/`
uruchamia się na maszynach, na których `doctor.sh` przepuszcza brak SDK jako „pomijam".
Bramka, której test wymaga narzędzia, jest bramką nietestowaną tam, gdzie zestaw
narzędzi jest jedynym, co chodzi.

Osobno pilnowana jest **numeracja wierszy**: `test_numer_wiersza_z_probki_wskazuje_ten_sam_wiersz_co_sed`
sprawdza, że numer w komunikacie wskazuje ten sam wiersz, co edytor. Gdyby próbka
liczyła od zera albo pomijała nagłówek, przedział prowadziłby śledztwo w złe miejsce
— a bramka wyglądałaby na sprawną.

## 8. Czego świadomie nie zrobiłem

- **Nie tknąłem `src/Sim`.** Pole „Poza zakresem" zabrania, a §3 pokazuje, że nie ma
  tam czego zmieniać: różnica nie pochodzi ze źródła.
- **Nie poprawiłem tabeli w treści `90a8c31`.** Treść commita jest niezmienialna,
  a przepisywanie historii nie wchodzi w grę. Rozjazd jest opisany tutaj.
- **Nie odtworzyłem 49 893 na .NET 8.** Wymagałoby to runtime, którego w tym
  środowisku nie ma, i którego repozytorium celowo nie chce (§3a).
- **Nie zmieniłem `dotnet-version: '10.0.x'` na pin co do łatki.** Byłaby to zmiana
  polityki CI wyprowadzona z jednej bramki — a §5 pokazuje, że bramka daje się napisać
  tak, żeby żyła z pinem, jaki jest.
