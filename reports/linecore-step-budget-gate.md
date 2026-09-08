# Bramka na koszt kroku `LineCore.Step` (6.D2)

**Zmierzone 06.09.2026 na commicie:** `b45be99c072d87882ecf84f52129f891f324b1ee`
**Przepisane 08.09.2026 na commicie:** `8b4cf7cf20811e9d86ca976b035b07a4b453f844` — sekcje 4 i 8; sekcje 1-3, 5-7
zostaja zapisem pomiaru z 06.09.2026 i nie sa przeliczane.

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

## 4. Próg: **14,0 µs/krok** — przepisane 08.09.2026

Ta sekcja jest **przepisana, nie dopisana obok**: do 08.09.2026 mówiła „Próg: 8,0 µs/krok"
i podawała dobór 1,71× nad najwyższym znanym pomiarem. Metoda była poprawna wobec tego,
co wtedy znano, i **na puli runnerów właściciela się złamała** — więc zostaje tu wypisana
jako historia doboru, a nie jako obowiązująca reguła.

### 4.1 Kalibracja pierwotna, 06.09.2026 — zapis pomiaru, zostaje bez zmian

| liczba | skąd |
|---|---|
| 3,798 µs | najwyższy z trzech przebiegów na kontenerze sesji |
| 4,665 µs | najwyższy znany wtedy pomiar tego scenariusza (§8.4 `reports/linecore-budget.md`, `dfbde8f`) |
| 8,0 µs | próg pierwotny — **1,71×** nad najwyższym znanym wtedy pomiarem |

Margines miał pochłonąć trzy rzeczy, których tamta sesja nie znała: **prędkość runnera
właściciela**, obciążenie maszyny w chwili przebiegu i przyrost kosztu od zmian
w rdzeniu, które nie są regresem. Precedens: 6.D11 ustawiła budżet czasu zestawu
narzędzi jako dwukrotność najwyższego zmierzonego przebiegu, z tego samego powodu.

### 4.2 Co pierwszy z tych trzech nieznanych okazał się wart

Pula `woogitsu` zaczerwieniła bramkę na pomiarach, które **ona sama uznała za mierzalne**
— czyli nie na niemierzalności z 6.D41, tylko na porównaniu z progiem, którego bramka nie
wstrzymała. Wklejone z logów jobów, nie przepisane z pamięci:

```
woogitsu-linux-04 (katalog woogitsu-host-04), run 34194126232 próba 1, 06:24:52
BLAD: koszt kroku 9.572 us przekracza prog 8.000 us
[BUDZET-BRAMKA] zgloszonych 32, na planie 9 (srednio 5.08, czeka 0.98); 9.572 us/krok
                przy progu 8.000; 0.110 % budzetu klatki; rozstep powtorzen 33.9 %

woogitsu-linux-02 (katalog woogitsu-host-02), run 34194126232 próba 2, 07:17:30
BLAD: koszt kroku 8.554 us przekracza prog 8.000 us
[BUDZET-BRAMKA] zgloszonych 32, na planie 9 (srednio 5.08, czeka 0.98); 8.554 us/krok
                przy progu 8.000; 0.100 % budzetu klatki; rozstep powtorzen 23.1 %
```

Próba 3, `woogitsu-linux-03`, przeszła na **tej samej treści kodu**. Na kontenerze tej
sesji trzy przebiegi tego samego scenariusza dały **4,356 / 4,413 / 4,500 µs** przy
rozstępie 3,9–10,5 %, wszystkie kodem 0.

Dwie rzeczy warto z tego zapisu wyjąć osobno, bo obie prostują mój własny wcześniejszy
zapis w commicie scalającym #406.

**Pierwsza: przebiegów odrzuconych było DWA, nie jeden.** Tamten commit nazwał tylko
8,554 µs. Najwyższy odrzucony pomiar mierzalny to **9,572 µs**, i to on, a nie 8,554,
jest dolnym ograniczeniem nowego progu — więc niekompletny zapis dałby próg **o 1 µs
za nisko**.

