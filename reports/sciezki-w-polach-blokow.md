# 6.D32 — ścieżka w polu bloku a plik, który w drzewie jest

**Zmierzone 07.09.2026 na commicie:** `2ffb0b00cce5a66d688647ccb603c1011416aa6f`
(`origin/main`, scalenie #386). Bramka: `tools/tests/test_field_paths.py`.

**O ZAPISIE ŚCIEŻEK W TYM RAPORCIE.** Ścieżki, których w drzewie NIE MA, stoją tu
**bez grawisów** — i to nie jest niekonsekwencja zapisu, tylko warunek postawiony przez
inną bramkę: `tools/tests/test_report_hygiene.py` żąda, żeby każda ścieżka w grawisach
w `reports/` rozwiązywała się w drzewie, a jego lista wyjątków jest pusta i ma taka
zostać. Raport o nieistniejących ścieżkach nie może więc ich cytować tak samo jak
istniejące. W blokach kodu grawisów nie ma wcale, więc wklejone wyjścia pomiaru są
dosłowne.

## 1. Co zmierzono

Skan trzech pól — „Wejście", „Wyjście", „Weryfikacja" — we wszystkich **111** blokach
`##### <numer> · …` z `docs/TASKS.md`. Cięcie pola takie samo, jak w
`tools/tests/test_backlog.py` (`missing_fields`) i `tools/tests/backlog_commands.py`
(`verification_field`): pole kończy się na następnym punkcie listy `- **…:**`.
Zgodność z tym drugim jest sprawdzana testem, nie założona.

| pole | ścieżek | nieistniejących | z tego USTEREK |
|---|---|---|---|
| „Wejście" | **442** | 2 | **2** |
| „Wyjście" | **45** | 2 | 0 |
| „Weryfikacja" | **191** | 3 | **1** |
| RAZEM | **678** | 7 | **3** |

678 to WYSTĄPIENIA; unikalnych trójek `(blok, pole, ścieżka)` jest **647** — ta sama
ścieżka bywa w bloku wymieniona dwa razy. Progi KW stoją na wystąpieniach.

Blok 6.D32 zapisał pomiar z `a4a3975`: **101** bloków, **387 / 40 / 149** ścieżek,
**dwie** usterki. Te liczby są tu **przeliczone, a nie przepisane**, bo od tamtego
pomiaru doszło dziesięć bloków — i przeliczenie znalazło **trzecią** usterkę, tej samej
rodziny co dwie znane.

## 2. Trzy usterki i ich poprawka

1. **6.B5**, pole „Wejście": cytowało tools/track/profile_scan.py, a plik leży
   w `tools/blender/profile_scan.py`. Katalog `tools/track/` istnieje i zawiera
   siedemnaście innych modułów, więc ścieżka wygląda sensownie i przeżyła przegląd.
2. **6.A30**, pole „Weryfikacja": komenda `replay --keys` wołała
   data/keys/L1_A-manual.json, a katalogu `data/keys` nie ma w drzewie **wcale**.
   Zapisy wejść leżą w `tests/data/`; poprawione na `tests/data/manual-keys.log`,
   czyli na plik, którym `--keys` wołają wszystkie trzy bramki odtworzenia
   w `.github/workflows/godot-first-run.yml`. Tę ścieżkę znalazł niezależnie agent
   wykonujący 6.A30 i zapisał w sekcji „zauważone" swojego wiersza.
3. **6.D35**, pole „Wejście": cytowało tests/Sim.Tests/MetroBxl.Sim.Tests.csproj,
   a plik nazywa się `tests/Sim.Tests/Sim.Tests.csproj`. `MetroBxl.Sim.Tests` jest
   wartością `<AssemblyName>` i `<RootNamespace>` **w tym pliku** (wiersze 14 i 15),
   więc pomyłka jest dokładnie tej samej klasy co dwie wyżej: nazwa się zgadza,
   miejsce nie.

   **Tej trzeciej nie było w pomiarze z bloku** i jest poprawiona dlatego, że szczebel 1
   bramki nie dopuszcza wyjątku — nie było jak jej obejść, nie łamiąc pola „Wyjście"
   tej pozycji. Blok 6.D35 jest odhaczony, ale poprawiane jest wyłącznie jego pole
   „Wejście"; cytat wyjścia `grep` w polu „Skąd" tego samego bloku, który tę samą
   ścieżkę zawiera, **zostaje nietknięty** — to pomiar z datą, a pola „Skąd" ta bramka
   świadomie nie obejmuje (§7).

## 3. Cztery ścieżki POPRAWNE — one wyznaczają kształt bramki

Cztery z siedmiu nieistniejących ścieżek są poprawne, każda z innego powodu. Bramka
„każda ścieżka musi istnieć" zgłasza je wszystkie: **cztery zgłoszenia poprawne na
trzy usterki**, czyli 57 % szumu w pierwszym przebiegu. Taka bramka zostaje wyłączona
w tym samym tygodniu (6.D27), a wyłączona jest gorsza niż żadna, bo zostawia po sobie
przekonanie, że coś było sprawdzane.

| rodzaj | blok, pole | ścieżka | dlaczego poprawna |
|---|---|---|---|
| (a) | 6.B44 „Wyjście" | tools/track/vertical_profile.py | plik, który pozycja ma **wytworzyć** |
| (a) | 6.B8 „Wyjście" | tools/tests/test_test_track_fixture.py | to samo; pozycja odhaczona w 5.8 pod inną nazwą |
| (b) | 6.B44 „Weryfikacja" | tools/track/vertical_profile.py | ten sam plik w **komendzie, która go tworzy** |
| (c) | 6.B39 „Weryfikacja" | tools/nie-ma-takiego-pliku.py | ścieżka **celowo** nieistniejąca — o jej brak w teście chodzi |

## 4. Bramka: trzy szczeble

1. **Pole „Wejście" — twardy błąd, BEZ WYJĄTKU MOŻLIWEGO DO DOPISANIA PO CICHU.** To
   jest adres, pod który idzie następny agent. Brak wyjątku nie jest przeoczeniem:
   `test_the_exception_list_stays_closed` sprawdza, że żaden klucz `EXCEPTIONS` nie
   dotyczy tego pola, więc dopisanie się tam jest widoczną zmianą asercji, a nie jedną
   linijką w słowniku. Kontrola KD-3 niżej to WYKONUJE.
2. **Pole „Weryfikacja" — nieistnienie przyjmowane tylko wtedy**, gdy ten sam plik stoi
   w polu „Wyjście" **tego samego** bloku (rodzaj b) albo ma wpis na liście wyjątków
   z powodem (rodzaj c). „Tego samego bloku" jest istotne: plik z „Wyjścia" bloku X nie
   usprawiedliwia komendy w bloku Y, i to jest sprawdzone na wejściu syntetycznym
   (blok 9.Z3), bo w dzisiejszym drzewie taka para nie występuje.
3. **Pole „Wyjście" — nieistnienie jest stanem normalnym** (rodzaj a). Reguła jest ta
   sama co dla szczebla 2 i dla tego pola wypada tożsamościowo. Nie jest to jednak
   pusty przebieg i ma to dwa mierzone skutki: pole liczy się do progu KW, i **karmi
   szczebel 2** — zbiór „Wyjścia" bloku jest jedynym, co odróżnia 6.B44 od 6.A30,
   bo obie ścieżki nie istniały identycznie.

Lista wyjątków ma dziś **jeden** wpis (6.B39) przy zapadce **1**; zapadkę wolno tylko
obniżać, a stać wyżej niż lista nie może.

## 5. Kontrole — WYKONANE

### 5.1 KD — kontrola dodatnia: literówka w polu „Wejście"

Wiersz 2899, blok 6.D25: `tools/tests/test_all.py` -> tools/tests/test_al.py. Przebieg
CAŁEGO zestawu, żeby pokazać, że czerwienieje **dokładnie nowa bramka**, a nie cokolwiek
innego:

```
  FAIL test_no_input_field_names_a_file_outside_the_tree: pole „Wejście" nazywa plik, którego w drzewie nie ma: ['6.D25 „Wejście": tools/tests/test_al.py']
  FAIL test_removing_the_field_distinction_moves_the_reported_set: ['6.D25 „Wejście": tools/tests/test_al.py']
  1941/1943 przeszło
EXIT=1
```

Dwa zgłoszenia, oba z `test_field_paths.py`; ani jeden inny moduł ze 102 nie drgnął.
Drugie jest poprawne i celowe: `test_removing_the_field_distinction_moves_the_reported_set`
żąda, żeby bramka rozróżniająca pola zgłaszała **zero**.

### 5.2 KD-2 i KD-3 — czy tę literówkę da się UCISZYĆ wpisem na liście wyjątków

Ta sama literówka **plus** wpis `("6.D25", "Wejście", …)` z powodem dłuższym niż 40
znaków, czyli dokładnie ta droga, którą wyjątek robi się tańszy od poprawki:

```
  FAIL test_no_input_field_names_a_file_outside_the_tree: pole „Wejście" nazywa plik, którego w drzewie nie ma: ['6.D25 „Wejście": tools/tests/test_al.py']
  FAIL test_removing_the_field_distinction_moves_the_reported_set: ['6.D25 „Wejście": tools/tests/test_al.py']
  FAIL test_the_exception_list_stays_closed: lista wyjątków urosła do 2 przy zapadce 1 — zła ścieżka ma dostać poprawkę, a nie miejsce na liście: ['6.D25 „Wejście": tools/tests/test_al.py']
  9/12 przeszło
```

KD-3: to samo, ale z zapadką podniesioną razem z wpisem (`MAX_EXCEPTIONS = 2`), czyli
z zamkniętą jedyną furtką, którą KD-2 zapaliła:

```
  FAIL test_no_input_field_names_a_file_outside_the_tree: pole „Wejście" nazywa plik, którego w drzewie nie ma: ['6.D25 „Wejście": tools/tests/test_al.py']
  FAIL test_removing_the_field_distinction_moves_the_reported_set: ['6.D25 „Wejście": tools/tests/test_al.py']
  FAIL test_the_exception_list_stays_closed: wyjątek dla pola „Wejście": ['6.D25 „Wejście": tools/tests/test_al.py'] — to pole jest adresem, pod który idzie następny agent, i wyjątku nie ma
  9/12 przeszło
```

Szczebel 1 zgłasza ścieżkę w obu przypadkach — wpis na liście nie ma na niego wpływu
żadnego, bo `accepted()` wychodzi na `False` przed spojrzeniem na wyjątki.

### 5.3 KU — kontrola ujemna: cztery poprawne ścieżki i zdjęcie rozróżnienia pól

Inwentarz **przed** poprawką trzech ścieżek (bramka dopięta, `docs/TASKS.md` jeszcze
nietknięty):

```
  Wejście       442 ścieżek  2 nieistniejących  2 zgłoszonych  (próg 420)
  Wyjście        45 ścieżek  2 nieistniejących  0 zgłoszonych  (próg 40)
  Weryfikacja   191 ścieżek  3 nieistniejących  1 zgłoszonych  (próg 180)
  RAZEM         678

  nieistniejące, z wyrokiem:
    6.A30 „Weryfikacja": data/keys/L1_A-manual.json            ZGŁOSZONA (szczebel 2)
    6.B39 „Weryfikacja": tools/nie-ma-takiego-pliku.py         przyjęta: wyjątek z powodem (rodzaj c)
    6.B44 „Weryfikacja": tools/track/vertical_profile.py       przyjęta: komenda, która go tworzy (rodzaj b)
    6.B44 „Wyjście": tools/track/vertical_profile.py           przyjęta: plik do wytworzenia (rodzaj a)
    6.B5 „Wejście": tools/track/profile_scan.py                ZGŁOSZONA (szczebel 1, bez wyjątku)
    6.B8 „Wyjście": tools/tests/test_test_track_fixture.py     przyjęta: plik do wytworzenia (rodzaj a)
    6.D35 „Wejście": tests/Sim.Tests/MetroBxl.Sim.Tests.csproj ZGŁOSZONA (szczebel 1, bez wyjątku)

  ZGŁOSZONYCH z rozróżnieniem pól:      3
  ZGŁOSZONYCH bez rozróżnienia pól:     7
```

Inwentarz **po** poprawce:

```
  Wejście       442 ścieżek  0 nieistniejących  0 zgłoszonych  (próg 420)
  Wyjście        45 ścieżek  2 nieistniejących  0 zgłoszonych  (próg 40)
  Weryfikacja   191 ścieżek  2 nieistniejących  0 zgłoszonych  (próg 180)
  RAZEM         678

  nieistniejące, z wyrokiem:
    6.B39 „Weryfikacja": tools/nie-ma-takiego-pliku.py         przyjęta: wyjątek z powodem (rodzaj c)
    6.B44 „Weryfikacja": tools/track/vertical_profile.py       przyjęta: komenda, która go tworzy (rodzaj b)
    6.B44 „Wyjście": tools/track/vertical_profile.py           przyjęta: plik do wytworzenia (rodzaj a)
    6.B8 „Wyjście": tools/tests/test_test_track_fixture.py     przyjęta: plik do wytworzenia (rodzaj a)

  ZGŁOSZONYCH z rozróżnieniem pól:      0
  ZGŁOSZONYCH bez rozróżnienia pól:     4
```

**Zdjęcie rozróżnienia pól przenosi zbiór zgłoszeń: 3 -> 7 przed poprawką, 0 -> 4 po.**
Blok 6.D32 przewidywał 2 -> 6 przy 101 blokach; różnica to trzecia usterka i dziesięć
nowych bloków. Liczba ścieżek nie zmieniła się ani o jedną (678 przed i po), bo każda
z trzech poprawek prowadzi do pliku, który wzorzec nadal widzi — poprawka, po której
ścieżka wypada ze skanu, byłaby ucieczką z pomiaru, nie poprawką.

Kontrola przeprowadzona też przez KOD, a nie tylko przez wypis: `accepted()`
z `return False` wstrzykniętym na pierwszej linii (czyli bramka „każda ścieżka musi
istnieć") na drzewie PO poprawce:

```
  FAIL test_no_verification_field_names_a_file_outside_the_tree_and_outside_its_own_output: pole „Weryfikacja" woła plik, którego nie ma i którego pozycja nie tworzy: ['6.B39 „Weryfikacja": tools/nie-ma-takiego-pliku.py', '6.B44 „Weryfikacja": tools/track/vertical_profile.py']
  FAIL test_removing_the_field_distinction_moves_the_reported_set: ['6.B39 „Weryfikacja": tools/nie-ma-takiego-pliku.py', '6.B44 „Weryfikacja": tools/track/vertical_profile.py', '6.B44 „Wyjście": tools/track/vertical_profile.py', '6.B8 „Wyjście": tools/tests/test_test_track_fixture.py']
  FAIL test_the_three_kinds_of_exception_are_told_apart_on_synthetic_input: 
  9/12 przeszło
```

Zgłoszone są dokładnie te cztery ścieżki, o których §3 mówi, że są poprawne. To jest
cała treść tej kontroli: **wyjątki mierzą coś, a nie milczą, bo nic ich nie dotyczy.**

### 5.4 KW — kontrola wzorca: zepsuty wzorzec ma zapalić próg, nie zielone zero

Ostatni segment ścieżki zawężony do `[Q]`:

```
  FAIL test_the_scan_sees_the_measured_number_of_paths_in_every_field: wzorzec złapał 0 ścieżek w polu „Wejście", a 07.09.2026 było ich 420 — spadek znaczy zepsuty wzorzec albo zepsute cięcie pola, nie posprzątane bloki
  3/12 przeszło
```

KW-2 — **dlaczego próg jest PER POLE, a nie łączny.** Literówka w nazwie jednego pola
(`Wyjscie` bez ogonka), czyli awaria, która zabiera ze skanu 45 ścieżek z 678 (6 %):

```
  FAIL test_the_scan_sees_the_measured_number_of_paths_in_every_field: wzorzec złapał 0 ścieżek w polu „Wyjście", a 07.09.2026 było ich 40 — spadek znaczy zepsuty wzorzec albo zepsute cięcie pola, nie posprzątane bloki
  9/12 przeszło
RAZEM 633 z 678; Wyjscie: 0
```

Próg łączny musiałby stać powyżej 633, żeby to zauważyć — czyli tuż pod stanem
faktycznym, gdzie zapalałby się przy pierwszym domkniętym bloku. Trzy progi per pole
łapią awarię, przy której łączny nie drgnąłby.

### 5.5 KP — pułapka kolejności alternatywy rozszerzeń

Wzorzec z `cs` przed `csproj` i `csv` oraz `json` przed `jsonl`, bez domknięcia
`(?![A-Za-z0-9])`, dopasowuje rozszerzenie do PRZEDROSTKA dłuższego i produkuje tokeny,
których nie ma w drzewie. Zmierzone na tych samych 111 blokach, oba wzorce obok siebie:

```
dobry wzorzec: 647 wystapien, nieistniejacych 4
ZLY wzorzec:   647 wystapien, nieistniejacych 9

tokeny, ktore ZLY wzorzec produkuje, a dobry nie (i ktorych nie ma w drzewie):
   6.A31    Wejście      src/Sim.Runner/Sim.Runner.cs                   istnieje=False
   6.B21    Wejście      src/Sim/Sim.cs                                 istnieje=False
   6.B44    Wejście      data/network/station-depths.cs                 istnieje=False
   6.B44    Weryfikacja  data/network/station-depths.cs                 istnieje=False
   6.D35    Wejście      tests/Sim.Tests/Sim.Tests.cs                   istnieje=False
```

Bramka na złym wzorcu zgłaszałaby więc **pięć wystąpień (cztery różne pliki) usterek,
których nie ma**, na drzewie, gdzie prawdziwych jest zero — i wszystkie pięć w polu
„Wejście", czyli na szczeblu bez prawa do wyjątku. Ostatni z nich, tests/Sim.Tests/Sim.Tests.cs,
pojawia się dopiero po poprawce z §2.3: `Sim.Tests.csproj` jest krótszy niż
`MetroBxl.Sim.Tests.csproj`, ale ucina się identycznie. Pilnuje tego
`test_the_extension_alternation_is_ordered_longest_first`, z asercją także na to, że
zły wzorzec NAPRAWDĘ ucina — bez niej „poprawka kolejności" byłaby twierdzeniem
o niczym.

Po każdej z sześciu kontrol plik był przywracany i zgodność sprawdzana `cmp`-em:

```
cmp: TASKS.md przywrocony bit w bit
cmp OK po KU
cmp OK po KW-2
```

## 6. Liczby zestawu

```
przed:  RAZEM 71.256 s, 1931 testów, 101 modułów   ->  1931/1931 przeszło, kod 0
po:     RAZEM 69.288 s, 1943 testów, 102 modułów   ->  1943/1943 przeszło, kod 0
```

Doszedł **jeden** moduł (`tools/tests/test_field_paths.py`) i **dwanaście** testów.
Liczba bloków szczegółów nie zmieniła się (**111**), więc `MINIMUM_DETAIL_BLOCKS`
w `tools/tests/test_backlog.py` zostaje na 111.

Weryfikacja z pola bloku, oba polecenia:

```
$ python3 tools/tests/test_all.py
  1943/1943 przeszło
  RAZEM 69.288 s, 1943 testów, 102 modułów
EXIT=0

$ python3 tools/tests/test_all.py test_backlog.py
  26/26 przeszło
  RAZEM 0.944 s, 26 testów, 1 modułów
EXIT=0
```

## 7. Czego świadomie NIE zrobiłem

* **Nie sprawdzam, czy komenda z pola „Weryfikacja" działa.** To jest 6.D33 i osobny
  pomiar — pole „Poza zakresem" tej pozycji mówi to wprost.
* **Nie obejmuję pól „Skąd" ani „Zależy od".** Tam plik bywa cytowany jako historia,
  a nie jako wejście; objęcie ich zamieniłoby bramkę w zakaz cytowania czegokolwiek
  usuniętego. Granicę pilnuje `test_the_scan_reads_only_the_three_fields_that_promise_a_file`,
  z asercją także na to, że wzorzec te ścieżki ZNAJDUJE — pominięcie jest decyzją
  o zakresie, nie skutkiem tego, że wzorzec ich nie widzi.
* **Nie wymagam, żeby ODHACZONA pozycja miała już plik ze swojego „Wyjścia".** Ta reguła
  wyglądałaby mocniej i była pierwszym pomysłem na szczebel 3; jest odrzucona **na
  podstawie pomiaru, nie z ostrożności**. Jedyne jej dzisiejsze zgłoszenie byłoby
  zgłoszeniem tekstu poprawnego: 6.B8 jest odhaczone jako „ZROBIONE — i to nie w tej
  pozycji, tylko w 5.8", a plik tools/tests/test_test_track_fixture.py pod tą nazwą nie
  powstał nigdy. Bramka zapalająca się na jedynym trafieniu, i to fałszywym, to 6.D27.
* **Nie ruszam globów** (`.github/workflows/*.yml`, `tools/tests/test_*.py`). Glob nie
  jest plikiem i „nie istnieje" nie jest o nim zdaniem prawdziwym; wypada ze wzorca sam,
  bo ostatni segment musi zaczynać się od znaku słowa.
* **Nie poprawiam cytatu `grep` w polu „Skąd" bloku 6.D35**, choć zawiera tę samą złą
  ścieżkę. Jest to cytowane wyjście polecenia z datą, a takich się nie przelicza
  (`CLAUDE.md` §5, `docs/04-conventions.md`) — patrz §8.1.
* **Nie dotykam `PATH_EXCEPTIONS`** w `tools/tests/test_report_hygiene.py`. Lista jest
  pusta i ma pozostać; ścieżki nieistniejące zapisałem w tym raporcie bez grawisów.

## 8. Zauważone przy okazji, NIETKNIĘTE

1. **Cytat `grep` w polu „Skąd" bloku 6.D35 nie mógł dać pokazanego wyjścia.** Wiersz
   `$ grep -c Godot tests/Sim.Tests/MetroBxl.Sim.Tests.csproj` z odpowiedzią `0` jest
   w bloku przedstawiony jako wykonany, a pliku o tej nazwie nie ma — `grep` skończyłby
   się `No such file or directory` i kodem 2, nie zerem. Wyjście `0` jest natomiast
   prawdziwe dla `tests/Sim.Tests/Sim.Tests.csproj`, więc pomiar był zrobiony, a błąd
   jest w PRZEPISANIU komendy. To jest rodzina 6.D33 („czy komenda z pola da się
   wpisać"), leży poza zakresem tej pozycji i jest zapisem z datą — dlatego zostaje.
2. **Wzorzec ścieżki w `tools/tests/test_report_hygiene.py` nie dopuszcza wiodącej
   kropki**, więc żadna ścieżka `.github/…` nigdy nie była w `reports/` sprawdzana. Tu
   takich wystąpień jest **15 w 10 blokach** (wszystkie istnieją) i wzorzec tej bramki
   je obejmuje. Ile ich jest w `reports/` — nie mierzyłem; to jest osobna pozycja
   i osobny pomiar, w tej zmieniłbym plik spoza zadania.
3. **Rozszerzeń `.yml`, `.yaml`, `.txt`, `.tscn`, `.geojson`, `.glb` i `.log` nie ma
   dziś w polach ani razu**, a wzorzec je zna. Nie usuwam ich: martwa gałąź wzorca
   ścieżki jest nieszkodliwa, a jej brak byłby dziurą w pokryciu w dniu, w którym ktoś
   dopisze taką ścieżkę. Odwrotny wybór zrobiła bramka `NOTATIONS`
   w `tools/tests/test_report_hygiene.py` i tam był słuszny, bo notacja daty nieużywana
   udaje prawdę o formacie; rozszerzenie nieużywane nie udaje niczego.
4. **`data/keys` nie występuje w drzewie w ogóle**, a poza blokiem 6.A30 nazywa go
   jeszcze wiersz tabeli tej samej pozycji (kolumna „zauważone przy okazji"). Wiersz
   tabeli nie jest polem bloku i ta bramka go nie ogląda; jest to zapis historyczny
   o tym, co znaleziono, i poprawianie go skasowałoby znalezisko.
