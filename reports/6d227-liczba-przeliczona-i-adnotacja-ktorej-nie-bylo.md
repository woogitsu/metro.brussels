# 6.D227 — pozycja była zrobiona od trzech dni, a kolejka o tym nie wiedziała

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `9032b5c`

Wziąłem 6.D227 jako następną pozycję w kolejności tabeli i **zastałem ją wykonaną**.
Praca weszła 16.09.2026 (`reports/6d227-zakres-nazwany-szerzej-niz-zmierzony.md`,
na `d0a97ae`): dwa czytniki, trzy stałe definiujące slajs, dwie podłogi, bramka
odróżniająca kształt od prawdziwości, pięć przypadków przejrzanych ręcznie i kontrole
negatywne. Brakowało **jednej rzeczy: adnotacji ZROBIONE w wierszu `| 6.D227 |`**.

Ten raport robi dwie rzeczy, których tamten zrobić nie mógł: **przelicza liczby na
dzisiejszym katalogu** i zapisuje, ile kosztowała brakująca adnotacja.

## 1. Co kosztowała brakująca adnotacja — trzy skutki, wszystkie zmierzone

**Pierwszy: zapas kolejki był zawyżony o jeden przez trzy doby.** `docs/PLAYABILITY.md`
§4 nazywa dokładnie ten przypadek: „pozycja zrobiona i nieoznaczona zawyża zapas o jeden
— czyli dokładnie w tę stronę, przed którą ten licznik ma chronić". Licznik
`tools/tests/test_backlog.py` liczy pozycje DO WZIĘCIA i 6.D227 była wśród nich,
choć do wzięcia nie było już czego.

**Drugi: raport został sierotą i znalazła go dopiero inna pozycja.** 6.D171 mierzyło
19.09.2026 raporty bez ani jednego odsyłacza w całym drzewie. Wyszły **dwa** i jednym
z nich był `6d227-zakres-nazwany-szerzej-niz-zmierzony`. Powód jest ten sam: odsyłacz
do raportu powstaje w adnotacji ZROBIONE, a adnotacji nie było.

**Trzeci, najdroższy: wziąłem pozycję, która była zrobiona.** Nie wiedziałem tego
z kolejki — dowiedziałem się z drzewa, po przeczytaniu modułu, w którym stały stałe
z komentarzem `6.D227`. Kolejka mówiła, że praca czeka; drzewo mówiło, że jest zrobiona.

## 2. Liczby przeliczone na dzisiejszym katalogu, nie przepisane

Czytniki pożyczone z `tools/tests/test_report_claims.py`, nie napisane drugi raz:

| slajs | 16.09.2026 (`d0a97ae`) | **19.09.2026 (`9032b5c`)** | podłoga |
|---|---|---|---|
| wąski (okno 60 znaków) | 35 | **47** | 35 |
| szeroki (orzeczenie gdziekolwiek w punkcie) | 64 | **81** | 64 |
| wąski przy oknie 20 znaków | 17 | **25** | — |
| wąski, wzorzec tylko katalogi | 14 | **23** | — |
| sekcji „zauważone" w katalogu | — | **235** | 196 |

Wszystkie cztery urosły, bo katalog urósł — `reports/` ma dziś **405** plików wobec
stanu z 16.09.2026. **Obie podłogi mają dziś zapas: 12 i 17.** Rosnąca populacja ich
nie rusza i to był wybór tamtej pozycji, zapisany w jej §5.

**Relacje z tamtego raportu przeliczone i NADAL PRAWDZIWE, choć liczby są inne:**
okno zwężone z 60 do 20 znaków wycina **ponad połowę** slajsu (47 → 25, wtedy 35 → 17);
wzorzec zawężony do samych katalogów odcina **około połowy** (47 → 23, wtedy 35 → 14
— czyli wtedy dwie trzecie, a dziś połowę; ta relacja się ZMIENIŁA i tak to zapisuję).

