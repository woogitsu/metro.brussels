# Triaż ocalałych mutacji: `tools/blender/lod.py`

**Snapshot przed triażem:** gałąź `mutation-sweep`, przebieg z 03.09.2026
**Snapshot po triażu:** `c572eb3`
**Data:** 2026-09-03

Drugi moduł triażu, po `clearance.py`. Wybrany dlatego, że miał **najwięcej ocalałych
w liczbach bezwzględnych** — 75 na 105 mutacji, czyli 71 % — i dlatego, że stoi na nim
cała geometria strumieniowana do silnika: wybór pierścieni, bryła kolizyjna i kontrola
manifestu. Moduł miał 50 własnych testów i to dobrych; ocalałe nie są dowodem, że testów
nie ma, tylko że **żaden nie stał na granicy**.

## Wynik

| | przed | po |
|---|---|---|
| mutacji | 105 | 105 |
| zabitych | 30 | **67** |
| ocalałych | 75 | **38** |
| dopisanych testów | — | 22 |
| ocalałe uznane za usterkę | — | **0** |
| udział zabitych | 29 % | **64 %** |

## Co się okazało usterką

### `lod_problems`: równa liczba trójkątów przechodziła jako „tańszy"

```python
if int(current["triangles"]) > int(previous["triangles"]):
    problems.append(f"{chunk['id']}: LOD {current['level']} nie jest tańszy ...")
```

Wiadomość mówi „nie jest tańszy", a poziom o **tej samej** liczbie trójkątów tańszy nie
jest. Kontrola bryły kolizyjnej dziesięć wierszy niżej liczy w tym samym miejscu `>=`,
więc te dwa warunki różniły się tylko przez przeoczenie.

Mutacja `>` → `>=` przeżywała, bo w żadnym teście dwa sąsiednie poziomy nie miały równej
liczby trójkątów.

**Zanim to zmieniłem, sprawdziłem, czy równość nie jest zachowaniem legalnym**, bo
zaostrzenie kontroli, która potem wyje na poprawnym manifeście, jest gorsze niż kontrola
za luźna. Nasycenie — dwa poziomy schodzące do tylu samo pierścieni — przy parametrach
generatora jest nieosiągalne. Najkrótszy chunk to 120 m (`sweep.DEFAULT_MIN_CHUNK_M`),
krok pierścienia 5 m (`sweep.DEFAULT_RING_STEP_M`), cięciwy poziomów to 0 / 25 / 60 m.
Zmierzone na prostej o tej długości:

```
prosta 120.0 m (najkrótszy chunk): LOD {0: 25, 1: 6, 2: 3}, kolizja 6
```

Trzy różne liczby, i to na prostej — na łuku strzałka dokłada jeszcze podziału. Równość
znaczy więc usterkę generatora, nie krótki chunk. Operator zmieniony na `>=`, powód
wpisany w kod razem z tym pomiarem.

**Uwaga na marginesie, nie zmieniana:** przy sztucznym rozstawie pierścieni 25 m poziom 1
schodzi do tego samego zestawu co poziom 0. Prawdziwy rozstaw to 5 m, więc w potoku to nie
zachodzi — ale zależność „LOD oszczędza tylko wtedy, gdy rozstaw pierścieni jest gęstszy
od cięciwy" nie jest nigdzie zapisana i warto, żeby była, gdyby ktoś kiedyś ruszył
`DEFAULT_RING_STEP_M`.

## Progi bez pokrycia — 20 dopisanych testów

Reszta ocalałych nie była usterką, tylko **granicą, której nikt nie przekroczył**. Poniżej
każda z nich razem z tym, co ją zabija. Kontrolą negatywną każdego testu jest ta właśnie
mutacja: test bez niej wygląda tak samo, a nie dowodzi niczego.

