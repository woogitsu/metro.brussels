using System;
using System.IO;
using MetroBxl.Tests.Shared;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Wpięcie sesji treningowej w scenę — sprawdzane LEKSYKALNIE, bo inaczej nie da się
/// tego sprawdzić wcale (MB-02).
///
/// <para><b>Dlaczego czytanie źródła, a nie wywołanie.</b> <c>FirstRun</c> jest węzłem
/// Godota i żaden test jednostkowy go nie uruchomi — to samo ograniczenie, które
/// wypchnęło z niego <see cref="RunReset"/>, <see cref="RunHeader"/> i
/// <see cref="RunPlan"/>. Trzy rzeczy jednak wypchnąć się nie dają, bo są KOLEJNOŚCIĄ
/// i WARUNKAMI w ciele metody węzła, a nie wiedzą: gdzie w kroku stoi
/// <c>TrainingSession.Observe</c>, że koniec sesji NIE ustawia <c>_done</c>, i że reset
/// idzie przez <see cref="RunReset.Apply"/> razem z sesją. Ta klasa czyta więc źródło
/// — tak samo jak <c>UiTextTests</c> robi to od 6.D83 i z tego samego powodu.</para>
///
/// <para><b>Czego ta klasa NIE udaje.</b> Nie sprawdza, że scena DZIAŁA — sprawdza, że
/// kod mówi to, co ma mówić. Uruchomienie sceny jest w CI (`godot-first-run.yml`)
/// i to ono jest dowodem zachowania; tutaj jest dowód, że dwie rzeczy niewidoczne
/// w telemetrii nie rozjadą się po cichu.</para>
/// </summary>
[TestClass]
public sealed class TrainingWiringTests
{
    [TestMethod]
    public void POMOC_LINII_BEZ_LINE_CORE_NIE_OBIECUJE_PRZEJECIA_SKLADU()
    {
        var source = FirstRunSource();
        var start = source.IndexOf("private string HelpLine()", StringComparison.Ordinal);
        var end = source.IndexOf("private ControlOwner ObservedOwner()", start, StringComparison.Ordinal);
        Assert.IsTrue(start >= 0 && end > start, "nie znaleziono wyboru pomocy HUD");
        var help = source[start..end];
        StringAssert.Contains(help, "if (_lineCore is null)",
            "bez LineCore pomoc musi przejść do opisu starszego trybu linii");
        StringAssert.Contains(help, "return DriverActions.HelpWhenLegacyLineRuns;",
            "starszy tryb linii musi mieć własny prawdziwy opis klawiszy");
    }

    [TestMethod]
    public void AUTOMATYCZNA_LINIA_NIE_ODCZYTUJE_NIEISTNIEJACEGO_LINE_CORE_W_HUD()
    {
        var source = FirstRunSource();
        var start = source.IndexOf("private string StationLine()", StringComparison.Ordinal);
        var end = source.IndexOf("if (_stations is null)", start, StringComparison.Ordinal);
        Assert.IsTrue(start >= 0 && end > start, "nie znaleziono wiersza stacji HUD");
        var stationLine = source[start..end];
        StringAssert.Contains(stationLine, "_lineCore is { Trains.Count: > 0 }",
            "podpowiedź wymaga istniejącego rdzenia linii");
        StringAssert.Contains(stationLine, "ObservedOwner() == ControlOwner.Driver",
            "autopilot nie powinien dostawać podpowiedzi maszynisty");
        StringAssert.Contains(stationLine, ": BrakingCueStage.None;",
            "bez rdzenia i kierowcy podpowiedź musi być pusta");
    }

    private static string FirstRunSource() =>
        KorzenRepozytorium.Tresc("src", "Game", "FirstRun.cs");

