# 6.D249 — datowanie 6.D108 gubiło commit, bo `git log` upraszcza historię na scalance

**16.09.2026**, na `135d323`. Wejście: `tools/tests/test_report_claims.py`
(`data_stalej`, `data_raportu`), log joba `blender-smoke` **104827561794**,
`reports/6d247-sufit-mierzalnosci-zamiast-nazwy-maszyny.md`. Wyjście: `--full-history`
w `data_stalej`, wypisana asymetria w `data_raportu`, przepisane zdanie w raporcie
6.D247, ten raport.

---

## 1. `main` był CZERWONY i to jest pierwsza rzecz, którą trzeba powiedzieć

```
$ git checkout 135d323          # czysty wierzchołek main
$ python3 tools/tests/test_all.py test_report_claims.py
FAIL test_every_constant_quoted_in_a_report_carries_the_value_from_the_code:
  '6d247-…md:214: `ASERCJI_NAPISOWYCH_RAZEM` mówi 896, kod 909
   [raport jest nie starszy od stałej (2026-09-16 15:31:53+02:00 >= 2026-09-16 15:31:53+02:00)]'
19/20 przeszło
```

Nie zauważyła tego ani jedna bramka **przed** scaleniem, bo przed scaleniem tej
konfiguracji nie było.

## 2. Usterka — i dlaczego nie dało się jej zobaczyć lokalnie

`data_stalej` pyta `git log -1 -G<definicja> -- <pliki>`, czyli „który commit zmienił
tę stałą". **`git log` z pathspec UPRASZCZA HISTORIĘ:** na commicie scalenia idzie
tylko jedną gałęzią, więc commit, który naprawdę zmienił stałą, przestaje być widoczny.

Przebieg `pull_request` stoi **zawsze** na scalance — `CLAUDE.md` §9 mówi to wprost
i każe czytać `HEAD is now at <sha> Merge <gałąź> into <baza>` z logu. W tym wypadku:

```
HEAD is now at 64fb72f Merge fe41b7dd423697410e4b09ced63880cc2f19ca73
                        into 135d323928ab70f5de9d8d1f6c0ce1e136706f5d
```

**Lokalnie tego nie widać i to jest sedno.** `git merge` gałęzi, która bazę już
zawiera, robi **przewinięcie**, a nie scalenie — HEAD jest wtedy zwykłym commitem
i uproszczenie nie ma czego uprościć. Ten sam SHA dawał więc:

| gdzie | wynik |
|---|---|
| lokalnie, po przewinięciu (HEAD = `fe41b7d`) | **20/20** |
| w CI, na scalance (HEAD = `64fb72f`) | **19/20** |

Odtworzone `git merge --no-ff` i zmierzone wprost:

```
$ git log -1 -G'ASERCJI_NAPISOWYCH_RAZEM' -- tools/tests/test_assertion_gate.py
135d323  6.D247: sufit mierzalności … (#636)        <- commit, który wniósł RAPORT

$ git log -1 --full-history -G'ASERCJI…' -- tools/tests/test_assertion_gate.py
fe41b7d  Zapadki po scaleniu — ZMIERZONE z drzewa   <- commit, który zmienił STAŁĄ
```

Stała dostawała więc datę **cudzego** commitu — tego samego, który wniósł cytujący ją
raport — przez co obie daty wychodziły równe **co do sekundy** i twierdzenie nie było
zwalniane, choć zmieniło się po raporcie.

## 3. Asymetria: `--full-history` TYLKO w `data_stalej` — zmierzona, nie przeoczona

Pierwsza poprawka dodawała flagę w obu miejscach. **Zmierzone: to psuje drugą stronę.**
`data_stalej` pyta, który commit ZMIENIŁ stałą — a odpowiedzi szuka `-G` po diffach,
których scalenie domyślnie nie pokazuje. `data_raportu` pyta, kiedy raport ostatnio
TKNIĘTO — a `--full-history` dorzuca tam scalenia, które raport wyłącznie **przeniosły**,
i przesuwa jego datę w przód:

```
z --full-history po obu stronach:
FAIL … '6d241-…md:197: `ASERCJI_NAPISOWYCH_RAZEM` mówi 898, kod 909
        [raport jest nie starszy od stałej (14:44:31 >= 14:00:48)]'
      … `MIN_REPORTS` mówi 354, kod 356 …
      … `MINIMUM_DETAIL_BLOCKS` mówi 310, kod 311 …
19/20 przeszło
```

Trzy twierdzenia **poprawne** zgłoszone jako nieaktualne — czyli 6.D27 z drugiej strony.

## 4. Czego ta poprawka NIE naprawia, powiedziane wprost

Przypadku z `main` **nie naprawia i naprawić nie może**: tam stała i raport wyszły
z **tego samego** commitu (squash `#636`), więc nie istnieje data, która by je
rozdzieliła. Datowanie odpowiada na pytanie „co było wcześniej", a na to pytanie
w jednym commicie nie ma odpowiedzi.

Naprawione zostało więc zdanie w raporcie 6.D247 — **przepisane, nie dopisane obok**.
Stało tam „podniesiona 896 → **897**" i w dniu pisania było prawdą o tamtej gałęzi;
scalenie ścisnęło tę pozycję i cudzą pracę w jeden commit, a zapadka wyszła z niego
na **909**. Liczba w raporcie przestała opisywać drzewo **bez żadnego commitu, który
by ją zmienił**. Zapisana jest teraz RÓŻNICA („o jeden"), która scalenia przeżywa,
a nie para liczb, która ich nie przeżywa.

**Wniosek ogólny, wart osobnej pozycji:** raport, który cytuje BEZWZGLĘDNĄ wartość
zapadki, jest nieodporny na squash-scalenie z cudzą pracą ruszającą tę samą zapadkę.
Bezwzględne wartości należą do komentarza przy stałej, gdzie zmieniają się razem z nią.

## 5. Kontrole negatywne — na odtworzonej scalance, przewidywania przed przebiegiem

| mutacja | przewidziane | wynik |
|---|---|---|
| KN-1 — `--full-history` zdjęte z `data_stalej` | czerwono | **19/20** |
| KN-2 — `--full-history` dodane też do `data_raportu` | czerwono | **19/20** |

Obie strony asymetrii są więc **nośne**: zdjęcie flagi psuje stałą, dodanie jej
psuje raport. Po każdej kontroli plik przywrócony z kopii, nie `git checkout --`;
`md5sum -c` → `OK`.

## 6. Weryfikacja

```
  2508/2508 przeszło
  RAZEM 218.597 s, 2508 testów, 127 modułów
```

Na **odtworzonej scalance** (`git merge --no-ff`, czyli dokładnie to, co robi CI):
`20/20 przeszło` — wobec `19/20` przed poprawką.

## 7. Zauważone, nietknięte

- **Bramki na tę usterkę NIE POSTAWIŁEM i mówię to wprost.** Wymagałaby zbudowania
  repozytorium próbnego z prawdziwym commitem scalenia i dwiema gałęziami — to jest
  wykonalne (6.D248 robi coś podobnego dla `git status`), ale jest osobną pozycją,
  a `main` jest czerwony teraz. Do czasu jej powstania usterkę tej klasy złapie
  dopiero CI, i to jest zapisane zamiast przemilczane.
- Cała dzisiejsza seria obejść („zapadki osobnym commitem, bo `git log -G` nie zagląda
  w scalenia") opisywała **objaw tej samej usterki**. Obejście działa tylko wtedy, gdy
  checkout jest przewinięciem; na scalance PR-a nie działa. Komunikaty tamtych commitów
  zostają — są prawdziwe o tym, co zmierzyłem wtedy — ale prawdziwą przyczyną jest ta.
