# Drugie tego dnia uzupełnienie kolejki na progu dwunastu pozycji (10.09.2026)

**Zmierzone 10.09.2026 na:** `dd53c4e`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_backlog.py` (`open_items`, `detail_sections`,
`missing_fields`), `tools/tests/test_field_paths.py` (`_all_blocks`, `_open_blocks`,
`_code_lines`), `tools/tests/test_provenance_classes.py` (`klasy_z_dokumentu`),
`python3 tools/tests/test_all.py`.

---

## 1. Dlaczego znowu, tego samego dnia

Po scaleniu #478 kolejka faz 5 i 6 miała **dokładnie dwanaście** pozycji otwartych —
tyle, ile wynosi `MINIMUM_READY_ITEMS`. Ten sam próg co rano, ten sam powód z `CLAUDE.md`
§8: wzięcie następnej pozycji zbiłoby licznik do jedenastu. Między jednym uzupełnieniem
a drugim zostało scalonych sześć pozycji, więc odstęp nie jest anomalią, tylko tempem.

Efektywnie otwartych było **jedenaście**, bo w dwunastu stoi **6.D53**, której pole
„Zależy od" brzmi „decyzji właściciela o zapisie do `data/network/sources.json`" —
to samo zawężenie, co przy pierwszym uzupełnieniu, i nadal nie moje do rozstrzygnięcia.

## 2. Skąd wzięło się sześć nowych pozycji

**Żadna nie została wymyślona na miejscu.** Wszystkie sześć wyszły z pomiarów zrobionych
w tej sesji przy wykonywaniu innych pozycji — pięć z nich przy pozycjach scalonych
w ciągu ostatnich kilku godzin.

| pozycja | skąd, i przy czym zmierzona |
|---|---|
| 6.D101 | trzy pola „Weryfikacja" wołające nieistniejące moduły — znalezione ręcznie przy 6.D74, 6.D86 i 6.D89 |
| 6.D102 | stary bajtkod, który przebił dwie kontrole negatywne przy 6.D86 |
| 6.D103 | trzy gałęzie `allOf` pominięte przez pętlę zgodności dopisaną w 6.D85 |
| 6.D104 | jeden wpis `ZAPRZECZENIA` wobec pięciu punktów README — policzone przy 6.D87 |
| 6.D105 | dwie tabele statusów pochodzenia zestawione ze sobą przy 6.D89 |
| 6.D106 | nazwy plików tymczasowych w `mutation_sweep.py`, przeczytane przy sprawdzaniu, czy 6.D90 to jedna usterka czy dwie |

## 3. Siódmy kandydat odrzucony, i to jest część wyniku

Rozważałem pozycję o **pułapce polskiego cudzysłowu**: otwierający `„` (U+201E) domknięty
w kodzie Pythona zwykłym `"` kończy literał i daje `SyntaxError`. Sesja wpadła w nią
dwa razy (6.D73, 6.D87), a przy pisaniu TEGO uzupełnienia trzeci.

Kandydat odrzucony po pomiarze, z dwóch niezależnych powodów. Pierwszy: mój wzorzec
szukający kształtu dał **471** trafień, z których żadne nie było usterką — to znak,
że wzorzec mierzy coś innego, niż nazywa. Drugi i rozstrzygający: prawdziwa pułapka jest
**błędem składni**, więc w scalonym drzewie istnieć nie może — plik z nią nie zaimportuje
się w żadnym przebiegu zestawu. Bramka pilnowałaby stanu, którego nie da się osiągnąć.
Kształt jest realny i kosztowny, ale kosztuje **w sesji**, nie w repozytorium, więc
miejscem na niego jest procedura, a nie test. Zapisany tutaj, żeby następny agent nie
przeliczał tego od nowa.

## 4. Pomiar, który obalił pierwszą wersję jednej z pozycji

Wpis 6.D105 napisałem najpierw tak: „`docs/21-measured-vs-assumed.md` używa klas
pochodzenia i nie sprawdza ich nic". Potem policzyłem i to jest nieprawda.

```
definiowane w docs/21: ['blocked', 'design_assumption', 'observed', 'spec']
definiowane w docs/02: ['design_model', 'est', 'observed', 'spec']
  blocked              użyć w docs/21:   7  def21=True  def02=False
  design_assumption    użyć w docs/21:  14  def21=True  def02=False
  design_model         użyć w docs/21:   6  def21=False  def02=True
  est                  użyć w docs/21:   0  def21=False  def02=True
  observed             użyć w docs/21:   4  def21=True  def02=True
  spec                 użyć w docs/21:  15  def21=True  def02=True
```

