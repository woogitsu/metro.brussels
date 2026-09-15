# 6.D213 — trzy wywołania, zero na wyliczeniu i pięć nazw, których sito nie widzi

**15.09.2026**, na `0393f9e`. Wejście: `src/Sim/**/*.cs`,
`tests/Game.Tests/UiTextTests.cs` (`KodLeksykalnie`, `WzorzecToStringBezArgumentu`,
`NazwyOTypieWyliczeniowym`), `tests/Sim.Tests/`,
`reports/6d199-jedno-wywolanie-dwa-korpusy-i-postac-ktorej-skan-nie-widzi.md` §7.

## 1. Trzy wywołania, te same trzy wiersze, trzeci dzień z rzędu

| miejsce | cel | co to jest | droga wyniku |
|---|---|---|---|
| `FixedBlockSystem.cs:521` | `text` | `StringBuilder` w `StateDigest()` | **odcisk stanu** — czyta go `DeterminismTests` |
| `DriverKeys.cs:85` | `NoneCode` | `const char NoneCode = '-'` | **plik zapisu wejścia** przez `Code()` |
| `InputLog.cs:321` | `text` | `StringBuilder` w serializatorze | **plik zapisu wejścia**, porównywany `cmp` |

**Na wartości typu wyliczeniowego: ZERO.** Liczby z pola „Skąd" (13.09) i przeliczenia
6.D208 (14.09) trzymają się co do numeru wiersza po raz trzeci.

Czytanie surowe i leksykalne dają dziś **tę samą trójkę** — w rdzeniu nie ma dziś
`.ToString()` w komentarzu ani w literale, więc różnica, którą 6.D199 zmierzyło dla
gry (4 surowo wobec 1 po masce), tu wynosi zero. Zapisane, bo cisza przyrządu i cisza
drzewa wyglądają tak samo.

## 2. Rozstrzygnięcie formy: ANI równość na trzech, ANI gołe sito po nazwie

Pole „Czego NIE wolno przyjąć bez pomiaru" pytało o formę zapadki. Odpowiedź wyszła
z **trzech podstawień**, nie z namysłu.

**Równość na trzech odpada** i to było w polu przewidziane: wszystkie trzy wywołania
stoją na `StringBuilder` albo `char`, są zachowaniem normalnym i przybywa ich razem
z kodem. Została **podłoga** — nie po to, żeby pilnować liczby, tylko żeby zero
znaczyło „czytnik przestał czytać", a nie „rdzeń czysty".

**Gołe sito po nazwie też odpada, i to jest zmierzone:**

| podstawienie | gołe sito | sito zawężone |
|---|---|---|
| `string status` + `status.ToString()` — **kod poprawny** | **TRAFIENIE FAŁSZYWE** | cisza |
| `DoorPhase faza` + `faza.ToString()` — usterka | trafienie | trafienie |
| `ParameterStatus status` + `.ToString()` — usterka na nazwie dwuznacznej | trafienie | **cisza** |

Bramka świecąca na kodzie poprawnym zostaje wyłączona, nie poprawiona (6.D27) — więc
gołego sita nie ma. Stoi **sito zawężone do nazw JEDNOZNACZNYCH**: 19 z 24.

## 3. Cena zawężenia: pięć nazw wypisanych Z NAZWY

`Reason`, `expected`, `phase`, `status`, `variant` — nazwy, które w `src/Sim/` noszą
typ wyliczeniowy **i jakiś inny** (`string`, `var`). Sito ich nie ogląda, więc
`.ToString()` na wartości wyliczenia nazwanej `phase` **przejdzie bez śladu**.

Zbiór stoi **wypisany, a nie policzony** (6.D131): liczba rosłaby razem z ślepą plamką
i jej podniesienie byłoby cichym poszerzeniem plamki; nazwa tego nie pozwala.

To te same nazwy, które 6.D197 wskazało dla `src/Game/` — `ProtectionMode.cs:33`
i `ParameterStatus.cs:32` biorą `string status`. **Zjawisko powtarza się w rdzeniu
co do nazwy**, a nie tylko co do rodzaju.

## 4. Gdzie stoi bramka i dlaczego NIE w `tests/Sim.Tests/`

Pole „Weryfikacja" mówiło `dotnet test tests/Sim.Tests`. Bramka stoi w
`tests/Game.Tests/UiTextTests.cs` i **to jest odstępstwo, wykonane po sprawdzeniu, a nie
z wygody**: `tests/Sim.Tests/` nie ma żadnego czytnika leksykalnego — sprawdzone
grepem po całym katalogu — a bramka na `.ToString()` bez maskowania komentarzy i
literałów mierzyłaby co innego. Napisanie tam własnego czytnika dałoby **trzecią
kopię** tego samego kodu, czyli dokładnie to, co ta pozycja przy okazji usunęła
(sekcja 6). Bramka siedzi więc obok `KodLeksykalnie` i obok swojej siostry z 6.D199,
która pyta o to samo dla `src/Game/`.

Weryfikacja brzmi zatem `dotnet test tests/Game.Tests`, a `dotnet test tests/Sim.Tests`
zostaje zielone i niezmienione.

