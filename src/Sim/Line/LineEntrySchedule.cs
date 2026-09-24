using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Json;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Jeden rozkładowy wjazd na oś. <see cref="BlockId"/> wiąże kursy tego samego
/// pojazdu, ale ten typ nie tworzy pojazdu ani nie planuje kolejnego kursu.
/// </summary>
public readonly record struct ScheduledLineEntry(
    string TripId, string BlockId, int StationIndex, long ReleaseStep);

/// <summary>
/// Typowane wejścia z projekcji GTFS. Krok zero jest północą dnia służby;
/// 25:00 z GTFS pozostaje po 24 godzinach, bez zawijania do następnej doby.
/// </summary>
public sealed class LineEntrySchedule
{
    private LineEntrySchedule(string date, DateOnly serviceDay, string axisId, string sourceGtfsSha256,
        IReadOnlyList<ScheduledLineEntry> entries)
    {
        Date = date;
        ServiceDay = serviceDay;
        AxisId = axisId;
        SourceGtfsSha256 = sourceGtfsSha256;
        Entries = entries;
    }

    /// <summary>Dzień służby zapisany w projekcji GTFS.</summary>
    public string Date { get; }
    /// <summary>Dzień służby jako data kalendarzowa, niezależny od godzin GTFS po 24:00.</summary>
    public DateOnly ServiceDay { get; }
    /// <summary>Identyfikator osi, na którą rzutowane są kursy.</summary>
    public string AxisId { get; }
    /// <summary>Odcisk źródłowego GTFS przeniesiony z projekcji.</summary>
    public string SourceGtfsSha256 { get; }
    /// <summary>Wjazdy posortowane po kroku i identyfikatorze kursu.</summary>
    public IReadOnlyList<ScheduledLineEntry> Entries { get; }

    /// <summary>
    /// Czyta wynik <c>tools/track/timetable.py --project-trips</c>. Odcisk SHA jest
    /// przenoszony z projekcji; sprawdzenie bajtów archiwum należy do generatora.
    /// Ten odczyt nie wywołuje <see cref="LineCore.AddAtStation"/>.
    /// </summary>
    public static LineEntrySchedule FromJson(string json, TrackAxis axis, FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(json);
        ArgumentNullException.ThrowIfNull(axis);
        step.RequireValid();
        if (step.Hertz <= 0)
        {
            throw new ArgumentException("Plan wejść wymaga kroku z całkowitą częstotliwością Hz.", nameof(step));
        }

        using var document = JsonText.Parse(json, "plan wejść GTFS");
        var root = document.RootElement;
        var axisId = root.RequiredField("axis_id", "Plan wejść GTFS").GetString()
            ?? throw new ArgumentException("Plan bez axis_id.", nameof(json));
        if (!string.Equals(axisId, axis.Id, StringComparison.Ordinal))
        {
            throw new ArgumentException($"Plan osi {axisId} nie pasuje do {axis.Id}.", nameof(json));
        }
        var date = root.RequiredField("date", "Plan wejść GTFS").GetString()
            ?? throw new ArgumentException("Plan bez daty.", nameof(json));
        if (!DateOnly.TryParseExact(date, "yyyyMMdd", CultureInfo.InvariantCulture,
                DateTimeStyles.None, out var serviceDay) ||
            !string.Equals(serviceDay.ToString("yyyyMMdd", CultureInfo.InvariantCulture), date,
                StringComparison.Ordinal))
        {
            throw new ArgumentException($"Niepoprawny dzień służby GTFS: {date}.", nameof(json));
        }
        var sha = root.RequiredField("source_gtfs_sha256", "Plan wejść GTFS").GetString()
            ?? throw new ArgumentException("Plan bez odcisku GTFS.", nameof(json));
        var entries = new List<ScheduledLineEntry>();
        var tripIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var run in root.RequiredField("runs", "Plan wejść GTFS").EnumerateArray())
        {
            var tripId = run.RequiredField("trip_id", "Kurs GTFS").GetString() ?? "";
            var blockId = run.RequiredField("block_id", "Kurs GTFS").GetString() ?? "";
            var firstStopId = run.RequiredField("first_stop_id", "Kurs GTFS").GetString() ?? "";
            if (string.IsNullOrWhiteSpace(tripId) || !tripIds.Add(tripId))
            {
                throw new ArgumentException($"Brak lub powtórzony trip_id: {tripId}.", nameof(json));
            }
            if (string.IsNullOrWhiteSpace(blockId))
            {
                throw new ArgumentException($"Kurs {tripId} nie ma block_id.", nameof(json));
            }
            var stationIndex = -1;
            for (var i = 0; i < axis.Stations.Count - 1; i++)
            {
                if (string.Equals(axis.Stations[i].StopId, firstStopId, StringComparison.Ordinal))
                {
                    stationIndex = i;
                    break;
                }
            }
            if (stationIndex < 0)
            {
                throw new ArgumentException(
                    $"Kurs {tripId}: stacja wejścia {firstStopId} nie leży przed końcem osi {axis.Id}.",
                    nameof(json));
            }
            var releaseSeconds = run.RequiredField("release_s", "Kurs GTFS").GetInt64();
            if (releaseSeconds < 0)
            {
                throw new ArgumentException($"Kurs {tripId}: ujemna godzina wejścia.", nameof(json));
            }
            entries.Add(new ScheduledLineEntry(tripId, blockId, stationIndex,
                checked(releaseSeconds * step.Hertz)));
        }
        entries.Sort((a, b) =>
        {
            var byTime = a.ReleaseStep.CompareTo(b.ReleaseStep);
            return byTime != 0 ? byTime : string.CompareOrdinal(a.TripId, b.TripId);
        });
        return new LineEntrySchedule(date, serviceDay, axisId, sha, entries.ToArray());
    }
}
