# `doctor.sh` meldował brak SDK, które leżało na dysku (6.D57)

**Zmierzone 09.09.2026 na:** `a5aa464`, kontener tej sesji.
**Przyrząd:** `env -u DOTNET_ROOT PATH=… bash doctor.sh; echo "kod: $?"` oraz
`python3 tools/tests/test_all.py test_dotnet_version.py`.

---

## 1. Objaw i przyczyna

`/root/.dotnet/dotnet` zgłasza `10.0.400`. `doctor.sh` bez `dotnet` w `PATH`:

```
kod: 1
  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+ (https://dotnet.microsoft.com/download)
```

Rada **„zainstaluj"** jest tu najgorsza z możliwych: SDK jest na dysku, a narzędzie
każe je pobrać.

Przyczyna była w kodzie, nie w środowisku. Przejście po katalogach kandydatów
**oraz** podpowiedź „na dysku JEST nowsze SDK" stały wewnątrz:

```sh
if [ -n "$REQUIRED_TFM" ] && [ -n "$HAVE_SDK_MAJOR" ]; then
  ...
  if [ "$HAVE_SDK_MAJOR" -lt "$REQUIRED_TFM" ]; then
    for candidate in "$HOME/.dotnet/dotnet" ...
```

a `HAVE_SDK_MAJOR` bierze się z `$DOTNET --version`. Bez `dotnet` w `PATH` zmienna
jest **pusta**, więc cały blok się nie wykonywał. Szukanie działało zatem
**wyłącznie** wtedy, gdy w `PATH` stało SDK **za stare**, i nigdy gdy nie stało
żadne.

## 2. Komentarz opisywał tę usterkę od pięciu dni

W `doctor.sh`, dwadzieścia wierszy nad zepsutym blokiem, stało od 04.09.2026:

> Zmierzone w tym środowisku 04.09.2026: `dotnet --version` daje 8.0.130, a obok
> stoi 10.0.400 w `$HOME/.dotnet`, którego doctor nie widział. Kazał więc pobrać
> SDK, które już było na dysku, **i to jest gorsze niż milczenie: brzmi jak brak,
> a jest ślepotą**.

Poprawka objęła wtedy **tylko** przypadek SDK za starego. Zdanie w prozie nazywało
usterkę precyzyjnie i nie zapobiegło jej w drugim wariancie — dokładnie jak
w 6.D56, gdzie „Próg stoi w jednym miejscu" stało trzy wiersze nad kopią progu.
**Deklaracja niezmiennika w prozie nie jest bramką.**

## 3. Dlaczego nie złapał tego żaden test — i to jest luka, nie brak testów

Cztery bramki podpowiedzi już istniały w `tools/tests/test_dotnet_version.py`:
`test_doctor_points_at_the_newer_sdk_that_is_already_on_disk`,
`..._does_not_invent_an_sdk_that_is_not_there`,
`..._does_not_offer_an_sdk_that_is_also_too_old`,
`..._does_not_offer_the_sdk_it_was_already_told_to_use`.

**Wszystkie cztery podstawiają `DOTNET_BIN` na atrapę.** `$DOTNET --version` zawsze
więc coś zwracało, `HAVE_SDK_MAJOR` nigdy nie było puste, i przypadek „w `PATH` nie
ma nic" **nie był sprawdzany przez nic** — a to on jest treścią 6.D57.

Dlatego doszła osobna pomocnicza funkcja `_run_doctor_bez_dotnet_w_path`, która
zdejmuje `DOTNET_BIN` i `DOTNET_ROOT` i zawęża `PATH` do `/usr/bin:/bin`.

## 4. Dwie naprawy NIE są równoważne — i podpowiedź musiała się zmienić

Pozycja twierdziła, że `DOTNET_BIN=<ścieżka>` zdejmuje `BRAK dotnet SDK`, ale
zostawia `WARN godot .NET hostfxr`. **Pierwszy pomiar tego nie potwierdził — i to
mój pomiar był nieważny, nie twierdzenie.** Ustawiłem `PATH=/usr/bin:/bin`, co
wyklucza `/usr/local/bin`, gdzie stoi Godot, więc kontrola `hostfxr` nie odpaliła
się wcale (jest opakowana w `if "$GODOT_CMD" --version`).

Powtórzone z Godotem osiągalnym:

