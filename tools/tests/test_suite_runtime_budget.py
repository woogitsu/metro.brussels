#!/usr/bin/env python3
"""6.D11: próg czasu ściany dla `python3 tools/tests/test_all.py` w CI.

**Dlaczego próg NIE siedzi w `test_all.py`.** Kod wyjścia tamtego pliku czyta
`tools/tests/mutation_sweep.py` (`run_suite`, regex `SUMMARY`): mutacja jest uznana
za PRZEŻYTĄ dokładnie wtedy, gdy linia `N/M przeszło` mówi `N == M` **i** kod wyjścia
jest zerowy. Gdyby `main()` w `test_all.py` zwracał 1 również przy przekroczeniu
czasu, zwykłe spowolnienie współdzielonej maszyny — a ta jest współdzielona, patrz
niżej — zamieniłoby się w falę fałszywych „zabić" mutacyjnych, tej samej rodziny co
`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`, tylko odwróconej: nie fałszywe
przeżycie, tylko fałszywa śmierć. Bramka czasu żyje więc w kroku CI (`.github/
workflows/python-tests.yml`), PO zakończeniu procesu — `test_all.py` sam wypisuje
tylko czas, nie ocenia go.

**Skąd próg.** Zmierzone 06.09.2026 na commicie `045730bd639c771d59b6d3b876c4d390d85f16ad`,
cztery przebiegi CAŁEGO procesu `python3 tools/tests/test_all.py` z rzędu, bez ŻADNEJ
zmiany kodu i przy stałych 1709 testach: **66,20 / 68,45 / 68,96 / 77,04 s**
(`time.perf_counter()` od uruchomienia procesu do jego zakończenia, mierzone z
zewnątrz — nie licznik wewnętrzny `test_all.py`, który liczy tylko samą pętlę testów
i wypada o ok. 1-2 s niżej, bo pomija import i odkrywanie modułów). Maszyna jest
KONTENEREM DZIELONYM z innymi sesjami agenta — `ps aux` w trakcie pomiaru pokazywał
równoległy `dotnet build` i proces Godota z sąsiedniego katalogu roboczego — stąd
rozrzut 10,84 s na średniej 70,16 s (15,45 % względem średniej, 16,37 % względem
najniższego pomiaru) przy tym samym kodzie i tej samej liczbie testów. Pełna tabela
per moduł: `reports/test-all-runtime-gate.md`.

**Skąd mnożnik.** `SUITE_RUNTIME_BUDGET_S` to NIE najwyższy zmierzony czas — to
najwyższy zmierzony czas razy margines, bo próg ma przeżyć DWIE rzeczy, których żadna
sesja nie zmierzyła: (1) maszyna właściciela (`woogitsu`, `CLAUDE.md` §9) chodzi gdzie
indziej, z nieznaną prędkością i własnym wzorcem obciążenia; (2) zestaw rośnie z każdym
zadaniem — o kilkadziesiąt testów dziennie — a próg dostrojony tuż nad dzisiejszym
maksimum wymagałby przeliczania co kilka dni, czyli przestałby być bramką, a stałby się
rytuałem.

**Ile ten margines wynosi, ten plik już nie twierdzi prozą — LICZY.** Ten akapit jest
przepisany, a nie dopisany obok (6.D26). Poprzednia wersja podawała mnożnik **wprost
w tekście**, a komentarz przy teście marginesu podawał **drugi, inny** — oba wyliczone
kiedyś wobec `MEASURED_MAX_WALL_S` wpisanego z ręki 05.09.2026, oba prawdziwe tamtego
dnia i oba **przestały być prawdziwe, nie zmieniając ani znaku**, gdy 07.09.2026 ten sam
zestaw zmierzył 107,33 s. Te dwie liczby stoją teraz w
`reports/zapis-czasu-zestawu.md`, gdzie są historią, a nie w kodzie, gdzie wyglądałyby
na obowiązujące. Nic tego nie zgłosiło, bo margines liczył się wobec
zapisanej liczby, nie wobec czegokolwiek zmierzonego później — a to jest dokładnie ten
kształt usterki, którego pilnuje `test_report_claims.py` dla stałych cytowanych
w raportach, tylko schowany we własnym docstringu bramki.

Teraz maksimum jest wyprowadzane z listy `POMIARY`, margines stoi w `MARGIN` jako
działanie, a osobny test pilnuje, żeby żadna liczba w tej prozie nie rozjechała się
z liczbą w kodzie. Próg 150,0 zostaje **nietknięty**: jego zmiana jest decyzją
o czułości bramki, a nie skutkiem ubocznym poprawiania zapisu pomiaru.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "python-tests.yml")

#: Dwie maszyny, na których ten zestaw bywa mierzony. Nazwy są zamknięte, bo od nich
#: zależy, KTÓRE pomiary wchodzą do marginesu — a wolny tekst w polu „na czym" dawał
#: dotąd odpowiedź, której nie dało się policzyć.
MASZYNA_RUNNER = "runner"
MASZYNA_KONTENER = "kontener"
MASZYNY = (MASZYNA_RUNNER, MASZYNA_KONTENER)

#: Przebiegi, które KTOŚ NAPRAWDĘ ZMIERZYŁ: (data, sekundy, modułów, maszyna, na czym).
#:
#: **Lista, a nie jedna liczba — poprawka na konkretną usterkę (6.D26).** Do tamtej
#: pozycji `MEASURED_MAX_WALL_S = 77.04` była wpisana z ręki jako „najwyższy z czterech
#: przebiegów" jednej, minionej sesji. Liczba wpisana raz opisuje dzień, w którym ją
#: wpisano; 07.09.2026 ten sam zestaw dawał **107,33 s**, czyli o 39 % więcej — a nic
#: tego nie zgłaszało. Obie nieaktualne wartości stoją w `reports/zapis-czasu-zestawu.md`.
#:
#: **Pole MASZYNY jest nowe (6.D135) i rozstrzyga, czego margines dotyczy.** Do
#: 11.09.2026 lista mieszała dwie maszyny pod jednym wolnym tekstem („host spokojny",
#: „kontener dzielony"), a `MEASURED_MAX_WALL_S` brało maksimum ze wszystkich.
#: Zmierzone tego dnia, przy 122 modułach i 2335 testach:
#:
#:   runner, sześć przebiegów CI   89,5–116,4 s ściany, CPU/ściana **1,599–1,971**
#:   kontener sesji, jeden przebieg  **170,685 s** ściany, CPU/ściana **0,991**
#:
#: **Kontener przekracza dziś próg o 14 % i podłoga mierzalności go NIE zatrzymuje**
#: — 0,991 stoi wysoko nad `MIERZALNOSC_MIN` (0,75), więc `werdykt` uznałby ten pomiar
#: za „pomiar kodu" i odrzucił. Test niżej wykonuje ten rachunek, żeby zdanie nie było
#: opinią. Nie jest to usterka bramki: bramka chodzi WYŁĄCZNIE na runnerze, w kroku
#: „Run tool tests". Jest to natomiast dowód, że **jedna lista na dwie maszyny daje
#: margines nieprawdziwy dla obu** — dokładnie to, o co pytała pozycja 6.D135.
#:
#: Runner liczy zestaw RÓWNOLEGLE (CPU/ściana powyżej jedynki), kontener szeregowo
#: (0,99). To nie są te same przebiegi tego samego zestawu — to dwa różne pomiary
#: tej samej pracy, i porównywanie ich jednym progiem nie ma sensu w żadną stronę.
#:
#: Pomiarów się nie przelicza ani nie nadpisuje: 77,04 zostaje jako pomiar swojego dnia.
#:
#: **Od 6.D160 kontener ma na jednym drzewie SZEŚĆ przebiegów, nie jeden.** Ten akapit
#: jest dopisany, a nie przepisany: zdanie wyżej o jednym przebiegu opisuje 11.09.2026
#: i zostaje prawdą tamtego dnia. Zmierzone 13.09.2026, 124 moduły, 2414 testów:
#:
#:   kontener sesji, sześć przebiegów   167,402–171,842 s, CPU/ściana 0,987–0,988
#:
#: **Rozrzut wynosi 2,65 %, a rekord padł na przebiegu PIERWSZYM i już się nie ruszył.**
#: Teza, z którą 6.D160 wchodziła („próg z n=1 byłby liczbą wpisaną z ręki"), jest tym
#: obalona: `max(n=1)` i `max(n=6)` to ta sama liczba. Tym, co zestarzało
#: `MEASURED_MAX_WALL_S = 77.04` przed 6.D26, był DRYF DRZEWA — 76,518 s przy
#: 93 modułach wobec 170,5 s przy 124 — czterdziestokrotnie większy od rozrzutu
#: powtórzeń, i żadną ich liczbą nienaprawialny. Rachunek robi
#: `test_powtorzenia_kontenera_NIE_ruszaja_maksimum_a_dryf_drzewa_rusza`.
POMIARY = (
    ("2026-09-05", 77.04, None, MASZYNA_KONTENER,
     "najwyższy z czterech przebiegów tamtej sesji; kontener DZIELONY, `ps aux` "
     "pokazywał równoległy `dotnet build` i proces Godota"),
    ("2026-09-07", 76.518, 93, MASZYNA_KONTENER,
     "po 6.B30 (pamięć na układ peronów), host spokojny"),
    ("2026-09-07", 102.122, 93, MASZYNA_KONTENER,
     "ten sam kod, host pod obciążeniem: `test_station_layout` mierzył wtedy 34,9 s "
     "wobec 22,7 s godzinę wcześniej — 1,54x rozrzutu na jednym module, "
     "potwierdzone identycznym pomiarem w drzewie sprzed 6.A18"),
    ("2026-09-07", 83.083, 95, MASZYNA_KONTENER,
     "po 6.A20, dwa moduły bramek więcej"),
    ("2026-09-07", 107.331, 95, MASZYNA_KONTENER,
     "to samo drzewo, host pod obciążeniem — najwyższy zmierzony W KONTENERZE do 11.09"),
    ("2026-09-11", 89.518, 122, MASZYNA_RUNNER,
     "job `tools`, PR #524, CPU/ściana 1,971 — 2315 testów"),
    ("2026-09-11", 92.119, 122, MASZYNA_RUNNER,
     "job `tools`, PR #525, CPU/ściana 1,857 — 2320 testów"),
    ("2026-09-11", 97.863, 122, MASZYNA_RUNNER,
     "job `tools`, PR #526, CPU/ściana 1,801 — 2326 testów"),
    ("2026-09-11", 100.654, 122, MASZYNA_RUNNER,
     "job `tools`, PR #527, CPU/ściana 1,810 — 2330 testów"),
    ("2026-09-11", 109.420, 122, MASZYNA_RUNNER,
     "job `tools`, PR #529, CPU/ściana 1,610 — 2335 testów"),
    ("2026-09-11", 116.404, 122, MASZYNA_RUNNER,
     "job `tools`, PR #528, CPU/ściana 1,599 — 2335 testów"),
    ("2026-09-11", 170.685, 122, MASZYNA_KONTENER,
     "kontener sesji, maszyna spokojna, CPU/ściana 0,991 — 2335 testów; PRZEKRACZA "
     "próg 150 s i podłoga mierzalności tego nie zatrzymuje, patrz komentarz wyżej"),
    # SZEŚĆ POWTÓRZEŃ NA JEDNYM DRZEWIE — 6.D160. Do tej pozycji kontener miał na
    # dzisiejszym drzewie JEDEN przebieg, więc rozrzutu nie było z czego policzyć.
    # Sześć poniżej zrobiono jedno po drugim, tym samym przyrządem, co krok CI
    # („Run tool tests" w `python-tests.yml`): `times` przed i po, `date +%s.%N`
    # na ścianie, CPU z `cpu_dzieci`. Czyszczenie `__pycache__` przed każdym.
    ("2026-09-13", 171.842, 124, MASZYNA_KONTENER,
     "kontener sesji, powtórzenie 1 z 6, CPU/ściana 0,987 — 2414 testów"),
    ("2026-09-13", 170.788, 124, MASZYNA_KONTENER,
     "kontener sesji, powtórzenie 2 z 6, CPU/ściana 0,988 — 2414 testów"),
    ("2026-09-13", 170.018, 124, MASZYNA_KONTENER,
     "kontener sesji, powtórzenie 3 z 6, CPU/ściana 0,987 — 2414 testów"),
    ("2026-09-13", 171.500, 124, MASZYNA_KONTENER,
     "kontener sesji, powtórzenie 4 z 6, CPU/ściana 0,988 — 2414 testów"),
    ("2026-09-13", 167.402, 124, MASZYNA_KONTENER,
     "kontener sesji, powtórzenie 5 z 6, CPU/ściana 0,987 — 2414 testów"),
    ("2026-09-13", 171.467, 124, MASZYNA_KONTENER,
     "kontener sesji, powtórzenie 6 z 6, CPU/ściana 0,988 — 2414 testów"),
    # SIÓDMY I ÓSMY PRZEBIEG RUNNERA — 6.D190. Do tej pozycji lista miała ich sześć
    # i wszystkie z jednego dnia; siódmy leżał zmierzony w polu „Skąd" pozycji
    # i nie wchodził, bo asercja przypinała gołą szóstkę. ŻADEN nie rusza maksimum
    # (116,404 s z 11.09), więc `MEASURED_MAX_WALL_S` i `MARGIN` zostają — a zmiana
    # progu jest poza zakresem tej pozycji.
    #
    # OBA WPISY SĄ WYPISANE PRZEZ `tools/ci/timing_record.py --z-logu`, a nie
    # przepisane z ręki, i to nie jest wygoda — to WARUNEK. Od 6.D152 każdy wpis
    # runnera musi mieć swój log joba w `tests/data/ci-logs/`, a `test_timing_record`
    # wyprowadza z niego wszystkie pięć pól i porównuje znak w znak; `WPISOW_Z_DOPISKIEM`
    # jest od 6.D163 równe ZERO, więc każde własne zdanie dopisane do pola „na czym"
    # zapala bramkę. Pierwsza wersja tych dwóch wpisów była pisana z ręki i miała
    # w sobie trzy usterki naraz: datę 2026-09-12 przy logu mówiącym 2026-09-13,
    # ogon „pierwszy przebieg runnera, który NIE ustanowił nowego maksimum" (zdanie
    # o LIŚCIE, nie o przebiegu — rodzina 6.B28, ta sama, którą 6.D163 zdjęło),
    # i „2433 testy" tam, gdzie log daje „2433 testów".
    ("2026-09-13", 104.530, 124, MASZYNA_RUNNER,
     "job `tools`, PR #571, CPU/ściana 1,819 — 2414 testów"),
    ("2026-09-13", 113.982, 124, MASZYNA_RUNNER,
     "job `tools`, PR #583, CPU/ściana 1,781 — 2433 testów"),
)

#: Pomiar, do którego bramka ma prawo się odnosić: wyłącznie z maszyny, NA KTÓREJ
#: CHODZI. Krok „Run tool tests" stoi w `python-tests.yml`, a ten workflow ma
#: `runs-on: self-hosted` — więc porównanie z progiem zdarza się tylko na runnerze.
#: Wpis kontenerowy z 11.09.2026 (170,685 s) jest w liście po to, żeby było widać,
#: czego margines NIE dotyczy; gdyby wchodził do maksimum, próg 150 s byłby już
#: przekroczony przez sam ZAPIS, bez jednego regresu w kodzie.
POMIARY_RUNNERA = tuple(w for w in POMIARY if w[3] == MASZYNA_RUNNER)

#: Najwyższy ZMIERZONY przebieg, wyprowadzony z `POMIARY`. Stała osobna od
#: `SUITE_RUNTIME_BUDGET_S`, żeby dało się sprawdzić SAM margines (test niżej), a nie
#: tylko to, że próg jest jakąś liczbą dodatnią.
MEASURED_MAX_WALL_S = max(sekundy for _d, sekundy, _m, _maszyna, _g in POMIARY_RUNNERA)

#: Próg bramki CI. Czytany z TEGO pliku przez krok „Run tool tests" w
#: `python-tests.yml` (`python3 -c "... import test_suite_runtime_budget ..."`) —
#: jedno miejsce prawdy, nie liczba wpisana w YAML z ręki.
SUITE_RUNTIME_BUDGET_S = 150.0

#: Margines progu nad najwyższym zmierzonym przebiegiem — LICZONY, nie opisany prozą.
#: Poprzednia wersja nosiła tę liczbę w komentarzu, wpisaną z ręki — i to właśnie
#: zdanie zestarzało się bez śladu, bo nic nie łączyło go z liczbami obok. Ile wtedy
#: podawało, stoi w `reports/zapis-czasu-zestawu.md`, gdzie jest historią.
MARGIN = SUITE_RUNTIME_BUDGET_S / MEASURED_MAX_WALL_S


#: Wzorzec wiersza wyjścia wbudowanego `times`: `0m0.002s 0m0.000s`.
TIMES_WIERSZ = re.compile(r"^(\d+)m([\d.]+)s\s+(\d+)m([\d.]+)s\s*$")


def cpu_dzieci(sciezka):
    """Czas CPU DZIECI powłoki (user + sys) z pliku zapisanego przez `times`.

    **Po co to jest (6.D42).** Bramka czasu ściany porównywała jedną liczbę
    z progiem i nie miała jak odróżnić „zestaw zwolnił" od „maszyna była zajęta".
    Zmierzone 09.09.2026 w kontenerze sesji, 4 rdzenie, ten sam kod zestawu:

        maszyna spokojna    ściana  91,7 s   CPU  90,5 s   CPU/ściana 0,987
        maszyna obciążona   ściana 203,9 s   CPU  91,9 s   CPU/ściana 0,451

    Czas CPU jest **niemal niezmienny** (+1,5 %), gdy ściana rośnie 2,2x. Stosunek
    CPU do ściany jest więc sygnałem mierzalności, i to darmowym — w odróżnieniu
    od drugiego przebiegu zestawu, który kosztuje tyle, co pierwszy, a rozstępu
    NIE pokazuje: dwa przebiegi na obciążonej maszynie różnią się o 1,63 %, czyli
    tyle samo co dwa na spokojnej (0,13 %). Pomiar: `reports/mierzalnosc-czasu-zestawu.md`.

    **Dlaczego plik, a nie `$(times)`.** Wbudowane `times` w podstawieniu
    poleceń zwraca same zera — zmierzone, nie założone: podpowłoka nie dziedziczy
    naliczonych czasów dzieci. Z przekierowaniem do pliku, w tej samej powłoce,
    zwraca prawdziwe wartości.
    """
    wiersze = [w for w in open(sciezka, encoding="utf-8").read().splitlines() if w.strip()]
    if len(wiersze) < 2:
        raise ValueError(f"{sciezka}: wyjście `times` ma mieć dwa wiersze, ma {len(wiersze)}")
    dopasowanie = TIMES_WIERSZ.match(wiersze[1])
    if dopasowanie is None:
        raise ValueError(f"{sciezka}: drugi wiersz nie wygląda jak wyjście `times`: {wiersze[1]!r}")
    minuty_u, sekundy_u, minuty_s, sekundy_s = dopasowanie.groups()
    return int(minuty_u) * 60 + float(sekundy_u) + int(minuty_s) * 60 + float(sekundy_s)


def over_budget(elapsed_s, budget_s=SUITE_RUNTIME_BUDGET_S):
    """Czy zmierzony czas ściany przekracza próg. Równość progu NIE jest przekroczeniem —

    ta sama konwencja, co gdzie indziej w tym repo dla granic włącznie (np.
    `PARALLEL_M jest granicą włącznie` w `test_report_claims.py`).
    """
    return elapsed_s > budget_s


#: PODŁOGA STOSUNKU CPU/ŚCIANA — poniżej niej czas ściany NIE JEST porównywany
#: z progiem, bo nie mówi o kodzie, tylko o maszynie (6.D42).
#:
#: WSZYSTKIE LICZBY, Z KTÓRYCH TA JEDNA WYSZŁA, zmierzone 09.09.2026:
#:
#:   kontener sesji, 4 rdzenie, maszyna spokojna    CPU/ściana  0,987 i 0,988
#:   kontener sesji, 4 rdzenie, 8 procesów w tle    CPU/ściana  0,451 i 0,444
#:   runner `metro-wsl-DOM-NEW-*`, job `tools`      CPU/ściana  1,323 i 1,361
#:
#: Runner jest POWYŻEJ JEDYNKI i to nie jest błąd odczytu: zestaw dostaje tam
#: więcej niż jeden rdzeń na sekundę ściany (53,517 s ściany przy 70,804 s CPU).
#: Podłoga musi więc leżeć poniżej najniższego zmierzonego przebiegu BEZ obciążenia
#: (0,987 w kontenerze) i powyżej najwyższego POD obciążeniem (0,451). Środek tego
#: przedziału to 0,719; wybrane **0,75** zostawia 24 % zapasu pod spokojnym
#: kontenerem i 66 % nad obciążonym, a stosunek zmierzony na runnerze (1,323) stoi
#: o 76 % powyżej tej podłogi.
#:
#: KIERUNEK BŁĘDU JEST BEZPIECZNY I TO JEST CZĘŚĆ WYBORU. Zbyt wysoka podłoga
#: NIE czerwieni CI — sprawia, że porównanie z progiem zostaje pominięte, a wiersz
#: o tym trafia do logu. Zbyt niska przepuszcza wolny przebieg do porównania, czyli
#: zachowuje się jak bramka sprzed tej zmiany. Fałszywy alarm, który wyłącza bramki
#: (6.D27), jest tu więc niemożliwy z konstrukcji.
#:
#: Runner ma dziś DWA pomiary (n=2, rozrzut 2,9 %) i to jest granica tej liczby,
#: wypisana razem z nią: `reports/mierzalnosc-czasu-zestawu.md` §5.
MIERZALNOSC_MIN = 0.75

#: Maszyna, na której próg został SKALIBROWANY — 6.D149.
#:
#: `SUITE_RUNTIME_BUDGET_S` wychodzi z `MEASURED_MAX_WALL_S`, a to bierze wyłącznie
#: `POMIARY_RUNNERA`. Próg opisuje więc runnera i nikogo więcej; dla maszyny innej
#: niż ta porównanie z nim jest zdaniem o czymś, czego nikt nie mierzył.
MASZYNA_PROGU = MASZYNA_RUNNER


def werdykt(elapsed_s, cpu_s, budget_s=SUITE_RUNTIME_BUDGET_S, podloga=MIERZALNOSC_MIN,
            maszyna=MASZYNA_PROGU):
    """Czy przebieg wolno porównać z progiem, i czy go przekroczył.

    Zwraca `(czy_odrzucic, komunikat)`. Odrzucenie znaczy „ten zestaw naprawdę
    przekroczył próg"; przebieg niemierzalny NIE jest odrzucany — jest opisany.

    Wzorem jest bliźniak z `tools/ci/assert_linecore_budget.py`, który tę samą
    rodzinę rozwiązał przy 6.D41: tam sygnałem jest rozstęp dziewięciu powtórzeń,
    tutaj stosunek CPU do ściany, bo zestaw chodzi RAZ i rozstępu nie ma z czego
    policzyć (`reports/mierzalnosc-czasu-zestawu.md` §2).

    **Warunki są DWA i od 6.D149 są rozdzielone — to jest rozstrzygnięcie tamtej
    pozycji.** Podłoga odpowiada na pytanie „czy ten pomiar mówi o KODZIE, czy
    o maszynie"; maszyna — na pytanie „czy ten PRÓG mówi o tej maszynie". Kontener
    sesji przechodzi pierwszy warunek (stosunek 0,991, wysoko nad podłogą 0,75)
    i nie przechodzi drugiego, a do 6.D149 była to jedna rzecz i pomiar kontenera
    dostawał odpowiedź progu, który jego nie dotyczy.

    **Kolejność jest tu treścią.** Maszyna rozstrzyga PIERWSZA, bo komunikat podłogi
    obiecuje „ten pomiar nie mówi nic o kodzie" — a dla spokojnego kontenera jest to
    nieprawda: 0,991 znaczy, że mówi. Nie mówi o tym PROGU. Dwa różne odmówienia,
    i zlanie ich w jedno było usterką, którą ta pozycja zamyka.
    """
    if elapsed_s <= 0:
        raise ValueError(f"czas ściany musi być dodatni, jest {elapsed_s}")
    stosunek = cpu_s / elapsed_s
    if maszyna != MASZYNA_PROGU:
        return False, (
            f"prog {budget_s} s jest skalibrowany na maszynie `{MASZYNA_PROGU}` "
            f"(z `POMIARY_RUNNERA`), a ten pomiar jest z `{maszyna}` — czas sciany "
            f"{elapsed_s:.3f} s NIE JEST z nim porownywany. Stosunek CPU/sciana "
            f"{stosunek:.3f} mowi, ze pomiar jest rzetelny; mowi tylko o innej "
            "maszynie niz ta, ktora prog opisuje")
    if stosunek < podloga:
        return False, (
            f"stosunek CPU/sciana {stosunek:.3f} jest ponizej podlogi {podloga}, "
            f"wiec czas sciany {elapsed_s:.3f} s NIE JEST porownywany z progiem "
            f"{budget_s} s — ten pomiar nie mowi nic o kodzie, tylko o maszynie, "
            "na ktorej go zrobiono")
    if over_budget(elapsed_s, budget_s):
        return True, (
            f"zestaw test_all.py przekroczyl prog czasu sciany: {elapsed_s:.3f} s "
            f"> {budget_s} s przy stosunku CPU/sciana {stosunek:.3f} "
            f"(podloga mierzalnosci {podloga}) — maszyna oddawala CPU, wiec to jest "
            "pomiar kodu")
    return False, (f"czas sciany {elapsed_s:.3f} s w progu {budget_s} s, "
                   f"stosunek CPU/sciana {stosunek:.3f} (podloga {podloga})")


def _workflow_text():
    with open(WORKFLOW, encoding="utf-8") as handle:
        return handle.read()


def test_budget_constant_is_a_sane_positive_number():
    assert isinstance(SUITE_RUNTIME_BUDGET_S, float)
    assert 30.0 < SUITE_RUNTIME_BUDGET_S < 900.0, SUITE_RUNTIME_BUDGET_S


def test_budget_stays_above_the_measured_maximum_with_a_real_margin():
    """Bramka na samą bramkę.

    Bez tego testu ktoś mógłby obniżyć `SUITE_RUNTIME_BUDGET_S` poniżej
    `MEASURED_MAX_WALL_S` bez żadnego ostrzeżenia — a próg niższy niż to, co
    już zostało zmierzone na spokojnej maszynie, zapala się na czerwono od
    samego sąsiedztwa na runnerze, bez żadnego regresu w kodzie.
    """
    assert SUITE_RUNTIME_BUDGET_S > MEASURED_MAX_WALL_S, (
        SUITE_RUNTIME_BUDGET_S, MEASURED_MAX_WALL_S)
    # Test żąda tylko, żeby margines NIE stopniał do czegoś ciasnego przy przyszłej
    # edycji — próg 1.2 łapie „obniżono do 78". Ile margines wynosi DZIŚ, mówi `MARGIN`,
    # liczone z `POMIARY`; wpisanie tu drugiej liczby z ręki byłoby powtórzeniem błędu,
    # który naprawiło 6.D26.
    assert MARGIN > 1.2, (MARGIN, SUITE_RUNTIME_BUDGET_S, MEASURED_MAX_WALL_S)


def test_every_recorded_run_says_when_and_on_what_it_was_measured():
    """Pomiar bez daty i bez kontekstu jest nierozstrzygalny.

    O to poszlo w 6.D26: `MEASURED_MAX_WALL_S = 77.04` nie mowilo ANI kiedy powstalo,
    ANI ze host jest kontenerem dzielonym — wiec czytajacy nie mial jak odroznic
    „zestaw przyspieszyl" od „tamtego dnia maszyna byla spokojna". Kazdy wpis musi
    nosic jedno i drugie.
    """
    assert len(POMIARY) >= 2, (
        "jeden pomiar nie pozwala odroznic regresu od rozrzutu hosta — po to jest lista")
    for data, sekundy, moduly, maszyna, gdzie in POMIARY:
        assert re.fullmatch(r"20\d\d-\d\d-\d\d", data), data
        assert isinstance(sekundy, float) and 10.0 < sekundy < 900.0, (data, sekundy)
        assert moduly is None or isinstance(moduly, int), (data, moduly)
        assert maszyna in MASZYNY, (
            "pomiar bez maszyny z zamknietej listy: %r — od tego pola zalezy, ktore "
            "przebiegi wchodza do marginesu (6.D135)" % ((data, maszyna),))
        assert len(gdzie) > 25, (
            "kontekst ma mowic, na czym i w jakich warunkach: " + repr((data, gdzie)))

    # Obie maszyny muszą być reprezentowane — inaczej podział na `POMIARY_RUNNERA`
    # jest podziałem na zbiór pełny i pusty, czyli nie robi nic, a wygląda, że robi.
    obecne = {maszyna for _d, _s, _m, maszyna, _g in POMIARY}
    assert obecne == set(MASZYNY), (
        "lista opisuje tylko %s — podzial na maszyny ma sens dopiero wtedy, gdy obie "
        "cos wnosza" % sorted(obecne))


def test_the_recorded_maximum_is_derived_not_typed_in():
    """Maksimum wyprowadzone, nie wpisane — inaczej dopisanie pomiaru nie zmienia
    niczego i lista staje sie ozdoba obok liczby, ktora nadal rzadzi."""
    assert MEASURED_MAX_WALL_S == max(s for _d, s, _m, _maszyna, _g in POMIARY_RUNNERA), (
        "maksimum %.3f s nie jest najwyzszym przebiegiem runnera z POMIARY — "
        "stala przestala byc wyprowadzona" % MEASURED_MAX_WALL_S)
    with open(__file__, encoding="utf-8") as uchwyt:
        source = uchwyt.read()
    assert not re.search(r"^MEASURED_MAX_WALL_S\s*=\s*[\d.]+\s*$", source, re.M), (
        "maksimum wpisane z reki zamiast wyprowadzone z POMIARY")

    # **I ze bierze WYLACZNIE runnera.** Maksimum z calej listy jest dzis WYZSZE od
    # progu — wpis kontenerowy z 11.09.2026 ma 170,685 s przy progu 150,0 s. Gdyby
    # wchodzil do marginesu, bramka na wlasna bramke zapalilaby sie od samego ZAPISU,
    # bez jednego regresu w kodzie, i jedynym wyjsciem byloby podniesienie progu albo
    # skasowanie pomiaru — czyli dokladnie to, czemu ta lista ma zapobiegac.
    max_wszystkich = max(s for _d, s, _m, _maszyna, _g in POMIARY)
    assert max_wszystkich > SUITE_RUNTIME_BUDGET_S > MEASURED_MAX_WALL_S, (
        "maksimum z calej listy %.3f s, z runnera %.3f s, prog %.1f s — jesli te "
        "trzy liczby przestaly stac w tej kolejnosci, podzial na maszyny stracil "
        "powod, dla ktorego powstal (6.D135)"
        % (max_wszystkich, MEASURED_MAX_WALL_S, SUITE_RUNTIME_BUDGET_S))


#: Pomiar kontenera z 11.09.2026, rozbity na człony, bo test niżej WYKONUJE na nim
#: `werdykt`, a nie opowiada o nim. Ściana i CPU z jednego przebiegu: `resource
#: .getrusage(RUSAGE_CHILDREN)` wokół `subprocess.run` na zestawie, drzewo `9549df6`.
KONTENER_11_09_SCIANA = 170.685
KONTENER_11_09_CPU = 169.185


def test_kontener_przekroczylby_prog_i_podloga_by_go_NIE_zatrzymala():
    """**Sedno 6.D135, wykonane jako rachunek. Od 6.D149 ma DRUGA polowe.**

    Podłoga mierzalności (6.D42) powstała po to, żeby czas maszyny OBCIĄŻONEJ nie był
    porównywany z progiem — zmierzone wtedy stosunki to 0,451 i 0,444 pod obciążeniem
    wobec 0,987 na spokojnym kontenerze. Kontener SPOKOJNY leży więc wysoko **nad**
    podłogą i podłoga go nie dotyczy — a jego czas ściany urósł od tamtego dnia na tyle,
    że dziś przekracza próg.

    Bramka na tym nie cierpi, bo chodzi WYŁĄCZNIE na runnerze. Cierpiałaby LISTA, gdyby
    jednym progiem opisywać obie maszyny — i to jest powód, dla którego `MEASURED_MAX_WALL_S`
    bierze dziś tylko `POMIARY_RUNNERA`.
    """
    stosunek = KONTENER_11_09_CPU / KONTENER_11_09_SCIANA
    assert stosunek > MIERZALNOSC_MIN, (
        "kontener spadl ponizej podlogi mierzalnosci (%.3f < %.2f) — wtedy teza tego "
        "testu przestaje byc prawdziwa i podzial na maszyny trzeba przemyslec od nowa"
        % (stosunek, MIERZALNOSC_MIN))

    # Polowa PIERWSZA (6.D135): z maszyna nienazwana pomiar kontenera dostaje
    # odpowiedz progu i zostaje odrzucony. To jest usterka, ktora nazwala 6.D149.
    odrzucony, komunikat = werdykt(KONTENER_11_09_SCIANA, KONTENER_11_09_CPU)
    assert odrzucony is True, (
        "pomiar kontenera NIE zostalby odrzucony (%.3f s przy progu %.1f s): %s"
        % (KONTENER_11_09_SCIANA, SUITE_RUNTIME_BUDGET_S, komunikat))
    assert "pomiar kodu" in komunikat, komunikat

    # Polowa DRUGA (6.D149): z maszyna NAZWANA ten sam pomiar nie jest z progiem
    # porownywany wcale — i komunikat mowi, dlaczego. Podloga sie w nim nie pojawia,
    # bo nie o nia tu chodzi.
    odrzucony_k, komunikat_k = werdykt(KONTENER_11_09_SCIANA, KONTENER_11_09_CPU,
                                       maszyna=MASZYNA_KONTENER)
    assert odrzucony_k is False, (
        "pomiar z maszyny, ktorej prog nie opisuje, zostal z nim porownany: %s"
        % komunikat_k)
    assert MASZYNA_PROGU in komunikat_k and MASZYNA_KONTENER in komunikat_k, komunikat_k
    assert "podloga" not in komunikat_k, (
        "komunikat o niewlasciwej maszynie powoluje sie na podloge mierzalnosci — "
        "to sa dwa rozne odmowienia i zlanie ich w jedno bylo usterka 6.D149: "
        + komunikat_k)

    # I strona druga: najwyzszy przebieg RUNNERA przechodzi, i to z zapasem.
    najwyzszy = max(POMIARY_RUNNERA, key=lambda w: w[1])
    odrzucony_runner, _k = werdykt(najwyzszy[1], najwyzszy[1] * 1.599)
    assert odrzucony_runner is False, (
        "najwyzszy zmierzony przebieg runnera (%.3f s) nie miesci sie w progu — "
        "wtedy margines %.3f nie istnieje" % (najwyzszy[1], MARGIN))


def test_jeden_prog_dla_obu_maszyn_przestalby_widziec_regres_na_runnerze():
    """ROZSTRZYGNIECIE 6.D149, policzone — nie wyrozumowane.

    Pytanie pola „Wyjscie" brzmialo: jeden prog dla obu maszyn, czy `werdykt`
    przyjmujacy maszyne. Odpowiadaja liczby. Prog wspolny musialby dopuszczac
    najwolniejszy pomiar kontenera z taka sama zapascia jak dzisiejszy, czyli
    wynosic **221,4 s**. Maksimum zmierzone na RUNNERZE to **116,404 s** — prog
    wspolny stalby wiec niemal dwa razy nad nim, a bramka przestalaby zauwazac na
    runnerze regres blisko dziewiecdziesieciu procent, czyli na maszynie, dla ktorej
    w ogole istnieje. Krotnosc liczy asercja nizej, zeby nie stala w prozie.

    **Liczba 221,4 jest nowa i to jest jedyna zmiana tego testu przy 6.D160.** Do
    13.09.2026 stalo tu 219,9 s i 1,890x, policzone z maksimum kontenera 170,685 s
    z JEDNEGO przebiegu. Szesc powtorzen tamtego dnia dalo maksimum 171,842 s, czyli
    o 1,157 s wyzej — rozstrzygniecie 6.D149 zostaje nietkniete, bo krotnosc ruszyla
    sie z 1,890 na 1,902. To jest zarazem pomiar tego, ile taki zapis WART jest bez
    powtorzen: jeden przebieg podal maksimum kontenera z bledem 0,7 %.

    Dlatego prog zostaje JEDEN i zostaje przy runnerze, a maszyna wchodzi do
    `werdykt` nie po to, zeby trzymac drugi prog, tylko po to, zeby ODMOWIC
    porownania pomiarowi, ktorego ten prog nie opisuje.
    """
    maks_runnera = max(w[1] for w in POMIARY_RUNNERA)
    maks_kontenera = max(w[1] for w in POMIARY if w[3] == MASZYNA_KONTENER)
    assert maks_kontenera > maks_runnera, (
        "kontener przestal byc wolniejszy od runnera (%.3f wobec %.3f) — wtedy caly "
        "rachunek tej pozycji trzeba powtorzyc" % (maks_kontenera, maks_runnera))

    prog_wspolny = maks_kontenera * MARGIN
    krotnosc = prog_wspolny / maks_runnera
    assert 1.85 < krotnosc < 1.95, (
        "prog wspolny wypadlby %.1f s, czyli %.3fx maksimum runnera — pomiar "
        "z 13.09.2026 dal 221,4 s i 1,902x; jesli liczby sie ruszyly, "
        "rozstrzygniecie 6.D149 trzeba przeliczyc" % (prog_wspolny, krotnosc))

    # I ze prog DZISIEJSZY jest wobec runnera ciasniejszy, czyli ze rozstrzygniecie
    # cos kosztuje kontener, a nie jest darmowe dla obu stron.
    assert SUITE_RUNTIME_BUDGET_S / maks_runnera < krotnosc, (
        "dzisiejszy prog nie jest ciasniejszy od wspolnego — wtedy wybor miedzy nimi "
        "nie ma tresci")


# --- 6.D163: zdanie o RANDZE wpisu w liscie, a nie o przebiegu ----------------------

#: Słowo rangi w opisie pomiaru. Wzorzec celowo WĄSKI: szuka superlatywu, a nie
#: „większy/mniejszy" — porównanie dwóch przebiegów jest zdaniem o nich, superlatyw
#: jest zdaniem o CAŁYM zbiorze i tylko on starzeje się wraz z listą.
RANGA_W_OPISIE = re.compile(
    r"NAJWY\w*SZY|NAJNI\w*SZY|najwy\w*szy|najni\w*szy"
    r"|NAJWOLNIEJSZ\w*|najwolniejsz\w*|NAJSZYBSZ\w*|najszybsz\w*",
    re.UNICODE)

#: Opisy, którym słowo rangi WOLNO nieść, każdy z powodem — 6.D163.
#:
#: **Rozróżnienie, na którym stoi ta pozycja: ranga OGRANICZONA a ranga OTWARTA.**
#: Ranga ograniczona mówi o zbiorze ZAMKNIĘTYM (cztery przebiegi tamtej sesji) albo
#: jest odcięta datą („do 11.09") — takie zdanie jest o przeszłości i prawdziwe
#: zostanie na zawsze. Ranga otwarta mówi „najwyższy z tej listy" i **przestaje być
#: prawdziwa przy pierwszym wpisie, który ją bije**, nie zmieniając ani znaku.
#:
#: Dwie otwarte zdjęto 13.09.2026, i obie warto wymienić, bo pokazują dwa różne
#: sposoby, w jakie takie zdanie szkodzi:
#:   - „, NAJWYŻSZY na runnerze" powtarzało to, co `MEASURED_MAX_WALL_S` liczy
#:     z listy — druga kopia liczby, rodzina 6.B28;
#:   - „, NAJNIŻSZY" przy wpisie 167,402 s było **już nieprawdziwe** w dniu, w którym
#:     to sprawdzono: najniższy pomiar kontenera w liście to 76,518 s. Dopisano je
#:     dzień wcześniej, przy 6.D160, w tej samej sesji, która potem je znalazła.
OPISY_Z_RANGA_DOZWOLONA = {
    "2026-09-05": "ranga w zbiorze ZAMKNIĘTYM — „najwyższy z czterech przebiegów "
                  "tamtej sesji” mówi o pochodzeniu pomiaru, nie o tej liście, "
                  "a tamta sesja się skończyła i liczby już nie zmieni",
    "2026-09-07": "ranga ODCIĘTA DATĄ — „najwyższy zmierzony w kontenerze do 11.09” "
                  "jest zdaniem o przeszłości i nowy pomiar go nie obali",
}


def opisy_z_ranga():
    """`[(data, sekundy, słowo)]` — wpisy `POMIARY`, których opis niesie superlatyw."""
    out = []
    for data, sekundy, _mod, _maszyna, gdzie in POMIARY:
        trafienie = RANGA_W_OPISIE.search(gdzie)
        if trafienie:
            out.append((data, sekundy, trafienie.group(0)))
    return out


def test_zaden_wpis_nie_niesie_rangi_OTWARTEJ_w_tej_liscie():
    """ROZSTRZYGNIĘCIE 6.D163: ranga otwarta znika, ranga ograniczona zostaje z powodem.

    **Ile ich było.** Cztery opisy z osiemnastu niosły superlatyw. Dwa są rangą
    ograniczoną (zbiór zamknięty, data odcinająca) i zostają. Dwa były rangą otwartą
    i zostały zdjęte — a `WPISOW_Z_DOPISKIEM` w `test_timing_record.py` zeszło przez
    to z jednego na zero, dokładnie tak, jak tamten komentarz to przewidywał.

    **Innych list pomiarów w drzewie NIE MA — i od 6.D193 jest to SPRAWDZANE, a nie
    przeczytane. Ten akapit jest przepisany, a nie dopisany obok.** Do 13.09.2026 stało
    tu, że „skan po `tools/tests/`" znalazł jedną listę — ale tamten skan **wykonano
    ręcznie raz i nie został w drzewie**; pod całym zdaniem nie było ani jednej linii
    kodu. Dziś liczy je `test_ile_ksztaltow_zapisu_pomiaru_niesie_drzewo` niżej, na całym
    `tools/`, a klasyfikator ma kontrolę przyrządu na wszystkich pięciu kształtach.

    **Odpowiedź „zero" się utrzymała, ale nie była sprawdzona, tylko trafiona:** stary
    wzorzec („krotka zaczynająca się od daty") nie mógł zobaczyć kształtu ze słownikiem,
    a jeden taki słownik — `OPISY_Z_RANGA_DOZWOLONA` — stoi **w tym samym pliku, kilkaset
    wierszy niżej**, i czyta go ta sama asercja, która to zdanie wypowiada.

    **Dlaczego wzorzec bierze superlatyw, a nie każde porównanie.** „Wolniejszy niż
    tamten" jest zdaniem o dwóch przebiegach i zostaje prawdziwe na zawsze.
    „Najwolniejszy" jest zdaniem o całym zbiorze i starzeje się razem z nim. Tylko
    ta druga rodzina jest tym, o co pozycja pytała.
    """
    znalezione = opisy_z_ranga()
    daty = [data for data, _sek, _slowo in znalezione]
    nierozstrzygniete = sorted(set(daty) - set(OPISY_Z_RANGA_DOZWOLONA))
    assert not nierozstrzygniete, (
        "opis ze słowem rangi, którego nikt nie rozstrzygnął: %s — ranga OTWARTA "
        "(„najwyższy z tej listy”) starzeje się przy pierwszym wpisie, który ją bije, "
        "nie zmieniając ani znaku. Albo ogranicz ją datą lub zamkniętym zbiorem, "
        "albo zdejmij" % nierozstrzygniete)

    # I DRUGA STRONA, bez ktorej wzorzec mogl by przestac cokolwiek znajdowac, a test
    # zostalby zielony: lista dozwolonych opisuje wpisy, ktore NAPRAWDE range niosa.
    zniknely = sorted(set(OPISY_Z_RANGA_DOZWOLONA) - set(daty))
    assert not zniknely, (
        "lista dozwolonych rang wymienia wpis %s, w którym wzorzec rangi już nic nie "
        "znajduje — albo opis przepisano, albo wzorzec przestał widzieć superlatywy "
        "i nowy dopisek wszedłby po cichu" % zniknely)

    for data, powod in OPISY_Z_RANGA_DOZWOLONA.items():
        assert len(powod) > 60, (data, powod)

    # Kontrola przyrzadu na WEJSCIU SYNTETYCZNYM: wzorzec ma widziec range otwarta
    # i NIE brac zwyklego porownania. Bez tego test bylby zielony takze wtedy, gdyby
    # wzorzec przestal cokolwiek znajdowac — a wtedy nowy dopisek wszedlby po cichu.
    assert RANGA_W_OPISIE.search("2335 testów, NAJWYŻSZY na runnerze"), (
        "wzorzec nie widzi rangi otwartej, czyli dokładnie tego, co ta pozycja zdjęła")
    assert RANGA_W_OPISIE.search("powtórzenie 5 z 6, NAJNIŻSZY"), (
        "wzorzec nie widzi drugiej ze zdjętych rang")
    for spokojny in ("host spokojny", "host pod obciążeniem, wolniejszy niż godzinę "
                     "wcześniej", "kontener sesji, powtórzenie 5 z 6, CPU/ściana 0,987"):
        assert not RANGA_W_OPISIE.search(spokojny), (
            "wzorzec bierze za rangę opis, który nią nie jest: %r" % spokojny)


# --- 6.D162: ile maszyn stoi pod jednym slowem `runner` -----------------------------

#: Logi jobow `tools` przechowywane w drzewie. Czytane `timing_record.z_logu`, czyli
#: TYM SAMYM czytnikiem, ktory sklada wpisy `POMIARY` — wlasny parser dawalby liczbe
#: o moim regexie, a nie o mechanizmie, ktory te wpisy naprawde produkuje.
KATALOG_LOGOW = os.path.join(ROOT, "tests", "data", "ci-logs")

#: Ile RÓŻNYCH maszyn niosą dzisiejsze logi. Wyprowadzone, nie wpisane — asercja niżej
#: liczy je z katalogu. Stała jest zapadką: trzecia maszyna w logach ma zmusić do
#: przeliczenia rozstrzygnięcia, a nie przejść niezauważona.
MASZYN_W_LOGACH = 2


def przebiegi_z_logow():
    """`[(plik, nazwa_maszyny, slowo_maszyny, sekundy, testow)]` — z logów w drzewie.

    Czyta `timing_record.z_logu`. Pole `runner` niesie nazwę maszyny z wiersza
    `Runner name:`, a pole `maszyna` — słowo, do którego ta nazwa jest sprowadzana
    przy składaniu wpisu `POMIARY`. Oba naraz, bo cała ta pozycja jest o różnicy
    między nimi.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))
    import timing_record

    out = []
    for nazwa in sorted(os.listdir(KATALOG_LOGOW)):
        if not nazwa.endswith(".log"):
            continue
        sciezka = os.path.join(KATALOG_LOGOW, nazwa)
        with open(sciezka, encoding="utf-8", errors="replace") as uchwyt:
            pola, _brak = timing_record.z_logu(uchwyt.read())
        if "runner" not in pola:
            continue
        out.append((nazwa, pola["runner"], pola["maszyna"],
                    pola["sekundy"], pola["testow"]))
    return out


