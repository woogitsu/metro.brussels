# 6.D278 — sto trzydzieści dwa zdania są jedno zdjęcie pogrubienia od zniknięcia

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `a8894d0`

## 1. Trzy liczby

Zmierzone na dzisiejszym drzewie, czytnikiem POŻYCZONYM z `test_message_claims.py`
(`proza`, `_akapity_prozy`, `SPECYFIKATOR`, `ZAPOWIEDZ_POMIARU`, `POGRUBIONA`,
`GRANICA_ZDANIA`, `DATA`, `gole_w_prozie_pomiarowej`) — żadnego drugiego sita:

| | co | ile |
|---|---|---|
| **L1** | zdań prozy pod `tools/tests/` z DOKŁADNIE JEDNĄ liczbą pogrubioną, poza akapitem z zapowiedzią pomiaru | **132** |
| **L2** | plików, w których te zdania stoją | **42** |
| **L3** | liczb gołych stojących dziś w tych zdaniach — znikną razem ze zdaniem | **96** |

Liczby kontrolne z tego samego przebiegu: populacja `gole_w_prozie_pomiarowej`
na całym drzewie **259**, `zdan_ogloszonych_pomiarem` **462**, zdań z co najmniej
dwiema pogrubionymi poza zapowiedzią **54** (populacja słusznie odsiana),
kolizji klucza `(plik, wiersz węzła, zdanie)` **0**.

Zdań niosących choć jedną liczbę gołą jest **53** ze 132; pozostałe zabrałyby
ze sobą tylko własną pogrubioną. Sto dziewięćdziesiąt sześć gołych z dwustu
pięćdziesięciu dziewięciu to niecałe **37 %** całej populacji dolnej zapadki —
tyle stoi dziś za jednym zdjęciem gwiazdek.

**Liczby są policzone DWA RAZY, dwoma różnie zbudowanymi pętlami**, i obie dały
to samo. To nie jest ostrożność: sito zgodne samo ze sobą czyta się dokładnie tak
samo jak sito poprawne (6.D276).

## 2. Dziura, pokazana obok siebie

Mutacja na kompletnej kopii drzewa: zdaniu z listy zdjęto pogrubienie.

```
plik: tools/tests/csharp_assertions.py
przed: #: **25** asercji, i wszystkie 25 zostaja NIEROZSTRZYGNIETE.
po:    #: 25 asercji, i wszystkie 25 zostaja NIEROZSTRZYGNIETE.
```

Ten sam przebieg, dwie bramki:

```
=== NOWA BRAMKA ===
FAIL test_czytnik_widzi_przypadek_ktory_pozycje_wywolal
FAIL test_ile_zdan_jest_jedno_zdjecie_od_znikniecia: ... jest 131 przy podlodze 132 (w 41 plikach)
1/3 przeszło

=== STARA ZAPADKA GÓRNA ===
19/19 przeszło
```

Po zdjęciu gwiazdek w tym wierszu stoją DWIE liczby, których nie pilnuje już nic,
a obie zapadki widzą o jedną liczbę MNIEJ niż przed zdjęciem. Zapadka górna jest
zapadką górną, więc spadek przechodzi ją celująco — 6.D27 od strony populacji.

## 3. Koszt podłogi jest POLICZONY, a nie oszacowany

Na całej historii `tools/tests/` — **664** rewizje, każda porównana ze **swoim
pierwszym rodzicem**:

| podłoga | rewizji wprowadzających spadek | czerwonych przebiegów na `main` |
|---|---|---|
| na L1 (`>= 132`) | **2**, obie na pracy uprawnionej | **4** |
| na L3 (`>= 96`) | **1**, na pracy uprawnionej | **4** |

Cztery czerwienie to jeden ciąg z 09.09.2026 — jedno zdarzenie trzymające bramkę
czerwoną przez cztery scalenia, aż populacja odrosła. Koszt jest tego samego rzędu
co koszt, który 6.D270 policzyło i który został przyjęty.

Dwa zmierzone spadki L1: raz zdanie z nieprawdziwą liczbą skasowano przy rozwiązywaniu
konfliktu scalania (`15f5aa3`), raz prozę przepisano na wciętą listę (`ab88b4c` —
i tam `156` oraz `157` **przetrwały jako liczby gołe**, czyli wypadły z obu sit).

**Zero kosztu przy scalaniu:** ze stu dwudziestu dziewięciu scaleń w zbiorze żadne
nie ma L1 ani L3 niższego niż jego drugi rodzic. Wciągnięcie `main` do gałęzi
nigdy tu populacji nie obniżyło.

## 4. Kształt, którego bałem się najbardziej, NIE ISTNIEJE

Przed pomiarem zapisałem, że podłogi na L1 nie wolno postawić, jeśli większość
spadków bierze się z pracy poprawnej w postaci „zdaniu przybyła DRUGA pogrubiona
liczba" — bo wtedy bramka zapala się na tym, czego `MAX_POGRUBIONYCH_BEZ_POKRYCIA`
od autora żąda. Zmierzone: takich spadków w historii tego drzewa **nie ma ani
jednego**. Rozumowałem z reguły zapadki, a nie z tego, co ludzie naprawdę robili.

## 5. Pomiar kosztu omal nie wyszedł zawyżony siedmiokrotnie

