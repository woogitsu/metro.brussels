#!/usr/bin/env python3
"""Testy klasyfikacji „w tunelu / poza tunelem". Bez sieci i bez pytest.

Wszystkie dane wejściowe są budowane w locie: OSM jako mały dokument XML, UrbIS jako
prostokąt. Test sprawdza logikę rozstrzygania, a nie dostępność serwisów.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import surface_sections as SS  # noqa: E402


def _osm(ways):
    """Dokument OSM z jednym węzłem na metr wzdłuż zadanych odcinków w WGS84."""
    nodes, body = [], []
    node_id = 1
    for way_id, coords, tags in ways:
        refs = []
        for lon, lat in coords:
            nodes.append(f'<node id="{node_id}" lon="{lon}" lat="{lat}"/>')
            refs.append(f'<nd ref="{node_id}"/>')
            node_id += 1
        tag_xml = "".join(f'<tag k="{k}" v="{v}"/>' for k, v in tags.items())
        body.append(f'<way id="{way_id}">{"".join(refs)}{tag_xml}</way>')
    return ("<osm version=\"0.6\">" + "".join(nodes) + "".join(body) + "</osm>").encode("utf-8")


# --- rozstrzyganie ------------------------------------------------------------

def test_surface_classify_agrees_when_both_sources_say_tunnel():
    verdict, urbis, osm = SS.classify({"niveau": "-"}, {"tunnel": "yes", "distance_m": 3.0})
    assert (verdict, urbis, osm) == ("zgodne", "tunel", "tunel")


def test_surface_classify_agrees_when_both_sources_say_surface():
    verdict, urbis, osm = SS.classify({"niveau": "0"}, {"tunnel": None, "distance_m": 3.0})
    assert (verdict, urbis, osm) == ("zgodne", "poza_tunelem", "poza_tunelem")


def test_surface_classify_reports_a_contradiction_instead_of_picking_a_side():
    """Rozbieżność jest wynikiem. Uśrednianie dwóch źródeł nie ma tu sensu."""
    verdict, urbis, osm = SS.classify({"niveau": "0"}, {"tunnel": "yes", "distance_m": 1.0})
    assert verdict == "sprzeczne" and urbis == "poza_tunelem" and osm == "tunel"


def test_surface_classify_ignores_an_osm_way_that_is_too_far():
    """Way sto metrów od osi opisuje inną linię, nie ten odcinek."""
    verdict, _urbis, osm = SS.classify({"niveau": "-"},
                                       {"tunnel": "yes", "distance_m": SS.NEAREST_MAX_M + 1.0})
    assert verdict == "jedno_zrodlo" and osm is None


def test_surface_classify_treats_covered_as_tunnel():
    _verdict, _urbis, osm = SS.classify(None, {"tunnel": "covered", "distance_m": 1.0})
    assert osm == "tunel"


def test_surface_classify_returns_unknown_when_neither_source_speaks():
    assert SS.classify(None, None)[0] == "nieznane"


# --- najbliższy way -----------------------------------------------------------

def test_surface_nearest_subway_picks_the_closest_way_not_the_first():
    """W węźle przesiadkowym w jednym kwadracie leży kilka linii na różnych poziomach."""
    import crs as CRS
    near = CRS.lambert72_to_wgs84(150000.0, 170000.0)
    far = CRS.lambert72_to_wgs84(150000.0, 170200.0)
    payload = _osm([
        ("far", [(far[0], far[1]), (far[0] + 0.002, far[1])],
         {"railway": "subway", "tunnel": "yes", "layer": "-3"}),
        ("near", [(near[0], near[1]), (near[0] + 0.002, near[1])],
         {"railway": "subway"}),
    ])
    best = SS.nearest_subway(payload, (150000.0, 170000.0))
    assert best["way_id"] == "near", best
    assert best["tunnel"] is None
    assert best["distance_m"] < 1.0


def test_surface_nearest_subway_ignores_other_railways():
    import crs as CRS
    lon, lat = CRS.lambert72_to_wgs84(150000.0, 170000.0)
    payload = _osm([("tram", [(lon, lat), (lon + 0.002, lat)], {"railway": "tram"})])
    assert SS.nearest_subway(payload, (150000.0, 170000.0)) is None


# --- rozmieszczenie sond ------------------------------------------------------

def test_surface_probe_chainages_always_hits_the_middle_of_every_range():
    """Regresja: bez tego wszystkie sondy przedziałów lądowały tuż za portalem."""
    chain = [float(i) for i in range(0, 3001, 10)]
    inside = [700.0 <= c <= 900.0 for c in chain]
    picks = SS.probe_chainages(chain, inside, 300.0, 800.0, [[700.0, 900.0]])
    assert any(abs(c - 800.0) < 1e-6 for c, _flag in picks), picks


def test_surface_probe_chainages_marks_portal_neighbourhood_separately():
    ranges = [[700.0, 900.0]]
    assert SS.range_position(800.0, ranges) == "srodek"
    assert SS.range_position(710.0, ranges) == "portal"
    assert SS.range_position(880.0, ranges) == "portal"
    assert SS.range_position(300.0, ranges) == "poza"


def test_surface_probe_chainages_are_sorted_and_unique():
    chain = [float(i) for i in range(0, 5001, 10)]
    inside = [1000.0 <= c <= 1400.0 for c in chain]
    picks = SS.probe_chainages(chain, inside, 300.0, 800.0, [[1000.0, 1400.0]])
    values = [c for c, _flag in picks]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


# --- progi range_position, dokładnie na granicy --------------------------------

def test_surface_range_position_hits_the_halo_boundary_exactly():
    """Sonda dokładnie `halo` od portalu ma być „portal", nie „poza" i nie „środek".

    Trzy progi w `range_position` są napisane przez `<=`, więc jedynym wejściem,
    które odróżnia je od `<`, jest wartość DOKŁADNIE równa progowi. Test dobiera
    liczby tak, żeby różnica była dokładna także w zmiennoprzecinkowym: 700, 900,
    60 i ich sumy są liczbami całkowitymi, więc `700.0 - 60.0` daje równo `640.0`,
    a `abs(760.0 - 700.0)` równo `60.0`. Gdyby próg wypadał na wartości typu
    `6700.0 + 0.01`, odejmowanie dałoby `0.010000000000218`, czyli NAD progiem,
    i test nigdy nie dotknąłby granicy, którą rzekomo sprawdza.
    """
    ranges = [[700.0, 900.0]]
    halo = SS.PORTAL_HALO_M
    assert halo == 60.0, halo
    assert 700.0 - halo == 640.0 and 900.0 + halo == 960.0
    assert abs(760.0 - 700.0) == halo and abs(840.0 - 900.0) == halo

    # zewnętrzna granica halo — wchodzi do przedziału i jest portalem
    assert SS.range_position(640.0, ranges) == "portal"
    assert SS.range_position(960.0, ranges) == "portal"
    # kontrola negatywna: o metr dalej jest już poza przedziałem
    assert SS.range_position(639.0, ranges) == "poza"
    assert SS.range_position(961.0, ranges) == "poza"

    # wewnętrzna granica halo — jeszcze portal, metr dalej już środek
    assert SS.range_position(760.0, ranges) == "portal"
    assert SS.range_position(840.0, ranges) == "portal"
    assert SS.range_position(761.0, ranges) == "srodek"
    assert SS.range_position(839.0, ranges) == "srodek"


# --- progi kroku sond, dokładnie na granicy ------------------------------------

def test_surface_probe_step_fires_at_a_distance_exactly_equal_to_the_step():
    """Sonda ma padać, gdy odległość od poprzedniej równa się KROKOWI, nie dopiero powyżej.

    Warunek jest napisany przez `>=`; różnicę z `>` widać wyłącznie na wejściu,
    w którym `value - reference` wynosi dokładnie tyle, co krok. Kilometraże są
    wielokrotnościami stu metrów, więc odejmowanie jest dokładne i sondy padają
    równo co 300 m. Przy `>` pierwsza sonda po zerze wypadłaby na 400 m.
    """
    chain = [i * 100.0 for i in range(31)]
    picks = [c for c, _flag in SS.probe_chainages(chain, [True] * 31, 300.0, 800.0)]
    assert picks[:4] == [0.0, 300.0, 600.0, 900.0], picks
    # kontrola negatywna: krok o metr większy niż siatka przesuwa sondy o jeden punkt
    shifted = [c for c, _flag in SS.probe_chainages(chain, [True] * 31, 301.0, 800.0)]
    assert shifted[:4] == [0.0, 400.0, 800.0, 1200.0], shifted


def test_surface_probe_outside_step_fires_at_its_own_exact_boundary():
    """Drugi warunek kroku (`>= step_outside_m`) też ma granicę i też ją sprawdzamy.

    Oba warunki w `probe_chainages` są identyczne dla punktów POZA przedziałem,
    więc tam mutacja jednego z nich nie zmienia niczego — drugi i tak strzela.
    Rozdziela je dopiero wejście, w którym punkt jest W przedziale, a krok
    wewnętrzny jest większy od zewnętrznego: wtedy o sondzie decyduje wyłącznie
    `value - last_any >= step_outside_m`. Argumenty `--step-inside-m`
    i `--step-outside-m` są wolnymi parametrami CLI, więc to wejście osiągalne.
    """
    chain = [i * 100.0 for i in range(31)]
    flags = [False] + [True] * 30
    picks = [c for c, _flag in SS.probe_chainages(chain, flags, 1000.0, 200.0)]
    assert picks[:5] == [0.0, 100.0, 300.0, 500.0, 700.0], picks
    # kontrola negatywna: krok zewnętrzny o metr większy przesuwa co drugą sondę
    shifted = [c for c, _flag in SS.probe_chainages(chain, flags, 1000.0, 201.0)]
    assert shifted[:5] == [0.0, 100.0, 400.0, 700.0, 1000.0], shifted


def test_surface_probe_middle_tolerance_is_measured_at_the_tolerance_itself():
    """Środek przedziału dokładnie 1e-6 od istniejącej sondy uchodzi za już pokryty.

    PUŁAPKA ZMIENNOPRZECINKOWA i sposób jej obejścia: `abs(a - b)` jest dokładne
    tylko wtedy, gdy jedna strona jest zerem albo gdy liczby są bliskimi sobie
    potęgami dwójki. Dlatego przedział to `[-1.0, 1.0]`, którego środek wynosi
    równo `0.0`, a jedyna sonda leży na `1e-6`: różnica `abs(0.0 - 1e-6)` jest
    wtedy bitowo równa literałowi `1e-6` z modułu. Naiwne „sonda na 1.000001
    obok środka 1.0" dałoby 1.0000000000287557e-06, czyli NAD progiem.
    """
    ranges = [[-1.0, 1.0]]
    assert 0.5 * (-1.0 + 1.0) == 0.0
    assert abs(0.0 - 1e-6) == 1e-6

    at = SS.probe_chainages([1e-6], [True], 300.0, 800.0, ranges)
    assert [c for c, _flag in at] == [1e-6], at          # środek NIE dochodzi
    # kontrola negatywna: odrobinę dalej i środek zostaje dopisany
    above = SS.probe_chainages([1.005e-6], [True], 300.0, 800.0, ranges)
    assert [c for c, _flag in above] == [0.0, 1.005e-6], above
    # oraz odrobinę bliżej — nadal pokryty
    below = SS.probe_chainages([0.995e-6], [True], 300.0, 800.0, ranges)
    assert [c for c, _flag in below] == [0.995e-6], below


# --- point_at na granicach odcinków --------------------------------------------

def test_surface_point_at_returns_the_first_point_for_chainage_zero():
    """Kilometraż 0 leży dokładnie na początku pierwszego odcinka i musi go trafić.

    Warunek `sa <= target` ma granicę w `target == sa`, a jedyny taki kilometraż
    dla pierwszego odcinka to zero. Przy `<` żaden odcinek nie pasuje i funkcja
    po cichu zwraca OSTATNI punkt osi — czyli sonda „z kilometrażu 0" opisywałaby
    drugi koniec linii.
    """
    points = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    chain = SS.chainage_of(points)
    assert chain == [0.0, 100.0, 200.0]
    assert SS.point_at(points, chain, 0.0) == (0.0, 0.0)
    # kontrola negatywna: środek pierwszego odcinka i koniec osi liczą się dalej
    assert SS.point_at(points, chain, 50.0) == (50.0, 0.0)
    assert SS.point_at(points, chain, 200.0) == (200.0, 0.0)


def test_surface_point_at_skips_a_zero_length_segment_instead_of_dividing_by_it():
    """Zdublowany punkt osi daje odcinek o zerowej długości — wolno go tylko pominąć.

    Strażnik `sb > sa` jest jedyną rzeczą, która stoi między tym wejściem
    a `ZeroDivisionError`: przy `>=` interpolacja liczy `(target - sa) / (sb - sa)`
    dla `sb == sa`. Zdublowane punkty w danych osi nie są egzotyką — bierze się
    je z zaokrąglenia współrzędnych w źródle.
    """
    doubled = [(0.0, 0.0), (0.0, 0.0), (100.0, 0.0)]
    chain = SS.chainage_of(doubled)
    assert chain == [0.0, 0.0, 100.0]
    assert SS.point_at(doubled, chain, 0.0) == (0.0, 0.0)
    # kontrola negatywna: bez duplikatu ta sama oś zachowuje się identycznie
    clean = [(0.0, 0.0), (100.0, 0.0)]
    assert SS.point_at(clean, SS.chainage_of(clean), 0.0) == (0.0, 0.0)


def test_surface_classify_accepts_a_way_exactly_at_the_distance_limit():
    """Way odległy dokładnie o `NEAREST_MAX_M` jeszcze opisuje ten odcinek.

    `distance_m <= NEAREST_MAX_M` różni się od `<` tylko dla równości, a istniejący
    test sprawdzał wyłącznie `NEAREST_MAX_M + 1.0`, czyli stronę bezpieczną.
    Odcięcie o metr za wcześnie zamienia sondę „zgodne" w „jedno_zrodlo" i cicho
    obniża liczbę sond porównywalnych.
    """
    limit = SS.NEAREST_MAX_M
    verdict, urbis, osm = SS.classify({"niveau": "-"}, {"tunnel": "yes", "distance_m": limit})
    assert (verdict, urbis, osm) == ("zgodne", "tunel", "tunel")
    # kontrola negatywna: metr dalej way już nie mówi nic o tym odcinku
    verdict, _urbis, osm = SS.classify({"niveau": "-"},
                                       {"tunnel": "yes", "distance_m": limit + 1.0})
    assert verdict == "jedno_zrodlo" and osm is None


# --- remis odległości: który way wygrywa ---------------------------------------

def _on_the_way(x, y):
    """Punkt Lambert 72 po pełnym obiegu przez WGS84 i z powrotem.

    Way'e w OSM są zapisane w stopniach i moduł przelicza je na Lambert 72, więc
    „ten sam punkt" w metrach to dopiero wynik takiego obiegu. Bez tego odległość
    wychodzi rzędu 1e-8 m zamiast zera i remis przestaje być remisem — a remis
    jest tu całą treścią testu.
    """
    import crs as CRS
    return CRS.wgs84_to_lambert72(*CRS.lambert72_to_wgs84(x, y))


def test_surface_nearest_subway_keeps_the_first_way_when_two_are_equidistant():
    """Dwa way'e w tym samym śladzie: wynik ma być deterministyczny, czyli pierwszy.

    W OSM zdublowany ślad zdarza się i bywa otagowany różnie — jeden `tunnel=yes`,
    drugi bez tagu. Wtedy wybór „pierwszy czy ostatni" nie jest kosmetyką: decyduje
    o tym, co narzędzie ogłosi o tym odcinku. `distance < best["distance_m"]`
    trzyma pierwszy; `<=` cicho przerzuca wynik na ostatni.
    """
    import crs as CRS
    start = CRS.lambert72_to_wgs84(150000.0, 170000.0)
    end = CRS.lambert72_to_wgs84(150200.0, 170000.0)
    trace = [(start[0], start[1]), (end[0], end[1])]
    payload = _osm([("pierwszy", trace, {"railway": "subway", "tunnel": "yes"}),
                    ("drugi", trace, {"railway": "subway"})])
    point = _on_the_way(150000.0, 170000.0)
    best = SS.nearest_subway(payload, point)
    assert best["distance_m"] == 0.0, best
    assert best["way_id"] == "pierwszy" and best["tunnel"] == "yes", best
    # kontrola negatywna: gdy remisu nie ma, wygrywa naprawdę bliższy
    far = CRS.lambert72_to_wgs84(150000.0, 170200.0)
    payload = _osm([("daleki", [(far[0], far[1]), (far[0] + 0.002, far[1])],
                     {"railway": "subway", "tunnel": "yes"}),
                    ("bliski", trace, {"railway": "subway"})])
    assert SS.nearest_subway(payload, point)["way_id"] == "bliski"


def test_surface_nearest_segment_keeps_the_first_segment_when_two_are_equidistant():
    """To samo pytanie na ścieżce pełnego pokrycia z Overpassa, gdzie liczy się każdy punkt."""
    a, b = (150000.0, 170000.0), (150200.0, 170000.0)
    segments = [(a, b, "pierwszy", "yes", "-2"), (a, b, "drugi", None, None)]
    index = SS.segment_grid(segments)
    best = SS.nearest_segment(a, segments, index)
    assert best["distance_m"] == 0.0, best
    assert best["way_id"] == "pierwszy" and best["tunnel"] == "yes", best
    # kontrola negatywna: przesunięcie drugiego odcinka bliżej zmienia zwycięzcę
    closer = [(  (150000.0, 170050.0), (150200.0, 170050.0), "pierwszy", "yes", "-2"),
              (a, b, "drugi", None, None)]
    index = SS.segment_grid(closer)
    assert SS.nearest_segment(a, closer, index)["way_id"] == "drugi"


def _pair_of_ways(order):
    """Dwa way'e metra po przeciwnych stronach osi, w zadanej kolejności dokumentu.

    `order` to lista `(way_id, odsunięcie_w_metrach, tagi)`. Odsunięcie jest podane
    w Lambert 72 i dopiero przeliczane na stopnie, bo próg, o który tu chodzi, ma
    rozmiar pół centymetra i musi być zadany w metrach, a nie w stopniach.
    """
    import crs as CRS
    ways = []
    for way_id, offset_m, tags in order:
        ends = (CRS.lambert72_to_wgs84(149900.0, 170000.0 + offset_m),
                CRS.lambert72_to_wgs84(150100.0, 170000.0 + offset_m))
        ways.append((way_id, [tuple(ends[0]), tuple(ends[1])], dict(tags, railway="subway")))
    return _osm(ways)


# Bliższy way leży 0.906 m od osi, dalszy 0.909 m — różnica 3 mm, czyli MNIEJ niż
# pół centymetra. Oba zaokrąglają się do tego samego 0.91 m, więc raport wygląda
# identycznie, a `tunnel` i `layer` są różne: to one decydują o werdykcie.
_CLOSER = ("blizszy", 0.906, {"tunnel": "yes", "layer": "-2"})
_FARTHER = ("dalszy", -0.909, {"layer": "-3"})


def test_surface_nearest_subway_prefers_the_closer_way_below_the_rounding_step():
    """Way bliższy o 3 mm ma wygrać, choć obie odległości zaokrąglają się do 0.91 m.

    Porównanie brzmiało `distance < best["distance_m"]`, a w `best` leżała wartość
    już zaokrąglona do dwóch miejsc. Kandydat oddalony o 0.909 m przechodził więc
    test wobec zapisanego 0.91 m i wypierał way leżący o 0.906 m — czyli DALSZY
    wygrywał z BLIŻSZYM, o ile tylko wypadł w dokumencie później.

    Kontrola negatywna jest wpisana w sam kształt danych: na kodzie sprzed zmiany
    ten test padał, bo `nearest_subway` zwracał `way_id == "dalszy"` z `tunnel=None`
    (sprawdzone przez uruchomienie tego samego wejścia na wersji z
    `origin/triaz-powierzchnia-i-szerokosc`). Druga kontrola negatywna jest na dole:
    przy różnicy 200 m wynik jest ten sam przed i po zmianie.
    """
    point = _on_the_way(150000.0, 170000.0)
    best = SS.nearest_subway(_pair_of_ways([_CLOSER, _FARTHER]), point)
    assert best["way_id"] == "blizszy", best
    assert best["tunnel"] == "yes" and best["layer"] == "-2", best
    # kontrola negatywna: przy różnicy dużo większej niż krok zaokrąglenia wybór
    # był poprawny także przed zmianą — poprawka nie rusza tego przypadku
    far = ("daleki", 200.0, {"layer": "-9"})
    assert SS.nearest_subway(_pair_of_ways([_CLOSER, far]), point)["way_id"] == "blizszy"
    assert SS.nearest_subway(_pair_of_ways([far, _CLOSER]), point)["way_id"] == "blizszy"


def test_surface_nearest_subway_gives_the_same_way_in_both_input_orders():
    """Ta sama para way'ów w obu kolejnościach ma dać ten sam wynik.

    To jest właściwa treść usterki: przy porównaniu z wartością zaokrągloną wynik
    zależał od kolejności elementów w dokumencie OSM, a ta kolejność nie niesie
    żadnej informacji o terenie — zmienia się przy każdej edycji mapy. Narzędzie,
    którego wynik zależy od kolejności wejścia, nie mierzy tego, co obiecuje.

    Na kodzie sprzed zmiany ten test padał: dla kolejności `[bliższy, dalszy]`
    wychodził way `dalszy`, dla `[dalszy, bliższy]` — way `bliższy`. Kontrola
    negatywna poniżej pokazuje, że sam test nie jest tautologią: gdy way'e są
    naprawdę różnie odległe, obie kolejności też muszą dać ten sam wynik.
    """
    point = _on_the_way(150000.0, 170000.0)
    first = SS.nearest_subway(_pair_of_ways([_CLOSER, _FARTHER]), point)
    second = SS.nearest_subway(_pair_of_ways([_FARTHER, _CLOSER]), point)
    assert first == second, (first, second)
    assert first["way_id"] == "blizszy", first
    # kontrola negatywna: niezależność od kolejności musi zachodzić także wtedy,
    # gdy zwycięzcą jest way podany jako drugi
    swapped = ("blizszy", -0.906, {"tunnel": "yes", "layer": "-2"})
    other = ("dalszy", 0.909, {"layer": "-3"})
    assert (SS.nearest_subway(_pair_of_ways([swapped, other]), point)["way_id"]
            == SS.nearest_subway(_pair_of_ways([other, swapped]), point)["way_id"]
            == "blizszy")


def test_surface_nearest_segment_prefers_the_closer_segment_and_ignores_input_order():
    """To samo pytanie na ścieżce pełnego pokrycia z Overpassa — punkt po punkcie.

    `nearest_segment` miał tę samą usterkę co `nearest_subway` i to ona liczy się
    w praktyce: ścieżka `--osm-file` klasyfikuje KAŻDY punkt osi, więc przerzucenie
    way'a o pół centymetra dotyczy setek punktów naraz. Na kodzie sprzed zmiany
    pierwsza asercja padała (wychodził `dalszy`, `tunnel=None`), a druga pokazywała
    dwa różne way'e dla dwóch kolejności tej samej pary.
    """
    def pair(order):
        return [((149900.0, 170000.0 + offset), (150100.0, 170000.0 + offset),
                 way_id, tags.get("tunnel"), tags.get("layer"))
                for way_id, offset, tags in order]

    forward = pair([_CLOSER, _FARTHER])
    backward = pair([_FARTHER, _CLOSER])
    point = (150000.0, 170000.0)
    best = SS.nearest_segment(point, forward, SS.segment_grid(forward))
    assert best["way_id"] == "blizszy" and best["tunnel"] == "yes", best
    assert best == SS.nearest_segment(point, backward, SS.segment_grid(backward)), best
    # kontrola negatywna: odcinek odsunięty o 200 m przegrywa w obu kolejnościach
    far = ("daleki", 200.0, {"layer": "-9"})
    for order in ([_CLOSER, far], [far, _CLOSER]):
        segments = pair(order)
        assert SS.nearest_segment(point, segments,
                                  SS.segment_grid(segments))["way_id"] == "blizszy"


def test_surface_nearest_reports_the_distance_rounded_to_two_places():
    """Do raportu ma iść odległość zaokrąglona do 2 miejsc — format się nie zmienia.

    Zmiana dotyczy wyłącznie tego, co porównywane; to, co zapisane, ma zostać takie
    samo, bo `distance_m` trafia do plików raportu i do progu `NEAREST_MAX_M`.
    Kontrola negatywna jest tu wymierzona w NAJPROSTSZĄ złą poprawkę tej usterki:
    „trzymaj w `best` surową odległość i tyle". Wtedy `distance_m` przestałoby być
    zaokrąglone, raporty zmieniłyby format, a ten test by to złapał — 12.3456789
    zamiast 12.35. Dlatego odsunięcie ma siedem miejsc po przecinku, a nie dwa.
    """
    import crs as CRS
    offset = 12.3456789
    point = _on_the_way(150000.0, 170000.0)
    best = SS.nearest_subway(_pair_of_ways([("jedyny", offset, {"tunnel": "yes"})]), point)
    assert best["distance_m"] == 12.35, best
    assert best["distance_m"] == round(best["distance_m"], 2), best

    segments = [((149900.0, 170000.0 + offset), (150100.0, 170000.0 + offset),
                 "jedyny", "yes", "-2")]
    entry = SS.nearest_segment((150000.0, 170000.0), segments, SS.segment_grid(segments))
    assert entry["distance_m"] == 12.35, entry
    assert entry["distance_m"] == round(entry["distance_m"], 2), entry
    # kontrola negatywna: inne odsunięcie daje inną liczbę, więc 12.35 nie bierze
    # się z tego, że pole jest stałe
    other = SS.nearest_subway(_pair_of_ways([("jedyny", 5.0, {"tunnel": "yes"})]), point)
    assert other["distance_m"] == 5.0, other


# --- filtry snapshotu Overpassa -------------------------------------------------

def _overpass(elements):
    return {"elements": elements}


def _overpass_way(way_id, tags, x_from=150000.0, x_to=150200.0, y=170000.0):
    import crs as CRS
    geometry = [{"lon": lon, "lat": lat} for lon, lat in
                (CRS.lambert72_to_wgs84(x_from, y), CRS.lambert72_to_wgs84(x_to, y))]
    return {"type": "way", "id": way_id, "tags": tags, "geometry": geometry}


def test_surface_overpass_segments_take_only_subway_ways_that_have_geometry():
    """Trzy filtry snapshotu Overpassa naraz — każdy sprawdzony osobnym wejściem.

    Cała ścieżka `--osm-file` nie miała żadnego testu, więc filtr typu elementu,
    filtr obecności geometrii i filtr `railway=subway` można było odwrócić i zestaw
    dalej świecił na zielono. Snapshot Overpassa niesie też węzły i inne tory,
    a wciągnięcie tramwaju do klasyfikacji metra jest błędem, którego nie widać
    w liczbie punktów — widać go dopiero w werdykcie.
    """
    subway = _overpass_way(11, {"railway": "subway", "tunnel": "yes"})
    ids = lambda payload: [s[2] for s in SS.overpass_segments(payload)]

    assert ids(_overpass([subway])) == ["11"]

    node = dict(_overpass_way(33, {"railway": "subway"}), type="node")
    assert ids(_overpass([subway, node])) == ["11"], "węzeł nie jest odcinkiem toru"

    without_geometry = {"type": "way", "id": 44, "tags": {"railway": "subway"}}
    assert ids(_overpass([subway, without_geometry])) == ["11"], "way bez geometrii"

    tram = _overpass_way(22, {"railway": "tram"})
    assert ids(_overpass([subway, tram])) == ["11"], "tramwaj to nie metro"

    # kontrola negatywna: drugi prawdziwy way metra ma się pojawić
    other = _overpass_way(12, {"railway": "subway"}, x_from=150400.0, x_to=150600.0)
    assert ids(_overpass([subway, other])) == ["11", "12"]


# --- cały przebieg: survey() i main() -------------------------------------------

_X0, _Y0, _STEP, _COUNT = 148000.0, 170000.0, 100.0, 31   # 3000 m prostej osi
_SURFACE_FROM, _SURFACE_TO = 700.0, 1500.0                # deklarowany odcinek niveau = 0


def _urbis_polygon(x_from, x_to, niveau, name):
    import crs as CRS
    corners = [(x_from, _Y0 - 40.0), (x_to, _Y0 - 40.0),
               (x_to, _Y0 + 40.0), (x_from, _Y0 + 40.0)]
    ring = [list(CRS.lambert72_to_wgs84(x, y)) for x, y in corners]
    return {"type": "Feature",
            "properties": {"type": "MT", "niveau": niveau, "name_fr": name},
            "geometry": {"type": "Polygon", "coordinates": [ring + [ring[0]]]}}


def _survey_fixture(directory, niveau_of_the_middle="0"):
    """Oś, snapshot UrbIS i snapshot Overpassa — wszystko lokalnie, bez sieci.

    Oś jest prosta i równoległa do osi X, więc kilometraż jest wielokrotnością
    stu metrów i wszystkie progi wypadają na liczbach dokładnych. `niveau` środkowego
    poligonu jest parametrem, bo to jedyne miejsce, które psuje kontrola negatywna.
    """
    import json
    import crs as CRS
    alignment = {"id": "TEST_A", "source_crs": "EPSG:31370",
                 "origin_source_crs": [_X0, _Y0],
                 "points": [[i * _STEP, 0.0] for i in range(_COUNT)],
                 "stations": []}
    alignment_path = os.path.join(directory, "TEST_A.json")
    with open(alignment_path, "w", encoding="utf-8") as handle:
        json.dump(alignment, handle)

    east = _X0 + _STEP * (_COUNT - 1) + 50.0
    urbis = {"type": "FeatureCollection", "features": [
        _urbis_polygon(_X0 - 50.0, _X0 + _SURFACE_FROM, "-", "tunel zachodni"),
        _urbis_polygon(_X0 + _SURFACE_FROM, _X0 + _SURFACE_TO,
                       niveau_of_the_middle, "wykop"),
        _urbis_polygon(_X0 + _SURFACE_TO, east, "-", "tunel wschodni"),
    ]}
    urbis_path = os.path.join(directory, "urbis.json")
    with open(urbis_path, "w", encoding="utf-8") as handle:
        json.dump(urbis, handle)

    def way(way_id, x_from, x_to, tags):
        geometry = [{"lon": lon, "lat": lat} for lon, lat in
                    (CRS.lambert72_to_wgs84(x_from, _Y0),
                     CRS.lambert72_to_wgs84(x_to, _Y0))]
        return {"type": "way", "id": way_id, "tags": dict(tags, railway="subway"),
                "geometry": geometry}

    overpass = {"elements": [
        way(1, _X0 - 50.0, _X0 + _SURFACE_FROM, {"tunnel": "yes"}),
        way(2, _X0 + _SURFACE_FROM, _X0 + _SURFACE_TO, {}),
        way(3, _X0 + _SURFACE_TO, east, {"tunnel": "yes"}),
    ]}
    overpass_path = os.path.join(directory, "overpass.json")
    with open(overpass_path, "w", encoding="utf-8") as handle:
        json.dump(overpass, handle)
    return alignment_path, urbis_path, overpass_path


def _osm_probe_blob():
    """Odpowiedź `api.openstreetmap.org/map` udawana dla KAŻDEJ sondy.

    Jeden way `tunnel=yes` biegnący całą osią. Dzięki temu sondy OSM mówią „tunel"
    wszędzie, także tam, gdzie UrbIS mówi `niveau = 0` — i przebieg produkuje obie
    klasy werdyktu, „zgodne" i „sprzeczne", w jednym wyniku.
    """
    import crs as CRS
    east = _X0 + _STEP * (_COUNT - 1) + 50.0
    nodes, refs = [], []
    for index, x in enumerate((_X0 - 50.0, east)):
        lon, lat = CRS.lambert72_to_wgs84(x, _Y0)
        nodes.append(f'<node id="{index + 1}" lon="{lon}" lat="{lat}"/>')
        refs.append(f'<nd ref="{index + 1}"/>')
    return ('<osm version="0.6">' + "".join(nodes) + '<way id="9">' + "".join(refs)
            + '<tag k="railway" v="subway"/><tag k="tunnel" v="yes"/></way></osm>'
            ).encode("utf-8")


def _run_survey(directory, niveau_of_the_middle="0"):
    alignment_path, urbis_path, overpass_path = _survey_fixture(
        directory, niveau_of_the_middle)
    args = SS.parse_args(["--alignment", alignment_path,
                          "--out", os.path.join(directory, "out.json"),
                          "--urbis-file", urbis_path,
                          "--osm-file", overpass_path])
    saved = SS.fetch_osm_box
    SS.fetch_osm_box = lambda lon, lat, half, timeout, cache=None: (
        _osm_probe_blob(), "test", None)
    try:
        return SS.survey(alignment_path, args)
    finally:
        SS.fetch_osm_box = saved


def test_surface_survey_counts_both_sources_and_does_not_average_them():
    """Cały przebieg na lokalnych snapshotach: liczby, nie „wykonało się bez błędu".

    `survey()` nie miał żadnego testu, więc odwrócenie dowolnego porównania w środku
    — który punkt jest `niveau = 0`, który werdykt jest „zgodne", który punkt OSM jest
    poza tunelem, która sonda stoi przy portalu — przechodziło niezauważone. Wszystkie
    te liczby są tu przybite naraz, bo wszystkie razem stanowią wynik narzędzia.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        report = _run_survey(directory)

    assert report["alignment_id"] == "TEST_A"
    assert report["axis_length_m"] == 3000.0

    # UrbIS: 7 punktów osi leży w poligonie niveau = 0, w jednym ciągłym przedziale
    assert report["niveau0_points"] == 7, report["niveau0_points"]
    assert report["niveau0_pct"] == 22.6
    assert report["niveau0_chainage_ranges_m"] == [[800.0, 1400.0]]

    # sondy: OSM mówi „tunel" wszędzie, więc w wykopie musi wyjść sprzeczność
    assert report["probe_count"] == 6
    assert report["verdicts"] == {"sprzeczne": 3, "zgodne": 3}
    assert report["matrix"] == {"urbis=poza_tunelem|osm=tunel": 3,
                                "urbis=tunel|osm=tunel": 3}
    assert report["comparable_probes"] == 6
    assert report["agreement_pct"] == 50.0
    # poza otoczeniem portali sond jest mniej i zgodność jest inna liczbą
    assert report["comparable_off_portal"] == 4
    assert report["agreement_off_portal_pct"] == 75.0

    full = report["full_coverage"]
    assert full["points"] == 31
    assert full["comparable_points"] == 31
    assert full["verdicts"] == {"sprzeczne": 1, "zgodne": 30}
    assert full["agreement_pct"] == 96.8
    assert full["matrix"] == {"urbis=poza_tunelem|osm=poza_tunelem": 7,
                              "urbis=tunel|osm=poza_tunelem": 1,
                              "urbis=tunel|osm=tunel": 23}
    assert full["osm_surface_points"] == 8
    assert full["osm_surface_pct"] == 25.8
    # Punkty osi 700 i 1500 leżą DOKŁADNIE w stykach way'ów, więc oba way'e są tam
    # od nich odległe o zero z dokładnością do szumu przeliczenia WGS84↔Lambert 72
    # (rzędu 4e-9 m). Który z pary wygrywa, jest w tym miejscu nierozstrzygalne
    # geometrycznie; liczby zbiorcze wyżej — 8 punktów poza tunelem i cała macierz —
    # nie zależą od tego wyboru, bo styk zawsze oddaje dokładnie jeden punkt.
    assert full["osm_surface_ranges_m"] == [[700.0, 1400.0]]
    assert len(full["contradictions"]) == 1
    assert full["contradictions"][0]["chainage_m"] == 700.0


