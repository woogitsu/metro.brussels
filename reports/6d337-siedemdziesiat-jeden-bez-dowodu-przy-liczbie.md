# 6.D337 · Siedemdziesiąt jeden raportów nie stawia przy liczbie ŻADNEGO dowodu — a kontrola przyrządu nie da się spełnić, bo pyta o raport, gdy jednostką jest ZDANIE

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `c5fd247`

6.D328 §1.2 zmierzyło, że liczba **136 nazw i 202 pary** z 6.D317 nie wychodzi
w żadnym z dwunastu odczytań definicji, którą tamten raport przy niej zapisał —
a drzewo się nie zmieniło. Ta pozycja pyta, ile jeszcze raportów podaje liczbę
populacji, nie niosąc przy niej tego, czego trzeba, żeby ją sprawdzić.
**Liczy i wypisuje imiennie**; żadnego raportu nie prostuje.

---

## 1. Kontrola przyrządu NIE PRZECHODZI — i nie da się jej spełnić

Pole żądało, żeby `reports/6d317-…md` wyszedł w klasie „nie nazywa ani czytnika,
ani polecenia". Nie wychodzi, i powód nie jest usterką przyrządu:

```
=== KONTROLA PRZYRZADU ===
   6d317-siedemdziesiat-jeden-procent-w-klasie-reszta.md
   klasy jego stwierdzen: CZYTNIK 3 · ODSYLACZ 3 · BEZ DOWODU 3 · POLECENIE 1
```

**Ten raport niesie oba rodzaje stwierdzeń naraz.** Ma sekcję weryfikacji z gołym
poleceniem, ma nazwy pożyczonych czytników w grawisach — i ma trzy zdania z liczbą,
przy których nie stoi nic. Żaden klasyfikator działający **na raportach** nie postawi
go w jednej klasie, bo raport nie jest w jednej klasie.

**Rozstrzygające jest to, że instrument zgadza się z 6.D328 tam, gdzie tamten mierzył.**
Zdanie, o które szło:

```
[BEZ DOWODU] **Liczba wystąpień (202) jest o 66 większa od liczby nazw (136)**, czyli średnio
             1,49 pliku na nazwę. …
```

wypada dokładnie w klasie bez dowodu. **Jednostką pytania jest ZDANIE, a nie raport**,
i to jest pierwsze znalezisko tej pozycji. Przewidywanie Q1 obalone.

## 2. Dwie usterki przyrządu, obie znalezione przez tę kontrolę

**Wersja pierwsza sprawdzała CAŁY RAPORT** — czy gdziekolwiek w nim stoi polecenie
albo nazwa czytnika. Postawiła `6d317` w klasie „nazywa polecenie", bo raport **ma**
sekcję weryfikacji — sześćdziesiąt stron dalej od liczby, której dotyczy pytanie.
Dowód ma stać **przy liczbie**, a nie gdziekolwiek w tekście.

**Wersja druga wiązała dowód z akapitem, ale uznawała KAŻDY blok ogrodzony za
polecenie.** Blok ``` ``` ``` w tych raportach jest zwykle **wyjściem**, nie
poleceniem: pierwszy zapis 136/202 w 6.D317 stoi właśnie w takim bloku i wersja
druga liczyła go jako udowodniony. Dowodem jest dopiero polecenie widoczne w oknie.

**Ścieżka liczby „bez dowodu" przez dwie porównywalne wersje: 824 → 1023.**
Dwieście stwierdzeń, czyli co piąte z tej klasy, zawdzięczało „dowód" samemu
istnieniu ogrodzenia.

## 3. Cztery liczby, których żądało pole

Populacja: **438 raportów z 457** podaje liczbę populacji (liczba ≥ 2 przy
rzeczowniku liczonego zbioru w tym samym akapicie albo bloku). Czytnik raportów —
`_reports` z `test_report_hygiene.py`, **pożyczony**.

### 3.1 Na poziomie RAPORTU — tak, jak pyta pole

Klasa = najlepszy dowód, jaki raport gdziekolwiek stawia przy jakiejkolwiek swojej
liczbie:

```
   POLECENIE PRZY LICZBIE      167
   CZYTNIK PRZY LICZBIE         75
   ODSYLACZ PRZY LICZBIE       125
   BEZ DOWODU PRZY LICZBIE      71
                              ----
   SUMA                        438   (populacja 438)   ZGADZA SIĘ
```

**Odpowiedź na pytanie zadane wprost: nieodtwarzalnych jest SIEDEMDZIESIĄT JEDEN,
czyli 16 % raportów podających liczbę populacji.** Klasy sumują się do populacji —
sprawdzone, a nie założone.

### 3.2 Na poziomie ZDANIA — bo §1 pokazało, że to jest właściwa jednostka

```
   POLECENIE PRZY LICZBIE       238
   CZYTNIK PRZY LICZBIE         230
   ODSYLACZ PRZY LICZBIE        798
   BEZ DOWODU PRZY LICZBIE     1023
                               ----
   SUMA                        2289
