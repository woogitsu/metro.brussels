# 6.D157 — powtarza się dokładnie jeden moduł i pada TRZY razy, a bramka istnienia nie mogła złapać ani jednego z sześciu

**12.09.2026**, na `4d26094`. Wejście: `tools/tests/test_field_paths.py`
(`poprawki_zapisow`, `PATH_TOKEN`), `docs/TASKS.md` (adnotacje `**Poprawione …:**`),
`reports/6d146-adresy-blokow-wykonanych.md` §3.

Pozycja żądała: **listy modułów, które w historii poprawek padły więcej niż raz jako
zły adres, z liczbą przy każdym**, i odpowiedzi, czy jeden powtarzający się moduł to
**reguła, czy zbieg okoliczności**. Pole „Skończone, gdy" mówiło: *liczba wyprowadzona
z adnotacji w drzewie, a nie wpisana.*

## 1. Rozdzielenie, bez którego licznik liczy nie to

Każda adnotacja poprawki ma jeden kształt: *„pole wskazywało/wołało `X`"*, gdzie `X`
jest adresem **BŁĘDNYM** — a reszta zdania nazywa ten **właściwy**. Licznik biorący
z powodu wszystkie moduły policzyłby oba naraz, i tak właśnie wyszło przy pierwszym
podejściu: `scan_gates.py` 3, `test_tree_walks.py` 2 — moduły, które w tych zdaniach
są ROZWIĄZANIEM, nie pomyłką.

**KN-2 mierzy dokładnie ten błąd**: wzorzec biorący każdy moduł z powodu zapala bramkę
kontroli przyrządu na pięciu z sześciu adnotacji.

## 2. GŁÓWNY WYNIK: jeden moduł, TRZY razy — a nie dwa

```
6.D73    10.09.2026   -> tools/tests/test_backlog.py
6.D74    10.09.2026   -> tools/tests/test_scan_gates.py
6.D74    11.09.2026   -> test_scan_gates.py
6.D86    10.09.2026   -> test_physics_reference.py
6.D89    10.09.2026   -> test_glossary.py
6.D133   11.09.2026   -> test_scan_gates.py
```

| zły adres | ile razy |
|---|---|
| **`test_scan_gates.py`** | **3** |
| `test_backlog.py` | 1 |
| `test_physics_reference.py` | 1 |
| `test_glossary.py` | 1 |

**Wpis pozycji mówił o dwóch blokach (6.D74 i 6.D133). Poprawek jest trzy**, bo
**blok 6.D74 był poprawiany DWUKROTNIE** — 10.09 i 11.09 — i obie poprawki nazywają
ten sam zły adres. Trzy na sześć to **połowa wszystkich poprawek w drzewie**.

Odpowiedź na pytanie z pola „Wyjście": **powtarza się dokładnie jeden moduł**,
a pozostałe trzy padły po razie.

## 3. ODPOWIEDŹ NA „reguła czy zbieg okoliczności": ani jedno — bramka nie mogła ich złapać

To jest wynik, po który warto było tę pozycję brać. **Żaden z sześciu złych adresów
nie mógł zostać złapany przez bramkę istnienia, i to z DWÓCH różnych powodów:**

| dlaczego nie złapany | ile | mechanizm |
|---|---|---|
| stoi **bez katalogu** | **4** | `PATH_TOKEN` żąda ukośnika, więc bramka w ogóle na nie nie patrzy |
| ma ukośnik, ale plik **ISTNIEJE** | **2** | bramka patrzy i przepuszcza — sprawdza ISTNIENIE, nie PRZEDMIOT |

Czyli: adresów, na które bramka w ogóle spojrzała, były **dwa z sześciu** — i **oba
przepuściła**, bo wskazany plik naprawdę leży w drzewie. Tyle że leży i mierzy co
innego.

**Stąd wniosek, który jest mocniejszy niż „ten moduł jest mylący":** adres, który
przechodzi za każdym razem, można wpisać za każdym razem. Powtórzenie nie wymaga
osobnego wyjaśnienia — wymagałby go raczej jego BRAK. Dwa wymyślone adresy
(`test_physics_reference.py`, `test_glossary.py`) w drzewie nie istnieją i nie
powtórzyły się ani razu; cztery istniejące dają wszystkie powtórzenia, jakie są.

