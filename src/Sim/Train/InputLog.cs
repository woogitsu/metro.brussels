using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace MetroBxl.Sim.Train;

/// <summary>Jedna zmiana stanu klawiszy w zapisie wejść.</summary>
/// <param name="Step">Numer kroku symulacji, od którego ten stan obowiązuje.</param>
/// <param name="Keys">Stan klawiszy obowiązujący od tego kroku do następnego wpisu.</param>
public readonly record struct InputLogEntry(long Step, DriverKeys Keys);

/// <summary>Rodzaj polecenia maszynisty w trybie linii — 6.M1.</summary>
public enum LineEventKind
{
    /// <summary>Przejęcie sterowania składem od autopilota.</summary>
    Take,

    /// <summary>Oddanie sterowania autopilotowi.</summary>
    Release,

    /// <summary>Żądanie otwarcia drzwi.</summary>
    DoorOpen,

    /// <summary>Żądanie zamknięcia drzwi.</summary>
    DoorClose,

    /// <summary>Zmiana składu obserwowanego, czyli tego, do którego idzie nastawnik.</summary>
    Observe,
}

/// <summary>
/// Jedno polecenie maszynisty w trybie linii, przypięte do kroku — 6.M1.
/// </summary>
/// <param name="Step">Numer kroku symulacji, PRZED którym polecenie się wykonuje.</param>
/// <param name="Kind">Rodzaj polecenia.</param>
/// <param name="TrainId">Skład, którego polecenie dotyczy.</param>
public readonly record struct InputLogEvent(long Step, LineEventKind Kind, string TrainId);

/// <summary>
/// Zapis wejść maszynisty **po numerze kroku**, nie po czasie ściennym.
/// <c>docs/01-architecture.md</c> §Determinizm: „z ziarna + zapisu wejść da się
/// odtworzyć przejazd". To jest ten zapis.
///
/// <para><b>Format jest tekstowy i czytelny dla człowieka</b>, jak reszta wyjść tego
/// repozytorium. Wiersze puste i zaczynające się od <c>#</c> są pomijane:</para>
///
/// <code>
/// # METRO BXL — zapis wejść maszynisty
/// # klawisze: W ciąg, S hamulec, X wybieg, E hamulec awaryjny (= pełny służbowy), - nic
/// wersja=1
/// kroki=7200
/// krok;klawisze
/// 0;W
/// 3600;S
/// </code>
///
/// <para><b>Znak <c>E</c> jest dopisany do zestawu 05.09.2026, a wersja formatu została
/// przy <c>1</c> — świadomie.</b> Kod klawiszy jest zbiorem znaków, więc plik bez
/// hamulca awaryjnego zapisuje się i czyta bajt w bajt tak samo jak przedtem; zmieniła
/// się wyłącznie linia komentarza z legendą, której <see cref="Parse"/> nie czyta.
/// Stary plik odtwarza się w nowym kodzie, nowy bez <c>E</c> — w starym.</para>
///
/// <para><b>RESET PRZEJAZDU jest wpisem, a nie klawiszem — i dlatego dostał wersję 2.</b>
/// Decyzja właściciela z 05.09.2026 (wariant W1). Wpis <c>krok;reset</c> znaczy: PRZED
/// wykonaniem tego kroku zacznij przejazd od nowa. Reset nie jest stanem dźwigni, tylko
/// zdarzeniem, więc nie mógł wejść do <see cref="DriverKeys"/>: <see cref="KeysAt"/>
/// zwracałoby wtedy „reset" jako położenie nastawnika, a przez to samo miejsce chodzi
/// polecenie do <see cref="DriverNotch"/>.</para>
///
/// <para><b>Numer kroku NIE wraca do zera po resecie.</b> Zapis indeksuje SESJĘ,
/// a <see cref="DriveState.Steps"/> indeksuje PRZEJAZD — po resecie te dwie liczby się
/// rozjeżdżają i to jest poprawne, bo opisują różne rzeczy. Gdyby zapis wracał do zera,
/// dwa wpisy z tym samym numerem opisywałyby dwa różne momenty i plik przestałby być
/// jednoznaczny. Dzięki temu <see cref="Steps"/> zostaje tym, czym był: liczbą kroków,
/// które odtworzenie ma wykonać.</para>
///
/// <para><b>Wersję pliku decyduje TREŚĆ, nie data.</b> Zapis bez resetu wychodzi jako
/// <c>wersja=1</c> — bajt w bajt taki, jak przed tą zmianą, więc dwa wzorce bramek CI
/// (<c>tests/data/manual-keys.log</c>, <c>tests/data/manual-keys-limit.log</c>) nie
/// wymagały migracji i dalej czyta je również stary kod. Zapis z resetem wychodzi jako
/// <c>wersja=2</c>. Odczyt bierze obie, ale każdą dosłownie: <c>wersja=1</c> z wierszem
/// resetu i <c>wersja=2</c> bez ani jednego są ODMOWĄ, bo w obu plik mówi o sobie co
/// innego, niż zawiera.</para>
///
/// <para><b>Zapisywane są ZMIANY, nie każdy krok.</b> Przejazd całą linią to ponad
/// 88 000 kroków, a człowiek przestawia nastawnik kilkadziesiąt razy — plik po jednym
/// wierszu na krok byłby nieczytelny dokładnie dla tego, kto ma go czytać. Wpis
/// obowiązuje od swojego kroku do kroku następnego wpisu; przed pierwszym wpisem
/// nie jest trzymane nic.</para>
///
/// <para><b><c>kroki=</c> jest w nagłówku, a nie wyprowadzane z ostatniego wiersza</b>,
/// bo długość przejazdu jest częścią zapisu, a nie skutkiem ubocznym ostatniego
/// naciśnięcia klawisza. Bez tej liczby odtworzenie nie wiedziałoby, kiedy się skończyć —
/// a przebieg ręczny, który się nie kończy, nie da się postawić w CI (§1.4
/// <c>reports/droga-do-grywalnosci.md</c>).</para>
/// </summary>
public sealed class InputLog
{
    /// <summary>Najstarsza wersja formatu, którą ta klasa czyta: zapis bez resetów.</summary>
    public const int VersionWithoutResets = 1;

