# 6.D119 — kabina kanoniczna: osiem pudełek, dwadzieścia cztery decyzje

**Zmierzone 11.09.2026 na:** `8c9e470`, kontener tej sesji.
**Przyrząd:** `tools/blender/m7_cab.py` (nowy, bez `bpy`),
`tools/blender/m7_cab_build.py` (nowy, generator), `tools/tests/test_m7_cab.py` (nowy),
`tools/tests/test_dimension_audit.py`, `tools/ci/m7_shell_check.sh`,
`docs/21-measured-vs-assumed.md`; Blender 5.2.1 z przypiętego tarballa,
`data/vehicle/m7-spec.json` — wyłącznie do odczytu.

---

## 1. Co powstało i czego NIE przedstawia

Układ **kanoniczny** kabiny: podłoga, ściana do przedziału pasażerskiego z jednymi
drzwiami, pulpit i fotel. Osiem brył na kabinę, dwie kabiny na skład.

**To nie jest kabina M7 i nie wolno jej tak przedstawiać.** STIB nie publikuje rzutów
kabiny, a `docs/03-legal.md` nie daje prawa do cudzych rysunków ani do odwzorowywania
kabiny ze zdjęć. Zdanie o tym jedzie **w raporcie generatora**, obok geometrii, a nie
tylko w dokumentacji — tak samo, jak zespół dostępu stacji mówi to o antresoli. Pilnuje
tego test, nie dobre chęci.

Ze `spec` przychodzą **wyłącznie** wymiary skorupy, przez `m7_layout.Layout`: szerokość
pudła, wysokość podłogi i długość składu. Pozostałe **24** liczby to `design_assumption`
z wpisem w `docs/21` §4g.

## 2. Podział na dwa moduły i co z niego wynikło

`m7_cab.py` liczy geometrię **bez `bpy`**, `m7_cab_build.py` zamienia pudełka na siatki.
Ten sam podział, co `station_components.py` wobec `station_kit.py`, i ten sam powód:
każdy wymiar da się sprawdzić bez uruchamiania silnika.

**Podział opłacił się w pierwszej godzinie i nie tam, gdzie się spodziewałem.** Tabela
windingu ścian (`FACES`) stała najpierw w module z `bpy` — i była **zła**. Klatka
`_normals` dała:

```
[NORMALNE] M7_cab_front_normals.png tylna_strona=0.65004  <-- SCIANY ODWROCONE
```

czyli dwie trzecie widocznej powierzchni oglądane od podszewki. Dopóki tabela mieszkała
po stronie `bpy`, jedynym sposobem sprawdzenia jej było **wygenerowanie i wyrenderowanie**.
Dziś stoi w module bez `bpy` i jest sprawdzana iloczynem wektorowym — sześć ścian, sześć
różnych kierunków, plus asercja, że normalna idzie OD środka bryły, a nie do niego (bez
niej tabela odwrócona w komplecie przeszłaby razem z odwróconą listą oczekiwań).

Po poprawce: `tylna_strona=0.00000`.

## 3. Zawieranie jest tu najważniejszym testem

`test_kazda_bryla_kabiny_miesci_sie_w_skorupie` sprawdza, że **każdy wierzchołek każdej
bryły** leży wewnątrz przekroju skorupy w tym samym X. Pudełko wystające przez blachę
wygląda na renderze z wnętrza jak kabina — widać je dopiero z zewnątrz, a kabinę ogląda
się od środka.

Połowa szerokości wnętrza **nie jest wpisana**: liczy się z przekroju w najwęższym
miejscu kabiny (przy licu szyby czołowej) minus wykładzina. Przy dzisiejszym `spec`
daje to 0,9156 m wobec 1,35 m połowy szerokości pudła — czoło jest zwężone o 0,384 m
na stronę przez ścięcie nosa. Zmiana szerokości pudła we `spec` przechodzi więc do
kabiny sama, a nie przez przepisanie liczby.

## 4. Cztery klatki kontrolne — OBEJRZANE

Renderowane z `build/M7_cab_front.glb`, czyli z **jednej** kabiny. Pierwszy przebieg
szedł z obu kabin naraz i był bezużyteczny: kadr obejmuje 94 m składu, więc każda
kabina zajmowała ~4 % szerokości obrazu — dwa jasne punkciki w narożnikach ciemnego
tła. Geometrycznie poprawne, do oglądania nie nadaje się wcale.

**`_iso`** — rzut z góry pod kątem. Widzę płaską płytę podłogi jako podstawę, na niej
trzy rzeczy w rzędzie: z lewej (od czoła) wysoki blok pulpitu szeroki na większość
kabiny, w środku niski sześcian siedziska z cienką płytą oparcia tuż za nim, z prawej
wysoka ściana z **wyraźnym prostokątnym otworem drzwi** sięgająca od podłogi do sufitu.
Scena nie jest pusta, nie jest zwinięta w punkt, proporcje czytają się jak wnętrze.