def _rozrzut(wartosci):
    """Iloraz największej do najmniejszej. Jedna definicja na cały ten rachunek."""
    return max(wartosci) / min(wartosci)


def miedzy_i_wewnatrz(przebiegi, na_test=False):
    """`(roznica_miedzy_maszynami, najwiekszy_rozrzut_wewnatrz)` dla listy przebiegów.

    Osobna funkcja, a nie pętla w teście, **żeby dało się ją zawołać na wejściu, którego
    drzewo nie produkuje** — patrz `test_rachunek_o_maszynach_UMIE_zapalic_sie_gdy`.
    Bez tego asercja o „mniej niż" byłaby zdaniem, o którym wiadomo tylko tyle, że dziś
    jest prawdziwe; ta sama lekcja, co osiemnaście zdań policzonych w 6.D161.
    """
    wg_maszyn = {}
    for _plik, nazwa, _slowo, sekundy, testow in przebiegi:
        wg_maszyn.setdefault(nazwa, []).append(sekundy / testow if na_test else sekundy)
    srednie = [sum(v) / len(v) for v in wg_maszyn.values()]
    wielokrotne = [v for v in wg_maszyn.values() if len(v) > 1]
    if len(srednie) < 2 or not wielokrotne:
        raise ValueError("rachunek potrzebuje dwóch maszyn i powtórzeń na którejś")
    return _rozrzut(srednie), max(_rozrzut(v) for v in wielokrotne)


