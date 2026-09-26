# T-905 — audio ground truth, prawa i bezpieczny field recording

Stan researchu: **31.08.2026**.

Maszynowe elementy polityki:
- `data/audio/audio-manifest.schema.json` — schema provenance każdego assetu audio;
- `data/audio/placeholders.json` — lista neutralnych warstw do technicznego vertical slice.

> Ten dokument jest polityką produkcyjną projektu, nie poradą prawną. Brak jasnego prawa do pliku/dźwięku oznacza neutralny oryginalny placeholder, nie próbę znalezienia „podobnej” kopii.

## Decyzja dla vertical slice

T-400 **nie czeka na realistyczne audio STIB**. Do technicznego vertical slice używamy wyłącznie własnych, neutralnych, syntetycznych warstw:

- traction/drive;
- rolling noise;
- generic wheel/rail squeal;
- braking/regen feedback;
- HVAC/auxiliary;
- body rattle;
- neutral door motor;
- **oryginalny neutralny** door warning, nie kopia STIB;
- własny/licencjonowany TTS dla nazw stacji albo tymczasowo brak voice;
- syntetyczny station ambience bez zrozumiałych rozmów;
- generic escalator/lift/mechanical layer;
- design-only cab safety tone;
- algorithmic tunnel/station reverb.

Żaden z tych placeholderów nie może być opisywany jako autentyczne brzmienie M7/KCV/CBTC/STIB.

## Czego nie pozyskujemy

Bez osobnej, jasnej podstawy prawnej projekt **nie**:

- ripuje dźwięków z aplikacji STIB;
- wycina audio z oficjalnej strony, filmów STIB, social media lub YouTube;
- wycina zapowiedzi, gongi i dźwięki drzwi z filmów osób trzecich;
- nagrywa oficjalnych zapowiedzi z głośnika po to, by opublikować je jako production asset;
- pobiera bibliotek producenta/CAF bez licencji;
- przedstawia wymyślone audio urządzeń KCV/CBTC jako rekonstrukcję rzeczywistego systemu.

Aktualne warunki korzystania z aplikacji STIB ograniczają jej użycie do osobistego i zabraniają kopiowania/extract/re-use Content bez odpowiedniej zgody. Niezależnie od tego warunki strony chronią publikowane treści, a proces zdjęć/filmowania STIB wymaga wcześniejszego ustalenia warunków dla zorganizowanej produkcji.

## Kategorie audio

### 1. Napęd i ruch M7

Potrzebne warstwy domenowe:
- `traction.drive` zależne od speed/load/traction command;
- `rolling.base` zależne głównie od prędkości i środowiska;
- `wheel_rail.squeal` zależne od łuku/scenariusza;
- `braking.regen` zależne od ujemnej pracy/command;
- `aux.hvac`;
- `body.rattle`.

Ground truth techniczny M7 (np. typ napędu i regenerative braking) może sterować **logiką** warstw. Nie daje to automatycznie prawa do konkretnego nagrania M7.

### 2. Drzwi

Rozdzielamy:
- warning/chime;
- unlock/release event;
- motor open/close;
- seal/impact;
- ewentualne single cab-side door events.

Do prototypu powstaje własny neutralny warning. Nie transkrybujemy melodii/gongu STIB nutka-po-nutce i nie tworzymy „prawie tego samego” jako obejścia.

### 3. Zapowiedzi

Nazwy stacji są faktami, ale konkretne:
- nagranie;
- głos;
- realizacja;
- jingle/melodia;
- efekty i aranżacja

mogą być osobno chronione.

Fallback produkcyjny: własne teksty operacyjne + własny lektor albo TTS z licencją pozwalającą na dystrybucję gry. Nie nazywać go „oficjalnym głosem STIB”.

### 4. Ambience stacji

Warstwy:
- wentylacja;
- pogłos;
- schody ruchome/windy;
- tłum jako nierozpoznawalne tło;
- odległy ruch uliczny przy wejściach.

Nagranie zawierające zrozumiałą rozmowę osoby trzeciej ma `contains_voice: true` i domyślnie status `rejected` lub trafia do osobnego legal/privacy review. Nie budujemy crowd bed z przypadkowo podsłuchanych rozmów.

