# 6.D149 — próg zostaje jeden, a `werdykt` dostaje maszynę; rozstrzyga liczba 219,9

**12.09.2026**, na `8333f3e`. Wejście: `tools/tests/test_suite_runtime_budget.py`,
`reports/mierzalnosc-czasu-zestawu.md`. Pozycja: podłoga mierzalności (0,75) powstała
po to, żeby czas maszyny **obciążonej** nie trafiał do porównania z progiem; kontener
**spokojny** ma 0,991, leży wysoko nad podłogą, a jego czas ściany (170,685 s)
przekracza próg 150 s.

## 1. Rozstrzygnięcie, i liczba, która je wymusza

Pole „Wyjście" pytało: jeden próg dla obu maszyn, czy `werdykt` przyjmujący maszynę.

| | |
|---|---:|
| maksimum zmierzone na **runnerze** | **116,404 s** |
| maksimum zmierzone w **kontenerze** | **170,685 s** |
| dzisiejszy próg | 150,0 s (margines **1,289×** nad runnerem) |
| **próg WSPÓLNY z tym samym zapasem** | **219,9 s** |
| …czyli wobec maksimum runnera | **1,890×** |

**Próg wspólny przestałby zauważać na runnerze regres blisko dziewięćdziesięciu
procent** — na maszynie, dla której w ogóle istnieje. To zamyka opcję „jeden próg
dla obu".

**Rozstrzygnięcie: próg zostaje jeden i zostaje przy runnerze, a maszyna wchodzi do
`werdykt` NIE po to, żeby trzymać drugi próg, tylko po to, żeby ODMÓWIĆ porównania
pomiarowi, którego ten próg nie opisuje.**

Wartość progu nie została zmieniona — pole „Poza zakresem" zabrania tego bez decyzji,
a rozstrzygnięcie tej zmiany nie potrzebuje.

## 2. Warunki są dwa i zlanie ich w jeden było usterką

| warunek | na jakie pytanie odpowiada | kontener 11.09 |
|---|---|---|
| podłoga `MIERZALNOSC_MIN` | czy ten pomiar mówi o **kodzie**, czy o maszynie | **przechodzi** (0,991 ≫ 0,75) |
| maszyna `MASZYNA_PROGU` | czy ten **próg** mówi o tej maszynie | **nie przechodzi** |

Do tej pozycji istniał tylko pierwszy, więc pomiar kontenera dostawał odpowiedź
progu, który jego nie dotyczy. Komunikat brzmiał „maszyna oddawała CPU, więc to jest
pomiar kodu" — prawda — i wyciągał z tego wniosek o progu, który prawdą nie jest.

**Kolejność jest treścią.** Maszyna rozstrzyga pierwsza, bo komunikat podłogi
obiecuje „ten pomiar nie mówi nic o kodzie", a dla spokojnego kontenera to nieprawda:
0,991 znaczy, że mówi. Nie mówi o **tym progu**.

Dziś:

```
werdykt(170.685, 169.185)                         -> (True,  'przekroczyl prog ...')
werdykt(170.685, 169.185, maszyna=kontener)       -> (False, 'prog 150.0 s jest
   skalibrowany na maszynie `runner` (z `POMIARY_RUNNERA`), a ten pomiar jest
   z `kontener` — czas sciany 170.685 s NIE JEST z nim porownywany. Stosunek
   CPU/sciana 0.991 mowi, ze pomiar jest rzetelny; mowi tylko o innej maszynie
   niz ta, ktora prog opisuje')
```

Pierwsza linia **zostaje** i nie jest usterką: domyślną maszyną jest `runner`, bo krok
„Run tool tests" stoi w `python-tests.yml`, a ten workflow ma `runs-on: self-hosted`.
CI woła `werdykt` bez argumentu i dostaje odpowiedź o sobie.

## 3. Dlaczego maszyny nie są porównywalne — to już było zmierzone

6.D135 zapisało to jako `test_runner_liczy_rownolegle_a_kontener_szeregowo`:
stosunek CPU do ściany mówi, ile rdzeni zestaw dostaje na sekundę zegara. Na runnerze
jest **powyżej jedynki** (1,599–1,971 w sześciu przebiegach), w kontenerze **poniżej**
(0,991). Ten sam kod, ta sama liczba modułów (122), a kontener jest **1,466×**
wolniejszy od maksimum runnera i **1,720×** od jego mediany.

