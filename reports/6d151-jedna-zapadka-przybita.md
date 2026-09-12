# 6.D151 — jedna zapadka przybita: `MIN_GAME_NEEDLES`, luz 14 igieł, koszt 5 z 11 rewizji

**12.09.2026**, na `3675007`. Wejście: `tools/tests/test_game_needle_specificity.py`,
`tools/tests/test_needle_specificity.py`, `tools/tests/test_tree_walks.py`.
Pozycja: zapadek wolnych jest 24, z czego 17 to progi `MIN_`/`MINIMUM_`; kształt
`len(x) >= MIN_Y` nie zapala się przy **obniżeniu** progu, a obniżenie jest właśnie
tym ruchem, który zwalnia bramkę z pilnowania.

## 1. Którą wybrałem i dlaczego — luz każdej z pięciu

Rodzina z pola „Dlaczego" to progi liczące trafienia skanu. Zmierzone 12.09.2026:

| próg | wartość | dziś w drzewie | **luz** | |
|---|---:|---:|---:|---:|
| `MIN_GAME_NEEDLES`, przed tą pozycją | 45 | **59** | **14** | **24 %** |
| `MIN_MESSAGES` | 97 | 106 | 9 | 8 % |
| `MIN_GAME_MESSAGES` | 142 | 150 | 8 | 5 % |
| `MIN_NEEDLES` | 68 | 70 | 2 | 3 % |
| `MIN_GAME_SOURCES` | 18 | 19 | 1 | 5 % |

**Luz to liczba, która może zniknąć, zanim próg cokolwiek powie.** `MIN_GAME_NEEDLES`
miał go największy — czternaście igieł, czyli co czwarta, mogło wyparować
z `tests/Game.Tests` w ciszy.

## 2. Co ten luz naprawdę przepuszczał — zmierzone, nie opisane

KN-3b zdejmuje z drzewa **jedną** asercję (`Assert.IsTrue(… Contains("--calls") …)`
w `RunPlanTests.cs:767`), czyli jedną igłę z pięćdziesięciu dziewięciu.

| kształt zapadki | wynik |
|---|---|
| po tej pozycji (`== 59`) | **26/27** — `wzorzec zlapal 58 roznych igiel, a zapadka stoi na 59` |
| przed nią (`>= 45`) | **10/10 ZIELONE** |

Ta sama utrata, ten sam moduł, dwa różne werdykty. To jest cała treść pozycji:
**przed nią igła mogła zniknąć i nie zgłaszało tego nic.**

## 3. Koszt, o który pole „Skończone, gdy" prosiło

**Zmierzony z historii, nie oszacowany.** Gdyby stała była przybita od początku,
trzeba by ją poprawić w **5 z 11** rewizji dotykających `tests/Game.Tests`:

```
e237717 2026-09-07  igiel= 45
a9d9f85 2026-09-08  igiel= 45
dba5737 2026-09-09  igiel= 49  <-- ZMIANA   6.B43
e12094c 2026-09-10  igiel= 49
e73680b 2026-09-10  igiel= 52  <-- ZMIANA   6.D83
e5c499e 2026-09-10  igiel= 54  <-- ZMIANA   6.D99
f9fdb31 2026-09-11  igiel= 54
3fa2bec 2026-09-11  igiel= 54
dfc7543 2026-09-11  igiel= 57  <-- ZMIANA   6.D130
0279704 2026-09-11  igiel= 57
8608c7c 2026-09-11  igiel= 59  <-- ZMIANA   6.D143
```

**45 % rewizji, jeden wiersz za każdym razem.** Dla porównania `MIN_REPORTS`
poprawiam przy **każdym** raporcie, czyli w 100 % pozycji — tax jest więc poniżej
normy tego repozytorium, a nie powyżej.

### Czego z tej liczby NIE da się wyprowadzić dla pozostałych dwudziestu trzech

