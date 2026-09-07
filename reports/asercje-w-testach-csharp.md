# Asercje w testach C# (6.D28)

**Zmierzone 07.09.2026 na commicie:** `d47c582fd519a27c2738221feaa62efa0c926e15`
(gałąź `claude/6d28-asercje-csharp`).

## 1. Po co

Zestaw Pythona ma `assertion_gate` od #139: test, który przeszedł **bez ani jednej
asercji**, jest tam awarią, nie sukcesem. Ta bramka zadziałała 07.09.2026 **dwa razy**
— przy 6.D26, na moim własnym teście, który po zawężeniu zakresu skanowania przestał
cokolwiek sprawdzać:

```
FAIL test_the_prose_does_not_quote_a_margin_that_the_numbers_do_not_give:
przeszedł bez wykonania ani jednej asercji — cichy skip zamiast testu
```

To był **jedyny ślad**, że przestał: kod wyjścia był poprawny, liczba testów bez
zmian, żaden inny test nie padł. Po stronie C# takiego śladu nie było — 2289 wywołań
`Assert` w 124 plikach i zero nadzoru.

## 2. Pomiar

```
[ASERCJE C#] metod testowych:        674
[ASERCJE C#] z asercja w tresci:     674
[ASERCJE C#] BEZ asercji w tresci:     0
```

Zero — ale dojście do tego zera wymagało **dwóch poprawek w czytniku**, i obie mówią
więcej niż sam wynik.

## 3. Pierwsza poprawka: czytnik zgłaszał własną niewiedzę jako brak

Ciało metody C# ma **dwie** postacie: blok `{ ... }` i ciało wyrazeniowe `=> …;`.
Pierwsza wersja czytnika znała tylko blok i zgłosiła jedną metodę „bez asercji":

```
tests/Sim.Tests/TrainProtectionTests.cs:570:
    public void Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB() =>
        CollectionAssert.AreEqual(
            new[] { KcvFunction.SecureAutomaticDoorOpening, … },
            TrainProtection.SourceBackedKcvFunctions.ToArray());
```

Ona **asertuje**. Co więcej, gorzej: przy tym kształcie klamra inicjatora tablicy
(`new[] { … }`) była brana za początek bloku metody, więc `CollectionAssert.AreEqual`
zostawało w „nagłówku", nie w „ciele" — i czytnik nie widział go po prostu nigdzie.

**Czytnik, który jednej z tych postaci nie zna, nie zgłasza braku asercji: zgłasza
własną niewiedzę jako brak.** To ta sama klasa błędu, którą łapałem dzisiaj cztery
razy w liczbach z grepa — tylko po stronie C# i o jeden poziom głębiej.

## 4. Druga poprawka: pomocnik `Assert*` to asercja

Przy samych wywołaniach `Assert.`/`StringAssert.`/`CollectionAssert.` wychodziło
**pięć** metod bez asercji. Cztery z nich asertują przez lokalny pomocnik:

```
tests/Sim.Tests/BrakingTests.cs:42:
        AssertBits(BrakingReference.CeilingDryAllAxlesMps2,
                   AllAxles.MaxDecelerationMps2(Model.DesignAdhesionDry));
```

Rozszerzenie na pomocników o nazwie zaczynającej się od `Assert` zbija pięć do jednej
(tej z §3). Bez tej reguły bramka świeciłaby na **poprawnym kodzie** — a taka bramka
zostaje wyłączona, nie poprawiona (6.D27).

Sprawdzone też rozwiązywanie pomocników **po ciele**, nie po nazwie: budowanie mapy
„pomocnik → czy jego ciało asertuje" i uznawanie wywołania takiego pomocnika za
asercję. **Nie daje ani jednej metody więcej** niż prosta reguła na `Assert*`:

```
bezposrednia             metod=671  bez asercji=5
z pomocnikami Assert*    metod=671  bez asercji=1
z pomocnikami klasy      metod=671  bez asercji=1
```

Zostaje reguła prostsza — bo droższa nie kupuje ani jednego trafienia, a nie chcę
utrzymywać mechanizmu, który na tym drzewie nie robi nic.

## 5. Granica postawiona świadomie

Ta bramka liczy asercje **obecne w treści** metody, nie **wykonane** w czasie
przebiegu. `assertion_gate` po stronie Pythona robi to drugie, przez instrumentację
AST — i dlatego złapał mój test z §1, który miał asercję w pętli, do której nic nie
weszło. Test C# z asercją w gałęzi nigdy nie wchodzonej przejdzie tu za asertujący.

To jest **słabsza** własność i pole „Poza zakresem" pozycji 6.D28 mówi o tym wprost:
liczenie wykonanych wymagałoby rozbioru składni C# albo wpięcia w runner testów, czyli
innej i znacznie większej pracy. Słabsza własność sprawdzana jest jednak lepsza od
żadnej, a granica jest zapisana w docstringu narzędzia, nie przemilczana.

