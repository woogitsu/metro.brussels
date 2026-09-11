# 6.D130 — bramka odrzucała z dwóch powodów i mówiła o obu jednym zdaniem

**Zmierzone 11.09.2026 na:** `0b5c8c4`, kontener tej sesji.
**Przyrząd:** `tests/Game.Tests/UiTextTests.cs` (`SlowaWKodzie`, `NazwyKlawiszy`,
`NazwyKlawiszySilnika`, `PowodOdrzucenia`), `Godot.Key`, `src/Game/Input/KeyNames.cs`.

---

## 1. Rozróżnienie DA SIĘ zrobić i nie potrzeba do niego listy słów

Pole „Wyjście" dopuszczało dwa wyjścia: dwa rozróżnione powody **albo** pomiar
pokazujący, że bez listy słów rozróżnić się ich nie da. Rozróżnić się da, bo silnik
ma własne wyliczenie nazw klawiszy:

| pomiar | wartość |
|---|---|
| nazw w `Godot.Key` | **193** |
| `Escape` jest nazwą | **tak** |
| `Esc` jest nazwą | **nie** |
| nazw z polskim znakiem diakrytycznym | **0** |
| literałów w `src/Game/` | **948** (746 różnych) |
| z nich będących nazwą klawisza | **6**: `Escape`, `F1`, `F2`, `Forward`, `Right`, `Up` |

`Godot.Key` nie jest listą słów: jest **wyliczeniem silnika**, rośnie razem z Godotem,
a nie razem z tekstem interfejsu, i ani jedna z jego 193 nazw nie niesie polskiego
znaku. Sześć kolizji w całym `src/Game/` to nazwy klawiszy i kierunków, żadna nie jest
tekstem dla człowieka.

## 2. Dwa zdania zamiast jednego

```
"Prędkość" (literał językowy zamiast klucza katalogu)
"Escape"   (nazwa klawisza silnika spoza `NazwyKlawiszy`)
```

Obie bramki literałów — HUD, metody `FirstRun` i pliki sterowania — składają komunikat
przez wspólne `ZPowodami`, więc rozróżnienie jest jedno na wszystkie trzy, a nie trzy
kopie tej samej reguły.

## 3. Objawu z wpisu NIE DA SIĘ DZIŚ ODTWORZYĆ, i to jest wynik tej pozycji

Wpis mówił: „podmiana `"Esc"` na `"Escape"` zapala
`W_plikach_sterowania_nie_ma_ani_jednego_slowa`". **Zmierzone dziś: nie zapala.**
KN-1 wykonała dokładnie tę podmianę w `KeyNames.cs` i padły **trzy** testy, ale
**żaden z nich nie jest bramką literałów** — wszystkie trzy są pinami z 6.D116
(`KeyNames` kontra wiersz pomocy) i mówią o tym, o czym mają mówić:

```
Assert.AreEqual failed. Expected:<Esc>. Actual:<Escape>.
  klawisz o kodzie fizycznym 4194305 (Escape) nazywa się 'Escape',
  a wiersz pomocy ma mówić 'Esc'
```

Powód jest prosty i wart zapisania: **`"Esc"` przeprowadził się**. Bramka literałów
skanuje `DriverActions.cs` i `EmergencyBrake.cs`, a od 6.D116 ten napis mieszka
w `KeyNames.cs`, którego nie skanuje nikt. Objaw z 11.09.2026 był prawdziwy wtedy,
gdy napis stał w pliku skanowanym.

Usterka komunikatu **jest jednak nadal osiągalna** i to pokazują KN-1b i KN-1c:
literał wstawiony do pliku sterowania daje dziś właściwe zdanie, jedno albo drugie.

## 4. Kontrola, która wyszła ZIELONA: `NazwyKlawiszy` nie robi dziś nic

**KN-4** zdjęła `"Esc"` z `NazwyKlawiszy` — jedynego wpisu tej listy. Wynik:
**233/233, zielono**.

