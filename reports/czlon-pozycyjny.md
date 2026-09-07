# Człon pozycyjny nieznany żadnemu poleceniu (6.A25)

**Zmierzone 07.09.2026 na commicie:** `a2293e65aba0e477bab63fdc4b8d4aa02010ad75`
(baza gałęzi `claude/6a25-czlon-pozycyjny`, czyli `main` po scaleniu #365).

## 1. Objaw: dwa różne wiersze poleceń, wypis nieodróżnialny

Przed poprawką (pomiar przy 6.A22, potwierdzony tutaj osobno):

```
budget … --atp 1          kod=0   [BUDŻET] … ATP=tak …      ← `1` zignorowane
budget … --atp            kod=0   [BUDŻET] … ATP=tak …      ← wypis identyczny
budget … zmyslony_czlon   kod=0   [BUDŻET] … ATP=nie …
```

Po:

```
$ … budget --axis data/track/L1_A.json --signalling …/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 90 --trains 2 --steps 100 --atp 1
BŁĄD: polecenie budget dostało człon pozycyjny 1, a nie bierze ani jednego. Człon bez
minusa nie jest opcją, więc wartość podana po fladze (np. --atp 1) trafia właśnie tutaj
kod=1

$ … --steps 100 zmyslony_czlon
BŁĄD: polecenie budget dostało człon pozycyjny zmyslony_czlon, a nie bierze ani jednego. …
kod=1

$ … --steps 100 --atp
[BUDŻET] oś L1_A, plan classic-2026-L1_A (23 bloków), 12 stacji, ATP=tak, nawrót 0 s, …
kod=0
```

## 2. Pomiar, o który prosiło pole „Wyjście": jedna liczba czy nowy rozbiór

Pozycja żądała rozstrzygnięcia **pomiarem**, ile poleceń bierze dziś choć jeden człon
pozycyjny — bo jeżeli tylko `compare`, wystarcza liczba przy poleceniu. Przejście po
`Program.cs` bez komentarzy, najwyższy indeks `args[N]` dla N ≥ 1 w ciele każdego
polecenia:

```
{'drive': 0, 'replay': 0, 'compare': 2, 'axis': 0, 'parity': 0,
 'braking': 0, 'line': 0, 'budget': 0, 'service-day': 0}
```

**Jedno polecenie, dwa człony.** `Compare` czyta `args[1]` i `args[2]`; poza samym
rozbiorem opcji w `Program.cs` nie ma ani jednego innego odczytu `args[N]` dla N > 0.
Jedna liczba przy poleceniu wystarcza, nowy rozbiór nie jest potrzebny — i to jest
zmierzone, a nie założone z góry.

Liczba stoi jako **trzecie pole** `KnownOptions` (`Positional`), a bramka po stronie
Pythona wyprowadza ją drugi raz z odczytów `args[N]` i porównuje. Ten sam układ, który
od 6.A11 pilnuje samych nazw opcji, z tego samego powodu: ręcznie wypisana liczba
starzeje się po cichu.

Czytnik jest **osobny** od `declared_table`, celowo. Tamten szuka `new[] {…}` albo
`Array.Empty<string>()` i liczby by nie zobaczył; doklejenie trzeciego pola do niego
zmusiłoby go do zwracania trójki wszędzie, gdzie dziś zwraca parę, i poprawka jednego
z dwóch pomiarów psułaby drugi.

## 3. Kontrole negatywne — WYKONANE, nie opisane

**KN-1 — zdjęta liczba członów `compare` (2 → 0).** Tego żądało pole „Skończone, gdy":
ma wywrócić test `compare`, a nie tylko nowy test.

```
FAIL test_the_positional_count_matches_what_each_command_reads: tabela i kod nie
     zgadzaja sie … tabela {'compare': 0, …} vs kod {'compare': 2, …}
11/12 przeszło  (bramka pythonowa)

  Failed Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne
  Failed Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu
  Failed Dwa_poprawne_pliki_nadal_przechodza
  Failed Compare_z_dwiema_sciezkami_nadal_przechodzi
  Failed Compare_z_trzecia_sciezka_nazywa_liczbe_ktora_bierze
Failed!  - Failed: 5, Passed: 579, Total: 584
```

Pięć testów, z czego **trzy starsze od tej pozycji** (6.A24). Liczba w tabeli jest więc
nośna, nie dokumentacyjna.

**KN-2 — odmowa z własną stałą zamiast odczytu z tabeli.** `known.Positional` zastąpione
wyrażeniem `command == "compare" ? 2 : 0` — zachowanie identyczne, źródło prawdy inne:

```
FAIL test_the_refusal_counts_positional_members_against_the_table: odmowa nie czyta
     liczby czlonow pozycyjnych z tabeli
11/12 przeszło

Passed!  - Failed: 0, Passed: 584, Total: 584
```

**Wszystkie testy C# zostają zielone.** To jest dokładnie usterka 6.D30 — bramka
porównująca dwa pola, z których żadne nie jest czytane przez kod, zgadza się zawsze —
i dlatego kontrola przyrządu stoi w zestawie na stałe, a nie tylko w tym raporcie.

**KN-3 — sama odmowa zdjęta, licznik zostaje (stan przed 6.A25).**

```
FAIL test_the_refusal_counts_positional_members_against_the_table: odmowa nie nazywa
     czlonu pozycyjnego po imieniu
11/12 przeszło

  Failed Wartosc_po_fladze_jest_czlonem_pozycyjnym_i_konczy_sie_odmowa
  Failed Czlon_pozycyjny_nieznany_poleceniu_konczy_sie_odmowa
  Failed Compare_z_trzecia_sciezka_nazywa_liczbe_ktora_bierze
Failed!  - Failed: 3, Passed: 581, Total: 584
```

Dokładnie trzy odmowy. `Compare_z_dwiema_sciezkami_nadal_przechodzi` i
`Wartosci_znanych_opcji_nie_licza_sie_jako_czlony_pozycyjne` zostają zielone —
mierzą drugi kierunek i mają zostać.

## 4. Test, który padł, i dlaczego to był dobry pomiar

Pierwsza wersja `Wartosc_ujemna_po_znanej_opcji_nadal_przechodzi` żądała kodu **0** dla
`line … --coast-from-m -1` i padła:

```
Assert.AreEqual failed. Expected:<0>. Actual:<1>.
BŁĄD: Początek wybiegu musi być skończone i nieujemne. (Parameter 'coastFromM')
```

Odmowa jest **z dziedziny**, nie z rozbioru argumentów — czyli test mierzył zakres
wartości opcji, a nie to, co ta pozycja zmienia. Przepisany na właściwy pomiar:
wartość ujemna **dochodzi do dziedziny**, więc rozbiór jej nie przechwycił jako
członu pozycyjnego ani jako nieznanej opcji.

## 5. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 584, Skipped: 0, Total: 584

$ python3 tools/tests/test_all.py test_runner_options.py
  12/12 przeszło        (9 → 12, trzy nowe testy)
```

## 6. Czego świadomie nie zrobiono

- **Nie przepisano wiersza poleceń na bibliotekę do rozbioru argumentów** — ta sama
  granica, którą postawiły 6.A11, 6.A15 i 6.A22.
- **Człon `-` sam w sobie liczy się jako pozycyjny.** To konwencja „standardowe
  wejście", której to repozytorium nie używa; gdyby zaczęło, `-` będzie musiało dostać
  własną gałąź, tak jak dziś ma w odmowie z 6.A15. Zostawione, bo poleceń biorących
  człony pozycyjne jest jedno i ono ścieżek ze standardowego wejścia nie czyta.
- **Nie tknięto liczby członów, jaką `compare` sprawdza u siebie.** `compare wymaga
  dwóch plików` przy jednej ścieżce zostaje tam, gdzie było: odmowa 6.A25 mówi o członie
  NADMIAROWYM, a brak drugiej ścieżki to brak, nie nadmiar. Dwie różne odmowy dwóch
  różnych rzeczy, każda ze swoim komunikatem.

## 7. Zauważone przy okazji, nie tknięte

**Test `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` przechodzi w KN-1 z całkiem
innego powodu, niż sądzi.** W KN-1 wywróciło się pięć testów `compare`, ale ten nie —
mimo że mierzy tę samą komendę. Powód, zmierzony wykonaniem:

```
$ compare build/zepsuty.csv build/dobry.csv     # przy compare Positional=0
BŁĄD: polecenie compare dostało człon pozycyjny build/zepsuty.csv, a nie bierze ani
jednego. Człon bez minusa nie jest opcją, …
kod=1
```

Trzy asercje tego testu — kod 1, komunikat zawiera `zepsuty`, komunikat NIE zawiera
`dobry` — są spełnione przez komunikat o rzeczy zupełnie innej. Test wierzy, że
sprawdził „odmowa nazywa zepsuty plik, a nie pierwszy"; sprawdził, że gdzieś w treści
stoi pierwsza ścieżka. Nie tknięte, bo to nie jest zakres tej pozycji, ale jest to ten
sam gatunek usterki, którą ta sesja widziała dziś kilka razy: **przyrząd meldujący
zgodę zamiast pomiaru.** Właściwą poprawką jest asercja na `wiersz`/`kolumna`
z komunikatu 6.A24, nie na samą nazwę pliku.
