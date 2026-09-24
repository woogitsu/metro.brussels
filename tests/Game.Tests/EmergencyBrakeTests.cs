using System;
using System.Globalization;
using System.Text.RegularExpressions;
using MetroBxl.Game.Input;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// DECYZJA 3 właściciela (05.09.2026): osobny klawisz hamulca awaryjnego robi
/// <b>dokładnie to samo</b>, co pełny hamulec służbowy, a HUD mówi to wprost.
///
/// <para><b>Czego te testy pilnują.</b> Nie tego, że wiersz istnieje — tego, że liczba
/// w nim jest liczbą, którą w tym samym kroku dostał kontroler. Napis o hamulcu jest
/// najgorszym możliwym miejscem na drugą kopię wartości: hamulec i tak hamuje, więc
/// rozjazd między napisem a poleceniem nie ma jak rzucić się w oczy. Ta sama rodzina
/// co <c>limit=80.0 km/h</c> w nagłówku, który przetrwał pięć miesięcy.</para>
/// </summary>
[TestClass]
public sealed class EmergencyBrakeTests
{
    private const double Rate = DesignAssumptions.ControlNotchRatePerSecond;

    private static DriverNotch Notch() => new(Rate);

    [TestMethod]
    public void E_during_autopilot_door_service_does_not_claim_the_driver_braked()
    {
        var axis = TrackAxis.FromJson(MetroBxl.Tests.Shared.KorzenRepozytorium.Tresc(
            "data", "track", "L1_A.json"));
        var plan = SignallingPlan.FromAxis(axis,
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            Units.KmhToMps(72.0), 0.0, ProtectionVariant.LegacyFixedBlock,
            requireRoute: false);
        var core = LineCore.M7(plan, axis,
            RunConditions.Level(VehicleModel.M7, TrainLoad.Aw2),
            new LineRunSettings(Units.KmhToMps(72.0), 8.0, 1.0, 5.0));
        core.Add(LineSession.CabTrainId, 0L);
        core.Step();
        var session = new LineSession(core, Notch(), FixedStep.Simulation);
        for (var i = 0; i < 40_000 &&
             session.Observed.Drive?.Phase != DoorPhase.Open; i++)
            session.Step(DriverKeys.None);

        Assert.AreEqual(DoorPhase.Open, session.Observed.Drive?.Phase,
            "autopilot must actually be serving a station with open doors");
        Assert.AreEqual(ControlOwner.Autopilot, session.Observed.Owner,
            "the train remains under autopilot before the ignored E input");
        session.Step(DriverKeys.EmergencyBraking);
        Assert.AreEqual(DoorPhase.Open, session.Observed.Drive?.Phase,
            "ignored E must not close the autopilot door cycle");
        Assert.AreEqual(string.Empty, EmergencyBrake.Notice(
            DriverKeys.EmergencyBraking, session.Command,
            session.Observed.Owner == ControlOwner.Driver),
            "E is ignored by the line session while autopilot owns the train");

        core.TakeControl(LineSession.CabTrainId);
        session.Step(DriverKeys.EmergencyBraking);
        Assert.AreEqual(ControlOwner.Driver, session.Observed.Owner,
            "the second E input belongs to the driver after takeover");
        Assert.AreEqual(DoorPhase.Open, session.Observed.Drive?.Phase,
            "braking does not interrupt an open door cycle");
        Assert.AreEqual(1.0, session.Command.Brake, 1e-12,
            "the driver's E applies full service braking");
        StringAssert.Contains(EmergencyBrake.Notice(
            DriverKeys.EmergencyBraking, session.Command,
            session.Observed.Owner == ControlOwner.Driver), "HAMULEC AWARYJNY",
            "the driver owned braking event is visible in the HUD");
    }

