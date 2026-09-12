# 6.D153 — ocena ryzyka kolizji policzona na korpusie, którego bramka nie czyta

**12.09.2026**, na `2b95084`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(docstring `NazwyKlawiszySilnika`), `src/Game/**/*.cs`, 40 rewizji `src/Game`
z historii repozytorium. Pozycja: zauważone przy 6.D143 — zdanie o ryzyku podaje
liczby z korpusu szerszego niż zasięg przyrządu, który opisuje.

## 1. Przesłanka pozycji jest prawdziwa i odtwarza się co do jedynki

Docstring mówił: *„W całym `src/Game/` stoi **948** literałów (746 różnych), a nazwą
klawisza jest **sześć**: `Escape`, `F1`, `F2`, `Forward`, `Right`, `Up`"*.

Bramka nie czyta „całego `src/Game/`". Czyta `ZrodlaGry()` przepuszczone przez
`KodBezKomentarzy()`: pliki `*.cs` bez `.godot` i bez `UiText.cs`, z pominięciem
wierszy zaczynających się od `//`. Oba korpusy zmierzone tym samym wyrażeniem, którego
używa `Literaly`:

| korpus | plików | literałów | różnych | nazw klawiszy |
|---|---|---|---|---|
| **zasięg bramki** (bez komentarzy, bez `UiText.cs`) | 21 | **521** | **395** | **7**: `C, F1, F2, R, S, W, X` |
| szerzej (z komentarzami i z `UiText.cs`) | 22 | 940 | 742 | **6**: `Escape, F1, F2, Forward, Right, Up` |

Liczby z zasięgu bramki — 521 / 395 / siedem — zgadzają się z polem „Wejście" pozycji
dokładnie. Szósta lista też się odtwarza, więc dawne zdanie **nie było zmyślone**:
było policzone nie tam.

**Różnica wobec liczby z pozycji jest odnotowana, a nie ukryta.** Pozycja mówiła
o szerszym korpusie „dziś 949 / 748"; mierzę **940 / 742**. Sprawdziłem, że nie robią
tego pliki generowane — z `.godot` i bez `.godot` wychodzi ta sama para 940 / 742 —
więc różnica bierze się z innego commitu pomiaru. Do raportu wchodzi liczba, którą
sam zmierzyłem, bo jest odtwarzalna poleceniem wyżej.

## 2. Cztery z tamtych sześciu nie są literałami kodu w ogóle

Nie chodzi o to, że stoją w innym pliku. Nie stoją w żadnym kodzie:

```
=== Escape
src/Game/Input/KeyNames.cs:15:/// stały poza kontrolą: podmiana <c>"Esc"</c> na <c>"Escape"</c> nie zapalała żadnej
=== Forward
src/Game/World/SceneAxis.cs:9:/// <param name="Forward">Kierunek jazdy.</param>
=== Right
src/Game/World/SceneAxis.cs:10:/// <param name="Right">Prawa strona względem kierunku jazdy.</param>
=== Up
src/Game/World/SceneAxis.cs:11:/// <param name="Up">Pion.</param>
```

`Escape` to cudzysłów w prozie komentarza, a pozostałe trzy to **wartości atrybutu
`<param name="...">`** w komentarzu XML. Wyrażenie `Literaly` puszczone na tekst
z komentarzami bierze je za literały, bo nie odróżnia kodu od komentarza — i to jest
cały mechanizm dawnej szóstki. Pięciu jednoliterowych, które w kodzie naprawdę stoją
(`C, R, S, W, X`), tamto zdanie nie wymieniało.

Ocena policzona szerzej niż zasięg przyrządu **zawyżała ryzyko** (czterema napisami,
których bramka nie widzi) i **jednocześnie pomijała to, które istnieje** (pięcioma,
które widzi).

## 3. Ile tego ryzyka jest naprawdę: zero — i jest to wynik, nie brak pomiaru

Do `PowodOdrzucenia` trafia wyłącznie literał **zgłoszony**, a zgłasza go
`WzorzecSlowa = \p{L}{2,}` — dwie litery pod rząd. Puszczone przez to samo sito:

```
w zasiegu bramki -> czy bramka w ogole by je ZGLOSILA:
   C        -> False
   F1       -> False
   F2       -> False
   R        -> False
   S        -> False
   W        -> False
   X        -> False
zglaszalnych z zasiegu: 0 z 7
szerzej (tylko w komentarzach) -> zglaszalne: ['Escape', 'Forward', 'Right', 'Up']
```

Kolizja w zasięgu bramki jest dziś **nieosiągalna**, i to ze względu strukturalnego:
pięć nazw jest jednoliterowych, a `F1` i `F2` niosą literę i cyfrę. Odwrotnie
w korpusie szerszym — tam zgłaszalne są **wszystkie cztery**, więc gdyby któraś zeszła
z komentarza do kodu, kolizja stałaby się realna tego samego dnia.

