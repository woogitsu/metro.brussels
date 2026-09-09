# Piąta kopia wartości progu, w docstringu samej bramki (6.D56)

**Zmierzone 08.09.2026 na:** `3fbc25d`.
**Przyrząd:** `grep -n` po treści `tools/ci/assert_linecore_budget.py`, wzorzec
„słowo *próg* plus liczba" z podziałem po wcięciu wiersza, oraz
`python3 tools/tests/test_linecore_budget_gate.py`.

---

## 1. Co było zepsute

Docstring `tools/ci/assert_linecore_budget.py` mówił:

> `null` zostaje celowo: **próg 8,0 µs** zmierzono na przejeździe **bez** wybiegu

W konfiguracji stało wtedy **14,0**. Liczba w docstringu była więc nie tylko kopią —
była kopią **nieprawdziwą**.

**Historia tej pomyłki jest jej treścią.** Commit #408 przepisał **to samo zdanie**
w `tools/ci/linecore-step-budget.json`, uzasadniając to wprost:

> PRZEPISANE 08.09.2026 w jednym slowie: stala tu WARTOSC progu (8,0), a naglowek
> tego samego pliku zakazuje wpisywania progu dwa razy, bo rozjezdza sie przy
> pierwszej zmianie. Zdanie mowi teraz o wlasnosci przejazdu, nie o liczbie —
> liczba stoi w microseconds_per_step_max i tylko tam.

I docstringu **nie tknął**. Powód:
`test_the_threshold_lives_in_one_place_and_the_step_does_not_compare_anything`
czytał **wyłącznie** `.github/workflows/sim-tests.yml`. Commit, którego tematem było
„liczba ma stać w jednym miejscu", zostawił ją w dwóch — bo bramka jednego miejsca
patrzyła tylko na jedno z nich.

## 2. Naiwne rozszerzenie byłoby ZIELONE nad tą usterką

To jest pomiar, który zdecydował o kształcie bramki, więc stoi przed opisem poprawki.

Oczywiste rozszerzenie brzmi: „wartość progu z konfiguracji nie może występować
w treści `.py`". Zmierzone, ile razy dzisiejsza wartość tam występuje:

```
prog w konfiguracji: 14.0 | repr: 14.0
szukane warianty zapisu: ['14', '14,0', '14.0', '14.000']

--- (pusto = dzisiejszej wartosci progu NIE MA w tresci bramki)
```

**Zero.** Taka asercja przechodziłaby dziś na zielono, a usterka stała trzy wiersze
od jej wzroku — bo kopia nie nosiła wartości **dzisiejszej**, tylko **przestarzałą**.
Zakaz dzisiejszej wartości chroni przed rozjazdem, którego jeszcze nie ma, i nie
widzi rozjazdu, który już jest.

Sprawdzony wzorzec to więc **zdanie prozy twierdzące, ILE wynosi próg**, bez względu
na liczbę:

| gdzie | wcięcie | trafień | co to jest |
|---|---:|---:|---|
| wiersz 21, docstring modułu | 0 | **1** | **usterka** — proza o dzisiejszym progu |
| wiersze 104–105, docstring `niemierzalny()` | 8 | 2 | datowany wypis przebiegu z 07.09.2026 |

## 3. Trójpodział wystąpień — wolno tknąć tylko jedno

Ta pozycja nie mówi „usuń liczbę z pliku", bo w pliku są **dwa różne rodzaje**
wystąpienia i tylko jeden jest usterką. To ten sam podział, który 6.D49 zmierzyło
na nazwach testów.

**Rodzaj pierwszy — proza o progu dzisiejszym (wiersz 21).** Twierdzenie, które musi
nadążać za konfiguracją, a nie nadąża. **Usunięte.**

**Rodzaj drugi — wklejony wypis datowanego przebiegu (wiersze 104–105):**

```
BLAD: koszt kroku 16.022 us przekracza prog 8.000 us
[BUDZET-BRAMKA] ... 16.022 us/krok przy progu 8.000; rozstep powtorzen 115.9 %
```

Poprzedzony w docstringu zdaniem „Zmierzone 07.09.2026 na runnerze `woogitsu-host-08`,
gdy dwanaście jobów liczyło naraz". `prog 8.000 us` jest tu **prawdą o tamtym dniu** —
tamten przebieg naprawdę porównywał się z progiem 8,0. **Zostaje nietknięte.**
Przepisanie tej liczby pod dzisiejszą wartość zamieniłoby zapis pomiaru na zapis
**zmyślony**, czego zabrania `CLAUDE.md` §5 — i to w pliku, którego cała wartość
polega na tym, że wypisy są prawdziwe.

