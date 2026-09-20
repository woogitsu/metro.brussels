# 6.D323 · Zero nazywa cokolwiek mimo krótkiego komunikatu — ale długość jest warunkiem KONIECZNYM, nie wystarczającym

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `894e6f2`

6.D311 §4 i §9 zapisało, że dwie pary z czterdziestu ośmiu mają zbiory nazw niepuste
i **równe**, a obie mają po stronie scalenia komunikat dłuższy niż `Scalenie #NNN:
tytuł`. Ta pozycja liczy, ile scaleń ma taki komunikat i czy pokrywa się to z tymi
dwiema. **LICZY kształt komunikatów, które już są w historii** — niczego nie
przepisuje i żadnej reguły pisania nie ustanawia.

Trzy liczby: **255 / 56 / 56**. A odpowiedź na pytanie, które pole kazało zadać
wprost — ile scaleń nazywa cokolwiek **mimo** komunikatu równego tytułowi — brzmi
**ZERO**.

Pole dopuszcza to zero i mówi, co wtedy znaczy: „długość komunikatu wystarcza do
przewidzenia obecności nazw". **Wystarcza w jedną stronę i to jest właściwy wynik:
z 255 komunikatów dłuższych niż tytuł nazwę niesie 56, a 199 nie niesie żadnej.**
Długość jest warunkiem **koniecznym**, nie wystarczającym — i różnica między tymi
dwoma zdaniami jest całą treścią tej pozycji.

---

## 1. Kontrola przyrządu — ZDANA dla obu commitów i w OBU klasach

Pole żąda, żeby scalenia `69a0c0b60e0f` i `d949439319e0` wyszły w klasie „komunikat
dłuższy niż tytuł" **i** w klasie „nazywa cokolwiek".

```
   69a0c0b60e0f  dluzszy=True  nazywa=True   nazwy=['test_mutation_sweep.py']
   d949439319e0  dluzszy=True  nazywa=True   nazwy=['MINIMUM_DETAIL_BLOCKS', 'MINIMUM_DOCUMENTED_ITEMS']
```

Obydwa, w obu klasach, za pierwszym przebiegiem. Kontrola pokazuje przy tym **co**
każde z nich nazywa — czyli sprawdza więcej niż przynależność do klasy.

## 2. TRZY LICZBY, których żądało pole

```
scalen w drzewie:                               336

  komunikat DLUZSZY niz pierwszy wiersz:        255
  NAZYWA cokolwiek (modul albo zapadke):         56
  PRZECIECIE (dluzszy I nazywa):                 56
  NAZYWA mimo komunikatu ROWNEGO tytulowi:        0
  dluzszy, a NIE nazywa niczego:                199
```

**Przecięcie równa się klasie „nazywa" co do jedynki — czyli `nazywa` ⊆ `dłuższy`,
zawieranie PEŁNE.** Nie jest to założenie ani zaokrąglenie: obie liczby wynoszą 56.

## 3. OSTRZEŻENIE POLA — potwierdzone w jedną stronę, obalone w drugą

Pole ostrzega, żeby nie brać „dłuższy niż tytuł" za „niesie nazwy", bo komunikat bywa
dłuższy o zdanie `CI: 10/10 zielone` albo o stopkę, w których nie pada żadna nazwa —
a bywa krótki i nazwę zawierać.

**Pierwsza połowa ostrzeżenia jest trafna i to mocno: 199 z 255 dłuższych komunikatów
nie nazywa NICZEGO, czyli 78 %.** Wzięcie długości za obecność nazw pomyliłoby się
w czterech przypadkach na pięć.

**Druga połowa jest zmierzona jako nietrafna: krótkich komunikatów niosących nazwę
jest ZERO.** Nie jest to niespodzianka po nazwaniu mechanizmu — `Scalenie #NNN: tytuł`
to jeden wiersz, a nazwa modułu albo zapadki w tytule scalenia nie pada nigdy, bo
tytuł streszcza pozycję słowami.

**Podaję obie połowy osobno, bo pole kazało policzyć je osobno**, i dokładnie dlatego
widać, że jedna trafiła, a druga nie. Zsumowanie ich do zdania „ostrzeżenie było
trafne" byłoby przemilczeniem połowy pomiaru.

## 4. Kontrola sita stopki — zero różnicy jest własnością DRZEWA, nie wzorca

Spisałem przed pomiarem, że stopkę (`Co-Authored-By`, `Claude-Session`, odsyłacz
sesji) odsiewam, bo inaczej „dłuższy" znaczyłoby „ma stopkę". Odczyt kontrolny ze
stopką wliczoną daje **tę samą liczbę 255, różnica zero**.

