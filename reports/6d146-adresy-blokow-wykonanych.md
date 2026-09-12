# 6.D146 — 92 adresy w 216 blokach wykonanych, dziesięciu kandydatów, zero złych

**11.09.2026**, na `2ed6379`. Wejście: `docs/TASKS.md`,
`tools/tests/test_field_paths.py`. Pozycja: 6.D126 poprawiło jeden adres i zapisało
regułę, a ile jest pozostałych, nie wiedział nikt.

## 1. Liczby, o które pozycja prosiła

| | |
|---|---:|
| bloków w `docs/TASKS.md` | 228 |
| z tego **wykonanych** (poza kolejką, więc poza skanem pól) | **216** |
| wywołań modułu w polu „Weryfikacja" bloków wykonanych | **92**, w 90 blokach |
| z tego modułów **nieistniejących** | **0** |
| kandydatów na zły adres wg reguły z pola „Wyjście" | **10** |
| z tego złych adresów **po przeczytaniu** | **0** |

Dziesięciu da się przeczytać po kolei i przeczytano. Odpowiedź na pytanie
„czy kandydatów jest na tyle mało, żeby przeczytać ich ręcznie" brzmi **tak** —
i właśnie dlatego bramki semantycznej nie warto budować.

## 2. Reguła z pola „Wyjście" nie mierzy adresu. Zmierzone, nie ocenione

Reguła brzmiała: nazwa modułu wołanego w „Weryfikacji" nie pada w żadnym zdaniu
bloku. Daje **10** kandydatów i **10** fałszywych alarmów — precyzja **zero**.

