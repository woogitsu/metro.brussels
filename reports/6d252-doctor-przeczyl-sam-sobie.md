# 6.D252 — doctor przeczył sam sobie w jednym przebiegu

**Data:** 17.09.2026 · **Gałąź:** `claude/6d252-sonda-path` · **Baza:** `abc4e59`

## 1. Usterka jest inna, niż opisywała pozycja — i ostrzejsza

Pozycja zakładała, że `doctor.sh` **nie umie znaleźć** SDK poza `PATH`. Przebieg przed
łatką pokazuje coś innego: **znajduje je i nazywa co do ścieżki i wersji**, a mimo to
cztery wiersze niżej melduje brak.

```
  BRAK  dotnet SDK  -> SDK JEST na dysku: /root/.dotnet/dotnet (wersja 10.0.401) …
  …
Testy rdzenia symulacji:
  pomijam — brak dotnet
```

**Jeden przebieg, dwa wiersze, sprzeczne ze sobą.** To nie jest ślepota sondy — to
sonda, która wie, i gałąź decyzyjna, która i tak pyta o co innego.

## 2. Co pytała gałąź

```sh
if ! command -v "${DOTNET_BIN:-dotnet}" >/dev/null 2>&1; then
  echo "  pomijam — brak dotnet"
```

Pytanie brzmiało „czy `dotnet` jest w `PATH`", a odpowiedź trafiała do zdania „czy jest
czym uruchomić testy". `SDK_NA_DYSKU` — zmienna niosąca działającą ścieżkę, wypisywaną
przez doctora w podpowiedzi dziesięć wierszy wyżej — nie brała w tej decyzji udziału.

To jest ta sama rodzina, którą `CLAUDE.md` §9 nazwał przy Blenderze: *„Sonda na obecność
byłaby tu wręcz szkodliwa"*. Tam kosztowała niewłaściwy silnik renderujący; tu kosztuje
połowę pętli weryfikacji z §5.

## 3. Dlaczego to nie jest kosmetyka — dowód z tej samej sesji

§5 czyni `dotnet test tests/Sim.Tests` obowiązkową częścią pętli. §8 mówi, że
zatrzymanie się jest poprawnym wynikiem pracy. Wiersz „pomijam — brak dotnet" **wygląda
jak to drugie, a jest pominięciem tego pierwszego**.

Przeczytałem go i uwierzyłem mu **cztery razy w jednej sesji** — w dwóch treściach
commitów i dwóch opisach PR napisałem, że w tym środowisku nie ma `dotnet`. Wiersz
z prawdziwą ścieżką stał wtedy wyżej w tym samym wyjściu, którego nie doczytałem.
Fałszywy brak jest gorszy od prawdziwego, bo produkuje **uzasadnienia dla niewykonanej
weryfikacji**.

## 4. Poprawka: runner rozstrzygnięty PRZED gałęzią

```sh
if command -v "${DOTNET_BIN:-dotnet}" >/dev/null 2>&1; then
  DOTNET_DO_TESTOW="${DOTNET_BIN:-dotnet}"
else
  DOTNET_DO_TESTOW="$SDK_NA_DYSKU"
fi

if [ -z "$DOTNET_DO_TESTOW" ]; then
  echo "  pomijam — brak dotnet"
```

Sonda pyta dziś o **zdolność**: czy jest czym uruchomić. Gdy nie ma ani binarki
w `PATH`, ani SDK na dysku, komunikat „brak dotnet" zostaje — bo wtedy jest prawdziwy.

Po łatce, ten sam kontener:

```
Testy rdzenia symulacji:
  ok    673/673 przeszło
```

**Wiersz `BRAK dotnet SDK` ZOSTAJE i to jest wybór, nie przeoczenie.** Mówi o czym
innym: że `DOTNET_ROOT` i `PATH` nie są ustawione, co nadal ma znaczenie dla `hostfxr`
Godota — komentarz przy tej podpowiedzi opisuje pomiar, w którym samo `DOTNET_BIN`
zdejmowało jeden komunikat i zostawiało `WARN godot .NET hostfxr`. Zdanie „środowisko
nie jest przygotowane" jest prawdziwe; fałszywe było wyłącznie „nie ma czym uruchomić
testów".

## 5. Ile sond pyta o `PATH` — liczba, której żądało pole „Wyjście"

W `doctor.sh` stoi dziś **osiem** wystąpień `command -v`, z czego **cztery są
komentarzami**. Prawdziwych sond są **cztery**:

| wiersz | o co pyta | czy `PATH` jest właściwym pytaniem |
|---|---|---|
| 115 | czy kandydat to ten sam plik, co już na `PATH` | **tak** — porównuje tożsamość, żeby nie zgłosić tego samego SDK dwa razy |
| 369 | czy `dotnet` jest osiągalny dla **Godota** | **tak** — odwzorowuje lookup silnika, który sam chodzi po `PATH` |
| 370 | gdzie leży `hostfxr` | **tak** — jak wyżej |
| 508 | czym uruchomić testy rdzenia | **NIE** — i to była ta usterka |

