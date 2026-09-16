# 6.D236 — klasa znaków z jednym znakiem obcym: 1574 liczebniki i 31 zmyślonych setek

**16.09.2026**, na `d971310`. Wejście: `tools/tests/test_prose_counts.py`
(`WZORZEC_POMOCNIKOW`, skan w `_liczby_slowne_w_prozie`, fixture `stary_pomocnikow`),
`LICZEBNIKI`, całe drzewo `.py`/`.md`. Wyjście: dwie żywe klasy naprawione, cytat
historyczny oznaczony, przepisana proza, ten raport.

## 1. Co było nie tak

Klasy znaków wypisane z ręki niosły w miejscu `ęŁł` **jeden znak `U+A8F3`**
(DEVANAGARI SIGN CANDRABINDU VIRAMA). Wygląda jak polskie litery, nie jest nimi.

Wystąpień w drzewie śledzonym: **8, w 3 plikach** —
`tools/tests/test_prose_counts.py` ×4, `reports/6d218-…md` ×3, `docs/TASKS.md` ×1.
Z czterech w module **żywe są dwa**; trzecie to proza, czwarte to cytat historyczny.

## 2. Skan mylił się w OBIE strony, i druga strona jest gorsza

**Gubił:** z 92 kluczy mapy `LICZEBNIKI` klasa nie dopasowywała CAŁEGO słowa
dla **24** — wszystkich z `ę` (`pięć`, `dziesięć`, `dziewięćdziesięciu`, `tysięcy`…).

**Zmyślał:** „często" rozcinał na „cz" + „sto", a `sto` jest kluczem mapy o wartości
**100**. Zmierzone na całym drzewie `.py`/`.md`: **31 fałszywych setek**.

```
falszywych trafien: 31
  ('często','sto',100) x12   ('gęsto','sto',100) x12   ('stoi','sto',100) x4
  ('stołu','sto',100)  x1    ('stoją','sto',100)  x1   ('Gęsto','sto',100) x1
```

Źródłem są więc także **`stoi` i `stoją`** — wyrazy pospolite, nie tylko przysłówki
na „-sto". Skan widział w tym drzewie trzydzieści jeden setek, których nikt nie napisał.

**Ile liczebników klasa zepsuta traciła, na całym drzewie:**

```
klasa UNIWERSALNA widzi: 21263
klasa ZEPSUTA    widzi: 19689      roznica 1574
```

Liczenie per wiersz z odcięciem ujemnych daje 1606; **różnica wprost daje 1574** i to
jest liczba uczciwsza, bo nie zależy od sposobu sumowania. Podaję obie, żeby nikt nie
odtwarzał trzeciej.

## 3. Czego ta poprawka NIE naprawia — i to jest główny wynik

**Usterki nie łapie ANI JEDNA bramka, ani przed poprawką, ani po niej.** Zmierzone:

```
przebieg z klasami ZEPSUTYMI (test_prose_counts, test_tree_walks,
test_field_paths, test_assertion_gate, test_scan_gates):   119/119 przeszło
```

Powód jest liczbowy: skan prozy dwudziestu dwóch modułów z zapadką daje po naprawie
**1931** trafień, a ostrze `MINIMUM_LICZB_SLOWNYCH` stoi na **900** — czyli **1031
poniżej** populacji. Uszkodzenie zabierało setki trafień i nie zbliżało się do progu.

**Weryfikacją tej pozycji są więc POMIARY z §2, a nie zieleń zestawu.** Mówię to wprost,
bo zielony przebieg przy takiej poprawce czyta się jak potwierdzenie, a nie jest nim.

## 4. Klasa uniwersalna, nie wyliczenie poprawione ręką — pomiar, nie gust

Oba warianty dają dziś na drzewie wynik **identyczny** (0 zgubionych, 0 fałszywych),
więc liczba ich nie rozróżnia. Rozróżnia je **tryb awarii**: wyliczenie tnie słowo na
każdej literze, której nie wymieniono, a to drzewo nosi `é`, `è`, `à`, `µ` i `Δ`
w setkach wystąpień. **Rozcięcie nie jest skutkiem ubocznym tej usterki, tylko jej
mechanizmem** — 31 fałszywych setek powstało dokładnie tak. Wybrana jest klasa, która
nie tnie i nie wymaga pilnowania listy.

Dodatkowy argument stoi w samym pliku: `_LICZBA_RZADZI` używał `[^\W\d_]` **od dawna**,
z komentarzem uzasadniającym to tą samą usterką. Plik dawał więc dwie różne odpowiedzi
na to samo pytanie; poprawka usuwa rozjazd, wyliczenie by go utrwaliło.

## 5. Cytat historyczny ZOSTAJE — i jest to sprawdzone, nie przyjęte

Czwarte wystąpienie (`stary_pomocnikow`) jest **cytatem** wzorca sprzed 6.D218, razem
z jego uszkodzonym kodowaniem. Klasa jest tam **nieczynna**: `_LICZBA_RZADZI` dopasowuje
ją jako `\[[^\]]*\]\+` i przechwytuje dopiero słowo PO niej (`pomocniki`, czysty ASCII).

