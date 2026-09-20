# 6.D330 · Sześć przyrostków spoza zapisu na dwadzieścia jeden nazw — a `Hz` z kontroli przyrządu NIE ISTNIEJE, bo `JitterFrequency` nazywa wielkość, nie jednostkę

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `565424e`

6.D320 §9.2 zapisało, że `docs/04-conventions.md` nie wymienia `J`, `N`, `W` ani `Hz`,
a wszystkie cztery padają w nazwach `src/` jako przyrostki — i że konwencja jest więc
szersza niż jej zapis. Ta pozycja **liczy i wypisuje imiennie**. Dopisanie czegokolwiek
do `docs/04-conventions.md` jest decyzją właściciela i nie należy do tej pozycji.

---

## 1. K0 — zapis konwencji PRZECZYTANY, nie przepisany z cudzego raportu

```
wierszy tabeli w docs/04-conventions.md: 0
```

```
- 1 jednostka Blendera/Godota = 1 metr.
- Prędkość w kodzie: m/s; masa: kg; czas: s; pochylenie: %.
```

**Pięć jednostek w dwóch wierszach listy, zero tabel** — potwierdzam pomiar 6.D320 §1
własnym odczytem, zamiast go przytoczyć.

## 2. Populacja i przyrostek

Populacja 6.D320: `double`/`float`/`decimal` poza metodami w `src/`, nazwy przypisane
literałowi `float` w `tools/`, rozbicie nazw z poprawką na `_camelCase`.

```
nazw src/=193  tools/=214 ; wieloczlonowych src/=175 tools/=174
roznych ostatnich czlonow: 60
```

**Liczby 193 i 214 są większe niż 188 i 209 z 6.D320 i nie uzgadniam tej różnicy —
podaję jej przyczynę.** Tamta pozycja odsiewała nazwy o rdzeniu bezwymiarowym
(`count`, `ratio`, `index`, …) jeszcze przed klasyfikacją; tutaj żadnej nazwy nie
odsiewam, bo pytanie dotyczy przyrostków, a nie wymiarowości.

Przyrostek to **ostatni człon**. Nazwa jednoczłonowa przyrostka nie ma — inaczej `a`,
`s`, `t`, `v` weszłyby jako amper, sekunda, tona i wolt, a 6.D329 §4 przeczytało je
jako symbole **wielkości**.

## 3. GŁÓWNE ZNALEZISKO: kontrola przyrządu NIE PRZECHODZI, i to nie z winy przyrządu

Pole żądało, żeby `J`, `N`, `W` i `Hz` wypadły w klasie „spoza zapisu", a `M` i `Kg`
w klasie „zna". **Pięć z sześciu wychodzi. Szóstego nie da się sprawdzić, bo
przyrostka `Hz` w tym drzewie NIE MA:**

```
czy wśród 60 różnych ostatnich członów jest `hz`:  NIE
```

Nazwą, którą 6.D320 §9.2 podało jako przykład dla `Hz`, jest `JitterFrequency` —
a jej ostatni człon to `frequency`. **To jest nazwa WIELKOŚCI, nie symbol
jednostki**, dokładnie tak jak `Speed` nie jest `Mps`. Jedyne dwa miejsca, w których
`Hz` w ogóle pada w `src/`, to **proza**, nie nazwy:

```
src/Sim/Signalling/TrainProtection.cs:301:  /// przy 120 Hz ostrzeżenie emitowane co krok …
src/Sim/Physics/FixedStep.cs:26:          /// <summary>Częstotliwość w Hz, jeśli krok powstał z FromHertz; …
```

