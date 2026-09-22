using System;
using System.Collections.Generic;
using MetroBxl.Game.Assets;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Plik ZŁY w każdym zmierzonym kształcie kończy się w jednej z dwóch klauzul osłony
/// czytników JSON sceny — a nie wyjątkiem, którego nie łapie nic (6.D235).
///
/// <para><b>Prawdziwe loadery, prawdziwe wyjątki.</b> Kształty są te, na których
/// 22.09.2026 zmierzono ucieczkę; test nie pyta, co loader rzuca, tylko czy rzucony typ
/// trafia do którejś z klauzul <c>FirstRun</c>.</para>
/// </summary>
[TestClass]
public sealed class BadFileTests
{
    /// <summary>Kopia filtra klauzuli pierwszej z <c>FirstRun</c> — ta sama co w <c>BrokenJsonRefusalTests</c>.</summary>
    private static bool ZlapieKlauzulaPierwsza(Exception error) =>
        error is ArgumentException or FormatException;

    private static IEnumerable<(string Nazwa, string Json)> ZlePliki()
    {
        yield return ("zepsuta składnia", "{{{");
        yield return ("napis pusty", "");
        yield return ("obiekt pusty", "{}");
        yield return ("korzeń-tablica", "[]");
        yield return ("korzeń-liczba", "5");
        yield return ("korzeń-napis", "\"napis\"");
        yield return ("pole złego typu", "{\"points\": 5}");
        yield return ("obce pole", "{\"chunks\": 5}");
    }

    private static IEnumerable<(string Nazwa, Action<string> Wywolaj)> Czytniki()
    {
        yield return ("TrackAxis.FromJson", json => TrackAxis.FromJson(json));
        yield return ("ChunkManifest.FromJson", json => ChunkManifest.FromJson(json));
        yield return ("SignallingPlan.FromJson", json => SignallingPlan.FromJson(json));
    }

    [TestMethod]
    public void Kazdy_zly_plik_trafia_do_jednej_z_dwoch_klauzul_oslony()
    {
        var pierwsza = 0;
        var druga = 0;
        foreach (var (czytnik, wywolaj) in Czytniki())
        {
            foreach (var (ksztalt, json) in ZlePliki())
            {
                Exception? error = null;
                try
                {
                    wywolaj(json);
                }
                catch (Exception e)
                {
                    error = e;
                }

                if (error is null)
                {
                    Assert.Fail($"{czytnik} przyjął plik `{ksztalt}` bez odmowy");
                }

                if (ZlapieKlauzulaPierwsza(error))
                {
                    pierwsza++;
                }
                else
                {
                    Assert.IsTrue(BadFile.IsWrongJsonShape(error),
                        $"{czytnik} na `{ksztalt}` rzuca {error.GetType().Name}, którego nie łapie "
                        + "żadna klauzula osłony — scena skończyłaby się zrzutem albo zawisła");
                    druga++;
                }
            }
        }

        // Obie klauzule są POTRZEBNE i to jest przybite liczbą: klauzula druga ze
        // zbiorem pustym byłaby zdaniem o niczym, a pierwsza — tą sprzed 6.D235.
        Assert.AreEqual(11, pierwsza, $"klauzula pierwsza złapała {pierwsza} z 24 par czytnik × kształt");
        Assert.AreEqual(13, druga, $"klauzula druga złapała {druga} z 24 par czytnik × kształt");
    }

    [TestMethod]
    public void Klauzula_druga_nie_lapie_odmow_z_polskim_komunikatem()
    {
        // Rozłączność: odmowa loadera ma iść klauzulą PIERWSZĄ, bo tylko tam wolno
        // przepisać jej komunikat. Gdyby druga łapała też ją, kolejność klauzul
        // przestałaby być bez znaczenia, a komunikat zależałby od niej.
        Assert.IsFalse(BadFile.IsWrongJsonShape(new FormatException("x")),
            "klauzula druga łapie FormatException");
        Assert.IsFalse(BadFile.IsWrongJsonShape(new ArgumentException("x")),
            "klauzula druga łapie ArgumentException");
        Assert.IsTrue(BadFile.IsWrongJsonShape(new KeyNotFoundException()),
            "klauzula druga nie łapie KeyNotFoundException");
        Assert.IsTrue(BadFile.IsWrongJsonShape(new InvalidOperationException()),
            "klauzula druga nie łapie InvalidOperationException");
    }
}
