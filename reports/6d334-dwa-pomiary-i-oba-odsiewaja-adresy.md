# 6.D334 · Pomiarów nazw w prozie są DWA i oba odsiewają adresy — a mój przyrząd przez trzy wersje mówił „zero", „jeden" i „pięć"

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `d2a79b6`

6.D324 §3 zmierzyło, że z osiemnastu wzorców łapiących identyfikator odcinka
**trzynaście łapie go jako część ścieżki albo wiersza tabeli**. Ta pozycja pyta,
ile pomiarów w `tools/tests/` to dotyka. **Liczy** i żadnego wzorca nie zmienia.

---

## 1. GŁÓWNE ZNALEZISKO metodologiczne: sito na ŹRÓDLE wzorca nie działa

Spisałem przed pomiarem sito, które rozpoznaje „wzorzec łapiący nazwę" po **kształcie
jego źródła** — innym wzorcem puszczonym na tekście `re.compile(...)`. Dało **zero**
przy kontroli, która żąda niezera:

```
=== WERSJA 1: sito na ZRODLE wzorca ===
   test_report_claims.py w populacji: False        <- KONTROLA NIE PRZESZLA
   pomiarow liczacych nazwy w prozie:    0
```

Sito na źródle nie ma jak działać i mówię dlaczego, zamiast je łatać: `CLAIM` pisze
klasę jako `[A-Z][A-Z0-9_]{3,}`, `PATH_TOKEN` jako `[A-Za-z0-9_][A-Za-z0-9_./+-]*`,
a `NAZWA_ZAPADKI` **składa się w czasie wykonania** z `"|".join(...)` po zbiorze nazw
— trzy różne zapisy tej samej intencji i jeden z nich w źródle w ogóle nie istnieje.

**Wersja druga jest FUNKCJONALNA:** kompiluję każdy wzorzec i puszczam na zdaniu
wzorcowym, w którym ta sama nazwa stoi raz goło, a raz w ścieżce.

```
PROZA = "Zapadka `MIN_RADIUS_M` wynosi 20, a stała `L1_A` 37. Adres `data/track/L1_A.json`
         i moduł `tools/tests/test_dead_constants.py` stoją obok, zmierzone 20.09.2026."
```

Dała **jeden** — bo wymóg „wzorzec użyty do policzenia" sprawdzałem w oknie ±5
wierszy, a wzorzec stoi w czytniku, gdy liczenie siedzi w teście kilkaset wierszy
dalej. **Wersja trzecia** liczy to użycie na poziomie modułu i dopiero ona przechodzi
kontrolę:

```
=== KONTROLA PRZYRZADU ===
   test_report_claims.py w populacji: True ; ODSIEWA adresy: True
```

