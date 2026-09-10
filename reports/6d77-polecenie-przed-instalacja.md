# Narzędzie wołane osiem kroków przed krokiem, który je zapewnia (6.D77)

**Zmierzone 10.09.2026 na:** `deb38f2`, kontener tej sesji.
**Przyrząd:** przejście po dziesięciu workflowach z `yaml.safe_load`,
`python3 tools/tests/test_all.py`, cztery kontrole negatywne z `md5sum -c`
po każdym powrocie.

---

## 1. Co dokładnie było zepsute

`.github/workflows/godot-first-run.yml`, indeksy kroków przed poprawką:

```
 6  Download Godot mono            -> bash tools/ci/godot_install.sh  (curl, unzip)
14  Install render libraries       -> bash tools/ci/apt_install.sh --set blender-xvfb
```

Osiem kroków różnicy. Polecenia nie stoją w `run:` kroku wcale — są w skrypcie,
i to jest powód, dla którego dotąd nikt tego nie zobaczył.

**To nie jest „zepsułoby się, gdyby".** Ta droga odpaliła się już raz, 07.09.2026,
jako `unzip: command not found` — kod 127, run 34155630333. Naprawiono wtedy
**sam brak pakietu** (dopisano `unzip` do zestawu i do sondy), a kolejność została.
Warunek powrotu jest w tym projekcie rutyną, nie hipotezą: świeża maszyna puli albo
nowy pin wersji silnika, bo wersja jest częścią ścieżki katalogu, więc nowy pin
zawsze wymusza pobranie.

## 2. `curl` nie był ani sondowany, ani w żadnym zestawie apt

Wołają go **oba** instalatory:

```
tools/ci/blender_install.sh:152   curl -fL --retry 4 ... -o "$TARBALL" "$URL"
tools/ci/godot_install.sh:107     curl -fL --retry 4 ... -o "$ZIP" "$URL"
```

Działał wyłącznie dlatego, że maszyny puli mają go z innych powodów — dokładnie ta
sama sytuacja, w której `unzip` doszedł do kodu 127 dwa dni wcześniej. Dopisany do
**obu** zestawów naraz, więc różnica między nimi zostaje ta sama (`xvfb`, `unzip`),
i do `commands:` wszystkich siedmiu sond.

Wpis `"curl": "curl"` w `POLECENIA_Z_PAKIETOW` jest **tożsamościowy** i to go nie
czyni zbędnym: bez niego bramka kolejności nie ma czego pilnować dla `curl`.

## 3. Pomiar przed poprawką: jeden winowajca na dziesięć workflowów

Przejście po wszystkich workflowach, z wchodzeniem w skrypty wołane przez `bash`:

```
blender-smoke.yml       sonda=[]                  instalacja=6   złe: brak
godot-first-run.yml     sonda=[unzip, xvfb-run]   instalacja=14  złe: (6, 'Download Godot mono', [curl, unzip])
m7-shell.yml            sonda=[]                  instalacja=4   złe: brak
material-style-smoke    sonda=[]                  instalacja=4   złe: brak
station-details.yml     sonda=[]                  instalacja=4   złe: brak
tunnel-alignment.yml    sonda=[]                  instalacja=4   złe: brak
visual-regression.yml   sonda=[]                  instalacja=4   złe: brak
```

Sześć pozostałych jest w porządku **przypadkiem, nie z zasady**: wołają
`blender_install.sh` (czyli `curl`) dopiero po instalacji, bo tak wypadła kolejność
kroków, a nie dlatego, że ktoś jej pilnował. Od tej pozycji pilnuje jej bramka.

## 4. Poprawka: para kroków przed pobieraniem silnika

Sonda, cache i instalacja przesunięte przed `Download Godot mono`. Indeksy po:

```
 5  Czy Godot już jest
 6  Czy biblioteki systemowe renderu już są      (sonda: curl xvfb-run unzip)
 7  Cache pakietów apt
 8  Install render libraries
 9  Download Godot mono
```

Koszt jest zerowy, bo instalacja jest bramkowana sondą (`libs == 'missing'`):
przesunięcie zmienia kolejność, nie liczbę wywołań `apt-get`.

