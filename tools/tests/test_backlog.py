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
CLAUDE = os.path.join(ROOT, "CLAUDE.md")

#: Liczebniki w dopełniaczu, bo tak stoją w zdaniu z `CLAUDE.md` §8: „poniżej
#: dwunastu pozycji". Tabela jest krótka celowo — obejmuje otoczenie dzisiejszego
#: progu, a nie wszystkie liczby, jakie da się zapisać słowem. Próg wyprowadzony
#: poza ten zakres wywala bramkę na braku wpisu, i to jest zachowanie chciane:
#: kto zmienia próg, ma dopisać słowo, którym go zapisał.
LICZEBNIKI = {
    "ośmiu": 8,
    "dziewięciu": 9,
    "dziesięciu": 10,
    "jedenastu": 11,
    "dwunastu": 12,
    "trzynastu": 13,
    "czternastu": 14,
    "piętnastu": 15,
    "szesnastu": 16,
    "osiemnastu": 18,
    "dwudziestu": 20,
}

#: Zdanie progu z `CLAUDE.md` §8. Wyłuskuje liczebnik i to, CO jest liczone —
#: dwie rzeczy, o których ta bramka rozstrzyga osobno, bo poprzednia wersja zdania
#: miała pierwszą i nie miała drugiej.
ZDANIE_PROGU = re.compile(
    r"poniżej\s+\*{0,2}([a-ząćęłńóśźż]+)\s+pozycji([^,.]*)", re.IGNORECASE)

