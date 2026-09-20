# 6.D308 · Trzydzieści dwie kolizje złośliwe — a największa z nich jest NAJBARDZIEJ ROZMYŚLNYM kodem w repozytorium

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `3c93a5d`

6.D299 zmierzyło, że skan po samej nazwie składnika myli się w 85 % wołań: z dwustu
dwudziestu siedmiu znalezionych do właściwego typu należą trzydzieści cztery. Pięć
z siedmiu badanych tam nazw kolidowało między typami. Ta pozycja liczy, ile takich
kolizji ma całe `src/`.

Odpowiedź: **102 nazwy kolidują, a 32 z nich zwracają różne typy.** Ale liczba, dla
której warto było tę pozycję wziąć, jest inna: **zero** z tych trzydziestu dwóch to
nazwa zwyczajowa, a największa z nich jest **idiomem stosowanym rozmyślnie i
konsekwentnie**.

---

## 1. Kontrola przyrządu — ZDANA co do nazwy, nie tylko co do liczby

Pole żąda, żeby `Assumptions` wyszło jako nazwa o **czterech** typach deklarujących
i o różnych typach zwracanych (6.D299 §2).

```
KONTROLA PRZYRZADU: Assumptions
   typow deklarujacych: 4 ['BrakeAdhesionLimit', 'DriveScenario',
                           'LineRunSettings', 'SignallingPlan']
   typow zwracanych   : 3 ['IReadOnlyList<BrakingAssumption>',
                           'IReadOnlyList<ScenarioAssumption>',
                           'IReadOnlyList<SignallingAssumption>']
```

Cztery typy i **te same cztery nazwy**, które 6.D299 wypisało imiennie. Kontrola
sprawdza tu więcej, niż żądało pole: zgadza się nie tylko licznik, ale i skład zbioru.

**Zasięg wzięty z 6.D307 §1, a nie domyślny.** `typy_publiczne` ma domyślny przedrostek
`src/Sim/`, a `Assumptions` deklarują typy z całego `src/`; przy zasięgu domyślnym
kontrola nie miałaby czego znaleźć. Jest to ta sama pułapka, którą ta poprzednia pozycja
zmierzyła dobę wcześniej — i **jedyny powód, dla którego jej tu nie powtórzyłem**.

## 2. TRZY LICZBY, których żądało pole „Wyjście"

```
typow publicznych src/:                       156
roznych nazw skladnikow publicznych:          527
nazw deklarowanych przez WIECEJ NIZ JEDEN typ: 102
   z nich zwracajacych ROZNE typy:             32
najwieksza liczba typow na jedna nazwe:        45  (ToString)
```

**Kolizja sama w sobie jest normą, nie usterką:** co piąta nazwa składnika w tym
drzewie jest deklarowana przez więcej niż jeden typ. Psuje skan dopiero ta, która
zwraca **co innego** — i takich jest trzydzieści dwie, czyli **jedna trzecia kolizji**.

## 3. DEFINICJA MA DWA CZYTANIA, a liczba, o którą pyta pole, jest w obu TA SAMA

Największa kolizja — `ToString` z czterdziestoma pięcioma typami — nie jest kolizją
między typami tego projektu, tylko **przesłonięciem** `object.ToString()`. Policzyłem
więc oba czytania, zamiast wybrać po cichu:

| | nazw | kolizji | **złośliwych** | największa |
|---|---|---|---|---|
| z przesłonięciami | 527 | 102 | **32** | `ToString` (45 typów) |
| bez przesłonięć | 525 | 101 | **32** | `M7` (13 typów) |

**Liczba złośliwych jest identyczna: 32.** Wybór czytania zmienia **czoło listy**,
a nie odpowiedź, o którą pole pyta — bo `ToString` zwraca `string` we wszystkich
czterdziestu pięciu wypadkach i do klasy złośliwych nie wchodzi w żadnym czytaniu.

Jest to ten sam kształt, który zmierzyłem dobę wcześniej przy 6.D306: tam wąskie
i szerokie czytanie „czytnika drzewa" przesunęło jeden moduł na trzydzieści dziewięć.
**Dwa razy z rzędu definicja okazała się ważna dla rankingu i nieważna dla liczby.**

## 4. ZERO nazw zwyczajowych — i lista była spisana PRZED pomiarem

Pole żąda powiedzieć wprost, ile z nazw złośliwych to nazwy zwyczajowe w rodzaju
`Count` albo `Id`, i dopuszcza odpowiedź „wszystkie".

```
z zlosliwych nazw ZWYCZAJOWYCH: 0   []
```

Lista, na której to sprawdziłem, stoi w moich definicjach spisanych przed pomiarem:
`Count`, `Id`, `Name`, `Length`, `Value`, `Key`, `Index`, `Item`, `Total`, `Kind`,
`Type`, `Size`. **Nie trafiła ani jedna.** Spisanie jej wcześniej jest tu treścią:
lista dobrana po obejrzeniu wyniku mogłaby dać dowolną odpowiedź.

**Wniosek jest mocniejszy niż zero.** Kolizje, które naprawdę psują skan po nazwie,
nie są przypadkowymi zbiegami na nazwach ogólnych — są **nazwami dziedzinowymi**:
`Parse`, `FromJson`, `Apply`, `Step`, `Load`, `Plan`, `Assumptions`, `Phase`,
`Profile`, `Variant`, `Trains`, `Build`, `Protection`, `Advance`. To są nazwy dobrane
celowo i celowo powtórzone, bo opisują **tę samą operację na różnych typach**.

## 5. NAJWIĘKSZA KOLIZJA ZŁOŚLIWA JEST NAJBARDZIEJ ROZMYŚLNYM KODEM W REPOZYTORIUM