**Rodzaj trzeci — zdanie o historii.** Tu jest rzecz, którą warto zapisać, bo bramka
ograniczyła mnie w trakcie pisania jej samej. Poprawiając wiersz 21, napisałem
najpierw akapit wyjaśniający: „Do 08.09.2026 stało tu »próg 8,0 µs«, czyli liczba,
która była już nieprawdziwa — konfiguracja mówiła wtedy 14,0". Zdanie **prawdziwe**
i historyczne. Ale:

- `grep` z pola „Weryfikacja" natychmiast je znalazł (`kod grepa: 0`, czyli trafienie);
- nowa asercja zapaliłaby się na nim, bo to proza z liczbą przy słowie „próg".

Rozstrzygnięcie: **zdanie historyczne z liczbą jest dla czytającego nierozróżnialne
od zdania o progu dzisiejszym** — a ta właśnie nierozróżnialność była usterką.
Historia idzie więc tam, gdzie pole „Skończone, gdy" umieszcza datowane zapisy: do
`reports/`, czyli do tego pliku. W `.py` zostaje zdanie o **własności** przejazdu
i odsyłacz tutaj.

## 4. Pierwsza wersja wzorca nie widziała słowa „próg"

Wzorzec zaczynał się od `\bpro`, więc **nie pasował do słowa „próg"** — bo `ó` to
inny znak niż `o`. Pomiar tą wersją dał:

```
=== trafienia wzorca "prog + liczba" wg wciecia:
  104: [WKLEJONE WYJSCIE (wciecie 8)] BLAD: koszt kroku 16.022 us przekracza prog 8.000 us
  105: [WKLEJONE WYJSCIE (wciecie 8)] [BUDZET-BRAMKA] ... przy progu 8.000; ...
```

Dwa trafienia, **oba legalne**, zero w prozie — czyli wzorzec meldował, że plik jest
czysty, w chwili gdy usterka stała w wierszu 21. **Bramka byłaby zielona nad usterką,
którą miała łapać**, a jej autor miałby na to wydruk. Litera `ó` stoi dziś w wzorcu
jawnie i jest to opisane przy jego definicji, bo bez tego wygląda jak ozdoba.

Po poprawce wzorca: **1 trafienie w prozie**, wiersz 21.

## 5. Czego bramka NIE sprawdza w `.py`, i to jest wynik pomiaru

Pole „Wyjście" mówi o progu **i o oknie pomiaru**. Zmierzone, ile fałszywych trafień
dałoby szukanie podciągu dla każdej z tych liczb w treści bramki:

| parametr | wartość | trafień | czym są |
|---|---:|---:|---|
| `scenario.steps` | 120000 | **0** | — |
| `scenario.headway_s` | 90 | 1 | `330–390` z akapitu o ekstrapolacji |
| `trains_on_line_expected` | 9 | **17** | daty `05.09.2026`, `group(9)`, liczby w prozie |
| `scenario.repeats` | 9 | **17** | ta sama liczba, te same trafienia |

**Sprawdzane jest więc `steps` (0 fałszywych trafień) i nie są sprawdzane `headway_s`
ani `trains_on_line_expected`.** Bramka o wskaźniku 17 fałszywych alarmów idzie do
wyłączenia (6.D27), a wyłączona bramka nie pilnuje niczego. Te dwie liczby zostają
pilnowane **tam, gdzie otaczający tekst jest krótki**: w kroku CI, przez tę samą
asercję, wyżej w jej treści. To nie jest poluzowanie — przed zmianą nie były
sprawdzane w `.py` wcale, a po zmianie jedna z trzech jest.

## 6. Bramka sprawdza po zmianie WIĘCEJ, nie mniej

Pole „Wyjście" żądało **rozszerzenia** istniejącej asercji, nie nowego testu.

| co sprawdza `test_the_threshold_lives_in_one_place…` | przed | po |
|---|---|---|
| workflow woła skrypt | ✓ | ✓ |
| krok CI nie nosi progu, `steps`, `headway_s` | ✓ | ✓ |
| krok CI nie porównuje sam (`bc`, `awk`, `-gt`…) | ✓ | ✓ |
| **treść `.py` nie nosi `steps`** | — | **✓** |
| **proza `.py` nie twierdzi, ile wynosi próg** | — | **✓** |

## 7. Weryfikacja z pola „Weryfikacja"

```
$ grep -n '8,0 µs\|8\.0 us\|14,0 µs\|14\.0' tools/ci/assert_linecore_budget.py
kod grepa: 1
```

