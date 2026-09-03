"""Decyzje renderu kontrolnego przed dotknięciem sceny — czysty Python, bez Blendera.

Wydzielone z `capture_blender.py`, który importuje `bpy` i `mathutils`. Przemiatanie
mutacyjne z 03.09.2026 dało tam 10 mutacji i 10 ocalałych. Piąta taka ekstrakcja
po `tunnel_manifest.py` (#142), `m7_report.py` (#144), `profile_scan.py` (#154)
i `glb_report.py` (#160).

Kadrowanie już jest testowalne — siedzi w `framing.py`. Tutaj zostaje to, co
`capture_blender.py` rozstrzyga **wokół** kadrowania i co do 03.09.2026 nie miało
ani jednego testu:

* którym EEVEE renderuje ten Blender i czy wolno mu renderować ten baseline,
* czy zestaw ujęć w ogóle należy do Blendera, czy do silnika,
* jak czytać kotwice z wiersza poleceń,
* gdzie na osi leży zadany chainage.

W `capture_blender.py` zostaje budowa kamer, materiał kontrolny, overlay siatki
i sam render.
"""

#: Wersja Blendera, od której `BLENDER_EEVEE`/`BLENDER_EEVEE_NEXT` znaczy EEVEE Next.
#: Legacy EEVEE usunięto w 4.2 (blender/blender#122433); nowy silnik nosił wtedy
#: identyfikator `BLENDER_EEVEE_NEXT`, a w 5.0 przemianowano go z powrotem na
#: `BLENDER_EEVEE`. Sama nazwa silnika NIE identyfikuje więc renderera — rozstrzyga
#: dopiero wersja Blendera.
EEVEE_NEXT_SINCE = (4, 2, 0)


def eevee_generation(version):
    """'next' albo 'legacy' — który EEVEE naprawdę stoi za nazwą `BLENDER_EEVEE`.

    `version` to krotka jak `bpy.app.version`. Porównanie krotek jest tu celowe:
    4.2.0 to PIERWSZA wersja z nowym silnikiem, więc granica należy do 'next'.
    """
    return "next" if tuple(version) >= EEVEE_NEXT_SINCE else "legacy"


def eevee_conflict(expected, actual, version_string):
    """Komunikat odmowy, gdy baseline projektu i ten Blender to dwa różne EEVEE.

    Zwraca `None`, gdy renderować wolno. Zwraca gotowe zdanie, gdy nie wolno —
    wołający ma je tylko podnieść jako `SystemExit`.

    Brak `eevee_generation` w manifeście znaczy „baseline nie deklaruje silnika",
    czyli zgodę, a nie konflikt. Bez tego rozróżnienia manifest bez tego pola
    blokowałby każdy render.

    ZMIERZONE 02.09.2026: `enum_items` dla `engine` zwraca DOKŁADNIE
    `['BLENDER_EEVEE']` i na 4.0.2, i na 5.0.1 — a to dwa różne silniki. Bez tej
    bramki CI liczyło ujęcia legacy EEVEE i uznawało je za porównywalne
    z baseline'em z EEVEE Next. Kosztowało dwie czerwone bramki
    (`tunnel-alignment` L1_B i L2_E) przy przejściu CI na maszynę właściciela.
    """
    if not expected:
        return None
    if actual == expected:
        return None
    return (f"BŁĄD: baseline projektu to EEVEE '{expected}', a ten Blender "
            f"({version_string}) daje EEVEE '{actual}'. Rendery z obu "
            "silników NIE są porównywalne — patrz EEVEE_NEXT_SINCE.")


def renderer_conflict(scene_set_name, renderer):
    """Komunikat odmowy, gdy zestaw ujęć nie należy do Blendera. `None`, gdy należy.

    Zestaw `godot` opisuje ujęcia z SILNIKA: kamery są w scenie Godota, a w manifeście
    zostają tylko identyfikatory i progi dla `compare.py`. Bez tej odmowy Blender
    wygenerowałby z niego klatki domyślną kamerą i nikt by nie zauważył, że to nie
    są te ujęcia.
    """
    if renderer == "blender":
        return None
    return (f"BŁĄD: zestaw {scene_set_name} jest renderowany przez '{renderer}', "
            "nie przez Blendera — tu nie ma czego renderować")


def parse_anchors(items):
    """`['nazwa=X,Y,Z', ...]` -> `{'nazwa': [x, y, z]}`. Odmawia zamiast domyślać się.

    Kotwica bez `=` i kotwica o innej liczbie współrzędnych niż trzy to dwa różne
    błędy wołającego i dostają dwa różne komunikaty — jeden komunikat na oba
    kazałby zgadywać, którą literówkę się popełniło.
    """
    anchors = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"zła kotwica {item!r}, oczekiwano nazwa=X,Y,Z")
        name, raw = item.split("=", 1)
        parts = [float(v) for v in raw.split(",")]
        if len(parts) != 3:
            raise ValueError(f"kotwica {name} musi mieć trzy współrzędne")
        anchors[name.strip()] = parts
    return anchors


def point_at_chainage(axis, stations, chainage):
    """Punkt na osi w zadanym chainage, jako krotka trzech liczb.

    Kotwice liczymy w METRACH, nie w ułamkach osi, więc chainage poza osią jest
    przycinany do jej końców, a nie odrzucany: kotwica podana przez wołającego
    z zewnątrz ma prawo minąć koniec chunka i wtedy sensowną odpowiedzią jest
    koniec, nie wyjątek.

    Zwraca krotkę, nie `Vector` — `mathutils` istnieje tylko w Blenderze.
    """
    chainage = max(stations[0], min(stations[-1], chainage))
    for index in range(len(stations) - 1):
        if stations[index] <= chainage <= stations[index + 1]:
            span = stations[index + 1] - stations[index]
            t = 0.0 if span <= 0.0 else (chainage - stations[index]) / span
            a, b = axis[index], axis[index + 1]
            return tuple(a[i] + t * (b[i] - a[i]) for i in range(3))
    return tuple(axis[-1])


def is_orthographic(solved):
    """Czy rozwiązane kadrowanie opisuje kamerę ortograficzną.

    Jedna linia, ale to rozgałęzienie decyduje, czy kamera dostanie `ortho_scale`,
    czy `lens` — a te dwie liczby nie są przeliczalne jedna na drugą. Pomyłka tutaj
    daje ujęcie w poprawnym miejscu i z niepoprawnym kadrem, czyli dokładnie taki
    render, który przechodzi bramkę metryczną i kłamie na oko.

    Porównanie jest do dokładnego napisu, nie do prawdziwościowości: `projection`
    z manifestu ma dwie dozwolone wartości i literówka w niej ma dać perspektywę
    zgodnie z domyślną gałęzią, a nie ortogonalność „bo niepuste".
    """
    return solved["projection"] == "ORTHO"
