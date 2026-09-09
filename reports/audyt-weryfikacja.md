# Weryfikacja audytu zewnętrznego: osiem findingów sprawdzonych, dwa pomiary, których audyt nie wykonał

**Zmierzone 09.09.2026 na:** `fcaaca0` i `f425908`, kontener tej sesji.
**Przyrząd:** sonda w `tools/tests/`, `tools/track/validate.py`,
`tools/tests/test_all.py`, `git` w lokalnym repozytorium bare,
`.github/workflows/prune-merged-branches.yml`, `src/Sim/Line/LineCore.cs`,
`data/network/lines.json`.

---

## 1. Skąd ten raport

Właściciel zlecił audyt wielodyscyplinarny drugiemu modelowi i rozstrzygnął, co
zrobić z wynikami: **każdy finding zweryfikować samemu**, a do kolejki wpisać
wyłącznie potwierdzone pomiarem, wymieniając odrzucone z powodem. Audyt zgłosił
24 findingi na `cbaa67e` i sam napisał, że kodu nie uruchamiał.

Ten raport zamyka pierwszą rundę: osiem findingów sprawdzonych, z tego **dwa
pomiarami, których audyt nie wykonał**, jeden potwierdzony i **naprawiony od razu**
(bo mieścił się w gałęzi już otwartej), jeden **przeważony w dół**, i jeden
**rozszerzony** o rzecz, której audyt nie zgłosił.

## 2. Potwierdzone pomiarem

### 2.1. Zestaw testów wychodzi kodem zero, nie wykonawszy niczego

Sonda: moduł w `tools/tests/` z `sys.exit(0)` w ciele i jednym celowo padającym
testem.

```
kod wyjścia całego zestawu: 0
bajtów wyjścia zestawu: 0
ile FAIL: 0
```

Zero wierszy wyjścia, zero dopasowań na grepie, kod sukcesu. Asymetria stoi
w dwóch wierszach jednego pliku: wykonanie testu łapie `except SystemExit`
i zamienia je na FAIL testu, a pętla importu łapie `except Exception` —
a `SystemExit` dziedziczy z `BaseException`.

To najgroźniejszy wynik całej rundy, bo **unieważnia każdy raportowany „kod 0"**:
milczenie zestawu jest nieodróżnialne od jego sukcesu. Dziś żaden moduł tak nie
robi, więc dzisiejsze pomiary są prawdziwe — ale przestałyby być bez ani jednego
sygnału. Pozycja 6.D65.

### 2.2. Walidator osi ogłasza zgodność, gdy różnica jest nieliczbowa

`NaN` podstawiony w pierwszą współrzędną kopii pliku osi:

```
·   punktów: 447, długość osi: nan m
·   length_m zgodne z łamaną, różnica nan mm
  0 błędów, 1 ostrzeżeń
kod=0
```

Audyt zgłosił „brak odrzucania wartości nieskończonych". Pomiar pokazuje coś
mocniejszego: wiersz `length_m zgodne z łamaną` jest **twierdzeniem o zgodności**,
wypisanym w chwili, w której różnica nie jest liczbą. Porównania z wartością
nieliczbową są zawsze fałszywe, więc próg dryfu nie może zapalić się nigdy.
Pozycja 6.D66.

### 2.3. Kasowanie gałęzi bez warunku na czubek

Plan zapisuje `$branch $sha`, a krok kasujący czyta `$sha` **wyłącznie do
komunikatu w logu**. Próba w lokalnym repozytorium bare, nie na `origin`:

```
plan zapisał 5ad473f3, zdalne jest 35023c81
kod wyjścia push z lease: 1
  git: rejected]  (delete) -> audit-branch (stale info)
zdalne po próbie: 35023c81
kod wyjścia dzisiejszej formy: 0
  ref skasowany razem z 35023c81
```

Audyt swojej próby nie wykonał i napisał to wprost. Wykonana potwierdza jedno
i drugie: proponowana poprawka odmawia, a dzisiejsza forma kasuje ref z commitem,
którego plan nie widział.

**Kontekst, którego audyt nie podał:** ten workflow chodzi wyłącznie ręcznie, więc
okno wyścigu wymaga pushu w trakcie ręcznego przebiegu. Skutku to nie zmienia,
prawdopodobieństwa — tak. Pozycja 6.D67.

### 2.4. Godot bez sumy kontrolnej, Blender z sumą

Ten sam runner, ten sam model zagrożenia, dwa standardy w jednym repozytorium:
Godot idzie pobraniem, rozpakowaniem i uruchomieniem bez ani jednego `sha256`,
a `tools/ci/blender_install.sh` woła `sha256sum -c` na sumie z pliku pinu.
Nierówność standardu jest tu całą treścią. Pozycja 6.D68.

### 2.5. Opcja przyjmowana i niewpływająca na werdykt

`expect_package` występuje w `tools/track/validate.py` **wyłącznie w sygnaturze**
funkcji; ciało używa `expect_line` w kilku miejscach i `expect_package` w żadnym.
Szósty przypadek wzorca „nazwa istnieje, zachowania nie ma". Pozycja 6.D69.

