#!/usr/bin/env python3
"""Zapas pracy, którego nie da się przeoczyć między sesjami.

`docs/TASKS.md` niesie regułę: agent nigdy nie ma mniej niż 24 godziny pracy przed
sobą, a uzupełnienie zapasu jest zadaniem samo w sobie. Reguła zapisana w dokumencie
i nigdzie niesprawdzana jest życzeniem — ten test robi z niej bramkę.

Powód nie jest wydajnościowy. Agent, który skończył kolejkę, ma do wyboru stanąć albo
wymyślić sobie zadanie na miejscu. Drugie jest gorsze: zadanie wymyślone w pośpiechu
omija format z sekcji 6 `CLAUDE.md` i ląduje w kodzie, którego nikt nie prosił o zmianę.

Do 05.09.2026 ten plik liczył WYŁĄCZNIE, ile pozycji stoi w kolejce — nigdy, czy
pozycja jest zadaniem. Zmierzone tego dnia: wycięcie z `docs/TASKS.md` całej sekcji
`#### Szczegóły ośmiu pozycji dopisanych 04.09.2026`, **15 802 znaki** z sześcioma
polami dla ośmiu pozycji, przechodziło **1467/1467** testów. Licznik widział 33 wiersze
tabel tak samo przed wycięciem, jak po nim, bo wiersz tabeli zostaje wierszem tabeli
niezależnie od tego, czy gdziekolwiek w pliku stoi opis, jak to zadanie wykonać.

Stąd druga połowa tego pliku: `detail_sections` czyta bloki `##### <numer> · …`
i sprawdza sześć pól z `docs/TASK-TEMPLATE.md`. Numery liczone do zapasu i numery
udokumentowane to **dwie różne liczby** — pierwsza mówi, ile pozycji ktoś wpisał,
druga, ile z nich da się wziąć bez dopytywania właściciela.

Pozycja ODHACZONA jest z tego wymagania wyłączona **jawnie**, a nie przez przeoczenie:
domknięte numery stoją w tabeli `#### Domknięte i zdjęte z kolejki`, której kolumny to
`| # | co było | gdzie zostało zrobione |`. Tam nie ma sześciu pól i nie ma ich mieć —
odpowiednikiem „Wyniku" z `docs/TASK-TEMPLATE.md` jest trzecia kolumna, a `ready_items`
i tak wyklucza te numery z licznika. Wymaganie sześciu pól obowiązuje dokładnie te
pozycje, które licznik zapasu liczy.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS = os.path.join(ROOT, "docs", "TASKS.md")

# Próg z `docs/TASKS.md`. Przy 20-45 minutach na zadanie z pełną weryfikacją
# dwanaście pozycji to dolna granica doby pracy — a część pozycji to generatory,
# więc realny zapas jest większy.
MINIMUM_READY_ITEMS = 12

# Zadania, które mają być KOLEJKĄ. Sekcja „Czego agent nie ruszy bez decyzji"
# celowo NIE jest tu wymieniona: jej pozycje czekają na właściciela i nie są pracą,
# po którą agent może sięgnąć.
QUEUE_PREFIXES = ("5.", "6.")

#: Nagłówek tabeli kolejki. Służy do jednego: sprawdzenia, że wycinanie sekcji
#: domknięć nie zabrało ze sobą tabeli, z której ta sekcja pochodzi.
QUEUE_TABLE_HEADER = "| # | zadanie |"

#: Sześć pól z `CLAUDE.md` §6 i `docs/TASK-TEMPLATE.md`, dokładnie w tym brzmieniu,
#: w jakim stoją w `docs/TASKS.md`: `- **Wejście:** …`.
REQUIRED_FIELDS = (
    "Wejście",
    "Wyjście",
    "Weryfikacja",
    "Skończone, gdy",
    "Poza zakresem",
    "Zależy od",
)

#: Pole, które `docs/TASK-TEMPLATE.md` DOKŁADA do wpisu odhaczonego, a którego nie ma
#: wpis czekający w kolejce. Zmierzone 05.09.2026 na tym drzewie: wpisów `### [x]` jest
#: **17**, żaden nie ma „Skończone, gdy", a **14** ma to pole — jest więc jednoznacznym
#: znacznikiem wpisu zamkniętego. (Liczby przepisane, a nie dopisane obok: przed
#: odhaczeniem T-212 i T-906 było 15 wpisów i 12 pól.)
DONE_ONLY_FIELD = "Wynik"

#: PODŁOGA zapasu pozycji **do wzięcia**: udokumentowanych i niezrobionych.
#:
#: **To NIE jest zapadka i cały ten komentarz jest z tego powodu przepisany.**
#: Do 06.09.2026 jedna stała niosła dwie sprzeczne role: „bloków nie wolno kasować"
#: (wielkość rosnąca) i „zapas ma starczyć na dobę pracy" (wielkość, która **maleje,
#: gdy praca jest wykonywana**). Po zmianie liczenia z #272 sprzeczność wyszła
#: natychmiast i dwa razy pod rząd: adnotowanie 6.D4 jako `ZROBIONE` zbiło licznik
#: z 11 na 10, adnotowanie 6.B2 — z 11 na 10 znowu. Bramka świeciła na czerwono
#: **dlatego, że wykonano pracę**, a jedynym sposobem jej zaspokojenia było dopisanie
#: nowego bloku w tym samym commicie.
#:
#: Rozstrzyga to arytmetyka, nie gust. **Zdanie przepisane, a nie dopisane obok:**
#: poprzednia wersja mówiła „pozycji do wzięcia bez bloku zostały **dwie** (5.6 i 6.B5,
#: przy czym 6.B5 czeka na decyzję o pakietach C, D, F)", i nieprawdziwe są w niej oba
#: członki. Obie te pozycje dostały bloki 06.09.2026, więc pozycji bez bloku jest **zero**
#: — a 6.B5 na tamtą decyzję **nie czeka**: promień łuku i skrajnia liczą się z osi,
#: która dla wszystkich sześciu pakietów leży w `data/track/` od #86. Na decyzję „co
#: budować zamiast rury" czeka 6.B3 (LOD tuneli), i to ona stoi w „Czego agent nie
#: ruszy bez decyzji" — pomyłka polegała na przeniesieniu blokady z sąsiedniego wiersza.
#:
#: Sens tamtej arytmetyki zostaje: po zużyciu pozycji bez bloku bramki **nie dałoby się
#: już spełnić**, a domknięta praca nie dałaby się zacommitować. Bramka, której da się
#: zadośćuczynić tylko przez chwilę, nie jest bramką.
#:
#: Rola „nie wolno kasować" przeniosła się na `MINIMUM_DETAIL_BLOCKS` — tam jest
#: monotoniczna i tam ma sens. Ta liczba jest **podłogą alarmową**: wolno jej opadać,
#: gdy zadania są domykane, a zapala się dopiero wtedy, gdy zapas naprawdę cienieje.
#: Docelowa wielkość zapasu to nadal `MINIMUM_READY_ITEMS`, a odległość do niej
#: opisuje akapit w `docs/TASKS.md`, którego pilnuje
#: `test_the_documented_shortfall_is_written_down_while_it_lasts`.
#:
#: **Liczba przepisana, a nie dopisana obok, i to w tym samym dniu.** Poprzednia wersja
#: mówiła „udokumentowanych i niezrobionych **10**", a po scaleniu #275…#279 tego samego
#: dnia było ich **osiem** — bo każde z tych pięciu zadań dostało w swoim wierszu
#: `ZROBIONE`, a `open_items` takie wiersze odsiewa. To jest ta sama mechanika, której
#: ten komentarz broni dwa akapity wyżej: **licznik zapasu opada od wykonywania pracy**,
#: więc każda jego liczba wpisana ręcznie starzeje się w tempie scaleń.
#: Zmierzone 06.09.2026 po pierwszym uzupełnieniu kolejki: udokumentowanych
#: i niezrobionych **18**, podłoga **6**. Po domknięciu 6.A3 i 6.D9 tego samego dnia
#: zapas zszedł do **11** — czyli PONIŻEJ progu doby pracy — i bramka to zapaliła.
#: To jest ta sama mechanika opisana wyżej, tym razem widziana od strony skutku:
#: zapas spadł nie przez zaniedbanie, tylko przez wykonanie dwóch zadań. Drugie
#: uzupełnienie podniosło go do **15**. Podłogi nie podnoszę do osiemnastu i to jest decyzja, nie zaniedbanie:
#: równanie jej z zapasem odtworzyłoby dokładnie to sprzężenie, które #274 rozplątywało.
MINIMUM_DOCUMENTED_ITEMS = 6

#: ZAPADKA na liczbę **napisanych** bloków szczegółów, niezależnie od tego, czy
#: pozycja jest już zrobiona. Ta wielkość rośnie tylko przez pisanie i maleje tylko
#: przez kasowanie, więc „wolno tylko podnosić" jest tu zdaniem sensownym — w
#: przeciwieństwie do zapasu, który maleje od wykonywania pracy.
#:
#: Chroni dokładnie to, co chroniła stara zapadka: skasowanie bloku zapala bramkę,
#: a dopisanie kolejnego wymusza podniesienie stałej w tym samym commicie.
#:
#: **Liczba przepisana, a nie dopisana obok.** Poprzednia wersja mówiła **19** i była
#: prawdziwa; commit uzupełniający kolejkę dopisał dziesięć bloków — dwa dla pozycji,
#: które stały w tabeli bez opisu (5.6, 6.B5), dwa dla pozycji dopisanych 06.09.2026
#: bez bloków (6.B13, 6.B14) i sześć dla pozycji nowych (6.A9, 6.B15, 6.B16, 6.D9,
#: 6.D10, 6.D11). Zmierzone 06.09.2026 po tym commicie: **29** bloków, wszystkie
#: z kompletem sześciu pól. W przeciwieństwie do podłogi zapasu ta liczba **nie opada
#: od wykonywania pracy** — blok pozycji zrobionej zostaje napisany — i dlatego tylko
#: tutaj „wolno wyłącznie podnosić" jest zdaniem, które da się utrzymać.
#: **Liczba przepisana, a nie dopisana obok — 98 → 101 (07.09.2026).** Trzy nowe bloki
#: (6.A19, 6.B43, 6.B44) nie są uzupełnieniem kolejki na przeczekanie: każdy z nich
#: istnieje, bo właściciel **rozstrzygnął** 07.09.2026 pozycję, która stała dotąd
#: w „Czego agent nie ruszy bez decyzji". Zapadka jest tu potrzebna z tego samego
#: powodu co zawsze: decyzja właściciela, po której nikt nie napisał, jak ją wykonać,
#: wygląda w tabeli identycznie jak decyzja niepodjęta.
#: **Liczba przepisana, a nie dopisana obok — 101 → 106 (07.09.2026, drugie
#: uzupełnienie tego dnia).** Pięć bloków (6.A33, 6.D32, 6.D33, 6.D34, 6.D35) weszło
#: dlatego, że kolejka po scaleniu #375 i #377 miała **14 pozycji do wzięcia**, a dwa
#: dalsze zadania w robocie zbiłyby ją do **dwunastu, czyli RÓWNO do progu** — czyli
#: następne domknięcie zapaliłoby `test_the_queue_holds_at_least_a_day_of_work` na
#: czerwonym zestawie w cudzym pull requeście. `docs/TASKS.md` żąda liczenia zapasu
#: **na stan po**, nie na stan przed, i to jest ten commit.
#:
#: Żadna z pięciu pozycji nie jest wymyślona na miejscu: trzy wychodzą z pomiarów
#: wykonanych tego dnia (`reports/audyt-asercji.md` §7 nazwał 6.A33 wprost i świadomie
#: go nie zrobił), a dwie z ścieżek, które nie istnieją w drzewie — jedną z nich
#: znalazł niezależnie agent wykonujący 6.A30, próbując wykonać pole „Weryfikacja"
#: własnego bloku.
#: **Liczba przepisana, a nie dopisana obok — 106 → 111 (07.09.2026, trzecie
#: uzupełnienie tego dnia).** Kolejka zeszła po 6.D35 do **dwunastu, czyli RÓWNO do
#: progu** `MINIMUM_READY_ITEMS`, więc następne domknięcie zapaliłoby bramkę zapasu.
#: `CLAUDE.md` §8 mówi wtedy jedno: pierwszym zadaniem jest uzupełnienie kolejki.
#:
#: Wszystkie pięć pozycji (6.B45, 6.B46, 6.D36, 6.D37, 6.D38) wyszło z **pomiarów
#: wykonanych przy zadaniach tego dnia** i z sekcji „Zauważone przy okazji" ich
#: raportów — czyli z rzeczy, które ktoś zobaczył i świadomie nie tknął, bo nie były
#: jego pozycją. Żadna nie jest wymyślona na miejscu, i to jest warunek, pod którym
#: wolno je było dopisać: zadanie wymyślone, bo skończyła się kolejka, omija format
#: z sekcji 6 i ląduje w kodzie, którego nikt nie prosił o zmianę.
#: **Liczba przepisana, a nie dopisana obok — 112 → 118 (08.09.2026).** Sześć bloków
#: (6.D42 … 6.D47) i to JEST uzupełnienie kolejki, w warunkach, które `CLAUDE.md` §8
#: opisuje wprost. Powód jest policzony, nie wyczuty: `open_items` stało na
#: **trzynastu** przy progu dwunastu, a wśród pull requestów czekających na scalenie
#: **pięć** domyka po jednej pozycji. Pierwsze domknięcie zeszłoby RÓWNO do progu,
#: drugie pod próg — czyli bramka zapasu zapaliłaby się na pull requeście, który
#: wykonuje pracę. Po tym uzupełnieniu jest ich dziewiętnaście, więc po wszystkich
#: pięciu domknięciach zostaje czternaście.
#:
#: Wszystkie sześć wyszło z pomiarów wykonanych **przy scalaniu tych właśnie pull
#: requestów** — nie z pomysłów. Trzy z nich mierzą jedną rodzinę usterki, tę samą,
#: którą 6.D41 naprawiła w bramce kroku: przyrząd, który porównuje liczbę z progiem,
#: nie sprawdziwszy, czy dała się zmierzyć (6.D42), topologia jobów, przy której
#: pierwszy przebieg każdego pull requesta jest niemierzalny z konstrukcji (6.D43),
#: i pytanie, czy ponowiony job mierzy dzisiejszą bazę (6.D47).
#:
#: **Trzy kandydatury ODRZUCIŁEM pomiarem, i to jest część tej samej pracy.**
#: „Nieużywane pola `depth_m` i `interpolated` w `data/track/`" — mają jedenastu
#: i czterech czytelników. „Wznowienie przeglądu mutacyjnego kończy się kodem 1,
#: gdy wszystko jest policzone" — `KOD_WZNOWIENIE_KOMPLETNE` wynosi już 0.
#: „Bramka dokumentów nie widzi zdań poza `CLAUDE.md`" — obejmuje `docs/`,
#: `reports/` i `README.md`. Pozycja dopisana bez sprawdzenia wygląda w tabeli
#: identycznie jak pozycja prawdziwa, dopóki ktoś po nią nie sięgnie.
#:
#: **Liczba przepisana raz jeszcze — 118 → 119 (08.09.2026).** Jeden blok (6.D39),
#: i ten JEDEN nie jest uzupełnieniem kolejki — jest zapisem usterki, która **w tej
#: samej godzinie zatrzymała cztery joby CI**, a której log nie umiał nazwać. Blok
#: istnieje z tego samego powodu co przy decyzjach właściciela wyżej: usterka bez
#: bloku wygląda w tabeli identycznie jak usterka nieistniejąca, a ta zostawiła po
#: sobie jedno zdanie `zgłasza ''` i nic więcej. Zapasu ta pozycja NIE rusza —
#: zmierzone scaleniem na czystym drzewie: `open_items` bez zmiany, bo 6.D39 weszła
#: i wyszła w jednym commicie.
#:
#: **Liczba przepisana raz jeszcze — 119 → 120 (08.09.2026).** Jeden blok (6.D40),
#: i ten JEDEN nie jest uzupełnieniem kolejki — jest zapisem usterki, która
#: **zatrzymała dziewięć jobów CI naraz** i której żadna bramka nie widziała, bo
#: sonda pytała o jedną bibliotekę z dziesięciu i odpowiadała „wszystko na miejscu"
#: zgodnie z prawdą. Blok istnieje z tego samego powodu co wyżej: usterka bez bloku
#: wygląda w tabeli identycznie jak usterka nieistniejąca. Zapasu ta pozycja NIE
#: rusza, bo weszła i wyszła w jednym commicie.
#:
#: **Uwaga o scalaniu, PRZEPISANA, a nie dopisana obok.** Ta gałąź niosła zdanie,
#: że druga z pary 6.D39 / 6.D40 musi w rozwiązaniu konfliktu dać **113**. Było
#: prawdziwe, gdy w locie były tylko te dwie gałęzie; przed nimi weszły jednak
#: 6.D41 i sześć pozycji uzupełnienia kolejki, więc równość wypadła siedem wyżej.
#: Zdanie zostaje tu jako zapis tego, jak łatwo taka liczba się starzeje: właściwym
#: rozwiązaniem nigdy nie jest wpisanie zapamiętanej wartości, tylko POMIAR liczby
#: bloków w pliku i ustawienie zapadki na jego wynik.
#:
#: **Liczba przepisana raz jeszcze — 120 → 124 (08.09.2026, drugie uzupełnienie tego
#: dnia).** Cztery bloki (6.D48 … 6.D51), i powód jest znów POLICZONY: `open_items`
#: stało RÓWNO na dwunastu, czyli na podłodze, a czekająca pozycja 6.C4 domyka jedną —
#: czyli zeszłaby POD próg i bramka zapasu zapaliłaby się na pull requeście, który
#: wykonuje pracę. Po uzupełnieniu jest ich szesnaście.
#:
#: Wszystkie cztery wyszły z pomiarów wykonanych **tego dnia, przy innych pozycjach**,
#: a dwie opisują **moją własną pomyłkę**: 6.D48 bierze się z tego, że uznałem
#: Blendera za nieobecnego po `command -v`, gdy leżał w cache od 06.09.2026, a 6.D49
#: z nazwy testu, którą sam przemianowałem przy 6.A19, zostawiając martwy odsyłacz
#: w raporcie. Pozycja opisująca własny błąd jest warta tyle samo co każda inna:
#: bez wpisu wygląda w tabeli identycznie jak błąd nieistniejący.
#: **124 → 125 (08.09.2026, jeden blok).** Nowa pozycja **6.D52** wchodzi nie
#: z pomiaru na drzewie, a z **decyzji właściciela** z tego dnia: „zserializować joby
#: czasowe wobec renderów". Powód, dla którego jest to POZYCJA, a nie od razu zmiana
#: w workflowach, też jest zmierzony: dziesięć jobów stoi w dziesięciu OSOBNYCH plikach
#: workflowu, a `concurrency` nie występuje w żadnym, więc `needs:` — pierwszy
#: i oczywisty pomysł, nazwany w bloku 6.D43 — na tę serializację nie ma zastosowania.
#: Zostaje wspólna grupa `concurrency`, której zachowania w tym repozytorium nikt nie
#: odczytał, bo nie ma z czego. Decyzja właściciela zdjęła pytanie „czy wolno";
#: pytania „jak, żeby nie anulować jobu" nie zdejmuje, i to jest treść 6.D52.
#:
#: Zapadka jest tu **podniesiona na POMIAR** liczby bloków w pliku (125), nie na
#: wartość zapamiętaną z rozmowy — reguła wypisana trzy akapity wyżej obowiązuje
#: także wtedy, gdy dopisuje się jeden blok, a nie cztery.
MINIMUM_DETAIL_BLOCKS = 125

#: Zdanie, które musi stać w `docs/TASKS.md`, dopóki zapadka nie dojdzie do progu.
#: Gdy ktoś podniesie `MINIMUM_DOCUMENTED_ITEMS` do `MINIMUM_READY_ITEMS`, ma je
#: usunąć — inaczej plan niesie nieprawdę o samym sobie.
SHORTFALL_MARKER = "**Zapas udokumentowany:**"


def _tasks():
    with open(TASKS, encoding="utf-8") as handle:
        return handle.read()


def queue_items(text):
    """Numery pozycji kolejki, np. ['5.1', '6.A1'] — wiersze tabel `| 5.x |` i `| 6.x |`."""
    found = []
    for line in text.splitlines():
        match = re.match(r"^\|\s*(\d+\.[A-Za-z]?\d+)\s*\|", line)
        if match and match.group(1).startswith(QUEUE_PREFIXES):
            found.append(match.group(1))
    return found


def _section(text, heading, stop_prefixes):
    """Treść sekcji od `heading` do pierwszego kolejnego nagłówka z `stop_prefixes`."""
    start = text.find(heading)
    if start < 0:
        return ""
    rest = text[start + len(heading):]
    ends = [rest.find(prefix) for prefix in stop_prefixes]
    ends = [e for e in ends if e >= 0]
    return rest if not ends else rest[:min(ends)]


def blocked_section(text):
    """Treść sekcji „Czego agent nie ruszy bez decyzji"."""
    return _section(text, "### Czego agent nie ruszy bez decyzji", ["\n### "])


