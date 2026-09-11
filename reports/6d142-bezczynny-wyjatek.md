# 6.D142 — wyjątek `NazwyKlawiszy` jest bezczynny dla swojego jedynego wpisu

**11.09.2026**, na `8f7660e`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/Input/KeyNames.cs`. Pozycja miała rozstrzygnąć, czy lista
`NazwyKlawiszy = { "Esc" }` zostaje wartownikiem, czy znika.

## Pytanie pozycji

Pole „Dlaczego to nie jest zdjęcie martwego wpisu" kazało rozstrzygnąć, czy lista
`NazwyKlawiszy = { "Esc" }` zostaje wartownikiem z zapisanym powodem, czy znika razem
z powodem, dla którego istniała.

## Wejście pozycji jest NIEPRAWDZIWE i to jest główny wynik

Wpis 6.D142 — za wpisem 6.D130 — mówił: zdjęcie `"Esc"` z listy daje 233/233, **bo**
napis mieszka od 6.D116 w `KeyNames.cs`, którego bramka literałów nie skanuje.

Zielono byłoby także wtedy, gdyby `"Esc"` stało wprost w pliku skanowanym. Kolejność
sit w `SlowaWKodzie` jest taka:

1. ścieżka węzła sceny,
2. identyfikator silnika,
3. **`NazwyKlawiszy.Contains`** ← wyjątek,
4. `UiText.Keys.Contains`,
5. `Regex.IsMatch(BezJednostek(BezDziur(literał)), WzorzecSlowa)`.

Sito 5 nie pyta o literał, tylko o literał **po zdjęciu jednostek**, a `Jednostki`
niosą `"s"`. Zmierzone przebiegiem probnym (tymczasowy test `PROBE_`, zdjęty po
pomiarze, `md5sum -c: OK`):

```
 PROBE Esc      BezJednostek=E c      jestSlowem=False zgloszone=0
 PROBE Enter    BezJednostek=Enter    jestSlowem=True  zgloszone=1
 PROBE Tab      BezJednostek=Tab      jestSlowem=True  zgloszone=1
 PROBE Shift    BezJednostek=Shift    jestSlowem=True  zgloszone=1
 PROBE Ctrl     BezJednostek=Ctrl     jestSlowem=True  zgloszone=1
 PROBE Alt      BezJednostek=Alt      jestSlowem=True  zgloszone=1
 PROBE Del      BezJednostek=Del      jestSlowem=True  zgloszone=1
 PROBE Ins      BezJednostek=In       jestSlowem=True  zgloszone=1
 PROBE Escape   BezJednostek=E cape   jestSlowem=True  zgloszone=1
