# 6.D268 — siedem nieprawdziwych liczb, których nie widzi nic

**Data:** 18.09.2026 · **Gałąź:** `claude/6d268-pokryte-przypadkiem` · **Baza:** `3c686e7`

## 1. Odpowiedź na pole „Wyjście"

Liczb pokrytych zbiegiem cyfr jest **49**, w **22** plikach. Podział przez
przeczytanie 49 zdań: **21** twierdzi o dzisiejszym drzewie (grupa A), **28** nie
twierdzi (grupa B) — bo opisuje pomiar przebiegu, cytuje dawną wartość, nazywa
commit jako punkt odniesienia albo opisuje zachowanie narzędzia, a nie liczebność.

Z grupy A **siedem** twierdzeń jest dziś nieprawdziwych, wszystkie w jednym
module, i **nie widzi ich nic**:

| miejsce | twierdzenie | proza | drzewo |
|---|---|---|---|
| `test_dead_constants_csharp.py:66` | deklaracji razem | 389 | **396** |
| `:83` | `const` | 304 | **307** |
| `:83` | `static readonly` | 85 | **89** |
| `:83` | razem w rozkładzie | 389 | **396** |
| `:84` | bez modyfikatora dostępu | 43 | **45** |
| `:91` | bez modyfikatora dostępu (drugie zdanie) | 43 | **45** |
| `:91` | zostaje po odjęciu | 346 | **351** |

Ósma liczba, „Zapas 59" z `:72`, jest również nieprawdziwa (dziś 66), ale jest
POCHODNĄ sumy: fałszywa dlatego, że fałszywa jest suma, która na liście stoi.
Na listę nie weszła, bo jej porównanie wymagało sięgnięcia po `MINIMUM_DEKLARACJI`,
a to dało tej zapadce DRUGIE użycie i zapaliło bramkę z 6.D254, która wtedy żąda
zmierzenia jej klasy mutacją. Cena wyższa od zysku.

**Dowodem tezy pozycji jest sam stan bazowy, a nie mutacja:** siedem twierdzeń
jest nieprawdziwych, a `python3 tools/tests/test_all.py` daje `2595/2595`. Bramka
6.D259 ich nie widzi, bo są „pokryte"; bramka 6.D264 liczy je jako pokryte, czyli
działa dokładnie tak, jak 6.D264 opisało — i dlatego ta pozycja istniała.

## 2. Podziału NIE DA SIĘ zmechanizować — zmierzone czterema próbami

Nie jest to ocena ani wygoda. Cztery kolejne próby, każda z inną usterką:

1. **Znaczniki przeszłości z `test_docs_ci_claims.HISTORICAL_MARKERS`** zawierają
   `"zmierzone"`, które pada w niemal każdym akapicie tego repozytorium. Podział
   byłby artefaktem listy zbudowanej do innego pytania.
2. **Znaczniki czytane ze ZDANIA** gubią punkt odniesienia, bo ten stoi zwykle
   w pierwszym zdaniu akapitu — `test_assertion_gate.py:66` otwiera się
   „Zmierzone 11.09.2026 na `e0543cd`", a zdanie z liczbą jest trzecie.
3. **„Akapit" bez sklejania z 6.D267** to jeden wiersz, bo `proza` zwraca po
   jednym wpisie na WIERSZ komentarza. Sklejanie z poprzedniej pozycji weszło tu
   od razu w użycie.
4. **Zawężenie do akapitów, które NAZYWAJĄ swój czytnik w grawisach**, daje pięć
   pozycji i **nie obejmuje tej, w której rozjazd faktycznie jest**: akapit
   o deklaracjach C# nazywa `const` i `static readonly`, a nie `rozklad`.

Do tego trzy porównania mechaniczne dały **trzy fałszywe rozjazdy**, każdy z tego
samego powodu — porównałem liczbę z czytnikiem, którego jej zdanie nie opisuje:
`2377` z `BEZ_KOMUNIKATU_RAZEM` (to są asercje C#, a zdanie mówi o pythonowych,
mierzonych na `e0543cd`); `44` z `pokrycie_pogrubionych()["bez pokrycia"]` (zdanie
opisuje czytnik KOMUNIKATÓW, z oknem symetrycznym); `20` bez czytnika w ogóle.
Jest to ten sam błąd, który popełniłem przy 6.D267 na luzach progów — **trzeci raz
w dwóch pozycjach**, i za każdym razem złapany przez przeczytanie źródła, nie
przez bramkę.

## 3. Czego pilnuje nowa bramka

