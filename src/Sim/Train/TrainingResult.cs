using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Jak skończyła się sesja treningowa — JEDNO wyliczenie, nie dwa.
///
/// <para><b>Dlaczego jedno, a nie „zaliczone?" plus „powód".</b> Para
/// <c>(bool, powód)</c> ma cztery kombinacje, z których dwie są bez sensu (zaliczone
/// z powodem „minięty cel", niezaliczone z powodem „wszystkie obsłużone"), i nic nie
/// broni przed ich zbudowaniem. Tutaj stan zaliczenia jest WYPROWADZONY z zakończenia
/// (<see cref="TrainingResult.Passed"/>), więc drugiej prawdy nie ma gdzie trzymać —
/// ta sama zasada, co w <see cref="RunRestart"/>: jedna odpowiedź, jedno miejsce.</para>
/// </summary>
public enum TrainingEnding
{
    /// <summary>Sesja trwa — wyniku jeszcze nie ma.</summary>
    Running,

    /// <summary>
    /// Wszystkie cele obsłużone, drzwi ostatniego zamknięte, skład stoi. Jedyne
    /// zakończenie, które jest zaliczeniem — i dokładnie warunek z
    /// <c>docs/PLAYABILITY.md</c> §3 („po obsłudze drugiego celu, gdy drzwi są zamknięte
    /// i skład stoi").
    /// </summary>
    AllTargetsServed,

    /// <summary>
    /// Wymagany cel minięty. Skład nie ma biegu wstecznego
    /// (<see cref="StationService"/>: „przejechana stacja jest przejechana na zawsze"),
    /// więc celu nie da się już obsłużyć żadnym późniejszym poleceniem.
    ///
    /// <para><b>Minięcie stacji, która celem NIE jest, sesji nie kończy</b> — kontrakt
    /// M1 mówi o „miniętym <b>wymaganym</b> celu", a oś pakietu A ma dwanaście stacji
    /// przy dwóch celach. Przejechanie trzeciej bez zatrzymania jest poza zadaniem,
    /// a nie porażką w nim.</para>
    /// </summary>
    TargetMissed,
}

/// <summary>
/// Jeden cel sesji, tak jak wygląda w wyniku.
///
/// <para><b>Pomiary są <c>double?</c>, a nie <c>NaN</c></b> — precedens
/// <see cref="StationCall.TractionWorkFromPreviousJ"/>. Powód jest mierzalny:
/// <c>NaN</c> przechodzi przez każde porównanie liczbowe jako FAŁSZ, po cichu, więc
/// „błąd zatrzymania ≤ 0,5 m" na celu nieobsłużonym wychodzi tak samo, jak na
/// zatrzymaniu o metr za daleko. <c>null</c> trzeba obsłużyć albo dostać wyjątek.</para>
/// </summary>
/// <param name="StopId">Identyfikator przystanku z osi — to po nim cel jest wyszukiwany.</param>
/// <param name="DisplayName">Nazwa do pokazania człowiekowi.</param>
/// <param name="Served">Czy cel został obsłużony (zatrzymanie w oknie i pełny cykl drzwi).</param>
/// <param name="StopErrorM">
/// Błąd zatrzymania ZE ZNAKIEM: <c>+</c> za daleko, <c>−</c> za blisko.
/// <c>null</c>, gdy celu nie obsłużono.
/// </param>
/// <param name="ArrivalSeconds">Czas zatrzymania; <c>null</c>, gdy celu nie obsłużono.</param>
/// <param name="DepartureSeconds">Czas ruszenia; <c>null</c>, gdy drzwi się nie domknęły.</param>
public readonly record struct TrainingTarget(
    string StopId,
    string DisplayName,
    bool Served,
    double? StopErrorM,
    double? ArrivalSeconds,
    double? DepartureSeconds);

