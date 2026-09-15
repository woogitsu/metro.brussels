# 6.D225 — dziura interpolacji jest kodem, a maska zasłaniała ją razem z napisem

**15.09.2026**, na `6ad172a`. Wejście: `tools/tests/test_dead_constants_csharp.py`,
`tools/tests/csharp_test_methods.py`, `src/**/*.cs`, `tests/**/*.cs`.

## 1. Co weszło

- **`tools/tests/csharp_test_methods.py`** — `dziury_interpolacji(source)`, publiczny
  czytnik zakresów kodu w dziurach interpolacji, idący **tym samym** `_przebieg`, co
  `maska` i `klasy_literalow`.
- **`tools/tests/test_dead_constants_csharp.py`** — `maska_z_dziurami`, `martwe()`
  czytające na niej, `UZASADNIONE` z powrotem **puste**, sześć nowych testów
  i podłoga `MINIMUM_DZIUR`.
- Zapadki: `MINIMUM_DZIUR` w rejestrze, `ASERCJI_NAPISOWYCH_RAZEM`, proza o rejestrze.

## 2. Obie liczby, o które pyta pozycja

**Stałych, które skan uznawał za nieczytane: 1.** `CzlonWyrazenia`
w `tests/Game.Tests/UiTextTests.cs`.
**Z nich czytanych wyłącznie przez interpolację: 1**, czyli **wszystkie**. Po poprawce
`martwe()` zwraca **pusty słownik**, a `UZASADNIONE` wraca do pustej — nie dlatego, że
wpis usunięto, tylko dlatego, że **zniknął powód, dla którego istniał**.

Populacja, na której to zmierzono, jest dzisiejsza i różni się od liczb wpisanych
w blok pozycji: **389 deklaracji** o **340 różnych nazwach** w **148** czytanych
plikach `.cs`. (6.D232 mierzyło 385/336 dziewięć commitów wcześniej; drzewo ruszyło.)

## 3. Rozkład dziur po postaciach literału — trzecia rzecz, o którą pyta pozycja

| postać literału | literałów | dziur | z klamrą, która dziurą NIE jest |
|---|---:|---:|---:|
| zwykły | 5939 | 0 | 104 |
| interpolowany (`$`) | 1263 | 2037 | 5 |
| werbatim (`@`) | 88 | 0 | 24 |
| surowy interpolowany (podwójny dolar) | 14 | 69 | **14** |
| surowy | 9 | 0 | 8 |
| werbatim interpolowany (`$@`) | 7 | 10 | 0 |

Dziur razem: **2116**. Podłoga `MINIMUM_DZIUR` **1800**, klasa WOLNA.

**Kolumna trzecia jest tu treścią, a nie ozdobą.** Klamrę, która dziurą nie jest, niosą
**wszystkie czternaście** literałów o przedrostku podwójnego dolara — tam pojedyncza
klamra jest zwykłym znakiem. Ostrzeżenie z pola „Czego NIE wolno przyjąć bez pomiaru"
jest więc potwierdzone co do sztuki: wzorzec dopisujący `{NAZWA}` bez liczenia dolarów
trafiłby w każdą z nich.

## 4. Czy poszerzenie daje trafienia FAŁSZYWE — zmierzone, nie oszacowane

Wzorzec naiwny (`{nazwa}` w **każdym** literale) daje odczyt dla **16 nazw**, dla
których odczytu nie ma: `case`, `if`, `return`, `var`, `void`, `get`, `DoorPhase`,
`Ending`, `L`, `_windowM`, `blok`, `komentarz`, `surowy`, `werbatim`, `Alfa`, `x`
— w większości z fragmentów C# **cytowanych w napisach zwykłych** w plikach testowych.
**Żadna z tej szesnastki nie jest dziś zadeklarowana jako stała**, więc werdykt bramki
by się nie zmienił. To jest dokładnie powód, dla którego ta szesnastka jest groźna,
a nie niegroźna: każda z tych nazw to stała, której bramka **by nie zgłosiła**, gdyby
kiedyś taką nazwę dostała, a sygnału o tym nie byłoby żadnego.

Potwierdza to KN-5 niżej: przy wzorcu naiwnym **jedyną czerwienią są dwie kontrole
syntetyczne**, a bramka na drzewie przechodzi.

## 5. Rozstrzygnięcie

