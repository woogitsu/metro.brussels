# 6.D39 — pusty numer wersji Blendera bez ani jednego słowa o przyczynie

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`

## 1. Skąd wzięła się ta pozycja

Cztery joby Blenderowe padły na PR #392, którego diff to trzy docstringi, jeden raport
i jeden wiersz w `docs/TASKS.md` — nic z tego nie jest czytane przez żaden potok
Blenderowy. Rozstrzyga jednak nie zasięg diffu, a inny job **tego samego przebiegu**:

| job | wynik | czas | start |
|---|---|---|---|
| `tunnel-alignment (L1_A)` | **success** | 3 min 51 s | 18:54:45 |
| `tunnel-alignment (L1_B)` | failure | 39 s | 18:54:45 |
| `tunnel-alignment (L2_E)` | failure | 39 s | 18:56:33 |
| `station-details` | failure | 39 s | 18:57:53 |
| `visual-regression` | failure | 37 s | 18:57:14 |

`L1_A` i `L1_B` wystartowały **w tej samej sekundzie, z tego samego commita**
`9418d09`, i dały przeciwne wyniki. To nie jest własność treści.

Log padającego joba powiedział o przyczynie **jedno zdanie**:

```
[BLENDER] pobieram https://download.blender.org/release/Blender5.2/blender-5.2.1-linux-x64.tar.xz
100 365.9M 100 365.9M    0     0  30.96M      0  00:11  00:11        29.23M
[BLENDER] sprawdzam sumę SHA-256
/home/matma/actions-runner/woogitsu-linux-01/_work/_temp/blender-5.2.1-linux-x64.tar.xz: OK
[BLENDER] BŁĄD: po rozpakowaniu .../metro-blender/5.2.1/blender-5.2.1-linux-x64/blender zgłasza '', oczekiwano '5.2.1'
```

Pobranie udane, suma **zgodna**, i pusty napis.

## 2. Co dokładnie było nie tak

`tools/ci/blender_install.sh`, przed zmianą:

```bash
installed_version() {
    [ -x "$BIN" ] || return 1
    "$BIN" --version 2>/dev/null | sed -n '1s/^Blender \([0-9.]*\).*/\1/p'
}
```

Blender, który nie startuje, pisze `error while loading shared libraries: <nazwa>`
**wyłącznie na stderr** i nic na stdout. `2>/dev/null` wyrzucało więc dokładnie tę
jedną informację, która jest tu potrzebna — a `[ -x "$BIN" ] || return 1` daje ten sam
pusty napis przy braku pliku. **Trzy różne przyczyny, jeden nierozróżnialny `''`**,
i każda z innym działaniem po stronie czytającego: złe rozpakowanie to usterka
skryptu, brakująca biblioteka to pakiet **na maszynie**.

To ta sama rodzina, którą ten projekt nazywał już wielokrotnie: przyrząd raportuje
pustkę zamiast pomiaru, a pustka wygląda identycznie niezależnie od powodu.

## 3. Dlaczego to nie jest kosmetyka logu

Sonda `probe-tools` przeszła w tym samym jobie:

```
wszystko sondowane jest na miejscu: libEGL.so.1
```

Sprawdza **jedną** bibliotekę, a `tools/ci/apt-packages/blender.txt` niesie dwa pakiety
(`libegl1`, `libgl1-mesa-dri`). Blender 5.2.1 potrzebuje więcej, a na maszynach WSL
tej puli reszta była obecna z innych powodów. Runner nazywa się `woogitsu-linux-01`
i **nie pasuje do żadnego opisu w drzewie**: `CLAUDE.md` §9 wymienia
`woogitsu-wsl-DOM-NEW-01`…`-04`, a komentarz w `blender_install.sh` mówi
o katalogach `~/actions-runner-woogitsu-01`…`-04`. Tarball schodził z sieci, czyli
`runner.tool_cache` był pusty — maszyna jest świeża.

**Tego raport nie rozstrzyga i nie udaje, że rozstrzyga:** czy pula jest wymieniana,
wie właściciel. Zapisane jest wyłącznie to, co widać w logu.

## 4. Poprawka

Cztery przyczyny rozdzielone, każda z własnym zdaniem. Lista brakujących bibliotek
**wyliczona przez `ldd`**, nie wpisana z ręki — wpisana musiałaby być zgadnięta,
a zgadnięta lista braków wygląda jak pomiar i nim nie jest.

## 5. Pierwsza wersja poprawki NIE DZIAŁAŁA, i złapała to kontrola, nie przegląd kodu

To najważniejsza część tej pozycji. Pierwsza wersja trzymała stderr w zmiennej:

```bash
BLENDER_STDERR=""
installed_version() {
    ...
    BLENDER_STDERR="$(cat "$err")"
    ...
}
```

Bramka wykonawcza dała:

```
FAIL test_ci_blender_installer_NAZYWA_powod_gdy_wersja_wyszla_pusta:
  instalator nie powtórzył stderr Blendera, czyli nadal gubi jedyną informację
  o przyczynie
