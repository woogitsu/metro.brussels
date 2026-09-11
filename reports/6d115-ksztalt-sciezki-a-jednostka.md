# 6.D115 — kształt ścieżki, a nie obecność ukośnika

**Zmierzone 11.09.2026 na:** `69a3d4f`, kontener tej sesji.
**Przyrząd:** `tests/Game.Tests/UiTextTests.cs` (`SciezkaWezla`, `Jednostki`,
`SlowaWKodzie`), `src/Game/UI/Hud.cs` — czytany, nietknięty; zrzuty skryptowe Godota
4.7.2 mono, `--view=cab --no-geometry`, 1280×720.

---

## 1. Usterka i jej jedyny dzisiejszy przypadek

`SlowaWKodzie` pomijało **każdy** literał zawierający `/`, nazywając go ścieżką węzła
sceny. Pod tę regułę wpadał też literał z `Hud.Update`. Po zawężeniu odsiania do
kształtu ścieżki skan zgłosił dokładnie jeden literał w całym `src/Game/`:

```
Assert.AreEqual failed. Expected:<0>. Actual:<1>. w `Hud.cs` stoi literał językowy
zamiast klucza katalogu: "{speedKmh,6:F1} km/h     a = {accelerationMps2,6:F2} m/s²"
```

Wpis kolejki przewidywał dokładnie ten jeden przypadek i pomiar go potwierdził —
w tej serii rzadkość, bo zwykle liczba z wpisu się nie odtwarza.

## 2. Rozstrzygnięcie: literał zostaje w kodzie, a bramka uczy się jednostek

Pole „Wyjście" dopuszcza dwa wyjścia: do katalogu albo z wypisanym powodem. Literał
**zostaje w kodzie**, a powód jest taki: 6.D99 postawiło granicę katalogu na SŁOWACH,
a 6.D83 zapisało w polu „Skończone, gdy", że **jednostki i formaty liczb zostają**.
Ten literał nie niesie ani jednego słowa — niesie dwie dziury interpolacji z formatem,
symbol `a` i jednostki `km/h` oraz `m/s²`. Wpuszczenie go do katalogu znaczyłoby, że
tłumacz może zmienić liczbę miejsc po przecinku.

Dlaczego więc bramka go dotąd nie zgłaszała bez odsiania ukośników? **Bo reguła
„słowo to dwie litery pod rząd" przepuszczała jednostki wyłącznie przez przypadek:**
`m` i `s` są jednoliterowe. `km` nie jest. Stąd zamknięty zbiór `Jednostki`,
zdejmowany przed pytaniem „czy to słowo" — wyprowadzony z pomiaru z §1, a nie
z wyobraźni.

Kształt ścieżki węzła: segmenty rozdzielone `/`, każdy identyfikator
(`^[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)+$`). `Panel/Rows/Speed` przechodzi,
`Prędkość/godzinę` i `Panel/Rows Prędkość` — nie.

## 3. Dlaczego kontrola idzie na wejściu syntetycznym

