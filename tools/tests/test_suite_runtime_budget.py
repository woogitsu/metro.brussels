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
import math
import os
import re
import statistics
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
#: **Kontener przekracza dziś próg o 14 %, a od 6.D247 zatrzymuje go PODŁOGA.**
#: Ten akapit jest PRZEPISANY, a nie dopisany obok (16.09.2026): poprzednia wersja
#: mówiła, że podłoga kontenera NIE zatrzymuje, bo 0,991 stało wysoko nad
#: `MIERZALNOSC_MIN` (0,75) — i to już nieprawda. Po podwyżce 0,75 → 1,168 stosunek
#: 0,991 leży POD podłogą, więc `werdykt` nie dopuszcza tego pomiaru do porównania
#: z progiem i mówi o tym wierszem w komunikacie. Test niżej wykonuje ten rachunek,
#: żeby zdanie nie było opinią, i ma odwróconą polaryzację razem z tym akapitem.
#: Nie jest to usterka bramki: bramka chodzi WYŁĄCZNIE na runnerze, w kroku
#: „Run tool tests". Zostaje natomiast dowód, że **jedna lista na dwie maszyny daje
#: margines nieprawdziwy dla obu** — dokładnie to, o co pytała pozycja 6.D135;
#: zmieniła się droga, którą drzewo to dziś mówi, a nie sam wniosek.
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
     "próg 150 s, a od 6.D247 zatrzymuje go PODŁOGA 1,168, patrz komentarz wyżej"),
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

#: CZEGO TA LICZBA NIE OBEJMUJE — dopisane 14.09.2026 (6.D205), bo bez tego zdania
#: czyta się ją jako „najwyższa ściana, jaką runner zmierzył", a jest to najwyższa
#: ściana, jaką ktoś ZAPISAŁ tutaj.
#:
#: Dwa przebiegi runnera z 13.09.2026 leżą WYŻEJ i wpisu nie mają: PR #580 — 130,046 s
#: (job 103685939363) i PR #581 — 130,982 s (job 103717054000, maszyna
#: `metro-wsl-DOM-NEW-03`, której ta lista nie zna). Oba spełniają regułę doboru
#: z `tests/data/ci-logs/README.md` i oba powinny tu być.
#:
#: NIE WESZŁY, bo wejście wywraca cztery asercje naraz — ZMIERZONE, nie wywnioskowane,
#: przez wstawienie obu wpisów razem z logami do osobnego drzewa roboczego: 28/32,
#: czerwone `test_budget_stays_above_the_measured_maximum_with_a_real_margin`
#: (MARGIN spada 1,2886 -> 1,1452, poniżej progu 1,2),
#: `test_jeden_prog_dla_obu_maszyn_przestalby_widziec_regres_na_runnerze`,
#: `test_runner_liczy_rownolegle_a_kontener_szeregowo` (stosunek 1,453 poniżej
#: dotychczasowego minimum 1,599) i `test_slowo_runner_stoi_nad_DWIEMA_maszynami_ale_ich_NIE_rozdziela`
#: (trzecia maszyna przy zapadce na dwóch).
#:
#: Każda z tych czterech naprawa jest zmianą ZAPASU albo rozstrzygnięcia 6.D149,
#: czyli tym, co pole „Poza zakresem" 6.D205 wyklucza. Wiersz stoi więc w sekcji
#: „Czego agent nie ruszy bez decyzji" w `docs/TASKS.md`.
#:
#: Co ta lista wie NIEZALEŻNIE od tego: `POMIARY_CPU_BIEZACEGO_DRZEWA` niżej niesie
#: ścianę 164,734 s z runnera, czyli powyżej `SUITE_RUNTIME_BUDGET_S`, i liczy to
#: `test_prog_cpu_NIE_zapalilby_sie_na_zadnym_zmierzonym_przebiegu`. Maksimum ściany
#: nie jest więc w projekcie NIEZNANE — jest rozdzielone na dwie listy o różnych
#: warunkach wejścia: ta wymaga zacommitowanego logu, tamta bierze artefakt.

#: Próg bramki CI. Czytany z TEGO pliku przez krok „Run tool tests" w
#: `python-tests.yml` (`python3 -c "... import test_suite_runtime_budget ..."`) —
#: jedno miejsce prawdy, nie liczba wpisana w YAML z ręki.
SUITE_RUNTIME_BUDGET_S = 150.0

#: Margines progu nad najwyższym zmierzonym przebiegiem — LICZONY, nie opisany prozą.
#: Poprzednia wersja nosiła tę liczbę w komentarzu, wpisaną z ręki — i to właśnie
#: zdanie zestarzało się bez śladu, bo nic nie łączyło go z liczbami obok. Ile wtedy
#: podawało, stoi w `reports/zapis-czasu-zestawu.md`, gdzie jest historią.
MARGIN = SUITE_RUNTIME_BUDGET_S / MEASURED_MAX_WALL_S

# --- PRÓG NA CZASIE CPU: co ODRZUCA bramka, i dlaczego już nie czas ściany ----------

#: Osiem przebiegów runnera na DZISIEJSZYM drzewie (2466 testów, 126 modułów),
#: wzięte z artefaktów `czas-zestawu` (`python-tests.yml`, krok „Zapis czasu przebiegu
#: jako artefakt", retencja 30 dni): `(id artefaktu, ściana_s, cpu_s)`.
#:
#: **Po co osobna lista, skoro `POMIARY` już jest.** `POMIARY` niesie czas ŚCIANY,
#: a czas CPU tylko pośrednio, jako stosunek w polu „na czym" — i wyłącznie dla drzew
#: z 11. i 13.09.2026 (2315-2433 testów). Margines progu CPU ma opisywać drzewo, dla
#: którego go liczono, a nie tamto; wpisy `POMIARY` dla dzisiejszego drzewa wymagają
#: swoich logów w `tests/data/ci-logs/` (6.D190) i to jest osobna pozycja.
#:
#: **Każdy wiersz jest do odtworzenia jednym poleceniem**, bo id artefaktu stoi obok
#: liczby — inaczej byłaby to lista liczb przepisanych z ręki, czyli to, co 6.D26
#: zdjęło z `MEASURED_MAX_WALL_S`:
#:
#:   curl -sL -H "Authorization: Bearer $GITHUB_TOKEN" \
#:     https://api.github.com/repos/woogitsu/metro.brussels/actions/artifacts/<ID>/zip
POMIARY_CPU_BIEZACEGO_DRZEWA = (
    (10339175683, 141.080, 212.746),
    (10338927190, 131.201, 202.146),
    (10341466241, 123.685, 209.685),
    (10341033235, 121.671, 203.091),
    (10341643027, 136.248, 199.405),
    (10341963856, 164.734, 226.537),
    (10344952688, 142.498, 201.193),
    (10345580689, 128.564, 196.031),
)

#: Najwyższy i środkowy ZMIERZONY czas CPU dzisiejszego drzewa — wyprowadzone, nie
#: wpisane, z tego samego powodu co `MEASURED_MAX_WALL_S`.
MEASURED_MAX_CPU_S = max(cpu for _id, _w, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA)
MEASURED_MED_CPU_S = statistics.median(
    [cpu for _id, _w, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA])

#: PRÓG, KTÓRY ODRZUCA. Od tej pozycji werdykt liczy się z czasu CPU, a nie ze ściany.
#:
#: **Skąd 440, i to są DWA rachunki dające tę samą liczbę.** Reguła 6.D11 brzmiała
#: „dwukrotność zmierzonego maksimum" (`150,0 = 1,947 x 77,04`); ta sama reguła nad
#: maksimum CPU dzisiejszego drzewa daje `1,947 x 226,537 = 441,1`. Margines tamtego
#: progu nad MEDIANĄ czterech przebiegów tamtego dnia wynosił `150,0 / 68,705 = 2,183`;
#: ta sama liczba nad medianą CPU dzisiejszego drzewa daje `2,183 x 202,618 = 442,4`.
#: Wybrane **440,0** leży pod obiema (marginesy `1,942` i `2,172`), czyli jest odrobinę
#: CIAŚNIEJSZE niż to, co ustawiono 06.09.2026, a nie luźniejsze.
#:
#: **Czego ta zmiana NIE naprawia, wypisane razem z liczbą.** Czas CPU też zależy od
#: maszyny: na IDENTYCZNYM drzewie zmierzono rozrzut `x1,239` (23,9 %), wobec `x1,412`
#: (41,2 %) na ścianie — czyli CPU jest mniej wrażliwy, a nie niewrażliwy. Margines
#: 1,942 zostawia nad tym rozrzutem jeszcze 57 % zapasu, i to jest cały powód, dla
#: którego próg na CPU w ogóle stoi wyżej niż szum. Liczby: `WZORZEC_ROZRZUTU` niżej.
SUITE_CPU_BUDGET_S = 440.0

#: Margines progu CPU — liczony, jak `MARGIN`, a nie opisany prozą.
MARGIN_CPU = SUITE_CPU_BUDGET_S / MEASURED_MAX_CPU_S