    [TestMethod]
    public void KONIEC_INTERAKTYWNEJ_LINII_ZOSTAWIA_KLAWISZE_I_RESET_R()
    {
        var source = FirstRunSource();
        var process = source[source.IndexOf("public override void _Process(", StringComparison.Ordinal)
            ..source.IndexOf("private long AdvanceBy(", StringComparison.Ordinal)];
        var reset = process.IndexOf("if (_lineMode && _readsKeyboard && _resetPending && _replay is null)",
            StringComparison.Ordinal);
        var restart = process.IndexOf("GetTree().ReloadCurrentScene()", StringComparison.Ordinal);
        var idleGuard = process.IndexOf("if (!_lineCompletionReported)", StringComparison.Ordinal);
        var advance = process.IndexOf("AdvanceBy(synthetic", StringComparison.Ordinal);
        Assert.IsTrue(reset >= 0 && restart > reset && advance > restart,
            "R musi odtworzyć linię także po jej zakończeniu, przed kolejnym krokiem");
        Assert.IsTrue(idleGuard > restart && advance > idleGuard,
            "ekran końca linii nie powinien dopisywać pustych kroków do akumulatora");
        StringAssert.Contains(process,
            "else if (_lineMode && !_lineCompletionReported",
            "po końcu linii krok fizyki powinien być pomijany");

        var finish = source[source.IndexOf("private void FinishLineRun()", StringComparison.Ordinal)
            ..source.IndexOf("private void WriteCalls(", StringComparison.Ordinal)];
        StringAssert.Contains(finish,
            "var interactive = _readsKeyboard && _callsPath is null && _replay is null;",
            "tylko prawdziwy gracz utrzymuje ekran końca linii");
        StringAssert.Contains(finish, "_done = !interactive;",
            "headless i replay muszą zamknąć proces po ukończeniu linii");
        var exitGuard = finish.IndexOf("if (!interactive)", StringComparison.Ordinal);
        var exit = finish.IndexOf("GetTree().Quit()", StringComparison.Ordinal);
        Assert.IsTrue(exitGuard >= 0 && exit > exitGuard,
            "przebieg headless/replay ma nadal kończyć proces");
        StringAssert.Contains(finish, "if (_lineCompletionReported)",
            "raport końca linii powinien powstać tylko raz");
    }

    [TestMethod]
    public void WYBOR_SKLADU_ODSWIEZA_HUD_I_KAMERE_BEZ_KROKU_FIZYKI()
    {
        var source = FirstRunSource();
        var start = source.IndexOf("private void ExecuteLineEvent(", StringComparison.Ordinal);
        var end = source.IndexOf("private void HandleTrainKeys(", start, StringComparison.Ordinal);
        Assert.IsTrue(start >= 0 && end > start,
            "nie znaleziono granic obsługi zdarzeń linii w FirstRun");
        var observe = source[start..end];
        var selection = observe.IndexOf("_observed = _lineSession.ObservedIndex;", StringComparison.Ordinal);
        var drive = observe.IndexOf("_line = _lineCore!.Trains[_observed].Drive;", StringComparison.Ordinal);
        var state = observe.IndexOf("_state = _line?.State ?? DriveState.AtRest;", StringComparison.Ordinal);
        var command = observe.IndexOf("_command = _lineSession.Command;", StringComparison.Ordinal);
        Assert.IsTrue(selection >= 0 && drive > selection && state > drive && command > state,
            "N musi przełączyć nazwę stacji, położenie i komendę w tej samej klatce, "
            + "także gdy akumulator nie wykona kroku 120 Hz");
    }

    [TestMethod]
    public void OBSERWACJA_SESJI_STOI_NA_KONCU_KROKU_A_NIE_NA_POCZATKU()
    {
        // Warunek zaliczenia pyta o prędkość PO kroku i o cykl drzwi PO filtrze stacji.
        // Policzony wyżej opisywałby krok POPRZEDNI — czyli kończyłby sesję o jeden krok
        // za wcześnie. Błąd o jeden krok w warunku końca wygląda dokładnie tak samo jak
        // warunek końca, który działa, i nie widać go w żadnej kolumnie telemetrii.
        var kod = FirstRunSource();

        var filtr = kod.IndexOf("_stations?.Filter(", StringComparison.Ordinal);
        var ruch = kod.IndexOf("_state = _controller.Advance(", StringComparison.Ordinal);
        var obserwacja = kod.IndexOf("_training?.Observe(", StringComparison.Ordinal);

        Assert.IsTrue(filtr > 0, "w `FirstRun` nie ma wywołania `_stations?.Filter(`");
        Assert.IsTrue(ruch > 0, "w `FirstRun` nie ma wywołania `_controller.Advance(`");
        Assert.IsTrue(obserwacja > 0,
            "w `FirstRun` nie ma wywołania `_training?.Observe(` — sesja treningowa "
            + "nie jest wpięta w krok i nigdy się nie skończy");

        Assert.IsTrue(obserwacja > filtr,
            "`_training?.Observe` stoi PRZED filtrem stacji — sesja pytałaby o cykl "
            + "drzwi sprzed tego kroku");
        Assert.IsTrue(obserwacja > ruch,
            "`_training?.Observe` stoi PRZED ruchem składu — sesja pytałaby o prędkość "
            + "sprzed tego kroku i kończyłaby się o krok za wcześnie");
    }

