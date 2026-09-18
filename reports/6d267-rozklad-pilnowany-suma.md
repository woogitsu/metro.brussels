# 6.D267 — rozkład pilnowany samą sumą: teza pozycji nie przeżyła pomiaru

**Data:** 18.09.2026 · **Gałąź:** `claude/6d267-rozklad-pilnowany-suma` · **Baza:** `62fcf2f`

## 1. Trzy liczby, których żądało pole „Wyjście"

Wyliczeń o kształcie „nazwa + liczba, trzy pary albo więcej" stoi w zasięgu
**dziesięć**: siedem w prozie pythonowej pod `tools/tests/`, dwa w markdownie
(`docs/`, `CLAUDE.md`) i jedno, które jest akapitem opisującym pozostałe dziewięć.
Stała trzymająca sumę istnieje dla **jednego**. Rozkładów rozjeżdżających się dziś
ze stanem drzewa jest **zero**.

Zasięg wyklucza `reports/` — tego żądało pole „Poza zakresem" — oraz `docs/TASKS.md`,
i to drugie jest rozstrzygnięciem tej pozycji, nie przeoczeniem: wiersz ZROBIONE
i pole „Skąd" są zapisem pomiaru z jego dnia, czyli dokładnie tym, czym raport,
a powód wykluczenia `reports/` był właśnie ten. Wykluczenie odrzuca **7** wyliczeń
i liczba ta stoi przybita w `WYLICZEN_Z_TASKS`, żeby dała się sprawdzić, a nie
tylko przeczytać (6.D243 w drugą stronę).

## 2. Główne znalezisko: kształt „nazwa + liczba" zlewa cztery różne związki

Trzecia liczba nie jest wynikiem tego sita i to jest treść tej pozycji. Rozkładem —
całością podzieloną na nazwane części — jest **jeden** z dziesięciu trafień:

| klasa | ile | przykład |
|---|---|---|
| ROZKŁAD | 2 (ten sam w dwóch miejscach) | `tools/tests` 139, `tools/blender` 29, … = 210 |
| WARTOŚĆ STAŁEJ | 2 | `DEFAULT_RING_STEP_M` 5, `DEFAULT_STATION_HALO_M` 90, … |
| LUZ PROGU, nie wartość | 1 | luz 8 przy progu `MIN_GAME_MESSAGES`, luz 9 przy `MIN_MESSAGES`, … |
| CYTAT BŁĘDNEGO ODCZYTU | 1 | odczyt 72 przy `NIEROZSTRZYGNIETYCH`, odczyt 15 przy `MINIMUM_CLAIMS`, … |
| ŁAŃCUCH REWIZJI | 1 | `D240` 1005, `D241` 1011, … |
| PARAMETRY SCENY | 1 | `depth_m` 30, `slab_radius_m` 40, … |
| OPIS CUDZYCH WYLICZEŃ | 1 | akapit nad samą bramką |

**Gdyby sito uznało każdą parę „nazwa + liczba" za człon rozkladu, fałszywych
alarmów byłoby dziewięć z dziesięciu.** Dwa przypadki są tu dosadne:

* `test_game_needle_specificity.py` podaje przy nazwach progów **ich luz**, a nie
  ich wartość: wylicza, ile każdy z czterech progów przepuszczał — osiem,
  dziewięć, dwa i jeden — przy wartościach, które wynoszą dziś odpowiednio 142,
  97, 68 i 18. Sito czytające ten kształt jako „stała + wartość" zgłasza cztery
  rozjazdy i **wszystkie cztery są fałszywe**.

  **Bramka `test_every_constant_quoted_in_a_report_carries_the_value_from_the_code`
  zapaliła się na PIERWSZEJ WERSJI TEGO AKAPITU** i miała rację: przepisując
  tamto zdanie w kształcie „`STALA` N" wprowadziłem do raportu dokładnie ten
  fałszywy kształt, który raport opisuje. Nie jest to powód do wyjątku — jest to
  powód, żeby zdanie napisać tak, jak znaczy: liczba stoi PRZED nazwą i nazwana
  jest luzem. Ten sam zabieg zastosowany do cytatów z `test_report_claims.py`.
