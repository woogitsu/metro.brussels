# 6.D201 — postaci jest sześć, nie cztery, i żadna nie jest bezczynna

**13.09.2026**, na `bb9e55e`. Wejście: `tools/tests/csharp_test_methods.py` (`maska`),
`tests/**/*.cs`, `src/**/*.cs`, `reports/6d188-czternascie-i-ani-jednego-jsona.md`.

## 1. Odpowiedź: liczb jest SZEŚĆ, a nie cztery, i to jest odpowiedź, nie poszerzenie zakresu

Pole „Wyjście" żądało **czterech** liczb — po jednej na gałąź — bo docstring `maska()`
mówił o „wszystkich czterech postaciach, które występują w `tests/`". Postaci, które ten
czytnik rzeczywiście rozróżnia, jest **sześć**; cztery liczby opisałyby cztery z nich
i przemilczały dwie.

| postać | `tests/` (52 pliki) | `src/` (77 plików) | razem |
|---|---:|---:|---:|
| zwykły | 3512 | 1223 | **4735** |
| interpolowany | 633 | 446 | **1079** |
| werbatim | 42 | **0** | **42** |
| surowy interpolowany (przedrostek podwójnego dolara) | 13 | 1 | **14** |
| surowy | 7 | 1 | **8** |
| werbatim interpolowany | 1 | **0** | **1** |
| **RAZEM** | **4208** | **1671** | **5879** |

**Dwie postacie, których tamta czwórka nie wymieniała w ogóle, występują.** Werbatim
interpolowany — raz, i to w żywym kodzie: `tests/Game.Tests/RunHeaderTests.cs:108`,
wzorzec `Regex` składany z nazwy pola i jednostki. Surowy interpolowany — czternaście
razy, czyli **więcej niż surowy bez przedrostka** (8).

Zdanie z docstringu było więc **niepełne, a nie nieaktualne**, i dlatego jest tam
**przepisane, a nie dopisane obok**, razem z sześcioma liczbami.

## 2. Gałąź o udziale zerowym: w całym korpusie NIE MA ANI JEDNEJ

To była druga połowa pytania — i odpowiedź jest po jednej stronie czysta, a po drugiej
ciekawsza.

- **W całym korpusie (`tests/` + `src/`): zero gałęzi bezczynnych.** Każda z sześciu ma
  udział dodatni, więc nie ma czego usuwać — a pole „Poza zakresem" i tak tego zabrania.
- **W samym `src/`: dwie gałęzie z zerem**, obie werbatim. Powód jest jeden i daje się
  nazwać: **werbatim służy w tym drzewie wyłącznie do wzorców `Regex`** (odwrotny
  ukośnik nie ucieka, więc `@"\\d+"` pisze się bez podwajania), a wzorce stoją
  w testach. Rdzeń i warstwa gry nie parsują tekstu wyrażeniami regularnymi.

Jest to ta sama zasada, którą 6.D186 zastosowało do markera `RootElement` (udział 0 z 18)
i 6.D187 do ukośnika w domknięciu wzorca — z tą różnicą, że **tam bezczynność wyszła na
jaw dopiero przez kontrolę negatywną, która wyszła ZIELONA, a tutaj dała się policzyć
wprost**. Liczba zamiast zdziwienia.

## 3. Liczenie idzie TYM SAMYM przebiegiem, co maskowanie

`klasy_literalow` i `maska` konsumują jeden generator `_przebieg`. Jest to cała treść tej
funkcji: bramka licząca własnym rozbiorem mówiłaby o sobie, a nie o tym, co `maska`
naprawdę robi — rodzina 6.D27, i dokładnie ten błąd, który przy 6.D198 dał 12 zamiast 10,
bo pytał o sąsiedztwo zamiast o deklarację.

**Przebudowa jest sprawdzona na wyjściu, nie na intencji.** Przed zmianą policzyłem
odcisk `md5` maski **129 plików**, po zmianie porównałem:

```
plikow o ZMIENIONEJ masce po przebudowie: 0
```

Zero na 129 — `maska` zwraca bajt w bajt to samo, co przed rozdzieleniem.

## 4. POPRAWKA DO RAPORTU 6.D200 — jego §7 mówi rzecz nieprawdziwą

