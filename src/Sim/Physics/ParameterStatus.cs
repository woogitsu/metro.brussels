using System;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Klasyfikacja pochodzenia parametru, wprost z <c>docs/21-measured-vs-assumed.md</c>
/// i z pola <c>status</c> w <c>data/vehicle/m7-spec.json</c>.
/// </summary>
public enum ParameterStatus
{
    /// <summary>Wartość z oficjalnego źródła pierwotnego, z URL-em w rejestrze.</summary>
    Spec,

    /// <summary>Pomiar z oficjalnych danych, ale nie wymiar publikowany.</summary>
    Observed,

    /// <summary>Oszacowanie historyczne do weryfikacji lub usunięcia.</summary>
    Est,

    /// <summary>Świadome założenie symulatora. Nie jest faktem o brukselskim metrze.</summary>
    DesignModel,
}

/// <summary>Zamiana napisów z rejestru na <see cref="ParameterStatus"/>, bez tolerancji dla literówek.</summary>
public static class ParameterStatusParser
{
    /// <summary>
    /// Nieznany status jest błędem, a nie wartością domyślną: gdyby ktoś dopisał do
    /// rejestru nową klasę pochodzenia, rdzeń ma się zatrzymać, a nie po cichu uznać
    /// jej za założenie projektowe.
    /// </summary>
    public static ParameterStatus Parse(string status) => status switch
    {
        "spec" => ParameterStatus.Spec,
        "observed" => ParameterStatus.Observed,
        "est" => ParameterStatus.Est,
        "design_model" => ParameterStatus.DesignModel,
        _ => throw new FormatException($"Nieznany status parametru w rejestrze M7: '{status}'."),
    };

    /// <summary>Napis dokładnie taki, jaki stoi w rejestrze JSON.</summary>
    public static string ToRegistryString(ParameterStatus status) => status switch
    {
        ParameterStatus.Spec => "spec",
        ParameterStatus.Observed => "observed",
        ParameterStatus.Est => "est",
        ParameterStatus.DesignModel => "design_model",
        _ => throw new ArgumentOutOfRangeException(nameof(status), status, "Nieobsłużony status."),
    };
}
