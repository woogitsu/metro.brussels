# 6.D40 — sonda pytała o jedną bibliotekę z dziesięciu i mówiła prawdę

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`

## 1. Objaw: dwa zdania z jednego joba

```
wszystko sondowane jest na miejscu: libEGL.so.1
...
[BLENDER] BŁĄD: po rozpakowaniu .../blender zgłasza '', oczekiwano '5.2.1'
```

Runy 34153517889 (`woogitsu-linux-01`) i 34155630324 (`woogitsu-linux-07`). Oba zdania
w tym samym jobie, kilkanaście sekund po sobie.

**Sonda nie kłamała.** `libEGL.so.1` na tych maszynach było. Startu Blendera blokowało
dziewięć **innych** bibliotek, o które nie pytała — a jej wyjście `libs=present` gasi
warunek `if: steps.tools.outputs.libs == 'missing'` na kroku instalacji pakietów.
Mechanizm, który miał te biblioteki doinstalować, nie dostawał sygnału, że czegoś
brakuje.

To inna usterka niż 6.D39, choć w tej samej awarii: tamta naprawiła **komunikat**, żeby
dało się zobaczyć, czego brakuje. Ta naprawia **mechanizm** instalacji.

## 2. Dlaczego to przeszło niezauważone tak długo

Stare maszyny puli miały te biblioteki z innych powodów — desktopowy stos WSL wozi
X11 i GL niezależnie od tego, co repozytorium instaluje. Sonda odpowiadała
`libs=present` zgodnie z prawdą, krok instalacji nie był potrzebny, a jego bezczynność
nie miała jak się ujawnić.

Nowa pula `woogitsu-linux-*` tych bibliotek nie ma. 07.09.2026 zatrzymało to **dziewięć
jobów naraz**, a nie jeden — i to jest jedyny powód, dla którego usterka wyszła.

## 3. Lista jest wyliczona, nie wpisana z ręki

Rachunek stoi w raporcie biblioteki-startowe-blendera.md, który wchodzi OSOBNYM
pull requestem — dlatego jest tu wymieniony prozą, nie ścieżką w grawisach: w tym
drzewie ta ścieżka jeszcze nie istnieje, a bramka higieny słusznie to łapie.
Pomiar: przypięty tarball 5.2.1
(suma SHA-256 zgodna), `readelf -d` po **201 plikach ELF** w archiwum, odjęte
**283 sonames wiezione przez samo archiwum**, a z pozostałych 28 policzone
**domknięcie startowe** binarium — to, co ładowacz rozwiązuje przed `main()`.

Siedem workflowów sonduje teraz dziesięć sonames, a oba zestawy apt niosą jedenaście
pakietów (dziesięć odpowiadających sonames plus `libgl1-mesa-dri` na programowy
sterownik, którego żaden soname nie wymaga przy starcie).

## 4. Zdanie w `blender.txt`, którego druga połowa była nieprawdziwa

Poprzednia wersja komentarza mówiła:

> zostają wyłącznie biblioteki, których tarball NIE wozi, bo są systemowe: kontekst EGL
> i programowy sterownik GL. Bez nich Blender startuje i wywraca się dopiero przy
> pierwszym renderze.

Pierwsza połowa jest prawdą. Druga jest fałszem: bez dziewięciu dołożonych pakietów
Blender **nie startuje wcale**. Do tego:

```
$ dpkg -L libgl1-mesa-dri | grep -c "libGL\.so"
0
```

`libgl1-mesa-dri` nie dostarcza **ani jednego** pliku `libGL.so` — wozi wyłącznie
sterowniki DRI. `libGL.so.1` daje `libgl1`, którego w zestawie nie było, a jest to
zależność **startowa**. Nazwa pakietu czyta się jak „to daje libGL" i to jest dokładnie
ta pomyłka, którą łatwo powtórzyć. Komentarz jest **przepisany, nie dopisany obok**.

## 5. Bramka PRZEKIEROWANA, nie poluzowana — i to ona zablokowała tę zmianę

`test_tool_installation_is_conditional_on_the_tool_being_missing` już wcześniej żądała,
żeby **każdy sondowany soname mapował się na pakiet, który TEN workflow instaluje**.
Po dopisaniu sonames zapaliła się natychmiast:

```
FAIL test_tool_installation_is_conditional_on_the_tool_being_missing:
  blender-smoke.yml: sonda pyta o libX11.so.6 (pakiet libx116), a zestaw apt tego
  workflow tego nie instaluje: ['libegl1', 'libgl1', ..., 'libx11-6', ...]
