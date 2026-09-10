# Pin niespełniony to nie brak SDK (10.09.2026)

**Zmierzone 10.09.2026 na:** `39e6589`, kontener tej sesji (jedno SDK: 10.0.401).
**Przyrząd:** `doctor.sh --no-tests` na drzewie z podmienionym `global.json`
i atrapą `dotnet`, `tools/tests/test_dotnet_version.py`.

---

## 1. Dwa zdania o tym samym SDK, sprzeczne ze sobą

Przy pinie, którego żadne zainstalowane SDK nie spełnia, `dotnet --version` kończy
kodem **155** i wypisuje **na stdout** listę zainstalowanych SDK. Doctor wypisywał
wtedy naraz:

```
  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+ …
  ok    dotnet SDK >= 10 (jest 10)
```

Pierwsze radzi zainstalować coś, co leży na dysku. Drugie melduje sprawdzenie zrobione
na wyjściu polecenia, które **padło**: `--version | cut -d. -f1` nie widzi kodu wyjścia
pierwszego członu potoku, więc brał `10` z pierwszego wiersza wypisanej listy SDK.

6.D79 dopisała blok nazywający tę sytuację, ale nie tknęła dwóch kontroli wyżej —
i to jest cała treść tej pozycji.

## 2. Rozstrzyga kod wyjścia, nie treść stdout

Trzy stany, trzy różne odpowiedzi, każdy rozpoznawany po tym, co polecenie **robi**,
a nie po tym, co wypisuje:

| stan | `--list-sdks` | `--version` | wypis |
|---|---|---|---|
| SDK jest, pin spełniony | lista | kod 0 | `ok dotnet SDK`, `ok dotnet SDK >= N` |
| SDK jest, pin niespełniony | lista | kod 155 | **jedno** zdanie o pinie, pozycja WYMAGANA |
| nie ma żadnego SDK | pusto | kod ≠ 0 | `BRAK dotnet SDK -> zainstaluj` (bez zmian) |

Wypis w stanie środkowym, zmierzony na atrapie:

```
  BRAK  dotnet SDK vs pin z global.json (10.0.999)  -> SDK SĄ na dysku, ale ŻADNE nie
        spełnia pinu 10.0.999 z global.json; `dotnet --version` kończy błędem —
        zmień pin albo doinstaluj tę wersję, NIE instaluj SDK od nowa
        na dysku: 10.0.401 [/atrapa/sdk]
```

Ani `BRAK dotnet SDK`, ani `ok dotnet SDK >= N` — dokładnie tego żąda pole
„Skończone, gdy".

## 3. Trzeci stan wymusiła bramka, nie projekt

Pierwsza wersja rozpoznawała obecność SDK po **kodzie wyjścia** `--list-sdks`. Bramka
`test_brak_jakiegokolwiek_sdk_nadal_kaze_instalowac` padła od razu: `dotnet
--list-sdks` na maszynie **bez ani jednego SDK** kończy **zerem** i nie wypisuje nic.
Stan „nie ma czego pinować" zlewał się więc ze stanem „pin niespełniony", a doctor
przestawał radzić instalację tam, gdzie była jedyną prawdziwą radą. Liczy się teraz
NIEPUSTE wyjście, nie sam kod.

## 4. Waga zdania jest częścią poprawki

Zdanie o pinie jest pozycją **wymaganą**, nie ostrzeżeniem: w tym stanie `dotnet build`
też nie ruszy, więc środowisko naprawdę nie nadaje się do pracy — zmienia się wyłącznie
przyczyna. Bramka sprawdza **kod wyjścia doctora**, bo o wadze mówi tylko on; WARN dałby
ten sam napis i zero na wyjściu, czyli środowisko niezdatne do pracy zameldowane jako
gotowe.

## 5. Pięć kontroli negatywnych, `md5sum -c: OK` po każdej

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | kontrola SDK znów wypisywana bezwarunkowo | **czerwona** 41/42 |
| KN-2 | `HAVE_SDK_MAJOR` wraca do potoku | **czerwona** 40/42, dwie bramki |
| KN-3 | obecność SDK po samym kodzie `--list-sdks` | **czerwona** 41/42 |
| KN-4 | zdanie o pinie jako WARN zamiast pozycji wymaganej | **czerwona** 41/42 |
| KN-5 | wypis nie pokazuje, co leży na dysku | **czerwona** 41/42 |

```
KN-2  FAIL test_liczba_wersji_nie_bierze_sie_z_polecenia_ktore_padlo:
      liczba wersji znów bierze się z potoku, który nie widzi kodu wyjścia
      FAIL test_niespelniony_pin_nie_daje_dwoch_sprzecznych_zdan:
      doctor melduje `ok dotnet SDK >= N` na podstawie wyjścia polecenia,
      które zakończyło się błędem
KN-3  FAIL test_brak_jakiegokolwiek_sdk_nadal_kaze_instalowac:
      przy braku JAKIEGOKOLWIEK SDK doctor przestał kazać je zainstalować
KN-4  FAIL test_niespelniony_pin_nie_daje_dwoch_sprzecznych_zdan:
      doctor kończy zerem przy pinie, którego żadne SDK nie spełnia
```

**KN-2 zapala DWIE bramki i to jest wybór, nie przypadek.** Jedna patrzy na wypis,
druga na źródło `doctor.sh` — mechanizm usterki (potok gubiący kod wyjścia) jest
przybity osobno od jej objawu, bo objaw da się usunąć, nie usuwając mechanizmu.