Trzy równości w `test_message_claims.py`, czyli w module, który pole „Weryfikacja"
tej pozycji nazwało poprawnie:

* **rozkład 49 po plikach**, nie sama suma — 6.D267 zmierzyło, że suma
  przesunięcia między członami nie widzi, a tu członem jest plik. Porównywany
  w obie strony, plus asercja, że sumuje się do `POKRYTYCH_ZBIEGIEM_CYFR`;
* **siedem rozjazdów jako DŁUG**, z obiema stronami przeliczanymi z drzewa.
  Bramka zapala się także wtedy, gdy ktoś liczbę POPRAWI — wpis przestaje być
  rozjazdem i ma zniknąć z listy. Nie jest to karanie poprawności (6.D27), bo
  poprawa jest ruchem o dwa kroki, a lista bez sprawdzania jest napisem (6.D243);
* **licznik pokrycia jest WIDOKIEM na listę**, nie osobnym przebiegiem.
  `pokrycie_pogrubionych` deleguje od dziś do `pozycje_pokrycia`, a osobna
  asercja pilnuje, żeby rozszczepienie ich z powrotem padło głośno (6.D213).

## 4. Kontrole negatywne — przewidywania spisane PRZED przebiegami

| kontrola | przewidziane | zmierzone |
|---|---|---|
| KN-a: POPRAWIENIE prozy `const` 304 → 307 | czerwień z żądaniem zdjęcia wpisu | **za pierwszym razem NIE zapaliła** — patrz niżej; po naprawie: `FAIL … te twierdzenia przestaly byc rozjazdami … [('test_dead_constants_csharp.py', 'const')]` |
| KN-b: zepsucie liczby ZGODNEJ 139 → 138 | bramki pokrycia MILCZĄ, zapala 6.D263 | **przewidywanie NIE POTWIERDZIŁO SIĘ**: zapaliły też bramki pokrycia (zbieg 49 → 50), bo zmiana wartości zmieniła KLASĘ pokrycia; 6.D263 zapaliła jak przewidziano |
| stan bazowy z siedmioma fałszywymi liczbami | cały zestaw zielony | `2595/2595 przeszło` |

**KN-a złapała kształt 6.D27 w mojej własnej, nowej bramce.** Pierwsza wersja
`rozjazdy_z_drzewa` mierzyła stronę DRZEWA, a stronę PROZY miała **wpisaną z ręki**.
Poprawienie liczby w prozie nie ruszało więc niczego w tej funkcji i bramka nie
umiała zobaczyć poprawy — a jej własny docstring twierdził, że umie. Była nim
przez jeden przebieg; teraz obie strony są czytane, kotwicami zdań (nie numerami
wierszy), a osobne dolne ostrze pilnuje, żeby każda kotwica łapała DOKŁADNIE jedno
zdanie — kotwica łapiąca dwa czytałaby pierwsze dla obu opisów.

**KN-b jest przewidywaniem, które się nie potwierdziło, i zostaje zapisane jako
takie.** Sądziłem, że bramki pokrycia przemilczą zmianę wartości; zapaliły, bo
`138` ma w swoim oknie inne pokrycie niż `139` i liczba przeszła ze `zbiegu` do
innej kupki. Census jest więc czulszy, niż zakładałem — ale nie na
NIEPRAWDZIWOŚĆ, tylko na zmianę klasy pokrycia, i siedem fałszywych liczb
w stanie bazowym tego dowodzi.

## 5. Pełna lista 49 z adresami

Adresy z numerami wierszy stoją tu, a nie w bramce: numer wiersza rusza się przy
każdym dopisanym akapicie, a liczba per plik nie. Litera `A`/`B` to grupa.

