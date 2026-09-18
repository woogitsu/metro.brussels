#!/usr/bin/env python3
"""Porownanie sum PNG miedzy DWOMA przebiegami tego samego commita.

Potok wizualny zapisuje w metadanych KAZDEJ klatki dwie sumy: `sha256` calego
pliku PNG i `idat_sha256` samych pikseli. Zapisuje je od dawna — ale nikt ich
miedzy przebiegami nie porownuje, i to jest cala dziura, ktora to narzedzie
zamyka.

**Porownuje sie `idat_sha256`, a nie `sha256`, i jest to WYNIK POMIARU.**
Suma calego pliku rozni sie na KAZDEJ klatce nawet wtedy, gdy piksele sa
bit-identyczne — bo PNG niesie w naglowkach rzeczy, ktore zmieniaja sie miedzy
przebiegami. Sito na `sha256` zglasza wiec kazda pare i liczba przestaje
cokolwiek znaczyc; zmierzone przy 6.D280 na parze z TEJ SAMEJ maszyny.
"""
import argparse
import json
import sys


def sumy_z_metadanych(sciezki):
    """`{prefix/kamera: (sha256, idat_sha256)}` z podanych plikow `*_metadata.json`.

    Bierze LISTE SCIEZEK, a nie katalog, i nie chodzi po drzewie samo. Rozwiniecie
    wzorca zostaje po stronie powloki — narzedzie czyta artefakt CI, ktory lezy
    poza repozytorium, wiec odsianie z `.gitignore` nic by tu nie znaczylo,
    a wlasna kopia takiej listy byloby druga lista tej samej rzeczy.
    """
    out = {}
    for sciezka in sorted(sciezki):
        with open(sciezka, encoding="utf-8") as uchwyt:
            dane = json.load(uchwyt)
        prefiks = dane.get("prefix", "?")
        for kamera in dane.get("cameras", []):
            klucz = "%s/%s" % (prefiks, kamera.get("id"))
            out[klucz] = (kamera.get("sha256"), kamera.get("idat_sha256"))
    return out


def rozjazdy(pierwszy, drugi, po_pikselach=True):
    """Klucze wspolne, ktorych suma sie rozni. Domyslnie po pikselach."""
    indeks = 1 if po_pikselach else 0
    wspolne = sorted(set(pierwszy) & set(drugi))
    return [k for k in wspolne if pierwszy[k][indeks] != drugi[k][indeks]]


def porownaj(pierwszy, drugi, po_pikselach=True):
    """`(wspolnych, rozjazdy, tylko_w_pierwszym, tylko_w_drugim)`."""
    wspolne = sorted(set(pierwszy) & set(drugi))
    return (wspolne,
            rozjazdy(pierwszy, drugi, po_pikselach),
            sorted(set(pierwszy) - set(drugi)),
            sorted(set(drugi) - set(pierwszy)))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pierwszy", required=True, nargs="+",
                   help="pliki `*_metadata.json` proby 1 (wzorzec rozwija powloka)")
    p.add_argument("--drugi", required=True, nargs="+",
                   help="pliki `*_metadata.json` proby 2")
    p.add_argument("--po-pliku", action="store_true",
                   help="porownaj `sha256` calego pliku zamiast pikseli "
                        "(zglasza kazda pare — patrz docstring)")
    a = p.parse_args(argv)
    pierwszy, drugi = sumy_z_metadanych(a.pierwszy), sumy_z_metadanych(a.drugi)
    wspolne, rozne, tylko1, tylko2 = porownaj(pierwszy, drugi, not a.po_pliku)
    print("[SUMY] wspolnych klatek: %d" % len(wspolne))
    if tylko1 or tylko2:
        print("[SUMY] tylko w probie 1: %d, tylko w probie 2: %d"
              % (len(tylko1), len(tylko2)))
    if not rozne:
        print("[SUMY] zaden piksel sie nie rozni")
        return 0
    print("[SUMY] ROZJAZD na %d klatkach:" % len(rozne))
    for k in rozne:
        print("   %s" % k)
    return 1


if __name__ == "__main__":
    sys.exit(main())
