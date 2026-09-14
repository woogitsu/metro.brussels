#!/usr/bin/env python3
"""Swoistosc igly asercji wobec komunikatow `src/Game/` — druga rodzina, ta sama metoda.

**Po co ta bramka istnieje.** `reports/audyt-asercji.md` §7 konczy sie zdaniem, ktorego
nie da sie czytac inaczej: „o tamtych 53 asercjach ten raport nie mowi nic — i nie udaje,
ze mowi". Cztery przypadki asercji nierozstrzygajacej z 07.09.2026 byly wszystkie
z runnera i z `tools/tests/`, wiec wniosek 6.A32 („przyrzad lapie 0 z 4") jest zdaniem
o TAMTEJ czworce, nie o `tests/Game.Tests`. 6.A33 zamknelo bramka rodzine komunikatow
runnera (`src/Sim.Runner/Program.cs`); ta pozycja stosuje **te sama metode** do drugiej
zamknietej rodziny i nie wymysla drugiej metody.

**Jeden czytnik C#, nie drugi (6.D30).** Literaly, maske i zszywanie konkatenacji
bierzemy WPROST z `test_needle_specificity` — `komunikaty`, `_spany`, `tresc_literalu`.
Drugi czytnik tego samego jezyka rozjechalby sie po cichu, a rozjazd dwoch przejsc po
jednym drzewie jest w tym repozytorium zmierzona usterka, nie przewidywana.

**Co jest KOMUNIKATEM.** Maksymalna grupa literalow zszytych `+`, wielowyrazowa —
definicja 6.A33, bez zmian. Rodzina to WSZYSTKIE pliki `.cs` pod `src/Game/`
(bez wygenerowanego `.godot/`), bo `tests/Game.Tests` testuje ten jeden zestaw i jedna
klase z niego wola drugiej: `EmergencyBrakeTests` asertuje `DriverInput.Help`, ktorego
tresc stoi w `Input/DriverActions.cs`, wiec rodzina zawezona do pliku o pasujacej nazwie
zglaszalaby te igle jako „bez dopasowania", czyli milczalaby o niej.

**Co jest IGLA — i dwa zawezenia, oba z powodem.**

1. Ksztalty: `StringAssert.Contains(co, "igla")` oraz `.Contains("igla")` WEWNATRZ
   `Assert.IsTrue(...)`. Ten drugi ksztalt jest w `Game.Tests` liczny i robi dokladnie
   to samo, co pierwszy.
2. `Assert.IsFalse(x.Contains("igla"))` **nie jest igla tej bramki** i to jest
   rozstrzygniecie, nie przeoczenie. Przy asercji na BRAK igla pospolita jest MOCNIEJSZA
   od swoistej — `Assert.IsFalse(naGranicy.Contains("jeszcze"))` w
   `ChaseCameraAimTests` ma zlapac kazde zdanie z tym slowem, a nie jedno. Rodzina
   usterki, o ktorej mowi 6.A32, dotyczy asercji na OBECNOSC.
3. Igla interpolowana (`$"--{name}"`) jest pomijana razem z igla trzymana w zmiennej.
   Napis, ktory test naprawde poda, sklada sie w czasie wykonania; dopasowanie
   `$"--{name}"` z tekstu do literalu `$"--{name}"` w `RunPlan.cs` jest zbieznoscia
   ZAPISU ZRODLA, a nie zdaniem o komunikacie. Bez tego zawezenia bramka policzylaby
   `--{name}` jako igle w czterech komunikatach i zazadala jej wzmocnienia — czego
   zrobic nie sposob, bo tam nie ma zadnej igly do wzmocnienia.

**Trzy szczeble, bo trzy rozne rzeczy.**

1. Igla zawarta w WIECEJ NIZ JEDNYM komunikacie `src/Game/` — zgloszenie. Naprawia sie
   **w tescie**, nie w programie: tresc komunikatow jest poza zakresem 6.D34. Komunikat
   awarii mowi przy tym, czy kolizja jest WEWNATRZ jednego pliku (ostrzejsza: ten sam
   program moze wypisac oba zdania), czy MIEDZY plikami.
2. Igla niejednoznaczna Z DOBREGO POWODU — wpis w `POWODY` z powodem podanym zdaniem.
   Lista zamknieta zapadka z OBU stron (wzorzec 6.A31), bo wpis tanszy od wzmocnienia
   igly rosnie po cichu, a wpis, ktory przestal opisywac niejednoznacznosc, gnije.
3. Igla bez ani jednego dopasowania — poza zakresem werdyktu, ale POD ZAPADKA. Bez niej
   najtanszym uciszeniem szczebla 1 byloby przepisanie igly na tekst, ktorego
   w literalach nie ma wcale, czyli zamiana niejednoznacznosci na niewidzialnosc.

**KONTROLE — kazda WYKONANA, wypisane w `reports/swoistosc-igly-game.md`:**

  KD (dodatnia)  oslabienie igly `--replay nie laczy sie z --line` do `--replay`
                 wywraca szczebel 1 i nic poza tym modulem.
                 Pilnuje tego `test_a_weakened_needle_lights_up_the_first_rung`.
  KU (ujemna)    igla jednoznaczna NIE jest zglaszana, a mutacja warunku `> 1` na
                 `>= 1` PRZENOSI zbior zgloszen — „nie zglasza" jest rozroznieniem,
                 nie pustym zbiorem.
                 Pilnuje tego `test_a_specific_needle_is_never_reported`.
  KP (przyrzad)  dopisanie do `src/Game/RunPlan.cs` drugiego komunikatu z istniejaca
                 igla PODNOSI jej licznik, a ten sam dopisek w komentarzu NIE.
                 Pilnuje tego `test_the_verdict_follows_the_source_files`.
  KW (wzorzec)   zepsuty wzorzec daje zero komunikatow i zero igiel, a wtedy caly modul
                 swieci zielono. Pilnuja tego progi `MIN_GAME_MESSAGES`,
                 `MIN_GAME_NEEDLES` i `MIN_GAME_SOURCES` oraz dwa testy granicy
                 na wejsciu syntetycznym.
"""

import collections
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as CTM  # noqa: E402
import test_needle_specificity as NS  # noqa: E402
import tree_walk as TW  # noqa: E402

