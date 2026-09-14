# MB-06 — jeden skład, dwa źródła komend, JEDNA droga

**14.09.2026**, na `4f02e81`, gałąź `claude/mb06-wspolne-komendy`. Wejście:
`src/Sim/Line/LineCore.cs`, `src/Sim/Train/LineDrive.cs`, `StationService.cs`,
`TrainController.cs`, sygnalizacja, Issue #26.

## 1. Zakres T-320 sprawdzony przed pracą, tak jak każe pole „Zależy od"

| etap T-320 | stan |
|---|---|
| etap 1 — `LineDrive` krokowany z zewnątrz | zrobione (#123) |
| etap 2 — `LineCore`, N składów, trzy fazy kroku | zrobione |
| nawrót na oba końce osi | zrobiony (#218), czas zmierzony z GTFS |
| takt 5:10/5:40, 48 kursów, 71 obiegów | **zostaje** |

MB-06 nie dotyka ani jednej z rzeczy, które w T-320 zostają. Warunek spełniony.

## 1a. DZIURA W OCHRONIE, KTÓRĄ TA POZYCJA NAJPIERW WPUŚCIŁA — i jak została znaleziona

**Pierwsze podejście do MB-06 zostawiło gałąź, w której komenda maszynisty omijała
ochronę.** Znalazł to audyt, nie ja, i nie znalazł go żaden z jedenastu testów, które
wtedy napisałem.

`LineDrive.Step` ma DWA wywołania `_controller.Advance`. Gałąź jazdy (dziś wiersz ~373)
ma nad sobą `Supervisor`. Gałąź postoju kończy się **własnym `return true`** osiemdziesiąt
wierszy wcześniej — i szła z `held` prosto do kontrolera. Dla autopilota nie znaczyło to
nic, bo autopilot trzyma tam pełny hamulec służbowy. Od MB-06 `wanted` bywa jednak
komendą **człowieka**, a `StationStop.Filter` zeruje wyłącznie `Throttle` i tylko poza
fazą `Closed`; **`Brake` nie rusza NIGDY**.

Zmierzone, zanim poprawka powstała:

| co | ile |
|---|---|
| kolejnych kroków postoju bez ANI JEDNEGO wywołania ochrony | **2220** (18,5 s) |
| staczanie na pochyleniu −3 % przy **otwartych** drzwiach | **38,27 m** |
| prędkość osiągnięta w fazie drzwi `Open` | **4,44 m/s (16 km/h)** |
| udział gałęzi postoju w prawdziwym przejeździe L1_A | **25,32 %** (21 780 z 86 032 kroków) |

Ruch był meldowany sygnalizacji przez `MoveTrain`, a ochrona nie była o nic pytana.

**Dlaczego KN-1 tego nie złapało.** Mutowało wiersz w gałęzi **jazdy** — czyli tej,
która ochronę ma. Gałąź, która jej nie miała, leżała poza zasięgiem kontroli negatywnej.
Wszystkie `TakeControl` w testach padały w JEŹDZIE (kroki 60/600/1200/5400); słowo
„drzwi" nie występowało w `ControlOwnerTests.cs` ani razu poza komentarzem klasy.

**Poprawka** to jeden wiersz — `held = Supervisor is null ? held : Supervisor(held);`
zaraz po filtrze drzwi — i **cztery nowe testy**, które pytają o tę gałąź wprost.
Kolejność jest treścią: najpierw DRZWI (czy wolno ciągnąć), potem OCHRONA (czy wolno
jechać tak szybko).

**Autopilot nie drgnął o bit** — sprawdzone tymi samymi trzema wariantami co w §3,
sumy MD5 identyczne z pomiarem sprzed MB-06.

## 1b. `TakeControl` przed wjazdem był CICHYM BRAKIEM SKUTKU

Druga rzecz z tego samego audytu. Dokumentacja `TakeControl` obiecywała, że skład
jeszcze poza planem „dostanie dźwignię przy wjeździe". Nieprawda: `Drive` powstaje
w fazie 1 tego samego kroku, a jego `LastCommand` jest wtedy jeszcze **inicjalizatorem
pola** (`Coast`, czyli `default(DriverCommand)`), bo `Step` jeszcze nie biegł.

Zmierzone skutki: przejęty przed wjazdem skład miał po 100 s **0,000 m i 0,000 m/s**
wobec **997,498 m i 16,667 m/s** pod autopilotem, stał na kilometrażu wjazdowym
i **blokował blok wjazdowy** — drugi skład po 250 s wciąż nie był na planie.

Dziś jest to **odmowa** z nazwanym powodem, tą samą drogą co `Drive(...)` na składzie
prowadzonym przez autopilota. Ciekawostka z kontroli negatywnej: mutacja przywracająca
stare zachowanie **nie kompiluje się** w postaci dosłownej — analiza nullowalności sama
odrzuca `train.Drive.LastCommand` bez strażnika. Musiałem napisać ją jako zachowanie
(cichy `return`), żeby kontrola była uczciwa.

## 2. Rozstrzygnięcie, z którego wynika cała reszta

**Komendy gracza NIE wchodzą przez `Supervisor`.** Byłoby to wygodne — hak już jest,
przyjmuje `DriverCommand` i zwraca `DriverCommand` — i byłoby błędem, który pole
„Pułapka wypisana w audycie" nazywa wprost.

`Supervisor` jest **ochroną**: stoi ZA poleceniem i może je tylko przyciąć. Gracz
potrzebuje czegoś innego: **źródła** polecenia, które staje w miejsce autopilota.
Wepchnięcie jednego w drugie zamieniłoby ochronę w drugie wejście, przez które da się
ją wyłączyć.

Stąd dwa osobne haki w `LineDrive`:

```
DriverInput   — ŹRÓDŁO polecenia; null = prowadzi autopilot
Supervisor    — OCHRONA; stoi za oboma, bez gałęzi omijającej
```

Kolejność w kodzie jest tożsama z tym zdaniem:

```csharp
command = DriverInput ?? command;                                   // źródło
LastCommand = command;
command = Supervisor is null ? command : Supervisor(command);       // ochrona
```

**Na postoju dźwignia też należy do właściciela, ale drzwi rozstrzygają.** Komenda
maszynisty wchodzi JAKO ARGUMENT tego samego `StationStop.Filter`, a nie obok niego —
`Filter` jest jedynym miejscem posuwającym licznik cyklu drzwi i musi zostać zawołane
dokładnie raz na krok.

## 3. Bez komend gracza nie zmienia się ANI JEDEN BIT — zmierzone

Nie „testy przechodzą", tylko bezpośredni pomiar: ten sam przejazd linii policzony
kodem **sprzed** zmiany (przez `git stash`) i **po** niej.

```
7648d73201d754e1e7b3b49a1aa5d539  build/t400/mb06/po.csv
7648d73201d754e1e7b3b49a1aa5d539  …/przed.csv
ŚLAD IDENTYCZNY CO DO BAJTU
```

86 033 wiersze śladu, ta sama suma MD5. Pole „Skończone, gdy" żąda dokładnie tego.

## 4. Przejęcie i oddanie nie ruszają składu

Autopilot **liczy swoje polecenie i posuwa swój zatrzask hamowania przez CAŁY czas
przejęcia**, i to jest decyzja, nie przeoczenie. Gdyby zatrzask zamarł, oddanie
sterowania wznawiałoby autopilota ze stanem sprzed przejęcia — a najgorszy przypadek
jest zmierzony i nazwany w T-320: autopilot z wyzerowanym zatrzaskiem, stojący przed
autorytetem, **pełznie 0,30 m w 58 s**.

Dźwignia przy przejęciu startuje z `LineDrive.LastCommand`, czyli z polecenia PRZED
ochroną, które autopilot wydał krok wcześniej. Przejęcie od zera nastawnika zmieniłoby
prędkość już w następnym kroku, a wyglądałoby na „samo przełączenie".

Najostrzejsza postać tego zdania jest testem: przejąć i natychmiast oddać, nie dotykając
dźwigni, a potem porównać **cały dalszy ślad** z przejazdem, w którym nikt niczego nie
brał — punkt po punkcie, przy tolerancji **0**.

## 5. Dźwignia TRWA do zmiany

Nastawnik jest dźwignią, nie przyciskiem. Komenda wygasająca po kroku dałaby skład,
który przy każdej zgubionej klatce przechodzi na wybieg — czyli sterowanie zależne od
tego, jak szybko rysuje się obraz. Ta sama zasada, co w kabinie.

Przy oddaniu dźwignia jest **zapominana**: zostawiona kazałaby następnemu przejęciu
zacząć od komendy, której skład w tej chwili nie wykonuje.

## 6. Odmowa zamiast cichego braku skutku

`Drive(trainId, command)` na składzie prowadzonym przez autopilota **rzuca**, a nie
zapisuje w próżnię. Cichy brak skutku wygląda w logu tak samo jak sterowanie, które nic
nie daje — wołający wierzyłby, że prowadzi, a prowadziłby autopilot. Nieznany
identyfikator też jest odmową, z tym identyfikatorem w treści.

## 7. DWA WZORCE TESTOWE BYŁY ZŁE I JEST TO ZAPISANE, a nie po cichu poprawione

Oba padły. W obu przypadkach **rację miał kod, a nie mój test**.

**Wzorzec pierwszy — „drugi skład zamarł".** Zatrzymywałem skład A pełnym hamulcem
i sprawdzałem, czy B jedzie dalej. B stał: `46.69 m -> 46.69 m`. Dopisałem do
komunikatu bramki stan sygnalizacji i on powiedział, o co chodzi:

```
skład B zamarł: 46.69 m -> 46.69 m; A na 626.54 m, autorytet B do 47.00 m (OccupiedBlock)
```

Skład ma **94 m**, więc ogon A stał na 532,54 m — WCIĄŻ w bloku `S01 [47, 553)`.
B stał słusznie. Źle postawione było pytanie: żeby zapytać, czy przejęcie JEDNEGO składu
dotyka drugiego, maszynista A musi prowadzić tak, żeby nie blokować linii. Druga wersja
(A pod pełną trakcją, ale 5 s) nadal padała, bo A nie zdążył zwolnić bloku; trzecia
stepuje 30 s i przechodzi.

**Wzorzec drugi — „dwie sekundy pełnego hamulca".** Stepowałem 240 kroków i oczekiwałem
zera. Krok wynosi **1/120 s**, więc 240 kroków to 2 s, a nie 2 s hamowania z 13 m/s przy
1,1 m/s² — na to trzeba niecałych 12 s. Test padał na 11,06 m/s i nie mówił nic
o dźwigni, tylko o mojej arytmetyce. Dziś stepuje 2400 kroków.

## 8. Pięć kontroli negatywnych — baza 629/629, ani jedna zielona

| KN | mutacja | czerwone |
|---|---|---|
| KN-1 | komenda człowieka wpięta **ZA** `Supervisor` (omija ochronę) | 1/629 |
| KN-2 | dźwignia wygasa po kroku | 1/629 |
| KN-3 | przejęcie zeruje nastawnik zamiast brać `LastCommand` | 1/629 |
| KN-4 | komenda bez przejęcia przechodzi po cichu | 1/629 |
| KN-5 | oddanie zostawia dźwignię | 1/629 |

Po poprawce dziury w ochronie doszły trzy kolejne, baza **633/633**:

| KN | mutacja | czerwone |
|---|---|---|
| KN-6 | ochrona zdjęta z gałęzi postoju | **2/633** |
| KN-7 | ochrona PRZED drzwiami zamiast po nich | 1/633 |
| KN-8 | ciche przejęcie składu przed wjazdem | 1/633 |

`md5sum -c: OK` po każdej z ośmiu.

## 9. Czego NIE zrobiłem

- **Nie tknąłem warstwy Godota.** MB-06 jest pozycją rdzenia; mapowanie `trainId` →
  `TrainView`, wybór obserwowanego składu i HUD właściciela sterowania to **MB-07**,
  i wypisane są w jego polu „Wyjście", nie w tym.
- **Nie rozszerzyłem zapisu wejść o przejęcia.** Pole „Wyjście" mówi „jeśli replay tego
  wymaga" — dzisiejszy `--replay` prowadzi JEDEN skład kabiną i nie zna `LineCore`,
  więc nie wymaga. Rozszerzenie formatu bez wołającego byłoby przybiciem kształtu,
  którego nikt nie czyta.
- **Nie zmieniłem ani jednego parametru trakcji** (pole „Poza zakresem").

## 9a. Trzy asercje, które niczego nie bramkowały

Ten sam audyt policzył, że w `ControlOwnerTests.cs` trzy asercje są **tożsamościami**:
dwie porównują wartości odczytane z tego samego obiektu bez kroku symulacji pomiędzy,
a trzecia porównuje `Drive.LastCommand` z tym, co `TakeControl` z niego przepisało.
Czwarta — pętla po śladzie — przechodziła także przy `0 == 0`, bo brakowało strażnika
niepustości, który ma jej bliźniak dwadzieścia wierszy niżej.

Dołożone: strażnik `Count > 0` i `AreNotEqual(Coast, …)`, który przybija przesłankę
„na kroku 1200 autopilot NIE jest na wybiegu" — bo bez niej asercja o dźwigni
rozróżniała mutację wyłącznie przez przypadek.

## 10. Co zauważyłem po drodze

- `Assert.ThrowsException` przyjmuje komunikat jako argument **drugi, po lambdzie**,
  i dlatego łatwo go pominąć — bramka
  `test_lista_asercji_C_bez_komunikatu_moze_tylko_malec` złapała u mnie pięć takich
  asercji, w tym te dwie. Dopisałem komunikaty, zamiast wpisywać plik na listę wyjątków.
- Liczba typów wyliczeniowych w `src/` **ruszyła drugi raz w ciągu doby** (MB-02, MB-06),
  więc zdanie „stoi nieruchomo od 02.09.2026" zniknęło z komentarza i z komunikatu
  bramki. Teza 6.D198 zostaje zawężona, nie obalona: `ControlOwner` nie dokłada ani
  jednej nazwy dwuznacznej — `NazwyDwuznaczneWSrc` nie drgnęło — więc jest przypadkiem
  odwrotnym niż `TrainingEnding`.
