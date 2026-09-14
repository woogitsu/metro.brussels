using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Wiersz o blokadzie trakcji mówi to samo, co ROBI rdzeń — MB-03.
///
/// <para><b>Ta klasa nie sprawdza napisu wobec napisu.</b> Gdyby sprawdzała, byłaby
/// porównaniem katalogu z samym sobą — a pytanie pozycji MB-03 brzmi inaczej:
/// czy HUD nazywa blokadę WTEDY i TYLKO WTEDY, gdy filtry rdzenia naprawdę
/// obcinają nastawnik. Dlatego bramka URUCHAMIA oba filtry
/// (<see cref="StationStop.Filter"/> i <see cref="ProtectionDecision.Apply"/>)
/// i porównuje ich wynik z odpowiedzią <see cref="TractionBlock.Blocked"/>.</para>
///
/// <para>Obie strony mieszkają w <c>src/Sim/</c>, więc bramka chodzi bez Godota —
/// ta sama zasada, co przy <c>SignallingHudTests</c>.</para>
/// </summary>
[TestClass]
public sealed class TractionBlockTests
{
    private static readonly FixedStep Step = FixedStep.Simulation;

    /// <summary>Decyzja ochrony o zadanej reakcji; reszta pól bez znaczenia dla wiersza.</summary>
    private static ProtectionDecision Decyzja(ProtectionAction action) =>
        new(20.0, 300.0, action, action == ProtectionAction.None ? 0.0 : 1.1, true, "test");

    /// <summary>
    /// Faza drzwi po zadanej liczbie kroków postoju — z cyklu rdzenia, nie z tabeli
    /// przepisanej do testu.
    /// </summary>
    private static (DoorPhase Phase, bool Allowed, DriverCommand Effective) Postoj(int kroki)
    {
        var stop = new StationStop(new DoorCycle(20.0), Step);
        var state = DriveState.AtRest;
        var effective = DriverCommand.FullPower;
        for (var i = 0; i <= kroki; i++)
        {
            effective = stop.Filter(state, DriverCommand.FullPower);
            state = state with { Steps = state.Steps + 1 };
        }

        return (stop.Phase, DoorCycle.TractionAllowed(stop.Phase), effective);
    }

    /// <summary>
    /// <b>Zapadka równościowa na TRZY brzmienia.</b> Wiersz jest tym, co gracz czyta
    /// w chwili, gdy pociąg nie rusza — zmiana jego brzmienia ma być decyzją, a nie
    /// skutkiem ubocznym zmiany w katalogu.
    /// </summary>
    [TestMethod]
    public void Trzy_brzmienia_wiersza_i_milczenie_gdy_trakcja_wolna()
    {
        Assert.AreEqual(
            "TRAKCJA ODCIĘTA — drzwi: otwarte",
            TractionBlock.Line(false, "otwarte", null),
            "wiersz blokady drzwiami zmienił brzmienie");
        Assert.AreEqual(
            "TRAKCJA ODCIĘTA — ATP hamuje służbowo",
            TractionBlock.Line(true, "zamknięte", Decyzja(ProtectionAction.ServiceIntervention)),
            "wiersz ingerencji służbowej zmienił brzmienie");
        Assert.AreEqual(
            "TRAKCJA ODCIĘTA — ATP hamuje awaryjnie",
            TractionBlock.Line(true, "zamknięte", Decyzja(ProtectionAction.EmergencyIntervention)),
            "wiersz ingerencji awaryjnej zmienił brzmienie");
        Assert.AreEqual(
            string.Empty,
            TractionBlock.Line(true, "zamknięte", Decyzja(ProtectionAction.None)),
            "wiersz mówi coś przy WOLNEJ trakcji — milczenie znaczy tu „jedź”");
        Assert.AreEqual(
            string.Empty,
            TractionBlock.Line(true, "zamknięte", null),
            "przejazd bez sygnalizacji dostał wiersz blokady, choć nic go nie blokuje");
    }

