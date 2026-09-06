using System;
using System.Globalization;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy własnościowe modelu trakcji (T-310) i solvera punktu hamowania (T-311) —
/// pozycja 6.A7. <c>BrakingTests</c> i <c>EnergyAndProfileTests</c> sprawdzają
/// konkretne, policzone ręcznie liczby; ten plik sprawdza **kształt** zachowania na
/// wielu losowych wejściach naraz, żeby złapać błąd, którego żaden pojedynczy
/// przypadek referencyjny nie widzi.
///
/// <para>Ziarno generatora jest stałe — <c>docs/01-architecture.md</c> wymaga
/// determinizmu, a „losowy" test, który raz na jakiś czas czerwienieje bez zmiany
/// kodu, jest gorszy niż brak testu.</para>
///
/// <para>Każda z czterech własności ma kontrolę negatywną: opisana jest w commicie,
/// który wprowadza ten plik, a nie w samym pliku, bo mutant wchodzi na chwilę do
/// <c>src/Sim</c> i wraca — nie zostaje w drzewie.</para>
/// </summary>
[TestClass]
public sealed class BrakingPropertyTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;
    private static readonly FixedStep Step = FixedStep.Simulation;

    // === (a1) droga hamowania rośnie monotonicznie z prędkością początkową =======

    /// <summary>
    /// **Własność 1a.** Przy stałym opóźnieniu i stałym celu (zatrzymanie) droga
    /// hamowania solvera T-311 jest ściśle rosnącą funkcją prędkości początkowej.
    /// Sto losowych prędkości z przedziału, w którym opóźnienie służbowe nie osiąga
    /// jeszcze progu zrywu (powyżej ~2,9 km/h dla M7) — więc każda para jest
    /// porównywalna tym samym wzorem, bez przejścia w gałąź „sam zryw".
    /// </summary>
    [TestMethod]
    public void Droga_hamowania_rosnie_monotonicznie_z_predkoscia_poczatkowa()
    {
        var solver = new BrakingPointSolver(Model);
        var decel = Model.DesignServiceBrakeMps2;
        var rng = new Random(6070001);

        var speedsKmh = new double[150];
        for (var i = 0; i < speedsKmh.Length; i++)
        {
            // Dolna granica 5 km/h zostawia zapas nad progiem zrywu (2,9 km/h dla
            // 1,10 m/s² i zrywu 0,75 m/s³); górna granica to Vmax modelu.
            speedsKmh[i] = 5.0 + (rng.NextDouble() * (Model.DesignMaxSpeedKmh - 5.0));
        }

        Array.Sort(speedsKmh);

        var previousSpeed = double.NaN;
        var previousDistance = double.NegativeInfinity;
        var comparisons = 0;
        foreach (var speedKmh in speedsKmh)
        {
            var startMps = Units.KmhToMps(speedKmh);
            var ceiling = solver.PlateauCeilingMps2(startMps, 0.0);
            Assert.IsTrue(decel < ceiling, $"{speedKmh:F3} km/h: opóźnienie musi być pod progiem zrywu dla tej próby");

            var distance = solver.DistanceM(startMps, 0.0, decel);

            if (!double.IsNaN(previousSpeed))
            {
                Assert.IsTrue(
                    distance > previousDistance,
                    string.Create(
                        CultureInfo.InvariantCulture,
                        $"{speedKmh:F6} km/h ({distance:F6} m) nie jest dalej niż " +
                        $"{previousSpeed:F6} km/h ({previousDistance:F6} m)"));
                comparisons++;
            }

            previousSpeed = speedKmh;
            previousDistance = distance;
        }

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[WŁASNOŚĆ 1a] {speedsKmh.Length} losowych prędkości, {comparisons} porównań par sąsiednich, wszystkie rosnące"));

        Assert.AreEqual(speedsKmh.Length - 1, comparisons);
    }

    // === (a2) droga hamowania nie maleje wraz z masą składu =======================

    /// <summary>
    /// **Własność 1b.** Przebieg z oporami (<see cref="BrakingRun"/>, T-311) na
    /// poziomie, bez sufitu przyczepnościowego: opór Davisa jest liczony na tonę,
    /// a hamulec jest poleceniem niezależnym od masy — więc droga hamowania w tym
    /// modelu w ogóle nie zależy od masy składu. Własność testowana tu jest słabsza
    /// i wystarczająca dla wiersza tabeli: **droga nie maleje**, gdy masa rośnie.
    /// Osiem mas z szerokiego przedziału (poniżej AW0, powyżej AW2), nie tylko
    /// dwóch punktów AW0/AW2 jak w <c>BrakingTests</c>.
    /// </summary>
    [TestMethod]
    public void Droga_hamowania_nie_maleje_wraz_ze_wzrostem_masy()
    {
        var run = new BrakingRun(Model);
        var rng = new Random(6070002);

        var aw0 = Model.MassKg(TrainLoad.Aw0);
        var aw2 = Model.MassKg(TrainLoad.Aw2);

        var massesKg = new double[8];
        for (var i = 0; i < massesKg.Length; i++)
        {
            // Przedział 0,5×AW0 .. 2×AW2 — szerzej niż realny skład, celowo: własność
            // matematyczna modelu nie ma prawa zależeć od tego, czy masa jest sensowna.
            massesKg[i] = (0.5 * aw0) + (rng.NextDouble() * ((2.0 * aw2) - (0.5 * aw0)));
        }

        Array.Sort(massesKg);

        var distances = new double[massesKg.Length];
        for (var i = 0; i < massesKg.Length; i++)
        {
            var conditions = new RunConditions(massesKg[i], 0.0, Model.DesignAdhesionDry, TrackEnvironment.Tunnel);
            var result = run.ToStop(conditions, 80.0, Model.DesignServiceBrakeMps2, null, Step);
            Assert.IsTrue(result.ReachedTarget, $"masa {massesKg[i]:F1} kg nie dobiegła do zatrzymania");
            distances[i] = result.DistanceM;
        }

        for (var i = 0; i < massesKg.Length; i++)
        {
            Console.WriteLine(string.Create(
                CultureInfo.InvariantCulture, $"[WŁASNOŚĆ 1b] {massesKg[i]:F1} kg -> {distances[i]:F9} m"));
        }

        for (var i = 1; i < distances.Length; i++)
        {
            // Tolerancja czysto na zaokrąglenie kroku całkowania (1/120 s), nie na fizykę.
            Assert.IsTrue(
                distances[i] >= distances[i - 1] - 1e-6,
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"masa {massesKg[i]:F1} kg dała krótszą drogę ({distances[i]:F6} m) niż lżejsza " +
                    $"{massesKg[i - 1]:F1} kg ({distances[i - 1]:F6} m)"));
        }
    }

    // === (b) bilans energii hamowania domyka się dla losowych warunków ===========

    /// <summary>
    /// **Własność 2.** <c>BrakingTests</c> i <c>EnergyAndProfileTests</c> sprawdzają
    /// domknięcie bilansu na garści ręcznie wybranych przypadków (0 %, ±3 % pochylenia,
    /// stała masa AW2). Tu 60 losowych kombinacji prędkości, masy, opóźnienia,
    /// pochylenia i otoczenia toru naraz — żeby złapać kombinację, której nikt ręcznie
    /// nie wybrał.
    /// </summary>
    [TestMethod]
    public void Bilans_energii_hamowania_domyka_sie_dla_losowych_warunkow()
    {
        var run = new BrakingRun(Model);
        var rng = new Random(6070003);
        const int samples = 60;
        const double tolerance = 1e-9;

        var worst = 0.0;
        for (var i = 0; i < samples; i++)
        {
            var speedKmh = 5.0 + (rng.NextDouble() * (Model.DesignMaxSpeedKmh - 5.0));
            var massKg = (0.5 * Model.MassKg(TrainLoad.Aw0))
                + (rng.NextDouble() * ((2.0 * Model.MassKg(TrainLoad.Aw2)) - (0.5 * Model.MassKg(TrainLoad.Aw0))));
            var decel = 0.3 + (rng.NextDouble() * 2.7);
            var gradePercent = -10.0 + (rng.NextDouble() * 20.0);
            var environment = rng.Next(2) == 0 ? TrackEnvironment.Tunnel : TrackEnvironment.Surface;

            var conditions = new RunConditions(massKg, gradePercent, Model.DesignAdhesionDry, environment);
            var result = run.ToStop(conditions, speedKmh, decel, null, Step);

            worst = Math.Max(worst, result.Energy.RelativeResidual);

            Assert.IsTrue(
                result.Energy.RelativeResidual < tolerance,
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"próba {i}: v0={speedKmh:F2} km/h, m={massKg:F0} kg, b={decel:F3} m/s², " +
                    $"pochylenie={gradePercent:F2}%, {environment}: reszta względna " +
                    $"{result.Energy.RelativeResidual:E3}"));
        }

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[WŁASNOŚĆ 2] {samples} losowych warunków, najgorsza reszta względna = {worst:E3}"));
    }

    // === (c) czas przebiegu nigdy nie jest ujemny =================================

    /// <summary>
    /// **Własność 3.** Czas w rdzeniu jest funkcją liczby kroków
    /// (<c>docs/01-architecture.md</c>), więc dla przebiegu krokowego jest nieujemny
    /// z definicji licznika. Solver T-311 liczy czas osobnym wzorem zamkniętym
    /// (<see cref="BrakingPointSolver.Solve"/>) — to jest jedyne miejsce, w którym
    /// „ujemny czas" w ogóle mógłby wyciec z błędu znaku we wzorze, więc własność
    /// sprawdza oba źródła czasu na losowych wejściach: przebieg krokowy
    /// (<see cref="BrakingRun"/>, <see cref="AccelerationRun"/>) i wzór zamknięty
    /// solvera.
    /// </summary>
    [TestMethod]
    public void Czas_przebiegu_nigdy_nie_jest_ujemny()
    {
        var rng = new Random(6070004);
        const int samples = 60;

        var brakingRun = new BrakingRun(Model);
        var accelerationRun = new AccelerationRun(Model);
        var solver = new BrakingPointSolver(Model);

        for (var i = 0; i < samples; i++)
        {
            var speedKmh = 5.0 + (rng.NextDouble() * (Model.DesignMaxSpeedKmh - 5.0));
            var massKg = (0.5 * Model.MassKg(TrainLoad.Aw0))
                + (rng.NextDouble() * ((2.0 * Model.MassKg(TrainLoad.Aw2)) - (0.5 * Model.MassKg(TrainLoad.Aw0))));
            var decel = 0.3 + (rng.NextDouble() * 2.7);
            var gradePercent = -10.0 + (rng.NextDouble() * 20.0);
            var conditions = new RunConditions(massKg, gradePercent, Model.DesignAdhesionDry, TrackEnvironment.Tunnel);

            var braking = brakingRun.ToStop(conditions, speedKmh, decel, null, Step);
            Assert.IsTrue(braking.Steps >= 0, $"próba {i}: BrakingRun dał ujemną liczbę kroków");
            Assert.IsTrue(
                braking.TimeSeconds >= 0.0,
                string.Create(CultureInfo.InvariantCulture, $"próba {i}: BrakingRun dał ujemny czas {braking.TimeSeconds:R} s"));

            var accelerationTargetKmh = 5.0 + (rng.NextDouble() * (Model.DesignMaxSpeedKmh - 5.0));
            var acceleration = accelerationRun.ToSpeed(conditions, accelerationTargetKmh, Step);
            Assert.IsTrue(
                acceleration.TimeSeconds >= 0.0,
                string.Create(
                    CultureInfo.InvariantCulture, $"próba {i}: AccelerationRun dał ujemny czas {acceleration.TimeSeconds:R} s"));

            // Solver: cel zawsze 0, start powyżej progu zrywu dla wylosowanego opóźnienia,
            // żeby test naprawdę wołał gałąź ze wzorem zamkniętym czasu, nie „sam zryw".
            var startMps = Units.KmhToMps(speedKmh);
            var ceiling = solver.PlateauCeilingMps2(startMps, 0.0);
            var solverDecel = Math.Min(decel, 0.5 * ceiling);
            var point = solver.Solve(startMps, 0.0, solverDecel);
            Assert.IsTrue(
                point.TimeSeconds >= 0.0,
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"próba {i}: solver dał ujemny czas {point.TimeSeconds:R} s przy v0={speedKmh:F3} km/h, " +
                    $"b={solverDecel:F4} m/s²"));
        }

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture, $"[WŁASNOŚĆ 3] {samples} losowych prób, trzy źródła czasu, zero ujemnych"));
    }
}
