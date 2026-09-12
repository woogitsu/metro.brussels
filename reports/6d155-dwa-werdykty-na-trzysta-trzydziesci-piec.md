# 6.D155 — jednostki kaleczą 335 literałów, a werdykt zmieniają DWÓM; w drugą stronę zero i to nie przypadek

**12.09.2026**, na `b0dc078`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(`Jednostki`, `BezJednostek`, `SlowaWKodzie`), `reports/6d142-bezczynny-wyjatek.md`,
korpus `src/Game/` (21 plików, 480 literałów).

Pozycja żądała **dwóch liczb** — ile literałów przechodzi sito słowa wyłącznie dzięki
zjedzonej literze i ile w kierunku odwrotnym — oraz odpowiedzi, **czy któraś dotyczy
tekstu dla gracza**. Pole „Dlaczego to nie jest poprawka" mówiło wprost: *najpierw
policzyć, a dopiero liczba rozstrzyga, czy warto.*

## 1. GŁÓWNY WYNIK

```
LITERALOW_DOTKNIETYCH_ZDEJMOWANIEM=335
SLOWO_ZNIKA_PRZEZ_ZDEJMOWANIE=2
SLOWO_POJAWIA_SIE_PRZEZ_ZDEJMOWANIE=0
```

| liczba | co znaczy |
|---|---|
| **335** z 480 | literałów, których TEKST zdejmowanie zmienia — zasięg mechaniki, 70 % korpusu |
| **2** | literały, którym zdejmowanie **zabiera** werdykt „to słowo" |
| **0** | literały, którym zdejmowanie werdykt **daje** |

**Mechanika kaleczy szeroko, a rozstrzyga wąsko.** Okaleczenia są spektakularne —

```
streaming            ->   trea ing
name                 ->  na e
collision_radius_m   ->  colli ion_radiu _
axis_length_m        ->  axi _length_
zasięg streamowania  ->  za ięg  trea owania
```

— ale bramka nie pyta „czy tekst jest całe", tylko „czy zostały **dwie litery pod
rząd**". Na to okaleczenie prawie nigdy nie wpływa: `streaming` traci `s`, a `trea ing`
wciąż ma dwie litery pod rząd i werdykt jest ten sam. Pytanie pozycji brzmiało
o WERDYKTY, i werdyktów jest **dwa**.

## 2. Które to dwa — i tak, jeden z nich to tekst dla gracza

| literał | plik | dlaczego traci werdykt | co to znaczy |
|---|---|---|---|
| `Esc` | `KeyNames.cs` | jednostka `s` zjada środkową literę → `E c` | przypadek, **na którym stoi rozstrzygnięcie 6.D142** |
| `{speedKmh,6:F1} km/h     a = {accelerationMps2,6:F2} m/s²` | `Hud.cs` | po zdjęciu dziur zostaje ` km/h     a =  m/s²`, a po zdjęciu jednostek — **sama litera `a`** | **wiersz prędkości HUD-u, widziany przez gracza** |

Odpowiedź na pytanie z pola „Skończone, gdy" brzmi więc **TAK** — i jest w bramce
**wykonana, a nie napisana**: test sprawdza, że drugi z dwóch literałów stoi w ciele
`Hud.Update`, czyli na drodze prześledzonej wczoraj przez 6.D183.

### 2.1. Ale milczenie bramki na tym wierszu jest POPRAWNE

Kuszące jest przeczytać „tekst dla gracza, o którym bramka milczy" jako usterkę.
**Nie jest.** Po zdjęciu dziur interpolacji i jednostek zostaje w tym wierszu
**jedna litera — `a`, symbol przyspieszenia** — plus znak równości i spacje. Nie ma
tam ani jednego słowa językowego: są jednostki (`km/h`, `m/s²`), formaty liczb
(`F1`, `F2`) i symbol wielkości fizycznej.