    /// <summary>Wersja formatu z wpisami resetu.</summary>
    public const int VersionWithResets = 2;

    /// <summary>Wersja formatu ze zdarzeniami linii (przejęcie, drzwi, obserwacja) — 6.M1.</summary>
    public const int VersionWithLineEvents = 3;

    /// <summary>Napis w kolumnie klawiszy oznaczający reset przejazdu.</summary>
    public const string ResetCode = "reset";

    /// <summary>Znak między kodem zdarzenia linii a identyfikatorem składu: <c>przejmij:A</c>.</summary>
    public const char EventTrainSeparator = ':';

    /// <summary>Nazwa pola nagłówka z wersją formatu.</summary>
    public const string VersionField = "wersja";

    /// <summary>Nazwa pola nagłówka z liczbą kroków przejazdu.</summary>
    public const string StepsField = "kroki";

    /// <summary>Wiersz nazw kolumn, oddzielający nagłówek od wpisów.</summary>
    public const string ColumnHeader = "krok;klawisze";

    private readonly InputLogEntry[] _entries;
    private readonly long[] _resets;
    private readonly InputLogEvent[] _events;

    /// <summary>
    /// Zapis bez resetów — z jawnej listy wpisów.
    /// </summary>
    /// <param name="steps">Liczba kroków przejazdu; nieujemna.</param>
    /// <param name="entries">Wpisy w rosnącej kolejności numerów kroków.</param>
    /// <exception cref="ArgumentNullException">Lista wpisów jest <c>null</c>.</exception>
    /// <exception cref="ArgumentOutOfRangeException">Liczba kroków jest ujemna.</exception>
    /// <exception cref="ArgumentException">Numery kroków nie rosną, są ujemne albo wychodzą poza przejazd.</exception>
    public InputLog(long steps, IReadOnlyList<InputLogEntry> entries)
        : this(steps, entries, Array.Empty<long>())
    {
    }

