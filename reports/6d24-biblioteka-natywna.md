# Brakująca biblioteka natywna runtime'u — mechanizm zmierzony, objaw nieodtworzony (6.D24)

**Zmierzone 09.09.2026 na:** `f8e3b4b`, kontener tej sesji.
**Przyrząd:** `timeout 20 godot --headless --path src/Game --quit-after 3` przy
`DOTNET_ROOT` wskazującym **cień** instalacji .NET (drzewo samych symlinków z jednym
plikiem zepsutym), oraz `bash doctor.sh` w tym samym cieniu.

Środowisko: Godot `4.7.2.stable.mono.official.ed1daf0bf` (headless), .NET SDK 10.0.400,
runtime 10.0.11, `src/Game` zbudowany. Blendera brak — nieistotne dla tej pozycji.

---

## 1. Skąd i co dokładnie było nieprzebadane

6.D21 wykonała sześć prób odtworzenia „ciszy do wypalenia limitu czasu" przez
**brakujący zestaw** i nie odtworzyła ani razu. Ta sama pozycja nazwała przy tym
mechanizm, którego celowo nie tknęła: brak **biblioteki natywnej samego runtime'u**,
`libhostfxr.so` albo `libcoreclr.so`. To inny poziom niż brakujące assembly, bo pada
zanim CLR w ogóle wstanie, i dlatego stał osobno jako 6.D24.

Do trzech nazw z komunikatu silnika (`hostfxr`, `hostpolicy`, `coreclr`) doszedł
w pomiarze **hostpolicy**, choć treść pozycji go nie wymieniała: to trzecia z nazw,
które sam silnik wypisuje w komunikacie o brakującej bibliotece zależnej, więc
pominięcie jej zostawiałoby jedną trzecią mechanizmu niezmierzoną.

## 2. Metoda — cień instalacji, żeby nie tknąć niczego poza repozytorium

Pole „Poza zakresem" zabrania trwałego uszkodzenia instalacji .NET. Zamiast
przemianowywać pliki w `/root/.dotnet`, każdy wariant dostaje **osobny cień**: drzewo,
w którym wszystko jest symlinkiem do prawdziwej instalacji, a mirrorowana jest
wyłącznie ścieżka do jednego pliku — tego zepsutego. `DOTNET_ROOT` wskazuje cień.
Prawdziwa instalacja nie jest przez cały pomiar otwierana do zapisu ani razu.

`PATH` jest zawężony do `/usr/bin:/bin:/usr/local/bin` (Godot leży w tym trzecim),
**bez `dotnet`** — inaczej silnik po nieudanym `DOTNET_ROOT` odpala `dotnet` przez
powłokę i wraca do PRAWDZIWEJ instalacji, czyli zepsucie zostaje zamaskowane. To nie
jest ostrożność na wyrost: dokładnie ten fallback opisuje §4.1 dokumentu środowiska
i widać go w wyjściu wariantu pierwszego (`sh: 1: dotnet: not found`).

### Kontrola przyrządu — wykonana PRZED wariantami

Cień bez żadnego zepsucia musi zachowywać się jak prawdziwy katalog. Inaczej każda
awaria wariantu mogłaby być awarią cienia:

```
BASELINE (prawdziwy root)   EXIT: 0  czas: 0.55 s  wierszy: 30
KONTROLA PRZYRZADU (cień)   EXIT: 0  czas: 0.64 s  wierszy: 30
$ diff out-baseline.txt out-kontrola.txt
  IDENTYCZNE co do wiersza
```

Baseline różni się przy tym od baseline'u 6.D21 (tam kod 4 i brak manifestu chunków,
tu kod 0) — chunki w tym kontenerze są zbudowane. Dla tej pozycji nieistotne: liczy
się różnica wobec baseline'u **tego samego dnia**, nie wobec tamtego.

## 3. Pięć wariantów — wynik

| # | co zepsute | jak | czas | kod wyjścia | wierszy na stdout/stderr |
|---|---|---|---:|---:|---:|
| 1 | `libhostfxr.so` | usunięty | 2,69 s | 134 | 25 |
| 2 | `libhostfxr.so` | obcięty do 200 B | 0,30 s | 134 | 20 |
| 3 | `libcoreclr.so` | usunięty | 0,19 s | 134 | 24 |
| 4 | `libcoreclr.so` | obcięty do 200 B | 0,35 s | 134 | 25 |
| 5 | `libhostpolicy.so` | usunięty | 0,24 s | 134 | 23 |