#: Drzewo, z ktorego bierze sie rodzina komunikatow. Cale `src/Game/`, bo klasy tego
#: zestawu wolaja siebie wzajemnie — patrz docstring modulu.
#:
#: **6.D117: `GAME_SOURCE_GLOB` i `GAME_SOURCE_SKIP` zniknely razem z wlasna regula
#: odsiania.** Wzorzec `src/Game/**/*.cs` byl argumentem rekurencyjnego `glob`,
#: a `.godot` — jednopozycyjna kopia listy z `.gitignore`. Obie rzeczy robi dzis
#: `TW.znajdz`, wiec obie stale przestaly byc czytane; martwa stala jest zdaniem
#: o repozytorium, ktore ktos przeczyta i uzna za prawdziwe (#50), wiec nie zostaja.
GAME_SOURCE_ROOT = os.path.join("src", "Game")

#: Pliki z iglami.
GAME_TEST_GLOB = os.path.join("tests", "Game.Tests", "*.cs")

#: Igly niejednoznaczne Z POWODEM. Klucz to TRESC igly, nie numer wiersza: numer
#: przesuwa kazdy commit dopisujacy cokolwiek wyzej, a bramka zapalajaca sie na tekscie
#: poprawnym zostaje wylaczona, nie naprawiona (6.D27).
POWODY = {
    "--from-telemetry":
        "Cala tresc testu `FromTelemetryRefusesEveryOtherSourceOfMovement`: szesc par "
        "wymienionych z nazwy (6.C3), a asercja obok tej sprawdza, ze komunikat nazywa "
        "DRUGI tryb pary. Igla jest nazwa PIERWSZEGO trybu i MA pasowac do wszystkich "
        "szesciu odmow — inaczej nie byloby czym sprawdzic, ze kazda z nich sie nim "
        "przedstawia. Wzmocnienie do calego zdania odmowy zabraloby testowi to, co "
        "mierzy z nazwy, a szescioro roznych zdan trzeba by wpisac do testu z reki.",
    "--telemetry":
        "Po wzmocnieniu zostal JEDEN uzytek: "
        "`OpcjaSciezkowaOdmawia_takze_samych_bialych_znakow` asertuje odmowe o PUSTEJ "
        "sciezce, a ta jest skladana interpolacja (`--{name} wymaga sciezki`), wiec "
        "swoistej igly dla niej nie ma w zadnym literale. Oba dopasowania — odmowa "
        "`--line` z `--telemetry` i odmowa o `--input-log` — dotycza komunikatow INNYCH "
        "niz mierzony. To ten sam przypadek, co `--steps` w 6.A33.",
    "skończoną":
        "Kolizja MIEDZY plikami: `RunPlan.cs` i `TelemetryTrack.cs` koncza swoje odmowy "
        "tym samym zwrotem „nie jest skonczona liczba\", bo obie mowia o tej samej "
        "rodzinie wartosci. Test stoi na `RunPlan.Parse` i komunikatu `TelemetryTrack` "
        "nie ma jak zobaczyc; czesc rozstrzygajaca zdania `RunPlan` (`[ARGUMENT]` "
        "i nazwa opcji) jest po drugiej stronie dziury interpolacyjnej, wiec igla "
        "swoista nie istnieje. Obok stoi druga igla tego testu (`abc`).",
    "skończoną liczbą":
        "Ta sama kolizja miedzyplikowa widziana z drugiej strony: test "
        "`AnUnparsableNumberIsRefusedWithItsColumn` stoi na `TelemetryTrack` i odmowy "
        "`RunPlan` nie ma jak zobaczyc. Numer wiersza i nazwa kolumny, czyli jedyne "
        "czlony rozstrzygajace, sa interpolowane; obok stoi druga igla tego testu "
        "(`chainage_m`).",
}

#: Zapadka na liste wyzej, z OBU stron — wzorzec 6.A31. Zmierzone 07.09.2026: cztery
#: wpisy. Bez dolnego ostrza zapadka stalaby wyzej niz lista i przyjmowalaby nowy wpis
#: bez sladu w diffie.
MAX_GAME_JUSTIFIED_NEEDLES = 4