/// <summary>
/// Wynik sesji treningowej — to, co powstaje DOKŁADNIE RAZ i co widzi gracz.
///
/// <para><b>To są FAKTY, nie punkty</b> (<c>docs/PLAYABILITY.md</c> §3): ukończono albo
/// pominięto cel, obsłużone cele, błąd zatrzymania na każdym, czas w czasie symulacji,
/// informacja o interwencji ochrony. Bez punktacji, gwiazdek i kar — i bez ani jednej
/// liczby, która byłaby oceną.</para>
///
/// <para><b>Wszystkie liczby są CZYTANE z obiektów, które prowadziły przejazd</b>
/// (<see cref="StationService.Calls"/>, <see cref="DriveState"/>,
/// <c>ProtectionDecision</c>), a nie liczone obok nich. Ta sama reguła i ten sam powód,
/// co w <c>Game.RunHeader</c>: liczba w wyniku, która nie jest wynikiem niczego, nie ma
/// czego porównać i rozjeżdża się po cichu.</para>
/// </summary>
/// <param name="Ending">Jak sesja się skończyła.</param>
/// <param name="Targets">Cele w kolejności, w jakiej je zadano.</param>
/// <param name="TotalSeconds">Czas symulacji w chwili zakończenia sesji.</param>
/// <param name="TotalDistanceM">Droga przebyta do chwili zakończenia sesji.</param>
/// <param name="AtpWarningEvents">
/// Ile RAZY prędkość weszła ponad dopuszczalną — zdarzenia, nie kroki.
/// Patrz <see cref="TrainingSession"/>: zdarzeniem jest ZBOCZE predykatu.
/// </param>
/// <param name="AtpInterventionEvents">Ile RAZY ochrona sięgnęła po hamulec.</param>
/// <param name="AtpEmergencyEvents">Ile RAZY ingerencja była awaryjna.</param>
public readonly record struct TrainingResult(
    TrainingEnding Ending,
    IReadOnlyList<TrainingTarget> Targets,
    double TotalSeconds,
    double TotalDistanceM,
    long AtpWarningEvents,
    long AtpInterventionEvents,
    long AtpEmergencyEvents)
{
    /// <summary>
    /// Czy sesja jest zaliczona. WYPROWADZONE z <see cref="Ending"/>, a nie osobne
    /// pole — patrz opis <see cref="TrainingEnding"/>.
    /// </summary>
    public bool Passed => Ending == TrainingEnding.AllTargetsServed;

    /// <summary>Ile celów obsłużono.</summary>
    public int TargetsServed
    {
        get
        {
            var served = 0;
            foreach (var target in Targets)
            {
                if (target.Served)
                {
                    served++;
                }
            }

            return served;
        }
    }

    /// <summary>
    /// Jeden wiersz wyniku; kultura niezmienna, żeby wyjście nie zależało od maszyny.
    ///
    /// <para><b>Po co ta linia istnieje.</b> Porównanie dwóch wyników przez <c>==</c>
    /// rekordu porównałoby <see cref="Targets"/> REFERENCJĄ, a dwa przebiegi tego samego
    /// zapisu wejść dają dwie listy — więc <c>==</c> powiedziałoby „różne" o wynikach
    /// identycznych. Ta linia jest kompletna i porównywalna znak w znak, i to ona jest
    /// wspólnym językiem bramki scena–rdzeń.</para>
    /// </summary>
    public override string ToString()
    {
        var wiersz = string.Create(
            CultureInfo.InvariantCulture,
            $"{(Passed ? "zaliczone" : "niezaliczone")} ({Ending}): " +
            $"{TargetsServed}/{Targets.Count} celów, {TotalSeconds:F3} s, " +
            $"{TotalDistanceM:F3} m, ATP {AtpWarningEvents}/{AtpInterventionEvents}/" +
            $"{AtpEmergencyEvents}");

        foreach (var target in Targets)
        {
            wiersz += string.Create(
                CultureInfo.InvariantCulture,
                $" | {target.StopId} {(target.Served ? "obsłużony" : "pominięty")} " +
                $"błąd {(target.StopErrorM is { } błąd ? $"{błąd:+0.000;-0.000;0.000} m" : "—")}");
        }

        return wiersz;
    }
}
