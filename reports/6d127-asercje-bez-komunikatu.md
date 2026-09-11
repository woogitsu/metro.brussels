# 6.D127 — 2377 asercji zgłasza się bez ani jednego słowa, i od dziś ta liczba może tylko maleć

**Zmierzone 11.09.2026 na:** `e0543cd`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_assertion_gate.py` (`asercje_bez_komunikatu`,
`nieme_w_drzewie`, `NIEME_ASERCJE`), `ast`, `tools/tests/tree_walk.py`.

---

## 1. Pomiar

| co | ile |
|---|---|
| asercji w `tools/tests/` razem | **6264** |
| z komunikatem | **3887** (62,1 %) |
| **bez komunikatu** | **2377** (37,9 %) |
| modułów, w których jest co najmniej jedna | **103** ze 121 |

Pięć modułów o największej liczbie: `test_clearance_profile.py` 117,
`test_inspire_rail.py` 102, `test_visual.py` 92, `test_surface_sections.py` 84,
`test_lod.py` 81.

Liczba jest **wypisana w module** jako `NIEME_ASERCJE` (per moduł) i `NIEMYCH_RAZEM`
(suma **liczona** z tamtej listy, nie wpisana obok niej — wpisana rozjechałaby się
przy pierwszym obniżonym wpisie, czyli dokładnie wtedy, gdy ktoś tę listę poprawia).

## 2. Dlaczego lista jest PER MODUŁ, a nie per asercja

Zamknięta lista 2377 pozycji byłaby dłuższa od kodu, który opisuje, i rozjeżdżałaby
się przy każdym przesunięciu wiersza. Moduł jest najmniejszą jednostką, którą da się
wymienić z nazwy i która **nie zmienia się od zmiany numeru wiersza**.

## 3. Zapadka działa w obie strony i obie są zamierzone

* **W górę:** dopisanie asercji bez komunikatu zapala bramkę (KN-1). Moduł spoza
  listy ma mieć **zero** — nowy plik testowy zaczyna z komunikatem przy każdej
  asercji (KN-4).
* **W dół:** dopisanie komunikatu **też** ją zapala, z żądaniem obniżenia wpisu
  w tym samym commicie (KN-3). Bez tego wpis zostawałby zawyżony i zwalniał moduł
  z pilnowania tylu asercji, ile zdążył naprawić.
* **Wpis bez modułu** znika razem z nim (KN-5).

Asercja **z** komunikatem dopisana do modułu z listy bramki **nie zapala** — KN-2 jest
kontrolą dodatnią i wyszła zielona, bo taka ma być. Bez niej nie dałoby się odróżnić
„bramka pilnuje asercji niemych" od „bramka pilnuje każdej nowej asercji".

## 4. Licznik czyta DRZEWO SKŁADNI, i to nie jest ostrożność

`assert x, "powód"` różni się od `assert x` obecnością pola `msg` w węźle, a nie
obecnością przecinka. Grep po przecinku myli się w obie strony, a najgorszy przypadek
jest realny: **`assert (a, b)` ma przecinek i komunikatu nie ma** — jest krotką, czyli
asercją **zawsze prawdziwą**. Licznik grepowy policzyłby go jako asercję z powodem
i przepuścił test, który nie sprawdza niczego.

KN-6 wymieniła AST na grep po przecinku. Wynik: zapaliły się **dwa** testy naraz,
a skan zaczął zgłaszać trzy moduły, których nie zgłaszał —
`test_csharp_test_methods.py`, `test_csv_provenance.py`, `test_runner_process_exit.py`.
Różnica nie jest więc hipotetyczna: grep myli się dziś, na tym drzewie, w trzech
miejscach.

## 5. Bramka złapała najpierw mnie

Pierwszy przebieg po dopisaniu bramki dał:

```
FAIL test_lista_asercji_bez_komunikatu_moze_tylko_malec:
  asercji bez komunikatu PRZYBYŁO (moduł, było, jest):
  [('test_assertion_gate.py', 2, 6)] — nowa asercja ma nieść powód
```

Cztery z sześciu to asercje, które sam przed chwilą napisałem w teście kontrolnym
licznika. **Dopisałem im komunikaty, zamiast podnieść wpis** — reguła obowiązuje od
kodu, który ją wprowadza, i to jest jedyny moment, w którym można to pokazać za darmo.

## 6. Kontrole negatywne — WYKONANE, nie opisane

Baza `test_assertion_gate.py`: **29/29** (było 27).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | asercja bez komunikatu dopisana do modułu z listy | **28/29** |
| KN-2 | asercja **z** komunikatem dopisana | **29/29 ZIELONA — poprawnie** |
| KN-3 | wpis podniesiony (99 wobec 7) | **28/29**, „UBYŁO" |
| KN-4 | nowy moduł spoza listy z asercją bez komunikatu | **28/29** |
| KN-5 | wpis na liście dla modułu, którego nie ma | **28/29** |
| KN-6 | licznik grepem po przecinku zamiast AST | **27/29**, dwa testy, trzy moduły |
| KN-7 | błąd składni daje `0` zamiast `None` | **28/29** |

Po każdej: `md5sum -c` → `OK` na dwóch plikach.

KN-7 pilnuje rzeczy, którą łatwo przeoczyć: plik z błędem składni ma dać `None`,
a nie zero. Zero czytałoby się jako „sprawdzone i czysto", czyli jako wynik pomiaru,
którego nie było — ta sama rodzina co 6.D27.

## 7. Czego nie zrobiłem

* **Nie dopisałem komunikatów do 2377 asercji** — wprost w polu „Poza zakresem":
  to praca liniowa w ich liczbie i osobna pozycja. Ta lista ma tylko móc **maleć**.
* **Nie ruszyłem `assertion_gate.py`** (licznika asercji). Bramka stanęła w module,
  który już mierzy asercje, tak jak żąda pole „Weryfikacja", ale sam licznik odpowiada
  na inne pytanie — ile asercji się **wykonało**, a nie ile ich **napisano**.
* **Nie objąłem skanem `src/` ani `tests/Sim.Tests/`.** Pole „Wejście" mówi
  o `tools/tests/`; asercje C# mają własny kształt (`Assert.AreEqual(..., "powód")`)
  i własną bramkę, więc wspólny licznik byłby licznikiem dwóch różnych rzeczy.

## 8. Zauważone przy okazji

**37,9 % asercji w zestawie nie mówi nic**, a zestaw ma 121 modułów i 2307 testów.
Największe skupiska to moduły geometryczne (`test_clearance_profile.py`,
`test_inspire_rail.py`, `test_visual.py`) — czyli te, których czerwień najtrudniej
czyta się z samego kodu, bo asercja porównuje tam liczbę z liczbą. Kolejność
naprawiania, gdyby ktoś ją kiedyś podjął, wynika więc z tej tabeli sama.
