# Reguła liczenia 60 → 59 była w danych przez cały czas, a raport ogłosił jej brak

**Zmierzone 09.09.2026 na:** `4f68d29`, kontener tej sesji.
**Przyrząd:** `data/network/lines.json` (blok `station_notes`), `data/network/stops.json`
(snapshot GTFS STIB pobrany 01.09.2026), `git log -S`, `tools/tests/test_network_declarations.py`,
`python3 tools/tests/test_all.py`.

---

## 1. Twierdzenie, które prostuję

`reports/przystanki-wobec-gtfs.md` §5, z tego samego dnia, mówi:

> Podsuwałem wyjaśnienie, że 59 wychodzi z liczenia Elisabeth i Simonis jako dwóch
> połówek jednego kompleksu. **GTFS temu przeczy:** obie są osobnymi stacjami (…).
> Wyjaśnienia różnicy 60 → 59 w danych **nie ma**, a proza nie podaje, którą stację
> wyłącza i dlaczego.

Wiersz kolejki „**59 czy 60 stacji** — reguła liczenia" niesie to samo, mocniej:
hipoteza jest tam nazwana **NIEPRAWDZIWĄ**, a decyzja przypisana właścicielowi jako
„twierdzenie o sieci".

**Obie połowy tego są nieprawdziwe**, i to nie z powodu nowego pomiaru, tylko dlatego,
że plik, który tamten pomiar czytał, odpowiada na to pytanie wprost.

## 2. Co naprawdę stoi w `data/network/lines.json`

```json
"station_notes": {
  "$comment": "Rozbieżności i pułapki w liczeniu stacji. Agent MA to przeczytać przed liczeniem czegokolwiek.",
  "simonis_elisabeth": {
    "issue": "Na listach linii występują dwie nazwy: 'Simonis' i 'Elisabeth'. To JEDEN kompleks
              stacyjny o dwóch halach peronowych. Linia 2 kończy bieg w hali Elisabeth,
              linia 6 w hali Simonis.",
    "consequence": "Unikalnych NAZW na listach przystanków jest 60. Unikalnych STACJI w sieci
                    jest 59. Obie liczby są poprawne — zależy, co się liczy."
  },
  "counting_rules": {"unique_stop_names": 60, "unique_stations": 59, "stations_incl_premetro": 69}
}
```

