# Rejestr gałęzi do skasowania

**Snapshot na commicie:** `737d592`
**Data:** 2026-09-02

Audyt repozytorium z 02.09.2026 wskazał 86 gałęzi zdalnych jako problem higieny. Ten
plik istnieje po to, żeby kasowanie **nie było nieodwracalne**: każda skasowana gałąź
ma tu zapisany SHA i numer PR-a, więc odtworzenie to `git branch <nazwa> <sha>`
i push, bez polegania na przycisku „Restore branch" w GitHubie.

## Kryterium

Audyt ostrzegał wprost, że `ahead_by == 0` **nie jest** kryterium, bo squash-merge
sprawia, że scalona gałąź wygląda na rozjechaną. Użyte kryterium jest inne i wymaga
obu warunków naraz:

1. gałąź ma PR, a ten PR ma ustawione `merged_at`;
2. **HEAD gałęzi jest identyczny z head-em scalonego PR-a** — czyli po scaleniu nie
   doszedł ani jeden commit.

Warunek 2 nie jest formalnością. Złapał jeden przypadek na 79.

## Gałąź, która ZOSTAJE

| gałąź | PR | powód |
|---|---|---|
| `axis-reaches-last-station` | #86 | HEAD `31e24f9` ≠ head PR-a `c68e877` — **jeden commit po scaleniu**. Gałąź niesie pracę, której nie ma w `main` |

## Gałęzie skasowane

Wszystkie spełniły oba warunki. SHA jest head-em scalonego PR-a i zarazem HEAD-em
gałęzi w chwili kasowania.

