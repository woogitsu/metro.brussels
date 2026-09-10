# 6.D103 — trzy gałęzie schematu, których nie dotyka ani jeden wpis

**Zmierzone 10.09.2026 na:** `fd48723`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_audio_rights.py` (`galezie`, `warunek_zachodzi`,
`niezgodnosci_podschematu`, `niezgodnosci_warunkowe`, wspólny `_niezgodnosci_pol`),
`data/audio/audio-manifest.schema.json` i `data/audio/placeholders.json` — oba
wyłącznie do czytania.

---

## 1. Czego pętla z 6.D85 nie widziała

Schemat ma **trzy** gałęzie `allOf`, każda w kształcie `if`/`then`:

| warunek | czego żąda |
|---|---|
| `source_type = licensed_library` | `license` niepusty |
| `source_type = original_recording` | `recorded_by`, `recorded_at`, `location`, `source_file_hash` |
| `rights_status = cleared` | `permission_ref` **albo** `license` (`anyOf`) |

Pętla zgodności z 6.D85 czyta wyłącznie `properties` najwyższego poziomu, a `license`
nie stoi w jego `required`. Wpis z `source_type = licensed_library` **bez licencji**
przechodził ją cicho, choć schemat go w tej gałęzi żąda.

Trzy istniejące testy modułu czytają `allOf` — ale pytają **„czy schemat tego
wymaga"**, a nie **„czy wpis to spełnia"**. To są dwa różne pytania i tylko pierwsze
miało dotąd odpowiedź.

## 2. Główny wynik pomiaru: dzisiejszy manifest nie wpada pod ani jedną gałąź

```
wpisów: 13
source_type:   Counter({'placeholder': 13})
rights_status: Counter({'placeholder': 13})
license nie-null: 0
permission_ref nie-null: 0
```

Wszystkie trzynaście wpisów to zastępniki. Żaden nie ma `source_type` ani
`rights_status` wyzwalającego którąkolwiek gałąź, więc nowa pętla jest dziś cicha
**nie dlatego, że wpisy gałęzie spełniają, tylko dlatego, że ich nie dotyczą**.

Pole „Skończone, gdy" żąda, żeby dzisiejszy manifest nie dawał fałszywego alarmu —
i nie daje. Ale powód jest mocniejszy, niż to zdanie sugeruje, i cały ciężar dowodu
niesie kontrola na wejściu syntetycznym. Stoi to wprost w docstringu testu, żeby
cisza nie została kiedyś wzięta za wynik.

## 3. Jeden czytnik pól, nie drugi

`properties` gałęzi sprawdza **ten sam** `_niezgodnosci_pol`, który sprawdza poziom
najwyższy — wydzielony z istniejącej pętli, a nie napisany obok. Drugi czytnik tych
samych reguł rozjechałby się po cichu, a rozjazd akurat tej pary znaczyłby, że gałąź
przyjmuje wartość, którą poziom najwyższy odrzuca.

Doszła do niego **rekurencja w obiekt**: gałąź `original_recording` żąda `location`
z własnym `required` i własnymi `properties`. Na poziomie najwyższym `location` ma
`oneOf` i przez to żadnej rekurencji nie wyzwala, więc dodanie jej niczego tam nie
zmienia — sprawdzone przebiegiem przed i po (10/10 → 10/10 na testach sprzed tej pozycji).

## 4. Dwie rzeczy, które musiałem poprawić, bo pokazała je kontrola, nie lektura

### 4.1 `required` pytało o niepustą wartość zamiast o klucz

Pierwsza wersja odrzucała w `required` także `None`. Werdykt wychodził ten sam, ale
**powód był inny niż ten, który poda walidator**: JSON Schema `required` pyta
wyłącznie o obecność klucza, a `null` odrzuca dopiero reguła typu z `properties` tej
samej gałęzi. Dzisiejszy manifest nie ma ani jednego z tych kluczy, więc różnicy nie
miałoby co zmierzyć — mierzy ją teraz osobna asercja na wpisie z `permission_ref: null`.

Ta asercja też musiała zostać poprawiona: pierwsza wersja czytała **złożony**
komunikat `anyOf`, w którym „wymaga tego pola" stoi zgodnie z prawdą — dla `license`,
którego klucza naprawdę nie ma. Czyta więc dziś pojedynczy wariant, w izolacji.

### 4.2 Klauzula `required` w `if` nie robiła nic, choć docstring twierdził, że robi

**KN-4 wyszła zielona.** Zdjęcie sprawdzania `required` z `warunek_zachodzi` niczego
nie zapalało. Powód: warunek porównywał `asset.get(pole) != const`, czyli zestawiał
`None` ze stałą — warunek odpadał sam, a klauzula `required` była martwa.

W JSON Schema `properties` jest dla pola nieobecnego **pusto spełnione**, więc bez
`required` wpis bez `source_type` wpadałby pod gałąź, która go nie dotyczy. Dopiero
po wiernym odwzorowaniu tej pustej prawdy klauzula stała się nośna i **KN-4b świeci
na czerwono**, wypisując pięć pól z dwóch gałęzi naraz:

```
FAIL: wpis BEZ `source_type` wpadł pod gałąź warunkową:
  [('license', …), ('recorded_by', …), ('recorded_at', …),
   ('location', …), ('source_file_hash', …)]