#: ROZRZUT NA IDENTYCZNYM DRZEWIE, zmierzony na 265 artefaktach `czas-zestawu`
#: z 10-14.09.2026 (30 grup o tej samej parze (testów, modułów), w każdej >= 3
#: przebiegi): `(mediana grup, maksimum grup)` ilorazu max/min.
#:
#: To jest liczba, która mówi, ILE margines musi unieść, zanim zacznie mówić o kodzie.
WZORZEC_ROZRZUTU = {
    "sciana": (1.091, 1.412),
    "cpu": (1.048, 1.239),
}


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
#: **DZISIEJSZA WARTOŚĆ TO 1,168. Akapity do wiersza z „0,75 -> 1,168" opisują
#: WYPROWADZENIE POPRZEDNIE (09.09.2026) i są tu jako historia, nie jako stan.**
#: Ten wiersz stoi na SZCZYCIE bloku, a nie pod nim, i to jest wybór: deklaracja
#: wtopiona za wywodem zostawia czytającego, który zaczął od góry, ze zdaniami
#: w czasie teraźniejszym o liczbie, której już nie ma — dokładnie ta pomyłka,
#: przed którą `CLAUDE.md` §9 przestrzega przy własnym akapicie o etykietach.
#:
#: WSZYSTKIE LICZBY, Z KTÓRYCH WYSZŁA POPRZEDNIA PODŁOGA, zmierzone 09.09.2026:
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
#: **0,75 -> 1,168 (16.09.2026, 6.D247, decyzja właściciela). Ten akapit jest
#: PRZEPISANY, a nie dopisany obok, i zmienia się w nim PYTANIE, nie tylko liczba.**
#:
#: Do 16.09.2026 podłoga odpowiadała na pytanie „czy maszyna oddawała rdzenie”
#: i rozdzielała kontener spokojny (0,987) od obciążonego (0,451). Rozdzielała je
#: poprawnie i robi to nadal — ale **przestało to wystarczać**, bo pula wykonująca
#: joby przestała być tą, na której próg skalibrowano.
#:
#: **Co się stało.** 16.09.2026 job `tools` padł na `docker-runner-02` z czasem CPU
#: **517,499 s** przy progu 440,0 s, stosunkiem CPU/ściana **0,992** i zestawem zielonym
#: w całości (`2497/2497 przeszło`). Ten sam commit bywa zielony w **159 s ściany**
#: na `metro-wsl-DOM-NEW-*`. Stosunek 0,992 leży **wysoko nad starą podłogą 0,75**,
#: więc pomiar został porównany z progiem, który opisuje inną maszynę.
#:
#: **Dlaczego nie załatwił tego warunek maszyny z 6.D149 — i to jest tu najważniejsze.**
#: Krok CI woła `B.werdykt(float(sys.argv[1]), float(sys.argv[2]))`, czyli DWA argumenty.
#: `maszyna` zostaje przy wartości domyślnej `MASZYNA_PROGU`, więc gałąź
#: `if maszyna != MASZYNA_PROGU` **nie wykonuje się w CI ani razu** — nic w kroku
#: nie czyta `RUNNER_NAME` i nazwa maszyny nie dociera do werdyktu w żadnej postaci.
#: Rozstrzygnięcie 6.D149 broni wyłącznie wywołań wewnątrz tego modułu.
#:
#: **Skąd 1,168.** Materiał kalibracyjny i incydent rozdzielają się bez reszty:
#:
#:   `POMIARY_RUNNERA`, 8 wpisów, `metro-wsl`       CPU/ściana  1,599 – 1,971
#:   `POMIARY_CPU_BIEZACEGO_DRZEWA`, 8 artefaktów    CPU/ściana  1,375 – 1,695
#:   kontener sesji, 7 wpisów                       CPU/ściana  0,987 – 0,991
#:   `docker-runner-02`, job `tools`, PR #633       CPU/ściana  **0,992**
#:
#: Luka między najniższym przebiegiem kalibracyjnym (1,375) a incydentem (0,992)
#: wynosi **x1,386**; środek geometryczny to **1,168**. Przy tej podłodze incydent
#: jest ODMÓWIONY z komunikatem, a **wszystkie osiem** przebiegów
#: `POMIARY_CPU_BIEZACEGO_DRZEWA` jest nadal PORÓWNANYCH — zmierzone.
#:
#: **Dlaczego nie nazwa maszyny.** `CLAUDE.md` §9 zabrania robić z nazwy maszyny
#: selektora; podłoga nie wymienia żadnej nazwy i nie mówi nic o liczebności puli.
#: Mierzy wyłącznie liczbę, którą krok i tak liczy i i tak wypisuje.
#:
#: KIERUNEK BŁĘDU ZOSTAJE BEZPIECZNY i to nadal jest część wyboru. Zbyt wysoka
#: podłoga NIE czerwieni CI — sprawia, że porównanie z progiem zostaje pominięte,
#: a wiersz o tym trafia do logu. Fałszywy alarm, który wyłącza bramki (6.D27),
#: jest tu niemożliwy z konstrukcji.
#:
#: **CZEGO TA PODWYŻKA NIE ROBI, i to jest wypisane, a nie przemilczane:** na maszynie
#: oddającej jeden rdzeń bramka po prostu MILKNIE. Prawdziwy regres kodu, który
#: trafi na `docker-runner-*`, przejdzie niezauważony — tak samo, jak dziś przechodzi
#: każdy przebieg kontenera. Wybór między fałszywym alarmem a ciszą został podjęty
#: świadomie i jest decyzją właściciela z 16.09.2026, nie wnioskiem agenta.
#:
#: **GRANICA TEJ LICZBY, wypisana razem z nią: n = 1.** Pod podłogą stoi JEDEN
#: przebieg `docker-runner-*`. Stara 0,75 miała n = 2 i też to mówiła
#: (`reports/mierzalnosc-czasu-zestawu.md` §5). Zanim 1,168 zacznie być traktowana
#: jak liczba dojrzała, powinna mieć kilka przebiegów z tej puli.
#:
#: **Odnośnik czytany razem z ostrzeżeniem, i to jest wybór.**
#: `reports/mierzalnosc-czasu-zestawu.md` jest raportem z 09.09.2026 i mówi o podłodze
#: **0,75** — w swoim dniu prawdziwie. **6.D108 zabrania go przepisywać**, więc nie
#: został tknięty; wyprowadzenie dzisiejszej liczby stoi w
#: `reports/6d247-sufit-mierzalnosci-zamiast-nazwy-maszyny.md`. Wskazanie obu naraz
#: jest tu potrzebne dlatego, że każdy z pięciu odnośników w tym module prowadzi
#: dziś do liczby, której moduł już nie wykonuje — i bez tego zdania czytający
#: musiałby się o tym dowiedzieć sam.
#:
#: **CZEGO TA PODŁOGA NIE WIDZI, liczbą, a nie zdaniem:** przebieg
#: (471,700 s ściany, 550,400 s CPU) ma stosunek 1,167, czyli o 0,001 pod podłogą,
#: a jego CPU stoi na **125 %** progu — i zostaje PRZEPUSZCZONY. Pod starą podłogą
#: 0,75 byłby odrzucony. Cisza wariantu (d) nie ogranicza się więc do maszyny
#: oddającej jeden rdzeń: obejmuje każdy przebieg o niskim stosunku, przy CPU
#: dowolnie wysokim. Pilnuje tego
#: `test_podloga_UCISZA_regres_ktory_stara_podloga_by_zlapala_i_to_jest_LICZBA`,
#: żeby cena tego wyboru stała w drzewie jako przypadek z liczbami.
MIERZALNOSC_MIN = 1.168

#: Maszyna, na której próg został SKALIBROWANY — 6.D149.
#:
#: `SUITE_RUNTIME_BUDGET_S` wychodzi z `MEASURED_MAX_WALL_S`, a to bierze wyłącznie
#: `POMIARY_RUNNERA`. Próg opisuje więc runnera i nikogo więcej; dla maszyny innej
#: niż ta porównanie z nim jest zdaniem o czymś, czego nikt nie mierzył.
MASZYNA_PROGU = MASZYNA_RUNNER