| wiersz | mutacja | czego nie sprawdzał żaden test | dopisana kontrola |
|---|---|---|---|
| 72 | `==` → `!=` | `level_params` mógł zwrócić pierwszy poziom **inny** niż zadany | każdy poziom oddaje sam siebie, plus odmowa dla nieistniejącego |
| 110, 183 | `<= 0.0` → `< 0.0` | odcinek zerowej długości w rzucie punktu — dzielenie przez zero | `a == b` w wersji 3D i 2D daje odległość od punktu |
| 125 | `<=` → `<` | `first == last`, czyli chunk o jednym pierścieniu | odmowa z `ValueError` |
| 135 | `>` → `>=` | cięciwa **równa** limitowi; poprzedni test miał stacje co 10 m przy limicie 10 m, gdzie obie wersje dają to samo | stacje 0/5/10/15 przy limicie 10: `[0, 2, 3]` wobec `[0, 1, 2, 3]` |
| 137 | `>` → `>=` | strzałka **równa** limitowi | łuk, limit ustawiony na zmierzoną strzałkę dwóch kroków |
| 199 | `< 3` → `<= 3`, `3` → `4` | trójkąt jako wielobok wejściowy `inset_polygon` | trójkąt wchodzi i wychodzi mniejszy |
| 206 | `<= 0.0` → `< 0.0` | krawędź zerowej długości w obrysie | odmowa z `ValueError` |
| 265 | `< 2` → `<= 2`, `2` → `3` | rura o **dwóch** pierścieniach — najkrótsza, jaka powstaje | objętość dodatnia i równa polu razy długość |
| 301 | `>= 3` → `> 3`, `3` → `4` | czworobok, który po sklejeniu jest trójkątem | trójkąt zostaje, nie wypada |
| 134 | `<=` → `<` | odcinek, który **cały** mieści się w limicie: ostatni pierścień przestaje być kandydatem, wraca przez `keep[-1] != last` i zostaje pierścień nadmiarowy — zmierzone `[0, 3, 4]` zamiast `[0, 4]` | prosta 20 m przy cięciwie 25 m oddaje dokładnie dwa końce |
| 471 (pierwszy `<=`) | `<=` → `<` | pociąg **dokładnie** na początku chunka: zmierzone `-500,0 m` zamiast zera | zero na obu krańcach i brak wartości ujemnej na całym przebiegu co 0,5 m |
| 480 | `>=` → `>` | odległość **dokładnie** na progu; test sprawdzał 250 m przy progu 200 m | 200 → poziom 1, 199,999 → poziom 0 |
| 487 | `> 0` → `> 1` | próg poziomu 1 wypadający z listy — chunk dostawałby pełną siatkę w dalekim planie, po cichu | tyle progów, ile poziomów bez zera, i w tej samej kolejności |
| 519 | `<=` → `<` | chunk **dokładnie** na promieniu kolizji | pociąg na 350 m, chunk od 500 m, odległość równa 150 m = `COLLISION_RADIUS_M` |
| 528 | `==` → `!=` | `lod_triangles` liczący pierwszy poziom **inny** niż w planie | suma dla każdego z trzech poziomów osobno |
| 552 | `<=` → `<` | dwa poziomy o **tym samym** progu przełączenia | manifest z równymi progami musi dać problem |
| 554 | `<=` → `<`, `0` → `1` | dwa poziomy o **tej samej** cięciwie; druga mutacja wyłączała kontrolę dla jedynej pary, w której da się ją złamać | manifest z równymi cięciwami poziomów 1 i 2 |
| 576 | `>` → `>=` | **usterka, patrz wyżej** | manifest z równą liczbą trójkątów |
| 579 | `<` → `<=` | tu równość jest w porządku i to jest różnica wobec 576: pytanie brzmi „czy błąd zmalał", nie „czy nie urósł" | równy błąd NIE jest meldowany |
| 583 | `<= 0` → `< 0` (×2), `0` → `1` (×2) | zero trójkątów albo zero wierzchołków w poziomie | zero meldowane, jeden nie meldowany — obie strony granicy |
| 594 | `>=` → `>` | kolizja o **tej samej** cenie co siatka wizualna | manifest z równą liczbą trójkątów |
| 598 | `< 0.0` → `<= 0.0`, `0.0` → `0.001` | zapas ścienny **równy zeru**, czyli bryła na styk ze światłem tunelu | zero przechodzi, `-1e-9` nie — granica przeciwna niż przy skrajni i to jest zamierzone |
| 601 | `<= 0.0` → `< 0.0`, `0.0` → `0.001` | zapas skrajni **równy zeru**, czyli pociąg ociera o kolizję | zero meldowane |
| 603 | `<= 0.0` → `< 0.0`, `0.0` → `0.001` | objętość bryły kolizyjnej **równa zeru** | zero meldowane |
| 594, 595, 614, 615 | `>` → `>=` (×4) | przesunięcie szwu **równe** tolerancji | cztery pola (LOD/kolizja × początek/koniec), obie strony granicy w każdym — **przy tolerancji będącej potęgą dwójki**, patrz niżej |

### Test granicy, który granicy nie dotykał

Pierwsza wersja kontroli szwu brała tolerancję `1e-6` i przesuwała szew o `+1e-6`.
Dla początku chunka (0,0 m) różnica wychodziła dokładnie `1e-6` i mutacja ginęła.
Dla końca (1000,0 m) wychodziło `9,999999974752427e-07`, czyli **mniej** niż tolerancja
— równość nigdy nie zachodziła, obie wersje warunku dawały to samo i **dwie z czterech
mutacji przeżywały mimo testu napisanego wprost pod nie**.

