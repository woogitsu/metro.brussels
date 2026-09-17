# 6.D259 — liczba w prozie: sito z 6.D255 nie przenosi się, i to jest zmierzone

**Data:** 17.09.2026 · **Gałąź:** `claude/6d259-liczba-w-prozie` · **Baza:** `a013a4a`

## 1. Co pozycja zakładała, a co wyszło

Pozycja zakładała, że zasięg sita z 6.D255 wystarczy poszerzyć na `ast.get_docstring`
i komentarze `#:`, a pytanie brzmi tylko „ile literałów dochodzi". Dochodzi ich
**dwadzieścia razy więcej**, a lista wyjątków przestaje się mieścić w tym, co da się
sprawdzić — czyli odpowiedź na pytanie z pola „Wyjście" brzmi **NIE**.

## 2. Pomiar populacji

```
komentarzy pod tools/tests/:   10511   literałów liczbowych w nich:  3663
docstringów:                    2657   literałów liczbowych w nich:  4713
                                       RAZEM:                        8376

dla porównania, w KOMUNIKATACH asercji (6.D255):                      418
```

## 3. Cztery zakresy, cztery liczby

Sito to samo, co przy komunikatach (6.D255), i pozyczone, a nie przepisane (6.D213):
te same stałe `SPECYFIKATOR`, `LICZBA`, `SKALE` oraz szerokość okna.
Oknem **najhojniejszym z możliwych**, więc
każda z tych liczb jest **podłogą**, nie oszacowaniem.

| zakres | literałów | bez pokrycia |
|---|---|---|
| cała proza pod `tools/tests/` | 8376 | **573** |
| zdania ogłaszające pomiar (`zmierzon`, `pomiar`, `policzon`…) | 2896 | **190** |
| liczby **pogrubione** `**N**` | 280 | **175** |
| z tego same komentarze `#:` | — | **71** |

Lista wyjątków z 6.D255 ma czterdzieści jeden wpisów przy 44 trafieniach. Najwęższy
zakres, który ma jeszcze sens, daje **163 unikalne klucze** — czterokrotnie więcej.
Lista tej długości nie jest listą, tylko podpisem pod obrazkiem (6.D243): nikt jej
nie przeczyta w całości przy żadnej zmianie.

**Dlaczego akurat pogrubienie.** Nie z wygody: `**N**` jest w tym repozytorium
konwencją na liczbę **zmierzoną**, a nie na liczbę w zdaniu. Zawężenie czyta więc
konwencję, którą repozytorium już stosuje, a nie kryterium wymyślone pod wynik.

## 4. Pierwsza wersja czytnika dawała 38 i to była USTERKA, nie postęp

Okno pokrycia obejmowało wiersze **samego komentarza**, więc liczba pokrywała
**samą siebie**. Sito wychodziło prawie puste i wyglądało na skuteczne — dokładnie
ten kształt, który 6.D255 złapało przy oknie komunikatów, tylko tam okno kończyło się
PRZED asercją, a tu musi być **wycięte ze środka**.

Złapała to **kontrola przyrządu, przy pierwszym przebiegu** — nie oko i nie recenzja.
Kontrola żądała trzech trafień na wejściu syntetycznym, a dostała zero:

```
FAIL test_czytnik_prozy_widzi_TRZY_OSOBNE_wezly_a_nie_jeden:
  sito prozy dalo [], a mialo dac ['111', '444', '666']
```

Po wycięciu zasięgu węzła (`od`–`do` z `token.start`/`token.end` i
`Constant.lineno`/`end_lineno`) liczba wynosi **175**, i to ona jest uczciwa.
**Bez tej kontroli pozycja zostałaby domknięta liczbą 38** — a 38 znaczyło „sito
prawie nic nie zostawia", czyli wniosek odwrotny do prawdziwego.

## 5. Rozstrzygnięcie: zapadka, a nie lista

Zostaje **zapadka górna** `MAX_POGRUBIONYCH_BEZ_POKRYCIA = 175`, wolno ją tylko
obniżać — ten sam wzorzec, co `MAX_UNMATCHED_NEEDLES` (33) i
`MAX_GAME_UNMATCHED_NEEDLES` (48) w `test_needle_specificity.py`, z tego samego
powodu: populacja jest za duża na wyliczanie, ale każdy NOWY przypadek ma zapalić.

Do niej **podłoga** `MIN_POGRUBIONYCH = 240` na populację pogrubionych. Para jest
treścią, nie symetrią: czytnik zepsuty do zera daje zero trafień, czyli przechodzi
zapadkę górną **celująco**. Bez podłogi byłoby to 6.D27 w czystej postaci.

**Bramka złapała przy tym dwa razy MOJĄ WŁASNĄ prozę**, dopisywaną w tym samym
commicie — raz `**2,94**` cytowane z cudzego pliku, raz `**41**` jako twierdzenie
o `WYJATKI`. Oba razy poprawiłem **zdanie**, nie zapadkę; `MAX_` podniesiona
o własne pisanie przestałaby być zapadką.

## 6. Trzy nazwane przypadki — werdykty

Pole „Skończone, gdy" żądało werdyktu dla każdego. **Wszystkie trzy nieprawdziwe.**