| wariant | `dotnet SDK` | `godot .NET hostfxr` |
|---|---|---|
| nic | **BRAK** | **WARN** |
| `DOTNET_BIN=/root/.dotnet/dotnet` | ok | **WARN — zostaje** |
| `DOTNET_ROOT=/root/.dotnet` + `PATH` | ok | **ok** |

Twierdzenie pozycji jest więc prawdziwe. Mechanizm stoi w samym `doctor.sh`:
`HOSTFXR_OK` bierze się z `DOTNET_ROOT` albo z **gołego** `command -v dotnet` —
a nie z `$DOTNET_BIN`.

**Konsekwencja jest ostrzejsza, niż mówi pozycja:** dotychczasowa podpowiedź
(w gałęzi SDK-za-stare) radziła `uruchom: DOTNET_BIN=$candidate bash doctor.sh`,
czyli **naprawę niepełną**. Zdejmowała jeden komunikat i zostawiała drugi — a ten
drugi mówi o awarii objawiającej się sygnałem 11 albo zawieszeniem bez wypisu.
Podpowiedź mówi dziś `export DOTNET_ROOT=…; export PATH="$DOTNET_ROOT:$PATH"`
i dopisuje, czego samo `DOTNET_BIN` nie załatwia.

## 5. Asercja PRZEKIEROWANA, nie poluzowana

`test_doctor_points_at_the_newer_sdk_that_is_already_on_disk` żądał
`"DOTNET_BIN=" in out and "bash doctor.sh" in out` — czyli **kodował radę
niepełną**. Po przekierowaniu sprawdza **cztery** rzeczy zamiast dwóch:

1. że doctor szukał (`na dysku JEST nowsze SDK`);
2. że nazwał **znalezioną ścieżkę**, a nie radził ogólnie;
3. że podał komplet `DOTNET_ROOT` **razem z** `PATH`;
4. że **nie** stawia gołego `DOTNET_BIN` jako polecenia do uruchomienia.

## 6. Mój własny błąd, złapany przez cztery istniejące bramki naraz

Pierwsza wersja poprawki dopisała do listy kandydatów `/root/.dotnet/dotnet`.
Zaczerwieniło to **cztery** istniejące testy jednocześnie:

```
FAIL test_doctor_does_not_invent_an_sdk_that_is_not_there:
FAIL test_doctor_does_not_offer_an_sdk_that_is_also_too_old: doctor podpowiedzial SDK 9.x przy wymaganym 10:
FAIL test_doctor_does_not_offer_the_sdk_it_was_already_told_to_use:
FAIL test_doctor_points_at_the_newer_sdk_that_is_already_on_disk:
```

Dopisek był **redundantny i szkodliwy naraz**. Redundantny, bo `$HOME` w tym
środowisku **jest** `/root`, więc `$HOME/.dotnet/dotnet` pokrywa tę samą ścieżkę —
zmierzone, nie założone. Szkodliwy, bo ścieżka **bezwzględna** przebija podstawiony
`HOME` w piaskownicy tych bramek: szukanie znajdowało SDK kontenera niezależnie od
tego, co test podstawił, więc podpowiedź zapalała się tam, gdzie testy żądały
milczenia.

Jest to ta sama rodzina co „liczba wpisana z ręki": **ścieżka jednej konkretnej
maszyny wpisana do narzędzia, które ma działać na wielu.** Dopisek został cofnięty
i przy liście stoi zapis, dlaczego go tam nie ma.

## 7. Weryfikacja z pola „Weryfikacja" — oba wyjścia wklejone

```
########## 1) env -u DOTNET_ROOT PATH=/usr/bin:/bin bash doctor.sh
kod: 1
  BRAK  dotnet SDK  -> SDK JEST na dysku: /root/.dotnet/dotnet (wersja 10.0.400) — nie instaluj, tylko uruchom: export DOTNET_ROOT=/root/.dotnet; export PATH="$DOTNET_ROOT:$PATH"   (samo DOTNET_BIN zdejmuje ten komunikat, ale ZOSTAWIA WARN godot .NET hostfxr — zmierzone)

########## 2) bash doctor.sh (srodowisko sesji, bez zmian)
kod: 1
  BRAK  dotnet SDK  -> SDK JEST na dysku: /root/.dotnet/dotnet (wersja 10.0.400) — nie instaluj, tylko uruchom: export DOTNET_ROOT=/root/.dotnet; export PATH="$DOTNET_ROOT:$PATH"   (samo DOTNET_BIN zdejmuje ten komunikat, ale ZOSTAWIA WARN godot .NET hostfxr — zmierzone)
  WARN  godot .NET hostfxr  -> ustaw DOTNET_ROOT na katalog SDK z host/fxr/*/libhostfxr.so (np. $HOME/.dotnet) albo dodaj dotnet do PATH — inaczej Godot mono pada sygnałem 11 (Failed to load hostfxr) albo wisi bez wyjścia przy starcie sceny z C#
```