**Druga: „woogitsu-host-02" i „woogitsu-linux-02" to ta sama maszyna.** Nazwa
zarejestrowanego runnera to `woogitsu-linux-02`, a katalog roboczy w tych samych logach
to `/home/matma/actions-runner/woogitsu-host-02/_work/…`. Tak samo dla `-04`. Dwie
„rodziny nazw" z `CLAUDE.md` §9 są więc co najmniej częściowo jednym zbiorem maszyn
widzianym przez dwie nazwy — a §9 mówi wprost, że liczby maszyn nie da się sprawdzić
z repozytorium, i to jest kolejny powód, dla którego jej tam nie ma.

### 4.3 Decyzja właściciela z 08.09.2026 i skąd bierze się 14,0

Pytanie poszło do właściciela w formie klikalnej z trzema wariantami. **Rekomendowałem
inny wariant niż wybrany** — i to zdanie jest tu celowo, bo bez niego nie widać, czym
ten próg dziś jest. Wybrana odpowiedź: **podnieść próg powyżej najwolniejszej maszyny**.

Wartość jest **obustronnie wyprowadzona z pomiarów**, nie wybrana wygodnie:

| ograniczenie | liczba | dlaczego stąd |
|---|---|---|
| od dołu | **> 9,572 µs** | najwyższy koszt, który bramka porównała z progiem i **odrzuciła**. To jest dosłowna treść decyzji: próg ponad najwolniejszą maszyną |
| od góry | **< 16,022 µs** | koszt zaobserwowany 07.09.2026 przy rozstępie 115,9 %, który bramka nazywa **niemierzalnym**. Próg stojący nad liczbą, którą bramka już widziała, przestaje być zapasem nad czymkolwiek |
| **wybrane** | **14,0 µs** | **1,46×** nad ograniczeniem dolnym, **12,6 %** pod górnym; **0,168 %** budżetu klatki 1/120 s |

**Metody z §4.1 nie dało się zastosować wprost, i to jest wynik rachunku, nie wygoda:**
1,71 × 9,572 = **16,4 µs**, czyli **powyżej ograniczenia górnego**. Dawny sposób doboru
kolidowałby dziś z własnością, której nie wolno stracić — dlatego §4.1 zostaje jako
historia, a nie jako reguła.

### 4.4 Cena, zmierzona i nieukryta

| | próg 8,0 | próg 14,0 |
|---|---|---|
| stosunek do pomiaru na maszynie niezajętej (4,500 µs) | 1,78× | **3,11×** |
| jaki regres przechodzi na zielono | podwojenie kosztu — nie | **potrojenie kosztu — tak** |

Zmiana **trojąca** koszt kroku na cichej maszynie przechodzi dziś na zielono. To jest
cena za to, żeby joby nie czerwieniły się od obciążenia puli, i taki był wybór
właściciela — wybór jego, zapis mój.

Drugi warunek — **1,0 % budżetu klatki** — zostaje bez zmian: jest zapasowy i grubszy,
łapie sytuację, w której ktoś zmieni `FixedStep.SimulationHertz` i mikrosekundy
przestaną znaczyć to, co dziś. Przy progu 14,0 µs jest od niego **6-krotnie** dalej niż
przy 8,0, więc jako drugie zdanie o wydajności znaczy jeszcze mniej niż znaczył.

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

> **Adnotacja z 08.09.2026.** Wklejone wyżej wyjście zostaje **nieprzeliczone** — to zapis
> pomiaru z 06.09.2026. Atrapa, na której KONTROLA 1 chodzi dziś, niesie **15,500 µs**,
> nie 9,091: przy progu podniesionym na 14,0 µs (§4.3) wartość 9,091 mieści się w progu,
> więc kontrola żądająca odmowy pytałaby o coś innego, niż mówi jej nazwa. Wartość stoi
> teraz w jednym miejscu (`WOLNY` w module testowym), a nie w trzech — §8.

## 7. Czego ta bramka NIE mierzy, świadomie

**Przejazdu z wybiegiem.** Mierzony jest przejazd **bez wybiegu**. Bramka mówi to
w wypisie przy każdym przebiegu, zamiast milcząco mierzyć jeden wariant i nazywać go
„kosztem kroku".

