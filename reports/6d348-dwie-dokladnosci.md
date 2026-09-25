# 6.D348 · Wspólny rdzeń nazwy nie oznacza jednej dokładności

**Data:** 25.09.2026 · **Baza pomiaru:** `d5f50078fcbd8d9e5d03a2e8ed2bb1358e85b65c` (przed tym commitem).

## Wynik

W `tools/track/*.py` i `tools/blender/*.py` jest **368 wywołań** `round` z jawną całkowitą liczbą miejsc. Sito nazw pól wyjściowych (usunięcie przedrostków `min_`, `max_`, `median_`, `p05_`, `p95_`, `worst_`, `from_`, `to_` itd.) oraz powtórzonych wyrażeń wskazuje **147 wywołań z powtórzonym rdzeniem**. To liczba kandydatów, nie twierdzenie, że każde dwa pola opisują tę samą fizyczną wartość. Surowe sito pól daje **21 par** o różnej dokładności: po prześledzeniu argumentu `round` pięć dotyczy tej samej wielkości, a **16 odpada mimo wspólnego rdzenia**. Dwie dalsze rzeczywiste pary (`make_test_track.py:21,23` i `profile_scan.py:80,160`) są poza sitem pól, bo jedna strona jest elementem listy albo ma inny klucz.

**Siedem par** opisuje tę samą wielkość w dwóch dokładnościach; **wszystkie siedem** może trafić do jednego pliku wyjściowego. Obejmują 13 różnych wywołań `round`, bo jedno wywołanie `compact` uczestniczy w dwóch porównaniach. Poza klasą wspólnego pliku jest **zero** potwierdzonych par. Pary w `tunnel_width.py` wymagają opcji `--survey`; zwykły przebieg zapisuje tylko drugą stronę porównania.

| plik i wiersze na bazie | dokładności | wspólny zapis i powód zaliczenia |
|---|---|---|
| `tools/track/make_test_track.py:21,23` | 3 / 2 | Jeden syntetyczny JSON: ta sama zmienna `z` w punkcie osi i `stations[].depth_m`. |
| `tools/track/tunnel_width.py:146,214` | 2 / 3 | Jeden `--out` JSON z `survey.*.narrowest[].corridor_width_m` i `samples[].width_m`; dwa estymatory szerokości tunelu w planie. |
| `tools/track/tunnel_width.py:158,233` | 2 / 3 | Ten sam `--out` JSON z `survey.*.median_m` i `summary.median_m`. To para wskazana w 6.D338 §8; populacje są różne, mierzona wielkość to szerokość tunelu. |
| `tools/blender/clearance_profile.py:615,715` | 3 / 2 | `profile_vehicle.py` wpisuje `statistics.min_at.start_m` i `critical[].worst_start_m` do jednego raportu. Oba biorą `worst["start_m"]`. |
| `tools/blender/clearance_profile.py:617,718` | 3 / 2 | Ten sam raport, `statistics.min_at.chainage_m` i `critical[].chainage_m`, oba z `worst["chainage_m"]`. |
| `tools/blender/profile_scan.py:80,160` | 6 / 5 | Jeden raport `profile_vehicle.py`: `reduction_check[].reduced_m` i `profile[].clearance_m` dla tego samego rekordu pomiaru. |
| `tools/blender/profile_scan.py:151,160` | 4 / 5 | Jeden raport: `crosscheck.at_minimum.measured_clearance_m` / warianty oraz `profile[].clearance_m`; `profile_vehicle.py` podaje do pierwszego `worst["clearance_m"]`, a drugi serializuje ten sam rekord. |

## Granice klasyfikacji

Sito nazw **nie jest werdyktem**. `build_alignment.py:206,219` ma dwie mediany o kluczu `median_m`, ale pierwsza liczy odchyłkę osi od źródła, a druga promień krzywizny. Dziewięć par 4/1 miejsca wynikających z samego końcowego `_m` odrzuciłem. `profile_vehicle.py:341,398` używa kluczy z rdzeniem `length_m`, lecz jeden opisuje długość wycinka obwiedni, drugi całą oś. `profile_scan.py:82,152` zapisuje `delta_mm` z dwoma precyzjami, ale porównuje inne pary wielkości (redukcja–pełny pomiar oraz wzór–pomiar), więc to nie jest dwukrotny zapis tego samego błędu. `tunnel_manifest.py:94,123` używa lokalnej nazwy `worst` dla odchylenia LOD i osobno dla szwu; identyczna nazwa zmiennej nie wystarcza.

Odwrotną pułapkę pokazuje `make_test_track.py`: punkt osi jest elementem listy, nie polem słownika, więc sito samych kluczy JSON pominęłoby jego parę. `profile_scan.py:80,160` używa różnych nazw kluczy dla tego samego rekordu i wymaga prześledzenia przekazania argumentu. Sito 147 kandydatów powstało z 136 wywołań w 54 grupach powtarzających rdzeń pola oraz 11 dodatkowych wywołań o powtórzonym, znaczącym wyrażeniu; lokalne nazwy `v`, `c`, `worst` bez potwierdzonego znaczenia nie dodają kandydatów.

Różna dokładność nie dowodzi błędu. W JSON podsumowanie może celowo być krótsze od szczegółu, a dwie metody pomiaru mogą mieć różne błędy. Nie zmieniam żadnego `round`, formatu ani zapadki: pozycja 6.D348 miała **policzyć i nazwać**, a wybór dokładności jest osobną decyzją projektową.

## Weryfikacja przyrządu

Para kontrolna z 6.D338 §8 (`tunnel_width.py:158,233`) jest w klasie potwierdzonej: 2 i 3 miejsca, różne populacje szerokości, jeden plik przy `--survey`. Źródło zapisu sprawdzono po wywołaniach `survey`, `summarise` i `_write` w `tunnel_width.py` oraz po złożeniu i zapisaniu raportu w `profile_vehicle.py:443–444`. Pomiar obejmuje wyłącznie jawne `round(x, n)` z całkowitym literałem `n` w obu katalogach wskazanych w zadaniu. Nie obejmuje formatowania `f"{x:.2f}"`, bo to nie jest wywołanie `round`.