#: Zapadka na igly bez ani jednego dopasowania (szczebel 3). Zmierzone 07.09.2026:
#: **16 z 45**. Rosnie tylko przez przepisanie igly na tekst, ktorego w literalach nie
#: ma — czyli przez zamiane niejednoznacznosci na niewidzialnosc.
#:
#: **16 -> 19, 10.09.2026 (6.D83).** Trzy nowe igle sa z zalozenia bez dopasowania
#: w komunikatach `src/Game`, bo nie sa komunikatami: `hud.nie-ma-takiego` to KLUCZ
#: celowo nieistniejacy (test zada, zeby katalog rzucil, a nie wyswietlil nazwe
#: klucza), a `Panel/Rows` i `font_size` to sciezka wezla sceny i nazwa wlasciwosci
#: motywu — obie sa kontrola przyrzadu skanu literalow w `UiTextTests`, ktory ma je
#: WIDZIEC, zeby bylo co odsiewac. Wzmocnienie tych igiel nie ma sensu: nie opisuja
#: zdania dla czlowieka.
#:
#: **19 -> 21, 10.09.2026 (6.D99).** Dwie nowe igle (`koniec bloku`, `wyrazeniowa`)
#: stoja w `UiTextTests.Wycinanie_ciala_metody_bierze_te_metode_a_nie_nastepna`
#: i asertuja na WEJSCIU SYNTETYCZNYM — na napisie zlozonym w samym tescie, ktory
#: udaje dwie metody C#. Komunikatem `src/Game` nie sa i byc nie maja: kontrola
#: sprawdza, czy wycinanie ciala metody bierze te metode, a nie nastepna, wiec musi
#: miec wlasne cialo do pociecia. Dopasowanie tych igiel do drzewa znaczyloby, ze
#: probka syntetyczna przypadkiem powtarza zdanie z programu — i wtedy kontrola
#: mierzylaby cos innego, niz mowi.
#:
#: **Trzymania igly w zmiennej NIE uzyto, choc ominelaby zapadke.** Bramka pomija
#: igle ze zmiennej (zawezenie 3), wiec `var x = "koniec bloku";` zdjelby te dwie
#: pozycje z licznika bez sladu. To jest dokladnie ta zamiana niejednoznacznosci na
#: niewidzialnosc, przed ktora szczebel trzeci ma bronic — wiec zapadka rosnie,
#: a igla zostaje widoczna.
#: **21 -> 24, 11.09.2026 (6.D130).** Trzy nowe igle i wszystkie trzy sa z zalozenia
#: bez dopasowania w komunikatach `src/Game`, bo nie sa komunikatami programu:
#: `Escape` to WEJSCIE SYNTETYCZNE testu
#: `Odrzucony_literal_mowi_KTORY_z_dwoch_powodow_go_dotyczy` — nazwa klawisza silnika
#: podana skanowi po to, zeby ja odrzucil, i dopasowanie jej do drzewa znaczyloby, ze
#: ten napis stoi w warstwie gry, czyli ze bramka literalow jest czerwona; `literal
#: jezykowy` i `nazwa klawisza silnika` to czlony komunikatu SAMEGO TESTU, ktory ten
#: test porownuje, zeby sprawdzic, ze oba odrzucenia daja dwa ROZNE zdania.
#:
#: Trzymania igiel w zmiennej znowu NIE uzyto, z tego samego powodu, co przy
#: 19 -> 21: bramka pomija igle ze zmiennej, wiec `var x = "Escape";` zdjelby je
#: z licznika bez sladu — czyli zamienilby niejednoznacznosc na niewidzialnosc,
#: przed ktora szczebel trzeci ma bronic.
#: **24 -> 26, 11.09.2026 (6.D143).** Dwie nowe igle, `Esc` i `input.key.space`, stoja
#: w `UiTextTests.Kazdy_literal_KeyNames_ma_ROZSTRZYGNIECIE_czy_bramka_go_widzi` jako
#: OCZEKIWANA ZAWARTOSC tablicy `Nazwy` z `KeyNames.cs`, przybita rownoscia calej listy.
#: Bez dopasowania sa z zalozenia i musza takie zostac: bramka szczebla 1 szuka igiel
#: w komunikatach WIELOWYRAZOWYCH `src/Game`, a te dwa napisy sa pozycjami tablicy —
#: jednowyrazowym napisem wytloczonym na klawiszu i kluczem katalogu. Gdyby ktorykolwiek
#: dopasowal sie do komunikatu programu, znaczyloby to, ze napis klawisza wszedl do
#: zdania dla czlowieka, czyli cos odwrotnego od tego, czego pilnuje 6.D143.
#:
#: Wzmocnienie igly nie ma tu sensu i to jest inny powod niz przy 19 -> 21: tam igla
#: opisywala wejscie syntetyczne, tu opisuje ZAWARTOSC DRZEWA, ktora test i tak pinuje
#: rownoscia calej listy. Igla dluzsza byla by tym samym pinem zapisanym drugi raz.
#: Trzymania igiel w zmiennej znowu NIE uzyto, z tego samego powodu, co wyzej.
#: **26 -> 28, 13.09.2026 (6.D184), i ten akapit jest DOPISANY PO FAKCIE.** Podniesienie
#: 6.D184 poszlo bez uzasadnienia i to bylo pominiecie: kazdy poprzedni szczebel ma tu
#: swoj akapit, a bez niego zapadka rosnie bez sladu, czyli robi dokladnie to, przed czym
#: ma bronic. Dwie igle sa z zalozenia bez dopasowania:
#: `//host/sciezka` to WEJSCIE SYNTETYCZNE testu
#: `Obcinacz_wierszowy_TNIE_literal_wielowierszowy_a_czytnik_nie` — wiersz zaczynajacy sie
#: od `//` schowany w SRODKU napisu wielowierszowego, po to, zeby obcinacz mial co uciac;
#: `StaryCzytnik(KodBezKomentarzyDlaStaregoCzytnika(kod))` to PIN NA KSZTALT KODU, a nie
#: komunikat — dopasowanie go do komunikatu `src/Game` znaczyloby, ze wywolanie z testu
#: stoi w napisie warstwy gry.
#: **28 -> 29, 13.09.2026 (6.D185).** Jedna igla, `_ => phase.ToString(),`, stoi
#: w `UiTextTests.Faza_ma_ramie_dla_kazdego_czlonu_DoorPhase_wiec_ramie_domyslne_jest_martwe`
#: i jest PINEM NA KSZTALT KODU tej samej rodziny co igla z 6.D184: pilnuje, ze ramie
#: domyslne `FirstRun.Faza` nie zniknelo, bo jego zniknieciem bylaby zmiana zachowania
#: HUD-u (wyjatek w czasie przejazdu zamiast angielskiej nazwy). Bez dopasowania jest
#: z zalozenia: bramka szczebla 1 szuka igiel w komunikatach WIELOWYRAZOWYCH `src/Game`,
#: a to jest fragment skladni C#. Gdyby sie dopasowala, znaczyloby to, ze ramie `switch`-a
#: stoi wewnatrz napisu dla czlowieka.
#:
#: Wzmocnienia igly nie ma po co robic — jest juz doslownym wierszem zrodla, razem
#: z przecinkiem, ktory odroznia ramie od zdania o nim w komentarzu dokumentacyjnym
#: (`FirstRun.cs:1798` niesie `phase.ToString()` bez przecinka; patrz 6.D199).
#: Trzymania igly w zmiennej znowu NIE uzyto, z tego samego powodu, co wyzej.
#: **29 -> 30, 13.09.2026 (6.D188).** Jedna igla, `otwarte`, stoi
#: w `UiTextTests.Zabrane_slowa_to_WYRAZENIA_C_a_nie_tekst_dla_gracza` jako WEJSCIE
#: SYNTETYCZNE: napis dla gracza schowany w dziurze interpolacji
#: (`$"stan: {(x ? "otwarte" : "zamkniete")}"`), podany czytnikowi po to, zeby
#: pokazac, ze zwraca go OSOBNO — a wiec ze `BezDziur` nie ma jak go schowac.
#: Bez dopasowania jest z zalozenia i musi takie zostac: dopasowanie znaczyloby,
#: ze probka syntetyczna przypadkiem powtarza napis z programu, i wtedy kontrola
#: mierzylaby co innego, niz mowi. Ta sama konstrukcja i ten sam powod, co przy
#: `koniec bloku` w kroku 19 -> 21.
#:
#: Wzmocnienie igly nie ma tu sensu: jest nia CALA tresc zagniezdzonego literalu,
#: a dluzsza probka to inny napis, nie mocniejsza igla. Trzymania w zmiennej znowu
#: NIE uzyto — bramka pomija igle ze zmiennej, wiec `var x = "otwarte";` zdjalby ja
#: z licznika bez sladu.
#:
#: **31 -> 42 (13.09.2026, MB-02), z powodem i z ROZSTRZYGNIECIEM, a nie z przeliczeniem.**
#: Jedenascie nowych igiel to igly `RunSummaryTests.cs` na tekst ZLOZONY: `cele: 2 z 2`,
#: `czas: 123.5 s`, `-0.250 m`, `3 ostrzezen` i podobne. Zadna z nich nie wystepuje
#: w `src/Game/` doslownie i wystepowac NIE MOZE — w zrodle stoi szablon katalogu
#: (`cele: {0} z {1}`), a igla jest jego wynikiem po podstawieniu.
#:
#: **To NIE jest ta klasa, przed ktora ta bramka broni.** Bramka pilnuje igly, ktora
#: nie ma dopasowania, bo ma LITEROWKE — taka igla przechodzi po cichu, gdy test tylko
#: jej szuka. Tutaj jest odwrotnie: igla stoi pod `StringAssert.Contains` na wyniku
#: `RunSummary.Compose`, wiec literowka w igle wywraca test NATYCHMIAST. Brak
#: dopasowania w zrodle jest tu wlasnoscia konstrukcji, a nie cisza.
#:
#: Granica, wypisana: gdyby ktos wpisal tu igle na tekst, ktory w zrodle stac POWINIEN
#: (klucz katalogu, nazwe akcji, sciezke), ta bramka nadal ja zlapie — bo takie igly
#: maja dopasowanie i jego brak jest wtedy usterka. Podniesienie tej liczby nie zwalnia
#: z rozstrzygniecia; zwalnia z niego dopiero POWOD wypisany tutaj.
#: **42 -> 46 (13.09.2026, MB-02), druga rodzina w tym samym commicie.** Cztery nowe
#: igly to igly `TrainingWiringTests.cs` na KOD, a nie na komunikat: `!_resetPending`,
#: `DesignAssumptions.TrainingTargets`, `_axis.Stations[i].StopId`, `for (var i = 1;`.
#: Ta klasa czyta zrodlo `FirstRun.cs`, bo trzy rzeczy — kolejnosc wywolania w kroku,
#: brak `_done` przy koncu sesji i przekazanie sesji do resetu — sa KOLEJNOSCIA
#: i WARUNKAMI w ciele metody wezla Godota, a nie wiedza, ktora da sie z niego wypchnac.
#: Igla na kod nie ma dopasowania w rodzinie komunikatow i miec go nie moze; literowka
#: w niej wywraca test natychmiast, wiec nie jest to klasa cicha.
#: **46 -> 48 (14.09.2026, MB-03).** Dwie nowe igly `TractionBlockTests.cs` na KOD
#: `FirstRun.cs`: `private double? SufitKmh() =>` i wyrazenie warunku trybu. Ta sama
#: rodzina, co cztery igly `TrainingWiringTests.cs` — literowka w nich wywraca test
#: natychmiast, wiec nie jest to klasa cicha.
#: **48 -> 50 (14.09.2026, MB-05).** Dwie nowe igly `CabPlacementTests.cs` na KOD:
#: `trainLength` (czy scena podaje kabinie dlugosc SKLADU) i `TrainLayout.PlaceWithRear(`
#: (czy `CabView` idzie przez wersje z zadanym ogonem). Ta sama rodzina i ten sam powod
#: co wyzej, ale z pomiarem, ktorego tamte dwa wpisy nie mialy: bramka LICZBOWA tych
#: dwoch rzeczy NIE LAPIE i to jest zmierzone — trzy kontrole negatywne na testach
#: arytmetycznych `CabPlacementTests` wyszly ZIELONE, bo mutacje siedza w wezlach
#: Godota, ktorych `dotnet test` nie powola. Igla na kod jest tu wiec jedyna droga,
#: a nie droga wygodniejsza.
#: **50 -> 48 (14.09.2026, audyt bramki MB-05) i ta zapadka schodzi W DOL, co jest
#: tu POPRAWNYM kierunkiem, a nie regresja.** Znikly dokladnie te dwie igly, ktore
#: akapit wyzej opisuje: `trainLength` i `TrainLayout.PlaceWithRear(`. Nie zniknela
#: jednak ochrona — obie byly argumentami `Assert.IsTrue(....Contains("..."))`, czyli
#: pytaly o PISOWNIE TOKENU, i obie przechodzily mutacje dajaca usterke 0,700 m
#: (`chainage - trainLength + 0.7` oraz `PlaceWithRear(axis, _bodies, rearChainageM
#: + 0.7)`) — zmierzone, 292/292 kazda. W ich miejsce weszly `Assert.AreEqual` na
#: CALA liste argumentow, ktorych `igly()` z definicji nie liczy, bo liczy wylacznie
#: `Contains` w `Assert.IsTrue` i `StringAssert.Contains`. Zapadka mowi wiec prawde:
#: igiel jest mniej, a bramka jest mocniejsza.
# ZOSTAJE NA 48 (14.09.2026, MB-08) — i jest to WYNIK, a nie brak zmiany.
# Katalog dostał zdanie `drzwi są już otwarte`, więc igła `otwarte` z wejścia
# SYNTETYCZNEGO zaczęła pasować do dwóch komunikatów `src/Game/` naraz. Zapadkę
# dałoby się wtedy obniżyć do 47 i byłoby to załatanie objawu: igła nie zaczęła
# mierzyć drzewa, tylko przestała być syntetyczna. Poprawione po stronie TESTU
# (`otwarte` -> `rozsunięte`), a nie po stronie tej liczby.
MAX_GAME_UNMATCHED_NEEDLES = 48

