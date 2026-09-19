# 6.D294 · Jedna nazwa „zniknęła" — a to commit, który ją USUWAŁ, bo nigdy nie istniała

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `dc0ff4a`

Klasa `rozne_nazwy` z `klasy_sladu`: commity, w których **obie strony** — komunikat
i raport — nazywają moduł albo zapadkę, tylko **inny**. 6.D283 policzyło ją i nie
zapytało, czy to rozjazd, czy artefakt słownika. Ta pozycja przypisuje każdemu
przypadkowi przyczynę.

---

## 1. Liczby

```
WASKO — klasa `rozne_nazwy`: 25 commitow

(1) komunikat nazywa MODUL, ktorego DZIS NIE MA :  1
(2) z nich: modulu NIE BYLO tez w chwili commita:  1
(3) raport nazywa modul, ktory TEN commit dotyka: 16
    przeciecie (1) i (3)                        :  1
(5) ANI JEDNO, ANI DRUGIE                       :  9
    kontrola: |1|+|3|-|oba|+|ani| = 25 (ma byc 25)
(4) ZAPADKI z komunikatu nieobecne w rejestrze  :  0
```

**Blok pozycji mówi 24, dziś jest 25, i to nie jest rozjazd.** Tamta liczba to pomiar
z 19.09.2026 rano; korpus urósł od tego czasu o commity tego samego dnia, w tym moje.
`docs/04-conventions.md` zabrania przeliczania pomiaru z datą — podaję więc obie
liczby zamiast poprawiać tamtą.

Przecięcie policzone **osobno**, nie przez odejmowanie. Przy 6.D293 ta sama ostrożność
uchroniła przed wynikiem „minus siedemnaście"; tutaj klasy też nie są rozłączne —
`dd53c4e89872` stoi w (1) i w (3) naraz.

## 2. Jedyna „zniknięta nazwa" to commit, który ją USUWAŁ

Klasa (1) liczy **jeden** commit: `dd53c4e89872`, a nazwą jest `test_glossary.py`.

```
$ git log --all --oneline --diff-filter=A -- '**/test_glossary.py'
(pusto)
```

**Ten moduł nie istniał NIGDY** — ani dziś, ani w chwili commita, ani w żadnym punkcie
historii żadnej gałęzi. Klasa (2) jest więc równa klasie (1), i to nie przez zbieg
okoliczności. Komunikat tamtego commita mówi wprost, dlaczego nazwa w nim stoi:

> Pole „Weryfikacja" poprawione: wołało nieistniejący `test_glossary.py`.

**Commit nazywa ten moduł, ponieważ go USUWA z pola „Weryfikacja" cudzej pozycji.**
Klasyfikator widzi „komunikat mówi o module, którego nie ma" i ma rację co do faktu,
a co do wniosku — przeciwnie: to jest commit naprawiający dokładnie tę usterkę,
którą klasa miała tropić.

Nie jest to więc ani rozjazd raportu z kontrolą, ani nazwa, która wyszła z użycia.
Jest to **jedyny kształt, którego blok pozycji nie przewidywał**: nazwa cytowana po to,
żeby ją zdjąć.

## 3. Zero w wierszu (4) jest własnością WZORCA, nie drzewa

Wiersz (4) — zapadki z komunikatu nieobecne w dzisiejszym rejestrze — wynosi **zero**.
Spisałem przed pomiarem, że tak wyjdzie, i **z jakiego powodu**; powód jest ważniejszy
od liczby.

Dwa ekstraktory tego modułu mają **różne domknięcie**:

| wzorzec | jak zbudowany | co widzi |
|---|---|---|
| `NAZWA_ZAPADKI` | alternatywa nazw z **dzisiejszego** rejestru `ZAPADKI` (91 pozycji) | wyłącznie nazwy istniejące DZIŚ — domknięcie **zamknięte** |
| `NAZWA_MODULU` | wzorzec ogólny `test_[a-z0-9_]+\.py` | każdą nazwę o tym kształcie, także nieistniejącą — domknięcie **otwarte** |

Zapadka przemianowana albo skasowana jest dla pierwszego wzorca **niewidzialna
w dawnym komunikacie**: nie stoi w alternatywie, więc nie zostanie wydobyta i nie ma
jak trafić do klasy „nazwa zniknęła". Zero w wierszu (4) jest zatem **gwarantowane
konstrukcją**, a nie zmierzone na drzewie.

**Podanie go jako faktu o repozytorium byłoby odczytaniem ślepej plamy przyrządu jako
dowodu.** To ta sama rodzina, którą 6.D293 złapało na `WYNIK_KONTROLI` trafiającym
w 113/113, i ta sama, o której mówi §7 raportu 6.D292 — tylko tam mylił mianownik,
a tu myli **zasięg słownika**.

Ile zapadek naprawdę zmieniło nazwę albo zniknęło, ta pozycja **nie wie i nie może
wiedzieć tym przyrządem**. Poszerzenie `NAZWA_ZAPADKI` o nazwy historyczne wykracza
poza pole „Poza zakresem" (zabrania zmiany rejestru), więc pytanie zostaje otwarte
i zapisane, a nie zamaskowane zerem.

## 4. Szesnaście z dwudziestu pięciu: rozjazd jest POZORNY

Klasa (3) liczy **16**: raport dopisany w tym samym commicie nazywa moduł, który
**ten sam commit dotyka**. Rozjazd nie polega więc na tym, że raport mówi o czym
innym niż praca — mówi o **module zmienionym**, a komunikat o **innym module z tej
samej pracy**. Dwie prawdziwe nazwy jednej roboty.

