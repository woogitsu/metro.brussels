# 6.D360 — pięć rozszerzeń poza bramką ścieżek raportów

**Data:** 25.09.2026 · **Gałąź:** `codex/6d360-path-report` · **Baza:** `0bcf169191ad01390ebd61a1cadd5c3cbb51d244`

## 1. Pomiar

Skan obejmuje 475 raportów
istniejących przed dodaniem niniejszego pliku. Rozszerzono wyłącznie na czas
pomiaru wzorzec bramki raportów o pięć rozszerzeń z bramki pól kolejki.
Wszystkie pozostałe warunki pozostawiono bez zmian: token musi stać w grawisach,
mieć ukośnik i nie zaczynać się od przedrostka ignorowanego przez `_paths_in`.
Niedostępność sprawdzono tym samym warunkiem istnienia pliku co bramka raportów.

| Rozszerzenie | Trafienia w grawisach | Brakujące pliki |
|---|---:|---:|
| glb | 0 | 0 |
| jsonl | 0 | 0 |
| log | 6 | 0 |
| png | 0 | 0 |
| zip | 2 | 2 |

Oba brakujące trafienia wskazują ten sam plik: data/gtfs/stib_gtfs.zip,
w raporcie zapisy-do-data.md, wiersze 109 i 203. Raport ten sam wyjaśnia,
że archiwum było gitignorowanym wejściem pomiaru i zostało po nim usunięte.
Zatem obecna różnica wzorców pozostawia dwa nieweryfikowane odsyłacze do
celowo nieobecnego archiwum; nie jest dowodem utraty pliku repozytorium.

## 2. Kontrola przyrządu i granica wniosku

Kontrola przyrządu: rozszerzenie md dało 929 trafień. Niezmieniona funkcja
`_pomiar_trafien` istniejącej bramki również dała 929. Liczono wystąpienia,
nie unikatowe ścieżki.

Historia wprowadzenia bramki raportów (commit 49a6236) uzasadnia kopię
listy rozszerzeń i wymóg żywego trafienia albo wyjątku dla każdego z nich,
lecz nie uzasadnia pominięcia tych pięciu. Raport 6.D352 identyfikuje różnicę
bez rozstrzygania jej powodu. W przejrzanych commitach i raportach nie znalazłem
zapisanego powodu rozbieżności. Ten pomiar nie zmienia żadnego wzorca ani
wyjątku; decyzja o objęciu archiwów bramką jest odrębna.
