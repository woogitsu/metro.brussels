# Powtórzona opcja przyjmowana w milczeniu (6.A23)

**Zmierzone 07.09.2026 na commicie:** `a6e280d2ef22e196f474bb168611fb6fa0e91c52`
(gałąź `claude/6a23-powtorzona-opcja`).

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na
`fdd5a9b` (scalenia #351 — 6.A22, pięć testów C# — #352 — 6.D29 — i #353 —
uzupełnienie kolejki). Oba zestawy przebiegły na nowej podstawie ponownie i dały ten
sam werdykt oraz tę samą deltę: C# **570 → 574**, narzędzia **+1** test. Liczby z dnia
pomiaru (565 → 569, 1841 → 1842) nie są przeliczane; ta adnotacja mówi, co powtórzono.

## 1. Stan wyjściowy: wygrywa pierwsza, druga znika bez słowa

```
$ line --axis data/track/L1_A.json --limit-kmh 72 --limit-kmh 50 --exchange-s 20
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 820.42 s, postoje 313.59 s, kroków 101872
kod=0

$ line --axis data/track/L1_A.json --limit-kmh 50 --limit-kmh 72 --exchange-s 20
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 901.76 s, postoje 313.59 s, kroków 111632
kod=0
```

Dwa przebiegi **różnią się o 81 sekund i 9760 kroków**, bo jeden jechał 72 km/h,
a drugi 50 — i oba skończyły się kodem 0 bez ani jednego zdania o tym, że wiersz
poleceń podawał dwie wartości. `Option` szuka pierwszego wystąpienia i nie patrzy dalej.

**Co NIE było tu problemem.** Wartość skuteczna nie była niewidoczna: `[LINIA]`
i `[ZAŁOŻENIE]` ją podają, i to jest zasługa 6.A5/6.A6. Problemem był brak informacji,
że **coś zostało odrzucone** — czytający widział 72 i nie miał powodu przypuszczać,
że komenda mówiła także 50. Od 6.A20 nastawy trafiają również do plików z `--out`,
więc ta sama luka siedziała w artefakcie, który **przeżywa proces** i trafia do raportów.

## 2. Odmowa czy wypis o nadpisaniu — rozstrzygnięte pomiarem

