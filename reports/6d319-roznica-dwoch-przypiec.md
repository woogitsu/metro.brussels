# 6.D319 · Dwa wyrażenia, ZERO pytań do drzewa — a jedna z czterech mutacji zapala bramkę z PUSTĄ różnicą w komunikacie

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `426149d`

6.D309 §9.3 zapisało, że dwie bramki mają przypięcie modułowe po **obu** stronach
odejmowania, i że do pytania tamtej pozycji nie należały, bo ta pytała o różnicę
**drzewa** od przypięcia. Ta pozycja pyta o te dwa wyrażenia i o nic więcej.

Trzy liczby, których żądało pole: **2 · 0 · 2**. Wyrażeń z przypięciem po obu
stronach jest **dwa**; żadne z nich nie pyta drzewa nawet pośrednio; i **oba** padają
przy zmianie tylko jednej strony — zmierzone czterema mutacjami, nie wywnioskowane.

Ale wynik, dla którego warto było tę pozycję wziąć, jest inny: **jedna z czterech
mutacji zapala bramkę, a różnica wypisana w jej komunikacie jest PUSTA** — bramka
mówi „coś jest nie tak" i w tym samym zdaniu pokazuje `[]`.

---

## 1. Kontrola przyrządu — ZDANA, i to co do NAZW, nie tylko co do liczby

Pole żąda, żeby oba wyrażenia z 6.D309 §3 wyszły w populacji; przyrząd widzący mniej
niż dwa czyta przypięcia inaczej niż tamta pozycja.

```
=== OBIE_PRZYPIETE (2) ===
   tools/tests/test_readme_claims.py:511
      lewa : ['PUNKTY_BRAKOW']
      prawa: ['POMIARY_BRAKOW']
      set(PUNKTY_BRAKOW) - set(POMIARY_BRAKOW)
   tools/tests/test_report_hygiene.py:1690
      lewa : ['ARCHIWUM']
      prawa: ['SZOSTKA_6D171']
      set(ARCHIWUM) - SZOSTKA_6D171
```

Zgadza się nie tylko licznik, ale i **cztery nazwy stałych**, które pole „Wejście"
wymienia z nazwy. Przyrząd czyta przypięcia tak samo jak 6.D309.

## 2. Populacja bazowa: 190, a nie 202 — i ROZDZIELIŁEM „drzewo się ruszyło" od „przyrząd czyta inaczej"

6.D309 podało populację 202 i rozkład `{ZADNA: 160, jedna_strona: 40, OBIE_PRZYPIETE: 2}`.
Mój przyrząd daje 190 i `{ZADNA: 144, jedna_strona: 44, OBIE_PRZYPIETE: 2}`.

Zamiast uzgadniać, **zmierzyłem, gdzie siedzi różnica**: puściłem swój przyrząd na
drzewie `757be46`, czyli na bazie samego 6.D309.

```
MOJ przyrzad na drzewie 757be46 (baza 6.D309): 190 {'ZADNA': 144, 'jedna_strona': 44, 'OBIE_PRZYPIETE': 2}
6.D309 podalo:                                 202 {'ZADNA': 160, 'jedna_strona': 40, 'OBIE_PRZYPIETE': 2}
```

**Co do jednej liczby te same wyniki co dziś.** Rozjazd jest więc w **stu procentach
własnością przyrządu i w zerowym drzewa** — a to jest zdanie zmierzone, nie założone.
Różnicy nie uzgadniam (lekcja 7, ten sam ruch co przy 6.D317 i 6.D318); mówię, czego
nie liczę: moja populacja bierze `ast.BinOp` z `ast.Sub` osiągalny z `ast.Assert.msg`
przy jednym skoku przez przypisanie w zasięgu funkcji, z odsiewem duplikatów po
`(plik, linia, kolumna)` — i to ostatnie jest najpewniejszym kandydatem na dwanaście
wyrażeń różnicy, bo 6.D309 nie mówi, czy odsiewało.

**To jest TRZECI z rzędu przyrząd tej rodziny, który nie odtwarza poprzedniego:**
6.D300 dało 132, 6.D309 dało 202 i odmówiło uzgodnienia, ja daję 190 i odmawiam tak
samo. Odpowiedź każdej z tych trzech pozycji była mimo to **odporna na spór o bazę** —
u mnie klasa `OBIE_PRZYPIETE` wynosi 2 przy każdej z trzech populacji.

**Przy okazji zmierzone, choć nikt nie pytał:** między `757be46` a dzisiejszym `main`
stoi **dziesięć scaleń**, a `tools/tests/*.py` zmieniły się w **3 plikach o 41 wierszy** —
i populacja nie ruszyła się **ani o jedno wyrażenie**. Kształt, o który pyta ta rodzina
pozycji, jest w skali dekady scaleń stabilny.

## 3. LICZBA DRUGA: ŻADNE z dwóch nie pyta drzewa, nawet pośrednio

