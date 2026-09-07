# Odmowa mówiła, że runner nie zna opcji, którą zna (6.A22)

**Zmierzone 07.09.2026 na commicie:** `07be80b7c7ed188e8fe2f812eff34cba9600639d`
(gałąź `claude/6a22-postac-z-rownosciem`).

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na `a6e280d`
(scalenia #349 — 6.B19, trzy testy narzędzi — i #350 — uzupełnienie kolejki). Oba
zestawy przebiegły na nowej podstawie ponownie i dały **ten sam werdykt**: narzędzia
**1841 → 1844** (ta sama delta trzech testów), kod wyjścia 0; C# **570/570**
niezmienione, bo tamte dwie pozycje nie dotykają `src/`. Liczby z dnia pomiaru
(1838 → 1841) nie są przeliczane.

## 1. Zdanie sprzeczne z tabelą

```
--zmyslona 7        kod=1  BŁĄD: polecenie line nie zna opcji --zmyslona. Zna: --axis, …
--limit-kmh=72      kod=1  BŁĄD: polecenie line nie zna opcji --limit-kmh=72. Zna: --axis, …
```

Pierwsze zdanie jest prawdziwe. Drugie **jest sprzeczne z faktem**: `--limit-kmh` stoi
w tabeli `KnownOptions` polecenia `line` — i stoi na liście, którą ten sam komunikat
zaraz wypisuje. Runner nie zna **postaci** `--opcja=wartość`; to inna wiadomość.

Nie jest to kosmetyka i wpis pozycji nazwał to dokładnie: odmowa z 6.A11 istnieje po
to, żeby literówka nie przechodziła w milczeniu, a jej wartość leży w tym, że czytający
jej **wierzy**. Komunikat, który raz na jakiś czas mówi nieprawdę o zawartości tabeli,
uczy czytać go z zastrzeżeniem — i wtedy przestaje działać także tam, gdzie miał rację.

## 2. Którą drogą — rozstrzygnięte pomiarem, nie z góry

Pole „Wyjście" dawało dwie drogi i **warunek wyboru**: obsłużyć postać
`--opcja=wartość`, albo ją odrzucić z komunikatem nazywającym postać, przy czym pomiar
ma powiedzieć, ile miejsc w repozytorium używa postaci z równością — bo jeżeli zero, to
druga droga wystarcza.

Policzone przez **sklejenie kontynuacji wierszy** (`\`) i klasyfikację każdego
wystąpienia po tym, jaki program dana komenda woła:

```
wystapien postaci `--opcja=` razem:   344
   inne / proza                       246
   komendy SCENY Godota                96
   komendy Sim.Runner                   2   <- oba to tekst TEJ pozycji w docs/TASKS.md

wystapien `--limit-kmh=` razem:        70
   inne / proza                        58
   komendy SCENY Godota                11
   komendy Sim.Runner                   1   <- pole „Weryfikacja" TEJ pozycji
```

**Ani jedna prawdziwa komenda `Sim.Runner` w repozytorium nie używa postaci
z równością.** Druga droga wystarcza, i to jest wniosek z pomiaru, nie z wygody: jest
mniejsza i nie zmienia niczego, co dziś działa.

**Sprostowanie liczby, którą sam wpisałem godzinę wcześniej.** Pierwsza wersja
komentarza w kodzie mówiła „wszystkie **40** wystąpień `--limit-kmh=` należy do sceny".
Czterdzieści było liczbą **wierszy** z `grep -c`, nie wystąpień, i nie było
sklasyfikowane — a klasyfikacja pokazuje 70 wystąpień, z czego do sceny należy 11,
bo większość to proza i testy rozbioru argumentów sceny. Wniosek („zero komend
`Sim.Runner`") się nie zmienił; liczba, którą go uzasadniałem, była zła. Poprawiona
w tym samym commicie, razem ze zdaniem mówiącym, skąd wzięła się poprzednia.

## 3. Dwie połowy projektu mają dwie konwencje, i to jest sedno

`--limit-kmh=70` nie jest w tym repozytorium literówką. Tak się woła **scenę Godota**:

```
$GODOT_BIN --headless --path src/Game -- --line --limit-kmh=70 \
    --calls="$PWD/build/t400/linia/scene-calls.csv"
```

`RunPlan` sceny postaci z równością **wymaga** — jej własne testy (`RunPlanTests.cs`,
17 wystąpień) sprawdzają dokładnie taki rozbiór. Czytający przychodzi więc do runnera
z drugiej połowy tego samego projektu i pisze to, co tam działa; komunikat mówiący mu
„nie znam opcji `--limit-kmh=72`" jest wtedy podwójnie mylący, bo opcję zna, a postaci
nie zna z powodu, o którym nie mówi.

Dlatego komunikat nazywa **postać** i podaje działającą komendę:

```
line --limit-kmh=72     kod=1  BŁĄD: polecenie line nie przyjmuje postaci
                               --opcja=wartość. Opcję --limit-kmh zna — podaj ją
                               jako dwa człony: --limit-kmh 72
budget --limit-kmh=72   kod=1  BŁĄD: polecenie budget nie przyjmuje postaci …
```

Nazwa polecenia bierze się z `args[0]` przez ten sam mechanizm, co od 6.D20 — drugi
wiersz pokazuje to wykonaniem, nie obietnicą.

## 4. Flaga dostaje inną radę, i to wyszło z własnego sondowania

Pierwsza wersja komunikatu mówiła **każdemu** znanemu przedrostkowi „podaj jako dwa
człony". Dla flagi to nieprawda:

```
budget … --atp=1     PIERWSZA WERSJA: … podaj ją jako dwa człony: --atp 1
```

`--atp` wartości nie bierze, więc `1` zostałoby członem **pozycyjnym** — a odmowa
członów pozycyjnych nie widzi (odsiewa je warunek na minusie, co 6.A15 zmierzyło
i przybiło testem). Komunikat radziłby więc komendę, która kończy się kodem 0
i cichym zignorowaniem `1`. To jest **ta sama usterka, którą ta pozycja zamyka,
przesunięta o jedno miejsce**: rada mówiąca nieprawdę zamiast komunikatu mówiącego
nieprawdę.

Po poprawce:

```
budget … --atp=1     kod=1  BŁĄD: polecenie budget nie przyjmuje postaci
                            --opcja=wartość, a --atp jest flagą i wartości nie
                            bierze — podaj samo --atp
```

## 5. Drugie znalezisko własnego sondowania: komunikat runnera pisany w odrzuconej postaci

`Program.cs` sam wypisywał:

```
replay --limit-kmh=-5 nie jest dodatnią prędkością
```

Od tej pozycji runner tę postać **odrzuca**, więc komunikat radził komendę, której sam
by nie wykonał. Poprawione na dwa człony, i **pilnuje tego bramka**, nie tylko dobra
wola: `test_no_message_writes_a_known_option_in_the_equals_form` przechodzi po
wszystkich nazwach z `KnownOptions` i szuka `<opcja>=` w kodzie **bez komentarzy** —
komentarz, który tę postać WYJAŚNIA, nie jest komunikatem, a bramka zapalająca się na
poprawnym tekście zostaje wyłączona, nie naprawiona.

## 6. Przedrostek też nieznany — druga połowa tego samego rozbioru

```
line --zmyslona=7    kod=1  BŁĄD: polecenie line nie zna opcji --zmyslona. Zna: …
```

Komunikat zostaje o nieznanej opcji, ale nazywa `--zmyslona`, a nie `--zmyslona=7` —
bo opcja, której nie ma w tabeli, nazywa się `--zmyslona`. To nie jest osobna funkcja,
tylko drugie ramię tego samego `if`; treść odmowy ma jednego pisarza (`Nieznana`),
z tego samego powodu, dla którego 6.A20 wydzieliła `Provenance`, a 6.A14 `NotANumber`.

## 7. Co się NIE zmieniło — sprawdzone wykonaniem

```
line --zmyslona 7                kod=1  BŁĄD: … nie zna opcji --zmyslona. Zna: …
line -zmyslona 7                 kod=1  BŁĄD: … nie zna opcji -zmyslona. Zna: …   (6.A15)
line --brake-usage -0.5          kod=1  BŁĄD: Ułamek hamulca musi być … (walidacja dziedzinowa)
line --trace build/a=b.csv       kod=0   równość w WARTOŚCI znanej opcji przechodzi
budget … --atp                   kod=0
line --limit-kmh 72              kod=0
```

Czwarty wiersz jest wart osobnej uwagi: równość w **wartości** znanej opcji nie jest
postacią `--opcja=wartość`. Ścieżka `build/a=b.csv` stoi po `--trace`, więc jest
pomijana razem z opcją; odmowa zbudowana na samym wystąpieniu znaku równości
wywróciłaby ten przejazd. Ma to swój test i swoją kontrolę negatywną (KN-3b).

## 8. Kontrole negatywne — WYKONANE, pięć

```
KN-1  galaz rownosci zdjeta w calosci
      Failed Postac_z_rownosciem_nazywa_postac_a_nie_nieznana_opcje
      Failed Postac_z_rownosciem_na_fladze_nie_radzi_dwoch_czlonow
      Failed Nieznany_przedrostek_z_rownosciem_nazywa_sam_przedrostek
      Failed!  - Failed: 3, Passed: 567, Total: 570
      + bramka: FAIL test_the_refusal_splits_a_token_on_the_equals_sign
                FAIL test_there_is_one_writer_of_the_unknown_option_message   (6/8)

KN-2  galaz FLAGI zdjeta (flaga dostaje rade dla opcji z wartoscia)
      Failed Postac_z_rownosciem_na_fladze_nie_radzi_dwoch_czlonow
      Failed!  - Failed: 1, Passed: 569, Total: 570
      bramka: 8/8 — i to jest wynik, nie przeoczenie; patrz nizej

KN-3b rownosc sprawdzana na KAZDYM czlonie, przed filtrem minusa
      Failed Postac_z_rownosciem_nazywa_postac_a_nie_nieznana_opcje
      Failed Postac_z_rownosciem_na_fladze_nie_radzi_dwoch_czlonow
      Failed Nieznany_przedrostek_z_rownosciem_nazywa_sam_przedrostek
      Failed!  - Failed: 3, Passed: 567, Total: 570
      + bramka: FAIL test_the_refusal_splits_a_token_on_the_equals_sign

KN-4  cala odmowa nieznanej opcji zdjeta
      Failed Line_z_nieznana_opcja_konczy_sie_kodem_jeden
      Failed Line_z_jednym_minusem_konczy_sie_kodem_jeden
      Failed Replay_nie_zna_wybiegu_bo_odtwarza_zapis_wejsc
      Failed Odmowa_wymienia_opcje_tego_polecenia_a_nie_wszystkich
      Failed Literowka_nadal_dostaje_komunikat_o_nieznanej_opcji
      Failed Postac_z_rownosciem_nazywa_postac_a_nie_nieznana_opcje
      Failed Postac_z_rownosciem_na_fladze_nie_radzi_dwoch_czlonow
      Failed Nieznany_przedrostek_z_rownosciem_nazywa_sam_przedrostek

KN-5  komunikat `replay` wraca do postaci z rownosciem
      FAIL test_no_message_writes_a_known_option_in_the_equals_form: komunikat albo
           kod pisze znana opcje w postaci z rownoscia: [('budget', '--limit-kmh'),
           ('line', '--limit-kmh'), ('replay', '--limit-kmh')]                  (7/8)
```

Suma 570 nie spada w żadnej z nich — po nauczce z 6.B27 jest to część kontroli.

**KN-2 jest tu najciekawszy i mówi coś o obu rodzajach kontroli.** Mutacja zlewała
gałąź flagi z gałęzią opcji wartościowej — i bramka Pythona przeszła **8/8**, bo oba
literały komunikatu wciąż stały w pliku, tylko jeden był nieosiągalny. Bramka czytająca
tekst widzi **kształt**, nie zachowanie; wywrócił ją dopiero test C#, który uruchamia
`Program.Main`. To nie jest wada bramki i nie jest to argument, żeby ją poprawić do
rozpoznawania osiągalności: to argument, dla którego **obie** istnieją, i dlatego ten
wynik jest tu wypisany, a nie przemilczany.

**KN-4 mierzy wartość kontroli drugiego kierunku**, o którą pole „Skończone, gdy"
prosiło wprost: bez `Literowka_nadal_dostaje_komunikat_o_nieznanej_opcji` odmowa zdjęta
w całości przeszłaby wszystkie testy tej pozycji, bo `--limit-kmh=72` i `--atp=1`
kończyłyby się wtedy kodem 0 — a cztery testy z 6.A11 i 6.A15 pokazują, ile odmowa
trzyma.

## 9. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 570, Skipped: 0, Total: 570        (565 + 5)

$ python3 tools/tests/test_all.py
  RAZEM 69.897 s, 1841 testów, 98 modułów
kod: 0
```

Zestaw narzędzi 1838 → **1841**: trzy nowe testy w `test_runner_options.py`
(8 zamiast 5), bez nowego modułu.

## 10. Czego świadomie nie zrobiono

- **Nie przepisano wiersza poleceń na bibliotekę do rozbioru argumentów** — pole „Poza
  zakresem": to zmiana zależności, a `Option`/`RequiredNumber`/`OptionalNumber` są dziś
  jednym miejscem, które `test_runner_options.py` umie czytać.
- **Nie obsłużono postaci `--opcja=wartość`** — droga odrzucona pomiarem z §2, nie
  z góry. Gdyby kiedyś jakaś komenda CI zaczęła jej wobec runnera używać, pomiar wyjdzie
  inaczej i wtedy wraca pierwsza droga; bramka z §5 pokaże to jako FAIL, zamiast czekać
  na czyjeś oko.

  > **Adnotacja z 07.09.2026, dopisana przy 6.A26 — zdanie wyżej BYŁO NIEPRAWDZIWE.**
  > Bramka z §5 (`test_no_message_writes_a_known_option_in_the_equals_form`) czyta
  > **wyłącznie** `src/Sim.Runner/Program.cs` i pilnuje, żeby komunikaty runnera nie
  > były pisane w odrzuconej postaci. Komenda w `.github/workflows/*.yml`, w `docs/`
  > albo w `tools/**/*.sh` była **poza jej zasięgiem**, więc obietnica „pokaże to jako
  > FAIL, zamiast czekać na czyjeś oko" nie miała pokrycia w kodzie. Zdanie zostaje
  > tam, gdzie było — pomiar i tekst z datą się nie przelicza — a domyka je 6.A26:
  > `test_no_runner_command_in_the_repository_uses_the_equals_form` klasyfikuje **każde**
  > wystąpienie tej postaci w repozytorium po wołanym programie i odmawia, gdy trafi
  > w komendę runnera. Pomiar w `reports/pomiar-rownosci.md`.
- **Nie tknięto konwencji sceny.** `RunPlan` postaci z równością wymaga i to jest jej
  wybór, przybity 27 testami w `tests/Game.Tests`. Ujednolicanie dwóch połów projektu
  jest decyzją właściciela, nie skutkiem ubocznym poprawki komunikatu.
- **Nie tknięto powtórzonej opcji** — to 6.A23, z tego samego sondowania.

## 11. Co zauważone przy okazji, nietknięte

- **Człon pozycyjny nadal przechodzi w milczeniu.** `budget … --atp 1` kończy się
  kodem 0 i `1` jest ignorowane; to samo dotyczy każdej wartości podanej fladze. Odmowa
  odsiewa człony bez minusa świadomie (ścieżki `compare`), więc zamknięcie tej dziury
  wymagałoby wiedzy, ile członów pozycyjnych bierze każde polecenie — czyli nowego pola
  w `KnownOptions`. Nie jest to ta pozycja i nie dopisuję tego jako zadania z głowy;
  zauważone tutaj, żeby nie zginęło.
