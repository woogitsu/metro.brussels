# T-902 — art direction technicznego i finalnego Metro BXL

Stan baseline: **31.08.2026**. Konfiguracja maszynowa: `data/design/visual-style.json`.

## Decyzja architektoniczna

Pipeline wizualny ma trzy warstwy i nigdy nie wymaga przepisywania geometrii tylko dlatego, że prawa do brandingu są nierozstrzygnięte:

1. `technical` — geometria, skala, skrajnia, kolizje, diagnostyka i visual regression;
2. `neutral_realistic` — fizycznie wiarygodne materiały i własne signage bez chronionej identyfikacji STIB;
3. `licensed_stib_optional` — opcjonalny branded pass dopiero po konkretnym rights gate z T-903.

Domyślny kierunek do czasu decyzji finalnych to **semi-realistic / physically plausible**. Realizm ma wynikać z prawdziwej geometrii, topologii, fizyki, światła i zachowania ruchu, a nie z kopiowania cudzych tekstur, map i dekoracji.

## Warstwa `technical`

Cel: natychmiast wykrywać błędy funkcjonalne.

- 1 jednostka = 1 m;
- materiały proceduralne bez zewnętrznych bitmap jako wymóg domyślny;
- wysoki kontrast funkcjonalny pomiędzy klasami powierzchni;
- brak logotypów, reklam, map, artworków i fontów STIB;
- stałe oświetlenie i kamery do visual regression;
- brak auto-exposure i efektów temporalnych utrudniających porównania;
- czytelność normalnych, szczelin i skrajni ważniejsza niż „ładny” render.

Ta warstwa jest wystarczająca dla T-210/T-220/T-211/T-212/T-400.

## Warstwa `neutral_realistic`

Cel: pierwsza wersja wyglądająca jak wiarygodna infrastruktura metra, ale działająca bez praw do marki.

Materiały bazowe:
- concrete clean/aged;
- painted concrete;
- generic ceramic tile small/large;
- stone;
- brushed metal;
- painted metal;
- glass;
- rubber;
- asphalt;
- rail steel;
- generic safety strip.

Zasady:
- rzeczywista skala materiału w metrach;
- materiał może być proceduralny albo pochodzić z jawnie licencjonowanej biblioteki;
- żadnego cropowania zdjęcia stacji jako tekstury;
- żadnego odwzorowywania charakterystycznego muralu/patternu jako „generic texture”;
- zabrudzenie i zużycie są osobnymi parametrami projektowymi, nie rekonstrukcją konkretnej stacji bez danych;
- rail/track material nie rozstrzyga geometrii toru; R-005 nadal kontroluje to, co wiemy o infrastrukturze.

## `licensed_stib_optional`

Ta warstwa istnieje tylko jako późniejszy overlay/pakiet assetów. Nie może być wymagana przez core sceny.

Gate: `data/legal/rights-matrix.json` musi dla konkretnego elementu zawierać prawo do konkretnego użycia i `permission_ref`/licencję. Brak wpisu lub `permission_required` oznacza zachowanie neutralnego fallbacku.

Dotyczy szczególnie:
- logo i oznaczeń STIB/MIVB;
- realnego livery M7;
- oficjalnego signage/piktogramów;
- oficjalnych map;
- dzieł sztuki;
- fontów i charakterystycznych patternów.

## Stabilny baseline renderu

`data/design/visual-style.json` definiuje testowe środowisko Blendera:
- 960×576;
- stałe tło/world strength;
- preferowany Eevee Next z fallbackiem Eevee;
- fixed camera lens;
- brak auto-exposure;
- deterministyczny seed;
- brak temporal jitter.

To nie jest finalne oświetlenie gry. Służy do porównywalnych screenshotów narzędzi. Baseline Godot powstanie dopiero po T-400, na rzeczywistym rendererze i sprzęcie self-hosted.

## Neutral material test scene

`tools/blender/material_test_scene.py` generuje od zera scenę zawierającą wszystkie presetowe materiały z `visual-style.json`.

Scena:
- nie używa zdjęć ani zewnętrznych tekstur;
- generuje własne próbki geometrii;
- nakłada materiały z parametrów JSON;
- ustawia stałe światło i kamery;
- eksportuje GLB;
- renderuje `iso`, `side` i `close` do `renders/`;
- raportuje liczbę materiałów, obiektów, bounding box i engine.

Artefakty nie trafiają do Git. Workflow `material-style-smoke.yml` przechowuje je jako artefakty CI do rzeczywistego obejrzenia.

T-902 **nie może zostać zamknięte**, dopóki ten job nie wykona się na runnerze self-hosted i trzy PNG nie zostaną ręcznie ocenione.