#: Czego to zdanie ma dotyczyć. Nie „pozycji" w ogóle: pozycji, których nie blokuje
#: cudza decyzja — czyli tego, co liczy `do_wziecia`.
LICZNIK_W_DOKUMENCIE = "DO WZIĘCIA"

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
#: **125 → 130 (08.09.2026, uzupełnienie kolejki o pięć pozycji o PRZYRZĄDACH).**
#: Wszystkie pięć wyszło z pomiarów wykonanych tego dnia przy innej pracy, a trzy
#: opisują usterki, które sam wprowadziłem albo przegapiłem — 6.D56 dotyczy commita,
#: którego tematem było „liczba ma stać w jednym miejscu" i który zostawił ją w dwóch.
#:
#: Najmocniejsza jest **6.D54**, bo dotyczy wyrocznia zieloności całego projektu:
#: `test_all.py` łapie `except Exception`, a `SystemExit` dziedziczy z `BaseException`,
#: więc test wołający `sys.exit(0)` kończy CAŁY zestaw **kodem 0** po jednym wykonanym
#: teście, bez wiersza `N/N przeszło` i bez `RAZEM`. Zmierzone sondą: 1999 testów nie
#: wykonało się wcale, a kod wyjścia — ten sam, który `CLAUDE.md` §5 czyni wyrocznią —
#: powiedział „zielono". Przy `sys.exit(1)` daje kod 1, czyli przyrząd myli się
#: WYŁĄCZNIE w stronę „wszystko w porządku".
#:
#: Zapadka podniesiona na POMIAR liczby bloków w pliku (130), nie na wartość
#: zapamiętaną — i to jest tego dnia trzecie podniesienie, przy którym trzeba było
#: liczyć, a nie pamiętać: dwie gałęzie mówiły jednocześnie „125", bo każda liczyła
#: tylko własny blok.
#: **130 → 131 (08.09.2026, blok 6.D53 z obejścia Overpassa).** Podniesienie jest tu
#: WYNIKIEM ROZWIĄZANIA KONFLIKTU, i to jest cała jego treść: gałąź obejścia mówiła
#: „125 → 126", `main` mówił „125 → 130", i **obie liczby były nieprawdziwe wobec pliku
#: scalonego**, bo każda strona liczyła wyłącznie własne bloki. Prawidłową wartością
#: nie jest żadna z nich, tylko POMIAR na pliku po scaleniu — 131. To trzeci raz tego
#: dnia, kiedy ta zapadka wymagała liczenia, a nie pamiętania, i pierwszy, kiedy
#: pułapką była nie pamięć, a DWIE prawdziwe liczby z dwóch osobnych drzew.
#:
#: Sam konflikt rozwiązano **nie sumą region po regionie**, choć git rozbił go na trzy
#: regiony, a między dwoma z nich zostawił jako wspólny **prefiks pól bloku** — czyli
#: dokładnie mechanizm, który 07.09.2026 wstawił blok 6.D39 w środek bloku 6.D40
#: i odebrał mu cztery pola. Plik zbudowano od wersji `main` i wstawiono do niego blok
#: 6.D53 **w całości**, wzięty z `git show :2:` — wiersz tabeli przed 6.D54, blok przed
#: blokiem 6.D54, oba CIĄGŁE. Sprawdzone przejściem po wszystkich 131 blokach: zero
#: braków pól.
#: Podniesione 09.09.2026 trzy razy: do **132** przy bloku 6.D59 w commicie pozycji
#: 6.D58, do **133** przy bloku 6.D60 w commicie 6.D24, i do **137** przy czterech
#: blokach 6.D61 … 6.D64 z commita uzupełniającego kolejkę. Każda wartość z POMIARU
#: `len(detail_sections(...))` na pliku po edycji, nie z dodania jedynki do
#: poprzedniej — i to jest cała reguła tej zapadki, bo trzy z tych czterech
#: podniesień poszły w jednym dniu, a arytmetyka z pamięci pomyliłaby się przy
#: pierwszym commicie dopisującym więcej niż jeden blok. Zdanie wyżej o 131 blokach
#: zostaje jako zapis tamtego pomiaru, bo mówi, jak rozwiązano tamten konflikt.
#: **166 → 167 (09.09.2026, przy 6.D71).** Jeden blok: **6.D94**, i nie wychodzi
#: z uzupełniania kolejki, tylko z POMIARU zrobionego przy innej pozycji.
#: Po naprawieniu kompilacji modułów testowych `python3 -O tools/tests/test_all.py`
#: kończy kodem 1 wobec 0 przy przebiegu zwykłym — bo narzędzie broni warunku
#: geometrycznego gołym `assert`, a `-O` zdejmuje `assert` w KAŻDYM module.
#: Liczba jest POLICZONA na pliku po dopisaniu bloku, nie zwiększona o jeden.
#: **173 → 179 (10.09.2026, drugie tego dnia uzupełnienie kolejki).** Sześć bloków:
#: 6.D101 … 6.D106, wszystkie z pomiarów zrobionych PRZY WYKONYWANIU pozycji 6.D73,
#: 6.D85, 6.D86, 6.D87 i 6.D89, a nie wymyślonych pod pustą kolejkę. Wartość jest
#: wynikiem `len(detail_sections(...))` na pliku po edycji — sześć bloków dopisanych
#: jednym commitem to dokładnie ten przypadek, w którym dodawanie jedynki z pamięci
#: się myli.
#: **179 → 185 (10.09.2026, przy 6.D96).** Sześć bloków: 6.D107 … 6.D112. Uzupełnienie
#: NIE jest tu osobnym commitem i to jest wybór wymuszony arytmetyką: domknięcie 6.D96
#: zbija kolejkę z dwunastu na jedenaście, czyli PONIŻEJ progu, więc `CLAUDE.md` §8
#: każe uzupełnić ją zanim cokolwiek innego się zacznie — a commit z samym domknięciem
#: zostawiłby drzewo czerwone. Wszystkie sześć wyszło z pomiarów zrobionych przy
#: pozycjach 6.D90, 6.D91, 6.D92, 6.D94, 6.D95 i 6.D96, zapisanych tam jako zauważone.
#: Wartość z `len(detail_sections(...))` na pliku po edycji.
#: **185 → 191 (10.09.2026, przy 6.D102).** Sześć bloków: 6.D113 … 6.D118, i znowu
#: NIE osobnym commitem, z tej samej arytmetyki: domknięcie 6.D102 zbija kolejkę
#: z dwunastu na jedenaście. Wszystkie sześć wyszło z pomiarów zrobionych przy
#: pozycjach 6.D97, 6.D99, 6.D100, 6.D101 i 6.D102 i zapisanych tam jako zauważone;
#: 6.D114 jest jedynym, na który natrafiłem NIE z lektury, tylko wołając zestaw
#: z czterema modułami i dostając wynik jednego. Wartość
#: z `len(detail_sections(...))` na pliku po edycji.
#: **191 → 199 (10.09.2026, osiem decyzji właściciela).** Osiem bloków:
#: 6.D119 … 6.D126, i tym razem NIE z uzupełnienia kolejki przy progu, tylko z pracy,
#: którą tworzą decyzje właściciela z tego dnia (sekcja „Rozstrzygnięte 10.09.2026"
#: w `docs/TASKS.md`). Wartość z `len(detail_sections(...))` na pliku po edycji.
#: **207 → 213 (11.09.2026, przy 6.D125).** Sześć bloków: 6.D135 … 6.D140, i NIE
#: osobnym commitem — z tej samej arytmetyki, co przy 6.D96 i 6.D102: domknięcie
#: 6.D125 zbija kolejkę z dwunastu na JEDENAŚCIE, czyli poniżej progu, więc `CLAUDE.md`
#: §8 każe uzupełnić ją zanim cokolwiek innego się zacznie, a commit z samym
#: domknięciem zostawiłby drzewo czerwone. Wszystkie sześć wyszło z pomiarów zrobionych
#: PRZY WYKONYWANIU pozycji 6.D120, 6.D121, 6.D122, 6.D123 i 6.D124 i zapisanych tam
#: jako zauważone — ani jedna nie jest wymyślona pod pustą kolejkę. Wartość
#: z `len(detail_sections(...))` na pliku po edycji.
#: **213 → 219 (11.09.2026, przy 6.D131).** Sześć bloków: 6.D141 … 6.D146, i NIE
#: osobnym commitem — z tej samej arytmetyki, co przy 6.D96, 6.D102 i 6.D125:
#: domknięcie 6.D131 zbija kolejkę z dwunastu na JEDENAŚCIE, czyli poniżej progu,
#: więc `CLAUDE.md` §8 każe uzupełnić ją zanim cokolwiek innego się zacznie, a commit
#: z samym domknięciem zostawiłby drzewo czerwone. Wszystkie sześć wyszło z pomiarów
#: zrobionych PRZY WYKONYWANIU pozycji 6.D126, 6.D127, 6.D130 i 6.D131 — trzy z nich
#: (6.D142, 6.D143, 6.D145) wyszły z kontroli negatywnych, które WYSZŁY ZIELONE albo
#: z granic czytnika wypisanych w jego własnym module, a nie z lektury. Wartość
#: z `len(detail_sections(...))` na pliku po edycji, nie z dodania szóstki do 213.
#: **219 → 225 (11.09.2026, przy 6.D137).** Sześć bloków: 6.D147 … 6.D152, i NIE
#: osobnym commitem — z tej samej arytmetyki, co przy 6.D96, 6.D102, 6.D125 i 6.D131:
#: domknięcie 6.D137 zbija kolejkę z dwunastu na JEDENAŚCIE, czyli poniżej progu.
#: Wszystkie sześć wyszło z pomiarów zrobionych PRZY WYKONYWANIU pozycji 6.D133,
#: 6.D134, 6.D135 i 6.D136 — cztery z nich (6.D147, 6.D148, 6.D149, 6.D152) z rzeczy
#: wypisanych w polu „Czego nie zrobiłem" tamtych pozycji, czyli z granic, które sam
#: nazwałem, zamiast je przemilczeć. Wartość z `len(detail_sections(...))` na pliku
#: po edycji, nie z dodania szóstki do 219.
#: **225 → 228 (11.09.2026, przy 6.D143).** Trzy bloki: 6.D153, 6.D154 i 6.D155, i NIE
#: osobnym commitem — z tej samej arytmetyki, co wyżej: domknięcie 6.D143 zbija kolejkę
#: z dwunastu na JEDENAŚCIE, czyli poniżej progu. Tym razem bloków jest TRZY, a nie
#: sześć, i to też jest liczba z arytmetyki, a nie z nawyku: jedenaście plus trzy daje
#: czternaście, a potrzeba dwunastu — zapas dwóch pozycji zamiast pięciu, bo wszystkie
#: trzy wyszły z pomiarów zrobionych PRZY WYKONYWANIU 6.D142 i 6.D143, a wymyślanie
#: dalszych na zapas byłoby braniem zadania z sufitu (`CLAUDE.md` §8, zdanie ostatnie).
#: Wartość z `len(detail_sections(...))` na pliku po edycji, nie z dodania trójki do 225.
#: **228 → 231 (11.09.2026, przy 6.D146).** Trzy bloki: 6.D156, 6.D157 i 6.D158,
#: znów NIE osobnym commitem, bo domknięcie 6.D146 zbija kolejkę z dwunastu na
#: JEDENAŚCIE. Wszystkie trzy wyszły z pomiarów zrobionych PRZY WYKONYWANIU 6.D145
#: i 6.D146, a dwa (6.D156, 6.D158) z rzeczy wypisanych w polu „Czego nie zrobiłem"
#: tamtych pozycji — czyli z granic, które sam nazwałem, zamiast je przemilczeć.
#: Wartość z `len(detail_sections(...))` po edycji, nie z dodania trójki do 228.
#: **231 → 234 (12.09.2026, przy 6.D149).** Trzy bloki: 6.D159, 6.D160 i 6.D161, znów
#: nie osobnym commitem, bo domknięcie 6.D149 zbija kolejkę z dwunastu na JEDENAŚCIE.
#: Dwa (6.D159, 6.D160) wyszły wprost z pól „Czego nie zrobiłem" pozycji 6.D147
#: i 6.D149; trzeci — z rzeczy, która zdarzyła się TRZY RAZY POD RZĄD w tych samych
#: trzech pozycjach i dopiero przez powtórzenie dała się zobaczyć.
#: Wartość z `len(detail_sections(...))` po edycji, nie z dodania trójki do 231.
# 283 -> 285 (14.09.2026, MB-08): 6.M1 (`--replay` nie działa z `--line`)
# i 6.M2 (jednostronne okno zatrzymania w `LineDrive`) — oba znaleziska POBOCZNE
# z MB-08, zapisane tak, jak każe `CLAUDE.md` §8 przy aktywnym kamieniu milowym.
# 285 -> 286 (14.09.2026, 6.D208): blok szesciu pol dla 6.D218 — zapas
# udokumentowany zszedl do 11 po domknieciu 6.D207 i 6.D208, czyli ponizej progu
# doby pracy, a §8 `CLAUDE.md` kaze wtedy najpierw uzupelnic kolejke.
# 286 -> 287 (14.09.2026, 6.D209): blok szesciu pol dla 6.D219 — remis dat raportu
# i stalej. Domkniecie 6.D209 zbilo zapas znowu do 11, a pozycji wymyslonej na miejscu
# nie bierze sie nigdy: 6.D219 wyszlo z pomiaru 6.D209, ktory znalazl remis w polowie
# wlasnej probki.
# 287 -> 288 (14.09.2026, 6.D210): blok szesciu pol dla 6.D220 — ten sam typ i dwie
# przeciwne decyzje o ramieniu domyslnym w jednym pliku. Ta sama mechanika: domkniecie
# 6.D210 zbilo zapas do 11, a pozycja wyszla z pomiaru, nie z potrzeby zapelnienia.
# 288 -> 289 (14.09.2026, 6.D211): blok szesciu pol dla 6.D221 — nazwa metody
# w prozie wiersza, ktorej plik jej nie deklaruje. Ta sama mechanika trzeci raz
# z rzedu: domkniecie zbilo zapas do 11, a pozycja wyszla z pomiaru — znalazlem
# ja, czytajac wlasny wiersz 6.D210 sprzed kilku godzin.
# 289 -> 290 (15.09.2026, 6.D212): blok szesciu pol dla 6.D222 — workflow,
# ktory nie wystartowal ani razu od 6.D108, i bramka, ktora tego nie widzi.
# Pozycja NIE wyszla z progu zapasu, tylko ze znaleziska po drodze: przebieg
# `prune-merged-branches.yml` stal czerwony na galezi PR-a 6.D211.
# 290 -> 291 (15.09.2026, 6.D222): blok szesciu pol dla 6.D223 — dwadziescia
# jeden przypuszczen z 6.D212, ktore po dwoch sprawdzonych podstawieniem maja
# 0 na 2 trafien. Pozycja wybrana przez wlasciciela klikalnie, a nie z progu.
# 291 -> 292 (15.09.2026, 6.D213): blok szesciu pol dla 6.D224 — `var`
# z wnioskowanym typem wyliczeniowym, czyli DRUGA slepa plamka sita, ktorej
# 6.D213 nie policzylo i tak to zapisalo. Domkniecie 6.D213 zbilo zapas do 11.
# 292 -> 293 (15.09.2026, 6.D214): blok szesciu pol dla 6.D225 — stale czytane
# wylacznie przez interpolacje, ktore skan widzi jako martwe. Pozycja NIE wyszla
# z progu zapasu, tylko ZGLOSILA JA SAMA BRAMKA projektu podczas tej pracy.
# 293 -> 294 (15.09.2026, 6.D215): blok szesciu pol dla 6.D226 — dwie listy
# tych samych czterech zapisow literalu, ktorych zgodnosci nie pilnuje nic.
# Pozycja wyszla z KN-4 tej pozycji: skreslenie jednej z czterech przeszlo
# na zielono, dopoki bramka nie zaczela pytac o ZBIOR.
# 294 -> 296 (15.09.2026, 6.D216): DWA bloki szesciu pol — 6.D227 (zdanie o zakresie
# SZERSZYM niz zmierzony; wyszlo z recznego przegladu, gdzie 6.D210 §9 mowi o calym
# `src/Sim/`, a mierzylo switche po WYLICZENIU) i 6.D228 (skan po RDZENIU SLOWA —
# naglowek sekcji „zauwazone" ma 23 brzmienia, a synonim wypada bez sladu).
# 296 -> 297 (15.09.2026, 6.D217): blok szesciu pol dla 6.D229 — `JsonDocument.Parse`
# przy zepsutej skladni omija filtr `catch`, wiec droga bledu konczy sie po angielsku
# i ze stosem. Pozycja NIE wyszla z progu zapasu, tylko z pomiaru tej pozycji:
# 2 z 4 probek przelatuja obok filtru.
# 297 -> 298 (15.09.2026, 6.D219): blok szesciu pol dla 6.D230 — dwa czytniki tego
# samego katalogu i dwie rozne granice: `claims_in_reports` pomija bloki ogrodzone,
# `wystapienia_w_jednych_grawisach` nie. Pozycja NIE wyszla z progu zapasu, tylko
# z czerwieni, ktora ta bramka zapalila na raporcie 6.D219.
# 298 -> 299 (15.09.2026, 6.D220): blok szesciu pol dla 6.D231 — `KorpusMetody` przy
# metodzie WYRAZENIOWEJ oddaje korpus NASTEPNEJ. Pozycja NIE wyszla z progu zapasu,
# tylko z przebiegu czytnika przy tej pozycji: `BrakingDistanceM` dostaje 3056 znakow
# korpusu `Supervise`, a straz `deklaracji == 1` przepuszcza to bez slowa.
# 299 -> 305 (15.09.2026, 6.D221): szesc blokow szesciu pol naraz — 6.D232 … 6.D237.
# Skok o szesc, a nie o jeden, bo kolejka zeszla po domknieciu 6.D221 do JEDENASTU
# pozycji DO WZIECIA przy progu dwunastu, a `CLAUDE.md` §8 kaze wtedy uzupelnic ja
# PIERWSZYM zadaniem. Pozycje nie sa wymyslone na miejscu (§8 tego zabrania): kazda
# wyszla z pomiaru wykonanego przy 6.D218 … 6.D229 i niesie liczby z tamtych przebiegow.
# Liczba POLICZONA przez `len(detail_sections(...))` na pliku PO edycji, nie wpisana
# z pamieci — tak jak kaze komentarz przy tej stalej od poczatku.
# 305 -> 307 (15.09.2026, 6.D223): dwa bloki szesciu pol — 6.D238 i 6.D239.
# Obie pozycje wyszly z POMIARU tej pozycji, a nie z progu zapasu: sa to dwie
# jedyne dziury, ktore 19 podstawien znalazlo i ktorych naprawianie blok 6.D223
# stawia poza zakresem — cytat przypinajacy WARTOSC zamiast WIERSZA (`test_t401_citation`)
# i tytul dziela w rejestrze praw, ktorego nie pilnuje nic. Liczba POLICZONA przez
# `len(detail_sections(...))` na pliku PO edycji, nie wpisana z pamieci.
# 312 -> 315 (17.09.2026): trzy bloki szesciu pol dla pozycji, ktore staly w tabeli
# BEZ bloku — 6.D169, 6.D170, 6.D171. Nie jest to uzupelnienie kolejki: pozycji do
# wziecia bylo 14 przed i jest 14 po, bo wiersze tych pozycji staly w tabeli od
# 12.09.2026. Ruszyl licznik `documented_items` (10 -> 13), czyli ten, ktory mowi,
# ile pozycji da sie wziac BEZ dopytywania — i to on byl pod progiem dwunastu.
# Czwarta pozycja bez bloku, 6.D168, bloku NIE dostala i jest to wynik zapisany
# w `docs/TASKS.md`: jej pole „Wyjscie" trzeba by wymyslic, bo wiersz stawia wybor
# miedzy zapisem do `data/` (§4.6) a oknem przejsciowym bez daty konca.
# Liczba POLICZONA przez `len(detail_sections(...))` na pliku PO edycji.
# 315 -> 319 (17.09.2026): cztery bloki pozycji 6.D252-6.D255, dopisane jako
# uzupelnienie kolejki wymuszone przez `test_the_queue_holds_at_least_a_day_of_work`
# po domknieciu 6.D232. Policzone czytnikiem `detail_sections` na pliku PO edycji.
# 319 -> 320 (17.09.2026, 6.D233): blok pozycji 6.D256, zapisujacej niewiadoma,
# na ktorej stoi zawezenie zakresu 6.D233. Policzone czytnikiem po edycji.
# 320 -> 321 (17.09.2026, 6.D253): blok pozycji 6.D257, dopisany jako uzupelnienie
# kolejki wymuszone przez `test_the_documented_shortfall_is_written_down_while_it_lasts`
# po adnotacji ZROBIONE na 6.D253 (zapas spadl na 11 przy progu 12).
# Policzone czytnikiem `detail_sections` na pliku PO edycji.
# 321 -> 322 (17.09.2026, 6.D254): blok pozycji 6.D258, dopisany jako uzupelnienie
# kolejki po adnotacji ZROBIONE na 6.D254 (zapas spadl na 11 przy progu 12).
# Policzone czytnikiem `detail_sections` na pliku PO edycji.
MINIMUM_DETAIL_BLOCKS = 322

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