    /// <summary>
    /// Zapis z jawnej listy wpisów i jawną listą kroków, w których przejazd zaczyna się
    /// od nowa.
    /// </summary>
    /// <param name="steps">Liczba kroków przejazdu; nieujemna.</param>
    /// <param name="entries">Wpisy w rosnącej kolejności numerów kroków.</param>
    /// <param name="resets">Numery kroków z resetem, rosnąco; reset obowiązuje PRZED swoim krokiem.</param>
    /// <exception cref="ArgumentNullException">Lista wpisów albo lista resetów jest <c>null</c>.</exception>
    /// <exception cref="ArgumentOutOfRangeException">Liczba kroków jest ujemna.</exception>
    /// <exception cref="ArgumentException">Numery kroków nie rosną, są ujemne albo wychodzą poza przejazd.</exception>
    public InputLog(long steps, IReadOnlyList<InputLogEntry> entries, IReadOnlyList<long> resets)
        : this(steps, entries, resets, Array.Empty<InputLogEvent>())
    {
    }

    /// <summary>
    /// Zapis z wpisami klawiszy, resetami i zdarzeniami linii — 6.M1.
    /// </summary>
    /// <param name="steps">Liczba kroków przejazdu; nieujemna.</param>
    /// <param name="entries">Wpisy w rosnącej kolejności numerów kroków.</param>
    /// <param name="resets">Numery kroków z resetem, rosnąco; reset obowiązuje PRZED swoim krokiem.</param>
    /// <param name="events">
    /// Zdarzenia linii w NIEMALEJĄCEJ kolejności kroków. Kilka zdarzeń w jednym kroku
    /// jest dozwolone i wykonuje się w kolejności listy — tak, jak zapisała je scena.
    /// </param>
    /// <exception cref="ArgumentNullException">Któraś z list jest <c>null</c>.</exception>
    /// <exception cref="ArgumentOutOfRangeException">Liczba kroków jest ujemna.</exception>
    /// <exception cref="ArgumentException">Numery kroków są w złej kolejności, ujemne albo wychodzą poza przejazd.</exception>
    public InputLog(
        long steps,
        IReadOnlyList<InputLogEntry> entries,
        IReadOnlyList<long> resets,
        IReadOnlyList<InputLogEvent> events)
    {
        ArgumentNullException.ThrowIfNull(entries);
        ArgumentNullException.ThrowIfNull(resets);
        ArgumentNullException.ThrowIfNull(events);
        if (steps < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(steps), steps,
                "Liczba kroków przejazdu nie może być ujemna.");
        }

        var copy = new InputLogEntry[entries.Count];
        var previous = -1L;
        for (var i = 0; i < entries.Count; i++)
        {
            var entry = entries[i];
            if (entry.Step <= previous)
            {
                throw new ArgumentException(
                    $"Numery kroków w zapisie muszą rosnąć: wpis {i} ma krok {entry.Step}, "
                    + $"a poprzedni {previous}.", nameof(entries));
            }

            if (entry.Step < 0)
            {
                throw new ArgumentException(
                    $"Wpis {i} ma ujemny numer kroku {entry.Step}.", nameof(entries));
            }

            if (entry.Step >= steps && steps > 0)
            {
                throw new ArgumentException(
                    $"Wpis {i} obowiązuje od kroku {entry.Step}, a przejazd ma {steps} kroków — "
                    + "taki wpis nigdy by nie zadziałał.", nameof(entries));
            }

            copy[i] = entry;
            previous = entry.Step;
        }

        var resetCopy = new long[resets.Count];
        var previousReset = -1L;
        for (var i = 0; i < resets.Count; i++)
        {
            var reset = resets[i];
            if (reset <= previousReset)
            {
                throw new ArgumentException(
                    $"Numery kroków z resetem muszą rosnąć: reset {i} ma krok {reset}, "
                    + $"a poprzedni {previousReset}.", nameof(resets));
            }

            if (reset < 0)
            {
                throw new ArgumentException(
                    $"Reset {i} ma ujemny numer kroku {reset}.", nameof(resets));
            }

            // Ten sam warunek, co dla wpisów, i z tego samego powodu: reset obowiązuje
            // PRZED swoim krokiem, więc reset w kroku równym długości przejazdu albo
            // dalszym nigdy by nie zadziałał — a zapis, który zawiera zdarzenie
            // niewykonalne, wygląda dokładnie tak samo jak zapis poprawny.
            if (reset >= steps && steps > 0)
            {
                throw new ArgumentException(
                    $"Reset {i} obowiązuje przed krokiem {reset}, a przejazd ma {steps} kroków — "
                    + "taki reset nigdy by nie zadziałał.", nameof(resets));
            }

            resetCopy[i] = reset;
            previousReset = reset;
        }

