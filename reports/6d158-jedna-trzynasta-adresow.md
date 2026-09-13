# 6.D158 — 6.D146 obejrzało 102 z 1279 adresów, czyli jedną trzynastą; a zero w dwóch polach jest STRUKTURALNE

**13.09.2026**, na `c439db0`. Wejście: `tools/tests/test_field_paths.py`
(`adresy_w_wykonanych`, `kandydaci_zlego_adresu`, `FIELDS`, `MODULE_CALL`,
`PATH_TOKEN`), `docs/TASKS.md`.

Pozycja żądała **liczby wywołań modułu per POLE** w blokach wykonanych i **liczby
kandydatów** dla każdego z trzech pól osobno, a pole „Skończone, gdy" — żeby wiadomo
było, **jaką część adresów obejrzało 6.D146, wyrażoną ułamkiem, a nie słowem**.

## 1. GŁÓWNY WYNIK: ani całość, ani jedna trzecia — jedna trzynasta

Bloków WYKONANYCH: **242** (po domknięciu tej pozycji — patrz §1.1).

| pole | adresów (`PATH_TOKEN`) | wywołań modułu | kandydatów |
|---|---|---|---|
| **Wejście** | **851** | **0** | **0** |
| **Wyjście** | **63** | **0** | **0** |
| **Weryfikacja** | **365** | **102** | **10** |
| **razem** | **1279** | **102** | **10** |

Pozycja pytała: *„czy 92 to całość adresów w blokach wykonanych, czy jedna trzecia"*.

**Nie jest ani jednym, ani drugim. Jest 102 z 1279, czyli niecałe osiem procent —
około jednej trzynastej.** Licząc same adresy `.py` wychodzi mniej więcej jedna siódma.

### 1.1. Domknięcie pozycji ZMIENIA liczbę, którą pozycja mierzy

Pierwszy pomiar, zrobiony przed zapisaniem rozstrzygnięcia, dał **849 / 63 / 364**
przy **241** blokach i **101** wywołaniach. Po domknięciu jest **851 / 63 / 365**
przy **242** i **102** — bo **domknięcie przenosi WŁASNY blok tej pozycji do zbioru
wykonanych**, razem z adresami, które ten blok cytuje w swoim polu „Wejście”.

Nie jest to usterka pomiaru, tylko jego własność, i stoi tu zapisana, bo przy następnym
czytaniu różnica 849 vs 851 wyglądałaby jak błąd. Ułamek drgnął o trzy tysięczne
i został tą samą jedną trzynastą — czyli rozstrzygnięcie §1 nie zależy od tego, po
której stronie domknięcia się mierzy. **Przybite są liczby PO**, bo to one opisują
drzewo, które ląduje w `main`.

Nie jest to zarzut wobec 6.D146: tamta pozycja mierzyła dokładnie to, o co pytało jej
własne pole „Wyjście". Jest to **liczba, której tamta pozycja nie miała** — a bez niej
zdanie „dziesięciu kandydatów da się przeczytać ręcznie" brzmi jak zdanie o całości,
a jest zdaniem o jednej trzynastej.

## 2. Zero w „Wejściu" i „Wyjściu" NIE jest odkryciem o pokryciu

Gdyby zostawić tabelę bez tego akapitu, wiersze `0` czytałoby się jako „w tych polach
nie ma adresów". **To nieprawda: stoi ich tam 914 — więcej niż w „Weryfikacji".**

