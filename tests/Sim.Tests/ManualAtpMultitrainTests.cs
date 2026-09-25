using System;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class ManualAtpMultitrainTests
{
    [TestMethod]
    public void ManualPowerIsActuallyBrakedByAtpWhileOtherTrainsRemainUnderAi()
    {
        double[] stations = { 0.0, 600.0, 1400.0, 2000.0 };
        var line = LineCore.M7(
            SignallingPlanTests.SyntheticPlan(requireRoute: false, stations),
            SignallingPlanTests.SyntheticAxis(stations),
            RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0),
            new LineRunSettings(Units.KmhToMps(90.0), 10.0, 1.0, 5.0),
            turnbackSeconds: 0.0,
            atp: true);
        line.Add("A", 0L);
        line.Add("B", 3600L);
        line.Add("C", 7200L);

        line.Step();
        line.TakeControl("A");
        var interventionOnA = false;
        var bStart = 0.0;
        var cStart = 0.0;
        var bProgress = 0.0;
        var cProgress = 0.0;
        var bEntered = false;
        var cEntered = false;

        for (var i = 0; i < 24_000 && !line.Finished; i++)
        {
            var a = line.Trains[0];
            if (a.OnLine && !a.Finished)
                line.Drive("A", DriverCommand.FullPower);

            line.Step((id, point) =>
            {
                if (id != "A" || a.Owner != ControlOwner.Driver ||
                    a.Protection is not { Action: not ProtectionAction.None } ||
                    point.Phase != DoorPhase.Closed || point.ChainageM >= 1400.0)
                    return;

                interventionOnA = true;
                Assert.AreEqual(DriverCommand.FullPower, a.DriverCommand,
                    "the driver must still be demanding full power");
                Assert.AreEqual(0.0, point.Command.Throttle, 1e-12,
                    "ATP intervention did not cut the driver's traction at the controller");
                Assert.IsTrue(point.Command.Brake > 0.0,
                    "ATP intervention did not apply braking at the controller");
            });

            foreach (var other in line.Trains.Skip(1))
            {
                Assert.AreEqual(ControlOwner.Autopilot, other.Owner,
                    $"{other.Id} lost AI control while A was manual");
                Assert.IsNull(other.DriverCommand, $"{other.Id} inherited A's command");
            }

            var b = line.Trains[1];
            if (b.OnLine)
            {
                if (!bEntered) { bEntered = true; bStart = b.Drive!.ChainageM; }
                bProgress = Math.Max(bProgress, b.Drive!.ChainageM - bStart);
            }

            var c = line.Trains[2];
            if (c.OnLine)
            {
                if (!cEntered) { cEntered = true; cStart = c.Drive!.ChainageM; }
                cProgress = Math.Max(cProgress, c.Drive!.ChainageM - cStart);
            }
        }

        Assert.IsTrue(interventionOnA,
            "the test never observed ATP intervene on manually driven A before the terminal");
        Assert.IsTrue(bEntered && bProgress > 100.0,
            $"AI train B did not make substantial progress: {bProgress:F3} m");
        Assert.IsTrue(cEntered && cProgress > 100.0,
            $"AI train C did not make substantial progress: {cProgress:F3} m");
        Assert.AreEqual(0, line.Signalling.Events.Count(e => e.Kind == SignallingEventKind.AuthorityViolation),
            "a train crossed its movement authority");
    }
}
