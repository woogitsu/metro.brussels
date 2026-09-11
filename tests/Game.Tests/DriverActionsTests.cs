using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Godot;
using MetroBxl.Game.Input;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Sterowanie przez <c>InputMap</c> (zadanie G-3, Issue #26 §Sterowanie).
///
/// <para><b>Czego te testy pilnują.</b> Nie tego, że akcje istnieją — tego, że
/// <c>src/Game/project.godot</c> i <c>DriverActions</c> mówią o TYCH SAMYCH klawiszach.
/// Plik projektu czyta silnik, tabelę czyta kod sceny i wiersz pomocy w HUD-zie;
/// rozjazd między nimi nie ma jak rzucić się w oczy, bo sterowanie działa dalej — tylko
/// pod innym klawiszem niż ten, który HUD obiecuje graczowi.</para>
///
/// <para><b>Dlaczego test czyta plik z drzewa repozytorium, a nie zasób silnika.</b>
/// <c>tests/Game.Tests</c> chodzi bez Godota. Gdyby czytał przypisania przez
/// <c>InputMap</c>, musiałby uruchomić silnik, a wtedy przestałby być testem
/// jednostkowym i nie odróżniałby braku wpisu od braku silnika. Czytany jest ten sam
/// plik, który wczytuje silnik, i to jest cały dowód.</para>
/// </summary>
[TestClass]
public sealed class DriverActionsTests
{
    /// <summary>Jedno zdarzenie klawiszowe wyjęte z <c>project.godot</c>.</summary>
    /// <param name="Keycode">Kod po ZNAKU; ma być zerem.</param>
    /// <param name="PhysicalKeycode">Kod po POŁOŻENIU; ma być niezerowy.</param>
    /// <param name="Device">Urządzenie; <c>-1</c> znaczy „dowolne".</param>
    private sealed record MappedEvent(int Keycode, int PhysicalKeycode, int Device);

    /// <summary>
    /// Sekcja <c>[input]</c> z <c>src/Game/project.godot</c>: akcja → jej zdarzenia,
    /// w kolejności zapisu.
    /// </summary>
    private static IReadOnlyDictionary<string, IReadOnlyList<MappedEvent>> InputMapFromProject()
    {
        var path = Path.Combine(RepositoryRoot(), "src", "Game", "project.godot");
        Assert.IsTrue(File.Exists(path), path);
        var text = File.ReadAllText(path);

        var section = Regex.Match(text, @"^\[input\]\r?$(.*?)(?=^\[|\z)", RegexOptions.Multiline | RegexOptions.Singleline);
        Assert.IsTrue(section.Success, $"{path} nie ma sekcji [input]");

        var result = new Dictionary<string, IReadOnlyList<MappedEvent>>(StringComparer.Ordinal);
        foreach (Match entry in Regex.Matches(
            section.Groups[1].Value,
            @"^(?<name>[A-Za-z_][A-Za-z0-9_]*)=\{(?<body>.*?)^\}",
            RegexOptions.Multiline | RegexOptions.Singleline))
        {
            var events = new List<MappedEvent>();
            foreach (Match device in Regex.Matches(entry.Groups["body"].Value, @"Object\(InputEventKey,(?<fields>[^)]*)\)"))
            {
                var fields = device.Groups["fields"].Value;
                events.Add(new MappedEvent(
                    Field(fields, "keycode"),
                    Field(fields, "physical_keycode"),
                    Field(fields, "device")));
            }

            result[entry.Groups["name"].Value] = events;
        }

        return result;
    }

    private static int Field(string fields, string name)
    {
        var match = Regex.Match(fields, $"\"{name}\":(?<value>-?[0-9]+)");
        Assert.IsTrue(match.Success, $"brak pola \"{name}\" w zdarzeniu: {fields}");
        return int.Parse(match.Groups["value"].Value, System.Globalization.CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Każda akcja z tabeli sterowania ma w <c>project.godot</c> przypisanie, i to
    /// DOKŁADNIE te klawisze, które tabela deklaruje.
    ///
    /// <para>„Co najmniej jedno przypisanie" nie wystarcza: akcja <c>driver_power</c>
    /// z samą strzałką w górę przeszłaby taki test, a wiersz pomocy dalej mówiłby „W
    /// ciąg" — i to jest dokładnie ten rozjazd, którego nie widać w grze.</para>
    /// </summary>
    [TestMethod]
    public void KazdaAkcjaSterowaniaMaWProjectGodotDokladnieSwojeKlawisze()
    {
        var mapped = InputMapFromProject();

        foreach (var binding in DriverActions.All)
        {
            Assert.IsTrue(
                mapped.ContainsKey(binding.Action),
                $"brak akcji '{binding.Action}' w [input]; są: {string.Join(", ", mapped.Keys)}");

            CollectionAssert.AreEqual(
                binding.PhysicalKeycodes.ToArray(),
                mapped[binding.Action].Select(e => e.PhysicalKeycode).ToArray(),
                $"akcja '{binding.Action}' ma inne klawisze niż tabela DriverActions");
        }
    }

    /// <summary>
    /// Sekcja <c>[input]</c> nie zawiera akcji spoza tabeli — lista sterowania ma jedno
    /// źródło w obie strony, nie tylko od tabeli do pliku.
    /// </summary>
    [TestMethod]
    public void ProjectGodotNieMaAkcjiSpozaTabeliSterowania()
    {
        var mapped = InputMapFromProject();
        var known = DriverActions.All.Select(binding => binding.Action).ToHashSet(StringComparer.Ordinal);
        var extra = mapped.Keys.Where(name => !known.Contains(name)).OrderBy(name => name, StringComparer.Ordinal).ToArray();

        Assert.AreEqual(0, extra.Length, $"akcje w project.godot spoza DriverActions.All: {string.Join(", ", extra)}");
        Assert.AreEqual(DriverActions.All.Count, mapped.Count, "liczba akcji w [input] nie zgadza się z tabelą");
    }

    /// <summary>
    /// Każde przypisanie jest FIZYCZNE i dla DOWOLNEGO urządzenia.
    ///
    /// <para>Dwie liczby, obie zmierzone w Godocie 4.7.2, obie łatwe do zepsucia bez
    /// żadnego objawu w pliku:</para>
    ///
    /// <para><c>keycode</c> niezerowe przy zerowym <c>physical_keycode</c> znaczy
    /// „klawisz po znaku". Na AZERTY, w Brukseli nieprzypadkowym, nastawnik ciągu
    /// przeniósłby się wtedy pod inny palec — a na maszynie z QWERTY, czyli na tej,
    /// na której to się pisze, nie byłoby tego widać.</para>
    ///
    /// <para><c>device</c> inne niż <c>-1</c> nie łapie zdarzenia z klawiatury.
    /// <c>ProjectSettings.save()</c> zapisuje świeży <c>InputEventKey</c> z
    /// <c>"device":16</c>; zmierzone na <c>InputMap.event_is_action</c>: mapa 16 ×
    /// zdarzenie 0 daje <c>false</c>, mapa −1 × zdarzenie 0 daje <c>true</c>. Sterowanie
    /// wygenerowane przez silnik byłoby więc sterowaniem, które w pliku wygląda
    /// poprawnie i nie reaguje na klawisz.</para>
    /// </summary>
    [TestMethod]
    public void KazdePrzypisanieJestFizyczneIDlaDowolnegoUrzadzenia()
    {
        foreach (var (action, events) in InputMapFromProject())
        {
            Assert.AreNotEqual(0, events.Count, $"akcja '{action}' nie ma ani jednego zdarzenia");
            foreach (var mapped in events)
            {
                Assert.AreEqual(0, mapped.Keycode, $"'{action}': przypisanie po ZNAKU (keycode={mapped.Keycode})");
                Assert.AreNotEqual(0, mapped.PhysicalKeycode, $"'{action}': brak physical_keycode");
                Assert.AreEqual(-1, mapped.Device, $"'{action}': device={mapped.Device} nie łapie klawiatury (ma być -1)");
            }
        }
    }

    /// <summary>
    /// Nazwa klawisza w wierszu pomocy zgadza się z kodem, który idzie do
    /// <c>project.godot</c> — dla nazw jednoliterowych, czyli dla W, S, X, C i R.
    ///
    /// <para>Kody fizyczne liter są kodami ASCII wielkich liter, więc porównanie jest
    /// tu możliwe bez drugiej tablicy nazw.</para>
    ///
    /// <para><b>Akapit niżej jest PRZEPISANY, a nie dopisany obok (6.D116).</b>
    /// Poprzednia wersja mówiła, że nazwy złożone („Spacja", „Esc") ten test pomija
    /// świadomie, bo ich odpowiednikiem byłaby druga kopia mapowania nazwa → kod.
    /// Skutek był taki, że <b>dwie z siedmiu nazw nie były przybite do niczego</b>:
    /// podmiana <c>"Esc"</c> na <c>"Escape"</c> nie zapalała żadnej bramki. Obie są
    /// dziś przybite w
    /// <see cref="NazwyBezLitery_sa_przybite_do_kodow_fizycznych"/>, a druga kopia
    /// mapowania rzeczywiście tam stoi — <b>z ręki, i to jest jej cała wartość</b>:
    /// porównanie <see cref="KeyNames"/> z <see cref="KeyNames"/> nie sprawdziłoby
    /// niczego. Ten sam wzorzec co pin napisów w 6.D99.</para>
    /// </summary>
    [TestMethod]
    public void JednoliterowaNazwaKlawiszaZgadzaSieZJegoKodemFizycznym()
    {
        var checkedNames = 0;
        foreach (var binding in DriverActions.All.Where(b => b.KeyName.Length == 1))
        {
            Assert.AreEqual(
                (int)binding.KeyName[0],
                binding.PhysicalKeycodes[0],
                $"'{binding.Action}': wiersz pomocy mówi '{binding.KeyName}', a kod to {binding.PhysicalKeycodes[0]}");
            checkedNames++;
        }

        Assert.AreEqual(5, checkedNames, "zmieniła się liczba jednoliterowych klawiszy sterowania");
    }

    /// <summary>
    /// Kod fizyczny → oczekiwana nazwa, <b>wpisane z ręki</b>. Pin, nie wyprowadzenie.
    ///
    /// <para>Dwie pary, bo tyle jest nazw, których nie da się odczytać z kodu. Zbiór
    /// jest tu domknięty w obie strony: każdy wpis <see cref="KeyNames.Znane"/> musi
    /// mieć tu parę i odwrotnie — inaczej dopisanie klawisza do tabeli produkcyjnej
    /// przechodziłoby bez ani jednego sprawdzenia, czyli dokładnie tak, jak przez
    /// ostatnie dwa dni przechodziły „Esc" i „Spacja".</para>
    /// </summary>
    private static readonly (Key Kod, string Nazwa)[] OczekiwaneNazwy =
    {
        (Key.Escape, "Esc"),
        (Key.Space, "Spacja"),
    };

    [TestMethod]
    public void NazwyBezLitery_sa_przybite_do_kodow_fizycznych()
    {
        CollectionAssert.AreEquivalent(
            OczekiwaneNazwy.Select(o => o.Kod).ToList(),
            KeyNames.Znane.ToList(),
            "tabela nazw klawiszy rozjechała się z pinem w teście — dopisany klawisz "
            + "byłby poza kontrolą tak samo, jak Esc i Spacja przed 6.D116");

        foreach (var (kod, nazwa) in OczekiwaneNazwy)
        {
            Assert.AreEqual(nazwa, KeyNames.For(kod),
                $"klawisz o kodzie fizycznym {(int)kod} ({kod}) nazywa się "
                + $"'{KeyNames.For(kod)}', a wiersz pomocy ma mówić '{nazwa}'");
        }
    }

    [TestMethod]
    public void Kazda_nazwa_z_tabeli_przypisan_jest_przybita_do_swojego_kodu()
    {
        // Siedem wierszy, siedem sprawdzeń — żadnego pominiętego. Litera idzie przez
        // kod ASCII, reszta przez pin wyżej; pominięcie któregokolwiek wiersza jest
        // tu BŁĘDEM, a nie wyborem, i dlatego licznik stoi obok pętli.
        var sprawdzone = 0;
        foreach (var binding in DriverActions.All)
        {
            var kod = (Key)binding.PhysicalKeycodes[0];
            var oczekiwana = binding.KeyName.Length == 1
                ? ((char)binding.PhysicalKeycodes[0]).ToString()
                : OczekiwaneNazwy.Single(o => o.Kod == kod).Nazwa;

            Assert.AreEqual(oczekiwana, binding.KeyName,
                $"'{binding.Action}': wiersz pomocy mówi '{binding.KeyName}', "
                + $"a kod fizyczny {(int)kod} ({kod}) nazywa się '{oczekiwana}'");
            sprawdzone++;
        }

        Assert.AreEqual(DriverActions.All.Count, sprawdzone,
            "pętla nie dotknęła wszystkich wierszy tabeli przypisań");
        Assert.AreEqual(7, sprawdzone, "zmieniła się liczba przypisań sterowania");
    }

    /// <summary>
    /// Wiersz pomocy wymienia KAŻDĄ akcję z tabeli — nazwę klawisza i to, co robi.
    /// </summary>
    [TestMethod]
    public void WierszPomocyWymieniaKazdaAkcjeZTabeli()
    {
        var help = DriverActions.Help;

        foreach (var binding in DriverActions.All)
        {
            StringAssert.Contains(help, $"{binding.KeyName} {binding.Meaning}", help);
        }

        Assert.AreEqual(
            DriverActions.All.Count - 1,
            Regex.Matches(help, Regex.Escape(DriverActions.HelpSeparator)).Count,
            help);
    }

    /// <summary>
    /// <c>DriverInput.Help</c> przestał być osobnym napisem: pokazuje to, co składa
    /// tabela sterowania. Stała, która żyła obok tabeli, rozjechałaby się z nią cicho.
    /// </summary>
    [TestMethod]
    public void OpisSterowaniaWDriverInputPochodziZTabeli()
    {
        Assert.AreEqual(DriverActions.Help, DriverInput.Help);
    }

    /// <summary>
    /// Wiersz pomocy wychodzi na ekran DOKŁADNIE w tych przebiegach, w których scena
    /// czyta klawiaturę.
    ///
    /// <para>To jest ta sama decyzja, którą pętla klatek podejmuje przed wołaniem
    /// <c>DriverInput.Read</c>, i dlatego mieszka w jednym miejscu
    /// (<c>RunPlan.ReadsKeyboard</c>). Przebieg z <c>--shot</c> ma wyjść z HUD-em
    /// identycznym jak przed dopisaniem wiersza: progi bramki
    /// <c>tools/visual/compare.py --set godot</c> są zmierzone na klatce z samym
    /// HUD-em i stały napis podniósłby dokładnie tę metrykę, którą ta bramka odrzuca
    /// pustą klatkę.</para>
    /// </summary>
    [TestMethod]
    public void PomocWychodziTylkoWPrzejezdzieProwadzonymZKlawiatury()
    {
        Assert.IsTrue(Plan().ReadsKeyboard, "przejazd ręczny");
        Assert.IsTrue(Plan("--line", "--limit-kmh=72").ReadsKeyboard, "przejazd linią — C i R działają");
        Assert.IsFalse(Plan("--shot=/tmp/a.png", "--at-chainage=2000").ReadsKeyboard, "zrzut");
        Assert.IsFalse(Plan("--telemetry=/tmp/a.csv").ReadsKeyboard, "telemetria");
        Assert.IsFalse(Plan("--replay=/tmp/a.log").ReadsKeyboard, "odtworzenie z zapisu wejść");
        Assert.IsFalse(
            Plan("--line", "--limit-kmh=72", "--shot=/tmp/a.png").ReadsKeyboard,
            "zrzut z przejazdu linią");
    }

    /// <summary>
    /// W <c>src/Game</c> nie został ani jeden odczyt klawisza po kodzie — poza prozą
    /// w komentarzach, która o nim OPOWIADA.
    ///
    /// <para>To jest bramka zakazu, nie asercja na napisie w kodzie: sprawdza, że
    /// czegoś NIE MA. Odczyt po kodzie działa i przechodzi każdy test funkcjonalny,
    /// tylko na innym układzie klawiatury robi co innego — więc jedynym miejscem, gdzie
    /// da się to złapać, jest właśnie skan źródeł.</para>
    /// </summary>
    [TestMethod]
    public void ZadenPlikSrcGameNieCzytaKlawiszyPoKodzie()
    {
        var root = Path.Combine(RepositoryRoot(), "src", "Game");
        var offenders = new List<string>();

        foreach (var file in Directory.EnumerateFiles(root, "*.cs", SearchOption.AllDirectories))
        {
            // `.godot/` trzyma źródła generowane przez silnik przy imporcie projektu —
            // nie są częścią tej warstwy i nie ma ich w repozytorium.
            if (file.Contains($"{Path.DirectorySeparatorChar}.godot{Path.DirectorySeparatorChar}", StringComparison.Ordinal)
                || file.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.Ordinal))
            {
                continue;
            }

            var number = 0;
            foreach (var line in File.ReadAllLines(file))
            {
                number++;
                var code = line.TrimStart();
                if (code.StartsWith("//", StringComparison.Ordinal))
                {
                    continue;
                }

                if (code.Contains("IsPhysicalKeyPressed", StringComparison.Ordinal)
                    || code.Contains("IsKeyPressed", StringComparison.Ordinal))
                {
                    offenders.Add($"{Path.GetRelativePath(root, file)}:{number}: {code}");
                }
            }
        }

        Assert.AreEqual(0, offenders.Count, string.Join("\n", offenders));
    }

    /// <summary>
    /// Scena ma etykietę, w której ten wiersz się pokazuje. Bez węzła
    /// <c>Hud/Panel/Rows/Help</c> <c>Hud._Ready</c> nie ma czego pobrać, a opis
    /// sterowania nie ma gdzie wyjść — i byłby dalej stałą, której nikt nie widzi.
    /// </summary>
    [TestMethod]
    public void ScenaMaWierszPomocyWPanelu()
    {
        var path = Path.Combine(RepositoryRoot(), "src", "Game", "Scenes", "FirstRun.tscn");
        var text = File.ReadAllText(path);

        StringAssert.Contains(
            text,
            "[node name=\"Help\" type=\"Label\" parent=\"Hud/Panel/Rows\"]",
            path);
    }

    private static RunPlan Plan(params string[] arguments) => RunPlan.Parse(arguments, 8, 9);

    private static string RepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "CLAUDE.md")))
            {
                return directory.FullName;
            }

            directory = directory.Parent;
        }

        Assert.Inconclusive("Test uruchomiony poza drzewem repozytorium.");
        throw new InvalidOperationException();
    }

    /// <summary>
    /// Wiersz pomocy pod <c>--line</c> ma mówić PRAWDĘ o tym trybie: skład prowadzi
    /// <c>LineDrive</c>, więc z siedmiu klawiszy działają dwa.
    ///
    /// <para>Test nie sprawdza brzmienia napisu — sprawdza, że każdy przejęty klawisz
    /// jest w nim nazwany po stronie „nie działają", a żaden działający nie wpadł tam
    /// przez pomyłkę. Asercja na cały napis pękałaby przy każdej zmianie interpunkcji
    /// i zostałaby przepisana bez patrzenia, co jest dokładnie tym trybem cichej awarii,
    /// przed którym ten plik broni.</para>
    /// </summary>
    [TestMethod]
    public void PodAutopilotemPomocNazywaKlawiszeKtoreNieDzialaja()
    {
        var pomoc = DriverActions.HelpWhenTheCoreDrives;
        var przejete = new HashSet<string>(DriverActions.TakenOverByTheCore);

        var ogon = pomoc[(pomoc.IndexOf("prowadzi rdzeń:", StringComparison.Ordinal))..];

        foreach (var binding in DriverActions.All)
        {
            if (przejete.Contains(binding.Action))
            {
                StringAssert.Contains(
                    ogon, binding.KeyName,
                    $"klawisz '{binding.KeyName}' nie działa pod --line, a pomoc o tym nie mówi");
                Assert.IsFalse(
                    pomoc.Contains($"{binding.KeyName} {binding.Meaning}", StringComparison.Ordinal),
                    $"pomoc obiecuje '{binding.KeyName} {binding.Meaning}', a ten klawisz nie działa");
            }
            else
            {
                StringAssert.Contains(
                    pomoc, $"{binding.KeyName} {binding.Meaning}",
                    $"klawisz '{binding.KeyName}' działa pod --line, a pomoc go nie wymienia");
            }
        }
    }

    /// <summary>
    /// Podział akcji na przejęte przez rdzeń i działające pod <c>--line</c> jest
    /// WYPISANY TU IMIENNIE — obie strony, po nazwie.
    ///
    /// <para><b>Dlaczego imiennie, a nie regułą.</b> Pierwsza wersja tego testu
    /// sprawdzała, że dwie listy „pokrywają tabelę bez reszty", i jej docstring głosił,
    /// że dzięki temu dopisanie klawisza wymusza decyzję. <b>Nie wymuszało.</b> Warunek
    /// arytmetyczny <c>|All| − |przejęte| = |All \ przejęte|</c> jest prawdziwy dla
    /// KAŻDEGO nowego wpisu, więc klawisz dopisany do <see cref="DriverActions.All"/>
    /// wpadał po cichu po stronie „działa" i pomoc obiecywała go pod <c>--line</c> —
    /// nie dlatego, że ktoś tak postanowił, tylko dlatego, że nikt nie został o to
    /// zapytany. Test przechodził. To jest dokładnie ta rodzina usterek, którą ten
    /// projekt goni: kontrola, która mówi „ok" także wtedy, gdy nic nie sprawdza.</para>
    ///
    /// <para>Dwie wypisane listy są brzydsze i działają: nowy klawisz wywala ten test,
    /// a jego autor musi dopisać go po jednej ze stron, czyli odpowiedzieć na pytanie,
    /// czy pod <c>--line</c> ten klawisz coś robi.</para>
    /// </summary>
    [TestMethod]
    public void KazdaAkcjaStoiPoDokladnieJednejStronie()
    {
        var wszystkie = DriverActions.All.Select(b => b.Action).ToList();

        CollectionAssert.AreEqual(
            new List<string>
            {
                DriverActions.Power, DriverActions.Brake, DriverActions.Coast,
                DriverActions.Emergency, DriverActions.ViewToggle,
                DriverActions.Reset, DriverActions.Quit,
            },
            wszystkie,
            "tabela przypisań się zmieniła — rozstrzygnij, po której stronie stoi nowy klawisz");

        CollectionAssert.AreEqual(
            new List<string>
            {
                DriverActions.Power, DriverActions.Brake, DriverActions.Coast,
                DriverActions.Emergency, DriverActions.Reset,
            },
            new List<string>(DriverActions.TakenOverByTheCore),
            "lista klawiszy przejętych przez rdzeń się zmieniła");

        foreach (var action in DriverActions.TakenOverByTheCore)
        {
            CollectionAssert.Contains(
                wszystkie, action,
                $"'{action}' jest na liście przejętych, a nie ma go w tabeli przypisań");
        }
    }
}
