# 6.D310 · Milczą dwie z szesnastu — a jednostka stoi w NAZWIE, czyli w miejscu, którego pole nie wymienia

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `fd09a09`

6.D301 znalazło szesnaście progów ułamkowych w `tools/tests/` i zapisało, że trzynaście
z nich to **tolerancje fizyczne**, a nie udziały populacji. Ta pozycja pyta, ile
tolerancji względnych ma przy sobie powiedziane, **czego** dotyczą i w jakiej jednostce.

Odpowiedź: **milczą dwie**. Ale liczba, dla której warto było tę pozycję wziąć, jest
inna: **jednostka stoi w tym projekcie w NAZWIE mierzonej wielkości**, czyli w miejscu,
którego pole „Wyjście" nie wymienia — siedem razy na osiem.

---

## 1. Populacja zgadza się z 6.D301 co do liczby, a mój PIERWSZY klasyfikator był zły

```
T1 — asercji z TOLERANCJA WZGLEDNA: 16    w 9 plikach
```

Szesnaście, dokładnie jak 6.D301. Ale automatyczny podział na wymiarowe
i bezwymiarowe, który napisałem najpierw, dał **trzy wymiarowe** — wobec trzynastu
u tamtej pozycji. Zamiast wybrać którąkolwiek liczbę, wypisałem wszystkie szesnaście
i **przeczytałem je z kontekstem**.

**Mój klasyfikator mylił się w OBIE strony.** Rozstrzygał po przyrostkach nazw
(`_m`, `_s`, `speed`, `radius`) — a wielkości w tych asercjach nazywają się `v0`,
`base`, `limit`, `reach`, `minimum`, `expected`. Dwa wpisy, które zgłosił jako
milczące, nazywają jednostkę **wprost w identyfikatorze**:

```
test_schedule_envelope.py  w.272   0.5 * SE.SEARCH_CEILING_KMH
test_sweep.py              w.142   0.8 * SW.UV_METRES_PER_UNIT
```

`KMH` i `METRES` stoją w nazwie stałej. Przyrząd, który ich nie widzi, mierzy własny
słownik przyrostków, a nie drzewo.

**Przy populacji szesnastu wpisów właściwym przyrządem są oczy, nie wyrażenie
regularne** — i zapisuję to jako pierwszą rzecz, bo wybór przyrządu był tu całą
różnicą między odpowiedzią a artefaktem.

## 2. Reguła podziału, spisana jawnie i stosowana do każdego z szesnastu

**Wielkość jest WYMIAROWA, gdy jej wartość zmienia się przy zmianie jednostki
projektu** (metr, sekunda, m/s, kg, procent pochylenia — `docs/04-conventions.md`,
przeczytane, a nie zgadnięte). Bezwymiarowa — gdy nie.

```
 1. test_braking.py            w.305   0.5 * v0 * seconds          WYMIAROWA  (droga, m)
 2. test_crs.py                w.253   0.9 * expected              WYMIAROWA  (wyznacznik, m²/deg²)
 3. test_lod.py                w.180   0.15 * (1.0 + reach)        WYMIAROWA  (stats["max_m"])
 4. test_lod.py                w.211   0.01 * base                 WYMIAROWA  (tube_volume_m3)
 5. test_lod.py                w.599   limit * 0.999               WYMIAROWA  (sagitta_m)
 6. test_placement.py          w.385   minimum * 0.999             WYMIAROWA  (MIN_SECTION_HEIGHT_M)
 7. test_schedule_envelope.py  w.272   0.5 * SEARCH_CEILING_KMH    WYMIAROWA  (km/h)
 8. test_schedule_envelope.py  w.297   speed * 0.999               WYMIAROWA  (km/h)
 9. test_shot_metadata_gate.py w.385   94.0 * 0.01                 WYMIAROWA  (length_m)
10. test_sweep.py              w.142   0.8 * UV_METRES_PER_UNIT    WYMIAROWA  (m na jednostkę)
11. test_shot_metadata_gate.py w.387   100.0 * 0.01                bezwymiarowa (własność float)
12. test_surface_sections.py   w.199   0.5 * (-1.0 + 1.0)          bezwymiarowa (środek przedziału)
13. test_visual.py             w.216   0.12 * 50                   bezwymiarowa (jasność 0–1)
14. test_visual.py             w.217   0.12 * 5                    bezwymiarowa (jasność 0–1)
15. test_visual.py             w.851   0.0722 * 60                 bezwymiarowa (współczynnik Rec.709)
16. test_visual.py             w.1300  0.0722 * 128                bezwymiarowa (współczynnik Rec.709)
```

