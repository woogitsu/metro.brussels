using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Sufit przyczepnościowy hamowania: ile opóźnienia da się w ogóle przenieść przez
/// styk koło–szyna.
///
/// <para><b>Skąd wzór.</b> <c>docs/02-simulation.md</c> daje dla TRAKCJI ograniczenie
/// <c>F ≤ μ · m · (4/6) · g</c> i nazywa 4/6 „legacy parametrem limitu adhezji".
/// Dla hamowania obowiązuje ten sam styk i ta sama fizyka, ale **inny udział osi**:
/// hamować może więcej osi, niż jest napędzanych. Udziału osi hamowanych M7 nie ma
/// w żadnym źródle, więc jest tu jawnym parametrem <c>design_assumption</c>
/// (<see cref="BrakingAssumptions"/>), z dwoma wariantami skrajnymi zamiast jednej
/// wybranej liczby.</para>
///
/// <para><b>Dwie interpretacje mas wirujących, obie policzone.</b> Siła na styku
/// jest ograniczona przez <c>μ · m · f · g</c>, gdzie <c>m</c> to masa rzeczywista
/// (masa wirująca nie dociska szyny). Opóźnienie **pudła** wychodzi z podzielenia tej
/// siły przez masę efektywną <c>m · λ</c>, bo tak samo liczy ruch
/// <see cref="Train.TrainController"/>: <see cref="MaxDecelerationMps2"/>. Gdyby zignorować
/// bezwładność wirującą, wyszłoby o <c>λ</c> więcej:
/// <see cref="MaxRigidBodyDecelerationMps2"/>. Rozdziału bezwładności wirującej na osie
/// hamowane i niehamowane nie ma w danych, więc model nie wybiera za czytelnika —
/// wystawia obie liczby, a raport podaje wnioski dla obu.</para>
///
/// <para><b>Masa się skraca.</b> Sufit opóźnienia nie zależy od masy składu:
/// <c>b_max = μ · f · g / λ</c>. AW0 i AW2 mają ten sam sufit i różnią się wyłącznie
/// siłą, jaką trzeba przenieść.</para>
/// </summary>
public sealed class BrakeAdhesionLimit
{
    /// <summary>
    /// Sufit przyczepnościowy dla zadanego udziału osi hamowanych.
    /// </summary>
    /// <param name="brakedMassFraction">Udział masy składu spoczywającej na osiach hamowanych, w (0, 1].</param>
    /// <param name="effectiveMassFactor">Współczynnik mas wirujących λ z modelu pojazdu.</param>
    /// <param name="variant">Nazwa wariantu do raportów; nie wpływa na obliczenia.</param>
    public BrakeAdhesionLimit(double brakedMassFraction, double effectiveMassFactor, string variant)
    {
        if (!double.IsFinite(brakedMassFraction) || brakedMassFraction <= 0.0 || brakedMassFraction > 1.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(brakedMassFraction), brakedMassFraction,
                "Udział osi hamowanych musi leżeć w (0, 1] — powyżej 1 nie ma już masy do oparcia o szynę.");
        }

