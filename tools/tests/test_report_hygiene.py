#!/usr/bin/env python3
"""Każdy raport w `reports/` mówi, KIEDY i NA CZYM mierzono.

Raport bez daty i bez commita jest nieodróżnialny od raportu aktualnego. #86
(`4a03982`) przeliczyło kilometraż stacji i wszystko, co z niego wynika — odległości
międzystacyjne, czasy przejazdu, dolne ograniczenia prędkości. Raporty sprzed tej
poprawki nadal leżą w `reports/` i nadal czytają się jak stan bieżący, bo nic
w nagłówku nie mówi, na jakim drzewie ich liczby powstały. Ta bramka pilnuje tego
jednego: **pola się nie gubią i nie gubią się w NOWYCH raportach**.

CZEGO TA BRAMKA NIE ROBI, ŚWIADOMIE. Nie pilnuje, czy liczby w raporcie są aktualne.
Nie da się z tekstu wyczytać, czy `1339/1339 przeszło` jest zdaniem o stanie bieżącym,
czy **cytatem wyjścia polecenia** z dnia pomiaru — a cytatu nie wolno przeliczać, bo
jego wartością jest właśnie to, że pokazuje, co wyszło tamtego dnia. Bramka, która
podmieniałaby takie liczby zbiorczo, psułaby datowane pomiary; zdarzyło się to w tej
sesji dwa razy (`docs/23-environment.md` §2.3 i pierwsza wersja poprawki
w `reports/R-006-line-speed.md`). Rodziny „nieaktualna liczba podana jako stan
bieżący" poprawia się więc ręcznie, po jednym akapicie, i tak też zostały poprawione.

DLACZEGO SHA NIE JEST SPRAWDZANY NA OSIĄGALNOŚĆ. Sprawdzenie `git cat-file -e`
wyglądałoby mocniej, a byłoby czerwone z dwóch niezależnych powodów. Pierwszy:
`actions/checkout` w tym repozytorium chodzi z domyślnym `fetch-depth: 1` (wyjątkiem
jest `prune-merged-branches.yml`), więc na runnerze prawie żaden commit z historii nie
istnieje jako obiekt. Drugi: squash-merge kasuje commity gałęzi, więc raport, który
poprawnie zapisał SHA swojego przebiegu, po scaleniu wskazuje na obiekt, którego już
nie ma — zmierzone: `reports/mutation-triage-lod.md` podaje `c572eb3` i ten SHA nie
rozwiązuje się w `main`. Taki zapis jest nadal poprawnym zapisem historycznym, a nie
usterką higieny, więc bramka sprawdza **kształt pola, nie osiągalność obiektu**.

DLACZEGO NAGŁÓWEK, A NIE CAŁY PLIK. Data gdziekolwiek w treści nie mówi, kiedy
mierzono — `reports/L1_A-geometry.md` i `reports/M7-in-tunnel.md` wymieniały daty
w środku raportu, a nie miały ani jednej w nagłówku. Skan całego pliku uznawał oba
za datowane. Nagłówkiem jest tu tekst przed pierwszym śródtytułem `## `.

KONTROLE NEGATYWNE — wykonane na kopii `reports/` w katalogu tymczasowym, każda
z wypisanym komunikatem, każda MUSI paść:

  1. zdjęta data z `reports/T-113-timetable.md`
     -> raporty bez daty pomiaru w nagłówku: ['T-113-timetable.md']
  2. zdjęty commit z `reports/network-chainage.md`
     -> raporty bez commita pomiaru w nagłówku: ['network-chainage.md']
  3. katalog raportów wskazany na pusty
     -> bramka przeszła tylko 0 raportów, a w `reports/` jest ich co najmniej 40
        (padają wszystkie cztery testy z licznikiem)
  4. NOWY raport bez daty i bez commita — kontrola odwrotnego kierunku
     -> raporty bez daty pomiaru w nagłówku: ['zzz-nowy-pomiar.md']
     -> raporty bez commita pomiaru w nagłówku: ['zzz-nowy-pomiar.md']
  5. nowy raport bez ani jednego `## `, czyli nagłówek = cały plik
     -> raporty bez śródtytułu `## `, w których nagłówek to cały plik:
        ['zzz-bez-srodtytulu.md']
  6. wyjątek na `R-006-line-speed.md` przestał być potrzebny, a został na liście
     -> R-006-line-speed.md ma już commita w nagłówku — zdejmij go z listy wyjątków
  7. do `NOTATIONS` dopisana notacja, której nie używa żaden raport
     -> notacje daty, których nie używa żaden raport: ['RRRR/MM/DD (nikt nie używa)']
  8. do `NOTATIONS` dopisany wzorzec `.?`, czyli łapiący WSZYSTKO
     -> L1_A-chunks.md: wzorzec daty łapie coś po usunięciu wszystkich dat z nagłówka

  9. pięciu raportom zdjęty SHA i dopisany wyjątek z długim powodem, lista 2 -> 7
     (05.09.2026, `6c1048b`) — PRZED zapadką `MAX_COMMIT_EXCEPTIONS` cały moduł
     przechodził na zielono, PO niej pada dokładnie jeden test, ten
     -> lista wyjątków od commita urosła do 7 przy zapadce 2: ['T-113-timetable.md',
        'T-310-physics.md', 'T-311-braking.md', 'T-312-doors.md', 'T-401-line-run.md']
        ponad limit — raport bez commita ma dostać nagłówek, a nie miejsce na liście
 10. zapadka podniesiona „na zapas" do 3 przy dwóch wyjątkach na liście
     -> zapadka 3 stoi wyżej niż lista (2) — obniż ją do stanu faktycznego

 11. przykład nagłówka w `docs/04-conventions.md` podmieniony na inny kształt
     (07.09.2026, `f684e40a3af52272f9cd1d32d241e9bf3abf644d`) — pada DOKŁADNIE jeden
     test, kod wyjścia 1, 13/14
     -> przykład nagłówka w `docs/04-conventions.md` ma kształt ['**Snapshot na
        commicie:** `<sha>` (`main`, <data>)'] przy kształcie 90 z 135 raportów:
        '**Zmierzone <data> na commicie:** `<sha>`'
 12. śródtytuł o raportach zdjęty z `docs/04-conventions.md`
     -> 11 raportów cytuje `docs/04-conventions.md` (['L1_A-chunks.md',
        'audyt-asercji.md', 'kolejka-uzupelnienie-drugie.md'] …), a plik nie ma ani
        jednego śródtytułu o raportach
     KONTROLA 12 BYŁA ŚLEPA ZA PIERWSZYM PODEJŚCIEM i to jest tu zapisane, bo samo
     zjawisko jest ważniejsze od poprawki: podstawiony śródtytuł brzmiał „Inny temat,
     bez slowa o raportach" i ZAWIERAŁ napis „raport", więc wzorzec go złapał, bramka
     została zielona kodem 0 i wyglądała na sprawdzoną. Dopiero śródtytuł „Inny temat"
     dał czerwień.
 13. PUŁAPKA WCIĘTEGO BLOKU — kontrola, dla której `FENCE` ma `[ \t]*`. Do konwencji
     dopisany DRUGI przykład, zgniły i wcięty pod punktem listy, obok poprawnego
     niewciętego. Wzorzec z `[ \t]*` widzi dwa przykłady i zgłasza zgniły (kod 1);
     wzorzec zakotwiczony na samym grzbiecie widzi jeden i zgłasza ZERO — bramka
     ZIELONA, nie zobaczywszy zgniłego przykładu w pliku
     -> odstające (`FENCE`): 1, kod 1; odstające (`^```` bez `[ \t]*`): 0, kod 0
 14. ZAPADKA `MIN_REPORTS` ZEPSUTA W TRZECH KIERUNKACH (6.D45, 08.09.2026, `a214ab9`,
     153 raporty w katalogu). Wykonane; po każdej mutacji `__pycache__` wyczyszczony,
     bo mutacja tej samej długości bajtowej w tym samym oknie mtime zostawia nieświeży
     `.pyc` — to przypadek z 6.D41. Suma `md5` pliku po każdym przywróceniu ta sama.
     - o jeden W GÓRĘ (154): pada SIEDEM testów — sześć podłóg „skan czyta
       katalog" i sam nowy test, bo nie da się ich spełnić razem z zapadką
       wyprzedzającą katalog
       -> raportów jest 153 przy `MIN_REPORTS` = 154 — któryś raport zniknął
          z `reports/` albo skan przestał go czytać
     - RÓWNO (153): 15/15, kod 0
     - o jeden W DÓŁ (152): pada DOKŁADNIE JEDEN test, ten nowy, 14/15, kod 1
       -> raportów w `reports/` jest 153, a `MIN_REPORTS` stoi na 152 — podnieś ją
          do 153 w tym samym commicie, w którym dopisujesz raport
     - na STARĄ WARTOŚĆ (40), czyli stan przed 6.D45: pada dokładnie ten sam jeden
       test i tym samym zdaniem („podnieś ją do 153"), 14/15, kod 1. PRZED tą zmianą
       ta wartość przechodziła cały moduł na zielono — to jest cała usterka 6.D45
       pokazana z jednej strony.
 15. ZAPADKA `MAX_REPORTS_WITHOUT_FIELD_LINE` ZEPSUTA W OBIE STRONY — para do 14,
     dla podłogi PRZEKIEROWANEJ z `MIN_REPORTS` na stan katalogu.
     - o jeden W GÓRĘ (6): zapas na przyszłe nagłówki bez wiersza pola
       -> zapadka 6 stoi wyżej niż stan (5) — obniż ją do stanu faktycznego
     - o jeden W DÓŁ (4): podłoga podniesiona nad stan
       -> tylko 148 raportów ma wiersz pola z SHA przy 153 w katalogu i zapadce 4 —
          przyrząd przestał czytać nagłówki
 16. PRZYRZĄD, KTÓRY PRZESTAŁ CZYTAĆ CZĘŚĆ NAGŁÓWKÓW — kontrola, dla której to
     przekierowanie w ogóle powstało. `_header_field_line` zawężony z `**` do
     `**Zmierzone`, czyli przestaje widzieć wiersz pola o innej etykiecie:
       -> tylko 140 raportów ma wiersz pola z SHA przy 153 w katalogu i zapadce 5 —
          przyrząd przestał czytać nagłówki (14/15, kod 1)
     Na TYM SAMYM zepsutym przyrządzie stara podłoga `sum(counts) >= MIN_REPORTS`
     przy `MIN_REPORTS = 40` jest **zielona** (140 >= 40) — zmierzone, nie
     przewidziane. Zielona zostaje też kontrola 7 wyżej, bo jej literał zaczyna się
     od `**Zmierzone`. Trzynastu nieczytanych nagłówków nie zobaczyłby więc nikt.

Kontrole 11 i 13 są parą jak 7 i 8, tylko dla przykładu w konwencjach: zapis zgniły
(11) i przyrząd, który zgniłego nie widzi (13). Kontrolę na tekście POPRAWNYM — kształt
zgodny z większością NIE odstaje — nosi w sobie
`test_detektor_przykladu_naglowka_widzi_blok_wciety` (punkty 3 i 4), bo bramka
zapalająca się na dobrym tekście zostaje wyłączona (6.D27).

Kontrole 7 i 8 są parą i pilnują dwóch przeciwnych sposobów, w które ta bramka mogłaby
udawać pomiar: wzorzec martwy (nie łapie nic, więc niczego nie sprawdza) i wzorzec
zbyt szeroki (łapie wszystko, więc każdy raport „ma datę"). Kontrole 9 i 10 są taką
samą parą dla listy wyjątków: lista rosnąca po cichu i miejsce zrobione na zapas.

DLACZEGO WYJĄTKI, A NIE DOPISANE NAGŁÓWKI — to jest wybór, nie przeoczenie. Dwa
raporty commita nie mają i mieć go nie mogą: `R-006-line-speed.md` mierzono PRZED
commitem, który go wniósł, a `T-401-line-run.md` ma sekcje mierzone na różnych
commitach i każda go nazywa u siebie. Dopisanie im wspólnego SHA byłoby dorobieniem
liczby do formularza — `CLAUDE.md` §4.1 — więc wyjątek jest tu uczciwszy od nagłówka.
Cena za to jest jedna: lista wyjątków musi być **zamknięta**, inaczej wyjątek robi się
tańszym wyjściem niż nagłówek. Zamyka ją `MAX_COMMIT_EXCEPTIONS` i kontrola 9.
"""

