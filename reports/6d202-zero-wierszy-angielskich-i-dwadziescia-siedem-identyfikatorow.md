# 6.D202 — wierszy angielskich jest ZERO, a angielskich identyfikatorów dwadzieścia siedem

**13.09.2026**, na `72428eb`. Wejście: `src/Game/DesignAssumptions.cs`,
`src/Game/**/*.cs` (wiersze wypisywane przez `GD.Print`),
`tests/Game.Tests/UiTextTests.cs` (`ZrodlaHud`, `BezDziur`),
`reports/6d188-czternascie-i-ani-jednego-jsona.md` §8.

## 1. Trzy liczby, o które pytało pole „Wyjście"

| liczba | ile |
|---|---:|
| wywołań `GD.Print` w `src/Game/` | **25** |
| wierszy z własnymi słowami, **wszystkie po polsku** | **21** |
| wierszy **bez ani jednego własnego słowa** (cała treść z wywołania) | **4** |
| wierszy **po angielsku** | **0** |

Cztery wiersze bez własnych słów prowadzą do czterech wytwórców i **każdy z nich pisze
po polsku**: `RunHeader.Line` → `[PRZEJAZD]`, `StationView.Describe` → `[PERON]`,
`TrainView.Describe` → `[SKŁAD]`, `TunnelView.Describe` → `[TUNEL]`. Sprawdza to osobna
asercja, żeby „cztery bez słów" nie czytało się jako „cztery nieznanego języka" — bo to
jest różnica między zerem wierszy angielskich a czterema niewiadomymi.

## 2. Przesłanka pozycji padła, i to na DWA sposoby naraz

Pozycja pisała: *„`BezDziur` zabiera mu wszystkie słowa (…) — a sam szablon jest po
angielsku"*. Szablon brzmi:

```csharp
$"{Name} = {Value:R} {Unit} — {Reason}"
```

**Nie ma w nim ani jednego słowa** — są dziury, znak równości i myślnik. Nie jest więc
„po angielsku"; nie jest w żadnym języku. Po drugie: **wszystkie 20 pól `Reason`
w `DesignAssumptions.All` są po polsku**, i po polsku jest też prefiks wiersza
(`[ZAŁOŻENIE widok]`). Jedyne, co przychodzi po angielsku, to pole `Name` — a ono jest
**IDENTYFIKATOREM z `nameof(...)`**, nie prozą.

Gotowy wiersz wygląda tak:

```
[ZAŁOŻENIE widok] CabEyeHeightM = 2.2 m — wysokość oka nad główką szyny; podłoga M7 …
```

Polski prefiks, angielski identyfikator, polskie uzasadnienie. **Jest to dokładnie ten
sam kształt, co przy 6.D185**, gdzie na HUD docierała angielska nazwa członu wyliczenia:
na wyjście trafia **identyfikator, nie zdanie**.

## 3. Dwadzieścia siedem identyfikatorów, dwiema drogami, o różnym ryzyku

| droga | ile | co się dzieje przy zmianie nazwy stałej |
|---|---:|---|
| `nameof(...)` | **25** | log idzie za nazwą automatycznie |
| literał napisowy | **2** | **log zostaje przy nazwie starej — po cichu** |

Dwa literały to `"StartChainageM"` i `"BrakeChainageM"`
w `src/Sim/Train/DriveScenario.cs:146` i `:149`. Liczba stoi w bramce **osobno**, bo jest
to inne ryzyko, a nie inna ilość tego samego: `nameof` jest sprawdzany przez kompilator,
literał nie jest sprawdzany przez nic.

## 4. Sito po znaku diakrytycznym myli się na TRZECH z dwudziestu pięciu

Pierwsza wersja bramki uznawała wiersz za polski, jeśli miał ogonek. Zmierzone: trzy
wiersze polskie ogonka **nie mają** — `[STACJA]`, `[ZRZUT] metadane` (`FirstRun.cs`)
oraz **cały wiersz `[PRZEJAZD]` z `RunHeader.cs`**, którego słowa to `tryb`, `widok`,
`krok`, `scenariusz`, `masa`. Bramka meldowała je jako nierozpoznane i **pytanie do
właściciela stałoby na liczbie „trzy wiersze angielskie", która jest nieprawdą**.

Znak diakrytyczny jest więc **pierwszym sitem, nigdy jedynym**; drugim jest lista słów
polskich bez ogonków. Złapała to bramka w pierwszym przebiegu, nie przegląd.

