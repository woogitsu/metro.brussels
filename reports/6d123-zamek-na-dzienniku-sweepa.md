# 6.D123 — zamek na dzienniku: 6.D106 odzyskuje wznowienie, nie tracąc rozdzielenia

**Zmierzone 11.09.2026 na:** `e9a89a1`, kontener tej sesji.
**Przyrząd:** `tools/tests/mutation_sweep.py` (`zajmij_dziennik`, `default_journal`,
`main`), `tools/tests/test_mutation_sweep.py`, sonda `flock` na `/tmp`, trzy przebiegi
prawdziwego sweepa.

---

## 1. Pytanie, na które ta pozycja miała odpowiedzieć

6.D106 rozdzieliło dwa równoległe przeglądy **nazwą** dziennika — dołożyło do niej
element unikatowy dla procesu — bo dwa przebiegi o tych samych czterech członach
dopisywały do jednego pliku, a `read_journal` powtórzeń nie odsiewa: oba raporty
liczyły każdą mutację dwa razy. Ceną było **zdjęcie wznowienia po nazwie domyślnej**.

Zamek rozwiązuje oba naraz — ale ma własne tryby awarii, których 6.D106 nie mierzyło:
zamek po ubitym procesie i zamek na systemie plików bez `flock`. Pole „Wyjście" tej
pozycji żąda **rozstrzygnięcia pomiarem**, a nie wyborem.

## 2. Pomiar: `flock` na tym systemie plików

Sonda na `tempfile.gettempdir()`:

```
[SONDA] tempdir: /tmp
[SONDA] system plikow: ext2/ext3
[A] pierwszy zamek: wziety
[B] drugi uchwyt w tym samym procesie: ODMOWA errno=11
[C] drugi proces przy trzymanym zamku: ODMOWA 11 kod 3
[D1] przy zywym wlascicielu: ODMOWA (dobrze)
[D2] po SIGKILL wlasciciela: WZIETY (dobrze)
[E] plik zostaje: True rozmiar 0
```

**`SIGKILL` nie zostawia zamka osieroconego** i to jest cały warunek tej pozycji:
sygnału nie da się obsłużyć, więc żaden kod sprzątający się nie wykonuje — zwolnienie
przychodzi od jądra, które zamyka opisy plików martwego procesu. Warunek zachodzi,
więc nazwa dziennika wraca do postaci zależnej od treści.

Wiersz `[E]` rozstrzygnął drugą rzecz: **zamek idzie na sam dziennik, nie na osobny
plik `.lock`**. Plik po `SIGKILL` zostaje na dysku; dziennik i tak zostaje, więc osobny
plik dokładałby drugi śmieć bez zysku.

## 3. Co się zmieniło w kodzie

* `default_journal` ma piąty parametr `zamek` i przy zamku dostępnym składa nazwę
  z **czterech** członów, jak przed 6.D106. Znacznik procesu zostaje w nazwie
  **wyłącznie tam, gdzie zamku nie ma** — parametr istnieje po to, żeby ta gałąź dała
  się wykonać na maszynie, która `fcntl` ma, zamiast być kodem, którego nikt nigdy
  nie uruchomił.
* `zajmij_dziennik(path, dostepny=None)` zwraca **trzy** stany: `"wziety"`, `"zajety"`,
  `"bez_zamka"`. Trzy, a nie `None`/uchwyt, bo „nie ma czym zamykać" i „ktoś inny
  trzyma" wymagają od wołającego czegoś innego — pierwsze puszcza przebieg dalej,
  drugie jest odmową. Zlanie ich w jedną wartość dałoby przebieg, który po cichu
  dzieli plik z innym, czyli usterkę z 6.D106 wróconą tylnymi drzwiami.
* `main` bierze zamek **przed pierwszym czytaniem dziennika**. Później byłoby za
  późno: między odczytem a dopisem zmieściłby się cały drugi przebieg.
* Odmowa ma własny kod wyjścia `KOD_ZAJETY_DZIENNIK = 5`, osobny od `2`, bo to inna
  sytuacja i inna rada: tamta mówi „skasuj plik albo podaj własny", ta — „poczekaj
  albo podaj własny".

## 4. Pułapka, na którą sam wpadłem: uchwyt zamka musi kogoś mieć

Pierwsza próba wołała `zajmij_dziennik` dwa razy pod rząd, nie trzymając wyniku
pierwszego wywołania, i **oba razy dostała `"wziety"`**:

```
('wziety', <_io.TextIOWrapper name='/tmp/zz.jsonl' ...>)
('wziety', <_io.TextIOWrapper name='/tmp/zz.jsonl' ...>)
```

