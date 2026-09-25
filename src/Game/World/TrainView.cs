using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;
using MetroBxl.Sim.Line;

namespace MetroBxl.Game.World;

/// <summary>Lokalny zakres X jednej bryły składu, tak jak go niesie jej AABB.</summary>
/// <param name="FromM">Koniec bliższy ogonowi składu.</param>
/// <param name="ToM">Koniec bliższy czołu składu.</param>
public readonly record struct BodySpan(double FromM, double ToM);

/// <summary>
/// Decyzja o jednej bryle: gdzie na osi leży jej cięciwa i czy wolno ją postawić.
/// </summary>
/// <param name="Index">Pozycja bryły w liście widoku.</param>
/// <param name="Span">Lokalny zakres X bryły — potrzebny do policzenia jej środka.</param>
/// <param name="FromChainageM">Chainage końca <c>Span.FromM</c>.</param>
/// <param name="ToChainageM">Chainage końca <c>Span.ToM</c>.</param>
/// <param name="Visible">Czy oś pokrywa tę cięciwę, czyli czy bryłę wolno postawić.</param>
public readonly record struct BodyPlacement(
    int Index,
    BodySpan Span,
    double FromChainageM,
    double ToChainageM,
    bool Visible);

/// <summary>
/// Bryła, którą widok składu ustawia: w scenie <c>Node3D</c>, w teście atrapa.
///
/// <para><b>Po co ten interfejs istnieje.</b> <c>dotnet test</c> nie jest silnikiem,
/// więc <c>Node3D</c> w teście nie powstanie, a <c>TrainView.PlaceAt</c> nie miał do
/// 04.09.2026 ani jednego testu — mutacja <c>Visible = covered</c> → <c>= true</c>
/// przeżyła przegląd przy #212. Interfejs przenosi całą pętlę ustawiania do kodu, który
/// da się zawołać bez silnika; po stronie sceny zostaje tylko przekazanie dwóch
/// właściwości do węzła (<c>TrainView.NodeBody</c>). To ta sama droga, którą repozytorium
/// przeszło dla modułów <c>bpy</c>: decyzja w czystym kodzie, wywołanie silnika cienkie
/// jak tylko da się je zrobić.</para>
/// </summary>
public interface ITrainBody
{
    /// <summary>Lokalny zakres X bryły.</summary>
    BodySpan Span { get; }

    /// <summary>Widoczność bryły w scenie.</summary>
    bool Visible { get; set; }

    /// <summary>Transformacja bryły w scenie.</summary>
    Transform3D Transform { get; set; }
}

/// <summary>
/// Rozkład brył składu na osi — cała decyzja o widoczności i o transformacie,
/// bez ani jednego wywołania silnika.
///
/// <para><c>TrackAxis.CoversChord</c> odpowiada na pytanie o JEDNĄ cięciwę i jest
/// przetestowany w <c>tests/Sim.Tests</c>. Brakowało strony wywołania: przy zadanym
/// kilometrażu czoła to tutaj powstaje lista decyzji dla wszystkich jedenastu brył M7,
/// razem z arytmetyką ogona. Ogon jest częścią decyzji, nie szczegółem pętli — pomyłka
/// w nim przesuwa cały skład o 94 m i nie zapala się nigdzie indziej.</para>
/// </summary>
public static class TrainLayout
{
    /// <summary>
    /// Długość składu jako rozpiętość zakresów brył. Liczona z geometrii, nie z 94,0 m
    /// wpisanych w kod: przy zmianie podziału członów nie ma tu czego poprawiać.
    /// </summary>
    public static double LengthM(IReadOnlyList<ITrainBody> bodies)
    {
        ArgumentNullException.ThrowIfNull(bodies);
        if (bodies.Count == 0)
        {
            return 0.0;
        }

        var min = double.PositiveInfinity;
        var max = double.NegativeInfinity;
        foreach (var body in bodies)
        {
            min = Math.Min(min, body.Span.FromM);
            max = Math.Max(max, body.Span.ToM);
        }

        return max - min;
    }

    /// <summary>Chainage ogona składu, którego czoło stoi w <paramref name="frontChainageM"/>.</summary>
    public static double RearChainageM(IReadOnlyList<ITrainBody> bodies, double frontChainageM) =>
        frontChainageM - LengthM(bodies);

