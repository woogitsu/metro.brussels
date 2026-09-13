using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Game.Input;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Panel wyniku sesji treningowej — to, co gracz widzi po zakończeniu przejazdu,
/// bez zamykania aplikacji (MB-02, punkt 4 odbioru M1).
///
/// <para>Ta klasa istnieje z tego samego powodu, co <see cref="RunResetTests"/>:
/// <c>FirstRun</c> jest węzłem Godota i żaden test jednostkowy go nie wywoła, więc
/// wiedza, którą trzeba przybić testem, musi wyjść z węzła. Tu jest przybita.</para>
/// </summary>
[TestClass]
public sealed class RunSummaryTests
{
    private static TrainingResult Wynik(
        TrainingEnding ending,
        params TrainingTarget[] cele) => new(
            ending, cele, 123.456, 1234.5, 0, 0, 0);

    private static TrainingTarget Obsluzony(string id, string nazwa, double blad) =>
        new(id, nazwa, true, blad, 10.0, 20.0);

    private static TrainingTarget Pominiety(string id, string nazwa) =>
        new(id, nazwa, false, null, null, null);

    [TestMethod]
    public void KAZDA_LICZBA_PANELU_PRZYCHODZI_Z_WYNIKU_A_NIE_JEST_LICZONA_TUTAJ()
    {
        var panel = RunSummary.Compose(Wynik(
            TrainingEnding.AllTargetsServed,
            Obsluzony("8742", "Beekkant", -0.25),
            Obsluzony("8292", "Étangs Noirs", 1.5)));

        StringAssert.Contains(panel, "SESJA ZALICZONA",
            "panel nie mówi, że sesja jest zaliczona");
        StringAssert.Contains(panel, "cele: 2 z 2",
            "panel nie niesie liczby obsłużonych celów");
        StringAssert.Contains(panel, "Beekkant",
            "panel nie wymienia celu z nazwy — gracz nie wie, o którą stację chodzi");
        StringAssert.Contains(panel, "-0.250 m",
            "błąd zatrzymania ZE ZNAKIEM nie wszedł do panelu: `-` znaczy „za blisko”");
        StringAssert.Contains(panel, "+1.500 m",
            "błąd zatrzymania ZE ZNAKIEM nie wszedł do panelu: `+` znaczy „za daleko”");
        StringAssert.Contains(panel, "czas: 123.5 s",
            "czas w panelu nie przyszedł z wyniku");
        StringAssert.Contains(panel, "droga: 1234.5 m",
            "droga w panelu nie przyszła z wyniku");
    }

    [TestMethod]
    public void A_MISSED_TARGET_HAS_NO_STOP_ERROR_AND_THE_PANEL_SAYS_SO()
    {
        // `StopErrorM` jest `double?`, a nie `NaN`, i tutaj widać po co: `NaN` wszedłby
        // w szablon jako słowo „NaN" i wyglądał na zmierzoną wartość. Cel pominięty NIE
        // MA błędu zatrzymania, a nie „ma błąd, którego nie da się porównać".
        var panel = RunSummary.Compose(Wynik(
            TrainingEnding.TargetMissed,
            Pominiety("8742", "Beekkant"),
            Pominiety("8292", "Étangs Noirs")));

        StringAssert.Contains(panel, "SESJA NIEZALICZONA — minięty cel",
            "panel nie mówi, dlaczego sesja nie jest zaliczona");
        StringAssert.Contains(panel, "cele: 0 z 2",
            "panel policzył obsłużony cel, choć skład nie zatrzymał się ani razu");
        StringAssert.Contains(panel, "Beekkant  minięty",
            "panel nie mówi przy CELU, że został minięty");
        Assert.IsFalse(panel.Contains("NaN", StringComparison.Ordinal),
            "w panelu stoi napis `NaN` — pomiar, którego nie ma, wygląda jak pomiar");
        Assert.IsFalse(panel.Contains(" m", StringComparison.Ordinal)
            && panel.Contains("0.000 m", StringComparison.Ordinal),
            "cel pominięty dostał błąd zatrzymania 0,000 m — a to jest wartość idealna");
    }