**Żaden z pięciu nie zawiesił procesu i żaden nie zamilkł.** Objaw z 6.D17 nie
odtwarza się więc ani przez brakujący zestaw (6.D21, sześć wariantów), ani przez
brakującą bibliotekę natywną (tu, pięć wariantów). **Nieodtworzenie jest wynikiem tej
pozycji, nie jej porażką** — tak samo jak w 6.D21.

### Wariant 1 — `libhostfxr.so` usunięty

```
ERROR: Missing hostfxr library in directory: …/cien-hostfxr-brak/host/fxr/10.0.11
   at: get_latest_fxr (modules/mono/editor/hostfxr_resolver.cpp:124)
ERROR: sh: 1: dotnet: not found
   at: try_get_dotnet_root_from_command_line (modules/mono/mono_gd/gd_mono.cpp:122)
ERROR: .NET: One of the dependent libraries is missing. Typically when the `hostfxr`, `hostpolicy` or `coreclr` dynamic libraries are not present in the expected locations.
   at: find_hostfxr (modules/mono/mono_gd/gd_mono.cpp:182)
Unable to load .NET runtime, specifically hostfxr.
ERROR: .NET: Failed to load hostfxr
```

### Wariant 2 — `libhostfxr.so` obcięty

```
ERROR: Can't open dynamic library: …/cien-hostfxr-obc/host/fxr/10.0.11/libhostfxr.so. Error: …: cannot read file data.
   at: open_dynamic_library (drivers/unix/os_unix.cpp:1066)
Unable to load .NET runtime, specifically hostfxr.
ERROR: .NET: Failed to load hostfxr
   at: initialize (modules/mono/mono_gd/gd_mono.cpp:676)
```

### Wariant 3 — `libcoreclr.so` usunięty

```
Could not resolve CoreCLR path. For more details, enable tracing by setting DOTNET_HOST_TRACE environment variable to 1
Failed to initialize context for config: /opt/metro-godot/4.7.2-stable/GodotSharp/Api/Debug/GodotPlugins.runtimeconfig.json. Error code: 0x80008087
ERROR: hostfxr_initialize_for_runtime_config failed with code: -2147450745
   at: initialize_hostfxr_for_config (modules/mono/mono_gd/gd_mono.cpp:370)
Unable to load .NET runtime, no compatible version was found.
ERROR: .NET: Failed to load compatible .NET runtime
ERROR: Parameter "godot_plugins_initialize" is null.
```

### Wariant 4 — `libcoreclr.so` obcięty

```
Failed to load …/cien-coreclr-obc/shared/Microsoft.NETCore.App/10.0.11/libcoreclr.so, error: …: cannot read file data
Failed to bind to CoreCLR at '…/shared/Microsoft.NETCore.App/10.0.11/'
Failed to create CoreCLR, HRESULT: 0x80008088
ERROR: hostfxr_get_runtime_delegate failed with code: -2147450743
```

### Wariant 5 — `libhostpolicy.so` usunięty

```
A fatal error was encountered. The library 'libhostpolicy.so' required to execute the application was not found in '…/shared/Microsoft.NETCore.App/10.0.11'.
ERROR: hostfxr_initialize_for_runtime_config failed with code: -2147450749
Unable to load .NET runtime, no compatible version was found.
ERROR: .NET: Failed to load compatible .NET runtime
ERROR: Parameter "godot_plugins_initialize" is null.
```

## 4. Ustalenie — mechanizm rozdziela się na dwa poziomy

1. **`libhostfxr.so` pada PRZED wejściem w runtime.** Brak pliku łapie resolver
   (`Missing hostfxr library in directory`), uszkodzenie pliku łapie `dlopen`
   (`cannot read file data`) — oba kończą się `Failed to load hostfxr`, czyli tym
   samym komunikatem, co brak `DOTNET_ROOT` z §4.1. **Z punktu widzenia logu te trzy
   przypadki są nierozróżnialne po ostatnim wierszu** i różnią się wyłącznie wierszem
   wcześniejszym — to jedyna rzecz, która pozwala je rozdzielić przy diagnozie.
