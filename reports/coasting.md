# 6.A6 · Wybieg zamiast trakcji: ile kosztuje w czasie, ile oszczędza w energii

**Zmierzone 06.09.2026 na commicie:** `8bcce67db1d11137824b90abd9d654373dc91734`

(Ten SHA jest commitem tej sesji na `claude/6a6-wybieg`, który już niósł cały kod i
wszystkie testy opisane niżej — `src/` i `tests/` identyczne co do bajtu z tym, na czym
mierzono §3, §4, §5 i §6. Ostatni `git commit --amend` tej sesji dopisał do tego samego
commita wyłącznie ten akapit i wklejone wyjście zestawów w §5, więc końcowy SHA na gałęzi
różni się od powyższego o te dwa fragmenty tego raportu i o nic więcej. Ten sam kompromis,
który `tools/tests/test_report_hygiene.py` świadomie akceptuje dla SHA po squash-merge:
liczy się kształt pola, nie osiągalność obiektu.)

Zakres: `docs/TASKS.md`, 6.A6. Model: `docs/02-simulation.md`, `reports/T-310-physics.md`
(trakcja), `reports/T-311-braking.md` (hamowanie), `reports/T-401-line-run.md` §2
(rezerwy rozkładowe pakietu A, wyprowadzone z `reports/T-113-timetable.md`).
Wejście: `src/Sim/Train/LineDrive.cs`, `src/Sim/Train/LineRunSettings.cs`,
`src/Sim/Train/LineRun.cs`, `src/Sim.Runner/Program.cs`, `data/track/L1_A.json`.

---

## 0. Co zrobiłem, w jednym zdaniu

`DriverCommand.Coast` był w rdzeniu od T-310 wyłącznie jako **stan domyślny** poza fazą
ciągu i hamowania — dopisałem go jako **strategię jazdy**: `LineRunSettings.CoastFromM`
mówi, od którego metra odcinka maszynista zdejmuje nastawnik, polecenie `line`
w `Sim.Runner` dostało przełącznik `--coast-from-m`, a każde zatrzymanie niesie teraz
**pracę trakcji wykonaną na swoim odcinku**, bo jedną liczbą na całą oś nie da się
odpowiedzieć na pytanie, które ta pozycja zadaje.

---

## 1. Dlaczego pole „Weryfikacja" tej pozycji zaczęło się od porażki i to było poprawne