| gałąź | PR | SHA |
|---|---|---|
| `plan-fazy-2-4` | #117 | `8682f061b43b0d14ce3d944a47dd6bc6338f3813` |
| `testy-manifest-i-zalozen` | #116 | `a9ace5806fbc9d448fa480e552e2f14fc521b1c9` |
| `testy-fetcherow` | #115 | `4522410a042ce39265d2b92f604fe9d9003b6660` |
| `testy-warstwy-godota` | #114 | `9c8baba4335506d28e24c5044151649d92f51b7c` |
| `testy-detail-markers` | #113 | `b0993d0851003cec6105c8b25629009493ab47c9` |
| `issue-106-akumulator-klatek` | #112 | `fc495bb584bba348bcf580de2d7617bc39b9ed6c` |
| `issue-107-brak-skladu` | #111 | `4d998d9c819470a2153afd24545562787bca676a` |
| `t211-station-kit` | #110 | `e947a143affd944ce14a49c28aab4b1a8ff2c269` |
| `ci-self-hosted` | #109 | `72b00f149477218fb80dae4e387a4a2e35dd0c2d` |
| `t211-zestaw-stacji` | #108 | `afcc15b3c71031988d6c25e6f8b840ad54548e3a` |
| `game-bramki-ktore-nie-porownuja` | #105 | `596e16d21e4bc096f4d56bddea920e7031dabad7` |
| `r007-wymiary-peronu` | #104 | `79975811566da0d7f9793271d69f085ddff825b1` |
| `issue-100-testy-modulow` | #103 | `a4357fc8ef72730a109e253e509f7b83a2c03437` |
| `issue-99-max-speed` | #102 | `f0fcbb5c97f5f7a6e153c132ee174da29fb1a980` |
| `t314-cbtc-tryb` | #101 | `6c4423e14b10ead620dbf0e6955651d3ec110538` |
| `stale-po-audycie` | #98 | `866bd4d4eada5931c5535eff7a65f1720a9f4e1e` |
| `testy-po-audycie` | #97 | `9f8614f5706aee240b6912befb517786ff48c516` |
| `rdzen-po-audycie` | #96 | `e43e192651ef6aacaf35fab1e67bea6523cdd316` |
| `tasks-sync-po-scaleniach` | #95 | `4873224ed0011e4155db3b0e04fe20406dbcc7ff` |
| `ci-bramki-ktore-bramkuja` | #94 | `2b50ad1ee426ad17907ac9f848176ce40f5fe341` |
| `t-011-detail-markers-do-main` | #93 | `aefcb23a8d2fa0b8bb5b046a82eae855e02dc1a2` |
| `ci-apt-cache` | #92 | `11cd8f0c04d406bba3ddaf4a988c432ea3ff86b4` |
| `t-313-classic-signalling` | #91 | `eda63c3d06037553f5dfe9c0610ee341a3045294` |
| `r-004-station-ground-truth` | #90 | `982c0ffe01d097f4ebc6ac77f1595b1102ee9daa` |
| `ci-apt-hardening` | #89 | `2cc776db9b6f86efa684b73d290af18a2e86c023` |
| `render-check-blank-frame` | #88 | `123d8eecb305f6c00247fa8536189518167afbcb` |
| `t-011-detail-markers` | #87 | `2fc5a0b3d05b3d716081bedf93f8a93ac62e7194` |
| `r-006-line-speed` | #85 | `a255ceac0c97514e874d82bcd1144a9698efa367` |
| `synthetic-axis-out-of-data` | #84 | `0e0faa11ae1b2a334e2a9084ea97656a17da2da2` |
| `axis-station-overrun` | #83 | `043f077dcddca6df1a326de3900eff45181bc06d` |
| `t-400-station-stops` | #82 | `46243c6630b7668f2470d9084c6d794c06251918` |
| `tasks-sync-t311-t312` | #81 | `81548e10bce447e8fba115ec09d6a5faffdefa03` |
| `t-113-timetable` | #80 | `e0de4a0d0c8d48072752a06c41f414e4f6e6ce18` |
| `t-312-doors` | #79 | `349044e351661df45a6d522dce5ab2f0ac6d48a2` |
| `t-311-braking` | #78 | `88468a2d4a8dc5eacefa31daa65055c8fb2cc028` |
| `t-012-godot-capture` | #77 | `87e54b2bd2b7e610f41b884810153527e8a1e076` |
| `tasks-refresh` | #76 | `bbb207e7ec2925dfa446b2902f12553a7cbda6a9` |
| `e13-chainage-map` | #75 | `b92cda13f573242d199442613c438dc6b6c3e83d` |
| `heartbeat-routine` | #74 | `326b6285d2fce95e55d887fa7252e55d897c351b` |
| `e14-clearance-be` | #73 | `37e7731aa4470636170b8796f309be7699c54241` |
| `t-210-packages-be` | #72 | `562a3a308878ce627cf22394b720536a9e6c8290` |
| `t-400-first-run` | #71 | `12af3b6d74eb9df330d19d7a0e984c5faf7a997a` |
| `e11-surface-vs-tunnel` | #70 | `e2243dbcb595e455cf7d24ededf67f41d650b637` |
| `t-310-physics-core` | #69 | `067a9002a9595b82c5f8bec42d572656432eb878` |
| `t-111-packages-bf` | #68 | `043ba27a385ec03840783acee8193d5daf730b1b` |
| `t-012-topology-invariant` | #67 | `885dd05ddf418883c1304f4eb069b090a9256b78` |
| `t-220-supersede-note` | #66 | `faed9b3e3829dc4f49dcfd8000b97ba26a43ceaf` |
| `t-220-clearance-profile` | #65 | `707e6a28513a373bf21c2e066689f74d33382be9` |
| `t-210-tunnel-lod` | #64 | `72cc17a211e60af4a74b9eb26e55e96d5d73d0b2` |
| `t-210-level-note` | #63 | `77b7c81945534fa579197c69fe44e30c79955c37` |
| `t-211-station-survey` | #62 | `f4fa282715f5985c09450f78aac72c6e4ad08f1c` |
| `t-210-tunnel-survey` | #61 | `6a364af346ff261b5798b904eee88ba14d11eb57` |
| `chore-tasks-current` | #60 | `aeadcb5e34daad6373baf9f9c7bfec171c646bbc` |
| `t-114-data-freshness` | #59 | `484733395174f359eef52f02fcd3a3886eea57b0` |
| `chore-readme-current` | #58 | `537e2754390ea691844ecd60c83bc8a29ec6f06f` |
| `t-012-dimension-audit` | #57 | `56aaf3676bbbe16f1340d912e0c37987d9e84b47` |
| `t-012-section-perpendicular` | #56 | `a650e433d88cef5539693442e9ffd0454415a58a` |
| `t-220-vehicle-in-tunnel` | #55 | `2c1a91118b0a197714402940064c2922cee13d7a` |
| `t-210-chunk-streaming` | #54 | `a3d486837670fee474bfbc23190950e049addb45` |
| `t-111-inspire-rail-spacing` | #53 | `d7b1eaa520fb30c08fd58b275f523829827c2401` |
| `t-012-bounded-framing` | #52 | `17c94120f46cdc4a4115c92381e39f346e9dc48f` |
| `t-210-tunnel-width` | #51 | `9ee72535a5137a9a6cee25c4a180783abdab0c3f` |
| `t-210-curve-clearance` | #50 | `271b96ae16fa017500f5c2fbb80564d1588a1c55` |
| `t-210-tunnel-package-a` | #49 | `dc6c17c985b2d5c8c91a07b884b13eb0b2c19f2d` |
| `t-012-inside-camera-anchor` | #48 | `d4687fc27a774e22ec1a904e58494f3fbfa54630` |
| `t-111-osm-per-track` | #47 | `34d175860bd2e26db2199611fa1c92b20cfa6980` |
| `t-111-alignment` | #46 | `3d7d3bdb07b91987cad71e735535b4b4f45b7848` |
| `t-110-gtfs-import` | #45 | `35f506050bf6b7ba97fc0a7b48030145b415cf9d` |
| `t-012-geometry-count-tolerance` | #44 | `c8d0f072eae8ee5120660c4effffb4f970855fed` |
| `t-220-m7-shell` | #43 | `6630db948de1957af2cc2c985e2167ed70103895` |
| `t-012-visual-regression` | #42 | `6789f98730ef011da30607666cf4661d15aae8eb` |
| `t-114-data-provenance` | #41 | `4f18e4865291478a7877e44e961c50fa5906a47d` |
| `chore/github-hosted-actions` | #40 | `2fa599dec41cd340a33bab5a087345b9748a6324` |
| `t-010-blender-wsl2-pipeline` | #36 | `c592b6aed079ae4b05a2406309535ad8514db058` |
| `r-005-infrastructure-ground-truth` | #35 | `0a6999c0acf0c3b561444f206327ba8c56cedde6` |
| `r-003-signalling-ground-truth` | #34 | `1e9ed8409f53dfadedf4ee849960409d2362c883` |
| `t-904-m7-ground-truth` | #33 | `cfb9fab11b789e699f9daf0b9be9e40f0d37b639` |
| `r-002-open-data-sources` | #28 | `41c74c1d51464c002fa9de3b332be4030753d13f` |