2. **`libcoreclr.so` i `libhostpolicy.so` padają JUŻ WEWNĄTRZ hostfxr**, kodami
   HRESULT: `0x80008087` (CoreCLR nierozwiązany), `0x80008088` (CoreCLR nie dał się
   utworzyć), `-2147450749` (brak hostpolicy). Ścieżka jest inna:
   `Failed to load compatible .NET runtime` → `Parameter "godot_plugins_initialize"
   is null` → crash. **Komunikat mówi „no compatible version was found", choć wersja
   jest dokładnie jedna i dokładnie ta, której silnik chce** — zepsuty jest jeden
   plik w środku. To komunikat, za którym pójście prowadzi w złe miejsce.

Dwie rzeczy zmierzone przy okazji, obie warte zapisania, bo obie mylą przy diagnozie:

- **Log mówi `signal 11`, a powłoka widzi `134`.** W każdym z pięciu wariantów
  Godot wypisuje `handle_crash: Program crashed with signal 11`, a `$?` daje **134**,
  czyli `SIGABRT`. Cytowanie tylko jednej z tych liczb wprowadza w błąd —
  w 6.D21 sygnał 11 zgadzał się z kodem 139, tu już nie.
- **Podpowiedź silnika radzi zainstalować SDK, które jest zainstalowane.**
  `Please install the .NET SDK 8.0 or later from https://get.dot.net` pada we
  wszystkich pięciu wariantach, w których SDK jest kompletne, a zepsuty jest jeden
  plik biblioteki.

## 5. Sonda `godot .NET hostfxr` w `doctor.sh` mówi `ok` przy CZTERECH z pięciu

To nie było celem pozycji, ale pole „Wejście" wymienia tę sondę, więc została
zmierzona, a nie przeczytana z kodu. `bash doctor.sh` w każdym z pięciu cieni:

```
kontrola (nic zepsutego)   ok    godot .NET hostfxr
libhostfxr.so usunięty     WARN  godot .NET hostfxr
libhostfxr.so obcięty      ok    godot .NET hostfxr
libcoreclr.so usunięty     ok    godot .NET hostfxr
libcoreclr.so obcięty      ok    godot .NET hostfxr
libhostpolicy.so usunięty  ok    godot .NET hostfxr
```

**Cztery zepsucia, przy których Godot pada w mniej niż sekundę, sonda melduje jako
`ok`.** Powód jest w jej treści: sprawdza `find "$DOTNET_ROOT/host/fxr" -name
'libhostfxr.so'`, czyli **obecność jednego pliku o danej nazwie** — nie jego
kompletność i nie pozostałe dwie biblioteki, o których mówi komunikat samego silnika.
Ta sama ślepota dotyczy sondy `--version`: przy obciętym `libhostfxr.so` binarka
podaje wersję i kończy kodem 0

```
$ DOTNET_ROOT=<cień z obciętym libhostfxr.so> godot --headless --version
4.7.2.stable.mono.official.ed1daf0bf
EXIT: 0
```

co §4.1 dokumentu środowiska mówi od 06.09.2026 — i co dziś okazuje się prawdą także
wtedy, gdy `DOTNET_ROOT` jest ustawiony i wskazuje katalog **z** plikiem o właściwej
nazwie.

**Naprawy tej sondy ta pozycja nie robi**, bo jej „Wyjście" to pomiar i adnotacja,
a wybór między kontrolą kompletności pliku, kontrolą trzech bibliotek i prawdziwym
testem ładowania jest decyzją projektową, nie oczywistością. Zgłoszone jako **6.D60**
z kompletem sześciu pól i z liczbą 4/5 z tego pomiaru.

## 6. Co poprawione w prozie i dlaczego to jest ta sama pozycja

`doctor.sh` twierdził w podpowiedzi sondy i w komentarzu nad nią, że Godot „wisi bez
wyjścia przy starcie sceny z C#". To zdanie 6.D21 zmierzyła jako nieodtwarzalne
06.09.2026, `docs/23-environment.md` §4.1 zostało wtedy poprawione, a **podpowiedź
`doctor.sh` została ze starą treścią** — czyli narzędzie mówi dziś człowiekowi
o objawie, którego dwie serie pomiarów (6+5 wariantów) nie zastały. Poprawione tu,
bo to dokładnie ten mechanizm, o którym ta pozycja mierzy, a pole „Skończone, gdy"
żąda, żeby dokumentacja mówiła o nim **wyłącznie to, co zmierzone**. Ta sama
poprawka objęła jedno zdanie w docstringu `tools/tests/test_dotnet_version.py`,
które cytuje tamten komentarz — inaczej opis przestałby zgadzać się z opisywanym
plikiem. **Żadna asercja nie została ruszona**: to zdania w prozie, a nie warunki.

