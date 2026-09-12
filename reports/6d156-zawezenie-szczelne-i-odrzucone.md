# 6.D156 — przyjęte zawężenie zabiera z klasy „nie wiem" cztery pozycje, odrzucone zabrałoby dwadzieścia pięć

**12.09.2026**, na `67e7bb8`. Wejście: `tools/tests/csharp_assertions.py`
(`klasa_komunikatu`, `RODZINA_Z_TOLERANCJA`), `tools/tests/test_csharp_assertions.py`
(`NIEROZSTRZYGNIETYCH`), `reports/6d145-komunikaty-asercji-csharp.md` §2.

Pozycja żądała: **liczby nierozstrzygniętych po zawężeniu, z podziałem na szczelne
i nieszczelne, oraz rozstrzygnięcia, które z nich wchodzi do kodu.** Pole „Dlaczego to
nie jest dopisanie reguły" ostrzegało: *zastosowanie obu zamieniłoby zadeklarowaną
niewiedzę na cichą heurystykę — a to jest gorsze od niewiedzy.*

## 1. Pomiar — kodem bramki, i odtwarza 72 co do jedynki

Skan chodził przez `csharp_assertions.klasa_komunikatu`, `WYWOLANIE`
i `argumenty_z_nawiasami` — czyli przez sam przyrząd, bez reimplementacji.
Odtwarza `NIEROZSTRZYGNIETYCH = 72` dokładnie, więc mierzy to, co bramka.

| pierwszy argument nierozstrzygniętej | ile |
|---|---|
| literał **napisowy** | **4** |
| literał **całkowity** | **25** |
| literał zmiennoprzecinkowy | 0 |
| cokolwiek innego | 43 |

**Liczba odrzuconego zawężenia wynosi 25, a nie 26.** Wpis pozycji mówił 26; drzewo
od 11.09.2026 się zmieniło. Różnica jest o jeden i nic nie przewraca, ale zapisana
jest jako pomiar dzisiejszy, nie jako przepisana liczba wczorajsza.

## 2. ROZSTRZYGNIĘCIE: wchodzi zawężenie po literale NAPISOWYM, nie wchodzi po CAŁKOWITYM

### 2.1. Napisowe jest WYKLUCZENIEM, nie prawdopodobieństwem

`Assert.AreEqual(double, double, double)` żąda, żeby **oba** porównywane były
zmiennoprzecinkowe. **Napis do `double` nie konwertuje się w C# nigdy** — więc gdy
pierwszy argument jest napisem, to przeciążenie nie może się związać, a trzeci
argument jest komunikatem. Nie ma tu zgadywania: jest wykluczenie.

### 2.2. Całkowite jest NIESZCZELNE i dlatego zostaje odrzucone

`int` konwertuje się do `double` bez zarzutu, więc przy `Assert.AreEqual(0, x, coś)`
przeciążenie z tolerancją **wiązać się może**. O tym, które wybrał kompilator,
rozstrzyga **typ trzeciego argumentu** — czyli dokładnie to, czego czytnik nie wie.
Zawężenie po literale całkowitym byłoby więc heurystyką: trafiałoby prawie zawsze
i milczałoby o tym, że trafia.

**Kuszące było je przyjąć: zabrałoby SZEŚĆ RAZY więcej pozycji niż to przyjęte.**
Właśnie ta dysproporcja jest powodem, dla którego obie liczby stoją przybite
w bramce — inaczej rozstrzygnięcie czytałoby się jak wybór bez kosztu.

### 2.3. Granica przebiega po `+`, a nie po „zaczyna się od cudzysłowu"

Wzorzec przepuszcza po literale **wyłącznie konkatenację albo koniec wyrażenia**:

| wyrażenie | typ | zawężone? |
|---|---|---|
| `"abc"` | `string` | **tak** |
| `"abc" + d` | `string` — w C# `string + cokolwiek` daje napis | **tak** |
| `"abc".Length` | `int` → konwertuje się do `double` | **nie** |
| `"abc"[0]` | `char` → konwertuje się do `double` | **nie** |

Gdyby wzorcem było samo `^[@$]*"` (tak wygląda istniejący `LITERAL_NAPISOWY`, używany
do OSTATNIEGO argumentu), `"abc".Length` przeszłoby jako napis i zawężenie przestałoby
być wykluczeniem. **KN-3 mierzy to wprost.**

## 3. Wzorzec jest ZACHOWAWCZY i to jest wybór

Ciało literału czyta prosto — tym samym kształtem, który 6.D182 wczoraj uznało za
niewystarczający dla C#. **Tu jest to bezpieczne, bo błąd idzie w jedną stronę:**
na napisie interpolowanym z zagnieżdżonym cudzysłowem wzorzec końca nie znajdzie,
nie dopasuje się, i asercja **zostanie w klasie „nie wiem"**. Fałszywy BRAK zawężenia
nie kosztuje nic; fałszywe zawężenie zamieniłoby zadeklarowaną niewiedzę na ciche
zgadywanie — czyli dokładnie to, przed czym ostrzegało pole „Dlaczego to nie jest
dopisanie reguły".

## 4. Wynik

```
{'bez': 1381, 'z': 1202, 'nierozstrzygniete': 68, 'razem': 2651}
```