Wyjaśnienie jest to samo co w §3: `grep -rn '"Esc"' src/Game/` daje **dwa** trafienia
i oba są w `KeyNames.cs` — jedno w dokumentacji, jedno w słowniku. W żadnym z czterech
plików, które bramki literałów skanują (`DriverActions.cs`, `EmergencyBrake.cs`,
`Hud.cs`, `FirstRun.cs`), tego napisu **nie ma**.

`NazwyKlawiszy` jest więc dziś **wyjątkiem bez zastosowania**: mechanizm stoi, ale nic
go nie potrzebuje. Nie tykam go — pole „Poza zakresem" wyklucza zmianę zawartości tej
listy wprost — ale zapisuję, bo wyjątek, którego zdjęcie niczego nie zmienia, jest
zdaniem o kodzie, które ktoś przeczyta i uzna za prawdziwe.

## 5. Kontrole negatywne — WYKONANE, nie opisane

Baza `tests/Game.Tests`: **233/233** (było 231).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | `"Esc"` → `"Escape"` w `KeyNames.cs` (objaw z wpisu) | **230/233**, ale **nie** bramka literałów — patrz §3 |
| KN-1b | nazwa klawisza silnika wstawiona do `DriverActions.cs` | **czerwona**, zdanie „nazwa klawisza silnika spoza `NazwyKlawiszy`" |
| KN-1c | polskie słowo wstawione do `DriverActions.cs` | **czerwona**, zdanie „literał językowy zamiast klucza katalogu" |
| KN-2 | `PowodOdrzucenia` zawsze mówi o polszczyźnie | **232/233** |
| KN-3 | zbiór nazw wpisany z ręki (jedna pozycja) | **232/233** |
| KN-4 | `"Esc"` zdjęte z `NazwyKlawiszy` | **233/233 ZIELONA** — patrz §4 |

Po każdej: `md5sum -c` → `OK` na plikach odłożonych na bok.

KN-1b i KN-1c są parą i dopiero razem dowodzą tezy pozycji: **to samo miejsce**, dwa
różne wejścia, dwa różne zdania — na prawdziwej bramce i prawdziwym pliku, nie na
wejściu syntetycznym.

## 6. Zapadka igieł podniesiona z zapisanym powodem

`MAX_GAME_UNMATCHED_NEEDLES`, podniesiona z 21 na **24**. Trzy nowe igły są z założenia bez dopasowania
w komunikatach `src/Game`, bo nie są komunikatami programu: `Escape` to wejście
syntetyczne (a dopasowanie go do drzewa znaczyłoby, że bramka literałów jest czerwona),
a `literał językowy` i `nazwa klawisza silnika` to człony komunikatu **samego testu**.

Trzymania igieł w zmiennej nie użyto, choć ominęłoby zapadkę — z tego samego powodu,
który ten moduł zapisał przy podniesieniu 19 → 21: to zamiana niejednoznaczności na
niewidzialność, przed którą trzeci szczebel ma bronić.

## 7. Czego nie zrobiłem

* **Nie zmieniłem zawartości `NazwyKlawiszy`** i nie przeniosłem niczego do katalogu
  tekstów — oba wprost w „Poza zakresem".
* **Nie dopisałem `KeyNames.cs` do plików skanowanych** przez bramkę literałów. Byłoby
  to dziś zielone (`"Esc"` jest w `NazwyKlawiszy`), ale rozszerza ZAKRES bramki, a ta
  pozycja jest o jej KOMUNIKATACH. Stoi to jako obserwacja w §3 i §4.
* **Nie wzmocniłem odsiania o resztę sześciu kolizji** (`F1`, `F2`, `Forward`, `Right`,
  `Up`): żadna z nich nie jest dziś odrzucana, więc nie ma czego poprawiać, a reguła
  pisana pod nieistniejący przypadek jest regułą bez pomiaru.