Powód jest systematyczny, a nie przypadkowy: proza nazywa bramkę **po tym, co robi**
(„bramka liczy przyspieszenie rozruchu z modelu i porównuje z tabelą"), a nie po
nazwie pliku. Dwa przypadki — 6.D86 i 6.D89 — stoją na tej liście wręcz dlatego,
że ich adres **został już poprawiony**, a poprawiona nazwa w starej prozie siłą
rzeczy nie pada.

**Kontrolą jest druga reguła, równie prawdopodobna**: czy moduł niesie numer bloku
(konwencja `— 6.D145` w docstringach). Daje **9** kandydatów. Wspólny z pierwszą
jest **jeden** (`6.D36` → `test_mutation_sweep.py`). Dwie reguły zgodne w jednym
przypadku na dziewiętnaście nie mierzą tej samej rzeczy — i żadna nie mierzy adresu;
mierzą własne konwencje pisania. `test_regula_prozy_nie_jest_tym_samym_co_regula_numeru`
przybija tę rozbieżność, żeby nie była opinią.

Dziesięć przeczytanych, z powodem przy każdym, stoi w `SPRAWDZONE_RECZNIE`.
Lista **nie jest zapadką** i to jest wybór: kandydat pojawia się przy każdym bloku,
którego proza nazywa bramkę opisowo, czyli często i bez związku z usterką. Zapadka
byłaby podatkiem od każdego nowego bloku, płaconym za sygnał o precyzji zero.

## 3. Wejście pozycji jest nieaktualne — poprawionych adresów jest pięć, nie jeden

Pole „Skąd" mówi „6.D126 poprawiło **jeden** adres (blok 6.D74)". Adnotacji
`**Poprawione …:**` jest w drzewie **sześć**, w **pięciu** blokach:

| blok | data | co było nie tak |
|---|---|---|
| 6.D73 | 10.09.2026 | skan przeprowadził się z `test_backlog.py` przy 6.D32 |
| 6.D74 | 10.09.2026 | `test_scan_gates.py` testuje `tools/blender/scan_gates.py` |
| 6.D74 | 11.09.2026 | ten sam blok drugi raz — bramka mieszka w `test_tree_walks.py` |
| 6.D86 | 10.09.2026 | `test_physics_reference.py` — **modułu nie ma** |
| 6.D89 | 10.09.2026 | `test_glossary.py` — **modułu nie ma** |
| 6.D133 | 11.09.2026 | znów `test_scan_gates.py`, znów nie ta bramka |

Podział jest tu treścią: **dwa** z sześciu to nazwa modułu, którego w drzewie nie ma
— kształt, który bramka ROZPOZNAJE. Cztery to moduł istniejący, ale nie ten — kształt
semantyczny, którego rozpoznać nie umie i po tej pozycji nie będzie próbować.

## 4. Co z tego wynikło: bramka istnienia patrzy teraz na bloki wykonane

`test_no_open_field_names_a_test_module_that_is_not_in_the_tree` czytał **wyłącznie
bloki otwarte** — blok wypadał mu z pola widzenia w chwili odhaczenia. Oba przypadki
„modułu nie ma" (6.D86, 6.D89) znalazł człowiek, już **po** odhaczeniu, kiedy bramka
przestała na nie patrzeć.

Test jest przepisany, a nie dopisany obok: nazywa się teraz
`test_zadne_pole_nie_wola_modulu_spoza_drzewa` i czyta `_all_blocks()`.
**Kosztuje to dziś zero** — nieistniejących nazw w blokach wykonanych jest zero —
i dokładnie dlatego wolno to zrobić bez pracy po pomiarze, której zabrania pole
„Poza zakresem".

## 5. Kontrole negatywne

Baza: **25/25**. Po każdej `cp` z kopii i `md5sum -c: OK` na dwóch plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | nieistniejący moduł w bloku **wykonanym** (6.D120) | **24/25** | rozszerzona bramka go widzi |
| KN-1b | ta sama mutacja, bramka czyta znów tylko otwarte | **25/25 ZIELONA** | **to jest dowód, że rozszerzenie było zmianą, a nie kosmetyką** |
| KN-2 | reguła prozy czyta cały blok, razem z płotkiem | **23/25** | kandydatów 10 → 0; bez cięcia płotka reguła nie odsiewa niczego |
| KN-3 | skan czyta pole „Wejście" zamiast „Weryfikacji" | **23/25** | wywołań 92 → 0; próg KW stoi na samym skanie |
| KN-4 | jeden wpis zdjęty z zapisu czytania | **24/25** | zapis dziesięciu przeczytanych jest przybity |
| KN-5 | obie reguły stają się tą samą regułą | **24/25** | rozbieżność z sekcji 2 jest mierzona, nie opisana |

**KN-1b jest tu wynikiem, nie formalnością.** Nazwa `test_profil_pionowy.py`
w polu „Weryfikacja" bloku 6.D120 przechodziła cały moduł na zielono, dopóki bramka
czytała same bloki otwarte. Tego kształtu dotyczą dwie z pięciu poprawek z sekcji 3.

## 6. Kolejka i zapadki

Domknięcie tej pozycji zbiło kolejkę z dwunastu na **jedenaście**, czyli pod próg §8,
więc doszły trzy bloki: **6.D156** (72 nierozstrzygnięte asercje C# i nieużyty pomiar
zawężenia), **6.D157** (`test_scan_gates.py` był złym adresem dwa razy) i **6.D158**
(adresy w polach „Wejście" i „Wyjście" bloków wykonanych). Wszystkie trzy z pomiarów
zrobionych przy 6.D145 i 6.D146, a dwa wprost z pól „Czego nie zrobiłem" tamtych
pozycji. Po uzupełnieniu **14 do wzięcia**.

Doszły też dwie zapadki i obie musiały dostać klasę w rejestrze z 6.D133:
`MIN_BLOKOW_WYKONANYCH` i `MIN_WYWOLAN_W_WYKONANYCH`, obie **wolne** (próg KW da się
obniżyć bez zapalenia czegokolwiek). Rejestr: 38 → **40**, klasy 13/3/21/1 → **13/3/23/1**.
Zapaliło to `test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem` przy pierwszym
przebiegu — przyrząd z 6.D133 zadziałał na zapadkach dopisanych półtorej doby później.

## 7. Czego nie zrobiono

- **Nie poprawiono ani jednego adresu** — pole „Poza zakresem" mówi to wprost,
  a po przeczytaniu dziesięciu kandydatów nie było czego poprawiać.
- **Nie zbudowano bramki semantycznej** („czy moduł zawiera bramkę, o której pole
  mówi"). Sekcja 2 mówi, dlaczego: obie mechaniczne reguły, jakie się nasuwają,
  mają zmierzoną precyzję zero.
- **Nie przybito listy kandydatów zapadką** — patrz sekcja 2, ostatni akapit.
- **Nie sprawdzono adresów w polach „Wejście" i „Wyjście"** bloków wykonanych.
  Pole „Wyjście" pozycji pytało o „Weryfikację" i tylko o nią; rozszerzenie byłoby
  trzykrotnie większym czytaniem, a bramka istnienia i tak obejmuje wszystkie trzy
  pola od tej pozycji.
