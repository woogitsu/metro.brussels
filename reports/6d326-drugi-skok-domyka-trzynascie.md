# 6.D326 · Drugi skok domyka TRZYNAŚCIE z czterystu dwudziestu ośmiu — bo reszta nie jest problemem łańcucha

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `1506524`

6.D315 §4 i §9 zmierzyło, że po skoku przez przypisanie w zasięgu klasa
`NIEROZSTRZYGNIETY` liczy 140 z 439 czytników, i zapisało, że **ile domknąłby drugi
skok, nie policzył nikt**. Ta pozycja liczy. **LICZY i żadnego czytnika nie
przepisuje.**

Trzy liczby na mojej populacji: **11 · 2 · 415**. Drugi skok domyka jedenaście,
trzeci dwa, a czterysta piętnaście nie domyka się nigdy.

Ale wynik, dla którego warto było tę pozycję wziąć, jest inny: **z 415, które nie
domykają się nigdy, tylko trzy są problemem ŁAŃCUCHA.** Pozostałe 412 to dwie
przyczyny, których długość łańcucha nie dotyczy wcale — i to znaczy, że pytanie
pola trafia w jedną trzydziestą tego, co klasę `NIEROZSTRZYGNIETY` naprawdę wypełnia.

---

## 1. Kontrola przyrządu — ZDANA

Pole żąda, żeby `pogrubione_bez_pokrycia` z `test_message_claims.py` domknęło się
**pierwszym** skokiem jako `LISTA`.

```
   pogrubione_bez_pokrycia: ['LISTA'] | klasa: LISTA
```

Pierwszym skokiem, jako `LISTA`. Klucz czytany tą samą regułą jednego skoku przez
przypisanie w zasięgu, którą 6.D309 wprowadziło, a 6.D315 poprawiło.

## 2. POPULACJI 439 I LICZBY 140 NIE ODTWARZAM — i mówię, czego nie liczę

```
czytnikow: 961   [6.D315: 439]
   NIEROZSTRZYGNIETY     428   [6.D315: 140]
   LISTA                 264
   SLOWNIK               132
   KROTKA                 58
   ZBIOR                  41
   STRUMIEN               28
   LICZNIK                10
```

**Moja populacja jest ponad dwukrotnie większa, a klasa nierozstrzygnięta trzykrotnie.**
Różnicy **nie uzgadniam** — to byłoby dobieranie definicji pod cudzą liczbę (lekcja 7;
ten sam ruch co przy 6.D317, 6.D318, 6.D319, 6.D321, 6.D323 i 6.D325).

**Sprawdziłem dwie hipotezy o tej różnicy i obie ją tłumaczą tylko częściowo**, więc
podaję je jako zmierzone, a nie jako domysł:

- **Funkcje zagnieżdżone.** Pierwsza wersja brała `ast.walk`, czyli także funkcje
  zdefiniowane wewnątrz testów: 1020 czytników. Zawężenie do poziomu modułu daje
  **961** — różnica 59, czyli za mało.
- **Zwroty skalarne.** Funkcji nie-testowych ze zwrotem na poziomie modułu jest
  **1082**; z tego **179** zwraca wyłącznie skalar (napis, liczbę, wartość logiczną).
  Odsianie ich daje **903** — nadal ponad dwukrotnie więcej niż 439.

Czego więc nie liczę tak samo jak 6.D315, nie wiem, i tak to zapisuję. **Wszystkie
liczby niżej są liczbami o MOJEJ populacji** i przy każdej to zaznaczam.

## 3. TRZY LICZBY: 11 · 2 · 415

```
=== ILE DOMYKA KTORY SKOK (z 428 nierozstrzygnietych) ===
   skok 2:   11
   skok 3:    2
   domkniete razem: 13
   NIE DOMYKA SIE NIGDY: 415
```

**Drugi skok domyka jedenaście z czterystu dwudziestu ośmiu — 2,6 %.** Trzeci dodaje
dwa. Czwartego i dalszych nie domyka **żaden**: rozkład długości łańcucha kończy się
na trzech ogniwach.

**Pole ostrzegało, żeby nie przyjąć, że dwa skoki wystarczą, i kazało policzyć
DŁUGOŚĆ łańcucha.** Policzyłem — i ostrzeżenie okazało się trafne w nieoczekiwaną
stronę: łańcuch nie jest za krótki, tylko **prawie go nie ma**. Trzynaście czytników
na 428 w ogóle ma drugie ogniwo.

## 4. GŁÓWNE ZNALEZISKO: 412 z 415 to NIE JEST problem łańcucha

```
=== PRZYCZYNY ===
   WOLANIE SPOZA tools/tests     208
   ZMIENNA SPOZA ZASIEGU         204
   ZWROT WARUNKOWY                 3
```

