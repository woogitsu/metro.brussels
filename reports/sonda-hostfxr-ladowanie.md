# Sonda `godot .NET hostfxr`: z jednego na pięć zepsuć z pięciu (6.D60)

**Zmierzone 09.09.2026 na:** `4c2e7e8`, kontener tej sesji, Godot
`4.7.2.stable.mono.official.ed1daf0bf`, .NET SDK 10.0.401.
**Przyrząd:** sześć cieni instalacji .NET (drzewo symlinków z jednym plikiem
zepsutym, metoda z 6.D24), `bash doctor.sh --no-tests` w każdym z nich,
`ctypes.CDLL` na trzech bibliotekach, `python3 tools/tests/test_all.py`.

---

## 1. Co było zepsute i dlaczego to nie jest kosmetyka

Kontrola `godot .NET hostfxr` brała się z `find "$DOTNET_ROOT/host/fxr" -name`
z nazwą pliku hostfxr — czyli z **obecności pliku o danej nazwie**. 6.D24 zmierzyła,
że przy czterech z pięciu zepsuć, po których Godot pada kodem 134 w 0,19–0,35 s,
ta kontrola mówi `ok`. Sonda meldująca sprawdzenie, którego nie zrobiła, jest gorsza
od braku sondy: brak sondy nie usypia.

## 2. Pomiar PRZED, na dzisiejszym drzewie — powtórzenie 6.D24, nie cytat

Sześć cieni, `DOTNET_ROOT` na cień, `PATH` **bez** `dotnet` (gałąź
`command -v dotnet` zapala kontrolę niezależnie od `DOTNET_ROOT`, więc z nią pomiar
mówiłby o `PATH`, a nie o cieniu; sprawdzone osobno: `command -v dotnet` w tym
`PATH` nie zwraca nic):

```
kontrola             ok    godot .NET hostfxr
hostfxr-brak         WARN  godot .NET hostfxr
hostfxr-obc          ok    godot .NET hostfxr
coreclr-brak         ok    godot .NET hostfxr
coreclr-obc          ok    godot .NET hostfxr
hostpolicy-brak      ok    godot .NET hostfxr
```

Cztery z pięciu na `ok` — liczba 6.D24 odtworzona co do wariantu.

## 3. Wybór kontroli, i dlaczego nie próg

Wpis 6.D60 zostawiał wybór otwarty i wymieniał trzy warianty. Rozstrzyga go pomiar,
nie gust:

- **obecność wszystkich trzech bibliotek** — łapie trzy z pięciu, przepuszcza oba
  obcięcia;
- **próg na nagłówku ELF** — przepuszcza oba obcięcia, bo 200 pierwszych bajtów
  to **poprawny** nagłówek. Próg na rozmiarze trzeba by zgadnąć, a zgadnięta liczba
  w tym projekcie starzeje się po cichu;
- **prawdziwe ładowanie** (`dlopen`) — nie ma progu do zgadnięcia i jest dokładnie
  tą czynnością, na której wywraca się silnik.

Zmierzone `ctypes.CDLL` na trzech bibliotekach w każdym z sześciu cieni:

```
kontrola         hostfxr=ZALADOWANA  hostpolicy=ZALADOWANA  coreclr=ZALADOWANA
hostfxr-brak     hostfxr=BRAK        hostpolicy=ZALADOWANA  coreclr=ZALADOWANA
hostfxr-obc      hostfxr=ODMOWA      hostpolicy=ZALADOWANA  coreclr=ZALADOWANA
coreclr-brak     hostfxr=ZALADOWANA  hostpolicy=ZALADOWANA  coreclr=BRAK
coreclr-obc      hostfxr=ZALADOWANA  hostpolicy=ZALADOWANA  coreclr=ODMOWA
hostpolicy-brak  hostfxr=ZALADOWANA  hostpolicy=BRAK        coreclr=ZALADOWANA
```

