# 6.A19 — odmowa `replay` mówiła nieprawdę o tym, czego odmawia

**Zmierzone 08.09.2026 na commicie:** `d201b16c8f507eac9a01a16955a011a887e5d109`

## 1. Objaw, zmierzony przed zmianą

```
$ dotnet run --project src/Sim.Runner -- replay --axis data/track/L1_A.json --coast-from-m 250
BŁĄD: polecenie replay nie zna opcji --coast-from-m. Zna: --atp, --axis, --exchange-s,
      --keys, --limit-kmh, --notch-rate, --out, --sample-every, --signalling, --stop-window-m
kod wyjscia: 1
```

Zdanie jest **nieprawdziwe co do sensu**: runner tę opcję zna i przyjmuje ją
w `line` oraz w `budget`. `replay` odmawia jej **z powodu**, nie z niewiedzy —
a czytający dostawał diagnozę „literówka" na zachowanie, które jest projektem.
Rozstrzygnięcie właściciela z 07.09.2026 wybrało wariant (a): odmowa zostaje na
stałe i jest udokumentowaną własnością polecenia. Ta pozycja poprawia więc
**treść komunikatu**, nie zachowanie.

## 2. Poprawka jest szersza niż jedna para, i to wyszło z pomiaru

Pierwsze czytanie sugerowało wpis dla pary (`replay`, `--coast-from-m`). To
byłaby tabela wyjątków udająca mechanizm — lekcja 6.D40. Zbiór poleceń
przyjmujących daną opcję jest **liczony z `KnownOptions`**, więc każda opcja
znana z innego polecenia dostaje prawdziwy komunikat, także bez wpisu o powodzie:

```
$ ... replay --keys build/nie-ma.keys --coast-from-m 250
BŁĄD: polecenie replay nie przyjmuje opcji --coast-from-m: odtworzenie zapisu wejść
      z --keys idzie przez TrainController i DriverNotch, więc nastawa automatu
      nadpisałaby to, co zrobił maszynista, a odtworzenie przestałoby być
      odtworzeniem. Odmowa jest udokumentowaną własnością polecenia —
      rozstrzygnięcie właściciela z 07.09.2026 na wariant (a), nie brak implementacji.
      Runner ją zna — przyjmują ją: budget, line. Opcje replay: --atp, --axis, ...
kod: 1

$ ... service-day --timetable build/nie-ma.json --trains 8
BŁĄD: polecenie service-day nie przyjmuje opcji --trains. Runner ją zna —
      przyjmują ją: budget. Opcje service-day: --at, --out, --timetable

$ ... replay --zmyslona 1
BŁĄD: polecenie replay nie zna opcji --zmyslona. Zna: --atp, --axis, ...
```

Trzeci przypadek jest tu równie ważny jak dwa pierwsze: opcja nieznana **nikomu**
zostaje przy dawnym komunikacie, bo o niej to zdanie jest prawdziwe. Fraza
„nie zna opcji" stoi w `Program.cs` nadal **dokładnie raz** — tego wymaga
bramka jednego pisarza z 6.A22.

## 3. Test, który przybijał nieprawdę jako zachowanie oczekiwane

Najciekawsze znalezisko nie jest w kodzie produkcyjnym. `dotnet test` po zmianie
wywrócił `Line_z_nieznana_opcja_konczy_sie_kodem_jeden`, który używał
`--headway-s` i żądał frazy `nie zna opcji`. Jego własny docstring wyjaśniał
wybór: `--headway-s` „NAPRAWDĘ istnieje, tyle że w `budget`", i jest to
„mocniejsza kontrola niż wymyślona nazwa".

Rozumowanie jest **słuszne** i zostaje. Ale skoro opcja naprawdę istnieje, to
żądane zdanie było o niej nieprawdziwe — test **żądał nieprawdy**. Dziś żąda
komunikatu prawdziwego; niezmienny jest **kod wyjścia 1**, i to on jest treścią
odziedziczoną po 6.D15. Nazwa mówiła „nieznana opcja" o opcji znanej, więc też
została przepisana na `Line_z_opcja_innego_polecenia_konczy_sie_kodem_jeden`.

## 4. Bramka swoistości igieł złapała moją pierwszą wersję — i miała rację

Pierwsza wersja tabeli powodów miała klucz złączony spacją: `"replay --coast-from-m"`.
Bramka 6.A33 zapaliła się natychmiast:

