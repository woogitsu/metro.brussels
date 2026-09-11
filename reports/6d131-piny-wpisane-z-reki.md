# 6.D131 — czterdzieści cztery piny w warstwie gry, i żadnego nie da się przybić inaczej

**Zmierzone 11.09.2026 na:** `dfc7543`, kontener tej sesji.
**Przyrząd:** `tools/tests/csharp_pins.py` (czytnik na masce z `csharp_test_methods`),
`tools/tests/test_csharp_pins.py`, `tests/Game.Tests/`, `tests/Sim.Tests/`.

---

## 1. Liczba

| katalog | pinów | plików z pinem | plików razem | pinów na plik |
|---|---|---|---|---|
| `tests/Game.Tests` | **44** | 8 | 16 | **2,75** |
| `tests/Sim.Tests` | **74** | 20 | 36 | **2,06** |

Pin to asercja, której **wartością oczekiwaną jest literał napisowy**:
`Assert.AreEqual`, `StringAssert.Contains/StartsWith/EndsWith`,
`CollectionAssert.AreEqual`. `Assert.IsTrue` pinem nie jest — nie niesie wartości
oczekiwanej, tylko warunek.

Rozkład w warstwie gry: `RunPlanTests.cs` **30**, `UiTextTests.cs` **5**,
`ChunkManifestTests.cs` **3**, `RunResetTests.cs` **2**, po jednym
`HudLayoutTests.cs`, `RunHeaderTests.cs`, `SignallingHudTests.cs`,
`TelemetryTrackTests.cs`.

**Gra pinuje gęściej od rdzenia** — 2,75 wobec 2,06 na plik — mimo że ma o połowę
mniej plików testowych. To jest liczba porównawcza, o którą prosiło pole „Wejście".

## 2. Czytnik jest LEKSYKALNY, nie składniowy

Pole „Wyjście" prosiło o liczbę „policzoną z drzewa składni". **Drzewa składni C#
w tym repozytorium nie ma i mieć nie będzie:** jedyną drogą byłby Roslyn, czyli nowa
zależność, a tych projekt nie dokłada — ta sama reguła, która w 6.D85 zabroniła
walidatora JSON Schema.

Zamiast tego czytnik stoi na `csharp_test_methods.maska`, która zamienia komentarze
i literały na spacje **znak w znak**, zachowując indeksy. Granice tego rozwiązania są
zmierzone i wypisane w module: czytnik nie wie, czy wywołanie stoi w metodzie
testowej, czy w pomocniku, i nie rozwija stałych — `Assert.AreEqual(OCZEKIWANY, x)`
z `const string OCZEKIWANY` nie jest tu pinem, choć nim jest.

**Pułapka, w którą wpadłem:** pierwsza wersja przeskakiwała białe znaki **po masce**,
a w masce literał jest spacjami — pętla przechodziła przez niego na wylot i czytnik
zgłaszał **0 pinów zamiast 44**, w obu katalogach naraz. Zero wyglądało jak wynik.

## 3. Kategorie — podział ZAPISANY, bo reguła się myli

| kategoria | ile | co to jest |
|---|---|---|
| **A — wynik złożony z kilku źródeł** | **4** | `UiTextTests.cs:490, :496, :501`, `SignallingHudTests.cs:37` |
| **B — wejście syntetyczne kontroli przyrządu** | **2** | `UiTextTests.cs:570, :571` |
| **C — wartość liczona w jednym miejscu** | **38** | reszta: nazwy trybów, ścieżki, identyfikatory |

**Próbowałem reguły mechanicznej i zmierzyłem, że się myli.** Reguła „literał zawiera
interpunkt albo dwie spacje pod rząd = wynik złożony" myli się na **dwóch z czterech**
przypadków kategorii A i B:

* **przepuszcza** `UiTextTests.cs:501` — wiersz o hamulcu awaryjnym, złożony, ale
  rozdzielony pojedynczymi spacjami;
* **łapie** `UiTextTests.cs:571` — który pinem wyjścia nie jest wcale, bo to wejście
  syntetyczne kontroli `BezDziur`.

