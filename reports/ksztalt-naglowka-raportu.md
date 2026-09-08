# Kształt nagłówka raportu — pomiar przed decyzją (6.D38)

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`

Pozycja 6.D38 postawiła pytanie, nie zadanie: **ile raportów ma nagłówek niezgodny ze
wzorem 6.D3 i czy wzór jest w ogóle jeden.** Dopiero z tą liczbą wolno było wybierać
między ujednoliceniem, bramką na kształt i niczym. Ten raport podaje liczby, a potem
wybór, który z nich wynika. Wybór brzmi: **bramki na kształt nie ma i nie powstaje**,
a to, co powstało, pilnuje czegoś innego i tańszego.

## 1. Czym mierzono

Kształtem raportu jest **wiersz pola nagłówka niosący SHA** — pierwszy wiersz przed
pierwszym śródtytułem `## `, który zaczyna się od `**` i ma SHA w grawisach.
Normalizacja: SHA → `<sha>`, data w obu notacjach → `<data>`. Dwa raporty zmierzone
w różnych dniach na różnych commitach mają więc ten sam kształt, a raport z inną
kolejnością pól — inny.

**Dlaczego nie każdy wiersz z SHA.** Nagłówki wspominają commity także w prozie
i w tabelach: `reports/T-400-stage-3b.md` nazywa dwa dodatkowe, a
`reports/mutacje-rdzen-sygnalizacji.md` cztery w tabeli dwóch niezależnych przeglądów.
Liczenie **każdego** wiersza z SHA daje **158 wierszy i 35 kształtów** zamiast 16 —
czyli przyrząd mierzyłby wtedy prozę, nie nagłówek. Ta liczba jest w raporcie celowo:
pokazuje, o ile pomiar byłby wyższy przy definicji, która wygląda równie sensownie.

## 2. Rozbicie kształtów z liczebnością

140 raportów. **135** ma wiersz pola z SHA, **5** nie ma. Kształtów jest **16**:
jeden wzorcowy i piętnaście innych.

| raportów | kształt wiersza pola | wzór 6.D3 |
|---|---|---|
| **90** | `**Zmierzone <data> na commicie:** `+ SHA w grawisach | **tak** |
| 22 | `**Zmierzone na commicie:** ` + SHA (data w osobnym wierszu) | nie |
| 9 | `**Zmierzone na commicie:** ` + SHA + ` · **data:** ` + data | nie |
| 2 | `**Snapshot wyjściowy:** ` + SHA | nie |
| 1 | `**Zmierzone na commicie:** ` + SHA + `(scalenie #212) · **data:** ` + data | nie |
| 1 | `**Zmierzone na commicie:** ` + SHA + `(scalenie #227) · **data:** ` + data | nie |
| 1 | `**Zmierzone na commicie:** ` + SHA + `(baza gałęzi … po przebazowaniu;` | nie |
| 1 | `**Zmierzone na commicie:** ` + SHA + `(main, data), 4 robotniki, 139 minut.` | nie |
| 1 | `**Zmierzone <data> na commicie ` + SHA + `**(gałąź …` | nie |
| 1 | `**Zmierzone na:** ` + SHA + `(stan main w chwili rozpoczęcia).` | nie |
| 1 | `**Snapshot na commicie:** ` + SHA | nie |
| 1 | `**Snapshot na commicie:** ` + SHA + `(main, data)` | nie |
| 1 | `**Snapshot na commicie:** ` + SHA + `(stan przed triażem)` | nie |
| 1 | `**Snapshot po triażu:** ` + SHA | nie |
| 1 | `**Snapshot repozytorium:** ` + SHA + `(main)` | nie |
| 1 | `**Gałąź:** … `· `**stan wyjściowy:** commit ` + SHA + ` · **data:** ` + data | nie |

**Odpowiedź na pytanie pozycji: 90 zgodnych, 45 niezgodnych, 16 kształtów — więc wzór
NIE jest jeden.** Kształt z wiersza 6.D38 (`reports/mutation-sweep.md`) jest jednym
z piętnastu i **nie jest wśród nich najczęstszy**: samotny, jak dziesięć innych.

