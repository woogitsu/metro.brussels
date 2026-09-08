# 6.B44 — profil pionowy z jawną niewiadomą, i reguła, która okazała się nie być hipotetyczna

**Zmierzone 07.09.2026 na commicie:** `e6b4dc182ede0db9b342c3e871ffd526b9af7c6f`

## 1. Co powstało

`tools/track/vertical_profile.py` — czyta oś pakietu i `data/network/station-depths.csv`,
pisze do `build/` profil, w którym **każdy** punkt osi niesie albo rzędną z interpolacji
między dwiema **znanymi** stacjami, albo `depth_m: null, confidence: "unknown"`.

Decyzja właściciela z 07.09.2026 brzmiała: **budować z jawnym `unknown`**, nie czekać na
uzupełnienie rejestru i nie zgadywać brakujących rzędnych. Dwanaście stacji pakietu A,
**trzy** z rzędną.

## 2. Reguła „interpolacja nie przechodzi przez niewiadomą" działa NA DZISIEJSZYCH DANYCH

Pierwsza wersja docstringu tego narzędzia napisała:

> Dziś w pakiecie A taki przypadek nie występuje (trzy znane leżą obok siebie
> w kilometrażu), ale wypełnienie jednej dziesiątej głębokości może go stworzyć.

**To była nieprawda i pomiar obalił ją w pierwszym przebiegu.** Trzy znane stacje NIE leżą
obok siebie:

```
    3129.94 m  De Brouckère                           -12.0
    3731.85 m  Gare Centrale|Centraal Station         NIEWIADOMA
    4075.66 m  Parc|Park                              -20.0
    4560.95 m  Arts-Loi|Kunst-Wet                     -12.0
```

**Gare Centrale leży między De Brouckère i Parc i rzędnej nie ma.** Para De Brouckère↔Parc
jest więc rozspojona, a wypełnić wolno wyłącznie Parc↔Arts-Loi:

| wariant | wypełnione |
|---|---|
| naiwna interpolacja od pierwszej do ostatniej znanej | **1431,01 m** |
| z regułą — tylko sąsiednie pary obie ze rzędną | **485,29 m** |

Różnica **945,72 m** to dokładnie tyle osi, ile naiwne narzędzie by **zmyśliło** —
twierdząc przy tym, że wie, na jakiej głębokości leży Gare Centrale.

Spodziewałem się pokrycia około 21 % i było to oszacowanie zrobione w głowie, przed
uruchomieniem. Wyszło **7,26 %**, i cała różnica siedzi w tej jednej stacji.

## 3. Pokrycie ma DWIE liczby, bo mierzą dwie różne rzeczy

```
[PROFIL] profil ZDEFINIOWANY na: 485.29 m z 6686.35 m (7.26 %)
[PROFIL] odcinków łamanej z rzędną na obu końcach: 468.38 m (7.01 %)
[PROFIL] osi bez rzędnej: 6217.97 m — zapisane jako depth_m=null, confidence=unknown
```

Rozdzielenie jest naprawą pomyłki, nie ozdobą. Sama pierwsza wersja podawała **7,01 %**,
co czyta się jako „profil pokrywa 7 % osi" — a to jest zdanie o **wierzchołkach łamanej**,
nie o profilu. Przyczyna różnicy 16,904 m jest jedna i zmierzona: łamana nie ma
wierzchołka na kilometrażu Parc (4075,66 m), najbliższy stoi na **4092,564 m**.

```
punktow ze rzedna: 32 z 447
pierwszy ze rzedna: 4092.564 m, ostatni: 4560.949 m
Parc na 4075.66; najblizszy punkt lamanej ze rzedna: 4092.564 (o 16.904 m dalej)
Arts-Loi na 4560.95; ostatni punkt ze rzedna: 4560.949 (o 0.001 m blizej)
```

## 4. Normalizacja nazw była martwym mechanizmem z NIEPRAWDZIWYM uzasadnieniem

Pierwsza wersja zdejmowała znaki diakrytyczne i wielkość liter, a docstring uzasadniał to
tak: „dopasowanie DOKŁADNE po `name_fr` daje 8 z 12, wśród zgubionych jest De Brouckère,
czyli jedna z trzech stacji ze rzędną".

**Liczba 8 z 12 jest prawdziwa. Uzasadnienie było fałszywe** — i złapała je kontrola
negatywna, nie przegląd kodu. Po zamianie normalizacji na `strip()` zestaw przeszedł
**16/16**, bo dopasowanie ścisłe po **pełnym zestawie pól** daje 12 z 12 i tak:

```
pelny zestaw pol osi ('name_fr', 'name_nl', 'name') -> 12 z 12

po zdjeciu JEDNEGO pola:
   bez name_fr    ('name_nl', 'name')      -> 12 z 12   pole zbedne
   bez name_nl    ('name_fr', 'name')      -> 12 z 12   pole zbedne
   bez name       ('name_fr', 'name_nl')   -> 10 z 12   POLE ZARABIA

tylko name_fr, tylko CSV station_fr (naiwnie): 8 z 12
```