```

To jest ta sama rodzina, co usterki tropione w tym repozytorium od 6.D27: zdanie
w dokumentacji mówiło o zabezpieczeniu, którego kod nie miał.

## 5. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` kopii na bok i `md5sum -c` po przywróceniu, z **`__pycache__`
czyszczonym przed każdym przebiegiem** (procedura z 6.D102, scalona godzinę wcześniej).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | czytnik gałęzi ślepy (pusta lista) | **10/12**, dwa testy, w tym zapadka `LICZBA_GALEZI` |
| KN-2 | `anyOf` pomijane — trzecia gałąź bez obsługi | **11/12** |
| KN-3 | `anyOf` spełnione, gdy JAKIKOLWIEK wariant zawodzi (`any` zamiast `all`) | **11/12** |
| KN-4 | warunek bez sprawdzania `required` | **12/12 — ZIELONA** |
| KN-4b | to samo po odwzorowaniu pustej prawdy | **11/12** |
| KN-5 | rekurencja w obiekt zdjęta | **11/12** |
| KN-6 | gałąź przestaje czytać wspólny czytnik pól | **11/12** |
| KN-7 | zapadka `LICZBA_GALEZI`, zaniżona do zera | **11/12** |

Po każdej: `md5sum -c` → `OK`.

KN-3 jest tu warta osobnego zdania: `anyOf` spełnione „gdy którykolwiek wariant
zawodzi" przechodzi wszystkie testy łamiące gałąź i pada dopiero na kierunku
przeciwnym — „sama zgoda ma wystarczyć". Bez asercji w tę stronę logika `anyOf`
mogłaby być odwrócona i nie byłoby tego widać.

## 6. Czego świadomie nie zrobiłem

- **Nie dopisałem zależności i nie zmieniałem schematu** — pole „Poza zakresem" mówi
  to wprost. Sprawdzanie jest ręczne i celowo głupie, tak jak pętla z 6.D85.
- **`data/` tylko do odczytu.** Ani `placeholders.json`, ani schemat nie zostały
  tknięte; wszystkie wpisy syntetyczne powstają w pamięci jako kopia wpisu wzorcowego.
- **Nie ruszałem trzech istniejących testów czytających `allOf`.** Pytają o schemat
  i to jest osobne, nadal potrzebne pytanie.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

- **`oneOf` na poziomie najwyższym nie jest sprawdzane przez nic.** `location` ma tam
  `oneOf: [null, obiekt]`, a pętla zgodności zna `type`, `enum`, `pattern`, `minLength`
  i od dziś obiekt — `oneOf` mija bez słowa. Dziś żaden wpis nie ma `location`, więc
  nie ma czego złamać; przy pierwszym prawdziwym nagraniu będzie.
- **Gałąź `cleared` nie żąda `as_of`.** Wpis może być „cleared" bez daty, od której to
  obowiązuje. To jest pytanie do schematu, czyli do właściciela, a nie do bramki.
