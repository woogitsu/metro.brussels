# 6.D226 — źródło chronione słabiej niż jego kopia: zbiór zapisów literału po obu stronach

**16.09.2026**, na `bac8789`. Wejście: `tools/tests/test_csharp_test_methods.py`
(`POSTACIE_LITERALU`), `tests/Game.Tests/UiTextTests.cs` (`PostacieLiteralu`).

## 1. Rozstrzygnięcie: bramka jest możliwa, i porównywany jest SAM LITERAŁ

Pozycja pytała, czy da się porównać obie listy bez rozbioru składni obu języków.
**Da się**, ale tylko na jednym z trzech stopni. Zmierzone:

| stopień | co porównuje | wynik |
|---|---|---|
| A | tekst zapisu **bez odkodowania** | rozjazd **4/4** — na samym escapowaniu |
| B | treść po odkodowaniu, **cały `Zapis`** | rozjazd **4/4** — na rusztowaniu |
| C | **sam literał** (od `= ` do domykającego `;`) | **zbiory równe co do znaku** |

Stopień A rozjeżdża się, bo ten sam cudzysłów pisze się inaczej w obu językach.
Stopień B rozjeżdża się na rusztowaniu: `x = ` wobec `var x = `, `{}` wobec
`var y = 1;`. Zbiory na stopniu C:

```
C#    : ['@"""a"', '@"a"""', '"""a"""', '$@"""a"']
Python: ['@"""a"', '@"a"""', '"""a"""', '$@"""a"']
ZBIORY ROWNE: True | licznosc: 4 4
```

**Porównanie całych zapisów byłoby bramką świecącą na kodzie poprawnym** — czyli
bramką do wyłączenia, nie do utrzymania (6.D27). Nie jest to teza: pokazuje to KN-3.

## 2. Asymetria, dla której ta bramka istnieje

To jest właściwy wynik tej pozycji, zmierzony na dzisiejszym drzewie:

```
skreślenie jednej z czterech po stronie PYTHONA (POSTACIE_LITERALU — ŹRÓDŁO):
  python3 tools/tests/test_all.py  ->  2497/2497 przeszło,  ZERO czerwieni

skreślenie jednej z czterech po stronie C# (PostacieLiteralu — KOPIA):
  dotnet test tests/Game.Tests  ->  Failed: 1, Passed: 317
  (asercja zbioru przedrostków, od 6.D215)
```

**Lista będąca ŹRÓDŁEM była chroniona słabiej niż jej kopia.** Kierunek jest zapisany
w komentarzu po obu stronach od 6.D215 — `POSTACIE_LITERALU` jest źródłem, `PostacieLiteralu`
kopią — a pilnowana była wyłącznie kopia.

## 3. Dekoder przybity do KOMPILATORA, nie do wyobrażenia

Dekoder ucieczek C# mógłby być drugim czytnikiem tabeli zamiast jej odczytem. Żeby
nim nie był, zmusiłem `dotnet test` asercją do wypisania czterech wartości
`PostacieLiteralu[i].Zapis`:

```
POMIAR>>>var x = @"""a"; var y = 1;<<SEP>>var x = @"a"""; var y = 1;<<SEP>>var x = """a"""; var y = 1;<<SEP>>var x = $@"""a"; var y = 1;<<<POMIAR
```

Znak w znak to, co zwraca dekoder na tym samym pliku. Przywrócenie po tym pomiarze:
`tests/Game.Tests/UiTextTests.cs: OK`.

## 4. Czytnik pożyczony, i to ma skutek, który warto nazwać

Literały bierze `czytnik._przebieg` — ten sam, którym chodzi `maska` (6.D213).
Ma to skutek **za darmo**: wiersz tabeli zakomentowany, blokowo albo przez `//`,
jest wtedy **komentarzem, a nie wierszem**, bez ani jednej własnej reguły.

**`maska` jest tu złym narzędziem i to jest zmierzone**, a nie założone: zasłania
literały w całości, więc czytnik na masce widzi **zero** wierszy tabeli. To ta sama
obserwacja, którą 6.D225 zrobiło od drugiej strony — maska zasłania to, o co tu pytamy.

Odsiew kolumn niebędących literałem idzie przez `klasy_literalow`, a nie przez własne
pytanie o pierwszy znak: kolumna `PoMasce` ma kształt `var x =       ; var y = 1;`,
więc wycinek między `= ` a `;` jest tam pusty i bez tego odsiewu wszedłby do zbioru
jako piąty element.

