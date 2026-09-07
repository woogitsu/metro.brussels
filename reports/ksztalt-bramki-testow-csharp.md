# Kształt bramki testów C# — i 27 metod, których nie widziała (6.B28)

**Zmierzone 07.09.2026 na commicie:** `7bf506295338ea1d1b119dbc52990666ef7b6b9e`
(gałąź `claude/6b28-datatestmethod`).

## 1. Wpis mówił o 40 metodach z argumentami. Pomiar mówi: 13 — i 27 czegoś innego

Pozycja 6.B28 stała na liczbie z 6.B27: „**708** atrybutów w plikach, **668**
objętych kształtem, **40 poza** — to `[DataTestMethod]` z wierszami `[DataRow]`,
czyli metody **z argumentami**". Pierwszy pomiar tej pozycji był rozbiciem tych 40
na nazwy, i rozbicie się nie zgodziło:

```
$ # atrybuty testowe w tests/**/*.cs, licznik po nazwie atrybutu
[TestMethod] w plikach:       706
[DataTestMethod] w plikach:    13
razem:                        719
objetych ksztaltem:           679
roznica:                       40
```

**`[DataTestMethod]` jest trzynaście, nie czterdzieści.** Pozostałe **27** to
zwyczajne `[TestMethod]` **bez** argumentów — czyli metody, które kształt bramki
obejmuje z definicji, a mimo to były poza nim. Rozbicie po plikach:

```
tests/Sim.Tests/ServiceDayTests.cs        16 atrybutow, widzianych  0
tests/Sim.Tests/SignallingPlanTests.cs    15 atrybutow, widzianych  4
tests/Sim.Tests/ValidationTests.cs        14 atrybutow, widzianych  9
tests/Sim.Tests/TrainControllerTests.cs    …, trzy metody poza
tests/Sim.Tests/BrakingTests.cs            …, cztery metody poza
tests/Sim.Tests/DesignModelAuditTests.cs   …, jedna metoda poza
```

`ServiceDayTests.cs` ma **szesnaście** metod testowych i bramka widziała z nich
**zero**. Meldowała przy tym „0 metod wygląda jak test i nie jest uruchamiane" —
bo nie miała czego zobaczyć. To jest ta sama wyrocznia zepsuta w stronę
„wszystko w porządku", którą ta rodzina pozycji zamyka od trzech dni, tylko tym
razem zepsuta była **bramka założona po to, żeby jej pilnować**.

## 2. Mechanizm: klamra w napisie brana za klamrę bloku

Przejście po ciele klasy liczyło klamry po **surowym** tekście. Pomocnicy testów
budują JSON, a JSON jest zbudowany z klamer:

```csharp
private static string Blok(string id, params (int Start, int End)[] windows) =>
    FormattableString.Invariant(
        $"{{\"block_id\":\"{id}\",\"trips\":{windows.Length},\"trip_windows\":[")
    + string.Join(",", windows.Select(w => …))
    + "]}";
```

Kształt, który to naprawdę topi, dał się wyodrębnić pomiarem do trzech wierszy:

```csharp
private static string Niesparowana()
{
    return "}";
}
```

Klamra otwierająca ciało metody podnosi licznik do 1; klamra **w napisie** zbija go
do 0, więc przejście uznaje ciało metody za skończone w środku napisu. Prawdziwą
klamrę zamykającą metody bierze potem za koniec ciała klasy i **przestaje szukać** —
wszystko za tym pomocnikiem staje się niewidzialne.

Naprawą jest `maska()`: kopia źródła, w której komentarze i literały są zamienione
na spacje **znak w znak**, więc indeksy i numery wierszy zostają te same. Struktura
chodzi po masce, wycinki bierze się z oryginału. Obsłużone są wszystkie cztery
postacie napisu, które w `tests/` występują — zwykła z ucieczkami, `@"..."` (gdzie
`""` jest cudzysłowem, a odwrotny ukośnik nie ucieka), `$"..."` (klamry interpolacji
zostają wewnątrz literału i w poprawnym C# są zbilansowane, więc pominięcie całego
literału jest bezpieczne) oraz surowa, otwierana trzema cudzysłowami.

Po naprawie samego liczenia klamr, przed dotknięciem kształtu:

```
[TESTY C#] atrybutow testowych w plikach: 719
[TESTY C#] objetych ksztaltem bramki:     706      (bylo 679)
[TESTY C#] poza ksztaltem:                 13      (bylo 40)
```

**Zostało dokładnie tyle, ile jest `[DataTestMethod]`** — czyli po naprawie luka jest
tą luką, którą wpis 6.B28 opisywał.