### 5. Kabina/safety/signalling

Dźwięki KCV/CBTC/ATS, których nie znamy ze źródła, są `design_audio`. Ich funkcje mogą wynikać z R-003, ale brzmienie nie może być „odtworzone” na podstawie cudzych filmów bez praw ani przedstawione jako vendor-spec.

## Audio manifest — twardy gate

Każdy realny plik produkcyjny otrzymuje sidecar zgodny z `data/audio/audio-manifest.schema.json`.

Wymagane minimum:
- `asset_id`;
- `source_type`;
- `creator`;
- `rights_status`;
- `processing_chain`;
- `contains_voice`;
- `contains_stib_brand_audio`;
- `redistribution_allowed`;
- `notes`.

Dla własnego nagrania zapisujemy dodatkowo:
- `recorded_by`;
- `recorded_at`;
- `location` + access class;
- SHA-256 źródła;
- `permission_ref`, jeśli nagranie było zorganizowane na sieci STIB.

Dla biblioteki zewnętrznej wymagamy pola `license`.

`rights_status: cleared` bez licencji albo konkretnego `permission_ref` jest błędem polityki.

## Surowe nagrania poza Git

Raw field recordings mogą być duże, zawierać dane wymagające review albo wersje, których nie wolno redystrybuować. Dlatego:

- `data/audio/raw/` — gitignored;
- `assets/audio/raw/` — gitignored;
- `recordings/` — gitignored;
- repo przechowuje tylko manifest/hash i dopuszczone finalne assety w później ustalonej lokalizacji.

Nie używamy Git LFS jako sposobu na obejście niejasnych praw: LFS rozwiązuje rozmiar, nie licencję.

## Plan field recording

Field recording uruchamiamy dopiero po pisemnym wyjaśnieniu warunków ze STIB dla zorganizowanej sesji przeznaczonej do gry.

### Etap A — wniosek

Wysyłamy zakres:
- nazwa projektu i brak sugerowania oficjalnego partnerstwa;
- komercyjny/niekomercyjny model dystrybucji;
- lokalizacje i typy potrzebnych dźwięków;
- liczebność ekipy;
- data/godzina z preferencją poza szczytem;
- sprzęt;
- czy nagrania mają wejść do gry czy tylko służyć jako reference;
- sposób publikacji/marketingu;
- potwierdzenie, że nie wchodzimy w strefy techniczne bez osobnej zgody.

### Etap B — bezpieczna sesja

Dozwolone wyłącznie w zakresie zgody:
1. przestrzenie dostępne pasażerom albo inne miejsca jawnie wskazane przez STIB;
2. brak mikrofonów/statywów na torowisku i w tunelu;
3. brak wejścia do kabiny, pomieszczeń technicznych, zajezdni i stref staff-only bez osobnej zgody/nadzoru;
4. nie blokować ruchu i nie nagrywać w sposób stwarzający ryzyko;
5. każde ujęcie/take dostaje numer i metadata od razu;
6. oznaczyć takes z rozpoznawalną mową/reklamą/muzyką/dziełem chronionym;
7. nic z kategorią `permission_required/rejected` nie przechodzi do builda.

### Etap C — ingest

Dla każdego take:
- hash raw file;
- data/godzina;
- stacja/pojazd, jeżeli dotyczy;
- pozycja typu `public_passenger_area`/`controlled_with_permission`;
- recorder/microphone/sample rate;
- permission reference;
- flagi voice/brand audio;
- notes o zdarzeniach przypadkowych.

Raw pozostaje poza Git.

## Minimalna take list po uzyskaniu zgody

Priorytetem byłyby warstwy, które da się nagrać bez ingerencji w infrastrukturę:

1. ambience na peronie bez zrozumiałej mowy;
2. przejazd pociągu z bezpiecznego miejsca pasażera;
3. wnętrze podczas jazdy — rolling/body/traction reference;
4. drzwi jako mechanika, **z wyłączeniem charakterystycznego warningu**, jeśli prawa do niego nie są osobno wyjaśnione;
5. escalator/lift ambience z przestrzeni publicznej;
6. wejście/street ambience.