Kod 1 znaczy „brak trafień" — wartości progu nie ma w treści bramki, czego żąda drugi
wiersz pola.

```
$ python3 tools/tests/test_linecore_budget_gate.py
  26/26 przeszło
kod: 0
```

## 8. Kontrole negatywne — dwie, i druga jest ważniejsza

**KN-1, wartość DZISIEJSZA (14,0) wpisana z powrotem do docstringu:**

```
FAIL test_the_threshold_lives_in_one_place_and_the_step_does_not_compare_anything: proza bramki twierdzi, ile wynosi prog — to kopia wartosci poza konfiguracja i rozjedzie sie przy pierwszej zmianie progu:
  21: `null` zostaje celowo: próg 14,0 µs zmierzono na przejeździe **bez** wybiegu, a wybieg
kod: 1
```

**KN-2, wartość PRZESTARZAŁA (8,0) — czyli dokładnie ta usterka, którą pozycja
opisuje:**

```
FAIL test_the_threshold_lives_in_one_place_and_the_step_does_not_compare_anything: proza bramki twierdzi, ile wynosi prog — to kopia wartosci poza konfiguracja i rozjedzie sie przy pierwszej zmianie progu:
  21: `null` zostaje celowo: próg 8,0 µs zmierzono na przejeździe **bez** wybiegu, a wybieg
kod: 1
```

**KN-2 jest ważniejsza od KN-1**, bo naiwny projekt bramki (zakaz dzisiejszej
wartości, §2) przechodziłby KN-1 i **oblewał KN-2** — a to KN-2 opisuje stan, który
w drzewie naprawdę stał.

`md5` `tools/ci/assert_linecore_budget.py` przed pierwszą mutacją i po każdym
przywróceniu: `0dc20ba139fe589372ddfac6df24a68c`. Po każdej mutacji
`find tools -name __pycache__ -type d -exec rm -rf {} +`.

**Pomyłka po drodze, warta zapisania:** pierwszą kontrolę cofnąłem przez
`git checkout tools/ci/assert_linecore_budget.py` — a plik nie był jeszcze
zacommitowany, więc `checkout` usunął **razem z mutacją całą poprawkę**. Wyszło to
z porównania `md5` (`492fa088…` zamiast `0dc20ba1…`), nie z pamięci. Dalsze kontrole
cofane były podmianą odwrotną w Pythonie.

## 9. Trzeci test: druga strona pary

Rozszerzenie z §6 samo w sobie idzie do wyłączenia przy pierwszym fałszywym alarmie,
więc obok stoi `test_datowany_zapis_pomiaru_NIE_jest_kopia_progu_i_bramka_o_nim_milczy`.
Żąda **dwóch rzeczy naraz**, i dlatego nie da się go spełnić przez poszerzenie progu
wcięcia:

1. w treści bramki **musi istnieć** wklejony wypis z wartością progu — inaczej
   rozróżnienie proza/zapis-pomiaru byłoby martwe i nikt by nie zauważył, że zniknęło;
2. **żadna proza** nie może takiej wartości nosić.

## 10. Czego świadomie nie zrobiłem

- **Nie zmieniłem wartości progu** ani granicy rozstępu — zabrania tego „Poza
  zakresem".
- **Nie przepisałem datowanych zapisów** w `reports/` ani wklejonego wypisu
  w `niemierzalny()` (6.D3, `CLAUDE.md` §5).
- **Nie rozszerzyłem bramki na inne stałe** niż próg i okno pomiaru; z okna weszło
  `steps`, a `headway_s` i `trains_on_line_expected` nie — z powodem zmierzonym w §5.
- **Nie dodałem nowego modułu testowego.** „Wyjście" żądało rozszerzenia istniejącej
  asercji i to jest jej rozszerzenie; dołożony jest jeden test pary, w tym samym
  pliku, bo bez niego rozszerzenie nie ma zabezpieczenia od strony 6.D27.

## 11. Zauważone przy okazji, nie tknięte

**Docstring bramki nadal kończy się zdaniem „Próg i scenariusz stoją
w `tools/ci/linecore-step-budget.json`, w jednym miejscu".** To zdanie było prawdziwe
o *zamiarze* i fałszywe o *stanie* przez cały czas, gdy trzy wiersze wyżej stała
kopia. Dziś jest prawdziwe i nic z nim nie robię — ale warto zauważyć, że **zdanie
deklarujące niezmiennik stało obok jego naruszenia** i to nie pomogło nikomu tego
zauważyć. Deklaracja w prozie nie jest bramką; dopiero teraz jest.
