# Gałąź, do której może nic nie wejść (6.D29)

**Zmierzone 07.09.2026 na commicie:** `07be80b7c7ed188e8fe2f812eff34cba9600639d`
(gałąź `claude/6d29-asercja-w-galezi`, po `git rebase origin/main`; bez zmian własnych
w `tests/**/*.cs` — to jest commit, na którego drzewie liczono).

**Adnotacja z tego samego dnia:** gałąź została po tym pomiarze przestawiona jeszcze raz,
na `a6e280d` (scalenia #349 — 6.B19 — i #350 — uzupełnienie kolejki). Klasyfikacja
przebiegła na nowej podstawie ponownie i dała **te same liczby**: 727 metod testowych,
83 zagnieżdżonych, 65 bezpiecznych, 18 interesujących, rozkład 14/1/3 — bo żadna z tych
dwóch pozycji nie dotyka `tests/**/*.cs`. Zestaw narzędzi po rebase: **1841** testów,
98 modułów, kod wyjścia 0. Liczby z dnia pomiaru nie są przeliczane; ta adnotacja mówi,
co powtórzono i z jakim wynikiem.

## 0. Przeliczenie po 6.B28 — czytaj to przed resztą

Ten raport miał już jedną wersję, zmierzoną **przed** rebase'em na commicie `7bf5062`.
Ta wersja pisała: „82" i „65" z wpisu 6.D29 są artefaktem błędu czytnika, naprawdę jest
**81/64**, a interesujących metod jest **17**. Niezależnie od tej sesji ten sam błąd
czytnika zmierzono i **naprawiono na `main`** jako pozycję **6.B28** (scalone jako
`#348`, commit `07be80b`) — `tools/tests/csharp_test_methods.py` ma teraz `maska()`:
kopię źródła z komentarzami i literałami zamienionymi na spacje znak w znak, po której
chodzi liczenie klamr. Naprawa poszła też **szerzej**, niż ta sesja przewidziała:
kształt bramki objął też **13** metod `[DataTestMethod]` z argumentami, które do
07.09.2026 były poza nim z zupełnie innego powodu (obawa o pomocników z argumentami —
zmierzona i nieziszczona, patrz `docs/TASKS.md` 6.B28).

**Skutek: WSZYSTKIE liczby z poprzedniej wersji tego raportu były zmierzone zepsutym
czytnikiem i są tu przeliczone, nie przepisane po cichu.**

| co | przed 6.B28 (ten raport, I wersja) | po 6.B28 (ten raport, II wersja — dziś) |
|---|---|---|
| metod testowych w drzewie | 679 (naiwnie) / 690 (mój prowizoryczny string-świadomy czytnik) | **727** — zgodne z `python3 tools/tests/csharp_assertions.py` I z `grep -c '\[TestMethod\]\|\[DataTestMethod\]' tests/*/*.cs` |
| wszystkie asercje zagnieżdżone | 82 (wpis) / 81 (mój przelicznik) | **83** |
| bezpieczne (`for`/`foreach` po zbiorze z testu) | 65 (wpis) / 64 (mój przelicznik) | **65** |
| „interesujące" | 17 | **18** |

**Moje własne „690" z poprzedniej wersji też było liczbą z niepełnego czytnika** — nie
tylko wpisowe „82/65". Mój prowizoryczny, niecommitowany string-świadomy czytnik (opisany
w I wersji tego raportu) łapał usterkę w `SignallingPlanTests.cs`, ale **nie łapał** tej
samej usterki w `tests/Sim.Tests/ServiceDayTests.cs` (16 metod testowych, **zero**
widzianych przez ówczesny naiwny czytnik — ten sam tryb awarii, inny plik) i w ogóle nie
próbował objąć 13 metod z argumentami, bo to nie było przedmiotem tej pozycji. Nie
zdiagnozowałem do końca, na którym dokładnie wzorcu mój prowizoryczny czytnik ślizgał się
w `ServiceDayTests.cs` — a że jest to kod niecommitowany i zastąpiony teraz oficjalną
`maska()`, nie ma to już znaczenia dla wyniku: **727 jest liczbą z oficjalnego,
przetestowanego, scalonego czytnika**, potwierdzoną niezależnie grepem, i to jest liczba,
na której stoi reszta tego raportu. Sekcja 3 (znalezisko o czytniku) jest niżej
**przepisana**, nie skasowana, bo pierwsza wersja tego raportu zgłaszała je jako
nienaprawione — to już nieprawda.