[BLENDER] powód: Blender startuje i nie wypisuje numeru w formacie 'Blender <numer>'
```

Komunikat mówił „startuje i nie wypisuje numeru" o Blenderze, który **nie startował
wcale**. Powód: `installed_version` jest wołane jako `got="$(installed_version)"`,
czyli w **podshellu**, a przypisanie do zmiennej w podshellu nie wychodzi do rodzica.

**Ta poprawka miała więc dokładnie tę usterkę, którą naprawia, o jeden poziom
głębiej** — i sama zgłaszała fałszywą przyczynę z pełną pewnością w głosie.
Rozwiązaniem jest plik zamiast zmiennej: ścieżka jest ustawiona w rodzicu, więc
zapis z podshella zostaje.

## 6. Kontrole negatywne — trzy, wszystkie WYKONANE

**KN-1: rozbrojenie przechwytu stderr.** `2>"$BLENDER_STDERR_FILE"` zamienione
z powrotem na `2>/dev/null`:

```
FAIL test_ci_blender_installer_NAZYWA_powod_gdy_wersja_wyszla_pusta
  56/57 przeszło
kod modulu: 1
```

Po przywróceniu: `57/57 przeszło`.

**KN-2: dwie przyczyny muszą dać DWA RÓŻNE zdania.** Asercja nie sprawdza obecności
napisu, tylko **porównuje oba komunikaty ze sobą** — bramka na obecność przechodziłaby
na komunikacie, który zawsze mówi to samo. Zmierzone wyjście obu przyczyn:

```
=== PRZYCZYNA 1: nie startuje (kod 1) ===
   [BLENDER] powód: Blender startuje, ale konczy sie bledem (stderr nizej)
   [BLENDER] stderr Blendera: blender: error while loading shared libraries: libXi.so.6: cannot open shared object file
=== PRZYCZYNA 2: startuje, milczy (kod 1) ===
   [BLENDER] powód: Blender startuje i nie wypisuje numeru w formacie 'Blender <numer>'
```

**KN-3: gałąź `ldd` na PRAWDZIWYM ELF-ie.** Atrapa w bashu **nie nadaje się** do
sprawdzenia tej gałęzi: `ldd` na skrypcie mówi „not a dynamic executable" i nie
wypisuje ani jednego `=> not found`, więc jedyna gałąź podająca **nazwy** pakietów
zostałaby bez kontroli. Kontrola buduje więc program C linkowany z `libatrapa.so`
i usuwa tę bibliotekę po zlinkowaniu, co odtwarza objaw dosłownie:

```
./blender: error while loading shared libraries: libatrapa.so: cannot open shared object file
kod=127
	libatrapa.so => not found
```

Po zdjęciu gałęzi `ldd` ze skryptu:

```
FAIL test_ci_blender_installer_WYLICZA_brakujace_biblioteki_z_ldd:
  instalator nie doszedł do gałęzi `ldd`, więc nie podał NAZW brakujących bibliotek:
  [BLENDER] powód: Blender startuje, ale konczy sie bledem (stderr nizej)
  57/58 przeszło
