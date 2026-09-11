# 6.D121 — pięć punktów README wobec drzewa: dwa zdania były nieprawdą, nie jedno

**Zmierzone 11.09.2026 na:** `91aa730`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_readme_claims.py` (`osie_plaskie`,
`wymiary_stacji_z_zalozenia`, `wezly_skladu_w_scenie`, `wymiary_kabiny_z_zalozenia`,
`dlugosc_pakietow_m`), `data/track/*.json`, `data/network/station-depths.csv`,
`tools/track/station_components.py`, `tools/blender/m7_cab.py`,
`src/Game/Scenes/FirstRun.tscn` — wszystkie dane wyłącznie do czytania.

---

## 1. Pozycja spodziewała się jednego fałszu. Są dwa, i trzeci punkt zestarzał się w locie

Pole „Skąd" tej pozycji wskazuje **jedno** zdanie znane jako nieprawdziwe: „pierwsza
stacja typowa (T-212) jest dopiero w planie". Pomiar wobec dzisiejszego drzewa daje
**dwa** zdania nieprawdziwe i **jedno** przeterminowane o dobę:

| punkt | co mówił | co jest w drzewie | werdykt |
|---|---|---|---|
| profilu pionowego | „**Cały** tunel jest wariantem `flat-preview` na Z = 0" | 6.D120 (#513, `91aa730`) dodało wariant `partial-vertical`; odcinek Parc↔Arts-Loi ma rzędne z rejestru | **przeterminowane o jeden dzień** |
| stacji jako brył | „pierwsza stacja typowa (T-212) jest **dopiero w planie**" | T-212 scalone jako #137 (`fe14d72`), `tools/track/station_components.py` w drzewie | **nieprawda** |
| wielu składów W SCENIE | „Scena pokazuje **jeden**" | 1 węzeł `TrainView` w `FirstRun.tscn` | prawda, bez zmian |
| kabiny i wnętrz | „Nie ma ich **ani w geometrii**, ani w scenie" | 6.D119 (#512, `4b00e35`) postawiło `tools/blender/m7_cab.py` | **nieprawda w połowie** |
| ciągłego kilometrażu linii | 34 481 m pakietów, 4034 m przerw | suma z plików: 34 480,6 m → 34 481 m | prawda, liczba druga niesprawdzalna |

Dwa fałsze mają **wspólną przyczynę i to jest wynik tej pozycji**: oba zdania opisywały
brak, którego fałszyfikatorem była **nazwa pliku, jeszcze nie wybrana**. 6.D104 zapisało
to wprost w `POWODY_BEZ_WPISU` — „fałszyfikatorem byłaby NAZWA, której dziś nie ma" —
i uznało, że dlatego wpisu mieć nie można. Obie nazwy powstały w ciągu następnej doby:
`station_components.py` był już w drzewie, gdy 6.D104 to pisało (stąd werdykt „nieprawda"),
a `m7_cab.py` doszedł dzień później. **Zdanie, którego nie pilnuje nic, starzeje się
dokładnie w tempie, w jakim projekt rośnie** — a ten projekt rośnie o jedną pozycję dziennie.

## 2. Co zostało przepisane i czym jest teraz uzasadnione

Każda zmiana treści punktu ma liczbę z drzewa, i **ta liczba stoi w README**, a nie tylko
w bramce — inaczej README byłby znowu stroną, której nikt nie liczy.

| punkt | liczba w README | skąd liczona |
|---|---|---|
| profilu pionowego | „Wszystkie **sześć** osi" | `osie_plaskie()` — pliki `data/track/*.json` ze `status = not_modelled` i wszystkimi Z = 0 |
| stacji wynikających z danych | „**18** wymiarów jako `design_assumption`" | `len(SC.DESIGN_ASSUMPTIONS)` |
| wielu składów W SCENIE | „Scena pokazuje **jeden**" | `wezly_skladu_w_scenie()` — węzły ze skryptem `src/Game/World/TrainView.cs` w scenie |
| wnętrza kabiny w scenie | „**24** jej wymiary" | `len(CAB.DESIGN_ASSUMPTIONS)` |
| ciągłego kilometrażu linii | 34 481 m nie stoi w prozie | `dlugosc_pakietow_m()` — suma `length_m` sześciu osi |

Dwa punkty zmieniły też **tytuł**, bo tytuł jest tezą zdania, a obie tezy przestały być
prawdziwe: „stacji jako brył" → „stacji wynikających z danych" (bryły SĄ, danych nie ma),
„kabiny i wnętrz" → „wnętrza kabiny w scenie" (kabina jest, wnętrza w scenie nie ma).
Punktów jest nadal **pięć**; pola „Poza zakresem" tej pozycji — zakaz dopisywania nowych
punktów i ruszania `ZAPRZECZENIA` — nie naruszono.

## 3. Nowa bramka: liczba wypisana w README musi być liczbą liczoną z drzewa

`test_the_true_absence_claims_still_match_the_numbers_in_the_tree` porównuje drzewo
z wartością zapisaną **w module testowym**. Jest więc ślepa na zmianę samego README:
przerobienie „18 wymiarów" na „19" nie rusza ani `station_components.py`, ani tabeli
`POMIARY_BRAKOW`, więc zestaw zostaje zielony. To jest dokładnie ta dziura, przez którą
README twierdził „41 plików `.cs`" przy czterdziestu czterech.

Stąd `test_every_number_the_section_prints_is_the_number_the_tree_counts`: każdy wpis
`POMIARY_BRAKOW` niesie czwarte pole — wzorzec, którym liczba wyjmuje się **z tekstu
tego jednego punktu** (cięcie po myślnikach, żeby „18" z jednego punktu nie zaliczało
się drugiemu). Cyfra i liczebnik obsłużone tym samym słownikiem `NUMERALS`, który moduł
miał już na liczbę workflowów.

Wpis bez wzorca (`None`) jest legalny i znaczy „ta liczba w README nie stoi": 34 481 m
jest w gałce bramki, a w prozie nie — wpisanie jej tam zrobiłoby z README **drugą kopię
tej samej wiedzy**, czyli tę usterkę, przeciw której cały ten moduł powstał. Żeby „None
wszędzie" nie wyciszyło bramki, test liczy porównane pary i żąda, by było ich tyle, ile
wpisów ze wzorcem, i nie mniej niż cztery (KN-6 niżej).

## 4. Tabela powodów opustoszała — i to jest miejsce, w którym łatwo o zieloną ciszę

`POWODY_BEZ_WPISU` miała dwa wpisy i oba zniknęły, bo oba punkty dostały pomiar. Pętla
`test_each_written_reason_says_why_the_table_cannot_hold_the_entry` po pustym słowniku
jest **zielona, nie sprawdziwszy niczego** — ta sama rodzina, którą projekt tropi od
6.D27 i którą 6.D80 zmierzył na pustej białej liście statusów.

Zamknięte gałęzią, która zamiast milczeć **asertuje powód pustki**: skoro powodu nie ma
ani jednego, pomiar musi mieć każdy z pięciu punktów. KN-9 to przybija: zdjęcie jednego
wpisu z `POMIARY_BRAKOW` przy pustych powodach daje komunikat z nazwą osieroconego punktu,
a nie ciszę.

Mechanizm powodu pisanego **zostaje** — jest pełnoprawnym rozstrzygnięciem i następny
punkt sekcji może go potrzebować. Pusty słownik to stan, nie usunięcie.

## 5. Czego pomiar punktu o kabinie NIE obejmuje

`wymiary_kabiny_z_zalozenia` pilnuje **połowy** zdania — tej o wymiarach. Druga połowa,
„scena nie ma węzła wnętrza", zostaje **niepilnowana** i to jest świadome, nie przeoczone:

* jej fałszyfikatorem jest węzeł o nazwie, której nikt jeszcze nie wybrał — bramka na
  zgadniętej nazwie milczy tym ciszej, im lepiej ktoś nazwie węzeł inaczej;
* licznik po WSZYSTKICH zasobach `FirstRun.tscn` zapalałby się na każdym dodanym drzewie
  i słupku, czyli na zmianie bez skutku dla zdania.

Zapisane w komentarzu przy `POWODY_BEZ_WPISU`, żeby nie trzeba było tego odkrywać
z samego kodu. To jedyne miejsce sekcji, które dziś nie ma przyrządu.

## 6. Druga liczba punktu o kilometrażu nadal jest niesprawdzalna — i README to teraz mówi

4034 m przerw międzypakietowych pochodzi z kształtów GTFS (`001m` v1, `005m` v1, `002m` v2,
`006m` v2), a te w repozytorium nie leżą: `data/network/shapes-manifest.json` wskazuje
zdalny `zip`. 6.D104 §5 ustaliło, że najbliższy istniejący przyrząd — `endpoint_gaps` —
mierzy co innego (dziewięć par końców, 8760,4 m) i podpięcie go pod to zdanie byłoby
wiązaniem zdania z liczbą, która go nie dotyczy.

Liczba zostaje, bo nie jest nieprawdą; **zmienia się jej opis**: README mówi teraz wprost,
że ta jedna liczba jest spoza repozytorium i żadna bramka jej nie sprawdza. Liczba
sprawdzana i niesprawdzana wyglądały w tym akapicie identycznie, a to jest ta sama forma
usterki co reszta tej pozycji — tyle że o jeden poziom wyżej.

## 7. Kontrole negatywne — WYKONANE, nie opisane

Każda przez `cp` czterech plików na bok i `md5sum -c` po przywróceniu (nigdy
`git checkout`), z `__pycache__` czyszczonym **przed każdym** przebiegiem — procedura
z 6.D102.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | README: „18 wymiarów" → „19" | **10/11**, nowa bramka |
| KN-2 | README: „24 jej wymiary" → „25" | **10/11**, nowa bramka |
| KN-3 | README: „sześć osi" → „siedem" (liczebnik, nie cyfra) | **10/11**, nowa bramka |
| KN-4 | `DESIGN_VOID_MARGIN_M`, zdjęty z tabeli założeń stacji | **9/11**, dwa testy |
| KN-5 | punkt wraca do tytułu „stacji jako brył" | **8/11**, trzy testy |
| KN-6 | wszystkie cztery wzorce ustawione na `None` | **10/11**, „porównano 0 liczb" |
| KN-7 | `wymiary_kabiny_z_zalozenia` czyta moduł stacji | **8/11**, trzy testy |
| KN-8 | punkt dostaje naraz pomiar i powód | **10/11** |
| KN-9 | pusta tabela powodów i punkt bez pomiaru | **9/11**, w tym gałąź pustki |
| KN-10 | `m7_cab` importuje `bpy`, przebieg samego modułu | **0/0**, FAIL importu |
| KN-10b | to samo, ale z atrapą `bpy` w `sys.modules` | **28/29**, asercja AST |

Po każdej: `md5sum -c` → `OK` na wszystkich czterech plikach.

**Ani jedna nie wyszła zielona** i to jest tutaj informacja, a nie oczywistość: pięć
kontroli z ostatnich dziesięciu pozycji tej sesji wychodziło zielono i za każdym razem
znaczyło to, że bramka pilnuje mniej, niż deklaruje. KN-6 i KN-9 były pisane właśnie
pod ten scenariusz — obie celują w pustkę, jedna w pustą listę wzorców, druga w pusty
słownik powodów — i obie są czerwone, więc pustka w tym module jest dziś słyszalna.

## 7a. Kontrola, która złapała MOJĄ WŁASNĄ asercję na tej samej usterce

Pomiar wymiarów kabiny wymaga, żeby `tools/blender/m7_cab.py` dał się zaimportować
**bez Blendera** — bramka README chodzi też tam, gdzie `bpy` nie ma. Pierwsza wersja
tej kontroli brzmiała:

```python
assert "bpy" not in sys.modules
```

i **przechodziła w przebiegu tego jednego modułu, a padała w pełnym zestawie**. Powód
jest zmierzony, nie wydedukowany: `test_blender_cli.py`, `test_detail_markers.py`
i `test_marker_gates.py` wstawiają **atrapę** `bpy` do `sys.modules`, więc asercja
mówiła o stanie CAŁEGO przebiegu, a nie o tym, co wciągnął import kabiny. Przyrząd
meldował sprawdzenie, którego nie zrobił — ta sama rodzina co 6.D27, tym razem
napisana w tym samym commicie, który ją tropi.

Zamknięte pomiarem **ze źródła**: `ast.parse` po `m7_cab.py` i zbiór nazw z `Import`
oraz `ImportFrom`. Dwie kontrole, bo mechanizm jest dwuczęściowy:

* **KN-10** — `import bpy` dopisany do modułu, przebieg samego `test_readme_claims.py`:
  `0/0` i FAIL importu. Kontrola czerwona, ale **nie przez moją asercję** — moduł
  w ogóle się nie ładuje. To jest stan maszyny bez Blendera i on chroni sam z siebie.
* **KN-10b** — ten sam `import bpy`, ale przebieg `test_detail_markers.py`
  + `test_readme_claims.py`, czyli z atrapą już w `sys.modules`: `28/29`, i pada
  **dokładnie ta asercja**, wypisując `importy: ['bpy', 'json', 'm7_layout']`.

Bez KN-10b zostałaby w drzewie asercja czerwona z dwóch powodów naraz, z których jeden
jest przypadkowy — i nie byłoby wiadomo, czy pilnuje czegokolwiek w przebiegu, w którym
naprawdę chodzi, czyli w pełnym zestawie.

## 8. Czego nie zrobiłem

* **Nie dopisałem szóstego punktu** i nie tknąłem `ZAPRZECZENIA` — oba wprost w polu
  „Poza zakresem".
* **Nie zmieniłem ani jednego pliku w `data/`** (§4.6). Wszystkie liczby są czytane.
* **Nie podpiąłem 4034 m pod `endpoint_gaps`** — powód w §6, ten sam co w 6.D104 §5.
* **Nie zbudowałem geometrii ani nie renderowałem**: ta pozycja nie tworzy zasobu 3D,
  więc pętla weryfikacji geometrii (§5) jej nie dotyczy. Weryfikacją jest zestaw.
* **Nie ruszyłem `docs/21-measured-vs-assumed.md`**, do którego sekcja odsyła — 18 i 24
  wymiary są tam opisane od 6.D119 i zgadzają się z tym, co teraz mówi README.
