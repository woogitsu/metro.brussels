# T-400 · Takeover and doors across 30, 60, and 120 logical FPS

**Date:** 2026-09-25 · **Measurement base:** `41e09354726ff7a20e5cc0286cf0aad4ce45aa5c`.

## Gap and method

The scene already compares a manual door run with the core at 4/2/1 ticks per frame, and a line run with takeover and manual door commands at 120/7 ticks per frame. These two checks did not combine the takeover and door events with the 30/60/120 logical FPS split. The new integration gate uses the committed `tests/data/m1-linia-drzwi.log` and stops after event `8040;oddaj:KABINA`, on tick 8041. No network data or input event is changed. This leaves takeover, a stop, door open, door close, and release in the tested range while avoiding the rest of the autonomous line replay.

The native core confirmed **8041 ticks, four line events, zero door refusals, one stop**. The real Godot scene, run headlessly, produced the following results:

| Logical FPS | Ticks per frame | Frames | Final chainage | Comparison with core |
| ---: | ---: | ---: | ---: | --- |
| 30 | 4 | 2011 | 509.727 m | 68 telemetry rows identical byte for byte |
| 60 | 2 | 4021 | 509.727 m | 68 telemetry rows identical byte for byte |
| 120 | 1 | 8041 | 509.727 m | 68 telemetry rows identical byte for byte |

The comparison uses tolerance zero for every telemetry column, not just the final position. The workflow also checks successful replay completion at tick 8041 and the expected, distinct frame counts. This demonstrates identical sampled Sim state for the same input and tick count through the scene and adapter while takeover and manual door commands execute. It does not measure a physical monitor's refresh rate, and the telemetry format does not expose every internal door phase; the event count, zero refusals and stopped service are separate evidence that the door commands were accepted.