def closed_section(text):
    """Treść sekcji „Domknięte i zdjęte z kolejki".

    Zatrzymuje się na nagłówku CZWARTEGO poziomu też, nie tylko trzeciego: sekcja
    domknięć jest `####` i stoi wewnątrz fazy 5, więc szukanie samego `\n### `
    wciągnęłoby resztę fazy razem z jej tabelą pozycji — czyli wykluczyłoby
    z licznika dokładnie tę kolejkę, której ma pilnować.
    """
    return _section(text, "#### Domknięte i zdjęte z kolejki", ["\n### ", "\n#### "])


def ready_items(text):
    """Pozycje kolejki, które są PRACĄ: bez zablokowanych i bez domkniętych."""
    excluded = set(queue_items(blocked_section(text))) | set(queue_items(closed_section(text)))
    return [item for item in queue_items(text) if item not in excluded]


def detail_sections(text):
    """Bloki `##### <numer> · tytuł` → treść, np. {'6.A8': '##### 6.A8 · …\n- …'}.

    Blok kończy się na PIERWSZYM kolejnym nagłówku dowolnego poziomu, nie tylko
    piątego: sekcja szczegółów jest ostatnia w fazie 6 i sąsiaduje z `### Czego agent
    nie ruszy bez decyzji`, więc szukanie samego `\n##### ` wciągnęłoby do ostatniej
    pozycji całą listę decyzji właściciela — i „Zależy od" znalazłoby się tam, gdzie
    go nie ma.
    """
    lines = text.splitlines()
    heads = [(i, m.group(1)) for i, line in enumerate(lines)
             for m in [re.match(r"^#####\s+(\d+\.[A-Za-z]?\d+)\s*·", line)] if m]
    sections = {}
    for position, (start, number) in enumerate(heads):
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("#"):
                end = j
                break
        sections[number] = "\n".join(lines[start:end])
    return sections


