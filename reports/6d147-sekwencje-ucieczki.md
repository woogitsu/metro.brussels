# 6.D147 — cztery złe sekwencje ucieczki, nie trzy, i czwartą dołożyłem sam

**12.09.2026**, na `42c7289`. Wejście: `tools/tests/csharp_test_methods.py`,
`tools/tests/test_conflict_markers.py`, `tools/tests/test_next_task.py`,
`tools/tests/test_dimension_audit.py`, `tools/tests/test_bytecode_staleness.py`.

## 1. Wejście pozycji mówiło o trzech modułach. Są cztery

| moduł | wiersz literału | sekwencje | skąd |
|---|---:|---|---|
| `csharp_test_methods.py` | 69 | `` \` `` | wpis 6.D147 |
| `test_conflict_markers.py` | 2 | `\|` ×2 | wpis 6.D147 |
| `test_next_task.py` | 260 | `\|`, `\.`, `\d` ×2 | wpis 6.D147 |
| **`test_dimension_audit.py`** | **266** | `` \` `` ×2 | **doszedł po pomiarze** |

Czwarty nie jest przeoczeniem wpisu: **dołożyłem go sam przy 6.D139**
(`4358ab5`, dobę wcześniej), a wpis 6.D147 powstał z logu CI przy 6.D136, czyli
przed tamtym commitem. **Nie zauważył tego nikt i nic.** To jest cały powód, dla
którego ta pozycja kończy się bramką, a nie samą poprawką.

Numery wierszy z wpisu (83, 28, 267) są **pozycjami znaku**; CPython raportuje
wiersz **otwarcia literału** (69, 2, 260). Obie liczby są prawdziwe i mówią o czym
innym.

Sekwencji jest **dziewięć**, a ostrzeżeń były cztery, bo **CPython zgłasza tylko
PIERWSZĄ złą sekwencję w danym literale**. Sam `test_next_task.py` miał ich cztery.

## 2. Polecenie z pola „Weryfikacja" nie weryfikuje niczego na tym Pythonie

```
$ python3 -V
Python 3.11.15
$ python3 -W error::SyntaxWarning -m compileall -q tools   # PRZED poprawką
KOD=0            ← i ani jednego wiersza, przy czterech sekwencjach w drzewie
```

Do 3.11 włącznie CPython zgłasza te sekwencje jako `DeprecationWarning`; od 3.12
jako `SyntaxWarning`. Polecenie z wpisu działa na runnerze (stamtąd 112 wierszy
logu) i **milczy w tym kontenerze**. Ta sama zmiana widziana klasą ostrzeżenia:

```
$ python3 -W error::DeprecationWarning -m compileall -q tools   # PRZED poprawką
*** Error compiling 'tools/tests/csharp_test_methods.py'...   invalid escape sequence '\`'
*** Error compiling 'tools/tests/test_conflict_markers.py'...  invalid escape sequence '\|'
*** Error compiling 'tools/tests/test_dimension_audit.py'...   invalid escape sequence '\`'
*** Error compiling 'tools/tests/test_next_task.py'...         invalid escape sequence '\|'
```

Dlatego bramka czyta **źródło**, a nie ostrzeżenia interpretera: bramka oparta
o klasę ostrzeżenia byłaby zielona na jednej z dwóch wersji Pythona, a projekt
chodzi dziś na obu.

## 3. Obawa z pola „Dlaczego" jest dla tych czterech nieprawdziwa — zmierzone

Pole mówiło: „docstring z surowym napisem zmienia sposób, w jaki czyta go bramka
roszczeń (`\` przestaje uciekać) — pozycja ma sprawdzić, czy któraś bramka na tym
stoi". Sprawdzone wprost, porównaniem wartości docstringa przed dopisaniem `r`
i po nim:

| moduł | wartość identyczna | długość |
|---|---|---:|
| `csharp_test_methods.py` | **tak** | 1095 / 1095 |
| `test_conflict_markers.py` | **tak** | 2688 / 2688 |
| `test_dimension_audit.py` | **tak** | 372 / 372 |
| `test_next_task.py` | **tak** | 913 / 913 |

Żaden z czterech nie niesie ucieczki **prawidłowej**, którą `r` by unieszkodliwiło.
Prefiks jest więc dla nich zmianą zerową w wartości i jedyną zmianą w źródle —
i dlatego wolno go dopisać bez dotykania treści („Poza zakresem").

## 4. Bramka, i dlaczego liczy 202 moduły

`sekwencje_ucieczki` chodzi po `tools/` przez `tree_walk.znajdz` (jedno odsianie
`.gitignore`, jedno przejście — 6.D74, 6.D97, 6.D117), parsuje każdy moduł i czyta
znaki po `\` w źródle każdego literału nieoznaczonego prefiksem `r`. **202 moduły,
3,1 s.** Zapadka `MAX_SEKWENCJI_UCIECZKI` stoi na **zerze, przybita z obu stron**;
`MINIMUM_MODULOW_SKANOWANYCH` jest progiem KW na samym skanie.

**Odsianie po ukośniku w WARTOŚCI literału jest konieczne, nie ozdobne:** bez niego
skan nie kończył się w 100 s, bo `ast.get_source_segment` tnie całe źródło na wiersze
przy każdym wywołaniu. Odsianie jest szczelne — sekwencja nieprawidłowa zostaje
w wartości razem z ukośnikiem, prawidłowa zamienia się na coś innego — i KN-6
pokazuje, że jego zdjęcie nie zmienia wyniku, tylko czas.

## 5. Kontrola KN-1 znalazła dziurę w moim własnym czytniku

Pierwsza wersja czytnika robiła `except SyntaxError: continue`. Mutacja KN-1 wstawiła
złą sekwencję tak, że plik **przestał się parsować** — i wtedy:

- `test_compileall_…` zgłosiło **201 plików zamiast 202**,
- a **moja bramka pozostała zielona**, bo plik wypadł jej ze skanu bez śladu.

Zero sekwencji było wtedy zdaniem o drzewie, którego bramka **nie przeczytała
w całości** — rodzina 6.D27, tym razem w przyrządzie tej pozycji. Pliki
nieparsowalne są odtąd zbierane i zgłaszane osobno, z komunikatem parsera; KN-7
wykonuje ten scenariusz wprost.

## 6. Kontrole negatywne

Baza: **18/18**. Po każdej `cp` z kopii i `md5sum -c: OK`.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1b | piąta zła sekwencja w drzewie | **17/18** | `[('tests/test_next_task.py', 44, '\|')]` |
| KN-2 | zdjęty prefiks `r` z jednego z czterech docstringów | **17/18** | poprawka z sekcji 3 jest tym, co daje zero |
| KN-3 | `SUROWY` uznaje każdy literał za surowy | **17/18** | prefiks jest naprawdę rozpoznawany |
| KN-4 | pary `\\` nie są przeskakiwane | **17/18** | zdublowany ukośnik nie jest fałszywym alarmem |
| KN-5b | skan zawężony do `tools/ci`, **próg nietknięty** | **17/18** | próg KW bije przy 9 modułach ze 202 |
| KN-6 | zdjęte odsianie po ukośniku w wartości | **18/18 ZIELONA** | odsianie zmienia **czas**, nie wynik — i tak ma być |
| KN-7 | plik nieparsowalny w drzewie | **16/18** | patrz sekcja 5 |

**KN-5 była pierwotnie źle zaprojektowana i to jest warte zapisania.** Zmieniła próg
**i** zakres skanu naraz, więc wyszła zielona i mierzyła wartość progu zamiast jego
obecności — ta sama pomyłka co przy 6.D129 i 6.D135, w trzeciej odsłonie. KN-5b
rusza sam zakres.

## 7. Czego nie zrobiono

- **Nie tknięto treści żadnego docstringa** poza prefiksem — pole „Poza zakresem".
- **Nie sprawdzono `tests/` ani `src/`** — pozycja mówi o `tools/`, a bramka czyta
  dokładnie ten katalog. Ile złych sekwencji jest poza nim, nie wiadomo.
- **Nie zmieniono polecenia w polu „Weryfikacja"** ani w żadnym workflow; sekcja 2
  mówi tylko, czego to polecenie na tym Pythonie nie pokazuje.
- **Nie policzono, ile z 202 modułów niesie literał surowy** — liczba nie była
  potrzebna do niczego w tej pozycji, a policzona bez odsiania trwała ponad dwie
  minuty.