```

Z `"Esc"` zostaje `"E c"`, czego `\p{L}{2,}` nie łapie. **Wyjątek jest osiągalny —
sito 3 wykonuje się na nim — ale BEZCZYNNY: jego zdjęcie nie zmienia wyniku dla
jedynego napisu, który wymienia.** To nie to samo, co „nieosiągalny", i nie to samo,
co „nieskanowany"; wpis 6.D130 nazwał trzecią rzecz.

Potwierdzone bramką, nie złożone z jej części — kontrola KN-2 niżej.

## Argument, który przy okazji odpadł

Przy pierwszym podejściu wpisałem do listy drugi powód, mocniejszy od pierwszego:
bez wyjątku `"Esc"` byłoby odrzucane z komunikatem „literał językowy zamiast klucza
katalogu", czyli nieprawdziwym, bo `Godot.Key` zna `Escape`, a `Esc` nie — czyli
odtworzyłaby się usterka, którą 6.D130 naprawiło.

Odrzucane nie byłoby **wcale**. `PowodOdrzucenia` woła się wyłącznie na literałach
zgłoszonych, a `"Esc"` zgłoszone nie jest ani z wyjątkiem, ani bez niego. Zdanie
o powodzie nie ma kiedy paść. Argument był nieprawdziwy z tego samego źródła, co
wejście pozycji: obie wersje zakładały, że bez wyjątku napis dojdzie do sita słowa
i je przejdzie.

## Rozstrzygnięcie: lista ZOSTAJE jako ubezpieczenie

Nie jako działający filtr — takim nie jest. Powód jest ten sam, co przy kolejności
`Jednostki` (kontrola KN-3 z 6.D115, wyszła zielona i porządek mimo to został):
mechanizm kosztuje zero, jest osiągalny i **działa dla nazwy klawisza, która słowem
zostaje** — osiem takich zmierzono wyżej.

Bezczynność akurat wpisu `"Esc"` wisi na **cudzej liście**: zdjęcie `"s"` z `Jednostki`
czyni wyjątek natychmiast działającym. Skasowany trzeba by go wtedy odtworzyć, nie
wiedząc po co.

Do tej pozycji tego wiązania nie pilnowało nic — patrz KN-3.

## Co doszło do kodu

- `WzorzecSlowa` — wzorzec `\p{L}{2,}` przeniesiony z ciała `SlowaWKodzie` do stałej,
  bo od tej pozycji pyta o niego także test. Dwie kopie rozjechałyby się cicho; ten
  sam powód, co przy `WzorzecWywolania`.
- `NazwyKlawiszyZglaszane` — osiem nazw z pomiaru wyżej. **Nie jest to lista wyjątków
  ani propozycja takiej listy**, tylko materiał pomiaru osiągalności.
- `Wyjatek_na_nazwy_klawiszy_ma_PRZEDMIOT_w_KeyNames` — każda pozycja `NazwyKlawiszy`
  ma być nazwą, którą `KeyNames` naprawdę zwraca, żeby wyjątek umarł razem ze swoim
  przedmiotem, a nie po nim. Zawieranie, a nie równość: `KeyNames` zwraca też
  „Spacja", którą bramka przepuszcza z innego powodu (`UiText.Keys`), a żądanie
  równości zrobiłoby z wyjątku drugą kopię katalogu.
- `Wyjatek_na_Esc_jest_BEZCZYNNY_a_mechanizm_jest_OSIAGALNY` — przyczyna bezczynności,
  ten sam wniosek zmierzony bramką, osiągalność na ośmiu nazwach i kontrola przyrządu.

## Kontrole negatywne

Baza: **235/235**. Po każdej `cp` z kopii i `md5sum -c: OK` na obu plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | `[Key.Escape] = "Esc"` → `"Escape"` w `KeyNames.cs` | **231/235**, cztery testy, w tym `…ma_PRZEDMIOT_w_KeyNames` | wyjątek jest związany ze swoim przedmiotem |
| KN-2 | `NazwyKlawiszy = { }` | **234/235**, JEDEN test — zapadka na długość listy | bezczynność potwierdzona bramką: `…jest_BEZCZYNNY…` **przeszedł** przy liście pustej |
| KN-3 | `"s"` zdjęte z `Jednostki` | **234/235**, tylko `…jest_BEZCZYNNY…` | wiązanie z cudzą listą jest pilnowane — i przez nic więcej |
| KN-4 | `WzorzecSlowa` → `\p{L}{3,}` | **234/235**, tylko `…jest_BEZCZYNNY…`, na `Ins` | ośmiu nazw nie da się zastąpić jedną — `Ins` leży na granicy |
| KN-5 | `WzorzecSlowa` → `\p{L}{99,}` | **231/235**, cztery testy | stała jest tą, której bramka używa; wyniesienie nie osierociło kopii |

KN-2 jest tu wynikiem, nie kontrolą przyrządu: gdyby zapalił się którykolwiek test
poza zapadką na długość, teza o bezczynności byłaby nieprawdziwa.

KN-3 jest najważniejszy i wart zdania osobno. Przed tą pozycją zdjęcie `"s"`
z `Jednostki` przechodziło całą bramkę na zielono, cicho zmieniając wyjątek
`NazwyKlawiszy` z bezczynnego w działający i zostawiając przy nim zdanie
nieprawdziwe. 234 pozostałe testy tego nie widzą **także dziś** — widzi jeden,
dopisany tutaj.

Komunikat KN-3, wklejony:

```
Assert.AreEqual failed. Expected:<E c>. Actual:<Esc>. `BezJednostek("Esc")` daje
teraz "Esc", a nie „E c” — jeśli `Jednostki` straciły „s”, wyjątek `NazwyKlawiszy`
WŁAŚNIE STAŁ SIĘ DZIAŁAJĄCY i rozstrzygnięcie 6.D142 trzeba przeczytać jeszcze raz
```

Komunikat KN-4, wklejony:

```
CollectionAssert.AreEqual failed. „Ins” przestało być zgłaszane () — wyjątek
`NazwyKlawiszy` nie miałby dla czego zostawać i argument z rozstrzygnięcia 6.D142
przestaje działać(Different number of elements.)
```

## Koszt uboczny, który zapaliła bramka z 6.D141

Spis pinów z 6.D141 jest kluczowany **numerem wiersza**, więc dopisanie dwóch testów
na końcu `UiTextTests.cs` przesunęło pięć zapisanych pozycji i zestaw stanął na ośmiu
testach — zanim cokolwiek zdążyło pójść dalej. To jest przyrząd działający zgodnie
z przeznaczeniem, nie usterka, i wart odnotowania w tę stronę: **spis policzył moją
zmianę wcześniej, niż ja ją policzyłem.**

Przeliczone i zapisane w `tools/tests/test_csharp_pins.py`:

| | przed | po |
|---|---:|---:|
| pinów napisowych w `UiTextTests.cs` | 5 | **6** |
| pinów napisowych w `tests/Game.Tests` | 44 | **45** |
| na plik (gra) | 2,75 | **2,81** |
| kategoria C (liczona, nie wpisana) | 38 | **39** |
| pinów liczbowych w `tests/Game.Tests` | 186 | **188** |
| w tym całkowitych | 82 | **84** |
| kategoria A, wiersze | 490, 496, 501 | **552, 558, 563** |
| kategoria B, wiersze | 570, 571 | **632, 633** |

Doszły: `Assert.AreEqual("E c", …)` (napisowy, kategoria C) oraz `AreEqual(0, …)`
i `AreEqual(1, …)` (całkowite). Zapadka „pin całkowity NIGDY nie ma tolerancji"
została na **zerze** po obu stronach, więc wniosek 6.D141 przeżył dopisanie dwóch
pinów całkowitych.

Opis kategorii C mówił „nazwa trybu, ścieżka, identyfikator", a nowy pin nie jest
żadną z tych rzeczy — jest wynikiem **jednej przemiany napisu**. Zdanie o kategorii
zostało dopisane razem z pinem, żeby kategoria nie rozszerzyła się po cichu.

## Czego nie zrobiono

- **Nie ruszono zakresu plików skanowanych** — `KeyNames.cs` nadal jest poza bramką.
  To jest 6.D143, wymienione wprost w polu „Poza zakresem".
- **Nie zdjęto `"s"` z `Jednostki`** ani niczego innego z tej listy. Pomiar mówi, co
  by się stało; zmiana wymagałaby własnej pozycji i własnego powodu.
- **Nie dopisano do `NazwyKlawiszy` żadnej z ośmiu zmierzonych nazw.** Żadna nie stoi
  dziś w kodzie, więc wpis byłby wyjątkiem bez przedmiotu — czyli dokładnie tym,
  przeciw czemu jest pierwszy z dopisanych testów.
- **Nie poprawiono wpisu 6.D130 w `docs/TASKS.md`.** Jego zdanie o przyczynie zieleni
  KN-4 jest nieprawdziwe; zostało obalone tutaj i tutaj jest sprostowane, a wpis
  zrobiony jest cudzym wierszem historii, którego ta pozycja nie obejmuje.

## Zauważone przy okazji, nietknięte

`Jednostki` są zbiorem zamkniętym wyprowadzonym z pomiaru w `src/Game/`, ale mają
skutek uboczny daleko poza jednostkami: zdejmują litery ze środka napisów, które
jednostkami nie są. `"Esc"` → `"E c"` i `"Escape"` → `"E cape"` to ta sama mechanika,
a różnią się wynikiem tylko dlatego, że w drugim zostają cztery litery pod rząd. Ile
napisów w `src/Game/` przechodzi dziś sito słowa **wyłącznie** dzięki temu, że
jednostka zjadła im literę, nie jest policzone.
