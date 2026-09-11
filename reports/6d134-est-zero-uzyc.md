# 6.D134 — `est` ma zero użyć, ale pilnował tego jeden plik z dwudziestu

**11.09.2026**, na `52a6feb`. Pozycja pytała, czy zero użyć statusu `est` da się przybić
bramką bez fałszywego alarmu na dokumencie, który tę nazwę **definiuje**.

## 1. Czego wpis nie wiedział

Wpis mówił „nic go nie pilnuje w żadną stronę". To jest **pół prawdy**: asercja istnieje
od 6.D89 (`dd53c4e`), w teście `test_the_document_still_defines_the_four_classes_…`,
i brzmi `w_danych.get("est", 0) == 0`. Czyta jednak `klasy_w_danych()`, czyli **wyłącznie
`data/vehicle/m7-spec.json`**.

Pomiar: pole `status` stoi w **20 plikach JSON** pod `data/` i niesie **21 różnych
wartości**. Nazwa wycofana mogła więc wrócić w dowolnym z pozostałych **dziewiętnastu**
i nie zgłosiłoby tego nic.

## 2. Dlaczego nie „każdy status ma być klasą modelu"

Pozostałe pliki mają własne słowniki — praw, torów, stacji. Reguła „każdy status należy
do klas z `docs/02-simulation.md`" zapaliłaby się dziś na **16 z 20 plików** i **18
nazwach**: `ok`, `unknown`, `source_backed`, `permission_required`, `not_modelled`,
`conflict`, `indicative` i jedenaście innych. Liczby te nie stoją w prozie — osobna
asercja **wykonuje tamtą regułę** i żąda dokładnie 16 i 18, żeby zdanie „byłaby szumem"
nie stało się opinią.

Zakaz jest więc **imienny**: `ZAKAZANE_W_DANYCH = {"est": …}`, a druga bramka żąda, żeby
każda nazwa z tej listy była w dokumencie **zdefiniowana** — zakaz ma stać przy definicji,
nie zamiast niej.

## 3. Dlaczego to nie może być grep — pokazane liczbą

Gołe słowo `est` stoi w `data/` **7 razy w 4 plikach i wszystkie siedem to francuski**:

| plik | ile | co to |
|---|---|---|
| `data/network/sources.json` | 2 | adresy STIB `…-on-en-est-ou`, `…-m7-est-arrive-…` |
| `data/network/lines.json` | 1 | ten sam adres w polu `source` |
| `data/vehicle/m7-spec.json` | 1 | ten sam adres w polu `url` |
| `data/network/station-depths.csv` | 3 | cytat z EIE: «la profondeur des quais … **est** d'environ 11 m» |

Trafień prawdziwych: **zero**. Grep po samym słowie dałby siedem fałszywych alarmów
i ani jednego prawdziwego. Grep po **podciągu** — co pokazała KN-4 — daje **401 trafień
w 28 plikach**, wciąż zero prawdziwych.

W `docs/` `est` stoi pięć razy i każde jest uprawnione: `02-simulation.md` (definicja),
`21-measured-vs-assumed.md` (nazwanie klasy drugiej tabeli), `08-m7-ground-truth.md`
trzy razy (zapis historyczny: „To było oznaczone jako `est`").

## 4. Definicja ma być cicha — i to też jest zmierzone, nie wywnioskowane

Pierwsza wersja mojego testu twierdziła, że dokument nie wchodzi do skanu, **bo filtr
rozszerzeń przepuszcza tylko `.json`**. Uzasadnienie było niepełne i pokazały to
**dwie kontrole zielone**:

* **KN-5** — dopisanie `.md` do filtru: **14/14, nic się nie zmienia** (markdown i tak
  nie parsuje się jako JSON);
* **KN-5b** — czytnik tekstowy zamiast parsera: **14/14, też nic** (filtr rozszerzeń go
  nie wpuszcza).

Obrony są **dwie i każda wystarcza sama**. Dopiero **KN-5c**, zdejmująca obie naraz, jest
czerwona:

```
FAIL test_dokument_definiujacy_status_bramki_nie_zapala: skan obok danych zobaczył
     dokument DEFINIUJĄCY klasy: {'02-simulation.md': {'spec': 1, 'observed': 1,
     'est': 1, 'design_model': 1}, 'dane.json': {'spec': 1}}
```

Dokument wniósłby `est: 1` jako **użycie** — dokładnie ten fałszywy alarm, którego
pozycja kazała szukać. Test kładzie dziś prawdziwy dokument w drzewie probnym i pyta skan
wprost, zamiast wnioskować, które z dwóch zabezpieczeń zadziałało.

## 5. Kontrole negatywne

Baza `test_provenance_classes.py`: **14/14** (było 10). `__pycache__` czyszczony przed
każdym przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK`.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | skan czyta tylko plik pojazdu (stan sprzed) | **12/14**, dwa testy |
| KN-2 | `est` wstawione do danych (na **kopii** `data/`) | trafienie zgłoszone |
| KN-3 | lista zakazanych opróżniona | **12/14**, dwa testy |
| KN-4 | wzorzec słowa zamieniony na podciąg | **13/14**, 401 trafień w 28 plikach |
| KN-5 | filtr rozszerzeń wpuszcza `.md` | **14/14 ZIELONA** |
| KN-5b | czytnik tekstowy zamiast parsera | **14/14 ZIELONA** |
| KN-5c | obie obrony zdjęte naraz | **13/14** |
| KN-6 | dokument „zna" wszystkie statusy z danych | **10/14**, cztery testy |
| KN-7 | `os.walk` zamiast `TW.walk` | **14/14 ZIELONA** |

**KN-2 szła na kopii katalogu**, nie na `data/` — `CLAUDE.md` §4.6 mówi „tylko do
odczytu", a kontrola negatywna nie jest od tego wyjątkiem. `git status data/` po niej:
pusto.

**KN-7 zielona jest zgodna z pomiarem 6.D74**: pod `data/` nie ma gałęzi pominiętych
w `.gitignore`, więc odsianie nie zmienia dziś ani jednej liczby. `TW.walk` stoi tam,
bo tego żąda bramka z 6.D74 — jest regułą kształtu kodu, nie zmierzoną koniecznością
w tym miejscu.

## 6. Weryfikacja

```
  14/14 przeszło        test_provenance_classes.py   (było 10)
  2335/2335 przeszło, 122 moduły, KOD=0, RAZEM 170.042 s
```

`data/` nietknięte: `git status --short data/` pusty.

## 7. Czego nie zrobiłem

* **Nie zmieniłem klasyfikacji żadnego parametru i nie usunąłem `est` z dokumentu** —
  oba wprost w „Poza zakresem", oba są decyzją o modelu.
* **Nie objąłem zakazem żadnej innej nazwy.** `ZAKAZANE_W_DANYCH` ma jeden wpis, bo
  jeden status dokument opisuje jako „do usunięcia". Dopisanie tam czegokolwiek bez
  takiego zdania w dokumencie byłoby regułą bez źródła — i osobna bramka tego pilnuje.
* **Nie ruszyłem asercji z 6.D89.** Została tam, gdzie była: mówi o rozkładzie klas
  w pliku pojazdu (`{spec, design_model}`) i to jest zdanie węższe, nie duplikat.
* **Nie objąłem skanem plików innych niż JSON.** `station-depths.csv` niesie status
  `estimated` w kolumnie, ale to słownik głębokości stacji, nie provenance modelu jazdy;
  wciągnięcie go wymagałoby czytnika kolumn CSV i własnego pomiaru.
