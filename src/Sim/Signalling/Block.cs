using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Signalling;

/// <summary>Stan bloku. Kolejność deklaracji idzie od najswobodniejszego do najbardziej zajętego.</summary>
public enum BlockState
{
    /// <summary>Wolny: bez składu i bez rezerwacji.</summary>
    Clear,

    /// <summary>Zarezerwowany pod zaryglowaną trasę, ale jeszcze bez składu.</summary>
    Reserved,

    /// <summary>Zajęty przez skład.</summary>
    Occupied,
}

/// <summary>Rola bloku w planie. Nie jest to typ urządzenia STIB, tylko rola w modelu.</summary>
public enum BlockKind
{
    /// <summary>Blok szlakowy między peronami.</summary>
    Interstation,

    /// <summary>Blok peronowy — obejmuje punkt zatrzymania stacji.</summary>
    Platform,
}

/// <summary>
/// Jeden blok stały: półotwarty odcinek chainage <c>[StartM, EndM)</c> na osi pakietu.
///
/// <para><b>Co jest faktem, a co modelem.</b> Faktem source-backed jest sama zasada:
/// STIB opisuje dotychczasową sygnalizację metra jako podział na duże strefy stałe
/// formowane obwodami torowymi, z co najwyżej jednym pociągiem w strefie
/// (<c>data/signalling/ground-truth.json</c>: <c>legacy_fixed_blocks</c>,
/// <c>legacy_track_circuits</c>). Modelem — i to jawnym <c>design_model</c> — są
/// <b>granice</b>: <c>unknown_parameters</c> wymienia „exact fixed-block boundaries and
/// lengths" jako rzecz niepubliczną. Ten typ nie ma więc żadnego pola, które
/// twierdziłoby, że blok odpowiada obwodowi torowemu STIB.</para>
///
/// <para><b>Półotwartość jest istotna.</b> Granica bloku należy do bloku następnego,
/// więc chainage 47,0 m przy bloku <c>[0, 47)</c> jest już w bloku kolejnym.
/// Bez tej reguły skład stojący dokładnie na granicy zajmowałby dwa bloki naraz
/// i zwalniał je w kolejności zależnej od zaokrągleń. Wyjątek jest jeden: koniec
/// ostatniego bloku planu jest domknięty, bo dalej nie ma gdzie przejść.</para>
/// </summary>
/// <param name="Id">Identyfikator bloku w planie, np. <c>P01</c> albo <c>S01</c>.</param>
/// <param name="StartM">Chainage początku, w metrach osi pakietu.</param>
/// <param name="EndM">Chainage końca.</param>
/// <param name="Kind">Rola bloku w planie.</param>
/// <param name="StationName">
/// Nazwa stacji dla bloku peronowego, dokładnie taka jak w <c>data/track/*.json</c>
/// (dwujęzyczna <c>FR|NL</c>). Pusta dla bloku szlakowego.
/// </param>
public readonly record struct Block(string Id, double StartM, double EndM, BlockKind Kind, string StationName)
{
    /// <summary>Długość bloku.</summary>
    public double LengthM => EndM - StartM;

    /// <summary>Czy blok jest peronowy.</summary>
    public bool IsPlatform => Kind == BlockKind.Platform;

    /// <summary>Czy chainage leży w bloku, przy półotwartej konwencji <c>[Start, End)</c>.</summary>
    public bool Contains(double chainageM) => chainageM >= StartM && chainageM < EndM;

    /// <summary>
    /// Czy blok przecina odcinek <c>[fromM, toM]</c>. Odcinek zdegenerowany do punktu
    /// (<c>fromM == toM</c>) jest traktowany jak <see cref="Contains"/> — inaczej skład
    /// o zerowej długości nie zajmowałby nic.
    /// </summary>
    public bool Overlaps(double fromM, double toM)
    {
        if (toM < fromM)
        {
            throw new ArgumentOutOfRangeException(
                nameof(toM), toM, "Koniec odcinka nie może leżeć przed jego początkiem.");
        }

        return toM > fromM
            ? toM > StartM && fromM < EndM
            : Contains(fromM);
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Id} [{StartM:F2}, {EndM:F2}) {LengthM:F2} m {Kind}{(StationName.Length == 0 ? string.Empty : $" — {StationName}")}");
}

/// <summary>
/// Trasa: uporządkowany zbiór bloków, które ryglują się razem.
///
/// <para><b>Minimalny interlocking, zgodnie z zasadą 5 z T-313.</b> Trasa nie zna
/// rozjazdów, nastawni, zwolnień sekcyjnych ani żadnej innej rzeczywistej logiki STIB
/// — <c>unknown_parameters</c> wymienia „station-specific route-locking/interlocking
/// logic" jako niepubliczną. Zostaje jedno, co da się modelować bez zgadywania:
/// **dwie trasy są w konflikcie wtedy i tylko wtedy, gdy dzielą blok.** Z tego wynika
/// odrzucenie żądania i nic więcej z tego nie udaje.</para>
/// </summary>
/// <param name="Id">Identyfikator trasy.</param>
/// <param name="FromBlockId">Blok początkowy — ten, w którym stoi skład przy żądaniu.</param>
/// <param name="ToBlockId">Blok docelowy — ostatni blok trasy.</param>
/// <param name="BlockIds">Wszystkie bloki trasy w kolejności chainage, włącznie ze skrajnymi.</param>
public readonly record struct Route(
    string Id,
    string FromBlockId,
    string ToBlockId,
    IReadOnlyList<string> BlockIds)
{
    /// <summary>Czy trasy dzielą choć jeden blok — jedyne kryterium konfliktu w tym modelu.</summary>
    public bool ConflictsWith(Route other)
    {
        ArgumentNullException.ThrowIfNull(other.BlockIds);
        foreach (var mine in BlockIds)
        {
            foreach (var theirs in other.BlockIds)
            {
                if (string.Equals(mine, theirs, StringComparison.Ordinal))
                {
                    return true;
                }
            }
        }

        return false;
    }

    /// <inheritdoc/>
    public override string ToString() =>
        $"{Id}: {FromBlockId} → {ToBlockId} ({string.Join(", ", BlockIds)})";
}
