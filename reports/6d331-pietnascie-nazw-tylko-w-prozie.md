# 6.D331 · Tylko DZIEWIĘTNAŚCIE z pięćdziesięciu siedmiu jest stałą kodu — a piętnaście nazw nie istnieje nigdzie poza prozą, która o nich mówi

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `150c758`

6.D312 zmierzyło populację **57** nazw o kształcie ALLCAPS z podkreśleniem, padających
w prozie pod `tools/` i nieprzypisanych nigdzie pod `tools/**/*.py`, i zapisało w §10
dwa wyjątki: identyfikatory odcinków i nazwy tokenów CPythona. Blok 6.D324 wymienił
siedem nazw jako identyfikatory odcinków, a `F0_N` nim nie jest — jest kluczem
słownika o wartości `248900.0`. Ta pozycja **czyta i liczy**; niczego nie prostuje
w cudzym bloku i żadnego wzorca nie zmienia.

---

## 1. Kontrola przyrządu ZDANA — dwie nazwy, dwie różne klasy

```
   L1_A     -> ('IDENTYFIKATOR ODCINKA', 'data/track/L1_A.json')
   F0_N     -> ('KLUCZ DANYCH', 'tools/physics/reference.py')
```

Pole żądało dokładnie tego rozdzielenia i ostrzegało, że przyrząd stawiający je
w jednej klasie powtarza błąd, który ma zmierzyć. Nie stawia.

## 2. Populacja — nazwy odtworzone co do jedynki, wystąpienia NIE

```
POPULACJA  nazw: 57   wystapien: 189   [6.D312: 57 / 170]
stalych przypisanych pod tools/ (odsiane): 8859   [6.D312: 1226]
```