```

Mapowanie soname → pakiet jest w tej bramce **mechaniczne**, a jej docstring obiecywał:

> Przekształcenie jest MECHANICZNE, **nie tablicą wyjątków**: małe litery, `.so`
> wypada, numer ABI zostaje przyklejony. Dzięki temu bramka nie trzyma drugiej listy
> „soname -> pakiet", która rozjechałaby się przy pierwszej nowej bibliotece.

Obietnica była prawdziwa wobec **dwóch** bibliotek, dla jakich ją napisano
(`libEGL.so.1`, `libGL.so.1`), i złamała się na **pierwszej nowej**. Zmierzone
`dpkg -S` na Ubuntu 24.04.4, na dziesięciu sonames z domknięcia startowego:

```
  libEGL.so.1          mechanicznie -> libegl1          dpkg -> libegl1          ZGODNE
  libGL.so.1           mechanicznie -> libgl1           dpkg -> libgl1           ZGODNE
  libX11.so.6          mechanicznie -> libx116          dpkg -> libx11-6         ROZJAZD
  libXrender.so.1      mechanicznie -> libxrender1      dpkg -> libxrender1      ZGODNE
  libXfixes.so.3       mechanicznie -> libxfixes3       dpkg -> libxfixes3       ZGODNE
  libXi.so.6           mechanicznie -> libxi6           dpkg -> libxi6           ZGODNE
  libxkbcommon.so.0    mechanicznie -> libxkbcommon0    dpkg -> libxkbcommon0    ZGODNE
  libXext.so.6         mechanicznie -> libxext6         dpkg -> libxext6         ZGODNE
  libICE.so.6          mechanicznie -> libice6          dpkg -> libice6          ZGODNE
  libSM.so.6           mechanicznie -> libsm6           dpkg -> libsm6           ZGODNE

rozjazdów: 1
```

**Dziewięć z dziesięciu** trafia mechanicznie. Dlatego reguła zostaje, a wyjątek jest
jeden: Debian nazywa pakiet `libX11.so.6` jako `libx11-6`, z dywizem, bo bez niego
numer ABI zlałby się z „11" w nazwie biblioteki. Z docstringu zniknęło wyłącznie
„nie tablicą wyjątków" — zdanie o mechaniczności zostaje, bo opisuje ścieżkę
dziewięciu przypadków.

Przekierowanie sprawdza **więcej** niż stan przed nim, bo doszedł test żądający, żeby
**każdy** wpis tabeli dawał wynik **inny** od reguły mechanicznej. Wpis, który powtarza
regułę, jest gorszy od braku wpisu: dziś nie zmienia zachowania, a jutro będzie dowodem,
że „tabela i tak jest, więc dosypmy".

## 6. Kontrole negatywne — trzy, wszystkie WYKONANE

**KN-1: tabela wyjątków wyczyszczona** („bo mechanicznie działa"):

```
FAIL test_the_package_name_exceptions_are_all_necessary: libX11.so.6 nie mapuje się
  na libx11-6 — reguła mechaniczna daje libx116, a taki pakiet w Ubuntu 24.04 nie istnieje
FAIL test_tool_installation_is_conditional_on_the_tool_being_missing:
  blender-smoke.yml: sonda pyta o libX11.so.6 (pakiet libx116) ...
  55/57 przeszło
```

Dwie bramki naraz, i to jest właściwy wynik: pierwsza nazywa przyczynę, druga pokazuje
skutek na siedmiu workflowach.

**KN-2: wpis redundantny dopisany do tabeli** (`libXi.so.6: libxi6`):

```
FAIL test_the_package_name_exceptions_are_all_necessary:
  wyjątki powtarzające regułę mechaniczną: ['libXi.so.6: reguła sama daje libxi6']
  56/57 przeszło
```

**KN-3: pakiet zdjęty z zestawu przy sondzie nadal o niego pytającej**:

```
FAIL test_tool_installation_is_conditional_on_the_tool_being_missing:
  blender-smoke.yml: sonda pyta o libxkbcommon.so.0 (pakiet libxkbcommon0),
  a zestaw apt tego workflow tego nie instaluje: [...]
  56/57 przeszło