> **Adnotacja z 06.09.2026 (6.A18).** Pomiar powyżej zostaje nietknięty — zmienia się
> tylko powód tego zdania. Gdy je pisano, `budget` **nie znał** `--coast-from-m`, więc
> pomiar z wybiegiem był niewykonalny. Od 6.A18 zna, i brak wybiegu jest tu **wyborem**:
> `coast_from_m: null` stoi w `tools/ci/linecore-step-budget.json` i stamtąd biorą go
> naraz wywołanie i zdanie w wypisie. `null` zostaje, bo próg pochodzi
> z przejazdów bez wybiegu — wartości progu tu **nie ma** i to jest poprawka
> z 08.09.2026: stała tu kopia liczby („8,0 µs") i przy podniesieniu progu
> zdanie stałoby się nieprawdziwe w środku akapitu o tym, żeby liczb nie
> dublować, a wybieg zmienia **przejazd**, nie tylko jego koszt —
> zmierzone przy 6.A18 na tej samej osi: `N_śr` 6,69 bez wybiegu, 6,67 przy 250 m,
> 6,40 przy 120 m, przy `µs/krok` nierozróżnialnym w szumie (3,73–3,84). Pomiar
> z wybiegiem wymaga więc **nowego progu i nowego raportu**, nie samej liczby w polu.

**Progu klatki z ekstrapolacji `N ≈ 330–390`.** `reports/linecore-budget.md` §7 mówi
wprost, że to ekstrapolacja **56–65× poza zakres pomiaru** (N ≤ 6,9). Pole „Poza
zakresem" pozycji 6.D2 wyklucza ją z bramki i to zostaje.

**Regresu mniejszego niż margines — i to pasmo się 08.09.2026 POSZERZYŁO.** Akapit
mówił „próg 1,71× nad najwyższym znanym pomiarem złapie regres rzędu dwukrotności, nie
dwudziestu procent"; przy progu 14,0 µs i pomiarze 4,500 µs na maszynie niezajętej
mnożnik wynosi **3,11×**, więc bramka nie złapie już nawet **potrojenia** kosztu kroku.
Zdanie jest przepisane, a nie dopisane obok, bo stara liczba mówiłaby o czułości, której
ta bramka nie ma. To jest cena za to, żeby bramka nie świeciła czerwono od obciążenia
puli (§4.4) — i jedyne, co ją częściowo odrabia, zostaje bez zmian: wypis podaje
zmierzoną wartość przy **każdym** przebiegu, więc dryf w tym paśmie jest widoczny
w logu, nawet kiedy bramka jest zielona. Jest to jednak widoczność dla **czytającego
log**, nie bramka — i po tej zmianie jest to warte powiedzenia wprost.

## 8. Co bramka po tej zmianie sprawdza WIĘCEJ (08.09.2026)

Podniesienie progu **osłabia** bramkę — to jest cała §4.4. Reguła projektu mówi, że
bramkę blokującą zmianę się **przekierowuje**, a po przekierowaniu ma sprawdzać więcej,
nie mniej. Tu blokującą bramką był sam próg, więc kompensata idzie w to, czego do
08.09.2026 **nie sprawdzało nic**.

**Wartości progu nie pilnowała żadna asercja.** `spread_pct_max` ma swoje ograniczenie
wyprowadzone od 6.D41 (`test_granica_rozstepu_jest_POWYZEJ_udokumentowanych_pomiarow_zielonych`),
a `microseconds_per_step_max` nie miał **żadnego**: dało się go ustawić na 100 µs i ani
jeden test by nie drgnął. Teraz trzyma go ograniczenie **obustronne**, oba końce z pomiaru
(`test_prog_kosztu_kroku_lezy_MIEDZY_pomiarem_odrzuconym_a_niemierzalnym`).

**Atrapa odmowy czasowej stała w CZTERECH kopiach — i czwartej nie znalazłem sam.**
Wyrażenie `.replace(…, ";9.091;…")` było wpisane osobno w **trzech** testach żądających
odmowy. Przy progu 14,0 µs 9,091 µs **mieści się w progu**, więc wszystkie trzy zaczęłyby
żądać odmowy od pomiaru zielonego. Atrapa ma teraz jednego pisarza (`WOLNY` = 15,500 µs)
i asercję wiążącą ją z progiem
(`test_atrapa_WOLNA_lezy_POWYZEJ_progu_wiec_odmowa_nie_jest_pusta`).

**Czwarta kopia siedziała w YAML-u i znalazło ją CI, nie ja.** Pierwsze uruchomienie
pull requesta z tą zmianą przeszło krok 16 (bramka kosztu kroku, zielono na progu 14,0)
i **wywróciło się na kroku 17** — kontroli negatywnej wpisanej wprost w
`.github/workflows/sim-tests.yml`, która drukuje własną atrapę z literałem `9.091`
(job `101988401447`, `woogitsu-linux-03`, 08.09.2026). Odtworzone lokalnie:

```
=== ODTWORZENIE AWARII: stara atrapa 9.091 przy progu 14,0 ===
[BUDZET-BRAMKA] ... 9.091 us/krok przy progu 14.000; rozstep powtorzen 9.1 %
  -> bramka: kod 0    (przyjęła — więc kontrola CI mówi „bramka przyjęła krok
                       wolniejszy od progu" o pomiarze, który wolniejszy NIE BYŁ)

=== PO POPRAWCE: atrapa wyliczona z progu ===
  wolny_us=15.400  wolny_pct=0.18
BLAD: koszt kroku 15.400 us przekracza prog 14.000 us
  -> bramka: kod 1    (odmówiła — kontrola CI przechodzi)
```

**Uzasadnienie, dla którego ten literał tam stał, było zapisane i było prawdziwe — do
tego dnia.** Docstring `test_the_threshold_lives_in_one_place_and_the_step_does_not_compare_anything`
mówił, że zmyślone liczby pomiaru w kroku kontroli „**mają** być literałami, bo udają
wyjście `budget`". Dla kolumn opisujących **kształt** przejazdu (obsada, mediany, rozstęp)
jest to prawda i one literałami zostają. Dla **jednej** kolumny — µs/krok atrapy „wolnej"
— było fałszem, bo ta kolumna musi leżeć powyżej progu, żeby kontrola cokolwiek znaczyła.
Jest dziś **wyliczana z progu** w kroku CI, a nie wpisana; docstring jest **przepisany,
nie dopisany obok**, i pilnuje tego
`test_atrapa_w_KROKU_CI_nie_jest_literalem_ponizej_progu`, który czyta wiersze `[BUDŻET]`
z treści kroku i odrzuca literał poniżej progu (podstawienie z powłoki przechodzi — o to
właśnie chodzi). To jest ta sama rodzina usterki co w 6.D40: obietnica „mechanicznie, nie
tablicą wyjątków" była prawdziwa wobec przypadków, dla których ją napisano, i złamała się
na pierwszym nowym.

**Dwie stałe zależą od siebie i nikt tego nie zapisywał.** Dolne ograniczenie progu
(9,572 µs) wzięte jest z przebiegu, którego rozstęp wynosił **33,9 %** — czyli obowiązuje
tylko dopóki `spread_pct_max` ten pomiar przepuszcza. Komentarz tej stałej **zapowiada
zaciskanie** granicy, a zaciśnięcie poniżej 33,9 % zamieniłoby tamten przebieg
w niemierzalność (kod 3) i podstawa progu wisiałaby w powietrzu. Sprzężenie pilnuje
`test_prog_i_granica_rozstepu_sa_SPRZEZONE`: zaciśnięcie granicy poniżej 33,9 % **czerwieni
się natychmiast** i każe przeliczyć podstawę progu w tej samej zmianie.

Czego w tym commicie **nie ma, świadomie**: granicy rozstępu nie zacisnąłem. Piąty pomiar
(33,9 % → 9,572 µs, czyli 2,1× maszyny niezajętej) jest argumentem, że 50 % przepuszcza
pomiary mówiące o obciążeniu, a nie o kodzie — ale zaciśnięcie jest **inną decyzją** niż
podjęta przez właściciela, a dwie decyzje w jednym commicie nie dają się potem rozdzielić.
Pomiar jest dopisany do komentarza stałej, więc nie zginie.

### 8.1 Kontrole negatywne — WYKONANE 08.09.2026

Wszystkie **pięć** na module testowym bramki (17 → 21 testów), każda z czyszczeniem
`__pycache__` przed przebiegiem — po 6.D41, gdzie mutacja o identycznej długości
zostawiła nieświeży bajtkod.

```
=== KN-1: próg cofnięty do 8,0 (stan przed decyzją) ===
FAIL: 1 ['test_prog_kosztu_kroku_lezy_MIEDZY_pomiarem_odrzuconym_a_niemierzalnym']

=== KN-2: próg podniesiony na 20,0 (ponad niemierzalny 16,022) ===
FAIL: 5 ['test_a_slow_step_is_refused',
         'test_atrapa_WOLNA_lezy_POWYZEJ_progu_wiec_odmowa_nie_jest_pusta',
         'test_dwa_werdykty_maja_DWA_ROZNE_kody_wyjscia',
         'test_prog_kosztu_kroku_lezy_MIEDZY_pomiarem_odrzuconym_a_niemierzalnym',
         'test_wolny_krok_przy_ZNOSNYM_rozstepie_nadal_jest_odmowa']

=== KN-3: granica rozstępu zaciśnięta do 30 % (poniżej 33,9 %) ===
FAIL: 1 ['test_prog_i_granica_rozstepu_sa_SPRZEZONE']

=== KN-4: atrapa WOLNY cofnięta do 9.091 (mieści się w progu 14,0) ===
FAIL: 4 ['test_a_slow_step_is_refused',
         'test_atrapa_WOLNA_lezy_POWYZEJ_progu_wiec_odmowa_nie_jest_pusta',
         'test_dwa_werdykty_maja_DWA_ROZNE_kody_wyjscia',
         'test_wolny_krok_przy_ZNOSNYM_rozstepie_nadal_jest_odmowa']

=== KN-5: atrapa w YAML-u cofnięta na literał 9.091 (stan, który wywalił job 17) ===
FAIL: 1 ['test_atrapa_w_KROKU_CI_nie_jest_literalem_ponizej_progu']

=== stan po przywróceniu ===
4b0a66879a6662891954155c16d5fb3c  .github/workflows/sim-tests.yml   (zgodne z kopią)
f8537104ea7092a4dc6885f56d4df16f  tools/ci/linecore-step-budget.json
f8537104ea7092a4dc6885f56d4df16f  (kopia sprawdzona)
a2f1b160a501034d1921659eb4a9ded7  tools/tests/test_linecore_budget_gate.py
a2f1b160a501034d1921659eb4a9ded7  (kopia sprawdzona)
FAIL: 0 []
```

**KN-2 jest tu najważniejsza i to nie z powodu liczby pięć.** Próg pchnięty ponad koszt,
który bramka nazywa niemierzalnym, wywraca nie tylko asercję ograniczeń — wywraca też
**trzy testy żądające odmowy czasowej i asercję atrapy**, bo przy takim progu żadna atrapa
nie stoi już nad nim. To jest dokładnie ten stan, w którym bramka wygląda na działającą
i nie odrzuca niczego. **KN-1** pokazuje drugą stronę: przy progu 8,0 czerwieni się
asercja ograniczeń, czyli powrót do stanu przed decyzją właściciela nie da się przemycić
po cichu.

### 8.2 Pomiar na kontenerze po zmianie

```
[BUDZET-BRAMKA] zgloszonych 32, na planie 9 (srednio 5.08, czeka 0.98); 4.500 us/krok
                przy progu 8.000; 0.050 % budzetu klatki; rozstep powtorzen 6.3 %
[BUDZET-BRAMKA] ... 4.413 us/krok przy progu 8.000; rozstep powtorzen 3.9 %
[BUDZET-BRAMKA] ... 4.356 us/krok przy progu 8.000; rozstep powtorzen 10.5 %
przebieg 1/2/3: kod 0
```

Te trzy przebiegi zrobiono **przed** zmianą progu i dlatego wypisują 8.000 — to jest zapis
pomiaru, więc zostaje z liczbą, którą wtedy wypisał. Oba przebiegi, które próg odrzucił
(§4.2: 9,572 i 8,554 µs), przechodzą pod progiem 14,0 µs; przebieg niemierzalny (16,022 µs
przy 115,9 %) **nadal wychodzi kodem 3**, bo strażnik rozstępu wstrzymuje porównanie
niezależnie od wartości progu — sprawdzone na atrapie w KN-owym przebiegu wyżej.