* `test_report_claims.py` cytuje odczyty, które ten sam akapit nazywa usterkami —
  „cytat BŁĘDNEGO odczytu, opisany jako błędny". Bramka na te cztery pary zapalałaby
  się na **prawidłowej** prozie, czyli poszłaby do wyłączenia: kształt 6.D27.

Złapane czytaniem źródła, nie przez bramkę. Dlatego przybita jest **klasa** każdego
wyliczenia, a nie sama ich liczba.

## 3. Teza pozycji jest FAŁSZYWA w postaci ogólnej, a prawdziwa w jednym punkcie

Pole „Skąd" twierdziło, że kształt „wyliczenie składników przy przybitej sumie"
powtarza się przy rozkładzie sześciu postaci literału, przy trzech podłogach
deklaracji C# i przy rozkładzie klas zapadek. Sprawdzone wprost, po kolei:

| kandydat | jak jest pilnowany | teza |
|---|---|---|
| `ROZKLAD_POSTACI` (sześć postaci literału) | **równość PER KLUCZ** wobec drzewa, `test_csharp_test_methods.py:683` | fałszywa |
| klasy zapadek | **równość na czwórce** `(18, 3, 47, 2)`, `test_tree_walks.py:1331` | fałszywa |
| gałęzie deklaracji C# | **trzy PODŁOGI**: `MINIMUM_CONST = 258`, `MINIMUM_STATIC_READONLY = 72`, `MINIMUM_BEZ_MODYFIKATORA = 36` | prawdziwa, ale inaczej |

Dwa z trzech kandydatów są pilnowane per człon. Trzeci ma człony pilnowane —
ale **podłogami, nie równościami**, i to jest dziura innego kształtu niż ta,
której pozycja szukała: przesunięcie między `const` i `static readonly`, które
zostawia oba nad ich podłogami, przechodzi w milczeniu przy niezmienionej sumie
nad `MINIMUM_DEKLARACJI = 330`. Nie jest to dziura SUMY, tylko dziura PODŁOGI.
Zapisane jako pozycja 6.D270; ta pozycja jej nie zamyka, bo pole „Poza zakresem"
wyklucza zakładanie zapadek na znalezione rozkłady.

**Jest to trzecia z rzędu pozycja mojego autorstwa, której teza nie przeżyła
pomiaru** (6.D262 i 6.D263 wcześniej), i trzeci raz powód jest ten sam: napisałem
ją, cytując dowody z zakresu, którego bramka nie używa. Tam były to zdania
ogłaszające pomiar; tu — trzy kandydatury wpisane z pamięci, bez sprawdzenia,
czym są pilnowane.

## 4. Dwie usterki własnego czytnika, obie złapane przed commitem

1. **Pusty wiersz `#:` jest granicą akapitu i bez tego sito zgłaszało dziurę
   dokładnie tam, gdzie stoi bramka.** Sklejanie wszystkich kolejnych wierszy
   komentarza dawało rozkładowi modułów sumę **346** zamiast 210, bo łapało
   jeszcze dawną liczbę z akapitu obok. Suma 346 nie trafia w żadną stałą, więc
   wyliczenie wyglądało na NIEPILNOWANE — a jest pilnowane od 6.D263.
2. **„Suma trzymana przez stałą" dopasowana po WARTOŚCI jest zbiegiem cyfr.**
   Pierwsza wersja szukała sumy w stałych całego drzewa: suma 200 „trafiła"
   w `MIN_PODPISOW_POMOCNIKA = 200`, z którym rozkład modułów nie ma nic
   wspólnego. Różnych wartości całkowitych w stałych `tools/` jest tylko 90,
   więc trafienie przypadkowe jest niemal pewne. Warunek idzie teraz po
   **tym samym module**. Jest to trap z 6.D264, popełniony dobę po jego opisaniu.

Trzecia rzecz nie była usterką czytnika, ale kosztem: `paragraphs` skleja kolejne
wiersze tabeli markdown, więc jedno „wyliczenie" z `docs/TASKS.md` niosło ~150 nazw
z jednego wiersza ZROBIONE. Wykluczenie `TASKS.md` zdejmuje to razem z powodem.

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Na kopii drzewa, z czyszczonym `__pycache__` (6.D102), każda z asercją,
że mutacja wylądowała.

