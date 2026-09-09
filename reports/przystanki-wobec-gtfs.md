# Listy przystanków wobec oficjalnego GTFS: jedna dziura i jeden fałszywy alarm

**Zmierzone 09.09.2026 na:** `9d38d5c`, kontener tej sesji.
**Przyrząd:** `data/network/stops.json` (snapshot GTFS STIB pobrany 01.09.2026,
suma treści w `data/network/gtfs-manifest.json`), `data/network/lines.json`,
`docs/00-network-data.md`. Dopasowanie nazw znormalizowane: bez znaków
diakrytycznych, wielkimi literami, po każdym członie nazwy dwujęzycznej i po
wariantach `name`, `name_fr`, `name_nl`.

---

## 1. Skąd ten raport

Właściciel rozstrzygnął dwa pytania z sekcji decyzji: **sprawdzić w źródłach**, czy
Madou należy do L6, i **wyprowadzić z danych** regułę liczenia stacji. Oba pytania
dały się rozstrzygnąć bez pobierania czegokolwiek: oficjalny snapshot GTFS leży
w repozytorium od 01.09.2026, z sumą treści i datą pobrania.

Ten raport nie zmienia ani jednego bajtu w `data/`.

## 2. Pytanie pierwsze: Madou na L6 — TAK

Pole `routes` każdej stacji w snapshocie niesie **numery linii**, nie
identyfikatory tras. Sprawdzone na stacjach o znanej przynależności, bo pierwszy
odczyt pomyliłem właśnie tutaj — `route_id` „6" w feedzie nie istnieje:

```
STOCKEL         routes=['1']                 (koniec linii 1)
ROI BAUDOUIN    routes=['6']                 (koniec linii 6)
ARTS-LOI        routes=['1', '2', '5', '6']  (przesiadka czterech linii)
MADOU           routes=['2', '6']
BOTANIQUE       routes=['2', '6']
```

**Madou jest obsługiwane przez linię 6** wedle oficjalnego GTFS, dokładnie tak jak
jego sąsiad Botanique. To potwierdza wniosek strukturalny z pomiaru z rana: dziura
była wewnętrzna, a poza nią sekwencja identyczna.

## 3. Pełne porównanie czterech linii, i tu wyszło coś ważniejszego

| linia | `lines.json` | GTFS | w `lines.json`, brak w GTFS | w GTFS, brak w `lines.json` |
|---|---|---|---|---|
| L1 | 21 | 30 | — | **dziewięć**: Jacques Brel, Aumale, Saint-Guidon, Veeweyde, Bizet, La Roue, Ceria, Eddy Merckx, Erasme |
| L2 | 19 | 19 | — | — |
| L5 | 28 | 28 | — | — |
| L6 | 25 | 26 | — | **Madou** |

L2 i L5 zgadzają się co do przystanku. L6 różni się **dokładnie jednym** i jest to
Madou. Ale L1 różni się **w przeciwną stronę**: GTFS przypisuje linii 1 dziewięć
stacji zachodniego odgałęzienia do Erasme, czyli trasy linii 5. Ten sam artefakt
widać na samym Erasme, które ma `routes=['1', '5']`.

**To jest właściwy wynik tego pomiaru i jest ostrzejszy od odpowiedzi na pytanie
o Madou.** Ten sam przyrząd, przyłożony do czterech linii, daje jedną prawdziwą
dziurę i jeden fałszywy alarm o dziewięciu pozycjach. Wniosek dla bramki: **naiwne
porównanie `lines.json` z polem `routes` nie może być bramką**, bo zażądałoby
dopisania do L1 dziewięciu stacji, których ta linia nie obsługuje. Bramka musi albo
porównywać po trasach z `trips`/`stop_times`, albo nieść jawną listę uzgodnionych
odstępstw — i to jest osobna pozycja, nie ta.

## 4. Pytanie drugie: 59 czy 60 — oba źródła maszynowe mówią 60

```
unikalnych nazw kanonicznych w GTFS: 60
przystanków (kanoniczne dopasowanie) w lines.json: 60
```

Deklaracja `network.metro_stations` i `docs/00-network-data.md` mówią **59**.
Rozbieżność jest więc jednostronna: nie między dwoma źródłami danych, a między
zgodnymi danymi i prozą.

Snapshot GTFS **sam już to zapisał**, i nikt na to nie zareagował:

```
"declared_metro_stations": 59,
"metro_stations": 61,
"metro_station_containers": 60,
"unique_station_names": 60,
"matches_declared": false,
"orphan_platforms": [{"name": "HEYSEL", "stop_id": "8825",
   "reason": "peron metra bez parent_station; potraktowany jako własna stacja"}]
```

Skąd 61 przy 60 nazwach: **Heysel ma dwa rekordy** (`59` i `8825`), bo jeden peron
metra nie ma rodzica w feedzie. Po odsianiu tego duplikatu zostaje 60 — czyli
liczba zgodna z `lines.json` co do jedności.

## 5. Moja hipoteza z rana była błędna

Podsuwałem wyjaśnienie, że 59 wychodzi z liczenia Elisabeth i Simonis jako dwóch
połówek jednego kompleksu. **GTFS temu przeczy:** obie są osobnymi stacjami, każda
z `routes=['2', '6']`, i obie mają własne rekordy. Wyjaśnienia różnicy 60 → 59
w danych **nie ma**, a proza nie podaje, którą stację wyłącza i dlaczego.

Zapisuję to wprost, bo hipoteza wypowiedziana i niesprawdzona zostaje w pamięci
jako ustalenie. Ta była wypowiedziana i jest nieprawdziwa.

## 6. Jedna różnica zapisu, nie stacji

```
w GTFS, nieznane lines.json: JOSEPH.-CHARLOTTE
```

To nie sześćdziesiąta pierwsza stacja, a skrócony zapis nazwy w feedzie („Joséph."
z kropką) wobec pełnej w `lines.json`. Normalizacja nazw musi to znosić i tutaj
zniosła — wymieniam, bo każda przyszła bramka na nazwach potknie się o to samo.

## 7. Weryfikacja

```
  RAZEM 2074 testów, 110 modułów, kod 0
```

Zestaw niezmieniony: ten raport nie tyka kodu ani danych.

## 8. Czego świadomie nie zrobiono, i co wymaga decyzji

**Nie dopisano Madou do `lines.json`.** Reguła 6 mówi, że `data/` jest tylko do
odczytu, chyba że zadanie mówi inaczej wprost, a to zadanie było pomiarem. Zmiana
wymaga dwóch rzeczy w jednym commicie: przystanku i podniesienia deklarowanej
liczby przystanków L6 z 25 na 26.

**Nie zmieniono liczby 59.** Wybór między „proza jest nieaktualna" a „proza stosuje
regułę, której nikt nie zapisał" jest twierdzeniem o sieci, nie wnioskiem z pomiaru
— a §4.1 zakazuje tu zgadywania. Pomiar mówi tylko, że oba źródła maszynowe dają 60
i że różnica to dokładnie jedna stacja.

**Nie postawiono bramki** zestawiającej listy przystanków z GTFS. Powód jest
w §3 i jest mierzalny: taka bramka w najprostszej postaci żądałaby dopisania do L1
dziewięciu stacji z cudzej trasy.
