# 6.D255 — liczba wpisana w komunikat asercji nie jest pilnowana przez nic

**Data:** 17.09.2026 · **Gałąź:** `claude/6d255-twierdzenia-w-komunikatach` · **Baza:** `3ba3020`

## 1. Pytanie i dlaczego jest trudne

Twierdzenia liczbowe w `reports/` pilnuje `claims_in_reports()`, w `README.md` —
`test_readme_claims.py`. **Komunikatów asercji pod `tools/tests/` nie czytał ani jeden
czytnik**, choć są to zdania pisane w tym samym trybie i starzejące się z tej samej
przyczyny: kod obok nich rośnie, a proza zostaje. Pozycja żąda dwóch liczb — ile ich
jest i ile jest nieprawdziwych — oraz rozstrzygnięcia, czy da się je objąć bramką.

## 2. Pożyczki czytnika NIE DA SIĘ zrobić, i to jest pomiar, nie wygoda

6.D213 każe pożyczyć czytnik zamiast pisać drugą kopię, więc pierwsze podejście było
takie. Wzorzec `CLAIM` szuka nazwy stałej w grawisach, po której stoi liczba.
Puszczony na wszystkie komunikaty asercji:

```
trafien ksztaltu TWIERDZENIA w komunikatach: 2
ROZJAZDOW: 2
    ('test_backlog.py:1514', 'MINIMUM_READY_ITEMS', '-00', '12')
    ('test_suite_runtime_budget.py:2347', 'MIERZALNOSC_MIN', '4', '1.168')
```

**Oba trafienia są artefaktem specyfikatora formatu** — `%d.` dało „-00", a `%.4f`
dało „4" — a same komunikaty są liczone z kodu, czyli akurat wzorowe. Kształt
`` `NAZWA` … liczba `` w komunikatach praktycznie nie występuje. Pożyczka jest więc
wykluczona **pomiarem**.

## 3. Pierwsza liczba: ile ich jest

```
komunikatow asercji z napisem: 2668
literalow liczbowych (po zdjeciu specyfikatorow %): 418
komunikatow z takim literalem: 234
```

Klasyfikacja wszystkich 418 — każdy literał obejrzany w źródle razem z kontekstem:

| kategoria | co to jest |
|---|---|
| `odsyłacz` | numer dokumentu, sekcji, pozycji, PR-a (`docs/01-`, `§8`, `#86`, `MB-00`, `T-311`) |
| `historia` | datowany łańcuch dawnych wartości zapadki |
| `próg w kodzie` | ta sama liczba stoi w warunku asercji albo w ciele testu |
| `TWIERDZENIE O DRZEWIE` | liczba wpisana z ręki o dzisiejszym stanie repozytorium |
| `inne` | artefakt ekstrakcji, cytat powłoki, fakt o cudzym narzędziu |

## 4. Druga liczba: cztery nieprawdziwe

**Dziewiętnaście** literałów to twierdzenia o dzisiejszym drzewie. **Cztery były
nieprawdziwe**; trzy sprawdziłem osobiście, czwarte odczytałem z danych:

```
asercje_napisowe()                → 925      komunikat mówił 849
sekcje_zauwazone() po rozszerzeniu → 39       komunikat mówił 32
RunPlanTests.cs: [TestMethod]      → 61       komunikat mówił „27 testow"
tests/Game.Tests: [TestMethod]     → 318
data/track/L1_A.json: length_m     → 6686.35  komunikat mówi „realne 6700"
```

**Pierwsze z nich jest najgorsze i to nie jest hiperbola.** W `test_assertion_gate.py`
liczba 849 stoi w komunikacie asercji, a kilkanaście wierszy niżej — w docstringu:

> **Liczba 849 jest strażnikiem listy, a nie ozdobą** … tego pilnuje właśnie równość
> na 849.

Równość stoi dziś na **925**. Zdanie ogłasza samo siebie pilnowanym i nie jest.

