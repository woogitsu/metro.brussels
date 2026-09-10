# Odmowa narzędzia nie znika pod `python3 -O` (10.09.2026)

**Zmierzone 10.09.2026 na:** `9784e3b`, kontener tej sesji.
**Przyrząd:** `python3 tools/tests/test_all.py` i `python3 -O tools/tests/test_all.py`,
skan drzewa składni po `tools/` (bez `tools/tests/`), nowy
`tools/tests/test_tool_refusals.py`.

---

## 1. Stan przed, zmierzony na dzisiejszym drzewie

```
python3 tools/tests/test_all.py     -> kod 0,  2178/2178, 116 modułów
python3 -O tools/tests/test_all.py  -> kod 1,  2176/2178, 116 modułów

  FAIL test_platform_exactly_as_wide_as_the_chamber_is_refused:
       peron zerowej szerokości przeszedł po prawej stronie
  FAIL test_platform_exactly_as_wide_as_the_chamber_is_refused_on_the_left_side_too:
       peron zerowej szerokości przeszedł po lewej stronie
```

Ta sama liczba testów i modułów, inny kod wyjścia. Padały dokładnie dwa, oba
pilnujące ODMOWY narzędzia — bo `-O` zdejmuje `assert` w **każdym** module, nie tylko
w testowym. Pod `-O` peron zerowej szerokości przechodził i geometria powstawała.

## 2. Ile ich było: TRZY, nie cztery

Skan drzewa składni po `tools/` z pominięciem `tools/tests/`:

```
tools/blender/station_sections.py:97,100  slab_sections  outer > inner / outer < inner
tools/physics/braking.py:65               params.design  rec['status'] == 'design_model'
```

**Pierwszy skan meldował cztery i to była usterka przyrządu, nie drzewa.** Chodził
`ast.walk`iem po każdej funkcji osobno, więc `assert` z `braking.py` wpadał do wyniku
dwa razy: raz jako należący do `params`, raz do zagnieżdżonego `design`. Liczba miejsc
jest treścią pola „Wyjście" tej pozycji, więc podwójne liczenie nie było kosmetyką.
Skan schodzi teraz rekurencyjnie z pamięcią funkcji, a osobna kontrola przyrządu
podaje mu `assert` w funkcji zagnieżdżonej i żąda **jednego** trafienia.

**Wszystkie trzy były strażnikami, żaden niezmiennikiem wewnętrznym.** Pierwsza próba
rozróżnienia ich automatycznie — „warunek odwołuje się do parametru funkcji" —
zaklasyfikowała **zero z trzech** jako strażników, bo `outer` i `inner` są liczone
wewnątrz funkcji z argumentów, a nie są argumentami. Przy trzech miejscach heurystyka
nie była potrzebna: przeczytałem je.

## 3. Drugi strażnik jest cichszy i groźniejszy

Wpis pozycji nazywał wyłącznie odmowę geometryczną. Druga, w `braking.params.design`,
jest kontrolą **POCHODZENIA** liczby: pod `-O` parametr o dowolnym innym statusie
wchodził do modelu hamowania bez śladu. To ta sama dyscyplina, którą `CLAUDE.md` §4.1
stawia jako regułę pierwszą, tyle że pilnowana konstrukcją, którą flaga interpretera
zdejmuje.

**Poprawka do pola „Wejście":** wpis wskazywał `tools/blender/station_kit.py`.
Funkcja tam JEST, ale jako re-eksport (`station_kit.py:53`
`slab_sections = SS.slab_sections`); ciało stoi w `tools/blender/station_sections.py`.

## 4. Kształt odmowy wybrany pomiarem

Pole „Wyjście" żądało rozstrzygnięcia z pomiarem, ilu wołających łapie dziś
`AssertionError`. Zmierzone:

```
raise ValueError w tools/ poza testami:                 68
AssertionError łapany poza tools/tests/:                 0
AssertionError łapany w tools/tests/:                    5
   test_station_kit.py:225,244   — łapią odmowę NARZĘDZIA (poprawione)
   test_assertion_gate.py:331,629 i test_streaming_fixture.py:107
                                 — łapią WŁASNE asercje testu (nietknięte)
```

`ValueError` jest więc formą tego repozytorium, a nie moim gustem. Precedens dla
odmowy pochodzeniowej stoi obok: `m7_layout.py:81` odmawia `ValueError`em wymiarowi
bez statusu `spec` od początku.

## 5. Stan po

```
python3 tools/tests/test_all.py     -> kod 0,  2182/2182, 117 modułów
python3 -O tools/tests/test_all.py  -> kod 0,  2182/2182, 117 modułów
```

Ten sam kod wyjścia i ta sama liczba testów — pole „Skończone, gdy" spełnione.
Strażników w narzędziach: **0**, i pilnuje tego bramka z pustą, zamkniętą listą
wyjątków.

## 6. Pięć kontroli negatywnych, `md5sum -c: OK` po każdej

