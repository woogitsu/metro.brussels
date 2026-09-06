using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Game;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Testy wczytywania pliku telemetrii dla trybu <c>--from-telemetry</c>
/// (<see cref="TelemetryTrack"/>).
///
/// <para><b>Dlaczego to ma testy jednostkowe, a nie tylko bramkę w CI.</b> Bramka
/// w <c>godot-first-run.yml</c> odpowiada na jedno pytanie — czy przejazd wczytany
/// i wypisany jest ten sam co do bajtu — i odpowiada na nie WYŁĄCZNIE dla plików
/// poprawnych. Wszystkie odmowy: zły nagłówek, brakująca kolumna, krok, który nie
/// rośnie, czas niezgodny z liczbą kroków — są gałęziami, których żaden zielony
/// przebieg nie dotyka. To ta sama dziura, którą w <c>src/Game</c> zamknął
/// <c>RunPlanTests</c>: klasa pilnowana wyłącznie integracyjnie nie ma
/// przetestowanej ani jednej ścieżki błędu.</para>
/// </summary>
[TestClass]
public sealed class TelemetryTrackTests
{
    private static FixedStep Step => FixedStep.Simulation;

    /// <summary>Wiersz w formacie rdzenia, złożony przez ten sam kod, co scena.</summary>
    private static string Row(long steps, double chainage, double distance, double speed,
        double acceleration, double throttle, double brake, string phase)
        => DriveTelemetry.Row(
            new DriveState(steps, speed, distance, 0.0), Step, chainage, acceleration,
            new DriverCommand(throttle, brake), phase);

    private static string File(params string[] rows)
    {
        var lines = new List<string> { DriveTelemetry.Header };
        lines.AddRange(rows);
        return string.Join("\n", lines) + "\n";
    }

    private static TelemetryTrack ParseOrFail(string text)
    {
        Assert.IsTrue(TelemetryTrack.TryParse(text, Step, out var track, out var error), error);
        Assert.IsNotNull(track);
        return track!;
    }

    private static string RefuseAndGetReason(string text)
    {
        var accepted = TelemetryTrack.TryParse(text, Step, out var track, out var error);
        Assert.IsFalse(accepted, "plik przeszedł, choć nie powinien");
        Assert.IsNull(track, "odrzucony plik zwrócił zapis");
        Assert.IsNotNull(error, "odmowa nie niesie powodu");
        return error!;
    }

    // --- plik poprawny ------------------------------------------------------------

    [TestMethod]
    public void ASampleCarriesEveryColumnTheFormatHas()
    {
        var text = File(
            Row(0, 94.0, 0.0, 0.0, 0.0, 1.0, 0.0, "traction"),
            Row(120, 94.5, 0.5, 1.25, 1.0, 1.0, 0.0, "traction"),
            Row(240, 97.0, 3.0, 2.5, 0.5, 0.0, 1.0, "brake"));

        var track = ParseOrFail(text);

        Assert.AreEqual(3, track.Samples.Count);
        Assert.AreEqual(0L, track.FirstStep);
        Assert.AreEqual(240L, track.LastStep);

        var last = track.Samples[2];
        Assert.AreEqual(240L, last.Steps);
        Assert.AreEqual(97.0, last.ChainageM, 1e-12);
        Assert.AreEqual(3.0, last.DistanceM, 1e-12);
        Assert.AreEqual(2.5, last.SpeedMps, 1e-12);
        Assert.AreEqual(0.5, last.AccelerationMps2, 1e-12);
        Assert.AreEqual(0.0, last.Command.Throttle, 1e-12);
        Assert.AreEqual(1.0, last.Command.Brake, 1e-12);
        Assert.AreEqual("brake", last.Phase);
    }

    [TestMethod]
    public void EverySampleGoesBackToTheByteItCameFrom()
    {
        // WŁAŚCIWOŚĆ, NA KTÓREJ STOI CAŁY TRYB: echo pliku ma być tym samym plikiem.
        // Tu jest sprawdzona bez silnika i bez pętli klatek, czyli tam, gdzie widać,
        // że bierze się z formatu, a nie ze szczęścia.
        var rows = new[]
        {
            Row(0, 94.0, 0.0, 0.0, 0.0, 1.0, 0.0, "traction"),
            Row(120, 94.516622262232141, 0.516622262232141, 1.024662174324133, 1.02452292357, 1.0, 0.0, "traction"),
            Row(38194, 6653.791185780133, 6559.791185780133, 0.0, -1.1136219962287026, 0.0, 1.0, "brake"),
        };

        var track = ParseOrFail(File(rows));

        Assert.AreEqual(rows.Length, track.Samples.Count);
        for (var index = 0; index < rows.Length; index++)
        {
            Assert.AreEqual(rows[index], track.Samples[index].Row(Step),
                $"próbka {index} nie składa się z powrotem");
        }
    }