## 3. Rozszerzenie kształtu: obawa z 6.B27 zmierzona i nieziszczona

Wpis dawał dwie drogi: rozszerzyć kształt albo — jeżeli rozszerzenie łapie pomocników
z argumentami — dopisać drugie kryterium dla `[DataRow]`. Rozstrzygnięte pomiarem,
nie wyborem:

```
$ # publiczne metody void/Task Z ARGUMENTAMI na bezposrednim poziomie klasy [TestClass]
  z atrybutem testowym:  13
  BEZ atrybutu testowego:  0
$ # metody z [DataRow] bez [DataTestMethod]
  razem: 0
```

**Zero** fałszywych trafień. Pomocniki tego repozytorium są `private static` albo
`internal static` — `public void` w klasie testowej jest sygnałem, nie szumem.
Kształt jest więc rozszerzony, a nie obudowany drugim kryterium, i docstring modułu
został **przepisany**, nie uzupełniony: zdanie „szerszy kształt łapałby pomocników
z argumentami i skończyłby wyłączony" było uzasadnieniem, którego pomiar nie
potwierdza.

```
[TESTY C#] atrybutow testowych w plikach: 719
[TESTY C#] objetych ksztaltem bramki:     719
[TESTY C#] poza ksztaltem:                  0
[TESTY C#] wygladaja jak test, nie sa uruchamiane: 0
```

Kryterium „Skończone, gdy" tej pozycji brzmiało: liczba metod poza kształtem jest
zerem **albo** jest uzasadniona pomiarem. Jest zerem.

## 4. Sprostowanie dwóch liczb, które sam opublikowałem wczoraj i dziś

Przejście po ciele klasy jest wspólne dla dwóch czytników od 6.D30, więc obie
wcześniejsze publikacje liczb szły przez ten sam zepsuty licznik klamr:

