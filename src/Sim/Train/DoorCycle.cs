using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Train;

/// <summary>Faza cyklu drzwi. Kolejność deklaracji jest kolejnością cyklu.</summary>
public enum DoorPhase
{
    /// <summary>Zamknięte i zaryglowane — jedyny stan, w którym wolno jechać.</summary>
    Closed,

    /// <summary>Odryglowanie po zatrzymaniu; drzwi jeszcze się nie ruszają.</summary>
    Unlocking,

    /// <summary>Otwieranie.</summary>
    Opening,

    /// <summary>Otwarte, wymiana pasażerów.</summary>
    Open,

    /// <summary>Sygnał zamykania — drzwi jeszcze otwarte, ale już ostrzegają.</summary>
    ClosingWarning,

    /// <summary>Zamykanie.</summary>
    Closing,

    /// <summary>Kontrola zamknięcia; dopiero jej koniec zwalnia blokadę jazdy.</summary>
    Checking,
}

/// <summary>
/// Cykl drzwi i czas postoju z <c>docs/02-simulation.md</c>.
///
/// <para><b>Co jest, a czego nie ma.</b> Pięć faz o stałym czasie — odryglowanie 0,5 s,
/// otwieranie 2,0 s, sygnał zamykania 3,0 s, zamykanie 2,5 s, kontrola 0,5 s — jest
/// wypisane wprost w <c>docs/02-simulation.md</c> jako <c>design_model</c> i tyle
/// z tego cyklu ma jakąkolwiek podstawę. **Czas wymiany pasażerów nie ma jej żadnej**:
/// zależy od potoku, pory dnia i stacji, a w rejestrze źródeł nie ma ani jednej z tych
/// rzeczy. Dlatego nie jest tu stałą — jest **argumentem**, a scenariusz, który go
/// poda, musi go zadeklarować jako własne założenie.</para>
///
/// <para><b>Minimalny postój</b> jest więc wielkością wyprowadzoną, nie przyjętą:
/// 0,5 + 2,0 + 3,0 + 2,5 + 0,5 = <b>8,5 s</b> niezależnie od tego, ilu pasażerów
/// wysiada. To jest dolne ograniczenie postoju, które wynika z samego cyklu drzwi.</para>
///
/// <para><b>Blokada jazdy</b> (<c>docs/02</c>: „Jazda zablokowana do potwierdzenia
/// zamknięcia") jest własnością bezpieczeństwa, nie parametrem: trakcja jest wolna
/// wyłącznie w fazie <see cref="DoorPhase.Closed"/>. Kontrola zamknięcia trwa 0,5 s
/// PO zakończeniu ruchu skrzydeł — składu nie wolno ruszyć w chwili, gdy skrzydła się
/// zetknęły, tylko gdy układ to potwierdzi.</para>
/// </summary>
public sealed class DoorCycle
{
    private readonly double _passengerExchangeSeconds;

    /// <summary>Odryglowanie po zatrzymaniu, sekundy. <c>docs/02-simulation.md</c>.</summary>
    public const double UnlockSeconds = 0.5;

    /// <summary>Otwieranie, sekundy. <c>docs/02-simulation.md</c>.</summary>
    public const double OpenSeconds = 2.0;

    /// <summary>Sygnał zamykania, sekundy. <c>docs/02-simulation.md</c>.</summary>
    public const double ClosingWarningSeconds = 3.0;

    /// <summary>Zamykanie, sekundy. <c>docs/02-simulation.md</c>.</summary>
    public const double CloseSeconds = 2.5;

    /// <summary>Kontrola zamknięcia, sekundy. <c>docs/02-simulation.md</c>.</summary>
    public const double CheckSeconds = 0.5;

    /// <summary>
    /// Suma faz o stałym czasie — dolne ograniczenie postoju, niezależne od potoku.
    /// Wyprowadzone, nie przyjęte.
    /// </summary>
    public const double MinimumDwellSeconds =
        UnlockSeconds + OpenSeconds + ClosingWarningSeconds + CloseSeconds + CheckSeconds;

