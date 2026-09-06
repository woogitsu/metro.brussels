#!/usr/bin/env python3
"""Testy nazw plików LOD (`tools/blender/lod_paths.py`).

Wydzielone z `if level == 0:` w `lod_entries()` (`tools/blender/tunnel_sweep.py`),
które siedziało obok `import bpy` na poziomie modułu. `level` pochodzi z
`lod.LOD_LEVELS` — zwykłej listy słowników — więc pytanie nie miało nic wspólnego
z Blenderem, ale przemiatanie mutacyjne liczyło je jako nieosiągalne.
`reports/bpy-extraction-round-3.md` mierzy dokładnie to miejsce.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import lod_paths as LP  # noqa: E402


# --- is_base_level -------------------------------------------------------------

def test_level_zero_is_the_base_level():
    assert LP.is_base_level(0) is True


def test_a_positive_level_is_not_the_base_level():
    assert LP.is_base_level(1) is False
    assert LP.is_base_level(2) is False


# --- lod_output_path -------------------------------------------------------------

def test_base_level_shares_the_chunk_file_name():
    """Poziom 0 NIE dostaje własnego pliku — dzieli nazwę z chunkiem bazowym."""
    assert LP.lod_output_path("L1_A_c00", 0) == "L1_A_c00.glb"


def test_higher_levels_get_their_own_suffixed_file():
    assert LP.lod_output_path("L1_A_c00", 1) == "L1_A_c00_lod1.glb"
    assert LP.lod_output_path("L1_A_c00", 2) == "L1_A_c00_lod2.glb"


def test_two_different_chunks_never_collide_on_the_same_level():
    assert (LP.lod_output_path("L1_A_c00", 1)
            != LP.lod_output_path("L1_A_c01", 1))
