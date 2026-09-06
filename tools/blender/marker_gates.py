#!/usr/bin/env python3
"""Wybór okna i bramki luzu dla znaczników — czysty Python, bez `bpy`.

**Dlaczego osobny moduł.** Do 06.09.2026 te trzy funkcje siedziały w
`detail_markers.py`, tuż obok `import bpy`. Nie wołały Blendera ani razu, ale
mieszkały w module, którego zestaw testów nie potrafi zaimportować — więc **żaden
test nie mógł ich dotknąć**, a przegląd mutacyjny liczył je jako „nieosiągalne":
**wszystkie 9 z 9** mutacji tego pliku. Dwie z ich własnych docstringów mówią wprost,
że powstały jako reakcja na ocalałą mutację z 03.09.2026 — i ta mutacja ocalała
dalej, bo funkcja przeniosła się z `main()` na poziom modułu, ale nie wyszła spod
`import bpy`.

To ta sama operacja, którą przeszły `m7_shell.py`, `tunnel_sweep.py`,
`profile_vehicle.py`, `glb_roundtrip.py` i `place_vehicle.py`.

Wszystkie trzy funkcje **odmawiają zamiast zgadywać**: puste okno kilometrażu,
nieznana strona osi i ujemny luz kończą się błędem, nie cichą wartością domyślną.
"""


def select_marks(marks, from_m, to_m):
    """Znaczniki mieszczące się w oknie kilometrażu. Puste okno jest błędem, nie zerem.

    **Po co osobna funkcja.** Wybór okna siedział w `main()` razem z `bpy`, więc nie
    dawał się dotknąć testem — a decyduje o tym, czy render kontrolny w ogóle coś
    pokaże. Bez okna kadr obejmuje 5,4 km i każdy słupek ma 0,03 piksela; scena
    wychodzi pusta, mimo że geometria jest. Zmierzone, nie przewidziane: pierwszy
    przebieg dał dokładnie taki pusty render.

    Puste okno kończy się `SystemExit`, a nie pustą listą, bo skrypt bez ani jednego
    znacznika wyprodukowałby pustą scenę i zapisał ją jako poprawny GLB.
    """
    low = from_m if from_m is not None else float("-inf")
    high = to_m if to_m is not None else float("inf")
    if low > high:
        raise SystemExit(f"BŁĄD: okno {low}–{high} m jest puste")
    selected = [m for m in marks if low <= m["chainage_m"] <= high]
    if not selected:
        raise SystemExit(f"BŁĄD: w oknie {low}–{high} m nie ma ani jednego znacznika")
    return selected, low, high

def side_sign(side):
    """'right' -> +1, 'left' -> -1. Odmawia zamiast zgadywać.

    Wyjęte z `main()` na poziom modułu, bo tam siedziało za `bpy.ops` i żaden test
    nie mógł tego dotknąć — przemiatanie mutacyjne z 03.09.2026 pokazało tu mutację
    ocalałą. Strona osi jest JEDNYM Z CZTERECH założeń projektowych tego modułu
    i sam docstring modułu obiecuje, że są „sprawdzane, nie tylko zadeklarowane".

    Poprzednia wersja, `1.0 if side == "right" else -1.0`, odpowiadała „lewa"
    na KAŻDĄ wartość różną od „right", literówkę włącznie. `argparse` ma tu
    `choices`, więc na drodze z CLI to nie zdarzy się — ale ta funkcja jest
    wołana także z testów i z innych narzędzi, a cicha odpowiedź „lewa"
    postawiłaby wszystkie słupki po drugiej stronie toru.
    """
    if side == "right":
        return 1.0
    if side == "left":
        return -1.0
    raise ValueError(f"strona osi musi być 'right' albo 'left', nie {side!r}")

def clearance_problems(worst_gauge_m, worst_wall_m, profile_name):
    """Lista zarzutów wobec zmierzonych luzów. Pusta lista = słupki wolno wypuścić.

    Dwie bramki tego modułu, wyjęte z `main()` razem, bo odpowiadają na to samo
    pytanie i mają wspólną granicę: luz DOKŁADNIE zerowy jest jeszcze dopuszczony,
    ujemny nie. Zero jest tu granicą, a nie przypadkiem brzegowym — słupek stykający
    się ze skrajnią jeszcze się w niej nie znajduje.

    Kolejność zarzutów jest ustalona, bo trafia do komunikatu błędu.
    """
    problems = []
    if worst_gauge_m < 0.0:
        problems.append(f"słupek wchodzi w skrajnię pojazdu o {-worst_gauge_m:.3f} m — "
                        "zwiększ --offset-m")
    if worst_wall_m < 0.0:
        problems.append(f"słupek przebija ścianę profilu {profile_name} o "
                        f"{-worst_wall_m:.3f} m — zmniejsz --offset-m")
    return problems
