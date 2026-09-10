using System.Collections.Generic;
using System.Linq;
using Godot;
using MetroBxl.Game.UI;

namespace MetroBxl.Game.Input;

/// <summary>
/// Jedno przypisanie sterowania: akcja <c>InputMap</c>, klawisz, którym maszynista ją
/// wywołuje, i to, co ten klawisz robi.
///
/// <para><b>Kody klawiszy są FIZYCZNE</b> — po położeniu na klawiaturze, nie po znaku.
/// W Brukseli to nie jest szczegół: AZERTY ma <c>W</c> tam, gdzie QWERTY ma <c>Z</c>,
/// a nastawnik ciągu ma zostać pod tym samym palcem. Odpowiada za to
/// <c>physical_keycode</c> w <c>project.godot</c>, i tego pilnuje
/// <c>DriverActionsTests</c>.</para>
/// </summary>
/// <param name="Action">Nazwa akcji w <c>InputMap</c>, np. <c>driver_power</c>.</param>
/// <param name="KeyName">
/// Nazwa klawisza w wierszu pomocy, np. <c>W</c>. <b>Zostaje tutaj, a nie idzie do
/// katalogu tekstów</b> (6.D99): to napis na klawiszu, nie zdanie po polsku, a dla
/// nazw jednoliterowych <c>DriverActionsTests</c> porównuje go wprost
/// z <c>physical_keycode</c>.
/// </param>
/// <param name="Meaning">
/// Co ten klawisz robi — treść do wiersza pomocy. <b>Idzie z katalogu</b>
/// (<see cref="MetroBxl.Game.UI.UiText"/>) od 6.D99, bo to jest zdanie po polsku.
/// </param>
/// <param name="PhysicalKeycodes">
/// Kody fizyczne, jakie akcja ma mieć przypisane w <c>project.godot</c>. Pierwszy jest
/// tym, który wymienia <paramref name="KeyName"/>; dalsze to warianty (strzałki).
/// </param>
public sealed record DriverBinding(
    string Action,
    string KeyName,
    string Meaning,
    IReadOnlyList<int> PhysicalKeycodes);

/// <summary>
/// Sterowanie jako DANE: nazwy akcji <c>InputMap</c>, klawisze pod nimi i opis do HUD-u,
/// w jednym miejscu i bez Godota.
///
/// <para><b>Po co osobny plik.</b> Do 05.09.2026 sterowanie było rozsypane po trzech
/// miejscach, które nic o sobie nie wiedziały: <c>DriverInput.Read</c> czytało kody
/// klawiszy wprost (<c>Godot.Input.IsPhysicalKeyPressed(Key.W)</c>),
/// <c>FirstRun.HandleViewKeys</c> czytało kolejne trzy, a <c>DriverInput.Help</c>
/// opisywało je napisem, którego <b>nic nie wołało</b>. Trzy kopie tej samej wiedzy
/// rozjeżdżają się przy pierwszej zmianie klawisza — i to nie jest hipoteza: opis mówił
/// o klawiszu awaryjnym dopisanym „na zapas", bo nie było jak sprawdzić, czy zgadza się
/// z odczytem.</para>
///
/// <para><b>Dlaczego bez Godota.</b> Ta sama zasada, co w <see cref="RunPlan"/>,
/// <see cref="RunHeader"/> i <see cref="EmergencyBrake"/>: tabela, która ma mówić prawdę
/// o <c>project.godot</c>, da się przybić testem tylko wtedy, gdy jej przeczytanie nie
/// wymaga uruchomionego silnika. <c>tests/Game.Tests</c> czyta stąd listę akcji i
/// porównuje ją z plikiem projektu — z tym samym plikiem, który wczytuje silnik.
/// Typ <c>Godot.Key</c> jest tu wyłącznie <b>stałą kompilacji</b> (<c>(int)Key.W</c>
/// to w IL liczba 87), więc odczyt tabeli nie ładuje ani jednej klasy silnika.</para>
///
/// <para><b>Czego tu nie ma.</b> Nowych poleceń sterujących — drzwi, przejęcia składu,
/// osobnego stopnia awaryjnego. Tabela opisuje DOKŁADNIE to, co scena robiła przed tą
/// zmianą, tylko przez <c>InputMap</c> zamiast po kodach klawiszy; hamulec awaryjny jest
/// w niej dlatego, że istniał już wcześniej (<see cref="EmergencyBrake"/>), a nie
/// dlatego, że tu powstaje.</para>
/// </summary>
public static class DriverActions
{
    /// <summary>Nastawnik jazdy w górę.</summary>
    public const string Power = "driver_power";

    /// <summary>Hamulec służbowy w górę.</summary>
    public const string Brake = "driver_brake";

    /// <summary>Wybieg — obie dźwignie do zera.</summary>
    public const string Coast = "driver_coast";

    /// <summary>Hamulec awaryjny; robi to samo, co pełny służbowy.</summary>
    public const string Emergency = "driver_emergency";

    /// <summary>Przełączenie widoku kabina/goniący.</summary>
    public const string ViewToggle = "view_toggle";

    /// <summary>Przejazd od nowa.</summary>
    public const string Reset = "run_reset";

    /// <summary>Wyjście ze sceny.</summary>
    public const string Quit = "run_quit";

    /// <summary>
    /// Rozdzielacz między pozycjami wiersza pomocy. Dwie spacje z każdej strony, bo
    /// wiersz jest jednym napisem w jednym <c>Label</c> i musi się dać przeczytać
    /// wzrokiem z fotela, a nie kursorem.
    /// </summary>
    public const string HelpSeparator = "  ·  ";

