# Test, który zakładał środowisko, zamiast je zagwarantować

**Zmierzone 09.09.2026 na:** `f0c8fc7`, kontener tej sesji oraz log runnera
`actions-runner-metro-03` z przebiegu bramki `tools`.
**Przyrząd:** `tools/tests/test_dotnet_version.py`, `doctor.sh`,
`python3 tools/tests/test_all.py`.

---

## Objaw

Po wymianie puli runnerów 09.09.2026 bramka `tools` zrobiła się czerwona
na `main` i na gałęzi `claude/6b43-prog-odsloniecia-chase`, choć żaden z tych
commitów nie tykał ani `doctor.sh`, ani testów SDK. Wyjście z runnera:

```
FAIL test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku: doctor melduje brak SDK, choć leży ono na dysku
FAIL test_doctor_bez_dotnet_w_PATH_i_bez_sdk_na_dysku_nadal_kaze_instalowac
  2057/2059 przeszło
```

W kontenerze tej sesji te same dwa testy przechodziły. Różnica nie była
w kodzie, tylko w maszynie.

## Przyczyna

Oba testy nazywają w swojej nazwie scenariusz „bez `dotnet` w `PATH`",
a wchodziły w niego przez podstawienie `PATH="/usr/bin:/bin"`. To nie jest
gwarancja scenariusza, tylko **założenie o zawartości `/usr/bin`** — prawdziwe
na starej puli i w kontenerze sesji, fałszywe na runnerach dodanych
09.09.2026, gdzie `/usr/bin/dotnet` istnieje i jest SDK w wersji 8.

Wobec takiego `PATH` `doctor.sh` szedł więc **inną gałęzią** niż ta, o której
mówi nazwa testu — gałęzią „SDK jest, ale za stare". Jego wyjście na runnerze:

```
ok   dotnet SDK
BRAK dotnet SDK >= 10 (jest 8)
na dysku JEST nowsze SDK: /tmp/.../home/.dotnet/dotnet
```

Test nie wykrył, że bada coś innego, bo nic tego nie sprawdzało. To ta sama
rodzina co bramki tropione w tej sesji od 6.D27: **przyrząd zepsuty
w kierunku „wszystko w porządku"** — z tą różnicą, że tu psuła go maszyna,
a nie treść drzewa.

## Poprawka

Zamiast zakładać, że gdzieś w `PATH` nie ma `dotnet`, test teraz **buduje**
środowisko, w którym go nie ma: katalog `bin` w katalogu tymczasowym
z symlinkami do wszystkiego, co widać w `PATH`, poza samą nazwą `dotnet`
(`_bin_bez_dotnet`). Po zbudowaniu stoi asercja, która **dowodzi
scenariusza**:

```python
assert shutil.which("dotnet", path=sciezka_bez_dotnet) is None, (...)
```

Bez niej maszyna z `dotnet` w miejscu, którego odsianie nie objęło, po cichu
zamieniłaby ten test na test innej gałęzi — czyli dokładnie tak, jak padł on
dzisiaj. Bramka nie została osłabiona: sprawdza teraz o jedno zdanie więcej
niż przed poprawką.

Pierwsze podejście do poprawki było inne — odsiewało z `PATH` te katalogi,
które zawierają `dotnet`. Padło od razu, bo razem z `/usr/bin` zabierało
`bash`, `git` i `python3`:

```
FAIL test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku: [Errno 2] No such file or directory: 'bash'
```

Symlinki są odpowiedzią na to: odsiewają **nazwę**, nie katalog.

## Weryfikacja

Warunek runnera odtworzony atrapą `/usr/bin/dotnet`, która melduje `8.0.404`.
Moduł, oba warianty:

```
═══ z atrapą (warunek runnera):
  28/28 przeszło
═══ bez atrapy (kontener sesji):
  28/28 przeszło
```

Kontrola negatywna — stary `PATH="/usr/bin:/bin"` przy tej samej atrapie
odtwarza awarię CI co do testu:

```
  FAIL test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku: …
  FAIL test_doctor_bez_dotnet_w_PATH_i_bez_sdk_na_dysku_nadal_kaze_instalowac: …
  26/28 przeszło
```

Atrapa zdjęta po pomiarze. Cały zestaw:

```
  RAZEM 108.621 s, 2059 testów, 109 modułów
kod=0
```

## Czego świadomie nie zrobiono

`doctor.sh` nie został tknięty. Zachowanie, które testy opisują, jest
poprawne — wadliwy był sposób wchodzenia w scenariusz, nie skrypt.

Nie dopisano wyjątku ani listy „maszyn, na których ten test się pomija".
Test, który pomija się na maszynie, jest zepsuty w tym samym kierunku co ten,
który zakłada maszynę.

## Co zauważone przy okazji, nie tknięte

`CLAUDE.md` §9 nadal opisuje selektor złożony z sześciu etykiet — do czterech
ogólnych dokłada dwie sprzętowe, nazwane tam wprost — a wszystkie
przebiegi w `.github/workflows/` chodzą już na gołym `self-hosted` po decyzji
właściciela z 09.09.2026. `tools/tests/test_ci_workflows.py` został wtedy
przekierowany na nowy stan, więc bramka i drzewo się zgadzają — nie zgadza się
z nimi konstytucja. To dokument właściciela i nie jest ruszany z tej gałęzi.
