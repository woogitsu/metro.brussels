# 6.D322 · Dziesięć rozjazdów, ZERO nieprawd — a moje sito potrzebowało TRZYNASTU kształtów, żeby odróżnić liczbę od odsyłacza

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `9fa7acc`

6.D311 §1 i §9 zapisało, że nieprawda z 6.D302 żyła w pięciu miejscach, a korekta
z PR #713 poprawiła raport i wiersze tabeli, **bloków sześciopolowych nie dosięgając**.
Ta pozycja liczy, ile bloków cytuje liczbę, której dziś w cytowanym raporcie nie ma.
**LICZY i niczego nie prostuje.**

Trzy liczby: **109 / 104 / 10**. Ale wynik, dla którego warto było tę pozycję wziąć,
jest inny: **wszystkie dziesięć rozjazdów jest datowanych, ani jeden nie jest
nieprawdą — a surowych rozjazdów było siedemnaście i siedem z nich zrobiło moje
własne sito**, które musiało dojść od czterech kształtów do trzynastu.

---

## 1. TRZY LICZBY, których żądało pole

```
blokow szesciopolowych:                  394
z ODSYLACZEM do konkretnego raportu:     109
   z nich podajacych LICZBE:             104
ROZJAZDOW (liczba nie stoi w raporcie):   10
   blokow z rozjazdem:                     7
   z tego DATOWANYCH:                      7
```

**Odsyłacz do konkretnego raportu ma 109 bloków z 394, czyli co czwarty.** Z nich
liczbę podaje **104**, czyli 95 % — blok, który już odsyła do raportu, prawie zawsze
przytacza przy tym liczbę.

## 2. Kontrola przyrządu — ZDANA co do obu żądanych warunków

Pole żąda, żeby blok **6.D311** wyszedł jako cytujący `reports/6d302-scalenie-i-jego-galaz.md`
i **nie** wyszedł jako rozjazd.

```
=== KONTROLA PRZYRZADU: blok 6.D311 ===
   cytuje: ['reports/6d302-scalenie-i-jego-galaz.md']
   liczby w polu Skad: ['6', '302']
   rozjazdy 6.D311: BRAK — zgodnie z polem
```

Oba warunki spełnione — i spełnione były **w każdej z trzech wersji przyrządu**,
także w tej z siedmioma fałszywymi rozjazdami. **Kontrola żądana przez pole nie
odróżniła przyrządu poprawnego od przyrządu, który mylił się na siedmiu blokach
z siedemnastu** — ten sam kształt, który zmierzyłem dobę wcześniej przy 6.D320 §4.

## 3. SITO POTRZEBOWAŁO TRZYNASTU KSZTAŁTÓW, a spisałem cztery

Pole ostrzega przed myleniem „liczby innej" z „liczbą nieprawdziwą". Zanim doszedłem
do tego rozróżnienia, musiałem odróżnić **liczbę od odsyłacza** — i to okazało się
trudniejsze.

Spisane **przed pomiarem**, cztery kształty liczby, która jest odsyłaczem, a nie
twierdzeniem: data `DD.MM.RRRR`, numer pozycji `6.D308`, numer sekcji `§3`, numer
PR-a `#713`.

Dołożone **po przeczytaniu wyniku**, dziewięć:

| kształt | przykład | skąd się wziął |
|---|---|---|
| data ISO | `2026-09-02` | blok 6.A3 |
| numer joba | `job 105971122979` | blok 6.D313 |
| numer wiersza | `wiersz 41 i 213` | blok 6.A3 |
| wpis rejestru | `T-011` | blok 6.B16 |
| godzina | `07:06:44` | blok 6.A3 |
| identyfikator długi | `101890547517` | blok 6.D43 |
| plik z wierszem | `reports/T-311-braking.md:257` | blok 6.A31 |
| SHA commita | `a4a3975` | bloki 6.A33, 6.D34, 6.D35 |
| numer wersji | `10.0.401` | bloki 6.D169, 6.D252 |

**Plus jedna usterka, która nie była kształtem, tylko ASYMETRIĄ mojego dopasowania.**
Granicę liczby po stronie raportu napisałem jako `(?<![\d.,])`, a po stronie bloku
liczbę brałem bez tego zastrzeżenia. `401` wewnątrz `10.0.401` było więc **w bloku
liczbą, a w raporcie nie** — i rozjazd brał się z mojego wzorca, nie z treści.
Granica jest teraz symetryczna (`(?<!\d)` / `(?!\d)`).

