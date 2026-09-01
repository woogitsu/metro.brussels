using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Rozwiązanie punktu hamowania: jakie opóźnienie i na jakiej drodze.
/// </summary>
/// <param name="DecelerationMps2">Opóźnienie na odcinku stałym, po dojściu zrywem.</param>
/// <param name="DistanceM">Droga od podania hamulca do osiągnięcia prędkości docelowej.</param>
/// <param name="TimeSeconds">Czas tego samego odcinka.</param>
/// <param name="RampSeconds">Czas narastania hamowania zrywem, <c>b / j</c>.</param>
/// <param name="SpeedAfterRampMps">Prędkość w chwili dojścia do pełnego opóźnienia.</param>
/// <param name="RampOnly">
/// <c>true</c>, gdy prędkość docelowa wypada jeszcze w trakcie narastania hamulca —
/// wtedy zadane opóźnienie nigdy nie zostaje osiągnięte, a droga nie zależy już od niego.
/// </param>
public readonly record struct BrakingPoint(
    double DecelerationMps2,
    double DistanceM,
    double TimeSeconds,
    double RampSeconds,
    double SpeedAfterRampMps,
    bool RampOnly)
{
    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"b = {DecelerationMps2:F4} m/s², s = {DistanceM:F3} m, t = {TimeSeconds:F3} s{(RampOnly ? " (sam zryw)" : string.Empty)}");
}

/// <summary>
/// Solver punktu hamowania: mając prędkość bieżącą, docelową i odległość — jakie
/// opóźnienie jest potrzebne; i odwrotnie — na jakiej drodze trzeba zacząć hamować.
///
/// <para><b>Nie jest to <c>v²/2a</c>.</b> Model z <c>docs/02-simulation.md</c> ma
/// ograniczenie zrywu 0,75 m/s³, więc hamowanie zaczyna się od zera i narasta.
/// Droga składa się z dwóch części: narastania zrywem (<c>t_r = b/j</c>) i odcinka
/// o stałym opóźnieniu. Po scałkowaniu:</para>
///
/// <code>
/// s(b) = (v₀² − v₁²) / (2b)  +  v₀·b / (2j)  −  b³ / (24 j²)
/// t(b) = (v₀ − v₁) / b       +  b / (2j)
/// </code>
///
/// <para>Pierwszy człon to szkolne <c>v²/2a</c>; dwa pozostałe są ceną zrywu. Przy
/// <c>j → ∞</c> znikają, co jest kontrolą wzoru.</para>
///
/// <para><b>Zryw stawia twardą granicę.</b> Powyżej <c>b = √(2 j Δv)</c> prędkość
/// docelowa wypada jeszcze w trakcie narastania hamulca, więc dalsze zwiększanie
/// zadanego opóźnienia **nic nie daje** — droga przestaje od niego zależeć. Ta
/// najkrótsza droga to <see cref="MinimumDistanceM"/> i jest własnością samego
/// ograniczenia zrywu, niezależną od tego, jak mocny jest hamulec. Poniżej niej
/// solver nie ma rozwiązania i mówi o tym wprost, zamiast zwrócić liczbę.</para>
///
/// <para><b>Czego solver NIE uwzględnia:</b> oporów ruchu, pochylenia i sufitu
/// przyczepnościowego. Opory i pochylenie w dół są w tym miejscu po stronie
/// bezpiecznej i po stronie niebezpiecznej odpowiednio, więc mieszanie ich do wzoru
/// zamkniętego dałoby wynik, którego nie da się sprawdzić ręcznie. Drogę z oporami
/// liczy numerycznie <see cref="BrakingRun"/>, a różnicę między jednym a drugim
/// raport podaje liczbą dla każdej prędkości. Osiągalność zadanego opóźnienia
/// sprawdza <see cref="BrakeAdhesionLimit"/>.</para>
/// </summary>
public sealed class BrakingPointSolver
{
    /// <summary>
    /// Liczba kroków bisekcji. Stała, bo determinizm z <c>docs/01-architecture.md</c>
    /// nie znosi pętli „aż się zbiegnie": ta sama liczba wejściowa ma dawać ten sam
    /// wynik co do bitu na każdej maszynie. 200 kroków to z zapasem więcej, niż potrzeba
    /// do wyczerpania mantysy <c>double</c> na przedziale rzędu 10 m/s².
    /// </summary>
    public const int BisectionSteps = 200;

