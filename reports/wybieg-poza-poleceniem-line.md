# Wybieg poza poleceniem `line` (6.A18)

**Zmierzone 06.09.2026 na commicie:** `239345d344919278976278bdb74833ecbcc06f8c`
(gałąź `claude/6a18-wybieg-w-trzech`, .NET 10, cztery rdzenie na runnerze sesji).

## 1. Co mówiła pozycja, a co jest w kodzie

Pozycja 6.A18 mówiła: „**trzy** polecenia czytają ten sam `LineRunSettings`, ale wybieg
widzi jedno", i wymieniała `line`, `budget` oraz `replay`. Pierwsza rzecz zrobiona w tym
zadaniu to sprawdzenie tego zdania, a nie wykonanie go:

```
$ grep -n "new LineRunSettings" src/Sim.Runner/Program.cs
741:        var settings = new LineRunSettings(
1257:        var settings = new LineRunSettings(Units.KmhToMps(limitKmh), exchange, brakeUsage, stopWindow);
```

**Dwa miejsca, nie trzy.** `LineRunSettings` budują `LineCommand` (741) i `Budget`
(1257). `Replay` nie buduje go wcale i nie może: odtwarza **zapis wejść** z `--keys`
przez `InputLog`, `TrainController` i `DriverNotch`, a nie przez `LineDrive`. Nastawa
automatu, która zdejmuje trakcję od X metra odcinka, nadpisywałaby w nim wejścia
z zapisu — po czym odtworzenie przestałoby być odtworzeniem, przy zielonym teście
porównania telemetrii, bo porównanie mierzy zgodność dwóch przebiegów, a nie to,
czy któryś z nich odtwarza cokolwiek.

Dlatego zrobiona jest **połowa `budget`**, a `replay` nie. Nie z braku czasu: pytanie
„co ma znaczyć wybieg w odtworzeniu zapisu wejść" jest decyzją projektową, której nie
ma w dokumentach, i idzie do tabeli decyzji właściciela jako **6.A19** — bo jest decyzją, a kolejka ma zawierać wyłącznie pozycje, które nie wymagają ani jednej. Dzisiejsza odmowa `replay` jest
przybita testem, żeby jej zniesienie było decyzją podjętą, a nie skutkiem ubocznym.

## 2. Weryfikacja z pola „Weryfikacja"

```
$ dotnet run --project src/Sim.Runner -c Release --no-build -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 10 --steps 200000 \
      --trains 9 --coast-from-m 250
[BUDŻET] oś L1_A, plan classic-2026-L1_A (23 bloków), 12 stacji, ATP=nie, nawrót 0 s, odstęp 10 s, wybieg 250.0 m odcinka
[BUDŻET] okno 200000 kroków, rozgrzewka 2, powtórzeń 7, rdzeni 4, budżet kroku 1/120 s = 8333.3 µs
[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu
[BUDŻET] 9;9;6.67;2.11;265221;236239;271542;13.3;3.770;1.01;0.05
[BUDŻET] mieści się w 1/120 s: 1 z 1 zmierzonych N; największe zmierzone N=9 zajmuje 0.05% budżetu kroku przy 9 składach faktycznie na planie
kod: 0
```

Oczekiwane pole „Weryfikacja" mówiło: kod 0 i wypis `[BUDŻET]`. Oba są.

## 3. Dlaczego kod 0 to za mało, i co go uzupełnia

