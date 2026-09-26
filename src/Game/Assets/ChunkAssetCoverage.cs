using System;
using System.Collections.Generic;
using System.IO;

namespace MetroBxl.Game.Assets;

/// <summary>Checks every file the tunnel streamer may need before a drive starts.</summary>
public static class ChunkAssetCoverage
{
    /// <summary>
    /// Returns missing LOD files and, when any track detail exists, missing detail files.
    /// A complete older package without track details remains valid.
    /// </summary>
    public static (bool HasDetails, IReadOnlyList<string> Missing) Check(
        ChunkManifest manifest, string directory, Func<string, bool> exists)
    {
        ArgumentNullException.ThrowIfNull(manifest);
        ArgumentNullException.ThrowIfNull(exists);

        var missing = new List<string>();
        var anyDetail = false;
        foreach (var chunk in manifest.Chunks)
            anyDetail |= exists(Path.Combine(directory, chunk.Id + "_detail.glb"));

        foreach (var chunk in manifest.Chunks)
        {
            foreach (var lod in chunk.Lods)
                if (!exists(Path.Combine(directory, lod.File)))
                    missing.Add(lod.File);
            if (anyDetail)
            {
                var detail = chunk.Id + "_detail.glb";
                if (!exists(Path.Combine(directory, detail)))
                    missing.Add(detail);
            }
        }

        return (anyDetail, missing);
    }
}