Pięć raportów bez wiersza pola:
`reports/R-006-line-speed.md` i `reports/T-401-line-run.md` (dwa jawne wyjątki od
wymogu commita, z powodami w `tools/tests/test_report_hygiene.py`) oraz trzy, które
commit i datę mają, ale w prozie albo w tabeli:
`reports/mutacje-rdzen-sygnalizacji.md`, `reports/mutation-triage-fizyka.md`,
`reports/mutation-triage-parametry.md`. Wszystkie trzy przeczytane — **każdy nazywa
datę i commit jednoznacznie**, więc informacji nie brakuje w żadnym z pięciu.

## 3. Liczba, która rozstrzygnęła: rozjazd jest historyczny

Rozbicie po dacie **dodania pliku** (`git log --diff-filter=A`), nie po treści:

| plik dodany | wzór 6.D3 | inny kształt |
|---|---|---|
| 01.09.2026 | 0 | 20 |
| 02.09.2026 | 0 | 9 |
| 03.09.2026 | 0 | 14 |
| 04.09.2026 | 0 | 3 |
| 05.09.2026 | 7 | 4 |
| 06.09.2026 | 33 | **0** |
| 07.09.2026 | 50 | **0** |

Wszystkie 45 niezgodnych dodano **05.09.2026 albo wcześniej**. Od 06.09.2026 doszło
**83 raporty pod rząd** i ani jeden nie odstaje. Bramka 6.D3 weszła 04.09.2026
(`839ad78`) i przyjęła się przez dwa dni bez żadnego pilnowania kształtu.

## 4. Dlaczego bramki na kształt NIE MA

Trzy liczby, każda osobno wystarczająca:

1. **Zapaliłaby się na 50 poprawnych raportach** (45 w innym kształcie + 5 bez wiersza
   pola). Wszystkie niosą datę i commit; rozjazd dotyczy układu, nie treści. Bramka
   zapalająca się na dobrym tekście zostaje wyłączona — 6.D27.
