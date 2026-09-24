using System;
using System.Collections.Generic;
using MetroBxl.Sim.Json;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Line;

/// <summary>Odcinek kursu tego samego obiegu na modelowanej osi.</summary>
public readonly record struct ProjectedBlockRun(
    string TripId, string BlockId, int EntryStationIndex, int ExitStationIndex,
    long ReleaseStep, long ExitStep);

/// <summary>Para kolejnych odcinków jednego block_id w projekcji; pomiędzy nimi mogą istnieć kursy poza osią.</summary>
public readonly record struct BlockTransition(
    string BlockId, string PreviousTripId, string NextTripId, long GapSteps,
    int ExitStationIndex, int NextEntryStationIndex)
{
    /// <summary>Czy oba odcinki stykają się na tej samej stacji osi.</summary>
    public bool SharesBoundaryStation => ExitStationIndex == NextEntryStationIndex;
}

/// <summary>Kontrola kolejności odcinków GTFS powiązanych block_id bez tworzenia pojazdów.</summary>
public sealed class BlockContinuity
{
    private BlockContinuity(IReadOnlyList<ProjectedBlockRun> runs,
        IReadOnlyList<BlockTransition> transitions)
    {
        Runs = runs;
        Transitions = transitions;
    }

    /// <summary>Odcinki w kolejności czasu wejścia, potem trip_id.</summary>
    public IReadOnlyList<ProjectedBlockRun> Runs { get; }
    /// <summary>Kolejne pary widoczne na osi w każdym obiegu, bez przypisania numeru taborowego.</summary>
    public IReadOnlyList<BlockTransition> Transitions { get; }

    /// <summary>
    /// Czyta tę samą projekcję co LineEntrySchedule. block_id oznacza wspólny
    /// obieg pojazdu, ale nie dostarcza numeru konkretnej jednostki taboru.
    /// Nakładające się odcinki jednego obiegu są sprzeczne i odrzucane.
    /// Różne stacje graniczne zostają jawnie niewyjaśnione.
    /// </summary>
    public static BlockContinuity FromJson(string json, TrackAxis axis, FixedStep step)
    {
        var entrySchedule = LineEntrySchedule.FromJson(json, axis, step);
        using var document = JsonText.Parse(json, "ciągłość obiegów GTFS");
        var root = document.RootElement;
        var entriesByTrip = new Dictionary<string, ScheduledLineEntry>(StringComparer.Ordinal);
        foreach (var entry in entrySchedule.Entries)
        {
            entriesByTrip.Add(entry.TripId, entry);
        }
        var runs = new List<ProjectedBlockRun>();
        var byBlock = new Dictionary<string, List<ProjectedBlockRun>>(StringComparer.Ordinal);
        foreach (var run in root.RequiredField("runs", "Projekcja GTFS").EnumerateArray())
        {
            var tripId = run.RequiredField("trip_id", "Kurs GTFS").GetString()!;
            var entry = entriesByTrip[tripId];
            var lastStopId = run.RequiredField("last_stop_id", "Kurs GTFS").GetString();
            var exitIndex = -1;
            for (var i = 0; i < axis.Stations.Count; i++)
            {
                if (string.Equals(axis.Stations[i].StopId, lastStopId, StringComparison.Ordinal))
                {
                    exitIndex = i;
                    break;
                }
            }
            if (exitIndex <= entry.StationIndex)
            {
                throw new ArgumentException($"Kurs {tripId}: niepoprawna stacja wyjścia {lastStopId}.", nameof(json));
            }
            var exitSeconds = run.RequiredField("exit_s", "Kurs GTFS").GetInt64();
            if (exitSeconds < 0 || checked(exitSeconds * step.Hertz) < entry.ReleaseStep)
            {
                throw new ArgumentException($"Kurs {tripId}: wyjście poprzedza wejście.", nameof(json));
            }
            var projected = new ProjectedBlockRun(tripId, entry.BlockId, entry.StationIndex,
                exitIndex, entry.ReleaseStep, checked(exitSeconds * step.Hertz));
            runs.Add(projected);
            if (!byBlock.TryGetValue(entry.BlockId, out var blockRuns))
            {
                blockRuns = new List<ProjectedBlockRun>();
                byBlock.Add(entry.BlockId, blockRuns);
            }
            blockRuns.Add(projected);
        }
        var transitions = new List<BlockTransition>();
        foreach (var block in byBlock)
        {
            block.Value.Sort((a, b) =>
            {
                var byTime = a.ReleaseStep.CompareTo(b.ReleaseStep);
                return byTime != 0 ? byTime : string.CompareOrdinal(a.TripId, b.TripId);
            });
            for (var i = 1; i < block.Value.Count; i++)
            {
                var previous = block.Value[i - 1];
                var next = block.Value[i];
                var gap = next.ReleaseStep - previous.ExitStep;
                if (gap < 0)
                {
                    throw new ArgumentException(
                        $"Obieg {block.Key}: kursy {previous.TripId} i {next.TripId} nakładają się.", nameof(json));
                }
                transitions.Add(new BlockTransition(block.Key, previous.TripId, next.TripId,
                    gap, previous.ExitStationIndex, next.EntryStationIndex));
            }
        }
        transitions.Sort((a, b) =>
        {
            var byBlockId = string.CompareOrdinal(a.BlockId, b.BlockId);
            return byBlockId != 0 ? byBlockId : string.CompareOrdinal(a.PreviousTripId, b.PreviousTripId);
        });
        return new BlockContinuity(runs.ToArray(), transitions.ToArray());
    }
}
