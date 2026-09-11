# 6.D120 — rzędne wchodzą do sceny, a granica wiedzy okazała się nieprzemiatalna

**Zmierzone 11.09.2026 na:** `4b00e35`, kontener tej sesji.
**Przyrząd:** `tools/track/apply_vertical.py` (nowy), `tools/track/vertical_profile.py`,
`tools/blender/tunnel_manifest.py` (`variant_plan`), `tools/blender/tunnel_sweep.py`,
`tools/tests/test_vertical_profile.py`, `tools/tests/test_tunnel_manifest.py`;
`data/track/L1_A.json` i `data/network/station-depths.csv` — wyłącznie do odczytu,
wynik idzie do `build/`.

---

## 1. Stan wyjściowy

`vertical_profile.py` liczy rzędne od 07.09.2026 i **nikt ich nie oglądał**: sześć osi
w `data/track/` ma `vertical.status = not_modelled`, wszystkie punkty mają Z = 0,
a `variant_plan` odrzuca `production`. Pomiar istniał i nie wchodził do geometrii wcale.

Dla pakietu A: **32 punkty z 447** mają rzędną, na odcinku Parc↔Arts-Loi,
**468,4 m z 6686,4 m** osi (7,01 %).

## 2. Główny wynik: uskoku NIE DA SIĘ zamieść, i to jest zmierzone

Pole „Wyjście" prosi o tunel z niezerowym Z na odcinku znanym i płaski poza nim,
z granicą **niewygładzoną**. Zbudowałem dokładnie taką oś — Z z rejestru tam, gdzie jest,
zero poza nim — i puściłem generator. Odpowiedział odmową **własnej bramki
geometrycznej**:

```
BŁĄD: skręt ramki 56.62 st.
[RAPORT] ... skret_ramki=56.6197 st.
```

przy progu `MAX_TWIST_DEG` równym **5,0**. Powód jest arytmetyczny: uskok wynosi
**19,721 m** na jednym kroku kilometrażu (~15 m), więc ramka Freneta obraca się między
dwoma pierścieniami o kilkadziesiąt stopni i siatka wychodzi skręcona.

Zostają trzy drogi i dwie są zamknięte:

| droga | dlaczego odpada albo zostaje |
|---|---|
| wygładzić uskok | zabrania tego pole „Poza zakresem" i cała reguła `vertical_profile.py`: wygładzenie twierdzi, że znamy spadek prowadzący do odcinka znanego |
| podnieść próg skrętu | to wyłączenie bramki, nie naprawa (6.D27) |
| **nie zamiatać przez granicę** | scena kończy się tam, gdzie kończy się wiedza; obie granice zostają w metadanych z powodem |

Wybrana jest trzecia. `apply_vertical.py --span known` przycina oś do samego odcinka
ze rzędnymi i zapisuje w `vertical.cropped` powód przycięcia razem z liczbą stopni
i progiem — żeby nikt nie musiał tego odkrywać drugi raz.

## 3. Po przycięciu generator przechodzi

```
[RAPORT] plik=build/L1_A_partial_vertical.glb wariant=partial-vertical
[RAPORT] profil=box_double (9.40 x 5.90 m) punkty_osi=32 pierscienie=95
[RAPORT] dlugosc_osi=468.47 m (zrodlo 468.45 m, wygladzenie 0.1363 m)
[RAPORT] chunki=1 suma=468.469 m max_szczelina=0.000 mm stacje_przeciete=0
[RAPORT] normalne_na_zewnatrz=0 zdegenerowane=0 nieskonczone=0 skret_ramki=1.0925 st.
[RAPORT] bbox_m: X=454.0 Y=90.7 Z=13.7
[RAPORT] kontrole geometryczne: OK
```

Skręt ramki spadł z **56,62°** na **1,09°**. Zasięg Z wynosi 13,7 m i zgadza się
z rachunkiem: 7,72 m różnicy rzędnych plus 5,90 m wysokości profilu.

Spadek liczony z geometrii: **1,647 – 1,655 %**, monotonicznie rosnący — czyli stała
prosta między dwiema znanymi stacjami, tak jak liczy ją `vertical_profile.py`, i mieści
się w limicie 4 % z `validate.py`.

## 4. Trzeci wariant, nie drugi

`variant_plan` znało dwa stany: `modelled` → `production`, wszystko inne →
`flat-preview`. Oś z rzędnymi na 7 % długości nie jest ani jednym, ani drugim.

Doszedł `partial-vertical` z sufiksem `_partial_vertical` w nazwie sceny
i `production_ready: False`. **`production` na osi `partial` jest odmową** — 7 % długości
ze rzędnymi nie czyni geometrii docelową, więc oś cząstkowa stoi tu po tej samej stronie
co płaska. Odmową jest też `partial-vertical` na osi, która nie jest `partial`: wariant
nie może twierdzić o osi czegoś, czego oś nie mówi.

Lista wariantów jest teraz w **jednym** miejscu: `tunnel_sweep.py` bierze `choices`
z `tunnel_manifest.SUFIKSY_WARIANTOW`, zamiast trzymać drugą kopię zbioru.

## 5. Co znaczy Z = 0 w wyniku

`depth_m` z rejestru to poziom główki szyny **względem poziomu ulicy**, ujemny. Z jest
więc w wyniku liczone od poziomu ulicy — to zmiana układu odniesienia wobec osi
wejściowej, gdzie Z = 0 było wypełniaczem.

