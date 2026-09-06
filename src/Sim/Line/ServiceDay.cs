using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Jeden obieg pojazdu — w GTFS <c>block_id</c>, czyli kursy wykonywane po kolei tym
/// samym składem.
/// </summary>
/// <param name="Id">Identyfikator obiegu z feedu.</param>
/// <param name="Windows">Okna kursów, sekundy od północy dnia służby, w kolejności.</param>
public readonly record struct ServiceBlock(string Id, IReadOnlyList<(double StartS, double EndS)> Windows)
{
    /// <summary>Wyjazd pierwszego kursu obiegu.</summary>
    public double FirstDepartureS => Windows[0].StartS;

    /// <summary>Przyjazd ostatniego kursu obiegu; doba służby wychodzi poza 24:00.</summary>
    public double LastArrivalS
    {
        get
        {
            var last = Windows[0].EndS;
            for (var i = 1; i < Windows.Count; i++)
            {
                if (Windows[i].EndS > last)
                {
                    last = Windows[i].EndS;
                }
            }

            return last;
        }
    }

    /// <summary>Ile obieg stoi w służbie, w sekundach.</summary>
    public double SpanSeconds => LastArrivalS - FirstDepartureS;

    /// <summary>Liczba kursów w obiegu.</summary>
    public int Trips => Windows.Count;

    /// <summary>
    /// Czy obieg jest w służbie w danej chwili. Przedział jest DOMKNIĘTY z obu stron:
    /// skład, który właśnie dojechał, jeszcze zajmuje tor.
    /// </summary>
    /// <param name="seconds">Chwila, sekundy od północy dnia służby.</param>
    public bool InServiceAt(double seconds) => seconds >= FirstDepartureS && seconds <= LastArrivalS;

    /// <summary>
    /// Ile par kolejnych kursów tego obiegu na siebie zachodzi. Jeden pojazd nie jedzie
    /// dwoma kursami naraz, więc każda taka para jest błędem w feedzie — i ma się
    /// zgłosić, a nie przemilczeć.
    /// </summary>
    public int OverlappingTrips
    {
        get
        {
            var count = 0;
            for (var i = 1; i < Windows.Count; i++)
            {
                if (Windows[i].StartS < Windows[i - 1].EndS)
                {
                    count++;
                }
            }

            return count;
        }
    }
}

/// <summary>Szczyt jednoczesności: ile obiegów naraz i o której.</summary>
/// <param name="Blocks">Największa liczba obiegów jednocześnie w służbie.</param>
/// <param name="AtSeconds">Chwila, w której ta liczba pada po raz pierwszy.</param>
public readonly record struct ServicePeak(int Blocks, double AtSeconds)
{
    /// <summary>Chwila jako <c>HH:MM:SS</c>, z godziną mogącą przekroczyć 24.</summary>
    public string AtClock => ServiceDay.Clock(AtSeconds);
}

/// <summary>
/// Doba służby odtworzona z obiegów rozkładu.
///
/// <para><b>Po co to jest w rdzeniu, skoro liczy to już <c>tools/track/timetable.py</c>.</b>
/// Bo <c>Sim.Runner line</c> dodaje JEDEN skład, a <c>budget</c> dodaje N składów na
/// równym takcie — żadne z nich nie odtwarza doby z obiegów. Wpis T-320 wypisuje to
/// wprost jako część, która „Zostaje". Liczby narzędzia Pythona są przy tym punktem
/// odniesienia, a nie źródłem: rdzeń liczy je z okien kursów DRUGI RAZ i różnica
/// choćby o jeden obieg jest wynikiem do zapisania, nie do zaokrąglenia.</para>
///
/// <para><b>Czego ta klasa nie robi.</b> Nie modeluje perturbacji ani polityki
/// dyspozytora — to jest 6.A4 i czeka na decyzję właściciela. Doba służby jest
/// odtworzeniem rozkładu, nie modelem zakłóceń.</para>
/// </summary>
public sealed class ServiceDay
{
    private readonly ServiceBlock[] _blocks;

    private ServiceDay(string date, ServiceBlock[] blocks)
    {
        Date = date;
        _blocks = blocks;
    }

    /// <summary>Dzień odniesienia, <c>RRRRMMDD</c>.</summary>
    public string Date { get; }

    /// <summary>Obiegi, w kolejności z pliku.</summary>
    public IReadOnlyList<ServiceBlock> Blocks => _blocks;

    /// <summary>Liczba obiegów — czyli składów w ruchu w ciągu doby, bez rezerwy.</summary>
    public int BlockCount => _blocks.Length;

    /// <summary>Suma nakładek między kolejnymi kursami w obrębie jednego obiegu.</summary>
    public int OverlappingTripsInABlock
    {
        get
        {
            var count = 0;
            foreach (var block in _blocks)
            {
                count += block.OverlappingTrips;
            }

            return count;
        }
    }

