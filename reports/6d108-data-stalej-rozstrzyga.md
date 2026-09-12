# 6.D108 — o tym, czy raport mówi o dziś, rozstrzyga data stałej w gicie, nie kształt zdania

**12.09.2026**, na `b629d36`. Wejście: `tools/tests/test_report_claims.py`
(`CLAIM`, `CLAIM_EXCEPTIONS`), `.github/workflows/*.yml`,
`reports/6d108-ksztaltu-nie-ma.md`. Mechanizm wybrany **decyzją właściciela
z 10.09.2026**: data ostatniej zmiany stałej z gita **wraz z `fetch-depth: 0`**
w workflowach. Wariantów „data z nagłówka raportu" i „kierunek zapadki" nie realizuje nic.

## 1. Co było nie tak

Bramka czytała **każde** trafienie wzorca jako twierdzenie o wartości **bieżącej**,
więc podniesienie dowolnej zapadki zapalało ją na raportach opisujących stan swojego
dnia. Zdarzyło się to trzy razy w jednej sesji (10.09.2026): na strzałce `207 → 208`,
potem na zdaniu „stoi na 208" nazajutrz, potem na „stoi na 209" godzinę później.
Za każdym razem poprawką było **przepisanie liczby słownie** — czyli obchodzenie
bramki zamiast rozstrzygnięcia.

Pomiar z `reports/6d108-ksztaltu-nie-ma.md` powiedział, dlaczego obejście było jedynym
wyjściem: **kształtu nie ma**. Wszystkie zdania datowane wyglądały dokładnie tak, jak
zdanie o wartości bieżącej — bo w dniu napisania nim **były**. Informacja rozstrzygająca
leży poza zdaniem.

## 2. Co rozstrzyga dziś

Porządek dwóch dat. Raport jest zdaniem o dniu pomiaru **wtedy i tylko wtedy, gdy stała
zmieniła się PO tym, jak raport ostatnio tknięto**.

| data stałej | data raportu | werdykt |
|---|---|---|
| 11.09 | 10.09 | **przedawnione** — raport pisał o swoim dniu |
| 11.09 | 12.09 | pilnowane — raport młodszy, więc pisze o wartości bieżącej |
| 11.09 | 11.09 | **pilnowane** — raport tknięty razem ze stałą pisze właśnie o niej |

Trzeci wiersz jest tu treścią, nie przypadkiem granicznym: raport powstający w tym samym
commicie co podniesienie zapadki opisuje **nową** wartość.

## 3. Drzewo robocze rozstrzyga przed gitem — i to jest treść, nie optymalizacja

Bramka chodzi **przed** commitem. Gdyby data stałej szła wyłącznie z historii:

- podniesienie zapadki w drzewie wyglądałoby jak **brak zmiany**, więc bramka zapalałaby
  się dokładnie tam, gdzie ta pozycja każe jej milczeć — i jedynym wyjściem znów byłoby
  przepisanie liczby słownie;
- przepisanie liczby w raporcie na nieprawdziwą wyglądałoby jak **brak zmiany raportu**
  i przechodziłoby.

Dlatego stała o wartości innej w drzewie niż w `HEAD` dostaje datę `TERAZ`, raport
zmieniony w drzewie tak samo, a dwa `TERAZ` **nie są uporządkowane** — więc raport pisany
dziś o zapadce podnoszonej dziś musi podać nową wartość. Obie strony mierzy KN-6 i KN-7,
a złożenie obu — KN-2b.

Warunek na stałą jest koniunkcją: plik **tknięty** ORAZ wartość **inna niż w HEAD**.
Bez drugiego członu dowolna edycja pliku zwalniałaby z pilnowania wszystkie jego stałe.

## 4. Płytki klon: „nie wiadomo" to nie jest „dawno"

Zmierzone 12.09.2026 w kontenerze tej sesji: klon jest **płytki** — 252 commity od
`b019436` z 07.09.2026 — a `git log -G` dla stałej nietkniętej w tym oknie wskazuje
**commit graniczny**, nie tę zmianę, która naprawdę była ostatnia. Na **28** stałych
cytowanych wtedy w raportach **18 dostawało w ten sposób datę granicy**, czyli odpowiedź
„dalej nie widzę" podaną jako fakt.

Czytelnik odróżnia więc trzy stany, a nie dwa: **data**, **`TERAZ`** i **`None` = historia
tego nie pokazuje**. `None` nie zwalnia z pilnowania — twierdzenie jest wtedy traktowane
jak zdanie o wartości bieżącej, a komunikat mówi wprost, że sprawdzenia nie było.

Stąd druga połowa decyzji właściciela: **`fetch-depth: 0` we wszystkich dziesięciu
workflowach**. `actions/checkout` bez tego wejścia daje głębokość **1**, więc w CI
ślepota byłaby zupełna — każda stała wyglądałaby na zmienioną w jedynym widocznym
commicie. Bramka pilnująca tego stoi **w tym module**, nie tylko w
`test_ci_workflows.py`: kto zdejmie `fetch-depth`, ma zobaczyć nazwę przyrządu,
który przez to oślepł.

