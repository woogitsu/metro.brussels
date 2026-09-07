# Nieliczbowa wartość opcji nazywa siebie (6.A14)

**Zmierzone 07.09.2026 na commicie:** `7dbea51e3b54c0877905fcbeefe397eb338f865b`
(gałąź `claude/6a14-wartosc-nieliczbowa`).

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na
`7bf5062` (scalenie #346 — 6.A15, trzy nowe testy C#). Oba zestawy przebiegły
na nowej podstawie ponownie: narzędzia **1836 testów, 98 modułów, kod 0** bez zmiany,
zestaw C# **565/565** — bo baza urosła z 554 na 557, a te osiem testów dokłada się do
niej tak samo. Delty w §7 i §8 (554 → 562, sumy 562 przy kontrolach negatywnych)
zostają liczbami z dnia pomiaru; nie są przeliczane, a ta adnotacja mówi, na czym
polega różnica.

## 1. Stan wyjściowy — jedenaście dróg, jeden komunikat platformy

6.D20 (#312) poprawiła komunikat o **braku** opcji i wprost zostawiła nietknięty ten
o złej **wartości**. Przesondowane dziś, przed jakąkolwiek zmianą — jedenaście
wywołań, każde z pełnym, poprawnym otoczeniem, żeby błąd był naprawdę w rozbiorze
wartości, a nie w czymś, co stoi przed nim:

```
line --limit-kmh abc          kod=1  BŁĄD: The input string 'abc' was not in a correct format.
line --exchange-s abc         kod=1  BŁĄD: The input string 'abc' was not in a correct format.
drive --sample-every abc      kod=1  BŁĄD: The input string 'abc' was not in a correct format.
compare --tolerance abc       kod=1  BŁĄD: The input string 'abc' was not in a correct format.
budget --steps abc            kod=1  BŁĄD: The input string 'abc' was not in a correct format.
budget --trains abc           kod=1  BŁĄD: The input string 'abc' was not in a correct format.
budget --repeats abc          kod=1  BŁĄD: The input string 'abc' was not in a correct format.
budget --warmup abc           kod=1  BŁĄD: The input string 'abc' was not in a correct format.
budget --trains 2,abc         kod=1  BŁĄD: The input string 'abc' was not in a correct format.
service-day --at 10:xx:00     kod=1  BŁĄD: The input string 'xx' was not in a correct format.
service-day --at abc          kod=1  BŁĄD: czas ma mieć postać HH:MM:SS, a jest „abc”
```

Ostatni wiersz jest jedynym, który **już** mówił coś swojego — i to jest ważne dla
zakresu: `ParseClock` sprawdzała **kształt** wartości, a nie liczbowość jej członów,
więc `10:xx:00` przechodziło jej kontrolę i wpadało dalej, w `double.Parse`. Kontrola
kształtu, która przepuszcza wartość do komunikatu platformy, to nie kontrola „prawie
dobra" — to kontrola, która o jednej z dwóch usterek milczy.

## 2. Pomiar, który zmienił rozmiar zadania: cztery pomocniki, nie jeden

Wpis pozycji wymieniał `RequiredNumber`, `OptionalNumber`, `ParseTrainCounts`
i `ParseClock`. Odczyt `Program.cs` pokazał, że dróg jest więcej, bo **trzy opcje
rozbierają się w miejscu wywołania**, bez żadnego pomocnika:

```
254:  var sampleEvery = long.Parse(Option(args, "--sample-every") ?? …, Inv);   ← drive
376:  var sampleEvery = long.Parse(Option(args, "--sample-every") ?? …, Inv);   ← replay
618:  var tolerance   = double.Parse(Option(args, "--tolerance") ?? "1E-9", Inv);
1287: var steps       = long.Parse(Option(args, "--steps") ?? throw …, Inv);
1289: var repeats     = int.Parse(Option(args, "--repeats") ?? "7", Inv);
1290: var warmup      = int.Parse(Option(args, "--warmup") ?? "2", Inv);
```

Typów jest **trzy** (`double`, `long`, `int`), więc poprawka jednego pomocnika nie
dowodzi niczego o pozostałych — i dlatego testy niżej biorą wszystkie cztery drogi
osobno, a nie jedną cztery razy.

`IntValue` jest osobny od `LongValue`, a nie rzutowaniem z niego: rzutowanie
zamieniłoby wartość poza zakresem `int` na inną liczbę **w milczeniu**, czyli na
dokładnie tę klasę wyrocznia-zepsuta-w-dobrą-stronę, którą ta rodzina pozycji zamyka.

## 3. Stan po zmianie

```
line --limit-kmh abc        kod=1  BŁĄD: line nie rozumie wartości --limit-kmh: „abc” nie jest liczbą
line --exchange-s abc       kod=1  BŁĄD: line nie rozumie wartości --exchange-s: „abc” nie jest liczbą
line --stop-window-m abc    kod=1  BŁĄD: line nie rozumie wartości --stop-window-m: „abc” nie jest liczbą
drive --sample-every abc    kod=1  BŁĄD: drive nie rozumie wartości --sample-every: „abc” nie jest liczbą
compare --tolerance abc     kod=1  BŁĄD: compare nie rozumie wartości --tolerance: „abc” nie jest liczbą
budget --steps abc          kod=1  BŁĄD: budget nie rozumie wartości --steps: „abc” nie jest liczbą
budget --repeats abc        kod=1  BŁĄD: budget nie rozumie wartości --repeats: „abc” nie jest liczbą
budget --warmup abc         kod=1  BŁĄD: budget nie rozumie wartości --warmup: „abc” nie jest liczbą
budget --trains 1,2,4,abc   kod=1  BŁĄD: budget nie rozumie wartości --trains: „abc” nie jest liczbą
service-day --at 10:xx:00   kod=1  BŁĄD: service-day nie rozumie wartości --at: „10:xx:00” nie jest liczbą
service-day --at abc        kod=1  BŁĄD: czas ma mieć postać HH:MM:SS, a jest „abc”
```

Nazwa polecenia bierze się z `args[0]` przez wspólny `Command(args)`, nie z nowej
zaszytej stałej — to jest wprost warunek z pola „Skończone, gdy" i zarazem nauczka
z 6.D20, gdzie zaszyta stała `line` myliła w dwóch przypadkach na trzy. Treść ma
**jednego** pisarza (`NotANumber`), z tego samego powodu, dla którego 6.A20 wydzieliła
`Provenance`: trzech pomocników mówiących to samo rozjeżdża się przy pierwszej
poprawce.

## 4. Dwie decyzje przeciwstawne, każda ze swoim testem

| wartość | cytowane | dlaczego |
|---|---|---|
| `--trains 1,2,4,abc` | **człon** `abc` | lista — czytający ma zobaczyć, **który** z czterech jest zły |
| `--at 10:xx:00` | **cała** wartość | zegar jest jedną wartością; `xx` nie powie, którą opcję poprawić |

To jest niespójność **wybrana**, nie przypadkowa, więc każdą połowę pilnuje test —
i każdy z nich zapala się na mutacji tej drugiej decyzji (KN-2 i KN-3 niżej). Bez
tych dwóch testów niespójność zostałaby po pierwszej poprawce jako przypadek.

## 5. Zbiór przyjmowanych postaci się NIE zwężył

`double.Parse(text, Inv)` przyjmował `NumberStyles.Float | NumberStyles.AllowThousands`,
`int.Parse`/`long.Parse` — `NumberStyles.Integer`. `TryParse` dostaje te same zbiory,
więc ta pozycja zmienia **komunikat**, nie to, co runner przyjmuje. Sprawdzone
wykonaniem, bo przeczytanie własnej zmiany nie jest pomiarem:

```
drive (domyslny --sample-every)          kod=0
drive --sample-every 5                   kod=0
line --limit-kmh 72                      kod=0
line --stop-window-m 5.5 (kropka)        kod=0
line --limit-kmh 7.2E1 (wykladnik)       kod=0
compare build/d1.csv build/d1.csv        kod=0
compare … --tolerance 1E-6               kod=0
budget --trains 1,2 --steps 200          kod=0
service-day --at 07:06:44                kod=0
service-day --at 25:10:00 (po polnocy)   kod=0
```

Godzina powyżej 24 przechodzi dalej — doba służby kończy się po północy i GTFS
zapisuje to właśnie tak, więc odmowa byłaby tu regresją, nie poprawką.

**Jedno kod=1, które nie jest tą zmianą.** `compare build/x.csv build/x.csv` na pliku
z `line --trace` kończy się kodem 1 z komunikatem `nagłówki telemetrii nie zgadzają
się z formatem rdzenia` — bo `--trace` pisze inny format niż `drive`. Zachowanie
sprzed zmiany, potwierdzone przebiegiem na prawdziwym pliku `drive` (kod 0 wyżej);
w tabeli stoi, żeby nie wyglądało na przemilczane.

## 6. Bramka, bo testy C# sprawdzają wywołania, a nie kod

`tools/tests/test_runner_number_parsing.py` (8 testów) czyta `Program.cs` jako tekst.
Powód jest ten sam, który miał `test_runner_exit_codes.py`: **nowa opcja dopisana
gołym `double.Parse` nie złamie żadnego istniejącego testu**, dopóki nikt nie napisze
jej własnego. Ujednolicenie, którego nikt nie pilnuje, rozjeżdża się przy pierwszej
nowej opcji.

Trzy rzeczy w tej bramce są przeniesione z wcześniejszych pozycji, nie wymyślone tu:

- **Klucz po METODZIE, nie po numerze wiersza.** Numer starzeje się przy pierwszej
  wstawce; przy 6.A20 to samo pokazał klucz po nazwie zmiennej.
- **Lista usprawiedliwień sprawdzana w OBIE strony.** Wpis, który przestał być
  potrzebny, też jest błędem — inaczej zostaje po poprawce i przepuszcza następny
  goły `Parse` w tej samej metodzie. Każdy wpis nosi **powód**; lista wymówek bez
  powodów rośnie sama (6.A20, KN-4 tamtej pozycji).
- **Próg na liczbę miejsc rozbioru.** Bramka szukająca wzorca, który przez literówkę
  nie pasuje do niczego, melduje zero znalezisk i świeci na zielono (6.B29, 6.B31,
  6.D27).

Jedyne usprawiedliwienie to `Compare` — rozbiór **komórek CSV**, gdzie komunikat
nazywający opcję byłby nieprawdą, bo zła komórka nie jest złą opcją. To nie znaczy,
że tamten komunikat jest dobry; stoi w kolejce jako **6.A24**.

**Próg wpisałem najpierw jako 7 i sam się zapalił przy pierwszym przebiegu** — bo
7 było moim szacunkiem („5 razy `TryParse`"), a `TryParse` jest w **czterech**
miejscach: `NumberValue`, `LongValue`, `IntValue`, `ParseClock`. Zmierzone: 2 gołe
(komórki CSV) + 4 = **6**. Liczba jest poprawiona w commicie, który ją znalazł,
razem ze zdaniem mówiącym, skąd wzięła się poprzednia — piąty raz dzisiaj, gdy
opublikowana liczba wyszła z szacunku albo z dopasowania tekstu, a nie z pomiaru.

## 7. Kontrole negatywne — WYKONANE, siedem

```
KN-1  NumberValue wraca do golego double.Parse
      Failed Line_z_nieliczbowym_limitem_nazywa_polecenie_opcje_i_wartosc
      Failed Budget_z_nieliczbowym_limitem_nazywa_budget_a_nie_line
      Failed Line_z_nieliczbowym_oknem_stacji_nazywa_opcje
      Failed!  - Failed: 3, Passed: 559, Total: 562
      + bramka: FAIL test_no_option_value_reaches_a_bare_parse
                FAIL test_one_writer_of_the_message                (6/8)

KN-2  ParseTrainCounts cytuje cala liste zamiast czlonu
      Failed Trains_cytuje_zly_czlon_a_nie_cala_liste
      Failed!  - Failed: 1, Passed: 561, Total: 562

KN-3  ParseClock cytuje czlon zamiast calej wartosci
      Failed Zegar_cytuje_cala_wartosc_a_nie_zly_czlon
      Failed!  - Failed: 1, Passed: 561, Total: 562

KN-4  NumberValue zwezony do NumberStyles.None
      Failed Kropka_dziesietna_i_wykladnik_nadal_przechodza
      Failed!  - Failed: 1, Passed: 561, Total: 562

KN-5  drugi pisarz tresci komunikatu (LongValue z wlasnym napisem)
      FAIL test_one_writer_of_the_message: tresc … stoi w 2 miejscach zamiast
           w jednym                                                (7/8)

KN-6  literowka we wzorcu typow ("doubel")
      FAIL test_parse_site_count_is_above_the_floor: miejsc rozbioru liczby jest
           2 przy progu 6
      FAIL test_detector_lights_up_on_injected_bare_parse
      FAIL test_the_allow_list_is_exact_in_both_directions          (5/8)

KN-7  wpis usprawiedliwienia, ktoremu nic nie odpowiada (LineCommand)
      FAIL test_the_allow_list_is_exact_in_both_directions: … obiecuje 1
           wystapien golego Parse, a jest 0                         (7/8)
```

Suma 562 nie spada w żadnej z nich — po nauczce z 6.B27 (metoda, która straciła
`[TestMethod]`, miała asercje i nie była uruchamiana; objawem była wyłącznie liczba)
jest to część kontroli, nie ozdoba.

**KN-4 i KN-7 mierzą wartość rzeczy, których same testy treści nie łapią.** KN-4:
bez testu na kropkę dziesiętną i wykładnik cała reszta byłaby zielona także dla
poprawki, która **zwęża** zbiór przyjmowanych postaci — a to byłaby regresja
podana jako poprawka komunikatu. KN-7: bez kontroli w obie strony lista
usprawiedliwień rośnie i po pierwszej poprawce przepuszcza to, co miała pilnować.
**KN-6 pokazuje, po co jest próg**: gdyby stał tylko test na goły `Parse`, literówka
we wzorcu dałaby zero znalezisk i zieloną bramkę mierzącą nic.

## 8. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 562, Skipped: 0, Total: 562        (554 + 8)

$ python3 tools/tests/test_all.py
  RAZEM 68.251 s, 1836 testów, 98 modułów
kod: 0
```

1836 = 1828 + **8** (nowy moduł bramki), 98 = 97 + **1**.

## 9. Czego świadomie nie zrobiono

- **Tłumaczenia pozostałych komunikatów platformy .NET** i **zmiany kodów wyjścia** —
  pole „Poza zakresem". Ta sama granica, którą postawiły 6.A10, 6.A11, 6.A13 i 6.D20.
- **Rozbioru komórek CSV w `compare`.** Jedyne usprawiedliwienie w bramce, i wyszło
  z tego samego sondowania. W kolejce jako **6.A24** — osobno, bo tam komunikat ma
  nazwać plik, wiersz i kolumnę, a nie opcję, więc to inna poprawka, nie ta sama.
- **Nie tknięto kontroli kształtu w `ParseClock`.** `--at abc` nadal odpowiada
  komunikatem o `HH:MM:SS`, i to jest właściwa odmowa: kształt jest zły, nie liczba.
  Zmieniono wyłącznie to, co ta kontrola przepuszczała dalej.
- **Nie tknięto postaci `--opcja=wartość`** (6.A22) ani **powtórzonej opcji**
  (6.A23). Obie z wcześniejszego sondowania, obie w kolejce.

## 10. Co zauważone przy okazji, nietknięte

- **`--sample-every` nie jest w `KnownOptions` polecenia `line`** i to jest poprawne:
  czyta je `drive` i `replay`. Sprawdzone, bo pierwsze sondowanie wyglądało na dziurę
  w bramce z 6.A11 — nie jest nią.
- **`budget` czyta `--signalling` przed liczbami**, więc próba z samym `--steps abc`
  odpowiada o brakującym planie sygnalizacji. Kolejność odczytu, nie usterka; wpłynęła
  natomiast na kształt każdej próby w §1 i §3, które muszą podawać pełne otoczenie.
