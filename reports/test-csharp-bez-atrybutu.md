# Metoda, która wygląda jak test C# i nie jest uruchamiana (6.B27)

**Zmierzone 06.09.2026 na commicie:** `239345d344919278976278bdb74833ecbcc06f8c`

## 1. Skąd ta pozycja

Z mojego własnego commitu przy 6.A16 (#327). Przepisując komentarz nad testem, atrybut
`[TestMethod]` został wycięty razem z nim. Metoda została w pliku, miała asercje,
wyglądała jak test — i nie była uruchamiana. Zestaw C# przeszedł **545/545 mimo
obecnego błędu**.

Objawem nie był żaden `FAIL`. Objawem była **liczba** — 545 zamiast 546 — i to, że
mutacja, która miała wywrócić test, nie wywróciła niczego. Zestaw Pythona ma na to
`assertion_gate` od #139; po stronie C# nie było nic.

## 2. Kształt, na którym stoi bramka

Publiczna metoda `void`/`Task` **bez argumentów**, zadeklarowana **bezpośrednio**
w klasie z `[TestClass]`. Taka jest metoda testowa w tym repozytorium i taka była ta,
która straciła atrybut.

Kształt jest wąski **celowo**. Szerszy — „każda publiczna metoda" — łapałby pomocników
z argumentami i skończyłby wyłączony, a bramka wyłączona nie jest bramką.

Głębokość ma znaczenie i jest liczona klamrami: `Reset()` w zagnieżdżonym przyrządzie
`tests/Game.Tests/RunResetTests.cs` jest publiczną, bezargumentową metodą `void`
i **nie jest testem**. Osobny test pilnuje, żeby bramka go nie zgłaszała — inaczej
zapalałaby się przy każdym przebiegu i skończyła wyłączona.

## 3. Pokrycie — nazwane liczbą, nie komentarzem

```
[TESTY C#] atrybutow testowych w plikach: 708
[TESTY C#] objetych ksztaltem bramki:     668
[TESTY C#] poza ksztaltem (z argumentami): 40
[TESTY C#] wygladaja jak test, nie sa uruchamiane: 0
```

**Czterdzieści metod jest poza kształtem** — to `[DataTestMethod]` z wierszami
`[DataRow]`, czyli metody z argumentami. Bramka ich nie sprawdza i mówi to liczbą,
którą wypisuje przy każdym przebiegu. Osobny test pilnuje, że ta liczba jest liczona,
a nie przepisana; luka opisana samym komentarzem po roku nie ma rozmiaru. Domknięcie
tej luki dopisane do kolejki jako **6.B28**.

## 4. Kontrola negatywna — wykonana

Zdjęty `[TestMethod]` z istniejącego testu, tego samego, który stracił go naprawdę:

```
[TESTY C#] atrybutow testowych w plikach: 707
[TESTY C#] objetych ksztaltem bramki:     667
[TESTY C#] wygladaja jak test, nie sa uruchamiane: 1
   BRAK [TestMethod]: tests/Sim.Tests/RunnerCommandTests.cs ::
   RunnerCommandTests.Compare_bez_dwoch_plikow_konczy_sie_kodem_jeden
kod skryptu: 1

FAIL test_no_method_looks_like_a_test_and_is_not_run: metody o ksztalcie testu bez
[TestMethod] — nie sa uruchamiane: tests/Sim.Tests/RunnerCommandTests.cs ::
RunnerCommandTests.Compare_bez_dwoch_plikow_konczy_sie_kodem_jeden
```

Bramka **nazywa test z imienia**, tak jak żąda pole „Skończone, gdy". Plik przywrócony;
`git status` po kontroli pokazuje wyłącznie dwa nowe pliki tej pozycji.

Do kontroli dochodzi druga, wstrzykiwana w katalogu tymczasowym: klasa z dwiema
metodami, jedną z atrybutem i jedną bez — czytnik ma widzieć obie i zgłosić dokładnie
tę drugą.

## 5. Weryfikacja

```
python3 tools/tests/test_all.py  ->  1782/1782 przeszło, kod wyjścia 0
```

Bramka nie potrzebuje `dotnet`: czyta pliki jako tekst.

## 6. Poza zakresem

**Liczenie asercji w testach C#** — to jest osobna, znacznie większa praca niż wykrycie
brakującego atrybutu i wymagałaby rozbioru składni C#, a nie czytania tekstu.
Dopisywanie brakujących testów. Zmiana czegokolwiek w `tests/`.
