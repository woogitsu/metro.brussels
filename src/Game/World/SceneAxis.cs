using System;
using Godot;
using MetroBxl.Sim.Line;

namespace MetroBxl.Game.World;

/// <summary>Ramka toru: położenie i trzy osie, wszystko w układzie sceny Godota.</summary>
/// <param name="Origin">Punkt na osi toru (główka szyny).</param>
/// <param name="Forward">Kierunek jazdy.</param>
/// <param name="Right">Prawa strona względem kierunku jazdy.</param>
/// <param name="Up">Pion.</param>
public readonly record struct TrackFrame(Vector3 Origin, Vector3 Forward, Vector3 Right, Vector3 Up);

/// <summary>
/// Most między osią z rdzenia a układem sceny.
///
/// Rdzeń liczy w układzie danych: X na wschód, Y na północ, Z w górę — tak jak
/// <c>data/track/*.json</c> i tak jak Blender (<c>docs/04-conventions.md</c>).
/// Godot ma Y w górę i −Z do przodu, a eksporter glTF przeliczył geometrię tunelu
/// i skorupy M7 przy zapisie. Ta klasa robi **tę samą** zamianę dla osi, więc skład
/// ląduje w tunelu, a nie obok niego. Jedno miejsce, jedna zamiana.
///
/// Ustawienie członów jest portem <c>tools/blender/placement.py: place_spans</c>:
/// każde pudło stoi na własnej cięciwie, bo M7 jest składem przegubowym i na łuku
/// nie jest jedną bryłą.
/// </summary>
public sealed class SceneAxis
{
    private readonly TrackAxis _axis;
    private readonly double _trackOffsetM;

    /// <summary>Most nad zadaną osią, z przesunięciem na oś toru.</summary>
    public SceneAxis(TrackAxis axis, double trackOffsetM)
    {
        ArgumentNullException.ThrowIfNull(axis);
        _axis = axis;
        _trackOffsetM = trackOffsetM;
    }

    /// <summary>Oś z rdzenia.</summary>
    public TrackAxis Axis => _axis;

    /// <summary>Przesunięcie osi toru względem osi trasy.</summary>
    public double TrackOffsetM => _trackOffsetM;

    /// <summary>Punkt danych (X wschód, Y północ, Z w górę) na punkt sceny (Y w górę).</summary>
    public static Vector3 ToScene(AxisPoint point) =>
        new((float)point.X, (float)point.Z, (float)-point.Y);

    /// <summary>Punkt osi **trasy** w scenie, bez przesunięcia na tor.</summary>
    public Vector3 CentreLinePoint(double chainageM) => ToScene(_axis.PointAt(chainageM));

    /// <summary>Pozycja oprawy wzdłuż osi jazdy lub rzeczywistej osi scenerii za nią.</summary>
    public Vector3? FixturePoint(double chainageM, SceneAxis? continuation,
        double lateralM, double heightM)
    {
        if (chainageM < 0.0)
            return null;
        var axis = this;
        var at = chainageM;
        if (chainageM > _axis.LengthM)
        {
            if (continuation is null)
                return null;
            axis = continuation;
            at -= _axis.LengthM;
        }
        if (at > axis._axis.LengthM)
            return null;
        var frame = axis.Chord(Math.Max(0.0, at - 0.5),
            Math.Min(axis._axis.LengthM, at + 0.5));
        return axis.CentreLinePoint(at) + frame.Right * (float)lateralM
            + frame.Up * (float)heightM;
    }

    /// <summary>
    /// Ramka toru dla cięciwy od <paramref name="fromChainageM"/> do
    /// <paramref name="toChainageM"/>. Cięciwa, a nie styczna, bo na niej stoi pudło.
    /// </summary>
    public TrackFrame Chord(double fromChainageM, double toChainageM)
    {
        var head = CentreLinePoint(fromChainageM);
        var tail = CentreLinePoint(toChainageM);
        var chord = tail - head;
        if (chord.LengthSquared() < 1e-12f)
        {
            throw new InvalidOperationException(
                $"zerowa cięciwa między {fromChainageM} m a {toChainageM} m");
        }

        var forward = chord.Normalized();
        var right = forward.Cross(Vector3.Up);
        if (right.LengthSquared() < 1e-12f)
        {
            right = Vector3.Right;
        }

        right = right.Normalized();
        var up = right.Cross(forward).Normalized();
        var centre = ((head + tail) * 0.5f) + (right * (float)_trackOffsetM);
        return new TrackFrame(centre, forward, right, up);
    }

    /// <summary>
    /// Transformacja bryły pojazdu, której lokalny zakres X to
    /// <paramref name="localFromM"/>..<paramref name="localToM"/>, a ogon składu stoi
    /// w chainage <paramref name="rearChainageM"/>.
    ///
    /// Kolumny bazy odpowiadają osiom pojazdu po konwersji glTF: lokalne +X biegnie
    /// wzdłuż składu, +Y jest pionem, +Z jest stroną. Dokładnie ta sama zamiana, co
    /// w <see cref="ToScene"/>.
    /// </summary>
    public Transform3D BodyTransform(double rearChainageM, double localFromM, double localToM) =>
        BodyTransform(
            rearChainageM + localFromM, rearChainageM + localToM, localFromM, localToM);

