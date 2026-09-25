# T-400 · Visible-pass geometric primitives at 1080p

**Date:** 2026-09-25 · **Measurement base:** `99397902be438f62d4596f0c9b2481fcf72bb103` plus the two probe changes described here.

## Measurement

This extends the [earlier 1080p baseline](t400-performance-baseline-1080p.md).

Godot 4.7.2 exposes `RenderingServer.viewport_get_render_info()` for the root viewport. Its `VIEWPORT_RENDER_INFO_TYPE_VISIBLE` excludes the shadow pass, while `VIEWPORT_RENDER_INFO_PRIMITIVES_IN_FRAME` counts points, lines, **or** triangles drawn. The probe now records this as `visible_pass_primitives` alongside `visible_pass_draw_calls`. The existing global `render_primitives` monitor remains separate: [Godot's documentation](https://docs.godotengine.org/en/stable/classes/class_performance.html) describes that monitor as a count of vertices or indices across render passes. The [RenderingServer documentation](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html) defines the viewport counter and its pass types.

Run `bash tools/perf/run_1080p.sh` on Ubuntu. The script rejects a zero median for either new visible-pass counter. The existing warmup of five seconds exceeds Godot's requirement for two rendered frames before viewport statistics become available.

Three runs used the real `FirstRun.tscn`, a hidden Xvfb display, 1920×1080, Godot 4.7.2 .NET, OpenGL 4.5, and `Mesa - llvmpipe (LLVM 20.1.2, 256 bits)`. Each sampled the next 15 seconds while holding `driver_power`. The probe ran in an ext4 checkout of the stated commit with the two modified scripts copied from this branch, because .NET build output on the Windows DrvFS mount failed with `MSB3374` when setting a file timestamp. No game window appeared on the user's display.

| Run | Sample frames | Visible-pass primitives median / p95 | Visible-pass draw calls median | Frame median / p95 (ms) | Resident mesh triangles | Peak process RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 622 | 42,598 / 42,958 | 63 | 24.041 / 31.419 | 65,906 | 443,672 KiB |
| 2 | 643 | 42,502 / 42,958 | 63 | 22.530 / 30.287 | 65,906 | 443,020 KiB |
| 3 | 423 | 41,650 / 42,958 | 41 | 30.397 / 52.542 | 65,906 | 438,628 KiB |

`visible_pass_primitives` is a per-frame count of mixed geometric primitives in the visible pass. It is **not a visible triangle count**: the API does not separate points and lines from triangles. `resident_mesh_triangles` counts all scene mesh surfaces, including unseen meshes, and is also **not a visible triangle count**. Neither metric should be divided or renamed to infer visible triangles. The numbers differ from the earlier baseline because the scene changed between measurement bases. The frame times and RSS are observations under software rendering and cannot establish hardware GPU performance or a target budget.
