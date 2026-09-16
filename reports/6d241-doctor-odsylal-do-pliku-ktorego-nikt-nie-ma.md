# 6.D241 — doctor odsyłał do pliku, którego w CI nikt nie ma

**16.09.2026**, na `bac8789`. Wejście: `doctor.sh`, logi jobów `blender-smoke`
104696967107 i 104702701634, `tools/tests/test_all.py`, `tools/ci/blender_smoke.sh`.
Wyjście: wyciąg z logu zestawu wypisywany przez `doctor.sh`, bramka
`tools/tests/test_doctor_test_log.py`, ten raport.

---

## 1. Skąd to wyszło — i to nie jest przypadek hipotetyczny

16.09.2026 `blender-smoke` padł na **dwóch niezależnych pull requestach**
(#630 i #632, **różne gałęzie**, ta sama baza `main`). Jedyny ślad po padniętym
zestawie w całym logu joba to jeden wiersz:

```
2026-09-16T06:58:50.7419954Z Testy narzędzi:
2026-09-16T07:11:02.6602853Z   BLAD  testy nie przechodzą — zobacz /tmp/mbxl_tests.log
```

Ani jednego `Traceback`, ani jednego wiersza `FAIL`, ani jednej nazwy testu.
Artefakt joba melduje „**With the provided path, there will be 1 file uploaded**",
**1393 bajty** (#630) i **1394 bajty** (#632) — czyli sam `build/t010/report.txt`,
który zawiera dokładnie to samo, co log joba, bo `blender_smoke.sh` ma
`exec > >(tee -a "$REPORT")`.

**Nazwy padającego testu nie dało się odzyskać z niczego, co CI zachowało.**
Plik `/tmp/mbxl_tests.log` leży poza workspace i nie jest zbierany przez żaden krok.

To jest ta sama rodzina, którą projekt tropi od 6.D27: **komunikat nie jest
wynikiem**. `CLAUDE.md` §5 zakazuje form weryfikacji typu „skrypt wykonał się bez
błędu" dokładnie z tego powodu — a doctor meldował porażkę i odsyłał do dowodu,
którego czytający nie ma.

## 2. Dlaczego wyciąg, a nie `tail` — i to jest liczba, nie wrażenie

Zmierzone na zielonym przebiegu z tego samego dnia (scalony wierzchołek `fd351f7`,
ten sam zestaw):

| wielkość | wartość |
|---|---|
| wierszy w logu zestawu | **2836** |
| numer wiersza `N/M przeszło` | **2707** |
| ile to od końca | **129** |
| co stoi za nim | wyłącznie lista czasów **126 modułów** |

`tail -n 100` nie sięga więc **nawet do podsumowania**. Wiersze `FAIL` zestaw
wypisuje w trakcie pętli po modułach — są rozrzucone po całej długości logu, a nie
zebrane na końcu. Ogon jest tu złym przyrządem i dlatego wypis jest wyciągiem:
wszystkie wiersze `FAIL` (do sufitu) plus wiersze `N/M przeszło` i `RAZEM`.

## 3. Co weszło

- `doctor.sh`: funkcja `wypisz_wyciag_z_logu`, sufit `WYCIAG_FAILI` (domyślnie **40**,
  nadpisywalny przez `MBXL_WYCIAG_FAILI`), gałąź porażki **przepisana, a nie dopisana
  obok** — zdanie „zobacz $log_file" zniknęło.
- Osobna gałąź na przypadek **zestawu padniętego POZA ciałem testu** (zero wierszy
  `FAIL`). Nie jest teoretyczna: 15.09.2026 cztery joby padły na
  `ModuleNotFoundError: No module named 'yaml'` (6.D240), czyli przed wykonaniem
  jakiegokolwiek testu. Wyciąg szukający wyłącznie `FAIL` byłby wtedy **pusty**,
  a pusty wypis czyta się jak brak problemu — więc ta gałąź nazywa sytuację i pokazuje
  ogon logu.
- `tools/tests/test_doctor_test_log.py` — **pięć bramek**, wszystkie na PRAWDZIWYM
  `doctor.sh` uruchamianym w podprocesie na drzewie symlinków z podmienioną atrapą
  `tools/tests/test_all.py` (ta sama technika co `test_doctor_queue_claim`).

**`MBXL_DOCTOR_RUNNING` jest w bramce ZDEJMOWANE i to nie jest ostrożność na zapas.**
`CLAUDE.md` §5 i `tools/ci/blender_smoke.sh` każą uruchamiać zestaw właśnie przez
doctora, który tę zmienną eksportuje — czyli w CI ten moduł biegnie z ustawionym
markerem. Bez zdjęcia go zagnieżdżony doctor wypisałby „Testy: pomijam" i bramka
mierzyłaby gałąź, której nie dotyczy: zielona w jobie `tools`, zielona
w `blender-smoke`, i ślepa w obu. Zmierzone w KN-4.

## 4. Kontrole negatywne — pięć, przewidywania zapisane przed przebiegiem

Baza: **5/5 przeszło**. Po każdej kontroli `md5sum -c` **OK** na obu plikach.

| # | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | gałąź porażki cofnięta do jednego wiersza `zobacz $log_file` | 1/5 | **1/5** |
| KN-2 | sufit podniesiony do 100, czyli POWYŻEJ atrapy (45 wierszy) | 4/5 | **4/5** |
| KN-3 | sufit ZDJĘTY z wypisu, stała zostaje w pliku | 4/5 | **4/5** |
| KN-4a | `MBXL_DOCTOR_RUNNING=1` w środowisku, zdejmowanie ZOSTAJE | 5/5 | **5/5** |
| KN-4b | to samo, ale zdejmowanie usunięte z bramki | 1/5 | **1/5** |
| KN-5 | gałąź „zero wierszy FAIL" przemilczana (bez ogona logu) | 4/5 | **4/5** |

**KN-3 jest tą, która odróżnia stałą od zapadki:** sufit zdjęty z samego wypisu, ale
nadal stojący w pliku, zapala bramkę — bo test liczy, ile wierszy doctor NAPRAWDĘ
pokazał, a nie czy liczba stoi w kodzie. Bez tego `WYCIAG_FAILI` byłby napisem.

**KN-4b jest tą, która mierzy własną ślepotę bramki**, a nie kodu: to jedyna kontrola,
w której mutowany jest test, nie `doctor.sh`.

## 5. Co złapały bramki tego repozytorium, zanim doszedłem do werdyktu

Cztery rzeczy, żadna z mojego oka:

- `test_every_module_delegates_to_the_one_runner` i
  `test_every_test_module_can_be_run_directly` — nowy moduł nie miał strażnika
  `__main__`;
- `test_caly_Python_drzewa_stoi_pod_tools`, `test_compileall_na_czystym_drzewie...`
  i `test_skan_sekwencji_czyta_KAZDY_modul_drzewa...` — trzy liczniki modułów drzewa
  (205 → **206**);
- `test_zdanie_o_liczbie_modulow_zgadza_sie_z_katalogiem` — proza w `test_all.py`
  mówiła o 126 modułach przy 127 w katalogu;
- `test_ile_bramek_stoi_na_NAPISIE_a_nie_na_ZACHOWANIU` — 886 → **894**.

## 6. Czego ta pozycja NIE robi

**Nie rozstrzyga, dlaczego `blender-smoke` jest czerwony.** To jest cała treść tego
zdania: pozycja daje *przyrząd*, którym da się tę przyczynę odczytać z następnego
przebiegu, a nie samą przyczynę. Co o tej awarii wiadomo dziś, zmierzone:

- pada na **dwóch różnych gałęziach** na tej samej bazie (#630 i #632), więc nie
  pochodzi z diffu żadnej z nich;
- obie czerwone przypadły maszynie **`docker-runner-04`**; wszystkie zielone
  przebiegi `blender-smoke` z ostatniej doby szły na `metro-wsl-DOM-NEW-01/02`;
- ten sam zestaw na tym samym scalonym wierzchołku jest **zielony w jobie `tools`**
  (159 s) i **zielony lokalnie** (2499/2499, kod 0, 213 s — także przy ustawionym
  `MBXL_DOCTOR_RUNNING=1` i przy istniejących katalogach `build/` i `renders/`);
- na `docker-runner-04` zestaw biegł pod doctorem **732 s**, czyli ok. **4,6×**
  dłużej niż w jobie `tools`.

Hipotezy o tym, KTÓRY test pada, w tym raporcie nie ma i nie będzie — bo bez wyciągu
nie da się jej sprawdzić, a zgadywanie jest dokładnie tym, co ten projekt tępi.

Nie ruszałem też: treści zestawu, żadnego progu czasowego, żadnego workflowa,
ani maszyn właściciela.

## 7. Weryfikacja

```
  2498/2498 przeszło
  RAZEM 217.318 s, 2498 testów, 127 modułów
```

`dotnet test tests/Sim.Tests` — **662/662**; `dotnet test tests/Game.Tests` — **318/318**.

Zapadki podniesione w tym samym commicie, każda z wartością DZISIEJSZĄ:
`ASERCJI_NAPISOWYCH_RAZEM` **894** (było 886, doszło osiem asercji nowego modułu),
`BAJTKOD_PO_COMPILEALL_PLIKI` **206** (było 205), `MODULOW_W_CALYM_DRZEWIE` **206**
(było 205), `MIN_REPORTS` **353** (było 352), proza o liczbie modułów **127** (było 126),
rozkład `tools/tests` **135** — w komentarzu zapadki stała liczba z 13.09.2026 i rozjechała
się o cztery. Dalej, wszystkie policzone **diffem list**, nie odejmowaniem:
`MINIMUM_DETAIL_BLOCKS` **309**, `ADRESOW_W_WYKONANYCH` **1013** / **64** / **401**
(doszły cztery adresy własnego bloku tej pozycji; pole „Wyjście” drgnęło tu pierwszy
raz od 6.D224) i `WYWOLAN_W_WYKONANYCH` **136** w polu „Weryfikacja” (jedno wywołanie
`test_all.py test_doctor_test_log.py` z płotka własnego bloku).