import os
import re
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS = os.path.join(ROOT, "reports")

#: Data pomiaru w obu notacjach, których ten repozytorium naprawdę używa. Obie są
#: policzone w `test_konwencja_naglowka_...`, więc notacja, której nikt nie stosuje,
#: nie da się tu wpisać jako „prawda o formacie" bez wywrócenia bramki.
NOTATIONS = {
    "ISO (2026-09-02)": re.compile(r'\b20\d\d-\d\d-\d\d\b'),
    "PL (02.09.2026)": re.compile(r'\b\d\d\.\d\d\.20\d\d\b'),
}

#: Commit, na którym mierzono: skrócony lub pełny SHA w grawisach.
#:
#: Pierwsza wersja odsiewała jeszcze napisy z samych cyfr, w obawie że liczba
#: w grawisach — `1339` z „1339/1339 przeszło" — trafi się jako fałszywy SHA. Filtr
#: był zły w obie strony i to jest zmierzone, nie przewidziane. Za krótkie liczby
#: `{7,40}` odsiewa samo; **skrócony SHA potrafi być z samych cyfr** i dwa takie
#: w tym repozytorium są: `4575195` (`reports/T-012-godot-capture.md`) i `1426940`
#: (`reports/T-211-station-layout.md`). Z filtrem oba raporty raportowały brak
#: commita, mając go w nagłówku. Bez filtru fałszywych trafień nie ma ani jednego:
#: przeskan 44 nagłówków daje 43 tokeny i wszystkie są SHA.
#:
#: DŁUGOŚĆ JEST DOKŁADNA (`{7}` lub `{40}`), NIE ZAKRESEM (`{7,40}`) — poprawka
#: 6.D13, znaleziona przy 6.D10. `{7,40}` łapało też `9e2066aef7ef` w nagłówku
#: `reports/T-400-stage-3b.md` — 12 znaków samego hexu, WYGLĄDA jak skrócony SHA
#: i trafia w ten sam wzorzec, ale to hash builda Blendera 5.2.1 LTS, zacytowany
#: w opisie środowiska pomiaru, a nie commit (`reports/commit-naglowka-a-raport.md`
#: §4 opisuje to pierwszy raz; `git cat-file -e` na nim zawodzi, bo obiektu o takiej
#: treści nikt nigdy nie stworzył). Zmierzone 06.09.2026 na całym `reports/` (80
#: plików): wzorzec `{7,40}` łapie w nagłówkach **90** tokenów, a ich długości to
#: `{7: 78, 12: 1, 40: 11}` — **dokładnie jeden** ma długość inną niż 7 albo 40,
#: i to jest właśnie ten token. Pełny werdykt na wszystkich 90:
#: `reports/wzorzec-commita-falszywe-trafienia.md`.
#:
#: Dlaczego zawężenie do zbioru {7, 40}, a nie np. `{7,11}` (odcięcie tuż przed
#: 12) — te dwie liczby nie są arbitralnym cięciem, tylko dwoma jedynymi formami,
#: jakie faktycznie produkuje `git`: `git rev-parse --short` (domyślnie 7 znaków)
#: i `git rev-parse` (40 znaków, pełny SHA-1). Skrócenie do jakiejkolwiek innej
#: długości nie jest czymś, co ten projekt kiedykolwiek robi — zmierzone: w 90
#: tokenach nie ma ANI JEDNEGO w przedziale 8..39 poza tym jednym 12-znakowym,
#: który i tak nie jest commitem. Test `test_wzorzec_commita_lapie_realne_dlugosci_i_nie_lapie_hasza_narzedzia`
#: pilnuje obu stron tego zawężenia: że skrócony i pełny SHA nadal wpadają, i że
#: hash builda Blendera już nie.
COMMIT = re.compile(r'`([0-9a-f]{40}|[0-9a-f]{7})`')

#: Ile raportów musi wpaść do pętli. Bez tego progu wskazanie katalogu na pusty
#: albo literówka w globie dawałyby pustą pętlę i zieloną bramkę.
#:
#: **LICZBA I WARUNEK PRZEPISANE, A NIE DOPISANE OBOK — 6.D45, 08.09.2026.**
#: Poprzednia wersja podawała **48** (zmierzone 05.09.2026 na `6c1048b`) i kończyła
#: się zdaniem „Próg stoi niżej, żeby nie trzeba go było ruszać przy każdym nowym
#: raporcie". To zdanie było całą usterką, a nie wygodą: stała stała na **40**, gdy
#: `reports/` miało **152** pliki `.md` (zmierzone 08.09.2026 na `a214ab9`), czyli
#: **112 pozycji** za katalogiem, którego pilnuje. Warunek `len(items) >= MIN_REPORTS`
#: jest nierównością **bez sufitu**, więc skan mógł przestać czytać 112 ze 152
#: raportów — niemal trzy czwarte katalogu — i przejść na zielono, a odległość
#: między stałą a stanem rosła z każdym dopisanym raportem i nic tego nie widziało.
#:
#: Dziś stała jest **zapadką dwustronną**, dokładnie na wzór `MINIMUM_DETAIL_BLOCKS`
#: z `tools/tests/test_backlog.py`:
#: `test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem` wymaga **równości**
#: z liczbą plików `.md` w `reports/`, więc ani nowy raport nie przechodzi bez
#: podniesienia stałej w tym samym commicie, ani zniknięcie raportu nie przechodzi
#: wcale. Sama podniesiona liczba usterki nie usuwa — bez zmiany warunku odległość
#: odrasta po tygodniu, i to jest powód, dla którego 6.D45 mówi wprost, że zmiana
#: liczby bez zmiany warunku NIE jest wykonaniem pozycji.
#:
#: Nazwa zostaje `MIN_REPORTS`, bo rola podłogi „skan czyta katalog" się nie zmienia
#: i niesie ją **sześć** asercji w sześciu testach: daty, commita, konwencji
#: nagłówka, nagłówka bez śródtytułu, ścieżek i zapisu w konwencjach. Numerów
#: wierszy tu nie ma świadomie — pole „Wejście" pozycji 6.D45 podawało „wiersze 249 i 263",
#: a w dniu wykonania te asercje stały w 334 i 348. Liczba wierszy starzeje się
#: przy każdym dopisanym akapicie; nazwa testu nie. Tak samo `MINIMUM_DETAIL_BLOCKS`
#: nosi przedrostek minimum, będąc pilnowane na równość.
#:
#: Liczba jest POMIAREM, nie wartością zapamiętaną — i ten akapit jest tego
#: dowodem z pierwszej ręki, bo **stała zestarzała się, zanim jej commit trafił
#: do `main`.** Poprzednia wersja tego akapitu podawała:
#:
#:     $ ls reports/*.md | wc -l        # na `a214ab9`
#:     152
#:
#: i wyliczała z tego **153** („152 plus raport, który ten commit dokłada"). Między
#: tym pomiarem a scaleniem gałęzi weszły do `main` trzy pull requesty z własnymi
#: raportami (#413, #414, #415), więc 153 było nieprawdziwe **o trzy** w chwili,
#: w której miało zostać zapisane. Zapadka równościowa nie dała tego przepuścić —
#: i to jest jedyny powód, dla którego ta liczba nie weszła zła. Gdyby warunek
#: został nierównością, jaką był (`>= 40`), 153 przeszłoby bez słowa i różnica
#: rosłaby dalej.
#:
#: **A potem zestarzała się przy KAŻDYM kolejnym raporcie, i to przestało być
#: anegdotą — stało się przewidywalnym kosztem.** Kolejne wartości i to, co je
#: unieważniło:
#:
#:     153  (a214ab9, #416)   -> padła, bo weszły #413, #414, #415 z raportami
#:     156  (e1fcfc1, #416)   -> padła przy 6.D43  reports/pojemnosc-puli-ci.md
#:     157  (1cada00, #417)   -> padła przy 6.D54  reports/wyrocznia-zielonosci-sys-exit.md
#:     158  (4a4f8f2, #418)   -> padła przy 6.D55  reports/znaczniki-konfliktu-bramka.md
#:     159  (3fbc25d, #419)   -> padła przy 6.D56  reports/piata-kopia-progu.md
#:     160  (d51b5df, #420)   -> padła przy 6.D44  reports/kopie-listy-sonames.md
#:     161  (a5aa464, #421)   -> padła przy 6.D57  reports/doctor-sdk-poza-path.md
#:
#: **Siedem razy pod rząd, w ciągu jednego wieczoru, i za każdym razem złapała to
#: zapadka, a nie czyjaś czujność.** Ta lista jest zamknięta: mechanizm jest już
#: pokazany, a kolejne wpisy niosłyby zero nowej informacji — kto podnosi tę stałą
#: po raz szósty, dopisuje wyłącznie liczbę, nie wiersz historii.
#:
#: To jest mocniejszy argument za równością niż pierwotne 112 pozycji różnicy. Sto
#: dwanaście dawało się opowiedzieć jako jedno zaniedbanie do nadgonienia; trzy
#: rozjazdy pod rząd pokazują mechanizm: **stała pilnująca katalogu, który rośnie,
#: starzeje się MIĘDZY napisaniem commita a jego scaleniem** — w okresie, w którym
#: autor już nic nie mierzy, bo uważa zadanie za skończone. Nie ma momentu, w którym
#: dyscyplina po stronie autora miałaby się włączyć. Załatwia to wyłącznie warunek,
#: który rozjazdu nie przepuszcza, i **cena tego warunku (każdy nowy raport wymusza
#: podniesienie stałej oraz poprawienie każdego raportu, który ją cytuje) jest ceną,
#: nie usterką.**
#:
#: Dlatego liczba nie jest tu wyliczana z żadnej innej liczby. Jest odczytana
#: z drzewa, na `6582eea` plus raport tego commita:
#:
#:     $ ls reports/*.md | wc -l
#:     168
#:     $ python3 -c 'import sys; sys.path.insert(0, "tools/tests");
#:       import test_report_hygiene as m; print(len(list(m._reports())))'
#:     168
#:
#: Oba pomiary stoją tu razem świadomie: asercja porównuje z `len(list(_reports()))`,
#: nie z wyjściem `ls`, a te dwa zbiory mogłyby się różnić (glob, katalogi, pliki
#: bez rozszerzenia). Dziś są równe i dopóki są, `ls` wolno używać jako skrótu —
#: rozjazd między nimi byłby osobną usterką, o której ta stała nic nie powie.
#:
#: Kto dopisze następny raport, nie przepisuje tej liczby z pamięci ani z tego
#: akapitu, tylko mierzy ją **na swoim drzewie po scaleniu `main`** — komunikat
#: asercji podaje wynik pomiaru wprost, żeby nie było potrzeby zgadywania.
#:
#: **188 → 189 (09.09.2026, 6.D52).** Jeden raport: `serializacja-jobow-ci.md`.
#: Liczba jest POLICZONA na drzewie po dopisaniu pliku (`ls reports/*.md | wc -l`
#: dało 189), nie przepisana z rozmowy — reguła trzy akapity wyżej obowiązuje
#: tak samo przy jednym raporcie, jak przy czterech.
#: **189 → 190 (09.09.2026, 6.D60).** Jeden raport: `sonda-hostfxr-ladowanie.md`.
#: Liczba znów POLICZONA na drzewie po dopisaniu pliku, nie zwiększona o jeden
#: „bo dopisałem jeden" — to są dwie różne czynności i tylko pierwsza jest pomiarem.
#: **190 → 191 (09.09.2026, 6.D62).** Jeden raport: `pamiec-kafli-osm.md`.
#: Policzona na drzewie, jak dwa akapity wyżej.
#: **207 → 208 (10.09.2026, drugie tego dnia uzupełnienie kolejki).** Jeden raport:
#: `uzupelnienie-kolejki-10-09-druga.md`. Policzona na drzewie (`ls reports/*.md | wc -l`
#: dało 208), nie zwiększona o jeden.
#: **208 → 209 (10.09.2026, 6.D90).** Jeden raport:
#: `6d90-okno-mutacji-a-czyste-drzewo.md`. Policzona na drzewie, jak wyżej.
#: **209 → 210 (10.09.2026, 6.D91).** Jeden raport:
#: `6d91-os-sprawdzana-wobec-kazdej-linii.md`. Policzona na drzewie.
#: **210 → 211 (10.09.2026, 6.D92).** Jeden raport:
#: `6d92-wspolny-odcinek-dwoch-linii.md`. Policzona na drzewie.
#: **211 → 212 (10.09.2026, 6.D93).** Jeden raport:
#: `6d93-czas-przebiegu-jako-artefakt.md`. Policzona na drzewie.
#: **212 → 213 (10.09.2026, 6.D94).** Jeden raport:
#: `6d94-odmowa-nie-znika-pod-O.md`. Policzona na drzewie.
#: **213 → 214 (10.09.2026, 6.D95).** Jeden raport:
#: `6d95-doctor-nazywa-zablokowana-pozycje.md`. Policzona na drzewie.
#: **214 → 215 (10.09.2026, 6.D96).** Jeden raport:
#: `6d96-pin-niespelniony-a-brak-sdk.md`. Policzona na drzewie.
#: **215 → 216 (10.09.2026, 6.D97).** Jeden raport:
#: `6d97-lokalne-filtry-katalogow.md`. Policzona na drzewie.
#: **216 → 217 (10.09.2026, 6.D98).** Jeden raport:
#: `6d98-dwie-formy-chk.md`. Policzona na drzewie.
#: **217 → 218 (10.09.2026, 6.D99).** Jeden raport:
#: `6d99-slowo-a-napis-na-klawiszu.md`. Policzona na drzewie.
#: **218 → 219 (10.09.2026, 6.D100).** Jeden raport:
#: `6d100-heredok-jako-jedna-komenda.md`. Policzona na drzewie.
#: **219 → 220 (10.09.2026, 6.D101).** Jeden raport:
#: `6d101-nazwa-modulu-jako-adres.md`. Policzona na drzewie.
#: **220 → 221 (10.09.2026, 6.D102).** Jeden raport:
#: `6d102-stary-bajtkod-pod-suma-md5.md`. Policzona na drzewie.
#: **221 → 222 (10.09.2026, 6.D103).** Jeden raport:
#: `6d103-galezie-warunkowe-schematu-audio.md`. Policzona na drzewie.
#: **222 → 223 (10.09.2026, 6.D104).** Jeden raport:
#: `6d104-piec-punktow-czego-nie-ma.md`. Policzona na drzewie.
#: **223 → 224 (10.09.2026, 6.D105).** Jeden raport:
#: `6d105-dwie-tabele-statusow.md`. Policzona na drzewie.
#: **224 → 225 (10.09.2026, 6.D106).** Jeden raport:
#: `6d106-nazwy-plikow-tymczasowych-sweepa.md`. Policzona na drzewie.
#: **225 → 226 (10.09.2026, 6.D107).** Jeden raport:
#: `6d107-pietnasty-parametr-hamowania.md`. Policzona na drzewie.
#: **226 → 227 (10.09.2026, 6.D108).** Jeden raport: `6d108-ksztaltu-nie-ma.md`.
#: Pozycja NIE jest zrobiona — raport zapisuje pomiar, z którego wyszło, że kształtu
#: żądanego przez jej pole „Wyjście" nie ma; wybór między trzema mechanizmami jest
#: decyzją właściciela. Policzona na drzewie.
MIN_REPORTS = 309

