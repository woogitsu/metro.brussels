# 6.D301 · Rozjazd mianowników nie siedzi w bramkach — siedzi w PROZIE ZADAŃ

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `fd35596`

6.D292 zmierzyło, że ten sam próg „jedna czwarta" daje dwa przeciwne werdykty
o nazwie `MIN_REPORTS`, zależnie od mianownika: cały korpus (1033 komunikaty) wyrzuca tę
nazwę ze zbioru wszechobecnych, populacja bramki (481 commitów) zostawia ją
z zapasem. Ta pozycja pyta, ile bramek ma ten sam kształt.

---

## 1. Znalezisko, które ustawia całą odpowiedź: przypadek założycielski NIE JEST BRAMKĄ

Pole „Weryfikacja" żądało kontroli przyrządu: `WSZECHOBECNE_NAZWY`
z `test_commit_claims.py` ma wyjść w klasie „mianownik szerszy". **Nie wychodzi
i nie może** — a powód nie jest usterką czytnika:

```
WSZECHOBECNE_NAZWY = frozenset({"MIN_REPORTS", "test_all.py"})
```

To jest **przypięty zbiór dwóch nazw**. W kodzie nie ma przy nim żadnego progu,
żadnego ilorazu i żadnego mianownika. Próg „jedna czwarta" istnieje **wyłącznie
w prozie bloku 6.D292** jako kryterium, po którym zbiór miał zostać sprawdzony.

Warunek obalenia spisany przed pomiarem brzmiał: „jeśli przypadek założycielski
nie wyjdzie w klasie »mianownik szerszy«, mam nazwać, która reguła go odrzuciła,
i NIE naciągać definicji, żeby wrócił". Odrzuciła go reguła pierwsza i najprostsza:
**czytnik skanuje asercje, a tam nie ma asercji.** Definicji nie naciągam —
zapisuję, że kontrola przyrządu z pola jest **niewykonalna przez skan kodu**, bo
opisuje coś, czego w kodzie nie ma.

## 2. Dwie liczby, których żądało pole „Wyjście"

Populacja rozpada się na dwie strony, dokładnie tak, jak wymienia je pole „Wejście":
`tools/tests/*.py` (progi w asercjach) **i** `docs/TASKS.md` (pola żądające udziału).

| strona | ile liczy udział | z tego mianownik SZERSZY |
|---|---|---|
| kod — asercje nad populacją | **3** | **1** |
| `docs/TASKS.md` — pola żądające udziału | **12** | patrz §4 |

### Lista imienna, strona kodu

| adres | wyrażenie | mianownik wobec licznika |
|---|---|---|
| `test_csharp_assertions.py:260` | `len(cialo) < len(zrodlo) / 10` | **SZERSZY** — licznik to wycinek, mianownik cały plik |
| `test_curve_radius_axes.py:266` | `sum(ratios.values()) / len(ratios)` | równy — ta sama mapa po obu stronach |
| `test_mutation_sweep.py:968` | `len(unreachable) < len(sweep.targets()) // 2` | równy — klucze `unreachable` pochodzą z `targets()` |

**Dwie z trzech mają mianownik RÓWNY** populacji licznika, i to jest sprawdzone
w kodzie, a nie przyjęte: w `test_mutation_sweep.py` komentarz nad asercją mówi
wprost, że klucze `unreachable` są brane z podanej listy celów, a
w `test_curve_radius_axes.py` obie strony są tą samą mapą `ratios`.

## 3. Jedyny szerszy mianownik w kodzie — i dlaczego NIE ROZJEŻDŻA werdyktu

`assert len(cialo) < len(zrodlo) / 10` porównuje długość wyciętego ciała metody
z długością całego pliku. Mianownik jest szerszy **z definicji zadania**: bramka
pilnuje, żeby czytnik wycinka nie brał za dużo, a „za dużo" ma sens wyłącznie
wobec całości pliku.

Werdykt nie może się rozjechać, bo **nie istnieje węższy mianownik, który by coś
znaczył**. Podzielenie długości wycinka przez długość wycinka dałoby jedynkę
niezależnie od stanu czytnika — czyli bramkę, która nie mierzy niczego. Szerokość
mianownika jest tu **treścią asercji**, a nie jej usterką.