| # | grupa | adres | liczba | zdanie |
|---|---|---|---|---|
| 1 | B | `csharp_pins.py:202` | 0 | całkowitych 336, z tolerancją **0** |
| 2 | B | `csharp_test_methods.py:2` | 13 | jest **13** i **wszystkie** maja atrybut testowy. Pomocniki sa tu `private static` |
| 3 | B | `mutation_sweep.py:378` | 0,224 | #: **0,224 s**. Klucz kosztuje 0,6 % tego, co oszczedza. |
| 4 | B | `mutation_sweep.py:462` | 7 | #: Bez `--only` chodzi **7** wywolan i te obejmuja wszystkie 63 cele. |
| 5 | B | `test_all.py:560` | 0 | a kod wyjścia i tak wyszedł **0** — wyrocznia nie zgadzała się z własnym wypisem. |
| 6 | B | `test_assertion_gate.py:66` | 2377 | #: z czego **3887** niesie komunikat, a **2377** nie niesie żadnego — w **103** |
| 7 | B | `test_assertion_gate.py:1909` | 1,0 | #: mieści się **386**, a wszystkie 12 wykonalnych kosztowałoby **1,0 s** — 3 % zapasu. |
| 8 | A | `test_bin_path_framework.py:157` | 29 | #: plus ten commit): **29** ścieżek `bin/…/netX.Y/` w `reports/` i `docs/`, w 8 plikach, |
| 9 | A | `test_bytecode_staleness.py:516` | 139 | #: `tools/tests` **139**, `tools/blender` 29, `tools/track` 23, `tools/ci` 9, |
| 10 | B | `test_bytecode_staleness.py:524` | 136 | #: nieprawdziwe, kazde inaczej. Komentarz mowil o `tools/tests` **136** przy 139 |
| 11 | B | `test_csharp_assertions.py:408` | 54 | #: `test_lista_asercji_C_bez_komunikatu_moze_tylko_malec` zapaliła się na **54** |
| 12 | A | `test_dead_constants_csharp.py:66` | 389 | #: ma dzis **389** deklaracji, wiec podloga stala **189** nizej, czyli 48,6 % populacji, |
| 13 | A | `test_dead_constants_csharp.py:72` | 59 | #: wylaczona, nie poprawiona (6.D27). Zapas **59** (15,2 %) jest dobrany POMIAREM |
| 14 | A | `test_dead_constants_csharp.py:83` | 304 | #: `const` **304**, `static readonly` **85**, razem **389**; bez modyfikatora dostepu |
| 15 | A | `test_dead_constants_csharp.py:83` | 85 | #: `const` **304**, `static readonly` **85**, razem **389**; bez modyfikatora dostepu |
| 16 | A | `test_dead_constants_csharp.py:83` | 389 | #: `const` **304**, `static readonly` **85**, razem **389**; bez modyfikatora dostepu |
| 17 | A | `test_dead_constants_csharp.py:84` | 43 | #: stoi **43** z nich (`public` 145, `private` 201). |
| 18 | A | `test_dead_constants_csharp.py:91` | 43 | #: zabiera **43** deklaracje, zostaje **346** — i SUME przechodzi nawet przy progu 330. |
| 19 | B | `test_dotnet_version.py:1556` | 2 | **2**, pin spełniony **4**, brak SDK **3**. Wpis kolejki mówił o trzech — trzy |
| 20 | A | `test_field_paths.py:1070` | 200 | # src/Game` w środku zdania. Zmierzone na całym `docs/TASKS.md`: **200** wystąpień |
| 21 | A | `test_game_needle_specificity.py:283` | 45 | #: i **45** roznych igiel w **53** mierzalnych wywolaniach z **64** o tym ksztalcie. |
| 22 | B | `test_json_required.py:76` | 108 | # jest commit, na którym przypięto **108**, nie 116 — sto szesnaście przypięto trzy |
| 23 | A | `test_mass_copies.py:32` | 4 | #: w rejestrze zapala **4** testy z 2346 i pinu z `test_all.py` NIE ma wśród nich; |
| 24 | A | `test_mass_copies.py:33` | 6 | #: podmiana w referencji zapala **6** i pin jest wśród nich. Testy niżej wykonują obie |
| 25 | A | `test_message_claims.py:236` | 44 | #: liczba w zdaniu. Populacja spada do **280**, a bez pokrycia zostaje **44** — |
| 26 | A | `test_mutation_sweep.py:883` | 15 | za `import bpy` daje dzis **15** modulow, a nieosiagalnych jest **10** — |
| 27 | B | `test_mutation_sweep.py:1111` | 6 | 6.D5 nazywa je wprost: `tools/track/crs.py` **6** ocalałych po triażu |
| 28 | B | `test_mutation_sweep.py:1111` | 2 | **2** (`reports/mutation-triage-png-metadata.md`). Te dwie liczby są historyczne |
| 29 | B | `test_mutation_sweep.py:2298` | 0 | daje w drzewie kod **0** i PUSTY wypis, bo modul bez `__main__` uruchomiony |
| 30 | A | `test_prose_counts.py:384` | 1 | prawdziwych deklaracji stoi na **4** w całym drzewie, z czego **1** jest żywa |
| 31 | A | `test_provenance_classes.py:604` | 20 | wyłącznie `data/vehicle/m7-spec.json`. Pole `status` stoi w **20** plikach JSON |
| 32 | B | `test_report_claims.py:1849` | 201 | #: bo rozszerzenie przesuwa populacje o 32 sekcje.** Zmierzone na `e1c63f7`: **201** |
| 33 | B | `test_report_claims.py:1850` | 197 | #: sekcji w **197** raportach, **271** twierdzen liczbowych. |
| 34 | A | `test_report_claims.py:1937` | 35 | #: slajs wąski ma **35** pozycji, a slajs szeroki (zakres nazwany + orzeczenie |
| 35 | A | `test_report_claims.py:1949` | 35 | #: slajs wąski ma **35** pozycji, przy **20** — **17**, czyli mniej niż połowę. Okno |
| 36 | B | `test_report_claims.py:1116` | 1 | `actions/checkout` bez tego wejścia daje głębokość **1**, więc `git log -G` nie ma |
| 37 | A | `test_report_hygiene.py:175` | 90 | #: plików): wzorzec `{7,40}` łapie w nagłówkach **90** tokenów, a ich długości to |
| 38 | B | `test_report_hygiene.py:228` | 153 | #: i wyliczała z tego **153** („152 plus raport, który ten commit dokłada"). Między |
| 39 | B | `test_report_hygiene.py:895` | 6,99 | #: 2016 wymaganych, czyli **6,99** ścieżki na raport przy podłodze żądającej 7. |
| 40 | B | `test_report_hygiene.py:911` | 8,00 | #: Ostatnie 50 dodanych ma **9,06** ścieżki na raport, ostatnie 30 — **8,00**, |
| 41 | B | `test_suite_runtime_budget.py:82` | 0,991 | #: kontener sesji, jeden przebieg **170,685 s** ściany, CPU/ściana **0,991** |
| 42 | B | `test_suite_runtime_budget.py:277` | 440,0 | #: Wybrane **440,0** leży pod obiema (marginesy `1,942` i `2,172`), czyli jest odrobinę |
| 43 | B | `test_suite_runtime_budget.py:365` | 0,75 | #: przedziału to 0,719; wybrane **0,75** zostawia 24 % zapasu pod spokojnym |
| 44 | B | `test_suite_runtime_budget.py:386` | 0,992 | #: **517,499 s** przy progu 440,0 s, stosunkiem CPU/ściana **0,992** i zestawem zielonym |
| 45 | B | `test_suite_runtime_budget.py:403` | 0,992 | #: `docker-runner-02`, job `tools`, PR #633 CPU/ściana **0,992** |
| 46 | B | `test_suite_runtime_budget.py:432` | 0,75 | #: **0,75** — w swoim dniu prawdziwie. **6.D108 zabrania go przepisywać**, więc nie |
| 47 | B | `test_suite_runtime_budget.py:1023` | 1,000 | # Do tego dnia stało tu `werdykt(prog+10, prog+10)`, czyli stosunek **1,000** — |
| 48 | B | `test_suite_runtime_budget.py:2363` | 0,001 | o **0,001** pod podłogą, a jego CPU stoi **125 %** progu. Pod starą podłogą 0,75 |
| 49 | B | `test_t401_citation.py:55` | 58,68 | #: Wiersz tabeli §4: `\| L5_D \| 57,64 \| **58,68** \| +1,04 \| ... \| ... \|` |

