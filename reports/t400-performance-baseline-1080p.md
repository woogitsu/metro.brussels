# T400 scene performance baseline at 1080p

**Date:** 2026-09-25 · **Measurement base:** `8e24db521e2fc634b731894fa8874a82bc26845d`.

Measured on WSL2 Ubuntu 24.04, Intel Core Ultra 7 270K Plus (18 logical CPUs). Godot 4.7.2 .NET rendered the real `src/Game/Scenes/FirstRun.tscn` through Xvfb/OpenGL 4.5 Mesa llvmpipe. This is a **software-rendering baseline**, not a GPU performance result.

## Reproduce

From a clean checkout on Ubuntu with `dotnet`, `python3`, `xvfb-run`, Blender and Godot dependencies available:

```sh
bash tools/perf/run_1080p.sh
```

The script obtains the project's pinned Godot and Blender versions, prepares the playable scene, builds the game, then makes three hidden 1920×1080 measurements. Each run warms up for five seconds and samples the following 15 seconds while holding the real `driver_power` input action. Raw logs and process high-water RSS are saved under `build/perf/scene-1080p/`. The test rejects scene errors, the wrong resolution and zero draw calls. The scene includes the real game adapter and geometry; it is not a synthetic mesh benchmark.

## Observations

| Run | Sample frames | Frame median / p95 (ms) | Draw calls median | Render primitives median | Resident mesh triangles | Godot static memory median | Linux process peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 514 | 24.009 / 49.264 | 40 | 42,324 | 62,522 | 46,589,719 B | 439,524 KiB |
| 2 | 634 | 23.748 / 30.193 | 53 | 42,636 | 62,522 | 46,666,975 B | 440,528 KiB |
| 3 | 659 | 20.597 / 40.724 | 56 | 43,092 | 62,522 | 46,612,079 B | 441,156 KiB |

The Godot render memory monitor reported 32,766,767 B in each run. Frame time varied between repeats on the shared host, so these are observations rather than a performance target. `render_primitives` is Godot's per-frame primitive monitor, which counts vertices or indices over render passes; it is **not a triangle count**. `resident_mesh_triangles` counts all scene mesh surfaces, including unseen geometry; it is **not a visible triangle count**.

## Simulation tick, separately

The existing native LineCore budget probe was run on the same WSL host, using L1_A/classic-2026, one train, 120,000 steps, three warmups and nine repeats:

```sh
dotnet build src/Sim.Runner/Sim.Runner.csproj -c Release --nologo
dotnet src/Sim.Runner/bin/Release/net10.0/MetroBxl.Sim.Runner.dll budget \
  --axis data/track/L1_A.json --signalling data/design/signalling/classic-2026.json \
  --limit-kmh 72 --exchange-s 8 --load AW2 --headway-s 90 --turnback-s 240 \
  --trains 1 --steps 120000 --warmup 3 --repeats 9 --out build/perf/sim-tick.csv
```

Result: **0.400 µs per LineCore tick**, 9.1% spread. This is a separate simulation workload. It does not measure the exact `FirstRun` scene's game-loop tick, so it must not be subtracted from the frame-time result. A scene-specific tick timer would be needed to establish that split.

## Limits

Xvfb used Mesa llvmpipe rather than the target hardware GPU. Frame timing and process memory include Godot, rendering, the scene and .NET runtime. The Godot process monitor measures frame processing, not the isolated simulation step. A hardware-rendered 1080p run and scene-specific simulation timing are still needed before setting performance budgets. No visible game window was opened.

The later [visible-pass primitive measurement](t400-visible-pass-primitives-2026-09-25.md) adds a viewport counter while retaining the same software-rendering limitation.