Kod 0 dowodzi, że opcja jest **przyjmowana**. Nie dowodzi, że **dochodzi** do
`LineCore` — dopisanie samej nazwy do tabeli `KnownOptions`, bez jednej linijki
działającego kodu, dałoby dokładnie ten sam kod 0 i ten sam wypis. Jest to ta sama
usterka, na której 6.D15 (#301) złapało `line`: dwa przejazdy, z opcją i bez niej, dały
pliki identyczne co do bajtu.

Dlatego pomiar jest **trójstronny**, na tym samym scenariuszu (`--trains 9`,
`--headway-s 10`, `--steps 200000`):

| wybieg | nagłówek | N_max | N_śr | czeka_śr | µs/krok |
|---|---|---|---|---|---|
| brak | `wybieg wyłączony` | 9 | **6.69** | **2.09** | 3.844 |
| 250 m | `wybieg 250.0 m odcinka` | 9 | **6.67** | **2.11** | 3.731 |
| 120 m | `wybieg 120.0 m odcinka` | 9 | **6.40** | **2.39** | 3.753 |

Kolumny ruchu poruszają się **monotonicznie i w stronę, którą da się przewidzieć
z fizyki**: wcześniejsze zdjęcie trakcji to wolniejszy przejazd, więc mniej składów
naraz na planie i więcej czekających. Kolumna `µs/krok` w tym **nie** pomaga — 3,73 do
3,84 to szum sąsiedztwa na runnerze, i gdyby dowodem miała być ona, dowodu by nie było.
Powtórzone wywołanie z `--coast-from-m 250` dało te same `6.67;2.11`, więc różnice
w kolumnach ruchu nie są rozrzutem pomiaru.

## 4. Nagłówek `[BUDŻET]` mówi teraz, którą nastawę zmierzył

Do tej pozycji wypis o wybiegu nie wspominał. Skoro wybieg zmienia **przejazd**, a nie
tylko jego koszt (§3), to dwa pomiary — z nim i bez niego — dawały się porównać jako
jeden. Ta sama usterka, którą wiersz `[LIMIT]` naprawił w `replay` przy #246: liczba
istniała, nie była wypisywana, a porównanie telemetrii co do bitu i tak wychodziło
zielone.

Zdanie o wybiegu ma **jedno** źródło — `LineRunSettings.CoastDescription` — bo wypisują
je dwie strony (`ToString()` i nagłówek `budget`), a dwa osobne wyrażenia rozjechałyby
się przy pierwszej zmianie formatu, przy czym rozjazd wyglądałby jak różnica nastawy,
nie jak różnica wypisu.

## 5. Bramka 6.D2 przestała mówić o niemożliwości

`tools/ci/assert_linecore_budget.py` wypisywał przy każdym przebiegu: „mierzony jest
przejazd BEZ wybiegu: `budget` nie zna `--coast-from-m` (6.A18)". Od tej zmiany to
zdanie byłoby **nieprawdą**, więc jest przepisane, a nie dopisane obok — razem
z mechanizmem, przez który się starzało: stało w kodzie na sztywno i nic nie łączyło go
z tym, co bramka naprawdę uruchamia.

Teraz obie strony czytają `scenario.coast_from_m` z `tools/ci/linecore-step-budget.json`:
`null` daje wywołanie bez opcji i zdanie „BEZ wybiegu — to jest wybór, nie brak",
liczba daje opcję w wywołaniu i zdanie „Z WYBIEGIEM od X m". Zdanie nie może rozjechać
się z wywołaniem, bo pochodzi z tego samego pola.

**`null` zostaje** i to nie jest zaniedbanie: próg 8,0 µs zmierzono na przejeździe bez
wybiegu, a §3 pokazuje, że wybieg zmienia przejazd. Pomiar z wybiegiem porównywałby się
z progiem wziętym z innego przejazdu — więc jego włączenie wymaga nowego pomiaru
i nowego raportu, nie samej liczby w polu. Osobny test przybija właśnie to.

## 6. Kontrola negatywna — WYKONANA

Nastawa zdjęta z tabeli `KnownOptions["budget"]`, kod czytający ją zostawiony:

```
  FAIL test_every_option_the_code_reads_is_in_the_table: polecenie budget czyta opcje
  spoza tabeli: ['--coast-from-m'] — dopisz je do KnownOptions, inaczej odmowa odrzuci
  opcje, ktora dziala
```

Jeden wpis, wskazany po nazwie. Po przywróceniu — zielono.

**Druga kontrola — po stronie C#, na wpięciu, a nie na tabeli.** Nastawa zostawiona
w kodzie jako czytana, ale **nieprzekazana** do `LineRunSettings` — czyli dokładnie ten
stan, o którym mówi §3:

```
  Failed Budget_zna_wybieg_i_wypisuje_go_w_naglowku [14 ms]
  StringAssert.Contains failed. String '[BUDŻET] oś L1_A, plan classic-2026-L1_A
  (23 bloków), 12 stacji, ATP=nie, nawrót 0 s, odstęp 90 s, wybieg wyłączony'
  does not contain string 'wybieg 250.0 m odcinka'.
Failed!  - Failed: 1, Passed: 548, Skipped: 0, Total: 549
```

Jeden test, wskazany po nazwie, i **549 wciąż uruchomionych** — liczba jest tu częścią
kontroli, po nauczce z 6.B27. Warto zobaczyć, co przy tej mutacji **nie** zapaliło się:
kod wyjścia został **0**, odmowa nadal milczała, wypis `[BUDŻET]` nadal miał wiersz
pomiaru. Weryfikacja z pola „Weryfikacja" pozycji 6.A18 — „kod 0 i wypis `[BUDŻET]`" —
przeszłaby na zielono z nastawą, która nigdzie nie dochodzi. Dlatego §3 i nagłówek
z §4 nie są ozdobą raportu, tylko jedynym miejscem, w którym ta usterka jest widoczna.

**Przy tej kontroli wyszła usterka w moim własnym sposobie mierzenia.** Pierwsze
podejście uruchomiło bramkę tak:

```
$ python3 tools/tests/test_runner_options.py
kod: 0
```

i zostało odczytane jako „bramka nie zapala się". Nieprawda: `tools/tests/test_runner_options.py`
**nie ma bloku `if __name__ == "__main__"`**, więc uruchomiony wprost wykonuje same
definicje, **zero testów**, i kończy się kodem 0 — nieodróżnialnie od przebiegu, w którym
wszystko przeszło. Kontrola powtórzona przez `tools/tests/test_all.py` pokazała FAIL
wypisany wyżej. Zmierzone, a nie domniemane:

```
$ tot=$(ls tools/tests/test_*.py | wc -l); z=$(grep -l '__main__' tools/tests/test_*.py | wc -l)
modulow test_*.py: 89; z blokiem __main__: 5; bez: 84
```

**84 z 89 modułów zachowuje się tak samo** — pięć wyjątków (`test_all`, `test_braking`,
`test_ci_workflows`, `test_mutation_sweep`, `test_reference_snapshot`) blok mają. Wzorzec
`python3 tools/tests/<moduł>.py` jest naturalnym odruchem przy sprawdzaniu jednej bramki
i w 84 przypadkach na 89 daje **zielony kod wyjścia z zera wykonanych testów** — czyli
dokładnie ten kształt usterki, który zestaw łapie u innych (`assertion_gate` od #139,
`grep FAIL` ślepy na błąd importu od 6.D19). Idzie do kolejki jako **6.D25**.

## 7. Czego świadomie nie zrobiono

- **`replay --coast-from-m`** — §1. Decyzja projektowa: nie kolejka, tylko tabela „Czego agent nie ruszy bez decyzji", pozycja **6.A19**.
- **Włączenia wybiegu w scenariuszu bramki 6.D2** — §5. Wymaga nowego progu i nowego
  raportu; poza zakresem tej pozycji.
- **Wyboru profilu jazdy dla gry.** 250 m i 120 m to wartości pomiarowe, wzięte za
  6.A6, żeby pokazać kierunek zmiany. Ta pozycja nie utrwala żadnej z nich jako
  domyślnej i nie twierdzi, że tak jeździ STIB — praktyka STIB nie jest publikowana.
- **Bloku `__main__` w modułach testowych** — §6. Zauważone, nietknięte, w kolejce
  jako 6.D25: to jest zmiana w 90 plikach zestawu, nie poprawka przy okazji.
