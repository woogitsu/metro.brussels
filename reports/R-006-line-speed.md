# R-006 · Prędkość dopuszczalna na torze — skąd biorą się 72 i 50 km/h

Stan: **2026-09-02**. Zadanie: znaleźć **pierwotne** źródło prędkości liniowej metra STIB,
bo `speed_limits` jest pustą listą we wszystkich sześciu osiach (`data/track/*.json`),
a `max_speed_kmh` = 80 w rejestrze M7 jest prędkością **konstrukcyjną pojazdu**
(`design_model`, `source_id: null`), nie dopuszczalną na torze.

---

## 1. Wynik, w jednym zdaniu

**Żaden dokument STIB nie podaje prędkości dopuszczalnej na torze.** Liczby 72 km/h
i 50 km/h krążące po sieci pochodzą z **jednej notatki prasowej z 11 lutego 2008 r.**,
a wersja o 50 km/h dla linii 2 jest **sprzeczna z dzisiejszym rozkładem STIB**, co
sprawdziłem pomiarem.

## 2. Skąd naprawdę pochodzą te liczby

Ślad prowadzi w jedno miejsce i się tam kończy:

```
fr.wikipedia „Métro de Bruxelles"
  „La limite de vitesse des rames est de 72 km/h"          ─┐
  „la vitesse maximale de la ligne 2 est limitée à 50 km/h" ─┤ jeden przypis
  „vitesse commerciale de 30 km/h"                          ─┘
        ↓
DH/Les Sports+, 11.02.2008: „Une ligne du métro bruxellois limitée à 50 km/h"
        ↓
komunikat STIB z 10.02.2008 — „conduite respectueuse de l'environnement"
```

Notatka prasowa podaje 72 km/h jako prędkość **obowiązującą przed** wprowadzeniem
ograniczenia i sama zapowiada możliwą zmianę „lors de la restructuration du réseau
de métro en février 2009".

**To jest kluczowe.** Zapowiadana restrukturyzacja to ta, która dała dzisiejszy układ
linii — samo repo datuje ją w `data/network/lines.json`: `"ring_closed": "2009-04-04"`.
Ograniczenie 50 km/h zostało więc ogłoszone dla **sieci sprzed obecnego układu**,
osiemnaście lat temu i przed zamknięciem pierścienia, po którym dziś jeżdżą linie 2 i 6.

Klasa źródła według `data/network/sources.json`: `manufacturer_or_trade_press`, czyli
przedostatnia pozycja w hierarchii — **poniżej** OSM.

## 3. Czego nie ma w dokumentach STIB

Przeszedłem dwa oficjalne zbiory statystyk STIB od deski do deski, wyciągając tekst
z PDF-ów. W obu **słowo „vitesse" pada dokładnie raz** i za każdym razem chodzi
o prędkość handlową:

| dokument | trafień „vitesse" | co podaje |
|---|---:|---|
| `STIB_statistic_report_fr.pdf` (raport roczny 2025, dane 2024–2025) | 1 | wyłącznie prędkość handlową |
| `STIB_Statistiques_2008.pdf` (dane 2007–2008) | 1 | wyłącznie prędkość handlową |

Prędkości maksymalnej ani dopuszczalnej na torze nie ma w żadnym z nich.

## 4. Pomiar: 50 km/h nie da się pogodzić z dzisiejszym rozkładem

Przepuściłem pakiet E (pierścień 2/6) przez pętlę z T-401 przy różnych limitach
i porównałem z rozkładem zmierzonym w T-113.

Blok niżej jest przebiegiem z 02.09.2026, czyli sprzed #86, i liczb w nim nie
przeliczam — to zapis tego, co wyszło tamtego dnia. Wiersz `58,75 km/h` był wtedy
próbą przy dolnym ograniczeniu, jakie podawało T-401.

