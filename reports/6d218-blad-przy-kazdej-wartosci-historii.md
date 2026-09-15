# 6.D218 — sześć wartości, sześć błędów, i za każdym razem dokładnie jeden

**15.09.2026**, na `dd52ba4`. Wejście: `tools/tests/test_prose_counts.py`
(`WZORZEC_ZAPADEK`, `WZORZEC_MODULOW`, `WZORZEC_POMOCNIKOW`, `WZORZEC_DEKLARACJI_POMIARU`,
`DEKLARACJE_SLOWNE`), `tools/tests/test_tree_walks.py` (zdanie o rejestrze zapadek),
`tools/tests/test_runner_number_parsing.py` (zdanie o pomocnikach),
`reports/6d206-jeden-kontener-na-dwadziescia-dziewiec.md`.

## 1. Ilu wzorców to dotyczy: DWÓCH z czterech

| wzorzec | niesie liczbę | wymusza formę | dziś |
|---|---|---:|---|
| `WZORZEC_ZAPADEK` | 5 liczb | **cztery formy** | **BŁĄD** |
| `WZORZEC_POMOCNIKOW` | liczebnik słowny | jedną (`pomocniki`) | poprawne, ale tylko przy 2–4 |
| `WZORZEC_MODULOW` | 1 liczbę | **żadnej** | poprawne przy każdej liczbie |
| `WZORZEC_DEKLARACJI_POMIARU` | nie niesie | — | — |

**`WZORZEC_MODULOW` jest odporny nie przez ostrożność, tylko przez budowę zdania:**
czyta „robi to samo dla N modulow", a przypadek narzuca tam **przyimek „dla"**, nie
liczebnik. Wzór na poprawkę leżał więc w tym samym pliku od początku.

## 2. Zdanie o rejestrze było błędne przy KAŻDEJ wartości swojej historii

Reguła polska: 1 → liczba pojedyncza; końcówka 2, 3, 4 poza 12–14 → liczba mnoga
mianownik; reszta → liczba mnoga dopełniacz. Stary kształt żądał `zapadek` (dop.),
`przybitych` (dop.), `częściowe` (mian.) i `WOLNE` (mian.) **bez względu na liczebnik**:

| rejestr | forma wymuszona błędnie |
|---|---|
| 46 / 17 / 3 / **25** | „25 WOLNE" — ma być WOLNYCH |
| 48 / 17 / 3 / **27** | „27 WOLNE" |
| 49 / 17 / 3 / **28** | „28 WOLNE" |
| 50 / 17 / 3 / **29** | „29 WOLNE" |
| 51 / 17 / 3 / **30** | „30 WOLNE" |
| **54** / 17 / 3 / 33 | „54 zapadek" — ma być zapadki |

**Sześć wartości, sześć błędów, za każdym razem dokładnie jeden.** Przy 33 forma
`WOLNE` zrobiła się poprawna, a błąd **przeskoczył o słowo**: nieprawdziwe zrobiło się
„54 zapadek". Błąd nie zniknął ani razu — zmienił miejsce.