Luz policzyłem dla pięciu (tabela w sekcji 1) i dla każdej kolejnej da się policzyć
tak samo — to jest strona **korzyści**. Strona **kosztu** wymaga przejścia po historii
plików, które dana zapadka mierzy, i policzenia, w ilu rewizjach jej liczba się
zmieniła. Przepis jest w `reports/` powyżej i zajmuje kilkanaście wierszy, ale wynik
zależy od populacji: zapadka mierząca rzadko ruszany katalog kosztuje mniej niż ta
mierząca `tests/`. Przenoszenie 45 % na pozostałe byłoby dokładnie tym, czego ta
pozycja unika.

## 4. Nazwa zostaje `MIN_`, i to jest zgodne z konwencją

Przedrostek nazywa stronę **zakazaną**, a równość strzeże **obu** — mówi to wprost
docstring `klasa_zapadki` w `test_tree_walks.py`: „Równość strzeże w obie".
W rejestrze stoi już siedem zapadek `MAX_` przybitych równością, więc para
„przedrostek + równość" jest tu wzorcem, a nie wyjątkiem.

**Wartość zmieniona z 45 na 59 nie jest przestrojeniem progu.** Pin musi równać się
temu, co pinuje, inaczej jest czerwony od pierwszego dnia; stara liczba stoi
w komentarzu jako historia, nie jako druga prawda. Pole „Poza zakresem" zabrania
przestrajania progów — a przestrojenie to ruch, który robi MIEJSCE; ten ruch je
zabiera.

## 5. Kontrole negatywne

Baza: **27/27** na parze modułów. Po każdej `cp` z kopii i `md5sum -c: OK` na trzech
plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | zapadka o jeden w dół (59 → 58) | **26/27** | ruch w zakazaną stronę pada |
| KN-1b | to samo przy STARYM kształcie (`>= 58`) | **26/27** | **pinu nie da się cicho cofnąć** — patrz niżej |
| KN-2 | zapadka o jeden w górę (59 → 60) | **26/27** | równość strzeże obu stron |
| KN-3b | jedna igła ZNIKA z drzewa | **26/27** | to, co luz przepuszczał |
| KN-3c | ta sama utrata przy `>= 45` | **10/10 ZIELONE** | pomiar „przed", sekcja 2 |
| KN-4 | klasa w `ZAPADKI` zostawiona na `WOLNA` | **26/27** | rejestr z 6.D133 żąda zgodności |
| KN-5 | liczby zbiorcze zostawione na 14/3/24/1 | **26/27** | suma klas nie jest ozdobnikiem |

### KN-1b jest tu wynikiem, nie formalnością

Przywrócenie kształtu `>=` razem z obniżoną wartością **nie zapala testu igieł**
(59 ≥ 58 przechodzi) — zapala **rejestr klas z 6.D133**:

```
zapadka zmieniła klasę (nazwa, było, jest): [('MIN_GAME_NEEDLES', 'przybita', 'wolna')]
— zmiana W STRONĘ `wolna` znaczy, że komuś ubył strażnik
```

Przyrząd z 6.D133 pilnuje więc nie tylko tego, że klasa jest wpisana, ale i tego,
że praca tej pozycji nie zostanie po cichu odwrócona.

### KN-3 wykonałem najpierw źle

Pierwsza próba **osłabiła** igłę (`"--calls"` → `"--"`) zamiast ją zdjąć. Igła nie
zniknęła — zrobiła się nieswoista i zapaliła szczebel 1 oraz kontrolę dodatnią, czyli
dwie bramki, które z tą pozycją nie mają nic wspólnego. Licznik igieł został na 59.
KN-3b zdejmuje całą asercję i dopiero to jest utratą igły.

## 6. Czego nie zrobiono

- **Nie przybito ani jednej więcej** — pole „Poza zakresem" mówi to wprost. Wolnych
  zostaje **23**.
- **Nie zmieniono wartości żadnego progu**, w tym czterech pozostałych z rodziny.
  Ich luz jest zmierzony i stoi w sekcji 1 jako materiał na następną pozycję.
- **Nie policzono kosztu dla pozostałych dwudziestu trzech** — sekcja 3 mówi,
  dlaczego jednej liczby nie wolno tu przenieść, i podaje przepis.
- **Nie tknięto `MAX_GAME_UNMATCHED_NEEDLES`** ani żadnej innej zapadki w tym module.
