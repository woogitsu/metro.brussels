# 6.D315 · Siedem par na dwieście pięćdziesiąt deklaruje różnicę klucza — a kontrola przyrządu złapała MOJĄ WŁASNĄ kolejność klauzul

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `07ba87a`

6.D304 zauważyło, że pod tą samą operacją powielenia wpisów `gole_w_prozie_pomiarowej`
daje 259 wobec 259, a `pogrubione_bez_pokrycia` rośnie ze 175 na 2298 — pierwszy
trzyma zbiór `widziane`, drugi nie odsiewa nic. Ta pozycja pyta, ile par czytników
tego zestawu różni się tak samo i przy ilu ta różnica jest **zapisana**.

---

## 1. Trzy liczby, których żądało pole „Wyjście"

```
CZYTNIKOW (funkcja nie-testowa, ktora zwraca albo yielduje dane):   439
PAR pozyczonych wobec siebie (wspolny wzorzec, okno albo czytnik):  449
   z tego ROZNIACYCH SIE KLUCZEM TOZSAMOSCI:                        250
      z tego z roznica ZAPISANA W PROZIE ktorejkolwiek polowy:        7
```

**Odpowiedź na pytanie, które pole kazało zadać wprost: siedem z dwustu
pięćdziesięciu**, czyli **2,8 %**. Pole dopuszczało odpowiedź „przy żadnej"
i tak blisko niej jest.

Wszystkie siedem, z nazwy:

```
csharp_test_methods.py         pliki [LISTA] / pomocnicy [SLOWNIK]
mutation_sweep.py              main [ZBIOR] / przyczyna_pustego_zbioru [KROTKA]
mutation_sweep.py              naglowek_odciskow [LISTA] / odcisk_przebiegu [NIEROZSTRZYGNIETY]
mutation_sweep.py              naglowek_odciskow [LISTA] / report [NIEROZSTRZYGNIETY]
test_dead_constants_csharp.py  martwe [SLOWNIK] / maska_z_dziurami [NIEROZSTRZYGNIETY]
test_message_claims.py         bez_pokrycia [LISTA] / gole_w_prozie_pomiarowej [ZBIOR]
test_message_claims.py         gole_w_prozie_pomiarowej [ZBIOR] / pogrubione_bez_pokrycia [LISTA]
```

## 2. GŁÓWNE ZNALEZISKO: kontrola przyrządu złapała usterkę w MOJEJ kolejności klauzul

To jest najważniejsza rzecz w tej pozycji i nie dotyczy drzewa, tylko mnie.

Plik definicji, spisany **przed** pomiarem, mówi:

> `ZBIOR` — wynik trafia do `set()` **albo funkcja trzyma zbiór `widziane`
> i pomija powtórki`.

Zaimplementowałem to tak, że **najpierw** sprawdzałem kształt wyrażenia w `return`,
a **dopiero potem** klauzulę o `widziane`. Dla funkcji, która robi jedno i drugie —
trzyma `widziane`, a zwraca listę — wygrywał kształt `return`. Dokładnie taka jest
`gole_w_prozie_pomiarowej`.

Skutek: **para kontrolna wypadła z listy różniących się kluczem.**

```
ZE SKOKIEM, kolejnosc BLEDNA:
   gole_w_prozie_pomiarowej [LISTA] / pogrubione_bez_pokrycia [LISTA]
   ROZNI SIE KLUCZEM: False          <- kontrola NIEZDANA

PO PRZYWROCENIU KOLEJNOSCI Z ZAPISU:
   gole_w_prozie_pomiarowej [ZBIOR] / pogrubione_bez_pokrycia [LISTA]
   ROZNI SIE KLUCZEM: True           <- kontrola zdana
```

**Bez tej kontroli zaraportowałbym 237 par z cicho zepsutym klasyfikatorem.**
Pole postawiło ją dokładnie po to i zadziałała dokładnie tak, jak miała.

Poprawka jest **powrotem do zapisu**, a nie dobraniem reguły pod wynik: klauzula
o `widziane` stoi w moim pliku definicji jako **równorzędna alternatywa**, nie jako
zapasowa, i to implementacja ją zdegradowała.

## 3. Trzy warianty tego samego rachunku — i o ile przestawiają wynik

```
                                       czytnikow  par  roznicacych  udokumentowanych
