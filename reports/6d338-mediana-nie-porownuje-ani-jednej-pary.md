# 6.D338 · Medianą nie porównuje dwóch klas ANI JEDNO miejsce w drzewie — bo przy każdej z sześciu stoi druga miara

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `4e6b275`

**Sprawdzone ponownie 21.09.2026 na bazie `e163388`, przed commitem, i wynik jest ten sam:** sześć wywołań `statistics.median` w trzech plikach, te same numery wierszy — 267 w `tools/tests/test_suite_runtime_budget.py`, 389 i 439 w `tools/track/inspire_rail.py`, 158, 233 i 237 w `tools/track/tunnel_width.py`. Daty pomiaru NIE przepisuję na dzisiejszą: liczby poniżej zmierzono 20.09.2026 i to jest ich data.

6.D328 §3.1 zapisało, że przewidywanie Z4 porównywało dwie klasy **medianą** — a ta
w obu wynosi **1,0**, więc nie rozróżnia ich w ogóle; rozróżnia je dopiero średnia
(1,98 wobec 1,86) i udział nazw jednoplikowych (56 % wobec 63 %). Ta pozycja
**czyta i liczy**; żadnej miary nie podmienia i żadnego progu nie rusza.

---

## 1. Kontrola przyrządu ZDANA

```
=== KONTROLA PRZYRZADU ===
   tools/tests/test_suite_runtime_budget.py:267  funkcja=<modul>
   kod=statistics.median([cpu for _id, _w, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA])
   czy w klasie POROWNANIE: False
```

`MEASURED_MED_CPU_S` wychodzi w klasie „liczy medianę" i **nie** wychodzi w klasie
„porównuje nią dwie klasy" — dokładnie jak żądało pole. Jest podłogą jednej
populacji, nie porównaniem dwóch.

## 2. Wszystkie sześć miejsc, imiennie

```
tools/tests/test_suite_runtime_budget.py   267  <modul>          statistics.median([cpu for …])
tools/track/inspire_rail.py                389  summarise_side   statistics.median(values)
tools/track/inspire_rail.py                439  spacing_by_link  statistics.median(values)
tools/track/tunnel_width.py                158  survey           statistics.median(widths)
tools/track/tunnel_width.py                233  summarise        statistics.median(widths)
tools/track/tunnel_width.py                237  summarise        statistics.median([r['width_m'] …])
```

