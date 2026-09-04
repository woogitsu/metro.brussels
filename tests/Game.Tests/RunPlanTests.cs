using System;
using System.Collections.Generic;
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
        StringAssert.Contains(plan.Error, "Znane:", "komunikat ma wypisać, co jest znane");
    }

    [TestMethod]
    public void TheCorrectlySpelledArgumentGoesThrough()
    {
        var plan = Parse("--at-chainage=2000");

        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual(2000.0, plan.ShotChainageM);
    }

    [TestMethod]
    public void EveryKnownArgumentIsAcceptedOnItsOwn()
    {
        foreach (var name in RunPlan.KnownArguments)
        {
            var value = name switch
            {
                "sample-every" or "steps-per-frame" => "10",
                "jitter" or "at-chainage" => "1.5",
                "view" => "cab",
                _ => "x",
            };
            var plan = Parse($"--{name}={value}");
            Assert.IsTrue(plan.IsValid, $"--{name}={value}: {plan.Error}");
        }
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

        foreach (var argument in nasty)
        {
            var plan = Parse(argument);
            Assert.IsNotNull(plan, argument);
            if (!plan.IsValid)
            {
                Assert.IsTrue(plan.ExitCode is UnknownArgument or BadArgumentValue,
                    $"{argument}: kod {plan.ExitCode}");
                Assert.IsFalse(string.IsNullOrWhiteSpace(plan.Error), argument);
            }
        }
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
}
