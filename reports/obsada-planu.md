# Ile składów naprawdę biegnie po planie (6.A12)

**Zmierzone 06.09.2026 na commicie:** `9b99b2375b82d152f9e2ccd6ff9cd70f8a0fbbd7`

Oś `data/track/L1_A.json`, plan `data/design/signalling/classic-2026.json`
(`classic-2026-L1_A`, **23 bloki**, **11 dróg**, **12 stacji**), `--limit-kmh 72`,
`--exchange-s 20`, `--repeats 1 --warmup 0`, ATP wyłączone, nawrót 0 s.
Krok symulacji 120 Hz, więc `--steps N` to okno `N/120` sekund.

## 1. Skąd ta pozycja

6.D15 (#301) naprawiło komendę z bloku 6.D2 i przy okazji zobaczyło wynik:

```
[BUDŻET] 32;1;1.00;0.00;132528;...
[BUDŻET] mieści się w 1/120 s: … największe zmierzone N=32 zajmuje 0.09% budżetu kroku
przy 1 składach faktycznie na planie
```

Trzydzieści dwa zgłoszone składy, **jeden** na planie. Kolumna `N_zgł` nie jest
liczbą składów, które biegły — i podsumowanie samo to przyznaje, tyle że na końcu
wiersza. Pomiar wydajności, który nie obciąża tego, co obiecuje obciążyć, jest bramką
bez zębów, a na tej liczbie ma stanąć 6.D2.

## 2. Mechanizm pierwszy: okno krótsze niż jeden odstęp

Składy są zgłaszane na krok `i × odstęp` (`LineBudgetScenario.Build`). Przy
`--headway-s 120` odstęp to **14 400 kroków**, a `--steps 1000` daje okno **8,3 s**.
Skład numer 1 zostaje zgłoszony na krok 14 400, czyli **poza oknem pomiaru** —
i tak samo każdy następny. `N_max = 1` niezależnie od `--trains`. To nie jest błąd
w wpuszczaniu; to okno.

```
--- headway=120 s, steps=1000  (okno 8 s)
[BUDŻET]  1;1;1.00;0.00;184223;…;0.07
[BUDŻET]  2;1;1.00;0.00;170097;…;0.07
[BUDŻET]  4;1;1.00;0.00;181376;…;0.07
[BUDŻET]  8;1;1.00;0.00;159604;…;0.08
[BUDŻET] 32;1;1.00;0.00;116318;…;0.10

--- headway=120 s, steps=200000  (okno 1667 s)
[BUDŻET]  1; 1;1.00;0.00;1735933;…;0.01
[BUDŻET]  2; 2;1.93;0.00; 825831;…;0.01
[BUDŻET]  4; 4;3.57;0.00; 477685;…;0.03
[BUDŻET]  8; 8;5.98;0.00; 213603;…;0.06
[BUDŻET] 32;12;7.25;0.20; 152643;…;0.08
```

Kolumny: `N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;…;%budżetu`.

## 3. Mechanizm drugi: sufit **12** składów na tej osi

Przy oknie 1667 s i odstępie **30 s** oraz **10 s** — dwie różne wartości
`--headway-s`, jak żąda pole „Skończone, gdy" — `N_max` przestaje rosnąć na **12**:

```
--- headway=30 s          --- headway=10 s
[BUDŻET]  4; 4;3.71;0.18   [BUDŻET]  4; 4;3.71; 0.25
[BUDŻET]  8; 8;6.25;1.25   [BUDŻET]  8; 8;6.25; 1.58
[BUDŻET] 32;12;7.56;15.51  [BUDŻET] 32;12;7.56;21.47
```

Sufit potwierdzony osobnym przebiegiem, w którym rośnie wyłącznie kolumna „czeka":

```
--- headway=10 s, steps=200000
[BUDŻET]  9; 9;6.69; 2.09;220265;…;0.05
[BUDŻET] 12;12;7.56; 4.05;166818;…;0.07
[BUDŻET] 13;12;7.56; 4.97;168748;…;0.07
[BUDŻET] 16;12;7.56; 7.72;167589;…;0.07
[BUDŻET] 24;12;7.56;14.79;152763;…;0.08
```

`N_max` i `N_śr` są dla 12, 13, 16 i 24 **identyczne co do cyfry**; przybywa tylko
składów czekających. Mechanizmem jest **brama wjazdowa**: `LineCore` wpuszcza skład
wyłącznie wtedy, gdy żaden blok nakładający się na obrys składu w punkcie wjazdu nie
jest zajęty (`EntryIsClear`), a plan ma 23 bloki na całej osi. To nie jest błąd i ta
pozycja go nie poprawia — to pojemność planu przy tych nastawach.

## 4. Co z tego wynika dla 6.D2

Bramka 6.D2 ma wywracać job, gdy koszt kroku przy **9 składach** przekroczy próg.
Dziewięć jest osiągalne: przy odstępie 10 s i oknie 200 000 kroków `N_max = 9`
dla `--trains 9`. Zmierzony koszt:

| składy na planie | µs/krok | % budżetu 1/120 s |
|---|---|---|
| 9 | 4,540 | 0,05 |
| 12 (sufit) | 5,995 | 0,07 |

Żeby taki pomiar cokolwiek znaczył, komenda bramki musi mieć **okno dłuższe niż
(N−1) × odstęp**, inaczej mierzy jeden skład i nazywa to dziewięcioma.

## 5. Zauważone przy okazji, nietknięte

`data/design/signalling/cbtc-test-2026.json` **nie daje się wczytać** przez
`SignallingPlan.FromJson`: plik jest opisem obszaru i trybu (`area_id`, `mode`,
`status`), nie planem bloków. Wyjątek `KeyNotFoundException` **nie jest łapany**
przez wspólny handler w `Program.Main` (ten łapie `IOException`,
`ArgumentException`, `FormatException`, `InvalidOperationException`), więc proces
kończy się kodem **134** i stosem wywołań zamiast odmowy. Dopisane do kolejki
jako **6.A13**; ta pozycja tego nie poprawia.
