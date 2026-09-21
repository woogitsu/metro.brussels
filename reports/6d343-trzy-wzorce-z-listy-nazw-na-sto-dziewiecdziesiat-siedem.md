# 6.D343 · Wzorców składanych z listy nazw są TRZY na 197 — a najciekawszy nie składa się z listy, tylko z INNEGO wzorca

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `473d9dd`

**POMIAR POWTÓRZONY PRZED COMMITEM.** Przyrząd uruchomiony ponownie na bazie `9d27100` odtwarza wynik co do jedynki: 147 plików, **197** wywołań, **186** literałów, **11** wyrażeń, **3** składane z listy nazw, zero f-stringów ze stałym polem, zero przypadków nierozstrzygniętych jednym skokiem, i kontrola na `NAZWA_ZAPADKI` przechodzi. Daty pomiaru NIE przepisuję na dzisiejszą.

6.D334 §1 zapisało, że sito rozpoznające wzorce po **kształcie ich źródła** dało zero
przy kontroli żądającej niezera, bo część wzorców w `tools/tests/` nie istnieje
w źródle jako literał. Ta pozycja **liczy i czyta**; żadnego wzorca nie przepisuje
i żadnego skanu nie naprawia.

Definicje i sześć przewidywań spisałem **przed** pomiarem, w `DEFINICJE.md` katalogu
roboczego tej pozycji. Przyrząd **jest zachowany** i daje się uruchomić ponownie —
przy 6.D339 jego brak kosztował sprawdzenie przed commitem.

---

## 1. Usterka przyrządu, ZŁAPANA PRZEZ KONTROLĘ, a nie poprawiona po cichu

Wersja pierwsza postawiła `NAZWA_ZAPADKI` w klasie „inne wyrażenie (BinOp)", a pole
żądało klasy „składany z listy nazw". Przyczyna jest w **mojej definicji**, nie
w drzewie: napisałem w `DEFINICJE.md` „na **wierzchu** stoi `str.join`", a prawdziwy
kształt to konkatenacja, w której `join` siedzi w środku:

```python
NAZWA_ZAPADKI = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(n) for n in
                             sorted(ZAPADKI, key=len, reverse=True)) + r")(?![\w])")
```

Na wierzchu stoi `BinOp`, a `join` jest jego środkowym składnikiem. Wersja druga
szuka `join` **gdziekolwiek w poddrzewie** argumentu. Ścieżka liczby przez obie
wersje: **0 → 3** wzorce składane z listy nazw.

