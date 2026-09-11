"""Celowanie kamery kontrolnej — czysta matematyka, bez Blendera.

Wydzielone z `render_check.py`, który importuje `bpy` i `mathutils`. Przemiatanie
mutacyjne z 03.09.2026 dało tam 8 mutacji i 8 ocalałych. Szósta taka ekstrakcja
po `tunnel_manifest.py` (#142), `m7_report.py` (#144), `profile_scan.py` (#154),
`glb_report.py` (#160) i `capture_plan.py` (#161).

Tutaj zostają trzy pytania, na które odpowiada się liczbami, a nie scenką:

* czy styczna osi jest zdegenerowana na tyle, że nie wyznacza kierunku,
* ile punktów musi mieć oś, żeby dało się po niej celować,
* czy kierunek patrzenia jest tak bliski pionu, że światowe „w górę" przestaje
  być użyteczne jako odniesienie.

Ostatnie jest najmniej oczywiste i najbardziej kosztowne, gdy pójdzie źle: przy
kamerze patrzącej prosto w dół iloczyn wektorowy kierunku ze światowym „w górę"
dąży do zera, więc `right` i `up` wychodzą losowe, a ujęcie jest obrócone
o przypadkowy kąt — i nadal przechodzi kontrolę pustej klatki.

W `render_check.py` zostaje wszystko, co dotyka sceny: budowa kamer, świat,
materiał kontrolny, overlay siatki i sam render.
"""
import math

#: Poniżej tej długości styczna nie wyznacza kierunku i trzeba wziąć zapasowy.
DEGENERATE_LENGTH = 1e-9

#: Powyżej tego |cos| między kierunkiem patrzenia a światowym „w górę" odniesienie
#: pionu przestaje być użyteczne. 0,995 to około 5,7° od pionu.
LEVEL_DOT_LIMIT = 0.995

#: Mniej punktów niż tyle to nie jest oś, tylko punkt — nie ma po czym celować.
MIN_CENTERLINE_POINTS = 2


def vector_length(vector):
    """Długość euklidesowa krotki. `math.hypot` po to, żeby nie tracić precyzji na kwadratach."""
    return math.hypot(*vector)


def is_degenerate(vector):
    """Czy wektor jest za krótki, żeby wyznaczać kierunek.

    Granica NALEŻY do „jeszcze użyteczny": wektor o długości dokładnie
    `DEGENERATE_LENGTH` jest przyjmowany. To odróżnia `<` od `<=` i tę granicę
    da się dotknąć dokładnie — `math.hypot(t, 0, 0)` zwraca `abs(t)` bit w bit,
    więc styczna `(DEGENERATE_LENGTH, 0, 0)` stoi na progu bez błędu reprezentacji.
    Podnoszenie do kwadratu i cofanie się pierwiastkiem tej własności nie ma.
    """
    return vector_length(vector) < DEGENERATE_LENGTH


def enough_centerline_points(count):
    """Czy oś ma po czym celować. Dwa punkty wystarczają, jeden nie."""
    return count >= MIN_CENTERLINE_POINTS


def needs_fallback_up(dot_abs):
    """Czy |cos| między kierunkiem i światowym pionem jest już za duży.

    Bierze GOTOWY iloczyn skalarny, a nie kierunek, właśnie po to, żeby granicę
    dało się dotknąć dokładnie. Wektor jednostkowy o składowej Z równej dokładnie
    0,995 nie istnieje w arytmetyce zmiennoprzecinkowej — normalizacja wprowadza
    błąd i test „na granicy" wypadłby obok, nie odróżniając `>` od `>=`.
    Tu granicę podaje się wprost i porównanie jest sprawdzalne.
    """
    return dot_abs > LEVEL_DOT_LIMIT


