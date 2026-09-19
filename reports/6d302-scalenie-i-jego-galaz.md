# 6.D302 · Para z 6.D293 nie jest wyjątkiem — jest jedną z czterdziestu ośmiu

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `4b3db54`

6.D293 zauważyło, że w klasie „bez raportu" dziesięć commitów okazało się sześcioma
kawałkami pracy, bo jedną z nich była para: scalenie `ead62d2aa1ae` i jego własna
gałąź `c705199f1bb7`. Poprawka dotyczyła **jednej klasy**, bo tylko do niej ktoś
zajrzał. Ta pozycja zagląda do wszystkich trzech.

---

## 1. Trzy liczby, których żądało pole „Wyjście"

```
trzy klasy: {'dotyczy': 157, 'nic_wspolnego': 213, 'bez_raportu': 113} suma: 483
scalen w populacji: 63
scalen oktopusowych: 0
par (scalenie + drugi rodzic OBA w populacji): 48
```

**Para z 6.D293 nie jest wyjątkiem.** Jest jedną z czterdziestu ośmiu, a scaleń
w populacji jest sześćdziesiąt trzy — czyli **przeszło trzy czwarte scaleń wciąga
do populacji także własną gałąź**.

## 2. Rozbicie na klasy i spadek liczności

| klasa | liczność | ile jest drugim rodzicem pary | po policzeniu pary raz |
|---|---|---|---|
| `dotyczy` | 157 | **24** | 133 |
| `nic_wspolnego` | 213 | **17** | 196 |
| `bez_raportu` | 113 | **7** | 106 |

Suma spadków wynosi 48 i równa się liczbie par — każda gałąź jest drugim rodzicem
dokładnie jednego scalenia.

**Największy spadek jest w klasie `dotyczy`, nie w `bez_raportu`.** Przewidziałem
odwrotnie. Klasa, którą 6.D293 poprawiło, ma spadek **najmniejszy** z trzech:
siedem ze stu trzynastu, czyli sześć procent, podczas gdy `dotyczy` traci
dwadzieścia cztery ze stu pięćdziesięciu siedmiu, czyli piętnaście.

## 3. Kontrola przyrządu — zdana

```
KONTROLA PRZYRZADU, para ead62d2aa1ae / c705199f1bb7:
  [('ead62d2aa1ae37c78f929df3b439ae2136b16004', 'bez_raportu',
    'c705199f1bb705abf3feef3f09e918a5bf637554', 'bez_raportu')]
```

Para wychodzi na liście i obie połowy stoją w klasie `bez_raportu` — dokładnie tak,
jak żądało pole „Weryfikacja". Czytnik mierzy więc to samo, co 6.D293.

## 4. Dwadzieścia jeden par ma POŁOWY W RÓŻNYCH KLASACH

To jest znalezisko, którego pytanie nie zakładało, a mój warunek obalenia
przewidział jako możliwość.

Z czterdziestu ośmiu par **dwadzieścia jeden** ma scalenie w innej klasie niż jego
własna gałąź. Kierunek jest jednostronny i mówi coś o tym repozytorium: w każdej
z tych par to **gałąź** trafia do klasy węższej (`dotyczy`), a **scalenie** do
szerszej (`nic_wspolnego`). Przykłady z listy:

```
c1f5618689ac [nic_wspolnego] + 7f7f4b2c6cf7 [dotyczy]
e8db22f07822 [nic_wspolnego] + 3089415ce538 [dotyczy]
efccb6160f9e [nic_wspolnego] + bbf63233b0f7 [dotyczy]
f259d5d4b2ca [nic_wspolnego] + 6e0d525b5fa8 [dotyczy]
f684e40a3af5 [nic_wspolnego] + cf0176343343 [dotyczy]
```

Powód jest zrozumiały po przeczytaniu, co klasa `dotyczy` sprawdza: raport dopisany
w tym samym commicie ma wymieniać nazwę modułu albo zapadki, którą wymienia też
komunikat. Komunikat scalenia jest **inny** niż komunikat gałęzi — przy scaleniu
squashem tytuł bywa przepisany na zdanie o pozycji, a nie o module. Gałąź zachowuje
oryginał i dlatego trafia do klasy ciaśniejszej.

Mój warunek obalenia mówił: „jeśli suma spadków nie równa się liczbie par, znaczy
to, że klasa scalenia bywa inna niż klasa gałęzi — wtedy wypisuję obie klasy przy
każdej parze". Suma **równa się** (48), bo liczę spadek po klasie **gałęzi**, a nie
scalenia; zjawisko jednak zachodzi i jest wypisane, bo warunek je przewidział.

## 5. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | scaleń w populacji: 15–120 | trafione (63) |
| 2 | par: 1–15 | **OBALONE** — 48, ponad trzykrotnie więcej niż górny kraniec |
| 3 | para z 6.D293 na liście, w `bez_raportu` | trafione |
| 4 | najwięcej par w `bez_raportu` | **OBALONE** — najwięcej w `dotyczy` (24) |
| 5 | scaleń oktopusowych zero | trafione |
| 6 | spadek `dotyczy`: 0–3 | **OBALONE** — 24 |
| 7 | suma spadków = liczba par | trafione (48 = 48) |

Cztery trafione, trzy obalone — i **wszystkie trzy obalenia są tym samym błędem
widzianym z trzech stron**: założyłem, że para z 6.D293 jest rzadkim zbiegiem.
Nie jest; scalenie wciągające własną gałąź to w tym repozytorium **norma**, a nie
wyjątek. Przewidywania 2, 4 i 6 upadły razem, bo wszystkie trzy wynikały z tego
jednego założenia.

Tym razem założenie nie było przepisane z cudzego wyniku — 6.D293 nigdzie nie
mówi, że para jest wyjątkiem; to ja domyśliłem to sobie z jej pojedynczości.
**Trzy poprzednie pozycje myliły się na cudzej liczbie, ta na własnym domyśle.**

## 6. Czego świadomie nie zrobiono

- **Nie zmieniono `klasy_sladu`, `DIFF_SCALENIA` ani żadnej podłogi** — pole
  „Poza zakresem", a obecność scaleń w populacji jest rozstrzygnięta od 6.D279.
- **Nie przeliczono liczb 6.D283 i 6.D293** — są pomiarami z datą. Populacja liczy
  dziś 483 wobec 481 z 6.D292, bo commitów przybyło; nie jest to rozjazd, tylko
  upływ czasu.
- **Nie przepisano ani jednego komunikatu commita.**
- **Nie przepisano ani jednego zdania prozy w `tools/tests/`** — z powodu, który
  zmierzyłem przy 6.D300.
- **Nie tknięto `src/`.**

## 7. Zauważone przy okazji, nietknięte

Skoro w dwudziestu jeden parach gałąź stoi w klasie ciaśniejszej niż jej własne
scalenie, to komunikat scalenia **traci** informację, którą niesie komunikat gałęzi.
Przy 6.D279 rozstrzygnięto, że scalenia mają być w populacji, bo niosą ten sam
komunikat co commit gałęzi — a ta liczba pokazuje, że w dwudziestu jeden przypadkach
na czterdzieści osiem **nie niosą**. Czy to podważa tamto rozstrzygnięcie, ta pozycja
nie pyta i nie rozstrzyga: 6.D279 mówiło o obecności w populacji, a nie o klasie
wewnątrz niej. Policzenie, ile nazw ginie między komunikatem gałęzi a komunikatem
scalenia, byłoby osobną pozycją.