Jeden próg czasu **ściany** porównywałby przebieg równoległy z szeregowym.

## 4. Kontrole negatywne

Baza: **19/19**. Po każdej `cp` z kopii i `md5sum -c: OK`.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | warunek maszyny zdjęty z `werdykt` | **17/19** | warunek jest tym, co zmienia odpowiedź |
| KN-2b | kolejność warunków odwrócona | **18/19** | patrz niżej |
| KN-3 | `MASZYNA_PROGU` przestawiona na kontener | **17/19** | wiązanie z `POMIARY_RUNNERA` trzyma |
| KN-4 | wpis kontenerowy dopisany do `POMIARY_RUNNERA` | **14/19** | pięć testów, w tym margines 0,879 |
| KN-5 | komunikat maszyny powołuje się na podłogę | **18/19** | dwa odmówienia mają zostać dwoma |

### KN-2 nie dało się wykonać na danych z drzewa i to jest warte zapisania

Pierwsza próba przestawienia kolejności wyszła **nierozstrzygająca**: dla kontenera
z 11.09 (stosunek 0,991) gałąź podłogi nie jest dotykana ani przed zmianą, ani po
niej, więc przestawienie warunków nie zmienia **ani jednego znaku**. Rozstrzyga
dopiero przebieg **jednocześnie z niewłaściwej maszyny i pod obciążeniem** — takiego
w `POMIARY` nie ma i mieć nie musi.

Dopisałem go jako wejście syntetyczne (`werdykt(200,0; 80,0; maszyna=kontener)`,
stosunek 0,4) razem z drugą stroną granicy (ta sama para na maszynie **właściwej**
ma nadal usłyszeć podłogę, tak jak od 6.D42). KN-2b na tej wersji jest czerwona.

Bez tego dopisania zdanie o kolejności byłoby deklaracją bez pokrycia — ta sama
sytuacja co przy KN-4 z 6.D148 i KN-6 z 6.D147, trzeci raz w trzech pozycjach.

## 5. Kolejka

Domknięcie tej pozycji zbiło kolejkę z dwunastu na **jedenaście**, więc doszły trzy
bloki. Dwa wprost z pól „Czego nie zrobiłem": **6.D159** (bramka sekwencji ucieczki
czyta `tools/`, a `tests/` i `src/` nie czyta nikt — z 6.D147) i **6.D160** (kontener
ma jeden pomiar, więc nie ma progu — z tej pozycji).

Trzeci, **6.D161**, wyszedł z rzeczy, która zdarzyła się **trzy razy pod rząd**
i dopiero przez powtórzenie dała się zobaczyć: KN-6 z 6.D147, KN-4 z 6.D148 i KN-2
stąd — wszystkie zielone, wszystkie z tego samego powodu. W drzewie stoi już kilka
zdań „ubezpieczenie, nie zmierzona konieczność", a ile z nich ma pod sobą wejście
syntetyczne, a ile jest samą deklaracją, nie policzył nikt.

Po uzupełnieniu **14 do wzięcia**.

## 6. Czego nie zrobiono

- **Nie zmieniono wartości progu** — „Poza zakresem", i rozstrzygnięcie tego nie
  wymagało.
- **Nie ruszono podłogi 0,75.** Pole „Dlaczego" pozycji mówiło wprost, że jej
  podniesienie odcięłoby zdrowe przebiegi (KN-5b z 6.D135: podłoga 0,995 zapala się
  na stosunku 0,987). Rozstrzygnięcie dotyczy progu wobec maszyny, nie podłogi.
- **Nie przyspieszono zestawu** — „Poza zakresem".
- **Nie dopisano progu dla kontenera.** Miałby n=1 na dzisiejszym drzewie; próg
  z jednego pomiaru jest liczbą wpisaną z ręki, a nie zmierzoną — dokładnie tym,
  co 6.D26 z tego pliku usuwało.
- **Nie podłączono `werdykt(maszyna=…)` do żadnego wywołania w CI.** Krok chodzi na
  runnerze, więc domyślna wartość jest tam poprawna; argument istnieje dla pomiarów
  robionych poza CI, w tym dla tego, który tę pozycję wywołał.
