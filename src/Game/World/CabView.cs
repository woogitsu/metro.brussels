using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;

namespace MetroBxl.Game.World;

/// <summary>
/// Wnętrze kabiny kanonicznej — bryły z <c>tools/blender/m7_cab.py</c> ustawione na osi
/// tak samo jak skorupa, ale widoczne DOKŁADNIE ODWROTNIE do niej.
///
/// <para><b>Po co osobna klasa, skoro ustawianie jest to samo.</b> Bo ustawianie JEST
/// to samo i dlatego nie jest tu powtórzone: <see cref="PlaceAt"/> przekazuje bryły
/// do <see cref="TrainLayout.PlaceWithRear"/> i NIE liczy przy tym niczego. Druga kopia
/// arytmetyki ogona rozjechałaby kabinę ze składem o kilkadziesiąt metrów i nie
/// zapaliłaby się nigdzie — pomyłka w ogonie przesuwa całość i wygląda jak decyzja.
/// Zdanie to jest PRZEPISANE, a nie dopisane obok: do 14.09.2026 stało tu, że
/// <c>PlaceAt</c> woła <c>TrainLayout.Place</c>, i było to nieprawdą od commitu, który
/// wprowadził <c>PlaceWithRear</c> — <c>Place</c> liczy ogon z rozpiętości PRZEKAZANYCH
/// brył, czyli robi dokładnie to, czego ta klasa robić nie może.
/// Własna klasa istnieje dla czegoś innego: dla POLITYKI WIDOCZNOŚCI, która jest
/// odwrotnością polityki skorupy i jest jedyną rzeczą, w której kabina różni się
/// od pudła.</para>
///
/// <para><b>Dlaczego to jest odwrotność, a nie niezależny przełącznik.</b>
/// <c>FirstRun.ApplyView</c> chowa skorupę w widoku kabinowym, bo kamera stoi w jej
/// wnętrzu i bez ukrycia widać z bliska drugą stronę ścianek. Do MB-05 nie było czego
/// pokazać w zamian — kabina jako model wnętrza nie istniała w scenie (<c>grep M7_cab</c>
/// po plikach <c>.cs</c> dawał ZERO trafień jeszcze 14.09.2026). Od tej pozycji
/// w zamian staje wnętrze, więc widoczność kabiny musi być związana z widokiem
/// TYM SAMYM warunkiem, a nie drugim, który da się przestawić osobno. Pole „Skończone,
/// gdy" pozycji MB-05 żąda tego wprost: wnętrze „nie znika razem ze skorupą ukrywaną
/// w trybie kabinowym".</para>
///
/// <para><b>Układ jest KANONICZNY i nie jest kabiną M7.</b> Zdanie to jedzie
/// w raporcie generatora obok geometrii i powtarza się tutaj, bo klasa sceny jest
/// miejscem, w którym ktoś zobaczy tę geometrię po raz pierwszy. Decyzja właściciela
/// z 10.09.2026 dotyczy układu neutralnego, nie odwzorowania prawdziwego pulpitu.</para>
/// </summary>
public sealed partial class CabView : Node3D
{
    private readonly List<ITrainBody> _bodies = new();

    /// <summary>Liczba wczytanych brył kabiny.</summary>
    public int BodyCount => _bodies.Count;

    /// <summary>Rozpiętość wczytanych brył wzdłuż osi składu.</summary>
    public double LengthM { get; private set; }

    /// <summary>Wysokość najwyższej krawędzi kabiny nad główką szyny.</summary>
    public double RoofHeightM { get; private set; }

    /// <summary>Wysokość podłogi kabiny nad główką szyny.</summary>
    public double FloorHeightM { get; private set; }

    /// <summary>Wczytuje bryły kabiny. Zwraca ich liczbę; zero znaczy „nie wczytano".</summary>
    public int Load(string cabPath, StandardMaterial3D material)
    {
        var scene = GlbLoader.Load(cabPath);
        if (scene is null)
        {
            return 0;
        }

        var minX = double.PositiveInfinity;
        var maxX = double.NegativeInfinity;
        var minY = double.PositiveInfinity;
        var maxY = double.NegativeInfinity;

        var wczytane = new List<CabBody>();
        foreach (var child in scene.GetChildren())
        {
            if (child is not MeshInstance3D mesh || mesh.Mesh is null)
            {
                continue;
            }

            var box = mesh.Mesh.GetAabb();
            minX = Math.Min(minX, box.Position.X);
            maxX = Math.Max(maxX, box.End.X);
            minY = Math.Min(minY, box.Position.Y);
            maxY = Math.Max(maxY, box.End.Y);
            wczytane.Add(new CabBody(mesh, new BodySpan(box.Position.X, box.End.X)));
        }

        foreach (var body in wczytane)
        {
            // Właściciela zdejmuje się PRZED przepięciem — inaczej Godot ostrzega
            // o niespójnym `owner`, bo węzeł nadal należałby do sceny, której już nie ma.
            // Ta sama kolejność i ten sam powód co w `TrainView.Load`.
            body.Node.Owner = null;
            scene.RemoveChild(body.Node);
            AddChild(body.Node);
            _bodies.Add(body);
        }

        scene.QueueFree();

        if (_bodies.Count == 0)
        {
            return 0;
        }

        LengthM = maxX - minX;
        RoofHeightM = maxY;
        FloorHeightM = minY;

        GlbLoader.ApplyNeutralMaterial(this, material);
        return _bodies.Count;
    }

