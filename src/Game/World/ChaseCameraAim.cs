using System;
using Godot;

namespace MetroBxl.Game.World;

/// <summary>
/// Kadr kamery goniącej: kilometraż kamery, kilometraż celu i to, czy oś ma je czym
/// rozdzielić.
/// </summary>
/// <param name="CameraChainageM">Kilometraż kamery, już przycięty do osi.</param>
/// <param name="TargetChainageM">Kilometraż punktu, na który kamera patrzy.</param>
/// <param name="FrontChainageM">Kilometraż czoła składu, przycięty do osi.</param>
/// <param name="TrainLengthM">Długość składu.</param>
public readonly record struct ChaseFraming(
    double CameraChainageM,
    double TargetChainageM,
    double FrontChainageM,
    double TrainLengthM)
{
    /// <summary>Kilometraż ogona składu; ujemny, dopóki cały skład nie wjedzie na oś.</summary>
    public double RearChainageM => FrontChainageM - TrainLengthM;

    /// <summary>
    /// Czy kilometraż kamery mieści się w kilometrażu zajętym przez skład.
    ///
    /// <para>Kamera goniąca stoi na osi toru (<c>CabEyeLateralM</c> = 0 m) na wysokości
    /// <c>ChaseHeightM</c> = 2,60 m, a dach M7 jest 3,60 m nad główką szyny — więc
    /// pokrycie kilometrażu znaczy tu wprost „kamera siedzi w skorupie składu".
    /// Ten predykat NIE zmienia kadru; jest po to, żeby pozycja 6.B11 z
    /// <c>docs/TASKS.md</c> („kamera obserwacyjna siedzi wewnątrz geometrii przez
    /// pierwsze ~106 m") była twierdzeniem, które da się zmierzyć testem, a nie
    /// liczbą przepisywaną z cudzego raportu. Zmierzone 04.09.2026: okno to
    /// <b>0..94 m</b>, czyli długość składu, a nie 106 m — bo od 94 m ogon jest już
    /// na osi i kamera przyciśnięta do zera stoi ZA nim, tylko bliżej niż 12 m.</para>
    /// </summary>
    public bool CameraWithinTrainSpan =>
        CameraChainageM >= RearChainageM && CameraChainageM <= FrontChainageM;
}

/// <summary>
/// Celowanie kamery goniącej — cała decyzja o kadrze, bez ani jednego wywołania
/// silnika.
///
/// <para><b>Po co ta klasa istnieje.</b> <c>Node3D.LookAtFromPosition</c> potrzebuje
/// kierunku, a kierunek pionowy albo zerowy go nie ma: Godot wypisuje wtedy
/// <c>WARNING: Target and up vectors are colinear</c> i obraca kamerę o kąt, którego
/// nikt nie wybrał. Zmierzone 04.09.2026 na <c>--line --limit-kmh=70</c>:
/// <b>10 takich ostrzeżeń na przebieg</b>, jedno z <c>_Ready</c> i dziewięć
/// z <c>_Process</c>, wszystkie z <c>FirstRun.PlaceEverything</c>. Przyczyna jest
/// arytmetyczna: przy kilometrażu czoła ≤ 47 m kamera (przycięta do 0 m) i cel
/// (środek składu, też przycięty do 0 m) wypadają w TYM SAMYM punkcie osi
/// i różnią się wyłącznie wysokością — 2,60 m wobec 1,80 m. Odcinek między nimi jest
/// wtedy pionowy, czyli równoległy do „w górę".</para>
///
/// <para><b>Co robi zamiast tego.</b> To samo, co <see cref="SceneAxis.CabPoint"/>
/// robi dla kamery kabinowej i z tego samego powodu: kamera bez zdefiniowanego celu
/// patrzy <b>wzdłuż osi</b>, bo innej prawdy o kierunku w tym miejscu nie ma,
/// a zmyślona byłaby gorsza od wziętej z cięciwy. Wyciszenie ostrzeżenia
/// (<c>LookAtFromPosition</c> z innym „w górę") dałoby ten sam nieokreślony obrót,
/// tylko bez wpisu w logu.</para>
///
/// <para><b>Gdzie jest decyzja.</b> Nie w <c>FirstRun</c>. Ta sama droga, którą
/// przeszły <see cref="TrainLayout"/> i <see cref="PlatformFit"/> po audycie
/// mutacyjnym: <c>dotnet test</c> nie jest silnikiem, więc kod trzymany w węźle sceny
/// nie ma jak dostać testu jednostkowego. <see cref="Vector3"/> jest strukturą
/// zarządzaną z GodotSharp i liczy się bez uruchomionego silnika, więc cała
/// arytmetyka wchodzi tutaj, a <c>PlaceEverything</c> zostaje cienkie.</para>
/// </summary>
public static class ChaseCameraAim
{
    /// <summary>
    /// Najkrótszy odcinek kamera–cel, który jeszcze niesie kierunek [m].
    ///
    /// <para>Poniżej tego progu odcinek jest punktem i kierunku nie ma wcale — to jest
    /// osobny przypadek od „odcinek pionowy", bo wektor zerowy nie ma też czego
    /// znormalizować.</para>
    /// </summary>
    public const float MinAimM = 1e-4f;

