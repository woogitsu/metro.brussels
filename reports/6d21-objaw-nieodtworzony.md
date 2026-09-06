# Drugi objaw z 6.D17 — nieodtworzony (6.D21)

**Zmierzone 06.09.2026 na commicie:** `7842878`

Środowisko: `dotnet` SDK 10.0.400, runtime 10.0.11
(`DOTNET_ROOT="$HOME/.dotnet"`), `GODOT_BIN` = `Godot_v4.7.2-stable_mono_linux_x86_64`
(engine mono, headless), `src/Game` zbudowany przez `dotnet build src/Game -c Debug`.
Blendera nie ma — nieistotne dla tej pozycji.

## Skąd

6.D17 (#305) opisała dwa objawy braku konfiguracji .NET dla Godota i odtworzyła
jeden — brak `DOTNET_ROOT` daje `Failed to load hostfxr` i sygnał 11. Drugi —
zawieszenie bez ani jednego wiersza na stdout przy brakującym assembly, z hostfxr
JUŻ załadowanym — został w dokumencie jako zdanie, którego 6.D17 nie pokazała, i
sama to napisała wprost. Ta pozycja miała albo odtworzyć ten objaw z limitem czasu
i wklejonym wyjściem, albo zmierzyć, że dziś nie da się go odtworzyć.

## Metoda

Baseline (bez żadnej ingerencji): `DOTNET_ROOT` ustawiony, `--headless --path
src/Game --quit-after 3`, limit 20 s.

```
$ time timeout 20 "$GODOT_BIN" --headless --path src/Game --quit-after 3
Godot Engine v4.7.2.stable.mono.official.ed1daf0bf - https://godotengine.org

[LIMIT] tryb ręczny: 72.00 km/h z planu classic-2026-L1_A (…)
ERROR: [ASSETS] brak manifestu …/build/t400/chunks/L1_A-chunks.json. …
   at: void MetroBxl.Game.FirstRun.Abort(int, string) (res://FirstRun.cs:462)
   …
real  0m1.268s
EXIT: 4
```

Zgodne z `docs/23-environment.md` §4.1 — hostfxr się ładuje, awaria jest w
`FirstRun.cs` (brak manifestu chunków, bo nie ma Blendera).

Od tego stanu wykonano sześć niezależnych sposobów na „brakujący assembly", każdy
z osobna, każdy przywrócony do stanu wyjściowego przed kolejną próbą (`git status`
czysty po każdej, dla plików spoza worktree — pliki w katalogu Godota — porównanie
sum/rozmiarów przed i po). Każdy przebieg: `timeout 20 "$GODOT_BIN" --headless
--path src/Game --quit-after 3`.

| # | co usunięto/uszkodzono | czas | kod wyjścia | co na stdout/stderr |
|---|---|---:|---:|---|
| 1 | `MetroBxl.Sim.dll` (zależność `MetroBxl.Game` w `.godot/mono/temp/bin/Debug/`) | 0,37 s | 0 | `System.TypeLoadException: Could not resolve type 'MetroBxl.Game.FirstRun'…`, potem pięć `ERROR: Cannot instantiate C# script…` dla każdej sceny |
| 2 | `MetroBxl.Game.dll` (sam projekt gry, ten sam katalog) | 0,47 s | 0 | te same pięć `ERROR: Cannot instantiate C# script…`, bez `TypeLoadException` (nie ma już czego ładować) |
| 3 | `GodotSharp.dll` silnika (`GodotSharp/Api/Debug/` obok `GODOT_BIN`) | 0,46 s | 4 | **żadnej zmiany** — identyczny przebieg jak baseline; silnik ma drugą kopię gdzie indziej (patrz Ustalenie) |
| 4 | `GodotPlugins.dll` silnika, usunięty | 0,23 s | 139 (SIGSEGV) | `ERROR: .NET: Failed to get GodotPlugins initialization function pointer` → `handle_crash: Program crashed with signal 11` |
| 4b | `GodotPlugins.dll` silnika, obcięty do 200 B (plik istnieje, jest uszkodzony) | 0,34 s | 139 (SIGSEGV) | identyczny komunikat jak #4 |
| 5 | `MetroBxl.Game.runtimeconfig.json` — `framework.version` z `10.0.0` na `99.0.0` (w katalogu projektu) | 0,86 s | 4 | **żadnej zmiany** — silnik czyta własny `GodotPlugins.runtimeconfig.json` obok `GODOT_BIN`, nie ten w katalogu projektu |
| 6 | `project.godot` → `project/assembly_name` z `MetroBxl.Game` na `MetroBxl.GameXXX` (nazwa bez odpowiadającego pliku) | 0,50 s | 0 | te same pięć `ERROR: Cannot instantiate C# script…` |

Dodatkowo sprawdzono usunięcie `MetroBxl.Game.deps.json` (nie zmienia niczego —
Godot nie używa standardowego uruchamiania `dotnet`, tylko własnego API hostfxr).

## Ustalenie

**Żaden z sześciu wariantów nie zawiesił procesu.** Każdy skończył się w
0,2–0,9 s, w jeden z trzech sposobów:

1. proces idzie dalej normalnie, bo silnik ładuje własną kopię `GodotSharp.dll` z
   `GodotSharp/Api/Debug/` obok `GODOT_BIN`, niezależną od kopii w katalogu
   projektu (warianty #3, #5) — usunięcie pliku po stronie projektu nic nie zmienia;
2. `System.TypeLoadException` / seria `ERROR: Cannot instantiate C# script…` na
   stdout/stderr i **kod wyjścia 0** (warianty #1, #2, #6) — Godot traktuje brak
   klasy skryptu jako błąd nieblokujący uruchomienia, nie jako fatalny;
3. `Failed to get GodotPlugins initialization function pointer` i **sygnał 11**
   (warianty #4, #4b) — brak albo uszkodzenie punktu wejścia, który hostfxr
   faktycznie woła, kończy proces natychmiast, nie zawiesza go.

W żadnym przebiegu stdout nie był pusty i żaden proces nie przeżył limitu czasu.

**Wniosek: symptom opisany w `6.D17` („cisza do wypalenia limitu czasu")
nie odtwarza się dziś, na Godot 4.7.2 mono + .NET SDK 10.0.400/runtime 10.0.11,
żadnym z sześciu wypróbowanych sposobów na brakujący/uszkodzony zestaw.** Nie
wyklucza to istnienia takiego scenariusza w innej wersji Godota, innej wersji
.NET, albo w rodzaju braku innym niż testowane tu sześć (np. brakujący plik
biblioteki natywnej `libhostfxr.so`/`libcoreclr.so` samego runtime'u, nie
badany tu, bo to inny mechanizm niż „brakujący assembly" z opisu usterki) — to
pozostaje nieprzebadane i nienazwane jako fakt.

## Przywrócenie drzewa

Wszystkie sześć zmian było odwracalnych i odwrócono każdą zaraz po pomiarze:
- pliki w `src/Game/.godot/mono/temp/bin/Debug/` (`MetroBxl.Sim.dll`,
  `MetroBxl.Game.dll`, `MetroBxl.Game.runtimeconfig.json`) — katalog ignorowany
  przez git (`.godot/`), przywrócone z kopii zapasowej sprzed usunięcia;
- pliki w katalogu instalacji Godota (`GodotSharp/Api/Debug/GodotSharp.dll`,
  `GodotPlugins.dll`) — poza repozytorium, przywrócone z kopii, sumy MD5/rozmiar
  potwierdzone identyczne z oryginałem;
- `src/Game/project.godot` — plik śledzony przez git, przywrócony, `git diff`
  puste, `git status` czyste po każdej próbie.

`git status` na worktree po zakończeniu wszystkich prób:

```
On branch claude/6d21-objaw-nieodtworzony
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

## Weryfikacja

```
bash doctor.sh          # zielono, WARN tylko na Blenderze (oczekiwane)
python3 tools/tests/test_all.py    # 1740/1740, kod 0
dotnet test tests/Sim.Tests        # 538/538, kod 0
```
