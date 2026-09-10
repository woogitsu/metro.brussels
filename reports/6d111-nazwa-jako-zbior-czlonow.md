# 6.D111 — nazwa przystanku jako zbiór członów

**Zmierzone 10.09.2026 na:** `779ef0e`, kontener tej sesji.
**Przyrząd:** `tools/track/stop_names.py` (nowy), `tools/track/validate.py`
(`_is_subsequence`), `tools/track/build_alignment.py` (`normalise`,
`canonical_station_index`), `tools/track/vertical_profile.py`,
`tools/tests/test_network_declarations.py` (`_canonical`), `tools/tests/test_packages.py`,
`tools/tests/test_vertical_profile.py`; dane `data/network/lines.json`
i `data/network/stops.json` — wyłącznie do odczytu.

---

## 1. Pomiar, z którego wyprowadzony jest kształt

```
unikalnych przystanków: 60
z kreską pionową: 26
liczba członów: {2: 26, 1: 34}
ze spacją wokół kreski: 0
człony identyczne po normalizacji: 0
członów kanonicznych: 86
kolizji (jeden człon w dwóch stacjach): 0
```

Kolejność języków, zmierzona **wobec oficjalnego snapshotu GTFS**
(`data/network/stops.json`, pola `name_fr` i `name_nl`), a nie oceniona na oko:

```
fr pierwszy: 25   nl pierwszy: 1   nierozstrzygnięte: 0
   Kraainem|Crainhem
```

Z tego wychodzi kształt normalizacji, i każdy jego element ma tu swój wiersz:

| element | z czego wynika |
|---|---|
| nazwa to **zbiór** członów | członów bywa jeden albo dwa, a jeden człon opisuje tę samą stację |
| porównanie przez **przecięcie** | źródło zewnętrzne ma prawo podać jeden człon tam, gdzie `lines.json` ma dwa |
| **bez** wrażliwości na kolejność | kolejność języków nie jest jednolita — `Kraainem\|Crainhem` |
| człony **obcinane** ze spacji | spacja wokół kreski jest zmianą zapisu, nie faktu |
| liczba członów **nigdzie nie jest stałą** | trzeci człon byłby nadal tą samą stacją |

## 2. Warunek, na którym stoi przecięcie — pilnowany, nie założony

Przecięcie działa tylko dopóty, dopóki żaden człon nie należy do dwóch stacji.
Gdyby należał, dwie stacje sklejałyby się w jedną **po cichu** — sklejenie nie
zgłasza się nigdzie, a wszystkie kontrole kolejności przestałyby cokolwiek znaczyć.
Dziś kolizji jest zero na 86 członów i pilnuje tego osobny test, a nie komentarz.

Że ten test nie jest ozdobą, pokazuje KN-5: obcięcie członu kanonicznego do czterech
znaków daje natychmiast cztery kolizje, w tym trzy stacje pod kluczem `GARE`.

## 3. Były TRZY normalizacje, nie jedna, i różniły się apostrofem

`build_alignment.normalise` zostawiała apostrof w napisie (`GARE DE L'OUEST`),
a `_canonical` z `test_network_declarations.py` zamieniała go na spację
(`GARE DE L OUEST`). Trzecim „normalizatorem" były rozsiane po drzewie wywołania
`split("|")`, w tym `split("|")[0]` w `test_packages.py` — porównanie po **pierwszym**
członie, przy kolejności języków, która jednolita nie jest.

Żaden z tych rozjazdów niczego nie zapalał i **to jest właśnie usterka**: obie strony
każdego porównania czytają dziś ten sam plik. Rozjazd czekał na pierwsze źródło
zewnętrzne.

Dziś jedno miejsce liczy regułę, a pozostałe są cienkimi nakładkami na nie.

## 4. KN-6 i KN-3 wyszły ZIELONE

Dwa razy w tej pozycji kontrola negatywna wróciła zielona i za każdym razem powód był
inny.

**KN-6** cofnęła `build_alignment.normalise` do jej dawnej, własnej reguły. Zestaw:
**6/6 i 31/31, zielono**. Powód jest dokładnie tezą §3 — dopóki obie strony czytają
ten sam plik, dwie różne reguły dają zgodny wynik, bo każda jest stosowana po obu
stronach swojego porównania. Pinuje to dziś `test_kazde_wejscie_normalizuje_TA_SAMA_regula`,
porównujące WYNIKI obu wejść z regułą wzorcową na próbkach dobranych tak, żeby dawna
różnica była w nich widoczna. **KN-6b jest czerwona.**