## 3. Co z pola „Skończone, gdy" jest spełnione i czym

* **Liczba ze slajsem i z definicją zakresu** — trzy stałe stoją obok siebie
  w `tools/tests/test_report_claims.py`: `ORZECZENIA_ZAKRESU` (**18** orzeczeń,
  przeliczone dziś), `OKNO_ZAKRESU` (60 znaków) i `ZAKRES_W_GRAWISACH`. Każda ma
  przy sobie zmierzoną cenę swojego wyboru.
* **Rozstrzygnięcie o sicie z powodem** — rozdzielone na dwie połowy: sita
  **prawdziwości** postawić się nie da (trzy przypadki tekstu POPRAWNEGO, na którym
  by się zapaliło), sito **kształtu** postawić się da i stoi. Że liczy kształt,
  a nie prawdziwość, pilnuje osobna bramka na wejściu syntetycznym.

## 4. Kontrole, przewidywania spisane PRZED przebiegami

Wszystkie na **pełnej** kopii drzewa z `.git`, `__pycache__` czyszczony przed każdym
przebiegiem, kopia przywracana `git checkout` między kontrolami.

| kontrola | zmiana na kopii | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-3 | nic, dwa przebiegi | liczby powtarzalne co do jedynki | **47 / 81 / 235** dwa razy | tak |
| KN-1 | zdanie o zakresie dopisane do sekcji „zauważone" | licznik rośnie o jeden | **48 / 82** | tak |
| KN-2 | sekcja „zauważone" usunięta z jednego raportu | licznik spada | **46 / 80 / 234** | tak |
| KN-4 | wzorzec zakresu zawężony do samego `src/Sim/` | populacja spada, widać cenę definicji | **3 / 6** | tak |

**KN-4 pokazuje więcej, niż przewidywanie zakładało:** przewidziałem „spadek", a spadek
jest z **47 do 3**. Czterdzieści cztery z czterdziestu siedmiu pozycji slajsu mówi
o zakresie INNYM niż `src/Sim/` — czyli klasa, którą ta pozycja tropi, nie jest
własnością jednego katalogu i przypadek założycielski 6.D210 jest jednym z wielu,
a nie wzorcem całości.

## 5. Weryfikacja

Polecenie z pola „Weryfikacja" pozycji:

```
$ python3 tools/tests/test_all.py test_report_claims.py
  29/29 przeszło
  RAZEM 4.373 s, 29 testów, 1 modułów
```

## 6. Czego świadomie nie zrobiono

* **Nie poprawiono ani jednego zdania w żadnym raporcie** — pole „Poza zakresem"
  i 6.D108: raport jest zapisem swojego dnia.
* **Nie ruszono klasyfikatora switchy** ani bramki na prawdziwości twierdzeń —
  oba zamknięte, 6.D210 i 6.D216.
* **Nie przepisano raportu z 16.09.2026.** Jego liczby były prawdziwe w jego dniu
  i takie zostają; dzisiejsze stoją tutaj, osobno.
* **Nie podniesiono podłóg** `MIN_TWIERDZEN_O_ZAKRESIE` ani `MIN_SLAJS_SZEROKI`
  do dzisiejszych 47 i 81. Są WOLNE świadomie (§5 tamtego raportu): równość zapalałaby
  się na każdym dopisanym raporcie, czyli na pracy poprawnej — 6.D27.

## 7. Zauważone przy okazji, nietknięte

Relacja „zawężenie wzorca do katalogów odcina dwie trzecie slajsu" z raportu
z 16.09.2026 dziś już nie zachodzi — odcina **połowę** (47 → 23 wobec 35 → 14).
Zdanie tamtego raportu **zostaje**, bo było prawdziwe w swoim dniu; zapisuję tylko,
że ułamek nie jest niezmiennikiem tego katalogu, a liczbą jego jednego dnia.
