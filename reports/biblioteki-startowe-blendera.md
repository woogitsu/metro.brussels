# Biblioteki systemowe, których Blender 5.2.1 potrzebuje do startu

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`

Dokument jest samowystarczalny: ma być czytany także poza tym repozytorium, przez kogoś,
kto ma dostęp do maszyn puli `woogitsu-linux-01` … `-10` i nie musi znać reszty projektu.

---

## 1. Do czego to jest potrzebne

07.09.2026 na runnerze `woogitsu-linux-01` padły cztery joby Blenderowe (run 34153517889
i dalsze). Pobranie Blendera udało się, suma SHA-256 archiwum **zgodziła się**, a jedyne,
co job powiedział o przyczynie, to:

```
[BLENDER] BŁĄD: po rozpakowaniu .../blender-5.2.1-linux-x64/blender zgłasza '', oczekiwano '5.2.1'
```

Pusty numer wersji. Blender, który nie wstaje, pisze `error while loading shared
libraries: <nazwa>` **wyłącznie na stderr** i nic na stdout, a instalator ten stderr
odrzucał — więc nazwa brakującej biblioteki nigdy nie dotarła do logu. Ten dokument
podaje ją z pomiaru zrobionego inną drogą, bez dostępu do tamtej maszyny.

Rozstrzygające dla „to nie wina zmiany w kodzie": job `tunnel-alignment (L1_A)`
**przeszedł na tym samym commicie**, startując w tej samej sekundzie co padający
`(L1_B)`. Ten sam kod, ta sama treść, inna maszyna, przeciwny wynik.

---

## 2. Jak zostało zmierzone

Lista **nie jest zgadnięta**. Zgadnięta lista braków wygląda dokładnie jak zmierzona,
dopóki ktoś nie zapłaci za różnicę cudzym czasem.

1. Pobrany **przypięty** tarball `blender-5.2.1-linux-x64.tar.xz` z download.blender.org
   i sprawdzona jego suma SHA-256 wobec wartości z `tools/ci/blender-version.txt` —
   `OK`, czyli to bajt w bajt ten sam plik, który dostał runner.
2. `readelf -d` po **wszystkich 201 plikach ELF** w archiwum: główne binaria, biblioteki
   z katalogu bibliotek archiwum i moduły rozszerzeń Pythona.
3. Odjęte **283 sonames, które archiwum dostarcza samo** (tych na maszynie być nie musi).
   Zostało 28 nazw oczekiwanych od systemu.
4. Z tych 28 policzone **domknięcie startowe** binarium `blender`: tylko to, co ładowacz
   rozwiązuje **przed** wejściem w `main()`. To rozróżnienie jest tu istotne — awaria
   była na `--version`, a moduły Pythona wczytują się dopiero przy imporcie i do tej
   awarii się nie liczą.
5. Nazwy pakietów sprawdzone `dpkg -S` na **Ubuntu 24.04.4 LTS**, tym samym wydaniu,
   na którym stoją runnery. Żadna nie jest wpisana z pamięci.

Zależności `DT_NEEDED` są zapisane w samym pliku ELF, więc krok 2 i 4 nie wymagają ani
uruchamiania Blendera, ani dostępu do zepsutej maszyny.

---

## 3. Co doinstalować

Dziewięć bibliotek. Bez którejkolwiek z nich `blender --version` nie startuje.

| soname | pakiet Ubuntu 24.04 | wymaga jej |
|---|---|---|
| `libX11.so.6` | `libx11-6` | binarium `blender` bezpośrednio |
| `libXrender.so.1` | `libxrender1` | binarium `blender` bezpośrednio |
| `libXfixes.so.3` | `libxfixes3` | binarium `blender` bezpośrednio |
| `libXi.so.6` | `libxi6` | binarium `blender` bezpośrednio |
| `libxkbcommon.so.0` | `libxkbcommon0` | binarium `blender` bezpośrednio |
| `libGL.so.1` | `libgl1` | biblioteka USD wieziona w archiwum |
| `libXext.so.6` | `libxext6` | biblioteka USD wieziona w archiwum |
| `libICE.so.6` | `libice6` | biblioteka USD wieziona w archiwum |
| `libSM.so.6` | `libsm6` | biblioteka USD wieziona w archiwum |

Cztery ostatnie są zależnościami **przechodnimi**, ale nie opcjonalnymi: binarium
`blender` linkuje tę bibliotekę USD wprost, więc ładowacz rozwiązuje cały ten graf
przed `main()`.

```bash
sudo apt-get install -y \
    libx11-6 libxrender1 libxfixes3 libxi6 libxkbcommon0 \
    libgl1 libxext6 libice6 libsm6
