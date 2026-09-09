# Trzynaście plików po terminie, jedno okno i zero zdań nazywających oś aktualną (6.D46)

**Zmierzone 09.09.2026 na:** `5e47b66`, kontener tej sesji.
**Przyrząd:** `python3 tools/track/data_freshness.py` (także `--strict` i `--out`),
skan 208 plików (`docs/*.md` — 25, `reports/*.md` — 182, `README.md`),
`.github/workflows/python-tests.yml`, `python3 tools/tests/test_all.py`.

---

## 1. Trzynaście przeterminowanych pozycji

Wzięte z przebiegu narzędzia (`--out`), nie przepisane z wpisu kolejki. Dzień
odniesienia narzędzia: **2026-09-09**.

| plik | okno ważności | pobrane | dni po terminie |
|---|---|---|---|
| `data/network/shapes-manifest.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L1_A.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L1_A.provenance.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L1_B.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L1_B.provenance.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L2_E.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L2_E.provenance.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L5_C.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L5_C.provenance.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L5_D.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L5_D.provenance.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L6_F.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |
| `data/track/L6_F.provenance.json` | 2026-03-02 … 2026-08-28 | 2026-09-01 | 12 |

Wszystkie trzynaście niosą `retrieved_after_expiry: true`: dane pobrano 01.09.2026,
cztery dni **po** wygaśnięciu okna. Liczba dni po terminie rośnie z każdym dniem
i dziś wynosi 12 — dlatego stoi tu razem z datą pomiaru w nagłówku.

**To jest trzynaście PLIKÓW, ale JEDNO okno.** Zmierzone:

```
różnych okien (valid_from, valid_to): 1  {('2026-03-02', '2026-08-28')}
różnych dat pobrania: {'2026-09-01'}
```

Komunikat narzędzia mówi „przeterminowanych okien: 13" i **liczy w nim pliki, nie
okna**. Nie jest to usterka rachunku — wszystkie trzynaście naprawdę są po terminie —
ale nazwa sugeruje trzynaście niezależnych spraw, gdy jest jedna: zestaw shapefile'ów
STIB o zadeklarowanej ważności do 28.08.2026, z którego zbudowano sześć osi i ich
prowenancje. Zapisane w §5 jako zauważone i nietknięte.

## 2. Zdania nazywające oś aktualną: ZERO

Przeszukane **208 plików**: `docs/*.md` (25), `reports/*.md` (182), `README.md` —
katalogi te nie mają podkatalogów z markdownem (`find docs reports -name '*.md'` daje
207, tyle samo co suma wyżej bez README).

Skan brał każdy wiersz, w którym stoi słowo z rodziny `aktualn|najnowsz|śwież|bieżąc`
**i jednocześnie** rzeczownik z rodziny `oś|dane|archiwum|snapshot|GTFS|shapefile`.
Dwadzieścia wierszy do przejrzenia, przeczytane po kolei. **Ani jeden nie nazywa osi
aktualną.** Dwa mówią wprost coś przeciwnego:

```
docs/09-data-provenance.md:148   „…faktem, który ma być widoczny, zanim ktoś nazwie oś »aktualną«"
reports/packages-BF-alignment.md:446  „żadnej z tych osi nie wolno nazywać »aktualną« bez świeższego snapshotu"
```

Pozostałe osiemnaście to daty snapshotu podane jako daty (`docs/00-network-data.md:3`),
odsyłacze do rejestru źródeł, tytuły pozycji kolejki i cytaty z tego samego wpisu 6.D46.
Jedyny wiersz, przy którym się zawahałem, to `docs/00-network-data.md:36` —
„**Aktualne** źródła pierwotne i ich role są w `data/network/sources.json`". Mówi on
o tym, **które źródła są dziś pierwotne**, a nie o świeżości pobranych z nich danych;
zostawiam bez zmian i wypisuję tutaj, żeby decyzja była widoczna, a nie domyślna.

Zgodnie z polem „Wyjście" wpisu: **zero jest poprawnym wynikiem i pozycja kończy się
bez bramki.** Bramka na kształt takich zdań miała powstać dopiero przy więcej niż
jednym miejscu.

## 3. Premisa wpisu była nieprawdziwa i to jest wynik pomiaru

Wpis 6.D46 mówił:

> `main()` w `tools/track/data_freshness.py` ma **dokładnie jedno** `return 0`
> i żadnej innej drogi wyjścia.

Druga połowa tego zdania jest nieprawdziwa. `main()` ma **dwie** drogi wyjścia:

```python
    if args.strict and expired:
        raise SystemExit(f"BŁĄD: {len(expired)} okien ważności minęło")
    return 0
```

Zmierzone:

```
$ python3 tools/track/data_freshness.py --strict ; echo "kod: $?"
BŁĄD: 13 okien ważności minęło
kod: 1
```

Narzędzie **umie** odmówić i robi to poprawnie. Nie umie tego krok CI — ale nie dlatego,
że mu brakuje drogi, tylko dlatego, że wywołuje narzędzie **bez `--strict`**, i to
z zapisanym powodem:

```yaml
      - name: Report data freshness
        # Informacyjnie, bez --strict: przeterminowane okno ważności nie jest błędem
        # samo w sobie, ale ma być widoczne w logu, zanim ktoś nazwie oś aktualną.
        run: python3 tools/track/data_freshness.py
```

To jest **wybór z uzasadnieniem**, a nie brakująca droga wyjścia. Wywołanie
`data_freshness.py` stoi w repozytorium w dokładnie jednym miejscu CI (zmierzone
`grep` po `.github/workflows/*.yml` i `tools/ci/*.sh`), więc nie ma drugiego kroku,
który by to nadrabiał albo psuł.

Zostaje więc jedna prawdziwa połowa pierwotnego zarzutu: **warunek wypowiedziany przez
narzędzie („oś z takiego archiwum nie może być nazywana aktualną") nie jest przez nic
pilnowany.** Pomiar z §2 mówi jednak, że nie ma go dziś czego pilnować — nikt takiego
zdania nie napisał, a dwa miejsca w drzewie mówią wprost odwrotnie.

## 3a. Kontrola detektora — skan, który nic nie znalazł, jest bezwartościowy bez niej

Zero z §2 znaczy coś tylko wtedy, gdy ten sam skan **umie** znaleźć zdanie, którego
szuka. Do kopii drzewa w katalogu tymczasowym dopisano jedno zdanie i puszczono ten sam
skan:

```
bez raportu:      plików 208, wierszy 20
kopia z wstawką:  plików 209, wierszy 29
wstawione zdanie ZŁAPANE: True
  [('00-network-data.md', 38, 'Oś pakietu A jest aktualna wobec dzisiejszych danych STIB.')]
```

Zdanie wymyślone na potrzeby kontroli **nie zostało dopisane do drzewa** — kopia leży
w katalogu tymczasowym sesji, a `docs/00-network-data.md` w repozytorium nie ma ani
jednego znaku zmiany (`git status` czysty dla tego pliku).

**Liczby 208 i 20 pochodzą z drzewa BEZ tego raportu** i to jest zapisane celowo:
sam ten plik pisze o świeżości danych, więc dokłada do skanu osiem własnych wierszy
(20 → 28 po jego dodaniu). Raport, który liczy zdania o aktualności, jest częścią
zbioru, który liczy — bez tego zastrzeżenia następny pomiar wyszedłby inny i wyglądał
na rozjazd.

## 4. Weryfikacja

```
$ python3 tools/track/data_freshness.py ; echo "kod: $?"
[ŚWIEŻOŚĆ] przeterminowanych okien: 13. To nie jest błąd sam w sobie — sieć metra nie
zmienia przebiegu co tydzień — ale oś zbudowana z takiego archiwum nie może być
nazywana aktualną.
kod: 0

$ python3 tools/track/data_freshness.py --strict ; echo "kod: $?"
BŁĄD: 13 okien ważności minęło
kod: 1

$ python3 tools/tests/test_all.py ; echo "kod: $?"
  RAZEM 2082 testów, 111 modułów
kod: 0
```

Liczba 13 w tabeli §1 pochodzi z `--out` tego samego przebiegu, nie z wpisu kolejki.
Zestaw bez zmian: ta pozycja nie tyka kodu ani danych.

## 5. Czego świadomie nie zrobiono

**Nie postawiono bramki na zdania o aktualności** — pomiar dał zero miejsc, a wpis
żądał bramki dopiero przy więcej niż jednym. Bramka na zerowym zbiorze pilnowałaby
kształtu zdania, którego nikt nie napisał, i pierwszy fałszywy alarm skończyłby się
jej wyłączeniem (6.D27).

**Nie zmieniono kroku CI na `--strict`.** Próg świeżości jest decyzją właściciela,
a wpis wprost jej nie podejmuje. Warto jednak zapisać, jak ta decyzja dziś wygląda
liczbowo: **dziś `--strict` zaczerwieniłby CI natychmiast**, bo wszystkie sześć osi
pochodzi z jednego, minionego okna.

**Nie poprawiono komunikatu narzędzia** („przeterminowanych okien: 13" liczy pliki,
nie okna — §1). Zmiana jest jednowierszowa, ale wyjście narzędzia jest czytane przez
`test_data_freshness.py` i przez krok CI, więc należy do osobnej pozycji z własną
kontrolą negatywną, a nie do raportu o oknach ważności.

**Nie odświeżono danych.** `data/` jest tylko do odczytu, a pobranie nowego archiwum
zmienia manifest prowenancji — pole „Poza zakresem" wpisu.
