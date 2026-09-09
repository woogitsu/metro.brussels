# Trzy kryteria T-112 przyłożone do wyjścia, i jedno z nich mówi o polu, którego nie ma

**Zmierzone 09.09.2026 na:** `c9db1e0`, kontener tej sesji, Blender 5.2.1
i .NET 10.0.401 doinstalowane tego dnia.
**Przyrząd:** `tools/track/vertical_profile.py` na `data/track/L1_A.json`
i `data/network/station-depths.csv`, wyjście `build/L1_A-vertical.json`,
`docs/TASKS.md` (wpis T-112), `docs/21-measured-vs-assumed.md`.

---

## 1. Skąd ten raport

`doctor.sh` wskazuje T-112 jako następne zadanie, bo to jedyny wpis `### [ ]` bez
markera blokady i bez `[CZŁOWIEK]`. Właściciel polecił je wziąć. Pierwszą czynnością
nie było jednak budowanie czegokolwiek, tylko sprawdzenie, **co z tego wpisu jest
jeszcze niezrobione** — bo sam wpis mówi, że wykonuje go pozycja **6.B44**, a ta jest
w kolejce oznaczona jako `ZROBIONE (07.09.2026)`.

Robienie po raz drugi rzeczy, która leży w `main`, jest w tym projekcie nazwaną
usterką (`test_next_task.py` powstał dokładnie po takim przypadku z T-212).

## 2. Trzy kryteria wpisu, przyłożone do rzeczywistego wyjścia

Wpis T-112 mówi: „**Skończone, gdy:** pochylenia interpolowanego profilu są 0–4%,
a każda wygenerowana wartość ma `interpolated:true` i `design_assumption`, **a każdy
odcinek bez danych ma `confidence: unknown`** i nie ma wartości wcale".

Przebieg z dzisiaj:

```
[PROFIL]    3129.94 m  De Brouckère                           -12.0 m (estimated)
[PROFIL]    3731.85 m  Gare Centrale|Centraal Station         NIEWIADOMA
[PROFIL]    4075.66 m  Parc|Park                              -20.0 m (estimated)
[PROFIL]    4560.95 m  Arts-Loi|Kunst-Wet                     -12.0 m (estimated)
[PROFIL] profil ZDEFINIOWANY na: 485.29 m z 6686.35 m (7.26 %)
[PROFIL] osi bez rzędnej: 6217.97 m — zapisane jako depth_m=null, confidence=unknown
```

Pomiar na zapisanym pliku, 447 punktów:

```
punktów ze rzędną: 32, bez rzędnej: 415
pochyleń policzonych: 31, max 1.655 %                      <- kryterium 1
brakujące klucze w punktach ze rzędną: []                  <- kryterium 2 (część)
wartości confidence (ze rzędną):   {'estimated'}
wartości confidence (bez rzędnej): {'unknown'}             <- kryterium 3
czy któryś punkt bez rzędnej NIESIE wartość: []            <- kryterium 3
przykład: {'between': ['Parc|Park', 'Arts-Loi|Kunst-Wet'], 'chainage_m': 4092.564,
           'confidence': 'estimated', 'depth_m': -19.721, 'interpolated': True}
```

**Kryterium 1 — spełnione.** Największe pochylenie to 1,655 %, przy dopuszczalnych 0–4 %.

**Kryterium 3 — spełnione.** Każdy z 415 punktów bez rzędnej ma `depth_m: null`
i `confidence: "unknown"`, i ani jeden nie niesie wartości.

**Kryterium 2 — spełnione w połowie, a druga połowa mówi o polu, którego nie ma.**
`interpolated: true` jest przy każdej wygenerowanej wartości. Ale `design_assumption`
**nie należy do słownika tego pola**. `data/network/station-depths.csv` deklaruje go
we własnym nagłówku:

```
# confidence: measured | counted | estimated | unknown
```

`design_assumption` pochodzi z **innej** osi opisu — z `docs/21-measured-vs-assumed.md`,
gdzie znaczy „decyzja projektowa; **nie jest faktem o sieci**". Rzędna interpolowana
między dwiema stacjami o głębokości `estimated` nie jest decyzją projektową; jest
wnioskiem z dwóch oszacowań. Wpisanie jej `design_assumption` byłoby zmianą **na
gorsze**: zdjęłoby z niej ślad prowadzący do EIE Métro 3 i przedstawiło ją jako coś,
co ktoś wybrał, a nie policzył.

Implementacja z 6.B44 propaguje więc `estimated` i to jest odczyt zgodny ze słownikiem
pola. **Kryterium wpisu jest nieaktualne, a nie kod.**

## 3. Co z T-112 zostaje naprawdę

Zostaje wariant `production` — i on jest zablokowany nie brakiem pracy, tylko
**sprzecznością dwóch oficjalnych źródeł**, którą wpis nazywa wprost: Schuman 15 m
wobec 17,42 m, Botanique 21,5 m wobec 20 m. Wybór strony konfliktu należy do T-901,
czyli do właściciela, i decyzja z 07.09.2026 tego wyboru **nie podejmowała**.

