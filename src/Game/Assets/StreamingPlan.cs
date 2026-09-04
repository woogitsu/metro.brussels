using System;
using System.Collections.Generic;

namespace MetroBxl.Game.Assets;

/// <summary>Co ma być w pamięci i w jakiej rozdzielczości dla składu na danym chainage.</summary>
/// <param name="LowM">Dolny koniec okna streamowania.</param>
/// <param name="HighM">Górny koniec okna streamowania.</param>
public readonly record struct StreamWindow(double LowM, double HighM);

/// <summary>Różnica między tym, co jest wczytane, a tym, co być powinno.</summary>
/// <param name="Load">Chunki do wczytania.</param>
/// <param name="Keep">Chunki, które zostają bez ruchu.</param>
/// <param name="Free">Chunki do zwolnienia.</param>
public readonly record struct StreamingDelta(
    IReadOnlyList<string> Load,
    IReadOnlyList<string> Keep,
    IReadOnlyList<string> Free);

/// <summary>
/// Predykat streamowania i wyboru poziomu szczegółowości — strona sceny.
///
/// <para><b>To jest DRUGA implementacja tego samego predykatu.</b> Pierwsza,
/// wzorcowa, jest w Pythonie: <c>tools/blender/sweep.py</c> (<c>stream_window</c>,
/// <c>chunks_in_range</c>, <c>chunks_for_train</c>, <c>streaming_plan</c>) oraz
/// <c>tools/blender/lod.py</c> (<c>chunk_distance_m</c>, <c>lod_for_distance</c>,
/// <c>lod_plan</c>, <c>collision_plan</c>). Tamta liczy plany przy generowaniu
/// geometrii i pilnuje spójności manifestu; ta wykonuje je w czasie jazdy.</para>
///
/// <para>Dwie implementacje jednego predykatu rozjeżdżają się po cichu — pierwsza
/// rozbieżność nie wywala żadnego testu, tylko robi dziurę w tunelu na jednym szwie
/// przy jednym kierunku jazdy. Dlatego obie strony są przybite do jednej tablicy
/// oczekiwań, policzonej raz przez implementację pythonową i zapisanej w
/// <c>tests/Game.Tests/fixtures/L1_A-streaming-plans.json</c> przez
/// <c>tools/tests/make_streaming_fixture.py</c>. Pythona pilnuje
/// <c>tools/tests/test_streaming_fixture.py</c>, C# —
/// <c>tests/Game.Tests/StreamingPlanTests.cs</c>. Żadna nie woła drugiej, a rozjazd
/// którejkolwiek psuje jej własną bramkę.</para>
///
/// <para><b>Rezydencja i rozdzielczość to dwa różne pytania</b> i są tu rozdzielone
/// tak samo jak po stronie Pythona. Rezydencja („czy plik jest w pamięci") zależy od
/// chainage i zmienia się skokowo na granicach chunków. Rozdzielczość („którą siatkę
/// pokazać") zależy od odległości i zmienia się w sposób ciągły. Wciągnięcie LOD-u do
/// predykatu okna zmuszałoby do przeładowania chunka, który JEST już rezydentny, tylko
/// dlatego że zmienił się dystans — a tego streaming ma właśnie unikać.</para>
/// </summary>
public static class StreamingPlan
{
    /// <summary>
    /// Domyślny promień rezydencji bryły kolizyjnej, gdy manifest go nie niesie.
    ///
    /// <para>ZAŁOŻENIE PROJEKTOWE, nie dana o sieci: 150 m to skład M7 (94,0 m,
    /// <c>data/vehicle/m7-spec.json</c>) z zapasem po obu stronach. Ta sama liczba stoi
    /// w <c>tools/blender/lod.py</c> jako <c>COLLISION_RADIUS_M</c>.</para>
    /// </summary>
    public const double DefaultCollisionRadiusM = 150.0;