#: Słowo, po którym poznaje się pole „Zależy od" mówiące o decyzji CZŁOWIEKA,
#: a nie o innej pozycji kolejki. Szukane bez końcówki, bo pole odmienia je przez
#: przypadki („decyzji właściciela", „decyzja właściciela"); zmierzone 10.09.2026:
#: w całym `docs/TASKS.md` nie ma ani jednego pola „Zależy od", w którym to słowo
#: znaczyłoby co innego.
SLOWO_WLASCICIELA = "właściciel"


#: Data w polu „Zależy od" — znaczy, że decyzja o tej treści JUŻ ZAPADŁA. Kształt
#: `DD.MM.RRRR`, ten sam, którym cały ten plik datuje pomiary i rozstrzygnięcia.
DATA_DECYZJI = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")


def pole_zaleznosci(body):
    """Treść pola „Zależy od" z bloku szczegółów; pusty napis, gdy pola nie ma."""
    marker = "- **Zależy od:**"
    at = body.find(marker)
    if at < 0:
        return ""
    rest = body[at + len(marker):]
    nxt = re.search(r"\n- \*\*", rest)
    return " ".join((rest if nxt is None else rest[:nxt.start()]).split())


def czeka_na_wlasciciela(text):
    """Numery pozycji OTWARTYCH, których „Zależy od" mówi o decyzji właściciela.

    **Po co (6.D95).** `doctor.sh` wypisywał zdanie STAŁE — „żadna nie wymaga decyzji
    właściciela" — obok liczby policzonej z pliku. Zdanie o zbiorze było więc
    wypowiadane bez zajrzenia do zbioru, a w policzonej kolejce stała 6.D53, której
    pole „Zależy od" brzmi dosłownie „decyzji właściciela o zapisie do
    `data/network/sources.json`". Ta sama rodzina co 6.D27: przyrząd melduje
    sprawdzenie, którego nie zrobił.

    **Nie rusza `open_items`** — pole „Poza zakresem" pozycji 6.D95 wyklucza to
    wprost. Bierze jego wynik i dzieli go na dwie kupki po treści pól.

    **DECYZJA DATOWANA JEST DECYZJĄ PODJĘTĄ** (10.09.2026, decyzja właściciela z tego
    dnia). Do tego dnia liczyła się każda wzmianka o właścicielu, więc pozycja, której
    pole mówi „decyzji właściciela **z 07.09.2026**", uchodziła za czekającą — choć ta
    decyzja dawno zapadła i pozycję właśnie odblokowała. Zmierzone na 138 rewizjach
    `docs/TASKS.md`: tak liczone były **6.B43** (w 70 rewizjach) i **6.B44** (w 28),
    obie z decyzjami datowanymi na 05. i 07.09.2026. Przyrząd meldował więc blokadę,
    której nie było — ta sama rodzina co 6.D27, tylko w drugą stronę: nie przemilczał
    stanu, tylko go zmyślał.

    Rozróżnienie idzie po **dacie w polu**, a nie po liście numerów: pole mówiące
    o decyzji BEZ daty opisuje decyzję, która ma dopiero zapaść. Cena, powiedziana
    wprost: pole, które nazywa decyzję oczekującą i przy okazji podaje jakąś inną datę,
    przestaje być liczone jako blokada. W dzisiejszym pliku taki przypadek nie
    występuje, a wariant odwrotny — liczenie decyzji podjętych — kosztował dwie pozycje
    w niemal każdej rewizji historii.
    """
    bloki = detail_sections(text)
    czekaja = []
    for numer in open_items(text):
        pole = pole_zaleznosci(bloki.get(numer, ""))
        if SLOWO_WLASCICIELA not in pole.lower():
            continue
        if DATA_DECYZJI.search(pole):
            continue
        czekaja.append(numer)
    return sorted(czekaja)