    /// <summary>
    /// Transformacja bryły z gotowej decyzji <see cref="TrainLayout"/>. Cięciwa jest
    /// wzięta z planu, a nie liczona tu po raz drugi: plan jest jedynym miejscem, w
    /// którym kilometraż ogona spotyka się z lokalnym zakresem bryły.
    /// </summary>
    public Transform3D BodyTransform(BodyPlacement placement) =>
        BodyTransform(
            placement.FromChainageM,
            placement.ToChainageM,
            placement.Span.FromM,
            placement.Span.ToM);

    private Transform3D BodyTransform(
        double fromChainageM, double toChainageM, double localFromM, double localToM)
    {
        var frame = Chord(fromChainageM, toChainageM);
        var basis = new Basis(frame.Forward, frame.Up, frame.Right);
        var centreLocalX = (float)(0.5 * (localFromM + localToM));
        var origin = frame.Origin - (basis * new Vector3(centreLocalX, 0.0f, 0.0f));
        return new Transform3D(basis, origin);
    }

    /// <summary>
    /// Punkt w kabinie: <paramref name="chainageM"/> jest chainage czoła składu,
    /// a punkt leży o <paramref name="setbackM"/> za czołem, <paramref name="heightM"/>
    /// nad główką szyny i <paramref name="lateralM"/> od osi pudła.
    /// </summary>
    public (Vector3 Position, Vector3 Forward) CabPoint(
        double chainageM, double setbackM, double heightM, double lateralM)
    {
        // Kilometraż kamery przycinamy do osi PRZED oknem cięciwy, nie po nim.
        // Przy przejeździe rozpoczętym na pierwszej stacji (kilometraż 0) oko maszynisty
        // wypada na −1,8 m, a okno [−2,8; −0,8] leży całe przed początkiem osi: oba końce
        // przycinały się wtedy do tego samego punktu i cięciwa wychodziła zerowa.
        // Kamera przed początkiem osi patrzy więc wzdłuż PIERWSZEJ cięciwy osi — innej
        // prawdy o kierunku w tym miejscu nie ma, a zmyślona byłaby gorsza od przyciętej.
        // Błąd położenia to najwyżej odsunięcie oka (1,8 m) i zeruje się, gdy czoło
        // minie ten dystans.
        var at = Math.Clamp(chainageM - setbackM, 0.0, _axis.LengthM);
        var frame = Chord(Math.Max(0.0, at - 1.0), Math.Min(_axis.LengthM, at + 1.0));
        var position = frame.Origin + (frame.Up * (float)heightM) + (frame.Right * (float)lateralM);
        return (position, frame.Forward);
    }

    /// <summary>
    /// Wygładzona pozycja oka dla animowanego widoku kabiny. Oś i ustawienie pudeł
    /// pozostają bez zmian; filtr rozkłada załamania kierunku z 5-metrowych odcinków
    /// osi na kilka klatek jazdy. Próbki są symetryczne, więc nie dodają opóźnienia.
    /// </summary>
    public (Vector3 Position, Vector3 Forward) SmoothCabPoint(
        double chainageM, double setbackM, double heightM, double lateralM)
    {
        var at = Math.Clamp(chainageM - setbackM, 0.0, _axis.LengthM);
        if (at == 0.0 || at == _axis.LengthM)
        {
            // CabPoint stawia oko w środku metrowej cięciwy. Na końcu osi
            // przełączenie z wygładzonej osi cofałoby je więc o pół metra.
            // Zachowaj dokładny kierunek z CabPoint, ale pozycję zakotwicz
            // w punkcie końcowym osi.
            var frame = at == 0.0
                ? Chord(0.0, Math.Min(_axis.LengthM, 1.0))
                : Chord(Math.Max(0.0, _axis.LengthM - 1.0), _axis.LengthM);
            var endPosition = CentreLinePoint(at)
                + frame.Right * (float)(_trackOffsetM + lateralM)
                + frame.Up * (float)heightM;
            return (endPosition, frame.Forward);
        }

        var centre = SmoothCentreLinePoint(at);
        var before = SmoothCentreLinePoint(Math.Max(0.0, at - 1.5));
        var after = SmoothCentreLinePoint(Math.Min(_axis.LengthM, at + 1.5));
        var forward = (after - before).Normalized();
        var right = forward.Cross(Vector3.Up).Normalized();
        var up = right.Cross(forward).Normalized();
        var position = centre + right * (float)(_trackOffsetM + lateralM) + up * (float)heightM;
        return (position, forward);
    }

    private Vector3 SmoothCentreLinePoint(double at)
    {
        // Dwumianowy filtr [1, 6, 15, 20, 15, 6, 1] / 64.
        // Promień 9 m obejmuje kilka pierścieni tunelu, ale na łukach linii A
        // odchyla oko od osi tylko nieznacznie.
        ReadOnlySpan<int> weights = [1, 6, 15, 20, 15, 6, 1];
        var sum = Vector3.Zero;
        for (var i = 0; i < weights.Length; i++)
        {
            sum += CentreLinePoint(Math.Clamp(at + (i - 3) * 3.0, 0.0, _axis.LengthM)) * weights[i];
        }

        var smoothed = sum / 64.0f;
        // Przy końcach próbki po jednej stronie są przycięte do tego samego punktu.
        // Średnia przesuwałaby oko o 1,4 m w głąb trasy. Wygaszamy filtr płynnie
        // przez jego 9-metrowy promień, zachowując dokładne końce osi.
        var distanceFromEnd = Math.Min(at, _axis.LengthM - at);
        var blend = (float)Math.Clamp(distanceFromEnd / 9.0, 0.0, 1.0);
        blend = blend * blend * (3.0f - 2.0f * blend);
        return CentreLinePoint(at).Lerp(smoothed, blend);
    }
}
