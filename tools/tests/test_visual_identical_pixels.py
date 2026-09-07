#!/usr/bin/env python3
"""Bramka zgodności klatek CO DO BAJTU (pozycja 6.D9).

**Co ta bramka dodaje do progów, które już są.** Progi (`MAE`, `p95`, `SSIM`)
odpowiadają na pytanie „czy klatka jest DOSTATECZNIE podobna" i przy porównaniu
z baselinem po zmianie sceny jest to pytanie właściwe. Test determinizmu pyta
o co innego: to samo wejście ma dać to samo wyjście. Tam „mieści się w progach"
jest odpowiedzią za słabą — przepuszcza różnicę, której przy identycznym wejściu
nie ma prawa być, i przepuszcza ją po cichu.

**Dlaczego wyrocznią jest suma `IDAT`, a nie suma pliku.** Zmierzone 06.09.2026 na
dwóch przebiegach tej samej sceny (ten sam GLB, te same kamery, Blender 5.2.1):
z 18 chunków PNG różnią się DWA, oba `tEXt` — `Date` i `RenderTime`. Suma całego
pliku różni się więc na każdej klatce i jako wyrocznia determinizmu jest bezużyteczna;
suma `IDAT` nie różni się na żadnej.

Testy nie wołają Blendera: PNG-i buduje się tu z bajtów. Bramka ma się dać sprawdzić
na maszynie, na której `doctor.sh` przepuszcza brak Blendera jako „pomijam".
"""
import json
import os
import struct
import sys
import tempfile
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))
sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))

import compare as C  # noqa: E402
import png_pixels_sha256 as P  # noqa: E402

# Progi brane z manifestu kamer, nie wpisane z ręki: bramka sprawdzana na progach
# innych niż produkcyjne odpowiadałaby na inne pytanie niż to, które zadaje CI.
# Zdjęte są wyłącznie progi „pustej klatki" — testowy PNG 2x1 nie ma jak ich spełnić,
# a pozycja 6.D9 nie dotyczy wykrywania pustej klatki.
with open(os.path.join(ROOT, "tools", "visual", "cameras.json"), encoding="utf-8") as _h:
    _PROGI = json.load(_h)["scene_sets"]["infrastructure"]["thresholds"]
THRESHOLDS = dict(_PROGI, min_ink_fraction=0.0, min_luma_std=0.0, min_distinct_levels=1)


def _png(path, pixels, text=None):
    """PNG 2x1 RGB o zadanych pikselach, z opcjonalnym blokiem `tEXt`."""
    def blok(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00" + pixels)
    out = [P.PNG_MAGIC, blok(b"IHDR", ihdr)]
    if text is not None:
        out.append(blok(b"tEXt", text))
    out += [blok(b"IDAT", idat), blok(b"IEND", b"")]
    with open(path, "wb") as handle:
        handle.write(b"".join(out))


def _para(tmp, piksele_a, piksele_b, tekst_a=None, tekst_b=None):
    a = os.path.join(tmp, "a.png")
    b = os.path.join(tmp, "b.png")
    _png(a, piksele_a, tekst_a)
    _png(b, piksele_b, tekst_b)
    return a, b


def test_te_same_piksele_z_innym_tEXt_sa_zgodne_co_do_bajtu():
    """To jest DOKŁADNIE przypadek Blendera: ta sama klatka, inny stempel czasu."""
    with tempfile.TemporaryDirectory() as tmp:
        a, b = _para(tmp, b"\xff\x00\x00\x00\xff\x00", b"\xff\x00\x00\x00\xff\x00",
                     b"Date\x002026/09/06 09:52:07", b"Date\x002026/09/06 09:52:50")
        assert P.idat_sha256(a) == P.idat_sha256(b), "suma IDAT nie ma prawa zależeć od tEXt"
        with open(a, "rb") as ha, open(b, "rb") as hb:
            assert ha.read() != hb.read(), "pliki MAJĄ się różnić — inaczej test niczego nie mierzy"

        wynik = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=a,
                              require_identical_pixels=True)
        assert wynik["status"] == "pass", wynik
        assert wynik["checks"]["identical_pixels"] is True, wynik


def test_jeden_inny_piksel_zapala_bramke_mimo_ze_progi_go_przepuszczaja():
    """Sedno pozycji 6.D9. Różnica jednego kanału na dwóch pikselach mieści się
    w progach z manifestu — i właśnie dlatego sama bramka progowa jest tu za słaba.
    """
    with tempfile.TemporaryDirectory() as tmp:
        a, b = _para(tmp, b"\xff\x00\x00\x00\xff\x00", b"\xfe\x00\x00\x00\xff\x00")

        progowo = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=a)
        assert progowo["status"] == "pass", (
            "kontrola założenia: bez żądania zgodności co do bajtu ta różnica "
            "PRZECHODZI przez progi — gdyby nie przechodziła, test niżej nie "
            "dowodziłby niczego")
        assert progowo["checks"]["regression"] is True

        dokladnie = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=a,
                                  require_identical_pixels=True)
        assert dokladnie["status"] == "fail", dokladnie
        assert dokladnie["checks"]["identical_pixels"] is False
        assert "co do bajtu" in dokladnie["reason"], dokladnie["reason"]


