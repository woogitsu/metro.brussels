using System.Globalization;
using Godot;

namespace MetroBxl.Game.UI;

/// <summary>
/// Podgląd stanu przejazdu. Siedem pól tekstowych i nic więcej: prędkość, położenie na
/// osi, to co robią nastawniki, stacja — dojazd albo faza cyklu drzwi — sygnalizacja,
/// czyli prędkość dopuszczalna z autorytetem jazdy, widok, gdy pokazywany jest inny niż
/// zamówiony, i opis sterowania, gdy przy sterowaniu siedzi człowiek.
///
/// <b>Hamulec awaryjny nie dostaje siódmego pola.</b> Jego wiersz dokleja się do pola
/// nastawników, bo mówi o tym samym hamulcu, którego wskaźnik stoi obok — i dlatego,
/// że HUD bez trzymanego klawisza ma wyjść napisem identycznym jak przed 05.09.2026.
///
/// <b>Bez brandingu.</b> <c>docs/03-legal.md</c> zabrania logo, map sieci, piktogramów
/// i wystroju STIB/MIVB. HUD jest gołym tekstem na półprzezroczystym tle i nie udaje
/// żadnego istniejącego pulpitu.
/// </summary>
public sealed partial class Hud : CanvasLayer
{
    private Label? _speed;
    private Label? _position;
    private Label? _controls;
    private Label? _station;
    private Label? _signalling;
    private Label? _view;
    private Label? _help;

    /// <inheritdoc/>
    public override void _Ready()
    {
        _speed = GetNode<Label>("Panel/Rows/Speed");
        _position = GetNode<Label>("Panel/Rows/Position");
        _controls = GetNode<Label>("Panel/Rows/Controls");
        _station = GetNode<Label>("Panel/Rows/Station");
        _signalling = GetNode<Label>("Panel/Rows/Signalling");
        _view = GetNode<Label>("Panel/Rows/View");
        _help = GetNode<Label>("Panel/Rows/Help");

        foreach (var label in new[] { _speed, _position, _controls, _station, _signalling, _view, _help })
        {
            label.AddThemeFontSizeOverride("font_size", 20);
            label.AddThemeColorOverride("font_color", new Color(0.92f, 0.94f, 0.96f));
        }

        _speed.AddThemeFontSizeOverride("font_size", 34);

        // Wiersz stacji startuje UKRYTY. W .tscn ma tekst zastępczy, żeby scena dała się
        // otworzyć w edytorze, a widoczność ustawia dopiero `Update` — inaczej przebieg
        // bez obsługi stacji (skryptowy, czyli każdy zrzut kontrolny) miałby na pierwszej
        // klatce czwarty wiersz i bramka wizualna zapłaciłaby za tekst zastępczy.
        _station.Visible = false;
        _signalling.Visible = false;
        _view.Visible = false;

        // Wiersz pomocy startuje ukryty z tego samego powodu co trzy powyższe, i z jednym
        // powodem więcej: w przebiegu skryptowym ma NIE WYJŚĆ WCALE. Progi bramki
        // `tools/visual/compare.py --set godot` są zmierzone na klatce bez geometrii,
        // czyli na samym HUD-zie — stały napis w każdej klatce podniósłby dokładnie tę
        // metrykę, którą ta bramka odrzuca pustą klatkę.
        _help.Visible = false;
    }