    [TestMethod]
    public void KLAWISZE_W_PANELU_PRZYCHODZA_Z_TEJ_SAMEJ_TABELI_CO_InputMap()
    {
        // Panel mówiący „naciśnij R" byłby drugą kopią przypisania klawiszy — a to
        // przypisanie już raz się w tym projekcie rozjechało (`play.sh`, MB-01 §10).
        var panel = RunSummary.Compose(Wynik(
            TrainingEnding.AllTargetsServed, Obsluzony("8742", "Beekkant", 0.0)));

        var reset = DriverActions.All.Single(b => b.Action == DriverActions.Reset);
        var quit = DriverActions.All.Single(b => b.Action == DriverActions.Quit);
        StringAssert.Contains(panel, $"[{reset.KeyName}] od nowa",
            "panel obiecuje inny klawisz ponowienia niż ten, który czyta `InputMap`");
        StringAssert.Contains(panel, $"[{quit.KeyName}] wyjście",
            "panel obiecuje inny klawisz wyjścia niż ten, który czyta `InputMap`");
    }

    [TestMethod]
    public void RAMIE_DOMYSLNE_RZUCA_ZAMIAST_POKAZAC_NAZWE_CZLONU()
    {
        // Ta sama decyzja, co w `UiText.Get` i z tego samego powodu (6.D83): panel
        // wyświetlający `AllTargetsServed` wygląda na ekranie jak usterka tekstu
        // i zostaje zgłoszony po dwóch dniach przez kogoś innego.
        //
        // `Running` jest tu najważniejszym przypadkiem, bo jest OSIĄGALNY: to jedyny
        // człon, który może stać w wyniku zbudowanym ręcznie. Sesja go tam nie wstawi
        // — `TrainingSession.Result` jest wtedy `null` — ale konstruktor rekordu nie
        // ma jak tego zabronić.
        var wyjatek = Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => RunSummary.Compose(Wynik(TrainingEnding.Running)),
            "panel złożył się dla `Running` — czyli dla sesji, która nie ma wyniku");
        StringAssert.Contains(wyjatek.Message, "nie ma nagłówka",
            "wyjątek nie mówi, czego brakuje — komunikat bez powodu każe czytać kod");
    }

    [TestMethod]
    public void KAZDY_CZLON_TrainingEnding_POZA_Running_MA_NAGLOWEK()
    {
        // KONTROLA PRZYRZĄDU, bez której test wyżej nie znaczyłby nic: gdyby nagłówka
        // nie miał ŻADEN człon, tamten test przechodziłby tak samo. Nowy człon
        // `TrainingEnding` zapala tę pętlę, a nie wychodzi po cichu na ekran.
        var czlony = Enum.GetValues<TrainingEnding>()
            .Where(e => e != TrainingEnding.Running)
            .ToList();
        Assert.IsTrue(czlony.Count >= 2,
            $"członów `TrainingEnding` poza `Running` jest {czlony.Count} — "
            + "przy jednym ta pętla przestaje cokolwiek porównywać");

        foreach (var czlon in czlony)
        {
            var panel = RunSummary.Compose(Wynik(czlon, Pominiety("8742", "Beekkant")));
            Assert.IsTrue(panel.Length > 0,
                $"człon `{czlon}` nie ma nagłówka w katalogu tekstów");
        }
    }

    [TestMethod]
    public void LICZNIKI_ATP_IDA_DO_PANELU_ROZDZIELONE_NA_TRZY()
    {
        var panel = RunSummary.Compose(new TrainingResult(
            TrainingEnding.AllTargetsServed,
            new List<TrainingTarget> { Obsluzony("8742", "Beekkant", 0.1) },
            60.0, 500.0, 3, 2, 1));

        StringAssert.Contains(panel, "3 ostrzeżeń",
            "licznik ostrzeżeń nie wszedł do panelu");
        StringAssert.Contains(panel, "2 ingerencji",
            "licznik ingerencji nie wszedł do panelu");
        StringAssert.Contains(panel, "1 awaryjnych",
            "licznik ingerencji awaryjnych nie wszedł do panelu — a to on odróżnia "
            + "hamowanie służbowe od awaryjnego");
    }
}
