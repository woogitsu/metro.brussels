# Jedno przejście po ciele klasy C#, i równość zamiast pasma (6.D30)

**Zmierzone 07.09.2026 na commicie:** `e0e65f903d3339b49d4b1aa41d90b7bdc2d4bb17`
(gałąź `claude/6d30-jeden-czytnik-csharp`).

## 1. Co było zepsute — i sprostowanie własnego wpisu

Wpis 6.D30 mówił, że dwa czytniki C# „**już raz podały różne liczby** (670 vs 674)".
To zdanie jest **mylące i pochodzi ode mnie**, więc naprawiam je tutaj, zanim naprawię
kod: tamte 670 wyszło pod **celową mutacją** w kontroli negatywnej KN-2 przy 6.D28, gdy
odebrałem nowszemu czytnikowi znajomość ciała wyrażeniowego. W normalnej pracy czytniki
**nigdy się nie rozjechały** — zmierzone dziś, przed jakąkolwiek zmianą:

```
csharp_test_methods.metody() z atrybutem: 676
csharp_assertions.metody_testowe():       676
```

Różnica **zero**. Zepsute było zatem coś innego i trzeba to nazwać dokładnie:

1. **Dwa przejścia po tym samym drzewie.** `_poziom_bezposredni` **wycinało** wnętrza
   klamr — poprawnie dla wykrywania brakującego `[TestMethod]` (6.B27), bezużytecznie
   dla liczenia asercji (6.D28), bo asercja siedzi właśnie w tym wnętrzu. Dlatego 6.D28
   dopisała drugie, obok pierwszego.
2. **Pasmo zamiast równości.** Test zgodności żądał `nowy - stary <= 20`. Postawiłem
   to pasmo nie dlatego, że 20 cokolwiek znaczyło, ale dlatego, że **mając dwa osobne
   rozbiory nie umiałem postawić równości**. Prawdziwa różnica była 0. Pasmo nie
   opisywało żadnego rozjazdu — opisywało moją niepewność co do własnego kodu.

## 2. Co zrobione

Przejście `czlonkowie()` (to nowsze, znające **oba** kształty ciała: blok `{…}`
i wyrażenie `=> …;`) zostało **ściągnięte do `csharp_test_methods`** — modułu niższego —
a starsze `_poziom_bezposredni` skasowane. Kierunek zależności jest jednokierunkowy:
`csharp_assertions` importuje z `csharp_test_methods`, nie odwrotnie, więc przeniesienie
w drugą stronę zrobiłoby cykl.

`metody()` liczy się teraz na tym samym przejściu i daje **te same liczby**:

```
z atrybutem: 676
coverage:    {'atrybuty_w_plikach': 716, 'objete_ksztaltem': 676, 'poza_ksztaltem': 40}
bez atrybutu: []
```

Test zgodności żąda **równości**, nie pasma.

## 3. Dlaczego równość nie wystarcza, i co doszło obok

Równość byłaby prawdziwa **także przy dwóch przejściach**, które akurat zgadzają się na
dzisiejszym drzewie — dokładnie tak było przy 6.D28. Doszedł więc drugi test, patrzący
na **kod**, nie na liczby: `czlonkowie` ma być zdefiniowane w jednym module, drugi ma je
**wołać, nie kopiować**, a `_poziom_bezposredni` nie ma wrócić.

Ten test też potrzebował poprawki, i tej samej co dwa razy wcześniej dzisiaj: pierwsza
wersja zabraniała **nazwy** `_poziom_bezposredni` w całym pliku i zapaliła się na
komentarzu, który **wyjaśnia, dlaczego to przejście zniknęło**. Wzmianka nie jest
powrotem. Warunek dotyczy teraz `def _poziom_bezposredni(` — ta sama różnica, którą
6.D27 postawiło między twierdzeniem a odsyłaczem, i ten sam wniosek: bramka świecąca na
poprawnym tekście zostaje wyłączona, nie poprawiona.

## 4. Kontrole negatywne — WYKONANE, trzy

```
KN-1  drugie przejscie wraca do csharp_assertions.py (kopia + wolanie lokalne)
      FAIL test_there_is_only_one_traversal_of_a_class_body: drugie przejscie wrocilo
      do csharp_assertions.py; 6.D30 sciagnela je do csharp_test_methods wlasnie po to,
      zeby bylo jedno

KN-2  starsze przejscie przywrocone jako DEFINICJA
      FAIL test_there_is_only_one_traversal_of_a_class_body: starsze przejscie
      wrocilo — ... jego definicja znaczy, ze znowu sa dwa

KN-3  czytniki rozjezdzaja sie o SZESC metod (nowszy pomija testy „Bilans*")
      FAIL test_both_readers_agree_exactly_on_how_many_methods_carry_a_test_attribute:
      czytniki podaja rozne liczby metod z atrybutem: 670 vs 676
```

**KN-3 mierzy wartość całej pozycji.** Różnica sześciu metod (670 vs 676) leży
**wewnątrz** starego pasma `<= 20`, więc test z 6.D28 przepuściłby ją **bez słowa** —
i przepuściłby jeszcze czternaście takich metod. Równość łapie pierwszą.

## 5. Weryfikacja

```
$ python3 tools/tests/test_csharp_assertions.py
  8/8 przeszło
kod: 0

$ python3 tools/tests/test_all.py
  RAZEM 68.128 s, 1828 testów, 97 modułów
kod: 0
```

Liczba testów rośnie o **1** (1827 → 1828): jeden test przepisany (pasmo → równość) i
jeden dopisany (jedno przejście). `dotnet test` nietknięty, bo ta pozycja nie dotyka
ani jednego pliku `.cs` — zmienia tylko to, czym się je czyta.

## 6. Czego świadomie nie zrobiono

- **Nie objęto metod z argumentami.** To 6.B28 (40 metod `[DataTestMethod]` poza
  kształtem, `poza_ksztaltem: 40` w wypisie wyżej) i wejście w nią tutaj zmieniłoby
  dwie rzeczy naraz.
- **Nie sięgnięto po bibliotekę do rozbioru C#** — pole „Poza zakresem". To zmiana
  zależności (`CLAUDE.md` §8); oba narzędzia stoją na czytaniu tekstu ze świadomością
  głębokości klamer i takie zostają.
- **Nie tknięto `KLASA` ani `METODA`.** Wzorce były już wspólne — importowane
  z modułu niższego. Rozjazd groził tylko na przejściu, i tylko ono się zmieniło.