2. **Kosztem byłoby 50 wyjątków przy dopuszczalnych dwóch.** `MAX_COMMIT_EXCEPTIONS`
   w `tools/tests/test_report_hygiene.py` stoi na 2 i wolno go tylko obniżać; drugą
   drogą jest przepisanie 50 nagłówków, czego pole „Poza zakresem" 6.D38 zabrania
   wprost („data i commit zostają takie, jakie były w dniu pomiaru").
3. **Chroniłaby przed zdarzeniem, które w 83 kolejnych plikach nie wystąpiło ani raz.**
   Stawka jest zerowa w mierzonym okresie, koszt pięćdziesięciokrotnie przekracza
   dopuszczalny — i to jest cała arytmetyka tej decyzji.

Ujednolicania też nie ma, z tego samego powodu 2: przepisanie 45 nagłówków datowanych
pomiarów jest poza zakresem pozycji, a nie zaniechaniem.

## 5. Co powstało zamiast bramki na kształt

Pole „Wyjście" 6.D38 przewiduje w tym wypadku **adnotację w `docs/04-conventions.md`,
że wzór jest zaleceniem, nie wymogiem**. Adnotacja jest — i przy okazji jej pisania
wyszło coś większego od samego kształtu.

**`docs/04-conventions.md` miał dziesięć wierszy i ani jednego zdania o raportach.**
Tymczasem powołuje się na niego jako na źródło reguły „pomiaru z datą się nie
przelicza": **11 raportów** w `reports/`, `tools/tests/test_bin_path_framework.py`
(punkt 3 jego docstringu) i **5 miejsc w `docs/TASKS.md`** — w tym pole „Wejście"
samej pozycji 6.D38, które wymienia „`docs/04-conventions.md` (zapis o nagłówku)"
jako wejście pomiaru. Z tych jedenastu raportów **dziesięć** cytuje regułę o pomiarze
z datą, a jeden (`reports/L1_A-chunks.md`) cytuje „1 jednostka = 1 metr" i to w pliku
było. Odsyłacz, którego nie ma czym rozwiązać, jest w tym repozytorium znaną rodziną
usterek (6.D4, 6.D8, 6.D32, 6.D35) — z tą różnicą, że tu wskazywano nie na zły plik,
a na **nieistniejące zdanie w istniejącym pliku**.

Zapis w `docs/04-conventions.md` mówi dziś trzy rzeczy: gdzie stoi nagłówek i co musi
nieść, jaki kształt jest **zalecany** (z liczbami 140 / 135 / 90 / 45 i datą pomiaru)
oraz że **pomiaru z datą się nie przelicza**. Trzy nowe testy w
`tools/tests/test_report_hygiene.py` (moduł **11 → 14**) pilnują tego zapisu, a nie
kształtu nagłówków:

- `test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow` — kształt
  zalecany **nie jest wpisany w test drugą listą**: bramka liczy kształty w
  `reports/`, bierze kształt większości i porównuje go z przykładem z konwencji.
  Rozjazd znaczy albo „zalecenie przestało opisywać repozytorium", albo „ktoś zmienił
  zalecenie i nie zmierzył skutku". Osobna asercja odrzuca **remis** kształtów, bo
  przy remisie „kształt większości" wskazywałby przypadkową stronę.
- `test_konwencje_maja_zapis_na_ktory_powoluja_sie_raporty` — cytowanie musi mieć co
  cytować. Sprawdzany jest **śródtytuł**, nie brzmienie zdania: asercja na prozę
  pękałaby przy każdym przeredagowaniu i nie mówiłaby nic o tym, czy zapis jest.
- `test_detektor_przykladu_naglowka_widzi_blok_wciety` — siedem kontroli detektora,
  w tym dwie na tekście **poprawnym** (kształt zgodny z większością nie odstaje; blok
  `bash` bez SHA nie jest przykładem nagłówka).

## 6. Kontrole negatywne — wykonane, nie zapowiedziane

**KN-11 — przykład w konwencjach w innym kształcie.** Przykład podmieniony na kształt
z wiersza 6.D38. Pada **dokładnie jeden** test, kod wyjścia 1:

```
FAIL test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow: przykład
nagłówka w [konwencjach] ma kształt [kształt ze snapshotu] przy kształcie 90 z 135
raportów: [kształt wzorcowy]
  13/14 przeszło
```

**KN-12 — konwencje bez śródtytułu o raportach.** Pada jeden test, kod 1, i komunikat
sam podaje skalę: `11 raportów cytuje docs/04-conventions.md (…), a plik nie ma ani
jednego śródtytułu o raportach`.

**KN-12 była za pierwszym razem ŚLEPA i mówię to wprost.** Pierwsza próba zamieniła
śródtytuł na „Inny temat, bez slowa o raportach" — a to zawiera napis „raport", więc
wzorzec go **złapał** i bramka została zielona, kod 0. Wyglądało to na kontrolę
wykonaną. Dopiero druga próba, ze śródtytułem „Inny temat", pokazała czerwień. Sama
kontrola negatywna potrafi więc być zielona z niewłaściwego powodu i to jest jej
własna pułapka, nie ciekawostka.

**KN-13 — pułapka wciętego bloku kodu, i to jest kontrola, dla której ten wzorzec
wygląda tak, jak wygląda.** Wzorzec zakotwiczony na `^` + grzbiet bloku pomija blok
stojący **pod punktem listy**, bo taki blok jest w markdownie wcięty. Do konwencji
dopisany drugi przykład — zgniły i wcięty — obok poprawnego niewciętego:

```
wzorzec z [ \t]* przed grzbietem widzi DWA przykłady: wzorcowy i zgniły
wzorzec zakotwiczony na samym grzbiecie widzi JEDEN: wzorcowy
odstające (mój wzorzec):        1 -> bramka CZERWONA, kod 1
odstające (zakotwiczony):       0 -> bramka ZIELONA, nie zobaczywszy zgniłego
```

Zero odstających przy zgniłym przykładzie w pliku to dokładnie ta postać fałszywej
zieloności, którą 6.D27 nakazuje wyłączać — i różnica jest wyłącznie w `[ \t]*`.

**KN-14 — kontrola na tekście POPRAWNYM.** Po przywróceniu każdego z trzech
zaburzeń moduł wraca do 14/14 i kodu 0. Sprawdzone po każdej z KN osobno, nie raz na
końcu.

## 7. Weryfikacja — wyjście wklejone

Zestaw narzędzi na tym drzewie, przed zmianą i po niej (obie liczby z osobnego
przebiegu na `f684e40a3af52272f9cd1d32d241e9bf3abf644d`, kod wyjścia jest wyrocznią,
nie wypis):

```
przed:  RAZEM 72.273 s, 1957 testów, 103 modułów      kod: 0
po:     RAZEM 70.800 s, 1960 testów, 103 modułów      kod: 0
```

Moduł higieny raportów osobno:

```
  14/14 przeszło
  RAZEM 0.076 s, 14 testów, 1 modułów
kod: 0
```

Trzy nowe testy to dokładnie różnica 1957 → 1960; żaden istniejący test nie zniknął
ani nie został osłabiony — liczba modułów bez zmian, 103.

## 8. Przesłanki pozycji, które pomiar sprostował

- **„ile z 128 raportów"** — dziś jest ich **140**. Liczba w wierszu kolejki była
  prawdziwa w dniu wpisania i **nie jest przeliczana**; podaję dzisiejszą osobno,
  bo pomiar na 128 i pomiar na 140 to dwa różne pomiary.
- **Pole „Wejście" wymienia „`docs/04-conventions.md` (zapis o nagłówku)"** — takiego
  zapisu w tym pliku **nie było**. Wejście pomiaru trzeba było więc dopiero napisać,
  i to jest §5.
- **Wzorzec z wiersza 6.D38 to „inny kształt", nie „ten drugi kształt".** Wiersz
  sugeruje dwójkę (wzór 6.D3 kontra nagłówek `reports/mutation-sweep.md`); kształtów
  jest szesnaście.

## 9. Czego świadomie nie zrobiłem

- **Nie tknąłem nagłówka `reports/mutation-sweep.md`.** Byłoby to ujednolicanie, które
  pomiar odrzucił, i przepisanie nagłówka datowanego pomiaru, którego pole „Poza
  zakresem" zabrania. Nagłówek niesie commit, gałąź i datę — nic z tego nie ginie.
- **Nie ruszyłem `MIN_REPORTS`, `MAX_COMMIT_EXCEPTIONS` ani listy wyjątków.** Żadna
  z tych liczb nie stoi na drodze wynikowi „bez bramki".
- **Nie dopisałem bramki na to, że nowy raport ma kształt większości.** To jest bramka
  na kształt w przebraniu: nie umie odróżnić raportu nowego od starego bez drugiej
  listy plików, a lista plików w teście starzeje się z każdym commitem.
- **Nie sprawdzam asercją brzmienia zdania „pomiaru z datą się nie przelicza".**
  Asercja na prozę pęka przy przeredagowaniu i nie mierzy, czy reguła jest zapisana.

## 10. Zauważone przy okazji, nie tknięte

- **`MIN_REPORTS = 40` przy 140 raportach**, a komentarz obok podaje „raportów jest
  48 (zmierzone 05.09.2026 na `6c1048b`)". Liczba ma commit, więc jest poprawnym
  pomiarem z datą; próg jest jednak dziś **trzy i pół raza** niżej niż stan, czyli
  wskazanie katalogu na trzecią część `reports/` przeszłoby przez licznik.
  To osobna pozycja, nie ta.

  **ADNOTACJA 08.09.2026 (6.D45).** Liczby wyżej zostają takie, jakie były w dniu
  pomiaru — pomiaru z datą się nie przelicza. Pozycja została wykonana: `MIN_REPORTS`
  stoi na **153** (zmierzony stan katalogu, nie zapamiętany), a warunek jest
  **równościowy**, więc próg nie może już zostać za katalogiem. Pomiar i kontrole
  negatywne: `reports/zapadka-liczby-raportow.md`.
- **`seen >= 500` w bramce ścieżek** ma ten sam kształt problemu: próg zmierzony przy
  623 trafieniach w 48 raportach, dziś raportów jest 140.
- **`reports/odcisk-w-naglowku-raportu.md` §8** — miejsce, w którym 6.D38 zostało
  zauważone — mówi o rozjeździe kształtu jako o jednym przypadku. Po tym pomiarze
  jest ich piętnaście; §8 zostaje nietknięte, bo jest pomiarem z datą.
