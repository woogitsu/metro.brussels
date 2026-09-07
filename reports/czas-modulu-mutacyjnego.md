# Jeden moduł zjada piątą część czasu zestawu — na co dokładnie (6.B38)

**Zmierzone 07.09.2026 na commicie:** `665bd987a4392155d954bd92cf4069e4142f3de4`
**Dotyczy:** `tools/tests/mutation_sweep.py`, `tools/tests/test_mutation_sweep.py`
**Poprzedni etap:** 6.B37, 6.D26 (próg czasu zestawu), 6.B30 (wzorzec: pamięć zamiast
zdejmowania testów)

## 1. Pomiar per test — bo pole „Wyjście" żądało go PRZED wyborem kierunku

Liczby z wpisu pozycji (14,9 s / 72 testy) są z 07.09.2026 i **nie są przeliczane** —
są pomiarem z datą. Dziś, po dołożeniu testów przez 6.B39, 6.B40 i 6.B42, moduł ma
**104 testy i 17,34 s**:

```
testow: 104   razem: 17.344 s
testow powyzej 0,1 s: 26   ich udzial: 16.973 s (97.9 %)

    7.142 s  test_every_mutation_still_parses
    1.786 s  test_every_real_target_except_the_blender_entry_points_is_reachable
    0.903 s  test_only_z_trafieniami_nadal_konczy_sie_zerem
    0.570 s  test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught
    0.499 s  test_obie_drogi_podaja_te_sama_przyczyne_tego_samego_stanu
    …  (dalsze 21 po ok. 0,3 s)
```

## 2. Trzy kupki, o które pytało pole — i założenie pozycji jest w nich NIETRAFIONE

Pole chciało wiedzieć, „ile z tego to `git worktree add`, ile uruchomienie procesu
Pythona, a ile prawdziwa praca". Zmierzone:

| kupka | koszt | udział w 17,34 s |
|---|---|---|
| `ast.parse` 2346 zmutowanych źródeł (**jeden** test) | **6,44 s** | 37 % |
| uruchomienia procesów (~24 testy × ~0,3 s) | ≈ 7 s | 40 % |
| `collect()` wołane **dziesięć razy** po 0,224 s | **2,24 s** | 13 % |
| import 63 modułów (jeden test) | 1,79 s | 10 % |
| **`git worktree add` + `remove`** (2 testy × 0,104 s) | **0,21 s** | **1 %** |

**`git worktree` nie jest kosztem tego modułu.** Jedno drzewo to 0,095 s na `add`
(541 plików w kopii) i 0,009 s na `remove`; używają go **dwa** testy. Pozycja
wskazywała je jako jedną z trzech głównych kupek — pomiar mówi, że są jedną
setną. Największą pojedynczą pozycją jest natomiast test, który **nie uruchamia
żadnego procesu**: `ast.parse` na 2346 mutacjach.

## 3. Co zostało zrobione: pamięć `collect` na (klasy, treść)

Z tych czterech kupek jedna jest **czystym marnotrawstwem**: dziesięć przeliczeń tej
samej listy. Pozostałe trzy są pracą, której testy nie mogą nie wykonać.

Pamięć jest kluczowana **odciskami wszystkich celów**, nie samym zestawem klas — i to
jest cała rzecz. Testy tego narzędzia **zmieniają pliki celów w trakcie jednego
procesu** (kontrole negatywne 6.B32, 6.B39, 6.B40), więc pamięć na klasach
podstawiałaby mutacje policzone dla innej treści: dokładnie ta usterka, którą 6.B32
zamykało w dzienniku, tylko przeniesiona do pamięci procesu.

**Klucz jest darmowy i to zmierzone**: odczyt i sha256 wszystkich 63 celów zajmuje
**0,0013 s** przy **0,224 s** na jedno `collect()` — 0,6 % tego, co oszczędza.

## 4. Czas przed i po — po trzy przebiegi każdej strony

