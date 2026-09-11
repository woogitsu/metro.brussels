# 6.D126 — zapis nieaktualny zostaje, zapis fałszywy wolno poprawić

**Zmierzone 11.09.2026 na:** `2d251b7`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_field_paths.py` (`_open_blocks`, `missing_modules`,
`module_names`), `docs/TASKS.md` (blok 6.D74), `tools/tests/test_tree_walks.py`,
`tools/tests/test_scan_gates.py`.

---

## 1. Co dokładnie jest nie tak

Pole „Weryfikacja" bloku **6.D74** wołało:

```bash
python3 tools/tests/test_all.py test_scan_gates.py
```

Bramka o przejściach po drzewie mieszka w **`test_tree_walks.py`** — i mieszkała tam
od dnia, w którym powstała. `test_scan_gates.py` w drzewie **jest**: testuje trzy
predykaty **skanu luzu** z `tools/blender/scan_gates.py`, z przejściami po drzewie
niezwiązane.

## 2. Dlaczego nie złapała tego żadna bramka — dwa powody naraz

1. **Moduł istnieje.** `missing_modules` rozstrzyga przez `test_all._only_path`,
   który tę nazwę **przyjmuje**. Pytanie „czy moduł zawiera bramkę, o której pole
   mówi" to pytanie o TREŚĆ, wykluczone wprost w polu „Poza zakresem" pozycji 6.D101.
2. **Blok jest wykonany.** `_open_blocks()` zawęża skan do pozycji DO WZIĘCIA, więc
   nawet gdyby moduł nie istniał, ten blok nie byłby czytany.

Każdy z tych powodów wystarcza osobno. 6.D101 zapisało to w swoim wierszu jako
zauważone — „adres błędny i żadna bramka tego nie powie" — i to jest ta pozycja.

## 3. Rozstrzygnięcie: różnica między „nieaktualny" a „fałszywy"

Docstring `_open_blocks` mówił dotąd, że zapis pozycji wykonanej jest historią, bo
„jej «Weryfikacja» cytuje polecenie, którym coś zmierzono, a narzędzie mogło się od
tamtej pory zmienić — i przepisanie tego cytatu sfałszowałoby pomiar".

**Ten powód dotyczy zapisu, który BYŁ PRAWDZIWY w dniu pomiaru.** Przepisanie takiego
polecenia faktycznie fałszuje pomiar: czytający zobaczyłby komendę, którą nikt niczego
nie mierzył. Powód **nie obejmuje** zapisu, który prawdziwy nie był **nigdy** — adresu
modułu, w którym opisywanej bramki nie było ani w dniu pomiaru, ani później. Tam
przepisanie niczego nie fałszuje, a zostawienie każe dokumentowi twierdzić nieprawdę.

**Warunki poprawki, wszystkie trzy naraz** — inaczej „fałszywy" staje się furtką do
przepisywania historii:

1. zapis jest fałszywy, a nie przestarzały: rzeczy, o której mówi, nie było pod tym
   adresem także w dniu, w którym pole powstało;
2. poprawka niesie adnotację `**Poprawione <data> …:**` z tym, co stało wcześniej,
   i z powodem — dawny zapis zostaje czytelny obok nowego;
3. adnotacja mówi, gdzie stoi ta reguła, żeby następny nie rozstrzygał od nowa.

Rozstrzygnięcie stoi w docstringu `_open_blocks`, czyli w bramce adresów — tego żąda
pole „Wyjście".

## 4. Konwencja nie jest wymyślona — jest używana od doby i niepilnowana

| blok | data | czego dotyczyła | czy bramka mogła to złapać |
|---|---|---|---|
| 6.D73 | 10.09.2026 | pole z adresem | — |
| 6.D74 | 10.09.2026 | `test_scan_gates.py` w polu „Wejście" | **nie**: moduł istnieje |
| 6.D86 | 10.09.2026 | `test_physics_reference.py` — **nie ma go w drzewie** | tak, gdyby blok był otwarty |
| 6.D89 | 10.09.2026 | `test_glossary.py` — **nie ma go w drzewie** | tak, gdyby blok był otwarty |

Cztery adnotacje, każda postawiona ad hoc, reguła nigdzie nie zapisana. **Trzy z nich
dotyczą modułu, którego nie ma; jedna — modułu, który jest**, i to ta jedna pokazuje,
czego bramka adresów nie złapie nigdy. Piąta adnotacja jest z tej pozycji, w tym samym
bloku 6.D74, tylko w innym polu: pole „Wejście" poprawiono dobę temu, pole
„Weryfikacja" zostało.

## 5. Co doszło do drzewa

* **`poprawki_zapisow`** — czytnik adnotacji `**Poprawione <data> …:**` po
  **wszystkich** blokach (nie tylko otwartych; KN-5 pokazuje, dlaczego to ma znaczenie).
* **`test_kazda_poprawka_zapisu_wykonanego_niesie_date_i_powod`** — pilnuje dwóch
  z trzech warunków: adnotacja niesie datę i niesie powód dłuższy niż
  `MINIMUM_POWODU`. **Trzeciego warunku — że zapis był fałszywy, a nie przestarzały —
  sprawdzić się nie da bez czytania historii, i mówię to wprost w docstringu testu,
  zamiast udawać, że bramka obejmuje całą regułę.**
* Liczba adnotacji przybita **równością**, nie progiem: w górę próg nie ma sensu, bo
  poprawek ma być mało; w dół też nie, bo zdjęcie adnotacji jest dokładnie tym cichym
  przepisaniem historii, przed którym ta reguła broni.
* **`test_pole_weryfikacji_6d74_wskazuje_modul_z_bramka_o_ktorej_mowi`** — jeden blok,
  pytanie o TREŚĆ modułu. Tylko ten jeden, bo przeglądanie pozostałych jest wprost
  w polu „Poza zakresem".

## 6. Kontrole negatywne — WYKONANE, nie opisane

Baza `test_field_paths.py`: **22/22** (było 20).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | adres 6.D74 wraca do `test_scan_gates.py` | **21/22** |
| KN-2 | adnotacja bez daty | **21/22**, licznik 4 przy zapadce 5 |
| KN-3 | adnotacja skrócona do „zły adres." | **21/22**, powód 11 znaków |
| KN-4 | wzorzec przyjmuje adnotację bez daty | **21/22** |
| KN-5 | skan czyta tylko bloki OTWARTE | **21/22**, licznik **0** przy zapadce 5 |
| KN-6 | asercja na treść zdjęta, adres na obcy moduł | **21/22** — patrz niżej |
| KN-7 | bramka wyprowadza się z `test_tree_walks.py` | **21/22**, asercja na treść |

`md5sum -c` → `OK` po każdej, na `test_field_paths.py`, `docs/TASKS.md`
i `test_tree_walks.py`.

**KN-5 jest tu najciekawsza:** zawężenie czytnika do bloków otwartych — czyli
dokładnie to, co robi `missing_modules` — zbija licznik z pięciu na **zero**. Wszystkie
pięć adnotacji stoi w blokach wykonanych, co jest oczywiste dopiero po powiedzeniu:
adnotacja o poprawce zapisu wykonanego z definicji nie stoi nigdzie indziej.

**KN-6 pokazała, że asercja na treść modułu NIE była tym, co zapaliło.** Zdjąłem ją
i jednocześnie podstawiłem obcy moduł — czerwona była asercja na **nazwę**, bo nazwa
jest przybita dokładnie. Asercja na treść celuje w inną mutację i KN-7 to potwierdza:
przemianowanie bramki **wewnątrz** `test_tree_walks.py`, przy niezmienionym polu,
zapala wyłącznie ją. Dwie mutacje, dwie asercje, żadna nie jest ozdobą — ale bez KN-7
zostałaby w drzewie asercja, o której wiedziałbym tylko tyle, że nie ona zapaliła.

## 7. Czego nie zrobiłem

* **Nie przejrzałem pozostałych bloków wykonanych pod kątem adresów** — wprost
  w „Poza zakresem", i jest to pomiar na osobną pozycję. Dziś nie wiem, ile takich
  adresów jest, i nie udaję, że wiem.
* **Nie rozszerzyłem `missing_modules` na bloki wykonane.** Zawężenie do otwartych
  jest tam decyzją z powodem, a nie niedopatrzeniem; zdjęcie go zamieniłoby zapis
  historyczny w rzecz do utrzymywania.
* **Nie zbudowałem bramki pytającej o treść modułu dla wszystkich bloków.** Wymaga
  semantyki („czy TA bramka jest w TYM module"), której z tekstu pola nie da się
  wyprowadzić — pole 6.D74 nie nazywa testu, tylko opisuje go prozą.