| gdzie | liczba opublikowana | liczba dzisiejsza | co się stało |
|---|---|---|---|
| 6.B27 (#331) | 708 atrybutów, 668 objętych, 40 poza | 719 / 719 / 0 | 27 metod było niewidzialnych, nie „z argumentami" |
| 6.D28 (#341) | 674 metody z asercją, 674/674 | 719 / 719 | ten sam licznik, ta sama strata |
| 6.D30 (#344) | 676 i 676, „różnica zero" | 719 i 719 | **równość była prawdziwa** — oba czytniki gubiły to samo |

Trzeci wiersz jest najciekawszy i wart nazwania wprost: 6.D30 ściągnęła dwa
przejścia do jednego właśnie po to, żeby czytniki nie mogły się rozjechać — i to
zadziałało. Ale **równość dwóch czytników nie jest równością z drzewem**. Dwa
czytniki dzielące jedno zepsute przejście zgadzają się co do cyfry i mylą się razem;
test zgodności tego nie widzi i nie ma jak zobaczyć. Widzi to dopiero **próg na
liczbę** porównywalny z niezależnym licznikiem — tu z liczbą atrybutów w plikach.
Dlatego próg jest w tym commicie podniesiony w obu bramkach, z przepisanym
uzasadnieniem:

```
test_csharp_test_methods.py   MINIMUM_WIDZIANYCH  (nowy)   700   bylo: `> 100`
test_csharp_assertions.py     MINIMUM_METOD       700 <- 600
```

Stary próg `> 100` przechodził, gdy czytnik gubił 27 metod z 719. Próg, który nie
zauważa utraty jednej metody z dwudziestu pięciu, nie mierzy tego, co obiecuje.

## 5. Kontrole negatywne — WYKONANE, cztery

```
KN-1  liczenie klamr wraca na surowy tekst (maska zdjeta)
      FAIL test_a_brace_inside_a_string_is_not_a_block: test stojacy ZA pomocnikiem
           z klamra w napisie jest niewidzialny: []
      FAIL test_the_reader_actually_sees_the_tests: czytnik widzi 692 metod przy progu 700
      FAIL test_the_shape_covers_every_test_attribute: 27 atrybutow poza ksztaltem
      4/7 przeszlo

KN-2  ksztalt wraca do pustych nawiasow
      FAIL test_a_data_test_method_without_its_attribute_is_named: []
      FAIL test_the_shape_covers_every_test_attribute: 13 atrybutow poza ksztaltem
      5/7 przeszlo

KN-3  maska przestaje rozpoznawac literal surowy
      FAIL test_a_brace_inside_a_string_is_not_a_block
      6/7 przeszlo

KN-4  DataTestMethod zdjety z listy atrybutow testowych
      FAIL test_the_reader_actually_sees_the_tests
      FAIL test_the_shape_covers_every_test_attribute: -13 atrybutow poza ksztaltem
      5/7 przeszlo
```

**KN-1 wywrócił się dopiero na drugiej wersji testu, i to jest częścią pomiaru.**
Pierwsza wersja `test_a_brace_inside_a_string_is_not_a_block` używała pomocników
**wyrażeniowych** (`=> "{...}"`) — a tam klamry w napisie trafiają do licznika
nawiasów, który i tak kończy na średniku, więc test przechodził **także bez maski**.
Opisywał wtedy własną niewiedzę jako brak usterki: dokładnie to, co przy 6.D28
robił czytnik asercji, gdy nie znał ciał wyrażeniowych. Przepisany na kształt
blokowy, który KN-1 topi.

**KN-3 też wymagał poprawki, z tego samego powodu.** W pierwszej wersji zdjęcie
obsługi literału surowego nie łamało niczego: przy nieznanej postaci cudzysłowy
parują się przypadkiem tak, że wnętrze i tak zostaje zamaskowane. Treść, która to
topi, została **znaleziona pomiarem** — pięć kandydatów, z których dwa różnicują:

```
tresc w literale surowym      z obsluga    bez obslugi (KN-3)
{"a": {"b": 1}}               widzi test   widzi test      <- nie mierzy niczego
}                             widzi test   widzi test      <- nie mierzy niczego
"}                            widzi test   NIE widzi       <- to jest w tescie
" }                           widzi test   NIE widzi
{"x"}}                        widzi test   widzi test
```

W prawdziwym drzewie zdjęcie obsługi literału surowego **nie zmienia dziś nic**
(719 w obu wariantach) — pliki z `"""` mają treść, która paruje się szczęśliwie.
Obsługa zostaje, bo jest poprawna, a test daje jej zęby na wypadek, gdy szczęście
się skończy.

## 6. Weryfikacja

```
$ python3 tools/tests/csharp_test_methods.py
[TESTY C#] atrybutow testowych w plikach: 719
[TESTY C#] objetych ksztaltem bramki:     719
[TESTY C#] poza ksztaltem:                  0
[TESTY C#] wygladaja jak test, nie sa uruchamiane: 0

$ python3 tools/tests/csharp_assertions.py
[ASERCJE C#] metod testowych:        719
[ASERCJE C#] z asercja w tresci:     719
[ASERCJE C#] BEZ asercji w tresci:   0

$ python3 tools/tests/test_all.py
  RAZEM 69.749 s, 1830 testów, 97 modułów
kod: 0

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 557, Skipped: 0, Total: 557
```

1830 = 1828 + **2** (`test_csharp_test_methods.py` z 5 na 7 testów). Zestaw C# bez
zmiany — ta pozycja nie dotyka `src/` ani `tests/`, wyłącznie czytnika i jego bramki.
**Zero nowych metod C# zostało zgłoszonych jako nieuruchamiane** i to jest wynik,
nie brak wyniku: 27 metod, które bramka wreszcie zobaczyła, ma swoje atrybuty.

## 7. Czego świadomie nie zrobiono

- **Liczenia asercji nie ruszano** — pole „Poza zakresem" tej pozycji. Zrobiła to
  6.D28 osobno; tu zmienił się tylko jej **wynik**, bo dzieli czytnik, i to jest
  w §4 nazwane liczbą.
- **Nie tknięto `test_dead_constants_csharp.py`** ani innych bramek czytających C#
  własnym przejściem — sprawdzone, że nie korzystają z `czlonkowie`.
- **Nie dopisywano drugiego kryterium dla `[DataRow]`.** Wpis dawał je jako drogę
  awaryjną na wypadek fałszywych trafień; pomiar pokazał zero, więc kryterium byłoby
  martwym kodem.

## 8. Co zauważone przy okazji, nietknięte

- `coverage()` nazywał swoje pole „poza ksztaltem **(z argumentami)**" i ta nazwa
  była nieprawdą przez cały czas, gdy 27 z 40 nie miało z argumentami nic wspólnego.
  Etykieta poprawiona razem z liczbą; wspominam, bo **etykieta też jest wyrocznią** —
  czytający wierzy jej dokładnie tak samo jak liczbie.
- `maska()` jest gotowa do użycia przez każdą przyszłą bramkę czytającą C# jako
  tekst. Żadnej takiej dziś nie ma poza dwiema opisanymi, więc nic więcej nie
  przepisywałem.
