# Triaż ocalałych mutacji: `tools/blender/clearance.py`

**Snapshot na commicie:** `5f6b68e` (stan przed triażem)
**Data:** 2026-09-03

Pierwszy moduł z kolejki triażu z `reports/mutation-sweep.md`. Wybrany nie dlatego, że
miał najwięcej ocalałych, tylko dlatego, że miał **najwyższy udział przy najmniejszym
rozmiarze**: 13 ocalałych na 14 mutacji, czyli 93 %. Mały moduł da się przejść pozycja
po pozycji i sprawdzić, czy metoda triażu w ogóle działa, zanim ruszy się na 425.

Moduł liczy, czy M7 mieści się w tunelu na łukach. Miał własne testy i to dobre —
sprawdzały wzór na strzałkę cięciwy, odtworzenie znanego okręgu i skrajnię na
zatwierdzonej osi. Żaden z nich nie dotykał **progów**.

## Wynik

| | przed | po |
|---|---|---|
| mutacji | 14 | 11 |
| zabitych | 1 | **5** |
| ocalałych | 13 | **6** |
| ocalałe uznane za usterkę | — | **0** |

Liczba mutacji spadła z 14 na 11, bo zniknęły dwie pozycje razem z **martwym
warunkiem** (niżej) i jedna razem ze strażnikiem `__main__`, wyciętym w narzędziu.

## Co się okazało usterką

### Martwy warunek w `circumradius`

```python
if area2 < 1e-12 or ab * bc * ca == 0.0:
    return None
```

Druga połowa tego warunku **nie mogła się nigdy wykonać**. Iloczyn `ab * bc * ca`
zeruje się tylko wtedy, gdy dwa z trzech punktów się pokrywają — a wtedy pole `area2`
też jest zerem i pierwszy warunek już odrzuca trójkę. Sprawdzone wprost: dla punktów
`(0,0), (0,0), (2,0)` wychodzi `area2 = 0.0` i `iloczyn = 0.0`, więc pierwszy warunek
łapie.

Przegląd mutacyjny pokazał to bez czytania kodu: mutacja `0.0 -> 0.001` w tym miejscu
**przeżywała**, bo nie da się jej zaobserwować. Martwy kod jest zawsze ocalałą mutacją.

Usunięty. To nie jest kosmetyka — warunek sugerował czytającemu, że istnieje wejście,
przed którym trzeba się bronić osobno.

### Trzy progi bez pokrycia

| miejsce | czego nie sprawdzał żaden test | dopisana kontrola |
|---|---|---|
| `versine`, promień niedodatni | testy podawały `None` i trafiały w gałąź `is None`, więc `radius_m <= 0.0` mogło mieć dowolny próg | promień `0.0` i `-5.0`, plus kontrola negatywna, że dodatni daje niezerową strzałkę |
| `circumradius`, próg `1e-12` | testy podawały punkty **dokładnie** współliniowe, więc `area2` wychodziło zerem i próg nie miał czego rozstrzygać | trójka o `area2 = 1,004e-12`, dobrana tak, żeby leżała **między** progiem a jego mutacją; obie strony przypięte |
| `_point_at`, krańce osi | kilometraż równy początkowi albo końcowi osi nie był sprawdzany wcale | oba krańce, węzeł wewnętrzny, interpolacja w środku, plus kontrola negatywna poza osią |
| `_point_at`, zerowe rozpięcie | powtórzony wierzchołek osi — bez strażnika `span <= 0.0` interpolacja dzieli przez zero | duplikat na **początku** osi (patrz niżej) |

**Duplikat musi stać na początku.** Pierwsza wersja tego testu miała powtórzony punkt
w środku osi i mutacji nie zabijała: pętla zwraca przy PIERWSZYM pasującym przedziale,
więc zdublowany wierzchołek w środku zawsze zostaje przykryty przez przedział
poprzedni. Gałąź zerowego rozpięcia jest osiągalna wyłącznie wtedy, gdy duplikat
stoi na samym początku.

## Co NIE jest usterką

Sześć ocalałych zostaje i tak ma zostać. Cztery są **dowodliwie równoważne** — nie
istnieje wejście, na którym dałoby się je odróżnić:

| miejsce | mutacja | dlaczego nieobserwowalna |
|---|---|---|
| `versine`, w. 47 | `<=` → `<` | przy promieniu `0.0` oryginał zwraca `0.0` przez strażnika, mutant przez gałąź `half >= radius_m` — ta sama liczba |
| `versine`, w. 50 | `>=` → `>` | przy `half == radius_m` oryginał zwraca `radius_m`, mutant liczy `radius_m - sqrt(r² - r²)` = `radius_m` |
| `circumradius`, w. 70 | `<` → `<=` | wymaga `area2` **dokładnie** równego `1e-12`; to pole liczone z współrzędnych, więc zbiór miary zero |
| `_point_at`, w. 99 | drugie `<=` → `<` | sprawdzone na całej dziedzinie: przedział półotwarty gubi tylko `target == stations[-1]`, a ten przypadek przechwytuje `return points[-1]` na końcu funkcji. Wyjście identyczne dla każdego wejścia |

Dwie są **równoważne w dziedzinie zadania** — formalnie da się je odróżnić, ale
wejściem, które w tym projekcie nie występuje:

| miejsce | mutacja | wejście rozróżniające | dlaczego nie piszę takiego testu |
|---|---|---|---|
| `versine`, w. 47 | `0.0` → `0.001` | promień z przedziału (0; 0,001] m | promień pół milimetra nie jest łukiem toru w żadnym sensie; `MIN_RADIUS_M` w tym module wynosi 20 m |
| `_point_at`, w. 101 | `0.0` → `0.001` | odcinek osi krótszy niż 1 mm | błąd wynikowy jest poddziałkowy wobec 0,25 m odchyłki, z jaką oś odwzorowuje łamaną STIB |

Dopisanie testu z absurdalnym wejściem tylko po to, żeby licznik ocalałych ładnie
wyglądał, byłoby **dopasowywaniem testu do narzędzia**. Klasyfikacja jest tańsza
i uczciwsza; dwa testy w `test_clearance.py` niosą tę informację w komentarzu, żeby
następny czytający nie próbował „naprawiać" tego samego drugi raz.

