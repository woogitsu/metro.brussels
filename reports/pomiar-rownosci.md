# Pomiar, na którym stoi decyzja 6.A22, jest pilnowany (6.A26)

**Zmierzone 07.09.2026 na commicie:** `becc2742eb65bc7ced1de865fd448b814c192fcf`
(baza gałęzi `claude/6a26-pomiar-rownosci`, czyli `main` po scaleniu #366).

## 1. Sprostowanie do własnego raportu

§10 `reports/postac-z-rownosciem.md` obiecał: gdyby komenda CI zaczęła postaci
`--opcja=wartość` używać wobec runnera, *„bramka z §5 pokaże to jako FAIL, zamiast
czekać na czyjeś oko"*.

**To była nieprawda i tu jest to pokazane, nie tylko powiedziane.** Bramka z §5
(`test_no_message_writes_a_known_option_in_the_equals_form`) czyta w całości tylko
jeden plik:

```python
source = _source()          # src/Sim.Runner/Program.cs
kod = _kod_bez_komentarzy(source)
for command, (values, flags) in table.items():
    for option in sorted(values | flags):
        if option + "=" in kod:
```

Komenda w `.github/workflows/*.yml`, w `docs/` albo w `tools/**/*.sh` nigdy nie
przechodziła przez ten kod. Decyzja 6.A22 — odrzucić postać z równością — była dobra
dokładnie tak długo, jak długo pomiar, na którym stanęła, był prawdziwy; nikt go nie
mierzył po tamtym dniu.

## 2. Pomiar dzisiejszy, z rozbiciem po wołanym programie

Klasyfikacja: sklejenie kontynuacji wierszy, potem podział każdego wiersza logicznego
po markerze wołanego programu.

Na drzewie, które idzie do scalenia:

```
razem 426   runner 1   scena 100   proza/kod 325
```

**Trzy pomiary, każdy z nazwanym drzewem, żaden nie wyrównany po cichu:**

| drzewo | razem | runner | scena | proza/kod |
|---|---|---|---|---|
| `main` przed 6.A25 i przed tą bramką | 409 | 1 | 99 | 309 |
| ta gałąź przed przestawieniem na `main` z 6.A25 | 419 | 1 | 99 | 319 |
| **ta gałąź po przestawieniu — stan do scalenia** | **426** | **1** | **100** | **325** |

Cały przyrost 409 → 426 jest **rozliczony po plikach**, nie zgadnięty:

```
  49 ->   50   docs/TASKS.md                       (wiersze 6.A25 i 6.A26)
   0 ->    5   reports/pomiar-rownosci.md          (ten raport)
   4 ->   15   tools/tests/test_runner_options.py  (klasyfikator i jego kontrole)
```

Bramka, która liczy także siebie, ma to powiedzieć wprost — inaczej pierwszy commit
dopisujący do niej test wyglądałby jak wzrost liczby komend w repozytorium. Kubełek
`scena` wzrósł o jeden z tego samego powodu: wzorce kontrolne KN-E i testu
pierwszeństwa niosą marker sceny i postać z równością, więc bramka widzi je tak samo
jak prawdziwe komendy sceny — i to jest poprawne, bo one **są** komendami sceny,
tylko syntetycznymi.

Jedyna komenda runnera w tej postaci:

```
docs/TASKS.md:3301  dotnet run --project src/Sim.Runner -c Release -- line
                    --axis data/track/L1_A.json --limit-kmh=72 --exchange-s 20
```

To pole **Weryfikacja** pozycji 6.A22 — komenda, której **całym sensem** jest pokazanie
odmowy dla tej postaci. Przepisana na dwa człony przestałaby weryfikować to, co tamta
pozycja zrobiła. Jest więc jednym wpisem na liście usprawiedliwień, z powodem przy
sobie, a osobny test pilnuje, żeby usprawiedliwienie nie przeżyło komendy, którą
opisuje (ta sama zasada, co 6.D29 dla wyjątków raportów i 6.B34 dla martwych stałych).

Klucz usprawiedliwienia to **(ścieżka, fragment komendy)**, nie numer wiersza: numer
przesuwa każdy commit dopisujący cokolwiek wyżej w pliku, a bramka zapalająca się na
tekście poprawnym zostaje wyłączona, nie naprawiona (nauczka 6.D27).

## 3. Kontrole — WYKONANE, nie opisane

**KN-A (dodatnia) — wstrzyknięta komenda runnera z równością** w prawdziwym pliku,
złamana na trzy wiersze, tak jak każda komenda w `docs/`:

```
FAIL test_no_runner_command_in_the_repository_uses_the_equals_form: komenda
     `Sim.Runner` w postaci `--opcja=wartość`, ktorej runner od 6.A22 nie przyjmuje:
    docs/TASKS.md:3948  dotnet run --project src/Sim.Runner -c Release -- budget
                        --axis data/track/L1_A.json --trains=3 --steps 100
13/14 przeszło
```

Plik i numer wiersza, i to numer **pierwszego** wiersza komendy — tego żądało pole
„Skończone, gdy".

**KN-B — wzorzec zepsuty** (wzorzec zmieniony na taki, który nie łapie nic):

```
FAIL test_the_equals_form_count_has_not_collapsed_to_nothing: postac z rownoscia
     wystepuje 0 razy przy progu 250
FAIL test_the_gate_catches_a_runner_command_written_in_the_equals_form
FAIL test_no_scene_command_is_reported_as_a_runner_command: wzorzec kontrolny nie ma rownosci
FAIL test_every_justification_still_describes_a_command_that_exists
10/14 przeszło
```

**Rzecz, którą ta kontrola pokazuje wprost:** `test_no_runner_command…` zostaje
**zielony**. Zero komend runnera to zero — i dokładnie tą drogą bramka kłamie w stronę
„wszystko w porządku". Próg na łączną liczbę wystąpień jest po to, żeby jej tę drogę
odebrać, i to jest jedyny powód jego istnienia.

**KN-C — sklejanie kontynuacji wyłączone**, z tą samą wstrzykniętą komendą:

```
FAIL test_the_gate_catches_a_runner_command_written_in_the_equals_form: klasyfikator
     nie widzi wstrzykniętej komendy runnera jako jednego wiersza logicznego —
     trzy wiersze osobno, marker w pierwszym, równość w trzecim
FAIL test_every_justification_still_describes_a_command_that_exists
12/14 przeszło
```

Bez sklejania komenda **znika z pola widzenia**: marker wołanego programu stoi
w pierwszym wierszu, a równość w trzecim — liczone osobno, trzeci wiersz nie ma
żadnego markera i wpada do prozy. Sklejanie jest więc nośne, nie kosmetyczne.

**KN-D — pierwszeństwo sceny zdjęte** (runner sprawdzany pierwszy):

```
15/15 przeszło          ← przed dopisaniem testu pierwszeństwa
FAIL test_a_line_naming_both_programs_counts_as_scene_not_runner: wiersz niosacy oba
     markery poszedl do kubelka runner — pierwszenstwo sceny jest zdjete
14/15 przeszło          ← po dopisaniu
```

**To jest znalezisko o mojej własnej bramce, nie o kodzie.** Pierwsza wersja
klasyfikatora sprawdzała scenę pierwszą i wyjaśniała powód komentarzem — a KN-D
zostawiła zestaw **zielony**, bo w dzisiejszym drzewie nie ma ani jednego wiersza
niosącego oba markery. Reguła nie była więc pilnowana wcale: była komentarzem.
Dopisany test przybija ją na wejściu syntetycznym, i dopiero wtedy KN-D coś wywraca.

Reguła zostaje taka, jaka była — scena postaci z równością **wymaga**, przybite
testami w `tests/Game.Tests`, więc bramka zgłaszająca scenę zostałaby wyłączona
w tym samym tygodniu, w którym powstała. Zmieniło się to, że jest mierzona.

**KN-E — kontrola ujemna, o którą prosiło pole „Skończone, gdy":** ani jedna z **99**
komend sceny nie jest zgłaszana. Sprawdzane dwoma sposobami: przejściem po całym
drzewie (lista zgłoszeń zawiera dokładnie jedną pozycję, tę usprawiedliwioną) i wzorcem
kontrolnym z równością, który ma być widziany jako scena.

## 4. Weryfikacja

```
$ python3 tools/tests/test_all.py test_runner_options.py
  15/15 przeszło          (9 → 15, sześć nowych testów)
```

## 5. Czego świadomie nie zrobiono

- **Nie obsłużono postaci `--opcja=wartość` w runnerze** — 6.A22 odrzuciła ją pomiarem
  i ta pozycja tego nie zmienia; zmienia to, że pomiar jest pilnowany.
- **Nie tknięto konwencji sceny.** Ujednolicenie dwóch połów projektu jest decyzją
  właściciela, a nie skutkiem ubocznym bramki.
- **Próg łącznej liczby stoi na 250, nie na 419.** Proza rośnie i maleje razem
  z raportami, więc próg przy dzisiejszej liczbie zapalałby się przy każdym usunięciu
  raportu — czyli na tekście poprawnym. Ma łapać zejście **do zera**, nie wahanie
  o kilkadziesiąt.
- **Lista rozszerzeń plików jest wypisana ręcznie.** Nowy format niosący komendę nie
  byłby widziany — ale odsianie po rozszerzeniu jest tańsze i przewidywalniejsze niż
  czytanie każdego pliku w drzewie, a próg z KN-B łapie zejście liczby do zera także
  wtedy, gdy przyczyną jest lista rozszerzeń.

## 6. Zauważone przy okazji, nie tknięte

**Dwie ścieżki `net8.0` obok jednej `net10.0`.** Wołanie DLL wprost jest jednym
z dwóch markerów runnera, więc te ścieżki przeszły mi przez ręce przy pomiarze:
```
reports/T-311-braking.md:257    Sim.Runner/bin/Release/net8.0/…
reports/T-400-first-run.md:235  Sim.Runner/bin/Release/net8.0/…
reports/linecore-budget.md:91   Sim.Runner/bin/Release/net10.0/…
$ grep TargetFramework src/Sim.Runner/Sim.Runner.csproj
    <TargetFramework>net10.0</TargetFramework>
```

Projekt buduje `net10.0`, więc dwie z tych trzech komend wskazują na katalog, którego
w drzewie nie ma. Oba raporty są **pomiarami z datą** i ich się nie przelicza — komenda
w prozie raportu nie jest bramką i miała rację w dniu, w którym ją wykonano. Nie
tknięte, ale warte zapisania: pole „Weryfikacja" cytujące taką ścieżkę **byłoby**
niewykonalne, a bramki na to nie ma.
