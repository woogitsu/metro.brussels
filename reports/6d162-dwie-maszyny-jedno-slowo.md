# 6.D162 — dwie maszyny pod jednym słowem, i nazwa NIE wchodzi do wpisu

**13.09.2026**, na `c7e9de8`. Wejście: `tools/tests/test_suite_runtime_budget.py`,
`tests/data/ci-logs/`, `tools/ci/timing_record.py`, `reports/6d152-pola-wpisu-z-logu.md`.

## 1. Ile maszyn

Sześć logów w drzewie, czytanych `timing_record.z_logu` — czyli tym samym czytnikiem,
który składa wpisy `POMIARY`, a nie własnym wzorcem:

| log | maszyna | ściana | testów |
|---|---|---:|---:|
| PR #524 | `…-01` | 89,518 s | 2315 |
| PR #526 | `…-01` | 97,863 s | 2326 |
| PR #527 | `…-01` | 100,654 s | 2330 |
| PR #525 | `…-03` | 92,119 s | 2320 |
| PR #529 | `…-03` | 109,420 s | 2335 |
| PR #528 | `…-03` | 116,404 s | 2335 |

**Dwie maszyny, po trzy przebiegi.** Liczba wyliczona z katalogu, nie wpisana —
trzecia nazwa w logach zapala bramkę. Pole `runner` niesie nazwę, a `z_logu`
sprowadza ją do jednego słowa `runner` w polu `maszyna`; cała ta pozycja jest
o różnicy między tymi dwoma polami.

## 2. Czy nazwa cokolwiek rozdziela — nie

| | surowo | na test |
|---|---:|---:|
| różnica MIĘDZY maszynami (średnie) | **10,38 %** | **10,07 %** |
| rozrzut WEWNĄTRZ maszyny, największy | **26,36 %** | **25,55 %** |

**Różnica, którą miałaby opisać nazwa, jest mniejsza od szumu na tej samej maszynie.**
Pole niosące nazwę dzieliłoby przebiegi wzdłuż granicy, której nie ma.

Rozrzuty wewnątrz: `…-01` 12,44 %, `…-03` 26,36 %.

## 3. Zarzut o dryf drzewa, odparty rachunkiem

Pole „Dlaczego" mówiło, że materiału nie da się rozdzielić, bo w tym samym oknie
zestaw rósł 2315 → 2335 testów, a maszyna `…-03` dostała akurat większe drzewa.
Po znormalizowaniu czasu **na test** wniosek się nie zmienia (kolumna druga wyżej).

I nie może się zmienić: **drzewo urosło w tym oknie o 0,65 %**, a czasy rozjechały się
o kilkanaście do dwudziestu kilku procent. Dryf tej skali nie tłumaczy różnicy tej
skali — to ta sama arytmetyka, którą 6.D160 wykonało w drugą stronę.

## 4. Czym więc jest rozrzut, skoro nie maszyną — okazją

Ta sama maszyna `…-03`:

| kiedy | przebiegi | rozrzut | drzewo |
|---|---|---:|---|
| 11.09.2026 | 92,119 / 109,420 / 116,404 s | **26,36 %** | 2320 → 2335 testów |
| 13.09.2026 | 104,530 / 106,548 / 106,836 s | **2,21 %** | 2414 → 2418 testów |

Nazwa maszyny jest w obu wierszach ta sama, drzewo w drugim wierszu jest wręcz
stabilniejsze, a rozrzut różni się **dwunastokrotnie**. To nie jest cecha maszyny,
tylko dnia.

Trzy przebiegi z 13.09 to joby `tools` trzech kolejnych PR-ów tej sesji. Wszystkie
trzy padły na `…-03`, więc **różnicy między maszynami nie rozstrzygają** — wnoszą
za to rozrzut wewnątrz maszyny przy drzewie stałym co do 0,17 %, czyli dokładnie tę
liczbę, której 11.09 nie dawało.

## 5. `CLAUDE.md` §9 — rozstrzygnięte wprost, bo pozycja tego żądała

