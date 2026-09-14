# 6.D206 — jeden kontener na dwadzieścia dziewięć, czyli granica jest sitem

**14.09.2026**, na `71db020`. Wejście: `tools/tests/test_suite_runtime_budget.py`
(`_ksztalt_literalu`, `stale_z_data_iso`, `STALE_BEZ_DATY_W_LITERALE`),
`tools/tests/test_readme_claims.py` (`POMIARY_BRAKOW`),
`reports/6d193-zdanie-trafione-a-nie-sprawdzone.md`.

## 1. Odpowiedź: `POMIARY_BRAKOW` nie jest wyjątkiem — wyjątkiem jest `POMIARY`

Pole „Czego NIE wolno zrobić bez pomiaru" ostrzegało przed przyjęciem, że
`POMIARY_BRAKOW` jest wyjątkiem jednym: *„jeden przypadek jest anegdotą; dopiero
liczba mówi, czy kryterium daty w literale jest sitem z dziurą, czy sitem z jedną
szczeliną"*. Liczba mówi **trzecią rzecz**, której żadne z tych dwóch określeń nie
przewidywało.

| | |
|---|---:|
| stałych modułowych pod `tools/` o nazwie WIELKIMI | 1191 |
| z nich z komentarzem `#:` | 555 |
| z nich `#:` mówi „zmierzone"/„zmierzono" | 119 |
| z nich komentarz niesie **także datę** | **91** |
| z tych 91 literał **nie** niesie daty ISO | **89** |
| z tych 91 to **kontenery** (jedyne, którym kształt przysługuje) | **29** |
| z tych 29 literał **nie** niesie daty ISO | **28** |

Kryterium daty w literale widzi **jeden kontener na dwadzieścia dziewięć**. Drugi
i ostatni zapis z datą ISO w literale to `DZIEN_PIERWSZEGO_WYNOSZENIA` — skalar,
który **jest** datą, więc kontenerem nie jest i kształt mu nie przysługuje.

**Granica z 6.D193 nie jest więc szczeliną w sicie. Jest kształtem całego sita.**

## 2. Rozstrzygnięcie: granica zostaje granicą, bramki z niej NIE MA

Pole „Wyjście" żądało wyboru: *„czy granica zostaje zapisana jako granica, czy urasta
do osobnej bramki"*. Odpowiedź wychodzi z liczby z sekcji 1, a nie z ostrożności:
bramka „komentarz deklaruje pomiar, a literał daty nie niesie" zapalałaby się na
**89 stałych napisanych poprawnie**. Próg, zapadka i tablica przypadków nie mają gdzie
nosić daty i nosić jej nie powinny. Bramka świecąca na poprawnym tekście zostaje
wyłączona, nie poprawiona (6.D27) — więc jej tu nie ma.

**Pilnowane jest co innego, i to się da pilnować: ZBIÓR** stałych, które datę ISO
w literale niosą, przypięty z nazwy w `Z_DATA_ISO_W_LITERALE`. Zbiór, a nie liczba
(6.D131): liczba 91 rośnie przy każdej nowej stałej z datowanym komentarzem, czyli
przy pracy poprawnej, a zbiór dwóch nazw zmienia się **tylko** wtedy, gdy ktoś nowy
przyjmie kształt `POMIARY` albo gdy `POMIARY` go porzuci — i jedno, i drugie zmienia
rozstrzygnięcie tej pozycji.

Obie populacje mają dodatkowo **podłogi**, nie równości (`MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU
= 80`, `MIN_KONTENEROW_Z_POMIAREM_W_KOMENTARZU = 25`). Bronią przed jedną rzeczą:
skanem, który oślepł i odpowiada zerem tak samo jak skan widzący.

## 3. Pomiar zmienił się przez to, że został zapisany — i to jest w kodzie

Po tym commicie szeroka liczba wynosi **92**, nie 91: komentarz `#:` nad
`MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU` sam deklaruje pomiar z datą, więc wchodzi do
populacji, którą opisuje. Ta sama mechanika co `ADRESOW_W_WYKONANYCH` z 6.D158, gdzie
domknięcie pozycji przenosi jej własny blok do zbioru mierzonego.

**Liczba, na której stoi rozstrzygnięcie, nie drgnęła:** kontenerów jest nadal **29**,
bo obie nowe stałe są skalarami. Samozwrotność przesunęła populację szeroką i nie
ruszyła wąskiej — a wyrok zapada na wąskiej. Oba warianty stoją w komentarzu obok
siebie; przy 6.D203 tego samego dnia to samo zjawisko rozwiązałem wykluczeniem modułu
z własnej populacji, i tam było to słuszne (liczba **była** wąską), a tutaj nie jest.

## 4. Czego skan NIE robi — granica przyrządu, zapisana

- **Czyta wyłącznie blok `#:` stojący BEZPOŚREDNIO nad przypisaniem.** Zdanie o pomiarze
  w docstringu modułu, w zwykłym `#` albo w komentarzu oddzielonym pustym wierszem do
  populacji nie wchodzi. Jest to ta sama granica, którą 6.D193 zapisało zamiast obchodzić:
  komentarz nie jest literałem, a `#:` jest w tym drzewie konwencją zapisu przy stałej.
