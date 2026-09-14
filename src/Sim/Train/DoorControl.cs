using System;
using System.Globalization;

namespace MetroBxl.Sim.Train;

/// <summary>Kto prowadzi cykl drzwi na postoju.</summary>
public enum DoorControl
{
    /// <summary>
    /// Cykl automatyczny: rusza sam w pierwszym kroku o zerowej prędkości i przechodzi
    /// wszystkie fazy po czasie z <see cref="DoorCycle"/>. Tryb sprzed MB-08 i domyślny,
    /// bo <b>każdy dzisiejszy wołający ma zostać nietknięty co do bitu</b>.
    /// </summary>
    Automatic,

    /// <summary>
    /// Cykl ręczny: nie rusza sam. Otwiera go <see cref="StationStop.RequestOpen"/>,
    /// a zamyka <see cref="StationStop.RequestClose"/>; między jednym a drugim drzwi
    /// stoją otwarte tak długo, jak chce maszynista.
    /// </summary>
    Manual,
}

/// <summary>
/// Powód odmowy polecenia drzwi. <see cref="None"/> znaczy „przyjęte".
///
/// <para><b>Dlaczego to enum, a nie sam napis.</b> Odmowa jest odpowiedzią, na którą
/// reaguje i HUD, i test. Napis jest do czytania przez człowieka i wolno go poprawić
/// bez ruszania kodu; powód jest do rozróżniania przez kod i musi przeżyć każdą taką
/// poprawkę. Test pytający o napis sprawdzałby korektę, a nie zachowanie.</para>
/// </summary>
public enum DoorRefusal
{
    /// <summary>Bez odmowy — polecenie przyjęte.</summary>
    None,

    /// <summary>Cyklem steruje automat; ręczne polecenia do niego nie należą.</summary>
    AutomaticControl,

    /// <summary>Skład jest w ruchu. Drzwi otwiera się na stojącym, nie na toczącym się.</summary>
    TrainMoving,

    /// <summary>Poza blokiem peronowym — nie ma postoju, do którego to polecenie by należało.</summary>
    OutsidePlatformWindow,

    /// <summary>Cykl już trwa: drzwi są otwarte albo właśnie się otwierają.</summary>
    DoorsAlreadyOpen,

    /// <summary>Drzwi nie są otwarte, więc nie ma czego zamykać.</summary>
    DoorsNotOpen,
}

/// <summary>
/// Odpowiedź na polecenie drzwi: przyjęte albo odmowa z powodem i zdaniem dla gracza.
/// </summary>
/// <param name="Refusal">Powód odmowy; <see cref="DoorRefusal.None"/> znaczy „przyjęte".</param>
public readonly record struct DoorRequestResult(DoorRefusal Refusal)
{
    /// <summary>Polecenie przyjęte.</summary>
    public static DoorRequestResult Accepted { get; } = new(DoorRefusal.None);

    /// <summary>Odmowa z podanym powodem.</summary>
    /// <param name="refusal">Powód; <see cref="DoorRefusal.None"/> jest tu błędem wołającego.</param>
    /// <returns>Odmowa.</returns>
    /// <exception cref="ArgumentOutOfRangeException">Podano <see cref="DoorRefusal.None"/>.</exception>
    public static DoorRequestResult Refused(DoorRefusal refusal) => refusal == DoorRefusal.None
        ? throw new ArgumentOutOfRangeException(
            nameof(refusal), refusal, "Odmowa musi mieć powód inny niż None.")
        : new DoorRequestResult(refusal);

    /// <summary>Czy polecenie zostało przyjęte.</summary>
    public bool Ok => Refusal == DoorRefusal.None;

    /// <summary>Zdanie dla gracza. Do czytania, nie do rozróżniania — od tego jest <see cref="Refusal"/>.</summary>
    public string Reason => Refusal switch
    {
        DoorRefusal.None => "przyjęte",
        DoorRefusal.AutomaticControl => "drzwiami steruje automat",
        DoorRefusal.TrainMoving => "skład jest w ruchu",
        DoorRefusal.OutsidePlatformWindow => "skład stoi poza peronem",
        DoorRefusal.DoorsAlreadyOpen => "drzwi są już otwarte",
        DoorRefusal.DoorsNotOpen => "drzwi nie są otwarte",
        _ => throw new ArgumentOutOfRangeException(nameof(Refusal), Refusal, "Nieznany powód odmowy."),
    };

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture, $"drzwi: {(Ok ? "przyjęte" : $"odmowa — {Reason}")}");
}