Nie planujemy capture urządzeń bezpieczeństwa, wnętrza szaf, torowiska, tuneli technicznych ani kabiny bez wyraźnie rozszerzonej zgody.

## Techniczny interfejs późniejszej implementacji

Audio powinno konsumować eventy/stany `src/Sim`, a nie produkować logikę domenową. Przykładowe źródła parametrów:

- `speed_mps` → rolling/traction pitch/load;
- traction/brake command + real work → drive/braking layers;
- door state events → release/open/close/warning;
- station arrival/departure event → announcement trigger;
- environment tag tunnel/station/surface → reverb/ambience;
- signalling intervention event → **design_audio** safety cue.

Brak pliku audio nie może zmienić physics/safety state.

## Draft zapytania do STIB Public Relations

**Temat:** Demande de clarification / autorisation pour des enregistrements sonores destinés à un simulateur indépendant

> Bonjour,
>
> Nous développons un simulateur indépendant du métro bruxellois. Le projet utilise actuellement uniquement des sons originaux et synthétiques et n’est pas présenté comme un produit officiel de la STIB/MIVB.
>
> Avant d’organiser toute session d’enregistrement sonore sur le réseau, nous souhaitons obtenir une confirmation écrite des conditions applicables à une prise de son destinée à un jeu/simulateur.
>
> Nous souhaiterions, si cela est autorisé, enregistrer depuis des espaces accessibles au public des ambiances de station, le passage et le roulement des rames, certains bruits mécaniques génériques (portes, escalators, ventilation) et l’ambiance intérieure pendant un trajet. Nous ne souhaitons pas accéder aux voies, tunnels techniques, locaux de service, cabines ou dépôts sans autorisation spécifique et accompagnement de la STIB.
>
> Nous souhaitons également savoir si certains sons caractéristiques — notamment les avertissements de portes, annonces enregistrées, jingles ou sons d’équipements — font l’objet de restrictions ou de droits spécifiques qui empêcheraient leur enregistrement et leur intégration dans le produit. En l’absence d’autorisation explicite, ces éléments resteront remplacés par nos propres sons neutres.
>
> Nous pouvons vous communiquer à l’avance la liste des stations, la date, les horaires, le nombre de personnes, le matériel utilisé, la méthode de prise de son ainsi que les plateformes et le modèle de distribution du projet.
>
> Pourriez-vous nous indiquer la procédure à suivre et les éventuelles conditions particulières pour ce type d’enregistrement sonore ?
>
> Bien cordialement,
> [coordonnées du porteur du projet]

Kontakt publikowany przez STIB dla zdjęć/filmowania: `relationspubliques@stib-mivb.brussels`. Nie zakładamy automatycznie, że opublikowany wyjątek dla zwykłych zdjęć turystycznych obejmuje komercyjny field recording audio — właśnie dlatego pytamy pisemnie.

## Źródła zweryfikowane 31.08.2026

1. STIB/MIVB Legal terms — `https://www.stib-mivb.be/Footer/Legal-terms`
2. STIB/MIVB mobile app terms (22.10.2025) — `https://www.stib-mivb.be/mobile-terms-and-conditions`
3. STIB/MIVB rules for photo/video — `https://www.stib-mivb.be/entreprises/presse-et-media/regles-pour-prise-de-vue-et-tournage-sur-le-reseau-stib`
4. STIB/MIVB General conditions for photo/video 2024 — `https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Professionals/Press-Media/conditions_generales_prise_de_vue_et_tournage_2024.pdf`

## Skończone technicznie przed realistycznym audio

T-400 może użyć `data/audio/placeholders.json` bez żadnego realnego nagrania STIB. Realistyczny pass może zacząć się dopiero, gdy konkretne pliki mają provenance i `rights_status: cleared` zgodnie ze schema.

## Neutral take-list

The auditable category list is in data/audio/take-list.json. It defines synthetic defaults, the limited conditions for original ambience recordings, required metadata, and rejection rules. It contains no audio assets.