Reguła myląca się w połowie przypadków jest gorsza niż wypisana tabela, bo **zmyśla
kategorię tam, gdzie nikt nie patrzy**. Stąd podział jest zapisany, a osobny test
(`test_regula_po_ksztalcie_literalu_myli_sie_i_dlatego_jej_nie_ma`) pilnuje, żeby to
rozstrzygnięcie nie stało się opinią: wykonuje tamtą regułę i żąda dokładnie tych
dwóch pomyłek.

## 4. Rozstrzygnięcie: żadnego nie da się przybić inaczej

Pole „Skończone, gdy" pyta, czy którykolwiek pin da się zastąpić. Odpowiedź brzmi
**nie**, i to dla każdej kategorii z innego powodu:

* **A** — wartość liczona z katalogu byłaby **porównaniem katalogu z samym sobą**.
  Pole „Skończone, gdy" pozycji 6.D99 żądało wypisu tych samych wierszy wprost i to
  jest ta sama decyzja, podjęta wtedy świadomie.
* **B** — to nie są piny, tylko **dane wejściowe** testu. Literał jest tu treścią
  próbki i inaczej zapisać się go nie da.
* **C** — wartość stoi w jednym miejscu produkcyjnym, więc jedyną alternatywą byłaby
  **wspólna stała** dzielona z kodem produkcyjnym. To zamienia pin w porównanie kodu
  z samym sobą — czyli w to, przed czym pin miał bronić. Cicha zmiana nazwy trybu
  z `"manual"` na `"reczny"` przeszłaby wtedy bez śladu.

Obawa z pola „Skąd" — że koszt pinu rośnie liniowo z tabelą przypisań — **jest
prawdziwa i zostaje**. Odpowiedzią nie jest rozluźnienie pinu, tylko świadomość, że
ten koszt jest ceną niezależności od kodu, który pin pilnuje.

## 5. Dwie kontrole, które wyszły ZIELONE, i co z nich wynikło

**KN-4** zastąpiła maskę samym źródłem. Wynik: **5/5, zielono.** W całym
`tests/Game.Tests` nie ma dziś ani jednego `Assert.AreEqual("` wewnątrz komentarza
albo napisu, więc na tym drzewie maska **nie zmienia ani jednej liczby**.

Gorzej: mój test maski składał ją **sam** i przez to nie pilnował `piny()` wcale — był
zielony niezależnie od tego, czy czytnik maski używa. Przepisany na przejście przez
`piny()` na drzewie probnym; po tej zmianie **KN-4b jest czerwona** (`czytnik policzył
wywołanie z komentarza`). Maska zostaje **ubezpieczeniem, nie zmierzoną koniecznością**,
i tak jest opisana.

**KN-6** dopisała `Assert.IsTrue` do wzorca. Wynik: **5/5, zielono** — i to jest
poprawne. `IsTrue` bierze `bool`, więc literału napisowego jako pierwszego argumentu
nie ma w drzewie ani jednego i mieć nie może. Wykluczenie jest **definicyjne, nie
zmierzone**; żadna kontrola negatywna tego nie odróżni, bo różnica jest w typie, nie
w danych. Zapisane przy wzorcu.

## 6. Kontrole negatywne — WYKONANE, nie opisane

Baza `test_csharp_pins.py`: **5/5** (moduł nowy, 122. w zestawie).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | nowy pin dopisany do pliku z tabeli | **3/5**, dwa testy |
| KN-2 | białe znaki przeskakiwane po masce (mój pierwszy błąd) | **1/5**, cztery testy, **0 pinów** |
| KN-3 | sklejanie literałów `"…" + "…"` zdjęte | **4/5**, 122 znaki → 38 |
| KN-4 | skan bez maski | **5/5 ZIELONA** — patrz §5 |
| KN-4b | to samo po wzmocnieniu testu maski | **4/5** |
| KN-5 | kategoria A wskazuje pin, którego nie ma | **3/5**, dwa testy |
| KN-6 | `Assert.IsTrue` dopisane do wzorca | **5/5 ZIELONA — poprawnie** |

