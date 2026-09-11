# Decyzja właściciela 11.09.2026 — `as_of` wymagane w gałęzi `cleared`

**11.09.2026**, na `feb4ea1`. Pytanie postawione klikalnie, odpowiedź: **„Tak, wymagane od teraz"**. Odwraca to
rekomendację, którą 6.D125 zapisało tego samego dnia — i dlatego blok rozstrzygnięcia
w `tools/tests/test_audio_rights.py` jest **przepisany, a nie dopisany obok**.

## 1. Co mówiło 6.D125

Że reguła ma stać w bramce, a nie w schemacie, z dwóch powodów: bo zmiana dotyka
`data/` (§4.6, tylko do odczytu), i bo `docs/03-legal.md` **nigdzie nie mówi o terminie**
— żąda zakresu („konkretne zamierzone użycie"), a nie daty. Dołożenie daty było więc
regułą, której dokument prawny projektu nie stawia, czyli **decyzją właściciela, nie
uzupełnieniem luki**. Pozycja policzyła jej koszt i przedstawiła do rozstrzygnięcia.

## 2. Co się zmieniło

Nie liczby — tylko to, czyja jest decyzja. Pomiar zostaje prawdziwy co do cyfry
(powtórzony na `feb4ea1`):

* manifest ma **13** wpisów, wszystkie `rights_status: placeholder`;
* wpisów `cleared` jest **zero** — wymaganie nie dotyka dziś ani jednego;
* **ani jeden** wpis nie niesie własnego `as_of`;
* korzeń manifestu niesie `as_of: 2026-08-31` — datę **audytu pliku**, nie prawa.

§4.6 wymienia dokładnie ten przypadek: `data/` jest do odczytu, „chyba że zadanie mówi
inaczej wprost". Decyzja właściciela jest tym „wprost".

## 3. Co stoi w schemacie

Gałąź `allOf[2].then` (warunek `rights_status == cleared`) dostała **trzy** rzeczy,
nie jedną:

```json
"required": ["as_of"],
"properties": {"as_of": {"type": "string", "minLength": 1, "format": "date"}},
```

Samo `required` przepuściłoby `null` i pusty napis — to ta sama pułapka, którą ten
moduł opisuje przy `permission_ref`: **`required` pyta wyłącznie o obecność klucza**,
a wartość odrzuca dopiero reguła typu z `properties` tej samej gałęzi.

Na poziomie najwyższym `as_of` **zostaje opcjonalne** i to jest część decyzji, a nie
niedoróbka: wpisy `placeholder` daty prawa nie mają i mieć nie muszą. KN-3 pokazuje,
co by było inaczej — wszystkie 13 placeholderów naraz.

## 4. Bramka z 6.D125 zostaje — i nie jest duplikatem

W tym repozytorium **nie ma walidatora JSON Schema** (6.D85 odrzuciło tę zależność),
więc jedynym, co schemat WYKONUJE, są czytniki tego modułu. Reguła zapisana wyłącznie
w schemacie byłaby zdaniem, którego nic nie sprawdza. KN-4 mierzy to wprost: zdjęcie
bramki modułowej zostawia schemat nietknięty, a mimo to coś przestaje działać.

## 5. Kontrole negatywne

Baza `test_audio_rights.py`: **14/14**. `__pycache__` czyszczony przed każdym
przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na obu plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | `required: ["as_of"]` zdjęte z gałęzi (stan sprzed decyzji) | **12/14**, dwa testy |
| KN-2 | zostaje `required`, znika reguła typu | **12/14**, dwa testy |
| KN-3 | `as_of` wymagane BEZWARUNKOWO | **12/14** — pada też walidacja 13 placeholderów |
| KN-4 | bramka modułowa zdjęta, schemat zostaje | **13/14** |

KN-2 jest tu najważniejsza: bez reguły typu wpis `cleared` z `as_of: null` i z `as_of: ""`
przechodziłby, czyli data byłaby wymagana **na niby**.

KN-3 pokazuje drugą granicę tej decyzji — gdyby wymaganie postawić o piętro wyżej,
zapaliłoby się natychmiast na całym dzisiejszym manifeście:

```
FAIL test_audio_placeholders_satisfy_the_schema_they_ship_next_to:
     ('placeholder.traction.drive', ['as_of'])
```

## 6. Weryfikacja

```
  14/14 przeszło        test_audio_rights.py
  2335/2335 przeszło, 122 moduły, KOD=0, RAZEM 165.550 s
```

Zmienione pliki: `data/audio/audio-manifest.schema.json` (trzy linie w jednej gałęzi)
i `tools/tests/test_audio_rights.py`. **Żaden wpis manifestu nie został zmieniony** —
`data/audio/placeholders.json` jest nietknięty, bo zero wpisów `cleared`.

## 7. Czego nie zrobiłem

* **Nie dopisałem `as_of` do żadnego wpisu manifestu.** Wszystkie trzynaście to
  `placeholder`; data prawa przy nich nie znaczyłaby nic.
* **Nie ruszyłem `as_of` w korzeniu manifestu.** Datuje audyt pliku i to jest inne
  zdanie niż data obowiązywania prawa — 6.D125 zmierzyło tę różnicę i ona zostaje.
* **Nie dopisałem terminu do `docs/03-legal.md`.** Dokument żąda zakresu, nie daty;
  decyzja dotyczy modelu danych, a zmiana dokumentu prawnego jest osobnym pytaniem,
  którego nikt nie zadał.