def test_bez_zadania_zgodnosci_bramka_w_ogole_nie_dopisuje_swojego_pola():
    """Domyślne zachowanie ma zostać nietknięte: pozycja zmienia WYROCZNIĘ tam, gdzie
    się o nią prosi, a nie kryterium wszystkich porównań.
    """
    with tempfile.TemporaryDirectory() as tmp:
        a, b = _para(tmp, b"\xff\x00\x00\x00\xff\x00", b"\xfe\x00\x00\x00\xff\x00")
        wynik = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=a)
        assert "identical_pixels" not in wynik["checks"], wynik["checks"]
        assert "idat_sha256" not in wynik["metrics"], wynik["metrics"]


def test_wynik_niesie_obie_sumy_zeby_dalo_sie_zobaczyc_ktora_klatka_odjechala():
    with tempfile.TemporaryDirectory() as tmp:
        a, b = _para(tmp, b"\xff\x00\x00\x00\xff\x00", b"\xfe\x00\x00\x00\xff\x00")
        wynik = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=a,
                              require_identical_pixels=True)
        assert wynik["metrics"]["idat_sha256"] == P.idat_sha256(b)
        assert wynik["metrics"]["baseline_idat_sha256"] == P.idat_sha256(a)
        assert wynik["metrics"]["idat_sha256"] != wynik["metrics"]["baseline_idat_sha256"]


def test_zadanie_zgodnosci_nie_wskrzesza_porownania_bez_baselinu():
    """Brak baseline'u zostaje statusem `new-baseline`, a nie cichym sukcesem —
    żądanie zgodności co do bajtu nie ma prawa tego obejść.
    """
    with tempfile.TemporaryDirectory() as tmp:
        b = os.path.join(tmp, "b.png")
        _png(b, b"\xff\x00\x00\x00\xff\x00")
        wynik = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=None,
                              require_identical_pixels=True)
        assert wynik["status"] == "new-baseline", wynik
        assert "identical_pixels" not in wynik["checks"]


def test_capture_blender_wpisuje_sume_pikseli_obok_sumy_pliku():
    """Manifest ma nieść OBIE liczby: suma pliku identyfikuje artefakt, suma IDAT
    identyfikuje obraz. Jedna nie zastępuje drugiej.
    """
    zrodlo = os.path.join(ROOT, "tools", "visual", "capture_blender.py")
    with open(zrodlo, encoding="utf-8") as handle:
        tekst = handle.read()
    assert 'record["sha256"] = sha256(path)' in tekst
    assert 'record["idat_sha256"] = idat_sha256(path)' in tekst


def test_narzedzie_sumy_pikseli_jest_wolane_a_nie_przepisane():
    """Dwie implementacje jednej wyroczni to jedna z nich niesprawdzona przez testy
    drugiej. Oba miejsca użycia mają IMPORTOWAĆ `tools/ci/png_pixels_sha256.py`.
    """
    for wzgledna in (("tools", "visual", "capture_blender.py"),
                     ("tools", "visual", "compare.py")):
        with open(os.path.join(ROOT, *wzgledna), encoding="utf-8") as handle:
            tekst = handle.read()
        assert "png_pixels_sha256" in tekst, wzgledna
        assert "def idat_sha256(path):\n    digest" not in tekst, (
            f"{wzgledna}: wygląda na kopię implementacji zamiast wywołania")


def test_bramka_determinizmu_w_skrypcie_zada_zgodnosci_co_do_bajtu():
    """Sam przełącznik nikogo nie chroni, dopóki nikt go nie użyje — a narzędzie
    napisane i niewołane jest tym, co ta pozycja miała naprawić.
    """
    with open(os.path.join(ROOT, "tools", "ci", "visual_smoke.sh"), encoding="utf-8") as handle:
        skrypt = handle.read()
    assert "--require-identical-pixels" in skrypt, (
        "skrypt kontroli wizualnej nie żąda zgodności co do bajtu w teście determinizmu")


def test_json_wyniku_da_sie_zserializowac():
    """Sumy wchodzą do raportu JSON; typ, którego `json` nie umie zapisać, wywróciłby
    bramkę dopiero na CI.
    """
    with tempfile.TemporaryDirectory() as tmp:
        a, b = _para(tmp, b"\xff\x00\x00\x00\xff\x00", b"\xff\x00\x00\x00\xff\x00")
        wynik = C.check_image(b, [2, 1], THRESHOLDS, baseline_path=a,
                              require_identical_pixels=True)
        # `json.dumps` bez asercji przechodzi przez ten test, ale NIE przez bramkę
        # asercji zestawu: test bez ani jednej asercji liczy się w tym projekcie jako
        # awaria, nie sukces. Złapała to kalibracja wyroczni mutacyjnej z #268 —
        # przegląd odmówił liczenia, bo czyste drzewo nie było zielone.
        odczytane = json.loads(json.dumps(wynik))
        assert odczytane["checks"]["identical_pixels"] is True, odczytane
        assert odczytane["metrics"]["idat_sha256"] == wynik["metrics"]["idat_sha256"]

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
