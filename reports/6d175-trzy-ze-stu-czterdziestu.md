# 6.D175 — trzy napisy ze 140 widzi gracz, i wszystkie trzy stoją poza zasięgiem bramki

**12.09.2026**, na `e428ba0`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/SignallingHud.cs`, `src/Game/FirstRun.cs`, `src/Game/World/ChaseCameraAim.cs`.
Pozycja żądała przeczytania każdego literału **w miejscu użycia**, z zakazem
rozstrzygania po brzmieniu.

## 1. Nie 46, tylko 140 — liczba z pozycji opisywała klasyfikację, nie właściwość

Pozycja mówi „46 literałów niosących polski znak diakrytyczny". Zmierzone bramką:
takich literałów jest **140**.

Różnica nie jest błędem pomiaru 6.D154, tylko skutkiem tego, że tamten klasyfikator
był **łańcuchem**: najpierw `throw`, potem prefiks diagnostyczny, potem
`DesignAssumptions`, potem kształt CLI, potem identyfikator, a dopiero na końcu
„polski znak". Do rodziny „tekst polski" trafiało więc to, co **nie zostało wcześniej
przypisane gdzie indziej** — 46 sztuk. Liczba była prawdziwa o klasyfikacji
i myląca jako opis właściwości.

Jest to trzecia w tej serii poprawka tego samego rodzaju (po 446 zamiast 348 i po
„18 w kontekście JSON-a", które mierzyło sam odczyt). Wspólny kształt: **liczba
poprawna dla tego, co zadeklarowałem, i węższa niż rzecz, o którą pytano.**

## 2. Wiersz nie wystarcza — przypisanie do INSTRUKCJI zbija kosz z 45 na 5

Klasyfikacja po wierszu zostawiała **45** literałów nierozstrzygniętych. Przykłady
pokazały dlaczego: `przejazd z zatrzymaniami wymaga co najmniej dwóch` to dalszy
fragment `$"[LINIA] oś {_axis.Id} ma …"`, a `max żądanie={cab.MaxBrakeDemandMps2:F3} m/s²`
— fragment `$"[ATP] ostrzeżeń=…"`. Dokładnie zjawisko zmierzone w 6.D174.

Po cofnięciu się do początku instrukcji (wiersz zaczynający się od `+`, albo
poprzedni kończący się na `+ , ( =`):

| grupa | ile |
|---|---:|
| wypis z prefiksem | **91** |
| proza założeń projektowych | **20** |
| komunikat wyjątku (`throw`) | **14** |
| wypis bez prefiksu | **6** |
| nierozstrzygnięte | **5** |
| **HUD** | **3** |
| `ToString` diagnostyczny | **1** |

Suma 140.

## 3. Pięć nierozstrzygniętych — rozstrzygnięte drogą wywołania, nie brzmieniem

**Cztery w `ChaseCameraAim.cs`**: `pasmo ukrycia z decyzji właściciela`,
`kamera siedzi w skorupie składu`, `widok chase niedostępny — {powod}`,
`dostępny po minięciu {FromChainageM:F1} m`. Brzmią jak komunikat dla użytkownika.
Droga wywołania mówi co innego: `ChaseCameraAim.Availability(…)` jest konsumowane
w `FirstRun.cs:2135` przez **`Abort(ExitViewUnavailable, …)`** — czyli wyjście
z kodem błędu, nie HUD. **Diagnostyka.**

**Jeden w `FirstRun.cs`**: `plan jest czytany, nie prowadzi — bez blokad i bez ochrony
pociągu`. Zmienna nazywa się `limitTail` i trafia do:

```csharp
GD.Print(string.Create(
    CultureInfo.InvariantCulture,
    $"[LIMIT] tryb ręczny: {…} km/h " +
    $"z planu {_manualPlan.PlanId} ({planNameForLog}); {limitTail}"));
```

**Diagnostyka.**

## 4. Trzy napisy widzi gracz — i to jest cała odpowiedź

```csharp
// src/Game/SignallingHud.cs
public const string WithoutSignalling  = "bez sygnalizacji — przejazd bez blokad (podaj --signalling)";
public const string NotOnPlanYet       = "sygnalizacja: skład jeszcze nie wjechał na plan";
public const string WithoutProtection  = "sygnalizacja: linia bez ochrony pociągu";
```

Droga na ekran, prześledzona do końca:

```
SignallingHud.NotOnPlanYet
  ← FirstRun.SignallingLine()            (FirstRun.cs:1693)
  ← _hud.Update(…, StationLine(), SignallingLine(), _viewLine, …)   (FirstRun.cs:1610)
```

`_hud.Update` to metoda rysująca panel. **Te trzy napisy docierają do gracza** i żaden
nie stoi w katalogu `UiText`.

**Wszystkie trzy są w `SignallingHud.cs`, którego bramka nie skanuje.** Potwierdza to
obserwację z 6.D154 i zawęża ją do liczby: nie „w SignallingHud jest tekst gracza",
tylko **trzy napisy, wymienione z nazwy, z drogą wywołania przy każdym**.

## 5. Stosunek, który warto zapamiętać

**3 na 140.** Rodzina „polski znak diakrytyczny" jest w 97,9 % diagnostyką i prozą
projektową. Gdyby bramkę rozszerzyć na całe `src/Game/` bez rozstrzygnięcia rodzin,
zgłosiłaby 137 napisów, których do katalogu wkładać nie należy — i zostałaby
wyłączona przy pierwszej takiej sesji.

## 6. Czego nie zrobiłem

- **Nie przeniosłem tych trzech do katalogu `UiText`.** Pozycja miała ustalić,
  ile ich jest i którędy idą; przeniesienie zmienia zachowanie HUD-u i jest osobną
  robotą, zależną od tej.
- **Nie rozszerzyłem zakresu bramki o `SignallingHud.cs`** — z tego samego powodu.
- **Nie sprawdzałem, czy `Hud.Update` rysuje wszystkie przekazane wiersze.** Droga
  jest prześledzona do wywołania rysującego; czy któryś wiersz bywa pomijany przy
  rysowaniu, jest pytaniem o `Hud.cs` i nie zostało zmierzone.
