# T-903 — macierz praw do brandingu, map, dzieł sztuki i referencji

Stan researchu: **31.08.2026**. Maszynowy rejestr: `data/legal/rights-matrix.json`.

> Ten dokument jest polityką kontroli ryzyka projektu, nie poradą prawną. Jeżeli status prawa jest niejasny, produkcyjny fallback jest neutralny i oryginalny.

## Decyzja dla vertical slice

Techniczny i neutral-realistic vertical slice **nie czeka na branding STIB/MIVB**. Do czasu udokumentowania uprawnienia:

- brak logo STIB/MIVB na pociągach, stacjach i materiałach marketingowych;
- brak kopii oficjalnych map, planów dzielnicowych, piktogramów i ekranów;
- brak kopiowanych dzieł sztuki;
- brak fontów korporacyjnych bez licencji;
- M7 zachowuje source-backed geometrię i parametry, ale używa neutralnego livery;
- stacje zachowują source-backed topologię, ale używają własnych materiałów i signage;
- źródłowe fotografie, filmy, screenshoty i rysunki są referencją, nie produkcyjnym assetem.

## Najważniejsza pułapka: Open Data ≠ ogólna licencja na markę

Warunki strony STIB/MIVB mówią, że treści strony — w tym fotografie, obrazy, logo i marki — są chronione, a użycie inne niż prywatne/osobiste wymaga uprzedniej zgody. Warunki dotyczące zdjęć i filmowania dodatkowo wskazują, że logo jest chronione, a dzieła sztuki w stacjach mogą mieć osobnych uprawnionych.

Jednocześnie warunki **STIB Open Data** zawierają własną Graphical and Ethical Charter. Dla produktów ponownie wykorzystujących Information regulują one m.in. kolory linii i sposób wyświetlania logo Producenta oraz przewidują wyświetlanie logo w określonych interfejsach/komunikacji związanej z reuse danych.

Projekt rozdziela te przypadki:

1. **Open Data compliance/attribution** — ewentualne użycie logo wyłącznie w zakresie i formie wynikającej z konkretnej licencji Open Data, po review warunków; logo nie jest wtedy assetem świata gry.
2. **Branding/livery/signage/marketing** — `permission_required`; nie wywodzimy zgody z licencji danych.

Dzięki temu klauzula Open Data nie zostaje przypadkiem użyta jako argument do naniesienia znaku STIB na model M7 albo do zrobienia „oficjalnie wyglądającej” kampanii gry.

## Macierz klas assetów

| Element | Zamierzone użycie | Status | Fallback |
|---|---|---|---|
| fakty i geometria z legalnych Open Data | własne dane/mesh/symulacja | `allowed_with_terms` | zachować attribution/provenance |
| nazwy stacji i numery linii jako fakty | navigation/timetable | `allowed_with_terms` | własna typografia |
| oficjalne kolory linii w UI powiązanym z Open Data | data-driven route UI | `licence_specific_review` | neutralna paleta poza compliance surface |
| logo STIB wymagane/dozwolone przez Open Data | attribution/compliance | `licence_specific_review` | tekstowa atrybucja do czasu review |
| logo STIB/MIVB jako livery/world/marketing | branding | `permission_required` | własna neutralna marka |
| realne livery M7 i oznaczenia eksploatacyjne | vehicle art | `permission_required` | neutralne livery przy zachowaniu source-backed wymiarów |
| font korporacyjny/oznakowania | signage/UI | `replace_with_original` | font własny albo licencjonowany |
| oficjalna mapa sieci / plan dzielnicowy jako obraz/tekstura | signage/map asset | `permission_required` | własna mapa generowana z danych |
| facts-only z tekstowych opisów wyjść | topologia proceduralna | `allowed_with_terms` | zapisać fakt + provenance, nie kopiować całego tekstu |
| oficjalne piktogramy/signage/ekrany | world assets | `permission_required` | własny neutralny system |
| dzieła sztuki | mesh/texture/reproduction | `permission_required` | neutralna ściana lub oryginalne dzieło projektu |
| fotografie/filmy/screenshoty STIB | research | `reference_only` | nie shipować |
| materiały CAF/producenta bez jasnej licencji | research | `reference_only` | odczytać tylko fakty/wymiary |
| permit drawings | facts/provenance | `reference_only` | nie bundlować jako asset bez licencji |
| własna zorganizowana sesja foto/video na sieci | production reference | `permission_required` | uzgodnić ze STIB przed sesją |

## Dzieła sztuki — pakiet A

Identyfikacja dzieła **nie oznacza prawa do reprodukcji**. Pole `rights_holder` pozostaje do potwierdzenia w umowie/estate/collecting society; fakt, że praca znajduje się w metrze, nie dowodzi że STIB posiada wszystkie prawa do reprodukcji w grze.