```

Po przywróceniu wszystkiego: `57/57 przeszło`. Moduł 56 → 57 testów (jeden nowy).

## 6a. Ta sama usterka w drugim wymiarze: `unzip`

Po doinstalowaniu dziewięciu bibliotek osiem jobów Blenderowych wstało (dwa doszły do
końca: `m7-shell` 8 min 20 s, `station-details` 8 min 32 s — **pierwsze, które
kiedykolwiek doszły do renderu na tej puli**). `first-run` padł dalej, po **19 sekundach**,
na `woogitsu-linux-02`, run 34155630333:

```
line 10: unzip: command not found
##[error]Process completed with exit code 127
```

Krok pobiera Godota 4.7.2-stable jako `.zip` i rozpakowuje go. `curl` zadziałał, więc
brakowało wyłącznie rozpakowywacza — a `unzip` **nie był ani sondowany, ani w żadnym
zestawie apt**. Sonda mówiła `present`, krok instalacji się nie odpalał, a job wywracał
się czternaście kroków dalej niż powód. To dokładnie ta sama usterka co przy
bibliotekach, tylko w wymiarze poleceń, nie bibliotek.

Bramka miała tu warunek przybity na sztywno do jednego polecenia:

> `xvfb-run` jest jedyną RÓŻNICĄ między dwoma zestawami, więc jest też jedynym
> miejscem, w którym sonda poleceń ma sens

Zdanie było prawdziwe, **dopóki różnica była jedna**. Warunek jest **przepisany**, nie
dopisany obok: tabela `POLECENIA_Z_PAKIETOW` i pętla po **każdym** jej wpisie, w obie
strony. Dla poleceń nie ma reguły mechanicznej (`unzip` z pakietu `unzip`, ale
`xvfb-run` z pakietu `xvfb`), więc tabela jest tu jedynym uczciwym rozwiązaniem
i nie udaje reguły — inaczej niż przy nazwach pakietów z §5, gdzie reguła trafia
w dziewięć przypadków z dziesięciu.

Trzy dalsze kontrole negatywne:

```
KN-4 (unzip w zestawie apt, sonda o niego nie pyta — stan sprzed poprawki):
  FAIL ...: godot-first-run.yml: instaluje pakiet unzip, a sonda o `unzip` nie pyta
    — krok instalacji nie dostanie sygnału, że go brakuje
  56/57 przeszło

KN-5 (sonda pyta o unzip, zestaw apt go nie instaluje):
  FAIL ...: sonda pyta o `unzip`, a zestaw apt tego workflow nie instaluje pakietu unzip
  56/57 przeszło

KN-6 (czy po uogólnieniu STARY warunek na xvfb nadal działa):
  FAIL ...: instaluje pakiet xvfb, a sonda o `xvfb-run` nie pyta
  56/57 przeszło
