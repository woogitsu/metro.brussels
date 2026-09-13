# 6.D199 — jedno wywołanie, dwa korpusy i postać, której ten skan nie widzi

**13.09.2026**, na `da3c3bd`. Wejście: `src/Game/` (wszystkie pliki poza `.godot/`),
`tests/Game.Tests/UiTextTests.cs` (`PominNieNapis`, `CzytajLiteral`,
`NazwyOTypieWyliczeniowym`, `ZrodlaGry`), `reports/6d185-nazwy-czlonow-na-ekranie.md` §10,
`reports/6d182-uciete-literaly.md`.

## 1. Trzy liczby, o które pytało pole „Wyjście"

| pytanie | odpowiedź |
|---|---|
| wywołań `.ToString()` bez argumentu, czytanych **leksykalnie** | **1** |
| z tego na wartości typu wyliczeniowego | **1** |
| z tego na drodze **na ekran** | **1** |

Jedynym wywołaniem jest `FirstRun.cs:1812` — ramię domyślne `Faza`, `phase` typu
`DoorPhase`. Do **logu** nie idzie ani jedno, do **telemetrii** ani jedno.

Droga jest więc nazwana dla wszystkich wywołań na wyliczeniu, bo jest jedno, i brzmi
**EKRAN**. To zarazem jedyna droga, na której angielski identyfikator jest tekstem dla
gracza, a nie danymi dla maszyny — czyli ta, której pole „Trzy drogi wyniku" tej pozycji
kazało szukać.

## 2. Szum to 67 %, nie 50 % — i różnicę robi KORPUS, nie drzewo

Pozycja pisała o **dwóch** trafieniach regeksu, z czego jednym w komentarzu, i budowała
na tym argument: *„na dwóch trafieniach 50 % szumu nie da się nazwać rozkładem"*.

Zmierzone:

```
src/Game/ CAŁE (pole „Wejście”):                     plikow 22, surowo 3, leksykalnie 1, szum 2 (67 %)
ZrodlaGry() — bez katalogu tekstów (korpus 6.D185):  plikow 21, surowo 2, leksykalnie 1, szum 1 (50 %)
```

**Obie liczby są prawdziwe i opisują dwa różne korpusy — wymienione w dwóch różnych
polach TEJ SAMEJ pozycji.** Pole „Skąd" liczyło po `ZrodlaGry()`, które **umyślnie**
pomija katalog tekstów `src/Game/UI/UiText.cs`; pole „Wejście" mówi „`src/Game/` (wszystkie pliki
poza `.godot/`)", czyli razem z katalogiem. Trzecie zgłoszenie to komentarz wierszowy
w `UI/UiText.cs:97`, stojący tam od 6.D99 (`e5c499e`) — nie doszedł po napisaniu pozycji,
tylko nigdy nie był w tamtym korpusie.

Nie jest to zarzut wobec 6.D185: `ZrodlaGry()` pomija katalog tekstów celowo i słusznie,
bo katalog jest tym, co bramka porównuje, a nie tym, co skanuje. Jest to natomiast
dokładnie ten kształt, przed którym pozycja ostrzegała: **statystyka szumu zmienia się
o 17 punktów w zależności od tego, które z dwóch pól czytelnik weźmie za korpus** —
i nie da się tego zobaczyć, dopóki nie policzy się obu.

**Czytanie leksykalne zostawia na obu korpusach TO SAMO jedno wywołanie.** Odporność na
wybór korpusu ma więc czytnik, a nie regeks.

## 3. Postać, której ten skan NIE WIDZI, jest dwanaście razy liczniejsza

`.ToString(coś)` — z argumentem — stoi w `src/Game/` **12 razy**, czyli dwanaście razy
częściej niż postać badana przez tę pozycję. **Żadne z tych dwunastu nie stoi na
wyliczeniu**: wszystkie na liczbach (`double`), formatowanych `CultureInfo.InvariantCulture`
(`DwellRemainingSeconds`, `StopErrorM`, `DistanceM`, `WindowM`, `command.Brake`,
`chainageM`, `axisLengthM`, `toStationM`, `throttle`, `brake`).

**Zero z ostatniego zdania jest przybite osobną stałą i to nie jest ozdoba.** Wartość
wyliczenia przekazana do `.ToString(kultura)` daje dokładnie ten sam angielski
identyfikator, co `.ToString()` — a skan z tej pozycji przechodzi obok niej, bo pyta
o nawias pusty. KN-6b mierzy to wprost: dołożenie takiego wywołania zapala bramkę
**dopiero przez to zero**, nie przez żadną z liczb wyżej.

## 4. Liczbę 12 przybiłem najpierw jako 13 i bramka to złapała w pierwszym przebiegu

Przy pisaniu stałej policzyłem pozycje wypisane przez pomiar w Pythonie **z głowy**
i wyszło mi trzynaście. Pierwszy przebieg `dotnet test`:

```
Assert.AreEqual failed. Expected:<13>. Actual:<12>. wywołań `.ToString(arg)` jest 12, a zmierzono 13: …
```

Jest to ta sama rodzina, co reguła „nie ufaj liczbie zapisanej w komentarzu — zmierz ją",
tyle że po mojej stronie: **liczba przepisana z wypisu, a nie wzięta z wypisu**, jest
liczbą zmyśloną, choćby pochodziła z prawdziwego pomiaru sprzed trzech minut.

## 5. Siedem kontroli negatywnych, baza 267/267

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | drugie `.ToString()` na wyliczeniu — **nie kompilowało się** (zła przestrzeń nazw) | — |
| KN-1b | to samo, z `MetroBxl.Sim.Train.DoorPhase` | 266/267 |
| KN-2 | czytnik leksykalny nie pomija komentarzy | **265/267** |
| KN-3 | czytnik leksykalny nie pomija literałów | 266/267 |
| KN-4 | wypełnianie `'\n'` zamiast `' '` | **267/267 ZIELONA** |
| KN-4b | czytnik zmienia DŁUGOŚĆ tekstu | 266/267 |
| KN-5 | korpus pomija `FirstRun.cs` (kontrola przyrządu) | 266/267 |
| KN-6 | wyliczenie trafia do `.ToString(kultura)` | 266/267 (na LICZBIE) |
| KN-6b | to samo przy podniesionej liczbie — jedna zmienna | 266/267 (na ZERZE) |

`md5sum -c` na obu plikach po każdej kontroli: `OK`.

**KN-3 zapala WYŁĄCZNIE kontrolę na wejściu syntetycznym, a liczby korpusowe zostawia
nietknięte — i to jest poprawne, nie przeoczone.** W `src/Game/` nie ma dziś ani jednego
`.ToString()` wewnątrz literału napisowego: trzy zgłoszenia regeksu to kod, komentarz
dokumentacyjny i komentarz wierszowy. Gałąź pomijająca literały jest więc na dzisiejszym
drzewie **bezczynna**, a jedyne, co ją ćwiczy, to wejście syntetyczne — rodzina 6.D159
i dokładnie powód, dla którego to wejście tu stoi.

**KN-4 wyszła ZIELONA i sprawdziłem, dlaczego.** Podstawienie zamieniało znak wypełnienia
ze spacji na `'\n'`, a oba są **jednoznakowe** — długość tekstu się nie zmienia, więc
asercja na długości nie ma czego zobaczyć. Kontrola mierzyła nie tę zmienną, którą miała
(ten sam błąd, co KN-5 przy 6.D191). KN-4b zmienia długość naprawdę i zapala. Przy okazji
wyszło coś, co zapisuję wprost: **asercja na długości pilnuje własności, której dzisiejsze
komunikaty tej bramki NIE UŻYWAJĄ** — zgłoszenia są w postaci `plik:nazwa`, bez numeru
wiersza. Zostaje, bo pomiar w §1 numery wierszy podaje i bez niej byłyby ciche; ale jest
to zapadka na przyszłość, nie na dziś, i lepiej, żeby to stało napisane, niż żeby ktoś ją
kiedyś zdjął jako „nikomu niepotrzebną".

## 6. Czego świadomie nie zrobiłem

- **Bramki na sam skan `.ToString()` nie postawiłem przed pomiarem** — pole „Poza
  zakresem" zabrania tego wprost. Bramka, którą dokładam, jest **po** pomiarze i niesie
  wszystkie cztery liczby razem z relacją między dwiema z nich.
- **Zachowania HUD-u nie zmieniałem**, `src/Sim/` nie ruszałem.
- **Korpusu `ZrodlaGry()` nie poprawiałem.** Pomija katalog tekstów celowo; zmiana
  ruszyłaby bramki 6.D185 i 6.D99, a ta pozycja o to nie prosiła.

## 7. Zauważone po drodze, nie tknięte

- **`src/Sim/` ma trzy `.ToString()` bez argumentu** (`FixedBlockSystem.cs:521`,
  `DriverKeys.cs:85`, `InputLog.cs:321`) i **żadne nie stoi na wyliczeniu** — wszystkie
  na napisach i na `NoneCode`. Rdzeń jest więc pod tym kątem czysty, ale nikt tego nie
  pilnuje, a `CLAUDE.md` §4.9 nie daje mu HUD-u, więc nowy przypadek byłby widoczny
  dopiero w telemetrii.
- **Dwie z dwunastu pozycji `.ToString(arg)` czytnik zwraca jako `.StopErrorM`** — z
  kropką na początku i bez nazwy obiektu. Wzorzec `([\w.]+)` łapie tu koniec wyrażenia
  przeniesionego do następnego wiersza. Klasyfikacji to nie zmienia (`double` zostaje
  `double`), ale **nazwa w komunikacie bramki jest urwana** i przy szukaniu miejsca
  trzeba by wrócić do pliku.