## Czego ten triaż uczy o metodzie

**Test, który wygląda na pokrycie progu, może nie dotykać tego progu wcale.** Pierwsze
podejście dopisało trzy testy — `versine` z promieniem zerowym, `circumradius` z trójką
prawie współliniową, granica nasycenia strzałki. Wyglądały dokładnie tak, jak powinny
wyglądać testy tych progów. Zabiły **zero** mutacji.

Dopiero policzenie, przy jakiej wartości oryginał i mutant się rozchodzą, pokazało, że
trzeba `area2` między `1e-12` a `1,01e-12`, a nie „prawie zera", i że duplikat musi stać
na początku osi, a nie w środku. Przegląd mutacyjny jest tu jedyną rzeczą, która
odróżnia test od jego pozoru.

Stąd zasada na resztę kolejki: **każdą dopisaną kontrolę mierzy się ponownie**, a nie
zakłada, że skoro dotyka funkcji, to coś w niej sprawdza.

---

# Triaż: `tools/blender/clearance_profile.py`

**Drugi moduł z kolejki.** 72 ocalałe na 77 mutacji (94 %) — najwyższy udział w całym
repo. Ten sam obszar co wyżej: luz M7 wzdłuż całej osi, tylko liczony wydajnie, z trzema
redukcjami zamiast naiwnego przebiegu po 5408 wierzchołkach na każdą pozycję.

## Wynik tego etapu

| | przed | po |
|---|---|---|
| zabitych | 7 | **11** |
| ocalałych | 72 | **66** |

Trzy dopisane testy zabiły cztery mutacje. **Zmierzone, nie założone** — po lekcji
z `clearance.py` każda kontrola idzie przez przegląd, zanim zostanie uznana za pokrycie.

## Co zostało domknięte

Strażniki **geometrii zdegenerowanej** w `hull_2d` i `halfplanes`, czyli w kodzie, który
odpowiada na pytanie „czy M7 mieści się w rurze". Jeżeli te bramki są nieszczelne, cała
reszta liczy się poprawnie na wejściu, które nie jest obrysem.

| kontrola | co łapie |
|---|---|
| otoczka trójkąta w obiegu przeciwnym do zegara | skrót `len(pts) <= 3` zwracałby punkty **posortowane leksykograficznie** zamiast po obiegu. `halfplanes` chodzi po pierścieniu i liczy normalne z kolejnych krawędzi — przy złej kolejności wyszłyby normalne skierowane **na zewnątrz** i luz zmieniłby znak |
| trójkąt jest poprawnym obrysem | mutacje `count < 3` -> `<= 3` i `3` -> `4` odrzucałyby go; kontrola negatywna pilnuje, że dwa punkty nadal są odrzucane |
| zdublowany wierzchołek | bez strażnika `length <= 0.0` normalna dzieli się przez zero i zamiast czytelnej odmowy leci `ZeroDivisionError` z wnętrza pętli |

## Klasyfikacja 66 pozostałych

| klasa | ile | co z tym |
|---|---|---|
| **strażnik zdegenerowany** | 19 | ta sama rodzina co domknięte wyżej — puste listy, zerowe kroki, jednoelementowe pierścienie. **Do zrobienia**, każdy wymaga wejścia dobranego pod konkretny warunek |
| **inne** | 16 | wymagają przeczytania funkcji po kolei; bez tego klasyfikacja byłaby zgadywaniem |
| **tolerancja numeryczna** | 11 | `1e-6`, `1e-9`, `1e-12` przesunięte o procent. Rozróżnia je wejście oddalone o mniej niż procent od tolerancji, czyli takie, którego geometria STIB nie produkuje. Klasa **równoważnych w dziedzinie** — do zapisania, nie do naprawiania |
| **próg klasyfikacji** | 11 | `ny >= 0.9` (która ściana wiąże), `clearance_m < threshold_m` (czy luz **dokładnie równy** dopuszczalnemu jest naruszeniem). To są prawdziwe pytania semantyczne i **wymagają rozstrzygnięcia**, a nie tylko testu |
| **remis przy minimum** | 9 | `if value < best` kontra `<=`. Przy remisie obie gałęzie dają tę samą **wartość**; różnią się tylko wyborem **indeksu**. Rozstrzygnięcie wymaga sprawdzenia, czy indeks jedzie dalej do raportu |

## Dlaczego to nie jest domknięte w jednym podejściu

66 pozycji po jednej mutacji na sztukę to sześć osobnych przeglądów mierzących skutek —
a lekcja z `clearance.py` mówi, że testu nie wolno uznać za pokrycie bez pomiaru.
Podział na klasy jest tu wynikiem samym w sobie: pokazuje, że **jedenaście** z tych
pozycji nie jest pytaniem o test, tylko o **decyzję**, czym ma być luz równy
dopuszczalnemu. Tego nie rozstrzyga się dopisaniem asercji.

## Etap drugi: klasa „strażnik zdegenerowany", 19 pozycji

**Data:** 2026-09-04
**Zmierzone na commitach:** `e982bc0` (przed) i **ten commit** (po) — oba przebiegi
`tools/tests/mutation_sweep.py --only clearance_profile.py`, 3 robotników.
Przebieg „po" wypisał `commit dfd403d`: to ten sam commit z dokładnie tym samym
drzewem testów, jeszcze przed dopisaniem tej sekcji do raportu. Przegląd czyta
kod pod testem i `tools/tests/`, `reports/` nie rusza, więc dopisanie sekcji
wyniku nie zmienia — przebieg na tym commicie da te same 28 i 49.

Podział z etapu wyżej odtworzony bez rozjazdu: narzędzie dało te same
**77 mutacji, 11 zabitych, 66 ocalałych**. Ocalałe rozpisane na klasy dają
dokładnie **19** pozycji strażnika zdegenerowanego i **47** pozostałych — obie
liczby z tabeli klasyfikacji zgadzają się z pomiarem, więc ten etap nie musiał
niczego naciągać. (Uwaga na liczenie: wiersz 643 nosi DWIE mutacje `<=` -> `<`
w porównaniu łańcuchowym `first <= r <= last`, więc zbiór par „wiersz + zmiana"
ma 65 elementów, nie 66.)