Grupa B liczy **28** pozycji, grupa A — **21**; suma stoi przybita w bramce razem
z sumą per plik, więc rozjechać się nie może po cichu.

## 6. Czego świadomie nie zrobiono

**Siedmiu nieprawdziwych liczb NIE poprawiono** i jest to decyzja zakresu, nie
przeoczenie: pole „Poza zakresem" tej pozycji zabrania poprawiania znalezionych
liczb poza wypisaniem ich. Zostają więc w drzewie — ale wypisane, przybite listą
porównywaną w obie strony i przypisane pozycji **6.D271**, która je poprawia.
Dług jest widoczny i policzony, a nie przemilczany.

Nie ruszono okna, wzorca pogrubienia ani zapadki górnej — to jest 6.D259 i jej
pole „Poza zakresem". Nie ruszono 15 liczb pokrytych przypisaniem stałej.

Dla **14** pozycji grupy A poza modułem deklaracji C# zgodność z drzewem nie
została sprawdzona i powód jest nazwany: każda wymaga wskazania czytnika, który
mierzy tę właśnie rzecz, a wskazania tego nie ma w tekście — cztery próby
zmechanizowania go opisuje §2. Jedna z nich jest sprawdzona i ZGODNA (`tools/tests`
139, potwierdzone przy 6.D267). To jest zmierzona granica tej pozycji, a nie
zawężenie jej zakresu w milczeniu.
