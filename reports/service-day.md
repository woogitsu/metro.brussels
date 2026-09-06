# Doba służby odtworzona przez rdzeń — 71 obiegów, 56 naraz o 07:06:44

**Zmierzone 06.09.2026 na commicie:** `0aec7ae`

Feed: STIB-MIVB GTFS, `feed_version` **2_20_20260831_010702**, zakres 20260831..20260927,
suma treści `28c2fba48783e278d20f8f703759e3f729b72608d015e00d0f8215fa3b278bb6`.
Dzień odniesienia **20260902, środa**, ten sam co w T-113.

## 1. Co ta pozycja rozstrzyga

`reports/T-113-timetable.md` podaje trzy liczby: **71 obiegów**, **56 naraz w służbie
o 07:06:44**. Liczy je narzędzie Pythona. Rdzeń tego nie umiał: `line` dodaje **jeden**
skład, a `budget` dodaje N składów na **równym takcie**, nie z obiegów — wpis T-320
wypisuje to wprost jako część, która „Zostaje".

Pozycja 6.A3 żąda, żeby te same trzy liczby wyszły **z rdzenia**, i żeby różniły się
od tamtych o zero.

## 2. Wynik

```
$ dotnet run --project src/Sim.Runner -c Release -- service-day \
      --timetable <plik rozkładu> --at 07:06:44
[SŁUŻBA] dzień 20260902: obiegów 71, naraz w służbie 56 o 07:06:44
[SŁUŻBA] nakładających się par kursów w jednym obiegu: 0
[SŁUŻBA] o 07:06:44 w służbie 56 obiegów
```

wobec narzędzia Pythona:

```
[SŁUŻBY] obiegów pojazdów (block_id): 71, naraz w służbie 56 o 07:06:44,
         kursów na obieg 6–35, czas w służbie mediana 13 h 27 min
```

| wielkość | Python | rdzeń | różnica |
|---|---:|---:|---:|
| obiegów | 71 | **71** | 0 |
| naraz w służbie | 56 | **56** | 0 |
| o której | 07:06:44 | **07:06:44** | 0 |
| nakładających się par kursów w obiegu | 0 | **0** | 0 |

## 3. Dlaczego to nie jest przepisanie liczby Pythona do C#

To jest sedno pozycji, a nie formalność. Rozkład zawierał dotąd **wynik** —
`blocks`, `max_concurrent_blocks`, `overlapping_trips_in_a_block` — ale nie **dane**,
z których ten wynik powstał. Rdzeń czytający takie pole nie liczyłby niczego; wypisałby
cudzą liczbę i bramka porównywałaby liczbę ze sobą samą.

Dlatego `tools/track/timetable.py` eksportuje teraz przy każdym obiegu
**okna kursów** — pary sekund od północy, po jednej na kurs — a rdzeń liczy z nich
wszystko od nowa: liczbę obiegów, zamiatanie po zdarzeniach dla szczytu i nakładki
między kolejnymi kursami. Trzy zgodności z §2 są więc **wynikiem dwóch niezależnych
rachunków**, a nie jednego przepisanego dwa razy.

`ServiceDay.FromJson` **odmawia** rozkładu bez `trip_windows`, i to też nie jest
ostrożność z góry: cicha zgoda dałaby dokładnie tę bramkę, która porównuje liczbę
ze sobą samą.

### 3a. Okna kursów są w sekundach, nie w zapisie zegarowym

Doba służby wychodzi poza 24:00 — najpóźniejszy przyjazd w tym feedzie to **24:36:14**.
`clock()` zapisuje to tekstem, którego żaden parser czasu nie przyjmie bez wiedzy
o konwencji, a zawinięcie do `00:36:14` przeniosłoby skład o dobę wstecz i zbiłoby
szczyt. Sekundy przenoszą tę samą informację bez konwencji do zgubienia; rdzeń
odtwarza zapis zegarowy sam i **pozwala godzinie przekroczyć 24**.

## 4. Kolejność przy remisie jest częścią definicji, nie szczegółem

Szczyt liczy się zamiataniem po zdarzeniach. Gdy jeden obieg kończy się w tej samej
sekundzie, w której zaczyna się drugi, **wejście liczy się przed wyjściem** — bo
przedział służby jest domknięty z obu stron i w tej sekundzie oba składy stoją
na sieci.

Odwrotna kolejność dałaby szczyt mniejszy o jeden i **wyglądałaby tak samo poprawnie**.
Dlatego ma własny test i własną kontrolę negatywną (§6, KN1), a nie komentarz.

## 5. Testy

| zestaw | przed | po |
|---|---:|---:|
| rdzeń (`dotnet test`) | 502 | **518** |
| narzędzia (`test_all.py`) | 1677 | **1680** |

Testy rdzenia **nie czytają prawdziwego rozkładu** i to jest decyzja, nie
niedopatrzenie: plik rozkładu powstaje z archiwum GTFS, którego nie ma w drzewie,
a pobranie wymaga sieci. Test wiążący się z tym plikiem przechodziłby na maszynie,
która akurat go ma, i padał w czystym checkoucie — dokładnie tak wywrócił się jeden
pull request 06.09.2026. Liczby z prawdziwego feedu stoją w §2; testy sprawdzają
**własności**, które te liczby produkują.

