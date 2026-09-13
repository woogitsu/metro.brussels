# 6.D161 — osiemnaście zdań, dziewięć bez wejścia, i pięć różnych losów zamiast dwóch

**13.09.2026**, na `ca9c595`. Wejście: `tools/tests/`, `reports/6d147-sekwencje-ucieczki.md`,
`reports/6d148-gdzie-stoi-compileall.md`, `reports/6d149-prog-a-maszyna.md`.

Pozycja pytała o dwie liczby: ile w drzewie stoi zdań rodziny „ubezpieczenie, nie
zmierzona konieczność", i ile z nich ma pod sobą wejście syntetyczne. Obie są niżej.
Ale **podział, który pole „Wyjście" zakładało, nie istnieje** — i to jest ważniejsze
od samych liczb.

## 1. Liczby

| | |
|---|---:|
| zdań rodziny w `tools/tests/` | **18** |
| z wejściem syntetycznym | **9** |
| bez wejścia syntetycznego | **9** |

Obie wyprowadzone ze źródeł: pierwsza skanem po `tools/tests/` przez wspólny filtr
drzewa, druga — listą przeczytaną po kolei. Dlaczego druga jest listą, a nie skanem,
mówi punkt 3.

## 2. Losy zielonej kontroli nie są dwa, tylko pięć

Pole „Wyjście" zakładało podział binarny: albo zdanie jest samą deklaracją, albo ma
pod sobą wejście syntetyczne. Przeczytanie wszystkich osiemnastu pokazuje, że zielona
kontrola negatywna kończy się w tym drzewie na **pięć różnych sposobów**:

| los | ile | przykład |
|---|---:|---|
| wejście syntetyczne dołożone | 9 | czwarty kształt zapisu dopisany razem z wejściem |
| **ubezpieczenie przyjęte świadomie** | 2 | zepsucia pliku docelowego nie udało się odtworzyć w pięciu próbach |
| **twierdzenie poprawione, nie przybite** | 2 | dawne zdanie o granicy zamka było po prostu nieprawdziwe |
| **mechanizm dołożony, wejścia mieć nie może** | 2 | asercji z pustym komunikatem jest w drzewie zero |
| **mechanizmu nie przyjęto** | 1 | osobna zapadka na liczbę nie zapalała się nigdy sama, więc jej nie ma |

Tylko **dwa** z osiemnastu to ubezpieczenie w ścisłym sensie pytania. Pozostałe siedem
bez wejścia to trzy inne rzeczy, z których żadna nie jest „deklaracją bez pokrycia":
dwa razy poprawiono zdanie zamiast dokładać sito, dwa razy mechanizm dołożono
wiedząc, że wejścia nie ma z czego zrobić, raz mechanizmu nie przyjęto w ogóle.

Zielona kontrola negatywna **nie jest więc jedną chorobą**. Bywa diagnozą, że chory
był opis, a nie kod.

## 3. Druga liczba jest listą, a nie skanem, i to jest wynik pomiaru

