# Logi jobów `tools` — materiał wpisów `POMIARY`

**Po jednym logu na KAŻDY wpis runnera** w `POMIARY`
(`tools/tests/test_suite_runtime_budget.py`) — równości obu zbiorów pilnuje
`test_kazdy_wpis_runnera_ma_log_w_drzewie`, a każde pięć pól wpisu jest z tego logu
wyprowadzane i porównywane znak w znak. Bez nich odpowiedź pozycji 6.D152 byłaby
zdaniem w raporcie, a nie sprawdzeniem.

**Ten katalog ROŚNIE i tak ma być — akapit jest przepisany, a nie dopisany obok
(6.D190).** Pierwsza wersja mówiła „sześć logów" i opisywała materiał JEDNEGO pomiaru;
po 6.D190 wpisy runnera zapisuje się dalej, a warunkiem wejścia wpisu do listy jest
właśnie ten plik. Sześć pierwszych (#524 … #529) to przebiegi, z których **6.D135
przepisało wpisy ręcznie**; kolejne dochodzą razem z wpisem.

Liczby plików ten plik nie podaje i podawać nie będzie: byłaby drugą kopią czegoś,
co widać przez `ls`, i rozjechałaby się przy pierwszym dopisanym wpisie (6.B28).

| plik | PR | job | data | skąd wzięty |
|---|---|---|---|---|
| `tools-pr524.log` | #524 | 103263889512 | 2026-09-11 | 6.D152 |
| `tools-pr525.log` | #525 | 103279051651 | 2026-09-11 | 6.D152 |
| `tools-pr526.log` | #526 | 103290647230 | 2026-09-11 | 6.D152 |
| `tools-pr527.log` | #527 | 103305260592 | 2026-09-11 | 6.D152 |
| `tools-pr528.log` | #528 | 103315552643 | 2026-09-11 | 6.D152 |
| `tools-pr529.log` | #529 | 103327216888 | 2026-09-11 | 6.D152 |
| `tools-pr571.log` | #571 | 103645523096 | 2026-09-13 | 6.D190 |
| `tools-pr583.log` | #583 | 103726356435 | 2026-09-13 | 6.D190 |

## Skąd

```bash
curl -sL -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/woogitsu/metro.brussels/actions/jobs/<ID JOBA>/logs" \
  -o tools-pr<NUMER>.log
```

## Dlaczego dosłowne i dlaczego NIE spakowane

**Dosłowne**, bo przycięcie do „wierszy, które są potrzebne" znaczyłoby, że bramka
sprawdza wybór człowieka, a nie log: ten sam ruch, którym psuje się kontrolę negatywną,
gdy zmienia się w niej dwie rzeczy naraz.

**Niespakowane — i ten akapit jest przepisany, a nie dopisany obok.** Pierwsza wersja
tego katalogu miała sześć plików `.gz` i tłumaczyła je tak: „surowy log ma ok. 292 KB,
a `gzip -9` schodzi do ok. 70 KB". Zdanie było prawdziwe i **nie o tym, co trzeba** —
mówiło o katalogu roboczym, a płaci się w historii. Dwa pomiary to obaliły:

1. **Bramka.** `test_conflict_markers.test_skan_czyta_CALE_drzewo_a_nie_pusty_zbior` żąda,
   żeby plik nieczytelny jako UTF-8 był **decyzją**, a nie cichym pominięciem: plik
   binarny zmniejsza skan konfliktów bez jednego słowa. Sześć `.gz` wywróciło **siedem
   jobów CI** naraz (12.09.2026, przebieg PR #548).
2. **Rozmiar w repozytorium, zmierzony.** Dwa puste repozytoria, tamte sześć logów,
   `git gc`: **234 858 B** tekstem wobec **428 699 B** gzipem. Tekst jest **1,83x
   tańszy**, bo git i tak pakuje zlibem i dodatkowo deltuje pliki podobne do siebie —
   a blobu już spakowanego nie skompresuje ani nie zdeltuje.

Odpowiedzią nie jest więc wyjątek na liście pilnowanych plików: taki wyjątek zdejmuje
plik spod bramki na zawsze, co sam moduł `test_conflict_markers.py` nazywa gorszym od
kotwiczenia wzorca. Odpowiedzią jest **plik, który bramka umie przeczytać**. Wzorców
konfliktu w tych logach jest zero — każdy wiersz zaczyna się od stempla czasu, a wzorce
są zakotwiczone na początku wiersza.

Sekrety są w logach zamaskowane przez GitHuba (`token: ***`) — sprawdzone przed
wstawieniem. Logi niosą natomiast nazwy maszyn puli i ścieżkę domową runnera; repozytorium
jest prywatne. `CLAUDE.md` §9 zakazuje **wybierania** runnera po nazwie i podawania
liczebności puli — zapis nazwy w materiale pomiaru nie jest ani jednym, ani drugim, ale
warto o tym wiedzieć, zanim ten katalog urośnie.

## Czego tu nie ma

Logu przebiegu z **kontenera sesji** — i to jest rozstrzygnięcie 6.D152, a nie
niedopatrzenie. Kontener nie jest runnerem, nie zapisuje niczego maszynowo i wpisy
kontenerowe w `POMIARY` zostają człowiekowi. Wpisy z CI nie zostają: log podaje wszystkie
pięć pól wpisu, co do znaku.

## Jak dopisać wpis runnera (6.D190)

Log najpierw, wpis potem — i wpis **wypisany**, a nie przepisany z ręki:

```bash
python3 tools/ci/timing_record.py --z-logu tests/data/ci-logs/tools-pr<NUMER>.log
```

`WPISOW_Z_DOPISKIEM` w `tools/tests/test_timing_record.py` jest od 6.D163 równe **zero**,
więc każde własne zdanie doklejone do pola „na czym" zapala bramkę. Pierwsza wersja
wpisów 6.D190 była pisana z ręki i miała trzy usterki naraz: złą datę, ogon o LIŚCIE
zamiast o przebiegu i „2433 testy" tam, gdzie log daje „2433 testów".