**Ścieżka liczby rozjazdów przez trzy wersje przyrządu: 25 → 17 → 10.** Pierwsza
wersja sklejała dodatkowo cyfry z dwóch stron zamaskowanego odsyłacza, bo wzorzec
liczby dopuszczał spację w środku (`70811149` z bloku 6.D311). **Piętnaście
z dwudziestu pięciu pierwszych rozjazdów zrobił mój przyrząd, a nie drzewo.**

## 4. ODPOWIEDŹ NA PYTANIE ZADANE WPROST: WSZYSTKIE SĄ DATOWANE, ŻADEN NIE JEST NIEPRAWDĄ

Pole żąda powiedzieć, ile rozjazdów jest **datowanych**, i dopuszcza odpowiedź
„wszystkie", bo wtedy rozjazd nie jest nieprawdą. **Jest „wszystkie": 7 bloków z 7.**

Przy dziesięciu rozjazdach reguła jest droższa niż czytanie, więc przeczytałem każdy
(lekcja 6.D317). Ani jeden nie jest twierdzeniem nieprawdziwym o cytowanym raporcie —
a powody są **cztery różne** i dlatego wypisuję je osobno, zamiast podać samo zero:

| blok | liczba | w raporcie | co to naprawdę jest |
|---|---|---|---|
| 6.A33 | `68` | nie ma | **pomiar WŁASNY bloku** — „Zmierzone 07.09.2026 na `a4a3975`: 16 z 68 igieł"; raport cytowany jest za zdanie z §7, nie za tę liczbę |
| 6.D34 | `63` | nie ma | **pomiar własny**, wynik `grep` wklejony w bloku: „razem Game.Tests: 63 w 7 plikach" |
| 6.D264 | `20` | nie ma | **parametr KODU**, nie raportu: okno `±20` wierszy bramki 6.D259 |
| 6.D268 | `20` | nie ma | jw. |
| 6.D263 | `06`, `055`, `07` | nie ma | **napisy w grawisach**, które blok cytuje jako przykłady fragmentów wyciętych z `6.D136` i z numerów pozycji — blok mówi o nich wprost, że „czytnik wziął je za liczby" |
| 6.D313 | `2664` | nie ma | **cytat ZAPRZECZONY**: blok pisze „`reports/6d304-…md` **nie dotyczy** — pomiar stoi w komunikacie tej pozycji" |
| 6.D318 | `70` | nie ma | **liczba WYPROWADZONA**: raport podaje 102 i 32, a 70 jest ich różnicą, której nie zapisuje |

**Najciekawszy jest 6.D313 i dlatego stoi tu z cytatem.** Ścieżka raportu pada w polu
„Skąd" **po to, żeby powiedzieć, że ten raport nie dotyczy**. Każdy skan liczący
odsyłacze — mój też — czyta obecność ścieżki, a nie jej zaprzeczenie. Jest to klasa,
której pole nie przewidziało: **cytat negatywny liczy się jako cytat**.

**Zaraz za nim 6.D318, bo to MÓJ WŁASNY blok z wczoraj.** Liczba `70` jest prawdziwa
i wyprowadzona z dwóch liczb, które raport podaje — ale w raporcie nie stoi, więc
każda bramka wiążąca blok z raportem zgłosiłaby ją jako rozjazd. **Pomiar trafił we
własny ogon i mówię to, zamiast wyłączyć własny przypadek.**

## 5. DRUGI ODCZYT — liczebniki słowne dają PIĘĆ rozjazdów i WSZYSTKIE są artefaktem

6.D314 zmierzyło, że w prozie tego projektu stoi 3810 zdań z liczebnikiem słownym,
a skan po cyfrach ich nie widzi. Policzyłem więc drugi raz, mapą słowo → liczba:

```
  6.D186   dziesięć       = 10    reports/6d181-dziewiecdziesiat-nazw-w-umowie.md
  6.D302   sto            = 100   reports/6d293-sto-trzynascie-bez-raportu.md
  6.D302   trzynascie     = 13    reports/6d293-sto-trzynascie-bez-raportu.md
  6.D308   trzydzieści    = 30    reports/6d299-siedem-w-liczbie-mnogiej.md
  6.D329   pięćdziesięciu = 50    reports/6d320-jednostka-w-nazwie-konwencja-bez-bramki.md
```