## 5. Kontrole negatywne — pięć, każda z przewidywaniem PRZED przebiegiem

| | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | skreślona postać po stronie **Pythona** (źródło) | nowa bramka zapala | **13/14, zapala** |
| KN-2 | skreślona postać po stronie **C#** (kopia) | nowa bramka zapala | **12/14, zapala** |
| KN-3 | porównanie **całych zapisów** (stopień B) | zapala na kodzie **poprawnym** | **12/14, zapala** |
| KN-4 | czytnik naiwny (regeks zamiast `_przebieg`) | zapala kontrola przyrządu | **12/14, zapala** |
| KN-5 | **podmiana** postaci, liczność bez zmiany | zapala asercja **zbioru** | **13/14, zapala** |

`md5sum -c` po każdej: `OK` na obu plikach.

### KN-1 jest sednem pozycji

To ta sama mutacja, która przed tą zmianą dawała **2497/2497 zielone**:

```
FAIL test_zbior_zapisow_literalu_jest_TEN_SAM_po_obu_stronach: zapisow jest 3 po
stronie Pythona i 4 po stronie C# przy zapadce 4 — czytnik przestal widziec wiersze
tabeli albo tabela sie zwezila
```

### KN-3 jest dowodem, dlaczego stopień C, a nie B

Porównanie całych zapisów zapala bramkę na drzewie, w którym **nic nie jest zepsute**:

```
FAIL test_zbior_zapisow_literalu_jest_TEN_SAM_po_obu_stronach: ZBIORY zapisow
literalu rozjechaly sie miedzy tools/tests/test_csharp_test_methods.py
a tests/Game.Tests/UiTextTests.cs
```

Gdybym wybrał stopień B, bramka weszłaby czerwona i musiałaby zostać wyłączona.

### KN-5 pokazuje, że zbiór jest czymś więcej niż licznością

Podmiana `$@` na `@$` po jednej stronie zostawia **cztery** zapisy po obu stronach,
więc asercja liczności przechodzi — zapala się dopiero porównanie **zbiorów**.
Bez niego bramka pytałaby o to samo, co pętla z 6.D215, czyli o nic nowego.

## 6. Granica nazwana, a nie przemilczana

**Literał niosący średnik w treści zostałby ucięty po obu stronach tak samo**, więc
rozjazd za średnikiem byłby dla tej bramki niewidoczny. Sita na to **świadomie nie ma**:
jedyne tanie — parzystość cudzysłowów — zapala się na literale **poprawnym** z uciekanym
cudzysłowem, czyli byłaby to bramka z 6.D27. Dziś żadna z czterech postaci średnika
nie niesie.

Druga granica, drobniejsza: dekoder ucieczek obsługuje sześć sekwencji i na nieznanej
**pada głośno** (`KeyError`), zamiast przepuścić napis bez zmiany. Dekoder milczący
o nieznanej ucieczce mówiłby o sobie, a nie o pliku.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py test_csharp_test_methods.py
  14/14 przeszło

python3 tools/tests/test_all.py
  2499/2499 przeszło,  126 modułów

dotnet test tests/Sim.Tests    Passed! - Failed: 0, Passed: 662, Total: 662
dotnet test tests/Game.Tests   Passed! - Failed: 0, Passed: 318, Total: 318
```

## 8. Czego świadomie nie zrobiłem

- **Nie ujednoliciłem oczekiwań** — mają być różne, bo czytniki są różne
  (`maska` zwraca kod, `Literaly` treść). Pole „Poza zakresem" tego zabrania.
- **Nie dołożyłem piątej postaci literału** ani nie tknąłem żadnego z dwóch czytników.
- **Nie postawiłem sita na średnik w treści** — powód w §6.

## 9. Co zauważyłem przy okazji, ale nie tknąłem

- **Asercja liczności zapala się przed asercją zbioru**, więc przy skreśleniu
  komunikat mówi o liczności, a nie o tym, która postać zniknęła. Przy podmianie
  (KN-5) mówi już o zbiorze. Rozważałem odwrócenie kolejności i zostawiłem tak,
  bo liczność jest tańsza do zrozumienia przy najczęstszej pomyłce — ale to wybór,
  nie konieczność.
- **`_odkoduj_zwykly_literal_csharp` obsługuje sześć ucieczek**, bo tyle wystarcza
  tej tabeli. Dekoder ogólny wymagałby `\u`, `\x` i `\U`, a te w tabeli nie padają
  ani razu — dopisanie ich byłoby kodem bez wołającego.
