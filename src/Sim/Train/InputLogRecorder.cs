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
///
/// <para><b>Reset przejazdu NIE kasuje zapisu — zostaje w nim jako wpis</b> (decyzja
/// właściciela z 05.09.2026, wariant W1). Do tego dnia stało tu <c>Clear()</c>, bo
/// licznik kroków przejazdu wracał do zera i dalsze nagrywanie nadpisywałoby numery,
/// które już padły. Rozwiązaniem nie było kasowanie, tylko rozdzielenie dwóch liczb:
/// <see cref="NextStep"/> liczy SESJĘ i nie wraca nigdy, a <c>DriveState.Steps</c> liczy
/// PRZEJAZD i po resecie zaczyna od zera. Dzięki temu przejazd z resetem odtwarza się
/// z pliku co do bitu, czyli da się na niego założyć bramkę.</para>
/// </summary>
public sealed class InputLogRecorder
{
    private readonly List<InputLogEntry> _entries = new();
    private readonly List<long> _resets = new();
    private readonly List<InputLogEvent> _events = new();
    private long _nextStep;
    private bool _started;

    /// <summary>Ile wpisów (zmian stanu) zebrano do tej pory.</summary>
    public int EntryCount => _entries.Count;

    /// <summary>Ile resetów zapisano do tej pory.</summary>
    public int ResetCount => _resets.Count;

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

    /// <summary>
    /// Zapisuje reset przejazdu: przed krokiem, którego zapis właśnie oczekuje, przejazd
    /// zaczyna się od nowa.
    ///
    /// <para>Stanu klawiszy nie dotyka i to nie jest przeoczenie. Reset przestawia
    /// pulpit, a nie rękę maszynisty: gracz trzyma dalej to, co trzymał, a
    /// <see cref="InputLog.KeysAt"/> szuka po całej sesji, więc wpis sprzed resetu
    /// obowiązuje dalej. Domykanie tu stanu klawiszy dopisywałoby zmianę, której
    /// nie było.</para>
    /// </summary>
    public void RecordReset() => _resets.Add(_nextStep);

    /// <summary>
    /// Zapisuje polecenie maszynisty w trybie linii — 6.M1. Polecenie wykonuje się
    /// PRZED krokiem, który zostanie zapisany jako następny, bo scena wydaje je między
    /// krokami (w obsłudze klawiszy klatki), a nie w środku kroku.
    /// </summary>
    /// <param name="rodzajZdarzenia">Rodzaj polecenia.</param>
    /// <param name="trainId">Skład, którego polecenie dotyczy.</param>
    public void RecordEvent(LineEventKind rodzajZdarzenia, string trainId) =>
        _events.Add(new InputLogEvent(_nextStep, rodzajZdarzenia, trainId));

    /// <summary>Liczba zapisanych zdarzeń linii — 6.M1.</summary>
    public int EventCount => _events.Count;

    /// <summary>Składa zapis z zebranych zmian; długością przejazdu jest liczba zapisanych kroków.</summary>
    /// <returns>Zapis wejść gotowy do zapisania na dysk.</returns>
    public InputLog Build() => new(_nextStep, _entries, _resets, _events);
}
