using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace MetroBxl.Sim.Line;

/// <summary>Stacja na trasie linii, z kilometrażem liczonym od początku TRASY, nie pakietu.</summary>
public readonly record struct RouteStation(
    string Name, double ChainageM, string StopId, string AxisId);

/// <summary>
/// Odcinek między pakietami: znana długość i czas jazdy, ale BEZ geometrii.
/// </summary>
/// <remarks>
/// Takie odcinki istnieją, bo `data/track/` pokrywa pakiety, a nie całe linie.
/// Dla linii 1 jest dokładnie jeden: Merode → Montgomery.
///
/// **Obie liczby są ZMIERZONE, żadna nie jest założeniem.** Długość pochodzi z łamanej
/// źródłowej STIB `ACTU_LIGNES_BRUTES` (`reports/packages-BF-alignment.md` §8), czas
/// jazdy z rozkładu GTFS (`build/timetable.json`, mediana z segmentów T-113).
///
/// Uwaga na cięciwę: `reports/network-chainage.md` podaje dla tej pary 703,0 m, ale to
/// odległość w linii prostej, czyli DOLNE OGRANICZENIE. Długość toru to 708,9 m.
/// </remarks>
public readonly record struct RouteGap(
    string FromStation, string ToStation, double LengthM, double MedianRunSeconds);

/// <summary>
/// Trasa linii złożona z osi pakietów i odcinków międzypakietowych.
/// </summary>
/// <remarks>
/// <para><b>Po co.</b> `TrackAxis` opisuje JEDEN pakiet, a rozkład z T-113 opisuje całe
/// linie. Bez tej klasy nie da się porównać niczego, co liczy rdzeń, ze zmierzonym
/// rozkładem — `reports/network-chainage.md` mówi wprost: „nie ma czegoś takiego jak
/// kilometraż linii 1".</para>
/// <para><b>Czego ta klasa NIE udaje.</b> Odcinek międzypakietowy nie ma geometrii —
/// nie ma go w `data/track/`. <see cref="PointAt"/> odmawia więc podania punktu wewnątrz
/// przerwy, zamiast interpolować między krańcami dwóch pakietów. Interpolacja dałaby
/// prostą tam, gdzie tor skręca, i wyglądałaby dokładnie tak samo jak prawdziwa
/// geometria. Rdzeń symulacji tego punktu nie potrzebuje, bo prowadzi składy po
/// kilometrażu; potrzebuje go dopiero scena, i tam ta przerwa ma zostać widoczna.</para>
/// </remarks>
public sealed class LineRoute
{
    private readonly IReadOnlyList<TrackAxis> _axes;
    private readonly IReadOnlyList<RouteGap> _gaps;
    private readonly double[] _axisStartM;
    private readonly RouteStation[] _stations;

    /// <summary>
    /// Trasa z <paramref name="axes"/> osi i <paramref name="gaps"/> przerw między nimi.
    /// Przerw musi być dokładnie o jedną mniej niż osi.
    /// </summary>
    public LineRoute(string id, IReadOnlyList<TrackAxis> axes, IReadOnlyList<RouteGap> gaps)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentNullException.ThrowIfNull(axes);
        ArgumentNullException.ThrowIfNull(gaps);
        if (axes.Count == 0)
        {
            throw new ArgumentOutOfRangeException(nameof(axes), axes.Count,
                "Trasa bez ani jednej osi nie jest trasą.");
        }

        if (gaps.Count != axes.Count - 1)
        {
            throw new ArgumentOutOfRangeException(nameof(gaps), gaps.Count,
                $"Osi jest {axes.Count}, więc przerw ma być {axes.Count - 1}, a nie {gaps.Count}. "
                + "Sklejenie dwóch pakietów bez przerwy skróciłoby linię o brakujący odcinek.");
        }

        foreach (var gap in gaps)
        {
            if (!(gap.LengthM > 0.0) || !double.IsFinite(gap.LengthM))
            {
                throw new ArgumentOutOfRangeException(nameof(gaps), gap.LengthM,
                    $"Przerwa {gap.FromStation} → {gap.ToStation} ma nierealną długość.");
            }
        }

