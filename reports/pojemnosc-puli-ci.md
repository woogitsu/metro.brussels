# Pojemność puli CI a mierzalność jobów czasowych (6.D43)

**Zmierzone 08.09.2026 na commitach:** `a9d9f85` … `15f5aa3` (siedem przebiegów
`pull_request`, #407 … #412).
**Przyrząd:** bramka kosztu kroku z 6.D41 (`tools/ci/assert_linecore_budget.py`,
kolumna `rozstęp_%`) plus okna `started_at`/`completed_at` jobów z API GitHuba.

---

## 1. Co ta pozycja miała zmierzyć, i co obaliła

Pole „Skąd" 6.D43 mówiło:

> przebieg jednego pull requesta to **jedenaście jobów**, z czego **cztery** to rendery
> Blendera. […] skutkiem jest to, że **pierwszy przebieg każdego pull requesta jest
> niemierzalny z konstrukcji**.

**Zdanie jest nieprawdziwe, i to jest główny wynik pozycji.** Jedenaście jobów nie chodzi
jednocześnie — pula na to nie pozwala, więc joby się **kolejkują**. Niemierzalność
z 07.09.2026 wzięła się z puli, która wtedy **miała** dwanaście slotów; to zmienna
maszyny, nie własność konstrukcji CI.

Dowód rozstrzygający: 08.09.2026 o 13:11 otwarto **dwa** pull requesty naraz, czyli
**dwadzieścia zgłoszonych jobów** — a szczyt równoległości **chwilowej** wyszedł **3**,
czyli tyle samo co przy jednym pull requeście.

> **Liczba otwartych pull requestów nie wyznacza obciążenia. Wyznacza je pula.**

## 2. Sparowany zbiór — rozstęp wobec liczby jobów

| jobów **chwilowo** | rozstęp | koszt kroku | job | jak ustalono równoległość |
|---:|---:|---:|---|---|
| **2** | **4,5 %** | 5,407 µs | `102042758924` (#410) | **policzona** z okien, zamiatarka |
| **3** | **19,8 %** | 5,649 µs | `102074810691` (#411) | **policzona** z okien, zamiatarka |
| **12** | **115,9 %** | 16,022 µs | 07.09.2026, `woogitsu-host-08` | **Z ZAPISU, nie policzona** |

Trzeci wiersz ma inną jakość niż dwa pierwsze i **to musi tu stać**, a nie być zamiecione:
liczbę „dwanaście" wzięto z zapisu w `reports/rozstep-budzetu-kroku.md`, nie z przejścia
po oknach jobów. Tak samo dwa dalsze punkty z archiwum — **102,6 %** (job
`101900177486`) i **84,0 %** (job `101890547517`) — są opisane **liczbą pull requestów**,
nie zmierzoną równoległością, więc do tabeli nie wchodzą.

**Najwyższa liczba jobów, przy której rozstęp trzyma się pod granicą
`spread_pct_max`, wynosi zatem 3 — z zastrzeżeniem, że punktów między 3 a 12 NIE MA.**
Pole „Skończone, gdy" żąda tej liczby i to jest odpowiedź, jaką dane pozwalają dać.

## 3. Rozstęp rośnie szybko, koszt stoi

| przejście | rozstęp | koszt kroku |
|---|---:|---:|
| 2 → 3 joby | **4,40 ×** | 1,045 × |
| 2 → 12 jobów | 25,8 × | 2,96 × |

Wniosek jest o **przyrządzie**, nie o rdzeniu: rozstęp jest wielkością **czułą** na
obciążenie, a koszt kroku **odporną**, dopóki obciążenie nie jest skrajne. W paśmie 2–3
jobów bramka czasu mierzy więc **kod**, a strażnik rozstępu już **maszynę**.

To jest podstawa pod procedurę, którą agent granicy rozstępu wskazał jako jedyną
rozstrzygającą i **świadomie nie wprowadził** z braku danych: **powtórzenie pomiaru**
przy słabym uwarunkowaniu, zamiast odrzucania go albo przepuszczania.

## 4. Czasy ściany jobów czasowych

| przebieg | job | równolegle | czas |
|---|---|---:|---:|
| #407 | `tools` | 5 | 158 s |
| #408 | `tools` | 3 | 115 s |
| #409 | `tools` | 2 | 118 s |
| #410 | `tools` | 2 | 125 s |
| #411 | `tools` | 3 | 120 s |
| #412 | `tools` | 2 | 91 s |

Konkurencja zaczyna kąsać **powyżej trzech**: między 2 i 3 różnica leży w szumie
(91–125 s), przy 5 czas rośnie do 158 s.

## 5. Cztery tryby obciążenia, wszystkie zmierzone tego dnia

| tryb | co zaobserwowano |
|---|---|
| pula szeroka | szczyt równoległości **5** (#407, 07:33) |
| pula wąska | szczyt **2** (#409, 09:33; #410, 12:05) |
| **przerwa** | **16 min** (10:13:10 → 10:29:14), **33 min** (11:26 → 11:59) i **54 min 28 s** (16:48:35 → 17:43:03) bez ani jednego startu — patrz §10 |
| **zakleszczenie** | run `34209969496`: `updated_at` = `created_at` (09:26:06) **niezmienione od 90 minut**, przy dziewięciu innych jobach tego samego pull requesta przeszłych w tym czasie. `rerun_workflow_run` odmówił („already running"); odzyskane przez **cancel + rerun**, po czym job przeszedł w **63 s** |

**Przerwa jest trybem osobnym i groźnym dla pomiaru**, bo pomiar czasu wykonany w dziurze
wygląda **identycznie** jak pomiar na cichej maszynie, a mówi o czymś innym.

## 6. Wariant zmiany topologii — wypisany z kosztem, NIE wprowadzony

Pole „Poza zakresem" tej pozycji zabrania dopisywać `concurrency` i `needs:`. Poniżej
sam rachunek, dla decyzji o **6.D52**.

- **`needs:` nie ma zastosowania.** Zmierzone przejściem po `.github/workflows/`:
  **dziesięć jobów stoi w dziesięciu osobnych plikach workflowu**, a `concurrency` nie
  występuje w żadnym. `needs:` działa wyłącznie **wewnątrz** jednego workflowu.
- **Zostaje wspólna grupa `concurrency`**, a z nią zachowanie, którego **w tym
  repozytorium nie zmierzono**: dokumentacja GitHuba mówi, że w grupie stoi jeden
  przebieg oczekujący, a kolejny **anuluje** tego oczekującego. Anulowany job nie jest
  „niemierzalny" — jego po prostu nie ma.
- **Koszt przy dzisiejszej puli jest bliski zeru korzyści.** Jeśli pula sama ogranicza
  się do 2–3 jobów, a rozstęp przy 3 jobach wynosi 19,8 % wobec granicy `spread_pct_max`,
  to serializacja **nie zmieni rozstępu**, a wydłuży przejście zestawu bramek: dziś
  jedenaście jobów przechodzi w ~50 minut przy równoległości 2–3, a szeregowo byłoby to
  suma czasów, czyli ~75 minut licząc same zmierzone dziś joby.
- **Serializacja ma sens przy puli szerokiej.** A szerokość puli jest dziś **zmienną,
  nie stałą** — spadła 5 → 2 w ciągu dwóch godzin i miała dwie przerwy. Wpisanie
  `concurrency` na podstawie dzisiejszego pomiaru zabezpieczałoby przed stanem, którego
  dziś nie ma, kosztem stanu, który jest.

**To jest liczba, na której właściciel ma oprzeć decyzję o 6.D52 — nie rekomendacja
zamiast niej.**

## 7. Uwaga o odczycie pomiaru z logu, wyniesiona z pięciu prób

Wiersz `[BUDZET-BRAMKA]` z **prawdziwym** pomiarem stoi w logu joba `sim` około **100
wierszy od końca**, bo za nim idą **dwa kroki kontroli negatywnej**, które drukują
**ten sam format** z liczbami **atrapy**: `15.400 µs` (wyliczane z progu) i `3.772 µs`
przy obsadzie jednego składu. Odczyt „z ogona logu" trafia więc w atrapę i **wygląda
jak pomiar**.

Pięć prób z różną długością ogona, zanim trafiono we właściwy wiersz; **dwie z nich
zostałyby odczytane jako pomiar**, gdyby nie znajomość wartości atrapy.

**Wniosek jest o jobie, nie o czytającym:** krok bramki powinien wypisywać wiersz pomiaru
do `$GITHUB_STEP_SUMMARY`, gdzie stoi sam i nie da się go pomylić z atrapą kontroli. To
jedno zdanie w workflowie, zdejmuje całą tę klasę pomyłki przy każdym przyszłym odczycie,
i jest zmianą w **sposobie raportowania**, nie w topologii jobów — więc nie wchodzi
w pole „Poza zakresem" tej pozycji.

## 8. Sprostowanie licznika użytego po drodze

Do 13:45 raportowano „szczyt równoległości 9 → 5 → 2" dla #407/#408/#409. **Ta liczba
liczyła co innego, niż nazywała:** zliczała, ile jobów nachodzi na **całe okno** danego
joba. Przy renderze trwającym 13 minut siedem różnych jobów dotyka jego okna, nie chodząc
ani chwili razem.

Równoległość **chwilowa**, policzona zamiatarką po zdarzeniach start/koniec:

| przebieg | dawny licznik | szczyt CHWILOWY |
|---|---:|---:|
| #407 | 9 | **5** |
| #408 | 5 | **3** |
| #409 | 2 | 2 |
| #410 | 3 | 2 |
| #411 + #412 (dwa PR-y, 20 jobów zgłoszonych) | 8 | **3** |

Liczby przy samych jobach czasowych były w większości poprawne, bo `sim` trwa ~50 s
i jego okno jest prawie chwilowe. Poprawki: #407 `sim` **5** (nie 6), #411 `sim` **3**
(nie 4), #412 `tools` **2** (nie 3). Tabela w §2 stoi na liczbach poprawionych.

---

## 9. Pomiar dopisany po zamknięciu paragrafów wyżej: job czasowy OBOK renderu

Ten paragraf powstał PO napisaniu wszystkiego wyżej i dlatego stoi osobno, a nie
wewnątrz §2 — pochodzi z innego okna czasowego i wtrącenie go do tamtej tabeli
zaciemniałoby, skąd się wziął. Jest tu, bo dotyka **premisy pozycji wprost**, a żaden
pomiar z §2 jej wprost nie dotykał.

Przebieg pull requesta #415 (`15f5aa3`, gałąź `claude/osm-api-zamiast-overpassa`)
zgłosił **jedenaście** jobów o `16:01:24`. Okna z API, w kolejności startów:

| job | start | koniec | trwanie |
|---|---|---|---:|
| `station-details` | 16:01:26 | 16:04:41 | 3 min 15 s |
| `material-style` | 16:06:38 | 16:09:16 | 2 min 38 s |
| `tunnel-alignment (L1_B)` — **render Blendera** | 16:09:17 | 16:21:45 | **12 min 28 s** |
| `tools` | 16:14:53 | 16:16:49 | 1 min 56 s |
| `sim` | 16:16:51 | 16:17:47 | **56 s** |
| `first-run` | 16:17:49 | 16:21:43 | 3 min 54 s |

Okno ma dwie różne fazy i to jest jego cała treść:

**Faza szeregowa, 16:01–16:09.** Kolejny job startuje po zakończeniu poprzedniego
(16:06:38 po 16:04:41; 16:09:17 po 16:09:16 — jedna sekunda). Szczyt równoległości
**chwilowej wynosi 1**, przy jedenastu jobach zgłoszonych w tej samej sekundzie.

**Faza z renderem, 16:14–16:17.** `tunnel-alignment (L1_B)` chodził od 16:09:17 do 16:21:45,
całe **12 min 28 s**, więc `tools` (16:14:53) i `sim` (16:16:51)
przeszły **w całości wewnątrz jego okna**. Równoległość chwilowa: **2**, i drugim
zadaniem jest render Blendera.

### To jest dokładnie sytuacja, którą pozycja nazwała niemierzalną

Treść 6.D43 mówi: joby czasowe „chodzą równolegle z czterema renderami Blendera z TEGO
SAMEGO przebiegu, więc pierwsze uruchomienie każdego pull requesta jest **niemierzalne
z konstrukcji**". Tu zachodzi przesłanka — `sim` chodził równolegle z renderem tego
samego przebiegu, i to było pierwsze uruchomienie tego pull requesta. Wniosek nie
zachodzi. Bramka wypisała (log joba `102136502392`, krok `assert_linecore_budget.py`):

```
[BUDZET-BRAMKA] zgloszonych 32, na planie 9 (srednio 5.08, czeka 0.98); 5.457 us/krok
przy progu 14.000; 0.070 % budzetu klatki; rozstep powtorzen 5.7 %
```

**Rozstęp 5,7 %** — wobec progu ostrzeżenia 22,5 % i granicy 100 %. Pomiar zrobiony obok
renderu jest o rząd wielkości bliżej pomiaru na pustej puli (4,0 %) niż tego, który
pozycję zrodził (102,6 %). Sparowany z tabelą §2:

| jobów naraz | co obok | rozstęp | µs/krok |
|---:|---|---:|---:|
| 2 | job nierenderujący | 4,5 % | 5,407 |
| **2** | **render Blendera** | **5,7 %** | **5,457** |
| 3 | — | 19,8 % | 5,649 |
| 12 | cztery rendery | 115,9 % (z zapisu) | 16,022 |

Różnica między wierszem pierwszym i drugim — 1,2 punktu rozstępu i 0,05 µs kosztu — jest
mniejsza niż różnica między dwoma a trzema jobami. **Nie „render obok", tylko LICZBA
jobów naraz jest zmienną, od której zależy mierzalność.** Premisa pozycji nazywała
winowajcą rodzaj sąsiada; pomiar wskazuje na ich liczbę.

### Czego ten pomiar NIE mówi

Nie mówi, że pula ma pojemność 1 ani 2 — mówi, co obsłużyła w oknie 16:01–16:17 dnia
08.09.2026. Tego samego dnia zmierzono chwilowe 5, 3 i 2 (§8), a rozstęp 115,9 % powstał
przy dwunastu jobach (§2). **Pojemność jest zmienna w czasie i nieogłoszona** — i to,
a nie żadna konkretna liczba, jest odpowiedzią tej pozycji na pytanie „ile jobów naraz
pula znosi". Zapis stałej „pojemność = N" byłby tą samą usterką, którą `CLAUDE.md` §9
opisuje przy liczbie maszyn: liczbą, która zestarzeje się po cichu, i to szybko —
w oknie jednej godziny pula pokazała tu 1 i 2, a rano 5.

Nie mówi też, że jeden render obok nigdy nie zaszkodzi. Mówi, że **jeden** nie
zaszkodził. Wiersz z dwunastoma jobami stoi w §2 dalej i nikt go nie odwołał; czterech
renderów naraz ten pomiar nie dotyczył.

### Cena, którą faza szeregowa nakłada na zestaw bramek

Jedenaście jobów obsługiwanych po jednym, po ~2–3 min każdy, to **28–33 min** na jeden
pull request licząc od zgłoszenia (zmierzone: od 16:01:24 do szóstego startu o 16:17:49
minęło 16 min przy sześciu jobach z jedenastu). Wariant serializacji z §6
(`concurrency`) w takim oknie nie odbiera **niczego**, bo równoległości i tak nie ma —
a w oknie z §2 odbierałby ~25 min. To ta sama konkluzja co w §6, zmierzona z drugiej
strony, i drugi powód, dla którego ten raport `concurrency` **nie wprowadza**.

### Rzecz uboczna, zmierzona przy okazji i warta zapisania

W tym samym logu przeszła kontrola negatywna bramki kosztu kroku z atrapą „wolną"
**wyliczaną z progu**, wprowadzoną dzień wcześniej po tym, jak literał `9.091` zmieścił
się w podniesionym progu 14,0 µs i kontrola zaczerwieniła się o pomiarze, który wolny
nie był. Log pokazuje wyliczoną wartość i odmowę:

```
BLAD: koszt kroku 15.400 us przekracza prog 14.000 us
kontrola negatywna: bramka odmówiła wolnego kroku i pomiaru jednego składu
```

15,400 = 14,000 × 1,1, czyli atrapa jest o 10 % nad progiem **bez względu na to, gdzie
próg stanie**. Piąta kopia progu, ta w docstringu `assert_linecore_budget.py`, nadal
mówi „8,0 µs" i jest osobną pozycją kolejki (6.D56) — ten raport jej nie tyka.

---

## 10. Najdłuższa zmierzona przerwa, i pomyłka w jej odczycie

Dopisane po §9, z tego samego powodu co §9: pomiar zdarzył się później.

**54 min 28 s bez ani jednego startu**, zmierzone 08.09.2026: ostatni job zakończony
przed przerwą to ponowienie `visual-regression` z przebiegu `34248481547`
(koniec **16:48:35**), pierwszy start po niej to `m7-shell` z przebiegu `34254662266`
na `woogitsu-linux-01` (**17:43:03**). Przerwa jest więc **o 21 minut dłuższa** od
poprzedniego maksimum (33 min) i to ona, a nie 33 min, jest dziś liczbą do zapamiętania
przy każdym „pula stoi".

**W środku tej przerwy odczytałem stan błędnie i to jest treść tego paragrafu, nie
przypis.** O 17:31, po 38 minutach bez startu, API pokazywało:

    status=in_progress  ->  0 przebiegów w CAŁYM repozytorium
    status=queued       -> 11 przebiegów, w tym TRZY z `push` na `main`
                           utworzone 16:52:54, czyli czekające 38 min
    wszystkie:  updated_at == created_at

Na tej podstawie napisałem, że sytuacja jest „inna w rodzaju" od wcześniejszego
czekania i zapowiedziałem uznanie jej za stan po stronie właściciela, bo runnery stoją
na jego maszynie. **Pula wróciła sama, dwanaście minut później.** Wniosek był
przedwczesny i jest tu wypisany, bo ta pozycja dotyczy dokładnie takich pomyłek:
odczytu, który brzmi jak diagnoza, a jest ekstrapolacją z ciszy.

Co w tym odczycie było prawdą, a co nie:

| przesłanka | czy prawdziwa |
|---|---|
| zero przebiegów `in_progress` w całym repozytorium | **tak**, zmierzone |
| joby `push` na `main` czekają 38 min | **tak**, zmierzone |
| `updated_at == created_at` u wszystkich | **tak**, zmierzone |
| „to nie jest kolejka za inną pracą, bo nic nie chodzi" | **tak**, i to jedyny wniosek, jaki z tego wynikał |
| „38 min > 33 min zmierzonego maksimum, więc poza normą" | **NIE** — maksimum było maksimum PRÓBKI, nie granicą zachowania; dziś ta sama próbka daje 54 min |
| „stan po stronie właściciela, nie do ruszenia stąd" | **NIE** — pula wróciła bez żadnej interwencji |

**Dwa rozróżnienia, które ta pomyłka wyostrzyła, i które są właściwym wynikiem §10:**

1. **Zero `in_progress` przy niezerowej kolejce NIE odróżnia „pula wyłączona" od
   „pula między jobami".** Obserwowalne jest to samo w obu wypadkach, a jedyna
   różnica leży w przyszłości. Żaden odczyt stanu przez API tego nie rozstrzyga —
   rozstrzyga wyłącznie upływ czasu, a ile go trzeba, nie wiadomo, bo maksimum
   przesuwa się z każdą nową próbką.
2. **Maksimum z próbki nie jest progiem.** Trzy dni temu maksimum wynosiło 16 min,
   dziś rano 33, dziś po południu 54. Wpisanie któregokolwiek z tych progów
   w narzędzie („po X minutach uznaj pulę za martwą") powtórzyłoby usterkę stałej
   „pojemność = N" z §9: liczba zestarzeje się po cichu, a bramka zacznie ogłaszać
   awarię tam, gdzie jest kolejka.

Czego z tego **nie** wynika: że pula nigdy nie stoi. Zakleszczenie z §5 (`34209969496`,
`updated_at` niezmienione **90 minut** przy dziewięciu przeszłych jobach rodzeństwa)
było prawdziwym zawieszeniem i wymagało `cancel` + `rerun`. **Odróżniało je od dzisiejszej
przerwy to, że rodzeństwo tego samego pull requesta W TYM CZASIE przechodziło** — czyli
pula pracowała, a stał jeden run. Dziś nie pracowało nic, i właśnie dlatego `cancel +
rerun` byłby tu bezcelowy: requeue nie budzi runnera, którego nie ma. **To jest jedyny
sygnał, jaki ten pomiar daje na odróżnienie tych dwóch stanów** — nie czas oczekiwania,
a to, czy w tym czasie przechodzi cokolwiek innego.