- **208 czytników zwraca wynik wywołania, którego celu nie ma w `tools/tests/`** —
  bibliotekę standardową, `subprocess`, `re`, `json`, `os.path`. Żadna liczba skoków
  tego nie domknie, bo skakać jest dokąd, ale cel nie jest czytnikiem tego projektu.
- **204 zwraca zmienną spoza zasięgu funkcji** — argument, globalną, wartość z pętli.
  Reguła jednego skoku z 6.D309 zagląda do przypisań **w zasięgu**; tu przypisania
  w zasięgu nie ma wcale, więc drugi skok nie ma punktu zaczepienia.
- **3 mają zwrot warunkowy o różnych kształtach** — i tylko te trzy są tym, o co
  pole pyta: przypadkiem, w którym klucz nie jest własnością statyczną.

**Pole dopuszczało odpowiedź „żaden nie domyka się nigdy" i mówiło, co by znaczyła:
klucz tożsamości nie jest własnością statyczną.** Odpowiedź nie brzmi „żaden", ale
prowadzi do wniosku bliskiego: **dla 412 z 428 czytników klucz nie jest własnością
statyczną TEGO DRZEWA** — jest własnością biblioteki standardowej albo wywołującego.

## 5. CYKLU NIE MA — i to jest liczba, nie brak pomiaru

Pole ostrzega wprost, że łańcuch bywa cykliczny, i kazało to policzyć. W czytaniu
po poziomie modułu **cykli jest ZERO**. W czytaniu szerszym, z funkcjami
zagnieżdżonymi, był **jeden**.

Podaję obie liczby, bo różnica między nimi jest treścią: **jedyny cykl w tym drzewie
przechodzi przez funkcję zdefiniowaną wewnątrz testu**, a nie między czytnikami
modułowymi. Wykrywacz cyklu stoi w przyrządzie i działa — zero nie jest tu brakiem
sprawdzenia.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| X1 | kontrola przyrządu przejdzie | trafione |
| X2 | populacji 439 i liczby 140 nie odtworzę | trafione — 961 i 428 |
| X3 | drugi skok domknie więcej niż połowę | **OBALONE** — 2,6 % |
| X4 | trzeci skok domknie mniej niż dziesięć | trafione — dwa |
| X5 | znajdzie się co najmniej jeden cykl | **OBALONE** w czytaniu modułowym, trafione w szerszym (§5) |
| X6 | największą przyczyną „nigdy" będzie zwrot warunkowy | **OBALONE** — zwrot warunkowy jest NAJMNIEJSZĄ przyczyną: 3 z 415 |

**X3 i X6 obalone razem opisują tę samą pomyłkę.** Wyobrażałem sobie klasę
`NIEROZSTRZYGNIETY` jako zbiór czytników o **skomplikowanym zwrocie** — łańcuchach,
warunkach, cyklach. Jest to zbiór czytników, których zwrot **wychodzi poza to drzewo**:
do biblioteki standardowej albo do wywołującego. Warunek obalenia dla X3 spisałem
przed pomiarem i honoruję go: rozkład długości łańcucha podaję w całości (§3),
zamiast streszczać jedną liczbą.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono klasyfikatora 6.D315** ani nie przepisano żadnego czytnika.
- **Nie postawiono bramki na kształcie zwrotu.**
- **Nie uzgodniono populacji 961 z 439** (§2) — dwie hipotezy sprawdzone, obie
  tłumaczą różnicę częściowo.
- **Nie uruchomiono żadnego kodu, żeby rozstrzygnąć klucz.** Pole wymienia to jako
  osobną możliwość; ta pozycja mierzy, ile daje się rozstrzygnąć **statycznie**,
  i odpowiedź brzmi: wszystko poza 415.
- **Nie rozstrzygnięto kluczy 208 wywołań spoza `tools/tests/`** — wymagałoby to
  klasyfikowania biblioteki standardowej, czyli drugiego drzewa.
- **Nie tknięto `src/` ani `data/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Dwieście osiem czytników zwraca wynik wywołania biblioteki standardowej.**
   Każdy pomiar „kształtu zwrotu" w tym drzewie rozbija się o tę granicę, a nie
   o długość łańcucha — i żaden dotąd tego nie nazwał.
2. **Dwieście cztery czytniki zwracają zmienną spoza zasięgu.** Reguła jednego skoku
   z 6.D309 jest dla nich bezczynna z definicji, a nie z niedopatrzenia: nie ma
   przypisania, do którego mogłaby skoczyć.
3. **Rozkład długości łańcucha kończy się na trzech ogniwach.** Przy 961 czytnikach
   nie ma w tym drzewie ani jednego łańcucha czteroogniwowego — co znaczy, że
   czytniki tego projektu prawie nie budują się jeden na drugim.