def werdykt(elapsed_s, cpu_s, budget_s=SUITE_RUNTIME_BUDGET_S, podloga=MIERZALNOSC_MIN,
            maszyna=MASZYNA_PROGU, cpu_budget_s=SUITE_CPU_BUDGET_S):
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
    sesji nie przechodzi dziś ANI JEDNEGO: stosunek 0,991 leży pod podłogą 1,168,
    a maszyna nie jest maszyną progu. **Zdanie jest przepisane, a nie dopisane obok
    (6.D247):** do 16.09.2026 stało tu, że kontener przechodzi pierwszy warunek
    „wysoko nad podłogą 0,75", i po podwyżce jest to nieprawda. Rozdzielenie warunków
    z 6.D149 zostaje nietknięte — zmieniła się wyłącznie odpowiedź, jaką pierwszy
    z nich daje na jednym przykładzie. Do 6.D149 była to jedna rzecz i pomiar
    kontenera dostawał odpowiedź progu, który jego nie dotyczy.

    **CO JEST PORÓWNYWANE Z PROGIEM — przepisane, a nie dopisane obok.** Do tej
    pozycji odrzucenie liczyło się z czasu ŚCIANY. Zmierzone na 265 artefaktach
    `czas-zestawu` z 10-14.09.2026: na drzewie o tej samej liczbie testów i modułów
    ściana rozjeżdża się o `x1,412`, a czas CPU o `x1,239` — i trzy jedyne przebiegi,
    które w tym oknie przekroczyły próg 150 s, mają TRZY NAJNIŻSZE stosunki CPU/ściana
    z całych 265 (1,375, 1,403, 1,471 wobec mediany 1,765). Były to więc przebiegi,
    w których maszyna oddała mniej rdzeni, a nie przebiegi, w których zestaw zaczął
    liczyć więcej. Werdykt odrzuca od tej pozycji na `SUITE_CPU_BUDGET_S`;
    `SUITE_RUNTIME_BUDGET_S` zostaje jako SUFIT INFORMACYJNY i wchodzi do komunikatu.

    **Podłoga mierzalności ZOSTAJE i to nie jest ozdoba** — ale jej powód się zwęził.
    Broniła czasu ściany przed maszyną, która nie oddaje CPU; czas CPU tej obrony
    potrzebuje w dużo mniejszym stopniu (dlatego ta pozycja w ogóle powstała), a przy
    stosunku poniżej podłogi nie mówi o kodzie ani jedno, ani drugie. Liczba podłogi
    stoi w `MIERZALNOSC_MIN` i od 6.D247 wynosi **1,168**, nie 0,75 — wypisana tu
    z ręki rozjeżdżałaby się przy każdej jej zmianie, i właśnie dlatego jej tu nie ma.

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
    if over_budget(cpu_s, cpu_budget_s):
        return True, (
            f"zestaw test_all.py przekroczyl prog czasu CPU: {cpu_s:.3f} s "
            f"> {cpu_budget_s} s (czas sciany {elapsed_s:.3f} s, stosunek CPU/sciana "
            f"{stosunek:.3f}) — czas CPU nie zalezy od tego, ile rdzeni maszyna "
            "akurat oddala, wiec to jest pomiar kodu")
    if over_budget(elapsed_s, budget_s):
        return False, (
            f"czas CPU {cpu_s:.3f} s jest w progu {cpu_budget_s} s, a czas sciany "
            f"{elapsed_s:.3f} s przekroczyl SUFIT INFORMACYJNY {budget_s} s przy "
            f"stosunku CPU/sciana {stosunek:.3f} — praca zestawu sie nie zmienila, "
            "zmienila sie maszyna; werdykt liczy sie z czasu CPU")
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


def test_kontener_przekroczylby_prog_a_od_6D247_zatrzymuje_go_PODLOGA():
    """**Sedno 6.D135, wykonane jako rachunek. Od 6.D149 ma DRUGA polowe, od 6.D247 TRZECIA.**

    **Nazwa jest PRZEPISANA 16.09.2026, bo przestała być prawdziwa.** Do tego dnia
    brzmiała `…_podloga_by_go_NIE_zatrzymala` i opisywała stan, w którym kontener
    (0,987) leżał nad podłogą 0,75. Podłoga poszła na 1,168 i zatrzymuje go dziś jako
    pierwsza — wynik ten sam, POWÓD inny.

    Podłoga mierzalności (6.D42) powstała po to, żeby czas maszyny OBCIĄŻONEJ nie był
    porównywany z progiem — zmierzone wtedy stosunki to 0,451 i 0,444 pod obciążeniem
    wobec 0,987 na spokojnym kontenerze. Kontener SPOKOJNY leży więc wysoko **nad**
    podłogą i podłoga go nie dotyczy — a jego czas ściany urósł od tamtego dnia na tyle,
    że dziś przekracza próg.

    Bramka na tym nie cierpi, bo chodzi WYŁĄCZNIE na runnerze. Cierpiałaby LISTA, gdyby
    jednym progiem opisywać obie maszyny — i to jest powód, dla którego `MEASURED_MAX_WALL_S`
    bierze dziś tylko `POMIARY_RUNNERA`.
    """
    # **PRZEPISANE 16.09.2026 (6.D247), a nie dopisane obok, i odwraca się tu ZNAK.**
    # Do tego dnia stało tu `stosunek > MIERZALNOSC_MIN` z komunikatem „kontener spadł
    # poniżej podłogi — wtedy teza tego testu przestaje być prawdziwa”. Podłoga
    # poszła 0,75 → 1,168 i kontener **jest dziś pod nią** — czyli to, co tamten
    # komunikat zapowiadał jako powrót do przemyślenia, właśnie się stało
    # i zostało przemyślane: podłoga przejęła rolę, którą miał wyłącznie warunek
    # maszyny — a ten w CI **nie wykonuje się ani razu** (krok woła `werdykt`
    # z dwoma argumentami, więc `maszyna` zostaje domyślna).
    #
    # WYNIK dla kontenera jest ten sam co przedtem — nieodrzucony — zmienił się
    # POWÓD, i to jest cała treść tej zmiany.
    stosunek = KONTENER_11_09_CPU / KONTENER_11_09_SCIANA
    assert stosunek < MIERZALNOSC_MIN, (
        "kontener (%.3f) wrócił nad podłogę %.3f — wtedy o jego nieodrzuceniu znowu "
        "decyduje WYŁĄCZNIE warunek maszyny, który w CI jest gałęzią martwą"
        % (stosunek, MIERZALNOSC_MIN))

    # Polowa PIERWSZA (6.D135), PRZEPISANA razem z progiem, a nie dopisana obok.
    # Do tej pozycji brzmiala: „z maszyna nienazwana pomiar kontenera dostaje odpowiedz
    # progu i ZOSTAJE ODRZUCONY". Na progu ze SCIANY to byla prawda i nadal nia jest —
    # `over_budget` ponizej wykonuje tamten rachunek. Na progu z CPU juz nie: kontener
    # liczy te sama prace szeregowo, wiec jego CPU (169,185 s) stoi glęboko w progu
    # 440 s, mimo ze jego SCIANA (170,685 s) sufit 150 s przekracza.
    #
    # To jest drugi, niezalezny powod, dla ktorego prog na CPU jest lepszy od progu na
    # scianie, i dlatego stoi tu jako rachunek: warunek maszyny z 6.D149 przestaje byc
    # JEDYNA rzecza, ktora dzieli ten pomiar od falszywej czerwieni.
    assert over_budget(KONTENER_11_09_SCIANA, SUITE_RUNTIME_BUDGET_S) is True, (
        "sciana kontenera (%.3f s) przestala przekraczac sufit %.1f s — wtedy caly ten "
        "test opisuje nieistniejaca sytuacje"
        % (KONTENER_11_09_SCIANA, SUITE_RUNTIME_BUDGET_S))
    odrzucony, komunikat = werdykt(KONTENER_11_09_SCIANA, KONTENER_11_09_CPU)
    assert odrzucony is False, (
        "pomiar kontenera zostal odrzucony (CPU %.3f s przy progu %.1f s): %s"
        % (KONTENER_11_09_CPU, SUITE_CPU_BUDGET_S, komunikat))
    # **Komunikat jest dziś INNY i to jest zmierzone, nie założone:** przed 6.D247
    # pomiar dochodził do porównania i słyszał o sufićie informacyjnym; dziś
    # zatrzymuje go podłoga i słyszy, że nie mówi o kodzie.
    assert "NIE JEST porownywany" in komunikat, komunikat

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
    # Mnożnik 1,599 to najniższy stosunek CPU/ściana zapisany w `POMIARY_RUNNERA`,
    # czyli liczba z pomiaru, a nie dobrana — i leży nad podłogą 1,168.
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
    # **Para (ściana, CPU) PRZEPISANA 16.09.2026 (6.D247), a nie dobrana na nowo.**
    # Do tego dnia stało tu `werdykt(prog+10, prog+10)`, czyli stosunek **1,000** —
    # nad starą podłogą 0,75, więc pomiar dochodził do warunku maszyny. Po podniesieniu
    # podłogi do 1,168 zatrzymywałaby go PIERWSZA gałąź i test mierzyłby podłogę
    # zamiast maszyny — czyli nie to, o czym mówi jego nazwa. Ściana jest więc dzielona
    # przez 1,6, mnożnik z **pomiaru** (`POMIARY_RUNNERA` niesie stosunki 1,599–1,971).
    cpu_ponad = SUITE_CPU_BUDGET_S + 10.0
    sciana_w_pasmie = cpu_ponad / 1.6
    for maszyna in MASZYNY:
        odrzucony, komunikat = werdykt(sciana_w_pasmie, cpu_ponad, maszyna=maszyna)
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

#: Koszt KRANCOWY jednego logu joba w historii repozytorium, w bajtach — 6.D205.
#:
#: Zmierzone 14.09.2026: dwanascie pustych repozytoriow, logi dokladane po jednym,
#: `git gc --aggressive --prune=now` po kazdym, mierzony katalog `objects/pack`.
#: Pierwszy log 73 374 B, kazdy nastepny 30 143 - 35 014 B; osmy 33 188, dziewiaty
#: 30 143. Ponizej stoi NAJNIZSZY zmierzony, zeby liczba byla podloga tego, co
#: wychodzi z pomiaru, a nie jego srodkiem.
#:
#: **Wartosc jest tu po to, zeby uzasadnienie reguly doboru nie zestarzalo sie w ciszy.**
#: Rozmiar pliku w katalogu roboczym to ok. 287 000 B, czyli DZIEWIEC RAZY wiecej;
#: kto siegnie po te druga liczbe, policzy koszt historii dziewieciokrotnie za wysoko
#: i odrzuci regule z powodu, ktorego nie ma. Tak wlasnie liczyl ten katalog do 6.D152,
#: gdy trzymal logi spakowane gzipem.
KOSZT_KRANCOWY_LOGU_B = 30143