def test_rachunek_o_maszynach_UMIE_zapalic_sie_gdy_nazwa_NAPRAWDE_rozdziela():
    """Kontrola przyrządu na WEJŚCIU SYNTETYCZNYM — bo drzewo takiego nie ma.

    **Dlaczego syntetyczne, a nie z logów.** Kontrola negatywna przestawiająca log
    PR #528 na drugą maszynę wyszła **ZIELONA**, i to nie dlatego, że podstawienie
    nie weszło: przeniesienie najwolniejszego przebiegu przez granicę zostawia
    różnicę między maszynami na 0,3 % przy rozrzucie wewnątrz 30 %, czyli
    **wzmacnia** tezę zamiast ją łamać. Żadne przetasowanie sześciu dzisiejszych
    logów tej asercji nie zapali — więc rozstrzyga wejście zbudowane na tę okazję.

    Dwie maszyny, każda powtarzalna co do procenta, ale różniące się dwukrotnie:
    tak wygląda świat, w którym nazwa maszyny COŚ rozdziela i pole na nią ma sens.
    """
    rozdziela = [
        ("a1.log", "szybka", MASZYNA_RUNNER, 100.0, 1000),
        ("a2.log", "szybka", MASZYNA_RUNNER, 101.0, 1000),
        ("b1.log", "wolna", MASZYNA_RUNNER, 200.0, 1000),
        ("b2.log", "wolna", MASZYNA_RUNNER, 202.0, 1000),
    ]
    miedzy, wewnatrz = miedzy_i_wewnatrz(rozdziela)
    assert miedzy > wewnatrz, (
        "przyrząd nie widzi różnicy nawet tam, gdzie maszyny różnią się dwukrotnie "
        "(%.4f wobec %.4f) — wtedy zielony wynik na drzewie nic nie znaczy"
        % (miedzy, wewnatrz))

    # I druga strona: na dzisiejszych logach ten sam rachunek mowi ODWROTNIE.
    miedzy_dzis, wewnatrz_dzis = miedzy_i_wewnatrz(przebiegi_z_logow())
    assert miedzy_dzis < wewnatrz_dzis, (miedzy_dzis, wewnatrz_dzis)