**Z = 0 na odcinku bez rzędnej NIE znaczy „główka szyny na poziomie ulicy".** Znaczy
„nie wiemy". Zdanie o tym jedzie w `vertical.note` **w pliku wyniku**, a nie tylko
w dokumentacji: oś wynikową czyta `tunnel_sweep.py`, Godot i ktokolwiek, a płaski
odcinek wygląda wtedy jak rzędna równa zeru. Pilnuje tego test.

## 6. Cztery klatki kontrolne — OBEJRZANE

Renderowane dwa razy: z całego obiektu (468 m) i z okna 120–260 m, bo pierwszy zestaw
powtórzył lekcję z 6.D119 — obiekt o proporcjach 468 × 9,4 × 13,7 m kadrowany w całości
jest kreską.

**`_iso` (cały)** — ciągła rura widziana z góry pod kątem, z wyraźnym łukiem w planie
między Parc a Arts-Loi i zamkniętymi kapturkami na obu końcach. Bez przerw, bez załamań.
Przekrój jest w tej skali nieczytelny i to jest powód, dla którego okno istnieje.

**`_iso` (okno)** — ta sama rura z bliska: widać **prostokątny przekrój** na ciętym końcu,
gładkie przejście między pierścieniami, brak skręcenia. Rura zakrzywia się w prawo i nie
ma na niej ani jednego uskoku — czyli przycięcie zadziałało.

**`_side` (cały)** — wąska, prawie pozioma wstęga przez środek kadru z delikatnym łukiem.
Przy proporcji ~78 : 1 tyle się da zobaczyć; że spadek jest monotoniczny i wynosi 1,65 %,
wiem z **liczb**, nie z tego kadru, i tak to zapisuję.

**`_inside` (okno)** — kadr z osi z nakładką siatki: prostokątne pierścienie zbiegają się
do punktu zbiegu, tunel skręca w prawo, geometria otacza kamerę ze wszystkich stron.
Bez przekroju, bez pustki, bez patrzenia „przez" ścianę.

**`_normals`** — pole jednolicie szare, `tylna_strona=0.00000`, w obu wersjach. **I to
jest tu poprawny wygląd, nie pusta klatka:** materiał orientacji jest płaski, więc
wszystkie cztery ściany rury renderują się tym samym szarym, a krawędzie pierścieni są
widoczne dopiero z nakładką siatki, której ta klatka nie ma. Jednolita szarość znaczy
więc „każda widoczna powierzchnia rury jest oglądana od LICA" — czyli dokładnie to, co
`CLAUDE.md` §5 tej klatce przypisuje. Kształtu z niej nie ocenia się wcale; od tego jest
`_inside`.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py test_vertical_profile.py
  23/23 przeszło          (było 17)

$ python3 tools/tests/test_all.py test_tunnel_manifest.py
  44/44 przeszło          (było 39)

$ python3 tools/tests/test_all.py
  2284/2284 przeszło, 121 modułów

$ dotnet test tests/Sim.Tests
  Passed!  - Failed: 0, Passed: 600
```

## 8. Czego nie zrobiłem

- **Nie rozstrzygam konfliktu Schuman 15 m vs 17,42 m** i nie zdejmuję blokady z T-112 —
  pole „Poza zakresem" wyklucza oba wprost.
- **Nie ekstrapoluję poza zakres znanych rzędnych.** Poza Parc i Arts-Loi nie ma ani
  jednej nowej liczby.
- **Nie zmieniam ani jednego pliku w `data/`.** Oś wynikowa idzie do `build/`, a narzędzie
  **odmawia** zapisu do `data/` samo, z własnym kodem wyjścia — to jest test, nie zasada
  w komentarzu.
- **Nie wpuszczam wyniku do CI.** Żadna bramka tego nie żąda (reguła generatorów obejmuje
  `tools/blender/`, a nowy moduł jest w `tools/track/` i nie tyka `bpy`), a przebieg
  zamiatania tunelu z rzędnymi to osobna decyzja o czasie joba.

## 9. Zauważone przy okazji

- **Oś pełna z uskokiem zostaje w narzędziu i jest domyślna** (`--span all`). Nie da się
  jej zamieść, ale da się ją obejrzeć w JSON-ie — a jej metadane są jedynym miejscem,
  w którym stoi wysokość obu uskoków (19,721 m i 12,0 m). Usunięcie tego wariantu
  zabrałoby liczbę, która tłumaczy przycięcie.
- **Pierwszy punkt ze rzędną leży na 4092,564 m, a Parc na 4075,660 m** — bo profil
  przypisuje rzędne punktom osi, a nie stacjom, i pierwszy punkt osi za stacją wypada
  17 m dalej. Różnica jest nieszkodliwa, ale wyjaśnia, dlaczego odcinek w metrykach ma
  468,4 m, a nie 485,3 m z wypisu `vertical_profile.py`: to są dwie różne wielkości
  i obie są w raporcie tamtego narzędzia.
- **`render_check.py --from-m/--to-m` zawęża tylko kamerę wnętrza.** Klatki `_iso`
  i `_side` nadal kadrują cały obiekt, więc okno pomaga obejrzeć wnętrze, a nie bryłę.
  Dla obiektu o proporcji 78 : 1 znaczy to, że `_side` jest kreską niezależnie od okna.
