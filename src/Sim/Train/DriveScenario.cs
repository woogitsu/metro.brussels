using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Założenie projektowe scenariusza. Osobny typ, a nie <see cref="DesignParameter"/>,
/// bo tamten wymaga ścieżki w <c>data/vehicle/m7-spec.json</c> — a te liczby nie są
/// parametrami pojazdu i w żadnym rejestrze ich nie ma. Wpisanie im zmyślonej ścieżki
/// byłoby dokładnie tym, przed czym ostrzega reguła 1 z <c>CLAUDE.md</c>.
/// </summary>
/// <param name="Name">Nazwa w kodzie.</param>
/// <param name="Value">Wartość użyta przez scenariusz.</param>
/// <param name="Reason">Dlaczego taka i czego brakuje, żeby przestała być założeniem.</param>
public readonly record struct ScenarioAssumption(string Name, double Value, string Reason)
{
    /// <inheritdoc/>
    public override string ToString() =>
        string.Create(CultureInfo.InvariantCulture, $"{Name} = {Value:R} — {Reason}");
}

/// <summary>Jedno polecenie obowiązujące od zadanego chainage do następnego wpisu.</summary>
/// <param name="FromChainageM">Chainage czoła składu, od którego polecenie obowiązuje.</param>
/// <param name="Command">Polecenie maszynisty.</param>
/// <param name="Label">Nazwa fazy do telemetrii.</param>
public readonly record struct DriveSegment(double FromChainageM, DriverCommand Command, string Label);

/// <summary>
/// Zapisany przejazd: co ma robić nastawnik i hamulec w funkcji chainage czoła składu.
///
/// Istnieje po to, żeby ten sam przejazd dało się policzyć **w dwóch miejscach naraz** —
/// w scenie Godota i w konsolowym <c>src/Sim.Runner</c> — i porównać liczba po liczbie.
/// Gdyby scenariusz mieszkał w scenie, porównanie z rdzeniem sprowadzałoby się do
/// porównania kodu z samym sobą przepisanym ręcznie.
///
/// Polecenie jest funkcją **chainage**, a nie czasu ani numeru kroku. Punkt na trasie
/// jest tym, co maszynista naprawdę widzi; poza tym wyzwalacz po chainage przeżywa
/// zmianę scenariusza prędkości, a wyzwalacz po czasie nie.
///
/// Wszystkie liczby konkretnego scenariusza są <c>design_assumption</c> — patrz
/// <see cref="Assumptions"/>. Żadna z nich nie jest faktem o brukselskim metrze.
/// </summary>
public sealed class DriveScenario
{
    private readonly DriveSegment[] _segments;

    /// <summary>Scenariusz z jawnej listy odcinków.</summary>
    public DriveScenario(
        string id,
        double startChainageM,
        double speedLimitMps,
        IReadOnlyList<DriveSegment> segments,
        IReadOnlyList<ScenarioAssumption> assumptions)
    {
        ArgumentNullException.ThrowIfNull(id);
        ArgumentNullException.ThrowIfNull(segments);
        ArgumentNullException.ThrowIfNull(assumptions);
        if (segments.Count == 0)
        {
            throw new ArgumentException("scenariusz bez odcinków nie prowadzi składu", nameof(segments));
        }

        for (var i = 1; i < segments.Count; i++)
        {
            if (segments[i].FromChainageM <= segments[i - 1].FromChainageM)
            {
                throw new ArgumentException(
                    "odcinki scenariusza muszą być ściśle rosnące po chainage", nameof(segments));
            }
        }

        Id = id;
        StartChainageM = startChainageM;
        SpeedLimitMps = speedLimitMps;
        _segments = new DriveSegment[segments.Count];
        for (var i = 0; i < segments.Count; i++)
        {
            _segments[i] = segments[i];
        }

        Assumptions = assumptions;
    }

    /// <summary>Identyfikator scenariusza; trafia do nagłówka telemetrii.</summary>
    public string Id { get; }

    /// <summary>Chainage czoła składu na starcie.</summary>
    public double StartChainageM { get; }

    /// <summary>Ograniczenie prędkości obowiązujące na całym przejeździe.</summary>
    public double SpeedLimitMps { get; }

    /// <summary>Odcinki scenariusza, rosnąco po chainage.</summary>
    public IReadOnlyList<DriveSegment> Segments => _segments;

    /// <summary>Katalog założeń projektowych tego scenariusza, z uzasadnieniami.</summary>
    public IReadOnlyList<ScenarioAssumption> Assumptions { get; }

    /// <summary>Polecenie obowiązujące dla zadanego chainage czoła składu.</summary>
    public DriveSegment SegmentAt(double chainageM)
    {
        var chosen = _segments[0];
        foreach (var segment in _segments)
        {
            if (segment.FromChainageM <= chainageM)
            {
                chosen = segment;
            }
            else
            {
                break;
            }
        }

        return chosen;
    }

    /// <summary>
    /// Pierwszy przejazd pakietu A: rozruch od Gare de l'Ouest, jazda z ograniczeniem
    /// prędkości modelu, jedno hamowanie służbowe do zatrzymania przed końcem osi.
    ///
    /// Bez postoju na stacjach pośrednich — cykl drzwi i czas postoju to T-312, a
    /// rozkład i dyspozytor to T-320. Przejazd bez zatrzymań jest tym, co da się zbudować
    /// z rzeczy, które w repo naprawdę są.
    /// </summary>
    /// <param name="model">Model pojazdu; dostarcza ograniczenie prędkości.</param>
    public static DriveScenario PackageAFirstRun(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);

        // Czoło składu na starcie. 94,0 m to długość M7 ze spec (data/vehicle/m7-spec.json):
        // przy mniejszej wartości ogon składu wystawałby poza początek osi i człony
        // ustawiałyby się na przyciętym chainage, czyli w jednym punkcie.
        const double startChainageM = 94.0;

        // Punkt podania hamulca. Dobrany tak, żeby czoło stanęło przed końcem osi
        // (6686,739 m) z zapasem kilkunastu metrów — zmierzona droga hamowania
        // służbowego z 80 km/h to 240,5 m (reports/T-310-physics.md §2).
        const double brakeChainageM = 6420.0;

        var assumptions = new[]
        {
            new ScenarioAssumption(
                "StartChainageM", startChainageM,
                "chainage czoła składu na starcie; równe długości M7 (94,0 m), żeby cały skład stał na osi"),
            new ScenarioAssumption(
                "BrakeChainageM", brakeChainageM,
                "chainage podania hamulca służbowego; dobrany do zmierzonej drogi hamowania 240,5 m"),
        };

        var segments = new[]
        {
            new DriveSegment(startChainageM, DriverCommand.FullPower, "traction"),
            new DriveSegment(brakeChainageM, DriverCommand.FullServiceBrake, "brake"),
        };

        return new DriveScenario(
            "package-a-first-run",
            startChainageM,
            Units.KmhToMps(model.DesignMaxSpeedKmh),
            segments,
            assumptions);
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Id}: start {StartChainageM:F1} m, limit {Units.MpsToKmh(SpeedLimitMps):F1} km/h, {_segments.Length} faz");
}
