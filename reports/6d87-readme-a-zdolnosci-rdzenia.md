# README zaprzeczało istniejącemu API wielu składów (6.D87)

**Zmierzone 09.09.2026, przeliczone 10.09.2026 na:** `c15edd0`, kontener tej sesji.
**Przyrząd:** zestawienie zdania README z nazwami w `src/Sim/Line/LineCore.cs`
i z nazwami testów, `python3 tools/tests/test_all.py`, trzy kontrole negatywne
z `md5sum -c` po każdym przywróceniu.

---

## 1. Zdanie i to, czemu przeczyło

README, sekcja „Czego nie ma":

> **wielu składów.** Rdzeń prowadzi jeden skład. T-320 jest następnym zadaniem;

**Obie połowy nieprawdziwe.** Rdzeń:

```
src/Sim/Line/LineCore.cs:172   private readonly List<LineTrain> _trains = new();
src/Sim/Line/LineCore.cs:473   public IReadOnlyList<LineTrain> Trains => _trains;
```

plus testy przybijające zachowanie, a nie samo istnienie pola:
`Drugi_sklad_zatrzymuje_sie_przed_blokiem_zajetym_przez_pierwszy`,
`Zaden_sklad_nie_wjezdza_w_blok_zajety_przez_inny`,
`Wynik_nie_zalezy_od_kolejnosci_zgloszenia_skladow`.

A T-320 stoi w `docs/TASKS.md` jako **`[~] W TOKU`** z etapem 2 zrobionym — nie jako
zadanie następne.

## 2. Co jest prawdą o jednym składzie

Prawdą o **widoku**: `src/Game/FirstRun.cs` ma jeden węzeł `TrainView` (`_train`).
To jest ograniczenie sceny, nie rdzenia — i dokładnie tego rozróżnienia README nie
robiło.

**Szkody wykonawczej nie ma** — kod jest poprawny, myli się podsumowanie. Ale README
jest pierwszym, co czyta nowy człowiek i agent, a zdanie o braku zdolności, która
istnieje, kieruje pracę w złe miejsce.

## 3. Poprawka

Punkt rozbity na dwa zdania: co potrafi rdzeń (N składów, jeden zegar, jedna oś, jeden
plan bloków) i co pokazuje scena (jeden `TrainView`), plus stan T-320 zgodny z kolejką.

## 4. Bramka wiąże ZDANIE z NAZWĄ, a nie z liczbą

Pole „Skończone, gdy" zabrania liczenia plików i wierszy wprost — i słusznie: liczba
rośnie od pisania czegokolwiek, więc bramka na liczbie zapala się na zmianie bez
skutku (6.D27). Nazwa albo w rdzeniu jest, albo jej nie ma.

Tabela `ZAPRZECZENIA` wiąże fragment zdania z README z nazwami, których istnienie mu
przeczy. Bramka pada, gdy oba są obecne **naraz**.

## 5. Dwie bramki, bo cisza ma dwie przyczyny — i KN-3 to pokazuje

Bramka na zaprzeczenie milczy z dwóch różnych powodów: bo zdania nie ma w README
(dobrze) albo bo **nazwy nie ma w rdzeniu** (źle — wtedy wpis jest martwy i nie
zapali się nigdy). Drugi test odcina ten przypadek.

Że to nie jest ostrożność, pokazuje **KN-3**: przemianowanie `_trains` → `_sklady`
i `Trains` → `Sklady` **przy jednoczesnym przywróceniu fałszywego zdania** ucisza
pierwszą bramkę — bo szukane nazwy znikają — ale zapala drugą z komunikatem
„wpis wskazuje nazwę, której w `src/Sim/Line/LineCore.cs` nie ma". Cisza pary nigdy
nie znaczy więc „README ma rację".

## 6. Trzy kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK` (trzy pliki).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | przywrócone dzisiejsze zdanie README | **czerwona** 5/6 — nazywa zdanie, plik i obie nazwy |
| KN-2 | wpis tabeli wskazuje nazwę, której nie ma | **czerwona** 5/6 — „wpis jest martwy" |
| KN-3 | nazwy przemianowane **i** zdanie przywrócone | **czerwona** 5/6 — pada kontrola przyrządu, nie bramka zdania |

**Cache bajtkodu czyszczony przed każdym przebiegiem.** Powód jest zmierzony przy
6.D86: przywrócenie pliku przez `cp` w tej samej sekundzie co mutacja, przy napisie
o tej samej długości, zostawia ważny `__pycache__` i kontrola przebiega na starym
bajtkodzie — wyglądając przy tym jak wynik.

## 7. Czego NIE zrobiłem

**Nie przeliczałem wklejonych wyników historycznych w README** — pole „Poza zakresem".
**Nie objąłem tabelą pozostałych czterech punktów** sekcji „Czego nie ma". Każdy
wymaga własnego pomiaru: „profilu pionowego" i „ciągłego kilometrażu" mówią o danych,
nie o API, więc wiązanie ich z nazwami w rdzeniu byłoby wiązaniem z czymś, czego nie
dotyczą. Tabela ma dziś jeden wpis i to jest stan zmierzony, nie próg.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_readme_claims.py
  -> 6/6 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 98,802 s, 2148 testów, 113 modułów, kod 0
```

Zestaw urósł z **2146** do **2148**: dwa nowe testy.
