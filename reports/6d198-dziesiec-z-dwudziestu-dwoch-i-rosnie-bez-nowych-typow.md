# 6.D198 — dziesięć z dwudziestu dwóch, i rośnie bez ani jednego nowego typu

**13.09.2026**, na `3a6a34e`. Wejście: `src/` (całe, poza `.godot/`, `obj/`, `bin/`),
`tests/Game.Tests/UiTextTests.cs` (`WyliczeniaZrodel`, `NazwyOTypieWyliczeniowym`,
`FalszyweTrafieniaSkanu`), `reports/6d185-nazwy-czlonow-na-ekranie.md` §5.

## 1. Odpowiedź: DZIESIĘĆ z dwudziestu dwóch — 45 %, nie trzy

Pozycja wymieniała trzy nazwy dwuznaczne i **sama zastrzegała**, że trzy to liczba
z dwunastu trafień, a nie z drzewa. Z drzewa wychodzi ponad trzy razy tyle.

| liczba | ile |
|---|---|
| typów wyliczeniowych w `src/` | **16** |
| nazw, pod którymi stoi wartość typu wyliczeniowego | **22** |
| z tego nazw **dwuznacznych** | **10** — czyli **45 %** |
| z tych dziesięciu takich, gdzie drugą stroną jest `string` | **9** |

Wszystkie trzy nazwy wskazane przez 6.D185 są na liście.

| nazwa | wyliczenie | drugi typ |
|---|---|---|
| `Action` | `ProtectionAction` | `string` ×1 |
| `Phase` | `DoorPhase` | `string` ×2 |
| `Reason` | `AuthorityLimit` | `string` ×8 |
| `Variant` | `ProtectionVariant` | `string` ×2 |
| `_view` | `ViewKind` | `Label` ×1 |
| `load` | `TrainLoad` | `string` ×1 |
| `phase` | `DoorPhase` | `string` ×1 |
| `status` | `ParameterStatus`, `ProtectionModeStatus` | `string` ×4 |
| `variant` | `ProtectionVariant` | `string` ×2 |
| `view` | `ViewKind` | `string` ×1 |

**Dziewiątka z ostatniej kolumny jest treścią, nie ciekawostką.** Gdyby drugą stroną
dwuznaczności były INNE WYLICZENIA, sito po nazwie dałoby się uratować słownikiem typów
— tak jak 6.D185 uratowało czytnik deklaracji, sięgając po `src/Sim/`. Napis takiej drogi
nie zostawia: `string` nie ma członów, po których dałoby się rozstrzygnąć.

## 2. Rośnie PRZY ZAMROŻONYCH obu populacjach, które miałyby to napędzać

