# 6.D204 — pamięć działa, pytanie zadano po raz drugi, a bramki nie doszła ani jedna

**14.09.2026**, na `8e9f830`. Wejście: `tools/tests/mutation_sweep.py`
(`coverage_map`, `pokrycie_w_celach`, `zapisz_pokrycie`, `wczytaj_pokrycie`,
`sciezka_pokrycia`, `targets`, `was_executed`), `tools/tests/test_module_entrypoints.py`,
`reports/6d191-nie-ta-zmienna.md`, `reports/pamiec-pokrycia.md`.

## 1. Odpowiedź: TAK — a przesłanka pozycji opisuje inną mapę niż ta, o którą pyta

Pole „Skąd" mówi, że `zapisz_pokrycie` nazywa mapę **pamięcią podręczną commita**,
a cztery klucze katalogów próbnych mogą ją czynić bezużyteczną. Zmierzone:
**mapa zapisywana nie niesie ani jednego takiego klucza i nie ma jak go nieść.**

Między `coverage_map` a `zapisz_pokrycie` stoi `pokrycie_w_celach`. Kolejność jest
tu całą treścią:

```
coverage_map()  →  pokrycie_w_celach()  →  zapisz_pokrycie()
   mapa SUROWA        obcięcie do celów        mapa na dysku
```

Klucze `tools/tests/test_dwa_<losowe>/…` stoją w mapie **surowej**, czyli na
wejściu obcięcia. Na dysk idzie jego wyjście. Pomiar z 13.09.2026, z którego
pozycja wyszła, oglądał wyjście `coverage_map` — i wnioskował z niego o pamięci,
czyli o wyjściu obcięcia. To jest cała różnica.

| | kluczy | wierszy | efemerycznych | pod `tools/tests/` |
|---|---:|---:|---:|---:|
| SUROWA (wyjście `coverage_map`) | 201 | 36 475 | **4** | 137 |
| OBCIĘTA (to, co idzie na dysk) | 64 | 8 711 | **0** | **0** |

Odczyt z dysku tym samym commitem: **identyczny z zapisem**, 64 klucze. Odczyt
innym commitem: `None`. Obcięcie zdejmuje **76 %** wierszy i **68 %** kluczy.

