# 6.D195 — 849 asercji, 31 na źródle, 12 wykonalnych i jedna trzecia droga

**13.09.2026**, na `30f3090`. Wejście: `tools/tests/` (asercje kształtu
`assert "…" in <źródło>`), `tools/tests/test_conflict_markers.py`,
`reports/6d165-dwie-bramki-slepe-i-cisza.md` §5.

## 1. Skala jest ODWROTNA, niż zakładała pozycja

Pozycja pisała, że „w `tools/tests/` stoi **wiele** bramek czytających źródło cudzego
modułu". Zmierzone skanem `ast` po całym `tools/tests/`:

| co | ile |
|---|---:|
| asercji kształtu `"literał" in coś` | **849** |
| z tego stoi już na **ZACHOWANIU** (wyjście wywołania albo procesu) | **560 (66 %)** |
| tekst czytany z jakiegokolwiek pliku | 258 |
| kod źródłowy w ogóle (`.py` + `.cs` + `.sh`) | 96 |
| **źródło `.py` — rodzina, o której mówi pozycja** | **31 (3,7 %)** |

**Dwie trzecie zestawu już pyta o zachowanie.** Rodzina `.py` nie jest przy tym
największa: bramki na `.cs` i `.sh` to 65, na YAML-u CI 69 — każda ponad dwa razy
liczniejsza. Jeśli pozycja mierzy „napis zamiast zachowania", to cięcie po samym `.py`
jest **węższe niż zjawisko**, i to jest pierwsza rzecz, którą ten pomiar poprawia.

## 2. Dlaczego LISTA, a nie liczba — zmierzone, nie przyjęte