#: Ile raportów trzyma SHA w nagłówku, ale **nie na wierszu pola** — czyli poza
#: wierszem zaczynającym się od `**`, z którego `_header_shapes` czyta kształt.
#:
#: SKĄD TA STAŁA I DLACZEGO POWSTAJE RAZEM Z 6.D45. Podłogą asercji „przyrząd
#: przestał czytać nagłówki" w `test_zapis_o_naglowku_w_konwencjach_...` było
#: `MIN_REPORTS`. Przy stałej 40 i 147 raportach z wierszem pola ta asercja miała
#: **107 raportów zapasu**: przyrząd mógł przestać czytać sto siedem nagłówków i nie
#: powiedzieć ani słowa. Podniesienie `MIN_REPORTS` do stanu katalogu zapaliłoby ją
#: natychmiast — nie dlatego, że coś jest zepsute, tylko dlatego, że wiersza pola
#: nie ma **pięć** raportów, i to jest prawda o katalogu. Asercja jest więc
#: **przekierowana, a nie poluzowana**: podłoga liczy się od stanu katalogu minus ta
#: zapadka, czyli zapas zszedł ze 107 do zera.
#:
#: ZMIERZONE 08.09.2026 na `a214ab9` — pięć raportów, każdy z powodem widocznym
#: w pliku: `R-006-line-speed.md` i `T-401-line-run.md` nie mają SHA wcale (są
#: w `COMMIT_EXCEPTIONS`, powody stoją tam), a `mutacje-rdzen-sygnalizacji.md`,
#: `mutation-triage-fizyka.md` i `mutation-triage-parametry.md` nazywają commity
#: w **tabeli** przeglądu, nie w wierszu pola.
#:
#: Czego ta zapadka NIE jest, świadomie: bramką na kształt nagłówka. 6.D38 zmierzyło,
#: że takiej być nie może (`reports/ksztalt-naglowka-raportu.md`),
#: a `docs/04-conventions.md` nazywa kształt **zaleceniem, nie wymogiem**. Zapadka
#: nie mówi, JAK wiersz pola ma wyglądać — kształtów jest dziś szesnaście i wszystkie
#: przechodzą. Mówi tylko, że liczba raportów, których przyrząd nie umie przeczytać,
#: nie rośnie **po cichu**: rośnie za cenę podniesienia tej stałej w tym samym
#: commicie, z powodem, tak jak przy tabeli w `mutacje-rdzen-sygnalizacji.md`.
MAX_REPORTS_WITHOUT_FIELD_LINE = 5

#: ZAPADKA NA DŁUGOŚĆ LISTY WYJĄTKÓW. Wolno ją tylko OBNIŻAĆ — jak
#: `MINIMUM_DOCUMENTED_ITEMS` w `tools/tests/test_backlog.py`, tylko w drugą stronę.
#:
#: SKĄD SIĘ WZIĘŁA, ZMIERZONE 05.09.2026 na `6c1048b`. Do tej zmiany lista wyjątków
#: nie miała ŻADNEGO ograniczenia rozmiaru, a jedyny test, który ją pilnował
#: (`test_lista_wyjatkow_nie_gnije`), sprawdza po jednym wpisie — czy powód jest
#: dłuższy niż 40 znaków i czy raport nadal pola nie ma. Wpis, który oba te warunki
#: spełnia, przechodził bez względu na to, ilu takich wpisów już jest. Pomiar: sześciu
#: raportom (`T-310-physics.md`, `T-311-braking.md`, `T-312-doors.md`,
#: `T-113-timetable.md`, `M7-shell.md`, `clearance-BE.md`) zdjęty SHA z nagłówka
#: i dopisany wyjątek z długim powodem — **wszystkie osiem testów tego modułu
#: zostało zielonych**, a lista urosła z 2 do 8. Bramka na „każdy raport niesie
#: commit" umiała więc przestać obejmować raporty jeden po drugim i nie powiedzieć
#: o tym ani słowa.
#:
#: Drugie ostrze tego samego: podłoga w `test_konwencja_naglowka_...` liczyła się
#: jako `MIN_REPORTS - len(COMMIT_EXCEPTIONS)`, czyli **malała o jeden z każdym
#: dopisanym wyjątkiem** (38 przy dwóch, 32 przy ośmiu, −8 przy czterdziestu ośmiu).
#: Dziś liczy się od zapadki, więc dopisanie wyjątku podłogi nie obniża.
MAX_COMMIT_EXCEPTIONS = 2

#: To samo dla daty. Zero jest wynikiem pomiaru — każdy raport datę ma — więc
#: zapadka mówi wprost: pierwszy raport bez daty nie prześlizgnie się przez listę
#: wyjątków, tylko dostanie datę albo zatrzyma bramkę.
MAX_DATE_EXCEPTIONS = 0

#: JAWNE WYJĄTKI OD WYMOGU COMMITA. Każdy z powodem, każdy pilnowany przez
#: `test_lista_wyjatkow_nie_gnije` — wyjątek, który przestał być potrzebny, wywraca
#: bramkę, więc lista nie może po cichu rosnąć ani po cichu zostać. Ilu ich może być,
#: mówi `MAX_COMMIT_EXCEPTIONS` i pilnuje `test_lista_wyjatkow_jest_zamknieta`.
COMMIT_EXCEPTIONS = {
    "R-006-line-speed.md":
        "Raport z 02.09.2026 nie zapisał commita pomiaru w chwili powstania, a dziś "
        "nie da się go ustalić bez zgadywania: wniósł go `78fa1f7`, ale pomiar "
        "wykonano PRZED tym commitem, na drzewie, którego raport nie nazywa. "
        "Wpisanie tam czegokolwiek byłoby dorobieniem liczby do formularza.",
    "T-401-line-run.md":
        "Sekcje tego raportu są mierzone na RÓŻNYCH commitach i każda go nazywa: "
        "§2 na `28e0d82`, §4 na `7d15987` (04.09.2026). Jeden SHA w nagłówku "
        "spłaszczyłby dwa różne pomiary do jednego i mówiłby nieprawdę o jednym "
        "z nich; nagłówek odsyła więc do sekcji, a nie udaje wspólnego commita.",
}

#: Wyjątków od wymogu DATY nie ma i to jest wynik pomiaru, nie założenie: po tej
#: zmianie każdy raport w `reports/` podaje datę w nagłówku.
DATE_EXCEPTIONS = {}


def _reports_in(directory):
    """(nazwa, treść) dla każdego `.md` w KATALOGU, posortowane.

    6.B24: wydzielone z `_reports()` tak, żeby kontrola regresyjna niżej mogła
    zawołać dokładnie tę samą funkcję nad katalogiem tymczasowym zamiast nad
    `reports/` — bez mutowania żadnego prawdziwego raportu.
    """
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as handle:
            yield name, handle.read()


def _reports():
    """(nazwa, treść) dla każdego raportu w `reports/`, posortowane."""
    yield from _reports_in(REPORTS)


def _header(text):
    """Tekst przed pierwszym śródtytułem `## ` — tam stoi nagłówek raportu."""
    match = re.search(r'^## ', text, re.M)
    return text[:match.start()] if match else text


def _dates(header):
    return [raw for pattern in NOTATIONS.values() for raw in pattern.findall(header)]


def _commits(header):
    return COMMIT.findall(header)


def _date_offenders(items, exceptions=frozenset()):
    """Raporty z `items` (nazwa, treść) bez daty pomiaru w nagłówku.

    6.B24: rdzeń `test_kazdy_raport_podaje_date_pomiaru`, wydzielony tak, żeby
    kontrola regresyjna niżej mogła zawołać dokładnie tę funkcję nad raportami
    wstrzykniętymi w katalogu tymczasowym.
    """
    return [name for name, text in items
            if name not in exceptions and not _dates(_header(text))]


def _commit_offenders(items, exceptions=frozenset()):
    """To samo dla commita — rdzeń `test_kazdy_raport_podaje_commit_na_ktorym_mierzono`."""
    return [name for name, text in items
            if name not in exceptions and not _commits(_header(text))]


def _no_subheading_offenders(items):
    """Raporty bez ani jednego śródtytułu `## ` — nagłówek równy całemu plikowi.

    Rdzeń `test_data_i_commit_stoja_w_naglowku_a_nie_gdziekolwiek_w_raporcie`.
    """
    return [name for name, text in items if len(_header(text)) >= len(text)]


def test_kazdy_raport_podaje_date_pomiaru():
    """Data gdziekolwiek w treści nie mówi, kiedy mierzono — musi być w nagłówku."""
    items = list(_reports())
    missing = _date_offenders(items, DATE_EXCEPTIONS)
    assert not missing, f"raporty bez daty pomiaru w nagłówku: {missing}"
    assert len(items) >= MIN_REPORTS, (
        f"bramka przeszła tylko {len(items)} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")


