using Godot;
using System;

namespace MetroBxl.Game.Assets;

/// <summary>
/// Wczytywanie GLB **w czasie działania**, a nie przez import do <c>res://</c>.
///
/// Powód jest zapisany w regule 8 z <c>CLAUDE.md</c>: chunki tunelu i skorupa M7 są
/// produktem generatora w <c>build/</c> i nie wchodzą do repozytorium. Import Godota
/// wymagałby, żeby leżały pod <c>res://</c> i miał obok siebie skomitowane pliki
/// <c>.import</c> — czyli żeby wygenerowana geometria stała się częścią repo.
/// <see cref="GltfDocument"/> czyta plik z dowolnej ścieżki systemu i buduje scenę
/// w pamięci, więc repo zostaje czyste, a generator pozostaje jedynym źródłem siatek.
///
/// Cena tej decyzji, żeby była powiedziana wprost: nie ma importu, więc nie ma
/// wstępnego przetworzenia siatek, a wczytanie kosztuje czas przy starcie sceny.
/// Dla 12 chunków pakietu A (867 kB, 16176 trójkątów) jest to nieistotne; dla całej
/// sieci trzeba będzie wrócić do tej decyzji.
/// </summary>
public static class GlbLoader
{
    /// <summary>
    /// Wczytuje plik GLB i zwraca korzeń zbudowanej sceny albo <c>null</c>, gdy plik
    /// nie istnieje lub nie daje się wczytać. Błąd jest logowany, nie przemilczany.
    /// </summary>
    public static Node3D? Load(string absolutePath)
    {
        if (!FileAccess.FileExists(absolutePath))
        {
            GD.PushError($"[ASSETS] brak pliku: {absolutePath}");
            return null;
        }

        var document = new GltfDocument();
        var state = new GltfState();
        var error = document.AppendFromFile(absolutePath, state);
        if (error != Error.Ok)
        {
            GD.PushError($"[ASSETS] {absolutePath}: AppendFromFile -> {error}");
            return null;
        }

        return document.GenerateScene(state) as Node3D;
    }

    /// <summary>
    /// Nadaje wszystkim siatkom poddrzewa jeden neutralny materiał. Jest to
    /// bezpieczna ścieżka dla zewnętrznych plików podanych przez argumenty.
    ///
    /// <c>docs/03-legal.md</c> jest twarde: żadnych logo, liverii, piktogramów ani
    /// wystroju STIB/MIVB. Własna proceduralna skorupa M7 zachowuje dwa neutralne
    /// materiały z generatora; pozostałe GLB dostają jednolitą szarość.
    /// </summary>
    public static int ApplyNeutralMaterial(Node node, StandardMaterial3D material)
    {
        var count = 0;
        if (node is MeshInstance3D mesh)
        {
            mesh.MaterialOverride = material;
            count++;
        }

        foreach (var child in node.GetChildren())
        {
            count += ApplyNeutralMaterial(child, material);
        }

        return count;
    }

    /// <summary>Neutralny materiał bez żadnego brandingu.</summary>
    public static StandardMaterial3D NeutralMaterial(Color albedo, float roughness) =>
        new()
        {
            AlbedoColor = albedo,
            Roughness = roughness,
            Metallic = 0.0f,
            CullMode = BaseMaterial3D.CullModeEnum.Back,
        };

    /// <summary>
    /// Neutral concrete with restrained, repeating construction joints. Tunnel
    /// UVs measure four metres per unit, so one texture tile is one short panel.
    /// The texture is generated once at startup and needs no packaged image.
    /// </summary>
    public static StandardMaterial3D TunnelConcreteMaterial()
    {
        const int size = 128;
        var image = Image.CreateEmpty(size, size, false, Image.Format.Rgba8);
        for (var y = 0; y < size; y++)
        {
            for (var x = 0; x < size; x++)
            {
                var broad = 0.025f * MathF.Sin(x * MathF.Tau / size)
                    + 0.018f * MathF.Sin(y * MathF.Tau * 2.0f / size);
                var joint = y == 0 || y == size - 1 ? -0.09f : 0.0f;
                var value = 0.97f + broad + joint;
                image.SetPixel(x, y, new Color(value, value, value, 1.0f));
            }
        }
        image.GenerateMipmaps();

        var material = NeutralMaterial(new Color(0.42f, 0.43f, 0.42f), 0.96f);
        material.AlbedoTexture = ImageTexture.CreateFromImage(image);
        material.TextureFilter = BaseMaterial3D.TextureFilterEnum.LinearWithMipmaps;
        material.TextureRepeat = true;
        return material;
    }
}
