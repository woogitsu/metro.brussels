# 6.D265 — piętnaście opakowań korzenia, których 6.D257 nie zdjęło

**Data:** 18.09.2026 · **Gałąź:** `claude/6d265-opakowania-korzenia` · **Baza:** `827d200`

## 1. Co stało w drzewie

Trzy rodziny identycznych pomocników z pomiaru 6.D261 były jednowierszowymi
delegacjami do `KorzenRepozytorium`, zostawionymi przez 6.D257:

| nazwa | definicji | zwraca | ciało |
|---|---|---|---|
| `RepositoryRoot` | 9 | `string` | `MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka;` |
| `RepoRoot` | 3 | `string` | `MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka;` |
| `FindRepositoryRoot` | 3 | `string?` | `MetroBxl.Tests.Shared.KorzenRepozytorium.SciezkaAlboNull;` |

Razem **15** definicji w **15** plikach — po jednej na plik.

## 2. Odpowiedź na pole „Wyjście": ile wywołań i którego rodzaju

Liczone czytnikiem z granicą słowa `(?<![A-Za-z0-9_.])NAZWA\(\)`, z pominięciem
samych wierszy definicji. Wyprzedzenie `FindRepositoryRoot` przed `RepositoryRoot`
jest tu treścią, nie kolejnością w słowniku: bez niego `RepositoryRoot`
złapałby ogon tej dłuższej nazwy.

| nazwa | wywołań | plików | zamiennik |
|---|---|---|---|
| `RepositoryRoot` | 21 | 9 | `KorzenRepozytorium.Sciezka` |
| `RepoRoot` | 32 | 3 | `KorzenRepozytorium.Sciezka` |
| `FindRepositoryRoot` | 5 | 3 | `KorzenRepozytorium.SciezkaAlboNull` |
| **razem** | **58** | **15** | |

Bez zmiany wyrażenia da się zamienić **53** wywołania; **5** wymaga wariantu
zwracającego `null`, bo `FindRepositoryRoot` było zadeklarowane jako `string?`.
Wystąpień na wiersz jest dokładnie jedno — sprawdzone, nie założone: żaden
z 58 wierszy nie ma dwóch wywołań, więc liczba wystąpień równa się liczbie
ruszonych wierszy. Największe skupisko to `RunnerCommandTests.cs` — 28 wywołań
z 58, czyli prawie połowa całości w jednym pliku.

## 3. Rodziny po zdjęciu

| | przed | po |
|---|---|---|
| rodziny IDENTYCZNE | 10 | **7** |
| rodziny JEDNOIMIENNE | 14 | **14** |
| podpisy `private static` pod `tests/` | 237 | 222 |

Liczba jednoimiennych nie ruszyła się i było to przewidziane przed przebiegiem:
żadna z trzech zdjętych nazw nie stała nad innym ciałem, więc do tamtej kupki
nie należała ani jedna. Podłoga `MIN_PODPISOW_POMOCNIKA = 200` została nietknięta —
222 mieści się nad nią z zapasem 22, więc zejście o piętnaście podpisów nie
oślepia równości powyżej.

## 4. Kontrola negatywna

Zapadka `RODZIN_IDENTYCZNYCH` stoi od tej pozycji na 7, a obniżona została **po**
przebiegu, nie przed. Przebieg na drzewie już zmienionym, przy zapadce jeszcze
na dawnej dziesiątce:

```
FAIL test_ile_rodzin_pomocnikow_jest_DUPLIKATEM_a_ile_ZBIEGIEM_NAZW:
rodzin identycznych 7 i jednoimiennych 14, a pomiar 17.09.2026 dal 10 i 14.
Identyczne: ['Moving', 'Notch', 'Parse', 'Protection', 'Service', 'Stopped',
'StraightAxis']. ...
  19/20 przeszło
```

Bramka z 6.D261 zapaliła się i **wypisała obie liczby oraz skład kupki** — czyli
liczy to, co mówi, że liczy. Przewidywanie z pola „Weryfikacja" tej pozycji
(spadek z 10 do 7) trafiło co do jedności.

## 5. Kontrola przyrządu — i pierwsze podejście, które było ŚLEPE

Kontrola miała pokazać, że czytnik odróżnia stopnie, a nie tylko „jest / nie ma".
Wykonana na kopii drzewa w katalogu roboczym, z przywracaniem opakowań `RepoRoot`:

```
KP-0: zero opakowan                identyczne=7  RepoRoot w rodzinach: False
KP-2: JEDNA kopia                  identyczne=7  RepoRoot w rodzinach: False
KP-b: DWIE kopie                   identyczne=8  RepoRoot w rodzinach: True
KP:   cala rodzina x3              identyczne=8  RepoRoot w rodzinach: True
```

**Pierwsze podejście do tej kontroli dało cztery razy 7 i przyrząd był ślepy** —
nie drzewo. `pomocnicy` i `rodziny_pomocnikow` mają `root=ROOT` jako **domyślny
argument**, a domyślny argument wiąże się raz, przy imporcie modułu. Podstawienie
`csharp_test_methods.ROOT = <kopia>` nie zmieniło więc niczego: czytnik cały czas
patrzył w prawdziwe drzewo, gdzie opakowań już nie było. Cztery jednakowe wyniki
czytały się dokładnie jak „czytnik nie reaguje na przywrócenie opakowań", czyli
jak wynik o kodzie — a były wynikiem o kontroli. Jest to kształt 6.D27 z drugiej
strony: nie bramka, która nie zapala się na zepsutym, ale kontrola, która nie
widzi niczego i wygląda przy tym jak pomiar. Złapane wyłącznie dlatego, że ruch
z 7 na 8 był **przewidziany przed przebiegiem**; gdyby kontrola nie miała
zapisanego oczekiwania, jej cztery siódemki byłyby do opowiedzenia jako
odkrycie. Naprawa: `root` przekazywany wywołaniem, nie podstawiany w module.

**Granica rodziny leży przy DWÓCH kopiach, nie przy jednej.** Pole „Weryfikacja"
tej pozycji zapowiadało, że „pozostawienie JEDNEGO opakowania ma dać 8, a nie 7".
Pomiar rozdziela to na dwa różne zdania: dla jednej **rodziny** (2–3 kopie) jest
prawdziwe, dla jednej **kopii** — fałszywe, bo rodzina jest z definicji nazwą
w więcej niż jednym pliku, więc przedostatnia kopia zabiera z rejestru także
ostatnią. Zapowiedź nie była więc zła, tylko nierozstrzygnięta co do jednostki,
i dopiero pomiar to rozdzielił.

## 6. Czego świadomie nie ruszono

Pozostałych **siedmiu** rodzin identycznych — 6.D261 zmierzyło, że żadna nie
zasługuje na wspólny plik, i ta pozycja tego nie rewiduje. Rodzin jednoimiennych
nie ruszono w ogóle: scalanie ich jest błędem, nie sprzątaniem. `src/` nietknięte.
