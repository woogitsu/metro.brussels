# 6.D307 · Przeterminowanych cytatów jest ZERO — i to zero jest własnością HISTORII, nie przyrządu

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `ffa406f`

6.D298 zmierzyło, że nazwa typu publicznego `src/` pada w 73 plikach `.py` pod `tools/`,
a źródła C# czyta tylko 32 z nich. Różnica to **proza** — docstringi i komentarze bramek
cytujące nazwy typów, i nikt nie sprawdza, czy cytowany typ jeszcze istnieje.

Odpowiedź na pytanie zadane wprost: **ani jednego**. Pole dopuszczało tę odpowiedź
i żądało, żeby powiedzieć ją wprost. Mówię — ale dopiero po sprawdzeniu, **czy przyrząd
mógł w ogóle zobaczyć cokolwiek innego**, bo to jest ten sam kształt, o który potknęły
się 6.D294, 6.D295 i 6.D303.

---

## 1. KONTROLA PRZYRZĄDU NAJPIERW PADŁA — i to jest znalezisko o samym POLU

Pole żąda: `DriverBinding` i `FirstRun` mają wyjść jako nazwy stojące w prozie oraz
w igle; przyrząd, który ich nie widzi, gubi także resztę. Pole każe też **pożyczyć**
czytnik `typy_publiczne` z `test_csharp_type_callers.py`.

Pożyczyłem i kontrola **padła**:

```
DriverBinding    typ publiczny: False   w prozie: False
FirstRun         typ publiczny: False   w prozie: False
```

Przyczyna nie jest w moim przyrządzie i ustaliłem ją **czytaniem kodu**, a nie domysłem:

```python
RDZEN = "src/Sim/"
def typy_publiczne(zrodla=None, root=ROOT, przedrostek=RDZEN):
```

Czytnik ma domyślny przedrostek **`src/Sim/`**, a oba typy kontrolne stoją w `src/Game/`
(`src/Game/Input/DriverActions.cs` i `src/Game/FirstRun.cs`). Zmierzone na obu zasięgach:

```
przedrostek=src/Sim/   typow: 109   DriverBinding: False  FirstRun: False
przedrostek=src/       typow: 156   DriverBinding: True   FirstRun: True
```

**Sto pięćdziesiąt sześć to dokładnie liczba, którą podaje 6.D298** — czyli pole „Wejście"
nazywa czytnik w jego zasięgu domyślnym, a pole „Weryfikacja" stawia warunek na populacji
**szerszej**, tej z 6.D298. Dwa pola tego samego bloku opisują **dwie różne populacje**.

Jest to ta sama usterka mianownika, którą 6.D292 zmierzyło na nazwach wszechobecnych,
a 6.D301 znalazło w prozie zadań — tylko o piętro wyżej: nie w zdaniu o udziale, lecz
w **parze pól jednego bloku**. Pracuję dalej na zasięgu, którego żąda kontrola
(`przedrostek="src/"`), i **nie naciągam własnej definicji**, żeby te dwie nazwy wyszły
przy zasięgu domyślnym. Warunek obalenia spisałem przed pomiarem dokładnie na ten wypadek.

Przy `przedrostek="src/"` kontrola przechodzi:

```
DriverBinding    typ publiczny: True   w prozie: True   plikow prozy:  1
FirstRun         typ publiczny: True   w prozie: True   plikow prozy: 15
```

## 2. TRZY LICZBY, których żądało pole „Wyjście"

```
typow publicznych src/ (przedrostek="src/"):   156
blokow prozy pod tools/:                     16636

nazw typow padajacych w PROZIE:                 56
   plikow prozy z taka nazwa:                   43
nazw typow w PRZYPIECIU:                        39
   wylacznie w przypieciu, NIGDY w prozie:      17
   wylacznie w prozie, nigdy w przypieciu:      34
   w obu:                                       22
```

**Rozróżnienie prozy od przypięcia zmienia odpowiedź dokładnie dwukrotnie** — trzydzieści
cztery nazwy stoją wyłącznie w prozie wobec siedemnastu wyłącznie przypiętych. Pole
ostrzegało, że pomylenie tych dwóch rzeczy zmienia odpowiedź dziesięciokrotnie (6.D298 §3);
na tej populacji mnożnik jest mniejszy, ale kierunek ten sam i **liczby są rozłączne**.

## 3. TRZECIA LICZBA: cytatów przeterminowanych ZERO — z kontrolą, która to znaczy

Kandydatów szukałem wśród nazw w **grawisach** w prozie, bo grawis jest w tym korpusie
znakiem cytatu, a nie zwykłej polszczyzny:

```
nazw PascalCase w grawisach w prozie:          143
   jest dzisiejszym typem publicznym src/:      23
   nie jest:                                   120
   z tego NIE jest tez nazwa pythonowa tools/: 115
```

Rozstrzygnięcie **nie po wyglądzie, tylko po historii**: nazwa jest przeterminowanym
cytatem wtedy i tylko wtedy, gdy `git log -S` znajduje jej deklarację w `src/`
kiedykolwiek, a dziś jej tam nie ma.

```
CYTATY PRZETERMINOWANE: 0
```

**I tu zaczyna się właściwa robota tej pozycji**, bo zero bez kontroli nie odróżnia
pustego zbioru od oślepłego przyrządu.

**Kontrola pozytywna — czy sonda w ogóle widzi deklaracje w historii:**

```
FirstRun:       'class'  -> 1 commitow
DriverBinding:  'record' -> 1 commitow
```

Widzi, i to dopasowując właściwe słowo kluczowe do właściwego typu (jeden jest klasą,
drugi rekordem). Przyrząd nie jest ślepy.

**Powód zera, zmierzony osobno:**

