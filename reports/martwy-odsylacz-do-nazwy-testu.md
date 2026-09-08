# Martwy odsyłacz do nazwy testu (6.D49)

**Zmierzone 08.09.2026 na commicie:** `a214ab9356dbdf1f29434a48c90d32b1fc95afbb`

Pozycja 6.D49 mówiła o jednym wierszu tabeli. Cała jej treść jest jednak w tym, **czego
nie wolno tknąć obok tego wiersza** — i to okazało się mierzalne.

## 1. Poprawiona jedna wzmianka

`reports/nieznana-opcja-runnera.md` §72, wiersz 4 tabeli „Kontrole negatywne —
wykonane", odsyłał do `Line_z_nieznana_opcja_konczy_sie_kodem_jeden`. Testu o tej
nazwie w drzewie nie ma: 6.A19 przepisała go i przemianowała na
`Line_z_opcja_innego_polecenia_konczy_sie_kodem_jeden`
(`tests/Sim.Tests/RunnerCommandTests.cs`, dziś wiersz 329), bo dawna nazwa mówiła
„nieznana opcja" o opcji, którą `budget` przyjmuje.

Wiersz jest **żywym odsyłaczem**, nie zapisem pomiaru: proza pod tabelą mówi w czasie
teraźniejszym, co dana mutacja **wywraca**, więc czytający ma po tej nazwie sięgnąć do
testu. Sięgał w puste miejsce.

Poprawka nie jest jednak samą podmianą. Tabela dokumentuje kontrolę **wykonaną
06.09.2026**, kiedy test nosił nazwę dawną, więc goła podmiana kazałaby czytać, że
kontrolę puszczono na teście o dzisiejszej nazwie. Wiersz nazywa więc jedno i drugie:
nazwę żywą, po której się sięga, i nazwę z dnia pomiaru, z odesłaniem do 6.A19.
Zapis pomiaru zostaje zapisem, odsyłacz staje się żywy.

## 2. Trzy rodzaje wystąpień tej jednej nazwy

Dawna nazwa stoi w `reports/` cztery razy i **trzy z tych czterech miejsc mają
zostać**:

| # | plik | rodzaj | co z tym |
|---|---|---|---|
| 1 | `reports/nieznana-opcja-runnera.md` §72 | żywy odsyłacz w tabeli kontroli | **poprawione** |
| 2 | `reports/postac-z-rownosciem.md` (KN-4, w bloku) | wklejone wyjście `dotnet test` | nietknięte |
| 3 | `reports/powtorzona-opcja.md` (KN-3, w bloku) | wklejone wyjście `dotnet test` | nietknięte |
| 4 | `reports/odmowa-replay-z-powodem.md` §3 | zdanie o historii („wywrócił X, który używał…") | nietknięte |

Wystąpienia 2 i 3 to `Failed <nazwa>` w blokach z licznikami `Failed: 1, Passed: 569,
Total: 570`. Przepisanie ich byłoby **falsyfikacją zapisu pomiaru**: wartością tych
linii jest to, co wyszło tamtego dnia, a tamtego dnia test nazywał się tak. Wystąpienie
4 jest zdaniem prawdziwym o przeszłości i przestałoby być prawdziwe po podmianie —
akapit obok, w tym samym raporcie, wymienia nazwę nową i tak ma zostać.

## 3. Ile jeszcze takich martwych odsyłaczy jest w `reports/` — jeden

Pole „Wyjście" pozycji żądało tej liczby, bo poprawka jednego wiersza bez niej nie
mówi, czy usterka jest jednostkowa. Pomiar poszedł przejściem po drzewie, nie oceną:
nazwy metod testowych C# czyta `tools/tests/csharp_test_methods.py` (ten sam czytnik,
którego używają bramki igieł), nazwy funkcji Pythona — skan `def` po `tools/`, a strona
porównywana to wszystkie pliki `reports/*.md`.

Stan **przed** tym commitem:

```
plikow w reports/:                          152
metod testowych C# w drzewie:               757
wzmianek o ksztalcie nazwy testu:           896
  nazw roznych:                             479
  w blokach ``` (wklejone wyjscie):         509
  w prozie / tabelach:                      387
MARTWYCH wzmianek (nazwy nie ma w drzewie):  36
  nazw roznych martwych:                     18
