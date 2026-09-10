# 6.D101 — nazwa modułu w polu zadania jest adresem, więc jest sprawdzana

**Zmierzone 10.09.2026 na:** `691ed7d`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_field_paths.py` (`MODULE_CALL`, `MODULE_ARGUMENT`,
`module_names`, `missing_modules`), `tools/tests/test_all.py` (`_only_path` — ten sam
czytnik, którego używa zestaw), `git worktree` na `c724001` dla przeliczenia liczb
z dnia, w którym pozycja powstała.

---

## 1. Liczby, i jedna z wpisu, która się nie odtwarza

Pole „Skończone, gdy" żąda wypisania liczby nazw widzianych przez skan i podaje
**57 / 12 / 0**. Policzone dziś przyrządem, który powstał w tej pozycji:

| | wpis | `c724001` (dzień powstania wpisu) | dziś (`691ed7d`) |
|---|---|---|---|
| nazw w blokach wszystkich | 57 | **60** | **66** (30 różnych) |
| nazw w blokach otwartych | 12 | **12** | **11** |
| nazw nieistniejących | 0 | **0** | **0** |

Dwie z trzech liczb wpisu się odtwarzają. **„57" nie odtwarza się pod żadnym
odczytem, jaki umiałem zbudować** — na `c724001` policzone wyszło:

```
wystapien 60 | par (blok,nazwa) 60 | blokow 58 | roznych nazw 27
bez zawezenia do plotkow: 124
tylko pierwszy argument: 60
```

Najbliżej stoi 58 (liczba bloków), ale to jest inna wielkość. Skąd wzięło się 57,
nie wiem i nie udaję, że wiem; wpisuję to tutaj, bo liczba w polu „Skończone, gdy"
jest warunkiem odbioru, a warunek, którego nie da się odtworzyć, jest gorszy niż
jego brak.

Różnica 12 → 11 w blokach otwartych to zwykły ruch kolejki: 6.D99 i 6.D100 zostały
od tamtej pory scalone i ich bloki przeszły z otwartych do wykonanych.
Różnica 60 → 66 to sześć nowych bloków, każdy z własnym poleceniem.

Wszystkie 66 nazw stoi w polu **„Weryfikacja"** — w „Wejściu" i „Wyjściu" ani jednej.

## 2. Czytany jest pierwszy argument, bo drugiego nie czyta nikt

`tools/tests/test_all.py` kończy się na:

```python
if __name__=="__main__": sys.exit(main(sys.argv[1]) if len(sys.argv)>1 else main())
```

Czyli honorowany jest **wyłącznie `argv[1]`**. Skan liczący wszystkie argumenty
mówiłby o wywołaniu, którego nie ma. W dzisiejszym pliku żadne pole nie podaje dwóch
modułów, więc dziś obie reguły dają to samo — ale reguła ma być prawdziwa, a nie
prawdziwa przypadkiem.

## 3. Nie każdy token po `test_all.py` jest nazwą — trzy kształty z drzewa

Wypis pierwszych argumentów po `test_all.py` w całym pliku pokazał trzy rzeczy,
których nie było w żadnym opisie:

| kształt | ile | przykład | blok |
|---|---|---|---|
| nazwa z ogonem `;` z łańcucha `cmd; cmd` | 3 | `test_ci_workflows.py;` | 6.D44, 6.D45, 6.D63 |
| goły `\|` — cały zestaw w potoku, bez modułu | 1 | `python3 … test_all.py \| tail -3` | 6.D26 |
| nazwa **bez rozszerzenia** | 3 | `test_report_claims` | 6.B30, 6.D26, 6.D27 |

Trzeci kształt jest istotny, bo pierwsza wersja skanu, którą napisałem, uznała te
trzy za nieistniejące. Nie są: `_only_path` dokłada `.py` sam, więc
`python3 tools/tests/test_all.py test_report_claims` jest wywołaniem **poprawnym**.
Bramka, która by je zgłosiła, zgłaszałaby tekst prawidłowy — czyli zostałaby
wyłączona, a nie poprawiona (6.D27).

Stąd reguła: **werdykt rozstrzyga `test_all._only_path`, a nie druga reguła zapisana
w bramce.** Drugi czytnik tej samej rzeczy rozjeżdża się po cichu, a rozjazd akurat
tej pary znaczyłby, że bramka przyjmuje nazwę, której zestaw odmówi, albo odwrotnie.

## 4. Czwarty zmierzony przypadek jest poza zasięgiem — i to jest wybór

Pole „Skąd" wymienia cztery przypadki. Trzy — `test_physics_reference.py` (6.D86),
`test_glossary.py` (6.D89), `test_all_self.py` (6.D102) — to nazwy, których w drzewie
nie ma, i te bramka łapie. Czwarty, `test_scan_gates.py` (6.D74), **w drzewie jest**,
tylko testuje co innego. Pytanie „czy moduł zawiera bramkę, o której pole mówi" jest
pytaniem o TREŚĆ i pole „Poza zakresem" wyklucza je wprost. Bramka na nazwy tego nie
złapie i nie ma udawać, że łapie.

## 5. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` kopii na bok i `md5sum -c` po przywróceniu; `__pycache__` czyszczony
przed każdym przebiegiem. Zestaw pełny to **20/20** (przed tą pozycją 16).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | brany każdy token po `test_all.py`, nie tylko pierwszy | **17/20**, trzy testy; werdykt zgłasza `python3` w czternastu blokach |
| KN-2 | bez sprawdzenia kształtu argumentu (`MODULE_ARGUMENT`) | **18/20**; werdykt zgłasza `\|` |
| KN-3 | ogon `;` nieodcinany | **19/20**; kotwica 6.D44 przestaje widzieć nazwę |
| KN-4 | własna reguła zamiast `_only_path` (wymóg rozszerzenia) | **19/20**; poprawne `test_report_claims` zapala bramkę |
| KN-5 | skan czyta całe pole, nie tylko płotki | **20/20 — ZIELONA** |
| KN-6 | wzorzec zepsuty (`test_alll.py`) | **17/20**, trzy testy, w tym próg `MIN_MODULE_NAMES`, przy którym skan widzi zero nazw |