## Gałąź skasowana z innego powodu

`ci-wsl2` nie ma PR-a, więc kryterium wyżej się do niej nie stosuje. Ma za to dowód
mocniejszy: **zero commitów unikatowych wobec `main`** (`git rev-list --count
origin/main..origin/ci-wsl2` = 0), czyli jej tip jest przodkiem `main` i skasowanie
nie traci dosłownie niczego. Do tego 80 commitów w tyle i koncepcja nieaktualna —
CI stoi dziś na gołej etykiecie `self-hosted`, bez `wsl2` (`CLAUDE.md` §9).

| gałąź | PR | SHA |
|---|---|---|
| `ci-wsl2` | brak | `2786388` |

## Kasowania NIE wykonano — 403

Sesja agenta **nie ma uprawnienia do usuwania refów**. Zwykły push działa,
`git push origin --delete` kończy się:

```
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
fatal: the remote end hung up unexpectedly
```

Weryfikacja, że to nie awaria sieci: ten sam remote przyjął push gałęzi
`audyt-galezi` minutę wcześniej, a proxy nie zgłasza żadnych `recentRelayFailures`.
Blokada dotyczy wyłącznie usuwania refów.

Lista niżej jest więc **gotowa do wykonania, ale niewykonana**. Polecenie do
skopiowania — bezpieczne, bo dotyczy dokładnie tych 79 gałęzi i żadnej innej:

```bash
git push origin --delete \
    plan-fazy-2-4 \
    testy-manifest-i-zalozen \
    testy-fetcherow \
    testy-warstwy-godota \
    testy-detail-markers \
    issue-106-akumulator-klatek \
    issue-107-brak-skladu \
    t211-station-kit \
    ci-self-hosted \
    t211-zestaw-stacji \
    game-bramki-ktore-nie-porownuja \
    r007-wymiary-peronu \
    issue-100-testy-modulow \
    issue-99-max-speed \
    t314-cbtc-tryb \
    stale-po-audycie \
    testy-po-audycie \
    rdzen-po-audycie \
    tasks-sync-po-scaleniach \
    ci-bramki-ktore-bramkuja \
    t-011-detail-markers-do-main \
    ci-apt-cache \
    t-313-classic-signalling \
    r-004-station-ground-truth \
    ci-apt-hardening \
    render-check-blank-frame \
    t-011-detail-markers \
    r-006-line-speed \
    synthetic-axis-out-of-data \
    axis-station-overrun \
    t-400-station-stops \
    tasks-sync-t311-t312 \
    t-113-timetable \
    t-312-doors \
    t-311-braking \
    t-012-godot-capture \
    tasks-refresh \
    e13-chainage-map \
    heartbeat-routine \
    e14-clearance-be \
    t-210-packages-be \
    t-400-first-run \
    e11-surface-vs-tunnel \
    t-310-physics-core \
    t-111-packages-bf \
    t-012-topology-invariant \
    t-220-supersede-note \
    t-220-clearance-profile \
    t-210-tunnel-lod \
    t-210-level-note \
    t-211-station-survey \
    t-210-tunnel-survey \
    chore-tasks-current \
    t-114-data-freshness \
    chore-readme-current \
    t-012-dimension-audit \
    t-012-section-perpendicular \
    t-220-vehicle-in-tunnel \
    t-210-chunk-streaming \
    t-111-inspire-rail-spacing \
    t-012-bounded-framing \
    t-210-tunnel-width \
    t-210-curve-clearance \
    t-210-tunnel-package-a \
    t-012-inside-camera-anchor \
    t-111-osm-per-track \
    t-111-alignment \
    t-110-gtfs-import \
    t-012-geometry-count-tolerance \
    t-220-m7-shell \
    t-012-visual-regression \
    t-114-data-provenance \
    chore/github-hosted-actions \
    t-010-blender-wsl2-pipeline \
    r-005-infrastructure-ground-truth \
    r-003-signalling-ground-truth \
    t-904-m7-ground-truth \
    r-002-open-data-sources \
    ci-wsl2
```

Alternatywnie w GitHubie: **Settings → General → Automatically delete head branches**
załatwia to na przyszłość, ale nie sprząta zaległości.

## Czego ten rejestr NIE obejmuje

Gałęzie **bez PR-a** nie były rozpatrywane, z jednym wyjątkiem opisanym wyżej.
Gałąź bez PR-a nigdy nie przeszła przez przegląd, więc nie ma dowodu, że jej
zawartość jest w `main`. Konkretnie zostaje `t-111-inspire-rail` — bez PR-a
i z jednym commitem unikatowym wobec `main` (`17c9412`), którego nikt nie sprawdził.

Nie zostały ruszone również gałęzie otwartych PR-ów: `t-902-art-direction` (#39),
`t-905-audio-rights` (#38), `t-903-rights-matrix` (#37) — objęte jawnym zakazem
właściciela — oraz `t320-trasa-linii` (#118) i `audyt-p0-dokumentacja` (#119).