```
     0.0 -> diff 1e-06                  == tol? True
   500.0 -> diff 9.999999974752427e-07  == tol? False
  1000.0 -> diff 9.999999974752427e-07  == tol? False
```

Tolerancja jest teraz `2**-20`, reprezentowalna dokładnie przy każdej z tych podstaw,
a sam test **sprawdza to założenie wprost** zamiast je zakładać. Bez tego ta sama pułapka
wróci przy pierwszej zmianie liczb w `_manifest`.

To jest ta sama rodzina błędu, co cztery pomyłki narzędzia opisane w `reports/mutation-sweep.md`:
coś, co nie jest sprawdzeniem, wygląda na sprawdzenie. Tu wyłapał ją dopiero **drugi**
przebieg mutacyjny po dopisaniu testów — czyli sam przegląd mutacyjny, użyty jako kontrola
własnych testów, a nie tylko cudzych.

### Dwie granice ustawione przeciwnie — i to celowo

`wall_margin_m < 0.0` odrzuca dopiero wartość ujemną, `gauge_margin_m <= 0.0` odrzuca już
zero. Wygląda to na niekonsekwencję, a nie jest:

- **zapas ścienny** mierzy, jak głęboko bryła kolizyjna siedzi wewnątrz światła tunelu.
  Zero znaczy „dotyka", a pytanie brzmi „czy **wystaje**" — na styk odpowiedź jest
  przecząca;
- **zapas skrajni** mierzy odstęp między skrajnią M7 a bryłą kolizyjną. Zero znaczy, że
  pociąg **dotyka** kolizji, czyli w nią wchodzi.

Obie granice są teraz przypięte testem z obu stron, więc następna osoba, która je zobaczy,
znajdzie tam odpowiedź, a nie zagadkę.

## Jak sprawdzałem równoważność — i dlaczego dwa razy się pomyliłem

Etykieta „mutant równoważny" jest wygodna i dlatego niebezpieczna: brzmi jak wniosek,
a bywa wymówką. Przy pierwszym podejściu **dwie** pozycje trafiły do niej z samego
czytania kodu i obie były błędne:

- **471, pierwszy `<=`** — napisałem, że ścieżka zapasowa i tak zwróci zero. Zwraca
  `-500,0 m`, bo przy `value == start` gałąź `value < start` nie zachodzi i wybierana
  jest druga;
- **134** — napisałem, że ostatni pierścień wróci przez `keep[-1] != last`. Wraca, ale
  **razem z przedostatnim**, którego w oryginale nie ma.

Dlatego każda pozycja z tabeli niżej została sprawdzona **wykonaniem**, a nie
rozumowaniem: mutacja wstrzyknięta w źródło, moduł skompilowany osobno i porównany
z oryginałem na łuku 91,5 m przez `deviation_stats` i `wall_margin_m` co do ostatniego
bitu, a dla funkcji czystych — wprost na wartościach zwracanych. Tabela poniżej wypisuje
tylko te, dla których porównanie wyszło identyczne.

## Co NIE jest usterką i zostaje

Ocalałe, których **nie da się odróżnić żadnym wejściem**. Każda pozycja z powodem, nie
z etykietą.