        // ZDARZENIA LINII — 6.M1. Kolejność NIEMALEJĄCA, a nie rosnąca jak przy wpisach
        // klawiszy: w jednej klatce gracz może przejąć skład i od razu otworzyć drzwi,
        // a oba polecenia trafiają przed ten sam krok. Ten sam warunek na koniec
        // przejazdu, co przy resetach, i z tego samego powodu.
        var eventCopy = new InputLogEvent[events.Count];
        var previousEvent = 0L;
        for (var i = 0; i < events.Count; i++)
        {
            var lineEvent = events[i];
            if (lineEvent.Step < previousEvent)
            {
                throw new ArgumentException(
                    $"Numery kroków zdarzeń linii nie mogą maleć: zdarzenie {i} ma krok "
                    + $"{lineEvent.Step}, a poprzednie {previousEvent}.", nameof(events));
            }

            if (lineEvent.Step >= steps && steps > 0)
            {
                throw new ArgumentException(
                    $"Zdarzenie {i} obowiązuje przed krokiem {lineEvent.Step}, a przejazd ma "
                    + $"{steps} kroków — takie zdarzenie nigdy by się nie wykonało.", nameof(events));
            }

            if (string.IsNullOrEmpty(lineEvent.TrainId)
                || lineEvent.TrainId.IndexOfAny(new[] { ';', EventTrainSeparator, '\n', '\r' }) >= 0)
            {
                throw new ArgumentException(
                    $"Zdarzenie {i} ma identyfikator składu '{lineEvent.TrainId}', którego nie da "
                    + "się zapisać w jednym polu wiersza.", nameof(events));
            }

            eventCopy[i] = lineEvent;
            previousEvent = lineEvent.Step;
        }

