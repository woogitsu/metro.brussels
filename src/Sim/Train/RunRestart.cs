using System;
using System.Collections.Generic;
using MetroBxl.Sim.Signalling;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Stan przejazdu po resecie, który mieszka w WARTOŚCIACH — to, czym wołający ma
/// nadpisać swoje pola.
/// </summary>
/// <param name="Drive">Stan składu: zero kroków, zero drogi, zero prędkości.</param>
/// <param name="Command">Położenie dźwigni maszynisty.</param>
/// <param name="AccelerationMps2">Przyspieszenie ostatniego kroku.</param>
public readonly record struct RunRestartValues(
    DriveState Drive,
    DriverCommand Command,
    double AccelerationMps2);

/// <summary>
/// Co znaczy „przejazd od nowa" dla RDZENIA — jedna odpowiedź dla wszystkich, którzy
/// ten rdzeń prowadzą.
///
/// <para><b>Po co osobny plik, skoro <c>Game.RunReset</c> już istnieje.</b> Bo od
/// 05.09.2026 reset przejazdu jest wpisem w zapisie wejść (decyzja właściciela W1),
/// a zapis wejść odtwarzają DWIE strony bramki CI: scena (<c>src/Game/FirstRun.cs</c>)
/// i rdzeń bez silnika (<c>Sim.Runner replay</c>). Gdyby każda z nich miała własną
/// listę „co reset zeruje", bramka porównywałaby dwie różne definicje resetu i
/// zgadzałaby się dokładnie do pierwszej rozbieżności — a wtedy nie odpowiadałaby już
/// na pytanie, o które ją zapytano. <c>Sim.Runner</c> nie może zobaczyć
/// <c>src/Game</c> (mieszka tam Godot, <c>CLAUDE.md</c> §4.9), więc wspólna odpowiedź
/// musi leżeć tutaj.</para>
///
/// <para><b>Podział jest po tym, kto co ma.</b> Tutaj stoi wszystko, co ma rdzeń:
/// dźwignia, obsługa stacji, ochrona pociągu kabiny, stan składu i zebrane wiersze
/// telemetrii. <c>Game.RunReset</c> dokłada to, czego rdzeń nie zna: akumulator kroków
/// klatki, odczyt klawiatury i zapis wejść — i woła tę funkcję zamiast powtarzać jej
/// treść.</para>
///
/// <para><b>Ochrona kabiny doszła tu 05.09.2026 razem z G-5 i nie jest wyjątkiem od
/// zdania wyżej — jest jego kolejnym przypadkiem.</b> <c>CabProtection</c> trzyma stan
/// SYGNALIZACJI przejazdu: położenie składu na planie, zaryglowane trasy, liczniki
/// ingerencji. Bez zresetowania go pierwszy meldunek ruchu po resecie skończyłby się
/// wyjątkiem, bo <c>FixedBlockSystem.MoveTrain</c> odmawia cofnięcia czoła — model nie
/// odtacza składów w tył. A gdyby zerowała go tylko scena, <c>Sim.Runner replay</c>
/// odtwarzałby ten sam zapis wejść z inną sygnalizacją i bramka przy progu 0 zgadzałaby
/// się dokładnie do pierwszego kroku, w którym ochrona ingeruje.</para>
///
/// <para><b>Czego reset NIE obejmuje:</b> osi, składu, warunków przejazdu ani planu
/// sygnalizacji. To są NASTAWY przejazdu, a reset znaczy „ten sam przejazd od nowa",
/// nie „inny przejazd".</para>
/// </summary>
public static class RunRestart
{
    /// <summary>
    /// Stan wartościowy na początku przejazdu: skład stoi, dźwignie na wybiegu,
    /// przyspieszenie zerowe.
    /// </summary>
    public static RunRestartValues Values => new(DriveState.AtRest, DriverCommand.Coast, 0.0);