To jest różnica wobec 6.D292, którą warto nazwać wprost: tam oba mianowniki były
sensowne i mierzyły dwie różne rzeczy („jak często nazwa pada w repozytorium"
kontra „ile informacji nazwa niesie tam, gdzie decyduje"). Tutaj sensowny jest
jeden.

## 4. Strona `docs/TASKS.md` — dwanaście pól żąda udziału, a mianownik podaje JEDNO

Pola żądające udziału (definicja wąska: słowo „udział", „odsetek", „jedna czwarta/
trzecia" albo „N % z / wszystkich / populacji / korpusu"):

```
6.B6   Skończone, gdy + Skąd        6.B7   Skończone, gdy + Skąd
6.B8   Skąd                         6.D1   Skończone, gdy
6.A5   Skończone, gdy               6.D201 Wyjście
6.D300 Czego NIE wolno przyjąć      6.D301 Wyjście + Skąd
6.D304 Czego NIE wolno przyjąć
```

**Tylko jedno z nich nazywa mianownik, i jest nim `6.D300`** — pole „Czego NIE
wolno przyjąć bez pomiaru" mówi wprost „że trzy z szesnastu przenosi się na cały
korpus", czyli podaje obie populacje i zakazuje ich mylenia. Pozostałe podają
udział bez powiedzenia, czego udział.

Nie jest to zarzut wobec żadnego z tych bloków: w większości mianownik jest
oczywisty z kontekstu jednego zdania. Jest to natomiast **odpowiedź na pytanie
pola „Wyjście"**: rozjazd mianowników, który 6.D292 zmierzyło, jest możliwy
wszędzie tam, gdzie kryterium udziału stoi w prozie, a nie w asercji — bo proza
nie ma miejsca, w którym mianownik musiałby być zapisany.

## 5. Odpowiedź na pytanie „czy werdykt się rozjeżdża"

| pozycja | rozjazd werdyktu |
|---|---|
| `test_csharp_assertions.py:260` | **nie** — węższy mianownik nie istnieje (§3) |
| `test_curve_radius_axes.py:266` | **nie** — mianownik równy |
| `test_mutation_sweep.py:968` | **nie** — mianownik równy |
| kryterium z bloku 6.D292 | **TAK** — 22,3 % wobec 39,3 % (6.D292 §1 i §2) |

**Rozjazd jest dokładnie jeden i pole to dopuszcza**, o ile stoi przy nim liczba.
Stoi: jeden na piętnaście miejsc, w których w tym drzewie liczy się udział — i to
jedyne, które nie jest bramką.

Przewidywanie czwarte brzmiało „co najwyżej dwa, i może być dokładnie jeden".
Jest dokładnie jeden.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | bramek liczących udział: 8–30 | trafione łącznie (15), pudło dla samego kodu (3) |
| 2 | z mianownikiem szerszym: 1–5 | trafione (1) |
| 3 | przypadek założycielski w klasie „mianownik szerszy" | **OBALONE** — nie jest bramką, §1 |
| 4 | rozjazd werdyktu: co najwyżej 2, może 1 | trafione (dokładnie 1) |
| 5 | większość ma mianownik równy | trafione (2 z 3) |
| 6 | próg wpisany wprost, bez nazwanej stałej | trafione (`/ 10`, `// 2`) |

Pięć trafionych, jedno obalone — i obalone jest **znowu** to, które przepisałem
z cudzego wyniku zamiast wyprowadzić z kodu. **Trzeci raz z rzędu**, po 6.D297
i 6.D299. Tym razem obalenie jest jednak informacją, a nie pomyłką w liczbie:
mówi, gdzie ten kształt naprawdę mieszka.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono żadnego progu** ani `WSZECHOBECNE_NAZWY` — pole „Poza zakresem".
- **Nie postawiono bramki na kształcie progu** — tamże.
- **Nie dopisano mianownika do jedenastu pól z §4.** Kusiło, bo poprawka wygląda
  na jednowierszową; byłaby to jednak zmiana cudzych bloków zadań na podstawie
  kryterium, którego te bloki nie zna��, a pozycja ma LICZYĆ.
- **Nie przepisano ani jednego zdania prozy w `tools/tests/`** — i to jest
  świadome zastosowanie tego, co zmierzyłem dobę wcześniej przy 6.D300: każde
  takie zdanie rusza cztery census-równości i dwie zapadki górne, a te ostatnie
  wolno wyłącznie obniżać.
- **Nie tknięto `data/` ani `src/`.**

## 8. Zauważone przy okazji, nietknięte

Pierwsza wersja mojego czytnika szukała progów ułamkowych w całym drzewie testów
i znalazła szesnaście — z czego **trzynaście to tolerancje fizyczne**
(`0.9 * expected`, `0.15 * (1.0 + reach)`, `abs(a - b) < 0.01 * 100.0`), a nie
udziały populacji. Kształt składniowy „liczba razy ułamek" jest wspólny dla obu,
a rozróżnia je dopiero to, **czy mianownik jest licznością zbioru**. Ile bramek
tego zestawu porównuje wielkość fizyczną z tolerancją względną i czy któraś z nich
ma tolerancję wpisaną bez jednostki w komentarzu, ta pozycja nie pyta.