**Po tej poprawce żadna sonda w `doctor.sh` nie zamienia braku w `PATH` na werdykt
„narzędzia nie ma".** Trzy pozostałe pytają o `PATH`, bo `PATH` jest tam przedmiotem
pytania, a nie zastępnikiem innego.

## 6. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Baza: **49/49** przed dopisaniem testów, **51/51** po.

| mutacja | przewidziane | zmierzone |
|---|---|---|
| KN-1 gałąź cofnięta do sondy `PATH` | czerwone, nowy test | **47/51 — CZTERY**, i to nie z powodu, który przewidziałem |
| KN-1b kotwica ZOSTAJE, znika sam fallback na `SDK_NA_DYSKU` | czerwone, dokładnie nowy test | **50/51 — dokładnie jeden** |
| KN-2 **kontrola negatywna wbudowana**: ani binarki, ani SDK na dysku | „brak dotnet" ZOSTAJE | **zielone**, komunikat obecny |

**KN-1 obaliło własne przewidywanie i dlatego jest tu wypisane, a nie zastąpione przez
KN-1b.** Cofnięcie gałęzi zmienia też **kotwicę** `DECISION_OPEN`, po której bramka
wycina fragment doctora do uruchomienia — więc padły cztery testy, z czego trzy na
asercji „nie znalazłem początku gałęzi decyzyjnej", a nie na zachowaniu. To dowodzi,
że strażnik kotwicy działa, **ale nie dowodzi, że poprawka jest nośna**. Dopiero KN-1b,
które kotwicę zostawia w miejscu i zabiera wyłącznie fallback, izoluje zachowanie:
jedna czerwień, ta właściwa.

Kontrola negatywna z pola „Weryfikacja" pozycji jest **testem stałym**, a nie
jednorazową mutacją: `test_doctor_NADAL_melduje_brak_gdy_nie_ma_ANI_JEDNEGO_dotneta`
pilnuje, żeby poprawka nie zamieniła sondy w atrapę zawsze mówiącą „jest". Bez niej
usunięcie całej gałęzi „brak dotnet" przechodziłoby na zielono.

## 7. Pomocnik testowy — i błąd, który sam w siebie wdepnąłem

Istniejący `_run_decision` zawsze podaje `DOTNET_BIN` wskazujący na atrapę, więc sonda
`command -v` **zawsze się udaje** i gałąź „nie ma czym uruchomić" nie zachodzi tam ani
razu. Usterka 6.D252 żyła dokładnie w gałęzi, której tamten pomocnik nie umie osiągnąć —
stąd `_run_decision_bez_path`.

Jego pierwsza wersja zerowała `PATH`. **Zmierzone, nie przewidziane:** bez `PATH` znikają
`grep`, `cut` i `tail`, których doctor używa do odczytania liczby testów z logu, więc
wypisywał `ok    / przeszło` — puste liczby. Test mierzyłby wtedy brak coreutils, a nie
gałąź decyzyjną. Dziś `PATH` zostaje prawdziwy, a nieosiągalna jest sama **nazwa** binarki.

## 8. Czego NIE zrobiono

- **Nie instalowano niczego** i nie ruszano wersji SDK — pole „Poza zakresem".
- **Nie przepisywano `docs/23-environment.md`** — to jest 6.D169.
- **Nie ruszano trzech pozostałych sond** (115, 369, 370): pytają o `PATH`, bo `PATH`
  jest tam przedmiotem pytania. Zmiana którejkolwiek zepsułaby kontrolę `hostfxr`,
  której komentarz opisuje awarię objawiającą się kodem 134.

## 9. Co zauważone przy okazji, nietknięte

- **Komentarz w `doctor.sh` powołuje się na bramkę, której NIE MA.** Wiersz 103 mówi
  „pilnuje tego dziś" i nazywa moduł **test_doctor_dotnet** — takiego pliku w drzewie
  nie ma; `ls tools/tests/ | grep doctor` daje `test_doctor_queue_claim.py`
  i `test_doctor_test_log.py`, a sprawy `dotnet` pilnuje `test_dotnet_version.py`.
  Zdanie o tym, co pilnuje bramka, samo nie jest pilnowane przez nic — dokładnie klasa
  z 6.D255. Nie tknięte, bo poprawienie nazwy w komentarzu bez sprawdzenia, czy tamta
  bramka kiedykolwiek istniała, byłoby zgadywaniem.

  **Nazwa stoi wyżej BEZ rozszerzenia i to nie jest niechlujstwo — to wymuszone przez
  bramkę, o której ten punkt mówi.** `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje
  _sie_w_drzewie` odrzuca raport wymieniający plik, którego w drzewie nie ma, i odrzuciła
  ten raport przy pierwszym przebiegu. Raport opisujący nieistniejący plik nie może go
  nazwać w kształcie ścieżki — co jest samo w sobie potwierdzeniem, że bramka działa,
  i drobną ceną: o takim znalezisku da się pisać tylko opisowo.
