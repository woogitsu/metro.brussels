# 6.D178 — granica `throw` wytrzymuje zmianę heurystyki, granica wyjścia nie

**12.09.2026**, na `9d814d0`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/RunHeader.cs`, `src/Game/World/ChaseCameraAim.cs`, `src/Game/Input/KeyNames.cs`.
Pozycja pytała, czy granica „tablica jest tekstem, `throw` jest diagnostyką"
postawiona w 6.D143 dla `KeyNames.cs` uogólnia się na cały korpus.

## 1. Po wierszu wykrycie daje ZERO z 19 — nie „nieprecyzyjnie", tylko ślepo

```
razem=361  wierszem=0  instrukcja=19
```

**Ani jeden** komunikat wyjątku nie jest widoczny, gdy patrzeć na wiersz samego
literału. Powód jest prosty i jednoznaczny: w tym kodzie `throw new X(` stoi zawsze
w wierszu **przed** komunikatem. Pierwszy pomiar 6.D154 dał `wThrow=0` i była to
prawda o metodzie, nie o kodzie.

Kontrola żądana przez pole „Weryfikacja" — ten sam `throw` w jednym i w dwóch
wierszach:

| zapis | przypisanie do instrukcji | po wierszu |
|---|---|---|
| `throw new …("oś nie ma stacji");` | **True** | True |
| `throw new …(` + `"oś nie ma stacji");` | **True** | **False** |

Po wierszu werdykt zależy od tego, gdzie ktoś złamał linię. Przy przypisaniu do
instrukcji — nie zależy.

## 2. Rozkład dziewiętnastu

```
RunHeader.cs 9, ChaseCameraAim.cs 4, ChunkManifest.cs 1, StreamingPlan.cs 1,
KeyNames.cs 1, PlatformFit.cs 1, SceneAxis.cs 1, TrainView.cs 1
```

`KeyNames.cs = 1` to dokładnie ten trzeci literał, który 6.D143 zostawiło poza
zakresem, skanując **tablicę** zamiast pliku. Granica uogólniona objęłaby go tą samą
regułą — czyli potwierdza tamtą decyzję od drugiej strony.

## 3. Byłem o krok od obalenia 6.D174 i test odporności mnie zatrzymał

Dwa PR-y wcześniej zapisałem w 6.D174, że **miejsca użycia tą bramką zmierzyć się nie
da** — bo liczba szła od 12 do 77 zależnie od szerokości okna. Tu przypisanie do
instrukcji dało jedną liczbę: `wyjscie=51`. Wyglądało to na dowód, że tamten wniosek
był za mocny, a narzędzie istnieje.

Sprawdziłem odporność — to samo, czego zażądałem od metody okiennej:

| reguła kontynuacji | `throw` | wyjście |
|---|---:|---:|
| tylko `+` | **0** | 12 |
| `+` i `(` | **17** | 12 |
| `+`, `,`, `(`, `=` | **19** | **51** |

**Przypisanie do instrukcji to kolejne pokrętło**, nie rozwiązanie. Wyjście skacze
z 12 na 51 przy dołożeniu kontynuacji po przecinku — bo przecinek skleja sąsiednie
argumenty i elementy tablic, które z wypisem nie mają nic wspólnego. **Wniosek
z 6.D174 zostaje w mocy i zostaje z tego samego powodu**: arbitralność przesunęła się
z rozmiaru okna na kształt reguły, a nie zniknęła.

## 4. Ale `throw` zachowuje się inaczej niż wyjście — i to jest odpowiedź pozycji

Różnica między rodzinami jest zmierzona, nie odczuta:

- **wyjście: 12 kontra 51** — cztery razy więcej przy jednej zmianie reguły;
- **`throw`: 17 kontra 19** — dwa literały różnicy, czyli **10 %**.

Wariant „tylko `+`" daje dla `throw` zero i jest odrzucony nie gustem, tylko
składnią: `throw new X(` kończy się nawiasem, więc reguła bez kontynuacji po nawiasie
nie może przejść przez ten zapis **z definicji**.

Powód, dla którego `throw` jest odporniejszy, jest strukturalny: `throw new Wyjątek(…)`
to **ciasny, rozpoznawalny kształt składniowy** — słowo kluczowe, konstruktor, nawias.
Wypis to zwykłe wywołanie metody, nieodróżnialne kształtem od dowolnego innego.

**Granica z 6.D143 uogólnia się**, z zastrzeżeniem, którego nie wolno przemilczeć:
liczba wynosi **17–19**, a nie dokładnie 19, i dokładnej poda dopiero rozbiór składni.
Każdy sensowny wariant zgadza się natomiast co do rzeczy: komunikaty wyjątków istnieją,
jest ich kilkanaście, a metoda „po wierszu" widzi **zero**.

## 5. Czego nie zrobiłem

- **Nie wpisałem granicy do bramki.** Poza znanym już powodem (pliki, w których stoi
  te 19 literałów, są w większości poza zasięgiem sita — `RunHeader.cs`,
  `ChaseCameraAim.cs`, `ChunkManifest.cs` nie występują w `UiTextTests.cs`), doszedł
  drugi: **wpisana granica musiałaby wybrać jedną regułę kontynuacji**, a pomiar
  mówi, że wybór między 17 a 19 nie jest uzasadniony niczym poza wygodą.
- **Nie sięgnąłem po rozbiór składni C#** — to samo miejsce, w którym zatrzymało się
  6.D174: dodanie zależności i zmiana klasy narzędzia, czyli §8.
- **Nie policzyłem, ile z tych 19 to tekst po polsku** — 6.D175 podało 14 dla
  literałów z polskim znakiem i ta liczba pochodzi z tej samej heurystyki, więc
  dziedziczy jej niepewność. Nie mnożę jej przez nową.