    /// <summary>Liczba hamulca wyciągnięta z gotowego wiersza HUD-u.</summary>
    private static double BrakeFromNotice(string notice)
    {
        var match = Regex.Match(notice, @"SŁUŻBOWY ([0-9]+(?:\.[0-9]+)?)");
        Assert.IsTrue(match.Success, $"wiersz nie podaje wartości hamulca: {notice}");
        return double.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Liczba w wierszu HUD-u jest liczbą z polecenia, a nie stałą wpisaną w tekst.
    /// Wiersz składa się z tego samego <see cref="DriverCommand"/>, który poszedł do
    /// kontrolera w tym kroku.
    /// </summary>
    [TestMethod]
    public void WierszHudMowiTaSamaLiczbeCoPolecenie()
    {
        var command = Notch().Advance(DriverKeys.EmergencyBraking, FixedStep.Simulation);

        var notice = EmergencyBrake.Notice(DriverKeys.EmergencyBraking, command);

        Assert.AreEqual(DriverCommand.FullServiceBrake, command);
        Assert.AreEqual(command.Brake, BrakeFromNotice(notice), 0.005, notice);
        Assert.AreEqual(1.0, BrakeFromNotice(notice), 0.005, notice);
    }

    /// <summary>
    /// Wiersz nazywa rzecz po imieniu: hamulec SŁUŻBOWY, i mówi wprost, że osobnego
    /// stopnia nie ma. To jest cała treść decyzji właściciela — gracz ma dostać gest,
    /// a nie fizykę, której model nie zna.
    /// </summary>
    [TestMethod]
    public void WierszHuduNieUdajeOsobnejFizyki()
    {
        var notice = EmergencyBrake.Notice(
            DriverKeys.EmergencyBraking, DriverCommand.FullServiceBrake);

        StringAssert.Contains(notice, "HAMULEC AWARYJNY", notice);
        StringAssert.Contains(notice, "SŁUŻBOWY", notice);
        StringAssert.Contains(notice, "nie ma osobnego stopnia", notice);
        StringAssert.Contains(notice, EmergencyBrake.KeyName, notice);
    }

    /// <summary>
    /// Bez trzymanego klawisza wiersz jest PUSTY, a nie „—" ani „hamulec awaryjny:
    /// nie". HUD składa go do wiersza nastawników, więc niepusty napis zmieniałby
    /// każdą klatkę każdego przebiegu — łącznie z tymi, które ogląda bramka wizualna.
    /// </summary>
    [TestMethod]
    public void BezKlawiszaWierszaNieMa()
    {
        foreach (var keys in new[]
                 {
                     DriverKeys.None, DriverKeys.Powering, DriverKeys.Braking,
                     DriverKeys.Coasting,
                 })
        {
            Assert.AreEqual(
                string.Empty,
                EmergencyBrake.Notice(keys, DriverCommand.FullServiceBrake),
                keys.Code());
        }
    }

    /// <summary>
    /// Pełny hamulec dojechany klawiszem S wygląda w poleceniu identycznie, ale wiersza
    /// NIE dostaje — bo wiersz mówi o geście, a nie o wartości hamulca. Gdyby zależał
    /// od samej liczby, pojawiałby się przy każdym zwykłym hamowaniu do zera.
    /// </summary>
    [TestMethod]
    public void ZwykleHamowanieDoPelnaNieDostajeWiersza()
    {
        var notch = Notch();
        var step = FixedStep.Simulation;
        for (var i = 0; i < (int)Math.Ceiling(step.Hertz / Rate) + 1; i++)
        {
            notch.Advance(DriverKeys.Braking, step);
        }

        Assert.AreEqual(DriverCommand.FullServiceBrake, notch.Command);
        Assert.AreEqual(
            string.Empty, EmergencyBrake.Notice(DriverKeys.Braking, notch.Command));
    }

    /// <summary>
    /// Opis sterowania wymienia nowy klawisz. <c>DriverInput.Help</c> jest dziś martwą
    /// stałą — nic jej nie woła i to jest osobne zadanie (G-3) — ale stała, która
    /// rozjeżdża się ze sterowaniem, jest gorsza niż jej brak: pokazana kiedyś, będzie
    /// kłamać o klawiszu, który istnieje.
    /// </summary>
    [TestMethod]
    public void OpisSterowaniaWymieniaKlawiszHamulcaAwaryjnego()
    {
        StringAssert.Contains(DriverInput.Help, EmergencyBrake.KeyName, DriverInput.Help);
        StringAssert.Contains(DriverInput.Help, "hamulec awaryjny", DriverInput.Help);
    }
}
