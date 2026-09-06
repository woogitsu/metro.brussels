# Wspólny dziennik przeglądu mutacyjnego mieszał wyniki, a nie tylko przeszkadzał

**Zmierzone 06.09.2026 na commicie:** `05c0f59`

## 1. Co wiersz kolejki mówił, a co jest naprawdę

Pozycja 6.B17 opisywała rzecz tak: domyślna ścieżka dziennika jest jedna na całą
maszynę, więc dwa przebiegi dopisują do tego samego pliku, a wznowienie pomija cudze
wyniki jako swoje. To jest prawda, ale **za słaba**.

Prawdziwy skutek jest ostrzejszy i widać go w jednym wierszu `tools/tests/mutation_sweep.py`:
wynik przebiegu czytany jest **z całego dziennika**, a nie z wpisów tego przebiegu.
Cudze wpisy nie są więc pomijane — one **wchodzą do raportu jako wynik tego pomiaru**.

## 2. Kontrola wykonana

Dziennik z dwoma wpisami: jeden dotyczy modułu, o który przebieg pyta, drugi zupełnie
innego modułu. Wywołana dokładnie ta droga, którą idzie przegląd:

```
$ python3 - <<'PY'
  wyniki = mutation_sweep.read_journal(dziennik)      # ta sama funkcja, co w sweep()
  wyniki.sort(key=lambda r: (r["plik"], r["wiersz"]))
  tekst = mutation_sweep.report(wyniki, "test")
PY
read_journal zwrocil wpisow: 2
pliki w wyniku: ['tools/blender/lod_paths.py', 'tools/track/detail_layout.py']
raport wymienia obcy modul: True
   > ### `tools/track/detail_layout.py` — 1
```

**Raport przebiegu, który dotyczył wyłącznie jednego modułu, dostał sekcję drugiego.**
Nie ostrzeżenie, nie adnotację — pełnoprawną sekcję, nieodróżnialną od wyniku pomiaru.

Znalezione przy pozycji 6.B14, gdzie dwa agenty liczyły równolegle na jednej maszynie.
Obejściem był wtedy własny dziennik, ale narzędzie nie sygnalizowało niczego i nic
nie chroniło następnego, który o tym nie będzie wiedział.

## 3. Poprawka

**Ścieżka domyślna jest jedna na PRZEBIEG, nie jedna na maszynę.** Nazwa zależy od
trzech rzeczy, które rozstrzygają, czego przebieg dotyczy: commita, klas operatorów
i zawężenia `--only`. Dwa przebiegi różniące się którąkolwiek z nich mierzą co innego
i nie mają prawa dzielić pliku; dwa zgodne we wszystkich trzech to **ten sam pomiar**,
więc wznowienie ma je znaleźć.

**Dziennik z wpisami spoza przebiegu przerywa start**, kodem wyjścia 2 i komunikatem,
który mówi, ile wpisów, z jakich plików i dlaczego to ma znaczenie. To chroni także
dziennik podany ręcznie przez `--journal`, którego pierwsza połowa poprawki nie dotyka.

Kryterium „obcy" to **plik spoza zbioru przebiegu** i nic więcej. Wpis o tym samym
pliku obcym nie jest — to wznowienie i ma działać.

## 4. Kontrole negatywne — wykonane

### 4.1 Ścieżki różnych przebiegów są różne, a tego samego przebiegu te same

```
inny moduł  : 9af2a0cbae03 != b9cd18f90319  -> True
inne klasy  : 9af2a0cbae03 != 063a9a7f2e16  -> True
inny commit : 9af2a0cbae03 != 6ccbe5fcb8b6  -> True
te same klasy w innej kolejności to TEN SAM przebieg -> True
```

Ostatni wiersz jest **kontrolą negatywną wbudowaną w test**: gdyby nazwa zależała
od czegoś jeszcze — choćby od kolejności klas albo od czasu — wznowienie nigdy nie
znalazłoby swojego dziennika, a „jeden na przebieg" znaczyłoby „nowy za każdym razem".

### 4.2 Obcy wpis przerywa przebieg

```
[MUTACJE] PRZERWANE — dziennik <ścieżka> niesie 1 wpisów spoza tego przebiegu,
  z plików: tools/track/detail_layout.py.
  Wynik przebiegu czytany jest Z CAŁEGO dziennika, więc te wpisy trafiłyby
  do raportu jako wynik TEGO pomiaru.
  Podaj własny --journal albo skasuj tamten plik.
kod wyjścia: 2
```

### 4.3 Własny wpis NIE przerywa — wznowienie nadal działa

Bez tej kontroli poprawka mogłaby po prostu odmawiać zawsze i przeszłaby 4.2.

```
[MUTACJE] wznowienie z <ścieżka>: 1 z 2 już policzonych
tools/blender/lod_paths.py:28 prog `0` -> `1`
razem: 1
```

## 5. Znalezione obok i ŚWIADOMIE NIETKNIĘTE

**Wpis dziennika nie niesie commita, a identyfikator mutacji to `plik:wiersz:przesunięcie
bajtowe`.** Dziennik z wcześniejszego drzewa może więc podstawić wynik zapisany dla
innego kodu — wystarczy, że przesunięcie bajtowe wypadnie tak samo. Docstring przy
wznowieniu twierdzi, że „zmiana kodu między przebiegami nie przemyci starego wyniku
pod nową mutację"; jest to prawdą tylko wtedy, gdy zmiana przesunie offsety.

Tego **nie naprawiam w tej pozycji** i nie jest to przeoczenie: pole „Poza zakresem"
pozycji 6.B17 mówi wprost „zmiana formatu dziennika i mechaniki wznawiania — pozycja
dotyczy **ścieżki**, nie tego, co się w niej zapisuje". Granicę tę zapisałem rano,
przy uzupełnianiu kolejki, i teraz mnie ona wiąże. Znalezisko idzie do kolejki jako
osobna pozycja.

**Jedno odstępstwo, wymuszone i nazwane:** `--only` zawęża teraz zbiór mutacji PRZED
czytaniem dziennika, a nie po. Bez znajomości zbioru plików przebiegu nie da się
sprawdzić, czy dziennik niesie cudze wpisy — a to sprawdzenie jest treścią poprawki.
Dla przebiegu bez `--only` kolejność nie zmienia niczego, bo zbiorem jest wtedy całość.

## 6. Dane do pozycji 6.B18

Przy okazji tej pozycji padł pomiar wart zapisania: przebieg na module o **dwóch**
mutacjach nie domknął się w **ponad dwadzieścia minut**, przy obciążeniu maszyny
**1,04** — czyli bez współbieżności, która zatrzymała pomiary w 6.B13 i 6.B14.
Przyczyna leży więc w samym narzędziu, nie w dzieleniu maszyny, i to jest dokładnie
pytanie pozycji 6.B18.

## 7. Testy

Trzy nowe w `tools/tests/test_mutation_sweep.py`, zestaw **1697 → 1700**. Drugi z nich
opisuje zachowanie **bez** poprawki — gdyby kiedyś ktoś uznał odmowę za nadgorliwość,
ten test pokazuje, co się wtedy dzieje.
