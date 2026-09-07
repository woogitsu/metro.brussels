# Stała C#, której nikt nie czyta (6.B31)

**Zmierzone 07.09.2026 na commicie:** `609591b80d5dc6d664598eb23fd19efd3b031d5d`
(gałąź `claude/6b31-martwe-stale-csharp`).

## 1. Wpis kolejki mylił się dwa razy, i oba razy pomiar to pokazał

**Raz co do katalogu.** 6.B29 wypisało brak w polu „czego nie zrobiono" jako
„nie tknięto zasięgu poza `tools/` i `src/` — `godot/`". Katalogu `godot/` w tym
repozytorium **nie ma**:

```
$ ls -d */
data/  docs/  reports/  src/  tests/  tools/
$ find . -name "*.tscn" -not -path "./.git/*"
./src/Game/Scenes/FirstRun.tscn
```

Scena Godota leży w `src/Game/`, czyli w drzewie, które bramka z 6.B29 **już
obchodzi** — tylko filtruje pliki po `.py`. Brak był realny, ale jest brakiem
**języka**, nie katalogu. Wpis 6.B31 powtórzył tę pomyłkę po raporcie, bo pisałem go
z tego samego przekonania.

**Dwa co do konwencji nazw.** Wpis mówił o stałych „o nazwie wielkimi literami" —
przeniesione z Pythona. C# w tym repozytorium pisze je **PascalCase**:

```
src/Game/DesignAssumptions.cs:35:    public const double CabEyeHeightM = 2.20;
tests/Game.Tests/RunHeaderTests.cs:39: private const double PlanLimitKmh = 72.0;
```

Kryterium na WIELKIE litery nie złapałoby **ani jednej** stałej C# w tym drzewie.
Bramka nie filtruje po kroju nazwy wcale.

## 2. Pomiar

```
[STALE C#] plikow .cs:                     124
[STALE C#] deklaracji const/static ro:     233
[STALE C#] roznych nazw:                   193
[STALE C#] nieczytanych nigdzie:             0
[STALE C#] z tego uzasadnionych:             0
```

Zero — **po** usunięciu jedynej, którą pomiar znalazł.

## 3. Jedna martwa stała, usunięta a nie usprawiedliwiona

```
tests/Game.Tests/RunHeaderTests.cs:42:
    /// <summary>Stacje osi syntetycznej; te same co w <c>LineCoreTests</c> rdzenia.</summary>
    private static readonly double[] StationChainagesM = { 0.0, 600.0, 1400.0, 2000.0 };
```

**Prywatne** pole klasy testowej, nieczytane przez nic — ani w `.cs`, ani w `.tscn`,
`.gd`, `*.sh`, `.github/`. Prywatne pole bez odczytu nie ma komu służyć: nic z zewnątrz
go nie widzi, nic z wewnątrz go nie czyta.

Usunięte, **nie** wpisane na listę uzasadnień, i różnica wobec 6.B29 jest tu istotna:
tam jedyna nieczytana stała (`LOCATION_STATION`) spisuje trzeci element wyliczenia
`location_type` z GTFS, więc jej usunięcie zepsułoby czytelność zbioru. Tu nie ma
zbioru — sąsiedzi (`UnknownArgument`, `BadArgumentValue`, `PlanLimitKmh`) są wszyscy
czytani. To była pozostałość, nie element.

Lista `UZASADNIONE` startuje więc **pusta**, i to jest mocniejsze niż start z wyjątkiem.

Oba zestawy C# po usunięciu:

```
$ dotnet test tests/Sim.Tests     Passed! - Failed: 0, Passed: 552, Total: 552
$ dotnet test tests/Game.Tests    Passed! - Failed: 0, Passed: 205, Total: 205
```

## 4. Kierunek pomyłki wybrany świadomie

Odczyt liczony jest jako wystąpienie identyfikatora **poza wierszem deklaracji**. Stała
o nazwie zbiegającej się z nazwą metody albo zmiennej gdzie indziej wyjdzie więc jako
**żywa, choć martwa** — to fałszywy negatyw. Wybrany, bo odwrotny błąd kazałby usunąć
coś, co działa, a bramka świecąca na poprawnym kodzie zostaje wyłączona, nie
poprawiona. Ta sama asymetria, co przy sprawdzaniu powłoki w 6.B29 i przy zwężeniu
wzorca w 6.D27.

Sprawdzone jest też to, czego po stronie C# nie da się zrobić przez `ast`: `.tscn`,
`.gd`, `*.sh` i `.github/`. Zmierzone: **zero** odczytów stamtąd — ale warunek
zostaje, bo jego brak zamieniłby jedno zapytanie w błędną diagnozę „martwa", gdy scena
czyta stałą po nazwie.

