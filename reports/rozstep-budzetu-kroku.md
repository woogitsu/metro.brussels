# 6.D41 — bramka porównywała z progiem pomiar, który sama nazwała niestabilnym

**Zmierzone 07.09.2026 na commicie:** `e6b4dc182ede0db9b342c3e871ffd526b9af7c6f`

## 1. Objaw

Job `sim` padł na PR #395, na runnerze `woogitsu-host-08`, gdy dwanaście jobów liczyło
naraz (CI ośmiu pull requestów odpalone przeze mnie w jednej chwili):

```
BLAD: koszt kroku 16.022 us przekracza prog 8.000 us
[BUDZET-BRAMKA] zgloszonych 32, na planie 9 (srednio 5.08, czeka 0.98);
                16.022 us/krok przy progu 8.000; 0.190 % budzetu klatki;
                rozstep powtorzen 115.9 %
```

Diff tej gałęzi to pliki workflow, listy pakietów apt i jeden moduł testowy — **ani
jednego pliku C#**. Komunikat mówił jednak o regresie wydajności rdzenia.

## 2. Ten sam kod na maszynie niezajętej

Cztery przebiegi, ta sama treść kodu, `dotnet build --configuration Release`:

```
  p0: 4.280 us/krok przy progu 8.000; 0.050 % budzetu klatki; rozstep powtorzen 3.7 %
  p1: 4.268 us/krok przy progu 8.000; 0.050 % budzetu klatki; rozstep powtorzen 2.9 %
  p2: 4.213 us/krok przy progu 8.000; 0.050 % budzetu klatki; rozstep powtorzen 1.9 %
  p3: 4.364 us/krok przy progu 8.000; 0.050 % budzetu klatki; rozstep powtorzen 3.5 %
```

**4,213–4,364 µs przy rozstępie 1,9–3,7 %, kod 0.** Rdzeń nie zwolnił czterokrotnie —
maszyna nie dała się zmierzyć.

## 3. Co dokładnie było nie tak

Kolumna `rozstęp_%` była **parsowana i wypisywana, ale nigdy nie asertowana**:
`spread_pct` czytany w `parse`, użyty wyłącznie w `describe`. Bramka znała liczbę
mówiącą, że jej własny pomiar jest niestabilny, i **porównywała go z progiem mimo to**.

Skutek jest gorszy niż czerwona bramka. Dwa różne stany świata:

| stan | co znaczy | co należy zrobić |
|---|---|---|
| rdzeń zwolnił | regres wydajności w kodzie | szukać regresu, czytać diff |
| nie umiem zmierzyć | maszyna obciążona | powtórzyć pomiar |

…dawały **jeden komunikat i jeden kod wyjścia**. Pierwszy z nich każe szukać w kodzie
regresu, którego nie ma — czyli bramka nie tylko myliła się, ale myliła się w kierunku
kosztownym dla czytającego.

## 4. Granica jest wyprowadzona z czterech pomiarów, nie zgadnięta

To była najtrudniejsza część, bo granica za ciasna zamienia bramkę w generator
fałszywych alarmów (6.D27: bramka zapalająca się na tekście poprawnym zostaje wyłączona),
a za luźna nie robi nic.

| rozstęp | skąd | rola |
|---|---|---|
| **1,9–3,7 %** | cztery przebiegi 07.09.2026, maszyna niezajęta | dolna obserwacja |
| **17,0 %** | atrapa `ZIELONY` w `tools/tests/test_linecore_budget_gate.py` | ogranicza od dołu |
| **22,5 %** | kalibracja progu 8,0 µs, `reports/linecore-step-budget-gate.md`, 06.09.2026 | ogranicza od dołu |
| **115,9 %** | `woogitsu-host-08`, dwanaście jobów naraz | jedyna obserwacja niemierzalna |

**50 %** leży 2,2× powyżej najwyższego udokumentowanego pomiaru **zielonego** i 2,3×
poniżej zaobserwowanego **niemierzalnego** — czyli poza szumem w obie strony. Wartość
jest **tymczasowa** i ma być **zaciśnięta**, gdy uzbiera się więcej rozstępów z samych
runnerów; rozluźnienie wymagałoby pomiaru pokazującego zielony przebieg powyżej 50 %.

> **Adnotacja z 08.09.2026 — ten akapit został wykonany na opak i to jest tu zapisane,
> nie przemilczane.** Granica została **rozluźniona** do 100 %, decyzją właściciela
> podjętą przeciwko rekomendacji sesji (`reports/linecore-step-budget-gate.md` §9).
> Pomiar zostaje nieprzeliczony, zmienia się reguła — i **warunek postawiony w zdaniu
> powyżej NIE został spełniony**: najwyższy zmierzony rozstęp przebiegu **zielonego** to
> **47,5 %** (3,810 µs, kod 0, kontener 08.09.2026), czyli **2,5 pp za mało**.
> Rozluźnienie stoi więc na decyzji właściciela, a nie na tym warunku. Argument, który
> tę decyzję popiera pomiarowo, jest inny i też był wtedy nieznany: przy granicy 50 %
> ten sam przebieg zielony przy 47,5 % stał **2,5 pp** od orzeczenia o nim
> niemierzalności, a bramka zapalająca się na przebiegu poprawnym zostaje wyłączona
> (6.D27).

**Progu 8,0 µs nie tknięto.** Ma udokumentowaną podstawę i podniesienie go byłoby
osłabieniem bramki, a nie naprawą pomiaru.

