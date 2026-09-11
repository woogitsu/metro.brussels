#!/usr/bin/env python3
"""Oś z rzędnymi tam, gdzie są, i płaska tam, gdzie ich nie ma — z JAWNĄ granicą.

    python3 tools/track/apply_vertical.py --axis data/track/L1_A.json \
        --profile build/L1_A-vertical.json --out build/L1_A-partial-vertical.json

DLACZEGO TO ISTNIEJE. `vertical_profile.py` liczy rzędne od 07.09.2026 i nikt ich nie
ogląda: sześć osi w `data/track/` ma `vertical.status = not_modelled`, wszystkie punkty
mają Z = 0, a `tunnel_manifest.variant_plan` odrzuca `production`. Wynik pomiaru nie
wchodził więc do geometrii wcale. Ta pozycja go wpuszcza — te rzędne, które SĄ, i ani
metra więcej.

**PISZE DO `build/`, NIGDY DO `data/`.** Oś źródłowa jest tylko do odczytu (§4.6),
a wynik jest pochodną dwóch plików i da się go odtworzyć w każdej chwili.

## Co znaczy Z w wyniku i czego NIE znaczy

`depth_m` z rejestru to **poziom główki szyny względem poziomu ulicy**, wartość ujemna.
W wyniku Z jest więc liczone od poziomu ulicy, a nie od główki szyny — i to jest zmiana
układu odniesienia wobec osi wejściowej, gdzie Z = 0 jest wypełniaczem.

Stąd druga połowa, ważniejsza: **Z = 0 na odcinku bez rzędnej NIE znaczy „główka szyny
na poziomie ulicy"**. Znaczy „nie wiemy" — tak samo, jak znaczyło w osi wejściowej.
Odcinek płaski jest wypełniaczem, nie pomiarem, i manifest ma to mówić.

## Dlaczego granica jest USKOKIEM, a nie zbiegiem

Między ostatnim punktem bez rzędnej a pierwszym z rzędną Z skacze o kilkanaście metrów.
Wygładzenie tego skoku znaczyłoby, że znamy spadek prowadzący do znanego odcinka — a nie
znamy go, i dokładnie o tym mówi reguła z `vertical_profile.py`, która zabrania
interpolacji przez niewiadomą. Uskok jest **widoczny w metadanych i policzalny**:
`vertical.boundaries` podaje kilometraż każdego przejścia i wysokość skoku.

Uskok jest artefaktem granicy wiedzy, nie spadkiem toru. Zdanie o tym stoi w wyniku,
w polu `vertical.note`, a nie tylko tutaj.
"""
import argparse
import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import provenance as P  # noqa: E402

#: Status wpisywany do osi wynikowej. Nie `modelled`, bo profil obejmuje 7 % długości,
#: i nie `not_modelled`, bo te 7 % jest prawdziwe. Trzecia nazwa, żeby żadna bramka
#: nie musiała zgadywać, którą z dwóch dawnych ma na myśli.
STATUS_CZASTKOWY = "partial"

#: Kod wyjścia, gdy profil nie pasuje do osi. Odmowa, nie cicha korekta.
KOD_ROZJAZD = 4