def missing_fields(body):
    """Których z sześciu pól brakuje w bloku — pusta lista znaczy komplet.

    Pole musi mieć TREŚĆ, nie tylko nagłówek. `- **Weryfikacja:**` bez niczego dalej
    jest dokładnie tym, przed czym `CLAUDE.md` §6 ostrzega: polem odhaczonym zamiast
    wypełnionego.
    """
    missing = []
    for field in REQUIRED_FIELDS:
        marker = "- **%s:**" % field
        at = body.find(marker)
        if at < 0:
            missing.append(field)
            continue
        rest = body[at + len(marker):]
        nxt = re.search(r"\n- \*\*", rest)
        if not (rest if nxt is None else rest[:nxt.start()]).strip():
            missing.append(field)
    return missing


def open_items(text):
    """Pozycje kolejki, które są pracą **DO WZIĘCIA**: bez tych z adnotacją ZROBIONE.

    **DLACZEGO TO NIE JEST `ready_items`.** `ready_items` odsiewa zablokowane i domknięte,
    ale przepuszcza pozycję, która **została wykonana i została w tabeli** — a takich jest
    dziś dziesięć. Zostają tam nie przez niedopatrzenie, tylko z powodu zapisanego przy
    każdej z nich: zdjęcie udokumentowanej pozycji zbijało `MINIMUM_DOCUMENTED_ITEMS`,
    a tę wolno tylko podnosić. Reguła zapasu obróciła się więc przeciwko sobie: chroniąc
    licznik, kazała trzymać w kolejce pracę już skończoną.

    Zmierzone 05.09.2026 po scaleniu #271: pozycji pracy jest **24**, z czego **10** nosi
    `ZROBIONE`, więc realnie do wzięcia jest **14**. Zapadka stała wtedy na 12 i była
    zielona — mimo że udokumentowanych i **jednocześnie niezrobionych** pozycji było
    **pięć**. Gwarancja „doby pracy przed agentem" mierzyła w większości wspomnienia
    po pracy.
    """
    zrobione = {item for item in ready_items(text)
                if DONE_ROW_MARKER in (queue_row(text, item) or "")}
    return [item for item in ready_items(text) if item not in zrobione]


