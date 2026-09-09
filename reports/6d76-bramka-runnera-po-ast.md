# Bramka zepsuta w obie strony z jednej przyczyny (6.D76)

**Zmierzone 09.09.2026 na:** `063de5b`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_assertion_gate.py`, `tools/tests/test_all.py`,
`python3 tools/tests/test_all.py`, wywołanie bramki wprost, z pominięciem runnera.

---

## 1. Usterka: jedna przyczyna, dwa przeciwne skutki

Bramka pilnująca, że runner testów ładuje moduły przez licznik asercji, robiła
cztery dopasowania `napis in treść_pliku`. Z tego wynikały dwie rzeczy naraz.

**Strona pierwsza — fałszywy alarm na poprawnej treści.** Pilnowane wywołania są
w `test_all.py` zapisane bez spacji po przecinku, czyli w formie, którą pierwsze
narzędzie stylu przepisuje:

```
ORYGINAL   PASS 'AG.load_instrumented(path,name)'
PEP8       FAIL 'AG.load_instrumented(path,name)'
```

Semantyka identyczna, `ast.parse` przechodzi, bramka czerwona. To rodzina 6.D27:
bramkę, która pada na poprawnej treści, wyłącza pierwszy zirytowany człowiek.

**Strona druga — cisza na rzeczywistym obejściu, i ta jest groźniejsza.** Podmiana
ładowania modułów na wykonanie skompilowanego źródła, **bez ani jednego wystąpienia
zakazanej nazwy**, przechodziła wszystkie cztery asercje na zielono — przy modułach
idących bez licznika. Jedyna bramka pilnująca, że asercje są liczone, przechodziła
na runnerze, który ich nie liczył. To rodzina 6.D65.

Obie strony wychodzą z tego samego: dopasowanie tekstowe nie odróżnia kodu od
komentarza ani od napisu i zależy od formatowania.

## 2. Poprawka

Bramka czyta teraz **drzewo składni**, nie treść pliku. Drzewo nie widzi ani spacji,
ani komentarzy.

Zakaz jest przy tym wyrażony **pozytywnie**, i to jest istotniejsze od samej zmiany
techniki: funkcja odkrywania modułów musi wołać `AG.load_instrumented`. Lista
zakazanych sposobów ładowania (`exec`, `eval`, importlib i pokrewne) stoi obok jako
nazwanie znanych obejść, ale nie ona rozstrzyga. Zakaz jednej nazwy łapał jedno
obejście; warunek pozytywny łapie każde, **nie znając jego nazwy z góry** — co
zostało zmierzone w §3.

## 3. Kontrole negatywne — wykonane

| mutacja | oczekiwane | skutek |
|---|---|---|
| przeformatowanie wywołań stylem (spacje po przecinkach) | **przejść** | `25/25 przeszło` — fałszywy alarm zniknął |
| ładowanie przez wykonanie skompilowanego źródła | **paść** | `BRAMKA PADŁA: runner nie wola bramki: ['AG.load_instrumented']` |
| własny loader, **nieznany liście zakazanych nazw** | **paść** | ta sama, prawdziwa odmowa |

`md5sum -c` po każdej: `OK`.

Kontrola trzecia jest tu najważniejsza: sprawdza warunek pozytywny na obejściu,
którego lista nie zna. Bez niej poprawka byłaby tylko dłuższą listą zakazów.

## 4. Pierwszy odczyt kontroli był mój błąd, nie wynik

Dwie pierwsze próby kontroli drugiej i trzeciej dały `0/0 przeszło` i wziąłem to za
wynik nierozstrzygający. To nie był wynik — to było **załamanie się runnera**,
którym te bramki są uruchamiane: mutacja psuje `test_all.py`, a `test_all.py` jest
zarazem narzędziem pomiaru.

Powtórzone z pominięciem runnera (wywołanie funkcji bramki wprost) dają odmowę
z komunikatem. Wniosek metodyczny: **przyrządu nie mierzy się nim samym**, a gdy nie
ma innego wyjścia, trzeba to powiedzieć wprost i obejść, nie interpretować.

Drugi błąd tej samej próby: filtrowałem wyjście grepem po nazwie własnego testu,
więc **nie widziałem prawdziwego wiersza porażki**. Za wąski filtr zamienił
rozstrzygający pomiar w pozorną ciszę.

## 5. Podejrzenie, które okazało się nieprawdziwe

`0/0 przeszło` wyglądało jak kolejny przypadek rodziny 6.D65 — zestaw meldujący
sukces, nie wykonawszy niczego. **Sprawdzone i nieprawdziwe:**

```
kod=1  ostatni wiersz:   FAIL <bramka asercji>: nie odkryto ani jednego testu
                              — bramka nie ma na co patrzeć
```

`suite_verdict` odmawia przy zerze odkrytych testów i kod wyjścia jest niezerowy.
Projekt ma to obsłużone i zapisane. Wpisuję to tutaj, bo podejrzenie bez pomiaru
zostałoby w głowie jako „chyba jest jeszcze jedna dziura", a nie ma jej.

## 6. Weryfikacja

```
  25/25 przeszło       test_assertion_gate.py
  RAZEM 101.989 s, 2070 testów, 110 modułów
kod=0
```

Liczba testów bez zmian: poprawka zamienia treść jednej bramki, nie dokłada nowej.

## 7. Czego świadomie nie zrobiono

**Nie przeformatowano `test_all.py`.** Bramka po poprawce przepuszcza oba zapisy,
więc styl tego pliku jest teraz decyzją niezależną od niej — i pozostaje osobną
decyzją, nie skutkiem ubocznym tej pozycji.

Nie ruszono trzech pozostałych bramek tego modułu, które nadal dopasowują napisy
(`test_gate_runner_counts_skipped_tests_outside_the_passed_total` i pokrewne).
Każda pilnuje **wypisu**, nie wywołania, a wypis jest napisem z natury —
przeniesienie ich na AST nie miałoby czego czytać. Ta różnica jest właściwym
kryterium: po AST idzie to, co jest kodem, po napisie to, co jest tekstem.
