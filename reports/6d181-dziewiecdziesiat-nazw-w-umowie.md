# 6.D181 — 90 nazw to umowa między programami, a dwie trzecie z nich to jedna rodzina z 6.D176

**12.09.2026**, na `baabfdd`. Wejście: `src/Game/FirstRun.cs`, `src/Game/RunPlan.cs`,
`tests/Game.Tests/UiTextTests.cs`, zrzut 90 zgłoszeń o kształcie identyfikatora
stojących poza kontekstem czytania JSON-a. Pozycja wyszła z 6.D173.

## 1. Podział po MIEJSCU UŻYCIA, nie po brzmieniu

| grupa | ile | po czym rozpoznana |
|---|---:|---|
| **argument wiersza poleceń** | **39** | `Argument(…)`, `arguments.ContainsKey(…)`, `TryDouble(arguments, …)`, `HasFlag(…)` |
| **lista nazw argumentów** | **21** | wiersz będący samą listą literałów |
| klucz JSON-a **wypisywanego** | **13** | `"nazwa":` w interpolowanym napisie |
| wartość trybu | 5 | `_mode = …`, `LineMode ? … : …` |
| stała z nazwami widoków | 4 | `KnownViews` |
| mapowanie nazwy widoku | 3 | `"chase" => ViewKind.Chase` |
| nazwa kolumny wejścia | 2 | `TryNumber(columns[7], …, "throttle", …)` |
| klucz wyniku | 1 | `_line!.Result("arrived")` |
| wartość API silnika | 1 | `DisplayServer.GetName() == "headless"` |
| wartość w JSON-ie | 1 | `"engine": "godot"` |

**Suma 90, w koszu „pozostałe" zero.** To było żądanie pola „Skończone, gdy".

## 2. Główny wynik: 60 z 90 to ta sama rodzina co 6.D176

Argumenty wiersza poleceń i ich listy dają **60 z 90**. Jest to **ta sama rodzina**,
którą 6.D154 wydzieliło jako „nazwa opcji CLI" i wpisało jako 6.D176 — tam było ich
**27**.

Podział na dwie pozycje wziął się z **przypadku ortograficznego**: 6.D154 rozpoznawało
tę rodzinę wzorcem `[a-z][a-z0-9]*(-[a-z0-9]+)+`, czyli **po myślniku**. Nazwy
dwuczłonowe (`sample-every`, `at-chainage`, `limit-kmh`) w niego wpadły; jednoczłonowe
(`axis`, `assets`, `manifest`, `shell`, `line`, `calls`, `shot`, `replay`) nie — i
wylądowały w rodzinie „identyfikator", a stamtąd w reszcie po 6.D173.

**Rzeczywista rodzina argumentów CLI liczy więc 87** (27 + 60), a nie 27. Podział
opisywał kształt zapisu, a nie rzecz. Wniosek wprost: **6.D176 i 6.D181 są jedną
pozycją** i tak należy je wziąć.

## 3. Drugi wynik: 6.D173 mierzyło tylko CZYTANIE JSON-a

Przy 6.D173 kontekst JSON-a został zmierzony jako `GetProperty`, `GetString`,
`RootElement` — czyli **wyłącznie odczyt**. Wyszło 18 ze 108.

Wśród tych 90 „poza kontekstem" stoi **13 kluczy JSON-a, który program WYPISUJE**:
`"engine":`, `"resolution":`, `"scene":`, `"vertices":`, `"faces":`, `"platforms":`,
`"slabs":`, `"train":`, `"bodies":`, `"last_shot":`. Ta sama rodzina, druga strona.

**Rodzina JSON-a liczy więc 31, nie 18.** Liczba z 6.D173 nie była błędna — mierzyła
to, co zadeklarowała — ale **deklaracja była węższa niż rodzina**, i sama tego nie
mówiła. Jest to ta sama usterka, którą projekt tropi od 6.D27, tylko po mojej stronie:
przyrząd melduje „kontekst JSON-a", a sprawdza połowę.

## 4. Żaden z 90 nie jest tekstem dla gracza

Każdy z nich jest **nazwą w umowie między programami**: argumentem wiersza poleceń,
kluczem JSON-a, nazwą widoku, kolumną wejścia albo wartością zwracaną przez API
silnika. Żaden nie dociera na ekran jako zdanie — i to jest zmierzone po miejscu
użycia, nie po brzmieniu, zgodnie z zakazem zgadywania z pola pozycji.

## 5. Granica istnieje i nie jest listą nazw

Dla największej grupy granica jest **zamkniętym zbiorem akcesorów**:
`Argument`, `HasFlag`, `arguments.ContainsKey`, `TryDouble(arguments, …)`.
To jest reguła o miejscu użycia, nie lista napisów — czyli dokładnie ten rodzaj
granicy, którego projekt żąda od 6.D130, i którego kształt napisu dać nie umiał
(6.D173: `stacja` i `streaming` nierozróżnialne).

Dla kluczy JSON-a granicą jest sąsiedztwo dwukropka w napisie interpolowanym —
**ale zmierzone jest to na 13 wystąpieniach i tylko w jedną stronę**; czy ten wzorzec
nie łapie niczego innego w korpusie, nie zostało sprawdzone i tu tego nie twierdzę.

## 6. Czego nie zrobiłem

- **Nie dodałem żadnego sita do bramki.** Pozycja miała ustalić, czym te napisy są;
  granica jest opisana, ale jej wpisanie to decyzja o zakresie bramki i należy do
  pozycji scalonej 6.D176+6.D181.
- **Nie scaliłem 6.D176 i 6.D181 w tabeli.** Zdanie „to jedna rodzina" jest wynikiem
  tej pozycji; scalenie wpisów zmienia kolejkę i jest do rozstrzygnięcia przez
  właściciela, a nie przy okazji.
- **Nie sprawdziłem wzorca kluczy JSON-a na całym korpusie** — patrz §5, mówię
  o tym wprost zamiast rozszerzać wniosek poza pomiar.