| Stacja | Dzieło | Twórca | Stan researchu | Produkcja |
|---|---|---|---|---|
| Gare de l'Ouest / Weststation | — | — | inventory pending | niczego nie zakładać; neutralny baseline |
| Beekkant | — | — | inventory pending | niczego nie zakładać; neutralny baseline |
| Étangs Noirs / Zwarte Vijvers | `Zwarte Vijvers` | Jan Burssens | zidentyfikowane | permission required |
| Comte de Flandre / Graaf van Vlaanderen | `16 x Icarus` | Paul Van Hoeydonck | zidentyfikowane | permission required |
| Sainte-Catherine / Sint-Katelijne | `Millefeuille` | Thierry Renard | zidentyfikowane | permission required |
| De Brouckère | `De Stad Beweegt In De Palm Van Mijn Hand` | Jan Vanriet | zidentyfikowane | permission required |
| De Brouckère | `Fietsersportretten` | An Van Gijsegem | instalacja czasowa — obecność 2026 do weryfikacji | excluded until cleared |
| Gare Centrale / Centraal Station | praca w emaliowanych panelach w korytarzu łączącym kolej–metro | Daniel Deltour | zidentyfikowane, przestrzeń wspólna | permission required + ustalić zakres STIB/SNCB/Beliris |
| Parc / Park | `Happy Metro To You` | Marc Mendelson | zidentyfikowane | permission required |
| Parc / Park | `La Ville` | Roger Dudant | zidentyfikowane | permission required |
| Parc / Park | `Mers et Océans` | Marie-Françoise Plissart | potwierdzone przez bieżący projekt STIB | permission required |
| Arts-Loi / Kunst-Wet | `Ortem` | Jean Rets | zidentyfikowane | permission required |
| Arts-Loi / Kunst-Wet | `Isjtar` | Gilbert Decock | zidentyfikowane | permission required |
| Maelbeek / Maalbeek | `Portraits - Portretten` | Benoît Van Innis | zidentyfikowane | permission required |
| Maelbeek / Maalbeek | `L'Olivier` | Benoît Van Innis | zidentyfikowane | permission required |
| Schuman | `Pourquoi Bruxelles Est-Elle Devenue La Capitale De L'Europe?` | Calogero Belluzzo / Philippe Van Parijs | inwentarz oznacza jako temporary/dynamic, obecność 2026 do weryfikacji | excluded until cleared |
| Merode | `Ensor : Vive La Sociale` | Roger Raveel | zidentyfikowane | permission required |
| Merode | `Carrelage Cinq` | Jean Glibert | zidentyfikowane | permission required |

### Źródła inwentarza dzieł

- Regionalny Inventaire du patrimoine mobilier: `https://collections.heritage.brussels/`
- Gare Centrale — Beliris: `https://www.beliris.be/projets/couloir-gare-centrale.html`
- Parc — aktualny projekt STIB: `https://www.stib-mivb.be/travel/works-and-projects/works-in-progress/station-parc-park-renovated-and-accessible`

Fotografie z inwentarza są oznaczone m.in. jako zdjęcia STIB/MIVB. **Nie są kopiowane do repo ani używane jako tekstury.**

## Mapy, plany i signage

### Dozwolony model pracy

1. pobierz legalny dataset;
2. zapisz source ID/licencję/hash/provenance;
3. wyprowadź facts-only/topologię/geometrię;
4. wygeneruj własną mapę, mesh i layout;
5. użyj własnego fontu i własnego neutralnego systemu signage;
6. zachowaj wymagane attribution osobno od świata gry.

### Zakazane skróty

- screenshot oficjalnej mapy jako tekstura;
- przerysowanie mapy 1:1 w celu zachowania jej ekspresji graficznej;
- crop fotografii stacji jako materiał ściany;
- „AI repaint” chronionego muralu mający zachować to samo dzieło;
- skopiowanie piktogramu/logo i zmiana jednego koloru;
- pobranie korporacyjnego fontu bez licencji.

## Fotografia i filmowanie na sieci

STIB publikuje osobny proces zdjęć/filmowania. Dla projektu nie zakładamy, że wyjątek dla spontanicznych zdjęć turystycznych obejmuje zorganizowaną sesję assetową, photogrammetry albo nagrania marketingowe.

Dla produkcyjnej sesji:

- najpierw opisać projekt i zakres STIB Public Relations;
- podać lokalizacje, datę, ekipę, sprzęt i sposób dystrybucji;
- nie wchodzić na torowisko, do tuneli, kabin ani pomieszczeń technicznych bez osobnej wyraźnej zgody i nadzoru;
- na miejscu kontrolować osoby trzecie, reklamy i dzieła sztuki w kadrze;
- każde zdjęcie produkcyjne otrzymuje provenance i `permission_ref`;
- plik źródłowy bez rozstrzygniętych praw nie trafia do produkcyjnego asset packa.

Kontakt wskazany przez STIB: `relationspubliques@stib-mivb.brussels`.

## Polityka contributorów

Każdy zewnętrzny asset lub materiał referencyjny proponowany do publikacji musi mieć co najmniej:

- `asset_id`;
- twórcę/źródło;
- source URL;
- licencję albo numer/reference pisemnej zgody;
- zamierzone użycie;
- informację `redistribution_allowed`;
- uwagi o ograniczeniach.

Twarde reguły:

1. Publiczna dostępność pliku **nie jest licencją**.
2. Repo GitHub bez jawnej kompatybilnej licencji = `reference_only`.
3. Nie commitujemy cudzych screenshotów, map, planów, zdjęć ani audio jako produkcyjnych assetów tylko dlatego, że są dostępne online.
4. Z dokumentu można odczytać fakt/wymiar z provenance; nie daje to automatycznie prawa do redystrybucji dokumentu.
5. Jeżeli status jest niejasny, używamy neutralnego oryginalnego zamiennika i zostawiamy unresolved rights item.
6. `permission_ref` nie może być „brak odpowiedzi”, ustną sugestią ani linkiem do publicznej strony. Ma wskazywać konkretną licencję albo zachowaną pisemną zgodę.

## Draft zapytania do STIB/MIVB

Poniższy tekst jest draftem do późniejszego wysłania; samo przygotowanie draftu nie tworzy zgody.

**Temat:** Demande d’autorisation / clarification des droits — simulateur indépendant du métro bruxellois

> Bonjour,
>
> Nous développons un simulateur indépendant du métro bruxellois fondé sur des données publiques et sur une reconstitution technique originale. Le projet n’est pas présenté comme un produit officiel de la STIB/MIVB et, en l’absence d’autorisation spécifique, utilise une identité visuelle neutre.
>
> Avant toute utilisation d’éléments de marque ou toute prise de vues organisée sur le réseau, nous souhaitons clarifier par écrit les droits et conditions applicables.
>
> Nous souhaiterions notamment savoir si, et sous quelles conditions, le projet pourrait utiliser :
>
> - le nom et le logo STIB/MIVB en dehors de la seule attribution imposée par les conditions Open Data ;
> - la livrée et certains marquages visuels des rames M7 ;
> - des éléments de signalétique et des pictogrammes présents dans les stations ;
> - des représentations d’œuvres d’art installées dans les stations, en sachant que les droits des artistes ou ayants droit devront le cas échéant être obtenus séparément ;
> - des photographies ou enregistrements réalisés par notre propre équipe dans les zones accessibles au public, uniquement comme références ou comme matériaux de production selon les autorisations accordées.
>
> Le projet peut fonctionner intégralement avec des éléments graphiques originaux et neutres. Nous ne souhaitons donc utiliser aucun élément protégé sans base écrite claire et nous pouvons vous transmettre des mockups comparant la version neutre à une éventuelle version sous licence.
>
> Pour une demande complète, nous pouvons également préciser les plateformes de distribution, le modèle de monétisation, la date de sortie envisagée, les territoires de diffusion, les stations concernées, la liste des œuvres et le plan d’une éventuelle session de prise de vues.
>
> Pourriez-vous nous indiquer le service compétent et les informations/documents nécessaires afin d’obtenir une réponse écrite sur ces différents usages ?
>
> Bien cordialement,
> [coordonnées du porteur du projet]

## Źródła prawne/polityczne zweryfikowane 31.08.2026

1. STIB/MIVB Legal terms — `https://www.stib-mivb.be/Footer/Legal-terms`
2. STIB/MIVB Open Data Terms — `https://data.stib-mivb.brussels/terms/terms-and-conditions.pdf`
3. STIB/MIVB Rules for photo/video — `https://www.stib-mivb.be/entreprises/presse-et-media/regles-pour-prise-de-vue-et-tournage-sur-le-reseau-stib`
4. STIB/MIVB General conditions for photo/video 2024 — `https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Professionals/Press-Media/conditions_generales_prise_de_vue_et_tournage_2024.pdf`

## Kryterium produkcyjne

Asset może przejść z neutralnego placeholdera do branded/final tylko wtedy, gdy `data/legal/rights-matrix.json` ma dla niego status pozwalający na zamierzone użycie i konkretne `licence_or_permission_ref`. Brak wpisu jest traktowany jak `excluded_until_cleared`, nie jak zgoda.