### Wynik

| | przed | po |
|---|---|---|
| mutacji | 77 | 77 |
| rozstrzygniętych | 77 | 77 |
| zabitych | 11 | **28** |
| ocalałych | 66 | **49** |
| pokrycie | 14,3 % | **36,4 %** |
| ocalałe w klasie „strażnik zdegenerowany" | 19 | **2** |

Piętnaście dopisanych testów zabiło **17 z 19** pozycji. Dwie zostały i obie są
wynikiem, nie brakiem: jedna jest zmierzoną równoważnością, druga wymaga decyzji
właściciela. Pozostałe 47 pozycji jest nietkniętych — z założenia.

### Zabite, pozycja po pozycji

| wiersz | mutacja | wejście, które ją rozstrzyga | test |
|---|---|---|---|
| 119 | `0.0` -> `0.001` | dwa wierzchołki 0,5 mm od siebie przy `bucket_m = 0,001`: kubełek daje 1 pasmo, pasma dokładne 2 | `..._positive_bucket_still_buckets_when_it_is_tiny` |
| 174 | `0.0` -> `0.001` | trójkąt 2 cm x 2 cm, `area2 = 4e-4` — orientacja brana z WIELKOŚCI pola wywraca normalne i obrys wypada jako wklęsły | `..._orientation_follows_the_sign_of_the_area_not_its_size` |
| 185 | `0.0` -> `0.001` | obrys z krawędzią 0,5 mm; strażnik broni przed dzieleniem przez zero, nie przed krótkim odcinkiem | `..._halfplanes_accept_a_half_millimetre_edge` |
| 237 | `>` -> `>=` | podpowiedź 1000 m na osi 400 m: mutant wychodzi z pętli natychmiast i zwraca indeks WSTAWIENIA 81 przy 81 ramkach | `..._nearest_frame_ignores_a_hint_off_the_axis` |
| 240 | `>` -> `>=` | oś [0; 1] (limit 8,0), okno 4,0 z podpowiedzią 6,0 rośnie do 8,0 — dokładnie do limitu | `..._nearest_frame_accepts_a_window_grown_to_the_limit` |
| 382 | `<=` -> `<` | `scan_positions(1000, 94, 0.0)`: oryginał odmawia, mutant leci `ZeroDivisionError` | `..._scan_positions_refuses_a_zero_step` |
| 382 | `0.0` -> `0.001` | krok 0,001 m: 1001 pozycji na zapasie 1 m | `..._scan_positions_accept_a_millimetre_step` |
| 385 | `<=` -> `<` | oś 94 m i skład 94 m: oryginał odmawia, mutant zwraca profil z jednej pozycji | `..._scan_positions_refuse_a_train_as_long_as_the_axis` |
| 385 | `0.0` -> `0.001` | oś 94,0005 m: zapas 0,5 mm jest zapasem, nie odmową | `..._scan_positions_accept_half_a_millimetre_of_room` |
| 544 | `<=` -> `<` | zdublowany OSTATNI wierzchołek osi (niżej, dlaczego ostatni); mutant leci `ZeroDivisionError` | `..._point_at_survives_a_duplicated_last_vertex` |
| 544 | `0.0` -> `0.001` | odcinek osi 0,5 mm, chainage 0,00025: oryginał interpoluje, mutant zwraca lewy koniec | `..._point_at_interpolates_inside_a_half_millimetre_span` |
| 605 | `<` -> `<=` | `support_directions(3)` — komunikat mówi „co najmniej 3" | `..._support_directions_accept_exactly_three` |
| 605 | `3` -> `4` | to samo wejście | jak wyżej |
| 682 | `<` -> `<=` | obrys podparcia z DOKŁADNIE trzech kierunków ma trzy wierzchołki | `..._support_polygon_from_three_directions_is_a_triangle` |
| 682 | `3` -> `4` | to samo wejście | jak wyżej |
| 692 | `<` -> `<=` | rura z DOKŁADNIE dwóch pierścieni: 8 wierzchołków, 4 ściany boczne, 2 zaślepki | `..._swept_mesh_from_exactly_two_rings` |
| 692 | `2` -> `3` | to samo wejście | jak wyżej |

Każdy z tych testów ma kontrolę negatywną albo drugą asercję po przeciwnej
stronie progu — rozluźnienie progu nie ma się zamienić w brak progu.

### Zerowe rozpięcie `point_at`: duplikat musi stać na KOŃCU

Etap wyżej zapisał, że w `clearance._point_at` duplikat wierzchołka musi stać
na POCZĄTKU osi, bo pętla zwraca przy pierwszym pasującym przedziale. W
`clearance_profile.point_at` jest **odwrotnie**:

```python
index = min(max(0, bisect.bisect_right(stations, value) - 1), len(points) - 2)
```

`bisect_right` zwraca pozycję ZA wszystkimi wpisami równymi wartości, więc
duplikat na początku albo w środku jest przeskakiwany i rozpięcie wychodzi
dodatnie. Zerowe wychodzi dopiero wtedy, gdy przycięcie do `len(points) - 2`
wskaże ostatnią, zdublowaną parę. Zmierzone na obu wejściach:

| oś | oryginał | mutant `span < 0.0` |
|---|---|---|
| duplikat na KOŃCU, `stations = [0, 5, 10, 10]`, chainage 10 | `(10.0, 0.0, 0.0)` | `ZeroDivisionError` |
| duplikat na POCZĄTKU, `stations = [0, 0, 5, 10]`, chainage 0 | `(0.0, 0.0, 0.0)` | `(0.0, 0.0, 0.0)` |

Lekcja jest ogólniejsza niż „duplikat na początku": **wejście zdegenerowane
dobiera się pod sposób wyznaczania indeksu**, a nie przepisuje z modułu obok.
Oba wejścia stoją w teście, to drugie z komentarzem, że warunku NIE uruchamia.

### Dwie pozycje bez testu — i dlaczego to wynik

