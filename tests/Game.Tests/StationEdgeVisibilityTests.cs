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
        const string contract = "Only the generated platform edge meshes receive the warning color";
        Assert.IsTrue(StationView.IsEdgeMeshName("Beekkant_positive_edge"), contract);
        Assert.IsTrue(StationView.IsEdgeMeshName("Beekkant_negative_edge"), contract);
        Assert.IsFalse(StationView.IsEdgeMeshName("Beekkant_positive_platform"), contract);
        Assert.IsFalse(StationView.IsEdgeMeshName("Beekkant_negative_platform"), contract);
        Assert.IsFalse(StationView.IsEdgeMeshName("Beekkant_edge_platform"), contract);
    }

    [TestMethod]
    public void AccessKitMeshesKeepDistinctVisualRoles()
    {
        var contract = nameof(AccessKitMeshesKeepDistinctVisualRoles);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_stairs0_00") == StationAccessKind.Stairs, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_stairs1_landing") == StationAccessKind.Stairs, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_lift") == StationAccessKind.Lift, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_mezzanine_near") == StationAccessKind.Mezzanine, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_corridor") == StationAccessKind.Corridor, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_portal") == StationAccessKind.Portal, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_positive_platform") == StationAccessKind.None, contract);
        Assert.IsTrue(StationView.AccessKindForMesh("Beekkant_positive_edge") == StationAccessKind.None, contract);
    }
}
