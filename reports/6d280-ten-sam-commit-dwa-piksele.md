# 6.D280 — ten sam commit, dwie maszyny, jedna klatka inna

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `91c50df`

## 1. Trzy liczby

| | co | ile |
|---|---|---|
| **L1** | par „ten sam commit, dwie maszyny" dających się porównać w artefaktach CI | **1** |
| **L2** | z tego takich, gdzie `idat_sha256` przynajmniej jednego PNG się różni | **1** |
| **L3** | kamer, które się rozjeżdżają | **1** — `LOD2/axis75` |

Populacja, z której to wyszło: **757** przebiegów `tunnel-alignment.yml`, **2194**
artefaktów o przedrostku `t-210-tunnel-`, z czego niewygasłych **1744**. **Żaden**
commit nie ma więcej niż jednego przebiegu — pary powstają wyłącznie z ponowień.
Par-wykonań jest **20**, z tego dwumaszynowych **17**, a komplet artefaktów ma
**jedna**: przebieg `35332005261`, job `tunnel-alignment (L2_E)`, SHA `bc1685b7`,
artefakty `-1` i `-2`.

Rozjazd na `LOD2/axis75`: `ink` **0,493582** wobec **0,041489**, czyli blisko
**dwunastokrotnie**. Siostrzane kamery `axis05`, `axis25`, `axis50` z tej samej
próby są bit-identyczne.

## 2. Wartość, którą pole „Wyjście" nazywa NIEODCZYTANĄ — odczytana

Pozycja zapisała wprost, że `ink` dla `axis75` w przebiegu, który **przeszedł**,
nie została odczytana, bo leżała poza oknem logu, i ma zostać odczytana
z artefaktu, a nie zgadnięta z tego, że job był zielony.

Odczytana z `t-210-tunnel-L2_E-35332005261-2`, trzema zgodnymi drogami:

```
report.txt w. 491:  [LOD] tusz siatki axis75: LOD 0 0.0971 -> LOD 2 0.0415 (-57.3%)
LOD2-render-sanity.json, kamera axis75:  ink_fraction = 0.041489
przeliczone z LOD2_axis75.png:           0.041489
```

Próba czerwona w tym samym wierszu: `LOD 2 0.4936 (+408.4%)` i zaraz pod nią
`BŁĄD: LOD 2 nie ma rzadszej siatki niż LOD 0 na: axis75`. Pierwsze 490 wierszy
obu `report.txt` są identyczne.

## 3. Pole „Wejście" wskazuje sumę, która NIE NADAJE SIĘ do tego porównania

Metadane niosą dwie sumy na klatkę: `sha256` całego pliku PNG i `idat_sha256`
samych pikseli. Pole „Wejście" tej pozycji mówi o `sha256`. Zmierzone:

| para | różnych po `idat_sha256` | różnych po `sha256` pliku |
|---|---|---|
| dwie maszyny (`L2_E`, 21 klatek wspólnych) | **1** | **21** |
| **jedna** maszyna (`L1_B`, 37 klatek wspólnych) | **0** | **37** |

Suma całego pliku różni się na **każdej** klatce także tam, gdzie piksele są
bit-identyczne. Sito zbudowane na niej zgłasza więc każdą parę — i rozjazd,
i jego brak — a to jest dokładnie kształt, przed którym ostrzega pole
„Kontrola przyrządu" tej pozycji. Porównuje się `idat_sha256`.

**Tego nie przewidziałem.** Przed pomiarem zapisałem, że obie sumy dadzą dla
tej pary ten sam werdykt.

## 4. Czego z tego pomiaru NIE wolno wyciągnąć

**Para porównywalna jest w całej historii jedna.** Z próby o liczności jeden nie
wychodzi ani częstość zjawiska, ani to, czy `axis75` jest kamerą wyróżnioną.

**Szesnaście par dwumaszynowych nie ma kompletu artefaktów — i to jest BRAK
POMIARU, a nie „zero różnic".** Powody są zmierzone, nie zgadnięte: czerwona próba
zwykle nie dochodzi do kroku wysyłki (`No files were found with the provided path`),
a **ponowienie „re-run all jobs" KASUJE artefakty poprzedniej próby** — job
`100155349060` wgrał artefakt `9835478468`, a zapytanie o niego daje dziś **404**,
nie „expired". Przy „re-run failed jobs" artefakt pierwszej próby zostaje.