```

```
raportow z CO NAJMNIEJ JEDNYM stwierdzeniem bez dowodu: 358 (82 %)
raportow, w ktorych ZADNE stwierdzenie nie ma dowodu:    71 (16 %)
```

**Te dwie liczby — 16 % i 82 % — są odpowiedziami na dwa różne pytania i podaję
obie**, zamiast wybrać wygodniejszą. Pole pyta o raport, więc odpowiedzią jest 71.
Ale zdanie bez dowodu stoi w czterech raportach na pięć, a właśnie takie zdanie
6.D328 znalazło w 6.D317.

**Najliczniejszą klasą stwierdzeń jest ODSYŁACZ (798)** — liczba podana z numerem
pozycji albo ze ścieżką raportu obok. Odsyłacz przenosi ciężar sprawdzenia na
cudzy raport i **nie jest sam w sobie odtwarzalnością**; jest nią wtedy i tylko
wtedy, gdy tamten raport dowód niesie. Tego ta pozycja nie mierzy i mówię to
wprost, zamiast liczyć odsyłacz jako dowód.

## 4. Lista imienna klasy „bez dowodu" — 71 raportów

```
6d105-dwie-tabele-statusow · 6d113-zero-i-dlaczego · 6d127-asercje-bez-komunikatu
6d128-jedno-wywolanie-list-sdks · 6d130-dwa-powody-odrzucenia-literalu
6d133-kierunek-zapadki · 6d134-est-zero-uzyc · 6d135-dwie-maszyny-jeden-prog
6d140-okno-kadru-a-cztery-klatki · 6d141-piny-liczbowe · 6d157-zly-adres-trzy-razy
6d161-zdania-ubezpieczenia · 6d162-dwie-maszyny-jedno-slowo · 6d166-liczby-w-prozie
6d167-straznicy-dwoch-zapadek · 6d174-prefiks-mierzalny-miejsce-uzycia-nie
6d175-trzy-ze-stu-czterdziestu · 6d179-koniec-pakietu-i-usterka-czytnika
6d185-nazwy-czlonow-na-ekranie · 6d187-gola-nazwa-i-zero-urobku
6d188-czternascie-i-ani-jednego-jsona · 6d194-dziewiec-retencji-osiem-bez-materialu
6d195-napis-a-zachowanie-849-na-31 · 6d202-zero-wierszy-angielskich-… · 6d21-objaw-nieodtworzony
… i czterdzieści sześć dalszych
```

**Wszystkie mieszczą się w przedziale numerów 6.D21 – 6.D202**, czyli w pracy
starszej niż 6.D203. Nie wyciągam z tego wniosku o tempie poprawy: tego, czy
konwencja dowodu przy liczbie się zacieśniła, ta pozycja nie mierzy, a przedział
numerów nie jest chronologiczny ani tematyczny — zmierzyło to 6.D170 i stoi
w `CLAUDE.md` §3.

## 5. Przewidywania — cztery trafione, jedno obalone, jedno rozdzielone

| # | przewidywanie | wynik |
|---|---|---|
| Q1 | kontrola przyrządu przejdzie | **OBALONE**: nie da się jej spełnić na poziomie raportu (§1) |
| Q2 | raportów z liczbą populacji więcej niż 200 | **trafione**: 438 z 457 |
| Q3 | „nazywa polecenie" będzie najliczniejsza | **rozdzielone**: na poziomie raportu tak (167), na poziomie zdania NIE — najliczniejszy jest odsyłacz (798) |
| Q4 | nieodtwarzalnych mniej niż jedna czwarta | **trafione**: 16 % — ale 82 % raportów ma co najmniej jedno zdanie bez dowodu (§3.2) |
| Q5 | sito pomyli się co najmniej raz | **trafione** dwa razy (§2) |
| Q6 | jakiś raport pasuje do trzech klas naraz | **trafione**: `6d317` pasuje do wszystkich czterech |

**Warunek obalenia Q4 spisałem przed pomiarem** i nie wypełniam go: przy odczycie,
o który pyta pole, nieodtwarzalnych jest 16 %, czyli poniżej czwartej części.
**6.D317 jest więc wypadkiem, a nie wzorcem** — ale wypadkiem należącym do klasy
siedemdziesięciu jeden, nie jedynym.

## 6. Czego świadomie nie zrobiłem

Nie sprostowałem żadnego raportu, nie postawiłem bramki na odtwarzalności, nie
zmieniłem `CLAIM`, nie tknąłem `src/` ani `data/` — wszystko to stoi w polu „Poza
zakresem".

**Nie sprawdziłem, czy odsyłacz prowadzi do raportu, który dowód niesie.** Byłby to
przejazd rekurencyjny po 798 odsyłaczach i **inne pytanie**; §3.2 mówi, że odsyłacza
nie liczę jako odtwarzalności, i na tym poprzestaję.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

Klasa „czytnik przy liczbie" urosła z wersji drugiej do trzeciej (204 → 230), choć
poprawka dotyczyła **poleceń**. Przyczyna jest w kolejności rozstrzygania: zdania,
które dotąd wygrywał „polecenie", przeszły do następnej pasującej klasy. Liczba
klasy zależy tu więc od miejsca w kolejce tak samo jak od drzewa — ten sam kształt,
który 6.D317 §2 nazwało przy klasach nakładających się, a 6.D333 §5 zmierzyło na
komunikatach scaleń.