    [TestMethod]
    public void KONIEC_SESJI_NIE_USTAWIA_done_BO_TO_ODCIELOBY_R_ESC_I_C()
    {
        // `_done` powoduje `return` w `_Process` PRZED odczytem klawiatury, a
        // `HandleViewKeys` jest JEDYNYM czytnikiem `Reset` (`R`), `Quit` (`Esc`)
        // i `ViewToggle` (`C`). Panel wyniku bez działających klawiszy jest ekranem,
        // z którego nie ma wyjścia — a punkty 4 i 5 odbioru M1 żądają obu.
        var kod = FirstRunSource();

        var gdzie = kod.IndexOf("_training is { Finished: true }", StringComparison.Ordinal);
        Assert.IsTrue(gdzie > 0,
            "w `FirstRun._Process` nie ma gałęzi zatrzymującej ticki po końcu sesji");

        var odczyt = kod.IndexOf("_keys = _input.Read();", StringComparison.Ordinal);
        Assert.IsTrue(gdzie > odczyt,
            "gałąź końca sesji stoi PRZED odczytem klawiatury — `R`, `Esc` i `C` "
            + "przestają działać dokładnie wtedy, kiedy są potrzebne");

        var galaz = kod.Substring(gdzie, Math.Min(400, kod.Length - gdzie));
        Assert.IsFalse(galaz.Contains("_done = true", StringComparison.Ordinal),
            "koniec SESJI ustawia `_done`, czyli koniec PROCESU — to są dwie różne "
            + "rzeczy i pomylenie ich odcina klawisze panelu wyniku");
        StringAssert.Contains(galaz, "!_resetPending",
            "gałąź końca sesji nie przepuszcza klatki z zamówionym resetem — `R` "
            + "ustawiałoby zamówienie, którego nikt by nie odebrał");
    }

    [TestMethod]
    public void RESET_SCENY_PRZEKAZUJE_SESJE_DO_RunReset()
    {
        // Jedna lista „co obejmuje reset" dla obu stron bramki scena–rdzeń. Gdyby scena
        // zerowała sesję u siebie, `Sim.Runner replay` odtwarzałby ten sam zapis wejść
        // z wynikiem z poprzedniego przejazdu.
        var kod = FirstRunSource();
        var wywolanie = kod.IndexOf("RunReset.Apply(", StringComparison.Ordinal);
        Assert.IsTrue(wywolanie > 0, "w `FirstRun` nie ma wywołania `RunReset.Apply(`");

        var fragment = kod.Substring(wywolanie, Math.Min(300, kod.Length - wywolanie));
        StringAssert.Contains(fragment, "_training",
            "`RunReset.Apply` nie dostaje sesji — reset zostawiłby wynik poprzedniego "
            + "przejazdu, a „ponów” dawałoby ekran, który już tam był");
    }

    [TestMethod]
    public void CELE_SESJI_WYCHODZA_Z_OSI_A_NIE_STOJA_W_KODZIE()
    {
        // `docs/PLAYABILITY.md` §3: „cele wyszukiwane po identyfikatorach z osi;
        // kilometraży nie kopiuje się do logiki". Wpisane `8742` i `8292` byłyby drugą
        // kopią danych z `data/track/L1_A.json` i milczałyby po zmianie osi.
        var kod = FirstRunSource();

        StringAssert.Contains(kod, "_axis.Stations[i].StopId",
            "cele sesji nie są czytane z osi");
        Assert.IsFalse(kod.Contains("\"8742\"", StringComparison.Ordinal),
            "identyfikator przystanku Beekkant stoi WPISANY w `FirstRun` — to druga "
            + "kopia danych z `data/track/`");
        Assert.IsFalse(kod.Contains("\"8292\"", StringComparison.Ordinal),
            "identyfikator przystanku Étangs Noirs stoi WPISANY w `FirstRun`");

        // Pętla zaczyna od indeksu 1: stacja zerowa jest punktem startowym i
        // `StationService` ją pomija, więc cel z niej nie trafiłby ani do wywołań,
        // ani do miniętych.
        StringAssert.Contains(kod, "for (var i = 1;",
            "pętla celów nie pomija punktu startowego osi — taki cel zawiesiłby sesję");
    }

    [TestMethod]
    public void SESJA_MA_TYLE_CELOW_ILE_MOWI_DECYZJA_PROJEKTOWA()
    {
        // Kontrola przyrządu: liczba stoi w JEDNYM miejscu i jest nią stała
        // z `DesignAssumptions`, a nie literał w pętli.
        Assert.AreEqual(2, DesignAssumptions.TrainingTargets,
            "liczba celów M1 zmieniła się bez zmiany kontraktu w `docs/PLAYABILITY.md`");
        StringAssert.Contains(FirstRunSource(), "DesignAssumptions.TrainingTargets",
            "`FirstRun` nie bierze liczby celów ze stałej — liczba stoi w dwóch miejscach");
    }
}
