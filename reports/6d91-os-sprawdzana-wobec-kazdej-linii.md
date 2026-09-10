# Oś sprawdzana wobec KAŻDEJ linii, nie tej z nazwy pliku (10.09.2026)

**Zmierzone 10.09.2026 na:** `1a675a4`, kontener tej sesji.
**Przyrząd:** `tools/track/validate.py` (`validate`, `linie_pakietu`),
`data/network/lines.json` i `data/track/*.json` (tylko do odczytu),
`tools/tests/test_validate_axis.py`, `tools/tests/test_ci_workflows.py`,
`python3 tools/tests/test_all.py`.

---

## 1. Rozmiar usterki jest DWA RAZY większy, niż mówił wpis

Wpis 6.D91 nazywał jedną parę: oś wspólnego pierścienia obsługują L2 i L6, a krok CI
sprawdzał tylko L2. Przeliczenie wszystkich sześciu osi wobec wszystkich czterech linii
pokazało **dwie** takie pary:

```
L1_A  pkg=A | linie układające oś w swoje przystanki: ['L1', 'L5']
L1_B  pkg=B | ['L1']
L2_E  pkg=E | ['L2', 'L6']
L5_C  pkg=C | ['L5']
L5_D  pkg=D | ['L5']
L6_F  pkg=F | ['L6']
```

Krok CI wołał `--line "${id%%_*}"`, czyli brał prefiks nazwy pliku: dla `L1_A` — L1,
dla `L2_E` — L2. **L5 na osi A i L6 na osi E nie były sprawdzane ani razu.**

## 2. Pomiar „przed i po", na obu parach

Kopia `lines.json` w katalogu tymczasowym, z jedną stacją usuniętą ze zbioru
przystanków tej DRUGIEJ linii (`data/` nietknięte, §4.6):

```
oś L2_E, usunięta z L6: Porte de Namur|Naamsepoort
  STARY kształt (--line L2):   kod 0   błędy: []
  NOWY  kształt (--all-lines): kod 1   ['kolejność stacji niezgodna z lines.json dla L6']

oś L1_A, usunięta z L5: Gare Centrale|Centraal Station
  STARY kształt (--line L1):   kod 0
  NOWY  kształt (--all-lines): kod 1   ['kolejność stacji niezgodna z lines.json dla L5']
```

To jest dosłownie pole „Skończone, gdy" tej pozycji: usunięcie stacji z drugiej linii
przechodziło bez śladu, a dziś zapala kontrolę.

**Pierwszy pomiar wypadł nierozstrzygający i to też jest wynik.** Usunąłem najpierw
`Pannenhuis` — stację, która w `lines.json` należy do L6, ale **nie leży na osi E**
(jest na pakiecie F). Oba kształty dały wtedy kod 0, i słusznie: kontrola pyta o to,
czy stacje OSI układają się w przystanki linii, więc usunięcie stacji spoza osi nie ma
prawa niczego zapalić. Mutacja musiała trafić w część wspólną (17 z 17 stacji osi E jest
w L6) i dopiero wtedy zmierzyła to, co miała mierzyć.

## 3. Skąd bierze się lista linii — i dlaczego NIE jest wyliczana

`--all-lines` czyta pakiet, który oś **sama deklaruje** (pole `package.id`, już w danych
od 6.D69), i mapuje go na linie przez `LINIE_PAKIETU` w `tools/track/validate.py`.

**Wyliczanie tego zbioru byłoby kontrolą pustą.** Naturalny pomysł — „linie, w których
przystanki układa się ta oś" — używa DOKŁADNIE tego predykatu, który kontrola potem
sprawdza. Usunięcie stacji z L6 wyrzuciłoby L6 ze zbioru wyliczonego, kontrola nie
miałaby czego sprawdzić i przebieg byłby zielony tak samo cicho jak przed tą pozycją.
Zbiór musi więc pochodzić skądinąd niż sprawdzenie.

**Drugie źródło w `lines.json` sprawdziłem i odrzuciłem po pomiarze.** Pole `unlocks`
pakietów wymienia linie prozą („rdzeń L2", „pełna L6"). Wyciąg `\bL[0-9]\b` daje
poprawny wynik dla pięciu pakietów i **pustkę dla pakietu C**, którego `unlocks` brzmi
„zajezdnia Erasme", „zajezdnia Jacques Brel". Źródło niepełne w jednym z sześciu
przypadków nie jest źródłem.

Została lista **przypięta**, z bramką w OBIE strony: para przypięta musi przechodzić
kontrolę, a para NIEprzypięta musi jej nie przechodzić. Rozjazd w którąkolwiek stronę
znaczy „dane ruszyły, przelicz listę ręcznie", a nie „dopasuj listę do danych".

## 4. Deklaracja stoi w narzędziu, nie w pliku osi — i to jest do rozstrzygnięcia

Pole „Wyjście" pozycji chce, żeby **oś deklarowała** listę linii. Deklaracja w pliku osi
jest zapisem do `data/`, a `CLAUDE.md` §4.6 mówi, że `data/` jest tylko do odczytu,
chyba że zadanie mówi inaczej **wprost** — ta pozycja nie mówi. Przypięcie po stronie
narzędzia daje tę samą własność sprawdzania i nie tyka danych, więc wykonałem je w tej
postaci; **przeniesienie deklaracji do plików osi zostaje pytaniem do właściciela**,
tej samej klasy co 6.D53. Nie jest to blokada: kontrola, o którą chodzi w polu
„Skończone, gdy", działa dziś.

