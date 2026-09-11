# 6.D127-poprawka — zapadka asercji zabiła przegląd mutacyjny

**11.09.2026**, na `6d9c5dc`. Nie jest to pozycja z kolejki: jest to regres, który
wszedł do `main` tego samego dnia razem z 6.D127 (#520), a znalazł go **jedyny sposób,
jakim się go dało znaleźć — uruchomienie narzędzia**, nie czytanie kodu.

## 1. Objaw

Przegląd mutacyjny odmawia policzenia czegokolwiek:

```
$ python3 tools/tests/mutation_sweep.py --only lod_paths --no-coverage \
    --journal /tmp/mieszany.jsonl --workers 1
[MUTACJE] --only 'lod_paths' dopasowało 1 plik(ów) docelowych i złapało 2 mutacji z 1 moduł(ów)
[MUTACJE] wznowienie z /tmp/mieszany.jsonl: 1 z 2 już policzonych
[MUTACJE] 1 mutacji do policzenia, 1 robotników, commit 6d9c5dc
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
          ['test_lista_asercji_bez_komunikatu_moze_tylko_malec:'] — dopóki tak jest,
          każda mutacja zostanie zapisana jako zabita, a przegląd nie mierzy niczego
```

Kod wyjścia 2. Ani jedna mutacja nie została policzona.

## 2. Mechanizm

Przegląd pracuje na kopii `git worktree add --detach HEAD`, w której
`neutralise_own_tests` podmienia `tools/tests/test_mutation_sweep.py` na zaślepkę:
plik **zostaje** (jego ścieżkę wymieniają raporty), ale treści już nie ma. Zaślepka
ma dwie asercje i **obie niosą komunikat**, więc moduł wypada z `nieme_w_drzewie()`.

Zapadka z 6.D127 czyta to jako „wpis na liście dla modułu, który zniknął z drzewa"
i żąda zdjęcia wpisu. Zmierzone w drzewie roboczym na `6d9c5dc`:

```
  FAIL test_lista_asercji_bez_komunikatu_moze_tylko_malec: wpis na liście dla modułu,
       który już nie ma ani jednej takiej asercji (albo zniknął z drzewa):
       ['test_mutation_sweep.py'] — zdejmij wpis w tym samym commicie
  2189/2190 przeszło
```

Jeden czerwony test na 2190. Skutek nie jest jednak „jeden czerwony test": to
`baseline_problem` czyta zestaw jako padający w czystym drzewie i **przerywa przegląd
przed pierwszą mutacją**, bo wyrocznia „zestaw padł, czyli mutacja wykryta" przestaje
być prawdziwa. Narzędzie znika, a jedyne, co o tym mówi, to jedna linia na stderr —
której nikt nie czyta, dopóki nie uruchomi przeglądu.

**To jest DRUGI raz.** Pierwszy był 07.09.2026: `test_module_entrypoints.py` zażądało
od każdego `test_*.py` strażnika `__main__`, którego zaślepka wtedy nie miała, i tak
samo wywracało każdy przegląd (opisane w docstringu zaślepki). Wspólny kształt obu:
**bramka chodząca po `tools/tests/` nie wie, że jeden z tych plików może nie być sobą.**

## 3. Poprawka

`mutation_sweep.py` dostaje dwie rzeczy publiczne:

* `WLASNE_TESTY = ("tools", "tests", "test_mutation_sweep.py")` — jedno źródło tej
  nazwy, zamiast wpisywania jej drugi raz po stronie bramki (6.B28);
* `czy_zaslepka(zrodlo)` — rozpoznanie po **całej** treści, nie po fragmencie.

`test_assertion_gate.py` dostaje `moduly_zaslepione(katalog=None)` i używa go w trzech
miejscach zapadki: moduł zaślepiony nie liczy się jako „zniknął", nie liczy się jako
„ubyło", a jego wpis wchodzi do sumy **z listy**, żeby suma dotyczyła tego samego
zbioru modułów, o którym mówi zapadka.

## 4. Czego pomiar nie potwierdził — dwa razy, oba moje

**Pierwsza wersja wyjątku miała własny test żądający zbioru PUSTEGO** („zaślepka ma
prawo istnieć wyłącznie w drzewie roboczym przeglądu"). Zdanie jest prawdziwe, bramka
z niego zrobiona — nie: w drzewie roboczym przeglądu zapaliła się dokładnie tak samo
jak ta, którą naprawiałem.

```
  FAIL test_w_drzewie_repozytorium_nie_ma_ani_jednego_modulu_zaslepionego:
       w drzewie repozytorium leży zaślepka przeglądu: ['test_mutation_sweep.py']
  2193/2194 przeszło
```

Bramka nie umie odróżnić repozytorium od jego kopii roboczej, bo treść pliku wygląda
w obu tak samo. Test jest **przepisany, a nie dopisany obok**: dziś pilnuje tego, co da
się sprawdzić z treści (wyjątek obejmuje wyłącznie moduł, który przegląd podmienia),
a pytanie „czy zaślepka nie została zacommitowana" zadaje osobny test — **gitowi**,
przez `git show HEAD:…`, bo tylko ono te dwa przypadki rozróżnia.

**KN-3 wyszła ZIELONA i pokazała dziurę, którą sam zrobiłem.** Podstawienie
`zaslepione = set(NIEME_ASERCJE)` w zapadce opróżnia `w_drzewie` ze wszystkiego, co
lista pilnuje, a suma dostaje te same 2377 z drugiego składnika — **zapadka staje się
pusta i zostaje zielona**. Osobny test szerokości wyjątku tego nie widział, bo woła
`moduly_zaslepione()` po swojemu. Asercja szerokości stoi od tej kontroli **w samej
zapadce**; KN-3b jest czerwona.

## 5. Kontrole negatywne

Baza `test_assertion_gate.py`: **34/34**. `__pycache__` czyszczony przed każdym
przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na obu plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | `czy_zaslepka` zawsze `False` | **32/34**, dwa testy |
| KN-2 | rozpoznanie po fragmencie (`"Zaślepka" in zrodlo`) | **31/34**, trzy testy |
| KN-3 | wyjątek rozlany na wszystkie moduły listy | **34/34 ZIELONA** — patrz §4 |
| KN-3b | to samo po dopisaniu asercji szerokości do zapadki | **33/34** |
| KN-4 | `WLASNE_TESTY` wskazuje inny plik | **33/34** |
| KN-5 | `git show` pytany o ścieżkę spoza HEAD | **33/34**, kod 128 nazwany w komunikacie |
| KN-6 | drugi składnik sumy zdjęty z zapadki | **34/34 ZIELONA** |
| KN-6b | to samo, mierzone w drzewie roboczym przeglądu | **33/34** |

**KN-6 zielona jest prawdziwym wynikiem, a nie słabą kontrolą, i KN-6b mówi dlaczego.**
Na drzewie repozytorium zaślepki nie ma, więc drugi składnik sumy jest zerem i jego
zdjęcie nie zmienia niczego. Dopiero w drzewie roboczym przeglądu składnik ma wartość:

```
  FAIL test_lista_asercji_bez_komunikatu_moze_tylko_malec: suma z listy 2377,
       suma z drzewa 2301 (+ 76 z 1 modułów zaślepionych: ['test_mutation_sweep.py']),
       pomiar z 11.09.2026 mówił 2377
```

2301 + 76 = 2377. Składnik jest **zmierzoną koniecznością**, nie ubezpieczeniem —
inaczej niż maska z 6.D131, i różnica między jednym a drugim jest właśnie taka: KN-6b
istnieje, a odpowiednika dla maski nie było.

## 6. Weryfikacja

Zestaw w drzewie repozytorium:

```
  34/34 przeszło        test_assertion_gate.py  (było 29)
```

Zestaw w **drzewie roboczym przeglądu**, czyli tam, gdzie regres siedział:

```
  przed poprawką:  2189/2190 przeszło,  kod 1
  po poprawce:     2195/2195 przeszło,  kod 0,  RAZEM 137.823 s, 122 moduły
```

## 7. Czego nie zrobiłem

* **Nie obniżyłem wpisu `test_mutation_sweep.py` w `NIEME_ASERCJE`** — komunikat
  zapadki tego żądał, ale żądanie było skutkiem usterki, a nie stanem drzewa:
  w repozytorium ten moduł ma tych asercji 76, tak jak mówi lista.
* **Nie dopisałem komunikatów do żadnej asercji.** To jest 6.D144 i ma własne pole
  „Skończone, gdy" z liczbą.
* **Nie obroniłem zaślepki przed TRZECIĄ bramką tego kształtu.** `czy_zaslepka` jest
  publiczne i każda następna bramka chodząca po `tools/tests/` może go zawołać, ale
  nic jej do tego nie zmusza; zmuszenie wymagałoby przebiegu całego zestawu w drzewie
  z zaślepką jako bramki, a to 138 s na każdy przebieg zestawu.
