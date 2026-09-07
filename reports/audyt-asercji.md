# Audyt asercji: obecność bez licznika i bez asercji na brak (6.A32)

**Zmierzone 07.09.2026 na commicie:** `aa64156ce02d00c1396911623919bca6e088bfa8`
(baza gałęzi `claude/6a32-asercja-rozstrzygajaca-audyt`, czyli `main` po scaleniu #373).

## 1. Werdykt, na początku, bo pozycja o niego prosiła wprost

**Bramki nie warto stawiać i pozycja kończy się bez zmiany w kodzie.** Nie z powodu
rozmiaru — 382 asercje dałoby się jeszcze objąć progiem — a dlatego, że **przyrząd
zmierzony na czterech znanych przypadkach nie łapie ani jednego z nich**, a wariant,
który łapie trzy, zgłasza 845 asercji, czyli praktycznie każde wywołanie `Contains`
w zestawie. Instrument, który przepuszcza wszystkie znane usterki i zapala się na
poprawkach, mierzy coś innego, niż obiecuje.

Liczba, uzasadnienie i kontrola przyrządu — niżej. Kolejność jest taka, jakiej żądało
pole „Wyjście": **najpierw pomiar**.

## 2. Pomiar — liczba dla Pythona i dla C# osobno

Jednostką liczenia jest **pojedyncza asercja**. Kwalifikacja „bez licznika i bez
asercji na brak" liczona jest w ciele **tej funkcji lub metody, w której ta asercja
stoi**, nie w pliku: grep po pliku łapie cudze linie tego samego kształtu i to jest
dokładnie ta usterka przyrządu, którą 6.A29 opisało w swojej kontroli KN-3.

Python czytany `ast`-em (`assert X in Y` to `Assert` z `Compare`/`In`), C# przez
`tools/tests/csharp_test_methods.py` — te same przejście po ciele klasy i ta sama
`maska()`, których używa `csharp_assertions.py`, więc liczone są **metody z atrybutem
testowym**, a nie linie w plikach.

```
[PYTHON] asercji na OBECNOSC ogolem:                 595
[PYTHON]   z nich w ciele BEZ licznika i BEZ braku:  255
[PYTHON]   z nich rozstrzygajace z innego powodu:    340
[PYTHON] funkcji z co najmniej jedna gola:           193
[C#] asercji na OBECNOSC ogolem:                 254
[C#]   z nich w ciele BEZ licznika i BEZ braku:  127
[C#]   z nich rozstrzygajace z innego powodu:    127
[C#] funkcji z co najmniej jedna gola:           79
```

**Liczba, o którą pozycja prosiła: Python 255, C# 127.** Razem 382, w 193 + 79 = 272
funkcjach, w 61 + 23 = 84 plikach.

Rozbicie na pliki (sześć najliczniejszych po każdej stronie) i na kształt asercji C#:

```
== PYTHON: obecnosc=595 gole=255 funkcji=193 plikow=61
     tools/tests/test_mutation_sweep.py             22
     tools/tests/test_lod.py                        16
     tools/tests/test_m7_report.py                  14
     tools/tests/test_chunks.py                     10
     tools/tests/test_ci_workflows.py               10
     tools/tests/test_line_calls_gate.py            9
== C#: obecnosc=254 gole=127 funkcji=79 plikow=23
     tests/Game.Tests/RunPlanTests.cs               20
     tests/Game.Tests/TelemetryTrackTests.cs        19
     tests/Sim.Tests/InputLogTests.cs               14
     tests/Sim.Tests/SignallingPlanTests.cs         8
     tests/Game.Tests/EmergencyBrakeTests.cs        6
     tests/Sim.Tests/MovementAuthorityTests.cs      6

C# rozbicie po ksztalcie asercji:
     Contains               113
     IsTrue                 11
     StartsWith             3
C# ogolem po ksztalcie:
     Contains               226
     IsTrue                 25
     StartsWith             3
```

### 2.1 Przyrząd widzi cały zestaw, a nie wycinek

Kontrola zasięgu, bo liczba „255" nic nie znaczy, dopóki nie wiadomo, z jak dużego
zbioru pochodzi:

```
[TESTY C#] atrybutow testowych w plikach: 756
[TESTY C#] objetych ksztaltem bramki:     756
[TESTY C#] poza ksztaltem:                 0
[ASERCJE C#] metod testowych:        756
[ASERCJE C#] z asercja w tresci:     756
[ASERCJE C#] BEZ asercji w tresci:   0

plikow tools/tests/*.py:      105
funkcji (ast):                2490
instrukcji `assert` (ast):    4834
grep `assert `:               4863
```

756 metod testowych C# w całości objętych, 105 plików Pythona, 4834 instrukcje
`assert` widziane przez `ast` przy 4863 wierszach z gołego grepa — różnica 29 to
wzmianki w komentarzach i napisach, których `ast` z definicji nie liczy. Przyrząd nie
jest zawężony do jednego katalogu ani do jednej rodziny testów.

## 3. Kontrola przyrządu — cztery znane przypadki, WYKONANA

Każdy z czterech przypadków przywrócony do stanu **przed** swoją poprawką, przyrząd
uruchomiony, stan przywrócony (`git status --porcelain` puste na końcu). Cztery
warianty wyjątków, bo „bez licznika i bez braku" to jedna z czterech możliwych
definicji, a wybór między nimi też ma być pomiarem:

```
=== KP-1 (6.A29) — stan PRZED poprawka; cele: Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy
   V0  bez licznika i bez braku (definicja z pola „Wyjscie")  obecnosc=1   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 382]
   V1  bez braku (wyjatek na licznik zdjety)                  obecnosc=1   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 570]
   V2  bez licznika (wyjatek na brak zdjety)                  obecnosc=1   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 518]
   V3  kazda asercja na obecnosc (bez wyjatkow)               obecnosc=1   zglosz=1    -> ZGLASZA       [zgloszen w calym zestawie: 845]

=== KP-2 (6.A27) — stan PRZED poprawka; cele: test_compare_refuses_through_the_common_handler
   V0  bez licznika i bez braku (definicja z pola „Wyjscie")  obecnosc=2   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 382]
   V1  bez braku (wyjatek na licznik zdjety)                  obecnosc=2   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 570]
   V2  bez licznika (wyjatek na brak zdjety)                  obecnosc=2   zglosz=2    -> ZGLASZA       [zgloszen w calym zestawie: 520]
   V3  kazda asercja na obecnosc (bez wyjatkow)               obecnosc=2   zglosz=2    -> ZGLASZA       [zgloszen w calym zestawie: 849]

=== KP-3 (6.A26) — stan PRZED poprawka; cele: test_a_line_naming_both_programs_counts_as_scene_not_runner
   V0  bez licznika i bez braku (definicja z pola „Wyjscie")  obecnosc=0   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 382]
   V1  bez braku (wyjatek na licznik zdjety)                  obecnosc=0   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 570]
   V2  bez licznika (wyjatek na brak zdjety)                  obecnosc=0   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 518]
   V3  kazda asercja na obecnosc (bez wyjatkow)               obecnosc=0   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 849]

=== KP-4 (6.A25 KN-2) — stan PRZED poprawka; cele: Wartosc_po_fladze_jest_czlonem_pozycyjnym_i_konczy_sie_odmowa, Czlon_pozycyjny_nieznany_poleceniu_konczy_sie_odmowa, test_the_refusal_counts_positional_members_against_the_table
   V0  bez licznika i bez braku (definicja z pola „Wyjscie")  obecnosc=3   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 380]
   V1  bez braku (wyjatek na licznik zdjety)                  obecnosc=3   zglosz=3    -> ZGLASZA       [zgloszen w calym zestawie: 568]
   V2  bez licznika (wyjatek na brak zdjety)                  obecnosc=3   zglosz=0    -> NIE ZGLASZA   [zgloszen w calym zestawie: 516]
   V3  kazda asercja na obecnosc (bez wyjatkow)               obecnosc=3   zglosz=3    -> ZGLASZA       [zgloszen w calym zestawie: 847]
```

| wariant | znanych przypadków złapanych | zgłoszeń w zestawie |
|---|---|---|
| V0 — definicja z pola „Wyjście" | **0 z 4** | 382 |
| V1 — bez wyjątku na licznik | 2 z 4 | 570 |
| V2 — bez wyjątku na brak | 1 z 4 | 518 |
| V3 — każda asercja na obecność | 3 z 4 | 845 |

**Dlaczego V0 przepuszcza wszystkie cztery — powód jest w kodzie tych testów, nie
w przyrządzie:**

- **KP-1 (6.A29).** Ciało przed poprawką to `Assert.AreEqual(1, result.ExitCode)`,
  `StringAssert.Contains(result.StdErr, zepsuty)` i
  `Assert.IsFalse(result.StdErr.Contains(dobry, …))`. Obok słabej asercji na obecność
  stoi **licznik** (kod wyjścia porównany z liczbą) **i asercja na brak** (drugiej
  ścieżki nie ma w komunikacie). Oba wyjątki definicji zachodzą jednocześnie — a test
  był mimo to niepilnujący niczego, co udowodniła KN-1 pozycji 6.A25.
- **KP-2 (6.A27).** Postać z 6.A16 to dwie asercje na obecność plus
  `assert "return 2;" not in body` — asercja na brak stoi obok, na tym samym stogu.
- **KP-3 (6.A26).** Przed poprawką **nie było żadnej asercji**: reguła pierwszeństwa
  sceny stała w komentarzu. Przyrząd liczący asercje nie ma tu czego zgłosić i żaden
  wariant tego nie zmieni — to nie jest luka w definicji, tylko granica całej rodziny
  bramek tego kroju.
- **KP-4 (6.A25).** Dwa testy C# odmowy członu pozycyjnego mają
  `Assert.AreEqual(1, result.ExitCode, result.StdOut)` — licznik obok.

**Sąsiedztwo asercji na brak nie czyni asercji na obecność rozstrzygającą, i to jest
zmierzone, nie przewidziane.** Cały wyjątek, na którym stoi definicja z pola
„Wyjście", opiera się na założeniu, którego czwarty przypadek dnia bezpośrednio
przeczy.

### 3.1 Kontrola ujemna — asercje rozstrzygające SĄ zgłaszane, i to WYKONANE

Pole „Skończone, gdy" żądało kontroli ujemnej pokazującej, że asercje rozstrzygające
nie są zgłaszane. **Ta kontrola pada.** Wstrzyknięta KN-2 pozycji 6.A25 (odmowa liczy
człony pozycyjne z własnej stałej `command == "compare" ? 2 : 0`, wszystkie trzy
odczyty z tabeli zastąpione, zachowanie identyczne):

```
$ python3 tools/tests/test_all.py test_runner_options.py
  FAIL test_the_refusal_counts_positional_members_against_the_table: odmowa nie czyta liczby czlonow pozycyjnych z tabeli
  17/18 przeszło

$ werdykt klasyfikatora V0 dla tej samej funkcji
test_the_refusal_counts_positional_members_against_the_table   obecnosc=2  zgloszonych=2  -> ZGLASZA
```

Ta funkcja to `assert "known.Positional" in body` i `assert "człon pozycyjny" in body`
— dwie gołe asercje na obecność, bez licznika i bez asercji na brak. Jest przy tym
**jedyną rzeczą w całym zestawie, która KN-2 łapie**: wszystkie testy C# zostają wtedy
zielone, co 6.A25 zapisało u siebie. Asercja **dowiedziona rozstrzygającą wykonanym
pomiarem** jest więc dwiema z 382 zgłoszonych.

Nie da się jej zresztą napisać inaczej: „odmowa czyta liczbę z tabeli" nie ma postaci
licznika ani postaci asercji na brak. Kształt, którego bramka miałaby zakazywać, jest
tu jedynym możliwym kształtem.

### 3.2 Metryka rusza się w ZŁĄ stronę, kiedy usterka jest naprawiana

To jest argument przeciw progowi, i też jest pomiarem. Te same cele, stan **po**
poprawce:

```
KP-1 (6.A29)     PO poprawce: obecnosc=5, z nich zglaszanych V0=0
KP-2 (6.A27)     PO poprawce: obecnosc=2, z nich zglaszanych V0=0
KP-3 (6.A26)     PO poprawce: obecnosc=0, z nich zglaszanych V0=0
KP-4 (6.A25)     PO poprawce: obecnosc=5, z nich zglaszanych V0=2
```

| przypadek | asercji na obecność przed | po | zgłoszeń V0 przed | po |
|---|---|---|---|---|
| KP-1 (6.A29) | 1 | **5** | 0 | 0 |
| KP-2 (6.A27) | 2 | 2 | 0 | 0 |
| KP-3 (6.A26) | 0 | 0 | 0 | 0 |
| KP-4 (6.A25) | 3 | **5** | 0 | **2** |

Poprawka 6.A29 **podniosła** liczbę asercji na obecność z 1 na 5, bo właściwym
lekarstwem na asercję prawdziwą-ale-nie-rozstrzygającą były **cztery kolejne asercje
na obecność**, tylko z igłami, których nie ma żadna inna odmowa (`wiersz 5`,
`kolumna 3`, `chainage_m`, `nie-liczba`). Poprawka 6.A25 podniosła liczbę **zgłoszeń**
z 0 na 2, bo dołożoną bramką jest właśnie asercja gołej obecności.

Rozstrzyga więc **swoistość igły**, nie kształt asercji — a swoistości igły nie da się
przeczytać z tekstu testu. `StringAssert.Contains(result.StdErr, "wiersz 5")`
i `StringAssert.Contains(result.StdErr, zepsuty)` są tym samym kształtem; różnią się
tym, czy ta igła występuje w innych komunikatach tego programu, i to jest zdanie
o **kodzie produkcyjnym**, nie o teście.

## 4. Dlaczego żaden z trzech kierunków się nie broni — tą liczbą, nie przekonaniem

**Bramka z listą utrzymywaną ręcznie.** Musiałaby wymienić **382** asercje w 272
funkcjach w 84 plikach, żeby zejść do zera zgłoszeń. Dla porównania: bramka 6.A29
trzyma tabelę **trzech** testów i jej własny raport nazywa tę tabelę „jej ceną", bo
nowy test odmowy nie będzie pilnowany, dopóki ktoś go tam nie dopisze. 382 to nie ta
sama cena o rząd wielkości — a lista wyjątków większa od tego, co pilnuje, jest bramką
wyłączoną, tylko zapisaną jako włączona (nauczka 6.D27, 6.D29).

**Próg na liczbę.** Zapadka na 382 przechodziłaby przez wszystkie cztery znane
usterki (V0 łapie 0 z 4), a zapaliłaby się na poprawkach: 6.A29 podnosi licznik o 4,
6.A25 o 2. Próg, który jest zielony przy usterce i czerwony przy jej naprawie, jest
wyrocznią odwróconą — to ten sam gatunek instrumentu, co 6.D30 (dwa martwe pola
zgadzają się zawsze) i 6.A27 (zdanie prawdziwe i dlatego nic nie mierzące).

**Wariant V3, jedyny łapiący więcej niż dwa.** 845 zgłoszeń przy 849 asercjach na
obecność w całym zestawie to nie bramka, a zakaz `Contains` — i nadal 3 z 4, bo KP-3
usterką bez asercji.

**Nic.** Zostaje to.

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py
  RAZEM 70.764 s, 1886 testów, 99 modułów
$ echo $?
0

$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   589, Skipped:     0, Total:   589, Duration: 29 s

$ dotnet test tests/Game.Tests
Passed!  - Failed:     0, Passed:   210, Skipped:     0, Total:   210, Duration: 1 s
```

Zestaw narzędzi **1886 → 1886**, `dotnet test` **589 + 210 → 589 + 210**: ta pozycja
nie dopisuje ani jednego testu, bo pomiar rozstrzygnął, że nie ma czego pilnować
kształtem. 756 atrybutów testowych daje 799 przebiegów, bo rodzina
`[DataTestMethod]` mnoży się przez wiersze `[DataRow]`.

Wszystkie cztery przywrócenia stanu „przed poprawką" cofnięte; `git status
--porcelain` po każdym z nich puste, sprawdzone po każdej kontroli osobno.

## 6. Czego świadomie nie zrobiono

- **Nie postawiono bramki.** Powód wyżej i jest to wynik dopuszczony wprost przez pole
  „Skończone, gdy" pozycji 6.A32.
- **Nie poprawiono ani jednej z 382 asercji.** Pole „Poza zakresem" mówi to wprost:
  pozycja dotyczy tego, czy da się je **wykrywać**, nie przepisywania zestawu. Cztery
  przypadki dnia są naprawione u siebie.
- **Nie zostawiono przyrządu w `tools/tests/`.** Klasyfikator, który zmierzył 382
  i został pobity na czterech znanych przypadkach 0 do 4, nie jest bramką ani
  biblioteką bramki; wstawiony do `tools/tests/` byłby kodem, którego nie woła żaden
  test, a martwy kod w tym katalogu jest osobną usterką tego projektu (6.B34,
  `test_dead_constants.py`). Definicja przyrządu jest zapisana w §2 i §3 dokładnie na
  tyle, żeby pomiar dał się powtórzyć: `ast` po `tools/tests/*.py` dla Pythona,
  `csharp_test_methods.czlonkowie()` + `maska()` dla C#, kwalifikacja w ciele funkcji,
  cztery warianty wyjątków z tabeli w §3.
- **Nie zmieniono definicji „licznika" i „braku" tak, żeby pasowała do wyniku.**
  Cztery warianty są wypisane w §3 razem z liczbą zgłoszeń każdego z nich — bo
  dobranie definicji po tym, jak się zobaczy, która łapie znane przypadki, jest
  dorabianiem liczby do formularza (`CLAUDE.md` §4.1).

## 7. Zauważone przy okazji, nie tknięte

- **Rozstrzygający jest jeden pomiar, którego ta pozycja nie robiła: czy igła asercji
  występuje w INNYM komunikacie tego samego programu.** To jest wykonalne dla
  **zamkniętej rodziny** komunikatów — i dokładnie to robi już bramka 6.A29, ręcznie,
  dla trzech odmów `compare`. Pomiar automatyczny tej własności (zebrać wszystkie
  literały odmów z `Program.cs`, dla każdej igły z testu policzyć, ile odmów ją
  zawiera, zgłosić igły niejednoznaczne) byłby osobną pozycją z własnym pomiarem —
  nie dopisuję jej, bo pozycja wymyślona na miejscu omija format z sekcji 6
  `CLAUDE.md`.
- **Trzy najliczniejsze pliki C# to testy Godota, nie runnera** (`RunPlanTests.cs` 20,
  `TelemetryTrackTests.cs` 19, `InputLogTests.cs` 14 gołych asercji na obecność).
  Cztery znane przypadki dnia są wszystkie z runnera i z `tools/tests/`, więc o tym,
  czy tamte 53 asercje są rozstrzygające, ten raport nie mówi nic — i nie udaje, że
  mówi.
- **`Assert.IsTrue(… .Contains(…))` jest w zestawie rzadkie**: 25 wystąpień wobec 226
  `StringAssert.Contains`. Wpis kolejki wymieniał obie postacie jako równorzędne;
  pomiar mówi, że pierwsza jest marginesem.
