using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class TrackEndStopTests
{
    [TestMethod]
    public void WeakManualBrakeCannotBypassTerminalIntervention()
    {
        var model = VehicleModel.M7;
        var conditions = RunConditions.Level(model, TrainLoad.Aw0);
        var controller = new TrainController(model);
        var solver = new BrakingPointSolver(model);
        var state = new DriveState(100, 8.0, 0.0, 0.0);
        var requested = new DriverCommand(0.0, 0.01);
        var required = TrackEndStop.RequiredBrake(state, 40.0, conditions, controller);
        Assert.IsTrue(required.Brake > requested.Brake,
            "test wymaga hamowania końcowego silniejszego niż ręczne 0,01");

        var engaged = false;
        var effective = TrackEndStop.ApproachCommand(state, 0.0, 40.0,
            conditions, controller, solver, 0.0, requested,
            terminalSection: true, ref engaged);

        Assert.IsTrue(engaged,
            "słaby hamulec maszynisty nie może zablokować interwencji końcowej");
        Assert.AreEqual(0.0, effective.Throttle,
            "interwencja końcowa musi odciąć ciąg");
        Assert.IsTrue(effective.Brake >= required.Brake,
            "hamowanie końcowe musi co najmniej dorównać wymaganej sile serwa");
    }

    [TestMethod]
    public void TerminalInterventionNeverWeakensDriversStrongerServiceBrake()
    {
        var model = VehicleModel.M7;
        var conditions = RunConditions.Level(model, TrainLoad.Aw0);
        var controller = new TrainController(model);
        var solver = new BrakingPointSolver(model);
        var engaged = true;
        var state = new DriveState(100, 8.0, 0.0, 0.0);
        var calculated = TrackEndStop.RequiredBrake(state, 100.0, conditions, controller);
        Assert.IsTrue(calculated.Brake < 1.0, "test wymaga słabszej komendy serwa");

        var effective = TrackEndStop.ApproachCommand(state, 0.0, 100.0,
            conditions, controller, solver, 1.0, DriverCommand.FullServiceBrake,
            terminalSection: true, ref engaged);

        Assert.AreEqual(0.0, effective.Throttle,
            "interwencja przed końcem toru musi odciąć ciąg");
        Assert.AreEqual(1.0, effective.Brake,
            "serwo nie może osłabić pełnego hamowania zadanego przez maszynistę");
    }

    [TestMethod]
    public void RepeatedPowerCannotMoveBeyondLastAxisPoint()
    {
        const double start = 94.0;
        const double end = 6686.739;
        var approaching = new DriveState(1, 20.0, end - start - 0.1, 0.0);
        Assert.AreEqual(approaching, TrackEndStop.Apply(approaching, start, end));

        var crossing = TrackEndStop.Apply(
            approaching with { Steps = 2, DistanceM = approaching.DistanceM + 0.2 },
            start, end);
        Assert.AreEqual(end - start, crossing.DistanceM, 1e-9);
        Assert.AreEqual(0.0, crossing.SpeedMps);
        Assert.IsTrue(TrackEndStop.Reached(start + crossing.DistanceM, end));

        for (var i = 0; i < 100; i++)
        {
            crossing = TrackEndStop.Apply(
                crossing with { Steps = crossing.Steps + 1, SpeedMps = 20.0,
                    DistanceM = crossing.DistanceM + 0.2 }, start, end);
            Assert.AreEqual(end - start, crossing.DistanceM, 1e-9);
            Assert.AreEqual(0.0, crossing.SpeedMps);
        }
    }
}