Pole „Wyjście" dawało dwa kierunki i **warunek wyboru**: odmowa jest spójniejsza
z 6.A16 („każda odmowa argumentowa = 1"), ale najpierw trzeba sprawdzić, czy któryś
skrypt CI albo `docs/` nie podaje świadomie tej samej opcji dwa razy — bo wtedy odmowa
wywróciłaby przebieg, który dziś działa.

Policzone przez sklejenie kontynuacji wierszy (`\`) i porównanie nazw opcji w każdej
komendzie wołającej `Sim.Runner` albo scenę:

```
komendy z POWTORZONA opcja:  4
  Sim.Runner  reports/jeden-minus.md:43   {'--no-build': 2}   ← proza; dwie komendy w jednym bloku
  Sim.Runner  docs/TASKS.md:702           {'--coast-from-m': 2} ← proza wiersza 6.A11
  Sim.Runner  docs/TASKS.md:727           {'--limit-kmh': 9}    ← proza wiersza 6.A22
  Sim.Runner  docs/TASKS.md:3333          {'--limit-kmh': 2}    ← pole „Weryfikacja" TEJ pozycji
```

**Ani jedno z czterech dopasowań nie jest prawdziwą komendą podającą opcję dwa razy.**
Trzy pierwsze to proza raportu i wierszy tabeli (licznik widzi nazwy opcji w tekście
zdania), czwarte to komenda z pola „Weryfikacja" tej pozycji. `--no-build` w pierwszym
stoi **przed** separatorem `--`, czyli jest flagą `dotnet run` i do `args` nie dochodzi —
ta sama pułapka, którą 6.A15 zmierzyło dla `-c Release`.

Zero prawdziwych powtórzeń, więc odmowa jest wolna i wybrana: kod 1, jak dla każdej
innej złej nastawy.

## 3. Co zostało zrobione

Odmowa z 6.A11 zapamiętuje teraz opcje z wartością widziane w tym wierszu poleceń
(`HashSet<string>` z porównaniem `Ordinal`) i drugie wystąpienie jest błędem:

```
line --limit-kmh 72 --limit-kmh 50   kod=1  BŁĄD: polecenie line dostało opcję
                                            --limit-kmh więcej niż raz. Wygrałaby
                                            pierwsza wartość, a pozostałe zniknęłyby
                                            bez słowa — podaj ją dokładnie raz
line --limit-kmh 50 --limit-kmh 72   kod=1  (ten sam komunikat)
```

**FLAG to nie dotyczy i jest to pole „Poza zakresem" tej pozycji, nie przeoczenie:**
`--atp --atp` znaczy dokładnie to samo, co `--atp`, więc nie ginie tam żadna wartość.
Sprawdzone uruchomieniem — kod 0 przed zmianą i po niej — i przybite testem, żeby
późniejsze przesunięcie tej granicy było widoczne, a nie ciche.

## 4. Przejazd nietknięty — dowód bajtowy, nie zapewnienie

Pole „Skończone, gdy" żądało wprost: przebieg z opcją podaną **raz** ma być
niezmieniony, **bit w bit** dla telemetrii. Zmierzone przez zbudowanie obu wersji
tego samego pliku binarnego i porównanie plików `--trace`:

```
$ line … --limit-kmh 72 --exchange-s 20 --trace build/po.csv      (po zmianie)
$ git stash && dotnet build … && line … --trace build/przed.csv   (przed zmianą)

po zmianie:   11d298315379ba7fbb4673250daeab83…
przed zmiana: 11d298315379ba7fbb4673250daeab83…
$ cmp build/przed.csv build/po.csv
IDENTYCZNE co do bajtu           (101 873 wiersze)
```

Ta pozycja nie ma prawa tknąć przejazdu i tego nie zrobiła.

## 5. Kontrole negatywne — WYKONANE, trzy

```
KN-1  kontrola powtorzenia zdjeta
      Failed Powtorzona_opcja_konczy_sie_odmowa
      Failed Powtorzona_opcja_odmawia_w_obu_kolejnosciach
      Failed!  - Failed: 2, Passed: 567, Total: 569
      + bramka: FAIL test_the_refusal_catches_a_repeated_value_option_but_not_a_repeated_flag

KN-2  FLAGA tez liczona jako powtorzenie
      Failed Powtorzona_flaga_nie_jest_odmowa
      Failed!  - Failed: 1, Passed: 568, Total: 569
      + bramka: FAIL test_the_refusal_catches_a_repeated_value_option_but_not_a_repeated_flag

KN-3  odmowa przy PIERWSZYM wystapieniu (warunek odwrocony)
      Failed ServiceDay_z_niepoprawnym_formatem_at_konczy_sie_kodem_jeden
      Failed Line_z_nieznana_opcja_konczy_sie_kodem_jeden
      Failed Line_zna_wybieg_i_nie_odmawia_go
      Failed Line_z_jednym_minusem_konczy_sie_kodem_jeden
      Failed Wartosc_ujemna_znanej_opcji_nie_jest_brana_za_opcje
      Failed Budget_zapisuje_nastawy_do_pliku_a_nie_tylko_na_konsole
      … (odmowa przy pierwszym wystapieniu wywraca kazda komende z opcja)
```

Suma 569 nie spada w żadnej z nich — po nauczce z 6.B27 jest to część kontroli.

**KN-2 mierzy dokładnie tę granicę, którą pole „Poza zakresem" postawiło**: gdyby
zbiór widzianych opcji obejmował flagi, `--atp --atp` zaczęłoby być odmową — czyli
pozycja zrobiłaby o jeden krok więcej, niż jej zlecono, i nikt by tego nie zauważył
bez tego testu. Bramka Pythona łapie to z drugiej strony, przez kod: `seen` ma być
dotykane w **jednym** miejscu i gałąź flagi nie ma go widzieć.

**KN-3 mierzy wartość kontroli pozytywnej.** Odwrócenie warunku na `if (seen.Add(…))`
robi odmowę z **każdej** komendy podającej choć jedną opcję — i wywraca sześć testów,
w tym `Opcja_podana_raz_nadal_przechodzi`. Bez niego dwa testy z §3 przeszłyby również
dla poprawki, która nie działa wcale.

## 6. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 569, Skipped: 0, Total: 569        (565 + 4)

$ python3 tools/tests/test_all.py
  RAZEM 74.279 s, 1842 testów, 98 modułów
kod: 0
```

1842 = 1841 + **1** (jeden test w `test_runner_options.py`, bez nowego modułu).

## 7. Czego świadomie nie zrobiono

- **Nie rozstrzygano konfliktów między opcjami RÓŻNYMI** (np. `--limit-kmh` ponad limit
  planu sygnalizacji) — osobne zagadnienie, opisane przy #246; pole „Poza zakresem".
- **Nie tknięto flag.** `--atp --atp` przechodzi i ma na to test. Uzasadnienie jest
  rzeczowe, nie wygodne: powtórzona flaga nie gubi żadnej wartości, więc nie ma tu
  wyroczni zepsutej w stronę „wszystko w porządku".
- **Nie zmieniono `Option` ani `Provenance`.** Poprawka siedzi w jednym miejscu —
  w odmowie, która i tak przechodzi po wszystkich członach — więc `Option` nie musi
  wiedzieć o niczym nowym, a plik z `--out` niesie nastawy tak samo jak dotąd.

## 8. Co zauważone przy okazji, nietknięte

- **Licznik powtórzeń widzi nazwy opcji w prozie** i to jest jego jedyna wada, którą
  §2 nazywa liczbą: cztery dopasowania, z których zero jest komendą. Nie budowałem
  z niego bramki właśnie dlatego — bramka zapalająca się na wierszu tabeli w
  `docs/TASKS.md` zostałaby wyłączona przy pierwszym raporcie opisującym tę pozycję.
  Powtórzenia pilnuje więc **runner**, przy uruchomieniu, gdzie proza nie dochodzi.

- **Bramka z 6.B28 złapała mój własny zepsuty rebase, w godzinę po scaleniu.** Przy
  rozstrzyganiu konfliktu w `RunnerCommandTests.cs` (dwie pozycje dopisały testy w tym
  samym miejscu) zniknęła klamra zamykająca jedną metodę. Zestaw C# odmówił kompilacji,
  ale **przed** nim odezwała się bramka kształtu:

  ```
  FAIL test_the_shape_covers_every_test_attribute: 4 atrybutow testowych jest poza
       ksztaltem bramki: {'atrybuty_w_plikach': 736, 'objete_ksztaltem': 732,
       'poza_ksztaltem': 4}
  ```

  Po naprawie klamry: **736 / 736 / 0**. Zapisuję to, bo bramka postawiona po to, żeby
  łapać metodę bez atrybutu, złapała przy okazji uszkodzoną strukturę pliku — i zrobiła
  to na drzewie, na którym `dotnet` nie musiał się nawet uruchomić.