def do_wziecia(text):
    """Pozycje otwarte BEZ zależności od decyzji właściciela."""
    czekaja = set(czeka_na_wlasciciela(text))
    return [n for n in open_items(text) if n not in czekaja]


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


def _blok_zaleznosci(numer, pole):
    """Blok szczegółów o jednym polu „Zależy od" — do kontroli na wejściu syntetycznym."""
    return ("##### %s · Pozycja syntetyczna\n\n- **Zależy od:** %s\n" % (numer, pole))


def test_decyzja_datowana_nie_liczy_sie_jako_oczekujaca():
    """Pole mówiące o decyzji Z DATĄ opisuje decyzję PODJĘTĄ — 10.09.2026.

    **Skąd.** Do 10.09.2026 liczyła się każda wzmianka o właścicielu, więc pozycja
    odblokowana zdaniem „decyzji właściciela z 07.09.2026" uchodziła za czekającą na
    tę samą decyzję, która ją odblokowała. Zmierzone na 138 rewizjach `docs/TASKS.md`:
    tak liczone były 6.B43 (70 rewizji) i 6.B44 (28). Przyrząd meldował blokadę,
    której nie było.

    Obie strony, bo tylko razem coś znaczą: bez daty ma liczyć, z datą nie ma.
    """
    tekst_bez = _blok_zaleznosci("6.Z1", "decyzji właściciela o kształcie profilu.")
    tekst_z = _blok_zaleznosci(
        "6.Z1", "decyzji właściciela z 07.09.2026 (pasmo 0..94,0 m).")

    assert SLOWO_WLASCICIELA in pole_zaleznosci(tekst_bez).lower(), (
        "wejście syntetyczne nie mówi o właścicielu — kontrola mierzyłaby nie to")
    assert SLOWO_WLASCICIELA in pole_zaleznosci(tekst_z).lower(), (
        "wejście syntetyczne z datą też ma mówić o właścicielu")

    assert DATA_DECYZJI.search(pole_zaleznosci(tekst_z)), (
        "wzorzec daty nie widzi daty w polu, które ją ma")
    assert not DATA_DECYZJI.search(pole_zaleznosci(tekst_bez)), (
        "wzorzec daty widzi datę w polu, które jej nie ma")


def test_czytnik_blokad_rozroznia_oba_ksztalty_na_kolejce_syntetycznej():
    """Ten sam czytnik na dwóch kolejkach: z blokadą prawdziwą i z decyzją podjętą.

    Kontrola idzie przez `czeka_na_wlasciciela`, a nie przez sam wzorzec — inaczej
    mierzyłaby regex, a nie werdykt. Kolejka syntetyczna, bo dzisiejsza kolejka nie
    ma dziś ani jednej blokady i cisza nic by nie znaczyła.
    """
    tresc = _tasks()
    wzorzec = "##### 6.D109 ·"
    assert wzorzec in tresc, "znikł blok, na którym stoi ta kontrola"

    def z_polem(pole):
        """Kolejka z dopisaną pozycją syntetyczną: WIERSZ TABELI **i** blok.

        Sam blok nie wystarcza i to nie jest szczegół: `open_items` czyta tabelę,
        a `czeka_na_wlasciciela` dzieli JEJ wynik. Pozycja bez wiersza nie jest
        pracą do wzięcia, więc nie ma czego dzielić — pierwsza wersja tej kontroli
        dopisywała sam blok i dostawała pustą listę z obu stron.
        """
        z_blokiem = tresc.replace(
            wzorzec, _blok_zaleznosci("6.Z1", pole) + "\n" + wzorzec, 1)
        return z_blokiem.replace(
            "| 6.D109 |",
            "| 6.Z1 | **Pozycja syntetyczna** | kontrola 10.09.2026 | S |\n| 6.D109 |", 1)

    z_blokada = z_polem("decyzji właściciela o kształcie profilu.")
    assert "6.Z1" in czeka_na_wlasciciela(z_blokada), (
        "decyzja BEZ daty nie została policzona jako oczekująca: %s"
        % czeka_na_wlasciciela(z_blokada))

    z_decyzja = z_polem("decyzji właściciela z 07.09.2026 o kształcie profilu.")
    assert "6.Z1" in open_items(z_decyzja), (
        "pozycja syntetyczna nie weszła do kolejki — kontrola mierzyłaby nic")
    assert "6.Z1" not in czeka_na_wlasciciela(z_decyzja), (
        "decyzja Z DATĄ została policzona jako oczekująca: %s"
        % czeka_na_wlasciciela(z_decyzja))