```
FAIL test_every_needle_matches_at_most_one_message_or_is_justified:
     '--coast-from-m' w 2 komunikatach
FAIL test_a_weakened_needle_lights_up_the_first_rung:
     szczebel 1 zapalony JUŻ przed osłabieniem: ['--coast-from-m', '--keys', 'coast', 'zapisu wejść']
```

Przyczyna nie była w igłach, tylko w **kluczu**: wielowyrazowy literał w tym pliku
bramka czyta jako **komunikat**, więc klucz udawał komunikat, którego nikt nie
wypisuje, i podnosił licznik dopasowań. Poprawką nie było więc osłabienie ani
usprawiedliwienie igły, a **usunięcie fałszywego komunikatu z rodziny**: klucz jest
dwupoziomowy (polecenie, potem opcja), czyli literały są jednowyrazowe, a takie
czytnik odrzuca z założenia. Po zmianie:

| igła | przed | po |
|---|---|---|
| `--coast-from-m` | 2 | **1** |
| `coast` | 2 | **1** |

Dwie moje igły zostały **wzmocnione**, nie usprawiedliwione: `--keys` (3 komunikaty)
i `zapisu wejść` (2) zamienione na jedną `zapisu wejść z --keys` (**1**) — bo
igła trafiająca w wypis pomocy nie przybija treści odmowy. `MAX_JUSTIFIED_NEEDLES`
zostaje na 7, lista usprawiedliwień nietknięta.

## 5. Dwie kontrole negatywne WYKONANE

**KN-1 — powód zdjęty z komunikatu.** Pole „Skończone, gdy" żądało, żeby wywracało
to **dokładnie jeden** test:

```
Failed!  - Failed: 1, Passed: 589, Total: 590
  Failed Replay_nie_zna_wybiegu_bo_odtwarza_zapis_wejsc
```

Po przywróceniu: `Passed! - Failed: 0, Passed: 590`.

**KN-2 — `--coast-from-m` dopisane do `KnownOptions[replay]`.** Opcja **nie** ma
tam wejść; bramka Pythona to łapie:

```
FAIL test_the_table_does_not_declare_options_nobody_reads:
     tabela deklaruje dla replay opcje, ktorych kod nie czyta: ['--coast-from-m']
  17/18 przeszło
```

Po przywróceniu 18/18, a plik jest **bajtowo identyczny** ze sprawdzoną kopią
(jedna suma md5 na dwóch plikach). Kontrole mutowały `.cs`, nie `.py`, więc
pułapka nieświeżego bajtkodu z 6.D41 tu nie zachodzi.

## 6. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 590, Skipped: 0, Total: 590

$ python3 tools/tests/test_all.py; echo "kod: $?"
  1996/1996 przeszło
  RAZEM 83.866 s, 1996 testów, 105 modułów
kod: 0
```

Liczba testów `dotnet test`: **589 → 590**. Jeden test dopisany
(`Odmowa_opcji_znanej_z_innego_polecenia_nie_klamie_ze_jej_nie_zna`), jeden
przepisany i przemianowany, żaden nie usunięty.

## 7. Czego świadomie NIE zrobiłem

- **Nie dopisałem `--coast-from-m` do `KnownOptions[replay]`.** Odmowa jest
  rozstrzygnięciem właściciela; zniesienie jej byłoby zmianą zachowania, nie treści.
- **Nie zmieniłem kodu wyjścia.** Zostaje 1, pokazane wykonaniem przed i po.
- **Nie dopisałem powodów dla innych par.** Powód wymaga decyzji właściciela;
  `service-day --trains` dostaje komunikat prawdziwy bez powodu i to wystarcza.
- **Nie tknąłem listy usprawiedliwień bramki igieł** ani jej zapadek.

## 8. Zauważone przy okazji, nietknięte

Trzy raporty wymieniają dawną nazwę przepisanego testu:
`reports/postac-z-rownosciem.md` §180 i `reports/powtorzona-opcja.md` §113
niosą ją we **wklejonym wyjściu** dawnych kontroli negatywnych — to zapis pomiaru
i przepisanie go byłoby falsyfikacją, więc zostaje.
`reports/nieznana-opcja-runnera.md` §72 wymienia ją natomiast w **tabeli kontroli**
jako nazwę żywą, i ta jedna wzmianka jest dziś nieaktualna. Nie ruszam jej w tym
commicie: to plik spoza zakresu tej pozycji (§4.10), a poprawka jest jednowierszowa
i należy do pozycji o spójności nazw w raportach, której w kolejce nie ma.