## 7. Przywrócenie — prawdziwa instalacja nietknięta

Nie było czego przywracać, i to jest różnica metody wobec 6.D21: żaden plik poza
repozytorium nie został przemianowany ani skopiowany na miejsce. Dowód — sumy,
rozmiary i czasy modyfikacji trzech bibliotek po całym pomiarze, z datą 06.09.2026,
czyli sprzed tej sesji:

```
bd28488222c43d876d574478d03183a8  libhostfxr.so     326952 B  2026-09-06 03:41:07
8aa33f2a26183719281603bf632f6f4f  libcoreclr.so    7109944 B  2026-09-06 03:41:11
c8ff5830992a7eadf8c1b0c5f7f56192  libhostpolicy.so  313480 B  2026-09-06 03:41:11
```

Wszystkie cienie usunięte zaraz po swoim przebiegu (`ls` na katalogu roboczym nie
znajduje żadnego), `git status` czyste.

## 8. Weryfikacja

```
$ bash doctor.sh; echo "kod: $?"
  ok    godot (godot)
  ok    godot .NET hostfxr
  Baza projektu jest gotowa.
kod: 0

$ python3 tools/tests/test_all.py; echo "kod: $?"
  2057/2057 przeszło
  RAZEM 92.730 s, 2057 testów, 109 modułów
kod: 0

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 590, Skipped: 0, Total: 590, Duration: 27 s
```

## 9. Czego świadomie nie zrobiłem

- **Nie tknąłem prawdziwej instalacji .NET ani Godota** — cień z symlinków daje ten
  sam pomiar bez ryzyka, którego zabrania pole „Poza zakresem".
- **Nie naprawiłem sondy `godot .NET hostfxr`** — §5, zgłoszone jako 6.D60.
- **Nie badałem wariantu „biblioteka podmieniona na inną, poprawną ELF-owo"**
  (np. `libhostfxr.so` z innej wersji runtime'u). Byłby to trzeci mechanizm —
  niezgodność wersji, nie brak pliku — i nie mieści się w treści tej pozycji.
- **Nie ruszyłem `.github/workflows/`** ani sposobu, w jaki CI ustawia `DOTNET_ROOT`.

## 10. Zauważone przy okazji, nie tknięte

**Cytat z komunikatu silnika zapalił bramkę dokumentu środowiska.** Pierwsza wersja
adnotacji w §4.1 wklejała `Please install the .NET SDK 8.0 or later` dosłownie, a
`test_the_document_declares_the_same_sdk_major` czyta wzorzec `.NET SDK <major>.<minor>`
jako deklarację TEGO dokumentu i zapaliła się na „8" przy projektach celujących
w `net10.0`. Bramka miała rację, nie ja: dokument stawiania środowiska nie ma prawa
podawać numeru SDK innego niż wymagany, niezależnie od tego, kto jest autorem zdania.
Rozwiązane bez ruszania bramki — dosłowne brzmienie zostało w tym raporcie, a §4.1
opisuje komunikat słowami. Parser ma furtkę na wiersze oznaczone jako historyczne
i nie ma jej na cudzy cytat; dopisywanie takiej furtki byłoby luzowaniem bramki
w pliku, którego ta pozycja nie dotyczy.

**`docs/TASKS.md` niesie stare brzmienie objawu w dwóch miejscach historycznych** —
w bloku ZROBIONE pozycji 6.D17 i w treści pierwotnej 6.D24 („wisi bez ani jednego
wiersza na stdout do wypalenia limitu czasu"). Nie ruszam ich i to jest wybór, nie
przeoczenie: oba są **zapisami tego, co pozycja mówiła w swoim dniu**, a nie żywymi
twierdzeniami narzędzia — a przepisywanie historii kolejki zabrałoby dowód, skąd
6.D21 i 6.D24 się wzięły (trichotomia z 6.D49: żywe odniesienie wolno poprawić,
zapis historyczny zostaje).
