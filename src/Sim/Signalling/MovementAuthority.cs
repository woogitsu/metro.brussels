using System;
using System.Globalization;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Powód, dla którego movement authority kończy się właśnie tam, gdzie się kończy.
///
/// Powód jest częścią authority, a nie komentarzem do niego: kabina ma pokazać coś
/// innego przy „koniec toru" niż przy „skład przed tobą", a test ma sprawdzić, że
/// authority skróciło się z **tego** powodu, a nie przypadkiem.
/// </summary>
public enum AuthorityLimit
{
    /// <summary>Koniec planu — dalej nie ma bloków.</summary>
    EndOfLine,

    /// <summary>Następny blok jest zajęty przez inny skład.</summary>
    OccupiedBlock,

    /// <summary>Następny blok jest zarezerwowany pod cudzą trasę.</summary>
    ReservedByOtherRoute,

    /// <summary>
    /// Plan wymaga zaryglowanej trasy, a następny blok do trasy tego składu nie należy
    /// — albo składu w ogóle nie prowadzi żadna trasa.
    /// </summary>
    BlockNotReserved,
}

/// <summary>
/// Movement authority: dokąd wolno jechać temu składowi i dlaczego nie dalej.
///
/// <para><b>Zasada 3 z T-313:</b> authority kończy się **przed** obszarem zajętym albo
/// niezabezpieczonym. W tym modelu znaczy to dosłownie: koniec authority leży na granicy
/// ostatniego bloku, który przeszedł kontrolę, pomniejszonej o
/// <see cref="SignallingPlan.AuthorityMarginM"/>. Zapas jest w planie i wynosi zero,
/// bo rzeczywistego overlapu STIB nie ma w żadnym publicznym źródle — model nie
/// wymyśla liczby, której nie zna.</para>
///
/// <para><b>Authority nie zna prędkości.</b> Zamiana odległości na dopuszczalną prędkość
/// należy do <see cref="TrainProtection"/> i idzie przez tę samą krzywą hamowania, co
/// prowadzenie składu (T-311). Gdyby authority niosło prędkość, w repo byłyby dwie
/// krzywe hamowania — dokładnie to, czego zabrania zasada 4 z T-313.</para>
/// </summary>
/// <param name="TrainId">Skład, którego dotyczy.</param>
/// <param name="FrontChainageM">Chainage czoła składu w chwili wyznaczenia.</param>
/// <param name="EndChainageM">Chainage końca authority; nigdy przed czołem składu.</param>
/// <param name="LimitBlockId">Blok, który wyznaczył koniec.</param>
/// <param name="Reason">Dlaczego authority kończy się w tym miejscu.</param>
public readonly record struct MovementAuthority(
    string TrainId,
    double FrontChainageM,
    double EndChainageM,
    string LimitBlockId,
    AuthorityLimit Reason)
{
    /// <summary>Odległość od czoła składu do końca authority; nigdy ujemna.</summary>
    public double DistanceM => Math.Max(0.0, EndChainageM - FrontChainageM);

    /// <summary>Czy skład ma w ogóle prawo się ruszyć.</summary>
    public bool AllowsMovement => DistanceM > 0.0;

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{TrainId}: authority do {EndChainageM:F2} m ({DistanceM:F2} m przed czołem), " +
        $"ogranicza {LimitBlockId} — {Reason}");
}
