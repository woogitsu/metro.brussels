# 6.D144 — ile kosztuje dopisanie komunikatów w jednym module

**11.09.2026**, na `8608c7c`. Wejście: `tools/tests/test_clearance_profile.py`,
`tools/tests/test_assertion_gate.py`. Pozycja żądała liczby: 117 asercji bez
komunikatu w jednym module ma zejść do zera, a raport ma podać koszt na jedną
asercję, żeby dało się oszacować pozostałe.

## 1. Zrobione

**117 → 0.** Wpis modułu wypadł z `NIEME_ASERCJE`, a zapadka zbiorcza zeszła
z 2372 na **2255**. Żadna asercja nie zmieniła warunku — modul daje 88/88 przed
zmianą i 88/88 po niej.

## 2. Koszt, cztery liczby

| miara | wartość |
|---|---:|
| asercji | **117** |
| wierszy dopisanych / zdjętych | **314 / 117** |
| wierszy napisanych na asercję | **2,68** |
| przyrost netto na asercję | **1,68** |
| plik | 1931 → **2128** wierszy (+10,2 %) |
| czas ściany (ten agent, od bazy do zera) | **251 s**, czyli **2,15 s** na asercję |

Czas jest podany, bo pole „Wyjście" go wymieniało, ale **nie jest przenośny**: mierzy
tego agenta, nie człowieka, i nie mówi o pozycji nic, czego nie mówią wiersze. Liczbą,
na której warto oprzeć decyzję, jest sekcja 3.

## 3. Co naprawdę kosztuje — i dlatego ten moduł jest ŁATWIEJSZY od średniej

Komunikat ma podawać POWÓD, nie warunek. Pisze się go więc z tego, co o teście
wiadomo — a to zależy od tego, czy funkcja ma docstring.

| | asercji | udział |
|---|---:|---:|
| w funkcjach **z docstringiem** (powód trzeba destylować) | **80** | 68,4 % |
| w funkcjach **bez docstringu** (powód trzeba odtworzyć z kodu) | **37** | 31,6 % |

To samo na całym `tools/tests/`, dla **2255** asercji, które zostały:

| | asercji | udział |
|---|---:|---:|
| w funkcjach z docstringiem | **1341** | 59,5 % |
| w funkcjach bez docstringu | **914** | 40,5 % |

**`test_clearance_profile.py` nie jest reprezentatywny i to jest wynik, nie
zastrzeżenie.** Pozycja wybrała go, bo ma asercji NAJWIĘCEJ — ale ma też
proporcjonalnie więcej funkcji opisanych (68 % wobec 60 %). Ekstrapolacja wprost
z tego modułu **zaniża** koszt pozostałych: 40,5 % reszty to asercje, przy których
nie ma z czego destylować.

Rząd wielkości, przy zastrzeżeniu wyżej: 2255 × 1,68 ≈ **+3 800 wierszy netto**
w 122 modułach, przy 314 wierszach napisanych na 117 asercji tutaj.

## 4. Kontrola KN-2 wyszła ZIELONA i znalazła dziurę w samym przyrządzie

To jest drugi wynik pozycji i ważniejszy od liczb.

Licznik pytał wyłącznie o `msg is None`. Zmierzone: `assert x, ""` przechodził jako
asercja **z powodem** — cały zestaw 122 moduły na zielono. Moduł dałoby się zbić
ze 117 na zero samym dopisaniem przecinka i pary cudzysłowów, a bramka zameldowałaby
sprawdzenie, którego nie zrobiła. Rodzina 6.D27, tym razem **w przyrządzie, na którym
stoi cała ta pozycja**: zdanie „wpis spadł do zera" byłoby wtedy warte tyle, co nic.

Dziura zamknięta: `komunikat_nic_nie_mowi` uznaje za brak powodu komunikat pusty,
biały, `None`, `0`, `False` i pusty f-string. **Ani jedna liczba się przez to nie
ruszyła** — zmierzone na całym `tools/tests/`: takich asercji było **zero**. Bramka
pilnuje więc czegoś, czego dziś nikt nie robi, i o to chodzi.

**Czego nie łapie i nie może:** komunikatu, który powtarza warunek zamiast podawać
powód (`assert a == b, "a != b"`). Rozróżnienie wymaga semantyki, nie kształtu.
Granica jest wypisana w kodzie, żeby zielona bramka nie czytała się jako „każdy
komunikat coś mówi".

## 5. Po co to było — ten sam błąd przed i po

Mutacja `cluster_gap_m` w `tools/blender/clearance_profile.py` (zwrot 25,0 dla kroku
2 m). Ten sam mutant, ten sam test, dwa odczyty:

przed pozycją:

```
  FAIL test_clearance_profile_cluster_gap_follows_the_scan_step: 
```

po:

```
  FAIL test_clearance_profile_cluster_gap_follows_the_scan_step: przy kroku 2 m odstęp
  ma zejść do 10 m; wpisana z powrotem stała 25,0 padnie właśnie tutaj
```

Pierwszy odczyt kończy się dwukropkiem i niczym. Drugi mówi, co jest nie tak i gdzie
szukać. To jest cała treść tej pozycji i powód, dla którego liczby z sekcji 2 są warte
zapłacenia.

## 6. Kontrole negatywne

Baza: **122/122** na parze modułów, **88/88** na samym module geometrycznym.
Po każdej `cp` z kopii i `md5sum -c: OK`.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | jedna asercja z powrotem bez komunikatu | **121/122** | zapadka bije po zejściu wpisu z listy, a nie tylko przy wzroście |
| KN-2 | komunikat pusty: `assert x, ""` | **122/122 ZIELONA** | **dziura w przyrządzie — patrz sekcja 4** |
| KN-2b | to samo po zamknięciu dziury | **121/122** | dziura zamknięta |
| KN-3 | zapadka zbiorcza zostawiona na 2372 | **121/122** | suma nie jest ozdobą i zapala się przy rozjeździe |
| KN-4 | mutacja `cluster_gap_m` w module pod testem | **87/88** | komunikat jest OSIĄGALNY i mówi to, po co go dopisano — sekcja 5 |

KN-2 jest tu wynikiem, nie formalnością: zielona kontrola zmieniła zakres pozycji
o cały punkt 4.

## 7. Czego nie zrobiono

- **Nie zmieniono treści ani jednej asercji.** Pole „Poza zakresem" mówi wprost:
  dopisuje się POWÓD, a nie warunek. 88/88 przed i po jest na to dowodem.
- **Nie tknięto pozostałych 2255 asercji.** Pozycja miała zmierzyć koszt, a nie
  zapłacić go w całości.
- **Nie dopisano docstringów do 16 funkcji, które ich nie mają.** Byłoby to drugą
  zmianą w jednym zadaniu, a przy okazji zatarłoby pomiar z sekcji 3: to właśnie ich
  brak jest tam mierzony.
- **Nie napisano bramki na komunikat powtarzający warunek** — patrz granica
  w sekcji 4.
