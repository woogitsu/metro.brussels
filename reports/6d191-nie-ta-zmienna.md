# 6.D191 — zjawisko jest możliwe, a pięć prób mierzyło nie tę zmienną

**13.09.2026**, na `a344f0f`. Wejście: `tools/tests/mutation_sweep.py` (`zapisz_pokrycie`,
`PROCES_ZNACZNIK`), `tools/tests/test_mutation_sweep.py`
(`test_plik_posredni_mapy_pokrycia_jest_wlasny_dla_procesu`),
`reports/6d161-zdania-ubezpieczenia.md`.

## 1. Czego pozycja żądała

Rozstrzygnięcia, czy okno zepsucia mapy pokrycia **istnieje** — z liczbą wyprowadzoną
ze ścieżki zapisu, a nie z kolejnych prób — a jeśli istnieje, ile prób trzeba, żeby
jego nietrafienie coś znaczyło.

Pozycja stawiała też hipotezę: jeśli okno nie istnieje, bo każdy pisarz pisze do własnej
nazwy pośredniej, to ubezpieczenie staje się **zdaniem o niemożliwości**, które wolno
zapisać jako pewnik.

## 2. ROZSTRZYGNIĘCIE: okno istniało, jest szerokie, a zjawisko zachodzi

**Hipoteza pozycji jest nieprawdziwa i odwrotność też nie jest tym, czego szukała.**
Pytanie „ile prób" nie ma tu zastosowania, bo mechanizm **nie zależy od zegara**:
odtwarza się za pierwszym razem, deterministycznie.

Trzy liczby, każda zmierzona:

| co | ile |
|---|---|
| szerokość okna: sam zapis mapy ~50 MB (39 877 908 B) | **2,360 s** |
| zepsucie pliku docelowego, mapy RÓŻNE, 8-40 MB, bariera startu | **12 / 20 prób** |
| zepsucie pliku docelowego, mapy TE SAME | **0 / 20 prób** |

Okno nie było więc wąskie — było **sekundowe**. Pięć prób z 6.D106 trafiło w nie pięć
razy na pięć i nic nie zobaczyło, bo **zmienną nie jest szerokość okna, tylko różnica
treści**: dwa strumienie zapisujące identyczne bajty nie mają czego przepleść.

To jest piąty rodzaj „zielonej kontroli" tropiony w tym projekcie od 6.D27, ale
w wydaniu, którego wcześniej nie było: **próba była prawidłowa, przyrząd działał,
a mierzona zmienna była nie ta.** Powtórzenie takiej próby sto razy daje sto zieleni
i ani jednego bitu informacji.

## 3. Druga połowa, przeoczona zupełnie: awaria zachodzi ZAWSZE

Przy wspólnej nazwie pośredniej **drugi `os.replace` nie ma czego przenieść**, bo
pierwszy już przeniósł plik:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '/tmp/…/pokrycie.json.czesciowy' -> '/tmp/…/pokrycie.json'
```

W **20 próbach na 20**, w obu wariantach treści, jeden z dwóch procesów padał z tym
wyjątkiem. Stara nazwa wywracała więc przebieg w stu procentach wypadków i niezależnie
od treści — a patrzono wyłącznie na plik docelowy, więc tej połowy nie zobaczył nikt.

**Osobna nazwa pośrednia nie jest zatem ubezpieczeniem od zjawiska nieodtworzonego.
Jest naprawą usterki w stu procentach powtarzalnej**, której nie zmierzono, bo się na
nią nie patrzyło. Oba zdania rodziny 6.D161 są przez to przepisane, a nie dopisane obok.

## 4. Czy wariant „mapy różne" jest osiągalny w produkcji — tak, ZAWSZE

To jest jedyne miejsce, w którym odpowiedź mogła się jeszcze odwrócić: `zapisz_pokrycie`
dzieli plik docelowy między przebiegami **tego samego commita**, a sweep odmawia na
brudnym drzewie, więc „jeden commit = jedno drzewo = jedna mapa" brzmi jak gwarancja,
że obaj pisarze piszą to samo.

**Nie jest.** Dwa pełne przebiegi sondy pokrycia na tym samym drzewie:

```
przebieg 1: 199 plikow, 35647 wierszy, 534.1 s
przebieg 2: 199 plikow, 35647 wierszy, 529.8 s
pliki tylko w 1: ['tools/tests/test_dwa_k4fq83sx/test_dwa_testy.py',
                  'tools/tests/test_pusty_oaga7ble/test_bez_zadnego_testu.py',
                  'tools/tests/test_wiele_yhdqzn35/test_drugi_modul.py',
                  'tools/tests/test_wiele_yhdqzn35/test_pierwszy_modul.py']