**Sześć wywołań w trzech plikach.** Przewidywanie P2 („więcej niż dziesięć")
obalone, a P5 („większość w `test_suite_runtime_budget.py`") obalone tym mocniej:
tam stoi **jedno**, a pięć z sześciu jest w `tools/track/`.

## 3. ODPOWIEDŹ NA PYTANIE ZADANE WPROST: porównań jest ZERO

Jedynym kandydatem była para w `summarise` (`tunnel_width.py:233` i `:237`) —
dwie mediany w jednej funkcji. Przeczytałem ją:

```python
        "median_m": round(statistics.median(widths), 3),
        …
        "per_polygon": {name: round(statistics.median(
            [r["width_m"] for r in running if r["polygon"] == name]), 3)
            for name in sorted({r["polygon"] for r in running})},
```

To jest **mediana całości i rozbicie na poligony**, czyli podsumowanie i jego
rozwinięcie — nie porównanie dwóch klas. **Żadne z sześciu miejsc nie rozstrzyga
medianą porównania dwóch klas**, więc klasa „mediana po obu stronach równa" jest
pusta **z konstrukcji drzewa, a nie z mojego sita**, i mówię to wprost.

Przewidywanie P4 („co najmniej w jednym porównaniu mediana jest równa") jest
**obalone**, a warunek obalenia spisałem przed pomiarem i wypełniam go:
**przypadek z 6.D328 §3.1 jest w kodzie tego drzewa odosobniony.** Co więcej, on
sam nie stał w drzewie — mediana z Z4 została policzona w przyrządzie roboczym,
a nie w żadnej bramce.

## 4. GŁÓWNE ZNALEZISKO: przy każdej z sześciu median stoi DRUGA miara

Przewidywanie P6 trafione, i to w pełnym komplecie — **sześć na sześć**:

| miejsce | co stoi obok mediany |
|---|---|
| `tunnel_width.py:158` | `min_m`, `p05_m`, `p95_m`, `max_m` |
| `tunnel_width.py:233` | `min_m`, `p05_m`, `p95_m`, `max_m`, `stdev_m` |
| `tunnel_width.py:237` | rozbicie per poligon, czyli cały rozkład |
| `inspire_rail.py:389` | `mean_m`, `stdev_m`, `p05_m`, `p95_m`, `min_m`, `max_m` |
| `inspire_rail.py:439` | `min_offset_m`, `max_offset_m` |
| `test_suite_runtime_budget.py:267` | `MEASURED_MAX_CPU_S` z tej samej populacji |

**Kod tego projektu nigdy nie zostawia mediany samej.** Usterka, którą 6.D328 §3.1
złapało na własnym przewidywaniu, w kodzie nie ma gdzie wystąpić, bo każde miejsce
liczące medianę liczy przy niej co najmniej jeszcze jedną miarę.

## 5. W PROZIE jest inaczej — i tam ten kształt widać

Pole „Skąd" wymienia też `reports/`. Dwa raporty mają tabelę porównawczą z kolumną
mediany, a w jednej z nich **mediana nie rozróżnia trzech wierszy**:

```
| pakiet | porównanie | mediana | P95 | maks. |
| B | `001m` v2 | 3,27 m | 4,03 m | 4,58 m |
| E | `002m` v1 | 3,27 m | 11,85 m | 25,75 m |
| E | `006m` v1 | 3,27 m | 11,85 m | 25,75 m |
```

Trzy wiersze mają **tę samą medianę 3,27 m**, a różnią się P95 trzykrotnie
(4,03 wobec 11,85) i maksimum pięciokrotnie. Gdyby tabela miała samą medianę,
pakiet B i pakiet E wyglądałyby identycznie.

**Tabela ich nie myli, bo niesie trzy kolumny obok.** Jest to więc ten sam wzorzec
co w kodzie (§4) i ta sama lekcja co w 6.D328 §3.1, tylko z drugiej strony: mediana
nie rozróżnia, a rozstrzyga to, co stoi obok niej.

**Drugiej tabeli mediana rozróżnia i jest w niej treścią**: w
`reports/L1_A-crosscheck.md` mediana **0,00 m** wobec 3,34 m mówi, że dwie linie
mają na pniu identyczną geometrię. Podaję oba przypadki, bo pole ostrzegało wprost,
że równa mediana bywa **wynikiem**, a nie miarą martwą.

## 6. Przewidywania — trzy trafione, trzy obalone

| # | przewidywanie | wynik |
|---|---|---|
| P1 | kontrola przyrządu przejdzie | **trafione** (§1) |
| P2 | miejsc liczących medianę więcej niż dziesięć | **OBALONE**: sześć |
| P3 | porównań dwóch klas mniej niż pięć | **trafione**: zero |
| P4 | w co najmniej jednym porównaniu mediana równa | **OBALONE**: porównań nie ma (§3) |
| P5 | większość median w `test_suite_runtime_budget.py` | **OBALONE**: jedno z sześciu |
| P6 | co najmniej jedno miejsce ma obok mediany drugą miarę | **trafione**, sześć na sześć (§4) |

## 7. Czego świadomie nie zrobiłem

Nie podmieniłem miary w żadnym miejscu, nie ruszyłem żadnego progu, nie postawiłem
bramki na wyborze miary, nie tknąłem `docs/04-conventions.md`, `src/` ani `data/` —
wszystko to stoi w polu „Poza zakresem".

**Nie policzyłem median w prozie systematycznie.** §5 podaje dwa przypadki, na które
trafiłem, czytając trzydzieści pięć raportów wymieniających medianę; pełny przejazd
po tabelach prozy jest innym pytaniem i innym przyrządem, a pole „Wyjście" pyta
o `tools/tests/`.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

`tools/track/tunnel_width.py:158` i `:233` liczą medianę tej samej wielkości —
szerokości tunelu — ale z **różną liczbą miejsc po przecinku**: `round(…, 2)`
w `survey` i `round(…, 3)` w `summarise`. Obie liczby trafiają do tego samego pliku
wyjściowego. Nie jest to usterka i nie pilnuje tego żadna bramka; zapisuję, bo przy
sześciu miejscach różnica rzuca się w oczy.