Zapisuję to, bo lekcja jest o pisaniu definicji, nie o tym module: **definicja
mówiąca o pozycji węzła („na wierzchu") opisuje jeden kształt zapisu, a nie
konstrukcję** — a pytanie pola dotyczyło konstrukcji. Po poprawce kontrola
przechodzi:

```
=== KONTROLA PRZYRZADU (NAZWA_ZAPADKI z test_commit_claims.py) ===
   tools/tests/test_commit_claims.py:31  klasa=WYRAZENIE  podklasa=skladany z listy nazw
```

## 2. Trzy liczby, których żądało pole

```
plikow przejrzanych: 147
wywolan re.compile:  197
   LITERAL     186  (94.4 %)
   WYRAZENIE    11  (5.6 %)

   literalow:                              186
   wyrazen:                                11
   z nich skladanych Z LISTY NAZW:         3
   skan po zrodle POMINALBY (= wyrazenia): 11
   skan zobaczylby ZLA TRESC (f-string):   0
   nierozstrzygniete jednym skokiem:       0
```

**Wzorców składanych z listy nazw są trzy:** `NAZWA_ZAPADKI`
(`tools/tests/test_commit_claims.py:31`), `GOLY_PARSE` i `TRY_PARSE`
(`tools/tests/test_runner_number_parsing.py:39` i `:40`).

## 3. Przeczytałem wszystkie jedenaście — i osiem pozostałych to CZTERY rodziny

Przy jedenastu przypadkach czytanie bije klasyfikowanie (lekcja 6.D317). Klasa
„inne wyrażenie (BinOp)" była w wersji pierwszej workiem na wszystko; po przeczytaniu
rozpada się na cztery rodziny, z których **żadna nie jest niedbałością**:

| rodzina | ile | przykład | co wstawia |
|---|---|---|---|
| jedna nazwa przez `re.escape`, z pętli albo argumentu | 3 | `tools/tests/test_sim_untested_members.py:90` | nazwę, której szuka wołający |
| wartość liczbowa z czasu wykonania | 3 | `tools/tests/test_message_claims.py:692` | liczbę sformatowaną tuż przed |
| stała modułu | 1 | `tools/tests/test_platform_length_in_pipeline.py:86` | `GENERATOR`, czyli ścieżkę |
| **wyciągnięty z INNEGO wzorca** | 1 | `tools/tests/test_field_paths.py:2570` | listę rozszerzeń wyłuskaną z `PATH_TOKEN` |

## 4. GŁÓWNE ZNALEZISKO: najciekawszy wzorzec nie składa się z listy, tylko z innego wzorca

```python
ROZSZERZENIA_Z_PATH_TOKEN = re.search(
    r"\\\.\(\?:([a-z|]+)\)", PATH_TOKEN.pattern).group(1)

BARE_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"([A-Za-z0-9_][A-Za-z0-9_.+-]*\.(?:" + ROZSZERZENIA_Z_PATH_TOKEN + r"))"
    r"(?![A-Za-z0-9/])")
```

`BARE_TOKEN` bierze listę rozszerzeń nie ze zbioru nazw, tylko **z tekstu innego
skompilowanego wzorca**, wyłuskanego z niego trzecim wzorcem. Odczytanie jego
wartości ze źródła wymagałoby uruchomienia `re.search` na `PATH_TOKEN.pattern` —
czyli wykonania dwóch wzorców po drodze.

**Jest to ta sama intencja, co przy `NAZWA_ZAPADKI`, i ten sam powód:** własna lista
rozszerzeń rozjechałaby się z `PATH_TOKEN` przy pierwszym nowym rozszerzeniu. Pole
„Czego NIE wolno przyjąć bez pomiaru" ostrzegało, żeby nie liczyć konieczności jako
niedbałości, i to ostrzeżenie **sprawdza się na wszystkich czterech przypadkach
dzielenia jednego źródła prawdy** (trzy z listy nazw plus ten).

Różnica jest jednak istotna dla pytania pola: **skan po źródle pominąłby wszystkie
cztery, ale tylko trzy da się odzyskać patrząc na kolekcję.** Czwartego nie —
jego źródłem jest wzorzec, a nie kolekcja.

## 5. Skan po źródle pomija jedenaście, ale nie wszystkie jednakowo

Liczba „jedenaście" jest odpowiedzią na pytanie pola i jest prawdziwa: **żadnego
z jedenastu skan po źródle nie odczyta**. Ale nie są równo nieodzyskiwalne i mówię to
zamiast podać samą jedenastkę:

* **Jeden odzyskuje się jednym skokiem po stałej modułu.**
  `GENERATOR = "tools/track/station_layout.py"` stoi w tym samym pliku jako literał,
  więc wartość `pattern` jest w zasięgu czytnika, który robi jeden skok.
* **Trzy odzyskują się jednym skokiem po kolekcji** — rodzina z §2.
* **Sześć nie odzyskuje się wcale**, bo wstawiają wartość z czasu wykonania: nazwę
  z pętli wołającego albo liczbę policzoną tuż przed.
* **Jeden nie odzyskuje się bez uruchomienia dwóch wzorców** — §4.

## 6. Przewidywania — cztery trafione, dwa obalone

| # | przewidywanie | wynik |
|---|---|---|
| P1 | kontrola przyrządu przejdzie | **trafione, ale dopiero w wersji drugiej** — i warunek obalenia spisany przed pomiarem mówił wprost, że wyjście w innej klasie znaczy usterkę MOJEGO przyrządu; tak było (§1) |
| P2 | wywołań `re.compile` więcej niż sto | **trafione**: 197 |
| P3 | literałów ponad 90 % | **trafione**: 94,4 % |
| P4 | składanych z listy nazw mniej niż pięć | **trafione**: trzy |
| P5 | wszystkie składane z listy nazw w czytnikach prozy albo historii gita | **OBALONE**: dwa z trzech stoją w `tools/tests/test_runner_number_parsing.py`, który czyta `src/Sim.Runner/Program.cs` **jako tekst C#** — nie prozę i nie git |
| P6 | co najmniej jeden f-string ze stałym polem, czytany ze złą treścią | **OBALONE**: zero |

**P6 obalone jest mocniejszym zdaniem niż trafione, i tak stało w warunku obalenia
spisanym przed pomiarem:** usterka z 6.D334 §1 ma dokładnie **jedną** postać —
niewidoczność — a nie dwie. Skan po źródle albo wzorca nie widzi, albo widzi go
poprawnie; nie ma w tym drzewie przypadku, w którym zobaczyłby go **źle**.

## 7. Czego świadomie nie zrobiłem

Nie przepisałem żadnego wzorca na literał, nie zmieniłem sposobu składania, nie
postawiłem bramki na literalności wzorca, nie tknąłem `src/` ani `data/` — wszystko
to stoi w polu „Poza zakresem".

**Nie rozszerzyłem populacji na `re.search`, `re.match` i `re.findall` wołane
z literałem w miejscu.** Pole pyta o `re.compile` i tego się trzymam; zapisałem ten
wybór w `DEFINICJE.md` **przed** pomiarem, żeby nie dało się go potem naciągnąć.

**Nie skakałem po nazwach rekurencyjnie.** Rozstrzygam jednym skokiem w tym samym
module; przypadków, których ten jeden skok nie rozstrzygnął, jest **zero**, i podaję
tę liczbę, zamiast ją przemilczeć.

## 8. Co zauważyłem przy okazji, ale nie tknąłem — i CO Z TEGO OBALIŁEM SAM

**Pierwsza wersja tego akapitu była nieprawdziwa i zostaje przepisana, a nie
dopisana obok.** Napisałem, że `ROZSZERZENIA_Z_PATH_TOKEN` jest w drzewie **jedynym**
miejscem czytającym `.pattern` innego wzorca, i że **nic tego nie pilnuje**. Sprawdziłem
oba zdania przed oddaniem raportu i **oba są fałszywe**:

```
tools/tests/test_prose_counts.py:763    zrodlo = wzorzec.pattern
tools/tests/test_field_paths.py:2564    re.search(r"\\\.\(\?:([a-z|]+)\)", PATH_TOKEN.pattern)
tools/tests/test_field_paths.py:2694    assert ROZSZERZENIA_Z_PATH_TOKEN in PATH_TOKEN.pattern
tools/tests/test_report_hygiene.py:1148 re.search(r"\(\?:([a-z|]+)\)", PATH_TOKEN.pattern)
```

Odczytów `.pattern` jest **siedem, w trzech modułach**. Wyłuskanie alternatywy
rozszerzeń z `PATH_TOKEN` robią **dwa** miejsca, nie jedno —
`tools/tests/test_field_paths.py:2564` i `tools/tests/test_report_hygiene.py:1148` —
i **oba mają swoją obronę**: pierwsze ma bramkę
`test_wzorzec_golej_nazwy_dzieli_rozszerzenia_z_PATH_TOKEN`, która sprawdza, że
wycięty napis naprawdę pochodzi ze wzorca ścieżek, drugie ma `assert` z komunikatem
mówiącym, co się stanie bez tego odczytu.

**Co z pierwszej wersji zostaje prawdą:** `BARE_TOKEN` jest jedynym z **jedenastu
wywołań `re.compile`** tej populacji, którego argument pochodzi z tekstu innego
wzorca — bo drugie wyłuskanie karmi porównanie, a nie nową kompilację. To zdanie §4
sprawdziłem osobno i ono się broni.

**Co zostaje jako rzecz niepilnowana, już po sprawdzeniu:** obie obrony pilnują, że
wycięcie **coś** daje i że pochodzi z `PATH_TOKEN`. Żadna nie pilnuje, że alternatywa
w `PATH_TOKEN` jest **jedna** — druga grupa `(?:a|b)` dopisana do tego wzorca
zostałaby wzięta lub pominięta zależnie od kolejności, a `re.search` nie powiedziałby
o tym nic. Nie jest to usterka dzisiaj i nie ruszam tego; zapisuję jako jedno zdanie,
sprawdzone, zamiast trzech zdań, z których dwa były zmyślone.
