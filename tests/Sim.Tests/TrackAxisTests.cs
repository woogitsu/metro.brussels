using System;
using System.Globalization;
using System.IO;
using System.Linq;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy osi trasy. Kontrola z <c>src/Sim.Runner axis</c> jest **integracyjna** —
/// porównuje całą oś pakietu A z manifestem generatora i z Pythonem. Tutaj są
/// przypadki, których takie porównanie nie pokrywa: pojedynczy odcinek, kilometraż
/// dokładnie na wierzchołku, oba końce osi i wartości poza zakresem.
/// </summary>
[TestClass]
public sealed class TrackAxisTests
{
    /// <summary>Oś z dwóch punktów: nie ma czego zagęszczać, więc łamana zostaje bez zmian.</summary>
    [TestMethod]
    public void Pojedynczy_odcinek_nie_jest_zageszczany()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)));

        Assert.AreEqual(2, axis.Points.Count);
        Assert.AreEqual(100.0, axis.LengthM, 0.0);
        Assert.AreEqual(0.0, axis.ChainagesM[0], 0.0);
        Assert.AreEqual(100.0, axis.ChainagesM[1], 0.0);
    }

    /// <summary>Krok zagęszczania ≤ 0 to tryb wierny: wychodzi surowa łamana STIB.</summary>
    [TestMethod]
    public void Krok_niedodatni_zostawia_lamana_bez_zmian()
    {
        var json = Json((0.0, 0.0), (50.0, 0.0), (100.0, 40.0), (200.0, 40.0));

        var faithful = TrackAxis.FromJson(json, 0.0);
        var densified = TrackAxis.FromJson(json);

        Assert.AreEqual(4, faithful.Points.Count);
        Assert.AreEqual(0.0, faithful.MaxDeviationFromSourceM(), 0.0,
            "tryb wierny nie może odchylić się od źródła ani o metr, ani o bit");
        Assert.IsTrue(densified.Points.Count > faithful.Points.Count,
            "zagęszczanie ma dołożyć punkty, a nie tylko przepisać łamaną");
    }

    /// <summary>Powtórzony punkt jest usuwany — zerowy segment wywraca każdą normalizację.</summary>
    [TestMethod]
    public void Powtorzone_punkty_sa_usuwane()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (0.0, 0.0), (100.0, 0.0)), 0.0);

        Assert.AreEqual(2, axis.SourcePoints.Count);
        Assert.AreEqual(100.0, axis.LengthM, 0.0);
    }

    /// <summary>Oś, z której po odsianiu duplikatów zostaje jeden punkt, nie jest osią.</summary>
    [TestMethod]
    public void Os_z_jednego_punktu_jest_odrzucana()
    {
        Assert.ThrowsException<ArgumentException>(
            () => TrackAxis.FromJson(Json((5.0, 5.0), (5.0, 5.0))));
        Assert.ThrowsException<ArgumentNullException>(() => TrackAxis.FromJson(null!));
    }

    /// <summary>Kilometraż dokładnie na wierzchołku daje ten wierzchołek, a nie sąsiada.</summary>
    [TestMethod]
    public void Chainage_na_wierzcholku_daje_ten_wierzcholek()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (30.0, 0.0), (30.0, 40.0)), 0.0);

        var atVertex = axis.PointAt(30.0);

        Assert.AreEqual(30.0, atVertex.X, 1e-12);
        Assert.AreEqual(0.0, atVertex.Y, 1e-12);
        Assert.AreEqual(70.0, axis.LengthM, 1e-12);
    }

    /// <summary>Oba końce osi trafiają dokładnie w punkty skrajne.</summary>
    [TestMethod]
    public void Konce_osi_trafiaja_w_punkty_skrajne()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (30.0, 0.0), (30.0, 40.0)), 0.0);

        var start = axis.PointAt(0.0);
        var end = axis.PointAt(axis.LengthM);

        Assert.AreEqual(0.0, start.X, 0.0);
        Assert.AreEqual(0.0, start.Y, 0.0);
        Assert.AreEqual(30.0, end.X, 1e-12);
        Assert.AreEqual(40.0, end.Y, 1e-12);
    }

    /// <summary>
    /// Kilometraż poza osią jest przycinany do jej końców — tak samo jak w
    /// <c>tools/blender/placement.py: frame_at</c>. Skład dłuższy niż resztka osi ma
    /// stanąć na jej końcu, a nie zniknąć albo wylecieć w nieskończoność.
    /// </summary>
    [TestMethod]
    public void Chainage_poza_osia_jest_przycinany_do_konca()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)), 0.0);

        Assert.AreEqual(0.0, axis.PointAt(-500.0).X, 0.0);
        Assert.AreEqual(100.0, axis.PointAt(9999.0).X, 1e-12);
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => axis.PointAt(double.NaN));
    }

    /// <summary>Punkt w połowie odcinka leży w jego połowie — interpolacja liniowa, bez niespodzianek.</summary>
    [TestMethod]
    public void Punkt_w_polowie_odcinka_lezy_w_jego_polowie()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)), 0.0);

        var middle = axis.PointAt(25.0);

        Assert.AreEqual(25.0, middle.X, 1e-12);
        Assert.AreEqual(0.0, middle.Y, 0.0);
        Assert.AreEqual(0.0, middle.Z, 0.0);
    }

    /// <summary>Zagęszczona oś przechodzi przez punkty źródłowe i jest od nich dłuższa na łuku.</summary>
    [TestMethod]
    public void Zageszczenie_wybrzusza_luk_na_zewnatrz_ciagliwy_i_dluzszy()
    {
        var json = Json((0.0, 0.0), (50.0, 0.0), (100.0, 50.0), (100.0, 150.0));

        var faithful = TrackAxis.FromJson(json, 0.0);
        var densified = TrackAxis.FromJson(json);

        Assert.IsTrue(densified.LengthM > faithful.LengthM,
            "krzywa przez te same punkty nie może być krótsza od łamanej");
        Assert.IsTrue(densified.MaxDeviationFromSourceM() > 0.0,
            "gdyby odchyłka wyszła zerowa, znaczyłoby to, że interpolacja nic nie robi");

        // Krok zagęszczania dzieli **cięciwę** źródłowego odcinka na równe części,
        // a krzywa przez te punkty jest od cięciwy dłuższa — więc odstęp mierzony po
        // łuku bywa nieco większy niż nominalny krok. Zmierzone na tym łuku maksimum
        // to 5,036 m przy kroku 5,0 m, czyli 0,7 %. Granica 10 % łapie rozjazd
        // rzędu wielkości, a nie karze za geometrię krzywej.
        var worstGap = 0.0;
        for (var i = 1; i < densified.Points.Count; i++)
        {
            worstGap = Math.Max(worstGap, densified.ChainagesM[i] - densified.ChainagesM[i - 1]);
        }

        Assert.IsTrue(worstGap <= 1.10 * TrackAxis.DefaultRingStepM,
            $"największy odstęp {worstGap} m przy kroku {TrackAxis.DefaultRingStepM} m");
        Assert.IsTrue(worstGap > 0.5 * TrackAxis.DefaultRingStepM,
            "odstępy dużo mniejsze od kroku znaczyłyby, że zagęszczanie liczy coś innego niż cięciwę");
    }

    /// <summary>Stacje wychodzą posortowane po chainage bez względu na kolejność w pliku.</summary>
    [TestMethod]
    public void Stacje_sa_posortowane_po_chainage()
    {
        const string json = """
            {"id":"T","length_m":100.0,"vertical":{"status":"not_modelled"},
             "points":[[0,0,0],[100,0,0]],
             "stations":[{"name":"B","chainage_m":80.0},{"name":"A","chainage_m":10.0}]}
            """;

        var axis = TrackAxis.FromJson(json, 0.0);

        CollectionAssert.AreEqual(
            new[] { "A", "B" }, axis.Stations.Select(s => s.Name).ToArray());
        Assert.AreEqual(10.0, axis.Stations[0].ChainageM, 0.0);
    }

    /// <summary>
    /// Profil pionowy jest raportowany, a nie zgadywany. Dopóki oś ma status
    /// <c>not_modelled</c>, nie wolno wyprowadzać z niej pochylenia
    /// (<c>docs/21-measured-vs-assumed.md</c> §3).
    /// </summary>
    [TestMethod]
    public void Status_profilu_pionowego_jest_przenoszony_z_pliku()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)), 0.0);

        Assert.AreEqual("not_modelled", axis.VerticalStatus);
        Assert.IsFalse(axis.IsVerticalModelled);
    }

    /// <summary>
    /// Kontrola na prawdziwej osi pakietu A: liczby muszą zgadzać się z manifestem
    /// generatora (<c>reports/L1_A-chunks.md</c>: 447 punktów źródłowych, oś
    /// zagęszczona 6686,739 m, 12 stacji). Test jest pomijany, gdy testy zostały
    /// uruchomione poza repozytorium.
    /// </summary>
    [TestMethod]
    public void Os_pakietu_A_zgadza_sie_z_geometria_generatora()
    {
        var root = FindRepositoryRoot();
        if (root is null)
        {
            Assert.Inconclusive("brak repozytorium na dysku — kontrola osi pakietu A pominięta");
            return;
        }

        var axis = TrackAxis.FromJson(File.ReadAllText(Path.Combine(root, "data", "track", "L1_A.json")));

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[OŚ L1_A] źródłowych {axis.SourcePoints.Count}, zagęszczonych {axis.Points.Count}, " +
            $"długość {axis.LengthM:F3} m, odchyłka {axis.MaxDeviationFromSourceM():F4} m"));

        Assert.AreEqual("L1_A", axis.Id);
        Assert.AreEqual(447, axis.SourcePoints.Count);
        Assert.AreEqual(1349, axis.Points.Count);
        Assert.AreEqual(6686.739, axis.LengthM, 1e-3, "długość osi z manifestu chunków T-210");
        Assert.AreEqual(6686.35, axis.DeclaredLengthM, 1e-9);
        Assert.AreEqual(12, axis.Stations.Count);
        Assert.IsFalse(axis.IsVerticalModelled);
    }

    private static string Json(params (double X, double Y)[] points)
    {
        var coordinates = string.Join(",", points.Select(p => string.Create(
            CultureInfo.InvariantCulture, $"[{p.X:R},{p.Y:R},0.0]")));
        return string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},"points":[{{coordinates}}],"stations":[]}""");
    }

    private static string? FindRepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "CLAUDE.md")))
            {
                return directory.FullName;
            }

            directory = directory.Parent;
        }

        return null;
    }
}
