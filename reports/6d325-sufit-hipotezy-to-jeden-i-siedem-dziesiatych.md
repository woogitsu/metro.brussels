# 6.D325 · Hipoteza 6.D314 może dotyczyć NAJWYŻEJ 1,7 % zdań — a czterdzieści siedem raportów powstało, zanim bramka istniała

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `52d8baa`

6.D314 §7 i §9 zmierzyło, że w prozie `reports/` stoi 3810 zdań z liczebnikiem
słownym, z czego 2370 twierdzi coś o mierzalnej wielkości — i postawiło hipotezę,
że proza pisze liczby słownie, bo `CLAUDE.md` podaje to jako lekarstwo na `CLAIM`.
Tamta pozycja **zapisała wprost, że to hipoteza wyprowadzona z dokumentu, a nie
pomiar**. Ta pozycja daje jej pomiar. **LICZY i niczego nie przepisuje.**

Trzy liczby: **06.09.2026 · 383 · 73**. Data wprowadzenia `CLAIM`; zdań w raportach
**starszych** od niej; zdań w młodszych, które **cyfrą naprawdę zapaliłyby wzorzec**.

Wynik, dla którego warto było tę pozycję wziąć: **hipoteza może dotyczyć najwyżej
73 zdań z 4210, czyli 1,7 %.** Pozostałe 98,3 % nie zapaliłoby `CLAIM` nawet
zapisane cyfrą — więc obchodzić go nie mogą.

---

## 1. Data wprowadzenia wzorca — jeden commit, bez niejednoznaczności

```
$ git log -S 'CLAIM = re.compile' -- tools/tests/test_report_claims.py
436a4ea 2026-09-06 6.D4: raport podający wartość stałej podaje tę z kodu — i tylko to
```

**Jeden commit, `436a4ea`, 06.09.2026.** Spisałem przed pomiarem, że podam dwie daty
— wprowadzenia i ostatniej zmiany — bo wzorzec był zwężany przy 6.D27. Okazało się
to niepotrzebne: `git log -S` po kształcie wzorca zwraca **jeden** commit, więc data
wprowadzenia jest jednoznaczna i to ona rozstrzyga.

## 2. Kontrola przyrządu — ZDANA

Pole żąda, żeby `reports/6d296-krzywa-ile-ginie-przy-n-wierszach.md` wyszedł jako
**młodszy** od daty wprowadzenia wzorca.

```
   6d296-krzywa-ile-ginie-przy-n-wierszach.md -> data 2026-09-20, klasa MLODSZY
```

Data czytana `data_raportu` **pożyczonym** z `test_report_claims.py`, czyli tym samym
czytnikiem, którego używa bramka — nie własnym.

## 3. POPULACJI 2370 NIE ODTWARZAM i mówię, czego nie liczę

```
zdan z liczebnikiem SLOWNYM twierdzacych o mierzalnej wielkosci: 4593   [6.D314: 2370]
```

**Moja populacja jest prawie dwukrotnie większa: 4593 wobec 2370, stosunek 1,94.**
Różnicy **nie uzgadniam** — byłoby to dobieranie definicji pod cudzą liczbę (lekcja
7; ten sam ruch co przy 6.D317, 6.D318, 6.D319, 6.D321 i 6.D323).

Czego nie liczę tak samo jak tamta pozycja: mój dzielnik zdań tnie po `.!?` i po
pustym wierszu, a **tabel markdown nie tnie wcale** — cała tabela wchodzi jako jedno
„zdanie". Moje sito „mierzalnej wielkości" bierze rzeczowniki miary i nazwy
w grawisach, a 6.D314 nie podaje swojego. Wszystkie liczby klas podaję **na swojej
populacji** i przy każdej to zaznaczam.

## 4. CZTERDZIEŚCI SIEDEM RAPORTÓW POWSTAŁO, ZANIM BRAMKA ISTNIAŁA

```
raportow z populacji: 448 | STARSZYCH od wzorca: 47 | mlodszych: 401
ZDAN w raportach starszych: 383 | w mlodszych: 4210
```

**Trzysta osiemdziesiąt trzy zdania stoją w raportach tkniętych ostatnio przed
06.09.2026** — czyli zanim `CLAIM` w ogóle wszedł do drzewa. **Te zdania nie mogły
obchodzić bramki, której nie było**, i to jest rozstrzygnięcie o nich, a nie
przypuszczenie.

Klasa jest jednorodna co do rodzaju: czterdzieści siedem to raporty z pierwszej fazy
projektu (`T-*`, `R-*`, `L1_A-*`, `M7-*`, `mutation-triage-*`), najstarszy
`branch-audit.md` z 02.09.2026, najmłodsze z 05.09.2026.

**Pole dopuszczało odpowiedź „żadnego" i mówiło, co by wtedy znaczyła:** cała
populacja powstałaby po bramce i hipoteza 6.D314 dostałaby warunek konieczny.
**Nie jest „żadnego", więc tego warunku hipoteza NIE DOSTAJE w czystej postaci** —
dostaje go dopiero po odjęciu tych 383 zdań, i dlatego dalsze liczby liczę na
populacji młodszej.

## 5. LICZBA ROZSTRZYGAJĄCA: 73 z 4210, czyli 1,7 %

Sprawdzam **mechanicznie**, a nie z kształtu zdania: podmieniam liczebnik słowny na
cyfrę i puszczam na przerobionym zdaniu prawdziwy `CLAIM` — ten sam obiekt, którego
używa bramka.

