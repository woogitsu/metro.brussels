# 6.D193 — odpowiedź „zero" była trafiona, nie sprawdzona

**13.09.2026**, na `0ac5592`. Wejście: `tools/tests/test_suite_runtime_budget.py`
(`POMIARY`, `opisy_z_ranga`), `tools/tests/test_field_paths.py` (`SZESC_PRZYPADKOW`),
`tools/tests/test_readme_claims.py` (`POMIARY_BRAKOW`),
`reports/6d163-ranga-otwarta-i-ograniczona.md`.

## 1. Czego pozycja żądała

Liczby **kształtów** zapisu pomiaru w drzewie, policzonej ze źródeł, i rozstrzygnięcia,
czy da się postawić regułę odróżniającą zapis przebiegów od tablicy przypadków — a jeśli
się nie da, to zapisanej granicy.

## 2. Zarzut pozycji był ostrzejszy, niż go postawiono

Pozycja mówiła, że zdanie „innych list pomiarów nie ma" **wisi na jednym odczycie jednej
osoby**. Sprawdzone: wisiało **na zerze linii kodu**. Skan, na który powoływał się
docstring, wykonano ręcznie raz 13.09.2026, a jego wynik przepisano do prozy; w drzewie
nie została z niego ani jedna asercja.

## 3. Liczby, ze źródeł

Skan po **całym `tools/`** (6.D163 skanowało samo `tools/tests/`), klasyfikacja po
POŁOŻENIU daty ISO w literale:

| kształt | co znaczy | ile |
|---|---|---:|
| A | data na pozycji 0 krotki wpisu | **1** — `POMIARY` |
| B | data na pozycji dalszej | **0** |
| C | data w kluczu słownika | **2** — `OPISY_Z_RANGA_DOZWOLONA`, `NOTATIONS` |
| D | data w wartości słownika | **0** |
| E | data gdzie indziej w literale | **0** |

Stałych modułowych z **jakąkolwiek** datą ISO w literale: **siedem**. Kontenerów wśród
nich: **trzy**. Pozostałe cztery to dwa widoki `POMIARY` odcięte datą
(`POMIARY_RUNNERA_11_09`, `POMIARY_KONTENERA_JEDNO_DRZEWO` — wyrażenia, nie literały)
i dwa skalary (`AS_OF`, `DZIEN_PIERWSZEGO_WYNOSZENIA`).

**Te dwie liczby opisują dwie różne populacje i pomyliłem je przy pierwszym podejściu:**
napisałem bramkę liczącą kontenery i przypiąłem ją do siedmiu. Zapaliła się od razu
(3 przy zapadce 7), więc kosztowało to jeden przebieg, a nie jedną cichą nieprawdę — ale
gdyby liczby były bliżej siebie, kosztowałoby to drugie.

## 4. Odpowiedź „zero" się utrzymała — ale nie była sprawdzona

Kształtów B i D nie ma ani jednego, więc lista pomiarów ukryta przed starym wzorcem
nie istnieje i zdanie z 6.D163 zostaje prawdziwe.