Dokument zakazuje **wybierania** runnera po nazwie i podawania liczebności puli.
Zapisanie nazwy w POMIARZE nie byłoby ani jednym, ani drugim: selektor `runs-on`
zostaje gołą etykietą, a liczba maszyn widoczna w sześciu logach nie jest liczbą
maszyn w puli i niczego o niej nie mówi. **Zakaz tego nie blokuje.**

Blokuje to pomiar z punktu 2. Pole, które nic nie rozdziela, jest polem, które
wygląda, jakby coś mówiło — a to jest rodzina tropiona w tym projekcie od 6.D27.

## 6. Rozstrzygnięcie

**Nazwa maszyny NIE wchodzi do wpisu `POMIARY`.** Zapisane jako stan drzewa, nie jako
zdanie: bramka sprawdza, że żaden wpis nazwy nie niesie. Wartości progu, zapasu
i podłogi nietknięte — „Poza zakresem", i nic w tym pomiarze tego nie wymagało.

## 7. Kontrole negatywne

Baza: **34/34**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK`; logi porównane
z `HEAD` po przywróceniu. Przed każdym przebiegiem czyszczony `__pycache__`; po
każdym podstawieniu `diff` z kopią roboczą i `assert` na jednym wystąpieniu.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | log PR #528 przypisany do drugiej maszyny | **ZIELONA** | patrz niżej |
| KN-2 | wszystkie logi z jednej maszyny | **32/34** | liczba maszyn jest liczona z katalogu |
| KN-3 | czytnik bierze słowo zamiast nazwy | **32/34** | bramka czyta pole `runner`, nie `maszyna` |
| KN-4 | wejście syntetyczne przestaje rozdzielać | **33/34** | kontrola przyrządu nie jest pusta |
| KN-5 | nazwa maszyny wchodzi do wpisu `POMIARY` | **32/34** | rozstrzygnięcie jest stanem drzewa |

### KN-1 wyszła zielona i to jest wynik, nie awaria

Podstawienie **weszło** — `diff` pokazał zmieniony wiersz `Runner name:`. Zielona jest
dlatego, że przeniesienie NAJWOLNIEJSZEGO przebiegu przez granicę zostawia różnicę
między maszynami na **0,3 %** przy rozrzucie wewnątrz **30 %**, czyli **wzmacnia** tezę
zamiast ją łamać. Żadne przetasowanie sześciu dzisiejszych logów tej asercji nie zapali:
jedna maszyna dostaje wtedy oba skrajne czasy i rozrzut wewnątrz rośnie szybciej niż
różnica średnich.

Rozstrzyga więc **wejście syntetyczne** (KN-4): dwie maszyny powtarzalne co do procenta,
różniące się dwukrotnie — świat, w którym nazwa COŚ rozdziela. Na nim rachunek zapala
się poprawnie, a na dzisiejszych logach mówi odwrotnie. To jest ten sam ruch, który
6.D161 policzyło jako dziewięć przypadków na osiemnaście, wykonany świadomie, a nie
odkryty po fakcie.

## 8. Czego nie zrobiono

- **Nie dopisano nazwy maszyny do wpisów** — to jest rozstrzygnięcie, nie pominięcie.
- **Nie tknięto `runs-on` ani doboru runnera** — zakazane w `CLAUDE.md` §9,
  i pomiar tego nie wymagał.
- **Nie zmieniono progu, zapasu ani podłogi** — „Poza zakresem".
- **Nie dopisano trzech logów z 13.09 do drzewa.** Wszystkie trzy są z jednej maszyny,
  więc liczby maszyn nie zmieniają; ich wkład (rozrzut 2,21 % przy stałym drzewie)
  jest w punkcie 4 jako pomiar, a nie jako plik.

## 9. Co zauważone przy okazji, nietknięte

`z_logu` ustawia `maszyna` na stałe słowo, gdy tylko znajdzie wiersz `Runner name:`.
Znaczy to, że log **bez** tego wiersza nie dostaje pola `maszyna` wcale — a wpis
`POMIARY` bez maszyny jest odrzucany przez bramkę z 6.D135. Dwa mechanizmy trzymają
się więc jednego wiersza logu, którego treści żaden z nich nie sprawdza. Dziś to nie
szkodzi, bo wszystkie sześć logów ten wiersz mają.
