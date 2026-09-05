# Triaż 9 ocalałych mutacji `tools/blender/m7_report.py` — wszystkie dziewięć równoważne

**Zmierzone 05.09.2026 na commicie:** `8c3f752`

Pozycja 6.B7 mówi: „udział modułu schodzi z 29 % poniżej 10 % (najwyżej 3 z 31)".
**Tego kryterium nie da się spełnić uczciwie.** Każda z dziewięciu ocalałych mutacji to
przestawienie `<=` na `<` albo `>` na `>=` w progu porównania, a różnica między
oryginałem a mutantem wymaga trafienia w próg **co do bitu**. Dla sześciu z nich takie
trafienie jest w arytmetyce podwójnej precyzji **niemożliwe**, dla trzech pozostałych
niemożliwe przy danych z `data/vehicle/m7-spec.json`, a dla czterech pierwszych — nawet
gdy próg zostanie trafiony — wynik funkcji jest identyczny.

Ten raport daje werdykt dla każdej z dziewięciu, z pomiarem przy każdym, i **zgłasza tę
sprzeczność zamiast naginać liczbę**. Rozstrzygnięcie należy do właściciela; sekcja 6
mówi, co dokładnie jest do rozstrzygnięcia.

## 0. Ostrzeżenie o poprzednim pomiarze