## Źródła zewnętrznych materiałów

Preferencja: własne materiały proceduralne. Jeżeli później potrzebne są bitmapy/HDRI, baseline dopuszcza tylko konkretne assety z zapisanym provenance.

### Poly Haven
- assets: CC0 według oficjalnej strony licencji;
- dozwolone jako źródło tekstur/HDRI/modeli po zapisaniu asset ID/URL/hash;
- logo, strona i API mają odrębne warunki — CC0 assetów nie przenosi się na markę/serwis;
- live API nie jest wymagane w runtime.

Źródło: `https://polyhaven.com/license`

### ambientCG
- materiały są publikowane jako CC0;
- zapisujemy dokładny asset ID/download/hash;
- nie zakładamy, że branding strony dziedziczy licencję assetów.

Źródło: `https://ambientcg.com/`

### Blender Institute texture archive
- archiwalne tekstury oznaczone jako CC0;
- każdy użyty plik nadal dostaje provenance/hash.

Źródło: `https://download.blender.org/archive/textures/`

## Metadata assetu

Każdy zewnętrzny materiał, który kiedykolwiek wejdzie do produkcji, musi mieć:
- `asset_id`;
- `source_type`;
- `source_url`;
- `license`;
- `source_hash`;
- `processing`;
- `redistribution_allowed`.

Brak któregoś pola = asset nie jest gotowy do produkcji.

## Oświetlenie

Baseline techniczny:
- stała ekspozycja;
- proste neutralne key/fill;
- brak agresywnego bloom;
- brak chromatic aberration;
- brak efektów, które zmieniają wynik między identycznymi renderami;
- osobna logika świata i przyszłej kabiny;
- sygnały/HUD muszą pozostać czytelne bez polegania wyłącznie na kolorze.

Neutral-realistic może mieć lokalną temperaturę/charakter światła zależną od stacji dopiero, gdy mamy źródła lub świadomy design. Nie kopiujemy konkretnej oprawy 1:1 tylko dlatego, że widać ją na fotografii referencyjnej.

## UI/HUD

Techniczny HUD T-400 jest oryginalnym interfejsem diagnostycznym. Nie odtwarza 1:1:
- aplikacji STIB;
- monitorów informacji pasażerskiej;
- paneli kabinowych;
- layoutu map i signage.

Statusy safety mają mieć redundancję: tekst/ikona/kształt, nie sam kolor.

## Performance: najpierw pomiar

Nie wpisujemy dziś arbitralnych limitów polygonów, draw calls, świateł, rozmiarów tekstur ani LOD distances.

`visual-style.json` zostawia te budżety jako `null`, dopóki T-400/T-012 nie zmierzy na docelowym runnerze self-hosted, na jego GPU:
- FPS/frame time;
- sim tick time osobno;
- draw calls;
- triangles;
- VRAM/RAM;
- koszt świateł/cieni.

Dopiero z tego powstanie budżet produkcyjny.

## Decyzje użytkownika do finalnego art pass

Nie blokują technicznego baseline, ale przed finalną warstwą produkcyjną trzeba ustalić:
1. docelowy stopień fotorealizmu;
2. stałą czy dynamiczną porę dnia;
3. czy `licensed_stib_optional` jest realnym celem produktu;
4. target hardware / rozdzielczość / FPS;
5. poziom widocznego zużycia i brudu.

Do tego czasu kod i assety mają pozostać kompatybilne z neutralnym fallbackiem.

## Weryfikacja po odblokowaniu runnera

Poprzednia wersja tego rozdziału — i dwa miejsca wyżej — mówiła „na self-hosted
WSL2"; etykietę `wsl2` zdjęto 02.08.2026, bo maszyna, która ją nosiła, została
wyłączona i joby zawisły w `queued`. Dlatego jest tu przepisana, a nie dopisana
obok: runner jest gołe `self-hosted`, bez dodatkowych etykiet (`CLAUDE.md` §9).

Na runnerze self-hosted:

```bash
python3 tools/tests/test_all.py
blender --background --python tools/blender/material_test_scene.py -- \
  --config data/design/visual-style.json \
  --out build/material-style.glb \
  --renders renders/material-style
```

Następnie rzeczywiście obejrzeć:
- `renders/material-style_iso.png` — czy materiały są wyraźnie rozróżnialne i nie ma pustej sceny;
- `renders/material-style_side.png` — czy skala próbek i oświetlenie są spójne;
- `renders/material-style_close.png` — czy metallic/roughness/glass zachowują się plausibly i bez clippingu/overexposure.

Automatyczne przejście procesu nie zastępuje tych oględzin.
