# 6.D105 — dwie tabele statusów i piąta nazwa, której żadna nie definiowała

**Zmierzone 10.09.2026 na:** `69970ad`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_provenance_classes.py` (`klasy_dokumentu_geometrii`,
`statusy_w_kolumnach_geometrii`, `statusy_uzyte_w_geometrii`,
`statusy_obce_bez_zrodla`, `_tabele`), `docs/21-measured-vs-assumed.md`,
`docs/02-simulation.md`.

---

## 1. Liczby z wpisu odtworzyły się co do jednej

Rzadki przypadek w tej serii: wpis 6.D105 podawał liczby, które **wszystkie** się
odtworzyły. Zmierzone na `69970ad`, przed jakąkolwiek moją edycją:

| status | użyć w `docs/21` | zdefiniowany w |
|---|---:|---|
| `spec` | 15 | obu tabelach |
| `design_assumption` | 14 | `docs/21` |
| `blocked` | 7 | `docs/21` |
| **`design_model`** | **6** | **`docs/02` — i `docs/21` o tym nie mówił** |
| `observed` | 4 | obu tabelach |
| `est` | 0 | `docs/02` |

Podział tabel również: wspólne **dwie** nazwy (`spec`, `observed`), wyłączne po
**dwie** z każdej strony (`blocked` i `design_assumption` tu, `est` i `design_model`
tam).

## 2. Usterka i jej naprawa

`docs/21` używał `design_model` sześć razy, nie definiując go we własnej tabeli i nie
odsyłając po niego nigdzie. Nazwa była czytelna wyłącznie dla kogoś, kto **wie**, że
istnieje druga tabela — a dokument nie mówił, że istnieje.

Naprawa jest jednym akapitem pod tabelą definiującą: nazwa, jej źródło
(`docs/02-simulation.md`), powód rozdzielenia tabel (wymiary geometrii kontra
parametry modelu jazdy), liczba wystąpień i podział nazw na wspólne i wyłączne.
**Tabel nie zlano, znaczenia żadnego statusu nie zmieniono, klasyfikacji żadnego
parametru nie ruszono** — pole „Poza zakresem" wyklucza wszystkie trzy.

## 3. Dwa czytniki, bo dwa różne pytania — i żaden nie zgaduje

6.D89 zmierzyło, że pytanie „czy ten napis w grawisach jest statusem" **nie ma na
prozie pewnej odpowiedzi**: pierwsza wersja tamtej bramki zgłosiła `as_of` z listy pól
metadanych. Ta pozycja tego pytania nie stawia ani razu:

* **nazwa NIEZNANA** łapie się w **kolumnie `status`** tabeli — rozpoznanie
  strukturalne, po nagłówku kolumny. Kolumna jest miejscem, w którym stoi status
  i nic innego;
* **nazwa ZNANA, ale cudza** łapie się w prozie po **słowniku zamkniętym** — sumie
  obu tabel. Słownik nie potrafi wymyślić nowej nazwy i nie musi.

Że rozpoznanie po nagłówku jest konieczne, też jest zmierzone. Prostszy skan
„komórka będąca pojedynczym napisem w grawisach" daje na tym dokumencie **cztery
fałszywe trafienia** — `box_double`, `bore_single`, `station` i `null`, czyli nazwy
profili tunelu i wartość pustą — na cztery prawdziwe nazwy.

## 4. Trzy razy kontrola pokazała, że coś nie jest przybite

### 4.1 Przypisanie po wierszu nie znosi zawijania prozy

Pierwsza wersja `statusy_obce_bez_zrodla` szukała nazwy i ścieżki **w tym samym
wierszu**. Mój własny akapit naprawczy przewinął się na kolejny wiersz i funkcja
uznała `design_model` za nieprzypisany. Wykrył to przebieg, nie lektura. Granica jest
dziś **akapitem** — bo zdanie o źródle ma stać przy nazwie, ale zdanie w markdownie
łamie się na kilka wierszy.

### 4.2 Granica akapitu nie była przez nic przybita — KN-3 zielona

Rozluźnienie przypisania do „gdziekolwiek w pliku" **nie zapalało niczego**: na
dzisiejszym dokumencie obie reguły dają ten sam wynik, bo ścieżka i nazwa stoją
w jednym akapicie. Granica jest więc dziś pinowana **wejściem syntetycznym** — nazwa
w jednym akapicie, ścieżka w drugim — i dopiero na nim **KN-3b jest czerwona**.

### 4.3 Wyłączenie tabeli definiującej też nie było przybite — KN-6 zielona

Wliczenie tabeli definiującej do „użyć" podnosi tylko liczby i nie zmienia ani jednego
werdyktu, więc wyłączenie jej było bez konsekwencji. Pinuje je dziś para wejść
syntetycznych: sama tabela definiująca daje zero użyć, tabela z kolumną `status` —
jedno. **KN-6b jest czerwona.**

Obie te kontrole wyszły zielone przy pierwszym podejściu i obie były zdaniami
o mechanizmie, których mechanizm nie potwierdzał. To ta sama rodzina, co KN-4
w 6.D103 i KN-5 w 6.D101 — w tej serii trzeci raz.

## 5. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` dwóch plików na bok i `md5sum -c` po przywróceniu, z `__pycache__`
czyszczonym przed każdym przebiegiem (procedura z 6.D102).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | status spoza sumy obu tabel wstawiony do kolumny | **8/9** |
| KN-2 | zdanie o źródle `design_model` usunięte z `docs/21` | **8/9** |
| KN-3 | przypisanie po całym pliku zamiast po akapicie | **9/9 — ZIELONA** |
| KN-3b | to samo po dopisaniu wejścia syntetycznego | **8/9** |
| KN-4 | czytnik kolumn bierze każdą komórkę w grawisach | **7/9**, dwa testy |
| KN-5 | słownik zamknięty tylko z jednej tabeli | **8/9** |
| KN-6 | tabela definiująca liczona jako użycie | **9/9 — ZIELONA** |
| KN-6b | to samo po dopisaniu wejścia syntetycznego | **8/9** |

