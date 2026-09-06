#!/usr/bin/env python3
"""Predykaty rejestru materiałów i kontrola wytworów — czysty Python, bez `bpy`.

**Dlaczego osobny moduł.** Cztery pytania niżej nie dotykają Blendera ani razu, ale
zadawano je **wewnątrz** funkcji, które go wołają. Przegląd mutacyjny liczył je jako
nieosiągalne: 8 z 12 mutacji `material_test_scene.py`.

Pułapka, w którą sam wpadłem 06.09.2026 i którą ten docstring zapisuje, żeby nie
powtórzyła się przy następnym module: klasyfikacja po **funkcjach** („czy gdziekolwiek
pada tu `bpy`") mówiła, że w tym pliku nie ma czego wyciągać — zero z dwunastu.
Klasyfikacja po **wierszach**, na których naprawdę siedzą mutacje, dała osiem.
Kod bez `bpy` bywa zamurowany w funkcji z `bpy`, i to jest typowy przypadek,
a nie wyjątek.

Wszystkie cztery są **bramkami**, nie pomocnikami: odpowiadają „czy wolno iść dalej".
"""
import os

#: Poniżej tylu bajtów plik nie jest renderem ani eksportem, tylko śladem po awarii.
#: Blender potrafi zapisać nagłówek PNG i przewrócić się przed pikselami; taki plik
#: istnieje, ma niezerowy rozmiar i przechodzi `os.path.isfile`. Zmierzone przy T-902:
#: najmniejszy poprawny render kontrolny miał 41 kB, najmniejszy sensowny GLB 12 kB.
MINIMUM_ARTEFACT_BYTES = 1024


def artefact_is_missing(path, minimum_bytes=MINIMUM_ARTEFACT_BYTES):
    """Czy wytwór NIE powstał: brak pliku albo plik nie większy niż próg.

    Granica jest **włącznie**: plik o rozmiarze dokładnie progu jest odrzucany.
    Próg nie jest rozmiarem poprawnego pliku, tylko sufitem na śmieć — plik równy
    sufitowi jest jeszcze śmieciem.
    """
    return not os.path.isfile(path) or os.path.getsize(path) <= minimum_bytes


def is_transparent(spec):
    """Czy materiał wymaga trybu mieszania. Krycie DOKŁADNIE 1,0 jest nieprzezroczyste.

    Granica jest **wyłączna** i to jest cała treść tej funkcji: `alpha == 1.0` znaczy
    „pełne krycie", więc przełączanie takiego materiału w tryb mieszania byłoby
    kosztem bez powodu i zmieniłoby wygląd renderu przy zerowej zmianie danych.
    """
    return float(spec.get("alpha", 1.0)) < 1.0


def is_glass(spec):
    """Czy próbkę tego materiału pokazać na kuli zamiast na sześcianie.

    Szkło na sześcianie wygląda jak sześcian z dziwnym cieniowaniem; dopiero na kuli
    widać załamanie. Dopasowanie jest po **dokładnym** identyfikatorze, nie po
    fragmencie: `"glass"` ma nie trafiać w `"glass_frosted"`, bo tamten może chcieć
    innej bryły.
    """
    return spec.get("id") == "glass"


def spec_id_problems(specs):
    """Lista zarzutów wobec identyfikatorów rejestru. Pusta lista = wolno budować.

    Identyfikatory są kluczem, po którym scena odnajduje próbkę do kadru zbliżenia.
    Duplikat znaczy, że jedna próbka przesłoni drugą **po cichu** — obie powstaną,
    a kamera wybierze którąś. Pusty identyfikator znaczy to samo dla pierwszej
    napotkanej pustej wartości.
    """
    problems = []
    ids = [s.get("id") for s in specs]
    if len(ids) != len(set(ids)):
        powtorzone = sorted({i for i in ids if ids.count(i) > 1 and i})
        problems.append(f"powtórzone identyfikatory materiałów: {powtorzone}")
    if any(not i for i in ids):
        problems.append(f"{sum(1 for i in ids if not i)} materiałów bez identyfikatora")
    return problems