Przykłady z listy: `aebd5468bb27` (raport nazywa `test_field_paths.py`,
`test_report_hygiene.py` i `test_suite_runtime_budget.py` — wszystkie dotykane),
`9032b5cfedd0` (trzy moduły, wszystkie dotykane).

**Sześćdziesiąt cztery procent klasy to więc nie usterka**, tylko skutek tego, że
commit ruszający kilka modułów ma w komunikacie jeden, a w raporcie inny.

## 5. Klasa (5): dziewięć bez żadnej z dwóch przyczyn

```
   9895e0677e2b  6.D287: zjawisko siedzi w DWOCH plikach z dwudziestu szesciu
   323bff51efeb  6.D227: pozycja byla zrobiona od trzech dob, a kolejka o tym nie wiedziala
   84ad27337823  6.D253: korzeń repozytorium po `MetroBxl.sln`
   ded3fa0aee19  6.D223: sito myli sie w OBIE strony — 36 % w jedna, 40 % w druga
   71db0209684a  6.D204: pamięć pokrycia DZIAŁA, a przesłanka pozycji opisuje wejście
   e12094c9f4aa  6.D82: panel interfejsu zakotwiczony po obu stronach
   5864828080e1  6.D80: biała lista statusów profilu pionowego
   07dc360acd8d  6.D45: MIN_REPORTS na zmierzonym stanie katalogu
   809e6f139831  Raporty w reports/ nie niosą już liczb, które przestały być prawdziwe
```

Pierwszy z listy — `9895e0677e2b` — to **mój własny commit z dzisiaj** (6.D287).
Zapisuję to, bo klasa nie jest zbiorem dawnych zaniedbań: kształt powstaje nadal
i powstał dziś, pod moją ręką.

Ta dziewiątka to reszta, której pole „Wyjście" nie zamawiało i której ta pozycja
**nie rozstrzyga**: obie strony nazywają moduły istniejące, raport nie mówi o module
dotykanym przez ten commit, a czy to rozjazd prawdziwy, rozstrzyga dopiero czytanie
każdego raportu — czego pole nie żąda.

## 6. Kontrole, obie wykonalne i zdane

```
KONTROLA NEGATYWNA — nazwa obecna do dzis ma NIE trafic do klasy (1): 24 z 25 poza klasa
KONTROLA PRZYRZADU — nazwa nieobecna dzis ma trafic: ['dd53c4e89872']
```

W przewidywaniach zastrzegłem, że kontrola przyrządu **może być niewykonalna**, gdyby
w klasie nie było ani jednego takiego modułu — i że wtedy trzeba to powiedzieć,
a nie udawać zdaną. Okazała się wykonalna, bo taki moduł jest dokładnie jeden.
Zastrzeżenie zostaje zapisane, bo było prawdziwe w chwili pisania.

## 7. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | commitów w klasie wąsko: 24 | **25** — blok podaje pomiar z datą, korpus urósł |
| 2 | moduł nieobecny dziś: 3–10 | **PUDŁO**, jest 1 |
| 3 | nie było też wtedy: 0–2 | trafione (1) |
| 4 | raport o module dotykanym: 10–18 | trafione (16) |
| 5 | zapadek nieobecnych: **zero, z powodu domknięcia wzorca** | trafione — i powód potwierdzony |
| 6 | kontrola negatywna zda | trafione |
| 7 | kontrola przyrządu zda, JEŚLI jest taki moduł | trafione, i był dokładnie jeden |

**Przewidywanie 5 jest jedynym dziś trafionym razem z MECHANIZMEM.** Przy 6.D289
liczba się zgodziła, a mechanizm nie; tutaj wyprowadziłem zero z konstrukcji wzorca
przed policzeniem czegokolwiek i konstrukcja się potwierdziła. Różnica jest w tym,
że tamto przewidywanie zgadywało zjawisko, a to czytało kod.

Pudło drugie jest znów **w dół** — spodziewałem się kilku zniknionych modułów,
a historia tego repozytorium modułów nie kasuje.

## 8. Czego świadomie nie zrobiono

- **Nie zmieniono rejestru `ZAPADKI`** ani nie poszerzono `NAZWA_MODULU`
  (pole „Poza zakresem").
- **Nie poszerzono `NAZWA_ZAPADKI` o nazwy historyczne**, choć §3 pokazuje, że bez
  tego wiersz (4) nie może być niczym innym niż zerem. Byłaby to zmiana rejestru,
  a pytanie zostaje zapisane jako otwarte.
- **Nie przepisano żadnego dawnego komunikatu** i nie zaproponowano przepisania.
- **Nie rozstrzygnięto dziewiątki z klasy (5)** — pole „Wyjście" jej nie zamawia,
  a rozstrzygnięcie wymaga przeczytania dziewięciu raportów.
- **Nie postawiono bramki.**
- **Nie tknięto `src/`.**

## 9. Zauważone przy okazji, nietknięte

`dd53c4e89872` trafia do klasy „obie strony nazywają co innego" **za naprawę**:
komunikat cytuje nazwę, którą ten commit usuwa z cudzego pola „Weryfikacja".
Klasyfikator nie odróżnia nazwy **używanej** od nazwy **cytowanej po to, by ją
zdjąć** — a to jest ten sam kształt, który 6.D291 zmierzyło na komunikatach bramek
(nazwa jako PRZEDMIOT wobec nazwy jako CYTATU) i który przy 6.D292 zapalił `CLAIM`
na moim własnym raporcie. Trzeci przypadek tej rodziny w jednej dobie; czy warto ją
policzyć osobno, ta pozycja nie pyta.
