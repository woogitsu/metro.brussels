# Kolejka zeszła do progu w dniu, w którym pięć zadań było w robocie

**Zmierzone 06.09.2026 na commicie:** `51d324a`

## 1. Co się stało

Kolejka fazy 6 miała 06.09.2026, po scaleniu #279, dokładnie **12 pozycji do wzięcia** —
czyli równo tyle, ile wynosi próg `MINIMUM_READY_ITEMS` = 12. Bramka
`test_the_queue_holds_at_least_a_day_of_work` świeciła na zielono i formalnie miała rację.

W tym samym momencie **pięć zadań było w robocie** (6.A5, 6.A7, 6.B13, 6.B14, 6.D1).
Każde z nich, po scaleniu, dostaje w swoim wierszu adnotację `ZROBIONE`, a `open_items`
takie wiersze odsiewa. Kolejka zeszłaby więc do **siedmiu** pozycji, a bramka zapaliłaby
się **po fakcie** — na czerwonym zestawie, w cudzym pull requeście, przy zadaniu, które
z tym nie ma nic wspólnego.

`CLAUDE.md` §8 mówi o tym wprost:

> Gdy kolejka zejdzie poniżej dwunastu pozycji, **pierwszym zadaniem jest jej
> uzupełnienie**, nie zatrzymanie się.

## 2. Licznik w planie mówił nieprawdę, i to nie przez niedopatrzenie

Akapit `docs/TASKS.md` deklarował „**11 udokumentowanych** przy progu 12". Zmierzone
tego dnia na `51d324a`, przed tym commitem:

```
$ python3 -c "import sys; sys.path.insert(0,'tools/tests'); import test_backlog as B; \
    t=B._tasks(); print(len(B.open_items(t)), len(B.documented_items(t)), len(B.detail_sections(t)))"
12 8 19
```