Po każdej: `md5sum -c` → `OK` na obu plikach.

KN-2 warta zdania: po usunięciu odsyłacza bramka zgłasza **`est`**, a nie
`design_model` — bo mój akapit naprawczy wymienia obie nazwy i jego usunięcie
zabiera źródło obu. Zgłoszenie jest więc prawdziwe, tylko nazwa w komunikacie inna,
niż się spodziewałem.

## 6. Czego świadomie nie zrobiłem

- **Nie zlałem tabel, nie zmieniłem znaczenia żadnego statusu i nie ruszyłem
  klasyfikacji ani jednego parametru** — wszystkie trzy stoją w polu „Poza zakresem"
  jako decyzje właściciela.
- **Nie dopisałem `docs/21` do `CYTUJACY`.** Reguła tamtej listy brzmi „nie wymieniaj
  klas, odsyłaj", a `docs/21` ma prawo definiować własne — dopisanie go tam zapaliłoby
  bramkę na tekście poprawnym.
- **Nie sprawdzam, czy każdy ZDEFINIOWANY status jest gdzieś użyty.** To odwrotne
  pytanie i dziś dałoby zgłoszenie na `est` (zero użyć w obu miejscach), a dokument
  modelu opisuje `est` jako oszacowanie historyczne do usunięcia — czyli zgłoszenie
  byłoby o tekście poprawnym.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

- **`est` ma zero użyć i to jest stan poprawny**, ale nic tego nie pilnuje w żadną
  stronę: nie ma bramki, która zauważy, że nazwa wycofywana wróciła do użycia.
- **Liczby użyć zmieniły się przez moją własną naprawę** — akapit odsyłający wymienia
  nazwy statusów, więc `spec` poszło z 15 na 16, `design_model` z 6 na 9, a `est`
  z 0 na 1. Bramka nie pinuje tych liczb dokładnie i nie powinna: dolne ostrze
  (`design_model` ≥ 6) łapie zniknięcie czytnika, a dokładna liczba rosłaby od
  każdego zdania o statusach.
