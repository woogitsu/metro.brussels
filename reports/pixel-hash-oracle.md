# Wzorcem klatki jest suma pikseli, nie suma pliku

**Zmierzone 06.09.2026 na commicie:** `4516a13`

Blender 5.2.1 LTS (wersja z pinu `tools/ci/blender-version.txt`), scena testowa
`box_double` z osi testowej, zestaw kamer `infrastructure`, pięć klatek.

## 1. Co było nie tak

`tools/visual/capture_blender.py` wpisywał do manifestu zrzutów sumę SHA-256
**całego pliku** PNG. Narzędzie liczące sumę samych pikseli — `idat_sha256`
w `tools/ci/png_pixels_sha256.py` — istniało z czterema testami i **nie było wołane
z żadnego workflowu ani skryptu**; jedyne odwołanie w drzewie pochodziło z jego
własnego testu.

Narzędzie napisane i nieużyte jest tym samym rodzajem rzeczy co bramka, która nigdy
nie zaświeciła.

## 2. Pomiar: dwa przebiegi tej samej sceny

Ten sam GLB, te same kamery, ten sam Blender, dwa przebiegi pod rząd.

| klatka | suma PLIKU a | suma PLIKU b | zgodne | suma IDAT a | suma IDAT b | zgodne |
|---|---|---|---|---|---|---|
| `inside` | `9f7fd0b2` | `d0a7a392` | **nie** | `1f7ea415` | `1f7ea415` | **tak** |
| `iso` | `030bd38f` | `3f824f2a` | **nie** | `f1cf9dae` | `f1cf9dae` | **tak** |
| `section` | `b9cdb7bf` | `cbe789ee` | **nie** | `49a4ebe3` | `49a4ebe3` | **tak** |
| `side` | `6823015f` | `9358c373` | **nie** | `cc8ecad8` | `cc8ecad8` | **tak** |
| `top` | `83741e3e` | `945a71d3` | **nie** | `807a3cb0` | `807a3cb0` | **tak** |

**Pięć klatek na pięć: suma pliku różna, suma `IDAT` identyczna.**

## 3. Co dokładnie się różni

Rozbiór klatki `iso` na chunki, przebieg a wobec przebiegu b:

```
  IHDR / sRGB / gAMA / cHRM / eXIf / oFFs / pHYs        identyczne
  tEXt  'File\x00<untitled>'                            identyczne
  tEXt  'Date\x002026/09/06 09:52:07'   ->  '09:52:50'  RÓŻNE
  tEXt  'Time\x0000:00:00:01'                           identyczne
  tEXt  'Frame\x00001'                                  identyczne
  tEXt  'Camera\x00cam_iso'                             identyczne
  tEXt  'Scene\x00Scene'                                identyczne
  tEXt  'RenderTime\x0000:29.17'        ->  '00:14.73'  RÓŻNE
  IDAT  8192 B / IDAT 8192 B / IDAT 4652 B              identyczne
  IEND                                                  identyczne
```

**Z osiemnastu chunków różnią się dokładnie dwa**, oba `tEXt`: `Date` i `RenderTime`.
Wszystkie trzy chunki `IDAT` są identyczne co do bajtu. Suma pliku nie mierzy więc
obrazu — mierzy **godzinę, o której render się skończył**.

## 4. Co z tego wynika dla bramki determinizmu

`tools/ci/visual_smoke.sh` ma test „determinizm: przebieg B względem przebiegu A
musi przejść". Do dziś ten test pytał **wyłącznie o progi** — `MAE`, percentyl 95
i `SSIM` — czyli „czy klatka jest DOSTATECZNIE podobna".

Przy identycznym wejściu to jest pytanie za słabe. Różnica jednego kanału jednego
piksela mieści się w progach z manifestu i **przechodziła tędy po cichu**. Test
nazywał się determinizmem, a mierzył podobieństwo.

Od tej pory ten jeden test żąda `--require-identical-pixels`: zgodności **co do bajtu**,
liczonej na sumie `IDAT`. Progi zostają nietknięte i zostają właściwym kryterium
wszędzie tam, gdzie porównuje się klatkę z baselinem po zmianie sceny — pozycja
zmienia **wyrocznię tam, gdzie się o nią prosi**, a nie kryterium wszystkich porównań.