def documented_items(text):
    """Pozycje liczone do zapasu: **niezrobione** i z kompletem sześciu pól.

    Do 05.09.2026 liczyło to `ready_items`, czyli także pozycje wykonane i zostawione
    w tabeli. Zdanie jest przepisane, a nie dopisane obok, bo zmienia się **zbiór**,
    który zapadka mierzy — i dlatego jej liczba po tej zmianie nie jest porównywalna
    z liczbą sprzed niej.
    """
    sections = detail_sections(text)
    return [item for item in open_items(text)
            if item in sections and not missing_fields(sections[item])]


def test_tasks_file_exists():
    assert os.path.isfile(TASKS), TASKS


def test_the_reserve_rule_is_written_down():
    text = _tasks()
    assert "### Reguła zapasu" in text, "reguła zapasu zniknęła z planu"
    assert "24 godzin" in text or "24 godziny" in text, "reguła bez liczby godzin"


def test_the_queue_holds_at_least_a_day_of_work():
    # `open_items`, nie `ready_items`: pozycja z adnotacją ZROBIONE stoi w tabeli
    # z powodu zapadki, a nie dlatego, że jest pracą. Doba pracy przed agentem
    # liczy się z tego, co da się wziąć.
    items = open_items(_tasks())
    assert len(items) >= MINIMUM_READY_ITEMS, (
        f"kolejka ma {len(items)} pozycji przy progu {MINIMUM_READY_ITEMS}; "
        "pierwszym zadaniem jest uzupełnienie fazy 6, nie zatrzymanie się")


def test_queue_numbers_are_unique():
    # Dwie pozycje o tym samym numerze to jedna pozycja policzona dwa razy —
    # zapas wyglądałby na większy, niż jest.
    items = queue_items(_tasks())
    assert len(items) == len(set(items)), (
        f"powtórzone numery: {[i for i in set(items) if items.count(i) > 1]}")


def test_every_queue_item_says_why_it_needs_no_decision():
    # Pozycja bez tej kolumny to pozycja, której nikt nie sprawdził pod kątem tego,
    # czy naprawdę da się ją zrobić bez właściciela. Taka trafia do kolejki i blokuje
    # ją dopiero wtedy, gdy agent po nią sięgnie.
    text = _tasks()
    for line in text.splitlines():
        if re.match(r"^\|\s*\d+\.[A-Za-z]?\d+\s*\|", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) >= 3, f"pozycja bez kolumny uzasadnienia: {line[:60]}"
            assert cells[2], f"puste uzasadnienie: {line[:60]}"


def test_blocked_work_is_not_counted_as_queue():
    # Kontrola negatywna do progu. Gdyby licznik zaglądał również do sekcji
    # „Czego agent nie ruszy bez decyzji", zapas rósłby o zadania, których
    # agent z definicji nie może wykonać — i bramka byłaby zielona przy pustej kolejce.
    blocked = blocked_section(_tasks())
    assert blocked, "sekcja o decyzjach właściciela zniknęła"
    assert not queue_items(blocked), (
        "pozycje z sekcji decyzji właściciela wpadają do licznika kolejki")


def test_closed_work_is_not_counted_as_queue():
    """Domknięcie pozycji ma zapas OBNIŻAĆ, a nie podnosić.

    Wiersz `| 6.C1 | ... |` wygląda dla parsera identycznie niezależnie od tego,
    w której tabeli stoi. Bez tego wykluczenia przeniesienie pozycji do sekcji
    domknięć zostawiało ją w liczniku — zmierzone 04.09.2026 przy zamykaniu 5.5,
    6.C1 i 6.C2: licznik pokazywał 28 przy 25 pozycjach realnych, czyli dokładnie
    tyle, ile przed domknięciem czegokolwiek.
    """
    text = _tasks()
    closed = closed_section(text)
    assert closed, "sekcja domknięć zniknęła z planu"

    numbers = queue_items(closed)
    assert numbers, "sekcja domknięć nie wymienia ani jednego numeru"

    ready = ready_items(text)
    for number in numbers:
        assert number not in ready, f"{number} jest domknięte, a nadal liczy się do zapasu"
    assert len(ready) < len(queue_items(text)), (
        "wykluczenie niczego nie odejmuje — licznik liczy domknięte razem z gotowymi")


