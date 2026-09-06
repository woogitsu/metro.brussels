#!/usr/bin/env python3
"""Nazwa pliku i pochodzenie siatki dla poziomu LOD-a — czysty Python, bez `bpy`.

**Dlaczego osobny moduł.** Do 06.09.2026 wybór między „poziom 0 dzieli plik
z chunkiem bazowym" a „poziom > 0 dostaje własny plik `_lodN`" siedział jako
`if level == 0` wewnątrz `lod_entries()` w `tunnel_sweep.py`, obok `import bpy`
na poziomie modułu. `level` pochodzi z `lod.LOD_LEVELS` — zwykłej listy słowników —
i nie ma w tym pytaniu nic z Blendera, ale przemiatanie mutacyjne liczyło je jako
„nieosiągalne", bo cały plik nie daje się zaimportować bez `bpy`.
`reports/bpy-extraction-round-2.md` §3: granicą do przecięcia jest **wiersz**,
nie funkcja.

Świadomie NIE ma tu `mesh.users == 0` z `drop_object` ani `item.users == 0`
z `clear_scene` — `.users` jest licznikiem odwołań żywego bloku danych Blendera;
test podstawiłby gołą liczbę i sprawdziłby `0 == 0`, nie zachowanie Blendera.
Ten sam wybór opisuje `material_specs.py` dla analogicznego `block.users == 0`
w `material_test_scene.py`.
"""


def is_base_level(level):
    """Czy to poziom 0 — ten, który NIE dostaje osobnego eksportu.

    Poziom 0 jest tożsamy z siatką bazową chunka (patrz `lod.py` §1: „LOD to
    podzbiór pierścieni LOD0"), więc nie generuje się dla niego osobna siatka
    ani osobny plik — dzieli ten, który `chunk_records()` eksportuje i tak.
    """
    return level == 0


def lod_output_path(chunk_id, level):
    """Nazwa pliku danego poziomu LOD, do złożenia z `chunk_dir` przez wołającego.

    Poziom 0 dzieli nazwę z chunkiem bazowym (`{chunk_id}.glb`, ten sam plik,
    który `chunk_records()` już eksportuje); każdy dalszy poziom dostaje własną
    nazwę `{chunk_id}_lod{level}.glb`. Nazwy są funkcją indeksu chunka i poziomu,
    więc są stabilne między przebiegami — manifest streamingowy je zapisuje,
    a Godot trzyma je w ścieżkach scen.
    """
    if is_base_level(level):
        return f"{chunk_id}.glb"
    return f"{chunk_id}_lod{level}.glb"
