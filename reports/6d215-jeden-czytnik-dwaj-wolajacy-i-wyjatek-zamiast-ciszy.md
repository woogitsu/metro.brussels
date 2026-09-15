# 6.D215 — jeden czytnik, dwaj wołający i wyjątek zamiast ciszy

**15.09.2026**, na `18c320d`. Wejście: `tools/tests/csharp_test_methods.py`
(`_koniec_literalu` po naprawie 6.D200), `tests/Game.Tests/UiTextTests.cs`
(`PrefiksLiteralu`, `CzytajLiteral`, `Literaly`, `KodLeksykalnie`),
`tools/tests/test_csharp_test_methods.py` (`POSTACIE_LITERALU`),
`reports/6d200-potrojny-cudzyslow-po-malpie-i-szesnascie-metod.md` §7.

## 1. Czytników z tą gałęzią jest JEDEN — potwierdzone, nie przyjęte

Pole „Skąd" mówiło o trzech, a przeliczenie 6.D208 sprowadziło je do jednego. Ta pozycja
to **sprawdziła**, a nie przepisała: warunek `cudzyslowow >= 3` stoi w kodzie
`UiTextTests.cs` **raz**, w `CzytajLiteral`. `Literaly` i `KodLeksykalnie` są jego
**wołającymi**, nie czytnikami; `maska` po stronie Pythona gałęzi nie ma od 6.D200.

Odpowiedź na pytanie „jedna poprawka czy trzy" brzmi więc: **jedna**.

## 2. Co połykali wołający — zmierzone PRZED poprawką, na wejściu syntetycznym

Drzewo tych czytników na tej gałęzi nie ćwiczy (zapis werbatim z potrójnym cudzysłowem
stoi w `tests/` i `src/` raz i to w komentarzu), więc dowodem może być tylko wejście
syntetyczne — tak jak przy 6.D200.

| próbka | `Literaly` | `KodLeksykalnie` |
|---|---|---|
| `@"""a"` — werbatim o treści `"a` | `a"; var y = 1;` — **wciągnięta reszta wiersza** | **`IndexOutOfRangeException`** |
| `@"a"""` — werbatim o treści `a"` | `a""` | poprawnie |
| `"""a"""` — literał surowy | `a` | poprawnie |
| `$@"""a"` — werbatim interpolowany | `a"; var y = 1;` — **reszta wiersza** | **`IndexOutOfRangeException`** |

## 3. I to jest POPRAWKA DO PRZYPUSZCZENIA, które postawiło tę pozycję

Pole „Dlaczego to nie jest «powtórz tę samą poprawkę trzy razy»" przewidywało, że przy
`KodLeksykalnie` awaria będzie najgorsza z trzech, bo „**zero zgłoszeń czyta się jako
czysto**".

**Zmierzone: nie czyta się jako czysto — czyta się jako wyjątek.** `KodLeksykalnie`
rzuca `IndexOutOfRangeException`, więc każda bramka, która go woła — skan `.ToString()`
z 6.D199, bramka rdzenia z 6.D213, bramka urwań z 6.D214 — **przewróciłaby się głośno**,
a nie zamilkła. Cichy jest za to `Literaly`: zwraca literał, który połknął kod, i nic
o tym nie mówi.

Kolejność „najgorszy przypadek" z pola jest więc **odwrócona**, i to jest ten rodzaj
różnicy, dla którego projekt każe mierzyć zamiast wnioskować.

## 4. Poprawka: jeden warunek, w jednym miejscu

```csharp
var surowy = cudzyslowow >= 3 && !doslowny;
```

`doslowny` stało dwa wiersze wyżej od 6.D182 i było gotowe — brakowało go tylko w tym
jednym warunku. Po poprawce wszystkie cztery postacie czytają się poprawnie i żadna nie
rzuca.

## 5. Kontrole negatywne

Baza: **313/313** w `Game.Tests`, **662/662** w `Sim.Tests`, **2485/2485** w zestawie.
Po każdej `md5sum -c`: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | gałąź cofnięta (`>= 3` bez `&& !doslowny`) | **2 czerwone** |
| KN-2 | warunek odwrócony (`&& doslowny`) | **5 czerwonych** — psuje też trzy bramki 6.D182/6.D199 |
| KN-3 | druga KOPIA warunku dołożona do pliku | **1 czerwony** — bramka „jedno miejsce" widzi kopię |
| KN-4 | jedna z czterech postaci skreślona z tabeli | **ZIELONE** — luka mojej bramki |
| KN-4b | to samo, po przybiciu ZBIORU przedrostków | **czerwone** |

**KN-4 jest tą, która zmieniła bramkę.** Pętla po tabeli wykonuje się poprawnie także
wtedy, gdy tabela ma trzy wiersze zamiast czterech — asercja „tyle obrotów, ile wierszy"
nie broni więc niczego. Dopiero **zbiór przedrostków** (`@"`, `@"""`, `"""`, `$@"""`)
mówi, KTÓRE cztery, bo każdy odpowiada innej gałęzi czytnika. To 6.D131 raz jeszcze:
zbiór, nie liczba.

Pełne przebiegi: `dotnet test tests/Game.Tests` — **313/313**, `dotnet test tests/Sim.Tests` — **662/662**, `python3 tools/tests/test_all.py` — **2485/2485**.

## 6. Dwie pomyłki własnej bramki, obie złapane przed werdyktem

1. **Długości masek liczyłem z ręki** i dwie z czterech były o jeden znak za długie.
   Wzięte z pomiaru, nie z liczenia w głowie.
2. **Liczyłem wystąpienia warunku w CAŁYM pliku** i dostałem cztery zamiast jednego —
   bo łapałem **własne komunikaty** tej bramki. Liczone jest teraz po kodzie
   zamaskowanym przez `KodLeksykalnie`, czyli czytnik, o który ta pozycja pyta, służy
   do zadania pytania o samego siebie.

## 7. Czego świadomie nie zrobiłem

- **Nie tknąłem zapisów literałów w `tests/` ani `src/`** — pole tego zabraniało.
- **Nie ruszałem `_cialo_klasy`** ani korpusu żadnego czytnika.
- **Nie dopisałem warunku w `Literaly` ani `KodLeksykalnie`** — i to jest wynik, nie
  zaniechanie: nie mają własnej kopii, więc dopisanie byłoby martwym kodem, przed czym
  ostrzegało pole „Czego NIE wolno zrobić bez pomiaru".

## 8. Zauważone, nie tknięte

- **`Literaly` zwraca treść SUROWĄ, nie odkodowaną**: dla `@"a"""` daje `a""`, a nie
  `a"`. Dla bramek, które pytają o obecność słowa, to bez różnicy; dla bramki, która
  porównywałaby treść znak w znak, byłoby. Żadna dziś tego nie robi.
- **`PostacieLiteralu` w C# i `POSTACIE_LITERALU` w Pythonie opisują te same cztery
  zapisy, ale mają OSOBNE oczekiwania** — bo czytniki są różne. Nic nie pilnuje, żeby
  listy zapisów pozostały te same, a KN-4 zmierzyła, że pojedyncza utrata przechodzi
  na zielono. Wpisane jako **6.D226**.