| wiersz | mutacja | dlaczego nieobserwowalna |
|---|---|---|
| 471 (drugi `<=`), 473 | `<=` → `<`, `<` → `<=` | tylko koniec chunka i tylko dolna gałąź: przy `value == end` ścieżka zapasowa zwraca `value - end`, czyli **to samo zero**; przy `value == start` gałąź `value < start` i tak nie zachodzi. Odróżnialny jest wyłącznie **pierwszy** `<=` tego wiersza i on jest w tabeli wyżej jako usterka |
| 351 (×2), 388 (×2) | `<` → `<=` | marsz po zachowanych pierścieniach: gdy `kept[slot+1] == index`, oryginał daje `high == index`, mutant `low == index`. W `deviation_stats` obie gałęzie trafiają w skrót `index == low or index == high`, w `wall_margin_m` dają `t = 1` i `t = 0` przy zamienionych końcach — **ten sam punkt** |
| 113 (×2), 186 (×2) | `<` → `<=`, `>` → `>=` | obcięcie parametru rzutu: `t < 0.0` przy `t == 0.0` zwraca `0.0` z obu stron warunku, tak samo `t > 1.0` przy `t == 1.0` |
| 201 | `>` → `>=` | znak pola wieloboku: równość znaczy pole zerowe, a wielobok zerowego pola nie przechodzi przez `inset_polygon` — poprzedza go kontrola krawędzi zerowej długości |
| 216 | `<` → `<=` | próg równoległości `abs(cross) < 1e-12`: równość **dokładnie** na progu wymagałaby dwóch krawędzi o iloczynie wektorowym równym co do bitu `1e-12` |
| 554 | `>` → `>=` | `previous["level"] >= 0` zamiast `> 0`: dla pary 0-1 warunek obok i tak nie zachodzi, bo poziom 0 ma cięciwę `0.0`, a `25.0 <= 0.0` jest fałszem. Odróżnialna jest tylko druga mutacja tego wiersza (`0` → `1`) i ona jest w tabeli wyżej |
| 311 | `<` → `<=` | porządkowanie klucza krawędzi `(a, b) if a < b else (b, a)`: `a == b` to pętla własna, której `weld` nie przepuszcza — usuwa ją zwijanie powtórzeń |
| 359, 395 | `<= 0.0` → `< 0.0` | zerowe rozpięcie chainage między zachowanymi pierścieniami: dwa pierścienie o tym samym kilometrażu wypadają wcześniej, w `sweep.dedupe` |
| 127 (×2) | `0.0` → `0.001` | „brak limitu" jest kodowany zerem; limit 0,001 m odrzucałby wszystko tak samo jak brak wyboru — obie gałęzie dają pełny zestaw pierścieni |
| 167 | `<` → `<=` | test przecięcia promienia w `point_in_polygon`: równość znaczy punkt **dokładnie** na krawędzi pionowej, czyli przypadek, w którym „wewnątrz" i „na zewnątrz" nie są rozłączne |
| 196 | `<= 0.0` → `< 0.0` | wcięcie o zero: skrót zwraca kopię, ścieżka pełna liczy przecięcia krawędzi przesuniętych o zero — **ta sama** geometria |
| 91 | `<= 0.0` → `< 0.0` | zerowe odchylenie: skrót zwraca `0.0`, ścieżka pełna liczy `0.0 / (tolerancja * kąt)`, czyli też `0.0` |

### Pasmo podmilimetrowe — zostawione świadomie

Mutacje `prog 0.0 → 0.001` (wiersze 91, 110, 127 ×2, 135, 137, 183, 186, 196, 201, 206,
610, 612) są odróżnialne **tylko** dla wartości z przedziału `(0, 0,001)`, czyli poniżej
milimetra. Testy dopisane wyżej trafiają w dokładne zero, które łapią obie wersje warunku.

Nie dopisywałem osobnych testów na pół milimetra, bo taki test mierzyłby narzędzie, a nie
model — z jednym wyjątkiem, który **przestał być pytaniem**: `gauge_margin_m`.

**ROZSTRZYGNIĘTE 03.09.2026 przez właściciela: próg podniesiony z zera na 1 mm.**
Zapas 0,5 mm między skrajnią M7 a bryłą kolizyjną nie jest zapasem, tylko stykiem,
w którym o wyniku decyduje zaokrąglenie `double`. Kontrola pyta teraz
`gauge_margin_m < COLLISION_GAUGE_MARGIN_MIN_M`, a stała jest jawnym
`design_assumption` z komentarzem mówiącym, że idzie do wymiany, gdy R-005 dostanie
liczbę ze STIB. Obie strony granicy przypięte testem, cztery kontrole negatywne.
Mutacja `0.0 -> 0.001` w tym wierszu jest tym samym martwa: progu nie da się już
przesunąć o milimetr bez wywrócenia testu.

`volume_m3` (wiersz 612) zostaje przy zerze i to jest inna sprawa: objętość nie ma
jednostki, którą warto progować — bryła albo ma objętość, albo jest zdegenerowana.

Podobnie `1e-12` w wierszu 216 (`prog` i `operator`): to próg równoległości krawędzi,
nie wielkość fizyczna, i jego mutacja jest odróżnialna wyłącznie dla iloczynu wektorowego
mieszczącego się dokładnie między `1e-12` a `1,01e-12`.

## Czego ten triaż nie ruszał

- **wartości progów** — 25 m, 60 m, 0,15 m, 0,35 m, 150 m, 0,05 m są założeniami
  projektowymi z `docs/TASKS.md` (T-210) i pozostają decyzją właściciela. Testy przypinają
  **granice porównań**, a nie liczby po prawej stronie;
- **`sweep.py`** — ocalałe tego modułu są osobną pozycją kolejki;
- **geometrii wyjściowej** — żaden test nie został osłabiony ani usunięty; 50 istniejących
  przechodzi bez zmian.