def _wczytaj(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def granice(punkty_z):
    """Miejsca, w których rzędna pojawia się albo znika. Lista uskoków.

    Każdy wpis to `(indeks, kilometraż, z_przed, z_po)` — czyli dokładnie tyle, ile
    trzeba, żeby powiedzieć, gdzie kończy się wiedza i o ile metrów skacze Z.
    """
    out = []
    for i in range(1, len(punkty_z)):
        przed = punkty_z[i - 1]
        po = punkty_z[i]
        if (przed["znana"]) != (po["znana"]):
            out.append({
                "index": i,
                "chainage_m": round(po["chainage_m"], 3),
                "z_before_m": round(przed["z_m"], 3),
                "z_after_m": round(po["z_m"], 3),
                "step_m": round(po["z_m"] - przed["z_m"], 3),
                "into": "known" if po["znana"] else "unknown",
            })
    return out


def zastosuj(axis, profil):
    """Oś z Z z profilu tam, gdzie jest, i Z = 0 tam, gdzie go nie ma."""
    punkty = axis["points"]
    wpisy = profil["points"]
    if len(punkty) != len(wpisy):
        raise ValueError(
            f"profil ma {len(wpisy)} punktów, a oś {len(punkty)} — to nie jest profil "
            "tej osi")
    if profil.get("axis_id") and axis.get("id") and profil["axis_id"] != axis["id"]:
        raise ValueError(
            f"profil jest dla osi {profil['axis_id']}, a wejście to {axis['id']}")

    nowe = []
    opis = []
    for punkt, wpis in zip(punkty, wpisy):
        x, y = float(punkt[0]), float(punkt[1])
        glebokosc = wpis.get("depth_m")
        z = 0.0 if glebokosc is None else float(glebokosc)
        nowe.append([x, y, round(z, 4)])
        opis.append({"chainage_m": wpis["chainage_m"], "z_m": z,
                     "znana": glebokosc is not None})

    ze_rzedna = [o for o in opis if o["znana"]]
    wynik = dict(axis)
    wynik["points"] = nowe
    wynik["vertical"] = {
        "status": STATUS_CZASTKOWY,
        "note": ("Z liczone od poziomu ulicy z `depth_m` rejestru głębokości. "
                 "Z = 0 NIE znaczy główki szyny na poziomie ulicy — znaczy BRAK "
                 "rzędnej. Uskok na granicy jest artefaktem granicy wiedzy, nie "
                 "spadkiem toru; wygładzenie go twierdziłoby, że znamy spadek "
                 "prowadzący do znanego odcinka."),
        "source_profile": {
            "axis_id": profil.get("axis_id"),
            "depths_sha256": (profil.get("source") or {}).get("depths_sha256"),
            "stations_with_depth": profil.get("stations_with_depth"),
            "stations_total": profil.get("stations_total"),
        },
        "coverage": profil.get("coverage"),
        "points_with_z": len(ze_rzedna),
        "points_total": len(opis),
        "z_min_m": round(min((o["z_m"] for o in ze_rzedna), default=0.0), 3),
        "z_max_m": round(max((o["z_m"] for o in ze_rzedna), default=0.0), 3),
        "boundaries": granice(opis),
        "generated_at": P.utc_now_iso(),
    }
    return wynik


def przytnij(wynik):
    """Oś obcięta do SAMEGO odcinka o znanych rzędnych, z kilometrażem od zera.

    **Po co, skoro pole „Wyjście" 6.D120 prosi o tunel płaski poza odcinkiem
    znanym.** Bo pełna oś z uskokiem NIE DA SIĘ zamiatać i to jest zmierzone, nie
    przewidziane: `tunnel_sweep.py` na osi z uskokiem 19,7 m na 15 m kilometrażu
    kończy odmową własnej bramki geometrycznej — `BŁĄD: skręt ramki 56.62 st.` przy
    progu `MAX_TWIST_DEG` równym pięć stopni. Ramka Freneta obraca się na takim
    skoku o kilkadziesiąt stopni między pierścieniami i siatka wychodzi skręcona.

    Zostają trzy drogi i dwie są zamknięte: wygładzić uskok (zabrania tego pole
    „Poza zakresem" i cała reguła `vertical_profile.py`), podnieść próg skrętu
    (to wyłączenie bramki, nie naprawa) albo **nie zamiatać przez granicę**. Ta
    funkcja robi to trzecie: scena kończy się tam, gdzie kończy się wiedza, a obie
    granice zostają w metadanych razem z powodem przycięcia.
    """
    punkty = wynik["points"]
    pionowy = wynik["vertical"]
    znane = [i for i, p in enumerate(punkty) if p[2] != 0.0]
    if not znane:
        raise ValueError("oś nie ma ani jednego punktu ze rzędną — nie ma czego przycinać")
    od, do = znane[0], znane[-1]
    if do - od + 1 != len(znane):
        raise ValueError(
            "punkty ze rzędną nie są ciągłe — przycięcie dałoby oś z dziurą w środku")

    wyciety = dict(wynik)
    wyciety["points"] = [list(p) for p in punkty[od:do + 1]]
    wyciety["id"] = f"{wynik.get('id', 'axis')}_known"
    wyciety["stations"] = [s for s in wynik.get("stations", [])
                           if punkty[od] and _w_zakresie(s, wynik, od, do)]
    nowy_pionowy = dict(pionowy)
    nowy_pionowy["cropped"] = {
        "reason": ("pełna oś z uskokiem nie przechodzi bramki geometrycznej "
                   "generatora: skręt ramki 56.62 st. przy progu 5.0 st. "
                   "(zmierzone 11.09.2026). Scena kończy się tam, gdzie kończy się "
                   "wiedza — granice zostają niżej."),
        "from_index": od,
        "to_index": do,
        "points": len(wyciety["points"]),
        "boundaries": pionowy["boundaries"],
    }
    nowy_pionowy["boundaries"] = []
    wyciety["vertical"] = nowy_pionowy
    return wyciety


def _w_zakresie(stacja, wynik, od, do):
    """Czy stacja leży w kilometrażu wyciętego odcinka."""
    km = float(stacja.get("chainage_m", -1.0))
    wpisy = wynik["vertical"].get("_km")
    if wpisy:
        return wpisy[od] <= km <= wpisy[do]
    granice = wynik["vertical"]["boundaries"]
    if len(granice) != 2:
        return False
    return granice[0]["chainage_m"] <= km <= granice[1]["chainage_m"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--axis", required=True)
    ap.add_argument("--profile", required=True, help="wyjście tools/track/vertical_profile.py")
    ap.add_argument("--out", required=True, help="ścieżka w build/")
    ap.add_argument("--span", default="all", choices=("all", "known"),
                    help="`all` — cała oś z uskokiem na granicy wiedzy (nie da się jej "
                         "zamiatać, patrz `przytnij`); `known` — sam odcinek ze rzędnymi")
    args = ap.parse_args(argv)

    if os.path.abspath(args.out).startswith(os.path.join(ROOT, "data") + os.sep):
        print("[PIONOWY] BŁĄD: wynik nie zapisuje się do `data/` — to jest katalog "
              "tylko do odczytu (§4.6)", file=sys.stderr)
        return KOD_ROZJAZD

    try:
        wynik = zastosuj(_wczytaj(args.axis), _wczytaj(args.profile))
        if args.span == "known":
            wynik = przytnij(wynik)
    except ValueError as blad:
        print(f"[PIONOWY] BŁĄD: {blad}", file=sys.stderr)
        return KOD_ROZJAZD

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with io.open(args.out, "w", encoding="utf-8") as handle:
        json.dump(wynik, handle, ensure_ascii=False, indent=1)

    pionowy = wynik["vertical"]
    print(f"[PIONOWY] punktów z rzędną: {pionowy['points_with_z']}/{pionowy['points_total']}"
          f"  Z od {pionowy['z_min_m']} do {pionowy['z_max_m']} m")
    przyciete = pionowy.get("cropped")
    if przyciete:
        print(f"[PIONOWY] oś PRZYCIĘTA do odcinka znanego: {przyciete['points']} punktów "
              f"(indeksy {przyciete['from_index']}..{przyciete['to_index']})")
        print(f"[PIONOWY] powód przycięcia: {przyciete['reason']}")
    for granica in pionowy["boundaries"] or (przyciete or {}).get("boundaries", []):
        print(f"[PIONOWY] granica wiedzy na {granica['chainage_m']} m: "
              f"Z {granica['z_before_m']} -> {granica['z_after_m']} m "
              f"(uskok {granica['step_m']} m, wchodzi w {granica['into']})")
    print(f"[PIONOWY] status osi: {pionowy['status']} — uskok jest artefaktem granicy "
          "wiedzy, nie spadkiem toru")
    print(f"[PIONOWY] zapisane: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