Zero z odsiewania bywa zerem wzorca, który nic nie złapał, więc sprawdziłem to
osobno:

```
KONTROLA SITA STOPKI: scalen ze stopka w komunikacie: 33 z 336
   z nich takich, gdzie stopka jest JEDYNA trescia poza tytulem: 0
```

**Sito widziało 33 scalenia i w żadnym stopka nie była jedyną treścią.** Zero różnicy
jest więc faktem o historii tego repozytorium, a nie o moim wyrażeniu regularnym.

## 5. Populacji 48 par z 6.D311 NIE ODTWARZAM i mówię, czego nie liczę

Pole wymienia „czterdzieści osiem par" jako wejście. Moja populacja to **336 scaleń
w drzewie**; kryterium „scalenie, którego druga gałąź też jest w drzewie" daje
**336**, czyli wszystkie — a nie 48.

Czterdzieści osiem par z 6.D311 było więc wybrane **innym kryterium** (obie połowy
w populacji „zgłasza kontrolę"), a nie samą strukturą rodziców. Różnicy **nie
uzgadniam** — to byłoby dobieranie definicji pod cudzą liczbę (lekcja 7, ten sam ruch
co przy 6.D317, 6.D318, 6.D319 i 6.D321). Pytanie pozycji brzmi „ile scaleń", więc
liczę scalenia i podaję kryterium jawnie.

**Przecięcie z dwiema parami z 6.D311, którego żądało pole, jest pełne:** obie są
w klasie „dłuższy" i w klasie „nazywa" (§1).

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| U1 | kontrola przyrządu przejdzie za pierwszym razem | trafione |
| U2 | „dłuższy niż tytuł" będzie MNIEJSZOŚCIĄ scaleń | **OBALONE** — 255 z 336, czyli 76 % |
| U3 | odsianie stopki zmieni liczbę o więcej niż połowę | **OBALONE** — zmieniło o zero |
| U4 | „nazywa mimo równego tytułowi" nie będzie zerem | **OBALONE** — jest zerem |
| U5 | przecięcie mniejsze niż każda z klas o co najmniej 10 % | **OBALONE** — równe jednej z nich co do jedynki |
| U6 | obie pary z 6.D311 znajdą się w przecięciu | trafione |

**Cztery pudła z sześciu, i wszystkie cztery w tę samą stronę: przeceniłem
nieuporządkowanie historii.** Spodziewałem się komunikatów krótkich z nazwami,
stopek podbijających licznik i przecięcia mniejszego od obu klas. Historia tego
repozytorium okazała się bardziej regularna, niż zakładałem: nazwy pojawiają się
wyłącznie tam, gdzie ktoś napisał treść, treść jest w trzech czwartych scaleń,
a stopka nigdy nie udaje treści.

**U4 zapisuję razem z warunkiem obalenia, który postawiłem przed pomiarem:** „jeśli
wyjdzie zero, znaczy to, że długość komunikatu wystarcza do przewidzenia obecności
nazw — i tak to zapisuję, zamiast szukać innego sita". Wyszło zero i tak to
zapisuję. **Ale zapisuję też drugą stronę, której warunek nie przewidywał:
wystarcza tylko w jedną stronę** (§3).

## 7. Czego świadomie nie zrobiono

- **Nie przepisano ani jednego komunikatu.**
- **Nie ustanowiono reguły pisania komunikatów scalenia** — pole nazywa to decyzją
  właściciela i `docs/04-conventions.md`.
- **Nie zmieniono `klasy_sladu` ani `DIFF_SCALENIA`.**
- **Nie uzgodniono populacji 336 z czterdziestoma ośmioma parami** (§5).
- **Nie policzono, czym są 199 komunikatów dłuższych, a nienazywających niczego** —
  pole pyta o liczby, nie o treść.
- **Nie tknięto `src/` ani `data/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Sto dziewięćdziesiąt dziewięć scaleń ma treść, która nie nazywa żadnego modułu
   ani zapadki.** Jest to trzy piąte wszystkich scaleń w drzewie. Czym ta treść jest,
   ta pozycja nie pyta — ale jest to największa klasa w całym pomiarze i każde
   pytanie o „co niosą komunikaty scaleń" trafi najpierw w nią.
2. **Nazwy niesie 56 scaleń z 336, czyli co szóste.** 6.D321 zmierzyło, że
   podstawienie komunikatu gałęzi za komunikat scalenia wprowadza do populacji
   123 scalenia — czyli ponad dwa razy więcej, niż dziś w ogóle cokolwiek nazywa.
3. **Stopka pada w 33 scaleniach z 336.** Jest to ślad po scaleniach squashem,
   które wciągnęły stopkę commita gałęzi; w pozostałych 303 komunikat scalenia
   powstał osobno.
