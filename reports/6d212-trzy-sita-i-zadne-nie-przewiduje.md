# 6.D212 — trzy sita, i żadne nie przewiduje

**15.09.2026**, na `0549474`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(`WyliczeniaZrodel`), `tools/tests/csharp_test_methods.py` (`maska`),
`tools/tests/*.py`, `tests/Sim.Tests/`,
`reports/6d197-jeden-switch-i-to-ten-juz-przybity.md` §6.

## 1. Populacja, w czterech zawężeniach

| | |
|---|---:|
| asercji z `len(` w `tools/tests/` | **678** |
| testów, w których stoi `len(<goła nazwa>)` | **382** |
| zbiorów mierzonych **wyłącznie** co do długości | **234** |
| z nich powstałych z wyrażenia listowego — populacja rozstrzygająca | **48** |

„Zbiór mierzony wyłącznie co do długości" znaczy: jego nazwa nie jest w tym samym
teście ani indeksowana, ani iterowana, ani porównywana — bo każda z tych trzech dróg
wpuszcza zawartość.

**Liczba 382 jest tu spójna z resztą łańcucha i to trzeba powiedzieć wprost**, bo trzy
sita dają na tym samym drzewie trzy liczby: jakiekolwiek `len(` w asercji — **482**,
`len(<dowolne wyrażenie>)` — **481**, `len(<goła nazwa>)` — **382**. Dalszy łańcuch
idzie po gołych nazwach, bo tylko dla nich da się zapytać, czy ta sama zmienna jest
gdzie indziej indeksowana.

## 2. Rozkład 48 po kształcie producenta i po kształcie asercji

Po producencie: 63 spoza testu, 50 → po poprawce **48** z wyrażenia listowego,
15 literałów w teście, ok. 108 pojedynczych wywołań nazwanego producenta (w większości
kontrole przyrządu, gdzie `len() > 0` jest podłogą).

Po kształcie asercji, wewnątrz 48: **10** zapadek wobec stałej modułu, **11** porównań
liczności z licznością, **10** równości na goły literał, **7** podłóg, **10** innych.

## 3. Wynik pierwszy: KSZTAŁT ASERCJI NIE PRZEWIDUJE ODPOWIEDZI

Klasa „liczność wobec liczności" zawiera oba skrajne przypadki naraz:

- `test_mutation_sweep::test_identifiers_are_unique` — `len(ids) == len(set(ids))`.
  Liczność **jest** całym twierdzeniem; podstawienia nie ma, bo o zawartości nie
  twierdzi się nic.
- `test_camera_aim::…::kamery` — `len(kamery) == len(CA.KAMERY_POD_OKNEM)`. Prawa
  strona jest **przypiętym zbiorem**, a użyta jest z niego tylko długość.

Sito po kształcie odsiałoby oba tak samo.

## 4. Wynik drugi, ważniejszy: OBAJ MOI KANDYDACI BYLI BŁĘDNI, I Z TEGO SAMEGO POWODU

Nie zgadywałem — sprawdziłem podstawieniem, i oba razy wyszło odwrotnie.

**`test_camera_aim::kamery`.** Kamera przemianowana w OBU miejscach
(`render_check.py` i `camera_aim.py`), liczność 4 → 4: **24/24 zielone**. Ale bramka
nie jest ślepa: w tym samym module stoi `assert z_drzewa == set(CA.KAMERY_POD_OKNEM)`,
więc przemianowanie **jednostronne** by ją zapaliło, a zgodne jest poprawnym
refaktorem, nie usterką.

**`test_environment_doc::unikalne`.** `.cache/metro-tools` → `.cache/ZLY-KATALOG`
w czterech miejscach naraz, liczność 1 → 1: **ZAPALIŁO**
`test_the_document_names_the_cache_directory_the_installer_uses`. Zawartości pilnuje
dokument — znowu przez siostrzany test tego samego modułu.

Oba błędy mają jedną przyczynę: **sito działało w obrębie JEDNEGO TESTU, a zawartości
pilnuje MODUŁ.**

## 5. Wynik trzeci: trzecie sito też nie przewiduje

Przeliczenie z zasięgiem modułu — „czy jakakolwiek asercja tego modułu przypina
zawartość, wspominając nazwy producenta" — daje **27 pilnowanych i 21 niepilnowanych**.
I ono myli się także: `kamery` ląduje wśród niepilnowanych, bo `add_camera` i
`KAMERY_POD_OKNEM` nie mają wspólnej nazwy, choć podstawienie mówi co innego.

| sito | wynik | czy przewiduje |
|---|---:|---|
| kształt asercji | 48 | **nie** |
| zasięg jednego testu | 48 | **nie** — 2 na 2 sprawdzone okazały się pilnowane |
| zasięg modułu po wspólnych nazwach | 27 / 21 | **nie** — myli się na `kamery` |

## 6. Rozstrzygnięcie: BRAMKA NIE POWSTAJE, i to nie jest zaniechanie

