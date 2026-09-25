#!/usr/bin/env python3
"""Sprawdza, czy skomitowane dane nie wyszły poza własne okno ważności.

    python3 tools/track/data_freshness.py
    python3 tools/track/data_freshness.py --strict     # kod wyjścia != 0 dla przeterminowanych

Archiwa STIB niosą własne pola `Date_debut`/`Date_fin`, a INSPIRE `tn:validFrom`/`validTo`.
`data/network/sources.json` ostrzega, że okno **bywa wcześniejsze niż data pobrania** —
i dokładnie tak jest: oś pakietu A powstała z archiwum ważnego do 28.08.2026, pobranego
01.09.2026. To ostrzeżenie siedziało w komentarzu i nikt go nie sprawdzał.

Przeterminowane dane **nie są błędem** i nie wywracają pipeline'u geometrii domyślnie:
sieć metra nie zmienia przebiegu co tydzień, a stary snapshot bywa jedynym dostępnym.
Są natomiast faktem, który ma być widoczny, zanim ktoś nazwie oś „aktualną".
"""
import argparse
import datetime
import json
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))

import tree_walk as TW  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

END_KEYS = ("date_fin", "valid_to", "validTo", "end")
START_KEYS = ("date_debut", "valid_from", "validFrom", "start")
WARN_DAYS = 30


def parse_date(value):
    """Akceptuje DD/MM/RRRR z DBF-a STIB oraz ISO z manifestów provenance."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", text)
    if match:
        day, month, year = (int(g) for g in match.groups())
        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None
    try:
        return datetime.date.fromisoformat(text[:10])
    except ValueError:
        return None


def _dates(value):
    values = value if isinstance(value, list) else [value]
    return [d for d in (parse_date(v) for v in values) if d is not None]


def collect(document, path=""):
    """Zwraca (ścieżka, start, koniec) dla każdego okna ważności w dokumencie."""
    out = []
    if isinstance(document, dict):
        window = {}
        for key, value in document.items():
            if key in START_KEYS:
                window["start"] = _dates(value)
            if key in END_KEYS:
                window["end"] = _dates(value)
        if window.get("end"):
            out.append((path or ".", min(window.get("start") or [None], default=None),
                        max(window["end"])))
        for key, value in document.items():
            out.extend(collect(value, f"{path}.{key}"))
    elif isinstance(document, list):
        for index, value in enumerate(document[:50]):
            out.extend(collect(value, f"{path}[{index}]"))
    return out


def retrieved_at(document):
    if isinstance(document, dict):
        for key in ("retrieved_at", "checked_at"):
            if key in document:
                found = parse_date(document[key])
                if found:
                    return found
        for value in document.values():
            found = retrieved_at(value)
            if found:
                return found
    return None


def audit(paths, today, root=ROOT):
    rows = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
        got = retrieved_at(document)
        seen = set()
        for where, start, end in collect(document):
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            days = (end - today).days
            rows.append({
                "file": os.path.relpath(path, root).replace(os.sep, "/"),
                "where": where,
                "valid_from": start.isoformat() if start else None,
                "valid_to": end.isoformat(),
                "retrieved_at": got.isoformat() if got else None,
                "days_left": days,
                "status": "przeterminowane" if days < 0
                          else ("kończy się" if days <= WARN_DAYS else "aktualne"),
                # Sedno ostrzeżenia z sources.json: archiwum bywa nieważne już w chwili pobrania.
                "retrieved_after_expiry": bool(got and got > end),
            })
    return rows


def data_files(root):
    out = []
    for base, _dirs, names in TW.walk(os.path.join(root, "data"), root):
        for name in sorted(names):
            if name.endswith(".json") and not name.endswith(".schema.json"):
                out.append(os.path.join(base, name))
    return sorted(out)


def known_expired(path):
    """Read an explicit, exact exception list for legacy expired windows."""
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    windows = document.get("windows") if isinstance(document, dict) else None
    if not isinstance(windows, list):
        raise ValueError("baseline must contain a windows list")
    keys = set()
    for row in windows:
        if not isinstance(row, dict) or set(row) != {"file", "valid_to", "retrieved_at"}:
            raise ValueError("baseline row must have file, valid_to and retrieved_at")
        if not isinstance(row["file"], str) or not row["file"].startswith("data/") \
                or "\\" in row["file"] or ".." in row["file"].split("/") \
                or not parse_date(row["valid_to"]) or not parse_date(row["retrieved_at"]):
            raise ValueError("invalid baseline row")
        key = (row["file"], row["valid_to"], row["retrieved_at"])
        if key in keys:
            raise ValueError(f"duplicate baseline row: {key}")
        keys.add(key)
    return keys


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kontrola świeżości skomitowanych danych")
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--today", help="data odniesienia RRRR-MM-DD; domyślnie dziś")
    parser.add_argument("--out", help="ścieżka na wynik JSON")
    parser.add_argument("--strict", action="store_true",
                        help="kod wyjścia != 0, gdy cokolwiek jest przeterminowane")
    parser.add_argument("--baseline", help="jawne znane wyjątki dla --strict (JSON)")
    args = parser.parse_args(argv)

    today = parse_date(args.today) if args.today else datetime.date.today()
    rows = audit(data_files(args.root), today, args.root)

    if not rows:
        print("[ŚWIEŻOŚĆ] żaden skomitowany plik nie deklaruje okna ważności")
    for row in sorted(rows, key=lambda r: r["days_left"]):
        marker = {"przeterminowane": "!", "kończy się": "~", "aktualne": " "}[row["status"]]
        print(f"[ŚWIEŻOŚĆ] {marker} {row['file']}: ważne do {row['valid_to']} "
              f"({row['days_left']:+d} dni), pobrane {row['retrieved_at']}"
              + (" — POBRANE PO WYGAŚNIĘCIU" if row["retrieved_after_expiry"] else ""))

    expired = [r for r in rows if r["status"] == "przeterminowane"]
    if expired:
        print(f"[ŚWIEŻOŚĆ] przeterminowanych okien: {len(expired)}. "
              "To nie jest błąd sam w sobie — sieć metra nie zmienia przebiegu co tydzień — "
              "ale oś zbudowana z takiego archiwum nie może być nazywana aktualną.")

    if args.out:
        target = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump({"today": today.isoformat(), "rows": rows}, handle,
                      ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"[RAPORT] {args.out}")

    if args.baseline and not args.strict:
        parser.error("--baseline wymaga --strict")
    if args.strict:
        baseline = known_expired(args.baseline) if args.baseline else set()
        observed = {(r["file"], r["valid_to"], r["retrieved_at"]) for r in expired}
        unexpected = observed - baseline
        obsolete = baseline - observed
        if unexpected or obsolete:
            raise SystemExit(
                f"BŁĄD: nowych przeterminowanych okien ważności: {len(unexpected)}, "
                f"nieaktualnych wyjątków: {len(obsolete)}; "
                f"nowe={sorted(unexpected)}, nieaktualne={sorted(obsolete)}")
        if baseline:
            print(f"[ŚWIEŻOŚĆ] {len(baseline)} znanych wygasłych okien w jawnej "
                  "baseline; nowe wygasłe okno albo nieaktualny wyjątek zatrzyma CI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