    /// <summary>
    /// Ustawia bryły kabiny dla składu, którego OGON stoi w <paramref name="rearChainageM"/>.
    ///
    /// <para><b>Ogon, a nie czoło, i nie liczony tutaj — to jest cała treść tej
    /// sygnatury.</b> Zakresy X brył kabiny są wyrażone w tym samym układzie co zakresy
    /// skorupy, ale kabina NIE jest całym składem: zaczyna się 0,35 m za czołem
    /// i kończy 0,35 m przed ogonem, więc jej własna rozpiętość to 93,300 m przy
    /// składzie 94,000 m. Zbiór brył, który nie jest całym składem, nie umie sam
    /// odpowiedzieć, gdzie skład się kończy.</para>
    ///
    /// <para>Zmierzone, zanim ta sygnatura wyglądała tak jak dziś: przy liczeniu ogona
    /// z rozpiętości WŁASNEJ szyba czołowa lądowała <b>0,700 m za daleko</b> — 0,35 m
    /// PRZED czołem pudła zamiast 0,35 m za nim.</para>
    ///
    /// <para><b>Zdanie o oku jest PRZEPISANE, a nie dopisane obok</b> (audyt
    /// 14.09.2026). Poprzednia wersja mówiła, że oko maszynisty zostawało wtedy ZA
    /// szybą, a nie przed nią, i że dlatego w kadrze nie było ramy szyby — oba człony są
    /// nieprawdziwe. Usterka przesuwa BRYŁY KABINY, a nie kamerę: oko liczy
    /// <c>FirstRun.PlaceEverything</c> z kilometrażu czoła i
    /// <see cref="DesignAssumptions.CabEyeSetbackM"/> = 1,80 m, więc przy czole
    /// na 2000,000 m stoi na 1998,200 m w OBU przypadkach. Oko jest po TEJ SAMEJ stronie
    /// płaszczyzny szyby przed poprawką i po niej — zmienia się odległość: −1,450 m
    /// poprawnie, −2,150 m z usterką. Ramy szyby nie ma zaś w kadrze nigdy, bo nie
    /// niesie jej żadna z szesnastu brył (podłoga, trzy części grodzi, pudło pulpitu,
    /// blat, siedzisko, oparcie — po osiem na koniec).</para>
    ///
    /// <para>Co usterka NAPRAWDĘ robiła, widać na fotelu i na pulpicie: oko wypadało
    /// ZA OPARCIEM zamiast nad siedziskiem — poprawnie siedzisko zajmuje
    /// 1998,100–1998,550 m i obejmuje oko, z usterką stoi na 1998,800–1999,250 m,
    /// a oparcie na 1998,700–1998,800 m — a pulpit odsuwał się z 0,70 m na 1,40 m przed
    /// okiem. Żadna z tych dwóch klatek nie wygląda na błędną i to jest powód, dla
    /// którego pomyłkę znalazł RACHUNEK z raportu generatora, a nie obejrzenie
    /// kadru.</para>
    /// </summary>
    public void PlaceAt(SceneAxis axis, double rearChainageM) =>
        TrainLayout.PlaceWithRear(axis, _bodies, rearChainageM);

    /// <summary>Jedna linia do logu przejazdu.</summary>
    public string Describe() => string.Create(
        CultureInfo.InvariantCulture,
        $"[KABINA] brył={BodyCount} rozpiętość={LengthM:F3} m podłoga={FloorHeightM:F3} m "
        + $"strop={RoofHeightM:F3} m nad główką szyny; UKŁAD KANONICZNY, nie kabina M7");

    /// <summary>Węzeł sceny jako <see cref="ITrainBody"/> — ta sama granica co w <c>TrainView</c>.</summary>
    private sealed class CabBody : ITrainBody
    {
        internal CabBody(Node3D node, BodySpan span)
        {
            Node = node;
            Span = span;
        }

        internal Node3D Node { get; }

        public BodySpan Span { get; }

        public bool Visible
        {
            get => Node.Visible;
            set => Node.Visible = value;
        }

        public Transform3D Transform
        {
            get => Node.Transform;
            set => Node.Transform = value;
        }
    }
}
