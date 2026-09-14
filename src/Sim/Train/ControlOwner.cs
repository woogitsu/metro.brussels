namespace MetroBxl.Sim.Train;

/// <summary>
/// Kto prowadzi ten skład — MB-06, 14.09.2026.
///
/// <para><b>Dlaczego to jest ENUM, a nie <c>bool IsDriven</c>.</b> Bo pytanie „kto
/// prowadzi" ma mieć w logu i w HUD-zie NAZWĘ, a nie prawdę logiczną: wiersz
/// „sterowanie: maszynista" czyta się sam, a „sterowanie: prawda" wymaga wiedzy,
/// której czytający nie ma. Ta sama zasada, co przy <c>ProtectionAction</c>.</para>
///
/// <para><b>Czym to NIE jest.</b> Nie jest przełącznikiem ochrony. <c>TrainProtection</c>
/// stoi nad OBOMA właścicielami i nie ma trybu, w którym człowiek ją omija — pole
/// „Pułapka wypisana w audycie" pozycji MB-06 mówi to wprost: supervisor zostaje
/// OCHRONĄ, nie zastępczym wejściem gracza. Nie jest też przełącznikiem okna
/// zatrzymania: dwustronne okno <c>StationService</c> obowiązuje maszynistę tak samo
/// jak autopilota, bo człowiek może przestrzelić peron, a autopilot nie.</para>
/// </summary>
public enum ControlOwner
{
    /// <summary>Prowadzi autopilot linii (<c>LineDrive.Command</c>). Stan domyślny.</summary>
    Autopilot,

    /// <summary>Prowadzi człowiek; komenda przychodzi z zewnątrz i trwa do zmiany.</summary>
    Driver,
}
