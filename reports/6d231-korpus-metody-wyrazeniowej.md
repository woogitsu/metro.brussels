# 6.D231 — `KorpusMetody` przy metodzie WYRAŻENIOWEJ zwracał korpus NASTĘPNEJ

**Data:** 17.09.2026 · **Gałąź:** `claude/6d231-korpus-wyrazeniowej` · **Baza:** `bb370e8`

## 1. Co było nieprawdą, i widać to w pięciu wierszach źródła

`KorpusMetody` w `tests/Sim.Tests/DefaultArmAuditTests.cs` szukał korpusu tak:
znajdź deklarację, weź pierwszą klamrę po niej, domknij. Metoda **wyrażeniowa**
własnej klamry nie ma, więc pierwsza klamra po deklaracji należy już do czegoś innego:

```
295:    public double BrakingDistanceM(double speedMps) =>
296:        speedMps <= 0.0 ? 0.0 : _solver.Solve(speedMps, 0.0, _serviceBrakeMps2).DistanceM;
…
307:    public ProtectionDecision Supervise(FixedBlockSystem system, string trainId, …)
```

Zapytany o `BrakingDistanceM`, czytnik zwracał **korpus `Supervise`** — 3056 znaków
zaczynających się od `ArgumentNullException.ThrowIfNull(system)`. Straż `deklaracji == 1`
tego nie łapie, bo deklaracja jest jedna i jest właściwa; fałszywy jest **korpus**.

## 2. Populacja

Pomiar wykonany dwiema niezależnymi sondami, bo rozbieżność jest tu wynikiem:

```
plikow .cs w src/Sim:                        59
deklaracji wyrazeniowych (sonda tej pozycji): 119
deklaracji wyrazeniowych (sonda pomiarowa):   123
```

Różnica czterech to deklaracje wieloliniowe i kształty na granicy wzorca — obie sondy
zgadzają się co do rzędu wielkości i co do liczby plików. Sonda pomiarowa rozłożyła
123 na cztery klasy, z których **81 czytnik przepuszczał bez jednego słowa odmowy**:
**41** zwracało korpus obcej składowej, **40** urywek własnego wyrażenia (pierwsza
klamra wpadała w dziurę interpolacji albo w switch-wyrażenie). Pozostałe łapała straż
`deklaracji != 1` albo brak klamry w ogóle.

Kotwica z treści pozycji odtworzyła się **co do znaku**: `KorpusMetody("BrakingDistanceM")`
daje `deklaracji = 1` i 3056 znaków cudzego korpusu.

## 3. Rozstrzygnięcie: ODMOWA z powodem, nie zwracanie treści wyrażenia

Pole „Wyjście" dopuszczało oba. Wybrana odmowa, bo zwracanie treści wyrażenia kazałoby
`ObsluzoneCzlony` czytać **switch-wyrażenie**, a to jest osobny czytnik i osobna decyzja —
klasyfikator ramion z 6.D210 stoi w polu „Poza zakresem".

Rozpoznanie jest **leksykalne**, bez rozbioru składni C# (też pole „Poza zakresem"):
między deklaracją a klamrą metody klamrowej stoi wyłącznie lista parametrów i ograniczenia
typów, a `=>` w żadnym z nich wystąpić nie może.