def test_kazdy_raport_podaje_commit_na_ktorym_mierzono():
    """Bez SHA nie da się odtworzyć drzewa, na którym liczby powstały.

    Mutacja, która przed tą bramką przechodziła całą suitę: skasowanie linii
    `**Zmierzone na commicie:**` z dowolnego z 32 raportów, które ją dostały.
    """
    items = list(_reports())
    missing = _commit_offenders(items, COMMIT_EXCEPTIONS)
    assert not missing, f"raporty bez commita pomiaru w nagłówku: {missing}"
    assert len(items) >= MIN_REPORTS, (
        f"bramka przeszła tylko {len(items)} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")


def test_konwencja_naglowka_jest_wyczytana_z_raportow_ktore_ja_juz_maja():
    """Bramka nie trzyma DRUGIEJ LISTY tego, jak wygląda nagłówek.

    Prawdę o formacie bierze z raportów, które datę i commit już mają, i sprawdza
    na nich dwie rzeczy naraz:

    - każda notacja daty, którą bramka zna, jest przez jakiś raport UŻYWANA — notacja
      martwa udawałaby prawdę o formacie, nie będąc nią;
    - usunięcie pola z prawdziwego nagłówka **przestaje przechodzić** kontrolę. To jest
      kontrola negatywna wpisana w bramkę: wzorzec, który łapie wszystko, wywraca ten
      test, a wzorzec, który nie łapie nic, wywraca dwa poprzednie.
    """
    usage = {label: 0 for label in NOTATIONS}
    reference = []
    checked = 0
    for name, text in _reports():
        checked += 1
        header = _header(text)
        for label, pattern in NOTATIONS.items():
            if pattern.search(header):
                usage[label] += 1
        if _dates(header) and _commits(header):
            reference.append((name, header))
    assert checked >= MIN_REPORTS, f"tylko {checked} raportów w pętli"
    unused = [label for label, count in usage.items() if count == 0]
    assert not unused, f"notacje daty, których nie używa żaden raport: {unused}"
    # PODŁOGA LICZY SIĘ OD ZAPADKI, NIE OD DŁUGOŚCI LISTY. Z `len(COMMIT_EXCEPTIONS)`
    # malała o jeden przy każdym dopisanym wyjątku, czyli sama sobie ustępowała:
    # zmierzone 05.09.2026 — 38 przy dwóch wyjątkach, 32 przy ośmiu.
    assert len(reference) >= MIN_REPORTS - MAX_COMMIT_EXCEPTIONS, (
        f"tylko {len(reference)} raportów ma oba pola — konwencja, którą bramka "
        "czyta z repozytorium, przestała być konwencją")
    for name, header in reference:
        bez_daty = header
        for pattern in NOTATIONS.values():
            bez_daty = pattern.sub("", bez_daty)
        assert not _dates(bez_daty), (
            f"{name}: wzorzec daty łapie coś po usunięciu wszystkich dat z nagłówka")
        assert not _commits(COMMIT.sub("", header)), (
            f"{name}: wzorzec commita łapie coś po usunięciu wszystkich SHA")


def test_wzorzec_commita_lapie_realne_dlugosci_i_nie_lapie_hasza_narzedzia():
    """Kontrola detektora dla 6.D13 — para w obie strony, jak dla wzorca ścieżki.

    `9e2066aef7ef` (hash builda Blendera w nagłówku `T-400-stage-3b.md`) jest
    sam hexem, w grawisach, długości 12 — nierozróżnialny od SHA samą treścią.
    Jedyny sygnał, na którym da się to rozstrzygnąć bez zgadywania semantyki
    zdania, to długość: ten projekt cytuje commity WYŁĄCZNIE jako skrócone (7)
    albo pełne (40) SHA — zmierzone na wszystkich 90 tokenach w `reports/`,
    zobacz `reports/wzorzec-commita-falszywe-trafienia.md`. Test pilnuje, żeby
    zawężenie z `{7,40}` (zakres) do `{7}`/`{40}` (dokładne długości) złapało
    TYLKO ten jeden fałszywy przypadek, a nie zamieniło wzorzec w martwy.
    """
    # 1. Skrócony SHA (7 znaków) — najczęstsza forma w tym repo (78/90 tokenów).
    assert COMMIT.findall("**Zmierzone na commicie:** `619b179`") == ["619b179"]
    # 2. Pełny SHA (40 znaków) — druga realna forma (11/90 tokenów).
    pelny = "fc5db5ff09eb3257e18ac6d8aaa7c5811f32fa18"
    assert COMMIT.findall(f"scalone na `{pelny}`") == [pelny]
    # 3. KONTROLA NEGATYWNA — token, który wywołał tę poprawkę. Sam hex, w
    #    grawisach, 12 znaków: dokładnie ta postać, którą stary wzorzec `{7,40}`
    #    łapał jako SHA. Musi PRZESTAĆ być łapany.
    assert COMMIT.findall(
        "Blender **5.2.1 LTS** (hash `9e2066aef7ef`)") == []
    # 4. Wzorzec nie stał się martwy w drugą stronę: długość spoza {7, 40}, ale
    #    NIE 12 (żeby nie było to zawężenie „na jeden token"), też odpada —
    #    zawężenie jest do dwóch długości, nie do wykluczenia jednej.
    assert COMMIT.findall("build `abc1234567890abcdef`") == []  # 20 znaków
    # 5. Sam stary wzorzec `{7,40}` (zakres) łapał token z kontroli 3 — to jest
    #    DOWÓD, że problem istniał, nie tylko twierdzenie o nim.
    stary_wzorzec = re.compile(r'`([0-9a-f]{7,40})`')
    assert stary_wzorzec.findall(
        "Blender **5.2.1 LTS** (hash `9e2066aef7ef`)") == ["9e2066aef7ef"]


def test_data_i_commit_stoja_w_naglowku_a_nie_gdziekolwiek_w_raporcie():
    """Nagłówek musi być WĘŻSZY niż plik, inaczej bramka cicho robi się skanem całości.

    Raport bez ani jednego śródtytułu `## ` daje nagłówek równy całej treści —
    i wtedy data wspomniana w §9 „co zauważyłem" liczyłaby się jak data pomiaru.
    """
    items = list(_reports())
    bez_srodtytulu = _no_subheading_offenders(items)
    assert not bez_srodtytulu, (
        f"raporty bez śródtytułu `## `, w których nagłówek to cały plik: "
        f"{bez_srodtytulu}")
    assert len(items) >= MIN_REPORTS, f"tylko {len(items)} raportów w pętli"


def test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem():
    """`MIN_REPORTS` ma nadążać za `reports/` — 6.D45.

    **SKĄD, ZMIERZONE 08.09.2026 na `a214ab9`.** Stała mówiła **40**, a katalog miał
    **152** pliki `.md`. Sześć asercji w sześciu testach tego modułu używa jej jako
    podłogi „skan czyta katalog", a każda z tych podłóg jest nierównością **bez
    sufitu** — więc skan mógł przestać czytać **112** raportów i przejść na zielono.
    Zapadka, która stoi sto pozycji za stanem, chroni w takim samym stopniu jak jej
    brak.

    **Dlaczego samo podniesienie liczby nie jest wykonaniem tej pozycji.** Odległość
    między stałą a katalogiem rośnie z każdym dopisanym raportem, bo nierówność ją
    dopuszcza. Bez zmiany warunku ta sama usterka wraca po tygodniu i wygląda wtedy
    dokładnie tak samo. Rozstrzyga to porównanie z rodziną, która tego nie ma:
    `MINIMUM_DETAIL_BLOCKS` w `tools/tests/test_backlog.py` jest pilnowane na
    **równość** i dlatego nie da się jej przespać — każdy nowy blok wywraca zestaw,
    dopóki stała nie pójdzie w górę, w tym samym commicie.

    Wzorem jest więc `test_the_documented_ratchet_does_not_lag_behind_the_file`:
    dwie asercje, dwa różne kierunki rozjazdu, dwa różne zdania. Pierwsza wywraca
    zestaw, gdy raportów jest WIĘCEJ niż stała (zapadka została z tyłu), druga — gdy
    MNIEJ (raport zniknął albo skan przestał go czytać). Kontrole obu kierunków
    wykonane, wypisane w `reports/zapadka-liczby-raportow.md` §4.
    """
    items = list(_reports())
    assert MIN_REPORTS >= len(items), (
        f"raportów w `reports/` jest {len(items)}, a `MIN_REPORTS` stoi na "
        f"{MIN_REPORTS} — podnieś ją do {len(items)} w tym samym commicie, w którym "
        "dopisujesz raport; zapadka, która została z tyłu, zwalnia skan z czytania "
        "różnicy")
    assert len(items) >= MIN_REPORTS, (
        f"raportów jest {len(items)} przy `MIN_REPORTS` = {MIN_REPORTS} — któryś "
        "raport zniknął z `reports/` albo skan przestał go czytać")