## 1. Po co

6.D28 postawiła swoją granicę wprost: `csharp_assertions.py` liczy asercje **obecne
w treści** metody, nie **wykonane**. Test z asercją w gałęzi, do której nic nie wchodzi,
przechodzi tamtędy za asertujący. Ta pozycja bierze te metody — te, u których WSZYSTKIE
asercje siedzą w bloku zagnieżdżonym — i sprawdza ręcznie, którym z nich to faktycznie
szkodzi.

## 2. Premisa wpisu, przeliczona na naprawionym czytniku

Wpis mówił: **82** metody mają wszystkie asercje zagnieżdżone, **65** to `for`/`foreach`
po zbiorze zadanym w teście, interesujących jest **17**. Odtworzyłem ten podział na
**oficjalnym, scalonym** czytniku (`CTM.czlonkowie`/`CTM.maska` z 6.B28) dwiema
niezależnymi metodami:

1. **Klasyfikacja po pierwszej asercji** — słowo otwierające najbliższy blok PIERWSZEJ
   asercji metody.
2. **Klasyfikacja „którykolwiek przodek ryzykowny"** — metoda jest „interesująca", gdy
   CHOĆ JEDNA jej asercja ma w łańcuchu otaczających bloków którykolwiek z:
   `if`/`else`/`while`/`do`/`try`/`catch`/`switch`/`lock`/`using`/nierozpoznany
   (np. ciało lambdy).

Obie metody zgadzają się co do **liczby wszystkich zagnieżdżonych: 83** (to jest
sprawdzenie strukturalne — dwa niezależne przejścia po tym samym drzewie muszą dać tę
samą sumę, i dają). Metoda 2 jest ta właściwa do wyłapania usterki opisanej wpisem (bo
usterka może siedzieć w DRUGIEJ czy TRZECIEJ asercji metody, nie tylko w pierwszej) i daje
**18** interesujących; metoda 1, słabsza z definicji, daje **16** — brakuje jej dokładnie
dwóch metod, u których to nie pierwsza, tylko późniejsza asercja jest ryzykowna
(`RunPlanTests.NoInputThrows`, `BrakingTests.Wzor_zamkniety_jest_granica_modelu_krokowego_przy_dt_do_zera`
— oba wyjaśnione w §4). To jest oczekiwana, wytłumaczona różnica, nie rozjazd.

**Liczba 17 z wpisu urosła do 18**, bo widoczny zbiór metod urósł z 679 do 727 (+48:
27 wcześniej niewidocznych przez błąd klamr, 13 z argumentami, 8 nowych z 6.A14) —
i dokładnie jedna z tych 48 nowo widocznych metod okazała się mieć wszystkie asercje
zagnieżdżone w ryzykownej gałęzi: `RunnerCommandTests.Zegar_cytuje_cala_wartosc_a_nie_zly_czlon`,
dopisana przez 6.A14 (merge `#347`, po pierwszej wersji tego raportu). Reszta 47 nowo
widocznych metod ma choć jedną asercję na poziomie metody (nie w bloku) albo pętlę bez
ryzykownego przodka.

## 3. Znalezisko o czytniku `czlonkowie()`/`_koniec_bloku()` — zmierzone niezależnie, naprawione jako 6.B28

**Pierwsza wersja tej sekcji zgłaszała, że `tools/tests/csharp_test_methods.py` liczy
klamry jako tekst, bez wiedzy o stringach i komentarzach, i że jeden niesparowany `{`
w literale stringowym `SignallingPlanTests.cs:132` (`.Replace("\"authority_margin_m\":
{", …)`) połyka 11 realnych metod tej klasy.** Zgłaszałem to jako „poza zakresem tej
pozycji" i zostawiałem nienaprawione.

