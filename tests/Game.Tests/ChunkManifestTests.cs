using System;
using System.Linq;
using MetroBxl.Game.Assets;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Manifest streamingowy z `tunnel_sweep.py`. Audyt mutacyjny 02.09.2026: mutacja
/// `chunks.Sort → Reverse` PRZEŻYŁA cały `godot-first-run.yml` — kolejność chunków
/// nie była przez nic sprawdzana, a decyduje o tym, w jakiej kolejności scena
/// dokłada geometrię wzdłuż osi.
/// </summary>
[TestClass]
public sealed class ChunkManifestTests
{
    /// <summary>Chunki podane CELOWO w złej kolejności — parser ma je uporządkować.</summary>
    private const string Json = """
    {"id":"L1_A","name":"pakiet A","variant":"flat-preview","production_ready":false,
     "profile":"box_double","profile_size_m":[9.40,5.90],"axis_length_m":6686.739,
     "totals":{"triangles":16176},
     "streaming":{"default_ahead_m":600.0,"default_behind_m":300.0},
     "chunks":[
       {"id":"c03","file":"c03.glb","start_m":400.0,"end_m":600.0},
       {"id":"c01","file":"c01.glb","start_m":0.0,"end_m":200.0},
       {"id":"c02","file":"c02.glb","start_m":200.0,"end_m":400.0}]}
    """;

    [TestMethod]
    public void ChunksComeOutSortedByChainageNoMatterHowTheyWereWritten()
    {
        // Dokładnie ta własność, którą psuła przeżywająca mutacja Sort→Reverse.
        var manifest = ChunkManifest.FromJson(Json);
        var starts = manifest.Chunks.Select(c => c.StartM).ToArray();
        CollectionAssert.AreEqual(new[] { 0.0, 200.0, 400.0 }, starts);
        CollectionAssert.AreEqual(new[] { "c01", "c02", "c03" },
            manifest.Chunks.Select(c => c.Id).ToArray());
    }

    [TestMethod]
    public void SortedChunksAreContiguousAlongTheAxis()
    {
        // Kontrola mocniejsza od samej kolejności: koniec każdego chunka ma być
        // początkiem następnego. Odwrócona kolejność łamie to natychmiast.
        var chunks = ChunkManifest.FromJson(Json).Chunks;
        for (var i = 1; i < chunks.Count; i++)
        {
            Assert.AreEqual(chunks[i - 1].EndM, chunks[i].StartM, 1e-9,
                $"dziura albo zakładka między {chunks[i - 1].Id} a {chunks[i].Id}");
        }
    }

    [TestMethod]
    public void EveryScalarFieldIsReadFromTheJsonNotDefaulted()
    {
        var manifest = ChunkManifest.FromJson(Json);
        Assert.AreEqual("L1_A", manifest.Id);
        Assert.AreEqual("flat-preview", manifest.Variant);
        Assert.IsFalse(manifest.ProductionReady, "wariant flat-preview nie jest gotowy produkcyjnie");
        Assert.AreEqual("box_double", manifest.Profile);
        Assert.AreEqual(9.40, manifest.ProfileWidthM, 1e-9);
        Assert.AreEqual(5.90, manifest.ProfileHeightM, 1e-9);
        Assert.AreEqual(6686.739, manifest.AxisLengthM, 1e-9);
        Assert.AreEqual(16176, manifest.Triangles);
    }

    [TestMethod]
    public void ProfileWidthAndHeightAreNotSwapped()
    {
        // Kontrola negatywna do testu wyżej: `profile_size_m` to para, więc zamiana
        // indeksów przeszłaby każdą kontrolę „pole jest niezerowe". Tunel box_double
        // jest SZERSZY niż wyższy i to rozstrzyga.
        var manifest = ChunkManifest.FromJson(Json);
        Assert.IsTrue(manifest.ProfileWidthM > manifest.ProfileHeightM,
            $"szerokość {manifest.ProfileWidthM} nie jest większa od wysokości {manifest.ProfileHeightM}");
    }

    [TestMethod]
    public void StreamingWindowLooksAheadFurtherThanBehind()
    {
        // docs/01-architecture.md: okno 600 m przed składem i 300 m za nim.
        // Zamiana tych dwóch pól dałaby scenę doklejającą geometrię za plecami.
        var manifest = ChunkManifest.FromJson(Json);
        Assert.AreEqual(600.0, manifest.DefaultAheadM, 1e-9);
        Assert.AreEqual(300.0, manifest.DefaultBehindM, 1e-9);
        Assert.IsTrue(manifest.DefaultAheadM > manifest.DefaultBehindM);
    }

    [TestMethod]
    public void ANullDocumentIsRefusedInsteadOfCrashingLater()
    {
        Assert.ThrowsException<ArgumentNullException>(() => ChunkManifest.FromJson(null!));
    }
}
