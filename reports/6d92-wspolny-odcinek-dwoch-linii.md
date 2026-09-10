# Wspólny odcinek dwóch linii: sformułowanie z wpisu zmierzone i błędne w obie strony (10.09.2026)

**Zmierzone 10.09.2026 na:** `caac31e`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_network_declarations.py` (`wspolne_odcinki`,
`naruszenia_sasiedztwa`), `data/network/lines.json` i `docs/00-network-data.md`
(tylko do odczytu), `python3 tools/tests/test_all.py`.

---

## 1. Co pozycja chciała, i dlaczego dostała co innego

Pole „Wyjście" 6.D92 brzmiało: „ciąg przystanków wspólnych dla pary linii ma być tą
samą sekwencją, czytaną w jedną albo w drugą stronę". Zmierzyłem to na dzisiejszych
danych, zanim napisałem bramkę:

```
L1/L2: wspólnych  3 | ta sama kolejność: False | odwrócona: False
L1/L5: wspólnych 12 | ta sama kolejność: True  | odwrócona: False
L1/L6: wspólnych  3 | ta sama kolejność: False | odwrócona: False
L2/L5: wspólnych  3 | ta sama kolejność: False | odwrócona: False
L2/L6: wspólnych 19 | ta sama kolejność: False | odwrócona: True
L5/L6: wspólnych  3 | ta sama kolejność: False | odwrócona: False
```

**Sformułowanie jest błędne w obie strony.**

Po pierwsze, **cztery pary z sześciu dałyby fałszywy alarm**. Ich część wspólna to
odcinek `Gare de l'Ouest`–`Beekkant` **plus osobna przesiadka `Arts-Loi`**, leżąca
gdzie indziej na każdej z linii. To nie jest jedna sekwencja i nie ma powodu, żeby nią
była — pole „Poza zakresem" wyklucza zresztą przesiadkę wprost, tylko mówi o
„pojedynczej wspólnej stacji", a tu wspólnych stacji jest trzy.

Po drugie, i gorzej: **przecięcie zbiorów jest ślepe na usunięcie**, którego pole
„Skończone, gdy" żąda złapać. Wyrzucenie Madou z L6 wyrzuca go też z części wspólnej,
więc obie strony porównania kurczą się zgodnie i porównanie przechodzi. To ta sama
pustka, którą wczoraj znalazłem w 6.D91: zbiór wyliczany tym samym predykatem, który
kontrola potem sprawdza, nie sprawdza niczego.

## 2. Reguła, która działa: sąsiedztwo, nie sekwencja

**Dwa przystanki sąsiadujące na jednej linii i obecne na drugiej muszą sąsiadować
i tam.** Zdanie krótkie i symetryczne, a łapie dokładnie ten kształt: usunięcie Madou
z L6 czyni `Arts-Loi` i `Botanique` sąsiadami na L6, a na L2 stoi między nimi Madou.

```
naruszeń na dzisiejszych danych:            0
naruszeń po usunięciu Madou z samej L6:     1
   ('L6', 'L2', 'Arts-Loi', 'Botanique', ['Madou'])
```

Zgłoszenie **nazywa brakujący przystanek**, czego żąda pole „Skończone, gdy".

Bramki są trzy: sąsiedztwo (wyżej), długość jedynego maksymalnego wspólnego odcinka
każdej pary (zamrożony pomiar, niżej) i porównanie tego odcinka pozycja po pozycji
w obu kierunkach.

## 3. Para, której wpis nie znał

Maksymalne wspólne odcinki, po jednym na parę:

```
L1/L2:  2 pozycje, kolejność w L2 ta sama:  Gare de l'Ouest … Beekkant
L1/L5: 12 pozycji, kolejność w L5 ta sama:  Gare de l'Ouest … Merode
L1/L6:  2 pozycje, kolejność w L6 odwrotna: Gare de l'Ouest … Beekkant
L2/L5:  2 pozycje, kolejność w L5 ta sama:  Gare de l'Ouest … Beekkant
L2/L6: 19 pozycji, kolejność w L6 odwrotna: Elisabeth … Simonis
L5/L6:  2 pozycje, kolejność w L6 odwrotna: Gare de l'Ouest … Beekkant
```

Wpis znał wyłącznie **L2/L6**. Para **L1/L5 dzieli dwanaście pozycji** i też nie była
przez nic porównywana — to ten sam pakiet A, na którym wczoraj przy 6.D91 wyszła
niesprawdzana linia L5. Dwa razy z rzędu ta sama para okazuje się drugą połową
usterki opisanej jako jednostkowa.

## 4. Kontrola negatywna z pola „Weryfikacja" — i poprawka do wpisu

Wpis żądał: usunąć Madou z samej L6 wraz z obniżeniem `stations` na 25, „czyli zmiana,
którą dzisiejsze cztery bramki przepuszczają". **Przepuszczają ją trzy z sześciu, nie
cztery z czterech** — wariant pierwszy zapala szóstą:

```
wariant 1 — zmieniony tylko lines.json:
  ZAPALIŁA  test_tabela_linii_w_docs_00_zgadza_sie_z_lines_json
            linia 6: docs/00 mówi 26 stacji, lines.json 25
  ZAPALIŁA  test_przystanek_lezacy_miedzy_sasiadami_drugiej_linii_jest_bledem  (nowa)
  ZAPALIŁA  test_wspolny_odcinek_kazdej_pary_ma_zmierzona_dlugosc               (nowa)
  ZAPALIŁA  test_wspolny_odcinek_czyta_sie_w_obie_strony_i_zgadza_na_kazdej_pozycji (nowa)
```