**Przyczyny rozjazdu nie ustaliłem i nie mogłem:** wymagałaby uruchomienia
Blendera, którego w tym środowisku nie ma — `CLAUDE.md` §2 każe wtedy przerwać
i powiedzieć o tym, a nie kombinować. Identyczne w obu próbach są: scalanka,
`sha256` źródłowego GLB, liczba obiektów, wierzchołków i ścian, wersja Blendera,
silnik, wersja manifestu i **każde pole wpisu kamery `axis75`**.

## 5. Dwa sprostowania do treści pozycji

1. Pozycja nazywa maszyny `actions-runner-metro-03` i `-01`. To są **katalogi
   instalacji runnera** widoczne w ścieżkach logu; `runner_name` w API to
   `metro-wsl-DOM-NEW-03` i `metro-wsl-DOM-NEW-01`. Ta sama para egzemplarzy,
   inny zapis.
2. **Oba joby raportują `Machine name: 'DOM-NEW'`** i ten sam katalog domowy.
   Czy to dwa hosty, czy dwa egzemplarze runnera na jednym — z logu nie widać.
   Zdania „różnicą jest maszyna" **nie uznaję za zamknięte**.

## 6. Kontrole

**Negatywna.** Sito oślepione (`rozjazdy` zwraca pustą listę), na kompletnej kopii
drzewa (215 plików `.py`, 399 raportów):

```
FAIL test_para_z_DWOCH_maszyn_rozjezdza_sie_na_jednej_klatce: klatek o roznych pikselach jest 0, a pomiar dal 1: []
FAIL test_suma_CALEGO_PLIKU_zglasza_KAZDA_pare_i_dlatego_sie_jej_nie_uzywa: suma calego pliku rozni sie na 0 z 21 klatek
2/4 przeszło
```

Przewidywałem **jedną** czerwień; są **dwie**. I to samo przewidywanie pokazuje,
czemu kontrola przyrządu musi być osobnym testem: **`test_para_z_JEDNEJ_maszyny…`
przechodzi na oślepionym sicie celująco**, bo tam pusta lista jest oczekiwanym
wynikiem. Sito, które nie widzi nic, zdaje kontrolę „nie zgłaszaj wszystkiego"
najlepiej ze wszystkich.

**Przyrządu, dwie różne.** Para z jednej maszyny ma pozostać zielona — jest,
na 37 klatkach. Czytnik metadanych sprawdzany osobno, na pliku zapisanym w locie:
bez tego testy porównywałyby słowniki między sobą i przeszłyby nawet wtedy, gdyby
czytnik przestał czytać z pliku to, co w nim stoi.

## 7. Co zauważyłem przy okazji, a czego nie tknąłem

1. **`report.txt` zielonego przebiegu zawiera słowo `BŁĄD` dwa razy** — w wierszu
   118 (`oś nie ma profilu pionowego (T-112), wariant production niedozwolony`)
   i 2569 (`wynik nie zapisuje się do data/ — to jest katalog tylko do odczytu`).
   To są oczekiwane kontrole negatywne wypisywane w toku, nie awarie, ale przez
   nie grep po słowie `BŁĄD` nie odróżnia zielonego przebiegu od czerwonego.
2. **W parze kontrolnej `34689512388` pierwsza próba była czerwona przy 28 z 28
   renderów bit-identycznych** — czyli jej czerwień nie wzięła się z obrazu.
   Skąd się wzięła, nie sprawdzałem.
3. **Proza opisująca własną klasyfikację jest układem SAMOZWROTNYM i ma punkt stały.**
   `test_message_claims.py` niesie wyliczenie „ile liczb jest pokrytych prozą, ile kodem,
   ile mieszanie" — a te liczby same są liczbami w prozie i same wchodzą do klasyfikacji,
   którą opisują. Podniesienie ich po dodaniu tej pozycji zmieniło pomiar, który je
   wyznacza, i zbiegło dopiero po **jednej** iteracji. Rozwiązałem to szukając punktu
   stałego mechanicznie, a nie wpisując wartość, która „powinna wyjść".
   **Bramka złapała przy tym moją własną nieprawdziwą prozę:** podniosłem stałe i zostawiłem
   zdanie mówiące stare wartości, przez co liczby przestały pasować do swoich przypisań
   i zjechały do klasy `zbieg`. To nie była kruchość okna, tylko nieaktualne zdanie —
   i dokładnie po to ta bramka istnieje. Samego mechanizmu nie tknąłem: to jest 6.D284.
4. **Komparator nie jest wpięty do żadnego workflowa** i jest to wybór: wpięcie
   go znaczy zmianę CI, a tej pozycja nie obejmuje. Dziś porównuje sumy przybite
   w module testowym; żeby porównywał artefakty żywego przebiegu, ktoś musi
   dołożyć krok pobierający artefakt poprzedniej próby.
