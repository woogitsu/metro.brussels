# 6.D242 — tar uruchamia `xz`, a nie pytał o to nikt

**16.09.2026**, na `bac8789`. Wejście: `tools/ci/blender_install.sh`,
`.github/actions/probe-tools/action.yml`, osiem workflowów, trzy zestawy apt,
`tools/tests/test_ci_workflows.py`, logi jobów 104702703203, 104702701527, 104702701634.
Wyjście: `xz` w sondzie ośmiu jobów, `xz-utils` w trzech zestawach apt, czytnik flag
kompresji i cztery bramki, ten raport.

---

## 1. Co się stało

16.09.2026 padły **trzy joby naraz**, na trzech różnych maszynach:

| check | maszyna | krok |
|---|---|---|
| `visual-regression` | `docker-runner-03` | `tools/ci/visual_smoke.sh` |
| `tunnel-alignment (L1_A)` | `docker-runner-01` | `tools/ci/tunnel_alignment.sh L1_A` |
| `blender-smoke` | `docker-runner-04` | `tools/ci/blender_smoke.sh` |

W dwóch logach, w których nazwy widać, stoją te same dwa wiersze:

```
  FAIL test_ci_blender_installer_NAZYWA_powod_gdy_wersja_wyszla_pusta
  FAIL test_ci_blender_installer_refuses_a_tarball_whose_checksum_does_not_match
```

a w obu komunikatach ten sam powód:

```
tar (child): xz: Cannot exec: No such file or directory
tar: Child returned status 2
```

Podsumowanie obu przebiegów, znak w znak: **2492/2494 przeszło**, `RAZEM 670,224 s`
i `604,805 s`. Czyli brak wyszedł po **ponad dziesięciu minutach pracy**.

Trzeci job, `blender-smoke`, idzie przez `doctor.sh` i nazw w jego logu nie ma —
to jest dokładnie ta ślepota, którą domyka 6.D241.

## 2. Czwarty raz ta sama klasa

| kiedy | zależność | jak wyszła |
|---|---|---|
| 07.09.2026 | `unzip` | `command not found`, kod 127 |
| 10.09.2026 (6.D77) | `curl` | wołany przez oba instalatory, w żadnym zestawie apt |
| 15.09.2026 (6.D240) | `python3-yaml` | `ModuleNotFoundError`, cztery joby naraz |
| **16.09.2026 (ta pozycja)** | **`xz`** | `tar (child): xz: Cannot exec`, trzy joby naraz |

Za każdym razem to samo: zależność realna, zadeklarowana nigdzie, działająca wyłącznie
dlatego, że maszyny puli miały ją z innych powodów. Przestała 16.09.2026 — nowe maszyny
`docker-runner-*` `xz` nie mają.

## 3. Dlaczego trzy poprzednie razy nie wystarczyły — i to jest treść tej pozycji

Tamte trzy zależności były wołane **po nazwie**: `unzip …`, `curl …`, `import yaml`.
Dawały się znaleźć grepem po nazwie i dokładnie tak zbudowane są dzisiejsze bramki
(`POLECENIA_Z_PAKIETOW`, `MODULY_Z_PAKIETOW`, skan AST importów z 6.D240).

**Tej nazwy w skrypcie nie ma.** `tools/ci/blender_install.sh:159` ma:

```sh
tar -xJf "$TARBALL" -C "$DIR"
```

Napis `xz` nie pada ani razu. GNU tar **nie dekompresuje xz wewnątrz siebie** — robi
`fork`/`exec` na osobnym binarium, i dopiero ten proces nosi nazwę `xz`. Bramka na
nazwy przepuściłaby to czwarty raz, i przepuszczała: `grep -rn xz tools/ci/` przed tą
pozycją nie dawał ani jednego trafienia w kodzie.

