# Dziennik mutacyjny odróżnia dwa przebiegi na tym samym commicie (6.B32)

**Zmierzone 07.09.2026 na commicie:** `0eef6212c1d2a38385023ac12cf82c5acd7daaf0`
(baza gałęzi `claude/6b32-odcisk-tresci`, czyli `main` po scaleniu #372).

## 1. Luka, którą 6.B19 nazwała, ale nie zamknęła

6.B19 (#349) dopisała do każdego wpisu dziennika `commit` z
`git rev-parse --short HEAD` i odmawia wznowienia, gdy dziennik niesie inny commit.
Przy niezacommitowanej zmianie — a `--dirty` jest dokładnie po to, żeby takie przebiegi
robić — **commit jest w obu przebiegach ten sam, a treść mutowanego pliku już nie**.
Odmowa z 6.B19 tego przypadku nie widzi i wznowienie podstawia wynik policzony dla innej
treści pod dzisiejszą mutację, po cichu. 6.B19 nazwała to wprost jako to, czego nie łapie.

## 2. Pomiar, o który prosiło pole „Wyjście": którą drogę wybrać

Pole żądało rozstrzygnięcia **pomiarem**, bo miało do wyboru rzecz tanią i słabą
(`git status --porcelain` — mówi tylko „drzewo brudne") wobec dokładnej i być może
drogiej (SHA-256 pliku):

```
mutacji w pelnym przegladzie: 2346   modulow: 63
suma bajtow modulow: 782261
najwiekszy: tools/blender/clearance_profile.py (46130 B)

SHA-256 raz na mutacje (2346 mutacji):  0.045 s
git status --porcelain raz:             0.015 s
```

Przy przebiegu **534–600 s** (liczba z wpisu 6.B36, pomiar z datą) odcisk liczony
**raz na każdą mutację** kosztuje **0,008 %**. Liczony raz na **plik** — 63 moduły,
i tak jest tu zrobione — jeszcze mniej. Przy tej różnicy nie ma powodu brać opcji,
która nie mówi, **co** w drzewie jest inne.

Odcisk to pierwsze 16 znaków szesnastkowych SHA-256. Sześćdziesiąt cztery bity przy
2346 mutacjach dają szansę przypadkowej kolizji rzędu 10⁻¹⁴, a wiersz dziennika zostaje
czytelny; pełne 64 znaki nie dają tu nic poza długością.

## 3. Rzecz, na której ta poprawka mogła być zbudowana źle

Odcisk **musi** być liczony z **drzewa roboczego**, nie z kopii robotnika, i to jest
cała treść tej pozycji:

- `collect()` liczy mutacje z drzewa roboczego — `open(path)` względem `ROOT`;
- `check_one()` stosuje je na kopii `git worktree add --detach HEAD`.

Te dwa źródła są **tym samym plikiem dopóki drzewo jest czyste** i **różnymi plikami
przy `--dirty`**. Odcisk liczony w `check_one` z kopii robotnika miałby więc dokładnie
wartość commita: byłby **slepy na przypadek, dla którego powstał**. Pilnuje tego
`test_the_fingerprint_reads_the_working_tree_not_the_worker_copy`, a kontrola KN-2
pokazuje, że bez niego pomyłka przechodzi.

## 4. Weryfikacja z pola „Weryfikacja" — WYKONANA, oba przebiegi

**Pierwszy przebieg, drzewo czyste:**

```
$ mutation_sweep.py --only tools/blender/lod_paths.py --journal /tmp/b32/dziennik.jsonl --workers 2
[MUTACJE] 2 mutacji do policzenia, 2 robotników, commit 8b1f98a, …
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 …
kod=0
```

Wpis dziennika niesie teraz odcisk:

```
{'id': 'tools/blender/lod_paths.py:28:1362', 'commit': '8b1f98a',
 'odcisk': 'fcb923b7000e0dca', 'plik': 'tools/blender/lod_paths.py', 'przezyla': False}
```

**Zmiana jednego znaku, BEZ commita:**

```
$ git rev-parse --short HEAD
8b1f98a                     ← ten sam commit
$ odcisk_tresci('tools/blender/lod_paths.py')
3080aab246047056            ← inny odcisk
```

**Drugi przebieg — odmawia:**

```
[MUTACJE] PRZERWANE — dziennik /tmp/b32/dziennik.jsonl niesie 2 wpisow policzonych na
INNEJ TRESCI pliku niz ta w drzewie roboczym, przy tym samym commicie '8b1f98a':
    tools/blender/lod_paths.py (dziennik fcb923b7000e0dca, drzewo 3080aab246047056)
  Identyfikator mutacji (plik:wiersz:przesuniecie bajtowe) nie niesie tresci, a `commit`
  nie odroznia dwoch przebiegow na tym samym commicie — wznowienie podstawiloby wynik
  policzony dla innego kodu pod dzisiejsza mutacje.
  Podaj wlasny --journal na inna sciezke albo skasuj tamten plik.
kod=2
```

**Wznowienie na drzewie NIEZMIENIONYM nadal działa** — tego żądało pole „Skończone, gdy":

```
[MUTACJE] wznowienie z /tmp/b32/dziennik.jsonl: 2 z 2 już policzonych
```

Odmowa nazywa **plik i oba odciski**, nie sam fakt: przy `--only` na katalog rozjazd
dotyczy zwykle jednego modułu z kilkunastu, a komunikat mówiący tylko „treść inna"
kazałby szukać ręcznie.

## 5. Kontrole negatywne — WYKONANE

**KN-1 — odmowa 6.B32 zdjęta** (stan przed tą pozycją):

```
FAIL test_resume_refuses_a_journal_written_on_other_content_of_the_same_commit:
     … wznowienie z …: 0 z 2 już policzonych … razem: 2
FAIL test_resume_refuses_a_journal_entry_without_the_content_fingerprint
75/77 przeszło
```

**Dokładnie dwa nowe testy, a odmowa z 6.B19 zostaje zielona** — tego żądało pole
„Skończone, gdy" wprost. Widać przy tym samą usterkę: bez odmowy narzędzie **wznawia**
z dziennika policzonego na innej treści i wypisuje `0 z 2 już policzonych`, czyli
podstawia cudzy wynik bez słowa.

**KN-2 — odcisk liczony z `HEAD` zamiast z drzewa roboczego:**

```
FAIL test_the_fingerprint_reads_the_working_tree_not_the_worker_copy: odcisk nie
     zmienil sie po zmianie pliku w drzewie roboczym — czytnik siega gdzie indziej
     niz `collect`
76/77 przeszło
```

Jeden test, ten właściwy. To jest kontrola na **moją własną możliwą pomyłkę**, nie na
kod cudzy: gdybym policzył odcisk w `check_one`, wszystkie pozostałe testy 6.B32 byłyby
zielone, a poprawka byłaby bezwartościowa.

## 6. Test 6.B19, który padł po drodze — i dlaczego to był dobry pomiar

```
FAIL test_resume_still_works_when_the_journal_is_from_the_same_tree:
     … PRZERWANE — … niesie 1 wpisow policzonych na INNEJ TRESCI …
     (dziennik None, drzewo fcb923b7000e0dca)
```

Pomocnik `_dziennik_z_wpisem` budował wpis **bez** pola `odcisk`, więc test mierzący
zgodność **commita** zaczął się wywracać na odmowie o **treści** — i przestałby mierzyć
to, co mierzy z nazwy. Pomocnik dostał więc pole `odcisk` z domyślną wartością
**prawdziwą, nie stałą**: każdy test tej rodziny psuje dokładnie jedno pole, a reszta
wpisu jest dzisiejsza. Wartownik `_BRAK` odróżnia „nie podano" (policz prawdziwy) od
`None` (wpis **bez** tego pola, czyli dziennik starszy niż ta poprawka).

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py test_mutation_sweep.py
  78/78 przeszło          (72 → 78, sześć nowych testów)

$ python3 tools/tests/test_all.py
  1886/1886 przeszło
  RAZEM 70.057 s, 1886 testów, 99 modułów
kod: 0
```

Liczba **1886**, nie 1885: gałąź stoi na `main` po scaleniu #372 (uzupełnienie kolejki
o 6.B40–6.B42), które wniosło jeden test do `test_backlog.py`. Pierwszy pomiar na
poprzedniej bazie dał `1885 / 69.635 s` i jest prawidłowy dla swojego drzewa.

## 8. Czego świadomie nie zrobiono

- **Nie tknięto schematu identyfikatora mutacji** (`plik:wiersz:przesunięcie bajtowe`) —
  pole „Poza zakresem"; przeliczyłby dotychczasowe dzienniki i zerwał porównywalność
  z raportami triażu. Ta sama granica, którą postawiła 6.B19.
- **Nie dodano progu czasowego na koszt odcisku.** Czas jest zmierzony (§2), ale próg na
  0,045 s byłby progiem na szumie. Przybity jest **kształt** — `odciski_przebiegu`
  zwraca słownik po plikach i jest wołane raz — bo to da się zmierzyć bez zegara.
- **Nie zmieniono odmowy `dirty_sources`.** Ona ostrzega, że mutacje policzone
  z drzewa roboczego trafiają na kopię `HEAD`; ta pozycja dotyczy **dziennika**, nie
  tamtego rozjazdu, i obie odmowy zostają obok siebie.

## 8a. Znalezisko na własnej poprawce: odmowa zasłaniała jaśniejszy komunikat

Odmowa odcisków stoi w `main` **przed** `dirty_sources`, bo musi działać także dla
`--list` — tamta odmowa jest za gałęzią `--list`. Skutek, zmierzony: przy brudnym
drzewie **bez** `--dirty` czytający dostawał komunikat o **dzienniku**, choć prawdziwym
problemem była jego własna niezacommitowana zmiana, a jaśniejszy komunikat
`dirty_sources` nie dochodził do głosu wcale.

Przestawienie kolejności nie jest rozwiązaniem: zdjęłoby odmowę odcisków z drogi
`--list`, czyli z jedynej taniej drogi, która ją sprawdza. Komunikat **nazywa** więc
drugą możliwą przyczynę — i tylko wtedy, gdy ona faktycznie zachodzi:

```
  Podaj wlasny --journal na inna sciezke albo skasuj tamten plik.
  UWAGA: te pliki maja niezacommitowane zmiany, i to jest prawdopodobna przyczyna
  rozjazdu odciskow:
    tools/blender/lod_paths.py
  Zacommituj je albo uruchom z --dirty, jesli wiesz, ze robisz co innego.
kod=2
```

Z `--dirty` tego zdania **nie ma** — przebieg jest wtedy zamierzony, a komunikat
radzący zacommitować to, co ktoś świadomie zostawił, byłby szumem. Oba kierunki
przybite; **KN-3** (zdanie dopisywane zawsze, bez warunku) wywraca dokładnie ten test:

```
FAIL test_the_fingerprint_refusal_names_the_dirty_tree_when_that_is_the_cause:
     przy --dirty komunikat radzi zacommitowac zmiane, ktora ktos zostawil swiadomie
77/78 przeszło
```

## 9. Zauważone przy okazji, nie tknięte

**Wznowienie, w którym wszystko jest już policzone, kończy się kodem 1.** Zmierzone
w §4 przy drugim przebiegu na czystym drzewie:

```
[MUTACJE] wznowienie z …: 2 z 2 już policzonych
brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych
kod=1
```

Kod 1 znaczy tu „nie zostało nic do policzenia", a nie „coś jest nie tak" — dla skryptu
CI, który uruchamia przegląd w pętli do skutku, jest to różnica między „gotowe"
i „awaria". Zachowanie jest **starsze od tej pozycji** i nie tknięte: to nie dziennik,
a kod wyjścia drogi bez mutacji, czyli inna klasa niż ta poprawka.