**Nie było jednak sprawdzone, tylko trafione.** Stary wzorzec („krotka zaczynająca się
od daty") nie mógł zobaczyć kształtu C, a jeden słownik tego kształtu —
`OPISY_Z_RANGA_DOZWOLONA` — stoi **w tym samym pliku, kilkaset wierszy pod `POMIARY`**,
i czyta go **ta sama asercja**, która tamto zdanie wypowiada.

## 5. Granica sita jest większa, niż zakładała pozycja

Pozycja podejrzewała założenie o **położeniu** daty. Pomiar pokazał dziurę o poziom
wyżej: z trzech stałych, które pozycja wymieniła jako kandydatki, **dwie nie mają daty
ISO nigdzie w literale**.

| stała | dat ISO w literale | co to jest |
|---|---:|---|
| `POMIARY` | 20 | zapis przebiegów |
| `SZESC_PRZYPADKOW` | **0** | tablica przypadków; numery pozycji (`6.D59`), nie daty |
| `POMIARY_BRAKOW` | **0** | **ZAPIS POMIARU** — ale data stoi w komentarzu `#:` („Zmierzone 10.09.2026 na `a202423`") i w notacji polskiej |

`POMIARY_BRAKOW` jest więc zapisem pomiaru **niewidocznym dla każdego kryterium opartego
na dacie w literale, niezależnie od jej położenia**. Poszerzanie wzorca o kształty B i D
tego nie naprawia i nigdy nie naprawi.

## 6. Reguły „przebiegi kontra tablica przypadków" postawić się NIE DA

Przeszukane cechy **czytelne z kodu**, nie z prozy:

| kandydat | bilans |
|---|---|
| data ISO na pozycji `[0]` | 3/3 — ale to jest to samo założenie o kształcie, które pozycja podważa |
| `max()`/`min()`/indeks porządkowy nad listą | 3/3 — ale **tautologiczne** wobec szukanej różnicy |
| liczność przypięta **podłogą**, nie równością | **fałsz w tym samym module** |
| wolne pole prozy porównywane ze źródłem zewnętrznym | `POMIARY_BRAKOW` też je ma (klucz musi stać w README) |
| liczebnik w nazwie (`SZESC_`) | `POMIARY_BRAKOW` go nie nosi, a jest zamknięta |

**Kontrprzykład dla „zapis przebiegów ⇒ podłoga" leży w tym samym pliku:**
`POMIARY_RUNNERA_11_09` i `POMIARY_KONTENERA_JEDNO_DRZEWO` **są zapisami przebiegów** —
te same krotki, te same daty, ta sama proza — a stoją przypięte **równością**, i to
świadomie: „Rownosc, bo dzien sie skonczyl."

Rozstrzyga więc nie **gatunek listy**, tylko **czy zbiór został odcięty datą** — a tę oś
drzewo już nazywa, w `OPISY_Z_RANGA_DOZWOLONA`: „Ranga ograniczona mówi o zbiorze
ZAMKNIĘTYM […] albo jest odcięta datą […] Ranga otwarta mówi »najwyższy z tej listy«".
Reguła, której pozycja szukała, **istnieje od 6.D163 i jest o czym innym, niż pozycja
zakładała**: nie o rodzaju listy, tylko o domknięciu zbioru.

Granica mocy tego wniosku, wypisana: przy **jednym** zapisie przebiegów i **dwóch**
tablicach każda z powyższych cech rozdziela trywialnie, więc materiał nie odróżnia
kandydatów od siebie. Pewne jest tylko obalenie — kontrprzykład wystarcza jeden.

## 7. Co weszło do drzewa

- `test_ile_ksztaltow_zapisu_pomiaru_niesie_drzewo` — skan po całym `tools/`, dwie liczby
  (**7** stałych, **3** kontenery), rozkład kształtów i granica z §5.
- `test_klasyfikator_ksztaltow_TRAFIA_W_KAZDY_Z_PIECIU` — **kontrola przyrządu na
  wejściu syntetycznym**, bez której „zero" nic nie znaczy: klasyfikator niewidzący
  kształtu B odpowiedziałby na niego zerem tak samo, jak klasyfikator widzący (rodzina
  6.D159). Plus dwa literały, na które ma **milczeć** (bez daty, data w notacji PL).

## 8. Osiem kontroli negatywnych, baza 67/67 — i DWIE wyszły ZIELONE

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | klasyfikator ślepy na kształt B | 66/67 |
| KN-2 | nowa lista kształtu C w cudzym module | 66/67 |
| KN-3 | nowa lista kształtu B — którego drzewo NIE MA | 66/67 |
| KN-4 | skan zawężony do katalogu bez ani jednej listy | 66/67 |
| KN-5 | granica zdjęta (pętla po pustym słowniku) | **67/67 ZIELONA** |
| KN-5b | to samo po pierwszej poprawce | **67/67 ZIELONA** |
| KN-5c | to samo po drugiej poprawce | 66/67 |
| KN-6 | `SZESC_PRZYPADKOW` dostaje datę ISO w literale | 66/67 |
| KN-7 | słownik graniczny opróżniony | 66/67 |

**KN-5 i KN-5b są tu najważniejsze, bo obie wskazały dziurę w mojej własnej bramce.**

KN-5: granica była **prozą w przebraniu asercji** — pętla „dla każdej nazwy sprawdź, że
skan jej nie widzi" wykonuje się **zero razy** po opróżnieniu słownika i przechodzi.
Poprawka: równość na liczbie pozycji plus sprawdzenie **wobec drzewa**, że każda
wymieniona stała tam naprawdę stoi i naprawdę nie niesie daty.

KN-5b: ta sama kontrola **znowu zielona**, bo równość pilnuje **słownika**, a podstawienie
oślepia **pętlę** — dokładnie rodzina `Take(0)` z 6.D188, gdzie asercja na długości listy
nie broniła liczby obrotów. Poprawka: jawny licznik obrotów. KN-5c pokazuje, że dopiero
on zamyka obie drogi:

```
FAIL … pętla granic wykonała 0 obrotów przy 2 wymienionych — pusta pętla przechodzi
     każdą asercję w środku, więc bez tego licznika granica jest prozą w przebraniu
     asercji (zmierzone: KN-5b wyszła ZIELONA)
```

**KN-4 warto przeczytać obok KN-1**: zawężenie skanu do katalogu bez list daje `0 przy
zapadce 7`, czyli bramka na liczbie łapie oślepienie ZAKRESU — ale kształtu, którego
klasyfikator nie umie zobaczyć, nie złapałaby nigdy. Te dwie kontrole pilnują dwóch
różnych rzeczy i żadna nie zastępuje drugiej.

## 9. Czego świadomie nie zrobiłem

- **`POMIARY` i wartości pomiarów nietknięte**, progu nie ruszałem — pole „Poza zakresem".
- **Tablic przypadków nie przenosiłem do innego kształtu**, żeby pasowały do wzorca — to
  samo pole, i byłoby to dopasowywanie drzewa do sita zamiast odwrotnie.
- **Sita nie poszerzyłem o datę z komentarza `#:`**, choć to ona czyni `POMIARY_BRAKOW`
  niewidocznym. Komentarz nie jest literałem, a skan czytający komentarze odpowiadałby
  na inne pytanie niż „jaki kształt ma zapis". Granica jest zapisana zamiast obejścia.

## 10. Zauważone po drodze, nie tknięte

- **`NOTATIONS` z `test_report_hygiene.py` weszło do wyniku i jest kształtem C** — słownik
  dwóch notacji daty, gdzie data w kluczu jest **próbką formatu**, nie zapisem wykonania.
  Stary skan go nie widział, nowy widzi i klasyfikuje; że nie jest zapisem przebiegów,
  wiadomo z jego komentarza, a nie z kształtu — czyli dokładnie tam, gdzie §6 mówi, że
  reguły nie ma.
- **`AS_OF` w `test_stations.py` nie ma nad sobą komentarza `#:`** i jest jedynym skalarem
  z datą, o którym nic nie wiadomo bez czytania użyć. Nie tknąłem: cudzy moduł.
