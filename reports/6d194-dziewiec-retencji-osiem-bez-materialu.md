# 6.D194 — dziewięć retencji, jedna z sensem, osiem bez materiału

**13.09.2026**, na `aebd546`. Wejście: `.github/workflows/` (dziewięć kroków
`upload-artifact`), `reports/6d164-artefakt-okno-ruchome.md`, `reports/`
i `docs/TASKS.md` jako materiał historyczny.

## 1. Pole „Skąd" tej pozycji podawało rozkład, który się NIE SUMUJE

Pozycja mówiła: „**30 dni** dla czasu zestawu, po **14** dla pięciu workflowów i po
**7** dla dwóch". To jest **osiem** miejsc przy **dziewięciu** deklarowanych w tym samym
zdaniu — sprzeczność wewnętrzna, którą dało się zobaczyć bez sięgania do drzewa.

Zmierzone z YAML-a:

```
krokow upload-artifact: 9
rozklad: {14: 6, 7: 2, 30: 1}
   14  blender-smoke.yml            blender-smoke
   14  godot-first-run.yml          first-run
   14  m7-shell.yml                 m7-shell
    7  material-style-smoke.yml     material-style
   30  python-tests.yml             tools
    7  sim-tests.yml                sim
   14  station-details.yml          station-details
   14  tunnel-alignment.yml         tunnel-alignment
   14  visual-regression.yml        visual-regression
```

**Czternastka występuje SZEŚĆ razy, nie pięć.** Szósty krok stoi w
`godot-first-run.yml` — plik ma 96 KB, a krok w okolicy wiersza 1536, więc przy liczeniu
z ręki wypadł. Liczba weszła do drzewa z `reports/6d164-artefakt-okno-ruchome.md:93`
i stamtąd do dwóch miejsc w `docs/TASKS.md`.

## 2. Ile razy sięgnięto po stary artefakt — i to jest cała odpowiedź

Przejrzane: 98 wierszy z „artefak" w `reports/*.md` (25 plików) i `docs/TASKS.md`, plus
osobne przebiegi po frazach pobrania i po dziewięciu nazwach artefaktów.

| pytanie | odpowiedź |
|---|---:|
| sięgnięć po artefakt **starszy niż doba** | **1** |
| sięgnięć po **treść** artefaktu starszego niż doba | **0** |
| sięgnięć po którykolwiek z **ośmiu pozostałych** artefaktów, kiedykolwiek | **0** |

Jedyny przypadek to **6.D164** (13.09.2026): artefakt `czas-zestawu` z przebiegu 1213,
utworzony 11.09 o 12:42, odczytany po **około dwóch dobach** — ale wyłącznie
`created_at`, `expires_at`, `expired` i rozmiar. **Treści** artefaktu starszego niż doba
nie przeczytał nikt; jedyny odczyt treści to 6.D93, tego samego dnia, w którym przebieg
chodził.

**Renderów kontrolnych nie pobrał z CI nikt i nigdy.** Wszystkie oglądane w tym projekcie
rendery powstawały lokalnie. Siedem kroków wynoszących rendery (T-010, T-012, T-210,
T-211, T-220, T-400, T-902) nie ma w historii repozytorium **ani jednego** udokumentowanego
odczytu.

## 3. Rozstrzygnięcie dla każdej z trzech wartości

| dni | ile kroków | rozstrzygnięcie |
|---:|---:|---|
| **30** | 1 | **zmierzony sens** — zasięg trendu z artefaktu czasu (6.D164), i `test_timing_record` czyta go z YAML-a zamiast nosić drugą kopię |
| **14** | 6 | **nie da się rozstrzygnąć z historii tego repozytorium** — zero sięgnięć |
| **7** | 2 | **to samo, z tą samą podstawą** — zero sięgnięć |

„Nie da się rozstrzygnąć" jest tu **wynikiem pomiaru, a nie brakiem pomiaru**, i pole
„Wyjście" pozycji dopuszcza go wprost, pod warunkiem że stoi zapisany. Stoi —
w `POWOD_RETENCJI`, przy każdej wartości, z progiem długości, żeby nie dało się go
zwinąć do „bo tak".