```
skasowanych plikow .cs w historii src/:                   0
usunietych deklaracji typu w historii src/ (wiersze "-"): 0
```

**Z `src/` nie zniknął nigdy ANI JEDEN typ** — ani przez skasowanie pliku, ani przez
usunięcie deklaracji z pliku, który przeżył. Zbiór, z którego mógłby pochodzić
przeterminowany cytat, jest **pusty z powodu historii drzewa**.

## 4. Czym to zero RÓŻNI SIĘ od zer z 6.D294, 6.D295 i 6.D303

Tamte trzy zera były własnością **przyrządu**: wzorzec zbudowany z dzisiejszego rejestru
nie mógł wydobyć nazwy, której w nim nie ma (6.D294); dwa pola krotki liczone były tym
samym wyrażeniem, więc nie mogły się różnić (6.D295); zbiór nazw zniknionych z rejestru
był pusty, więc nie miał czego dopasować (6.D303).

**To zero jest własnością DRZEWA.** Przyrząd działa — pokazuje to kontrola pozytywna —
a populacja jest pusta, bo w tym projekcie żaden typ jeszcze nie umarł. Różnica jest
praktyczna, nie stylistyczna: tamte zera znikną dopiero po zmianie przyrządu, a **to
zniknie samo**, przy pierwszym usuniętym typie.

Konsekwencja dla bramki, którą ta pozycja miała przygotować: bramka „czy cytowany typ
jeszcze istnieje" byłaby dziś bramką **nad zbiorem pustym**. Nie znaczy to, że jest
niepotrzebna — znaczy, że **jej pierwszy prawdziwy przebieg odbędzie się dopiero wtedy,
gdy ktoś usunie typ**, i że do tego czasu nie da się jej odróżnić od bramki zepsutej.
To jest dokładnie rodzina 6.D27.

## 5. Przewidywania spisane PRZED pomiarem — i tym razem NIEZALEŻNE

Zapisuję to jako pierwszą rzecz o przewidywaniach, bo przy 6.D306 było odwrotnie
i tam odnotowałem, że siedem trafień nic nie znaczy: **tej pozycji nie mierzył wcześniej
żaden agent**, więc przedziały nie były przepisane z cudzego wyniku.

| # | przewidywanie | wynik |
|---|---|---|
| U1 | nazw typów w prozie: 40–90 | trafione (56) |
| U2 | plików prozy: 25–60 | trafione (43) |
| U3 | cytatów przeterminowanych: **1–8, na pewno nie zero** | **OBALONE — zero** |
| U4 | kontrola przyrządu przejdzie | trafione **dopiero po rozstrzygnięciu zasięgu**; przy zasięgu domyślnym PADŁA |
| U5 | nazw wyłącznie przypiętych: 5–25 | trafione (17) |
| U6 | podział proza/przypięcie zmieni odpowiedź co najmniej dwukrotnie | trafione (34 wobec 17, czyli dokładnie dwa razy) |

**U3 jest obalone i powód jest pouczający.** Rozumowałem tak: 6.B25 skasowało stałe,
a ich nazwy **zostały w prozie** (zmierzyłem to przy 6.D303 — `MIN_RADIUS_M` pada dziś
w czterech plikach, choć stała nie żyje). Założyłem, że typy zachowują się jak stałe.
**Nie zachowują się** — i różnica nie jest w higienie prozy, tylko w tym, że stałe w tym
projekcie **bywają usuwane**, a typy **nie były usuwane nigdy**. Przeniosłem regułę
z populacji, która umiera, na populację, która jeszcze nie zaczęła.

## 6. Czego świadomie nie zrobiono

- **Nie poprawiono ani jednego zdania prozy** i nie usunięto żadnego przypięcia —
  pole „Poza zakresem" zabrania obu.
- **Nie postawiono bramki na wyniku.** §4 mówi wprost, dlaczego byłaby dziś bramką nad
  zbiorem pustym; to jest argument do rozstrzygnięcia, a nie samo rozstrzygnięcie.
- **Nie zmieniono `RDZEN` ani domyślnego przedrostka `typy_publiczne`**, choć §1 pokazuje
  rozjazd między dwoma polami tego bloku. Czytnik jest cudzy, a jego zasięg ma **powód
  zapisany w komentarzu obok** (zawężenie w ciele wymusiłoby drugą kopię czytnika).
  Poprawić należy **pole**, nie czytnik — i to jest osobna decyzja.
- **Nie policzono, ile z 115 nazw w grawisach to typy frameworka .NET, a ile klasy
  Pythona spoza `tools/`** — pytanie szersze niż pole.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 7. Zauważone przy okazji, nietknięte

1. **Sto dwadzieścia nazw w grawisach w prozie bramek nie jest dzisiejszym typem `src/`,
   a sto piętnaście nie jest też nazwą pythonową pod `tools/`.** Czym są, ta pozycja nie
   pyta: część to typy frameworka (`StringBuilder`, `JsonSerializer`), część nazwy
   plików i narzędzi. Ale to znaczy, że **grawis w tej prozie cytuje głównie coś spoza
   tego repozytorium**, i żadna bramka nie wie, co.
2. **`FirstRun` pada w prozie piętnastu plików, a `DriverBinding` w jednym** — przy
   obu typach istniejących i obu wymienionych imiennie przez 6.D298. Rozkład cytatów
   po typach jest więc bardzo nierówny i nikt go nie liczył.
3. **Żaden typ nigdy nie zniknął z `src/`** (§3). Jest to liczba o projekcie, nie
   o bramkach: przy 903 stałych żyjących i 73 kiedykolwiek usuniętych (6.D303) populacja
   stałych ma już swoją śmiertelność, a populacja typów jeszcze nie.
