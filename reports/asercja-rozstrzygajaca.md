# Asercja rozstrzygająca, nie tylko prawdziwa (6.A29)

**Zmierzone 07.09.2026 na commicie:** `8dc5af5aaf135d0ac50149ad179fad6fb6e1a2a8`
(baza gałęzi `claude/6a29-asercja-rozstrzygajaca`, czyli `main` po scaleniu #369).

## 1. Skąd — i dlaczego to nie był domysł

Kontrola negatywna KN-1 pozycji 6.A25 zdjęła `compare` liczbę członów pozycyjnych
(2 → 0). Pięć testów `compare` padło, a `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie
_pierwszy` **został zielony** — mimo że mierzy tę samą komendę. Powód, wykonany:

```
$ compare build/zepsuty.csv build/dobry.csv     # przy compare Positional=0
BŁĄD: polecenie compare dostało człon pozycyjny build/zepsuty.csv, a nie bierze ani
jednego. Człon bez minusa nie jest opcją, …
kod=1
```

Trzy asercje tego testu — kod 1, treść zawiera `zepsuty`, treść **nie** zawiera
`dobry` — są spełnione przez komunikat o rzeczy zupełnie innej.

## 2. Pomiar, o który prosiło pole „Wyjście": ile testów miało asercję rozstrzygającą

Pole żądało tego pomiaru **przed** poprawką, bo od niego zależało, czy poprawka jest
jedna i wspólna, czy cztery osobne. Przejście po ciałach czterech testów rodziny 6.A24:

| test | asercje | rozstrzyga? |
|---|---|---|
| `Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne` | kod 1, ścieżka, `wiersz 3`, `kolumna 1`, `step`, `abc` | **tak** |
| `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` | kod 1, ścieżka, brak ścieżki dobrej | **nie** |
| `Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu` | kod 1, `kolumna 5`, `speed_mps`, `wiersz 7` | **tak** |
| `Dwa_poprawne_pliki_nadal_przechodza` | kod 0, `[PORÓWNANIE]` na stdout | drugi kierunek |

**Trzy z czterech, nie zero z czterech.** Poprawka dotyczy więc **jednego** testu —
warunek z pola „Wyjście" („jeżeli wszystkie cztery, poprawka jest jedna i wspólna")
nie zaszedł, i to jest odpowiedź, o którą pozycja prosiła.

Licząc tylko testy asercjonujące **treść odmowy** (trzy z czterech; czwarty mierzy
drugi kierunek i treści odmowy nie ma czego asercjonować): **2 z 3 przed poprawką,
3 z 3 po**.

## 3. Co dołożono

Do jednego testu, cztery asercje na te części komunikatu, których nie ma żadna inna
odmowa runnera. Zmierzone wykonaniem, jaki komunikat ten test naprawdę oglądа:

```
$ compare build/zepsuty.csv build/dobry.csv
BŁĄD: build/zepsuty.csv: wiersz 5 (nagłówek to wiersz 0), kolumna 3 „chainage_m” — „nie-liczba” nie jest liczbą
kod=1
```

`DwaPlikiTelemetrii(5, 2, "nie-liczba")` psuje trzecią kolumnę (`chainage_m`), a nie
drugą — komunikat liczy kolumny **od jednego**, i to jest decyzja 6.A24, nie przypadek.
Dołożone asercje: `wiersz 5`, `kolumna 3`, `chainage_m`, `nie-liczba`.

Asercje są **dopisane, nie przepisane**: tamte trzy były prawdziwe, tylko za słabe.
Skasowanie ich odebrałoby testowi to, co mierzy z nazwy — że komunikat nazywa plik
**zepsuty**, a nie pierwszy z wiersza poleceń.

## 4. Bramka, żeby to nie wróciło

Nowy test po stronie Pythona trzyma tabelę „test → części komunikatu, które musi
asercjonować" i osobno przybija istnienie testu drugiego kierunku. Bez tej drugiej
asercji bramka byłaby zielona także wtedy, gdyby ktoś usunął jedyny test sprawdzający,
że dwa poprawne pliki nadal przechodzą — a wtedy odmowa zbudowana zbyt szeroko nie
miałaby czego wywrócić.

Do tego kontrola przyrządu: czytnik ciała metody wycina od nagłówka do pierwszego
`\n    }`, a gdyby wycinał do końca pliku, bramka byłaby zielona **zawsze**, bo
`wiersz `, `kolumna ` i nazwy kolumn występują w tym pliku wielokrotnie.

