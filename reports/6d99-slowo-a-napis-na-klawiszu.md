# 6.D99 — trzydzieści osiem segmentów językowych poza katalogiem, i granica, na której się zatrzymały

**Zmierzone 10.09.2026 na:** `3b896d2`, kontener tej sesji.
**Przyrząd:** `dotnet test tests/Game.Tests` (`UiTextTests`, `DriverActionsTests`,
`EmergencyBrakeTests`), przebieg skryptowy Godota z `--shot` (sumy MD5 klatek),
`git worktree` na `3b896d2` dla pinu z drugiego drzewa,
`tools/tests/test_game_needle_specificity.py`, `python3 tools/tests/test_all.py`.

---

## 1. Co było policzone, a co przepisane z wpisu

Wpis 6.D99 mówi: „Liczbę miejsc i słów pozycja ma policzyć z drzewa, a nie przepisać
z tego zdania". Policzone, i wpis mylił się w dwóch miejscach.

Przyrząd stoi w `UiTextTests` i jest ten sam, którym 6.D83 pilnuje `Hud.cs` — drugi
czytnik tych samych literałów rozjechałby się po cichu. **Segment** to spójny kawałek tekstu literału POMIĘDZY dziurami
interpolacji; segment jest **językowy**, gdy niesie dwie litery pod rząd. Ta definicja
odsiewa jednoliterowe jednostki (`m`, `s`) i formaty (`F1`, `+0.00;-0.00;0.00`),
a zostawia słowa — łącznie z dwuliterowym „za".

| jednostka | segmenty ogółem | językowe | przeniesione | zostały, bo nie są słowem |
|---|---|---|---|---|
| `FirstRun.StationLine` + `Faza` + `HelpLine` | 25 | 25 | 25 | 0 |
| `src/Game/Input/DriverActions.cs` | 17 | 9 | 9 | 7 nazw akcji `InputMap` + „Esc" |
| `src/Game/Input/EmergencyBrake.cs` | 4 | 4 | 4 | 0 |
| **razem** | **46** | **38** | **38** | **8** |

Po zmianie: **zero** segmentów językowych w tych jednostkach, katalog urósł
z **2** do **29** kluczy, a 38 segmentów zmieściło się w **27** wpisach — bo segment
jest kawałkiem zdania, a wpis całym zdaniem.

**Pierwsza pomyłka wpisu: `HelpLine` nie ma ani jednego słowa.** Wpis wymienia ją obok
`StationLine` i `Faza`. Metoda ma jeden wiersz i wybiera między
`DriverActions.HelpWhenTheCoreDrives` a `DriverInput.Help`; słowa, o które chodzi, stoją
w `DriverActions`, czyli w innej pozycji tej samej listy. Metoda została w bramce
(`MetodyFirstRun` wymienia trzy), żeby dopisanie do niej napisu zapaliło się od razu.

**Druga pomyłka wpisu: fazy drzwi jest siedem, nie osiem.** Wpis mówi „osiem faz drzwi
po polsku". `DoorPhase` ma siedem wartości; ósme ramię `switch` to `_ => phase.ToString()`
i nazwy po polsku nie ma z definicji — dla wartości spoza wyliczenia nie byłoby czego
wpisać do katalogu. Ramię zostało nietknięte.

## 2. Granica: SŁOWO kontra NAPIS NA KLAWISZU

Osiem segmentów zostało w kodzie i to jest rozstrzygnięcie, nie niedokończenie.

Siedem to nazwy akcji `InputMap` (`driver_power`, `view_toggle`, …) — identyfikatory
silnika, nie zdania. Ósmy to `"Esc"`.

Nazwa klawisza mówi, co jest **wytłoczone na klawiszu**, a nie co program chce
powiedzieć. Dla nazw jednoliterowych ma to pokrycie w bramce:
`DriverActionsTests` (`DriverActionsTests.cs:164`) porównuje `binding.KeyName` z
`PhysicalKeycodes[0]` dla każdego wiązania o nazwie jednoznakowej — pięć z siedmiu.
„Esc" pod tę pętlę nie wchodzi (trzy znaki) i nie wchodziłoby też z katalogu, więc
przeniesienie nie kupiłoby niczego, a dołożyłoby wpis, którego tłumacz mógłby dotknąć.

**`"Spacja"` poszła do katalogu i to jest ta sama reguła, nie wyjątek od niej.** Na
klawiszu Esc napisane jest „Esc". Na spacji nie jest napisane nic — „Spacja" to polski
rzeczownik, którym o tym klawiszu mówi się po polsku, i po francusku brzmiałby inaczej.
Stała `EmergencyBrake.KeyName` przestała przez to być `const`; sprawdzone, że nikt nie
używa jej w miejscu wymagającym stałej kompilacji (jedyne użycia to argument konstruktora
rekordu i porównania w testach).

