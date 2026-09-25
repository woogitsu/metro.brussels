# T-400 · Why the aggregate scene-step median varies

**Date:** 2026-09-25 · **Measurement base:** `54db92776c06445dbc3dfcc6d15954969a618662`.

The earlier 1080p scene probe measured roughly 1,800 real `FirstRun.StepOnce` calls in each 15-second sample, but one run's median was 2.426 µs and two others were around 13–14 µs. The probe now records each step's ordinal within the rendered frame and reports first steps separately from later steps. The timer still encloses the same scene step; storing the ordinal happens after the timer stops.

Run the hidden probe with `bash tools/perf/run_1080p.sh`. Three new runs on the same WSL2/Xvfb Mesa llvmpipe host gave:

| Run | First steps | First median (µs) | Later steps | Later median (µs) | Aggregate median (µs) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 917 | 15.316 | 882 | 2.155 | 14.023 |
| 2 | 943 | 15.368 | 857 | 2.202 | 14.423 |
| 3 | 893 | 15.119 | 906 | 2.156 | 5.144 |

The first step in a rendered frame is consistently about 15 µs; subsequent steps are about 2.2 µs. Each group accounts for about half the sample, so a small change in their proportions moves the aggregate median between these modes. This explains the earlier median spread **as a measurement aggregation effect**. It does not establish which operation makes the first step slower; cache state and frame scheduling remain hypotheses, not measured causes. These times are for the whole scene step, not just `LineCore.Step`, and this renderer is software llvmpipe rather than a hardware GPU.

The probe checks that the first and later counts sum to all timed steps. Comparisons and future budgets should use the separated distributions and frame timing, not the unstable aggregate median alone.
