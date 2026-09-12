# 6.D150 — status w kolumnie CSV wchodzi do skanu, ale słowniki się nie spotykają

**12.09.2026**, na `4e79c5a`. Wejście: `data/network/station-depths.csv` (tylko do
odczytu), `tools/tests/test_provenance_classes.py`. Pozycja: skan statusów z 6.D134
czyta wyłącznie JSON-y, a CSV ma status w **kolumnie** i nie widzi go nic.

## 1. Liczba, o którą pozycja prosiła

```
CSV pod data/:  ['network/station-depths.csv']
statusy:        {'network/station-depths.csv': {'confidence': {'unknown': 9, 'estimated': 3}}}
```

**Jeden plik, jedna kolumna, dwanaście wartości.** Żaden inny plik CSV pod `data/`
nie istnieje — i to też jest przybite, żeby nowy nie wszedł poza skan.

### Trzecia wartość z wpisu pozycji jest odciskiem czytnika, nie danymi

Wpis mówił „`estimated` 3×, `unknown` 9×, **`confidence` 1×**". Ta trzecia to
**policzony NAGŁÓWEK**. Plik ma cztery wiersze komentarza `#`, a dopiero piąty jest
nagłówkiem; `csv.DictReader` puszczony wprost bierze za nagłówek pierwszy komentarz
i całą resztę czyta jako jedną kolumnę. Wykonane w kontroli przyrządu:

```
list(csv.DictReader(uchwyt))[0].keys()  ->  ['# komentarz jeden']
"confidence" in naiwny[0]               ->  False
```

Czytnik pomija więc wiersze `#`, a nagłówkiem jest pierwszy wiersz niekomentarzowy.

## 2. Rozstrzygnięcie: słowniki się NIE spotykają — i odmawia tego bramka starsza ode mnie

Pole „Dlaczego" pytało, czy `estimated` z CSV i `est` z modelu mają wejść do jednego
słownika. Odpowiada przecięcie zbiorów:

| | |
|---|---|
| słownik CSV (z **nagłówka tego pliku**: `# confidence: measured \| counted \| estimated \| unknown`) ∩ klasy modelu (`docs/02`) | **∅** |
| ten sam słownik ∩ statusy z JSON-ów pod `data/` | **{`unknown`}** — jedno słowo, w JSON-ach 268× |

Dwa słowniki opisują dwie różne rzeczy: klasy modelu mówią, **skąd wzięto parametr
jazdy**, a kolumna `confidence` — **jak pewny jest pomiar głębokości**.

**Mocniejszy dowód przyszedł z kontroli KN-4.** Dopisanie `estimated` do
`ZAKAZANE_W_DANYCH` — czyli złączenie słowników — zapala **trzy** testy, w tym
`test_kazda_klasa_zakazana_jest_ZDEFINIOWANA_w_dokumencie_modelu`:

```
zakaz na klasę, której dokument modelu nie definiuje: ['estimated'] —
zakaz ma stać przy definicji, a nie zamiast niej
```

To jest bramka z **6.D134**, starsza od tej pozycji, i odrzuca złączenie niezależnie
od mojego rozumowania. Złączenie wymagałoby też zmiany klasyfikacji trzech wierszy,
których pole „Poza zakresem" dotykać zabrania — i akurat tych trzech, które jako
jedyne w pliku niosą cytat ze źródła i podaną precyzję (±1 m).

## 3. Co jednak obowiązuje w obu miejscach

**Klasa zakazana `est` obowiązuje wszędzie, gdzie stoi status** — niezależnie od
słownika, jakim posługuje się plik. `est` wstawione do kolumny CSV zapala bramkę
(KN-1b), i to jest osobne zdanie od złączenia słowników: `est` nie staje się przez
to częścią słownika `station-depths.csv`, tylko nazwą, której w danych nie wolno.

## 4. Kontrole negatywne

Baza: **19/19**. Po każdej `cp` z kopii i `md5sum -c: OK` na dwóch plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1b | `est` w kolumnie CSV (na **kopii drzewa**) | **15/19** | cztery testy, w tym grep słowa `est` 7 → 8 |
| KN-2 | czytnik nie pomija wierszy komentarza | **15/19** | statusy 12 → 0; plik wypada ze skanu |
| KN-3 | `confidence` zdjęte z `KOLUMNY_STATUSU_CSV` | **15/19** | tabela nagłówków jest tym, co wiąże kolumnę |
| KN-4 | `estimated` dopisane do `ZAKAZANE_W_DANYCH` | **16/19** | **złączenie odrzuca bramka z 6.D134** |
| KN-5 | skan nie schodzi do podkatalogów `data/` | **16/19** | plik leży w `data/network/`, nie w `data/` |

### KN-1 wykonałem najpierw źle i to jest warte zapisania

Pierwsza próba mutowała `data/network/station-depths.csv` **w miejscu**. Plik został
przywrócony z kopii i `md5sum -c` dał `OK`, ale reguła jest ostrzejsza niż
„przywróć po sobie": `data/` jest tylko do odczytu, a kontrola negatywna nie jest
od tego wyjątkiem — drzewo się **kopiuje**. KN-1b powtarza ten sam pomiar na kopii
całego drzewa w `/tmp` (46 MB, bez `.git`, `build/`, `renders/`) i daje ten sam
wynik. Liczby w tabeli pochodzą z przebiegu na kopii.

## 5. Czego nie zrobiono

- **Nie zmieniono ani jednej klasyfikacji głębokości** i nie zapisano nic do `data/`
  — pole „Poza zakresem". Plik jest w drzewie bit w bit taki, jak był.
- **Nie dopisano `station-depths.csv` do skanu JSON-owego.** To osobny czytnik, bo
  CSV nie ma pola `status`, tylko kolumnę — dokładnie tak, jak 6.D105 zrobiło dla
  tabel Markdown.
- **Nie objęto skanem CSV poza `data/`.** Pozycja pytała o `data/`; czy `docs/`
  albo `reports/` niosą tabele CSV ze statusem, nie sprawdzałem.
- **Nie rozstrzygnięto, czy `unknown` w CSV i `unknown` w JSON-ach to ta sama rzecz.**
  To jedno wspólne słowo obu słowników; w JSON-ach stoi 268 razy i najpewniej znaczy
  po prostu „nie wiadomo", ale zdania o tym nie ma w żadnym dokumencie i zgadywać
  go nie będę.
