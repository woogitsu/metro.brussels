namespace MetroBxl.Sim.Tests;

/// <summary>
/// Liczby wypisane przez <c>tools/physics/reference.py</c> na pełnej precyzji
/// (<c>repr()</c>, czyli round-trip double), a nie zaokrąglone do jednego miejsca
/// jak w raporcie referencji.
///
/// Dlaczego kopia w kodzie, a nie wywołanie Pythona z testu: test rdzenia nie może
/// wymagać interpretera ani ścieżki do repo, bo wtedy przestaje być testem rdzenia,
/// a CI .NET musiałoby instalować Pythona. Kopia jest za to jawnie oznaczona i
/// pilnowana — jeśli referencja się zmieni, ten plik trzeba zaktualizować świadomie,
/// zamiast obserwować, jak test cicho zmienia znaczenie.
///
/// Snapshot z <c>python3 tools/physics/reference.py</c>, model po migracji T-904
/// (AW0 = 170 t, moc 2160 kW), krok 1/120 s.
/// </summary>
internal static class PythonReference
{
    /// <summary>Krok referencji.</summary>
    public const int StepsPerSecond = 120;

    /// <summary>Punkt przejścia F0 → P w m/s: 2160 kW / 248,9 kN.</summary>
    public const double TransitionSpeedMps = 8.678184009642427;

    /// <summary>Punkt przejścia F0 → P w km/h.</summary>
    public const double TransitionSpeedKmh = 31.241462434712737;

    /// <summary>0 → 80 km/h, AW0, tunel, sucho, poziom.</summary>
    public const double Accel80Aw0TimeS = 25.191666666665878;

    /// <inheritdoc cref="Accel80Aw0TimeS"/>
    public const double Accel80Aw0DistanceM = 337.47813150560165;

    /// <summary>Liczba kroków przebiegu 0 → 80 km/h AW0.</summary>
    public const long Accel80Aw0Steps = 3023;

    /// <summary>0 → 80 km/h, AW2, tunel, sucho, poziom.</summary>
    public const double Accel80Aw2TimeS = 33.31666666666542;

    /// <inheritdoc cref="Accel80Aw2TimeS"/>
    public const double Accel80Aw2DistanceM = 447.9202581360521;

    /// <summary>Liczba kroków przebiegu 0 → 80 km/h AW2.</summary>
    public const long Accel80Aw2Steps = 3998;

    /// <summary>Hamowanie służbowe 80 → 0. Model kinematyczny, więc AW0 i AW2 mają tę samą wartość.</summary>
    public const double ServiceBrake80TimeS = 20.933333333332786;

    /// <inheritdoc cref="ServiceBrake80TimeS"/>
    public const double ServiceBrake80DistanceM = 240.47942013889713;

    /// <summary>Liczba kroków hamowania służbowego 80 → 0.</summary>
    public const long ServiceBrake80Steps = 2512;

    /// <summary>Hamowanie awaryjne 80 → 0, ten sam model kinematyczny.</summary>
    public const double EmergencyBrake80TimeS = 17.958333333332956;

    /// <inheritdoc cref="EmergencyBrake80TimeS"/>
    public const double EmergencyBrake80DistanceM = 208.844868055545;

    /// <summary>0 → 80 km/h, AW2, pochylenie +3%.</summary>
    public const double Accel80Aw2UphillTimeS = 70.7333333333357;

    /// <inheritdoc cref="Accel80Aw2UphillTimeS"/>
    public const double Accel80Aw2UphillDistanceM = 1096.089866682524;

    /// <summary>0 → 80 km/h, AW2, pochylenie −3%.</summary>
    public const double Accel80Aw2DownhillTimeS = 22.966666666666004;

    /// <inheritdoc cref="Accel80Aw2DownhillTimeS"/>
    public const double Accel80Aw2DownhillDistanceM = 292.7570916187659;

    /// <summary>0 → 80 km/h, AW0, mokra szyna μ = 0,13.</summary>
    public const double Accel80Aw0WetTimeS = 31.72499999999884;

    /// <inheritdoc cref="Accel80Aw0WetTimeS"/>
    public const double Accel80Aw0WetDistanceM = 377.1278853474714;

    /// <summary>Opór ruchu AW0 przy 80 km/h w tunelu, w niutonach.</summary>
    public const double DavisTunnelAw080KmhN = 8529.039637999998;

    /// <summary>Opór ruchu AW0 przy 80 km/h na powierzchni, w niutonach.</summary>
    public const double DavisSurfaceAw080KmhN = 7035.29071;

    /// <summary>Limit przyczepnościowy AW0 na suchej szynie, w niutonach.</summary>
    public const double AdhesionLimitAw0DryN = 277855.0833333333;

    /// <summary>Limit przyczepnościowy AW2 na mokrej szynie, w niutonach.</summary>
    public const double AdhesionLimitAw2WetN = 188628.95141999997;
}