    /// <summary>
    /// Okno streamowania wokół składu, z uwzględnieniem kierunku jazdy.
    ///
    /// <para><c>heading</c> mniejsze od zera znaczy jazdę w stronę malejącego chainage,
    /// więc „przed składem" leży wtedy po stronie mniejszych wartości. Bez tego skład
    /// jadący z powrotem doładowywałby geometrię za plecami, a przed sobą miał 300 m.</para>
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Gdy zasięg jest ujemny.</exception>
    public static StreamWindow Window(double chainageM, double aheadM, double behindM,
        double heading = 1.0)
    {
        if (aheadM < 0.0 || behindM < 0.0)
        {
            throw new ArgumentOutOfRangeException(nameof(aheadM),
                $"zasięg streamowania nie może być ujemny (przód {aheadM}, tył {behindM})");
        }

        return heading >= 0.0
            ? new StreamWindow(chainageM - behindM, chainageM + aheadM)
            : new StreamWindow(chainageM - aheadM, chainageM + behindM);
    }

    /// <summary>Okno z domyślnych zasięgów manifestu.</summary>
    public static StreamWindow Window(ChunkManifest manifest, double chainageM,
        double heading = 1.0)
    {
        ArgumentNullException.ThrowIfNull(manifest);
        return Window(chainageM, manifest.DefaultAheadM, manifest.DefaultBehindM, heading);
    }

    /// <summary>
    /// Chunki przecinające zakres, w kolejności chainage.
    ///
    /// <para>Przedział jest domknięty z OBU stron i to jest decyzja, nie niedopatrzenie:
    /// pociąg stojący dokładnie na szwie potrzebuje obu chunków. Nadmiarowy chunk
    /// kosztuje pamięć, brakujący — dziurę w tunelu.</para>
    /// </summary>
    public static IReadOnlyList<ChunkEntry> ChunksInRange(ChunkManifest manifest,
        double lowM, double highM)
    {
        ArgumentNullException.ThrowIfNull(manifest);

        if (highM < lowM)
        {
            (lowM, highM) = (highM, lowM);
        }

        var found = new List<ChunkEntry>();
        foreach (var chunk in manifest.Chunks)
        {
            if (chunk.StartM <= highM && chunk.EndM >= lowM)
            {
                found.Add(chunk);
            }
        }

        found.Sort(static (a, b) => a.StartM.CompareTo(b.StartM));
        return found;
    }

    /// <summary>Co musi być w pamięci dla składu na podanym chainage.</summary>
    public static IReadOnlyList<ChunkEntry> ChunksForTrain(ChunkManifest manifest,
        double chainageM, double heading = 1.0)
    {
        var window = Window(manifest, chainageM, heading);
        return ChunksInRange(manifest, window.LowM, window.HighM);
    }

    /// <summary>
    /// Trzy listy, których potrzebuje pętla klatki: co wczytać, co zostawić, co zwolnić.
    ///
    /// <para>Liczone raz, żeby pętla nie przeliczała zbiorów przy każdej klatce.
    /// <c>Free</c> jest posortowane, bo kolejność zwalniania musi być powtarzalna —
    /// inaczej dwa przebiegi tej samej trasy zwalniałyby pamięć w innej kolejności
    /// i porównanie telemetrii przestałoby cokolwiek znaczyć.</para>
    /// </summary>
    public static StreamingDelta Delta(ChunkManifest manifest, double chainageM,
        IEnumerable<string> loadedIds, double heading = 1.0)
    {
        ArgumentNullException.ThrowIfNull(loadedIds);

        var have = new HashSet<string>(loadedIds, StringComparer.Ordinal);
        var needed = ChunksForTrain(manifest, chainageM, heading);

        var load = new List<string>();
        var keep = new List<string>();
        var neededIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var chunk in needed)
        {
            neededIds.Add(chunk.Id);
            (have.Contains(chunk.Id) ? keep : load).Add(chunk.Id);
        }

        var free = new List<string>();
        foreach (var id in have)
        {
            if (!neededIds.Contains(id))
            {
                free.Add(id);
            }
        }

