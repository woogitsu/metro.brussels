# Bramka na koszt kroku `LineCore.Step` (6.D2)

**Zmierzone 06.09.2026 na commicie:** `b45be99c072d87882ecf84f52129f891f324b1ee`

## 1. Czego pilnuje ta bramka — i co jest w niej nieoczywiste

Nie samej liczby mikrosekund. Pilnuje **dwóch** warunków naraz, a drugi jest ważniejszy
od pierwszego:

1. koszt kroku nie przekracza progu;
2. pomiar dotyczy **dziewięciu składów na planie**.

Powód drugiego warunku jest zmierzony, nie wymyślony. 6.A12 (#308) pokazała, że
`budget --trains 32` melduje `N_max = 1`, gdy okno pomiaru jest krótsze niż jeden
odstęp — składy są zgłaszane na krok `i × odstęp`, więc przy `--headway-s 120`
i `--steps 1000` (okno 8,3 s) drugi skład nigdy nie wyjeżdża. Kolumna `µs_krok` ma
wtedy wartość i **mieści się w progu z ogromnym zapasem**, tylko opisuje zupełnie inny
przejazd. Bramka czytająca samą liczbę mikrosekund przechodziłaby wtedy na zielono
i nazywała pomiar jednego składu pomiarem dziewięciu.

## 2. Scenariusz

Kształt z `reports/linecore-budget.md` §4, zawężony do **jednej** obsady:

```
--axis data/track/L1_A.json
--signalling data/design/signalling/classic-2026.json
--limit-kmh 72 --exchange-s 20
--headway-s 90 --turnback-s 240
--steps 120000 --warmup 3 --repeats 9
--trains 32
```

`--warmup 3` nie jest ozdobą: §8.1 tamtego raportu zmierzył **6,2× różnicy** między
zimnym a rozgrzanym przebiegiem przy krótkim oknie. `--turnback-s 240` daje sufit
**9 składów** na tej osi; przy nawrocie 0 s sufit wynosi 12 (6.A12) — to dwa różne
scenariusze i bramka pilnuje tego pierwszego.

## 3. Pomiar

Trzy przebiegi z rzędu na tym kontenerze, ten sam kod:

```
[BUDŻET] 32;9;5.08;0.98;265081;223360;268544;17.0;3.772;1.01;0.05
[BUDŻET] 32;9;5.08;0.98;263287;243858;278454;13.1;3.798;1.01;0.05
[BUDŻET] 32;9;5.08;0.98;273610;242983;304590;22.5;3.655;1.01;0.04
```

Najwyższy: **3,798 µs/krok**. Dla porównania, ten sam scenariusz na maszynie projektu
05.09.2026: **4,561 µs** (`6c1048b`) i **4,665 µs** (`dfbde8f`) — §8.4, różnica 2,2 %
przy różnym obciążeniu maszyny.

Różnica wobec §4 jest w `N_śr`: **5,08** tutaj wobec **5,23** tam. Tamten przebieg
liczył całą drabinkę N z przeplotem, ten liczy jedną pozycję. `N_max = 9` w obu.

## 4. Próg: **8,0 µs/krok**

| liczba | skąd |
|---|---|
| 3,798 µs | najwyższy z trzech przebiegów na tym kontenerze |
| 4,665 µs | najwyższy znany pomiar tego scenariusza (§8.4, `dfbde8f`) |
| **8,0 µs** | próg — **1,71×** nad najwyższym znanym pomiarem |
| 8333,3 µs | budżet kroku 1/120 s; próg to **0,096 %** tego budżetu |

Margines pochłania trzy rzeczy, których ta sesja nie zna i nie udaje, że zna:
**prędkość runnera właściciela**, obciążenie maszyny w chwili przebiegu (§8.4: 2,2 %
między dwoma seriami; rozstęp powtórzeń w moich przebiegach do 22,5 %) oraz przyrost
kosztu od zmian w rdzeniu, które nie są regresem.

Precedens dla tego sposobu doboru jest w tym repozytorium: 6.D11 ustawiła budżet czasu
zestawu narzędzi jako dwukrotność najwyższego zmierzonego przebiegu, z tego samego
powodu i tym samym zdaniem o nieznanej prędkości maszyny właściciela.

Drugi warunek — **1,0 % budżetu klatki** — jest zapasowy i grubszy: łapie sytuację,
w której ktoś zmieni `FixedStep.SimulationHertz` i mikrosekundy przestaną znaczyć to,
co dziś.

## 5. Próg stoi w JEDNYM miejscu

`tools/ci/linecore-step-budget.json` — razem ze scenariuszem. Krok w
`.github/workflows/sim-tests.yml` woła wyłącznie `tools/ci/assert_linecore_budget.py`
i **nic nie porównuje sam**. Pilnuje tego test, który sprawdza, że ani próg, ani okno
pomiaru nie występują w treści YAML-a — liczba wpisana w dwóch miejscach rozjeżdża się
przy pierwszej zmianie.

## 6. Kontrole negatywne — wykonane

```
=== KONTROLA 1: krok spowolniony do 9,091 µs ===
BLAD: koszt kroku 9.091 us przekracza prog 8.000 us
kod: 1

=== KONTROLA 2: pomiar JEDNEGO składu podany jako dziewięć (pułapka 6.A12) ===
BLAD: na planie było 1 składów, a próg jest ustawiony na 9. Pomiar dotyczy INNEGO
przejazdu niż ten, o którym mówi próg — najczęstsza przyczyna to okno krótsze
niz (N-1) x odstep (6.A12)
kod: 1
```

Druga kontrola jest tu istotna: ten sam pomiar **mieści się w progu czasowym**
(3,772 µs przy progu 8,0), więc odrzucenie wynika wyłącznie z obsady. Osobny test
pilnuje, żeby powód odmowy był właśnie ten, a nie przekroczony czas.

Obie kontrole chodzą też w CI, jako krok „Core step gate can actually go red".

## 7. Czego ta bramka NIE mierzy, świadomie

**Przejazdu z wybiegiem.** Mierzony jest przejazd **bez wybiegu**. Bramka mówi to
w wypisie przy każdym przebiegu, zamiast milcząco mierzyć jeden wariant i nazywać go
„kosztem kroku".

> **Adnotacja z 06.09.2026 (6.A18).** Pomiar powyżej zostaje nietknięty — zmienia się
> tylko powód tego zdania. Gdy je pisano, `budget` **nie znał** `--coast-from-m`, więc
> pomiar z wybiegiem był niewykonalny. Od 6.A18 zna, i brak wybiegu jest tu **wyborem**:
> `coast_from_m: null` stoi w `tools/ci/linecore-step-budget.json` i stamtąd biorą go
> naraz wywołanie i zdanie w wypisie. `null` zostaje, bo próg 8,0 µs pochodzi
> z przejazdu bez wybiegu, a wybieg zmienia **przejazd**, nie tylko jego koszt —
> zmierzone przy 6.A18 na tej samej osi: `N_śr` 6,69 bez wybiegu, 6,67 przy 250 m,
> 6,40 przy 120 m, przy `µs/krok` nierozróżnialnym w szumie (3,73–3,84). Pomiar
> z wybiegiem wymaga więc **nowego progu i nowego raportu**, nie samej liczby w polu.

**Progu klatki z ekstrapolacji `N ≈ 330–390`.** `reports/linecore-budget.md` §7 mówi
wprost, że to ekstrapolacja **56–65× poza zakres pomiaru** (N ≤ 6,9). Pole „Poza
zakresem" pozycji 6.D2 wyklucza ją z bramki i to zostaje.

**Regresu mniejszego niż margines.** Próg 1,71× nad najwyższym znanym pomiarem złapie
regres rzędu dwukrotności, nie dwudziestu procent. To jest cena za to, żeby bramka nie
świeciła czerwono od sąsiedztwa na runnerze — i jest wybrana świadomie, a nie
przeoczona: wypis podaje zmierzoną wartość przy **każdym** przebiegu, więc dryf w tym
paśmie jest widoczny w logu, nawet kiedy bramka jest zielona.