def test_missing_date_commit_and_subheading_offenders_light_up_on_injected_reports():
    """Kontrola regresyjna 6.B24 dla trzech bramek wyżej — katalog tymczasowy, nie `reports/`.

    Docstring modułu (KONTROLE NEGATYWNE, punkty 1, 2 i 5) opisuje kontrole
    wykonane NAPRAWDĘ — na kopii `reports/` w katalogu tymczasowym — ale jako
    dowód historyczny jednego przebiegu, a nie test uruchamiany przy KAŻDYM
    przebiegu. Ten test woła DOKŁADNIE `_date_offenders`, `_commit_offenders`
    i `_no_subheading_offenders` — te same funkcje, na których stoją bramki
    wyżej — nad czterema `.md` napisanymi tutaj do świeżego `tempfile
    .TemporaryDirectory()`, przez `_reports_in()`. Żaden plik w `reports/` nie
    jest dotykany.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        with open(os.path.join(tmp_dir, "czysty.md"), "w", encoding="utf-8") as h:
            h.write("Zmierzone: 2026-09-06.\n\n"
                    "**Zmierzone na commicie:** `abc1234`\n\n"
                    "## Sekcja\n\ntreść.\n")
        with open(os.path.join(tmp_dir, "bez-daty.md"), "w", encoding="utf-8") as h:
            h.write("**Zmierzone na commicie:** `abc1234`\n\n## Sekcja\n\ntreść.\n")
        with open(os.path.join(tmp_dir, "bez-commita.md"), "w", encoding="utf-8") as h:
            h.write("Zmierzone: 2026-09-06.\n\n## Sekcja\n\ntreść.\n")
        with open(os.path.join(tmp_dir, "bez-srodtytulu.md"), "w", encoding="utf-8") as h:
            h.write("Zmierzone: 2026-09-06. **Zmierzone na commicie:** `abc1234` "
                     "treść bez ani jednego śródtytułu w całym pliku.\n")

        items = list(_reports_in(tmp_dir))
        assert len(items) == 4, items

        assert _date_offenders(items) == ["bez-daty.md"]
        assert _commit_offenders(items) == ["bez-commita.md"]
        assert _no_subheading_offenders(items) == ["bez-srodtytulu.md"]

        # ten sam raport z wyjątkiem przestaje być offenderem — jak dla
        # prawdziwych COMMIT_EXCEPTIONS/DATE_EXCEPTIONS wyżej.
        assert _date_offenders(items, exceptions={"bez-daty.md"}) == []
        assert _commit_offenders(items, exceptions={"bez-commita.md"}) == []

        # kontrola w drugą stronę: czysty raport nie zapala żadnej z trzech bramek.
        assert "czysty.md" not in _date_offenders(items)
        assert "czysty.md" not in _commit_offenders(items)
        assert "czysty.md" not in _no_subheading_offenders(items)


def test_lista_wyjatkow_nie_gnije():
    """Wyjątek, który przestał być potrzebny, musi z listy ZNIKNĄĆ.

    Bez tego testu lista wyjątków jest miejscem, w którym raport bez nagłówka
    przeżywa na zawsze: dopisanie się na nią kosztuje jedną linijkę, a zdjęcie
    z niej nie kosztuje nic, więc nikt tego nie robi.
    """
    existing = {name for name, _text in _reports()}
    checked = 0
    for table, reader, what in ((COMMIT_EXCEPTIONS, _commits, "commita"),
                                (DATE_EXCEPTIONS, _dates, "daty")):
        for name, reason in table.items():
            checked += 1
            assert name in existing, f"wyjątek na {name} — takiego raportu nie ma"
            assert len(reason) > 40, f"wyjątek na {name} bez powodu: {reason!r}"
            # POWÓD NIE MOŻE OBIECYWAĆ WŁASNEGO USUNIĘCIA, i to jest usterka
            # zmierzona na tej bramce, nie ostrożność. Oba pierwotne wyjątki brzmiały
            # „gałąź w locie przepisuje ten nagłówek, wyjątek do zdjęcia po scaleniu".
            # Gałąź (#195) scaliła się 04.09.2026 — a asercja niżej sprawdza tylko,
            # czy plik JUŻ MA pole. Nie ma, bo nikt go nie dopisał, więc wyjątek
            # zostawał uzasadniony na zawsze przez powód, który dawno wygasł.
            # Bramka nie umie dopilnować obietnicy, więc jej nie przyjmuje: powód
            # musi opisywać stan TRWAŁY, taki jak „raport nie zapisał commita
            # i nie da się go dziś ustalić" albo „sekcje mierzono na różnych".
            obietnice = ("po scaleniu", "do zdjęcia", "w locie", "gałęzi w locie",
                         "tymczasow", "na razie", "docelowo")
            znalezione = [f for f in obietnice if f in reason.lower()]
            assert not znalezione, (
                f"wyjątek na {name} uzasadnia się obietnicą {znalezione} — bramka nie "
                "umie sprawdzić, czy obietnica została dotrzymana, więc powód musi "
                "opisywać stan trwały")
            with open(os.path.join(REPORTS, name), encoding="utf-8") as handle:
                header = _header(handle.read())
            assert not reader(header), (
                f"{name} ma już {what} w nagłówku — zdejmij go z listy wyjątków")
    assert checked == len(COMMIT_EXCEPTIONS) + len(DATE_EXCEPTIONS)


def test_lista_wyjatkow_jest_zamknieta():
    """Lista wyjątków ma ROZMIAR, nie tylko wpisy — inaczej rośnie po cichu.

    `test_lista_wyjatkow_nie_gnije` ogląda każdy wpis OSOBNO: powód dłuższy niż 40
    znaków, bez obietnicy własnego usunięcia, raport nadal bez pola. Wpis spełniający
    te trzy warunki przechodził niezależnie od tego, ilu takich wpisów już jest —
    a wyjątek jest tańszy niż nagłówek, więc lista rośnie w jedną stronę z definicji.

    KONTROLA NEGATYWNA WYKONANA 05.09.2026 na `6c1048b`: pięciu raportom zdjęty SHA
    z nagłówka i dopisany wyjątek z długim powodem, lista 2 -> 7. PRZED tą zapadką
    komplet testów modułu był zielony przy takiej mutacji — zmierzone, nie
    przewidziane. PO niej pada ten jeden test i tylko on:

        lista wyjątków od commita urosła do 7 przy zapadce 2: ['T-113-timetable.md',
        'T-310-physics.md', 'T-311-braking.md', 'T-312-doors.md', 'T-401-line-run.md']
        ponad limit — raport bez commita ma dostać nagłówek, a nie miejsce na liście

    Zapadkę wolno tylko OBNIŻAĆ. Podniesienie jej jest widoczną zmianą stałej w diffie
    i wymaga powodu tam, gdzie powody tego repozytorium stoją — w treści commita —
    a nie jednej dopisanej linijki w słowniku.
    """
    assert len(COMMIT_EXCEPTIONS) <= MAX_COMMIT_EXCEPTIONS, (
        f"lista wyjątków od commita urosła do {len(COMMIT_EXCEPTIONS)} przy zapadce "
        f"{MAX_COMMIT_EXCEPTIONS}: {sorted(COMMIT_EXCEPTIONS)[MAX_COMMIT_EXCEPTIONS:]} "
        "ponad limit — raport bez commita ma dostać nagłówek, a nie miejsce na liście")
    assert len(DATE_EXCEPTIONS) <= MAX_DATE_EXCEPTIONS, (
        f"lista wyjątków od daty urosła do {len(DATE_EXCEPTIONS)} przy zapadce "
        f"{MAX_DATE_EXCEPTIONS}: {sorted(DATE_EXCEPTIONS)} — daty da się ustalić "
        "dla każdego raportu, więc wyjątku od niej nie ma")
    # ZAPADKA NIE MOŻE STAĆ WYŻEJ, NIŻ POTRZEBA. Gdyby wolno jej było wyprzedzać
    # listę, podniesienie „na zapas" otwierałoby miejsce na przyszłe wyjątki bez
    # ani jednego raportu, który by ich potrzebował — czyli dokładnie ta cicha
    # rezerwa, której ta bramka ma nie dopuszczać.
    assert MAX_COMMIT_EXCEPTIONS == len(COMMIT_EXCEPTIONS), (
        f"zapadka {MAX_COMMIT_EXCEPTIONS} stoi wyżej niż lista "
        f"({len(COMMIT_EXCEPTIONS)}) — obniż ją do stanu faktycznego")
    assert MAX_DATE_EXCEPTIONS == len(DATE_EXCEPTIONS), (
        f"zapadka {MAX_DATE_EXCEPTIONS} stoi wyżej niż lista "
        f"({len(DATE_EXCEPTIONS)}) — obniż ją do stanu faktycznego")
    # Podłoga w `test_konwencja_naglowka_...` liczy się od zapadki, więc zapadka
    # równa MIN_REPORTS zdjęłaby tamtą kontrolę do zera. Ten limit mówi, że wyjątek
    # jest wyjątkiem: najwyżej co dziesiąty raport przy dzisiejszym progu.
    assert MAX_COMMIT_EXCEPTIONS + MAX_DATE_EXCEPTIONS <= MIN_REPORTS // 10, (
        f"zapadki wyjątków ({MAX_COMMIT_EXCEPTIONS} + {MAX_DATE_EXCEPTIONS}) sięgają "
        f"dziesiątej części progu {MIN_REPORTS} — wyjątek przestaje być wyjątkiem")


# --- ścieżka w raporcie musi wskazywać na plik, który istnieje --------------------

#: DLACZEGO TO JEST W TYM MODULE, A NIE NOWY.
#:
#: Docstring wyżej mówi, czego ta bramka świadomie NIE robi: nie pilnuje, czy liczby
#: w raporcie są aktualne, bo z tekstu nie da się odróżnić cytatu wyjścia polecenia od
#: zdania o stanie bieżącym. **Ścieżka nie jest liczbą i tej dwuznaczności nie ma.**
#: `src/Sim/Line/LineDrive.cs` albo się rozwiązuje, albo nie, i sprawdza to system
#: plików, a nie druga lista w teście.
#:
#: SKĄD SIĘ WZIĘŁO. Zmierzone 05.09.2026 na `9f4ae98`, skan 48 raportów: dokładnie
#: jedna ścieżka nie rozwiązywała się w drzewie — `reports/T-400-stage-3b.md` §1
#: wymieniało w tabeli zmian `src/Sim/Line/LineDrive.cs`, podczas gdy plik od chwili
#: powstania (`90a8c31`, T-320) leży w `src/Sim/Train/`. `git log --follow` nie
#: pokazuje ani jednego przeniesienia, więc nie jest to zapis historyczny — to była
#: literówka, prawdziwa już w dniu pomiaru, i przeżyła przegląd PR-a, bo nazwa pliku
#: się zgadzała, a katalog wyglądał sensownie (`Line/` obok `LineDrive`).
#:
#: DLACZEGO SYGNAŁ JEST CZYSTY. Jedno trafienie na 48 plików i ~1500 tokenów w
#: grawisach. Wzorzec bierze wyłącznie tokeny z ukośnikiem i ze znanym rozszerzeniem,
#: więc `sweep.max_deviation` czy `docs/24` przez niego nie przechodzą.
#: MARTWE POLE ZDJĘTE 09.09.2026 (6.D59) — wzorzec PRZEPISANY, nie dopisany obok.
#: Poprzednia wersja startowała token znakiem z `[A-Za-z0-9_]`, więc ścieżka
#: zaczynająca się KROPKĄ nie wchodziła do skanu wcale. Zmierzone: **26 wzmianek
#: w 18 raportach**, wszystkie pod `.github/`, były dla bramki niewidzialne — i to
#: w bramce, której jedynym zadaniem jest łapanie odsyłaczy w puste miejsce. Każda
#: z tych 26 rozwiązuje się dziś w drzewie, więc pozycja nie naprawiła usterki
#: w raportach, tylko PRZYRZĄD, który jej nie umiał zobaczyć.
#:
#: Kropka jest dopuszczona TYLKO przed nazwą katalogu (`(?=[A-Za-z0-9_]+/)`), więc
#: `.gitignore` i `.plik.md` nadal nie wchodzą: dotfile bez katalogu nie jest
#: ścieżką repozytoryjną, którą ta bramka umie sprawdzić.
PATH_TOKEN = re.compile(r'`((?:\.(?=[A-Za-z0-9_]+/))?[A-Za-z0-9_][A-Za-z0-9_./-]*\.'
                        r'(?:py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv))`')

#: ILE ŚCIEŻEK NA RAPORT musi znaleźć wzorzec. Nie jest to stała porównywana
#: z `seen` wprost — mnoży się przez liczbę PRZECZYTANYCH raportów, więc podłoga
#: rośnie razem z katalogiem i nie ma czego podnosić przy nowym raporcie.
#:
#: SKĄD 5 — AKAPIT PRZEPISANY 12.09.2026, A NIE DOPISANY OBOK. Do tego dnia stało
#: tu 6, z rachunkiem z 09.09.2026 (`c8fb583`, 162 raporty, 1466 trafień, 9,05 na
#: raport). Brzeg od góry zaczerwienił się przy 288 raportach: 2012 trafień wobec
#: 2016 wymaganych, czyli **6,99** ścieżki na raport przy podłodze żądającej 7.
#:
#: Oba brzegi liczy z drzewa `test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami`,
#: więc nie ma tu liczby, która mogłaby zostać z tyłu. Zmierzone 12.09.2026 na 288
#: raportach:
#:   od dołu  — zawężenie kontrolne (`ROZSZERZENIE_KONTROLNE` = `md`, 699 trafień)
#:              zbija stosunek do **4,56**, więc 5 je łapie, a 4 już nie;
#:   od góry  — podłoga musi stać co najmniej jedną PEŁNĄ ścieżkę na raport pod
#:              dzisiejszym stosunkiem (`seen >= checked * (K + 1)`): 5 zostawia
#:              zapas 572 trafień, 6 już się nie mieści.
#: Przedział mieszczący się w obu brzegach to dziś **{5}** — JEDNA WARTOŚĆ, a nie
#: {6, 7, 8} jak 09.09.2026. Wyboru trwałości nie ma i to jest treść, nie brak:
#: podłoga stosunkowa ma tyle miejsca, ile daje jej stosunek, a ten spadł z 9,05
#: do 6,99, bo katalog urósł ze 162 raportów do 288.
#:
#: DLACZEGO STOSUNEK SPADŁ, MIMO ŻE ŚWIEŻE RAPORTY SĄ GĘSTSZE OD ŚREDNIEJ.
#: Ostatnie 50 dodanych ma **9,06** ścieżki na raport, ostatnie 30 — **8,00**,
#: czyli powyżej całego katalogu. Spadek bierze się stąd, że 09.09.2026 średnią
#: podbijały raporty najstarsze (pierwsze 50: 15,14), a ich udział w katalogu
#: maleje z każdym nowym. Podłoga stosunkowa NIE starzeje się więc od chudnięcia
#: raportów, tylko od rozcieńczania ogona grubych.
#:
#: TRWAŁOŚĆ NOWEJ WARTOŚCI, zmierzona tym samym rachunkiem: przy gęstości 5,11
#: (najchudszy dobrze obsadzony dzień, 02.09.2026, n=9) brzeg od góry zaczerwieni
#: się po **319** raportach, przy 5,0 — po 284, przy 4,0 — po 142, a przy 6,0
#: i wyżej NIGDY. Dla 6 każda z tych gęstości daje „już teraz", co jest dokładnie
#: powodem tej zmiany.
#:
#: KIERUNEK W GÓRĘ NIE DAJE FAIL i to jest zmierzony wynik, nie luka w boksowaniu:
#: przy 6 brzeg od góry pada, więc jedynym kierunkiem z miejscem jest dół. Pole
#: „Skończone, gdy" pozycji 6.D58 żądało trójki FAIL/zielono/FAIL, bo było pisane
#: dla zapadki RÓWNOŚCIOWEJ; podłoga stosunkowa ma z natury jeden brzeg twardy
#: i jeden z zapasem. Powód i rachunek stoją w `reports/podloga-sciezek-na-raport.md`
#: oraz — dla tej zmiany — w `reports/6d179-koniec-pakietu-i-usterka-czytnika.md` §6.
SCIEZEK_NA_RAPORT_MIN = 5

#: Rozszerzenie, którego zdjęcie ze wzorca jest ZAWĘŻENIEM KONTROLNYM dla podłogi
#: wyżej: najprawdopodobniejszy realny dryf (ktoś zacieśnia wzorzec „do plików
#: kodu") i druga co do wielkości klasa trafień — 561 z 1466, zmierzone
#: 09.09.2026. Stosunek po jego zdjęciu przelicza się w czasie testu.
ROZSZERZENIE_KONTROLNE = "md"

#: ROZSZERZENIA PILNOWANE — kopia alternatywy z `PATH_TOKEN`, i kopia UMYŚLNA.
#: Bramka pokrycia nie może czytać listy z samego wzorca: zdjęcie `md` z wzorca
#: zdjęłoby `md` także z listy do sprawdzenia, więc bramka byłaby ZIELONA nad
#: dokładnie tą usterką, którą ma łapać. To ta sama rodzina, którą 6.D54, 6.D55
#: i 6.D56 zmierzyły trzy razy pod rząd na świeżo napisanych bramkach.
#: Zgodność tej kopii ze wzorcem pilnuje asercja RÓWNOŚCIOWA w
#: `test_zestaw_rozszerzen_w_kodzie_i_we_wzorcu_JEST_TEN_SAM` — kopia bez bramki
#: na zgodność jest gorsza niż brak kopii (6.D44).
ROZSZERZENIA_PILNOWANE = ("py", "cs", "md", "json", "sh", "yml", "yaml", "txt",
                          "csproj", "tscn", "geojson", "csv")

#: Rozszerzenia ze wzorca, które DZIŚ nie mają w raportach ani jednego trafienia,
#: z powodem przy każdym. Zmierzone 09.09.2026 na `c8fb583`. Wpis tutaj znaczy
#: „wiem, że pokrycia nie ma", a nie „nie sprawdzaj": test żąda od każdego wpisu
#: ZERA trafień, więc pierwsza policzona ścieżka `.yml` zaczerwieni zestaw i każe
#: wpis zdjąć. Bez tej drugiej strony lista gniłaby po cichu, dokładnie tak jak
#: `COMMIT_EXCEPTIONS` bez `test_lista_wyjatkow_nie_gnije`.
ROZSZERZENIA_BEZ_TRAFIEN = {
    "yaml": "w drzewie nie ma ani jednego pliku `.yaml` (`git ls-files '*.yaml'` "
            "daje 0); rozszerzenie stoi we wzorcu, bo YAML dopuszcza oba zapisy",
    "geojson": "w drzewie nie ma ani jednego pliku `.geojson`, więc raport nie "
               "miałby czego wymienić",
}

#: Przedrostki, których nie ma po co sprawdzać: wytwory przebiegu (reguła 8 zabrania
#: ich komitować, więc ich BRAK jest stanem poprawnym), ścieżki Godota, katalogi
#: tymczasowe i adresy.
IGNORED_PREFIXES = ("build/", "renders/", "res://", "/tmp/", "http://", "https://",
                    "/opt/", "/usr/", "~/")

#: JAWNE WYJĄTKI: ścieżki, które w raporcie stoją słusznie, choć w drzewie ich nie ma.
#: Pusto — i to jest wynik pomiaru, nie założenie. Gdy pierwszy raport będzie musiał
#: nazwać plik skasowany albo przemianowany, wyjątek wchodzi tutaj z powodem, tak samo
#: jak `COMMIT_EXCEPTIONS` wyżej, i tak samo pilnowany przez test „nie gnije".
PATH_EXCEPTIONS = {}


def _paths_in(text, pattern=PATH_TOKEN):
    """Ścieżki repozytoryjne wymienione w grawisach: `(token, numer wiersza)`.

    `pattern` jest wejściem, bo boksowanie podłogi i bramka pokrycia mierzą
    ten sam katalog wzorcem ZAWĘŻONYM. Drugi czytnik z własną kopią warunku
    `IGNORED_PREFIXES` rozjechałby się z tym przy pierwszej zmianie (6.D44).
    """
    for number, line in enumerate(text.splitlines(), 1):
        for token in pattern.findall(line):
            if "/" not in token or token.startswith(IGNORED_PREFIXES):
                continue
            yield token, number


def test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie():
    """Raport, który nazywa nieistniejący plik, wysyła czytelnika w puste miejsce.

    Kontrola negatywna WYKONANA 05.09.2026, na kopii katalogu w `/tmp` (opis metody
    niżej, w teście detektora): po przywróceniu w `reports/T-400-stage-3b.md`
    poprzedniego zapisu `src/Sim/Line/LineDrive.cs` ten test pada komunikatem

        ścieżki, których nie ma w drzewie:
        ['T-400-stage-3b.md:92: `src/Sim/Line/LineDrive.cs`']
    """
    missing = []
    checked = 0
    seen = 0
    for name, text in _reports():
        checked += 1
        for token, number in _paths_in(text):
            seen += 1
            if token in PATH_EXCEPTIONS:
                continue
            if not os.path.exists(os.path.join(ROOT, token)):
                missing.append(f"{name}:{number}: `{token}`")
    assert not missing, f"ścieżki, których nie ma w drzewie: {missing}"
    assert checked >= MIN_REPORTS, (
        f"bramka przeszła tylko {checked} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")
    # PODŁOGA PRZELICZANA Z LICZBY RAPORTÓW, NIE STAŁA — 6.D58, 09.09.2026.
    #
    # Poprzednia wersja brzmiała `assert seen >= 500` i kończyła się zdaniem „próg
    # stoi niżej, żeby nie trzeba go było ruszać przy każdym nowym raporcie". To
    # zdanie było całą usterką: przy 1466 trafieniach w 162 raportach zapas wynosił
    # **966**, czyli wzorzec mógł przestać łapać **65,9 %** ścieżek i przejść.
    # Co gorsza stała SŁABŁA z każdym raportem — 500 to dziś 3,09 ścieżki na raport,
    # a przy 300 raportach byłoby 1,67.
    #
    # Zmierzone 09.09.2026 na `c8fb583` przez ZAWĘŻANIE wzorca — liczby, których
    # żądało pole „Weryfikacja" tej pozycji:
    #
    #   wzorzec                     seen   stara >=500   nowa >= checked*6
    #   pełny (12 rozszerzeń)       1466     ZIELONA          zielona
    #   bez .md (11)                 905     ZIELONA          CZERWONA
    #   bez .py (11)                 869     ZIELONA          CZERWONA
    #   tylko .py                    597     ZIELONA          CZERWONA
    #   tylko .csv                     4    czerwona          CZERWONA
    #
    # Stara podłoga nie łapała ANI JEDNEGO zawężenia poza absurdalnym.
    #
    # DLACZEGO STOSUNEK, A NIE RÓWNOŚĆ — odstępstwo od pola „Wyjście" tej pozycji,
    # z powodu zmierzonego, nie z wygody. Pole żądało zapadki równościowej na `seen`,
    # wzorem `MIN_REPORTS` z 6.D45. Ale `seen` rośnie przy KAŻDEJ wzmiance o pliku
    # w prozie dowolnego raportu, nie przy dopisaniu raportu — a `MIN_REPORTS`
    # w kształcie równościowym wymusiło siedem podniesień w ciągu jednego wieczoru.
    # Równość na `seen` kosztowałaby podniesienie przy każdej edycji prozy, co realnie
    # kończy się wyłączeniem bramki (6.D27).
    #
    # CZEGO TA PODŁOGA NIE ŁAPIE, i to też jest zmierzone: zdjęcie ze wzorca
    # któregokolwiek z pozostałych dziesięciu rozszerzeń zbija stosunek najwyżej
    # do 8,08 (bez `.cs`), więc przechodzi przy każdej wartości z przedziału.
    # Podłoga stosunkowa jest więc bramką na ZAŁAMANIE OBJĘTOŚCI, a pokrycie
    # rozszerzeń pilnuje osobna bramka niżej, bez żadnego progu.
    assert seen >= checked * SCIEZEK_NA_RAPORT_MIN, (
        f"wzorzec znalazł {seen} ścieżek w {checked} raportach, czyli "
        f"{seen / checked:.2f} na raport przy wymaganych {SCIEZEK_NA_RAPORT_MIN} — "
        "wzorzec przestał łapać część rozszerzeń albo skan przestał czytać treść")


#: Ile wpisów wolno mieć `ROZSZERZENIA_BEZ_TRAFIEN`. Zapadka jednokierunkowa:
#: wolno WYŁĄCZNIE obniżać, tak samo jak `MAX_COMMIT_EXCEPTIONS` wyżej. Bez tego
#: limitu bramkę pokrycia rozbroiłoby dopisanie wszystkich dwunastu rozszerzeń
#: do wyjątków — przeszłaby, nie sprawdzając niczego.
MAX_ROZSZERZEN_BEZ_TRAFIEN = 3

#: Podłoga, która stała tu przed 6.D58, trzymana jako OPERAND, nie jako wspomnienie:
#: brzeg „nowa podłoga żąda więcej niż stara" jest przez to sprawdzany, a nie
#: napisany w komentarzu. Wartość jest martwa — nic w drzewie już jej nie używa.
STARA_PODLOGA_STALA = 500


def _rozszerzenia_we_wzorcu():
    """Alternatywa rozszerzeń WYJĘTA z `PATH_TOKEN`, nie wpisana drugi raz."""
    grupa = re.search(r"\(\?:([a-z|]+)\)", PATH_TOKEN.pattern)
    assert grupa, (
        "w `PATH_TOKEN` nie ma już alternatywy rozszerzeń w postaci `(?:a|b|c)` — "
        f"wzorzec brzmi {PATH_TOKEN.pattern!r}, a bez tego odczytu bramka zgodności "
        "porównywałaby kopię z niczym")
    return tuple(grupa.group(1).split("|"))


def _pomiar_trafien(pattern=PATH_TOKEN):
    """(liczba przeczytanych raportów, {rozszerzenie: trafienia}).

    Filtr jest JEDEN — `_paths_in` — bo druga kopia warunku `IGNORED_PREFIXES`
    rozjechałaby się z pierwszą przy pierwszej zmianie (6.D44).
    """
    checked = 0
    po_rozszerzeniu = {}
    for _name, text in _reports():
        checked += 1
        for token, _number in _paths_in(text, pattern):
            klucz = token.rsplit(".", 1)[1]
            po_rozszerzeniu[klucz] = po_rozszerzeniu.get(klucz, 0) + 1
    return checked, po_rozszerzeniu


def test_zestaw_rozszerzen_w_kodzie_i_we_wzorcu_JEST_TEN_SAM():
    """`ROZSZERZENIA_PILNOWANE` musi się zgadzać z alternatywą w `PATH_TOKEN`.

    Bez tej asercji kopia byłaby gorsza niż jej brak: bramka pokrycia niżej
    sprawdzałaby rozszerzenia, których wzorzec już nie zna, albo — co gorsza —
    milczałaby o tych, które ze wzorca wypadły.
    """
    we_wzorcu = set(_rozszerzenia_we_wzorcu())
    w_kodzie = set(ROZSZERZENIA_PILNOWANE)
    assert len(ROZSZERZENIA_PILNOWANE) == len(w_kodzie), (
        f"`ROZSZERZENIA_PILNOWANE` ma powtórzenie: {ROZSZERZENIA_PILNOWANE}")
    assert w_kodzie == we_wzorcu, (
        "kopia listy rozszerzeń rozjechała się ze wzorcem — zrównaj je w tym samym "
        "commicie, w którym zmieniasz `PATH_TOKEN`:\n"
        f"  we wzorcu, brak w kodzie: {sorted(we_wzorcu - w_kodzie)}\n"
        f"  w kodzie, brak we wzorcu: {sorted(w_kodzie - we_wzorcu)}")
    nieznane = set(ROZSZERZENIA_BEZ_TRAFIEN) - w_kodzie
    assert not nieznane, (
        f"`ROZSZERZENIA_BEZ_TRAFIEN` wymienia {sorted(nieznane)}, których nie ma "
        "wśród pilnowanych — wyjątek od nieistniejącego wymagania nic nie robi")


def test_kazde_pilnowane_rozszerzenie_ma_zywe_trafienie_albo_jawny_wyjatek():
    """Pokrycie rozszerzeń — bramka BEZ PROGU, i to jest jej cała wartość.

    Podłoga stosunkowa wyżej łapie zdjęcie ze wzorca tylko `.py` albo `.md`:
    zmierzone 09.09.2026 na `c8fb583`, zdjęcie któregokolwiek z pozostałych dziesięciu
    zostawia stosunek na 8,08 albo wyżej, czyli **2 z 12** zawężeń. Ta bramka łapie
    **9 z 12** — wszystkie poza trzema, które i dziś nie mają trafień — i nie ma
    w niej liczby, która mogłaby się zestarzeć.

    Kontrola negatywna jest w raporcie `reports/podloga-sciezek-na-raport.md` §5:
    po zdjęciu `csv` ze wzorca (4 trafienia, stosunek 9,02, podłoga zielona) pada
    wyłącznie ta bramka i bramka zgodności kopii.
    """
    checked, po_rozszerzeniu = _pomiar_trafien()
    assert checked >= MIN_REPORTS, (
        f"bramka przeszła tylko {checked} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")
    bez_pokrycia = sorted(r for r in ROZSZERZENIA_PILNOWANE
                          if not po_rozszerzeniu.get(r)
                          and r not in ROZSZERZENIA_BEZ_TRAFIEN)
    assert not bez_pokrycia, (
        f"rozszerzenia {bez_pokrycia} nie mają w {checked} raportach ani jednego "
        "trafienia — wzorzec przestał je łapać albo klasa ścieżek zniknęła z prozy; "
        "jeśli to drugie, wpis idzie do `ROZSZERZENIA_BEZ_TRAFIEN` Z POWODEM")
    # DRUGA STRONA: wyjątek musi być MARTWY, inaczej lista gnije po cichu.
    ozywione = {r: po_rozszerzeniu[r] for r in ROZSZERZENIA_BEZ_TRAFIEN
                if po_rozszerzeniu.get(r)}
    assert not ozywione, (
        f"`ROZSZERZENIA_BEZ_TRAFIEN` wymienia {sorted(ozywione)}, a trafienia już "
        f"są ({ozywione}) — zdejmij wpis, bo od tej chwili chroni rozszerzenie, "
        "które bramka umie sprawdzić naprawdę")
    assert len(ROZSZERZENIA_BEZ_TRAFIEN) <= MAX_ROZSZERZEN_BEZ_TRAFIEN, (
        f"wyjątków od pokrycia jest {len(ROZSZERZENIA_BEZ_TRAFIEN)} przy limicie "
        f"{MAX_ROZSZERZEN_BEZ_TRAFIEN} — zapadka jest jednokierunkowa, wolno ją "
        "wyłącznie obniżać")


def test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami():
    """`SCIEZEK_NA_RAPORT_MIN` między dwoma brzegami LICZONYMI Z DRZEWA.

    Bez tego testu komentarz przy stałej byłby zdaniem o niezmienniku, którego nic
    nie pilnuje — usterka zamknięta w 6.D56 i 6.D57, dwa razy pod rząd.

    Brzegi są przeliczane przy każdym przebiegu, więc nie ma tu ani jednej liczby
    przepisanej z pomiaru. Kierunki, zmierzone 09.09.2026 na `c8fb583`:
    5 pada na brzegu od dołu (zawężenie kontrolne przechodzi), 6 jest zielone,
    9 pada na brzegu od góry. 7 i 8 mieszczą się w obu brzegach — wybór 6
    z tego przedziału jest pomiarem trwałości opisanym przy stałej, nie asercją.
    """
    checked, po_rozszerzeniu = _pomiar_trafien()
    seen = sum(po_rozszerzeniu.values())
    assert checked >= MIN_REPORTS, (
        f"bramka przeszła tylko {checked} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")

    # KONTROLA PRZYRZĄDU: zawężenie kontrolne musi naprawdę coś zabierać. Gdyby
    # `ROZSZERZENIE_KONTROLNE` nie miało trafień, brzeg od dołu porównywałby
    # podłogę z niezmienionym stosunkiem i był zielony nad każdą wartością stałej.
    ubytek = po_rozszerzeniu.get(ROZSZERZENIE_KONTROLNE, 0)
    assert ubytek > 0, (
        f"zawężenie kontrolne zdejmuje `.{ROZSZERZENIE_KONTROLNE}`, a to "
        "rozszerzenie nie ma dziś ani jednego trafienia — brzeg od dołu przestał "
        "cokolwiek mierzyć, wybierz na kontrolne rozszerzenie z trafieniami")
    zawezony = seen - ubytek

    # BRZEG OD DOŁU: podłoga musi zaczerwienić zawężenie kontrolne.
    assert checked * SCIEZEK_NA_RAPORT_MIN > zawezony, (
        f"po zdjęciu `.{ROZSZERZENIE_KONTROLNE}` ze wzorca zostaje {zawezony} "
        f"trafień, czyli {zawezony / checked:.2f} na raport, a podłoga żąda "
        f"{SCIEZEK_NA_RAPORT_MIN} — zawężenie PRZESZŁOBY. Podnieś "
        "`SCIEZEK_NA_RAPORT_MIN`, a jeśli to zabierze cały zapas od góry, znaczy to, "
        "że podłoga stosunkowa wyczerpała miejsce i pilnuje już tylko objętości")

    # BRZEG OD GÓRY: podłoga musi stać co najmniej JEDNĄ pełną ścieżkę na raport
    # pod dzisiejszym stosunkiem. Zapas w tej postaci nie starzeje się razem
    # z katalogiem, bo liczy się w ścieżkach NA RAPORT, a nie w trafieniach.
    assert seen >= checked * (SCIEZEK_NA_RAPORT_MIN + 1), (
        f"drzewo daje {seen / checked:.2f} ścieżki na raport przy podłodze "
        f"{SCIEZEK_NA_RAPORT_MIN} — zapas zszedł poniżej jednej pełnej ścieżki "
        f"({seen} trafień wobec {checked * (SCIEZEK_NA_RAPORT_MIN + 1)} wymaganych), "
        "więc następne chude raporty zaczerwienią bramkę bez żadnej usterki. "
        "Obniż `SCIEZEK_NA_RAPORT_MIN` w tym samym commicie, w którym to widzisz")

    # RÓŻNICA WOBEC STAREJ PODŁOGI, LICZBĄ: nowa żąda więcej i rośnie z katalogiem,
    # stara słabła z każdym raportem (500 to 3,09 ścieżki na raport przy 162
    # raportach, a 1,67 przy 300).
    assert checked * SCIEZEK_NA_RAPORT_MIN > STARA_PODLOGA_STALA, (
        f"nowa podłoga żąda {checked * SCIEZEK_NA_RAPORT_MIN} trafień, a stała, "
        f"którą zastąpiła, żądała {STARA_PODLOGA_STALA} — zmiana przestała "
        "sprawdzać więcej, niż sprawdzała poprzednia wersja")


def test_wzorzec_sciezki_lapie_to_co_ma_i_nie_lapie_prozy():
    """Kontrola detektora: bez niej test wyżej byłby zielony także przy martwym wzorcu.

    Sześć par, każda z powodem — po jednej na sposób, w jaki ten wzorzec mógłby
    cicho przestać być pomiarem. Dwie ostatnie doszły z 6.D59: kropka na początku
    ścieżki była martwym polem wzorca przez cały czas jego istnienia i **żadna
    z czterech wcześniejszych par by tego nie pokazała**, bo wszystkie mierzyły
    to, co wzorzec łapie albo odrzuca po prawej stronie kropki.
    """
    def found(line):
        return [t for t, _n in _paths_in(line)]

    # 1. Ścieżka repozytoryjna — musi wejść.
    assert found("zmiana w `src/Sim/Train/LineDrive.cs` i nic więcej") == [
        "src/Sim/Train/LineDrive.cs"]
    # 2. Kwalifikowana nazwa w kodzie NIE jest ścieżką — brak ukośnika.
    assert found("`sweep.max_deviation` i `lod.lod_plan`") == []
    # 3. Wytwór przebiegu NIE jest brakiem — reguła 8 zabrania go komitować.
    assert found("artefakt `build/t400/scene-line.log`") == []
    # 4. Odsyłacz bez rozszerzenia nie jest ścieżką pliku.
    assert found("patrz `docs/24` i `tools/ci`") == []
    # 5. Ścieżka zaczynająca się KROPKĄ jest ścieżką — 6.D59. Do 09.09.2026 wzorzec
    #    jej nie widział i 26 wzmianek w 18 raportach nie było sprawdzanych.
    assert found("workflow `.github/workflows/python-tests.yml` i skill "
                 "`.claude/skills/heartbeat/SKILL.md`") == [
        ".github/workflows/python-tests.yml", ".claude/skills/heartbeat/SKILL.md"]
    # 6. Dotfile BEZ katalogu ścieżką repozytoryjną w tym sensie nie jest — kropka
    #    jest dopuszczona tylko przed nazwą katalogu, więc rozszerzenie wzorca
    #    z pary 5 nie otwiera go na cokolwiek z kropką z przodu.
    assert found("plik `.gitignore` oraz `.plik.md`") == []


def test_lista_wyjatkow_od_sciezek_nie_gnije():
    """Wyjątek, który przestał być potrzebny, musi z listy ZNIKNĄĆ — jak wyżej.

    Dziś lista jest pusta i ten test to sprawdza wprost: pusta lista jest wynikiem
    pomiaru („żaden raport nie potrzebuje wyjątku"), a nie miejscem, w którym nic
    jeszcze nie zdążyło się nazbierać.
    """
    for token, reason in PATH_EXCEPTIONS.items():
        assert len(reason) > 40, f"wyjątek na {token} bez powodu: {reason!r}"
        assert not os.path.exists(os.path.join(ROOT, token)), (
            f"`{token}` już istnieje — zdejmij go z listy wyjątków")
    assert isinstance(PATH_EXCEPTIONS, dict)

# --- kształt nagłówka: zalecenie zapisane tam, gdzie raporty go szukają ----------

#: `docs/04-conventions.md` — plik, na który powołuje się 11 raportów w `reports/`
#: i `tools/tests/test_bin_path_framework.py`, cytując go jako źródło reguły
#: „pomiaru z datą się nie przelicza". Zmierzone 07.09.2026 na
#: `f684e40a3af52272f9cd1d32d241e9bf3abf644d`: plik miał wtedy **dziesięć wierszy**
#: i ani jednego zdania o raportach, nagłówkach czy pomiarach — dziesięć z tych
#: jedenastu cytowań wskazywało w puste miejsce (jedenaste, `reports/L1_A-chunks.md`,
#: cytuje go za „1 jednostka = 1 metr" i to w pliku było). Ta bramka pilnuje, żeby
#: cytowanie miało co cytować.
CONVENTIONS = os.path.join(ROOT, "docs", "04-conventions.md")

#: BLOK KODU RAZEM Z WCIĘTYM. Wzorzec zakotwiczony na `^```` (bez `[ \t]*`) pomija
#: blok stojący pod punktem listy — a taki blok w markdownie jest wcięty o dwa albo
#: cztery znaki. Przyrząd z takim wzorcem zwraca ZERO przykładów i wygląda przez to
#: na zielony, nie sprawdziwszy niczego; jest to dokładnie ta postać fałszywej
#: zieloności, którą 6.D27 nakazuje wyłączać. Parę w obie strony wykonuje
#: `test_detektor_przykladu_naglowka_widzi_blok_wciety`.
FENCE = re.compile(r'^[ \t]*```[^\n]*\n(.*?)^[ \t]*```', re.M | re.S)


def _header_field_line(header):
    """Wiersz POLA nagłówka niosący SHA — pierwszy wytłuszczony, albo `None`.

    Nagłówek potrafi wspominać commity także w prozie i w tabeli (`T-400-stage-3b.md`
    nazywa dwa dodatkowe, `mutacje-rdzen-sygnalizacji.md` cztery w tabeli dwóch
    przeglądów), więc kształtem raportu jest wyłącznie wiersz pola: taki, który
    zaczyna się od `**` i niesie SHA w grawisach. Zmierzone 07.09.2026: liczenie
    KAŻDEGO wiersza z SHA daje 35 kształtów zamiast 16, bo wchodzą do tego zdania
    prozy — czyli przyrząd mierzyłby wtedy prozę, nie nagłówek.
    """
    for line in header.splitlines():
        if line.startswith("**") and COMMIT.search(line):
            return line.strip()
    return None


def _shape(line):
    """Kształt wiersza: SHA -> `<sha>`, data w obu notacjach -> `<data>`.

    Normalizacja jest po to, żeby dwa raporty zmierzone w różnych dniach na różnych
    commitach miały ten sam kształt, a raport z inną KOLEJNOŚCIĄ pól — inny.
    """
    out = COMMIT.sub("`<sha>`", line.strip())
    for pattern in NOTATIONS.values():
        out = pattern.sub("<data>", out)
    return out


def _header_shapes(items):
    """Ile raportów z `items` ma który kształt wiersza pola: `{kształt: liczba}`."""
    counts = {}
    for _name, text in items:
        line = _header_field_line(_header(text))
        if line is None:
            continue
        counts[_shape(line)] = counts.get(_shape(line), 0) + 1
    return counts


def _naglowki_w_konwencjach(conventions_text):
    """Kształty przykładów nagłówka pokazanych w blokach kodu konwencji.

    Przykładem nagłówka jest blok kodu niosący SHA w grawisach — reszta bloków
    (gdyby doszły) tę bramkę nie interesuje.
    """
    return [_shape(block.strip()) for block in FENCE.findall(conventions_text)
            if COMMIT.search(block)]


def _przyklad_odstajacy(conventions_text, dominujacy):
    """(przykłady, te z nich, które NIE są dzisiejszym kształtem większości)."""
    przyklady = _naglowki_w_konwencjach(conventions_text)
    return przyklady, [p for p in przyklady if p != dominujacy]


def _brak_zapisu_o_raportach(conventions_text):
    """Czy konwencje mają w ogóle śródtytuł o raportach — `True`, gdy nie mają."""
    return not re.search(r'^#{1,6} .*raport', conventions_text, re.M | re.I)


def test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow():
    """Zalecany kształt nagłówka stoi w JEDNYM miejscu i jest tym, którego się używa.

    Bramka NIE jest bramką na kształt nagłówków — pomiar 6.D38 rozstrzygnął, że
    takiej być nie może: zmierzone 07.09.2026 na
    `f684e40a3af52272f9cd1d32d241e9bf3abf644d` — 140 raportów, 135 z wierszem pola,
    **90 w kształcie wzorcowym i 45 w piętnastu innych, wszystkich czytelnych**,
    a `docs/TASKS.md` (pole „Poza zakresem" 6.D38) zabrania przepisywania nagłówków
    datowanych pomiarów. Bramka na kształt zapalałaby się więc na 50 poprawnych
    raportach, a wyjątków wolno tu mieć dwa (`MAX_COMMIT_EXCEPTIONS`).

    Pilnowane jest coś innego i tańszego: że **przykład w konwencjach nie zgnije**.
    Kształt zalecany nie jest tu wpisany drugą listą — bramka bierze go z raportów
    (kształt większości) i porównuje z przykładem z `docs/04-conventions.md`.
    Rozjazd znaczy jedno z dwojga: albo zalecenie przestało opisywać repozytorium,
    albo ktoś zmienił zalecenie i nie zmierzył skutku. Oba warte zatrzymania.
    """
    items = list(_reports())
    counts = _header_shapes(items)
    assert len(items) >= MIN_REPORTS, f"tylko {len(items)} raportów w pętli"
    # PODŁOGA PRZEKIEROWANA, NIE POLUZOWANA — 6.D45. Stała tu `MIN_REPORTS`, czyli 40
    # przy 147 raportach z wierszem pola: przyrząd mógł przestać czytać sto siedem
    # nagłówków i przejść. Podniesienie `MIN_REPORTS` do stanu katalogu zapaliłoby tę
    # asercję na prawdzie o katalogu, nie na usterce — wiersza pola nie ma pięć
    # raportów i każdy z powodem (patrz `MAX_REPORTS_WITHOUT_FIELD_LINE`). Podłoga
    # liczy się więc od STANU KATALOGU minus zapadka: zapas zszedł ze 107 do zera.
    bez_wiersza = [name for name, text in items
                   if _header_field_line(_header(text)) is None]
    assert sum(counts.values()) >= len(items) - MAX_REPORTS_WITHOUT_FIELD_LINE, (
        f"tylko {sum(counts.values())} raportów ma wiersz pola z SHA przy "
        f"{len(items)} w katalogu i zapadce {MAX_REPORTS_WITHOUT_FIELD_LINE} — "
        "przyrząd przestał czytać nagłówki")
    assert MAX_REPORTS_WITHOUT_FIELD_LINE >= len(bez_wiersza), (
        f"raportów bez wiersza pola z SHA jest {len(bez_wiersza)} przy zapadce "
        f"{MAX_REPORTS_WITHOUT_FIELD_LINE}: {bez_wiersza} — daj nowemu raportowi "
        "wiersz pola, a jeżeli SHA naprawdę stoi w tabeli, podnieś zapadkę w tym "
        "samym commicie i napisz przy niej, który to raport")
    assert len(bez_wiersza) >= MAX_REPORTS_WITHOUT_FIELD_LINE, (
        f"zapadka {MAX_REPORTS_WITHOUT_FIELD_LINE} stoi wyżej niż stan "
        f"({len(bez_wiersza)}) — obniż ją do stanu faktycznego, inaczej robi zapas "
        "na przyszłe nagłówki bez wiersza pola")
    ranking = sorted(counts.items(), key=lambda para: -para[1])
    dominujacy, ile = ranking[0]
    drugi, ile_drugiego = ranking[1]
    # Bez tego „kształt większości" mógłby być remisem i bramka wskazywałaby
    # przypadkową stronę remisu jako prawdę o formacie.
    assert ile > ile_drugiego, (
        f"remis kształtów: {dominujacy!r} i {drugi!r} po {ile} — nie ma czego "
        "nazwać zaleceniem")

    with open(CONVENTIONS, encoding="utf-8") as handle:
        conventions = handle.read()
    przyklady, odstajace = _przyklad_odstajacy(conventions, dominujacy)
    assert przyklady, (
        "`docs/04-conventions.md` nie pokazuje ani jednego przykładu nagłówka "
        "raportu w bloku kodu — zalecenia, którego nie widać, nie da się stosować")
    assert not odstajace, (
        f"przykład nagłówka w `docs/04-conventions.md` ma kształt {odstajace} "
        f"przy kształcie {ile} z {sum(counts.values())} raportów: {dominujacy!r}")


def test_konwencje_maja_zapis_na_ktory_powoluja_sie_raporty():
    """Cytowanie musi mieć co cytować — inaczej odsyłacz jest ozdobą.

    Zmierzone 07.09.2026 na `f684e40a3af52272f9cd1d32d241e9bf3abf644d`: jedenaście
    raportów powołuje się na `docs/04-conventions.md`, dziesięć z nich za regułę
    o pomiarze z datą, a plik był wtedy listą dziesięciu punktów o jednostkach
    i osiach — ani śródtytułu, ani zdania o raporcie.

    Sprawdzany jest ŚRÓDTYTUŁ, a nie brzmienie zdania. Asercja na prozę pękałaby
    przy każdym przeredagowaniu akapitu i nie mówiłaby nic o tym, czy zapis jest;
    śródtytuł jest najgrubszym sygnałem, jaki da się sprawdzić bez zgadywania treści.
    """
    citing = sorted(name for name, text in _reports()
                    if "docs/04-conventions.md" in text)
    assert citing, (
        "żaden raport nie powołuje się już na `docs/04-conventions.md` — ta bramka "
        "przestała cokolwiek chronić i idzie do skasowania, a nie do obniżenia")
    with open(CONVENTIONS, encoding="utf-8") as handle:
        conventions = handle.read()
    assert not _brak_zapisu_o_raportach(conventions), (
        f"{len(citing)} raportów cytuje `docs/04-conventions.md` ({citing[:3]} …), "
        "a plik nie ma ani jednego śródtytułu o raportach")


def test_detektor_przykladu_naglowka_widzi_blok_wciety():
    """Para kontrolna dla dwóch bramek wyżej — bez niej byłyby zielone przy zerze.

    Punkt 1 jest tym, na czym ten przyrząd naprawdę mógł się wyłożyć: blok kodu
    stojący pod punktem listy jest w markdownie WCIĘTY, a wzorzec zakotwiczony
    na `^```` go pomija. Zero przykładów przechodziłoby wtedy przez `assert
    przyklady` jako pusta lista — czyli bramka byłaby czerwona z właściwego powodu
    tylko przypadkiem, a przy jednym niewciętym bloku obok zrobiłaby się zielona,
    nie widząc wciętego.
    """
    wciety = (
        "## Nagłówek\n\n"
        "- punkt listy, a pod nim blok:\n\n"
        "  ```\n"
        "  **Zmierzone 07.09.2026 na commicie:** `abc1234`\n"
        "  ```\n")
    # 1. WCIĘTY blok jest widziany — to jest cała ta kontrola.
    assert _naglowki_w_konwencjach(wciety) == [
        "**Zmierzone <data> na commicie:** `<sha>`"]
    # 2. DOWÓD, że pułapka istnieje, a nie tylko twierdzenie o niej: wzorzec bez
    #    `[ \t]*` przed grzbietem nie znajduje w tym samym tekście NICZEGO.
    zakotwiczony = re.compile(r'^```[^\n]*\n(.*?)^```', re.M | re.S)
    assert zakotwiczony.findall(wciety) == []
    # 3. Blok BEZ SHA nie jest przykładem nagłówka — inaczej każdy blok `bash`
    #    w konwencjach liczyłby się jako zalecenie o nagłówku.
    assert _naglowki_w_konwencjach(
        "```bash\nbash doctor.sh\n```\n") == []
    # 4. KONTROLA NA PRZYKŁADZIE POPRAWNYM: kształt zgodny z większością NIE
    #    odstaje. Bramka zapalająca się na dobrym tekście zostaje wyłączona (6.D27).
    dobry = "```\n**Zmierzone 2026-09-07 na commicie:** `abc1234`\n```\n"
    przyklady, odstajace = _przyklad_odstajacy(
        dobry, "**Zmierzone <data> na commicie:** `<sha>`")
    assert przyklady and not odstajace, (przyklady, odstajace)
    # 5. KONTROLA NEGATYWNA: przykład w INNYM kształcie odstaje i jest wskazany.
    inny = "```\n**Snapshot na commicie:** `abc1234` (`main`, 04.09.2026)\n```\n"
    _przyklady, odstajace = _przyklad_odstajacy(
        inny, "**Zmierzone <data> na commicie:** `<sha>`")
    assert odstajace == ["**Snapshot na commicie:** `<sha>` (`main`, <data>)"], odstajace
    # 6. Brak śródtytułu o raportach jest wykrywany, a obecny — nie zgłaszany.
    assert _brak_zapisu_o_raportach("# Konwencje\n\n- 1 jednostka = 1 metr.\n")
    assert not _brak_zapisu_o_raportach(
        "# Konwencje\n\n## Nagłówek raportu\n\ntreść\n")
    # 7. Wiersz pola bierze się z `**`, nie z prozy — nagłówek wspominający commit
    #    w zdaniu nie ma wiersza pola i do rozbicia kształtów nie wchodzi.
    assert _header_field_line("Punkt wyjścia: przegląd na `737d592`.") is None
    assert _header_field_line(
        "# Tytuł\n\n**Zmierzone na commicie:** `737d592`\n") == (
        "**Zmierzone na commicie:** `737d592`")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