```

Trzydzieści sześć martwych wzmianek — i **dokładnie jedna** z nich jest usterką.
Pozostałe trzydzieści pięć rozkłada się na pięć rodzajów, z których żaden usterką nie
jest. Klasyfikacja jest ręczna, bo maszynowa jest właśnie tym, czego nie da się tu
zrobić (§4):

| rodzaj | wzmianek | przykład | dlaczego to nie usterka |
|---|---|---|---|
| A. nazwa obiektu Blendera, nie testu | 22 | `M7_car_6`, `M7_articulation_1`, `NEG_no_geometry` | to nazwy bryt w GLB i kamer kontrolnych; z testem dzieli **tylko kształt leksykalny** |
| B. nazwa modułu, nie metody | 1 | `test_suite_runtime_budget` w wywołaniu `import` | moduł istnieje jako plik, funkcji o tej nazwie nie ma i mieć nie musi |
| C. wklejone wyjście **ucięte** wielokropkiem | 6 | `Failed Numer_i_nazwa_kolumny…` | prefiks żywej nazwy `Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu`; kolumnowe wyjście `dotnet test` ucina długie nazwy |
| D. wklejone wyjście z nazwą od tamtej pory zmienioną | 3 | `Failed Compare_bez_dwoch_plikow_konczy_sie_kodem_dwa` | zapis pomiaru; dziś `…_kodem_jeden`, ale tamtego dnia padło to, co padło |
| E. prawdziwe zdanie o historii | 3 | „Pierwsza wersja `Wartosc_ujemna_po_znanej_opcji_nadal_przechodzi` żądała kodu 0" | zdanie jest o wersji pierwszej i jest prawdziwe |
| F. **żywy odsyłacz do nazwy, której nie ma** | **1** | `reports/nieznana-opcja-runnera.md` §72 | **usterka — poprawiona tym commitem** |

Rodzajów jest więc **sześć**, nie trzy. Trzy z pola „Gdzie różnica ma znaczenie"
opisują wystąpienia **tej jednej nazwy** i tam zgadzają się co do jednego (sekcja 2);
populacja martwych wzmianek w całym katalogu jest szersza, i to jest ustalenie tego
pomiaru, nie naciągnięcie wiersza kolejki.

Odpowiedź na pytanie pola „Wyjście" brzmi zatem: **martwy odsyłacz jest jeden i był
jeden**. Wyjściem jest raport mówiący to wprost, nie bramka — z powodu w sekcji 4.

## 4. Decyzja o bramce: NIE dodana, i to jest wynik pomiaru

Martwy odsyłacz do nazwy testu wygląda na klasę usterki, nie na przypadek, a bramka na
bliźniaczą klasę **już istnieje**: `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`
w `tools/tests/test_report_hygiene.py` pilnuje, żeby każda ścieżka wymieniona w raporcie
rozwiązywała się w drzewie. Jej własny docstring stawia granicę, o którą tu chodzi:
„**Ścieżka nie jest liczbą i tej dwuznaczności nie ma**" — liczba w raporcie może być
cytatem wyjścia albo zdaniem o stanie bieżącym, i z tekstu tego nie rozstrzygniesz.

Nazwa testu leży **po stronie liczby, nie ścieżki**, i pomiar pokazuje cztery
niezależne powody, każdy sam wystarczający:

1. **Kształt nie odsiewa.** Dwadzieścia dwie z trzydziestu sześciu martwych wzmianek to
   nazwy obiektów Blendera. `M7_car_6` i `Line_z_jednym_minusem_konczy_sie_kodem_jeden`
   mają identyczny kształt leksykalny — Słowo, potem człony małą literą. Żadna reguła
   na samej nazwie ich nie rozdzieli, bo repozytorium używa tej samej konwencji do
   nazywania bryt w GLB.
2. **Wklejone wyjście jest ucinane.** Kolumnowe wyjście `dotnet test` skraca długie
   nazwy wielokropkiem, więc bramka czytająca bloki zgłasza jako martwe sześć
   **prefiksów nazw żywych**. Wyjęcie bloków z zakresu nie pomaga: usterka F stoi
   w prozie razem z dwudziestoma czterema wzmiankami niebędącymi usterką.
3. **Filtr na historię wyciszyłby dokładnie ten jeden przypadek, o który chodzi.**
   Żeby uciszyć rodzaje D i E, bramka musiałaby rozpoznawać zdania o przeszłości.
   Wiersz, który 6.D49 poprawia, brzmi „odmowa zdjęta w całości (**stan sprzed** tej
   pozycji)" — niesie znacznik czasu przeszłego, choć odsyłacz w nim jest żywy.
   Sprawdziłem to na własnym klasyfikatorze, zanim uznałem wynik: pierwsza wersja
   pomiaru odłożyła §72 do rodzaju „zdanie o historii" i zameldowała **zero** żywych
   martwych odsyłaczy. Bramka o takim filtrze byłaby zielona nad jedyną usterką, jaką
   miała łapać.
4. **Licznik nie odróżnia stanu poprawionego od zepsutego — i to zmierzone, nie
   przewidziane.** Kontrola KN-1 (§6) przywróciła w §72 goły martwy odsyłacz i licznik
   martwych wzmianek **nie drgnął: 47 przed, 47 po**. Powód jest strukturalny, nie
   przypadkowy: poprawka nie usuwa dawnej nazwy z pliku, tylko **zmienia jej rolę** —
   z odsyłacza na zapis. Bramka licząca wystąpienia mierzy więc rzecz, która przy tej
   poprawce jest niezmienna, czyli nie byłaby nawet detektorem regresji. Jedyna
   różnica między jednym stanem a drugim leży w **roli** wzmianki, a rola jest tu tym,
   czego z tekstu nie da się odczytać.

Bilans, powiedziany liczbą: bramka bez filtrów daje **1 trafienie i 35 fałszywych
alarmów** (97 %); zawężona do prozy — **1 i 23**; z filtrem na historię — **0 i 23**;
w postaci licznika — **0 i 0**, bo licznik jest na tę poprawkę niewrażliwy.
Reguła projektu z 6.D27 mówi, co się z taką bramką dzieje: bramka zapalająca się na
tekście poprawnym zostaje **wyłączona, nie poprawiona**. Dodanie jej byłoby więc
dopisaniem modułu z terminem ważności, a nie zapadką.

Czego to **nie** znaczy: nie znaczy, że klasa usterki jest nieszkodliwa. Znaczy, że
dzisiejszy sygnał jej nie unosi. Warunek, pod którym decyzja się odwraca, jest jeden
i mierzalny: gdyby żywych martwych odsyłaczy zrobiło się więcej niż jeden, przy tym
samym rozkładzie rodzajów, stosunek trafień do alarmów przestaje być argumentem
i bramka wraca do rozważenia. Pomiar z tej sekcji da się powtórzyć skryptem z §5.

## 5. Weryfikacja

Zestaw narzędzi, przed i po zmianie, bez różnicy — zmiana dotyka wyłącznie prozy
w `reports/` i wiersza w `docs/TASKS.md`:

```
$ python3 tools/tests/test_all.py
  1996/1996 przeszło
  RAZEM 95.621 s, 1996 testów, 105 modułów