**`_side`** — rzut z boku. Od lewej: cienki pas podłogi biegnący przez całą szerokość
kadru, blok pulpitu (mniej więcej dwa razy wyższy od siedziska), przerwa, siedzisko
i wystające ponad nie oparcie, potem **długi pusty odcinek podłogi**, a na końcu ściana
z otworem drzwi, najwyższy element kadru. Jednostki się zgadzają: pulpit sięga niecałej
połowy wysokości ściany, oparcie kończy się tuż nad pulpitem. Profil pionowy bez
niespodzianek — wszystko stoi na podłodze, nic nie wisi.

**`_normals`** — zbliżenie na ścianę. Jednolita jasnoszara powierzchnia (lico
zewnętrzne materiału kontrolnego) z trzema ciemnogranatowymi prostokątami: środkowy to
otwór drzwi, dwa skrajne to tło poza ścianą. **Ani jednego ciemnego pola na samej
geometrii**, czyli żadna ściana nie jest oglądana od tyłu. To jest ta klatka, która
zapaliła się przy pierwszej wersji windingu i dlatego jest tu opisana osobno.

**`_inside`** — kadr z osi, z nakładką siatki. Dolną połowę zajmuje jasna płaszczyzna
podłogi, przecięta ciemnym pasem jej krawędzi; w górze ściana z otworem drzwi, przez
który widać ciemne tło, i ukośne linie siatki schodzące do punktu zbiegu. Geometria
otacza kamerę ze wszystkich stron — nie ma pustki, nie ma przekroju, nie widać „przez"
ścianę tam, gdzie ściana jest.

## 5. Pusta przestrzeń za fotelem — zauważona, nie ukryta

Rzut z boku pokazuje **około 1,5 m pustej podłogi** między oparciem a ścianą do
przedziału pasażerskiego. Rachunek: pulpit 0,50–1,10 m od czoła kabiny, siedzisko
1,45–1,90 m, oparcie 1,90–2,00 m, ściana 3,52–3,60 m. To nie jest usterka geometrii —
to skutek tego, że kabina ma 3,60 m, a układ kanoniczny nie stawia w niej nic poza
pulpitem i fotelem. W prawdziwej kabinie stoi tam przejście i szafy aparatury, a tych
ta pozycja nie robi (pole „Poza zakresem": przyrządy i wskaźniki).

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_m7_cab.py
  10/10 przeszło          (moduł nowy)

$ python3 tools/tests/test_all.py test_dimension_audit.py
  18/18 przeszło          (było 15)

$ python3 tools/tests/test_all.py
  2273/2273 przeszło, 121 modułów
```

Generator, dwie kabiny i jedna:

```
[KABINA] brył=16 otworów=6 -> build/M7_cab.glb (17848 B)
[KABINA] brył=8 otworów=6 -> build/M7_cab_front.glb (9140 B)
[KABINA] UKŁAD KANONICZNY, NIE kabina M7: rzeczywiste wymiary kabiny M7 —
         wszystkie liczby są design_assumption
```

## 7. Czego nie zrobiłem

- **Nie robię przyrządów, wskaźników ani niczego pokazującego stan pociągu** — pole
  „Poza zakresem" wyklucza to wprost. Pulpit jest bryłą, nie panelem.
- **Nie odwzorowuję kabiny M7 z czyichkolwiek zdjęć ani rysunków** (`docs/03-legal.md`).
- **Nie wycinam szyb w skorupie.** Szyba czołowa i okna boczne są policzone jako
  **dane** i sprawdzone, że mieszczą się w przekroju pudła; wycięcie otworu należy do
  generatora skorupy, którego ta pozycja nie zmienia.
- **Nie podpinam kabiny do sceny Godota.** `--view=cab` nadal ustawia kamerę i nic poza
  tym; wprowadzenie bryły do sceny to osobna praca.
- **Nie zmieniłem ani jednej wartości w `data/`** (§4.6).

## 8. Zauważone przy okazji

- **Bez `libEGL.so.1` Blender renderuje „do końca" i nie renderuje nic.** Pierwszy
  przebieg `render_check.py` na tej maszynie skończył się linią
  `Couldn't open libEGL.so.1` **po** wypisaniu wszystkich kroków importu — i nie
  powstał ani jeden PNG. Lista pakietów jest w repozytorium
  (`tools/ci/apt-packages/blender.txt`) i to ona załatwiła sprawę; wartość tego wpisu
  polega na tym, że komunikat nie mówi, czego brakuje, dopóki nie dojdzie się do końca
  wypisu.
- **Klatka `_iso` z dwóch kabin naraz jest bezużyteczna i nic tego nie mówi.**
  `render_check.py` kadruje całą zawartość pliku, więc dwa obiekty oddalone o 94 m dają
  dwa punkciki. Bramka `[RENDER]` przeszła — kadr nie jest pusty i ma odchylenie
  standardowe powyżej progu. To ta sama rodzina, co przykład z `docs/06-worked-example.md`
  §1: metryka odrzuca klatkę **czarną**, nie **złą**.
