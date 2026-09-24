# M7: otwory i szyby boczne — stan źródeł

24.09.2026. Odbiór wizualny bazowej skorupy: `build/train-qa/baseline-side.png`,
`baseline-front.png`, `baseline-iso.png` (lokalne, niepublikowane kadry).

## Co jest potwierdzone

- [STIB, komunikat z 13.07.2020](https://stib.prezly.com/le-nouveau-metro-m7-est-arrive-a-bruxelles)
  podaje 94 m długości, 2,70 m szerokości, 1,03 m wysokości podłogi,
  sześć członów, 18 podwójnych drzwi na stronę o świetle 1,60 m i dwie
  drzwi kabinowe. Te wartości są już w `data/vehicle/m7-spec.json`.
- [STIB, komunikat z 26.05.2021](https://stib.prezly.com/les-voyageurs-pourront-bientot-monter-dans-le-nouveau-metro-m7)
  potwierdza srebrny wygląd pudła i szersze drzwi. Oficjalne zdjęcia
  w obu komunikatach pokazują pojazd, lecz nie są zwymiarowanym rzutem bocznym.
- Generator `tools/blender/m7_shell.py` wycina obecnie tylko otwory drzwiowe.
  Ciemne prostokąty na renderze boku to otwory drzwi, nie okna.

## Czego nie potwierdzono

W sprawdzonych materiałach operatora i rejestrze projektu nie ma liczby okien
na człon, ich szerokości i wysokości, wysokości parapetu, odstępów od drzwi
i przegubów, grubości szkła ani przekroju uszczelki. Zdjęcie perspektywiczne
nie pozwala wyznaczyć tych miar z dokładnością potrzebną do wycięcia otworu.
Nie wolno przepisywać parametrów M6/Boa jako parametrów M7.

## Granica bezpiecznej implementacji

Otwory muszą być wycięte w istniejących sześciu siatkach pudła; oszklenie
powinno pozostać wewnątrz obrysu szerokości 2,70 m. Eksport musi zachować
11 węzłów (6 członów i 5 przegubów), istniejące krawędzie wszystkich drzwi,
rozpiętość 94 m oraz profil skrajni. Naklejka na nieprzeciętej ścianie
nie jest oszkleniem; panel wystający na zewnątrz łamie skrajnię.

## Następny krok

Pozyskać od STIB/CAF zwymiarowany rzut boczny M7 albo ortogonalne zdjęcie
jednego pełnego członu z miarą odniesienia w tej samej płaszczyźnie
(drzwi 1,60 m). Na tej podstawie wpisać wymiary okien do rejestru z osobnym
statusem źródła i niepewnością pomiaru. Dopiero potem wyciąć otwory w
istniejących siatkach, dodać oszklenie do tych samych węzłów i porównać
render boku/przodu oraz testy skrajni, drzwi i importu GLB. Same zdjęcia
operatora służą jako materiał referencyjny; nie są kopiowane do paczki gry.
