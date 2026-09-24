using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;

namespace MetroBxl.Game;

/// <summary>
/// Wiersz HUD-u o sygnalizacji: prędkość dopuszczalna, autorytet jazdy, powód jego
/// końca, licznik nastawni i to, czy ochrona pociągu właśnie hamuje za maszynistę.
///
/// <para><b>Dlaczego osobny plik BEZ GODOTA.</b> Ta sama decyzja i ten sam powód, co
/// przy <see cref="RunPlan"/>, <see cref="RunHeader"/> i <see cref="RunReset"/>: napis
/// złożony z liczb przebiegu da się sprawdzić testem jednostkowym tylko wtedy, gdy nie
/// wymaga uruchomionego silnika. Póki składanie tego wiersza siedziało w metodzie węzła
/// <c>Node3D</c>, pilnował go wyłącznie ludzki wzrok czytający zrzut.</para>
///
/// <para><b>Dlaczego JEDEN skład dla dwóch trybów.</b> Bo od 05.09.2026 wiersz mają dwa
/// przebiegi: linia prowadzona <c>LineCore</c> i kabina prowadzona przez człowieka pod
/// <c>CabProtection</c>. Obie strony pokazują dokładnie te same wielkości i gdyby każda
/// składała je u siebie, rozjechałyby się cicho — a wiersz z inną jednostką albo innym
/// zaokrągleniem wygląda tak samo jak wiersz prawdziwy. Format jest tu więc jeden i to
/// jest cała treść tego pliku; napis dla trybu <c>--line</c> nie zmienił się o ani jeden
/// znak, bo zrzuty kontrolne z <c>--line --shot</c> ogląda bramka wizualna.</para>
///
/// <para><b>Wiersz POKAZUJE decyzję, a nie liczy drugiej.</b> Do 04.09.2026 stało w tym
/// miejscu własne wołanie <c>TrainProtection.Supervise</c> „tylko do pokazania". Drugie
/// wołanie liczyłoby decyzję z innego stanu — HUD chodzi w klatkach, rdzeń w krokach —
/// i nie dałoby się powiedzieć, która liczba jest prawdziwa; a przy okazji emitowałoby
/// zdarzenia sygnalizacji z widoku.</para>
/// </summary>
public static class SignallingHud
{
    /// <summary>
    /// Wiersz przebiegu, który sygnalizacji nie ma. Milczenie wyglądałoby dokładnie tak
    /// samo jak „droga wolna", a to dwie różne rzeczy.
    /// </summary>
    public const string WithoutSignalling = "bez sygnalizacji — przejazd bez blokad (podaj --signalling)";

    /// <summary>Wiersz składu, który jeszcze nie wjechał na plan (wejście zajęte).</summary>
    public const string NotOnPlanYet = "sygnalizacja: skład jeszcze nie wjechał na plan";

    /// <summary>Skład po końcu przejazdu zjechał z planu; nie oczekuje na wyjazd.</summary>
    public const string LeftPlan = "sygnalizacja: skład zakończył przejazd i zjechał z planu";

    /// <summary>Stan składu bez bieżącego autorytetu jazdy.</summary>
    public static string WithoutAuthority(LineTrain train) =>
        train.LeftPlan ? LeftPlan : NotOnPlanYet;

    /// <summary>Wiersz przejazdu pod planem, ale bez ochrony pociągu.</summary>
    public const string WithoutProtection = "sygnalizacja: linia bez ochrony pociągu";

    /// <summary>Wiersz przed pierwszym krokiem, gdy decyzji ochrony jeszcze nie ma.</summary>
    public const string BeforeFirstStep = "sygnalizacja: przed pierwszym krokiem";

    /// <summary>
    /// Wiersz z liczbami. Bierze gotową decyzję i gotowy autorytet — niczego nie liczy
    /// i niczego nie pyta o stan.
    /// </summary>
    /// <param name="authority">Autorytet jazdy odczytany w tym kroku przez rdzeń.</param>
    /// <param name="decision">Decyzja ochrony z tego samego kroku.</param>
    /// <param name="lockedRoutes">Ile tras nastawnia zaryglowała do tej pory.</param>
    /// <param name="refusedRoutes">Ile żądań odrzuciła. Odmowa jest normalną odpowiedzią, nie usterką.</param>
    /// <returns>Gotowy wiersz HUD-u.</returns>
    public static string Line(
        MovementAuthority authority, ProtectionDecision decision, int lockedRoutes, int refusedRoutes)
    {
        var ostrzezenie = decision.Overspeed ? "  PRZEKROCZENIE" : string.Empty;
        var ingerencja = decision.Action == ProtectionAction.None
            ? string.Empty
            : string.Create(
                CultureInfo.InvariantCulture,
                $"  ATP HAMUJE: {decision.Action} {decision.BrakeDemandMps2:F2} m/s²");
        return string.Create(
            CultureInfo.InvariantCulture,
            $"v_dop {Units.MpsToKmh(decision.PermittedSpeedMps),5:F1} km/h   "
            + $"autorytet {authority.DistanceM,7:F0} m ({authority.Reason}, blok {authority.LimitBlockId})   "
            + $"tras {lockedRoutes}/odmów {refusedRoutes}"
            + $"{ostrzezenie}{ingerencja}");
    }
}
