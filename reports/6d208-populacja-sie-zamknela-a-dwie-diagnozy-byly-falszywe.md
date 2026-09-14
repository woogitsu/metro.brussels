# 6.D208 — populacja się zamknęła, a dwie diagnozy okazały się fałszywe

**14.09.2026**, na `c5c78b9`. Wejście: `docs/TASKS.md` (pola „Skąd" pozycji otwartych),
`tools/tests/test_backlog.py` (`twierdzenia_w_polach_skad`, `open_items`,
`detail_sections`), `reports/6d196-osiemdziesiat-liczb-polowa-nieprawdziwa.md` §2 i §5.

## 1. Populacja, o której mówiła pozycja, w większości ZAMKNĘŁA SIĘ — i zrobiłem to ja

Pole „Skąd" mówi o **15 liczbach rozjechanych w polach „Skąd" pozycji OTWARTYCH**,
zmierzonych 13.09.2026. 6.D196 nazwało pozycje, które je niosą: 6.D199, 6.D201, 6.D203,
6.D204 i 6.D207. Zmierzone dzisiaj:

| pozycja | otwarta dziś? |
|---|---|
| 6.D199 | **nie** — domknięta |
| 6.D201 | **nie** — domknięta |
| 6.D203 | **nie** — domknięta (dziś, #608) |
| 6.D204 | **nie** — domknięta (dziś, #609) |
| 6.D207 | tak (domknięcie czeka w #612) |

**Cztery z pięciu zamknęły się, a dwie z nich zamknąłem dzisiaj, kilka godzin przed tą
pozycją.** Wiersz pozycji domkniętej jest zapisem swojego dnia i przepisywaniu nie
podlega (6.D108) — a `twierdzenia_w_polach_skad()` z `test_backlog.py` czyta wyłącznie
pozycje otwarte i zwraca dziś **zero** twierdzeń.

To nie jest wymówka, tylko własność mechanizmu, którą ta pozycja odsłania: **„praca po
pomiarze" ma okno, a okno zamyka domknięcie pozycji.** Praca wykonalna dziś dotyczy
więc populacji **dzisiejszej**, i ona została przeliczona w całości.

## 2. Populacja dzisiejsza: 13 bloków, 8 pól z liczbami przeliczalnymi

Pozycji otwartych jest **18**, z tego **13** ma blok szczegółów z polem „Skąd".
Liczby przeliczalne stoją w **ośmiu** z nich; `6.D207`, `6.D209` i `6.D212` nie niosą
żadnej, a `6.M1` i `6.M2` niosą wyłącznie „08" z nazwy MB-08.

| pozycja | twierdzenie | werdykt |
|---|---|---|
| **6.D208** | 30 przeliczalnych, 15 niezgodnych | **datowane** — populacja z 13.09, dziś inna (sekcja 1) |
| **6.D210** | 12 switchy: 8 wyrażeniowych + 4 instrukcyjne | **poprawione na 14: 10 + 4**; adres `LineCore.cs:667` → `:881` |
| **6.D211** | 7 z 17 członów, 10 do `default`, 2 z 3 `ProtectionAction` | **wszystkie liczby się trzymają**; poprawiony tylko adres `LineCore.cs:667` → `:881` |
| **6.D213** | 3 wywołania `.ToString()`, trzy adresy | **trzyma się co do numeru wiersza** — jedyne takie |
| **6.D214** | „dwie z dwunastu… bo wyrażenie przechodzi do następnego wiersza" | **liczba zostaje, DIAGNOZA FAŁSZYWA** (sekcja 3) |
| **6.D215** | „tę samą gałąź niosą jeszcze **trzy** czytniki" | **FAŁSZYWE — czytnik jest JEDEN** (sekcja 4) |
| **6.D216** | „14 z 22 z przedrostkiem", „2449 testów" | **nieprzeliczalne** bez czytnika `Literaly`; zapisana granica |
| **6.D217** | 25 wywołań `GD.Print` | **datowane: dziś 30** (wzrost drzewa, MB-06…MB-08) |

## 3. 6.D214 — przyczyną jest indeksator, nie łamanie wiersza

Pole twierdzi, że `.StopErrorM` wraca ze skanu urwane, „bo wyrażenie przechodzi do
następnego wiersza". **Obie pozycje mają całe wyrażenie w jednym wierszu:**

```
2382:                var blad = _line.Calls[^1].StopErrorM.ToString(
2383:                    BladZatrzymaniaFormat, CultureInfo.InvariantCulture);
```

Do następnego wiersza przechodzi **argument**, którego wzorzec w ogóle nie ogląda.
Urywa **indeksator**: `[\w.]+` nie wchodzi w `]`, więc z `_line.Calls[^1].StopErrorM`
zostaje `.StopErrorM`. Sprawdzone wykonaniem wzorca `([\w.]+)\.ToString\(` na trzech
próbkach różniących się jedną rzeczą:

| próbka | wynik |
|---|---|
| wiersz z indeksatorem (2382 dosłownie) | `.StopErrorM` |
| ten sam bez indeksatora | `_line.Ostatni.StopErrorM` |
| `.ToString(` przeniesione do następnego wiersza | **brak trafienia** |

**To jest trzecia liczba z kategorii (c) 6.D196 — nieprawdziwa w chwili wpisania** —
i pierwsza, w której fałszywa jest **przyczyna**, a nie sama liczba. Pytanie pozycji
(„ile czytników w drzewie ma ten sam wzorzec") zostaje, ale naprawa dotyczy **innego
zbioru miejsc**, niż pole zapowiada.

## 4. 6.D215 — czytnik jest jeden, a jeden z trzech naprawiło 6.D200

Gałąź „trzy cudzysłowy to napis surowy, bez patrzenia na `@`" stoi w **jednym** miejscu:
`tests/Game.Tests/UiTextTests.cs:588`, `var surowy = cudzyslowow >= 3;`.

- `KodLeksykalnie` **nie ma własnej kopii** — woła `CzytajLiteral` przez
  `PrefiksLiteralu`. Jest wołającym, nie czytnikiem.
- `maska` w `tools/tests/csharp_test_methods.py` **gałęzi już nie ma**: naprawiło ją
  **6.D200**, czyli ta sama pozycja, którą to pole cytuje jako źródło. Dziś stoi tam
  `surowy = cudzyslowy >= 3 and not verbatim` (wiersze 164 i 204).

Trzy niezależne dochodzenia schodzą więc do jednego, z dwoma wołającymi. **Czwarta
liczba z kategorii (c)** — i najbardziej kosztowna, bo nazywała jako niesprawne to,
co cytowana pozycja już naprawiła.

## 5. 6.D210 — teza się WZMOCNIŁA, a nie osłabła

Switchy po wartości wyliczeniowej jest w `src/Sim/` dziś **14**, nie 12: doszły
`DoorControl.cs:75` (`Refusal switch`) i `StationStop.cs:252` (`phase switch`), oba
z MB-08 **tego samego dnia**. Oba są postaci **wyrażeniowej** i oba mają ramię domyślne
**rzucające**, więc podział „wyrażeniowy rzuca / instrukcyjny milczy" trzyma się dziś
**10/10 i 4/4** — mocniej niż przy pomiarze 6.D197.

Sprawdzone też, że `ProtectionMode.cs:33` i `ParameterStatus.cs:32` **nie są** switchami
po wyliczeniu (obie biorą `string status`), czyli ósemka z dnia pomiaru była poprawna,
a nie przypadkowo trafiona.

## 6. Czego świadomie nie zrobiłem

- **Nie tknąłem pól „Skąd" pozycji DOMKNIĘTYCH** — 6.D108 mówi o nich wprost, a to
  właśnie tam trafiła większość tych piętnastu liczb.
- **Nie poszerzałem wzorca twierdzeń** — pole „Poza zakresem"; to jest 6.D209.
- **Nie zmieniałem rozmiarów `S`/`M`** ani nie domykałem pozycji, których liczby
  poprawiam (to samo pole). 6.D210, 6.D214 i 6.D215 zostają **otwarte**, z liczbami
  poprawionymi i pytaniami zapisanymi na nowo.
- **Nie przeliczyłem „14 z 22" z 6.D216** — wymaga uruchomienia czytnika `Literaly`,
  a skan po ogranicznikach mierzy co innego. Granica zapisana w polu.

## 7. Kolejka — domknięcie tej pozycji zbiło zapas poniżej progu

Po domknięciu 6.D207 i 6.D208 zapas **udokumentowany** (pozycje z kompletem sześciu pól)
zszedł do **11** przy progu 12, co zapaliło
`test_the_documented_shortfall_is_written_down_while_it_lasts`. `CLAUDE.md` §8 mówi
wprost, że wtedy **pierwszym zadaniem jest uzupełnienie kolejki** — więc 6.D218, wpisane
przy 6.D206 jako sam wiersz tabeli, dostało **komplet sześciu pól**. Zapas wrócił do
**12**, a podłoga na liczbę bloków szczegółów poszła tym samym commitem o jeden w górę.

**Nazwy tej stałej nie ma w zdaniu wyżej i to jest wymuszone przez bramkę, nie styl.**
`test_report_claims` czyta pierwszą liczbę po nazwie stałej w grawisach, a raport, który
poda JAKĄKOLWIEK jej wartość, zestarzeje się przy następnym podniesieniu — co zdarzyło
się temu zdaniu w ciągu jednej doby, przy 6.D209. Wartość zapadki stoi w commicie
i w `tools/tests/test_backlog.py`, gdzie jest pilnowana; w raporcie jest kierunek.

## 8. Zauważone, nie tknięte

- **Bramka `twierdzenia_w_polach_skad()` zwraca dziś zero**, i zero znaczy tu dwie różne
  rzeczy naraz: „nie ma rozjazdów" i „nie ma twierdzeń w kształcie, który czytnik widzi".
  Dolnego ostrza ta funkcja nie ma; kształtu ``` `NAZWA = N` ``` dotyczy 6.D209, ale
  **braku ostrza nie dotyczy nic**.
- **Cztery z pięciu pozycji niosących te liczby domknąłem w ciągu jednego dnia**, w tym
  dwie kilka godzin przed wzięciem 6.D208. Kolejność brania pozycji z tabeli sprawia, że
  pozycja „praca po pomiarze" trafia do agenta **po** tym, jak ten sam agent zamknął jej
  przedmiot. Nic tego nie pilnuje i nie jest to zapisane nigdzie poza tym akapitem.
- **`LineCore.cs` urósł dziś o ponad 200 wierszy** (MB-06…MB-08), przez co dwa pola
  „Skąd" wskazywały wiersz z komentarzem dokumentacyjnym. Adresy z numerem wiersza
  starzeją się przy każdym commicie w tym pliku, a `test_field_paths` sprawdza
  **istnienie pliku**, nie numer wiersza.
