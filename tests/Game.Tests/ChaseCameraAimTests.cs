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
    public void TheChaseViewIsUnavailableUntilTheWholeTrainIsOnTheAxis()
    {
        // Decyzja właściciela z 05.09.2026: widok jest NIEDOSTĘPNY, dopóki cały skład
        // nie wjedzie na oś. Granica to długość składu — i to ta z rejestru, nie 106 m
        // przepisane z pozycji 6.B11.
        Assert.IsFalse(ChaseCameraAim.IsAvailable(0.0, TrainM));
        Assert.IsFalse(ChaseCameraAim.IsAvailable(20.0, TrainM), "zmierzone: kadr to płyta pudła");
        Assert.IsFalse(ChaseCameraAim.IsAvailable(48.0, TrainM), "zmierzone: 56,4 % bieli");
        Assert.IsFalse(ChaseCameraAim.IsAvailable(90.0, TrainM));
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(TrainM, TrainM),
            "granica NALEŻY do pasma ukrycia — ogon leży dokładnie na kamerze");
        Assert.IsTrue(ChaseCameraAim.IsAvailable(TrainM + 0.001, TrainM));
        Assert.IsTrue(ChaseCameraAim.IsAvailable(110.0, TrainM));
        Assert.IsTrue(ChaseCameraAim.IsAvailable(2000.0, TrainM));
    }

    [TestMethod]
    public void TheBandBoundaryIsTheRegisteredTrainLength()
    {
        // Granica ma pochodzić z `data/vehicle/m7-spec.json`, a nie z liczby wpisanej
        // obok. Test pyta rejestr DRUGI RAZ, wprost, żeby mutacja podmieniająca `TrainM`
        // na literał (choćby na 95,0 m z decyzji o długości peronu, T-212) miała gdzie paść.
        var registered = VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec);
        Assert.AreEqual(registered, TrainM, 1e-12, "granica pasma nie jest liczbą z rejestru");
        Assert.AreEqual(
            registered,
            ChaseCameraAim.Availability(0.0, TrainM).FromChainageM,
            1e-12,
            "widok ma się otwierać na kilometrażu równym długości składu ze spec");
        Assert.IsFalse(
            ChaseCameraAim.IsAvailable(registered, registered),
            "dokładnie na długości składu widok jest jeszcze niedostępny");
    }

    [TestMethod]
    public void AvailabilityAgreesWithTheFramingItIsAbout()
    {
        // Predykat pyta o DWIE liczby, `CameraWithinTrainSpan` liczy się z czterech.
        // Jeśli te dwa twierdzenia o tej samej geometrii rozjadą się choćby na jednym
        // kilometrażu, HUD mówiłby co innego niż kadr. Przemiatanie co 0,25 m.
        for (var front = 0.0; front <= 300.0; front += 0.25)
        {
            Assert.AreEqual(
                At(front).CameraWithinTrainSpan,
                !ChaseCameraAim.IsAvailable(front, TrainM),
                $"kilometraż {front} m");
        }
    }

    [TestMethod]
    public void TheRemainingDistanceCountsDownToTheBoundary()
    {
        Assert.AreEqual(TrainM, ChaseCameraAim.Availability(0.0, TrainM).RemainingM, 1e-9);
        Assert.AreEqual(74.0, ChaseCameraAim.Availability(20.0, TrainM).RemainingM, 1e-9);
        Assert.AreEqual(0.0, ChaseCameraAim.Availability(TrainM, TrainM).RemainingM, 1e-9);
        Assert.AreEqual(
            0.0,
            ChaseCameraAim.Availability(2000.0, TrainM).RemainingM,
            1e-9,
            "za pasmem brakuje zera metrów, a nie ujemnych");
    }

    [TestMethod]
    public void AnUnavailableViewSaysWhyAndFromWhere()
    {
        // Wiersz HUD-u i komunikat odmowy zrzutu biorą się z TEGO zdania — jedno
        // źródło, więc nie mają jak podać dwóch różnych kilometraży.
        var reason = ChaseCameraAim.Availability(20.0, TrainM).Reason;
        StringAssert.Contains(reason, "niedostępny");
        StringAssert.Contains(reason, "94.0 m", "zdanie ma mówić, OD KIEDY widok będzie");
        StringAssert.Contains(reason, "74.0 m", "zdanie ma mówić, ile jeszcze zostało");

        // Na samej granicy nie ma czego dopisywać: 94,0 m to jeszcze pasmo ukrycia,
        // a „jeszcze 0,0 m" czytałoby się jak usterka, nie jak odmowa.
        var naGranicy = ChaseCameraAim.Availability(TrainM, TrainM).Reason;
        StringAssert.Contains(naGranicy, "po minięciu 94.0 m");
        Assert.IsFalse(naGranicy.Contains("jeszcze"), naGranicy);

        Assert.AreEqual(
            string.Empty,
            ChaseCameraAim.Availability(2000.0, TrainM).Reason,
            "widok dostępny nie ma o czym mówić — inaczej HUD kłamałby przez cały przejazd");
    }

    [TestMethod]
    public void AvailabilityRefusesANegativeTrainLength()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => ChaseCameraAim.Availability(0.0, -1.0));
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
