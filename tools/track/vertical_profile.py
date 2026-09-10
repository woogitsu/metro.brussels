#!/usr/bin/env python3
"""Profil pionowy osi z głębokości stacji — z JAWNĄ niewiadomą, nie z interpolacji przez nią.

    python3 tools/track/vertical_profile.py --axis data/track/L1_A.json \
        --depths data/network/station-depths.csv --out build/L1_A-vertical.json

DLACZEGO TO ISTNIEJE. `data/network/station-depths.csv` ma dwanaście wierszy pakietu A
i **trzy** wypełnione głębokości; dziewięć zostaje `unknown`, bo dwa oficjalne źródła
podają sprzeczne wartości i rejestr nie wybiera zwycięzcy (`reports/R-007-platform-dimensions.md`).
Decyzja właściciela z 07.09.2026: **budować z jawnym `unknown`**, a nie czekać na
uzupełnienie i nie zgadywać brakujących rzędnych.

DLACZEGO INTERPOLACJA NIE PRZECHODZI PRZEZ NIEWIADOMĄ. Odcinek między dwiema stacjami
o znanej rzędnej wolno wypełnić prostą — to jest założenie o stałym spadku i da się je
podważyć pomiarem. Odcinek, w którym leży stacja bez rzędnej, prostą wypełnić się NIE
da: przechodząca przez nią prosta twierdziłaby, że wiemy, na jakiej głębokości ta stacja
leży, a nie wiemy. Niewiadoma między dwiema wiadomymi jest **niewiadomą**, nie prostą.

**Ta reguła NIE jest hipotetyczna i pierwsza wersja tego docstringu myliła się co do tego.**
Zmierzone 07.09.2026 na `e6b4dc1`: trzy stacje ze rzędną to De Brouckère (3129,94 m),
Parc (4075,66 m) i Arts-Loi (4560,95 m), ale **Gare Centrale (3731,85 m) leży MIĘDZY
De Brouckère i Parc i rzędnej nie ma**. Para De Brouckère↔Parc jest więc rozspojona,
a wypełnić wolno wyłącznie Parc↔Arts-Loi. Naiwna interpolacja przez niewiadomą dałaby
1431,01 m profilu; reguła zostawia **485,29 m** nominalnie. Różnica **945,72 m** to
dokładnie tyle osi, ile takie narzędzie by zmyśliło.

DLACZEGO EKSTRAPOLACJI NIE MA WCALE. Poza zakresem pierwszej i ostatniej znanej stacji
każda wartość byłaby przedłużeniem spadku w rejon, o którym źródła nie mówią nic.
`build/` dostaje wtedy `null`, a nie ostatnią znaną rzędną powtórzoną w nieskończoność.

DLACZEGO DOPASOWANIE NAZW MA WŁASNĄ ASERCJĘ NA LICZBĘ. Nazwy w CSV i w osi nie zgadzają
się pole w pole. Zmierzone 07.09.2026 na `e6b4dc1`:

    dopasowanie naiwne (CSV `station_fr` wobec osi `name_fr`)          8 z 12
    pełny zestaw pól, dopasowanie ŚCISŁE                             12 z 12
    ten sam zestaw bez pola `name`                                   10 z 12

Cztery stacje, które gubi wariant naiwny, to `De Brouckère`, `Étangs Noirs`,
`Gare de l'Ouest` i `Comte de Flandre` — a wśród nich **De Brouckère, czyli jedna
z TRZECH stacji mających głębokość**. Naiwny czytnik straciłby jedną trzecią znanych
danych, wypisał profil i skończył kodem 0.

Ratuje to **zestaw pól**, nie normalizacja napisów: pole `name` niesie wariant
dwujęzyczny z pełną pisownią (`Comte de Flandre|Graaf van Vlaanderen`), a `name_nl`
łapie te wiersze, w których CSV podaje nazwę niderlandzką. Zdjęcie `name` kosztuje
dwie stacje — dlatego to pole jest w zestawie z pomiaru, nie z ostrożności.

**Pierwsza wersja tego narzędzia zdejmowała znaki diakrytyczne i wielkość liter,
a docstring uzasadniał to liczbą 8 z 12. To uzasadnienie było nieprawdziwe** i złapała
je kontrola negatywna, nie przegląd kodu: po zamianie normalizacji na `strip()` zestaw
przeszedł **16/16**, bo dopasowanie ścisłe po pełnym zestawie pól daje 12 z 12 i tak.
Liczba 8 z 12 opisuje wariant jednopolowy, którego to narzędzie nigdy nie używało.
Normalizacji więc NIE MA — martwy mechanizm z nieprawdziwym uzasadnieniem jest gorszy
od jego braku (`tools/tests/test_dead_constants.py`, ta sama zasada dla stałych).

Prawdziwym zabezpieczeniem jest **odmowa**: narzędzie kończy kodem 3 i wypisuje nazwy,
gdy nie dopasuje wszystkich stacji. Cicha utrata jest niemożliwa niezależnie od tego,
jak nazwy się w przyszłości rozjadą.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))
sys.path.insert(0, HERE)

import provenance as P  # noqa: E402
import stop_names  # noqa: E402

#: Wartości kolumny `confidence`, które NIOSĄ rzędną. `unknown` jej nie niesie, a każda
#: inna nazwa jest błędem danych, nie nowym poziomem ufności — dlatego lista jest zamknięta
#: i nierozpoznana wartość jest odmową, nie cichym pominięciem wiersza.
UFNOSCI_Z_RZEDNA = ("measured", "counted", "estimated")

#: Pełny zbiór dopuszczalnych wartości kolumny, razem z `unknown`.
UFNOSCI = UFNOSCI_Z_RZEDNA + ("unknown",)

#: Pola osi, po których szukamy nazwy z CSV. Zestaw jest z POMIARU, nie z ostrożności:
#: zdjęcie `name` kosztuje 2 stacje z 12 (patrz docstring modułu), więc to pole zarabia
#: na miejsce. `name_fr` i `name_nl` są dziś każde osobno zbędne, ale kosztują wiersz
#: i chronią przed rozjazdem, którego odmowa wprawdzie nie przepuści, ale i nie naprawi.
POLA_NAZW_OSI = ("name_fr", "name_nl", "name")

#: Pola CSV, którymi szukamy. Oba, bo rejestr podaje raz nazwę francuską, raz niderlandzką.
POLA_NAZW_CSV = ("station_fr", "station_nl")

#: Kody wyjścia. Rozdzielone, bo wołający ma prawo odróżnić „dane są niepełne, ale
#: narzędzie zrobiło swoje" od „nie umiem tych danych przeczytać".
KOD_OK = 0
KOD_ZLE_DANE = 2
KOD_BRAK_DOPASOWANIA = 3


def czytaj_glebokosci(path: str, pakiet: str) -> list[dict]:
    """Wiersze CSV dla jednego pakietu, w kolejności z pliku.

    Komentarze `#` odsiewane PRZED `DictReader`, bo pierwsze trzy wiersze pliku to proza
    dla człowieka, a nie nagłówek.
    """
    with io.open(path, encoding="utf-8") as handle:
        czyste = (linia for linia in handle if not linia.lstrip().startswith("#"))
        wiersze = [w for w in csv.DictReader(czyste) if (w.get("package") or "").strip() == pakiet]
    if not wiersze:
        raise ValueError(f"{path} nie ma ani jednego wiersza pakietu {pakiet!r}")
    for w in wiersze:
        ufnosc = (w.get("confidence") or "").strip()
        if ufnosc not in UFNOSCI:
            raise ValueError(
                f"{path}: stacja {w.get('station_fr')!r} ma confidence={ufnosc!r}, "
                f"a dopuszczalne są {list(UFNOSCI)}")
        surowa = (w.get("depth_m") or "").strip()
        if ufnosc == "unknown":
            if surowa:
                raise ValueError(
                    f"{path}: stacja {w.get('station_fr')!r} ma confidence=unknown, "
                    f"ale depth_m={surowa!r} — jedno z dwóch jest nieprawdą")
            w["_depth"] = None
        else:
            if not surowa:
                raise ValueError(
                    f"{path}: stacja {w.get('station_fr')!r} ma confidence={ufnosc!r} "
                    f"bez wartości depth_m")
            w["_depth"] = float(surowa)
            if w["_depth"] >= 0:
                raise ValueError(
                    f"{path}: stacja {w.get('station_fr')!r} ma depth_m={w['_depth']}, "
                    "a kolumna wymaga wartości UJEMNEJ (poniżej poziomu ulicy)")
    return wiersze


def dopasuj(stacje_osi: list[dict], wiersze: list[dict]) -> list[tuple[dict, dict]]:
    """Pary (stacja osi, wiersz CSV) — albo wyjątek nazywający niedopasowane.

    Dopasowanie idzie po nazwie znormalizowanej, nie po kolejności w plikach: zgodność
    kolejności jest dziś prawdziwa, ale nie jest niczym gwarantowana, a dopasowanie po
    indeksie przy przestawieniu jednego wiersza przypisałoby rzędną CUDZEJ stacji —
    czyli dałoby wynik gorszy niż odmowa.

    Nazwa osi brana z `name_fr` i z `name`, bo `name` niesie wariant dwujęzyczny
    (`Étangs Noirs|Zwarte Vijvers`) i sam bywa jedynym miejscem z pełną pisownią.
    """
    def klucze_osi(s):
        klucze = set()
        for pole in POLA_NAZW_OSI:
            if pole == "name":
                klucze |= set(stop_names.czlony(s.get("name") or ""))
            elif s.get(pole):
                klucze.add(s[pole].strip())
        return {k for k in klucze if k}

    pary, bez_pary_csv = [], []
    uzyte = set()
    for w in wiersze:
        szukane = {(w.get(pole) or "").strip() for pole in POLA_NAZW_CSV}
        szukane = {s for s in szukane if s}
        trafiona = None
        for idx, s in enumerate(stacje_osi):
            if idx in uzyte:
                continue
            if klucze_osi(s) & szukane:
                trafiona = idx
                break
        if trafiona is None:
            bez_pary_csv.append(w.get("station_fr"))
        else:
            uzyte.add(trafiona)
            pary.append((stacje_osi[trafiona], w))

    bez_pary_osi = [s.get("name") for idx, s in enumerate(stacje_osi) if idx not in uzyte]
    if bez_pary_csv or bez_pary_osi:
        raise LookupError(
            "dopasowano %d z %d stacji; bez pary w CSV: %s; bez pary w osi: %s"
            % (len(pary), len(stacje_osi), bez_pary_csv or "brak", bez_pary_osi or "brak"))
    return pary


def kilometraze(punkty: list[list[float]]) -> list[float]:
    """Kilometraż narastający po łamanej, w metrach. Liczony w płaszczyźnie XY.

    Z jest w `data/track/*.json` placeholderem (`vertical.status = "not_modelled"`),
    więc wciągnięcie go do długości dodałoby zero do każdego odcinka i tylko udawało,
    że coś mierzy.
    """
    suma, out = 0.0, [0.0]
    for (x1, y1, _), (x2, y2, _) in zip(punkty, punkty[1:]):
        suma += math.hypot(x2 - x1, y2 - y1)
        out.append(suma)
    return out


def profil(pary: list[tuple[dict, dict]], km_punktow: list[float]) -> tuple[list[dict], list[dict]]:
    """Rzędna dla każdego punktu osi. Zwraca (punkty profilu, stacje w kolejności kilometrażu).

    Interpolacja liniowa WYŁĄCZNIE między dwiema SĄSIEDNIMI w kilometrażu stacjami,
    które obie mają rzędną. Jeżeli między nimi leży stacja bez rzędnej — odcinek jest
    niewiadomą; patrz docstring modułu.
    """
    stacje = sorted(
        ({"chainage_m": float(s["chainage_m"]),
          "name": s.get("name"),
          "depth_m": w["_depth"],
          "confidence": (w.get("confidence") or "").strip()}
         for s, w in pary),
        key=lambda z: z["chainage_m"])

    # Odcinki, które wolno wypełnić: para sąsiadów, oba ze rzędną. Sąsiedztwo liczone
    # na PEŁNEJ liście stacji, więc stacja bez rzędnej stojąca w środku rozspaja parę.
    odcinki = []
    for lewa, prawa in zip(stacje, stacje[1:]):
        if lewa["depth_m"] is not None and prawa["depth_m"] is not None:
            odcinki.append((lewa, prawa))

    punkty = []
    for km in km_punktow:
        wpis = {"chainage_m": round(km, 3), "depth_m": None,
                "confidence": "unknown", "interpolated": False, "between": None}
        for lewa, prawa in odcinki:
            if lewa["chainage_m"] <= km <= prawa["chainage_m"]:
                rozpietosc = prawa["chainage_m"] - lewa["chainage_m"]
                t = 0.0 if rozpietosc == 0 else (km - lewa["chainage_m"]) / rozpietosc
                rzedna = lewa["depth_m"] + t * (prawa["depth_m"] - lewa["depth_m"])
                # Ufność interpolacji nie może być wyższa od SŁABSZEGO końca. Oba końce
                # są dziś `estimated`, ale reguła jest w kodzie, żeby wypełnienie jednej
                # rzędnej pomiarem nie podniosło po cichu ufności całego odcinka.
                slabszy = max(UFNOSCI_Z_RZEDNA.index(lewa["confidence"]),
                              UFNOSCI_Z_RZEDNA.index(prawa["confidence"]))
                wpis.update(depth_m=round(rzedna, 3),
                            confidence=UFNOSCI_Z_RZEDNA[slabszy],
                            interpolated=(t not in (0.0, 1.0)),
                            between=[lewa["name"], prawa["name"]])
                break
        punkty.append(wpis)
    return punkty, stacje


def pokrycie(punkty: list[dict], km_punktow: list[float], stacje: list[dict]) -> dict:
    """Metry osi ze rzędną i bez — DWIE liczby, bo mierzą dwie różne rzeczy.

    `with_depth_m` liczy po ODCINKACH ŁAMANEJ, których OBA końce mają rzędną. Liczenie
    po punktach zawyżałoby albo zaniżało zależnie od zagęszczenia — `data/track/L1_A.json`
    ma odcinki od 5 do 20 m, więc „procent punktów" nie jest procentem osi.

    `defined_span_m` liczy ROZPIĘTOŚĆ NOMINALNĄ odcinków między sąsiednimi stacjami ze
    rzędną — czyli tyle osi, na ile profil jest ZDEFINIOWANY, niezależnie od tego, gdzie
    wypadły wierzchołki łamanej.

    **Rozdzielenie tych dwóch liczb jest naprawą zmierzonej pomyłki, nie ozdobą.** Na
    `e6b4dc1` wychodzi 468,385 m wobec 485,29 m nominalnie, a różnica 16,904 m ma jedną
    przyczynę: łamana nie ma wierzchołka na kilometrażu Parc (4075,66 m), najbliższy
    stoi na 4092,564 m. Podana sama, pierwsza liczba czytałaby się jako „profil pokrywa
    7 % osi", co jest nieprawdą o profilu — jest prawdą o wierzchołkach łamanej.
    """
    z_rzedna = 0.0
    for (km1, w1), (km2, w2) in zip(zip(km_punktow, punkty), zip(km_punktow[1:], punkty[1:])):
        if w1["depth_m"] is not None and w2["depth_m"] is not None:
            z_rzedna += km2 - km1
    rozpietosc = 0.0
    for lewa, prawa in zip(stacje, stacje[1:]):
        if lewa["depth_m"] is not None and prawa["depth_m"] is not None:
            rozpietosc += prawa["chainage_m"] - lewa["chainage_m"]
    calosc = km_punktow[-1] if km_punktow else 0.0
    return {"axis_length_m": round(calosc, 3),
            "with_depth_m": round(z_rzedna, 3),
            "without_depth_m": round(calosc - z_rzedna, 3),
            "with_depth_percent": round(100.0 * z_rzedna / calosc, 2) if calosc else 0.0,
            "defined_span_m": round(rozpietosc, 3),
            "defined_span_percent": round(100.0 * rozpietosc / calosc, 2) if calosc else 0.0}


def zbuduj(axis_path: str, depths_path: str, pakiet: str | None = None) -> dict:
    axis = json.load(io.open(axis_path, encoding="utf-8"))
    pakiet = pakiet or (axis.get("package") or {}).get("id")
    if not pakiet:
        raise ValueError(f"{axis_path} nie podaje `package.id`, a `--package` nie zostało podane")
    wiersze = czytaj_glebokosci(depths_path, pakiet)
    pary = dopasuj(axis["stations"], wiersze)
    km_punktow = kilometraze(axis["points"])
    punkty, stacje = profil(pary, km_punktow)
    with io.open(depths_path, "rb") as handle:
        odcisk = hashlib.sha256(handle.read()).hexdigest()
    znane = [z for z in stacje if z["depth_m"] is not None]
    return {
        "schema_version": 1,
        "axis_id": axis.get("id"),
        "package": pakiet,
        "generated_at": P.utc_now_iso(),
        "source": {
            "axis": os.path.relpath(axis_path, ROOT),
            "depths": os.path.relpath(depths_path, ROOT),
            "depths_sha256": odcisk,
        },
        "stations": stacje,
        "stations_with_depth": len(znane),
        "stations_total": len(stacje),
        "coverage": pokrycie(punkty, km_punktow, stacje),
        "points": punkty,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--axis", required=True, help="oś pakietu, np. data/track/L1_A.json")
    ap.add_argument("--depths", required=True, help="data/network/station-depths.csv")
    ap.add_argument("--out", required=True, help="ścieżka wyjściowa w build/")
    ap.add_argument("--package", default=None,
                    help="identyfikator pakietu; domyślnie brany z osi")
    args = ap.parse_args(argv)

    try:
        raport = zbuduj(args.axis, args.depths, args.package)
    except LookupError as blad:
        print(f"[PROFIL] BŁĄD dopasowania stacji: {blad}", file=sys.stderr)
        return KOD_BRAK_DOPASOWANIA
    except (ValueError, KeyError) as blad:
        print(f"[PROFIL] BŁĄD danych: {blad}", file=sys.stderr)
        return KOD_ZLE_DANE

    katalog = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(katalog, exist_ok=True)
    with io.open(args.out, "w", encoding="utf-8") as handle:
        json.dump(raport, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    p = raport["coverage"]
    print("[PROFIL] oś %s, pakiet %s, %.2f m" % (raport["axis_id"], raport["package"],
                                                 p["axis_length_m"]))
    print("[PROFIL] stacji ze rzędną: %d z %d" % (raport["stations_with_depth"],
                                                  raport["stations_total"]))
    for z in raport["stations"]:
        znacznik = ("%.1f m (%s)" % (z["depth_m"], z["confidence"])
                    if z["depth_m"] is not None else "NIEWIADOMA")
        print("[PROFIL]   %8.2f m  %-38s %s" % (z["chainage_m"], z["name"], znacznik))
    print("[PROFIL] profil ZDEFINIOWANY na: %.2f m z %.2f m (%.2f %%)"
          % (p["defined_span_m"], p["axis_length_m"], p["defined_span_percent"]))
    print("[PROFIL] odcinków łamanej z rzędną na obu końcach: %.2f m (%.2f %%)"
          % (p["with_depth_m"], p["with_depth_percent"]))
    print("[PROFIL] osi bez rzędnej: %.2f m — zapisane jako depth_m=null, confidence=unknown"
          % p["without_depth_m"])
    print("[PROFIL] zapisane: %s" % args.out)
    return KOD_OK


if __name__ == "__main__":
    sys.exit(main())
