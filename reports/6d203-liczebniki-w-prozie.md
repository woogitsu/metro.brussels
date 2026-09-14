# 6.D203 — bramka prozy czyta cyfry, a liczby bywają słowne

**14.09.2026**, na `a2ef9e0`, gałąź `claude/6d203-liczby-slowne`. Wejście:
`tools/tests/test_prose_counts.py`, `test_assertion_gate.py`, `test_tree_walks.py`,
`reports/6d191-nie-ta-zmienna.md`.

## 1. Odpowiedź, w jednym zdaniu

**Skanu liczebników postawić się NIE DA** — na prozie tego drzewa daje 1216 trafień
przy 4 prawdziwych deklaracjach — ale sam skan **nie poszedł do kosza**: użyty jako
przyrząd TRIAŻU zwęził 1216 zdań do 23 do przeczytania ręką i znalazł wśród nich
deklarację, której nie pilnowało w drzewie **nic**.

## 2. Dwie liczby, których żądało pole „Wyjście"

Zmierzone na prozie **21 modułów** niosących zapadkę z `test_tree_walks.ZAPADKI`.
Proza znaczy komentarze i napisy dokumentacyjne, odsiane przez `tokenize`, a nie przez
wyrażenie regularne po nawiasach — przyrząd liczący własnym rozbiorem mówiłby o sobie
(rodzina 6.D27).

| miara | wynik |
|---|---|
| liczb słownych w prozie tych modułów | **1216** |
| z tego w promieniu 2 wierszy od definicji zapadki | **23** |
| w promieniu 12 wierszy | **93** |
| z tych 93 równych WARTOŚCI sąsiedniej zapadki | **9** |
| …a z tych 9 będących DEKLARACJAMI tej zapadki | **2** |
| z 1216 równych wartości JAKIEJKOLWIEK zapadki | **1192**, czyli **98 %** |

Ostatni wiersz jest tym, który rozstrzyga. Wartościami zapadek są między innymi
1, 2, 3, 4 i 5, więc sito „liczba słowna równa wartości zapadki" zgłasza **prawie całą
prozę tego drzewa**. Bramka świecąca na poprawnym tekście zostaje wyłączona, a nie
poprawiona — to jest lekcja `RODZINA_UBEZPIECZENIA`, przywołana w polu „Skąd" tej
pozycji, i tu kończy się dokładnie tak samo.

**Werdykt nie zależy od promienia**, i to też jest zmierzone, a nie przyjęte:

```
promień  2 wiersze   trafień  23   równych wartości sąsiada  4
promień  4 wiersze   trafień  38   równych wartości sąsiada  6
promień  8 wierszy   trafień  65   równych wartości sąsiada  6
promień 12 wierszy   trafień  93   równych wartości sąsiada  9
promień 20 wierszy   trafień 143   równych wartości sąsiada 13
promień 40 wierszy   trafień 227   równych wartości sąsiada 17
```

Prawdziwych deklaracji jest **4** w całym drzewie przy każdym z tych promieni.

## 3. Przesłanka pozycji okazała się PRAWDZIWA TYLKO POŁOWICZNIE — i to jest pomiar

Pole „Dlaczego to nie jest przeoczenie jednego człowieka" mówiło: *„nic nie broni przed
napisaniem następnej liczby słownie"*. Dla **zdań, które bramka parsuje**, jest to
nieprawda, i sprawdziłem to wykonaniem, a nie lekturą:

```
=== BAZA ===                                                     3/3 przeszło
=== KN-A: suma zapadek napisana SŁOWNIE ===
#: czterdzieści pięć zapadek: **17 przybitych, 3 częściowe, …**
  FAIL test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem:
       zdanie o rejestrze zapadek nie zostało znalezione (trafień: 0)
                                                                 2/3 przeszło
=== KN-B: liczba modułów SŁOWNIE ===
  FAIL test_zdanie_o_liczbie_modulow_zgadza_sie_z_katalogiem:
       zdanie o liczbie modułów nie zostało znalezione (trafień: 0)
                                                                 2/3 przeszło
```