Żeby odtworzyć scenariusz z wpisu dosłownie, trzeba obniżyć **też** liczbę w
`docs/00-network-data.md`. Wtedy stan jest dokładnie taki, jak zapowiadał:

```
wariant 2 — lines.json i docs/00 obniżone zgodnie:
  PRZESZŁA  test_gtfs_potwierdza_kazdy_przystanek_wypisany_na_linii
  PRZESZŁA  test_kazda_linia_deklaruje_tyle_przystankow_ile_ich_wypisuje
  PRZESZŁA  test_regula_liczenia_stacji_zgadza_sie_z_listami_i_z_deklaracja_sieci
  PRZESZŁA  test_roznica_miedzy_liczba_nazw_a_liczba_stacji_jest_wytlumaczona_co_do_jednosci
  PRZESZŁA  test_tabela_linii_w_docs_00_zgadza_sie_z_lines_json
  PRZESZŁA  test_zaden_przystanek_nie_powtarza_sie_na_tej_samej_linii
  ZAPALIŁA  test_przystanek_lezacy_miedzy_sasiadami_drugiej_linii_jest_bledem
  ZAPALIŁA  test_wspolny_odcinek_kazdej_pary_ma_zmierzona_dlugosc
  ZAPALIŁA  test_wspolny_odcinek_czyta_sie_w_obie_strony_i_zgadza_na_kazdej_pozycji
```

Obie kontrole szły na **kopii w katalogu tymczasowym**, ze stałymi `NETWORK` i `DOC`
przestawionymi na tę kopię. `data/` nietknięte — i to nie jest formalność: wczorajsze
6.D90 zmierzyło, że okno, w którym plik śledzony jest zmieniony, widzi każda
równoległa kontrola czystości.

## 5. Cztery kontrole negatywne na nowych bramkach, `md5sum -c: OK` po każdej

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | zapis mówi 18 zamiast 19 dla L2/L6 | **czerwona** 8/10, dwie bramki |
| KN-2 | odcinkiem jest już pojedyncza przesiadka | **czerwona** 7/10, trzy bramki |
| KN-3 | reguła sąsiedztwa oślepiona (warunek zawsze fałszywy) | **czerwona** 9/10 + patrz niżej |
| KN-4 | wspólny odcinek liczony tylko w tę samą stronę | **czerwona** 7/10, trzy bramki |

**KN-3 ma dwie połowy i dopiero razem coś znaczą.** Bramka syntetyczna zgłosiła
oślepienie (9/10), a osobno sprawdziłem to, o co naprawdę chodzi: oślepiona reguła
puszczona na PRAWDZIWYCH danych z usuniętym Madou **przechodzi**, a zdrowa na tych
samych danych zapala się z nazwą przystanku. Bez tej drugiej połowy „bramka syntetyczna
świeci" nie mówiłoby jeszcze, że przyrząd widzi usterkę, dla której powstał.

**KN-4 pokazała, że dwie asercje wypisywały pusty komunikat** (`[]` jako cała treść) —
ta sama usterka, którą naprawiałem wczoraj przy 6.D81 i dziś przy 6.D91. Wszystkie
pięć asercji kontroli przyrządu ma teraz zdanie przed wartością.

**Pułapka polskiego cudzysłowu, po raz czwarty w tej sesji.** Poprawiając te komunikaty
wpisałem `„Skończone, gdy"` wewnątrz literału w cudzysłowach prostych; zamykający znak
skończył literał i moduł przestał się importować (`SyntaxError`, wiersz 401). Zestaw
złapał to natychmiast, bo od 6.D25 nieudany import jest FAILEM, a nie cichym pominięciem.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_network_declarations.py
  -> 10/10 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 105,613 s, 2172 testów, 115 modułów, kod 0
  -> 2172/2172 przeszło
```

Zestaw **2168 → 2172**, moduły bez zmiany (115). Zapadka `MIN_REPORTS` została w tym
commicie podniesiona ze dwustu dziesięciu na dwieście jedenaście — słownie, bo
`test_report_claims.py` czyta pierwszą liczbę po nazwie stałej jako twierdzenie o jej
bieżącej wartości.

## 7. Czego świadomie nie zrobiłem

Nie dopisałem ani nie usunąłem żadnego przystanku w `data/`, nie rozstrzygałem, czy
jakakolwiek stacja należy do linii — jedno i drugie wyklucza pole „Poza zakresem",
a drugie jest pytaniem o dane z `CLAUDE.md` §4.1. `git status data/` po całej pracy
jest pusty. Nie objąłem bramką par o **jednej** wspólnej stacji: przesiadka nie jest
wspólnym odcinkiem i tak stoi w polu „Poza zakresem".

Nie zamieniłem zamrożonych długości na zapadkę: zapadka mówi „nie mniej niż", a tu
zmiana w **którąkolwiek** stronę znaczy, że ruszyła topologia sieci, i ma być widoczna
w diffie razem z powodem.

## 8. Zauważone i nietknięte

Reguła sąsiedztwa jest silniejsza, niż wygląda: mówi, że żadna linia tego metra nie
przejeżdża przez stację, na której inna linia się zatrzymuje, bez zatrzymania. Dziś to
prawda na wszystkich sześciu parach i zero naruszeń, ale jest to **fakt o tej sieci**,
a nie prawo — sieć z przejazdem bez zatrzymania zapaliłaby tę bramkę słusznie co do
litery i niesłusznie co do intencji. Gdyby taki odcinek kiedyś wszedł do danych,
rozstrzygnięcie należy do właściciela, a nie do bramki.