**Czego z tego NIE wynika:** że czternaście albo siedem dni jest za mało. Zero sięgnięć
znaczy dokładnie tyle, że **nikt nie próbował** — a to jest zdanie o użyciu, nie
o wystarczalności. Dlatego retencji nie ruszam (pole „Poza zakresem" i tak tego zabrania
bez pomiaru), tylko zapisuję, czego brakuje: **pierwszego sięgnięcia**.

## 4. Co weszło do drzewa

- `test_rozklad_retencji_zgadza_sie_z_YAMLEM_a_nie_z_proza` — rozkład liczony
  `yaml.safe_load`, nie grepem (komentarz z liczbą dałby fałszywe trafienie), plus
  **żądanie, żeby każdy krok wynoszący artefakt MIAŁ `retention-days`**: bez tego
  obowiązuje domyślna retencja repozytorium, o której ten projekt nie powiedział słowa.
- `test_kazda_wartosc_retencji_ma_POWOD_albo_ZAPISANA_GRANICE` — każda wartość z YAML-a
  ma mieć wpis w `POWOD_RETENCJI` i odwrotnie; plus sprawdzenie, że trzydziestkę nosi
  **jeden** krok, bo powód z 6.D164 mówi o artefakcie czasu i o nim jednym.

## 5. Sześć kontroli negatywnych, baza 97/97, ani jedna zielona

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | rozkład wpisany wg **błędnej prozy pozycji** (14×5) | 96/97 |
| KN-2 | krok wynoszący artefakt **bez** `retention-days` | 96/97 |
| KN-3 | nowa wartość retencji (21 dni) | 96/97 |
| KN-4 | powód przy 14 zwinięty do „bo tak" | 96/97 |
| KN-5 | **pętla powodów oślepiona, słownik nietknięty** | 96/97 |
| KN-6 | drugi krok dostaje 30 dni | **95/97** |

**KN-1 jest tu najważniejsza, bo odtwarza dokładnie ten błąd, który pozycja przyniosła
ze sobą:**

```
FAIL … kroków wynoszących artefakt jest 9, a rozkład sumuje się do 8
```

Liczba wpisana z prozy zapala bramkę na **samej arytmetyce**, zanim ktokolwiek policzy
kroki — czyli sprzeczność, którą ta pozycja niosła od dnia wpisania, nie przeszłaby dziś
ani jednego przebiegu.

**KN-5 jest lekcją przeniesioną z 6.D193**, gdzie ta sama kontrola wyszła zielona **dwa
razy z rzędu**: równość pilnowała słownika, a podstawienie oślepiało pętlę. Tutaj licznik
obrotów stał od początku i zapala się natychmiast:

```
FAIL … pętla powodów wykonała 0 obrotów przy 3 wartościach — pusta pętla przechodzi
     każdą asercję w środku (zmierzone przy 6.D193)
```

## 6. Czego świadomie nie zrobiłem

- **Żadnej retencji nie zmieniłem** — pole „Poza zakresem" zabrania tego bez pomiaru,
  a pomiar mówi, że materiału na zmianę nie ma.
- **Wartości nie ujednoliciłem** — to samo pole, i byłoby to naprawianie rozbieżności,
  która usterką nie jest.
- **Kroków wynoszących artefakty nie tknąłem** — to samo pole.
- **`reports/6d164-artefakt-okno-ruchome.md` nie przepisany**, choć to z niego wyszło
  „14 dla pięciu": raport mówi o swoim dniu pomiaru i taki zostaje (6.D108). Zamiast tego
  rozkład liczy się od dziś z YAML-a, a przy wierszu 6.D164 w `docs/TASKS.md` stoi
  odsyłacz-poprawka.

## 7. Zauważone po drodze, nie tknięte

- **`sim-tests.yml` to jedyny krok pod `failure()`**, a nie `always()`, i jedyny bez
  `if-no-files-found`. Jego artefakt powstaje więc wyłącznie przy czerwonym przebiegu —
  co czyni „zero sięgnięć" jeszcze słabszą podstawą do oceny jego siedmiu dni niż
  w pozostałych przypadkach, bo artefaktu często po prostu nie ma.
- **`material-style-smoke.yml` jest jedyny z `if-no-files-found: error`** (reszta `warn`).
  Rozbieżność nie jest opisana nigdzie; nie tknąłem, bo to nie jest retencja.
- Wszystkie dziewięć kroków stoi na tym samym SHA `actions/upload-artifact@ea165f8d…`,
  zgodnie z §9 `CLAUDE.md`.