Liczba 8 z 12 opisuje wariant **jednopolowy**, którego to narzędzie nigdy nie używało.
Ratuje sytuację **zestaw pól**, nie normalizacja: `name` niesie wariant dwujęzyczny
z pełną pisownią (`Comte de Flandre|Graaf van Vlaanderen`), a `name_nl` łapie wiersze,
w których rejestr podaje nazwę niderlandzką.

Normalizacji więc **nie ma**. Martwy mechanizm z nieprawdziwym uzasadnieniem jest gorszy
od jego braku — to ta sama zasada, którą projekt stosuje do stałych, których nikt nie
czyta (`tools/tests/test_dead_constants.py`). Prawdziwym zabezpieczeniem jest **odmowa**:
kod wyjścia 3 i wypisane nazwy, gdy dopasowanie nie obejmie wszystkich stacji.

## 5. Kontrole negatywne — cztery, wszystkie WYKONANE

**KN-1: reguła zdjęta** — interpolacja od pierwszej do ostatniej znanej, przez niewiadome:
```
FAIL test_interpolacja_NIE_PRZECHODZI_przez_stacje_bez_rzednej: 63 z 63 punktów między
  De Brouckère i Parc dostało rzędną, choć między nimi leży stacja bez rzędnej
FAIL test_interpolacja_jest_monotoniczna_miedzy_dwiema_znanymi: ciąg nie jest monotoniczny
FAIL test_pokrycie_podaje_DWIE_liczby...: rozpiętość nominalna 485.29 < odcinki 1412.788
  13/16 przeszło
```

**KN-2: normalizacja zdjęta** — `16/16 przeszło`. **To jest kontrola, która niczego nie
złapała, i właśnie dlatego jest najcenniejsza z czterech**: pokazała, że mechanizm nie
jest nośny, a jego uzasadnienie nieprawdziwe. Gdybym jej nie wykonał, w drzewie zostałby
kod z fałszywym komentarzem.

**KN-3: ekstrapolacja dopuszczona**:
```
FAIL test_ekstrapolacji_nie_ma...: 352 punktów poza zakresem znanych stacji dostało
  rzędną, np. {'chainage_m': 0.0, 'depth_m': -87.187, ...}
FAIL test_rzedne_sa_ujemne...: 94 punktów ma rzędną >= 0, np. depth_m: 0.051
  12/16 przeszło
```
Rzędna **−87,187 m** na kilometrażu 0 i **dodatnia** rzędna za Arts-Loi to dwa objawy tej
samej usterki: przedłużenie spadku −20,0 → −12,0 w rejon, o którym źródła nie mówią nic.

**KN-4: pole `name` zdjęte z zestawu**:
```
FAIL test_KAZDE_pole_zestawu...: pełny zestaw ('name_fr', 'name_nl') dopasowuje 10 z 12
FAIL test_dopasowanie_obejmuje_WSZYSTKIE_stacje...: dopasowano 10 z 12 stacji;
  bez pary w CSV: ['Comte de Flandre', 'De Brouckère']
  13/17 przeszło
```
Kontrola **nazywa** obie zgubione stacje, w tym De Brouckère.

## 6. Weryfikacja

```
$ python3 tools/track/vertical_profile.py --axis data/track/L1_A.json \
      --depths data/network/station-depths.csv --out build/L1_A-vertical.json
[PROFIL] oś L1_A, pakiet A, 6686.35 m
[PROFIL] stacji ze rzędną: 3 z 12
[PROFIL]       0.00 m  Gare de l'Ouest|Weststation            NIEWIADOMA
[PROFIL]     509.73 m  Beekkant                               NIEWIADOMA
[PROFIL]    1451.90 m  Étangs Noirs|Zwarte Vijvers            NIEWIADOMA
[PROFIL]    2054.78 m  Comte de Flandre|Graaf van Vlaanderen  NIEWIADOMA
[PROFIL]    2720.75 m  Sainte-Catherine|Sint-Katelijne        NIEWIADOMA
[PROFIL]    3129.94 m  De Brouckère                           -12.0 m (estimated)
[PROFIL]    3731.85 m  Gare Centrale|Centraal Station         NIEWIADOMA
[PROFIL]    4075.66 m  Parc|Park                              -20.0 m (estimated)
[PROFIL]    4560.95 m  Arts-Loi|Kunst-Wet                     -12.0 m (estimated)
[PROFIL]    5152.42 m  Maelbeek|Maalbeek                      NIEWIADOMA
[PROFIL]    5467.35 m  Schuman                                NIEWIADOMA
[PROFIL]    6686.35 m  Merode                                 NIEWIADOMA
kod: 0
```

Moduł testowy: **17/17 przeszło**.

## 6a. Dwie cudze bramki PRZEKIEROWANE, bo powstanie tego pliku je wywróciło

Obie należą do świeżo scalonej 6.D32 (`tools/tests/test_field_paths.py`) i obie padły
**z powodu poprawnego wykonania tej pozycji**, nie z powodu usterki.

