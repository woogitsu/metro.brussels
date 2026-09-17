# 6.D260 — łańcuch dawnych wartości: 41 stałych, 206 ogniw, dziewięć przerwanych

**Data:** 17.09.2026 · **Gałąź:** `claude/6d260-lancuch-wartosci` · **Baza:** `abec3d5`

## 1. Skąd ta pozycja

6.D256 spędziło trzy doby nad liczbą **108**, którą odtworzenie dało przy stałej
stojącej na **116**. Odpowiedź leżała kilkanaście wierszy wyżej, w komentarzu tej
samej stałej: `108 -> 112 -> 113 -> 114 -> 116`. Sto osiem było **ostatnim ogniwem
przed łańcuchem**, a nie liczbą znikąd. Wskazówka była w tym samym pliku i nie
przeczytał jej nikt — bo łańcuchów nie czytało **nic**.

## 2. Obie liczby, których żądało pole „Wyjście"

```
stałych z łańcuchem zmian:   41   (12 w Pythonie, 29 w C#)
ogniw razem:                206   (dawnych wartości zapisanych MASZYNOWO CZYTELNIE)
```

**Kształt jest jeden po obu stronach językowych**, i to jest pomiar, a nie założenie:
`A -> B (DD.MM.RRRR, pozycja): powód`, różniący się wyłącznie znakiem komentarza
(`#` w Pythonie, `//` w C#).

**Strzałka `→` nie jest markerem łańcucha i celowo nie jest czytana.** W C# stoi
też przy mutacjach (`TrackOffsetM 2.10→0.0`), przy fizyce (`40 km/h → 506,3 MJ`)
i przy przejściach prędkości. Zmierzone: **29** wystąpień `→` w `tests/` i `src/`,
z czego łańcuchem zmian nie jest **ani jedno**.

## 3. Znalezisko, którego pozycja nie przewidywała: dziewięć łańcuchów jest przerwanych

Wartość zmieniła się bez dopisania ogniwa. Luki są duże, więc nie są artefaktem
czytnika:

Cztery po stronie Pythona, pięć w `UiTextTests.cs`. Luki, licząc od lewej strony
ogniwa do lewej strony następnego — **liczby opisują OGNIWA łańcucha, a nie dzisiejszą
wartość którejkolwiek stałej**:

* zapadka bloków szczegółów w `test_backlog.py` — skok o dwanaście między 6.D223
  a 6.D233;
* zapadka liczby raportów w `test_report_hygiene.py` — skok o szesnaście między
  6.D224 a 6.D237;
* zapadka wywołań w `test_field_paths.py` — trzy luki naraz;
* dolna zapadka igieł gry w `test_game_needle_specificity.py` — ogniwo idzie
  **w dół** między MB-02 a MB-03, przy zapadce DOLNEJ;
* pięć stałych w `UiTextTests.cs` — luka w środku łańcucha.

Jeden łańcuch jest wprost **nieaktualny**: ostatnie ogniwo stałej liczącej klucze
katalogu na ekranie w `UiTextTests.cs` niesie liczbę o dziewięć mniejszą niż sama stała.

**Bramka nie żąda ciągłości od wszystkich i to jest wybór z 6.D27**, a nie pobłażanie:
zażądanie jej dziś dawałoby dziewięć czerwieni na PRAWIDŁOWYM drzewie i bramka poszłaby
do wyłączenia. Żąda jej od tych, które ciągłe **są**; lista przerwanych stoi
w `LANCUCHY_PRZERWANE` i porównywana jest **w obie strony** (6.D243), więc przerwanie
łańcucha dziś ciągłego zapala bramkę, a naprawienie przerwanego zapala ją tak samo
i każe zdjąć wpis.

## 4. Rozstrzygnięcie: komunikat odmowy DA SIĘ rozszerzyć

Pole „Wyjście" pytało, czy komunikat da się rozszerzyć o zdanie „liczba %d stała tu
do <data>, pozycja <numer>". **Da się**, i odpowiedź jest w kodzie:
`LancuchZmian.SkadTaLiczba` po stronie C# i `dawna_wartosc` po stronie Pythona.

**Pytane są OBIE liczby, bo znaczą dwie różne rzeczy:**

* **zmierzona** będąca dawną wartością → odtworzenie mierzy korpus zamrożony na tamtym
  commicie; to jest przypadek 6.D256;
* **stała** będąca dawną wartością → ktoś cofnął zapadkę do liczby, która już tu stała.

Pierwsza wersja pytała wyłącznie o zmierzoną — i **kontrola negatywna wyszła przez
to BEZ tego zdania**, bo jej mutacja rusza stałą, nie pomiar. Poprawione po przebiegu,
nie przed.

## 5. Dwa czytniki, i to jest wybór wbrew 6.D257

6.D257 kazało szukać JEDNEGO miejsca na jedną rzecz. Tu są dwa: `LancuchZmian.cs`
czyta pliki `.cs`, `test_value_chains.py` czyta oba drzewa. Wspólnego czytnika nie da
się mieć bez wołania Pythona z testu C# albo odwrotnie.

Wspólny jest natomiast **kształt**, a bramka pythonowa sprawdza go **po obu stronach**
i ma na to własną asercję (`z_pythona and z_csharp`). Gdyby te wzorce się rozjechały,
tamta bramka przestałaby widzieć łańcuchy C# i zapaliłaby się na podłodze liczby
stałych. Zabezpieczeniem jest więc pomiar, a nie obietnica.

## 6. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Mutacje na KOPII drzewa (§4.6), `__pycache__` czyszczony (6.D102), każda z asercją,
że **wylądowała**.

### KN — obniżenie stałej do jednej z jej DAWNYCH wartości

Przewidywanie: komunikat zawiera dawną wartość **i jej datę**.

```
MUTACJA: ZgloszenWaskichWierszami 116 -> 108, wylądowała (1)

Assert.AreEqual failed. Expected:<108>. Actual:<116>. drogą wierszową wąska reguła
daje dziś 116 zgłoszeń wobec 108 z 6.D173 — odtworzenie 6.D181 mierzy wtedy inny
korpus i nie ma prawa go poprawiać. UWAGA: 108 stała tu do 14.09.2026, pozycja MB-04
— oczekiwana liczba jest DAWNĄ wartością tej samej stałej, czyli zapadka została
cofnięta do wartości, która już tu stała (6.D260)
```

To jest dokładnie zdanie, którego żądało pole „Skończone, gdy".

### Kontrola przyrządu, C# — czytnik nie odpowiada na wszystko

Cztery przypadki, każdy osobno: dawna wartość (odpowiada), **dzisiejsza wartość**
(milczy — 116 stoi wyłącznie po prawej stronie ostatniego ogniwa, więc nigdy tu „nie
stała do"), liczba spoza łańcucha (milczy), **cudza stała** (milczy). Bez tej kontroli
zdanie dopisywane do komunikatu byłoby nie do odróżnienia od zdania dopisywanego
ZAWSZE — a takie mówiłoby o każdej liczbie, że jest dawną wartością.

### Kontrola przyrządu, Python — siedem kształtów na drzewie próbnym

Łańcuch ciągły, łańcuch przerwany, stała bez ani jednego ogniwa, komentarz bez ogniwa,
strona C#, strzałka unicode (ma **nie** być łańcuchem) oraz `8 // 2` — dzielenie
całkowite w Pythonie, które przy luźniejszym wzorcu znaku komentarza byłoby czytane
jako komentarz C#.

**Kontrola padła przy pierwszym przebiegu** i złapała usterkę czytnika: wzorzec stałej
pythonowej nie łapał WARTOŚCI, więc `wartosc` było `None` dla każdej stałej pythonowej
i bramka na zgodność końca łańcucha sprawdzała **wyłącznie stronę C#**, przechodząc
na zielono nie widząc połowy drzewa. Złapała to lista wyjątków porównywana w obie strony.

## 7. Czego bramka nie zrobiła, a co złapała u mnie

**Dwie zapadki górne złapały moją własną pracę i obu nie podniosłem:**

* `MAX_GAME_UNMATCHED_NEEDLES` (48) — kontrola przyrządu miała wpisane wprost
  `"14.09.2026"` i `"MB-04"`, które dla skanu igieł są igłami bez dopasowania w `src/`.
  Zamiast podnosić zapadkę, kontrola sprawdza teraz **kształt** odpowiedzi (data
  `DD.MM.RRRR`, niepusta pozycja, pytana liczba), a konkretne wartości sprawdza strona
  pythonowa, gdzie ten skan nie sięga.
* `MAX_POGRUBIONYCH_BEZ_POKRYCIA` (175, z 6.D259) — mój własny docstring niósł pięć
  pogrubionych liczb bez pokrycia. Zdjąłem pogrubienie.

**To drugie jest zmierzoną CENĄ bramki z 6.D259 i zapisałem je jako pozycję 6.D264,
a nie obszedłem w milczeniu:** konwencja „pogrubienie znaczy liczba zmierzona" działa
tam, gdzie liczba stoi obok swojej stałej, a nie w opisie całego pomiaru. Bramka
karze więc dokładnie ten rodzaj prozy, który projekt chce pisać.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py
  2580/2580 przeszło
  RAZEM 251.595 s, 2580 testów, 131 modułów

~/.dotnet/dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 673, Skipped: 0, Total: 673

~/.dotnet/dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 319, Skipped: 0, Total: 319
```

## 9. Zauważone, nietknięte

- **Nie naprawiono żadnego z dziewięciu przerwanych łańcuchów.** Dopisanie brakujących
  ogniw wymaga przejścia historii gita dla każdej stałej osobno i jest osobną pracą;
  pole „Poza zakresem" tej pozycji zabrania zresztą przepisywania samych łańcuchów.
- **Stała licząca klucze katalogu na ekranie ma łańcuch nieaktualny** i to jest
  jedyny przypadek, w którym rozjazd nie bierze się ze słownika. Stoi w
  `KONIEC_INNY_NIZ_WARTOSC` z powodem nazywającym go wprost.
- **Nowy moduł poruszył czternaście zapadek w całym drzewie** — od liczby modułów
  (130 → 131) przez rozkład sześciu postaci literału po liczbę asercji C#. Żadna
  z nich nie jest zapadką GÓRNĄ podniesioną; dwie górne, które zapaliły, zgasiłem
  poprawiając kod, a nie próg.
