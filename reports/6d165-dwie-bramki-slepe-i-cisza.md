# 6.D165 — dwie bramki ślepe, zero przez `tree_walk`, i wypis, który milczał

**13.09.2026**, na `8f365ac`. Wejście: `tools/tests/test_conflict_markers.py`,
`tools/tests/test_runner_options.py`, `tools/tests/tree_walk.py`,
`tools/tests/test_all.py`, `reports/6d152-pola-wpisu-z-logu.md`.

## 1. Ile bramek pyta gita o listę plików — dwie, nie trzy

| moduł | czy wykonuje `git ls-files` |
|---|---|
| `test_conflict_markers.py` | **tak** |
| `test_runner_options.py` | **tak** |
| `test_report_hygiene.py` | **nie** — tylko cytuje to polecenie w komunikacie błędu |

Pole „Ile bramek to dotyczy" wymieniało dwa pierwsze wprost i pytało o resztę.
Trzeci moduł, który `git ls-files` **wymienia**, nie **wywołuje** go — różnica jest tu
treścią, bo bramka cytująca polecenie w tekście nie jest na nic ślepa.

## 2. Przez `tree_walk` nie pyta ani jeden — i to obala przesłankę pozycji

Pole mówiło: „ile modułów chodzi po `git ls-files` **pośrednio**, przez `tree_walk`,
jest do zmierzenia, a nie do zgadnięcia". Zmierzone: **zero**.

`tree_walk` importuje wyłącznie `fnmatch`, `os` i `shutil`. Gita nie woła w ogóle —
czyta `.gitignore` jako **tekst** i chodzi po katalogach. Dwadzieścia kilka modułów,
które go importują, widzi więc pliki nieśledzone normalnie.

**Ślepota nie rozlewa się na drzewo — siedzi w dwóch modułach.** To jest wynik
przeciwny do tego, którego pozycja się spodziewała, i dlatego wart zapisania.

## 3. Stan drzewa dzisiaj

| | |
|---|---:|
| plików śledzonych | 756 |
| plików nieśledzonych i nieignorowanych | **0** |
| plików ignorowanych | 352 |
| plików widzianych przez `tree_walk` od korzenia | 1218 |

Zero nieśledzonych **nie znaczy, że problem nie istnieje** — znaczy, że dziś przebieg
jest zrobiony po `git add`. Dokładnie dlatego wypis jest potrzebny: różnicy między
„nic nie pominięto" a „nikt nie sprawdził" nie było wcześniej widać.

## 4. Co weszło: wypis, nie bramka

`test_all.py` wypisuje teraz jedną linię, tak samo jak `[BAJTKOD]` od 6.D122:

```
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
```

**Nie jest bramką i nie zmienia kodu wyjścia.** Liczba większa od zera znaczy „tyle
plików ten przebieg pominął", a nie „błąd" — zamiana tego w bramkę byłaby karą za
normalny sposób pracy, a usterka z PR #548 polegała na **ciszy**, nie na istnieniu
plików roboczych.

Gdy gita zapytać się nie da, linia mówi to wprost zamiast wypisać zero: **zadeklarowana
niewiedza zamiast cichego zera**, bo zero przy zepsutym wywołaniu wygląda identycznie
jak zero przy czystym drzewie.

## 5. Kontrola negatywna, która wyszła ZIELONA DWA RAZY

To jest najważniejsza część tego raportu.

Pierwsza wersja bramki sprawdzała, czy w źródle `test_all.py` **występuje napis**
`_metro_drzewo_policzone` i `[DRZEWO]`. KN-3 (zamiana warunku wartowni na `if False:`)
wyszła **zielona**. Po dołożeniu asercji na nazwę — **znowu zielona**, bo nazwa
zostawała w drugiej połowie konstrukcji (`sys._metro_drzewo_policzone=True`).

**Napis w źródle nie jest wypisem na wyjściu.** Funkcja licząca była sprawdzona,
a jej **użycie** nie — czyli mechanizm dałby się wyłączyć bez ani jednego czerwonego
testu, i to w bramce, która powstała właśnie po to, żeby przebieg przestał milczeć.

Poprawka: bramka **uruchamia przebieg** (`test_all.py test_lod_paths.py` w podprocesie)
i szuka `[DRZEWO]` w jego **wyjściu**. Na tej wersji KN-3 jest czerwona.

## 6. Czego ta kontrola nie sprawdza — powiedziane wprost

Wartownia na `sys` chroni przed podwójnym wypisem, gdy `_discover` ładuje `test_all.py`
po raz drugi pod nazwą `test_all__mierzony`. Przy wywołaniu z **jednym nazwanym
modułem to się nie dzieje**: KN-5 (zdjęcie wartowni) wyszła zielona, a wypis nadal padł
dokładnie raz.

Asercji na liczbę wystąpień **nie ma**, bo nie mogłaby zapalić się nigdy — byłaby
kontrolą pustą z konstrukcji, czyli tą samą rodziną, którą 6.D161 policzyło jako
dziewięć przypadków na osiemnaście. Wartownia zostaje jako **ubezpieczenie bez
wejścia**, i jest to powiedziane wprost zamiast udawane asercją.

## 7. Kontrole negatywne

Baza: **7/7**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK` na obu plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | licznik zawsze zwraca zero | **6/7** | repozytorium próbne odróżnia licznik od atrapy |
| KN-2 | niewiedza zamieniona na ciche zero | **6/7** | `None` z powodem nie jest ozdobą |
| KN-3 | wypis zdjęty z przebiegu (wersja z napisem) | **ZIELONA** | patrz §5 |
| KN-3c | to samo, po sprawdzaniu przebiegiem | **6/7** | poprawka działa |
| KN-4 | `test_all.py` wpisany między bramki ślepe | **6/7** | reporter nie jest bramką |
| KN-5 | wartownia zdjęta | **ZIELONA** | patrz §6 — i dlatego asercji nie ma |

## 8. Czego nie zrobiono

- **Nie zamieniono `git ls-files` na chodzenie po katalogach** — „Poza zakresem",
  i zdejmowałoby ochronę przed `build/`.
- **Nie zmieniono kodu wyjścia zestawu** — „Poza zakresem", i wypis celowo nie jest
  bramką (§4).
- **Nie tknięto dwóch bramek ślepych.** Ich wybór jest słuszny; usterką była cisza
  przebiegu, a nie zasięg bramek.