**Ścieżka liczby przez trzy wersje przyrządu: 0 → 1 → 5.** Przewidywanie U5 („sito
pomyli się co najmniej raz") trafione dwa razy, i obie pomyłki były w **definicji
użycia**, nie w regule.

## 2. Trzy liczby z automatu — i co z nich zostaje po przeczytaniu

```
=== TRZY LICZBY (automat, wersja 3) ===
   pomiarow liczacych nazwy w prozie:            5
   z nich ODSIEWA adresy plikow:                 2
   z nich WNIOSKUJE o liczbie nazw roznych:      3

=== LISTA IMIENNA ===
   modul                                      odsiewa  rozne   adres   wzorzec:wiersz
   test_dead_constants_csharp.py              False    True    True    IDENTYFIKATOR:236
   test_digit_boundaries.py                   True     False   True    TOKEN_LICZBOWY:30
   test_docs_ci_claims.py                     False    True    True    NEXT_LABEL:102
   test_prose_counts.py                       False    True    False   PARA_NAZWA_LICZBA:878
   test_report_claims.py                      True     False   False   CLAIM:85
```

**Przeczytałem wszystkie pięć i trzy odpadają.** Przy pięciu pozycjach czytanie jest
tańsze niż reguła (lekcja 6.D317, potwierdzona w 6.D320 i 6.D329):

| moduł | wzorzec | dlaczego odpada |
|---|---|---|
| `test_dead_constants_csharp.py` | `IDENTYFIKATOR = [A-Za-z_][A-Za-z0-9_]*` | skanuje **kod C#**, nie prozę — `maska_z_dziurami(zapis)` w wierszu 579 |
| `test_digit_boundaries.py` | `TOKEN_LICZBOWY = \d+(?:[.,]\d+)*` | łapie **liczby**, nie nazwy; w moim zdaniu trafił w cyfrę `1` wewnątrz `L1_A` |
| `test_docs_ci_claims.py` | `NEXT_LABEL` | czyta **etykiety runnera** dopiero po kotwicy `runs-on:`, więc prozy z adresem nigdy nie widzi |

**`TOKEN_LICZBOWY` jest najciekawszy i dlatego stoi w tabeli, a nie w przypisie:**
wpadł do populacji, bo identyfikator odcinka **ma w sobie cyfrę**. To ten sam kształt
co usterka z 6.D322 — wzorzec liczbowy sklejający cyfry przez maskowany odsyłacz.
Mój przyrząd powtórzył go z drugiej strony i mówię to, zamiast wyciąć przypadek.

## 3. Odpowiedź na pytanie zadane wprost

**Pomiarów liczących nazwy w prozie są DWA:**

```
   test_report_claims.py    CLAIM:85               `([A-Z][A-Z0-9_]{3,})` + liczba
   test_prose_counts.py     PARA_NAZWA_LICZBA:878  nazwa w grawisach albo WIELKIMI + liczba
```

**Oba odsiewają adresy plików, czyli dwa z dwóch** — a automat mówił „jeden z dwóch",
i to też jest pomyłka mojego sita, nie własność drzewa. Szukałem odsiewania po
nazwach `ADRES_NIE_TWIERDZENIE`, `PATH_TOKEN` i `IGNORED_PREFIXES`, a `test_prose_counts.py`
odsiewa **własnym** wzorcem, stojącym wiersz pod tym, który liczy:

```python
ODSYLACZ_PLIKU = re.compile(r"\.(md|py|cs|json|csv|txt|glb|png)$")
...
        if ODSYLACZ_PLIKU.search(nazwa):
            continue
```

I odsiewa **z tego samego powodu**, który ta pozycja bada — komentarz nad wzorcem
mówi to wprost: „Nazwa z rozszerzeniem pliku jest ODSYŁACZEM `plik:wiersz`, a nie
członem rozkładu, i jest odsiewana — inaczej każde `raport.md 127` wchodzi do
wyliczenia i sito liczy odsyłacze, dokładnie jak w 6.D263."

### 3.1 Ile wnioskuje o liczbie nazw RÓŻNYCH: ZERO

Pole żądało tej liczby także wtedy, gdy wynosi zero, i mówiło, co by to znaczyło.
**Wynosi zero.** Przeczytałem obie drogi liczenia:

* `CLAIM` → `claims_in_reports` zwraca **trafienia**, a bramka porównuje ich liczbę
  z `MINIMUM_CLAIMS = 10` (`checked >= MINIMUM_CLAIMS`). To liczba trafień.
* `PARA_NAZWA_LICZBA` → `_pary_wyliczenia` zwraca **pary**, a próg
  `MINIMUM_PAR_ROZKLADU = 3` liczy pary w akapicie. Zbiór `odciski` w wierszu 1109
  jest zbiorem **odcisków wyliczeń**, a nie nazw.

Jedyne `set(...)` przy nazwach w `test_report_claims.py` stoi w `constant_values()`
i buduje je z `DEFINITION`, czyli z **kodu**, nie z prozy.

**Wniosek, którego żądało pole: liczenie adresu jako nazwy nie psuje w tym drzewie
niczego.** Oba pomiary pytają „ile razy pada", a nie „ile nazw" — a oba i tak adresy
odsiewają. Przewidywanie U4 jest **obalone** i spełniam warunek spisany przed
pomiarem: nie szukam trzeciego pytania, które by się o to rozbiło.

## 4. Przewidywania — trzy trafione, trzy obalone

| # | przewidywanie | wynik |
|---|---|---|
| U1 | kontrola przyrządu przejdzie | **trafione**, ale dopiero w trzeciej wersji (§1) |
| U2 | pomiarów będzie więcej niż dziesięć | **OBALONE**: pięć z automatu, dwa po przeczytaniu |
| U3 | odsiewających adresy będzie mniejszość | **OBALONE**: wszystkie, czyli dwa z dwóch (§3) |
| U4 | co najmniej jeden wnioskuje o liczbie nazw różnych | **OBALONE**: żaden (§3.1) |
| U5 | sito pomyli się co najmniej raz | **trafione** dwa razy w definicji użycia i raz w definicji odsiewania |
| U6 | jakiś moduł liczy i trafienia, i nazwy różne | **trafione**: `test_report_claims.py` liczy trafienia `CLAIM` i osobno nazwy różne w `constant_values()` — tylko że to drugie idzie z kodu, nie z prozy |

**Trzy obalenia z sześciu i wszystkie w tę samą stronę:** spodziewałem się drzewa,
w którym liczenie nazw w prozie jest rozpowszechnione i nieostrożne. Jest rzadkie
i ostrożne — dwa pomiary, oba z własnym odsiewaniem adresów, oba liczące trafienia,
a nie nazwy.

## 5. Czego świadomie nie zrobiłem

Nie zmieniłem żadnego wzorca, nie odsiałem adresów, nie postawiłem bramki na wyniku,
nie tknąłem `src/` ani `data/` — wszystko to stoi w polu „Poza zakresem".

**Nie dociągnąłem sita do zera fałszywych trafień.** Trzy moduły odrzucone w §2
zostawiam w wyniku automatu i odrzucam je **czytaniem**, bo zwężanie wzorca pod znany
wynik byłoby dopasowywaniem przyrządu do odpowiedzi — tak samo rozstrzygnęło 6.D322.

## 6. Co zauważyłem przy okazji, ale nie tknąłem

`NEXT_LABEL` w `test_docs_ci_claims.py` obcina z tokenu końcowe `.` i `-`, z komentarzem
„bez tego komunikat mówiłby o etykiecie `wsl2.`". Jest to **jedyne** miejsce
w `tools/tests/`, gdzie interpunkcja zdania jest odejmowana od nazwy jawnie i z powodem
zapisanym obok. Wszystkie inne czytniki nazw albo opierają się na grawisach, albo nie
mają tego problemu — i żaden pomiar tego nie zestawia.