**To już nieprawda i jest przepisane, nie dopisane obok.** Niezależnie od tej sesji ten
sam błąd zmierzyła i naprawiła pozycja **6.B28** (`docs/TASKS.md`, scalone jako `#348`).
Pomiar 6.B28 poszedł dalej, niż ja poszedłem: oprócz `SignallingPlanTests.cs` (15 metod,
4 widoczne — zgodne z moim pomiarem) znalazł ten sam błąd w `ServiceDayTests.cs` (16
metod, **zero** widocznych) — plik, którego mój własny prowizoryczny string-świadomy
czytnik NIE złapał jako różniącego się (patrz §0). Razem **27** realnych metod było
niewidocznych dla `csharp_test_methods.metody()` i `csharp_assertions.metody_testowe()`
— nie liczonych, nie sprawdzanych pod kątem asercji, nienazwanych przez żadną z bramek
6.B27/6.D28/6.D30. Naprawę niesie `maska(source)`
(`tools/tests/csharp_test_methods.py`): kopia źródła tej samej długości, z komentarzami
i **czterema** postaciami literału stringowego (`"…"`, `@"…"`, `$"…"`, surowy
otwierany trzema cudzysłowami) zamienionymi na spacje znak w znak — struktura klas
i metod chodzi po masce, wycinki treści bierze się z oryginału.

**Sprawdzone bezpośrednio na dzisiejszym drzewie, że naprawa trzyma:**

```
$ python3 tools/tests/csharp_test_methods.py
[TESTY C#] atrybutow testowych w plikach: 727
[TESTY C#] objetych ksztaltem bramki:     727
[TESTY C#] poza ksztaltem:                 0
[TESTY C#] wygladaja jak test, nie sa uruchamiane: 0

$ grep -rho '\[TestMethod\]\|\[DataTestMethod\]' tests/*/*.cs | wc -l
727
```

Zero rozjazdu między liczeniem strukturalnym (`csharp_test_methods.py`) a prostym grepem
po atrybutach — to jest dokładnie ten sam rodzaj drugiej, niezależnej metody, którego
zabrakło przy 82/65 z wpisu.

**Co to zmienia dla klasyfikacji w tym raporcie.** Wcześniej wyliczona metoda
`SignallingPlanTests.Loader_odrzuca_gola_liczbe_bez_deklaracji_pochodzenia` w ogóle nie
trafia dziś do zbioru „82/83 zagnieżdżonych" — poprawnie przeczytana, jej dwie asercje
stoją wprost w ciele metody, żadna nie jest zagnieżdżona (to ustalenie z I wersji tego
raportu zostaje prawdziwe). Pozostałe 26 nowo widocznych metod (`ServiceDayTests.cs`
w całości plus 10 z 11 dawniej niewidocznych w `SignallingPlanTests.cs`) i 13 metod
z argumentami **nie wniosły żadnej nowej metody do zbioru interesujących poza jedną**
(`RunnerCommandTests.Zegar_cytuje_cala_wartosc_a_nie_zly_czlon` — ale ta jest nowa z
zupełnie innego powodu, dopisana przez 6.A14, patrz §2) — sprawdzone pętlą po
wszystkich 727 metodach, nie na próbce. Jedna z 13 metod z argumentami trafiła
dodatkowo do zbioru **bezpiecznych** (`BrakingTests.Prog_krytyczny_jest_odwrotnoscia_sufitu`,
`foreach` po literale dwuelementowym, z `if (fraction > 1.0) { continue; }` PRZED
asercjami, nie wokół nich).

Naprawa czytnika **nie jest częścią tego commitu** — jest już na `main`, scalona
niezależnie. Nic w tej pozycji jej nie dotyka.

## 4. 18 metod „interesujących" — klasyfikacja z nazwami

Definicja z wpisu: (a) gałąź **zawsze** wchodzona, bo test sam ustawia warunek — asercja
się wykonuje; (b) gałąź może nie wejść, ale sam brak wejścia jest sprawdzony **osobno**;
(c) gałąź może nie wejść i **nikt tego nie sprawdza** — jedyna prawdziwa usterka.

### (a) — 14 metod, gałąź zawsze wchodzona

