# „9 z 44" było prawdą w dniu wpisania — i to zmieniło całą pozycję (6.B45)

**Zmierzone 07.09.2026 na commicie:** `d9d87092cf0bd14b15ef7fff5e3d68f1ea7b018c`
**Dotyczy:** `tools/tests/test_mutation_sweep.py`
**Rodzina:** 6.D3 (pomiar mówi, na czym powstał), 6.D26 i 6.A31 (liczbę się wyprowadza)

## 1. Pozycja zakładała nieprawdę o samej sobie

Wiersz kolejki mówił, że docstring „podaje 9 z 44, a zmierzone jest 10 z 63 — i obie
liczby są nieprawdziwe". Pierwsza część jest prawdziwa, druga **nie**: sprawdzone na
commicie, który to zdanie wprowadził.

```
ff99d13 (03.09.2026, commit wprowadzający zdanie)   celów 44   nieosiągalnych  9
6bbbf37 (04.09.2026)                                celów 55   nieosiągalnych 10
d9d8709 (07.09.2026, dziś)                          celów 63   nieosiągalnych 10
```

**„9 z 44" zgadzało się co do sztuki w dniu wpisania.** To nie było fałszywe
twierdzenie, a **pomiar bez daty** — czyli inna usterka, wymagająca innej poprawki.
Nie przepisuję więc liczb na 10 i 63; przepisuję docstring tak, żeby każda liczba
miała commit, i dokładam własność, której nie trzeba utrzymywać.

Odpowiedź na pytanie z pola „Wyjście" („ile modułów z bpy doszło i odeszło"): w cztery
dni celów przybyło **dziewiętnaście**, a nieosiągalnych — **jeden**. Asercja na
dokładną liczbę zapaliłaby się więc raz na cztery dni, czyli byłaby bramką, nie
udręką; wybrałem jednak własność wyprowadzoną, bo nie wymaga nawet tego jednego razu.

## 2. Co nie było przybite: asercja stała na progu

```python
assert len(unreachable) < len(sweep.targets()) // 2
```

Dziś to `10 < 31`. Przechodzi przy 9, przy 10 i przy 30 — więc liczba w docstringu
mogła się starzeć bez żadnego objawu. Jakościowa połowa zdania **była** pilnowana
pętlą `assert "bpy" in reason` i pozostaje prawdziwa: dziesiąty moduł
(`tools/visual/capture_blender.py`) też importuje `bpy`.

## 3. Własność wyprowadzona z drzewa

Zmierzone 07.09.2026: zbiór nieosiągalnych **równa się dokładnie** zbiorowi modułów
importujących `bpy` **na poziomie modułu** — 10 = 10, zbiory identyczne. Rozróżnienie
„na poziomie modułu" jest tu całą treścią:

```
celow: 63
nieosiagalnych (sonda):            10
z 'import bpy' TEKSTOWO:           15
z importem bpy NA POZIOMIE MODULU: 10

tylko tekstowo, a osiagalne: ['tools/blender/lod_paths.py', 'tools/blender/marker_gates.py',
  'tools/blender/scan_gates.py', 'tools/blender/station_sections.py',
  'tools/blender/vehicle_fit.py']
```

