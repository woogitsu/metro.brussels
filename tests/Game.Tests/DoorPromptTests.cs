using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Podpowiedź drzwi ręcznych w HUD-zie (MB-08).
///
/// <para><b>Ten plik istnieje dlatego, że MB-03 zmierzyło, ile warta jest bramka
/// na kodzie w węźle Godota: NIC.</b> Kontrola negatywna KN-4 tamtej pozycji
/// (<c>_traction.Visible = true</c>, czyli wiersz widoczny zawsze) nie zapaliła ANI
/// JEDNEGO testu, bo wszystkie przypisania stały w klasie, której żaden test
/// jednostkowy nie zbuduje. Napis o drzwiach stoi więc w <see cref="DoorPrompt"/>,
/// czyli poza <c>FirstRun</c> — i stąd te testy w ogóle mogą istnieć.</para>
/// </summary>
[TestClass]
public sealed class DoorPromptTests
{
    private static readonly DoorPhase[] WszystkieFazy = Enum.GetValues<DoorPhase>();

    [TestMethod]
    public void Podpowiedz_otwarcia_podaje_wolna_trakcje_DOKLADNIE_tam_gdzie_rdzen_ja_zwalnia()
    {
        // Informacja o wolnej trakcji ma odpowiadać rdzeniowi, lecz nie zachęcać
        // do odjazdu przed otwarciem drzwi i obsługą peronu.
        var podpowiedz = UiText.Get("hud.doors.open-to-serve");
        var zHudu = WszystkieFazy
            .Where(faza => DoorPrompt.For(faza, refusal: null) == podpowiedz)
            .ToList();
        var zRdzenia = WszystkieFazy.Where(DoorCycle.TractionAllowed).ToList();

        CollectionAssert.AreEqual(zRdzenia, zHudu,
            "HUD podaje wolną trakcję w fazach " + string.Join(", ", zHudu)
            + ", a rdzeń zwalnia trakcję w " + string.Join(", ", zRdzenia));
        Assert.AreEqual(1, zRdzenia.Count, "bez tego ostrza zgodność dwóch pustych zbiorów "
            + "przeszłaby tak samo dobrze, jak zgodność dwóch prawdziwych");
    }

    [TestMethod]
    public void Zamkniete_drzwi_przed_obsluga_peronu_nie_zachecaja_do_odjazdu()
    {
        var postoj = new StationStop(new DoorCycle(8.0), FixedStep.Simulation, DoorControl.Manual);
        Assert.AreEqual(DoorPhase.Closed, postoj.Phase,
            "ręczny postój przed otwarciem drzwi zaczyna się w fazie zamkniętej");
        Assert.IsFalse(postoj.Finished, "peron nie został jeszcze obsłużony");
        Assert.IsTrue(DoorCycle.TractionAllowed(postoj.Phase),
            "fizyczna możliwość ruszenia nie oznacza zakończenia obsługi");

        var tekst = DoorPrompt.For(postoj.Phase, refusal: null);
        StringAssert.Contains(tekst, "D: otwórz drzwi",
            "podpowiedź ma prowadzić do obsługi peronu przed odjazdem");
        Assert.AreEqual(UiText.Get("hud.doors.open-to-serve"), tekst,
            "fizyczny stan nastawnika i polecenie otwarcia pozostają widoczne razem");
        Assert.IsFalse(tekst.Contains("można odjechać", StringComparison.OrdinalIgnoreCase),
            "odjazd z zamkniętymi drzwiami pominąłby obsługę peronu");
    }

    [TestMethod]
    public void Reczny_postoj_rozdziela_faze_podpowiedz_i_wynik_na_czytelne_wiersze()
    {
        foreach (var (phase, action) in new[]
        {
            (DoorPhase.Closed, "D: otwórz drzwi"),
            (DoorPhase.Open, "F zamyka drzwi"),
        })
        {
            var text = UiText.Format("hud.station.doors-manual",
                phase == DoorPhase.Closed ? "zamknięte" : "otwarte",
                DoorPrompt.For(phase, refusal: null), "+0.03", 1);
            var lines = text.Split('\n');
            Assert.AreEqual(3, lines.Length, "fazę, działanie i wynik trzeba odczytać osobno");
            Assert.AreEqual("DRZWI " + (phase == DoorPhase.Closed ? "zamknięte" : "otwarte")
                + " (ręcznie)", lines[0], "pierwsza linia ma nazywać dokładną fazę");
            StringAssert.Contains(lines[1], action, "druga linia ma podawać następny klawisz");
            StringAssert.Contains(lines[2], "błąd zatrzymania +0.03 m",
                "trzecia linia ma zachować dokładność zatrzymania");
            StringAssert.Contains(lines[2], "obsłużone 1",
                "trzecia linia ma zachować licznik obsługi");
        }
    }