Udokumentowanych było **osiem**, nie jedenaście. Różnicy nie zrobiła żadna zmiana
w planie — zrobiło ją **scalenie pięciu zadań tego samego dnia** (#275, #276, #277,
#278, #279).

To jest sedno, a nie szczegół: **licznik zapasu opada wtedy, gdy praca idzie dobrze.**
Liczba wpisana do planu ręcznie nie ma jak za tym nadążyć i starzeje się w tempie
scaleń, nie w tempie edycji. Rozjazd o trzy pozycje narósł w ciągu jednego dnia,
bez ani jednej zmiany w akapicie, który go niósł.

Ten sam mechanizm złapał już raz `MINIMUM_DOCUMENTED_ITEMS`: sprzężenie, które #274
rozplątywało, polegało dokładnie na tym, że **wykonanie pracy zapalało bramkę**.

## 3. Co dopisano

| co | ile | numery |
|---|---|---|
| bloki dla pozycji, które stały w tabeli bez opisu | 2 | 5.6, 6.B5 |
| bloki dla pozycji dopisanych 06.09.2026 bez bloków | 2 | 6.B13, 6.B14 |
| pozycje nowe, każda z blokiem sześciu pól | 6 | 6.A9, 6.B15, 6.B16, 6.D9, 6.D10, 6.D11 |

Sześć nowych pozycji nie jest wymyślone przy biurku — każda ma w polu **Skąd** pomiar
zrobiony w tym drzewie:

| pozycja | pomiar, z którego wyrosła |
|---|---|
| 6.A9 | `src/Sim.Runner/Program.cs` rozdziela osiem poleceń; nazwę polecenia wymienia jakikolwiek plik w `tests/Sim.Tests/` **tylko dla `axis`** — pozostałych siedmiu nie wymienia ani jeden |
| 6.B15 | modułów `test_*.py` w `tools/tests/` jest **73**, wyrażenie „kontrola negatywna" stoi w **33** |
| 6.B16 | `reports/mutation-drift.md` podaje dla `tools/track/detail_layout.py` **8** ocalałych mutacji z 9 — najgorszy stosunek w tabeli |
| 6.D9 | `idat_sha256` leży w `tools/ci/png_pixels_sha256.py` z czterema testami; jedyne odwołanie do niego w całym drzewie pochodzi z jego własnego testu |
| 6.D10 | raportów z SHA w nagłówku jest **48**; commit z nagłówka nigdy nie dotknął pliku raportu w **25** z nich, a sam `51fd842` stoi w siedmiu |
| 6.D11 | `python3 tools/tests/test_all.py` zbiera **1638** testów i chodzi **62,8 s**; nikt tego nie pilnuje |

### 3a. Pozycja 6.D10 jest tu warta osobnego zdania

Liczba „25 z 48" wygląda na listę błędów i **nią nie jest** — i właśnie dlatego jest
pozycją kolejki, a nie poprawką. Naturalna kolejność pracy w tym repozytorium to
**zmierzyć na HEAD, a raport dopisać commitem następnym**; przy niej „SHA z nagłówka
dotyka pliku raportu" jest relacją *niewłaściwą*, a nie niespełnioną.

Dopisanie bramki na tę relację przybiłoby więc konwencję odwrotną do tej, którą projekt
faktycznie stosuje. Dlatego 6.D10 jest **pomiarem relacji**, a jej pole „Skończone, gdy"
dopuszcza wprost wynik „żadnej relacji nie wolno przybić bramką". To także prostuje
zdanie, które padło w tej sesji przy okazji `reports/M7-shell.md` — że nagłówek cytuje
commit, który tego raportu nie dotyka. Cytuje, tak jak dwadzieścia cztery inne, i sam
ten fakt niczego jeszcze nie dowodzi.

## 4. Stan po uzupełnieniu

```
$ python3 -c "import sys; sys.path.insert(0,'tools/tests'); import test_backlog as B; \
    t=B._tasks(); print(len(B.open_items(t)), len(B.documented_items(t)), len(B.detail_sections(t)))"
18 18 29
```

**18 pozycji do wzięcia, wszystkie 18 udokumentowane, 29 bloków** z kompletem sześciu pól.

Zapas jest policzony **na stan po**, nie na stan przed: po scaleniu pięciu zadań
w robocie zostanie **13 do wzięcia i 13 udokumentowanych**, nadal nad progiem 12.
Liczenie zapasu na stan przed jest dokładnie tym błędem, który postawił kolejkę
na progu w chwili, gdy pięć zadań było w robocie.

Zapadka `MINIMUM_DETAIL_BLOCKS` = 32. Ten commit podniósł ją z 19 na 29; na 32 poszła jeszcze tego samego dnia, przy **drugim** uzupełnieniu — bo domknięcie 6.A3 i 6.D9 zbiło zapas do 11, czyli poniżej progu, i bramka to zapaliła. Liczba jest tu przepisana, a nie dopisana obok, i to jest ta sama mechanika, którą opisuje §2: **licznik opada od wykonywania pracy**, więc wartość zacytowana w raporcie starzeje się w tempie scaleń, nie edycji. Pilnuje tego `test_every_constant_quoted_in_a_report_carries_the_value_from_the_code` i to on wywrócił tę linijkę. Podłoga `MINIMUM_DOCUMENTED_ITEMS`
zostaje na 6 i **to jest decyzja, nie zaniedbanie**: zrównanie jej z zapasem odtworzyłoby
sprzężenie, które #274 rozplątywało.

## 5. Kontrole negatywne — wykonane

### 5.1 Skasowany blok zapala zapadkę

```
$ # blok 6.D11 usunięty z docs/TASKS.md
$ python3 tools/tests/test_all.py 2>&1 | grep -E "^\s*FAIL"
  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 28 przy zapadce 29 — któryś zniknął albo stracił jedno z sześciu pól
```

### 5.2 Znacznik niedoboru przy zapasie nad progiem zapala bramkę

Bramka `test_the_documented_shortfall_is_written_down_while_it_lasts` ma **dwie**
gałęzie i obie trzeba było sprawdzić osobno. Ta pilnuje, żeby plan nie opisywał luki,
której już nie ma:

```
$ # nagłówek niedoboru wstawiony z powrotem, przy zapasie 18
$ python3 tools/tests/test_all.py 2>&1 | grep -E "^\s*FAIL"
  FAIL test_the_documented_shortfall_is_written_down_while_it_lasts: zapas doszedł do progu, a plan nadal opisuje lukę
```

### 5.3 Zapas pod progiem zapala obie bramki

Symulacja stanu, do którego kolejka by doszła: siedem pozycji oznaczonych jako
domknięte, zapas spada do 11.

```
$ python3 tools/tests/test_all.py 2>&1 | grep -E "^\s*FAIL"
  FAIL test_the_documented_shortfall_is_written_down_while_it_lasts: zapas udokumentowany to 11 przy progu 12, a plan o tym milczy
  FAIL test_the_queue_holds_at_least_a_day_of_work: kolejka ma 11 pozycji przy progu 12; pierwszym zadaniem jest uzupełnienie fazy 6, nie zatrzymanie się
```

To jest dokładnie ten komunikat, który zobaczyłby autor **niezwiązanego** pull requesta,
gdyby ten commit nie powstał.

## 6. Poprawione przy okazji, bo dotyczyło tego samego licznika

- **6.B13 i 6.B14 stały w tabeli pasma D**, a są pozycjami pasma B (`tools/`).
  Przeniesione do właściwej tabeli.
- Komentarz w `tools/tests/test_backlog.py` twierdził, że **6.B5 czeka na decyzję
  o pakietach C, D, F**. Nie czeka: promień łuku i skrajnia liczą się **z osi**, a osie
  wszystkich sześciu pakietów leżą w `data/track/` od #86. Na tamtą decyzję czeka
  **6.B3** (LOD tuneli) — blokada została przypisana sąsiedniemu wierszowi. Zdanie
  przepisane, a nie dopisane obok, w tym samym commicie.
- Nagłówek sekcji szczegółów mówił o dwunastu blokach przy dziewiętnastu istniejących.
  Przepisany tak, żeby liczba nie stała w nim jako trwałe twierdzenie — pilnuje jej
  zapadka, nie akapit.

## 7. Czego ten commit nie robi

- **Nie wykonuje żadnej z dopisanych pozycji.** To jest uzupełnienie kolejki, nie praca
  nad zadaniami.
- **Nie podnosi podłogi zapasu** — powód w §4.
- **Nie dopisuje bramki na relację z 6.D10.** Pomiar mówi, że relacja, którą łatwo byłoby
  przybić, jest niewłaściwa; przybicie jej byłoby utrwaleniem błędu, a nie bramką.