**Dziesięć wymiarowych, sześć bezwymiarowych.**

## 3. NIE ODTWARZAM trzynastki z 6.D301 i mówię, których sześciu nie liczę

6.D301 podało trzynaście tolerancji fizycznych; ja liczę **dziesięć**. Różnicy nie
uzgadniam — wypisuję, co odsiewam i dlaczego, żeby dało się to sprawdzić bez czytania
mojego kodu:

* **`100.0 * 0.01 == 1.0`** — to jest zdanie o **arytmetyce zmiennoprzecinkowej**,
  prawdziwe niezależnie od jednostki; stoi obok wielkości wymiarowej, ale samo nią
  nie jest. Jest tam po to, żeby uzasadnić konstrukcję testu.
* **`0.5 * (-1.0 + 1.0)`** — środek przedziału znormalizowanego.
* **cztery wpisy z `test_visual.py`** — `0.12` i `0.0722` to współczynniki jasności
  (Rec.709) i gradient w skali 0–1; obraz nie ma metrów.

Możliwe, że 6.D301 liczyło do fizycznych także te sześć albo część z nich — **tego
nie wiem i nie zgaduję**. Mówię tylko, na czym stoi moja dziesiątka.

## 4. ODPOWIEDŹ: MILCZĄ DWIE — a jednostka mieszka w NAZWIE

Pole pyta, ile z wymiarowych nazywa jednostkę **w komunikacie albo w komentarzu**.
Policzyłem to i wyszła liczba, która niczego nie tłumaczy — dopóki nie dołożyć
trzeciego miejsca:

```
jednostka nazwana w IDENTYFIKATORZE mierzonej wielkosci:  7
jednostka nazwana w KOMUNIKACIE asercji:                  1
jednostka nie nazwana NIGDZIE:                            2
```

**Siedem z ośmiu wypadków, w których jednostka w ogóle pada, to identyfikator:**
`stats["max_m"]`, `tube_volume_m3`, `sagitta_m`, `MIN_SECTION_HEIGHT_M`,
`SEARCH_CEILING_KMH`, `length_m`, `UV_METRES_PER_UNIT`. W komunikacie pada raz —
`test_schedule_envelope.py` w. 297, gdzie f-string mówi `{distance} m / {scheduled} s:
{speed} km/h`. W komentarzu **nie pada ani razu**.

**Pole wymienia dwa miejsca, a projekt konsekwentnie używa trzeciego.** Jest to ten
sam kształt, który zmierzyłem przy 6.D304: tam pole prosiło o podział na dwie klasy,
a populacja miała trzy, i 4 + 10 nie dawało 18. Tutaj 1 + 0 nie daje 8.

**Milczące dwie:**

```
test_braking.py  w.305   assert distance > 0.5 * v0 * seconds, (distance, v0 * seconds)
test_crs.py      w.253   assert 0.9 * expected < value < 1.2 * expected, (...)
```

Pierwsza porównuje **drogę** z iloczynem prędkości i czasu; `seconds` nazywa jednostkę
jednego czynnika, ale metr wyniku nie pada nigdzie. Druga porównuje **wyznacznik
jakobianu** przekształcenia lon/lat → x/y, czyli wielkość o jednostce `m²/deg²`,
a komunikat jest krotką wartości.

## 5. Odpowiedź na pytanie, które pole kazało zadać wprost