Manifest zrzutów niesie **obie** sumy, nie jedną zamiast drugiej:

| suma | co identyfikuje | do czego się nadaje |
|---|---|---|
| całego pliku (`sha256`) | **artefakt** | „to jest dokładnie ten plik z tamtego przebiegu" |
| samych pikseli (`idat_sha256`) | **obraz** | wyrocznia determinizmu renderu |

`idat_sha256` jest w obu miejscach **wołane**, a nie przepisane: dwie implementacje
jednej wyroczni to jedna z nich niesprawdzona przez testy drugiej. Pilnuje tego
`test_narzedzie_sumy_pikseli_jest_wolane_a_nie_przepisane`.

## 5. Kontrole negatywne — wykonane

### 5.1 Jeden piksel zapala bramkę, choć progi go przepuszczają

To jest cała wartość tej pozycji, więc ma osobny test z **kontrolą założenia** w środku:

```
test_jeden_inny_piksel_zapala_bramke_mimo_ze_progi_go_przepuszczaja
  1. bez --require-identical-pixels:  status "pass",  checks.regression = True
     (kontrola założenia — gdyby ta różnica NIE przechodziła przez progi,
      punkt 2 nie dowodziłby niczego)
  2. z    --require-identical-pixels:  status "fail", checks.identical_pixels = False
     reason: „piksele różnią się co do bajtu: IDAT ... — przy identycznym wejściu
              to jest regres determinizmu, nawet gdy metryki mieszczą się w progach"
```

### 5.2 Ten sam obraz z innym stemplem czasu przechodzi

Odwrotna strona tej samej własności: gdyby wyrocznią została suma pliku, ta para
zapaliłaby bramkę przy każdym przebiegu i bramka zostałaby wyłączona w tydzień.

```
test_te_same_piksele_z_innym_tEXt_sa_zgodne_co_do_bajtu
  pliki różne (asercja w teście), suma IDAT identyczna, status "pass"
```

### 5.3 Kontrola w samym skrypcie CI

`visual_smoke.sh` dostał krok **2b/5**: kopia przebiegu B z **jednym zmienionym
kanałem jednego piksela** (podmiana w strumieniu `IDAT`, bez ruszania niczego innego —
przepisanie obrazu przez `pngio` zmieniłoby przy okazji kompresję i filtry, więc
różnica przestałaby być jednym pikselem). Krok wymaga, żeby porównanie **odmówiło**,
i sprawdza, że odmówiło **z powodu pikseli**, a nie z jakiegokolwiek innego.

### 5.4 Brak baseline'u nadal nie jest sukcesem

`test_zadanie_zgodnosci_nie_wskrzesza_porownania_bez_baselinu`: żądanie zgodności
co do bajtu nie ma prawa obejść statusu `new-baseline`.

## 6. Testy

`tools/tests/test_visual_identical_pixels.py` — **9 testów**. Nie wołają Blendera:
PNG-i budowane są z bajtów, bo bramka ma się dać sprawdzić na maszynie, na której
`doctor.sh` przepuszcza brak Blendera jako „pomijam".

Progi w testach brane są **z manifestu kamer**, nie wpisane z ręki — bramka sprawdzana
na progach innych niż produkcyjne odpowiadałaby na inne pytanie niż to, które zadaje CI.
Zdjęte są wyłącznie progi „pustej klatki", bo testowy PNG 2×1 nie ma jak ich spełnić,
a ta pozycja nie dotyczy wykrywania pustej klatki.

## 7. Czego świadomie nie zrobiłem

- **Nie ruszałem progów tolerancji** — pole „Poza zakresem" zabrania, a §4 tłumaczy,
  dlaczego progi nadal są właściwym kryterium tam, gdzie porównuje się różne sceny.
- **Nie zamieniłem sumy pliku na sumę pikseli.** Obie liczby mówią co innego i obie
  zostają w manifeście.
- **Nie rozszerzyłem żądania zgodności co do bajtu na porównania z baselinem
  wizualnym.** Baseline zmienia się celowo przy zmianie sceny; tam „co do bajtu"
  znaczyłoby „nigdy nie wolno nic zmienić".
