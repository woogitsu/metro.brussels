using System;
using System.Collections.Generic;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Rejestruje pojedyncze wejścia GTFS w LineCore dokładnie w kroku rozkładowym.
/// Fizyczny wjazd wykonuje LineCore.Step po sprawdzeniu bloków zajętości.
/// </summary>
public sealed class LineEntryGate
{
    private readonly LineCore _line;
    private readonly HashSet<string> _usedBlocks = new(StringComparer.Ordinal);

    /// <summary>Bramka dla jednego zegara linii. Nie przejmuje jego wykonywania.</summary>
    public LineEntryGate(LineCore line)
    {
        _line = line ?? throw new ArgumentNullException(nameof(line));
    }

    /// <summary>
    /// Rejestruje kurs w jego ReleaseStep. Drugi kurs tego samego block_id jest
    /// odrzucany, dopóki nie istnieje jawna polityka ponownego użycia pojazdu.
    /// Zajęty peron zatrzyma fizyczny wjazd w LineCore.Step; EnteredAtStep pokaże
    /// rzeczywisty krok, gdy blok się zwolni.
    /// </summary>
    public LineTrain QueueDue(ScheduledLineEntry entry)
    {
        if (string.IsNullOrWhiteSpace(entry.TripId) || string.IsNullOrWhiteSpace(entry.BlockId))
        {
            throw new ArgumentException("Kurs wymaga trip_id i block_id.", nameof(entry));
        }
        if (entry.ReleaseStep != _line.Steps)
        {
            throw new ArgumentOutOfRangeException(nameof(entry),
                $"Kurs {entry.TripId} ma releaseStep {entry.ReleaseStep}, a zegar linii {_line.Steps}.");
        }
        if (_usedBlocks.Contains(entry.BlockId))
        {
            throw new InvalidOperationException(
                $"Obieg {entry.BlockId} wymaga rozstrzygnięcia kolejnego kursu przed ponownym wjazdem.");
        }

        var train = _line.AddAtStation(entry.TripId, entry.ReleaseStep, entry.StationIndex);
        _usedBlocks.Add(entry.BlockId);
        return train;
    }
}
