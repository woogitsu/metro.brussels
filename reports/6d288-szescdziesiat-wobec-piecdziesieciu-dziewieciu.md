# Sześćdziesiąt wobec pięćdziesięciu dziewięciu — różnica to JEDNA para, a przesłanka pozycji jest obalona dwa razy

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `9895e06`

Pozycja 6.D288 stawiała dwie tezy naraz: że suma unikalnych przystanków z czterech
linii (**60**) rozjeżdża się z `network.metro_stations` (**59**) bez wyjaśnienia,
i że **żadna bramka tych dwóch liczb nie zestawia**. Obie są nieprawdziwe od
09.09.2026. Ta pozycja nie dobudowuje więc czwartej bramki o tym samym — **mierzy
i nazywa, dlaczego to samo zdanie wróciło po raz trzeci**.

---

## 1. Liczby, drogą pierwszą

Czytnik: `json.load` na `data/network/lines.json`, nazwy składane z `lines[*].stops`.

```
linii: 4 -> ['L1', 'L2', 'L5', 'L6']
  L1: 21 przystanków
  L2: 19 przystanków
  L5: 28 przystanków
  L6: 26 przystanków
SUMA DŁUGOŚCI LIST: 94
NAZW RÓŻNYCH: 60
network.metro_stations: 59
network.stations_incl_premetro: 69
counting_rules: {'unique_stop_names': 60, 'unique_stations': 59, 'stations_incl_premetro': 69}
```

**Pierwsze przewidywanie padło i padło mocno.** Spisałem przed pomiarem, że suma
długości list wyniesie **69**, bo `network` ma pole `stations_incl_premetro` = 69.
Wyszło **94**. Pomyliłem dwie różne rzeczy: 69 jest liczbą STACJI z premetrem,
a 94 sumą DŁUGOŚCI list, w której każdy przystanek wspólnego pnia liczy się tyle
razy, ile linii przez niego biegnie. Nie ma tu żadnego napięcia — `Arts-Loi|Kunst-Wet`
stoi na czterech listach i wnosi cztery.

## 2. Różnica imiennie — to JEDNA para i nosi nazwy

Sześćdziesiąt nazw, w kolejności pierwszego wystąpienia, z liniami, na których stoją:

| # | nazwa | linie |
|---|---|---|
| 1 | Gare de l'Ouest\|Weststation | L1, L2, L5, L6 |
| 2 | Beekkant | L1, L2, L5, L6 |
| 3 | Étangs Noirs\|Zwarte Vijvers | L1, L5 |
| 4 | Comte de Flandre\|Graaf van Vlaanderen | L1, L5 |
| 5 | Sainte-Catherine\|Sint-Katelijne | L1, L5 |
| 6 | De Brouckère | L1, L5 |
| 7 | Gare Centrale\|Centraal Station | L1, L5 |
| 8 | Parc\|Park | L1, L5 |
| 9 | Arts-Loi\|Kunst-Wet | L1, L2, L5, L6 |
| 10 | Maelbeek\|Maalbeek | L1, L5 |
| 11 | Schuman | L1, L5 |
| 12 | Merode | L1, L5 |
| 13 | Montgomery | L1 |
| 14 | Joséphine-Charlotte | L1 |
| 15 | Gribaumont | L1 |
| 16 | Tomberg | L1 |
| 17 | Roodebeek | L1 |
| 18 | Vandervelde | L1 |
| 19 | Alma | L1 |
| 20 | Kraainem\|Crainhem | L1 |
| 21 | Stockel\|Stokkel | L1 |
| **22** | **Elisabeth** | **L2, L6** |
| 23 | Ribaucourt | L2, L6 |
| 24 | Yser\|IJzer | L2, L6 |
| 25 | Rogier | L2, L6 |
| 26 | Botanique\|Kruidtuin | L2, L6 |
| 27 | Madou | L2, L6 |
| 28 | Trône\|Troon | L2, L6 |
| 29 | Porte de Namur\|Naamsepoort | L2, L6 |
| 30 | Louise\|Louiza | L2, L6 |
| 31 | Hôtel des Monnaies\|Munthof | L2, L6 |
| 32 | Porte de Hal\|Hallepoort | L2, L6 |
| 33 | Gare du Midi\|Zuidstation | L2, L6 |
| 34 | Clemenceau | L2, L6 |
| 35 | Delacroix | L2, L6 |
| 36 | Osseghem\|Ossegem | L2, L6 |
| **37** | **Simonis** | **L2, L6** |
| 38 | Erasme\|Erasmus | L5 |
| 39 | Eddy Merckx | L5 |
| 40 | CERIA\|COOVI | L5 |
| 41 | La Roue\|Het Rad | L5 |
| 42 | Bizet | L5 |
| 43 | Veeweyde\|Veeweide | L5 |
| 44 | Saint-Guidon\|Sint-Guido | L5 |
| 45 | Aumale | L5 |
| 46 | Jacques Brel | L5 |
| 47 | Thieffry | L5 |
| 48 | Pétillon | L5 |
| 49 | Hankar | L5 |
| 50 | Delta | L5 |
| 51 | Beaulieu | L5 |
| 52 | Demey | L5 |
| 53 | Herrmann-Debroux | L5 |
| 54 | Roi Baudouin\|Koning Boudewijn | L6 |
| 55 | Heysel\|Heizel | L6 |
| 56 | Houba-Brugmann | L6 |
| 57 | Stuyvenbergh | L6 |
| 58 | Bockstael | L6 |
| 59 | Pannenhuis | L6 |
| 60 | Belgica | L6 |

