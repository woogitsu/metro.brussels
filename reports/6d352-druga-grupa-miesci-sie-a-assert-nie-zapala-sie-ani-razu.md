# 6.D352 · Druga grupa `(?:…)` mieści się w obu wzorcach i zagrożenie jest REALNE — a `assert` nie zapala się ani razu na dziewięciu wariantach

**Data:** 23.09.2026 · **Gałąź:** `claude/6d352-druga-alternatywa` · **Baza:** `c4ef8a1`

6.D343 §8 zapisało, że dwa miejsca wyłuskują alternatywę rozszerzeń z tekstu wzorca
ścieżek pierwszym trafieniem `re.search`, że oba mają obronę i że żadna z nich nie
sprawdza, czy grupa `(?:a|b|c)` jest **jedna**. Ta pozycja **mierzy na wejściu
syntetycznym i liczy**. Żadnego wzorca, żadnego wyłuskania i żadnej obrony nie
zmienia — warianty wzorca wstawia przyrząd do **kopii źródła modułu w pamięci**,
a drzewo zostaje nietknięte.

Przewidywań przed pomiarem **nie spisałem** i nie udaję, że było inaczej; stąd ten
raport nie ma sekcji „trafione / obalone".

---

## 1. Poprawka założenia: wzorców ścieżek są DWA, nie jeden

§8 tamtego raportu i blok tej pozycji mówią o „tamtym wzorcu" w liczbie pojedynczej.
To nieprawda i wyszło w pierwszym wierszu przyrządu: oba wyłuskania czytają
**różne obiekty o tej samej nazwie**, każdy zdefiniowany we własnym module.

```
te same obiekty?  False  ten sam tekst?  False
```

* `tools/tests/test_field_paths.py` — `PATH_TOKEN` pól kolejki, wyłuskanie
  do `ROZSZERZENIA_Z_PATH_TOKEN` (karmi `BARE_TOKEN`), obrona — bramka
  `test_wzorzec_golej_nazwy_dzieli_rozszerzenia_z_PATH_TOKEN`;
* `tools/tests/test_report_hygiene.py` — `PATH_TOKEN` raportów, wyłuskanie
  w `_rozszerzenia_we_wzorcu`, obrona — `assert grupa` z komunikatem.

Listy rozszerzeń obu wzorców **nie są równe**: siedemnaście wobec dwunastu.

```
miedzy modulami: tylko field_paths=['glb', 'jsonl', 'log', 'png', 'zip']  tylko report_hygiene=[]
```

Pytanie pozycji odpowiadam więc **osobno dla każdego wzorca** — bo to dwa pytania,
nie jedno. Różnicy pięciu rozszerzeń nie oceniam (§6).

## 2. Kontrola przyrządu — przechodzi

Pole żądało, żeby na DZISIEJSZYM wzorcu oba wyłuskania dały tę samą listę. Wobec §1
kontrola ma sens tylko jako porównanie **dwóch wyłuskań na tym samym tekście**:
każde z nich puszczone na każdy z dwóch wzorców.

```
przepisanie obu wyluskan zgodne z drzewem: TAK
F0 i H0 odtwarzaja dzisiejsze wzorce co do znaku: TAK

=== KONTROLA PRZYRZADU: oba wyluskania na KAZDYM z dzisiejszych wzorcow ===
field_paths     A=geojson|csproj|jsonl|yaml|json|tscn|glb|yml|txt|png|csv|zip|log|sh|md|py|cs
                B=geojson|csproj|jsonl|yaml|json|tscn|glb|yml|txt|png|csv|zip|log|sh|md|py|cs
                A==B: True
report_hygiene  A=py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv
                B=py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv
                A==B: True
```

Na każdym z dzisiejszych wzorców oba wyłuskania dają tę samą listę, więc **rozjazdu
wyłuskań dziś nie ma** i pytanie o drugą grupę nie jest przedwczesne. Różne listy
między modułami (§1) nie są rozjazdem wyłuskania, tylko różnicą samych wzorców.
Wiersze „przepisanie … zgodne" i „F0 i H0 odtwarzają" są dwiema osobnymi kontrolami:
wyrażenia wyłuskań w przyrządzie są porównane napisowo ze źródłem obu modułów,
a warianty zerowe — co do znaku z dzisiejszym `PATH_TOKEN.pattern`.

## 3. Odpowiedź pierwsza: ile grup nieprzechwytujących niesie dziś wzorzec

