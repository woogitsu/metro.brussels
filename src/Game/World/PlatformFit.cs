using System;
using System.Collections.Generic;
using Godot;

namespace MetroBxl.Game.World;

/// <summary>
/// Pomiary brył peronu — cała arytmetyka widoku stacji, bez ani jednego wywołania
/// silnika.
///
/// <para><b>Po co osobna klasa.</b> Ta sama droga, którą przeszedł
/// <see cref="TrainLayout"/> po audycie mutacyjnym z 04.09.2026: <c>Node3D</c>
/// w <c>dotnet test</c> nie powstanie, więc kod trzymany w węźle sceny nie ma jak
/// dostać testu jednostkowego i jedyną jego kontrolą zostaje zrzut ekranu. Zrzut
/// nie odróżni peronu stojącego 1000 m dalej od peronu, którego nie ma — oba dają
/// kadr pustego tunelu. <see cref="Aabb"/> i <see cref="Vector3"/> są strukturami
/// zarządzanymi z GodotSharp i działają bez uruchomionego silnika, więc pomiar
/// wchodzi tutaj w całości, a <see cref="StationView"/> zostaje cienki.</para>
///
/// <para>Pomiar jest <b>poziomy</b>, czyli z pominięciem osi Y. Płyta peronu ciągnie
/// się od główki szyny (0 m) w górę do 1,03 m, a oko maszynisty jest na 2,20 m —
/// odległość liczona w trzech wymiarach mieszałaby „peron jest gdzie indziej"
/// z „peron jest niżej niż kamera", a to drugie jest normalne.</para>
/// </summary>
public static class PlatformFit
{
    /// <summary>Actual horizontal projection of a platform mesh, rather than its
    /// axis-aligned box (which includes empty space around a curved platform).</summary>
    public readonly record struct Footprint(Aabb Bounds, IReadOnlyList<Vector3> Faces);

    /// <summary>Whether a point's horizontal projection lies on any platform
    /// triangle. Height is intentionally ignored for an eye above the slab.</summary>
    public static bool Covers(IReadOnlyList<Footprint> platforms, Vector3 point)
    {
        foreach (var platform in platforms)
        {
            if (HorizontalDistanceM(platform.Bounds, point) > 0.0)
            {
                continue;
            }

            var faces = platform.Faces;
            for (var i = 0; i + 2 < faces.Count; i += 3)
            {
                if (InTriangle(point, faces[i], faces[i + 1], faces[i + 2]))
                {
                    return true;
                }
            }
        }

        return false;
    }

    /// <summary>Choose the first camera position actually above a generated
    /// slab, or the side inspection position between stations.</summary>
    public static Vector3 CameraPosition(
        IReadOnlyList<Footprint> platforms, Vector3 right, Vector3 left, Vector3 fallback) =>
        Covers(platforms, right) ? right : Covers(platforms, left) ? left : fallback;

    private static bool InTriangle(Vector3 point, Vector3 a, Vector3 b, Vector3 c)
    {
        static double Cross(Vector3 u, Vector3 v, Vector3 w) =>
            ((v.X - u.X) * (w.Z - u.Z)) - ((v.Z - u.Z) * (w.X - u.X));

        var area = Cross(a, b, c);
        if (Math.Abs(area) < 1e-8)
        {
            return false; // Vertical faces have no horizontal area.
        }

        var first = Cross(a, b, point) / area;
        var second = Cross(b, c, point) / area;
        var third = Cross(c, a, point) / area;
        return first >= -1e-6 && second >= -1e-6 && third >= -1e-6;
    }

    /// <summary>
    /// Odległość POZIOMA punktu od prostopadłościanu; zero, gdy rzut punktu leży
    /// wewnątrz rzutu bryły.
    /// </summary>
    public static double HorizontalDistanceM(Aabb box, Vector3 point)
    {
        var lo = box.Position;
        var hi = box.End;
        var dx = Math.Max(Math.Max(lo.X - point.X, point.X - hi.X), 0.0f);
        var dz = Math.Max(Math.Max(lo.Z - point.Z, point.Z - hi.Z), 0.0f);
        return Math.Sqrt((dx * dx) + (dz * dz));
    }

    /// <summary>
    /// Indeksy brył, których rzut leży nie dalej niż <paramref name="radiusM"/>
    /// od <paramref name="point"/>. Kolejność rosnąca po indeksie, żeby dwa przebiegi
    /// tego samego przejazdu dawały tę samą listę.
    /// </summary>
    public static IReadOnlyList<int> Near(
        IReadOnlyList<Aabb> boxes, Vector3 point, double radiusM)
    {
        ArgumentNullException.ThrowIfNull(boxes);
        if (radiusM < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(radiusM), radiusM, "promień szukania nie może być ujemny");
        }

        var found = new List<int>();
        for (var index = 0; index < boxes.Count; index++)
        {
            if (HorizontalDistanceM(boxes[index], point) <= radiusM)
            {
                found.Add(index);
            }
        }

        return found;
    }

    /// <summary>
    /// Obwiednia wskazanych brył albo <c>null</c>, gdy nie wskazano żadnej.
    ///
    /// <para><c>null</c>, a nie <c>new Aabb()</c>: pusta obwiednia to prostopadłościan
    /// o zerowym rozmiarze zaczepiony w początku układu, czyli liczba, która wygląda
    /// jak pomiar i nią nie jest. Wołający ma zobaczyć różnicę między „zmierzyłem"
    /// a „nie było czego mierzyć".</para>
    /// </summary>
    public static Aabb? Merge(IReadOnlyList<Aabb> boxes, IReadOnlyList<int>? indices = null)
    {
        ArgumentNullException.ThrowIfNull(boxes);

        Aabb? merged = null;
        if (indices is null)
        {
            foreach (var box in boxes)
            {
                merged = merged is null ? box : merged.Value.Merge(box);
            }

            return merged;
        }

        foreach (var index in indices)
        {
            var box = boxes[index];
            merged = merged is null ? box : merged.Value.Merge(box);
        }

        return merged;
    }

    /// <summary>
    /// Najwyższy punkt wskazanych brył nad główką szyny albo <c>null</c>, gdy nie ma
    /// ani jednej. To jest liczba, którą bramka porównuje z wysokością podłogi M7:
    /// STIB pisze, że podłoga M7 jest „à hauteur du quai" (R-007), więc peron na
    /// innej wysokości niż podłoga jest błędem, a nie wariantem.
    /// </summary>
    public static double? TopM(IReadOnlyList<Aabb> boxes, IReadOnlyList<int>? indices = null)
    {
        var merged = Merge(boxes, indices);
        return merged?.End.Y;
    }
}
