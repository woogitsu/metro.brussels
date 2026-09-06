# Nieznana opcja `Sim.Runner` przyjmowana w milczeniu (6.A11)

**Zmierzone 06.09.2026 na commicie:** `417d3dc484c017a42b4b5bd32b1a5634d1840146`

## 1. Stan zastany

Komenda z pola „Weryfikacja" pozycji 6.A6, wpisana dosłownie:

```
$ dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --coast-from-m X --trace build/coast-on.csv
[LINIA] największy błąd zatrzymania: 0.307 m
...
kod: 0
```

Opcji `--coast-from-m` nie ma nigdzie w `src/`. `X` nie jest liczbą. Proces kończy
się kodem 0 i normalnym przebiegiem, a plik wychodzi identyczny co do bajtu jak
z przebiegu bez tej opcji:

```
11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079  build/coast-off.csv
11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079  build/coast-on.csv
```

Literówka w nazwie opcji była więc **nieodróżnialna od opcji działającej**. Rdzeń był
pod tym względem łagodniejszy od sceny: `RunPlan.KnownArguments` po stronie Godota
odmawia nieznanemu argumentowi od dawna (`[ARGUMENT] nieznany widok '--view=zmyslony'`).

## 2. Stan po zmianie

```
$ dotnet run ... -- line --axis data/track/L1_A.json --limit-kmh 72 --exchange-s 20 \
      --coast-from-m X --trace build/coast-on.csv
BŁĄD: polecenie line nie zna opcji --coast-from-m. Zna: --axis, --brake-usage, --calls,
--exchange-s, --limit-kmh, --load, --signalling, --stop-window-m, --timetable, --trace
kod: 1
```

Kod wyjścia 1 nie jest wybrany: to ta sama stała, którą `Program.cs` daje wszystkim
odmowom argumentowym przez wspólny handler `ArgumentException`. Wprowadzenie nowej
wartości byłoby decyzją z rodziny, którą 6.A10 zostawiła właścicielowi.

Trzy zachowania, których zmiana **nie** tyka, sprawdzone uruchomieniem:

| co | wynik |
|---|---|
| ta sama komenda bez nieznanej opcji | kod 0 |
| `compare A B --tolerance 0` (dwie ścieżki pozycyjne) | brak odmowy argumentowej; kod 1 z czytania pliku |
| `budget ... --atp` (flaga bez wartości) | kod 0, `ATP=tak` |

## 3. Dlaczego tabela jest ręczna, a mimo to nie starzeje się po cichu

Komunikat ma wymieniać opcje **tego** polecenia, nie sumę wszystkich — inaczej odmowa
przestaje cokolwiek znaczyć. Stąd ręczna tabela `KnownOptions` w `Program.cs`.
Ręczna tabela ma dokładnie jedną wadę: opcja dopisana do kodu bez dopisania jej tam
przechodzi wszystkie testy C#, bo nikt jej w teście nie poda.

Dlatego `tools/tests/test_runner_options.py` czyta `Program.cs` **jako tekst** i
wyprowadza nazwy z wywołań `Option`, `RequiredNumber`, `OptionalNumber`
i `Array.IndexOf` w ciele każdego polecenia, po czym porównuje oba zbiory w **obie
strony**. Bramka nie potrzebuje `dotnet` — zestaw narzędzi chodzi tam, gdzie
`doctor.sh` przepuszcza brak SDK.

## 4. Kontrole negatywne — wykonane

| # | co popsute | co padło |
|---|---|---|
| 1 | `--kontrola-negatywna` czytana przez `budget`, nie dopisana do tabeli | `test_every_option_the_code_reads_is_in_the_table` |
| 2 | `--nikt-tego-nie-czyta` dopisane do tabeli `service-day` | `test_the_table_does_not_declare_options_nobody_reads` |
| 3 | odmowa przeniesiona za rozdzielacz | `test_the_refusal_is_actually_wired_into_main` |
| 4 | odmowa zdjęta w całości (stan sprzed tej pozycji) | `Line_z_nieznana_opcja_konczy_sie_kodem_jeden`, `Odmowa_wymienia_opcje_tego_polecenia_a_nie_wszystkich` |

Każda z pierwszych trzech wywraca **dokładnie jeden** test (1720/1721). Czwarta wywraca
dokładnie dwa testy C# i **nie** rusza dwóch pozostałych — bo tamte pilnują kierunku
odwrotnego: że odmowa nie zjada argumentów pozycyjnych ani członu po fladze. Po każdej
kontroli `git diff --stat src/` pokazuje wyłącznie zmianę tej pozycji.

## 5. Poza zakresem

Ujednolicanie kodów wyjścia (`compare` zwraca 2 tam, gdzie reszta odmów zwraca 1) —
to jest decyzja właściciela, nazwana już przy 6.A10. Poza zakresem także komunikat
`RequiredNumber`, który mówi `line` niezależnie od polecenia: to osobna pozycja 6.D20.

## 6. Zauważone, nietknięte

Odmowa działa na członach zaczynających się od `--`. Człon zaczynający się od
**jednego** minusa nie jest dziś opcją w żadnym poleceniu, więc nie jest sprawdzany;
gdyby kiedyś doszła forma krótka, ten warunek trzeba rozszerzyć razem z nią.