Zapis słowny **nie jest przez tę bramkę przepuszczany, tylko niewidziany** — a dolne
ostrze na czytnik („trafień: 0") zamienia niewidzenie w czerwień. Mówi to wprost
docstring `test_czytnik_nie_widzi_deklaracji_zapisanej_slownie…`, który stoi w module
od 12.09.2026; pozycja 6.D203 tego nie zauważyła.

**Luka jest więc węższa, niż opisywała pozycja, i leży gdzie indziej:** nie w tym, że
bramka przepuszcza słowa, tylko w tym, że **parsuje 2 deklaracje przy 46 zapadkach**.
Reszty prozy nie pilnuje nic — i po pomiarze z §2 wiadomo, że skanem pilnować się
jej nie da.

## 4. Co ten skan znalazł, zanim został odrzucony jako bramka

Dwadzieścia trzy zdania z promienia 2 (plus dziewięć z promienia 12) przeczytane ręką
dały **cztery** deklaracje słowne w całym drzewie:

| miejsce | zdanie | los |
|---|---|---|
| `test_platform_length_in_pipeline.py:55` | „04.09.2026 wywołań są dwa" | **datowane** — opisuje dzień pomiaru, zestarzeć się nie może |
| `test_game_needle_specificity.py:131` | „Zmierzone 07.09.2026: cztery" | **datowane**, jak wyżej |
| `test_backlog.py:68` | „dwanaście pozycji to dolna granica doby pracy" | **żywe**, ale jest echem progu z `CLAUDE.md` §8, który `test_backlog.prog_z_dokumentu` czyta — też ze słowa — i porównuje z `MINIMUM_READY_ITEMS` |
| `test_runner_number_parsing.py:75` | „Trzy pomocniki, ktore maja byc JEDYNA droga wartosci opcji do liczby" | **żywe i niepilnowane przez NIC** |

Ostatnie jest znaleziskiem tej pozycji. `POMOCNIKI` to krotka trzech nazw, a
`len(POMOCNIKI)` **nie było przybite w drzewie nigdzie** — sprawdzone `grep`em: dwa
wystąpienia nazwy w całym `tools/tests/`, definicja i pętla. Czwarty pomocnik dopisany
do krotki zostawiłby zdanie nad nią nieprawdziwym i nikt by się o tym nie dowiedział.

## 5. Co weszło zamiast skanu

**Trzeci WZORZEC**, nie sito po słowach. Bramka umie teraz przeczytać deklarację
zapisaną słownie — w miejscu, o którym wie, że jest deklaracją — i porównać ją
z krotką. Mapa liczebników jest wołana wyłącznie przez wzorce zadeklarowane w module;
puszczona po prozie dałaby te 1216 trafień z §2.

Do tego dwie rzeczy, których pozycja nie żądała, a bez których nowy wzorzec starzałby
się tak samo jak proza, której pilnuje:

- **`DEKLARACJI_POD_BRAMKA = 3`** — zapadka w jedną stronę. Deklaracja raz objęta
  czytaniem nie ma prawa z niego wypaść, bo wypadnięcie jest **bezgłośne**: zdanie
  zostaje w pliku i wygląda tak samo jak przedtem. Druga asercja tego testu żąda, żeby
  liczba czytanych deklaracji była MNIEJSZA od liczby zapadek — czyli żeby zdanie
  o małym pokryciu przestało być prawdziwe głośno, a nie po cichu.
- **`DEKLARACJE_SLOWNE`** — cztery zdania z §4 wypisane **z nazwy**, nie policzone
  (6.D131: zbiór przeżywa edycję prozy, liczba nie), z testem, że każde nadal stoi
  w drzewie. Wpis opisujący nieistniejący tekst byłby zdaniem o przeszłości udającym
  zdanie o dziś.

**Odmiana w mapie liczebników nie jest ozdobą** i jest to zmierzone: mapa z 23 kluczami
(same mianowniki) daje 774 trafienia, mapa z 92 — 1216. Wąska zaniżyłaby liczbę, na
której stoi werdykt, o **36 %**.

## 6. Kontrole negatywne — pięć, każda WYKONANA, `md5sum -c: OK` po każdej

Baza `test_prose_counts.py` **7/7**.

| kontrola | co podmieniono | wynik |
|---|---|---|
| KN-1 | czwarty pomocnik dopisany do `POMOCNIKI` | 1 czerwony — „proza mówi o 3 pomocnikach (`trzy`), a krotka ma 4" |
| KN-2 | zdanie o pomocnikach przeredagowane | **2 czerwone** — dolne ostrze czytnika ORAZ lista `DEKLARACJE_SLOWNE` |
| KN-3 | wzorzec zdjęty z listy czytanych | 1 czerwony — `DEKLARACJI_POD_BRAMKA` |
| KN-4 | skan oślepiony (mapa bez odmiany, 4 klucze) | 1 czerwony — 394 trafienia przy ostrzu 900 |
| KN-5 | zdanie z `DEKLARACJE_SLOWNE` znika z modułu | 1 czerwony |

KN-4 jest tą, dla której dolne ostrze w ogóle istnieje: przyrząd, który nie widzi nic,
„udowodniłby" brak fałszywych trafień zerem.

## 7. Zapadki podniesione w tym samym commicie

| zapadka | było → jest | powód |
|---|---|---|
| `ZAPADEK_RAZEM` | **46** (było 45) | `MINIMUM_LICZB_SLOWNYCH` |
| `MIN_REPORTS` | **330** (było 329) | ten raport |

Kolejność „jest (było)", a nie „było → jest", jest tu **wymuszona przez bramkę**
i warto to zapisać: `test_report_claims` czyta PIERWSZĄ liczbę po nazwie stałej
i porównuje ją z kodem, więc zapis „329 → 330" mówi bramce, że raport twierdzi
329 przy 330 w kodzie. Zapaliła się na tym wierszu — słusznie.
| rozkład klas | 17/3/24/1 → 17/3/**25**/1 | jw., klasa WOLNA — próg jednostronny |
| zdanie o rejestrze w prozie | „45 zapadek… 24 WOLNE" → „46… 25 WOLNE" | **sprawdza je ta sama bramka, którą ta pozycja rozbudowuje** |

Ostatni wiersz jest tu najprzyjemniejszy: pozycja o prozie przy zapadkach musiała
przy okazji poprawić prozę przy zapadce, a zapaliła ją własna bramka.

## 7a. Populacja pomiaru NIE OBEJMUJE tego modułu — i to jest wybór

`MINIMUM_LICZB_SLOWNYCH` sprawiła, że `test_prose_counts.py` sam wpadł do rejestru
zapadek, czyli do populacji, którą mierzy. Bez wyłączenia liczba z §2 staje się
**samozwrotna**: każde słowo dopisane do prozy tego pliku ją zmienia, a proza tego
pliku opisuje właśnie ją. Zmierzone: z tym plikiem 1244 trafienia, bez niego 1216.
Liczba, którą da się zmienić zdaniem o niej samej, nie jest pomiarem drzewa.

**Znalazłem to dopiero po wciągnięciu `main`** — pierwszy pomiar dał 1206 na 21
modułach, a po zarejestrowaniu zapadki i scaleniu MB-08 (które dopisało do prozy
kilkunastu modułów własne komentarze z liczebnikami) ten sam skan dawał 1244 na 22.
Obie liczby były prawdziwe dla swojego drzewa i obie byłyby nieprawdziwe w commicie —
dlatego wszystkie liczby w §2 są przeliczone na drzewie, które idzie do przeglądu,
a nie na tym, na którym zaczynałem.

## 8. Czego świadomie NIE zrobiłem

- **Nie postawiłem skanu liczebników jako bramki.** Powód jest liczbą z §2, nie
  ostrożnością.
- **Nie ruszyłem prozy w cudzych modułach** — pole „Poza zakresem" zabrania tego
  wprost. Trzeci wzorzec czyta zdanie `test_runner_number_parsing.py` **takie, jakie
  jest**; gdyby wymagał przepisania go na cyfry, ta pozycja wyszłaby poza swój zakres.
- **Nie ruszyłem `ZDAN_RODZINY_RAZEM` ani `ZDAN_BEZ_POKRYCIA`** — również zakazane
  polem „Poza zakresem".
- **Nie rozszerzyłem bramki na dokumenty w `docs/`** — jw. Zaznaczam jednak, że
  `test_backlog.prog_z_dokumentu` już tam czyta liczebnik słowny („dwunastu pozycji
  DO WZIĘCIA") i porównuje go z `MINIMUM_READY_ITEMS`, więc mechanizm z §5 istnieje
  w drzewie w dwóch miejscach niezależnie od siebie.

## 9. Co zauważyłem po drodze, a nie tknąłem

- **Pokrycie tej bramki to 3 deklaracje na 46 zapadek** i nie da się go podnieść
  inaczej niż po jednej. Czy warto — jest pytaniem do kolejki, nie do tej pozycji:
  większość zapadek nie ma przy sobie ani jednego zdania liczbowego, więc wzorzec
  nie miałby czego czytać.
- **Najczęstsze liczebniki w prozie tego drzewa** to „dwa" (148), „jeden" (134),
  „trzy" (112) i „dwie" (98) — czyli dokładnie te, które są też najczęstszymi
  wartościami zapadek. Sito po wartości jest z tego powodu bezużyteczne
  **strukturalnie**, a nie przez dzisiejszy stan drzewa.
