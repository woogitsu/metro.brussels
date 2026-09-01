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


def audit(paths, today):
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
                "file": os.path.relpath(path, ROOT),
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
    for base, _dirs, names in os.walk(os.path.join(root, "data")):
        for name in sorted(names):
            if name.endswith(".json") and not name.endswith(".schema.json"):
                out.append(os.path.join(base, name))
    return sorted(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kontrola świeżości skomitowanych danych")
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--today", help="data odniesienia RRRR-MM-DD; domyślnie dziś")
    parser.add_argument("--out", help="ścieżka na wynik JSON")
    parser.add_argument("--strict", action="store_true",
                        help="kod wyjścia != 0, gdy cokolwiek jest przeterminowane")
    args = parser.parse_args(argv)

    today = parse_date(args.today) if args.today else datetime.date.today()
    rows = audit(data_files(args.root), today)

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

    if args.strict and expired:
        raise SystemExit(f"BŁĄD: {len(expired)} okien ważności minęło")
    return 0


if __name__ == "__main__":
    sys.exit(main())