#: Progi KW. Literowka we wzorcu daje zero dopasowan i caly modul zielony; te trzy
#: liczby sa jedynym powodem, dla ktorego taka literowka jest widoczna. Zmierzone
#: 07.09.2026: **142** wielowyrazowe grupy literalow w **18** plikach `src/Game/`
#: i **45** roznych igiel w **53** mierzalnych wywolaniach z **64** o tym ksztalcie.
MIN_GAME_MESSAGES = 142

#: **PRZYBITA ROWNOSCIA od 6.D151 — ten akapit jest przepisany, a nie dopisany obok.**
#: Do 12.09.2026 stala byla progiem (`>= 45`) i lezala w rodzinie zapadek WOLNYCH:
#: obnizenie progu nie zapalalo niczego, a obnizenie jest wlasnie tym ruchem, ktory
#: zwalnia bramke z pilnowania.
#:
#: **Ile ten prog przepuszczal, jest zmierzone: 14 igiel, czyli 24 %.** Igiel bylo
#: 07.09.2026 czterdziesci piec, a 12.09.2026 jest **59** — czternascie moglo znikac
#: z `tests/Game.Tests` i prog nie powiedzialby ani slowa. Z pieciu progow tej rodziny
#: ten mial luz najwiekszy (pozostale: `MIN_GAME_MESSAGES` 8, `MIN_MESSAGES` 9,
#: `MIN_NEEDLES` 2, `MIN_GAME_SOURCES` 1).
#:
#: **Wartosc zmieniona z 45 na 59 NIE jest przestrojeniem progu**: pin musi rownac
#: sie temu, co pinuje, inaczej jest czerwony od pierwszego dnia. Stara liczba stoi
#: wyzej jako historia, a nie jako druga prawda.
#:
#: **Nazwa zostaje `MIN_`, i to jest zgodne z konwencja, nie wbrew niej**: przedrostek
#: nazywa strone ZAKAZANA, a rownosc strzeze obu — tak samo jak `MAX_COMMIT_EXCEPTIONS`
#: i szesc innych zapadek `MAX_` przybitych rownoscia (`klasa_zapadki`
#: w `test_tree_walks.py` mowi to wprost: „Rownosc strzeze w obie").
#:
#: **Koszt jest zmierzony, nie oszacowany.** Gdyby ta stala byla przybita od poczatku,
#: trzeba by ja poprawic w **5 z 11** rewizji dotykajacych `tests/Game.Tests`
#: (45 -> 49 -> 52 -> 54 -> 57 -> 59), czyli w 45 % z nich. To mniej, niz kosztuje
#: `MIN_REPORTS`, poprawiane przy kazdym raporcie.
# 65 -> 84 (13.09.2026, MB-02): czternascie roznych igiel w `RunSummaryTests.cs`
# i piec w `TrainingWiringTests.cs`.
# 65 -> 87 (14.09.2026, MB-03): czternascie roznych igiel w `RunSummaryTests.cs`,
# piec w `TrainingWiringTests.cs` i osiem w `TractionBlockTests.cs`.
# 87 -> 89 (14.09.2026, MB-05): dwie igly `CabPlacementTests.cs` — `trainLength`
# i `TrainLayout.PlaceWithRear(`. Obie sa iglami na KOD, nie na komunikat, i obie
# licza sie takze w `MAX_GAME_UNMATCHED_NEEDLES` (48 -> 50); powod stoi tam.
# 89 -> 87 (14.09.2026, audyt bramki MB-05): te same dwie igly ZNIKLY, bo obie
# pytaly o pisownie tokenu i obie przepuszczaly usterke 0,700 m (zmierzone: 292/292).
# Zastapily je porownania dokladne calej listy argumentow, ktorych `igly()` nie liczy.
# Bramka jest przez to mocniejsza, a liczba mniejsza — powod pelny stoi przy
# `MAX_GAME_UNMATCHED_NEEDLES`.
MIN_GAME_NEEDLES = 87
MIN_GAME_SOURCES = 18

