# Konwencje

- 1 jednostka Blendera/Godota = 1 metr.
- Prędkość w kodzie: m/s; masa: kg; czas: s; pochylenie: %.
- Dane geograficzne: EPSG:31370 (Lambert 72), origin sceny przy Gare de l'Ouest.
- Blender: Z w górę. Godot: Y w górę, -Z do przodu.
- `data/` = dane wejściowe; `tools/` = narzędzia; `src/` = kod; `build/` i `renders/` = generowane, nie commitować.
- Python: `snake_case`; C#: `PascalCase` publiczne, `_camelCase` prywatne.
- Nazwy stacji dwujęzyczne FR|NL tam, gdzie funkcjonują dwie nazwy.
- Jedno zadanie = jedna gałąź = jeden logiczny commit.

## Nagłówek raportu w `reports/`

Nagłówkiem jest tekst **przed pierwszym śródtytułem `## `**. Musi nieść datę pomiaru
i commit, na którym mierzono; pilnuje tego `tools/tests/test_report_hygiene.py`.
Zalecany kształt wiersza pola:

```
**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`
```

**Ten kształt jest zaleceniem dla nowych raportów, nie wymogiem — i to jest wynik
pomiaru, nie gustu.** Zmierzone 07.09.2026 na
`f684e40a3af52272f9cd1d32d241e9bf3abf644d`: 140 raportów, 135 z wierszem pola
niosącym SHA, **90 w kształcie wyżej i 45 w piętnastu innych**, wszystkich
czytelnych. Wszystkie 45 dodano **05.09.2026 albo wcześniej**; od 06.09.2026 nie
doszedł ani jeden — 83 raporty pod rząd w kształcie wyżej. Bramka na kształt
zapalałaby się więc na 50 poprawnych raportach, żeby chronić przed rozjazdem, który
w 83 kolejnych plikach nie wystąpił ani raz. Pomiar: `reports/ksztalt-naglowka-raportu.md`.

Pilnowany jest za to sam ten zapis: bramka porównuje przykład wyżej z kształtem
**większości raportów** i zapala się, gdy jedno przestaje opisywać drugie.

**Pomiaru z datą się nie przelicza.** Data i commit w nagłówku raportu mówią, na czym
liczby powstały, więc zostają takie, jakie były w dniu pomiaru — nieaktualna liczba
w datowanym raporcie dostaje **adnotację**, a nie podmianę. Zmienić może się najwyżej
układ nagłówka. Ta reguła stała dotąd wyłącznie w cytowaniach: 11 raportów w `reports/`
i `tools/tests/test_bin_path_framework.py` powoływało się na ten plik jako jej źródło,
a plik jej nie zawierał.