def test_the_closed_section_stands_below_the_queue_it_is_carved_out_of():
    """Wycinanie sekcji domknięć nie może zabrać ze sobą tabeli kolejki.

    Dziś nie zabiera — ale NIE dzięki liście nagłówków zamykających, tylko dzięki
    POŁOŻENIU: sekcja `#### Domknięte` stoi pod tabelą fazy 5, więc poniżej niej
    nie ma już ani jednego wiersza `| 5.x |`. Pierwsza wersja tego testu twierdziła,
    że pilnuje listy nagłówków, i była fałszywa: usunięcie `"\n#### "` z `closed_section`
    NIE wywracało jej ani razu, bo nie było czego pochłonąć. Zmierzone, nie wyczytane.

    Ten test pilnuje więc tego, co naprawdę trzyma licznik w ryzach. Gdyby sekcja
    domknięć trafiła NAD tabelę, wycinanie zabrałoby całą kolejkę fazy 5 i próg
    spełniałby się na samej fazie 6 — czyli bramka byłaby zielona przy zapasie
    mniejszym, niż pokazuje.
    """
    text = _tasks()
    assert "#### Domknięte i zdjęte z kolejki" in text, "sekcja domknięć zniknęła z planu"

    # Wprost: wycięty blok nie ma prawa zawierać NAGŁÓWKA tabeli kolejki. Gdyby
    # sekcja domknięć stała nad tabelą, wycinanie zabrałoby nagłówek i wszystkie
    # wiersze pod nim — i to jest jedyny objaw, który widać z samego pliku.
    carved = closed_section(text)
    assert QUEUE_TABLE_HEADER not in carved, (
        "sekcja domknięć stoi NAD tabelą kolejki i wycinanie zabiera ją razem z sobą")

    # I skutek tego położenia: każda niedomknięta pozycja 5.x zostaje w zapasie.
    closed_numbers = set(queue_items(carved))
    ready = ready_items(text)
    phase_five = [i for i in queue_items(text)
                  if i.startswith("5.") and i not in closed_numbers]
    assert phase_five, "faza 5 nie ma ani jednej niedomkniętej pozycji"
    for item in phase_five:
        assert item in ready, f"{item} z fazy 5 wypadło z zapasu"


def test_the_parser_actually_parses():
    # Kontrole negatywne samego licznika. Bez nich testy wyżej przechodziłyby także
    # wtedy, gdyby `queue_items` zwracał pustą listę na wszystkim albo łapał co popadnie.
    assert queue_items("| 5.1 | coś | bo tak |") == ["5.1"]
    assert queue_items("| 6.A1 | coś | bo tak |") == ["6.A1"]
    assert queue_items("| 6.B12 | coś | bo tak |") == ["6.B12"]
    assert queue_items("| # | zadanie | dlaczego |") == [], "nagłówek tabeli nie jest pozycją"
    assert queue_items("| 4.1 | stara faza |") == [], "faza spoza kolejki nie liczy się"
    assert queue_items("tekst 5.1 w zdaniu") == [], "wzmianka w prozie nie jest pozycją"
    assert queue_items("|---|---|---|") == [], "separator tabeli nie jest pozycją"


def test_the_threshold_is_not_trivially_satisfied():
    # Próg, który spełnia się sam, nie jest progiem. Ten test pada, gdyby ktoś
    # obniżył `MINIMUM_READY_ITEMS` do wartości, przy której bramka nigdy nie zaświeci.
    assert MINIMUM_READY_ITEMS >= 12, (
        "próg poniżej dwunastu pozycji przestaje odpowiadać dobie pracy")


# ---------------------------------------------------------------------------
# Format pozycji, a nie tylko jej liczba.
# ---------------------------------------------------------------------------


def test_the_detail_scan_actually_finds_something():
    """Bramka bez przedmiotu ma PAŚĆ, nie przechodzić na pustym zbiorze.

    To jest ta sama pułapka, którą ten plik już raz złapał przy sekcji domknięć,
    tylko o poziom wyżej. Gdyby ktoś zmienił poziom nagłówka `#####` na `####`,
    przeniósł szczegóły do osobnego pliku albo wyciął całą sekcję — `detail_sections`
    zwróciłoby `{}`, a test „każdy blok ma sześć pól" byłby zielony, bo nie miałby
    czego sprawdzić. Zmierzone 05.09.2026: wycięcie 15 802 znaków tej sekcji
    przechodziło 1467/1467.
    """
    sections = detail_sections(_tasks())
    assert len(sections) >= MINIMUM_DOCUMENTED_ITEMS, (
        f"skan znalazł {len(sections)} bloków szczegółów przy zapadce "
        f"{MINIMUM_DOCUMENTED_ITEMS}; albo sekcja z sześcioma polami zniknęła "
        "lub zmieniła kształt nagłówka i bramka przestała mieć na co patrzeć, "
        "albo ktoś podniósł zapadkę bez dopisania bloków")


def test_every_detail_block_carries_all_six_fields():
    # Blok, który ma nagłówek i trzy pola, jest gorszy niż brak bloku: wygląda
    # na wypełniony i przechodzi wzrokiem. Sześć pól albo żadnego.
    for number, body in sorted(detail_sections(_tasks()).items()):
        missing = missing_fields(body)
        assert not missing, f"{number} bez pól: {', '.join(missing)}"


def test_no_detail_block_describes_a_number_that_left_the_tables():
    # Odwrotna strona tego samego rozjazdu: opis został, wiersz zniknął.
    # Taki blok wygląda jak zadanie do wzięcia, a nie ma go w żadnej kolejce.
    text = _tasks()
    numbers = set(queue_items(text))
    for number in sorted(detail_sections(text)):
        assert number in numbers, (
            f"blok szczegółów {number} nie ma wiersza w żadnej tabeli")


def test_the_documented_reserve_does_not_regress():
    """Zapadka na liczbie pozycji, które naprawdę da się wziąć.

    `MINIMUM_READY_ITEMS` mówi, ile pozycji ktoś WPISAŁ. Ta liczba mówi, ile z nich
    niesie sześć pól, czyli ile agent może wziąć bez dopytywania właściciela.
    Zmierzone 05.09.2026 po dopisaniu czterech bloków: **12 z 29**. Poprzednie wersje
    tego zdania mówiły 8 z 31 i 8 z 33 (`b41c158`) — mianownik zmieniał się dwa razy
    bez ruchu zapadki, bo 6.B11 i 6.B12 wyszły do tabeli domknięć. Wolno tylko
    podnosić — a podnosi się ją, dopisując pola tam, gdzie da się je ODCZYTAĆ
    z `docs/`, `reports/` i `data/`, nie zmyślając ich.
    """
    text = _tasks()
    documented = documented_items(text)
    assert len(documented) >= MINIMUM_DOCUMENTED_ITEMS, (
        f"pozycji z kompletem sześciu pól jest {len(documented)} "
        f"przy zapadce {MINIMUM_DOCUMENTED_ITEMS}: "
        f"{sorted(set(ready_items(text)) - set(documented))} są bez kompletu")


