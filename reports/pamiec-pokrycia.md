# Mapa pokrycia liczona raz na commit (6.B36)

**Zmierzone 07.09.2026 na commicie:** `aa64156ce02d00c1396911623919bca6e088bfa8`
(baza gałęzi `claude/6b36-pamiec-pokrycia`).

## 1. Dwa pomiary, których żądało pole „Wyjście"

Pole mówiło wprost: *„najpierw pomiar, potem kierunek"*, i wymieniało dwie rzeczy.

**Czy mapa zależy od mutowanego modułu.** Nie — i widać to najpierw z sygnatury:
`coverage_map(out_dir, timeout)` **nie bierze żadnego argumentu o module**. Jeden
przebieg zestawu z licznikiem wierszy w kopii `git worktree add --detach HEAD`,
śledzone jest całe `tools/`. Potwierdzone przebiegiem na **innym** module (§3, p3):
mapa policzona dla `lod_paths.py` posłużyła bez zmian dla `crs.py`.

**Ile z tego to sam zestaw, a ile narzut instrumentacji.** Zmierzone trzema
przebiegami w drzewie roboczym `git worktree`:

```
zestaw bez sondy   54.49 s     (RAZEM 53.199 s, 1809 testów, 99 modułów, kod 0)
zestaw z sondą    332.57 s
zestaw z sondą    331.92 s
```

Narzut licznika wierszy to **około 278 s**, czyli sonda kosztuje **6,1 raza** tyle,
co goły zestaw. Liczby są niższe od tych z 6.B20 (416,7–426,6 s) — tamten pomiar jest
z datą i się go nie przelicza; obciążenie maszyny i drzewo były inne. Dla kierunku nie
ma to znaczenia: w obu pomiarach sonda dominuje.

## 2. Znalezisko, które zmieniło implementację

Dwie sondy z **tego samego drzewa** dały po **162 klucze** i te same **25 732
wiersze**, ale **różne zbiory kluczy**:

```
mapy IDENTYCZNE: False
  rozne klucze: ['tools/tests/test_dwa_4ydu68u1/test_dwa_testy.py',
                 'tools/tests/test_dwa_f0tjwadq/test_dwa_testy.py',
                 'tools/tests/test_pusty_7l141vtn/test_bez_zadnego_testu.py',
                 'tools/tests/test_pusty_xfz551js/test_bez_zadnego_testu.py']
  rozne wartosci w 0 modulach
```

Różnica to **piaskownice, które zestaw zakłada sam** — bramka 6.D25 tworzy
`tools/tests/test_dwa_<losowe>/` i `tools/tests/test_pusty_<losowe>/`, a losowy
przyrostek zmienia się co przebieg. **W ani jednym module wspólnym dla obu map zbiory
wierszy się nie różniły.** Mapa jest więc stabilna per commit dla każdego prawdziwego
modułu, a jedyną niestabilnością są ścieżki efemeryczne.

Gdybym zapamiętał mapę bez obcięcia, każdy test porównujący mapę z pamięci z policzoną
od nowa byłby **chwiejny** — i to nie z winy pokrycia. Dlatego `pokrycie_w_celach`
obcina mapę do celów mutacji, a obcięcie jest przy tym darmowe i **nie zmienia ani
jednego werdyktu**:

```
kluczy w mapie: 162      z tego celow mutacji: 57       (celow jest 63)
wierszy razem: 25732     w celach: 7582
kluczy pod tools/tests/: 105
```

Sześciu celów zestaw nie uruchamia wcale, a sto pięć kluczy to `tools/tests/` — zestaw
obserwujący sam siebie. `was_executed` pyta wyłącznie o `mutation.path`, czyli zawsze
o cel, i jest **jedynym** czytnikiem tej mapy; sprawdzone: żaden cel mutacji nie leży
pod `tools/tests/`, więc obcięcie nie może zgubić prawdziwego modułu.

## 3. Oszczędność, z czterech przebiegów tego samego modułu

```
p1    pamięć pusta,  lod_paths.py (2 mutacje)     437.2 s   sonda policzona
p2    pamięć pełna,  lod_paths.py, inny dziennik  112.7 s   mapa z pamięci
KN-1  pamięć z cudzym commitem, lod_paths.py      445.7 s   sonda policzona od nowa
KN-2  pamięć właściwa, lod_paths.py               113.6 s   mapa z pamięci
```

Zimno **437,2 / 445,7 s**, z pamięci **112,7 / 113,6 s** — oszczędność około
**328 s, czyli 74 %**. Przebieg na **innym** module z tej samej pamięci:

```
p3    pamięć pełna, crs.py (29 mutacji)           891.7 s
      [MUTACJE] sonda pokrycia: mapa z pamieci … (57 modulow) — commit aa64156 bez zmian
      [MUTACJE] wykonywanych wierszy dotyczy 29 z 29 mutacji
```

891,7 s to praca 29 mutacji, nie sonda — i to jest dowód, że mapa przechodzi **między
modułami**, o co pytało pole „Wyjście".

## 4. Werdykty identyczne — wiersz po wierszu

```
wpisow: 2 / 2   te same identyfikatory: True
roznice w polach istotnych: BRAK

  tools/blender/lod_paths.py:28:1362
    p1: przezyla=False wykonana=True kod=1 padlo=4
    p2: przezyla=False wykonana=True kod=1 padlo=4
  tools/blender/lod_paths.py:28:1365
    p1: przezyla=False wykonana=True kod=1 padlo=4
    p2: przezyla=False wykonana=True kod=1 padlo=4
```

Porównane pola: `przezyla`, `rozstrzygniete`, `wykonana`, `kod`, `plik`, `wiersz`,
`rodzaj`, `bylo`, `jest`, `commit`, `odcisk`, `ile_padlo`.