**Skan poszerzony, `UZASADNIONE` wraca do pustej.** Wpis na liście opisywałby granicę
**skanera** jako właściwość **stałej** — a to jest ta pomyłka, którą 6.D27 każe wyłączać,
a nie hodować. Czytnik jest **pożyczony**, nie przepisany (6.D213): `dziury_interpolacji`
chodzi tym samym `_przebieg`, którym chodzi `maska`, więc mówi o tym, co maska naprawdę
zasłania, a nie o moim wyobrażeniu o niej.

## 6. Dwie granice nazwane, a nie przemilczane

**Specyfikator formatu wchodzi jako odczyt.** W `$"{Lambda:yyyy}"` część za dwukropkiem
nie jest kodem, a czytnik oddaje z niej `yyyy`. Odcięcie było rozważone i **odrzucone**:
ucięty fragment to identyfikator mniej, czyli stała mogłaby wyjść na martwą, choć jest
czytana — a bramka zapalająca się na poprawnym kodzie zostaje wyłączona, nie poprawiona.
Cena zmierzona: specyfikatory dają **16 różnych** tokenów (`F0`–`F9`, `E3`, `E6`, `R`,
`D4`, `P0`, `yyyy`, `MM`, `dd`, `e`) i **ani jeden** nie jest dziś zadeklarowany jako
stała.

