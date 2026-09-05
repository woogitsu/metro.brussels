using System;
using System.Collections.Generic;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Zbiera stan klawiszy krok po kroku i składa z niego <see cref="InputLog"/>.
///
/// <para>Zapisuje wyłącznie ZMIANY: <see cref="Record"/> wołane 88 000 razy z tym samym
/// stanem daje jeden wpis. To nie jest kompresja dla oszczędności miejsca, tylko
/// warunek czytelności — plik ma czytać człowiek, a nie tylko <c>cmp</c>.</para>
///
/// <para>Numer kroku musi rosnąć. Nagrywanie „w tył" znaczyłoby, że ktoś woła to
/// z pętli klatek zamiast z pętli kroków, czyli dokładnie z tego miejsca, którego
/// pozbywa się ta zmiana — i wtedy zapis udawałby determinizm, którego by nie było.</para>
/// </summary>
public sealed class InputLogRecorder
{
    private readonly List<InputLogEntry> _entries = new();
    private long _nextStep;
    private bool _started;

    /// <summary>Ile wpisów (zmian stanu) zebrano do tej pory.</summary>
    public int EntryCount => _entries.Count;

    /// <summary>Numer kroku, którego oczekuje następne wywołanie <see cref="Record"/>.</summary>
    public long NextStep => _nextStep;

    /// <summary>
    /// Zapisuje stan klawiszy dla jednego kroku symulacji.
    /// </summary>
    /// <param name="step">Numer kroku, od zera, rosnąco i bez luk.</param>
    /// <param name="keys">Stan klawiszy w tym kroku.</param>
    /// <exception cref="ArgumentOutOfRangeException">Numer kroku nie jest tym, którego oczekiwano.</exception>
    public void Record(long step, DriverKeys keys)
    {
        if (step != _nextStep)
        {
            throw new ArgumentOutOfRangeException(nameof(step), step,
                $"Zapis wejść oczekiwał kroku {_nextStep}. Krok musi rosnąć o jeden — "
                + "inaczej zapis opisuje inny przejazd niż ten, który się odbył.");
        }

        _nextStep = step + 1;
        if (!_started || _entries[^1].Keys != keys)
        {
            _entries.Add(new InputLogEntry(step, keys));
            _started = true;
        }
    }

    /// <summary>Składa zapis z zebranych zmian; długością przejazdu jest liczba zapisanych kroków.</summary>
    /// <returns>Zapis wejść gotowy do zapisania na dysk.</returns>
    public InputLog Build() => new(_nextStep, _entries);

    /// <summary>Zapomina wszystko — do resetu przejazdu.</summary>
    public void Clear()
    {
        _entries.Clear();
        _nextStep = 0;
        _started = false;
    }
}