| kontrola | przewidziane | zmierzone |
|---|---|---|
| KN-a: nowy akapit `#: \`x\` 1, \`y\` 2, \`z\` 3` | czerwień, odcisk `('x','y','z')` bez klasy | `FAIL … wyliczenia bez klasy: [('test_module_entrypoints.py', ('x', 'y', 'z'))]`, 13/14 |
| KN-b: `tools/tests` 139→138 i `tools/blender` 29→30, **suma 210 bez zmian** | census ZIELONY, 6.D263 CZERWONY | `test_prose_counts` 14/14; `FAIL test_oba_zdania_o_rozkladzie_niosa_TE_SAME_liczby: komentarz w tym module nie niesie pary tools/blender = 29` |
| KN-c: podmiana `D247`→`D999` we wpisie klasy | czerwień z OBU stron | `wyliczenia bez klasy: [… 'D247')]; wpisy bez wyliczenia w drzewie: [… 'D999')]` |

**KN-b jest całą treścią tej pozycji w jednym przebiegu:** census pilnuje
ISTNIENIA wyliczenia, a nie jego członów, i przy przesunięciu w rozkładzie
pozostaje zielony — zapala bramka 6.D263, która człony porównuje. Podział jest
zamierzony: census ma zapalać na wyliczeniu NOWYM i niesklasyfikowanym, bo to
ono może być rozkładem pilnowanym samą sumą.

Pierwsze podejście do KN-a dało `FAIL … No such file or directory: '.gitignore'` —
błąd środowiska kopii, nie zapalenie bramki. Odnotowane, bo czyta się identycznie
jak czerwień, której się oczekuje, a nie jest nią; dopiero dołożenie `.gitignore`
do kopii dało bazę 14/14 i kontrolę wartą czegokolwiek.

## 6. Kontrola przyrządu

```
dwie pary            -> 2 pary,  < MINIMUM_PAR_ROZKLADU  (nie jest rozkładem)
trzy pary            -> 3 pary, == MINIMUM_PAR_ROZKLADU  (jest)
odsyłacze `plik.md 127 …` -> []  (odsyłacz nie jest członem)
akapit z pustym `#:` -> 2 akapity po dwie pary  (granica trafiła)
```

Próg dwóch par odrzucony wprost, bo przy znanej sumie dwie pary wyznaczają się
nawzajem — tego żądało pole „Weryfikacja".

## 7. Akapit, który liczy sam siebie

Bramka zapaliła się przy pierwszym przebiegu na **własnym akapicie opisującym
pomiar**, bo ten wymienia po nazwie członów cudzych wyliczeń. Wycięcie go
wymagałoby wyjątku na „akapit o bramce", a taki wyjątek zdejmuje z zasięgu także
każdy przyszły akapit tego kształtu — czyli dokładnie te, których bramka ma
pilnować. Akapit ma więc własną klasę i liczy się do dziesiątki, a zdanie o tym
stoi w nim samym.

## 8. Czego świadomie nie zrobiono

Zapadek na znalezione rozkłady — wyklucza to pole „Poza zakresem", a dziura
podłogowa z §3 jest zapisana jako 6.D270. Liczb w rozkładach nie poprawiano,
bo żadna nie okazała się nieprawdziwa. `reports/` i `docs/TASKS.md` poza zasięgiem,
z powodem i z liczbą odrzuconych.

Bramka weszła do `test_prose_counts.py`, a nie do `test_bytecode_staleness.py`,
którą nazywało pole „Weryfikacja" tej pozycji. Pole było napisane źle: modułem
o „liczbie wpisanej w prozę obok bramki, porównywanej z tym, co bramka mierzy"
jest `test_prose_counts.py` i to tam stoją już czytniki tego rodzaju (6.D213).
`test_bytecode_staleness.py` trafiło do tamtego pola tylko dlatego, że 6.D263
umieściło w nim `ROZKLAD_MODULOW`.