Każde z trzech sit zapalałoby się dziś na kodzie poprawnym. Bramka świecąca na
poprawnym tekście zostaje **wyłączona, nie poprawiona** (6.D27) — więc jej nie ma.
Trwałe jest zdanie, które ta pozycja zmierzyła:

> Liczność bywa jedynym uprawnionym twierdzeniem znacznie częściej, niż wygląda
> z kształtu asercji, a rozstrzyga dopiero **podstawienie** — 2 na 2 sprawdzone
> tak wypadły.

To jest też wprost odpowiedź na ostrzeżenie z pola pozycji: „zamienić wszystkie na
porównanie zawartości" NIE jest odpowiedzią domyślną, i teraz wiadomo, o ile nie jest.

## 7. `WyliczeniaZrodel()` — rozstrzygnięcie: MASKA, z kontrolą przyrządu

Czytnik surowy i maskujący dają dziś w całym `src/` **20 wyliczeń i zero rozjazdów**.
Zmiana nie bierze się więc z usterki w drzewie, tylko z trzech **zmierzonych**
podstawień, które te czytniki rozdzielają:

| podstawienie | surowy | maskujący |
|---|---|---|
| `/* public enum Duch { Alfa, } */` | wymyśla wyliczenie `Duch` | widzi tylko prawdziwe |
| `"public enum Duch { Alfa, }"` w literale | wymyśla `Duch` | widzi tylko prawdziwe |
| `/* x */ Dry,` | **gubi człon** `Dry` | widzi `Dry` i `Wet` |
| `Dry, // sucha` | `Dry`, `Wet` | `Dry`, `Wet` — **bez różnicy** |

**Czwarty wiersz jest poprawką do zdania zapisanego, a nie nowym ustaleniem.**
`reports/6d197-…` §6 mówi, że „komentarz członu w tym samym wierszu (`Dry, // sucha`)
przesunąłby oba czytniki". Zmierzone: nie przesuwa — sito członów bierze **pierwsze
słowo wiersza**, a jest nim `Dry`. Raportu nie poprawiam (6.D108: raport jest historią);
granica stoi w dokumentacji czytnika i w teście.

**Maska nie jest nowym czytnikiem** — składa `PominNieNapis`, `PrefiksLiteralu`
i `CzytajLiteral`, te same prymitywy, na których stoją `Literaly` i `CialoDeklaracji`.
Druga kopia rozjechałaby się przy pierwszej poprawce (6.D209, 6.D211).

Kontrola przyrządu jest konieczna, bo rozjazd w drzewie wynosi zero: test żąda, żeby
czytnik **surowy** dał na trzech pierwszych próbkach wynik INNY, a na czwartej ten sam.
Bez tego zieleń mówiłaby tyle, co czytnik, który ją wypisał.

## 8. Kontrole negatywne

| | podstawienie | wynik |
|---|---|---|
| KN-1 | kamera przemianowana w obu miejscach (liczność 4 → 4) | **zielone** — i powód nazwany w §4 |
| KN-2 | ścieżka cache zmieniona w czterech miejscach (liczność 1 → 1) | **czerwone** — dokument ją przypina |
| KN-3 | maska zdjęta z `WyliczeniaZrodel` | kontrola przyrządu **czerwona** |
| KN-4 | `Dry, // sucha` | **zgodne oba czytniki** — granica, nie usterka |

Baza po zmianie: `dotnet test tests/Game.Tests` — **307/307**, `dotnet test tests/Sim.Tests` — **662/662**, `python3 tools/tests/test_all.py` — **2481/2481**. Po KN-3 `md5sum -c: OK`.

## 9. Czego świadomie nie zrobiłem

- **Nie postawiłem bramki** na żadnym z trzech sit — §6.
- **Nie zamieniłem żadnej bramki liczności na porównanie zawartości.** Dwie, które
  wyglądały na wymagające tego, okazały się pilnowane.
- **Nie ruszyłem `maska()`** — to 6.D200.
- **Nie tknąłem zapadek rosnących razem z drzewem** (`MIN_REPORTS` i pokrewne)
  poza przeliczeniem wymuszonym własnym commitem.

## 10. Zauważone, nie tknięte

- **Dwadzieścia jeden przypadków z §5 nie zostało sprawdzonych podstawieniem** — po
  dwóch, które sprawdziłem, przypuszczenie „niepilnowane" ma u mnie **0 na 2**
  trafień, więc tej liczby nie należy czytać jako liczby usterek.
- **`test_conflict_markers::sledzone` i `test_xml_doc_blocks::documented`** to kontrole
  przyrządu („skan naprawdę czyta drzewo"), w których `len()` jest podłogą — sito
  modułowe wrzuca je do „niepilnowanych", a nie mają czego pilnować.
- Trzy sita policzyłem, czwartego — „czy producent jest deterministyczny" — nie
  próbowałem; dla wyrażeń listowych po skanie drzewa bywa, że nie jest.
