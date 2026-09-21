# 6.D341 · Per-modułowego CZASU CPU w artefakcie NIE MA — a na ścianie osiemdziesiąt procent przyrostu robi dziesięć modułów, z czego sześć to czytniki prozy

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `cd9fa69`

**POMIAR POWTÓRZONY PRZED COMMITEM — i powtórzenie ZNALAZŁO WŁASNOŚĆ PRZYRZĄDU, której ten raport wcześniej nie miał.** Przyrząd tej pozycji został zachowany, dane też (570 artefaktów), więc uruchomiłem go ponownie na bazie `473d9dd`. Wszystkie liczby odtwarzają się identycznie — 117,072 s sumy, 42,655 s klasy „doszedł", 93,896 s dziesiątki, 80 %, `TO SAMO: True` — **z jednym wyjątkiem**: klasa „istniał" dała w trzech kolejnych przebiegach **74,418 / 74,418 / 74,417 s**, a z ustalonym ziarnem haszowania dwa razy 74,418.

**Przyczyna jest w kodzie przyrządu i jest zlokalizowana, a nie zgadnięta:** pętla idzie `for m in M0 | M1`, czyli po **zbiorze napisów**, a akumulacja robi `sumy[klasa] += v["delta"]` w kolejności, którą ten zbiór narzuca. Kolejność zbioru napisów zależy od ziarna haszowania procesu, a dodawanie `float` nie jest łączne. Różnica to **jedna tysięczna sekundy na 74**, czyli 1,3·10⁻⁵ względnie, i **nie zmienia żadnego wniosku poniżej** — ale jest zmierzoną własnością przyrządu, więc stoi tutaj, a nie w milczeniu. Ile bramek w drzewie sumuje tak samo, jest osobnym pytaniem i stoi jako 6.D350.

Daty pomiaru NIE przepisuję na dzisiejszą — liczby zmierzono 21.09.2026 na bazie `cd9fa69`.

6.D332 §2.1 zmierzyło, że zestaw podrożał od dnia ustawienia progu o **147,983 s**
CPU, z czego przyrost liczby testów odpowiada za **16,357 s**, a **131,626 s** to
podrożenie pojedynczego testu. Ta pozycja pyta, które moduły to robią. **Mierzy
i rozbija**; nie przyspiesza niczego i nie rusza progu.

Te same **570 artefaktów** `czas-zestawu`, co w 6.D332.

---

## 1. Kontrola przyrządu NIE PRZECHODZI — bo żąda liczby, której w danych nie ma

Pole żądało, żeby suma przyrostów po modułach zgodziła się ze 147,983 s w granicy
1 s. Nie zgadza się:

```
   suma przyrostow po modulach: 117.072 s   [6.D332: 147,983 s]   roznica -30.911 s
```

Przyczynę zmierzyłem, zamiast ją założyć. Sprawdziłem, do czego **sumuje się** pole
`moduly[].sekundy` w każdym artefakcie:

```
dzien          suma_mod     wall_s      cpu_s  mod/wall  mod/cpu
2026-09-14      133.255    133.272    209.425     1.000     0.636
2026-09-20      253.392    253.407    357.408     1.000     0.709
```

**Suma czasów modułów równa się `wall_s` co do trzeciego miejsca — na obu dniach,
ilorazem 1,000.** Do `cpu_s` nie sumuje się nigdy, a iloraz wobec niego **sam się
zmienia** (0,636 → 0,709), czyli nie jest nawet stałym przelicznikiem.

**Per-modułowego czasu CPU w tym artefakcie nie ma.** Pole prosiło o rozbicie
liczby CPU na moduły, a dane niosą wyłącznie rozbicie **ściany**. Warunek kontroli
jest więc niespełnialny — nie przez usterkę czytnika, tylko przez to, czego
artefakt nie zapisuje.

**Odpowiadam na ścianie i mówię to wprost**, zamiast przemnażać ścianę przez iloraz:
przelicznik nie jest stały (0,636 → 0,709), więc przemnożenie dałoby liczbę, która
nie opisuje żadnego modułu.

Odniesienie dla ściany, policzone tą samą metodą co 6.D332:

```
   mediana sciany:  133.272 -> 253.407 s   (+120.135)
   suma przyrostow po modulach:             +117.072
```

Różnica **3,06 s** bierze się z tego, że mediana sumy nie jest sumą median —
i to jest cała reszta, bez żadnego modułu, który by umykał.

## 2. Dwie liczby, których żądało pole

```
modulow w dniu progu: 126   dzis: 139   doszlo: 13   znikelo: 0

   istnial    modulow=126  przyrost=  74.418 s  (64 % sumy)
   doszedl    modulow=13   przyrost=  42.655 s  (36 % sumy)
   zniknal    modulow=0    przyrost=   0.000 s
```