    [TestMethod]
    public void TheStateHandedToTheSceneIsTheCoresOwnState()
    {
        // Scena podstawia tę strukturę wprost w miejsce stanu liczonego przez rdzeń,
        // więc czas i km/h muszą wyjść z niej tą samą drogą, co z przejazdu liczonego.
        var track = ParseOrFail(File(
            Row(0, 94.0, 0.0, 0.0, 0.0, 0.0, 0.0, "traction"),
            Row(1200, 200.0, 106.0, 20.0, 0.0, 1.0, 0.0, "traction")));

        var state = track.Samples[1].State;
        Assert.AreEqual(1200L, state.Steps);
        Assert.AreEqual(20.0, state.SpeedMps, 1e-12);
        Assert.AreEqual(106.0, state.DistanceM, 1e-12);
        Assert.AreEqual(10.0, state.TimeSeconds(Step), 1e-12, "1200 kroków przy 1/120 s to 10 s");
        Assert.AreEqual(Units.MpsToKmh(20.0), state.SpeedKmh, 1e-12);
        Assert.AreEqual(0.0, state.BrakeRateMps2, 1e-12,
            "telemetria nie niesie opóźnienia hamulca, więc nie wolno go tu zmyślić");
    }

    // --- odmowy -------------------------------------------------------------------

    [TestMethod]
    public void AnEmptyFileIsRefusedInsteadOfBeingAnEmptyRun()
    {
        // Pusty plik przepuszczony jako „zapis bez próbek" dałby przebieg, który
        // kończy się natychmiast i kodem zero — czyli zieloną bramkę nad niczym.
        foreach (var pusty in new[] { string.Empty, "\n", "\n\n" })
        {
            var reason = RefuseAndGetReason(pusty);
            StringAssert.Contains(reason, "pusty");
        }
    }

    [TestMethod]
    public void AFileWithOnlyAHeaderIsRefused()
    {
        var reason = RefuseAndGetReason(DriveTelemetry.Header + "\n");
        StringAssert.Contains(reason, "bez ani jednej próbki");
    }

    [TestMethod]
    public void AForeignHeaderIsRefusedAndShowsTheCoresOne()
    {
        var reason = RefuseAndGetReason("krok,czas,km\n0,0,94\n");

        StringAssert.Contains(reason, "nagłówek");
        StringAssert.Contains(reason, DriveTelemetry.Header,
            "odmowa nie pokazuje, jak nagłówek rdzenia wygląda");
    }

    [TestMethod]
    public void AMissingColumnIsRefusedWithItsRowNumber()
    {
        var text = File(
            Row(0, 94.0, 0.0, 0.0, 0.0, 0.0, 0.0, "traction"),
            "120,1,94.5,0.5,1.25,4.5,1,1,0");

        var reason = RefuseAndGetReason(text);

        StringAssert.Contains(reason, "wiersz 2");
        StringAssert.Contains(reason, "kolumn 9");
    }

    [TestMethod]
    public void StepsThatDoNotGrowAreRefusedBecauseThePlayheadWouldNeverReachThem()
    {
        // Odmowa jest tu treścią, nie higieną formatu: głowica odtwarzania idzie po
        // jednym kroku, więc próbka o numerze nie większym od poprzedniej nie zostałaby
        // przyjęta NIGDY, a przebieg wisiałby do wypalenia limitu czasu w CI.
        foreach (var (drugi, opis) in new[] { (0L, "ten sam krok"), (-0L, "zero"), (0L, "cofnięcie") })
        {
            var text = File(
                Row(120, 94.0, 0.0, 0.0, 0.0, 0.0, 0.0, "traction"),
                Row(drugi, 95.0, 1.0, 0.0, 0.0, 0.0, 0.0, "traction"));

            var reason = RefuseAndGetReason(text);
            StringAssert.Contains(reason, "wiersz 2", opis);
            StringAssert.Contains(reason, "nie jest większy", opis);
        }
    }

    [TestMethod]
    public void ANegativeStepNumberIsRefused()
    {
        var text = File("-1,0,94,0,0,0,0,0,0,traction");

        var reason = RefuseAndGetReason(text);

        StringAssert.Contains(reason, "wiersz 1");
        StringAssert.Contains(reason, "nieujemnym numerem kroku");
    }