def test_the_queue_holds_at_least_a_day_of_work():
    """Próg porównuje pozycje DO WZIĘCIA, nie wpisane — 6.D109, 10.09.2026.

    `open_items`, nie `ready_items`: pozycja z adnotacją domknięcia stoi w tabeli
    z powodu zapadki, a nie dlatego, że jest pracą. Ale `open_items` też nie jest
    tym, co agent może wziąć: pozycja czekająca na decyzję właściciela stoi w kolejce
    i jest **niewykonalna**. Gwarancja z `CLAUDE.md` §8 mówi o dobie pracy PRZED
    AGENTEM, więc liczy się to, co da się zacząć.

    **Zmierzone na 139 rewizjach `docs/TASKS.md`** (czytnikiem poprawionym w tym
    samym dniu — poprzedni liczył decyzje datowane, czyli już podjęte, jako
    oczekujące):

        różnica 0 →  54 rewizje
        różnica 1 →  84 rewizje
        różnica 2 →   1 rewizja

    Czyli różnica jest **mała** (prawie zawsze jeden) i **częsta, ale nie stała**:
    85 rewizji ze 139. Czekały kiedykolwiek trzy pozycje: 6.D53 (84 rewizje),
    6.D52 i 6.D108 (po jednej). Wybór licznika przesuwa więc moment uzupełnienia
    kolejki o jedną pozycję w 61 % rewizji — i przesuwa go we WŁAŚCIWĄ stronę, bo
    pozycji zablokowanej agent nie weźmie.

    **Komunikat podaje obie liczby**, żeby nie trzeba było zgadywać, którą próg
    porównał: to jest wprost żądanie pola „Skończone, gdy" pozycji 6.D109.
    """
    tekst = _tasks()
    wpisane = open_items(tekst)
    wolne = do_wziecia(tekst)
    czekaja = czeka_na_wlasciciela(tekst)
    assert len(wolne) >= MINIMUM_READY_ITEMS, (
        f"kolejka ma {len(wolne)} pozycji DO WZIĘCIA przy progu "
        f"{MINIMUM_READY_ITEMS} (wpisanych: {len(wpisane)}, czeka na właściciela: "
        f"{', '.join(czekaja) if czekaja else 'żadna'}); pierwszym zadaniem jest "
        "uzupełnienie fazy 6, nie zatrzymanie się")


def test_prog_zapasu_porownuje_pozycje_do_wziecia_a_nie_wpisane():
    """Kolejka syntetyczna z pozycją ZABLOKOWANĄ pokazuje, którą liczbę próg czyta.

    Tego żąda pole „Skończone, gdy" pozycji 6.D109. Na dzisiejszej kolejce obie
    liczby są równe (nikt nie czeka na właściciela od decyzji z 10.09.2026), więc
    werdykt nie odróżniłby jednego licznika od drugiego — różnicę widać dopiero na
    wejściu, w którym pozycja zablokowana jest.

    Kolejka jest tu **budowana**, a nie brana z drzewa: musi mieć dokładnie tyle
    pozycji, ile wynosi próg, żeby zdjęcie jednej przez blokadę było widoczne.
    """
    numery = ["6.Z%d" % i for i in range(1, MINIMUM_READY_ITEMS + 1)]
    wiersze = "\n".join("| %s | **Pozycja syntetyczna** | kontrola | S |" % n
                        for n in numery)
    bloki = "\n\n".join(_blok_zaleznosci(n, "brak.") for n in numery)
    kolejka = ("## Faza 6\n\n| pozycja | rzecz | skąd | waga |\n|---|---|---|---|\n"
               + wiersze + "\n\n" + bloki + "\n")

    assert len(open_items(kolejka)) == MINIMUM_READY_ITEMS, (
        "kolejka syntetyczna nie ma tylu pozycji, ile wynosi próg — kontrola "
        "mierzyłaby nie to: %d" % len(open_items(kolejka)))
    assert len(do_wziecia(kolejka)) == MINIMUM_READY_ITEMS, len(do_wziecia(kolejka))

    # Jedna pozycja dostaje blokadę: WPISANYCH nadal tyle, ile progu, DO WZIĘCIA mniej.
    zablokowana = kolejka.replace(
        "##### 6.Z1 · Pozycja syntetyczna\n\n- **Zależy od:** brak.",
        "##### 6.Z1 · Pozycja syntetyczna\n\n- **Zależy od:** decyzji właściciela.", 1)
    assert len(open_items(zablokowana)) == MINIMUM_READY_ITEMS, (
        "blokada zmieniła liczbę WPISANYCH — a miała zmienić tylko liczbę do wzięcia")
    assert len(do_wziecia(zablokowana)) == MINIMUM_READY_ITEMS - 1, (
        len(do_wziecia(zablokowana)))
    assert czeka_na_wlasciciela(zablokowana) == ["6.Z1"], (
        czeka_na_wlasciciela(zablokowana))

    # I to jest cała treść rozstrzygnięcia: przy tej kolejce próg na WPISANYCH
    # przechodzi, a próg na DO WZIĘCIA — nie. Bramka wyżej czyta ten drugi.
    assert len(open_items(zablokowana)) >= MINIMUM_READY_ITEMS
    assert not len(do_wziecia(zablokowana)) >= MINIMUM_READY_ITEMS, (
        "kolejka z pozycją zablokowaną spełnia próg liczony po pozycjach do wzięcia "
        "— kontrola nie odróżnia dwóch liczników")


def sekcja_osma(tekst=None):
    """Treść `CLAUDE.md` §8, od nagłówka do następnego."""
    if tekst is None:
        with open(CLAUDE, encoding="utf-8") as uchwyt:
            tekst = uchwyt.read()
    poczatek = tekst.index("## 8. ")
    return tekst[poczatek:tekst.index("\n## 9.", poczatek)]


def prog_z_dokumentu(tekst=None):
    """Para: (liczba z §8, co §8 każe liczyć). Bez zdania progu — `(None, "")`."""
    trafienie = ZDANIE_PROGU.search(sekcja_osma(tekst))
    if trafienie is None:
        return None, ""
    return LICZEBNIKI.get(trafienie.group(1).lower()), trafienie.group(2)


def test_dokument_i_kod_mowia_o_tej_samej_liczbie():
    """`CLAUDE.md` §8 podaje próg słowem; ta bramka porównuje go z `MINIMUM_READY_ITEMS`.

    Tego żąda pole „Skończone, gdy" pozycji 6.D109: **dokument i kod mówią o tej
    samej** liczbie. Bez bramki „ta sama" znaczyłoby „była ta sama w dniu, w którym
    ktoś patrzył" — a próg jest stałą w pliku, którą wolno podnieść jednym znakiem.

    Rozstrzyga o DWÓCH rzeczach, bo poprzednia wersja zdania miała pierwszą i nie
    miała drugiej: o **wartości** progu i o tym, **co** jest liczone. Zdanie „poniżej
    dwunastu pozycji" było zgodne co do liczby i mimo to nie mówiło, czy chodzi
    o pozycje wpisane, czy o te do wzięcia — a to jest dokładnie różnica, którą 6.D109
    zmierzyło na 85 rewizjach ze 139.
    """
    liczba, o_czym = prog_z_dokumentu()
    assert liczba is not None, (
        "w `CLAUDE.md` §8 nie ma zdania progu w kształcie „poniżej <liczebnik> pozycji"
        "” albo liczebnik jest spoza tabeli LICZEBNIKI")
    assert liczba == MINIMUM_READY_ITEMS, (
        f"`CLAUDE.md` §8 mówi o {liczba} pozycjach, a kod porównuje z "
        f"{MINIMUM_READY_ITEMS}")
    assert LICZNIK_W_DOKUMENCIE in o_czym, (
        "`CLAUDE.md` §8 nie mówi, KTÓRE pozycje liczy — po progu stoi "
        f"{o_czym!r}, a bramka zapasu porównuje pozycje {LICZNIK_W_DOKUMENCIE}")


