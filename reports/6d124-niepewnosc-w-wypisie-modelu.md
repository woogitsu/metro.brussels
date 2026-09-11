# 6.D124 — przybliżony parametr jest dokładnie jeden, a liczba mówi o rejestrze, nie o danych

**Zmierzone 11.09.2026 na:** `8fc0910`, kontener tej sesji.
**Przyrząd:** skan po wszystkich `data/**/*.json`, `tools/physics/braking.py`
(`PARAMETRY`, `parametry_przyblizone`, `report`), `tools/physics/reference.py`,
`tools/tests/test_braking.py`, `data/network/station-depths.csv` — wszystkie dane
wyłącznie do czytania.

---

## 1. Liczba, o którą prosiło pole „Wyjście"

Skan po **każdym** pliku `data/**/*.json`, szukający obiektów z `approximate: True`:

```
--- data/vehicle/m7-spec.json: 1
    parameters.empty_mass_kg  value=170000.0 unit=kg
RAZEM approximate:True w data/**/*.json: 1
```

**Jeden.** Pozycja przewidywała, że może tak wyjść („także wtedy, gdy wynosi jeden"),
i wyszło. Wartość to masa pusta M7, 170 000 kg, z notatką „STIB states approximately
170 tonnes; retain approximation explicitly".

## 2. Jeden to liczba o REJESTRZE, nie o danych — i to jest właściwy wynik

Przybliżeń w projekcie jest więcej. Mówią o sobie **innym językiem**, więc licznik
`approximate` ich nie widzi:

| gdzie | czym się oznacza | ile |
|---|---|---|
| `data/vehicle/m7-spec.json` | `approximate: true` | **1** |
| `data/network/station-depths.csv` | kolumna `confidence` | **3** wierszy `estimated`, 9 `unknown` |

Trzy `estimated` to De Brouckère, Parc i Arts-Loi — **te same trzy rzędne, które
6.D120 wpuściło do geometrii**. Ich notatki w CSV mówią wprost, że źródło pisze
„environ 11 m" i że precyzja nie jest lepsza niż ±1 m. Nie wchodzą do modelu jazdy
i mają własny język opisu, więc ten licznik ich nie obejmuje i obejmować nie ma —
ale zdanie „przybliżona wartość w tym projekcie jest jedna" byłoby **nieprawdą**.

Skan po innych markerach (`approx`, `environ`, `około`, `estimated`, `~`, `±`,
`roughly`, `circa`) w JSON-ach `data/` dał poza tym tylko trafienia w prozie metadanych
źródeł (`sources.json`: „ZIP ~378 kB", opis formatów) — nie są to wartości modelu.

## 3. Czy wchodzi do modelu: tak, i to jedną drogą

`empty_mass_kg` wchodzi jako `aw0_kg`, **jeden z piętnastu** parametrów
`braking.PARAMETRY`. Czytelnicy:

* `tools/physics/schedule_envelope.py:124` — `cfg["aw0_kg"]` przy `mass_key == "AW0"`;
* `tools/tests/test_braking.py` w dwóch miejscach.

`braking.report()` **nie wypisywał żadnej masy** — ani przybliżonej, ani nie — więc
nie było czego oznaczać obok liczby. Stąd wybór: wiersz osobny, nazywający parametry
przybliżone wprost, zamiast dopisku przy nieistniejącej kolumnie.

## 4. Rozstrzygnięcie: wypis modelu je nazywa

```
zryw = 0.75 m/s^3, lambda = 1.08, sluzbowe = 1.1 m/s^2, awaryjne = 1.3 m/s^2
PARAMETRY PRZYBLIZONE (rejestr, approximate: true): 1
  parameters.empty_mass_kg = 170000  — STIB states approximately 170 tonnes; retain approximation explicitly.
```

Wypis idzie **ścieżką rejestru**, a nie nazwą pythonową — dlaczego, mówi §4a.

Trzy decyzje, każda z powodem:

* **Liczony z rejestru, po tabeli `PARAMETRY`** — tej samej, z której `params` buduje
  model. Własna lista nazw byłaby drugą kopią wiedzy „który parametr jest przybliżony"
  i rozjechałaby się przy pierwszej zmianie w `data/`, nie zapalając niczego (KN-1).
* **Wiersz pada ZAWSZE, także przy zerze.** Wypisywanie go tylko wtedy, gdy jest co
  wypisać, robi z ciszy dwa różne zdania — „nic nie jest przybliżone" i „nikt nie
  sprawdzał" — nieodróżnialne dla czytającego (KN-3).
* **Wypis cytuje notatkę rejestru**, bo sama liczba nie mówi, CO jest przybliżone
  i z czyjej ręki (KN-4, KN-5).

## 4a. Bramka CI wywróciła pierwszą wersję — i miała rację

Pierwsza wersja wypisywała `aw0_kg = empty_mass_kg 170000  — …`, czyli **nazwą
pythonową**. Job `sim` poszedł na czerwono:

```
 zryw = 0.75 m/s^3, lambda = 1.08, sluzbowe = 1.1 m/s^2, awaryjne = 1.3 m/s^2
-PARAMETRY PRZYBLIZONE (rejestr, approximate: true): 1 z 15
-  aw0_kg = empty_mass_kg 170000  — STIB states approximately 170 tonnes; …
```

Krok „Sim.Runner braking kontra referencja" w `sim-tests.yml` porównuje `diff`em
**co do bitu** wypis rdzenia C# z wypisem `tools/physics/braking.py` — to są dwie
niezależne drogi do tych samych liczb i mają dawać jeden tekst. Moje dwa wiersze
istniały tylko po stronie Pythona.

**Zestaw lokalny tego nie łapie i łapać nie może**: ta bramka nie jest testem, tylko
krokiem workflowa, więc `python3 tools/tests/test_all.py` i `dotnet test` przechodzą
obok niej. Znalazło ją CI, dokładnie tak, jak ma znajdować.

Rozwiązanie nie jest jednak „dopisać to samo po stronie C#" wprost: rdzeń **nie zna
nazw pythonowych** (`aw0_kg`, `jerk`, `lam`) — one żyją w tabeli `braking.PARAMETRY`.
Wypisanie ich zmusiłoby rdzeń do trzymania **drugiej kopii tablicy nazw**, czyli
usterki, przed którą ta sama pozycja broni się gdzie indziej. Wspólną nazwą obu stron
jest **ścieżka rejestru** `parameters.empty_mass_kg` — i to ona stoi w wypisie.

Po stronie rdzenia weszło minimum: `RegistryEntry` czyta `approximate` i `notes`
(dotąd czytał `value`, `status` i `source_id`), a `VehicleRegistry.ApproximateEntries()`
zwraca je w porządku ordinalnym ścieżek — tym samym, co `przyblizone_wpisy` po stronie
Pythona. Rdzeń czyta **ten sam plik**, więc obie drogi zostają niezależne; nie powstała
ani jedna kopia wiedzy „która wartość jest przybliżona".

Mianownik „z 15" z wypisu zniknął z tego samego powodu: liczba parametrów modelu
hamowania jest wielkością pythonowej tabeli `PARAMETRY`, a rdzeń buduje model inaczej.
Pytanie „ile przybliżonych wchodzi do modelu" nie zniknęło — odpowiada na nie
`parametry_przyblizone` i pilnuje osobny test.

## 5. Przypadek zera trzeba było dać się WYKONAĆ

Dzisiejsze dane produkują jedynkę, więc zdanie „wiersz pada zawsze" i „wiersz pada,
bo akurat jest co wypisać" są na nich **nieodróżnialne**. `report()` dostało więc
parametr `registry` — ten sam zabieg, co `zamek=` w 6.D123 — żeby test mógł podstawić
rejestr bez flagi i sprawdzić, że wiersz nadal pada, z liczbą `0 z 15`.

Bez tego KN-3 (wiersz pod warunkiem `if przyblizone:`) przeszłaby na zielono.

## 6. Trzecia kopia liczby 170 000

Przy okazji zmierzone: ta sama liczba stoi w drzewie **trzy razy**.

1. `data/vehicle/m7-spec.json` — źródło, z flagą i notatką;
2. `tools/physics/reference.py:9` — `MASS={"AW0":170000.0,...}`, literał **bez żadnego
   znaku**, że jest przybliżony;
3. `tools/tests/test_all.py:104` — `assert R.MASS["AW0"] == 170000.0`.

Asercja z punktu 3 porównuje **kopię z kopią**: przeszłaby, gdyby rejestr podał co
innego. Doszedł więc test porównujący kopię ze **źródłem** — i żądający, żeby rejestr
nadal oznaczał tę wartość jako przybliżoną, bo `reference.py` niesie ją bez żadnego
znaku (KN-6). Wartości nie ruszam: `data/` jest tylko do odczytu, a literały
`reference.py` są treścią tablicy referencyjnej. Zmienia się to, czy rozjazd ma gdzie
zapalić.

## 7. Kontrole negatywne — WYKONANE, nie opisane

`cp` na bok i `md5sum -c` po przywróceniu (nigdy `git checkout`), `__pycache__`
czyszczony przed każdym przebiegiem. Baza `test_braking.py`: **34/34**.

Baza `test_braking.py`: **35/35**. KN-8 i KN-9 nie mają liczby z tego zestawu, bo
dotyczą bramki `diff` i rdzenia — ich wynik jest podany osobno.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | wykaz wpisany z ręki zamiast czytany z rejestru | **34/35** |
| KN-2 | `is True` zamienione na prawdziwość | **34/35**, flaga `"false"` |
| KN-3 | wiersz wypisywany tylko gdy jest co wypisać | **34/35** |
| KN-4 | wypis podaje liczbę, ale nie nazwy | **34/35** |
| KN-5 | wypis gubi notatkę rejestru | **34/35** |
| KN-6 | ręczna kopia masy w `reference.py` rozjechana o 1 kg | **34/35** |
| KN-7 | `aw0_kg` zdjęty z `PARAMETRY` | **30/35**, pięć testów |
| KN-8 | rdzeń nie wypisuje przybliżonych (stan sprzed poprawki) | **`diff` ROZJAZD**, dwa wiersze |
| KN-9 | rdzeń uznaje KAŻDY wpis za przybliżony | **Sim.Tests 599/601**, dwa testy |

Po każdej: `md5sum -c` → `OK` na pięciu plikach.

KN-8 odtwarza dokładnie ten stan, w którym CI zapaliło — i jest jedyną z tych
dziewięciu, której nie widzi żaden zestaw testów, tylko krok workflowa. KN-9 pokazuje,
że flaga jest po stronie rdzenia **czytana**, a nie zwracana dla wszystkiego: przy
kilkudziesięciu wpisach rejestru lista „wszystkich" wyglądałaby w werdykcie tak samo
jak lista „oznaczonych", gdyby wpis był jeden.

KN-2 jest warta zdania: rejestr pisany ręcznie prędzej czy później wyprodukuje
`"approximate": "false"` albo `0`. Dla `if rec.get(...)` napis `"false"` jest
**prawdziwy**, dla `is True` — nie. Różnica jest niewidoczna na dzisiejszych danych
i dlatego ma własną asercję.

## 8. Czego nie zrobiłem

* **Nie zmieniłem ani jednej wartości ani statusu w `data/`** — wprost w „Poza
  zakresem" i w §4.6.
* **Nie propaguję niepewności przez model** — „to jest osobna, większa rzecz",
  mówi pole „Poza zakresem", i to prawda: ±1 tona na masie pustej przekłada się na
  drogę hamowania przez opory Davisa i przez `lam`, a żadna z tych zależności nie
  jest dziś policzona.
* **Nie tknąłem `schedule_envelope.py`**, choć to ON wypisuje `[KOPERTA] … masa AW0`,
  czyli jedyny wypis, który dziś nazywa masę po imieniu. Nie stoi w polu „Wejście",
  a pozycja jest o wypisie modelu hamowania. To jest najbliższe naturalne miejsce
  na następny krok i dlatego stoi tu zapisane, a nie zrobione po cichu.
* **Nie dopisałem wiersza do `docs/21-measured-vs-assumed.md`**: masa pusta jest
  tam parametrem ze źródła (`spec`), a nie założeniem projektowym, więc tamta tabela
  nie jest jej miejscem.
