using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Bilans energii przebiegu, liczony na obwodzie kół.
///
/// To jest energia mechaniczna, a nie pobór z sieci: model nie zna sprawności
/// przetwornic, silników i przekładni, poboru potrzeb własnych ani odzysku przy
/// hamowaniu, bo żadnej z tych wielkości nie ma w źródłach STIB. Karta M7 potwierdza
/// tylko sam fakt odzysku energii hamowania.
///
/// <see cref="ResidualJ"/> jest drugą, niezależną drogą do tego samego wyniku:
/// praca trakcji musi się równać sumie przyrostu energii kinetycznej, pracy oporów,
/// pracy na pochyleniu i jawnie policzonego członu dyskretyzacji. Rozjazd między
/// tymi dwiema drogami jest informacją o schemacie całkowania, a nie szumem.
/// </summary>
/// <param name="TractionWorkJ">Praca siły pociągowej.</param>
/// <param name="ResistanceWorkJ">Praca oporów ruchu; zawsze dodatnia.</param>
/// <param name="GradeWorkJ">Praca przeciw ciężarowi; ujemna przy jeździe z góry.</param>
/// <param name="KineticEnergyJ">Energia kinetyczna masy efektywnej na końcu przebiegu.</param>
/// <param name="DiscretizationWorkJ">
/// Człon schematu: <c>½ · m_ef · Σ(Δv)²</c>. Bierze się z liczenia pracy po prędkości
/// z końca kroku i znika jak <c>dt</c>.
/// </param>
/// <param name="ClampedWorkJ">
/// Praca, której model nie zamienił na ruch, bo obciął przyrost prędkości: przy
/// dojściu do prędkości docelowej (ostatni krok rozruchu) i przy zakazie ujemnego
/// przyspieszenia. To jest artefakt modelu, a nie strata fizyczna — prawdziwy
/// maszynista zdejmuje nastawnik przed osiągnięciem prędkości, model tnie nadmiar.
/// Wyodrębnienie tego członu jest jedynym sposobem, żeby bilans energii domykał się
/// do zera i dalej coś znaczył.
/// </param>
public readonly record struct EnergyAccount(
    double TractionWorkJ,
    double ResistanceWorkJ,
    double GradeWorkJ,
    double KineticEnergyJ,
    double DiscretizationWorkJ,
    double ClampedWorkJ)
{
    /// <summary>Domknięcie bilansu. Zero oznacza, że obie drogi dają tę samą liczbę.</summary>
    public double ResidualJ =>
        TractionWorkJ - ResistanceWorkJ - GradeWorkJ - KineticEnergyJ - DiscretizationWorkJ - ClampedWorkJ;

    /// <summary>Domknięcie odniesione do pracy trakcji; wielkość bez jednostki.</summary>
    public double RelativeResidual =>
        TractionWorkJ == 0.0 ? 0.0 : Math.Abs(ResidualJ) / Math.Abs(TractionWorkJ);

    /// <summary>Praca trakcji w kWh — do raportów energetycznych.</summary>
    public double TractionWorkKwh => TractionWorkJ / 3_600_000.0;

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"E_trakcji = {TractionWorkKwh:F4} kWh, opory = {ResistanceWorkJ / 1e6:F3} MJ, " +
        $"pochylenie = {GradeWorkJ / 1e6:F3} MJ, E_kin = {KineticEnergyJ / 1e6:F3} MJ, " +
        $"dyskretyzacja = {DiscretizationWorkJ:F1} J, obcięcie = {ClampedWorkJ:F1} J, " +
        $"reszta = {ResidualJ:E3} J");
}