def test_the_documented_shortfall_is_written_down_while_it_lasts():
    """Różnica między zapadką a progiem nie ma prawa zniknąć po cichu.

    **Ten docstring jest przepisany, a nie dopisany obok.** Poprzednia wersja mówiła
    „Dziś zapadka stoi na 8, a próg zapasu na 12 — cztery pozycje kolejki są wierszem
    tabeli bez opisu, jak je wykonać", i to już nieprawda: 05.09.2026 doszły bloki
    6.A7, 6.B1, 6.B2 i 6.D2, zapadka zrównała się z progiem, a akapit o niedoborze
    **zniknął z `docs/TASKS.md`** — czego pilnuje gałąź `else` tego testu.

    **Od 06.09.2026 warunek patrzy na POMIAR, nie na stałą.** Wcześniej porównywał
    `MINIMUM_DOCUMENTED_ITEMS` z `MINIMUM_READY_ITEMS`, czyli dwie liczby wpisane
    w ten plik — a po rozdzieleniu podłogi od zapadki pierwsza z nich stoi celowo
    nisko i porównanie byłoby zawsze prawdziwe, czyli martwe. Teraz liczy się
    rzeczywisty zapas: akapit ma stać w planie dokładnie wtedy, gdy zapas jest poniżej
    progu doby pracy, i zniknąć, gdy go dogoni.
    Plan, który po domknięciu luki nadal ją opisuje, jest tak samo nieprawdziwy jak
    plan, który jej nigdy nie opisał; ten test łapie oba te stany.
    """
    text = _tasks()
    reserve = len(documented_items(text))
    if reserve < MINIMUM_READY_ITEMS:
        assert SHORTFALL_MARKER in text, (
            f"zapas udokumentowany to {reserve} przy progu {MINIMUM_READY_ITEMS}, "
            "a plan o tym milczy")
    else:
        assert SHORTFALL_MARKER not in text, (
            "zapas doszedł do progu, a plan nadal opisuje lukę")


def test_the_ratchet_cannot_be_set_above_what_it_guards():
    # Zapadka wyższa od progu zapasu byłaby wymaganiem bez pokrycia w regule:
    # `docs/TASKS.md` żąda dwunastu pozycji, nie dwudziestu udokumentowanych.
    assert 0 < MINIMUM_DOCUMENTED_ITEMS < MINIMUM_READY_ITEMS, (
        "podłoga zapasu stoi poza przedziałem (0, próg doby pracy)")
    assert MINIMUM_DETAIL_BLOCKS > 0, "zapadka bloków wyzerowana"


def test_closed_items_are_exempt_from_the_six_fields_on_purpose():
    """Rozstrzygnięcie wprost: pozycja ODHACZONA nie ma sześciu pól i nie ma ich mieć.

    `docs/TASK-TEMPLATE.md` daje pozycji niezrobionej sześć pól, a zrobionej dokłada
    „Wynik". W tabelach 5.x/6.x odpowiednikiem „Wyniku" jest trzecia kolumna tabeli
    domknięć — `| # | co było | gdzie zostało zrobione |`. Wymaganie kompletu
    dotyczy więc dokładnie `ready_items`, i ten test pilnuje, żeby to zwolnienie
    było ŻYWE: gdyby wszystkie domknięte numery miały nagle bloki szczegółów,
    zwolnienie byłoby martwym zapisem i nikt by nie zauważył, że przestało cokolwiek
    znaczyć.
    """
    text = _tasks()
    closed = queue_items(closed_section(text))
    assert closed, "sekcja domknięć nie wymienia ani jednego numeru"

    sections = detail_sections(text)
    without = [n for n in closed if n not in sections]
    assert without, (
        "każdy domknięty numer ma blok szczegółów — zwolnienie z sześciu pól "
        "przestało cokolwiek zwalniać")

    documented = set(documented_items(text))
    for number in closed:
        assert number not in documented, (
            f"{number} jest domknięte, a liczy się do zapasu udokumentowanego")

    # I to, co domknięta pozycja mieć MUSI zamiast sześciu pól: wskazanie, gdzie
    # została zrobiona. Pusta trzecia kolumna zamieniłaby tabelę domknięć
    # w listę numerów bez śladu po pracy.
    for line in closed_section(text).splitlines():
        if re.match(r"^\|\s*\d+\.[A-Za-z]?\d+\s*\|", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) >= 3 and cells[2], (
                f"domknięta pozycja bez wskazania, gdzie ją zrobiono: {line[:60]}")


def test_the_field_parser_actually_parses():
    # Kontrole negatywne samego czytnika pól. Bez nich testy wyżej przechodziłyby
    # także wtedy, gdyby `missing_fields` zwracał pustą listę na wszystkim.
    complete = "\n".join("- **%s:** treść." % f for f in REQUIRED_FIELDS)
    assert missing_fields(complete) == []
    assert missing_fields("") == list(REQUIRED_FIELDS), "pusty blok ma być bez pól"
    assert missing_fields(complete.replace("- **Wyjście:** treść.", "")) == ["Wyjście"]
    assert missing_fields(complete.replace("- **Weryfikacja:** treść.",
                                           "- **Weryfikacja:**")) == ["Weryfikacja"], \
        "sam nagłówek pola bez treści nie jest polem"
    assert missing_fields("Wejście: bez pogrubienia") == list(REQUIRED_FIELDS), \
        "wzmianka w prozie nie jest polem"

    # I czytnik bloków.
    sample = ("##### 6.Z9 · tytuł\n- **Wejście:** a\n"
              "### inny nagłówek\n- **Wyjście:** nie moje\n")
    parsed = detail_sections(sample)
    assert list(parsed) == ["6.Z9"], parsed
    assert "nie moje" not in parsed["6.Z9"], "blok przelewa się przez nagłówek"
    assert detail_sections("#### 6.Z9 · zły poziom") == {}, \
        "nagłówek innego poziomu nie jest blokiem szczegółów"
    assert detail_sections("##### T-010 · nie numer kolejki") == {}



def test_the_documented_ratchet_does_not_lag_behind_the_file():
    """Zapadka na liczbę NAPISANYCH bloków ma nadążać za plikiem.

    **Ten docstring jest przepisany, a nie dopisany obok.** Poprzednia wersja pilnowała
    `documented_items`, czyli pozycji udokumentowanych i niezrobionych — wielkości,
    która maleje, gdy praca jest wykonywana. Od 06.09.2026 zapadka patrzy na
    `detail_sections`: bloki napisane, niezależnie od tego, czy pozycja jest już
    domknięta. Powód rozdzielenia stoi przy `MINIMUM_DOCUMENTED_ITEMS`.

    Ochrona zostaje ta sama i z tego samego powodu co dawniej. Zmierzone 05.09.2026
    na `8b7b767`: dopisanie dziewiątego bloku **przechodziło cały zestaw**, 1475/1475,
    a zapadka zostawała na ósemce i od tej chwili zwalniała jedną opisaną pozycję.
    Ten test wymusza podniesienie stałej w tym samym commicie, w którym rośnie liczba
    bloków.
    """
    blocks = [item for item, body in detail_sections(_tasks()).items()
              if not missing_fields(body)]
    assert MINIMUM_DETAIL_BLOCKS >= len(blocks), (
        f"bloków z kompletem sześciu pól jest {len(blocks)}, a zapadka stoi na "
        f"{MINIMUM_DETAIL_BLOCKS} — podnieś ją do {len(blocks)} w tym samym commicie, "
        "w którym dopisujesz blok")
    assert len(blocks) >= MINIMUM_DETAIL_BLOCKS, (
        f"bloków jest {len(blocks)} przy zapadce {MINIMUM_DETAIL_BLOCKS} — "
        "któryś zniknął albo stracił jedno z sześciu pól")


