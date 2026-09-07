# Zapis czasu zestawu i margines, który przestał być prawdą (6.D26)

**Zmierzone 07.09.2026 na commicie:** `d49a76afdd2a77e28127570a467e905526e8f011`
(gałąź `claude/6d26-zapis-czasu`).

## 1. Co dokładnie było zepsute — bo nie to, co myślałem wpisując pozycję

Wpis 6.D26 twierdził między innymi, że „rozrzut hosta nie jest nigdzie zapisany".
**To było nieprawdą i pierwsze czytanie pliku to pokazało**: docstring
`test_suite_runtime_budget.py` opisuje rzecz dokładnie — kontener **dzielony** z innymi
sesjami, `ps aux` w trakcie pomiaru pokazujący równoległy `dotnet build` i proces
Godota, rozrzut 10,84 s na średniej 70,16 s. Ten plik nie był naiwny.

Zepsute było coś węższego i gorszego: **maksimum było wpisane z ręki jako jedna liczba
z minionej sesji, a margines liczył się wobec niej.**

```python
MEASURED_MAX_WALL_S = 77.04     # „najwyższy z czterech przebiegów"
SUITE_RUNTIME_BUDGET_S = 150.0
```

Docstring podawał mnożnik wprost w tekście, a komentarz przy teście marginesu podawał
**drugi, inny** (dla porządku, bo w kodzie ich już nie ma: „×2" i „ok. 1.95"). Oba były
prawdziwe 05.09.2026 wobec zapisanych 77,04 — i oba **przestały być prawdziwe, nie
zmieniając ani znaku**.

## 2. Ile to naprawdę wynosi

Pięć przebiegów zmierzonych dziś i wczoraj, wpisanych do listy z datą i kontekstem:

| data | s | modułów | na czym |
|---|---|---|---|
| 2026-09-05 | 77,04 | — | najwyższy z czterech tamtej sesji, kontener dzielony |
| 2026-09-07 | 76,518 | 93 | po 6.B30, host spokojny |
| 2026-09-07 | 102,122 | 93 | **ten sam kod**, host pod obciążeniem |
| 2026-09-07 | 83,083 | 95 | po 6.A20, dwa moduły bramek więcej |
| 2026-09-07 | 107,331 | 95 | to samo drzewo, host pod obciążeniem — **najwyższy** |

Maksimum to **107,331 s**, czyli o **39 %** więcej niż zapisane 77,04. Margines progu
150 s wynosi więc **1,3975**, a nie liczbę, którą podawała proza.

Wiersz trzeci i drugi to ten sam kod: 76,5 s i 102,1 s. Różnicę robi host — przy
6.B30 zmierzone osobno: `test_station_layout` daje 34,86 s w drzewie **sprzed** 6.A18
i 34,91 s na `main`, a godzinę wcześniej mierzył 22,7 s. Ten sam moduł, ten sam kod,
1,54 raza rozrzutu.

## 3. Co realnie przepuszczała stara wersja

Nie jest to usterka kosmetyczna. „Bramka na bramkę" ma nie dopuścić progu niższego niż
to, co już zostało zmierzone — bo taki próg zapala się na czerwono **bez żadnego regresu
w kodzie**. Zmierzone:

```
PRZED 6.D26 (maksimum zamrozone na 77.04):
  prog 100.0 > 77.04 ?  True
  margines 1.298 > 1.2 ? True
  -> bramka na bramke PRZEPUSCILABY prog 100.0 s
  a zestaw naprawde chodzi do 107.331 s, wiec CI szlo by na czerwono na CZYSTYM drzewie

PO 6.D26 (maksimum wyprowadzone = 107.331):
  prog 100.0 > 107.331 ?  False  -> ODMOWA
```

Obniżenie progu do 100 s przechodziło wszystkie testy i dawało czerwone CI na drzewie
bez ani jednej usterki. Po tej zmianie jest odmową.

## 4. Kształt: lista z datami, maksimum wyprowadzone, mnożnik liczony

- `POMIARY` — krotka wpisów `(data, sekundy, modułów, na czym)`. Dopisanie przebiegu
  **automatycznie** zacieśnia raportowany margines; nie da się mieć jednego bez
  drugiego. Dat nie przelicza się ani nie nadpisuje: 77,04 zostaje jako pomiar swojego
  dnia.
- `MEASURED_MAX_WALL_S = max(...)` — wyprowadzone. Test pilnuje, że **nie wróci** jako
  liczba wpisana z ręki, bo wtedy lista byłaby ozdobą obok wartości, która nadal rządzi.
- `MARGIN = SUITE_RUNTIME_BUDGET_S / MEASURED_MAX_WALL_S` — **działanie**, nie zdanie.
- Każdy wpis musi nieść **datę i kontekst**. Pomiar bez kontekstu jest nierozstrzygalny:
  nie da się odróżnić „zestaw przyspieszył" od „tamtego dnia maszyna była spokojna".

