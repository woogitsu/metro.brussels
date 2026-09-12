# 6.D53 — rejestr opisuje dwie końcówki OSM z liczbami, a nie dwoma słowami

**12.09.2026**, na `3263966`. Wejście: `data/network/sources.json` (wpis `openstreetmap`),
`docs/07-open-data-research.md` („Dwie drogi do OSM"),
`tools/track/crosscheck_alignment.py`, `tools/tests/test_osm_api_fallback.py`,
`reports/osm-api-droga-zapasowa.md`.
Zapis do `data/` uprawniony **decyzją właściciela z 10.09.2026**, dotyczącą tej jednej
pozycji i tego jednego pliku.

## 1. Co rejestr mówił, a czego nie

```json
"access": { "type": "osm_or_overpass", "authentication": "endpoint-dependent" }
```

Dwa słowa: „dróg jest dwie" i „uwierzytelnienie zależy od końcówki". **Żadnej liczby.**
Nie było `url` żadnej z nich, nie było limitu obszaru, nie było nawet tego, że jedna
z dwóch dróg filtruje po stronie serwera, a druga nie — a to jest różnica, przez którą
ta sama odpowiedź waży **66,1 MB zamiast kilkuset kilobajtów**.

Skutek był konkretny i stał w kodzie: `OSM_API_NODE_LIMIT = 50000` w
`tools/track/crosscheck_alignment.py`. **Liczba o źródle mieszkała w narzędziu, a nie
w rejestrze źródeł** — czyli tam, gdzie nikt jej nie szuka, czytając o źródłach.

## 2. Co rejestr mówi dziś

`access.endpoints` — lista dwóch końcówek, każda z `url`, `role`, `authentication`,
`server_side_filter`, limitem i datą pomiaru:

| | `overpass` | `osm-api` |
|---|---|---|
| `role` | **primary** | **fallback** |
| `url` | `overpass-api.de/api/interpreter` | `api.openstreetmap.org/api/0.6/map` |
| `server_side_filter` | **true** | **false** |
| `query_language` | `Overpass QL` | `null` |
| `node_limit_per_call` | `null` **+ zdanie, dlaczego** | **50000** |
| `timeout_s` | 60 | — |
| `base_timestamp_field` | `osm3s.timestamp_osm_base` | `null` |

**`null` u Overpassa nie stoi samo.** Pole bez wartości jest nieodróżnialne od pola,
którego nikt nie wypełnił, więc obok stoi `node_limit_note`: limitu węzłów nie ma, bo
filtr wykonuje serwer, więc rozmiar odpowiedzi zależy od zapytania, a nie od prostokąta.
Nieobecność jest tu **zdaniem**, a bramka tego zdania wymaga.

Dwa stare słowa zostały na miejscu — czytniki sprzed tej pozycji czytają `access.type`
i nie mają się wywrócić. Rozstrzyga lista.

## 3. Strażnik dwóch liczb o jednym fakcie

`OSM_API_NODE_LIMIT` **zostaje w kodzie**, i to jest decyzja, nie zaniechanie: narzędzie
musi rozpoznać `HTTP 400` jako „kafel za duży", także gdy rejestru nie ma pod ręką —
przy przebiegu z kopii, z kafla w pamięci podręcznej, z innego drzewa. Dwie liczby o tym
samym fakcie są więc świadome i **dlatego mają strażnika**.

`pary_rejestr_kod()` zestawia **sześć** par, a wypis pokazuje obie strony każdej:

```
$ python3 -c "import sys; sys.path.insert(0,'tools/track'); import crosscheck_alignment as X; print(*X.wiersze_limitow(), sep=chr(10))"
[LIMIT] osm-api: węzłów na wywołanie: rejestr 50000, kod 50000 (zgodne)
[LIMIT] osm-api: url: rejestr 'https://api.openstreetmap.org/api/0.6/map', kod 'https://api.openstreetmap.org/api/0.6/map' (zgodne)
[LIMIT] overpass: timeout zapytania [s]: rejestr 60, kod 60 (zgodne)
[LIMIT] overpass: url: rejestr 'https://overpass-api.de/api/interpreter', kod 'https://overpass-api.de/api/interpreter' (zgodne)
[LIMIT] overpass: filtr po stronie serwera: rejestr True, kod True (zgodne)
[LIMIT] osm-api: filtr po stronie serwera: rejestr False, kod False (zgodne)
```

Pole „Weryfikacja" pozycji żądało **dwóch liczb obok siebie, a nie zdania, że się
zgadzają** — i to jest powód tego kształtu: zdanie „zgadza się" wygląda identycznie przy
liczbach zgodnych i przy rozjechanych.

### Pierwsza wersja tego wypisu porównywała dwie nieobecności

Dla Overpassa wypisywała `rejestr None, kod None (zgodne)` — porównanie dwóch braków,
czyli zdanie prawdziwe **zawsze**. Zostało przepisane, a nie obudowane: parą Overpassa
jest dziś `timeout_s` z rejestru wobec `[timeout:60]` **wyjętego z `OVERPASS_TEMPLATE`**,
a parą „filtr po stronie serwera" — obecność nazwy taga w szablonie zapytania wobec jej
braku w `OSM_API_QUERY_FMT`. Sześć par, w każdej obie strony pochodzą z czegoś, co
naprawdę może się zmienić. Osobna asercja pilnuje, żeby żadna para nie zestawiała
`None` z `None`.

## 4. Kontrole negatywne

Baza `test_osm_api_fallback.py`: **33/33** (przed pozycją 28). Kontrole dotykające
`data/` wykonane **na kopii drzewa** w `/tmp` (48 MB), nie w miejscu — zgoda właściciela
obejmuje zapis do rejestru w ramach tej pozycji, ale kontrola negatywna to nie jest jej
treść. Po każdej przywrócenie i `md5sum` zgodny z drzewem roboczym; `__pycache__`
czyszczony przed każdym przebiegiem.

| | co psuje | gdzie | wynik | co zapaliło |
|---|---|---|---|---|
| KN-1 | `node_limit_per_call` 50000 → 49999 | kopia drzewa | 30/33 | para rejestr↔kod **i** wypis, oba nazywają obie liczby |
| KN-2 | `access` wraca do dwóch słów | kopia drzewa | **29/33** | czytelnik odmawia, trzy bramki |
| KN-3 | `len(wpisy) != 1` → `< 1` | kod | **33/33 ZIELONE** | **nic — patrz niżej** |
| KN-3b | to samo po dołożeniu wejścia syntetycznego | kod | 32/33 | odmowa przy dwóch wpisach OSM |
| KN-4 | `OSM_API_NODE_LIMIT` → 50001 | kod | 30/33 | para rejestr↔kod **i** wypis |
| KN-5 | `z_rejestru == z_kodu` → `!=` w wypisie | kod | 32/33 | kontrola przyrządu wypisu |
| KN-6 | obie końcówki dostają `server_side_filter: true` | kopia drzewa | 30/33 | bramka rozróżnienia dróg |
| KN-7 | `w["id"] == "openstreetmap"` → `!=` | kod | **28/33** | pięć bramek |

### KN-3 wyszła ZIELONA i to jest najważniejszy wynik tej pozycji

Warunek `len(wpisy) != 1` w `koncowki_osm_z_rejestru` przepuszczał mutację na `< 1`
**bez jednego czerwonego testu**. Powód jest ten sam, co przy 6.D147, 6.D148 i 6.D149
(pozycja 6.D161): rejestr ma dziś dokładnie jeden wpis `openstreetmap`, więc gałąź
„wpisów jest kilka" nie była wykonywana przez nic — mechanizm poprawny, któremu żadne
wejście z drzewa nie odróżnia obecności od braku.

Dwa wpisy o tym samym `id` nie są scenariuszem teoretycznym: `sources` jest **listą**,
a nie słownikiem, więc powstają przez zwykłe rozwiązanie konfliktu scalania. Czytelnik
brałby wtedy pierwszy i milczał — a drugi mógłby nieść inny limit.

Dołożone wejście syntetyczne (`test_czytelnik_rejestru_ODMAWIA_gdy_wpisow_OSM_jest_wiecej_niz_jeden`)
duplikuje wpis w rejestrze probnym i żąda odmowy **z liczbą**, bo „coś nie tak z wpisem"
nie mówi, czy jest ich zero, czy dwa. KN-3b jest po tym czerwona.

**Różnica wobec trzech poprzednich razy:** tam wejście syntetyczne dokładałem po tym, jak
kontrola wyszła zielona, i to samo robię tutaj — ale tym razem zielona kontrola nie była
niespodzianką w mechanizmie cudzym, tylko w kodzie napisanym pół godziny wcześniej.
Reguła z tego jest prosta i trafia do raportu, a nie do dokumentu: **każdy nowy warunek
strażniczy potrzebuje wejścia, które go wykonuje, w tym samym commicie.**

## 5. Cztery nowe punkty mutacji, wszystkie z kontrolą

`reports/mutation-drift.md` liczy dla tego modułu **31 → 35**. Przyrost jest wymieniony
imiennie, bo liczba bez nazw nie pozwala sprawdzić, czy to, co doszło, jest tym, co się
dopisało:

| punkt | klasa | kontrola |
|---|---|---|
| `w["id"] == "openstreetmap"` | operator | KN-7 |
| `len(wpisy) != 1` | operator | KN-3b |
| `len(wpisy) != 1` | próg | KN-3b |
| `z_rejestru == z_kodu` | operator | KN-5 |

Kolumna ocalałych w audycie **nieprzeliczona** i taka zostaje — to pomiar z datą, którego
dopisanie kodu nie unieważnia; ta sama zasada, co przy 6.B52 i 6.D62 w tym samym wierszu.

## 6. Przepisane, nie dopisane obok

`docs/07-open-data-research.md` mówiło: *„czego rejestr nie zapisuje, to limity anonimowe
tej konkretnej końcówki i to jest zgłoszone jako osobna pozycja kolejki, a nie poprawione
tutaj (`data/` jest tylko do odczytu)"*. Tą pozycją była **ta** pozycja, więc zdanie jest
dziś nieprawdziwe i zostało zastąpione opisem tego, co rejestr niesie — razem z powodem,
dla którego limit stoi w dwóch miejscach, i z poleceniem wypisującym pary.

## 7. Czego nie zrobiono

- **Nie ruszyłem hierarchii źródeł** — OSM zostaje klasą 4, poniżej STIB i Regionu
  („Poza zakresem" pozycji). Bramka `test_the_source_doc_keeps_osm_below_the_official_sources`
  przechodzi bez zmian.
- **Nie dopisałem kluczy API ani nie zmieniłem `access.authentication`** — oba w „Poza
  zakresem". Obie końcówki mają `"authentication": "none"` jako **fakt o końcówce**;
  napis `endpoint-dependent` na poziomie wyżej został nietknięty.
- **Nie ruszyłem `checked_at`** wpisu (`2026-08-31`). Nie sprawdzałem dziś źródła —
  wstawiłem liczby zmierzone 08.09.2026 i **każda końcówka niesie własne `measured_at`
  z tą datą**. Podniesienie `checked_at` byłoby zadeklarowaniem kontroli, której nie było.
- **Nie pobrałem niczego do `data/`** („Poza zakresem"); żaden test tej pozycji nie
  rusza sieci.
- **Nie przeniosłem `OSM_API_TILE_DEG` do rejestru.** Bok kafla jest NASZĄ nastawą
  wyprowadzoną z cudzego limitu, a nie faktem o źródle; rejestr opisuje źródła.