Pierwsze podejście liczyło różnice między kolejnymi pozycjami `git rev-list --reverse`.
Dało **20** spadków L1-podobnych zamiast dwóch. To **artefakt porządku**: `rev-list`
przeplata gałęzie, więc „kolejna rewizja" bywa commitem z innego drzewa. Widać to
gołym okiem — cztery różne commity dają identyczny spadek, a żaden niczego z prozy
nie usunął. Zakotwiczenie na pierwszym rodzicu jest poprawne i sprawdzone: 664
rewizje mają 664 różne drzewa `tools/tests`, a drzewo każdego rodzica ma wśród nich
odpowiednik. Gdyby użyć tamtych liczb, koszt byłby zawyżony siedmiokrotnie dla L1
i dwunastokrotnie dla L3 — **i wyglądałby na porządny pomiar**.

## 6. Kontrole

**Negatywna:** §2, na kompletnej kopii drzewa (212 plików `.py`, 397 raportów),
`__pycache__` czyszczony przed przebiegiem (6.D102). Mutacja weszła do kopii, odczyt
kopii się zmienił, odczyt drzewa roboczego nie, `git status --porcelain` pusty.

**Przyrządu:** zdanie z dwiema pogrubionymi ma NIE trafić na listę — sprawdzone
i na parze syntetycznej, i na żywym drzewie (żadne z 54 takich zdań na liście nie
stanęło). Osobny test kotwiczy na ŻYWEJ instancji przypadku, który pozycję wywołał.

**Czytnik złapał własną samozwrotność:** proza tego modułu ma dokładnie ten kształt,
który moduł mierzy, więc bez odjęcia liczba mówiłaby o własnym przyrządzie. Plik jest
odejmowany jawnie, tak samo jak w 6.D277. Zauważyłem to, bo kontrola negatywna dała
najpierw czerwień na jednej podłodze zamiast na obu — populacja nie spadła poniżej
progu, bo domknęła ją moja własna proza.

**Bramka złapała mnie po raz drugi:** `MAX_POGRUBIONYCH_BEZ_POKRYCIA` zapaliła się
na prozie tego modułu (175 → 177), bo wpisałem liczby kosztu jako pogrubione i bez
pokrycia. Lekarstwo jest to, którego żąda jej własny komunikat: liczby stoją teraz
w kodzie jako stałe i wchodzą do komunikatu asercji przez `%d`.

**Przewidywania spisane przed przebiegiem — trzy z pięciu nietrafione:** liczbę spadków
L1 przewidziałem na 10–40 (są 2), liczbę spadków populacji całkowitej na 20–60 (są 3),
a kształt „druga pogrubiona" na większość (jest zero).

## 7. Czego ta pozycja nie ruszała

`ZAPOWIEDZ_POMIARU` nie została poszerzona — odrzucone pomiarem w 6.D275 i byłoby
osobnym rozstrzygnięciem. `MAX_GOLYCH_W_PROZIE_POMIAROWEJ` i
`MAX_POGRUBIONYCH_BEZ_POKRYCIA` nietknięte. Niczego nie pogrubiono.

**Podłogi na liczbę PLIKÓW (42) świadomie NIE postawiłem:** jej kosztu nikt nie
policzył, a zapadka bez policzonego kosztu jest dokładnie tym, czego ta seria nie robi.
Liczba idzie do raportu i do komunikatu asercji, nie do zapadki.

## 8. Co zauważyłem przy okazji, a czego nie tknąłem

1. **Szukanie po populacji znajduje zdjęcia, których szukanie po komunikatach commitów
   nie widzi.** 6.D275 zmierzyło, że zdjęcie pogrubienia zgłasza dwanaście komunikatów,
   a w diffie widać zero — bo ruch zachodzi przed commitem. Idąc od strony populacji
   znalazłem **jedno** zdjęcie widoczne w diffie (`ab88b4c`). To nie jest sprzeczność,
   tylko inny zbiór wejściowy; ale pokazuje dziurę w wyszukiwaniu po komunikatach,
   którą wyszukiwanie po populacji zamyka. Zapisane jako pozycja kolejki, nie wzięte.
2. **Pokrycie pogrubionej liczby bywa ZBIEGIEM CYFR z wiersza oddalonego dokładnie
   o szerokość okna — i wtedy zrywa je każda edycja obok.** W `test_bytecode_staleness.py`
   pogrubiona liczba w komentarzu o rozkładzie modułów była pokryta wyłącznie przez
   ogniwo łańcucha stojące o całe okno dalej. Dopisanie jednego wiersza ogniwa do słownika
   wypchnęło je poza okno i zapadka `MAX_POGRUBIONYCH_BEZ_POKRYCIA` zapaliła się na
   liczbie, której nikt nie ruszał. Ogniwa złożyłem w jeden wiersz, żeby nie przesuwać
   cudzej prozy — ale klasa „pokryta zbiegiem" jest z natury krucha i bramka sama ją tak
   nazywa. Nie tknąłem tego: zmiana szerokości okna albo klasy pokrycia jest osobnym
   rozstrzygnięciem.
3. **Jednostką „zdania" dla komentarzy `#:` jest POJEDYNCZY WIERSZ**, bo `proza` zwraca
   każdy token komentarza osobno. Zdanie rozpisane na dwa wiersze komentarza jest dla
   bramki dwoma zdaniami. To własność czytnika, nie pomiaru — poprawianie jej byłoby
   zmianą sita, a nie mierzeniem dziury.