Po każdej: `md5sum -c` → `OK`.

### 5.1 KN-5 wyszła zielona i to jest główny wynik tej sekcji

Zdjęcie zawężenia do bloków ogrodzonych **niczego nie zmieniło**, choć docstring
mówi, że zawężenie jest po coś. Kontrola przyrządu, którą wtedy miałem, stawiała
w prozie zdanie bez wywołania — pilnowała więc czegoś, czego nie sprawdzała.

Pierwsza poprawka też była zielona (**KN-5b**), i z powodu, którego nie przewidziałem:
zdanie z grawisami cichnie nie dzięki zawężeniu, tylko dlatego, że `(\S+)` bierze
`` test_nie_ma_takiego.py`, `` razem z grawisem i przecinkiem, a taki token odrzuca
`MODULE_ARGUMENT`. Dwa różne mechanizmy dawały ten sam zielony.

Dopiero zdanie **bez grawisów** — „dawniej trzeba było uruchomić
python3 tools/tests/test_all.py test_nie_ma_takiego.py i porównać" — rozdziela te dwa
mechanizmy. **KN-5c** jest na nim czerwona:

```
FAIL test_the_three_measured_module_names_light_the_gate_when_put_back:
     cytat wywołania w prozie został wzięty za wywołanie:
     [('6.D999', 'Weryfikacja', 'test_nie_ma_takiego.py')]
```

Kontrola dodatnia stoi obok: ta sama nazwa **w płotku** zapala bramkę, więc cisza
w prozie nie jest ciszą skanu, który nie widzi nic.

## 6. Czego świadomie nie zrobiłem

- **Nie sprawdzam, czy moduł zawiera bramkę, o której pole mówi** — pole „Poza
  zakresem" wyklucza to wprost, i dlatego czwarty zmierzony przypadek zostaje
  niezłapany.
- **Nie poprawiałem wpisu 6.D101 o liczbę 57 w treści pozycji** poza wierszem
  „ZROBIONE": treść pierwotna zostaje w wierszu, bo zapis pozycji jest historią.
- **Progu na blokach OTWARTYCH nie postawiłem.** Kolejka maleje z każdą scaloną
  pozycją, więc taki próg czerwieniałby od sprzątania — ta sama decyzja, co przy
  kształcie katalogowym w 6.D73.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

- **`test_all.py` czyta wyłącznie `argv[1]`, po cichu.** Wywołanie
  `test_all.py a.py b.py` uruchomi `a.py` i o `b.py` nie powie nic — ani ostrzeżenia,
  ani kodu niezerowego. Dziś żadne pole tak nie pisze, więc nie ma czego naprawiać,
  ale jest to milczące pominięcie argumentu, a nie odmowa.
- **`test_scan_gates.py` nadal stoi w polu 6.D74 jako miejsce bramki o przejściach
  po drzewie**, a bramka ta mieszka w `test_tree_walks.py`. Blok jest wykonany, więc
  jego zapis jest historyczny — ale adres w nim jest błędny i żadna bramka tego nie
  powie.
