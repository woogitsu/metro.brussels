# T-400: visual evidence for the current vertical slice

**Date of review:** 25.09.2026. **Measured on commit:** `4cc4237e400de1fbc416f4c7c5beac660c7bd145` (hosted frames); additional local Parc frames use `1afb4d6235b5811699f5221cac58e47e8ac5957f`. These are capture sources, not the commit that adds this report.

This is a review of actual 1280×720 Godot frames, not a claim that screenshot commands alone prove scene quality. The committed PNGs and capture logs are in [visual-evidence/t400-run-36078093066](visual-evidence/t400-run-36078093066). `manifest.json` records exact SHA-256 values and two distinct sources. `python3 tools/visual/verify_t400_evidence.py` verifies every committed file and PNG dimensions; it cannot decide whether a visual requirement is satisfied.

## Provenance and reproduction

Four frames and two metadata files came from successful hosted run [36078093066](https://github.com/woogitsu/metro.brussels/actions/runs/36078093066), head `4cc4237e400de1fbc416f4c7c5beac660c7bd145`, artifact `t-400-first-run-36078093066-1` (ID 10841256039). They were captured by `.github/workflows/godot-first-run.yml` using Godot 4.7.2 under Xvfb. Download again with:

```sh
gh run download 36078093066 --repo woogitsu/metro.brussels --dir /tmp/t400-evidence
```

The five new Parc frames and their raw logs were generated locally on Ubuntu 24.04 from `1afb4d6235b5811699f5221cac58e47e8ac5957f`. The generated geometry was made afresh, not read from a committed GLB. Reproduce without displaying the game:

```sh
git checkout 1afb4d6235b5811699f5221cac58e47e8ac5957f
export BLENDER_BIN=/path/to/pinned/blender
bash tools/dev/prepare-playable.sh build/t400
dotnet build src/Game/MetroBxl.Game.csproj --configuration Debug
export GODOT_BIN=/path/to/pinned/Godot_v4.7.2-stable_mono_linux.x86_64
mkdir -p build/t400/visual-extra
for spec in 'PARC_approach_cab 3995 cab' 'PARC_platform_chase 4075 chase' 'PARC_platform_outside 4075 outside'; do
  read -r name chainage view <<< "$spec"
  xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
    --path src/Game -- --shot="$PWD/build/t400/visual-extra/$name.png" \
    --at-chainage="$chainage" --view="$view" \
    > "build/t400/visual-extra/$name.log" 2>&1
done
xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
  --path src/Game -- --line --limit-kmh=70 \
  --shot="$PWD/build/t400/visual-extra/PARC_line_outside.png" \
  --at-chainage=4075.66 --view=outside \
  > build/t400/visual-extra/PARC_line_outside.log 2>&1
xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
  --path src/Game -- --line --limit-kmh=70 \
  --shot="$PWD/build/t400/visual-extra/PARC_line_chase.png" \
  --at-chainage=4075 --view=chase \
  > build/t400/visual-extra/PARC_line_chase.log 2>&1
cp build/t400/visual-extra/PARC_metadata.json \
  build/t400/visual-extra/PARC_line_chase_metadata.json
```

The `--at-chainage` argument is a screenshot target. The log gives the actual capture position and speed. The first three Parc snapshots use scripted motion at 80 km/h. The last two use `--line`: both logs record **4075.4 m and 0.0 km/h**. The outside PNG shows `DRZWI otwarte`, the Parc/Park sign, a platform, and a gray train body. The chase PNG shows the rear of that stopped train; its metadata reports four platform slabs near the shot, although the platform is outside that camera frame. Parc/Park already exists at chainage 4075.66 m on `data/track/L1_A.json`; `data/stations/package-a.json` includes its station record. No data change was needed.

## Reviewed coverage

| Requirement from #26 | Direct image evidence | Assessment |
| --- | --- | --- |
| Tunnel with train | `GODOT_chase_2000m.png`; rear of gray M7 body, track and tunnel visible | Observed, but visual finish remains basic |
| Entry to Parc/Park | `PARC_approach_cab.png`; track enters lit station opening, HUD says Parc 81 m ahead. `PARC_platform_outside.png` shows Parc/Park sign inside station | Observed as approach and station context; not a continuous arrival sequence |
| M7 at platform | `PARC_line_outside.png` shows a gray train body beside the Parc/Park platform and sign while stopped; `PARC_line_chase.png` shows its rear at the same stop | Observed as a train shape in complementary frames; model details and camera framing are too primitive for a convincing M7 showcase |
| Driver view | `GODOT_cab_2000m.png` and `PARC_approach_cab.png` show forward cab camera and HUD | Observed; detailed cab interior is outside this framing |
| HUD in motion | `GODOT_cab_2000m.png` and Parc shots show 80.0 km/h and chainage | Observed |
| HUD stopped with doors open | `PARC_line_outside.png` shows 0.0 km/h, `DRZWI otwarte`, Parc/Park sign, and 4075.4 m; raw log agrees. `LINIA_outside_Beekkant.png` supplies a second station | Observed at Parc/Park and Beekkant |

The current evidence does **not** close #26. It supplies the required scene states as separate frames, but not a continuous approach/braking/stop sequence or a visually convincing M7 presentation at the platform. The train appears as a simple gray shell, and the outside camera places it far from the viewer. A platform-facing camera and a recorded arrival sequence would provide stronger proof of geometry, train identity, and smooth motion. The current PNGs do not prove those qualities.

The images are a visual audit only. SHA-256 and render sanity protect file identity and basic image validity; human inspection is still required for train position, legibility, and scene quality.

## Side view follow-up

The original `outside` image places the stopped train too far away to inspect its side. A separate technical `--view=side` camera now stands alongside the first car on the adjacent track, 14 m behind the front and 4.20 m laterally from the train axis, looking 28 m behind the front. It does not encode or establish the real platform side. [The 1280×720 Parc side frame](visual-evidence/t400-side/PARC_side.png) was captured from the generated package A scene with Godot 4.7.2, Xvfb/OpenGL3, at a real line stop. The [capture log](visual-evidence/t400-side/PARC_side.log) records 54,449 simulation steps, chainage 4075.4 m, speed 0.0 km/h and `widok=Side`; the HUD visibly says `DRZWI otwarte`. PNG SHA-256: `b7f6cae53041995d9e0238203cafd3eaf6bd98a0567f9b42f513cf10967362b5`.

To reproduce after generating assets with `bash tools/dev/prepare-playable.sh build/t400` and building the game project, run Godot under Xvfb with `--line --limit-kmh=70 --shot=/absolute/path/PARC_side.png --at-chainage=4075.66 --view=side`. The existing `PARC_line_outside.png` is the before frame from an older head and a different camera. It shows a small gray train; the new frame exposes the window band and door openings across the side of the train. These are complementary diagnostic views, not a pixel-for-pixel visual regression pair. The open cutouts and plain body still make the M7 presentation unfinished; the frame does not close #26 or prove a continuous arrival.

## Platform camera follow-up

`--view=platform` places an inspection camera above a generated platform slab when the train reaches a station. It tests each candidate against the horizontal projection of the imported slab triangles, rather than the whole slab's axis-aligned bounding box, which includes empty space around curves. The candidates are 6 m to either side of the route axis; `CabPoint` is measured from the selected track, so the 2.1 m track offset is subtracted before checking them. Between stations the view falls back to the side inspection position. These are technical camera positions, not evidence of the real boarding side: package A generates slabs on both sides.

[The 1280×720 Parc frame](visual-evidence/t400-platform/PARC_platform.png) shows the stopped train and platform edge from a camera above the modeled slab. The Parc name marker is mostly occluded by the train in this revised frame; its visibility is not established here. [Its capture log](visual-evidence/t400-platform/PARC_platform.log) records 54,449 simulation steps, chainage 4075.4 m, speed 0.0 km/h and `widok=Platform`; the HUD reports open doors. PNG SHA-256: `845ba9d0761f768d27250b532c94243baf7c9fe65d9d6e462c903e6bf7f86c35`.

[The 1280×720 Beekkant frame](visual-evidence/t400-platform/BEEKKANT_platform.png) checks a second generated platform on a bend, with the train side and slab in view. [Its log](visual-evidence/t400-platform/BEEKKANT_platform.log) records 5,818 steps, chainage 509.4 m and speed 0.0 km/h. PNG SHA-256: `eabf0db796b2e5dc3b198c73468a81e9f08c314da81a06eda77c4aca366ba269`. Neither frame verifies the real platform side or completes the unfinished M7 exterior.

To reproduce from generated package A assets, run Godot 4.7.2 under Xvfb with `--line --limit-kmh=70 --shot=/absolute/path/PARC_platform.png --at-chainage=4075.66 --view=platform`; use `--at-chainage=509.73` for Beekkant. The logs are from the fixed camera geometry in commits `fa4015d` and `007aa93`.