**Moduły istniejące w dniu progu wnoszą 74,418 s, dopisane później — 42,655 s.**
Przewidywanie S2 („dopisane wnoszą mniej niż połowę") trafione, ale różnica jest
mniejsza, niż zakładałem: dopisane trzynaście modułów to ponad **jedna trzecia**
całego przyrostu.

**Nie zniknął ani jeden moduł.** Klasę „zniknął" spisałem przed pomiarem i podaję
jej zero, zamiast ją przemilczeć.

## 3. Dziesięć modułów o największym przyroście

```
   modul                                            przed        po     delta  klasa
   test_dotnet_version.py                          36.203    53.674    17.471  istnial
   test_commit_claims.py                            0.000    13.710    13.710  doszedl
   test_field_paths.py                             12.563    26.035    13.472  istnial
   test_doctor_queue_claim.py                      12.450    24.131    11.681  istnial
   test_message_claims.py                           0.000    10.835    10.835  doszedl
   test_backlog.py                                  6.460    13.428     6.968  istnial
   test_doctor_test_log.py                          0.000     6.093     6.093  doszedl
   test_csharp_type_callers.py                      0.000     5.472     5.472  doszedl
   test_report_claims.py                            1.570     5.821     4.251  istnial
   test_one_bold_sentences.py                       0.000     3.945     3.945  doszedl
```

**Dziesiątka wnosi 93,896 s ze 117,072 s, czyli 80 %.** Przewidywanie S4
(„więcej niż połowa") trafione z dużym zapasem.

**Sześć z dziesięciu to czytniki prozy albo historii gita** — `test_commit_claims`,
`test_message_claims`, `test_field_paths`, `test_report_claims`, `test_backlog`,
`test_one_bold_sentences`. Przewidywanie S6 trafione, i to jest właściwa odpowiedź
na pytanie 6.D332 §2.1 „co podrożało": **korpus, po którym te czytniki chodzą,
rośnie szybciej niż zestaw, bo rosną go same raporty i bloki kolejki.**

**Pięć z dziesiątki to moduły, których w dniu progu NIE BYŁO**, i wnoszą 40,054 s.
Cztery z tych pięciu czytają prozę. Zestaw nie tyle zwolnił, ile **dostał nowe
bramki prozy**.

## 4. GŁÓWNE ZNALEZISKO: najdroższy moduł JEST tym, który podrożał najbardziej

```
   najdrozszy DZIS:            test_dotnet_version.py   53.674 s
   najwiekszy PRZYROST:        test_dotnet_version.py   17.471 s
   TO SAMO: True
```

Pole ostrzegało, żeby nie zakładać, że moduł o największym czasie podrożał
najbardziej — „moduł może być drogi od początku i nie drgnąć, a podrożeć może tani".
**Zmierzone: to jednak ten sam moduł.** Przewidywanie S3 obalone, a warunek obalenia
spisałem przed pomiarem i wypełniam go: **podrożenie idzie tu za poziomem**, a nie
przeciw niemu, i idzie o **17,471 s z 117,072**, czyli o 15 % całego przyrostu
w jednym module.

`test_dotnet_version.py` był najdroższy już w dniu progu (36,203 s przy medianie
całości 133,272 s, czyli 27 % zestawu) i dziś jest najdroższy (53,674 s przy
253,407 s, czyli 21 %). **Jego udział spadł, a bezwzględny przyrost jest
największy** — obie rzeczy naraz, i dlatego podaję obie.

## 5. Żaden moduł nie staniał

```
   razem: 9 modulow, -0.027 s
   najwiekszy spadek: test_detail_layout.py  -0.000 s
```

Dziewięć modułów ma przyrost ujemny, ale największy z nich wynosi **cztery
tysięczne sekundy**. Przewidywanie S5 („co najmniej jeden ma przyrost ujemny")
trafione co do litery i **puste co do treści**: żaden moduł nie staniał, a dziewięć
wartości ujemnych to szum pomiaru. Mówię to zamiast zaliczyć S5 jako trafione
i przejść dalej.

## 6. Przewidywania — cztery trafione, jedno obalone, jedno puste

| # | przewidywanie | wynik |
|---|---|---|
| S1 | kontrola przejdzie w granicy 1 s | **OBALONE**: niespełnialna, bo per-modułowego CPU nie ma (§1) |
| S2 | dopisane wnoszą mniej niż połowę | **trafione**: 36 % |
| S3 | najdroższy NIE jest tym, który podrożał najbardziej | **OBALONE**: jest (§4) |
| S4 | dziesiątka wnosi więcej niż połowę | **trafione**: 80 % |
| S5 | co najmniej jeden moduł z przyrostem ujemnym | **trafione co do litery, puste co do treści** (§5) |
| S6 | w dziesiątce czytnik prozy albo historii gita | **trafione**: sześć z dziesięciu (§3) |

## 7. Czego świadomie nie zrobiłem

Nie przyspieszałem żadnego modułu, nie ruszyłem `SUITE_CPU_BUDGET_S` ani żadnej
podłogi, nie zmieniłem workflowa, nie tknąłem `src/` ani `data/` — wszystko to stoi
w polu „Poza zakresem".

**Nie przemnożyłem ściany przez iloraz CPU/ściana**, żeby dać liczbę wyglądającą
jak odpowiedź na pytanie postawione w CPU. Iloraz zmienił się między tymi dwoma
dniami z 1,571 na 1,410 (spadek, zgodnie z 6.D332 §3.1), więc przemnożona liczba
opisywałaby przelicznik, a nie moduł.

**Nie zaproponowałem, żeby artefakt zapisywał CPU per moduł.** Byłaby to zmiana
narzędzia pomiarowego i decyzja właściciela; §1 podaje, czego brakuje, żeby dało się
o to zapytać.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

`test_doctor_queue_claim.py` i `test_doctor_test_log.py` mają razem **17,774 s**
przyrostu, a obydwa uruchamiają `doctor.sh` w podprocesie. Są jedynymi modułami
w pierwszej dziesiątce, które nie czytają ani prozy, ani drzewa — kosztują tyle, ile
kosztuje uruchomienie cudzego skryptu. Nie jest to usterka; zapisuję, bo przy
rozbiciu po module wychodzi jako osobna rodzina obok czytników prozy.