Nie jest to proza do interpretacji: `counting_rules` niesie **obie liczby maszynowo**,
a `simonis_elisabeth` nazywa **dokładnie tę stację**, o którą pytał wiersz kolejki
(„proza nie podaje, którą stację wyłącza"). Wyjaśnienie jest więc w danych, w tym samym
pliku, dwie linie niżej od list, które tamten pomiar porównywał.

## 3. Od kiedy tam jest — zmierzone, nie założone

```
$ git log --all --format="%h %ad %s" --date=short -S "simonis_elisabeth" -- data/network/lines.json
b019436 2026-09-07 Scalenie #380: 6.B41 — pusty zbiór mutacji nazywa rzeczywistą przyczynę

$ git show 9d38d5c:data/network/lines.json | grep -c simonis_elisabeth
1
```

`9d38d5c` to commit, na którym mierzył poranny raport. Blok był tam obecny w chwili
pomiaru. To nie jest wiedza, która przyszła później.

## 4. Niezależne potwierdzenie z oficjalnego GTFS — i ono też nie przeczy

Poranny raport odczytał z GTFS „dwa osobne rekordy" i uznał to za zaprzeczenie
kompleksu. Dwa rekordy peronowe nie są jednak zaprzeczeniem jednej stacji, i widać to
w tym samym feedzie, w polu, którego nikt nie sprawdził — w **wejściach**:

```
kontenerów bez ani jednego wejścia: 2 z 61  ->  SIMONIS, HEYSEL

pięć najbliższych par kontenerów:
       3.3 m  HEYSEL <-> HEYSEL          (znany duplikat: peron metra bez parent_station)
      96.2 m  ELISABETH <-> SIMONIS
     304.1 m  GARE CENTRALE <-> PARC
     314.1 m  MAELBEEK <-> SCHUMAN
     334.3 m  DELTA <-> HANKAR
```

SIMONIS nie ma w feedzie **ani jednego własnego wejścia**: wszystkie sześć
(`0470138`, `0470238`, `0470338`, `0470438`, `0470638`, `0470738`) należą do kontenera
ELISABETH, 96,2 m dalej, przy najbliższej **prawdziwej** parze stacji w odległości
304 m. Oba kontenery mają `routes=['2','6']` i po dwa perony.

Struktura feedu mówi więc to samo, co blok w danych: jeden kompleks, dwie hale,
wejścia wspólne. **Kontrola negatywna tego odczytu jest w samej liczbie 2 z 61** —
gdyby „brak wejść" był w tym feedzie zjawiskiem pospolitym, nie znaczyłby nic.

## 4a. Flaga `matches_declared` nie była dowodem — nie może być prawdziwa

Poranny raport przytoczył jako poparcie: „Snapshot sam to zapisał i nikt nie zareagował:
`matches_declared: false`". Ta flaga nie mówi tego, co jej przypisano. `normalize_stops.py`
liczy ją tak (wiersz 250):

```python
document["summary"]["matches_declared"] = declared == summary["metro_stations"]
```

a `metro_stations` to liczba **rekordów**, nie stacji ani nazw:

```
declared_metro_stations: 59
metro_stations:          61     <- z osieroconym peronem Heysel
metro_station_containers: 60
unique_station_names:     60
matches_declared:      False
```

Porównanie idzie więc 59 wobec **61**. Byłoby fałszywe także wtedy, gdyby proza mówiła 60
— i pozostanie fałszywe, dopóki Heysel ma w feedzie peron bez rodzica. **Nie ma tu więc
sygnału, na który ktoś nie zareagował; jest flaga, która przy tym feedzie nie umie być
prawdziwa.** Sam komunikat narzędzia („Nie koryguję — wymaga rozstrzygnięcia drugim
źródłem") zaprasza do rozstrzygania czegoś, co drugie źródło — `station_notes` w tym samym
repozytorium — już rozstrzyga.

Naprawa narzędzia (porównywać po nazwach kanonicznych i po regule z `station_notes`,
zamiast po liczbie rekordów) **nie jest częścią tej pozycji**: zmieniałaby wyjście
generatora danych, a to osobna robota z osobną weryfikacją. Zapisane tu, żeby nie zginęło.

## 5. Dlaczego przyrząd tego nie zobaczył

Poranny pomiar wczytał `lines.json` i porównał `lines[*].stops` z GTFS. Bloku
`station_notes` w tym samym słowniku **nie odczytał ani razu** — mimo że jego własny
`$comment` brzmi „Agent MA to przeczytać przed liczeniem czegokolwiek".

To jest rodzina 6.D65, 6.D66 i 6.D76: **przyrząd melduje sprawdzenie, którego nie
zrobił.** Tu z dodatkiem, który warto zapisać osobno: raport nie tylko przeoczył dane,
ale **ogłosił ich nieistnienie** („wyjaśnienia w danych NIE MA") i na tej podstawie
skierował pytanie do właściciela. Przeoczenie kosztuje jeden pomiar; ogłoszony brak
kosztuje cudzą decyzję.

## 6. Bramka

`tools/tests/test_network_declarations.py` dostaje trzy asercje:

1. `counting_rules.unique_stop_names` równa się liczbie unikalnych nazw z list linii;
2. `counting_rules.unique_stations` równa się `network.metro_stations`,
   a `stations_incl_premetro` — swojemu odpowiednikowi;
3. **różnica** między nazwami a stacjami jest wytłumaczona co do jedności: bloki
   `station_notes` opisujące kompleks muszą wymieniać dokładnie tyle nadmiarowych nazw,
   ile wynosi różnica. Dziś: 60 − 59 = 1, a `simonis_elisabeth` wymienia dwie nazwy
   z list (`Simonis`, `Elisabeth`), czyli jedną nadmiarową. Zgadza się.

Trzecia asercja jest tą, która zamienia notatkę w regułę sprawdzalną: dopisanie
sześćdziesiątej pierwszej nazwy albo zmiana `metro_stations` przestaje być cicha.

## 6a. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| `counting_rules.unique_stop_names` 60 → 59 | `FAIL …zgadza_sie_z_listami…: counting_rules mówi 59 unikalnych nazw, a listy przystanków dają 60` (i druga bramka: różnica 0, a bloki tłumaczą 1), 4/6 |
| `network.metro_stations` 59 → 58 | `FAIL …zgadza_sie_z_listami…: counting_rules mówi 59 stacji, a network.metro_stations 58`, 5/6 |
| **obie** liczby stacji na 58 — liczby zgodne ze sobą, rozjechane z powodem | `FAIL …wytlumaczona_co_do_jednosci: różnica … wynosi 2, a bloki station_notes tłumaczą 1`, 5/6 |
| nazwy w notatce przestają być cytowane (`'Simonis'` → `Simonis`) | `FAIL …wytlumaczona_co_do_jednosci: różnica … wynosi 1, a bloki station_notes tłumaczą 0: []`, 5/6 |

`md5sum -c` po każdej: `OK`.

Trzecia kontrola jest tą, dla której druga bramka w ogóle istnieje: **liczby mogą się
zgadzać ze sobą i rozjechać z powodem.** Czwarta pilnuje, żeby bramka **odmawiała**,
gdy przestaje rozumieć notatkę, zamiast przechodzić na pustym dopasowaniu — bez niej
przeredagowanie bloku uciszyłoby ją bez śladu.

## 7. Weryfikacja

```
  6/6 przeszło       test_network_declarations.py
  RAZEM 2080 testów, 111 modułów, kod 0
```

Zestaw przed pozycją: 2078 testów, 111 modułów.

## 8. Czego świadomie nie zmieniono

**Ani jednej liczby w `data/` i `docs/`.** 59 w `docs/00-network-data.md`
i w `network.metro_stations` jest **poprawne** — pomiar to potwierdza, a nie obala.
Poprawiane są wyłącznie zdania o tych liczbach.

**Nie przeliczono raportu z rana.** `docs/04-conventions.md` mówi, że pomiaru z datą
się nie przelicza; jego liczby zostają, bo są prawdziwe. Fałszywy jest wniosek, więc
§5 tamtego raportu dostaje blok korekty z odsyłaczem tutaj, a nie nową treść w miejscu
starej.
