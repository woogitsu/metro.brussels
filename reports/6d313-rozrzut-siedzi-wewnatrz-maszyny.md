# 6.D313 · Wzorzec rozrzutu NIE opisuje już tego zestawu — a rozrzut siedzi WEWNĄTRZ jednej maszyny, nie między maszynami

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `b882f20`

Przy PR #712 job `tools` padł na budżecie CPU przy **2664/2664 przeszło**. Ta pozycja
liczy rozrzut na dzisiejszym korpusie tą samą metodą, którą policzono wzorzec
14.09.2026, rozbija go po modułach i rozstrzyga, czy wzorzec jeszcze ten zestaw
opisuje.

**Źródło jest to samo, co wzorca**: artefakty `czas-zestawu` z `python-tests.yml`,
pobrane wprost z API po identyfikatorze — czyli tak, jak zapowiada komentarz przy
`POMIARY_CPU_BIEZACEGO_DRZEWA`. Pobrałem **wszystkie 538 niewygasłych**, nie próbkę.

---

## 1. Odpowiedź na pytanie zadane wprost: NIE OPISUJE

Wzorzec policzony dziś tą samą metodą — grupy o tej samej parze (liczba testów,
liczba modułów), co najmniej trzy przebiegi w grupie, iloraz `max/min`, a potem
mediana i maksimum po grupach:

```
                          MEDIANA GRUP      MAKSIMUM GRUP
wzorzec z 14.09.2026      sciana 1,091      sciana 1,412       265 artefaktow, 30 grup
(w drzewie)               cpu    1,048      cpu    1,239

dzisiaj, WSZYSTKIE        sciana 1,134      sciana 4,796       538 artefaktow, 60 grup
maszyny                   cpu    1,061      cpu    2,696

dzisiaj, BEZ KONTENERA    sciana 1,121      sciana 2,049       530 artefaktow, 60 grup
(tylko `metro-wsl-*`)     cpu    1,058      cpu    1,629
```

**Kryterium spisałem przed pomiarem**: wzorzec opisuje korpus wtedy i tylko wtedy,
gdy maksimum grup nie przekracza wpisanej wartości. Nie mieści się **ani ściana**
(2,049 wobec 1,412), **ani CPU** (1,629 wobec 1,239) — i to już po odjęciu kontenera,
czyli w wariancie dla wzorca najżyczliwszym.

**Mediana prawie się nie ruszyła, a maksimum wybuchło** — i to jest właściwy kształt
tego wyniku. Typowy przebieg jest dziś tak samo powtarzalny jak wtedy (1,058 wobec
1,048 na CPU); zmienił się **ogon**. Próg postawiony na medianie nie zauważyłby
niczego; próg postawiony na maksimum zapala się dziś naprawdę.

## 2. Rozrzut siedzi WEWNĄTRZ maszyny — tytuł tej pozycji mówi inaczej i jest nieprawdziwy

Pole „Czego NIE wolno przyjąć bez pomiaru" ostrzegało, żeby nie zakładać, że rozrzut
bierze się z maszyny. Ostrzegało słusznie. Grupa dzisiejszego korpusu — **2664 testy,
139 modułów, pięćdziesiąt przebiegów, zero przebiegów kontenera**:

```
miedzy maszynami (iloraz srednich z trzech maszyn):  1,099
najwiekszy rozrzut WEWNATRZ jednej maszyny:          1,572
rozrzut calej grupy:                                 1,629

   metro-wsl-DOM-NEW-01   n=19   cpu 303,6 - 403,3   max/min 1,328
   metro-wsl-DOM-NEW-02   n=21   cpu 310,5 - 406,5   max/min 1,309
   metro-wsl-DOM-NEW-03   n=10   cpu 314,6 - 494,5   max/min 1,572
```

