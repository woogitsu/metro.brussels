# 6.D159 — poza `tools/` nie ma ANI JEDNEGO modułu, a bramka położenia w pierwszej wersji była bezczynna

**13.09.2026**, na `df0078b`. Wejście: `tools/tests/test_bytecode_staleness.py`
(`sekwencje_ucieczki`, `MAX_SEKWENCJI_UCIECZKI`), `.github/workflows/python-tests.yml`,
`tests/`, `src/`.

Pozycja żądała **liczby złych sekwencji poza `tools/`, per katalog**, i rozstrzygnięcia,
czy bramka je obejmuje. Pole „Skończone, gdy": *dla każdego katalogu z Pythonem w drzewie
wiadomo, czy bramka go czyta i czy CI go kompiluje.*

## 1. PRZESŁANKA POZYCJI JEST NIEPRAWDZIWA

Pole „Dlaczego to nie jest poszerzenie ścieżki" mówiło, że `tests/` i `src/` *„niosą
Pythona o innym przeznaczeniu (pomocniki testów C#, narzędzia sceny)"*.

**Nie niosą. Ani jednego pliku `.py`.**

```
git ls-files '*.py' | awk -F/ '{print $1}' | sort | uniq -c
    203 tools

find . -name '*.py' -not -path './.git/*' -not -path './tools/*'
    (pusto)
```

Cały Python tego repozytorium — **co do jednego z 203 modułów** — stoi pod `tools/`.
Jest to ósma przesłanka pozycji obalona pomiarem w tym projekcie i w tej sesji trzecia
(po 6.D182 i 6.D180); pole „Skąd" 6.D147, z którego ta pozycja wyrosła, opisywało
katalogi, które istnieją, ale Pythona w nich nie ma.

**Wpis mówił o 202 modułach — jest 203.** Drzewo urosło od 12.09.2026.

## 2. Odpowiedź na pytanie pozycji, i dlaczego liczba nie wystarcza

| pytanie | odpowiedź |
|---|---|
| ile złych sekwencji poza `tools/` | **zero** |
| per katalog | nie ma katalogu, w którym byłoby co liczyć |
| czy bramka je obejmuje | obejmuje **wszystko, co jest** — 203 z 203 |
| czy CI kompiluje | `compileall -q tools` kompiluje **wszystko, co jest** |

**Ale „zero" znaczy tu co innego, niż wygląda.** Odpowiedź „zero złych sekwencji poza
`tools/`" jest prawdziwa **nie dlatego, że tamtejszy Python jest czysty — tylko dlatego,
że tamtejszego Pythona nie ma.** Te dwie odpowiedzi mają tę samą liczbę i różnią się
wszystkim innym: pierwsza mówi „sprawdzone", druga „nie ma czego sprawdzać, a gdy się
pojawi, nikt się nie dowie".

**Dlatego bramka, którą ta pozycja stawia, pilnuje POŁOŻENIA, a nie liczby.** Pierwszy
moduł dopisany poza `tools/` wypada jednocześnie:

- ze skanu `sekwencje_ucieczki` (jego korzeń to `tools`),
- z kroku `compileall -q tools` w CI,
- i z zapadki `BAJTKOD_PO_COMPILEALL_PLIKI`.

Żadna z nich nie zapala się na tym, że coś **poza nimi** istnieje. Nowa bramka jest
jedynym miejscem, które to powie.

## 3. PIERWSZA WERSJA TEJ BRAMKI BYŁA BEZCZYNNA — i pokazała to kontrola, nie ja

Bramka położenia w pierwszym podejściu brzmiała: „czytnik drzewa daje 203 moduły
i żaden nie stoi poza `tools/`". **KN-1 — zawężenie czytnika drzewa do samego
`tools/` — wyszła ZIELONA, a podstawienie weszło** (`diff` to potwierdził).

Powód jest ten sam, który tropi 6.D161: **dopóki cały Python stoi pod `tools/`, czytnik
patrzący na całe drzewo i czytnik patrzący tylko pod `tools/` dają identyczny wynik.**
Bramka była prawdziwa z **pustego zbioru** i przechodziłaby tak samo przy czytniku,
który poza `tools/` nie patrzy wcale — czyli pilnowałaby dokładnie tego, czego miała
pilnować, gdyby kiedykolwiek przestała działać.

Naprawa to **wejście syntetyczne**: katalog tymczasowy z dwoma modułami — jednym
WEWNĄTRZ gałęzi narzędzi i jednym POZA nią — na którym czytnik **musi** zwrócić ten
drugi. Po niej KN-1 zapala **dwa** testy i wypisuje wszystkie 203 moduły jako „poza".

(Nazwy tych dwóch plików stoją w kodzie testu, a nie tutaj, i to jest konieczność, nie
styl: bramka `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie` żąda,
żeby każda ścieżka zacytowana w raporcie istniała — a te dwie z założenia nie istnieją,
bo żyją w katalogu tymczasowym przez trzy linijki. Złapała mnie na tym przy pierwszym
przebiegu.)

**To jest czwarty raz w tej sesji, kiedy zielona kontrola coś znaczyła** — ale
pierwszy, w którym znaczyła **prawdę o mojej bramce**, a nie o podstawieniu, które
nie weszło (6.D182 KN-5, 6.D183 KN-3, 6.D157 KN-1/KN-2) ani o kontroli pustej
z konstrukcji (6.D180 KN-3). Zielona kontrola negatywna ma cztery różne przyczyny
i wszystkie wyglądają tak samo.

## 4. Trzy bramki

| test | co pilnuje |
|---|---|
| `test_caly_Python_drzewa_stoi_pod_tools` | 203 moduły, zero poza `tools/` |
| `test_czytnik_drzewa_WIDZI_modul_poza_tools_gdy_taki_jest` | **że powyższa nie jest tautologią** — §3 |
| `test_skan_sekwencji_czyta_KAZDY_modul_drzewa_a_nie_tylko_swoj_katalog` | zasięg skanu == całość drzewa == cel `compileall` |

Trzecia wiąże trzy liczby, które dotąd stały osobno: ile modułów widzi skan, ile ma
drzewo i ile kompiluje CI. Dopóki są równe, „bramka czyta wszystko" jest zdaniem
sprawdzonym, a nie założonym.

Dochodzi do nich `test_skan_ZNAJDUJE_zla_sekwencje_poza_tools_gdy_taka_jest` —
kontrola, że sam **skan sekwencji** nie jest ślepy poza własnym katalogiem, na
katalogu tymczasowym z jednym `\d`.

## 5. Kontrole negatywne — trzy, wszystkie czerwone

Baza: **22/22** w module. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | czytnik drzewa patrzy tylko pod `tools/` | **20/22** |
| KN-2 | skan sekwencji ignoruje podany korzeń | **20/22** |
| KN-3 | `KATALOG_Z_PYTHONEM` wskazuje inny katalog | **20/22** |

KN-1 jest tą, która **przed naprawą z §3 wychodziła zielona**. Dziś zapala bramkę
położenia i kontrolę syntetyczną naraz — czyli obie połowy mechanizmu są sprawdzane.

## 6. ROZSTRZYGNIĘCIE: ani zakres bramki, ani zakres kroku w CI nie rośnie

Pole „Dlaczego to nie jest poszerzenie ścieżki" kazało **najpierw policzyć, a dopiero
liczbie rozstrzygnąć**, czy rośnie zasięg bramki, czy zasięg kroku CI. Liczba wynosi
**zero modułów poza `tools/`**, więc **nie rośnie żaden z dwóch** — nie ma czego objąć.

Nie jest to jednak „nic do zrobienia": dokładnie dlatego, że dziś pokrycie wynosi sto
procent, **jedyną rzeczą wartą dołożenia jest zdanie, które zapali się w dniu, w którym
przestanie**. I to zostało dołożone.

## 7. Czego świadomie nie zrobiłem

- **Nie poszerzyłem `sekwencje_ucieczki` ani kroku `compileall`** — §6 mówi dlaczego,
  liczbą.
- **Nie tknąłem treści żadnego literału** i nie zmieniłem kroku CI — pole „Poza
  zakresem" zabrania obu.
- **Nie dopisałem bramki na `git ls-files`** obok tej na `tree_walk`. Oba czytniki
  dałyby dziś tę samą odpowiedź, a różnica między nimi (plik nieśledzony jest dla
  `git ls-files` niewidzialny) jest przedmiotem otwartej pozycji **6.D165** — dołożenie
  drugiego czytnika tutaj rozstrzygałoby ją po cichu i przy okazji.