def test_the_reserve_floor_falls_when_work_is_done_and_the_ratchet_does_not():
    """Dwie liczby, dwa zachowania — i to jest cała treść rozdzielenia.

    **Skąd.** Do 06.09.2026 jedna stała niosła obie role. Po zmianie liczenia z #272
    sprzeczność zapaliła bramkę dwa razy pod rząd, przy 6.D4 i przy 6.B2: domknięcie
    udokumentowanej pozycji zbijało licznik, więc **wykonanie pracy** wywracało zestaw.
    Zaspokoić to dało się tylko dopisaniem nowego bloku w tym samym commicie, a pozycji
    bez bloku zostały wtedy dwie — po ich zużyciu bramki nie dałoby się już spełnić.

    Ten test przybija różnicę na sztucznym planie, więc nie zależy od tego, ile pozycji
    stoi dziś w `docs/TASKS.md`.
    """
    def plan(zrobione):
        znacznik = f"**{DONE_ROW_MARKER} w #1** — " if zrobione else ""
        return (
            "## Faza 6\n\n"
            "| # | zadanie | dlaczego bez decyzji | rozmiar |\n"
            "|---|---|---|---|\n"
            f"| 6.X1 | {znacznik}**Coś** | powód | S |\n\n"
            "##### 6.X1 · Coś\n\n"
            "- **Skąd:** stąd.\n- **Wejście:** plik.\n- **Wyjście:** plik.\n"
            "- **Weryfikacja:** polecenie.\n- **Skończone, gdy:** liczba.\n"
            "- **Poza zakresem:** reszta.\n- **Zależy od:** nic.\n")

    otwarte, domkniete = plan(False), plan(True)

    # 1. Zapas maleje, gdy pozycja zostaje domknięta — i tak ma być.
    assert len(documented_items(otwarte)) == 1, documented_items(otwarte)
    assert len(documented_items(domkniete)) == 0, documented_items(domkniete)

    # 2. Liczba NAPISANYCH bloków się nie zmienia — blok stoi tam dalej.
    assert len(detail_sections(otwarte)) == len(detail_sections(domkniete)) == 1

    # 3. Podłoga stoi wyraźnie niżej od progu doby pracy, więc domknięcie jednej
    #    pozycji nie wywraca zestawu. Gdyby ktoś podniósł ją do progu, wróciłby
    #    dokładnie ten defekt, który to rozdzielenie usuwa.
    assert MINIMUM_DOCUMENTED_ITEMS < MINIMUM_READY_ITEMS, (
        "podłoga zapasu zrównana z progiem doby pracy — domknięcie udokumentowanej "
        "pozycji znowu będzie wywracać zestaw")


def test_no_detail_block_carries_the_field_of_a_finished_entry():
    """Pozycja ZROBIONA ma inne pola i nie ma prawa zostać w zapasie.

    `test_closed_items_are_exempt_from_the_six_fields_on_purpose` rozstrzyga
    przypadek, w którym pozycja **przeniosła się** do tabeli domknięć. Zostaje
    przypadek odwrotny i cichszy: pozycja została zrobiona, ktoś dopisał jej wynik
    do bloku szczegółów i **nie ruszył** wiersza w tabeli kolejki. Blok ma wtedy
    komplet sześciu pól, więc liczy się do `documented_items`, a pracy już nie ma —
    licznik znów pokazuje więcej zapasu, niż jest.

    Miara jest ta sama, którą posługuje się `docs/TASK-TEMPLATE.md`: pole „Wynik",
    dokładane do wpisu odhaczonego. Zmierzone 05.09.2026 na tym drzewie: wpisów
    `### [x]` jest **17**, **żaden** nie ma pola „Skończone, gdy", a **14** ma
    „Wynik" — to pole jest więc jednoznacznym znacznikiem wpisu zamkniętego,
    a nie przypadkowym słowem. Przed odhaczeniem T-212 (#137, stało `[ ]` przez
    dwanaście scaleń) i T-906 (#209) było 15 wpisów i 12 pól.
    """
    text = _tasks()
    ready = set(ready_items(text))
    marker = "- **%s:**" % DONE_ONLY_FIELD
    for number, body in sorted(detail_sections(text).items()):
        if number in ready:
            assert marker not in body, (
                "%s ma pole %s, czyli jest zrobione, a jego wiersz nadal stoi "
                "w tabeli kolejki i liczy sie do zapasu; miejsce takiego numeru "
                "jest w sekcji domkniec" % (number, DONE_ONLY_FIELD))


def test_the_finished_entry_field_is_the_one_the_template_adds():
    # Kontrola negatywna do miary wyżej. Gdyby `DONE_ONLY_FIELD` przestało być
    # polem, którego szablon NIE wymaga od pozycji niezrobionej, test wyżej albo
    # wywracałby każdy poprawny blok, albo nie zapalałby się nigdy.
    assert DONE_ONLY_FIELD not in REQUIRED_FIELDS, (
        "pole wpisu zrobionego trafiło do sześciu pól wymaganych — "
        "wtedy zakaz wyżej wywraca każdy poprawny blok")
    assert "**%s:**" % DONE_ONLY_FIELD in _tasks(), (
        "pole wpisu zrobionego zniknęło z całego planu — miara straciła desygnat")


#: Napis, którym wiersz tabeli mówi, że pozycja jest już wykonana, a stoi w kolejce
#: wyłącznie z powodu zapadki. Wzór ustalił właściciel 05.09.2026 dla 6.D6 i powtarzają
#: go 6.B10, 6.B1, 6.B8 i 6.D5.
DONE_ROW_MARKER = "ZROBIONE"


def declared_report_outputs(body):
    """Ścieżki `reports/*.md` wymienione w polu **Wyjście** bloku szczegółów."""
    at = body.find("- **Wyjście:**")
    if at < 0:
        return []
    rest = body[at:]
    nxt = re.search(r"\n- \*\*", rest)
    field = rest if nxt is None else rest[:nxt.start()]
    return sorted(set(re.findall(r"reports/[A-Za-z0-9._-]+\.md", field)))


def queue_row(text, number):
    """Wiersz tabeli kolejki dla tego numeru — albo pusty napis."""
    for line in text.splitlines():
        match = re.match(r"^\|\s*(\d+\.[A-Za-z]?\d+)\s*\|", line)
        if match and match.group(1) == number:
            return line
    return ""


def finished_but_still_silent(text, exists=os.path.exists):
    """Pozycje, których WSZYSTKIE zadeklarowane raporty istnieją, a wiersz milczy.

    `exists` jest wstrzykiwane, żeby kontrola negatywna mogła podstawić własne
    odpowiedzi zamiast tworzyć pliki w `reports/` — test, który zaśmieca katalog,
    którego pilnuje inna bramka, jest gorszy niż brak testu.
    """
    sections = detail_sections(text)
    late = []
    for number in ready_items(text):
        outputs = declared_report_outputs(sections.get(number, ""))
        if not outputs:
            continue
        if all(exists(os.path.join(ROOT, path)) for path in outputs):
            if DONE_ROW_MARKER not in queue_row(text, number):
                late.append(f"{number}: {', '.join(outputs)} już istnieje")
    return late