**Wiersz 91, `len(pts) <= 2` -> `< 2` w `hull_2d`: mutant równoważny.**
Nie orzeczone z lektury kodu. Oryginał i mutant przepuszczone obok siebie przez
200 000 losowych zbiorów punktów, z osobnym licznikiem trafień w próg:

```
91 <=->< : wejść trafiających w próg (len(set)==2) DOKŁADNIE: 99840; różniących wynik: 0
      pasmo o DWÓCH punktach w rzeczywistym przebiegu `candidate_bands`: identyczne
```

Próg jest więc osiągalny — 99 840 trafień, w tym w przebiegu `candidate_bands`
na paśmie o dwóch punktach — a wynik nie różni się ani raz: dla pary punktów
łańcuch monotoniczny zwraca `lower[:-1] + upper[:-1]`, czyli tę samą parę w tej
samej kolejności, co skrót. Test zdegenerowanej otoczki (0, 1, 2 punkty i punkt
zdublowany) jest dopisany jako pokrycie samego zejścia, z tym pomiarem
w docstringu — nie jako zabójca mutacji.

**Wiersz 174, `area2 > 0.0` -> `>= 0.0`: potrzebna decyzja właściciela.**
Ta mutacja rozstrzyga się WYŁĄCZNIE na pierścieniu o polu dokładnie zerowym,
czyli na trójce współliniowej — a `halfplanes` takiego pierścienia nie odrzuca,
choć odrzuca zerową krawędź. Zmierzone na siatce 41 x 41 punktów:

```
174 >->>= : pierścień o polu DOKŁADNIE 0 (trzy punkty współliniowe)
      punktów sprawdzonych: 1681; identyczny LUZ: 1681; identyczna ETYKIETA: 1640
      największa różnica luzu: 0.0
      największy luz w oryginale: -0.0
      normalne orig   = [(0.0, -1.0, 0.0), (0.0, -1.0, 0.0), (0.0, 1.0, 0.0)]
      normalne mutant = [(-0.0, 1.0, 0.0), (-0.0, 1.0, 0.0), (-0.0, -1.0, -0.0)]
```

Luz liczony przez `clearance_in_planes` jest identyczny we wszystkich 1681
punktach, a największy luz w takim pierścieniu wynosi -0,0 — wnętrza nie ma,
więc nie ma czego mierzyć. Różni się tylko **etykieta** wiążącej krawędzi,
w 41 punktach na 1681. Zabicie tej mutacji wymagałoby albo przypięcia dowolnej
konwencji znaku na wejściu bez wnętrza, albo **nowego strażnika** odrzucającego
pierścień o zerowym polu — a to zmiana kontraktu modułu, czyli decyzja
właściciela, nie asercja. §8: zatrzymanie na tej pozycji jest wynikiem pracy.

### Czego ten etap nie tknął

- **47 pozostałych ocalałych.** W szczególności 11 pozycji klasy „próg
  klasyfikacji" (`ny >= 0.9`, `clearance_m < threshold_m`) — pytania semantyczne,
  nadal czekające na rozstrzygnięcie, a nie na test.
- **Martwego kodu w tych 19 pozycjach nie ma**, inaczej niż w `circumradius`
  z etapu wyżej, więc `clearance_profile.py` wychodzi z tego etapu bez jednej
  zmiany. Osobna obserwacja, nietknięta: `SweptEnvelope.rings` odsiewa wiersze
  z `-inf`, a `add` wypełnia wszystkie gniazda przy pierwszym wywołaniu, więc
  ten warunek nie ma jak być prawdziwy. Mutacja `==` -> `!=` stoi tam **zabita**
  (mutant zwraca puste pierścienie), więc do klasy ocalałych nie należy.
- **Dwa strażniki zdegenerowane, których żadna mutacja nie pokrywa.** Wiersz 580
  (`norm(chord) < 1e-9`) i 679 (`abs(det) < 1e-12`): dla wejścia zdegenerowanego
  — zerowej cięciwy, równoległych kierunków — prawdziwe są wszystkie trzy
  warianty (`0 < 1e-9`, `0 <= 1e-9`, `0 < 1,01e-9`). Ich mutacje rozstrzygają
  się dopiero na wartości równej tolerancji z dokładnością do procenta, więc
  siedzą w klasie „tolerancja numeryczna", a nie tutaj. Test na samo wejście
  zdegenerowane nic by w przeglądzie nie ruszył i dlatego go nie ma.


## Etap trzeci: reszta ocalałych — trzy klasy, 44 → 17

**Data:** 2026-09-04
**Zmierzone na commitach:** `8a02538` (przed) i `68da7da` (po) — oba przebiegi
`tools/tests/mutation_sweep.py --only clearance_profile.py --workers 3`, każdy
z własnym dziennikiem. Przebieg „po" stoi na commicie z dokładnie tym samym
drzewem testów, co ten; ta sekcja doszła po nim, a przegląd czyta kod pod testem
i `tools/tests/`, więc `reports/` nie zmienia wyniku.

### Punkt odniesienia się NIE zgadza z tym z `docs/24`, i to jest wyjaśnione

Pomiar końcowy pozycji 12 (`docs/24`) podawał na `c82157f` **76 mutacji, 28 zabitych,
48 ocalałych**. Na dzisiejszym `main` (`8a02538`) wychodzi **76 / 32 / 44**. Różnica
nie jest szumem i ma dwa niezależne powody, oba zmierzone:

**1. #203 (scalone jako `8a02538`) dołożyło cztery zabicia.** Zbiór mutacji ma nadal
76 pozycji, ale jego SKŁAD się zmienił — porównanie AST obu wersji modułu:

```
c82157f mutacji: 76   c87576a mutacji: 76
  ('<', '<='): 22 -> 21
  ('<=', '<'): 16 -> 17
```

`critical_places` przestało porównywać `clearance_m < threshold_m` wprost i woła
`at_or_below_threshold`, a doszły dwie funkcje pasma (`within_threshold_band`,
`at_or_below_threshold`), każda z własnym `<=`. Cztery testy pasma ±1 mm z #203
zabijają je razem ze starym warunkiem.

**2. Jedno z tych 32 zabić było FAŁSZYWE.** Dziennik przebiegu „przed" pokazuje, że
mutację `w.142 '<=' -> '<'` uznano za zabitą, bo padł jeden test — i **nie był to
test tego modułu**:

```
w.142 <= -> < : przezyla False, kod 1,
                padly ['test_ci_blender_installer_refuses_a_tarball_whose_checksum_does_not_match']
```

Ta mutacja jest tą samą, którą etap drugi zmierzył jako **równoważną** (99 840 trafień
w próg `len(set) == 2`, zero różnic w wyniku), więc zabita być nie mogła. Uczciwy punkt
odniesienia to zatem **31 zabitych i 45 ocalałych**, a nie 32 i 44 — i tak jest liczony
niżej. Przyczyna flaka jest wypisana na końcu tej sekcji.

### Wynik

| | przed (`8a02538`) | po (`68da7da`) |
|---|---:|---:|
| mutacji | 76 | 76 |
| rozstrzygniętych | 76 | 76 |
| zabitych, surowo z narzędzia | 32 | **59** |
| z tego zabić fałszywych (flak) | 1 | **0** |
| zabitych, uczciwie | 31 | **59** |
| **ocalałych** | **45** | **17** |
| pokrycie | 40,8 % | **77,6 %** |

Dwadzieścia nowych testów w `tools/tests/test_clearance_profile.py` zabiło
**28 mutacji**. Modułu nie tknięto ani w jednym miejscu — cała zmiana to testy
i `docs/24`.

Siedemnaście ocalałych rozkłada się bez reszty na **dziewięć zmierzonych
równoważności** i **osiem pytań do właściciela**, z czego siedem stało w `docs/24`
już wcześniej, a jedno doszło dziś jako pozycja 13.

### Metoda: zero trafień w próg to dowód luki, nie równoważności

Ta zasada nie jest tu ozdobą — zadziałała dwa razy w tej samej sesji.

**Raz na plus.** Mutacja `value < best` -> `<=` w `clearance_in_planes`: 200 000
losowych punktów w prawdziwym profilu `box_double` trafiło w remis półpłaszczyzn
**DOKŁADNIE ZERO razy**. Samo próbkowanie orzekłoby więc równoważność. Wystarczyło
podać kwadrat, żeby trafiać w 25 % przypadków — 50 023 remisy na 200 000 — i etykieta
wiążącej krawędzi różniła się we **wszystkich 50 023**.

**Raz na minus.** Mutacja `>` -> `>=` w progu ogona osi (`w.470`): tu zero trafień
na 300 000 wejść nie było lukę pomiaru, tylko prawdą — i dowodzi tego argument,
a nie próbkowanie. Ogon jest różnicą `last` i `round(count * step, 6)`, a `fl(1e-9)`
nie jest wielokrotnością odstępu double przy realnym kilometrażu:

```
(0,5   + 1e-9) - 0,5   = 9.999999717180685e-10   != 1e-9
(94,0  + 1e-9) - 94,0  = 1.0000036354540498e-09  != 1e-9
(6700  + 1e-9) - 6700  = 1.000444171950221e-09   != 1e-9
```

Zostaje `out[-1] == 0.0`, czyli oś rzędu nanometra. Różnica między tymi dwoma
przypadkami jest cała w tym, że drugi ma **wypisany warunek osiągalności progu**,
a nie tylko liczbę prób.

### Klasa „remis przy minimum": 9 pozycji, 7 zabitych

Raport klasyfikował ją jednym zdaniem: „różnią się tylko wyborem indeksu,
rozstrzygnięcie wymaga sprawdzenia, czy indeks jedzie dalej do raportu". Pomiar
pokazał, że **klasa nie jest jednorodna** — w siedmiu miejscach jedzie, w dwóch nie.

| wiersz | co wybiera indeks | co się zmienia przy remisie | trafień w remis | test |
|---|---|---|---:|---|
| 298 | wiążąca półpłaszczyzna | `bound_by` w każdym rekordzie i w `bound_by_counts`: `podłoga` -> `ściana` | 50 023 / 200 000 (kwadrat); **0** / 200 000 (`box_double`) | `..._a_tie_between_planes_picks_the_first_edge_in_ring_order` |
| 329 | ramka pasma | zwracany INDEKS: 0 -> 1 | 9 935 / 50 000 | `..._a_tie_between_frames_keeps_the_earlier_frame` |
| 418 | najgorszy kandydat | punkt styku w `min_at`: chainage 100,0 -> 115,0, lateral +1,35 -> −1,35 | remis w każdej pozycji na prostej | `..._a_tie_in_the_worst_candidate_keeps_the_first_vertex` |
| 447 | to samo, przebieg naiwny | chainage 100,0 -> 115,0 — czyli `--verify-full` porównywałby dwa różne punkty | jak wyżej | `..._a_tie_in_the_naive_measurement_keeps_the_first_vertex` |
| 569 | najbliższa stacja | NAZWA w raporcie: „A" -> „B" przy odległości 100 m po obu stronach | 276 / 50 000 | `..._a_tie_between_stations_names_the_earlier_one` |
| 666 | kilometraż minimalnego promienia | miejsce najciaśniejszego łuku: 5,0 -> 25,0 przy promieniu 3,125 co do bitu | 5 / 5 (oś o stałym promieniu) | `..._a_tie_in_the_minimum_radius_keeps_the_first_chainage` |
| 835 | najgorszy wierzchołek obwiedni | `where`: lateral +1,0 -> −1,0 | 2 / 4 | `..._a_tie_in_the_envelope_clearance_keeps_the_first_vertex` |

**Remis konstruuje się pod sposób wybierania, nie pod funkcję.** Trzy przykłady z tej
tabeli, bo każdy wymagał innego pomysłu:

- w.298 — środek kwadratu remisuje na czterech krawędziach naraz; prawdziwy profil
  tunelu nie remisuje nigdy, bo nie jest symetryczny w pionie.
- w.329 — punkt DOKŁADNIE w połowie między dwiema ramkami: `|along|` wynosi 2,5
  do jednej i do drugiej, i to jest równość **co do bitu**, nie przybliżenie.
