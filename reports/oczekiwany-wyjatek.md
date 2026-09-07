# Test oczekujący wyjątku może polec, gdy wyjątku nie ma (6.B33)

**Zmierzone 07.09.2026 na commicie:** `24678a78b5ce0a130638cf6b8d4a116670781c0f`
(gałąź `claude/6b33-oczekiwany-wyjatek`).

## 1. O co chodzi — cała wyrocznia stoi w jednym wierszu za blokiem

```csharp
try { InputLog.Parse("wersja=1\nkrok;klawisze\n0;W\n"); }
catch (FormatException error) { StringAssert.Contains(error.Message, "kroki"); return; }

Assert.Fail("zapis bez liczby kroków został przyjęty — odtworzenie nie wiedziałoby, kiedy skończyć");
```

Gdy kod przestanie rzucać, `catch` nie jest wchodzony, jego asercje nie wykonują się
**wcale**, a wykonanie dochodzi do `Assert.Fail` i test pada. Bez tego jednego wiersza
test przechodzi w milczeniu za każdym razem, gdy odmowa zniknie z kodu.

**Stan wyjściowy: czysty.** Dwanaście metod używa tego wzorca i **wszystkie dwanaście**
mają `Assert.Fail` na właściwym miejscu. Ta pozycja niczego więc nie naprawia — stawia
strażnika, żeby trzynasta bez niego nie przeszła. To ta sama klasa co 6.B27, gdzie
objawem brakującego `[TestMethod]` była wyłącznie liczba testów.

## 2. Pułapka, na którą wpadł mój pierwszy detektor — i dlaczego jest w docstringu

Pierwsza wersja szukała `Assert.Fail` **wewnątrz** bloku `try` i zgłosiła **wszystkie
dwanaście** jako usterkę:

```
try/catch w metodach testowych — z Assert.Fail w try:  0
try/catch BEZ Assert.Fail w try:                      12
    DriverNotchTests.UninitialisedStepIsRefused
    InputLogTests.MissingStepCountIsRefused
    … (dwanascie nazw)
```

**Zero z nich nią było.** Przeczytałem dwie z listy przed opublikowaniem liczby i wtedy
wyszło, że `Assert.Fail` stoi **za** `catch`, nie w `try` — czyli wzorzec jest
poprawny, a mój detektor patrzył w złe miejsce. Bramka zbudowana na tym odruchu
zapaliłaby się na dwunastu poprawnych testach i skończyłaby wyłączona (6.D27).

Jest to **siódma dziś sytuacja**, w której liczba wzięta z dopasowania tekstu okazała
się fałszywa, i pierwsza, w której zdążyłem ją zatrzymać przed wpisaniem do kolejki
jako „usterka".

KN-2 niżej odtwarza tę pomyłkę **jako wykonaną kontrolę**, więc pułapka nie jest
opisana z pamięci.

## 3. Czego bramka nie łapie — zmierzone, nie założone

```
wystapien `try` w metodach testowych:                      22
  z `catch` POCHLANIAJACYM wyjatek (ten wzorzec):          12
  `try`/`finally` BEZ `catch` (sprzatanie plikow):         10
```

Dziesięć bloków `try`/`finally` bez `catch` to sprzątanie plików tymczasowych
(`finally { File.Delete(...) }`). **Wyjątek tam nie ginie** — leci dalej i wywala test
głośno — więc żądanie od nich `Assert.Fail` byłoby bramką zapalającą się na poprawnym
kodzie. Bramka kluczuje na `catch` **pochłaniającym** wyjątek, nie na obecności `try`;
`catch` z `throw;` też nie jest tym wzorcem. Oba wyłączenia mają swój test na
wstrzykniętym wejściu.

## 4. Bramka pisana po to, żeby łapać cichy fałszywy negatyw, sama go miała

Najważniejsza rzecz w tej pozycji nie wyszła z pomiaru drzewa, tylko z **kontroli
negatywnej na własnej bramce**. KN-1 podmienił prawdziwe `Assert.Fail(...)`
w `InputLogTests.cs` na komentarz:

```
        // KN-1: Assert.Fail zdjety
```

i bramka została **zielona, 6/6**. Powód: warunek szukał podciągu `Assert.Fail`
w surowym tekście, a podciąg nadal był w pliku — w komentarzu. Czyli bramka postawiona
po to, żeby żaden test nie przechodził w milczeniu, sama przepuszczała test, któremu
zdjęto wyrocznię, jeżeli tylko zdjęcie zostawiło po sobie komentarz. A ten projekt
zdejmując coś, **zwykle zostawia komentarz** — reguła „przepisuj, nie dopisuj obok".

