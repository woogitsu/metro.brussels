# Parc/Park: continuous arrival capture

The reviewed [animation](visual-evidence/parc-arrival/parc-arrival.gif) contains **106 consecutive rendered frames from one line run**, frames 1720–1825 inclusive. It shows approach, braking, a stop at Parc/Park, doors opening, and doors open. Three original 1280×720 frames (`frame-1720.png`, `frame-1790.png`, `frame-1820.png`), the raw Godot log, and SHA-256 manifest sit beside it. The GIF is resized to 960×540 and plays its 0.25 simulation seconds per frame in 80 ms, so playback is about 3.1 times simulation speed; the final frame is held for 1 second.

## Reproduce

Use Ubuntu/Xvfb, the versions pinned by the repo, and a **separate checkout of exact source commit** `1afb4d6235b5811699f5221cac58e47e8ac5957f`. The capture script refuses another commit. This keeps the frame numbers meaningful; later scene changes can shift them. The run generates geometry afresh and writes 1835 temporary PNGs under `build/`, outside Git.

```sh
export GAME_SOURCE=/absolute/path/to/checkout-at-1afb4d6
export BLENDER_BIN=/absolute/path/to/pinned/blender
export GODOT_BIN=/absolute/path/to/Godot_v4.7.2-stable_mono_linux.x86_64
bash tools/visual/capture_parc_arrival.sh
python3 -m pip install Pillow==12.3.0
python3 tools/visual/build_parc_arrival.py \
  "$GAME_SOURCE/build/t400/parc-movie/hd" \
  reports/visual-evidence/parc-arrival
```

The exact Godot invocation is in `capture_parc_arrival.sh`: `--write-movie` under Xvfb at 1280×720, `--line --limit-kmh=70 --view=outside --steps-per-frame=30 --calls=…`, `--quit-after 1835`. `--calls` makes the line run use its deterministic synthetic frame clock. The temporary output is deliberately not committed. The included `capture.log` confirms the engine recorded 1835 frames at its configured 60 movie FPS. The three original PNGs and GIF were opened and visually inspected; the GIF was also decoded and checked for 106 frames.

## Measurements from the rendered HUD

| Raw frame | Chainage | Speed | Visible state |
| ---: | ---: | ---: | --- |
| 1720 | 3858.2 m | 51.9 km/h | Parc/Park 217 m ahead |
| 1740 | 3937.3 m | 61.0 km/h | Parc/Park 138 m ahead |
| 1760 | 4007.1 m | 43.0 km/h | Braking, Parc/Park 65 m ahead |
| 1780 | 4056.5 m | 23.3 km/h | Braking on the platform approach |
| 1790 | 4069.2 m | 13.3 km/h | Parc/Park sign above platform |
| 1800 | 4075.0 m | 3.3 km/h | Final approach |
| 1804 | 4075.4 m | 0.0 km/h | First frame with `DRZWI odryglowanie` |
| 1810 | 4075.4 m | 0.0 km/h | `DRZWI otwieranie` |
| 1814 | 4075.4 m | 0.0 km/h | First frame with `DRZWI otwarte`; HUD reports stop error −0.31 m |

These values were read from the actual 1280×720 frames, not inferred from file names. The capture establishes a coherent line run and visible HUD states at Parc/Park. It does **not** prove real time motion smoothness at the player's frame rate: simulation advances 0.25 s per recorded frame and GIF playback is accelerated. Nor does this outside view identify fine M7 model details or reveal the doors themselves moving; the visible door state is the HUD. A platform-facing camera and real time playback remain useful follow-up work for #26.
