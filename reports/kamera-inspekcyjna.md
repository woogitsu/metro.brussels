# 6.C4 — kamera inspekcyjna, i trzy usterki, które sam wprowadziłem

**Zmierzone 08.09.2026 na commicie:** `006bb7fe5bc10b9dca03924bea6de7406d9644cd`
Blender 5.2.1 LTS, Godot 4.7.2.stable.mono.official.ed1daf0bf.

## 1. Przesłanka pozycji: potwierdzona pomiarem

Pozycja twierdziła, że oglądanie geometrii wymaga **przejechania do niej**. Kod to
potwierdza wprost — pętla `while (ChainageM < _shotChainageM && StepOnce())` — a pomiar
podaje cenę:

```
--view=outside --at-chainage=2521.1   kroków=14686   chainage=2521.2 m
```

## 2. Stałe kamery są WYPROWADZONE, nie dobrane wzrokiem

Pole „Poza zakresem" zostawia ocenę estetyczną T-902, więc żadnej liczby nie wybierałem
patrzeniem na kadr. Przekrój `box_double` wzięty z `tools/blender/profiles.py`, nie
z prozy: x od −4,70 do 4,70 (**9,40 m**), y od −1,20 do 4,70 (**5,90 m**).

| stała | wartość | skąd |
|---|---|---|
| `InspectStandoffM` | **6,32 m** | 5,90 / (2·tan 35°) = 4,2130 m wypełnia kadr dokładnie; 6,32 / 4,2130 = 1,5001, czyli zapas 1,50× |
| `InspectHeightM` | **1,75 m** | (−1,20 + 4,70) / 2 — środek przekroju, kadr na rurze, nie na główce szyny |
| `InspectLateralM` | **0,0 m** | na osi: niesymetryczność geometrii czyta się wtedy JAKO niesymetryczność |

Szerokość jest luźniejsza od wysokości (3,7757 m przy poziomym 102,45° dla 16:9), więc
wiąże wysokość — policzone, nie założone.

## 3. Trzy usterki, każdą złapał INNY przyrząd

Wszystkie trzy wprowadziłem sam, w tej samej godzinie. Wypisuję je, bo to one są
treścią tej pozycji, a nie czterdzieści wierszy kodu, które zostały.

### 3.1 Pusta gałąź zamiast wyjścia — złapał `timeout`, nie przegląd kodu

Pierwsza wersja wychodziła z `FastForwardToShot()` przez wyjście z metody, pomijając
**jej ogon**, w którym stoi `_shotCountdown = 5` — jedyny wyzwalacz migawki. Scena nie
robiła zrzutu wcale:

```
inspect  kod=124  czas=300.010 s        (outside: kod=0, 1.242 s)
```

Poprawka to gałąź **pusta**, nie drugi `_shotCountdown = 5`: wyzwalacz zostaje przy
jednym pisarzu.

### 3.2 Dwa `if` zamiast łańcucha — złapało porównanie md5 między kilometrażami

Mój blok stał jako osobne `if`, a stojący pod nim `if (Outside) … else …` wykonywał
wtedy swoje `else` i **nadpisywał** kamerę ustawieniem pościgowym. Trzy różne
kilometraże dawały obraz **bajtowo identyczny**:

```
500    -> 744dc83514d083f7  141891 B
2521.1 -> 744dc83514d083f7  141891 B
5000   -> 744dc83514d083f7  141891 B
```

**Czego to NIE złapało:** bramka metadanych dawała kod 0, metadane podawały żądany
kilometraż, a render wyglądał wiarygodnie — tunel z peronami, jak należy. Usterkę
pokazało wyłącznie porównanie DWÓCH kilometraży; jeden render nie mówił nic.

### 3.3 Okno streamowania szło za pojazdem — złapało OBEJRZENIE renderu

Po naprawieniu łańcucha kamera stała już w dobrym miejscu, ale chunki wchodziły do
pamięci wokół **pojazdu** (94 m), nie wokół kadru (2521 m). Kadr był **czarny**:

