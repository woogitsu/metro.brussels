namespace MetroBxl.Sim.Tests;

/// <summary>
/// Liczby wypisane przez <c>tools/physics/braking.py</c> na pełnej precyzji
/// (<c>repr()</c>, czyli round-trip <c>double</c>), a nie zaokrąglone jak w raporcie.
///
/// Ta sama rola i to samo uzasadnienie, co <see cref="PythonReference"/> dla T-310:
/// test rdzenia nie może wymagać interpretera ani ścieżki do repo, bo wtedy przestaje
/// być testem rdzenia. Kopia jest jawnie oznaczona — jeśli referencja się zmieni,
/// ten plik trzeba zaktualizować świadomie, zamiast patrzeć, jak test cicho zmienia
/// znaczenie.
///
/// <see cref="PythonReference"/> zostaje nietknięty: tamten jest zamrożonym
/// snapshotem parytetu T-310 i nie ma powodu go ruszać przy T-311.
/// </summary>
internal static class BrakingReference
{
    // --- sufit przyczepnościowy (b_max opóźnienia pudła, m/s²) --------------------

    /// <summary>Sucha szyna, wszystkie osie hamowane: μ = 0,25, f = 1,0.</summary>
    public const double CeilingDryAllAxlesMps2 = 2.27005787037037;

    /// <summary>Sucha szyna, tylko osie napędne: μ = 0,25, f = 4/6.</summary>
    public const double CeilingDryPoweredOnlyMps2 = 1.5133719135802468;

    /// <summary>Mokra szyna, wszystkie osie hamowane: μ = 0,13, f = 1,0.</summary>
    public const double CeilingWetAllAxlesMps2 = 1.1804300925925926;

    /// <summary>Mokra szyna, tylko osie napędne: μ = 0,13, f = 4/6.</summary>
    public const double CeilingWetPoweredOnlyMps2 = 0.7869533950617283;

    /// <summary>Ten sam sufit bez uwzględnienia mas wirujących: sucho, f = 1,0.</summary>
    public const double CeilingRigidDryAllAxlesMps2 = 2.4516625;

    /// <summary>Ten sam sufit bez uwzględnienia mas wirujących: mokro, f = 1,0.</summary>
    public const double CeilingRigidWetAllAxlesMps2 = 1.2748645;

    // --- progi krytyczne ----------------------------------------------------------

    /// <summary>Udział osi hamowanych potrzebny na 1,10 m/s² na suchej szynie.</summary>
    public const double RequiredFractionServiceDry = 0.4845691444071116;

    /// <summary>Udział osi hamowanych potrzebny na 1,10 m/s² na mokrej szynie.</summary>
    public const double RequiredFractionServiceWet = 0.9318637392444453;

    /// <summary>Udział osi hamowanych potrzebny na 1,30 m/s² na suchej szynie.</summary>
    public const double RequiredFractionEmergencyDry = 0.5726726252084046;

    /// <summary>
    /// Udział osi hamowanych potrzebny na 1,30 m/s² na mokrej szynie — **powyżej 1**,
    /// czyli żądanie jest nieosiągalne przy każdym układzie hamulcowym.
    /// </summary>
    public const double RequiredFractionEmergencyWet = 1.1012935100161625;

    /// <summary>Przyczepność potrzebna na 1,10 m/s² przy f = 1,0.</summary>
    public const double RequiredAdhesionService = 0.1211422861017779;

    /// <summary>Przyczepność potrzebna na 1,30 m/s² przy f = 1,0.</summary>
    public const double RequiredAdhesionEmergency = 0.14316815630210114;

    // --- solver punktu hamowania ---------------------------------------------------

    /// <summary>Opóźnienie progowe zrywu z 80 km/h do zatrzymania: √(2·j·Δv).</summary>
    public const double PlateauCeiling80Mps2 = 5.773502691896257;

    /// <summary>
    /// Najkrótsza droga hamowania z 80 km/h dopuszczona przez sam zryw 0,75 m/s³,
    /// bez względu na siłę hamulca.
    /// </summary>
    public const double MinimumDistance80M = 114.04449761770385;

    /// <summary>Opóźnienie potrzebne na zatrzymanie z 80 km/h na 150 m.</summary>
    public const double RequiredDeceleration80On150M = 2.0539735726130854;

    /// <summary>Opóźnienie potrzebne na zatrzymanie z 80 km/h na 200 m.</summary>
    public const double RequiredDeceleration80On200M = 1.3728636956799676;

    /// <summary>Opóźnienie potrzebne na zatrzymanie z 80 km/h na 240 m.</summary>
    public const double RequiredDeceleration80On240M = 1.1035188875716144;

    /// <summary>Opóźnienie potrzebne na zatrzymanie z 80 km/h na 300 m.</summary>
    public const double RequiredDeceleration80On300M = 0.8593815362888466;

    /// <summary>Opóźnienie potrzebne na zatrzymanie z 80 km/h na 400 m.</summary>
    public const double RequiredDeceleration80On400M = 0.6320502299465222;

    // --- tablica dróg hamowania, hamulec służbowy 1,10 m/s², krok 1/120 s ---------

    /// <summary>Prędkości początkowe tablicy referencyjnej, km/h.</summary>
    public static double[] SpeedsKmh { get; } = { 30.0, 40.0, 50.0, 60.0, 70.0, 80.0 };

    /// <summary>Droga ze wzoru zamkniętego solvera (granica dt → 0, bez oporów), m.</summary>
    public static double[] ClosedFormM { get; } =
    {
        37.578175084175086, 64.16627833894499, 97.76897194163861,
        138.38625589225592, 186.01813019079685, 240.6645948372615,
    };

    /// <summary>Droga modelu kinematycznego T-310, krokiem stałym, bez oporów, m.</summary>
    public static double[] KinematicM { get; } =
    {
        37.5087430555562, 64.07369791666629, 97.65324305555346,
        138.247378472218, 185.856104166668, 240.47942013889713,
    };

    /// <summary>Droga z oporami Davisa w tunelu (c = 1,40), m.</summary>
    public static double[] TunnelM { get; } =
    {
        36.92758439010127, 62.96921335874769, 95.75983912124623,
        135.21634084616534, 181.2411080175386, 233.72277949490203,
    };

    /// <summary>Droga z oporami Davisa na powierzchni (c = 1,00), m.</summary>
    public static double[] SurfaceM { get; } =
    {
        36.94971949295876, 63.0339084390711, 95.90979873600335,
        135.51561262426236, 181.7788474261521, 234.6167561676803,
    };

    /// <summary>Liczba kroków przebiegu kinematycznego przy dt = 1/120 s.</summary>
    public static long[] KinematicSteps { get; } = { 997, 1300, 1603, 1906, 2209, 2512 };
}