```
test_field_paths.PATH_TOKEN      (?: = 1, z alternatywa | = 1
test_report_hygiene.PATH_TOKEN   (?: = 2, z alternatywa | = 1
      (?:\.(?=[A-Za-z0-9_]+/))                                     alternatywa=nie
      (?:py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv)    alternatywa=TAK
```

**Wzorzec raportów niesie DRUGĄ grupę nieprzechwytującą już dziś** — opcjonalną
wiodącą kropkę przed katalogiem — i stoi ona **przed** grupą rozszerzeń. Wyłuskanie
z `_rozszerzenia_we_wzorcu` ją przeżywa, ale nie dzięki obronie: przeżywa, bo klasa
`[a-z|]+` nie przyjmuje ukośnika wstecznego, a tamta grupa zaczyna się od `\.`.
Pierwsze trafienie jest więc dziś właściwe **z powodu kształtu treści pierwszej
grupy**, a nie dlatego, że ktoś to sprawdza.

## 4. Odpowiedź druga: co zwracają wyłuskania przy dwóch grupach

Rozstrzyga próba dopisania, nie czytanie, więc przyrząd dopisuje. Wiersz „ścieżki
identyczne" mówi, czy wariant **zmienia to, co widzi sam wzorzec ścieżek**
(na `docs/TASKS.md` albo na `reports/*.md`) — „TAK" znaczy, że druga grupa weszła
**bez zmiany zachowania wzorca**, czyli jako refaktor, który nikogo by nie zaniepokoił.

**Wzorzec pól kolejki** (wyłuskanie A, obrona = bramka):

```
wariant                                             sciezki     A zwraca                         obrona
F1 podzial, kazda czesc z wlasnym \. (dlugie 1.)    TAK         geojson|csproj|jsonl|…|glb|yml   CZERWONA (probka: goly .py)
F2 podzial, kazda czesc z wlasnym \. (krotkie 1.)   TAK         txt|png|csv|zip|log|sh|md|py|cs  CZERWONA (brak csproj)
F3 podzial zagniezdzony pod jednym \.               TAK         None                             import modulu PADA (AttributeError)
F4 (?:\.(?:min|test))? PRZED rozszerzeniem          TAK         min|test                         CZERWONA (brak csproj)
F5 (?:docs|tools|src)/ PRZED, bez \.                NIE         pelna lista                      zielona
F6 (?:\.(?:bak|orig))? PO rozszerzeniu              TAK         pelna lista                      zielona
F7 podzial z py, csproj, geojson w 1. czesci        TAK         geojson|csproj|jsonl|json|py     ZIELONA
F8 nowe sln|godot|cfg jako DRUGA grupa              NIE (+6)    pelna lista (bez sln|godot|cfg)  ZIELONA
F9 nowe sln|godot|cfg jako PIERWSZA grupa           NIE (+6)    sln|godot|cfg                    CZERWONA (brak csproj)
```

**Wzorzec raportów** (wyłuskanie B, obrona = `assert`):

```
wariant                                             sciezki     B zwraca                         assert
H1 podzial, kazda czesc z wlasnym \. (1. polowa)    TAK         py|cs|md|json|sh|yml             nie zapala sie
H2 podzial, kazda czesc z wlasnym \. (2. polowa)    TAK         yaml|txt|csproj|tscn|geojson|csv nie zapala sie
H3 podzial zagniezdzony pod jednym \.               TAK         py|cs|md|json|sh|yml             nie zapala sie
H4 (?:\.(?:min|test))? PRZED rozszerzeniem          TAK         min|test                         nie zapala sie
H5 (?:docs|tools|src)/ PRZED, bez \.                NIE         docs|tools|src                   nie zapala sie
H6 (?:\.(?:bak|orig))? PO rozszerzeniu              TAK         pelna lista                      nie zapala sie
H8 nowe sln|godot|cfg jako DRUGA grupa              NIE (+35)   pelna lista (bez sln|godot|cfg)  nie zapala sie
H9 nowe sln|godot|cfg jako PIERWSZA grupa           NIE (+35)   sln|godot|cfg                    nie zapala sie
```

Tabele są zestawieniem wypisu przyrządu; dosłowne wiersze dwóch par, które
rozstrzygają „wzięta albo pominięta zależnie od kolejności" — ten sam zbiór
rozszerzeń, zamieniona tylko kolejność grup:

```
-- F8 NOWE rozszerzenia drzewa jako DRUGA grupa, po dzisiejszej
   A na wariancie: geojson|csproj|jsonl|yaml|json|tscn|glb|yml|txt|png|csv|zip|log|sh|md|py|cs
   OBRONA test_wzorzec_golej_nazwy_dzieli_rozszerzenia_z_PATH_TOKEN: zielona
-- F9 NOWE rozszerzenia drzewa jako PIERWSZA grupa, przed dzisiejsza
   A na wariancie: sln|godot|cfg
   OBRONA test_wzorzec_golej_nazwy_dzieli_rozszerzenia_z_PATH_TOKEN: CZERWONA — AssertionError: wyciecie alternatywy z `PATH_TOKEN` nie dalo znanych rozszerzen: 'sln|godot|cfg'
-- H8 NOWE rozszerzenia drzewa jako DRUGA grupa, po dzisiejszej
   B na wariancie: py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv
   OBRONA assert w _rozszerzenia_we_wzorcu: nie zapala sie
   testy modulu, ktore zczerwienialy (0 z 23):
-- H9 NOWE rozszerzenia drzewa jako PIERWSZA grupa, przed dzisiejsza
   B na wariancie: sln|godot|cfg
   OBRONA assert w _rozszerzenia_we_wzorcu: nie zapala sie
```

Rozszerzenia `sln`, `godot` i `cfg` nie są wymyślone: to jedyne rozszerzenia plików
śledzonych przez git (poza `gitignore`), których nie zna żaden z dwóch wzorców.
Wariant F8 dokłada w `docs/TASKS.md` sześć adresów, oba istniejące
(`src/Game/export_presets.cfg`, `src/Game/project.godot`), a `BARE_TOKEN` żadnego
z nich nie widzi — dokładnie dwie listy, które 6.D187 zlikwidowało.

## 5. Odpowiedź trzecia: która obrona się zapala

**`assert` w `_rozszerzenia_we_wzorcu` nie zapala się ANI RAZU na dziewięciu
wariantach** (H0–H6, H8, H9). Pilnuje wyłącznie tego, że **jakaś** grupa
`(?:[a-z|]+)` istnieje — a wśród dopisań, które przyrząd spróbował, nie ma ani
jednego, które by ją usunęło. Przy wzorcu raportów łapie za to **inna** bramka:
równość `test_zestaw_rozszerzen_w_kodzie_i_we_wzorcu_JEST_TEN_SAM` z kopią
`ROZSZERZENIA_PILNOWANE` zczerwieniła się na H1, H2, H3, H4, H5 i H9 — zawsze, gdy
pierwsza grupa przestała być dzisiejszą listą. Milczy na H6 i H8, czyli wtedy, gdy
druga grupa stoi **po** pierwszej: jej rozszerzenia wypadają z pokrycia
`test_kazde_pilnowane_rozszerzenie_ma_zywe_trafienie_albo_jawny_wyjatek` po cichu,
choć wzorzec (H8) łapie przez nie 35 nowych ścieżek w raportach.

**Bramka w `test_field_paths.py` zapala się na F1, F2, F4 i F9**, ale z dwóch
różnych powodów: F2, F4 i F9 łapie jej pierwsza asercja (w wyłuskaniu nie ma
`csproj` albo `geojson`), a F1 — próbka syntetyczna z gołą nazwą `.py`, bo `py`
wypadło akurat do drugiej grupy. F7 pokazuje, że to drugie jest **przypadkiem
wyboru próbki**: ta sama konstrukcja, tylko z `py`, `csproj` i `geojson`
w pierwszej części, przechodzi bramkę na zielono. F3 nie dochodzi do bramki wcale
— import modułu pada na `.group(1)` z `None`, co jest głośne, ale nie jest obroną.

**Przemiatanie po jednym rozszerzeniu** mierzy, ile z tego jest ciche do końca:
każde z siedemnastu rozszerzeń wyniesione osobno do drugiej grupy, wzorzec ścieżek
w każdym przypadku identyczny z dzisiejszym, i liczba czerwonych testów w całym
module.

```
   geojson  sciezki identyczne=TAK  obrona=CZERWONA  czerwonych testow modulu=1
   csproj   sciezki identyczne=TAK  obrona=CZERWONA  czerwonych testow modulu=1
   yaml     sciezki identyczne=TAK  obrona=zielona   czerwonych testow modulu=0
   tscn     sciezki identyczne=TAK  obrona=zielona   czerwonych testow modulu=0
   yml      sciezki identyczne=TAK  obrona=zielona   czerwonych testow modulu=0
   zip      sciezki identyczne=TAK  obrona=zielona   czerwonych testow modulu=0
   log      sciezki identyczne=TAK  obrona=zielona   czerwonych testow modulu=0
   py       sciezki identyczne=TAK  obrona=CZERWONA  czerwonych testow modulu=5
   CALKIEM CICHE (zero czerwonych w module): 5 z 17: ['yaml', 'tscn', 'yml', 'zip', 'log']
```