### 2.6. `Finished` przeczy własnej dokumentacji nawrotu

`src/Sim/Line/LineCore.cs`, wiersz 95: skład jest skończony w chwili przyjazdu.
Opis `TurnbackEnabled` mówi, że przy włączonym nawrocie pojazdy krążą i **nigdy
nie kończą**. Przy jednym składzie pętla `Run()` wychodzi w kroku przyjazdu.

To sprzeczność **zapisów**, i tak została wpisana: pozycja 6.D70 wymaga testu
wykonywanego, bo kolejność zdarzeń w kroku przyjazdu rozstrzyga o wyniku,
a czytanie jej nie rozstrzyga.

## 3. Przeważony w dół

Audyt nadał wagę wysoką kompilacji bez jawnego trybu w bramce asercji. Sprawdzone
osobno: ani `.github/workflows/`, ani `tools/ci/`, ani `doctor.sh` nie ustawiają
zmiennej wyłączającej asercje i nie wołają interpretera z wyłączonymi asercjami —
**scenariusz nie ma dziś drogi wywołania**. Rodzina jest ta sama co w §2.1, ale to
„zepsułoby się, gdyby", nie „jest zepsute". Wpisane jako 6.D71 z wagą niższą
i z powodem obniżenia zapisanym przy pozycji.

## 4. Potwierdzony i naprawiony od razu

Audyt zgłosił, że dokumenty wymagają kompletu sześciu etykiet runnera, gdy drzewo
egzekwuje jedną — i wskazał **dwa** miejsca, gdy ja znalazłem jedno. Drugim był
`README.md`; jego akapit był zwolniony z bramki tym samym mechanizmem, co §9.

Naprawione w tym samym commicie, w gałęzi, która była już otwarta na §9, razem
z kontrolą negatywną. Pomiar i wnioski: `reports/9-goly-selektor.md` §8. Wniosek
osobny od poprawki: **jedno wystąpienie wzorca nie mówi nic o liczbie wystąpień** —
zmierzyłem mechanizm na jednej sekcji i uznałem sprawę za zamkniętą, nie
policzywszy reszty.

## 5. Rozszerzony: dane sieci

Audyt zgłosił, że jedna stacja wspólnego pierścienia znika z listy jednej linii.
Potwierdzone strukturalnie i mocniej, niż opisał:

```
L2 sąsiedzi Madou: Botanique|Kruidtuin  <->  Arts-Loi|Kunst-Wet
Botanique i Arts-Loi sąsiadują w L6: True
```

Brakujący przystanek jest **wewnętrzny**: w L6 jego dwaj sąsiedzi z L2 stoją obok
siebie, a poza tą jedną dziurą sekwencja jest identyczna (18 z 19). Wzorzec obsługi
wyrzucałby odcinek, nie jeden przystanek w środku.

**Czego audyt nie zgłosił, a co wyszło przy tym pomiarze:** suma unikalnych
przystanków z czterech linii daje **60**, a `network.metro_stations`
i `docs/00-network-data.md` mówią **59**. Najprawdopodobniejsze wyjaśnienie to dwie
połowy jednego kompleksu liczone raz — ale nic w repozytorium tego nie mówi
i **żadna bramka tych dwóch liczb nie zestawia**.

Obie rzeczy dotykają `data/`, które jest tylko do odczytu, i obie są twierdzeniami
o sieci, których nie wolno zgadywać. Poszły więc do sekcji decyzji właściciela,
nie do kolejki.

## 6. Czego jeszcze nie sprawdziłem

Findingi o zgodności manifestu dźwięku ze schematem oraz czternaście pozycji
o wagach średniej i niskiej (interfejs, teksty, filtry ścieżek workflowów, wersja
SDK, materiały kontrolne renderu, cytowanie progów przyspieszenia) — nie zostały
zweryfikowane w tej rundzie. Nie są wpisane do kolejki i **nie są przez to
odrzucone**; są niesprawdzone i tak trzeba je czytać.

## 7. Weryfikacja

```
  RAZEM 2066 testów, 110 modułów, kod 0
```

Kolejka po tej rundzie: **23** pozycje do wzięcia, przy progu dwunastu.

## 8. Ocena samego audytu

Rzetelny w miejscu, w którym łatwo byłoby udawać: napisał wprost, że kodu nie
uruchamiał, że polecenia są procedurami dla właściciela, a nie zapisami prób,
i że prognozowanych wyników nie wolno cytować jako pomiarów. Podał zakres
przeczytanego (66 plików, 57 w całości) zamiast sugerować pełne przejście.

Dwa braki, oba tego samego rodzaju: tam, gdzie pomiar był tani, audyt zostawiał
podejrzenie. `NaN` i lease dały się sprawdzić w kilka minut i **oba wyszły gorzej,
niż audyt zakładał** — pierwszy dlatego, że przyrząd nie milczy, a ogłasza
zgodność; drugi dlatego, że proponowana poprawka naprawdę działa, co czyni brak
poprawki tańszym do usunięcia, niż wyglądało.