- **Wymaga zarówno deklaracji pomiaru, jak i daty.** Sito po samej dacie zgłaszałoby
  każdą listę, której proza wspomina dzień; sito po samym słowie „zmierzone" — 119 stałych,
  z których 28 daty nie podaje wcale.
- **Nie rozstrzyga, czy stała JEST zapisem pomiaru.** Odpowiada na pytanie węższe i
  sprawdzalne: czy jej komentarz to **deklaruje**.

## 5. Kontrole negatywne

Baza modułu: **34/34**. Po każdej `md5sum -c` na obu plikach: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | przyrząd oślepiony na datę w notacji polskiej | **32/34**, populacja 92 → **1** |
| KN-2 | `POMIARY_BRAKOW` dostaje datę ISO w literale | 32/34, zbiór rośnie do trzech |
| KN-3 | `POMIARY` traci datę z literału pierwszej krotki | 33/34, zbiór maleje do jednego |
| KN-4 | **92 → 93** po dopisaniu daty do komentarza stałej `GRANIC_SITA_DATY` | stała wchodzi do populacji |

**KN-4 jest tą kontrolą, o którą prosiło pole „Weryfikacja"** — „stała z datą dopisaną
do komentarza **wchodzi** do tej liczby". Nie jest czerwienią, bo obie populacje są
przypięte **podłogą**, a podłoga na wzrost nie reaguje; jest pomiarem liczby przed
i po, wykonanym na drzewie.

**KN-2 był raz spartaczony i to jest zapisane.** Pierwsza wersja wstawiła do literału
`POMIARY_BRAKOW` **krotkę**, a to jest słownik — moduł przestał się parsować, bramka
kształtów zgłosiła `invalid syntax`, a mój test wypisał „`POMIARY_BRAKOW` wypadło
z populacji", co było prawdą o zepsutym pliku, nie o zmianie. Powtórzone jako wpis
słownikowy, z `ast.parse` **przed** przebiegiem. Ta sama usterka, którą tego samego
dnia popełniłem przy 6.D204 (KN-8).

## 6. Czego świadomie nie zrobiłem

- **`POMIARY_BRAKOW` ani żadnego innego zapisu pomiaru nie ruszyłem** — pole „Poza
  zakresem".
- **Nie przeniosłem żadnej daty z komentarza do literału**, żeby pasowała do sita (to
  samo pole). Pomiar pokazuje, że musiałbym to zrobić 89 razy, żeby sito zaczęło opisywać
  drzewo — czyli przepisać drzewo pod przyrząd.
- **Nie poszerzyłem `_ksztalt_literalu`** (to samo pole). Nowy skan stoi obok, czyta
  komentarze i nie dotyka klasyfikatora kształtów ani jego zapadek.
- **Nie postawiłem bramki na liczbie 92 ani 29.** Obie rosną przy poprawnej pracy;
  przypięte są podłogami, a rozstrzygnięcie trzyma zbiór dwóch nazw.

## 7. Zauważone, nie tknięte

- **119 stałych ma `#:` mówiący „zmierzone", a 28 z nich nie podaje daty wcale.**
  Zdanie „zmierzone" bez dnia jest zapisem, którego nie da się zestarzeć ani odświeżyć,
  bo nie wiadomo, względem czego. Ta pozycja ich nie dotyka — mierzyła przecięcie
  z datą — ale liczba 28 stoi tu zapisana, bo nigdzie indziej jej nie ma.
- **`stale_z_data_iso()` znajduje 7 stałych z datą ISO w literale, a tylko 2 z nich
  mają `#:` deklarujący pomiar.** Pozostałe pięć to widoki `POMIARY`, `AS_OF`,
  `NOTATIONS` i `OPISY_Z_RANGA_DOZWOLONA` — data w literale nie jest więc nawet
  wskaźnikiem tego, że stała jest zapisem pomiaru.
- **`WZORZEC_ZAPADEK` w `test_prose_counts.py` żąda formy „N WOLNE", a po liczebniku 27
  poprawna jest „WOLNYCH".** Podniesienie rejestru z 46 na 48 zapadek wymagało więc
  napisania zdania niepoprawnego po polsku: sprawdzone wykonaniem — `7/7` przy „WOLNE",
  `6/7` przy „WOLNYCH", z komunikatem „zdanie nie zostało znalezione (trafień: 0)".
  Bramka świeci na poprawnym tekście, a obejście jest tanie, więc usterka utrwala się
  po cichu przy każdym podniesieniu. Wpisane jako **6.D218**; tej pozycji nie dotyczy.
- **Blok `#:` oddzielony od stałej pustym wierszem jest dla tego skanu niewidzialny.**
  Ile takich jest, nie sprawdzałem; konwencja drzewa mówi „bezpośrednio nad", ale nic
  jej nie pilnuje.