    [TestMethod]
    public void W_fazie_otwartej_HUD_prosi_o_zamkniecie_a_nie_o_otwarcie()
    {
        Assert.AreEqual(
            UiText.Get("hud.doors.prompt-close"),
            DoorPrompt.For(DoorPhase.Open, refusal: null),
            "w fazie otwartej jedyną rzeczą do zrobienia jest zamknięcie");
    }

    [TestMethod]
    public void W_fazach_ruchu_skrzydel_HUD_mowi_o_zablokowanej_trakcji()
    {
        var wRuchu = WszystkieFazy
            .Where(f => f != DoorPhase.Closed && f != DoorPhase.Open)
            .ToList();
        Assert.AreEqual(5, wRuchu.Count, "cykl ma pięć faz poza zamkniętą i otwartą");

        foreach (var faza in wRuchu)
        {
            Assert.AreEqual(
                UiText.Get("hud.doors.working"), DoorPrompt.For(faza, refusal: null),
                $"faza {faza}");
        }
    }

    [TestMethod]
    public void Odmowa_ma_pierwszenstwo_przed_podpowiedzia_w_KAZDEJ_fazie()
    {
        // Odmowa odpowiada na pytanie, które gracz właśnie zadał; podpowiedź — na takie,
        // którego nie zadał nikt. Sprawdzane na siatce faza × powód, a nie na jednej
        // parze: przy jednej parze przeoczenie w którejkolwiek fazie byłoby niewidoczne.
        foreach (var faza in WszystkieFazy)
        {
            foreach (var powod in Enum.GetValues<DoorRefusal>().Where(r => r != DoorRefusal.None))
            {
                Assert.AreEqual(
                    UiText.Format("hud.doors.refused", DoorPrompt.Reason(powod)),
                    DoorPrompt.For(faza, powod),
                    $"faza {faza}, powód {powod}");
            }
        }
    }

    [TestMethod]
    public void Kazdy_powod_odmowy_ma_WLASNE_zdanie_z_katalogu()
    {
        var widziane = new HashSet<string>(StringComparer.Ordinal);
        foreach (var powod in Enum.GetValues<DoorRefusal>().Where(r => r != DoorRefusal.None))
        {
            var zdanie = DoorPrompt.Reason(powod);
            Assert.IsTrue(
                UiText.Keys.Any(k => string.Equals(UiText.Get(k), zdanie, StringComparison.Ordinal)),
                $"{powod} nie pochodzi z katalogu tekstów: {zdanie}");
            Assert.IsTrue(widziane.Add(zdanie), $"{powod} powtarza cudze zdanie: {zdanie}");
        }

        Assert.AreEqual(5, widziane.Count, "pięć powodów odmowy, pięć różnych zdań");
    }

    [TestMethod]
    public void Czlon_spoza_wyliczenia_dostaje_nazwe_WIDOCZNA_zamiast_wyjatku()
    {
        // Ramię domyślne ma ten sam powód, co w `FirstRun.Faza`: wyjątek w metodzie
        // składającej wiersz HUD-u przewróciłby klatkę zamiast powiedzieć graczowi,
        // czego nie umiemy nazwać. Nazwa angielska jest widoczna i zgłaszalna.
        var nazwa = DoorPrompt.Reason((DoorRefusal)99);
        Assert.AreEqual("99", nazwa, "ramię domyślne oddaje nazwę członu, a nie pustkę");
        Assert.IsFalse(
            UiText.Keys.Any(k => string.Equals(UiText.Get(k), nazwa, StringComparison.Ordinal)),
            "wyjście awaryjne nie udaje katalogu");
    }

    [TestMethod]
    public void Powod_None_nie_ma_klucza_bo_nie_jest_odmowa()
    {
        // `DoorRefusal.None` znaczy „przyjęte", więc nie ma zdania dla gracza i nie ma go
        // mieć. `For` dostaje wtedy `null`, a nie „brak powodu" — i właśnie dlatego
        // argument jest typem dopuszczającym `null`.
        Assert.AreEqual("None", DoorPrompt.Reason(DoorRefusal.None),
            "None nie jest odmową, więc nie ma klucza w katalogu");
        Assert.AreEqual(
            UiText.Get("hud.doors.open-to-serve"), DoorPrompt.For(DoorPhase.Closed, refusal: null),
            "brak odmowy to `null`, a nie `DoorRefusal.None`");
    }
}