## 5. Klucz to COMMIT, nie odcisk treści — i to jest różnica warta nazwania

6.B32 (tego samego dnia) kluczuje dziennik **odciskiem treści z drzewa roboczego**,
bo `collect` liczy mutacje właśnie z drzewa roboczego. Sonda przeciwnie: czyta kopię
`git worktree add --detach HEAD`, więc jej wynik zależy od `HEAD` i **tylko** od
`HEAD`. Dwa klucze do dwóch różnych rzeczy, każdy zmierzony.

Caching **nie wprowadza tu nowego zagrożenia**: mapa była policzona z `HEAD` już przed
tą pozycją, więc przy `--dirty` była i jest niezgodna z mutowaną treścią w ten sam
sposób. To jest granica, której 6.B36 nie przesuwa.

Commit jest **krótki** (`git rev-parse --short HEAD`), tak samo jak w `default_journal`
i we wpisie dziennika z 6.B19 — jedna konwencja w jednym narzędziu.

## 6. Kontrola negatywna, której żądało pole „Skończone, gdy" — WYKONANA

Mapa z **innego commita** musi być **odrzucona, a nie użyta**. Commit podmieniony
**wewnątrz pliku**, nazwa pliku bez zmian — bo nazwę da się zmienić jednym `mv`:

```
=== stan pamieci przed KN-1 ===
  wersja: 1  commit w pliku: 0000000  modulow: 57

=== KN-1: PELNY przebieg z cudzym commitem w pliku ===
  kod=0  CALOSC 445.676204423 s
    [MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy
    [MUTACJE] mapa zapamietana w /tmp/metro-pokrycie-aa64156.json: 57 modulow z 162 sledzonych

=== stan pamieci PO KN-1 ===
  commit w pliku: aa64156  modulow: 57

=== KN-2: ten sam przebieg raz jeszcze, pamiec teraz wlasciwa ===
  kod=0  CALOSC 113.550777494 s
    [MUTACJE] sonda pokrycia: mapa z pamieci … — commit aa64156 bez zmian
```

**Dowodem jest różnica czasów — 445,7 s wobec 113,6 s — a nie komunikat.** Komunikat
mógłby kłamać; przebieg trwający cztery razy dłużej nie może.

**Pierwsza próba tej kontroli była nierozstrzygająca i jest to tu napisane.**
Uruchomiłem ją z `--list`, a ta gałąź wychodzi z `main` **przed** sondą: wiersz
o pokryciu nie pojawił się wcale, plik nie został przepisany, a kontrola nie zmierzyła
niczego. To ten sam kształt pomyłki, który 6.B37 zmierzyło dla `add_worktree`, i dobrze
pokazuje, dlaczego kontrola musi wywracać coś **obserwowalnego**, a nie tylko zostawiać
zielony ekran.

Pozostałe drogi odrzucenia sprawdzone testem jednostkowym: plik nieczytelny, plik
o innej wersji kształtu, plik niebędący słownikiem, `pokrycie` niebędące słownikiem,
plik nieistniejący. Każda daje `None`, czyli „brak mapy" — a nie mapę niepełną.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py test_mutation_sweep.py
  83/83 przeszło          (78 → 83, pięć nowych testów)

$ python3 tools/tests/test_all.py
  1891/1891 przeszło
  RAZEM 68.057 s, 1891 testów, 99 modułów
kod: 0
```

## 8. Czego świadomie nie zrobiono

- **Nie wyłączono sondy** — pole „Poza zakresem". Bez niej ocalałe trafiają do kupki
  „niezmierzone", co narzędzie mówi wprost w pomocy.
- **Nie tknięto limitu czasu mutacji** — jest **wyrocznią** dla mutacji powodujących
  pętlę nieskończoną (zmierzone w 6.B14).
- **Nie skrócono samej sondy.** Pomiar mówi, że narzut instrumentacji to ~278 s
  z 332 s; przyspieszenie licznika wierszy jest osobną pozycją i wymaga własnego
  pomiaru, bo `sitecustomize` z `settrace` jest tu wybrany świadomie (podprocesy).
  Ta pozycja usuwa **powtarzanie** tego kosztu, nie sam koszt.
- **Nie dodano flagi wymuszającej przeliczenie.** Mapa jest samoopisująca się
  i kluczowana commitem, więc stan „pamięć jest nieaktualna" nie ma jak powstać
  bez ręcznej edycji pliku — a wtedy odmowa z §6 go łapie. Flaga byłaby przełącznikiem
  bez przypadku użycia.
- **Mapa stoi w katalogu tymczasowym, nie w repozytorium.** Jest pochodną drzewa,
  nie jego treścią, a `git clean -ffdx` z checkoutu CI zdejmowałby ją przy każdym
  przebiegu — ta sama zasada, dla której Godot i Blender leżą poza workspace.

## 9. Zauważone przy okazji, nie tknięte

**Pierwszy przyrząd pomiarowy nie ruszył wcale i nie zauważyłem tego przez kilka
minut.** Pomiar trzech przebiegów opakowałem w `/usr/bin/time`, którego w tym
kontenerze nie ma:

```
/bin/bash: line 26: /usr/bin/time: No such file or directory
```

Trzy przebiegi nie wykonały się, a skrypt zakończył się **kodem 0**, bo kod wyjścia
brał się z ostatniego polecenia w bloku, nie z przebiegów. Przepisane na pomiar
`date +%s.%N` w shellu. Nie tknięte w repozytorium, bo to był przyrząd doraźny —
ale warte zapisania, bo jest to dokładnie ta klasa usterki, którą ta sesja tropiła
cały dzień: **narzędzie meldujące sukces, nie wykonawszy pracy.**
