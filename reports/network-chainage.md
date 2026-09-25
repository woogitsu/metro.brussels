# Mapa kilometrażu sieci — co pokrywają pakiety, gdzie są dziury, gdzie rury się przenikają

**Zmierzone na commicie:** `580882c`

Stan: **2026-09-01**. Narzędzie: `tools/track/network_chainage.py`.
Wejście: sześć osi z `data/track/`, bez sieci i bez dodatkowych źródeł.

Pakiety są jednostką **budowy**, nie jazdy. Każda oś zaczyna kilometraż od zera,
a między pakietami zostają odcinki, których nikt nie zbudował. Skład jadący całą
linią 1 przekracza granicę pakietu i musi wiedzieć, gdzie ona jest i co za nią leży.

---

## 1. Kilometraż nie jest ciągły i nie da się go zszyć

**Żadne dwa pakiety nie stykają się końcami.** Wszystkie sześć zaczyna i kończy na
innej stacji niż sąsiad:

| granica | cięciwa między końcami osi |
|---|---:|
| L1_A start (Gare de l'Ouest) ↔ L2_E koniec (Beekkant) | 509,6 m |
| L1_A start (Gare de l'Ouest) ↔ L5_C start (Jacques Brel) | 614,9 m |
| L1_B start (Montgomery) ↔ L5_D start (Thieffry) | 674,5 m |
| **L1_A koniec (Merode) ↔ L1_B start (Montgomery)** | **703,0 m** |
| L2_E start (Elisabeth) ↔ L6_F start (Belgica) | 737,2 m |
| L1_A koniec (Merode) ↔ L5_D start (Thieffry) | 738,1 m |
| L2_E koniec (Beekkant) ↔ L5_C start (Jacques Brel) | 1123,5 m |

**Cięciwa to nie jest długość brakującego toru.** Odcinków międzypakietowych nie ma
w `data/track/`, więc nie da się ich zmierzyć wzdłuż trasy — cięciwa jest dolnym
ograniczeniem i tyle o niej wiadomo. Długości wzdłuż łamanej źródłowej policzył
`reports/packages-BF-alignment.md` §8: **4034 m w pięciu odcinkach**.

Wniosek dla T-400 i dalej: **nie ma czegoś takiego jak kilometraż linii 1.** Jest
kilometraż pakietu A i kilometraż pakietu B, a między nimi 703 m, których nie ma.
Skład dojeżdżający do Merode na 6686,7 m nie ma dokąd jechać dalej — nie dlatego,
że coś się zepsuło, tylko dlatego, że `lines.json` definiuje pakiety tak, jak
definiuje. Domknięcie sieci jest osobną decyzją właściciela.

## 2. Co pokrywa która oś

| oś | pakiet | od → do | długość | stacji |
|---|---|---|---:|---:|
| `L1_A` | A — Pień 1/5 | Gare de l'Ouest → Merode | 6686,4 m | 12 |
| `L1_B` | B — Wschód 1 | Montgomery → Stockel | 5083,2 m | 9 |
| `L2_E` | E — Pierścień 2/6 | Elisabeth → Beekkant | 9020,8 m | 17 |
| `L5_C` | C — Zachód 5 | Jacques Brel → Erasme | 5386,4 m | 9 |
| `L5_D` | D — Wschód 5 | Thieffry → Herrmann-Debroux | 3847,2 m | 7 |
| `L6_F` | F — Północ 6 | Belgica → Roi Baudouin | 4456,7 m | 7 |

Razem **34 480,6 m**. Wszystkie sześć mają `vertical.status = "not_modelled"`.

## 3. Dwie rury przechodzące przez siebie

To jest znalezisko tego zadania i wejście dla sceny, która wczyta więcej niż jeden
pakiet naraz.

Osie **L1_A i L2_E dzielą korytarz na 464,7 m**, w dwóch miejscach:

| miejsce | kilometraż L1_A | kilometraż L2_E | co to jest |
|---|---|---|---|
| Gare de l'Ouest – Beekkant | 105,0–524,8 m | 8616,2–9020,8 m | linie 1/5 i 2/6 biegną **równolegle** |
| Arts-Loi | 4482,4–4527,3 m | 3656,3–3701,3 m | linie **krzyżują się** |

Te dwa przypadki znaczą co innego i narzędzie je rozdziela:

- **Korytarz równoległy jest faktem o sieci.** Mediana odległości osi na odcinku
  Gare de l'Ouest – Beekkant to **14,91 m**, czyli dwa sąsiednie korytarze. Rury
  o szerokości 9,40 m przy takim rozstawie się nie dotykają.
- **Skrzyżowanie jest artefaktem braku niwelety.** W dwóch miejscach osie zbliżają
  się poniżej szerokości profilu:

| odległość osi | kilometraż L1_A | miejsce |
|---:|---:|---|
| **1,05 m** | 179,9 m | Gare de l'Ouest +180 m |
| **1,30 m** | 4497,3 m | Arts-Loi −64 m |
| 3,28 m | 194,9 m | Gare de l'Ouest +195 m |
| 5,96 m | 164,9 m | Gare de l'Ouest +165 m |

Przy odległości osi 1,05 m dwie rury o szerokości 9,40 m nachodzą na siebie
o **8,35 m** — czyli praktycznie całą szerokością. W rzeczywistości nic tam nie
koliduje, bo linie krzyżują się **na różnych poziomach**; w modelu wszystko leży na
Z = 0 i nic ich pionowo nie rozdziela.

**Konsekwencja praktyczna:** dopóki T-112 (#10) nie dostarczy niwelety, sceny
zawierającej jednocześnie pakiet A i pakiet E **nie da się zbudować uczciwie**.
Pierwszy przejazd (T-400) używa jednego pakietu i to nie był przypadek.

## 4. Czego ten raport NIE rozstrzyga

- **Nie domyka sieci.** Odcinki międzypakietowe nie powstają; `lines.json` jest
  `data/`, czyli tylko do odczytu, a zmiana definicji pakietów to decyzja właściciela.
- **Nie proponuje wspólnego kilometrażu linii.** Zszycie pakietu A z B wymagałoby
  osi odcinka Merode – Montgomery, której nie ma.
- **Nie rozwiązuje kolizji.** Rozdzielenie pionowe rur wymaga rzędnych główki szyny,
  których nie ma w publicznych źródłach (T-901). Podniesienie jednej rury „na oko"
  byłoby zmyśleniem głębokości, czego zabrania reguła 1 z `CLAUDE.md`.
- **Nie sprawdza pozostałych par osi.** Żadna inna para nie zbliża się na 30 m, więc
  nie ma czego mierzyć — ale to wynika z tego, że cztery z sześciu pakietów leżą na
  peryferiach sieci, a nie z tego, że sieć nigdzie indziej się nie krzyżuje.
  Nieistniejące odcinki międzypakietowe mogą krzyżować się z czymkolwiek.

## 5. Aktualizacja 24.09.2026 — fizyczny koniec pakietu A

**Sprawdzone na poprawce `0700278` (w integracji `264d2e3`),** na rzeczywistej osi
`data/track/L1_A.json`. To kontrola zachowania gry, nie nowy pomiar sieci.
Merode leży na 6686,350 m, a przejezdna oś kończy się na 6686,739 m.

Próba zaczynała się na Schuman (5467,350 m), z limitem 72 km/h. Autopilot
zatrzymał się przy Merode na 6686,048 m w kroku 11428, tak samo jak przed
poprawką. Maszynista, trzymając pełny ciąg, osiągnął koniec osi w kroku 8345.
Po kolejnych 600 krokach tego samego polecenia czoło nadal stało na 6686,739 m
z prędkością 0 km/h; ślad ruchu wskazywał tę samą pozycję i prędkość.
Względna reszta bilansu energii tego ręcznego przebiegu wyniosła `1,007e-13`.

Pozycja obrazu i pozycja symulacji kończą się więc w tym samym miejscu.
Scena pokazuje koniec toru, a po założeniu postoju obsługę Merode. Ta blokada
nie buduje brakującego odcinka Merode–Montgomery opisanego wyżej.

**Aktualizacja po `1fabd10` (24.09.2026).** Powyższy pomiar dokumentuje
zabezpieczenie fizycznej granicy osi. W zwykłej jeździe ręcznej z pełnym ciągiem
skład rozpoczyna teraz hamowanie służbowe przed Merode i staje na
6686,349700 m, około 0,0003 m przed kilometrażem stacji, zamiast dojeżdżać do
6686,739 m i zatrzymywać się przez przycięcie stanu. Zabezpieczenie granicy
pozostaje na wypadek zbyt późnego hamowania. W osobnym przebiegu maszynista
przełączył W → S → W; skład stanął na 6682,052 m (błąd −4,298 m, w oknie
peronu ±5 m) i nie ruszył ponownie. Oba 65 000-krokowe zapisy odtworzono bez
grafiki w Godot 4.7.2 i `Sim.Runner`; telemetria każdej pary była identyczna
co do bajtu. Nadal brak przejezdnej osi Merode–Montgomery.
