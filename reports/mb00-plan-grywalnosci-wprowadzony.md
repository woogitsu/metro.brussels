# MB-00 — plan grywalności wprowadzony, i jedno twierdzenie audytu padło

**13.09.2026**, na `bd29ced`. Wejście: audyt zewnętrzny z 13.09.2026 (snapshot `main`
`c2a5f9d76a9b4bc401b6ec08eeabf18c21fdbb97`), `CLAUDE.md`, `docs/TASKS.md`,
`docs/TASK-TEMPLATE.md`, `tools/tests/test_backlog.py`,
`reports/droga-do-grywalnosci.md`, Issue #25 i #26.

## 1. Co weszło

- **`docs/PLAYABILITY.md`** — plan produktu: M1 (grywalny trening jednym M7) i M2
  (autonomiczna linia z przejęciem sterowania), kontrakt M1 z siedmioma punktami odbioru,
  kolejność MB-00…MB-08, zmiana polityki kolejki i lista rzeczy odłożonych.
- **Pasmo M w `docs/TASKS.md`** — dziewięć pozycji, każda z kompletem sześciu pól.
- **`CLAUDE.md`** — `docs/PLAYABILITY.md` w mapie dokumentów §3 oraz **dopisany**
  (nie przepisany) akapit §8 o pierwszeństwie pasma M przy aktywnym kamieniu milowym.
- **Bramka polityki** w `tools/tests/test_backlog.py` — trzy testy, w tym jeden
  pilnujący, że zmiana **niczego nie rozluźniła**.

## 2. Twierdzenia audytu sprawdzone, nie przyjęte na słowo

Snapshot audytu jest od dzisiejszego `main` starszy o **jeden commit i dziewiętnaście
minut** (`c2a5f9d` → `44804bd`), a ten commit nie rusza ani jednego pliku w `src/`,
`data/`, `.github/` ani `tools/blender/`. Osiem twierdzeń o stanie kodu sprawdzono
po kolei — **wszystkie osiem aktualne**, każde z adresem:

| twierdzenie | dowód |
|---|---|
| brak końca ręcznego przejazdu | `FirstRun.cs:988-1060`; `_done = true` tylko w czterech `Finish*`, żaden nie dotyczy trybu ręcznego |
| `_done` odcina `R`/`Esc` | `FirstRun.cs:1010` `if (_done) return;` PRZED odczytem klawiatury w `:1015-1030` |
| kabina niewpięta | `grep m7_cab` w `src/Game/**` — zero trafień |
| jeden `TrainView` | `FirstRun.tscn:32`, `FirstRun.cs:362`; scena bierze `Trains[0]` (`:1117`, `:1690`) |
| `placeholders.json` to metadane | `data/audio/` = dwa pliki `.json`, zero nagrań, zero `AudioStream` w `src/` |
| ścieżki poza `res://` | `FirstRun.cs:477-481` — `res://` + `../../` |
| reguła zapasu egzekwowana | `test_backlog.py:70`, `:694-698`, `:914` |

## 3. Co PADŁO: „HUD nie mówi graczowi, co ma zrobić"

Audyt opisuje HUD jako „tekstowy diagnostyczny i pomoc klawiszowa" i z tego wyprowadza
całe MB-03. **Pomiar mówi co innego.**

- Wiersz `Position` niesie **nazwę następnej stacji i odległość do niej** —
  `src/Game/UI/UiText.cs:74`: `„chainage {0} m / {1} m     {2} za {3} m"`.
- Wiersz `Station` niesie **odległość do punktu zatrzymania razem z oknem ±**
  i komunikatem `„  W OKNIE — zatrzymaj się"` — `UiText.cs:90-91`, składany
  w `FirstRun.StationLine()` (`src/Game/FirstRun.cs:1721-1793`) — plus fazę drzwi,
  resztę postoju, błąd zatrzymania i licznik obsłużonych oraz miniętych stacji.

**MB-03 jest z tego powodu przepisane wobec brzmienia audytu, a nie powtórzone:**
zadaniem nie jest dodanie celu i odległości, bo są, tylko **priorytet informacji** —
co widać od razu, co dopiero na postoju, a co idzie do osobnej diagnostyki. Siedem
etykiet, z czego cztery startują ukryte (`src/Game/UI/Hud.cs:53-62`).