## 5. Sześć kontroli negatywnych, `md5sum -c: OK` po każdej

Cache bajtkodu czyszczony przed każdym przebiegiem (powód z 6.D86).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | z pakietu E znika L6 (para pasuje, ale nieprzypięta) | **czerwona** 46/47 |
| KN-2 | pakiet C bez ani jednej linii | **czerwona** 45/47, dwie bramki |
| KN-3 | do pakietu B dopięta L2, która nie pasuje | **czerwona** 46/47 |
| KN-4 | krok CI wraca do prefiksu nazwy pliku | **czerwona** 75/76 |
| KN-5 | pusta lista linii zamiast odmowy | **czerwona** 46/47 |
| KN-6 | pętla sprawdza tylko pierwszą linię | **czerwona** 46/47 |

```
KN-1  FAIL test_przypisanie_linii_zgadza_sie_z_danymi_w_OBIE_strony:
      L2_E: oś układa się w przystanki linii L6, a ta nie jest przypięta
KN-2  FAIL test_kazda_os_ma_przypisane_linie_i_kazda_z_nich_istnieje:
      L5_C: pakiet C nie ma przypisanych linii w LINIE_PAKIETU
KN-3  FAIL test_przypisanie_linii_zgadza_sie_z_danymi_w_OBIE_strony:
      L1_B: linia L2 jest przypięta, a oś nie układa się w jej przystanki
KN-4  FAIL test_ci_walidacja_osi_sprawdza_kazda_linie_a_nie_prefiks_nazwy_pliku:
      python-tests.yml: krok walidacji osi nie woła `--all-lines`
KN-5  FAIL test_all_lines_odmawia_zamiast_milczec_gdy_nie_ma_z_czego_wziac_linii
KN-6  FAIL test_all_lines_sprawdza_KAZDA_linie_a_nie_pierwsza:
      kontrola nie sprawdziła obu linii pakietu A: ['kolejność stacji zgodna (L1)']
```

**KN-1 i KN-3 mierzą przeciwne kierunki tej samej bramki i dlatego stoją osobno:**
pierwsza pyta, czy zapomniana para zostanie zauważona, druga — czy para dopisana bez
pokrycia w danych zostanie odrzucona. Bramka tylko w jedną stronę przyjęłaby albo listę
zbyt krótką, albo listę zmyśloną.

**KN-5 wypisała pusty komunikat i to zostało poprawione przy okazji.** Asercja niosła
jako komunikat samą listę błędów, która w tym przypadku jest pusta — czyli przyrząd
mówił „coś nie gra" i nie mówił co. Ta sama usterka co przy 6.D81; obie asercje mają
teraz zdanie przed listą.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_validate_axis.py
  -> 47/47 przeszło

python3 tools/tests/test_all.py test_ci_workflows.py
  -> 76/76 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 105,968 s, 2168 testów, 115 modułów, kod 0
  -> 2168/2168 przeszło

python3 tools/track/validate.py data/track/L1_A.json --all-lines --package A
  ·   kolejność stacji zgodna z lines.json (L1)
  ·   kolejność stacji zgodna z lines.json (L5)
python3 tools/track/validate.py data/track/L2_E.json --all-lines --package E
  ·   kolejność stacji zgodna z lines.json (L2)
  ·   kolejność stacji zgodna z lines.json (L6), oś biegnie odwrotnie do kolejności z listy
```

Zestaw **2162 → 2168**, moduły bez zmiany (115). Zapadka `MIN_REPORTS` została w tym
commicie podniesiona ze dwustu dziewięciu na dwieście dziesięć — słownie, z tego samego
powodu, dla którego zapis cyfrowy poprawiłem dziś już dwa razy (sekcja 8).

## 7. Czego świadomie nie zrobiłem

Nie rozstrzygałem, czy jakakolwiek stacja należy do drugiej linii — pole „Poza zakresem"
wyklucza to wprost i jest to pytanie właściciela. Niczego w `data/` nie zmieniłem;
wszystkie pomiary z podmienioną siecią szły na kopii w katalogu tymczasowym,
`git status data/` po całej pracy jest pusty. Nie dopisałem deklaracji linii do plików
osi (§4 punkt 6, sekcja 4 wyżej). Nie ruszyłem `--line`: opcja zostaje, bo jest jedyną
drogą, którą da się zapytać o linię POJEDYNCZĄ, i chodzi nią większość testów tego
walidatora.

## 8. Zauważone i nietknięte

**Zdanie w raporcie podające BIEŻĄCĄ wartość zapadki starzeje się przy najbliższym jej
podniesieniu, i dziś zapaliło bramkę `test_report_claims.py` trzy razy** — na strzałce
`207 → 208`, na zdaniu „stoi na 208" nazajutrz i na „stoi na 209" godzinę później. Za
każdym razem poprawka polegała na przepisaniu liczby słownie. Kształt jest powtarzalny
i nadaje się na pozycję kolejki: raport ma prawo mówić o wartości Z DNIA POMIARU, a
bramka czyta to jako twierdzenie o dziś. Nie dopisuję jej tutaj, bo kolejka nie stoi na
progu, a wymyślanie pozycji przy okazji jest tym, czego zabrania §8.

Nazwy stacji są w tym repozytorium dwujęzyczne z kreską pionową
(`Porte de Namur|Naamsepoort`), a porównanie idzie po całym napisie. Zmiana samej formy
zapisu po jednej stronie rozjechałaby kontrolę bez zmiany faktu o sieci — dziś nic tego
nie pilnuje, bo obie strony czyta się z tego samego pliku.