Proste kryterium („w obejmującej funkcji pada `.py` albo `getsource`") daje **158**
trafień wobec 31 z listy ręcznej:

```
kryterium PROSTE: 158
lista RECZNA    :  31
czesc wspolna   :  22
falszywe trafienia: 136
przeoczenia       :   9
```

Myli się **w obie strony**. Automat na tej liczbie byłby dokładnie tym cichym sitem,
którego ten projekt unika — więc **liczby nie ma, jest lista**, tak samo jak przy
`Z_WEJSCIEM_SYNTETYCZNYM` z 6.D161.

Kotwicą wpisu jest `(plik, funkcja, operator, literał)`, **nie numer wiersza**: numer
przesuwa się przy każdej edycji i lista rozjechałaby się sama. Sama trójka bez operatora
jest niejednoznaczna dla dwóch wpisów (ten sam literał pod `in` i pod `not in`),
z operatorem — jednoznaczna dla wszystkich. **Granica, wypisana:** w całych 849 zostaje
10 kotwic niejednoznacznych (21 asercji); żadna nie jest na liście.

## 3. Podział trzydziestu jeden

| klasa | ile | co znaczy |
|---|---:|---|
| **WYKONALNA** | **12** | zachowanie da się wywołać tanio |
| **STRUKTURALNA** | **9** | bramka pilnuje KSZTAŁTU, nie zachowania |
| **STRUKTURALNA_AST** | **2** | nie szuka napisu — czyta drzewo składni |
| **KOSZTOWNA** | **7** | zachowanie za Blenderem albo innym trybem interpretera |
| **NIE_Z_TEJ_RODZINY** | **1** | wpis omyłkowy, zostaje z powodem |

**Dziewięć STRUKTURALNYCH to nie jest zaniedbanie i to jest sedno.** Bramka „moduł X
woła pomocnika Y" albo „w module X nie ma importu Z" mówi o kształcie, a nie o wyniku —
przez wywołanie tego nie widać **z definicji**, bo dwa różne kształty dają to samo
zachowanie i o to właśnie chodzi. `test_mass_copies.py` żąda, żeby moduł **niósł literał**
`"AW0":170000.0`, czyli był drugą, niezależną drogą wobec rejestru; wartość odczytana
importem byłaby ta sama również wtedy, gdyby zaczął czytać rejestr — a to jest dokładnie
to, co ma paść.

**Jeden wpis jest na liście omyłkowo i zostaje z zapisanym powodem:**
`test_mutation_sweep.py:1200` czyta plik w katalogu **tymczasowym**, wytworzony przez
`sweep.neutralise_own_tests` dwa wiersze wyżej — asercja stoi już na wyniku wywołania.
Zostaje wymieniona, żeby następny pomiar nie policzył jej drugi raz.

## 4. Koszt, którego pozycja żądała z pomiaru

```
koszt jednej zamiany „napis -> przebieg w podprocesie”:
  proba 1: 0.090 s   proba 2: 0.087 s   proba 3: 0.085 s   sredni: 0.087 s

SUITE_RUNTIME_BUDGET_S : 150.0
MEASURED_MAX_WALL_S    : 116.404
zapas do progu         : 33.596 s
zamian miesci sie      : 386
```

Wszystkie **12 wykonalnych kosztowałoby 1,0 s — 3 % zapasu**. Ograniczenie, o którym
mówi pozycja, **istnieje, ale nie wiąże**.

**Zastrzeżenie, które stawiam przeciwko własnej liczbie:** 0,087 s zmierzyłem
w KONTENERZE, a próg jest skalibrowany na RUNNERZE. Dokładanie kosztu z jednej maszyny
do zapasu z drugiej jest tym samym mieszaniem, przed którym 6.D135 i 6.D149 postawiły
podłogę mierzalności. Wniosek przeżywa to **wyłącznie** dlatego, że zapas jest
trzydziestokrotny; przy zapasie ciasnym liczby trzeba by zmierzyć na runnerze.

## 5. Pozycja stawia wybór BINARNY, a drzewo ma TRZECIĄ drogę

Pole „Skończone, gdy" mówi: „zamienić albo zostawić z powodem". Trzecia możliwość
istnieje i **drzewo już jej używa**: czytać **drzewo składni** zamiast tekstu.

- `test_readme_claims.py:598` — `"bpy" not in importy`, gdzie `importy` pochodzą
  z `ast.parse`. Docstring mówi, że wersja zachowaniowa (`sys.modules`) była
  **zmierzona jako fałszywa**, bo inne moduły wstawiają atrapy `bpy`.
- `test_mutation_sweep.py:1996` — `"wiersze_starego_bajtkodu" in wolane`, gdzie `wolane`
  to nazwy wywołań z `ast.walk`.
- `test_conflict_markers.py:421` sam nazywa różnicę: *„byłoby zielone także wtedy, gdyby
  moduł wołał gita przez `os.popen`, i czerwone na samym słowie w komentarzu. Lista
  importów jest tu faktem sprawdzalnym."*

Jest to **tanie** (nie potrzebuje Blendera ani podprocesu) i **ściśle mocniejsze** od
szukania podnapisu.

## 6. Najostrzejszy przypadek: bramka, która nie pilnuje tego, co mówi

`test_camera_aim.py` ma docstring **„Wypis ma mówić jedno i drugie"** i trzy asercje
szukające trzech podnapisów **w całym pliku**. Wejście syntetyczne:

```python
def cokolwiek():
    print("[OKNO] zaweza kamery: ")          # wypis PUSTY
def gdzie_indziej():
    x = CA.KAMERY_POD_OKNEM                  # nazwa w innej funkcji
def i_tu():
    y = CA.proporcje_okna(1, 2)              # proporcje policzone i wyrzucone
```

**Wszystkie trzy asercje przechodzą.** Nic nie wiąże trzech podnapisów z jednym `print`,
a wypis może być pusty. Zachowanie stoi za `import bpy` (klasa KOSZTOWNA), więc
uruchomienie odpada — ale **droga z §5 jest otwarta**: znaleźć wywołanie `print` w drzewie
składni i zażądać, żeby wszystkie trzy części stały w JEGO argumentach. Tego nie robię,
bo zamiana bramek stoi w „Poza zakresem" tej pozycji; zapisuję jako rozstrzygnięcie
do wykonania.

## 7. Siedem kontroli negatywnych, baza 45/45 — i jedna ZIELONA, z wyjaśnieniem

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | nowa bramka na napisie w źródle (32. wpis) | 44/45 |
| KN-2 | czytnik nie rozkłada `and` | **43/45** |
| KN-3 | literał na liście przepisany | 44/45 |
| KN-4 | jedna WYKONALNA przeklasyfikowana | 44/45 |
| KN-5 | pętla listy oślepiona, słownik nietknięty | 44/45 |
| KN-6 | skan zawężony do katalogu bez takich asercji | 44/45 |
| KN-7 | kontrola przyrządu zdjęta (bez komunikatu) | 44/45 |
| KN-7b | **kontrola przyrządu zdjęta, z komunikatem** | **45/45 ZIELONA** |

**KN-2 jest tu najważniejsza i daje liczbę przy okazji:** oślepienie czytnika na `and`
zbija liczbę z 849 na **751**, czyli **98 asercji siedzi w łańcuchach `and`/`or`**.
Zapala przy tym i kontrolę przyrządu, i liczbę — dwie różne drogi do tego samego.

**KN-7 zapaliła CUDZĄ bramkę, nie moją** (asercja bez komunikatu), więc powtórzyłem ją
jako **KN-7b, z komunikatem — i wyszła ZIELONA.** Kontroli przyrządu nie broni nic.
Sprawdziłem jednak, czy to usterka, i **nie jest**: z pięciu kształtów, które ta kontrola
wymienia, `assert not ("x" in y)` ma w drzewie **zero wystąpień**. Liczba 849 nie może go
więc obronić z zasady, a kontrola jest jedyną drogą — czyli robi dokładnie to, po co
istnieje. Zieleń KN-7b jest **przewidywalna i wytłumaczona**, a nie przeoczona.

## 8. Czego świadomie nie zrobiłem

- **Ani jednej bramki nie zamieniłem na uruchamianie** — pole „Poza zakresem" zabrania
  tego bez pomiaru kosztu. Pomiar jest zrobiony (§4) i mówi, że zamiana się mieści; samą
  zamianę zostawiam osobnej pozycji, bo dwanaście zamian to dwanaście decyzji, a nie
  jedna.
- **Progu czasu ściany nie ruszałem** — to samo pole.
- **Bramek kroku CI nie tknąłem** — to samo pole.
- **Rodziny `.cs`, `.sh` i YAML-a nie policzyłem po jednej** — pozycja pytała o `.py`,
  a rozszerzenie zakresu bez pytania byłoby poszerzaniem pozycji. Liczby zbiorcze (65
  i 69) stoją w §1 jako materiał.

## 9. Zauważone po drodze, nie tknięte

- **`test_mass_copies.py:170` szuka `'"AW0":170000.0'` BEZ SPACJI.** Dziś przechodzi, bo
  `tools/physics/reference.py` jest zapisany bez spacji; **każde przeformatowanie tego
  pliku zapali tę bramkę**, choć zachowanie się nie zmieni. Bramka jest strukturalna
  słusznie, ale jej kotwica jest krucha wobec formatowania.
- **66 asercji klasy WYJŚCIE bada zwrot pomocnika z samego pliku testu**, a nie modułu
  pod testem — to cieńsza rodzina niż 265 zwrotów modułu pod testem i nikt jej nie
  rozdzielił.
- **`test_dotnet_version.py:1687` i `:1689` czytają przez `inspect.getsource` funkcję
  pomocniczą z tego samego pliku testowego**, a nie moduł narzędzia. To one mają
  najtańszą drogę wyjścia z rodziny: pomocnik zwraca zbudowany napis w słowniku.