Dlatego 6.D242 nie kończy się na dopisaniu wiersza do tabeli. Czytnik
`kompresory_w_skrypcie` czyta **opcje, nie nazwy**: rozbiera skupisko krótkich opcji
na litery (`-xJf` → `J`) i dopasowuje opcje długie w całości (`--zstd`).

## 4. Dlaczego `xz` potrzebuje też job, który niczego nie rozpakowuje

Job `tools` z `python-tests.yml` nie instaluje Blendera i nie dotyka tarballa —
a i tak potrzebuje `xz`, bo **zestaw testów wykonuje instalator**:
`_run_blender_installer` w `test_ci_workflows.py` uruchamia `blender_install.sh`
na atrapie archiwum. 16.09.2026 `tools` przeszedł tylko dlatego, że trafił na maszynę,
która `xz` miała.

Bramka liczy więc **dwie drogi**: krok wołający skrypt wprost i krok wołający zestaw.
Zmierzone: **8 jobów** (`blender-smoke`, `godot-first-run:first-run`, `m7-shell`,
`material-style`, `python-tests:tools`, `station-details`, `tunnel-alignment`,
`visual-regression`).

## 5. Kontrole negatywne — pięć, przewidywania zapisane przed przebiegiem

Baza modułu: **92/92**. Przywracanie **z kopii w scratchpadzie**, nie przez
`git checkout --` (patrz §7). `md5sum -c` **OK** po każdej.

| # | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | `xz` zdjęte z `commands:` w `blender-smoke.yml` | 91/92 | **90/92** |
| KN-2 | `xz-utils` zdjęte z `blender.txt` | 91/92 | **91/92** |
| KN-3 | wpis `xz` zdjęty z `POLECENIA_Z_PAKIETOW` | 90/92 | **90/92** |
| KN-4 | `tar -xJf` → `tar -xf`, czyli zależność ZNIKA | 90/92 | **90/92** |
| KN-5 | czytnik oślepiony (`return set()`) | 89/92 | **89/92** |

**KN-1 obaliła przewidywanie i jest przez to najciekawsza.** Spodziewałem się jednej
czerwieni — mojej nowej bramki. Zapaliła się **także istniejąca**
`test_tool_installation_is_conditional_on_the_tool_being_missing`:

```
blender-smoke.yml: instaluje pakiet xz-utils, a sonda o `xz` nie pyta —
krok instalacji nie dostanie sygnału, że go brakuje
```

To znaczy, że stara bramka wiąże sondę z zestawem apt **w obie strony** i sama złapałaby
połowę tej usterki — pod warunkiem, że ktoś najpierw dopisałby pakiet do zestawu.
Nie złapała jej 16.09, bo **ani sonda, ani zestaw nie wiedziały o `xz`**, więc obie
strony były zgodnie puste. Bramka porównująca dwa miejsca milczy, gdy brak jest
w obu — i to jest wynik wart zapisania.

**KN-4 jest kontrolą przyrządu od strony drzewa:** po zamianie `-xJf` na `-xf`
zależność naprawdę znika, czytnik nie znajduje nic i zapalają się **dwie** asercje
pilnujące pustego zbioru — ta w `test_kazdy_kompresor…` i podłoga `JOBOW_Z_KOMPRESOREM`.
Bez nich pusty zbiór czytałby się jak brak usterki.

## 6. Weryfikacja

```
  2497/2497 przeszło
  RAZEM 215.451 s, 2497 testów, 126 modułów
```

## 7. Zauważone przy okazji, zapisane bo kosztowało

`git checkout -- <plik>` przy przywracaniu po kontroli negatywnej **skasował moją
własną, niezacommitowaną pracę** — gałąź stała na `origin/main`, więc „przywrócenie"
oznaczało cofnięcie do stanu sprzed całej pozycji. Trzy pliki trzeba było napisać
od nowa, w tym cały czytnik z bramkami. Kopie w scratchpadzie są jedyną drogą, która
tego nie robi; ta sama pułapka wyszła już raz przy 6.D225.
