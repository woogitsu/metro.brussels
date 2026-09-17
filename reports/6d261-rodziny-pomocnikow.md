# 6.D261 — dwadzieścia cztery powtórzone nazwy to DWIE różne rzeczy: 10 i 14

**Data:** 17.09.2026 · **Gałąź:** `claude/6d261-rodziny-pomocnikow` · **Baza:** `101f211`

## 1. Obie liczby, których żądało pole „Wyjście"

Skan podpisów `private static` pod `tests/`: **67 plików, 237 podpisów**, z czego
**24 nazwy** padają w więcej niż jednym pliku. Podział, o który pytała pozycja:

```
rodzin IDENTYCZNYCH   (ta sama nazwa nad TYM SAMYM ciałem):  10
rodzin JEDNOIMIENNYCH (ta sama nazwa nad INNYM ciałem):      14
```

**Podpisów jest 237, a opis pozycji mówił 236** — liczba urosła o jeden przez dobę,
między 6.D257 a dziś. To ten sam kształt, który 6.D259 złapało na własnym opisie.

### Dziesięć rodzin identycznych

| rodzina | kopii | projekty | długość ciała | delegacja do `KorzenRepozytorium`? |
|---|---|---|---|---|
| `RepositoryRoot` | 9 | Game+Sim | 91 | **tak** |
| `RepoRoot` | 3 | Sim | 85 | **tak** |
| `FindRepositoryRoot` | 3 | Sim | 104 | **tak** |
| `Notch` | 2 | Game+Sim | 48 | nie |
| `Parse` | 2 | Game | 119 | nie |
| `StraightAxis` | 2 | Game | 163 | nie |
| `Protection` | 2 | Sim | 83 | nie |
| `Service` | 2 | Sim | 156 | nie |
| `Stopped` | 2 | Sim | 103 | nie |
| `Moving` | 2 | Sim | 124 | nie |

### Czternaście rodzin jednoimiennych

`Settings` ×7 w czterech postaciach, `Level` ×7 w trzech, `Plan` ×6 w czterech,
`Axis` ×5 w trzech, `Zrodlo` ×3, `Scene` ×3, `Drive` ×3, `Line` ×3, oraz sześć
rodzin po dwie kopie. **Scalenie któregokolwiek z nich byłoby błędem, a nie
sprzątaniem** — i to jest cała treść podziału.

## 2. Znalezisko: 6.D257 zdjęło PĘTLE, a nie OPAKOWANIA

Trzy największe rodziny identycznych — razem **15 kopii** — są dziś jednowierszowymi
**delegacjami**:

```csharp
private static string RepositoryRoot() =>
    MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka;
```

6.D257 zastąpiło dziewiętnaście własnych pętli jednym pomocnikiem i to zostaje
prawdą — ale metody opakowujące przetrwały w piętnastu plikach. Są identyczne
**dlatego**, że wszystkie prowadzą do tego samego miejsca. Zdjęcie ich jest czystym
przemianowaniem o zerowym zachowaniu, i jest osobną pozycją: pole „Poza zakresem"
tej pozycji zabrania scalania rodzin wprost.

## 3. Rozstrzygnięcie: ŻADNA z siedmiu nie zasługuje na wspólny plik

Pole „Wyjście" pytało, czy którakolwiek z rodzin identycznych zasługuje na wspólny
plik w `tests/Shared/`. **Odpowiedź brzmi: żadna z siedmiu** (po odjęciu trzech
rodzin delegacji, które wspólny plik już mają). Jest to liczba, nie ocena:

* wszystkie siedem ma po **dwie** kopie — nie dziewięć, jak rodzina, którą 6.D257
  uznało za wartą pliku;
* wszystkie siedem to **jednowierszowce**: 48–163 znaki treści po normalizacji;
* **sześć z siedmiu** stoi w obrębie JEDNEGO projektu, więc nie przekracza granicy,
  dla której `tests/Shared/` w ogóle powstało;
* jedyna rodzina międzyprojektowa (`Notch`) jest **najkrótsza z całej dziesiątki**
  (48 znaków: `private static DriverNotch Notch() => new(Rate);`).

Wspólny plik kosztuje wpis `Compile Include` w każdym `.csproj`, który go bierze.
Dla jednowierszowca użytego dwa razy w tym samym projekcie jest to koszt większy
niż oszczędność.

## 4. Bramka: DWIE równości, a nie próg na sumie

`RODZIN_IDENTYCZNYCH = 10` i `RODZIN_JEDNOIMIENNYCH = 14`, obie równościami, plus
podłoga `MIN_PODPISOW_POMOCNIKA = 200` na populację.