    /// <summary>
    /// Zeruje stan rdzenia i zwraca wartości, którymi wołający ma nadpisać swoje.
    /// </summary>
    /// <param name="notch">Dźwignia maszynisty; wraca na wybieg.</param>
    /// <param name="stations">Obsługa stacji albo <c>null</c>, gdy przejazd jej nie ma.</param>
    /// <param name="cab">
    /// Ochrona pociągu kabiny albo <c>null</c>, gdy przejazd jedzie bez sygnalizacji.
    /// Brak obiektu jest tu poprawnym stanem, a nie błędem — tak samo jak brak obsługi
    /// stacji poza trybem ręcznym.
    /// </param>
    /// <param name="telemetry">Zebrane wiersze telemetrii albo <c>null</c>.</param>
    /// <param name="session">
    /// Sesja treningowa albo <c>null</c>, gdy przejazd jej nie ma (skryptowy, liniowy,
    /// z telemetrii). Brak obiektu jest tu poprawnym stanem — tak samo jak brak obsługi
    /// stacji i brak ochrony kabiny, i z tego samego powodu.
    /// </param>
    /// <returns>Wartości stanu przejazdu po resecie.</returns>
    /// <exception cref="ArgumentNullException">Dźwignia jest <c>null</c>.</exception>
    public static RunRestartValues Apply(
        DriverNotch notch,
        StationService? stations,
        CabProtection? cab,
        IList<string>? telemetry,
        TrainingSession? session = null)
    {
        ArgumentNullException.ThrowIfNull(notch);

        var start = Values;

        // Dźwignia wraca na wybieg tą samą drogą, co przy starcie: `Set`, a nie przesuw.
        // Reset jest przestawieniem pulpitu, a nie jazdą do zera.
        notch.Set(start.Command);

        // Cała obsługa stacji od nowa — kolejka, rejestry wywołań i minięć, trwający
        // cykl drzwi. To jest usterka G-4 i to jest miejsce, w którym była.
        stations?.Reset();

        // Sygnalizacja kabiny od nowa: skład wraca na kilometraż startu, trasy i bloki
        // są puste, liczniki ingerencji zerowe. Bez tego reset byłby WYJĄTKIEM, a nie
        // resetem — patrz akapit przy klasie.
        cab?.Reset();

        // SESJA TRENINGOWA OD NOWA — wynik znika, liczniki zdarzeń ATP wracają do zera,
        // pamięć zboczy do fałszu. Cele zostają: reset znaczy „ta sama sesja od nowa",
        // a nie „inne zadanie", dokładnie tak samo jak oś i skład nie wracają tu do
        // wyboru. Argument stoi TUTAJ, a nie obok w scenie, z tego samego powodu, co
        // `cab` przy G-5: reset jest wpisem w zapisie wejść (decyzja W1), a zapis
        // odtwarzają DWIE strony bramki — scena i `Sim.Runner replay`. Dwie listy „co
        // reset zeruje" zgodziłyby się dokładnie do pierwszego resetu po pierwszym celu.
        session?.Reset();

        DropSamples(telemetry);
        return start;
    }

    /// <summary>
    /// Zdejmuje z telemetrii próbki, zostawiając sam wiersz nagłówka.
    ///
    /// <para>Po resecie numery kroków przejazdu zaczynają się od zera, więc wiersze
    /// sprzed resetu opisywałyby inny przejazd tymi samymi numerami. Nagłówek zostaje —
    /// jest opisem pliku, a nie próbką przejazdu.</para>
    ///
    /// <para>Lista pusta znaczy „przejazd nie zbiera telemetrii" i wychodzi z tego
    /// pusta — dopisanie nagłówka tutaj byłoby włączeniem zapisu, o który nikt
    /// nie prosił.</para>
    /// </summary>
    /// <param name="telemetry">Zebrane wiersze albo <c>null</c>.</param>
    public static void DropSamples(IList<string>? telemetry)
    {
        if (telemetry is null)
        {
            return;
        }

        while (telemetry.Count > 1)
        {
            telemetry.RemoveAt(telemetry.Count - 1);
        }
    }
}