- w.666 — oś ze zygzaka o odcinkach (3, 4). Długość odcinka to dokładnie 5,0, więc
  kilometraże wychodzą całkowite (`[0, 5, 10, 15, 20, 25, 30]`), `point_at` na
  kilometrażu ±5 m trafia w węzeł bez interpolacji i wszystkie pięć promieni
  wychodzi `3.125` co do bitu. Na łuku okręgu ten sam pomysł daje jedno trafienie
  na 55 — zaokrąglenie kilometraży rozstrzyga remis za nas.

#### Dwie pozycje, które zostają — z liczbą

**w.407, wybór ramki dla pojedynczego wierzchołka: równoważna, 854 trafienia.**
Remis jest tu częsty (2 480 trafień w 400 pozycjach na prostej, 854 w przeszukaniu
osi łamanych o różnych kątach), a wyjście różni się **najwyżej o 8,88e-16 m**.
Powód jest algebraiczny i też zmierzony: na odcinku prostym `band_coefficients`
dwóch sąsiednich ramek dają identyczne chainage, lateral i vertical — różnica 0,0
na 15 porównaniach — bo przesunięcie początku ramki wzdłuż stycznej znosi się
z przyrostem kilometrażu. Osiem femtometrów przy mikrometrze, w którym `statistics`
zapisuje minimum, to dziesięć rzędów zapasu.

**w.755, `if value > row[slot]`: równoważna bez potrzeby szukania wejścia.**
Przy remisie gałąź przypisuje wartość **równą tej, która już stoi w gnieździe** —
żaden indeks się nie wybiera. Zmierzone i tak: 40 001 remisów `value == row[slot]`
na 200 000 losowych par, `heights` i `rings()` identyczne po 4 000 próbkach,
a próbka podana dwa razy daje ten sam słownik wysokości.

### Klasa „tolerancja numeryczna": 13 pozycji, 8 zabitych

**Klasyfikacja z raportu była w części nieprawdziwa i to trzeba zapisać wprost.**
Raport pisał: „rozróżnia je wejście oddalone o mniej niż procent od tolerancji, czyli
takie, którego geometria STIB nie produkuje. Klasa równoważnych w dziedzinie — do
zapisania, nie do naprawiania". Sprawdzenie pokazało, że **pięć progów jest osiągalnych
DOKŁADNIE, i to wejściem, które nie jest absurdalne**: `coverage_gaps`,
`support_polygon` i `envelope_contains` są funkcjami czystymi, którym próg podaje się
wprost na wejściu, a nie przez geometrię osi.

| wiersz | próg | wejście trafiające DOKŁADNIE | co robi mutant |
|---|---|---|---|
| 481 | `abs(starts[0]) > 1e-6` | `starts[0] = 1e-6` | zgłasza „pierwsza pozycja czoła w 1e-06 m, nie w 0" |
| 481 | `1e-6` -> `1,01e-6` | `starts[0] = 1,005e-6` | PRZESTAJE zgłaszać pozycję, która jest za daleko |
| 484 | `abs(starts[-1] - koniec) > 1e-6` | `starts[-1] = 1e-6` przy oczekiwanym 0,0 | zgłasza problem, którego nie ma |
| 484 | `1e-6` -> `1,01e-6` | `starts[-1] = 1,005e-6` | przestaje zgłaszać |
| 487 | `b - a > step_m + 1e-6` | `a = 0,0`, `b = 5,000001` | zgłasza „dziurę 5,000 m", której nie ma |
| 781 | `abs(det) < 1e-12` | `det((1, 0), (1, 1e-12)) == 1e-12` | pomija wierzchołek: 5 -> 4 |
| 781 | `1e-12` -> `1,01e-12` | `det == 1,005e-12` | to samo, o krok dalej |
| 857 | `odległość < -tolerance_m` | punkt `2**-20` poza kwadratem przy `tolerance_m = 2**-20` | liczy próbkę jako leżącą poza obwiednią |

#### `docs/24` pozycja 6 potwierdza się liczbą, i to w dwie strony

Tamta pozycja pytała, czy `1e-6` ma zostać, czy zmienić się na potęgę dwójki, bo
`1e-6` przy dużym kilometrażu jest po jednej stronie granicy, a przy małym po drugiej.
Ten etap dostarcza dwa niezależne pomiary tego samego zjawiska:

```
w.487, czy b - a jest DOKŁADNIE równe step + 1e-6:
    a =    0,0   b-a = 5.000001              == 5.000001 : True
    a =    5,0   b-a = 5.000000999999999     == 5.000001 : False
    a = 6700,0   b-a = 5.0000010000003385    == 5.000001 : False
  300 000 losowych par (a, a + step + 1e-6): trafień w równość 135, WSZYSTKIE przy a = 0

w.857, czy odległość od obrysu jest DOKŁADNIE równa tolerancji:
    punkt (1 + 2**-20, 0) -> -9.5367431640625e-07   == -2**-20 : True
    punkt (1 + 1e-6,   0) -> -9.999999999177334e-07 == -1e-6   : False
  200 000 losowych punktów: trafień w -1e-6 ZERO, w -2**-20 trafia się co do bitu
```

Rekomendacja techniczna z pozycji 6 (potęga dwójki) jest więc nie tylko czystsza —
jest **jedyną, którą da się przypiąć testem przy niezerowej podstawie**. To nadal
pytanie o zmianę wartości progu, więc rozstrzygnięcia nie wyprzedzam; test w.857
podaje `tolerance_m = 2**-20` jako ARGUMENT, nie zmienia stałej.

#### Dwie tolerancje naprawdę nieosiągalne — z warunkiem, nie z liczby prób

**w.470, ogon osi (`1e-9`).** Zero trafień na 300 000 losowych trójek (oś 200-7000 m,
skład 15-94 m, krok 0,25-5 m) plus warunek wypisany wyżej: przy `count > 0` różnica
NIE MOŻE wyjść `fl(1e-9)`, bo `fl(1e-9)` nie jest wielokrotnością odstępu double
w tym rzędzie. Jedyne wejście trafiające to `scan_positions(2e-9, 1e-9, 1.0)` —
oś dwóch nanometrów. Test przybija to, po co ten próg stoi (ogon pokryty i NIE
zdublowany), a nie samą granicę.