def test_bramka_zgodnosci_lapie_obie_rozbieznosci():
    """Kontrola negatywna: osobno rozjazd liczby i osobno brak nazwy licznika.

    Jeden test na obie połowy opisywałby co innego, niż sprawdza — więc obie
    rozbieżności są tu podane na wejściu syntetycznym, nie na drzewie.
    """
    szablon = ("## 8. Kiedy przerwać\n\nGdy kolejka zejdzie poniżej %s, "
               "**pierwszym zadaniem jest jej uzupełnienie**.\n\n## 9. CI\n")

    zgodne = szablon % ("**dwunastu pozycji DO WZIĘCIA**")
    assert prog_z_dokumentu(zgodne) == (12, " DO WZIĘCIA**"), prog_z_dokumentu(zgodne)

    # Rozjazd liczby: dokument mówi o dziesięciu, kod o dwunastu.
    rozjazd, o_czym = prog_z_dokumentu(szablon % "**dziesięciu pozycji DO WZIĘCIA**")
    assert rozjazd == 10 and rozjazd != MINIMUM_READY_ITEMS, (rozjazd, o_czym)

    # Dawne brzmienie: liczba się zgadza, a licznika nie widać.
    liczba, o_czym = prog_z_dokumentu(szablon % "dwunastu pozycji")
    assert liczba == MINIMUM_READY_ITEMS, liczba
    assert LICZNIK_W_DOKUMENCIE not in o_czym, (
        "kontrola nie odróżnia zdania z nazwą licznika od zdania bez niej: %r" % o_czym)

    # Zdania nie ma wcale — bramka ma to zgłosić, a nie przepuścić.
    assert prog_z_dokumentu("## 8. Kiedy przerwać\n\nNic.\n\n## 9. CI\n") == (
        None, "")


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

#: Pasmo M — droga do grywalności. Pozycje MB-* mają INNY prefiks niż kolejka 6.x
#: i to jest wybór, nie niedopatrzenie: `queue_items` i `detail_sections` czytają
#: kształt `<cyfra>.<litera><cyfra>`, więc pasmo M **nie wchodzi** do liczb zapasu
#: ani do `MINIMUM_DETAIL_BLOCKS`. Dzięki temu wprowadzenie planu grywalności NIE
#: podniosło ani nie obniżyło żadnej istniejącej zapadki — a gdyby weszło do tamtych
#: liczb, nie dałoby się odróżnić „przybyło pracy" od „zmieniono miarę".
POZYCJI_PASMA_M = 9

#: Pola, których żąda `CLAUDE.md` §6 — te same, co dla kolejki 6.x.
POLA_PASMA_M = ("Wejście", "Wyjście", "Weryfikacja", "Skończone, gdy",
                "Poza zakresem", "Zależy od")

def bloki_pasma_M(text):
    """`MB-00` → treść bloku szczegółów. Osobny czytnik, bo prefiks jest inny."""
    lines = text.splitlines()
    heads = [(i, m.group(1)) for i, line in enumerate(lines)
             for m in [re.match(r"^#####\s+(MB-\d+)\s*·", line)] if m]
    sections = {}
    for start, number in heads:
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("#"):
                end = j
                break
        sections[number] = "\n".join(lines[start:end])
    return sections


def wiersze_pasma_M(text):
    """Numery pozycji MB-* z tabeli pasma M."""
    return [m.group(1) for line in text.splitlines()
            for m in [re.match(r"^\|\s*(MB-\d+)\s*\|", line)] if m]


def test_pasmo_M_ma_komplet_szesciu_pol_tak_samo_jak_kolejka_6x():
    # Pasmo M jest kolejką jak każda inna i §6 obowiązuje w nim tak samo. Bez tej
    # bramki plan grywalności byłby jedynym miejscem w repozytorium, gdzie zadanie
    # wolno wpisać bez kompletu pól — a to jest dokładnie ten wyjątek, przez który
    # następna sesja bierze pozycję i nie wie, kiedy skończyła.
    text = _tasks()
    bloki = bloki_pasma_M(text)
    wiersze = wiersze_pasma_M(text)

    assert len(wiersze) == POZYCJI_PASMA_M, (
        "wierszy pasma M jest %d, a zmierzono %d: %s"
        % (len(wiersze), POZYCJI_PASMA_M, wiersze))
    assert sorted(bloki) == sorted(wiersze), (
        "wiersze pasma M to %s, a bloki szczegółów %s — każda pozycja ma mieć oba"
        % (sorted(wiersze), sorted(bloki)))

    sprawdzonych = 0
    for numer, tresc in sorted(bloki.items()):
        brakujace = [pole for pole in POLA_PASMA_M
                     if ("- **%s:**" % pole) not in tresc]
        assert not brakujace, (
            "pozycja %s nie ma pól: %s — §6 `CLAUDE.md` żąda kompletu sześciu"
            % (numer, ", ".join(brakujace)))
        sprawdzonych += 1

    assert sprawdzonych == POZYCJI_PASMA_M, (
        "pętla po blokach pasma M wykonała się %d razy zamiast %d — wtedy asercje "
        "wyżej nie sprawdzają wszystkich (rodzina 6.D193)"
        % (sprawdzonych, POZYCJI_PASMA_M))


def test_pasmo_M_NIE_wchodzi_do_liczb_zapasu_i_to_jest_zmierzone():
    # **Najważniejsza asercja tej rodziny.** Zmiana polityki kolejki (MB-00) mogłaby
    # po cichu rozluźnić regułę zapasu — wystarczyłoby, żeby dziewięć nowych pozycji
    # weszło do `do_wziecia` i próg spełniał się sam. Ta bramka mierzy, że NIE weszło:
    # czytniki kolejki 6.x mają widzieć dokładnie to, co widziały przed MB-00.
    text = _tasks()
    numery_M = set(wiersze_pasma_M(text))
    assert numery_M, "pasma M nie ma w tabelach — reszta tej bramki nie ma przedmiotu"

    assert not (numery_M & set(queue_items(text))), (
        "pozycje pasma M weszły do `queue_items`: %s. Wtedy próg zapasu spełnia się "
        "dziewięcioma pozycjami planu i przestaje mierzyć to, co mierzył"
        % sorted(numery_M & set(queue_items(text))))
    assert not (numery_M & set(detail_sections(text))), (
        "bloki pasma M weszły do `detail_sections` — `MINIMUM_DETAIL_BLOCKS` zaczęło "
        "liczyć inny zbiór niż w dniu pomiaru")

    # I DRUGA STRONA: próg sam się nie ruszył. MB-00 zmienia KOLEJNOŚĆ BRANIA,
    # a nie wysokość progu, i to ma być sprawdzane, a nie deklarowane.
    assert MINIMUM_READY_ITEMS == 12, (
        "`MINIMUM_READY_ITEMS` = %d. MB-00 zmieniło kolejność brania, nie próg — "
        "jeśli próg się ruszył, zmiana polityki zrobiła coś, czego nie zapowiadała"
        % MINIMUM_READY_ITEMS)