## 5. Kontrole negatywne — WYKONANE

**KN-1 — ta, której żądało pole „Skończone, gdy": `compare` z zerową liczbą członów
pozycyjnych musi wywrócić WSZYSTKIE testy 6.A24, a nie cztery z pięciu.**

```
przed 6.A29:                              po 6.A29:
  Failed Zepsuta_komorka_nazywa_plik…       Failed Zepsuta_komorka_nazywa_plik…
  (Zepsuta_..._a_nie_pierwszy ZIELONY)      Failed Zepsuta_..._a_nie_pierwszy
  Failed Numer_i_nazwa_kolumny…             Failed Numer_i_nazwa_kolumny…
  Failed Dwa_poprawne_pliki…                Failed Dwa_poprawne_pliki…
  Failed Compare_z_dwiema_sciezkami…        Failed Compare_z_dwiema_sciezkami…
  Failed Compare_z_trzecia_sciezka…         Failed Compare_z_trzecia_sciezka…
Failed: 5, Passed: 579, Total: 584        Failed: 6, Passed: 578, Total: 584
```

Cztery z czterech testów 6.A24 padają. Piąty i szósty to testy 6.A25 i mają padać
z tego samego powodu.

**KN-2 — dołożone asercje cofnięte** (stan przed tą pozycją):

```
FAIL test_every_cell_refusal_test_asserts_what_only_that_message_carries: test odmowy
     komorki nie asercjonuje czesci komunikatu, ktora odroznia go od kazdej innej
     odmowy `compare`: [('Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy', 'wiersz '),
     (..., 'kolumna '), (..., 'chainage_m')]
9/10 przeszło
```

Bramka nazywa **który** test i **których** części mu brakuje.

**KN-3 — przyrząd oślepiony** (wycinek ciała metody do końca pliku):

```
FAIL test_the_reader_of_test_bodies_is_not_matching_the_whole_file: wycinek ciala
     metody ma 8538 znakow przy pliku 63695 — czytnik bierze za duzo
9/10 przeszło
```

## 6. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 584, Skipped: 0, Total: 584

$ python3 tools/tests/test_all.py test_csharp_assertions.py
  10/10 przeszło          (8 → 10)
```

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono treści komunikatu 6.A24** — pole „Poza zakresem"; on ma rację, słaby
  był test.
- **Nie ruszono reszty `RunnerCommandTests`.** Audyt wszystkich asercji tego pliku to
  inna pozycja niż naprawa jednego testu, który ta wskazuje z nazwy — i pole „Poza
  zakresem" mówi to wprost.
- **Nie skasowano trzech starych asercji tego testu.** Były prawdziwe, tylko za słabe;
  usunięcie ich odebrałoby testowi to, co mierzy z nazwy.
- **Bramka pilnuje trzech testów, nie wszystkich odmów runnera.** Tabela jest wypisana
  ręcznie i to jest jej cena — nowy test odmowy komórki nie będzie pilnowany, dopóki
  ktoś go tam nie dopisze. Wypisanie z nazwy jest jednak jedynym sposobem, żeby ubytek
  jednej asercji był widoczny; próg liczbowy tego nie daje, bo asercje różnych testów
  dotyczą różnych części komunikatu.

## 8. Zauważone przy okazji, nie tknięte

**Wzorzec asercji „prawdziwej, ale nie rozstrzygającej" wyszedł dziś czwarty raz.**
Tutaj (`Contains(sciezka)` spełnione przez odmowę o czym innym), w 6.A27
(`throw` istnieje, cztery `Console.Error` obok — bramka zielona), w 6.A26 (reguła
pierwszeństwa pilnowana wyłącznie komentarzem) i w 6.A25 (KN-2: odmowa z własną stałą
zostawia wszystkie testy C# zielone). Wspólna cecha wszystkich czterech: asercja na
**obecność** czegoś dobrego zamiast na **brak** czegoś złego albo na **liczbę**.
Nie dopisuję z tego zadania, bo pozycja wymyślona na miejscu omija format z sekcji 6
`CLAUDE.md` — ale zapisuję, bo audyt asercji `Contains` / `in body` w całym zestawie
byłby zadaniem z pomiarem, nie z pomysłu.
