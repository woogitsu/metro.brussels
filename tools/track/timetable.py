#!/usr/bin/env python3
"""Rozkład jazdy metra z oficjalnego GTFS STIB/MIVB — takty, pierwsze i ostatnie kursy,
czasy przejazdu między stacjami.

    python3 tools/track/timetable.py --gtfs build/gtfs/stib_gtfs.zip \
        --out build/timetable.json --date 2026-09-02

To jest **pomiar rozkładu**, nie model ruchu. Odpowiada na pytania, na które T-320
(wiele składów naraz) nie da się odpowiedzieć bez danych: ile składów jest na linii
w szczycie, co ile odjeżdżają, o której zaczyna się i kończy służba i ile STIB
przewiduje na przejazd między dwiema stacjami.

**Czas rozkładowy to nie czas jazdy** — zawiera postój i rezerwę. Ale postój DA SIĘ
wyodrębnić, wbrew temu, czego się spodziewałem: feed STIB podaje na metrze
`arrival_time != departure_time` na **każdym** zatrzymaniu pośrednim, więc
`departure - arrival` jest **rozkładowym czasem postoju**, a
`arrival(następna) - departure(ta)` rozkładowym czasem jazdy. Narzędzie liczy obie
wielkości osobno i tak je raportuje.

Postój liczy się **wyłącznie na zatrzymaniach pośrednich**. Kraniec kursu ma
`arrival == departure` z definicji i nie jest postojem zerowym, tylko brakiem postoju
w tym kursie; wliczony do rozkładu zaniża udział postojów niezerowych ze 100 % do 94 %.
Krańce raportowane są osobno, a nie wyrzucane po cichu.

Rezerwy z czasu jazdy nadal nie da się wyodrębnić — rozkład nie mówi, ile z niego
jest jazdą, a ile zapasem. Porównanie z fizyką (T-310/T-311) jest więc porównaniem
„czas rozkładowy wobec czas jazdy", w którym **rozkład jest górnym ograniczeniem**.

GTFS dopuszcza godziny > 24:00:00 dla kursów po północy; parser to zachowuje, bo
inaczej ostatnie kursy wypadałyby z doby i takt nocny wychodziłby fałszywie rzadki.
"""
import argparse
import csv
import io
import json
import os
import statistics
import sys
import zipfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import provenance as P  # noqa: E402