kod: 0
```

Pomiar z §3 jest powtarzalny; czytnik nazw bierze się z drzewa, nie z listy:

```python
import glob, os, re, sys
sys.path.insert(0, "tools/tests")
import csharp_test_methods as CTM

drzewo = {m for _p, _k, m, _ma in CTM.metody()}
for path in glob.glob("tools/**/*.py", recursive=True):
    if "__pycache__" in path:
        continue
    drzewo |= set(re.findall(r"^\s*def\s+(\w+)", open(path, encoding="utf-8").read(), re.M))

KSZTALT = re.compile(r"^(?:[A-Z][A-Za-z0-9]*(?:_[a-z0-9][A-Za-z0-9]*){2,}"
                     r"|test_[a-z0-9]+(?:_[a-z0-9]+){2,})$")
CYTAT = re.compile(r"`([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)`")
GOLE = re.compile(r"(?<![`\w.])((?:test_|[A-Z][a-z0-9]+_)[A-Za-z0-9_]*[a-z0-9])(?![\w`.])")

martwe = []
for path in sorted(glob.glob("reports/*.md")):
    w_bloku = False
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.lstrip().startswith("```"):
            w_bloku = not w_bloku
            continue
        for n in {m.group(1) for m in CYTAT.finditer(line)} | {m.group(1) for m in GOLE.finditer(line)}:
            if KSZTALT.match(n) and n not in drzewo:
                martwe.append((os.path.basename(path), i, n, "BLOK" if w_bloku else "proza"))
