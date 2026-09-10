# Wersja SDK niepinowana: wzorzec kanału zamiast pinu (6.D79)

**Zmierzone 10.09.2026 na:** `0da6d61`, kontener tej sesji (SDK 10.0.401)
i runner `metro-01` (log joba `sim`, przebieg PR #466).
**Przyrząd:** podstawianie pinu do `global.json` i czytanie **kodu wyjścia**
`dotnet --version`, `python3 tools/tests/test_all.py`, cztery kontrole negatywne
z `md5sum -c` po każdym powrocie.

---

## 1. Co było zepsute

`global.json` nie istniał ani w drzewie, ani w indeksie. Trzy workflowy podawały:

```
.github/workflows/blender-smoke.yml:91     dotnet-version: '10.0.x'
.github/workflows/godot-first-run.yml:127  dotnet-version: '10.0.x'
.github/workflows/sim-tests.yml:76         dotnet-version: '10.0.x'
```

`10.0.x` jest **wzorcem kanału**: instalator rozwiązuje go do najnowszej łatki
**w momencie instalacji**. Bramka wersji sprawdzała wyłącznie numer główny
(`version.startswith("10.")`), `doctor.sh` też (`cut -d. -f1`).

**Gdzie to boli, a gdzie nie.** Na maszynie właściciela SDK przeżywa przebiegi
w cache narzędzi, więc rozjazd **nie** następuje między przebiegami jednej maszyny.
Następuje **między maszynami puli** i po każdym czyszczeniu cache — czyli dokładnie
tam, gdzie nikt na niego nie patrzy.

## 2. Zmierzona wersja, ta sama po obu stronach

```
runner metro-01   dotnet-install: .NET Core SDK with version '10.0.401' is already installed
                  10.0.401 [/home/mateusz/actions-runner-metro-01/_work/_tool/metro-dotnet/sdk]
kontener sesji    10.0.401 [/root/.dotnet/sdk]
```

Pin nie podnosi więc niczego i nie ma podnosić — pole „Poza zakresem" wyklucza
podniesienie wersji SDK.

## 3. Pomiar, który obalił moje własne założenie o `rollForward`

Podstawiony pin, `rollForward: latestPatch`, jedno SDK na dysku (10.0.401), czytany
**kod wyjścia** `dotnet --version`:

```
pin 10.0.401  -> kod 0     stdout: 10.0.401
pin 10.0.402  -> kod 155   stdout: 10.0.401 [/root/.dotnet/sdk]
pin 10.0.301  -> kod 155   stdout: 10.0.401 [/root/.dotnet/sdk]
pin 11.0.100  -> kod 155   stdout: 10.0.401 [/root/.dotnet/sdk]
```

**Dwie rzeczy, obie założone przeze mnie najpierw błędnie i obie poprawione
pomiarem, a nie namysłem:**

1. **`latestPatch` NIE znaczy „każda łatka przejdzie".** Znaczy „ta wersja albo
   wyższa łatka **w tym samym paśmie funkcji**". SDK **starsze** od pinu
   (10.0.301 wobec pinu 10.0.401) jest odrzucane w całości. Pierwsza wersja
   komentarza w `doctor.sh` mówiła „rollForward=latestPatch zbuduje to bez błędu"
   — nieprawda w jedną stronę.
2. **Przy niespełnialnym pinie `dotnet --version` kończy błędem i wypisuje na
   stdout listę zainstalowanych SDK.** Kontrola `chk_required "dotnet SDK"` widzi
   wtedy niezerowy kod i melduje `BRAK dotnet SDK -> zainstaluj .NET SDK 10.0+`,
   a SDK **jest** — nie zgadza się wyłącznie wersja. Co gorsza, następna kontrola
   bierze `cut -d. -f1` z przeciekłej listy i melduje `ok dotnet SDK >= 10`.
   Doctor mówił więc naraz „nie ma" i „jest w porządku".

## 4. Poprawka

```json
{
  "sdk": {
    "version": "10.0.401",
    "rollForward": "latestPatch"
  }
}
```

Trzy `dotnet-version:` przestawione na `10.0.401` — pełną trójkę, nie wzorzec.
`setup-dotnet` z jawnym `dotnet-version` **ignoruje** `global.json`, więc rozjazd
między nimi znaczyłby, że CI instaluje jedno SDK, a `dotnet build` żąda drugiego;
bramka żąda ich równości, a nie tylko zgodności numeru głównego.

`doctor.sh` dostał blok czytający pin **z pliku** (nie drugi raz z ręki) i nazywający
prawdziwą przyczynę w obu przypadkach. Zmierzone na obu gałęziach:

```
$ pin 10.0.401
  ok    dotnet SDK
  ok    dotnet SDK >= 10 (jest 10)
  ok    dotnet SDK == pin z global.json (10.0.401)

$ pin 10.0.402
  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+ (https://dotnet.microsoft.com/download)
  ok    dotnet SDK >= 10 (jest 10)
  WARN  dotnet SDK vs pin z global.json (10.0.402)  -> SDK SĄ na dysku, ale ŻADNE nie
        spełnia pinu; `dotnet --version` kończy błędem, a komunikat wyżej mówi o braku
        SDK i jest w tej sytuacji mylący
        na dysku: 10.0.401 [/root/.dotnet/sdk]
```

Kontrola jest **opcjonalna**, i to jest wybór: wyższa łatka w tym samym paśmie buduje
projekt poprawnie, więc zaczerwienienie byłoby nieprawdą o stanie środowiska — ale
różne łatki na dwóch maszynach puli to dokładnie to, czego pozycja dotyczy, więc warto
je **pokazać**.

## 5. Cztery warunki „Skończone, gdy", cztery osobne asercje, plus kontrola parsera

| warunek | asercja |
|---|---|
| plik pinu istnieje | `test_the_sdk_pin_file_exists` |
| wersja jest pełną trójką (nie wzorcem) | `test_the_pinned_version_is_a_full_triple_and_not_a_channel_pattern` |
| numer główny zgadza się z docelową platformą | `test_the_pinned_major_matches_what_the_projects_target` |
| wszystkie miejsca w workflowach są zgodne | `test_every_workflow_installs_exactly_the_pinned_version` |
| **kontrola parsera** | `test_the_pin_parser_does_not_pass_by_returning_nothing` |

Druga asercja żąda też **jawnej** `rollForward`. Domyślna (`latestPatch`) jest
w pliku niewidoczna, a niewidoczna polityka jest dokładnie tym, przez co wzorzec
kanału przetrwał tak długo.

Kontrola parsera podstawia cztery pliki w `/tmp` i sprawdza, że `pin_sdk()` **nie**
zwraca `None` na wszystkim — bez niej wszystkie cztery warunki wyżej przechodzą przez
pętlę po niczym. Podstawienie jest zdejmowane w `finally`, a ostatni wiersz sprawdza,
że przyrząd znów widzi prawdziwy pin: wyciek podstawienia uciszyłby cztery bramki na
resztę przebiegu.

## 6. Cztery kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | pin wraca na `10.0.x` | **czerwona** 33/36 — trzy bramki, w tym rozjazd z workflowami |
| KN-2 | pin bez `rollForward` | **czerwona** 35/36 — „niewidoczna polityka" |
| KN-3 | pliku pinu nie ma | **czerwona** 31/36 — pięć bramek |
| KN-4 | jeden workflow wraca na `10.0.x` | **czerwona** 35/36 — nazywa `sim-tests.yml` i obie wartości |

**KN-3 wykryła słabość moich własnych komunikatów i to jest jej wynik.** Pierwsza
wersja trzech bramek padała przy braku pliku na
`'NoneType' object has no attribute 'get'` — czyli mówiła o Pythonie zamiast o tym,
czego brakuje. Po dopisaniu `_pin_sdk_lub_stop()` ta sama mutacja daje pięć zdań
o pinie; jedno z nich jest wciąż tylko diagnostyczne
(`test_the_pin_parser…` — „po przywróceniu przyrząd nie widzi prawdziwego pinu"),
i tak ma być, bo ta bramka mówi o przyrządzie, a nie o drzewie.

## 7. Czego NIE zrobiłem

**Nie podniosłem wersji SDK** ani **nie zmieniłem docelowej platformy projektów** —
oba stoją w polu „Poza zakresem". Pin podaje 10.0.401, czyli to, co JEST na runnerze
i w kontenerze.
**Nie zdjąłem `dotnet-version` z workflowów** na rzecz samego `global.json`, choć
`setup-dotnet` bez tego wejścia potrafi czytać pin: dałoby to jedno miejsce mniej, ale
zmieniłoby zachowanie kroku instalacji na sposób, którego w tym kontenerze nie mam jak
zmierzyć. Pole „Skończone, gdy" żąda **zgodności** miejsc, a nie ich likwidacji.
**Nie tknąłem `chk_required "dotnet SDK"`**, choć pomiar §3 pokazuje, że przy
niespełnialnym pinie mówi ono nieprawdę o przyczynie. Poprawka tamtej kontroli jest
zmianą w zachowaniu doctora poza tą pozycją; nowy blok **nazywa** tę sytuację
i mówi wprost, że komunikat wyżej jest wtedy mylący.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_dotnet_version.py
  -> 36/36 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 94,053 s, 2141 testów, 113 modułów, kod 0

DOTNET_ROOT=$HOME/.dotnet bash doctor.sh
  -> ok dotnet SDK == pin z global.json (10.0.401)
```

Zestaw urósł z **2136** do **2141** testów; modułów bez zmiany.
