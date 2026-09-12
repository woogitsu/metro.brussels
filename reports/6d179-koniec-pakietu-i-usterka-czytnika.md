# 6.D179 — czwarty napis dla gracza, usterka czytnika, i kosz, którego nie da się uczciwie opróżnić

**12.09.2026**, na `9475b0e`. Wejście: zrzut 361 zgłoszeń, `src/Game/FirstRun.cs`,
`src/Game/RunPlan.cs`, `tests/Game.Tests/UiTextTests.cs`. Pozycja żądała, żeby każdy
literał dostał rodzinę albo został nazwany nierozstrzygalnym — **z pustym koszem
„pozostałe"**.

## 1. GŁÓWNY WYNIK: `koniec pakietu` widzi gracz, a wszystkie rodziny go przegapiły

```csharp
private void UpdateHud()
{
    var chainage = ChainageM;
    var name = "koniec pakietu";       // ← FirstRun.cs:1569
    …
    _hud.Update(
        _state.SpeedKmh, _acceleration, chainage, _axis.LengthM,
        name, distance, …);            // ← FirstRun.cs:1607
}
```

Jest to **nazwa następnej stacji pokazywana na HUD-zie, gdy następnej stacji nie ma**.
Droga na ekran identyczna z tą, którą 6.D175 prześledziło dla trzech napisów
`SignallingHud`.

**6.D175 odpowiedziało „trzy napisy ze 140" i odpowiedź była poprawna dla rodziny,
którą mierzyła** — literałów z polskim znakiem diakrytycznym. `koniec pakietu` żadnego
nie ma, więc do tych 140 nigdy nie wszedł. Tekstu dla gracza w kodzie jest zatem
**co najmniej cztery, nie trzy**.

I jest to dokładnie przypadek, przed którym ostrzegało 6.D173 — tam na wejściu
**syntetycznym** (`stacja`, `pociag`, `peron`, `drzwi`, `postoj`, `hamulec`). Tutaj
stoi jego **prawdziwy egzemplarz w kodzie**: polski napis dla gracza bez znaku
diakrytycznego, nieodróżnialny kształtem od identyfikatora.

## 2. DRUGI WYNIK: czytnik rozcina napisy interpolowane i to psuje samą bazę 348

Siedem „literałów" w zrzucie nie jest literałami. Powstają, bo `Literaly` czyta
wyrażeniem regularnym napis interpolowany zawierający **zagnieżdżony cudzysłów**:

```
$"[ARGUMENT] nieznany argument '--{name}'. Znane: --{string.Join(" --", KnownArguments)}"

  1. "[ARGUMENT] nieznany argument '--{name}'. Znane: --{string.Join("   ← UCIĘTY W POŁOWIE
  2. ", KnownArguments)}"                                               ← NIE JEST LITERAŁEM
```

Skutek nie ogranicza się do siedmiu pozycji kosza: **baza 348 zawiera literały ucięte**,
więc każda rodzina licząca po treści literału (prefiks, polski znak, kształt) mogła
policzyć fragment zamiast całości. Nie przeliczam tu żadnej z wcześniejszych liczb —
mówię, że mają wspólne źródło niepewności, i zapisuję to jako pozycję.

## 3. Rozbicie pełne, z uczciwym koszem

| rodzina | ile | skąd rozstrzygnięcie |
|---|---:|---|
| opcja CLI | 91 | 6.D176, 6.D181 |
| wypis z prefiksem | 75 | 6.D174 |
| identyfikator / pole JSON | 35 | 6.D173 |
| polski — diagnostyka | 30 | 6.D175 |
| proza założeń | 20 | 6.D177 |
| komunikat wyjątku | 19 | 6.D178 |
| fragment dalszy komunikatu | 17 | 6.D174 |
| klucz JSON-a | 13 | 6.D181 |
| **POZOSTAŁE** | **13** | — |
| ścieżka pliku | 11 | 6.D179 |
| wypis bez prefiksu | 10 | 6.D174 |
| HUD — tekst gracza | 9 | 6.D175 |
| węzeł sceny / zasób | 8 | 6.D179 |
| **artefakt czytnika (nie literał)** | **7** | 6.D179 |
| identyfikator wielkimi literami | 2 | 6.D179 |
| nagłówek CSV | 1 | 6.D179 |

Suma 361.

## 4. Kosza NIE opróżniam i to jest odpowiedź, a nie uchylenie się

Pole „Skończone, gdy" żąda, żeby nie została ani jedna pozycja w koszu. Z trzynastu:

- **jedenaście** to dalsze fragmenty komunikatów (`+ "przychodzi z odtwarzanego pliku…"`,
  `+ $"a format rdzenia ma {…}"`). Widać to okiem od razu;
