using System;
using System.IO;

namespace MetroBxl.Tests.Shared;

/// <summary>
/// Korzeń repozytorium — JEDNO miejsce dla obu projektów testowych (6.D257).
///
/// <para><b>Dlaczego plik LINKOWANY, a nie projekt.</b> `Game.Tests` i `Sim.Tests` są
/// dwoma niezależnymi projektami i celowo: `Game.Tests` nie stoi w `MetroBxl.sln`, bo
/// rdzeń ma się budować i testować bez silnika (reguła 9 `CLAUDE.md`). Trzeci projekt
/// byłby nową zależnością obu, a linkowany plik źródłowy nie jest zależnością — wchodzi
/// do każdego z nich jako własny kod.</para>
///
/// <para><b>Marker to `MetroBxl.sln`, a nie katalog `.git`, i to jest zmierzone.</b>
/// W worktree `.git` jest PLIKIEM, nie katalogiem, więc `Directory.Exists` nie znajduje
/// korzenia nigdy — 6.D253 zmierzyło na tym SIEDEM padających testów w worktree przy
/// zerze w głównym katalogu roboczym. `.sln` jest treścią repozytorium i plikiem
/// w obu układach.</para>
///
/// <para><b>Punkt startu to `AppContext.BaseDirectory`, a nie katalog bieżący.</b>
/// Katalog bieżący zależy od tego, skąd uruchomiono runner; katalog binarki nie.</para>
///
/// <para><b>Ta klasa NIE woła `Assert`</b> — i to jest wybór, nie przeoczenie. Brak
/// korzenia nie jest niespełnionym oczekiwaniem testu, tylko niemożliwym do
/// przeprowadzenia przebiegiem: plik pomocniczy bez zależności od frameworka wchodzi
/// do obu projektów tak samo, cokolwiek który z nich kiedyś zmieni.</para>
/// </summary>
public static class KorzenRepozytorium
{
    /// <summary>Nazwa pliku, po którym poznaje się korzeń.</summary>
    public const string Marker = "MetroBxl.sln";

    private static readonly Lazy<string?> Znaleziony = new(SzukajAlboNull);

    /// <summary>Ścieżka bezwzględna do korzenia repozytorium; odmawia, gdy go nie ma.</summary>
    public static string Sciezka => Znaleziony.Value ?? throw new InvalidOperationException(
        $"nie znaleziono korzenia repozytorium: szukano pliku `{Marker}` w górę od "
        + $"`{AppContext.BaseDirectory}` i nie ma go w żadnym katalogu nadrzędnym — "
        + "przebieg stoi poza drzewem repozytorium");

    /// <summary>
    /// To samo, ale `null` zamiast odmowy — dla testów, które SAME rozstrzygają,
    /// co zrobić poza drzewem repozytorium.
    ///
    /// <para>Ta druga postać istnieje, bo trzy testy rdzenia branżują na `null`:
    /// jeden woła `Assert.IsNotNull`, drugi `Assert.Inconclusive`. Zamiana ich na
    /// odmowę byłaby ZMIANĄ ZACHOWANIA przemyconą przy sprzątaniu duplikatów —
    /// a sprzątanie duplikatów ma zostawić zachowanie takim, jakie było.</para>
    /// </summary>
    public static string? SciezkaAlboNull => Znaleziony.Value;

    /// <summary>Ścieżka do pliku w repozytorium, złożona z członów względnych.</summary>
    public static string Plik(params string[] czlony)
    {
        if (czlony is null || czlony.Length == 0)
        {
            throw new ArgumentException("brak członów ścieżki", nameof(czlony));
        }

        var wszystkie = new string[czlony.Length + 1];
        wszystkie[0] = Sciezka;
        Array.Copy(czlony, 0, wszystkie, 1, czlony.Length);
        return Path.Combine(wszystkie);
    }

    /// <summary>Treść pliku z repozytorium, złożonego z członów względnych.</summary>
    public static string Tresc(params string[] czlony) => File.ReadAllText(Plik(czlony));

    private static string? SzukajAlboNull()
    {
        var katalog = AppContext.BaseDirectory;
        while (katalog is not null && !File.Exists(Path.Combine(katalog, Marker)))
        {
            katalog = Directory.GetParent(katalog)?.FullName;
        }

        return katalog;
    }
}
