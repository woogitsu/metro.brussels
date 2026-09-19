# 6.D298 · Cztery drogi pokrywają CAŁĄ klasę nienazwanych — co do jednego typu

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `6fee235`

6.D289 rozstrzygnęło, że census typów zostaje przy rdzeniu, i oparło to na zdaniu,
że powód wpisu bywa dla bramki **niesprawdzalny**. Zdanie było poparte trzema
nazwanymi przypadkami i jedną rodziną opisaną od 6.D234. Liczby dla całego `src/`
nie było. Ta pozycja ją liczy.

---

## 1. Populacja i definicje, ustalone PRZED liczeniem

```
POPULACJA: typow publicznych src/ = 156  (z src 117 | tylko testy 15 | NIENAZWANE 24)
plikow zasobow silnika pod src/: 2 ; plikow .py pod tools/: 219, czytajacych .cs: 32
```

Liczby zgodne z 6.D289 (109 + 42 + 5 = 156) i 6.D290 (24 nienazwane) — ten sam
czytnik, pożyczony przez `przedrostek="src/"`, a nie kopia.

Każda droga ma **dwa czytania**, i oba są podane, bo „droga dotyczy typu" jest
niejednoznaczne dokładnie tak, jak niejednoznaczne było „typ zwracany" przy 6.D290:

* **SZEROKIE** — droga dotyczy typu, niezależnie od tego, czy skan po nazwie go widzi.
* **WĄSKIE** — droga dotyczy typu **z klasy „nienazwane nigdzie"**, czyli tego, dla
  którego skan nie ma wołającego.

Definicje (spisane przed pomiarem, w scratchpadzie, razem z przewidywaniami):

| droga | definicja |
|---|---|
| D1 wiązanie silnika | nazwa typu pada w pliku zasobu Godota pod `src/` (`*.tscn`, `*.tres`, `*.godot`) |
| D2 punkt wejścia | własny plik typu deklaruje punkt wejścia środowiska (`static … Main(`) |
| D3 odczyt przez bramkę Pythona | nazwa typu pada w `tools/**/*.py` — **pięć czytań, §3** |
| D4 konsumpcja przez `var` | typ stoi w pozycji zwracanej publicznego składnika **innego typu** |

## 2. Cztery liczby z listami imiennymi

| droga | szerokie | wąskie |
|---|---|---|
| D1 wiązanie silnika | 11 | 1 |
| D2 punkt wejścia | 1 | 0 |
| D3 igła-fragment źródła (§3) | 7 | 2 |
| D4 w opakowaniu | 88 | 22 |
| D4 wprost | 71 | 15 |

**D1, lista imienna (11):** `CabView`, `DriverActions`, `FirstRun`, `GlbLoader`,
`Hud`, `KeyNames`, `RunSummary`, `StationView`, `TractionBlock`, `TrainView`,
`TunnelView`. Wąskie: sam `FirstRun`.

**D2, lista imienna (1):** `Program`. Wąskie: **żaden** — `Program` wychodzi skanowi
jako „wołany wyłącznie z testów", a nie jako „nienazwany", i 6.D289 §3 mówi to samo.

**D3, lista imienna przy czytaniu najostrzejszym (7):** `DriverBinding`, `FirstRun`,
`LineDrive`, `LineTrain`, `Program`, `RunPlan`, `UiText`. Wąskie: `DriverBinding`
i `FirstRun`.

**D4, wąskie (22)** — to są te same dwadzieścia dwa, które 6.D290 §2 wymieniło jako
„w opakowaniu", a piętnaście z nich to jego lista „wprost", nazwa w nazwę.

## 3. D3 ma PIĘĆ czytań, a odpowiedź waha się dziesięciokrotnie

Tu jest drugie znalezisko tej pozycji, i jest ono o przyrządzie, nie o drzewie.

| czytanie | szerokie | wąskie | co dominuje wynik |
|---|---|---|---|
| a. nazwa pada gdziekolwiek w `.py` | 73 | 15 | **przypięte zbiory censusu** — bramka wymienia typ, bo go LICZY |
| b. nazwa pada w literale napisowym | 65 | 15 | to samo; przypięcia są literałami |
| c. literał wygląda na fragment C# | 48 | 6 | **docstringi** — proza bramek cytuje nazwy z nawiasami |
| d. jak c., ale plik faktycznie czyta `.cs` | 43 | 5 | nadal docstringi, tylko w węższym zbiorze plików |
| e. igła: literał jednolinijkowy do 60 znaków | 18 | 2 | **ścieżki plików** (`"X.cs"`) obok prawdziwych igieł |
| e′. z tego FRAGMENT ŹRÓDŁA, nie ścieżka | **7** | **2** | — |