    /// <summary>Odświeża wszystkie siedem wierszy.</summary>
    /// <param name="speedKmh">Prędkość w km/h.</param>
    /// <param name="accelerationMps2">Przyspieszenie ze znakiem.</param>
    /// <param name="chainageM">Chainage czoła składu.</param>
    /// <param name="axisLengthM">Długość osi pakietu.</param>
    /// <param name="nextStation">Nazwa najbliższej stacji przed składem.</param>
    /// <param name="toStationM">Odległość do niej; ujemna, gdy już za składem.</param>
    /// <param name="throttle">Nastawnik jazdy.</param>
    /// <param name="brake">Hamulec.</param>
    /// <param name="mode">Nazwa trybu przejazdu.</param>
    /// <param name="station">
    /// Wiersz o stacji, złożony po stronie wołającego. HUD go NIE składa: faza drzwi,
    /// okno zatrzymania i licznik wywołań mieszkają w <c>StationService</c>, a druga
    /// kopia tej wiedzy tutaj rozjechałaby się z pierwszą. Puste znaczy „bez wiersza",
    /// czyli przebieg bez obsługi stacji.
    /// </param>
    /// <param name="signalling">
    /// Wiersz o sygnalizacji, złożony po stronie wołającego — z tego samego powodu, co
    /// wiersz o stacji: prędkość dopuszczalna, autorytet i powód jego końca mieszkają
    /// w <c>TrainProtection</c> i <c>MovementAuthority</c>, a druga kopia tej wiedzy
    /// tutaj rozjechałaby się z pierwszą. Puste znaczy „przebieg bez sygnalizacji".
    /// </param>
    /// <param name="view">
    /// Wiersz o widoku: dlaczego zamówionego widoku w tej chwili nie widać i od
    /// jakiego kilometraża będzie. Puste znaczy „widok jest ten, o który proszono".
    ///
    /// <para>Wiersz istnieje z tego samego powodu, co zdanie „bez sygnalizacji —
    /// przejazd bez blokad": MILCZENIE WYGLĄDA TAK SAMO JAK „wszystko w porządku",
    /// a to dwie różne rzeczy. Gracz, który wcisnął C i zobaczył kabinę, musi wiedzieć,
    /// czy widok goniący nie działa, czy jeszcze nie jest dostępny.</para>
    /// </param>
    /// <param name="emergency">
    /// Wiersz o hamulcu awaryjnym, złożony po stronie wołającego przez
    /// <c>MetroBxl.Game.Input.EmergencyBrake.Notice</c> — z tego samego powodu, co dwa
    /// poprzednie: liczba w nim ma pochodzić z polecenia, którym pojechał kontroler.
    /// Puste znaczy „klawisz nie jest trzymany".
    ///
    /// <para>Dokleja się do wiersza nastawników, a nie zajmuje własnego: mówi
    /// o hamulcu, którego wskaźnik stoi obok, a HUD bez trzymanego klawisza ma wyjść
    /// napisem IDENTYCZNYM jak przedtem — bramka wizualna ogląda te wiersze.</para>
    /// </param>
    /// <param name="help">
    /// Opis sterowania — składa go <c>MetroBxl.Game.Input.DriverActions</c> z tej samej
    /// tabeli, z której biorą się przypisania <c>InputMap</c> w <c>project.godot</c>.
    /// Puste znaczy „tego przejazdu nie prowadzi człowiek", czyli przebieg skryptowy
    /// albo odtworzenie z zapisu wejść.
    ///
    /// <para>HUD tego napisu NIE SKŁADA — ta sama zasada, co przy trzech poprzednich
    /// wierszach. Druga kopia listy klawiszy tutaj rozjechałaby się z pierwszą przy
    /// pierwszej zmianie sterowania, a rozjechałaby się CICHO: wiersz pomocy mówiący
    /// o niewłaściwym klawiszu wygląda dokładnie tak samo jak wiersz prawdziwy.</para>
    /// </param>
    public void Update(
        double speedKmh,
        double accelerationMps2,
        double chainageM,
        double axisLengthM,
        string nextStation,
        double toStationM,
        double throttle,
        double brake,
        string mode,
        string station,
        string signalling,
        string view,
        string emergency,
        string help)
    {
        if (_speed is null || _position is null || _controls is null
            || _station is null || _signalling is null || _view is null || _help is null)
        {
            return;
        }

        _speed.Text = string.Create(
            CultureInfo.InvariantCulture, $"{speedKmh,6:F1} km/h     a = {accelerationMps2,6:F2} m/s²");
        _position.Text = string.Create(
            CultureInfo.InvariantCulture,
            $"chainage {chainageM,9:F1} m / {axisLengthM:F1} m     {nextStation} za {toStationM:F0} m");
        var emergencySuffix = emergency.Length > 0 ? "   " + emergency : string.Empty;
        _controls.Text = string.Create(
            CultureInfo.InvariantCulture,
            $"ciąg {Bar(throttle)} {throttle:F2}   hamulec {Bar(brake)} {brake:F2}   [{mode}]{emergencySuffix}");
        _station.Text = station;
        _station.Visible = station.Length > 0;
        _signalling.Text = signalling;
        _signalling.Visible = signalling.Length > 0;
        _view.Text = view;
        _view.Visible = view.Length > 0;
        _help.Text = help;
        _help.Visible = help.Length > 0;
    }

    private static string Bar(double value)
    {
        var filled = (int)System.Math.Round(value * 10.0);
        return new string('#', filled) + new string('.', 10 - filled);
    }
}