**Czego to NIE dowodzi:** że `test_scan_gates.py` jest bardziej mylący niż
`test_backlog.py`. Oba są w tej samej klasie „istnieje, więc przechodzi", a jeden
padł trzy razy i drugi raz. **Sześć punktów danych nie rozdziela „podatny" od
„trafiło się"** i mówię to wprost, zamiast dorabiać regułę do czterech liczb.

## 4. Bramki — trzy, każda na inne pytanie

| test | co pilnuje |
|---|---|
| `test_kazda_poprawka_nazywa_DOKLADNIE_jeden_zly_adres` | **kontrola przyrządu**: skan widzi każdą z sześciu adnotacji |
| `test_ktory_modul_padl_jako_zly_adres_wiecej_niz_raz` | rozkład 3/1/1/1 i to, że powtarza się dokładnie jeden |
| `test_bramka_istnienia_nie_mogla_zlapac_ani_jednej_z_tych_szesciu` | podział 4 bez katalogu / 2 istniejące — §3 |

Pierwsza istnieje, bo **mniejszy licznik wygląda dokładnie tak samo jak mniejsza
liczba pomyłek**. Gdyby wzorzec chybił adnotacji, rozkład byłby cichszy i nikt by się
nie dowiedział.

## 5. Kontrole negatywne — cztery, wszystkie czerwone

Baza: **28/28** w module. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | wzorzec łapie tylko „wskazywało", gubi „wołało" (4 z 6) | **25/28** — 3 czerwone |
| KN-2 | licznik bierze KAŻDY moduł z powodu, nie tylko zły adres | **27/28** |
| KN-3 | `_istnieje_w_drzewie` zawsze prawdziwe | **27/28** |
| KN-4 | `PATH_TOKEN` nie żąda ukośnika | **27/28** |

KN-3 i KN-4 zapalają **tę samą** bramkę z dwóch przeciwnych stron — raz psując „które
istnieją", raz „na które bramka patrzy" — i to jest dowód, że obie połowy zdania z §3
są w niej naprawdę sprawdzane, a nie że jedna niesie drugą.

### 5.1. Pierwsze podejście do KN-1 i KN-2 NIE WESZŁO — trzeci raz w tej sesji

Oba podstawienia chybiły (`AssertionError: 0`), bo w skrypcie stały escape'y
`ł`, a w pliku leżą prawdziwe bajty `ł`. Przebiegi pokazały **28/28** — czyli
**zieleń pliku nietkniętego**, wyglądającą identycznie jak „kontrola nic nie wykryła".

Złapał to `diff` z kopią roboczą robiony **po** podstawieniu, a **przed** przebiegiem,
i twarde `assert s.count(old) == 1` w samym podstawieniu. Jest to **trzeci raz w tej
sesji**, kiedy zielona kontrola znaczyła coś innego, niż wyglądała (6.D182 KN-5,
6.D183 KN-3, teraz), i **za każdym razem rozstrzygnął ten sam odruch**: sprawdzić, że
podstawienie weszło, zanim uwierzy się przebiegowi.

## 5.2. Bramka projektu złapała moją funkcję pomocniczą

`_istnieje_w_drzewie` w pierwszej wersji wołało `os.walk` wprost i zapaliło
`test_no_tool_walks_the_tree_without_the_shared_filter` — bramkę, którą to
repozytorium stawia od 6.D74, poszerza od 6.D97 i domyka od 6.D117. Własne przejście
po drzewie omija wspólny filtr `.gitignore`, więc widzi gałęzie, których reszta
narzędzi nie widzi.

Zapisane, bo to **czwarty kształt tej samej rzeczy w jednej sesji**: bramka zobaczyła
to, czego ja nie zobaczyłem, czytając własny diff. Poprawione na `tree_walk.znajdz`.

## 6. Czego świadomie nie zrobiłem

- **Nie przemianowałem żadnego modułu i nie poprawiłem żadnego adresu** — pole
  „Poza zakresem" zabrania obu.
- **Nie rozszerzyłem `PATH_TOKEN` o nazwy bez katalogu**, choć §3 pokazuje, że to
  właśnie one wypadają z zasięgu bramki w czterech z sześciu przypadków. Byłaby to
  zmiana bramki przy okazji pozycji, która miała POLICZYĆ — a skutków takiego
  poszerzenia (ile gołych nazw plików stoi w `docs/` i ile z nich to fałszywe
  trafienia) ta pozycja nie mierzyła. Zostawiam nazwane, nie zrobione.
- **Nie dorobiłem reguły odróżniającej moduł „podatny" od „trafiło się"** — §3 mówi,
  dlaczego sześć punktów na to nie wystarcza.
