using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Założenia przejazdu z zatrzymaniami. **Wszystkie cztery są bez źródła** i dlatego
/// mieszkają w osobnym typie z katalogiem <see cref="Assumptions"/>, a nie jako stałe
/// w <see cref="LineRun"/>: stała w kodzie wygląda dokładnie tak samo jak liczba
/// z rejestru, a te nią nie są.
///
/// <para>Konstruktor **nie ma wartości domyślnych**. Ta sama decyzja, co w
/// <see cref="DoorCycle"/>: kod woli nie skompilować się bez podanej liczby, niż
/// podstawić zmyśloną i pozwolić jej wyjść w raporcie jako fakt o metrze w Brukseli.</para>
/// </summary>
public sealed class LineRunSettings
{
    /// <summary>Założenia przejazdu.</summary>
    /// <param name="speedLimitMps">
    /// Jedno ograniczenie prędkości na całą oś. W <c>data/track/*.json</c> pole
    /// <c>speed_limits</c> jest **pustą listą we wszystkich sześciu pakietach** i nie ma
    /// dla nich źródła; T-113 daje wyłącznie ograniczenie **dolne** (57,65 km/h dla AW0),
    /// a <c>max_speed_kmh</c> = 80 w rejestrze M7 jest prędkością konstrukcyjną pojazdu
    /// ze statusem <c>design_model</c>, nie prędkością dopuszczalną na torze.
    /// </param>
    /// <param name="passengerExchangeSeconds">
    /// Czas wymiany pasażerów. Nie ma go w żadnym źródle — patrz T-312. T-113 ogranicza
    /// go od góry rozkładowym postojem minus cykl drzwi: ≤ 10,5 s przy medianowym
    /// postoju 19 s, ≤ 3,5 s przy najkrótszym w sieci 12 s.
    /// </param>
    /// <param name="brakeUsageFraction">
    /// Ułamek hamulca służbowego, przy którym maszynista zaczyna hamować. 1,0 znaczy
    /// „hamuj w ostatniej możliwej chwili" i nie zostawia zapasu na nic. Nie ma na to
    /// liczby w żadnym dokumencie — praktyka prowadzenia nie jest publikowana.
    /// </param>
    /// <param name="stopWindowM">
    /// Jak blisko chainage stacji zatrzymanie liczy się jako zatrzymanie na tej stacji.
    /// Nie jest to dokładność zatrzymania M7 — jest to okno rozpoznania stacji przez
    /// pętlę. Rzeczywisty błąd zatrzymania jest **mierzony** i wychodzi w
    /// <see cref="StationCall.StopErrorM"/>.
    /// </param>
    public LineRunSettings(
        double speedLimitMps,
        double passengerExchangeSeconds,
        double brakeUsageFraction,
        double stopWindowM)
    {
        Require(speedLimitMps, nameof(speedLimitMps), "Ograniczenie prędkości");
        Require(passengerExchangeSeconds, nameof(passengerExchangeSeconds), "Czas wymiany pasażerów", allowZero: true);
        Require(brakeUsageFraction, nameof(brakeUsageFraction), "Ułamek hamulca");
        Require(stopWindowM, nameof(stopWindowM), "Okno stacji");
        if (brakeUsageFraction > 1.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(brakeUsageFraction), brakeUsageFraction,
                "Ułamek hamulca powyżej 1,0 znaczyłby hamowanie mocniejsze niż służbowe — to hamulec awaryjny.");
        }

        SpeedLimitMps = speedLimitMps;
        PassengerExchangeSeconds = passengerExchangeSeconds;
        BrakeUsageFraction = brakeUsageFraction;
        StopWindowM = stopWindowM;
    }

    /// <summary>Jedno ograniczenie prędkości na całą oś.</summary>
    public double SpeedLimitMps { get; }

    /// <summary>Czas wymiany pasażerów przekazany do cyklu drzwi.</summary>
    public double PassengerExchangeSeconds { get; }

    /// <summary>Ułamek hamulca służbowego wyzwalający hamowanie.</summary>
    public double BrakeUsageFraction { get; }

    /// <summary>Okno rozpoznania stacji.</summary>
    public double StopWindowM { get; }

    /// <summary>Katalog założeń tego przejazdu, w kolejności deklaracji — czyli stałej.</summary>
    public IReadOnlyList<ScenarioAssumption> Assumptions => new[]
    {
        new ScenarioAssumption(
            nameof(SpeedLimitMps), SpeedLimitMps,
            "jedno ograniczenie na całą oś; speed_limits w data/track/*.json jest puste we " +
            "wszystkich sześciu pakietach, a 80 km/h z rejestru M7 to prędkość konstrukcyjna " +
            "pojazdu (design_model), nie prędkość dopuszczalna na torze"),
        new ScenarioAssumption(
            nameof(PassengerExchangeSeconds), PassengerExchangeSeconds,
            "brak źródła (T-312). T-113 ogranicza od góry: postój rozkładowy minus cykl drzwi " +
            "8,5 s, czyli ≤ 10,5 s przy medianowym postoju 19 s"),
        new ScenarioAssumption(
            nameof(BrakeUsageFraction), BrakeUsageFraction,
            "ułamek hamulca służbowego, przy którym maszynista zaczyna hamować; praktyka " +
            "prowadzenia STIB nie jest publikowana"),
        new ScenarioAssumption(
            nameof(StopWindowM), StopWindowM,
            "okno rozpoznania stacji przez pętlę, nie dokładność zatrzymania M7 — " +
            "rzeczywisty błąd zatrzymania jest mierzony i wychodzi w StationCall.StopErrorM"),
    };

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"limit {Units.MpsToKmh(SpeedLimitMps):F2} km/h, wymiana {PassengerExchangeSeconds:F1} s, " +
        $"hamulec {BrakeUsageFraction:P0} służbowego, okno stacji {StopWindowM:F1} m");

    private static void Require(double value, string name, string label, bool allowZero = false)
    {
        if (!double.IsFinite(value) || value < 0.0 || (!allowZero && value <= 0.0))
        {
            throw new ArgumentOutOfRangeException(
                name, value, $"{label} musi być skończone i {(allowZero ? "nieujemne" : "dodatnie")}.");
        }
    }
}
