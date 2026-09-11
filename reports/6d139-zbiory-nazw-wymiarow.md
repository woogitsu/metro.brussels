# 6.D139 — audyt i moduły mają wymieniać TE SAME wymiary, nie tyle samo

**11.09.2026**, na `5b652dc`. Pozycja: README podaje 18 i 24, obie liczby od 6.D121
sprawdzane wobec drzewa — a `docs/21-measured-vs-assumed.md` niesie te same wymiary
wypisane z osobna i **nikt tamtej listy z modułami nie porównuje**.

## 1. Co było, a czego nie było

Bramki z T-212 i 6.D119 pytają w **jedną stronę**: czy każda stała modułu ma wpis
w dokumencie. Dwie dziury, obie zmierzone kontrolami:

* **kierunek** — nazwa, która **została w dokumencie**, choć z modułu zniknęła, nie
  zapala niczego. Dokument mówi wtedy o wymiarze, którego nie ma (KN-2: **tylko nowa
  bramka**, 20/21);
* **zasięg** — pytanie brzmi `f"\`{nazwa}\`" not in text`, czyli o obecność nazwy
  **gdziekolwiek w dokumencie**. Wpis przeniesiony do innej sekcji albo wspomniany
  w prozie zaspokaja je tak samo dobrze jak wiersz tabeli (KN-3: bramka nazw została
  **zielona**, choć wiersza w tabeli już nie było).

Licznik też by tego nie złapał — i to jest powód, dla którego pole „Wyjście" żądało
**zbiorów, nie sum**: wymiana jednego wymiaru na inny zostawia liczbę bez zmian.

## 2. Pomiar

| sekcja audytu | moduł | nazw w dokumencie | stałych w module | różnica |
|---|---|---:|---:|---|
| `## 4e.` | `station_components` | **18** | **18** | żadna |
| `## 4g.` | `m7_cab` | **24** | **24** | żadna |

Zbiory są dziś równe co do nazwy. Odwzorowanie kluczy kabiny na stałe modułowe jest
regularne (`cab_bulkhead_m` → `DESIGN_CAB_BULKHEAD_M`) i **jest bijekcją** — sprawdzone
osobno, bo „zwykle się zgadza" nie jest zdaniem o kodzie.

## 3. Co stoi w bramce

* **porównanie zbiorów w obie strony, w obrębie sekcji** — komunikat wypisuje obie
  różnice z nazwy;
* **liczba per sekcja** (18 i 24), przybita równością, z odesłaniem do README;
* **bijekcja kluczy** słownika na stałe modułowe, osobno dla obu modułów —
  `station_components` ma tu dziś tożsamość, ale „dziś" nie znaczy „zawsze";
* **kontrola przyrządu na wejściu syntetycznym**: nazwa wspomniana w **prozie** sekcji
  nie liczy się jako wpis, a cięcie po nagłówku naprawdę odcina sekcję następną.

## 4. Kontrole negatywne

Baza `test_dimension_audit.py`: **21/21** (było 18). `__pycache__` czyszczony przed
każdym przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na trzech
plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | wymiar przemianowany w dokumencie | **18/21**, trzy testy |
| KN-2 | wpis w dokumencie, którego moduł nie zna | **20/21** — **tylko nowa bramka** |
| KN-3 | wiersz przeniesiony do prozy innej sekcji | **19/21**; bramka nazw ZIELONA |
| KN-4 | klucz słownika rozjechany ze stałą modułową | **20/21** |
| KN-5 | cięcie po nagłówku zdjęte | **19/21**, dwa testy |
| KN-6 | liczba 24 rozjechana z drzewem | **20/21** |

**KN-2 jest rozstrzygająca.** Dokładnie ten przypadek, o którym mówi pole „Skończone,
gdy": stare bramki milczą, nowa mówi, czego dokument nie ma prawa twierdzić.

**KN-3 pokazuje drugą dziurę osobno**: po przeniesieniu wiersza do prozy
`test_audit_covers_every_cab_design_constant` **przeszedł** — nazwa nadal jest
w dokumencie. Zapaliły się tylko bramka wartości i nowa bramka zbiorów.

**KN-5 mierzy, ile robi samo cięcie sekcji**: bez niego do zbioru sekcji 4e wchodzi
**46 nazw** z całego dokumentu, w tym wszystkie stałe kabiny i sweepa.

## 5. Weryfikacja

```
  21/21 przeszło        test_dimension_audit.py   (było 18)
  2352/2352 przeszło, 123 moduły, KOD=0, RAZEM 171.140 s
```

## 6. Czego nie zrobiłem

* **Nie zmieniłem wartości żadnego wymiaru ani nie dopisałem nowego** — oba wprost
  w „Poza zakresem".
* **Nie objąłem porównaniem zbiorów pozostałych sekcji audytu** (`m7_layout`,
  `profiles`, `sweep`). Mają one bramki tego samego, jednokierunkowego kształtu i tę
  samą dziurę, ale pole „Wejście" tej pozycji wymienia dwa moduły, a rozszerzenie
  wymaga odwzorowania nazw dla każdego z osobna — `profiles` na przykład nie trzyma
  stałych `DESIGN_*` wcale.
* **Nie zdjąłem starych bramek jednokierunkowych.** Nowa jest od nich mocniejsza, ale
  ich komunikaty mówią co innego („stała bez wpisu" kontra „zbiory się różnią"), a przy
  dwóch różnicach naraz obie wypowiedzi są czytelniejsze niż jedna.