Pierwszy dzisiejszy przebieg tej pozycji dał `31/31 zabitych, 0 ocalałych` i był
**fałszywy**: narzędzie miało zepsutą wyrocznię, opisaną w
`reports/wyrocznia-mutacyjna-falszywe-zabicia.md` (scalenie #268). Liczby niżej pochodzą
z przebiegu po naprawie, z kalibracją wyroczni w drzewie bez mutacji:

```
[MUTACJE] 31 mutacji do policzenia, 2 robotników, commit 8c3f752, klasy operator,prog
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] wykonywanych wierszy dotyczy 31 z 31 mutacji; pozostałe 0 siedzą w kodzie,
          którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 31/31, zabitych 22, ocalałych 9 (w tym 0 nieuruchomionych)
```

Dziewięć ocalałych, ta sama dziewiątka co w `reports/mutation-sweep.md`. Żadna nie ocalała
z powodu nieuruchomienia — sonda pokrycia mówi `wykonana=True` przy każdej.

## 1. Dziewięć mutacji, po `plik:wiersz:przesunięcie`

Rozróżnienie po przesunięciu jest tu konieczne, nie formalne: wiersze 46 i 52 niosą po
dwa `<=` i to dwie różne mutacje.

| id | kod | zmiana |
|---|---|---|
| `m7_report.py:46:1778` | `if start - 1e-9 <= nose_end <= end + 1e-9:` | lewe `<=` → `<` |
| `m7_report.py:46:1790` | to samo | prawe `<=` → `<` |
| `m7_report.py:52:2153` | `if start - 1e-9 <= candidate <= end + 1e-9:` | lewe `<=` → `<` |
| `m7_report.py:52:2166` | to samo | prawe `<=` → `<` |
| `m7_report.py:85:3308` | `if abs(abs(point[1]) - layout.half_width) > VERTEX_EPS:` | `>` → `>=` |
| `m7_report.py:87:3400` | `key = (round(point[0], 4), 1 if point[1] > 0 else -1)` | `>` → `>=` |
| `m7_report.py:95:3722` | `has_bottom = any(abs(z - door["z0"]) <= VERTEX_EPS …)` | `<=` → `<` |
| `m7_report.py:96:3801` | `has_top = any(abs(z - door["z1"]) <= VERTEX_EPS …)` | `<=` → `<` |
| `m7_report.py:169:7495` | `… abs(opening["measured_width_m"] - layout.door_width) > TOLERANCE_M` | `>` → `>=` |

## 2. Werdykty — trzy różne powody, nie jeden

### 2a. Wiersze 46 i 52 (cztery mutacje): próg trafialny, wynik i tak ten sam

Te cztery porównania decydują, czy punkt podziału `nose_end` albo `candidate` wpada
w przedział `[start, end]` z pasmem ochronnym 1e-9. Mutant różni się od oryginału
dokładnie wtedy, gdy `start - 1e-9 == nose_end` albo `candidate == end + 1e-9`.

To trafienie **jest osiągalne** — `start = nose_end + 1e-9` daje je co do bitu:

```
start=2.400000001  start-1e-9==2.4: True
```

Nie zmienia to jednak niczego w wyniku, bo do zbioru trafia `round(nose_end, 6)`,
a `round(start, 6)` już tam jest i jest tą samą liczbą: **pasmo ochronne 1e-9 jest tysiąc
razy węższe niż krok zaokrąglenia**.

```
round(start,6)=2.4  round(prog,6)=2.4  równe: True
```

Pomiar różnicowy na czterech wariantach `x_stations`, po jednej mutacji na wariant:

```
wejść: 404, w tym trafień DOKŁADNIE w próg: 129
  w.46 lewe `<=`     różnic w wyniku: 0
  w.46 prawe `<=`    różnic w wyniku: 0
  w.52 lewe `<=`     różnic w wyniku: 0
  w.52 prawe `<=`    różnic w wyniku: 0
```

Liczba 129 jest tu ważniejsza od 404: bez trafień w próg pomiar sprawdzałby wyłącznie
wejścia, na których oba warianty są tożsame z definicji, i nie mówiłby o mutacji nic.

**Werdykt: równoważne.** To jedyna czwórka, dla której nie mam dowodu dla wszystkich
liczb podwójnej precyzji, tylko pomiar na 404 wejściach dobranych pod próg. Różnica
wymagałaby, żeby granica zaokrąglenia do sześciu miejsc wypadła wewnątrz pasma 1e-9
i **jednocześnie** próg został trafiony co do bitu.

### 2b. Wiersze 85, 95, 96, 169 (cztery mutacje): próg nieosiągalny w IEEE 754

Każde z tych porównań zestawia różnicę dwóch liczb ze stałym progiem. Mutacja jest
rozstrzygalna tylko przy równości dokładnej — a wynik odejmowania wokół podstawy leży na
siatce o kroku `ulp(podstawa)` i próg na tę siatkę nie trafia. Przeszukanie ±5000 ulpów
wokół rozwiązania dokładnego:

```
okno przeszukania: +/-5000 ulpów wokół rozwiązania dokładnego

w.85  abs(abs(y) - 1.35) == 1e-4  (y > 0)      NIEOSIĄGALNE  ulp=2.220e-16 prog/ulp=450359962737.049622
w.85  abs(abs(y) - 1.35) == 1e-4  (y < 0)      NIEOSIĄGALNE  ulp=2.220e-16 prog/ulp=450359962737.049622
w.95/96  abs(z - 0.9) == 1e-4                  NIEOSIĄGALNE  ulp=1.110e-16 prog/ulp=900719925474.099243
w.95/96  abs(round(z,4) - 0.9) == 1e-4         NIEOSIĄGALNE  ulp=1.110e-16 prog/ulp=900719925474.099243
w.169  abs(szer - 1.6) == 1e-3                 NIEOSIĄGALNE  ulp=2.220e-16 prog/ulp=4503599627370.496094
w.169  abs(round(szer,4) - 1.6) == 1e-3        NIEOSIĄGALNE  ulp=2.220e-16 prog/ulp=4503599627370.496094

KONTROLA DODATNIA — te same wyrażenia z podstawą, przy której próg
JEST wielokrotnością ulp, więc trafienie musi istnieć:
kontrola  abs(y - 0.0) == 1e-4                 OSIĄGALNE     ulp=1.355e-20 prog/ulp=7378697629483821.000000
kontrola  abs(y - 1.0) == 0.5                  OSIĄGALNE     ulp=2.220e-16 prog/ulp=2251799813685248.000000
```

Rozstrzyga kolumna `prog/ulp`: końcówki `.049622`, `.099243` i `.496094` znaczą, że próg
**nie jest** wielokrotnością kroku siatki. Kontrola dodatnia pokazuje, że ten sam skrypt
znajduje trafienie tam, gdzie ono istnieje — bez niej „NIEOSIĄGALNE" mogłoby być po
prostu błędem w pętli.

**Werdykt: równoważne, dowodliwie.** Żaden test nie zabije tych czterech, bo żadna liczba
podwójnej precyzji ich nie rozróżnia. Zależy to od podstaw `1.35`, `0.9` i `1.6`,
czyli od `data/vehicle/m7-spec.json`; przy innych wymiarach wniosek trzeba przeliczyć.

### 2c. Wiersz 87 (jedna mutacja): kod za filtrem, który wyklucza jedyną różniącą wartość

`1 if point[1] > 0 else -1` różni się od `>=` wyłącznie przy `point[1] == 0.0`
(albo `-0.0`). Ten wiersz stoi jednak zaraz za filtrem z wiersza 85, który przepuszcza
tylko wierzchołki o `|y|` bliskim połowie szerokości pudła:

```
half_width z domyślnego layoutu: 1.35
y == 0.0 przechodzi filtr w.85?  False
y == -0.0 przechodzi filtr w.85?  False
najmniejsze |y|, jakie filtr przepuszcza: 1.3499
czyli 0.0 jest odległe od dopuszczonego pasma o 1.3499 m = 13499 razy szerokość pasma

kontrola dodatnia, half_width = 5e-05: y == 0.0 przechodzi filtr?  True
```

Kontrola dodatnia mówi, przy jakim warunku wniosek by upadł: gdyby połowa szerokości
zeszła poniżej `VERTEX_EPS`, zero przeszłoby filtr i mutacja stałaby się rozstrzygalna.
Przy 1,35 m do tego brakuje czterech rzędów wielkości.

**Werdykt: równoważne przy geometrii M7.**

## 3. Ile testów dopisałem: zero, i to jest wynik

`CLAUDE.md` §8 zabrania zadań wymyślonych na miejscu, a test przybijający zachowanie,
którego żadne wejście nie odróżnia, jest dokładnie tym: kupuje procent w tabeli pokrycia
i nie mówi nic o module. Gdyby taki test powstał, jego jedyną treścią byłoby „ten mutant
jest równoważny", a to jest zdanie do raportu, nie do zestawu.

Zestaw zostaje bez zmian:

```
$ python3 tools/tests/test_all.py
  1601/1601 przeszło
```

## 4. Co przy okazji widać w module, a czego nie ruszam

**Pasmo ochronne 1e-9 w wierszach 46 i 52 jest w praktyce martwe.** Wszystko, co przez nie
wchodzi albo wypada, i tak przechodzi przez `round(…, 6)`, czyli siatkę tysiąc razy
grubszą. Nie znaczy to, że jest szkodliwe — znaczy, że jego szerokość nie ma dziś
znaczenia i można ją zmienić o trzy rzędy wielkości w obie strony bez żadnego skutku.
Zmiana należy do właściciela; tu jest tylko zapisana.

**`VERTEX_EPS = 1e-4` i `TOLERANCE_M = 0.001` są nietestowalne na granicy z tej samej
przyczyny:** obie są potęgami dziesiątki, a podstawy porównań (1,35 m, 0,9 m, 1,6 m) nie
są dokładnie reprezentowalne. Gdyby progi wyrazić jako wielokrotności ulp podstawy albo
porównywać przez `math.isclose`, granica stałaby się osiągalna i te mutacje dałyby się
zabić. Jest to zmiana projektowa w kodzie, którego zadanie nie obejmuje.

## 5. Czego ten triaż świadomie nie zrobił

- **Nie ruszył `data/vehicle/m7-spec.json`.** `data/` jest do odczytu, a wymiary M7 są
  poza zakresem tej pozycji wprost.
- **Nie przepisał `reports/mutation-sweep.md`.** Jego wiersz 9 / 31 był prawdą na
  `66b8301` i jest prawdą dziś; datowanego pomiaru się nie przelicza.
- **Nie zmienił progów w module.** Sekcja 4 mówi, co by to dało; decyzja nie jest moja.

## 6. Sprzeczność do rozstrzygnięcia przez właściciela

Kryterium „**Skończone, gdy**" pozycji 6.B7 żąda najwyżej 3 ocalałych z 31. Uczciwy triaż
zostawia 9, bo tyle jest mutantów równoważnych. Trzy wyjścia, w kolejności od najtańszego:

1. **Przyjąć dziewięć werdyktów „równoważny" i poprawić kryterium** na „każda z 9 ma
   werdykt poparty pomiarem". Nic w kodzie się nie zmienia; kolejka przestaje żądać
   liczby, której nie da się osiągnąć bez oszustwa.
2. **Zmienić progi w module** tak, żeby granice stały się osiągalne (sekcja 4) — wtedy
   te mutacje dadzą się zabić testami granicznymi. Kosztuje zmianę zachowania kodu,
   który dziś działa, i wymaga własnego zadania z własnym pomiarem.
3. **Wyłączyć mutanty równoważne z mianownika** przeglądu, z rejestrem powodów.
   Rozwiązuje klasę, nie ten jeden przypadek, ale wymaga miejsca na rejestr i bramki,
   która pilnuje, żeby nie stał się workiem na niewygodne mutacje.

Rekomendacja: **1**, i osobno rozważyć 3 jako pozycję kolejki. Wyjście 2 zmienia kod pod
metrykę, co jest tą samą pomyłką co dopisanie testu do mutanta równoważnego, tylko droższą.

## 7. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/mutation_sweep.py --only m7_report.py --workers 2 \
      --operators operator,prog --journal build/b7-prawdziwy.jsonl
[MUTACJE] rozstrzygniętych 31/31, zabitych 22, ocalałych 9 (w tym 0 nieuruchomionych),
          nierozstrzygniętych 0
  OCALAŁA  tools/blender/m7_report.py:46 operator `<=` -> `<`
  OCALAŁA  tools/blender/m7_report.py:46 operator `<=` -> `<`
  OCALAŁA  tools/blender/m7_report.py:52 operator `<=` -> `<`
  OCALAŁA  tools/blender/m7_report.py:52 operator `<=` -> `<`
  OCALAŁA  tools/blender/m7_report.py:85 operator `>` -> `>=`
  OCALAŁA  tools/blender/m7_report.py:87 operator `>` -> `>=`
  OCALAŁA  tools/blender/m7_report.py:95 operator `<=` -> `<`
  OCALAŁA  tools/blender/m7_report.py:96 operator `<=` -> `<`
  OCALAŁA  tools/blender/m7_report.py:169 operator `>` -> `>=`

$ python3 tools/tests/test_all.py
  1601/1601 przeszło
```

Zestaw nie zmienia się ani o jeden test — sekcja 3 mówi dlaczego.
