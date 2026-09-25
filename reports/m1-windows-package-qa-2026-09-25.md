# M1 Windows x64 package smoke test after #810

**Zmierzone 25.09.2026 na commicie:** `2f1eb96518c7e96f2fc757c9f8845373e26d6aac`.

## Wynik
The Windows export used pinned Godot 4.7.2 stable mono and its matching export
templates. The source tree was that exact commit; generated `build/t400` assets
were reused from an earlier local visual build. The resulting package contained
`MetroBXL.exe`, `MetroBXL.pck`, the bundled .NET runtime, and 70 files under
`zasoby/`. Its total size was 201 MB.

The package was copied to an isolated Windows temporary directory, then launched
as a hidden **headless** process. A complete first-run simulation with
`--telemetry=qa-smoke.csv --steps-per-frame=600` exited with code 0 and wrote 321
telemetry rows. The final row was simulation step 38194, time 318.2833333333333 s,
and speed 0. Stderr was empty. The final CSV row was:

```text
38194,318.2833333333333,6653.791185780133,6559.791185780133,0,0,-1.1136219962287026,0,1,brake
```

The exported executable's SHA-256 was
`16e0ec3cfd398b938f514de95ff2474b532b5061ada78f92226dba3f7584d55d`.

For the negative check, `zasoby/M7_cab.glb` was temporarily hidden in that
isolated copy. The same hidden headless launch exited with code 14 and named
the missing file in a `[KABINA]` error:

```text
[KABINA] C:\Users\matma\AppData\Local\Temp\metro-win-package-current-qa\zasoby\M7_cab.glb nie dał ani jednej bryły.
```

The file was then restored. This checks
the missing-resource exit code and diagnostic in the actual Windows export.

The new `AcceptDialog` branch in #810 is conditional on a graphical launch and
was **not exercised** here. The headless result cannot establish that the dialog
is visible, legible, or dismissible when a player double-clicks the executable.