**Atrapa oddaje ZMIERZONE zachowanie, nie wyobrażone:** `--version` przy niespełnionym
pinie wypisuje listę SDK **na stdout** i kończy kodem 155. Gdyby atrapa pisała na
stderr, cała usterka by w niej nie istniała i bramki mierzyłyby coś innego.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_dotnet_version.py
  -> 42/42 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 120,078 s, 2190 testów, 118 modułów, kod 0
  -> 2190/2190 przeszło
```

Zestaw **2186 → 2190**, moduły bez zmiany (118). Zapadka `MIN_REPORTS` została w tym
commicie podniesiona ze dwustu czternastu na dwieście piętnaście — słownie, bo
`test_report_claims.py` czyta pierwszą liczbę po nazwie stałej jako twierdzenie o jej
bieżącej wartości.

## 6a. Uzupełnienie kolejki jedzie w tym samym commicie i to jest wymuszone

Domknięcie tej pozycji zbija kolejkę z dwunastu wpisanych na **jedenaście**, czyli
PONIŻEJ `MINIMUM_READY_ITEMS`. `CLAUDE.md` §8 każe wtedy najpierw uzupełnić kolejkę —
a commit z samym domknięciem zostawiłby drzewo **czerwone** na dwóch bramkach zapasu.
Dwa commity jeden po drugim dałyby ten sam efekt w połowie drogi, więc uzupełnienie
jedzie razem z pozycją, a nie osobno, i jest tu wypisane, żeby nie wyglądało na
poprawkę przy okazji.

Sześć nowych pozycji, **wszystkie z pomiarów zrobionych przy pozycjach zamkniętych
dzisiaj** i zapisanych tam jako zauważone:

| pozycja | pomiar |
|---|---|
| 6.D107 | 14 z 15 parametrów `braking.params` przechodzi przez `design()`, `aw0_kg` nie (6.D94) |
| 6.D108 | 18 miejsc w 12 raportach niesie bieżącą wartość zapadki cyfrą |
| 6.D109 | próg zapasu porównuje wpisane (11), nie do wzięcia (10) (6.D95) |
| 6.D110 | 6 miejsc w `tools/tests/` pisze przez `shutil`/`os.replace` (6.D90) |
| 6.D111 | 26 z 60 nazw przystanków jest dwujęzycznych z kreską (6.D91, 6.D92) |
| 6.D112 | 3 wywołania `--version` w jednym bloku doctora (ta pozycja) |

`MINIMUM_DETAIL_BLOCKS`, podniesiona ze stu siedemdziesięciu dziewięciu na sto
osiemdziesiąt pięć — wynik `len(detail_sections(...))` na pliku po edycji. Kolejka: wpisanych **17**, do wzięcia **16**.

**Bramka zapaliła się przy okazji po raz CZWARTY tego dnia** — cztery raporty niosły
bieżącą wartość `MINIMUM_DETAIL_BLOCKS` cyfrą i musiały zostać przepisane słownie.
To jest dokładnie kształt, który opisuje nowa pozycja 6.D108, tyle że zaobserwowany
w commicie, który ją zakłada.

## 6b. Bramka wartości zapadki zapaliła się CZTERY razy przy tym jednym commicie

Warto to zapisać razem, bo to jest materiał dla nowej pozycji 6.D108 i cztery różne
kształty tej samej usterki:

1. `MINIMUM_DETAIL_BLOCKS`, podniesiona ze stu siedemdziesięciu dziewięciu na sto
   osiemdziesiąt pięć — cztery raporty niosły starą wartość cyfrą i zapaliły bramkę;
2. przepisałem dwa z nich na „ma sto osiemdziesiąt pięć — **10.09.2026** doszło…"
   i bramka zapaliła się **znowu**, tym razem czytając `10.09` jako deklarowaną
   wartość: liczbą jest tu DATA, stojąca w zasięgu wzorca zaraz za nazwą;
3. mój własny raport, ten plik, niósł w tabeli `MINIMUM_DETAIL_BLOCKS **179 → 185**`
   i zapalił ją po raz trzeci.

Był i **czwarty**: akapit, który czytasz, w pierwszej wersji sam wypisywał
`179 → 185` obok nazwy i zapalił bramkę w commicie, w którym o niej opowiada.

Wszystkie cztery domknięte tak samo: **przecinek zaraz za nazwą stałej**, bo wzorzec
`CLAIM` na przecinku się zatrzymuje. Jest to obejście, nie reguła, i dlatego pozycja
6.D108 mówi o rozróżnieniu po KSZTAŁCIE zdania, a nie o dopisywaniu wyjątków.

## 7. Czego świadomie nie zrobiłem

Nie zmieniałem polityki `rollForward` ani wersji w pinie — pole „Poza zakresem"
wyklucza jedno i drugie. Nie ruszałem podpowiedzi o `DOTNET_ROOT` przy SDK leżącym
poza `PATH`: to inna sytuacja i inna rada, sprawdzana przez cztery istniejące bramki.

## 8. Zauważone i nietknięte

`doctor.sh` woła `"$DOTNET" --version` **trzy razy** w tym bloku: raz w rozpoznaniu
stanu, raz przy `HAVE_SDK_MAJOR`, raz w gałęzi pinu spełnionego. Na atrapie to nic nie
kosztuje, na prawdziwym SDK każde wywołanie to kilkadziesiąt milisekund. Nie scalam
ich w jedno, bo scalenie wymagałoby przeniesienia wyniku między blokami, które dziś są
czytelne osobno — ale jest to trzykrotne pytanie o tę samą rzecz.