**w.682, cięciwa zerowa (`1e-9`).** Tu próg JEST trafialny co do bitu: na osi prostej
cięciwa od 0 do 1e-9 daje wektor `(1e-09, 0.0, 0.0)` i normę dokładnie `1e-9`.
Tylko że po obu stronach progu wychodzi **to samo zero** — oryginał zwraca 0,0
przez strażnika, mutant `<=` zwraca 0,0 licząc. Mutacja progu (`1e-9` -> `1,01e-9`)
rozróżnia się dopiero na łuku i daje różnicę 1,8e-15 m, czyli 2 femtometry, przy
cięciwie bryły M7 wynoszącej 15,12 m. Na łuku norma nie trafia w próg ani razu
(0 na 200 000 par kilometraży), bo `frame_at` interpoluje.

### Klasa „inne": 15 pozycji, 13 zabitych

| wiersz | mutacja | co rozstrzyga | test |
|---|---|---|---|
| 150 | `<=` -> `<` | wierzchołek DOKŁADNIE na krawędzi otoczki zostaje w otoczce | `..._hull_drops_a_collinear_point_on_the_lower_chain` |
| 150 | `0.0` -> `0.001` | wierzchołek o zakręcie 0,0005 wypada z otoczki | `..._hull_keeps_a_lower_vertex_below_one_millimetre_of_turn` |
| 155 | `<=` -> `<` | to samo w łańcuchu GÓRNYM | `..._hull_drops_a_collinear_point_on_the_upper_chain` |
| 155 | `0.0` -> `0.001` | to samo, próg | jak wyżej |
| 515 | `<=` -> `<` | dwa okna DOKŁADNIE styczne przestają się scalać: `[(-4,12)]` -> `[(-4,4), (4,12)]` | `..._touching_refine_windows_merge_into_one` |
| 560 | `<` -> `<=` | luz DOKŁADNIE 0 liczony jako pozycja ujemna | `..._zero_clearance_is_not_counted_as_negative` |
| 560 | `0.0` -> `0.001` | luz 0,5 mm liczony jako pozycja ujemna | jak wyżej |
| 661 | `<` -> `<=` | kilometraż równy połowie cięciwy pomijany: 5,0 -> 10,0 | `..._min_radius_includes_the_chainage_exactly_at_half_chord` |
| 661 | `>` -> `>=` | kilometraż `total - half` pomijany: (25,0; 3,125) -> (20,0; 7,906) | `..._min_radius_includes_the_last_admissible_chainage` |
| 742 | `<` -> `<=` | próbka na `low_m` nie wnosi się do żadnego pierścienia: `(1, 2)` -> `()` | `..._envelope_rings_include_both_range_ends` |
| 742 | `>` -> `>=` | to samo na `high_m`: `(5, 6)` -> `()` | jak wyżej |
| 745 | `<=` -> `<` (lewa) | pierścień o indeksie `first` wypada: `(2, 3)` -> `(3,)` | `..._envelope_rings_include_the_first_and_last_ring_index` |
| 745 | `<=` -> `<` (prawa) | pierścień o indeksie `last` wypada: `(5, 6)` -> `(5,)` | jak wyżej |

**Dwa łańcuchy otoczki to dwie osobne bramki, i to trzeba było zmierzyć.** Wejście
współliniowe na DOLE zmienia otoczkę pod mutacją w.150 i nie zmienia jej pod w.155;
na GÓRZE odwrotnie. Jedno wejście dawałoby więc pokrycie jednej z dwóch bramek
i wyglądałoby dokładnie tak, jakby dawało pokrycie obu. Trafienia w próg policzone:
na 200 000 losowych zbiorów na siatce 4x4 trójka o zakręcie DOKŁADNIE zero wypadła
49 621 razy, a otoczka różniła się w 22 482.

**Wiersz 745 nosi DWIE mutacje** — `self.first <= r <= self.last` to porównanie
łańcuchowe i narzędzie liczy każdy operator osobno. Obie zabija ten sam test, ale
osobnymi asercjami: lewą przy chainage na początku zakresu, prawą na końcu.

#### Dwie pozycje „inne", które zostają

**w.405 `<` -> `<=`: `if along < 0.0: along = -along`, czyli ręczna wartość bezwzględna.**
Mutant podstawia `-0.0` zamiast `0.0`. `-0.0 == 0.0` jest prawdą, `-0.0 < 0.0`
fałszem, a `along` nie jedzie dalej niż do porównania `along < closest` — więc
podmiana jest nieobserwowalna. Zmierzone: `along == 0.0` wypadło **DOKŁADNIE
1 488 razy** w 120 pozycjach na osi prostej i rekord nie różnił się ani razu.

**w.405 `0.0` -> `0.001`: równoważna w dziedzinie, z warunkiem.** Mutant negowałby
każdy `along` poniżej milimetra, a różnica wymaga **DWÓCH kandydatów bliżej niż
milimetr od swoich kilometraży**. Kandydaci to sąsiednie pierścienie osi, czyli 5 m
od siebie — zmierzone: **0 takich par na 24 800 sprawdzonych wierzchołków**. Na osi
zdegenerowanej (łuk R = 0,01 m, pierścienie co 0,5 mm) różnica pojawia się w 7 z 8
pozycji i wynosi 2,47e-05 m, ale `MIN_RADIUS_M` w tym repozytorium to 20 m.

### Co zostało wypisane jako pytanie, a nie rozstrzygnięte