- `NIEROZSTRZYGNIETYCH`, podniesione z 72 na **68**
- `Z_KOMUNIKATEM_RAZEM`, podniesione z 1198 na **1202**
- `ASERCJI_RAZEM` 2651 — bez zmian; trzy klasy nadal sumują się do całości, o co
  pole „Weryfikacja" prosiło wprost.

(Przecinek tuż po backticku jest tu **konieczny**, a nie stylistyczny: bramka roszczeń
czyta `` `STAŁA` 72 `` jako twierdzenie „stała wynosi 72" i zapala się na zapisie
„z 72 na 68". Pułapka z Issue #547 §6.6 — złapała mnie i tu jest obejście.)

Cztery zawężone asercje i ich trzecie argumenty — wszystkie są komunikatami, więc
zawężenie nie tylko jest szczelne, ale i trafia:

```
RunHeaderTests.cs          "classic_2026"          -> path
RunPlanTests.cs            "jakas/sciezka.json"    -> nazwa
ProvenanceSidecarTests.cs  "# polecenie: drive"    -> string.Join("\n", settings)
ProvenanceSidecarTests.cs  "# polecenie: " + cmd   -> string.Join("\n", settings)
```

Czwarta jest tu ciekawa: to **konkatenacja**, nie goły literał — czyli przypadek,
dla którego reguła z §2.3 w ogóle istnieje.

## 5. Kontrole negatywne — cztery, wszystkie czerwone

Baza: **18/18** w module. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`
na obu plikach.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | przyjęte TAKŻE zawężenie nieszczelne (literał całkowity) | **15/18** — 3 czerwone |
| KN-2 | zawężenie zdjęte całkiem | **15/18** — wraca 72 |
| KN-3 | wzorzec przepuszcza cokolwiek po literale (`^[@$]*"`) | **17/18** |
| KN-4 | wzorzec nie łapie NICZEGO | **14/18** — 4 czerwone |

**KN-1 jest tu najważniejsza**: pokazuje, że odrzucone zawężenie naprawdę działa
i naprawdę zabrałoby 25 pozycji (nierozstrzygniętych spada z 68 do 43). Odrzucenie
nie jest więc odrzuceniem czegoś bezczynnego.

**KN-4 istnieje, bo bez niej dwie bramki byłyby zielone z niczego.** Gdyby wzorzec nie
łapał NICZEGO, zdanie „żadna nierozstrzygnięta nie ma napisu w pierwszym argumencie"
byłoby prawdą pustą. `test_zawezenie_naprawde_cos_zabralo_z_klasy_nie_wiem` liczy
zawężone **niezależnie od** `klasa_komunikatu` i zapala się na zerze — i zapaliła się
dokładnie tym komunikatem.

**KN-2 NIE zapala tej bramki i tak ma być**: zdejmuje UŻYCIE wzorca, a nie wzorzec.
Bramka bezczynności mierzy wzorzec, więc jej werdykt się nie zmienia — co jest
poprawne, a nie przeoczone.

## 6. Po drodze: polski cudzysłów zamykający w literale Pythona

Komunikat asercji zawierał `„nie wiem"` z cudzysłowem ASCII i **zakończył napis
Pythona w środku zdania** — `SyntaxError: unterminated string literal`. Pułapka jest
wypisana w przekazaniu pracy (Issue #547 §6.5) i mimo to weszła; zapisuję ją tutaj,
bo złapał ją dopiero import modułu, a nie oko. Poprawne jest `”` (U+201D).

## 7. Czego świadomie nie zrobiłem

- **Nie dopisałem ani jednego komunikatu do asercji C#** i **nie ruszyłem zapadki
  `BEZ_KOMUNIKATU`** — pole „Poza zakresem" zabrania obu.
- **Nie zawęziłem 43 pozostałych** („cokolwiek innego" w pierwszym argumencie).
  Dla nich pierwszy argument jest identyfikatorem albo wywołaniem, więc jego typu nie
  widać bez sprawdzacza typów — ta sama granica, co w 6.D141 i 6.D145.
- **Nie poprawiłem `LITERAL_NAPISOWY`** (ten od OSTATNIEGO argumentu), choć wzorzec
  `^[@$]*"` ma teoretycznie tę samą dziurę co wariant odrzucony w §2.3: `"abc".Length`
  policzyłby jako komunikat. **Zmierzone: dziura kosztuje dziś ZERO.** Ostatnich
  argumentów, które zaczynają się cudzysłowem, a czystym literałem nie są, jest
  **cztery** — i wszystkie cztery to napisy interpolowane z zagnieżdżonym cudzysłowem:

  ```
  $"--signalling przeszło z {string.Join(" ", skryptowy)}"
  $"{limit.Variant}.{property.Name} = {value.ToString("R", CultureInfo.…)}"
  $"autorytet {system.Authority("A")} nie wyszedł za blok peronowy"
  $"na wybiegu przyspieszenie musi być ujemne, jest {forces.Acceleration…}"
  ```

  Wszystkie **są** napisami, więc `LITERAL_NAPISOWY` klasyfikuje je poprawnie — różnią
  się od mojego wzorca tylko dlatego, że mój jest ZACHOWAWCZY i ich nie domyka (§3).
  Ani jednego przypadku, w którym wzorzec myli się na niekorzyść, w drzewie nie ma.
  Nie zakładam osobnej pozycji na dziurę, której koszt zmierzyłem i wynosi zero —
  wpis o niej zostaje tutaj, żeby następny czytelnik nie musiał mierzyć drugi raz.
