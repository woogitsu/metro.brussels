using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class TrackEndStopTests
{
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