```

**KN-6 jest tu najważniejsza:** uogólnienie warunku mogło go po cichu osłabić, a ta
kontrola pokazuje, że przypadek, który stary warunek łapał, nowy łapie nadal.

## 7. Zapadka bloków

`MINIMUM_DETAIL_BLOCKS` ma 164. Wartość rośnie dalej przy każdym uzupełnieniu kolejki — 09.09.2026 doszło najpierw dziesięć bloków 6.D65 … 6.D74 z weryfikacji audytu zewnętrznego (zapadka 147), a potem siedemnaście bloków 6.D75 … 6.D91 z rundy pięciu agentów (**164**); wcześniej tego samego dnia stała na 137; 08.09.2026 doszły najpierw cztery bloki 6.D48 … 6.D51 (zapadka 124), potem 6.D52 z decyzji właściciela o serializacji jobów (125), a potem pięć pozycji o PRZYRZĄDACH 6.D54 … 6.D58, i zapadka stoi na **130**; po scaleniu doszedł blok 6.D53 (131), a 09.09.2026 bloki 6.D59 w commicie pozycji 6.D58 (132), 6.D60 w commicie pozycji 6.D24 (133) i cztery bloki 6.D61 … 6.D64 z commita uzupełniającego kolejkę (**137**). Liczby w blokach pomiarowych niżej zostają przy swoich datach; ten akapit niesie stan bieżący. **Pomiar niżej jest z 07.09.2026 i zostaje taki,
jaki był** — wtedy wartością równą stanowi drzewa było 112, bo blok 6.D40 był
jedynym dochodzącym. Ta gałąź niosła też zdanie, że druga z pary 6.D39 / 6.D40
musi w rozwiązaniu konfliktu dać **113**; było prawdziwe, gdy w locie były tylko
te dwie gałęzie, ale przed nimi weszły 6.D41 i sześć pozycji uzupełnienia
kolejki, więc równość wypadła siedem wyżej, na 120. Nie przeliczam poniższego
bloku: to była kontrola wykonana na innym stanie drzewa, a przepisanie jej liczb
zamieniłoby zapis pomiaru w zapis przypuszczenia.

**Wniosek, który z tego zostaje na przyszłość:** zapamiętana wartość zapadki
starzeje się między napisaniem pozycji a jej scaleniem. Właściwym rozwiązaniem
konfliktu nigdy nie jest wpisanie liczby z pamięci, tylko POMIAR liczby bloków
w pliku i ustawienie zapadki na jego wynik.

Kontrola z 07.09.2026, przy 112 blokach w drzewie:

```
prog 113:  FAIL ... bloków jest 112 przy zapadce 113        25/26 przeszło
prog 111:  FAIL ... bloków jest 112, a zapadka stoi na 111  25/26 przeszło
prog 112:  26/26 przeszło
```

Kontrola powtórzona 08.09.2026 na drzewie po scaleniu, przy 120 blokach:

```
zapadka 121 (wyzsza od stanu):  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
                                bloków jest 120 przy zapadce 121 — któryś zniknął albo
                                stracił jedno z sześciu pól
                                25/26 przeszło
zapadka 120 (rowna stanowi):    26/26 przeszło
zapadka 119 (nizsza od stanu):  FAIL test_the_documented_ratchet_does_not_lag_behind_the_file:
                                bloków z kompletem sześciu pól jest 120, a zapadka stoi
                                na 119 — podnieś ją do 120 w tym samym commicie
                                25/26 przeszło
```

Każdy przebieg kontroli czyścił `__pycache__` przed uruchomieniem: mutacja
`= 120` na `= 119` ma identyczną długość pliku, a to jest dokładnie ten przypadek,
w którym przywrócenie przez `cp` zostawia nieświeży bajtkod (znalezione przy 6.D41).

## 8. Czego świadomie NIE zrobiłem

- **Nie doinstalowałem niczego ręcznie na maszynach właściciela.** Poprawka idzie przez
  **istniejący** mechanizm warunkowej instalacji: sonda zgłosi teraz `missing`, więc
  pierwszy przebieg zrobi to sam. Nie prosiłem o dostęp i nie proponowałem obejścia.
- **Nie dodałem bibliotek, których wymagają wyłącznie moduły Pythona Blendera**
  (`libXt.so.6`, `libGLX.so.0`, `libOpenGL.so.0`, `libncursesw.so.6`, `libpanelw.so.6`,
  `libtinfo.so.6`, `libuuid.so.1`) **ani backendów GPU denoisera** (`libcuda.so.1`,
  `libamdhip64.so.7`, `libze_loader.so.1`). Nie blokują startu ani renderu na CPU,
  a wpisanie ich kazałoby komuś szukać sterownika, którego to zadanie nie wymaga.
- **Nie zmieniłem treści sondy** w akcji lokalnej. Sonda robiła dokładnie to, co miała;
  usterką był jej **argument**, nie implementacja.
- **Nie tknąłem `runs-on`** — to osobna, równolegle otwarta zmiana.

## 9. Zauważone przy okazji, nietknięte

Lista sonames stoi teraz w **siedmiu** kopiach, po jednej w każdym workflowie. Akcja
`probe-tools` powstała 04.09.2026 dokładnie po to, żeby usunąć siedem kopii sondy —
a jej **argument** siedmiu kopii nie stracił. Dziś to nie boli, bo bramka wiąże każdą
kopię z zestawem apt tego samego workflow, więc rozjazd między kopią a instalacją jest
łapany; nie jest natomiast łapany rozjazd **między kopiami**: sonda pytająca w jednym
workflowie o osiem sonames zamiast dziesięciu przejdzie, jeśli jego zestaw apt też ma
tylko osiem. Przyrząd na to musiałby porównać siedem list ze sobą i zdecydować, która
jest wzorcem — czyli jest to osobna pozycja z własnym pomiarem, nie dopisek do tej.