```
2521.1 -> 22384 B      (500 m -> 92315 B)
okno=[-206.0, 694.0]   temat=2521.1
```

Bramka metadanych przechodziła na tym czarnym kadrze **kodem 0**. To jest dokładnie
przypadek, dla którego `CLAUDE.md` §5 każe render OBEJRZEĆ, a nie opisać z metryk.

Poprawka: okno idzie za `SubjectChainageM`, czyli za tematem kadru. Dla trzech widoków
jazdy to ta sama liczba co dotąd, więc dla nich nie zmienia się nic.

## 4. Bramka przechodziła na czarnym kadrze — teraz go łapie

Metadane opisywały kadr kilometrażem **pojazdu**, więc dla widoku inspekcyjnego
opisywały inne miejsce osi niż to, które widać. Dwie zmiany, obie w kierunku
„sprawdzać WIĘCEJ":

1. Scena wypisuje `last_shot.subject_chainage_m` — kilometraż, który kadr naprawdę
   pokazuje. Pole jest **dopisane, nie podmienione**: `chainage_m` zostaje pozycją
   pojazdu, bo na niej stoi kontrola peronu („peron jest przy składzie").
2. Bramka kotwiczy kontrole GEOMETRII na `subject_chainage_m`, a dla widoku
   `inspect` żąda dodatkowo zera kroków i tego, żeby kilometraż pojazdu **różnił się**
   od tematu kadru.

Skutek zmierzony na tym samym czarnym kadrze co w §3.3: bramka daje dziś **kod 1**
i nazywa przyczynę. Przed zmianą dawała kod 0.

**Pole jest wymagane tylko dla widoku `inspect`,** i to też jest wybór z pomiarem:
żądanie go od wszystkich wywracało dziesięć testów bramki, których atrapa jest
**metadanymi zmierzonymi** na przebiegu Godota 4.3 — dopisanie do zapisu pomiaru pola,
którego tamten przebieg nie wypisał, byłoby jego falsyfikacją. Dla widoków jazdy
`subject_chainage_m` jest RÓWNE `chainage_m` z konstrukcji, więc odwrót na drugie pole
nie jest cichą zgodą; to ta sama liczba. Komunikat odmowy nazywa **pole, które
naprawdę porównano**, a nie zawsze to nowe.

## 5. Moja własna pomyłka w weryfikacji

Uruchomiłem bramkę na `build/6c4/inspect_metadata.json` i dostałem kod 0 — na pliku
**nieaktualnym**. Prefiks metadanych bierze się z nazwy pliku PRZED pierwszym
podkreśleniem, więc zrzut `inspect.png` zapisuje `GODOT_metadata.json`, a
`inspect_metadata.json` został po starszym przebiegu `inspect_2521.png`. Po powtórzeniu
na pliku świeżym bramka dawała **kod 1**.

Zauważone i nietknięte: ta reguła prefiksu jest pułapką niezależną od tej pozycji.

## 6. Pole „Skończone, gdy" żądało demonstracji, której NIE MA

Pole mówiło, że brak przejazdu ma pokazać **pomiar czasu obu wariantów**. Zmierzone,
trzy powtórzenia każdego:

| | czas | kroki |
|---|---|---|
| `outside` | 1,137 / 1,204 / 1,139 s | 14 686 |
| `inspect` | 1,241 / 1,299 / 1,165 s | **0** |

**Przedziały się zachodzą, a `inspect` jest nawet nieco wolniejszy.** Powód jest
policzalny: 14 686 kroków przy 4,4 µs/krok (6.D41) to ~65 ms, czyli ~5 % przebiegu
trwającego 1,2 s — poniżej rozrzutu. Czas tej różnicy nie pokazuje i pokazać nie może.

Demonstracja jest więc **przekierowana na liczbę, która ją pokazuje**: zero kroków.
Nie zostaje przy tym prozą — sprawdza ją bramka (§4), czyli po przekierowaniu jest jej
WIĘCEJ, nie mniej.

## 7. Co widzę na renderach

**`inspect` przy 2521,1 m.** Wnętrze rury `box_double` widziane z osi: podłoga, dwie
ściany boczne, płaski strop i ścięte narożniki górne widoczne jako skośne pasy przy
górnej krawędzi kadru. Rura biegnie w dal i **zakręca w prawo** — prawa ściana jest
bliżej i jaśniejsza, dalszy koniec ciemnieje. Składu w kadrze **nie ma** (stoi na
94,0 m) i nie ma peronów, co zgadza się z bramką: „w promieniu 20,0 m od kilometrażu
zrzutu 0 brył".

**`inspect` przy 500 m.** Rura **prosta**, a po obu stronach płyty peronowe —
podniesione krawędzie zbiegające się do punktu zbiegu. Inne miejsce, inna geometria,
zgodne z tym, co dane mówią o tych kilometrażach. To jest dowód, że kamera naprawdę
chodzi za kilometrażem, a nie stoi w jednym miejscu (§3.2).

**Ciemność kadru jest oczekiwana i NIE naprawiam jej:** reflektor jest przy pojeździe,
a pojazdu tu nie ma. Światło i materiały są w polu „Poza zakresem" (T-902, ocena
estetyczna). Zgłaszam to jako obserwację, nie jako usterkę.