Nadmiarowa wobec pięćdziesięciu dziewięciu jest **dokładnie jedna** z pary
**`Elisabeth` (22) i `Simonis` (37)**. Nie jest to mój wniosek — stoi wprost
w `data/network/lines.json`, w bloku `station_notes.simonis_elisabeth`:

> „Na listach linii występują dwie nazwy: 'Simonis' i 'Elisabeth'. To JEDEN kompleks
> stacyjny o dwóch halach peronowych."
> „Unikalnych NAZW na listach przystanków jest 60. Unikalnych STACJI w sieci jest 59.
> Obie liczby są poprawne — zależy, co się liczy."

**Przewidywanie czwarte trafione**, ale trafione tanio: odpowiedź leżała w danych
i wystarczyło ją przeczytać. Blok pozycji nazywał ją „hipotezą, nie pomiarem" —
jest pomiarem cudzym, zapisanym maszynowo w `counting_rules`, dwie linie niżej
od list, które pozycja kazała sumować.

## 3. Ile bramek zestawia dziś te dwie liczby — liczba, nie słowo

Pole „Wyjście" żądało liczby. Liczba zależy od tego, o co się pyta, więc podaję obie
i mówię, która na które pytanie odpowiada.

**Miejsc, które dotykają tej pary, jest TRZY:**

| miejsce | co robi |
|---|---|
| `tools/tests/test_network_declarations.py:159` | `unique_stop_names == len(nazwy)` (60 wobec list) **i** `unique_stations == network.metro_stations` (59 wobec 59) |
| `tools/tests/test_network_declarations.py:183` | liczy `roznica = unique_stop_names − unique_stations` i żąda, by bloki `station_notes` wymieniały **z nazwy** dokładnie tyle nadmiarowych nazw |
| `tools/tests/test_all.py:218` | `len(uniq) == counting_rules["unique_stop_names"]` — pilnuje wyłącznie strony 60 |

**Wyrażeń, w których 60 i 59 stoją razem, jest JEDNO** — `:183`. Pozostałe dwa
przybijają każdą liczbę do jej źródła osobno. Rozdzielam to, bo audyt zwiadowczy
zgłosił mi „dwie bramki", a właściciel decydował na podstawie tej liczby: bramek
dotykających pary jest o jedną więcej, a bramka zestawiająca obie liczby w jednym
wyrażeniu jest jedna. Żadna z trzech nie jest niepotrzebna i żadna nie jest
duplikatem pozostałych — `:159` pilnuje przybicia do źródeł, `:183` pilnuje, żeby
liczby nie rozjechały się **z powodem**.

Poza bramkami stoi jeszcze `tools/track/normalize_stops.py:250`
(`matches_declared = declared == summary["metro_stations"]`), ale to **nie jest
bramka**: narzędzie raportuje rozbieżność, a `tools/tests/test_gtfs_stops.py`
ćwiczy je na feedach syntetycznych, nie na `data/`. Liczy tam rekordy peronowe,
nie nazwy — `reports/simonis-elisabeth-regula-liczenia.md` §4a mierzy, że przy tym
feedzie porównanie idzie 59 wobec **61** i nie umie być prawdziwe.

## 4. Kontrola przyrządu — ta sama para DRUGĄ drogą, i przyrząd na niej poległ

Pole „Weryfikacja" żądało policzenia drugą drogą. Droga druga nie używa `json`
do list, nie pyta `network` o 59 i bierze 94 z innych pól:

```
pola `stations`: [21, 19, 28, 26, 12, 9, 9, 7, 17, 7] -> suma 155
kolumna tabeli w 00-network-data.md: [21, 19, 28, 26] -> suma 94
nazw z surowego tekstu, z powtórzeniami: 94
nazw RÓŻNYCH z surowego tekstu: 60
zdanie z 00-network-data.md: - 59 stacji metra · 69 łącznie z premetro
  stacji: 59  z premetrem: 69

PARA DROGĄ DRUGĄ: (60, 59)
```

**Para zgadza się co do cyfry** — 60 złożone wyrażeniem regularnym z surowego tekstu
i 59 przeczytane ze zdania prozą w `docs/00-network-data.md` dają to samo, co droga
pierwsza. Tabela w dokumencie odtwarza 21/19/28/26 co do wiersza.

**Ale kontrola złapała usterkę we własnym przyrządzie, i to jest jej wynik, nie
dygresja.** Wzorzec `"stations"\s*:\s*(\d+)` na surowym tekście daje **dziesięć**
trafień, nie cztery, i sumę **155** zamiast 94. Sześć nadmiarowych to pola
`stations` pakietów budowy `A`…`F`: **12, 9, 9, 7, 17, 7**, razem **61**.
Naiwny czytnik po nazwie pola zsumowałby linie z pakietami i podał liczbę, która
nie znaczy nic. Droga pierwsza tej pułapki nie miała, bo schodziła po strukturze
(`lines[*].stops`), a nie po nazwie pola — i to jest cała różnica między tymi dwoma
czytnikami.

**Trzecia liczba w tym samym pliku, zapisana bez rozstrzygnięcia:** suma `stations`
pakietów A–F wynosi **61**, przy 59 stacjach i 60 nazwach. Czy pakiety się pokrywają,
czy niosą premetro, ta pozycja nie pyta i nie rozstrzyga; żadna bramka tej sumy
z niczym nie zestawia (`build_packages` czytają tylko `test_packages.py:304`
i `test_validate_axis.py:160`, i pytają o identyfikatory, nie o liczbę stacji).

## 5. Dlaczego to samo zdanie wróciło po raz TRZECI — to jest właściwy wynik pozycji

Chronologia z `git log`, 09.09.2026, jeden dzień:

```
dafb7a1 2026-09-09 12:08:55 +0200  Kolejka: dziesięć pozycji z weryfikacji audytu … (#432)
                                    <- dodaje reports/audyt-weryfikacja.md
a3a8a7b 2026-09-09 16:55:32 +0200  Reguła liczenia 60 → 59 była w danych przez cały czas … (#441)
                                    <- dodaje OBIE bramki i reports/simonis-elisabeth-regula-liczenia.md

$ git rev-list --count dafb7a1..a3a8a7b
9
```

Zdanie „żadna bramka tych dwóch liczb nie zestawia" było **prawdziwe w chwili
zapisu** i przestało być prawdziwe **cztery godziny i czterdzieści siedem minut
później**, dziewięć commitów dalej. Nie zestarzało się przez dziesięć dni — zestarzało
się tego samego popołudnia.

**Korekta została napisana i trafiła do JEDNEGO z DWÓCH raportów niosących to
twierdzenie.** `reports/simonis-elisabeth-regula-liczenia.md` §8 zapowiada:
„§5 tamtego raportu dostaje blok korekty z odsyłaczem tutaj". Blok istnieje —
`reports/przystanki-wobec-gtfs.md:98`, „### KOREKTA 09.09.2026, ten sam dzień,
`4f68d29`", z odsyłaczem w wierszu 115. Drugi raport z tego samego dnia,
`reports/audyt-weryfikacja.md`, niesie w §5 **to samo zdanie** i korekty nie dostał:

```
$ grep -rln "żadna bramka tych dwóch liczb nie zestawia" reports/ docs/
reports/audyt-weryfikacja.md
docs/TASKS.md
$ grep -c "simonis-elisabeth" reports/audyt-weryfikacja.md
0
```

Tę właśnie, nieskorygowaną kopię przeczytało 6.D171 dnia 19.09.2026 i z niej
powstała 6.D288. Przyczyną nawrotu nie jest więc przeoczenie ani upływ czasu, tylko
**korekta zastosowana do jednego z dwóch nosicieli**. Dlatego ta pozycja dopisuje
blok korekty do `reports/audyt-weryfikacja.md` §5 — i jest to jedyna zmiana treści,
jaką robi poza zapisaniem pytania na liście.

## 6. Znalezisko poboczne, NIETKNIĘTE: hale kompleksu przypisane odwrotnie niż `to`

