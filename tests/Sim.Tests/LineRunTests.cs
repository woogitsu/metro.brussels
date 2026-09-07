using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Przejazd linii z zatrzymaniem na każdej stacji.
///
/// Testy pilnują **własności pętli**, a nie liczb dla pakietu A: liczby zależą od
/// założeń bez źródła (ograniczenie prędkości, czas wymiany pasażerów), więc
/// przypięcie ich tutaj przypięłoby założenia, a nie model. Liczby dla prawdziwej
/// osi wychodzą z <c>src/Sim.Runner line</c> i są w <c>reports/T-401-line-run.md</c>.
/// </summary>
[TestClass]
public sealed class LineRunTests
{
    private static readonly LineRun Run = LineRun.M7;

    private static RunConditions Level() => RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0);

    private static LineRunSettings Settings(
        double limitKmh = 60.0, double exchange = 10.0,
        double usage = 1.0, double window = 5.0, double? coast = null) =>
        new(Units.KmhToMps(limitKmh), exchange, usage, window, coast);

    /// <summary>Prosta oś o zadanych kilometrażach stacji.</summary>
    private static TrackAxis Axis(params double[] stationChainages)
    {
        var length = stationChainages[^1] + 100.0;
        var stations = string.Join(",", stationChainages.Select((c, i) => string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"name":"S{{i}}","chainage_m":{{c.ToString("R", CultureInfo.InvariantCulture)}},"stop_id":"P{{i}}"}""")));
        return TrackAxis.FromJson(string.Create(
            CultureInfo.InvariantCulture,
            $$"""
            {"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},
             "points":[[0.0,0.0,0.0],[{{length.ToString("R", CultureInfo.InvariantCulture)}},0.0,0.0]],
             "stations":[{{stations}}]}
            """), 0.0);
    }

    // --- zatrzymania ---------------------------------------------------------

    [TestMethod]
    public void Zatrzymuje_sie_na_kazdej_stacji_poza_poczatkowa()
    {
        var result = Run.Run(Axis(0.0, 600.0, 1400.0, 2000.0), Level(), Settings());

        Assert.AreEqual("arrived", result.FinishReason);
        Assert.AreEqual(3, result.Calls.Count, "stacja startowa nie jest zatrzymaniem — skład już na niej stoi");
        CollectionAssert.AreEqual(
            new[] { "S1", "S2", "S3" }, result.Calls.Select(c => c.Name).ToArray());
    }

    [TestMethod]
    public void Staje_na_peronie_a_nie_gdziekolwiek_w_oknie()
    {
        var result = Run.Run(Axis(0.0, 900.0, 1800.0), Level(), Settings(window: 5.0));

        foreach (var call in result.Calls)
        {
            Assert.IsTrue(
                Math.Abs(call.StopErrorM) < 0.5,
                $"{call.Name}: błąd zatrzymania {call.StopErrorM:F3} m — okno stacji to nie jest dokładność zatrzymania");
        }
    }

    [TestMethod]
    public void Blad_zatrzymania_nie_kumuluje_sie_wzdluz_linii()
    {
        var result = Run.Run(Axis(0.0, 700.0, 1400.0, 2100.0, 2800.0), Level(), Settings());
        var first = Math.Abs(result.Calls[0].StopErrorM);
        var last = Math.Abs(result.Calls[^1].StopErrorM);

        Assert.IsTrue(last < first + 0.1, $"pierwszy {first:F3} m, ostatni {last:F3} m");
    }

    // --- postój --------------------------------------------------------------

    [TestMethod]
    public void Postoj_trwa_pelny_cykl_drzwi()
    {
        var settings = Settings(exchange: 12.0);
        var result = Run.Run(Axis(0.0, 800.0, 1600.0), Level(), settings);
        var expected = DoorCycle.MinimumDwellSeconds + 12.0;

        foreach (var call in result.Calls)
        {
            if (!double.IsFinite(call.DepartureSeconds))
            {
                continue;
            }

            Assert.AreEqual(expected, call.DepartureSeconds - call.ArrivalSeconds, 2.0 / FixedStep.SimulationHertz);
        }
    }

    [TestMethod]
    public void Dluzsza_wymiana_pasazerow_wydluza_przejazd_o_dokladnie_tyle_ile_postojow()
    {
        var axis = Axis(0.0, 800.0, 1600.0, 2400.0);
        var quick = Run.Run(axis, Level(), Settings(exchange: 5.0));
        var slow = Run.Run(axis, Level(), Settings(exchange: 15.0));

        // Dwa postoje pośrednie po 10 s różnicy; ostatnia stacja to przyjazd, jej postój
        // nie wchodzi do czasu przejazdu.
        Assert.AreEqual(20.0, slow.TotalSeconds - quick.TotalSeconds, 0.05);
    }

    [TestMethod]
    public void Skladu_nie_da_sie_ruszyc_przy_otwartych_drzwiach()
    {
        var moved = 0;
        var open = 0;
        Run.Run(Axis(0.0, 700.0, 1400.0), Level(), Settings(), LineRun.DefaultStepBudget, point =>
        {
            if (point.Phase == DoorPhase.Closed)
            {
                return;
            }

            open++;
            if (point.Command.Throttle > 0.0 || point.SpeedMps > 0.0)
            {
                moved++;
            }
        });

        Assert.IsTrue(open > 0, "ślad nie zarejestrował ani jednego kroku z otwartym cyklem drzwi");
        Assert.AreEqual(0, moved, "trakcja albo ruch przy niezamkniętym cyklu drzwi");
    }

    // --- jazda ---------------------------------------------------------------

    [TestMethod]
    public void Wyzszy_limit_predkosci_skraca_czas_przejazdu()
    {
        var axis = Axis(0.0, 1200.0, 2400.0);
        var slow = Run.Run(axis, Level(), Settings(limitKmh: 45.0));
        var fast = Run.Run(axis, Level(), Settings(limitKmh: 70.0));

        Assert.IsTrue(fast.TotalSeconds < slow.TotalSeconds,
            $"70 km/h: {fast.TotalSeconds:F2} s, 45 km/h: {slow.TotalSeconds:F2} s");
    }

    [TestMethod]
    public void Nie_przekracza_zadanego_limitu_predkosci()
    {
        var limit = Units.KmhToMps(55.0);
        var worst = 0.0;
        Run.Run(Axis(0.0, 2500.0, 5000.0), Level(), Settings(limitKmh: 55.0),
            LineRun.DefaultStepBudget, point => worst = Math.Max(worst, point.SpeedMps));

        Assert.IsTrue(worst <= limit + 1e-9, $"{Units.MpsToKmh(worst):F3} km/h przy limicie 55");
    }

    [TestMethod]
    public void Wczesniejsze_hamowanie_wydluza_czas_jazdy()
    {
        var axis = Axis(0.0, 1500.0);
        var late = Run.Run(axis, Level(), Settings(usage: 1.0));
        var early = Run.Run(axis, Level(), Settings(usage: 0.6));

        Assert.IsTrue(early.TotalSeconds > late.TotalSeconds,
            $"usage 0,6: {early.TotalSeconds:F2} s, usage 1,0: {late.TotalSeconds:F2} s");
    }

    [TestMethod]
    public void Ciezszy_sklad_jedzie_dluzej_na_tej_samej_osi()
    {
        var axis = Axis(0.0, 1200.0, 2400.0);
        var empty = Run.Run(axis, RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0), Settings());
        var loaded = Run.Run(axis, RunConditions.Level(VehicleModel.M7, TrainLoad.Aw2), Settings());

        Assert.IsTrue(loaded.TotalSeconds > empty.TotalSeconds,
            $"AW2: {loaded.TotalSeconds:F2} s, AW0: {empty.TotalSeconds:F2} s");
    }

    [TestMethod]
    public void Raz_zaczete_hamowanie_nie_wraca_do_trakcji()
    {
        // Ta regresja ma nazwę i liczbę: pierwsza wersja pętli sprawdzała próg hamowania
        // TAKŻE w trakcie hamowania, więc przy chwilowym spadku wymaganego opóźnienia
        // wracała do nastawnika. W śladzie było to 3,12 s pełzania na 1,08 m przed Merode.
        //
        // Zerowe polecenie hamulca samo w sobie regresją NIE jest: gdy opory ruchu
        // wystarczają, prawidłową odpowiedzią serwa jest odpuszczenie hamulca. Regresją
        // jest dopiero powrót nastawnika.
        var tractionAfterBraking = 0;
        var braking = false;
        Run.Run(Axis(0.0, 1500.0), Level(), Settings(), LineRun.DefaultStepBudget, point =>
        {
            if (point.Phase != DoorPhase.Closed)
            {
                return;
            }

            if (point.Command.Brake > 0.0)
            {
                braking = true;
            }
            else if (braking && point.Command.Throttle > 0.0 && point.SpeedMps > 0.0)
            {
                tractionAfterBraking++;
            }
        });

        Assert.IsTrue(braking, "ślad nie zarejestrował ani jednego kroku hamowania");
        Assert.AreEqual(0, tractionAfterBraking, "nastawnik wrócił po rozpoczęciu hamowania");
    }

    // --- determinizm i granice ----------------------------------------------

    [TestMethod]
    public void Ten_sam_przejazd_dwa_razy_daje_te_same_liczby_co_do_bitu()
    {
        var axis = Axis(0.0, 900.0, 1900.0);
        var first = Run.Run(axis, Level(), Settings());
        var second = Run.Run(axis, Level(), Settings());

        Assert.AreEqual(first.Steps, second.Steps);
        Assert.AreEqual(first.TotalSeconds, second.TotalSeconds, 0.0);
        for (var i = 0; i < first.Calls.Count; i++)
        {
            Assert.AreEqual(first.Calls[i].StoppedAtChainageM, second.Calls[i].StoppedAtChainageM, 0.0);
            Assert.AreEqual(first.Calls[i].ArrivalSeconds, second.Calls[i].ArrivalSeconds, 0.0);
        }
    }

    [TestMethod]
    public void Os_bez_dwoch_stacji_jest_odrzucana_a_nie_przejezdzana()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Run.Run(Axis(0.0), Level(), Settings()));
    }

    [TestMethod]
    public void Budzet_krokow_konczy_przejazd_zamiast_petli_bez_konca()
    {
        var result = Run.Run(Axis(0.0, 3000.0, 6000.0), Level(), Settings(), 1200);

        Assert.AreEqual("step-budget", result.FinishReason);
        Assert.AreEqual(1200, result.Steps);
    }

    // --- założenia -----------------------------------------------------------

    [TestMethod]
    public void Kazde_zalozenie_przejazdu_ma_powod()
    {
        var settings = Settings();

        Assert.AreEqual(4, settings.Assumptions.Count);
        foreach (var assumption in settings.Assumptions)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Reason), assumption.Name);
            Assert.IsTrue(double.IsFinite(assumption.Value), assumption.Name);
        }
    }

    [TestMethod]
    public void Ustawienia_odrzucaja_liczby_bez_sensu()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(limitKmh: 0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(usage: 1.5));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(window: -1.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(exchange: -0.1));
    }

    [TestMethod]
    public void Zerowa_wymiana_pasazerow_jest_dozwolona_i_nie_znosi_cyklu_drzwi()
    {
        var result = Run.Run(Axis(0.0, 800.0, 1600.0), Level(), Settings(exchange: 0.0));
        var call = result.Calls[0];

        Assert.AreEqual(
            DoorCycle.MinimumDwellSeconds, call.DepartureSeconds - call.ArrivalSeconds,
            2.0 / FixedStep.SimulationHertz);
    }

    // --- złączenie z rozkładem ----------------------------------------------

    [TestMethod]
    public void Zatrzymanie_niesie_identyfikator_peronu_do_zestawienia_z_rozkladem()
    {
        var result = Run.Run(Axis(0.0, 800.0, 1600.0), Level(), Settings());

        CollectionAssert.AreEqual(
            new[] { "P1", "P2" }, result.Calls.Select(c => c.StopId).ToArray());
    }

    [TestMethod]
    public void Os_bez_stop_id_nie_wymysla_identyfikatora()
    {
        var axis = TrackAxis.FromJson(
            """
            {"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},
             "points":[[0.0,0.0,0.0],[1700.0,0.0,0.0]],
             "stations":[{"name":"A","chainage_m":0.0},{"name":"B","chainage_m":1600.0}]}
            """, 0.0);
        var result = Run.Run(axis, Level(), Settings());

        Assert.AreEqual(string.Empty, result.Calls[0].StopId);
    }

    // --- wybieg (6.A6) -------------------------------------------------------

    /// <summary>
    /// Ślad co krok, w postaci porównywalnej **co do bitu**. Tego samego kształtu używa
    /// <c>--trace</c> w <c>Sim.Runner</c>, więc test porównuje to samo, co bramka CI.
    /// </summary>
    private static string[] Trace(LineRunSettings settings, TrackAxis axis)
    {
        var rows = new List<string>();
        Run.Run(axis, Level(), settings, LineRun.DefaultStepBudget, point => rows.Add(string.Create(
            CultureInfo.InvariantCulture,
            $"{point.TimeSeconds:R},{point.ChainageM:R},{point.SpeedMps:R}," +
            $"{point.BrakeRateMps2:R},{point.Command.Throttle:R},{point.Command.Brake:R}")));
        return rows.ToArray();
    }

    [TestMethod]
    public void Bez_wybiegu_ustawienia_nie_wymyslaja_metra_od_ktorego_zdjac_trakcje()
    {
        Assert.IsNull(Settings().CoastFromM);
        Assert.AreEqual(4, Settings().Assumptions.Count,
            "przejazd bez wybiegu nie ma o czym założyć — wpis „CoastFromM = 0” mówiłby " +
            "coś wprost przeciwnego do stanu faktycznego");
        Assert.AreEqual(5, Settings(coast: 250.0).Assumptions.Count);
        Assert.AreEqual(
            250.0,
            Settings(coast: 250.0).Assumptions.Single(a => a.Name == "CoastFromM").Value);
    }

    [TestMethod]
    public void Ustawienia_odrzucaja_wybieg_bez_sensu()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(coast: -1.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(coast: double.NaN));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Settings(coast: double.PositiveInfinity));
    }

    /// <summary>
    /// Próg dalszy niż cały odcinek nie ma gdzie zadziałać — i przejazd musi być wtedy
    /// identyczny **co do bitu**, a nie „prawie taki sam”. To jest kontrola, że wybieg
    /// wchodzi wyłącznie w gałąź „nie hamuję jeszcze”, a nie zmienia czegokolwiek po drodze.
    /// </summary>
    [TestMethod]
    public void Wybieg_dalszy_niz_odcinek_nie_zmienia_ani_jednego_kroku()
    {
        var axis = Axis(0.0, 800.0, 1600.0);

        CollectionAssert.AreEqual(Trace(Settings(), axis), Trace(Settings(coast: 5000.0), axis));
    }

    [TestMethod]
    public void Wybieg_wydluza_jazde_i_zmniejsza_prace_trakcji()
    {
        var axis = Axis(0.0, 1500.0, 3000.0);
        var bez = Run.Run(axis, Level(), Settings());
        var zWybiegiem = Run.Run(axis, Level(), Settings(coast: 300.0));

        Assert.AreEqual("arrived", zWybiegiem.FinishReason);
        Assert.AreEqual(bez.Calls.Count, zWybiegiem.Calls.Count);
        Assert.IsTrue(zWybiegiem.TotalSeconds > bez.TotalSeconds,
            $"wybieg ma KOSZTOWAĆ czas: bez {bez.TotalSeconds:F3} s, z wybiegiem {zWybiegiem.TotalSeconds:F3} s");
        Assert.IsTrue(zWybiegiem.Energy.TractionWorkJ < bez.Energy.TractionWorkJ,
            $"wybieg ma OSZCZĘDZAĆ trakcję: bez {bez.Energy.TractionWorkJ:E6} J, "
            + $"z wybiegiem {zWybiegiem.Energy.TractionWorkJ:E6} J");

        for (var index = 0; index < bez.Calls.Count; index++)
        {
            Assert.IsTrue(
                zWybiegiem.Calls[index].TractionWorkFromPreviousJ
                    < bez.Calls[index].TractionWorkFromPreviousJ,
                $"odcinek {index}: praca trakcji nie spadła");
            Assert.IsTrue(
                zWybiegiem.Calls[index].RunSecondsFromPrevious
                    > bez.Calls[index].RunSecondsFromPrevious,
                $"odcinek {index}: czas jazdy nie urósł");
        }
    }

    /// <summary>
    /// Wybieg zdejmuje TRAKCJĘ, a nie dokłada hamulca. Bez tej kontroli „oszczędność
    /// energii” dałoby się osiągnąć hamowaniem, czyli zmianą krzywej hamowania —
    /// wprost poza zakresem 6.A6.
    /// </summary>
    [TestMethod]
    public void Wybieg_zdejmuje_nastawnik_i_nie_dotyka_hamulca()
    {
        var rows = Trace(Settings(coast: 300.0), Axis(0.0, 1500.0));
        var wybieg = 0;
        // Próg pyta o kilometraż PRZED krokiem, a ślad zapisuje ten PO nim, więc
        // wierszem rozstrzygającym jest poprzedni. Bez tego przesunięcia test wywracałby
        // się na jednym kroku — tym, który zaczął się przed 300 m, a skończył za nim.
        for (var index = 1; index < rows.Length; index++)
        {
            var poprzedni = double.Parse(
                rows[index - 1].Split(',')[1], CultureInfo.InvariantCulture);
            var pola = rows[index].Split(',');
            var predkosc = double.Parse(pola[2], CultureInfo.InvariantCulture);
            var nastawnik = double.Parse(pola[4], CultureInfo.InvariantCulture);
            var hamulec = double.Parse(pola[5], CultureInfo.InvariantCulture);
            if (poprzedni < 300.0 || predkosc <= 0.0 || hamulec > 0.0)
            {
                continue;
            }

            Assert.AreEqual(0.0, nastawnik, $"za {poprzedni:F2} m nastawnik nadal ciągnie");
            wybieg++;
        }

        Assert.IsTrue(wybieg > 100, $"kroków wybiegu tylko {wybieg} — próg nie zadziałał");
    }

    /// <summary>
    /// Praca trakcji rozłożona na odcinki musi domykać się do pracy CAŁEGO przejazdu.
    /// Bez tej równości liczba w kolumnie „ubytek pracy trakcji” byłaby drugim,
    /// niezależnym rachunkiem, który wolno rozjechać się z pierwszym.
    /// </summary>
    [TestMethod]
    public void Praca_trakcji_odcinkow_domyka_sie_do_pracy_przejazdu()
    {
        foreach (var coast in new double?[] { null, 300.0 })
        {
            var result = Run.Run(Axis(0.0, 1500.0, 3000.0, 4200.0), Level(), Settings(coast: coast));
            var suma = result.Calls.Sum(c => c.TractionWorkFromPreviousJ ?? double.NaN);

            Assert.AreEqual(
                result.Energy.TractionWorkJ, suma, Math.Abs(result.Energy.TractionWorkJ) * 1e-12,
                $"wybieg {coast}: suma odcinków nie domyka się do przejazdu");
        }
    }

    /// <summary>
    /// Odcinek, na którym hamowanie zaczyna się PRZED zadanym metrem, ma jechać się
    /// bit w bit tak samo jak bez wybiegu — także wtedy, gdy na tej samej osi inne
    /// odcinki wybiegiem jadą. Inaczej „per odcinek” byłoby napisem, a nie własnością.
    /// </summary>
    [TestMethod]
    public void Odcinek_krotszy_niz_prog_jedzie_sie_tak_samo_jak_bez_wybiegu()
    {
        var axis = Axis(0.0, 320.0, 1820.0);
        var bez = Run.Run(axis, Level(), Settings());
        var zWybiegiem = Run.Run(axis, Level(), Settings(coast: 300.0));

        Assert.AreEqual(bez.Calls[0], zWybiegiem.Calls[0],
            "pierwszy odcinek jest krótszy niż droga hamowania — wybieg nie ma tam czego zmienić");
        Assert.AreNotEqual(bez.Calls[1], zWybiegiem.Calls[1],
            "drugi odcinek jest długi — gdyby i on się nie zmienił, próg nigdy by nie zadziałał");
    }
    // --- człon obcięcia (6.A17) -----------------------------------------------

    /// <summary>
    /// 6.A17. Człon obcięcia rośnie, gdy limit prędkości maleje — i to nie jest
    /// przypadek, tylko wprost mechanizm z <c>LineDrive.AccumulateEnergy</c>.
    ///
    /// <para><b>Skąd ta zależność.</b> Obcięcie to <c>(F_netto − m·Δv/Δt)·s</c>, czyli
    /// praca siły, której całkujący krok nie zamienił na energię kinetyczną, bo ściął
    /// prędkość do limitu. Prędkość przejścia siła→moc to <b>31,24 km/h</b>
    /// (2160 kW / 248,9 kN), więc na każdym limicie z tego zakresu skład wisi na
    /// limicie w obszarze STAŁEJ MOCY: trakcja daje <c>P/v</c>, a nadwyżka nad opory
    /// jest w całości odrzucana. Niższy limit znaczy więc dwie rzeczy naraz —
    /// dłuższy czas na limicie i WIĘKSZĄ siłę <c>P/v</c> w tym czasie.</para>
    ///
    /// <para><b>Zmierzone 07.09.2026 na osi L1_A</b> (`reports/czlon-obciecia.md`):
    /// 40 km/h → 506,3 MJ, 50 → 338,6 MJ, 60 → 210,2 MJ, 72 → 96,9 MJ, czyli
    /// monotonicznie. Ten test bierze oś SYNTETYCZNĄ, żeby nie zależeć od pliku
    /// z <c>data/</c> ani nie kosztować przejazdu całej linii; kierunek jest ten sam,
    /// bo wynika z równania, nie z konkretnej osi.</para>
    /// </summary>
    [TestMethod]
    public void Czlon_obciecia_rosnie_gdy_limit_predkosci_maleje()
    {
        var axis = Axis(0.0, 1500.0, 3000.0);
        double Obciecie(double limitKmh) =>
            Run.Run(axis, Level(), Settings(limitKmh: limitKmh), LineRun.DefaultStepBudget)
                .Energy.ClampedWorkJ;

        var wysoki = Obciecie(72.0);
        var sredni = Obciecie(60.0);
        var niski = Obciecie(45.0);

        Assert.IsTrue(niski > sredni, $"45 km/h: {niski:F0} J, 60 km/h: {sredni:F0} J");
        Assert.IsTrue(sredni > wysoki, $"60 km/h: {sredni:F0} J, 72 km/h: {wysoki:F0} J");
    }

    /// <summary>
    /// Druga strona tej samej pary, bez której pierwsza niczego nie przybija: obcięcie
    /// jest <b>dodatnie</b>, a nie „rośnie" z zera do zera.
    ///
    /// <para>Bez tej asercji test wyżej przechodziłby także wtedy, gdyby wszystkie trzy
    /// przejazdy dały obcięcie równe zeru — bo <c>0 &gt; 0</c> jest fałszem, ale
    /// wystarczyłby jeden krok, w którym obcięcie stałoby się ujemne, żeby porządek
    /// zaszedł bez żadnego obcięcia. 6.A6 zmierzyła ten człon jako <b>19 %</b> pracy
    /// trakcji przy 72 km/h; jest wielkością, nie resztą zamknięcia (reszta domyka
    /// się względnie do 2,1E-15).</para>
    /// </summary>
    [TestMethod]
    public void Czlon_obciecia_jest_dodatni_a_nie_resztka_zamkniecia()
    {
        var przejazd = Run.Run(
            Axis(0.0, 1500.0, 3000.0), Level(), Settings(limitKmh: 60.0), LineRun.DefaultStepBudget);

        Assert.IsTrue(przejazd.Energy.ClampedWorkJ > 0.0, $"{przejazd.Energy.ClampedWorkJ:F1} J");
        Assert.IsTrue(
            przejazd.Energy.ClampedWorkJ > przejazd.Energy.DiscretizationWorkJ,
            $"obcięcie {przejazd.Energy.ClampedWorkJ:F1} J nie jest większe od członu " +
            $"dyskretyzacji {przejazd.Energy.DiscretizationWorkJ:F1} J — a to on, nie obcięcie, " +
            "jest członem rzędu błędu kroku");
        Assert.AreEqual(
            0.0, przejazd.Energy.RelativeResidual, 1e-9,
            "bilans przestał się domykać, więc obcięcie nie znaczy już tego, co mówi jego nazwa");
    }

}
