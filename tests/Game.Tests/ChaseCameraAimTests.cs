using System;
using Godot;
using MetroBxl.Game;
using MetroBxl.Game.World;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Celowanie kamery goniącej.
///
/// <para><b>Skąd te liczby.</b> Nie z opisu zadania, tylko z przebiegu zmierzonego
/// 04.09.2026: <c>--line --limit-kmh=70</c> na Godocie 4.7.2 wypisywał
/// <b>10 ostrzeżeń</b> <c>Target and up vectors are colinear</c>, wszystkie
/// z <c>FirstRun.PlaceEverything</c> — jedno z <c>_Ready</c>, dziewięć z
/// <c>_Process</c>. Przebieg telemetryczny (start na 94 m) nie wypisywał ani jednego,
/// bo tam kilometraż nigdy nie wchodzi w pasmo degeneracji.</para>
///
/// <para>Skład M7 ma 94,0 m, kamera stoi 12,0 m za ogonem
/// (<see cref="DesignAssumptions.ChaseBehindM"/>), więc pasma są dwa i trzeba je
/// odróżniać: <b>0..47 m</b> — kamera i cel w tym samym punkcie osi (ostrzeżenie),
/// <b>0..94 m</b> — kilometraż kamery pokryty przez skład (kamera w skorupie).
/// Ani jedno, ani drugie nie kończy się na 106 m; 106 m to kilometraż, od którego
/// kamera odzyskuje PEŁNE 12 m odstępu.</para>
/// </summary>
[TestClass]
public sealed class ChaseCameraAimTests
{
    /// <summary>
    /// Długość składu — z REJESTRU POJAZDU, nie z literału.
    ///
    /// <para>Ta liczba jest granicą pasma, w którym widok goniący ma być niedostępny
    /// (decyzja właściciela z 05.09.2026), więc przepisanie jej tutaj ręcznie znaczyłoby,
    /// że zmiana w <c>data/vehicle/m7-spec.json</c> przesuwa scenę, a testu nie rusza.
    /// Wymuszony status <c>spec</c> dokłada drugie zabezpieczenie: awans wartości
    /// z <c>design_model</c> wywraca test, zamiast po cichu zmienić znaczenie granicy.
    /// Ta sama droga, którą <c>RunHeaderTests</c> bierze długość składu do nagłówka.</para>
    /// </summary>
    private static readonly double TrainM =
        VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec);

    /// <summary>
    /// Próg odsłonięcia widoku goniącego — ze <c>DesignAssumptions</c>, nie z literału,
    /// z tego samego powodu, co długość składu wyżej: liczba jest DECYZJĄ właściciela
    /// (07.09.2026), a test, który ją przepisuje, przepuściłby zmianę decyzji bez słowa.
    /// </summary>
    private const double RevealM = DesignAssumptions.ChaseRevealFromM;

    private const double AxisM = 6686.739;
    private const double BehindM = DesignAssumptions.ChaseBehindM;

    private static ChaseFraming At(double frontChainageM) =>
        ChaseCameraAim.Frame(frontChainageM, TrainM, AxisM, BehindM);

    // --- kilometraże kadru ---------------------------------------------------

    [TestMethod]
    public void CameraKeepsTheNominalGapOnceTheAxisAllowsIt()
    {
        var framing = At(2000.0);
        Assert.AreEqual(2000.0 - TrainM - BehindM, framing.CameraChainageM, 1e-9);
        Assert.AreEqual(2000.0 - (TrainM * 0.5), framing.TargetChainageM, 1e-9);
        Assert.AreEqual(
            BehindM,
            framing.RearChainageM - framing.CameraChainageM,
            1e-9,
            "poza pasmem degeneracji odstęp ma być dokładnie nominalny");
    }

    [TestMethod]
    public void BothChainagesCollapseToZeroBelowHalfTheTrain()
    {
        // To jest cała przyczyna ostrzeżenia: DWA przycięcia do zera naraz.
        var framing = At(0.0);
        Assert.AreEqual(0.0, framing.CameraChainageM, 1e-9);
        Assert.AreEqual(0.0, framing.TargetChainageM, 1e-9);
        Assert.AreEqual(-TrainM, framing.RearChainageM, 1e-9, "cały skład jest przed osią");
    }

    [TestMethod]
    public void TheTargetLeavesZeroExactlyAtHalfTheTrain()
    {
        // Granica całkowita i dotykalna: 47,0 m to jeszcze zero, 47,001 m to już nie.
        // Mutacja `* 0.5` -> `* 0.25` przesuwa ją na 23,5 m i ten test to widzi.
        Assert.AreEqual(0.0, At(TrainM * 0.5).TargetChainageM, 1e-12);
        Assert.IsTrue(At((TrainM * 0.5) + 0.001).TargetChainageM > 0.0);
    }

    [TestMethod]
    public void TheCameraLeavesZeroExactlyAtTrainPlusGap()
    {
        // 106,0 m — liczba z pozycji 6.B11. Tyle wynosi kilometraż, od którego kamera
        // przestaje być przyciśnięta do początku osi, a NIE kilometraż, do którego
        // siedzi w składzie ani do którego wypisuje ostrzeżenie.
        Assert.AreEqual(0.0, At(TrainM + BehindM).CameraChainageM, 1e-12);
        Assert.IsTrue(At(TrainM + BehindM + 0.001).CameraChainageM > 0.0);
    }

    [TestMethod]
    public void ChainagesNeverLeaveTheAxis()
    {
        foreach (var front in new[] { -50.0, 0.0, 1.0, 5000.0, AxisM, AxisM + 500.0 })
        {
            var framing = At(front);
            Assert.IsTrue(framing.CameraChainageM >= 0.0 && framing.CameraChainageM <= AxisM, $"{front}");
            Assert.IsTrue(framing.TargetChainageM >= 0.0 && framing.TargetChainageM <= AxisM, $"{front}");
            Assert.IsTrue(framing.FrontChainageM >= 0.0 && framing.FrontChainageM <= AxisM, $"{front}");
        }
    }

    [TestMethod]
    public void AnAxisWithoutLengthIsRefused()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => ChaseCameraAim.Frame(0.0, TrainM, 0.0, BehindM));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => ChaseCameraAim.Frame(0.0, -1.0, AxisM, BehindM));
    }

    // --- twierdzenie o „wchodzeniu w geometrię" ------------------------------

    [TestMethod]
    public void TheCameraSitsInsideTheTrainForTheFirstTrainLength()
    {
        // Pozycja 6.B11 mówi „~106 m". Zmierzone: 94,0 m — dokładnie długość składu.
        Assert.IsTrue(At(0.0).CameraWithinTrainSpan);
        Assert.IsTrue(At(93.999).CameraWithinTrainSpan);
        Assert.IsTrue(At(TrainM).CameraWithinTrainSpan, "przy 94 m ogon dotyka kamery");
        Assert.IsFalse(At(94.001).CameraWithinTrainSpan, "ogon minął kamerę");
        Assert.IsFalse(At(TrainM + BehindM).CameraWithinTrainSpan);
        Assert.IsFalse(At(2000.0).CameraWithinTrainSpan);
    }

    [TestMethod]
    public void BetweenTrainLengthAndTheNominalGapTheCameraIsOutButTooClose()
    {
        // Pasmo 94..106 m: kamera jest już za składem, ale bliżej niż 12 m. To NIE jest
        // „wewnątrz geometrii" i nie daje ostrzeżenia — a właśnie tym pasmem różni się
        // liczba 106 od liczby 94.
        var framing = At(100.0);
        Assert.IsFalse(framing.CameraWithinTrainSpan);
        Assert.AreEqual(6.0, framing.RearChainageM - framing.CameraChainageM, 1e-9);
    }

    // --- dostępność widoku ---------------------------------------------------

    [TestMethod]
    public void TheChaseViewIsUnavailableUntilTheRevealThreshold()
    {
        // PRZEPISANE 09.09.2026 (6.B43), nie dopisane obok. Do tej pozycji granicą była
        // sama długość składu i test nazywał się „...UntilTheWholeTrainIsOnTheAxis".
        // Decyzja właściciela z 07.09.2026 odsuwa granicę na 110 m, bo kadr na 96 m jest
        // jeszcze płytą pudła — zmierzone 46,67 % bieli, patrz raport 6.B43.
        Assert.IsFalse(ChaseCameraAim.IsAvailable(0.0, TrainM, RevealM));
        Assert.IsFalse(ChaseCameraAim.IsAvailable(20.0, TrainM, RevealM), "zmierzone: kadr to płyta pudła");
        Assert.IsFalse(ChaseCameraAim.IsAvailable(48.0, TrainM, RevealM), "zmierzone: 56,4 % bieli");
        Assert.IsFalse(ChaseCameraAim.IsAvailable(90.0, TrainM, RevealM));
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(TrainM, TrainM, RevealM),
            "94,0 m to już NIE granica — pasmo ukrycia idzie dalej");
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(96.0, TrainM, RevealM),
            "zmierzone 09.09.2026: 46,67 % pikseli jaśniejszych niż 0,80 w górnych 60 % kadru");
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(98.0, TrainM, RevealM),
            "98 m ma już 0,00 % bieli, ale 110 m jest DECYZJĄ właściciela, nie wynikiem pomiaru");
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(RevealM, TrainM, RevealM),
            "granica NALEŻY do pasma ukrycia: po minięciu znaczy ostro większe");
        Assert.IsTrue(ChaseCameraAim.IsAvailable(RevealM + 0.001, TrainM, RevealM));
        Assert.IsTrue(ChaseCameraAim.IsAvailable(2000.0, TrainM, RevealM));
    }

    [TestMethod]
    public void TheBandBoundaryIsTheOwnerDecisionAndNotTheRegisteredTrainLength()
    {
        // PRZEPISANE (6.B43). Poprzednia wersja żądała, żeby granica RÓWNAŁA SIĘ
        // długości składu z rejestru — po decyzji z 07.09.2026 to twierdzenie jest
        // fałszywe, więc test pyta o jedno i drugie i o RELACJĘ między nimi.
        var registered = VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec);
        Assert.AreEqual(registered, TrainM, 1e-12, "długość składu nie jest liczbą z rejestru");
        Assert.AreEqual(
            DesignAssumptions.ChaseRevealFromM,
            ChaseCameraAim.Availability(0.0, TrainM, RevealM).FromChainageM,
            1e-12,
            "widok ma się otwierać po minięciu progu odsłonięcia, nie długości składu");
        Assert.IsTrue(RevealM > registered,
            "próg odsłonięcia ma leżeć ZA długością składu — inaczej nie odsuwa niczego");
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(registered, registered, RevealM),
            "dokładnie na długości składu widok jest niedostępny");
    }

    [TestMethod]
    public void TheThresholdNeverPullsTheBoundaryCloserThanTheTrainItself()
    {
        // Druga strona `max(...)`, bez której próg mniejszy od długości składu wsadziłby
        // kamerę z powrotem do skorupy — czyli odtworzyłby usterkę z 05.09.2026.
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(50.0, TrainM, 10.0),
            "próg 10 m nie ma prawa odsłonić widoku w środku składu");
        Assert.AreEqual(
            TrainM,
            ChaseCameraAim.Availability(0.0, TrainM, 10.0).FromChainageM,
            1e-12,
            "przy progu mniejszym od składu granicą zostaje długość składu");
    }

    [TestMethod]
    public void AvailabilityNoLongerAgreesWithTheFramingAndThatIsTheWholePoint()
    {
        // PRZEPISANE (6.B43), nie usunięte. Do tej pozycji te dwa twierdzenia były
        // TOŻSAME i test przemiatał 0..300 m, żeby tego pilnować. Po decyzji z
        // 07.09.2026 tożsame już nie są — i test mówi dokładnie GDZIE się rozchodzą,
        // bo „przestały być tożsame" bez granicy byłoby zdaniem bez treści.
        //
        // `CameraWithinTrainSpan` opisuje GEOMETRIĘ (czy kamera siedzi w skorupie)
        // i to się nie zmieniło: jest prawdziwe do 94,0 m. `IsAvailable` opisuje
        // DOSTĘPNOŚĆ WIDOKU i jest fałszywe do 110,0 m. Pasmo między nimi — 94..110 m —
        // to jedyne miejsce, gdzie kamera jest już za składem, a widok nadal ukryty.
        var wPasmie = 0;
        for (var front = 0.0; front <= 300.0; front += 0.25)
        {
            var wSkorupie = At(front).CameraWithinTrainSpan;
            var dostepny = ChaseCameraAim.IsAvailable(front, TrainM, RevealM);
            Assert.IsFalse(wSkorupie && dostepny,
                $"kilometraż {front} m: kamera w skorupie, a widok dostępny — to jest usterka z 05.09.2026");
            var wPasmieRozejscia = front > TrainM && front <= RevealM;
            Assert.AreEqual(
                wPasmieRozejscia,
                !wSkorupie && !dostepny,
                $"kilometraż {front} m: pasmo rozejścia ma być dokładnie (94,0; 110,0]");
            if (wPasmieRozejscia)
            {
                wPasmie++;
            }
        }

        // ASERCJA, BEZ KTÓREJ PĘTLA WYŻEJ JEST ZIELONA NAD PUSTYM PASMEM. Zmierzone:
        // po powrocie progu do długości składu pasmo (94,0; 94,0] jest puste, warunek
        // `wPasmieRozejscia` fałszywy wszędzie i cała pętla przechodzi — czyli test
        // o rozejściu przechodziłby nad stanem, w którym rozejścia nie ma. 64 punkty
        // to (110,0 − 94,0) / 0,25.
        Assert.AreEqual(64, wPasmie,
            "pasmo rozejścia ma 16,0 m przemiatane co 0,25 m — puste pasmo znaczy, "
            + "że próg odsłonięcia wrócił do długości składu");
    }

    [TestMethod]
    public void TheRemainingDistanceCountsDownToTheBoundary()
    {
        // Liczby PRZELICZONE na nową granicę (6.B43): odliczanie idzie do 110 m,
        // nie do 94 m. Stare wartości (94,0 i 74,0) opisywały poprzednią granicę
        // i przepisanie ich tutaj bez zmiany byłoby testem o stanie minionym.
        Assert.AreEqual(RevealM, ChaseCameraAim.Availability(0.0, TrainM, RevealM).RemainingM, 1e-9);
        Assert.AreEqual(90.0, ChaseCameraAim.Availability(20.0, TrainM, RevealM).RemainingM, 1e-9);
        Assert.AreEqual(
            16.0,
            ChaseCameraAim.Availability(TrainM, TrainM, RevealM).RemainingM,
            1e-9,
            "na długości składu do odsłonięcia zostaje jeszcze 110,0 − 94,0 m");
        Assert.AreEqual(0.0, ChaseCameraAim.Availability(RevealM, TrainM, RevealM).RemainingM, 1e-9);
        Assert.AreEqual(
            0.0,
            ChaseCameraAim.Availability(2000.0, TrainM, RevealM).RemainingM,
            1e-9,
            "za pasmem brakuje zera metrów, a nie ujemnych");
    }

    [TestMethod]
    public void AnUnavailableViewSaysWhyAndFromWhere()
    {
        // Wiersz HUD-u i komunikat odmowy zrzutu biorą się z TEGO zdania — jedno
        // źródło, więc nie mają jak podać dwóch różnych kilometraży. Po 6.B43 tą
        // jedną liczbą jest 110,0 m.
        var reason = ChaseCameraAim.Availability(20.0, TrainM, RevealM).Reason;
        StringAssert.Contains(reason, "niedostępny");
        StringAssert.Contains(reason, "110.0 m", "zdanie ma mówić, OD KIEDY widok będzie");
        StringAssert.Contains(reason, "90.0 m", "zdanie ma mówić, ile jeszcze zostało");
        Assert.IsFalse(
            reason.Contains("94.0 m"),
            "zdanie nie może już podawać starej granicy — HUD i odmowa mówią jedną liczbę: " + reason);

        // Na samej granicy nie ma czego dopisywać: 110,0 m to jeszcze pasmo ukrycia,
        // a „jeszcze 0,0 m" czytałoby się jak usterka, nie jak odmowa.
        var naGranicy = ChaseCameraAim.Availability(RevealM, TrainM, RevealM).Reason;
        StringAssert.Contains(naGranicy, "po minięciu 110.0 m");
        // ASERCJA ZAOSTRZONA (6.B43), nie poluzowana. Poprzednia szukała samego słowa
        // „jeszcze" i przechodziła TYLKO dlatego, że tekst powodu go nie zawierał —
        // czyli pilnowała sufiksu przez cechę zdania obok. Dziś pyta o sufiks wprost
        // i dodatkowo żąda, żeby zdanie KOŃCZYŁO SIĘ granicą, więc żaden dopisek
        // o zerowej odległości nie ma jak się w nim schować.
        Assert.IsFalse(naGranicy.Contains("jeszcze 0.0"), naGranicy);
        Assert.IsTrue(
            naGranicy.EndsWith("po minięciu 110.0 m", System.StringComparison.Ordinal),
            "na granicy zdanie kończy się kilometrażem, bez ani jednego dopisku: " + naGranicy);

        Assert.AreEqual(
            string.Empty,
            ChaseCameraAim.Availability(2000.0, TrainM, RevealM).Reason,
            "widok dostępny nie ma o czym mówić — inaczej HUD kłamałby przez cały przejazd");
    }

    [TestMethod]
    public void TheReasonNamesTheRightCauseInEachHalfOfTheBand()
    {
        // 6.B43: pasmo ukrycia ma od tej pozycji DWA powody, więc jedno zdanie dla obu
        // byłoby na jednym z nich nieprawdziwe. Zmierzone przy 100 m: kamera stoi 6,0 m
        // za ogonem, czyli JUŻ NIE w skorupie — a widok jest ukryty decyzją.
        var wSkorupie = ChaseCameraAim.Availability(20.0, TrainM, RevealM).Reason;
        StringAssert.Contains(wSkorupie, "kamera siedzi w skorupie składu");
        StringAssert.Contains(wSkorupie, "110.0 m");

        var zDecyzji = ChaseCameraAim.Availability(100.0, TrainM, RevealM).Reason;
        StringAssert.Contains(zDecyzji, "decyzji właściciela");
        StringAssert.Contains(zDecyzji, "110.0 m");
        Assert.IsFalse(
            zDecyzji.Contains("skorupie"),
            "na 100 m kamera jest 6,0 m za ogonem — zdanie o skorupie byłoby nieprawdziwe: " + zDecyzji);

        // Granica między powodami to długość składu, nie liczba wpisana obok.
        Assert.IsTrue(
            ChaseCameraAim.Availability(TrainM, TrainM, RevealM).Reason.Contains("skorupie"),
            "dokładnie na długości składu kamera jest jeszcze w płaszczyźnie czoła pudła");
        Assert.IsTrue(
            ChaseCameraAim.Availability(TrainM + 0.001, TrainM, RevealM).Reason.Contains("decyzji"),
            "o milimetr dalej powodem jest już decyzja, a nie geometria");
    }

    [TestMethod]
    public void AvailabilityRefusesANegativeTrainLength()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => ChaseCameraAim.Availability(0.0, -1.0, RevealM));
    }

    [TestMethod]
    public void AvailabilityRefusesANegativeRevealThreshold()
    {
        // Nowy parametr dostaje własną odmowę, bo bez niej ujemny próg przechodziłby
        // przez `Math.Max` bez słowa i wyglądałby jak brak progu.
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => ChaseCameraAim.Availability(0.0, TrainM, -1.0));
    }

    // --- degeneracja kierunku ------------------------------------------------

    private static readonly Vector3 Up = Vector3.Up;

    [TestMethod]
    public void AVerticalAimIsDegenerate()
    {
        // Dokładnie ten odcinek, który powstawał w scenie: kamera 2,60 m, cel 1,80 m
        // nad tym samym punktem osi.
        Assert.IsTrue(ChaseCameraAim.IsDegenerate(new Vector3(0.0f, -0.8f, 0.0f), Up));
        Assert.IsTrue(ChaseCameraAim.IsDegenerate(new Vector3(0.0f, 0.8f, 0.0f), Up));
    }

    [TestMethod]
    public void AZeroAimIsDegenerate()
    {
        Assert.IsTrue(ChaseCameraAim.IsDegenerate(Vector3.Zero, Up));
        Assert.IsTrue(
            ChaseCameraAim.IsDegenerate(new Vector3(ChaseCameraAim.MinAimM * 0.5f, 0.0f, 0.0f), Up),
            "odcinek krótszy od progu nie ma czego znormalizować");
    }

    [TestMethod]
    public void ARealChaseAimIsNotDegenerate()
    {
        // Kadr nominalny: 59 m wybiegu poziomego, 0,80 m w dół.
        Assert.IsFalse(ChaseCameraAim.IsDegenerate(new Vector3(59.0f, -0.8f, 0.0f), Up));
        // I kadr z samej granicy pasma: 0,1 m wybiegu na 0,80 m w dół to 7,1° od pionu,
        // czyli sinus 0,124 — Godot już przy tym nie ostrzega i my też nie.
        Assert.IsFalse(ChaseCameraAim.IsDegenerate(new Vector3(0.1f, -0.8f, 0.0f), Up));
    }

    [TestMethod]
    public void TheColinearThresholdIsPinnedAndStricterThanTheEngine()
    {
        // Godot bada `up × kierunek` przez `is_zero_approx` na KWADRACIE długości
        // z CMP_EPSILON = 1e-5, czyli ostrzega jeszcze przy sinusie ~3,2e-3. Próg
        // niższy od tej liczby przepuszczałby ostrzeżenia do logu; mutacja
        // `1e-2` -> `1e-6` musi ten test wywrócić.
        Assert.AreEqual(1e-2f, ChaseCameraAim.ColinearSine);
        Assert.IsTrue(ChaseCameraAim.ColinearSine > 3.2e-3f, "próg poniżej progu silnika");

        // Sinus dokładnie na progu jest już użyteczny, tuż pod nim — nie.
        var justAbove = new Vector3(2.0e-2f, 1.0f, 0.0f);
        var justBelow = new Vector3(1.0e-3f, 1.0f, 0.0f);
        Assert.IsFalse(ChaseCameraAim.IsDegenerate(justAbove, Up));
        Assert.IsTrue(ChaseCameraAim.IsDegenerate(justBelow, Up));
    }

    [TestMethod]
    public void AZeroUpIsDegenerateToo()
    {
        Assert.IsTrue(ChaseCameraAim.IsDegenerate(new Vector3(59.0f, 0.0f, 0.0f), Vector3.Zero));
    }

    [TestMethod]
    public void UpDoesNotHaveToBeNormalised()
    {
        // `Vector3.Up` jest jednostkowy, ale predykat nie ma prawa na tym stać:
        // dzielenie przez długość jest w kodzie i mutacja usuwająca je ma tu paść.
        Assert.IsTrue(ChaseCameraAim.IsDegenerate(new Vector3(0.0f, -0.8f, 0.0f), Up * 1000.0f));
        Assert.IsFalse(ChaseCameraAim.IsDegenerate(new Vector3(59.0f, -0.8f, 0.0f), Up * 1000.0f));
    }

    // --- punkt celowania -----------------------------------------------------

    [TestMethod]
    public void AUsableTargetIsReturnedUntouched()
    {
        var camera = new Vector3(0.0f, 2.6f, 0.0f);
        var target = new Vector3(59.0f, 1.8f, 0.0f);
        Assert.AreEqual(
            target,
            ChaseCameraAim.LookTarget(camera, target, Vector3.Right, Up),
            "poza degeneracją kierunek osi nie ma prawa niczego podmienić");
    }

    [TestMethod]
    public void ADegenerateTargetIsReplacedByTheAxisDirection()
    {
        // Kilometraż 0: kamera 2,60 m, cel 1,80 m nad tym samym punktem.
        var camera = new Vector3(0.0f, 2.6f, 0.0f);
        var target = new Vector3(0.0f, 1.8f, 0.0f);
        var forward = new Vector3(0.0f, 0.0f, -1.0f);

        var aim = ChaseCameraAim.LookTarget(camera, target, forward, Up);

        Assert.AreEqual(camera + forward, aim);
        Assert.IsFalse(
            ChaseCameraAim.IsDegenerate(aim - camera, Up),
            "odpowiedź zastępcza nie może być tak samo zdegenerowana jak pytanie");
    }

    [TestMethod]
    public void TheReplacementIsTheSameDirectionTheCabCameraGets()
    {
        // `_cab.LookAtFromPosition(eye, eye + forward, Up)` — ta sama forma.
        var camera = new Vector3(12.0f, 2.6f, -3.0f);
        var forward = new Vector3(0.6f, 0.0f, -0.8f);
        Assert.AreEqual(
            camera + forward,
            ChaseCameraAim.LookTarget(camera, camera, forward, Up));
    }

    [TestMethod]
    public void NoChainageOfThePackageAProducesADegenerateAim()
    {
        // Przemiatanie całego pakietu A co 0,25 m po TEJ SAMEJ arytmetyce, którą liczy
        // scena — z osią wyprostowaną, bo tu chodzi o degenerację kierunku, nie o łuk.
        // Bez podmiany kierunku pierwsze 47 m dałoby 189 zdegenerowanych kadrów.
        var degenerate = 0;
        var replaced = 0;
        for (var front = 0.0; front <= AxisM; front += 0.25)
        {
            var framing = At(front);
            var camera = new Vector3((float)framing.CameraChainageM, 2.6f, 0.0f);
            var target = new Vector3((float)framing.TargetChainageM, 1.8f, 0.0f);
            if (ChaseCameraAim.IsDegenerate(target - camera, Up))
            {
                degenerate++;
            }

            var aim = ChaseCameraAim.LookTarget(camera, target, Vector3.Right, Up);
            if (aim != target)
            {
                replaced++;
            }

            Assert.IsFalse(
                ChaseCameraAim.IsDegenerate(aim - camera, Up),
                $"kilometraż {front} m dalej daje kierunek bez definicji");
        }

        Assert.AreEqual(189, degenerate, "pasmo 0..47 m co 0,25 m to 189 kadrów");
        Assert.AreEqual(degenerate, replaced);
    }
}
