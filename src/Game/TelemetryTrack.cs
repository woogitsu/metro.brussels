using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game;

/// <summary>
/// Jedna próbka odczytana z pliku telemetrii — stan składu w jednym kroku, taki jaki
/// ZOSTAŁ ZAPISANY, a nie policzony jeszcze raz.
///
/// <para>Pola są dokładnie tymi, które <see cref="DriveTelemetry.Header"/> wymienia
/// jako kolumny nieliczone z innych: <c>t_s</c> wynika z <see cref="Steps"/> i kroku,
/// a <c>speed_kmh</c> z <see cref="SpeedMps"/>, więc drugi raz ich tu nie ma. Kopia
/// liczby, która jest funkcją innej liczby, rozjeżdża się z nią po cichu — ta sama
/// zasada, dla której <c>RunHeader</c> nie przyjmuje limitu parametrem.</para>
/// </summary>
/// <param name="Steps">Numer kroku symulacji, z którego pochodzi próbka.</param>
/// <param name="ChainageM">Kilometraż czoła składu, w metrach.</param>
/// <param name="DistanceM">Droga przebyta od początku przebiegu, w metrach.</param>
/// <param name="SpeedMps">Prędkość w tym kroku, m/s.</param>
/// <param name="AccelerationMps2">Przyspieszenie w tym kroku, m/s².</param>
/// <param name="Command">Położenie nastawników w tym kroku.</param>
/// <param name="Phase">Nazwa fazy przejazdu, przepisana z pliku.</param>
public readonly record struct TelemetrySample(
    long Steps,
    double ChainageM,
    double DistanceM,
    double SpeedMps,
    double AccelerationMps2,
    DriverCommand Command,
    string Phase)
{
    /// <summary>
    /// Stan składu widziany przez rdzeń. Opóźnienie hamulca jest zerem, bo telemetria
    /// go nie niesie — i nie musi: w odtwarzaniu nikt nie całkuje, a
    /// <see cref="DriveTelemetry.Row(DriveState, FixedStep, double, double, DriverCommand, string)"/>
    /// tego pola nie wypisuje. Podstawienie tu czegokolwiek innego byłoby liczbą
    /// zmyśloną, która nigdzie nie wychodzi i której nikt nie sprawdzi.
    /// </summary>
    public DriveState State => new(Steps, SpeedMps, DistanceM, 0.0);

    /// <summary>Ta próbka złożona z powrotem w wiersz CSV, tym samym formatem co rdzeń.</summary>
    /// <param name="step">Krok stały, z którego liczy się kolumna <c>t_s</c>.</param>
    /// <returns>Wiersz zgodny z <see cref="DriveTelemetry.Header"/>.</returns>
    public string Row(FixedStep step)
        => DriveTelemetry.Row(State, step, ChainageM, AccelerationMps2, Command, Phase);
}

