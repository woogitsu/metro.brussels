# 6.D164 — materiału jest sto cztery przebiegi, ale okno jest ruchome

**13.09.2026**, na `a5e9ff0`. Wejście: `.github/workflows/python-tests.yml` (krok
wynoszący artefakt), `tools/ci/timing_record.py`, `tools/tests/test_timing_record.py`,
API artefaktów repozytorium.

## 1. Ile materiału — co najmniej 104 przebiegi

Zmierzone na **żywych** artefaktach, przez API repozytorium:

| przebieg | artefakt utworzony | wygasa | stan |
|---|---|---|---|
| 1213 (11.09.2026 12:36, PR #524) | 11.09 12:42:31 | 11.10 12:42:28 | `expired: false` |
| 1315 (13.09.2026 03:07) | 13.09 03:16:26 | 13.10 03:16:24 | 2123 bajty |

Ostatni przebieg tego workflowa ma numer **1316**, a przebieg 1213 ma artefakt żywy —
czyli **104 przebiegi w przedziale domkniętym**, każdy z krokiem `if: always()`, więc
także te czerwone. Materiał jest, i to nie jest ślad jednego przebiegu.

**Dlaczego „co najmniej", a nie dokładnie.** Wynoszenie zaczęło się 10.09, a numeru
pierwszego przebiegu po tej dacie nie odczytałem: API tego serwera nie filtruje
przebiegów ani po dacie, ani po commicie, więc jedyną drogą byłoby przejście listy
1316 przebiegów, z których każdy niesie pełną treść commita. Liczba dokładna
kosztowałaby wielokrotnie więcej niż odpowiedź, której pozycja potrzebuje, a dolna
granica na nią wystarcza. Granica jest tu **wypisana, nie przemilczana**.

## 2. Zasięg wstecz — i dlaczego dziś nic nie wygasło

| | |
|---|---|
| krok wynoszący wszedł do workflowa | **10.09.2026** (`9784e3b`, 6.D93) |
| retencja zadeklarowana w workflowie | **30 dni** |
| retencja zmierzona na dwóch artefaktach | **30 dni** co do dwóch sekund |
| pierwsze wygaśnięcie | **10.10.2026** |

Wcześniej niż 10.09 nie ma czego szukać — nic się nie wynosiło. Nic dziś nie wygasło
**i wygasnąć nie mogło**, bo wynoszenie trwa krócej niż retencja. Test wykonuje tę
nierówność, zamiast ją opowiadać: gdy liczba dni wynoszenia przekroczy retencję,
zdanie „nic nie wygasło" przestanie być prawdziwe i bramka każe przepisać docstring.

Deklaracja i zachowanie API **zgadzają się**, więc retencję wolno czytać z drzewa —
i bramka ją stamtąd czyta, zamiast nosić drugą kopię liczby.

## 3. Rozstrzygnięcie: materiał na trend TAK, ale ruchomy

Artefakt niesie czasy **per moduł**, `commit`, `runner`, `workflow` i podział
`odkryte`/`wykonane` — wszystko to, czego z logu wyjąć się nie da, bo log podaje same
sumy. Na trend to wystarcza z nadmiarem.

**Ale okno jest ruchome, i to jest cała odpowiedź.** Od 10.10.2026 przestanie rosnąć
i zacznie się przesuwać. Trend zbudowany na artefaktach **nigdy nie sięgnie dalej niż
trzydzieści dni wstecz**.

**Co z tego wynika dla `POMIARY`** — pytanie z pola „Skończone, gdy". Lista zostaje
i artefakt jej nie zastąpi, bo zapisuje co innego: `POMIARY` jest **trwałe** (wpis
z 05.09.2026 stoi w niej do dziś i będzie stał), artefakt **wygasa**. To, co ma
przeżyć dłużej niż miesiąc, musi zostać **zżęte do drzewa przed wygaśnięciem** — tak
jak sześć logów w `tests/data/ci-logs/`, które właśnie dlatego tam leżą. Te sześć
logów jest z 11.09, więc ich artefakty wygasną 11.10; w drzewie zostaną.

Czytnika artefaktów ta pozycja **nie pisze**: pole „Poza zakresem" zabrania zmiany
kroku CI i dopisywania wpisów automatem, a pytanie brzmiało, czy materiał jest.

## 4. Kontrole negatywne

Baza: **12/12**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK` na obu plikach.
Przed każdym przebiegiem czyszczony `__pycache__`; po każdym podstawieniu `diff`
z kopią roboczą i `assert` na jednym wystąpieniu.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | retencja w workflowie obniżona do 7 dni | **11/12** | zasięg czytany z drzewa, nie wpisany |
| KN-2 | artefakt zmienia nazwę | **11/12** | bramka szuka kroku, a nie wierzy, że jest |
| KN-3 | krok traci `if: always()` | **10/12** | zapala też bramkę z 6.D93 |
| KN-4 | zmierzona retencja przestawiona | **11/12** | dwa źródła są porównywane, nie jedno |

KN-3 jest tu najciekawsza: zapala **dwie** bramki naraz — nową i tę, którą 6.D93
postawiło przy tym samym kroku. Przebieg czerwony jest tym, którego czasy są
najbardziej potrzebne, więc obie pilnują tego samego z dwóch stron.

## 5. Czego nie zrobiono

- **Nie napisano czytnika artefaktów** — „Poza zakresem", i pytanie pozycji brzmiało,
  czy materiał jest, a nie co z nim zrobić.
- **Nie zmieniono kroku CI ani retencji** — „Poza zakresem".
- **Nie dopisywano wpisów `POMIARY` automatem** — „Poza zakresem", i 6.D152 już
  rozstrzygnęło, że o wejściu pomiaru do listy decyduje człowiek.
- **Nie odczytano dokładnej liczby artefaktów** — powód i koszt w punkcie 1.

## 6. Co zauważone przy okazji, nietknięte

Retencja artefaktów jest w tym repozytorium **zróżnicowana i nigdzie nie uzasadniona**:
30 dni dla czasu zestawu, po 14 dla pięciu workflowów, po 7 dla dwóch. Liczby są
zadeklarowane w każdym workflowie osobno, więc nie rozjadą się po cichu — ale nic nie
mówi, **dlaczego** akurat tak, ani czy 7 dni wystarcza na cokolwiek. Przy artefakcie
czasu 30 dni ma teraz zapisany sens (to jest zasięg trendu); przy pozostałych ośmiu
nie ma żadnego.
