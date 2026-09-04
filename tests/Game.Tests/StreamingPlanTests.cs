using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using MetroBxl.Game.Assets;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Predykat streamowania i planu LOD po stronie sceny (<see cref="StreamingPlan"/>).
///
/// <para><b>Dlaczego połowa tych testów czyta plik zamiast liczyć w miejscu.</b>
/// Ten predykat jest napisany dwa razy — w Pythonie jako implementacja wzorcowa przy
/// generowaniu geometrii i w C# jako to, co wykona scena w czasie jazdy. Test
/// jednostkowy napisany osobno dla każdej strony sprawdza tylko, czy dana strona
/// zgadza się sama ze sobą. Dwie implementacje rozjeżdżają się cicho: pierwsza
/// rozbieżność nie wywala niczego, tylko robi dziurę w tunelu na jednym szwie przy
/// jednym kierunku jazdy.</para>
///
/// <para>Dlatego obie strony są przybite do JEDNEJ tablicy oczekiwań, policzonej raz
/// implementacją pythonową (<c>tools/tests/make_streaming_fixture.py</c>) i zapisanej
/// w repozytorium. Pythona pilnuje <c>tools/tests/test_streaming_fixture.py</c>,
/// C# — ten plik. Żadna strona nie woła drugiej w trakcie testu.</para>
///
/// <para>Wzorzec jest z PRAWDZIWEGO manifestu (L1_A, 12 chunków, 6686,739 m), nie
/// z wymyślonego JSON-a. To nie kosmetyka: chainage szwów ma wtedy tyle miejsc po
/// przecinku, ile ma naprawdę, a próbki leżą dokładnie na szwach. Szew wpisany
/// z ręki jako <c>1754.15</c> mija prawdziwy <c>1754.152651</c> o cztery milimetry
/// i sprawdza zwykły punkt w środku chunka zamiast granicy (§5.1).</para>
/// </summary>
[TestClass]
public sealed class StreamingPlanTests
{
    private static ChunkManifest? _manifest;
    private static JsonDocument? _plans;

    private static string FixturePath(string name)
        => Path.Combine(AppContext.BaseDirectory, "fixtures", name);

    private static ChunkManifest Manifest => _manifest ??=
        ChunkManifest.FromJson(File.ReadAllText(FixturePath("L1_A-chunks.json")));

    private static JsonElement Plans => (_plans ??=
        JsonDocument.Parse(File.ReadAllText(FixturePath("L1_A-streaming-plans.json")))).RootElement;

    // --- zgodność z implementacją wzorcową ------------------------------------------