## 4. Przybity jest ZBIÓR, a nie liczba, i to jest pomiar, nie gust

Na 40 rewizjach `src/Game` z historii repozytorium:

```
rewizji dotykajacych src/Game: 40
rewizji, w ktorych para (literaly, rozne) SIE ZMIENILA: 29 z 39 przejsc
przejsc, w ktorych ZBIOR nazw klawiszy sie zmienil: 2 z 39
roznych zbiorow w historii: 3
```

Zapadka na liczbach zapalałaby się w **trzech rewizjach na cztery** — czyli zostałaby
wyłączona przy pierwszym tygodniu pracy, jak każda bramka, która krzyczy na poprawną
zmianę. Zapadka na **zbiorze** kosztuje 2 na 39 i pilnuje dokładnie tego, o czym mówi
akapit: że w zasięgu bramki nie pojawiła się nowa nazwa klawisza. Liczby zostają jako
**dolne ostrza na sam skan** — bez nich pusty korpus dałby „zero osiągalnych kolizji"
i test meldowałby sprawdzenie, którego nie zrobił (6.D27).

**Pomiar był możliwy dopiero po odgłębieniu klonu.** Kontener sesji dostał 50 commitów;
`git log -- src/Game` widział wtedy **2** rewizje, więc liczba „29 z 39" nie istniała.
Po `git fetch --unshallow` historia ma 882 commity i 40 rewizji `src/Game`. Jest to ten
sam kształt, który 6.D108 rozstrzygnęło dla dat stałych i z którego wziął się
`fetch-depth: 0` — tym razem trafiony od strony pomiaru, a nie bramki.

## 5. Kontrole negatywne

Baza `dotnet test tests/Game.Tests`: **238/238** (przed pozycją 237). Po każdej
kontroli `md5sum -c` na `UiTextTests.cs` daje `OK`.

| kontrola | co zmienia | skutek |
|---|---|---|
| KN-1 | literał `"Escape"` w pliku **kodu skanowanego** | **237/238** — `zbiór nazw klawiszy w korpusie bramki rozjechał się…: C, Escape, F1, F2, R, S, W, X` |
| KN-2 | literał `"Q"` tamże (nazwa klawisza NIEzgłaszalna) | **237/238** — `…: C, F1, F2, Q, R, S, W, X` |
| KN-3 | skan zwężony do jednego pliku | **0/1** — `korpus bramki ma 1 plików wobec zmierzonych 21` |
| KN-4 | `WzorzecSlowa` żąda dziewięciu liter | **0/1** — ``Escape` przestało być zgłaszalne — wtedy zero wyżej nie mówi o strukturze nazw, tylko o tym, że sito nic nie zgłasza` |

**KN-1 jest tą kontrolą, której żąda reguła „nowy warunek strażniczy potrzebuje
wejścia, które go wykonuje".** Warunek `IsFalse(wKorpusie.Contains(nazwa))` mówi
o zejściu nazwy z komentarza do kodu — bez KN-1 byłby zdaniem o zdarzeniu, które nigdy
nie zaszło, a więc zielenią niczego nie mierzącą.

**KN-4 jest parą do zieleni z sekcji 3.** Pierwsza połowa testu wychodzi zielona
i jest to odpowiedź pozycji, a nie brak pomiaru — ale zielona byłaby także wtedy, gdyby
sito przestało zgłaszać cokolwiek. KN-4 mierzy, że różnicę robi **struktura nazw**,
a nie zanik pilnowania: przy sicie żądającym dziewięciu liter `Escape` przestaje być
zgłaszalne i test zapala się własnym komunikatem.

**KN-2 oddziela dwie zapadki od siebie.** `Q` jest nazwą członu `Godot.Key`
i jednocześnie nie jest zgłaszalne, więc zapala wyłącznie zapadkę na zbiór, zostawiając
„zero osiągalnych" zerem. Bez niej jedna czerwień mogłaby uchodzić za obie.

## 6. Czego ten raport nie rusza

- **Drugiego akapitu o skali w `CzlonyKeyNames`** („348 literałów w 21 plikach,
  z czego 22 w `throw`"). Mówi o czymś innym — ile bramka **zgłosiłaby** na całym
  `src/Game/`, a nie ile stoi literałów — i należy do 6.D143. Reguła 10 mówi, że
  zadanie nie poprawia przy okazji plików ani zdań spoza swojego zakresu.
- **`reports/6d130-dwa-powody-odrzucenia-literalu.md`**, który niesie tamtą szóstkę.
  Raport opisuje stan swojego dnia i po 6.D108 jest to zdanie poprawne, a nie dług.
- **Wartości żadnej zapadki** poza `MIN_REPORTS`, którą podnosi sam fakt dołożenia
  tego pliku.