    private readonly double _jerk;

    /// <summary>Solver dla zadanego ograniczenia zrywu.</summary>
    public BrakingPointSolver(double jerkMps3)
    {
        if (!double.IsFinite(jerkMps3) || jerkMps3 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(jerkMps3), jerkMps3, "Ograniczenie zrywu musi być dodatnie i skończone.");
        }

        _jerk = jerkMps3;
    }

    /// <summary>Solver zbudowany z modelu pojazdu.</summary>
    public BrakingPointSolver(VehicleModel model)
        : this((model ?? throw new ArgumentNullException(nameof(model))).DesignJerkMps3)
    {
    }

    /// <summary>Solver M7.</summary>
    public static BrakingPointSolver M7 { get; } = new(VehicleModel.M7);

    /// <summary>Ograniczenie zrywu użyte przez solver.</summary>
    public double JerkMps3 => _jerk;

    /// <summary>
    /// Opóźnienie, powyżej którego prędkość docelowa wypada jeszcze w trakcie
    /// narastania hamulca: <c>√(2 j Δv)</c>. Powyżej tej wartości droga już nie maleje.
    /// </summary>
    public double PlateauCeilingMps2(double startSpeedMps, double targetSpeedMps)
    {
        RequireSpeeds(startSpeedMps, targetSpeedMps);
        return Math.Sqrt(2.0 * _jerk * (startSpeedMps - targetSpeedMps));
    }

    /// <summary>
    /// Najkrótsza droga hamowania, jaką dopuszcza samo ograniczenie zrywu — bez względu
    /// na to, jak mocny jest hamulec i ile osi hamuje.
    /// </summary>
    public double MinimumDistanceM(double startSpeedMps, double targetSpeedMps) =>
        Solve(startSpeedMps, targetSpeedMps, PlateauCeilingMps2(startSpeedMps, targetSpeedMps)).DistanceM;

    /// <summary>
    /// Przebieg hamowania dla zadanego opóźnienia: droga, czas i to, czy opóźnienie
    /// w ogóle zostaje osiągnięte przed dojściem do prędkości docelowej.
    /// </summary>
    /// <param name="startSpeedMps">Prędkość bieżąca.</param>
    /// <param name="targetSpeedMps">Prędkość docelowa; 0 dla zatrzymania.</param>
    /// <param name="decelerationMps2">Zadane opóźnienie na odcinku stałym.</param>
    public BrakingPoint Solve(double startSpeedMps, double targetSpeedMps, double decelerationMps2)
    {
        RequireSpeeds(startSpeedMps, targetSpeedMps);
        if (!double.IsFinite(decelerationMps2) || decelerationMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(decelerationMps2), decelerationMps2, "Opóźnienie musi być dodatnie i skończone.");
        }

        var ceiling = PlateauCeilingMps2(startSpeedMps, targetSpeedMps);
        if (decelerationMps2 >= ceiling)
        {
            // Sam zryw: a(t) = j·t aż do prędkości docelowej. Droga i czas nie zależą
            // wtedy od zadanego b w ogóle — zależą wyłącznie od zrywu i od Δv.
            var rampTime = Math.Sqrt(2.0 * (startSpeedMps - targetSpeedMps) / _jerk);
            var rampDistance = (startSpeedMps * rampTime) - (_jerk * rampTime * rampTime * rampTime / 6.0);
            return new BrakingPoint(
                decelerationMps2, rampDistance, rampTime, rampTime, targetSpeedMps, RampOnly: true);
        }

        var plateauTime = decelerationMps2 / _jerk;
        var speedAfterRamp = startSpeedMps - (decelerationMps2 * decelerationMps2 / (2.0 * _jerk));
        var distance = DistanceM(startSpeedMps, targetSpeedMps, decelerationMps2);
        var time = ((startSpeedMps - targetSpeedMps) / decelerationMps2) + (decelerationMps2 / (2.0 * _jerk));

        return new BrakingPoint(decelerationMps2, distance, time, plateauTime, speedAfterRamp, RampOnly: false);
    }

    /// <summary>
    /// Droga hamowania z ograniczeniem zrywu, wzorem zamkniętym.
    /// Obowiązuje dla <c>b ≤ √(2 j Δv)</c>; powyżej użyj <see cref="Solve"/>.
    /// </summary>
    public double DistanceM(double startSpeedMps, double targetSpeedMps, double decelerationMps2)
    {
        RequireSpeeds(startSpeedMps, targetSpeedMps);
        var b = decelerationMps2;
        return (((startSpeedMps * startSpeedMps) - (targetSpeedMps * targetSpeedMps)) / (2.0 * b))
            + (startSpeedMps * b / (2.0 * _jerk))
            - (b * b * b / (24.0 * _jerk * _jerk));
    }

    /// <summary>
    /// Odwrotność: jakie opóźnienie trzeba zadać, żeby zejść z <paramref name="startSpeedMps"/>
    /// do <paramref name="targetSpeedMps"/> dokładnie na drodze <paramref name="distanceM"/>.
    /// </summary>
    /// <returns><c>false</c>, gdy droga jest krótsza niż <see cref="MinimumDistanceM"/>.</returns>
    public bool TryRequiredDeceleration(
        double startSpeedMps, double targetSpeedMps, double distanceM, out BrakingPoint point)
    {
        RequireSpeeds(startSpeedMps, targetSpeedMps);
        if (!double.IsFinite(distanceM) || distanceM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(distanceM), distanceM, "Odległość do punktu docelowego musi być dodatnia i skończona.");
        }

        var ceiling = PlateauCeilingMps2(startSpeedMps, targetSpeedMps);
        var shortest = Solve(startSpeedMps, targetSpeedMps, ceiling);
        if (distanceM < shortest.DistanceM)
        {
            point = default;
            return false;
        }

        // s(b) jest na (0, ceiling] malejąca, a w samym ceiling ma pochodną dokładnie
        // zero — dlatego bisekcja po tym przedziale jest jednoznaczna i zbieżna.
        var low = 0.0;
        var high = ceiling;
        for (var i = 0; i < BisectionSteps; i++)
        {
            var mid = 0.5 * (low + high);
            if (mid <= low || mid >= high)
            {
                break;
            }

            if (DistanceM(startSpeedMps, targetSpeedMps, mid) > distanceM)
            {
                low = mid;
            }
            else
            {
                high = mid;
            }
        }

        point = Solve(startSpeedMps, targetSpeedMps, high);
        return true;
    }

    /// <summary>
    /// To samo co <see cref="TryRequiredDeceleration"/>, ale odmowa jest wyjątkiem
    /// z liczbą: żądanie krótsze niż minimum wynikające ze zrywu nie ma rozwiązania
    /// i nie wolno na nie odpowiedzieć „prawie".
    /// </summary>
    public BrakingPoint RequiredDeceleration(double startSpeedMps, double targetSpeedMps, double distanceM)
    {
        if (TryRequiredDeceleration(startSpeedMps, targetSpeedMps, distanceM, out var point))
        {
            return point;
        }

        var minimum = MinimumDistanceM(startSpeedMps, targetSpeedMps);
        throw new ArgumentOutOfRangeException(
            nameof(distanceM), distanceM, string.Create(
                CultureInfo.InvariantCulture,
                $"Przy zrywie {_jerk:R} m/s³ droga z {startSpeedMps:R} do {targetSpeedMps:R} m/s " +
                $"nie może być krótsza niż {minimum:R} m, bez względu na siłę hamulca."));
    }

    private static void RequireSpeeds(double startSpeedMps, double targetSpeedMps)
    {
        if (!double.IsFinite(startSpeedMps) || startSpeedMps <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(startSpeedMps), startSpeedMps, "Prędkość początkowa musi być dodatnia i skończona.");
        }

        if (!double.IsFinite(targetSpeedMps) || targetSpeedMps < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(targetSpeedMps), targetSpeedMps, "Prędkość docelowa musi być nieujemna i skończona.");
        }

        if (targetSpeedMps >= startSpeedMps)
        {
            throw new ArgumentOutOfRangeException(
                nameof(targetSpeedMps), targetSpeedMps,
                "Prędkość docelowa musi być mniejsza od bieżącej — inaczej to nie jest hamowanie.");
        }
    }
}