| metoda | dlaczego zawsze wchodzi |
|---|---|
| `EnergyAccountTests.Wiersz_konta_rozruchu_nie_zalezy_od_kultury_maszyny` | `WithCulture(culture, () => {…})` woła `body()` bezwarunkowo w `try`, przed `finally` — lambda zawsze się wykonuje |
| `EnergyAccountTests.Wiersz_konta_hamowania_nie_zalezy_od_kultury_maszyny` | to samo |
| `EnergyAccountTests.Caly_katalog_zalozen_M7_wypisuje_sie_w_kulturze_niezmiennej` | to samo + `foreach (var value in values)`, a `values` ma być niepuste, bo linijkę wcześniej stoi `Assert.IsTrue(lines.Count >= 16, …)` |
| `BrakingTests.Wzor_zamkniety_jest_granica_modelu_krokowego_przy_dt_do_zera` | `foreach` po **literale** `new[] { 120, 1200, 12000 }` (3 elementy, stałe w teście); wewnętrzny `if (!double.IsNaN(previous))` jest fałszywy TYLKO na 1. iteracji z konstrukcji (sentinel), prawdziwy gwarantowanie na 2. i 3. — druga asercja w drugiej iteracji jest tym, co Metoda 1 z §2 gubi |
| `LineDriveTests.Postoj_przed_autorytetem_jest_naprawde_postojem_a_nie_pelzaniem` | `while (chainage < 100 \|\| speed > 0)` — skład startuje z `Axis(0.0, 800.0)` na kilometrażu ~0, więc warunek jest prawdziwy od pierwszej iteracji z konstrukcji testu |
| `StepAccumulatorTests.CarryStaysBelowOneStepAndNeverGoesNegative` | `while (frame < 5000)`, `frame` to licznik testu startujący od 0 — odpowiednik `for` |
| `MovementAuthorityTests.Wiersz_authority_niesie_powod_i_blok_ograniczajacy_niezaleznie_od_kultury` | `try { asercje } finally { przywróć kulturę }` — **bez `catch`**: wyjątek wywaliłby test głośno (nieobsłużony), nie ominąłby asercji po cichu |
| `MovementAuthorityTests.Wiersz_bloku_niesie_granice_dlugosc_i_role` | to samo |
| `RunnerCommandTests.ServiceDay_z_niepoprawnym_formatem_at_konczy_sie_kodem_jeden` | `try { asercje } finally { File.Delete }` — bez `catch` |
| `RunnerCommandTests.Budget_zapisuje_nastawy_do_pliku_a_nie_tylko_na_konsole` | to samo + `foreach` po literale 10-elementowej tablicy nazw kolumn |
| `RunnerCommandTests.Dwa_przebiegi_roznia_sie_widocznie_nastawa_a_nie_tylko_liczbami` | to samo |
| `RunnerCommandTests.ServiceDay_zapisuje_nastawy_jako_komentarz_przed_naglowkiem` | to samo |
| `RunnerCommandTests.Zegar_cytuje_cala_wartosc_a_nie_zly_czlon` | **nowa metoda, dopisana przez 6.A14 po I wersji tego raportu** — ten sam wzorzec `try { asercje } finally { File.Delete }` co pięć powyższych z tej samej klasy |
| `SpeedProfileTests.Wiersz_probki_nie_zalezy_od_kultury_maszyny` | `try { asercje } finally { przywróć kulturę }` — bez `catch` |