Przy wypisywaniu nazw imiennie wyszło coś, czego pozycja nie szukała. Blok
`station_notes.simonis_elisabeth.issue` mówi:

> „Linia 2 kończy bieg w hali **Elisabeth**, linia 6 w hali **Simonis**."

Listy w tym samym pliku mówią co innego o linii 6:

```
L2  from: Elisabeth              to: Simonis
    stops: Elisabeth(1) … Osseghem(18) Simonis(19)

L6  from: Roi Baudouin|Koning Boudewijn   to: Elisabeth
    stops: Roi Baudouin(1) … Simonis(8) Osseghem(9) … Ribaucourt(25) Elisabeth(26)
```

Linia 6 **kończy bieg w hali Elisabeth**, a `Simonis` jest jej ósmym z dwudziestu
sześciu przystanków. Linia 2 ma oba końce w kompleksie: zaczyna w `Elisabeth`,
kończy w `Simonis`. Zdanie z bloku i pola `to` przypisują hale **odwrotnie**.

**Nie rozstrzygam tego i nie tykam `data/`.** To twierdzenie o sieci (§4.1) w pliku
tylko do odczytu (§4.6), a rozstrzygnięcie wymaga sięgnięcia do oficjalnego źródła
STIB — czyli dokładnie tego, czego pole „Poza zakresem" tej pozycji zabrania.
Zapisane jako wiersz w sekcji „Czego agent nie ruszy bez decyzji", obok pytania,
po które ta pozycja została wzięta. Żadna bramka dziś tego zdania z polami `to`
nie zestawia — sprawdzone.

## 7. Przewidywania spisane PRZED pomiarem — trafienia i pudła

| # | przewidywanie | wynik |
|---|---|---|
| 1 | suma długości list = 69 | **PUDŁO**, jest 94 — pomyliłem stacje z premetrem z sumą po liniach |
| 2 | nazw różnych = 60 | trafione |
| 3 | `metro_stations` = 59 | trafione |
| 4 | różnica to jedna para, dwie hale kompleksu | trafione, i odpowiedź stoi w danych wprost |
| 5 | bramek porównujących = 2 | **niedokładne**: dotykających pary jest 3, zestawiających obie liczby w jednym wyrażeniu 1 |
| 6 | kontrola drugą drogą da tę samą parę | trafione — ale przy okazji obaliła mój drugi czytnik na polu `stations` |
| 7 | nie dotknę `data/` | dotrzymane, zero zapisów |
| 8 | nie rozstrzygnę, która liczba jest prawdziwa | dotrzymane — obie są prawdziwe, o czym mówi blok w danych |
| 9 | nie dobuduję bramki | dotrzymane, bramek nie przybyło |
| 10 | wiersz w sekcji decyzji trzeba będzie dopisać | trafione, i wyszły DWA wiersze, nie jeden |

Dwa z dziesięciu chybiły i **oba w tę samą stronę**: zakładałem, że stan repozytorium
jest uboższy, niż jest — mniej przystanków na listach i mniej bramek nad nimi.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py
```

Wynik wklejony w opisie pull requesta i w adnotacji wiersza 6.D288.

**Kontroli negatywnej na bramce tu nie ma i być nie może** — pozycja żadnej bramki
nie dodaje ani nie zmienia. Kontrolą, której pole „Weryfikacja" naprawdę żądało,
jest pomiar drugą drogą z §4 i ta kontrola **zapaliła się na moim własnym czytniku**
(155 zamiast 94), co jest jedynym sensownym dowodem, że nie była ozdobą.

## 9. Czego świadomie nie zrobiono

- **Ani jednego zapisu w `data/`** i ani jednej zmiany w `docs/00-network-data.md`.
- **Nie dobudowano czwartej bramki** o tej samej parze liczb — decyzja właściciela
  z 19.09.2026, i pomiar z §3 ją potwierdza: trzy miejsca wystarczają.
- **Nie rozstrzygnięto zdania o halach** z §6 ani sumy 61 z pakietów budowy z §4.
- **Nie przeliczono `reports/audyt-weryfikacja.md`.** `docs/04-conventions.md`
  zabrania przeliczania pomiaru z datą: liczby tamtego raportu zostają, bo były
  prawdziwe o 12:08. Fałszywy jest wniosek utrzymany po 16:55, więc §5 dostaje blok
  korekty z odsyłaczem, a nie nową treść w miejscu starej — tak samo jak
  `przystanki-wobec-gtfs.md` dostał go tego samego dnia.