A to jest **dokładnie to, co pole „Skończone, gdy" pozycji 6.D83 kazało zostawić
w kodzie** („jednostki i formaty liczb zostają") i dokładnie powód, dla którego
6.D115 zdejmowanie jednostek w ogóle wprowadziło. Bramka milczy nie **mimo** tej
mechaniki, tylko **dzięki** niej, i milczy słusznie.

Test przybija **co** zostaje (`"a"`), a nie „czy zostaje słowo" — to drugie wynikałoby
z samego członkostwa w liście dwóch i byłoby zdaniem o sobie samym.

## 3. Zero w drugą stronę NIE JEST przypadkiem dzisiejszego drzewa

Liczba `0` policzona z drzewa mówi tylko, że dziś się nie trafiło. Mechanizm mówi
więcej: **`BezJednostek` podstawia SPACJĘ, a spacja rozdziela litery.** Pary liter,
której nie było, utworzyć nie umie — więc zbiór „przechodzi po zdjęciu" jest
**podzbiorem** zbioru „przechodzi przed zdjęciem", zawsze, nie tylko dzisiaj.

Wykonane na wejściu syntetycznym, w obie strony:

```csharp
BezJednostek("akmb")            ==  "a b"     // spacja, nie pusty napis
JestSlowo("akmb", zdejmuj: false) == true     // przed zdjęciem: słowo
JestSlowo("akmb", zdejmuj: true)  == false    // po zdjęciu: nie
```

Trzecia asercja jest tu konieczna: bez niej `IsFalse` przechodziłby także wtedy,
gdyby wejście nie było słowem od początku — czyli byłby zgodnością dwóch zer.

**KN-1 mierzy tę granicę wprost**: podstawienie pustego napisu zamiast spacji sprawia,
że `akmb` → `ab`, czyli sito **tworzy** parę liter, i kierunek podany jako niemożliwy
staje się możliwy. Test zapala się natychmiast.

## 4. ROZSTRZYGNIĘCIE: nie warto zmieniać `BezJednostek` — i to jest wynik pomiaru

Pole „Dlaczego to nie jest poprawka" ostrzegało, że zmiana na zdejmowanie **warunkowe**
uczyniłaby wyjątek `NazwyKlawiszy` działającym i wymagałaby przeczytania decyzji 6.D142
od nowa. Liczba mówi, ile by się za to kupiło:

- **Fałszywych werdyktów nie ma ani jednego.** Oba dotknięte są poprawne: `Esc` ma
  być odrzucony (to napis wytłoczony na klawiszu), wiersz prędkości ma milczeć
  (nie ma w nim słowa).
- **335 okaleczonych tekstów nie zmienia ani jednego werdyktu.** Brzydota nie jest
  kosztem, dopóki nikt tych napisów nie czyta — a nikt nie czyta: `BezJednostek`
  karmi wyłącznie `Regex.IsMatch`.
- **Kierunek fałszywie-dodatni jest zamknięty mechanicznie**, a nie tylko pusty dzisiaj.

Zmiana kosztowałaby więc otwarcie zamkniętej decyzji i nie naprawiłaby niczego.
**Bramka nie dostaje ani jednej linijki nowego sita** — dostaje trzy liczby przybite
z drzewa, żeby to rozstrzygnięcie nie zgniło po cichu, gdy korpus się zmieni.

## 5. Kontrole negatywne — cztery, wszystkie czerwone

Baza: **247/247**. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | zdejmowanie podstawia PUSTY napis zamiast spacji | **244/247** — 3 czerwone |
| KN-2 | `JestSlowo` ignoruje flagę (obie strony liczone tak samo) | **245/247** |
| KN-3 | jednostka `s` zdjęta z `Jednostki` | **244/247** — 3 czerwone |
| KN-4 | powiązanie z 6.D183 wskazuje inny człon `Hud.cs` | **246/247** |

KN-1 i KN-3 zapalają też `Wyjatek_na_Esc_jest_BEZCZYNNY_a_mechanizm_jest_OSIAGALNY`,
czyli bramkę z 6.D142 — co jest **dowodem wykonanym**, że obie pozycje stoją na tej
samej mechanice i że zmiana `BezJednostek` naprawdę wymagałaby przeczytania tamtej
decyzji od nowa. Pole „Dlaczego to nie jest poprawka" twierdziło to; tu jest zmierzone.

## 6. Czego świadomie nie zrobiłem

- **Nie zmieniłem `Jednostki` ani rozstrzygnięcia 6.D142** — pole „Poza zakresem"
  zabrania obu.
- **Nie zmieniłem `BezJednostek` na zdejmowanie warunkowe** — §4 mówi dlaczego,
  liczbą, a nie ostrożnością.
- **Nie tknąłem 335 okaleczonych tekstów** — nikt ich nie czyta, a „ładniejszy wynik
  pośredni" nie jest celem, którego pozycja by żądała.