        if (!double.IsFinite(effectiveMassFactor) || effectiveMassFactor <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(effectiveMassFactor), effectiveMassFactor,
                "Współczynnik mas wirujących musi być dodatni i skończony.");
        }

        ArgumentNullException.ThrowIfNull(variant);

        DesignBrakedMassFraction = brakedMassFraction;
        EffectiveMassFactor = effectiveMassFactor;
        Variant = variant;
    }

    /// <summary>
    /// Wariant górny: hamują wszystkie osie, cała masa składu pracuje na przyczepność.
    /// </summary>
    public static BrakeAdhesionLimit AllAxles(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        return new BrakeAdhesionLimit(
            BrakingAssumptions.AllAxlesBrakedMassFraction, model.DesignEffectiveMassFactor, "all-axles");
    }

    /// <summary>
    /// Wariant dolny: hamują wyłącznie osie napędne — czyli tyle, ile mógłby oddać sam
    /// hamulec elektrodynamiczny. Udział 4/6 pochodzi z rejestru, gdzie jest
    /// <c>design_model</c> opisany jako parametr limitu adhezji **dla trakcji**;
    /// przeniesienie go na hamowanie jest osobnym założeniem, nie faktem.
    /// </summary>
    public static BrakeAdhesionLimit PoweredAxlesOnly(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        return new BrakeAdhesionLimit(
            model.DesignPoweredMassFraction, model.DesignEffectiveMassFactor, "powered-axles-only");
    }

    /// <summary>Nazwa wariantu; wyłącznie do raportów.</summary>
    public string Variant { get; }

    /// <summary>Udział masy na osiach hamowanych. <c>design_assumption</c>, brak źródła.</summary>
    public double DesignBrakedMassFraction { get; }

    /// <summary>Współczynnik mas wirujących użyty przy zamianie siły na opóźnienie pudła.</summary>
    public double EffectiveMassFactor { get; }

    /// <summary>Katalog założeń, na których stoi ten sufit.</summary>
    public IReadOnlyList<BrakingAssumption> Assumptions => BrakingAssumptions.All;

    /// <summary>
    /// Największa siła hamowania, jaką da się przenieść przez styk koło–szyna:
    /// <c>μ · m · f · g</c>. Masa jest rzeczywista, bo masa wirująca nie dociska szyny.
    /// </summary>
    public double MaxBrakeForceN(double massKg, double adhesion)
    {
        RequireMass(massKg);
        RequireAdhesion(adhesion);
        return adhesion * massKg * DesignBrakedMassFraction * Units.StandardGravityMps2;
    }

    /// <summary>
    /// Sufit opóźnienia pudła: <c>μ · f · g / λ</c>. Nie zależy od masy składu.
    /// To jest liczba porównywalna z 1,10 i 1,30 m/s² z <c>docs/02-simulation.md</c>,
    /// bo <see cref="Train.TrainController"/> zamienia opóźnienie na ruch przez masę efektywną.
    /// </summary>
    public double MaxDecelerationMps2(double adhesion)
    {
        RequireAdhesion(adhesion);
        return adhesion * DesignBrakedMassFraction * Units.StandardGravityMps2 / EffectiveMassFactor;
    }

    /// <summary>
    /// Sufit opóźnienia przy zignorowaniu bezwładności wirującej: <c>μ · f · g</c>.
    /// Wariant kontrolny — pokazuje, o ile wnioski zależą od decyzji o masach wirujących.
    /// </summary>
    public double MaxRigidBodyDecelerationMps2(double adhesion)
    {
        RequireAdhesion(adhesion);
        return adhesion * DesignBrakedMassFraction * Units.StandardGravityMps2;
    }

    /// <summary>Opóźnienie, które naprawdę da się uzyskać: mniejsze z żądanego i z sufitu.</summary>
    public double AchievableDecelerationMps2(double demandMps2, double adhesion)
    {
        RequireDemand(demandMps2);
        return Math.Min(demandMps2, MaxDecelerationMps2(adhesion));
    }

    /// <summary>Czy żądane opóźnienie przekracza sufit przyczepnościowy.</summary>
    public bool IsAdhesionLimited(double demandMps2, double adhesion)
    {
        RequireDemand(demandMps2);
        return MaxDecelerationMps2(adhesion) < demandMps2;
    }

    /// <summary>
    /// Najmniejszy udział osi hamowanych, przy którym żądane opóźnienie jest jeszcze
    /// osiągalne: <c>f = b · λ / (μ · g)</c>. Wynik powyżej 1 znaczy, że żądanie jest
    /// **nieosiągalne przy każdym układzie hamulcowym** — nie ma tylu osi.
    /// </summary>
    public double RequiredBrakedMassFraction(double demandMps2, double adhesion)
    {
        RequireDemand(demandMps2);
        RequireAdhesion(adhesion);
        return demandMps2 * EffectiveMassFactor / (adhesion * Units.StandardGravityMps2);
    }

    /// <summary>
    /// Najmniejsza przyczepność, przy której żądane opóźnienie jest osiągalne przy
    /// tym udziale osi: <c>μ = b · λ / (f · g)</c>.
    /// </summary>
    public double RequiredAdhesion(double demandMps2)
    {
        RequireDemand(demandMps2);
        return demandMps2 * EffectiveMassFactor / (DesignBrakedMassFraction * Units.StandardGravityMps2);
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Variant}: f = {DesignBrakedMassFraction:R}, λ = {EffectiveMassFactor:R}");

    private static void RequireAdhesion(double adhesion)
    {
        if (!double.IsFinite(adhesion) || adhesion <= 0.0 || adhesion > 1.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(adhesion), adhesion, "Współczynnik przyczepności musi leżeć w (0, 1].");
        }
    }

    private static void RequireMass(double massKg)
    {
        if (!double.IsFinite(massKg) || massKg <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(massKg), massKg, "Masa składu musi być dodatnia i skończona.");
        }
    }

    private static void RequireDemand(double demandMps2)
    {
        if (!double.IsFinite(demandMps2) || demandMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(demandMps2), demandMps2, "Żądane opóźnienie musi być dodatnie i skończone.");
        }
    }
}