def test_dokument_planu_istnieje_i_CLAUDE_na_niego_wskazuje():
    # Plan, na który nie wskazuje konstytucja, jest plikiem, którego następna sesja
    # nie przeczyta — a §3 `CLAUDE.md` jest jedynym miejscem, do którego zagląda
    # przed każdym zadaniem.
    plan = os.path.join(ROOT, "docs", "PLAYABILITY.md")
    assert os.path.exists(plan), (
        "nie ma `docs/PLAYABILITY.md`, a `CLAUDE.md` §8 i pasmo M na niego wskazują")

    with open(plan, encoding="utf-8") as handle:
        tresc_planu = handle.read()
    for slowo in ("M1", "M2", "MB-00", "MB-08"):
        assert slowo in tresc_planu, (
            "`docs/PLAYABILITY.md` nie mówi o %s — plan bez kamieni milowych "
            "i bez zakresu pasma nie jest planem" % slowo)

    with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as handle:
        konstytucja = handle.read()
    assert "docs/PLAYABILITY.md" in konstytucja, (
        "`CLAUDE.md` nie wymienia `docs/PLAYABILITY.md` — plan jest wtedy dokumentem, "
        "o którego istnieniu nikt się nie dowie")
    assert "pasmo M" in konstytucja or "pasma M" in konstytucja, (
        "`CLAUDE.md` §8 nie mówi o pierwszeństwie pasma M — reguła kolejności "
        "zostałaby wtedy wyłącznie w `docs/TASKS.md`, czyli poza konstytucją")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.

# --- 6.D196: liczba w polu „Skąd" opisuje dzień pomiaru, a czyta się jak bieżącą -------
#
# **Trzy liczby, których pozycja żądała ze źródeł** (zmierzone 13.09.2026 na `0c1e499`,
# szesnaście pozycji otwartych): liczb w polach „Skąd" jest **80**, przeliczalnych
# automatem **30**, a **NIEZGODNYCH z drzewem — 15, czyli POŁOWA przeliczalnych**.
#
# **Rozjazd ma CZTERY przyczyny, a nie jedną, i to jest główny wynik.** Pozycja zakładała
# starzenie się w czasie; pomiar pokazał co innego:
#   (a) **cudza pozycja domknęła podstawę** — 10 z 15. 6.D184 zlikwidowało
#       `KodBezKomentarzy` (2 liczby), 6.D191 przepisało trzy zdania rodziny (7 liczb),
#       6.D193 dopisało brakujące asercje (1 liczba);
#   (b) **drzewo urosło** — 1 (mapa pokrycia, 35 647 → 35 969 wierszy);
#   (c) **liczba była nieprawdziwa W CHWILI WPISANIA** — 4. Tej kategorii teza pozycji
#       NIE PRZEWIDUJE: 6.D199 pisze o „dwóch trafieniach `phase.ToString()`", a trzecie
#       leży w `src/Game/UI/` od 10.09.2026, czyli było tam w dniu wpisania — liczba
#       powstała ze skanu PŁYTSZEGO NIŻ ZAPISANY. Tak samo 6.D201 („cztery postacie
#       literału" przy pięciu w `tests/`).
#
# **Pole „Skąd" cytujące inną pozycję starzeje się w CHWILI, gdy tamta zostaje domknięta
# — nie po dniach.** Dziesięć z piętnastu niezgodności jest właśnie takich.
#
# **Wszystkie 11 liczb przypiętych stałą zgadza się co do jedynki. Wszystkie 15
# niezgodnych to liczby, których NIC NIE PILNUJE.** Stąd bramka niżej.

#: Kształt twierdzenia, którego mechanizm z 6.D108 **NIE WIDZI**: nazwa stałej i liczba
#: w JEDNEJ parze grawisów. `CLAIM` z `test_report_claims.py` wymaga grawisów wyłącznie
#: wokół nazwy i zakazuje grawisa w przerwie do liczby — a tutaj grawis zamykający stoi
#: ZA liczbą, więc wzorzec się nie zaczepia.
#:
#: **Zmierzone, nie założone:** ten kształt pada w `docs/TASKS.md` **33 razy** (22 razy
#: z nazwą, którą drzewo zna) i w `reports/` **41 razy** (35 z nazwą znaną) — czyli cała
#: populacja, której tamta bramka nie ogląda, także w plikach, które skanuje.
CLAIM_W_JEDNYCH_GRAWISACH = re.compile(
    r"`([A-Z][A-Z0-9_]{3,})\s*=\s*(-?\d+(?:[.,]\d+)?)`")

#: Ile takich twierdzeń stoi w polach „Skąd" pozycji OTWARTYCH. Równość, bo każde jest
#: zdaniem, które następny agent przeczyta jako stan dzisiejszy.
#:
#: **2 -> 4 (13.09.2026, 6.D201), i to jest ROZSTRZYGNIĘCIE, nie dopisanie.** Ta bramka
#: zapaliła się na pozycji 6.D203, której pole „Skąd" cytowało `ZDAN_RODZINY_RAZEM = 19`
#: przy 24 w drzewie. Poprawka nie mogła polegać na podmianie liczby: pole „Skąd" opisuje
#: **dzień wpisania** i tamta dziewiętnastka jest tam prawdziwa — to ona jest powodem,
#: dla którego pozycja powstała. Dlatego w polu stoją teraz **obie** liczby, stara
#: z datą i dzisiejsza z nazwą stałej, a bramka liczy **cztery** twierdzenia zamiast
#: dwóch: po dwa na stałą. Rozjazd zrobiły trzy pozycje tego samego dnia (6.D191,
#: 6.D196, 6.D201) — czyli dokładnie tempo, dla którego ta bramka istnieje.
#: **4 -> 0 (14.09.2026, 6.D203) i jest to SPADEK POŻĄDANY, a nie regresja.**
#: Wszystkie cztery twierdzenia stały w polu „Skąd" pozycji **6.D203** — tej samej,
#: na której ta bramka zapaliła się dzień wcześniej. Pozycja została domknięta, więc
#: jej pole „Skąd" wypadło z populacji pozycji OTWARTYCH i liczba zeszła do zera.
#: Zero nie znaczy tu „bramka oślepła": skan po `docs/TASKS.md` widzi ten kształt
#: nadal, tylko w blokach domkniętych, których ta bramka świadomie nie ogląda —
#: bo zdanie w domkniętej pozycji jest zapisem przeszłości, a nie stanem dzisiejszym.
TWIERDZEN_W_POLACH_SKAD = 0


def _pole_skad(blok):
    """Treść pola `- **Skąd:**` bloku szczegółów albo `None`."""
    trafienie = re.search(r"- \*\*Skąd:\*\*(.*?)(?=\n- \*\*|\Z)", blok, re.S)
    return trafienie.group(1) if trafienie else None


def twierdzenia_w_polach_skad():
    """`[(pozycja, stała, liczba w polu, pole)]` — dla pozycji OTWARTYCH.

    Tylko otwarte, bo wiersz pozycji DOMKNIĘTEJ jest zapisem swojego dnia i przepisywaniu
    nie podlega (6.D108). Pole „Skąd" pozycji otwartej czyta się przeciwnie: jako stan,
    z którego bierze się rozmiar pracy.
    """
    tekst = open(TASKS, encoding="utf-8").read()
    otwarte = set(open_items(tekst))
    bloki = detail_sections(tekst)
    out = []
    for numer in sorted(otwarte):
        blok = bloki.get(numer)
        if not blok:
            continue
        pole = _pole_skad(blok)
        if pole is None:
            continue
        for nazwa, liczba in CLAIM_W_JEDNYCH_GRAWISACH.findall(pole):
            out.append((numer, nazwa, liczba, pole))
    return out