    /// <summary>
    /// Wszystkie przypisania, w kolejności, w jakiej wychodzą do wiersza pomocy:
    /// najpierw prowadzenie, potem obsługa przejazdu.
    /// </summary>
    public static readonly IReadOnlyList<DriverBinding> All = new[]
    {
        // Strzałki obok liter, bo tak było przed przejściem na `InputMap` i zadanie G-3
        // nie zmienia sterowania, tylko sposób jego czytania.
        new DriverBinding(
            Power, "W", UiText.Get("input.power"), new[] { (int)Key.W, (int)Key.Up }),
        new DriverBinding(
            Brake, "S", UiText.Get("input.brake"), new[] { (int)Key.S, (int)Key.Down }),
        new DriverBinding(Coast, "X", UiText.Get("input.coast"), new[] { (int)Key.X }),

        // Nazwa klawisza przychodzi z `EmergencyBrake`, a nie jest tu wpisana drugi raz:
        // wiersz HUD-u o trzymanym hamulcu i wiersz pomocy mają mówić o tym samym
        // klawiszu z definicji, a nie przez zgodność dwóch napisów.
        new DriverBinding(
            Emergency,
            EmergencyBrake.KeyName,
            UiText.Get("input.emergency"),
            new[] { (int)Key.Space }),
        new DriverBinding(ViewToggle, "C", UiText.Get("input.view"), new[] { (int)Key.C }),
        new DriverBinding(Reset, "R", UiText.Get("input.reset"), new[] { (int)Key.R }),

        // Esc też idzie przez `InputMap`, choć kryterium zadania dopuszczało zostawienie
        // go na surowym kodzie. Powód jest testowy, nie estetyczny: „zero odczytów
        // klawiszy w src/Game" jest warunkiem, który da się sprawdzić bez wyjątku
        // dopisanego do wzorca, a wyjątek w bramce to miejsce, którym wraca to, co
        // bramka miała wykluczyć.
        new DriverBinding(Quit, "Esc", UiText.Get("input.quit"), new[] { (int)Key.Escape }),
    };

    /// <summary>
    /// Opis sterowania do wypisania w HUD — składany z <see cref="All"/>, a nie wpisany
    /// obok niej.
    ///
    /// <para>To jest cała treść tej właściwości: napis o klawiszach i przypisania
    /// klawiszy mają jedno źródło. Zmiana klawisza w tabeli przechodzi do wiersza pomocy
    /// i do <c>project.godot</c> naraz albo nie przechodzi nigdzie — a poprzednia wersja
    /// tego opisu była osobną stałą, więc mogła (i musiała) rozjechać się cicho.</para>
    /// </summary>
    public static string Help { get; } =
        string.Join(HelpSeparator, All.Select(binding => $"{binding.KeyName} {binding.Meaning}"));

    /// <summary>
    /// Akcje, które w przejeździe prowadzonym przez rdzeń (<c>--line</c>) NIE DZIAŁAJĄ,
    /// choć scena je odczytuje.
    ///
    /// <para><b>Skąd to się wzięło.</b> W trybie <c>--line</c> skład prowadzi
    /// <c>LineDrive</c>: <c>StepOnce</c> nadpisuje stan składu z <c>_line.State</c>,
    /// więc polecenie maszynisty nie dojeżdża do fizyki, a reset przejazdu jest
    /// cofany w następnym kroku. Do 05.09.2026 HUD wypisywał nad takim przejazdem ten
    /// sam wiersz pomocy, co nad przejazdem gracza — czyli obiecywał siedem klawiszy,
    /// z których działały dwa. <c>reports/droga-do-grywalnosci.md</c> §5.4 nazywał to
    /// „bezgłośnie bezskuteczne"; decyzja właściciela z 05.09.2026 brzmi: zachowanie
    /// zostaje, ale HUD ma to powiedzieć.</para>
    ///
    /// <para>Lista jest tu, a nie w scenie, z tego samego powodu, co cała tabela: żeby
    /// dało się ją przeczytać bez uruchomionego silnika i przybić testem. Test pilnuje
    /// też, że ta lista i <see cref="All"/> DZIELĄ zbiór akcji na dwie części bez reszty
    /// — dopisanie klawisza wymaga wtedy rozstrzygnięcia, po której stronie stoi,
    /// zamiast cichego wpadnięcia do tej, która akurat jest domyślna.</para>
    /// </summary>
    public static readonly IReadOnlyList<string> TakenOverByTheCore = new[]
    {
        Power, Brake, Coast, Emergency, Reset,
    };

    /// <summary>
    /// Opis sterowania dla przejazdu prowadzonego przez rdzeń — składany z tej samej
    /// tabeli, co <see cref="Help"/>.
    ///
    /// <para>Wymienia klawisze, które DZIAŁAJĄ, i osobno mówi, które przejął rdzeń.
    /// Nie jest to skrócony <see cref="Help"/>: pominięcie klawiszy bez słowa
    /// zostawiłoby gracza z pytaniem, czemu ich nie ma, a wypisanie ich razem z resztą
    /// jest obietnicą, której ten tryb nie dotrzymuje.</para>
    /// </summary>
    public static string HelpWhenTheCoreDrives { get; } = BuildCoreDrivesHelp();

    private static string BuildCoreDrivesHelp()
    {
        var taken = new HashSet<string>(TakenOverByTheCore);
        var working = All.Where(binding => !taken.Contains(binding.Action));
        var inactive = All.Where(binding => taken.Contains(binding.Action));

        return string.Join(HelpSeparator, working.Select(b => $"{b.KeyName} {b.Meaning}"))
            + HelpSeparator
            + UiText.Format(
                "help.core-drives", string.Join(", ", inactive.Select(b => b.KeyName)));
    }
}