`MODULE_CALL` to `test_all\.py\s+(\S+)`, szukane **wyłącznie w płotku** (` ``` `).
Czyli szuka **WYWOŁANIA**. Polecenia stoją w „Weryfikacji" i tylko tam; „Wejście"
i „Wyjście" niosą **ścieżki**, a nie komendy. **Zero jest więc własnością pytania,
a nie drzewa.**

Wykonane na wejściu **syntetycznym**, bo drzewo tych dwóch przypadków nie rozdziela —
pole ze ścieżką i bez wywołania wygląda w nim tak samo jak pole, którego czytnik nie
umie przeczytać:

```python
module_names("- **Wejście:** `tools/tests/test_backlog.py`, `docs/TASKS.md`.")
    == []                           # wywołań nie ma
PATH_TOKEN → ["tools/tests/test_backlog.py", "docs/TASKS.md"]
                                    # ale ścieżki SĄ — obie strony porównania

module_names("- **Weryfikacja:**\n  ```bash\n  python3 … test_all.py test_backlog.py\n  ```")
    == ["test_backlog.py"]          # a wywołanie czytnik widzi
```

Trzecia asercja jest tu konieczna: bez niej dwie pierwsze przechodziłyby także wtedy,
gdyby `module_names` nie widziało **niczego**. **KN-3 mierzy to wprost** i zapala się
komunikatem „zero wyżej jest zerem czytnika, a nie zerem drzewa".

## 3. WNIOSEK, KTÓRY Z TEGO PŁYNIE, JEST O BRAMCE — i domyka 6.D157

Rozszerzenie reguły kandydatów na pozostałe dwa pola **nie polega na podaniu jej innej
nazwy pola**. Tam nie ma wywołań do znalezienia; potrzebna byłaby **reguła innego
kształtu**.

To spotyka się z wczorajszym 6.D157. Tamta pozycja zmierzyła, że klasą, która się
powtarza, jest **adres ISTNIEJĄCY, ale nie ten** — bo bramka istnienia przepuszcza go
za każdym razem. Dziś dochodzi druga połowa: **jedyna reguła celująca w tę klasę
(kandydaci wg prozy) sięga do 102 z 1279 adresów i strukturalnie nie może sięgnąć do
pola, w którym adresów jest najwięcej.**

Bramka **istnienia** obejmuje od 6.D146 wszystkie trzy pola i wszystkie bloki — nazwa
modułu NIEISTNIEJĄCEGO jest pilnowana wszędzie. Poza zasięgiem jest, wszędzie poza
„Weryfikacją", wyłącznie adres zły-ale-istniejący.

## 4. Bramki — trzy

| test | co pilnuje |
|---|---|
| `test_ile_adresow_stoi_w_kazdym_z_trzech_pol_blokow_wykonanych` | dziewięć liczb z §1, każda równością |
| `test_jaka_czesc_adresow_obejrzala_regula_kandydatow_6D146` | ułamek, przybity **z obu stron** (między 1/20 a 1/8) |
| `test_zero_wywolan_poza_Weryfikacja_jest_STRUKTURALNE` | §2, na wejściu syntetycznym |

Ułamek jest przybity **przedziałem, a nie równością**, i to jest wybór: równość na
samym ułamku zapalałaby się przy każdym dopisanym bloku, a zdanie tej pozycji brzmi
„około jednej trzynastej", nie konkretny iloraz. Same liczby stoją przybite
równością piętro wyżej.

## 5. Kontrole negatywne — trzy, wszystkie czerwone

Baza: **31/31** w module. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | adresy liczone zawsze w „Weryfikacji" (pole ignorowane) | **29/31** |
| KN-2 | `MODULE_CALL` łapie każdy moduł, nie tylko wołany przez `test_all.py` | **29/31** |
| KN-3 | czytnik wywołań zawsze pusty | **22/31** — dziewięć czerwonych |

**KN-3 zapala dziewięć testów, w tym cztery starsze niż ta pozycja** — czyli czytnik
wywołań jest nośnikiem całej rodziny, a nie tylko moich trzech liczb. Zapala też
`test_zero_wywolan_poza_Weryfikacja_jest_STRUKTURALNE` dokładnie tym komunikatem,
dla którego ten test powstał.

**Pierwsze podejście do KN-2 wysypało się `TypeError`-em zamiast zapalić asercję** —
podmieniałem `_code_lines` na `text.split`, a `field_body` bywa `None`. Kontrola,
która wywala się w innym miejscu, niż mierzy, nie mierzy nic; przepisana na podmianę
samego `MODULE_CALL`.

## 6. Czego świadomie nie zrobiłem

- **Nie czytałem nowych kandydatów i nie poprawiałem adresów** — pole „Poza zakresem"
  zabrania obu.
- **Nie dopisałem reguły dla „Wejścia" i „Wyjścia"**, choć §3 mówi, że jej brakuje.
  Ta pozycja miała **policzyć**; jaki kształt miałaby mieć reguła obejmująca 851
  adresów bez zalania kosza fałszywymi trafieniami, jest osobnym pytaniem — i stoi
  już w kolejce jako 6.D187, od strony `PATH_TOKEN`.
- **Nie ruszyłem `MODULE_CALL` ani `PATH_TOKEN`** — obie liczby z §1 wyszły z nich
  takich, jakie są, i zmiana przyrządu przy okazji pomiaru unieważniłaby pomiar.