        free.Sort(StringComparer.Ordinal);
        return new StreamingDelta(load, keep, free);
    }

    /// <summary>
    /// Odległość po chainage od składu do chunka; zero, gdy skład jest w środku.
    /// </summary>
    public static double DistanceM(ChunkEntry chunk, double chainageM)
    {
        if (chunk.StartM <= chainageM && chainageM <= chunk.EndM)
        {
            return 0.0;
        }

        return chainageM < chunk.StartM ? chunk.StartM - chainageM : chainageM - chunk.EndM;
    }

    /// <summary>
    /// Poziom dla podanej odległości; <c>thresholds[k]</c> to dystans, od którego
    /// wolno poziom <c>k+1</c>.
    /// </summary>
    /// <remarks>
    /// Porównanie jest nieostre (<c>&gt;=</c>): dystans DOKŁADNIE równy progowi należy
    /// już do poziomu wyższego. Progi w manifeście są zaokrąglone do dziesiątej metra
    /// (158,0 i 404,4 dla L1_A), więc równość nie jest tu przypadkiem brzegowym bez
    /// pokrycia — skład zatrzymany na okrągłej wartości chainage trafia w nią dokładnie.
    /// </remarks>
    public static int LodForDistance(double distanceM, IReadOnlyList<double> thresholds)
    {
        ArgumentNullException.ThrowIfNull(thresholds);

        var level = 0;
        for (var index = 0; index < thresholds.Count; index++)
        {
            if (distanceM >= thresholds[index])
            {
                level = index + 1;
            }
        }

        return level;
    }

    /// <summary>
    /// Poziom szczegółowości dla każdego rezydentnego chunka.
    ///
    /// <para>Rezydencja bierze się z niezmienionego <see cref="ChunksForTrain"/>, więc
    /// predykat okna zostaje jedynym źródłem prawdy o tym, co jest w pamięci. Chunk,
    /// w którym stoi skład, ma odległość 0, więc zawsze wypada na poziom 0 — to
    /// niezmiennik, nie efekt uboczny: właśnie ten chunk jest oglądany z bliska i
    /// właśnie dla niego wczytana jest bryła kolizyjna.</para>
    /// </summary>
    public static IReadOnlyDictionary<string, int> LodPlan(ChunkManifest manifest,
        double chainageM, double heading = 1.0, IReadOnlyList<double>? thresholds = null)
    {
        ArgumentNullException.ThrowIfNull(manifest);

        thresholds ??= manifest.LodThresholds;
        var plan = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (var chunk in ChunksForTrain(manifest, chainageM, heading))
        {
            plan[chunk.Id] = LodForDistance(DistanceM(chunk, chainageM), thresholds);
        }

        return plan;
    }

    /// <summary>
    /// Chunki, dla których trzeba mieć wczytaną bryłę kolizyjną.
    ///
    /// <para>Kolizja jest osobnym plikiem, więc jej rezydencja jest osobną decyzją i
    /// nie zależy od tego, w jakim poziomie chunk akurat jest rysowany. Chunk pod
    /// składem ma odległość 0, więc jest w wyniku zawsze — na tym niezmienniku stoi
    /// cały sens tej listy.</para>
    /// </summary>
    public static IReadOnlyList<string> CollisionPlan(ChunkManifest manifest,
        double chainageM, double heading = 1.0, double? radiusM = null)
    {
        ArgumentNullException.ThrowIfNull(manifest);

        var radius = radiusM ?? manifest.CollisionRadiusM;
        var needed = new List<string>();
        foreach (var chunk in ChunksForTrain(manifest, chainageM, heading))
        {
            if (DistanceM(chunk, chainageM) <= radius)
            {
                needed.Add(chunk.Id);
            }
        }

        return needed;
    }

    /// <summary>Trójkąty, które trafiłyby na kartę graficzną dla danego planu poziomów.</summary>
    public static long TrianglesFor(ChunkManifest manifest,
        IReadOnlyDictionary<string, int> plan)
    {
        ArgumentNullException.ThrowIfNull(manifest);
        ArgumentNullException.ThrowIfNull(plan);

        var byId = new Dictionary<string, ChunkEntry>(StringComparer.Ordinal);
        foreach (var chunk in manifest.Chunks)
        {
            byId[chunk.Id] = chunk;
        }

        var total = 0L;
        foreach (var (id, level) in plan)
        {
            total += byId[id].Lod(level).Triangles;
        }

        return total;
    }
}