**Piąte zdanie, które wyglądało na nieprawdę, nią nie jest** i warto to zapisać:
`test_report_claims.py` mówi „remis to 26 twierdzeń ze 101", a dziś jest 18 z 86 —
ale zdanie niesie datę („zmierzone 15.09.2026"), więc zgodnie z 6.D108 jest zdaniem
o dniu pomiaru. Liczby agenta przyjąłem, werdykt odrzuciłem.

## 5. Rozstrzygnięcie: bramka TAK, i oto jej cena

Sito: literał ma pokrycie, gdy stoi w warunku asercji, albo w ciele testu dwadzieścia
wierszy nad nią (także w innej skali — 2 cm ↔ `0.02`), albo tuż za znakiem odsyłacza,
albo gdy komunikat niesie datę.

```
literalow: 418
zdjete przez sito: 374
bez pokrycia: 44 wystapienia w 41 parach (plik, liczba)
```

Czterdzieści jeden wpisów wyjątków to cena. Płacę ją, bo **trzy z czterech dzisiejszych
nieprawd sito łapie**, a lista jest porównywana z drzewem **w obie strony**, więc nie
może rosnąć po cichu (6.D243). Trzy nieprawdziwe komunikaty poprawiono tym samym
commitem: liczba jest teraz podstawiana z kodu albo znika, bo nie była treścią zdania.

**Czwartej nie złapie żadna bramka na liczbach i to jest zmierzona granica, nie
przeoczenie.** „6700 m, czyli na realnej długości pakietu A" — liczba 6700 stoi
w samym warunku asercji jako podstawa arytmetyki zmiennoprzecinkowej i jest tam
**poprawna**; nieprawdziwy jest przymiotnik „realnej". Bramka licząca liczby widzi
liczbę, a nie zdanie.

## 6. Sito samo raz skłamało

W pierwszej wersji okno „dwadzieścia wierszy nad asercją" obejmowało też **wiersz samej
asercji**, więc liczba z komunikatu pokrywała SAMĄ SIEBIE. Sito zostawiało **34** zamiast
44 i wyglądało na skuteczniejsze, niż jest. Złapała to **kontrola przyrządu na wejściu
syntetycznym**, przy pierwszym przebiegu modułu — nie oko.

Drugi błąd w tym samym miejscu: zamiana przecinków na kropki w oknie psuła dopasowanie
`0.02` w `[(0.02, 0)]`, bo po liczbie stawała kropka i granica słowa przestawała
zachodzić. Też złapany kontrolą syntetyczną. Oba zostają opisane w module.

## 7. Kontrole negatywne — przewidywania spisane PRZED przebiegami

| kontrola | przewidziane | zmierzone |
|---|---|---|
| KN-A liczba bez pokrycia dopisana do cudzego komunikatu | czerwone, z parą `(plik, 4242)` | `[(('test_conflict_markers.py', '4242'), 239)]`, **1/3** |
| KN-B zdjęcie jednego wpisu z `WYJATKI` | czerwone, gałąź „nowe" | `[(('test_lod.py', '0,5'), 836)]`, **1/3** |
| KN-C wpis o parze, której w drzewie nie ma | czerwone, gałąź „zniknięte" | para wskazująca plik, którego w drzewie nie ma, **1/3** |
| KN-D kontrola przyrządu, pięć kształtów syntetycznych | sito zdejmuje cztery, zostawia jeden | zielone |

KN-D nie jest ozdobna: **to ona złapała oba błędy sita z §6.** Bez niej sito
wychodziło zielone i zostawiało mniej winnych, niż powinno — czyli meldowało
sprawdzenie, którego nie zrobiło (6.D27).

## 8. Czego NIE zrobiono

- **Nie poprawiono zdania o „realnej długości 6700 m"** — to zmiana prozy, której
  ta bramka nie obejmie, a pole „Poza zakresem" pozycji zabrania przepisywania
  komunikatów, których pomiar nie obejmuje. Stoi w §5 jako nazwana granica.
- **Nie poszerzono `claims_in_reports()`** na `tools/tests/` — 6.D230 pokazało, że
  granica czytnika jest rozstrzygnięciem, a §2 pokazuje, że tu pożyczka nie działa.
- **Nie tknięto 101 literałów datowanej historii** w `test_tree_walks.py` — to
  poprawnie oznaczone zdania o dniu pomiaru.

## 9. Co zauważone przy okazji, nietknięte

- **Ten sam kształt usterki żyje w KOMENTARZACH, których ta bramka nie czyta.**
  `test_mutation_sweep.py:2492` mówi „dałoby 2346 zamiast 63", a dziś `targets()` daje
  **71** i `collect()` **2586** — sprawdzone. Komentarz nie jest komunikatem asercji,
  więc nie wchodzi w zasięg; objęcie komentarzy to osobna pozycja i osobny koszt.
- **Scratchpad sesji jest współdzielony między agentami.** Jeden z przebiegów zapisał
  plik pomiarowy pod nazwą, którą zajął już inny agent, i wypis pokazał cudze dane
  w cudzym formacie. Złapało się to tylko dlatego, że format się nie zgadzał — przy
  zgodnym kształcie wyjścia pomiar poszedłby na cudzym zakresie bez śladu. Ten sam
  kształt co pułapka bajtkodu z §5 `CLAUDE.md`: narzędzie milczy i wychodzi zielono.
- **`MIN_SEKCJI_ZAUWAZONE` i sąsiednie podłogi** stoją przy komentarzu z pomiaru
  `e1c63f7` (201 sekcji w 197 raportach), a dziś jest 215 w 211 — komentarz przy
  stałej starzeje się tak samo jak komunikat, i też nie pilnuje go nic.