    /// <summary>
    /// Każdy wiersz tablicy wzorcowej: okno, rezydencja, poziomy i kolizje.
    ///
    /// <para>To jest właściwa bramka tego pliku. Reszta testów opisuje pojedyncze
    /// własności; ten sprawdza CAŁY predykat na 138 wierszach naraz, w obu kierunkach
    /// jazdy, z próbkami dokładnie na każdym z 13 szwów.</para>
    /// </summary>
    [TestMethod]
    public void EveryRowOfThePythonReferenceTableIsReproducedExactly()
    {
        var rows = 0;
        var seams = 0;
        var seamChainages = new HashSet<double>();
        foreach (var chunk in Manifest.Chunks)
        {
            seamChainages.Add(chunk.StartM);
            seamChainages.Add(chunk.EndM);
        }

        foreach (var row in Plans.EnumerateArray())
        {
            rows++;
            var chainage = row.GetProperty("chainage_m").GetDouble();
            var heading = row.GetProperty("heading").GetDouble();
            var where = string.Create(CultureInfo.InvariantCulture,
                $"chainage {chainage:R} m, kierunek {heading:R}");

            if (seamChainages.Contains(chainage))
            {
                seams++;
            }

            var window = StreamingPlan.Window(Manifest, chainage, heading);
            Assert.AreEqual(row.GetProperty("window_low_m").GetDouble(), window.LowM, 0.0,
                $"dolny koniec okna, {where}");
            Assert.AreEqual(row.GetProperty("window_high_m").GetDouble(), window.HighM, 0.0,
                $"górny koniec okna, {where}");

            var expectedResident = row.GetProperty("resident")
                .EnumerateArray().Select(e => e.GetString()).ToArray();
            var resident = StreamingPlan.ChunksForTrain(Manifest, chainage, heading)
                .Select(c => c.Id).ToArray();
            CollectionAssert.AreEqual(expectedResident, resident,
                $"rezydencja, {where}: wzorzec [{string.Join(",", expectedResident)}], "
                + $"scena [{string.Join(",", resident)}]");

            var plan = StreamingPlan.LodPlan(Manifest, chainage, heading);
            foreach (var entry in row.GetProperty("lod").EnumerateArray())
            {
                var id = entry.GetProperty("id").GetString()!;
                Assert.IsTrue(plan.ContainsKey(id), $"brak {id} w planie LOD, {where}");
                Assert.AreEqual(entry.GetProperty("level").GetInt32(), plan[id],
                    $"poziom chunka {id}, {where}");
            }

            Assert.AreEqual(row.GetProperty("lod").GetArrayLength(), plan.Count,
                $"plan LOD ma inną liczbę pozycji niż wzorzec, {where}");

            var expectedCollision = row.GetProperty("collision")
                .EnumerateArray().Select(e => e.GetString()).ToArray();
            CollectionAssert.AreEqual(expectedCollision,
                StreamingPlan.CollisionPlan(Manifest, chainage, heading).ToArray(),
                $"plan kolizji, {where}");
        }

        // Bez tego test przechodziłby na pustym albo okrojonym pliku wzorca.
        Assert.AreEqual(138, rows, "tablica wzorcowa ma inną liczbę wierszy niż w chwili pisania");
        Assert.AreEqual(26, seams,
            $"próbek leżących DOKŁADNIE na szwie jest {seams} — wzorzec przestał sprawdzać granice");
    }

    // --- okno -----------------------------------------------------------------------

    /// <summary>
    /// Okno jest niesymetryczne i kierunek jazdy je odwraca, a nie przesuwa.
    /// </summary>
    [TestMethod]
    public void DrivingBackwardsPutsTheLongerReachTowardsFallingChainage()
    {
        var forward = StreamingPlan.Window(1000.0, 600.0, 300.0, heading: 1.0);
        Assert.AreEqual(700.0, forward.LowM, 0.0);
        Assert.AreEqual(1600.0, forward.HighM, 0.0);

        var backward = StreamingPlan.Window(1000.0, 600.0, 300.0, heading: -1.0);
        Assert.AreEqual(400.0, backward.LowM, 0.0);
        Assert.AreEqual(1300.0, backward.HighM, 0.0);

        // Oba okna mają tę samą długość — zmienia się strona, nie budżet pamięci.
        Assert.AreEqual(forward.HighM - forward.LowM, backward.HighM - backward.LowM, 0.0);
    }

    /// <summary>
    /// Zero należy do jazdy do przodu. Granica czytana z wnętrza funkcji, więc dosłowna.
    /// </summary>
    [TestMethod]
    public void HeadingExactlyZeroCountsAsForward()
    {
        var window = StreamingPlan.Window(1000.0, 600.0, 300.0, heading: 0.0);
        Assert.AreEqual(700.0, window.LowM, 0.0);
        Assert.AreEqual(1600.0, window.HighM, 0.0);
    }