```
MODUL, PRZED (origin/main 665bd98):   17.022 / 17.255 / 17.571 s   mediana 17.255
MODUL, PO:                            15.798 / 15.674 / 16.226 s   mediana 15.798
                                      → -1,46 s, -8,5 %

ZESTAW, PRZED:                        71.459 / 73.599 / 75.111 s   mediana 73.599
ZESTAW, PO:                           71.216 / 71.448 / 73.053 s   mediana 71.448
```

Liczba testów modułu **104 → 108**: czas spadł, a testów jest **więcej**, nie mniej.

**Efekt na całym zestawie jest zgodny w znaku, ale mieści się w jego własnym
rozrzucie** i tak go tu podaję. Przedziały zachodzą (przed 71,5–75,1; po 71,2–73,1),
więc z trzech przebiegów na stronę nie da się powiedzieć więcej niż „nie pogorszyło".
Pewny jest pomiar modułu, gdzie przedziały są rozłączne.

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1931/1931 przeszło
  RAZEM 71.093 s, 1931 testów, 101 modułów
kod: 0
```

Zestaw **1927 → 1931**, moduł **104 → 108**.

## 6. Cudza bramka zapaliła się na tej poprawce — i została PRZEKIEROWANA, nie zdjęta

`test_the_fingerprint_is_computed_once_per_file_not_once_per_mutation` (6.B32) liczyła
**wystąpienia napisu** `odciski_przebiegu(` w pliku i żądała dokładnie dwóch
(definicja + jedno wołanie). Pamięć `collect` dokłada drugie, poprawne wołanie, więc
bramka zapaliła się na zmianie, która jej własności nie narusza.

`CLAUDE.md` zabrania osłabiania bramek: bramkę blokującą zmianę **przekierowuje się na
zachowanie w tym samym commicie i po przekierowaniu ma sprawdzać WIĘCEJ, nie mniej.**
Nowa asercja liczy **prawdziwe wywołania** `odcisk_tresci` i żąda, żeby na jedno
`collect()` było ich tyle, ile **celów** (63), a nie tyle, ile mutacji (2346).

Że jest mocniejsza, jest **wykonane, nie powiedziane** — KN-A niżej.

## 7. Kontrole negatywne — WYKONANE

**KN-A — odcisk liczony raz na MUTACJĘ** (pętla po `found` w `collect`):

```
FAIL test_the_fingerprint_is_computed_once_per_file_not_once_per_mutation:
     odcisk liczony 2409 razy na 63 celow — ma byc raz na PLIK, nie raz na mutacje
```

Stara asercja tekstowa tego **nie widziała**: wołanie w pętli używa `odcisk_tresci`,
nie `odciski_przebiegu`, więc licznik napisu zostałby na 2 i bramka byłaby zielona.
Przekierowanie jest więc mocniejsze w obu kierunkach: łapie usterkę, której proxy nie
łapało, i nie zapala się na poprawnym drugim rozmówcy.

**KN-B — klucz pamięci bez odcisków, na samych klasach:**

```
FAIL test_pamiec_collect_UNIEWAZNIA_SIE_gdy_tresc_celu_sie_zmieni
FAIL test_pamiec_uniewaznia_sie_takze_przy_zmianie_BEZ_ani_jednej_mutacji
FAIL test_the_fingerprint_is_computed_once_per_file_not_once_per_mutation
  105/108 przeszło
```

**KN-C — pamięć zwraca tę samą listę, nie kopię.** Padają **cztery** testy, w tym
**dwa starsze od tej pozycji**:

```
FAIL test_pamiec_collect_zwraca_KOPIE_a_nie_te_sama_liste
FAIL test_pamiec_uniewaznia_sie_takze_przy_zmianie_BEZ_ani_jednej_mutacji
FAIL test_the_new_kinds_add_mutations_rather_than_replace_them
FAIL test_there_is_something_to_sweep
  104/108 przeszło
```

I to jest **uzasadnienie kopii, nie ozdoba**: test kopii wywołuje `.clear()` na
zwróconej liście, więc bez kopii zatruwałby pamięć **wszystkim** następnym testom.
Współdzielenie stanu między testami zamieniłoby je w atrapy — pole „Skończone, gdy"
żądało dokładnie tej kontroli, tylko dla drzew, a wypadła dla listy.

Plik przywrócony po każdej z trzech i sprawdzony przez `cmp`.

## 8. Dwie usterki w MOICH przyrządach, obie w rodzinie tego dnia

**Pierwsza: zmierzyłem komendę, która się nie wykonała.** Pierwszy pomiar kosztu
`git worktree add` dał **0,002 s** i wniosek „drzewa są darmowe". Sprawdzone: kod
wyjścia **128**, `fatal: invalid reference`, katalogu nie ma. Pomyliłem kolejność
argumentów (`add --detach HEAD <ścieżka>` zamiast `add --detach <ścieżka> HEAD`), więc
mierzyłem czas wypisania błędu przez gita. Prawdziwy koszt to **0,095 s**, czyli
47 razy więcej — a wniosek „drzewa nie są tu kosztem" ocalał tylko dlatego, że 0,095 s
razy dwa testy to nadal 1 %. To ta sama usterka co `/usr/bin/time` w
`reports/pamiec-pokrycia.md` §9: **narzędzie meldujące wynik, nie wykonawszy pracy.**

**Druga: przyrząd zmienił to, co mierzył.** Pomiar `ast.parse` na 2346 mutacjach dał
najpierw **39,9 s** — pięć razy więcej niż czas całego testu, który to samo robi.
Powód: gromadziłem drzewa w liście, a test je odrzuca. Zmierzone osobno:

```
bez gromadzenia drzew     6.443 s
z gromadzeniem w liste   28.633 s
```

**4,4×** różnicy, wyłącznie z trzymania wyników. Gdybym pierwszej liczbie uwierzył,
raport mówiłby, że jeden test zjada 39,9 s z 17,3 s modułu — czyli liczbę wewnętrznie
sprzeczną, którą łatwo przeoczyć.

## 9. Czego świadomie nie zrobiłem

- **Nie zdjąłem ani nie połączyłem ani jednego testu** — pole „Poza zakresem".
  Testów jest po tej pozycji **więcej** (104 → 108).
- **Nie tknąłem progu z 6.D26** — pole „Poza zakresem".
- **Nie ruszyłem `ast.parse` w `test_every_mutation_still_parses`** ani importów
  w teście osiągalności: to praca, nie marnotrawstwo. Ich koszt jest nazwany w §2,
  żeby następna reakcja na przekroczony próg nie zaczęła się od zdejmowania testów.
- **Nie wprowadziłem współdzielenia drzew `git worktree`** między testami. Pole
  „Skończone, gdy" przewidywało taki kierunek i żądało dla niego kontroli — pomiar
  pokazał, że drzewa to 1 % czasu, więc współdzielenie kupiłoby 0,1 s za cenę stanu
  dzielonego między testami. KN-C pokazuje, ile taki stan kosztuje, gdy pęknie.

## 10. Zauważone przy okazji, nietknięte

- **`test_every_real_target_except_the_blender_entry_points_is_reachable` ma
  w docstringu „9 z 44 modułów", a dziś nieosiągalnych jest 10 na 63.** Znalazł to
  agent wykonujący 6.B41 i nie tknął; ja też nie, bo to nie ten plik i nie ta pozycja.
  Asercja stoi na progu i przechodzi — czyli liczba w opisie starzeje się cicho, tak
  jak 6.D33 opisuje dla audytu komend.
- **`collect()` nie ma parametru zawężenia**, więc test, który potrzebuje świeżego
  przeliczenia, płaci za wszystkie 63 cele. Dlatego nowe testy mierzą **deltę** liczby
  kluczy pamięci, a nie czyszczą jej całej: czyszczenie kosztowałoby 0,224 s każdemu
  następnemu wywołaniu i zjadłoby oszczędność tej pozycji. Zawężenie w `collect()`
  byłoby osobną pozycją z własnym pomiarem.