To jest właściwa odpowiedź na pytanie pozycji („czy przybywa ich z każdym nowym typem").
**Nie przybywa ich z nowym typem, bo nowych typów nie ma — a dwuznaczności przybywa.**

| commit | data | plików `.cs` | wyliczeń | nazw | dwuznacznych |
|---|---|---|---|---|---|
| `6991b8c8` | 02.09 | 50 | **16** | 19 | 5 |
| `a643f056` | 03.09 | 53 | 16 | 20 | 5 |
| `259d8ef4` | 04.09 | 58 | 16 | 20 | 5 |
| `c68e099a` | 05.09 | 62 | 16 | **22** | 7 |
| `ee84432a` | 05.09 | 67 | 16 | 22 | 8 |
| `3e2b0ef7` | 06.09 | 74 | 16 | 22 | 9 |
| `6e0d525b` | 07.09 | 75 | 16 | 22 | 9 |
| `c19f2f1b` | 09.09 | 75 | 16 | 22 | **10** |
| `fdabff4e` | 11.09 | 77 | 16 | 22 | 10 |

**Liczba wyliczeń stoi na 16 od 02.09.2026. Liczba nazw stoi na 22 od 05.09.2026.**
Między 05.09 a 11.09 plików przybyło **piętnaście**, typów **zero**, nazw **zero**,
a dwuznacznych **trzy**. Mechanizm nie jest więc „nowy typ = nowa dwuznaczność", tylko
**„nowe pole `string` dostaje nazwę, której wyliczenie już używa"** — a pól `string`
przybywa nieporównanie szybciej niż typów.

## 3. Rozstrzygnięcie: zdanie o „puszczeniu szerzej" jest PRZEPISANE, nie powtórzone

6.D185 zapisało warunek: *„gdyby trafień fałszywych ubyło do zera, skan po nazwie wolno
byłoby puścić szerzej niż na drogę `Hud.Update`"*.

**Warunek zostaje, bo jest poprawny** — gdyby ubyło, wolno by było — i zostaje tam, gdzie
stoi: w komunikacie tamtej bramki, który zapali się w obie strony. **Przestaje natomiast
być planem**, i to jest zmiana, którą ta pozycja wnosi. Spełnienie warunku wymaga drzewa,
które dwuznaczności się pozbywa; zmierzony ruch idzie monotonicznie w drugą stronę
(5 → 7 → 8 → 9 → 10, ani razu w dół), napędza go populacja rosnąca niezależnie od typów,
a w drzewie nie ma niczego, co by go hamowało. Kto przeczyta tamto zdanie jako zapowiedź,
będzie czekał na stan, do którego nic nie zmierza.

Zapisane jest to **liczbą i listą**, nie prozą: `WyliczenWSrc = 16`,
`NazwPodWyliczeniem = 22`, `NazwyDwuznaczneWSrc` (dziesięć nazw, równość na liście),
`DwuznacznychPrzezNapis = 9`. Lista, a nie sama liczba, bo liczba nie mówi, KTÓRA nazwa
doszła — rodzina 6.D212. Komunikat asercji mówi **obie strony**: jeśli przybyło, sito jest
jeszcze mniej zdatne niż w dniu zapisu warunku; jeśli ubyło, warunek 6.D185 zbliżył się
do spełnienia i wolno wrócić do pytania o korpus.

## 4. Kształt deklaracji ZDEJMUJE zależność od obcinacza komentarzy

Pierwsza wersja czytnika pytała tylko o sąsiedztwo (`Typ nazwa`). Zmierzone na trzech
wariantach tego samego tekstu:

```
SUROWE     deklaracja=False  wyliczen=16 nazw=24 dwuznacznych=12
WIERSZOWO  deklaracja=False  wyliczen=16 nazw=24 dwuznacznych=11
MASKA      deklaracja=False  wyliczen=16 nazw=24 dwuznacznych=11

SUROWE     deklaracja=True   wyliczen=16 nazw=22 dwuznacznych=10
WIERSZOWO  deklaracja=True   wyliczen=16 nazw=22 dwuznacznych=10
MASKA      deklaracja=True   wyliczen=16 nazw=22 dwuznacznych=10
```

**Bez członu o kształcie deklaracji wynik ZALEŻY OD CZYTNIKA**, a nie od drzewa: polskie
zdanie „…wcina `Environment`…" wygląda dla wzorca tak samo jak deklaracja, a
`Nieznany status parametru` z literału napisowego — tak samo jak `string status`.
Dwunastka i jedenastka różnią się wyłącznie tym, czy komentarze zdjęto.

**Z tym członem wszystkie trzy warianty dają tę samą dziesiątkę.** Obcinacz przestaje
rozstrzygać — i jest to **postawione jako asercja**, a nie zapisane w komentarzu:
`Ksztalt_deklaracji_ZDEJMUJE_zaleznosc_od_obcinacza_komentarzy` liczy obie strony i
porównuje je, z jawnym licznikiem obiegów pętli (rodzina 6.D193). Zniknęły przy tym dwa
fałszywe trafienia z listy nazw: `Parse` (nazwa METODY, poprzedzana typem zwracanym) i
`StateOf` (to samo) — 24 nazwy to było 22 nazwy plus dwie metody.

Jest to dokładnie ten kształt, który 6.D197 zapisało jako **6.D212**: bramka, której wynik
zależy od czytnika, mówi o czytniku, a nie o drzewie. Tutaj dało się to **usunąć**, a nie
tylko nazwać — zaostrzając pytanie, a nie zmieniając obcinacz.

## 5. Sześć kontroli negatywnych, baza 265/265

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | nowa nazwa dwuznaczna w `src/` (`private string Kind;` w `RunPlan.cs`) | **4 czerwone** |
| KN-2 | człon `PoNazwieWDeklaracji` zdjęty (pytanie o samo sąsiedztwo) | 3 czerwone |
| KN-3 | bez odsiewania typów wyliczeniowych z drugiej strony | 3 czerwone |
| KN-4 | bez odsiewania słów kluczowych C# | 2 czerwone |
| KN-5 | skan pomija `FirstRun.cs` (kontrola przyrządu) | 2 czerwone |
| KN-6 | pętla po wariantach tekstu obiega raz zamiast dwóch | 1 czerwona |

`md5sum -c` na obu plikach po każdej kontroli: `OK`. **Ani jedna kontrola nie wyszła
zielona** — pierwszy raz w tej sesji od 6.D194.

**KN-6 jest tu obowiązkowa, nie ozdobna.** Test porównujący dwa warianty tekstu składa się
z pętli i równości; równość na liście o jednym elemencie przechodzi zawsze. Dokładnie ta
pułapka zapaliła się przy 6.D193 dwa razy z rzędu, więc licznik obiegów stoi tu od razu,
a KN-6 sprawdza, że działa.

## 6. Czego świadomie nie zrobiłem

- **Nazw w `src/` nie zmieniałem** — pole „Poza zakresem" mówi wprost, że to zmiana
  rdzenia i warstwy gry naraz.
- **Korpusu bramki 6.D185 nie poszerzyłem** — pole „Poza zakresem" zabrania tego przed
  rozstrzygnięciem tej pozycji, a rozstrzygnięcie brzmi: nie poszerzać.
- **Zdania z 6.D185 nie usunąłem.** Jest poprawnym warunkiem i ma się zapalić, gdyby
  drzewo ruszyło w drugą stronę. Przepisane jest to, czym ono JEST — warunkiem, nie planem
  — i stoi to w sekcji 6.D198, przy liczbach, które to rozstrzygają.

## 7. Zauważone po drodze, nie tknięte

- **`Reason` jest dwuznaczne OŚMIOKROTNIE** — to **8 z 23** deklaracji po drugiej stronie,
  czyli ponad jedna trzecia całego zjawiska w jednej nazwie, a druga co do wielkości
  (`status`) ma cztery. Jest to ta sama nazwa, którą 6.D185 wymieniło pierwszą.
- **`_view` jest jedynym przypadkiem, gdzie druga strona NIE jest napisem** — stoi pod nią
  `Label` z Godota. Jest to też jedyna dwuznaczność, która przyszła z warstwy silnika,
  a nie z rdzenia; `CLAUDE.md` §4.9 zabrania rdzeniowi znać Godota, więc ta jedna nie
  może się rozprzestrzenić do `src/Sim/`.
- **`Status` (z wielkiej litery) jest dziś JEDNOZNACZNE, a `status` (z małej) nie.** Ta
  sama nazwa w dwóch pisowniach leży po dwóch stronach podziału, a czytnik jest
  rozróżniający wielkość liter. Gdyby ktoś ujednolicił nazewnictwo pól i parametrów,
  dwuznaczność przeskoczyłaby na `Status` bez żadnej zmiany semantyki.