**Pierwsza — atrapa zależna od stanu kolejki.** Test syntetyczny używał
`tools/track/vertical_profile.py` jako przykładu pliku nieistniejącego, a ten plik był
**obiecany w polu „Wyjście" pozycji 6.B44**. Atrapa zależała więc od tego, że pozycja
z kolejki NIE zostanie wykonana. Podmienione na nazwę ATRAPA_ktorej_nie_bedzie.py w tym samym katalogu
— nazwę, która nie jest niczyim wyjściem, więc próbka mierzy regułę, a nie kolejkę.

**Druga — próg, który wymagał, żeby pozycje nie były wykonywane.**
`test_the_same_block_output_rule_is_the_one_actually_carrying_the_exceptions` żądał
`len(carried) >= 3` i zapalił się przy 1, bo `tools/track/vertical_profile.py`
i `tools/tests/test_vertical_profile.py` **przestały być wyjątkami — powstały**.

Autor tej bramki **przewidział ten przypadek w jednym teście i nie przewidział w drugim**;
w `test_removing_the_field_distinction_moves_the_reported_set` stoi wprost:

> Liczba 4 NIE jest tu wpisana jako asercja i to jest wybór: `tools/track/vertical_profile.py`
> (6.B44) i test_test_track_fixture.py (6.B8) mają kiedyś powstać, a
> wtedy zbiór luźny zejdzie do 2

Przekierowanie sprawdza **więcej**, nie mniej: zamiast liczby żąda, żeby **zdjęcie reguły
faktycznie dołożyło zgłoszenia** i żeby dołożyło **dokładnie te ścieżki**, które reguła
usprawiedliwia. Dowód żywotności reguły nie zależy już od tego, ile pozycji zostało
niewykonanych.

**KN-5:** reguła rozbrojona w `accepted()` (`hit["in_own_output"]` → `False`):
```
FAIL test_the_same_block_output_rule_is_the_one_actually_carrying_the_exceptions:
  zdjęcie reguły nie dołożyło ani jednego zgłoszenia, choć usprawiedliwia 1 ścieżek
  — jedna z tych dwóch rzeczy jest policzona źle:
  [('6.B8', 'Wyjscie', 'tools/tests/test_test_track_fixture.py')]
FAIL test_removing_the_field_distinction_moves_the_reported_set
FAIL test_the_three_kinds_of_exception_are_told_apart_on_synthetic_input
  9/12 przeszło
```

Do tego `test_only_z_trafieniami_nadal_konczy_sie_zerem` w module mutacyjnym przybija
liczbę celów w `tools/track/` — **19 → 20**, bo doszedł nowy plik. Ta liczba mierzy
drzewo i rośnie razem z nim; nie jest progiem i nie wolno jej zamienić na nierówność,
bo przestałaby odróżniać „zawężenie trafiło w katalog" od „trafiło w cokolwiek".

## 7. Czego świadomie NIE zrobiłem

- **Nie tknąłem `data/network/station-depths.csv`.** Wypełnianie tego pliku należy do
  człowieka (T-901) i `CLAUDE.md` §4.6 czyni `data/` tylko do odczytu. Test
  `test_narzedzie_nie_pisze_do_data` sprawdza to **odciskiem SHA-256** przed i po,
  nie ufnością.
- **Nie wybrałem zwycięzcy w konflikcie 15 m vs 17,42 m dla Schuman.** Rejestr go nie
  wybiera i narzędzie też nie — stacja zostaje niewiadomą.
- **Nie podłączyłem profilu do `tools/blender/tunnel_manifest.py`.** Manifest jest w polu
  „Wejście" tej pozycji jako **wzorzec narzędzia**, nie jako cel; podłączenie zmieniałoby
  geometrię, której nie mam czym zweryfikować (Blendera w tym kontenerze nie ma).
- **Nie dodałem interpolacji spline ani wygładzania.** Prosta między dwiema wartościami
  jest założeniem, które da się podważyć pomiarem; krzywa dokładałaby drugie założenie
  — o kształcie spadku — bez żadnego źródła.

## 8. Zauważone przy okazji, nietknięte

`data/track/L1_A.json` ma w każdej stacji pola `depth_m: null` i `interpolated: false`
— **czekają puste od #86**. To znaczy, że oś była przygotowana na rzędne, których nigdy
nie dostała, i że istnieją dziś **dwa** miejsca, w których profil pionowy mógłby żyć:
te pola w `data/` i wyjście tego narzędzia w `build/`. Drugie jest właściwe (`data/`
to tylko odczyt), ale pierwsze nie jest oznaczone jako nieużywane i przy następnym
czytaniu osi wygląda jak dane, które ktoś zapomniał wypełnić. Osobna pozycja: albo
adnotacja w osi, albo bramka mówiąca, że te pola są celowo puste.

Drugie: `vertical.status` w osi mówi `"not_modelled"` i odsyła do T-112 jako do zadania,
które to odblokuje. Po tej pozycji zdanie jest **niepełne** — profil istnieje, tylko na
7,26 % osi i w `build/`, nie w `data/`. Nie poprawiłem go, bo `data/` jest tylko do
odczytu, ale rozjazd jest realny.