#: Igla, na ktorej stoja kontrole dodatnia i przyrzadu. Musi byc SWOISTA i musi stac
#: w tescie; oba testy mowia to wprost w komunikacie awarii, bo bez tego zniknieci
#: probki wygladaloby jak zepsuta bramka.
GAME_PROBKA = "--replay nie łączy się z --line"

#: Plik, w ktorym stoi komunikat probki — kontrola przyrzadu dopisuje do niego drugi.
GAME_PROBKA_PLIK = os.path.join("src", "Game", "RunPlan.cs")


def _read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def zrodla():
    """Sciezki plikow `src/Game/`, wzgledne, bez galezi pominietych w `.gitignore`.

    **6.D117: odsianie idzie przez `tree_walk`, a nie przez wlasna regule.** Do
    11.09.2026 stala tu kopia listy o jednej pozycji (`.godot`) — czyli ten sam
    ksztalt bledu, ktory 6.D97 usunelo z przejsc `os.walk`, tylko w trzecim ksztalcie
    przejscia. Wynik jest CO DO PLIKU ten sam: **22 pliki** przed i po (zmierzone
    11.09.2026), bo `src/Game/obj/` i `bin/` dzis nie istnieja — ale gdy powstana,
    dawna regula wpuscilaby je, a ta nie.
    """
    znalezione = TW.znajdz(os.path.join(ROOT, GAME_SOURCE_ROOT), "*.cs")
    return sorted(os.path.relpath(p, ROOT) for p in znalezione)


def testy():
    """Sciezki plikow testowych `tests/Game.Tests/`, wzgledne."""
    return sorted(os.path.relpath(p, ROOT)
                  for p in glob.glob(os.path.join(ROOT, GAME_TEST_GLOB)))


def _zamkniecie(maska, start):
    """Indeks nawiasu zamykajacego wywolanie otwarte na `start`, albo `None`."""
    glebokosc = 0
    for i in range(start, len(maska)):
        if maska[i] == "(":
            glebokosc += 1
        elif maska[i] == ")":
            glebokosc -= 1
            if glebokosc == 0:
                return i
    return None


def _argumenty(maska, start, koniec):
    """Granice `(od, do)` argumentow wywolania, ciete po MASCE i po nawiasach.

    Nie regexem na jednym wierszu: wywolanie rozbite na dwa wiersze wzorzec wierszowy
    gubi, a przecinek w literale zamienilby jeden argument na dwa.
    """
    granice = []
    glebokosc = 0
    ostatni = start + 1
    for i in range(start + 1, koniec):
        znak = maska[i]
        if znak in "([{":
            glebokosc += 1
        elif znak in ")]}":
            glebokosc -= 1
        elif znak == "," and glebokosc == 0:
            granice.append((ostatni, i))
            ostatni = i + 1
    granice.append((ostatni, koniec))
    return granice