def _rowne(w_polu, w_drzewie):
    """Czy liczba z prozy jest tą samą, co w kodzie. Przecinek dziesiętny wchodzi."""
    def znormalizuj(x):
        x = str(x).replace(",", ".")
        return x.rstrip("0").rstrip(".") if "." in x else x
    return znormalizuj(w_polu) == znormalizuj(w_drzewie)


def test_twierdzenie_o_stalej_w_polu_SKAD_jest_prawdziwe_albo_PODAJE_DZISIEJSZA():
    """ODPOWIEDŹ 6.D196: rozstrzygnięciem jest DATOWANIE, i jest ono wykonalne.

    **Dlaczego nie „przelicz wszystkie liczby":** pole „Poza zakresem" tej pozycji
    zabrania poprawiania liczb, a 7 z 30 przeliczalnych automat i tak nie policzy
    (ile przebiegów CI, ile prób odtworzenia zjawiska, czyja ręka dopisała siedem miejsc).
    Bramka na nich świeciłaby na poprawnym tekście i zostałaby wyłączona, nie poprawiona.

    **Dlaczego akurat ten kształt:** bo jest to jedyna grupa, w której liczba **nazywa
    stałą**, więc dzisiejszą wartość da się odczytać z drzewa bez jednego osądu. Pozostałe
    liczby mają zapisaną granicę zamiast bramki i tak stoi to w komentarzu wyżej.

    **Warunek jest ALTERNATYWĄ, nie zakazem:** twierdzenie wolno zostawić nieaktualne,
    ale wtedy pole ma podać **dzisiejszą wartość obok**. Marker przeszłości tu nie
    wystarcza i to jest zmierzone: `HISTORICAL_MARKERS` z `test_docs_ci_claims.py` zawiera
    „zmierzone", a tym słowem zaczyna się niemal każde pole „Skąd" — warunek byłby
    spełniony zawsze, czyli bramka nie pilnowałaby niczego.
    """
    import test_report_claims as RC

    wartosci = RC.constant_values()
    znalezione = twierdzenia_w_polach_skad()
    znane = [(n, s, l, p) for n, s, l, p in znalezione if s in wartosci]

    assert len(znane) == TWIERDZEN_W_POLACH_SKAD, (
        "twierdzeń o nazwanej stałej w polach „Skąd” pozycji otwartych jest %d przy "
        "zapadce %d: %s — nowe ma być rozstrzygnięte, a nie dopisane"
        % (len(znane), TWIERDZEN_W_POLACH_SKAD,
           sorted((n, s) for n, s, _l, _p in znane)))

    sprawdzonych = 0
    for numer, stala, w_polu, pole in znane:
        w_drzewie = wartosci[stala]
        if not _rowne(w_polu, w_drzewie):
            # Nieaktualne WOLNO zostawić — ale pole ma powiedzieć, ile jest dziś.
            assert str(w_drzewie) in pole or _rowne(str(w_drzewie), w_polu), (
                "pozycja %s podaje `%s = %s`, w drzewie jest %s, a pole „Skąd” nigdzie "
                "nie mówi, ile jest DZIŚ — następny agent przeczyta tę liczbę jako stan "
                "bieżący i z niej oszacuje pracę. Albo popraw, albo dopisz dzisiejszą "
                "obok (6.D196)" % (numer, stala, w_polu, w_drzewie))
        sprawdzonych += 1

    assert sprawdzonych == len(znane), (
        "pętla twierdzeń wykonała %d obrotów przy %d twierdzeniach — pusta pętla "
        "przechodzi każdą asercję w środku (zmierzone przy 6.D193)"
        % (sprawdzonych, len(znane)))


def test_czytnik_twierdzen_WIDZI_ksztalt_ktorego_6D108_nie_widzi():
    """Kontrola PRZYRZĄDU: dwa kształty obok siebie, jeden widziany, drugi nie.

    Bez niej „dwa twierdzenia" nie znaczyłoby nic: czytnik niewidzący kształtu
    odpowiedziałby zerem tak samo, jak czytnik widzący i nieznajdujący (rodzina 6.D159).
    Wejście wymienia też kształt, który mechanizm z 6.D108 **łapie**, żeby było widać,
    że te dwa wzorce opisują różne rzeczy, a nie jeden drugiego.
    """
    import test_report_claims as RC

    widziany = "stała `MIN_REPORTS = 314` stoi w module"
    assert CLAIM_W_JEDNYCH_GRAWISACH.findall(widziany) == [("MIN_REPORTS", "314")], (
        "czytnik nie widzi kształtu `NAZWA = N` — a to jest jedyny kształt, po który "
        "ta sekcja istnieje")
    assert RC.CLAIM.findall(widziany) == [], (
        "mechanizm z 6.D108 jednak widzi ten kształt — wtedy ta sekcja opisuje lukę, "
        "której nie ma, i trzeba ją przeliczyć")

    stary = "stała `MIN_REPORTS` stoi dziś na 314"
    assert CLAIM_W_JEDNYCH_GRAWISACH.findall(stary) == [], (
        "czytnik łapie kształt, którego 6.D108 już pilnuje — dwie bramki na to samo "
        "zdanie dałyby dwa komunikaty o jednej usterce")
    assert RC.CLAIM.findall(stary), (
        "mechanizm z 6.D108 nie widzi własnego kształtu — wtedy nie o nim mowa")

    for milczy in ("`ZWYKLY_NAPIS = abc`", "`ab = 3`", "MIN_REPORTS = 314"):
        assert CLAIM_W_JEDNYCH_GRAWISACH.findall(milczy) == [], (
            "czytnik zapalił się na %r — wtedy liczba dwóch twierdzeń opisuje co innego, "
            "niż mówi" % milczy)

    # ZAWĘŻENIE POLA „SKĄD" JEST DZIŚ BEZCZYNNE I DLATEGO MA WEJŚCIE SYNTETYCZNE.
    # Zmierzone kontrolą negatywną (KN-6): poszerzenie czytnika do KOŃCA bloku nic nie
    # zmienia, bo żadna pozycja otwarta nie ma dziś twierdzenia `NAZWA = N` poza polem
    # „Skąd". Zawężenie jest słuszne — pozycja pyta o to pole i tylko o nie — ale drzewo
    # go nie ćwiczy, więc bez tego wejścia byłoby mechanizmem bez kontroli (6.D159).
    blok = ("##### 6.X1 · próbny\n\n"
            "- **Skąd:** nic tu nie stoi.\n"
            "- **Wyjście:** `MIN_REPORTS = 40` — to pole NIE jest polem „Skąd”.\n")
    assert _pole_skad(blok) is not None, "czytnik nie znalazł pola „Skąd” w bloku próbnym"
    assert CLAIM_W_JEDNYCH_GRAWISACH.findall(_pole_skad(blok)) == [], (
        "czytnik pola „Skąd” sięgnął do NASTĘPNEGO pola — wtedy bramka pilnuje całego "
        "bloku, a nie tego, o co pyta 6.D196, i liczba twierdzeń przestaje znaczyć to, "
        "co mówi: %r" % _pole_skad(blok))

    z_polem = blok.replace("- **Skąd:** nic tu nie stoi.",
                           "- **Skąd:** stała `MIN_REPORTS = 40` z dnia pomiaru.")
    assert CLAIM_W_JEDNYCH_GRAWISACH.findall(_pole_skad(z_polem)) == [("MIN_REPORTS", "40")], (
        "czytnik NIE widzi twierdzenia stojącego w samym polu „Skąd” — wtedy zero "
        "znalezionych nie odróżnia „nie ma” od „nie umiem zobaczyć”")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
