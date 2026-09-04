using System.Globalization;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Rodzaje zdarzeń domenowych klasycznej sygnalizacji.
///
/// <para>Lista jest **minimalna** i pochodzi wprost z T-313 (#23): zajętość bloku,
/// cykl życia trasy, movement authority, nadzór prędkości i interfejs drzwi. Nie ma
/// tu aspektów sygnałów ani telegramów — <c>data/signalling/ground-truth.json</c>
/// wymienia jedno i drugie w <c>unknown_parameters</c>, więc wystawienie ich jako
/// zdarzeń byłoby udawaniem wiedzy, której repo nie ma.</para>
///
/// <para>Kolejność deklaracji jest częścią kontraktu: <see cref="SignallingEvent.Sequence"/>
/// porządkuje strumień, a nazwa rodzaju wchodzi do odcisku stanu.</para>
/// </summary>
public enum SignallingEventKind
{
    /// <summary>Skład wprowadzony na plan; niesie długość i chainage czoła.</summary>
    TrainRegistered,

    /// <summary>
    /// Skład wypisany z planu — zwolnił wszystkie bloki i trasę.
    ///
    /// Dopisane przy turnbacku: skład, który dojechał do ostatniego peronu, musi
    /// zwolnić ten peron, inaczej trzyma go NA ZAWSZE i następny skład nie ma jak
    /// zaryglować ostatniej trasy. Zmierzone przed tą zmianą na pakiecie A: drugi
    /// skład stawał na 5514,04 m, bo pierwszy nigdy nie odjeżdżał z Merode.
    /// </summary>
    TrainDeregistered,

    /// <summary>Blok przeszedł w zajętość pod danym składem.</summary>
    BlockOccupied,

    /// <summary>Blok zwolniony — tył składu go opuścił.</summary>
    BlockReleased,

    /// <summary>Blok zarezerwowany pod zaryglowaną trasę.</summary>
    BlockReserved,

    /// <summary>Rezerwacja bloku zdjęta razem z trasą.</summary>
    BlockReservationReleased,

    /// <summary>Żądanie trasy — zapisane niezależnie od tego, czy zostanie przyjęte.</summary>
    RouteRequested,

    /// <summary>Trasa zaryglowana.</summary>
    RouteLocked,

    /// <summary>Trasa odrzucona; powód w <see cref="SignallingEvent.Detail"/>.</summary>
    RouteRejected,

    /// <summary>Trasa zwolniona.</summary>
    RouteReleased,

    /// <summary>Zmiana movement authority: nowy koniec i powód ograniczenia.</summary>
    AuthorityIssued,

    /// <summary>Skład przekroczył koniec authority albo wjechał w blok zajęty przez inny skład.</summary>
    AuthorityViolation,

    /// <summary>Prędkość ponad dopuszczalną krzywą.</summary>
    OverspeedWarning,

    /// <summary>Ingerencja hamulcem służbowym.</summary>
    OverspeedIntervention,

    /// <summary>Ingerencja hamulcem awaryjnym.</summary>
    EmergencyIntervention,

    /// <summary>Zwolnienie drzwi zablokowane.</summary>
    DoorInhibit,

    /// <summary>Zwolnienie drzwi dozwolone.</summary>
    DoorRelease,
}

/// <summary>
/// Jedno zdarzenie domenowe sygnalizacji.
///
/// <para><b>Dlaczego strumień, a nie same pola stanu.</b> Zasada 6 z T-313: sygnalizacja
/// niczym nie steruje, tylko emituje stan domenowy. Odbiorcą może być kabina, HUD,
/// dispatcher albo test — i żaden z nich nie ma prawa sięgać do wnętrza
/// <see cref="FixedBlockSystem"/>. Strumień jest jednocześnie **zapisem**, z którego
/// da się odtworzyć stan ryglowania: patrz <see cref="FixedBlockSystem.Replay"/>.</para>
///
/// <para><b>Czego zdarzenie nie niesie.</b> Ani czasu w sekundach, ani numeru kroku —
/// sygnalizacja nie ma własnego zegara. Porządek daje <see cref="Sequence"/>, licznik
/// całkowity, dokładnie z tego samego powodu, dla którego <c>FixedStep</c> liczy kroki
/// zamiast sumować <c>dt</c>: liczba całkowita nie dryfuje.</para>
/// </summary>
/// <param name="Sequence">Numer porządkowy w strumieniu, od zera.</param>
/// <param name="Kind">Rodzaj zdarzenia.</param>
/// <param name="SubjectId">Czego dotyczy: identyfikator bloku, trasy albo składu.</param>
/// <param name="TrainId">Skład, którego dotyczy; pusty, gdy zdarzenie nie ma składu.</param>
/// <param name="ChainageM">Chainage istotny dla zdarzenia — czoło składu albo koniec authority.</param>
/// <param name="Detail">
/// Uzupełnienie zależne od rodzaju: identyfikator trasy przy rezerwacji bloku, powód
/// odrzucenia trasy, powód ograniczenia authority. Nigdy <c>null</c>.
/// </param>
public readonly record struct SignallingEvent(
    long Sequence,
    SignallingEventKind Kind,
    string SubjectId,
    string TrainId,
    double ChainageM,
    string Detail)
{
    /// <summary>Jedna linia zapisu; kultura niezmienna, żeby wyjście nie zależało od maszyny.</summary>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"#{Sequence} {Kind} {SubjectId} train={TrainId} @ {ChainageM:F3} m{(Detail.Length == 0 ? string.Empty : $" [{Detail}]")}");
}