#: Zdania reguly doboru, ktore ta bramka CYTUJE z `tests/data/ci-logs/README.md`.
#: Reguly nie da sie sprawdzic wykonaniem — mowi o przebiegach, ktorych w drzewie
#: NIE MA, a zestaw do GitHuba nie siega. Cytat jest wiec tym, na co pozwala pole
#: „Weryfikacja" 6.D205: „albo bramka, albo zdanie, ktore bramka cytuje".
ZDANIA_REGULY_DOBORU = (
    "Obowiązkowo wchodzi przebieg runnera, który ustanawia CO NAJMNIEJ JEDNO z trzech",
    "nowe maksimum ściany",
    "maszynę, której lista jeszcze nie zna",
    "nowy skrajny stosunek CPU/ściana",
    "Każdy inny przebieg wolno dopisać i żadnego nie trzeba",
)


def test_regula_doboru_przebiegow_stoi_w_drzewie_RAZEM_ze_swoimi_liczbami():
    """Pole „Wyjscie" 6.D205 zada reguly ZAPISANEJ, a nie rozstrzygnietej w raporcie.

    Bramka sprawdza trzy rzeczy, i kazda z nich psuje sie inaczej:

    1. **zdania reguly stoja** — bez tego regula znika przy pierwszym przepisaniu
       README i nikt tego nie zobaczy;
    2. **nazwy testow, na ktore regula sie powoluje, ISTNIEJA w tym module** — regula
       uzasadnia dwa ze swoich trzech punktow konkretnymi bramkami, wiec po zmianie
       nazwy wskazywalaby na nic;
    3. **liczba kosztu w README zgadza sie z `KOSZT_KRANCOWY_LOGU_B`** — czyli
       uzasadnienie reguly i stala mowia to samo, a nie dwie rzeczy (6.D26).
    """
    sciezka = os.path.join(ROOT, "tests", "data", "ci-logs", "README.md")
    with open(sciezka, encoding="utf-8") as uchwyt:
        readme = uchwyt.read()

    for zdanie in ZDANIA_REGULY_DOBORU:
        assert zdanie in readme, (
            "regula doboru przebiegow nie stoi juz w `tests/data/ci-logs/README.md` — "
            "brakuje zdania %r; lista wpisow runnera rosnie wtedy tak, jak rosla "
            "do 6.D205, czyli przypadkiem" % zdanie)

    wlasny = globals()
    for nazwa in ("test_slowo_runner_stoi_nad_DWIEMA_maszynami_ale_ich_NIE_rozdziela",
                  "test_runner_liczy_rownolegle_a_kontener_szeregowo"):
        assert nazwa in readme, (
            "regula przestala powolywac sie na `%s` — punkt, ktory ta bramka "
            "uzasadniala, stoi wtedy bez powodu" % nazwa)
        assert callable(wlasny.get(nazwa)), (
            "regula w README powoluje sie na `%s`, a takiej bramki w tym module NIE MA "
            "— cytat wskazuje na nic" % nazwa)

    # Separator tysiecy czytany JAKIMKOLWIEK odstepem, bo README pisze „30 143",
    # a spacja nierozdzielajaca i zwykla wygladaja tak samo i roznia sie bajtem.
    cyfry = str(KOSZT_KRANCOWY_LOGU_B)
    wzorzec = re.compile(cyfry[:-3] + r"\s*" + cyfry[-3:])
    assert wzorzec.search(readme), (
        "README nie podaje juz kosztu krancowego %s B, a `KOSZT_KRANCOWY_LOGU_B` "
        "stoi na tej liczbie — uzasadnienie reguly i stala rozjechaly sie" % cyfry)

    # KONTROLA PRZYRZADU: bez niej wszystkie asercje wyzej przechodza tak samo dobrze
    # na pliku PUSTYM, jak na pelnym (6.D27).
    assert len(readme) > 3000, (
        "README logow ma %d znakow — czytnik dostal cos innego niz ten plik"
        % len(readme))


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
    # **PRZEPISANE 16.09.2026 (6.D247), a nie dopisane obok.** Do tego dnia stało tu
    # `min(stosunki) > MIERZALNOSC_MIN` z komunikatem „ten przebieg mówi o maszynie,
    # nie o kodzie” — przy podłodze 0,75 kontener (0,987) leżał nad nią i asercja
    # była spełniona. Po 0,75 → 1,168 leży pod nią, a **rozstrzygnięcie 6.D160 stoi
    # dalej i nie zależy od podłogi**: sześć powtórzeń mierzy ten sam kod na tej samej
    # maszynie, więc ich rozrzut mówi o kodzie bez względu na to, czy ta maszyna jest
    # porównywalna z progiem RUNNERA. Podłoga odpowiada na pytanie „czy ten pomiar
    # wolno postawić obok progu”, a nie „czy te sześć liczb można porównać ze sobą”.
    #
    # Pytanie jest więc przepisane na to, o które tu naprawdę chodzi: że sześć
    # powtórzeń mierzyło maszynę w JEDNYM stanie, a nie raz obciążoną i raz spokojną.
    rozrzut_stosunkow = max(stosunki) / min(stosunki)
    assert rozrzut_stosunkow < 1.05, (
        "stosunki CPU/ściana szesciu powtorzen rozjezdzaja sie o %.4f (%.3f–%.3f) — "
        "maszyna byla w ROZNYCH stanach, wiec rozrzut scian nie mowi juz o kodzie"
        % (rozrzut_stosunkow, min(stosunki), max(stosunki)))
    assert max(stosunki) < MIERZALNOSC_MIN, (
        "powtorzenie ze stosunkiem %.3f wrocilo nad podloge %.3f — kontener przestal "
        "byc maszyna SZEREGOWA, a caly rachunek 6.D160 opisuje maszyne szeregowa"
        % (max(stosunki), MIERZALNOSC_MIN))


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

    # 2. Prawdziwe spowolnienie KODU: maszyna oddaje CPU, czas CPU ponad progiem.
    #    Liczba przepisana razem z progiem: do tej pozycji odrzucała ściana 200 s,
    #    dziś odrzuca CPU powyżej `SUITE_CPU_BUDGET_S`, a 200 s CPU stoi w progu.
    odrzuc, komunikat = werdykt(300.0, SUITE_CPU_BUDGET_S + 1.0)
    assert odrzuc is True, komunikat
    assert "przekroczyl prog" in komunikat, komunikat

    # 3. Zmierzone przebiegi RUNNERA w progu. **Lista przepisana 16.09.2026 (6.D247),
    #    a nie skrócona po cichu:** stała tu obok para spokojnego kontenera
    #    `(91.742, 90.522)`, stosunek **0,987**. Przy podłodze 0,75 dochodziła do
    #    porównania i słyszała „w progu”; przy 1,168 zatrzymuje ją podłoga — bo
    #    maszyna oddająca jeden rdzeń nie jest tą, którą próg opisuje. Para nie znika
    #    z testu: przenosi się niżej, do punktu 4, jako asercja na NOWE zachowanie.
    for sciana, cpu in ((53.517, 70.804), (121.671, 203.091)):
        odrzuc, komunikat = werdykt(sciana, cpu)
        assert odrzuc is False, komunikat
        assert "w progu" in komunikat, komunikat

    # 4. Strona czwarta, dopisana przy 6.D247: maszyna SZEREGOWA, przebieg zdrowy
    #    i głęboko w progu — a mimo to NIE porównywany, bo próg jej nie opisuje.
    #    To jest dokładnie ta cisza, którą wariant (d) kupuje w zamian za fałszywy
    #    alarm, i dlatego stoi tu jako asercja, a nie jako zdanie w komentarzu.
    odrzuc, komunikat = werdykt(91.742, 90.522)
    assert odrzuc is False, komunikat
    assert "NIE JEST porownywany" in komunikat, komunikat
    assert "w progu" not in komunikat, komunikat


