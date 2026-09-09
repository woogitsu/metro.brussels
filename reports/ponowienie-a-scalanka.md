# Ponowienie po ruchu bazy pobiera STARĄ scalankę — zmierzone, nie wywnioskowane (6.D47)

**Zmierzone 09.09.2026 na:** `1b1db40` (wierzchołek `main` w chwili ponowienia).
**Przyrząd:** przebieg `pull_request` nr **34362242593** (`Python tool tests`, PR #439),
próba 1 z 14:13 UTC i próba 2 z 17:34 UTC, logi kroku `Checkout` obu prób,
API GitHub Actions (`rerun_workflow_run`).

---

## 1. Czego brakowało

`reports/ponowienie-a-ruch-bazy.md` (08.09.2026) ustalił, że w **1919** przebiegach
`pull_request` z 01–08.09.2026 (45 z więcej niż jedną próbą) **nie ma ani jednego**
ponowienia, między którego próbami ruszył `main`. Z materiału historycznego pytania
„czy ponowienie przelicza scalankę na dzisiejszej bazie" rozstrzygnąć się nie dało,
i tamten raport nazwał brakujący przebieg kształtem: potrzebny jest **ruch bazy między
dwiema próbami tego samego przebiegu**.

`CLAUDE.md` §9 zapisuje tę granicę wprost: „czy ponowienie po ruchu bazy przeliczyłoby
scalankę na nowej bazie, **nie zostało zmierzone**".

## 2. Przebieg, który tego brakującego kształtu dostarczył

Zamiast czekać na cudze scalenie w trakcie życia pull requesta, warunek został
**wytworzony**: przebieg PR #439 zakończył się o 14:15, a między nim a ponowieniem
o 17:34 `main` przesunął się o **pięć scaleń** (#440, #441, #442, #444, #445, #446,
#447 — licząc commity na `main`: `902cb6f` → `1b1db40`).

| | próba 1 | próba 2 |
|---|---|---|
| czas | 2026-09-09 14:13 UTC | 2026-09-09 17:34 UTC |
| `main` w tej chwili | `902cb6f` | `1b1db40` |
| job | 102501892182 | 102574742672 |
| wynik | `success` | `success` |

## 3. Odczyt z logów kroku `Checkout`

```
próba 1:  HEAD is now at b09dbcb Merge 570222c977c917bda2a3a5977e9fa723887d99b5 into 902cb6f70aeef0317ebf8f5485913b203ad85a3a
próba 2:  HEAD is now at b09dbcb Merge 570222c977c917bda2a3a5977e9fa723887d99b5 into 902cb6f70aeef0317ebf8f5485913b203ad85a3a
```

**Ten sam SHA scalanki, ta sama baza w opisie, mimo pięciu scaleń między próbami.**

Odpowiedź jednym zdaniem: **ponowienie przebiegu `pull_request` NIE przelicza scalanki
na dzisiejszej bazie — pobiera tę, która została zapisana przy tworzeniu przebiegu.**

## 4. Rzecz, którą log pokazuje przy okazji, i warto ją znać

Każda próba ma w logu **trzy** wiersze `HEAD is now at`, nie jeden:

```
próba 2:
  HEAD is now at 1b1db40 T-112 przyłożone do wyjścia … (#447)      <- stan workspace PRZED czyszczeniem
  HEAD is now at 1b1db40 T-112 przyłożone do wyjścia … (#447)
  HEAD is now at b09dbcb Merge 570222c9… into 902cb6f7…            <- to jest checkout scalanki
próba 1:
  HEAD is now at 902cb6f Pomiar: listy przystanków … (#438)        <- stan workspace PRZED czyszczeniem
  HEAD is now at 902cb6f Pomiar: listy przystanków … (#438)
  HEAD is now at b09dbcb Merge 570222c9… into 902cb6f7…
```

Dwa pierwsze wiersze mówią o **workspace współdzielonym między przebiegami** (runner
resetuje to, co zostało po poprzednim jobie) i **zmieniają się** razem z `main`.
Trzeci mówi o scalance i **nie zmienia się**. Czytający, który weźmie pierwszy wiersz
za odpowiedź na pytanie „co ten job sprawdził", dostanie liczbę wyglądającą na
dzisiejszą i będzie w błędzie. Procedura z `CLAUDE.md` §9 każe czytać wiersz
z `Merge … into …` i to jest dokładnie ten trzeci.

## 5. Co z tego wynika dla reguły

`CLAUDE.md` §9 mówił dotąd: „Ponowienie (`re-run failed jobs`) tego nie daje"
i opierał to na obserwacji, że **wszystkie próby w logach tego repozytorium pobrały
ten sam SHA** — czyli na materiale, w którym baza nie ruszała. Teza była **słuszna**,
a jej podstawa niepełna. Od dziś podstawa jest pełna: ruch bazy o pięć scaleń nie
zmienił scalanki ponowionej próby.

Zapis idzie do `docs/04-conventions.md`, na wzór zapisu o `queued`, bo to jest reguła
czytania wyniku CI, a nie zdanie o treści workflowa.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py
  -> RAZEM 2087 testów, 111 modułów, kod 0
```

Sam pomiar nie tyka repozytorium: to dwa odczyty z logów zakończonych jobów.
Numery jobów stoją w §2, żeby dało się je sprawdzić bez zaufania temu raportowi.

## 7. Czego świadomie nie zrobiono

**Nie zmieniono strategii checkoutu ani nie wprowadzono wymogu aktualnej gałęzi** —
pole „Poza zakresem" pozycji 6.D47.

**Nie sprawdzono, czy `rerun_failed_jobs` zachowuje się inaczej niż `rerun_workflow_run`.**
Zmierzone jest ponowienie CAŁEGO przebiegu. Oba warianty pobierają scalankę tym samym
krokiem `actions/checkout` bez wejścia `ref`, więc różnicy nie oczekuję — ale nie
zmierzyłem jej i nie twierdzę, że jej nie ma.

**Nie ponowiono przebiegu z otwartego pull requesta.** Użyty przebieg należy do PR-a
już scalonego, co dla pytania o scalankę jest bez znaczenia (checkout idzie po SHA,
nie po nazwie refa — to samo ustalenie z `reports/ponowienie-a-ruch-bazy.md`), ale
jest różnicą wobec sytuacji z 08.09.2026 i dlatego stoi tu wypisana.