Zmierzone podstawieniem **siedmiu** różnych klas:

```
U+A8F3 (cytat)  -> [('stary_pomocnikow', 'pomocniki')]
[Q]             -> [('stary_pomocnikow', 'pomocniki')]
[ą]             -> [('stary_pomocnikow', 'pomocniki')]
[0-9]           -> [('stary_pomocnikow', 'pomocniki')]
[^x]            -> [('stary_pomocnikow', 'pomocniki')]
[^\W\d_]        -> [('stary_pomocnikow', 'pomocniki')]
wyliczenie ęŁł  -> [('stary_pomocnikow', 'pomocniki')]
```

Nawet `[Q]` i `[0-9]` dają ten sam wynik, więc **zawartość klasy nie może mieć
znaczenia**. Poprawienie zamieniłoby cytat w parafrazę i skasowało jedyny ślad, że
usterka jest **starsza** niż 6.D218, nie zyskując ani jednego trafienia. Przy klasie
stoi teraz komentarz z tym pomiarem, żeby następny audyt nie zgłosił jej po raz trzeci.

## 6. Proza przepisana, bo poprawka czyniła ją nieprawdziwą

Komentarz przy `_LICZBA_RZADZI` mówił, że klasy wypisane z ręki „**mają**" uszkodzone
kodowanie. Po naprawie zdanie stałoby się nieprawdą **stojącą bezpośrednio przy
naprawionym przyrządzie** — dokładnie kształt, którego `test_prose_counts.py` istnieje,
żeby pilnować u innych. Akapit jest **przepisany, a nie dopisany obok**, z liczbami
datowanymi na dzień pomiaru.

## 7. Weryfikacja

```
KOD=0
  <pełny zestaw — liczby z przebiegu wyłącznego>
```

Moduły liczące drzewo, każdy osobno: `test_prose_counts.py`, `test_tree_walks.py`,
`test_field_paths.py`, `test_assertion_gate.py`, `test_scan_gates.py`,
`test_report_claims.py` — **147/147**.

Zapadki: **żadna nie drga**. Diff nie zmienia ani jednej stałej liczbowej — tylko dwa
literały wyrażeń regularnych i dwa bloki komentarza. `MINIMUM_LICZB_SLOWNYCH` zostaje
na 900 (wartość pilnowana rośnie z 1768 do 1931, czyli zapas rośnie),
`MIN_DEKLARACJI_POMIARU` bez zmian. `MIN_REPORTS` rośnie o jeden za ten raport.

## 8. Czego świadomie nie zrobiłem

- **Nie tknąłem trzech wystąpień w `reports/6d218-…md`** — to raport DATOWANY, opisuje
  stan z 15.09.2026 i wtedy był prawdziwy. Raporty tego projektu są zapisem przeszłości
  (6.D108).
- **Nie tknąłem wystąpienia w `docs/TASKS.md`** — wiersz pozycji mówi „w trzech
  miejscach"; po tej poprawce wymaga przepisania na „w trzech, z czego dwa naprawione,
  trzecie jest cytatem", ale to zmiana wiersza pozycji, którą robię adnotacją, a nie
  przepisywaniem treści pierwotnej.
- **Nie podniosłem `MINIMUM_LICZB_SLOWNYCH`** z 900 bliżej 1931, mimo że §3 pokazuje, jak
  nisko stoi. To zmiana zapadki, czyli osobna decyzja — a moduł sam pisze, że ostrze ma
  stać nisko, bo liczba rusza się przy każdej edycji prozy. **Zgłaszam jako kandydata na
  pozycję**, nie robię przy okazji (§4.10).

## 9. Co zauważyłem przy okazji, ale nie tknąłem

- **Drugi homoglif w drzewie, ×4: `U+0430 CYRILLIC SMALL LETTER A` w słowie „oglądа".**
  `tools/tests/test_needle_specificity.py:123`, `reports/swoistosc-igly.md`,
  `reports/swoistosc-igly-game.md`, `reports/asercja-rozstrzygajaca.md`. Ta sama rodzina:
  znak wygląda poprawnie i nie jest tym, czym się wydaje. W module stoi **w napisie
  asercji**, więc porównanie po znakach dałoby cichy rozjazd. Kandydat na pozycję.
- **Inwentarz liter spoza ASCII w `.py`/`.md`**, przydatny przy każdej przyszłej klasie
  wypisywanej z ręki: `µ`, `é`, `Δ`, `è`, `É`, `μ`, `à`, `λ`, `ô`, `ꣳ`, `а`, `ê`, `ⁿ`,
  `ℓ`, `σ`, `î`, `œ`, `φ`, `ε`, `û`, `ç`. **Każda klasa wypisana z ręki musi je wszystkie
  wymienić albo po cichu tnie.**
- **`reports/6d218-…md` twierdzi, że uszkodzenie stoi w DWÓCH miejscach.** Stoi
  w czterech, z czego żywe były dwa. Zdanie było prawdziwe w swoim zakresie (żywe), ale
  czyta się jak zdanie o wszystkich; nie poprawiam z powodu 6.D108.
