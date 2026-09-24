using System;
using System.Collections.Generic;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Rejestruje pojedyncze wejścia GTFS w LineCore dokładnie w kroku rozkładowym.
/// Fizyczny wjazd wykonuje LineCore.Step po sprawdzeniu bloków zajętości.
/// </summary>
public sealed class LineEntryGate
{
    private readonly LineCore _line;
    private readonly HashSet<string> _usedBlocks = new(StringComparer.Ordinal);
    private readonly LineEntrySchedule? _schedule;
    private int _nextExpected;

    /// <summary>Bramka dla jednego zegara linii. Nie przejmuje jego wykonywania.</summary>
    public LineEntryGate(LineCore line)
    {
        _line = line ?? throw new ArgumentNullException(nameof(line));
    }

    /// <summary>Bramka z kontrolą, czy wszystkie wjazdy planu zostały zgłoszone przed krokiem linii.</summary>
    public LineEntryGate(LineCore line, LineEntrySchedule schedule, DateOnly serviceDay) : this(line)
    {
        _schedule = schedule ?? throw new ArgumentNullException(nameof(schedule));
        if (_schedule.ServiceDay != serviceDay)
        {
            throw new ArgumentException(
                $"Plan należy do dnia służby {_schedule.Date}, a zegar uruchomiono dla {serviceDay:yyyyMMdd}.",
                nameof(serviceDay));
        }
    }

    /// <summary>
    /// Wykonuje krok dopiero po zgłoszeniu wszystkich kursów z releaseStep równym
    /// bieżącemu krokowi. Nie zgłasza ich automatycznie. Wywołujący musi używać
    /// tej metody zamiast bezpośredniego LineCore.Step, aby kontrola działała.
    /// </summary>
    public void Step(Action<string, LineRun.TracePoint>? trace = null)
    {
        if (_schedule is null)
        {
            throw new InvalidOperationException("Kontrola pominiętych kursów wymaga planu wejść.");
        }
        if (_nextExpected < _schedule.Entries.Count &&
            _schedule.Entries[_nextExpected].ReleaseStep <= _line.Steps)
        {
            var missed = _schedule.Entries[_nextExpected];
            throw new InvalidOperationException(
                $"Kurs {missed.TripId} obiegu {missed.BlockId} z releaseStep {missed.ReleaseStep} nie został zgłoszony przed krokiem {_line.Steps}.");
        }
        _line.Step(trace);
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
        if (_schedule is not null &&
            (_nextExpected >= _schedule.Entries.Count || entry != _schedule.Entries[_nextExpected]))
        {
            throw new InvalidOperationException(
                $"Kurs {entry.TripId} nie jest następnym wejściem w planie.");
        }
        if (_usedBlocks.Contains(entry.BlockId))
        {
            throw new InvalidOperationException(
                $"Obieg {entry.BlockId} wymaga rozstrzygnięcia kolejnego kursu przed ponownym wjazdem.");
        }

        var train = _line.AddAtStation(entry.TripId, entry.ReleaseStep, entry.StationIndex);
        _usedBlocks.Add(entry.BlockId);
        if (_schedule is not null)
        {
            _nextExpected++;
        }
        return train;
    }
}
