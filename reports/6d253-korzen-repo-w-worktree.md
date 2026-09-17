# 6.D253 — `.git` jest w worktree PLIKIEM, więc korzeń szukany po katalogu nie znajdzie się nigdy

**Data:** 17.09.2026 · **Gałąź:** `claude/6d253-korzen-repo` · **Baza:** `5d7278f`

## 1. Usterka, zmierzona w obu układach

Dwa testy `Game.Tests` szukały korzenia repozytorium tak:

```csharp
while (katalog is not null && !Directory.Exists(Path.Combine(katalog, ".git")))
```

W zwykłym checkoucie `.git` jest **katalogiem**, więc pętla znajduje korzeń. W worktree
`.git` jest **plikiem** — u mnie 57 bajtów — więc `Directory.Exists` nie znajdzie go
nigdy i pętla dochodzi do korzenia systemu plików.

```
główny katalog roboczy:   Passed! - Failed: 0, Passed: 318, Total: 318
worktree (.git to plik):  Failed! - Failed: 7, Passed: 311, Total: 318
```

**Ten sam commit, ta sama komenda, dwa różne wyniki** — różnicą jest wyłącznie układ
katalogu roboczego.

## 2. Dlaczego to stało tak długo

`CLAUDE.md` §5 wymienia jako weryfikację kodu `python3 tools/tests/test_all.py`
i `dotnet test tests/Sim.Tests`. **`Game.Tests` w tej pętli nie stoi.** Czerwień poza
pętlą weryfikacji stoi dokładnie tak długo, jak długo nikt na nią nie patrzy — a agenci
tego projektu pracują w worktree **z instrukcji**, czyli w jedynym układzie, w którym ta
usterka się objawia.

## 3. Rozkład siódemki — zmierzony, nie podzielony na oko

Cofnięcie poprawki **po jednym miejscu naraz** rozkłada ją jednoznacznie:

| plik | ile testów pada w worktree |
|---|---|
| `TrainingWiringTests.cs` | **5** |
| `TractionBlockTests.cs` | **2** |

Pierwotny pomiar (przy 6.D229 i 6.D233) nazywał **jedno** miejsce; drugie wyszło dopiero
przy pisaniu tej pozycji. Oba były nośne — cofnięcie każdego z osobna daje czerwień.

## 4. Poprawka: marker, który jest plikiem w obu układach

Wzór stał w tym samym katalogu od dawna — `HandleTrainKeysGateTests`:

```csharp
while (katalog is not null && !File.Exists(Path.Combine(katalog, "MetroBxl.sln")))
```

`MetroBxl.sln` jest **treścią repozytorium** i **plikiem** niezależnie od tego, czy
katalog roboczy jest checkoutem, czy worktree. Punkt startu przeniesiony przy okazji
z `Directory.GetCurrentDirectory()` na `AppContext.BaseDirectory` — tak samo jak we
wzorze, bo katalog bieżący zależy od tego, skąd uruchomiono runner, a katalog binarki
nie.

Po poprawce, oba układy:

```
główny katalog roboczy:   Passed! - Failed: 0, Passed: 318, Total: 318
worktree (.git to plik):  Passed! - Failed: 0, Passed: 318, Total: 318
```

## 5. Bramka, bo sama poprawka wraca po cichu

Poprawka bez bramki jest jednorazowa: następny test napisany z tym samym wzorem
przejdzie u autora i padnie na maszynie agenta. Bramka
`test_zaden_test_nie_szuka_korzenia_repozytorium_po_KATALOGU_git` skanuje wszystkie
`tests/*/*.cs` i odmawia kształtu `Directory.Exists(… ".git")`.

**Wzorzec stoi na SUROWYM źródle, nie na masce, i to jest wymóg, nie skrót:** `maska()`
tego modułu zamienia literały na spacje, a `".git"` **jest** literałem — po masce tego
kształtu nie da się zobaczyć w ogóle.

**Komentarz nie liczy się jako usterka.** Wiersz jest ucinany na `//` przed
sprawdzeniem, żeby dało się o tej usterce napisać w komentarzu — czego ten plik teraz
robi w dwóch miejscach.

## 6. Kontrole negatywne — przewidywania spisane PRZED przebiegami

| mutacja | przewidziane | zmierzone |
|---|---|---|
| KN-1 poprawka cofnięta w **jednym** miejscu, przebieg w worktree | czerwone, **część** siódemki | **5/318 padło** — dokładnie testy `TrainingWiringTests` |
| KN-2 ta sama usterka wobec **bramki** | czerwone, z nazwą pliku i wierszem | **15/16**, `[('TrainingWiringTests.cs', 35, …)]` |
| KN-3 **kontrola przyrządu**, wejście syntetyczne | wzorzec widzi zły kształt, **nie widzi** dobrego, **nie widzi** komentarza | zielone, wszystkie trzy |

**KN-3 jest tu obowiązkowa, nie ozdobna.** Bez niej literówka we wzorcu dawałaby zero
winnych i zieleń — stan **nieodróżnialny** od poprawnego drzewa. Trzecia jej asercja
(komentarz nie jest usterką) chroni przed bramką, która zapala się na prozie o sobie
samej; sam ten raport i komentarze w poprawionych plikach są jej przypadkiem użycia.

## 7. Czego NIE zrobiono

- **Nie dopisano `Game.Tests` do pętli weryfikacji `CLAUDE.md` §5.** To zmiana
  konstytucji projektu i decyzja właściciela; pole „Poza zakresem" tej pozycji mówi
  o tym wprost. Bramka z §5 tego raportu łapie **kształt** w kodzie, a nie zastępuje
  uruchamiania `Game.Tests` — czerwień z innej przyczyny nadal stanie niezauważona.
- **Nie ruszono żadnej czerwieni `Game.Tests` o innej przyczynie** — dziś nie ma takiej,
  ale gdyby była, byłaby osobną pozycją.

## 8. Co zauważone przy okazji, nietknięte

- **Trzy różne sposoby szukania korzenia w jednym katalogu testów.**
  `HandleTrainKeysGateTests` szuka po `MetroBxl.sln` od `AppContext.BaseDirectory`,
  a dwa poprawione pliki robiły to po `.git` od `Directory.GetCurrentDirectory()`.
  Po tej pozycji zostają dwa warianty startu, bo poprawka ujednoliciła marker, a nie
  całą procedurę. Wspólny pomocnik byłby osobną pozycją — i dopiero on zdjąłby ryzyko,
  że czwarty plik wymyśli czwarty sposób.
