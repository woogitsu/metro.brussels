# Bramka od odsyłaczy w puste miejsce nie widziała ścieżek z kropką (6.D59)

**Zmierzone 09.09.2026 na:** `8ef2368`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_report_hygiene.py` (`PATH_TOKEN`, `_paths_in`,
`ROZSZERZENIA_BEZ_TRAFIEN`), 181 raportów w `reports/`,
`python3 tools/tests/test_all.py`.

---

## 1. Usterka

`PATH_TOKEN` startował token znakiem z klasy `[A-Za-z0-9_]`:

```python
PATH_TOKEN = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.'
                        r'(?:py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv))`')
```

Ścieżka zaczynająca się kropką nie wchodziła więc do skanu **wcale** — a bramka,
której ten wzorzec służy, ma dokładnie jedno zadanie: łapać odsyłacze w puste miejsce.
Zmierzone na dzisiejszym katalogu:

```
trafień pod `.github/`  starym wzorcem:  0  (w 0 raportach)
trafień pod `.github/`  nowym wzorcem:  26  (w 18 raportach)
trafień ogółem:  1579 -> 1605, przyrost 26, wszystkie z przedrostkiem `.github`
nowych ścieżek NIEISTNIEJĄCYCH w drzewie: 0
```

Wpis kolejki mówił o **22 wzmiankach w 15 raportach** — liczba z 09.09.2026 rano;
od tamtej pory doszły raporty i dziś jest ich 26 w 18. Ani jedna z nich nie była
sprawdzana, i ani jedna nie jest dziś zepsuta: pozycja nie naprawia usterki
w raportach, tylko **przyrząd, który jej nie umiał zobaczyć**.

To była też jedyna przyczyna zerowego pokrycia rozszerzenia `yml`, wypisana wprost
przy jego wpisie w `ROZSZERZENIA_BEZ_TRAFIEN`.

## 2. Co powstało

Kropka dopuszczona **tylko przed nazwą katalogu**:

```python
PATH_TOKEN = re.compile(r'`((?:\.(?=[A-Za-z0-9_]+/))?[A-Za-z0-9_][A-Za-z0-9_./-]*\.'
                        r'(?:py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv))`')
