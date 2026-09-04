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
