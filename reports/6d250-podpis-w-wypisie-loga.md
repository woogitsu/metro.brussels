# 6.D250 — `log.showSignature` wywracał trzy bramki na kodzie POPRAWNYM

**16.09.2026**, na `0f489b6`. Wejście: `tools/tests/test_report_claims.py`
(`_data`, `data_z_commita`, `data_stalej`, `data_raportu`). Wyjście: odporne parsery,
`--no-show-signature` w obu wywołaniach `git log`, bramka
`test_datowanie_PRZEZYWA_wiersze_doklejone_przed_wypisem_loga`, ten raport.

---

## 1. Usterka — fałszywy alarm, nie cisza

Gdy w konfiguracji gita stoi `log.showSignature = true`, `git log` dokleja **przed**
wypisem wynik weryfikacji podpisu, więc `--format=%cI` przestaje być jedyną treścią
wyjścia. Zmierzone na tym repozytorium, przez dopisanie ustawienia do `~/.gitconfig`
i **bez żadnej zmiany w kodzie**:

```
FAIL test_every_constant_quoted_in_a_report_carries_the_value_from_the_code:
     Invalid isoformat string: 'signature\n813f660c… 2026-09-02T21:47:55+00:00'
FAIL test_kazde_twierdzenie_dostaje_POWOD_takze_gdy_jest_pilnowane: (to samo)
FAIL test_ksztalt_w_jednych_grawisach_daje_SAME_CYTATY: (to samo)
17/20 przeszło
```

**Liczbą tej pozycji są TRZY PADAJĄCE BRAMKI, a nie ułamek `17/20`** — i to zdanie
jest dopisane 16.09.2026, bo mianownik zdążył się zestarzeć w ciągu doby. Po scaleniu
#640 ten sam pomiar na `origin/main` daje **18/21**: padają te same trzy bramki, a
modułowi przybył jeden test. Wartość bezwzględna opisuje więc dzień pomiaru, nie
usterkę; usterkę opisuje liczba padających i ich nazwy, i te są niezmienne.

**To jest 6.D27 od strony fałszywego alarmu i przez to gorsze niż cisza.** Bramka
meldowała usterkę, której nie ma, komunikatem (`Invalid isoformat string`)
nieodróżnialnym od prawdziwej awarii. Ktoś, kto zobaczy to u siebie, pójdzie szukać
usterki w raportach — a raporty są w porządku.

## 2. DWIE obrony, bo bronią przed czym innym

- **`--no-show-signature`** w obu wywołaniach `git log` — usuwa znany powód.
- **Parsery biorą OSTATNI niepusty wiersz** (`_data`, `data_z_commita`) — przeżywają
  **każdy** doklejony wiersz, także taki, którego dziś nie znamy.

**Sama flaga NIE wystarcza i to jest zmierzone, nie przypuszczane.** Flaga dotyczy
wywołań wymienionych z ręki; nowe wywołanie `git log` w tym module odtworzyłoby
usterkę bez śladu. Kontrola KN-3 dopisała dokładnie takie wywołanie:

```
nowe wywolanie PADA: ValueError Invalid isoformat string:
  "gpg: directory '/root/.gnupg' created
   gpg: keybox '/root/.gnupg/pubring.kbx' created
   gpg: Signature made Sun Sep 13 21:29:28 2026 UTC
   gpg:                using RSA key B5690EEEBB952194
   gpg: Can't check signature: No public key
   2026-09-13T23:29:28+02:00"
```

**Pięć** doklejonych wierszy, nie jeden — a `--format` stoi w ostatnim.

## 3. Bramka jest SYNTETYCZNA i to jest wybór z pomiaru, a nie wygoda

Pierwsza wersja budowała repozytorium próbne z `log.showSignature=true` i wołała
prawdziwe `data_raportu`. **Kontrola negatywna ją obaliła:** zdjęcie
`--no-show-signature` dawało przy niej **21/21 NA ZIELONO**.

Powód zmierzony: git dokleja te wiersze tylko wtedy, gdy commit jest **podpisany**
albo gdy `gpg.format` wskazuje backend zgłaszający błąd. Commity repozytorium
próbnego są niepodpisane, więc fixture nie odtwarzał niczego:

```
repozytorium próbne, log.showSignature=true, commit niepodpisany:
  2026-09-16T15:23:24+00:00        <- czysto, ani jednego doklejonego wiersza
```

Bramka wierna wymagałaby **kluczy podpisujących w środowisku przebiegu** — czyli
zależności od cudzej konfiguracji, a to jest dokładnie ta klasa, przed którą ta
pozycja broni. Mierzone jest więc **zachowanie parsera** na wejściu, które git w takiej
konfiguracji produkuje: trzy kształty doklejki (`No signature`, `signature\n<sha>`,
pięciowierszowy blok `gpg:`) plus kontrola, że commit **graniczny** nadal daje `None`.

To jest ta sama pułapka, na którą złapałem się dziś przy 6.D248: test, który **nie
zapala się na zepsutym kodzie**, wygląda identycznie jak test, który przechodzi.
Kontrola negatywna jest jedyną rzeczą, która je rozróżnia.

## 4. Kontrole negatywne — przewidywania wypisane PRZED przebiegiem

| mutacja | przewidziane | wynik |
|---|---|---|
| KN-1 — `_data` z powrotem na całym napisie | czerwono | **20/21** |
| KN-2 — `data_z_commita` z powrotem na `wypis.split` | czerwono | **20/21** |
| KN-3 — parsery cofnięte, flagi zostają, NOWE wywołanie bez flagi | czerwono + nowe wywołanie pada | **20/21**, `ValueError` z pięciowierszową doklejką |
| KN-0 (obalona) — fixture z repozytorium próbnym, flaga zdjęta | czerwono | **21/21 ZIELONO** — fixture nie odtwarzał usterki |

Po każdej plik przywrócony z kopii, nie `git checkout --`; `md5sum -c` → `OK`.

## 5. Weryfikacja

```
  2509/2509 przeszło
  RAZEM 230.439 s, 2509 testów, 127 modułów
```

Z wrogim `~/.gitconfig` (`log.showSignature = true`), na kodzie z poprawką:
moduł **bez ani jednej czerwieni** — wobec **trzech** bez niej (w liczbach dnia
pomiaru 20/20 wobec 17/20; po #640 byłoby 21/21 wobec 18/21, patrz §1).

## 6. Zauważone, nietknięte

- Sprawdzone osobno i **nieszkodliwe**: `status.showUntrackedFiles = no`,
  `merge.ff = only`, `log.date = raw`. Ryzykiem jest wyłącznie podpis.
- `data_stalej` przyjmuje pathspec z `pliki_definicji()`; gdy stała jest zdefiniowana
  w **wielu** plikach, uproszczenie historii liczy się dla całego zestawu i może
  działać inaczej niż w przypadku jednoplikowym, który zmierzyłem przy 6.D249.
  Nie badałem — osobna pozycja.
- Nie przeszukałem reszty drzewa pod kątem innych wywołań `git log --format`, które
  miałyby ten sam problem. `test_report_claims.py` jest jedynym modułem, który datuje
  twierdzenia, ale zdania tego nie zmierzyłem.
