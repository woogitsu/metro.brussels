using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Runner;

/// <summary>
/// Gospodarz rdzenia bez silnika. Cztery polecenia, każde odpowiada na jedno pytanie
/// z pętli weryfikacji <c>CLAUDE.md</c> §5:
///
/// <list type="bullet">
/// <item><c>drive</c> — jak wygląda przejazd policzony samym rdzeniem;</item>
/// <item><c>compare</c> — o ile rozjeżdża się z przejazdem policzonym w Godocie;</item>
/// <item><c>axis</c> — czy oś w C# jest tą samą krzywą, po której zamiatany jest tunel;</item>
/// <item><c>parity</c> — czy kontroler przy pełnej trakcji to nadal rdzeń z T-310;</item>
/// <item><c>braking</c> — tablice referencyjne hamowania z T-311, do porównania
/// z <c>tools/physics/braking.py</c> wiersz po wierszu.</item>
/// </list>
/// </summary>
public static class Program
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    /// <summary>Punkt wejścia.</summary>
    public static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Usage();
            return 2;
        }

        try
        {
            return args[0] switch
            {
                "drive" => Drive(args),
                "compare" => Compare(args),
                "axis" => Axis(args),
                "parity" => Parity(),
                "braking" => Braking(),
                _ => Unknown(args[0]),
            };
        }
        catch (Exception exception) when (exception is IOException or ArgumentException or FormatException or InvalidOperationException)
        {
            Console.Error.WriteLine("BŁĄD: " + exception.Message);
            return 1;
        }
    }

    private static int Unknown(string command)
    {
        Console.Error.WriteLine($"nieznane polecenie: {command}");
        Usage();
        return 2;
    }

    private static void Usage()
    {
        Console.Error.WriteLine("""
            MetroBxl.Sim.Runner — konsolowy gospodarz rdzenia symulacji

              drive   [--out PLIK] [--sample-every N]     telemetria przejazdu z rdzenia
              compare PLIK_A PLIK_B [--tolerance METRY]   rozjazd dwóch telemetrii
              axis    --axis PLIK [--manifest PLIK]       kontrola osi wobec manifestu chunków
              parity                                      kontroler vs AccelerationRun z T-310
              braking                                     tablice referencyjne hamowania (T-311)
            """);
    }

    // --- drive --------------------------------------------------------------------

    private static int Drive(string[] args)
    {
        var output = Option(args, "--out");
        var sampleEvery = long.Parse(Option(args, "--sample-every") ?? DriveTelemetry.DefaultSampleEverySteps.ToString(Inv), Inv);

        var model = VehicleModel.M7;
        var scenario = DriveScenario.PackageAFirstRun(model);
        var drive = NewDrive(model, scenario);

        var lines = new List<string> { DriveTelemetry.Header };
        lines.Add(DriveTelemetry.Row(drive));
        while (drive.Step())
        {
            if (DriveTelemetry.IsSample(drive.State.Steps, sampleEvery) || drive.Finished)
            {
                lines.Add(DriveTelemetry.Row(drive));
            }
        }

        if (output is null)
        {
            foreach (var line in lines)
            {
                Console.Out.WriteLine(line);
            }
        }
        else
        {
            File.WriteAllLines(output, lines);
        }

        Console.Error.WriteLine(string.Create(
            Inv,
            $"[RDZEŃ] {scenario.Id}: kroków={drive.State.Steps} t={drive.State.TimeSeconds(drive.TimeStep):F3} s " +
            $"chainage={drive.ChainageM:F3} m droga={drive.State.DistanceM:F3} m koniec={drive.FinishReason}"));

        return 0;
    }

    /// <summary>
    /// Warunki przejazdu. Pochylenie 0 nie jest wyborem: profil pionowy pakietu A ma
    /// status <c>not_modelled</c> i <c>docs/21-measured-vs-assumed.md</c> §3 zabrania
    /// wyprowadzania z niego rzędnych. Otoczenie <c>Tunnel</c> jest z geometrii pakietu A.
    /// </summary>
    internal static ScenarioDrive NewDrive(VehicleModel model, DriveScenario scenario) =>
        new(
            model,
            scenario,
            new RunConditions(model.MassKg(TrainLoad.Aw2), 0.0, model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            FixedStep.Simulation);

    // --- compare ------------------------------------------------------------------

    private static int Compare(string[] args)
    {
        if (args.Length < 3)
        {
            Console.Error.WriteLine("compare wymaga dwóch plików");
            return 2;
        }

        var tolerance = double.Parse(Option(args, "--tolerance") ?? "1E-9", Inv);
        var left = File.ReadAllLines(args[1]);
        var right = File.ReadAllLines(args[2]);

        if (left.Length != right.Length)
        {
            Console.Error.WriteLine($"różna liczba wierszy: {left.Length} vs {right.Length}");
            return 1;
        }

        if (!string.Equals(left[0], right[0], StringComparison.Ordinal) ||
            !string.Equals(left[0], DriveTelemetry.Header, StringComparison.Ordinal))
        {
            Console.Error.WriteLine("nagłówki telemetrii nie zgadzają się z formatem rdzenia");
            return 1;
        }

        var worst = new double[DriveTelemetry.ColumnCount - 1];
        var worstRow = new int[DriveTelemetry.ColumnCount - 1];
        var identicalBytes = true;

        for (var i = 1; i < left.Length; i++)
        {
            if (!string.Equals(left[i], right[i], StringComparison.Ordinal))
            {
                identicalBytes = false;
            }

            var a = left[i].Split(',');
            var b = right[i].Split(',');
            if (a.Length != DriveTelemetry.ColumnCount || b.Length != DriveTelemetry.ColumnCount)
            {
                Console.Error.WriteLine($"wiersz {i}: zła liczba kolumn");
                return 1;
            }

            if (!string.Equals(a[^1], b[^1], StringComparison.Ordinal))
            {
                Console.Error.WriteLine($"wiersz {i}: różna faza scenariusza ({a[^1]} vs {b[^1]})");
                return 1;
            }

            for (var c = 0; c < DriveTelemetry.ColumnCount - 1; c++)
            {
                var delta = Math.Abs(double.Parse(a[c], Inv) - double.Parse(b[c], Inv));
                if (delta > worst[c])
                {
                    worst[c] = delta;
                    worstRow[c] = i;
                }
            }
        }

        var names = DriveTelemetry.Header.Split(',');
        var failed = false;
        Console.Out.WriteLine($"[PORÓWNANIE] wierszy={left.Length - 1} identyczne co do bajtu={(identicalBytes ? "TAK" : "NIE")}");
        for (var c = 0; c < worst.Length; c++)
        {
            var over = worst[c] > tolerance;
            failed |= over;
            Console.Out.WriteLine(string.Create(
                Inv, $"[PORÓWNANIE] {names[c],-12} max |Δ| = {worst[c]:E3} (wiersz {worstRow[c]}) {(over ? "PONAD PRÓG" : "ok")}"));
        }

        Console.Out.WriteLine(string.Create(Inv, $"[PORÓWNANIE] próg = {tolerance:E3}"));
        return failed ? 1 : 0;
    }

    // --- axis ---------------------------------------------------------------------

    private static int Axis(string[] args)
    {
        var axisPath = Option(args, "--axis") ?? throw new ArgumentException("axis wymaga --axis");
        var axis = TrackAxis.FromJson(File.ReadAllText(axisPath));

        Console.Out.WriteLine(string.Create(
            Inv,
            $"[OŚ] {axis.Id}: punktów źródłowych={axis.SourcePoints.Count} zagęszczonych={axis.Points.Count} " +
            $"długość_źródłowa={axis.DeclaredLengthM:F3} m długość_zagęszczona={axis.LengthM:F3} m"));
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[OŚ] odchyłka od łamanej STIB = {axis.MaxDeviationFromSourceM():F4} m, stacji={axis.Stations.Count}, " +
            $"profil_pionowy={axis.VerticalStatus}"));

        // Zrzut punktów istnieje po to, żeby dało się porównać oś z C# z osią z Pythona
        // punkt po punkcie, a nie tylko po długości. Format R — bez zaokrągleń.
        var dump = Option(args, "--dump-points");
        if (dump is not null)
        {
            var rows = new List<string>(axis.Points.Count);
            foreach (var point in axis.Points)
            {
                rows.Add(string.Create(Inv, $"{point.X:R},{point.Y:R},{point.Z:R}"));
            }

            File.WriteAllLines(dump, rows);
            Console.Out.WriteLine($"[OŚ] zrzut {rows.Count} punktów -> {dump}");
        }

        var manifestPath = Option(args, "--manifest");
        if (manifestPath is null)
        {
            return 0;
        }

        using var manifest = System.Text.Json.JsonDocument.Parse(File.ReadAllText(manifestPath));
        var manifestLength = manifest.RootElement.GetProperty("axis_length_m").GetDouble();
        var delta = Math.Abs(manifestLength - axis.LengthM);

        // Manifest zapisuje długość zaokrągloną do 1 mm (sort_keys + round w generatorze),
        // więc zgodność poniżej 1 mm jest maksimum, jakie ten plik potrafi potwierdzić.
        const double toleranceM = 1e-3;
        var ok = delta <= toleranceM;
        Console.Out.WriteLine(string.Create(
            Inv,
            $"[OŚ] manifest chunków: {manifestLength:F3} m, C#: {axis.LengthM:F3} m, |Δ| = {delta:E3} m -> {(ok ? "ZGODNE" : "ROZJAZD")}"));

        return ok ? 0 : 1;
    }

    // --- parity -------------------------------------------------------------------

    /// <summary>
    /// Kontrola, że <see cref="TrainController"/> nie jest drugą fizyką: przy pełnym
    /// nastawniku, odpuszczonym hamulcu i rozruchu z postoju musi dać **co do bitu** to
    /// samo, co <see cref="AccelerationRun"/> z T-310 — a ten odtwarza
    /// <c>tools/physics/reference.py</c>.
    /// </summary>
    private static int Parity()
    {
        var model = VehicleModel.M7;
        var step = FixedStep.Simulation;
        var target = Units.KmhToMps(model.DesignMaxSpeedKmh);
        var failed = false;

        foreach (var load in new[] { TrainLoad.Aw0, TrainLoad.Aw2 })
        {
            var conditions = RunConditions.Level(model, load);
            var reference = new AccelerationRun(model).ToSpeed(conditions, model.DesignMaxSpeedKmh, step);

            var controller = new TrainController(model);
            var state = DriveState.AtRest;
            while (state.SpeedMps < target && state.Steps < 300 * FixedStep.SimulationHertz)
            {
                state = controller.Advance(state, conditions, DriverCommand.FullPower, target, step, out _);
            }

            var sameSteps = state.Steps == reference.Steps;
            var sameBits = BitConverter.DoubleToInt64Bits(state.DistanceM) == BitConverter.DoubleToInt64Bits(reference.DistanceM);
            failed |= !sameSteps || !sameBits;

            Console.Out.WriteLine(string.Create(
                Inv,
                $"[PARYTET] {load}: kroki {state.Steps} vs {reference.Steps} ({(sameSteps ? "==" : "!=")}), " +
                $"droga {state.DistanceM:F3} m vs {reference.DistanceM:F3} m ({(sameBits ? "co do bitu" : "ROZJAZD")})"));
        }

        // Hamowanie: kontroler **nie** ma dawać tej samej drogi, co ServiceBrakingRun,
        // i warto, żeby to było widać liczbą. Tamten model jest czysto kinematyczny —
        // nie zna oporów ruchu. Kontroler dokłada do zadanego opóźnienia opory Davisa,
        // bo prowadzony skład jedzie w tunelu, a nie w próżni. Różnica jest **całą**
        // pracą oporów na drodze hamowania i nie wolno jej nazwać tolerancją.
        var brakeConditions = RunConditions.Level(model, TrainLoad.Aw2);
        var kinematic = new ServiceBrakingRun(model).ToStop(model.DesignMaxSpeedKmh, step);
        var controlled = new TrainController(model);
        var braking = new DriveState(0, target, 0.0, 0.0);
        while (braking.SpeedMps > 0.0 && braking.Steps < 120 * FixedStep.SimulationHertz)
        {
            braking = controlled.Advance(braking, brakeConditions, DriverCommand.FullServiceBrake, target, step, out _);
        }

        Console.Out.WriteLine(string.Create(
            Inv,
            $"[HAMOWANIE] kinematyczne (T-310) {kinematic.DistanceM:F3} m / {kinematic.TimeSeconds:F3} s, " +
            $"kontroler z oporami {braking.DistanceM:F3} m / {braking.TimeSeconds(step):F3} s, " +
            $"różnica {kinematic.DistanceM - braking.DistanceM:F3} m = praca oporów Davisa"));

        return failed ? 1 : 0;
    }

    // --- braking ------------------------------------------------------------------

    /// <summary>
    /// Tablice referencyjne hamowania z T-311, w formacie jeden do jednego z
    /// <c>tools/physics/braking.py</c> — po to, żeby dało się je porównać wiersz po
    /// wierszu, a nie „na oko". Rdzeń i referencja są tu dwiema niezależnymi drogami
    /// do tych samych liczb, dokładnie tak jak w T-310.
    /// </summary>
    private static int Braking()
    {
        var model = VehicleModel.M7;
        var solver = new BrakingPointSolver(model);
        var step = FixedStep.Simulation;

        Console.Out.WriteLine(string.Create(
            Inv,
            $"zryw = {model.DesignJerkMps3:R} m/s^3, lambda = {model.DesignEffectiveMassFactor:R}, " +
            $"sluzbowe = {model.DesignServiceBrakeMps2:R} m/s^2, awaryjne = {model.DesignEmergencyBrakeMps2:R} m/s^2"));
        Console.Out.WriteLine();

        Console.Out.WriteLine("SUFIT PRZYCZEPNOSCIOWY (design_assumption: udzial osi hamowanych)");
        Console.Out.WriteLine("rail  mu     wariant             f       b_max     b_max_bez_lambda  1.10  1.30");
        var limits = new[] { BrakeAdhesionLimit.AllAxles(model), BrakeAdhesionLimit.PoweredAxlesOnly(model) };
        foreach (var (rail, mu) in new[]
                 {
                     ("dry", model.DesignAdhesionDry), ("wet", model.DesignAdhesionWet),
                 })
        {
            foreach (var limit in limits)
            {
                var service = !limit.IsAdhesionLimited(model.DesignServiceBrakeMps2, mu);
                var emergency = !limit.IsAdhesionLimited(model.DesignEmergencyBrakeMps2, mu);
                Console.Out.WriteLine(string.Create(
                    Inv,
                    $"{rail,-5} {mu,-6:0.00} {limit.Variant,-19} {limit.DesignBrakedMassFraction:0.0000}  " +
                    $"{limit.MaxDecelerationMps2(mu),8:0.0000}  {limit.MaxRigidBodyDecelerationMps2(mu),16:0.0000}  " +
                    $"{(service ? "tak" : "NIE"),4}  {(emergency ? "tak" : "NIE"),4}"));
            }
        }

        Console.Out.WriteLine();
        Console.Out.WriteLine("PROGI KRYTYCZNE");
        var allAxles = BrakeAdhesionLimit.AllAxles(model);
        foreach (var (decel, name) in new[]
                 {
                     (model.DesignServiceBrakeMps2, "sluzbowe"), (model.DesignEmergencyBrakeMps2, "awaryjne"),
                 })
        {
            foreach (var (rail, mu) in new[]
                     {
                         ("dry", model.DesignAdhesionDry), ("wet", model.DesignAdhesionWet),
                     })
            {
                var required = allAxles.RequiredBrakedMassFraction(decel, mu);
                var note = required > 1.0 ? "  -> NIEOSIAGALNE przy kazdym ukladzie osi" : string.Empty;
                Console.Out.WriteLine(string.Create(
                    Inv, $"  {name} {decel:0.00} m/s^2 {rail}: f_min = {required:0.000000}{note}"));
            }

            Console.Out.WriteLine(string.Create(
                Inv, $"  {name} {decel:0.00} m/s^2 przy f=1: mu_min = {allAxles.RequiredAdhesion(decel):0.000000}"));
        }

        Console.Out.WriteLine();
        Console.Out.WriteLine("DROGA HAMOWANIA, hamulec sluzbowy, krok 1/120 s");
        Console.Out.WriteLine(
            "v0[km/h]  wzor[m]   bez_oporow[m]  tunel[m]  powierzchnia[m]  dS_tunel  dS_pow  " +
            "dS_tunel_z_energii  dS_pow_z_energii");
        var conditions = RunConditions.Level(model, TrainLoad.Aw2);
        var speeds = new[] { 30.0, 40.0, 50.0, 60.0, 70.0, 80.0 };
        foreach (var row in new BrakingRun(model).ReferenceTable(conditions, speeds, model.DesignServiceBrakeMps2, step))
        {
            Console.Out.WriteLine(string.Create(
                Inv,
                $"{row.StartSpeedKmh,8:0}  {row.ClosedFormDistanceM,8:0.000}  {row.KinematicDistanceM,13:0.000}  " +
                $"{row.TunnelDistanceM,8:0.000}  {row.SurfaceDistanceM,15:0.000}  {row.TunnelShorteningM,8:0.000}  " +
                $"{row.SurfaceShorteningM,6:0.000}  {row.TunnelShorteningFromEnergyM,18:0.000}  " +
                $"{row.SurfaceShorteningFromEnergyM,16:0.000}"));
        }

        Console.Out.WriteLine();
        Console.Out.WriteLine("SOLVER PUNKTU HAMOWANIA (bez oporow, z ograniczeniem zrywu)");
        var top = Units.KmhToMps(model.DesignMaxSpeedKmh);
        Console.Out.WriteLine(string.Create(
            Inv,
            $"  minimum ze zrywu z {model.DesignMaxSpeedKmh:0} km/h do 0 = {solver.MinimumDistanceM(top, 0.0):0.000} m " +
            $"(b_progowe = {solver.PlateauCeilingMps2(top, 0.0):0.0000} m/s^2)"));
        foreach (var distance in new[] { 150.0, 200.0, 240.0, 300.0, 400.0 })
        {
            var point = solver.RequiredDeceleration(top, 0.0, distance);
            var back = solver.DistanceM(top, 0.0, point.DecelerationMps2);
            Console.Out.WriteLine(string.Create(
                Inv,
                $"  s = {distance,6:0.0} m -> b = {point.DecelerationMps2:0.000000} m/s^2, " +
                $"kontrola s(b) = {back:0.000000} m, |delta| = {Math.Abs(back - distance):0.000e+00} m"));
        }

        return 0;
    }

    // --- pomocnicze ---------------------------------------------------------------

    private static string? Option(string[] args, string name)
    {
        for (var i = 0; i < args.Length - 1; i++)
        {
            if (string.Equals(args[i], name, StringComparison.Ordinal))
            {
                return args[i + 1];
            }
        }

        return null;
    }
}
