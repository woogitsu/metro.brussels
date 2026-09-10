# Klasa pochodzenia parametru nieaktualna w dwóch plikach (6.D89)

**Zmierzone 09.09.2026, przeliczone 10.09.2026 na:** `35c05e8`, kontener tej sesji.
**Przyrząd:** przejście po czterech zapisach klas, `python3 tools/tests/test_all.py`,
pięć kontroli negatywnych z `md5sum -c` po każdym przywróceniu.

---

## 1. Cztery zapisy obok siebie

```
docs/02-simulation.md:3      spec, observed, est, design_model      DEFINICJA, 4 klasy
.claude/skills/sim-physics/  spec, est, design                      kopia, 3 klasy
docs/07-open-data-research   spec, est, design                      kopia, 3 klasy
data/vehicle/m7-spec.json    spec x15, design_model x18             użycie
```

Rozjeżdżała się **jedna nazwa z trzech**: `design` nie jest klasą tego dokumentu
(jest `design_model`) i nie występuje w danych ani razu. Czwartej klasy — `observed` —
obie kopie nie wymieniały **wcale**.

`est` w danych pojazdu **nie występuje ani razu**, choć dokument nadal ją definiuje —
i to jest stan poprawny, bo definiuje ją jako „oszacowanie historyczne do
usunięcia/weryfikacji", czyli jako klasę, której obecność byłaby usterką.

**To nie jest „skrót rozjechał się z dokumentacją".** Starsza litera słownika
przetrwała w DWÓCH plikach, gdy dokument modelu i dane pojazdu przeszły na nowszą.

## 2. Poprawka

Skrót i `docs/07` **odsyłają** do `docs/02-simulation.md` zamiast powtarzać listę.
Cytaty historyczne w `docs/08-m7-ground-truth.md` (`155,0 t est`, `206,94 t est`)
zostają nietknięte — pole „Poza zakresem" mówi o nich wprost.

**Nazwy wycofanej nie zapisałem w grawisach**, choć oba pliki wspominają o zmianie:
grawisy znaczą w tym repozytorium „to jest nazwa z obowiązującego słownika", więc
historyczna wzmianka w grawisach byłaby dokładnie tym rozjazdem, który ta pozycja
zamyka. Bramka zapaliła się na mojej pierwszej wersji tekstu i to ona wymusiła
tę poprawkę.

## 3. Reguła jest ODWROTNA, niż wygląda na pierwszy rzut oka

Naturalne „każda cytowana nazwa musi być znana" wymaga rozstrzygnięcia, **który**
napis w grawisach jest nazwą klasy — a to jest heurystyka na prozie. Pierwsza wersja
próbowała po wierszu, potem po akapicie zawierającym słowo „klas"; wersja liniowa
przepuściła nazwę stojącą w drugiej linii złamanego zdania, a akapitowa zgłosiła
**`as_of`** z listy pól metadanych, czyli nazwę, która klasą nie jest.

Reguła dzisiejsza pytania nie stawia: plik cytujący **nie wymienia klas w ogóle**,
tylko odsyła do dokumentu. Do tego druga bramka żąda, żeby odesłanie **było** — bez
niej pierwsza jest zielona także dla pliku, z którego wypadło jedyne zdanie kierujące
czytelnika do definicji.

**Czego ta para nie złapie, i mówię to wprost:** nazwy zupełnie nowej, która nie jest
ani klasą zdefiniowaną, ani wycofaną. Złapie ponowne wpisanie listy i powrót nazwy
wycofanej — czyli dwa kształty, które w tym repozytorium wystąpiły.

## 4. Zbiór jest PARSOWANY, nie przepisany

Gdyby stał w teście jako lista, byłby **trzecią** kopią tej samej wiedzy i rozjechał
się jak dwie poprzednie. Dopisanie klasy do dokumentu nie zapala niczego; kontrola
przyrządu podstawia dokument z klasą `nowa_klasa` i żąda, żeby parser ją zobaczył,
a napis w grawisach **bez** znaku równości (nazwa parametru, ścieżka) — żeby zignorował.

Osobna kotwica pilnuje, że dokument nadal definiuje cztery klasy zmierzone dziś:
zawężenie słownika jest niewidoczne dla dwóch bramek wyżej (nikt nie cytuje
`observed`, więc jej zniknięcie nikomu nie przeszkadza), a ma być widoczne w diffie.

## 5. Pięć kontroli negatywnych, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`. Cache bajtkodu czyszczony przed każdym
przebiegiem (powód z 6.D86).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | dawna litera wraca do skrótu | **czerwona** 4/5 — „`est` — klasa wymieniona zamiast odesłania" |
| KN-2 | odesłanie znika ze skrótu | **czerwona** 4/5 — „nie odsyła do `docs/02-simulation.md`" |
| KN-3 | dane pojazdu dostają klasę spoza dokumentu | **czerwona** 3/5 — dwie bramki naraz |
| KN-4 | dokument przestaje definiować `observed` | **czerwona** 3/5 — „zawężenie ma być widoczne" |
| KN-5 | zbiór wpisany na sztywno zamiast parsowany | **czerwona** 4/5 — kontrola przyrządu |

KN-3 zmieniała `data/`; plik przywrócony, `md5sum -c: OK`, `git status data/` pusty.

## 6. Czego NIE zrobiłem

**Nie zmieniłem klasyfikacji ani cytatów historycznych** — pole „Poza zakresem".
Żadna wartość `status` w `data/vehicle/m7-spec.json` nie została ruszona.
**Nie tknąłem `docs/05-glossary.md`**, choć stoi w polu „Wejście": sprawdzone —
nie zawiera ani jednej nazwy klasy pochodzenia, więc nie było czego poprawiać.
**Nie objąłem bramką `docs/21-measured-vs-assumed.md`**, który klas używa obficie
(`design_assumption` x14, `spec` x15, `design_model` x6). Ten dokument nie jest
kopią listy — on **klasyfikuje konkretne parametry**, więc reguła „nie wymieniaj
klas, odsyłaj" byłaby dla niego nieprawdziwa. Objęcie go wymaga innej reguły
i własnego pomiaru.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py test_provenance_classes.py
  -> 5/5 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 100,298 s, 2155 testów, 114 modułów, kod 0

git status --short data/   ->  pusto
```

Zestaw urósł z **2150** do **2155**, modułów z **113** na **114**: nowy moduł
`tools/tests/test_provenance_classes.py`.