/// <summary>
/// Zapis przejazdu wczytany z pliku telemetrii — wejście trybu
/// <c>--from-telemetry</c>.
///
/// <para><b>To NIE jest <c>--replay</c> i różnica jest cała.</b> Zapis wejść
/// (<see cref="InputLog"/>, #239) niesie KLAWISZE i przechodzi przez tę samą fizykę,
/// co człowiek przy klawiaturze; telemetria niesie WYNIK i jest odtwarzana jako ruch
/// zadany. Pierwsze odpowiada na pytanie „czy rdzeń policzy to samo drugi raz",
/// drugie na „czy scena pokaże to, co już policzono". Jedno źródło poleceń nie
/// zastępuje drugiego i dlatego <c>RunPlan</c> odmawia ich łączenia.</para>
///
/// <para><b>Dlaczego plik BEZ GODOTA.</b> Ta sama konwencja i ten sam powód, co przy
/// <see cref="RunPlan"/> i <see cref="RunHeader"/>: parsowanie da się wtedy zawołać
/// wprost z <c>tests/Game.Tests</c>, a w scenie zostaje wyłącznie odczyt bajtów
/// przez <c>FileAccess</c>.</para>
///
/// <para><b>Kontrola najostrzejsza z możliwych: wiersz musi się ZŁOŻYĆ Z POWROTEM.</b>
/// Po sparsowaniu każdy wiersz jest składany na nowo przez
/// <see cref="DriveTelemetry"/> i porównywany z oryginałem CO DO BAJTU. Plik, który
/// tego nie przechodzi, nie jest telemetrią tego rdzenia i odtwarzanie go byłoby
/// pokazywaniem przejazdu, którego rdzeń nigdy nie policzył. Przy okazji ta jedna
/// kontrola zastępuje dwie oddzielne — zgodność <c>t_s</c> z liczbą kroków i
/// <c>speed_kmh</c> z <c>speed_mps</c> — bo obie te kolumny są w składaniu wyliczane,
/// a nie przepisywane.</para>
///
/// <para><b>Czego ta kontrola NIE robi, i to jest ważne dla bramki CI.</b> Nie czyni
/// porównania <c>Sim.Runner compare</c> bezprzedmiotowym: gwarantuje wyłącznie, że
/// POJEDYNCZY wiersz wychodzi taki sam, a nie że wyszły wszystkie, w tej samej
/// kolejności i po jednym razie. Zgubiona, powtórzona albo przestawiona próbka
/// przechodzi tę kontrolę i wywala porównanie — czyli dokładnie to, co porównanie
/// ma badać: pętlę odtwarzania, nie formatowanie liczby.</para>
/// </summary>
public sealed class TelemetryTrack
{
    private TelemetryTrack(IReadOnlyList<TelemetrySample> samples)
    {
        Samples = samples;
    }

    /// <summary>Próbki w kolejności z pliku; co najmniej jedna, o rosnących numerach kroków.</summary>
    public IReadOnlyList<TelemetrySample> Samples { get; }

    /// <summary>Numer kroku pierwszej próbki — od niego rusza głowica odtwarzania.</summary>
    public long FirstStep => Samples[0].Steps;

    /// <summary>Numer kroku ostatniej próbki — na nim odtwarzanie się kończy.</summary>
    public long LastStep => Samples[Samples.Count - 1].Steps;

    /// <summary>
    /// Czyta plik telemetrii. Nie rzuca wyjątków: odmowa jest wartością zwracaną
    /// wraz z powodem, tak samo jak w <see cref="RunPlan.Parse"/> — scena musi umieć
    /// z niej zrobić kod wyjścia, a nie wyjątek w środku <c>_Ready</c>.
    /// </summary>
    /// <param name="text">Zawartość pliku CSV.</param>
    /// <param name="step">Krok stały rdzenia, którym liczy się kolumna <c>t_s</c>.</param>
    /// <param name="track">Wczytany zapis albo <c>null</c>, gdy plik jest odrzucony.</param>
    /// <param name="error">Powód odmowy albo <c>null</c>.</param>
    /// <returns>Prawda, gdy plik da się odtworzyć.</returns>
    public static bool TryParse(string text, FixedStep step, out TelemetryTrack? track, out string? error)
    {
        track = null;
        error = null;
        step.RequireValid();

        var lines = (text ?? string.Empty).Replace("\r\n", "\n", StringComparison.Ordinal).Split('\n');
        var rows = new List<string>(lines.Length);
        foreach (var line in lines)
        {
            // Pusty wiersz na końcu pliku jest normalny — `FileAccess.StoreLine`
            // kończy każdy wiersz znakiem nowej linii — więc jego pominięcie nie jest
            // pobłażliwością. Pusty wiersz w ŚRODKU odsiewa się tak samo, bo nie da
            // się z niego zrobić próbki, a numer wiersza w komunikacie i tak liczy
            // się od oryginału.
            if (line.Length > 0)
            {
                rows.Add(line);
            }
        }

        if (rows.Count == 0)
        {
            error = "[TELEMETRIA] plik jest pusty: nie ma czego odtwarzać";
            return false;
        }

        if (!string.Equals(rows[0], DriveTelemetry.Header, StringComparison.Ordinal))
        {
            error = $"[TELEMETRIA] nagłówek '{rows[0]}' nie jest nagłówkiem rdzenia "
                + $"'{DriveTelemetry.Header}'";
            return false;
        }

        if (rows.Count == 1)
        {
            error = "[TELEMETRIA] plik ma sam nagłówek, bez ani jednej próbki";
            return false;
        }

        var samples = new List<TelemetrySample>(rows.Count - 1);
        var previousSteps = long.MinValue;
        for (var index = 1; index < rows.Count; index++)
        {
            if (!TryRow(rows[index], step, index, previousSteps, out var sample, out error))
            {
                return false;
            }

            previousSteps = sample.Steps;
            samples.Add(sample);
        }

        track = new TelemetryTrack(samples);
        return true;
    }

