# 6.D232 — podłoga sumy broni przed wzorcem MARTWYM, nie przed OKALECZONYM

**Data:** 17.09.2026 · **Gałąź:** `claude/6d232-rozklad-deklaracji` · **Baza:** `1f4ad3d`

## 1. Pomiar dzisiejszy, nie przepisany z opisu

```
DEKLARACJI razem = 390
rozklad -> {'const': 305, 'static readonly': 85, 'bez modyfikatora': 44}
MINIMUM_DEKLARACJI = 200   (przed tą pozycją)
```

Pilnowana liczba to `sum(len(v) for v in deklaracje().values())`, a **nie** `len(deklaracje())`:
pierwsza daje **390** deklaracji, druga **341** nazw. Rozróżnienie jest tu treścią i sam się
na nim raz pomyliłem, czytając słownik zamiast sumy jego wartości.

Wiersz pozycji mówił „185 poniżej stanu drzewa" przy 385 deklaracjach. Dziś różnica wynosi
**190** przy 390 — liczba z opisu jest sprzed dwóch dni i została **zastąpiona zmierzoną**,
nie przepisana. Wiersz myli też „148 plików skanowanych" z „plikami, w których stoi
deklaracja" — tych jest **81**.

## 2. Dlaczego podniesienie samej sumy jest niewystarczające — ZMIERZONE

Rozstrzyga para kontroli, nie rozumowanie. Baza: **32/32**.

**KN-A — wzorzec OKALECZONY** (z `DEKLARACJA` zdjęty jest `?` po grupie modyfikatora,
czyli modyfikator dostępu staje się WYMAGANY):

```
FAIL test_kazda_galaz_wzorca_ma_wlasna_podloge: deklaracji bez modyfikatora dostepu
  jest 0 przy progu 36 (rozklad: {'const': 261, 'static readonly': 85,
  'bez modyfikatora': 0}) — wymuszenie modyfikatora w `DEKLARACJA` zabiera je
  wszystkie, a SUMA zostaje na 346 przy progu 330 i PRZECHODZI
  14/15 przeszło
```

**Dokładnie jedna czerwień, i jest nią podłoga gałęziowa. Suma przeszła** — 346 ≥ 330.
Bez trzeciej podłogi ta awaria jest niewidzialna.

**KN-B — gałąź `static readonly` WYCIĘTA z wzorca:**

```
FAIL test_kazda_galaz_wzorca_ma_wlasna_podloge: galaz `static readonly` daje 0 przy progu 72
FAIL test_the_gate_sees_the_declarations_it_is_supposed_to_see: bramka widzi 305 przy progu 330
FAIL test_the_pattern_reads_the_shapes_this_repository_actually_uses: …
  12/15 przeszło
```

**Trzy czerwienie, w tym suma.** Tu suma **wystarcza**.

**Różnica między KN-A i KN-B jest całą treścią rozbicia jednej podłogi na cztery**, i nie
jest to argument z gustu: wycięcie gałęzi zabiera 85 z 390 i suma to słyszy, a okaleczenie
wzorca zabiera 44 i suma tego nie słyszy. Podłoga na sumie broni więc przed wzorcem
**martwym**; przed **okaleczonym** broni dopiero rozkład.

## 3. Kontrola DODATNIA

**KN-C — legalna nowa `const` w `src/Sim/Physics/DavisResistance.cs`**, dopisana razem
z odczytem, żeby nie była martwa:

```
  32/32 przeszło
rozklad pod mutacja: {'const': 306, 'static readonly': 85, 'bez modyfikatora': 44}
```

Zielone. Podłogi są KW, więc rosnąca populacja ich nie rusza — bramka nie zapala się na
pracy poprawnej (6.D27).

**Pierwsze podejście do KN-C NIE ZASTOSOWAŁO SIĘ** (kotwica wyrażenia regularnego nie
pasowała do żadnego ciała typu) i zestaw dał wtedy **32/32** — czyli wynik
**nieodróżnialny od zielonej kontroli dodatniej**. Złapała to asercja „mutacja NIE
zastosowana", nie moje oko. Dwa przebiegi 32/32 o przeciwnym znaczeniu w odstępie minuty
są najkrótszym opisem tego, po co ta asercja stoi przy każdej mutacji.

## 4. Rozmiar zapasu — z historii, nie z wyczucia

Zapas wynika z pomiaru na **572 rewizjach** z `.cs` (636 commitów first-parent), tym samym
wzorcem nad blobami `src/` i `tests/`:

```
SPADKOW: 2
  spadek ('2026-09-05', '8f27a033', 199, 198, 1)
  spadek ('2026-09-07', 'd47c582f', 234, 233, 1)
max spadek: 1
```