## 6. Kontrole negatywne — wykonane

Każda mutacja w `src/Sim/Line/ServiceDay.cs`, przebieg pełnego zestawu, cofnięcie.
`git diff --stat src/Sim/` po wszystkich: pusty.

| # | mutacja | pada | z 518 |
|---|---|---|---|
| KN1 | remis rozstrzygany na korzyść wyjścia | `Wejscie_liczy_sie_przed_wyjsciem_gdy_padaja_w_tej_samej_sekundzie` | 1 |
| KN2 | przedział służby otwarty od dołu (`>=` → `>`) | `Przedzial_sluzby_jest_domkniety_z_obu_stron` **i** test remisu | 2 |
| KN3 | ostatni przyjazd = koniec ostatniego okna | `Ostatni_przyjazd_to_maksimum_a_nie_koniec_ostatniego_okna` | 1 |
| KN4 | styk kursów liczony jako nakładka (`<` → `<=`) | `Nakladajace_sie_kursy_w_jednym_obiegu_sa_zgloszone_a_nie_przemilczane` | 1 |

```
########## KN1 ##########
  Failed Wejscie_liczy_sie_przed_wyjsciem_gdy_padaja_w_tej_samej_sekundzie [14 ms]
Failed!  - Failed: 1, Passed: 517, Total: 518

########## KN2 ##########
  Failed Wejscie_liczy_sie_przed_wyjsciem_gdy_padaja_w_tej_samej_sekundzie [14 ms]
  Failed Przedzial_sluzby_jest_domkniety_z_obu_stron [< 1 ms]
Failed!  - Failed: 2, Passed: 516, Total: 518

########## KN3 ##########
  Failed Ostatni_przyjazd_to_maksimum_a_nie_koniec_ostatniego_okna [19 ms]
Failed!  - Failed: 1, Passed: 517, Total: 518

########## KN4 ##########
  Failed Nakladajace_sie_kursy_w_jednym_obiegu_sa_zgloszone_a_nie_przemilczane [13 ms]
Failed!  - Failed: 1, Passed: 517, Total: 518
```

**KN2 wywraca dwa testy i to jest uczciwe, a nie wygodne.** Otwarcie przedziału
od dołu psuje nie tylko domkniętość, ale i remis: test remisu sprawdza
`ConcurrentAt(200) == 2`, a to opiera się na domkniętości z obu stron. Dwa testy
mierzą tu jedną własność z dwóch stron i nie udaję, że są niezależne.

### 6.1 Kontrola, która znalazła błąd w moim własnym teście

Pierwsza wersja `test_timetable_exports_trip_windows_so_the_core_can_recount_them`
oczekiwała okna `[21600, 21840]`. Bramka je wywróciła: prawdziwe okno to
`[21615, 21840]`, bo kurs zaczyna się **odjazdem** z pierwszego przystanku
(06:00:15), nie przyjazdem na niego (06:00:00). Literał był mój, nie kodu — i jest to
drugi raz tego dnia, gdy własny literał w teście okazał się przyczyną czerwieni.

## 7. Czego świadomie nie zrobiłem

- **Perturbacji i polityki dyspozytora nie ma** — to jest 6.A4, przeniesione do
  „Czego agent nie ruszy bez decyzji". Doba służby jest **odtworzeniem rozkładu**,
  nie modelem zakłóceń.
- **Nic nie zapisuję do `data/`.** Pobranie archiwum aktualizuje pole `retrieved_at`
  w manifeście proweniencji; przywróciłem plik, bo pole „Poza zakresem" tej pozycji
  zabrania zapisu do `data/` wprost. Suma treści feedu jest przy tym **identyczna**
  z zapisaną w repozytorium, więc archiwum nie zmieniło się od 01.09.2026 —
  odtwarzalność tych liczb tego nie narusza.
- **Nie dopisałem bramki CI na te trzy liczby.** Wymagałaby pobierania archiwum GTFS
  przy każdym przebiegu, czyli sieci i 14,5 MB na job. Pole „Weryfikacja" pozycji
  przewiduje przebieg ręczny i tak został wykonany.
- **Nie ruszałem obsady linii ani kroku rdzenia.** Doba służby liczy się z okien
  kursów; symulowanie 71 składów przez 19 godzin przy 120 Hz to rząd 8·10⁶ kroków
  na skład i nie jest tym, o co pyta pole „Skończone, gdy".

## 8. Zauważone obok, nietknięte

`tools/track/fetch_gtfs.py` **pisze do `data/`** (manifest proweniencji), mimo że
`CLAUDE.md` §4.6 nazywa ten katalog tylko do odczytu. Dla tej pozycji rozstrzyga to
pole „Poza zakresem" i plik został przywrócony, ale sam rozjazd między narzędziem
a regułą zostaje — narzędzie robi to celowo, jako zapis proweniencji, a reguła nie
przewiduje wyjątku.