Te pięć to moduły **wyciągnięte spod `bpy`** w 6.B9 (#276) i 6.B13 (#284) — wspominają
`bpy` w funkcji, nie w ciele. Bramka na tekstowy `grep` zgłaszałaby je jako usterkę.

Równość nie wymaga utrzymywania żadnej liczby: rośnie razem z drzewem.

## 4. Czego równość NIE łapie — i to jest zmierzone, nie założone

Pierwsza wersja docstringu twierdziła, że równość broni tych pięciu modułów. **Nie
broni.** `import bpy` dopisany na poziomie modułu do `lod_paths.py` wchodzi do **obu**
zbiorów naraz, więc równość zostaje spełniona, a próg (`11 < 31`) też przechodzi —
regres przeszedłby przez oba strażniki.

Dlatego tych pięciu broni osobna asercja na liście imiennej
`MODULY_WYCIAGNIETE_SPOD_BPY`. Lista jest utrzymywana ręcznie i to decyzja, nie
zaniedbanie: **„moduł, który kiedyś importował bpy i przestał" nie jest własnością
dzisiejszego drzewa** i wyprowadzić się jej nie da.

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1957/1957 przeszło
  RAZEM 74.155 s, 1957 testów, 103 modułów
kod: 0
```

Liczba testów bez zmian (**111** w module): pozycja dokłada asercje do istniejącego
testu i jedną stałą, nie nowy test.

## 6. Kontrola negatywna — WYKONANA za czwartym podejściem, i trzy pierwsze były ślepe

To jest najważniejsza część tego raportu, bo **trzy kolejne wersje tej kontroli nic nie
mierzyły, a dwie z nich zdążyły przekonać mnie do wniosku.**

**Próba 1** — `import bpy` wstawiony po pierwszym wystąpieniu napisu `import ` w pliku.
Padł **cudzy** test (`test_the_fingerprint_refusal_names_the_dirty_tree_when_that_is_the_cause`,
bo `lod_paths.py` jest jego atrapą brudnego drzewa), a mój **przeszedł**. Odczytałem to
jako „równość nie łapie regresu" i **wpisałem ten wniosek do docstringu**.

**Próba 2** — to samo po dołożeniu asercji na listę imienną. Znowu padł tylko cudzy
test. Wtedy sprawdziłem, gdzie wylądowało wstrzyknięcie:

```
pierwsze 'import ' na pozycji 327 -> kontekst:
'_lodN`" siedział jako\n`if level == 0` wewnątrz `lod_entries()` w `tunnel_sweep.py`,
 obok `import bpy`\nna poziomie modułu. `level` '
```

Pierwsze `import ` w tym pliku stoi **w docstringu modułu** — a docstring mówi
dokładnie o `import bpy` na poziomie modułu. Wstrzyknięcie wylądowało więc **wewnątrz
literału** i było bezczynne. Kontrola meldowała „nie złapane" dla zmiany, której nie
było.

**Próba 3** — wstawienie za ostatnim importem najwyższego poziomu, wyznaczonym `ast`-em:

```
AssertionError: modul nie ma importow na poziomie modulu
```

`lod_paths.py` **nie ma ani jednego importu w ciele** — i to jest właśnie powód, dla
którego 6.B9 go wyciągnęło. Trzecia próba nie wstrzyknęła niczego, ale przynajmniej
powiedziała to wprost, zamiast zameldować sukces.

**Próba 4, wykonana i potwierdzona trzema niezależnymi sprawdzeniami:**

```
import bpy na POZIOMIE MODULU: True
modul da sie zaimportowac: False | kod: 1

FAIL test_every_real_target_except_the_blender_entry_points_is_reachable:
  modul wyciagniety spod `bpy` w 6.B9/6.B13 znow importuje go w swoim ciele
  i przestal byc testowalny: ['tools/blender/lod_paths.py']
  109/111 przeszło
```

Komunikat pochodzi z asercji **listy imiennej**, a nie z równości — a równość stoi
w kodzie **przed** nią (wiersz 849 wobec 860). Równość więc **przeszła**, czyli wniosek
z próby 1 był prawdziwy; nowość jest w tym, że teraz jest **dowiedziony**, a nie
odgadnięty z kontroli, która nic nie robiła.

Plik przywrócony po każdej z czterech prób i sprawdzony `cmp`-em.

## 7. Czego świadomie nie zrobiłem

- **Nie przepisałem „9 z 44" na „10 z 63".** Liczba pierwotna była poprawna w swoim
  dniu; poprawką jest **data przy liczbie**, nie inna liczba.
- **Nie zdjąłem progu** `< len(targets()) // 2`. Po zmianie nie jest zbędny: równość
  jest spełniona także wtedy, gdy **oba** zbiory są puste, więc sama nie odróżnia
  „sonda widzi tyle, ile ma" od „na tej maszynie `bpy` jest dostępne".
- **Nie tknąłem `unreachable_modules`** — pozycja dotyczy zdania o sondzie, nie sondy.
- **Nie dopisałem bloku szczegółów** ani nowego testu, więc `MINIMUM_DETAIL_BLOCKS`
  zostaje na 111.

## 8. Zauważone przy okazji, nietknięte

- **`test_the_fingerprint_refusal_names_the_dirty_tree_when_that_is_the_cause` używa
  `lod_paths.py` jako atrapy brudnego drzewa**, więc każda kontrola negatywna
  modyfikująca ten plik wywraca go „przy okazji". Dwa razy wzięłem ten fałszywy alarm
  za brak sygnału z własnej bramki. Nie tknięte: to jest cudzy test i cudza atrapa,
  a rozwiązaniem byłaby osobna atrapa dla kontroli — czyli osobna pozycja.
- **Tekstowy `grep` za `import bpy` daje 15, a właściwa liczba to 10.** Różnica pięciu
  to dokładnie owoc 6.B9 i 6.B13. Gdyby ktoś kiedyś postawił bramkę na `grep`,
  zgłosiłaby pięć modułów, których naprawa polegała na tym, że `bpy` z nich wyszło.