def _igla_z_argumentu(source, od, do):
    """Tresc igly, albo `None`, gdy argument nie jest ZWYKLYM literalem.

    Odrzucane sa dwa przypadki i oba z tego samego powodu — z tekstu nie da sie
    powiedziec, jaki napis test naprawde poda: igla w zmiennej albo w wyrazeniu
    (`EmergencyBrake.KeyName`, `"--" + nazwa`) i igla interpolowana (`$"--{name}"`).
    """
    surowy = source[od:do].strip()
    spany = NS._spany(surowy)
    if len(spany) != 1 or spany[0] != (0, len(surowy)):
        return None
    przedrostek = surowy[:len(surowy) - len(surowy.lstrip("@$"))]
    if "$" in przedrostek:
        return None
    return NS.tresc_literalu(surowy)


def igly(source):
    """`{igla: [wiersze]}` dla obu ksztaltow asercji na OBECNOSC.

    `Assert.IsFalse(x.Contains(...))` nie wchodzi — przy asercji na brak igla pospolita
    jest mocniejsza od swoistej, patrz docstring modulu.
    """
    maska = CTM.maska(source)
    out = {}
    for wywolanie in re.finditer(r"StringAssert\.Contains\s*\(", maska):
        start = wywolanie.end() - 1
        koniec = _zamkniecie(maska, start)
        if koniec is None:
            continue
        granice = _argumenty(maska, start, koniec)
        if len(granice) < 2:
            continue
        od, do = granice[1]
        igla = _igla_z_argumentu(source, od, do)
        if igla is not None:
            out.setdefault(igla, []).append(source.count("\n", 0, od) + 1)
    for wywolanie in re.finditer(r"Assert\.IsTrue\s*\(", maska):
        start = wywolanie.end() - 1
        koniec = _zamkniecie(maska, start)
        if koniec is None:
            continue
        for wewnetrzne in re.finditer(r"\.Contains\s*\(", maska[start:koniec]):
            wnetrze = start + wewnetrzne.end() - 1
            zamkniecie = _zamkniecie(maska, wnetrze)
            if zamkniecie is None:
                continue
            od, do = _argumenty(maska, wnetrze, zamkniecie)[0]
            igla = _igla_z_argumentu(source, od, do)
            if igla is not None:
                out.setdefault(igla, []).append(source.count("\n", 0, od) + 1)
    return out


def wywolania(source):
    """Ile wywolan obu ksztaltow stoi w pliku, niezaleznie od tego, czy sa mierzalne.

    Osobno od `igly`, bo roznica miedzy ta liczba a liczba wywolan mierzalnych JEST
    wynikiem pomiaru — mowi, ile igiel z tekstu nie da sie odczytac.
    """
    maska = CTM.maska(source)
    ile = len(re.findall(r"StringAssert\.Contains\s*\(", maska))
    for wywolanie in re.finditer(r"Assert\.IsTrue\s*\(", maska):
        start = wywolanie.end() - 1
        koniec = _zamkniecie(maska, start)
        if koniec is None:
            continue
        ile += len(re.findall(r"\.Contains\s*\(", maska[start:koniec]))
    return ile


def komunikaty_rodziny(nadpisz=None):
    """`[(plik, wiersz, tekst)]` — komunikaty calej rodziny `src/Game/`.

    `nadpisz` (`{sciezka: zrodlo}`) sluzy WYLACZNIE kontroli przyrzadu: podstawia tresc
    pliku bez pisania po drzewie.
    """
    nadpisz = nadpisz or {}
    out = []
    for sciezka in zrodla():
        source = nadpisz.get(sciezka, _read(sciezka))
        for wiersz, tekst in NS.komunikaty(source):
            out.append((sciezka, wiersz, tekst))
    return out


def igly_rodziny(nadpisz=None):
    """`{igla: [(plik, wiersz)]}` dla calego `tests/Game.Tests`."""
    nadpisz = nadpisz or {}
    out = {}
    for sciezka in testy():
        source = nadpisz.get(sciezka, _read(sciezka))
        for igla, wiersze in igly(source).items():
            out.setdefault(igla, []).extend((sciezka, w) for w in wiersze)
    return out


def licznik(nadpisz=None):
    """`{igla: {plik: ile komunikatow tego pliku zawiera igle}}`."""
    wiadomosci = komunikaty_rodziny(nadpisz)
    wynik = {}
    for igla in igly_rodziny(nadpisz):
        per = collections.Counter()
        for plik, _wiersz, tekst in wiadomosci:
            if igla in tekst:
                per[plik] += 1
        wynik[igla] = dict(per)
    return wynik


def razem(per_plik):
    return sum(per_plik.values())


def w_jednym_pliku(per_plik):
    return max(per_plik.values()) if per_plik else 0


def zgloszenia(nadpisz=None, prog=1):
    """Igly przekraczajace `prog` dopasowan w rodzinie, BEZ wpisu w `POWODY`.

    `prog` sluzy WYLACZNIE mutacji w kontroli ujemnej.
    """
    trafienia = licznik(nadpisz)
    return sorted(igla for igla, per in trafienia.items()
                  if razem(per) > prog and igla not in POWODY)


def bez_dopasowania(nadpisz=None):
    trafienia = licznik(nadpisz)
    return sorted(igla for igla, per in trafienia.items() if razem(per) == 0)


def _opis(igla, per):
    rodzaj = ("w JEDNYM pliku" if w_jednym_pliku(per) > 1 else "miedzy plikami")
    return "%r w %d komunikatach (%s): %s" % (igla, razem(per), rodzaj, per)


# --------------------------------------------------------------------------- testy


def test_the_message_family_and_the_needles_are_both_read_from_the_files():
    """Progi KW: zepsuty wzorzec daje zero i caly modul swieci zielono.

    To jest najczestszy sposob, w jaki bramka klamie w strone „wszystko w porzadku",
    i jedyny powod, dla ktorego ten test stoi osobno od pozostalych.
    """
    wiadomosci = komunikaty_rodziny()
    plikow = len({plik for plik, _w, _t in wiadomosci})
    igielki = igly_rodziny()
    assert len(wiadomosci) >= MIN_GAME_MESSAGES, (
        "wzorzec zlapal %d wielowyrazowych komunikatow `src/Game/`, a 07.09.2026 bylo "
        "ich %d — spadek znaczy zepsuty czytnik, nie posprzatany plik"
        % (len(wiadomosci), MIN_GAME_MESSAGES))
    assert plikow >= MIN_GAME_SOURCES, (
        "komunikaty przyszly z %d plikow, a 07.09.2026 z %d" % (plikow, MIN_GAME_SOURCES))
    assert len(igielki) == MIN_GAME_NEEDLES, (
        "wzorzec zlapal %d roznych igiel w `tests/Game.Tests`, a zapadka stoi na %d — "
        "od 6.D151 jest to ROWNOSC, nie prog: liczba w dol znaczy, ze igly znikaja "
        "(albo ze czytnik je gubi), a w gore — ze doszly i trzeba ja poprawic w tym "
        "samym commicie" % (len(igielki), MIN_GAME_NEEDLES))
    assert all(wiersz > 0 for _plik, wiersz, _tekst in wiadomosci)


