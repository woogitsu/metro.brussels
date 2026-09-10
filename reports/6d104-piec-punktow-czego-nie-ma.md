# 6.D104 — pięć zdań o braku, dwie tabele i jedno zdanie, które jest nieprawdą

**Zmierzone 10.09.2026 na:** `a202423`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_readme_claims.py` (`osie_plaskie`,
`wezly_skladu_w_scenie`, `dlugosc_pakietow_m`, `POMIARY_BRAKOW`, `POWODY_BEZ_WPISU`),
`data/track/*.json`, `src/Game/Scenes/FirstRun.tscn`, `data/network/lines.json`,
`tools/track/network_chainage.py` — wszystkie dane wyłącznie do czytania.

---

## 1. Rozstrzygnięcie dla każdego z pięciu punktów

| punkt sekcji „Czego nie ma" | rozstrzygnięcie | liczba z drzewa |
|---|---|---|
| profilu pionowego | **pomiar** | 6 osi z `vertical.status = not_modelled` i Z = 0 |
| stacji jako brył | **powód** | zdanie jest dziś NIEPRAWDZIWE |
| wielu składów W SCENIE | **pomiar** | 1 węzeł `TrainView` w `FirstRun.tscn` |
| kabiny i wnętrz | **powód** | fałszyfikatorem byłaby nazwa, której nie ma |
| ciągłego kilometrażu linii | **pomiar** | 34 481 m osi w sześciu pakietach |

Trzy pomiary plus dwa powody to pięć, i tej arytmetyki pilnuje osobny test —
`test_every_absence_bullet_has_a_measurement_or_a_written_reason`. Bez niego szósty
punkt dopisany do README nie zostałby przez nic zauważony, a dokładnie tak powstała
ta pozycja: tabela miała **jeden** wpis na **pięć** punktów i nikt tego nie liczył.

## 2. Dlaczego to nie mogły być cztery wiersze dopisane do istniejącej tabeli

`ZAPRZECZENIA` ma semantykę: **„zdanie twierdzi, że czegoś nie ma, a te nazwy
dowodzą, że jest"**. Trzyma więc zdania **już fałszywe**, a jej kontrola przyrządu
(`test_the_denial_table_points_at_names_that_are_really_in_the_core`) żąda wprost,
żeby wskazane nazwy dziś w drzewie **były** — bo wpis wskazujący nazwę nieobecną nie
zapali się nigdy.

Wszystkie cztery pozostałe punkty są **dziś prawdziwe**. Zdania prawdziwego w tej
tabeli zapisać się nie da: jego fałszyfikator z definicji jeszcze nie istnieje.
Stąd druga tabela, `POMIARY_BRAKOW`, o **odwrotnej** semantyce — zdanie jest dziś
prawdziwe, a wpis podaje liczbę, przy której pozostaje prawdziwe. Pierwsza łapie
zdanie, które JUŻ jest nieprawdziwe; druga — zdanie, które PRZESTAJE być prawdziwe.

Jedyny wpis `ZAPRZECZENIA` zostaje nietknięty. Jego zdanie („Rdzeń prowadzi jeden
skład") w README dziś nie stoi — 6.D87 je poprawiło — więc wpis jest **wartownikiem**
na wypadek powrotu tamtego sformułowania, i to jest jego poprawna rola.

## 3. Jedno z pięciu zdań jest nieprawdą

Punkt „stacji jako brył" mówi: **„pierwsza stacja typowa (T-212) jest dopiero
w planie"**.

T-212 stoi w `docs/TASKS.md` jako **`[x]`**, scalone jako **#137** (`fe14d72`), a jego
pole „Wynik" podaje: **37 brył, 596 wierzchołków, 522 ściany** na stacji Parc
(`corridor=1, edge=2, lift=1, mezzanine=2, platform=2, portal=1, stairs=28`).
W drzewie leżą `tools/track/station_components.py`, `tools/blender/station_kit.py`,
`tools/tests/test_station_components.py` i `reports/T-212-station.md`.

**Druga połowa tego samego punktu zostaje prawdą** i to jest istotne: układ antresoli,
przebieg korytarzy i liczba wyjść **nie wynikają z żadnych danych**. Moduł mówi to
wprost — buduje układ *kanoniczny*, wszystkie wymiary są `design_assumption`, żaden
nie pochodzi ze STIB. Punkt jest więc w połowie nieaktualny, a nie w całości.

**Nie poprawiłem go**, bo pole „Poza zakresem" tej pozycji wyklucza zmianę treści
punktów README. Wpis w tabeli też nie wchodzi: zapaliłby się natychmiast i zostawił
drzewo czerwone. Zdanie jest więc zmierzone i zapisane — w `POWODY_BEZ_WPISU`, gdzie
przeczyta je każdy, kto sięgnie po tę tabelę — a nie naprawione po cichu ani przemilczane.

## 4. Punkt, którego związać się nie da, i dlaczego

„kabiny i wnętrz" — fałszyfikatorem byłby **generator kabiny** w `tools/blender/`
albo węzeł wnętrza w scenie. Ani jedno, ani drugie dziś nie istnieje, więc:

* w `ZAPRZECZENIA` wpis wskazywałby nazwę nieobecną — odrzuca to kontrola przyrządu
  tamtej tabeli, i słusznie;
* liczbą też się tego nie zwiąże: „zero generatorów kabiny" wymagałoby zgadywania,
  jak taki plik zostanie kiedyś nazwany, a bramka na zgadniętej nazwie milczy tym
  ciszej, im lepiej ktoś nazwie plik inaczej.

`--view=cab` w scenie **jest kamerą, nie wnętrzem** i fałszyfikatorem nie jest.

## 5. Punkt związany w połowie: 34 481 m tak, 4034 m nie

Zdanie o kilometrażu ma dwie liczby. Pierwsza jest z drzewa:

```
[SIEĆ] 6 osi, razem 34480.6 m
```

`sum(length_m)` po sześciu osiach daje **34 481 m** po zaokrągleniu — dokładnie liczbę
z `reports/packages-BF-alignment.md` §8, tyle że policzoną z plików, a nie przepisaną
z raportu. Bramka pilnuje też, że suma **jest mniejsza** od 39 900 m
(`network.metro_length_km` z `lines.json`), bo na tym stoi zdanie „pokrywa pakiety,
nie linie".

Druga liczba, **4034 m w pięciu odcinkach**, z drzewa policzyć się dziś nie da.
Pochodzi z pomiaru po **kształtach GTFS** (`001m` v1, `005m` v1, `002m` v2, `006m` v2),
a te w repozytorium nie leżą: `data/network/shapes-manifest.json` jest manifestem
wskazującym zdalny plik `zip` o 856 291 bajtach, pobierany osobno. Najbliższy
istniejący przyrząd, `network_chainage.endpoint_gaps`, mierzy **cięciwy między końcami
osi** i daje co innego — **dziewięć** par bliżej niż 2 km, razem **8760,4 m** — bo
liczy każdą parę końców, a nie pięć rzeczywistych odcinków międzypakietowych. Podpięcie
go pod to zdanie byłoby wiązaniem zdania z liczbą, która go nie dotyczy.

## 6. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` czterech plików na bok i `md5sum -c` po przywróceniu, z `__pycache__`
czyszczonym przed każdym przebiegiem (procedura z 6.D102).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | oś dostaje rzędne i `vertical.status = modelled` | **8/10**, dwa testy |
| KN-2 | scena dostaje drugi węzeł `TrainView` | **9/10** |
| KN-3 | szósty punkt dopisany do sekcji README | **9/10** |
| KN-4 | punkt ma naraz pomiar i powód | **9/10** |
| KN-5 | powód skrócony do zdawkowego „nie da się" | **8/10**, dwa testy |
| KN-6 | suma długości bierze jeden plik zamiast wszystkich | **8/10**, dwa testy |
| KN-7 | licznik węzłów nie znajduje zasobu i zwraca zero | **9/10** |

Po każdej: `md5sum -c` → `OK` na wszystkich czterech plikach.

KN-7 jest tu warta osobnego zdania: licznik, który nie znajdzie zasobu skryptu, zwraca
zero — a zero czyta się jako „scena nie pokazuje **ani jednego** składu", czyli jako
zdanie MOCNIEJSZE niż to w README. Bez asercji na obecność `src/Game/World/TrainView.cs`
w scenie zepsuty licznik wyglądałby jak wynik.

## 7. Czego świadomie nie zrobiłem

- **Nie zmieniałem treści żadnego punktu README** ani nie przeliczałem wyników
  historycznych — pole „Poza zakresem" mówi to wprost. Dotyczy to także punktu
  z §3, o którym wiem, że jest nieprawdziwy.
- **Nie ruszałem `ZAPRZECZENIA`.** Wpis jest wartownikiem i jego rola się nie
  zmieniła.
- **`data/` tylko do odczytu.** Mutacje w kontrolach szły przez `cp` kopii i zostały
  cofnięte z potwierdzeniem sumą.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- **Punkt „stacji jako brył" wymaga osobnej pozycji** — zdanie o T-212 jest
  nieprawdziwe od 04.09.2026, a jego poprawienie to zmiana treści README, czyli
  dokładnie to, czego ta pozycja nie robi.
- **`network_chainage.endpoint_gaps` liczy pary końców, nie odcinki sieci.**
  Dziewięć par przy pięciu rzeczywistych dziurach — narzędzie nie jest zepsute, po
  prostu odpowiada na inne pytanie, ale nazwa `endpoint_gaps` sugeruje to samo, co
  „dziury między pakietami", i już raz mnie na tym zatrzymała.