**Próg 150,0 zostaje nietknięty.** Jego zmiana jest decyzją o czułości bramki, a nie
skutkiem ubocznym poprawiania zapisu pomiaru — i wpis kolejki mówił wprost, czego nie
wolno: podnieść stałej bez powiedzenia, skąd liczba jest.

## 5. Bramka na prozę, i trzy próby, które ją ukształtowały

Nowy test odmawia, gdy proza tego pliku podaje **mnożnik**, którego nie daje `MARGIN`.
Jego dzisiejszy kształt nie jest projektem od stołu — jest wynikiem trzech własnych
potknięć, każdego złapanego przez inne narzędzie:

1. **Za szeroki.** Pierwsza wersja brała za mnożnik każdą liczbę w pobliżu słowa
   „margines" i zapaliła się na `77,04` — czyli na **pomiarze**, w zdaniu o tym, wobec
   czego margines się liczył. Poprawka: liczba musi stykać się ze znacznikiem mnożenia.
2. **Skanował sam siebie.** Docstring testu **opisuje** składnię, którą test rozpoznaje,
   więc musi te mnożniki wymienić jako przykłady — i bramka zapaliła się na własnej
   dokumentacji. Poprawka: własny test wycięty ze skanowania, z powodem w kodzie. Bramka
   świecąca na poprawnym tekście zostaje wyłączona, nie poprawiona.
3. **Przestał cokolwiek sprawdzać.** Po wycięciu własnego docstringa w pliku nie zostało
   **ani jednego** zdania z mnożnikiem, więc pętla nie miała po czym iterować i test
   przeszedł **bez ani jednej asercji**. Złapała to bramka asercji z #139:
   ```
   FAIL test_the_prose_does_not_quote_a_margin_that_the_numbers_do_not_give:
   przeszedł bez wykonania ani jednej asercji — cichy skip zamiast testu
   ```
   Poprawka jest tu ważniejsza od samego błędu: test sprawdza teraz **narzędzie**, nie
   tylko dzisiejszy tekst. Za każdym przebiegiem weryfikuje, że detektor łapie
   podstawione zdanie nieaktualne, przepuszcza zdanie zgodne z `MARGIN`, **nie** bierze
   pomiaru za mnożnik i **nie** wchodzi w mnożniki spoza zdań o marginesie.
4. **Kropka dziesiętna urywała okno.** Kontrola narzędzia zgłosiła „detektor nie widzi
   zdania, które ma widzieć" na zdaniu zbudowanym przez `%.2f`. Okno zdania wykluczało
   każdą kropkę, żeby nie wyjść za zdanie — a `1.40x` widziało jako `1`. Repozytorium
   pisze mnożniki przecinkiem, więc przy prawdziwym tekście to nie wyszło; wyszło
   dopiero przy kontroli. Kropka jest teraz przepuszczana, gdy stoi przed cyfrą.

**Czego ta bramka nie łapie, świadomie:** zdania „margines wynosi 1,40" bez znacznika
mnożenia. Węższe kryterium przepuszcza taki zapis, szersze zapala się na każdej liczbie
w okolicy — punkt 1 pokazał, jak to wygląda.

## 6. Kontrole negatywne — WYKONANE, cztery

```
KN-1  nieaktualny mnoznik wraca do prozy
      FAIL ..._does_not_quote_a_margin_...: proza podaje mnoznik 2.0, a MARGIN = 1.3975
KN-2  maksimum wpisane z reki zamiast wyprowadzone
      FAIL test_the_recorded_maximum_is_derived_not_typed_in
KN-3  pomiar bez kontekstu ("szybko")
      FAIL test_every_recorded_run_says_when_and_on_what_it_was_measured:
      kontekst ma mowic, na czym i w jakich warunkach: ('2026-09-07', 'szybko')
KN-4  prog obnizony pod zmierzone maksimum (150 -> 100)
      FAIL test_budget_stays_above_the_measured_maximum_with_a_real_margin: (100.0, 107.331)
```

KN-4 jest tą, która mierzy wartość całej zmiany: **przed nią przechodziła** (§3).

## 7. Czego świadomie nie zrobiono

- **Nie tknięto progu bramki** (stała `SUITE_RUNTIME_BUDGET_S`, wartość jak w §4).
  Jego zmiana jest decyzją o czułości bramki, nie skutkiem poprawiania zapisu pomiaru.
- **Nie przeliczono 77,04.** Dat pomiarów się nie przelicza; wpis stoi z datą
  05.09.2026 i kontekstem tamtej sesji.
- **Nie tknięto pomiarów per moduł w `reports/test-all-runtime-gate.md`.** Tamten raport
  opisuje swój dzień; ten opisuje swój.
- **Nie dodano automatycznego dopisywania przebiegów do `POMIARY`.** Wpis, który dopisuje
  się sam, przestaje być czyimś świadomym pomiarem, a kontekst („host pod obciążeniem")
  jest właśnie tym, czego automat nie wie. Wpisy zostają ręczne, a bramka pilnuje, żeby
  każdy miał datę i kontekst.