Kod **1**, nie 0, i to jest poprawne: SDK nadal nie jest osiągalne, więc pozycja
wymagana pozostaje niespełniona. Zmieniło się to, że doctor **mówi, co zrobić**,
zamiast kazać instalować to, co ma.

Cały zestaw:

```
2054/2054 przeszło
RAZEM 114.430 s, 2054 testów, 109 modułów
kod: 0
```

## 8. Kontrole negatywne

### KN-A: kandydat `$HOME/.dotnet/dotnet` usunięty z listy

```
FAIL test_doctor_points_at_the_newer_sdk_that_is_already_on_disk:
  25/26 przeszło
kod: 1
```

Tego żąda pole „Skończone, gdy". `md5` `doctor.sh` po przywróceniu:
`c4004bce808c8c30130f6526a8758a98`.

### KN-B: SDK **naprawdę** nieobecne

```
kod: 1
  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+ (https://dotnet.microsoft.com/download)
--- czy obiecuje cokolwiek na dysku:
0
```

Zachowanie bez zmian, i sprawdzone osobno bramką
`test_doctor_bez_dotnet_w_PATH_i_bez_sdk_na_dysku_nadal_kaze_instalowac`.

### KN-C: nowe bramki na kodzie SPRZED poprawki

```
FAIL test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku: doctor melduje brak SDK, choć leży ono na dysku — to usterka 6.D57:
  ok   test_doctor_bez_dotnet_w_PATH_i_bez_sdk_na_dysku_nadal_kaze_instalowac
  26/28 przeszło
kod: 1
```

Nowa bramka czerwienieje, a jej **para zostaje zielona** — bo zachowanie „nic na
dysku" było już poprawne i poprawka go nie ruszyła. Dwa FAIL-e z 28 to ta nowa
i asercja przekierowana z §5; obie z powodu, który poprawka usuwa.

`md5` `doctor.sh` po każdym przywróceniu ta sama; `__pycache__` czyszczony po
każdej mutacji (6.D41).

## 9. Czego świadomie nie zrobiłem

- **Niczego nie instalowałem** ani nie zmieniałem katalogu cache — „Poza zakresem".
- **Nie tknąłem sondy Blendera** ani wymaganej wersji SDK.
- **Nie zmieniłem kodu wyjścia** przy nieosiągalnym SDK: pozostaje 1, bo pozycja
  wymagana jest nadal niespełniona. Zmiana kodu na 0 byłaby zamieniem tej usterki
  na cichą — narzędzie mówiłoby „w porządku" o środowisku, w którym `dotnet test`
  nie pójdzie.
- **Nie dopisałem `DOTNET_ROOT` do listy zmiennych w `--help`** — jest tam już
  `DOTNET_BIN`, a rozstrzygnięcie, którą zmienną dokument ma polecać jako główną,
  dotyka `docs/23-environment.md` i wykracza poza pole „Wyjście" tej pozycji.

## 10. Zauważone przy okazji, nie tknięte

**Kontrola `godot .NET hostfxr` czyta goły `command -v dotnet`, a nie `$DOTNET_BIN`
ani `$DOTNET`.** Jest to spójne z tym, jak Godot naprawdę szuka runtime'u (opisane
w komentarzu tamtej kontroli), więc **nie jest usterką** — ale sprawia, że doctor
odpowiada „ok" na `dotnet SDK` i „WARN" na `hostfxr` o tym samym SDK, w zależności
od tego, którą zmienną ustawiono. Podpowiedź mówi o tym dziś wprost i to wystarcza;
zgłoszenia osobnej pozycji nie ma, bo nie ma tu nic do naprawienia w kodzie —
rozbieżność jest własnością Godota, nie skryptu.
