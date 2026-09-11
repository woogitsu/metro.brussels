# 6.D136 — „każdy przebieg CI zaczyna zimno" obalił log, a winowajcą jest nazwany krok

**11.09.2026**, na `0d26b43`. Pozycja kazała **zmierzyć**, które kroki tworzą bajtkod,
który zestaw zastaje w CI, i dopiero na tej liczbie oprzeć brzmienie zdania.

## 1. Zdanie i to, co je obala

`docs/06-worked-example.md` mówił: „`actions/checkout` robi `git clean -ffdx`,
`__pycache__` jest w `.gitignore`, **więc każdy przebieg CI zaczyna zimno**".

Log joba `tools`, przebieg PR #530:

```
2026-09-11T16:34:17Z   [BAJTKOD] wyczyszczono 7 kat. __pycache__ (201 plikow) pod tools/ — 6.D122
```

201 plików leżało, zanim zestaw wystartował. Pierwsza połowa uzasadnienia jest
prawdziwa — checkout naprawdę zostawia drzewo bez bajtkodu. Druga nie.

## 2. Kto je tworzy — nie hipoteza z wpisu, tylko nazwany krok

Wpis pozycji zgadywał: „kroki, które wcześniej importują `test_suite_runtime_budget`".
**Nieprawda.** Log pokazuje osobny, nazwany krok tego samego joba, stojący
**przed** krokiem budżetu:

```
16:32:47.7629Z  ##[group]Run python3 -m compileall -q tools     <- Compile Python tools
16:32:48.0919Z  ##[group]Run set -euo pipefail                  <- krok budżetu, import
16:34:17.8101Z  [BAJTKOD] wyczyszczono 7 kat. __pycache__ (201 plikow)
```

`python-tests.yml` ma go pod nazwą **`Compile Python tools`**, bezpośrednio nad
krokiem „Run tool tests". Kosztuje **0,33 s** (16:32:47,76 → 16:32:48,09).

## 3. Liczby odtworzone lokalnie, co do pliku

```bash
find . -name __pycache__ -prune -exec rm -rf {} +
python3 -m compileall -q tools
```

```
po compileall: 7 katalogów, 201 plików
   tools/blender/__pycache__   29
   tools/ci/__pycache__         9
   tools/data/__pycache__       2
   tools/physics/__pycache__    3
   tools/tests/__pycache__    130
   tools/track/__pycache__     23
   tools/visual/__pycache__     5
```

**7 i 201** — dokładnie to, co wypisuje CI. Jeden krok tłumaczy całość; nic innego nie
dokłada ani jednego pliku.

## 4. Wniosek zostaje, ale wynika z czego innego

Pułapki w CI nadal nie ma — i to jest ważniejsze niż samo sprostowanie. Ten bajtkod
powstał **z tego samego checkoutu, w tym samym jobie, pół sekundy wcześniej**, więc
przykryć źródła nie może: pułapka z 6.D102 potrzebuje bajtkodu **starszego niż zmiana
pliku**. Chroni więc nie pusty katalog, tylko **jednoczesność**.

## 5. Co zostało zrobione

* Akapit w `docs/06-worked-example.md` **przepisany**, z nazwą kroku, jego poleceniem
  i rozkładem 201 plików po katalogach.
* Trzy bramki w `test_bytecode_staleness.py`: krok musi stać **przed** zestawem, musi
  kompilować **całe `tools`**, a liczby muszą się zgadzać z `compileall` na kopii drzewa.
* `tree_walk.policz_bajtkod` — bliźniak `wyczysc_bajtkod`, który **liczy zamiast
  kasować**. Mieszka tam z tego samego powodu: przedmiotem obu jest katalog pominięty
  w `.gitignore`, a zapadkę `MAX_WOLNO_WPROST` wolno wyłącznie obniżać, więc trzeci
  wyjątek na `os.walk` byłby jej podniesieniem.

## 6. Kontrole negatywne

Baza `test_bytecode_staleness.py`: **16/16** (było 13). `__pycache__` czyszczony przed
każdym przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na czterech
plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | dawne brzmienie wraca do dokumentu | **15/16** |
| KN-2 | krok `compileall` przeniesiony ZA zestaw | **15/16** |
| KN-3 | cel zawężony na `tools/tests` | **16/16 ZIELONA** |
| KN-3b | to samo po poprawce wzorca | **14/16**, dwa testy |
| KN-4 | liczba plików rozjechana ze zmierzoną | **14/16**, dwa testy |
| KN-5 | akapit skasowany zamiast poprawiony | **15/16** |
| KN-6 | liczenie przez `TW.walk` zamiast `policz_bajtkod` | **15/16** |

**KN-3 wyszła zielona i znalazła dziurę w moim własnym wzorcu.** Sprawdzałem obecność
polecenia przez `POLECENIE_KOMPILACJI in tekst`, a `python3 -m compileall -q tools` jest
**przedrostkiem** `python3 -m compileall -q tools/tests`. Zawężenie celu zmieniłoby
liczbę plików z 201 na 130 i **bramka by milczała**. Dziś cel jest wyciągany regexem
sięgającym końca wiersza i **brany z workflowa** także przez test odtwarzający liczby —
więc obie bramki mówią o tym, co CI naprawdę uruchamia. KN-3b jest czerwona.

**KN-6 mierzy, dlaczego liczenie nie może iść przez wspólny filtr**: `TW.walk` odsiewa
`__pycache__` niezależnie od korzenia, więc daje **0 katalogów i 0 plików** zamiast 7
i 201 — odsiewa dokładnie przedmiot pomiaru.

## 7. Weryfikacja

```
  16/16 przeszło        test_bytecode_staleness.py   (było 13)
  2341/2341 przeszło, 122 moduły, KOD=0, RAZEM 168.283 s
```

## 8. Czego nie zrobiłem, i co zauważyłem przy okazji

* **Nie zmieniłem kolejności kroków ani nie zdjąłem czyszczenia** — oba wprost
  w „Poza zakresem".
* **Nie zdjąłem kroku `Compile Python tools`, choć zestaw i tak kasuje jego wynik.**
  Od 6.D122 `test_all.py` usuwa cały `__pycache__` pod `tools/`, więc 201 plików ginie
  parę sekund po powstaniu. Krok ma jednak **drugą rolę**, którą widać w tym samym
  logu: jest najwcześniejszą kontrolą składni całego `tools/` i wypisuje ostrzeżenia
  (`SyntaxWarning: "\\`" is an invalid escape sequence` w trzech modułach). Zdjęcie go
  jest zmianą workflowa i osobną decyzją, nie skutkiem ubocznym tej pozycji.
* **Nie sprawdziłem pozostałych dziewięciu workflowów.** Ten sam krok może stać
  w kilku; pozycja pytała o `python-tests.yml` i log jego joba.