```
=== ZDANIA MLODSZE: czy CYFRA zapalilaby CLAIM ===
   ZAPALILABY:       114
   nie zapalilaby:   4096
```

**Sto czternaście z czterech tysięcy stu dziewięćdziesięciu pięciu — 2,7 %.**
Ale przeczytałem te 114 zamiast podać samą liczbę, i połowa z nich nie jest prozą:

```
   z tego WIERSZE TABEL (>=4 kreski):  41  (36 %)
   PROZA ciagla:                        73
```

Czterdzieści jeden trafień to **wiersze tabel** (`| KN-1 | … |`), które wchodzą do
mojej populacji przez usterkę dzielnika zdań opisaną w §3. **Prawdziwej prozy jest
73, w 56 plikach — czyli 1,7 % populacji młodszej.**

**To jest odpowiedź tej pozycji: hipoteza 6.D314 może dotyczyć najwyżej
siedemdziesięciu trzech zdań.** Pozostałe 4137 zdań młodsze nie zapaliłyby `CLAIM`
nawet zapisane cyfrą — nie mają nazwy w grawisach w wymaganym układzie, nie mają
liczby w zasięgu czterdziestu znaków albo rozdziela je przecinek, którego wzorzec
nie przepuszcza.

**Czego to NIE dowodzi, i mówię to wprost, bo pole ostrzega:** nawet dla tych 73
zdań intencja jest nieobserwowalna. Polszczyzna pisze liczebniki słownie na początku
zdania i w prozie ciągłej niezależnie od jakiejkolwiek bramki. **Liczba 73 jest
sufitem hipotezy, a nie jej potwierdzeniem** — i sufit ten jest o dwa rzędy wielkości
niższy niż populacja, z której hipoteza wyrosła.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| W1 | kontrola przyrządu przejdzie | trafione |
| W2 | populacji 2370 nie odtworzę co do jedynki | trafione — 4593 |
| W3 | raportów starszych od wzorca będzie niezero | trafione — 47 |
| W4 | z młodszych mniej niż połowa ma kształt zapalający | trafione, i to **z ogromnym zapasem** — 2,7 %, a po odsianiu tabel 1,7 % |
| W5 | data wprowadzenia będzie wcześniejsza niż zwężenie 6.D27 | **NIEROZSTRZYGALNE PRZYRZĄDEM** — `git log -S` po kształcie wzorca zwraca jeden commit, więc „data wprowadzenia" i „data ostatniej zmiany kształtu" są tą samą datą; pytania nie da się postawić na tym czytniku |
| W6 | podmiana liczebnika na cyfrę okaże się niejednoznaczna dla części zdań | trafione — **191 wystąpień liczebnika złożonego** w `reports/` |

**W6 jest przewidywaniem o moim własnym przyrządzie i trafiło.** Podmieniam każde
słowo-liczebnik na `7`, więc `dwadzieścia cztery` staje się `7 7`, a nie `24`.
Wystąpień takich par jest **191**. Nie poprawiam tego i mówię dlaczego: podmiana
służy wyłącznie sprawdzeniu, **czy w zdaniu jest cyfra w zasięgu nazwy** — a `7 7`
daje cyfrę tak samo jak `24`. Gdyby wzorzec pytał o wartość, poprawka byłaby
konieczna; pyta o kształt, więc nie jest.

**W5 zapisuję jako nierozstrzygalne przyrządem, a nie jako trafione albo pudło.**
Postawiłem je, zakładając, że wzorzec ma osobną datę wprowadzenia i osobną datę
zwężenia. `git log -S` pokazuje jeden commit, bo zwężenie 6.D27 zmieniło wnętrze
wyrażenia, nie jego pierwsze wystąpienie w pliku. Rozstrzygnięcie wymagałoby innego
czytnika i tej pozycji nie dotyczy.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono `CLAIM` ani `CLAUDE.md`** — pole zabrania obu, a §5 pokazuje,
  że rozstrzygnięcie o lekarstwie z konstytucji wymaga liczby, którą ta pozycja
  dopiero daje.
- **Nie przepisano ani jednego zdania** i nie zamieniono żadnego liczebnika na cyfrę
  w drzewie — podmiana żyje wyłącznie w pamięci przyrządu.
- **Nie postawiono bramki na liczebnikach.**
- **Nie uzgodniono populacji 4593 z 2370** (§3).
- **Nie rozstrzygnięto intencji** dla żadnego z 73 zdań — jest nieobserwowalna (§5).
- **Nie poprawiono dzielnika zdań**, mimo że wciąga tabele; zamiast tego policzyłem,
  ile trafień z niego pochodzi (41 ze 114).
- **Nie tknięto `src/` ani `data/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Czterdzieści jeden ze stu czternastu trafień to wiersze tabel markdown.**
   Każdy pomiar „zdań prozy" w tym repozytorium, który tnie po `.!?`, liczy tabelę
   jako jedno zdanie — a tabele są tu główną formą podawania liczb.
2. **Czterdzieści siedem raportów pierwszej fazy nie było tknięte od 05.09.2026.**
   Jest to jedyna klasa w `reports/`, o której da się powiedzieć, że żadna dzisiejsza
   bramka nie mogła wpłynąć na jej kształt — i przez to jedyna próbka kontrolna,
   jaką ten korpus ma.
3. **Zdania zapalające `CLAIM` cyfrą stoją w 56 plikach z 400**, czyli w co siódmym.
   Rozkład jest więc rozproszony, a nie skupiony w kilku raportach — czego hipoteza
   „pisano słownie, żeby obejść" nie przewidywała w żadną stronę.
