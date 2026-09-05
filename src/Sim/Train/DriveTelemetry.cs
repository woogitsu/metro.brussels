using System;
using System.Globalization;
using MetroBxl.Sim.Physics;

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

    /// <summary>Nazwa fazy dla przejazdu prowadzonego przez człowieka albo z zapisu wejść.</summary>
    /// <remarks>
    /// Przejazd ręczny nie ma faz scenariusza — nikt nie zapisał z góry, gdzie skład
    /// ciągnie, a gdzie hamuje, bo o tym decyduje maszynista w każdym kroku. Kolumna
    /// zostaje, bo format jest jeden dla wszystkich przejazdów i porównanie z rdzeniem
    /// (próg 0) porównuje wiersze, nie podzbiory kolumn.
    /// </remarks>
    public const string ManualPhase = "manual";

    /// <summary>Jeden wiersz telemetrii z bieżącego stanu przejazdu.</summary>
    /// <param name="drive">Przejazd po scenariuszu.</param>
    /// <returns>Wiersz CSV zgodny z <see cref="Header"/>.</returns>
    public static string Row(ScenarioDrive drive)
    {
        ArgumentNullException.ThrowIfNull(drive);

        return Row(
            drive.State, drive.TimeStep, drive.ChainageM,
            drive.AccelerationMps2, drive.Command, drive.Phase);
    }

    /// <summary>
    /// Jeden wiersz telemetrii ze składników. Przeciążenie istnieje, bo przejazd
    /// prowadzony przez człowieka (albo odtworzony z zapisu wejść) nie ma
    /// <see cref="ScenarioDrive"/> — a musi wypisywać wiersz IDENTYCZNY co do bajtu,
    /// inaczej porównanie z rdzeniem przy progu 0 porównywałoby formatowanie.
    /// Wersja ze scenariuszem woła tę i nie ma własnego napisu formatującego.
    /// </summary>
    /// <param name="state">Stan składu po kroku.</param>
    /// <param name="step">Krok symulacji, z którego liczy się czas.</param>
    /// <param name="chainageM">Kilometraż czoła składu, w metrach.</param>
    /// <param name="accelerationMps2">Przyspieszenie w tym kroku, m/s².</param>
    /// <param name="command">Położenie nastawników w tym kroku.</param>
    /// <param name="phase">Nazwa fazy przejazdu.</param>
    /// <returns>Wiersz CSV zgodny z <see cref="Header"/>.</returns>
    public static string Row(
        DriveState state,
        FixedStep step,
        double chainageM,
        double accelerationMps2,
        DriverCommand command,
        string phase)
        => string.Create(
            CultureInfo.InvariantCulture,
            $"{state.Steps},{state.TimeSeconds(step):R},{chainageM:R},{state.DistanceM:R},{state.SpeedMps:R},{state.SpeedKmh:R},{accelerationMps2:R},{command.Throttle:R},{command.Brake:R},{phase}");

    /// <summary>Czy przy tym numerze kroku wypada próbka.</summary>
    public static bool IsSample(long steps, long everySteps) => everySteps <= 1 || steps % everySteps == 0;
}