## 6. Kontrole negatywne — WYKONANE, cztery, każda na innym trybie awarii

```
KN-1  asercja zdjeta z ISTNIEJACEGO testu (cialo wyrazeniowe)
      FAIL ..._has_an_assertion_in_its_body: tests/Sim.Tests/TrainProtectionTests.cs
      :: TrainProtectionTests.Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB

KN-2  czytnik przestaje znac cialo wyrazeniowe
      FAIL ..._both_readers_agree_on_how_many_methods...: nowy czytnik widzi MNIEJ
      metod (670) niz starszy (674) — zna cialo wyrazeniowe, wiec nie ma prawa
      FAIL ..._sees_both_shapes_of_a_method_body: {'Blokiem': True}

KN-3  pomocnik Assert* przestaje sie liczyc
      FAIL ..._a_helper_whose_name_starts_with_assert...: {'PrzezPomocnika': False}
      FAIL ..._has_an_assertion_in_its_body: cztery metody z BrakingTests i DeterminismTests

KN-4  czytnik uznaje KAZDA metode za asertujaca
      FAIL ..._a_test_method_without_any_assertion_is_reported: [... 'NicNieSprawdza', True]
```

**KN-4 jest tą, której brak byłby najgroźniejszy.** Drzewo ma dziś **zero** braków,
więc bramka „zero braków" jest zielona zarówno wtedy, gdy czytnik działa, jak i wtedy,
gdy uznaje za asertującą każdą metodę. Kontrola pozytywna na syntetycznej metodzie bez
asercji chodzi przy **każdym** przebiegu i to ona odróżnia jedno od drugiego.

**KN-2 pokazuje przy okazji, po co jest test na zgodność dwóch czytników**: różnica
670 vs 674 wyszła sama, bez oglądania kodu.

## 7. Weryfikacja

```
$ python3 tools/tests/csharp_assertions.py
[ASERCJE C#] metod testowych:        674
[ASERCJE C#] z asercja w tresci:     674
[ASERCJE C#] BEZ asercji w tresci:     0
kod: 0

$ python3 tools/tests/test_all.py
  RAZEM 65.216 s, 1827 testów, 97 modułów
kod: 0
```

Bramka kosztuje **0,50 s** — i to jest liczba, na którą patrzyłem od 6.B31, gdzie
pierwsza wersja czytnika C# kosztowała 20,7 s.

Liczba 674 zgadza się z pomiarem 6.B27 (#329): tamten policzył **708** atrybutów
testowych i **668** objętych kształtem „metoda bez argumentów". Ten czytnik widzi
674, bo zna dodatkowo ciało wyrazeniowe; pozostałe **34** to metody Z ARGUMENTAMI,
czyli `[DataTestMethod]` z wierszami `[DataRow]` — i to jest osobna pozycja **6.B28**,
nietknięta tutaj. Osobny test pilnuje, żeby ta różnica nie rozjechała się dowolnie.

## 8. Czego świadomie nie zrobiono

- **Liczenia asercji wykonanych** — §5, pole „Poza zakresem".
- **Nie tknięto 34 metod z argumentami** (`[DataTestMethod]`). To 6.B28, a wejście
  w nią tutaj zmieniłoby dwie rzeczy naraz i żadnej nie dałoby się zmierzyć osobno.
- **Nie dopisano ani jednej asercji do ani jednego testu.** Nie było czego dopisywać —
  i to jest wynik, nie zaniedbanie.
- **Nie objęto `Assert.Throws`-podobnych wyrażeń osobną regułą**: `Assert.ThrowsException`
  zaczyna się od `Assert.`, więc wpada pod regułę bezpośrednią bez żadnego dopisku.

  Pierwsza wersja tego punktu twierdziła dalej, że „nie ma na tym drzewie testu, który
  sprawdzałby wyjątek inaczej niż przez `Assert.`" — **i to było twierdzenie ponad
  pomiar**. Sprawdzone: dwa pliki (`DriverNotchTests.cs`, `InputLogTests.cs`) używają
  `try`/`catch` bez `Assert.Throws`. Oba **asertują wewnątrz `catch`**:

  ```
  tests/Sim.Tests/DriverNotchTests.cs:261:
          catch (ArgumentException)
          {
              Assert.AreEqual(0.0, notch.Command.Throttle, 0.0);
              return;
          }
  ```

  Dla tej bramki nie ma to znaczenia, bo asercja jest w treści metody — ale zdanie,
  które napisałem, mówiło o czymś, czego nie zmierzyłem, i dlatego jest tu poprawione
  zamiast usunięte. Warto przy tym zauważyć, czego ta bramka o takim teście **nie
  wie**: gdyby wyjątek przestał lecieć, `catch` by nie wszedł, asercja by się nie
  wykonała, a bramka nadal widziałaby ją w tekście. To dokładnie ta granica z §5.