Wyglądało to dokładnie jak zamek, który nie działa. Nie działał **GC**: `flock` żyje
tak długo, jak otwarty opis pliku, a uchwyt pierwszego wywołania nie miał do kogo
należeć i został zebrany. Z trzymaną referencją ten sam kod daje:

```
pierwszy: wziety
drugi przy TRZYMANYM pierwszym: zajety
po zamknieciu pierwszego: wziety
```

Stąd `_UCHWYT_ZAMKA` na poziomie modułu — zmienna lokalna w `main` zwolniłaby zamek
przy wyjściu z funkcji, czyli natychmiast po sprawdzeniu — i stąd osobny test, który
czyta ze źródła, że `main` naprawdę przypisuje uchwyt do czegoś trwałego.

## 5. Trzy rzeczy sprawdzone WYKONANIEM, nie rozumowaniem

Pole „Weryfikacja" tej pozycji żąda tego wprost.

**A. Dwa przebiegi naraz — jeden pomiar, jedna odmowa, jeden dziennik.**

```
--- bieg1 ---
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 …
kod1=0
--- bieg2 ---
[MUTACJE] PRZERWANE — dziennik /tmp/metro-mutacje-1a55290f9dfc.jsonl trzyma inny przebieg.
  Wynik czytany jest Z CAŁEGO dziennika, a `read_journal` nie odsiewa powtórzeń, …
kod2=5
--- dzienniki w /tmp ---
/tmp/metro-mutacje-1a55290f9dfc.jsonl
```

Jeden plik, nie dwa — i to jest różnica wobec 6.D106, gdzie rozdzielały je nazwy.

**B. Wznowienie po nazwie DOMYŚLNEJ działa** — czyli cena zapłacona przez 6.D106
wraca:

```
[MUTACJE] wznowienie z /tmp/metro-mutacje-1a55290f9dfc.jsonl: 2 z 2 już policzonych
brak mutacji do sprawdzenia: … przebieg zrobił wszystko, o co go proszono
```

**C. `SIGKILL` w środku prawdziwego przebiegu nie blokuje następnego.** Przebieg ubity
po 12 s, dziennik został na dysku, następny przebieg wystartował bez odmowy:

```
ubity PID=24920
/tmp/metro-mutacje-1a55290f9dfc.jsonl
--- nastepny przebieg po ubiciu ---
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 …
```

## 6. Kontrole negatywne — WYKONANE, nie opisane

`cp` na bok i `md5sum -c` po przywróceniu (nigdy `git checkout`), `__pycache__`
czyszczony przed każdym przebiegiem. Baza `test_mutation_sweep.py`: **125/125**.

Wszystkie przeliczone na jednej bazie: `test_mutation_sweep.py` **126/126**.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | `zajmij_dziennik` zawsze zwraca `"wziety"` | **122/126**, cztery testy |
| KN-2 | `LOCK_NB` zdjęte (zamek blokujący) | **przebieg PRZERWANY po 240 s** |
| KN-3 | `"zajety"` i `"bez_zamka"` zlane w jedną wartość | **122/126**, cztery testy |
| KN-4 | `default_journal` znów zawsze z `PROCES_ZNACZNIK` | **124/126**, dwa testy |
| KN-5 | `global _UCHWYT_ZAMKA` zdjęte z `main` | **125/126** |
| KN-6 | zamek brany PO `read_journal` | **126/126 ZIELONA** — patrz §6a |
| KN-6b | zamek brany PO wywołaniu `sweep` | **125/126** |
| KN-7 | gałąź `bez_zamka` tworzy plik | **125/126** |

KN-2 nie daje liczby i to jest jej wynik: zamek blokujący zawiesza przebieg, bo
pomocnik trzyma plik 120 s, a `zajmij_dziennik` czeka bez końca. Odmowa natychmiastowa
nie jest więc wygodą — bez `LOCK_NB` drugi przebieg nie odmawia, tylko stoi.

## 6a. Druga kontrola, która wyszła ZIELONA — i twierdzenie, które się przez nią zmieniło

**KN-6** przeniosła wzięcie zamka za `read_journal`. Wynik: **126/126**, zielono.

Komentarz, który tam napisałem, mówił: *„zamek PRZED pierwszym czytaniem dziennika;
później byłoby za późno — między odczytem a dopisem zmieściłby się cały drugi
przebieg"*. **To była nieprawda**, i kontrola ją obaliła, zamiast tylko pokazać brak
testu. `read_journal` niczego nie zapisuje, więc odczyt przed zamkiem nic nie kosztuje:
gdy dwa przebiegi czytają pusty dziennik naraz, zamek i tak przepuszcza jeden,
a drugiemu odmawia, zanim którykolwiek dopisze wiersz.