**KN-3** zdjęła `.strip()` z `czlony`. Zestaw: **7/7, zielono** — bo na drodze
POROWNANIA obcięcie jest zbędne: `kanoniczny_czlon` i tak skleja białe znaki. Nie jest
zbędne na drodze drugiej, tej, w której człon jest **kluczem**: `stop_aliases`
i `vertical_profile` budują z członów klucze porównywane z polami `name_fr` / `name_nl`.
Pinuje to dziś `test_czlony_zwracaja_SUROWE_nazwy_obciete_i_w_kolejnosci`, i ten sam
test pilnuje kolejności — `kanoniczna` jest zbiorem, więc kolejności nie niesie i jej
zgubienia nie zauważyłaby żadna inna kontrola. **KN-3b jest czerwona.**

## 5. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem, po każdej `md5sum -c` na pięciu
plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | `ta_sama` wraca do porównania całego napisu | 5/7 i 47/48 |
| KN-2 | nazwa jako KROTKA członów, porównanie po równości | 5/7 i 47/48 |
| KN-3 | człony przestają być obcinane | **7/7 ZIELONA** |
| KN-3b | ta sama mutacja po dopisaniu kontroli członów | 7/8 |
| KN-4 | `ta_sama` zawsze `True` | 6/7 i **dwa testy** w walidatorze |
| KN-5 | człon kanoniczny obcięty do czterech znaków | 5/8, w tym kolizje |
| KN-6 | `build_alignment.normalise` wraca do własnej reguły | **6/6 ZIELONA** |
| KN-6b | ta sama mutacja po dopisaniu kontroli jednej reguły | 6/7 |

**KN-4 warta zdania:** „wszystko jest tą samą stacją" zapala nie tylko nowy test, ale
i `test_all_lines_sprawdza_KAZDA_linie_a_nie_pierwsza` sprzed tej pozycji — czyli
kontrola napisana wcześniej, dla innego powodu, łapie tę degenerację niezależnie.

**KN-1 i KN-2 dają ten sam obraz i to jest oczekiwane:** równość krotek jest wrażliwa
na kolejność tak samo jak równość napisów, więc obie mutacje padają na tej samej parze
wejść — na odwróconej kolejności członów.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_network_declarations.py
  10/10 przeszło

$ python3 tools/tests/test_all.py test_stop_names.py
  8/8 przeszło          (moduł nowy)

$ python3 tools/tests/test_all.py test_validate_axis.py
  48/48 przeszło        (było 47)

$ python3 tools/tests/test_all.py
  2243/2243 przeszło, 120 modułów

$ dotnet test tests/Sim.Tests
  Passed!  - Failed: 0, Passed: 600
```

Walidator na wszystkich sześciu osiach, po zmianie: **0 błędów** na każdej, po jednym
ostrzeżeniu o brakujących głębokościach (stan sprzed tej pozycji), a wiersze
`kolejność stacji zgodna z lines.json (L1)` i `(L5)` stoją tak samo jak przedtem.

## 7. Czego nie zrobiłem

- **Nie zmieniłem ani jednej nazwy w `data/`**, nie wybrałem języka wiodącego i nic
  nie tłumaczyłem — pole „Poza zakresem" wyklucza to wprost, a `data/` jest tylko
  do odczytu (§4.6).
- **Nie ujednoliciłem `split("|")` w miejscach, które nie porównują nazw** — na
  przykład w parserach tabel Markdown, gdzie kreska pionowa jest separatorem komórki,
  a nie członu nazwy.
- **Nie dopisałem `tools/track/stop_names.py` do audytu mutacyjnego**; audyt obejmuje
  moduły sprzed 05.09.2026 i dopisanie nowego wymaga własnego przebiegu triażu.

## 8. Zauważone przy okazji

- **`test_sam_PYTHONDONTWRITEBYTECODE_nie_wystarcza` zapaliło się RAZ, w jednym
  przebiegu całego zestawu, i nie odtworzyło się.** Nie odtworzyło się ani w tym samym
  drzewie (dwa przebiegi modułu osobno, dwa przebiegi całego zestawu), ani na czystym
  `main` w osobnym worktree (pełny zestaw, zero zgłoszeń). Test pochodzi z 6.D102
  i mierzy zjawisko zależne od SEKUNDY zapisu, więc jego wrażliwość na kolejność
  modułów w zestawie jest prawdopodobna — ale to jest hipoteza, nie pomiar. Do zakresu
  6.D111 nie należy (§4.10) i dlatego stoi tu, a nie w kodzie.
- **`reports/mutation-drift.md` musiał zostać przeliczony dla `validate.py`**: 40 → 39
  mutacji w zestawie starym, bo `_is_subsequence` zamieniło operator `==` na wywołanie.
  Ubyła mutacja, nie kontrola — reguła przeniosła się do modułu, którego audyt nie
  obejmuje.
- **`tools/track/` ma dziś 22 cele mutacyjne zamiast 21.** Liczba w
  `test_mutation_sweep.py` mierzy drzewo i rośnie razem z nim; podniosłem ją razem
  z powodem.
