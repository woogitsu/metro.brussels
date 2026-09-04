using System.Globalization;
using Godot;

namespace MetroBxl.Game.UI;

/// <summary>
/// Podgląd stanu przejazdu. Pięć pól tekstowych i nic więcej: prędkość, położenie na
/// osi, to co robią nastawniki, stacja — dojazd albo faza cyklu drzwi — i sygnalizacja,
/// czyli prędkość dopuszczalna z autorytetem jazdy.
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

    /// <inheritdoc/>
    public override void _Ready()
    {
        _speed = GetNode<Label>("Panel/Rows/Speed");
        _position = GetNode<Label>("Panel/Rows/Position");
        _controls = GetNode<Label>("Panel/Rows/Controls");
        _station = GetNode<Label>("Panel/Rows/Station");
        _signalling = GetNode<Label>("Panel/Rows/Signalling");

        foreach (var label in new[] { _speed, _position, _controls, _station, _signalling })
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
    }

    /// <summary>Odświeża wszystkie trzy wiersze.</summary>
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
        string signalling)
    {
        if (_speed is null || _position is null || _controls is null
            || _station is null || _signalling is null)
        {
            return;
        }

        _speed.Text = string.Create(
            CultureInfo.InvariantCulture, $"{speedKmh,6:F1} km/h     a = {accelerationMps2,6:F2} m/s²");
        _position.Text = string.Create(
            CultureInfo.InvariantCulture,
            $"chainage {chainageM,9:F1} m / {axisLengthM:F1} m     {nextStation} za {toStationM:F0} m");
        _controls.Text = string.Create(
            CultureInfo.InvariantCulture,
            $"ciąg {Bar(throttle)} {throttle:F2}   hamulec {Bar(brake)} {brake:F2}   [{mode}]");
        _station.Text = station;
        _station.Visible = station.Length > 0;
        _signalling.Text = signalling;
        _signalling.Visible = signalling.Length > 0;
    }

    private static string Bar(double value)
    {
        var filled = (int)System.Math.Round(value * 10.0);
        return new string('#', filled) + new string('.', 10 - filled);
    }
}
