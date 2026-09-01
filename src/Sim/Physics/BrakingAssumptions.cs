using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Jedno założenie projektowe modelu hamowania.
///
/// Osobny typ, a nie <see cref="DesignParameter"/>, z tego samego powodu, dla którego
/// osobnym typem jest <c>ScenarioAssumption</c>: tamten wymaga ścieżki w
/// <c>data/vehicle/m7-spec.json</c>, a tych liczb w żadnym rejestrze **nie ma**.
/// Wpisanie im zmyślonej ścieżki byłoby dokładnie tym, przed czym ostrzega reguła 1
/// z <c>CLAUDE.md</c>. <c>data/</c> jest tylko do odczytu (reguła 6), więc dopisanie
/// ich do rejestru nie wchodzi w grę — należy do właściciela repo.
/// </summary>
/// <param name="Name">Nazwa właściwości <c>Design*</c> albo stałej w kodzie.</param>
/// <param name="Value">Wartość użyta przez model.</param>
/// <param name="Unit">Jednostka.</param>
/// <param name="Reason">Dlaczego taka i czego brakuje, żeby przestała być założeniem.</param>
public readonly record struct BrakingAssumption(string Name, double Value, string Unit, string Reason)
{
    /// <summary>Jedna linia raportu; kultura niezmienna, żeby wyjście nie zależało od maszyny.</summary>
    public override string ToString() =>
        string.Create(CultureInfo.InvariantCulture, $"{Name} = {Value:R} {Unit} — {Reason}");
}

/// <summary>
/// Wszystkie liczby modelu hamowania, dla których **nie ma źródła**, w jednym miejscu.
///
/// <para><b>Czego tu celowo nie ma.</b> W rejestrze źródeł nie ma rozdziału hamulca
/// elektrodynamicznego i pneumatycznego, nie ma charakterystyki zanikania ED przy
/// niskiej prędkości, nie ma udziału osi hamowanych i nie ma krzywych bezpieczeństwa
/// STIB. Z tej listy T-311 modeluje **wyłącznie udział osi hamowanych**, i to jako
/// jawny parametr o dwóch skrajnych wariantach, a nie jako jedną wybraną liczbę.
/// Rozdziału ED/P nie ma w kodzie w ogóle — model, który dzieli siłę hamowania na dwa
/// człony bez źródła na proporcję, wygląda dokładnie tak samo jak model prawdziwy.</para>
///
/// <para>Wartości z <c>docs/02-simulation.md</c> — 1,10 m/s² służbowe, 1,30 m/s²
/// awaryjne, zryw 0,75 m/s³, μ = 0,25 / 0,13 — są już <c>design_model</c> w rejestrze
/// M7 i mają wpisy w <see cref="VehicleModel.DesignAssumptions"/>. Tutaj się nie
/// powtarzają; tu są tylko liczby, których w rejestrze nie ma.</para>
/// </summary>
public static class BrakingAssumptions
{
    /// <summary>
    /// Górny kres udziału osi hamowanych: cała masa składu spoczywa na osiach, które
    /// hamują. Nie jest to pomiar układu hamulcowego M7 — jest to kres przedziału,
    /// w którym musi leżeć wartość prawdziwa.
    /// </summary>
    public const double AllAxlesBrakedMassFraction = 1.0;

    /// <summary>
    /// Katalog założeń modelu hamowania, w kolejności deklaracji — czyli stałej.
    /// Wartość wariantu „tylko osie napędne" pochodzi z rejestru M7
    /// (<c>parameters.powered_mass_fraction</c>), więc katalog buduje się z modelu.
    /// </summary>
    public static IReadOnlyList<BrakingAssumption> All { get; } = Build(VehicleModel.M7);

    /// <summary>Katalog dla zadanego modelu pojazdu.</summary>
    public static IReadOnlyList<BrakingAssumption> Build(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);

        return new[]
        {
            new BrakingAssumption(
                nameof(AllAxlesBrakedMassFraction), AllAxlesBrakedMassFraction, "-",
                "górny kres udziału osi hamowanych; STIB/CAF nie publikuje układu hamulcowego M7, " +
                "więc 1,0 jest granicą przedziału, a nie zmierzonym udziałem"),
            new BrakingAssumption(
                "PoweredAxlesBrakedMassFraction", model.DesignPoweredMassFraction, "-",
                "dolny wariant: hamują wyłącznie osie napędne. Liczba 4/6 pochodzi z " +
                "parameters.powered_mass_fraction, która sama jest design_model i w rejestrze " +
                "opisana jako legacy parametr limitu adhezji dla TRAKCJI — użycie jej dla hamowania " +
                "jest osobnym założeniem, nie przeniesieniem faktu"),
            new BrakingAssumption(
                "BrakeForceInertiaFactor", model.DesignEffectiveMassFactor, "-",
                "siła hamulca jest liczona jako m_ef · b, czyli od masy efektywnej — tak samo, jak " +
                "TrainController z T-400 zamienia opóźnienie na ruch. Brak danych o rozdziale " +
                "bezwładności wirującej na osie hamowane i niehamowane, więc raport podaje obie " +
                "skrajne interpretacje (z tym czynnikiem i bez niego)"),
        };
    }
}