def test_every_needle_matches_at_most_one_message_or_is_justified():
    """Szczebel 1 i 2 razem: zgloszenie albo wpis z powodem, trzeciej drogi nie ma."""
    trafienia = licznik()
    gdzie = igly_rodziny()
    bad = ["%s [test %s]" % (_opis(igla, trafienia[igla]), gdzie[igla])
           for igla in zgloszenia()]
    assert bad == [], (
        "igla asercji pasuje do wiecej niz jednego komunikatu `src/Game/` i nie ma "
        "wpisu z powodem — wzmocnij ja w tescie albo wpisz na liste: %s" % bad)


def test_a_specific_needle_is_never_reported():
    """KU: bramka lapiaca igle POPRAWNA zostalaby wylaczona w tym samym tygodniu.

    Nie wystarczy, ze nic sie nie zglasza — trzeba pokazac, ze igly jednoznaczne
    W PLIKACH SA, ze zadna z nich nie trafia do zgloszen, i ze przesuniecie warunku
    `> 1` na `>= 1` PRZENOSI zbior zgloszen. Bez ostatniego czlonu ten test
    przechodzilby takze wtedy, gdyby wzorzec nie lapal niczego.
    """
    trafienia = licznik()
    jednoznaczne = {igla for igla, per in trafienia.items() if razem(per) == 1}
    assert len(jednoznaczne) >= 20, sorted(jednoznaczne)
    assert not jednoznaczne & set(zgloszenia())
    przy_jedynce = set(zgloszenia(prog=1))
    przy_zerze = set(zgloszenia(prog=0))
    assert przy_zerze > przy_jedynce, (sorted(przy_jedynce), sorted(przy_zerze))
    assert jednoznaczne <= przy_zerze, sorted(jednoznaczne - przy_zerze)


def test_the_verdict_follows_the_source_files():
    """KP: dopisanie DRUGIEGO komunikatu z istniejaca igla podnosi jej licznik.

    Bez tego testu „bramka czytajaca `src/Game/`" bylaby nieodroznialna od tabeli liczb
    wpisanej z pamieci: obie daja dzis ten sam werdykt. Druga polowa kontroli stoi
    w tym samym tescie: ten sam dopisek w KOMENTARZU licznika nie podnosi, bo komentarz
    maska zamienia na spacje.
    """
    program = _read(GAME_PROBKA_PLIK)
    przed = licznik()
    assert razem(przed.get(GAME_PROBKA, {})) == 1, (
        "igla-przyrzad %r nie stoi juz w tescie albo nie jest swoista (licznik %r) — "
        "kontrola przyrzadu stracila punkt odniesienia"
        % (GAME_PROBKA, przed.get(GAME_PROBKA)))
    drugi = GAME_PROBKA + ", i to jest drugi komunikat"
    komentarz = program + '\n// oslona: Console.Error.WriteLine("%s");\n' % drugi
    assert razem(licznik({GAME_PROBKA_PLIK: komentarz})[GAME_PROBKA]) == 1, (
        "bramka policzyla literal z komentarza")
    kod = program + '\nstatic class Oslona { const string X = "%s"; }\n' % drugi
    po = licznik({GAME_PROBKA_PLIK: kod})
    assert razem(po[GAME_PROBKA]) == 2, po[GAME_PROBKA]
    assert GAME_PROBKA in zgloszenia({GAME_PROBKA_PLIK: kod}), (
        "podniesiony licznik nie trafil do zgloszen")


def test_a_weakened_needle_lights_up_the_first_rung():
    """KD: oslabienie igly swoistej do wieloznacznej wywraca szczebel 1.

    Na wejsciu podstawionym, bo bramka ma dzis szczebel 1 pusty i sam jego zielony
    kolor nie dowodzi niczego (ta sama zasada, co przy 6.A31).
    """
    plik = os.path.join("tests", "Game.Tests", "RunPlanTests.cs")
    source = _read(plik)
    assert GAME_PROBKA in source, (
        "igla-przyrzad %r zniknela z %s — kontrola dodatnia nie ma czego oslabiac"
        % (GAME_PROBKA, plik.replace(os.sep, "/")))
    oslabione = source.replace('"%s"' % GAME_PROBKA, '"--replay"')
    assert oslabione != source, GAME_PROBKA
    assert zgloszenia() == [], (
        "szczebel 1 zapalony JUZ przed oslabieniem: %s — kontrola dodatnia nie pokazuje "
        "wtedy niczego" % zgloszenia())
    assert "--replay" in zgloszenia({plik: oslabione}), zgloszenia({plik: oslabione})


def test_the_needle_reader_reads_presence_and_skips_absence():
    """Granica czytnika igiel, w obie strony, na wejsciu syntetycznym.

    Cztery rozstrzygniecia naraz, bo cztery razy mogloby byc inaczej: oba ksztalty na
    OBECNOSC sa igla, `Assert.IsFalse` nie jest, igla w zmiennej i igla interpolowana
    nie sa. Bez tego testu `igly` moglaby zwracac pusty slownik na wszystkim — a wtedy
    bramka bylaby zielona zawsze.
    """
    probka = "\n".join([
        'class T {',
        '  void A() {',
        '    StringAssert.Contains(plan.Error, "swoista igła");',
        '    StringAssert.Contains(plan.Error, zmienna);',
        '    StringAssert.Contains(',
        '        plan.Error, "igła z dwóch wierszy");',
        '    StringAssert.Contains(plan.Error, "z, przecinkiem");',
        '    Assert.IsTrue(plan.Error!.Contains("igła z IsTrue"), plan.Error);',
        '    Assert.IsFalse(plan.Error!.Contains("brak"), plan.Error);',
        '    Assert.IsTrue(plan.Error!.Contains($"--{name}"), plan.Error);',
        '  }',
        '}',
    ])
    znalezione = igly(probka)
    assert set(znalezione) == {
        "swoista igła", "igła z dwóch wierszy", "z, przecinkiem", "igła z IsTrue",
    }, znalezione
    assert znalezione["igła z dwóch wierszy"] == [6], znalezione
    # Szesc, nie siedem: `Assert.IsFalse` do tej rodziny nie nalezy, a licznik
    # wywolan liczy dokladnie te ksztalty, ktorych igly bramka mierzy.
    assert wywolania(probka) == 6, wywolania(probka)