Cache bajtkodu czyszczony przed każdym przebiegiem (6.D86).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | `assert` wraca do `station_sections` | **czerwona** 1/4 + pod `-O` 22/23 |
| KN-2 | `assert` wraca do `braking.py` (funkcja ZAGNIEŻDŻONA) | **czerwona** 1/4 |
| KN-3 | skan nie schodzi do funkcji (oślepiony) | **czerwona** 3/4 |
| KN-4 | wpis w `WOLNO_ASSERT` bez pokrycia w drzewie | **czerwona** 3/4 |
| KN-5 | odmowa pochodzenia przepuszcza status `spec` | **czerwona** 3/4 |

```
KN-1  FAIL test_zadne_narzedzie_nie_broni_warunku_golym_assertem:
      [('tools/blender/station_sections.py', 104, 'slab_sections', 'outer > inner')]
      a pod -O, na module perona:
      FAIL test_platform_exactly_as_wide_as_the_chamber_is_refused:
           peron zerowej szerokości przeszedł po prawej stronie
KN-2  FAIL test_zadne_narzedzie_nie_broni_warunku_golym_assertem:
      [('tools/physics/braking.py', 70, 'design', "rec['status'] == 'design_model'")]
KN-3  FAIL test_skan_widzi_asserty_ktore_ma_widziec: []
KN-4  FAIL test_lista_wyjatkow_nie_gnije: (…, 97) nie ma już `assert`a
KN-5  FAIL test_odmowa_geometryczna_i_pochodzeniowa_dzialaja_takze_pod_O:
      parametr o statusie 'spec' wszedł do modelu hamowania
```

**KN-1 ma dwie połowy i dopiero razem coś znaczą:** bramka statyczna zgłasza powrót
`assert`a, a przebieg `-O` pokazuje SKUTEK — peron zerowej szerokości znów przechodzi.
Bez drugiej połowy bramka mówiłaby o kształcie kodu, a nie o zachowaniu narzędzia.

**KN-2 istnieje osobno od KN-1 właśnie dlatego, że pierwszy skan liczył go podwójnie:**
mutacja w funkcji zagnieżdżonej jest tym przypadkiem, na którym przyrząd się mylił.

**KN-5 dwa razy wyszła czerwona z niewłaściwego powodu**, zanim zaczęła mierzyć to,
co obiecuje. Rejestr syntetyczny wypisywałem z ręki i był niepełny — raz wywrócił się
na `emergency_brake_mps2`, raz na `empty_mass_kg` (czytanym w `params` **z pominięciem**
`design()`), za każdym razem `KeyError`em zamiast odmową. Rejestr oddaje teraz każdy
klucz, o który go poproszą, więc nie ma jak rozjechać się z tą funkcją.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py test_tool_refusals.py
  -> 4/4 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 103,506 s, 2182 testów, 117 modułów, kod 0

python3 -O tools/tests/test_all.py
  -> RAZEM 105,814 s, 2182 testów, 117 modułów, kod 0
```

Zestaw **2178 → 2182**, moduły **116 → 117**. Zapadka `MIN_REPORTS` została w tym
commicie podniesiona ze dwustu dwunastu na dwieście trzynaście — słownie, bo
`test_report_claims.py` czyta pierwszą liczbę po nazwie stałej jako twierdzenie o jej
bieżącej wartości.

## 7a. Pomiar, który wyszedł czerwony z powodu mojego własnego wyścigu

Przedostatni przebieg `-O` dał **kod 1, 2181/2182** i przez chwilę wyglądał jak regres
tej pozycji. Nie był nim:

```
FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem:
     raportów w `reports/` jest 213, a `MIN_REPORTS` stoi na 212
```

Przebieg wystartował po dopisaniu tego raportu, a przed podniesieniem zapadki — czyli
zmierzył drzewo w stanie przejściowym, którego nigdy nie zamierzałem commitować.
Wypisane, bo pokazuje, że przebieg w tle na zmienianym drzewie mierzy to, co zastanie,
a nie to, o co się go prosiło; liczby w sekcji 5 są z przebiegów po zamknięciu edycji.

## 8. Czego świadomie nie zrobiłem

Nie wołam zestawu z `-O` w CI ani nie zmieniam warunku geometrycznego — pole „Poza
zakresem" wyklucza jedno i drugie. Nie tknąłem `assert`ów w `tools/tests/`: tam są
mechanizmem werdyktu, a nie strażnikiem wejścia, i pole „Poza zakresem" wyłącza
`assert` w rolach innych niż strażnik. Nie ruszyłem trzech miejsc w `tools/tests/`,
które łapią `AssertionError` z własnych asercji testu.

## 9. Zauważone i nietknięte

**`aw0_kg` omija kontrolę pochodzenia.** `params` czyta `empty_mass_kg` jako
`float(par["empty_mass_kg"]["value"])`, z pominięciem `design()`, więc jego status nie
jest sprawdzany wcale — ani przed tą pozycją, ani po niej. To nie jest usterka, którą
`-O` tworzy, więc nie należy do 6.D94; jest to jednak jedyny parametr modelu hamowania
bez kontroli statusu i nadaje się na osobną pozycję.

`-O` zdejmuje też `__debug__`-owe gałęzie i docstringi (`-OO`). Zestaw nie chodzi dziś
pod żadną z tych flag w CI i ta pozycja tego nie zmienia; zmierzone jest wyłącznie to,
co robi `-O`.