**Wszystkie pięć to LICZEBNIKI ZŁOŻONE, których mapa słowo → liczba złożyć nie umie.**
`6.D302` cytuje raport, który ma **sto trzynaście w samej nazwie pliku**, a moja mapa
rozbija to na `sto` = 100 i `trzynaście` = 13 i szuka ich osobno. `6.D329` mówi
„pięćdziesięciu dziewięciu", czyli 59 — liczby, którą cytowany raport podaje wprost.

**Drugi odczyt dodaje ZERO prawdziwych rozjazdów i pięć fałszywych.** Podaję go mimo
to, bo pytanie „czy skan po cyfrach coś gubi" ma tu odpowiedź zmierzoną, a nie
założoną — i jest nią „nie gubi, a odczyt słowny bez składania liczebników szkodzi".

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| T1 | kontrola przyrządu przejdzie za pierwszym razem | trafione — ale **jałowo**, §2 |
| T2 | bloków z odsyłaczem będzie większość populacji | **OBALONE** — 109 z 394, czyli 28 % |
| T3 | z nich liczbę poda ponad połowa | trafione — 95 % |
| T4 | rozjazdów mniej niż 10 | **OBALONE co do litery** — dokładnie 10 |
| T5 | odpowiedź na „ile datowanych" nie brzmi „wszystkie" | **OBALONE** — brzmi „wszystkie" |
| T6 | odczyt słowny doda co najmniej jeden rozjazd, którego cyfry nie widzą | **OBALONE** — dodał zero prawdziwych i pięć fałszywych |
| T7 | moja reguła odsiewu okaże się niewyczerpująca | trafione — **dziewięć razy**, §3 |

**T4 zapisuję jako obalone co do litery, a nie jako trafione.** Postawiłem „mniej niż
10", wyszło dokładnie 10. Warunek obalenia spisałem przed pomiarem i honoruję go:
klasa została rozbita po przyczynie (§4), zamiast podać samą liczbę.

**T7 trafione po raz DZIEWIĄTY z rzędu w tej sesji** — po 6.D317, 6.D318 i 6.D320.
Różnica jest tym razem ilościowa i warta zapisania: lista spisana z góry miała cztery
pozycje, a musiała mieć trzynaście. **Nie chybiła o jeden kształt; chybiła o dwie
trzecie.**

## 7. Czego świadomie nie zrobiono

- **Nie sprostowano ani jednego bloku.** §4 pokazuje, że nie ma czego prostować:
  żadna z dziesięciu liczb nie jest nieprawdziwa.
- **Nie postawiono bramki wiążącej blok z raportem.** Pole zabrania, a §4 mówi,
  dlaczego byłaby szkodliwa: zapalałaby się na pomiarze własnym bloku, na parametrze
  kodu, na napisie w grawisach i na cytacie zaprzeczonym — czyli na czterech rzeczach,
  z których żadna nie jest usterką.
- **Nie zmieniono `CLAIM`** ani żadnego wzorca w `tools/tests/`.
- **Nie dociągano sita do zera.** Dziesięć rozjazdów zostaje w liczbie, bo każdy
  z nich jest zrozumiały po przeczytaniu, a dalsze zwężanie wzorca pod znany wynik
  byłoby dopasowywaniem przyrządu do odpowiedzi.
- **Nie tknięto `src/` ani `data/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Cytat zaprzeczony liczy się jako cytat** (6.D313). Dotyczy to każdego skanu
   po ścieżkach w tym repozytorium, nie tylko mojego — a ścieżek w prozie pilnuje
   `tools/tests/test_report_hygiene.py`.
2. **Blok 6.D318 podaje liczbę wyprowadzoną z dwóch liczb raportu.** Jest to kształt
   częsty w tej rodzinie pozycji („102 minus 32") i żadna bramka porównująca napisy
   go nie przepuści. Ile takich wyprowadzeń stoi w blokach, nie liczy nikt.
3. **Czwarta część bloków nie odsyła do żadnego raportu** (285 z 394). Czym wtedy
   jest ich pole „Skąd", ta pozycja nie pyta.