Pole ostrzegało wprost, żeby nie przyjąć bez pomiaru, że różnica dwóch przypięć jest
martwa — bo któraś strona może być **budowana z drzewa pośrednio**. Sprawdziłem obie
strony obu wyrażeń, czytając kod, a nie wnioskując z kształtu:

| wyrażenie | lewa | prawa | pyta drzewa pośrednio? |
|---|---|---|---|
| `set(PUNKTY_BRAKOW) - set(POMIARY_BRAKOW)` | krotka literałów, poziom modułu | słownik literałów, poziom modułu | **nie pyta** |
| `set(ARCHIWUM) - SZOSTKA_6D171` | słownik literałów, poziom modułu | `frozenset` literałów, poziom modułu | **nie pyta** |

`set()` jest wbudowane, nie czytnikiem drzewa. Żadna ze stron nie zawiera wywołania
funkcji tego modułu ani importu z `tools/`, więc **0 z 2**.

**Ostrzeżenie pola było jednak trafne co do kierunku, w którym patrzyło**, i mówię to,
zamiast raportować samo zero: w tym samym module, kilka wierszy wyżej, stoi test
`test_kazdy_z_szostki_6D171_ma_odsylacz_albo_wpis_w_ARCHIWUM`, który te **same dwa
przypięcia** zestawia z drzewem przez `_korpus()`. Obie listy są więc trzymane przy
drzewie — tylko nie **tym** wyrażeniem. Kontrola spójności dwóch list pisanych ręcznie,
o której mówi pole, tutaj naprawdę istnieje i jest osobna od pytania do drzewa.

## 4. LICZBA TRZECIA: 2 z 2 padają przy zmianie JEDNEJ strony — zmierzone czterema mutacjami

Pole żąda mutacji, nie wniosku, „także gdy wynosi zero". Nie wynosi zera. Każdą stronę
każdego wyrażenia zmieniłem osobno, drzewo przywracałem po każdej mutacji:

| mutacja | zmieniona strona | skutek |
|---|---|---|
| M1a | `POMIARY_BRAKOW` (prawa) | **FAIL** `test_each_written_reason_says_why_the_table_cannot_hold_the_entry` · komunikat: `pomiaru nie mają: ['profilu pionowego']` |
| M1b | `PUNKTY_BRAKOW` (lewa) | **FAIL** ten sam test · komunikat: `pomiaru nie mają: []` |
| M2a | `ARCHIWUM` (lewa) | **FAIL** `test_ARCHIWUM_nie_rozrasta_sie_po_cichu_i_kazdy_wpis_ma_POWOD` · komunikat: `['NIE-ISTNIEJE-W-SZOSTCE']` |
| M2b | `SZOSTKA_6D171` (prawa) | **FAIL** ten sam test · komunikat: `['uzupelnienie-kolejki-10-09']` |

**Cztery mutacje, cztery zapalone bramki.** Teza „różnica dwóch przypięć jest martwa",
przed którą pole ostrzegało, jest **zmierzona jako nieprawdziwa** — oba wyrażenia
pilnują obu swoich stron.

## 5. ZNALEZISKO: M1b zapala bramkę z PUSTĄ różnicą w komunikacie

Trzy z czterech mutacji zapalają bramkę **i mówią, czego brakuje**. Czwarta zapala ją
i wypisuje `[]`.

Mechanizm jest jednokierunkowy i widać go dopiero po zestawieniu mutacji z tekstem:
asercja brzmi `set(POMIARY_BRAKOW) == set(PUNKTY_BRAKOW)`, czyli sprawdza **równość
w obie strony**, a komunikat wypisuje różnicę **tylko w jedną**: `PUNKTY − POMIARY`.
Gdy ubywa po stronie `POMIARY` (M1a), różnica jest niepusta i diagnoza jest pełna.
Gdy ubywa po stronie `PUNKTY` (M1b), różnica w **tym** kierunku jest pusta — bramka
zapala się poprawnie, a jej komunikat nie mówi ani słowa o tym, co się stało.

**To jest ta sama jednostronność, którą 6.D309 §4 zmierzyło dla pięciu wyrażeń
`przypięcie − drzewo`** — tyle że tam była własnością pytania, a tutaj jest własnością
**komunikatu przy asercji symetrycznej**. Bramka nie przepuszcza błędu; przepuszcza
**wiedzę o błędzie**. Nie poprawiam tego, bo pole zabrania zmieniać asercje, a
dopisanie drugiego kierunku jest zmianą treści komunikatu, nie literówką.

## 6. ZNALEZISKO SPOZA PYTANIA: wyrażenie 1 żyje tylko dlatego, że TRZECIE przypięcie jest PUSTE

Pole pyta o dwa przypięcia. Wyrażenie 1 stoi jednak pod warunkiem `if not POWODY_BEZ_WPISU:`,
czyli pod **trzecim**, o które pole nie pyta. Sprawdziłem mutacją, co robi jego zmiana:

```
M3: POWODY_BEZ_WPISU przestaje byc puste
  ok   test_each_written_reason_says_why_the_table_cannot_hold_the_entry
```

**Test przechodzi na ZIELONO, a gałąź z wyrażeniem 1 nie jest wykonywana ani razu.**
Jedno dopisanie w innym miejscu pliku wycisza to wyrażenie **bez zapalenia czegokolwiek** —
i jest to zachowanie zamierzone (komentarz przy tej gałęzi powołuje się na 6.D121:
asercja istnieje właśnie po to, żeby pusta tabela nie znaczyła „nic nie sprawdzono").
Zamierzone nie znaczy niewidoczne: przy niepustej tabeli różnica dwóch przypięć
**przestaje istnieć jako pomiar**, a żadna liczba w tej pozycji tego nie pokazuje.

Zapisuję to osobno, bo odpowiada na pytanie pola „czy ta różnica jest martwa"
z kierunku, którego pole nie nazwało: **dziś nie jest martwa, ale jej życie zależy
od wartości stałej, o którą nikt nie pyta.**

## 7. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| Q1 | populacja bazowa odtworzy 202 co do jedynki | **OBALONE** — 190 |
| Q2 | `OBIE_PRZYPIETE` wyjdzie dokładnie 2 | trafione |
| Q3 | co najmniej jedno wyrażenie pyta drzewa pośrednio | **OBALONE** — zero z dwóch |
| Q4 | mutacja jednej strony zapali bramkę w obu wyrażeniach | trafione — i w obu kierunkach, 4 z 4 |
| Q5 | `ZADNA` 160 i `jedna_strona` 40 co do jedynki | **OBALONE** — 144 i 44 |
| Q6 | moja lista kształtów „czytnika drzewa" okaże się niewyczerpująca | **NIESPRAWDZONE** |

**Q6 zapisuję jako niesprawdzone, a nie jako pudło ani trafienie**, i jest to ten sam
ruch, którym 6.D309 §7 potraktowało swoje X7. Lista nie została wykonana **ani razu**:
skoro żadna strona żadnego wyrażenia nie zawiera wywołania, sito czytników drzewa nie
miało czego odsiewać. Zaliczenie Q6 w którąkolwiek stronę byłoby zmyśleniem — po ośmiu
trafieniach z rzędu przy 6.D310–6.D318 byłoby zmyśleniem szczególnie łatwym.

**Q3 obalone jest właściwym wynikiem §3, a nie porażką przewidywania.** Postawiłem je,
bo pole ostrzegało przed dokładnie tym; pomiar mówi, że tu ostrzeżenie nie trafiło —
a trafiło o kilkanaście wierszy dalej, w teście, który **te same przypięcia** zestawia
z drzewem osobną asercją.

## 8. Czego świadomie nie zrobiono

- **Nie usunięto ani nie przepisano żadnego przypięcia.**
- **Nie zmieniono żadnej asercji** — w szczególności nie dopisano drugiego kierunku
  różnicy w komunikacie z §5, mimo że pomiar pokazuje, iż jeden kierunek milczy.
- **Nie postawiono bramki na kształcie wyrażenia** ani na liczbie przypięć po obu stronach.
- **Nie uzgodniono populacji 190 z 202** — §2 pokazuje, gdzie ta różnica siedzi,
  i to jest mocniejsze niż jej wyrównanie.
- **Nie rozstrzygnięto, czy warunek z §6 jest usterką** — jest udokumentowany
  w kodzie jako decyzja i rozstrzygnięcie należy do autora.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 9. Zauważone przy okazji, nietknięte

1. **Trzy przyrządy tej rodziny dały trzy populacje bazowe: 132, 202 i 190** — a każda
   z trzech pozycji dostała tę samą odpowiedź na swoje pytanie. Zaczyna to być
   własność rodziny, nie pojedynczego pomiaru: **populacja bazowa w tej rodzinie jest
   nieporównywalna między pozycjami i nieistotna dla ich odpowiedzi.** Ile jeszcze
   pozycji musi to powtórzyć, zanim przestanie to być niespodzianką, nie pyta nikt.
2. **Dziesięć scaleń i 41 zmienionych wierszy w korpusie nie ruszyło populacji o ani
   jedno wyrażenie** (§2). Odejmowania w komunikatach asercji są w tym drzewie
   kształtem stabilnym — i to jest liczba, której żadna z trzech pozycji nie miała.
3. **Obie listy z §3 są trzymane przy drzewie osobnym testem, kilka wierszy dalej.**
   Wyrażenie, o które pyta ta pozycja, jest więc **drugą** kontrolą tych samych
   danych, a nie jedyną — czego z samego kształtu `PIN − PIN` zobaczyć się nie da.