    /// <summary>
    /// Ogon SKŁADU o zmierzonej długości <paramref name="trainLengthM"/>, którego czoło
    /// stoi w <paramref name="frontChainageM"/>.
    ///
    /// <para><b>Po co osobno od <see cref="RearChainageM"/> — i to jest cała treść tej
    /// metody.</b> Tamta bierze BRYŁY i liczy ich rozpiętość sama, więc podanie jej brył
    /// kabiny jest wywołaniem poprawnym składniowo i błędnym co do treści: rozpiętość
    /// kabiny to 93,300 m przy składzie 94,000 m, a wynik wychodzi wtedy 0,700 m za
    /// daleko. Dokładnie to wywołanie stało w scenie przed MB-05 i nie zapaliło niczego.
    /// Ta bierze LICZBĘ, więc sprawdzić jej nie ma jak — i nie udaje, że sprawdza. Jej
    /// treścią jest to, że odejmowanie ogona stoi w JEDNYM miejscu, przybitym liczbowo
    /// w <c>tests/Game.Tests/CabPlacementTests.cs</c>, a nie w wyrażeniu wpisanym
    /// w argument wywołania — bo wyrażenia w argumencie nie widzi żaden test, a jego
    /// mutacja (<c>chainage - trainLength + 0.7</c>) przechodziła 292/292.</para>
    ///
    /// <para><b>Zera nie odrzuca i to jest decyzja, nie przeoczenie.</b> Sprawdzone
    /// w <c>FirstRun</c>: przy <c>--no-geometry</c> skorupa nie jest wczytywana wcale,
    /// a <c>PlaceEverything</c> leci mimo to, więc <see cref="TrainView.LengthM"/> jest
    /// wtedy zerem. Rzut byłby awarią trybu, który ma działać bez geometrii — i byłby
    /// to CICHY ODWRÓT tej samej rodziny co usunięty stąd fallback na 94,0 m, tylko
    /// w drugą stronę.</para>
    /// </summary>
    public static double RearOfTrain(double frontChainageM, double trainLengthM) =>
        frontChainageM - trainLengthM;

    /// <summary>Decyzja o jednej bryle: jej cięciwa na osi i to, czy oś ją pokrywa.</summary>
    public static BodyPlacement PlacementFor(
        TrackAxis axis, BodySpan span, double rearChainageM, int index)
    {
        ArgumentNullException.ThrowIfNull(axis);

        // Bryła leżąca CAŁA poza osią zostaje UKRYTA, a nie postawiona gdziekolwiek.
        // Przy przejeździe rozpoczętym na pierwszej stacji (kilometraż 0) cały skład
        // leży 94 m przed początkiem osi; `TrackAxis.PointAt` przycina kilometraż, więc
        // oba końce takiej cięciwy dają ten sam punkt i ramki nie da się zbudować.
        // Ukrycie jest jedyną odpowiedzią, która nie zmyśla geometrii: osi tam po prostu
        // nie ma. Bryła wjeżdża na oś i pojawia się sama.
        var from = rearChainageM + span.FromM;
        var to = rearChainageM + span.ToM;
        return new BodyPlacement(index, span, from, to, axis.CoversChord(from, to));
    }

    /// <summary>
    /// Lista decyzji dla całego składu, którego czoło stoi w <paramref name="frontChainageM"/>.
    /// Kolejność odpowiada kolejności brył w liście.
    /// </summary>
    public static IReadOnlyList<BodyPlacement> Plan(
        TrackAxis axis, IReadOnlyList<ITrainBody> bodies, double frontChainageM)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(bodies);

        var rear = RearChainageM(bodies, frontChainageM);
        var plan = new List<BodyPlacement>(bodies.Count);
        for (var index = 0; index < bodies.Count; index++)
        {
            plan.Add(PlacementFor(axis, bodies[index].Span, rear, index));
        }