    /// <summary>
    /// <b>Kolejność ramion jest kolejnością FILTRÓW.</b> Gdy blokują obie strony,
    /// poleceniem kontrolera rządzi ochrona (<c>FirstRun.StepOnce</c>: filtr stacji
    /// <c>:1259</c>, ochrona <c>:1267</c>) — więc to ona ma być nazwana.
    /// </summary>
    [TestMethod]
    public void Gdy_blokuja_obie_nazwany_jest_filtr_OSTATNI()
    {
        Assert.AreEqual(
            "TRAKCJA ODCIĘTA — ATP hamuje służbowo",
            TractionBlock.Line(false, "otwarte", Decyzja(ProtectionAction.ServiceIntervention)),
            "przy dwóch blokadach naraz HUD nazywa drzwi, a poleceniem rządzi ATP — "
            + "gracz zamknąłby drzwi i pociąg dalej by nie ruszył");
    }

    /// <summary>
    /// <b>To jest właściwa treść tej bramki.</b> Dla każdej pary (faza drzwi ×
    /// reakcja ochrony) porównuje się DWIE rzeczy policzone niezależnie: czy filtry
    /// rdzenia obniżyły nastawnik i czy <see cref="TractionBlock.Blocked"/> mówi,
    /// że blokada jest. Rozejście się ich znaczy, że HUD ma własne zdanie o blokadzie
    /// — czyli dokładnie to drugie źródło prawdy, którego MB-03 zakazuje.
    /// </summary>
    [TestMethod]
    public void Odpowiedz_HUD_zgadza_sie_z_tym_co_ROBIA_filtry_rdzenia()
    {
        var akcje = new[]
        {
            ProtectionAction.None,
            ProtectionAction.ServiceIntervention,
            ProtectionAction.EmergencyIntervention,
        };
        // Kroki dobrane tak, żeby trafić w KAŻDĄ z siedmiu faz `DoorPhase` — przy
        // 120 Hz i cyklu 0,5 + 2,0 + 20,0 + 3,0 + 2,5 + 0,5 s. Nie jest to okrągła
        // siatka: okrągła minęłaby `Checking`, która trwa pół sekundy.
        var kroki = new[] { 0, 120, 600, 2820, 3240, 3390, 3600 };
        // Opóźnienie hamulca służbowego bierze się z rejestru pojazdu, a nie ze
        // stałej wpisanej w test — `ProtectionDecision.Apply` jest jego funkcją.
        var serviceBrake = VehicleModel.M7.DesignServiceBrakeMps2;
        var par = 0;
        var zBlokada = 0;
        var faz = new HashSet<DoorPhase>();

        foreach (var krok in kroki)
        {
            var (phase, allowed, poFiltrzeStacji) = Postoj(krok);
            faz.Add(phase);
            foreach (var akcja in akcje)
            {
                par++;
                var decision = Decyzja(akcja);
                var poOchronie = decision.Apply(poFiltrzeStacji, serviceBrake);
                var zmierzone = poOchronie.Throttle < DriverCommand.FullPower.Throttle;
                var powiedziane = TractionBlock.Blocked(allowed, decision);

                Assert.AreEqual(zmierzone, powiedziane,
                    $"faza {phase} (krok {krok}), reakcja {akcja}: rdzeń obniżył "
                    + $"nastawnik = {zmierzone}, a HUD mówi blokada = {powiedziane} — "
                    + "HUD ma własne zdanie o blokadzie, czyli DRUGIE źródło prawdy");
                Assert.AreEqual(powiedziane, TractionBlock.Line(allowed, "x", decision).Length > 0,
                    $"faza {phase}, reakcja {akcja}: `Blocked` i `Line` mówią co innego");
                if (zmierzone)
                {
                    zBlokada++;
                }
            }
        }

        // DOLNE OSTRZE NA SAM POMIAR: bez niego pętla, która nic nie obiegła, przeszłaby
        // wszystkie asercje wyżej bez jednego sprawdzenia (6.D27).
        Assert.AreEqual(21, par, "siatka par przestała mieć 21 pozycji");
        Assert.AreEqual(20, zBlokada,
            "blokada wypadła w innej liczbie par niż zmierzone 20 — siatka opisuje "
            + "inne fazy albo inne reakcje");
        Assert.AreEqual(7, faz.Count,
            "siatka kroków przestała trafiać w każdą z siedmiu faz drzwi: "
            + string.Join(", ", faz.Select(f => f.ToString())));
    }

