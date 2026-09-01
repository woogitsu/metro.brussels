using System;
using System.Globalization;
using System.IO;
using System.Collections.Generic;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Parametry pojazdu użyte przez fizykę, wczytane z canonical registry, nie wklejone.
///
/// Konwencja nazw jest przeniesiona z <c>tools/blender/m7_layout.py</c>: wartości ze
/// źródła pierwotnego mają nazwy zwykłe (<see cref="EmptyMassKg"/>), a każde założenie
/// projektowe ma przedrostek <c>Design</c> i wpis w <see cref="DesignAssumptions"/>.
/// Po nazwie właściwości widać więc od razu, czy liczba jest faktem o M7, czy decyzją
/// symulatora — dokładnie o to chodzi w regule 1 z <c>CLAUDE.md</c>.
/// </summary>
public sealed class VehicleModel
{
    private VehicleModel(VehicleRegistry registry)
    {
        Registry = registry;

        // --- spec: potwierdzone źródłem pierwotnym STIB -------------------------
        EmptyMassKg = registry.RequireValue("parameters.empty_mass_kg", ParameterStatus.Spec);
        InstalledPowerW = registry.RequireValue("parameters.traction_installed_power_kw", ParameterStatus.Spec) * 1000.0;

        // --- design_model: świadome założenia symulatora -------------------------
        DesignMaxSpeedKmh = Design("parameters.max_speed_kmh");
        DesignPoweredMassFraction = Design("parameters.powered_mass_fraction");
        DesignPassengerMassKg = Design("reference_model.passenger_mass_kg");
        DesignAw2Passengers = Design("reference_model.aw2_model_passengers");
        DesignAw2MassKg = Design("reference_model.aw2_model_mass_kg");
        DesignStartupForceN = Design("reference_model.startup_force_n");
        DesignServiceBrakeMps2 = Design("reference_model.service_brake_mps2");
        DesignEmergencyBrakeMps2 = Design("reference_model.emergency_brake_mps2");
        DesignJerkMps3 = Design("reference_model.jerk_mps3");
        DesignEffectiveMassFactor = Design("reference_model.effective_mass_factor");
        DesignAdhesionDry = Design("reference_model.adhesion_dry");
        DesignAdhesionWet = Design("reference_model.adhesion_wet");
        DesignDavisA = Design("reference_model.davis_a");
        DesignDavisB = Design("reference_model.davis_b");
        DesignDavisC = Design("reference_model.davis_c");
        DesignTunnelResistanceMultiplier = Design("reference_model.tunnel_resistance_multiplier");
        DesignSurfaceResistanceMultiplier = Design("reference_model.surface_resistance_multiplier");

        // Punkt przejścia jest liczony tak samo jak w referencji (P / F0), a nie
        // czytany z rejestru — inaczej model mógłby milcząco rozjechać się z własnymi
        // składnikami. Rejestr służy tu za kontrolę: gdyby ktoś zmienił F0 albo moc i
        // nie przeliczył wpisu pochodnego, rdzeń się nie uruchomi.
        DesignForcePowerTransitionSpeedMps = InstalledPowerW / DesignStartupForceN;
        RequireDerived(
            "reference_model.force_power_transition_speed_kmh",
            Units.MpsToKmh(DesignForcePowerTransitionSpeedMps),
            RegistryConsistencyToleranceKmh);

        // Masa modelowa AW2 też ma w rejestrze swój wzór; sprawdzamy, że wpis i
        // składniki nadal się zgadzają.
        RequireDerived(
            "reference_model.aw2_model_mass_kg",
            EmptyMassKg + (DesignAw2Passengers * DesignPassengerMassKg),
            RegistryConsistencyToleranceKg);

        DesignAssumptions = BuildDesignAssumptions();

        double Design(string path) => registry.RequireValue(path, ParameterStatus.DesignModel);

        void RequireDerived(string path, double computed, double tolerance)
        {
            var stored = registry.RequireValue(path, ParameterStatus.DesignModel);
            if (Math.Abs(stored - computed) > tolerance)
            {
                throw new InvalidDataException(string.Create(
                    CultureInfo.InvariantCulture,
                    $"Wpis pochodny '{path}' = {stored:R} nie zgadza się z wartością wyliczoną ze składników = {computed:R}."));
            }
        }
    }

    /// <summary>
    /// Tolerancja kontroli spójności wpisów pochodnych w km/h. Wpis w rejestrze
    /// powstał z tego samego dzielenia, więc dopuszczalna jest wyłącznie różnica
    /// ostatnich bitów mantysy, a nie zaokrąglenie liczby w dokumencie.
    /// </summary>
    public const double RegistryConsistencyToleranceKmh = 1e-12;

