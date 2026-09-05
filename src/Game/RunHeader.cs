using System;
using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
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
    /// <para><b>Tryb RĘCZNY bierze limit z PLANU SYGNALIZACJI, nie ze scenariusza.</b>
    /// Decyzja właściciela z 05.09.2026: kabina jedzie tym samym limitem, co autopilot
    /// pod sygnalizacją, czyli 72,00 km/h z planu <c>classic-2026</c>. Do tego dnia
    /// jechała 80 km/h ze scenariusza — czyli prędkością KONSTRUKCYJNĄ M7, i to jest ta
    /// sama usterka, którą ten plik naprawił dla <c>--line</c>, tyle że ścieżka ręczna
    /// została wtedy pominięta. Liczba nie jest tu wpisana: przychodzi
    /// <see cref="SignallingPlan.PermittedSpeedMps"/> z pliku, który to samo repozytorium
    /// podaje autopilotowi pod <c>--signalling</c>, więc drugiej kopii nie ma gdzie
    /// trzymać.</para>
    ///
    /// <para><b>Wyjątek: kabina POD OCHRONĄ ma sufit maszynisty.</b> Gdy tryb ręczny
    /// dostał plan argumentem (<see cref="RunPlan.ManualSignalling"/>) i podano
    /// <c>--limit-kmh</c>, kontroler jedzie tą liczbą, a prędkość dopuszczalna z planu
    /// zostaje tym, czego PILNUJE ochrona. Nagłówek pokazuje wtedy sufit, bo to on jest
    /// liczbą, którą naprawdę dostaje rdzeń — czyli ta sama zasada, która stoi za całym
    /// tym plikiem, a nie odstępstwo od niej. Prędkość dopuszczalna ma swój własny
    /// wiersz: <c>[SYGNALIZACJA]</c> w logu i <c>v_dop</c> w HUD-zie.</para>
    ///
    /// <para>Scenariusz jest OSTATNI i wyłącznie dla trybu SKRYPTOWEGO
    /// (<c>--telemetry</c>, <c>--shot</c>) — tam limit ze scenariusza jest tym, którym
    /// jedzie <c>ScenarioDrive</c> w rdzeniu, a telemetria sceny jest z rdzeniem
    /// porównywana CO DO BITU. Ani przejazd linią bez prowadzenia z rdzenia, ani
    /// przejazd ręczny bez planu nie mają prawa dostać tu wartości domyślnej: cichy
    /// odwrót na 80 km/h jest dokładnie tą usterką, którą ten plik naprawia, więc oba
    /// są wyjątkiem, a nie liczbą.</para>
    /// </summary>
    /// <param name="plan">Rozstrzygnięty wiersz poleceń: tryb przebiegu.</param>
    /// <param name="scenario">Scenariusz przebiegu skryptowego.</param>
    /// <param name="core">Linia z sygnalizacją albo <c>null</c>.</param>
    /// <param name="line">Prowadzenie tego składu albo <c>null</c>.</param>
    /// <param name="manualPlan">
    /// Plan sygnalizacji, z którego tryb ręczny bierze prędkość dopuszczalną; wczytuje
    /// go scena z <see cref="RunPlan.ManualSpeedLimitPlanPath"/>. Poza trybem ręcznym
    /// i odtworzeniem jest <c>null</c> i nie jest czytany.
    /// </param>
    /// <exception cref="ArgumentException">
    /// Przejazd linią bez prowadzenia z rdzenia albo przejazd ręczny bez planu.
    /// </exception>
    public static double SpeedLimitMps(
        RunPlan plan, DriveScenario scenario, LineCore? core, LineDrive? line,
        SignallingPlan? manualPlan)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(scenario);

        if (core is not null)
        {
            return core.SpeedLimitMps;
        }

        if (line is not null)
        {
            return line.SpeedLimitMps;
        }

        if (plan.LineMode)
        {
            throw new ArgumentException(
                "Przejazd linią bez prowadzenia z rdzenia nie ma skąd wziąć limitu, "
                + "a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7, nie "
                + "ograniczenie na torze.",
                nameof(plan));
        }

        if (plan.ScriptedMode)
        {
            return scenario.SpeedLimitMps;
        }

        // TRYB RĘCZNY POD OCHRONĄ: `--limit-kmh` jest tu SUFITEM MASZYNISTY, a nie
        // prędkością dopuszczalną. Kontroler dostaje sufit, bo tyle wolno maszyniście
        // POPROSIĆ; prędkości dopuszczalnej pilnuje ochrona z planu i to ona wychodzi
        // w wierszu HUD-u jako `v_dop`. Rozdzielenie tych dwóch liczb jest jedynym
        // sposobem, żeby ingerencja ATP mogła się w ogóle zdarzyć — przy suficie równym
        // limitowi planu sterownik nie przekroczy 72,00 km/h, więc ochrona nie ma czego
        // łapać (`docs/15-classic-signalling.md` §5, wiersz „72,0 km/h": 0/0).
        //
        // Warunek stoi PRZED odmową „przejazd ręczny bez planu", nie za nią, i to nie
        // jest kolejność dowolna: `RunPlan` dopuszcza `--limit-kmh` w trybie ręcznym
        // WYŁĄCZNIE razem z `--signalling`, więc plan tu wtedy jest — ten podany
        // argumentem. Sufit bez planu nie przejdzie przez `RunPlan.Parse` w ogóle.
        if (plan.ManualSignalling && plan.LimitKmh > 0.0)
        {
            return Units.KmhToMps(plan.LimitKmh);
        }

        if (manualPlan is null)
        {
            throw new ArgumentException(
                "Przejazd ręczny bez planu sygnalizacji nie ma skąd wziąć limitu, "
                + "a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7, nie "
                + "ograniczenie na torze.",
                nameof(manualPlan));
        }

        return manualPlan.PermittedSpeedMps;
    }

    /// <summary>
    /// Wiersz <c>[PRZEJAZD]</c>. Limit dobiera <see cref="SpeedLimitMps"/> — nagłówek
    /// nie przyjmuje go parametrem, bo parametr znaczyłby, że ktoś na zewnątrz może
    /// podać liczbę inną niż ta, którą jedzie rdzeń.
    /// </summary>
    /// <param name="plan">Rozstrzygnięty wiersz poleceń: tryb i to, czy jedzie linia.</param>
    /// <param name="view">Widok aktywny w chwili wypisania nagłówka.</param>
    /// <param name="scenario">Scenariusz przebiegu skryptowego.</param>
    /// <param name="step">Krok stały, którym idzie rdzeń — nie stała klasy.</param>
    /// <param name="conditions">Warunki podane rdzeniowi: masa, pochylenie, przyczepność.</param>
    /// <param name="core">Linia z sygnalizacją albo <c>null</c>.</param>
    /// <param name="line">Prowadzenie tego składu albo <c>null</c>.</param>
    /// <param name="manualPlan">Plan, z którego limit bierze tryb ręczny; poza nim <c>null</c>.</param>
    public static string Line(
        RunPlan plan,
        ViewKind view,
        DriveScenario scenario,
        FixedStep step,
        RunConditions conditions,
        LineCore? core,
        LineDrive? line,
        SignallingPlan? manualPlan)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(scenario);
        ArgumentNullException.ThrowIfNull(conditions);

        var limitMps = SpeedLimitMps(plan, scenario, core, line, manualPlan);
        return string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZEJAZD] tryb={plan.Mode} widok={view} scenariusz={scenario.Id} " +
            $"krok=1/{step.Hertz} s masa={conditions.MassKg:F0} kg " +
            $"limit={Units.MpsToKmh(limitMps):F1} km/h");
    }
}
