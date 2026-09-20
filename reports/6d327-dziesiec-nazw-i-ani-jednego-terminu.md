# 6.D327 · Dziesięć nazw stoi wyłącznie bez grawisów — i ANI JEDNA nie jest polskim terminem

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `cb77af0`

6.D317 §3.3 i §8 zmierzyło, że czternaście nazw z populacji to **polskie terminy**
pisane PascalCase — pojęcia wprowadzone przez ten projekt w prozie bramek, bez
odpowiednika w kodzie — i zapisało, że ile ich stoi **bez grawisów**, nie policzył
nikt. Ta pozycja liczy. **LICZY i niczego nie poprawia.**

Trzy liczby: **30 · 3 · 17**, a nazw stojących **wyłącznie bez grawisów** jest
**dziesięć**.

Wynik, dla którego warto było tę pozycję wziąć: **ani jedna z tych dziesięciu nie
jest polskim terminem tego projektu.** Są to nazwy własne (`GitHub` dwadzieścia
jeden razy, `CPython` dziesięć, `YouTube`) i nazwy składników C# cytowane z `src/`.
**Konwencja grawisu dla polskich terminów jest stosowana bez wyjątku** — wszystkie
sześć nazw, które pole wymienia z nazwy, stoi w grawisach.

---

## 1. Kontrola przyrządu — ZDANA, i to dla wszystkich sześciu nazw pola

Pole żąda, żeby `TylkoKod` wyszedł jako nazwa występująca **także** w grawisach.

```
   TylkoKod w grawisach: True | bez grawisow: False
```

Sprawdziłem przy okazji wszystkie sześć nazw, które pole wymienia:

```
   CzlonWyrazenia             bez grawisow=False w grawisach=True
   KodBezKomentarzy           bez grawisow=False w grawisach=True
   KorzenRepozytorium         bez grawisow=False w grawisach=True
   LiteralowWZasieguBramki    bez grawisow=False w grawisach=True
   PostacieLiteralu           bez grawisow=False w grawisach=True
   TylkoKod                   bez grawisow=False w grawisach=True
```

**Wszystkie sześć: w grawisach tak, bez grawisów nie.** Kontrola sprawdza tu
sześć razy więcej, niż żądało pole — i dopiero to szersze sprawdzenie złapało
usterkę mojego przyrządu, opisaną niżej.

## 2. USTERKA PRZYRZĄDU: mój kształt nie przechodził przez POLSKI PRZYIMEK

Pierwszy przebieg dał dla `LiteralowWZasieguBramki` **`w grawisach=False`** — a ta
nazwa stoi w prozie `tools/tests/test_csharp_pins.py` sześć razy, w grawisach.
Gdyby pole żądało kontroli tylko na `TylkoKod`, przeszłaby i usterka zostałaby
w przyrządzie.

Przyczyna jest w kształcie, który spisałem przed pomiarem:

```
PASCAL2 = \b(?:[A-Z][a-z0-9]+){2,}\b
```

Każdy człon musi mieć wielką literę **i co najmniej jedną małą**. Polskie złożenie
zawiera **jednoliterowe przyimki**: `LiteralowW·Zasiegu·Bramki`. Człon `W` nie ma
po sobie małej litery, więc wzorzec się na nim rozpada.

**Jest to usterka swoiście polska i dlatego nazywam ją wprost:** konwencja PascalCase
przeniesiona na polskie terminy produkuje człony jednoliterowe (`W`, `Z`, `I`),
których angielskie PascalCase prawie nie ma. Sito napisane dla nazw angielskich
odsiewa polskie terminy **systematycznie**, a nie przypadkiem.

Poprawka dopuszcza człon jednoliterowy **tylko wtedy, gdy następuje po nim kolejny
człon**, żeby wzorzec nie łapał akronimów (`README`, `CI`):

```
CZLON = (?:[A-Z][a-z0-9]+|[A-Z](?=[A-Z][a-z]))
```

Po poprawce: **28 → 30** nazw bez grawisów, a wszystkie sześć nazw pola wychodzi
w grawisach.

## 3. TRZY LICZBY, których żądało pole

```
=== TRZY LICZBY ===
  nazw PascalCase (>=2 czlony) BEZ grawisow:         30
  z nich stojacych WYLACZNIE na poczatku zdania:      3
  z pozostalych padajacych TAKZE w grawisach:        17
  => WYLACZNIE BEZ GRAWISOW:                         10
```

Populacja prozy: **14 778 węzłów** pod `tools/`, czytanych **pożyczonym** `proza`
z `test_message_claims.py`.

**Dwa warunki pola policzyłem osobno, bo pole tak kazało — i odsiewają całkiem
inaczej.** Wymóg dwóch członów przepuszcza 30 nazw z całej prozy; wymóg „pozycja
inna niż początek zdania" odsiewa z nich **trzy**, czyli jedną dziesiątą. Pole
ostrzegało, że polskie złożenie na początku zdania wygląda jak termin — przy wymogu
dwóch członów ta pułapka **prawie znika**, i to jest liczba, nie przypuszczenie.

## 4. ODPOWIEDŹ NA PYTANIE ZADANE WPROST: dziesięć — i ani jedna nie jest terminem