Na dzisiejszym `src/Game/` obie reguły — dawna („jest ukośnik") i dzisiejsza („ma
kształt ścieżki") — dają ten sam werdykt dla **wszystkiego poza jednym literałem**.
Kontrola na samym drzewie nie odróżniłaby więc jednej od drugiej; sześć wejść
syntetycznych odróżnia, po trzy na każdą stronę reguły.

## 4. KN-3 wyszła ZIELONA i mój własny komentarz był nieprawdziwy

Komentarz przy `Jednostki` twierdził, że kolejność „najdłuższe najpierw" jest
konieczna, bo inaczej z `km/h` zostałby wiszący `/h`. Kontrola negatywna z odwróconą
kolejnością wyszła **229/229, zielona**: `/h` ma jedną literę i pytania „czy to słowo"
i tak nie przechodzi. **Żadne dzisiejsze wejście obu kolejności nie odróżnia.**

Komentarz jest przepisany i mówi dziś, ile jest wart: porządek zostaje jako
ubezpieczenie, bo kosztuje zero, a przy jednostce, której zdjęcie zostawiłoby dwie
litery pod rząd, zacząłby być potrzebny. Skoro jednak jest wyborem, jest też
sprawdzalny — doszła asercja, że tablica jest uporządkowana malejąco po długości.
**KN-3b, ta sama mutacja po dopisaniu asercji, jest czerwona.**

To ta sama rodzina co zielone kontrole w 6.D103, 6.D105, 6.D110 i 6.D111: zdanie
w komentarzu mówiło o zabezpieczeniu, którego kod nie potrzebował.

## 5. Wypis HUD-u co do bajtu

Trzy przebiegi skryptowe, ten sam kadr kabiny:

```
$ xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
    --path src/Game -- --shot=$SP/hud_$km.png --at-chainage=$km --view=cab --no-geometry

km=300    ba915e3ecb2d7eb14fa712d0cdc35228
km=900    88cb4fd443113fc4eb8b4b70ad5f4404
km=2500   f126b3604533f1163a52e9eaf676b36c
```

**Te trzy sumy są identyczne z zapisanymi w `reports/6d99-slowo-a-napis-na-klawiszu.md`**,
czyli z pomiarem sprzed tej pozycji i sprzed kilkunastu scaleń. Zdanie „wypis nie
drgnął" jest tu więc mocniejsze, niż żąda pole „Skończone, gdy": nie drgnął nie tylko
wobec stanu sprzed tej zmiany, ale wobec baseline'u 6.D99.

Jest to zresztą spodziewane i warto to powiedzieć wprost, żeby nikt nie wziął tego za
dowód czegoś więcej: **ta pozycja zmienia wyłącznie plik testowy**. `src/Game/` jest
nietknięty, więc zrzut nie miał jak się zmienić. Wartość tego pomiaru polega na tym,
że potwierdza właśnie to — a nie na tym, że coś odkrywa.

## 6. Kontrole negatywne

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | odsianie wraca do „jest ukośnik" | 228/229 |
| KN-2 | jednostki przestają być zdejmowane | **227/229, dwa testy** |
| KN-3 | kolejność jednostek odwrócona | **229/229 ZIELONA** |
| KN-3b | ta sama mutacja po dopisaniu asercji o porządku | 228/229 |
| KN-4 | kształt ścieżki rozluźniony do `^[^/]*/[^/]*$` | **227/229, dwa testy** |

**KN-4 warta zdania:** rozluźnienie do „cokolwiek/cokolwiek" zapala nie tylko kontrolę
syntetyczną, ale i bramkę na `Hud.cs` — bo literał prędkości wraca wtedy pod odsianie,
dokładnie jak przed tą pozycją. Kontrola mierzy więc to, co ma: **kształt**, a nie sam
fakt zawężenia.

## 7. Weryfikacja

```
$ dotnet test tests/Game.Tests
  Passed!  - Failed: 0, Passed: 229          (było 228)

$ python3 tools/tests/test_all.py
  2254/2254 przeszło, 120 modułów
```

## 8. Czego nie zrobiłem

- **Nie dodałem drugiego języka i nie zmieniłem brzmienia żadnego napisu** — pole
  „Poza zakresem" wyklucza oba wprost. Ta pozycja rozstrzyga, co jest ścieżką.
- **Nie ruszyłem `src/Game/`** ani jednym znakiem: usterka była w bramce, nie w kodzie
  gry.
- **Nie rozszerzyłem `Jednostki` o jednostki, których w drzewie nie ma** (`kW`, `kN`,
  `‰`). Zbiór jest zamknięty i wyprowadzony z pomiaru; dopisywanie na zapas jest tym
  samym, przed czym broni komentarz przy regule identyfikatorów silnika.

## 9. Zauważone przy okazji

- **`m` i `s` w tablicy jednostek nie robią nic** i to jest świadome: jednoliterowe
  symbole i tak nie przechodzą pytania „dwie litery pod rząd". Stoją tam, żeby tablica
  była listą JEDNOSTEK, a nie listą „jednostek, które akurat psują regułę" — ale nic
  ich nie pilnuje i usunięcie ich nie zapaliłoby niczego.
- **Odsianie po kształcie przepuści ścieżkę węzła z cyfrą w segmencie**
  (`Panel/Rows2`), bo cyfra po literze jest częścią identyfikatora — ale **nie**
  przepuści `Panel/2`, bo segment zaczynający się cyfrą identyfikatorem nie jest.
  Godot dopuszcza taką nazwę węzła; dziś żadna scena jej nie ma.