## 5. Warunki obsady zostają sprawdzane zawsze

Strażnik wstrzymuje **wyłącznie** porównania czasu. Liczba składów na planie nie zależy
od obciążenia maszyny, więc pomiar niestabilny **z błędną obsadą** jest nadal usterką
scenariusza i wychodzi kodem 1, nie kodem niemierzalności. Bez tego rozdziału
„nie umiem zmierzyć" przesłoniłoby zarzut, który od maszyny nie zależy wcale — a to
jest dokładnie ta sama usterka, tylko odwrócona.

## 6. Cztery kontrole negatywne — WYKONANE

**KN-1: strażnik zdjęty** (stan sprzed poprawki):
```
FAIL ...MIESZCZACY_SIE_w_progu_tez_jest_odmowa: pomiar z rozstepem 115,9 % przeszedl,
     bo czas byl w progu
FAIL ...NIE_JEST_porownywany_z_progiem: ['koszt kroku 16.022 us przekracza prog 8.000 us']
  15/17 przeszło
```

**KN-2: granica zaniżona do 10 %** — pięć FAIL, w tym **na atrapie zielonej**:
```
FAIL test_a_green_measurement_passes: ['rozstep powtorzen 17.0 % przekracza granice 10.0 %...']
FAIL test_granica_rozstepu_jest_POWYZEJ...: granica 10.0 % odrzucalaby wlasna atrape zielona (17.0 %)
FAIL test_wolny_krok_przy_ZNOSNYM_rozstepie_nadal_jest_odmowa
```
To najważniejsza z czterech: pokazuje, że za ciasna granica **odrzuca prawdziwe
odmowy o czasie** razem z pomiarami zielonymi.

**KN-3: granica podniesiona do 200 %** — cztery FAIL, w tym asercja wyprowadzona:
```
FAIL test_granica_rozstepu_jest_POWYZEJ...: granica 200.0 % przepuszczalaby
     zaobserwowany pomiar niemierzalny (115,9 %), czyli nie robilaby nic
```

**KN-4: kod niemierzalności zrównany z kodem przekroczenia**:
```
FAIL test_dwa_werdykty_maja_DWA_ROZNE_kody_wyjscia: oba werdykty wychodza tym samym
     kodem, wiec rozroznienia nie ma
  16/17 przeszło
```

## 7. Dziura w mojej WŁASNEJ procedurze kontroli, znaleziona przy okazji

Po KN-4 przywróciłem plik przez `cp` i sprawdziłem stan — moduł pokazał **16/17**, choć
źródło miało poprawną wartość. Przyrząd czytał `KOD_NIEMIERZALNY = 1`, gdy w pliku
stało `3`.

Przyczyna: mutacja KN-4 zmieniała `= 3` na `= 1`, czyli miała **identyczną długość
pliku**, a przywrócenie trafiło w to samo okno rozdzielczości mtime. Python uznał
zapamiętany bajtkod za świeży i użył **starego** `.pyc`.

Znaczenie jest szersze niż ta pozycja: **każda kontrola negatywna mutująca plik `.py`
o stałej długości i przywracana przez `cp` może po przywróceniu weryfikować STARY
bajtkod.** Złapałem to tylko dlatego, że sprawdzam stan po przywróceniu, a nie ufam
samemu `cp`. Od teraz kontrole czyszczą `__pycache__` przed weryfikacją stanu.

To nie jest hipoteza — po `find tools -name __pycache__ -exec rm -rf` moduł wrócił do
`17/17` bez ani jednej zmiany w źródłach.

## 8. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1963/1963 przeszło
  RAZEM 82.052 s, 1963 testów, 103 modułów
kod: 0

$ python3 tools/ci/assert_linecore_budget.py
[BUDZET-BRAMKA] ... 4.393 us/krok przy progu 8.000; 0.050 % budzetu klatki;
                rozstep powtorzen 4.0 %
kod: 0
```

Moduł bramki 11 → 17 testów.

## 9. Czego świadomie NIE zrobiłem

- **Nie ruszyłem progu 8,0 µs.** Osłabienie bramki nie jest naprawą pomiaru.
- **Nie dodałem automatycznego powtarzania pomiaru** przy niestabilnym wyniku. Brzmi
  oczywiście, ale wymagałoby pomiaru, **jak często powtórzenie pomaga** — a bez tego
  byłoby to maskowanie obciążenia, nie jego wykrywanie. Osobna pozycja.
- **Nie zmieniłem `repeats: 9`** w scenariuszu. Więcej powtórzeń zmniejszyłoby rozstęp,
  ale zmieniłoby też pomiar, do którego przybity jest próg 8,0 µs.
- **Nie tknąłem `runs-on`** ani liczby jednocześnie odpalanego CI — choć to ja odpaliłem
  osiem pull requestów naraz i prawdopodobnie sam wywołałem ten rozstęp.

## 10. Zauważone przy okazji, nietknięte

Trzy razy dzisiaj CI padło z przyczyn, które nie były w kodzie: dwa razy
`The runner has received a shutdown signal` w trakcie pracy, raz utrata katalogu
`_actions` na jednej maszynie. Do tego doszedł ten rozstęp 115,9 % przy dwunastu jobach.
Wspólny mianownik — obciążenie wspólnego sprzętu — jest **hipotezą**, nie pomiarem:
nie mierzyłem ani pamięci, ani liczby równoległych renderów Blendera. Pomiar, który by
to rozstrzygnął, wymaga dostępu do maszyn i jest osobną pozycją.