    /// <summary>
    /// Najmniejszy sinus kąta między kierunkiem patrzenia a pionem, przy którym kierunek
    /// jest jeszcze użyteczny.
    ///
    /// <para>Próg jest <b>celowo dużo wyższy</b> niż ten, przy którym ostrzega Godot.
    /// Godot bada <c>up × kierunek</c> swoim <c>CMP_EPSILON</c> na KWADRACIE długości,
    /// więc ostrzega jeszcze przy sinusie rzędu 3·10⁻³; gdyby ta stała była równa
    /// epsilonowi silnika, bramka <c>tools/ci/assert_no_godot_warnings.py</c> łapałaby
    /// wąskie pasmo kilometraży tuż nad granicą. 10⁻² to 0,57° od pionu — kadr goniący
    /// ma nominalnie 59 m wybiegu poziomego na 0,80 m różnicy wysokości, czyli 0,8°
    /// od POZIOMU, więc ten próg nie ma jak zabrać ani jednego prawdziwego celu.</para>
    /// </summary>
    public const float ColinearSine = 1e-2f;

    /// <summary>
    /// Kilometraż kamery i celu dla składu, którego czoło stoi w
    /// <paramref name="frontChainageM"/>.
    ///
    /// <para>Kamera stoi <paramref name="behindM"/> za ogonem, cel jest w połowie
    /// składu. Oba kilometraże są przycięte do osi, bo poza nią nie ma z czego zbudować
    /// ramki toru — i to przycięcie jest źródłem całej degeneracji: dopóki czoło nie
    /// minie połowy składu, oba wychodzą zerem.</para>
    /// </summary>
    public static ChaseFraming Frame(
        double frontChainageM, double trainLengthM, double axisLengthM, double behindM)
    {
        if (trainLengthM < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(trainLengthM), trainLengthM, "skład nie ma ujemnej długości");
        }

        if (axisLengthM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axisLengthM), axisLengthM, "oś bez długości nie niesie kadru");
        }

        var front = Math.Clamp(frontChainageM, 0.0, axisLengthM);
        var camera = Math.Clamp(front - trainLengthM - behindM, 0.0, axisLengthM);
        var target = Math.Clamp(front - (trainLengthM * 0.5), 0.0, axisLengthM);
        return new ChaseFraming(camera, target, front, trainLengthM);
    }

    /// <summary>
    /// Czy odcinek <paramref name="aim"/> niesie kierunek nadający się dla
    /// <c>LookAtFromPosition</c> przy pionie <paramref name="up"/>.
    ///
    /// <para>Dwa powody odmowy i oba są tu osobno, bo mają osobne progi: odcinek za
    /// krótki, żeby go znormalizować, i odcinek równoległy do pionu.</para>
    /// </summary>
    public static bool IsDegenerate(Vector3 aim, Vector3 up)
    {
        var length = aim.Length();
        if (length < MinAimM)
        {
            return true;
        }

        var upLength = up.Length();
        if (upLength < MinAimM)
        {
            return true;
        }

        return (aim / length).Cross(up / upLength).Length() < ColinearSine;
    }

    /// <summary>
    /// Punkt, na który kamera stojąca w <paramref name="cameraPosition"/> ma patrzeć:
    /// <paramref name="targetPosition"/>, a gdy ten kierunek jest zdegenerowany —
    /// punkt o metr do przodu wzdłuż osi.
    ///
    /// <para><paramref name="axisForward"/> jest styczną cięciwy z
    /// <see cref="SceneAxis.CabPoint"/>, czyli wektorem jednostkowym wzdłuż toru.
    /// Odpowiedź zastępcza jest tym samym, co dostaje kamera kabinowa
    /// (<c>eye + forward</c>), więc obie kamery w tym samym miejscu patrzą w tę samą
    /// stronę.</para>
    /// </summary>
    public static Vector3 LookTarget(
        Vector3 cameraPosition, Vector3 targetPosition, Vector3 axisForward, Vector3 up)
        => IsDegenerate(targetPosition - cameraPosition, up)
            ? cameraPosition + axisForward
            : targetPosition;
}