        return plan;
    }

    /// <summary>Liczba brył, których oś nie pokrywa — czyli tych ukrytych.</summary>
    public static int HiddenCount(IReadOnlyList<BodyPlacement> plan)
    {
        ArgumentNullException.ThrowIfNull(plan);

        var hidden = 0;
        foreach (var placement in plan)
        {
            if (!placement.Visible)
            {
                hidden++;
            }
        }

        return hidden;
    }

    /// <summary>
    /// Wykonuje gotowy plan: ustawia widoczność każdej bryły, a transformację **tylko**
    /// tym, które oś pokrywa. Bryła ukryta nie dostaje żadnej transformacji, bo nie ma
    /// jej z czego policzyć — <c>SceneAxis.Chord</c> rzuciłby na zerowej cięciwie.
    /// </summary>
    public static void Apply(
        SceneAxis axis, IReadOnlyList<ITrainBody> bodies, IReadOnlyList<BodyPlacement> plan)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(bodies);
        ArgumentNullException.ThrowIfNull(plan);
        if (plan.Count != bodies.Count)
        {
            throw new ArgumentException(
                $"plan ma {plan.Count} pozycji, a skład {bodies.Count} brył", nameof(plan));
        }

        for (var index = 0; index < bodies.Count; index++)
        {
            var placement = plan[index];
            bodies[index].Visible = placement.Visible;
            if (placement.Visible)
            {
                bodies[index].Transform = axis.BodyTransform(placement);
            }
        }
    }

    /// <summary>
    /// Plan i jego wykonanie dla zbioru brył, którego OGON JEST ZADANY Z ZEWNĄTRZ.
    ///
    /// <para><b>Po co to istnieje i co bez tego wychodzi — zmierzone przy MB-05.</b>
    /// <see cref="Place(SceneAxis, IReadOnlyList{ITrainBody}, double)"/> liczy ogon jako
    /// <c>czoło − LengthM(bryły)</c>, czyli z ROZPIĘTOŚCI SAMEGO ZBIORU. Dla skorupy jest
    /// to poprawne, bo skorupa JEST składem: jej rozpiętość to 94,000 m. Dla kabiny już
    /// nie — bryły kabiny mają wspólny układ współrzędnych ze skorupą (oba generatory
    /// wychodzą z <c>m7_layout.py</c>), ale rozpiętość WŁASNĄ 93,300 m, bo kabina zaczyna
    /// się 0,35 m za czołem i kończy 0,35 m przed ogonem.</para>
    ///
    /// <para>Skutek liczbowy, policzony wprost: przy czole na 2000,000 m szyba czołowa
    /// lądowała na <b>2000,350 m</b>, czyli <b>0,35 m PRZED czołem składu</b>, zamiast na
    /// 1999,650 m — <b>0,700 m za daleko</b>. Kabina wystawała przodem przez czoło pudła,
    /// a oko maszynisty — 1998,200 m, czyli 1,80 m za czołem, liczone z kilometrażu czoła
    /// i NIEZALEŻNE od położenia kabiny — wypadało za oparciem fotela zamiast nad
    /// siedziskiem: poprawnie siedzisko zajmuje 1998,100–1998,550 m i obejmuje oko,
    /// z usterką stoi na 1998,800–1999,250 m, a oparcie na 1998,700–1998,800 m. Pulpit
    /// odsuwał się przy tym z 0,70 m na 1,40 m przed okiem. Żadna bramka liczbowa tego
    /// nie widziała: obie liczby są poprawnymi rozpiętościami swoich zbiorów.</para>
    ///
    /// <para><b>Ten akapit jest PRZEPISANY, a nie dopisany obok</b> (audyt 14.09.2026).
    /// Poprzednia wersja mówiła, że oko „zostawało za szybą zamiast przed nią" i że
    /// „w kadrze nie było więc ramy szyby w ogóle". Pierwsze jest nieprawdą: oko stoi
    /// na 1998,200 m w obu przypadkach i po tej samej stronie płaszczyzny szyby, tylko
    /// dalej od niej (−1,450 m poprawnie, −2,150 m z usterką). Drugie jest nieprawdziwym
    /// związkiem przyczynowym: ramy szyby nie ma w kadrze ani przed poprawką, ani po
    /// niej, bo nie niesie jej żadna bryła kabiny — przesunięcie o 0,700 m nie mogło
    /// tego wywołać ani odwołać.</para>
    ///
    /// <para>Dlatego ogon jest tu ARGUMENTEM, a nie wynikiem: zbiór brył, który nie jest
    /// całym składem, nie umie sam odpowiedzieć, gdzie kończy się skład.</para>
    /// </summary>
    public static int PlaceWithRear(
        SceneAxis axis, IReadOnlyList<ITrainBody> bodies, double rearChainageM)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(bodies);

        var plan = new List<BodyPlacement>(bodies.Count);
        for (var index = 0; index < bodies.Count; index++)
        {
            plan.Add(PlacementFor(axis.Axis, bodies[index].Span, rearChainageM, index));
        }

        Apply(axis, bodies, plan);
        return plan.Count - HiddenCount(plan);
    }

    /// <summary>Plan i jego wykonanie w jednym kroku. Zwraca liczbę ustawionych brył.</summary>
    public static int Place(
        SceneAxis axis, IReadOnlyList<ITrainBody> bodies, double frontChainageM)
    {
        ArgumentNullException.ThrowIfNull(axis);

        var plan = Plan(axis.Axis, bodies, frontChainageM);
        Apply(axis, bodies, plan);
        return plan.Count - HiddenCount(plan);
    }
}