Dlatego nagłówek wpisu dostaje marker blokady z nazwaną przyczyną. Skutek uboczny jest
tym, o co chodzi: `doctor.sh` przestaje wskazywać jako „następne zadanie" pozycję,
której wykonalna część leży w `main` od 07.09.2026, a niewykonalna czeka na człowieka.

## 3a. Marker odsłonił drugą usterkę, o wiele gorszą od pierwszej

Postawienie markera blokady na T-112 sprawiło, że `doctor.sh` po raz pierwszy wszedł
w gałąź kolejki — i **wskazał jako „następne zadanie" pozycję z adnotacją ZROBIONE**:

```
  Baza projektu jest gotowa. Rozpiska nie ma odblokowanego zadania z numerem,
  więc zgodnie z CLAUDE.md §8 bierzesz pierwszą pozycję z kolejki faz 5 i 6:
    5.6 · ZROBIONE (08.09.2026), i pozycja pomyliła się co do trzech rzeczy naraz — pomiar to pokazał.
```

Przyczyna jest zmierzona i jest to **druga kopia reguły**. Doctor miał własny wzorzec
`^\| [56]\.[0-9]+ \|`, niezależny od `open_items`:

```
wierszy łapanych przez wzorzec doctora: 8
z nich ZROBIONE: 1
open_items ogółem: 34
open_items pasujące do wzorca doctora: []
```

**Ani jedna** z 34 otwartych pozycji nie pasowała do wzorca, bo wszystkie mają w numerze
literę (`6.D67`, `6.B5`), a wzorzec dopuszczał wyłącznie cyfry. Osiem, które łapał, to
prace domknięte. Gałąź była nieosiągalna, dopóki w rozpisce stał niezablokowany wpis
`### [ ]` — czyli dokładnie sytuacja, którą komentarz w samym doctorze opisuje słowami
„nie była martwym kodem — była kodem, którego nikt nie widział, bo poprzedzał go stan
nieaktualny". Ten sam mechanizm, drugi raz, w tym samym pliku.

Doctor bierze teraz pierwszą pozycję z `test_backlog.open_items`, czyli z tego samego
czytnika, którym od 6.D50 liczy zapas. Po poprawce:

```
    6.D47 · Nie wiadomo, czy ponowne uruchomienie joba pull requesta po ruszeniu bazy sprawdza starą czy nową scalankę
  Kolejka faz 5 i 6 ma 34 pozycji do wzięcia, żadna nie wymaga decyzji właściciela.
```

**Bramka, która tego nie zauważyła, jest przekierowana i sprawdza teraz więcej.**
`test_doctor_points_at_the_queue_and_the_rule_is_not_retyped` porównywała wybór doctora
z pierwszym wierszem dopasowanym **swoją własną kopią** tego samego wzorca — czyli
kopię z kopią. Teraz porównuje z `open_items` i dodatkowo żąda, żeby wskazany wiersz
**nie nosił adnotacji ZROBIONE**. Trzecia bramka dopowiedziała resztę: po usunięciu
ostatniego czytelnika stałej `QUEUE_ROW` zapaliło się
`test_every_unread_constant_is_justified`, więc stała została **usunięta**, a nie
uzasadniona — była właśnie tą drugą kopią.

## 4. Weryfikacja

```
python3 tools/track/vertical_profile.py --axis data/track/L1_A.json \
    --depths data/network/station-depths.csv --out build/L1_A-vertical.json
  -> [PROFIL] zapisane: build/L1_A-vertical.json, kod 0

python3 tools/tests/test_all.py
  -> RAZEM 2087 testów, 111 modułów, kod 0

bash doctor.sh   (z DOTNET_ROOT i BLENDER_BIN)
  ok    2087/2087 przeszło
  ok    593/593 przeszło
  Baza projektu jest gotowa. … bierzesz pierwszą pozycję z kolejki faz 5 i 6:
    6.D47 · Nie wiadomo, czy ponowne uruchomienie joba pull requesta …
  Kolejka faz 5 i 6 ma 34 pozycji do wzięcia, żadna nie wymaga decyzji właściciela.
```

`build/` nie jest commitowane (`CLAUDE.md` §4.8) — plik powstaje przy każdym przebiegu.

## 5. Czego świadomie nie zrobiono

**Nie odhaczono T-112.** Trzy kryteria są spełnione, ale wpis niesie też wariant
`production`, a ten nie ma z czego powstać. Odhaczenie mówiłoby, że sprzeczność źródeł
została rozstrzygnięta — nie została.

**Nie wybrano strony konfliktu głębokości.** To jest T-901 i `CLAUDE.md` §4.1.

**Nie ruszono `tools/track/vertical_profile.py`.** Kod robi to, co trzeba; nieaktualne
było kryterium, nie zachowanie.

**Nie zmierzono profilu dla pakietów B–F.** Wpis T-112 dotyczy pakietu A.