## 5. Ile to zmienia — zmierzone na dzisiejszym drzewie

```
miejsc twierdzeń: 33
zwolnionych przy podniesieniu ICH stałej: 33
pilnowanych mimo to: []
stałych różnych: 28
plików raportów: 18
```

Pole „Skończone, gdy" żądało, żeby podniesienie dowolnej zapadki nie zapalało bramki na
**żadnym** ze zmierzonych miejsc. Jest spełnione dla **33 z 33** — pozycja mówiła o 18
miejscach w 12 plikach, a późniejszy pomiar (`6d108-ksztaltu-nie-ma.md`) o 9 w 7;
dziś jest ich 33 w 18, bo raportów przybyło.

Dziś **przedawnionych jest zero**: wszystkie 33 twierdzenia zgadzają się z kodem
i wszystkie są pilnowane. Mechanizm nie zwalnia dziś niczego — zwalnia dopiero w chwili,
w której zapadka idzie w górę.

## 6. Kontrole negatywne

Baza `test_report_claims.py` + `test_ci_workflows.py`: **92/92** (przed pozycją 86).
Po każdej przywrócenie przez `cp` i `md5sum -c: OK`, `__pycache__` czyszczony przed
każdym przebiegiem.

| | co psuje | wynik | co zapaliło |
|---|---|---|---|
| KN-1 | `MINIMUM_READY_ITEMS` 12 → 13, raporty nietknięte | **92/92 ZIELONE** | **nic — i to jest odpowiedź pozycji** |
| KN-1b | to samo, ale z **wyłączonym datowaniem** | 91/92 | cztery twierdzenia o `MINIMUM_READY_ITEMS` |
| KN-2 | `BACKGROUND_TOLERANCE` 0,02 → 0,03 w raporcie | 91/92 | `[historia nie pokazuje…]` — pilnowane mimo braku daty |
| KN-2b | zapadka +1 **i** raport tknięty z nieprawdą | 91/92 | `[raport jest nie starszy od stałej]` |
| KN-4 | jeden workflow bez `fetch-depth: 0` | 91/92 | `fetch-depth=None` w `sim-tests.yml` |
| KN-5 | commit graniczny uchodzi za datę | 91/92 | kontrola przyrządu na wejściu syntetycznym |
| KN-6 | `data_stalej` bez gałęzi drzewa roboczego | 91/92 | zapadka podniesiona w drzewie nie dostaje `TERAZ` |
| KN-7 | `data_raportu` bez gałęzi drzewa roboczego | 91/92 | raport tknięty w drzewie przestaje być pilnowany |

### KN-1 jest zielona z założenia i dlatego stoi w parze z KN-1b

Zielona kontrola zwykle znaczy, że nic nie zostało zmierzone. Tutaj **zieleń jest
odpowiedzią**: pozycja pyta wprost, czy podniesienie zapadki przestało zapalać bramkę na
raportach datowanych. Żeby ta zieleń nie znaczyła „bramka oślepła", stoi obok niej
**KN-1b — ta sama mutacja z wyłączonym datowaniem**, czerwona. Para mierzy, że różnicę
robi mechanizm, a nie zanik pilnowania. Osobno pilnuje tego asercja
`checked - datowane >= MINIMUM_CLAIMS`: datowanie ma zwalniać zdania o dniu pomiaru,
a nie wygaszać bramkę.

### KN-2 pokazuje, jak wygląda odpowiedź bez wiedzy

`BACKGROUND_TOLERANCE` nie zmieniła się w widocznym oknie historii, więc jej data to
`None`. Twierdzenie **jest pilnowane**, a komunikat mówi dlaczego:
`[historia nie pokazuje, kiedy stała zmieniła się ostatnio (klon płytki albo commit
graniczny) — twierdzenie jest pilnowane jak zdanie o wartości bieżącej]`. To jest
różnica między bramką, która nie wie, a bramką, która nie wie i milczy.

## 7. Czego nie zrobiono

- **Nie zmieniłem wartości żadnej zapadki** ani nie przepisałem raportów historycznych na
  zapis słowny — oba w „Poza zakresem" pozycji. Zapisy słowne, które powstały jako
  obejście, **zostają**: są dziś poprawnym zdaniem, a przepisywanie ich z powrotem na
  cyfry byłoby ruszaniem raportów datowanych.
- **Nie tknąłem `CLAIM_EXCEPTIONS`.** Lista jest nadal pusta i o to chodziło: mechanizm
  miał rozstrzygać **po kształcie zjawiska**, a nie po liście wyjątków.
- **Nie zmierzyłem kosztu `fetch-depth: 0` w CI.** Workspace runnera jest trwały, więc
  pełną historię pobiera się raz; pierwszy przebieg po tej zmianie pokaże liczbę.
- **Nie zrobiłem odpowiednika dla `test_readme_claims.py`.** README opisuje stan bieżący,
  nie pomiar z datą, więc datowanie nie ma tam desygnatu — ale nikt tego nie zmierzył
  i dlatego jest to zapisane tutaj, a nie zrobione po cichu.