def test_slowo_runner_stoi_nad_DWIEMA_maszynami_ale_ich_NIE_rozdziela():
    """ROZSTRZYGNIĘCIE 6.D162: nazwa maszyny NIE wchodzi do wpisu, bo nic nie dzieli.

    **Ile maszyn.** Logi w drzewie niosą **dwie** różne nazwy, po trzy przebiegi
    każda, a `z_logu` sprowadza obie do jednego słowa `runner`. Liczba jest liczona
    z katalogu, nie wpisana.

    **Czy je rozdziela — i to jest cała odpowiedź.** Różnica MIĘDZY maszynami
    (średnie 96,0 wobec 106,0 s) wynosi **10,4 %**, a rozrzut WEWNĄTRZ jednej maszyny
    sięga **26,4 %**. Różnica, którą miałaby opisać nazwa, jest więc **mniejsza od
    szumu na tej samej maszynie** — pole niosące nazwę rozdzielałoby przebiegi wzdłuż
    granicy, która nie istnieje.

    **Zarzut o dryf drzewa odparty rachunkiem, nie słowem.** Pole „Dlaczego" pozycji
    mówiło, że materiał jest zmieszany, bo w tym samym oknie zestaw rósł 2315 → 2335
    testów, a maszyna `…-03` dostała akurat większe drzewa. Po znormalizowaniu czasu
    NA TEST wniosek się nie zmienia: między maszynami **10,1 %**, wewnątrz **25,6 %**.
    Dryf drzewa tej różnicy nie tłumaczy, bo drzewo urosło w tym oknie o 0,65 %,
    a czasy rozjechały się o kilkanaście do dwudziestu kilku procent.

    **Czym więc jest rozrzut, skoro nie maszyną.** OKAZJĄ. Ta sama maszyna `…-03`
    dała 26,4 % rozrzutu 11.09.2026 i **2,2 %** 13.09.2026 przy drzewie stałym co do
    0,17 % (6.D160 i dwa przebiegi po niej). Nazwa maszyny jest w obu przypadkach ta
    sama, a rozrzut różni się dwunastokrotnie.

    **`CLAUDE.md` §9, rozstrzygnięte wprost, bo pozycja tego żądała.** Dokument
    zakazuje WYBIERANIA runnera po nazwie i podawania liczebności puli. Zapisanie
    nazwy w POMIARZE nie byłoby ani jednym, ani drugim — selektor `runs-on` zostaje
    gołą etykietą, a liczba maszyn w logach nie jest liczbą maszyn w puli. Zakaz
    więc tego nie blokuje. Blokuje to pomiar wyżej: pole, które nic nie rozdziela,
    jest polem, które wygląda, że coś mówi.
    """
    przebiegi = przebiegi_z_logow()
    assert len(przebiegi) >= 4, (
        "logów w drzewie jest %d — przy mniej niż czterech rozrzut wewnątrz maszyny "
        "nie ma z czego powstać i ten rachunek nic nie znaczy" % len(przebiegi))

    nazwy = {nazwa for _p, nazwa, _s, _sek, _t in przebiegi}
    assert len(nazwy) == MASZYN_W_LOGACH, (
        "logi niosą %d różnych maszyn (%s), a zapadka stoi na %d — trzecia maszyna "
        "wymaga przeliczenia rozstrzygnięcia, nie samego podniesienia liczby"
        % (len(nazwy), sorted(nazwy), MASZYN_W_LOGACH))

    slowa = {slowo for _p, _n, slowo, _sek, _t in przebiegi}
    assert slowa == {MASZYNA_RUNNER}, (
        "czytnik logów przestał sprowadzać nazwy do jednego słowa: %s — wtedy ta "
        "pozycja opisuje nieistniejący już mechanizm" % sorted(slowa))

    # SEDNO: miedzy maszynami MNIEJ niz wewnatrz jednej. Liczone dwa razy — na czasie
    # surowym i na czasie NA TEST, zeby zarzut o dryf drzewa nie zostal bez rachunku.
    for etykieta, na_test in (("surowy", False), ("na test", True)):
        miedzy, wewnatrz = miedzy_i_wewnatrz(przebiegi, na_test=na_test)
        assert miedzy < wewnatrz, (
            "czas %s: różnica MIĘDZY maszynami (%.4f) przestała być mniejsza od "
            "rozrzutu WEWNĄTRZ maszyny (%.4f) — wtedy nazwa maszyny zaczyna coś "
            "rozdzielać i rozstrzygnięcie 6.D162 trzeba przeliczyć od nowa"
            % (etykieta, miedzy, wewnatrz))

    # I ze nazwa maszyny NIE weszla do zadnego wpisu `POMIARY` — rozstrzygniecie
    # zapisane jako stan drzewa, a nie tylko jako zdanie w tym docstringu.
    for _data, _sek, _mod, maszyna, gdzie in POMIARY:
        assert maszyna in MASZYNY, maszyna
        for nazwa in nazwy:
            assert nazwa not in gdzie, (
                "wpis POMIARY niesie nazwę maszyny %r — 6.D162 rozstrzygnęło, że "
                "nazwa nic nie rozdziela, więc do wpisu nie wchodzi: %s"
                % (nazwa, gdzie))


