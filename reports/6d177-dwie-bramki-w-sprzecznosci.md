# 6.D177 — te 20 literałów jest WYMAGANYCH przez inny test, więc przeniesienie ich łamie bramkę

**12.09.2026**, na `810732c`. Wejście: `src/Game/DesignAssumptions.cs`,
`tests/Game.Tests/DesignAssumptionsTests.cs`, `tests/Game.Tests/UiTextTests.cs`.
Pozycja pytała, czy plik ma być wyłączony z zakresu bramki nazwany wprost (jak
`UiText.cs`), czy jego zawartość przenosi się do `docs/`.

## 1. Czym są te 20 literałów

Plik trzyma dwadzieścia rekordów `ViewAssumption(Name, Value, Unit, Reason)`.
Dwadzieścia literałów zgłaszanych przez sito słów to pola **`Reason`**:

```csharp
new ViewAssumption(nameof(CabEyeHeightM), CabEyeHeightM, "m",
    "wysokość oka nad główką szyny; podłoga M7 jest na 1,03 m (spec), reszta to
     postawa siedzącego maszynisty — STIB nie publikuje rysunku pulpitu"),
```

## 2. Rozstrzygnięcie: przeniesienie do `docs/` ŁAMIE istniejącą bramkę

`tests/Game.Tests/DesignAssumptionsTests.cs` trzyma cztery testy o tej liście
i dwa z nich czynią te literały **wymaganymi**:

```csharp
public void EveryAssumptionSaysWhyItIsAnAssumption()
{
    foreach (var assumption in DesignAssumptions.All)
    {
        Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Unit), assumption.Name);
        Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Reason), assumption.Name);
        var reason = assumption.Reason.Trim().ToLowerInvariant();
        Assert.IsFalse(Placeholders.Contains(reason),
            $"{assumption.Name}: uzasadnienie '{assumption.Reason}' to zaślepka");
    }
}
```

oraz `EveryDeclaredAssumptionMatchesTheConstantItNames`, które **refleksją** wiąże
`assumption.Value` z rzeczywistą stałą (`1e-12`), a `EveryConstantIsDeclaredAsAnAssumption`
żąda wpisu dla **każdej** stałej klasy.

**Uzasadnienie nie jest prozą obok wartości — jest polem, którego istnienia pilnuje
test, przywiązanym refleksją do liczby, którą opisuje.** Przeniesienie go do `docs/`
zostawiłoby `Reason` pustym i zapaliło `EveryAssumptionSaysWhyItIsAnAssumption`
dwadzieścia razy.

To jest mocniejszy argument niż ten, który sam wpisałem do pola pozycji („przeniesienie
rozdziela stałą od powodu"). Tamten był zdaniem o dobrej praktyce. **Ten jest zdaniem
o czerwonym teście.**

## 3. Dwie bramki stanęłyby w bezpośredniej sprzeczności

Gdyby zakres sita słów rozszerzyć na całe `src/Game/` bez wyłączenia tego pliku:

| bramka | czego żąda od tych samych 20 literałów |
|---|---|
| `DesignAssumptionsTests.EveryAssumptionSaysWhyItIsAnAssumption` | **mają istnieć** i nie być zaślepką |
| sito słów w `UiTextTests` | **nie mają istnieć** — to polski tekst w kodzie |

Nie jest to niedogodność do przełknięcia, tylko para wykluczających się żądań na tym
samym zbiorze. **Wyłączenie `DesignAssumptions.cs` nazwane wprost jest więc jedyną
odpowiedzią zgodną z oboma testami** — i dokładnie z tego powodu, z którego wyłączony
jest `UiText.cs`: tam klucz stoi jako **wpis**, a nie jako wywołanie; tu uzasadnienie
stoi jako **dana wymagana przez test**, a nie jako tekst dla gracza.

## 4. Ale dziś to wyłączenie byłoby BEZCZYNNE — i to jest drugi wynik

Zmierzone, zanim cokolwiek napisałem:

- `DesignAssumptions.cs` **nie występuje w `UiTextTests.cs` ani razu** — sito słów
  czyta `Hud.cs`, trzy metody `FirstRun.cs`, tablicę `Nazwy` z `KeyNames.cs` oraz
  `DriverActions.cs` i `EmergencyBrake.cs`.
- Plik **jest** w `ZrodlaGry()` (wyłączone są tam tylko `.godot` i `UiText.cs`), ale ma
  **zero** wywołań `UiText.`, więc skan kluczy katalogu nie znajduje w nim niczego.

Żadna dzisiejsza bramka nie czyta tych 20 literałów. Wyłączenie zmieniłoby dziś tylko
jedną rzecz: liczbę plików w korpusie z 21 na 20, czyli zapadkę `PlikowWZasieguBramki`
wprowadzoną przy 6.D153.

**Rozstrzygnięcie zapisane, wyłączenie NIE wpisane** — z tego samego powodu co przy
6.D176: kod, który dziś nie działa, wygląda jak ochrona i nie chroni niczego, a przy
rozszerzaniu zakresu i tak trzeba go będzie napisać razem z decyzją o zakresie.

## 5. Pomyłka po drodze, zapisana a nie zamieciona

Szukając konsumentów listy, napisałem `grep -rln "ViewAssumption" src/Game tests` i
dostałem **jeden plik** — samą `DesignAssumptions.cs`. Wniosek nasuwał się sam: listy
nikt nie czyta, jest martwa.

**Był nieprawdziwy.** `DesignAssumptionsTests.cs` czyta ją przez `DesignAssumptions.All`
i nigdzie nie nazywa typu `ViewAssumption`, więc mój wzorzec jej nie widział. Gdybym
na tym poprzestał, zapisałbym w raporcie zdanie odwrotne do prawdy — i to o rzeczy,
która jest sednem pozycji. Sprawdzenie kosztowało jedno `ls tests/Game.Tests/`.

Jest to ten sam kształt, co cztery wcześniejsze pomyłki tej sesji: **wzorzec mierzył
to, co zadeklarowałem, i węziej niż rzecz, o którą pytałem.**

## 6. Czego nie zrobiłem

- **Nie wyłączyłem pliku z `ZrodlaGry()`** — sekcja 4.
- **Nie tknąłem żadnego uzasadnienia ani żadnej stałej** — pole „Poza zakresem"
  pozycji wyklucza zmianę wartości, a uzasadnienia są danymi pod testem.
- **Nie sprawdzałem, czy `docs/21-measured-vs-assumed.md` powtarza te uzasadnienia.**
  Gdyby powtarzał, byłaby to druga kopia tej samej prozy i osobna pozycja — ale tego
  nie zmierzyłem i nie twierdzę.