- **jeden** to `scene.Name = "Platforms"`, czyli węzeł sceny;
- **jeden** to `koniec pakietu` — sekcja 1.

Regułę, która wciągnęłaby te jedenaście, umiem napisać: wystarczy poszerzyć okno
kontekstu. **I właśnie dlatego jej nie piszę.** 6.D174 zmierzyło, że okno daje
12–77 zależnie od szerokości; 6.D178 zmierzyło, że przypisanie do instrukcji daje
12–51 zależnie od reguły kontynuacji. Poszerzanie okna aż kosz wyjdzie pusty to
**dopasowywanie przyrządu do żądanego wyniku** — czyli to samo, co obniżanie progu,
żeby bramka przeszła.

Kosz zostaje więc jawny: **jedenaście fragmentów rozstrzygalnych okiem i nierozstrzygalnych
regułą niezależną od formatowania, jeden węzeł sceny, jeden tekst gracza.** To jest
uczciwa odpowiedź na pytanie „czym są te literały", a pusty kosz byłby odpowiedzią
ładniejszą i nieprawdziwą.

## 5. Czego nie zrobiłem

- **Nie przeniosłem `koniec pakietu` do katalogu.** Zmienia to zachowanie HUD-u,
  tak samo jak trzy napisy z 6.D175 — osobna robota, teraz obejmująca cztery napisy,
  a nie trzy.
- **Nie naprawiłem czytnika.** `Literaly` wymaga rozumienia napisów interpolowanych
  z zagnieżdżeniem, a to jest zmiana klasy narzędzia (§8) i wchodzi jako 6.D182.
- **Nie przeliczyłem wcześniejszych rodzin** po odkryciu usterki czytnika — sekcja 2.
- **Nie poszerzyłem okna, żeby opróżnić kosz** — sekcja 4.

## 6. Bramka zapaliła się w trakcie i kazała OBNIŻYĆ próg — sprawdziłem, zanim posłuchałem

Dopisanie tego raportu zaczerwieniło `test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami`:

```
drzewo daje 6.99 ścieżki na raport przy podłodze 6 — zapas zszedł poniżej jednej
pełnej ścieżki (2012 trafień wobec 2016 wymaganych) […]
Obniż `SCIEZEK_NA_RAPORT_MIN` w tym samym commicie, w którym to widzisz
```

**„Obniż próg" to ruch, który ta sesja krytykowała cztery razy**, więc nie posłuchałem
od razu. Podłoga jest zaboksowana dwoma brzegami liczonymi z drzewa, a komentarz przy
stałej mówił, że zawężenie kontrolne zbija stosunek do **5,59** — przy tej liczbie 5
przestaje łapać kontrolę i obniżenie byłoby oślepieniem bramki.

**Zmierzyłem oba brzegi zamiast wierzyć komentarzowi:**

```
checked=288  seen=2012  stosunek=6.986
ubytek .md=699  zawezony=1313  stosunek zawezony=4.559

  K=5: kontrola ŁAPANA, zapas>=1 ścieżka: True   -> MIEŚCI SIĘ
  K=6: kontrola łapana,  zapas>=1 ścieżka: False -> nie
```

Zawężenie kontrolne daje dziś **4,56**, a nie 5,59 — udział `.md` urósł do 699 trafień
z 2012. Przy tej liczbie **5 łapie kontrolę z zapasem**, więc komunikat bramki miał
rację, a moja podejrzliwość opierała się na liczbie sprzed trzech dni wpisanej
w komentarz.

**Jest to ta sama pomyłka, co pięć wcześniejszych w tej sesji, tylko odwrócona:**
zaufanie liczbie z prozy zamiast pomiarowi omal nie kazało mi **odrzucić poprawnej
instrukcji**. Poprzednie pięć razy ten sam nawyk kazał mi coś błędnego przyjąć.

Przedział mieszczący się w obu brzegach to dziś **{5}** — jedna wartość, a 09.09.2026
było ich trzy. Komentarz przy stałej jest przepisany, nie dopisany obok, i niesie
liczby z dzisiejszego pomiaru razem z rachunkiem trwałości: przy gęstości 5,11 nowy
próg zaczerwieni się po **319** raportach, przy 6,0 i wyżej — nigdy.

**Spadek stosunku nie bierze się z chudnięcia raportów.** Ostatnie 50 dodanych ma
**9,06** ścieżki na raport, ostatnie 30 — **8,00**, czyli powyżej katalogu. Średnią
z 09.09.2026 podbijały raporty najstarsze (pierwsze 50: 15,14) i to ich udział maleje.
Szesnaście raportów z tej sesji ma średnią **7,12**, czyli nieco powyżej katalogu —
ale sześć z nich ma po 3–5 ścieżek, a każdy taki kosztuje zapas, bo brzeg żąda siedmiu.