def test_maszyna_progu_jest_ta_ktora_daje_MEASURED_MAX_WALL_S():
    """Wiazanie, bez ktorego `MASZYNA_PROGU` bylaby napisem obok liczby — 6.D149.

    `MEASURED_MAX_WALL_S` bierze `POMIARY_RUNNERA`; gdyby ktos przestawil jedno bez
    drugiego, `werdykt` odmawialby porownania maszynie, na ktorej prog powstal,
    i przyjmowal te, na ktorej nie.
    """
    assert MASZYNA_PROGU in MASZYNY, MASZYNA_PROGU
    assert all(w[3] == MASZYNA_PROGU for w in POMIARY_RUNNERA), (
        "`POMIARY_RUNNERA` niesie wpis z innej maszyny niz `MASZYNA_PROGU`")
    assert MEASURED_MAX_WALL_S == max(w[1] for w in POMIARY if w[3] == MASZYNA_PROGU), (
        "maksimum, z ktorego wychodzi prog, nie jest maksimum maszyny progu")

    # Kontrola przyrzadu: dla KAZDEJ maszyny spoza progu `werdykt` odmawia, a dla
    # maszyny progu porownuje. Bez drugiej polowy „odmawia" byloby prawda takze dla
    # funkcji odmawiajacej zawsze.
    for maszyna in MASZYNY:
        odrzucony, komunikat = werdykt(SUITE_RUNTIME_BUDGET_S + 10.0,
                                       SUITE_RUNTIME_BUDGET_S + 10.0,
                                       maszyna=maszyna)
        if maszyna == MASZYNA_PROGU:
            assert odrzucony is True, (maszyna, komunikat)
        else:
            assert odrzucony is False, (maszyna, komunikat)

    # KOLEJNOSC obu warunkow, na wejsciu syntetycznym — bo na pomiarach z `POMIARY`
    # nie widac jej wcale. Kontener z 11.09 ma stosunek 0,991, czyli galezi podlogi
    # nie dotyka, wiec przestawienie warunkow nie zmienia tam ANI JEDNEGO znaku.
    # Rozstrzyga dopiero przebieg jednoczesnie z NIEWLASCIWEJ maszyny i POD
    # OBCIAZENIEM: ma uslyszec, ze prog go nie dotyczy, a nie ze jego pomiar nic nie
    # mowi o kodzie — bo o kodzie moze nie mowic, ale to jest wtedy drugi powod,
    # nie pierwszy.
    _o, komunikat = werdykt(200.0, 80.0, maszyna=MASZYNA_KONTENER)      # stosunek 0,4
    assert MASZYNA_KONTENER in komunikat and "skalibrowany" in komunikat, (
        "przebieg z niewlasciwej maszyny I pod obciazeniem dostal odpowiedz podlogi, "
        "a ma dostac odpowiedz maszyny — kolejnosc warunkow w `werdykt` sie "
        "odwrocila: " + komunikat)
    assert "nie mowi nic o kodzie" not in komunikat, komunikat

    # I druga strona tej samej granicy: na WLASCIWEJ maszynie pod obciazeniem
    # odpowiada podloga, tak jak od 6.D42.
    _o2, komunikat2 = werdykt(200.0, 80.0, maszyna=MASZYNA_PROGU)
    assert "nie mowi nic o kodzie" in komunikat2, komunikat2


def test_pomiar_kontenera_stoi_w_liscie_z_ta_sama_liczba():
    """Dwie kopie jednej liczby rozjezdzaja sie po cichu (6.B28) — wiec ich nie ma.

    Stala `KONTENER_11_09_SCIANA` i wpis w `POMIARY` musza podawac to samo; test
    pilnuje, zeby edycja jednego miejsca nie zostawila drugiego z wczorajsza prawda.
    """
    kontenerowe_dzis = [w for w in POMIARY
                        if w[0] == "2026-09-11" and w[3] == MASZYNA_KONTENER]
    assert len(kontenerowe_dzis) == 1, kontenerowe_dzis
    assert kontenerowe_dzis[0][1] == KONTENER_11_09_SCIANA, (
        "wpis w POMIARY mowi %.3f s, a stala %.3f s"
        % (kontenerowe_dzis[0][1], KONTENER_11_09_SCIANA))


#: Przebiegi runnera z 11.09.2026 — FAKT HISTORYCZNY, ktory sie nie zmieni.
#:
#: **Rozdzielone od liczby wszystkich wpisow runnera przy 6.D190, i to jest cala
#: tresc tamtej pozycji.** Do niej jedna asercja robila dwie rzeczy naraz: pilnowala,
#: ze kazdy wpis runnera niesie stosunek CPU/sciana (kontrola ZYWA, lapie wpis
#: dopisany bez stosunku), i zapisywala, ILE przebiegow dal jeden konkretny dzien
#: (fakt HISTORYCZNY). Dopoki byly jednym zdaniem, kazdy nowy pomiar runnera
#: kosztowal edycje twierdzenia o przeszlosci — a to samo zdanie stoi w prozie
#: `reports/6d149-prog-a-maszyna.md` („w szesciu przebiegach"), gdzie jest historia
#: i przepisywaniu nie podlega. Ta sama rodzina, ktora 6.D108 rozstrzygnelo dla
#: raportow: zdanie o wartosci biezacej to nie zdanie o wartosci z dnia pomiaru.
POMIARY_RUNNERA_11_09 = tuple(
    w for w in POMIARY_RUNNERA if w[0] == "2026-09-11")

#: Ile ich bylo tamtego dnia. Rownosc, bo dzien sie skonczyl.
PRZEBIEGOW_RUNNERA_11_09 = 6

#: Podloga na liczbe WSZYSTKICH wpisow runnera. Prog, nie rownosc: wpisow przybywa
#: z kazdym przebiegiem CI, ktory ktos zapisze, a zero znaczy zepsuty czytnik listy —
#: i to jest jedyna rzecz, przed ktora ta liczba ma bronic (6.D27).
MIN_WPISOW_RUNNERA = 6


def test_liczba_przebiegow_runnera_z_11_09_jest_FAKTEM_HISTORYCZNYM():
    """Szostka opisuje JEDEN DZIEN, a nie stan listy — 6.D190.

    Wydzielone z `test_runner_liczy_rownolegle_a_kontener_szeregowo`, gdzie stalo
    razem z kontrola zywa. Po rozdzieleniu siodmy wpis runnera nie czyni nieprawdziwym
    ani tej asercji, ani zdania „w szesciu przebiegach" z `reports/6d149-prog-a-maszyna.md`:
    oba mowia o 11.09.2026 i tyle samo mowia dzisiaj, co wczoraj.

    Ze zdanie raportu naprawde odnosi sie do TEGO dnia, jest tu sprawdzone, a nie
    zalozone — inaczej „nic sie nie stalo nieprawdziwe" byloby twierdzeniem bez
    pokrycia.
    """
    assert len(POMIARY_RUNNERA_11_09) == PRZEBIEGOW_RUNNERA_11_09, (
        "przebiegow runnera z 11.09.2026 jest %d, a bylo ich szesc — dzien sie "
        "skonczyl, wiec ta liczba zmienic sie nie moze: %s"
        % (len(POMIARY_RUNNERA_11_09), [w[1] for w in POMIARY_RUNNERA_11_09]))

    sciezka = os.path.join(ROOT, "reports", "6d149-prog-a-maszyna.md")
    with open(sciezka, encoding="utf-8") as uchwyt:
        raport = uchwyt.read()
    assert "sześciu przebiegach" in raport, (
        "`reports/6d149-prog-a-maszyna.md` nie mowi juz o szesciu przebiegach — "
        "wtedy rozdzielenie z 6.D190 chroni zdanie, ktorego nie ma")

    # ZDANIE RAPORTU NIE NIESIE DATY, i to jest zmierzone przy 6.D190. Kotwica jest
    # inna: obok stoi liczba modulow (122), a wpisow runnera o 122 modulach jest
    # dokladnie tych szesc z 11.09 — zadnego innego dnia. Nie ma wiec potrzeby
    # przepisywac raportu (pole „Poza zakresem"), zeby wiedziec, o czym mowi.
    assert "122" in raport, (
        "raport 6.D149 nie podaje juz liczby modulow — wtedy jego „sześciu "
        "przebiegach” nie ma zadnej kotwicy i moze byc czytane jako stan listy")
    o_122 = tuple(w for w in POMIARY_RUNNERA if w[2] == 122)
    assert o_122 == POMIARY_RUNNERA_11_09, (
        "wpisy runnera o 122 modulach przestaly pokrywac sie z przebiegami "
        "z 11.09.2026 — kotwica zdania raportu przestaje wtedy wskazywac ten dzien: "
        "%s wobec %s" % ([w[:2] for w in o_122], [w[:2] for w in POMIARY_RUNNERA_11_09]))


def test_runner_liczy_rownolegle_a_kontener_szeregowo():
    """Liczba, ktora rozstrzyga, ze to NIE SA porownywalne przebiegi.

    Stosunek CPU do sciany mowi, ile rdzeni zestaw dostaje na sekunde zegara. Na
    runnerze jest **powyzej jedynki** (1,599-1,971 w szesciu przebiegach z 11.09.2026),
    w kontenerze **ponizej** (0,991). To nie jest rozrzut tej samej maszyny — to dwa
    rozne sposoby wykonania tej samej pracy, i jeden prog czasu SCIANY nie opisuje obu.

    **Liczba wpisow przypieta jest tu PODLOGA, nie rownoscia — 6.D190.** Rownosc
    robila z kazdego nowego pomiaru runnera edycje twierdzenia o przeszlosci; fakt
    historyczny stoi odtad osobno, w
    `test_liczba_przebiegow_runnera_z_11_09_jest_FAKTEM_HISTORYCZNYM`. Kontrola ZYWA
    — ze kazdy wpis niesie stosunek — zostaje tutaj i dziala na WSZYSTKICH wpisach,
    takze na dopisanych po tej pozycji.
    """
    kontener = KONTENER_11_09_CPU / KONTENER_11_09_SCIANA
    assert kontener < 1.0, (
        "kontener przestal liczyc szeregowo (CPU/sciana %.3f) — wtedy roznica "
        "miedzy maszynami znika i podzial listy trzeba przemyslec" % kontener)
    # Stosunki runnera stoja w polu opisowym wpisow — czytane stamtad, a nie wpisane
    # tu drugi raz. Format: „CPU/ściana 1,971".
    stosunki = []
    for _d, _s, _m, maszyna, gdzie in POMIARY:
        if maszyna != MASZYNA_RUNNER:
            continue
        trafienie = re.search(r"CPU/ściana (\d+),(\d+)", gdzie)
        assert trafienie, ("wpis runnera nie podaje stosunku CPU/ściana: " + gdzie)
        stosunki.append(float("%s.%s" % trafienie.groups()))
    assert len(stosunki) >= MIN_WPISOW_RUNNERA, (
        "wpisow runnera jest %d przy podlodze %d — lista przestala byc czytana, "
        "a pusta lista przechodzi kazde `min()` nizej bez jednego sprawdzenia: %s"
        % (len(stosunki), MIN_WPISOW_RUNNERA, stosunki))
    assert min(stosunki) > 1.0, (
        "ktorys przebieg runnera ma stosunek ponizej jedynki: %s — wtedy zdanie "
        "o rownoleglosci przestaje byc prawdziwe" % stosunki)
    assert min(stosunki) > kontener * 1.5, (
        "runner przestal byc wyraznie szybszy od kontenera: %s wobec %.3f"
        % (stosunki, kontener))