pliki tylko w 2: ['tools/tests/test_dwa_zu29qhn0/test_dwa_testy.py',
                  'tools/tests/test_pusty_lvl_gofr/test_bez_zadnego_testu.py',
                  'tools/tests/test_wiele_autj3o_1/test_drugi_modul.py',
                  'tools/tests/test_wiele_autj3o_1/test_pierwszy_modul.py']
plikow o roznym zbiorze wierszy: 0
MAPY ROZNE
```

Liczby modułów i wierszy zgadzają się co do jednego, **a mapy są różne** — bo
`test_module_entrypoints.py` buduje drzewa próbne przez
`tempfile.TemporaryDirectory(dir=TESTY, prefix="test_dwa_")` (i `test_wiele_`,
`test_pusty_`), czyli **wewnątrz `tools/tests/`, z losowym przyrostkiem**. A
`METRO_COVER_ROOT` wskazuje właśnie `tools/`, więc tropiciel zapisuje te ścieżki
jak każde inne.

Cztery klucze mapy niosą więc losową nazwę katalogu i **żadne dwa przebiegi nie dadzą
tej samej mapy**. Wariant, który psuje plik w 12 przypadkach na 20, jest w produkcji
nie tylko osiągalny — jest jedynym, jaki zachodzi.

## 5. Wejście syntetyczne: bez zegara, bez procesów, za pierwszym razem

Dwa procesy dają przeplot, w który trzeba **trafić**, więc jego nietrafienie nie znaczy
nic — dokładnie to obalił §2. Wejście w drzewie używa więc **dwóch uchwytów na jednej
ścieżce**: mają to samo, co para procesów (własne offsety, obcięcie przy otwarciu),
ale przeplot jest **wymuszony**, a nie wylosowany.

| wariant | plik pośredni | `os.replace` |
|---|---|---|
| nazwa WSPÓLNA (sprzed 10.09.2026) | nieczytelny | `["przeszla", "brak_pliku"]` |
| nazwa Z ELEMENTEM PROCESU (dziś) | oba czytelne | `["przeszla", "przeszla"]` |

Pisarze robią w obu wariantach **dokładnie to samo** — różni się wyłącznie nazwa pliku
pośredniego. To jest cała asercja tego wejścia.

**Pierwsza wersja tego wejścia wyszła ZIELONA i to jest osobne znalezisko.** Miałem
obie mapy tej samej długości — a obie zaczynają się tym samym prefiksem
(`{"wersja": 1, "commit": …`), więc dłuższy pisarz nadpisał krótszego **co do bajtu**
i plik wyszedł poprawny. Zepsucie wymaga, żeby pisarz, który jest **dalej**, dopisywał
za końcem tego, co zapisał drugi: dopiero wtedy między nimi zostaje dziura wypełniona
zerami. Wejście ma dziś asercję na ten warunek, żeby cicho nie przestało go spełniać.

Jest to ta sama usterka co w 6.D106, popełniona drugi raz, w innej skali: **model,
w którym obaj pisarze piszą prawie to samo, mierzy nie tę zmienną.**

## 6. Osiem kontroli negatywnych, baza 169/169, ani jedna zielona

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | wariant „stara nazwa" dostaje jednak DWIE różne nazwy | 168/169 |
| KN-2 | `zapisz_pokrycie` wraca do wspólnej nazwy (stan sprzed 10.09.2026) | 168/169 |
| KN-3 | obie mapy identyczne — **błąd 6.D106 popełniony ponownie** | 168/169 |
| KN-4 | pisarz A nie jest dalej niż koniec B (dziura znika) | 168/169 |
| KN-5 | przeplot zdjęty — ale podstawienie zmieniało DWIE rzeczy | 168/169 |
| KN-5b | przeplot zdjęty JEDNĄ zmianą: B kończy, zanim A otworzy | 168/169 |
| KN-6 | `PROCES_ZNACZNIK` stały, nie per proces | 168/169 |
| KN-7 | jedno zdanie wraca do worka bez pokrycia | 168/169 |

**KN-3 jest tu najważniejsza, bo jest kontrolą na MOJĄ WŁASNĄ pomyłkę z §5:**

```
FAIL … pisarz A nie jest DALEJ niż koniec pisarza B (588-16 vs 588) —
     wtedy nie ma dziury i wejście przestaje ćwiczyć mechanizm, który ma ćwiczyć
```

Czyli: gdy ktoś kiedyś zrówna obie mapy — a to jest dokładnie ruch, przez który
6.D106 nic nie zobaczyło — wejście **nie wychodzi zielone**, tylko zapala się na
warunku dziury. Bez tej asercji powtórzenie tamtego błędu byłoby niewidoczne.

**KN-5 wyszła czerwona, ale na niewłaściwej asercji, i to jest zapisane, a nie
przemilczane.** Podstawienie miało zdjąć przeplot, a zmieniało przy okazji to, co pisze
A (ogon lądował dwa razy), więc zapaliła połowa o OSOBNYCH nazwach. Dwie zmiany naraz
w kontroli negatywnej to ten sam ruch, którym psuje się pomiar — więc kontrola została
powtórzona jako **KN-5b**, z jedną zmianą: pisarz B kończy całą pracę, zanim A w ogóle
otworzy plik. Zapala wtedy właściwa asercja („wspólna nazwa dała plik CZYTELNY").

**KN-6 pilnuje ogniwa, którego wejście syntetyczne nie dotyka:** model używa dwóch
napisów zamiast dwóch procesów, więc to KN-6 odpowiada za zdanie „dwa PROCESY naprawdę
biorą różne nazwy".

```
FAIL … plik POŚREDNI jest ten sam w dwóch procesach:
     /tmp/metro-pokrycie-abc1234.json.czesciowy-6d363a7c
```

## 7. Czego ta pozycja NIE rozstrzygnęła

**Ile prób trzeba** — pytanie zostaje bez odpowiedzi i to jest poprawny wynik, a nie
brak. Nie trzeba żadnej: mechanizm jest deterministyczny, więc liczba prób nie jest
tu wielkością, która cokolwiek mierzy. Gdyby kiedyś stanął tu mechanizm naprawdę
losowy, pytanie wróci — ale wtedy będzie dotyczyło **znanego okna**, a nie cierpliwości.

## 8. Czego świadomie nie zrobiłem

- **Mechanizmu nazwy pośredniej nie ruszyłem** — pole „Poza zakresem". Pomiar mówi,
  że dzisiejszy jest poprawny, więc nie było zresztą po co.
- **Przeglądu mutacyjnego nie przyspieszałem** — to samo pole.
- **Losowych nazw katalogów próbnych w `test_module_entrypoints.py` nie tknąłem**,
  choć to one czynią mapy różnymi. Zmiana tam byłaby poszerzeniem pozycji o cudzy
  moduł, a mapa i tak ma dziś osobną nazwę pośrednią, więc nic się na tym nie psuje.
  Zapisane jako materiał, nie jako usterka.
- **`reports/6d161-zdania-ubezpieczenia.md` nie przepisany** — raport mówi o swoim
  dniu pomiaru i dalej jest prawdziwy (6.D108). Tak samo `reports/6d106-…`.

## 9. Zauważone po drodze, nie tknięte

- **Trzy zdania prozy w `test_assertion_gate.py` były nieprawdziwe od 6.D165, czyli od
  następnego dnia po pomiarze, i nie złapała tego żadna bramka.** „Wszystkie osiemnaście"
  i „osiemnaście / dziewięć / dziewięć" stały w czasie teraźniejszym obok stałych
  mówiących 19 i 10. `test_prose_counts.py` istnieje dokładnie po to, ale czyta **cyfry**,
  a te liczby stały **słownie**. Przepisałem je, bo dwie z nich psuje ta pozycja
  (los „ubezpieczenie przyjęte świadomie" ma dziś zero członków) — ale **luki w bramce
  nie załatałem**: to jest cudzy moduł i inna pozycja. Materiał dla rodziny 6.D166.
- **`reports/6d106-nazwy-plikow-tymczasowych-sweepa.md` (w. 85-86)** mówi „**i tak jest
  opisane w kodzie oraz w docstringu testu**" — pierwsza połowa tego zdania jest datowana,
  druga mówi o kodzie DZISIEJSZYM i od tej pozycji jest nieprawdziwa. Raportu nie ruszam
  (6.D108), ale jest to ten sam kształt, o który pyta 6.D196: zdanie o dniu pomiaru
  wtopione w zdanie o stanie bieżącym.
- **Mapy dwóch przebiegów różnią się przez losowe nazwy katalogów próbnych** budowanych
  przez `test_module_entrypoints.py` WEWNĄTRZ `tools/tests/`. Poza tym, że czyni to wariant
  „mapy różne" jedynym osiągalnym (§4), znaczy też, że mapa pokrycia jako pamięć podręczna
  commita **nigdy nie trafia w to samo** w czterech kluczach. Nie tknąłem: cudzy moduł,
  a przy osobnej nazwie pośredniej nic się na tym nie psuje.
