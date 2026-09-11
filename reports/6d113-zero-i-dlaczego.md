# 6.D113 — zero mutacji na starym bajtkodzie, i dlaczego akurat zero

**Zmierzone 10–11.09.2026 na:** `c98321b` (gałąź robocza nad `875f495`), kontener tej sesji.
**Przyrząd:** `tools/tests/mutation_sweep.py` (`bajtkod_przykrywa_zrodlo`, `usun_bajtkod`,
`check_one`), `tools/tests/test_bytecode_staleness.py` (`_zapisz`, `_sekwencja`),
dwa prawdziwe przebiegi przeglądu mutacyjnego — drzewo tylko do odczytu, mutacje idą
do kopii `git worktree`.

---

## 1. Liczba, której żąda wpis

```
[MUTACJE] --only 'tools/blender/lod_paths.py' … 2 mutacji
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0
[MUTACJE] mutacji zapisanych pod ważnym starym bajtkodem: 0

[MUTACJE] --only 'tools/track/crs.py' … 29 mutacji
[MUTACJE] rozstrzygniętych 29/29, zabitych 24, ocalałych 5 (w tym 0 nieuruchomionych)
[MUTACJE] mutacji zapisanych pod ważnym starym bajtkodem: 0
```

**Zero na 31 mutacji.** Pole `stary_bajtkod` stoi w **29 z 29** wpisów dziennika
większego przebiegu — sprawdzone czytaniem `jsonl`, żeby „zero" nie okazało się
brakiem pola:

```
metro-mutacje-de597df7b650-26a627d3.jsonl wpisów: 29 pole stary_bajtkod: {False: 29}
```

Dzienniki sprzed tej pozycji pola nie mają i to jest w porządku — licznik czyta je
przez `.get`, więc stary dziennik nie wywraca wznowienia.

## 2. Dlaczego zero — i dlaczego to nie była zasługa

Pułapka 6.D102 wymaga, żeby zapis do pliku trafił w **tę samą sekundę** co zapis,
z którego skompilowano leżący `.pyc`, przy **tym samym rozmiarze**. W sweepie sekwencja
na jeden plik wygląda tak:

```
T        zapis mutacji do F
T…T+D    przebieg zestawu — import kompiluje `.pyc` i zapisuje w nim parę (T, rozmiar)
T+D      przywrócenie F   (bez importu, więc bez nowego `.pyc`)
T+D      zapis następnej mutacji
```

Następny zapis do `F` dzieli od zapamiętanej sekundy **całe `D`** — czas jednego
przebiegu zestawu. Zmierzone w tej sesji: **115–137 s**. Sekundy nie mają więc jak się
zejść i para nigdy nie pasuje.

**Ale to była odporność z przypadku, nie z projektu**, i dokładnie tego nie wiedział
dotąd nikt — pole „Wyjście" wpisu żąda zapisania właśnie tego. Warunek brzmi „zestaw
trwa dłużej niż sekundę", nigdzie nie był zapisany i nigdzie nie był pilnowany. Wystarczyłby
jeden przebieg kończący się w ułamku sekundy — sweep w innym repozytorium, mniejszy zestaw,
przerwanie przed pierwszym testem — żeby „PRZEŻYŁA" zaczęło czasem znaczyć „nie wykonano".

Od tej pozycji odporność nie zależy już od czasu: `check_one` **kasuje `.pyc` zmutowanego
pliku** przed każdym przebiegiem, a przedtem pyta, czy pułapka zachodziła — i ta liczba
idzie do dziennika i do wypisu **zawsze**, także gdy wynosi zero. Milczenie byłoby
nieodróżnialne od braku pomiaru.

## 3. Kolejność pytania i kasowania jest treścią

`check_one` pyta **przed** skasowaniem. Odwrotna kolejność dałaby `stary_bajtkod`
zawsze `False` — czyli przyrząd meldujący pomiar, którego nie zrobił. To jest ta sama
rodzina, którą projekt tropi od 6.D27, i dlatego ma osobny test, a nie komentarz.

Sam detektor też jest przybity **w obie strony**: bez `.pyc` → `False`, przy zastawionej
pułapce → `True`, po samej zmianie czasu źródła → `False`. Reguła „zawsze `True`"
spełniałaby połowę warunków idealnie.

## 4. Usterka znaleziona po drodze: bramka 6.D102 zależy od losu zegara

Przegląd mutacyjny **nie dawał się uruchomić** — przerywał na kalibracji:

```
[MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
['test_stary_bajtkod_potrafi_ukryc_mutacje:']
```

Powód: `_sekwencja` z 6.D102 liczy na to, że zapis bazy i zapis mutacji trafią w tę
samą sekundę zegara. Zmierzone 11.09.2026, **200 przebiegów bez obciążenia**:

```
różne sekundy zapisu: 5      mutacja WIDOCZNA (test padał): 5
```

Pięć na dwieście, czyli 2,5 % — a przy czterech zestawach naraz (kalibracja sweepa)
wystarczająco często, żeby zatrzymać narzędzie. **Ta sama przyczyna tłumaczy jednorazowe
zapalenie `test_sam_PYTHONDONTWRITEBYTECODE_nie_wystarcza`, które 6.D111 zapisało jako
niewyjaśnione** — to nie była zagadka, tylko ten sam los zegara.

Poprawka: czas zapisu mutacji jest **ustawiany** przez `os.utime` na czas zapisu bazy.
Po niej, ten sam pomiar na 200 przebiegach:

```
mutacja WIDOCZNA (test by padł): 0
```

Ustawienie czasu nie zamienia pomiaru na założenie: pułapka bierze się z pary
`(mtime w sekundach, rozmiar)`, a `os.utime` odtwarza dokładnie ten warunek, zamiast
czekać, aż wypadnie sam. To, co test mierzy — czy CPython przy tej parze sięgnie po stary
bajtkod — zostaje bez zmian.

## 5. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem, po każdej `md5sum -c` na trzech plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | `usun_bajtkod` przestaje kasować | 119/121, dwa testy |
| KN-2 | detektor zawsze mówi „nie ma pułapki" | 120/121 |
| KN-3 | detektor zawsze mówi „pułapka jest" | 120/121 |
| KN-4 | `check_one` kasuje ZANIM zapyta | 120/121, zgłasza `['kasowanie', 'pytanie']` |
| KN-5 | sekwencja wraca do brania czasu z zegara | 6/7 w `test_bytecode_staleness.py` |

**KN-5 jest tu najważniejsza i najtrudniejsza**, bo mierzy coś, czego zwykły przebieg
nie odróżnia: wersja zegarowa przechodzi w 195 przebiegach na 200. Test pyta więc nie
o wynik, tylko o to, **czy zapis mutacji dostał czas ustawiony** — inaczej zielony
przebieg nie odróżniałby procedury działającej od procedury działającej losowo.

**KN-2 i KN-3 są parą i osobno nie znaczą nic:** detektor stały w którąkolwiek stronę
spełnia połowę asercji.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_mutation_sweep.py
  121/121 przeszło          (było 117)

$ python3 tools/tests/test_all.py test_bytecode_staleness.py
  7/7 przeszło              (było 6)

$ python3 tools/tests/mutation_sweep.py --only tools/track/crs.py --workers 4 --no-coverage
  rozstrzygniętych 29/29, zabitych 24, ocalałych 5
  mutacji zapisanych pod ważnym starym bajtkodem: 0
```

## 7. Czego nie zrobiłem

- **Nie zmieniłem definicji „mutacja zabita"** ani nie przeliczałem dawnych werdyktów
  sweepa — pole „Poza zakresem" wyklucza oba wprost.
- **Nie puściłem pełnego przeglądu** (985 mutacji osiągalnych): przy ~2 minutach na
  mutację i czterech robotnikach to kilkanaście godzin. Zmierzone są dwa przebiegi
  ograniczone `--only`, 31 mutacji razem; rozstrzygnięcie o zerze opiera się na nich
  **i** na warunku z §2, który mówi, dlaczego liczba nie zależy od próbki.
- **Nie kasuję `__pycache__` całego drzewa roboczego**, tylko `.pyc` pliku zmutowanego:
  reszta bajtkodu jest poprawna, a kasowanie wszystkiego dokładałoby kompilację całego
  `tools/` do każdego z setek przebiegów.

## 8. Zauważone przy okazji

- **Pięć mutacji `crs.py` ocalało mimo uruchomienia** (`wykonana` = `True`):
  `212 argument 6 -> 7`, oraz po parze `operator < -> <=` i `prog 1e-12 -> 1.01e-12`
  w wierszach 300 i 419. Wszystkie dotyczą progów zbieżności iteracji — zmiana progu
  o procent nie zmienia wyniku w granicach tolerancji testów. To jest wynik o pokryciu,
  nie o bajtkodzie, i do zakresu tej pozycji nie należy.
- **Wznowienie z dziennika sprzed tej pozycji podstawi wpisy bez pola `stary_bajtkod`.**
  Licznik czyta je przez `.get`, więc nie wywraca się i nie zawyża — ale w takim
  przebiegu „zero" znaczy „zero wśród wpisów nowych", a nie „zero w całym dzienniku".
  Wypis tego nie rozróżnia; rozróżnienie wymagałoby trzeciego stanu w liczniku.