#: Sześć powtórzeń kontenera z 13.09.2026 na JEDNYM drzewie (124 moduły, 2414 testów)
#: — 6.D160. WYPROWADZONE z `POMIARY`, nie wpisane obok drugi raz: lista jest jedynym
#: zapisem pomiaru, a druga kopia tych liczb rozjechałaby się z nią po cichu (6.B28).
POMIARY_KONTENERA_JEDNO_DRZEWO = tuple(
    w for w in POMIARY if w[0] == "2026-09-13" and w[3] == MASZYNA_KONTENER)

#: Ile powtórzeń niesie rozstrzygnięcie 6.D160. Pozycja pytała wprost, ILE ich trzeba
#: i CZY tyle ich jest — więc liczba stoi w kodzie i jest pilnowana, a nie tylko
#: opowiedziana w raporcie.
POWTORZEN_KONTENERA = 6


def test_powtorzenia_kontenera_NIE_ruszaja_maksimum_a_dryf_drzewa_rusza():
    """ROZSTRZYGNIĘCIE 6.D160, policzone — i obalona teza, z którą pozycja wchodziła.

    Pozycja mówiła: „próg z n=1 byłby liczbą wpisaną z ręki". **Zmierzone:
    nieprawda.** Sześć powtórzeń na jednym drzewie różni się o 2,65 %, a rekord padł
    na przebiegu PIERWSZYM i nie ruszył się już ani razu. `max(n=1)` i `max(n=6)` to
    ta sama liczba, więc liczba powtórzeń nie jest tym, co czyni taki próg wpisanym
    z ręki.

    Czym jest — widać na tej samej liście: kontener spokojny mierzył 76,518 s przy
    93 modułach i 170,5 s przy 124, czyli **dryf drzewa jest od rozrzutu powtórzeń
    czterdziestokrotnie większy**. Tego żadna liczba powtórzeń nie naprawia, bo one
    mierzą co innego. Dokładnie na tym poległo `MEASURED_MAX_WALL_S = 77.04` przed
    6.D26: nie na tym, że przebieg był jeden, tylko na tym, że drzewo urosło.

    Test pilnuje obu połówek, bo obie są zdaniami o liczbach, które mogą się ruszyć.
    """
    assert len(POMIARY_KONTENERA_JEDNO_DRZEWO) == POWTORZEN_KONTENERA, (
        "rozstrzygniecie 6.D160 stoi na %d powtorzeniach, a lista niesie %d — "
        "zdanie o rozrzucie stracilo podstawe"
        % (POWTORZEN_KONTENERA, len(POMIARY_KONTENERA_JEDNO_DRZEWO)))

    sciany = [w[1] for w in POMIARY_KONTENERA_JEDNO_DRZEWO]
    rozrzut = max(sciany) / min(sciany)
    assert rozrzut < MARGIN, (
        "rozrzut szesciu powtorzen (%.4f) przestal miescic sie w zapasie progu "
        "(%.4f) — wtedy maksimum JEST loteria i rozstrzygniecie 6.D160 trzeba "
        "przeliczyc" % (rozrzut, MARGIN))

    # SEDNO: przy KAZDEJ liczbie powtorzen prog zbudowany tak, jak prog runnera
    # (maksimum razy zapas), przykrywa maksimum ze wszystkich szesciu. Czyli
    # dolozenie przebiegow nie zmienia liczby, ktora by z tego wyszla.
    for n in range(1, len(sciany) + 1):
        prog_z_n = max(sciany[:n]) * MARGIN
        assert prog_z_n >= max(sciany), (
            "prog zbudowany z %d pierwszych powtorzen (%.3f s) nie przykrywa "
            "maksimum z szesciu (%.3f s) — wtedy n=1 naprawde bylo za malo"
            % (n, prog_z_n, max(sciany)))

    # I ze te szesc to POMIARY KODU, a nie zajetej maszyny — inaczej rozrzut mowilby
    # o hoscie i caly rachunek wyzej byloby o czym innym. Stosunki czytane z pola
    # opisowego, tak samo jak dla runnera, a nie wpisane tu drugi raz.
    stosunki = []
    for _d, _s, _m, _maszyna, gdzie in POMIARY_KONTENERA_JEDNO_DRZEWO:
        trafienie = re.search(r"CPU/ściana (\d+),(\d+)", gdzie)
        assert trafienie, ("powtorzenie nie podaje stosunku CPU/ściana: " + gdzie)
        stosunki.append(float("%s.%s" % trafienie.groups()))
    assert min(stosunki) > MIERZALNOSC_MIN, (
        "powtorzenie z stosunkiem %.3f lezy pod podloga %.2f — ten przebieg mowi "
        "o maszynie, nie o kodzie, wiec do rozrzutu kodu nie nalezy"
        % (min(stosunki), MIERZALNOSC_MIN))


def test_prog_dla_kontenera_nie_zapalilby_sie_na_zadnym_zmierzonym_przebiegu():
    """DRUGA połowa rozstrzygnięcia 6.D160: dałoby się go wyprowadzić, i byłby bezczynny.

    Próg zbudowany tak jak runnerowy — maksimum kontenera razy ten sam zapas — wypada
    221,4 s. Przebiegów kontenera lista niesie osiem i **ani jeden** go nie przekracza.
    Jedyny przebieg kontenera nad tą liczbą w historii projektu to incydent
    z 08.09.2026 (335,668 s), a ten ma stosunek CPU/ściana 0,211, czyli odpowiada mu
    podłoga mierzalności, ZANIM próg zostanie w ogóle zapytany.

    Do tego woła `werdykt` w całym drzewie jedno miejsce — krok „Run tool tests"
    w `python-tests.yml`, a ten workflow ma `runs-on: self-hosted`. Argument `maszyna`
    istnieje dla pomiarów spoza CI (6.D149) i żadna automatyka go nie podaje.

    Dlatego kontener progu NIE dostaje: nie dlatego, że nie dałoby się go zmierzyć —
    dałoby się — tylko dlatego, że nie zmieniłby ani jednego werdyktu, a starzałby się
    dryfem drzewa jak ten, który 6.D26 z tego pliku usuwało.
    """
    # PROG LICZONY Z SZESCIU POWTORZEN, a sprawdzany na WSZYSTKICH wpisach kontenera
    # — i ten podzial jest tu trescia, nie stylem. Wersja liczaca prog z tej samej
    # listy, na ktorej potem szuka przekroczen, nie moze zapalic sie NIGDY: `max(L) *
    # MARGIN` przy `MARGIN > 1` nie jest przekraczalne przez zaden element `L`.
    # Byla tak napisana i zostala poprawiona, zanim wyszla z tej pozycji.
    prog_hipotetyczny = max(w[1] for w in POMIARY_KONTENERA_JEDNO_DRZEWO) * MARGIN
    kontenerowe = [w[1] for w in POMIARY if w[3] == MASZYNA_KONTENER]
    nad_progiem = [s for s in kontenerowe if s > prog_hipotetyczny]
    assert nad_progiem == [], (
        "prog hipotetyczny %.3f s zapalilby sie na przebiegach %s — wtedy przestaje "
        "byc bezczynny i rozstrzygniecie 6.D160 trzeba przeliczyc"
        % (prog_hipotetyczny, nad_progiem))

    # Incydent z 08.09.2026: NAD progiem, a mimo to nieporownywany — bo odpowiada mu
    # podloga. Liczone `werdykt`, a nie powtorzone prozą.
    odrzuc, komunikat = werdykt(335.668, 70.8, budget_s=prog_hipotetyczny)
    assert 335.668 > prog_hipotetyczny, (
        "incydent 08.09 przestal byc nad progiem hipotetycznym — wtedy ten test nie "
        "sprawdza juz tego, co opisuje")
    assert odrzuc is False and "nie mowi nic o kodzie" in komunikat, (
        "jedyny przebieg kontenera nad progiem hipotetycznym zostalby przez niego "
        "odrzucony: " + komunikat)


#: Zdanie o marginesie i mnoznik, ktory sie w nim styka ze znacznikiem mnozenia.
#: Dwa wzorce, nie jeden, i oba wyszly z prob na tym pliku — patrz docstring testu.
#: Kropka jest przepuszczana TYLKO wtedy, gdy stoi przed cyfra — inaczej okno urywa
#: sie na kropce dziesietnej i `1.40x` widzi jako `1`. Wyszlo z proby: kontrola
#: narzedzia zglosila „detektor nie widzi zdania, ktore ma widziec" na zdaniu
#: zbudowanym przez `%.2f`, czyli z kropka, a nie z przecinkiem.
_OKOLICA_MARGINESU = re.compile(
    r"(?:margines\w*|mnoznik\w*|mnożnik\w*)(?:[^.\n]|\.(?=\d)){0,80}", re.IGNORECASE)
_MNOZNIK = re.compile(r"(?:x\s*(\d+(?:[.,]\d+)?)\b"
                      r"|\b(\d+(?:[.,]\d+)?)\s*[x×]"
                      r"|\brazy\s+(\d+(?:[.,]\d+)?))")


def mnozniki_w(text):
    """Mnozniki podane w zdaniach o marginesie, jako liczby. Pusta lista = zadnych."""
    znalezione = []
    for fragment in _OKOLICA_MARGINESU.finditer(text):
        for trafienie in _MNOZNIK.finditer(fragment.group(0)):
            surowa = next(g for g in trafienie.groups() if g)
            znalezione.append(float(surowa.replace(",", ".")))
    return znalezione


def test_the_prose_does_not_quote_a_margin_that_the_numbers_do_not_give():
    """Sedno 6.D26. Proza tego pliku nie ma prawa podawac MNOZNIKA, ktorego nie daja
    stale obok — bo wlasnie takie zdanie zestarzalo sie tu bez sladu.

    Liczba liczy sie jako mnoznik dopiero wtedy, gdy **styka sie ze znacznikiem**
    mnozenia (`x2`, `1,4x`, `1,95×`, `razy 2`) i stoi w zdaniu o marginesie. Dwa
    warunki, a nie jeden, i oba wyszly z prob na tym pliku:
    - bez znacznika bramka brala za mnoznik KAZDA liczbe obok slowa „margines" —
      zapalila sie na `77,04`, czyli na POMIARZE w zdaniu o tym, wobec czego margines
      sie liczyl;
    - bez warunku na „margines" brala kazdy mnoznik w pliku, a plik mowi tez o `1,54x`
      rozrzutu hosta na jednym module, ktory z marginesem progu nie ma nic wspolnego.

    **Test sprawdza NARZEDZIE, nie tylko dzisiejszy tekst** — i to tez wyszlo z proby:
    po wycieciu wlasnego docstringa ze skanowania w pliku nie zostalo ANI JEDNEGO
    zdania z mnoznikiem, wiec petla nie miala po czym iterowac i test przeszedl
    **bez ani jednej asercji**. Zlapala to bramka asercji z #139. Wersja nizej ma
    asercje zawsze: sprawdza, ze detektor lapie podstawione zdanie nieaktualne, ze
    przepuszcza zdanie zgodne z `MARGIN`, ze nie bierze pomiaru za mnoznik i ze nie
    wchodzi w mnozniki spoza zdan o marginesie.

    **Czego ta bramka NIE lapie, swiadomie:** zdania „margines wynosi 1,40" bez
    znacznika. Wezsze kryterium przepuszcza taki zapis, szersze zapala sie na kazdej
    liczbie w okolicy — a bramka, ktora swieci na poprawnym tekscie, zostaje wylaczona.
    Zapis mnoznikiem jest w tym repozytorium konwencja, wiec kryterium trafia w to, jak
    te zdania naprawde sie pisze.
    """
    with open(__file__, encoding="utf-8") as uchwyt:
        source = uchwyt.read()
    # Wlasny test jest wyciety ze skanowania, i to nie jest wyjatek dla wygody: jego
    # docstring OPISUJE skladnie, ktora bramka rozpoznaje, wiec musi te mnozniki
    # wymienic jako przyklady. Bramka skanujaca sama siebie zapalalaby sie na wlasnej
    # dokumentacji — i zostalaby wylaczona, nie poprawiona.
    granica = source.index("#: Zdanie o marginesie i mnoznik")
    for podana in mnozniki_w(source[:granica]):
        assert abs(podana - MARGIN) < 0.005, (
            "proza podaje mnoznik %s, a MARGIN = %.4f" % (podana, MARGIN))

    # Kontrola narzedzia — wykonywana za kazdym przebiegiem, nie raz przy pisaniu.
    nieaktualne = "Margines jest x2 nad najwyzszym zmierzonym przebiegiem."
    assert mnozniki_w(nieaktualne) == [2.0], mnozniki_w(nieaktualne)
    zgodne = "Margines wynosi %.2fx nad najwyzszym zmierzonym przebiegiem." % MARGIN
    for podana in mnozniki_w(zgodne):
        assert abs(podana - MARGIN) < 0.005, (podana, MARGIN)
    assert mnozniki_w(zgodne), "detektor nie widzi zdania, ktore ma widziec"
    pomiar = "Margines liczyl sie wobec zapisanych 77,04 sekundy."
    assert mnozniki_w(pomiar) == [], (
        "pomiar wziety za mnoznik: " + repr(mnozniki_w(pomiar)))
    obok = "Rozrzut hosta na jednym module to 1,54x przy tym samym kodzie."
    assert mnozniki_w(obok) == [], (
        "mnoznik spoza zdania o marginesie: " + repr(mnozniki_w(obok)))