Napisałem najpierw automat: szukaj markera wejścia syntetycznego (`tempfile`, „drzewo
próbne", „wejście syntetyczne", „kontrola przyrządu") w definicji obejmującej zdanie.
Dał **dwanaście pokrytych na osiemnaście** — i **cztery z tych dwunastu są fałszywe**.
Wszystkie cztery tam, gdzie zakresem jest moduł albo funkcja na czterysta wierszy:

| zdanie w zakresie | odległość markera od zdania |
|---|---:|
| funkcja na 401 wierszy | +179 wierszy |
| moduł na 921 wierszy | −437 wierszy |
| moduł na 768 wierszy | −196 wierszy |
| moduł na 181 wierszy | −30 wierszy (jedyny z czwórki prawdziwy) |

Marker leżący czterysta wierszy od zdania nie mówi o tym zdaniu nic. Liczba
wyprowadzona z takiego automatu byłaby dokładnie tym cichym sitem, którego ta pozycja
szuka — więc **liczby z automatu nie podaję, podaję listę przeczytaną**. Bramka
pilnuje, żeby lista była PEŁNA: każde znalezione zdanie musi stać w jednym z dwóch
worków, a worki muszą być rozłączne i sumować się do całości.

## 4. Granica wzorca, zmierzona i powiedziana wprost

Wzorzec znajduje zdania, które **przyznają się** do rodziny: słowem „ubezpieczenie",
„zmierzona konieczność" albo „kontrola wyszła ZIELONA". Rodziny to nie wyczerpuje
i **to nie jest domysł**: pole „Dlaczego" tej pozycji wymienia jako jej członków dwa
mechanizmy, których wzorzec nie znajduje, bo żaden z nich nie niesie ani jednego
z tych słów. Pierwszy uzasadnia się kosztem skanu i szczelnością odsiania, drugi
podaje pomiar („różnicy nie ma ani jednej") bez nazwania go ubezpieczeniem.

Szersze kryterium jest niemożliwe do utrzymania: samo „nie odróżnia" daje
w `tools/tests/` grubo ponad setkę trafień, w ogromnej większości o czymś zupełnie
innym (tolerancja nie odróżnia gałęzi, commit nie odróżnia przebiegów, nazwa silnika
nie odróżnia wersji). Bramka na takim kryterium świeciłaby na poprawnym tekście
i zostałaby wyłączona, nie poprawiona — ten sam wybór, co przy wzorcu twierdzeń
w raportach.

**Osiemnaście jest więc liczbą zdań JAWNYCH, a nie liczbą mechanizmów bez pokrycia.**
Tej drugiej z tekstu wyprowadzić się nie da i zdanie o tym stoi w kodzie, nie tylko tu.

## 5. Własna sekcja jest wycięta ze skanu, i to jest zmierzone

Ta sekcja **wymienia** słowa, które wzorzec rozpoznaje, więc bramka skanująca samą
siebie zapala się na własnej dokumentacji. Zmierzone: bez wycięcia wzorzec znajduje
tu **cztery** zdania o sobie samym, czyli 22 zamiast 18. Cięcie idzie od NAGŁÓWKA
sekcji, a nie od pierwszej stałej pod nim — cięcie niżej zostawiało jedno trafienie
(19 zamiast 18), bo nagłówek też te słowa wymienia. Ta sama konstrukcja, co wycięcie
własnego docstringa w bramce marginesu.

## 6. Kontrole negatywne

Baza: **36/36**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK`. Przed każdym
przebiegiem czyszczony `__pycache__`; po każdym podstawieniu `diff` z kopią roboczą
i `assert` na dokładnie jednym wystąpieniu wzorca.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | wzorzec traci gałąź o zielonej kontroli | **35/36**, „zdań rodziny jest 6" | gałąź niesie dwie trzecie trafień, nie jest ozdobą |
| KN-2 | jeden wpis skreślony z worka bez pokrycia | **35/36**, „zdanie, którego nikt nie przeczytał" | lista musi być pełna, a nie tylko niepusta |
| KN-3 | własna sekcja NIE jest wycięta | **35/36**, „zdań rodziny jest 22" | liczba cztery z punktu 5 jest zmierzona, nie oszacowana |
| KN-4 | przyrząd bierze każdą funkcję, nie tylko ze zdaniem | **34/36**, „3529" i kontrola przyrządu | kontrola na drzewie próbnym NIE jest pusta |
| KN-5 | zdanie dopisane **bez** wejścia syntetycznego | **35/36**, „bez pokrycia wymieniono 10 przy zapadce 9" | dokładnie to, czego żądało pole „Weryfikacja" |

KN-4 jest tu najważniejsza: zapala **dwa** testy, w tym kontrolę przyrządu na drzewie
próbnym. Bez niej nie byłoby wiadomo, czy ta kontrola w ogóle coś sprawdza — a to
jest ta sama pułapka, o którą pozycja pyta, tylko we własnym kodzie.

## 7. Czego nie zrobiono

- **Nie dopisano brakujących wejść syntetycznych** — „Poza zakresem", i pole mówi
  wprost, że to jest praca po pomiarze. Teraz wiadomo, przy których dziewięciu
  zdaniach taka praca miałaby sens, a przy których nie: przy dwóch zjawisko jest
  nieodtworzone, przy dwóch wejścia nie ma z czego zrobić, przy dwóch poprawiono
  zdanie zamiast kodu, a przy jednym mechanizmu nie ma.
- **Nie poszerzono wzorca o kryteria semantyczne** — punkt 4 mówi, ile by to
  kosztowało.
- **Nie tknięto żadnego z osiemnastu zdań.** Pozycja jest pomiarem.

## 8. Co zauważone przy okazji, nietknięte

Nazwa `_moduly_testowe` istniała już w tym module w innym znaczeniu (z parametrem
katalogu, dla przeglądu mutacyjnego). Moja pierwsza wersja pomocnika nosiła tę samą
nazwę i **przesłoniła tamtą, wywracając cztery testy** — nie dlatego, że coś zepsuła
merytorycznie, tylko przez kolizję nazw w jednej przestrzeni. Zmieniona na
`_moduly_do_skanu_rodziny`. Warte odnotowania, bo moduł ma dziś ponad tysiąc
trzysta wierszy i jest to pierwszy raz, gdy kolizja nazw w nim coś kosztowała.
