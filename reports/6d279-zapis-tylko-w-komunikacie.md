# 6.D279 — zapis, który istnieje tylko w komunikacie commita

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `4a9529f`

## 1. Cztery liczby

Populacja: wszystkie **1012** commitów `git log`. Czytniki pożyczone — rejestr nazw
zapadek z `tools/tests/test_tree_walks.py::ZAPADKI`, bez własnej listy nazw.

| | co | ile |
|---|---|---|
| **A1** | komunikatów ZGŁASZAJĄCYCH zmianę zapadki (nazwa z rejestru, a **po niej** para wartości) | **218** |
| **A2** | z tego takich, u których zmianę widać w DIFFIE tego samego commita | **217** |
| **B1** | komunikatów zgłaszających WYKONANĄ kontrolę negatywną | **468** |
| **B2** | z tego takich, u których w drzewie stoi jej ślad (raport w `reports/` albo plik testu) | **464** |

Różnice: **A1 − A2 = 1**, **B1 − B2 = 4**. Para odwrotna — commity, których diff
zapadkę rusza, a komunikat nie wymienia jej ani razu — liczy **152**.

Adresy. Zgłoszone bez widocznego: `8ae17c40`. Zgłoszona kontrola bez śladu:
`3f40cd09`, `758fe8f7`, `c0afb220`, `e940dc9e`.

## 2. Liczby zależą od szerokości kotwicy, i to jest ZMIERZONE, nie zastrzeżone

| kotwica | ile |
|---|---|
| A, para wartości **po** nazwie (przyjęta) | **218** |
| A, para wartości także **przed** nazwą | **225** |
| B, fraza + `KN-N`, z wymogiem śladu wykonania (przyjęta) | **468** |
| B, dodatkowo samo `KN` | **475** |
| B, sama fraza, bez wymogu śladu wykonania | **458** |

Granica „zgłasza wykonaną" wobec „wspomina o kontroli" jest **progiem czytnika,
a nie faktem w drzewie**. Dlatego stoją tu wszystkie trzy warianty B, a różnicę
między wariantami A pilnuje osobny test — gdyby oba zaczęły dawać to samo, sito
przestałoby rozróżniać to, co rozróżnia dziś.

## 3. `--diff-merges=first-parent` zmienia wynik i jest rozstrzygnięciem, nie wygodą

Domyślnie `git log -p` **pomija diff scalenia w całości**, a scalenia tego
repozytorium niosą w komunikacie te same zgłoszenia co commity gałęzi. Bez tego
przełącznika kilkanaście scaleń wpada do pary „zgłoszone bez widocznego" z powodu
czysto technicznego. Sprawdzone na `bb3896e8` (komunikat mówi o zapadce 8 → 12):

```
$ git show --format= bb3896e8 | grep -cE '^[+-] *MINIMUM_DOCUMENTED_ITEMS *='
0
$ git show --format= --diff-merges=first-parent bb3896e8 | grep -E '^[+-] *MINIMUM_DOCUMENTED_ITEMS *='
-MINIMUM_DOCUMENTED_ITEMS = 8
+MINIMUM_DOCUMENTED_ITEMS = 12
```

## 4. Mój pierwszy czytnik nie zgadzał się z pomiarem rozpoznania — i to ja się myliłem

Pierwsza wersja dała **225 / 223 / 493 / 489** zamiast 218 / 217 / 468 / 464.
Dwa powody, oba merytoryczne i oba po mojej stronie:

1. kotwica A szukała pary wartości w **całym** oknie wokół nazwy, a nie po nazwie —
   przez co para stojąca przy jednej nazwie liczyła się także nazwie sąsiedniej,
   a komunikat wymieniający kilka podniesionych zapadek naraz jest tu zwykłym kształtem;
2. kotwica B liczyła **wzmianki** o kontroli zamiast kontroli **wykonanych** — a pole
   „Wyjście" tej pozycji mówi wprost „zgłasza WYKONANĄ kontrolę negatywną".

Po poprawieniu **A odtwarza się co do jedności**. B zostaje węższe od rozpoznania
ze świadomego wyboru: nie przyjmuję samego `KN`, bo skrót jest wieloznaczny — i obie
liczby stoją w §2.

## 5. Wyprodukowałem żywą instancję zjawiska, które ta pozycja mierzy