Wiersz `sha256sum` w poleceniu weryfikacyjnym nie jest ozdobą. 6.D15 (#301) zmierzyło,
że przed 6.A11 obie komendy z tego pola kończyły się **kodem 0** i dawały pliki
**identyczne co do bajtu** — bo opcji `--coast-from-m` nie było wtedy nigdzie
w `src/`, a runner nieznaną opcję przyjmował w milczeniu. Weryfikacja spełniała się
przez NIEZROBIENIE zadania.

Po 6.A11 (#307) nieznana opcja kończy się odmową, więc **pierwsza komenda z tego pola
padała**, dopóki opcja nie została dopisana. To jest poprawne zachowanie wyroczni,
a nie usterka: bramka, która ma wykryć brak funkcji, ma na jej braku być czerwona.

Dowodem, że opcja naprawdę coś robi, jest **para sum SHA-256**, a nie kod wyjścia:

```
$ sha256sum build/coast-off.csv build/coast-on.csv
11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079  build/coast-off.csv
439961645395f24f2bb1ef7d832c333bb42d8c6cea1a39cd72e0f194d6b05c79  build/coast-on.csv
```

Pierwsza suma jest **tą samą**, którą 6.D15 zmierzyło dla OBU plików. Przejazd bez
wybiegu jest więc bit w bit tym samym przejazdem, co przed tą zmianą — a przejazd
z wybiegiem jest innym plikiem. Obie rzeczy naraz, jedną komendą.

---

## 2. Jak wybieg wchodzi w prowadzenie

`LineDrive.Command` ma dokładnie jedną gałąź, w której maszynista sam decyduje, czy
ciągnąć: tę przed wyzwoleniem hamowania. Wybieg wchodzi tam i **nigdzie indziej**.

```
próg hamowania nie zadziałał  ->  prędkość < limitu I NIE wybieg  ->  pełna trakcja
                              ->  w przeciwnym razie               ->  Coast
```

Trzy konsekwencje, wszystkie zmierzone, nie założone:

1. **Punkt hamowania się nie zmienia.** Nadal wychodzi z solvera T-311, w każdym kroku
   z bieżącej prędkości i odległości. Model oporów i krzywa hamowania — nietknięte.
2. **Odcinek, na którym hamowanie zaczyna się przed zadanym metrem, jedzie się bit
   w bit tak samo jak bez wybiegu.** W tabeli §3 są to trzy odcinki z Δt równym zeru
   i ubytkiem pracy trakcji równym zeru — nie „bliskim zeru".
3. **Odległość liczy się od odjazdu z poprzedniej stacji**, nie od początku osi.
   Próg mierzony od początku osi zdjąłby trakcję raz i na zawsze, czyli mierzyłby
   zupełnie inną rzecz.

Wybieg zdejmuje **nastawnik**, a nie dokłada hamulca. To jest osobna kontrola w testach
(`Wybieg_zdejmuje_nastawnik_i_nie_dotyka_hamulca`) i nie jest formalnością: „oszczędność
energii" dałoby się osiągnąć hamowaniem, czyli zmianą krzywej hamowania — wprost poza
zakresem tej pozycji.

---

## 3. Pakiet A, wybieg od 250 metra odcinka, per odcinek

Limit 72 km/h, wymiana pasażerów 20 s, AW0, `data/track/L1_A.json`. Czasy jazdy liczone
z `--calls` (odjazd z poprzedniej stacji → przyjazd na tę), praca trakcji z wypisu
`[ODCINEK]`. Kolumna „droga" jest z przejazdu **bez** wybiegu; w przejeździe z wybiegiem
różni się o milimetry, bo skład staje minimalnie inaczej (§3a). Rezerwa rozkładowa —
kolumna „rezerwa" — jest wzięta z
`reports/T-401-line-run.md` §2, gdzie czas modelu na każdym z tych odcinków jest **co do
setnej sekundy** ten sam co w kolumnie „t bez wybiegu" poniżej.

| # | odcinek | droga | t bez wybiegu | t z wybiegiem | Δt | trakcja bez | trakcja z | Δ trakcji | rezerwa | mieści się |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Gare de l'Ouest → Beekkant | 509,42 m | 43,2667 s | 43,2667 s | **+0,0000 s** | 11,5949 kWh | 10,6449 kWh | −0,9500 kWh | **brak** | patrz niżej |
| 2 | Beekkant → Étangs Noirs | 942,18 m | 65,4750 s | 66,1917 s | +0,7167 s | 18,0919 kWh | 10,6517 kWh | −7,4402 kWh | +12,53 s | TAK |
| 3 | Étangs Noirs → Comte de Flandre | 602,88 m | 48,5250 s | 48,6000 s | +0,0750 s | 13,0018 kWh | 10,6517 kWh | −2,3501 kWh | +9,47 s | TAK |
| 4 | Comte de Flandre → Sainte-Catherine | 665,96 m | 51,6833 s | 51,8250 s | +0,1417 s | 13,9468 kWh | 10,6517 kWh | −3,2951 kWh | +19,32 s | TAK |
| 5 | Sainte-Catherine → De Brouckère | 409,20 m | 38,8250 s | 38,8250 s | **+0,0000 s** | 9,9366 kWh | 9,9366 kWh | **0,0000 kWh** | +12,18 s | TAK |
| 6 | De Brouckère → Gare Centrale | 601,91 m | 48,4750 s | 48,5500 s | +0,0750 s | 12,9868 kWh | 10,6517 kWh | −2,3351 kWh | +12,53 s | TAK |
| 7 | Gare Centrale → Parc | 343,82 m | 35,3750 s | 35,3750 s | **+0,0000 s** | 8,5962 kWh | 8,5962 kWh | **0,0000 kWh** | +3,63 s | TAK |
| 8 | Parc → Arts-Loi | 485,27 m | 42,6500 s | 42,6500 s | **+0,0000 s** | 11,2368 kWh | 10,6517 kWh | −0,5851 kWh | +8,35 s | TAK |
| 9 | Arts-Loi → Maelbeek | 591,47 m | 47,9583 s | 48,0167 s | +0,0583 s | 12,8318 kWh | 10,6517 kWh | −2,1801 kWh | +6,04 s | TAK |
| 10 | Maelbeek → Schuman | 314,93 m | 33,7917 s | 33,7917 s | **+0,0000 s** | 7,9811 kWh | 7,9811 kWh | **0,0000 kWh** | +11,21 s | TAK |
| 11 | Schuman → Merode | 1219,00 m | 79,3167 s | 81,0333 s | **+1,7167 s** | 22,2469 kWh | 10,6517 kWh | **−11,5952 kWh** | +10,68 s | TAK |

Całość pakietu A: **+2,7833 s** czasu jazdy i **−30,7309 kWh** pracy trakcji
(142,4516 → 111,7207 kWh, czyli **−21,6 %**). Praca hamulca spada w tym samym przejeździe
ze 104,3574 do 100,2494 kWh — nie jest to jednak zysk tej samej klasy, bo o tym, ile
z niej wraca do sieci, karta M7 milczy (patrz `reports/energy-balance.md`).

**Wszystkie jedenaście odcinków mieści się w rezerwie rozkładowej.** Odcinek 1 —
Gare de l'Ouest → Beekkant — jest w tej odpowiedzi wymieniony osobno i nazwany wprost:
**rozkład STIB nie ma dla niego pary przystanków**, więc rezerwy dla niego nie ma i nie
da się jej dorobić. T-401 §2 liczy z tego samego powodu „10 z 10" dopasowanych odcinków
na jedenaście przejechanych. Wybieg kosztuje tam **zero sekund**, więc pytanie
„czy się mieści" i tak nie ma jak wypaść źle — ale to jest zbieg okoliczności tego
przebiegu, a nie odpowiedź na pytanie o rozkład.

### 3a. Trzy odcinki, na których wybieg nie robi nic — i jeden, na którym robi wszystko

Odcinki 5, 7 i 10 mają **zero** w obu kolumnach różnicowych: 409,20 m, 343,82 m
i 314,93 m. Na żadnym z nich skład nie dojeżdża do 250 metra odcinka przed wyzwoleniem
hamowania, więc gałąź wybiegu nigdy się nie wykonuje. To jest ta sama własność, którą
opisuje §2 punkt 2, tylko zmierzona na prawdziwej osi.

Odcinek 11 — Schuman → Merode, **najdłuższy w pakiecie** (1219,00 m) — bierze na siebie
**62 %** całego kosztu czasowego (+1,7167 s z +2,7833 s) i **38 %** całej oszczędności
(−11,5952 kWh z −30,7309 kWh). Wybieg jest więc zjawiskiem odcinków długich; krótkie
przechodzą obok niego bez śladu.

**Odcinki 1 i 8 są ciekawsze niż zera i niż odcinek 11.** Praca trakcji spada tam
o 0,9500 i 0,5851 kWh przy Δt **równym co do kroku zeru**: skład zdejmuje nastawnik,
ale zdąża wyhamować na peronie w tej samej liczbie kroków symulacji. Zmienia się za to
błąd zatrzymania (na odcinku 1: −0,307 → −0,301 m), więc przejazd jest inny, tylko nie
dłuższy. Jest to najtańszy możliwy wybieg — i jedyne miejsce w tym pomiarze, gdzie
energia jest za darmo.

---

## 4. Gdzie wybieg przestaje się mieścić w rozkładzie

Ta pozycja mierzy koszt, a nie wybiera profilu jazdy — ale odpowiedź „wszystko się
mieści" jest warta tyle, ile próba znalezienia progu, przy którym przestaje. Ten sam
pomiar dla pięciu wartości `--coast-from-m`:

| wybieg od | Δt całego pakietu | praca trakcji | odcinki poza rezerwą |
|---:|---:|---:|---|
| 250 m | +2,7833 s | 111,7207 kWh (−21,6 %) | **żaden** |
| 200 m | +13,3917 s | 99,0680 kWh (−30,4 %) | **żaden** |
| 150 m | +34,2000 s | 82,2280 kWh (−42,3 %) | **Schuman → Merode** (+11,4667 s wobec +10,68 s) |
| 100 m | +77,8083 s | 61,3203 kWh (−57,0 %) | Beekkant → Étangs Noirs, Arts-Loi → Maelbeek, Schuman → Merode |
| 50 m | +203,5333 s | 35,9000 kWh (−74,8 %) | osiem z dziesięciu dopasowanych |

Pierwszym odcinkiem, który wypada z rozkładu, jest **Schuman → Merode** — i to jest
wynik nieoczywisty. Nie jest to odcinek o najciaśniejszej rezerwie: ten tytuł ma
Gare Centrale → Parc z rezerwą +3,63 s (T-401 §3), a on wypada dopiero jako szósty.
Wybieg kosztuje czas **proporcjonalnie do tego, jak długo się nim jedzie**, a nie
proporcjonalnie do ciasnoty rozkładu — więc łamie odcinki najdłuższe, nie najciaśniejsze.
Na Gare Centrale → Parc (343,82 m) przy progu 150 m koszt to +0,1833 s przy rezerwie
+3,63 s, mimo że jest to najciaśniejszy odcinek pakietu.

---

## 5. Rzeczywiste wyjście weryfikacji

Polecenia dokładnie z pola „Weryfikacja" pozycji 6.A6.

```
$ dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --trace build/coast-off.csv
[LINIA] ślad 101872 kroków -> build/coast-off.csv
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 820.42 s, postoje 313.59 s, kroków 101872, koniec=arrived
[LINIA] limit 72.00 km/h, wymiana 20.0 s, hamulec 100 % służbowego, okno stacji 5.0 m, wybieg wyłączony, obciążenie AW0 170000 kg
...
[ENERGIA] E_trakcji = 142.4515 kWh, E_hamulca = 104.3574 kWh, opory = 39.900 MJ, pochylenie = 0.000 MJ, ΔE_kin = 0.000 MJ, dyskretyzacja = 349052.8 J, obcięcie = 96889720.4 J, reszta = -1.907E-006 J, względnie = 2.147E-015
[ODCINEK] Gare de l'Ouest|Weststation → Beekkant: 509.42 m w 43.27 s, trakcja 11.5949 kWh
[ODCINEK] Schuman → Merode: 1219.00 m w 79.32 s, trakcja 22.2469 kWh
kod wyjścia: 0

$ dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --coast-from-m 250 --trace build/coast-on.csv
[LINIA] ślad 102206 kroków -> build/coast-on.csv
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 823.21 s, postoje 313.59 s, kroków 102206, koniec=arrived
[LINIA] limit 72.00 km/h, wymiana 20.0 s, hamulec 100 % służbowego, okno stacji 5.0 m, wybieg 250.0 m odcinka, obciążenie AW0 170000 kg
[ZAŁOŻENIE] CoastFromM = 250 — metr odcinka, od którego maszynista zdejmuje trakcję i jedzie wybiegiem; strategia prowadzenia, nie własność toru — praktyka STIB nie jest publikowana, a 6.A6 mierzy koszt tej liczby, nie twierdzi, że tak się jeździ
...
[ENERGIA] E_trakcji = 111.7210 kWh, E_hamulca = 100.2494 kWh, opory = 39.418 MJ, pochylenie = 0.000 MJ, ΔE_kin = 0.000 MJ, dyskretyzacja = 345470.6 J, obcięcie = 1533880.7 J, reszta = 1.042E-005 J, względnie = 1.365E-014
[ODCINEK] Gare de l'Ouest|Weststation → Beekkant: 509.43 m w 43.27 s, trakcja 10.6449 kWh
[ODCINEK] Schuman → Merode: 1219.00 m w 81.03 s, trakcja 10.6517 kWh
kod wyjścia: 0

$ sha256sum build/coast-off.csv build/coast-on.csv
11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079  build/coast-off.csv
439961645395f24f2bb1ef7d832c333bb42d8c6cea1a39cd72e0f194d6b05c79  build/coast-on.csv
```

Zestawy testów, oba przez kod wyjścia:

```
$ python3 tools/tests/test_all.py ; echo "kod: $?"
  RAZEM 66.050 s, 1740 testów, 85 modułów
kod: 0

$ dotnet test tests/Sim.Tests -c Release ; echo "kod: $?"
Passed!  - Failed:     0, Passed:   546, Skipped:     0, Total:   546, Duration: 14 s - MetroBxl.Sim.Tests.dll (net10.0)
kod: 0
```

Bilans energii domyka się w obu przejazdach: względna reszta 2,147·10⁻¹⁵ bez wybiegu
i 1,365·10⁻¹⁴ z wybiegiem — czyli wybieg nie rozstroił rachunku, który T-310 i T-311
prowadzą dwiema niezależnymi drogami. Człon obcięcia spada z 96,89 MJ do 1,53 MJ i to
jest spodziewane: bez wybiegu skład jedzie długimi odcinkami na pełnym nastawniku
przyciętym do limitu prędkości, a z wybiegiem przy limicie nie wisi.

---

## 6. Kontrole negatywne — WYKONANE, nie opisane

Pięć sabotaży, każdy z rzeczywistym wyjściem, każdy przywrócony (`git diff --stat src/`
puste po przywróceniu, sprawdzone `diff -q` wobec kopii sprzed sabotażu).

**KN-1. Opcja czytana w kodzie, ale zdjęta z tabeli `KnownOptions`.** Ma zapalić bramkę
zgodności tabeli z kodem — i zapala dokładnie jeden test z pięciu:

```
FAIL test_every_option_the_code_reads_is_in_the_table -> polecenie line czyta opcje spoza
     tabeli: ['--coast-from-m'] — dopisz je do KnownOptions, inaczej odmowa odrzuci opcje,
     ktora dziala
PASS test_the_refusal_is_actually_wired_into_main
PASS test_the_refusal_skips_positional_arguments
PASS test_the_table_covers_every_command_the_dispatcher_knows
PASS test_the_table_does_not_declare_options_nobody_reads
```

**KN-2. Drugi kierunek: opcja w tabeli, ale kod jej nie czyta.** To jest sabotaż
odwzorowujący „dopisałem tylko do tabeli" i musi paść **inny** test niż w KN-1:

```
PASS test_every_option_the_code_reads_is_in_the_table
PASS test_the_refusal_is_actually_wired_into_main
PASS test_the_refusal_skips_positional_arguments
PASS test_the_table_covers_every_command_the_dispatcher_knows
FAIL test_the_table_does_not_declare_options_nobody_reads -> tabela deklaruje dla line
     opcje, ktorych kod nie czyta: ['--coast-from-m']
```

Para KN-1/KN-2 jest istotą tej pozycji: opcja dopisana tylko do kodu **albo** tylko do
tabeli jest w obu wypadkach opcją zepsutą i bramka łapie obie strony osobno.

**KN-3. Wybieg nigdy nie zachodzi** (`Coasting => false`) — czyli przełącznik, który
istnieje i nie robi nic. To jest dokładnie stan, w którym pole „Weryfikacja" spełniało
się przez niezrobienie zadania:

```
  Failed Wybieg_wydluza_jazde_i_zmniejsza_prace_trakcji [52 ms]
  Failed Wybieg_zdejmuje_nastawnik_i_nie_dotyka_hamulca [22 ms]
  Failed Odcinek_krotszy_niz_prog_jedzie_sie_tak_samo_jak_bez_wybiegu [23 ms]
Failed!  - Failed:     3, Passed:   543, Skipped:     0, Total:   546
```

**KN-4. Wybieg realizowany hamulcem** zamiast zdjęciem nastawnika (`Coast` podmieniony
na 20 % hamulca służbowego). Czas by urósł, energia trakcji spadła — obie liczby
z §3 wyszłyby „poprawnie", a model hamowania byłby ruszony, czyli zadanie zrobione
wbrew polu „Poza zakresem":

```
  Failed Wybieg_zdejmuje_nastawnik_i_nie_dotyka_hamulca [102 ms]
   Assert.IsTrue failed. kroków wybiegu tylko 7 — próg nie zadziałał
Failed!  - Failed:     1, Passed:   545, Skipped:     0, Total:   546
```

**KN-5. Migawka pracy trakcji zerowana zamiast odświeżanej przy odjeździe** — każdy
odcinek raportowałby wtedy pracę od początku PRZEJAZDU, a nie od poprzedniej stacji.
Kolumny „trakcja" w §3 nadal wyglądałyby jak liczby:

```
  Failed Praca_trakcji_odcinkow_domyka_sie_do_pracy_przejazdu [42 ms]
   Assert.AreEqual failed. Expected a difference no greater than <0.0002958179059441504>
   between expected value <295817905.9441504> and actual value <611015458.413286>.
   wybieg : suma odcinków nie domyka się do przejazdu
Failed!  - Failed:     1, Passed:   545, Skipped:     0, Total:   546
```

---

## 7. Czego świadomie nie zrobiłem

- **Nie wybrałem profilu jazdy dla gry.** Pole „Poza zakresem" mówi to wprost: pozycja
  mierzy koszt i zysk. Liczba 250 m jest **pytaniem pomiarowym**, nie odwzorowaniem
  praktyki STIB — ta nie jest publikowana, tak samo jak ułamek hamulca służbowego,
  przy którym maszynista zaczyna hamować.
- **Nie ruszyłem modelu oporów ani krzywej hamowania.** Wybieg wchodzi wyłącznie w gałąź
  „nie hamuję jeszcze"; punkt hamowania nadal wychodzi z solvera T-311.
- **Nie dopisałem wybiegu do poleceń `budget` ani `replay`.** Pole „Wyjście" mówi
  o przełączniku w `Sim.Runner` dla przejazdu liniowego; rozszerzanie go na pomiar
  kosztu kroku rdzenia i na przejazd z zapisu wejść byłoby zmianą, o którą nikt nie prosił.
- **Nie przeliczyłem rozkładu.** Rezerwy z T-113 wymagają `build/gtfs/stib_gtfs.zip`,
  którego w drzewie nie ma i którego nie da się pobrać w tym środowisku. Kolumna
  „rezerwa" jest **datowanym pomiarem cytowanym z T-401 §2** — i jest to cytat legalny,
  bo czasy modelu w tamtym raporcie zgadzają się z kolumną „t bez wybiegu" co do setnej
  sekundy na wszystkich dziesięciu dopasowanych odcinkach.
- **Nie ujednoliciłem kodów wyjścia runnera** (`compare` zwraca 2, reszta odmów 1).
  To decyzja właściciela, nazwana już przy 6.A10, 6.A11, 6.A13 i 6.D20.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- **Wiersz 6.A11 w `docs/TASKS.md` cytuje komunikat odmowy dla `--coast-from-m`.** Ta
  nazwa przestała być dziś nieznana, więc cytat opisuje stan sprzed tej pozycji. Jest to
  datowany zapis („ZROBIONE 06.09.2026"), a nie twierdzenie o stanie bieżącym, i taki
  zapis w tym repozytorium się nie przelicza (`tools/tests/test_report_hygiene.py`).
  Przepisałem natomiast **oba miejsca, które mówiły o tym w czasie teraźniejszym**:
  komentarz przy `KnownOptions` w `Program.cs` i test odmowy w `RunnerCommandTests`
  (ten drugi padał na rozbiorze `X` jako liczby, czyli sprawdzałby coś innego, niż mówi
  jego nazwa — rolę przykładu przejął `--headway-s`, opcja istniejąca w `budget`
  i nieistniejąca w `line`).
- **Człon obcięcia w bilansie energii przejazdu bez wybiegu to 96,89 MJ**, czyli
  ok. 27 kWh przy pracy trakcji 142,45 kWh. Jest to artefakt schematu (przycięcie
  prędkości do limitu), nie fizyka, i `TripEnergyAccount` nazywa go wprost — ale
  jego rząd wielkości mówi, ile czasu skład wisi na limicie z pełnym nastawnikiem.
  Nie jest to usterka do naprawienia w tej pozycji; jest to obserwacja, że „pełna
  trakcja do progu hamowania" jest prowadzeniem bardzo daleko od oszczędnego.
- **Rozkład STIB nie ma pary przystanków dla odcinka Gare de l'Ouest → Beekkant.**
  Wie o tym już T-401 („10 z 10" przy jedenastu odcinkach), ale nigdzie nie jest to
  nazwane jako brak DANYCH, tylko jako liczba dopasowań. Ten raport nazywa to wprost.