**Wzorzec dla ośmiu `try`:** żaden nie ma `catch`. `try`/`finally` bez `catch` nie jest
gałęzią, która „może nie wejść po cichu" — jest odwrotnie: jeśli coś w środku rzuci,
wyjątek ucieka nieobsłużony, framework testowy zgłasza to jako **FAIL**, a nie jako
milczący sukces. Ryzyko z definicji pozycji („gałąź, do której może nic nie wejść, a test
mimo to przechodzi") tu nie zachodzi.

### (b) — 1 metoda, brak wejścia pilnowany osobno

**`DriverActionsTests.PodAutopilotemPomocNazywaKlawiszeKtoreNieDzialaja`** — pętla
`foreach (var binding in DriverActions.All)` z `if (przejete.Contains(binding.Action))
{…} else {…}`. Który `binding` trafia do której gałęzi, zależy od
`DriverActions.TakenOverByTheCore` — danych produkcyjnych, nie stałej testu. Gdyby ten
zbiór stał się pusty (albo równy całości), jedna z dwóch gałęzi przestałaby wchodzić
w ogóle, po cichu. To jest jednak **osobno przypięte**: metoda
`KazdaAkcjaStoiPoDokladnieJednejStronie` w **tej samej klasie** pinuje
`CollectionAssert.AreEqual` dokładną 7-elementową listę `DriverActions.All` i dokładną
5-elementową listę `TakenOverByTheCore` (a więc i to, że 2 akcje leżą PO DRUGIEJ
stronie). Zanim `TakenOverByTheCore` mogłoby stać się puste albo pełne, ten drugi test
padnie pierwszy — głośno, z nazwaną listą.

### (c) — 3 metody, nikt nie sprawdza, że gałąź w ogóle wchodzi

**`RunPlanTests.EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds`** — pętla po
`RunPlan.KnownArguments` (dane produkcyjne) z `if (!towarzysz.TryGetValue(name, out …))
{ … continue; }`, gdzie `towarzysz` to **lokalny** słownik trzech kluczy: `"line"`,
`"limit-kmh"`, `"calls"`. Trzy asercje sprawdzające zachowanie „argument wymaga
towarzysza" wykonują się TYLKO dla nazw, które są jednocześnie w `KnownArguments`
I w `towarzysz`. Nic w tej klasie ani w pliku nie pinuje, że `KnownArguments` nadal
zawiera te trzy nazwy — komentarz w samej metodzie mówi wprost, że `--signalling`
**zeszło** z tej listy 05.09.2026, czyli lista jest żywa i bywa skracana. Gdyby kiedyś
zniknęły z niej wszystkie trzy, cała gałąź „wymaga towarzysza" (i jej trzy asercje)
przestałaby się wykonywać na zawsze, a test nadal przechodziłby.

**`RunPlanTests.NoInputThrows`** — pętla po literale 9 „paskudnych" napisów. Jedyna
asercja wykonywana zawsze to `Assert.IsNotNull(plan, argument)` — to ona sprawia, że
Metoda 1 z §2 (klasyfikacja po PIERWSZEJ asercji) tej metody nie widzi jako
interesującej. Dwie kolejne (`ExitCode` jest `UnknownArgument`/`BadArgumentValue`,
komunikat błędu niepusty) stoją w `if (!plan.IsValid) { … }`. Nic w zestawie nie pinuje,
że te konkretne 9 napisów jest dziś odrzucanych — gdyby parser zaczął (błędnie)
akceptować którykolwiek z nich jako poprawny, ta gałąź przestałaby wchodzić dla niego,
a test i tak by przeszedł, nie sprawdziwszy nic ponad „nie rzuciło wyjątkiem".

**`TrainProtectionTests.Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311`** —
pętla po literale `new[] { 10.0, 50.0, 120.0, 300.0, 700.0 }` z
`if (permitted >= plan.PermittedSpeedMps) { assert …; continue; }`. Gałąź „osiągnięto
sufit prędkości planu" wchodzi tylko wtedy, gdy DLA KTóREGOŚ z pięciu dystansów krzywa
hamowania (`Model.DesignServiceBrakeMps2`) faktycznie dociera do limitu planu — a to
zależy od parametrów modelu, nie od samego testu. Nic w pliku nie pinuje, że przy
dzisiejszych parametrach choć jeden z pięciu dystansów tę gałąź otwiera. Zmiana
parametrów hamowania albo limitu planu mogłaby wyłączyć tę gałąź po cichu.

## 5. Decyzja o bramce: NIE budowana

Rozkład 14/1/3 sam pokazuje, dlaczego bramka syntaktyczna (na samej zagnieżdżoności,
albo na samym słowie `if`/`while`/`try`) jest tu ślepa: złapałaby **15 z 18** przypadków
poprawnych — dokładnie „bramka, która zapala się na poprawnym kodzie" z 6.D27, którą
„wyłącza się, nie naprawia". Rozróżnienie (a)/(b) od (c) wymaga wiedzy, której żaden
statyczny czytnik tekstu nie ma: czy `try` ma `catch`; czy pętla idzie po literale, czy
po danych produkcyjnych; czy istnieje **osobny** test pinujący warunek gałęzi (jak
w przypadku (b)). To dokładnie ta sama granica, którą 6.D28 postawiła dla siebie wprost
w polu „Poza zakresem" — liczenie WYKONANYCH asercji wymaga rozbioru składni albo
wpięcia w runner testów. Automatyczna bramka na ten wzorzec zostaje więc **niezbudowana
świadomie**, a trzy przypadki (c) są udokumentowane tutaj z nazwami — spełnia to
„Skończone, gdy" wpisu w wariancie „uzasadnione pomiarem", bo liczba w kategorii (c) nie
jest zerem.

Testy same w sobie **nie zostały zmienione** — decyzja, jak dokładnie wzmocnić te trzy
metody (dopisać asercję pinującą warunek gałęzi, przepisać pętlę, czy coś trzeciego),
jest wyborem kształtu testu, którego ten pomiar świadomie nie przesądza.

## 6. Weryfikacja

```
$ python3 tools/tests/csharp_assertions.py
[ASERCJE C#] metod testowych:        727
[ASERCJE C#] z asercja w tresci:     727
[ASERCJE C#] BEZ asercji w tresci:   0
kod: 0

$ python3 tools/tests/test_all.py
  RAZEM 71.081 s, 1838 testów, 98 modułów
kod: 1

$ dotnet test tests/Sim.Tests --nologo
Passed! - Failed: 0, Passed: 565, Skipped: 0, Total: 565

$ dotnet test tests/Game.Tests --nologo
Passed! - Failed: 0, Passed: 205, Skipped: 0, Total: 205
```

**`test_all.py` kończy się kodem 1 — wklejone, nie ukryte.** Powód nie leży w tej
pozycji: `test_backlog.py` (`test_the_queue_holds_at_least_a_day_of_work`) liczy pozycje
fazy 6 do wzięcia i żąda co najmniej 12. Domknięcie **6.B28** i domknięcie **6.D29** (ta
pozycja) w tym samym oknie czasu, przez dwie niezależne sesje, zdjęło z licznika dwie
pozycje naraz i zbiło zapas z 12 do **11** — mechanizm nazwany wprost w `docs/TASKS.md`
§„Reguła zapasu": licznik opada od wykonywania pracy, nie od zaniedbania. Dopisałem
wymagany przez `test_the_documented_shortfall_is_written_down_while_it_lasts` akapit
`**Zapas udokumentowany:**` w `docs/TASKS.md` (ta bramka jest zielona), ale **nie
dopisałem nowej, w pełni udokumentowanej pozycji fazy 6**, żeby podnieść sam zapas do
progu — to wymaga własnego pomiaru/źródła (`CLAUDE.md` §6, sześć pól) i jest poza
wąskim zakresem tej korekty. `CLAUDE.md` §8 nazywa to wprost jako **następne zadanie**,
nie jako powód zatrzymania tej pozycji.

Liczba testów w `dotnet test` (565 + 205 = 770, w tym 8 nowych z 6.A14) i w
`csharp_assertions.py` (727) rosną względem poprzedniej wersji tego raportu wyłącznie
przez rebase na `main` — nie dotknięto ani jednego pliku `tests/**/*.cs` w tej pozycji.

## 7. Czego świadomie nie zrobiono

- **Nie budowano bramki** na wzorzec „asercja w niepewnie wchodzonej gałęzi" — §5.
- **Nie zmieniono treści żadnej z 18 metod**, w tym trzech (c) — decyzja, jak je
  wzmocnić, zostaje właścicielowi lub osobnej pozycji.
- **Nie zmieniono treści testów pętlowych** (65 „bezpiecznych") — poza zakresem z góry.
- **Nie dopisano nowej pozycji fazy 6**, żeby podnieść zapas kolejki z powrotem do
  progu 12 (§6) — zaznaczone jako znalezisko, nie zrobione w tym commicie.
- **Nie doszukano się do końca**, na którym dokładnie wzorcu mój własny, już
  nieistniejący prowizoryczny czytnik ślizgał się w `ServiceDayTests.cs` (§0/§3) — bez
  znaczenia dla wyniku, bo ten kod nigdy nie był commitowany i jest dziś zastąpiony
  oficjalną `maska()`.

## 8. Co zauważono przy okazji, ale nie tknięto

Nic nowego ponad to, co już zgłasza `docs/TASKS.md` 6.B28 i co ten raport nazwał wprost
w §6: zapas udokumentowanych pozycji fazy 6 stoi dziś na 11 przy progu 12, bo dwie
niezależne sesje domknęły swoje pozycje w tym samym oknie. To nie jest usterka tej
pozycji ani błąd pomiaru — jest zapisane w `docs/TASKS.md` i zniknie, gdy ktoś dopisze
kolejną udokumentowaną pozycję.