```

Instalacja wszystkich dziewięciu jest bezpieczna: te już obecne apt pominie.

---

## 4. Dziura w tym, co repozytorium instaluje dziś

`tools/ci/apt-packages/blender.txt` niesie dwa pakiety: `libegl1` i `libgl1-mesa-dri`.
Sprawdzone zawartością pakietu, nie z nazwy:

```
$ dpkg -L libgl1-mesa-dri | grep -c "libGL\.so"
0
```

**`libgl1-mesa-dri` nie dostarcza ani jednego pliku `libGL.so`** — wozi wyłącznie
sterowniki DRI. `libGL.so.1` daje `libgl1`, którego na tej liście nie ma.

Wniosek jest mocniejszy, niż wygląda: `libGL.so.1` jest zależnością **startową**
Blendera, a repozytorium nigdy jej nie instalowało. Na starych maszynach puli była
obecna z innych powodów, więc brak nigdy się nie ujawnił. Nazwa `libgl1-mesa-dri` czyta
się jak „to daje libGL" i to jest dokładnie ta pomyłka, którą łatwo powtórzyć.

**Oba istniejące pakiety zostają.** Nie są zamiennikami dla dziewiątki wyżej, są
zestawem do innego momentu: `libegl1` **nie jest** w domknięciu startowym, bo Blender
ładuje EGL dopiero przy renderze headless, a `libgl1-mesa-dri` daje programowy
sterownik, bez którego Blender startuje i wywraca się przy pierwszej klatce.

---

## 5. Czego NIE instalować

Ta sekcja jest równie ważna jak sekcja 3: `readelf` po całym archiwum wypisuje 28 nazw,
a dosypanie wszystkich byłoby zgadywaniem w drugą stronę.

| soname | dlaczego nie |
|---|---|
| `libcuda.so.1` | backend CUDA denoisera, ładowany leniwie przez `dlopen`; przychodzi ze sterownikiem NVIDIA, nie z pakietu bibliotecznego |
| `libamdhip64.so.7` | to samo dla HIP (AMD) |
| `libze_loader.so.1` | to samo dla oneAPI Level Zero |
| `libXt.so.6` | wymagają jej wyłącznie moduły Pythona MaterialX, nie ścieżka startowa |
| `libGLX.so.0`, `libOpenGL.so.0` | jak wyżej — moduły Pythona MaterialX/USD |
| `libncursesw.so.6`, `libpanelw.so.6`, `libtinfo.so.6` | moduły `_curses` i `_curses_panel` Pythona Blendera |
| `libuuid.so.1` | moduł `_uuid` Pythona Blendera |
| `libc.so.6`, `libm.so.6`, `libdl.so.2`, `librt.so.1`, `libpthread.so.0`, `libutil.so.1`, `libstdc++.so.6`, `libgcc_s.so.1`, `ld-linux-x86-64.so.2` | glibc i gcc — na każdym Linuksie z definicji |

Trzy pierwsze wiersze są tu z konkretnego powodu: brak backendu GPU **nie** blokuje
startu ani renderu na CPU, więc ich obecność na liście „do doinstalowania" kazałaby
komuś szukać sterownika, którego to zadanie nie wymaga.

---

## 6. Dowód, że dziewięć wystarcza

Binarium z tego samego archiwum, uruchomione tam, gdzie te dziewięć bibliotek jest:

```
$ ./blender --version
Blender 5.2.1 LTS
	build date: 2026-08-25
	build time: 02:12:34
kod=0

$ ldd ./blender | grep "not found"
  (żadnych)
```

Zero `=> not found` znaczy, że lista **nie ma dziur** — nie została w niej pominięta
żadna biblioteka. Wypisany numer `5.2.1` to dokładnie ta wartość, której instalator
oczekiwał, a której na runnerze nie dostał.

---

## 7. Czego ten dokument NIE rozstrzyga

Mówi, czego Blender **potrzebuje** — nie mówi, których z tych dziewięciu brakuje
**konkretnie** na `woogitsu-linux-01`. Tego nie da się ustalić bez dostępu do tamtej
maszyny, a wnioskowanie „skoro padło, to brakuje wszystkich" byłoby dokładnie tym
zgadywaniem, którego ten dokument unika.

Odpowiedź maszynowa przyjdzie sama: po zmianie w `tools/ci/blender_install.sh`, która
przestaje odrzucać stderr i **wylicza** braki przez `ldd`, log CI wypisze
`brakuje bibliotek systemowych: <nazwy>` z tej właśnie maszyny. Do tego czasu lista
z sekcji 3 jest kompletnym nadzbiorem — instalacja całej dziewiątki załatwia sprawę
niezależnie od tego, których brakowało.

---

## 8. Zauważone przy okazji

Sonda w `.github/actions/probe-tools/action.yml` jest wołana w tych jobach z jedną
biblioteką: `libEGL.so.1`. Wypisała `wszystko sondowane jest na miejscu` **w tym samym
jobie, w którym Blender nie wstał** — i była to prawda, bo `libEGL.so.1` faktycznie
tam było, a startu blokowało coś, o co sonda nie pytała.

Jest to ta sama rodzina usterki co pusty numer wersji: bramka zielona, bo pyta o zbyt
mało. Rozszerzenie sondy na dziewiątkę z sekcji 3 wymaga tej listy — i to jest powód,
dla którego pozycja naprawiająca komunikat zapisała rozszerzenie sondy jako **poza
swoim zakresem**: bez pomiaru lista byłaby zgadnięta.