## 5. Kontrole negatywne

Baza: **309/309** w `Game.Tests`, **662/662** w `Sim.Tests`.
Po każdej `md5sum -c` na dwóch plikach: `OK`.

| | podstawienie w `src/Sim/Train/DoorCycle.cs` | czerwonych testów |
|---|---|---:|
| KN-1 | `.ToString()` na `DoorPhase faza` — nazwa jednoznaczna | **1** |
| KN-2 | `.ToString()` na `string opis` — **kod poprawny** | **0** |
| KN-3 | `.ToString()` na `DoorPhase phase` — nazwa **dwuznaczna** | **0** |
| KN-4 | sito oślepione (nie rozpoznaje typu wyliczeniowego) | **2** |

**KN-1 i KN-2 to para, o którą prosiło pole „Weryfikacja"** — „wywołanie na wartości
wyliczenia **zapala**, a na napisie — nie". Zapala i nie zapala.

**KN-3 jest ważniejsza od obu.** Wykonuje ślepą plamkę na prawdziwym drzewie
i prawdziwym wyliczeniu: to samo wywołanie, co w KN-1, tylko zmienna nazywa się
`phase` zamiast `faza` — i bramka milczy. Granica jest **wykonana**, a nie opisana.

Pełne przebiegi: `dotnet test tests/Game.Tests` — **309/309**, `dotnet test tests/Sim.Tests` — **662/662**, `python3 tools/tests/test_all.py` — **2485/2485**.

## 6. Znalezione przy okazji i naprawione: mój własny duplikat czytnika

6.D212 dopisało do `UiTextTests.cs` metodę `Zamaskowany`, składającą `PominNieNapis`,
`PrefiksLiteralu` i `CzytajLiteral` — i opisało ją zdaniem „maska nie jest nowym
czytnikiem". **Była nim.** `KodLeksykalnie` z 6.D199 robi dokładnie to samo, w tym
samym pliku, od trzech dni.

Zmierzone przed usunięciem: oba czytniki dają wynik **identyczny znak w znak na każdym
pliku `src/`**. Kopia poszła, `WyliczeniaZTekstu` woła czytnik, który był pierwszy,
a `Game.Tests` przechodzi bez zmian. Docstring przy `WyliczeniaZrodel` jest przepisany,
a nie dopisany obok: mówi teraz, że pierwsza wersja BYŁA drugą kopią.

## 7. Dwie pomyłki własnej kontroli przyrządu, obie złapane przed werdyktem

1. **Próbki syntetyczne nosiły nazwy `faza` i `status`**, czyli takie, jakie KN-1
   dokłada do drzewa. Skutek: KN-1 zapalała **dwa** testy zamiast jednego, bo kontrola
   przyrządu liczyła trafienie z drzewa razem ze swoim. Nazwy zmienione na `probaFaza`
   i `probaNapis`.
2. **Kontrola zwracała SUMĘ trafień, a nie PRZYROST.** Po poprawce (1) problem został:
   próbka „kod poprawny" żądała pustej listy, a dostawała trafienie z drzewa dołożone
   przez KN-1. Kontrola liczy teraz różnicę wobec bazy.

**Trzecia próbka jest wyjątkiem i to jest wybór:** bierze nazwę Z LISTY nazw
dwuznacznych, bo ślepa plamka jest własnością zbioru nazw w `src/Sim/` — nazwa
wymyślona na miejscu nie byłaby dwuznaczna i sito **zobaczyłoby** ją, czyli próbka
mierzyłaby co innego.

## 8. Czego świadomie nie zrobiłem

- **Nie zmieniłem żadnego z trzech wywołań** — pole „Poza zakresem" tego zabrania,
  a wszystkie trzy są poprawne.
- **Nie tknąłem `src/Game/`** (6.D199, domknięte) ani postaci `.ToString(argument)`.
- **Nie naprawiłem ślepej plamki.** Dałoby się ją zamknąć rozbiorem składni C# albo
  odczytem typu z kompilatora — obie drogi są większe niż ta pozycja i obie wymagają
  decyzji o zależności, której `CLAUDE.md` §8 nie pozwala podjąć samemu.

## 9. Zauważone, nie tknięte

- **Sito po nazwie ma w rdzeniu 5 nazw dwuznacznych na 24**, czyli **jedną piątą**.
  Dla `src/Game/` 6.D197 podało „myli się na POŁOWIE trafień" — rdzeń jest pod tym
  względem czystszy, ale rząd wielkości ten sam.
- **`DriverKeys.NoneCode` to `const char`, nie wyliczenie**, i to jedyne z trzech
  wywołań, które stoi na wartości, a nie na `StringBuilder`. Gdyby kiedyś stał się
  wyliczeniem, wywołanie zmieniłoby klasę bez zmiany wiersza — bramka by to złapała,
  bo `NoneCode` jest nazwą jednoznaczną.
- `NazwyWyliczeniowychWRdzeniu` czyta deklaracje wzorcem, nie parserem, więc nie widzi
  `var` z wnioskowanym typem wyliczeniowym; ile takich jest, nie liczyłem.
