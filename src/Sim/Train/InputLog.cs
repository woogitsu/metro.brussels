using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace MetroBxl.Sim.Train;

/// <summary>Jedna zmiana stanu klawiszy w zapisie wejść.</summary>
/// <param name="Step">Numer kroku symulacji, od którego ten stan obowiązuje.</param>
/// <param name="Keys">Stan klawiszy obowiązujący od tego kroku do następnego wpisu.</param>
public readonly record struct InputLogEntry(long Step, DriverKeys Keys);

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
/// # klawisze: W ciąg, S hamulec, X wybieg, - nic
/// wersja=1
/// kroki=7200
/// krok;klawisze
/// 0;W
/// 3600;S
/// </code>
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
    /// <summary>Wersja formatu, którą ta klasa czyta i pisze.</summary>
    public const int Version = 1;

    /// <summary>Nazwa pola nagłówka z wersją formatu.</summary>
    public const string VersionField = "wersja";

    /// <summary>Nazwa pola nagłówka z liczbą kroków przejazdu.</summary>
    public const string StepsField = "kroki";

    /// <summary>Wiersz nazw kolumn, oddzielający nagłówek od wpisów.</summary>
    public const string ColumnHeader = "krok;klawisze";

    private readonly InputLogEntry[] _entries;

    /// <summary>
    /// Zapis z jawnej listy wpisów.
    /// </summary>
    /// <param name="steps">Liczba kroków przejazdu; nieujemna.</param>
    /// <param name="entries">Wpisy w rosnącej kolejności numerów kroków.</param>
    /// <exception cref="ArgumentNullException">Lista wpisów jest <c>null</c>.</exception>
    /// <exception cref="ArgumentOutOfRangeException">Liczba kroków jest ujemna.</exception>
    /// <exception cref="ArgumentException">Numery kroków nie rosną, są ujemne albo wychodzą poza przejazd.</exception>
    public InputLog(long steps, IReadOnlyList<InputLogEntry> entries)
    {
        ArgumentNullException.ThrowIfNull(entries);
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

        Steps = steps;
        _entries = copy;
    }

    /// <summary>Liczba kroków przejazdu. Odtworzenie kończy się po tylu krokach.</summary>
    public long Steps { get; }

    /// <summary>Wpisy zapisu, w rosnącej kolejności numerów kroków.</summary>
    public IReadOnlyList<InputLogEntry> Entries => _entries;

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
    /// Zapis do tekstu. Kultura niezmienna i <c>\n</c> jako koniec wiersza, żeby plik
    /// wyszedł identyczny co do bajtu na każdej maszynie — jest porównywany <c>cmp</c>.
    /// </summary>
    /// <returns>Treść pliku zapisu wejść.</returns>
    public string ToText()
    {
        var text = new StringBuilder();
        text.Append("# METRO BXL — zapis wejść maszynisty\n");
        text.Append($"# klawisze: {DriverKeys.PowerCode} ciąg, {DriverKeys.BrakeCode} hamulec, ");
        text.Append($"{DriverKeys.CoastCode} wybieg, {DriverKeys.NoneCode} nic\n");
        text.Append("# wpis obowiązuje od swojego kroku do kroku następnego wpisu\n");
        text.Append(CultureInfo.InvariantCulture, $"{VersionField}={Version}\n");
        text.Append(CultureInfo.InvariantCulture, $"{StepsField}={Steps}\n");
        text.Append(ColumnHeader);
        text.Append('\n');
        foreach (var entry in _entries)
        {
            text.Append(CultureInfo.InvariantCulture, $"{entry.Step};{entry.Keys.Code()}\n");
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

            DriverKeys keys;
            try
            {
                keys = DriverKeys.Parse(line[(semicolon + 1)..]);
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

        if (version != Version)
        {
            throw new FormatException(
                $"Zapis wejść jest w wersji {version}, a ta wersja programu czyta {Version}.");
        }

        if (steps is null)
        {
            throw new FormatException($"Brak pola nagłówka '{StepsField}='.");
        }

        if (!inRows)
        {
            throw new FormatException($"Brak wiersza kolumn '{ColumnHeader}'.");
        }

        return new InputLog(steps.Value, entries);
    }
}