Odmowa niesie **powód**, nie `null`: sygnatura `KorpusMetody(…, out int deklaracji)`
dostała `out string? powod`, a dwa miejsca wołania podają go w komunikacie asercji.
Dawny komunikat brzmiał jednakowo („nie udało się domknąć korpusu") dla trzech różnych
przyczyn.

## 4. Kontrole negatywne — wykonane przeze mnie na drzewie scalonym

Pomiar tej pozycji przyszedł z osobnego przebiegu na starszej bazie. **Powtórzyłem dwie
decydujące na dzisiejszym drzewie**, bo raport z cudzego przebiegu nie jest weryfikacją
mojego commita. Baza: `663/663`, kod 0.

| mutacja | przewidziane | zmierzone |
|---|---|---|
| KN-1 gałąź `=>` usunięta — **konfiguracja, DLA KTÓREJ łatka powstała** | czerwone, jedna asercja | **`Failed: 1, Passed: 662`**, `Assert.IsNull failed. metoda wyrażeniowa ma dostać ODMOWĘ, a czytnik zwrócił:` |
| KN-P1 **kontrola DODATNIA** — `BrakingDistanceM` przepisana na klamrową, równoważnie | zielone, 663 | **`Passed! - Failed: 0, Passed: 663`** |

Każda mutacja z asercją, że się **zastosowała** (KN-1 sprawdza, że napis „jest WYRAŻENIOWA"
zniknął z pliku — `grep -c` daje 0). Po każdej przywracanie z kopii, `md5sum -c` → `OK`.

**KN-P1 jest tu ważniejsza od KN-1** i to nie jest zdanie ogólne: dwie pozycje tego samego
dnia (6.D237, 6.D238) miały kontrolę dodatnią **czerwoną**, czyli bramkę zapalającą się na
pracy poprawnej, i w obu wypadkach dowiedziałem się tego wyłącznie z tej kontroli. Tutaj
przepisanie metody wyrażeniowej na klamrową jest dokładnie taką pracą poprawną — i jest
zielone.

## 5. Zapadki

Żadnej nowej. Cztery istniejące **równości** przesunięte, bo pozycja dokłada kod testowy;
wszystkie cztery są równościami na populacji `tests/`, więc zapasu nie mają i mieć nie
powinny — taka jest ich konstrukcja:

| stała | dziś | wcześniej | co doszło |
|---|---|---|---|
| `ASERCJI_RAZEM` | **3179** | 3170 | 9 asercji nowej kontroli przyrządu |
| `Z_KOMUNIKATEM_RAZEM` | **1732** | 1723 | te same 9, wszystkie z komunikatem |
| rozkład pinów | razem **479**, bez tolerancji **291**, całkowite **283** | 477 / 289 / 281 | 2 piny całkowite bez tolerancji |
| rozkład literałów `tests/` | zwykły **4583**, interpolowany **789** | 4562 / 783 | literały czytnika i jego komunikatów |

**Kolejność kolumn w tej tabeli jest wymogiem, nie układem.** Czytnik twierdzeń
`test_report_claims` bierze PIERWSZĄ liczbę stojącą po nazwie stałej, więc zapis
„stara → nowa" czyta się jako twierdzenie o wartości STAREJ i zapala bramkę. Zapaliła
się na tym raporcie przy pierwszym przebiegu, na dwóch wierszach; dlatego wartość
dzisiejsza stoi przed poprzednią.

Że te liczby zgadzają się z drzewem, **nie jest tu twierdzeniem z łatki**: wszystkie cztery
są asercjami równości, więc zielony przebieg `59/59` na tych modułach **jest** ich pomiarem.

`ZAPADEK_RAZEM` w `tools/tests/test_tree_walks.py` **nie rusza się** — pozycja nie dokłada
progu. `MIN_REPORTS` o jeden, za ten raport.

## 6. Czego NIE zrobiono

- **Nie dopisano piątego wpisu do `PolykaneCzlony`** — jawnie poza zakresem.
- **Nie tknięto klasyfikatora ramion z 6.D210** ani `ObsluzoneCzlony` — poza zakresem,
  mimo że pomiar pokazał, że osiem kandydatów niesie switch **wyrażeniowy**, którego ten
  klasyfikator nie czyta.
- **Nie zbudowano rozbioru składni C#** — pole „Poza zakresem" żąda czytnika wzorcowego.
- **Nie naprawiono 22 przypadków łapanych dziś przez straż `deklaracji != 1`**
  (przeciążenia `ToString`, `M7`) — inna klasa, inna pozycja.

## 7. Co zauważone przy okazji, nietknięte

- **`Korpus` ma tę samą ślepotę na literały napisowe.** 40 ze 123 metod wyrażeniowych
  dostawało urywek z dziury interpolacji (`$"FixedStep({Seconds:R} s)"` → zwrot `Seconds:R`).
  Ta łatka zamyka to po drodze, bo odmowa przychodzi wcześniej — ale **metoda KLAMROWA,
  której korpus zaczyna się od literału z klamrą, nadal jest czytana źle**. Dziś żadna
  z czterech w `PolykaneCzlony` taka nie jest, więc to leży i czeka.
- **Deklaracja wieloliniowa jest dla wzorca niewidzialna** — ta sama ślepota, którą 6.D221
  opisało przy swoim czytniku. `KorpusMetody` dostaje wtedy `deklaracji = 0` i odmawia,
  czyli milczy zdrowo; ale wpis na taką metodę byłby nie do zrobienia.
- **`ZrodlaRdzenia` czyta tylko `src/Sim/`** — `src/Game/` i `src/Sim.Runner/` nie są objęte
  tą bramką w ogóle. Nie wiem, czy to decyzja, czy przeoczenie.
- **`doctor.sh` melduje brak `dotnet`, choć SDK leży w `~/.dotnet`**, bo sonduje `PATH`.
  Fałszywy brak jest gorszy od prawdziwego: wygląda na uczciwe zatrzymanie się (§8), a jest
  pominięciem połowy pętli z §5. Sam w to wdepnąłem dziś cztery razy. Osobna pozycja.