```
=== WYLACZNIE BEZ GRAWISOW (10) — lista imienna ===
   CPython                            x10   mutation_sweep.py
   CPythonie                          x1    mutation_sweep.py
   CoversChord                        x2    test_xml_doc_blocks.py
   GitHub                             x21   test_ci_workflows.py
   GitHuba                            x16   test_ci_workflows.py
   LineRun                            x1    test_xml_doc_blocks.py
   PointAt                            x1    test_validate_axis.py
   TracePoint                         x1    test_xml_doc_blocks.py
   TurnbackEnabled                    x1    test_xml_doc_blocks.py
   YouTube                            x1    test_audio_rights.py
```

Pole dopuszczało odpowiedź „żadna" i mówiło, co by znaczyła: konwencja grawisu
stosowana bez wyjątku. **Odpowiedź brzmi „dziesięć", ale dla klasy, o którą pole
pyta — polskich terminów — brzmi „żadna".** Dziesiątka dzieli się na dwie rodziny
i żadna nie jest terminem tego projektu:

- **Nazwy własne, pięć nazw i 49 wystąpień:** `GitHub` (21), `GitHuba` (16),
  `CPython` (10), `CPythonie`, `YouTube`. Grawis byłby tu błędem — to nie są
  identyfikatory, tylko nazwy firm i implementacji. **Dwie z nich są odmienione
  po polsku** (`GitHuba`, `CPythonie`), co żaden skan po kształcie nie rozpozna
  jako tej samej nazwy.
- **Nazwy składników C# z `src/`, pięć nazw i sześć wystąpień:** `CoversChord`,
  `LineRun`, `PointAt`, `TracePoint`, `TurnbackEnabled`. Te **powinny** stać
  w grawisach według konwencji — cztery z pięciu padają w jednym pliku,
  `test_xml_doc_blocks.py`.

**Wniosek jest mocniejszy niż liczba:** konwencja grawisu jest w tej prozie
stosowana konsekwentnie dla terminów i dla identyfikatorów projektu, a wyjątki
są albo poprawne (nazwy własne), albo skupione w jednym pliku.

## 5. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| Y1 | kontrola przyrządu przejdzie | trafione — ale dopiero po poprawce z §2 |
| Y2 | nazw bez grawisów będzie więcej niż 50 | **OBALONE** — 30 |
| Y3 | początek zdania odsieje mniej niż jedną czwartą | trafione — 3 z 30, czyli 10 % |
| Y4 | odpowiedź nie brzmi „żadna" | trafione co do litery (10), **obalone co do treści**: dla polskich terminów brzmi „żadna" |
| Y5 | wśród wyłącznie bez grawisów będą dominować nazwy angielskie | trafione — **wszystkie dziesięć** |
| Y6 | wymóg dwóch członów nie wystarczy | trafione **DWA RAZY**, §2 i §4 |

**Y6 trafione po raz dziesiąty z rzędu w tej sesji**, licząc od 6.D317 — ale tym
razem trafiło w dwóch miejscach naraz i oba są swoiście polskie: **człon
jednoliterowy** (przyimek w złożeniu) i **odmiana nazwy własnej** (`GitHuba`,
`CPythonie`). Żadnego z nich nie przewidziałem, mimo że przewidziałem, iż reguła
będzie niewyczerpująca.

**Y4 podaję jako trafione co do litery i obalone co do treści**, i to jest wybór,
a nie wykręt: pytanie pola brzmiało o nazwy PascalCase bez grawisów, i takich jest
dziesięć. Ale pole stoi w pozycji o **polskich terminach**, a tych wśród nich nie
ma ani jednego. Podanie samej dziesiątki byłoby odpowiedzią na pytanie literalne
przy przemilczeniu pytania rzeczywistego.

## 6. Czego świadomie nie zrobiono

- **Nie dopisano ani jednego grawisu** i nie poprawiono żadnego zdania prozy —
  pole zabrania wprost.
- **Nie postawiono bramki na terminach.** §4 pokazuje, dlaczego byłaby szkodliwa:
  zapalałaby się na `GitHub` i `YouTube`, gdzie grawis byłby błędem.
- **Nie zmieniono `docs/04-conventions.md`.**
- **Nie rozstrzygnięto, czy pięć nazw składników C# ma dostać grawisy** — to
  decyzja o konwencji, nie pomiar.
- **Nie policzono nazw jednoczłonowych** — pole żąda co najmniej dwóch i podaje
  powód.
- **Nie tknięto `src/` ani `data/`.**

## 7. Zauważone przy okazji, nietknięte

1. **Cztery z pięciu nazw składników C# bez grawisów stoją w jednym pliku,
   `tools/tests/test_xml_doc_blocks.py`.** Rozkład jest więc skupiony, a nie
   rozproszony — co przy dziesięciu wyjątkach na 14 778 węzłów prozy znaczy, że
   konwencji nie łamie zwyczaj, tylko jeden plik.
2. **`GitHub` pada dwadzieścia jeden razy, a `GitHuba` szesnaście.** Skan po
   kształcie widzi je jako dwie różne nazwy; każdy pomiar „ile razy pada nazwa X"
   w polskiej prozie rozbija się o odmianę, a żaden dotąd tego nie nazwał.
3. **Człon jednoliterowy jest kształtem swoiście polskim** (§2). Każdy wzorzec
   PascalCase napisany dla nazw angielskich odsiewa polskie terminy tego projektu
   systematycznie — a takich wzorców w `tools/tests/` jest więcej niż jeden.