**Że to mają być dwie liczby, a nie suma, pokazała pierwsza kontrola negatywna**
— patrz §5. Podłoga stoi obok, bo czytnik oślepiony do zera przechodzi obie
równości zejściem do `(0, 0)`.

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Mutacje na KOPII drzewa (§4.6), `__pycache__` czyszczony (6.D102), każda z asercją,
że **wylądowała**.

### KN-1 — dwudziesta piąta KOPIA (nazwa już istniejąca, inne ciało)

Przewidywanie: bramka czerwona.

```
MUTACJA WYLĄDOWAŁA: 1
FAIL test_ile_rodzin_pomocnikow_jest_DUPLIKATEM_a_ile_ZBIEGIEM_NAZW:
  rodzin identycznych 9 i jednoimiennych 15, a pomiar 17.09.2026 dal 10 i 14
```

**I to jest wynik mocniejszy, niż przewidywałem.** `Protection` przeszło z kupki
identycznych do jednoimiennych, więc **suma została ta sama — 24**. Próg albo równość
na SUMIE nie zapaliłyby się wcale. Bramka widzi to wyłącznie dlatego, że trzyma
podział, a nie sumę; napisałem ją tak z innego powodu i kontrola pokazała, że powód
był lepszy, niż wiedziałem.

### KN-2 — dwudziesta piąta NAZWA, dosłownie jak w zadaniu

Przewidywanie: `RODZIN_IDENTYCZNYCH` 10 → 11, czerwień.

```
MUTACJA WYLĄDOWAŁA w dwoch plikach: HudLayoutTests.cs:1 BrakingTests.cs:1
FAIL test_ile_rodzin_pomocnikow_jest_DUPLIKATEM_a_ile_ZBIEGIEM_NAZW:
  rodzin identycznych 11 i jednoimiennych 14, a pomiar 17.09.2026 dal 10 i 14
```

Zgodnie z przewidywaniem.

### Kontrola przyrządu — pięć kształtów na drzewie próbnym

Zadanie żądało jej wprost: dwie metody o tej samej nazwie i RÓŻNYCH ciałach mają
trafić do kupki „ta sama nazwa, inna treść", a nie do duplikatów. Sprawdzane naraz:
rozróżnienie ciał, **obojętność na wcięcie** (treść, nie zapis), **przeciążenie
w jednym pliku** (nie jest rodziną między plikami) oraz **metoda wyrażeniowa
`=> ...;`**, która klamry nie ma — a jest postacią większości powtórzonych pomocników
w tym drzewie.

**Padła przy pierwszym przebiegu i złapała usterkę czytnika**: pliki były kluczowane
po `basename`, więc dwa pliki o tej samej nazwie w różnych projektach były dla niego
JEDNYM plikiem, a rodzina wymaga dwóch. W dzisiejszym drzewie powtórzonych nazw
plików **nie ma ani jednej** (`ls tests/*/*.cs | xargs -n1 basename | sort | uniq -d`
daje pustkę), więc żadna liczba w tym module by się nie ruszyła i usterka przeszłaby
cały zestaw na zielono. Złapał ją wyłącznie fixture, który takie dwa pliki tworzy.
Po poprawce (klucz `projekt/plik`) liczby są **te same**: 10 i 14.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_csharp_test_methods.py
  20/20 przeszło

python3 tools/tests/test_all.py
  2582/2582 przeszło
  RAZEM 249.783 s, 2582 testów, 131 modułów

~/.dotnet/dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 673, Skipped: 0, Total: 673

~/.dotnet/dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 319, Skipped: 0, Total: 319
```

## 7. Zauważone, nietknięte

- **Nie scalono żadnej rodziny.** Pole „Poza zakresem" mówi, że scalanie to osobna
  pozycja na rodzinę i osobny koszt.
- **Piętnaście delegacji po 6.D257 zostaje.** Zdjęcie ich to przemianowanie o zerowym
  zachowaniu, ale dotyka piętnastu plików i jest właśnie taką osobną pozycją.
- **Skan nie obejmuje `src/`** — poza testami duplikat pomocnika jest inną usterką
  i pole „Poza zakresem" zabrania tego wprost. Nie obejmuje też nazw publicznych.
- Oczekiwane w polu „Weryfikacja" **318/318** jest dziś **319/319**: 6.D260 dołożyło
  kontrolę przyrządu do `UiTextTests.cs` tą samą dobą. Liczba z pola zestarzała się
  między napisaniem pozycji a jej wykonaniem — trzeci taki przypadek w tej serii.