    /// <summary>Ile obiegów jest w służbie w danej chwili.</summary>
    /// <param name="seconds">Chwila, sekundy od północy dnia służby.</param>
    public int ConcurrentAt(double seconds)
    {
        var count = 0;
        foreach (var block in _blocks)
        {
            if (block.InServiceAt(seconds))
            {
                count++;
            }
        }

        return count;
    }

    /// <summary>
    /// Szczyt jednoczesności, liczony zamiataniem po zdarzeniach.
    ///
    /// <para><b>Kolejność przy remisie jest częścią definicji, nie szczegółem.</b>
    /// Gdy jeden obieg kończy się dokładnie w sekundzie, w której zaczyna się drugi,
    /// wejście liczy się PRZED wyjściem — bo przedział służby jest domknięty z obu
    /// stron i w tej sekundzie oba składy stoją na sieci. Odwrotna kolejność dałaby
    /// szczyt mniejszy o jeden i wyglądałaby tak samo poprawnie.</para>
    /// </summary>
    public ServicePeak Peak
    {
        get
        {
            var events = new List<(double At, int Delta)>(_blocks.Length * 2);
            foreach (var block in _blocks)
            {
                events.Add((block.FirstDepartureS, +1));
                events.Add((block.LastArrivalS, -1));
            }

            events.Sort(static (a, b) =>
            {
                var byTime = a.At.CompareTo(b.At);
                return byTime != 0 ? byTime : b.Delta.CompareTo(a.Delta);
            });

            var current = 0;
            var best = 0;
            var at = 0.0;
            foreach (var (moment, delta) in events)
            {
                current += delta;
                if (current > best)
                {
                    best = current;
                    at = moment;
                }
            }

            return new ServicePeak(best, at);
        }
    }

    /// <summary>
    /// Doba służby z treści <c>build/timetable.json</c>.
    /// </summary>
    /// <param name="json">Zawartość pliku rozkładu.</param>
    /// <exception cref="ArgumentException">Gdy pliku nie da się odczytać jako doby służby.</exception>
    public static ServiceDay FromJson(string json)
    {
        ArgumentNullException.ThrowIfNull(json);

        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;

        var date = root.TryGetProperty("date", out var dateElement)
            ? dateElement.GetString() ?? "?"
            : "?";

        if (!root.TryGetProperty("duties", out var duties) ||
            !duties.TryGetProperty("rows", out var rows))
        {
            throw new ArgumentException(
                "rozkład bez sekcji duties.rows — to nie jest wynik tools/track/timetable.py",
                nameof(json));
        }

        var blocks = new List<ServiceBlock>();
        foreach (var row in rows.EnumerateArray())
        {
            var id = row.TryGetProperty("block_id", out var idElement)
                ? idElement.GetString() ?? "?"
                : "?";

            if (!row.TryGetProperty("trip_windows", out var windowArray))
            {
                // Bez okien kursów rdzeń nie ma z czego liczyć NIC drugi raz — mógłby
                // co najwyżej przepisać liczby Pythona. Odmowa jest tu jedyną uczciwą
                // odpowiedzią; cicha zgoda dałaby bramkę, która porównuje liczbę
                // ze sobą samą.
                throw new ArgumentException(
                    $"obieg {id} bez `trip_windows` — rozkład pochodzi ze starszej wersji " +
                    "tools/track/timetable.py i nie da się z niego odtworzyć doby",
                    nameof(json));
            }

            var windows = new List<(double StartS, double EndS)>();
            foreach (var window in windowArray.EnumerateArray())
            {
                windows.Add((window[0].GetDouble(), window[1].GetDouble()));
            }

            if (windows.Count == 0)
            {
                throw new ArgumentException($"obieg {id} bez ani jednego kursu", nameof(json));
            }

            blocks.Add(new ServiceBlock(id, windows));
        }

        if (blocks.Count == 0)
        {
            throw new ArgumentException("rozkład bez ani jednego obiegu", nameof(json));
        }

        return new ServiceDay(date, blocks.ToArray());
    }

    /// <summary>
    /// Sekundy od północy jako <c>HH:MM:SS</c>. Godzina MOŻE przekroczyć 24 i to nie
    /// jest błąd: doba służby kończy się po północy, a GTFS zapisuje to właśnie tak.
    /// </summary>
    /// <param name="seconds">Sekundy od północy dnia służby.</param>
    public static string Clock(double seconds)
    {
        var total = (long)Math.Round(seconds, MidpointRounding.AwayFromZero);
        var hours = total / 3600L;
        var minutes = (total % 3600L) / 60L;
        var rest = total % 60L;
        return string.Create(CultureInfo.InvariantCulture, $"{hours:00}:{minutes:00}:{rest:00}");
    }
}
