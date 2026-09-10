# Predykat profilu pionowego: negacja jednej wartości zamiast białej listy (6.D80)

**Zmierzone 10.09.2026 na:** `0da6d61` + gałąź tej sesji, kontener sesji,
SDK 10.0.401.
**Przyrząd:** `dotnet test tests/Sim.Tests`, cztery kontrole negatywne
z `md5sum -c` po każdym powrocie.

---

## 1. Co było zepsute

```csharp
public bool IsVerticalModelled =>
    !string.Equals(VerticalStatus, "not_modelled", StringComparison.Ordinal);
```

Predykat był **prawdziwy dla wszystkiego poza jednym napisem**. Zmierzone 09.09.2026
sondą wołającą prawdziwy typ osi:

```
brak klucza vertical           IsVerticalModelled = True
status = unknown               IsVerticalModelled = True
status = nod_modelled          IsVerticalModelled = True    (literówka)
status = not_modelled          IsVerticalModelled = False
```

Trzy pierwsze wiersze to **trzy sposoby, na jakie plik osi może powiedzieć NIC** —
a predykat odpowiadał na nie „zamodelowany".

## 2. Dlaczego to nie jest dzisiejsza usterka liczbowa

Dziś z tego predykatu nie liczy się nic: jedynymi konsumentami są dwa testy, oba
oczekujące fałszu, a pochylenie wchodzi do fizyki jako **jawne zero** z komentarzem,
że to nie jest wybór. Szkoda jest **kontraktowa**: pierwszy konsument, który zaufa
predykatowi, policzy zerowe pochylenie jako **zmierzone**, a nie jako założenie —
czyli przekroczy granicę z `docs/21-measured-vs-assumed.md`.

## 3. Poprawka: biała lista, zamknięta i dziś pusta

```csharp
public static IReadOnlyList<string> ModelledVerticalStatuses { get; } =
    Array.Empty<string>();

public bool IsVerticalModelled => IsModelledStatus(VerticalStatus);
```

Dopisanie wartości do listy jest **oświadczeniem, że dla tego statusu profil naprawdę
jest w danych**, i ma iść razem z rzędnymi w plikach osi. Rzędnych główki szyny nie
ma dziś w żadnym z nich, więc lista jest pusta — i to jest stan rzeczy, nie ostrożność.

## 4. Kontrola, która wyszła ZIELONA, i co z niej wynikło

**KN-3 jest najważniejszym wynikiem tej pozycji.** Mutacja zastępująca całą pętlę po
liście przez `return false` przeszła **597/597, zielono**.

Powód jest ogólny i wart zapisania: **przy liście PUSTEJ predykat czytający listę
i predykat zwracający twarde `false` są dla testów nieodróżnialne.** Pusta biała lista
jest więc miejscem, w którym bardzo łatwo napisać bramkę pilnującą niczego — dokładnie
ta rodzina, którą projekt tropi od 6.D27.

Zamknięte przeciążką `IsModelledStatus(status, allowed)`, która pozwala sprawdzić
regułę na liście **niepustej**. Cztery asercje na syntetycznej liście
`{"surveyed", "modelled"}` — dwie na prawdę, jedna na fałsz spoza listy, jedna na
`Ordinal` (status pochodzi z pliku, nie od człowieka, więc równoważność wielkości
liter byłaby zgadywaniem). Po tej zmianie **ta sama mutacja wywraca test** (KN-3b).

## 5. Cztery kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | przywrócona negacja jednej wartości | **czerwona** 2/597 — oba nowe testy o „powiedzieć NIC" |
| KN-2 | `"not_modelled"` dopisany do białej listy | **czerwona** 3/597 — nowe testy i test o pustej liście |
| KN-3 | predykat przestaje czytać listę (`return false`) | **ZIELONA** 597/597 — patrz §4 |
| KN-3b | ta sama mutacja po dodaniu kontroli na liście niepustej | **czerwona** 1/597 |
| KN-4 | `Ordinal` poluzowany do `OrdinalIgnoreCase` | **czerwona** 1/597 |

KN-1 jest tą, której żąda pole „Skończone, gdy" („przywrócenie negacji jednej wartości
wywraca ten test"). KN-2 dowodzi, że lista jest **czytana**, a nie że wynik jest
zaszyty: dopisanie do niej `not_modelled` natychmiast ogłasza profil zamodelowanym
i trzy testy to widzą.

## 6. Czego NIE zrobiłem

**Nie dopisałem żadnego statusu do `data/`** — `CLAUDE.md` §4.1 i §4.6, i tak stoi
w polu „Poza zakresem". Pliki osi nie zostały tknięte ani odczytem, ani zapisem poza
istniejącym testem kontrolnym na `L1_A.json`.
**Nie wyprowadziłem pochylenia z osi** — rzędnych główki szyny nadal nie ma, a ta
pozycja tego nie zmienia i zmienić nie może.
**Nie tknąłem miejsca, w którym pochylenie wchodzi do fizyki jako zero.** Ono jest
dziś jawnie opisane jako założenie i takie zostaje; ta pozycja pilnuje wyłącznie tego,
żeby predykat nie zamienił go po cichu w pomiar.

## 7. Weryfikacja

```
dotnet test tests/Sim.Tests   (przed zmianą, git stash)
  -> Passed!  Failed: 0, Passed: 594, Total: 594

dotnet test tests/Sim.Tests   (po zmianie)
  -> Passed!  Failed: 0, Passed: 597, Total: 597

python3 tools/tests/test_all.py
  -> RAZEM 94,713 s, 2141 testów, 113 modułów, kod 0
```

Trzy nowe testy: oś bez klucza profilu, sześć wariantów statusu (w tym literówka
`nod_modelled` i `NOT_MODELLED`), oraz stan i czytelność samej białej listy.
