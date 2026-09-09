# Render, który miał wykrywać wywrócone normalne, i nie wykrywał (6.D75)

**Zmierzone 09.09.2026 na:** `ef9c4f6`, kontener tej sesji, Blender 5.2.1.
**Przyrząd:** para fixture różniąca się wyłącznie orientacją ścian,
`tools/blender/render_check.py`, `tools/visual/compare.py`,
`tools/blender/tunnel_sweep.py`, `python3 tools/tests/test_all.py`.

---

## 1. Usterka

`CLAUDE.md` §5 przypisuje renderowi `_inside` wykrywanie wywróconych normalnych
(„widać »przez« ścianę") i jest to jedyna bramka normalnych w opisanej pętli
weryfikacji geometrii. Para fixture różniąca się **wyłącznie** windingiem — te same
wierzchołki, ta sama kamera, ta sama oś:

```
[KLATKA] good_inside.png     640x384 ink=0.09278 std=0.04349 poziomy=140
[KLATKA] flipped_inside.png  640x384 ink=0.09278 std=0.04349 poziomy=140

side:   roznych_bajtow=0  max_delta=0
inside: roznych_bajtow=4  max_delta=255
```

`_side` bit w bit identyczny, `_inside` różny o cztery bajty na 737 tysięcy, czyli
szum kompresji. Oba obrazy obejrzane: ani jednej różnicy, wersja z odwróconymi
normalnymi wygląda jak zdrowy tunel.

Przyczyna jest trzykrotna i każda wystarcza sama: materiał kontrolny jest
dwustronny, silnik cieniuje tylną stronę z odwróconą normalną, a emisja dokłada
składową niezależną od zwrotu.

## 2. Dlaczego OSOBNA klatka, a nie kulling na `_inside`

Kulling na materiale kontrolnym byłby prostszy i dosłowniej zgodny z §5 („widać
przez ścianę"). Nie został wybrany, i powód jest mierzalny, nie estetyczny:
`render_check.py` renderuje także pudło pojazdu i przekroje stacji, oglądane
**legalnie od tyłu**. Wspólny materiał jednostronny zapalałby się wtedy na
poprawnej geometrii, a bramka, która fałszywie alarmuje, zostaje wyłączona przez
pierwszego zirytowanego człowieka — rodzina 6.D27, ścigana w tym projekcie osobno.

Osobna klatka nic nie ukrywa i nic nie odbiera trzem istniejącym: **dodaje sygnał.**
Nie rusza też ani jednego bajtu `_iso`, `_side` i `_inside`, więc regresja wizualna
i jej sumy kontrolne zostają nietknięte.

## 3. Co powstało

Klatka `_normals` z materiału, w którym **przód ściany świeci na 0.10, a tył na
0.95**. Emisja, nie kolor bazowy: nie zależy od kąta światła, więc ta sama ściana
daje ten sam poziom niezależnie od pozycji słońca. Odczyt idzie po luminancji, nie
po barwie, bo czytnik PNG tego repozytorium zwraca skalę szarości — magenta
i szarość byłyby dla niego tym samym.

Klatka powstaje **przed** nakładką siatki i przed przywróceniem materiału
kontrolnego. To nie kolejność z gustu: duplikaty siatki mają własne ściany, więc
liczyłyby się do udziału tylnej strony i mierzyłoby się nakładkę zamiast geometrii.
Osobna asercja tego pilnuje.

## 4. Pomiar

```
good.glb    [NORMALNE] good_normals.png    tylna_strona=0.00000
flipped.glb [NORMALNE] flipped_normals.png tylna_strona=0.99661  <-- SCIANY ODWROCONE
```

I na **prawdziwym** zasobie z `tunnel_sweep.py`, czterech obiektach:

```
[NORMALNE] material orientacji przypisany do 4 obiektow
[NORMALNE] TEST_normals.png tylna_strona=0.00000
```

## 5. Co widzę na klatkach — obejrzane, nie odczytane z liczby

- **`good_normals.png`**: jednolite **ciemnoszare** pole, w środku mały ciemny
  niebieskoszary kwadrat. Kwadrat to tło świata widoczne przez wylot rury.
- **`flipped_normals.png`**: to samo ujęcie, ten sam kwadrat w tym samym miejscu,
  ale pole jest **jasnoszare**.
- **`TEST_normals.png`** (prawdziwy tunel): jednolite ciemnoszare pole, ani jednego
  jasnego piksela, bez kwadratu — trasa jest dość długa, żeby tło nie prześwitywało.

Ciemne wobec jasnego, na całej powierzchni kadru. Różnicy nie da się przeoczyć ani
pomylić z szumem, a identyczny kwadrat w obu klatkach fixture potwierdza, że różni
je orientacja ścian, nie kadr.

**Czego ta klatka NIE ocenia:** jest niemal jednolita z założenia i nie mówi nic
o czytelności geometrii. Do tego są trzy pozostałe. Dlatego nie przechodzi przez
podłogę pustej klatki — tamta podłoga mierzy rozrzut poziomów szarości i zamieniłaby
POPRAWNY wynik w błąd.

## 6. Bramka bez Blendera

Matematyka pikseli została przeniesiona do `tools/visual/compare.py`, gdzie już
mieszkają statystyki obrazu i podłogi — właśnie po to, żeby klatkę dało się
sprawdzić w zestawie, który Blendera nie uruchamia. Za samo renderowanie
odpowiada job Blendera w CI.

Powstały dwie bramki. Pierwsza sprawdza zachowanie funkcji: przód daje zero, tył
jedynkę, **połowa na połowę daje 0.5** (bez tego funkcja mogłaby zwracać tylko zero
albo jedynkę i częściowe odwrócenie byłoby nierozpoznawalne), próg leży **między**
dwoma poziomami materiału, a pusta klatka nie dzieli przez zero. Druga sprawdza, że
skrypt tę funkcję naprawdę **woła** i że klatka powstaje przed nakładką — bez tego
poprawka mogłaby zostać zredukowana do martwej funkcji: matematyka gotowa, klatka
nierenderowana, pierwsza bramka zielona.

## 7. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| wywołanie klatki usunięte ze skryptu | `FAIL test_skrypt_renderu_naprawde_wola_klatke_orientacji: _normals.png`, 9/10 |
| klatka przeniesiona ZA nakładkę siatki | ten sam test pada i mówi, że **kolejności nie da się sprawdzić**, 9/10 |
| próg przesunięty pod poziom przodu ściany | `FAIL test_klatka_orientacji_odroznia_przod_sciany_od_tylu: 1.0`, 9/10 |
| funkcja zwraca tylko 0 albo 1 | ten sam test, `0.0` na klatce pół na pół, 9/10 |
| `>` zamienione na `<` w porównaniu progu | `FAIL … : 1.0` — mutacja celowana **ZABITA**, 2069/2070 |

`md5sum -c` po każdej: `OK`.

Kontrola druga zasługuje na zdanie osobno. Jej pierwsza wersja pokazywała komunikat
`substring not found` — czyli błąd biblioteki wyciekający z bramki zamiast powodu.
Poprawione: bramka rozróżnia teraz „klatka powstaje po nakładce" od „nie da się
ustalić kolejności" i mówi to wprost, bo milczenie bramki nie może znaczyć
„kolejność jest dobra".

## 8. Skutek, którego nie przewidziałem

Dopisanie funkcji do `compare.py` zmieniło liczbę mutacji tego modułu i **inna
bramka to złapała**:

```
FAIL test_drift_report_mutation_count_is_the_one_the_tool_gives_today:
  reports/mutation-drift.md rozjechał się z drzewem — przelicz audyt dla tych
  modułów: ['tools/visual/compare.py: raport mówi 25, narzędzie liczy 26']
```

Wiersz audytu mutacyjnego został **przedłużony, nie nadpisany**: niesie teraz
dzisiejszy pomiar celowany obok tego z 6.D9, w tym samym stylu, w jakim był
zapisany. To jest bramka pilnująca, żeby raport z audytu mutacyjnego nie stał się
zdaniem o przeszłości udającym stan bieżący — i zadziałała dokładnie tak, jak miała.

## 9. Weryfikacja

```
  10/10 przeszło       test_render_engine.py
  RAZEM 105.327 s, 2070 testów, 110 modułów
kod=0
```

Zestaw przed pozycją: 2068 testów.

## 10. Czego świadomie nie zrobiono

**Nie postawiono twardego progu odmowy** przy wysokim udziale tylnej strony. Skrypt
woła się dziś z dwóch miejsc: z próby dymnej Blendera (zmierzone `0.00000`)
i z przekrojów stacji, **których nie zmierzyłem** — bez tej drugiej liczby próg
odmowy mógłby zaczerwienić przebieg na poprawnym zasobie, a push wywracający CI
kosztuje cykl i zaufanie. Klatka na razie **mówi** i stawia znacznik przy wartości
powyżej połowy. Brakujący pomiar idzie na najbliższe uzupełnienie kolejki.

**Nie tknięto `CLAUDE.md` §5.** Jego tabela nadal przypisuje wykrywanie normalnych
renderowi `_inside`, a od tej poprawki zdolność istnieje, tylko w innej klatce.
To dokument właściciela i jednowierszowa zmiana należy do niego — zgłoszone,
nie zrobione.

Nie zmieniono materiału kontrolnego ani trzech istniejących klatek: ich bajty
zostają, żeby regresja wizualna nie musiała przeliczać sum.