    /// <summary>
    /// Każdy wiersz, który MOŻE MILCZEĆ, chowa się po długości WŁASNEGO napisu —
    /// sprawdzane LEKSYKALNIE, bo inaczej nie da się tego sprawdzić wcale.
    ///
    /// <para><b>Ta bramka wyszła z ZIELONEJ kontroli negatywnej.</b> KN-4 podstawiła
    /// <c>_traction.Visible = true;</c> — czyli wiersz „TRAKCJA ODCIĘTA" widoczny
    /// przez cały przejazd — i zestaw został zielony (284/284). Powód jest zmierzony,
    /// a nie domyślony: wszystkie przypisania <c>Visible</c> stoją w węźle Godota,
    /// którego żaden test jednostkowy nie zbuduje.</para>
    ///
    /// <para><b>Dlaczego to nie jest kosmetyka.</b> W MB-03 milczenie wiersza blokady
    /// ZNACZY „jedź" — wiersz pojawia się wtedy i tylko wtedy, gdy gracz ciągnie
    /// i nic się nie dzieje. Wiersz widoczny zawsze zajmuje pasmo pierwsze, nie niosąc
    /// niczego, i odbiera całej pozycji jej treść: to była pozycja o PRIORYTECIE,
    /// a nie o dodaniu informacji.</para>
    /// </summary>
    [TestMethod]
    public void Kazdy_wiersz_ktory_moze_milczec_chowa_sie_po_WLASNYM_napisie()
    {
        var kod = HudSource();
        var cialo = kod[kod.IndexOf("public void Update(", StringComparison.Ordinal)..];

        foreach (var (pole, argument) in new[]
                 {
                     ("_station", "station"), ("_signalling", "signalling"),
                     ("_view", "view"), ("_help", "help"),
                     ("_summary", "summary"), ("_traction", "traction"),
                 })
        {
            StringAssert.Contains(cialo, $"{pole}.Visible = {argument}.Length > 0;",
                $"`{pole}` nie chowa się po długości `{argument}` — wiersz, który może "
                + "milczeć, a milczy niewidocznie, zajmuje miejsce w panelu bez treści");
        }

        // KONTROLA PRZYRZĄDU: trzy wiersze widoczne ZAWSZE są wymienione z nazwy,
        // a nie pominięte milczeniem. Bez tej pętli lista wyżej mogłaby opisywać
        // dowolny podzbiór i nikt by nie wiedział, czy któryś wypadł.
        foreach (var pole in new[] { "_speed", "_position", "_controls" })
        {
            Assert.IsFalse(cialo.Contains($"{pole}.Visible", StringComparison.Ordinal),
                $"`{pole}` zaczął się chować — te trzy wiersze niosą stan przejazdu "
                + "w każdej klatce i ich zniknięcie wygląda jak zawieszona gra");
        }
    }

