# 6.D143 — `KeyNames.cs` wchodzi do zakresu bramki tablicą, a nie plikiem

**11.09.2026**, na `0279704`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/Input/KeyNames.cs`. Pozycja pytała, czy plik ma wejść do zakresu bramki
literałów, i żądała liczby literałów policzonej z drzewa.

## 1. Trzy literały, i każdy z innym rozstrzygnięciem

Zmierzone czytnikiem bramki (`Literaly(KodBezKomentarzy(…))`):

| literał | sito, które go łapie | widzi go bramka? |
|---|---|---|
| `Esc` | 3 — wyjątek `NazwyKlawiszy` | **tak**, w zakresie |
| `input.key.space` | 4 — klucz katalogu | **tak**, w zakresie |
| `nie ma nazwy dla klawisza o kodzie fizycznym {(int)key} ({key})` | 5 — **ZGŁOSZONY** | nie, poza zakresem |

Dwa pierwsze stoją w tablicy `Nazwy`, trzeci jest komunikatem `KeyNotFoundException`
w `For`. `"Esc"` przechodzi wyjątkiem, `"input.key.space"` — katalogiem, i to są dwa
RÓŻNE powody; rozróżnienie z 6.D130 dostaje tu pierwszy prawdziwy przedmiot.

## 2. Rozstrzygnięcie: skanowana jest TABLICA, nie plik

Skan całego pliku zapaliłby bramkę **dziś**, na komunikacie wyjątku, i zostałby
wyłączony — czyli bramka zniknęłaby razem z tym, czego miała pilnować. To ta sama
decyzja i to samo zdanie, co przy `MetodyFirstRun` (6.D99).

**Druga droga została rozważona i przegrała.** Tu byłaby wykonalna inaczej niż przy
`FirstRun.cs`: skan całego pliku z komunikatem wpisanym na listę wyjątków, bo wyjątek
byłby **jeden**. Przegrywa, bo lista wyjątków rośnie z każdym nowym `throw` i jest
drogą powrotną dla tego, co bramka miała wykluczyć — ten sam powód, dla którego sito
identyfikatorów silnika jest REGUŁĄ, a nie listą nazw. Granica po członie mówi
natomiast coś prawdziwego i trwałego: **tablica jest tekstem, `throw` jest diagnostyką.**

**Skala, dla której ta granica w ogóle istnieje, jest zmierzona.** Bramka puszczona
na całe `src/Game/` zgłosiłaby **348** literałów w **21** plikach, z czego **22** stoją
w `throw`, a reszta to wypisy diagnostyczne (`[TELEMETRIA]`, `[LINIA]`, `[TUNEL]`),
prozą opisane założenia projektowe i nazwy pól JSON. Najwięcej: `RunPlan.cs` 142,
`FirstRun.cs` 105, `DesignAssumptions.cs` 20, `ChunkManifest.cs` 20. `KeyNames.cs`
ma z tych 348 dokładnie **jeden**.

## 3. Objaw z 6.D130 jest odtwarzalny po raz pierwszy

To jest główny wynik pozycji. Wpis 6.D130 mówił, że podmiana `"Esc"` na `"Escape"`
nie zapala żadnej bramki, i że objawu **nie dało się odtworzyć**, bo napis przeniósł
się do pliku, którego nikt nie skanuje. Po tej pozycji zapala się, z komunikatem,
który 6.D130 stworzyło właśnie na tę okazję (kontrola KN-2, wklejona):

```
Assert.AreEqual failed. Expected:<0>. Actual:<1>. w `IReadOnlyDictionary<Key, string>
Nazwy` stoi literał, którego katalog nie zna: "Escape" (nazwa klawisza silnika spoza
`NazwyKlawiszy`)
```

## 4. Kontrole negatywne

Baza: **237/237**. Po każdej `cp` z kopii i `md5sum -c: OK` na obu plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | `"Esc"` → `"Prędkość"` w tablicy | **231/237**, sześć testów | bramka łapie polszczyznę tam, gdzie jej dotąd nie widziała |
| KN-2 | `"Esc"` → `"Escape"` w tablicy | **231/237**, sześć testów | objaw z 6.D130 odtworzony, z właściwym powodem |
| KN-3 | `CzlonyKeyNames` puste | **236/237**, JEDEN test | **znalazła dziurę, którą sam zrobiłem** — patrz niżej |
| KN-3b | to samo po załataniu | **235/237**, dwa testy | dziura zamknięta |
| KN-4 | nagłówek członu rozjechany | **235/237**, dwa testy | `CialoMetody` nie mierzy cudzego członu po cichu |
| KN-5 | nowa diagnostyka po polsku poza tablicą | **236/237**, test rozstrzygnięć | literał dopisany gdziekolwiek w pliku wymusza decyzję |

### KN-3 jest tu wynikiem, nie formalnością

Przy pustej liście członów `W_tablicy_KeyNames_nie_ma_ani_jednego_slowa` **przechodzi**:
pętla nie wykonuje ciała ani razu, więc bramka melduje sprawdzenie, którego nie
zrobiła — dokładnie ta rodzina, którą projekt tropi od 6.D27, tym razem z mojej ręki.
Zapalił się wyłącznie test rozstrzygnięć, czyli sąsiad. Bramka nie ma mieć dziury,
którą łata sąsiad, więc doszło dolne ostrze na długość listy członów i KN-3b pokazuje
obie czerwone.

Komunikat KN-5, wklejony:

```
Assert.AreEqual failed. Expected:<3>. Actual:<4>. `KeyNames.cs` ma 4 literałów, a pomiar
z 11.09.2026 dał 3: Esc | input.key.space | tabela nazw klawiszy ma wpisow:  | nie ma
nazwy dla klawisza o kodzie fizycznym {(int)key} ({key})
```

## 5. Zauważone przy okazji: liczba z 6.D130 jest mierzona na innym korpusie niż bramka

Docstring `NazwyKlawiszySilnika` (6.D130) niesie ocenę ryzyka kolizji: „w całym
`src/Game/` stoi **948** literałów (**746** różnych), a nazwą klawisza jest **sześć**:
`Escape`, `F1`, `F2`, `Forward`, `Right`, `Up`". Liczba jest odtwarzalna — ale tylko
**z komentarzami i z `UiText.cs`**:

| korpus | literałów | różnych | nazw klawiszy |
|---|---:|---:|---:|
| jak w docstringu (wszystkie `.cs`, z komentarzami) | 949 | 748 | 6 — `Escape, F1, F2, Forward, Right, Up` |
| `ZrodlaGry()`, z komentarzami | 861 | 684 | 6 — te same |
| **`ZrodlaGry()`, bez komentarzy — czyli to, co bramka WIDZI** | **521** | **395** | **7 — `C, F1, F2, R, S, W, X`** |
| regiony skanowane przed tą pozycją | 67 | — | 13 wystąpień, 7 różnych |

Cztery z sześciu nazw z docstringu — `Escape`, `Forward`, `Right`, `Up` — **istnieją
wyłącznie w komentarzach**, których bramka nie czyta. W kodzie widzianym przez bramkę
nazwami klawiszy są za to `W`, `S`, `X`, `C`, `R`, których docstring nie wymienia
wcale, bo są jednoliterowe.

Ocena ryzyka policzona na korpusie szerszym niż zasięg przyrządu **zawyża ryzyko
i jednocześnie pomija to, które istnieje** — lustrzane odbicie rodziny 6.D27.
Zdania nie ruszam: należy do `NazwyKlawiszySilnika` i do 6.D130, a jedno zadanie to
jedna zmiana. Do kolejki poszła osobna pozycja.

## 6. Dwie zapadki podniesione, obie z powodem wypisanym

**`MAX_GAME_UNMATCHED_NEEDLES`, podniesiona z 24 na 26.** Dwie nowe igle, `Esc` i `input.key.space`,
stoją w teście rozstrzygnięć jako **oczekiwana zawartość tablicy `Nazwy`**, przybita
równością całej listy. Bez dopasowania w komunikatach `src/Game` są z założenia i mają
takie zostać: bramka szczebla 1 szuka igieł w komunikatach WIELOWYRAZOWYCH, a to są
pozycje tablicy — jednowyrazowy napis wytłoczony na klawiszu i klucz katalogu. Gdyby
którakolwiek dopasowała się do komunikatu programu, znaczyłoby to, że napis klawisza
wszedł do zdania dla człowieka, czyli coś odwrotnego od tego, czego ta pozycja pilnuje.
Wzmocnienie igły nie ma tu sensu z innego powodu niż przy 19 → 21: tam igła opisywała
wejście syntetyczne, tu opisuje **zawartość drzewa**, którą test i tak pinuje równością.
Igła dłuższa byłaby tym samym pinem zapisanym drugi raz.

**`MINIMUM_DETAIL_BLOCKS`, podniesiona z 225 na 228**, bo doszły trzy bloki (6.D153 – 6.D155). Trzy,
a nie sześć jak poprzednio, i to też jest liczba z arytmetyki: jedenaście plus trzy
daje czternaście przy progu dwunastu. Wymyślanie dalszych na zapas byłoby braniem
zadania z sufitu, czego `CLAUDE.md` §8 zabrania ostatnim zdaniem.

Spis pinów z 6.D141 znów zapalił się na przesunięciu wierszy: kategoria A
552/558/563 → **689/695/700**, B 632/633 → **769/770**, piny liczbowe 188 → **191**
(całkowite 84 → **87**). Pinów napisowych przybyło zero — `CollectionAssert.AreEqual`
czytnikiem nie jest.

## 7. Czego nie zrobiono

- **Nie zmieniono zawartości `KeyNames.cs`** ani katalogu tekstów — pole „Poza zakresem".
- **Nie rozszerzono zakresu na resztę `src/Game/`.** 348 zgłoszeń to nie jest praca,
  którą wolno dopisać przy okazji; liczba jest zmierzona i czeka na własną pozycję.
- **Nie dodano sita na `throw`.** Byłoby regułą zamiast listy, ale zmieniłoby też to,
  co bramka widzi w plikach już skanowanych — czyli poszerzyłoby pozycję o pliki,
  o które nikt nie prosił.
- **Nie poprawiono docstringu `NazwyKlawiszySilnika`** — patrz sekcja 5.