## 3. Wypis co do znaku — dwa różne dowody, bo dwa różne rodzaje wierszy

### 3.1 Wiersze widoczne na ekranie — zrzut

Trzy przebiegi skryptowe Godota, ten sam kadr kabiny przed i po zmianie:

```
$ xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
    --path src/Game -- --shot=$SP/hud_$km.png --at-chainage=$km --view=cab --no-geometry

          przed (3b896d2)                    po
km=300    ba915e3ecb2d7eb14fa712d0cdc35228   ba915e3ecb2d7eb14fa712d0cdc35228
km=900    88cb4fd443113fc4eb8b4b70ad5f4404   88cb4fd443113fc4eb8b4b70ad5f4404
km=2500   f126b3604533f1163a52e9eaf676b36c   f126b3604533f1163a52e9eaf676b36c
```

Klatka jest identyczna bajt w bajt, więc wiersz pozycji, wiersz stacji i wiersz pomocy
brzmią co do znaku tak samo.

### 3.2 Wiersze, których zrzut nie pokazuje — pin z drugiego drzewa

Zrzut nie pokazuje wiersza hamulca awaryjnego (klawisz nie jest trzymany) ani wiersza
pomocy dla `--line`. Te trzy napisy pinuje nowy test
`Wiersze_zlozone_z_katalogu_brzmia_co_do_znaku_tak_jak_przed_przenosinami`, z oczekiwaną
treścią **wpisaną z ręki** — bo porównanie z napisem złożonym z tego samego katalogu nie
sprawdziłoby niczego.

Sam zielony pin dowodzi tylko, że napis równa się temu, co wpisałem. **Kontrola: ten sam
plik testu, bez zmiany ani jednego znaku, uruchomiony na drzewie SPRZED przeniesienia**
(`git worktree add --detach … HEAD`, plik skopiowany jako `PinCoDoZnaku.cs`):

```
Passed!  - Failed: 0, Passed: 1, Skipped: 0, Total: 1 — MetroBxl.Game.Tests.dll (net10.0)
```

Pin przechodzi po obu stronach, więc trzy napisy są identyczne przed i po.

## 4. Trzy usterki, które ta zmiana znalazła u siebie

Wszystkie trzy zapaliły się przy pierwszym uruchomieniu rozszerzonej bramki i żadna
nie została zauważona z lektury.

**4.1 „Nikt nie woła" znaczyło „nie patrzę tam".** `UiTextTests` czytało wywołania
katalogu wyłącznie z `Hud.cs`. Pierwszych 27 kluczy wołanych z `FirstRun` i z `Input/`
było dla testu **martwych** — i test miał rację, bo pytał o zły plik. To jest ta sama
rodzina, co przyrząd meldujący sprawdzenie, którego nie zrobił: wąska rodzina plików
zamienia zdanie o programie w zdanie o jednym pliku, nie mówiąc o tym. Skan czyta dziś
całe `src/Game/` bez `.godot/` i bez samego `UiText.cs` (wpis nie jest wołającym).

**4.2 Klucz schowany za `?:` jest dla skanu niewidoczny.** Pierwsza wersja pisała
`UiText.Get(warunek ? "hud.traction.free" : "hud.traction.locked")`. Skan czyta literał
WPROST po `UiText.Get(`, więc zobaczył 27 wywołań zamiast 29, a oba klucze zgłosił jako
martwe. Naprawą jest **pokazanie wywołania** (dwie gałęzie, każda ze swoim `Get`), a nie
poszerzenie wzorca o składnię C#. Ślepa plamka zostaje, ale zapala się GŁOŚNO — jako
martwy klucz — a nie po cichu.

**4.3 Skan czytał nazwy zmiennych z wnętrza dziur interpolacji.**
`$"{binding.KeyName} {binding.Meaning}"` nie niesie ani jednego słowa dla człowieka,
a bramka zgłosiła go jako polszczyznę. `Hud.cs` przechodził dotąd przypadkiem: jego
jedyny taki literał zawiera `/` (`m/s²`) i wpadał pod odsianie **ścieżki węzła sceny**.
Dziury są dziś wycinane przed sprawdzeniem słowa (`BezDziur`), a że wycinają dziury,
a nie tekst wokół nich, sprawdzają dwie asercje na wejściu syntetycznym.

## 5. Zapadka igieł: 19 → 21, z powodem

`MAX_GAME_UNMATCHED_NEEDLES`, podniesiona o dwie. Nowe igły to `koniec bloku`
i `wyrażeniowa` z kontroli przyrządu
`Wycinanie_ciala_metody_bierze_te_metode_a_nie_nastepna`: obie asertują na **wejściu
syntetycznym** — na napisie złożonym w samym teście, który udaje dwie metody C#.
Komunikatem `src/Game` nie są i być nie mają; gdyby się dopasowały, znaczyłoby to, że
próbka przypadkiem powtarza zdanie z programu, a wtedy kontrola mierzyłaby co innego,
niż mówi.