    [TestMethod]
    public void InfinityAndNaNAreRefusedEvenThoughTryParseAcceptsThem()
    {
        // Ta sama para, co w `RunPlanTests`, i z tego samego powodu: `TryParse` je
        // przyjmuje, a nieskończony kilometraż ustawia skład w miejscu, którego
        // macierz kamery nie umie policzyć.
        foreach (var zly in new[] { "Infinity", "-Infinity", "NaN" })
        {
            var text = File($"0,0,{zly},0,0,0,0,0,0,traction");

            var reason = RefuseAndGetReason(text);
            StringAssert.Contains(reason, "chainage_m", zly);
            StringAssert.Contains(reason, "skończoną liczbą", zly);
        }
    }

    [TestMethod]
    public void ATimeColumnThatDisagreesWithTheStepCountIsRefused()
    {
        // Czas NIE jest przepisywany z pliku — liczy się z numeru kroku, tak samo jak
        // w rdzeniu. Plik, w którym te dwie liczby się rozjeżdżają, opisuje przejazd
        // z dwoma zegarami; odtworzony wyszedłby z czasem policzonym, a więc innym
        // niż wczytany, i porównanie przy progu 0 padłoby bez powiedzenia dlaczego.
        var text = File(
            Row(0, 94.0, 0.0, 0.0, 0.0, 0.0, 0.0, "traction"),
            "120,7,94.5,0.5,1.25,4.5,1,1,0,traction");

        var reason = RefuseAndGetReason(text);

        StringAssert.Contains(reason, "wiersz 2");
        StringAssert.Contains(reason, "nie składa się z powrotem");
    }

    [TestMethod]
    public void ASpeedInKmhThatDisagreesWithMetresPerSecondIsRefused()
    {
        // Druga kolumna liczona, i ta sama zasada: 1,25 m/s to 4,5 km/h, więc wpisane
        // obok 4,4 znaczy, że jedna z tych liczb została poprawiona ręcznie.
        var text = File("120,1,94.5,0.5,1.25,4.4,1,1,0,traction");

        var reason = RefuseAndGetReason(text);

        StringAssert.Contains(reason, "wiersz 1");
        StringAssert.Contains(reason, "nie składa się z powrotem");
    }

    [TestMethod]
    public void ARoundedRowIsRefusedBecauseRoundingHidesTheDivergenceItWasWrittenToShow()
    {
        // `DriveTelemetry` pisze formatem `R` właśnie po to, żeby wiersz nie ukrył
        // rozjazdu na czwartym miejscu po przecinku. Plik zaokrąglony do trzech miejsc
        // wygląda jak telemetria i nią nie jest — i to jest różnica, którą ta odmowa
        // nazywa, zamiast odtworzyć przejazd zaokrąglony i nazwać go dokładnym.
        var dokladny = Row(120, 94.516622262232141, 0.516622262232141, 1.024662174324133,
            1.0245229235701194, 1.0, 0.0, "traction");
        var zaokraglony = string.Create(
            CultureInfo.InvariantCulture,
            $"120,1,94.517,0.517,1.025,3.689,1.025,1,0,traction");

        Assert.AreNotEqual(dokladny, zaokraglony, "wzorzec kontrolny nie różni się od dokładnego");
        ParseOrFail(File(dokladny));

        var reason = RefuseAndGetReason(File(zaokraglony));
        StringAssert.Contains(reason, "nie składa się z powrotem");
    }

    [TestMethod]
    public void CarriageReturnsFromAWindowsCheckoutDoNotBreakTheFile()
    {
        // Plik przepuszczony przez narzędzie, które zamienia końce wierszy, ma się
        // wczytać — bo różnica jest w bajtach POZA wierszem, a wiersz jest tym, co
        // format opisuje. Odmowa tutaj wyglądałaby jak zepsuta telemetria.
        var lf = File(
            Row(0, 94.0, 0.0, 0.0, 0.0, 0.0, 0.0, "traction"),
            Row(120, 94.5, 0.5, 1.25, 1.0, 1.0, 0.0, "traction"));

        var crlf = lf.Replace("\n", "\r\n", StringComparison.Ordinal);
        Assert.AreNotEqual(lf, crlf, "wzorzec kontrolny nie ma znaków CR");

        var track = ParseOrFail(crlf);
        Assert.AreEqual(2, track.Samples.Count);
        Assert.AreEqual(120L, track.LastStep);
    }

    [TestMethod]
    public void AStepThatIsNotAWholeNumberIsRefused()
    {
        var text = File("0.5,0,94,0,0,0,0,0,0,traction");

        var reason = RefuseAndGetReason(text);

        StringAssert.Contains(reason, "wiersz 1");
        StringAssert.Contains(reason, "numerem kroku");
    }
}
