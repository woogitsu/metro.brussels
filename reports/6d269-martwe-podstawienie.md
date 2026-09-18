# 6.D269 — martwe podstawienie stałej: teza się potwierdziła

**Data:** 18.09.2026 · **Gałąź:** `claude/6d269-martwe-podstawienie` · **Baza:** `2554ce5`

## 1. Odpowiedź na pole „Wyjście"

| pytanie | odpowiedź |
|---|---|
| wiązań domyślnych pod `tools/` | **132** w **36** plikach |
| różnych par `(moduł, nazwa)` | **81** |
| podstawień `moduł.STAŁA` w `tools/tests/` | **23** w **6** plikach, przy **8** stałych |
| z nich MARTWYCH | **0** |

**Teza pola „Skąd" potwierdziła się co do jedności** — pierwszy raz po trzech
pozycjach, których tezy pomiaru nie przeżyły (6.D262, 6.D263, 6.D267). Liczby
132 i 36, wpisane do pola przy 6.D265, zgadzają się z drzewem `2554ce5`.

**Dwie liczby po stronie wiązania są podane, bo są RÓŻNE, i pomylenie ich złapała
podłoga tej bramki przy pierwszym przebiegu.** Proza mówiła o 132 wystąpieniach,
a czytnik dawał 81 — bo `wiazane_domyslnie` zwraca nazwy (do przecięcia liczy się
to, CZY stała jest wiązana), a pole „Wyjście" pytało o funkcje. Podłoga stała na
100 i zapaliła się na 81; gdyby stała na 50, obie liczby przeszłyby jako jedna.

## 2. Zero jest ZBIEGIEM, nie zabezpieczeniem

Żadna z ośmiu podstawianych stałych nie jest przechwytywana przy imporcie:

| plik testowy | podstawienie | moduł po rozwiązaniu aliasu |
|---|---|---|
| `test_godot_warning_gate.py` | `G.ALLOWED` ×2 | `assert_no_godot_warnings` |
| `test_inspire_rail.py` | `IR.CRS` ×2, `IR.SOURCE_REGISTRY` ×2 | `inspire_rail` |
| `test_mutation_sweep.py` | `sweep.ROOT` ×8, `sweep.OWN_TESTS_STUB` ×2 | `mutation_sweep` |
| `test_shot_metadata_gate.py` | `G.AXIS_TOLERANCE_M` ×2 | `assert_shot_metadata` |
| `test_surface_sections.py` | `SS.PORTAL_HALO_M` ×3 | `surface_sections` |
| `test_validate_axis.py` | `V.NET` ×2 | `validate` |

Pierwsze podstawienie stałej, która któryś z kształtów niżej ma, dałoby kontrolę
cichą i zieloną — i to jest cała treść tej bramki.

## 3. Przechwycić wartość można DWOMA kształtami, nie jednym

Drugiego kształtu pozycja nie nazywała; doszedł z pomiaru:

1. **domyślny argument** — `def f(root=ROOT)`: wyrażenie domyślne liczy się raz,
   przy definiowaniu funkcji;
2. **stała pochodna na poziomie modułu** — `SCIEZKA = os.path.join(ROOT, "x")`:
   liczy się przy imporcie, więc podstawienie `ROOT` nie rusza `SCIEZKA`.

Ten drugi jest zmierzony i dziś pusty: żadna z ośmiu podstawianych stałych nie ma
pochodnej na poziomie modułu. Czytnik bierze wyłącznie `drzewo.body`, a nie
`ast.walk` — to samo wyrażenie w ciele funkcji liczy się przy każdym wywołaniu
i podstawienie widzi.

## 4. Alias musi być ROZWIĄZANY, i to jest zmierzone, nie założone

`G` prowadzi w tym drzewie do **dwóch różnych modułów**: w
`test_godot_warning_gate.py` do `assert_no_godot_warnings`, a w
`test_shot_metadata_gate.py` do `assert_shot_metadata`. Czytnik biorący alias
dosłownie wrzuciłby oba do jednego worka `G` i porównywał stałe jednego modułu
z listą drugiego — czyli zgłaszałby kolizję tam, gdzie jej nie ma, albo przeoczył
tę, która jest. Pilnuje tego osobna asercja, która **żąda, żeby materiał istniał**:
jeżeli żaden alias nie prowadzi już do dwóch modułów, kontrola straciła podstawę
i trzeba ją oprzeć na drzewie próbnym.

## 5. Kontrola negatywna — przewidywanie spisane PRZED przebiegiem

Na kopii drzewa, z czyszczonym `__pycache__`, z asercją że mutacja wylądowała.

| mutacja | przewidziane | zmierzone |
|---|---|---|
| `def _kn_6d269(root=ROOT)` dopisane do `mutation_sweep.py` | czerwień z ośmioma martwymi podstawieniami `sweep.ROOT` | `FAIL … martwych podstawien jest 8, a pomiar 18.09.2026 dal 0: [('test_mutation_sweep.py', 109, 'ROOT', 'mutation_sweep', 'domyslny argument'), …]`, 8/9 |

Baza na kopii: `9/9 przeszło`. Przewidywanie trafiło co do liczby i co do kształtu.

## 6. Kontrola przyrządu

Bramka jest równością na ZERO, więc bez kontroli przechodziłaby także przy
czytniku, który nie widzi niczego. Na drzewie próbnym, trzy przypadki naraz:

```
ROOT             wiazany `def f(root=ROOT)`        -> zgłoszony, "domyslny argument"
POCHODNA_ZRODLO  SCIEZKA = POCHODNA_ZRODLO + '/x'  -> zgłoszony, "stala pochodna"
ZDROWY           czytany tylko w ciele funkcji     -> NIE zgłoszony
```

Trzeci przypadek jest tu treścią: bez niego bramka mówiłaby „nie podstawiaj
stałych", a nie „nie podstawiaj TYCH". Wyrażona jest jedną równością, a nie parą
`X in` / `Y not in` — rozbicie dawało bramce `test_ile_bramek_stoi_na_NAPISIE`
dwie asercje kształtu „literał in coś", a mówiło mniej.

Do tego dwie podłogi na oba czytniki, obie WOLNE, bo obu populacji przybywa
razem z narzędziami.

## 7. Ten moduł sam jest przykładem kształtu pierwszego

`definicje(root=ROOT)`, `odczyty(root=ROOT)` i `_pliki_python(root=ROOT)`
w `test_dead_constants.py` wiążą `ROOT` domyślnie. Nie jest to usterka — nikt
tego `ROOT` nie podstawia, a testy przekazują `root` wywołaniem. Jest to natomiast
powód, dla którego bramka porównuje PRZECIĘCIE dwóch list, a nie karze samego
wiązania: 132 funkcje mają ten kształt i przepisanie ich byłoby pracą bez
zmierzonej potrzeby.

## 8. Czego świadomie nie zrobiono

Nie przepisano 132 domyślnych argumentów na odczyt w ciele — większość to progi
liczbowe, których nikt nie podstawia, a zmiana sygnatur byłaby pracą bez
zmierzonej potrzeby; wyklucza to też pole „Poza zakresem". `src/` nietknięte.

Zapadka prozy z 6.D259 złapała mój akapit **szósty raz w tej serii**: cztery
pogrubione liczby podniosły ją ze 175 na 179. Podnosić górnej nie wolno, więc
zdjąłem pogrubienie z trzech i zostawiłem przy dacie, która pogrubienia nie liczy.