    private static bool TryRow(
        string line, FixedStep step, int index, long previousSteps,
        out TelemetrySample sample, out string? error)
    {
        sample = default;
        error = null;

        var columns = line.Split(',');
        if (columns.Length != DriveTelemetry.ColumnCount)
        {
            error = $"[TELEMETRIA] wiersz {index}: kolumn {columns.Length}, "
                + $"a format rdzenia ma {DriveTelemetry.ColumnCount}";
            return false;
        }

        if (!long.TryParse(columns[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out var steps)
            || steps < 0)
        {
            error = $"[TELEMETRIA] wiersz {index}: '{columns[0]}' nie jest nieujemnym numerem kroku";
            return false;
        }

        // Numery kroków muszą ROSNĄĆ. Ten warunek nie jest higieną formatu: głowica
        // odtwarzania idzie po jednym kroku i przyjmuje próbkę, gdy w nią trafi.
        // Próbka z numerem nie większym od poprzedniej nie zostałaby przyjęta nigdy,
        // przebieg zawisłby na niej do wypalenia `timeout-minutes` — dokładnie ta
        // rodzina usterek, którą w tym pliku zamknęło `double.IsFinite`.
        if (steps <= previousSteps)
        {
            error = $"[TELEMETRIA] wiersz {index}: krok {steps} nie jest większy "
                + $"od kroku {previousSteps} w wierszu poprzednim";
            return false;
        }

        if (!TryNumber(columns[2], index, "chainage_m", out var chainage, out error)
            || !TryNumber(columns[3], index, "distance_m", out var distance, out error)
            || !TryNumber(columns[4], index, "speed_mps", out var speed, out error)
            || !TryNumber(columns[6], index, "accel_mps2", out var acceleration, out error)
            || !TryNumber(columns[7], index, "throttle", out var throttle, out error)
            || !TryNumber(columns[8], index, "brake", out var brake, out error))
        {
            return false;
        }

        sample = new TelemetrySample(
            steps, chainage, distance, speed, acceleration,
            new DriverCommand(throttle, brake), columns[9]);

        // ZŁOŻENIE Z POWROTEM. Kolumny `t_s` i `speed_kmh` nie są tu przepisywane,
        // tylko liczone — więc plik, w którym czas nie zgadza się z liczbą kroków
        // albo km/h z m/s, wychodzi z tego składania inny i zostaje odrzucony
        // z numerem wiersza. Porównanie idzie CO DO BAJTU, bo format `R` jest
        // dwustronny: liczba wypisana i wczytana z powrotem daje ten sam bit.
        var rebuilt = sample.Row(step);
        if (!string.Equals(rebuilt, line, StringComparison.Ordinal))
        {
            error = $"[TELEMETRIA] wiersz {index} nie składa się z powrotem formatem rdzenia: "
                + $"'{line}' -> '{rebuilt}'";
            sample = default;
            return false;
        }

        return true;
    }

    private static bool TryNumber(
        string text, int index, string column, out double value, out string? error)
    {
        error = null;

        // `IsFinite` obok `TryParse`, z tego samego powodu co w `RunPlan.TryDouble`:
        // `TryParse` przyjmuje "Infinity" i "NaN", a nieskończony kilometraż ustawiłby
        // skład w miejscu, którego macierz kamery nie umie policzyć.
        if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value)
            && double.IsFinite(value))
        {
            return true;
        }

        value = 0.0;
        error = $"[TELEMETRIA] wiersz {index}, kolumna {column}: "
            + $"'{text}' nie jest skończoną liczbą";
        return false;
    }
}