def test_over_budget_boundary_is_strict_greater_than():
    assert over_budget(SUITE_RUNTIME_BUDGET_S) is False
    assert over_budget(SUITE_RUNTIME_BUDGET_S - 0.001) is False
    assert over_budget(SUITE_RUNTIME_BUDGET_S + 0.001) is True


def test_over_budget_default_argument_tracks_the_shared_constant():
    """Wersja bez podanego `budget_s` musi patrzeć na TĘ SAMĄ stałą, nie na kopię."""
    assert over_budget(SUITE_RUNTIME_BUDGET_S + 1.0) is True
    assert over_budget(SUITE_RUNTIME_BUDGET_S - 1.0) is False


def test_ci_gate_step_reads_this_files_constant_not_a_second_copy():
    """Krok YAML musi czytać `SUITE_RUNTIME_BUDGET_S` STĄD, nie nosić drugiej liczby.

    Dwa źródła progu rozjeżdżają się bezszelestnie przy pierwszej edycji jednego
    z nich — dokładnie klasa usterki, którą `test_report_claims.py` łapie dla
    stałych cytowanych w `reports/`. YAML nie jest raportem, więc tamta bramka
    go nie widzi; ten test jest jej odpowiednikiem dla workflow.
    """
    text = _workflow_text()
    assert "tools/tests/test_suite_runtime_budget.py" in text, text
    assert "SUITE_RUNTIME_BUDGET_S" in text, text
    # Żaden inny fragment kroku nie wpisuje progu jako gołej liczby przypisanej do
    # zmiennej „budget" z ręki — to złapałoby drugą, ukrytą kopię wartości.
    assert not re.search(r"budget\s*=\s*[\"']?\d", text, re.IGNORECASE), text


def test_ci_gate_step_is_a_comparison_that_can_exit_non_zero():
    """Krok o tej nazwie musi umieć wywalić joba, nie tylko wypisać liczby.

    Ta sama klasa kontroli, co `test_ci_reference_parity_step_is_a_gate_not_a_print`
    w `test_ci_workflows.py` (zarezerwowanym dla innej pozycji) — napisana tu, żeby
    nie dotykać cudzego pliku.
    """
    text = _workflow_text()
    step_start = text.index("Run tool tests")
    step = text[step_start:text.index("\n      - name:", step_start)]
    assert "SUITE_RUNTIME_BUDGET_S" in step, step
    assert re.search(r"exit\s+1\b", step), step
    assert "set -euo pipefail" in step, (
        "bez tego krok kontynuowałby po awarii test_all.py aż do własnego "
        "porownania czasu i mógłby zameldować sukces mimo nieudanych testów")

def test_cpu_dzieci_czyta_drugi_wiersz_times_i_odrzuca_smieci():
    """Kontrola detektora dla `cpu_dzieci`: dobre wejście, złe wejście, granica.

    Wartość bierze się z DRUGIEGO wiersza (`times` daje najpierw powłokę, potem
    dzieci) — bramka na pierwszym wierszu mierzyłaby czas samej powłoki, czyli
    liczbę bliską zeru, i stosunek CPU/ściana wychodziłby zawsze „niemierzalny".
    """
    import tempfile

    def zapisz(tresc):
        uchwyt = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        uchwyt.write(tresc)
        uchwyt.close()
        return uchwyt.name

    odczyt = cpu_dzieci(zapisz("0m0.002s 0m0.000s\n1m30.500s 0m0.020s\n"))
    assert odczyt == 90.52, (
        f"czytnik zwrócił {odczyt}, a dzieci mają 1m30.500s + 0m0.020s = 90.52 s; "
        "wartość 0.002 znaczy, że czyta PIERWSZY wiersz, czyli czas samej powłoki")
    zero = cpu_dzieci(zapisz("0m1.000s 0m2.000s\n0m0.000s 0m0.000s\n"))
    assert zero == 0.0, (
        f"czytnik zwrócił {zero} dla zerowych dzieci — bierze wiersz powłoki")

    for zle, opis in (("0m0.002s 0m0.000s\n", "jeden wiersz"),
                      ("", "pusty plik"),
                      ("0m0.002s 0m0.000s\nreal 1m30s\n", "inny format drugiego wiersza")):
        try:
            cpu_dzieci(zapisz(zle))
        except ValueError:
            continue
        raise AssertionError(f"`cpu_dzieci` przyjęło wejście, którego nie powinno: {opis}")


def test_werdykt_odmawia_porownania_gdy_maszyna_nie_oddawala_cpu():
    """Trzy strony naraz, każda na PRAWDZIWYM pomiarze z 09.09.2026.

    Bramka bez pierwszej strony byłaby dzisiejszą bramką; bez drugiej byłaby
    bramką WYŁĄCZONĄ, przepuszczającą prawdziwe spowolnienie kodu.
    """
    # 1. Przebieg z incydentu 08.09.2026 (335,668 s) przy CPU rzędu runnerowego:
    #    ponad progiem, ale NIE odrzucony, bo maszyna nie oddawała CPU.
    odrzuc, komunikat = werdykt(335.668, 70.8)
    assert odrzuc is False, komunikat
    assert "NIE JEST porownywany" in komunikat, komunikat

    # 2. Prawdziwe spowolnienie KODU: maszyna oddaje CPU, czas ponad progiem.
    odrzuc, komunikat = werdykt(200.0, 200.0)
    assert odrzuc is True, komunikat
    assert "przekroczyl prog" in komunikat, komunikat

    # 3. Zmierzone przebiegi w progu — runner i spokojny kontener.
    for sciana, cpu in ((53.517, 70.804), (91.742, 90.522)):
        odrzuc, komunikat = werdykt(sciana, cpu)
        assert odrzuc is False, komunikat
        assert "w progu" in komunikat, komunikat


def test_podloga_mierzalnosci_lezy_miedzy_zmierzonymi_stanami_maszyny():
    """Podłoga ma rozdzielać POMIARY, nie być okrągłą liczbą.

    Kontrola na obu brzegach: musi leżeć pod najniższym zmierzonym przebiegiem bez
    obciążenia i nad najwyższym pod obciążeniem. Wartości są tu wpisane jako dane
    pomiaru — ich źródłem jest `reports/mierzalnosc-czasu-zestawu.md`.
    """
    bez_obciazenia = (0.987, 0.988, 1.323)
    pod_obciazeniem = (0.451, 0.444)
    assert MIERZALNOSC_MIN < min(bez_obciazenia), (
        f"podłoga {MIERZALNOSC_MIN} jest nad zmierzonym przebiegiem bez obciążenia "
        f"{min(bez_obciazenia)} — bramka pomijałaby porównanie na zdrowej maszynie")
    assert MIERZALNOSC_MIN > max(pod_obciazeniem), (
        f"podłoga {MIERZALNOSC_MIN} jest pod zmierzonym przebiegiem POD obciążeniem "
        f"{max(pod_obciazeniem)} — bramka porównywałaby czas maszyny z progiem kodu")


def test_krok_ci_liczy_werdykt_modulem_a_nie_wlasnym_porownaniem():
    """Krok ma wołać `werdykt`, a nie porównywać liczby po swojemu.

    Druga kopia warunku rozjechałaby się z modułem przy pierwszej zmianie podłogi —
    ta sama rodzina, co `test_ci_gate_step_reads_this_files_constant_not_a_second_copy`.
    """
    text = _workflow_text()
    step_start = text.index("Run tool tests")
    step = text[step_start:text.index("\n      - name:", step_start)]
    assert "B.werdykt(" in step, (
        "krok nie woła `werdykt` z tego modułu:\n" + step)
    assert not re.search(r"sys\.exit\(0 if float\('?\$?\w+'?\) <=", step), (
        "w kroku został stary warunek porównujący czas z progiem z pominięciem "
        "podłogi mierzalności:\n" + step)


def test_krok_ci_mierzy_czas_cpu_zestawu_a_nie_tylko_sciane():
    """Krok musi WOŁAĆ `times` wokół zestawu i liczyć różnicę — 6.D42.

    Sam wypis stosunku bez dwóch odczytów mierzyłby CPU wszystkich dzieci kroku,
    razem z podstawieniami liczącymi próg. Różnica dwóch odczytów mierzy zestaw.
    """
    text = _workflow_text()
    step_start = text.index("Run tool tests")
    step = text[step_start:text.index("\n      - name:", step_start)]
    assert step.count("times > ") == 2, (
        "krok ma czytać `times` PRZED i PO zestawie; jeden odczyt nie daje różnicy:\n" + step)
    assert "cpu_dzieci" in step, "krok nie woła czytnika z tego modułu, tylko liczy po swojemu"
    # STOSUNEK MA TRAFIC DO LOGU — sprawdzone DWUSTRONNIE, a nie po napisie w YAML-u.
    # Wersja z 6.D42 (1/2) szukała tu literału `CPU/sciana` w kroku; po wpięciu
    # `werdykt` stosunek jedzie do logu JEGO komunikatem, więc bramka na literał
    # zapaliłaby się na poprawnym kroku. Przekierowana, i sprawdza teraz WIĘCEJ:
    # że krok wypisuje komunikat werdyktu ORAZ że każda gałąź werdyktu ten stosunek
    # w komunikacie niesie.
    assert "print(komunikat)" in step, (
        "krok liczy werdykt, ale go nie wypisuje — liczby nie zobaczy nikt:\n" + step)
    for sciana, cpu, opis in ((335.668, 70.8, "niemierzalny"),
                              (200.0, 200.0, "ponad progiem"),
                              (53.517, 70.804, "w progu")):
        _odrzuc, komunikat = werdykt(sciana, cpu)
        assert "CPU/sciana" in komunikat, (
            f"komunikat werdyktu ({opis}) nie niesie stosunku: {komunikat!r}")
    przed = step.index("times > ")
    start = step.index("start=$(date")
    assert przed < start, "pierwszy odczyt `times` musi stać PRZED startem pomiaru ściany"


# --- 6.D193: ile KSZTAŁTÓW zapisu pomiaru niesie drzewo ------------------------------
#
# **Skąd ta sekcja.** Do 13.09.2026 zdanie „innych list pomiarów w drzewie NIE MA"
# stało w docstringu testu wyżej i **nie miało pod sobą ani jednej linii kodu**. Skan,
# na który się powołuje, wykonano RĘCZNIE raz, a jego wynik przepisano do prozy — czyli
# dokładnie to, przed czym ten projekt broni się wszędzie indziej. Ta sekcja jest
# przepisaniem tamtego zdania na bramkę, a nie dopiskiem obok.
#
# **Skan po dacie ISO jest ZAŁOŻENIEM O KSZTAŁCIE i dlatego klasyfikuje, a nie tylko
# liczy.** Lista z datą w kluczu słownika albo na drugiej pozycji krotki nie zostałaby
# przez wzorzec „krotka zaczynająca się od daty" znaleziona, a milczenie skanu wyglądałoby
# identycznie jak brak takiej listy — rodzina 6.D159, bramka prawdziwa z pustego zbioru.

#: Gdzie stoi data ISO w literale stałej. Pięć kształtów, bo tyle da się odróżnić
#: strukturalnie; `KSZTALTY_BEZ_PRZYKLADU` mówi, których drzewo dziś nie ma.
KSZTALT_A = "data na pozycji 0"         # krotka/lista wpisów, data pierwsza — `POMIARY`
KSZTALT_B = "data na pozycji > 0"       # krotka/lista wpisów, data dalej
KSZTALT_C = "data w kluczu słownika"    # `OPISY_Z_RANGA_DOZWOLONA`, `NOTATIONS`
KSZTALT_D = "data w wartości słownika"
KSZTALT_E = "data gdzie indziej w literale"

#: Zmierzone 13.09.2026 na całym `tools/` (6.D163 skanowało tylko `tools/tests/`).
#: Wartość to liczba stałych danego kształtu.
KSZTALTY_W_DRZEWIE = {KSZTALT_A: 1, KSZTALT_C: 2}

#: **Kształty, których drzewo NIE MA — i to jest treść, a nie dopisek.** Zero znaczy
#: tyle, co przyrząd, który je wypisał: skan niewidzący kształtu B odpowiedziałby „zero"
#: tak samo, jak skan widzący i nieznajdujący. Dlatego bramka niżej **wstrzykuje**
#: literały wszystkich pięciu kształtów i żąda, żeby klasyfikator trafił w każdy.
KSZTALTY_BEZ_PRZYKLADU = (KSZTALT_B, KSZTALT_D, KSZTALT_E)