Przewidywanie X1 („kontrola przejdzie dla wszystkich sześciu") jest więc **obalone**,
i obalone przez wadę **cudzego zdania przeniesionego do pola**, a nie przez mój
czytnik. Jest to trzecia pozycja z rzędu, w której kontrola przyrządu opisuje
populację innym kształtem, niż ta populacja ma (6.D317 §1, 6.D328 §1, teraz ta) —
z tą różnicą, że tutaj przyczyna jest **imiennie wskazywalna**: jedna nazwa wzięta
za przyrostek.

**Nie poprawiam 6.D320.** Jego zdanie „konwencja jest szersza niż jej zapis" zostaje
prawdziwe — tylko stoi na trzech przyrostkach, nie czterech, i §4 pokazuje, że
naprawdę stoi na sześciu.

## 4. Trzy klasy przyrostków, z liczbami

```
klasa          przyrostkow     nazw     src/   tools/
ZNA                      7      238      109      129
POCHODNA                 6       30       20       10
SPOZA ZAPISU             6       21       16        5
ODRZUCONE PO CZYTANIU    3        3        3        0
```

**ZNA (7 zapisów pięciu jednostek):** `m` (189), `seconds` (20), `mps` (9), `s` (7),
`kg` (7), `second` (4), `percent` (2). Ta sama jednostka ma **trzy** zapisy dla
sekundy (`S`, `Seconds`, `Second`) — i to jest w zapisie konwencji nieuregulowane
tak samo jak jednostki spoza piątki.

**POCHODNA od wymienionej (6):** `mps2` (11), `kmh` (8), `mm` (5), `mps3` (3),
`us` (2), `m2` (1).

**SPOZA ZAPISU (6 przyrostków, 21 nazw)** — z przykładem i wielkością PRZECZYTANĄ
z kodu, nie odgadniętą z symbolu:

| przyrostek | jednostka | nazw | przykład | co to jest, z kodu |
|---|---|---|---|---|
| `J` | dżul | 9 | `ResidualJ` | „Domknięcie bilansu" energii hamowania — `BrakingEnergyAccount.cs:44` |
| `Deg` | stopień kątowy | 5 | `CabFovDeg` | pole widzenia kamery kabiny |
| `N` | niuton | 2 | `DesignStartupForceN` | `Design("reference_model.startup_force_n")` |
| `W` | wat | 2 | `InstalledPowerW` | `…traction_installed_power_kw * 1000.0` — przeliczone na waty W KODZIE |
| `Kwh` | kilowatogodzina | 2 | `TractionWorkKwh` | praca trakcji |
| `Px` | piksel | 1 | `PIXEL_BUDGET_TOLERANCE_PX` | tolerancja w pikselach |

**Nazw z przyrostkiem spoza zapisu jest w całym drzewie 21** — szesnaście w `src/`
i pięć w `tools/`. Przewidywanie X5 („mniej niż 60") trafione, X2 („więcej niż
cztery przyrostki") trafione: jest sześć, a nie cztery — i to mimo że jeden
z czterech wymienionych przez 6.D320 nie istnieje (§3).

## 5. TRZY kandydatury odrzucone PO PRZECZYTANIU — pole ostrzegało słusznie

Pole ostrzega, że `A`, `V` czy `N` bywają pojedynczą literą nazwy własnej, nie
amperem, woltem ani niutonem. **Ostrzeżenie się sprawdziło, i to w miejscu, którego
sam bym nie wskazał:**

```
DesignDavisA, DesignDavisB, DesignDavisC
/// <summary>Wyraz stały wzoru Davisa, kgf/t.</summary>
```

`A`, `B`, `C` to **nazwy wyrazów wzoru Davisa**, a nie ampery, bele ani kulomby.
Przewidywanie X4 trafione — trzy nazwy odrzucone, wszystkie z jednej rodziny.

**A przy okazji wychodzi siódma jednostka spoza zapisu, której przyrostek nie
złapie w ogóle: `kgf/t`.** Stoi w prozie przy `DesignDavisA` i nie ma jak stanąć
w nazwie, bo ukośnika nazwa nie zniesie. Zapisuję, bo pole żądało wielkości
przeczytanej z kodu — a tu kod mówi coś, czego nazwa powiedzieć nie umie.

**`N` i `W` natomiast czytanie POTWIERDZIŁO:** `DesignStartupForceN` bierze wartość
z klucza `reference_model.startup_force_n`, a `InstalledPowerW` mnoży kilowaty przez
1000,0. Odrzucenie kandydata po przeczytaniu nie jest więc regułą — jest wynikiem
czytania, który raz na cztery wypada odmownie.

## 6. Przewidywania — cztery trafione, dwa obalone

| # | przewidywanie | wynik |
|---|---|---|
| X1 | kontrola przejdzie dla wszystkich sześciu | **OBALONE**: `Hz` nie istnieje (§3) |
| X2 | przyrostków spoza zapisu więcej niż cztery | **trafione**: sześć |
| X3 | najliczniejszy przyrostek to `M` | **trafione**: 189 nazw, czyli więcej niż wszystkie pozostałe razem |
| X4 | co najmniej jeden kandydat okaże się literą nazwy własnej | **trafione**: trzy (§5) |
| X5 | nazw z przyrostkiem spoza zapisu mniej niż 60 | **trafione**: 21 |
| X6 | klasa POCHODNA liczniejsza w `tools/` niż w `src/` | **OBALONE**: 10 wobec 20 |

### 6.1 Dlaczego X6 padło

Rozumowanie było takie, że skrypty liczą w milimetrach i mikrosekundach (6.D329 §3),
więc pochodnych będzie tam więcej. Milimetry i mikrosekundy **rzeczywiście są
wyłącznie w `tools/`** — ale to siedem nazw, a po stronie `src/` stoi czternaście
nazw z `Mps2` i `Mps3`, których w `tools/` nie ma ani jednej:

```
  mm    src=0  tools=5        mps2  src=11 tools=0
  us    src=0  tools=2        mps3  src=3  tools=0
  m2    src=0  tools=1        kmh   src=6  tools=2
```

Podział jest więc ostrzejszy, niż przewidywałem, tylko w drugą stronę: **każda
pochodna należy prawie wyłącznie do jednego korpusu**, a te z `src/` są liczniejsze.

## 7. Czego świadomie nie zrobiłem

Nie tknąłem `docs/04-conventions.md`, nie przemianowałem żadnej nazwy, nie postawiłem
bramki na przyrostkach, nie tknąłem `src/` ani `data/` — wszystko to stoi w polu
„Poza zakresem". Lista z §4 i §5 jest dokładnie tym, czego dopisanie **by dotyczyło**,
gdyby właściciel zdecydował o dopisaniu; decyzji nie podejmuję i nie sugeruję.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

Sekunda ma w nazwach **trzy** zapisy (`S`, `Seconds`, `Second`), metr jeden (`M`),
a `SecondsInPhase` i `SecondsSinceStopped` niosą jednostkę na **pierwszym** członie,
nie na ostatnim — mój przyrostek ich nie widzi i liczy je jako `phase` i `stopped`.
Ile nazw niesie jednostkę na członie innym niż ostatni, ta pozycja nie mierzy: pole
definiuje przyrostek i tylko o niego pyta.
