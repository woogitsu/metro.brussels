using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using MetroBxl.Game.Assets;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

[TestClass]
public sealed class ChunkAssetCoverageTests
{
    private static ChunkManifest Manifest => ChunkManifest.FromJson(File.ReadAllText(
        Path.Combine(AppContext.BaseDirectory, "fixtures", "L1_A-chunks.json")));

    private static HashSet<string> TunnelFiles(ChunkManifest manifest) =>
        manifest.Chunks.SelectMany(chunk => chunk.Lods.Select(lod => lod.File))
            .ToHashSet(StringComparer.Ordinal);

    [TestMethod]
    public void MissingLaterLodIsReportedBeforeStreamingReachesIt()
    {
        var manifest = Manifest;
        var files = TunnelFiles(manifest);
        var laterLod = manifest.Chunks[^1].Lods[^1].File;
        files.Remove(laterLod);

        var result = ChunkAssetCoverage.Check(manifest, "assets",
            path => files.Contains(Path.GetFileName(path)));

        Assert.IsFalse(result.HasDetails, "No detail GLBs were supplied.");
        CollectionAssert.AreEqual(new[] { laterLod }, result.Missing.ToArray(),
            "A missing late LOD must fail before the train reaches that chunk.");
    }

    [TestMethod]
    public void PartialDetailSetIsRejectedButOldAssetSetWithoutDetailsIsAllowed()
    {
        var manifest = Manifest;
        var files = TunnelFiles(manifest);
        var withoutDetails = ChunkAssetCoverage.Check(manifest, "assets",
            path => files.Contains(Path.GetFileName(path)));
        Assert.IsFalse(withoutDetails.HasDetails, "Older asset sets may omit every detail GLB.");
        Assert.AreEqual(0, withoutDetails.Missing.Count,
            "An older complete asset set remains playable.");

        files.Add(manifest.Chunks[0].Id + "_detail.glb");
        var partial = ChunkAssetCoverage.Check(manifest, "assets",
            path => files.Contains(Path.GetFileName(path)));
        Assert.IsTrue(partial.HasDetails, "One detail GLB opts into the complete detail set.");
        Assert.AreEqual(manifest.Chunks.Count - 1, partial.Missing.Count,
            "Every other chunk must then report its missing detail GLB.");

        foreach (var chunk in manifest.Chunks)
            files.Add(chunk.Id + "_detail.glb");
        var complete = ChunkAssetCoverage.Check(manifest, "assets",
            path => files.Contains(Path.GetFileName(path)));
        Assert.IsTrue(complete.HasDetails, "Every chunk now has a detail GLB.");
        Assert.AreEqual(0, complete.Missing.Count,
            "A complete detail set and all LODs must pass.");
    }
}
