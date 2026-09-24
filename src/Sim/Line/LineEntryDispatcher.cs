using System;
using System.Collections.Generic;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Advances one axis through the dated entry plan. Each trip is an independent
/// traversal; reuse of a GTFS block_id needs a separate, verified vehicle-transfer
/// policy and is deliberately refused here.
/// </summary>
public sealed class LineEntryDispatcher
{
    private readonly LineCore _line;
    private readonly LineEntryGate _gate;
    private readonly IReadOnlyList<ScheduledLineEntry> _entries;
    private int _next;

    /// <summary>Bind a dated, single-axis plan to a line with no automatic turnback.</summary>
    public LineEntryDispatcher(LineCore line, LineEntrySchedule schedule, DateOnly serviceDay)
    {
        _line = line ?? throw new ArgumentNullException(nameof(line));
        ArgumentNullException.ThrowIfNull(schedule);
        if (line.Steps != 0 || line.Trains.Count != 0)
            throw new ArgumentException(
                "Dyspozytor wymaga świeżej linii bez wcześniejszych kroków i składów.", nameof(line));
        if (!string.Equals(line.AxisId, schedule.AxisId, StringComparison.Ordinal))
            throw new ArgumentException("Plan wejść dotyczy innej osi niż linia.", nameof(schedule));
        if (line.TurnbackEnabled)
            throw new ArgumentException("Rozkładowe wejścia wymagają linii bez automatycznego nawrotu.", nameof(line));

        // Reject before moving the line or registering part of a plan. block_id
        // identifies a vehicle duty, not an inexhaustible supply of new vehicles.
        var blocks = new HashSet<string>(StringComparer.Ordinal);
        foreach (var entry in schedule.Entries)
            if (!blocks.Add(entry.BlockId))
                throw new InvalidOperationException(
                    $"Obieg {entry.BlockId} występuje ponownie; brak polityki transferu pojazdu między kursami.");

        _gate = new LineEntryGate(line, schedule, serviceDay);
        _entries = schedule.Entries;
    }

    /// <summary>Number of trips handed to the entry gate at their scheduled step.</summary>
    public int RegisteredEntries => _next;

    /// <summary>Future departures keep the dispatcher alive even when current trains finish.</summary>
    public bool Finished => _next == _entries.Count && (_entries.Count == 0 || _line.Finished);

    /// <summary>Register every trip due now, then advance the shared line clock once.</summary>
    public bool Step()
    {
        if (Finished)
            return false;
        while (_next < _entries.Count && _entries[_next].ReleaseStep == _line.Steps)
        {
            _gate.QueueDue(_entries[_next]);
            _next++;
        }
        _gate.Step();
        return true;
    }

    /// <summary>Run until all planned trips arrive or the absolute step budget is exhausted.</summary>
    public string Run(long stepBudget)
    {
        if (stepBudget < 0)
            throw new ArgumentOutOfRangeException(nameof(stepBudget));
        while (_line.Steps < stepBudget && Step()) { }
        return Finished ? "arrived" : "step-budget";
    }
}