## 5. Bramka liczy INDEKSY i wchodzi w skrypty

`test_ci_no_step_uses_a_packaged_command_before_installing_it`. Kształt wzięty
z istniejącej `test_ci_no_workflow_uses_blender_before_installing_it` (dla
`$BLENDER_BIN`), z jedną różnicą, która jest tu całą treścią: bramka czyta także
**skrypty, które krok uruchamia**. Bez tego byłaby ślepa dokładnie na przypadek, dla
którego powstała — `Download Godot mono` ma w `run:` wyłącznie
`bash tools/ci/godot_install.sh`.

Kontrola przyrządu żąda, żeby workflowów z instalacją było siedem i żeby w każdym
z nich **było co mierzyć** (co najmniej jedno polecenie z tabeli). Bez tego wiersza
usunięcie instalacji ze wszystkich workflowów zostawiłoby bramkę zieloną.

## 6. Bramka sumy kontrolnej PRZEPISANA, bo dopisanie `curl` do sond ją zapaliło

`test_every_place_that_downloads_a_tool_checks_its_checksum` (6.D68) brała **surowy
tekst pliku**, więc liczyła każde wystąpienie napisu `curl` jako pobranie — także
w `with: commands: curl`, czyli w NAZWIE polecenia, o które pyta sonda. Dopisanie
`curl` do siedmiu sond zapaliło ją w siedmiu workflowach naraz, z których żaden
niczego nie pobiera.

Zawężenie do ciał `run:` (zbieranych z dokumentu YAML na dowolnej głębokości,
w jobach i w akcjach złożonych) sprawdza **więcej, nie mniej**: dane wejściowe akcji
przestają udawać kod, a każde prawdziwe `curl` w `run:` nadal wchodzi. Kontrola
negatywna dostała parę na ten zmierzony przypadek: `commands: curl` w `with:` nie
jest pobraniem, `curl` w `run:` jest.

## 7. Cztery kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | sonda i instalacja wracają na indeks 14 | **czerwona** 71/72, nazywa plik, krok 6 i granicę 14 |
| KN-2 | bramka przestaje czytać skrypty | **czerwona** 70/72 — zmierzony przypadek znika, a kontrola przyrządu mówi „trywialnie zielona" |
| KN-3 | `curl` znika z zestawu apt, zostaje w sondzie | **czerwona** 71/72 — „sonda pyta o `curl`, a zestaw apt tego nie instaluje" |
| KN-4 | bramka sumy wraca na surowy tekst pliku | **czerwona** 71/72 — siedem workflowów zgłoszonych fałszywie |

KN-2 zapala **dwie** bramki naraz i to jest jej wynik: kontrola negatywna traci
zmierzony przypadek, a kontrola przyrządu nazywa powód — bez czytania skryptów
sześć z siedmiu workflowów nie wołałoby ani jednego polecenia z tabeli.

## 8. Czego NIE zrobiłem

**Nie podniosłem wersji silnika** i **nie zmieniłem sposobu pobierania Blendera** —
oba stoją w polu „Poza zakresem".
**Nie ruszyłem sześciu pozostałych workflowów** poza dopisaniem `curl` do sondy:
ich kolejność jest już poprawna, a bramka teraz tego pilnuje.
**Nie zweryfikowałem tego przebiegiem na świeżej maszynie** — na dzisiejszej puli
`curl` i `unzip` są obecne, więc sonda mówi `present`, instalacja się nie odpala
i różnicy nie widać z logu. Dowodem jest tu kolejność w pliku i bramka, a nie
przebieg; tak samo, jak przy `unzip` 07.09.2026 dowodem był kod 127, a nie zielony job.

## 9. Weryfikacja

```
python3 tools/tests/test_all.py test_ci_workflows.py
  -> 72/72 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 94,414 s, 2133 testów, 113 modułów, kod 0

yaml.safe_load po dziesięciu workflowach: wszystkie parsują się
```

Zestaw urósł z **2130** do **2133** testów; modułów bez zmiany.
