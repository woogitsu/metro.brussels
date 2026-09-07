# Raport nazywał plik z `Sim.Tests` testem Godota — i dlaczego bramki na to nie ma (6.D35)

**Zmierzone 07.09.2026 na commicie:** `021ddc55fdd7ec6d75b946c6edd1566dfc2cdb2d`
**Dotyczy:** `reports/audyt-asercji.md` §7
**Rodzina:** 6.D4 (bramka na twierdzenia raportów), 6.D3, 6.D8

## 1. Zdanie i dlaczego jest nieprawdziwe

`reports/audyt-asercji.md` §7, scalony do `main` w #375, mówił:

> Trzy najliczniejsze pliki C# to testy Godota, nie runnera (`RunPlanTests.cs` 20,
> `TelemetryTrackTests.cs` 19, `InputLogTests.cs` 14 gołych asercji na obecność).

Sprawdzone:

```
$ ls tests/*/InputLogTests.cs
tests/Sim.Tests/InputLogTests.cs
$ grep -n "namespace" tests/Sim.Tests/InputLogTests.cs
7:namespace MetroBxl.Sim.Tests;
$ grep -c Godot tests/Sim.Tests/*.csproj    → 0
$ grep -c Godot tests/Game.Tests/*.csproj   → 1
```

Trzeci plik nie jest testem Godota ani przez katalog, ani przez przestrzeń nazw, ani
przez odwołanie w pliku projektu.

**Sprzeczność była wewnątrz jednego dokumentu.** Rozbicie w §2 **tego samego raportu**
podaje pełne ścieżki i mówi to wprost:

```
== C#: obecnosc=254 gole=127 funkcji=79 plikow=23
     tests/Game.Tests/RunPlanTests.cs               20
     tests/Game.Tests/TelemetryTrackTests.cs        19
     tests/Sim.Tests/InputLogTests.cs               14
```

§7 czytał więc własne §2 i przepisał je z błędem. Zdanie **przepisane**, nie dopisane
obok, a liczby 20 / 19 / 14 **nieprzeliczone** — są pomiarem z datą.

## 2. Czy da się na to postawić bramkę — pomiar mówi NIE

Pozycja pytała, czy `test_report_claims.py` da się rozszerzyć o twierdzenia postaci
„plik X należy do projektu Y". Zasada tamtej bramki na to pozwala: sprawdza wyłącznie
to, co **nie jest datowanym pomiarem**, a przynależność pliku do projektu nią nie jest
— odczytuje się ją z drzewa.

Przyrząd: dla każdego wiersza w `reports/*.md`, który nazywa plik `*Tests.cs`
**i** zawiera marker projektu (`Sim.Tests`, `Game.Tests`, `Godot`), sprawdź, czy
marker zgadza się z faktycznym katalogiem pliku. Zmierzone:

```
plikow *Tests.cs w drzewie: 47   projekty: ['Game.Tests', 'Sim.Tests']
wierszy w reports/ nazywajacych plik *Tests.cs RAZEM z markerem projektu: 84
zgloszen przyrzadu: 5
```

**Wszystkie pięć zgłoszeń to fałszywe alarmy**, każde z tego samego powodu: marker stoi
w **innej komórce tabeli** niż nazwa pliku.

| zgłoszenie | dlaczego fałszywe |
|---|---|
| `T-400-stage-3b.md:464` | wiersz tabeli o `src/Game/World/StationView.cs`, plik testowy w innej kolumnie |
| `droga-do-grywalnosci.md:216` | komórka o `src/Game/FirstRun.cs`, obok komórka z `tests/Sim.Tests/…` |
| `droga-do-grywalnosci.md:229` | komenda `grep … src/Game/project.godot` — słowo „godot" z nazwy pliku silnika |
| `droga-do-grywalnosci.md:230` | `src/Game/RunReset.cs` w jednej komórce, plik testowy w innej |
| `kolejka-uzupelnienie-drugie.md:226` | zdanie **o tej usterce**, cytujące ją |

**A teraz rzecz rozstrzygająca: przyrząd NIE ZGŁASZA wiersza, dla którego powstał.**
`audyt-asercji.md:290` przechodzi jako poprawny, bo ten sam wiersz zawiera także
`RunPlanTests.cs`, który **naprawdę** jest w `Game.Tests` — a mylnie opisany
`InputLogTests.cs` stoi w wierszu **następnym**.

Wynik: **5 fałszywych alarmów na 84 trafienia (6 %) i 0 z 1 prawdziwych.** To ta sama
arytmetyka, którą 6.A32 zamknęło bez bramki, i z tej samej przyczyny strukturalnej:
twierdzenie rozciąga się na dwa wiersze, a marker nie stoi przy pliku, którego dotyczy.

Pozycja kończy się więc **poprawką zdania i bez bramki** — wynik dopuszczony wprost
przez jej pole „Wyjście": „jeżeli nie, raport dostaje adnotację i pozycja kończy się
na niej".

## 3. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1931/1931 przeszło
  RAZEM 72.093 s, 1931 testów, 101 modułów
kod: 0
```

Zestaw **1931 → 1931**: ta pozycja nie dopisuje ani jednego testu, i to jest jej
wynik, nie jej brak.

## 4. Czego świadomie nie zrobiłem

- **Nie postawiłem bramki** — powód w §2, zmierzony.
- **Nie przeliczyłem liczb 255 / 127 / 382 z §2** tamtego raportu ani liczb 20 / 19 / 14
  — są pomiarem z datą (`docs/04-conventions.md`).
- **Nie tknąłem `tests/Game.Tests`** — audyt asercji tego projektu to 6.D34, osobna
  pozycja.

## 5. Zauważone przy okazji, nietknięte

**Odtworzyłem klasyfikator „gołych" asercji i dostałem 114, nie 127 — i NIE jest to
sprostowanie tamtej liczby.** Różnicę robi definicja licznika: mój wzorzec uznaje za
licznik także `Assert.AreEqual(x.Length, …)` i `Assert.AreEqual(x.Count, …)`, tamten
najwidoczniej nie. Podaję to jako **osobny pomiar o innej definicji**, nie jako
poprawkę, bo dwie liczby z dwóch definicji zlane w jedną są gorsze od obu osobno —
i dokładnie tego rodzaju zlanie 6.A32 nazwało „dorabianiem liczby do formularza".

Rozbicie mojego klasyfikatora, dla porządku i z jego własną definicją:

```
GOLE asercje na obecnosc, po projekcie:
   Sim.Tests      61   (ogolem obecnosci: 166)
   Game.Tests     53   (ogolem obecnosci: 64)
   RAZEM         114
```

Warto przy tym zauważyć proporcję, której żaden z dwóch pomiarów nie nazywa:
w `Game.Tests` **53 z 64** asercji na obecność jest gołych (83 %), a w `Sim.Tests`
**61 z 166** (37 %). To jest liczba dla 6.D34, nie dla tej pozycji, i tam należy
ją zmierzyć jej własną definicją.