#: Ile stałych modułowych pod `tools/` niesie JAKĄKOLWIEK datę ISO w literale — górne
#: ograniczenie na „coś, co może być zapisem pomiaru". **Siedem, i te dwie liczby opisują
#: DWIE RÓŻNE populacje, co pomyliłem przy pierwszym podejściu:** kontenerów (krotka,
#: lista, słownik) jest **trzy** i tylko one dają się sklasyfikować po położeniu daty;
#: pozostałe cztery to dwa widoki `POMIARY` odcięte datą (`POMIARY_RUNNERA_11_09`,
#: `POMIARY_KONTENERA_JEDNO_DRZEWO` — wyrażenia, nie literały) i dwa skalary
#: (`AS_OF`, `DZIEN_PIERWSZEGO_WYNOSZENIA`). Widok nie jest osobnym zapisem, a skalar
#: nie jest listą — ale **oba niosą datę i oba musi widzieć skan**, inaczej „siedem"
#: byłoby liczbą bez przedmiotu.
STALYCH_Z_DATA_ISO = 7

#: Ile z tych siedmiu to KONTENERY, czyli jedyne, którym kształt w ogóle przysługuje.
KONTENEROW_Z_DATA_ISO = 3

#: **GRANICA TEGO SKANU, wypisana, bo jest jego najważniejszą częścią (6.D193).**
#: Kryterium daty w literale nie jest pełnym sitem na zapisy pomiarów, i to jest
#: **zmierzone, nie przewidziane**: z trzech stałych, które pozycja 6.D193 wymieniła
#: jako kandydatki, **dwie nie mają daty ISO nigdzie w literale**.
#: `SZESC_PRZYPADKOW` (`test_field_paths.py`) niesie numery pozycji, nie daty;
#: `POMIARY_BRAKOW` (`test_readme_claims.py`) **JEST zapisem pomiaru** („Zmierzone
#: 10.09.2026 na `a202423`"), ale ta data stoi w komentarzu `#:` i w notacji polskiej,
#: więc nie widzi jej ŻADNE kryterium oparte na dacie w literale — niezależnie od jej
#: położenia. Zarzut pozycji dotyczył położenia daty; pomiar pokazał dziurę większą.
#:
#: **Ta stała jest SPRAWDZANA WOBEC DRZEWA, a nie tylko wymieniana, i to jest poprawka
#: po zielonej kontroli negatywnej (KN-5).** Pierwsza wersja miała pętlę „dla każdej
#: nazwy w tym słowniku sprawdź, że skan jej nie widzi" — i opróżnienie słownika
#: **nic nie zmieniało**, bo pętla po pustym zbiorze wykonuje się zero razy. Granica
#: była wtedy prozą w przebraniu asercji. Dziś każda pozycja ma podany moduł, a bramka
#: żąda, żeby stała tam NAPRAWDĘ była i żeby w jej literale NAPRAWDĘ nie było daty —
#: plus równości na liczbie pozycji, żeby skreślenie wpisu nie przeszło po cichu.
STALE_BEZ_DATY_W_LITERALE = {
    "SZESC_PRZYPADKOW": (
        "tools/tests/test_field_paths.py",
        "tablica przypadków bramki; numery pozycji (`6.D59`), nie daty"),
    "POMIARY_BRAKOW": (
        "tools/tests/test_readme_claims.py",
        "ZAPIS POMIARU, ale data stoi w komentarzu `#:`, nie w literale"),
}

#: Ile granic sita daty jest wymienionych. Równość, bo skreślenie granicy ma zapalać.
GRANIC_SITA_DATY = 2

_DATA_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def _stala_w_module(sciezka, nazwa):
    """Literał przypisany stałej `nazwa` w module `sciezka`, albo `None`."""
    import ast

    with open(sciezka, encoding="utf-8") as uchwyt:
        drzewo = ast.parse(uchwyt.read())
    for wezel in drzewo.body:
        if isinstance(wezel, ast.Assign) and any(
                getattr(cel, "id", None) == nazwa for cel in wezel.targets):
            return wezel.value
    return None


def _ksztalt_literalu(wezel):
    """Kształt literału stałej albo `None`, gdy daty ISO w nim nie ma.

    Klasyfikuje po POŁOŻENIU daty, bo to właśnie położenie odróżnia zapis, który stary
    wzorzec widział, od zapisu, którego by nie zobaczył.
    """
    import ast

    if not isinstance(wezel, (ast.Tuple, ast.List, ast.Dict)):
        return None
    if not _DATA_ISO.search(ast.unparse(wezel)):
        return None

    if isinstance(wezel, ast.Dict):
        for klucz in wezel.keys:
            if klucz is not None and _DATA_ISO.search(ast.unparse(klucz)):
                return KSZTALT_C
        return KSZTALT_D

    for element in wezel.elts:
        if not isinstance(element, (ast.Tuple, ast.List)) or not element.elts:
            continue
        for i, pole in enumerate(element.elts):
            if _DATA_ISO.search(ast.unparse(pole)):
                return KSZTALT_A if i == 0 else KSZTALT_B
    return KSZTALT_E


def stale_z_data_iso():
    """`[(plik, wiersz, nazwa, kształt)]` — stałe modułowe pod `tools/` z datą ISO.

    `kształt` jest `None` dla wszystkiego, co nie jest kontenerem: skalara i wyrażenia.
    **Wchodzą do wyniku mimo to**, bo górna granica „co może być zapisem pomiaru" ma
    obejmować także je — inaczej skan odpowiadałby na węższe pytanie, niż zadano.

    Przez `tree_walk.walk`, bo to jedyne przejście honorujące `.gitignore` w tym
    projekcie; własny `os.walk` wchodziłby w `build/` i `__pycache__`.
    """
    import ast
    import tree_walk as tw

    nazwa_stalej = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
    out = []
    for baza, _kat, pliki in tw.walk(os.path.join(ROOT, "tools")):
        for plik in sorted(pliki):
            if not plik.endswith(".py"):
                continue
            sciezka = os.path.join(baza, plik)
            with open(sciezka, encoding="utf-8", errors="replace") as uchwyt:
                try:
                    drzewo = ast.parse(uchwyt.read())
                except SyntaxError:
                    continue
            for wezel in drzewo.body:
                if not isinstance(wezel, ast.Assign):
                    continue
                for cel in wezel.targets:
                    nazwa = getattr(cel, "id", None)
                    if not nazwa or not nazwa_stalej.match(nazwa):
                        continue
                    if not _DATA_ISO.search(ast.unparse(wezel.value)):
                        continue
                    out.append((os.path.relpath(sciezka, ROOT), wezel.lineno, nazwa,
                                _ksztalt_literalu(wezel.value)))
    return out


def test_klasyfikator_ksztaltow_TRAFIA_W_KAZDY_Z_PIECIU():
    """Kontrola PRZYRZĄDU na wejściu syntetycznym — bez niej „zero" nic nie znaczy.

    Drzewo ma dziś kształty A i C, a B, D i E **nie ma ani jednego**. Skan, który
    kształtu B nie umiałby zobaczyć, odpowiedziałby na nie „zero" **tak samo**, jak skan
    umiejący. To jest rodzina 6.D159 — bramka prawdziwa z pustego zbioru — i jedyną
    obroną jest literał zbudowany na tę okazję.
    """
    import ast

    probki = {
        KSZTALT_A: '(("2026-09-11", 1.0, "cos"),)',
        KSZTALT_B: '(("cos", "2026-09-11", 1.0),)',
        KSZTALT_C: '{"2026-09-11": "powod"}',
        KSZTALT_D: '{"klucz": "zmierzone 2026-09-11"}',
        KSZTALT_E: '("2026-09-11", "plaska krotka bez zagniezdzenia")',
    }
    for spodziewany, zrodlo in sorted(probki.items()):
        dostany = _ksztalt_literalu(ast.parse(zrodlo, mode="eval").body)
        assert dostany == spodziewany, (
            "klasyfikator na literale %s dał %r zamiast %r — kształt, którego nie umie "
            "zobaczyć, wygląda w wyniku identycznie jak kształt, którego nie ma"
            % (zrodlo, dostany, spodziewany))

    for milczy in ('(("cos", 1.0),)', '{"klucz": "11.09.2026"}'):
        assert _ksztalt_literalu(ast.parse(milczy, mode="eval").body) is None, (
            "klasyfikator zapalił się na literale bez daty ISO: %s — wtedy liczby niżej "
            "mówią o czymś innym, niż mówią, że mówią" % milczy)


def test_ile_ksztaltow_zapisu_pomiaru_niesie_drzewo():
    """ODPOWIEDŹ 6.D193: „innych list pomiarów nie ma" przestaje wisieć na odczycie.

    Zdanie zostaje prawdziwe po zdjęciu założenia o kształcie — ale **nie było
    sprawdzone, tylko trafione**: stary skan nie mógł zobaczyć kształtu C, a jeden
    słownik tego kształtu (`OPISY_Z_RANGA_DOZWOLONA`) stoi **w tym samym pliku, kilkaset
    wierszy pod `POMIARY`**, i czyta go ta sama asercja, która tamto zdanie wypowiada.
    """
    znalezione = stale_z_data_iso()
    assert len(znalezione) == STALYCH_Z_DATA_ISO, (
        "stałych modułowych z datą ISO w literale jest %d przy zapadce %d: %s"
        % (len(znalezione), STALYCH_Z_DATA_ISO,
           sorted((p, n) for p, _w, n, _k in znalezione)))

    import collections
    kontenery = [w for w in znalezione if w[3] is not None]
    assert len(kontenery) == KONTENEROW_Z_DATA_ISO, (
        "kontenerów z datą ISO jest %d przy zapadce %d: %s — tylko im przysługuje "
        "kształt, więc ta liczba i `STALYCH_Z_DATA_ISO` opisują dwie różne populacje"
        % (len(kontenery), KONTENEROW_Z_DATA_ISO,
           sorted((p, n) for p, _w, n, _k in kontenery)))

    rozklad = collections.Counter(k for _p, _w, _n, k in kontenery)
    assert dict(rozklad) == KSZTALTY_W_DRZEWIE, (
        "rozkład kształtów to %s, a zmierzony 13.09.2026 był %s — kształt, który doszedł, "
        "trzeba rozstrzygnąć: zapis przebiegów czy tablica przypadków"
        % (dict(rozklad), KSZTALTY_W_DRZEWIE))

    for pusty in KSZTALTY_BEZ_PRZYKLADU:
        assert pusty not in rozklad, (
            "kształt `%s` przestał być pusty — a to jest ten, którego stary wzorzec "
            "by NIE ZOBACZYŁ" % pusty)

    # GRANICA: kryterium daty w literale nie jest pełnym sitem. Dwie stałe wymienione
    # w pozycji nie mają daty ISO nigdzie w literale, a jedna z nich JEST zapisem pomiaru.
    #
    # Sprawdzane WOBEC DRZEWA, nie wymieniane: pętla po samym słowniku wychodziła zielona
    # po jego opróżnieniu (KN-5), bo zero obrotów przechodzi każdą asercję w środku.
    assert len(STALE_BEZ_DATY_W_LITERALE) == GRANIC_SITA_DATY, (
        "granic sita daty wymieniono %d przy zapadce %d — skreślenie granicy ma zapalać "
        "bramkę, a nie wygaszać ją przez brak obrotów pętli"
        % (len(STALE_BEZ_DATY_W_LITERALE), GRANIC_SITA_DATY))

    nazwy = {n for _p, _w, n, _k in znalezione}
    # LICZNIK OBROTÓW, nie długość słownika — poprawka po KN-5b (rodzina `Take(0)`
    # z 6.D188). Równość wyżej pilnuje SŁOWNIKA i przechodzi, gdy ktoś oślepi PĘTLĘ;
    # dopiero ten licznik wiąże jedno z drugim.
    sprawdzonych = 0
    for nazwa, (modul, powod) in sorted(STALE_BEZ_DATY_W_LITERALE.items()):
        assert nazwa not in nazwy, (
            "`%s` stała się widoczna dla kryterium daty w literale — granica zapisana "
            "przy 6.D193 („%s”) przestała obowiązywać i trzeba ją przeliczyć"
            % (nazwa, powod))
        assert len(powod) > 40, (nazwa, powod)

        # I DRUGA STRONA: stała ma w tym module NAPRAWDĘ stać, a jej literał NAPRAWDĘ
        # nie nieść daty. Bez tego „skan jej nie widzi" byłoby prawdą także o stałej,
        # której nie ma — czyli zdaniem o niczym.
        wezel = _stala_w_module(os.path.join(ROOT, modul), nazwa)
        assert wezel is not None, (
            "`%s` nie stoi już w `%s` — granica opisuje stałą, której nie ma, więc "
            "„skan jej nie widzi” przestało cokolwiek znaczyć" % (nazwa, modul))
        import ast
        assert not _DATA_ISO.search(ast.unparse(wezel)), (
            "`%s` w `%s` NIESIE dziś datę ISO w literale — granica z 6.D193 mówiła, że "
            "nie niesie, i to jest właśnie ta zmiana, którą miała złapać" % (nazwa, modul))
        sprawdzonych += 1

    assert sprawdzonych == GRANIC_SITA_DATY, (
        "pętla granic wykonała %d obrotów przy %d wymienionych — pusta pętla przechodzi "
        "każdą asercję w środku, więc bez tego licznika granica jest prozą w przebraniu "
        "asercji (zmierzone: KN-5b wyszła ZIELONA)" % (sprawdzonych, GRANIC_SITA_DATY))


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