Poprawka: `Assert.Fail` szukane na **masce** (`CTM.maska` z 6.B28), gdzie komentarze
i literały są spacjami. Doszedł test na dokładnie ten przypadek. Po poprawce KN-1
wywraca bramkę w **obu** wariantach: gdy `Assert.Fail` jest zakomentowane i gdy jest
usunięte w całości.

To jest ta sama usterka, którą wpis **6.B34** opisuje dla bramki martwych stałych —
tylko że tam daje fałszywy negatyw w bramce liczącej odczyty, a tu dawała go w bramce
liczącej wyrocznie.

## 5. Kontrole negatywne — WYKONANE, pięć

```
KN-1a prawdziwy Assert.Fail podmieniony na KOMENTARZ (InputLogTests)
      FAIL test_every_expected_exception_test_can_fail_when_nothing_throws
      6/7 przeszlo
      PRZED poprawka z §4: 6/6 przeszlo — bramka byla ZIELONA

KN-1b prawdziwy Assert.Fail usuniety calkiem
      FAIL test_every_expected_exception_test_can_fail_when_nothing_throws
      6/7 przeszlo

KN-2  detektor szuka Assert.Fail WEWNATRZ try (moja pierwotna pomylka)
      FAIL test_every_expected_exception_test_can_fail_when_nothing_throws
      FAIL test_the_detector_lights_up_on_a_test_without_assert_fail
      4/6 przeszlo

KN-3  literowka we wzorcu klauzuli (`catchh`)
      FAIL test_the_gate_sees_the_pattern_it_is_supposed_to_see: wzorzec rozpoznany
           0 razy przy progu 12
      FAIL test_the_detector_lights_up_on_a_test_without_assert_fail
      FAIL test_the_detector_is_not_fooled_by_a_brace_in_a_string
      3/6 przeszlo

KN-4  warunek na `throw` zdjety (catch z `throw;` liczony jako pochlaniajacy)
      FAIL test_a_rethrowing_catch_is_not_the_pattern
      5/6 przeszlo
```

**KN-3 pokazuje, po co jest próg.** Bez niego literówka we wzorcu dawałaby zero
znalezisk i zieloną bramkę mierzącą nic — a przy „zero usterek" jako stanie
oczekiwanym jest to jedyna rzecz, która odróżnia bramkę działającą od milczącej.

## 6. Weryfikacja

```
$ python3 tools/tests/test_expected_exception.py
  ok   test_a_commented_out_assert_fail_does_not_count
  ok   test_a_rethrowing_catch_is_not_the_pattern
  ok   test_a_try_finally_without_catch_is_not_the_pattern
  ok   test_every_expected_exception_test_can_fail_when_nothing_throws
  ok   test_the_detector_is_not_fooled_by_a_brace_in_a_string
  ok   test_the_detector_lights_up_on_a_test_without_assert_fail
  ok   test_the_gate_sees_the_pattern_it_is_supposed_to_see
  7/7 przeszło

$ python3 tools/tests/test_all.py
  RAZEM 71.483 s, 1851 testów, 99 modułów
```

1851 = 1844 + **7**, modułów 98 → **99**. Zestawy C# nietknięte — ta pozycja nie
dopisuje ani nie zmienia żadnego testu C#, tylko go czyta.

## 7. Czego świadomie nie zrobiono

- **Nie przepisano dwunastu testów na `Assert.ThrowsException`** — pole „Poza
  zakresem". Wszystkie dwanaście są dziś poprawne; przepisanie ich byłoby zmianą
  kształtu poprawnego kodu, a nie postawieniem strażnika.
- **Nie tknięto `catch` z ponownym rzuceniem** — tam wyjątek nie ginie, więc nie ma
  czego pilnować, i ma to swój test.
- **Nie zmieniono ani jednego pliku w `tests/`** — `git status` po wszystkich pięciu
  kontrolach pokazuje wyłącznie nowy moduł bramki.

## 8. Co zauważone przy okazji, nietknięte

- **`CTM.maska` przydała się drugi raz w ciągu godziny** i za każdym razem w innej
  bramce. Powstała przy 6.B28 dla przejścia po ciele klasy, a tutaj załatwiła zupełnie
  inny problem: odróżnienie wywołania od wzmianki. Zapisuję to, bo przy 6.B34 stoi
  wpis żądający tego samego dla bramki martwych stałych, a to już trzecie miejsce.
