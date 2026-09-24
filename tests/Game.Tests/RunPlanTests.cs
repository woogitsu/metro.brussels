using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Game;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Testy rozstrzygania wiersza poleceń sceny (<see cref="RunPlan"/>).
///
/// <para><b>Dlaczego ten plik istnieje.</b> <c>FirstRun.cs</c> ma 847 linii i do
/// 03.09.2026 <c>grep -rn "FirstRun" tests/</c> nie dawał ANI JEDNEGO trafienia.
/// Jedyne, co pilnowało tej klasy, to asercje na napisach w kodzie źródłowym,
/// pisane w Pythonie: <c>assert "_line!.Step(" in text</c>. Test, który sprawdza
/// obecność napisu w pliku <c>.cs</c>, nie odróżnia kodu wykonywanego od
/// zakomentowanego i nie dotyka ani jednej gałęzi.</para>
///
/// <para>Trzy usterki, które tą dziurą przeszły, mają tu po teście z osobna. Nie są
/// wymyślone — każda jest opisana w komentarzu w kodzie, z datą pomiaru.</para>
/// </summary>
[TestClass]
public sealed class RunPlanTests
{
    private const int UnknownArgument = 8;
    private const int BadArgumentValue = 9;

    private static RunPlan Parse(params string[] arguments)
        => RunPlan.Parse(arguments, UnknownArgument, BadArgumentValue);

    // --- domyślne wartości --------------------------------------------------------

    [TestMethod]
    public void NoArgumentsGivesTheManualMode()
    {
        var plan = Parse();

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("manual", plan.Mode);
        Assert.IsFalse(plan.ScriptedMode);
        Assert.IsNull(plan.TelemetryPath);
        Assert.IsNull(plan.ShotPath);
        Assert.AreEqual(ViewKind.Cab, plan.View);
    }

    [TestMethod]
    public void DefaultsAreThePinnedOnes()
    {
        var plan = Parse();

        Assert.AreEqual(RunPlan.DefaultSampleEvery, plan.SampleEvery);
        Assert.AreEqual(RunPlan.DefaultStepsPerFrame, plan.StepsPerFrame);
        Assert.AreEqual(120L, plan.SampleEvery, "120 kroków to jedna sekunda przy 1/120 s");
        Assert.AreEqual(120L, plan.StepsPerFrame);
        Assert.AreEqual(0.0, plan.Jitter);
        Assert.AreEqual(0.0, plan.ShotChainageM);
    }

    // --- USTERKA 1: literówka w nazwie argumentu ----------------------------------

    /// <summary>
    /// Zmierzone 02.09.2026 audytem mutacyjnym: <c>--at-chainag=2000</c>, literówka na
    /// JEDNYM znaku, kończyło się kodem 0 i zrzutem o nazwie <c>GODOT_cab_2000m.png</c>
    /// przedstawiającym stojący skład na 94 m. Pięć „ujęć kontrolnych" mogło więc być
    /// pięcioma kopiami tego samego kadru, a wszystkie opisy kamer z <c>cameras.json</c>
    /// były niesprawdzalnymi deklaracjami.
    /// </summary>
    [TestMethod]
    public void ATypoInAnArgumentNameStopsTheRun()
    {
        var plan = Parse("--at-chainag=2000");

        Assert.IsFalse(plan.IsValid, "literówka przeszła jako poprawny argument");
        Assert.AreEqual(UnknownArgument, plan.ExitCode);
        StringAssert.Contains(plan.Error, "at-chainag");
        StringAssert.Contains(plan.Error, "Znane: --", "komunikat ma wypisać, co jest znane");
    }

    [TestMethod]
    public void TheCorrectlySpelledArgumentGoesThrough()
    {
        var plan = Parse("--at-chainage=2000");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual(2000.0, plan.ShotChainageM);
    }

    [TestMethod]
    public void EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds()
    {
        // Przepisane 04.09.2026, gdy doszły trzy argumenty z PRAWDZIWĄ zależnością:
        // `--line` bez `--limit-kmh` musi odmówić (limit nie ma źródła, R-006, a domyślne
        // 80 km/h to prędkość konstrukcyjna pojazdu), a `--calls` i `--limit-kmh` bez
        // `--line` nic by nie robiły. Poprzednia wersja tego testu twierdziła, że KAŻDY
        // znany argument działa samotnie — po tych trzech przestało to być prawdą.
        //
        // Test jest teraz MOCNIEJSZY, nie słabszy: argument z zależnością musi odmówić
        // KOMUNIKATEM WYMIENIAJĄCYM towarzysza, a nie zostać po cichu zignorowany.
        // Argument, który nic nie robi, jest gorszy od nieznanego: nieznany zatrzymuje
        // przebieg, a bezczynny wygląda jak działający.
        var towarzysz = new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["line"] = new[] { "--limit-kmh=70" },
            ["limit-kmh"] = new[] { "--line" },
            ["calls"] = new[] { "--line", "--limit-kmh=70" },
            ["scheduled-entries"] = new[] { "--line", "--limit-kmh=70", "--signalling=x" },
        };

        // `--signalling` ZESZŁO z tej listy 05.09.2026 i to jest treść G-5, a nie
        // rozluźnienie testu: plan podany samotnie znaczy „kabina jedzie pod tym
        // planem" — bloki, autorytet jazdy i ATP ingerujące w polecenie człowieka —
        // więc argument nie jest już bezczynny. Że nadal jest bezczynny w przebiegu
        // SKRYPTOWYM i tam odmawia, pilnuje `SignallingWithoutLineIsTheCabUnderSignalling`.

        var samotnych = 0;
        var zZaleznoscia = 0;

        foreach (var name in RunPlan.KnownArguments)
        {
            var value = name switch
            {
                "sample-every" or "steps-per-frame" or "headway-steps" => "10",
                // `--trains` MUSI dostać wartość z zakresu 1..MaxTrains, bo poza nim
                // plan odmawia — a ten test pyta, czy argument DZIAŁA SAMOTNIE, nie czy
                // odrzuca bzdury. Od tego jest osobna asercja przy `MaxTrains`.
                "trains" => "2",
                "jitter" or "at-chainage" => "1.5",
                "view" => "cab",
                "limit-kmh" => "70",
                _ => "x",
            };

            if (!towarzysz.TryGetValue(name, out var potrzebne))
            {
                var plan = Parse($"--{name}={value}");
                Assert.IsTrue(plan.IsValid, $"--{name}={value}: {plan.Error}");
                samotnych++;
                continue;
            }

            var samotny = Parse($"--{name}={value}");
            Assert.IsFalse(samotny.IsValid, $"--{name} przeszło samotnie, choć wymaga towarzysza");
            foreach (var wymagany in potrzebne)
            {
                var goly = wymagany.Split('=')[0];
                Assert.IsTrue(samotny.Error!.Contains(goly) || samotny.Error!.Contains($"--{name}"),
                    $"komunikat dla --{name} nie wymienia ani siebie, ani {goly}: {samotny.Error}");
            }

            var lista = new List<string> { $"--{name}={value}" };
            lista.AddRange(potrzebne);
            var razem = Parse(lista.ToArray());
            Assert.IsTrue(razem.IsValid, $"--{name} z towarzyszem nadal odmawia: {razem.Error}");
            zZaleznoscia++;
        }

