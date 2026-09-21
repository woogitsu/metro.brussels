# 6.D340 · Jednostkę poza ostatnim członem niesie PIĘĆ nazw, a naprawdę cztery — i wszystkie cztery to `Per` albo zdanie

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `cd9fa69`

**POMIAR POWTÓRZONY PRZED COMMITEM, i to jest sprawdzenie, a nie deklaracja.** Przyrząd tej pozycji został zachowany, więc uruchomiłem go ponownie na bazie `91604c0`. Wynik odtwarza się co do jedynki: populacja **405** nazw, **pięciu** kandydatów, rozkład położeń `{0: 4, 1: 1}`, zero nazw z symbolem także na ostatnim członie, obie kontrole (`SecondsInPhase` i `SecondsSinceStopped` kandydatami, `M7_BODIES` nie). Daty pomiaru NIE przepisuję na dzisiejszą — liczby zmierzono 21.09.2026 na bazie `cd9fa69`.

6.D330 §8 zapisało, że `SecondsInPhase` i `SecondsSinceStopped` niosą jednostkę na
**pierwszym** członie, a przyrząd tamtej pozycji widzi tylko ostatni i liczy je jako
`phase` i `stopped`. Ta pozycja **liczy**; definicji przyrostka nie zmienia — podaje,
ile ta definicja pomija.

---

## 1. Kontrola przyrządu przechodzi w DWÓCH warunkach z trzech, a trzeciego nie da się spełnić

```
   SecondsInPhase           kandydat=True  (['seconds', 'in', 'phase'], [0])
   SecondsSinceStopped      kandydat=True  (['seconds', 'since', 'stopped'], [0])
   M7_BODIES                kandydat=False
```

Pole żądało, żeby `M7_BODIES` wyszedł w klasie „odrzucone po przeczytaniu". **Nie
wychodzi, bo nie wchodzi do populacji w ogóle** — i powód jest w rozbijaczu nazw,
nie w czytaniu:

```
M7_BODIES                ['m7', 'bodies']
SDK_NA_DYSKU             ['sdk', 'na', 'dysku']
```