**Cudzysłów w dziurze literału NIE-surowego urywa literał, i ta granica jest ODZIEDZICZONA
po `maska`, a nie wniesiona dziś.** W `$"{slownik["Ksi"]}"` (legalne od C# 11) `_przebieg`
kończy literał na cudzysłowie wewnątrz dziury, więc reszta wiersza idzie u niego jako kod.
Przed 6.D225 `maska` oddawała z tej próbki dokładnie to samo `Ksi`. Zmierzone
15.09.2026: w `src/` i `tests/` jest **55** takich literałów, prawie wszystkie
z `string.Join("…")` w dziurze. Poprawka należy do `_przebieg`, nie do tego skanu.

## 7. Kontrole negatywne — pięć, każda z przewidywaniem PRZED przebiegiem

| | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | `dziury_interpolacji` zwraca `[]` | 4 czerwone, w tym bramka na drzewie | **10/14, dokładnie te cztery** |
| KN-2 | czytnik ślepy na liczbę dolarów | tylko próbka `$$`; drzewo nic | **13/14, tylko próbka** |
| KN-3 | bez reguły ucieczki `{{` | tylko próbka `{{Delta}}` | **13/14, tylko próbka** |
| KN-4 | treść dziury bez drugiej maski | tylko próbka z napisem w dziurze | **13/14, tylko próbka** |
| KN-5 | każda postać niesie dziurę | 2 kontrole syntetyczne; drzewo nic | **12/14, tylko syntetyczne** |

Rzeczywiste wyjścia:

```
KN-1  FAIL test_dziura_interpolacji_jest_kodem_a_reszta_literalu_nie: interpolowany:
        z 'var a = $"x{Alfa}y";' czytnik widzi [], a ma widziec ['Alfa']
      FAIL test_every_unread_csharp_constant_is_justified: ... CzlonWyrazenia
        (tests/Game.Tests/UiTextTests.cs)
      FAIL test_stala_czytana_WYLACZNIE_przez_interpolacje_nie_jest_zglaszana
      FAIL test_the_gate_sees_the_interpolation_holes_it_is_supposed_to_see:
        skan widzi 0 dziur interpolacji przy progu 1800
      10/14 przeszło

KN-2  FAIL ...: surowy z dwoma dolarami: POJEDYNCZA klamra to zwykly znak:
        czytnik widzi ['Epsilon'], a ma widziec []
      13/14 przeszło

KN-3  FAIL ...: podwojna klamra jest uciekniete, nie dziura:
        z 'var a = $"x{{Delta}}y";' czytnik widzi ['Delta'], a ma widziec []
      13/14 przeszło

KN-4  FAIL ...: napis W DZIURZE nie jest odczytem: czytnik widzi ['Ni'], a ma widziec []
      13/14 przeszło

KN-5  FAIL ...: bez dolara nie ma dziury w ogole: czytnik widzi ['Theta'], ma widziec []
      FAIL test_klamra_w_literale_NIE_interpolowanym_nie_jest_odczytem: {}
      12/14 przeszło
```

**KN-2 i KN-5 są najcenniejsze i mówią to samo zdanie z dwóch stron:** obie mutacje
przechodzą na **całym drzewie** i zapalają **wyłącznie** próbki syntetyczne. Gdyby tego
modułu nie było, obie te usterki weszłyby do repozytorium na zielono — a poszerzenie
skanu przestałoby odróżniać dziurę od napisu, nie mówiąc o tym ani słowem.

Przywrócenie po każdej mutacji sprawdzone `md5sum -c` na kopii wziętej **przed** serią,
nie na wersji z indeksu — patrz §10.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_dead_constants_csharp.py
  14/14 przeszło

python3 tools/tests/test_all.py
  2497/2497 przeszło,  RAZEM 246.724 s, 2497 testów, 126 modułów

dotnet test tests/Sim.Tests
  Passed! - Failed: 0, Passed: 662, Skipped: 0, Total: 662

dotnet test tests/Game.Tests
  Passed! - Failed: 0, Passed: 318, Skipped: 0, Total: 318
```

## 9. Zapadki

- **`MINIMUM_DZIUR` 1800** — nowa, klasa WOLNA, wpisana do rejestru w
  `tools/tests/test_tree_walks.py` w tym samym commicie. Bez niej oślepiony czytnik dziur
  jest **dziś zielony**: martwych nie przybywa, bo żadna stała nie wychodzi przez to na
  martwą. KN-1 pokazała to wprost.
- **`ASERCJI_NAPISOWYCH_RAZEM` 889** (było 886) — trzy nowe asercje, wszystkie stoją
  na ZACHOWANIU: pytają, czy nazwa stałej jest w wyniku `martwe()` na wstrzykniętym
  drzewie, a nie o brzmienie komunikatu.
- **Rejestr zapadek: 55** (było 54), rozkład **17/3/34/1** (było 17/3/33/1).
- `MINIMUM_DEKLARACJI` **200** — bez zmiany, i to jest rozstrzygnięcie 6.D232, którego
  ta pozycja nie rusza.

## 10. Czego świadomie nie zrobiłem

- **Nie usunąłem żadnej stałej** — pole „Poza zakresem" tego zabrania, a po poprawce
  nie ma już czego usuwać.
- **Nie tknąłem `maska`.** Poszerzenie dotyczy wyłącznie skanu martwych stałych; gdyby
  `maska` przestała zasłaniać dziury, zmieniłoby to wynik **każdej** bramki czytającej
  na masce, a żadna o to nie prosiła.
- **Nie tknąłem `POSTACIE_LITERALU`** (pomiar 6.D200, domknięty) ani strony Pythona
  (`test_dead_constants.py` — osobny skan, osobna populacja).
- **Nie poprawiłem granicy z §6** (cudzysłów w dziurze literału nie-surowego), choć
  dotyczy **55** miejsc w drzewie. Leży w `_przebieg`, czyli w czytniku wspólnym dla
  wszystkich bramek — to osobna pozycja, nie przypis do tej.

## 11. Co zauważyłem przy okazji, ale nie tknąłem

- **`_tresc_poza_csharp(root)` ignoruje własny argument `root`.** Bierze `POZA_CSHARP`,
  zbudowane z bezwzględnych ścieżek liczonych od `ROOT`, więc przebieg po drzewie
  wstrzykniętym czyta mimo to `.tscn`, `.sh` i `.yml` **z prawdziwego repozytorium**.
  Dziś nie szkodzi, bo próbki mają nazwy własne, ale kontrola przyrządu opiera się
  na tym, że nazwa nie trafi się przypadkiem w prawdziwym drzewie.
- **Klon tej sesji był płytki (50 commitów) i to samo w sobie dawało czerwień.**
  `test_every_constant_quoted_in_a_report_carries_the_value_from_the_code` zapaliło się
  na `reports/martwe-pole-wzorca-sciezek.md`, bo datowanie twierdzenia czyta historię
  gita, a w płytkim klonie jej nie ma — komunikat mówił to wprost („klon płytki albo
  commit graniczny"). Po `git fetch --unshallow` (962 commity) bramka jest zielona
  bez żadnej zmiany w drzewie. Workflowy tego pilnują
  (`test_wszystkie_workflowy_biora_PELNA_historie`), ale środowisko agenta — nie.
- **`_dziury_w_literale` i `_rozbior_prefiksu` są prywatne, a `dziury_interpolacji`
  jest jedynym wołającym** — dziś nazwa opisuje zasięg poprawnie. Wpisuję to tylko
  dlatego, że rodzina tej uwagi już w kolejce stoi.