## 5. Pytanie do właściciela — NA LICZBACH, nie na jednym przykładzie

Pole pozycji żądało wprost, żeby pytanie stało na liczbach. Stoi tak:

> Log przejazdu ma **25 wierszy, z czego 0 po angielsku**. Jedyna angielszczyzna to
> **27 identyfikatorów** w wierszach `[ZAŁOŻENIE scenariusz]` i `[ZAŁOŻENIE widok]` —
> nazwy stałych, nie zdania. Czy to zostaje tak, jak jest?

Pytanie **nie brzmi** „czy założenia mają być po polsku", bo one po polsku **są**.
Brzmi: czy w polskim wierszu logu ma stać angielska nazwa stałej, skoro jest ona
jedynym kluczem od tego wiersza do kodu.

## 6. Siedem kontroli negatywnych, baza 270/270

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | wiersz logu po angielsku dopisany do `src/Game/` | 265/270 (na przypiętych liczbach korpusu) |
| KN-1b | to samo przy podniesionych liczbach — jedna zmienna | 265/270 (na **SICIE JĘZYKA**) |
| KN-2 | `TunnelView.Describe` przestaje pisać po polsku | 268/270 |
| KN-3 | pętla po wytwórcach obiega raz zamiast czterech | 269/270 |
| KN-4 | czytnik leksykalny zdjęty (czytanie źródła surowego) | **270/270 ZIELONA** |
| KN-4b | `GD.Print` w komentarzu, po dołożeniu asercji | 269/270 |
| KN-5 | korpus pomija `FirstRun.cs` (kontrola przyrządu) | 269/270 |
| KN-6 | szablon założenia dostaje własne słowo | 267/270 |

`md5sum -c` na czterech plikach po każdej: `OK`.

**KN-4 wyszła zielona i sprawdziłem, dlaczego.** Zmierzone: w `src/Game/` `GD.Print`
stoi **25 razy w źródle surowym i 25 razy po zdjęciu komentarzy i literałów** — ani
jednego w prozie, więc czytnik nie ma czego zdjąć i zieleń jest poprawna. Z bezczynności
zrobiłem rzecz **sprawdzaną** (asercja porównuje obie liczby); KN-4b to potwierdza.

**Mechanizm nie jest przy tym teoretyczny i to jest różnica wobec 6.D197:** tam słowa
`switch` w prozie nie było nigdzie, tu `GD.Print` w prozie **stoi** — w
`src/Sim.Runner/Program.cs`, czyli w pliku poza korpusem tej pozycji. Gałąź jest więc
bezczynna **przez granicę korpusu**, a nie przez brak zjawiska.

## 7. Czego świadomie nie zrobiłem

- **Niczego nie przetłumaczyłem** — pole „Poza zakresem" zabrania, a pomiar mówi, że
  nie ma czego: wierszy angielskich jest zero.
- **`src/Game/` nie zmieniałem**, wierszy logu do katalogu `UiText` nie przenosiłem.
- **Decyzji nie podjąłem.** Pozycja mówi wprost, że to decyzja właściciela, a ta pozycja
  ma ją PRZYGOTOWAĆ — §5 jest tym przygotowaniem.

## 8. Zauważone po drodze, nie tknięte

- **`src/Sim.Runner/Program.cs` ma `GD.Print` w prozie** — pierwszy w drzewie przypadek,
  w którym obcinacz komentarzy dla tego skanu **przestaje być bezczynny**. Poza korpusem
  tej pozycji, ale to znaczy, że skan puszczony szerzej niż `src/Game/` musi go mieć.
- **`GD.PrintErr` i `GD.PushError` stoją poza tym pomiarem.** `Abort(int, string)`
  wypisuje `message` obiema drogami, a treść przychodzi od wołającego — żadna z liczb
  tej pozycji ich nie obejmuje, bo pytanie było o **log przejazdu**, nie o błędy.
  Ilu jest wołających `Abort` i w jakim języku piszą, nie policzył nikt.
- **Dwa literały nazw założeń (`"StartChainageM"`, `"BrakeChainageM"`) są jedynym
  miejscem w tym mechanizmie, gdzie przemianowanie stałej rozjeżdża log z kodem po
  cichu.** Zamiana na `nameof(...)` jest jednowierszowa i nic poza tym nie rusza —
  ale leży w `src/Sim/`, a pole „Poza zakresem" tej pozycji mówi o `src/Game/`.
