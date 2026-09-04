# Blokady prawne — twarde

To nie jest porada prawna. Agent nie umieszcza poniższych elementów bez pisemnej zgody potwierdzonej przez człowieka albo bez jednoznacznej licencji obejmującej **konkretne zamierzone użycie**.

Szczegółowa macierz klas assetów, dzieł sztuki i fallbacków: `docs/18-rights-matrix.md` oraz `data/legal/rights-matrix.json`.

| Element | Powód | Status |
|---|---|---|
| Płaskorzeźby Tintina, Stockel | prawa autorskie | BRAK |
| Dzieła sztuki na stacjach | prawa autorskie twórcy/estate/collecting society; zakres umów instalacyjnych do weryfikacji | BRAK |
| Logo i znaki STIB/MIVB jako livery/world/marketing | znak towarowy / warunki STIB | BRAK |
| Krój pisma oznakowania STIB | licencja fontu | BRAK |
| Pełna identyfikacja wizualna STIB | prawa/znaki/design | BRAK |
| Oficjalne mapy i plany jako obrazy/tekstury | chroniona ekspresja / warunki strony | BRAK |

## Dozwolone roboczo

- nazwy stacji jako fakty topograficzne, zawsze dwujęzycznie tam, gdzie występują dwie nazwy
- przebieg linii, kolejność stacji, długości i inne fakty z legalnych źródeł zgodnie z ich warunkami
- własna proceduralna architektura wyprowadzona z facts-only/topologii
- własne oznakowanie, czytelnie odmienne od STIB
- neutralne livery i materiały własnego projektu
- numery i kolory linii w zakresie uzasadnionym danymi/licencją; szczegóły Open Data poniżej

## Otwarte dane STIB/MIVB

Warunki Open Data STIB dopuszczają ponowne wykorzystanie informacji przy spełnieniu warunków licencji. Ich Graphical and Ethical Charter reguluje również nazwy Producenta, kolory linii i sposób wyświetlania logo w produktach ponownie wykorzystujących Information.

**To nie jest w projekcie traktowane jako ogólna licencja na markę.** Rozdzielamy:

1. `open_data_compliance` — ewentualne wymagane/dozwolone użycie nazwy, kolorów lub niezmodyfikowanego logo wyłącznie w zakresie licencji danych i w interfejsie/komunikacji bezpośrednio związanej z reuse;
2. `brand_world_marketing` — logo na M7, stacjach, signage, splash screenach, store assets i marketingu; domyślnie `permission_required`.

Do czasu review konkretnego obowiązku licencyjnego preferujemy tekstową atrybucję w neutralnej warstwie prawnej projektu i nie wprowadzamy logo do świata gry.

## Materiały referencyjne

- publiczna dostępność pliku nie jest licencją;
- zdjęcia, screenshoty, filmy, mapy i plany STIB są `reference_only`, jeśli brak osobnej licencji/zgody;
- permit drawings i materiały producenta mogą służyć do odczytania faktów/wymiarów z provenance, ale nie są automatycznie redistributable;
- repo GitHub bez jawnej kompatybilnej licencji = `reference_only`;
- dzieło sztuki nie staje się wolne do reprodukcji dlatego, że znajduje się w przestrzeni publicznej lub na oficjalnym zdjęciu.

## Własne zdjęcia i nagrania na sieci

Zorganizowana sesja zdjęciowa/nagraniowa do produkcji gry jest traktowana jako wymagająca wcześniejszego wyjaśnienia warunków ze STIB Public Relations. Nie zakładamy, że wyjątki dla spontanicznych zdjęć turystycznych obejmują photogrammetry, sesję assetową lub materiały marketingowe.

Kontakt publikowany przez STIB: `relationspubliques@stib-mivb.brussels`.

## Reguła merge dla assetów

Każdy zewnętrzny asset produkcyjny ma `source/licence/permission_ref`. Brak udokumentowanego prawa do zamierzonego użycia = neutralny oryginalny fallback albo wykluczenie assetu. Brak odpowiedzi uprawnionego **nie jest zgodą**.