## 8. Weryfikacja

```
$ GODOT ... --shot=build/6c4v/INSPECT_2521.png --at-chainage=2521.1 --view=inspect
kod 0; [ZRZUT] ... widok=Inspect kroków=0 chainage=94.0 m

$ python3 tools/ci/assert_shot_metadata.py --metadata build/6c4v/INSPECT_metadata.json ...
[METADANE] 3/12 chunków rezydentnych, 3 obiektów, 9576 wierzchołków, oś 6686.739 m == 6686.739 m
kod 0

$ GODOT --path src/Game -- --view=zmyslony
kod 9; [ARGUMENT] nieznany widok '--view=zmyslony'. Znane: cab, chase, outside, inspect

$ python3 tools/tests/test_all.py; echo "kod: $?"
  1996/1996 przeszło        RAZEM 93.324 s, 1996 testów, 105 modułów        kod: 0

$ dotnet test tests/Sim.Tests    ->  Passed: 590 / 590
$ dotnet test tests/Game.Tests   ->  Passed: 212 / 212
```

`RunPlanTests` 59 → **61** metod testowych.

## 9. Dwie kontrole negatywne WYKONANE

**KN-1 — `InspectStandoffM` zdjęte z listy `All`.** Pole „Skończone, gdy" żądało, żeby
każdą nową stałą łapało `DesignAssumptionsTests`:

```
Failed!  - Failed: 1, Passed: 211, Total: 212
  Failed EveryConstantIsDeclaredAsAnAssumption
```

Po przywróceniu 212/212.

**KN-2 — streamowanie wraca na pojazd.** To kontrola poprawki z §3.3 i pokazuje naraz
dwie rzeczy: kadr znów jest czarny, a bramka **już to łapie**:

```
rozmiar kadru bez poprawki: 22384 B      (z poprawką: 81211 B)
bramka kod: 1, window_low_m = -206.0, window_high_m = 694.0
```

## 10. Czego świadomie NIE zrobiłem

- **Nie tknąłem światła ani materiałów.** Pole „Poza zakresem" odsyła je do T-902.
- **Nie tknąłem pasma 94..106 m kamery goniącej.** Osobna decyzja właściciela; nowy
  widok nie jest jej obejściem — nie dotyka `ChaseBehindM` ani `_chaseAvailable`.
- **Nie przeliczyłem ocalałych w `reports/mutation-drift.md`.** Mianownik dla
  `assert_shot_metadata.py` przepisany 65 → **73**, bo bramka go sprawdza i liczy się
  w ułamku sekundy; ocalałe wymagają przebiegu zestawu na mutację, więc liczba 32
  pochodzi z pomiaru sprzed tej pozycji i tak jest w raporcie oznaczona.
- **Nie poprawiłem reguły prefiksu metadanych** z §5 — pułapka realna, ale spoza
  zakresu tej pozycji (§4.10).