`docs/21` **nie jest kopią** listy z dokumentu modelu — ma własną tabelę statusów.
Wspólne są dwa, po dwa są wyłączne dla każdej strony. Usterką jest jedna linijka
tej tabeli: `design_model` jest w `docs/21` użyty **sześć razy** i nie jest tam ani
zdefiniowany, ani odesłany gdzie indziej. Reguła z 6.D89 („nie wymieniaj, odsyłaj")
dla tego dokumentu byłaby **fałszywa**, więc wpis został przepisany, a nie poprawiony
o liczbę.

## 5. Pomiar, który znalazł usterkę w moim własnym bloku

Pod pozycję 6.D101 policzyłem gołe nazwy modułów podawane po `test_all.py` w blokach
`docs/TASKS.md`. Wynik pierwszego przebiegu, na pliku już z sześcioma nowymi blokami:

```
gołe nazwy modułów: wszystkie 58 | otwarte 13
nieistniejące otwarte: [('6.D102', 'test_all_self.py')]
```

Jedyna nieistniejąca nazwa w całym pliku stała w polu „Weryfikacja" bloku, który
napisałem kwadrans wcześniej — czyli **czwarty przypadek dokładnie tego kształtu,
o którym jest pozycja obok, popełniony w commicie ją zakładającym**. Nie znalazła go
bramka; znalazł go pomiar robiony pod tę pozycję. Pole zostało przepisane na przebieg
całego zestawu, z wypisanym powodem, dla którego nie nazywa modułu bramki: takiego
modułu dziś nie ma, a nazwanie go z góry byłoby powtórzeniem usterki.

Po poprawce:

```
gołe nazwy modułów: wszystkie 57 | otwarte 12
nieistniejące: []
```

## 6. Zapadki

`MINIMUM_DETAIL_BLOCKS` stoi na **179**, podniesiona ze stu siedemdziesięciu trzech,
bo bloków przybyło sześć. Wartość jest wynikiem `len(detail_sections(...))` na pliku
po edycji, nie sumą „173 plus sześć" — przy commicie dopisującym więcej niż jeden blok
te dwie czynności rozjeżdżają się po cichu.

`MINIMUM_READY_ITEMS` **bez zmiany** (12). Jest progiem, poniżej którego nie wolno zejść,
a nie licznikiem stanu; podniesienie go do osiemnastu zamieniłoby próg w wymaganie
i zapaliłoby bramkę przy pierwszej scalonej pozycji.

`MIN_REPORTS` została w tym commicie podniesiona ze dwustu siedmiu na dwieście osiem:
jeden raport, ten plik, policzony na drzewie. Obie liczby stoją tu słownie, a nie
cyfrowo, bo bramka `test_report_claims.py` bierze pierwszą liczbę po nazwie stałej za
twierdzenie o jej BIEŻĄCEJ wartości — na strzałce `207 → 208` zapaliła się od razu,
a na zdaniu „stoi na 208” zapaliła się nazajutrz, przy pierwszym kolejnym podniesieniu.
Oba zapalenia są poprawnym działaniem bramki i dlatego zdanie o wartości z DNIA
POMIARU nie ma tu prawa stać cyfrą.

## 7. Cztery kontrole negatywne, `md5sum -c: OK` po każdej

Cache bajtkodu czyszczony przed każdym przebiegiem — powód zapisany przy 6.D86
i będący treścią nowej pozycji 6.D102.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | zapadka bloków ustawiona na 180, czyli POWYŻEJ stanu pliku | **czerwona** 25/26 |
| KN-2 | zapadka bloków ustawiona na 178, czyli PONIŻEJ stanu pliku | **czerwona** 25/26 |
| KN-3 | z bloku 6.D106 znika pole „Zależy od" | **czerwona** 24/26, dwie bramki naraz |
| KN-4 | zapadka liczby raportów ustawiona na 209, czyli powyżej stanu `reports/` | **czerwona**, pięć bramek higieny |

```
KN-1  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
      bloków jest 179 przy zapadce 180 — któryś zniknął albo stracił jedno z sześciu pól
KN-2  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
      bloków z kompletem sześciu pól jest 179, a zapadka stoi na 178 — podnieś ją do 179
KN-3  FAIL test_every_detail_block_carries_all_six_fields: 6.D106 bez pól: Zależy od
      FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 178 przy zapadce 179
KN-4  FAIL test_kazdy_raport_podaje_commit_na_ktorym_mierzono:
      bramka przeszła tylko 208 raportów, a w `reports/` jest ich co najmniej 209
```

**KN-1 i KN-2 mierzą kierunki PRZECIWNE i dlatego są osobno.** Zapadka ma dwie
asercje: jedna nie pozwala ustawić jej wyżej niż stan pliku (inaczej byłaby
życzeniem), druga nie pozwala zostawić jej niżej (inaczej dopisany blok mógłby po
cichu wypaść). Kontrola tylko w jedną stronę przyjęłaby „poprawkę" zdejmującą drugą
asercję.

## 8. Weryfikacja

```
python3 -c "... tb.open_items(t) ..."
  -> otwartych: 18
  -> ['6.D53', '6.D90', ..., '6.D100', '6.D101', '6.D102', '6.D103', '6.D104',
      '6.D105', '6.D106']

python3 -c "... tb.detail_sections(t) ..."
  -> bloków: 179
  -> 6.D101..6.D106: po jednym bloku, missing_fields puste dla każdego
```

```
python3 tools/tests/test_all.py
  -> RAZEM 99,548 s, 2155 testów, 114 modułów, kod 0
  -> 2155/2155 przeszło
```

Zestaw **bez zmiany** (2155) i to jest stan poprawny: uzupełnienie kolejki dopisuje
tekst i podnosi dwie zapadki, a nie dokłada testów.

## 9. Czego świadomie nie zrobiłem

Nie wziąłem 6.D90, choć była następna w kolejności — §8 każe najpierw uzupełnić kolejkę.
Nie dopisałem siódmej pozycji o cudzysłowie (§3). Nie ruszyłem żadnej pozycji istniejącej
poza trzema raportami, w których stała wartość `MINIMUM_DETAIL_BLOCKS`: te trzy zmiany
wymusiła bramka `test_report_claims.py`, bo zapadka zmieniła wartość, a akapity mówiły
o jej stanie bieżącym.

## 10. Zauważone i nietknięte

`est` nie występuje dziś ani w `docs/21`, ani w danych pojazdu, ani w `docs/02` poza
własną definicją — dokument modelu opisuje ją jako oszacowanie historyczne „do usunięcia
lub weryfikacji", i nikt tego nie rozstrzygnął. To jest kandydat na pozycję przy
następnym uzupełnieniu, jeśli 6.D105 sam go nie zamknie.