**Trzymania igły w zmiennej nie użyto, choć ominęłoby zapadkę.** Bramka pomija igłę ze
zmiennej (zawężenie 3 jej docstringa), więc `var x = "koniec bloku";` zdjąłby obie
pozycje z licznika bez śladu w diffie. To jest dokładnie zamiana niejednoznaczności na
niewidzialność, przed którą szczebel trzeci ma bronić.

Pozostałe progi tej bramki po zmianie: komunikatów **149** (było 150, próg 142) —
jeden ubył, bo `"prowadzi rdzeń: " + … + " nie działają"` było grupą sklejeń, a jest
jednym szablonem; igieł **54** (było 52, próg 45); plików **21** (próg 18).
Pięć igieł, które dotąd trafiały w komunikaty przenoszonych plików
(`HAMULEC AWARYJNY`, `SŁUŻBOWY`, `nie ma osobnego stopnia`, `hamulec awaryjny`,
`chainage_m`), trafia dalej — tekst przeniósł się do `UiText.cs`, a rodziną jest całe
`src/Game/`.

## 6. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` kopii na bok i `md5sum -c` po przywróceniu; żadna przez
`git checkout <plik>`.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | zdjęcie z katalogu używanego klucza `hud.door.checking` | **2 testy czerwone**: `Kazdy_klucz_wolany_z_warstwy_gry…` („`FirstRun.cs` woła klucz `hud.door.checking`, którego katalog (pl) nie zna") i `W_wyczyszczonych_metodach_FirstRun…` |
| KN-2 | słowo `"wybieg"` wpisane z powrotem wprost w `DriverActions` | **3 testy czerwone**, w tym `W_plikach_sterowania…` z nazwą literału i `Katalog_nie_ma_wpisow_martwych` z osieroconym `input.coast` |
| KN-3 | wpis `hud.nikt-nie-wola`, którego nikt nie woła | **1 test czerwony**: `Katalog_nie_ma_wpisow_martwych` |

Po każdej: `md5sum -c` → `OK`.

Kontrola dodatnia dla samego skanu stoi w
`Skan_literalow_widzi_te_ktore_sa_i_nie_bierze_sciezki_wezla_za_slowo`: odsianie
identyfikatorów silnika odsiewa `driver_power`, `view_toggle`, `font_size` i `Esc`,
a NIE odsiewa `koniec przejazdu` ani `od nowa`. Bez drugiej połowy reguła „to
identyfikator" mogłaby zjeść cały werdykt i zostawić go zielonym z niewiedzy.

Dolne ostrza na sam skan: **29** wywołań w **4** plikach. Literówka we wzorcu daje pustą
listę, a pusta lista przechodzi pętlę bez ani jednego sprawdzenia.

## 7. Czego świadomie nie zrobiłem

- **Drugiego języka nie ma i niczego nie przetłumaczyłem.** Pole „Poza zakresem" mówi to
  wprost; katalog ma jeden język i jest domyślnym.
- **Siedmiu literałów zastępczych w scenie nie tknąłem** — to tekst dla edytora.
- **`Hud.cs` odsiewa literały ze znakiem `/` jako „ścieżkę węzła sceny"** i to odsianie
  przepuszcza też `"{…} km/h     a = {…} m/s²"`, czyli napis ze słowem. Zapaliło się to
  przy 4.3 jako powód, dla którego usterka dziur nie została zauważona w 6.D83.
  Nie ruszam: `Hud.cs` jest poza wejściem tej pozycji, a zawężenie odsiania to zmiana
  w bramce, o którą nikt nie prosił. **Zauważone i nietknięte.**
- **Formatów liczb nie wpuściłem do katalogu.** `F1`, `F0`, `F2` i
  `+0.00;-0.00;0.00` zostają w kodzie — ta sama granica, co w 6.D83. Format powtarzał
  się w dwóch wariantach wiersza drzwi i dostał jedną stałą
  (`FirstRun.BladZatrzymaniaFormat`), a nie dwa wpisy.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- `DriverActionsTests` porównuje `binding.KeyName` z kodem fizycznym **tylko dla nazw
  jednoznakowych** (`KeyName.Length == 1`). „Esc" i „Spacja" nie są przez nic związane
  z `project.godot`: zmiana `"Esc"` na `"Escape"` nie zapali dziś żadnej bramki.
  Dla „Spacji" katalog dokłada dwie (brak klucza, martwy wpis); dla „Esc" — żadnej.
- `UiText.Format` przyjmuje `params object?[]`, więc `int` idzie do niego bez
  formatowania. Dla `InvariantCulture` daje to ten sam napis, ale granica „liczby
  formatuje wołający" jest w tym miejscu zapisana, a nie wymuszona.