def test_the_message_reader_is_the_one_from_the_runner_gate():
    """Jeden czytnik C#: komunikaty czyta `test_needle_specificity`, nie kopia.

    Gdyby ten modul dorobil wlasny czytnik literalow, oba rozjechalyby sie po cichu —
    a to jest w tym repozytorium usterka zmierzona (6.D30), nie przewidywana.
    """
    assert igly.__module__ == __name__
    assert NS.komunikaty.__module__ == "test_needle_specificity"
    probka = "\n".join([
        'class P {',
        '  static string[] Tabela = new[] { "--axis", "--limit-kmh" };',
        '  static void M() {',
        '    Console.Error.WriteLine("odmowa w trzech "',
        '        + "czesciach, jedno "',
        '        + "zdanie");',
        '  }',
        '}',
    ])
    teksty = [tekst for _wiersz, tekst in NS.komunikaty(probka)]
    assert teksty == ["odmowa w trzech czesciach, jedno zdanie"], teksty


def test_every_justification_still_describes_an_ambiguous_needle():
    """Powod nie moze przezyc igly, ktora opisuje.

    Wpis, ktorego nie ma czego usprawiedliwiac, jest dziura w bramce ubrana w proze —
    ta sama zasada, ktora 6.D29 postawilo dla listy wyjatkow raportow, 6.B34 dla
    martwych stalych i 6.A31 dla sciezek `bin/`.
    """
    trafienia = licznik()
    martwe = sorted(igla for igla in POWODY
                    if razem(trafienia.get(igla, {})) <= 1)
    assert martwe == [], (
        "powod igly, ktora niejednoznaczna juz nie jest: %s" % martwe)
    puste = sorted(igla for igla, powod in POWODY.items() if len(powod.strip()) < 40)
    assert puste == [], "powod niepodany zdaniem: %s" % puste


def test_the_justification_list_stays_closed():
    """Zapadka z obu stron: wpis tanszy od wzmocnienia igly rosnie po cichu."""
    assert len(POWODY) <= MAX_GAME_JUSTIFIED_NEEDLES, (
        "lista powodow urosla do %d przy zapadce %d — igla ma zostac wzmocniona "
        "w tescie, a nie dostac miejsce na liscie"
        % (len(POWODY), MAX_GAME_JUSTIFIED_NEEDLES))
    assert MAX_GAME_JUSTIFIED_NEEDLES <= len(POWODY), (
        "zapadka %d stoi wyzej niz lista (%d) — obniz ja do stanu faktycznego"
        % (MAX_GAME_JUSTIFIED_NEEDLES, len(POWODY)))


def test_needles_without_a_single_match_stay_under_a_ratchet():
    """Szczebel 3: zamiana niejednoznacznosci na niewidzialnosc musi byc widoczna.

    Igla przepisana na tekst, ktorego w literalach nie ma wcale, ucisza szczebel 1
    i nie zglasza sie nigdzie — chyba ze jej liczba stoi pod zapadka. Wtedy trzeba ja
    podniesc w tym samym commicie, czyli w diffie.
    """
    bez = bez_dopasowania()
    assert len(bez) <= MAX_GAME_UNMATCHED_NEEDLES, (
        "igiel bez ani jednego dopasowania jest %d przy zapadce %d: %s"
        % (len(bez), MAX_GAME_UNMATCHED_NEEDLES, bez))
    assert MAX_GAME_UNMATCHED_NEEDLES <= len(bez), (
        "zapadka %d stoi wyzej niz stan faktyczny (%d) — obniz ja"
        % (MAX_GAME_UNMATCHED_NEEDLES, len(bez)))


def main():
    """Inwentarz do wklejenia w raport: wszystkie igly z licznikiem i wyrokiem."""
    wiadomosci = komunikaty_rodziny()
    gdzie = igly_rodziny()
    trafienia = licznik()
    wszystkich = sum(wywolania(_read(p)) for p in testy())
    print("komunikatow wielowyrazowych src/Game: %d w %d plikach"
          % (len(wiadomosci), len({p for p, _w, _t in wiadomosci})))
    print("igiel roznych: %d (mierzalnych wywolan %d z %d o tym ksztalcie)"
          % (len(gdzie), sum(len(v) for v in gdzie.values()), wszystkich))
    print()
    zgl = zgloszenia()
    for igla in sorted(trafienia, key=lambda i: (-razem(trafienia[i]), i)):
        per = trafienia[igla]
        ile = razem(per)
        wyrok = ("ZGLOSZONA" if igla in zgl
                 else "z powodem" if ile > 1
                 else "bez dopasowania" if ile == 0 else "swoista")
        print("  %-16s %2d %-2s %-44r %s"
              % (wyrok, ile, "1p" if w_jednym_pliku(per) > 1 else "",
                 igla, sorted(per)))
    print()
    print("  swoistych (dokladnie 1 komunikat):   %d"
          % len([1 for per in trafienia.values() if razem(per) == 1]))
    print("  niejednoznacznych (>1):              %d"
          % len([1 for per in trafienia.values() if razem(per) > 1]))
    print("    z tego w JEDNYM pliku:             %d"
          % len([1 for per in trafienia.values() if w_jednym_pliku(per) > 1]))
    print("    z tego z powodem:                  %d (zapadka %d)"
          % (len(POWODY), MAX_GAME_JUSTIFIED_NEEDLES))
    print("    z tego ZGLOSZONYCH:                %d" % len(zgl))
    print("  bez ani jednego dopasowania:         %d (zapadka %d)"
          % (len(bez_dopasowania()), MAX_GAME_UNMATCHED_NEEDLES))
    for igla in zgl:
        print("    ZGLOSZONA: %s" % _opis(igla, trafienia[igla]))
    return 0


if __name__ == "__main__":
    if "--inwentarz" in sys.argv:
        raise SystemExit(main())
    import test_all

    raise SystemExit(test_all.main(__file__))
