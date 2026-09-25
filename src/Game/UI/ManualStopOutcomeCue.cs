using MetroBxl.Game.World;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.UI;

/// <summary>Readable cab feedback while the overhead target is out of view.</summary>
public static class ManualStopOutcomeCue
{
    /// <summary>Latest manual stop result for the cab station row, or empty before any event.</summary>
    public static string For(StationService service) => StationView.LatestStopTargetOutcome(service) switch
    {
        StopTargetOutcome.Confirmed => UiText.Get("hud.station.target-confirmed"),
        StopTargetOutcome.Served => UiText.Get("hud.station.target-served"),
        StopTargetOutcome.Missed => UiText.Get("hud.station.target-missed"),
        _ => string.Empty,
    };
}