def test_surface_survey_keeps_the_two_sources_independent():
    """Kontrola negatywna: psujemy JEDNO pole i sprawdzamy, że rusza się tylko ono.

    Zmiana `niveau` środkowego poligonu z `0` na `-` dotyczy wyłącznie UrbIS.
    Statystyki OSM — ile punktów jest poza tunelem i w jakich przedziałach — mają
    zostać co do liczby takie same. Gdyby narzędzie gdziekolwiek uśredniało źródła
    albo przepisywało jedno z drugiego, ten test by to pokazał.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        healthy = _run_survey(directory, "0")
    with tempfile.TemporaryDirectory() as directory:
        broken = _run_survey(directory, "-")

    assert healthy["niveau0_points"] == 7 and broken["niveau0_points"] == 0
    assert broken["niveau0_chainage_ranges_m"] == []
    assert broken["verdicts"] == {"zgodne": 4}
    assert broken["agreement_pct"] == 100.0

    healthy_full, broken_full = healthy["full_coverage"], broken["full_coverage"]
    assert healthy_full["osm_surface_points"] == broken_full["osm_surface_points"] == 8
    assert healthy_full["osm_surface_ranges_m"] == broken_full["osm_surface_ranges_m"]
    assert broken_full["verdicts"] == {"sprzeczne": 8, "zgodne": 23}


def test_surface_main_prints_only_the_contradictions():
    """Na konsolę idą sondy SPRZECZNE i tylko one — to jest wynik czytany przez człowieka.

    Bez tego odwrócenie porównania w pętli wypisującej zamienia listę rozbieżności
    w listę wszystkiego, co rozbieżnością nie jest. Raport JSON pozostaje wtedy
    poprawny, a operator czyta dokładnie odwrotność tego, co go interesuje.
    """
    import contextlib
    import io
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        alignment_path, urbis_path, _overpass = _survey_fixture(directory)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = SS.main(["--alignment", alignment_path,
                            "--out", os.path.join(directory, "out.json"),
                            "--urbis-file", urbis_path, "--skip-osm"])
        printed = buffer.getvalue()

    assert code == 0
    # bez OSM żadna sonda nie może być sprzeczna — nie ma z czym być sprzeczna
    assert "SPRZECZNE" not in printed, printed
    # kontrola negatywna: reszta raportu jest wypisana, więc milczenie nie bierze się
    # z tego, że pętla w ogóle nie doszła do wypisywania
    assert "niveau=0 na 7 punktach" in printed, printed
    assert "urbis=poza_tunelem|osm=None: 3" in printed, printed

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
