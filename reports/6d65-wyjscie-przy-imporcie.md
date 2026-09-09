# Drugie drzwi: zestaw wychodził kodem zero, nie wypisawszy ani jednego wiersza (6.D65)

**Zmierzone 09.09.2026 na:** `5d06146`, kontener tej sesji.
**Przyrząd:** sonda w `tools/tests/`, `tools/tests/test_all.py`,
`tools/tests/test_assertion_gate.py`, `python3 tools/tests/test_all.py`.

---

## 1. Usterka

Moduł, który wychodzi z procesu **przy imporcie**, kończył cały zestaw kodem
z wyjątku i bez ani jednego wiersza wyjścia. Sonda: jeden moduł w skanowanym
katalogu z `sys.exit(0)` w ciele i jednym celowo padającym testem.

```
kod wyjścia całego zestawu: 0
bajtów wyjścia zestawu: 0
ile FAIL: 0
```

Zero wierszy, zero dopasowań na grepie po `FAIL`, kod sukcesu — przy teście, który
nie miał najmniejszej szansy przejść.

## 2. Dlaczego to było najgroźniejsze, co ten zestaw mógł robić

**Milczenie zestawu jest nieodróżnialne od jego sukcesu.** Ta jedna gałąź
unieważniała każde raportowane „kod 0" — nie dlatego, że któryś moduł tak robił,
ale dlatego, że gdyby zaczął, nie byłoby o tym ani jednego sygnału. Cała kontrola
jakości tego repozytorium stoi na jednym kodzie wyjścia i jednym wierszu
podsumowania.

## 3. Przyczyna: 6.D54 naprawiło JEDNE drzwi z dwóch

`SystemExit` dziedziczy z `BaseException`, nie z `Exception`. Dwie pętle w tym samym
pliku łapały wyjątki różnie:

| ścieżka | co łapała | skutek |
|---|---|---|
| wykonanie testu | `except SystemExit` → FAIL testu | poprawne od 6.D54 |
| **import modułu** | `except Exception` | `SystemExit` przelatywał do procesu |

6.D54 zostało zmierzone i opisane w docstringu klasy, która tam powstała — dla
ścieżki wykonania. Nikt wtedy nie policzył, że ta sama różnica dziedziczenia dotyczy
także pętli o dziesięć wierszy wyżej.

## 4. Poprawka

Pętla importu dostała własną gałąź i **własną klasę** z zapisanym powodem.
Osobną, nie tę z 6.D54 — bo rada jest inna: tam „złap `SystemExit` w teście", tu
„kod na poziomie modułu nie może wychodzić z procesu". Jeden komunikat na dwie
różne rady byłby mylący dokładnie w chwili, w której ktoś go czyta.

Po poprawce, ta sama sonda:

```
kod wyjścia: 1
bajtów wyjścia: 150120
FAIL-i: 1
FAIL <import>test_zz_sonda_wyjscia: WyjscieZImportu: zawolal sys.exit(0) PRZY
  IMPORCIE modulu — kod na poziomie modulu nie moze wychodzic z procesu, bo wynosi
  sterowanie z calego zestawu. Przenies to wywolanie do `if __name__ == "__main__":`
  albo do ciala testu, gdzie `SystemExit` jest FAIL-em jednego testu
```

## 5. Bramka, żeby to nie wróciło

Sama poprawka bez bramki jest jednorazowa. Powstały dwa testy, oba **bez tworzenia
pliku** w skanowanym katalogu — podstawiają loader, bo mierzona jest gałąź `except`,
a nie odkrywanie plików. Plik-sonda zapalałby przy okazji dwie inne bramki (o
strażniku uruchomienia wprost), czyli mierzyłby trzy rzeczy naraz; to widać w §7.

Pierwszy test sprawdza, że wyjście przy imporcie ląduje jako niepowodzenie importu
właściwej klasy i z komunikatem mówiącym o imporcie. Niesie też asercję
**strukturalną** — że `SystemExit` jest poza `Exception` — bo bez niej ktoś mógłby
usunąć gałąź w przekonaniu, że `except Exception` wystarcza.

Drugi test pilnuje, że stara ścieżka nie została zabrana: błąd składni nadal trafia
do niepowodzeń importu i **nie** jest przekierowany do nowej gałęzi.

## 6. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| gałąź `SystemExit` zdjęta z pętli importu, sonda obecna | `kod 0`, `0 bajtów`, `0 FAIL-i` — usterka odtworzona |
| ta sama gałąź zdjęta, bez sondy | `FAIL test_modul_wychodzacy_z_procesu_PRZY_IMPORCIE_jest_FAILEM_IMPORTU`, `24/25` |
| kolejność obu gałęzi odwrócona | `25/25 przeszło` — **kontrola NIE zapala**, patrz §8 |

`md5sum -c` po każdej: `OK`.

## 7. Rzecz, którą kontrola pokazała po drodze

Sonda bez strażnika uruchomienia wprost zapaliła **trzy** FAIL-e, nie jeden, i dwa
dodatkowe były poprawne. Jeden z nich mówi:

```
FAIL test_every_test_module_can_be_run_directly: modul testowy bez straznika
  `__main__` — uruchomiony wprost skonczy sie kodem 0, nie wykonawszy ani jednego
  testu: tools/tests/test_zz_sonda_wyjscia.py
```

To ten sam objaw co 6.D65 — „kod 0, ani jednego testu" — tylko dla **uruchomienia
wprost**, i był pilnowany od 6.D25. Bramka na jeden z dwóch trybów wywołania
istniała od dawna; brakowało jej bliźniaczki dla trybu zbiorczego. Dlatego nowe
testy podstawiają loader, zamiast kłaść plik: inaczej mierzyłyby przy okazji tamtą
bramkę i nie dałoby się powiedzieć, która z trzech porażek jest ta właściwa.

## 8. Poprawka do własnego uzasadnienia

Pierwsza wersja docstringa drugiego testu twierdziła, że gałąź `SystemExit` **musi**
stać przed `except Exception`, bo inaczej błąd składni przestanie być raportowany.
Kontrola negatywna to obaliła: po odwróceniu kolejności moduł przechodzi `25/25`.

Kolejność jest nieistotna dokładnie z tego powodu, który czyni całą usterkę 6.D65
możliwą — żadna z tych gałęzi nie przechwytuje drugiej, bo `SystemExit` jest poza
`Exception`. Uzasadnienie zostało przepisane na prawdziwe, a nie usunięte: pilnuje
tego asercja strukturalna, nie kolejność zapisu. Zdanie nieprawdziwe w docstringu
bramki jest tą samą rodziną usterki, którą bramka ściga — tylko o jeden poziom
wyżej.

## 9. Weryfikacja

```
  25/25 przeszło       test_assertion_gate.py
  RAZEM 105.333 s, 2068 testów, 110 modułów
kod=0
```

Zestaw przed pozycją: 2066 testów.

## 10. Czego świadomie nie zrobiono

Nie tknięto ścieżki wykonania testu — to 6.D54 i zostaje bez zmian. Nie dopisano
zakazu uruchamiania zestawu z wyłączonymi asercjami: to osobna pozycja (6.D71),
z własnym pomiarem i własną kontrolą.

Nie poprawiono bramki, która pilnuje runnera **dopasowaniem tekstowym** — to 6.D76,
i jest tam mierzone, że przechodzi ona na runnerze nieliczącym asercji. Nowe testy
tej pozycji są od niej niezależne: pytają o zachowanie, nie o treść pliku.