def up_reference(direction):
    """Światowe „w górę" albo zapasowe „w stronę +Y", gdy patrzymy prawie w pion.

    Zwraca krotkę. Kierunek nie musi być znormalizowany — normalizacja jest tutaj,
    bo bez niej iloczyn skalarny nie jest cosinusem i próg 0,995 nic nie znaczy.

    Kierunek zerowy nie ma pionu do wyznaczenia; wtedy zwracane jest światowe
    „w górę", bo to ta sama odpowiedź co dla kierunku poziomego i nie wymaga
    od wołającego obsługi trzeciego przypadku.
    """
    length = vector_length(direction)
    if length < DEGENERATE_LENGTH:
        return (0.0, 0.0, 1.0)
    dot_abs = abs(direction[2] / length)
    return (0.0, 1.0, 0.0) if needs_fallback_up(dot_abs) else (0.0, 0.0, 1.0)


def centerline_position(count, fraction):
    """`(lo, hi, t)` — który odcinek osi i jak głęboko w nim leży zadany ułamek.

    Wydzielone bez interpolacji samych punktów, bo interpolację robi `Vector.lerp`
    i ona należy do Blendera. Tutaj jest to, co decyduje: indeksy i waga.

    `hi` jest przycięte do ostatniego punktu, więc ułamek 1,0 nie wychodzi za oś.
    """
    position = (count - 1) * fraction
    lo = int(math.floor(position))
    hi = min(lo + 1, count - 1)
    return lo, hi, position - lo


# --- 6.D140: okno kadru a czytelność klatek --------------------------------------

#: Kamery, którym okno `--from-m/--to-m` narzuca środek i rozmiar kadru.
#:
#: **Wpis pozycji 6.D140 twierdził, że okno zawęża WYŁĄCZNIE `_inside`, a `_iso`
#: i `_side` nadal kadrują cały obiekt. To nieprawda i obalił to pomiar** na osi
#: `L1_A` (5452,5 m długości, 5,9 m wysokości, proporcje 924 : 1), Blender 5.2.1:
#:
#:   bez okna         cam_iso distance 7920,3 m   ink 0,00277
#:                    cam_side distance 7677,3 m  ink 0,00292
#:   okno 400–500 m   cam_iso distance  137,3 m   ink 0,11039
#:                    cam_side distance  133,1 m  ink 0,10808
#:
#: Czterdziestokrotna różnica w pokryciu klatki bierze się stąd, że `render_check`
#: podstawia `center` i `size` z okna ZANIM zbuduje pierwszą kamerę — więc okno
#: rządzi wszystkimi czterema, nie jedną.
KAMERY_POD_OKNEM = ("cam_iso", "cam_side", "cam_normals", "cam_inside")


def proporcje_okna(dlugosc_m, wysokosc_m):
    """Ile razy okno jest dłuższe niż wysokie. `None`, gdy wysokość jest zerowa.

    Liczba, która przewiduje kształt klatki `_side` — a nie długość osi, i to jest
    poprawka wobec wpisu 6.D140. Zmierzone na `L1_A`, `box_double`, wysokość 5,9 m:

        okno       proporcje   ink `_side`
        100 m        17 : 1      0,10808
        300 m        51 : 1      0,04044
        1000 m      169 : 1      0,01278
        3000 m      508 : 1      0,00556
        bez okna    924 : 1      0,00292

    **Progu tu nie ma i to jest wybór.** Pokrycie spada gładko, a podłoga pustej
    klatki (`compare.EMPTY_FRAME_FLOOR`, ink 0,0002) nie zapala się **w żadnym**
    z tych pięciu przypadków — także przy 924 : 1, gdzie obejrzana klatka jest
    włosem. Gdzie kreska przestaje być czytelna, jest oceną estetyczną, a `CLAUDE.md`
    §8 każe takich nie podejmować samemu. Liczba jest więc **wypisywana**, żeby
    oglądający wiedział, czego się spodziewać, i nie brał włosa za pustą scenę.
    """
    if not wysokosc_m:
        return None
    return dlugosc_m / wysokosc_m
