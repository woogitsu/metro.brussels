using System;
using System.Globalization;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Format telemetrii przejazdu. Jedno miejsce, w którym powstaje wiersz CSV, bo dwa
/// miejsca rozjechałyby się formatowaniem i porównanie Godota z rdzeniem porównywałoby
/// wtedy zaokrąglenia, a nie fizykę.
///
/// Liczby idą formatem <c>R</c> (round-trip) i w kulturze niezmiennej. To jest brzydkie
/// w czytaniu i **zamierzone**: wiersz z <c>F3</c> ukryłby rozjazd na czwartym miejscu
/// po przecinku, a właśnie po to ten plik powstaje. Do raportu i tak liczy się różnica
/// wyliczona z parsowanych liczb, a nie wygląd wiersza.
/// </summary>
public static class DriveTelemetry
{
    /// <summary>Co ile kroków wypada próbka: 120 kroków = 1 s przy kroku rdzenia.</summary>
    public const long DefaultSampleEverySteps = 120;

    /// <summary>Nagłówek pliku telemetrii.</summary>
    public const string Header = "step,t_s,chainage_m,distance_m,speed_mps,speed_kmh,accel_mps2,throttle,brake,phase";

    /// <summary>Liczba kolumn wiersza telemetrii.</summary>
    public const int ColumnCount = 10;

    /// <summary>Jeden wiersz telemetrii z bieżącego stanu przejazdu.</summary>
    public static string Row(ScenarioDrive drive)
    {
        ArgumentNullException.ThrowIfNull(drive);

        var state = drive.State;
        return string.Create(
            CultureInfo.InvariantCulture,
            $"{state.Steps},{state.TimeSeconds(drive.TimeStep):R},{drive.ChainageM:R},{state.DistanceM:R},{state.SpeedMps:R},{state.SpeedKmh:R},{drive.AccelerationMps2:R},{drive.Command.Throttle:R},{drive.Command.Brake:R},{drive.Phase}");
    }

    /// <summary>Czy przy tym numerze kroku wypada próbka.</summary>
    public static bool IsSample(long steps, long everySteps) => everySteps <= 1 || steps % everySteps == 0;
}