def test_podloga_mierzalnosci_lezy_miedzy_zmierzonymi_stanami_maszyny():
    """Podłoga ma rozdzielać POMIARY, nie być okrągłą liczbą.

    Kontrola na obu brzegach: musi leżeć pod najniższym zmierzonym przebiegiem bez
    obciążenia i nad najwyższym pod obciążeniem. Wartości są tu wpisane jako dane
    pomiaru — ich źródłem jest `reports/mierzalnosc-czasu-zestawu.md`.
    """
    # **Brzegi PRZEPISANE, a nie dopisane obok — 6.D247, 16.09.2026.** Do tego dnia
    # podłoga rozdzielała maszynę OBCIĄŻONĄ od SPOKOJNEJ (0,451 wobec 0,987) i robiła
    # to poprawnie. Przestało wystarczać: pula wykonująca joby przestała być tą,
    # na której próg skalibrowano, a maszyna spokojna oddająca JEDEN rdzeń (0,992)
    # jest od maszyny kalibracyjnej (1,375 i wyżej) nieodróżnialna starą podłogą.
    # Brzegami są więc dziś PASMA KALIBRACJI, a nie stany obciążenia.
    w_pasmie_kalibracji = (1.375, 1.599, 1.695, 1.971)
    poza_pasmem = (0.451, 0.444, 0.987, 0.988, 0.992)
    assert MIERZALNOSC_MIN < min(w_pasmie_kalibracji), (
        f"podłoga {MIERZALNOSC_MIN} jest nad najniższym przebiegiem KALIBRACYJNYM "
        f"{min(w_pasmie_kalibracji)} — bramka pomijałaby porównanie na maszynie, "
        "którą próg opisuje, czyli milczałaby zawsze")
    assert MIERZALNOSC_MIN > max(poza_pasmem), (
        f"podłoga {MIERZALNOSC_MIN} jest pod najwyższym przebiegiem SPOZA pasma "
        f"{max(poza_pasmem)} — bramka porównywałaby z progiem maszynę, której "
        "ten próg nie opisuje, i to jest usterka, którą 6.D247 domyka")
    # Zapas po obu stronach, wypisany liczbą, żeby następna maszyna puli była widoczna.
    assert min(w_pasmie_kalibracji) / MIERZALNOSC_MIN > 1.17, (
        "zapas nad podłogą do najniższego przebiegu kalibracyjnego zszedł poniżej 17 %% "
        "(%.4f) — podłoga zaczyna dotykać maszyny, którą ma przepuszczać"
        % (min(w_pasmie_kalibracji) / MIERZALNOSC_MIN))


def _tekst_kroku_werdyktu():
    """Treść kroku CI „Run tool tests" — JEDEN czytnik, nie dwie kopie (6.D213).

    Wydzielone przy 6.D247, bo to samo wycięcie robiły odtąd dwa testy.

    **Asercja na JEDNOKROTNOŚĆ nazwy stoi tu, a nie w teście, i to jest wybór.**
    Wersja pierwsza brała `text.index(...)`, czyli **pierwsze** wystąpienie — a krok
    o nazwie zawierającej tę frazę wystarczy postawić wyżej, żeby czytnik oddawał
    jego treść zamiast treści kroku bramkującego. Zmierzone podstawieniem 16.09.2026:
    krok-atrapa `Sonda Run tool tests` przed krokiem prawdziwym, a w prawdziwym
    `B.werdykt(maszyna=os.environ.get('RUNNER_NAME',''), …)` — czyli dokładnie to,
    czego `test_krok_CI_NIE_podaje_nazwy_maszyny…` zabrania — dało **34/37**, a ta
    bramka była wśród zielonych. Trzy czerwienie pochodziły od starszych sąsiadek
    i trafiły przypadkiem, bo one czytają krok po swojemu.

    Asercja jest w CZYTNIKU, bo inaczej każdy jego użytkownik musiałby ją powtórzyć —
    a to jest ta sama druga kopia, przed którą broni 6.D213.
    """
    text = _workflow_text()
    ile = text.count("Run tool tests")
    assert ile == 1, (
        "fraza „Run tool tests” stoi w `%s` %d razy, a czytnik bierze PIERWSZE "
        "wystąpienie — drugi krok o takiej nazwie przesłania krok bramkujący "
        "i wszystkie bramki czytające go przez ten czytnik robią się zielone "
        "nad krokiem, którego nie oglądają" % (WORKFLOW, ile))
    start = text.index("Run tool tests")
    return text[start:text.index("\n      - name:", start)]


def test_krok_ci_liczy_werdykt_modulem_a_nie_wlasnym_porownaniem():
    """Krok ma wołać `werdykt`, a nie porównywać liczby po swojemu.

    Druga kopia warunku rozjechałaby się z modułem przy pierwszej zmianie podłogi —
    ta sama rodzina, co `test_ci_gate_step_reads_this_files_constant_not_a_second_copy`.
    """
    step = _tekst_kroku_werdyktu()
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
#:
#: **ILU ZAPISÓW TA GRANICA DOTYCZY — dopisane 14.09.2026 (6.D206), a nie przepisane,
#: bo zdanie wyżej jest nadal prawdziwe; brakowało mu skali.** Kontenerów, których `#:`
#: deklaruje pomiar z datą, jest w drzewie **29**, a datę ISO w literale niesie
#: z nich **JEDEN** — `POMIARY`. `POMIARY_BRAKOW` nie jest więc wyjątkiem; wyjątkiem
#: jest `POMIARY`. Granica nie jest szczeliną w sicie, tylko kształtem całego sita,
#: i dlatego bramki z niej NIE MA: zapalałaby się na dziewięćdziesięciu stałych
#: napisanych poprawnie. Liczby i rozstrzygnięcie: sekcja 6.D206 na końcu tego modułu.
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


# --- 6.D206: ILU ZAPISOW POMIARU DOTYCZY GRANICA Z 6.D193 ---------------------------
#
# **Odpowiedz: prawie wszystkich. Granica nie jest szczelina w sicie — jest sitem.**
#
# 6.D193 zapisalo, ze kryterium daty w literale nie widzi `POMIARY_BRAKOW`, bo tamta
# data stoi w komentarzu `#:` i w notacji polskiej. Pozycja 6.D206 pytala, ILU zapisow
# ta granica dotyczy — „jeden przypadek jest anegdota". Zmierzone 14.09.2026 na `71db020`:
#
#     stalych modulowych pod `tools/` o nazwie WIELKIMI        1191
#     z nich z komentarzem `#:`                                 555
#     z nich `#:` mowi „zmierzone"/„zmierzono"                  119
#     z nich komentarz niesie TAKZE date                         91
#     z tych 91 literal NIE niesie daty ISO                      89
#     z tych 91 to KONTENERY (jedyne, ktorym ksztalt przysluguje) 29
#     z tych 29 literal NIE niesie daty ISO                      28
#
# **Po TYM commicie szeroka liczba wynosi 92, i to nie jest usterka pomiaru — to jest
# pomiar, ktory zmienil sie przez to, ze zostal zapisany.** Komentarz `#:` nad
# `MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU` nizej sam deklaruje pomiar z data, wiec wchodzi
# do populacji, ktora opisuje. Ta sama mechanika co `ADRESOW_W_WYKONANYCH` z 6.D158,
# gdzie domkniecie pozycji przenosi jej wlasny blok do zbioru mierzonego.
#
# **Liczba, na ktorej stoi rozstrzygniecie, NIE drgnela:** kontenerow jest nadal 29,
# bo obie nowe stale sa skalarami. Samozwrotnosc przesunela populacje szeroka i nie
# ruszyla waskiej — a wyrok zapada na waskiej.
#
# **`POMIARY_BRAKOW` nie jest wyjatkiem — wyjatkiem jest `POMIARY`.** Kontener,
# ktorego `#:` deklaruje pomiar z data i ktory te date ma takze w literale, jest
# w calym drzewie **jeden**. Drugi zapis z data ISO w literale to
# `DZIEN_PIERWSZEGO_WYNOSZENIA`, ktory kontenerem nie jest: jest sama data.
#
# **ROZSTRZYGNIECIE: granica ZOSTAJE granica i bramki z niej NIE ROBIE.** Bramka
# „komentarz deklaruje pomiar, a literal daty nie niesie" zapalalaby sie na 89 stalych
# napisanych poprawnie — prog, ratchet i tablica przypadkow nie maja gdzie nosic daty
# i nosic jej nie powinny. Bramka swiecaca na poprawnym tekscie zostaje wylaczona,
# nie poprawiona (6.D27), wiec jej tu nie ma.
#
# **Pilnowane jest co innego i to sie da pilnowac:** ZBIOR stalych, ktore date ISO
# w literale niosa. Zbior, a nie liczba (6.D131) — liczba 91 rosnie przy kazdej nowej
# stalej z datowanym komentarzem, czyli przy poprawnej pracy, a zbior dwoch nazw zmienia
# sie tylko wtedy, gdy ktos nowy przyjmie ksztalt `POMIARY` albo gdy `POMIARY` go porzuci.

#: Stale pod `tools/`, ktorych `#:` deklaruje pomiar Z DATA, a literal date ISO NIESIE.
#: Zbior, nie liczba — patrz akapit wyzej. Wartoscia jest modul i powod.
Z_DATA_ISO_W_LITERALE = {
    "POMIARY": (
        "tools/tests/test_suite_runtime_budget.py",
        "lista pomiarow czasu zestawu; data jest PIERWSZYM polem kazdej krotki"),
    "DZIEN_PIERWSZEGO_WYNOSZENIA": (
        "tools/tests/test_timing_record.py",
        "skalar, ktory JEST data — kontenerem nie jest, wiec ksztalt mu nie przysluguje"),
}

#: Podlogi na obie populacje. PODLOGI, nie rownosci: obie rosna przy kazdej nowej stalej
#: z datowanym komentarzem, czyli przy pracy poprawnej. Bronia przed jedna rzecza —
#: skanem, ktory oslepl i odpowiada zerem tak samo jak skan widzacy (6.D27). Zmierzone
#: 14.09.2026: 91 i 29 PRZED tym commitem, 92 i 29 po nim — roznica to ten komentarz,
#: patrz akapit o samozwrotnosci wyzej.
MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU = 80
MIN_KONTENEROW_Z_POMIAREM_W_KOMENTARZU = 25

_DATA_PL = re.compile(r"\b\d{1,2}\.\d{2}\.\d{4}\b")
_DEKLARACJA_POMIARU = re.compile(r"[Zz]mierzon[eoy]|[Zz]mierzono")


