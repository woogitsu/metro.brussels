# Test zgodności ze schematem nie sprawdzał typów ani wzorców (6.D85)

**Zmierzone 09.09.2026, przeliczone 10.09.2026 na:** `02d8681`, kontener tej sesji.
**Przyrząd:** mutacje `data/audio/placeholders.json`, `md5sum -c` po każdym
przywróceniu, `python3 tools/tests/test_all.py test_audio_rights.py`.

---

## 1. Pomiar, przeliczony — i różni się od wpisu

Wpis pozycji podawał cztery mutacje przechodzące 9/9 z kodem 0. Przeliczenie
na dzisiejszym drzewie daje **trzy z czterech**, i różnica jest pouczająca:

```
contains_voice = "nie"              exit=1   8/9    ZŁAPANE
contains_stib_brand_audio = "nie"   exit=1   8/9    ZŁAPANE
redistribution_allowed = "nie"      exit=0   9/9    PRZESZŁO
processing_chain = "normalizacja"   exit=0   9/9    PRZESZŁO
asset_id = "ZŁY ID!"                exit=0   9/9    PRZESZŁO
pole spoza schematu                 exit=0   9/9    PRZESZŁO
creator = 123                       exit=0   9/9    PRZESZŁO
notes / as_of / source_file_hash    exit=0   9/9    PRZESZŁO
```

**Dwa pola logiczne były chronione PRZYPADKIEM**, nie przez tę bramkę: `contains_voice`
przez test o RODO (`isinstance(..., bool)`), a `contains_stib_brand_audio` przez test
o marce STIB (`is False`, co odrzuca też napis). Trzecie pole logiczne — i to
akurat **`redistribution_allowed`**, na którym `docs/03-legal.md` stawia blokadę
prawną — nie było chronione niczym.

Wpisując do kolejki „typ pola logicznego → 9/9" trafiono więc w prawdę o JEDNYM
z trzech pól logicznych, i to o tym najważniejszym; dwa pozostałe dawały wynik
odwrotny. Ten raport podaje rozbicie, bo różnica zmienia to, co bramka ma robić:
nie chodzi o dopisanie kontroli typu tam, gdzie jej brak, tylko o to, żeby przestała
zależeć od tego, czy inny test przypadkiem pyta o to samo pole.

## 2. Co bramka sprawdzała, a czego nie

```python
for field, rule in properties.items():
    if field not in asset or "enum" not in rule:
        continue
    assert asset[field] in rule["enum"], …
```

Obecność pól wymaganych i przynależność do `enum`. **Typ, wzorzec, długość minimalna
i zakaz pól spoza schematu — nic.** Schemat deklaruje `additionalProperties: false`
i wzorce (`^[a-z0-9][a-z0-9._-]*$` dla `asset_id`, `^sha256:[0-9a-f]{64}$` dla
skrótu), a jedyny istniejący manifest nie był wobec nich sprawdzany wcale.

## 3. Poprawka: mapa typów zamiast zależności

Pole „Poza zakresem" zabrania dopisywania zależności, więc walidatora z biblioteki tu
nie ma. Jest mapa nazw typów JSON Schema na typy Pythona i pętla sprawdzająca cztery
rzeczy, każdą z osobnym powodem w komunikacie: **typ** (także lista typów, np.
`["string", "null"]`), **wzorzec**, **`minLength`**, **`enum`**, plus typ elementów
tablicy i **zakaz pól spoza schematu**.

**`bool` stoi przed `integer` i to nie jest drobiazg składniowy:** w Pythonie `True`
jest instancją `int`, więc mapa bez tego rozróżnienia przepuszczałaby wartość logiczną
w polu liczbowym. Osobna asercja w kontroli przyrządu przybija oba kierunki
(`not _zgodny_typ(True, "integer")` i `_zgodny_typ(True, "boolean")`).

Pole `location` ma w schemacie regułę pustą (`{}`) i zostaje przyjmowane bez warunku —
schemat nic o nim nie mówi, więc bramka też nie może.

## 4. Pięć kontroli negatywnych, każda WYKONANA na prawdziwym manifeście

`md5sum -c data/audio/placeholders.json` po każdym przywróceniu: `OK`; po wszystkich
`git status data/` pusty.

| mutacja | przed | po |
|---|---|---|
| `redistribution_allowed = "tak"` | 9/9, exit 0 | **8/10, exit 1** |
| `processing_chain = "normalizacja"` | 9/9, exit 0 | **8/10, exit 1** |
| `asset_id = "ZŁY ID!"` | 9/9, exit 0 | **8/10, exit 1** |
| pole spoza schematu | 9/9, exit 0 | **8/10, exit 1** — `('pole_ktorego_nie_ma_w_schemacie', 'pole spoza schematu')` |
| `creator = 123` | 9/9, exit 0 | **8/10, exit 1** |

Piąta nie stoi w polu „Skąd" i jest dopisana z pomiaru §1: pola napisowe też nie były
sprawdzane.

**`data/` było przy tym zmieniane i to wymaga nazwania.** `CLAUDE.md` §4.6 czyni ten
katalog tylko do odczytu; mutacje szły na plik w drzewie, bo bramka czyta stałą
ścieżkę, i każda była przywracana z kopii z weryfikacją sumy — ta sama technika, co
przy `md5 Program.cs` w 6.A21. Commit nie niesie ani jednej zmiany w `data/`.

## 5. Kontrola przyrządu, bo cisza sama nic nie znaczy

Pętla po prawdziwym manifeście jest dziś cicha i ma być. Osobny test bierze pierwszy
wpis manifestu jako wzorcowy, podmienia w nim po jednym polu i żąda, żeby każdy
z czterech kształtów zgłosił się z **innym** powodem — plus kierunki przeciwne
(poprawne wartości milczą). Bez tego pusta lista niezgodności byłaby zielona także
wtedy, gdyby pętla przestała cokolwiek sprawdzać.

## 6. Czego NIE zrobiłem

**Nie dopisałem zależności** ani **nie tknąłem schematu** — oba w polu „Poza zakresem".
**Nie wybrałem wariantu z pola „Wyjście" polegającego na przemianowaniu testu**
(„alternatywa uczciwsza: przemianować test na to, co naprawdę sprawdza"): przemianowanie
opisałoby stan, zamiast go zmienić, a mapa typów okazała się krótsza niż spodziewany
koszt — kontrola typów, wzorca i pól dodatkowych mieści się w jednej pętli.
**Nie sprawdzam `allOf`** ze schematu, czyli gałęzi zależnych od `source_type`.
Trzy osobne testy tego modułu czytają je dziś wprost i to zostaje; objęcie ich tą samą
pętlą jest zmianą w tamtych testach, a nie w tym.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py test_audio_rights.py
  -> 10/10 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 98,198 s, 2144 testów, 113 modułów, kod 0

git status --short data/   ->  pusto
```

Zestaw urósł z **2143** do **2144**: doszedł jeden test — kontrola przyrządu.
