# 6.D256 — niewiadomej nie ma: migawka dała liczbę przypiętą na TAMTYM commicie

**Data:** 17.09.2026 · **Gałąź:** `claude/6d256-inna-liczba` · **Baza:** `ee1d054`

## 1. Co twierdziła pozycja

`ZgloszenWaskichWierszami` stoi w `tests/Game.Tests/UiTextTests.cs` na **116**.
Przy 6.D233 zamrożono korpus `src/Game/` bajt w bajt i odtworzenie dało **108**.
Komentarz przy `POZOSTALE_GOLE` w `tools/tests/test_json_required.py` opisywał to
tak — i na tym opisie stało zawężenie zakresu:

> migawka bajt w bajt z dnia pomiaru daje 108 zamiast przypiętych 116. Powód nie
> został ustalony i dlatego zawężenie jest tymczasowe … korpus, zbiór 21 plików
> i każdy czytnik w łańcuchu są bajtowo IDENTYCZNE **z commitem, na którym te liczby
> przypięto** — a wynik i tak jest inny.

Poprzednia sesja wykluczyła po kolei: różnicę korpusu, różnicę zbioru plików (21 = 21
nazwa w nazwę), różnicę któregokolwiek z dziesięciu czytników w łańcuchu, wzrost
katalogu `UiText` (29 → 57, ale **zero** nowych kluczy przechodzi wąską regułę).
Zostało zdanie „powodu nie ustalono".

## 2. Powód: ostatnie cztery słowa cytatu są nieprawdziwe

```
git log -S "ZgloszenWaskichWierszami = 108"  →  7771af3  (6.D186)
git log -S "ZgloszenWaskichWierszami = 116"  →  0ae0acf  (MB-07)
```

**`7771af3` to commit, na którym przypięto 108, a nie 116.** Sto szesnaście przypięto
trzy pozycje MB później. Migawka zamrożona z `7771af3` dała więc dokładnie tę liczbę,
którą **miała** dać; porównano ją z wartością przypiętą znacznie później i nazwano
różnicę zagadką.

Historia samej stałej stoi zresztą w jej własnym komentarzu i mówi to wprost:
`108 -> 112 (MB-04)`, `112 -> 113 (MB-05)`, `113 -> 114 (MB-05)`, `114 -> 116 (MB-07)`.
Odtworzone **108** jest ostatnim ogniwem PRZED tym łańcuchem, co samo w sobie było
wskazówką — liczba nie była losowa, była poprzednią wartością tej samej stałej.

## 3. Zmierzone w trzech układach, nie wywnioskowane

```
worktree @ 7771af3:  private const int ZgloszenWaskichWierszami = 108
   dotnet test --filter Trzynastka…  →  Passed!  - Failed: 0, Passed: 1, Total: 1

worktree @ 0ae0acf:  private const int ZgloszenWaskichWierszami = 116
   dotnet test --filter Trzynastka…  →  Passed!  - Failed: 0, Passed: 1, Total: 1

dzisiejsze drzewo:   private const int ZgloszenWaskichWierszami = 116
   dotnet test --filter Trzynastka…  →  Passed!  - Failed: 0, Passed: 1, Total: 1
```

Czytnik daje na każdym z tych korpusów dokładnie tę liczbę, która jest przy nim
przypięta. **Przyrząd działał; mylił się opis.**

**Poprawiam też własną liczbę z wcześniejszego etapu tej sesji:** notowałem, że dzisiejsze
drzewo daje **120**. Nie daje — daje **116**, a test przechodzi. Liczba 120 nie ma
pokrycia w żadnym z trzech przebiegów wyżej.

## 4. Druga połowa uzasadnienia stoi i jest odtworzona własnoręcznie

Zawężenie miało DWA powody. Pierwszy właśnie upadł. Drugi sprawdziłem od nowa:
osłoniłem wszystkie **24** gołe odczyty w `src/Game/Assets/ChunkManifest.cs`
(`GetProperty` → `RequiredField`, plus `using MetroBxl.Sim.Json;`):

```
Failed Korpus_niesie_konstrukcje_ktorych_stary_czytnik_nie_czytal
Failed Zdejmowanie_jednostek_kosztuje_dwa_werdykty_na_trzystu_trzydziestu_pieciu
Failed Z_trzech_markerow_kontekstu_JSON_a_niesie_liczbe_JEDEN
Failed Trzynastka_z_6D181_odtwarza_sie_CO_DO_JEDYNKI_droga_WIERSZOWA
Failed Ta_sama_miara_droga_CALOPLIKOWA_daje_JEDNO_trafienie_i_jest_nim_ARGUMENT
Failed Ile_literalow_traci_WSZYSTKIE_slowa_przez_BezDziur
Failed!  - Failed: 6, Passed: 312, Skipped: 0, Total: 318
```

Po przywróceniu pliku: `Passed! - Failed: 0, Passed: 318, Total: 318`.

**Sześć, tak samo jak przy 6.D233.** Powód jest strukturalny i nie zniknie: osłona
zmienia `src/Game/`, a te odtworzenia mierzą `src/Game/` **z definicji**. Ich własny
docstring zabrania najtańszej naprawy — „odtworzenie 6.D181 mierzy wtedy inny korpus
i nie ma prawa go poprawiać".

## 5. Rozstrzygnięcie

Wpis `src/Game/Assets/ChunkManifest.cs` w `POZOSTALE_GOLE` **zostaje i dostaje powód
TRWAŁY zamiast tymczasowego** — czego pole „Skończone, gdy" tej pozycji żąda wprost.
Komentarz opisujący nierozstrzygniętą zagadkę jest **przepisany, a nie dopisany obok**,
bo opisywał stan, którego nie ma.

**Czego to NIE znaczy.** Nie znaczy, że `ChunkManifest.cs` nie da się osłonić nigdy.
Znaczy, że da się to zrobić dopiero razem z rozstrzygnięciem, czy sześć odtworzeń ma
mierzyć korpus DZISIEJSZY, czy zamrożony — a to jest decyzja projektowa, nie pomiar,
i ta pozycja jej nie podejmuje. Teraz jednak wiadomo, że zamrożenie **działa**: migawka
z właściwego commita dałaby liczbę zgodną z przypiętą.

## 6. Czego NIE zrobiono

- **Nie osłonięto `ChunkManifest.cs`.** Zapaliłoby sześć odtworzeń, a ich poprawienie
  jest tym, czego ich docstring zabrania.
- **Nie zamrożono korpusu na stałe.** Pomiar mówi, że migawka z `0ae0acf` byłaby zgodna,
  ale wybór między korpusem dzisiejszym a zamrożonym jest decyzją projektową.
- **Nie ruszono `ZgloszenWaskichWierszami` ani sąsiednich liczb** — pole „Poza zakresem"
  pozycji zabrania tego wprost, a po tym pomiarze nie ma zresztą czego poprawiać.

## 7. Co zauważone przy okazji, nietknięte

- **Odtworzona liczba była poprzednią wartością tej samej stałej** i to widać w jej
  własnym komentarzu zmian. Gdy odtworzenie daje liczbę, która stoi w łańcuchu historii
  tej samej stałej, pierwszym podejrzanym jest commit, nie czytnik — warte zapisania
  jako reguła czytania, ale to osobna pozycja.
- **Komentarz przy `POZOSTALE_GOLE` przez trzy doby twierdził coś nieprawdziwego i nie
  pilnowało go nic** — jest komentarzem, nie komunikatem asercji, więc bramka z 6.D255
  go nie czyta. To ten sam kształt, po który sięga 6.D259.