    /// <summary>Cykl z zadanym czasem wymiany pasażerów.</summary>
    /// <param name="passengerExchangeSeconds">
    /// Czas wymiany pasażerów. <b>Nie ma źródła</b> — musi pochodzić ze scenariusza,
    /// który deklaruje go jako własne założenie. Zero jest dopuszczalne i znaczy
    /// „nikt nie wysiada ani nie wsiada", a nie „drzwi się nie otwierają".
    /// </param>
    public DoorCycle(double passengerExchangeSeconds)
    {
        if (!double.IsFinite(passengerExchangeSeconds) || passengerExchangeSeconds < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(passengerExchangeSeconds), passengerExchangeSeconds,
                "Czas wymiany pasażerów musi być nieujemny i skończony.");
        }

        _passengerExchangeSeconds = passengerExchangeSeconds;
    }

    /// <summary>Czas wymiany pasażerów użyty przez ten cykl.</summary>
    public double PassengerExchangeSeconds => _passengerExchangeSeconds;

    /// <summary>Pełny czas postoju: fazy stałe plus wymiana pasażerów.</summary>
    public double DwellSeconds => MinimumDwellSeconds + _passengerExchangeSeconds;

    /// <summary>Czas trwania zadanej fazy.</summary>
    public double PhaseSeconds(DoorPhase phase) => phase switch
    {
        DoorPhase.Closed => 0.0,
        DoorPhase.Unlocking => UnlockSeconds,
        DoorPhase.Opening => OpenSeconds,
        DoorPhase.Open => _passengerExchangeSeconds,
        DoorPhase.ClosingWarning => ClosingWarningSeconds,
        DoorPhase.Closing => CloseSeconds,
        DoorPhase.Checking => CheckSeconds,
        _ => throw new ArgumentOutOfRangeException(nameof(phase), phase, "Nieznana faza cyklu drzwi."),
    };

    /// <summary>
    /// Faza po zadanym czasie od otwarcia cyklu, oraz czas spędzony już w tej fazie.
    ///
    /// Poza końcem cyklu zwraca <see cref="DoorPhase.Closed"/> — cykl się domknął
    /// i skład może jechać.
    /// </summary>
    public (DoorPhase Phase, double ElapsedInPhaseSeconds) At(double secondsSinceStop)
    {
        if (!double.IsFinite(secondsSinceStop) || secondsSinceStop < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(secondsSinceStop), secondsSinceStop, "Czas od zatrzymania musi być nieujemny i skończony.");
        }

        var remaining = secondsSinceStop;
        foreach (var phase in Sequence)
        {
            var length = PhaseSeconds(phase);
            if (remaining < length)
            {
                return (phase, remaining);
            }

            remaining -= length;
        }

        return (DoorPhase.Closed, remaining);
    }

    /// <summary>
    /// Czy w tej fazie wolno podać trakcję. <b>Tylko przy zamkniętych i sprawdzonych.</b>
    ///
    /// Faza <see cref="DoorPhase.Open"/> o zerowej długości nadal nie zwalnia blokady —
    /// cykl przechodzi przez nią natychmiast, ale blokada trwa aż do końca kontroli.
    /// </summary>
    public static bool TractionAllowed(DoorPhase phase) => phase == DoorPhase.Closed;

    /// <summary>Czy skrzydła są w tej fazie odsunięte na tyle, że nie wolno ruszyć.</summary>
    public static bool LeavesMoving(DoorPhase phase) =>
        phase is DoorPhase.Opening or DoorPhase.Closing;

    /// <summary>Kolejność faz w cyklu, bez fazy <see cref="DoorPhase.Closed"/>.</summary>
    public static IReadOnlyList<DoorPhase> Sequence { get; } = new[]
    {
        DoorPhase.Unlocking,
        DoorPhase.Opening,
        DoorPhase.Open,
        DoorPhase.ClosingWarning,
        DoorPhase.Closing,
        DoorPhase.Checking,
    };

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"cykl drzwi: {MinimumDwellSeconds:F1} s faz stałych + {_passengerExchangeSeconds:F1} s wymiany " +
        $"= {DwellSeconds:F1} s postoju");
}