    /// <summary>
    /// Wiersz prędkości ma DWA warianty, a tryb bez sufitu nie pyta o sufit —
    /// bramka na REGRESJĘ, którą znalazł przebieg CI, a nie lektura.
    ///
    /// <para><b>Co się stało.</b> Pierwsza wersja MB-03 podawała do HUD-u
    /// <c>Units.MpsToKmh(SpeedLimitMps)</c> bez warunku. <c>RunHeader.SpeedLimitMps</c>
    /// RZUCA przy odtwarzaniu telemetrii i rzuca świadomie: ruch jest wtedy zadany
    /// plikiem, a nie liczony, więc żadna liczba nie byłaby tam wynikiem prowadzenia
    /// przebiegu. Skutkiem był wyjątek w KAŻDEJ KLATCE — zmierzone: <b>12 983
    /// w 90 sekundach</b> — przebieg, który nigdy nie dochodził do warunku końca,
    /// i job CI wiszący <b>dziewiętnaście minut zamiast czterdziestu jeden sekund</b>.
    /// Kod wyjścia tego nie odróżniał: proces nie padał, tylko się nie kończył.</para>
    ///
    /// <para><b>Dlaczego bramka jest LEKSYKALNA.</b> `FirstRun` jest węzłem Godota,
    /// więc warunku w jego metodzie nie wywoła żaden test jednostkowy — to samo
    /// ograniczenie, co przy `TrainingWiringTests`. Sprawdzane są więc trzy rzeczy,
    /// których zniknięcie przywróciłoby usterkę: że sufit idzie przez `SufitKmh()`,
    /// że ta metoda pyta o TRYB, i że katalog ma drugi wariant wiersza.</para>
    /// </summary>
    [TestMethod]
    public void Tryb_BEZ_SUFITU_nie_pyta_o_sufit_i_ma_wlasny_wariant_wiersza()
    {
        var kod = FirstRunSource();

        StringAssert.Contains(kod, "private double? SufitKmh() =>",
            "zniknęła metoda `SufitKmh` — sufit wraca do wywołania bezwarunkowego, "
            + "a `RunHeader.SpeedLimitMps` rzuca przy odtwarzaniu telemetrii");
        StringAssert.Contains(kod, "_fromTelemetryMode ? null : Units.MpsToKmh(SpeedLimitMps)",
            "`SufitKmh` przestała pytać o TRYB — wyjątek jest tu informacją, że pytanie "
            + "nie ma sensu, więc poprawną odpowiedzią jest go nie zadać");
        Assert.IsFalse(
            kod.Contains("Units.MpsToKmh(SpeedLimitMps), _acceleration",
                StringComparison.Ordinal),
            "sufit wraca do `_hud.Update` bez warunku — to jest dokładnie ta regresja, "
            + "która zawiesiła job CI na dziewiętnaście minut");

        // Katalog MA drugi wariant, i to jest druga połowa tej samej regresji: bez
        // niego warunek wyżej nie miałby czego wyświetlić.
        Assert.AreEqual(
            "{0} km/h     a = {1} m/s²", UiText.Get("hud.speed.no-limit"),
            "wariant wiersza prędkości BEZ sufitu zmienił brzmienie albo zniknął");
        // IGŁA WZMOCNIONA, a nie wpisana na listę wyjątków: samo „sufit" pasuje
        // do TRZECH komunikatów `src/Game/` (`RunPlan.cs:595`, `FirstRun.cs:717`
        // i ten wpis), więc `test_every_needle_matches_at_most_one_message…` miało
        // rację, a `test_a_weakened_needle_lights_up_the_first_rung` przestawało
        // cokolwiek pokazywać — szczebel pierwszy zapalał się JUŻ przed osłabieniem.
        // `"km/h   sufit"` (z trzema spacjami) występuje w `src/Game/` DOKŁADNIE RAZ.
        StringAssert.Contains(UiText.Get("hud.speed"), "km/h   sufit",
            "wariant Z sufitem przestał go nazywać albo zmienił odstęp — a odstęp "
            + "jest tu jedyną rzeczą, która odróżnia tę igłę od dwóch innych "
            + "komunikatów `src/Game/` niosących słowo „sufit”");
    }

    private static string FirstRunSource() => ZrodloGry("FirstRun.cs");

    private static string HudSource() => ZrodloGry(System.IO.Path.Combine("UI", "Hud.cs"));

    private static string ZrodloGry(string wzgledna)
    {
        var katalog = System.IO.Directory.GetCurrentDirectory();
        while (katalog is not null
               && !System.IO.Directory.Exists(System.IO.Path.Combine(katalog, ".git")))
        {
            katalog = System.IO.Directory.GetParent(katalog)?.FullName;
        }

        Assert.IsNotNull(katalog, "nie znaleziono korzenia repozytorium");
        return System.IO.File.ReadAllText(
            System.IO.Path.Combine(katalog!, "src", "Game", wzgledna));
    }
}