**Tylko czytania a i b były zdefiniowane przed pomiarem; c, d, e i e′ dopisałem PO
zobaczeniu, co dominuje każdy kolejny wynik.** Zapisuję to wprost, bo dopisywanie
czytań po obejrzeniu liczb jest dokładnie tym ruchem, którym da się wyprodukować
dowolną odpowiedź. Obroną jest tu jedno: **każde kolejne zawężenie ma NAZWANY
zanieczyszczacz**, a nie docelową liczbę. Kolejno były to przypięte zbiory censusu
(bramka wymienia typ, bo go liczy — nie dlatego, że czyta jego kod), docstringi
bramek (proza cytująca nazwy) i ścieżki plików (igła nazywa PLIK, a nie użycie typu).

Rozbicie czytania e: **jedenaście** igieł to ścieżki pliku, **siedem** to fragmenty
źródła. Z siedmiu tylko cztery są cięciem po składni: `"new DriverBinding("`,
`"List<LineTrain> _trains"`, `"IReadOnlyList<LineTrain> Trains"` i
`'UiText\.Get\("(input\.[a-z.]+)"\)'`.

Ta pozycja podaje jako liczbę D3 **czytanie e′ (7 / 2)**, bo ono odpowiada zdaniu,
które 6.D289 §10 zapisało: „czyta go bramka Pythona cięciem po napisie". Pozostałe
cztery stoją w tabeli wyżej i nie znikają.

## 4. Przecięcia — pole „Wyjście" pytało o nie osobno

Przy czytaniu D3 = e′:

```
szerokie: objetych jakakolwiek droga 103 z 156 ; wiecej niz jedna droga:  4
waskie:   objetych jakakolwiek droga  24 z  24 ; wiecej niz jedna droga:  1
```

Cztery przecięcia szerokie: `FirstRun` (D1+D3), `LineDrive` (D3+D4),
`LineTrain` (D3+D4), `Program` (D2+D3). Jedno wąskie: `FirstRun` (D1+D3).

Przy czytaniu D3 = a przecięć szerokich jest **48**, a wąskich **14** — czyli
liczba przecięć zależy od czytania D3 mocniej niż od czegokolwiek innego.

## 5. ZNALEZISKO: cztery drogi pokrywają całą klasę nienazwanych

```
niewolanych: 24
D1: ['FirstRun'] | D2: [] | D3: ['DriverBinding', 'FirstRun'] | D4: 22
UNIA: 24 | reszta bez drogi: []
suma z powtorzeniami: 25
```

**Ani jeden z dwudziestu czterech typów nienazwanych nie zostaje bez drogi.**
Dwadzieścia dwa tłumaczy `var`, jeden — wiązanie silnika, jeden — igła bramki
Pythona; `FirstRun` wchodzi dwiema drogami naraz, stąd suma z powtórzeniami
o jeden większa niż unia.

Spisałem przed pomiarem przewidywanie odwrotne — „suma czterech dróg wąskich
**mniejsza** niż dwadzieścia cztery" — bo zakładałem resztę, której nikt nie
wyjaśnił. **Reszty nie ma.** To jest najmocniejsza liczba tej pozycji i jedyna,
która mogła wyjść inaczej: gdyby choć jeden typ został poza unią, zdanie 6.D289
o niesprawdzalności miałoby przykład, którego dziś nie ma.

## 6. Usterka mojego przyrządu, złapana warunkiem spisanym PRZED pomiarem

Pierwszy przebieg dał dla D4 wąskiego **zero** zamiast dwudziestu dwóch. Warunek
obalenia, spisany przed pomiarem, brzmiał: „jeśli przyrząd da dla D4 wąskiego liczbę
inną niż dwadzieścia dwa, to przyrząd liczy inaczej niż 6.D290 i to jest usterka
MOJA — mam ją nazwać, a nie dopasować definicję po fakcie".

Usterka: moja definicja mówiła „składnik zadeklarowany w **innym typie**",
a implementacja odsiewała po **innym PLIKU**. `BrakingPoint` jest zadeklarowany
w `src/Sim/Physics/BrakingPointSolver.cs` — tym samym pliku, co zwracający go
`Solve()` klasy `BrakingPointSolver`. Typ deklarujący jest inny, plik ten sam,
więc odsiew po pliku wyrzucał całą rodzinę.

Po poprawieniu odsiewu na **typ otaczający** (najbliższa deklaracja typu przed
składnikiem) trzy warianty dają:

| odsiew | wprost szer./wąsk. | w opakowaniu szer./wąsk. |
|---|---|---|
| po pliku (usterka) | 46 / 0 | 52 / 0 |
| po typie (poprawny) | 71 / 15 | 88 / 22 |
| bez odsiewu | 82 / 15 | 99 / 22 |

Wariant „po typie" odtwarza 6.D290 co do cyfry **i co do nazwy**: piętnaście wprost
to dokładnie lista z §2 tamtego raportu.

## 7. Rozstrzygnięcie 6.D289 przeczytane na nowo — ZOSTAJE, i to jest wynik