Raport 6.D200 (scalony w #594) kończy się zdaniem:

> **`$"""…"""` (surowy interpolowany) nie występuje w drzewie ani razu.** Gałąź surowa
> jest więc ćwiczona wyłącznie przez zapisy bez przedrostka — a tych jest 30 par
> potrójnych cudzysłowów w `tests/` i `src/`.

**Pierwsze zdanie jest prawdziwe, drugie nie.** Surowy interpolowany z przedrostkiem
**pojedynczego** dolara istotnie nie występuje — ale z przedrostkiem **podwójnego**
występuje **czternaście razy**, i to jest ta sama gałąź. Gałąź surowa jest więc ćwiczona
**w 14 z 22 przypadków właśnie przez zapis z przedrostkiem**, a nie „wyłącznie przez
zapisy bez przedrostka". Liczba „30" pochodziła przy tym z `grep`-a po potrójnych
cudzysłowach, czyli liczyła **znaczniki**, a nie literały; literałów surowych jest **22**.

**Raportu nie poprawiam — raporty są historią (6.D108).** Poprawka stoi tutaj i wskaźnik
do niej dopisany jest do wiersza 6.D200 w `docs/TASKS.md`, tak jak przy 6.D106 i 6.D164.

**Skąd wziął się błąd, jest ważniejsze niż to, że był:** zdanie powstało z jednego
`grep`-a w sekcji „zauważone po drodze", a nie z przebiegu czytnika — czyli z dokładnie
tej drogi, którą ten projekt odrzuca w regule „pomiar o bramce robi się kodem samej
bramki". Sekcja „zauważone, nie tknięte" jest przy tym najmniej pilnowaną częścią
raportu i **żadna bramka jej nie sprawdza**: `test_report_claims` pyta o stałe cytowane
z kodu, a to zdanie nie cytowało żadnej.

## 5. Sześć kontroli negatywnych, baza 12/12

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | literał werbatim dopisany do `src/` (gałąź z zerem przestaje być zerowa) | 11/12 |
| KN-2 | `_przebieg` myli werbatim interpolowany z werbatim | **10/12** |
| KN-3 | pętla po korzeniach obiega raz zamiast dwóch | 11/12 |
| KN-4 | siódma gałąź w `_przebieg`, nienazwana w `POSTACIE` | 11/12 (na LICZBIE) |
| KN-4b | siódma NAZWA w `POSTACIE`, nieużywana — jedna zmienna | **10/12** (na KONTROLI PRZYRZĄDU) |
| KN-5 | korpus zwężony do trzech plików | 11/12 |

`md5sum -c` na trzech plikach po każdej: `OK`. **Ani jedna zielona.**

**KN-2 zapala DWA testy i to jest projekt, nie przypadek:** rozkład przestaje się zgadzać
z drzewem **i** rozjeżdża się kontrola na wejściu syntetycznym. Gdyby zapalał się tylko
rozkład, nie byłoby wiadomo, czy zmienił się czytnik, czy drzewo.

**KN-4b jest konieczna, bo KN-4 zapala się na czym innym.** Siódma gałąź w `_przebieg`
kradnie wystąpienia gałęziom istniejącym, więc pierwsza zapala się równość liczb i test
kończy bieg przed kontrolą przyrządu. Dopiero nazwa dodana **bez** użycia zostawia liczby
nietknięte i zostawia kontrolę samą. Ten sam wzorzec, co KN-6b przy 6.D199 i KN-3b przy
6.D200 — trzeci raz w tej sesji.

## 6. Czego świadomie nie zrobiłem

- **Żadnej gałęzi nie usunąłem** — pole „Poza zakresem" zabrania, a pomiar i tak mówi,
  że nie ma czego: zer w całym korpusie nie ma.
- **Gałęzi werbatim nie naprawiałem** — to 6.D200, domknięte w #594.
- **Nie poprawiłem raportu 6.D200.** Raporty są historią; poprawka jest w §4 tego
  raportu i we wskaźniku przy wierszu 6.D200.

## 7. Zauważone po drodze, nie tknięte

- **Sekcji „zauważone, nie tknięte" nie pilnuje żadna bramka** i §4 jest tego dowodem:
  zdanie oparte na jednym `grep`-ie przeszło przez pełny zestaw, przegląd i scalenie.
  Jest to najmniej sprawdzana część raportu, a czyta się tak samo jak reszta.
- **Wszystkie 42 wystąpienia werbatim w `tests/` to wzorce `Regex`** — sprawdzone na
  próbce pięciu pierwszych, wszystkie zaczynają się od znaku kotwicy albo klasy znaków.
  Gdyby ktoś przeniósł parsowanie tekstu do `src/`, dwa zera z §2 przestałyby być zerami
  i bramka to pokaże — ale **nie powie, że powodem jest przeniesienie**, tylko że liczba
  wzrosła.
- **`$$"""` jest liczniejszy od `"""` (14 do 8), a docstring nie wymieniał go wcale.**
  Postać najbardziej egzotyczna składniowo jest w tym drzewie **częstsza** od tej, którą
  opis uznał za podstawową.