/// <summary>
/// Widok składu M7: sześć pudeł i pięć mieszków ze skorupy z <c>tools/blender/m7_shell.py</c>,
/// każde ustawiane osobno na własnej cięciwie osi.
///
/// <b>Skąd biorą się zakresy członów.</b> Nie z przepisanych stałych, tylko z bryły
/// pojazdu: lokalny zakres X każdego węzła siatki jest odczytywany z jego AABB. Dzięki
/// temu warstwa silnika nie powtarza ani jednej liczby z <c>m7_layout.py</c> — ustawia
/// dokładnie tę geometrię, którą dostała, i przy zmianie podziału członów nie trzeba
/// tu niczego poprawiać. Skopiowana stała rozjeżdża się po cichu; odczytana nie.
///
/// <b>Gdzie jest decyzja.</b> Nie tutaj. Widoczność i transformację liczy
/// <see cref="TrainLayout"/>, który nie dotyka silnika i jest przybity w
/// <c>tests/Game.Tests/TrainViewLayoutTests.cs</c>. Tej klasie zostaje wczytanie skorupy
/// i przekazanie dwóch właściwości do węzłów.
/// </summary>
public sealed partial class TrainView : Node3D
{
    private readonly List<NodeBody> _bodies = new();

    /// <summary>Długość składu zmierzona z wczytanej bryły.</summary>
    public double LengthM { get; private set; }

    /// <summary>Szerokość składu zmierzona z wczytanej bryły.</summary>
    public double WidthM { get; private set; }

    /// <summary>Wysokość górnej krawędzi bryły nad główką szyny.</summary>
    public double RoofHeightM { get; private set; }

    /// <summary>Liczba ustawianych brył (pudła + mieszki).</summary>
    public int BodyCount => _bodies.Count;

    /// <summary>Wczytuje skorupę i przygotowuje bryły do ustawiania. Zwraca liczbę brył.</summary>
    public int Load(string shellPath, StandardMaterial3D material,
        bool preserveGeneratedMaterials = false)
    {
        var scene = GlbLoader.Load(shellPath);
        if (scene is null)
        {
            return 0;
        }

        var minX = double.PositiveInfinity;
        var maxX = double.NegativeInfinity;
        var minZ = double.PositiveInfinity;
        var maxZ = double.NegativeInfinity;
        var maxY = double.NegativeInfinity;

        foreach (var child in scene.GetChildren())
        {
            if (child is not MeshInstance3D mesh || mesh.Mesh is null)
            {
                continue;
            }

            var box = mesh.Mesh.GetAabb();
            minX = Math.Min(minX, box.Position.X);
            maxX = Math.Max(maxX, box.End.X);
            minZ = Math.Min(minZ, box.Position.Z);
            maxZ = Math.Max(maxZ, box.End.Z);
            maxY = Math.Max(maxY, box.End.Y);

            _bodies.Add(new NodeBody(mesh, new BodySpan(box.Position.X, box.End.X)));
        }

        foreach (var body in _bodies)
        {
            // Właściciela trzeba zdjąć **przed** przepięciem, inaczej Godot ostrzega
            // o niespójnym owner: węzeł nadal należałby do sceny, której już nie ma.
            body.Node.Owner = null;
            scene.RemoveChild(body.Node);
            AddChild(body.Node);
        }

        scene.QueueFree();

        LengthM = maxX - minX;
        WidthM = maxZ - minZ;
        RoofHeightM = maxY;

        // Wyjątek dotyczy wyłącznie naszej proceduralnej skorupy M7. Dla assetów
        // podanych przez gracza zachowujemy neutralną nakładkę bez względu na GLB.
        if (!preserveGeneratedMaterials)
        {
            GlbLoader.ApplyNeutralMaterial(this, material);
        }
        return _bodies.Count;
    }