```
CZOLO zlosliwych BEZ przeslonięć:
   M7            typow=13  zwracanych=13
   Parse         typow=6   zwracanych=6
   FromJson      typow=5   zwracanych=5
   Apply         typow=5   zwracanych=4
   Step          typow=5   zwracanych=3
```

`M7` deklaruje **trzynaście** typów i **każdy zwraca własny typ**. Przeczytałem, czym
to jest, zamiast wnioskować z liczby:

```
src/Sim/Signalling/CabProtection.cs:122  public static CabProtection M7(...)
src/Sim/Line/LineCore.cs:427             public static LineCore M7(
src/Sim/Physics/DavisResistance.cs:35    public static DavisResistance M7 { get; }
src/Sim/Physics/VehicleModel.cs:90       public static VehicleModel M7 { get; }
src/Sim/Physics/AccelerationRun.cs:32    public static AccelerationRun M7 { get; }
```

To jest **idiom nazwanego konstruktora**: każdy typ ma swój gotowy wariant dla taboru
M7. Nazwa koliduje i zwraca różne typy **dokładnie dlatego, że idiom jest stosowany
konsekwentnie** — i im lepiej jest stosowany, tym gorzej dla skanu po nazwie.

**To jest ostrzeżenie pola w jego najmocniejszej postaci.** Pole mówi: „nie wolno
przyjąć, że kolizja nazwy jest usterką". Tutaj kolizja nie jest usterką ani zbiegiem —
jest **własnością projektu, którą ktoś wybrał**. Osiemdziesiąt pięć procent pudła
z 6.D299 nie bierze się więc z niechlujstwa w żadnym miejscu; bierze się z tego, że
skan po nazwie jest przyrządem nieprzystającym do kodu, który tak nazywa rzeczy.

## 6. Trzynaście kolizji przechodzi MIĘDZY podkatalogami

```
nazw ZLOSLIWYCH deklarowanych w ROZNYCH podkatalogach src/: 13
   All, Apply, Build, DesignAssumptions, FromJson, Get, Parse,
   Plan, Profile, Samples ...        (Game i Sim; Build: Sim i Sim.Runner)
```

Te są najtrudniejsze do zauważenia przy czytaniu, bo żaden plik nie pokazuje obu stron
naraz. Jest to też jedyna klasa, w której skan po nazwie myli się **poza zasięgiem
wzroku autora** — w `src/Sim/` i `src/Game/` pracuje się osobno.

## 7. Przewidywania spisane PRZED pomiarem — i znowu NIEZALEŻNE

Tej pozycji nie mierzył w tej sesji żaden agent; zapisałem to w definicjach, a nie po
fakcie.

| # | przewidywanie | wynik |
|---|---|---|
| W1 | nazw kolidujących: 40–150 | trafione (102) |
| W2 | złośliwych: 15–60 | trafione (32) |
| W3 | największa liczba typów na nazwę: 5–15 | **ROZSTRZYGNIĘTE ZALEŻNIE OD DEFINICJI** — 13 bez przesłonięć (trafione), 45 z nimi (pudło) |
| W4 | największą nazwą nie będzie `Assumptions` | trafione (`ToString` / `M7`) |
| W5 | kontrola przyrządu przejdzie | trafione |
| W6 | zwyczajowych wśród złośliwych mniej niż połowa | trafione — **zero** |
| W7 | znajdzie się kolizja między podkatalogami | trafione (13) |

**W3 podaję jako zależne od definicji, a nie jako trafione**, i to jest wybór: moje
K2 nie mówiło nic o przesłonięciach, więc nie mam prawa wybrać czytania, przy którym
przedział się zgadza. Przedział postawiłem, myśląc o kolizjach dziedzinowych — i dla
nich jest trafny — ale zapisałem go bez zastrzeżenia, którego pomiar okazał się wymagać.

## 8. Czego świadomie nie zrobiono

- **Nie przemianowano niczego.** Pole nazywa to decyzją projektową, a §5 pokazuje,
  że przy `M7` przemianowanie znaczyłoby porzucenie idiomu, a nie poprawienie usterki.
- **Nie napisano analizatora symboli.** 6.D299 zmierzyło, ile kosztuje jego brak;
  ta pozycja mierzy, na czym ten brak się łamie, i to wystarczy do rozstrzygnięcia,
  którego pole zabrania podejmować.
- **Nie postawiono bramki na wyniku** ani na liczbie kolizji.
- **Nie policzono, ile z 102 kolizji niezłośliwych jest niezłośliwych z KONSTRUKCJI**
  (ten sam typ zwracany wymuszony interfejsem), a ile przypadkiem — pytanie szersze
  niż pole.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 9. Zauważone przy okazji, nietknięte

1. **`ToString` przesłania czterdzieści pięć typów, czyli blisko jedną trzecią
   wszystkich publicznych.** Nie jest to kolizja w żadnym sensie, o który pyta pozycja,
   ale jest to liczba mówiąca, jak bardzo skan po nazwie jest w tym drzewie
   zanieczyszczony przez nazwy z biblioteki standardowej — a `ToString` jest tylko
   najczęstszą z nich.
2. **Kolizji jest 102 na 527 nazw, czyli co piąta.** Przy 156 typach znaczy to, że
   nazwy składników są w tym projekcie **dobierane z małego słownika** — i im
   konsekwentniej, tym więcej kolizji.
3. **`Build` koliduje między `src/Sim/` a `src/Sim.Runner/`**, czyli między rdzeniem
   a jego własnym uruchamiaczem. Jest to jedyna kolizja przechodząca granicę, której
   obie strony pisze ta sama osoba w tym samym celu.