def _komentarz_hash_dwukropek(linie, wiersz):
    """Blok `#:` stojacy BEZPOSREDNIO nad wierszem `wiersz` (1-based), sklejony."""
    out = []
    i = wiersz - 2
    while i >= 0 and linie[i].lstrip().startswith("#:"):
        out.append(linie[i].lstrip()[2:].strip())
        i -= 1
    return "\n".join(reversed(out))


def stale_z_pomiarem_w_komentarzu_w_zrodle(zrodlo, sciezka="<pamiec>"):
    """`[(plik, wiersz, nazwa, kontener, data_w_literale)]` dla JEDNEGO zrodla.

    Wydzielone ze skanu drzewa, zeby dalo sie podac przyrzadowi wejscie syntetyczne —
    pole „Weryfikacja" 6.D206 zada kontroli negatywnej pokazujacej, ze stala z data
    dopisana do komentarza WCHODZI do tej liczby, a takiej kontroli nie da sie zrobic
    na drzewie bez zmieniania cudzego modulu.
    """
    import ast

    nazwa_stalej = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
    linie = zrodlo.split("\n")
    try:
        drzewo = ast.parse(zrodlo)
    except SyntaxError:
        return []
    out = []
    for wezel in drzewo.body:
        if not isinstance(wezel, ast.Assign):
            continue
        for cel in wezel.targets:
            nazwa = getattr(cel, "id", None)
            if not nazwa or not nazwa_stalej.match(nazwa):
                continue
            komentarz = _komentarz_hash_dwukropek(linie, wezel.lineno)
            if not komentarz or not _DEKLARACJA_POMIARU.search(komentarz):
                continue
            if not (_DATA_PL.search(komentarz) or _DATA_ISO.search(komentarz)):
                continue
            out.append((
                sciezka, wezel.lineno, nazwa,
                isinstance(wezel.value, (ast.Tuple, ast.List, ast.Dict)),
                bool(_DATA_ISO.search(ast.unparse(wezel.value)))))
    return out


def stale_z_pomiarem_w_komentarzu():
    """To samo przez cale `tools/`, przez `tree_walk.walk` — jak `stale_z_data_iso`."""
    import tree_walk as tw

    out = []
    for baza, _kat, pliki in tw.walk(os.path.join(ROOT, "tools")):
        for plik in sorted(pliki):
            if not plik.endswith(".py"):
                continue
            sciezka = os.path.join(baza, plik)
            with open(sciezka, encoding="utf-8", errors="replace") as uchwyt:
                out.extend(stale_z_pomiarem_w_komentarzu_w_zrodle(
                    uchwyt.read(), os.path.relpath(sciezka, ROOT)))
    return out


def test_przyrzad_6D206_WIDZI_date_dopisana_do_komentarza():
    """Kontrola PRZYRZADU na wejsciu syntetycznym, zadana wprost przez pole „Weryfikacja".

    Bez niej liczba 91 znaczylaby tyle, co skan, ktory ja wypisal: przyrzad niewidzacy
    daty w notacji polskiej odpowiedzialby mniejsza liczba i nic by tego nie zdradzilo.
    Cztery probki roznia sie od siebie DOKLADNIE JEDNA rzecza naraz.
    """
    bez_daty = '#: Zmierzone na drzewie.\nPROBKA_JEDEN = (1, 2)\n'
    z_data_pl = '#: Zmierzone 10.09.2026 na `a202423`.\nPROBKA_DWA = (1, 2)\n'
    z_data_iso = '#: Zmierzone 2026-09-10 na `a202423`.\nPROBKA_TRZY = (1, 2)\n'
    bez_pomiaru = '#: Lista rzeczy z 10.09.2026.\nPROBKA_CZTERY = (1, 2)\n'

    assert stale_z_pomiarem_w_komentarzu_w_zrodle(bez_daty) == [], (
        "komentarz mowi o pomiarze, ale daty nie niesie — nie jest datowanym zapisem "
        "pomiaru i do tej liczby wchodzic nie ma")
    assert stale_z_pomiarem_w_komentarzu_w_zrodle(bez_pomiaru) == [], (
        "komentarz niesie date, ale pomiaru nie deklaruje — sito po samej dacie "
        "zglaszaloby kazda liste z data w prozie")

    for zrodlo, etykieta in ((z_data_pl, "polskiej"), (z_data_iso, "ISO")):
        trafienia = stale_z_pomiarem_w_komentarzu_w_zrodle(zrodlo)
        assert len(trafienia) == 1, (
            "data w notacji %s dopisana do komentarza NIE weszla do liczby — przyrzad "
            "jej nie widzi, wiec kazda liczba, ktora poda, jest zanizona: %s"
            % (etykieta, trafienia))
        _p, _w, nazwa, kontener, w_literale = trafienia[0]
        assert kontener is True and w_literale is False, (nazwa, kontener, w_literale)

    # I DRUGA STRONA: literal Z data ISO ma byc rozpoznany jako niosacy date, inaczej
    # zbior `Z_DATA_ISO_W_LITERALE` bylby pusty z powodu przyrzadu, a nie drzewa.
    z_literalem = ('#: Zmierzone 10.09.2026.\n'
                   'PROBKA_PIEC = (("2026-09-10", 1.0),)\n')
    trafienia = stale_z_pomiarem_w_komentarzu_w_zrodle(z_literalem)
    assert [t[4] for t in trafienia] == [True], (
        "literal z data ISO nie zostal rozpoznany jako niosacy date: %s" % (trafienia,))


def test_ile_zapisow_pomiaru_niesie_date_WYLACZNIE_w_prozie():
    """Pole „Skonczone, gdy" 6.D206 zada liczby ZE ZRODEL — i ona rozstrzyga pozycje.

    Kryterium daty w literale widzi **jeden kontener na 29**. Granica z 6.D193 nie jest
    wiec szczelina, tylko ksztaltem calego sita — i dlatego zostaje ZAPISANA, a bramki
    z niej nie ma: zapalalaby sie na 89 stalych napisanych poprawnie.
    """
    import ast

    znalezione = stale_z_pomiarem_w_komentarzu()
    kontenery = [t for t in znalezione if t[3]]

    assert len(znalezione) >= MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU, (
        "stalych z datowana deklaracja pomiaru w `#:` jest %d przy podlodze %d — skan "
        "oslepl albo drzewo sie skurczylo, a zero odpowiada tak samo jak skan widzacy"
        % (len(znalezione), MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU))
    assert len(kontenery) >= MIN_KONTENEROW_Z_POMIAREM_W_KOMENTARZU, (
        "kontenerow wsrod nich jest %d przy podlodze %d" % (
            len(kontenery), MIN_KONTENEROW_Z_POMIAREM_W_KOMENTARZU))

    # ZBIOR, nie liczba: to on rozstrzyga, czy granica nadal opisuje drzewo.
    z_data = {nazwa for _p, _w, nazwa, _k, w_literale in znalezione if w_literale}
    assert z_data == set(Z_DATA_ISO_W_LITERALE), (
        "stale z data ISO w literale to dzis %s, a wymienione sa %s — ktos przyjal "
        "ksztalt `POMIARY` albo `POMIARY` go porzucil; jedno i drugie zmienia "
        "rozstrzygniecie 6.D206 i ma byc widoczne"
        % (sorted(z_data), sorted(Z_DATA_ISO_W_LITERALE)))

    # I DRUGA STRONA, na wzor `STALE_BEZ_DATY_W_LITERALE`: kazda wymieniona stala ma
    # w podanym module NAPRAWDE stac. Licznik obrotow, bo pusta petla przechodzi.
    sprawdzonych = 0
    for nazwa, (modul, powod) in sorted(Z_DATA_ISO_W_LITERALE.items()):
        wezel = _stala_w_module(os.path.join(ROOT, modul), nazwa)
        assert wezel is not None, (
            "`%s` nie stoi juz w `%s`" % (nazwa, modul))
        assert _DATA_ISO.search(ast.unparse(wezel)), (nazwa, modul)
        assert len(powod) > 40, (nazwa, powod)
        sprawdzonych += 1
    assert sprawdzonych == len(Z_DATA_ISO_W_LITERALE), sprawdzonych

    # `POMIARY_BRAKOW` — stala, od ktorej pozycja wyszla — ma byc w tej populacji
    # i ma NIE miec daty w literale. To jest zdanie 6.D193 sprawdzone, a nie powtorzone.
    nazwy = {t[2] for t in znalezione}
    assert "POMIARY_BRAKOW" in nazwy, (
        "`POMIARY_BRAKOW` wypadlo z populacji datowanych zapisow pomiaru — pozycja "
        "6.D206 wyszla wlasnie od niego")
    assert "POMIARY_BRAKOW" not in z_data, (
        "`POMIARY_BRAKOW` niesie dzis date ISO w literale — granica z 6.D193 mowila, "
        "ze nie niesie")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))


# --- PRÓG NA CZASIE CPU: bramki na tę zmianę ----------------------------------------