BEZ SKOKU (sam ksztalt `return`)             439  449          168                 4
ZE SKOKIEM przez przypisanie w zasiegu       439  449          237                 7
ZE SKOKIEM + kolejnosc Z ZAPISU              439  449          250                 7
```

**Populacja par nie drgnęła ani razu** (449 w każdym wariancie) — to jest własność
drzewa. **Liczba par różniących się kluczem urosła o 49 %** między wariantem
pierwszym a trzecim, i to jest własność definicji klucza, nie drzewa.

Skok przez przypisanie w zasięgu jest tą samą regułą, którą 6.D309 ustaliło w tym
repozytorium przy innym pytaniu. Bez niego klasa `NIEROZSTRZYGNIETY` liczyła **294**
z 439 czytników, czyli dwie trzecie, bo ten zestaw pisze `out = []` … `return out`,
a nie `return [...]`.

## 4. Trzy wartości klucza NIE WYSTARCZYŁY — i przewidziałem to przed pomiarem

Plik definicji zapowiadał trzy wartości: `ZBIOR`, `LISTA`, `LICZNIK`. Zmierzone:

```
LISTA               159
NIEROZSTRZYGNIETY   140
SLOWNIK              67
ZBIOR                35
KROTKA               24
STRUMIEN              8
LICZNIK               6
```

**Dwieście trzydzieści dziewięć czytników z czterystu trzydziestu dziewięciu —
pięćdziesiąt cztery procent — wpada poza trójkę, którą zapowiedziałem.** Trzy
z czterech dodatkowych klas są realnymi kształtami (`SLOWNIK`, `KROTKA`,
`STRUMIEN`), a czwarta (`NIEROZSTRZYGNIETY`, 140) jest brakiem przyrządu i tak ją
nazywam — nie jest kształtem, tylko miejscem, w którym mój czytnik nie umie
odpowiedzieć.

Mój warunek obalenia mówił: „jeśli którakolwiek funkcja nie da się przypisać do
żadnej z trzech wartości, **raportuję czwartą z nazwy** zamiast rozciągać definicję
którejś z trzech". Raportuję cztery.

## 5. Które klucze najczęściej się rozjeżdżają

```
LISTA / NIEROZSTRZYGNIETY          79
LISTA / SLOWNIK                    56
NIEROZSTRZYGNIETY / SLOWNIK        32
NIEROZSTRZYGNIETY / ZBIOR          22
LISTA / ZBIOR                      16
SLOWNIK / ZBIOR                    12
KROTKA / NIEROZSTRZYGNIETY         10
LISTA / STRUMIEN                    5
```

Przewidywałem, że najczęstsza będzie para `ZBIOR` wobec `LISTA`. Jest **piąta**,
z szesnastoma wystąpieniami wobec siedemdziesięciu dziewięciu u zwycięzcy —
a zwycięzca (`LISTA` wobec `NIEROZSTRZYGNIETY`) jest w połowie **artefaktem mojego
przyrządu**, bo `NIEROZSTRZYGNIETY` to brak odpowiedzi, a nie klucz.

## 6. Czego ta pozycja NIE mówi

Pole ostrzegało: „nie wolno przyjąć, że rozjazd klucza jest usterką. Czytnik liczący
TRAFIENIA ma pełne prawo policzyć tę samą liczbę dwa razy". **Nie przyjmuję.**
Z dwustu pięćdziesięciu par nie orzekam ani o jednej, że jest zepsuta — liczę tylko,
ile z nich **deklaruje** różnicę, i wychodzi siedem.

Zdanie „dwieście czterdzieści trzy pary milczą" jest zdaniem o prozie, nie o kodzie.

## 7. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| T1 | par: 8–40 | **OBALONE** — 449 |
| T2 | różniących się kluczem **mniej niż połowa** | **OBALONE** — 250 z 449, czyli 55,7 % |
| T3 | udokumentowanych mniej niż połowa różniących się | trafione (2,8 %) — ale §7.1 |
| T4 | najczęstsza para to `ZBIOR` wobec `LISTA` | **OBALONE** — piąta, 16 wobec 79 |
| T5 | kontrola wyjdzie na liście różniących się | trafione — **po naprawie z §2** |
| T6 | trzy wartości klucza **nie wystarczą** | trafione — 239 z 439 poza trójką |

### 7.1 T3 było postawione tak słabo, że nie jest wynikiem

„Mniej niż połowa" mieści każdą odpowiedź od zera do stu dwudziestu czterech.
Zmierzone siedem leży przy samym dole tego przedziału i o przedziale nie mówi nic.
Liczę je jako trafione, bo tak brzmi, ale wartość poznawcza jest zerowa — ta sama
szerokość, którą 6.D303 nazwało u siebie.

### 7.2 T5 jest trafione DOPIERO po naprawie i tak je zapisuję

Przy pierwszym poprawnym przebiegu kontrola **nie zdała się** (§2). Gdybym zaliczył
T5 bez tej uwagi, byłoby to twierdzenie o przyrządzie, którego ten przyrząd wtedy
nie spełniał.

### 7.3 T6 nie było niezależne i mówię to drugi raz

Zapowiedziałem w pliku definicji, że T6 stawiam **z nawyku**, bo w tej sesji podział
z pola okazał się niewyczerpujący cztery razy (6.D304, 6.D310, 6.D312, 6.D314).
Trafiło po raz piąty. Nie jest to prognoza o drzewie, tylko obserwacja o tym,
jak sam piszę definicje — i piąte potwierdzenie z rzędu znaczy, że **domyślnie
powinienem zakładać niewyczerpalność**, a nie zgadywać ją za każdym razem.

## 8. Czego świadomie nie zrobiono

- **Nie ujednolicono żadnego klucza** ani nie dopisano odsiewu do jakiegokolwiek
  czytnika. Pole zabrania wprost, a §6 mówi, dlaczego nie byłoby to nawet poprawne.
- **Nie zmieniono żadnej zapadki**; górne wolno wyłącznie obniżać.
- **Nie przepisano prozy w `tools/tests/`** — w tym prozy dwustu czterdziestu trzech
  par, które różnicy nie deklarują.
- **Nie poprawiono klasy `NIEROZSTRZYGNIETY`** (140 czytników). Jest brakiem mojego
  przyrządu i nazywam ją brakiem, zamiast domykać ją regułą wymyśloną po pomiarze.
- **Nie tknięto `src/`** ani `data/`.

## 9. Zauważone przy okazji, nietknięte

**Klasa `NIEROZSTRZYGNIETY` to 140 z 439 czytników, czyli prawie jedna trzecia**,
i to po skoku przez przypisanie. Zawiera funkcje zwracające wynik wywołania innej
funkcji, wyrażenie warunkowe albo zmienną przypisaną w pętli. Ile z nich da się
rozstrzygnąć drugim skokiem, a ile wymaga uruchomienia kodu, nie liczyłem.

**Trzy z siedmiu udokumentowanych par stoją w `mutation_sweep.py`**, czyli w jednym
narzędziu, a nie w bramkach. Czy to znaczy, że narzędzia opisują swoje czytniki
staranniej niż bramki, czy tylko że tamten plik ma dłuższe docstringi — nie
zmierzyłem.

**Populacja par (449) nie drgnęła w żadnym z trzech wariantów rachunku.** Przy
6.D306, 6.D308 i 6.D314 wybór definicji przestawiał ranking; tutaj przestawia
**klasyfikację**, a populację zostawia w spokoju. Jest to czwarty kształt tej samej
rodziny i wart osobnego zapisania: definicja bywa nieszkodliwa dla jednej liczby
i rozstrzygająca dla drugiej **w tym samym pomiarze**.

## 10. Weryfikacja — rzeczywiste wyjście

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2664/2664 przeszło
  RAZEM 369.370 s, 2664 testów, 139 modułów
EXIT=0
```