**W całej historii repozytorium populacja spadła dwa razy, za każdym razem o jeden.**
Zapas 60 jest sześćdziesiąt razy głębszy niż najgłębszy spadek, jaki to drzewo zrobiło.
Per gałąź: `const` spadła raz o jeden, `static readonly` raz o jeden, przekrój „bez
modyfikatora" **ani razu**.

| stała | dziś | populacja | zapas |
|---|---|---|---|
| `MINIMUM_DEKLARACJI` | **330** | 390 | 60 (15,4 %) |
| `MINIMUM_CONST` | **258** | 305 | 47 (15,4 %) |
| `MINIMUM_STATIC_READONLY` | **72** | 85 | 13 (15,3 %) |
| `MINIMUM_BEZ_MODYFIKATORA` | **36** | 44 | 8 (18,2 %) |

**Równości (`== 390`) nie ma i to jest wybór wprost:** populacja rośnie z każdym nowym
polem w `src/`, więc równość zapalałaby się na pracy poprawnej — co KN-C pokazuje
wykonaniem, a nie zapowiedzią.

## 5. Klasyfikator zapadek odrzucił dwie postacie tego testu — i to jest znalezisko

Próg zapisany jako `populacja >= PRÓG` klasyfikuje się jako **WOLNA**. Ten sam próg
zapisany jako pętla po krotce `(nazwa, prog)` wychodzi **POZA SKANEM** (nazwa nie pada
w żadnym `ast.Compare`, tak jak przy `MIN_PATHS`), a zapisany jako `if widziane[...] < PRÓG`
wychodzi **CZĘŚCIOWA** — bo od strony stałej jest to `Gt`, czyli **straż**, a straży tam
nie ma żadnej.

**Kierunek zapisu porównania jest tu treścią, nie stylem**, i kosztował dwa przebiegi.
Zapadka opisana w rejestrze jako strzeżona, a nieprzybita niczym, jest napisem.

**Czego to NIE mówi:** czy któraś z 60 zapadek już stojących w rejestrze jest tą drogą
zaklasyfikowana fałszywie. Nie sprawdzone, osobna pozycja.

## 6. Liczby w komunikatach są LICZONE, nie wpisane — poprawka z tego przebiegu

Pierwsza wersja komunikatu mówiła „zabiera ich **43 z 389**". Literał zestarzał się
w ciągu doby: dziś jest ich 44 z 390. **Nie pilnuje tego żadna bramka** —
`test_report_claims` czyta `reports/`, a nie komunikaty asercji w `tools/tests/`.

Twierdzenie w komunikacie bramki jest twierdzeniem tak samo jak w raporcie, tylko nikt go
nie sprawdza. Komunikat liczy więc dziś sumę pozostałą po okaleczeniu wzorca i podaje ją
razem z progiem — widać to w wyjściu KN-A wyżej („zostaje na 346 przy progu 330").

## 7. Zapadki

- `MINIMUM_DEKLARACJI` na **330**; nowe `MINIMUM_CONST` **258**, `MINIMUM_STATIC_READONLY`
  **72**, `MINIMUM_BEZ_MODYFIKATORA` **36** — wszystkie trzy klasy **WOLNEJ**.
- `ZAPADEK_RAZEM` na **63**, klasy na **17/3/42/1**. **Liczba jest PRZELICZONA z drzewa po
  scaleniu, nie wzięta z żadnej strony konfliktu:** gałąź mierzyła bazę 59 i dawała 62,
  `main` miał w tym czasie 60, a scalone drzewo niesie wszystkie zapadki obu stron.
  Konflikt miał **pięć** miejsc i w każdym oba łańcuchy historii zostały zachowane.
- `MIN_REPORTS` o jeden.

## 8. Czego NIE zrobiono

- **Nie poszerzono wzorca** o nowe kształty deklaracji i nie zmieniono listy skanowanych
  plików — pole „Poza zakresem".
- **Nie ruszono `MINIMUM_DZIUR`** ani innych zapadek tego modułu — rozkład ich nie dotyczy.
- **Nie sprawdzono, czy któraś z istniejących zapadek jest fałszywie zaklasyfikowana**
  przez pisownię porównania (§5) — osobna pozycja.

## 9. Co zauważone przy okazji, nietknięte

- **Pole „Poza zakresem" tej pozycji wymienia `MINIMUM_NAZW` i `MINIMUM_PLIKOW`, a takich
  stałych w drzewie NIE MA.** Sprawdzone: `hasattr` daje `False` dla obu. Zdanie zabezpiecza
  przed ruszeniem czegoś, co nie istnieje — wygląda na przepisane z innej pozycji.
- **`_tresc_poza_csharp(root)` ignoruje własny argument** i przy drzewie wstrzykniętym czyta
  `.tscn`/`.sh`/`.yml` z prawdziwego repozytorium. Znalezisko zapisane już przy 6.D225,
  wciąż obecne.
- **W `/tmp` wisi ponad trzydzieści worktree'ów**, część na commitach sprzed kilku dni.
