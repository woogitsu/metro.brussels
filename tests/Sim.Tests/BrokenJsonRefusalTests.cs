using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Plik o ZEPSUTEJ SKŁADNI ma kończyć się odmową, a nie stosem wywołań (6.D229).
///
/// <para><b>Czego te testy pilnują.</b> Nie tego, że loader „coś rzuca" — tego, że
/// rzuca typ, który filtry <c>catch</c> tego repozytorium <b>wymieniają z nazwy</b>:
/// wspólny handler <c>Sim.Runner.Program.Main</c> (<c>IOException</c>,
/// <c>ArgumentException</c>, <c>FormatException</c>, <c>InvalidOperationException</c>)
/// i filtry <c>FirstRun.ReadSignallingPlan</c>/<c>ReadInputLog</c>
/// (<c>ArgumentException</c>, <c>FormatException</c>). Przed 6.D229
/// <c>JsonDocument.Parse</c> rzucał <c>JsonReaderException</c>, którego nie wymienia
/// ŻADEN z nich — i `--signalling` na pliku z `{{{` kończyło się kodem 134,
/// angielskim komunikatem .NET-a i stosem, zamiast wierszem odmowy.</para>
///
/// <para><b>Dlaczego filtry stoją w teście jako kopia, a nie jako odwołanie.</b>
/// Filtr jest wyrażeniem <c>when</c> w kodzie, którego nie da się z niego odczytać.
/// Kopia listy typów zestarzeje się, gdy ktoś filtr rozszerzy — ale zestarzeje się
/// w stronę BEZPIECZNĄ: test dalej wymaga typu, który stary filtr łapał.</para>
/// </summary>
[TestClass]
public sealed class BrokenJsonRefusalTests
{
    /// <summary>Filtr wspólnego handlera z <c>src/Sim.Runner/Program.cs:247</c>.</summary>
    private static bool ZlapieHandlerRunnera(Exception error)
        => error is IOException or ArgumentException or FormatException or InvalidOperationException;

    /// <summary>Filtr z <c>src/Game/FirstRun.cs:1034</c> i <c>:1061</c>.</summary>
    private static bool ZlapieFiltrFirstRun(Exception error)
        => error is ArgumentException or FormatException;

    /// <summary>Kształty, na których 6.D229 zmierzyło szczelinę.</summary>
    private static IEnumerable<(string Nazwa, string Json)> ZepsutaSkladnia()
    {
        yield return ("{{{", "{{{");
        yield return ("napis pusty", "");
    }

    private static IEnumerable<(string Nazwa, Action<string> Wywolaj)> Loadery()
    {
        yield return ("SignallingPlan.FromJson", json => SignallingPlan.FromJson(json));
        yield return ("TrackAxis.FromJson", json => TrackAxis.FromJson(json));
        yield return ("ServiceDay.FromJson", json => ServiceDay.FromJson(json));
        yield return ("CbtcTestArea.FromJson", json => CbtcTestArea.FromJson(json));
        yield return ("JsonText.Parse", json => JsonText.Parse(json, "plik").Dispose());
    }

    [TestMethod]
    public void Zepsuta_skladnia_konczy_sie_typem_ktory_filtry_lapia()
    {
        var sprawdzonych = 0;
        foreach (var (loader, wywolaj) in Loadery())
        {
            foreach (var (ksztalt, json) in ZepsutaSkladnia())
            {
                var error = Assert.ThrowsException<FormatException>(
                    () => wywolaj(json),
                    $"{loader} na `{ksztalt}`: oczekiwano FormatException");

                Assert.IsTrue(ZlapieHandlerRunnera(error),
                    $"{loader} na `{ksztalt}`: {error.GetType().Name} omija handler Sim.Runner");
                Assert.IsTrue(ZlapieFiltrFirstRun(error),
                    $"{loader} na `{ksztalt}`: {error.GetType().Name} omija filtr FirstRun");
                sprawdzonych++;
            }
        }

        Assert.AreEqual(10, sprawdzonych,
            "test nie przeszedł po wszystkich parach loader × kształt");
    }

    [TestMethod]
    public void Odmowa_jest_po_polsku_i_nazywa_plik()
    {
        var error = Assert.ThrowsException<FormatException>(
            () => SignallingPlan.FromJson("{{{"),
            "plan o zepsutej składni ma kończyć się FormatException");

        StringAssert.Contains(error.Message, "nie jest poprawnym JSON-em",
            "odmowa nie mówi po polsku, czego dotyczy");
        StringAssert.Contains(error.Message, "plan sygnalizacji",
            "odmowa nie nazywa czytanego pliku");

        // Powód parsera zostaje DOŁĄCZONY, a nie wyrzucony: bez niego nie widać,
        // w którym miejscu pliku składnia się rozjechała.
        Assert.IsInstanceOfType(error.InnerException, typeof(JsonException),
            "powód parsera ma zostać jako InnerException");
    }

    [TestMethod]
    public void Poprawny_plik_przechodzi_nietkniety()
    {
        // Kontrola dodatnia w samym teście: owinięcie ma odmawiać TYLKO zepsutej
        // składni. Plan pakietu A ma się wczytać tak samo jak przed 6.D229.
        var plan = SignallingPlanTests.PackageAPlan();
        Assert.IsTrue(plan.Blocks.Count > 0, "poprawny plan wczytał się pusty");
    }
}
