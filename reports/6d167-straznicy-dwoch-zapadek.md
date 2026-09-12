# 6.D167 — dwie zapadki stały równo na drzewie i nie broniły się przed cofnięciem

**12.09.2026**, na `65299fc`. Wejście: `tools/tests/test_bin_path_framework.py`,
`tools/tests/test_tree_walks.py`, historia `reports/` i `docs/`. Pozycja z audytu
repozytorium z 12.09.2026, wpisana do kolejki przy 6.D166.

## 1. Co było nie tak

`MIN_PATHS_IN_TREE = 29` i `MIN_FILES_WITH_PATHS = 8` miały po jednej asercji
**nośnej** — takiej, która pada, gdy kurczy się drzewo:

```python
assert len(hits) >= MIN_PATHS_IN_TREE
assert len(files) >= MIN_FILES_WITH_PATHS
```

Nie miały ani jednej **strzegącej**, czyli takiej, która pada, gdy ktoś obniży samą
stałą. Rejestr `test_tree_walks.py` klasyfikował je z tego powodu jako **WOLNE**,
i był to pomiar, nie przypuszczenie: `klasa_zapadki` zwraca `WOLNA`, gdy wśród
porównań nie ma ani jednego o relacji strzegącej.

Obie stały przy tym **dokładnie na stanie drzewa**: 29 i 8. Połączenie jest gorsze
niż każda z tych rzeczy osobno — pierwsze skasowanie ścieżki `bin/…/netX.Y/`
z `reports/` albo `docs/` zapala bramkę, a najbliższą pod ręką „naprawą" jest
obniżenie stałej. Po tej naprawie nie zapala się nic i nikt się nie dowiaduje.

To ta sama rodzina, którą 6.D45 zmierzyło na `MIN_REPORTS`, tylko w drugą stronę:
tam zapadka stała sto pozycji za drzewem i nie mierzyła niczego, tu stoi równo
i nie broni się przed cofnięciem.

## 2. Rozstrzygnięcie: przybicie równością, bo koszt zmierzony wyszedł zerowy

Wybór między „przybić równością" a „odsunąć próg od stanu" nie był kwestią gustu.
Populacja pilnowana przez obie zapadki — ścieżki `bin/…/netX.Y/` w `reports/`
i `docs/` — była liczona na historii tych katalogów:

```
rewizji dotykajacych reports/ lub docs/ (ostatnie 120): 120
przejsc, w ktorych para (sciezek, plikow) sie zmienila: 0 z 59
roznych wartosci: 1
```

**Zero zmian na 59 przejściach.** Przybicie kosztuje więc tyle, co nic: nie będzie
zapalać się na poprawnej pracy, więc nie zostanie wyłączone.

Ten sam pomiar, ta sama metoda i **przeciwne zalecenie** niż osiem godzin wcześniej
przy 6.D153: tam para (literały, różne) zmieniała się w **29 przejściach na 39**,
więc przybita została nie liczba, tylko zbiór. Metodę warto było powtórzyć zamiast
przenosić wniosek — i to jest cała treść tego akapitu.

## 3. Kształt wyrażenia jest treścią, nie stylem

`klasa_zapadki` uznaje strażnika za przybijającego dopiero wtedy, gdy mierzy **tę
samą populację** co próg — porównuje `ast.dump` obu stron. Strażnik napisany jako
`MIN_PATHS_IN_TREE >= 0` byłby obecny i nic by nie dawał: klasa spada wtedy do
`czesciowa`, bo ruch o jeden nadal przechodzi. Dlatego `len(hits)` i `len(files)`
stoją w strażniku znak w znak tak, jak w asercji nośnej. Zmierzone kontrolą KN-3,
nie wywnioskowane.

## 4. Bramka z 6.D166 zadziałała pierwszy raz naprawdę

Przejście obu zapadek do klasy `przybita` zmienia rozkład **15 / 3 / 23 / 1** na
**17 / 3 / 21 / 1**, a ten rozkład stoi w prozie `test_tree_walks.py`. Zdanie zostało
zapalone przez bramkę dołożoną dzień wcześniej — bez niej przeszłoby nietknięte:

```
FAIL test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem: proza: 15 przybitych, rejestr: 17
```

Jest to jej **pierwsze zadziałanie na prawdziwej zmianie**, a nie w kontroli
negatywnej — czyli dokładnie ten rodzaj potwierdzenia, którego 6.D166 nie mogło
sobie wystawić samo.

## 5. Kontrole negatywne

Baza `test_bin_path_framework.py` + `test_tree_walks.py`: **29/29**. Po każdej
`md5sum -c` na obu plikach: `OK`.

| kontrola | co zmienia | skutek |
|---|---|---|
| KN-1 | `MIN_PATHS_IN_TREE` 29 → 28 (ruch w ZAKAZANĄ stronę) | **28/29** — `= 28 stoi PONIŻEJ drzewa (29 ścieżek) — zapadkę obniżono zamiast przeliczyć` |
| KN-2 | `MIN_FILES_WITH_PATHS` 8 → 7 | **28/29** — `= 7 stoi PONIŻEJ drzewa (8 plików)` |
| KN-3 | strażnik zostaje, ale mierzy INNĄ populację (`len(hits)` → `0`) | **28/29** — `zapadka zmieniła klasę: [('MIN_PATHS_IN_TREE', 'przybita', 'czesciowa')]` |

**KN-3 jest tą kontrolą, dla której ta pozycja w ogóle ma sens.** KN-1 i KN-2
pokazują, że strażnik działa; dopiero KN-3 pokazuje, że działa **z powodu, dla
którego został tak napisany** — obecność asercji nie wystarcza, populacja musi się
zgadzać. Bez niej „dodałem strażnika" byłoby zdaniem o kodzie, a nie o jego skutku.

## 6. Czego nie zrobiłem

- **Nie ruszyłem pozostałych 21 zapadek klasy WOLNA.** Audyt wymienia je co do
  nazwy, ale żadna z nich nie stoi dziś równo na drzewie — a to połączenie, nie sama
  klasa, robi z zapadki pułapkę. Zapadka wolna z zapasem jest ryzykiem; wolna
  i przybita do stanu jest ryzykiem, które zadziała przy najbliższej zmianie.
- **Nie zmieniłem wartości żadnej z dwóch stałych.** Pozycja daje im strażnika,
  a nie nowy próg: 29 i 8 są nadal tym, co mierzy drzewo.
