using System;
using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game;

/// <summary>
/// Nagłówek przebiegu — jeden wiersz <c>[PRZEJAZD]</c>, który scena wypisuje po
/// zbudowaniu symulacji.
///
/// <para><b>Dlaczego to jest osobny plik BEZ GODOTA.</b> Ta sama decyzja i ten sam
/// powód, co przy <see cref="RunPlan"/>: nagłówek jest tekstem złożonym z liczb
/// przebiegu, a złożenie liczb da się sprawdzić testem jednostkowym tylko wtedy, gdy
/// nie wymaga uruchomionego silnika. Póki składanie tego wiersza siedziało w metodzie
/// węzła <c>Node3D</c>, pilnował go wyłącznie ludzki wzrok czytający log.</para>
///
/// <para><b>Co ten plik naprawia.</b> Zmierzone 04.09.2026: przy
/// <c>--line --limit-kmh=70</c> nagłówek wypisywał <c>limit=80.0 km/h</c>, a skład
/// w tym samym przebiegu rozpędzał się do 70,00 km/h na dziewięciu z jedenastu
/// odcinków (<c>[STACJA] ... szczyt 70.00 km/h</c>). Powód: pole brało liczbę
/// z <c>DriveScenario.SpeedLimitMps</c>, czyli z rejestru pojazdu — 80 km/h to
/// prędkość KONSTRUKCYJNA M7 (<c>design_model</c>), nie ograniczenie na torze
/// i nie argument, którym jedzie rdzeń. Liczba w napisie nie była wynikiem niczego,
/// więc nic jej nie porównywało.</para>
///
/// <para><b>Reguła, z której to wynika.</b> Każda liczba w nagłówku jest CZYTANA
/// z obiektu, który prowadzi przebieg — nie liczona obok niego. Limit z prowadzenia
/// (<see cref="LineCore.SpeedLimitMps"/> / <see cref="LineDrive.SpeedLimitMps"/>),
/// krok z <see cref="FixedStep"/> podanego rdzeniowi, masa z
/// <see cref="RunConditions"/> podanych rdzeniowi. Kopia obok byłaby drugą prawdą
/// i rozjechałaby się dokładnie tak, jak rozjechał się limit.</para>
/// </summary>
public static class RunHeader
{
    /// <summary>
    /// Ograniczenie prędkości, którym NAPRAWDĘ jedzie ten przebieg.
    ///
    /// <para>Kolejność nie jest dowolna. <see cref="LineCore"/> idzie pierwszy, bo
    /// w przejeździe z sygnalizacją prowadzenie składu (<see cref="LineDrive"/>)
    /// powstaje leniwie — dopiero w pierwszym kroku, w fazie wyjazdów — a nagłówek
    /// leci przed nim. To jest ta sama kolejność warunków, którą ma <c>StepOnce</c>
    /// i <c>FastForwardToShot</c> w <c>FirstRun.cs</c>, i z tego samego powodu.</para>
    ///
    /// <para>Scenariusz jest OSTATNI i wyłącznie dla trybu ręcznego i skryptowego —
    /// tam limit ze scenariusza jest tym, którym jedzie kontroler, bo <c>--limit-kmh</c>
    /// się z tymi trybami nie łączy (<see cref="RunPlan"/> odmawia). Przejazd linią bez
    /// prowadzenia z rdzenia nie ma prawa dostać tu wartości domyślnej: cichy odwrót na
    /// 80 km/h jest dokładnie tą usterką, którą ten plik naprawia, więc jest tu
    /// wyjątkiem, a nie liczbą.</para>
    /// </summary>
    /// <param name="lineMode">Czy to przejazd linią (<c>--line</c>).</param>
    /// <param name="scenario">Scenariusz przebiegu ręcznego i skryptowego.</param>
    /// <param name="core">Linia z sygnalizacją albo <c>null</c>.</param>
    /// <param name="line">Prowadzenie tego składu albo <c>null</c>.</param>
    public static double SpeedLimitMps(
        bool lineMode, DriveScenario scenario, LineCore? core, LineDrive? line)
    {
        ArgumentNullException.ThrowIfNull(scenario);

        if (core is not null)
        {
            return core.SpeedLimitMps;
        }

        if (line is not null)
        {
            return line.SpeedLimitMps;
        }

        if (lineMode)
        {
            throw new ArgumentException(
                "Przejazd linią bez prowadzenia z rdzenia nie ma skąd wziąć limitu, "
                + "a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7, nie "
                + "ograniczenie na torze.",
                nameof(lineMode));
        }

        return scenario.SpeedLimitMps;
    }

    /// <summary>
    /// Wiersz <c>[PRZEJAZD]</c>. Limit dobiera <see cref="SpeedLimitMps"/> — nagłówek
    /// nie przyjmuje go parametrem, bo parametr znaczyłby, że ktoś na zewnątrz może
    /// podać liczbę inną niż ta, którą jedzie rdzeń.
    /// </summary>
    /// <param name="plan">Rozstrzygnięty wiersz poleceń: tryb i to, czy jedzie linia.</param>
    /// <param name="view">Widok aktywny w chwili wypisania nagłówka.</param>
    /// <param name="scenario">Scenariusz przebiegu ręcznego i skryptowego.</param>
    /// <param name="step">Krok stały, którym idzie rdzeń — nie stała klasy.</param>
    /// <param name="conditions">Warunki podane rdzeniowi: masa, pochylenie, przyczepność.</param>
    /// <param name="core">Linia z sygnalizacją albo <c>null</c>.</param>
    /// <param name="line">Prowadzenie tego składu albo <c>null</c>.</param>
    public static string Line(
        RunPlan plan,
        ViewKind view,
        DriveScenario scenario,
        FixedStep step,
        RunConditions conditions,
        LineCore? core,
        LineDrive? line)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(scenario);
        ArgumentNullException.ThrowIfNull(conditions);

        var limitMps = SpeedLimitMps(plan.LineMode, scenario, core, line);
        return string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZEJAZD] tryb={plan.Mode} widok={view} scenariusz={scenario.Id} " +
            $"krok=1/{step.Hertz} s masa={conditions.MassKg:F0} kg " +
            $"limit={Units.MpsToKmh(limitMps):F1} km/h");
    }
}