Koszt policzenia mapy, zmierzony trzema przebiegami: **845,5 / 855,2 / 857,0 s**
(pierwszy na `a2ef9e0`, dwa dalsze na `8e9f830`) — czyli uzasadnienie wspólnego
pliku docelowego („policzenie kosztuje jeden pełny przebieg zestawu") opisuje
mechanizm, który istnieje. **Zostaje, nie jest przepisywane.**

**„Efemeryczne" liczone jest po ISTNIENIU PLIKU, nie po przedrostku nazwy**, i to
jest poprawka wyciągnięta z własnej sondy. Pierwsza wersja odsiewała wzorcem
`(test_dwa_|test_wiele_|test_pusty_)[a-z0-9]{8}` i zgłosiła **zero** efemerycznych
przy czterech obecnych: `tempfile` dobiera przyrostek z alfabetu, w którym jest
także podkreślnik, a w tym przebiegu wypadło `test_wiele__vlngc3k`. Sito po
przedrostku jest więc przyrządem gubiącym część populacji, którą ma liczyć;
pytanie „czy ten plik jeszcze jest na dysku" nie ma tej wady. Cztery klucze
nieistniejące to dokładnie trzy piaskownice (`test_wiele_` zostawia dwa pliki).

**Pytanie to zostało już raz zadane, 07.09.2026** — sześć dni przed wpisaniem
pozycji. Tamten pomiar (`reports/pamiec-pokrycia.md`) zrobił dokładnie to, czego
żąda pole „Skąd": dwie sondy z tego samego drzewa, te same 25 732 wiersze, **różne
zbiory kluczy**, różnica w piaskownicach. Odpowiedzią było wtedy **napisanie
`pokrycie_w_celach`**. Pozycja jest więc rodziną 6.D27 odwróconą: mechanizm
istnieje i działa, a zapis o nim był rozproszony na tyle, że ta sama obserwacja
wyszła drugi raz jako nowa.

## 2. Druga liczba, której żądało pole „Skończone, gdy"

> *„…i czy przegląd mutacyjny czyta je jako wiersze wykonane"*

**Nie czyta, i nie z uprzejmości.** `was_executed` pyta wyłącznie o
`mutation.path`, a `mutation.path` jest zawsze celem z `targets()`:

```
CELÓW (targets): 71, celów pod tools/tests/: 0
celów, których zestaw NIE URUCHAMIA wcale: 7
MUTACJI: 2586, PLIKÓW Z MUTACJĄ: 70, z nich pod tools/tests/: 0
przecięcie (klucze efemeryczne z przebiegu) × (ścieżki mutacji): 0
```

Przecięcie zerowe nie jest zbiegiem okoliczności ani własnością konfiguracji:
`targets()` odsiewa `tools/tests/` z definicji, a piaskownice leżą **wyłącznie**
tam. Nawet mapa surowa, podana `was_executed` wprost, nie zmieniłaby ani jednego
werdyktu.

## 3. Bramki nie doszła ani jedna — i to jest wynik, nie zaniechanie

Napisałem po drodze **dwie** i **obie usunąłem**, każdą po kontroli negatywnej,
która pokazała, że mierzy to, co już jest zmierzone. Zapisuję to, bo bez tego
trzeci agent napisze je po raz trzeci.

**Bramka pierwsza: „zapis → odczyt → tożsamość".** Przesłanka była taka, że
bramki tego modułu pytają **osobno** o obcięcie i **osobno** o odrzucenie mapy
z cudzego commita, a całej drogi nie przechodzi żadna. Przesłanka jest fałszywa,
i pokazała to nie lektura, tylko KN-6: mutacja gubiąca jeden klucz przy zapisie
zapala `test_the_remembered_map_survives_a_round_trip`, który robi dokładnie
zapis → odczyt → porównanie z wejściem (i dodatkowo sprawdza, że wartości wracają
**zbiorami**, bo `was_executed` robi na nich `in`). Drugą połowę trzyma
`test_a_remembered_map_from_another_commit_is_refused`, który idzie dalej niż moja
wersja: przenosi plik **pod nazwę innego commita**, żeby sprawdzić, że nazwa nie
wystarcza.

**Bramka druga: dolne ostrze `len(cele) >= 60` na `test_tests_are_never_targets`.**
Tu przesłanka jest prawdziwa — pętla po pustej liście przechodzi każdą regułę,
jaką się w nią wpisze (6.D27) — ale ostrze i tak jest zbędne, i to jest zmierzone
zawężeniem `targets()`, trzy razy, przy bazie **133/133**:

| zawężenie | wynik | czerwonych |
|---|---|---:|
| do 3 celów | 113/133 | 20 |
| do 55 celów | 131/133 | 2 |
| do 24 celów **dobranych tak, by zachować wszystkie trzy pliki przypięte z nazwy** | 129/133 | 4 |

Zawężenia, które zapala **wyłącznie** ostrze na liczbie, nie udało się zbudować.
Broni tego miejsca trójka niezależna od siebie: `test_targets_cover_the_real_tools`
(przypina **zbiór nazw**, nie liczbę — kształt z 6.D131),
`test_zaden_cel_mutacji_nie_lezy_poza_kodem_narzedzi` (`len(cele) > 20`,
postawione dokładnie na tę pułapkę i z tym powodem wypisanym w docstringu) oraz
testy `--only`, które wołają CLI na konkretnych katalogach. Czwarte zdanie o tym
samym byłoby sitem, które nic nie chroni.

**Co weszło zamiast bramek:** liczby wyżej i powód ich braku — w
`test_tests_are_never_targets`, w bloku nad `test_the_remembered_map_…` i w
`pokrycie_w_celach`, czyli w trzech miejscach, w których następny agent tę samą
myśl będzie miał.

## 4. Kontrole negatywne

Baza modułu: **133/133**. Po każdej `md5sum -c` na obu plikach: `OK`.

| | mutacja | wynik | zapaliło |
|---|---|---|---|
| KN-6 | `zapisz_pokrycie` gubi pierwszy klucz mapy | **131/133** | `..._survives_a_round_trip`, `..._from_another_commit_is_refused` |
| KN-7 | `wczytaj_pokrycie` przestaje sprawdzać commit | **132/133** | `..._from_another_commit_is_refused` |
| KN-8 | obcięcie przepuszcza wszystko (`if path in cele` → warunek zawsze prawdziwy) | **132/133** | `test_the_map_is_trimmed_to_mutation_targets` |
| KN-9 | `targets()` zawężone do 3 | **113/133** | 20 testów, wymienione wyżej |
| KN-9b | `targets()` zawężone do 55 | **131/133** | `..._cover_the_real_tools`, `..._only_z_trafieniami_…` |
| KN-9c | `targets()` zawężone do 24 z zachowaniem trzech nazw | **129/133** | cztery testy `--only` i `..._legacy_kinds_…` |

**KN-8 był raz spartaczony i to jest zapisane, a nie przemilczane.** Pierwsze
podejście wycięło `sed`em korpus `pokrycie_w_celach` na tyle nieszczęśliwie, że
moduł przestał się importować (`NameError: PROCES_ZNACZNIK is not defined`).
Przebieg padał **przed** jakąkolwiek asercją, więc **nie mierzył niczego** —
a czerwień z zepsutego importu wygląda w wyjściu identycznie jak czerwień
z zapalonej bramki. Powtórzone jako podmiana jednego warunku, składniowo poprawna.

## 5. Co jest przepisane, a co dopisane

- `pokrycie_w_celach`: liczby z 07.09.2026 **zostają**, dzisiejsze stoją **obok** —
  tamte są powodem, dla którego ta funkcja powstała, i przepisane przestałyby nim
  być. Dopisana definicja „efemerycznego" po istnieniu pliku.
- `zapisz_pokrycie`: zdanie o koszcie **przepisane** (dochodzą trzy zmierzone
  czasy), dopisany akapit mówiący, **co dokładnie jest pamiętane** — bo to jest
  zdanie, którego brak pozwolił zadać pytanie drugi raz.
- `test_tests_are_never_targets`: komentarz **przepisany** — niesie dziś i zdanie,
  które na tej bramce stoi, i pomiar mówiący, czemu ostrza mimo to nie dostała.
- Blok nad `test_the_remembered_map_survives_a_round_trip`: **dopisany**, z tabelą
  liczb i z odesłaniem do `reports/pamiec-pokrycia.md`.

## 6. Czego świadomie nie zrobiłem

- **Nie ruszyłem miejsca, w którym `test_module_entrypoints.py` buduje drzewa
  próbne** — pole „Poza zakresem" mówi o tym wprost, a pomiar pokazał, że ruszać
  nie ma czego: te klucze giną w obcięciu i tak.
- **Nie przyspieszałem przeglądu mutacyjnego** (to samo pole).
- **Nie postawiłem bramki na liczbach z sekcji 1.** Są to liczby drzewa, nie stałe
  kodu; rosną z każdym nowym modułem i zapadka na nich zapalałaby się na poprawnej
  pracy. Stoją datowane, w docstringu, obok liczb z 07.09.2026.
- **Nie liczyłem mapy w bramce.** Kosztuje 845–857 s; bramka, która tyle trwa,
  jest bramką, której nikt nie uruchomi.

## 7. Zauważone, nie tknięte

- **`unreachable_modules` podaje „138 mutacji w siedmiu modułach z `import bpy`,
  135 przeżywa — 98 %", a dziś zestaw nie uruchamia 7 z 71 celów.** Zgodność tych
  siódemek jest prawdopodobnie przypadkowa (jedna liczy moduły z `bpy`, druga —
  cele bez ani jednego wiersza w mapie pokrycia), ale **tego nie sprawdziłem**,
  a dwie siódemki obok siebie w jednym module to dokładnie ten kształt, w którym
  ktoś je kiedyś zeszyje w jedno zdanie.
- **Liczba 36 475 wierszy mapy surowej urosła o 79 między `a2ef9e0` a `8e9f830`**,
  czyli o jeden scalony PR (#608, 6.D203). Mapa **obcięta** ma w obu 8 711 wierszy
  co do jednego — bo tamten PR dotknął wyłącznie `tools/tests/`. Jest to najtańsza
  ilustracja tezy z sekcji 1, jaką ten pomiar dał, i nie stoi nigdzie w kodzie.
- **Dwa przebiegi sondy na tym samym drzewie dały 201 kluczy i 36 475 wierszy co do
  jednego.** Zjawisko z 6.D191 („mapy RÓŻNE przy identycznych licznikach") jest więc
  nadal żywe i nadal niewidoczne w żadnej sumie zbiorczej.
