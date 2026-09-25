# T-400: visual evidence for the current vertical slice

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