Pole żąda powiedzieć, ile z milczących dotyczy wielkości **bezwymiarowej** — bo wtedy
milczenie nie jest brakiem — i dopuszcza odpowiedź „wszystkie".

**Zero.** Obie milczące są wymiarowe. Milczenie jest więc w obu wypadkach brakiem,
a nie własnością wielkości. **Nie znaczy to, że jest usterką** — pole zabrania tego
wniosku i słusznie: `distance` przy `v0 * seconds` jest w metrach dla każdego, kto
zna `docs/04-conventions.md`, a wyznacznik jakobianu ma jednostkę, której nikt
rozsądny nie wpisuje do komunikatu. **Liczę, nie oceniam.**

## 6. Przewidywania spisane PRZED pomiarem — NIEZALEŻNE, i trzy OBALONE

Tej pozycji nie mierzył w tej sesji żaden agent; zapisałem to w definicjach.

| # | przewidywanie | wynik |
|---|---|---|
| Y1 | tolerancji względnych: 15–45 | trafione (16) |
| Y2 | wymiarowych **mniej niż połowa** | **OBALONE** — dziesięć z szesnastu, czyli 62 % |
| Y3 | z wymiarowych milczy **więcej niż połowa** | **OBALONE** — dwie z dziesięciu, czyli 20 % |
| Y4 | odpowiedź nie brzmi „wszystkie" | trafione (zero) |
| Y5 | kontrola nie zda się w literze | trafione (dziesięć wobec trzynastu) |
| Y6 | największe skupienie w module o geometrii | **OBALONE** — `test_visual.py` z czterema |

**Y2 i Y3 upadły razem i z jednego powodu, który nazywam:** założyłem, że zestaw
narzędzi mierzy głównie **siebie** — liczności, udziały, pokrycia — a fizyki dotyka
rzadko. Jest odwrotnie w tej populacji: **tolerancja względna jest w tym drzewie
idiomem FIZYCZNYM**, bo udziały porównuje się z progiem całkowitym albo z ułamkiem
liczności, a nie z tolerancją. Zgadłem z charakteru zestawu zamiast policzyć.

Y3 upadło dodatkowo dlatego, że nie przewidziałem §4 — spodziewałem się, że jednostka
pada w komunikacie albo nigdzie, bo pole wymienia tylko te dwa miejsca. **Przyjąłem
podział pola za wyczerpujący**, a to jest dokładnie ten błąd, przed którym broniła się
6.D304 czwartą klasą.

## 7. Czego świadomie nie zrobiono

- **Nie dopisano jednostki do żadnej z dwóch milczących** — pole zabrania wprost,
  a §5 mówi, dlaczego milczenie nie jest tam automatycznie usterką.
- **Nie zmieniono żadnego progu** ani żadnego komunikatu.
- **Nie postawiono bramki na kształcie tolerancji.**
- **Nie uzgodniono mojej dziesiątki z trzynastką 6.D301** — §3 wypisuje sześć wpisów,
  których nie liczę, żeby różnicę dało się sprawdzić bez czytania mojego kodu.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Jednostka jako część identyfikatora jest w tym projekcie konwencją, której nie
   pilnuje żadna bramka.** `sagitta_m`, `tube_volume_m3`, `MIN_SECTION_HEIGHT_M`,
   `SEARCH_CEILING_KMH` — siedem nazw z siedmiu wypadków. Konwencja bez bramki działa
   tak długo, jak długo wszyscy ją pamiętają.
2. **`test_visual.py` ma cztery z szesnastu tolerancji i wszystkie bezwymiarowe** —
   to moduł najdalszy od fizyki linii, a zarazem największe skupienie tolerancji
   względnych. Moje przewidywanie szukało ich w geometrii.
3. **`0.999` pada trzy razy** (`limit * 0.999`, `minimum * 0.999`, `speed * 0.999`)
   i za każdym razem znaczy to samo: „o włos poniżej progu, żeby pokazać, że próg
   jest ostry". Jest to idiom, a nie tolerancja — i mój czytnik liczy go razem
   z tolerancjami, bo składniowo się nie różnią.