Granicą, która ma znaczenie, jest **pierwszy ZAPIS**, czyli wywołanie `sweep`. Zamek
wzięty po nim zostawia okno, w którym oba przebiegi mają już wpisy w jednym pliku —
usterkę z 6.D106. Komentarz jest więc przepisany na prawdziwy, a nowy test
`test_zamek_stoi_przed_pierwszym_ZAPISEM_do_dziennika` przybija tę kolejność czytaniem
AST funkcji `main`. **KN-6b** (zamek przeniesiony za `sweep`) daje **125/126**.

Różnica wobec poprzedniej zielonej kontroli tej sesji jest tu warta nazwania: KN-4
w 6.D122 pokazała asercję, która nie mierzyła tego, co deklarowała. KN-6 pokazała
**zdanie, które było fałszywe** — i gdyby nie została wykonana, zostałoby w drzewie
jako uzasadnienie kolejności, której nikt nie umiałby obronić.

## 7. Czego nie zrobiłem

* **Nie ruszyłem zbioru mutacji ani sposobu liczenia wyników** — oba wprost w polu
  „Poza zakresem".
* **Nie zdjąłem `PROCES_ZNACZNIK`**: nadal nazywa plik POŚREDNI mapy pokrycia
  (`<cel>.czesciowy-<znacznik>`) i nadal wchodzi do nazwy dziennika tam, gdzie zamku
  nie ma.
* **Nie zrobiłem zamka blokującego z czasem oczekiwania.** Odmowa natychmiastowa jest
  tym, czego żąda pole „Skończone, gdy" („dwa równoległe przebiegi nie mieszają
  wyników"); czekanie zamieniłoby dwa przebiegi w jeden dłuższy, a przegląd mutacyjny
  trwa kilkadziesiąt minut.
* **Nie tknąłem trzech odmów z 6.B19, 6.B32 i 6.D106** (kod 2) — zamek jest przed
  nimi i ich nie zastępuje: one pilnują TREŚCI dziennika, on — kto go teraz pisze.

## 8. Zauważone przy okazji — w tym sprostowanie do 6.D122

**Sprostowanie.** Raport 6.D122 §9 i wiersz 6.D122 w `docs/TASKS.md` mówią, że
`SUITE_RUNTIME_BUDGET_S`, czyli próg 150,0 s, ma dziś margines 1,3 s i że „najbliższy dopisany moduł
przewróci zapadkę". To jest prawda o **tym kontenerze** (dziś 150,842 s przy progu
150,0, czyli już po progu), ale czyta się jak zdanie o bramce CI — a bramka mierzy
**runnera**, gdzie ostatni przebieg dał:

```
czas sciany test_all.py: 78.465 s (prog 150.0 s)
czas CPU zestawu: 146.568 s
```

Runner liczy zestaw równolegle (stosunek CPU/ściana **1,868**), więc margines po jego
stronie wynosi 71,5 s, a nie 1,3 s. Zdanie z 6.D122 nie jest fałszem, ale mówi o innej
maszynie niż ta, o której czytelnik pomyśli. Progu nie ruszam — nie jest przekroczony
tam, gdzie jest sprawdzany.

Co jest w tym naprawdę nieaktualne: `MEASURED_MAX_WALL_S` wynosi **107,331 s** i pochodzi
z 07.09.2026, z przebiegu o **95** modułach. Dziś modułów jest 121. `MARGIN` liczony jest
więc wobec pomiaru, którego nikt już nie powtórzy — i to jest zapadka mierząca wczoraj,
a nie dziś. Nie tknąłem, bo to nie jest zadanie tej pozycji.

**Druga rzecz, i też dotyczy zdania, które sam wczoraj napisałem.** `docs/06-worked-example.md`
mówi, że w CI pułapki bajtkodu nie ma, bo „`actions/checkout` robi `git clean -ffdx`,
więc każdy przebieg CI zaczyna zimno". Log ostatniego przebiegu pokazuje:

```
[BAJTKOD] wyczyszczono 7 kat. __pycache__ (199 plikow) pod tools/ — 6.D122
```

Czyli **199 plików bajtkodu leżało tam, zanim zestaw wystartował**. Nie przeczy to
wnioskowi (ten bajtkod powstał w TYM SAMYM jobie, w krokach, które wcześniej importują
`test_suite_runtime_budget`, więc jest świeży i pułapki nie robi), ale przeczy zdaniu
„zaczyna zimno" wziętemu dosłownie. Zostawiam do osobnej pozycji: poprawianie
`docs/06-worked-example.md` przy zadaniu o zamku na dzienniku byłoby ruszaniem pliku
spoza zakresu (§4.10).