    [TestMethod]
    public void ANegativeReachIsRefusedInsteadOfSilentlyInvertingTheWindow()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => StreamingPlan.Window(1000.0, -1.0, 300.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => StreamingPlan.Window(1000.0, 600.0, -1.0));
    }

    [TestMethod]
    public void TheManifestWindowIsTheOneFromTheArchitectureDocument()
    {
        // docs/01-architecture.md: 600 m przed składem, 300 m za nim.
        var window = StreamingPlan.Window(Manifest, 1000.0);
        Assert.AreEqual(1000.0 - 300.0, window.LowM, 0.0);
        Assert.AreEqual(1000.0 + 600.0, window.HighM, 0.0);
    }

    // --- szwy -----------------------------------------------------------------------

    /// <summary>
    /// Skład DOKŁADNIE na szwie ma w pamięci oba chunki.
    ///
    /// <para>Wartość szwu jest czytana z manifestu, nie wpisana — inaczej test nigdy
    /// nie trafiłby w granicę i nie odróżniłby <c>&lt;=</c> od <c>&lt;</c> (§5.1).</para>
    /// </summary>
    [TestMethod]
    public void AtTheExactSeamBothChunksAreResident()
    {
        for (var i = 1; i < Manifest.Chunks.Count; i++)
        {
            var seam = Manifest.Chunks[i].StartM;
            Assert.AreEqual(Manifest.Chunks[i - 1].EndM, seam, 0.0,
                "szwy manifestu nie są równe co do bitu — wzorzec nie testuje granicy");

            var resident = StreamingPlan.ChunksInRange(Manifest, seam, seam)
                .Select(c => c.Id).ToArray();
            CollectionAssert.AreEqual(
                new[] { Manifest.Chunks[i - 1].Id, Manifest.Chunks[i].Id }, resident,
                $"na szwie {seam:R} m rezydencja to [{string.Join(",", resident)}]");
        }
    }

    /// <summary>Odległość do chunka, w którym stoi skład, jest dokładnie zerem.</summary>
    [TestMethod]
    public void DistanceInsideAChunkIsExactlyZeroIncludingBothItsEnds()
    {
        var chunk = Manifest.Chunks[3];
        Assert.AreEqual(0.0, StreamingPlan.DistanceM(chunk, chunk.StartM), 0.0);
        Assert.AreEqual(0.0, StreamingPlan.DistanceM(chunk, chunk.EndM), 0.0);
        Assert.AreEqual(0.0,
            StreamingPlan.DistanceM(chunk, (chunk.StartM + chunk.EndM) / 2.0), 0.0);

        Assert.AreEqual(1.0, StreamingPlan.DistanceM(chunk, chunk.StartM - 1.0), 1e-9);
        Assert.AreEqual(1.0, StreamingPlan.DistanceM(chunk, chunk.EndM + 1.0), 1e-9);
    }

    // --- poziomy --------------------------------------------------------------------

    /// <summary>
    /// Dystans równy progowi należy już do poziomu wyższego.
    ///
    /// <para>Progi są brane z manifestu (158,0 i 404,4 m dla L1_A), więc równość jest
    /// dosłowna. Test wpisujący próg z ręki minąłby go i nie odróżnił
    /// <c>&gt;=</c> od <c>&gt;</c>.</para>
    /// </summary>
    [TestMethod]
    public void ADistanceExactlyOnTheThresholdBelongsToTheCoarserLevel()
    {
        var thresholds = Manifest.LodThresholds;
        CollectionAssert.AreEqual(new[] { 158.0, 404.4 }, thresholds.ToArray(),
            "progi z manifestu się zmieniły — reszta tego testu przestała trafiać w granicę");

        Assert.AreEqual(0, StreamingPlan.LodForDistance(thresholds[0] - 0.1, thresholds));
        Assert.AreEqual(1, StreamingPlan.LodForDistance(thresholds[0], thresholds));
        Assert.AreEqual(1, StreamingPlan.LodForDistance(thresholds[1] - 0.1, thresholds));
        Assert.AreEqual(2, StreamingPlan.LodForDistance(thresholds[1], thresholds));
        Assert.AreEqual(2, StreamingPlan.LodForDistance(1e6, thresholds));
    }

    /// <summary>Poziom 0 nie ma progu; wciągnięcie go przesunęłoby wszystkie pozostałe.</summary>
    [TestMethod]
    public void LevelZeroHasNoThresholdSoTheListIsOneShorterThanTheLevels()
    {
        Assert.AreEqual(2, Manifest.LodThresholds.Count);
        Assert.AreEqual(0, StreamingPlan.LodForDistance(0.0, Manifest.LodThresholds),
            "chunk pod składem wypadł z poziomu 0 — progi są przesunięte o jeden");
    }

    /// <summary>Chunk pod składem jest ZAWSZE na poziomie 0, na całej długości osi.</summary>
    [TestMethod]
    public void TheChunkUnderTheTrainIsAlwaysAtFullDetail()
    {
        foreach (var chunk in Manifest.Chunks)
        {
            var middle = (chunk.StartM + chunk.EndM) / 2.0;
            var plan = StreamingPlan.LodPlan(Manifest, middle);
            Assert.AreEqual(0, plan[chunk.Id],
                $"chunk {chunk.Id} pod składem na {middle:F1} m nie jest na poziomie 0");
        }
    }

    /// <summary>
    /// Plan LOD naprawdę oszczędza trójkąty, a nie tylko przepisuje poziomy.
    /// </summary>
    [TestMethod]
    public void ThePlanCostsFewerTrianglesThanDrawingEverythingAtLevelZero()
    {
        var plan = StreamingPlan.LodPlan(Manifest, 3000.0);
        var planned = StreamingPlan.TrianglesFor(Manifest, plan);

        var flat = plan.ToDictionary(e => e.Key, _ => 0, StringComparer.Ordinal);
        var full = StreamingPlan.TrianglesFor(Manifest, flat);

        Assert.IsTrue(planned < full,
            $"plan daje {planned} trójkątów, pełna siatka {full} — LOD niczego nie oszczędza");
        Assert.IsTrue(planned > 0, "plan daje zero trójkątów — nic by się nie narysowało");
    }

    [TestMethod]
    public void AskingForALevelTheManifestDoesNotHaveIsRefusedNotRoundedToZero()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Manifest.Chunks[0].Lod(7));
    }

    // --- różnica dla pętli klatki ---------------------------------------------------

    /// <summary>Trzy listy pętli klatki: co wczytać, co zostawić, co zwolnić.</summary>
    [TestMethod]
    public void TheDeltaSplitsResidencyIntoLoadKeepAndFree()
    {
        var needed = StreamingPlan.ChunksForTrain(Manifest, 3000.0).Select(c => c.Id).ToArray();
        Assert.IsTrue(needed.Length >= 2, "za mało chunków w oknie, żeby test cokolwiek dzielił");

        var loaded = new[] { needed[0], "chunk-ktorego-juz-nie-ma" };
        var delta = StreamingPlan.Delta(Manifest, 3000.0, loaded);

        CollectionAssert.AreEqual(new[] { needed[0] }, delta.Keep.ToArray());
        CollectionAssert.AreEqual(needed.Skip(1).ToArray(), delta.Load.ToArray());
        CollectionAssert.AreEqual(new[] { "chunk-ktorego-juz-nie-ma" }, delta.Free.ToArray());
    }

    /// <summary>Nic nie może wypaść ani powtórzyć się między trzema listami.</summary>
    [TestMethod]
    public void LoadAndKeepTogetherAreExactlyTheResidencyAndFreeIsDisjoint()
    {
        var loaded = Manifest.Chunks.Take(5).Select(c => c.Id).ToArray();

        for (var chainage = 0.0; chainage <= Manifest.AxisLengthM; chainage += 137.0)
        {
            var delta = StreamingPlan.Delta(Manifest, chainage, loaded);
            var needed = StreamingPlan.ChunksForTrain(Manifest, chainage)
                .Select(c => c.Id).ToArray();

            CollectionAssert.AreEquivalent(needed, delta.Load.Concat(delta.Keep).ToArray(),
                $"load+keep to nie jest rezydencja na {chainage:F0} m");
            Assert.AreEqual(0, delta.Free.Intersect(needed).Count(),
                $"chunk jest jednocześnie zwalniany i potrzebny na {chainage:F0} m");
            Assert.AreEqual(0, delta.Load.Intersect(delta.Keep).Count(),
                $"chunk jest jednocześnie wczytywany i trzymany na {chainage:F0} m");
        }
    }

    /// <summary>
    /// Kolejność zwalniania jest powtarzalna, niezależnie od kolejności wejścia.
    /// </summary>
    [TestMethod]
    public void FreeComesOutSortedSoTwoRunsFreeMemoryInTheSameOrder()
    {
        var ids = new[] { "z-obcy", "a-obcy", "m-obcy" };
        var forward = StreamingPlan.Delta(Manifest, 3000.0, ids).Free.ToArray();
        var reversed = StreamingPlan.Delta(Manifest, 3000.0, ids.Reverse()).Free.ToArray();

        CollectionAssert.AreEqual(new[] { "a-obcy", "m-obcy", "z-obcy" }, forward);
        CollectionAssert.AreEqual(forward, reversed);
    }

    // --- kolizje --------------------------------------------------------------------

    /// <summary>Bryła kolizyjna chunka pod składem jest wczytana zawsze.</summary>
    [TestMethod]
    public void TheCollisionHullUnderTheTrainIsAlwaysLoaded()
    {
        foreach (var chunk in Manifest.Chunks)
        {
            var middle = (chunk.StartM + chunk.EndM) / 2.0;
            CollectionAssert.Contains(StreamingPlan.CollisionPlan(Manifest, middle).ToArray(),
                chunk.Id, $"brak bryły kolizyjnej pod składem na {middle:F1} m");
        }
    }

    /// <summary>
    /// Promień kolizji jest węższy od okna streamowania — inaczej byłby bez sensu.
    /// </summary>
    [TestMethod]
    public void CollisionResidencyIsNarrowerThanStreamingResidency()
    {
        Assert.AreEqual(150.0, Manifest.CollisionRadiusM, 1e-9,
            "promień kolizji z manifestu przestał być 150 m (długość M7 94,0 m z zapasem)");

        var wider = 0;
        for (var chainage = 0.0; chainage <= Manifest.AxisLengthM; chainage += 97.0)
        {
            var collision = StreamingPlan.CollisionPlan(Manifest, chainage);
            var resident = StreamingPlan.ChunksForTrain(Manifest, chainage).ToArray();
            Assert.IsTrue(collision.Count <= resident.Length,
                $"kolizji jest więcej niż chunków w pamięci na {chainage:F0} m");
            if (collision.Count < resident.Length)
            {
                wider++;
            }
        }

        Assert.IsTrue(wider > 0,
            "kolizja nigdy nie jest węższa od rezydencji — promień nic nie zawęża");
    }

    /// <summary>
    /// Chunk dokładnie na promieniu kolizji JESZCZE się liczy.
    ///
    /// <para>Promień nie jest tu wpisany z ręki, tylko odczytany z
    /// <see cref="StreamingPlan.DistanceM"/> dla wybranego chunka i podany z powrotem
    /// jako próg. Dzięki temu porównanie <c>odległość &lt;= promień</c> zachodzi na
    /// wartościach równych CO DO BITU, bez oglądania się na to, czy
    /// <c>start - (start - 150)</c> wyszło równo 150 (§5.1: dokładnie tylko wtedy, gdy
    /// wartość jest czytana z wnętrza funkcji).</para>
    ///
    /// <para>Kontrola negatywna 03.09.2026: mutacja <c>&lt;=</c> na <c>&lt;</c>
    /// przechodziła cały zestaw 43/43. Żadna z próbek co 97 m nie leżała dokładnie
    /// 150,0 m od granicy chunka, więc test „kolizja jest węższa od rezydencji"
    /// nigdy nie dotykał granicy, którą miał opisywać.</para>
    /// </summary>
    [TestMethod]
    public void AChunkExactlyAtTheCollisionRadiusIsStillLoaded()
    {
        // Skład stoi na początku osi; mierzymy, jak daleko stąd jest następny chunk,
        // i robimy z tej odległości promień. Chunk musi być REZYDENTNY — plan kolizji
        // wybiera spośród tego, co jest w oknie streamowania, więc chunk spoza okna
        // nie wszedłby do wyniku niezależnie od promienia i test niczego by nie mierzył.
        var chainage = Manifest.Chunks[0].StartM;
        var far = Manifest.Chunks[1];
        var distance = StreamingPlan.DistanceM(far, chainage);
        Assert.IsTrue(distance > 0.0, "następny chunk nie leży poza bieżącym — test nie ma progu");
        CollectionAssert.Contains(
            StreamingPlan.ChunksForTrain(Manifest, chainage).Select(c => c.Id).ToArray(),
            far.Id, $"chunk {far.Id} nie jest rezydentny na {chainage:R} m");

        var atRadius = StreamingPlan.CollisionPlan(Manifest, chainage, radiusM: distance);
        CollectionAssert.Contains(atRadius.ToArray(), far.Id,
            $"chunk {far.Id} dokładnie na promieniu {distance:R} m wypadł z planu kolizji");

        // I kontrola z drugiej strony: o jeden ULP mniej i już go nie ma.
        var justBelow = StreamingPlan.CollisionPlan(Manifest, chainage,
            radiusM: Math.BitDecrement(distance));
        CollectionAssert.DoesNotContain(justBelow.ToArray(), far.Id,
            $"chunk {far.Id} został w planie mimo promienia mniejszego o ULP — "
            + "porównanie nie patrzy na promień");
    }

    /// <summary>Każdy chunk niesie plik bryły kolizyjnej; brak byłby dziurą w podłodze.</summary>
    [TestMethod]
    public void EveryChunkCarriesACollisionFile()
    {
        foreach (var chunk in Manifest.Chunks)
        {
            Assert.IsNotNull(chunk.CollisionFile, $"chunk {chunk.Id} bez bryły kolizyjnej");
            Assert.IsTrue(chunk.CollisionTriangles > 0,
                $"chunk {chunk.Id} ma bryłę kolizyjną z {chunk.CollisionTriangles} trójkątów");
        }
    }

    // --- manifest -------------------------------------------------------------------

    /// <summary>Wzorzec to prawdziwy manifest, nie zaokrąglona atrapa.</summary>
    [TestMethod]
    public void TheFixtureIsARealManifestWithFractionalSeams()
    {
        Assert.AreEqual(12, Manifest.Chunks.Count);
        Assert.AreEqual(6686.739, Manifest.AxisLengthM, 1e-9);

        var fractional = Manifest.Chunks.Count(c => Math.Abs(c.EndM - Math.Round(c.EndM)) > 1e-9);
        Assert.IsTrue(fractional >= 10,
            $"tylko {fractional} z 12 szwów ma część ułamkową — wzorzec wygląda na wpisany z ręki");
    }

    /// <summary>Każdy chunk ma trzy poziomy i rosnąco po numerze.</summary>
    [TestMethod]
    public void EveryChunkHasAllThreeLevelsInAscendingOrder()
    {
        foreach (var chunk in Manifest.Chunks)
        {
            Assert.AreEqual(3, chunk.Lods.Count, $"chunk {chunk.Id}");
            for (var level = 0; level < chunk.Lods.Count; level++)
            {
                Assert.AreEqual(level, chunk.Lods[level].Level,
                    $"poziomy chunka {chunk.Id} nie są rosnące");
            }

            Assert.IsTrue(chunk.Lod(0).Triangles > chunk.Lod(2).Triangles,
                $"poziom 2 chunka {chunk.Id} nie jest lżejszy od poziomu 0");
        }
    }
}