def test_prog_cpu_stoi_nad_zmierzonym_maksimum_z_marginesem_reguly_6D11():
    """Ta sama kontrola, co `test_budget_stays_above_the_measured_maximum_with_a_real
    _margin`, tylko dla progu, który od tej pozycji ODRZUCA.

    Dwie liczby zamiast jednej, bo reguła 6.D11 miała dwa czytania i oba są zapisane:
    margines nad MAKSIMUM (1,947 = 150,0/77,04) i nad MEDIANĄ (2,183 = 150,0/68,705)
    przebiegów z dnia, w którym próg ustawiono. Próg 440 s ma leżeć pod OBOMA — czyli
    być ciaśniejszy niż tamten, a nie luźniejszy.
    """
    assert SUITE_CPU_BUDGET_S > MEASURED_MAX_CPU_S, (
        SUITE_CPU_BUDGET_S, MEASURED_MAX_CPU_S)
    assert MARGIN_CPU == SUITE_CPU_BUDGET_S / MEASURED_MAX_CPU_S, (
        "margines %.4f przestal byc ILORAZEM tych dwoch stalych — wtedy jest trzecia "
        "liczba wpisana z reki i rozjedzie sie z nimi po cichu (6.B28)" % MARGIN_CPU)
    nad_maksimum = 150.0 / 77.04
    nad_mediana = 150.0 / 68.705
    assert MARGIN_CPU < nad_maksimum, (
        "margines progu CPU (%.4f) jest LUŹNIEJSZY niż margines, z jakim 06.09.2026 "
        "ustawiono próg ściany nad maksimum tamtego dnia (%.4f)"
        % (MARGIN_CPU, nad_maksimum))
    assert SUITE_CPU_BUDGET_S / MEASURED_MED_CPU_S < nad_mediana, (
        "margines progu CPU nad medianą (%.4f) jest luźniejszy niż tamten (%.4f)"
        % (SUITE_CPU_BUDGET_S / MEASURED_MED_CPU_S, nad_mediana))
    # I żeby nie stopniał do czegoś ciasnego: musi unieść ZMIERZONY rozrzut CPU
    # na identycznym drzewie, i to z zapasem.
    _med, max_rozrzut = WZORZEC_ROZRZUTU["cpu"]
    assert MARGIN_CPU > max_rozrzut * 1.4, (
        "margines %.4f nie stoi 40 %% nad zmierzonym rozrzutem CPU %.4f — wtedy próg "
        "zaczyna mierzyć maszynę, dokładnie tak jak próg na ścianie"
        % (MARGIN_CPU, max_rozrzut))


def test_prog_cpu_NIE_zapalilby_sie_na_zadnym_zmierzonym_przebiegu():
    """Kontrola obustronna: cisza na materiale i głos na spowolnieniu.

    Sama pierwsza połowa byłaby prawdziwa także dla progu nieskończonego, więc druga
    jest tu warunkiem, a nie ozdobą — ta sama konstrukcja, co przy `MASZYNA_PROGU`.
    """
    for ident, sciana, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA:
        odrzuc, komunikat = werdykt(sciana, cpu)
        assert odrzuc is False, (ident, komunikat)
    # I ten sam materiał na STARYM progu: trzy z ośmiu... a dokładnie jeden, i to jest
    # cała pozycja — przebieg 10341963856 (164,734 s) był CZERWONY, a ten sam commit
    # w powtórzeniu 10344952688 (142,498 s) ZIELONY, przy czasach CPU 226,537
    # i 201,193 s. Bramka wykonuje ten rachunek, żeby nie był zdaniem w raporcie.
    czerwone_na_scianie = [i for i, w, _c in POMIARY_CPU_BIEZACEGO_DRZEWA
                           if over_budget(w, SUITE_RUNTIME_BUDGET_S)]
    assert czerwone_na_scianie == [10341963856], czerwone_na_scianie
    para = {i: (w, c) for i, w, c in POMIARY_CPU_BIEZACEGO_DRZEWA
            if i in (10341963856, 10344952688)}
    assert para[10341963856][0] / para[10344952688][0] > 1.15, para
    assert para[10341963856][1] / para[10344952688][1] < 1.15, para

    # DRUGA POŁOWA: prawdziwe spowolnienie nadal odrzucane. Punkt odniesienia to
    # najwyższy zmierzony przebieg — zestaw, który zaczyna liczyć o `MARGIN_CPU`
    # więcej, ma zapalić bramkę bez względu na to, jak szybka jest maszyna.
    for mnoznik, spodziewane in ((1.0, False), (MARGIN_CPU + 0.01, True)):
        cpu = MEASURED_MAX_CPU_S * mnoznik
        odrzuc, _k = werdykt(cpu / 1.6, cpu)
        assert odrzuc is spodziewane, (mnoznik, cpu, odrzuc)


def test_przekroczony_SUFIT_sciany_nie_jest_juz_werdyktem_ale_jest_w_logu():
    """Przebieg z incydentu 14.09.2026 (ściana 164,734 s, CPU 226,537 s).

    Ma przejść — i ma powiedzieć, CZEMU przeszedł, bo bramka, która milczy o pominiętym
    porównaniu, jest przyrządem meldującym sprawdzenie, którego nie zrobił (6.D27).
    """
    odrzuc, komunikat = werdykt(164.734, 226.537)
    assert odrzuc is False, komunikat
    assert "SUFIT INFORMACYJNY" in komunikat, komunikat
    assert "164.734" in komunikat and "226.537" in komunikat, komunikat
    assert "CPU/sciana" in komunikat, komunikat


def test_kazda_galaz_werdyktu_niesie_OBIE_liczby():
    """Cztery gałęzie, cztery komunikaty — i w każdym ma stać ściana ORAZ CPU.

    Komunikat z jedną liczbą zaprasza do porównywania przebiegów, których nie wolno
    porównać; to jest ta sama usterka, którą 6.D42 naprawiło wypisaniem stosunku.
    """
    przypadki = (
        (200.0, 80.0, MASZYNA_KONTENER, "inna maszyna"),
        (335.668, 70.8, MASZYNA_PROGU, "ponizej podlogi"),
        (300.0, SUITE_CPU_BUDGET_S + 1.0, MASZYNA_PROGU, "ponad progiem CPU"),
        (164.734, 226.537, MASZYNA_PROGU, "ponad sufitem sciany"),
        (128.564, 196.031, MASZYNA_PROGU, "w progu"),
    )
    for sciana, cpu, maszyna, opis in przypadki:
        _o, komunikat = werdykt(sciana, cpu, maszyna=maszyna)
        assert "CPU/sciana" in komunikat, (opis, komunikat)
        assert f"{sciana:.3f}" in komunikat, (opis, komunikat)


def test_krok_ci_czyta_prog_CPU_z_tego_pliku_a_nie_z_drugiej_kopii():
    """To samo, co `test_ci_gate_step_reads_this_files_constant_not_a_second_copy`,
    dla stałej, która od tej pozycji rozstrzyga."""
    text = _workflow_text()
    step_start = text.index("Run tool tests")
    step = text[step_start:text.index("\n      - name:", step_start)]
    assert "SUITE_CPU_BUDGET_S" in step, step
    assert not re.search(r"cpu_budget\s*=\s*[\"\']?\d", step), (
        "próg CPU wpisany do YAML-a jako goła liczba — druga kopia:\n" + step)


#: Przebieg, który wymusił rozstrzygnięcie 6.D247 — job `tools` na PR #633,
#: maszyna `docker-runner-02`, 16.09.2026. Zestaw przeszedł w całości
#: (`2497/2497 przeszło`, `RAZEM 518.283 s, 2498 testów, 127 modułów`), a job padł
#: na bramce budżetu: `czas CPU zestawu: 517.499 s (prog 440.0 s)`.
#:
#: Liczby stoją tu jako DANE POMIARU, nie jako próg: żaden rachunek ich nie używa,
#: a jedyna asercja pyta, co `werdykt` na nich mówi.
INCYDENT_DOCKER_SCIANA = 521.900
INCYDENT_DOCKER_CPU = 517.499


def test_incydent_z_docker_runnera_JEST_ODMOWIONY_a_nie_odrzucony():
    """Przebieg, od którego zaczęło się 6.D247, kończy się dziś ODMOWĄ — nie czerwienią.

    **To jest asercja na rozstrzygnięcie właściciela z 16.09.2026** (wariant „sufit
    mierzalności"), a nie na liczbę: pyta o ZNAK werdyktu na danych, które ten
    wariant miał obsłużyć. Bez niej podłoga 1,168 byłaby liczbą, o której nic nie
    wiadomo poza tym, że stoi w pliku.

    **Dwie strony, bo jedna nie wystarcza.** Sama odmowa na incydencie byłaby
    spełniona także przez podłogę ustawioną absurdalnie wysoko — taka bramka
    milczałaby zawsze i nikt by tego nie zauważył, bo kierunek błędu jest cichy.
    Druga strona pyta więc, czy WSZYSTKIE osiem przebiegów kalibracyjnych nadal
    dochodzi do porównania.
    """
    odrzuc, komunikat = werdykt(INCYDENT_DOCKER_SCIANA, INCYDENT_DOCKER_CPU)
    assert odrzuc is False, (
        "przebieg z `docker-runner-02` (CPU %.3f s, stosunek %.3f) nadal jest "
        "ODRZUCANY, czyli rozstrzygnięcie 6.D247 nie działa: %s"
        % (INCYDENT_DOCKER_CPU,
           INCYDENT_DOCKER_CPU / INCYDENT_DOCKER_SCIANA, komunikat))
    assert "NIE JEST porownywany" in komunikat, komunikat
    assert "przekroczyl prog" not in komunikat, komunikat

    # Strona druga: podłoga nie może uciszyć maszyny, którą próg OPISUJE.
    porownane = 0
    for _run, sciana, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA:
        _o, k = werdykt(sciana, cpu)
        assert "NIE JEST porownywany" not in k, (
            "przebieg kalibracyjny (%.3f s ściany, %.3f s CPU, stosunek %.3f) przestał "
            "być porównywany z progiem — podłoga %.3f ucisza maszynę, którą ten próg "
            "opisuje, czyli bramka milczy zawsze"
            % (sciana, cpu, cpu / sciana, MIERZALNOSC_MIN))
        porownane += 1
    assert porownane == len(POMIARY_CPU_BIEZACEGO_DRZEWA), (porownane,)
    assert porownane >= 8, (
        "przebiegów kalibracyjnych jest %d — poniżej ośmiu, na których mierzono "
        "rozstrzygnięcie 6.D247" % porownane)