# route_type 1 = metro (GTFS Reference). Nie filtrujemy po nazwie linii, bo nazwa
# jest tekstem redakcyjnym, a typ jest polem znormalizowanym.
METRO_ROUTE_TYPE = "1"
# Godziny, w których liczymy takt szczytu. Zakres z rozkładu STIB dla dnia roboczego;
# jest to okno POMIARU, nie twierdzenie o tym, kiedy STIB ma szczyt.
PEAK_HOURS = (7, 8, 16, 17)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Rozkład jazdy metra z GTFS STIB")
    parser.add_argument("--gtfs", default=os.path.join("build", "gtfs", "stib_gtfs.zip"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--date", help="dzień w formacie YYYY-MM-DD; domyślnie pierwszy dzień feedu")
    parser.add_argument("--peak-hours", default=",".join(str(h) for h in PEAK_HOURS))
    parser.add_argument("--axis", action="append", default=None,
                        help="oś pakietu z data/track/*.json; można podać wielokrotnie. "
                             "Łączy odcinki rozkładowe z chainage po stop_id.")
    return parser.parse_args(argv)


def read_table(archive, name):
    with archive.open(name) as handle:
        yield from csv.DictReader(io.TextIOWrapper(handle, "utf-8-sig"))


def parse_time(text):
    """Sekundy od północy. GTFS dopuszcza 25:14:00 dla kursów po północy."""
    parts = text.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None


def clock(seconds):
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def weekday_column(date_text):
    """Kolumna calendar.txt dla daty. Bez `datetime.strptime` na wejściu z pliku."""
    import datetime
    day = datetime.date(int(date_text[0:4]), int(date_text[4:6]), int(date_text[6:8]))
    return ("monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday")[day.weekday()]


def services_on(archive, date_text):
    """Identyfikatory służb kursujących danego dnia, z uwzględnieniem wyjątków.

    `calendar_dates.txt` **musi** być uwzględniony: STIB ma 571 wyjątków przy 338
    służbach, więc sam `calendar.txt` dałby rozkład, którego danego dnia nie ma.
    """
    column = weekday_column(date_text)
    active = set()
    for row in read_table(archive, "calendar.txt"):
        if row["start_date"] <= date_text <= row["end_date"] and row[column] == "1":
            active.add(row["service_id"])
    added, removed = set(), set()
    for row in read_table(archive, "calendar_dates.txt"):
        if row["date"] != date_text:
            continue
        (added if row["exception_type"] == "1" else removed).add(row["service_id"])
    return (active | added) - removed, len(added), len(removed)


def metro_routes(archive):
    return {row["route_id"]: row for row in read_table(archive, "routes.txt")
            if row.get("route_type") == METRO_ROUTE_TYPE}


def headways(departures):
    """Odstępy między kolejnymi odjazdami, w sekundach."""
    ordered = sorted(departures)
    return [b - a for a, b in zip(ordered, ordered[1:])]


def summarise_headways(gaps):
    if not gaps:
        return None
    ordered = sorted(gaps)
    return {
        "count": len(ordered),
        "min_s": ordered[0],
        "median_s": ordered[len(ordered) // 2],
        "p90_s": ordered[int(0.9 * (len(ordered) - 1))],
        "max_s": ordered[-1],
        "mode_s": Counter(ordered).most_common(1)[0][0],
    }


def stop_names(archive):
    """id -> nazwa peronu. Bez tego odcinki są parami liczb i nie da się ich zestawić
    z `data/network/lines.json` ani z osią z T-210."""
    return {row["stop_id"]: row.get("stop_name", "") for row in read_table(archive, "stops.txt")}


def axis_chainage(paths):
    """stop_id -> (pakiet, chainage_m) z osi T-210.

    Klucz jest ten sam `stop_id`, którym GTFS opisuje peron, bo `tools/track/normalize_stops.py`
    wpisał go do osi z tego samego feedu. Dlatego to jest złączenie po identyfikatorze,
    a nie po nazwie — nazwy różnią się wielkością liter i wariantem językowym.
    """
    table = {}
    for path in paths or ():
        full = path if os.path.isabs(path) else os.path.join(ROOT, path)
        with open(full, encoding="utf-8") as handle:
            axis = json.load(handle)
        for station in axis.get("stations", []):
            stop = station.get("stop_id")
            if stop:
                table.setdefault(stop, []).append((axis["id"], float(station["chainage_m"])))
    return table


def segment_distance(table, a_stop, b_stop):
    """Odległość wzdłuż osi, ale **tylko wewnątrz jednego pakietu**.

    Para stacji rozdzielona między dwa pakiety nie dostaje odległości: chainage każdego
    pakietu liczy się od jego własnego zera, więc odejmowanie ich od siebie dałoby liczbę
    wyglądającą jak metry i nie będącą metrami. Ciągłość chainage między pakietami
    zamyka T-112, nie to zadanie.
    """
    for a_axis, a_chain in table.get(a_stop, ()):
        for b_axis, b_chain in table.get(b_stop, ()):
            if a_axis == b_axis:
                return a_axis, round(abs(b_chain - a_chain), 2)
    return None, None


def peak_concurrency(intervals):
    """Największa liczba kursów jednocześnie w ruchu i chwila, w której to zachodzi.

    Jest to **dolne ograniczenie liczby składów w ruchu**, nie liczba składów: rozkład
    nie mówi, czy kurs kończący się o 08:12 na krańcu jest tym samym pojazdem, co kurs
    zaczynający się tam o 08:16. Obrót na krańcu i rezerwa dokładają do floty i nie
    wychodzą z rozkładu.
    """
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort()
    best = current = 0
    at = None
    for moment, delta in events:
        current += delta
        if current > best:
            best, at = current, moment
    return best, at


def block_summary(blocks):
    """Obiegi pojazdów z `block_id`: ile pojazdów, ile kursów każdy, jak długo w służbie.

    W GTFS `block_id` wiąże kursy wykonywane **tym samym pojazdem po kolei**. Feed STIB
    ma go wypełniony dla metra, więc liczba różnych bloków jest liczbą obiegów, a nie
    oszacowaniem. Nadal nie jest to wielkość floty: obiegi tego samego dnia to pojazdy
    w ruchu, bez rezerwy i bez naprawy.

    Kursy w jednym bloku nie mogą się nakładać w czasie — jeden pojazd nie jedzie dwoma
    kursami naraz. Nakładka oznacza błąd w feedzie i jest raportowana, a nie milczana.
    """
    rows = []
    overlaps = 0
    for block, trips in sorted(blocks.items()):
        ordered = sorted(trips)
        for (_s1, end), (start, _e2) in zip(ordered, ordered[1:]):
            if start < end:
                overlaps += 1
        rows.append({
            "block_id": block,
            "trips": len(ordered),
            "first_departure": clock(ordered[0][0]),
            "last_arrival": clock(max(end for _s, end in ordered)),
            "span_s": max(end for _s, end in ordered) - ordered[0][0],
            # Okna kursów, sekundy od północy. DLACZEGO SUROWE SEKUNDY, A NIE `clock`:
            # doba służby wychodzi poza 24:00 (ostatni przyjazd bywa o 24:36:14),
            # a `clock` to zapisuje tekstem, którego żaden parser czasu nie przyjmie
            # bez wiedzy o tej konwencji. Sekundy przenoszą tę samą informację bez
            # konwencji do zgubienia.
            #
            # DLACZEGO W OGÓLE SĄ W PLIKU. Pole `overlapping_trips_in_a_block` mówi,
            # czy kursy jednego obiegu się nakładają — ale mówi to SŁOWEM narzędzia,
            # które samo je policzyło. Bez okien kursów rdzeń nie ma z czego policzyć
            # tego drugi raz, więc porównanie dwóch stron sprowadzałoby się do
            # przepisania liczby Pythona do C#. Pozycja 6.A3 żąda czegoś odwrotnego:
            # żeby obie strony miały czym się różnić.
            "trip_windows": [[start, end] for start, end in ordered],
        })
    concurrent, at = peak_concurrency(
        [(row_trips[0][0], max(end for _s, end in row_trips))
         for row_trips in (sorted(v) for v in blocks.values())])
    spans = sorted(row["span_s"] for row in rows)
    return {
        "blocks": len(rows),
        "overlapping_trips_in_a_block": overlaps,
        "max_concurrent_blocks": concurrent,
        "max_concurrent_blocks_at": clock(at) if at is not None else None,
        "trips_per_block": dict(sorted(Counter(row["trips"] for row in rows).items())),
        "span_min_s": spans[0] if spans else None,
        "span_median_s": spans[len(spans) // 2] if spans else None,
        "span_max_s": spans[-1] if spans else None,
        "rows": rows,
    }


def survey(archive, date_text, peak_hours, axis_paths=None):
    routes = metro_routes(archive)
    names = stop_names(archive)
    chainage = axis_chainage(axis_paths)
    active, added, removed = services_on(archive, date_text)

    trips = {}
    for row in read_table(archive, "trips.txt"):
        if row["route_id"] in routes and row["service_id"] in active:
            trips[row["trip_id"]] = row

    # Jedno przejście po 1,5 mln wierszy; trzymamy tylko to, co dotyczy metra.
    per_trip = defaultdict(list)
    dwells = defaultdict(list)
    for row in read_table(archive, "stop_times.txt"):
        trip = row["trip_id"]
        if trip not in trips:
            continue
        departure = parse_time(row["departure_time"])
        arrival = parse_time(row["arrival_time"])
        if departure is None or arrival is None:
            continue
        per_trip[trip].append((int(row["stop_sequence"]), row["stop_id"], arrival, departure))

    lines = {}
    segments = defaultdict(list)
    blocks = defaultdict(list)
    trip_records = []
    terminus_stops = Counter()
    terminus_non_zero = Counter()
    dwell_written = 0
    for trip_id, stops in per_trip.items():
        stops.sort()
        route = trips[trip_id]["route_id"]
        direction = trips[trip_id].get("direction_id", "")
        trip_records.append({
            "trip_id": trip_id,
            "block_id": trips[trip_id].get("block_id") or "",
            "route_id": route,
            "direction_id": direction,
            "stops": [
                {"stop_sequence": sequence, "stop_id": stop_id,
                 "arrival_s": arrival, "departure_s": departure}
                for sequence, stop_id, arrival, departure in stops
            ],
        })
        key = (route, direction)
        entry = lines.setdefault(key, {"departures": [], "trips": 0, "stops_per_trip": Counter(),
                                       "intervals": []})
        entry["departures"].append(stops[0][3])
        entry["intervals"].append((stops[0][3], stops[-1][2]))
        block = trips[trip_id].get("block_id") or ""
        if block:
            blocks[block].append((stops[0][3], stops[-1][2]))
        entry["trips"] += 1
        entry["stops_per_trip"][len(stops)] += 1
        for (_s1, a_stop, _a_arr, a_dep), (_s2, b_stop, b_arr, _b_dep) in zip(stops, stops[1:]):
            segments[(route, direction, a_stop, b_stop)].append(b_arr - a_dep)
        # Postój liczymy **tylko na zatrzymaniach pośrednich**. Kraniec kursu ma w GTFS
        # arrival == departure z definicji (kurs się tam kończy albo zaczyna), więc
        # wliczenie krańców rozcieńcza rozkład postoju zerami, które nie są postojem
        # zerowym, tylko brakiem postoju w tym kursie.
        for _sequence, _stop, arrival, departure in stops[1:-1]:
            dwells[key].append(departure - arrival)
        terminus_stops[key] += min(2, len(stops))
        terminus_non_zero[key] += sum(
            1 for _s, _i, arr, dep in (stops[:1] + stops[-1:]) if dep != arr)
        dwell_written += sum(1 for _s, _i, arr, dep in stops if dep != arr)

    rows = []
    for (route, direction), entry in sorted(lines.items()):
        gaps = headways(entry["departures"])
        concurrent, concurrent_at = peak_concurrency(entry["intervals"])
        peak = [b - a for a, b in zip(sorted(entry["departures"]), sorted(entry["departures"])[1:])
                if (a // 3600) % 24 in peak_hours]
        rows.append({
            "route_id": route,
            "line": routes[route].get("route_short_name"),
            "name": routes[route].get("route_long_name"),
            "direction_id": direction,
            "trips": entry["trips"],
            "first_departure": clock(min(entry["departures"])),
            "last_departure": clock(max(entry["departures"])),
            "service_span_s": max(entry["departures"]) - min(entry["departures"]),
            "stops_per_trip": dict(sorted(entry["stops_per_trip"].items())),
            "headway_all": summarise_headways(gaps),
            "headway_peak": summarise_headways(peak),
            "max_concurrent_trips": concurrent,
            "max_concurrent_at": clock(concurrent_at) if concurrent_at is not None else None,
        })

    dwell_rows = []
    for (route, direction), values in sorted(dwells.items()):
        ordered = sorted(values)
        non_zero = [v for v in ordered if v > 0]
        dwell_rows.append({
            "route_id": route, "direction_id": direction,
            "line": routes[route].get("route_short_name"),
            "stops": len(ordered),
            "non_zero": len(non_zero),
            "non_zero_pct": round(100.0 * len(non_zero) / max(1, len(ordered)), 1),
            "terminus_stops": terminus_stops[(route, direction)],
            "terminus_non_zero": terminus_non_zero[(route, direction)],
            "min_non_zero_s": non_zero[0] if non_zero else None,
            "median_non_zero_s": non_zero[len(non_zero) // 2] if non_zero else None,
            "max_s": ordered[-1],
        })

    segment_rows = []
    matched = 0
    for (route, direction, a_stop, b_stop), values in sorted(segments.items()):
        ordered = sorted(values)
        package, distance = segment_distance(chainage, a_stop, b_stop)
        row = {
            "route_id": route, "line": routes[route].get("route_short_name"),
            "direction_id": direction,
            "from_stop": a_stop, "to_stop": b_stop,
            "from_name": names.get(a_stop, ""), "to_name": names.get(b_stop, ""),
            "samples": len(ordered),
            "min_s": ordered[0],
            "median_s": ordered[len(ordered) // 2],
            "max_s": ordered[-1],
            "mean_s": round(statistics.fmean(ordered), 2),
        }
        if distance is not None:
            matched += 1
            # Prędkość średnia rozkładowa. Skoro czas rozkładowy jest GÓRNYM ograniczeniem
            # czasu jazdy, ta prędkość jest DOLNYM ograniczeniem prędkości jazdy — i o tyle
            # samo jest niższa od prędkości maksymalnej, ile rozkład ma rezerwy.
            row["package"] = package
            row["distance_m"] = distance
            row["mean_speed_kmh"] = round(3.6 * distance / ordered[len(ordered) // 2], 2)
        segment_rows.append(row)

    return {
        "checked_at": P.utc_now_iso(),
        "date": date_text,
        "weekday": weekday_column(date_text),
        "services_active": len(active),
        "calendar_dates_added": added,
        "calendar_dates_removed": removed,
        "metro_routes": {rid: r.get("route_short_name") for rid, r in sorted(routes.items())},
        "metro_trips": len(trips),
        # Wierna projekcja kursów na aktywny dzień. Agregaty `duties` i `segments`
        # gubią powiązanie kurs → kierunek → godzina na stacji; LineCore nie może
        # odtworzyć wejścia na oś z samych okien całych kursów.
        "trip_records": sorted(trip_records, key=lambda row: row["trip_id"]),
        "peak_hours": sorted(peak_hours),
        "lines": rows,
        "duties": block_summary(blocks),
        "max_concurrent_trips": peak_concurrency(
            [i for entry in lines.values() for i in entry["intervals"]])[0],
        "dwell": dwell_rows,
        "dwell_histogram_s": dict(sorted(Counter(
            value for values in dwells.values() for value in values).items())),
        "segments": segment_rows,
        "segments_with_distance": matched,
        "axis_files": sorted(axis_paths or ()),
        "stop_times_with_dwell": dwell_written,
        "terminus_stops": sum(terminus_stops.values()),
        "terminus_non_zero": sum(terminus_non_zero.values()),
        "note": ("Postój rozkładowy = departure - arrival, liczony wyłącznie na "
                 "zatrzymaniach POŚREDNICH; w feedzie STIB jest niezerowy "
                 f"w {dwell_written} zatrzymaniach metra tego dnia, czyli da się go "
                 "wyodrębnić. Kraniec kursu ma arrival == departure z definicji i nie "
                 "jest postojem zerowym, tylko brakiem postoju w tym kursie. "
                 "Czas jazdy = arrival(następna) - departure(ta) i zawiera "
                 "rezerwę, której z rozkładu wyodrębnić się NIE da — jest więc górnym "
                 "ograniczeniem czasu jazdy, a nie jego pomiarem."),
    }


def main(argv=None):
    args = parse_args(argv)
    path = args.gtfs if os.path.isabs(args.gtfs) else os.path.join(ROOT, args.gtfs)
    if not zipfile.is_zipfile(path):
        raise SystemExit(f"BŁĄD: {path} nie jest archiwum ZIP — pobierz feed "
                         "przez tools/track/fetch_gtfs.py")
    peak = {int(h) for h in args.peak_hours.split(",") if h.strip()}
    with zipfile.ZipFile(path) as archive:
        date_text = (args.date or "").replace("-", "")
        if not date_text:
            feed = next(read_table(archive, "feed_info.txt"), {})
            date_text = feed.get("feed_start_date", "")
            if not date_text:
                raise SystemExit("BŁĄD: brak --date, a feed_info.txt nie podaje daty startu")
        report = survey(archive, date_text, peak, args.axis)

    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    print(f"[ROZKŁAD] {report['date']} ({report['weekday']}): "
          f"{report['services_active']} kalendarzy kursowania "
          f"(+{report['calendar_dates_added']} / -{report['calendar_dates_removed']} z wyjątków), "
          f"{report['metro_trips']} kursów metra")
    for row in report["lines"]:
        peak_row = row["headway_peak"]
        print(f"[ROZKŁAD] linia {row['line']} kier. {row['direction_id']}: {row['trips']:4d} kursów, "
              f"{row['first_departure']}–{row['last_departure']}, "
              f"takt mediana {row['headway_all']['median_s'] // 60}:{row['headway_all']['median_s'] % 60:02d}"
              + (f", szczyt {peak_row['median_s'] // 60}:{peak_row['median_s'] % 60:02d}" if peak_row else "")
              + f", naraz {row['max_concurrent_trips']} kursów o {row['max_concurrent_at']}")
    duties = report["duties"]
    print(f"[SŁUŻBY] najwięcej kursów naraz w całym metrze: {report['max_concurrent_trips']} "
          "— tyle składów jest w danej chwili w ruchu")
    if duties["blocks"]:
        print(f"[SŁUŻBY] obiegów pojazdów (block_id): {duties['blocks']}, "
              f"naraz w służbie {duties['max_concurrent_blocks']} o "
              f"{duties['max_concurrent_blocks_at']}, kursów na obieg "
              f"{min(duties['trips_per_block'])}–{max(duties['trips_per_block'])}, "
              f"czas w służbie mediana {duties['span_median_s'] // 3600} h "
              f"{(duties['span_median_s'] % 3600) // 60} min")
        if duties["overlapping_trips_in_a_block"]:
            print(f"[SŁUŻBY] UWAGA: {duties['overlapping_trips_in_a_block']} par kursów w tym "
                  "samym obiegu nakłada się w czasie — jeden pojazd nie jedzie dwoma naraz")
    else:
        print("[SŁUŻBY] feed nie ma block_id dla metra — obiegów pojazdów nie da się odczytać")
    print(f"[ROZKŁAD] odcinków międzystacyjnych: {len(report['segments'])}, "
          f"z odległością wzdłuż osi: {report['segments_with_distance']}")
    for row in report["segments"]:
        if "distance_m" in row:
            print(f"[ODCINEK] {row['package']} linia {row['line']} kier. {row['direction_id']}: "
                  f"{row['from_name']} → {row['to_name']}: "
                  f"{row['distance_m']:.0f} m w {row['median_s']} s = {row['mean_speed_kmh']:.1f} km/h")
    for row in report["dwell"]:
        print(f"[POSTÓJ] linia {row['line']} kier. {row['direction_id']}: pośrednich "
              f"{row['non_zero']}/{row['stops']} niezerowych ({row['non_zero_pct']} %), "
              f"min {row['min_non_zero_s']} s, mediana {row['median_non_zero_s']} s, "
              f"maks {row['max_s']} s")
    print(f"[ROZKŁAD] zapisano {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