Mój własny commit 6.D278 (`4a9529f`) **wykonał kontrolę negatywną** — jej wyjście
stoi w raporcie i w opisie PR — a jego komunikat nie zawiera ani razu słowa
„kontrol". Detektor komunikatów go nie widzi:

```
$ git log -1 --format=%B 4a9529f | grep -c "kontrol"
0
```

Przewidywałem, że po moich dwóch commitach obie pary urosną o dwa. Para A urosła,
para B nie — i dopiero to pokazało mi, dlaczego. Przypadek jest **przybity jako
kontrola przyrządu**: sito liczy zgłoszenia, więc ma go NIE liczyć; gdyby zaczęło,
mierzyłoby wykonania, o których nic nie wie.

## 6. Kontrole

**Negatywna.** Mutacja na kompletnej kopii drzewa (213 plików `.py`, 398 raportów,
razem z `.git`, bo moduł czyta historię): `zglasza_i_widac` liczone z KOMUNIKATU
zamiast z diffa, czyli sito przestaje sprawdzać zgodność, o której mówi. Wynik:

```
FAIL test_komunikat_zglaszajacy_zapadke_ktorej_diff_NIE_rusza_jest_zgloszony:
     commit 8ae17c4 trafil do `zgloszone i widoczne`, a jego diff zapadki nie rusza
4/5 przeszło
```

Przewidywałem **dwie** czerwienie; jest jedna. Asercja podzbioru nie zapala się,
bo po mutacji zbiór staje się **równy**, a nie większy — i tak to zapisuję,
zamiast poprawiać przewidywanie.

**Przyrządu, trzy różne.** Commit zmieniający zapadkę bez wzmianki w komunikacie
(`d833c41c`) ma trafić do pary odwrotnej, a nie wypaść z obu. Commit z kontrolą
wykonaną, ale niezgłoszoną (§5), ma NIE być liczony. Szerokość kotwicy A ma dawać
liczbę **różną** od wąskiej.

**Bramki tej serii złapały mnie trzy razy na tym jednym module:**

1. **Moja własna bramka z 6.D277** znalazła w nim `\b` przy cyfrze (`\bKN-\d+\b`) —
   nowy wzorzec dokładałby się do zbioru, który tamta pozycja właśnie przybiła.
2. **Pierwsza poprawka tego wzorca była błędna, i złapała ją podłoga:** `(?![\d,.])`
   gubi etykietę `KN-1` kończącą zdanie **kropką**, bo kropka zdaniowa nie jest
   separatorem dziesiętnym. Populacja spadła o jeden, `468 → 467`. Poprawne jest
   węższe `(?!\d)`.
3. **Klasyfikator klas zapadek** uznał moje pięć stałych za `poza skanem`, bo
   porównywałem je w pętli, a nie gołą nazwą — czyli wypisywał „nie pilnuje ich nic"
   o progach, które pilnują. Asercje przepisane na gołe nazwy.

## 7. Czego ta pozycja nie ruszała

**Bramki odrzucającej commit po treści komunikatu tu nie ma i jest to wybór, a nie
przeoczenie.** Komunikatu nie da się poprawić bez przepisania historii, więc taka
bramka ma zupełnie inny koszt i jest osobnym rozstrzygnięciem — tak stoi w polu
„Poza zakresem". Nie przybiłem też RÓŻNICY A1 − A2 jako zapadki górnej, bo to jest
ta sama bramka tylnymi drzwiami.

## 8. Co zauważyłem przy okazji, a czego nie tknąłem

1. **Para odwrotna liczy 152 commity** — czyli ruch zapadki bez wzmianki w komunikacie
   jest w tym repozytorium **kilkadziesiąt razy częstszy** niż wzmianka bez ruchu.
   To jest odwrotność tego, czego szukała ta pozycja, i nikt tej liczby nie zamawiał.
   Nie wyciągam z niej wniosku: żeby coś znaczyła, trzeba by odróżnić podniesienie
   rutynowe (census po dodaniu pliku) od zmiany progu, która jest decyzją.
2. **Cztery commity zgłaszają kontrolę bez śladu w drzewie**, a trzy z nich to prace
   sprzed wprowadzenia konwencji raportów w `reports/`. Kryterium śladu jest szczelne
   od góry, nieszczelne od dołu: sprawdza, czy w commicie stoi raport albo test,
   a nie czy ten raport opisuje TĘ kontrolę.