Pole „Skończone, gdy" żąda przeczytania rozstrzygnięcia o zasięgu wobec tych liczb,
**także gdy brzmi „zostaje przy rdzeniu"**. Brzmi.

Liczby go nie podważają, a jedna go wzmacnia: skoro cztery drogi tłumaczą **całą**
klasę nienazwanych, to rozszerzenie censusu na `src/Game/` i `src/Sim.Runner/`
dołożyłoby jedenaście wpisów klasy „nienazwane" (10 + 1 wg 6.D289 §1), z których
**każdy ma powód spoza zasięgu skanu po nazwie**. Bramka nie umiałaby ich odróżnić
od długu, bo żaden z tych powodów nie jest dla niej sprawdzalny — a dwa z nich
(`FirstRun`, `Program`) już dziś mają osobne asercje, postawione przy 6.D289 właśnie
dlatego, że skan ich nie widzi.

Czego liczby **nie** mówią: że rozszerzenie jest niemożliwe. Mówią, ile kosztuje —
jedenaście wpisów wymagałoby jedenastu rozstrzygnięć, a nie jednego.

## 8. Kontrola przyrządu — zdana

Pole „Weryfikacja" żąda, by droga „wiązanie silnika" odtworzyła `FirstRun` jako
jedyny niewidoczny skrypt sceny. Odtworzyła: D1 wąskie to dokładnie `['FirstRun']`,
czyli wynik, który przybija dziś `test_slepota_siedzi_w_KORZENIU_sceny_a_nie_w_calym_katalogu`
— przy czym tamta bramka liczy na `src/Game/`, a ja na całym `src/`. Zgodność mimo
różnicy zasięgu znaczy, że poza `src/Game/` nie ma ani jednego typu wiązanego przez
silnik i niewidocznego dla skanu.

```
python3 tools/tests/test_all.py test_csharp_type_callers.py
  10/10 przeszło
```

## 9. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | D1 szerokie 6–15 | trafione (11) |
| 2 | D1 wąskie = 1, `FirstRun` | trafione |
| 3 | D2 szerokie 1–2 | trafione (1) |
| 4 | D2 wąskie = 0 | trafione |
| 5 | D3 szerokie 2–12 | **pudło** przy czytaniu zdefiniowanym (73); trafione dopiero przy e′ (7) |
| 6 | D3 wąskie 0–2 | **pudło** przy czytaniu zdefiniowanym (15); trafione przy e′ (2) |
| 7 | D4 szerokie 40–90 | trafione (88) |
| 8 | D4 wąskie = 22 | trafione — ale dopiero po naprawie przyrządu, §6 |
| 9 | przecięć szerokich 0–4 | trafione przy e′ (4), pudło przy a (48) |
| 10 | przecięć wąskich 0 | **OBALONE** — jedno, `FirstRun` |
| 11 | unia dróg wąskich mniejsza niż 24 | **OBALONE** — równa 24, §5 |

Osiem trafionych, dwa obalone, a dwa pudła (5 i 6) mówią o czytaniu, nie o drzewie.
**Oba obalone przewidywania dotyczyły tej samej rzeczy — reszty, której nie ma.**
Zakładałem, że część nienazwanych zostanie bez drogi i że drogi się nie przecinają;
myliłem się w obie strony naraz, i to jest spójne: przecięcie i pełne pokrycie to
ten sam fakt widziany z dwóch stron.

## 10. Czego świadomie nie zrobiono

- **Nie usunięto ani nie podłączono żadnego typu** — pole „Dlaczego bez decyzji"
  mówi wprost, że pozycja LICZY.
- **Nie rozszerzono censusu** na `src/Game/` ani `src/Sim.Runner/` — pole „Poza
  zakresem" nazywa to rozstrzygnięciem, które te liczby mają przygotować, a nie
  przesądzić. §7 podaje jego koszt i nic więcej.
- **Nie postawiono bramki** na żadnej z czterech liczb. Cztery drogi mają dziś dwie
  asercje (obie z 6.D289) i to jest stan, którego ta pozycja nie zmienia.
- **Nie zmieniono rozbioru deklaracji** — `TYP` i `SKLADNIK` pożyczone, nie tknięte.
- **Nie tknięto `data/` ani `src/`.**

## 11. Zauważone przy okazji, nietknięte

Z 219 plików `.py` pod `tools/` **32 czytają źródła C#**, a nazwa typu pada
w 73 z nich. Różnica między tymi liczbami to prawie wyłącznie **proza** — docstringi
i komentarze bramek cytujące nazwy typów. Ta sama proza jest materiałem, na którym
pracują bramki pokrycia z 6.D284 i 6.D296. Czy nazwa typu C# w docstringu bramki
starzeje się tak samo cicho, jak starzeje się liczba (6.D288), ta pozycja nie pyta:
żadna bramka nie sprawdza dziś, czy cytowany w prozie typ nadal istnieje w drzewie.