**Drugie ustalenie, którego audyt nie miał:** `export_presets.cfg` nie tylko nie istnieje
— jest **jawnie w `.gitignore:31`**. MB-04 musi więc zmienić także `.gitignore`.

## 4. Zmiana polityki kolejki — co się zmieniło, a co NIE

**Zmieniło się:** przy aktywnym kamieniu milowym pasmo M ma pierwszeństwo przed
pasmami A–D, a poboczne znalezisko zapisuje się krótko i nie bierze przed domknięciem
kamienia.

**Nie zmieniło się nic innego** — i to jest sprawdzane, nie deklarowane:
`test_pasmo_M_NIE_wchodzi_do_liczb_zapasu_i_to_jest_zmierzone` mierzy, że dziewięć
pozycji MB **nie weszło** ani do `queue_items`, ani do `detail_sections`, oraz że
`MINIMUM_READY_ITEMS` nadal wynosi 12. Gdyby weszły, próg spełniałby się samym planem
i przestałby mierzyć to, co mierzył — a różnicy „przybyło pracy" od „zmieniono miarę"
nie dałoby się już zobaczyć.

**Dlaczego ta zmiana w ogóle:** między 6.D190 a 6.D202 domknąłem **trzynaście pozycji
i ani jedna nie przybliżyła gry do grywalności**. Reguła zapasu działała dokładnie tak,
jak napisano — i właśnie dlatego praca nigdy nie dochodziła do kamienia milowego.

## 5. Pięć kontroli negatywnych, baza 36/36

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | pole „Poza zakresem" zdjęte z bloku MB-05 | 35/36 |
| KN-2 | `queue_items` łapie także `MB-*` | 35/36 (**„pasmo M weszło do zapasu"**) |
| KN-3 | `MINIMUM_READY_ITEMS` obniżone z 12 na 9 | **33/36** — trzy bramki naraz |
| KN-4 | `CLAUDE.md` bez wskazania planu | 35/36 |
| KN-5 | pętla po blokach pasma M obiega raz zamiast dziewięciu | 35/36 |

`md5sum -c` na trzech plikach po każdej: `OK`. Ani jedna zielona.

**KN-3 zapala TRZY bramki i to jest tu treścią:** obniżenie progu łapią równolegle
`test_dokument_i_kod_mowia_o_tej_samej_liczbie` (6.D109), `test_bramka_zgodnosci…`
i nowa bramka pasma M. Zmiana polityki **nie zdjęła** żadnej z dwóch starych — dołożyła
trzecią, z innego kierunku.

## 6. Czego świadomie nie zrobiłem

- **Nie tknąłem `reports/droga-do-grywalnosci.md`.** Raporty są historią (6.D108).
  Wskaźnik, że jako plan został zastąpiony i że jego §1.2 jest nieaktualny od #239
  i #249, stoi w `docs/PLAYABILITY.md`, a nie w tamtym pliku.
- **Nie zmieniłem ani jednej linii zachowania gry.** MB-00 jest planem i dokumentem;
  pierwsza zmiana kodu gry to MB-01.
- **Nie wykonałem playtestu i nie twierdzę, że wykonałem.** Tak samo jak audyt:
  w tym środowisku nie ma Godota, Blendera ani interaktywnego okna.
- **Nie zamknąłem Issue #26.** M1 jest etapem pośrednim; pełne kryteria #26 ocenia się
  przy M2, po MB-08.

## 7. Zauważone po drodze, nie tknięte

- **`docs/TASKS.md` ma 1 547 678 B (1,55 MB).** Audyt podawał „około 1,53 MB" i miał
  rację **dla swojego snapshotu** (1 533 427 B). Przyrost od snapshotu: **+14 251 B
  w dwóch commitach**, czyli około 7 kB na pozycję kolejki. Przy tym tempie sam plik
  kolejki rośnie szybciej niż kod, którego dotyczy.
- **HUD ma siedem etykiet, z czego cztery startują ukryte.** Ta czwórka zapala się
  warunkowo i nikt nie zmierzył, ile z nich widać naraz w typowej chwili przejazdu —
  a to jest liczba, od której zaczyna się MB-03.
- **`FirstRun.cs` ma 2282 wiersze** i mieści pięć trybów uruchomienia oraz składanie
  wierszy HUD-u. Audyt zakazuje generalnego refaktoru przed M1 i słusznie, ale MB-02
  wymaga rozdzielenia stanu sesji od zakończenia procesu — czyli pierwszego cięcia
  w tym pliku.
