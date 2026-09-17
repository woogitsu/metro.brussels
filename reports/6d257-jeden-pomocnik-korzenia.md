# 6.D257 — korzeń repozytorium: dziewiętnaście własnych pętli zastąpionych jedną

**Data:** 17.09.2026 · **Gałąź:** `claude/6d257-korzen-jeden-pomocnik` · **Baza:** `ee1d054`

## 1. Opis pozycji mówił o CZTERECH kopiach. Jest ich DZIEWIĘTNAŚCIE

6.D253 ujednoliciła **marker** — korzeń szuka się po pliku `MetroBxl.sln`, a nie po
katalogu `.git`, bo w worktree `.git` jest plikiem. Nie ujednoliciła **procedury**.
Pozycja 6.D257, którą sam napisałem przy domykaniu tamtej, wymieniała cztery pliki
i mówiła „cztery własne pętle na trzy sposoby". **To była nieprawda i wyszło to przy
pomiarze, nie przy czytaniu.**

Prawdziwy stan przed tą pozycją:

| marker | kopii | kształt |
|---|---|---|
| `MetroBxl.sln` | **4** | `while (katalog is not null && !File.Exists(…))` — jednowierszowy |
| `CLAUDE.md` | **15** | `while (directory is not null) { if (File.Exists(…)) … }` — wielowierszowy |

Piętnastu nie widział nikt, bo nazywały się inaczej (`RepositoryRoot` ×9,
`RepoRoot` ×3, `FindRepositoryRoot` ×3) i szukały innego pliku.

## 2. Bramka, którą napisałem godzinę wcześniej, była ZIELONA i twierdziła nieprawdę

Pierwsza wersja `test_korzenia_repozytorium_szuka_DOKLADNIE_JEDNO_miejsce` żądała
`File.Exists` w **tym samym wierszu** co `while`. Kształt wielowierszowy ma sprawdzenie
istnienia trzy wiersze niżej — więc bramka **przechodziła**, mówiąc „dokładnie jedno
miejsce", przy piętnastu kopiach w drzewie.

To jest 6.D27 w czystej postaci i trafiło na mnie: bramka meldowała sprawdzenie,
którego nie zrobiła. Znalazł to **pomiar powtórzonych pomocników** (`private static`
o tej samej nazwie w więcej niż jednym pliku), zrobiony przy szukaniu pozycji do
uzupełnienia kolejki — nie przegląd kodu i nie własna bramka.

Czytnik jest teraz **blokowy**: `while` plus osiem wierszy okna. Osiem, bo tyle zajmuje
najdłuższa ze znalezionych kopii.

## 3. Jeden pomocnik, linkowany do obu projektów

`tests/Shared/KorzenRepozytorium.cs`, wciągany do `Game.Tests` i `Sim.Tests` przez
`<Compile Include="../Shared/KorzenRepozytorium.cs" Link="…" />`.

**Dlaczego plik linkowany, a nie trzeci projekt.** `Game.Tests` i `Sim.Tests` są
niezależne celowo: `Game.Tests` nie stoi w `MetroBxl.sln`, bo rdzeń ma się budować
i testować bez silnika (reguła 9 `CLAUDE.md`). Trzeci projekt byłby **nową zależnością
obu**, a linkowany plik źródłowy nią nie jest.

**Dwie postaci, i to nie jest ozdoba.** `Sciezka` odmawia, gdy korzenia nie ma;
`SciezkaAlboNull` zwraca `null`. Druga istnieje, bo **trzy testy rdzenia branżują na
`null`** — jeden woła `Assert.IsNotNull`, drugi `Assert.Inconclusive`. Zamiana ich na
odmowę byłaby **zmianą zachowania przemyconą przy sprzątaniu duplikatów**, a sprzątanie
duplikatów ma zostawić zachowanie takim, jakie było.

**Pomocnik nie woła `Assert`**: brak korzenia nie jest niespełnionym oczekiwaniem testu,
tylko niemożliwym do przeprowadzenia przebiegiem, a plik bez zależności od frameworka
wchodzi do obu projektów tak samo.

## 4. Weryfikacja

```
WSZYSTKICH petli z File/Directory.Exists w tests/: 1
  KorzenRepozytorium.cs   73   while (katalog is not null && !File.Exists(Path.Combine(katalog, Marker)))

~/.dotnet/dotnet test tests/Game.Tests
Passed!  - Failed:     0, Passed:   318, Skipped:     0, Total:   318

~/.dotnet/dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   673, Skipped:     0, Total:   673
```

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

| kontrola | przewidziane | zmierzone |
|---|---|---|
| KN-1 kopia w kształcie **jednowierszowym**, z poprawnym markerem | nowa bramka czerwona, **stara z 6.D253 ZIELONA** | tak: `('HandleTrainKeysGateTests.cs', 54, 'while (katalog is not null && !File.Exists(…))')`, **16/18**; bramka markera milczy |
| KN-1b ta sama kopia w kształcie **wielowierszowym** | po rozszerzeniu czytnika: czerwona; **przed rozszerzeniem była ZIELONA** | `('HandleTrainKeysGateTests.cs', 54, 'while (directory is not null)')`, **16/18** |
| KN-2 podmiana markera w POMOCNIKU na `.git` | bramka z 6.D253 czerwona, wskazuje **jeden** plik, nie dziewiętnaście | `[('KorzenRepozytorium.cs', 59, …)]`, **16/18** |
| KN-3 kontrola przyrządu, pięć kształtów syntetycznych | widzi cztery kopie, **nie widzi** komentarza, wołania pomocnika ani zwykłej pętli | zielone |

**KN-1b jest tą kontrolą, która uratowała tę pozycję przed opublikowaniem nieprawdy.**
Pokazuje na żywo, że pierwsza wersja czytnika była ślepa dokładnie na ten kształt,
w którym stało piętnaście kopii.

KN-3 sprawdza teraz **pięć** kształtów, nie cztery: doszedł wielowierszowy, a także
przypadek negatywny „zwykła pętla bez sprawdzania istnienia pliku" — bez niego czytnik
uznałby każdy `while` w testach za kopię szukania korzenia.

## 6. Czego NIE zrobiono

- **Nie ujednolicono markera `CLAUDE.md` → `MetroBxl.sln` jako osobnej zmiany** — po
  konsolidacji marker jest jeden, bo pętla jest jedna; piętnaście miejsc przestało mieć
  własny marker w ogóle.
- **Nie dodano trzeciego projektu testowego** — byłby nową zależnością obu.
- **Nie objęto `src/`** — poza testami nikt w repozytorium korzenia nie szuka,
  a w kodzie produkcyjnym taka pętla byłaby osobną usterką, nie duplikatem.
- **Nie zdjęto martwych gałęzi `null`** u trzech wywołujących `SciezkaAlboNull`.
  Są dziś nieosiągalne w normalnym przebiegu, ale ich zdjęcie jest zmianą zachowania,
  a nie sprzątaniem duplikatów.

## 7. Co zauważone przy okazji, nietknięte

- **Powtórzonych nazw pomocników `private static` w `tests/` jest 24**, na 236
  wszystkich. Szukanie korzenia było największą rodziną (19), ale nie jedyną:
  `Settings` ×7, `Level` ×7, `Plan` ×6, `Axis` ×5. Żadnej z nich nie pilnuje nic.
- **Duplikat, który wygląda na wariant, jest trudniejszy do zauważenia niż dosłowny.**
  Piętnaście kopii różniło się wyłącznie nazwą metody i typem zwracanym; trzy warianty
  nazwy wystarczyły, żeby przez dwie doby nikt ich nie policzył.