    /// <summary>
    /// Drugi i każdy następny skład: te same SIATKI, własne węzły. Zwraca liczbę brył.
    ///
    /// <para><b>Dlaczego nie <see cref="Load"/> drugi raz i dlaczego nie
    /// <c>Duplicate()</c> — obie odpowiedzi są POMIAREM, nie ostrożnością</b>
    /// (14.09.2026, MB-07).</para>
    ///
    /// <para><c>GlbLoader.Load</c> buduje scenę przez <c>GltfDocument.AppendFromFile</c>
    /// za każdym razem od nowa, więc dwa wywołania <b>nie współdzielą ani jednego
    /// zasobu</b>: zmierzone „wspólnych zasobów <c>Mesh</c> 0 z 11", drugi skład
    /// kosztuje wtedy <b>666 252 B</b>. Ta metoda kosztuje <b>35 752 B</b>, czyli
    /// <b>18,6× mniej</b> — bo bierze <c>Mesh</c> ze składu źródłowego zamiast czytać
    /// plik.</para>
    ///
    /// <para><c>Duplicate()</c> byłoby jeszcze krótsze i jest PUŁAPKĄ: kopiuje
    /// właściwości Godota, a nie pola C#. Lista <c>_bodies</c> zostaje w duplikacie
    /// <b>pusta</b>, więc <see cref="PlaceAt"/> nie ustawia niczego, a
    /// <see cref="LengthM"/> jest zerem — drugi skład byłby niewidoczny i nieruchomy
    /// w origo, a kabina pojechałaby po <c>czoło − 0</c>. Zmierzone: duplikat ma
    /// <c>BodyCount=0</c> i <c>LengthM=0.000</c> przy 11 węzłach siatek w scenie.
    /// Jest to dokładnie ten rodzaj usterki, który przechodzi bramki — skrypt wykona
    /// się bez błędu.</para>
    ///
    /// <para><b>Rozpiętości nie liczy drugi raz</b>: geometria jest ta sama, więc
    /// <see cref="BodySpan"/>, <see cref="LengthM"/>, <see cref="WidthM"/>
    /// i <see cref="RoofHeightM"/> są KOPIOWANE ze źródła. Drugi rachunek na tych
    /// samych bryłach mógłby dać inną liczbę tylko przez pomyłkę.</para>
    ///
    /// <para>Materiał zewnętrznego GLB zostaje per-instancja
    /// (<c>MaterialOverride</c>); własne materiały M7 pozostają w dzielonej siatce.
    /// Współdzielenie <c>Mesh</c> nie zabiera możliwości pomalowania składów różnie.</para>
    /// </summary>
    public int LoadSharedFrom(TrainView source, StandardMaterial3D material,
        bool preserveGeneratedMaterials = false)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (source._bodies.Count == 0)
        {
            // Odmowa, a nie ciche zero: skład zbudowany z pustego źródła wygląda
            // w logu tak samo jak zbudowany poprawnie, a w kadrze go nie ma.
            return 0;
        }

        foreach (var wzor in source._bodies)
        {
            var mesh = new MeshInstance3D { Mesh = ((MeshInstance3D)wzor.Node).Mesh };
            AddChild(mesh);
            _bodies.Add(new NodeBody(mesh, wzor.Span));
        }

        LengthM = source.LengthM;
        WidthM = source.WidthM;
        RoofHeightM = source.RoofHeightM;

        if (!preserveGeneratedMaterials)
        {
            GlbLoader.ApplyNeutralMaterial(this, material);
        }
        return _bodies.Count;
    }

    /// <summary>
    /// Ustawia wszystkie bryły dla zadanego chainage **czoła** składu.
    ///
    /// Ogon liczy się od czoła przez zmierzoną rozpiętość brył, a nie przez 94,0 m
    /// wpisane w kod: jeśli generator kiedyś zmieni długość, skład nadal będzie stał
    /// całością na osi. Cała arytmetyka i cała decyzja o widoczności są w
    /// <see cref="TrainLayout"/> — ta metoda nie ma własnego wariantu.
    /// </summary>
    public void PlaceAt(SceneAxis axis, double frontChainageM) =>
        TrainLayout.Place(axis, _bodies, frontChainageM);

    /// <summary>Jedna linia do logu przejazdu.</summary>
    public string Describe() => string.Create(
        CultureInfo.InvariantCulture,
        $"[SKŁAD] brył={BodyCount} długość={LengthM:F3} m szerokość={WidthM:F3} m dach={RoofHeightM:F3} m nad główką szyny");

    /// <summary>
    /// Węzeł sceny jako <see cref="ITrainBody"/>.
    ///
    /// <para>To jest CAŁA granica między decyzją a silnikiem — dwie właściwości
    /// przekazane do <c>Node3D</c> i nic więcej. Wszystko, co da się sprawdzić bez
    /// silnika, leży po drugiej stronie tej granicy, w <see cref="TrainLayout"/>.</para>
    /// </summary>
    private sealed class NodeBody : ITrainBody
    {
        internal NodeBody(Node3D node, BodySpan span)
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