    /// <summary>Tolerancja kontroli spójności masy modelowej, w kg.</summary>
    public const double RegistryConsistencyToleranceKg = 1e-6;

    /// <summary>Model M7 z canonical registry.</summary>
    public static VehicleModel M7 { get; } = new(VehicleRegistry.M7);

    /// <summary>Rejestr, z którego pochodzą wszystkie liczby tego modelu.</summary>
    public VehicleRegistry Registry { get; }

    // --- spec ---------------------------------------------------------------

    /// <summary>Masa składu pustego, ~170 t. <c>spec</c>, STIB 13.07.2020, wartość przybliżona w źródle.</summary>
    public double EmptyMassKg { get; }

    /// <summary>Moc zainstalowana trakcji, 16 × 135 kW = 2160 kW. <c>spec</c>, STIB 13.07.2020.</summary>
    public double InstalledPowerW { get; }

    // --- design_model -------------------------------------------------------

    /// <summary>Prędkość maksymalna używana przez model. Brak potwierdzonego Vmax M7.</summary>
    public double DesignMaxSpeedKmh { get; }

    /// <summary>Udział masy napędzanej 4/6, wyłącznie do limitu przyczepności.</summary>
    public double DesignPoweredMassFraction { get; }

    /// <summary>Masa pasażera przyjęta do modelu obciążenia.</summary>
    public double DesignPassengerMassKg { get; }

    /// <summary>Liczba pasażerów w modelowym obciążeniu AW2.</summary>
    public double DesignAw2Passengers { get; }

    /// <summary>Masa modelowa AW2. Nie istnieje publiczna definicja AW2 dla M7.</summary>
    public double DesignAw2MassKg { get; }

    /// <summary>Siła rozruchu F0 = 248,9 kN. Kalibracja modelu, nie dana CAF/STIB.</summary>
    public double DesignStartupForceN { get; }

    /// <summary>
    /// Punkt przejścia siła stała → moc stała, w m/s. Pochodna: moc zainstalowana
    /// (<c>spec</c>) podzielona przez F0 (<c>design_model</c>), więc sama jest
    /// <c>design_model</c>. To nie jest prędkość bazowa M7.
    /// </summary>
    public double DesignForcePowerTransitionSpeedMps { get; }

    /// <summary>Hamowanie służbowe 1,10 m/s².</summary>
    public double DesignServiceBrakeMps2 { get; }

    /// <summary>Hamowanie awaryjne 1,30 m/s².</summary>
    public double DesignEmergencyBrakeMps2 { get; }

    /// <summary>Ograniczenie zrywu 0,75 m/s³.</summary>
    public double DesignJerkMps3 { get; }

    /// <summary>Współczynnik mas wirujących 1,08.</summary>
    public double DesignEffectiveMassFactor { get; }

    /// <summary>Przyczepność na suchej szynie, μ = 0,25.</summary>
    public double DesignAdhesionDry { get; }

    /// <summary>Przyczepność na mokrej szynie, μ = 0,13.</summary>
    public double DesignAdhesionWet { get; }

    /// <summary>Wyraz stały wzoru Davisa, kgf/t.</summary>
    public double DesignDavisA { get; }

    /// <summary>Wyraz liniowy wzoru Davisa, kgf/t na km/h.</summary>
    public double DesignDavisB { get; }

    /// <summary>Wyraz kwadratowy wzoru Davisa, kgf/t na (km/h)².</summary>
    public double DesignDavisC { get; }

    /// <summary>Mnożnik oporu aerodynamicznego w tunelu, c = 1,40.</summary>
    public double DesignTunnelResistanceMultiplier { get; }

    /// <summary>Mnożnik oporu aerodynamicznego na powierzchni, c = 1,00.</summary>
    public double DesignSurfaceResistanceMultiplier { get; }

    /// <summary>
    /// Pełna lista założeń projektowych modelu — odpowiednik <c>DESIGN_ASSUMPTIONS</c>
    /// z <c>tools/blender/m7_layout.py</c>. Kolejność jest kolejnością deklaracji, czyli stała.
    /// </summary>
    public IReadOnlyList<DesignParameter> DesignAssumptions { get; }

    /// <summary>
    /// Masa dla zadanego obciążenia modelowego. AW0 jest <c>spec</c>, AW2 nie —
    /// dlatego to dwie różne liczby o dwóch różnych statusach, a nie jeden „parametr masy".
    /// </summary>
    public double MassKg(TrainLoad load) => load switch
    {
        TrainLoad.Aw0 => EmptyMassKg,
        TrainLoad.Aw2 => DesignAw2MassKg,
        _ => throw new ArgumentOutOfRangeException(nameof(load), load, "Nieznane obciążenie składu."),
    };

