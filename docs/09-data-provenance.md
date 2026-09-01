# Data provenance i zmiany upstream

Ten dokument definiuje wspólny format audytu wejściowych danych STIB/MIVB, Brussels Mobility/Paradigm, Belgian Mobility i OSM.

## Cel

Każdy downloader lub generator, który wprowadza zewnętrzne dane do pipeline'u, zapisuje osobny manifest provenance. Aktualizacja upstream nie może po cichu zmienić wersjonowanego artefaktu: najpierw porównujemy manifesty, potem świadomie akceptujemy zmianę.

Implementacja współdzielona:
- `tools/data/provenance.py` — hashe, sanitizacja, walidacja formatu, pobieranie z redirectami, manifest i diff;
- `tools/data/snapshot_source.py` — CLI do snapshotu oraz porównania dwóch manifestów;
- `data/schema/source-manifest.schema.json` — maszynowy kontrakt formatu.

## Minimalny manifest

Manifest zawiera co najmniej:
- `source_id` zgodne z `data/network/sources.json`;
- `requested_url` i finalny `final_url` po redirectach, oba po sanitizacji;
- `retrieved_at` w UTC;
- opcjonalną deklarowaną wersję/daty datasetu;
- `etag` i `last_modified`, jeśli istnieją;
- SHA-256 surowych bajtów oraz `size_bytes`;
- MIME i format;
- CRS, jeśli dotyczy;
- `parser_version`;
- opcjonalny SHA-256 canonical artefact;
- listę transformacji i wejściowych source IDs;
- `source_metadata` i `stats` do audytowalnego diffu;
- dla zapytań OSM jedynie `query_sha256`, nie pełny query string w manifeście.

`retrieved_at`, ETag i Last-Modified są metadanymi obserwacji. Nie są częścią hasha treści i nie mogą zmieniać byte-deterministycznego canonical outputu.

## Bezpieczeństwo sekretów

Sekrety nie trafiają do manifestów ani logów. `sanitize_url()` redaguje typowe parametry query (`token`, `api_key`, `access_token`, `signature` itd.). Credentials w URL userinfo są błędem. Nagłówki `Authorization`, `Proxy-Authorization` i API-key są odrzucane przez `sanitize_headers()` zamiast zapisywane.

## Walidacja pobranego formatu

Downloader nie ufa samemu kodowi HTTP. `validate_payload()` odrzuca HTML/login page oraz sprawdza podstawową strukturę lub magic bytes:
- ZIP — `PK...`;
- JSON — poprawny parser JSON;
- XML/NeTEx — poprawny XML;
- GeoPackage/SQLite — `SQLite format 3`;
- LAS/LAZ — `LASF`;
- tekst/CSV — UTF-8;
- PBF — minimalny rozmiar sanity-check.

Parser konkretnego datasetu może i powinien dołożyć bardziej szczegółową walidację semantyczną.

## CLI snapshot

Przykład kontrolowany przez registry:

```bash
python3 tools/data/snapshot_source.py snapshot stib_gtfs \
  --format zip \
  --output build/provenance/stib_gtfs.json
```

Jeżeli registry nie zawiera bezpośredniego download URL albo endpoint wymaga ręcznie uzyskanego adresu, można użyć `--url`. Tokenów nie zapisujemy w argumentach, manifeście ani repo.

Dla OSM można podać `--query`; manifest zachowa wyłącznie SHA-256 zapytania.

## Diff upstream

```bash
python3 tools/data/snapshot_source.py diff old.json new.json
python3 tools/data/snapshot_source.py diff old.json new.json --fail-on-change
```

Raport zwraca `changed`/`unchanged` oraz jawne różnice dla:
- SHA-256 wejścia;
- finalnego URL/redirectu;
- `source_id` i deklarowanej wersji;
- wersji parsera i SHA canonical artefact;
- `source_metadata`, gdzie można utrzymywać m.in. licencję i datę weryfikacji;
- `stats`, gdzie parsery zapisują liczby rekordów, feature count, bbox albo statystyki GTFS;
- `query_sha256` dla OSM.

Zmiana ETag bez zmiany bajtów nie jest zmianą treści. Zmiana jednego bajtu daje inny `content_sha256` i `source_changed: true`.

## Statystyki parserów

Wspólna warstwa nie interpretuje domeny. Downloader/parser przekazuje do `stats` dane specyficzne dla formatu, np.:

```json
{
  "record_count": 12345,
  "bbox": [4.3, 50.7, 4.5, 50.9],
  "gtfs": {
    "feed_start_date": "20260901",
    "feed_end_date": "20261231",
    "routes": 4,
    "trips": 1234,
    "stops": 59
  }
}
```

Dzięki temu `diff_manifests()` pokaże zmianę statystyk bez wprowadzania zależności GTFS/GIS do warstwy bazowej.

## Integracja T-110 / T-111

T-110 i T-111 powinny:
1. pobrać źródło przez wspólną walidację albo równoważny transport używający tych samych zasad;
2. policzyć SHA surowego inputu przed transformacją;
3. wyprodukować canonical output deterministycznie;
4. policzyć SHA canonical output;
5. zapisać parser version, transformations, input sources i stats;
6. przed nadpisaniem wersjonowanego artefaktu porównać nowy manifest z poprzednim i pokazać diff.

Automatyczne zaakceptowanie zmiany upstream pozostaje poza zakresem.