| adres | co mówi | co jest dziś |
|---|---|---|
| `test_mutation_sweep.py:2492` | „dałoby 2346 zamiast 63" | `targets()` = **71**, `collect()` = **2586** |
| `test_dead_constants_csharp.py:83` | `const` 304, `static readonly` 85, razem 389 | **307 / 86 / 45**, razem **438** |
| `test_report_claims.py:1863` | oślepienie kosztuje 201 / 197 / 271 | **219** sekcji w **215** raportach |

Przy trzecim nieprawdziwa okazała się także **liczba z samego opisu pozycji**: opis,
napisany dobę wcześniej przy 6.D255, mówił „215 w 211". Dziś jest 219 w 215. Opis
pozycji o starzeniu się liczb zestarzał się przez dobę — i to jest najkrótszy
argument za tą bramką, jaki w tym raporcie stoi.

## 7. Czego bramka nie obejmuje i dlaczego

- **Łańcuchy zmian** `A -> B (data, pozycja): powód` — **146** komentarzy, pomijane
  co do jednego. To populacja **6.D260**, która mierzy liczby mające pokrycie
  W HISTORII; ta mierzy liczby bez żadnego. Dwie bramki nie mają mówić o tym samym
  wierszu, a kontrola przyrządu sprawdza, że łańcuch NIE wchodzi do prozy.
- **Zdania z datą** — wyłączane **per WIERSZ, nie per cały tekst**, i to jedyna
  różnica wobec czytnika komunikatów. Powód zmierzony: komunikat ma jedno zdanie,
  więc data gdziekolwiek w nim dotyczy całości; docstring ma kilkanaście akapitów
  i data w jednym zwalniała wszystkie pozostałe. Różnica kosztuje **44 → 38** na
  czytniku z usterką z §4, a na poprawionym jest wliczona w 175.
- **`docs/` i `reports/`** — czyta je `test_report_claims.py`; granica tamtego
  czytnika to osobne rozstrzygnięcie (6.D230). Pole „Poza zakresem" zabrania.

## 8. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Mutacje na KOPII drzewa (§4.6), `__pycache__` czyszczony (6.D102), każda z asercją,
że **wylądowała**.

### Kontrola przyrządu — trzy osobne węzły

Zadanie żądało jej wprost. Komentarz `#:`, docstring modułu i docstring funkcji to
trzy różne węzły `ast`, a czytnik widzący jeden z nich przechodzi tak samo zielono
jak kompletny. Sprawdzane cztery rzeczy naraz: że wszystkie trzy rodzaje docierają,
że łańcuch zmian jest pomijany, że pogrubienie jest warunkiem koniecznym, i że okno
działa **w obie strony** (stała PRZED komentarzem i stała PO nim).

Ta kontrola **padła przy pierwszym przebiegu** i to jest jej cała wartość — §4.

### KN-a — nowa pogrubiona liczba bez pokrycia

Przewidywanie: **czerwień**, 176 przy zapadce 175.

```
KN-a mutacja wyladowala: 1
FAIL test_zadna_NOWA_pogrubiona_liczba_w_prozie_nie_wchodzi_bez_pokrycia:
  pogrubionych liczb bez pokrycia jest 176 przy zapadce 175
  5/6 przeszło
```

Zgodnie z przewidywaniem.

### KN-b — oślepienie czytnika do zera

Przewidywanie: zapadka górna przechodzi **celująco**, czerwień ma dać **podłoga**.

```
KN-b mutacja wyladowala: 1
FAIL test_czytnik_prozy_widzi_TRZY_OSOBNE_wezly_a_nie_jeden: [] 
FAIL test_zadna_NOWA_pogrubiona_liczba_w_prozie_nie_wchodzi_bez_pokrycia:
  pogrubionych liczb w prozie jest 0 przy podlodze 240 — czytnik oslepl
  4/6 przeszło
```

Zgodnie z przewidywaniem, i to jest odpowiedź na pytanie, po co podłoga obok górnej:
**sama górna dała się oślepić na zielono.**

## 9. Weryfikacja

```
python3 tools/tests/test_all.py test_message_claims.py
  6/6 przeszło

python3 tools/tests/test_all.py
  2574/2574 przeszło
  RAZEM 251.082 s, 2574 testów, 130 modułów

~/.dotnet/dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 673, Skipped: 0, Total: 673

~/.dotnet/dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 318, Skipped: 0, Total: 318
```

## 10. Zauważone, nietknięte

- Trzech nazwanych przypadków **nie poprawiono**. Wszystkie trzy niosą liczby, których
  nie da się podstawić z kodu bez przeliczenia ich w bramce, a pole „Poza zakresem"
  pozycji zabrania przepisywania prozy, której pomiar nie obejmie. Werdykty są
  zapisane w `NAZWANE_PRZYPADKI` z bramką sprawdzającą, że wskazane wiersze nadal
  istnieją — inaczej byłby to napis o stanie, którego nie ma.
- **163 unikalne klucze wobec 175 trafień** znaczy, że dwanaście liczb pada w tym samym
  pliku po dwa razy. Klucz jest parą `(plik, liczba)`, a nie trójką z wierszem, bo
  wiersz przesuwa się przy każdej edycji — ale przy zapadce na LICZBĘ trafień to nie
  ma znaczenia i dlatego nie jest tu rozstrzygane.
- Zapadka stoi na **175**, a nie na zaokrągleniu w górę, i dlatego zapala się przy
  pierwszym nowym przypadku. Cena jest znana: każde dopisanie pogrubionej liczby bez
  pokrycia wymaga albo policzenia jej, albo zdjęcia pogrubienia. To jest cel, nie koszt.
