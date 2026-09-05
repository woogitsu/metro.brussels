using System;
using System.Collections.Generic;
using MetroBxl.Game.Input;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game;

/// <summary>
/// Stan przejazdu, który mieszka w WARTOŚCIACH — to, czym reset nadpisuje pola sceny.
///
/// <para>Rekord, a nie sześć osobnych stałych, z jednego powodu: reset ma być czymś,
/// co da się WYWOŁAĆ i SPRAWDZIĆ, a nie listą przypisań w metodzie węzła Godota.
/// Poprzednia wersja była taką listą i dlatego brakowało w niej trzech pozycji naraz
/// (<c>StationService</c>, polecenie po filtrze stacji, przyspieszenie), a żaden test
/// nie miał czego złapać.</para>
/// </summary>
/// <param name="Drive">Stan składu: zero kroków, zero drogi, zero prędkości.</param>
/// <param name="Keys">Klawisze odczytane w tej klatce.</param>
/// <param name="ActiveKeys">Klawisze ostatniego wykonanego kroku — to, co czyta HUD.</param>
/// <param name="Command">Położenie dźwigni maszynisty.</param>
/// <param name="EffectiveCommand">Polecenie po filtrze stacji, czyli wejście fizyki.</param>
/// <param name="AccelerationMps2">Przyspieszenie ostatniego kroku.</param>
public readonly record struct RunStart(
    DriveState Drive,
    DriverKeys Keys,
    DriverKeys ActiveKeys,
    DriverCommand Command,
    DriverCommand EffectiveCommand,
    double AccelerationMps2);

/// <summary>
/// Reset przejazdu (akcja <c>run_reset</c>, klawisz <c>R</c>) jako JEDNA funkcja, która
/// rozstrzyga, co reset obejmuje — i jako jedyne miejsce, w którym ta odpowiedź stoi.
///
/// <para><b>Skąd to się wzięło.</b> Do 05.09.2026 reset był sześcioma przypisaniami
/// w <c>FirstRun.HandleViewKeys</c> i zerował stan dynamiczny składu, nie dotykając
/// obsługi stacji. Skutek, opisany w <c>reports/droga-do-grywalnosci.md</c> §5.4
/// i w zadaniu G-4: skład wracał na 94,0 m z kolejką stacji ustawioną tam, dokąd
/// dojechał, a <c>StationService._next</c> idzie tylko w przód — pominiętych peronów
/// nie dało się już obsłużyć. <b>Trwający cykl drzwi przeżywał reset</b>, czyli po
/// „przejeździe od nowa" trakcja bywała zablokowana w tunelu, a licznik postoju szedł
/// dalej z poprzedniego przejazdu.</para>
///
/// <para><b>Dlaczego bez Godota.</b> Ta sama zasada, co w <see cref="RunPlan"/>,
/// <see cref="RunHeader"/> i <see cref="DriverActions"/>: <c>FirstRun</c> jest węzłem
/// silnika i żaden test jednostkowy go nie wywoła, więc wiedza, którą trzeba przybić
/// testem, musi wyjść z węzła. Tutaj wychodzi cała: <see cref="Apply"/> zeruje stan
/// mieszkający w OBIEKTACH (akumulator, nastawnik, obsługa stacji, zapis wejść,
/// telemetria) i zwraca stan mieszkający w WARTOŚCIACH. Scenie zostaje sześć przypisań
/// z jednego rekordu i ani jednej decyzji.</para>
///
/// <para><b>Czego reset NIE obejmuje i dlaczego.</b> Osi, składu, warunków przejazdu,
/// planu sygnalizacji, widoku kamery ani licznika klatek sceny. Pierwsze cztery to
/// NASTAWY przejazdu — reset jest „ten sam przejazd od nowa", a nie „inny przejazd".
/// Widok jest własnością patrzącego, nie przejazdu (klawisz <c>C</c> działa niezależnie).
/// Licznik klatek jest zegarem węzła, a nie stanem symulacji: kroki liczy
/// <see cref="DriveState.Steps"/> i to on wraca do zera.</para>
/// </summary>
public static class RunReset
{
    /// <summary>
    /// Stan wartościowy na początku przejazdu. <see cref="DriveState.AtRest"/> to zero
    /// kroków, zero drogi i zero prędkości; dźwignie na wybiegu, klawisze puszczone.
    /// </summary>
    public static RunStart Values => new(
        RunRestart.Values.Drive,
        DriverKeys.None,
        DriverKeys.None,
        RunRestart.Values.Command,
        RunRestart.Values.Command,
        RunRestart.Values.AccelerationMps2);

