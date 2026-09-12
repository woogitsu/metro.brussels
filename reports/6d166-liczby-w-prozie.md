# 6.D166 — liczba wpisana w prozę obok bramki nie była przez nic porównywana

**12.09.2026**, na `bf7c2d0`. Wejście: `tools/tests/test_tree_walks.py`,
`tools/tests/test_all.py`, audyt repozytorium z 12.09.2026. Pozycja wyszła
z audytu, nie z kolejki — decyzja właściciela z tego samego dnia.

## 1. Dwa zdania, oba nieprawdziwe, oba przy własnym przyrządzie

| gdzie | co mówiła proza | co mierzy przyrząd obok |
|---|---|---|
| `test_tree_walks.py:147` | „Trzydzieści osiem: **13** przybitych, **3** częściowe, **21** WOLNYCH i **1** poza zasięgiem skanu” | `len(ZAPADKI)` = **42**, rozkład **15 / 3 / 23 / 1** |
| `test_all.py:389` | „przebieg bez argumentu robi to samo dla **120 modulow**” | `ls tools/tests/test_*.py` = **123** |

Pomiar, nie odczyt z audytu — powtórzony u siebie:

```
$ python3 -c "... import test_tree_walks as T; print(len(T.ZAPADKI)); print(Counter(...))"
42
Counter({'wolna': 23, 'przybita': 15, 'czesciowa': 3, 'poza skanem': 1})

$ ls tools/tests/test_*.py | wc -l
123
```

## 2. Nie znalazł ich żaden test i nie mógł

Akapit w `test_tree_walks.py` sam zapewnia, tuż pod nieprawdziwą liczbą:

> **Lista jest z NAZWAMI, nie z samymi liczbami, i to jest wybór.** […] Rozjechać się
> ta lista nie może, bo jest porównywana z drzewem W OBIE STRONY.

Zdanie jest prawdziwe o **liście** i nieprawdziwe o **zdaniu nad nią**. Bramka
`test_kazda_zapadka_ma_klase_i_modul` porównuje SŁOWNIK z drzewem; deklaracja
liczbowa stojąca dwa wiersze wyżej leży poza jej zasięgiem. Jest to ta sama
usterka, którą projekt tropi od 6.D27 — przyrząd melduje sprawdzenie, którego
nie zrobił — tylko o piętro wyżej: nie w kodzie, a w prozie o kodzie.

Że akurat **tu** to boli, widać po tym, że `ZAPADEK_RAZEM == 42` **jest** przybite
w asercji (`:664`). Czyli całość była pilnowana, a zdanie o całości nie.

## 3. Dlaczego samo przeliczenie zostało odrzucone

Przepisanie „38” na „42” naprawia dzisiaj i pozwala rozjechać się jutro — a rozjechało
się już raz i nikt tego nie zobaczył, dopóki nie przyszedł audyt. Liczba w prozie
potrzebuje dokładnie tego, co liczba w kodzie: **kogoś, kto ją porównuje**. Stąd
`tools/tests/test_prose_counts.py`, który czyta deklarację ze źródła i zestawia ją
z `len(ZAPADKI)`, z rozkładem klas i z zawartością `tools/tests/`.

Bramka ma **dolne ostrze na sam czytnik**: jeżeli wzorzec nie znajdzie deklaracji,
pada z komunikatem „trafień: 0”, zamiast przejść pętlę bez ani jednego porównania.
Bez tego przeredagowane zdanie dawałoby zieleń — czyli dokładnie tę chorobę,
którą ta pozycja leczy.

## 4. Trzeci test był zły i to jest tu zapisane, a nie zamiecione

Pierwsza wersja `test_deklaracja_stoi_cyframi_a_nie_slownie` szukała form słownych
(„Trzydzieści”, „czterdzieści dwie”) w **całym** `test_tree_walks.py`. Zapaliła się
natychmiast — **na moim własnym akapicie**, tym, który CYTUJE dawne brzmienie, żeby
wyjaśnić, co się zmieniło:

```
FAIL test_deklaracja_stoi_cyframi_a_nie_slownie: suma zapadek wróciła do zapisu
słownego (Trzydzieści, trzydzieście osiem) — czytnik jej nie widzi, a człowiek owszem
```

Bramka miała rację co do litery i nie miała co do rzeczy. Cytat historyczny wygląda
dokładnie jak deklaracja — **ta sama obserwacja, którą 6.D108 zrobiło dla raportów:
kształtu nie ma**. Skan po słowach kazałby nie opisywać przeszłości, czyli psułby
regułę „przepisane, a nie dopisane obok”, której projekt wymaga w każdym akapicie.

Zastąpiony kontrolą przyrządu z wejściem syntetycznym: deklaracja zapisana słownie
nie jest przez wzorzec **przepuszczana**, tylko **niewidziana**, a dolne ostrze
zamienia niewidzenie w czerwone. Obejście zapisem słownym jest więc możliwe do
zrobienia i niemożliwe do zrobienia **po cichu**.

## 5. Kontrole negatywne

Baza `test_prose_counts.py`: **3/3**. Po każdej `md5sum -c` na trzech plikach: `OK`.

| kontrola | co zmienia | skutek |
|---|---|---|
| KN-1 | suma w prozie 42 → 41 | **2/3** — `proza mówi o 41 zapadkach, a rejestr ma 42` |
| KN-2 | jeden człon kłamie (23 WOLNE → 22), **suma zostaje** | **2/3** — `proza: 22 wolnych, rejestr: 23` |
| KN-3 | proza o modułach 124 → 123 | **2/3** — `proza mówi o 123 modułach, a pod tools/tests/ leży 124` |
| KN-4 | deklaracja przepisana **słownie** | **2/3** — `zdanie o rejestrze zapadek nie zostało znalezione (trafień: 0)` |

**KN-2 jest tą kontrolą, dla której lista stoi z nazwami, a nie z samymi liczbami.**
Suma pozostaje prawdziwa, kłamie jeden człon — i właśnie to zostaje złapane. Bez
rozbicia na klasy zamiana jednej zapadki przybitej na wolną przeszłaby bez śladu,
co akapit obok przewidywał i czego dotąd nikt nie sprawdzał.

**KN-4 mierzy, że obejście jest głośne**, a nie że jest niemożliwe. To rozróżnienie
jest treścią, nie ostrożnością: bramka, która zakazuje zapisu słownego w całym
pliku, zakazuje też cytowania przeszłości — sekcja 4.

**Kontrole były robione DWA RAZY i pierwszy przebieg był nieważny.** Cofałem mutacje
przez `git checkout -- <plik>`, a moje zmiany były niescommitowane, więc po pierwszym
cofnięciu plik wracał do stanu SPRZED poprawki i KN-2, KN-3, KN-4 mierzyły nie to,
co miały. Widać to było po `md5sum -c: FAILED` na dwóch plikach. Powtórzone na kopii
w katalogu roboczym sesji; dopiero ten przebieg jest w tabeli wyżej.

## 6. Czego nie zrobiłem

- **Nie ruszyłem `docs/23-environment.md`**, mimo że audyt wskazał je jako trzecie
  miejsce nieprawdziwe. Dowodem miało być 10.0.401 w kontenerze tej sesji — ale
  **ten dotnet zainstalowałem sam godzinę wcześniej**, bo `doctor.sh` meldował
  `BRAK`. Dzisiejszy kontener nie jest więc świadkiem w tej sprawie. Zdanie mówi
  „na tej maszynie” i opisuje kontener z 08.09.2026; różnica wobec
  `test_dotnet_version.py` (10.0.401, 10.09.2026) to dwa kontenery z dwóch dni,
  a po 6.D108 oba zdania są poprawne w swoim dniu. Pozycja 6.D169 zapisuje
  to, co tu naprawdę jest: zdanie o maszynie bez daty przy sobie.
- **Nie przeliczyłem pozostałych liczb w prozie `tools/tests/`.** Bramka czyta dwie
  deklaracje, bo dwie znalazł audyt; ogólny skan „wszystkich liczb w docstringach”
  byłby innym zadaniem i innym mechanizmem.