```
$ dotnet run --project src/Sim.Runner -- line --axis data/track/L2_E.json \
    --limit-kmh <X> --exchange-s 10.5 --timetable build/timetable.json

L2_E przy 50    km/h:  3/15 odcinków wolniejszych od rozkładu, najmniejsza rezerwa  −7.20 s
L2_E przy 55    km/h:  1/15                                                          −2.60 s
L2_E przy 58,75 km/h:  0/15                                                          +0.18 s
L2_E przy 72    km/h:  0/15                                                         +11.12 s
```

Przy 50 km/h **trzech z piętnastu odcinków nie da się przejechać w rozkładowym czasie**,
najciaśniejszy spóźnia się o 7,2 s. Wniosek jest warunkowy względem modelu rozpędzania
z T-310, ale kierunek jest jednoznaczny: albo ograniczenie zniknęło przy restrukturyzacji
2009, albo dotyczyło innego odcinka, albo nigdy nie było tym, czym opisała je prasa.

**72 km/h natomiast jest zgodne ze wszystkim, co zmierzyłem** — leży powyżej dolnego
ograniczenia 58,68 km/h z T-401 i zostawia rezerwę na każdym z 49 odcinków sieci.

Do 04.09.2026 stała w tym zdaniu wartość sprzed #86. Wniosek się nie ruszył, bo 72
leży powyżej obu, ale liczba cytowana z T-401 ma być tą, którą T-401 podaje dzisiaj.

## 5. Kontrola krzyżowa: prędkość handlowa się zgadza

Tego akurat STIB podaje, i to co roku. Zestawienie z tym, co wychodzi z GTFS:

| źródło | prędkość handlowa metra |
|---|---:|
| STIB, statystyki 2025 (dane 2025 i 2024) | **27,9 km/h** |
| STIB, statystyki 2008 — 2007 / 2008 | 29,8 / 29,0 km/h |
| STIB 2008, dzień roboczy: szczyt / poza szczytem / wieczór | 28,9 / 29,4 / 31,1 km/h |
| **mój pomiar z GTFS, pakiet A** (6687 m, jazda 655 s + 10 postojów po 20 s) | **28,16 km/h** |

28,16 wobec 27,9 przy zupełnie innej drodze dojścia — STIB liczy średnią ważoną po całej
sieci ze swoich danych eksploatacyjnych, ja policzyłem jeden pień z opublikowanego GTFS.
To jest **pierwsza kontrola całego łańcucha T-113 wobec liczby opublikowanej przez STIB**
i łańcuch ją przechodzi.

Sama jazda bez postojów daje na pakiecie A 36,75 km/h — różnica 8,6 km/h to koszt
zatrzymywania się co 600 m.

## 6. Co jeszcze wyszło przy okazji

Trzy liczby z tych samych dokumentów, przydatne gdzie indziej:

| wielkość | STIB 2025 / 2024 | STIB 2008 / 2007 | uwaga |
|---|---:|---:|---|
| długość osi metra z terminusami | **39,778 km** | 39,9 / 39,7 km | `lines.json` ma 39,9 — to wartość z 2008 |
| stacje metra i premetra | 69 (9 przesiadkowych) | 69 (9) | bez zmian |
| rozjazdy o napędzie elektrycznym | **121** | 79 | wzrost o 53 % |
| nastawnie (postes de signalisation) | **82** | 74 | do T-313 |

Dwie z nich są wprost interesujące:

- **`lines.json` podaje `metro_length_km: 39.9`, a aktualny raport STIB 39,778 km.**
  Nie jest to błąd w repo — 39,9 to prawdziwa liczba STIB, tylko z danych za 2008 r.
  Liczba stacji się zgadza: `stations_incl_premetro: 69` wobec 69 u STIB.