(Wiersze pozostałych dziewięciu rozszerzeń — bramka zielona, czerwienią się
zapadki liczb gołych nazw — stoją w wypisie przyrządu i pomijam je tu dla
długości.) Obrona zapala się na **trzech z siedemnastu**: dokładnie na tych,
które nazywa jej asercja i jej próbka. Pięć z czternastu pozostałych nie zapala
**niczego** w module, a co z tego ginie, policzyłem na `docs/*.md`:

```
dzis: 2053 wystapien golych nazw w docs/*.md
   yaml  wariant: 2053  (utracone: 0; dzis z tym rozszerzeniem: 0)
   tscn  wariant: 2050  (utracone: 3; dzis z tym rozszerzeniem: 3)
   yml   wariant: 1999  (utracone: 54; dzis z tym rozszerzeniem: 54)
   zip   wariant: 2053  (utracone: 0; dzis z tym rozszerzeniem: 0)
   log   wariant: 2052  (utracone: 1; dzis z tym rozszerzeniem: 1)
```

Przy `yml` gołych nazw ubywa **54**, a zestaw zostaje zielony, bo próg
`MIN_GOLYCH_W_DOKUMENTACH` ma zapas, a równość `GOLYCH_BEZ_ODPOWIEDNIKA` liczy tylko
nazwy bez odpowiednika.

## 6. Wniosek: zagrożenie jest realne, nie teoretyczne

Blok tej pozycji dopuszczał odpowiedź „nie da się". Pomiar ją obala: druga grupa
`(?:…)` **mieści się** w obu wzorcach, i to na trzy sposoby, z których żaden nie
zmienia tego, co widzi sam wzorzec ścieżek — podział alternatywy (F1, F2, F7,
H1, H2), zagnieżdżenie (F3, H3) i opcjonalny człon przed albo po rozszerzeniu
(F4, F6, H4, H6). Wzorzec raportów **niesie drugą grupę już dziś** (§3). Kolejność
decyduje o tym, co zostaje wzięte (F8 wobec F9, H8 wobec H9), i §8 raportu 6.D343
opisuje więc kształt, który się **może** zdarzyć, a nie taki, który się nie zdarzy.

Z dwóch obron §8 **jedna nie zapala się nigdy** (`assert`), a druga zapala się
wtedy, gdy druga grupa zabiera `csproj`, `geojson` albo `py` — czyli tam, gdzie
akurat patrzy. Najcichszy przypadek realny to F8/H8: ktoś rozszerza wzorzec
ścieżek o nowy typ pliku, dopisując grupę **obok** zamiast wpisać rozszerzenie
do istniejącej — i obie listy pochodne nie dowiadują się o tym wcale.

## 7. Czego świadomie nie zrobiłem

Nie zmieniłem żadnego z dwóch `PATH_TOKEN`, nie dołożyłem warunku żadnej obronie
(np. „grupa `(?:[a-z|]+)` jest dokładnie jedna") i nie scaliłem dwóch wyłuskań
w jedno — wszystkie trzy stoją w polu „Poza zakresem". Warunek na liczbę grup
byłby zmianą bramki, czyli decyzją właściciela.

Nie oceniłem, czy różnica pięciu rozszerzeń między wzorcami jest zamierzona.
Pozycja pytała o wyłuskanie, a nie o skład list; zapisuję to jako nową pozycję
(§8).

Przyrząd nie wchodzi do commitu — leży w katalogu roboczym pozycji i uruchomiony
z korzenia drzewa odtwarza wszystkie wypisy tego raportu (drugi przebieg:
281,1 s).

## 8. Co zauważyłem przy okazji, ale nie tknąłem

**Dwa wzorce o jednej nazwie różnią się pięcioma rozszerzeniami**, i nie znalazłem
w drzewie zdania, które by tę różnicę uzasadniało: wzorzec pól kolejki zna `glb`,
`jsonl`, `log`, `png` i `zip`, wzorzec raportów nie zna żadnego z nich — więc
ścieżka `.log` albo `.png` w grawisach raportu nie jest sprawdzana, czy istnieje.
Ile takich ścieżek stoi dziś w `reports/*.md`, nie policzyłem. Zapisane jako
**6.D360**.