    /// <summary>
    /// Zeruje cały stan przejazdu i zwraca wartości, którymi wołający ma nadpisać swoje.
    ///
    /// <para>Argumenty dopuszczające <c>null</c> to te, których dany tryb przejazdu może
    /// nie mieć: obsługa stacji istnieje tylko w trybie ręcznym, zapis wejść tylko przy
    /// <c>--input-log</c>, telemetria tylko przy <c>--telemetry</c>. Brak obiektu jest
    /// tu poprawnym stanem, a nie błędem — inaczej reset w trybie <c>--line</c>
    /// przewracałby scenę.</para>
    /// </summary>
    /// <param name="accumulator">Akumulator kroków; nierozliczona reszta czasu znika.</param>
    /// <param name="notch">Dźwignia maszynisty; wraca na wybieg.</param>
    /// <param name="input">Odczyt klawiatury; zapomina ostatni stan klawiszy.</param>
    /// <param name="stations">Obsługa stacji albo <c>null</c> poza trybem ręcznym.</param>
    /// <param name="recorder">Zapis wejść albo <c>null</c>, gdy przejazd go nie zbiera.</param>
    /// <param name="telemetry">Zebrane wiersze telemetrii albo <c>null</c>.</param>
    /// <returns>Wartości stanu przejazdu po resecie.</returns>
    /// <exception cref="ArgumentNullException">Akumulator, nastawnik albo odczyt klawiatury jest <c>null</c>.</exception>
    public static RunStart Apply(
        StepAccumulator accumulator,
        DriverNotch notch,
        DriverInput input,
        StationService? stations,
        InputLogRecorder? recorder,
        IList<string>? telemetry)
    {
        ArgumentNullException.ThrowIfNull(accumulator);
        ArgumentNullException.ThrowIfNull(notch);
        ArgumentNullException.ThrowIfNull(input);

        // Nierozliczona reszta czasu klatki należała do poprzedniego przejazdu.
        // Przeniesiona dalej dołożyłaby nowemu przejazdowi krok, którego nikt nie zamówił.
        accumulator.DropCarry();

        // Dźwignia, obsługa stacji, telemetria i stan składu — czyli wszystko, co ma
        // także rdzeń bez silnika. Ta lista NIE jest tu powtórzona: `Sim.Runner replay`
        // odtwarza ten sam zapis wejść i musi zresetować dokładnie to samo, a dwie listy
        // rozjechałyby się po cichu (`RunRestart`).
        var core = RunRestart.Apply(notch, stations, telemetry);

        // ZAPIS WEJŚĆ ZOSTAJE I DOSTAJE WPIS. Do 05.09.2026 stało tu `recorder?.Clear()`,
        // bo licznik kroków przejazdu wracał do zera i dalsze nagrywanie nadpisywałoby
        // numery, które już padły. Decyzja właściciela (wariant W1) rozdzieliła te dwie
        // liczby: zapis indeksuje SESJĘ i nie wraca nigdy, `DriveState.Steps` indeksuje
        // PRZEJAZD i zaczyna od zera. Dzięki temu przejazd z resetem odtwarza się z pliku.
        recorder?.RecordReset();

        input.Clear();
        return new RunStart(
            core.Drive,
            DriverKeys.None,
            DriverKeys.None,
            core.Command,
            core.Command,
            core.AccelerationMps2);
    }

    /// <summary>
    /// Zdejmuje z telemetrii próbki, zostawiając sam wiersz nagłówka —
    /// <see cref="RunRestart.DropSamples"/> pod nazwą, której używa scena.
    /// </summary>
    /// <param name="telemetry">Zebrane wiersze albo <c>null</c>.</param>
    public static void DropSamples(IList<string>? telemetry) => RunRestart.DropSamples(telemetry);
}