**I ani razu nic się nie zapaliło**, bo bramką był ten sam wzorzec, który błąd wymuszał.
Obejście („napisz niepoprawnie") jest tu darmowe, więc usterka utrwalała się po cichu
przy każdym podniesieniu rejestru — ostatni raz **w commicie bezpośrednio przed tą
pozycją** (6.D216, 51 → 54).

## 3. Rozstrzygnięcie: zdania zmieniają KSZTAŁT, wzorce NIE są poszerzane

Pole „Czego NIE wolno zrobić bez pomiaru" zabraniało poszerzyć wzorzec na obie formy
i uznać rzecz za załatwioną — i to jest słuszne z powodu, który widać na liczbach:
wzorzec przyjmujący obie formy przestaje odróżniać zdanie poprawne od niepoprawnego,
czyli przestaje pilnować czegokolwiek.

Kształt, w którym **liczba stoi PO etykiecie**, nie wymusza niczego, bo przypadek
rządzony jest dwukropkiem:

```
Zapadek: 54. **Przybitych: 17, częściowych: 3, WOLNYCH: 33, poza zasięgiem skanu: 1.**
Pomocnikow, ktore maja byc JEDYNA droga wartosci opcji do liczby: trzy.
```

**Przechwyceń jest nadal pięć i jedno** — wzorce nie są ani o jotę luźniejsze. Nowa
próbka w kontroli przyrządu wykonuje to wprost: cztery liczebniki (`1`, `2`, `5`, `22`),
wymagające po polsku czterech różnych form, czyta ten sam wzorzec bez zmiany słowa.

## 4. Bramka: zbiór wzorców wymuszających formę ma być PUSTY

`formy_wymuszane_po_liczebniku()` czyta **źródło wzorca** (`.pattern`), a nie prozę —
bo wymuszenie jest własnością wzorca, nie zdania: zdanie da się napisać poprawnie tylko
wtedy, gdy wzorzec na to pozwala.

Dwie granice, obie **wykonane**, nie opisane:

- **Przyimek PRZED liczbą zwalnia** — wtedy to on rządzi przypadkiem. Bez tej reguły
  skan zapala się na `WZORZEC_MODULOW`, czyli na wzorcu poprawnym (6.D27).
- **Przyimek PO liczbie też zwalnia** — liczba nie rządzi przyimkiem. Bez tej reguły
  skan zgłaszał „1 poza zasięgiem skanu" jako wymuszenie formy `poza`. Złapane przed
  werdyktem, kontrolą negatywną KN-4.

Zbiór jest pusty, więc stoi przy nim **kontrola przyrządu** (6.D159): oba kształty
sprzed tej pozycji podane skanowi wprost, z żądaniem, żeby je zobaczył.

## 5. Pomyłka własnej bramki, złapana przed werdyktem

Pierwsza wersja czytnika wypisywała klasę liter z ręki, kopiując ją z tego samego pliku
— a **klasy w `test_prose_counts.py` mają uszkodzone kodowanie**: stoi w nich `Ęꣳ`
zamiast `ĘęŁł`. Skan zatrzymywał się przez to w środku słowa i czytał „częściowe" jako
„cz". Klasa uniwersalna `[^\W\d_]` nie ma tego problemu i nie wymaga pilnowania.

**Kodowania tych klas nie naprawiam** — działają dla swoich wejść, a naprawa jest poza
polem tej pozycji.

## 6. Kontrole negatywne

Baza: **11/11** w module, **2490/2490** w zestawie. `md5sum -c` `OK` po każdej.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | `WZORZEC_ZAPADEK` i zdanie cofnięte do starego kształtu | **2 czerwone**, z wykazem czterech form |
| KN-2 | `WZORZEC_POMOCNIKOW` cofnięty | **2 czerwone** |
| KN-3 | czytnik `_LICZBA_RZADZI` oślepiony | **1 czerwony** — kontrola przyrządu |
| KN-4 | reguła „przyimek PO liczbie" zdjęta | **1 czerwony** — `poza` wchodzi jako wymuszenie |
| KN-5 | przyimek `dla` zdjęty z listy rządzących | **1 czerwony** — `WZORZEC_MODULOW` zgłoszony fałszywie |

**KN-3 jest tą, która nadaje sens pustemu zbiorowi.** Pusty zbiór odpowiada „nic nie
wymusza" tak samo przekonująco jak skan, który oślepł — dopiero podanie mu obu kształtów
sprzed tej pozycji odróżnia jedno od drugiego.

**KN-4 i KN-5 mierzą cenę obu granic w tę samą stronę:** każda z nich, zdjęta, zamienia
bramkę w taką, która świeci na tekście poprawnym.

Pełne przebiegi:

```
$ python3 tools/tests/test_all.py test_prose_counts.py
  11/11 przeszło

$ python3 tools/tests/test_all.py
  2490/2490 przeszło
  RAZEM 251.558 s, 2490 testów, 126 modułów
```

## 7. Czego świadomie nie zrobiłem

- **Nie poszerzyłem żadnego wzorca o obie formy** — pole tego zabraniało, a pomiar
  pokazuje, dlaczego: wzorzec przyjmujący obie nie odróżnia poprawnego od błędnego.
- **Nie zmieniłem wartości żadnej zapadki ani rejestru** — liczby 54/17/3/33/1 stoją
  nietknięte, zmienił się wyłącznie kształt zdania.
- **Nie przepisywałem prozy poza dwoma zdaniami, których wzorce dotyczą.**
- **Nie naprawiałem uszkodzonego kodowania klas liter** w tym pliku (§5).

## 8. Zauważone, nie tknięte

- **Uszkodzone kodowanie klas liter w `test_prose_counts.py`** (`Ęꣳ` zamiast `ĘęŁł`,
  `[A-Za-zĄąĆćĘꣳŃńÓóŚśŹźŻż]`) stoi w **dwóch** miejscach i działa dziś tylko dlatego,
  że jego wejściem są słowa bez `ę` i `ł` („Trzy"). Liczebnik „pięć" albo „łącznie"
  przeciąłby je w środku i nikt by się nie dowiedział.
- **Reguła odmiany, którą wpisałem w bramkę, obejmuje liczebniki główne i nic więcej.**
  Rzędy „tysiąc", „milion" mają własną odmianę; w tym drzewie żadna zapadka do nich nie
  dochodzi, ale skan tego nie sprawdza.
