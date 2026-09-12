# 6.D182 — czytnik rozcinał 5 literałów na 480, a rodzin liczonych po treści nie ruszył ani o jeden

**12.09.2026**, na `dad68a0`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/RunPlan.cs`, `src/Game/FirstRun.cs`, korpus `src/Game/` (21 plików).
Pozycja żądała dwóch rzeczy: **zmierzyć, ile literałów jest uciętych**, i **rozstrzygnąć,
czy czytnik da się naprawić bez rozbioru składni C#** — a jeśli nie, to które liczby
z 6.D154…6.D179 wymagają przeliczenia. Pole pozycji mówiło wprost: *zgadywanie zakazane*.

## 1. Jak to zmierzone — kodem bramki, nie reimplementacją

Cały pomiar chodził jako **tymczasowy `[TestMethod]` wstawiony do
`tests/Game.Tests/UiTextTests.cs`** i puszczany przez `dotnet test --filter`, więc
pytał dokładnie tego `Literaly`, `KodBezKomentarzy`, `ZrodlaGry` i `SlowaWKodzie`,
które czyta bramka. Po pomiarze metody zdjęte, `md5sum -c` na pliku: `OK`.

Powód tej ostrożności jest z tej samej sesji: przy 6.D179 reimplementacja sita
w Pythonie dała **446** zamiast **348** i wyglądała jak wynik. Kontrola, że przyrząd
jest ten sam, jest tu twarda — pomiar odtwarza `348` **co do jedynki**.

## 2. GŁÓWNY WYNIK: uciętych jest **pięć** literałów na **480**, w **dwóch** plikach z 21

Referencją był **lekser** napisany na tę okazję (stan: komentarz wierszowy, komentarz
blokowy, literał znakowy, napis zwykły, dosłowny, surowy, dziura interpolacji).

```
PLIKOW=21 BRAMKA=521 LEKSER=480 ZGODNYCH=475
UCIETYCH=3 NIE-LITERALOW=43 NIEWIDZIANYCH=2 PLIKOW_DOTKNIETYCH=2
```

Czyta się to tak:

| liczba | co znaczy |
|---|---|
| **480** | literałów jest w korpusie naprawdę |
| **521** | pozycji zwracał stary czytnik |
| **475** | z tych 521 było literałami w całości |
| **3** | było kawałkami literałów urwanymi w połowie |
| **43** | nie było literałami w ogóle — to kawałki KODU między cudzysłowami |
| **5** | literałów prawdziwych nie docierało do żadnej bramki w całości |

**Różnica „siedem fałszywych pozycji" a „N literałów policzonych w połowie", o którą
pozycja pytała wprost, wynosi: fałszywych pozycji jest 46, a literałów rozciętych 5.**
Liczby te nie są tą samą liczbą i żadna nie wynosi siedem.

### 2.1. `RunPlan.cs` — dwa napisy interpolowane z zagnieżdżonym cudzysłowem

```csharp
$"[ARGUMENT] nieznany argument '--{name}'. Znane: --{string.Join(" --", KnownArguments)}"
$"[ARGUMENT] nieznany widok '--view={view}'. Znane: {string.Join(", ", KnownViews)}"
```

Każdy dawał **dwie** pozycje zamiast **dwóch literałów**, i to nie tych samych:

| stary czytnik zwracał | co to jest |
|---|---|
| `[ARGUMENT] nieznany argument '--{name}'. Znane: --{string.Join(` | literał **urwany** |
| `, KnownArguments)}` | **kawałek kodu**, nie literał |
| `[ARGUMENT] nieznany widok '--view={view}'. Znane: {string.Join(` | literał **urwany** |
| `, KnownViews)}` | **kawałek kodu**, nie literał |

a literałami są tu **cztery** rzeczy: dwa napisy zewnętrzne w całości oraz dwa napisy
z dziur interpolacji — `" --"` i `", "`. Te dwa ostatnie nie docierały **nigdzie**:
nie były ani zwrócone, ani urwane, tylko połknięte.

### 2.2. `FirstRun.cs` — jeden napis surowy rozcięty na 42 pozycje

`FirstRun.cs:2232` niesie **napis surowy interpolowany** `$$"""…"""` długości
czterdziestu wierszy — metadane JSON zrzutu. Stary czytnik robił z niego
**jeden kawałek urwany i 41 pozycji, które literałami nie są**, a sam literał
ginął w całości. Pozycje wyglądały tak:

```
  UCIETY   |\n        {\n         |
  NIE-LIT  |: |
  NIE-LIT  |,\n         |
  NIE-LIT  |: {{ChainageM:F3}}, |
  NIE-LIT  |: [{{lo.X:F4}}, {{lo.Y:F4}}, {{lo.Z:F4}}],\n          |
```

**Parzystość cudzysłowów jest tu treścią, a nie ciekawostką.** Czytnik parował
cudzysłów zamykający nazwę pola z otwierającym jego wartość, więc zwracał
**przerwy między polami JSON-a, a nie same pola**. Nazwy `engine`, `godot`, `scene`,
`vertices` nie stały w jego wyjściu **ani razu** — mimo że stoją w pliku.

## 3. ROZSTRZYGNIĘCIE: czytnik da się naprawić **bez** rozbioru składni C#

Wszystkie cztery konstrukcje, które łamały wzorzec, są **leksykalne**: o tym, gdzie
kończy się napis, rozstrzyga sam ciąg znaków, a nie to, czym jest otaczające wyrażenie.

| konstrukcja | co rozstrzyga koniec napisu | w korpusie |
|---|---|---|
| dziura interpolacji `{…}` | domknięcie klamry, licząc zagnieżdżenia | 2 |
| napis surowy `"""`, `$$"""` | tyle cudzysłowów, iloma się otworzył | 1 |
| napis dosłowny `@"…"` | cudzysłów niepodwojony | 0 |
| literał znakowy `'"'` | apostrof zamykający | 0 |

Wystarczy więc **lekser ze stanem**, a parser jest niepotrzebny. Roslyn
(`Microsoft.CodeAnalysis.CSharp`) byłby **zależnością**, a `CLAUDE.md` §8 każe przy
dodaniu zależności przerwać i zapytać — droga odrzucona, nie przeoczona.

Naprawa stoi w `Literaly` i jest **jedną kopią**: wszystkie **siedem** miejsc, które
czytnik wołały, dostało ją naraz, bo żadne nie ma własnego wzorca.

## 4. KTÓRE LICZBY TO RUSZA — zmierzone na obu czytnikach, nie wywnioskowane

Ten sam pomiar puszczony raz z czytnikiem leksykalnym i raz z przywróconym wzorcem:

| liczba | stary czytnik | po naprawie | |
|---|---|---|---|
| baza: sito na całym `src/Game/` | **348** | **347** | **ZMIENIA SIĘ** |
| plików zgłaszających | 16 | 16 | bez zmian |
| prefiks w nawiasie kwadratowym | 71 | 71 | bez zmian |
| identyfikator, reguła wąska `^[a-z_][a-z0-9_]*$` | 96 | 96 | bez zmian |
| identyfikator, reguła szeroka z kropką i myślnikiem | 123 | 123 | bez zmian |
| literał z polskim znakiem diakrytycznym | 140 | 140 | bez zmian |
| 6.D180: `FirstRun.cs` całym plikiem | **105** | **106** | **ZMIENIA SIĘ** |
| 6.D180: `FirstRun.cs` wiersz po wierszu | 118 | 118 | bez zmian |

**Odpowiedź na pytanie pozycji brzmi więc: przeliczenia wymagają DWIE liczby — baza
348 i jedna z dwóch liczb 6.D180 — a żadna z rodzin liczonych po TREŚCI literału nie
wymaga go wcale.**

Dlaczego rodziny nie drgnęły, choć wyszły z zepsutego czytnika:

- Z bazy **odchodzą cztery** pozycje i **dochodzą trzy**, stąd 348 → 347.
- Para `[ARGUMENT]` odchodzi **urwana** i wraca **w całości** — prefiks ma taki sam,
  więc rodzina prefiksów liczy ją tak samo przed i po.
- Dwa ogony `, KnownArguments)}` i `, KnownViews)}` nie mają kształtu identyfikatora
  ani polskiego znaku, więc nie były liczone w żadnej z czterech rodzin.
- Napis surowy dochodzi do bazy jako **jeden** literał i też nie wpada w żadną z nich.
- Dwa literały z dziur — `" --"` i `", "` — nie mają ani jednej litery, więc przez
  sito „czy to słowo" nie przechodzą i bazy nie ruszają.

To jest wynik **przeciwny** do tego, czego pozycja się obawiała („baza 348 zawiera
literały ucięte, więc każda rodzina licząca po TREŚCI mogła policzyć fragment zamiast
całości"). Obawa była uzasadniona — ucięte literały w bazie rzeczywiście stały — ale
**zmierzona odpowiedź jest taka, że rodziny tego nie dotknęło**, i to dlatego pozycja
kazała zmierzyć, a nie przeliczyć na wyczucie.

**Czego ten pomiar NIE mówi:** że rodziny były policzone dobrze. Mówi tylko, że
**ten** defekt ich nie przesunął.

### 4.1. Znalezione po drodze: liczba plików w akapicie o skali była nieprawdziwa

Akapit przy `CzlonyKeyNames` mówił „**348** literałów w **21** plikach". Plików
zgłaszających jest **16**; 21 to wielkość korpusu, nie liczba plików ze zgłoszeniem.
Poprawione razem z liczbą 348, bo to ten sam akapit i ten sam pomiar.

Liczba „**22** stoją w `throw`" **zostaje bez zmian i to też jest sprawdzone, a nie
przyjęte**: żadna z siedmiu pozycji, które wchodzą albo wychodzą, nie stoi w `throw` —
para `[ARGUMENT]` idzie przez `Refusal(…)`, a napis surowy przez `string.Create(…)`.

### 4.2. 6.D180 zostaje otwarte, a jego różnica zwęża się o jeden z trzynastu

Kusiło, żeby ogłosić, że ten defekt tłumaczy 6.D180 — bo rozcinany napis surowy ma
czterdzieści wierszy, a 6.D180 jest właśnie o różnicy między liczeniem całym plikiem
a wiersz po wierszu. **Pomiar tego nie potwierdza.** Różnica była `105` vs `118`,
czyli trzynaście, a jest `106` vs `118`, czyli **dwanaście**. Napis surowy odpowiada
za **jeden** z trzynastu i pozostałych dwunastu nie tłumaczy.

Liczba `118` nie drgnęła, bo przy liczeniu wiersz po wierszu napis wielowierszowy
rozcina **sam podział na wiersze**, niezależnie od czytnika.

## 5. Kontrole negatywne — sześć, wszystkie czerwone

Baza: **240/240**. Każda kontrola zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | `Literaly` z powrotem na stary wzorzec | **238/240** — 2 czerwone |
| KN-2 | bez pomijania literału znakowego | **239/240** — 1 czerwony |
| KN-3 | napis surowy czytany jak zwykły | **238/240** — 2 czerwone |
| KN-4 | literały z dziur interpolacji niezbierane | **237/240** — 3 czerwone |
| KN-5 | bez podwojonego cudzysłowu w napisie dosłownym | **239/240** — 1 czerwony |
| KN-6 | bez pomijania komentarza wierszowego | **239/240** — 1 czerwony |

**KN-5 za pierwszym razem wyszła ZIELONA i nie znaczyła nic** — podstawienie nie
zastosowało się przez cytowanie w powłoce, więc przebieg zmierzył plik niezmieniony.
Wyszło to na `diff` z kopią roboczą, robionym po każdym podstawieniu właśnie na taką
okazję. Zapisane tutaj, bo zielona kontrola, której podstawienie nie weszło, wygląda
**dokładnie** jak zielona kontrola, której mechanizm nie działa.

KN-4 jest tu najciekawsza: zapala też `Ocena_ryzyka_kolizji_jest_mierzona_na_korpusie_bramki`,
czyli test, który o dziurach interpolacji nie mówi ani słowa — bo przybiła liczbę
literałów korpusu, a ta bez literałów z dziur jest inna.

## 6. Kontrola na wejściu SYNTETYCZNYM — bo drzewo nie ma dwóch z czterech konstrukcji

Napisu dosłownego `@"…"` i literału znakowego z cudzysłowem `src/Game/` nie ma dziś
**ani razu**. Bramka na samym drzewie nie odróżniłaby więc czytnika, który je umie, od
czytnika, który ich nie umie — ta sama pułapka co 6.D147 KN-6 i 6.D148 KN-4. Dlatego
`Czytnik_literalow_czyta_leksykalnie_a_nie_wzorcem` pyta o **pięć** wejść syntetycznych
i przy każdym o **dwie** rzeczy: co zwraca czytnik dzisiejszy i co na tym samym wejściu
zwracał stary. Bez drugiej połowy test byłby zielony także po przywróceniu wzorca.

Obok stoi `Korpus_niesie_konstrukcje_ktorych_stary_czytnik_nie_czytal` — na prawdziwym
drzewie, z komunikatem mówiącym wprost, że **zero** rozbieżnych plików znaczy „korpus
przestał nieść konstrukcję, dla której ten czytnik powstał", a nie „jest dobrze".

## 7. Co ZOSTAŁO NIETKNIĘTE i dlaczego

- **`KodBezKomentarzy` zostaje na miejscu, choć czytnik pomija komentarze sam.**
  Wołany jest w **dziesięciu** miejscach i jest obcinaczem **wierszowym**: usuwa każdy
  wiersz zaczynający się od `//`, także
  gdyby taki wiersz stał w środku napisu wielowierszowego. Dziś w `src/Game/` takiego
  wiersza nie ma, więc nic to nie psuje — ale jest to druga usterka tej samej rodziny
  i zdjęcie jej razem z pierwszą zmieniłoby dwie rzeczy naraz. Wpisane do kolejki.
- **Liczby rodzin z 6.D154…6.D179 zostają w swoich wpisach niezmienione** — pomiar
  z §4 mówi, że zmiany nie wymagają.
- **Bramek poza `Literaly` nie ruszałem.** `SlowaWKodzie`, `BezDziur`, `Jednostki`,
  `SciezkaWezla` są takie same co do znaku.