def test_podloga_mierzalnosci_JEST_PRZYBITA_do_pomiaru_z_ktorego_wyszla():
    """Podłoga ma się zgadzać ze środkiem geometrycznym luki, a nie być liczbą z ręki.

    **Skąd ta bramka, 16.09.2026, z przeglądu adwersaryjnego 6.D247.** Sama
    `MIERZALNOSC_MIN` nie była przybita niczym: podmiana `1.168` na `1.0` dawała
    **37/37 przeszło**, choć przy 1,0 incydent `docker-runner-02` (0,992) leży już
    tylko **o 0,008** pod podłogą, a cały akapit o „środku geometrycznym luki" staje
    się nieprawdą — po cichu. Liczba, którą da się przesunąć bez zapalenia czegokolwiek,
    jest liczbą, o której proza mówi, a drzewo nie wie.

    Przybita jest do **wyliczenia**, a nie do samej siebie: podłoga ma być średnią
    geometryczną najniższego przebiegu kalibracyjnego i najwyższego przebiegu
    odmówionego. Dzięki temu dopisanie nowego przebiegu do któregokolwiek zbioru
    **przelicza** podłogę zamiast ją unieważniać, a rozjazd wychodzi tutaj.
    """
    dol_kalibracji = min(cpu / sciana for _, sciana, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA)
    gora_odmowiona = INCYDENT_DOCKER_CPU / INCYDENT_DOCKER_SCIANA
    srodek = math.sqrt(dol_kalibracji * gora_odmowiona)
    assert gora_odmowiona < dol_kalibracji, (
        "przebieg ODMÓWIONY (%.3f) nie leży już pod najniższym przebiegiem "
        "KALIBRACYJNYM (%.3f) — zbiory się przecięły i podłogi nie da się między nie "
        "wstawić; wtedy trzeba przeliczyć cały wybór, a nie poprawić stałą"
        % (gora_odmowiona, dol_kalibracji))
    assert abs(MIERZALNOSC_MIN - srodek) <= 0.001, (
        "`MIERZALNOSC_MIN` stoi na %.4f, a środek geometryczny luki między "
        "najniższym przebiegiem kalibracyjnym (%.4f) a przebiegiem odmówionym "
        "(%.4f) wynosi %.4f — jedno z dwóch jest z ręki. Proza nad stałą wywodzi ją "
        "z tego wyliczenia, więc rozjazd znaczy, że proza opisuje inną liczbę niż ta, "
        "którą wykonuje kod" % (MIERZALNOSC_MIN, dol_kalibracji, gora_odmowiona, srodek))
    # Kontrola przyrządu: podłoga naprawdę rozdziela oba zbiory, a nie tylko wypada
    # między dwie liczby, które akurat podano.
    for _, sciana, cpu in POMIARY_CPU_BIEZACEGO_DRZEWA:
        assert cpu / sciana >= MIERZALNOSC_MIN, (
            "przebieg kalibracyjny %.3f/%.3f = %.3f wpadł POD podłogę %.3f — podłoga "
            "przestała porównywać materiał, na którym próg został skalibrowany"
            % (cpu, sciana, cpu / sciana, MIERZALNOSC_MIN))


def test_podloga_UCISZA_regres_ktory_stara_podloga_by_zlapala_i_to_jest_LICZBA():
    """Cena wariantu (d), wypisana liczbą zamiast zdaniem — 16.09.2026.

    Proza nad stałą mówi, że na maszynie oddającej jeden rdzeń bramka MILKNIE, i to
    jest prawda ogólna. **Czego nie mówiła, a co przegląd adwersaryjny wyciągnął:**
    milknie także na przebiegu, który przekracza próg CPU o **ćwierć** — bo o dopuszczeniu
    do porównania decyduje wyłącznie stosunek, a ten może być niski przy CPU dowolnie
    wysokim. Przebieg (471,700 s ściany, 550,400 s CPU) ma stosunek **1,167**, czyli
    o **0,001** pod podłogą, a jego CPU stoi **125 %** progu. Pod starą podłogą 0,75
    ten przebieg byłby ODRZUCONY.

    Bramka nie żąda, żeby tak nie było — wariant (d) wybrał właściciel i cisza jest
    jego świadomą ceną. Żąda, żeby ta cena stała w drzewie jako **przypadek z liczbami**,
    a nie jako zdanie o „maszynie oddającej jeden rdzeń". Gdy ktoś podłogę ruszy, ten
    test powie mu, co dokładnie przestaje być widziane.
    """
    sciana, cpu = 471.700, 550.400
    odrzuc, komunikat = werdykt(sciana, cpu)
    assert cpu > SUITE_CPU_BUDGET_S, (
        "przypadek kontrolny przestał przekraczać próg (%.3f wobec %.1f) — wtedy nie "
        "mierzy już niczego" % (cpu, SUITE_CPU_BUDGET_S))
    assert cpu / sciana < MIERZALNOSC_MIN, (
        "przypadek kontrolny (%.3f) wyszedł NAD podłogę %.3f — jeżeli podłoga spadła "
        "świadomie, przepisz ten test razem z nią; jeżeli nie, cisza opisana w prozie "
        "nad stałą zmieniła zasięg" % (cpu / sciana, MIERZALNOSC_MIN))
    assert odrzuc is False, (
        "przebieg %.1f %% progu CPU zostaje dziś ODRZUCONY, a proza nad stałą mówi, "
        "że podłoga go przepuszcza — jedno z dwóch trzeba przepisać"
        % (100.0 * cpu / SUITE_CPU_BUDGET_S))
    assert "NIE JEST porownywany" in komunikat, (
        "komunikat nie mówi, że porównanie zostało POMINIĘTE — a cisza bez wiersza "
        "w logu jest ciszą, której nikt nie zauważy:\n" + komunikat)


def test_krok_CI_NIE_podaje_nazwy_maszyny_i_to_jest_WYBOR_a_nie_przeoczenie():
    """Warunek maszyny z 6.D149 jest w CI gałęzią martwą — i ma nią zostać.

    **Zmierzone 16.09.2026 (6.D247).** Krok „Run tool tests" woła werdykt z DWOMA
    argumentami pozycyjnymi, więc `maszyna` zostaje przy domyślnym `MASZYNA_PROGU`,
    a gałąź `if maszyna != MASZYNA_PROGU` nie wykonuje się w CI **ani razu**. Nic
    w kroku nie czyta `RUNNER_NAME`. Rozstrzygnięcie 6.D149 broni więc wyłącznie
    wywołań wewnątrz tego modułu — i przez to przebieg z `docker-runner-02` doszedł
    do porównania z progiem, którego ta maszyna nie dotyczy.

    **Dlaczego to NIE jest usterka do naprawienia dopisaniem argumentu.** Podanie
    nazwy maszyny zrobiłoby z niej selektor, czego `CLAUDE.md` §9 zabrania wprost
    („Runnera nie wybiera się po nazwie"), a liczebność puli nie ma prawa stać
    w drzewie. Rozstrzygnięcie właściciela z 16.09.2026 idzie więc inną drogą:
    odsiewa PODŁOGA, która nie wymienia żadnej nazwy i mierzy wyłącznie liczbę,
    którą krok i tak liczy.

    Ta bramka pilnuje, żeby nikt nie „naprawił" martwej gałęzi przez dopisanie nazwy.
    """
    krok = _tekst_kroku_werdyktu()
    assert "B.werdykt(" in krok, krok
    assert "maszyna=" not in krok, (
        "krok CI podaje `werdykt` nazwę maszyny — to robi z niej selektor, czego "
        "`CLAUDE.md` §9 zabrania; odsiewaniem jest PODŁOGA, nie nazwa:\n" + krok)
    assert "RUNNER_NAME" not in krok, (
        "krok CI czyta `RUNNER_NAME` — ta nazwa nie ma prawa dotrzeć do werdyktu "
        "(`CLAUDE.md` §9):\n" + krok)
    # Kontrola przyrządu: czytnik naprawdę widzi treść kroku, a nie pusty napis.
    assert "SUITE_CPU_BUDGET_S" in krok or "test_suite_runtime_budget" in krok, (
        "czytnik kroku oddał tekst, w którym nie ma ani nazwy modułu, ani progu — "
        "wtedy trzy asercje wyżej są zielone nad niczym:\n" + krok)