        Id = id;
        _axes = axes;
        _gaps = gaps;

        _axisStartM = new double[axes.Count];
        var cursor = 0.0;
        var stations = new List<RouteStation>();
        for (var i = 0; i < axes.Count; i++)
        {
            _axisStartM[i] = cursor;
            foreach (var station in axes[i].Stations)
            {
                stations.Add(new RouteStation(
                    station.Name, cursor + station.ChainageM, station.StopId, axes[i].Id));
            }

            cursor += axes[i].LengthM;
            if (i < gaps.Count)
            {
                cursor += gaps[i].LengthM;
            }
        }

        LengthM = cursor;
        _stations = stations.ToArray();
    }

    /// <summary>Identyfikator trasy, np. <c>L1</c>.</summary>
    public string Id { get; }

    /// <summary>Długość całej trasy: osie plus przerwy.</summary>
    public double LengthM { get; }

    /// <summary>Osie pakietów w kolejności jazdy.</summary>
    public IReadOnlyList<TrackAxis> Axes => _axes;

    /// <summary>Odcinki międzypakietowe, po jednym między kolejnymi osiami.</summary>
    public IReadOnlyList<RouteGap> Gaps => _gaps;

    /// <summary>Wszystkie stacje trasy, w kilometrażu trasy, w kolejności jazdy.</summary>
    public IReadOnlyList<RouteStation> Stations => _stations;

    /// <summary>Suma długości samych osi, bez przerw — do kontroli krzyżowej.</summary>
    public double AxisLengthM => _axes.Sum(a => a.LengthM);

    /// <summary>Suma długości przerw — do kontroli krzyżowej.</summary>
    public double GapLengthM => _gaps.Sum(g => g.LengthM);

    /// <summary>Czy podany kilometraż trasy wypada wewnątrz odcinka bez geometrii.</summary>
    public bool IsInGap(double chainageM) => AxisIndexAt(chainageM) < 0;

    /// <summary>
    /// Punkt trasy w układzie danych. Odmawia wewnątrz przerwy — patrz uwaga w klasie.
    /// </summary>
    public AxisPoint PointAt(double chainageM)
    {
        var index = AxisIndexAt(chainageM);
        if (index < 0)
        {
            var gap = GapAt(chainageM);
            throw new InvalidOperationException(
                $"Kilometraż {chainageM:F1} m trasy {Id} wypada w odcinku "
                + $"{gap.FromStation} → {gap.ToStation}, który nie ma geometrii w data/track/. "
                + "Długość i czas jazdy tego odcinka są zmierzone, ale przebieg toru nie — "
                + "interpolacja dałaby prostą tam, gdzie tor skręca.");
        }

        return _axes[index].PointAt(chainageM - _axisStartM[index]);
    }

    /// <summary>Indeks osi pokrywającej kilometraż, albo −1 wewnątrz przerwy.</summary>
    public int AxisIndexAt(double chainageM)
    {
        for (var i = 0; i < _axes.Count; i++)
        {
            var start = _axisStartM[i];
            if (chainageM >= start && chainageM <= start + _axes[i].LengthM)
            {
                return i;
            }
        }

        return -1;
    }

    /// <summary>Kilometraż, na którym zaczyna się oś o podanym indeksie.</summary>
    public double AxisStartM(int index) => _axisStartM[index];

    private RouteGap GapAt(double chainageM)
    {
        for (var i = 0; i < _gaps.Count; i++)
        {
            var start = _axisStartM[i] + _axes[i].LengthM;
            if (chainageM > start && chainageM < start + _gaps[i].LengthM)
            {
                return _gaps[i];
            }
        }

        throw new ArgumentOutOfRangeException(nameof(chainageM), chainageM,
            $"Kilometraż poza trasą {Id} (0 … {LengthM:F1} m).");
    }

    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"LineRoute({Id}: {_axes.Count} osi + {_gaps.Count} przerw, {LengthM:F1} m, {_stations.Length} stacji)");
}