**`M7` jest JEDNYM członem, nie `M` plus `7`.** Reguła 6.D320 rozbija `[A-Z][a-z0-9]*`,
więc cyfra przykleja się do litery. Ostrzeżenie pola („`M` w `M7_BODIES` jest
oznaczeniem taboru") opisuje więc rozjazd, którego ten rozbijacz nie produkuje —
tak samo `S` w `SDK_NA_DYSKU`, gdzie członem jest `sdk`.

Jest to **trzeci raz w tej sesji**, gdy warunek kontroli zapisany w polu nazywa coś,
czego przyrząd nie umie wytworzyć (6.D330 §3 — `Hz`; 6.D337 §1 — jednostka pytania;
teraz `M7_BODIES`). Za każdym razem przyczyną było przeniesienie do pola zdania
z cudzego raportu **bez sprawdzenia, czy przyrząd to zdanie może potwierdzić**.

## 2. Usterka przyrządu: zbiór symboli z PRZYROSTKÓW jest węższy niż lista jednostek

Pierwsza wersja brała symbole z przyrostków znalezionych przez 6.D330 i dała
**dwa** kandydaty. Ten zbiór nie zawiera `microseconds`, `metres` ani `milliseconds`
— **bo przyrostkiem nikt tak nie pisze**. Na członie pierwszym pisze się właśnie tak.

Po wzięciu unii z listami 6.D320 (`JEDN_DLUGIE`, `JEDN_KROTKIE`) plus `mm`, `us`,
`px` z 6.D329 i 6.D330: **2 → 5**.

Zgłaszam to, zamiast poprawić po cichu, bo usterka jest pouczająca: **zbiór
symboli zebrany z JEDNEGO położenia nie opisuje innego położenia.**

## 3. Trzy liczby, których żądało pole

```
=== KANDYDACI: symbol jednostki na czlonie INNYM niz ostatni ===
   razem: 5
   rozklad po POZYCJI czlonu: {0: 4, 1: 1}
   z nich majacych symbol TAKZE na ostatnim czlonie: 0

MicrosecondsPerStep    src/    microseconds·per·step     [0]
SecondsInPhase         src/    seconds·in·phase          [0]
SecondsSinceStopped    src/    seconds·since·stopped     [0]
UV_METRES_PER_UNIT     tools/  uv·metres·per·unit        [1]
a_brake                tools/  a·brake                   [0]
```

**Przeczytałem wszystkie pięć.** Cztery niosą jednostkę naprawdę, jedna nie:

| nazwa | czytanie | werdykt |
|---|---|---|
| `SecondsSinceStopped` | „Czas od zatrzymania; ujemny znaczy «jeszcze nie stanął»" | **sekundy** |
| `SecondsInPhase` | zwraca `_cycle.At(…).ElapsedInPhaseSeconds` | **sekundy** |
| `MicrosecondsPerStep` | „Średni czas jednego kroku w mikrosekundach"; `WallSeconds * 1e6 / Steps` | **mikrosekundy** |
| `UV_METRES_PER_UNIT` | metry na jednostkę UV, podawane do `chunk_records` | **metry** |
| `a_brake` | `a_brake = 0.0` obok `s`, `v`, `grade_a` w symulacji hamowania — `a` to **przyspieszenie**, nie amper | **ODRZUCONE** |

```
   nazw z symbolem poza ostatnim członem:        5
   z nich niosących jednostkę NAPRAWDĘ:          4
   odrzuconych po przeczytaniu:                  1
   najczęstsze położenie:                        człon PIERWSZY (4 z 5)
```

**`a_brake` odrzucam z tego samego powodu co `DesignDavisA` w 6.D330 §5:** `a` jest
symbolem **wielkości**, nie jednostki. Ta sama litera stoi w `JEDN_KROTKIE` jako
amper i w prozie fizyki jako przyspieszenie, a rozstrzyga dopiero kod obok.

**Przewidywanie O3 jest OBALONE** — odrzucona jest jedna z pięciu, nie większość —
i wypełniam warunek obalenia spisany przed pomiarem: **definicja przyrostka z 6.D330
pomija realną klasę, i liczy ona CZTERY nazwy.**

## 4. GŁÓWNE ZNALEZISKO: wszystkie cztery to `Per` albo zdanie

Cztery prawdziwe dzielą się na dwie rodziny, i żadna nie jest niedbałością:

* **LICZNIK ułamka przed `Per`, dwie nazwy:** `MicrosecondsPerStep`,
  `UV_METRES_PER_UNIT`. Jednostka **musi** stać przed `Per`, bo po nim stoi
  mianownik.
* **Jednostka OTWIERAJĄCA zdanie, dwie nazwy:** `SecondsInPhase`,
  `SecondsSinceStopped`. Nazwa czyta się jak zdanie — „sekundy od zatrzymania" —
  i jednostka jest w nim podmiotem.

**To domyka rachunek z 6.D339.** Tamta pozycja zmierzyła **pięć** nazw, w których
jednostka stoi po `Per`, czyli jest **mianownikiem** (`RatePerSecond`,
`StepsPerSecond`, `ControlNotchRatePerSecond`, `_ratePerSecond`,
`resistance_per_kg`). Tutaj wychodzą **dwie**, w których stoi przed `Per`, czyli
jest **licznikiem**. Razem **siedem nazw, w których konstrukcja `Per` wypycha
jednostkę z pozycji przyrostka** — i to jest jedyna systematyczna przyczyna, dla
której definicja przyrostka z 6.D330 czegoś nie widzi.

## 5. Przewidywania — jedno trafione, pięć obalonych

| # | przewidywanie | wynik |
|---|---|---|
| O1 | kontrola przejdzie dla wszystkich trzech | **OBALONE**: dwa z trzech, trzeciego nie da się spełnić (§1) |
| O2 | kandydatów więcej niż dziesięć | **OBALONE**: pięć |
| O3 | większość odrzucona po przeczytaniu | **OBALONE**: jedna z pięciu (§3) |
| O4 | najczęstszym położeniem będzie człon pierwszy | **trafione**: cztery z pięciu |
| O5 | wśród odrzuconych po jednej z każdego korpusu | **OBALONE**: odrzucona jest jedna, i to z `tools/` |
| O6 | nazwa z jednostką na środkowym I ostatnim członie | **OBALONE**: zero |

**Pięć obaleń z sześciu, i wszystkie z jednego założenia**: że klasa jest duża
i zaśmiecona. Jest mała i czysta — pięć nazw, cztery prawdziwe, jedna pomyłka
symbolu, którą rozstrzygnęło czytanie.

## 6. Czego świadomie nie zrobiłem

Nie zmieniłem definicji przyrostka z 6.D330, nie przemianowałem żadnej nazwy, nie
postawiłem bramki na położeniu jednostki, nie tknąłem `docs/04-conventions.md`,
`src/` ani `data/` — wszystko to stoi w polu „Poza zakresem".

**Nie poprawiłem warunku kontroli w polu tej pozycji**, choć §1 pokazuje, że jest
niespełnialny. Przepisanie zatarłoby ślad po wzorcu, który ta sesja zmierzyła już
trzy razy.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

`UV_METRES_PER_UNIT` jest jedyną nazwą w całej populacji, w której jednostka stoi na
członie **drugim**, a nie pierwszym ani ostatnim — i jedyną, która pisze metr słowem
(`metres`), a nie symbolem `M`. Według 6.D339 metr ma w nazwach **jeden** zapis,
`M`; ta nazwa go nie łamie tylko dlatego, że tamten pomiar patrzył na przyrostki,
a tutaj `metres` przyrostkiem nie jest. Dwa pomiary, dwie prawdy, jedna nazwa —
zapisuję to, bo bez tego zdania wyglądałyby na sprzeczne.