**Różnica między maszynami wynosi dziesięć procent, a wewnątrz jednej maszyny —
pięćdziesiąt siedem.** Nazwa tej pozycji („rozrzut czasu CPU MIĘDZY MASZYNAMI")
opisuje więc zjawisko, którego pomiar nie potwierdza; zostawiam nazwę, bo nie
przepisuję czyjegoś tytułu przy wykonaniu, ale zapisuję wprost, że treść jest inna.

**Kontener został odjęty, a nie pominięty po cichu.** W całym zbiorze stoi osiem
przebiegów z maszyn `docker-runner-*` i to one robią dwie skrajne grupy (2508/127
o ilorazie 4,796 i 2509/127 o ilorazie 4,100): kontener liczy 645,8 s CPU tam, gdzie
runner liczy 250,4 s. Mieszanie obu klas maszyn w jednym rachunku nie mierzy rozrzutu,
tylko różnicę sprzętu — dlatego §1 podaje obie liczby, a §2 liczy na samym runnerze.

## 3. Rozbicie po modułach — i dlaczego NAJWIĘKSZY ILORAZ jest tu bezużyteczny

```
modulow obecnych w KAZDYM z 50 przebiegow, z czasem > 0:   118
modulow nieobecnych w czesci przebiegow:                     0
modulow z co najmniej jednym czasem 0,000 s:                21
mediana rozrzutu po modulach:                            1,957
rozrzut calego zestawu (cpu):                            1,629
```

**Mediana rozrzutu pojedynczego modułu jest WIĘKSZA niż rozrzut całego zestawu** —
sumowanie stu trzydziestu dziewięciu modułów uśrednia szum, więc zestaw jest
stabilniejszy niż jego części. To tłumaczy, dlaczego próg na całości może stać
znacznie ciaśniej niż próg na module.

Czternaście modułów o największym ilorazie:

```
modul                                   max/min     min_s     med_s     max_s
test_snapshot_source.py                  101,60     0,005     0,505     0,508
test_all.py                               17,31     0,032     0,538     0,554
test_playable_scripts.py                   5,00     0,001     0,001     0,005
test_axis_claims.py                        4,00     0,001     0,002     0,004
test_line_trace_gate.py                    3,83     0,012     0,016     0,046
test_camera_aim.py                         3,67     0,003     0,004     0,011
test_runner_number_parsing.py              3,50     0,004     0,004     0,014
test_tree_walks.py                         3,01     6,417     8,960    19,287
test_station_components.py                 3,00     0,001     0,001     0,003
test_player_package.py                     3,00     0,001     0,001     0,003
test_network_declarations.py               3,00     0,001     0,002     0,003
test_data_freshness.py                     3,00     0,001     0,002     0,003
test_packages.py                           2,78     0,009     0,011     0,025
test_prose_counts.py                       2,69     2,472     3,256     6,657
```

**Iloraz jest tu złym przyrządem i mówię to zamiast podawać czołówkę jako wynik.**
Sto jeden razy przy `test_snapshot_source.py` bierze się z jednego przebiegu, w którym
moduł policzył 0,005 s zamiast 0,505 s — czyli z **rozdzielczości pomiaru**, a nie
z czegokolwiek o module. Jedyny wiersz tej czternastki, który niesie treść, to
`test_tree_walks.py`: 6,417 wobec 19,287 s, czyli trzykrotność na wielkościach
mierzalnych.

## 4. Czym NAPRAWDĘ różni się przebieg najszybszy od najwolniejszego

Tu iloraz zastępuję **udziałem bezwzględnym** — różnicą sekund tego samego modułu
między dwoma konkretnymi przebiegami:

```
najszybszy:     cpu 303,6 s   sciana 227,4 s   metro-wsl-DOM-NEW-01
najwolniejszy:  cpu 494,5 s   sciana 412,9 s   metro-wsl-DOM-NEW-03
suma roznic po modulach: 184,5 s sciany

   +43,30 s  test_dotnet_version.py
   +24,65 s  test_field_paths.py
   +17,31 s  test_doctor_queue_claim.py
   +12,71 s  test_message_claims.py
   +12,27 s  test_mutation_sweep.py
   +11,92 s  test_tree_walks.py
   + 7,79 s  test_backlog.py
   + 7,62 s  test_doctor_test_log.py
```

**Pięć z ośmiu czołowych modułów woła podprocesy** — `.NET` (`test_dotnet_version.py`),
`doctor.sh` (`test_doctor_queue_claim.py`, `test_doctor_test_log.py`) albo własny
interpreter (`test_mutation_sweep.py`). Podejrzenie zapisane w polu „Skąd" tej
pozycji — że rozrzut bierze się z korpusu, a nie z maszyny — **potwierdza się**,
i potwierdza się w drugiej połowie także §2: to nie maszyna jest inna, tylko to,
co ten sam zestaw robi na tej samej maszynie przy różnym obciążeniu.

## 5. Kontrola przyrządu — zdana, z zastrzeżeniem o kluczu grupowania

Pole żądało, by przebieg o czasie 494,486 s CPU i przebieg bazy z tego samego dnia
trafiły do jednej grupy „identyczne drzewo":

```
ZNALEZIONY: artefakt 10592848820  cpu=494,486  sciana=412,854
            runner=metro-wsl-DOM-NEW-03  commit=44eea436
grupa: (2664, 139)      przebiegow w grupie: 50
```

Przebieg jest w grupie dzisiejszego korpusu razem z czterdziestoma dziewięcioma
innymi, więc kontrola przechodzi.

**Zastrzeżenie, które zapisuję zamiast przemilczeć:** tych pięćdziesiąt przebiegów
ma **pięćdziesiąt różnych commitów**. Klucz „(liczba testów, liczba modułów)" jest
**przybliżeniem** identyczności drzewa, a nie identycznością — dwa drzewa o tej samej
parze liczb mogą różnić się treścią, byle nie liczbą testów. Tak grupował wzorzec
i tak grupuję ja, żeby liczby dało się porównać; ale zdanie „rozrzut na identycznym
drzewie" jest o jeden krok słabsze, niż brzmi, i było takie już przy tamtych 265.

## 6. Dwie liczby, których pole nie zamawiało, a które z tego wypadają

```
przebiegow dzisiejszego korpusu ponad SUITE_CPU_BUDGET_S:  1 z 50  (2,0 %)
   494,486 s   metro-wsl-DOM-NEW-03   44eea436

cpu w grupie:  min 303,6   mediana 343,2   maksimum 494,5
dzisiejsze maksimum / `MEASURED_MAX_CPU_S`, czyli 226,537:  2,183
```

Zapisuję je, bo bez nich §1 daje się przeczytać jako „próg jest za ciasny", a to nie
jest to, co zmierzyłem. **Próg odrzucił jeden przebieg na pięćdziesiąt.** Mediana
dzisiejszego korpusu stoi na 343,2 s, czyli 78 % progu; maksimum przekracza go
o 12 %. Czy to znaczy, że próg ma się ruszyć, **nie rozstrzygam** — pole „Poza
zakresem" zabrania tego wprost, a zapadki górnej i tak wolno wyłącznie obniżać.

## 7. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| V1 | rozrzut CPU przekroczy 1,239 | trafione (1,629) — o niezależności niżej |
| V2 | rozrzut ściany przekroczy 1,412 | trafione (2,049) |
| V3 | grup o >= 3 przebiegach będzie **mniej niż 30** | **OBALONE** — sześćdziesiąt |
| V4 | największy rozrzut po modułach da moduł wołający podprocesy | **rozstrzygnięte w OBIE strony** |
| V5 | rozrzut po modułach będzie większy niż rozrzut zestawu | trafione (1,957 wobec 1,629) |
| V6 | kontrola przyrządu zda się | trafione, z zastrzeżeniem §5 |

**V1 liczę jako niezależne, bo warunek na to spisałem przed pomiarem, a nie po.**
Plik definicji mówił: zaliczyć tylko wtedy, gdy pomiar z artefaktów pójdzie inną
drogą niż znany mi iloraz 1,387 z PR #712 — inne przebiegi, inna maszyna, bez
kontenera. Poszedł: tamten był porównaniem dwóch drzew na jednym kontenerze,
ten jest pięćdziesięcioma przebiegami na trzech maszynach runnera, bez ani jednego
przebiegu kontenera.

**V4 jest rozstrzygnięte w obie strony i tak je zapisuję, zamiast wybierać stronę
wygodną.** Po **ilorazie** przewidywanie jest obalone: czołówkę robi
`test_snapshot_source.py`, który podprocesów nie woła, a jego sto jeden razy to
artefakt rozdzielczości (§3). Po **udziale bezwzględnym** przewidywanie jest trafione:
pierwsze miejsce ma `test_dotnet_version.py` z czterdziestoma trzema sekundami (§4).
Przewidywanie nie mówiło, którą miarą — i to jest jego wada, nie zasługa.

**V3 upadło przez pomyłkę w jedną stronę, którą warto nazwać:** spodziewałem się
mniejszej liczby grup, bo myślałem o grupach z dzisiejszego drzewa. Tymczasem
retencja trzydziestu dni sięga wstecz do korpusów o 2178 testach, więc grup jest
dwa razy więcej niż we wzorcu — a nie mniej.

## 8. Czego świadomie nie zrobiono

- **Nie tknięto `SUITE_CPU_BUDGET_S`, `WZORZEC_ROZRZUTU` ani `MARGIN_CPU`.**
  Pole „Poza zakresem" zabrania tego wprost, a zapadkę górną i tak wolno wyłącznie
  obniżać — więc podniesienie jej po tym pomiarze byłoby złamaniem reguły, nie
  wnioskiem z liczb.
- **Nie zmieniono workflowa** ani kroku zapisującego artefakty.
- **Nie dopisano pamięci do żadnego czytnika** — to 6.D306 i osobna pozycja.
- **Nie wyrzucono przebiegów kontenera ze zbioru**, tylko policzono obie wersje
  osobno: wyrzucenie byłoby decyzją o tym, co jest „tą samą maszyną".
- **Nie tknięto `src/`** ani `data/`.
- **Nie rozstrzygnięto, czy próg ma się ruszyć** — §6 podaje liczby, nie wniosek.

## 9. Zauważone przy okazji, nietknięte

**Komentarz przy `POMIARY_CPU_BIEZACEGO_DRZEWA` mówi „DZISIEJSZYM drzewie (2466
testów, 126 modułów)", a dzisiejsze drzewo ma 2664 testy i 139 modułów.** Lista
niosąca w nazwie słowo „bieżącego" opisuje korpus sprzed stu dziewięćdziesięciu
ośmiu testów i trzynastu modułów. Nie ruszam jej, bo pole zabrania — ale nazwa
„bieżące" starzeje się po cichu, dokładnie tak jak liczebność puli runnerów,
o której CLAUDE.md §9 mówi, że nigdy nie będzie wpisana.

**Dwadzieścia jeden modułów ma w co najmniej jednym z pięćdziesięciu przebiegów
czas 0,000 s.** Dla nich iloraz `max/min` jest nieokreślony albo nieskończony,
a mój rachunek je odsiewa. Ile z nich naprawdę wykonuje pracę poniżej rozdzielczości
zegara, a ile jest pustych, nie liczyłem.

**Osiem przebiegów w całym zbiorze pochodzi z maszyn `docker-runner-*`**, a CI tego
projektu chodzi na `self-hosted`. Skąd się tam wzięły i czy `WZORZEC_ROZRZUTU`
policzono z nimi czy bez, nie wiem — i to jest pytanie, którego ta pozycja nie
zadaje, a które zmienia interpretację maksimum 1,239.

## 10. Weryfikacja — rzeczywiste wyjście

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2664/2664 przeszło
  RAZEM 365.940 s, 2664 testów, 139 modułów
EXIT=0
```

Zero `FAIL`. **Bramki nie przybyło** — pozycja LICZY, a pole „Poza zakresem"
zabrania zmiany któregokolwiek progu. Bramki dotknięte tą pozycją przeszły
wcześniej osobno — `test_report_hygiene`, `test_field_paths`, `test_backlog`,
`test_report_claims`, `test_suite_runtime_budget` i `test_docs_map`: **177/177**.

**Ten przebieg jest CZWARTYM pomiarem ściany na tym kontenerze w tej sesji**, przy
tej samej liczbie testów i modułów:

```
414,695 s     418,599 s     361,079 s     365,940 s
```

Rozkładają się w **dwie pary** odległe o szesnaście procent (`418,599 / 361,079 =
1,160`), a nie w jedno pasmo z szumem. Jest to ta sama wielkość, którą §2 mierzy
na runnerze — **rozrzut wewnątrz jednej maszyny** — tylko na maszynie innej klasy
i przy próbie czterech przebiegów zamiast pięćdziesięciu. Zapisuję ją jako dane,
a nie jako wniosek: cztery punkty nie rozstrzygają, czy pasma są dwa, czy to
przypadek; pozycja tego nie pytała i tego nie liczy.
