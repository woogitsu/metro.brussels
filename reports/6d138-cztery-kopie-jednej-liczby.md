# 6.D138 — cztery kopie liczby 170 000, i każda pilnuje czego innego

**11.09.2026**, na `540ee3c`. Pozycja: `assert R.MASS["AW0"] == 170000.0` porównuje
kopię z kopią i przeszłaby, gdyby rejestr podał co innego. Rozstrzygnąć, gdzie należy
odczyt, a gdzie literał.

## 1. Kopii jest cztery, nie trzy

| # | gdzie | czym jest |
|---|---|---|
| 1 | `data/vehicle/m7-spec.json` | **źródło**, z `source_id` i `approximate: true` |
| 2 | `tools/physics/reference.py` | **druga droga** — literał jest treścią tablicy |
| 3 | `test_all.py`, pin masy | **pin na kopii 2** |
| 4 | `test_m7_spec_registry_provenance` | **pin na kopii 1** |

Wpis pozycji wymieniał trzy; czwartą — pin na samym źródle — widać dopiero wtedy, gdy
się rejestr podmieni.

## 2. Pomiar: co się zapala na czym

Na kopii roboczej drzewa, bez zmiany `data/` (`CLAUDE.md` §4.6 — kontrola negatywna nie
jest od tego wyjątkiem). Całe drzewo, 2346 testów:

```
podmiana w REJESTRZE    (170000 → 171000)   4 testy;  pin z test_all.py MILCZY
podmiana w REFERENCJI   (170000 → 171000)   6 testów; pin z test_all.py JEST wśród nich
```

Na dwóch modułach, których dotyczy pole „Weryfikacja" (`test_all.py test_braking.py`),
zbiory są mniejsze i **dokładnie znane** — i to one stoją dziś w kodzie jako pin:

| zmiana | testy, które padają |
|---|---|
| rejestr | `test_ile_parametrow_modelu_jest_PRZYBLIZONYCH`, `test_m7_spec_registry_provenance`, `test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM`, `test_wypis_modelu_NAZYWA_parametry_przyblizone` |
| referencja | `test_m7_reference_mass_pin_has_not_drifted`, `test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM` |

**Część wspólna to dokładnie jeden test** — ten, który porównuje kopię ze **źródłem**
(6.D124). To jest cały podział pracy, wypisany liczbą zamiast prozą.

## 3. Rozstrzygnięcie

**Literał zostaje** — i to nie z wygody. Gdyby `reference.py` czytało rejestr,
zniknęłaby druga droga, na której stoi porównanie C# z Pythonem; KN-2 to mierzy:
po takiej zmianie pin zaczyna zapalać się na zmianach **rejestru**, czyli przestaje
być niezależnym świadkiem.

**Zmienia się nazwa i komunikat.** Dawne imię brzmiało
`test_m7_reference_uses_source_backed_aw0` i obiecywało sprawdzenie oparcia o źródło,
którego ta asercja nie robi — 6.D27 w miniaturze. Dziś:
`test_m7_reference_mass_pin_has_not_drifted`, z komunikatem mówiącym wprost, czego
ten pin **nie** sprawdza i kto to sprawdza zamiast niego.

Przy okazji dwie asercje dostały komunikaty, których nie miały:
`test_m7_spec_registry_provenance` padał jako `FAIL …:` — dwukropek i nic dalej, mimo
że zmieniona wartość w rejestrze była dokładnie tym, co się zmieniło. `NIEME_ASERCJE`
dla `test_all.py` spada z **72 na 68**, suma z 2376 na 2372.

## 4. Pułapka, w którą wpadłem

Pierwsza wersja tych testów stała w `test_braking.py` — czyli w module, który same
uruchamiają w drzewie probnym. Przebieg **nie skończył się w 300 s** i został ubity:
kopia zawierała test budujący kolejną kopię, bez końca. Ta sama pułapka co przy 6.D122
i 6.D114. Stąd osobny moduł `test_mass_copies.py` i zdanie w jego docstringu:
**drzewo probne nie może zawierać testu, który je buduje.**

Nowy moduł podniósł przy okazji liczbę plików bajtkodu z 201 na 202 — i **bramka
z 6.D136 zapaliła się na tej jedynce sama**, w pierwszym przebiegu po dopisaniu pliku.
Liczba w niej i w `docs/06-worked-example.md` jest przeliczona.

## 5. Kontrole negatywne

Baza `test_mass_copies.py`: **3/3**, moduł nowy. `__pycache__` czyszczony przed każdym
przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na czterech plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | pin masy w `test_all.py` zdjęty | **2/3** |
| KN-2 | `reference.py` czyta rejestr zamiast literału | **0/3**, trzy testy |
| KN-3 | pin na źródle zdjęty | **2/3** |
| KN-4 | porównanie ze źródłem (6.D124) zdjęte | **1/3**, dwa testy |
| KN-5 | drzewo probne bez `docs/` i `reports/` | **3/3 ZIELONA** |
| KN-5b | to samo po zamianie zawierania na RÓWNOŚĆ | **1/3**, dwa testy |

**KN-2 jest najmocniejsza**: pokazuje, że dzisiejsze milczenie pinu na zmianie rejestru
**bierze się z niezależności drugiej drogi**, a nie z niedopatrzenia. Po podłączeniu
`reference.py` do rejestru pin zaczyna reagować na rejestr — i to jest dokładnie ta
utrata, przed którą pole „Dlaczego" tej pozycji ostrzegało.

**KN-5 wyszła zielona i zmieniła kształt testu.** Testy pytały „czy nazwa X jest
w zbiorze", więc dorzucenie czterech testów padających na brakujących plikach niczego
nie ruszało. Dziś porównanie jest **równością** — pilnuje CAŁEGO zbioru, czyli tego,
o co pozycja pytała — a KN-5b jest czerwona i wypisuje te cztery nazwy.

## 6. Weryfikacja

```
  3/3 przeszło          test_mass_copies.py   (moduł nowy, 123. w zestawie)
  2349/2349 przeszło, 123 moduły, KOD=0, RAZEM 173.899 s
```

## 7. Czego nie zrobiłem

* **Nie zmieniłem wartości w `data/` ani tablicy referencyjnej** — oba wprost
  w „Poza zakresem". Wszystkie pomiary szły na kopii; `git status data/` pusty.
* **Nie objąłem pomiarem całego zestawu w teście.** Zbiory 4 i 6 zmierzyłem ręcznie
  na pełnym drzewie, ale test chodzi na dwóch modułach: dwa przebiegi całego zestawu
  to 340 s wobec 2,1 s, a pytanie „KTÓRY test się zapala" obie drogi rozstrzygają
  tak samo.
* **Nie tknąłem trzeciej kopii liczby 221 940** (AW2). Ta sama rodzina, ale masa
  obciążona ma status `design_model` i nie ma flagi przybliżenia, więc jej role
  rozkładają się inaczej — to osobny pomiar.