**w.262, `turn < -CONVEXITY_EPS`** — nowa pozycja **13** w
`docs/24-clearance-profile-decisions.md`. `CONVEXITY_EPS` jest w `halfplanes` użyta
dwa razy, o osiemnaście wierszy od siebie, i odchyłka DOKŁADNIE równa tolerancji
trafia w tych dwóch miejscach po przeciwnych stronach granicy: pole obrysu na progu
**odrzuca** (`<=`, przybite testem w #197 na mocy decyzji z pozycji 12), a zakręt na
progu **przyjmuje** (`<`). Oba wejścia skonstruowane co do bitu — obrys
`[(0,0), (1,0), (2,-1e-9), (3,0), (3,2), (0,2)]` ma najmniejszy zakręt równy `-1e-9`
i `area2 = 12.000000002`, więc jest obrysem, a nie geometrią zdegenerowaną.

To jest ten sam kształt pytania, co pozycja 4: ta sama stała, ta sama jednostka,
przeciwna konwencja na granicy. Przypięcie w.262 testem **bez odpowiedzi**
zabetonowałoby zachowanie, którego nikt nie wybrał — czyli dokładnie to, przed czym
`docs/24` ostrzega we wstępie. `CLAUDE.md` §8: zatrzymanie się tutaj jest wynikiem.

Konsekwencja dla dzisiejszych danych: **zerowa.** Najmniejszy zakręt w `profiles.py`
to `bore_single` z 0,0606 — 7,8 rzędu powyżej progu.

### Siedemnaście ocalałych, bez reszty

| wiersz | mutacja | status |
|---|---|---|
| 142 | `<=` -> `<` | zmierzona równoważność (etap drugi: 99 840 trafień, 0 różnic) |
| 262 | `<` -> `<=` | **pytanie do właściciela — `docs/24` pozycja 13** |
| 277 | `<=` -> `<` | `docs/24` pozycja 1, otwarta |
| 279 | `>=` -> `>` | `docs/24` pozycja 1, otwarta |
| 279 | `0.9` -> `0.909` | `docs/24` pozycja 1, otwarta |
| 281 | `>=` -> `>` | `docs/24` pozycja 2, otwarta |
| 281 | `0.9` -> `0.909` | `docs/24` pozycja 2, otwarta |
| 405 | `<` -> `<=` | zmierzona równoważność (1 488 trafień, 0 różnic) |
| 405 | `0.0` -> `0.001` | równoważna w dziedzinie (0 par na 24 800 wierzchołków) |
| 407 | `<` -> `<=` | zmierzona równoważność (854 trafienia, różnica ≤ 8,88e-16 m) |
| 470 | `>` -> `>=` | równoważna w dziedzinie (0 / 300 000 + warunek osiągalności) |
| 470 | `1e-9` -> `1,01e-9` | jak wyżej |
| 586 | `<=` -> `<` | `docs/24` pozycja 8, otwarta |
| 612 | `<=` -> `<` | `docs/24` pozycja 5, otwarta |
| 682 | `<` -> `<=` | zmierzona równoważność (próg trafiony, po obu stronach 0,0) |
| 682 | `1e-9` -> `1,01e-9` | równoważna w dziedzinie (2 femtometry na cięciwie 1 nm) |
| 755 | `>` -> `>=` | równoważność dowodliwa (przypisanie wartości równej) |

Dziewięć równoważności, osiem pytań. **Żadna ocalała nie jest już nierozpoznana.**

### Zauważone przy okazji, nietknięte — **ZAMKNIĘTE 04.09.2026 przez #207**

> **Ten akapit jest przepisany, a nie dopisany obok.** Jego poprzednia wersja kończyła
> się zdaniem „`tools/tests/test_ci_workflows.py` jest poza zakresem tego zadania, więc
> nie ruszony. Poprawka jest jednozdaniowa (katalog tymczasowy zamiast `/tmp` na stałe)"
> — i **to już nieprawda**. Poprawka weszła tego samego dnia jako #207 (`afefc2e`,
> gałąź `7368ad9`), czyli o jedno scalenie po #206, w którym ten raport powstał.
> Zapis o „poprawce, która czeka" wysyłałby dziś kolejną sesję do roboty leżącej
> w `main`. Opis usterki niżej zostaje w czasie przeszłym, bo to on tłumaczy, skąd
> w tabeli „przed" wzięło się jedno fałszywe zabicie.
>
> Czego dokładnie nie ma już w kodzie, sprawdzone lekturą `tools/tests/test_ci_workflows.py`
> na `9f4ae98`: stałej `FAKE_BLENDER_VERSION` nie ma wcale, a wersję atrapy wydaje
> funkcja `fake_blender_version()` zwracająca `0.<secrets.randbits(24)>.<secrets.randbits(24)>`,
> czyli inną ścieżkę w `/tmp` dla **każdego wywołania**. Pilnuje tego osobny test
> `test_ci_blender_fake_version_is_unique_so_the_gate_cannot_race_itself`. Pierwsza
> wersja tamtej naprawy szła po PID i **padła w pomiarze** (10 z 12 wątków dostało tę
> samą wersję), więc unikalność nie opiera się dziś na modelu równoległości.
>
> **Wniosek z ostatniego akapitu zostaje w mocy i nie jest historyczny:** narzędzie
> nadal liczy „padł jakikolwiek test" jako zabicie, więc każdy przegląd nadal musi
> czytać dziennik, a nie tylko podsumowanie. Ta lekcja przeżyła usterkę, która ją
> wywołała.

**Jak było.** `test_ci_blender_installer_refuses_a_tarball_whose_checksum_does_not_match`
**był** flaky przy przebiegu współbieżnym — i to on wyprodukował fałszywe zabicie
w przebiegu „przed". Nazwa tarballa była w nim zaszyta na stałe:

```python
leftover = f"/tmp/blender-{FAKE_BLENDER_VERSION}-linux-x64.tar.xz"
```

Trzy robotnicy przeglądu uruchamiają `test_all.py` równolegle i wchodzą sobie w tę
jedną ścieżkę: jeden sprząta plik, którego drugi jeszcze używa. W dzienniku „przed"
test padł 1 raz, w dzienniku „po" 3 razy — i tylko raz był JEDYNYM padniętym testem,
czyli tylko raz przekłamał werdykt. W przebiegu „po" każdy dotknięty flakiem wpis
miał też prawdziwe padnięcie, więc **żadne z 59 zabić nie jest fałszywe** —
sprawdzone wpis po wpisie w dzienniku, nie założone.

`tools/tests/test_ci_workflows.py` był poza zakresem **tamtego** zadania, więc #206 go
nie ruszyło; zrobiło to #207 nazajutrz. Zostaje z tego powód, żeby
**każdy przyszły przegląd czytał dziennik, a nie tylko podsumowanie**: narzędzie
liczy „padł jakikolwiek test" jako zabicie i nie ma jak wiedzieć, że padł test
o niczym.
