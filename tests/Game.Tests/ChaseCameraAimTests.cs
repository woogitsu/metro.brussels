using System;
using Godot;
using MetroBxl.Game;
using MetroBxl.Game.World;
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
    private const double TrainM = 94.0;
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
