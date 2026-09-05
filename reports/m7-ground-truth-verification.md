# T-904 verification record

**Zmierzone na commicie:** `51fd842`

Date: 2026-09-01

## Source verification

Primary STIB technical sheet (13.07.2020) was re-opened during final verification and directly confirms:
- length 94 m;
- width 2.70 m;
- floor height 1.03 m;
- 6 cars;
- 18 double doors per side;
- 2 single cab doors;
- 1.60 m door opening;
- capacity 742 manual / 758 automatic;
- empty train weight approximately 170 t;
- installed traction power 16 x 135 kW = 2160 kW;
- three-phase asynchronous traction with regenerative braking.

The 26.05.2021 STIB source independently confirms the M7 programme, CAF as builder, the 43-train framework and operational testing context, but does not promote the currently unverified physics values to primary-source spec.

## Reference-model numeric verification

Using the migrated reference equations with `dt = 1/120 s`:

```text
installed power = 2160.0 kW
F0 = 248900.0 N (design_model)
transition speed = 8.678184009642427 m/s = 31.241462434712737 km/h
AW0 accel 0->80 = 25.191666666665878 s, 337.47813150560165 m
AW2 accel 0->80 = 33.31666666666542 s, 447.9202581360521 m
AW0 service brake 80->0 = 20.933333333332786 s, 240.47942013889713 m
AW2 service brake 80->0 = 20.933333333332786 s, 240.47942013889713 m
```

These are model outputs, not claimed M7 performance measurements.

## Migration summary

- AW0: `155000 kg` historical `est` -> `170000 kg` approximate source-backed `spec`.
- AW2: the historical value is not preserved as a claimed fact. The reference load is rebuilt explicitly as `170000 + 742 * 70 = 221940 kg`, status `design_model`.
- Power: the old implicit `248.9 kN * 35 km/h ~= 2419.9 kW` is replaced by the STIB-backed installed-power ceiling `2160 kW`.
- Force/power transition: `35 km/h` legacy design point -> `31.241462... km/h`, derived from `2160 kW / 248.9 kN`; this is a `design_model` consequence, not an M7 specification.
- Vmax 80 km/h, powered-mass fraction 4/6, F0, braking, jerk, adhesion and resistance coefficients remain `design_model` because no primary source was confirmed.

## CI evidence

Zmierzone/obowiązujące 01.09.2026: repository policy had changed that day to
GitHub-hosted Actions. **This sentence is rewritten, not appended to, because it is
no longer true of the repository**: on 02.09.2026 the GitHub Actions minutes ran out
and every job moved to the bare `self-hosted` label (`CLAUDE.md` §9). The clause is
kept in the past tense so the verification record still says under which policy it
was accepted, without asserting that policy today.

Completion requires a green `Python tool tests` run for the final PR head; the
concrete run ID and conclusion are recorded in the PR/Issue verification comment
rather than hard-coded here before CI executes.