def test_a_documented_item_whose_reports_all_exist_says_so_in_its_row():
    """Kolejka nie ma prawa opisywać stanu sprzed pracy, która już weszła.

    **Skąd ta bramka.** 05.09.2026, w jednej sesji, SZEŚĆ pozycji okazało się
    wykonanych, a wszystkie stały w kolejce jak otwarte: 5.1 (#184), 5.2 (`470632d`),
    5.8 i 6.B8 (`f5126a3`, jedno wykonanie zamknęło obie), 6.D5 (#259) oraz 6.B3
    (LOD dla B i E istnieje od T-210). Cztery z nich wyszły dopiero wtedy, gdy ktoś
    wziął pozycję do zrobienia i **pomiar obalił jej założenie** — czyli najdroższym
    możliwym sposobem. `docs/TASKS.md` mówi wprost: „Aktualizacja tej listy jest
    częścią pracy, nie dodatkiem do niej", i to zdanie nie miało dotąd żadnej bramki.

    **Co ta bramka łapie.** Pozycję udokumentowaną, której pole **Wyjście** nazywa
    raporty, i wszystkie te raporty już leżą w `reports/`. Wtedy albo praca jest
    zrobiona i wiersz ma to mówić, albo pole **Wyjście** obiecuje plik, który znaczy
    co innego niż to, co powstało — i jedno, i drugie jest usterką planu.

    **Czego NIE łapie, i to jest granica, nie przeoczenie.** Pozycji bez bloku
    sześciu pól (5.1 i 5.2 były właśnie takie — ich dowodem był commit, nie plik),
    pozycji, których wyjściem jest kod bez raportu, ani pozycji, której raport
    **rozszerza** plik już istniejący. Ten ostatni przypadek jest jedynym źródłem
    fałszywego trafienia i ma tanie lekarstwo: pole **Wyjście** ma wtedy nazwać nowy
    plik albo sekcję, a nie cały istniejący raport — czyli dokumentację, która i tak
    jest lepsza.
    """
    late = finished_but_still_silent(_tasks())
    assert not late, (
        "kolejka opisuje stan sprzed pracy, która już weszła — wiersz ma dostać "
        f"adnotację „{DONE_ROW_MARKER} w #NNN” albo wyjść do tabeli domknięć: {late}")


def test_the_finished_item_detector_reacts_to_both_halves_of_its_condition():
    """Kontrola do bramki wyżej — obie połowy warunku, każda osobno.

    Detektor stoi na koniunkcji „raport istnieje" AND „wiersz milczy". Test, który
    ćwiczy tylko jedną z nich, przechodziłby także dla detektora zwracającego stałą.
    """
    plan = (
        "| # | zadanie |\n"
        "| 6.Z1 | **Coś do zrobienia** | bo tak | M |\n"
        "| 6.Z2 | **ZROBIONE w #999.** Coś innego | bo tak | M |\n"
        "\n##### 6.Z1 · pozycja bez adnotacji\n"
        "- **Wejście:** cokolwiek\n- **Wyjście:** `reports/zmyslony.md`\n"
        "- **Weryfikacja:** cokolwiek\n- **Skończone, gdy:** cokolwiek\n"
        "- **Poza zakresem:** cokolwiek\n- **Zależy od:** nic.\n"
        "\n##### 6.Z2 · pozycja z adnotacją\n"
        "- **Wejście:** cokolwiek\n- **Wyjście:** `reports/zmyslony.md`\n"
        "- **Weryfikacja:** cokolwiek\n- **Skończone, gdy:** cokolwiek\n"
        "- **Poza zakresem:** cokolwiek\n- **Zależy od:** nic.\n")

    # 1. Raport istnieje, wiersz milczy → trafienie, i tylko na tej pozycji.
    late = finished_but_still_silent(plan, exists=lambda path: True)
    assert [entry.split(":")[0] for entry in late] == ["6.Z1"], late

    # 2. Ten sam plan, ale raportu nie ma → cisza. Bez tego bramka mogłaby zgłaszać
    #    każdą pozycję z polem Wyjście i nadal wyglądać na działającą.
    assert finished_but_still_silent(plan, exists=lambda path: False) == []

    # 3. Pole Wyjście bez ścieżki do raportu jest poza zasięgiem — pozycja z samym
    #    kodem na wyjściu nie ma jak zapalić tej bramki.
    assert declared_report_outputs("- **Wyjście:** testy w `tools/tests/`.") == []
    assert declared_report_outputs("- **Wyjście:** `reports/a.md` i `reports/b.md`.") == [
        "reports/a.md", "reports/b.md"]

    # 4. Pole Wyjście kończy się na następnym polu, a nie na końcu bloku: raport
    #    wymieniony w „Weryfikacji" albo w „Poza zakresem" NIE jest wyjściem pozycji.
    assert declared_report_outputs(
        "- **Wyjście:** testy.\n- **Weryfikacja:** patrz `reports/cudzy.md`.") == []


def test_the_reserve_counts_work_to_take_not_work_already_done():
    """Pozycja z adnotacją ZROBIONE nie liczy się ani do zapasu, ani do zapadki.

    **Skąd ta bramka.** Do 05.09.2026 obie liczby brały `ready_items`, czyli wszystko,
    co stoi w tabeli jako praca — razem z pozycjami wykonanymi i zostawionymi tam
    **z powodu tej właśnie zapadki**. Reguła zapasu obróciła się przeciwko sobie:
    chroniąc licznik, kazała trzymać w kolejce pracę skończoną, aż udokumentowanych
    i jednocześnie niezrobionych zostało pięć przy zapadce stojącej na dwunastu
    i świecącej na zielono.

    Ta bramka pilnuje, żeby liczenie nie wróciło po cichu do starego. Sprawdza obie
    strony na tym samym tekście, więc nie da się jej spełnić przez samo `ready_items`.
    """
    text = _tasks()
    gotowe = ready_items(text)
    do_wziecia = open_items(text)
    zrobione = [item for item in gotowe if item not in do_wziecia]

    # 1. Zbiory są w tej relacji, w jakiej mają być.
    assert set(do_wziecia) <= set(gotowe), "open_items wypuszcza pozycję spoza kolejki"
    assert zrobione, (
        "żadna pozycja kolejki nie nosi dziś adnotacji ZROBIONE — jeśli to prawda, "
        "ta bramka straciła powód i trzeba ją zdjąć, a nie zostawić jako obrzęd")

    # 2. Każda odsiana NAPRAWDĘ nosi znacznik, a nie wypadła z innego powodu.
    for item in zrobione:
        assert DONE_ROW_MARKER in (queue_row(text, item) or ""), item

    # 3. Zapadka mierzy pozycje DO WZIĘCIA. Bez tego zdania `documented_items`
    #    mogłoby wrócić do `ready_items`, a wszystkie liczby dalej by się zgadzały.
    assert set(documented_items(text)) <= set(do_wziecia), (
        "zapadka liczy pozycję, której nie da się wziąć: "
        f"{sorted(set(documented_items(text)) - set(do_wziecia))}")


def test_the_open_item_filter_reacts_to_the_marker_and_not_to_something_else():
    """Kontrola detektora: bez niej `open_items` mogłoby odsiewać cokolwiek.

    Trzy wiersze na jednym sztucznym planie. Pierwszy nosi znacznik i ma wypaść,
    drugi go nie nosi i ma zostać, trzeci zawiera słowo o podobnym kształcie
    („do zrobienia") i **też ma zostać** — inaczej filtr łapałby prozę zamiast
    adnotacji.
    """
    plan = (
        "## Faza 6\n\n"
        "| # | zadanie | dlaczego bez decyzji | rozmiar |\n"
        "|---|---|---|---|\n"
        "| 6.X1 | **ZROBIONE w #999** — treść pierwotna: coś tam | powód | S |\n"
        "| 6.X2 | **Coś otwartego** | powód | M |\n"
        "| 6.X3 | **Coś do zrobienia jeszcze** | powód | L |\n")
    assert sorted(queue_items(plan)) == ["6.X1", "6.X2", "6.X3"], queue_items(plan)
    assert sorted(open_items(plan)) == ["6.X2", "6.X3"], open_items(plan)

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