        Steps = steps;
        _entries = copy;
        _resets = resetCopy;
        _events = eventCopy;
    }

    /// <summary>Liczba kroków przejazdu. Odtworzenie kończy się po tylu krokach.</summary>
    public long Steps { get; }

    /// <summary>Wpisy zapisu, w rosnącej kolejności numerów kroków.</summary>
    public IReadOnlyList<InputLogEntry> Entries => _entries;

    /// <summary>
    /// Numery kroków, przed którymi przejazd zaczyna się od nowa, rosnąco.
    /// Pusta lista znaczy zapis w wersji <see cref="VersionWithoutResets"/>.
    /// </summary>
    public IReadOnlyList<long> Resets => _resets;

    /// <summary>
    /// Wersja formatu, w której ten zapis zostanie zapisany. Decyduje TREŚĆ: zapis bez
    /// resetu wychodzi w wersji 1, czyli bajt w bajt jak przed dopisaniem resetów.
    /// </summary>
    public int FormatVersion => _events.Length > 0 ? VersionWithLineEvents
        : _resets.Length == 0 ? VersionWithoutResets : VersionWithResets;

    /// <summary>Zdarzenia linii w kolejności wykonania — 6.M1.</summary>
    public IReadOnlyList<InputLogEvent> Events => _events;

    /// <summary>
    /// Zdarzenia linii, które wykonują się PRZED krokiem <paramref name="step"/>,
    /// w kolejności zapisu. Pusta lista, gdy w tym kroku nie ma żadnego.
    /// </summary>
    /// <param name="step">Numer kroku sesji.</param>
    public IReadOnlyList<InputLogEvent> EventsAt(long step)
    {
        var low = 0;
        var high = _events.Length;
        while (low < high)
        {
            var middle = low + ((high - low) / 2);
            if (_events[middle].Step < step)
            {
                low = middle + 1;
            }
            else
            {
                high = middle;
            }
        }

        var end = low;
        while (end < _events.Length && _events[end].Step == step)
        {
            end++;
        }

        return end == low ? Array.Empty<InputLogEvent>() : _events[low..end];
    }

    /// <summary>Kod zdarzenia linii w kolumnie zapisu — 6.M1.</summary>
    /// <param name="rodzajZdarzenia">Rodzaj zdarzenia.</param>
    public static string EventCode(LineEventKind rodzajZdarzenia) => rodzajZdarzenia switch
    {
        LineEventKind.Take => "przejmij",
        LineEventKind.Release => "oddaj",
        LineEventKind.DoorOpen => "drzwi-otworz",
        LineEventKind.DoorClose => "drzwi-zamknij",
        LineEventKind.Observe => "obserwuj",
        _ => throw new ArgumentOutOfRangeException(nameof(rodzajZdarzenia), rodzajZdarzenia, "nieznany rodzaj zdarzenia linii"),
    };

    private static bool TryEventKind(string code, out LineEventKind rodzajZdarzenia)
    {
        foreach (var candidate in Enum.GetValues<LineEventKind>())
        {
            if (EventCode(candidate) == code)
            {
                rodzajZdarzenia = candidate;
                return true;
            }
        }

        rodzajZdarzenia = default;
        return false;
    }

    /// <summary>
    /// Stan klawiszy obowiązujący w zadanym kroku. Wyszukiwanie binarne, nie skan —
    /// metoda jest wołana raz na krok symulacji, czyli 120 razy na sekundę przejazdu.
    /// </summary>
    /// <param name="step">Numer kroku, od zera.</param>
    /// <returns>Stan klawiszy z ostatniego wpisu o numerze nie większym niż <paramref name="step"/>.</returns>
    public DriverKeys KeysAt(long step)
    {
        var low = 0;
        var high = _entries.Length - 1;
        var found = -1;
        while (low <= high)
        {
            var middle = low + ((high - low) / 2);
            if (_entries[middle].Step <= step)
            {
                found = middle;
                low = middle + 1;
            }
            else
            {
                high = middle - 1;
            }
        }

        return found < 0 ? DriverKeys.None : _entries[found].Keys;
    }

    /// <summary>
    /// Czy przed tym krokiem przejazd zaczyna się od nowa. Wyszukiwanie binarne
    /// z tego samego powodu, co w <see cref="KeysAt"/>: metoda jest wołana raz na krok
    /// symulacji, czyli 120 razy na sekundę przejazdu.
    /// </summary>
    /// <param name="step">Numer kroku sesji, od zera.</param>
    /// <returns><c>true</c>, jeżeli w zapisie stoi reset dokładnie w tym kroku.</returns>
    public bool IsResetAt(long step)
    {
        var low = 0;
        var high = _resets.Length - 1;
        while (low <= high)
        {
            var middle = low + ((high - low) / 2);
            var candidate = _resets[middle];
            if (candidate == step)
            {
                return true;
            }

            if (candidate < step)
            {
                low = middle + 1;
            }
            else
            {
                high = middle - 1;
            }
        }

        return false;
    }

    /// <summary>
    /// Zapis do tekstu. Kultura niezmienna i <c>\n</c> jako koniec wiersza, żeby plik
    /// wyszedł identyczny co do bajtu na każdej maszynie — jest porównywany <c>cmp</c>.
    /// </summary>
    /// <returns>Treść pliku zapisu wejść.</returns>
    public string ToText()
    {
        var text = new StringBuilder();
        text.Append("# METRO BXL — zapis wejść maszynisty\n");
        text.Append($"# klawisze: {DriverKeys.PowerCode} ciąg, {DriverKeys.BrakeCode} hamulec, ");
        text.Append($"{DriverKeys.CoastCode} wybieg, {DriverKeys.EmergencyCode} hamulec awaryjny ");
        text.Append($"(= pełny służbowy), {DriverKeys.NoneCode} nic\n");
        text.Append("# wpis obowiązuje od swojego kroku do kroku następnego wpisu\n");
        if (_resets.Length > 0)
        {
            text.Append(CultureInfo.InvariantCulture,
                $"# wpis '{ResetCode}' znaczy: PRZED tym krokiem przejazd zaczyna się od nowa;\n");
            text.Append("# numer kroku NIE wraca wtedy do zera, bo zapis indeksuje sesję, nie przejazd\n");
        }

        if (_events.Length > 0)
        {
            text.Append(CultureInfo.InvariantCulture,
                $"# zdarzenia linii 'kod{EventTrainSeparator}skład' wykonują się PRZED swoim krokiem: ");
            text.Append("przejmij, oddaj, drzwi-otworz, drzwi-zamknij, obserwuj\n");
        }

        text.Append(CultureInfo.InvariantCulture, $"{VersionField}={FormatVersion}\n");
        text.Append(CultureInfo.InvariantCulture, $"{StepsField}={Steps}\n");
        text.Append(ColumnHeader);
        text.Append('\n');

        // Wiersze idą po numerze kroku, a przy równym numerze reset stoi PRZED zmianą
        // klawiszy — bo tak też się wykonują. Plik czytany od góry do dołu opisuje więc
        // tę samą kolejność zdarzeń, którą wykona odtworzenie; inna kolejność zapisu
        // dałaby plik poprawny dla `Parse` i mylący dla człowieka.
        //
        // Zdarzenia linii (6.M1) stoją między resetem a zmianą klawiszy tego samego kroku:
        // wykonują się przed krokiem, tak jak reset, ale po nim — bo reset zaczyna
        // przejazd od nowa, a polecenie wydane po resecie dotyczy już nowego przejazdu.
        var nextEntry = 0;
        var nextReset = 0;
        var nextEvent = 0;
        while (nextEntry < _entries.Length || nextReset < _resets.Length || nextEvent < _events.Length)
        {
            var entryStep = nextEntry < _entries.Length ? _entries[nextEntry].Step : long.MaxValue;
            var eventStep = nextEvent < _events.Length ? _events[nextEvent].Step : long.MaxValue;
            var takeReset = nextReset < _resets.Length
                && _resets[nextReset] <= entryStep && _resets[nextReset] <= eventStep;
            if (takeReset)
            {
                text.Append(CultureInfo.InvariantCulture, $"{_resets[nextReset]};{ResetCode}\n");
                nextReset++;
            }
            else if (nextEvent < _events.Length && eventStep <= entryStep)
            {
                var lineEvent = _events[nextEvent];
                text.Append(CultureInfo.InvariantCulture,
                    $"{lineEvent.Step};{EventCode(lineEvent.Kind)}{EventTrainSeparator}{lineEvent.TrainId}\n");
                nextEvent++;
            }
            else
            {
                var entry = _entries[nextEntry];
                text.Append(CultureInfo.InvariantCulture, $"{entry.Step};{entry.Keys.Code()}\n");
                nextEntry++;
            }
        }

        return text.ToString();
    }

    /// <summary>
    /// Odczyt z tekstu. Każda niezgodność jest BŁĘDEM, a nie wartością domyślną:
    /// zapis, który cicho dojechał do innego przejazdu niż zapisany, jest gorszy niż
    /// brak zapisu, bo wygląda dokładnie tak samo jak dobry.
    /// </summary>
    /// <param name="text">Treść pliku zapisu wejść.</param>
    /// <returns>Odczytany zapis.</returns>
    /// <exception cref="ArgumentNullException">Tekst jest <c>null</c>.</exception>
    /// <exception cref="FormatException">Brakuje pola nagłówka, wiersz jest nieczytelny albo numery kroków nie rosną.</exception>
    public static InputLog Parse(string text)
    {
        ArgumentNullException.ThrowIfNull(text);

        long? version = null;
        long? steps = null;
        var inRows = false;
        var entries = new List<InputLogEntry>();
        var resets = new List<long>();
        var events = new List<InputLogEvent>();
        var lineNumber = 0;

        foreach (var raw in text.Split('\n'))
        {
            lineNumber++;
            var line = raw.Trim('\r', ' ', '\t');
            if (line.Length == 0 || line[0] == '#')
            {
                continue;
            }

            if (!inRows)
            {
                if (line == ColumnHeader)
                {
                    inRows = true;
                    continue;
                }

                var equals = line.IndexOf('=', StringComparison.Ordinal);
                if (equals < 0)
                {
                    throw new FormatException(
                        $"Wiersz {lineNumber} '{line}' nie jest ani polem nagłówka 'nazwa=wartość', "
                        + $"ani wierszem kolumn '{ColumnHeader}'.");
                }

                var name = line[..equals];
                var value = line[(equals + 1)..];
                if (!long.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var number))
                {
                    throw new FormatException(
                        $"Wiersz {lineNumber}: pole '{name}' ma wartość '{value}', która nie jest liczbą całkowitą.");
                }

                switch (name)
                {
                    case VersionField:
                        version = number;
                        break;
                    case StepsField:
                        steps = number;
                        break;
                    default:
                        throw new FormatException(
                            $"Wiersz {lineNumber}: nieznane pole nagłówka '{name}'. "
                            + $"Znane: {VersionField}, {StepsField}.");
                }

                continue;
            }

            var semicolon = line.IndexOf(';', StringComparison.Ordinal);
            if (semicolon < 0)
            {
                throw new FormatException(
                    $"Wiersz {lineNumber} '{line}' nie ma średnika; wpis ma postać 'krok;klawisze'.");
            }

            var stepText = line[..semicolon];
            if (!long.TryParse(stepText, NumberStyles.Integer, CultureInfo.InvariantCulture, out var entryStep))
            {
                throw new FormatException(
                    $"Wiersz {lineNumber}: '{stepText}' nie jest numerem kroku.");
            }

            var field = line[(semicolon + 1)..];
            if (field == ResetCode)
            {
                resets.Add(entryStep);
                continue;
            }

            var separator = field.IndexOf(EventTrainSeparator, StringComparison.Ordinal);
            if (separator >= 0)
            {
                if (!TryEventKind(field[..separator], out LineEventKind rodzajZdarzenia))
                {
                    throw new FormatException(
                        $"Wiersz {lineNumber}: '{field[..separator]}' nie jest zdarzeniem linii; "
                        + "znane: przejmij, oddaj, drzwi-otworz, drzwi-zamknij, obserwuj.");
                }

                events.Add(new InputLogEvent(entryStep, rodzajZdarzenia, field[(separator + 1)..]));
                continue;
            }

            DriverKeys keys;
            try
            {
                keys = DriverKeys.Parse(field);
            }
            catch (FormatException error)
            {
                throw new FormatException($"Wiersz {lineNumber}: {error.Message}", error);
            }

            entries.Add(new InputLogEntry(entryStep, keys));
        }

        if (version is null)
        {
            throw new FormatException($"Brak pola nagłówka '{VersionField}='.");
        }

        if (version != VersionWithoutResets && version != VersionWithResets
            && version != VersionWithLineEvents)
        {
            throw new FormatException(
                $"Zapis wejść jest w wersji {version}, a ta wersja programu czyta "
                + $"{VersionWithoutResets}, {VersionWithResets} i {VersionWithLineEvents}.");
        }

        // Ta sama zasada co przy resetach, o jeden rodzajZdarzenia wpisu dalej (6.M1): wersja 3
        // istnieje WYŁĄCZNIE dla zapisów ze zdarzeniami linii, a zapis bez nich musi
        // mówić o sobie 1 albo 2.
        if (version == VersionWithLineEvents && events.Count == 0)
        {
            throw new FormatException(
                $"Zapis mówi '{VersionField}={VersionWithLineEvents}', a nie ma ani jednego "
                + "zdarzenia linii; zapis bez nich jest w wersji "
                + $"{VersionWithoutResets} albo {VersionWithResets}.");
        }

        if (version != VersionWithLineEvents && events.Count > 0)
        {
            throw new FormatException(
                $"Zapis mówi '{VersionField}={version}', a zawiera {events.Count} zdarzeń linii; "
                + $"zdarzenia istnieją dopiero od wersji {VersionWithLineEvents}.");
        }

        // WERSJA MA ZGADZAĆ SIĘ Z TREŚCIĄ W OBIE STRONY. Plik, który mówi o sobie co
        // innego, niż zawiera, jest gorszy niż plik odrzucony, bo wygląda dokładnie tak
        // samo jak poprawny — a to jest ta sama zasada, dla której każda niezgodność
        // w tym pliku jest błędem, a nie wartością domyślną.
        if (version == VersionWithoutResets && resets.Count > 0)
        {
            throw new FormatException(
                $"Zapis mówi '{VersionField}={VersionWithoutResets}', a zawiera {resets.Count} "
                + $"wpisów '{ResetCode}'; reset istnieje dopiero od wersji {VersionWithResets}.");
        }

        if (version == VersionWithResets && resets.Count == 0)
        {
            throw new FormatException(
                $"Zapis mówi '{VersionField}={VersionWithResets}', a nie ma ani jednego wpisu "
                + $"'{ResetCode}'; zapis bez resetu jest w wersji {VersionWithoutResets}.");
        }

        if (steps is null)
        {
            throw new FormatException($"Brak pola nagłówka '{StepsField}='.");
        }

        if (!inRows)
        {
            throw new FormatException($"Brak wiersza kolumn '{ColumnHeader}'.");
        }

        return new InputLog(steps.Value, entries, resets, events);
    }
}