Zero `FAIL`. **Bramki nie przybyło** — pole „Poza zakresem" zabrania ujednolicania
kluczy i dopisywania odsiewu, a §6 mówi, dlaczego bramka na rozjeździe klucza nie
byłaby nawet poprawna. Bramki dotknięte tą pozycją przeszły wcześniej osobno —
`test_report_hygiene`, `test_backlog`, `test_field_paths`, `test_report_claims`,
`test_docs_map` i `test_message_claims`: **159/159**.

**Szósty pomiar ściany na tym kontenerze w tej sesji**, przy tej samej liczbie testów:

```
414,695   418,599   361,079   365,940   364,619   369,370
```

Pięć ostatnich punktów mieści się w paśmie 361–370 s, a odstaje wyłącznie pierwsza
para. Zapisuję jako dane dla 6.D313, a nie jako wniosek — i odnotowuję, że zdanie
z §10 poprzedniej pozycji („dwie pary odległe o 15 %") było **wcześniejszym
odczytem tej samej rosnącej próby**: przy sześciu punktach wygląda to raczej na
dwa przebiegi odstające na początku niż na dwa pasma. Nie rozstrzygam tego i nie
poprawiam tamtego zdania — tamto opisywało stan przy pięciu punktach i było wtedy
prawdziwe.