    /// <summary>Przyczepność dla stanu szyny.</summary>
    public double Adhesion(RailCondition condition) => condition switch
    {
        RailCondition.Dry => DesignAdhesionDry,
        RailCondition.Wet => DesignAdhesionWet,
        _ => throw new ArgumentOutOfRangeException(nameof(condition), condition, "Nieznany stan szyny."),
    };

    /// <summary>Masa efektywna: masa rzeczywista razy współczynnik mas wirujących.</summary>
    public double EffectiveMassKg(double massKg) => massKg * DesignEffectiveMassFactor;

    private IReadOnlyList<DesignParameter> BuildDesignAssumptions() => new[]
    {
        new DesignParameter(nameof(DesignMaxSpeedKmh), "parameters.max_speed_kmh", DesignMaxSpeedKmh,
            "prędkość maksymalna modelu; audyt T-904 nie znalazł źródła pierwotnego na Vmax M7"),
        new DesignParameter(nameof(DesignPoweredMassFraction), "parameters.powered_mass_fraction", DesignPoweredMassFraction,
            "historyczne 4/6; używane wyłącznie przez limit przyczepności, nie opisuje układu napędu"),
        new DesignParameter(nameof(DesignPassengerMassKg), "reference_model.passenger_mass_kg", DesignPassengerMassKg,
            "masa pasażera w modelu obciążenia; STIB nie publikuje definicji obciążenia"),
        new DesignParameter(nameof(DesignAw2Passengers), "reference_model.aw2_model_passengers", DesignAw2Passengers,
            "pojemność manualna 742 użyta jako liczba pasażerów modelu; to nie jest definicja AW2"),
        new DesignParameter(nameof(DesignAw2MassKg), "reference_model.aw2_model_mass_kg", DesignAw2MassKg,
            "170 t + 742 × 70 kg; brak publicznej masy AW2 dla M7"),
        new DesignParameter(nameof(DesignStartupForceN), "reference_model.startup_force_n", DesignStartupForceN,
            "F0 = 248,9 kN z kalibracji modelu; charakterystyka siła–prędkość M7 nie jest publiczna"),
        new DesignParameter(nameof(DesignForcePowerTransitionSpeedMps), "reference_model.force_power_transition_speed_kmh", DesignForcePowerTransitionSpeedMps,
            "pochodna: 2160 kW / 248,9 kN; nie jest to prędkość bazowa pojazdu"),
        new DesignParameter(nameof(DesignServiceBrakeMps2), "reference_model.service_brake_mps2", DesignServiceBrakeMps2,
            "hamowanie służbowe; brak źródła pierwotnego"),
        new DesignParameter(nameof(DesignEmergencyBrakeMps2), "reference_model.emergency_brake_mps2", DesignEmergencyBrakeMps2,
            "hamowanie awaryjne; brak źródła pierwotnego"),
        new DesignParameter(nameof(DesignJerkMps3), "reference_model.jerk_mps3", DesignJerkMps3,
            "ograniczenie zrywu; brak źródła pierwotnego"),
        new DesignParameter(nameof(DesignEffectiveMassFactor), "reference_model.effective_mass_factor", DesignEffectiveMassFactor,
            "współczynnik mas wirujących; brak danych o wirnikach, przekładniach i kołach M7"),
        new DesignParameter(nameof(DesignAdhesionDry), "reference_model.adhesion_dry", DesignAdhesionDry,
            "przyczepność sucha; brak danych adhezyjnych STIB"),
        new DesignParameter(nameof(DesignAdhesionWet), "reference_model.adhesion_wet", DesignAdhesionWet,
            "przyczepność mokra; brak danych adhezyjnych STIB"),
        new DesignParameter(nameof(DesignDavisA), "reference_model.davis_a", DesignDavisA,
            "wyraz stały oporu ruchu; współczynnik do kalibracji, nie parametr CAF/STIB"),
        new DesignParameter(nameof(DesignDavisB), "reference_model.davis_b", DesignDavisB,
            "wyraz liniowy oporu ruchu; współczynnik do kalibracji"),
        new DesignParameter(nameof(DesignDavisC), "reference_model.davis_c", DesignDavisC,
            "wyraz kwadratowy oporu ruchu; współczynnik do kalibracji"),
        new DesignParameter(nameof(DesignTunnelResistanceMultiplier), "reference_model.tunnel_resistance_multiplier", DesignTunnelResistanceMultiplier,
            "mnożnik oporu w tunelu; brak pomiaru dla przekroju tuneli STIB"),
        new DesignParameter(nameof(DesignSurfaceResistanceMultiplier), "reference_model.surface_resistance_multiplier", DesignSurfaceResistanceMultiplier,
            "mnożnik oporu na powierzchni; wartość odniesienia dla mnożnika tunelowego"),
    };
}