**Nazw jest dokładnie 57, a wystąpień o 19 więcej.** Różnicy nie uzgadniam; podaję,
czego nie liczę tak samo. Moje sito odsiewające („przypisane pod `tools/`") obejmuje
**każdą nazwę po lewej stronie przypisania oraz nazwy funkcji i klas** — stąd 8859
wobec 1226 u 6.D312, które odsiewało wyłącznie stałe. To, że przy siedmiokrotnie
szerszym sicie populacja wyszła **ta sama co do nazwy**, znaczy tylko tyle, że
nadmiarowo odsiane nazwy w prozie i tak nie padają; wystąpień liczę więcej, bo
zliczam każde trafienie kształtu w węźle prozy, także powtórzone w jednym węźle.

## 3. CZTERY KLASY — sumują się do populacji

Kolejność rozstrzygania spisałem przed pomiarem i pierwsza pasująca wygrywa:

```
   IDENTYFIKATOR ODCINKA      6
   KLUCZ DANYCH               7
   STALA KODU                19
   COS JESZCZE               25
   SUMA                      57   (populacja 57)   ZGADZA SIĘ
```

**Suma jest SPRAWDZONA, a nie założona** — i wychodzi, w przeciwieństwie do 6.D312,
gdzie cztery klasy dawały 101 przy populacji 57. Różnica nie jest zasługą: tam
klasy były **czterema niezależnymi własnościami**, tutaj są podziałem z konstrukcji,
bo rozstrzyga pierwsza pasująca. Przewidywanie Y6 trafione z tego powodu, a nie
dlatego, że drzewo się zmieniło.

**IDENTYFIKATOR ODCINKA — dokładnie sześć** (Y3 trafione): `L1_A` (37 wystąpień),
`L5_D` (11), `L1_B` (8), `L2_E` (7), `L6_F` (4), `L5_C` (1); każdy z adresem
`data/track/<nazwa>.json`. **`F0_N` wśród nich nie ma** — co potwierdza przesłankę
pozycji pomiarem, a nie cytatem.

**KLUCZ DANYCH — siedem:** `F0_N` (`tools/physics/reference.py`),
`APT_UPDATE_ATTEMPTS`, `MAX_ASERCJA`, `MAX_GALAZ_RAISE`, `NIE_Z_TEJ_RODZINY`,
`RUNNER_NAME`, `STRUKTURALNA_AST`.

**STAŁA KODU — dziewiętnaście**, z adresem poza `tools/**/*.py`: jedenaście
w workflowach i skryptach pod `tools/ci/` (`BLENDER_BIN`, `GODOT_BIN`,
`GODOT_VERSION`, `RUNNER_TOOL_CACHE`, `RUNNER_TEMP`, `DOTNET_ROOT`,
`DOTNET_INSTALL_DIR`, `METRO_TIMING_OUT`, `APT_OPTS`, `APT_INSTALL_TIMEOUT_S`,
`INSTALL_TIMEOUT_S`) i osiem w `doctor.sh` (§4).

## 4. Usterka mojego przyrządu, znaleziona przy czytaniu klasy „coś jeszcze"

Skan „przypisane poza `tools/**/*.py`" objął `*.cs` pod `src/`, `*.yml` pod
`.github/` i `*.sh` pod `tools/` — **i pominął `doctor.sh`, który leży w korzeniu
repozytorium.** Osiem nazw wpadło przez to do klasy „coś jeszcze", choć mają adres:

```
HAVE_SDK_MAJOR      doctor.sh:248     REQUIRED_TFM     doctor.sh:87
HOSTFXR_OK          doctor.sh:373     RUN_TESTS        doctor.sh:15
MBXL_DOCTOR_RUNNING doctor.sh:399     SDK_NA_DYSKU     doctor.sh:104
WYCIAG_FAILI        doctor.sh:404     SDK_NA_LISCIE    doctor.sh:198
```

Zgłaszam to, zamiast poprawić po cichu, i liczby w §3 są **już po poprawce**.
Znalazło ją czytanie klasy resztkowej, a nie żadna kontrola — dokładnie dlatego
klasę resztkową się czyta.

## 5. GŁÓWNE ZNALEZISKO: piętnaście nazw nie istnieje nigdzie poza prozą

Klasa „coś jeszcze" ma 25 nazw i pole żądało adresu przy każdej. Przeczytałem je
wszystkie. Rozpadają się na trzy rzeczy, a jedna z nich jest znaleziskiem:

| podklasa | nazw | co to jest |
|---|---|---|
| zmienna środowiskowa, CZYTANA nie przypisywana | 4 | `DOTNET_BIN` (`${DOTNET_BIN:-dotnet}`), `MBXL_WYCIAG_FAILI`, `GITHUB_ENV`, `GITHUB_TOKEN` |
| nazwa z CUDZEJ biblioteki | 6 | `FSTRING_START`, `FSTRING_MIDDLE`, `FSTRING_END` (`token`), `RUSAGE_CHILDREN` (`resource`), `BLENDER_EEVEE`, `BLENDER_EEVEE_NEXT` (Blender) |
| **nazwa istniejąca WYŁĄCZNIE w prozie** | **15** | niżej |

**Piętnaście nazw, które w tym drzewie nie mają adresu w ogóle:**

```
BUILD_DIRS · CHECKED_HASH · GAME_SOURCE_GLOB · GAME_SOURCE_SKIP · HAMOWANIA_MUTANT
INSTALL_ATTEMPTS · KOTWICA_ZABLOKOWANA · MAX_X · MAX_Y · MIN_GOLYCH_ROZNYCH
MIN_RADIUS_M · POLECENIE_KOMPILACJI · WARTOSC_W_KODZIE · WIELKIE_LITERY · WIELKIMI_LITERAMI
```

I to nie jest zaniedbanie — **część z nich jest w prozie po to, żeby powiedzieć,
że ich nie ma:**

```
test_game_needle_specificity.py:88  «6.D117: `GAME_SOURCE_GLOB` i `GAME_SOURCE_SKIP`
                                     zniknely razem z wlasna regula»
test_ci_workflows.py:289            «nazwa `INSTALL_ATTEMPTS` nie pada»
test_dead_constants.py:4            «`MIN_RADIUS_M = 20.0` stalo …» — stała MARTWA,
                                     usunięta; bramka istnieje z jej powodu
test_tree_walks.py:222              «`MAX_X >= ile`» — SZABLON reguły, nie nazwa
test_bytecode_staleness.py:26       «tryb `CHECKED_HASH`» — tryb z PEP 552
```

**To jest ten sam kształt, który 6.D322 zmierzyło jako „cytat zaprzeczony":
obecność nazwy w prozie czyta każdy skan, a jej zaprzeczenie — żaden.** Tam
dotyczyło to odsyłacza do raportu, tu nazwy stałej; w obu wypadkach zdanie mówi
„tego nie ma", a przyrząd liczy „to jest".

Przewidywanie Y2 („klasa »coś jeszcze« będzie najliczniejsza") trafione, ale
z powodu, którego nie przewidziałem: nie dlatego, że nazwy są z cudzych bibliotek,
tylko dlatego, że **proza tego repozytorium nazywa rzeczy nieistniejące częściej,
niż cytuje cudze**. Piętnaście wobec sześciu.

## 6. Ile nazw siedzi w klasie innej, niż mówi 6.D312

Pole żądało tej liczby wprost i żądało rozróżnienia, czy błąd jest pojedynczy, czy
systematyczny.

**Stałą kodu jest 19 z 57. Pozostałe 38 są czymś innym.** 6.D312 §10 nazwało dwa
wyjątki — identyfikatory odcinków i nazwy tokenów CPythona — które obejmują
**dziewięć** nazw (sześć identyfikatorów i trzy `FSTRING_*`). Wyjątki nazwane
pokrywają zatem **dziewięć z trzydziestu ośmiu**, czyli niecałą czwartą część.

**Błąd jest SYSTEMATYCZNY, nie pojedynczy** (Y4 trafione), i mówię to z liczbą:
dwadzieścia dziewięć nazw stoi w klasie, o której 6.D312 nie mówi nic. Największą
z nich jest ta z §5.

**Nie prostuję przez to ani 6.D312, ani 6.D324** — pole wyklucza to wprost, a §10
tamtej pozycji nie twierdzi, że wyjątki są kompletne; mówi tylko, że są. Ta pozycja
podaje, ile ich jest naprawdę.

## 7. Przewidywania — pięć trafionych, jedno połowicznie

| # | przewidywanie | wynik |
|---|---|---|
| Y1 | populacja odtworzy 57 / 170 co do jedynki | **połowicznie**: nazw 57 zgadza się, wystąpień 189 wobec 170 (§2) |
| Y2 | klasa „coś jeszcze" najliczniejsza | **trafione**, z innego powodu niż zakładałem (§5) |
| Y3 | identyfikatorów dokładnie sześć | **trafione** |
| Y4 | nazw w innej klasie więcej niż jedna | **trafione**: 38, z czego 29 poza wyjątkami nazwanymi |
| Y5 | co najmniej jedna nazwa bez adresu w drzewie | **trafione**: piętnaście (§5) |
| Y6 | cztery klasy zsumują się do populacji | **trafione**, z konstrukcji (§3) |

## 8. Czego świadomie nie zrobiłem

Nie tknąłem bloku 6.D312 ani 6.D324, nie zmieniłem żadnego wzorca, nie odsiałem
identyfikatorów, nie tknąłem `src/` ani `data/` — wszystko to stoi w polu „Poza
zakresem". **Nie postawiłem też bramki na klasie z §5**, choć piętnaście nazw to
dość, żeby o niej pomyśleć: zapalałaby się na zdaniu „tej stałej już nie ma",
czyli na prozie, która mówi prawdę.

## 9. Co zauważyłem przy okazji, ale nie tknąłem

`BLENDER_EEVEE` pada w `data/design/visual-style.json` jako **wartość**, nie klucz —
i jest to jedyna nazwa z populacji, która mieszka w `data/`. Moja kolejność klas
stawia ją w „cudzej bibliotece", bo tym jest; gdyby ktoś liczył „nazwy padające
w danych", wypadłaby inaczej. Zapisuję, bo to przypadek graniczny mojej własnej
kolejności rozstrzygania, a nie własność drzewa.
