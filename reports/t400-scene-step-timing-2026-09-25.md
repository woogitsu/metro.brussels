# T-400 · Scene simulation step timing at 1080p

**Date:** 2026-09-25 · **Measurement base:** `c599e1e1da1b0d3c19f6a7681b6afe06d5727378`.

The hidden 1080p probe now times each successful call to the real `FirstRun.StepOnce` during its 15-second sample. The clock encloses the complete scene step, including game-side work around the simulation core. It does not claim to isolate `LineCore.Step`. Profiling is opt-in and starts after the five-second warmup; the ordinary game path keeps no sample array.

## Reproduce

On Ubuntu with the dependencies described in `reports/t400-performance-baseline-1080p.md`:

```sh
bash tools/perf/run_1080p.sh
```

The probe enters the real scene, holds the traction input, and writes three `[PERF]` records under the ignored `build/perf/scene-1080p/` directory. `scene_steps` must be positive. `scene_step_us` is derived from `Stopwatch.GetTimestamp()` around the actual scene step and summarized independently from frame intervals.

| Run | Scene steps | Step median / p95 (µs) | Frame median / p95 (ms) |
| --- | ---: | ---: | ---: |
| 1 | 1,802 | 13.307 / 17.005 | 16.916 / 19.336 |
| 2 | 1,803 | 2.426 / 17.394 | 17.376 / 20.559 |
| 3 | 1,803 | 13.975 / 16.589 | 16.925 / 19.317 |

The second run has a much lower step median despite the same tick count and similar p95. The cause was not established, so no budget is inferred from these runs. The frame result remains dominated by other work under this software renderer; subtracting a median step from a median frame would not produce a valid rendering time.

The recorded device was `Mesa - llvmpipe (LLVM 20.1.2, 256 bits)` under Xvfb/OpenGL 4.5. This is **not a hardware GPU measurement**. The WSL installation exposes `/dev/dxg`, but this hidden display uses llvmpipe, while the available WSLg display would create a visible game window. A hidden hardware-backed display or a verified native offscreen renderer is required before reporting GPU figures.
