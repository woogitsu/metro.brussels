# Test zakładał wolną nazwę w katalogu tymczasowym (6.D84)

**Zmierzone 09.09.2026, odtworzone 10.09.2026 na:** `db0be47`, kontener tej sesji.
**Przyrząd:** `python3 tools/tests/test_all.py test_assertion_gate.py` przy nazwie
wolnej i zajętej, trzy kontrole negatywne z `md5sum -c` po każdym powrocie.

---

## 1. Pomiar, odtworzony na dzisiejszym drzewie

```
== BASELINE (nazwa wolna) ==      27/27 przeszło
== nazwa ZAJĘTA ==                26/27 przeszło
   FAIL test_gate_catches_the_pr139_shape_of_a_silent_skip:
        ścieżka udająca brakujący artefakt jednak istnieje …
```

Wpis pozycji podawał 23/23 i 22/23 — liczby z 09.09.2026. Dziś moduł ma
**27 testów**, więc te same dwa stany to 27/27 i 26/27; kierunek i przyczyna bez
zmian. Zajęcie nazwy to jedno `mkdir -p` plus jeden plik, bez ruszania repozytorium.

## 2. Co dokładnie było zepsute

```python
nieistniejacy = os.path.join(
    tempfile.gettempdir(), "mbxl-bramka-asercji-nie-ma-takiego-pliku", "chunks.json")
assert not os.path.exists(nieistniejacy), …
```

Ścieżka była **stałą nazwą w cudzym katalogu**, a test tylko ZAKŁADAŁ, że nikt jej nie
zajął. Pada wtedy nie ten test, który coś mierzy, tylko jego strażnik — i pada
**nie ze swojego powodu**.

**Kierunek jest odwrotny niż w usterce, którą ten moduł łapie** (tam bramka milczy,
gdy powinna zgłosić; tu zgłasza, gdy nie powinna) i to nie znosi pozycji: fałszywy
alarm zależny od obcego stanu jest w tym projekcie osobną kategorią (6.D27), bo
bramkę, która pada nie ze swojego powodu, ktoś w końcu wyłączy. Ten sam moduł niesie
zresztą opis identycznej usterki z 05.09.2026 — wtedy ścieżka wskazywała
`build/t400/chunks/…`, czyli plik, który generatory tego repozytorium naprawdę
tworzą. Poprawka przeniosła ją do `/tmp` i **zatrzymała się w połowie**: zniknął
konflikt z artefaktem, został konflikt z nazwą.

## 3. Poprawka: katalog prywatny i dwie asercje zamiast jednej

Ścieżka wskazuje **nieutworzone dziecko** katalogu z `TemporaryDirectory`, więc
nieistnienie jest **skonstruowane**, a nie wyproszone. Asercja nieistnienia mimo to
zostaje — skonstruowany warunek i tak trzeba udowodnić; ten sam wzorzec, co w 6.D57.

Obok stoi **druga** asercja: katalog prywatny musi istnieć. Bez niej sama nieobecność
ścieżki jest prawdziwa także dla literówki w nazwie zmiennej albo dla katalogu, którego
nigdy nie utworzono — a wtedy test przechodzi, **nie mierząc niczego**. To jest te
„dwie rzeczy zamiast jednej", których żąda pole „Wyjście", i nie jest to zdanie
z rozpędu: kontrola negatywna KN-2 pokazuje, że bez tego wiersza literówka przechodzi
zielono.

## 4. Trzy kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | powrót do stałej ścieżki, nazwa zajęta | **czerwona** 26/27 — dokładnie to, czego żąda pole „Skończone, gdy" |
| KN-2 | literówka w katalogu, **bez** asercji na katalog | **ZIELONA** 27/27 — test mierzy nic |
| KN-2b | ta sama literówka, **z** asercją na katalog | **czerwona** 26/27, „katalog prywatny nie powstał: …-literowka" |

Po KN-1 moduł został puszczony jeszcze raz **przy tej samej zajętej nazwie** i dał
**27/27** — czyli poprawka znosi usterkę, a nie maskuje ją przypadkiem czystego `/tmp`.

KN-2 wyszła **zielona** i jest tu wypisana razem z tym wynikiem, bo to ona uzasadnia
drugą asercję: bez niej „poprawka" polegająca na wskazaniu ścieżki w nieistniejącym
drzewie byłaby nieodróżnialna od prawdziwej.

## 5. Czego NIE zrobiłem

**Nie tknąłem tego, co ten test sprawdza merytorycznie** — pole „Poza zakresem".
Kształt kodu atrapy (`if not os.path.isfile(path): return`) zostaje bajt w bajt, bo
o ten kształt w teście chodzi, a nie o konkretny plik.
**Nie przejrzałem pozostałych modułów** pod kątem tej samej rodziny. Test o dwa niżej
(`test_gate_catches_the_silent_skip_even_when_the_artefact_is_there`) używa katalogu
prywatnego od początku i był w polu „Wejście" wymieniony jako wzorzec — reszty drzewa
ta pozycja nie obejmuje.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_assertion_gate.py     (nazwa wolna)
  -> 27/27 przeszło
python3 tools/tests/test_all.py test_assertion_gate.py     (nazwa ZAJĘTA)
  -> 27/27 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 96,785 s, 2143 testów, 113 modułów, kod 0
```

Liczba testów **bez zmiany**: pozycja nie dopisuje testu, tylko wzmacnia istniejący
o drugą asercję.