        // POMIAR, nie ozdoba (6.D31): wszystkie asercje tego testu stoją w pętli po
        // `RunPlan.KnownArguments`, więc opróżniona tablica dawałaby test zielony
        // bez ani jednej wykonanej asercji. Liczby niżej są ZMIERZONE przebiegiem,
        // nie policzone z tablicy w kodzie — dlatego rozjazd w którąkolwiek stronę
        // (argument dopisany, usunięty, przesunięty między rodzinami) jest tu FAIL-em,
        // a nie cichą zmianą pokrycia.
        // 17 -> 18 (14.09.2026, MB-05): `--cab`. Argument SAMOTNY, tak jak `--shell`
        // i `--platforms`, bo jest tym samym: ścieżką do bryły wczytywanej przez
        // scenę, i nie wymaga żadnego towarzysza. Że ta liczba drgnęła, jest tu
        // dowodem, a nie kosztem: `FirstRun` czytało `--cab` już wcześniej, a plan
        // odrzucał je jako nieznane — nadpisanie było nieosiągalne i żaden test
        // tego nie widział, bo nikt tego argumentu nie podawał.
        // 18 -> 20 (14.09.2026, MB-07): `--trains` i `--headway-steps`. Oba SAMOTNE
        // i oba LICZBOWE, więc na liście `PathArguments` ich nie ma i być nie powinno —
        // tamta mówi o kształcie WARTOŚCI, a pusta wartość liczbowa odpada już na
        // `TryLong`. Zakres `--trains` sprawdza osobna asercja przy `MaxTrains`.
        Assert.AreEqual(20, samotnych, "argumentów bez zależności");
        Assert.AreEqual(4, zZaleznoscia, "argumentów z zależnością");
        Assert.AreEqual(
            RunPlan.KnownArguments.Length, samotnych + zZaleznoscia,
            "pętla nie odwiedziła każdego znanego argumentu");
    }

    // --- USTERKA 2: nieznany widok -------------------------------------------------

    /// <summary>
    /// Zmierzone: <c>--view=zmyslony</c> CICHO spadało do widoku z kabiny. Zrzut
    /// nazwany „z zewnątrz" mógł więc być kolejnym kadrem z kabiny i nikt by tego nie
    /// zauważył po nazwie pliku — bo nazwę pliku podaje wołający, a nie scena.
    /// </summary>
    [TestMethod]
    public void AnUnknownViewIsRefusedInsteadOfFallingBackToTheCab()
    {
        var plan = Parse("--view=zmyslony");

        Assert.IsFalse(plan.IsValid, "nieznany widok cicho spadł do kabiny");
        Assert.AreEqual(BadArgumentValue, plan.ExitCode);
        StringAssert.Contains(plan.Error, "zmyslony");
    }

    [TestMethod]
    public void EachKnownViewMapsToItsOwnKind()
    {
        Assert.AreEqual(ViewKind.Cab, Parse("--view=cab").View);
        Assert.AreEqual(ViewKind.Chase, Parse("--view=chase").View);
        Assert.AreEqual(ViewKind.Outside, Parse("--view=outside").View);
        Assert.AreEqual(ViewKind.Inspect, Parse("--view=inspect").View);
    }

    /// <summary>
    /// KAŻDY znany widok ma własny <see cref="ViewKind"/> — i to jest liczone
    /// z <see cref="RunPlan.KnownViews"/>, nie wypisane.
    ///
    /// <para><b>Skąd ten test.</b> Test wyżej wymienia widoki z ręki, więc dopisanie
    /// piątego do <c>KnownViews</c> bez gałęzi w <c>switch</c> przeszłoby go: nowa
    /// nazwa spadłaby na <c>_ => ViewKind.Cab</c> i scena CICHO dałaby kabinę.
    /// Dokładnie ta usterka jest opisana przy 6.C4 dla <c>--view=zmyslony</c>, tylko
    /// tam nazwa była nieznana, a tu byłaby znana i milcząca. Liczba widoków
    /// jest POMIAREM tablicy, a różnorodność rodzajów — jej sprawdzeniem.</para>
    /// </summary>
    [TestMethod]
    public void ZadenZnanyWidokNieSpadaCichoDoKabiny()
    {
        var rodzaje = new List<ViewKind>();
        foreach (var view in RunPlan.KnownViews)
        {
            var plan = Parse($"--view={view}");
            Assert.IsTrue(plan.IsValid, $"--view={view} stoi w KnownViews, a nie przeszło");
            rodzaje.Add(plan.View);
        }

        Assert.AreEqual(RunPlan.KnownViews.Length, rodzaje.Distinct().Count(),
            "dwie znane nazwy widoku dają ten sam ViewKind — któraś spada na gałąź "
            + "domyślną i scena cicho podstawia inny widok: " + string.Join(", ", rodzaje));
    }

    /// <summary>
    /// Widok inspekcyjny jest CZWARTY, a nie podmienionym trzecim: trzy widoki jazdy
    /// zostają w tablicy i zachowują swoje rodzaje. Bez tego testu poprawka
    /// przestawiająca kolejność albo podmieniająca nazwę przeszłaby wszystko wyżej.
    /// </summary>
    [TestMethod]
    public void Widok_inspekcyjny_dochodzi_do_trzech_a_nie_zamiast()
    {
        CollectionAssert.AreEqual(
            new[] { "cab", "chase", "outside", "inspect" },
            RunPlan.KnownViews,
            "kolejność i skład KnownViews: " + string.Join(", ", RunPlan.KnownViews));
    }

    /// <summary>Wielkość liter ma znaczenie: „Cab" nie jest „cab" i ma być odmową.</summary>
    [TestMethod]
    public void ViewMatchingIsCaseSensitive()
    {
        foreach (var view in new[] { "Cab", "CAB", "Outside" })
        {
            var plan = Parse($"--view={view}");
            Assert.IsFalse(plan.IsValid, $"--view={view} przeszło");
        }
    }

    // --- USTERKA 3: wartość, która nie jest skończoną liczbą ----------------------

    /// <summary>
    /// Zmierzone: <c>--at-chainage=abc</c> rzucało wyjątkiem w środku <c>_Ready</c>,
    /// gdy <c>_shotPath</c> było już ustawione — a wtedy <c>_Process</c> wchodziło
    /// w odliczanie od <c>int.MaxValue</c> i kręciło się w nieskończoność. Nie dawało
    /// ani PNG-a, ani kodu błędu: w CI to wypalony <c>timeout-minutes: 45</c>
    /// bez informacji, o co chodziło.
    /// </summary>
    [TestMethod]
    public void AChainageThatIsNotANumberIsRefusedWithItsValue()
    {
        var plan = Parse("--at-chainage=abc");

        Assert.IsFalse(plan.IsValid, "śmieciowy kilometraż przeszedł");
        Assert.AreEqual(BadArgumentValue, plan.ExitCode);
        StringAssert.Contains(plan.Error, "abc", "komunikat ma pokazać, co dostał");
        StringAssert.Contains(plan.Error, "skończoną");
    }

    /// <summary>
    /// <c>double.TryParse</c> SAM NIE WYSTARCZA i to jest sedno tej usterki:
    /// przyjmuje „Infinity" i „NaN" jako poprawne. Dopiero <c>double.IsFinite</c>
    /// je odrzuca. Bez tego drugiego warunku nieskończony kilometraż przeszedłby
    /// walidację i zachował się dokładnie tak, jak „abc" — pętla bez końca.
    /// </summary>
    [TestMethod]
    public void InfinityAndNaNAreRefusedEvenThoughTryParseAcceptsThem()
    {
        foreach (var text in new[] { "Infinity", "-Infinity", "NaN" })
        {
            Assert.IsTrue(double.TryParse(text, System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out var parsed),
                $"{text}: TryParse miało to przyjąć — na tym stoi ten test");
            Assert.IsFalse(double.IsFinite(parsed), text);

            var plan = Parse($"--at-chainage={text}");
            Assert.IsFalse(plan.IsValid, $"--at-chainage={text} przeszło");
            Assert.AreEqual(BadArgumentValue, plan.ExitCode);
        }
    }

    [TestMethod]
    public void AnIntegerArgumentThatIsNotAnIntegerIsRefused()
    {
        foreach (var name in new[] { "sample-every", "steps-per-frame" })
        {
            var plan = Parse($"--{name}=1.5");
            Assert.IsFalse(plan.IsValid, $"--{name}=1.5 przeszło jako liczba całkowita");
            Assert.AreEqual(BadArgumentValue, plan.ExitCode);
            StringAssert.Contains(plan.Error, "całkowitą");
        }
    }

    /// <summary>
    /// Liczby czyta się w kulturze niezmiennej, bo CI bywa w innej lokalizacji.
    ///
    /// <para><b>Ten test PODMIENIA kulturę wątku i to jest cała jego treść.</b>
    /// Pierwsza wersja tylko wołała <c>Parse</c> i sprawdzała, że przecinek nie
    /// przechodzi — i przechodziła też wtedy, gdy zamienić w <c>RunPlan</c>
    /// <c>InvariantCulture</c> na <c>CurrentCulture</c>. Powód: domyślna kultura
    /// tego przebiegu to kultura niezmienna (<c>CultureInfo.CurrentCulture.Name</c>
    /// zwraca pusty napis), więc obie wersje robiły dokładnie to samo. Test o nazwie
    /// „nie kultura lokalna" nie miał ani jednego wejścia, w którym lokalna kultura
    /// różniłaby się od niezmiennej. Kontrola negatywna 03.09.2026: mutacja
    /// <c>InvariantCulture -&gt; CurrentCulture</c> przechodziła 53/53.</para>
    ///
    /// <para>W <c>pl-PL</c> separatory są odwrócone względem niezmiennej: przecinek
    /// dziesiętny, kropka grupująca. <c>NumberStyles.Float</c> nie zawiera
    /// <c>AllowThousands</c>, więc pod <c>pl-PL</c> obie wartości zmieniają wynik —
    /// <c>0.25</c> przestaje się parsować, a <c>0,25</c> zaczyna. Dopiero to
    /// odróżnia jedną kulturę od drugiej.</para>
    /// </summary>
    [TestMethod]
    public void DecimalsUseTheInvariantCultureNotTheLocalOne()
    {
        var polish = new System.Globalization.CultureInfo("pl-PL");
        Assert.AreEqual(",", polish.NumberFormat.NumberDecimalSeparator,
            "środowisko nie ma danych ICU dla pl-PL — ten test nie ma czego sprawdzać");

        var previous = System.Globalization.CultureInfo.CurrentCulture;
        try
        {
            System.Globalization.CultureInfo.CurrentCulture = polish;

            var plan = Parse("--jitter=0.25");
            Assert.IsTrue(plan.IsValid,
                "kropka dziesiętna odpadła pod pl-PL — czytanie idzie kulturą lokalną");
            Assert.AreEqual(0.25, plan.Jitter);

            var comma = Parse("--jitter=0,25");
            Assert.IsFalse(comma.IsValid,
                "przecinek dziesiętny przeszedł pod pl-PL — kultura nie jest niezmienna");
        }
        finally
        {
            System.Globalization.CultureInfo.CurrentCulture = previous;
        }
    }

    // --- tryby ---------------------------------------------------------------------

    [TestMethod]
    public void TelemetryPathSwitchesTheModeAndMakesTheRunScripted()
    {
        var plan = Parse("--telemetry=build/t400/run.csv");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("telemetry", plan.Mode);
        Assert.IsTrue(plan.ScriptedMode);
        Assert.AreEqual("build/t400/run.csv", plan.TelemetryPath);
    }

    [TestMethod]
    public void ShotPathSwitchesTheModeToShot()
    {
        var plan = Parse("--shot=build/t400/kadr.png", "--at-chainage=2496");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("shot", plan.Mode);
        Assert.IsTrue(plan.ScriptedMode);
        Assert.AreEqual(2496.0, plan.ShotChainageM);
    }

    /// <summary>Telemetria wygrywa z zrzutem, bo tak robił kod przed wydzieleniem.</summary>
    [TestMethod]
    public void TelemetryWinsOverShotWhenBothAreGiven()
    {
        var plan = Parse("--telemetry=a.csv", "--shot=b.png");

        Assert.AreEqual("telemetry", plan.Mode);
    }

    // --- kształt wiersza poleceń ---------------------------------------------------

    [TestMethod]
    public void AFlagWithoutAValueIsStillRecognised()
    {
        var plan = Parse("--no-geometry");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsTrue(plan.HasFlag("no-geometry"));
        Assert.IsFalse(plan.HasFlag("shell"));
    }

    /// <summary>Godot podaje argumenty raz z myślnikami, raz bez — oba kształty muszą działać.</summary>
    [TestMethod]
    public void LeadingDashesAreOptional()
    {
        Assert.AreEqual(ViewKind.Chase, Parse("view=chase").View);
        Assert.AreEqual(ViewKind.Chase, Parse("-view=chase").View);
        Assert.AreEqual(ViewKind.Chase, Parse("--view=chase").View);
    }

    /// <summary>Ścieżka z „=" w środku zostaje cała — dzielimy na PIERWSZYM znaku.</summary>
    [TestMethod]
    public void OnlyTheFirstEqualsSignSplitsNameFromValue()
    {
        var plan = Parse("--telemetry=build/a=b/run.csv");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("build/a=b/run.csv", plan.TelemetryPath);
    }

    [TestMethod]
    public void AnEmptyCommandLineIsValidAndSoIsANullOne()
    {
        Assert.IsTrue(RunPlan.Parse(Array.Empty<string>(), UnknownArgument, BadArgumentValue).IsValid);
        Assert.IsTrue(RunPlan.Parse(null!, UnknownArgument, BadArgumentValue).IsValid);
    }

    [TestMethod]
    public void TheLastValueWinsWhenAnArgumentRepeats()
    {
        var plan = Parse("--view=chase", "--view=outside");

        Assert.AreEqual(ViewKind.Outside, plan.View);
    }

    // --- odmowa jest wartością, nie wyjątkiem --------------------------------------

    /// <summary>
    /// Żadna zła wartość nie ma prawa rzucić wyjątkiem. To jest cała różnica wobec
    /// stanu sprzed wydzielenia: wyjątek w środku <c>_Ready</c> zostawiał scenę
    /// w połowie zbudowaną i pętlę klatek bez końca.
    /// </summary>
    [TestMethod]
    public void NoInputThrows()
    {
        var nasty = new List<string>
        {
            "--at-chainage=", "--jitter=--", "--sample-every=", "--view=",
            "=", "--=1", "--telemetry=", "----", "--at-chainage=1e999",
        };

        var odrzuconych = 0;
        var przyjete = new List<string>();

        foreach (var argument in nasty)
        {
            var plan = Parse(argument);
            Assert.IsNotNull(plan, argument);
            if (!plan.IsValid)
            {
                Assert.IsTrue(plan.ExitCode is UnknownArgument or BadArgumentValue,
                    $"{argument}: kod {plan.ExitCode}");
                Assert.IsFalse(string.IsNullOrWhiteSpace(plan.Error), argument);
                odrzuconych++;
            }
            else
            {
                przyjete.Add(argument);
            }
        }

        // POMIAR, nie ozdoba (6.D31): wszystkie asercje poza `IsNotNull` stały
        // w gałęzi `if (!plan.IsValid)`. Gdyby rozbiór zaczął PRZYJMOWAĆ te wejścia
        // jako poprawne, gałąź przestałaby być wchodzona, test nie sprawdzałby już
        // niczego poza „plan nie jest nullem" — i nie powiedziałby o tym ani słowa.
        // Liczba niżej jest ZMIERZONA przebiegiem, nie policzona z listy w kodzie.
        // **Liczba PRZEPISANA 07.09.2026 przy 6.A28, nie dopisana obok: 8 -> 9.**
        Assert.AreEqual(9, odrzuconych,
            "paskudnych wejść odrzuconych; przyjęte: " + string.Join(" | ", przyjete));

        // **Dziewiąte wejście było PRZYJMOWANE do 07.09.2026 i jest to już naprawione.**
        // `--telemetry=` (pusta ścieżka) przechodziło jako plan poprawny, bo wartość
        // tej opcji jest napisem i pustka nie wywracała żadnego rozbioru — a
        // `TelemetryPath` wychodziło napisem PUSTYM, nie `null`, więc scena zbierała
        // wiersze telemetrii i próbowała je zapisać pod pustą nazwą. 6.D31 tego nie
        // ruszyło świadomie (wzmacniało TESTY, a to jest zmiana zachowania sceny)
        // i przybiło fakt z imienia. 6.A28 zmienia tę listę RAZEM z poprawką, tak jak
        // żądało tego pole „Skończone, gdy" tamtej pozycji.
        //
        // Pomiar, który rozstrzygnął zakres poprawki: pustkę przyjmowało **dziewięć
        // z dziesięciu** opcji ścieżkowych, a dziesiąta (`--calls`) była odrzucana
        // z powodu niezwiązanego z pustką. Poprawka jest więc jedna i wspólna —
        // `RunPlan.PathArguments` — a nie dziesięć osobnych.
        //
        // Lista pusta, a nie skasowana asercja: `CollectionAssert.AreEqual` na pustym
        // zbiorze jest asercją BEZWARUNKOWĄ i wywraca się, gdy rozbiór zacznie
        // cokolwiek z tej dziewiątki przyjmować. Skasowanie jej zostawiłoby test
        // z samym licznikiem, a licznik nie mówi KTÓRE wejście przeszło.
        CollectionAssert.AreEqual(
            System.Array.Empty<string>(), przyjete,
            "rozbiór PRZYJMUJE paskudne wejście, którego nie przyjmował po 6.A28 — "
            + "jeżeli poprawka jest zamierzona, zmień tę listę razem z nią");
    }

    /// <summary>Poprawny plan nie ma powodu odmowy ani kodu wyjścia.</summary>
    [TestMethod]
    public void AValidPlanCarriesNeitherAnErrorNorAnExitCode()
    {
        var plan = Parse("--view=outside", "--jitter=0.5");

        Assert.IsTrue(plan.IsValid);
        Assert.IsNull(plan.Error);
        Assert.AreEqual(0, plan.ExitCode);
    }

    /// <summary>Odmowa niesie kod RÓŻNY dla dwóch różnych rodzajów błędu.</summary>
    [TestMethod]
    public void TheTwoKindsOfRefusalCarryDifferentExitCodes()
    {
        Assert.AreEqual(UnknownArgument, Parse("--nieznany=1").ExitCode);
        Assert.AreEqual(BadArgumentValue, Parse("--view=nieznany").ExitCode);
        Assert.AreNotEqual(UnknownArgument, BadArgumentValue);
    }

    // --- czas klatki i jitter ------------------------------------------------------

    private const double StepSeconds = 1.0 / 120.0;

    [TestMethod]
    public void WithoutJitterEveryFrameIsTheSameLength()
    {
        var plan = Parse();

        var first = plan.SyntheticFrameSeconds(StepSeconds, 0);
        for (long frame = 1; frame < 50; frame++)
        {
            Assert.AreEqual(first, plan.SyntheticFrameSeconds(StepSeconds, frame),
                $"klatka {frame} ma inną długość bez --jitter");
        }
    }

    /// <summary>
    /// Bez jittera czas klatki musi być DOKŁADNIE iloczynem, bez śladu po sinusie.
    ///
    /// <para><b>Sprostowanie do wcześniejszej wersji tego opisu.</b> Stało tu, że
    /// mnożenie przez <c>1 + 0 * sin(...)</c> „dokładałoby błąd zaokrąglenia".
    /// Zmierzone 03.09.2026 i to nieprawda: mutacja granicy <c>Jitter &lt;= 0.0</c>
    /// na <c>Jitter &lt; 0.0</c> przechodzi cały zestaw, bo jest RÓWNOWAŻNA.
    /// Dowód nie z czytania kodu, tylko z przebiegu obu wersji obok siebie
    /// (§5.2): 483 120 wejść — 13 wartości jittera z ręki plus 2000 losowych,
    /// 6 długości kroku (w tym 0,0 i 1e9), 40 klatek — z czego <b>480 trafiło
    /// dokładnie w granicę</b> <c>Jitter == 0.0</c> (razem z <c>-0.0</c>), a różnic
    /// co do bitu było <b>0</b>. Powód: <c>0.0 * Math.Sin(x)</c> jest dokładnie
    /// zerem dla każdego skończonego <c>x</c>, <c>1.0 + 0.0</c> to dokładnie
    /// <c>1.0</c>, a mnożenie przez <c>1.0</c> jest w IEEE 754 tożsamością.</para>
    ///
    /// <para>Gałąź zostaje, ale za intencję, nie za dokładność: zero i wartości
    /// ujemne znaczą „nie wstrzykuj", i tak są tu zapisane wprost. Ten test pilnuje
    /// wyniku — że bez jittera długość klatki jest czystym iloczynem — i to pilnuje
    /// nadal, niezależnie od tego, którą stroną granica leży.</para>
    /// </summary>
    [TestMethod]
    public void ZeroJitterIsExactlyTheProductNotTheProductTimesOne()
    {
        var plan = Parse("--jitter=0");

        Assert.AreEqual(RunPlan.DefaultStepsPerFrame * StepSeconds,
            plan.SyntheticFrameSeconds(StepSeconds, 7));
    }

    [TestMethod]
    public void NegativeJitterIsTreatedAsNoJitter()
    {
        var plan = Parse("--jitter=-0.5");

        Assert.AreEqual(RunPlan.DefaultStepsPerFrame * StepSeconds,
            plan.SyntheticFrameSeconds(StepSeconds, 3));
    }

    [TestMethod]
    public void JitterMakesFramesUnequalWhichIsThePointOfIt()
    {
        var plan = Parse("--jitter=0.25");

        var lengths = new HashSet<double>();
        for (long frame = 0; frame < 20; frame++)
        {
            lengths.Add(plan.SyntheticFrameSeconds(StepSeconds, frame));
        }

        Assert.IsTrue(lengths.Count > 15,
            $"jitter dał tylko {lengths.Count} różnych długości klatki na 20 — "
            + "test determinizmu nie miałby czego sprawdzać");
    }

    /// <summary>Powtarzalność co do bitu: ta sama klatka, ten sam czas, zawsze.</summary>
    [TestMethod]
    public void TheSameFrameAlwaysGivesTheSameLength()
    {
        var plan = Parse("--jitter=0.25");

        for (long frame = 0; frame < 10; frame++)
        {
            Assert.AreEqual(plan.SyntheticFrameSeconds(StepSeconds, frame),
                plan.SyntheticFrameSeconds(StepSeconds, frame),
                "czas klatki nie jest powtarzalny — przebieg nie byłby deterministyczny");
        }
    }

    /// <summary>
    /// Klatka zerowa jest DOKŁADNIE długością bazową, bo sinus startuje z zera.
    ///
    /// <para>To jedyne miejsce, w którym da się przybić fazę jittera bez powtarzania
    /// wzoru z <c>RunPlan</c> w asercji. <c>Math.Sin(0 * 1.7)</c> to <c>Math.Sin(0.0)</c>,
    /// czyli dokładnie zero — próg czytany z wnętrza funkcji, a nie zgadywany, więc
    /// równość jest tu dosłowna (§5.1: dokładnie tylko wtedy, gdy jedna strona jest
    /// zerem). Kontrola negatywna 03.09.2026: mutacja <c>frameIndex * JitterFrequency</c>
    /// na <c>frameIndex + JitterFrequency</c> przechodziła 53/53 — żaden z pozostałych
    /// testów jittera nie patrzył na wartość, tylko na „jest różnorodnie" i „jest
    /// dodatnio", a to mutant spełniał tak samo dobrze.</para>
    /// </summary>
    [TestMethod]
    public void FrameZeroIsExactlyTheBaseLengthBecauseTheSineStartsAtZero()
    {
        var plan = Parse("--jitter=0.9");
        var baseSeconds = plan.StepsPerFrame * StepSeconds;

        Assert.AreEqual(baseSeconds, plan.SyntheticFrameSeconds(StepSeconds, 0L),
            "klatka 0 nie jest dokładnie długością bazową — faza jittera nie zaczyna się od zera");
    }

    /// <summary>
    /// Faza jittera biegnie z NUMEREM klatki, nie z dodaną stałą.
    ///
    /// <para>Test patrzy na znaki, nie na wartości, więc nie przepisuje wzoru z
    /// <c>RunPlan</c> do asercji. Przy częstotliwości 1,7 rad na klatkę sinus zmienia
    /// znak po przekroczeniu π (klatka 2: 3,4 rad) i wraca nad zero po 2π (klatka 4:
    /// 6,8 rad), co daje wzór 0, +, −, −, +. Mutant z dodawaniem daje +, +, −, −, −,
    /// bo jego argumenty to 1,7 2,7 3,7 4,7 5,7.</para>
    ///
    /// <para><b>Czego ten test NIE sprawdza.</b> Wzór znaków nie odróżnia 1,7 od 1,6 —
    /// zmierzone 03.09.2026: mutacja <c>JitterFrequency = 1.6</c> daje te same znaki
    /// 0, +, −, −, + i przechodziła 55/55. Częstotliwość przybija dopiero
    /// <see cref="TheJitterFrequencyIsPinnedToAMeasuredValue"/>.</para>
    /// </summary>
    [TestMethod]
    public void TheJitterPhaseAdvancesWithTheFrameIndexNotWithAConstant()
    {
        var plan = Parse("--jitter=0.5");
        var baseSeconds = plan.StepsPerFrame * StepSeconds;

        var signs = new List<int>();
        for (long frame = 0; frame < 5; frame++)
        {
            var delta = plan.SyntheticFrameSeconds(StepSeconds, frame) - baseSeconds;
            signs.Add(delta == 0.0 ? 0 : (delta > 0.0 ? 1 : -1));
        }

        CollectionAssert.AreEqual(new List<int> { 0, 1, -1, -1, 1 }, signs,
            "znaki odchyłki klatek 0..4 to nie 0,+,-,-,+ — faza jittera nie biegnie "
            + $"z numerem klatki co {RunPlan.JitterFrequency} rad; zmierzone: "
            + string.Join(",", signs));
    }

    /// <summary>
    /// Częstotliwość jittera jest przybita liczbą, bo od niej zależy każda zapisana
    /// długość klatki.
    ///
    /// <para>Wartość oczekiwana nie jest przepisanym wzorem z <c>RunPlan</c>, tylko
    /// stałą policzoną poza projektem — <c>python3 -c "import math;
    /// print(repr(0.5*math.sin(1.7)))"</c> daje <c>0.4958324052262343</c>. Tolerancja
    /// 1e-12 jest o dziewięć rzędów ciaśniejsza niż odstęp do sąsiednich
    /// częstotliwości: 1,6 dałoby 0,49978680, 1,8 dałoby 0,48692382.</para>
    ///
    /// <para>Powód, dla którego to w ogóle stoi osobno: kontrola negatywna
    /// 03.09.2026 pokazała, że mutacja <c>1.7 -&gt; 1.6</c> przechodziła cały zestaw
    /// 55/55. Wszystkie pozostałe testy jittera sprawdzały kształt (różnorodność,
    /// dodatniość, znaki, zero w klatce 0), a kształt jest dla obu wartości ten sam.
    /// Determinizm przebiegu to jednak konkretne liczby, nie kształt: po zmianie
    /// częstotliwości ta sama telemetria z tym samym ziarnem daje inne klatki.</para>
    /// </summary>
    [TestMethod]
    public void TheJitterFrequencyIsPinnedToAMeasuredValue()
    {
        const double DeltaAtFrameOne = 0.4958324052262343;

        var plan = Parse("--jitter=0.5");
        var baseSeconds = plan.StepsPerFrame * StepSeconds;

        var measured = (plan.SyntheticFrameSeconds(StepSeconds, 1L) / baseSeconds) - 1.0;

        Assert.AreEqual(DeltaAtFrameOne, measured, 1e-12,
            $"odchyłka klatki 1 to {measured:R}, a ma być {DeltaAtFrameOne:R} — "
            + $"częstotliwość jittera nie wynosi {RunPlan.JitterFrequency} rad na klatkę");
    }

    /// <summary>Jitter nie ma prawa dać klatki zerowej ani ujemnej.</summary>
    [TestMethod]
    public void FrameLengthStaysPositiveForEveryReasonableJitter()
    {
        foreach (var jitter in new[] { 0.1, 0.25, 0.5, 0.9 })
        {
            var plan = Parse($"--jitter={jitter.ToString(System.Globalization.CultureInfo.InvariantCulture)}");
            for (long frame = 0; frame < 200; frame++)
            {
                Assert.IsTrue(plan.SyntheticFrameSeconds(StepSeconds, frame) > 0.0,
                    $"jitter {jitter}, klatka {frame}");
            }
        }
    }

    [TestMethod]
    public void StepsPerFrameScalesTheFrameLength()
    {
        var one = Parse("--steps-per-frame=1");
        var many = Parse("--steps-per-frame=240");

        Assert.AreEqual(StepSeconds, one.SyntheticFrameSeconds(StepSeconds, 0));
        Assert.AreEqual(240 * StepSeconds, many.SyntheticFrameSeconds(StepSeconds, 0));
    }

    // --- tryb przejazdu linią -----------------------------------------------------

    [TestMethod]
    public void LineModeRefusesToRunWithoutAnExplicitSpeedLimit()
    {
        // To NIE jest higiena argumentów, to jest naprawa zmierzonej usterki. Pierwsza
        // wersja trybu `--line` brała limit z `DriveScenario.PackageAFirstRun`, a ten
        // woła `Units.KmhToMps(model.DesignMaxSpeedKmh)` — czyli 80 km/h, prędkość
        // KONSTRUKCYJNĄ pojazdu. Zmierzone: scena rozpędzała skład do 80,00 km/h
        // i przejeżdżała linię w 724,94 s wobec 733,14 s rdzenia, czyli o 8,2 s szybciej.
        // Prędkość dopuszczalna na torze nie ma źródła (R-006), więc musi przyjść
        // od wołającego — ta sama zasada, co brak domyślnych w `LineRunSettings`.
        var plan = Parse("--line");

        Assert.IsFalse(plan.IsValid, "tryb linii przeszedł bez podanego limitu");
        Assert.IsTrue(plan.Error!.Contains("--line wymaga --limit-kmh"), plan.Error);
        Assert.IsTrue(plan.Error!.Contains("KONSTRUKCYJN"), plan.Error);
        Assert.AreEqual(BadArgumentValue, plan.ExitCode);
    }

    [TestMethod]
    public void LineModeWithALimitIsValidAndNamesItself()
    {
        var plan = Parse("--line", "--limit-kmh=70");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsTrue(plan.LineMode);
        Assert.AreEqual("line", plan.Mode);
        Assert.AreEqual(70.0, plan.LimitKmh, 1e-12);
        Assert.IsFalse(plan.ScriptedMode);
    }

    [TestMethod]
    public void LineModeRefusesTelemetryButAcceptsAShot()
    {
        // `--telemetry` jest DRUGIM sterownikiem tego samego składu i jego wyjście
        // porównuje się z rdzeniem co do bitu, więc pomyłka wyglądałaby jak rozjazd
        // fizyki. `--shot` sterownikiem nie jest — to migawka — i właśnie po to się
        // z `--line` łączy, żeby dało się OBEJRZEĆ skład przy peronie z otwartymi
        // drzwiami, a nie tylko przeczytać, że się zatrzymał.
        var zTelemetria = Parse("--line", "--limit-kmh=70", "--telemetry=/tmp/a.csv");
        Assert.IsFalse(zTelemetria.IsValid, "linia z telemetrią przeszła");
        Assert.IsTrue(zTelemetria.Error!.Contains("--line nie łączy się z --telemetry"), zTelemetria.Error);

        var zZrzutem = Parse("--line", "--limit-kmh=70", "--shot=/tmp/a.png", "--at-chainage=509.73");
        Assert.IsTrue(zZrzutem.IsValid, zZrzutem.Error);
        Assert.IsTrue(zZrzutem.LineMode, "zrzut wyłączył tryb linii");
        Assert.AreEqual("shot", zZrzutem.Mode);
        Assert.AreEqual(509.73, zZrzutem.ShotChainageM, 1e-12);
    }

    [TestMethod]
    public void CallsAndLimitOnlyMakeSenseWithLineMode()
    {
        // Argument, który nic nie robi, jest gorszy od nieznanego: nieznany zatrzymuje
        // przebieg, a bezczynny wygląda jak działający. Ta sama zasada, dla której
        // nieznany argument jest tu błędem, a nie ostrzeżeniem.
        var samoCalls = Parse("--calls=/tmp/a.csv");
        Assert.IsFalse(samoCalls.IsValid, "--calls przeszło bez --line");
        Assert.IsTrue(samoCalls.Error!.Contains("--calls"), samoCalls.Error);

        var samLimit = Parse("--limit-kmh=70");
        Assert.IsFalse(samLimit.IsValid, "--limit-kmh przeszło bez --line");
        Assert.IsTrue(samLimit.Error!.Contains("--limit-kmh wymaga --line albo --signalling"), samLimit.Error);
    }

    [TestMethod]
    public void LineModeStillRefusesAnUnknownArgumentAndABadLimit()
    {
        var literowka = Parse("--line", "--limit-khm=70");
        Assert.IsFalse(literowka.IsValid, "literówka w nazwie limitu przeszła");
        Assert.AreEqual(UnknownArgument, literowka.ExitCode);

        foreach (var zly in new[] { "--limit-kmh=0", "--limit-kmh=-70", "--limit-kmh=abc" })
        {
            var plan = Parse("--line", zly);
            Assert.IsFalse(plan.IsValid, $"{zly} przeszło");
            Assert.AreEqual(BadArgumentValue, plan.ExitCode, zly);
        }
    }

    [TestMethod]
    public void SignallingWithoutLineIsTheCabUnderSignalling()
    {
        // PRZEPISANE 05.09.2026 (G-5), a nie dopisane obok. Poprzednia wersja nazywała
        // się `SignallingOnlyMakesSenseWithLineMode` i twierdziła, że „przebieg
        // skryptowy i ręczny nie mają składu zarejestrowanego w sygnalizacji, więc plan
        // byłby wczytany i nieużyty". Dla przebiegu ręcznego to już nieprawda: skład
        // wchodzi na bloki, dostaje autorytet jazdy i ochronę, która ingeruje
        // w polecenie człowieka.
        var reczny = Parse("--signalling=/tmp/plan.json");
        Assert.IsTrue(reczny.IsValid, reczny.Error);
        Assert.IsTrue(reczny.ManualSignalling, "tryb ręczny z planem nie jest kabiną pod sygnalizacją");
        Assert.AreEqual("manual", reczny.Mode);
        Assert.AreEqual("/tmp/plan.json", reczny.SignallingPath);

        // Odtworzenie z zapisu wejść jest trybem ręcznym z klawiszami z pliku, więc
        // tak samo wolno mu jechać pod ochroną — i to jest jedyny sposób, żeby przejazd
        // pod ATP dało się porównać z rdzeniem przy progu 0.
        var odtworzenie = Parse("--replay=/tmp/keys.log", "--signalling=/tmp/plan.json");
        Assert.IsTrue(odtworzenie.IsValid, odtworzenie.Error);
        Assert.IsTrue(odtworzenie.ManualSignalling);
        Assert.AreEqual("replay", odtworzenie.Mode);
    }

    [TestMethod]
    public void SignallingStillRefusesToJoinAScriptedRun()
    {
        // Druga połowa tej samej reguły i to ona nie może zniknąć razem z pierwszą.
        // Przebieg skryptowy prowadzi `ScenarioDrive`, a jego telemetria jest
        // porównywana z rdzeniem CO DO BITU — ochrona zmieniłaby przejazd, którego
        // zgodność jest całą treścią tamtej bramki.
        foreach (var skryptowy in new[]
                 {
                     new[] { "--signalling=/tmp/plan.json", "--telemetry=/tmp/out.csv" },
                     new[] { "--signalling=/tmp/plan.json", "--shot=/tmp/a.png", "--at-chainage=2000" },
                 })
        {
            var plan = Parse(skryptowy);
            Assert.IsFalse(plan.IsValid, $"--signalling przeszło z {string.Join(" ", skryptowy)}");
            Assert.IsTrue(plan.Error!.Contains("--signalling nie łączy się z przebiegiem skryptowym"), plan.Error);
            Assert.AreEqual(BadArgumentValue, plan.ExitCode);
        }

        // `--line --shot --signalling` PRZECHODZI: `--shot` nie jest sterownikiem,
        // tylko migawką, i po to jest, żeby dało się obejrzeć skład pod blokadami.
        var migawka = Parse(
            "--line", "--limit-kmh=70", "--signalling=/tmp/plan.json",
            "--shot=/tmp/a.png", "--at-chainage=2000");
        Assert.IsTrue(migawka.IsValid, migawka.Error);
        Assert.IsFalse(migawka.ManualSignalling, "przebieg linii nie jest kabiną pod sygnalizacją");
    }

    [TestMethod]
    public void TheDriverCeilingNeedsSomebodyToWatchIt()
    {
        // `--limit-kmh` w trybie ręcznym jest SUFITEM MASZYNISTY, a nie prędkością
        // dopuszczalną. Bez planu nikt go nie pilnuje i przejazd byłby ręcznym
        // przejazdem z wymyśloną prędkością — dokładnie usterką z #246, w której
        // nagłówek mówił `limit=80.0 km/h`, czyli prędkość KONSTRUKCYJNĄ M7.
        var bezNadzoru = Parse("--limit-kmh=76");
        Assert.IsFalse(bezNadzoru.IsValid, "--limit-kmh przeszło bez --line i bez --signalling");
        Assert.IsTrue(bezNadzoru.Error!.Contains("--limit-kmh wymaga --line albo --signalling"), bezNadzoru.Error);
        Assert.AreEqual(BadArgumentValue, bezNadzoru.ExitCode);

        var zNadzorem = Parse("--limit-kmh=76", "--signalling=/tmp/plan.json");
        Assert.IsTrue(zNadzorem.IsValid, zNadzorem.Error);
        Assert.IsTrue(zNadzorem.ManualSignalling);
        Assert.AreEqual(76.0, zNadzorem.LimitKmh, 1e-12);

        // Sufit jest opcją, a nie warunkiem: bez niego kabina jedzie limitem planu,
        // czyli tą samą liczbą, której ochrona pilnuje.
        var bezSufitu = Parse("--signalling=/tmp/plan.json");
        Assert.IsTrue(bezSufitu.IsValid, bezSufitu.Error);
        Assert.AreEqual(0.0, bezSufitu.LimitKmh, 1e-12);
    }

    [TestMethod]
    public void LineModeWithoutSignallingIsValidAndSaysSoByLeavingThePathNull()
    {
        // Brak planu NIE jest błędem — jest wyborem „jedź bez blokad", i scena mówi to
        // wprost w HUD. Ciche wykrywanie planu dla osi dałoby przebieg, o którym nie
        // da się powiedzieć, czy sygnalizacja w nim była.
        var bez = Parse("--line", "--limit-kmh=70");
        Assert.IsTrue(bez.IsValid, bez.Error);
        Assert.IsNull(bez.SignallingPath);

        var z = Parse("--line", "--limit-kmh=70", "--signalling=/tmp/plan.json");
        Assert.IsTrue(z.IsValid, z.Error);
        Assert.AreEqual("/tmp/plan.json", z.SignallingPath);
        Assert.IsTrue(z.LineMode);
    }

    // --- zapis i odtworzenie wejść gracza -----------------------------------------

    [TestMethod]
    public void ReplayIsItsOwnModeAndIsNotScripted()
    {
        // `--replay` prowadzi ten sam `DriverNotch`, co człowiek — różni się wyłącznie
        // źródłem stanu klawiszy. Gdyby wpadło w `ScriptedMode`, scena zbudowałaby
        // `ScenarioDrive` i odtworzenie jechałoby scenariuszem T-400 zamiast zapisem.
        var plan = Parse("--replay=/tmp/keys.log");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("replay", plan.Mode);
        Assert.IsTrue(plan.ReplayMode);
        Assert.IsFalse(plan.ScriptedMode);
        Assert.AreEqual("/tmp/keys.log", plan.ReplayPath);
    }

    [TestMethod]
    public void TelemetryWithReplayIsNotAScriptedRun()
    {
        // To jest para, na której stoi cała weryfikacja G-1: ten sam zapis wejść puszczony
        // przy różnym `--steps-per-frame` ma dać telemetrię identyczną co do bitu.
        // Bez tego rozróżnienia `--telemetry` samo z siebie robiło z przebiegu scenariusz.
        var plan = Parse("--replay=/tmp/keys.log", "--telemetry=/tmp/out.csv", "--steps-per-frame=4");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("replay", plan.Mode);
        Assert.IsFalse(plan.ScriptedMode, "telemetria z --replay zrobiła z przebiegu scenariusz");
        Assert.AreEqual("/tmp/out.csv", plan.TelemetryPath);
        Assert.AreEqual(4L, plan.StepsPerFrame);
    }

    [TestMethod]
    public void TelemetryWithoutReplayIsStillAScriptedRun()
    {
        // Kontrola w drugą stronę: rozróżnienie wyżej nie ma prawa rozbroić istniejącej
        // bramki `--telemetry`, która porównuje przebieg sceny z rdzeniem przy progu 0.
        var plan = Parse("--telemetry=/tmp/out.csv");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("telemetry", plan.Mode);
        Assert.IsTrue(plan.ScriptedMode);
        Assert.IsFalse(plan.ReplayMode);
    }

    [TestMethod]
    public void ReplayRefusesASecondSourceOfCommand()
    {
        // `--replay` z `--line` jest od 6.M1 POPRAWNE (test niżej); odmową zostaje zrzut,
        // bo to drugi warunek końca tego samego przebiegu.
        var zeZrzutem = Parse("--replay=/tmp/keys.log", "--shot=/tmp/a.png", "--at-chainage=2000");
        Assert.IsFalse(zeZrzutem.IsValid, "--replay przeszło razem z --shot");
        Assert.AreEqual(BadArgumentValue, zeZrzutem.ExitCode);
    }

    [TestMethod]
    public void InputLogOnlyMakesSenseWhereTheDriverGivesTheCommand()
    {
        // Plik nazwany „zapisem wejść", powstały z przebiegu, którego nikt nie prowadził,
        // wyglądałby po odtworzeniu jak dowód determinizmu wejścia gracza — i nim nie był.
        //
        // `--line` wyszło z tej listy przy 6.M1: przejazd linii ma maszynistę przy jednym
        // ze składów, a jego polecenia trafiają do zapisu (test niżej).
        foreach (var tryb in new[] { "--shot=/tmp/a.png", "--telemetry=/tmp/o.csv" })
        {
            var arguments = new List<string> { "--input-log=/tmp/keys.log" };
            arguments.AddRange(tryb.Split(' '));
            var plan = RunPlan.Parse(arguments, UnknownArgument, BadArgumentValue);

            Assert.IsFalse(plan.IsValid, $"--input-log przeszło z {tryb}");
            Assert.IsTrue(plan.Error!.Contains("--input-log ma sens tylko"), plan.Error);
            Assert.AreEqual(BadArgumentValue, plan.ExitCode, tryb);
        }
    }

    [TestMethod]
    public void Linia_przyjmuje_odtworzenie_z_telemetria_i_zapis_wejsc_6M1()
    {
        // Odtworzenie linii: telemetria jest wtedy WYJŚCIEM, więc tryb zostaje liniowy,
        // a nie skryptowy — inaczej scena zbudowałaby `ScenarioDrive` zamiast linii.
        var odtworzenie = Parse(
            "--replay=/tmp/keys.log", "--line", "--limit-kmh=70", "--signalling=/tmp/p.json",
            "--telemetry=/tmp/o.csv");
        Assert.IsTrue(odtworzenie.IsValid, odtworzenie.Error);
        Assert.IsTrue(odtworzenie.LineMode, "odtworzenie z --telemetry przestało być trybem linii");
        Assert.IsFalse(odtworzenie.ScriptedMode, "odtworzenie linii wpadło w przebieg skryptowy");
        Assert.IsTrue(odtworzenie.ReplayMode, "--replay przestało być odtworzeniem");
        Assert.IsFalse(odtworzenie.ReadsKeyboard, "odtworzenie linii czyta klawiaturę");

        // Przejazd linii z klawiatury ZAPISUJE wejścia.
        var zapis = Parse("--input-log=/tmp/keys.log", "--line", "--limit-kmh=70");
        Assert.IsTrue(zapis.IsValid, zapis.Error);
        Assert.IsTrue(zapis.LineMode, "--line z --input-log przestało być trybem linii");
        Assert.IsTrue(zapis.ReadsKeyboard, "przejazd linii z zapisem wejść nie czyta klawiatury");

        // Kontrola w drugą stronę: bez `--replay` para `--line --telemetry` zostaje ODMOWĄ,
        // bo wtedy telemetria byłaby drugim źródłem polecenia.
        var bezOdtworzenia = Parse("--line", "--limit-kmh=70", "--telemetry=/tmp/o.csv");
        Assert.IsFalse(bezOdtworzenia.IsValid, "--line --telemetry przeszło bez --replay");
        Assert.AreEqual(BadArgumentValue, bezOdtworzenia.ExitCode, "odmowa --line --telemetry bez --replay ma zły kod wyjścia");

        // Bez planu sygnalizacji linia nie ma maszynisty — odtworzenie jest ODMOWĄ.
        var bezPlanu = Parse("--replay=/tmp/keys.log", "--line", "--limit-kmh=70");
        Assert.IsFalse(bezPlanu.IsValid, "--replay --line przeszło bez --signalling");
        Assert.IsTrue(bezPlanu.Error!.Contains("--replay z --line wymaga --signalling"), bezPlanu.Error);
        Assert.AreEqual(BadArgumentValue, bezPlanu.ExitCode, "odmowa --replay --line bez --signalling ma zły kod wyjścia");
    }

    [TestMethod]
    public void InputLogIsAllowedFromTheKeyboardAndFromAReplay()
    {
        var zKlawiatury = Parse("--input-log=/tmp/keys.log");
        Assert.IsTrue(zKlawiatury.IsValid, zKlawiatury.Error);
        Assert.AreEqual("manual", zKlawiatury.Mode);
        Assert.AreEqual("/tmp/keys.log", zKlawiatury.InputLogPath);

        // Zapis odtworzenia jest sprawdzeniem samego formatu w obie strony:
        // `cmp` wejścia z wyjściem musi wyjść zerowy.
        var zOdtworzenia = Parse("--replay=/tmp/in.log", "--input-log=/tmp/out.log");
        Assert.IsTrue(zOdtworzenia.IsValid, zOdtworzenia.Error);
        Assert.AreEqual("/tmp/out.log", zOdtworzenia.InputLogPath);
        Assert.AreEqual("/tmp/in.log", zOdtworzenia.ReplayPath);
    }

    [TestMethod]
    public void NeitherNewArgumentIsSilentlyIgnored()
    {
        // Ta sama zasada, co przy `--at-chainag`: literówka ma ZATRZYMAĆ przebieg.
        foreach (var literowka in new[] { "--input-logs=/tmp/a", "--replays=/tmp/a" })
        {
            var plan = Parse(literowka);
            Assert.IsFalse(plan.IsValid, $"{literowka} przeszło");
            Assert.AreEqual(UnknownArgument, plan.ExitCode, literowka);
        }

        CollectionAssert.Contains(RunPlan.KnownArguments, "input-log");
        CollectionAssert.Contains(RunPlan.KnownArguments, "replay");
    }

    // --- odtwarzanie telemetrii jako ruchu zadanego -------------------------------

    [TestMethod]
    public void FromTelemetryIsItsOwnModeAndIsNeitherScriptedNorReplay()
    {
        // `--from-telemetry` jest CZWARTYM źródłem ruchu i jedynym, w którym fizyka
        // nie liczy się wcale. Gdyby wpadło w `ScriptedMode`, scena zbudowałaby
        // `ScenarioDrive` i „odtworzenie" wypisałoby scenariusz T-400 zamiast
        // wczytanego przejazdu — z kodem wyjścia zero.
        var plan = Parse("--from-telemetry=/tmp/przejazd.csv");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("from-telemetry", plan.Mode);
        Assert.IsTrue(plan.FromTelemetryMode);
        Assert.AreEqual("/tmp/przejazd.csv", plan.FromTelemetryPath);
        Assert.IsFalse(plan.ScriptedMode, "ruch zadany zrobił się przebiegiem skryptowym");
        Assert.IsFalse(plan.ReplayMode, "ruch zadany zrobił się odtworzeniem zapisu wejść");
        Assert.IsFalse(plan.LineMode);
        Assert.IsFalse(plan.ReadsKeyboard, "scena czytałaby klawiaturę w przebiegu, którym nikt nie steruje");
    }

    [TestMethod]
    public void TelemetryOutputIsAllowedNextToFromTelemetryAndDoesNotScriptTheRun()
    {
        // To jest para, na której stoi CAŁA weryfikacja tego trybu: plik wczytany
        // i ten sam plik wypisany, porównane przy progu 0. Bez tego rozróżnienia
        // `--telemetry` samo z siebie robiło z przebiegu scenariusz — dokładnie tak,
        // jak robiło przed `TelemetryWithReplayIsNotAScriptedRun`.
        var plan = Parse(
            "--from-telemetry=/tmp/wejscie.csv", "--telemetry=/tmp/echo.csv", "--steps-per-frame=7");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual("from-telemetry", plan.Mode, "nazwa trybu poszła za wyjściem, nie za źródłem ruchu");
        Assert.IsFalse(plan.ScriptedMode, "telemetria z --from-telemetry zrobiła z przebiegu scenariusz");
        Assert.AreEqual("/tmp/echo.csv", plan.TelemetryPath);
        Assert.AreEqual("/tmp/wejscie.csv", plan.FromTelemetryPath);
        Assert.AreEqual(7L, plan.StepsPerFrame);
    }

    [TestMethod]
    public void FromTelemetryRefusesEverySecondSourceOfMovementByName()
    {
        // CZWARTA ODMOWA, w tym samym wzorcu co trzy istniejące. Wymaganie jest
        // ostrzejsze niż „nie przechodzi": komunikat ma wymienić OBA tryby, bo cichy
        // wybór jednego z dwóch źródeł daje przejazd nie do odróżnienia po wyniku.
        var pary = new (string Argument, string Nazwa)[]
        {
            ("--line --limit-kmh=72", "--line"),
            ("--replay=/tmp/keys.log", "--replay"),
            ("--input-log=/tmp/keys.log", "--input-log"),
            ("--shot=/tmp/a.png --at-chainage=2000", "--shot"),
            ("--signalling=/tmp/plan.json", "--signalling"),
            ("--sample-every=1", "--sample-every"),
        };

        foreach (var (argument, nazwa) in pary)
        {
            var arguments = new List<string> { "--from-telemetry=/tmp/przejazd.csv" };
            arguments.AddRange(argument.Split(' '));
            var plan = RunPlan.Parse(arguments, UnknownArgument, BadArgumentValue);

            Assert.IsFalse(plan.IsValid, $"--from-telemetry przeszło razem z {nazwa}");
            Assert.IsTrue(plan.Error!.Contains("--from-telemetry", StringComparison.Ordinal),
                $"komunikat nie nazywa pierwszego trybu: {plan.Error}");
            Assert.IsTrue(plan.Error!.Contains(nazwa, StringComparison.Ordinal),
                $"komunikat nie nazywa drugiego trybu ({nazwa}): {plan.Error}");
            Assert.AreEqual(BadArgumentValue, plan.ExitCode, nazwa);
        }
    }

    [TestMethod]
    public void FromTelemetryStillAllowsWhatChangesOnlyTheFrameRhythmOrTheView()
    {
        // Kontrola w drugą stronę do testu wyżej: zestaw odmów nie ma prawa zamknąć
        // argumentów, które w tym trybie NAPRAWDĘ coś robią. `--steps-per-frame`
        // i `--jitter` zmieniają podział kroków na klatki, a widok wybiera kamerę —
        // i to jest jedyny sposób, żeby ten sam plik puścić przy innym rytmie klatek
        // i sprawdzić, że wychodzi z niego to samo.
        var plan = Parse(
            "--from-telemetry=/tmp/przejazd.csv", "--steps-per-frame=37", "--jitter=0.45",
            "--view=outside", "--no-geometry");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual(37L, plan.StepsPerFrame);
        Assert.AreEqual(0.45, plan.Jitter, 1e-12);
        Assert.AreEqual(ViewKind.Outside, plan.View);
        Assert.AreEqual("from-telemetry", plan.Mode);
    }

    [TestMethod]
    public void FromTelemetryIsNotSilentlyIgnoredWhenMisspelled()
    {
        // Ta sama zasada, co przy `--at-chainag`: literówka ma ZATRZYMAĆ przebieg.
        // Tutaj kosztowałaby więcej niż zwykle — `--from-telemetri=plik` bez tej
        // bramki dałoby przejazd RĘCZNY, który nie kończy się nigdy, czyli wypalony
        // limit czasu w CI zamiast komunikatu.
        foreach (var literowka in new[] { "--from-telemetri=/tmp/a.csv", "--from-telemetries=/tmp/a.csv" })
        {
            var plan = Parse(literowka);
            Assert.IsFalse(plan.IsValid, $"{literowka} przeszło");
            Assert.AreEqual(UnknownArgument, plan.ExitCode, literowka);
        }

        CollectionAssert.Contains(RunPlan.KnownArguments, "from-telemetry");
    }
    // --- pusta wartosc opcji sciezkowej (6.A28) ---------------------------------

    /// <summary>
    /// KAZDA opcja sciezkowa odmawia pustej wartosci, i to wypisana z listy, nie
    /// z jednego przykladu.
    /// </summary>
    /// <remarks>
    /// Pomiar, ktory rozstrzygnal zakres poprawki: pustke przyjmowalo DZIEWIEC
    /// z dziesieciu opcji sciezkowych (kod 0, `IsValid` prawdziwe, wartosc rowna
    /// napisowi pustemu), a dziesiata — `--calls` — byla odrzucana z powodu
    /// niezwiazanego z pustka, bo wymaga `--line`. Poprawka jest wiec jedna
    /// i wspolna, i to pole „Wyjscie" 6.A28 kazalo rozstrzygnac pomiarem.
    ///
    /// PO poprawce odmawiaja wszystkie DZIESIEC i kazda z powodu pustki, bo
    /// sprawdzenie stoi w `Parse` przed sprawdzeniem zaleznosci miedzy argumentami.
    /// Tez zmierzone: pierwsza wersja tego testu zadala, zeby `--calls` szlo inna
    /// droga, i padla.
    ///
    /// Petla po `RunPlan.PathArguments`, a nie dziesiec osobnych testow: opcja
    /// dopisana do tamtej listy dostaje ten test za darmo, a opcja z niej usunieta
    /// przestaje byc sprawdzana — i to widac w tescie nizej, ktory pilnuje liczby.
    /// </remarks>
    [TestMethod]
    public void KazdaOpcjaSciezkowaOdmawiaPustejWartosci()
    {
        var inna_droga = new List<string>();
        foreach (var nazwa in RunPlan.PathArguments)
        {
            var plan = Parse("--" + nazwa + "=");

            Assert.IsFalse(plan.IsValid, nazwa + ": plan z pusta sciezka jest poprawny");
            Assert.AreEqual(BadArgumentValue, plan.ExitCode, nazwa);
            Assert.IsFalse(string.IsNullOrWhiteSpace(plan.Error), nazwa);
            if (plan.Error!.Contains("wymaga ścieżki", StringComparison.Ordinal))
            {
                StringAssert.Contains(plan.Error, "--" + nazwa,
                    "odmowa nie nazywa opcji, ktorej dotyczy");
            }
            else
            {
                inna_droga.Add(nazwa + " -> " + plan.Error);
            }
        }

        // **Zmierzone, nie zalozone — i pierwsza wersja tego testu byla tu w bledzie.**
        // Zakladalem, ze `--calls=` odmowi WCZESNIEJ i z innego powodu (wymaga
        // `--line`), i test zadal takiej wlasnie listy. Przebieg pokazal liste PUSTA:
        // sprawdzenie pustej sciezki stoi w `Parse` PRZED sprawdzeniem zaleznosci
        // miedzy argumentami, wiec wszystkie dziesiec odmawia z powodu wlasciwego —
        // pustki — i kazda odmowa nazywa swoja opcje.
        //
        // Lista pusta, a nie skasowany warunek: gdyby ktos przesunal sprawdzenie
        // pustki ZA sprawdzenie zaleznosci, ta asercja to pokaze wraz z komunikatem,
        // ktory wtedy padnie — a sam licznik odmow nie pokazalby niczego, bo odmowa
        // by byla, tylko o czym innym.
        CollectionAssert.AreEqual(
            System.Array.Empty<string>(), inna_droga,
            "opcja sciezkowa odmawia pustki z INNEGO powodu niz sama pustka: "
            + string.Join(" | ", inna_droga));
    }

    /// <summary>
    /// Wartosc z samych bialych znakow to ta sama usterka, tylko trudniejsza
    /// do zauwazenia w wierszu polecen.
    /// </summary>
    [TestMethod]
    public void OpcjaSciezkowaOdmawia_takze_samych_bialych_znakow()
    {
        var plan = Parse("--telemetry= ");

        Assert.IsFalse(plan.IsValid, plan.Error);
        Assert.AreEqual(BadArgumentValue, plan.ExitCode);
        StringAssert.Contains(plan.Error!, "--telemetry");
    }

    /// <summary>
    /// Kontrola drugiego kierunku, i to ONA jest tu wazniejsza od odmow wyzej:
    /// wartosc NIEPUSTA nadal przechodzi. Odmowa zbudowana zbyt szeroko odrzucalaby
    /// kazdy plan ze sciezka, a testy odmowy nadal bylyby zielone.
    /// </summary>
    [TestMethod]
    public void Niepusta_sciezka_nadal_przechodzi_dla_kazdej_opcji()
    {
        foreach (var nazwa in RunPlan.PathArguments)
        {
            if (nazwa is "calls" or "scheduled-entries")
            {
                // `--calls` wymaga `--line`, a `--line` wymaga `--limit-kmh`.
                continue;
            }

            var plan = Parse("--" + nazwa + "=jakas/sciezka.json");

            Assert.IsTrue(plan.IsValid, nazwa + ": " + plan.Error);
            Assert.AreEqual("jakas/sciezka.json", plan.Argument(nazwa), nazwa);
        }
    }

    /// <summary>
    /// Lista opcji sciezkowych jest podzbiorem znanych argumentow, a jej liczba jest
    /// przybita. Bez tego opcja usunieta z `PathArguments` przestalaby byc sprawdzana,
    /// a petla wyzej nadal bylaby zielona — na mniejszym zbiorze.
    /// </summary>
    [TestMethod]
    public void Lista_opcji_sciezkowych_jest_podzbiorem_znanych_i_ma_jedenascie_pozycji()
    {
        Assert.AreEqual(11, RunPlan.PathArguments.Length,
            "opcji sciezkowych jest 11: " + string.Join(" ", RunPlan.PathArguments));
        foreach (var nazwa in RunPlan.PathArguments)
        {
            Assert.IsTrue(Array.IndexOf(RunPlan.KnownArguments, nazwa) >= 0,
                nazwa + " jest na liscie sciezkowych, a nie ma go w KnownArguments");
        }
        CollectionAssert.AllItemsAreUnique(RunPlan.PathArguments);
    }

    [TestMethod]
    public void Rozklad_dwoch_wejsc_wymaga_linii_i_sygnalizacji_oraz_odmawia_replay()
    {
        var baseArgs = new[] { "--line", "--limit-kmh=70", "--signalling=plan.json",
            "--scheduled-entries=entries.json" };
        Assert.IsTrue(Parse(baseArgs).IsValid, "plan dwóch wejść ma jawny tryb linii i sygnalizację");
        Assert.IsFalse(Parse("--scheduled-entries=entries.json").IsValid,
            "plan bez linii nie może być cicho ignorowany");
        Assert.IsFalse(Parse(baseArgs.Append("--replay=inputs.csv").ToArray()).IsValid,
            "Runner nie umie jeszcze odtworzyć dyspozytora");
        Assert.IsFalse(Parse(baseArgs.Append("--input-log=inputs.csv").ToArray()).IsValid,
            "nie wolno zapisać przejazdu, którego Runner nie odtworzy");
    }

    /// <summary>
    /// Pusta sciezka dawala `TelemetryPath` rowne napisowi PUSTEMU, nie `null` — i to
    /// jest mechanizm usterki, nie jej objaw. Warunek `_telemetryPath is not null`
    /// w scenie byl wiec prawdziwy: scena zbierala wiersze telemetrii przez caly
    /// przejazd i probowala je zapisac pod pusta nazwa. Ten test przybija, ze do tego
    /// stanu nie da sie juz dojsc.
    /// </summary>
    [TestMethod]
    public void Pusta_sciezka_nie_dochodzi_do_TelemetryPath()
    {
        var plan = Parse("--telemetry=");

        Assert.IsFalse(plan.IsValid);
        Assert.AreEqual(BadArgumentValue, plan.ExitCode);

        // Kontrola przyrzadu: przy sciezce NIEPUSTEJ `TelemetryPath` ja niesie,
        // wiec asercja wyzej nie jest spelniona przez to, ze pole jest zawsze puste.
        var dobry = Parse("--telemetry=build/t.csv");
        Assert.AreEqual("build/t.csv", dobry.TelemetryPath);
    }
}