- **121 rozjazdów i 82 nastawnie** to pierwsze liczby o skali sygnalizacji, jakie repo ma
  z pierwotnego źródła. R-003 (#34) tego nie zastępuje, ale dobrze się z tym zestawi.

## 7. Rekomendacja

**Nie wpisywać żadnej prędkości do `data/track/*.json`.** Uzasadnienie jest teraz mocniejsze
niż „nie mamy źródła": źródło jest znane, zidentyfikowane co do daty i **zdyskwalifikowane**
— notatka prasowa sprzed osiemnastu lat, opisująca sieć w innym układzie, w części
sprzeczna z dzisiejszym rozkładem.

Co proponuję zamiast tego:

1. **72 km/h wolno używać jako parametru scenariusza**, jawnie zadeklarowanego przez
   wołającego (`LineRunSettings.SpeedLimitMps`), z tym raportem jako uzasadnieniem
   wyboru. Nie jako wpis w `data/`.
2. **Dolne ograniczenie 58,68 km/h z T-401 zostaje pomiarem** — to jedyna liczba
   o prędkości liniowej, która w tym repo ma wyprowadzenie: `reports/T-401-line-run.md`
   §4, maksimum kolumny C# po sześciu pakietach, czyli odcinek Beaulieu → Demey
   w L5_D. Ta liczba się rusza przy każdym przeliczeniu T-401, dlatego pilnuje jej
   `tools/tests/test_t401_citation.py`, a nie dobra wola czytającego.
3. **Prawdziwe źródło wymaga kontaktu ze STIB** albo dostępu do dokumentacji
   przetargowej CBTC (Ansaldo 2016 dla L1/L5, Pulsar/SYSTRA-GESTE-Tractebel 2017).
   Dokumenty przetargowe nie są publiczne; to zadanie dla człowieka, tak samo jak T-903.

## 8. Czego nie zrobiłem

- **Nie tknąłem `data/`.** Ani `speed_limits`, ani `lines.json` (rozbieżność 39,9 / 39,778
  zostaje do decyzji właściciela — to zmiana faktu o sieci, nie poprawka narzędzia).
- **Nie zarejestrowałem nowych źródeł w `sources.json`.** Oba PDF-y statystyk są pierwotne
  i policzyłem im hasze (§9), ale wpis do rejestru to zapis do `data/` i należy do właściciela.
- **Nie dotarłem do bilansu STIB 2006**, na który powołuje się przypis w Wikipedii.
  Ślad prowadzi do notatki prasowej z 2008, więc nie sądzę, żeby bilans 2006 zawierał
  cokolwiek więcej — ale tego nie sprawdziłem i nie twierdzę.

## 9. Dokumenty gotowe do rejestracji

Gdyby właściciel chciał je wpisać do `data/network/sources.json`:

```
id:      stib_statistics_2025
class:   official_stib          publisher: STIB/MIVB
url:     https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Corporate/
         Rapport%20annuel/Rapport%20annuel%202025/STIB_statistic_report_fr.pdf
sha256:  e39572e66c32c4e8ba156e2766e6d997841a2591229a83fc699a3a544ce83c61   (589 551 B)
role:    commercial_speed, network_length, signalling_asset_counts
limits:  brak prędkości dopuszczalnej na torze; statystyka eksploatacyjna, nie specyfikacja

id:      stib_statistics_2008
class:   official_stib          publisher: STIB/MIVB
url:     https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Corporate/
         STIB_Statistiques_2008.pdf
sha256:  90bcc9a5c6d3004f6b683c94980731a856bf3fd33ab0890b59540c77d29f22fa   (130 940 B)
role:    commercial_speed_history, network_length_history
limits:  dane 2007–2008, sprzed restrukturyzacji sieci z lutego 2009
```

## 10. Źródła

- STIB/MIVB, *Statistiques* (raport roczny 2025) — <https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Corporate/Rapport%20annuel/Rapport%20annuel%202025/STIB_statistic_report_fr.pdf>
- STIB/MIVB, *Statistiques — Rapport d'activités 2008* — <https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Corporate/STIB_Statistiques_2008.pdf>
- DH/Les Sports+, 11.02.2008, *Une ligne du métro bruxellois limitée à 50 km/h* — <https://www.dhnet.be/actu/belgique/2008/02/11/une-ligne-du-metro-bruxellois-limitee-a-50-kmh-O4BLHVOQKRDTXCST7YQI4ABSBQ/>
- *Métro de Bruxelles*, fr.wikipedia — <https://fr.wikipedia.org/wiki/M%C3%A9tro_de_Bruxelles> (źródło wtórne; wskazuje na powyższą notatkę)