```

Po przywróceniu: `58/58 przeszło`, **bez pominięcia** — czyli gałąź jest rzeczywiście
wykonywana, a nie przeskakiwana z braku `gcc`. Na maszynie bez `gcc` test woła
`AG.skip` z powodem, bo pominięcie ma w tym zestawie własny mianownik.

## 7. Zapadka bloków

`MINIMUM_DETAIL_BLOCKS` ma 126. Wartość rośnie dalej przy każdym uzupełnieniu kolejki — 08.09.2026 doszły najpierw cztery bloki 6.D48 … 6.D51 (zapadka 124), potem 6.D52 z decyzji właściciela o serializacji jobów (125), a przy 6.B52 blok 6.D53 o rejestrze źródeł, i zapadka stoi na **126**. Żadna z dwóch gałęzi, które się tu spotkały, nie miała tej liczby: obie mówiły 125, bo obie liczyły tylko własny blok — zapadkę ustawił POMIAR na pliku scalonym. Liczby w blokach pomiarowych niżej zostają przy swoich datach; ten akapit niesie stan bieżący. **Pomiar niżej jest z 07.09.2026 i zostaje taki,jaki był** — wtedy wartością równą stanowi drzewa było 112, bo blok 6.D39 był
jedynym dochodzącym. Do scalenia (08.09.2026) weszły przed nim 6.D41, sześć
pozycji uzupełnienia kolejki i 6.D40, każda ze swoim blokiem, więc równość
wypadła o osiem wyżej. Nie przeliczam poniższego bloku na 119: to była kontrola wykonana
na innym stanie drzewa, a przepisanie jej liczb zamieniłoby zapis pomiaru w zapis
przypuszczenia.

Kontrola z 07.09.2026, przy 112 blokach w drzewie:

```
prog 113 (wyzszy niz stan):  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
                             bloków jest 112 przy zapadce 113
                             25/26 przeszło
prog 112 (rowny stanowi):    26/26 przeszło
```

Kontrola powtórzona 08.09.2026 na drzewie po scaleniu, przy 119 blokach — trzy
kierunki, nie dwa, bo zapadka wymaga RÓWNOŚCI i pomylić się da się w obie strony:

```
zapadka 120 (wyzsza od stanu):  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
                                bloków jest 119 przy zapadce 120 — któryś zniknął albo
                                stracił jedno z sześciu pól
                                25/26 przeszło
zapadka 119 (rowna stanowi):    26/26 przeszło
zapadka 118 (nizsza od stanu):  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
                                bloków z kompletem sześciu pól jest 119, a zapadka stoi
                                na 118 — podnieś ją do 119 w tym samym commicie
                                25/26 przeszło
```

Każdy przebieg kontroli czyścił `__pycache__` przed uruchomieniem: mutacja
`= 119` na `= 118` ma identyczną długość pliku, a to jest dokładnie ten przypadek,
w którym przywrócenie przez `cp` zostawia nieświeży bajtkod (znalezione przy 6.D41).

## 8. Weryfikacja

```
$ python3 tools/tests/test_all.py test_ci_workflows.py
  58/58 przeszło
```

Moduł 57 → 58 testów: dwie nowe bramki (jedna sprawdza dwie przyczyny naraz).

## 9. Czego świadomie NIE zrobiłem

- **Nie doinstalowałem pakietów na `woogitsu-linux-01`.** To maszyna właściciela
  i nie ma tu obejścia. Ta pozycja daje wyłącznie komunikat, z którego wynika,
  co doinstalować.
- **Nie rozszerzyłem `tools/ci/apt-packages/blender.txt`** ani listy w sondzie.
  Lista musi wyjść z **pomiaru na tej maszynie**, który ta pozycja dopiero umożliwia.
  Dopisanie dziś `libxi6 libxxf86vm1 libxfixes3 …` byłoby zgadywaniem wpisanym
  w plik będący **kluczem cache'a** — czyli zgadnięciem, które unieważnia cache
  i wygląda przy tym jak pomiar.
- **Nie wciągnąłem tej poprawki do #392.** Tam idzie 6.B46 o pamięci `collect()`;
  poszerzenie tamtego PR-a o CI byłoby zmianą, o którą nikt nie prosił.
- **Nie tknąłem `2>/dev/null` w innych miejscach drzewa.** Ta pozycja dotyczy jednego
  zmierzonego przypadku; przejście po wszystkich to osobny pomiar.

## 10. Zauważone przy okazji, nietknięte

`powod_pustej_wersji` rozdziela cztery przyczyny, ale **czwarta — wypis w innym
formacie — jest sprawdzona tylko na atrapie milczącej**. Blender, który wypisze
`Blender-5.2.1` albo `blender 5.2.1`, trafi w tę samą gałąź i dostanie ten sam
komunikat, co jest poprawne, ale nierozróżnialne od milczenia. Rozdzielenie
wymagałoby pokazania w komunikacie **pierwszej linii wypisu**, a to osobna zmiana
z własną kontrolą.

Druga rzecz: sonda `probe-tools` sprawdza jedną bibliotekę i **przechodzi na maszynie,
na której Blender nie startuje**. Jest to dokładnie ta sama rodzina co usterka wyżej —
bramka zielona, bo pyta o zbyt mało — ale jej naprawa wymaga listy z pomiaru,
czyli czeka na pierwszy przebieg z nowym komunikatem.
