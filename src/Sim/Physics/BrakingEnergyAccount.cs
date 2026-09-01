using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Bilans energii przebiegu hamowania, liczony na obwodzie kół — druga, niezależna
/// droga do tej samej drogi hamowania.
///
/// <para>Równanie kroku przy zerowej trakcji brzmi
/// <c>m_ef · a = −F_oporu − m_ef · b − F_pochylenia</c>. Po przemnożeniu przez drogę
/// i zsumowaniu po całym przebiegu:</para>
///
/// <code>
/// ½·m_ef·(v₀² − v_k²) = W_oporów + W_hamulca + W_pochylenia + W_dyskretyzacji
/// </code>
///
/// <para><see cref="ResidualJ"/> jest różnicą obu stron. Zero oznacza, że droga
/// policzona przez całkowanie i energia policzona z sił mówią to samo.</para>
///
/// <para><b>To jest energia mechaniczna, nie odzysk.</b> Karta M7 potwierdza sam fakt
/// hamowania odzyskowego i nic ponadto — nie ma sprawności odzysku, nie ma podziału na
/// hamulec elektrodynamiczny i pneumatyczny, nie ma progu zanikania ED przy niskiej
/// prędkości. Dlatego <see cref="BrakeWorkJ"/> jest **całą** pracą hamulca, bez
/// rozbicia na człony, których nikt nie opublikował.</para>
/// </summary>
/// <param name="KineticLossJ">Ubytek energii kinetycznej masy efektywnej.</param>
/// <param name="ResistanceWorkJ">Praca oporów ruchu; zawsze dodatnia, zawsze pomaga hamować.</param>
/// <param name="BrakeWorkJ">Praca hamulca, <c>m_ef · Σ b·ds</c>.</param>
/// <param name="GradeWorkJ">Praca przeciw ciężarowi; ujemna przy jeździe z góry.</param>
/// <param name="DiscretizationWorkJ">
/// Człon schematu <c>½·m_ef·Σ(Δv)²</c>: krok liczy siły od prędkości z początku,
/// a drogę od prędkości z końca. Znika jak <c>dt</c> i jest wypisany osobno, zamiast
/// być rozmazany w tolerancji.
/// </param>
public readonly record struct BrakingEnergyAccount(
    double KineticLossJ,
    double ResistanceWorkJ,
    double BrakeWorkJ,
    double GradeWorkJ,
    double DiscretizationWorkJ)
{
    /// <summary>Domknięcie bilansu. Zero oznacza, że obie drogi dają tę samą liczbę.</summary>
    public double ResidualJ =>
        KineticLossJ - ResistanceWorkJ - BrakeWorkJ - GradeWorkJ - DiscretizationWorkJ;

    /// <summary>Domknięcie odniesione do ubytku energii kinetycznej; wielkość bez jednostki.</summary>
    public double RelativeResidual =>
        KineticLossJ == 0.0 ? 0.0 : Math.Abs(ResidualJ) / Math.Abs(KineticLossJ);

    /// <summary>
    /// Ile metrów drogi hamowania „załatwiły" opory ruchu: praca oporów podzielona
    /// przez siłę hamowania. To jest zamiana bilansu energii na metry, czyli druga
    /// droga do skrócenia drogi hamowania wobec modelu bez oporów.
    /// </summary>
    /// <param name="effectiveMassKg">Masa efektywna składu.</param>
    /// <param name="decelerationMps2">Opóźnienie na odcinku stałym.</param>
    public double ResistanceShorteningM(double effectiveMassKg, double decelerationMps2)
    {
        if (!double.IsFinite(effectiveMassKg) || effectiveMassKg <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(effectiveMassKg), effectiveMassKg, "Masa efektywna musi być dodatnia i skończona.");
        }

        if (!double.IsFinite(decelerationMps2) || decelerationMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(decelerationMps2), decelerationMps2, "Opóźnienie musi być dodatnie i skończone.");
        }

        return ResistanceWorkJ / (effectiveMassKg * decelerationMps2);
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"E_kin = {KineticLossJ:F3} J, opory = {ResistanceWorkJ:F3} J, hamulec = {BrakeWorkJ:F3} J, " +
        $"pochylenie = {GradeWorkJ:F3} J, dyskretyzacja = {DiscretizationWorkJ:F3} J, " +
        $"reszta = {ResidualJ:E3} J, względnie = {RelativeResidual:E3}");
}