```

Wygląd na przód (`(?=[A-Za-z0-9_]+/)`) jest tu treścią, nie ozdobą: bez niego wzorzec
otwierałby się na każdy dotfile, a `.gitignore` czy `.plik.md` **nie są** ścieżkami,
które ta bramka umie sprawdzić. Zmierzone na parach:

```
`.github/workflows/python-tests.yml`     stary: []   nowy: ['.github/workflows/python-tests.yml']
`.claude/skills/heartbeat/SKILL.md`      stary: []   nowy: ['.claude/skills/heartbeat/SKILL.md']
`.gitignore`                             stary: []   nowy: []
`.plik.md`                               stary: []   nowy: []
`docs/00-network-data.md`                stary: [...]  nowy: [...]   (bez zmian)
`sweep.max_deviation`                    stary: []   nowy: []        (bez zmian)
```

Wpis `yml` znika z `ROZSZERZENIA_BEZ_TRAFIEN`, bo bramka pokrycia żąda od każdego
wpisu **zera** trafień, a tych jest teraz 26. Nie trzeba było o tym pamiętać —
zażądała tego sama, i to jest w §4 pokazane.

Kontrola detektora w `test_wzorzec_sciezki_lapie_to_co_ma_i_nie_lapie_prozy` rośnie
z czterech par do sześciu. Warto zapisać, dlaczego cztery poprzednie tego nie
złapały: **wszystkie mierzyły to, co wzorzec robi po PRAWEJ stronie kropki**
(rozszerzenie, ukośnik, przedrostek wytworu). Martwe pole leżało po lewej.

## 3. Czego ta zmiana NIE rusza

`SCIEZEK_NA_RAPORT_MIN` zostaje na 6 i nie wymaga przeliczenia: to podłoga
**stosunkowa** (`seen >= checked * K`), a stosunek po zmianie rośnie, nie maleje.
Boksowanie tej podłogi liczy oba brzegi z drzewa w czasie testu, więc też nie ma tam
liczby do poprawienia.

## 4. Kontrole negatywne — wykonane

Nazwa pliku w kontroli pierwszej **powstała w czasie kontroli** (`/dev/urandom`)
i nie stoi w polu „Weryfikacja" pozycji — to pole ma wołać wyłącznie pliki istniejące.

| mutacja | skutek |
|---|---|
| do raportu dopisana **nieistniejąca** ścieżka .github/workflows/89f94f71a2b4.yml (bez grawisów w tym wierszu — powód niżej), wzorzec NOWY | `FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie: ['liczba-pozycji-w-prozie.md:141: .github/workflows/89f94f71a2b4.yml']`, 17/18 |
| **ta sama wstawka**, wzorzec przywrócony do starego | bramka rozwiązywania **MILCZY** o wstawce; padają za to dwie inne: `FAIL …ma_zywe_trafienie_albo_jawny_wyjatek: rozszerzenia ['yml'] nie mają w 181 raportach ani jednego trafienia` oraz `FAIL test_wzorzec_sciezki_lapie_to_co_ma_i_nie_lapie_prozy`, 16/18 |

`md5sum -c` po obu: `OK` dla `tools/tests/test_report_hygiene.py` i dla raportu.

**Nazwa wymyślona stoi w tej tabeli BEZ grawisów, i to nie jest formatowanie.** Pierwsza
wersja tego raportu cytowała ją w grawisach — i bramka z tej właśnie pozycji zapaliła się
na własnym raporcie:

```
FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie:
  ścieżki, których nie ma w drzewie: ['martwe-pole-wzorca-sciezek.md:83: .github/workflows/89f94f71a2b4.yml']
  (w oryginale komunikatu nazwa stoi w grawisach — tutaj są zdjęte z tego samego powodu, co wyżej)
```

Jest to trzecia, niezaplanowana kontrola negatywna i najmocniejsza z trzech: **rozszerzony
wzorzec złapał ścieżkę pod `.github/` w raporcie napisanym po zmianie**, czyli dokładnie
to, czego stary wzorzec nie umiał. Wyjątku w `PATH_EXCEPTIONS` nie dopisano — lista jest
dla plików, które kiedyś istniały, a nie dla nazw wymyślonych na potrzeby kontroli.

Druga kontrola jest właściwym pomiarem tej pozycji i mówi dwie rzeczy naraz.
Po pierwsze: **stary wzorzec nie widzi wstawionego kłamstwa** — dokładnie ta klasa
odsyłacza, dla której bramka istnieje. Po drugie: zdjęcie wpisu `yml` z listy
wyjątków nie było czynnością do zapamiętania — **bramka pokrycia sama jej zażądała**
w chwili, gdy wzorzec wrócił do starej postaci, a zachowanie kontroli detektora
złapało zmianę drugi raz, niezależnie.

## 5. Weryfikacja

```
  18/18 przeszło       test_report_hygiene.py
  RAZEM 2082 testów, 111 modułów, kod 0
```

Liczba testów się nie zmienia: obie nowe pary są asercjami w istniejącym teście, a nie
nowymi testami. Zestaw przed pozycją: 2082 testów, 111 modułów.

## 6. Czego świadomie nie zrobiono

**Nie rozszerzono wzorca na katalogi bez rozszerzenia** — pole „Poza zakresem"
pozycji, i słusznie: `docs/24` czy `tools/ci` nie są plikami, a bramka sprawdza
istnienie pliku.

**Nie dopisano żadnej ścieżki do żadnego raportu.** Przyrost 26 trafień pochodzi
wyłącznie z tego, że wzorzec zaczął widzieć to, co w raportach stało od dawna.

**Nie tknięto `SCIEZEK_NA_RAPORT_MIN` ani `MIN_REPORTS`** — §3 i pole „Poza zakresem".
