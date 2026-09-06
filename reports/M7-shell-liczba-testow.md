# `test_m7_shell.py` — 22 czy 21 testów (6.D8)

**Zmierzone 06.09.2026 na commicie:** `77c72da`

Rozstrzygnięcie jedynego wiersza z §1 `reports/report-claims-audit.md`, którego
datowanie nie tłumaczy. Siedem pozostałych rozjazdów tej klasy idzie w stronę
„raport mówi mniej, plik ma więcej" — plik urósł po pomiarze i raport ma prawo być
datowanym snapshotem. Ten jeden idzie w drugą stronę: `reports/M7-shell.md` twierdzi
w wierszu 77, że `tools/tests/test_m7_shell.py` ma **22 testy**, a plik ma **21**.
Raport nie mógł policzyć więcej testów, niż plik miał w dniu pomiaru.

Audyt zostawił trzy możliwości: (1) testy istniały i zostały usunięte, (2) liczba była
nieprawdziwa od początku, (3) „test" znaczy w raporcie coś innego niż `def test_`.

## Odpowiedź

**Zachodzi możliwość 2: liczba była nieprawdziwa w chwili, w której raport wszedł do
repozytorium.** Możliwość 1 jest wykluczona pomiarem — nie ma w historii tego
repozytorium ani jednej wersji pliku, która miałaby 22 testy. Możliwość 3 jest
wykluczona czytaniem pliku — nie ma w nim testów zapisanych inaczej niż jako
funkcja `def test_…` na marginesie modułu.

Osobno da się wskazać, **skąd wzięła się dwudziestka dwójka**, i to jest §3.

## Dowód z historii

Plik i raport urodziły się w tym samym commicie. `tools/tests/test_m7_shell.py`
wnosi do `main` commit `de574ff` („T-220: proceduralna bryła zewnętrzna M7 (#43)",
01.09.2026 12:08 +0200) — squash-merge PR-a #43 — i ten sam commit wnosi
`reports/M7-shell.md`. W drzewie nie ma commita, który by ten plik testowy później
zmienił: przez całą historię ma **jeden blob**, `efae1167`.

| co zmierzono | jak | wynik |
|---|---|---:|
| plik dziś, na `77c72da` | `grep -c '^def test_'` | **21** |
| plik na commicie z nagłówka raportu, `51fd842` | jw. | **21** |
| plik na commicie, który go wniósł, `de574ff` | jw. | **21** |
| plik na jedynym commicie gałęzi PR-a #43, `6630db9` | jw. | **21** |
| wszystkie wersje pliku w historii (551 commitów, 504 z plikiem) | skan blobów | **1 blob, 21 testów** |
| ile testów z tego pliku zalicza `tools/tests/test_all.py` | `ok   test_m7_shell_…` w wyjściu | **21** |

Skan blobów jest tu istotniejszy od `git log`: `git log --follow` na tym pliku
pokazuje **jeden** commit, więc gdyby liczba kiedykolwiek spadła, musiałoby istnieć
drugie wejście w historii. Nie istnieje.

Zostaje jedna szczelina, którą squash-merge normalnie zostawia: commity gałęzi
przed scaleniem. Tu jej nie ma, bo **PR #43 miał dokładnie jeden commit**,
`6630db948de1957af2cc2c985e2167ed70103895` (01.09.2026 10:02 UTC), i w nim plik ma
21 testów, a raport obok — w wierszu 75 tamtej wersji — już mówi „22 testy".
Commit gałęzi nie jest osiągalny z `main` po squashu; żeby to odtworzyć, trzeba go
najpierw ściągnąć:

```
git fetch origin 6630db948de1957af2cc2c985e2167ed70103895
git show 6630db94:tools/tests/test_m7_shell.py | grep -c '^def test_'   ->  21
git show 6630db94:reports/M7-shell.md | sed -n 75p
    Rozkład (`tools/tests/test_m7_shell.py`, bez Blendera) — 22 testy:
```

Historia nie zna więc momentu, w którym te dwie liczby byłyby zgodne. Nie ma czego
datować i nie ma usuniętego testu do wskazania.

## Skąd wzięła się 22

Plik ma na marginesie modułu **22 definicje funkcji**: 21 testów i jednego pomocnika
`_layout()`, który zwraca świeży rozkład z `tools/blender/m7_layout.py`.

```
grep -c '^def '      tools/tests/test_m7_shell.py   ->  22
grep -c '^def test_' tools/tests/test_m7_shell.py   ->  21
```

Dwudziestka dwójka jest w tym pliku **jedyną** liczbą, która pasuje do słowa „testy":
sekcji oznaczonych komentarzem jest 4, asercji 49, pustych wierszy 52, a punktów na
liście pod tym zdaniem w raporcie — 9, bo lista grupuje testy tematycznie, nie
wymienia ich po jednym. Najoszczędniejsze wyjaśnienie jest więc takie, że policzono
`^def ` zamiast `^def test_`.

To **nie czyni z tego możliwości 3.** `_layout()` nie jest testem w żadnym sensie,
w jakim tego słowa używa to repozytorium: nie zawiera ani jednej asercji, a
`tools/tests/test_all.py` zbiera z modułu wyłącznie nazwy zaczynające się od `test_`
i wywołuje 21 z tego pliku. „22 testy" nie jest inną definicją testu, tylko pomyłką
w liczeniu — jednym `def` za dużo.

## Wniosek: raport jest do sprostowania

Zakaz przeliczania datowanych pomiarów (6.D3, pilnuje go
`tools/tests/test_report_hygiene.py`) chroni zdanie, które **było prawdziwe w dniu
pomiaru**. To zdanie nigdy prawdziwe nie było, więc pod ochronę nie wchodzi —
przeciwnie, zostawione bez zmiany wysyła czytelnika po dwa testy, których w pliku
nie ma i nigdy nie było.

Wiersz 77 `reports/M7-shell.md` jest w tej samej gałęzi przepisany na **21 testów**,
a pod nim stoi sprostowanie w konwencji tego repozytorium: co poprzednia wersja
mówiła, że to była nieprawda i dlaczego zdanie jest przepisane, a nie dopisane obok.
Sam pomiar zostaje przy wierszu 77, żeby odsyłacz z §1
`reports/report-claims-audit.md` nadal wskazywał na to zdanie.

Poza tym jednym zdaniem raportu nie ruszono. Reszta jego liczb to zapis przebiegu
z 01.09.2026 i podlega 6.D3 bez wyjątku — w szczególności wyniki
`tools/ci/m7_shell_check.sh`, których ta pozycja nie odtwarzała.

## Czego ta pozycja nie zrobiła

- **Nie dopisano brakującego testu.** Rozjazd znika przez sprostowanie liczby, nie
  przez dorobienie 22. testu do liczby wpisanej kiedyś w raporcie; dorabianie kodu
  do liczby w prozie jest dokładnie tym, czego zakazuje `CLAUDE.md` §4.1.
- **Nie ruszono `reports/report-claims-audit.md`.** Tabela w jego §1 jest pomiarem
  z 06.09.2026 i w tamtym dniu mówiła prawdę: raport mówił 22, plik miał 21.
- **Nie ruszono siedmiu pozostałych wierszy tej tabeli.** Wszystkie są poprawnymi
  datowanymi snapshotami i tak mają zostać.
