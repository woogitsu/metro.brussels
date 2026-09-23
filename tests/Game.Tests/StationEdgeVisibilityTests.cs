using MetroBxl.Game.World;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

[TestClass]
public sealed class StationEdgeVisibilityTests
{
    [TestMethod]
    public void OnlyWarningStripMeshesReceiveTheEdgeTreatment()
    {
        // station_kit.py exports both sides with distinct platform and edge meshes.
        Assert.IsTrue(StationView.IsEdgeMeshName("Beekkant_positive_edge"));
        Assert.IsTrue(StationView.IsEdgeMeshName("Beekkant_negative_edge"));
        Assert.IsFalse(StationView.IsEdgeMeshName("Beekkant_positive_platform"));
        Assert.IsFalse(StationView.IsEdgeMeshName("Beekkant_negative_platform"));
        Assert.IsFalse(StationView.IsEdgeMeshName("Beekkant_edge_platform"));
    }
}