Po każdej: `md5sum -c` → `OK` na trzech plikach.

KN-2 jest tu warta zdania: odtwarza mój własny błąd i pokazuje go tak, jak wyglądał —
**zero pinów w obu katalogach**, czyli wynik, który bez tabeli kategorii czytałby się
jako „nie ma pinów", a nie jako „czytnik nie działa".

## 7. Czego nie zrobiłem

* **Nie zdjąłem ani nie przepisałem żadnego pinu** — wprost w polu „Poza zakresem".
  Ta pozycja mierzy i rozstrzyga.
* **Nie objąłem czytnikiem `Assert.AreEqual` z wartością LICZBOWĄ.** Pin na `9.40`
  albo `4L` też jest pinem wpisanym z ręki, ale pole „Skąd" mówi o wierszu pomocy,
  czyli o napisach, a rozszerzenie zmieniłoby liczbę, o którą pozycja pytała.
  Do wzięcia osobno.
* **Nie rozwijam stałych.** `Assert.AreEqual(OCZEKIWANY, x)` z `const string` nie jest
  tu policzony; wymagałoby to rozwiązywania nazw, czyli tego drzewa składni, którego
  nie ma.

## 8. Uzupełnienie kolejki w tym samym commicie

Domknięcie 6.D131 zbija kolejkę z dwunastu pozycji DO WZIĘCIA na **jedenaście**, czyli
poniżej progu z `CLAUDE.md` §8. Bramka zapaliła się dokładnie tym zdaniem:

```
FAIL test_the_documented_shortfall_is_written_down_while_it_lasts: zapas udokumentowany to 11 przy progu 12, a plan o tym milczy
FAIL test_the_queue_holds_at_least_a_day_of_work: kolejka ma 11 pozycji DO WZIĘCIA przy progu 12 (wpisanych: 11, czeka na właściciela: żadna); pierwszym zadaniem jest uzupełnienie fazy 6, nie zatrzymanie się
```

Uzupełnienie idzie tym samym commitem, z tej samej arytmetyki, co przy 6.D96, 6.D102
i 6.D125: commit z samym domknięciem zostawiłby drzewo czerwone.

Sześć pozycji, **żadna nie wymyślona pod pustą kolejkę** — każda ma źródło w pomiarze
zrobionym przy wykonywaniu 6.D126, 6.D127, 6.D130 albo 6.D131:

| nowa | skąd |
|---|---|
| 6.D141 · piny liczbowe nie są policzone | z tej pozycji, §7 — czytnik widzi tylko literał napisowy |
| 6.D142 · `NazwyKlawiszy` jest wyjątkiem bez zastosowania | z 6.D130, **KN-4 zielona** |
| 6.D143 · `KeyNames.cs` nie jest skanowany | z 6.D130 — powód, dla którego objawu nie dało się odtworzyć |
| 6.D144 · ile kosztuje dopisanie komunikatów w jednym module | z 6.D127 — 117 asercji w `test_clearance_profile.py` |
| 6.D145 · asercje C# bez komunikatu nie są policzone | z 6.D127 — bramka staje na granicy języka |
| 6.D146 · ile bloków wykonanych ma zły adres | z 6.D126, pole „Poza zakresem" nazwało to wprost |

Trzy z nich (6.D142, 6.D143, 6.D145) nie wyszły z lektury, tylko z **kontroli, która
wyszła zielona**, albo z granicy czytnika wypisanej w jego własnym module — czyli
z miejsc, w których pomiar powiedział coś, czego wpis pozycji nie przewidywał.

Zapadka `MINIMUM_DETAIL_BLOCKS`, podniesiona z 213 na 219. Wartość jest wynikiem
`len(detail_sections(...))` na pliku **po edycji**, nie sumą 213 i sześciu — sześć
bloków dopisanych jednym commitem to dokładnie ten przypadek, w którym arytmetyka
z pamięci się myli.

Po uzupełnieniu:

```
  53/53 przeszło   (test_backlog.py 31, test_field_paths.py 22)
```

pozycji DO WZIĘCIA: **17**, wpisanych: 17, czeka na właściciela: żadna.