print(len(martwe), "martwych wzmianek")
```

Po tym commicie ten sam skrypt daje **47** martwych wzmianek zamiast 36, czyli
**więcej, nie mniej** — i to jest poprawne. Jedenaście dołożonych wzmianek to dziesięć
w tym raporcie i jedna w nawiasie w §72 `reports/nieznana-opcja-runnera.md`: wszystkie
**cytują dawną nazwę jako przedmiot opisu**, żadna nie jest odsyłaczem, czyli wszystkie
są rodzaju E. Liczba nazw różnych martwych stoi niezmieniona na **18**, bo ani jednej
nowej nazwy tu nie wprowadzono. Podaję obie liczby razem, bo sama liczba po zmianie
wyglądałaby jak pogorszenie.

## 6. Kontrole negatywne — wykonane

Zmiana jest w prozie, więc kontrola negatywna nie ma testu do wywrócenia w zwykłym
sensie. Kontrolowalne jest natomiast to, czy **pomiar jest pomiarem**, a nie stałą
przepisaną z oczekiwania — i to sprawdzone jest w trzy strony. Rzeczywiste wyjścia:

```
KN-1  dawna nazwa przywrocona w §72 jako goly odsylacz (stan przed poprawka)
      MARTWYCH wzmianek (nazwy nie ma w drzewie): 47
        nazw roznych martwych:                     18
      wiersz 72: | 4 | odmowa zdjeta w calosci (stan sprzed tej pozycji) |
                 `Line_z_nieznana_opcja_konczy_sie_kodem_jeden`, `Odmowa_wymienia…
      -> LICZNIK NIE DRGNAL: 47 przed poprawka i 47 po niej. Kontrola miala
         potwierdzic, ze pomiar widzi usterke — pokazala, ze NIE widzi, i to jest
         najwazniejszy wynik tej pozycji. Patrz §4 punkt 4.

KN-2  metoda w tests/Sim.Tests/RunnerCommandTests.cs przemianowana na zmyslona
      (`Line_z_opcja_innego_polecenia_konczy_sie_kodem_jeden`
       -> `Line_z_kontrola_negatywna_zmyslona_nazwa`)
      metod testowych C# w drzewie:               757
      MARTWYCH wzmianek (nazwy nie ma w drzewie):  50   (+3)
        nazw roznych martwych:                      19   (+1)
      -> czytnik czyta DRZEWO, nie liste: zniknieciu metody odpowiada dokladnie
         trzy wzmianki, tyle ile razy nowa nazwa stoi dzis w `reports/`

KN-3  czytnik nazw C# wskazany na katalog `tests/Sim.Tests` bez ani jednego pliku
      metod testowych C# w drzewie:                 0
      MARTWYCH wzmianek (nazwy nie ma w drzewie): 242
      -> prog na liczbe metod jest tu potrzebny: bez niego pusty czytnik
         zameldowalby 242 martwe wzmianki i wygladaloby to jak pomiar, a nie
         jak zepsuty przyrzad
```

Po każdej z trzech kontrol `__pycache__` wyczyszczony
(`find tools -name __pycache__ -type d -exec rm -rf {} +`), a po przywróceniu
`md5sum -c` na obu ruszanych plikach zgadzał się ze sprawdzoną kopią:

```
reports/nieznana-opcja-runnera.md: OK
tests/Sim.Tests/RunnerCommandTests.cs: OK
```

## 7. Poza zakresem

Nietknięte świadomie, bo pole „Poza zakresem" pozycji nazywa je wprost: wklejone
wyjścia dawnych pomiarów (§2, wystąpienia 2 i 3), zmiana nazw testów, bramka na
kształt tabel kontroli.

Nietknięte także liczby w prozie pod tabelą §72 w `reports/nieznana-opcja-runnera.md`
(„wywraca dokładnie dwa testy C#", „1720/1721"). To datowany pomiar z 06.09.2026;
6.A19 zmieniła od tamtej pory zarówno test, jak i sumę zestawu, więc dzisiejszy
przebieg dałby inne liczby — ale przeliczanie datowanego pomiaru jest dokładnie tym,
czego zakazuje 6.D3, a pozycja 6.D49 prosiła o nazwę, nie o liczbę.

## 8. Zauważone, nietknięte

- **Nazwy obiektów Blendera i nazwy testów dzielą jedną konwencję.** Dwadzieścia dwie
  z trzydziestu sześciu martwych wzmianek to bryły M7 (`M7_car_6`) i kamery kontrolne
  (`NEG_no_geometry`). To nie usterka, ale jest to powód, dla którego jakakolwiek
  przyszła bramka na nazwy w `reports/` musiałaby najpierw dostać rozłączne
  przestrzenie nazw. Osobna pozycja, gdyby kiedyś była potrzebna.
- **`reports/polecenia-runnera-bez-testu.md` niesie w bloku
  `Compare_bez_dwoch_plikow_konczy_sie_kodem_dwa`**, a dzisiejszy test nazywa się
  `Compare_bez_dwoch_plikow_konczy_sie_kodem_jeden`. Jest to wklejone wyjście, więc
  ma zostać — wymieniam, bo to druga para nazw, którą w tym repozytorium
  przemianowano, i przy trzeciej warto będzie wiedzieć, że nie jest pierwsza.
- **`reports/axis-station-chainage.md` §7 opisuje test „odwrócony, nie usunięty"** i
  nazywa starą nazwę w zdaniu o przeszłości, wymieniając zaraz obok trzy nazwy nowe.
  Jest to wzorcowy zapis tej rodziny zmiany i gdyby kiedyś powstawała konwencja
  „jak pisać o przemianowanym teście", ten akapit jest jej gotowym przykładem.