## 5. Wzorzec deklaracji: kształt sprawdzony, nie założony

Wzorzec wymaga inicjatora `=` w tym samym wierszu. Sprawdzone, czy to wystarcza:

```
$ grep -rnE "(static readonly|const)\s+[^ ]+\s+[A-Za-z_][A-Za-z0-9_]*\s*;" --include=*.cs src/ tests/
(bez trafień)
$ grep -rnE "(static readonly|const)\s+[^ ]+\s+[A-Za-z_][A-Za-z0-9_]*\s*$" --include=*.cs src/ tests/
(bez trafień)
```

**Wszystkie 233** deklaracje mają inicjator w wierszu — ani jedna nie kończy się
średnikiem bez `=`, ani jedna nie przenosi `=` do następnego wiersza. Gdyby ktoś taką
dopisał, bramka jej nie zobaczy; dlatego stoi próg `MINIMUM_DEKLARACJI`, a osobny test
pilnuje, że liczba widzianych deklaracji nie spada pod zmierzoną wartość. Bez tego
progu literówka we wzorcu dałaby zero deklaracji, zero martwych i **zieloną bramkę** —
ta sama pułapka, którą `MINIMUM_CLAIMS` zamyka w `test_report_claims.py`.

## 6. Pierwsza wersja bramki kosztowała 20,7 s i to było nie do przyjęcia

```
przed:  20.724 s  test_dead_constants_csharp.py  (5 testów)
po:      0.421 s  test_dead_constants_csharp.py  (5 testów)
```

Szła po **każdej** nazwie osobno przez wszystkie wiersze — 193 nazwy razy 124 pliki.
Dwadzieścia sekund to dwie trzecie tego, co 6.B30 właśnie zdjęło z **całego** zestawu
(105,3 s → 76,5 s); dokładanie tego z powrotem jedną bramką byłoby oddaniem tamtej
pracy. Jedno przejście po plikach z licznikiem identyfikatorów daje **ten sam wynik**
w ułamku czasu. Wynik sprawdzony po zmianie, nie założony: te same 233 deklaracje, te
same 193 nazwy, ta sama jedna martwa (przed usunięciem).

## 7. Kontrole negatywne — WYKONANE, cztery

```
KN-1  martwa stala dopisana do src/Game/DesignAssumptions.cs
      FAIL test_every_unread_csharp_constant_is_justified:
      ... MartwyProgTestowyM (src/Game/DesignAssumptions.cs)

KN-2  usunieta StationChainagesM przywrocona
      FAIL test_every_unread_csharp_constant_is_justified:
      ... StationChainagesM (tests/Game.Tests/RunHeaderTests.cs)

KN-3  wpis w UZASADNIONE bez martwej stalej
      FAIL test_no_justification_outlives_the_constant_it_describes: ... NieMaTakiej

KN-4  literowka we wzorcu deklaracji
      FAIL test_the_gate_sees_the_declarations_it_is_supposed_to_see:
      bramka widzi 0 deklaracji przy progu 200
      FAIL test_a_declaration_line_is_not_counted_as_a_read
```

**KN-2 jest warta osobnego zdania**: dowodzi, że bramka złapałaby stałą, którą
usunąłem w tym samym commicie — bez niej „usunąłem coś, co bramka i tak by
przepuściła" byłoby nierozstrzygalne. **KN-4** pokazuje, po co jest próg: bez niego
literówka we wzorcu dawałaby zieloną bramkę mierzącą zero.

Dwie dalsze kontrole nie są jednorazowe — są testami: że wiersz deklaracji nie liczy
się jako odczyt (inaczej każda stała czytałaby się sama) i że wzorzec czyta cztery
kształty **wzięte z tego repozytorium**, nie z podręcznika C#.

## 8. Weryfikacja

```
$ python3 tools/tests/test_all.py
  RAZEM 69.822 s, 1819 testów, 96 modułów
kod: 0
```

## 9. Czego świadomie nie zrobiono

- **Pól, właściwości, metod i klas nieużywanych** — pole „Poza zakresem". Wymagałoby
  rozstrzygnięcia, czym jest publiczne API typu.
- **Nie tknięto `enum`.** Nieużywany element wyliczenia to ten sam kształt, co
  `LOCATION_STATION` po stronie Pythona: element zbioru, który spisuje się w całości.
  Objęcie go tą bramką wymagałoby listy uzasadnień na starcie, a nie pustej.
- **Nie ruszono kroju nazw jako kryterium.** Bramka bierze każdą deklarację `const`
  i `static readonly`; filtr po PascalCase wykluczyłby stałe pisane inaczej, a takich
  w drzewie nie zmierzyłem.
