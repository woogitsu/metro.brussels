#!/usr/bin/env python3
"""Bramki „czy ten etap skanu ma się wykonać" dla `profile_vehicle.py` — czysty
Python, bez `bpy`.

**Dlaczego osobny moduł.** Do 06.09.2026 te trzy predykaty siedziały wewnątrz
`main()` w `profile_vehicle.py`, tuż obok `import bpy` na poziomie modułu.
Same nie wołały Blendera ani razu, ale przemiatanie mutacyjne liczyło je jako
„nieosiągalne", bo pytanie zadawane jest WYKONANIEM: `test_all.py` nie potrafi
zaimportować pliku z `import bpy`, więc żaden test nigdy nie doszedł do tych
linii. `reports/bpy-extraction-round-2.md` §3 nazwał to wprost: granicą do
przecięcia jest **wiersz**, nie funkcja — moduł „z `bpy`" może niemal w całości
składać się z arytmetyki, i to jest dokładnie ten przypadek.

Wszystkie trzy odpowiadają na pytanie „iść dalej czy nie", nie liczą geometrii —
ta siedzi w `clearance_profile.py` i `profile_scan.py`.

Świadomie NIE ma tu `obj.type == "MESH"` z `import_glb` ani filtra tego samego
kształtu na wierzchołku `bpy.data.objects` w `main()` — wartość porównania tam
pochodzi z żywego obiektu Blendera, testowanie `"MESH" == "MESH"` nie sprawdza
niczego. Ten sam wybór jest już opisany w `vehicle_fit.py` dla analogicznego
miejsca w `place_vehicle.py`.
"""


def should_refine(refine_step_m):
    """Czy doszlifować dołki wokół zgrubnego minimum. Krok <= 0 wyłącza doszlifowanie.

    Granica jest **wyłączna**: krok dokładnie 0,0 znaczy „nie doszlifowuj", tak samo
    jak krok ujemny. `--refine-step 0` jest udokumentowaną drogą wyłączenia tego etapu
    z CLI (`parse_args`), więc próg nie może zsunąć się na `>= 0` — to policzyłoby
    zero jako włączone i uruchomiło doszlifowanie o zerowym kroku.
    """
    return refine_step_m > 0.0


def should_verify(verify_full_count):
    """Czy przeliczyć próbkę pozycji naiwnie, po wszystkich wierzchołkach, dla kontroli redukcji.

    Granica jest **wyłączna**: `--verify-full 0` jest udokumentowaną drogą wyłączenia
    kontroli (kosztownej — liczy po WSZYSTKICH wierzchołkach, nie po kandydatach),
    więc zero musi dać `False`, nie `True`.
    """
    return verify_full_count > 0


def is_not_vehicle_tag(source_tag):
    """Czy znacznik `metro_source` NIE jest pojazdem — połowa filtra sceny `--swept-scene-out`.

    Scena obwiedni ma pokazać tunel i geometrię obwiedni obok siebie — pojazd,
    z którego obwiednia powstała, zaciemniałby widok i podwajał wierzchołki w tym
    samym miejscu. `main()` łączy to z `obj.type == "MESH"` w jednym warunku, ale
    te dwa pytania są różnej natury: `object_type` pyta Blendera „czy to w ogóle
    siatka" (wartość żywego obiektu, nie do przetestowania bez sceny — zostaje
    w `profile_vehicle.py`), a znacznik tutaj to zwykły string, który `import_glb`
    przypina sam i który dowolny test może podstawić bez sceny.

    Dopasowanie jest **dokładne**, nie przez `in`/`startswith`: znacznik `"vehicle"`
    ma wykluczyć TYLKO pojazd, nie `"vehicle_debug"` ani inny przyszły tag, który
    mógłby zacząć się tym samym słowem.
    """
    return source_tag != "vehicle"
