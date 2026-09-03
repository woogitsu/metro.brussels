# Triaż ocalałych mutacji: `tools/blender/clearance.py`

**Snapshot na commicie:** `5f6b68e` (stan przed triażem)
**Data:** 2026-09-03

Pierwszy moduł z kolejki triażu z `reports/mutation-sweep.md`. Wybrany nie dlatego, że
miał najwięcej ocalałych, tylko dlatego, że miał **najwyższy udział przy najmniejszym
rozmiarze**: 13 ocalałych na 14 mutacji, czyli 93 %. Mały moduł da się przejść pozycja
po pozycji i sprawdzić, czy metoda triażu w ogóle działa, zanim ruszy się na 425.

Moduł liczy, czy M7 mieści się w tunelu na łukach. Miał własne testy i to dobre —
sprawdzały wzór na strzałkę cięciwy, odtworzenie znanego okręgu i skrajnię na
zatwierdzonej osi. Żaden z nich nie dotykał **progów**.

## Wynik

| | przed | po |
|---|---|---|
| mutacji | 14 | 11 |
| zabitych | 1 | **5** |
| ocalałych | 13 | **6** |
| ocalałe uznane za usterkę | — | **0** |

Liczba mutacji spadła z 14 na 11, bo zniknęły dwie pozycje razem z **martwym
warunkiem** (niżej) i jedna razem ze strażnikiem `__main__`, wyciętym w narzędziu.

## Co się okazało usterką

### Martwy warunek w `circumradius`

```python
if area2 < 1e-12 or ab * bc * ca == 0.0:
    return None
```

Druga połowa tego warunku **nie mogła się nigdy wykonać**. Iloczyn `ab * bc * ca`
zeruje się tylko wtedy, gdy dwa z trzech punktów się pokrywają — a wtedy pole `area2`
też jest zerem i pierwszy warunek już odrzuca trójkę. Sprawdzone wprost: dla punktów
`(0,0), (0,0), (2,0)` wychodzi `area2 = 0.0` i `iloczyn = 0.0`, więc pierwszy warunek
łapie.

Przegląd mutacyjny pokazał to bez czytania kodu: mutacja `0.0 -> 0.001` w tym miejscu
**przeżywała**, bo nie da się jej zaobserwować. Martwy kod jest zawsze ocalałą mutacją.

Usunięty. To nie jest kosmetyka — warunek sugerował czytającemu, że istnieje wejście,
przed którym trzeba się bronić osobno.

### Trzy progi bez pokrycia

| miejsce | czego nie sprawdzał żaden test | dopisana kontrola |
|---|---|---|
| `versine`, promień niedodatni | testy podawały `None` i trafiały w gałąź `is None`, więc `radius_m <= 0.0` mogło mieć dowolny próg | promień `0.0` i `-5.0`, plus kontrola negatywna, że dodatni daje niezerową strzałkę |
| `circumradius`, próg `1e-12` | testy podawały punkty **dokładnie** współliniowe, więc `area2` wychodziło zerem i próg nie miał czego rozstrzygać | trójka o `area2 = 1,004e-12`, dobrana tak, żeby leżała **między** progiem a jego mutacją; obie strony przypięte |
| `_point_at`, krańce osi | kilometraż równy początkowi albo końcowi osi nie był sprawdzany wcale | oba krańce, węzeł wewnętrzny, interpolacja w środku, plus kontrola negatywna poza osią |
| `_point_at`, zerowe rozpięcie | powtórzony wierzchołek osi — bez strażnika `span <= 0.0` interpolacja dzieli przez zero | duplikat na **początku** osi (patrz niżej) |

**Duplikat musi stać na początku.** Pierwsza wersja tego testu miała powtórzony punkt
w środku osi i mutacji nie zabijała: pętla zwraca przy PIERWSZYM pasującym przedziale,
więc zdublowany wierzchołek w środku zawsze zostaje przykryty przez przedział
poprzedni. Gałąź zerowego rozpięcia jest osiągalna wyłącznie wtedy, gdy duplikat
stoi na samym początku.

## Co NIE jest usterką

Sześć ocalałych zostaje i tak ma zostać. Cztery są **dowodliwie równoważne** — nie
istnieje wejście, na którym dałoby się je odróżnić:

| miejsce | mutacja | dlaczego nieobserwowalna |
|---|---|---|
| `versine`, w. 47 | `<=` → `<` | przy promieniu `0.0` oryginał zwraca `0.0` przez strażnika, mutant przez gałąź `half >= radius_m` — ta sama liczba |
| `versine`, w. 50 | `>=` → `>` | przy `half == radius_m` oryginał zwraca `radius_m`, mutant liczy `radius_m - sqrt(r² - r²)` = `radius_m` |
| `circumradius`, w. 70 | `<` → `<=` | wymaga `area2` **dokładnie** równego `1e-12`; to pole liczone z współrzędnych, więc zbiór miary zero |
| `_point_at`, w. 99 | drugie `<=` → `<` | sprawdzone na całej dziedzinie: przedział półotwarty gubi tylko `target == stations[-1]`, a ten przypadek przechwytuje `return points[-1]` na końcu funkcji. Wyjście identyczne dla każdego wejścia |

Dwie są **równoważne w dziedzinie zadania** — formalnie da się je odróżnić, ale
wejściem, które w tym projekcie nie występuje:

| miejsce | mutacja | wejście rozróżniające | dlaczego nie piszę takiego testu |
|---|---|---|---|
| `versine`, w. 47 | `0.0` → `0.001` | promień z przedziału (0; 0,001] m | promień pół milimetra nie jest łukiem toru w żadnym sensie; `MIN_RADIUS_M` w tym module wynosi 20 m |
| `_point_at`, w. 101 | `0.0` → `0.001` | odcinek osi krótszy niż 1 mm | błąd wynikowy jest poddziałkowy wobec 0,25 m odchyłki, z jaką oś odwzorowuje łamaną STIB |

Dopisanie testu z absurdalnym wejściem tylko po to, żeby licznik ocalałych ładnie
wyglądał, byłoby **dopasowywaniem testu do narzędzia**. Klasyfikacja jest tańsza
i uczciwsza; dwa testy w `test_clearance.py` niosą tę informację w komentarzu, żeby
następny czytający nie próbował „naprawiać" tego samego drugi raz.

## Czego ten triaż uczy o metodzie

**Test, który wygląda na pokrycie progu, może nie dotykać tego progu wcale.** Pierwsze
podejście dopisało trzy testy — `versine` z promieniem zerowym, `circumradius` z trójką
prawie współliniową, granica nasycenia strzałki. Wyglądały dokładnie tak, jak powinny
wyglądać testy tych progów. Zabiły **zero** mutacji.

Dopiero policzenie, przy jakiej wartości oryginał i mutant się rozchodzą, pokazało, że
trzeba `area2` między `1e-12` a `1,01e-12`, a nie „prawie zera", i że duplikat musi stać
na początku osi, a nie w środku. Przegląd mutacyjny jest tu jedyną rzeczą, która
odróżnia test od jego pozoru.

Stąd zasada na resztę kolejki: **każdą dopisaną kontrolę mierzy się ponownie**, a nie
zakłada, że skoro dotyka funkcji, to coś w niej sprawdza.