Sześć wierszy, sześć różnych odpowiedzi, każda wskazująca **dokładnie** zepsuty plik
i żaden inny. Kontrola stoi w `tools/ci/dotnet_native_probe.py`, bo z osobnego pliku
da się ją wywołać z testu — a kontrola wpisana w `doctor.sh` w jednej linii byłaby
sprawdzalna wyłącznie przez uruchomienie całego doctora.

## 4. Pomiar PO

```
kontrola             ok    godot .NET hostfxr
hostfxr-brak         WARN  ... hostfxr: brak (…/host/fxr/*/libhostfxr.so)
hostfxr-obc          WARN  ... hostfxr: odmowa (…/host/fxr/10.0.12/libhostfxr.so: cannot read file data)
coreclr-brak         WARN  ... coreclr: brak (…/shared/Microsoft.NETCore.App/*/libcoreclr.so)
coreclr-obc          WARN  ... coreclr: odmowa (…/libcoreclr.so: cannot read file data)
hostpolicy-brak      WARN  ... hostpolicy: brak (…/shared/Microsoft.NETCore.App/*/libhostpolicy.so)
```

Pięć z pięciu, a komunikat **nazywa bibliotekę** zamiast kazać „ustawić DOTNET_ROOT",
co przy ustawionym `DOTNET_ROOT` było radą pustą.

**Żaden inny wiersz doctora nie zmienił treści** — i nie jest to zdanie o zamiarze,
tylko wynik porównania pełnego wyjścia `bash doctor.sh --no-tests` przed i po:

```
diff doctor-przed.txt doctor-po.txt
  (bez różnic)
```

## 5. Bramka i kontrola negatywna

`test_the_hostfxr_probe_refuses_every_one_of_the_five_measured_breakages` buduje
sześć atrap i żąda: kontrolna przechodzi, każde z pięciu zepsuć zostaje odrzucone
z nazwą biblioteki. Atrapa **nie potrzebuje prawdziwego .NET** — trzy pliki to kopie
skompilowanego modułu `_ctypes` samego Pythona, czyli prawdziwe biblioteki, które
`dlopen` naprawdę ładuje. To jest wybór, nie skrót: job `tools` w CI .NET-a nie
instaluje, więc bramka wymagająca instalacji byłaby zielona tylko tam, gdzie SDK
akurat stoi.

Parą jest `test_the_probe_catches_what_the_old_presence_check_let_through`: dawna
kontrola, przepisana w teście jeden do jednego, musi na tych samych atrapach
przepuścić **cztery z pięciu**, a nowa **zero**. Bez tej pary pierwsza bramka byłaby
zielona także dla kontroli, która niczego nie poprawiła.

Trzecia, `test_doctor_asks_the_probe_and_not_the_name_of_a_file`, pilnuje, żeby
kontrola nie wróciła do pytania o nazwę pliku — czyta **kod bez komentarzy**,
i to też jest wynik pomiaru: pierwsza wersja tej bramki **zapaliła się na własnym
commicie**, bo komentarz nad kontrolą cytuje dawną postać, żeby było widać, co
zostało przepisane. Bramka czytająca prozę uznała cytat za nawrót. Trzecia asercja
tej bramki żąda teraz, żeby cytat w komentarzu **został** — kod bez zapisu, przed
czym broni, jest gorszy niż kod z zapisem.

## 6. Czego NIE zrobiłem

**Nie uruchomiłem Godota na pięciu cieniach.** Pozycja opiera się na pomiarze 6.D24
(kod 134, 0,19–0,35 s) i wymienia go w polu „Zależy od"; powtórzenie wymagałoby
zbudowania `src/Game`, co jest poza jej zakresem. To, co ta pozycja miała zmierzyć —
zachowanie **sondy** — jest zmierzone w całości.

**Nie tykałem** samego Godota, sposobu, w jaki CI ustawia `DOTNET_ROOT`, ani zapisów
historycznych w `docs/TASKS.md`; wszystkie trzy stoją w polu „Poza zakresem".

## 7. Weryfikacja

```
python3 tools/tests/test_all.py
  -> RAZEM 2092 testów, 111 modułów, kod 0
```
