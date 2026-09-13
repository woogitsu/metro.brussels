# 6.D185 — nazwy członów wyliczeń na ekranie: sześć, nie dziesięć, i dwiema drogami

**13.09.2026**, na `641b70f`. Wejście: `src/Game/SignallingHud.cs`,
`src/Game/FirstRun.cs`, `src/Sim/Signalling/MovementAuthority.cs`,
`src/Sim/Signalling/TrainProtection.cs`, `src/Sim/Train/DoorCycle.cs`,
`tests/Game.Tests/UiTextTests.cs` (mapa `ZrodlaHud`),
`reports/6d183-tekst-na-ekranie-droga-wywolania.md` §4.

## 1. Pytanie pozycji

Ile nazw członów wyliczeń dociera na ekran, którą drogą, i czy przy każdej da się
postawić bramkę. Pole „Weryfikacja” żądało konkretu: lista znalezionych dziur ma
zawierać `authority.Reason` i `decision.Action`, bo inaczej skan patrzy nie tam.

## 2. Ile ich jest — SZEŚĆ, a pole „Co gracz widzi” mówi dziesięć

Pozycja wymienia `EndOfLine`, `OccupiedBlock`, `ReservedByOtherRoute`,
`BlockNotReserved`, `None`, `ServiceIntervention`, `EmergencyIntervention` i nazwę
ósmej fazy drzwi. Pomiar daje **sześć**, i różnica nie jest arytmetyczna:

| wyliczenie | członów | na ekran | dlaczego |
|---|---|---|---|
| `AuthorityLimit` | 4 | **4** | dziura bezwarunkowa; wszystkie cztery nadawane w `FixedBlockSystem.cs:636…665` |
| `ProtectionAction` | 3 | **2** | przed dziurą stoi straż — `None` nie dociera |
| `DoorPhase` | 7 | **0** | wszystkie siedem ma klucz katalogu; ramię domyślne jest martwe |

Straż przy `None` stoi w `SignallingHud.Line` i jest jawna:

```csharp
var ingerencja = decision.Action == ProtectionAction.None
    ? string.Empty
    : string.Create(CultureInfo.InvariantCulture,
        $"  ATP HAMUJE: {decision.Action} {decision.BrakeDemandMps2:F2} m/s²");
```

Napis z nazwą powstaje **dopiero po odrzuceniu `None`**. Nazwa `None` nie ma więc
drogi na ekran przez tę dziurę, a innej dziury `ProtectionAction` w `src/Game/` nie ma.

`DoorPhase` na ekran dziś nie dociera ani razu: `FirstRun.Faza` ma ramię dla każdego
z siedmiu członów, a `_ => phase.ToString()` jest ramieniem martwym. **Nie znaczy to,
że pozycja pomyliła się co do `DoorPhase`** — znaczy, że ósma faza jest warunkiem,
a nie stanem. Dlatego liczba sześć stoi obok bramki, która ten warunek pilnuje.

## 3. Dwie drogi, a nie jedna

| droga | gdzie | co ją łapie |
|---|---|---|
| **A — dziura interpolacji** `{wartość}` | `SignallingHud.Line`: `{authority.Reason}`, `{decision.Action}` | `Dziury_z_wyliczeniem_na_drodze_Hud_Update` |
| **B — jawne `.ToString()`** | `FirstRun.Faza`, ramię `_ => phase.ToString()` | `Faza_ma_ramie_dla_kazdego_czlonu_DoorPhase_wiec_ramie_domyslne_jest_martwe` |

Droga B **nie jest dziurą i skan dziur jej nie widzi** — dokładnie tak samo, jak
rodziny liczone po literałach nie widzą drogi A. Łapie ją co innego i bez jednej
heurystyki: **siedem członów `DoorPhase` wobec siedmiu ramion `Faza`**. Ósmy człon
bez ósmego ramienia ożywia ramię domyślne, a wtedy liczby przestają się zgadzać.

## 4. Granica korpusu — przesuwa się dla DEKLARACJI, nie dla skanowanego tekstu

Pozycja pytała, czy korpus bramki ma sięgnąć `src/Sim/`. Odpowiedź jest rozdzielona:

- **skanowanym tekstem** zostaje droga `Hud.Update` w `src/Game/` — tam stoją szablony,
  tam biegnie droga na ekran, i `src/Sim/` nie ma w tym udziału;
- **słownikiem typów** musi być całe `src/`, bo `AuthorityLimit` i `ProtectionAction`
  mieszkają w rdzeniu. Bramka czytająca deklaracje tylko z `src/Game/` nie wie, że to
  wyliczenia, i znajduje **zero** dziur — cicho i na zielono.

Zmierzone kontrolą KN-2: zwężenie słownika do `src/Game/` zapala **wszystkie cztery**
testy sekcji.

## 5. Kandydat z pola „Wyjście”: skan po NAZWIE — działa na drodze HUD-u, a szerzej MYLI SIĘ NA POŁOWIE

Kandydat pozycji to skan szablonów pod kątem dziur, których typ jest wyliczeniem.
Rozstrzygnięcie typu w C# wymaga rozbioru składni, czyli zależności, przed którą §8
każe przerwać — więc przyrząd jest z konieczności **sitem po NAZWIE**: dziura trafia,
gdy jej ostatni człon (`Reason` z `authority.Reason`) jest w `src/` zadeklarowany pod
typem wyliczeniowym.

Na drodze `Hud.Update` sito daje **dokładnie dwa trafienia i oba prawdziwe**:
`authority.Reason` i `decision.Action` — czyli to, czego żądało pole „Weryfikacja”.

Puszczone na **całe `src/Game/`** daje **12 trafień, z czego 6 fałszywych**:

| trafienie | co tam naprawdę stoi |
|---|---|
| `ChunkManifest.cs:Variant` | `public string Variant { get; }` |
| `DesignAssumptions.cs:Reason` | `record struct ViewAssumption(…, string Reason)` |
| `FirstRun.cs:availability.Reason` | `ChaseAvailability.Reason`, typu `string` |
| `FirstRun.cs:_manifest.Variant` | `ChunkManifest.Variant`, typu `string` |
| `RunPlan.cs:view` | `var view = Argument(arguments, "view") ?? "cab";` |
| `TunnelView.cs:manifest.Variant` | `ChunkManifest.Variant`, typu `string` |

**Nie jest to wąskie sito ani literówka we wzorcu — jest to stan drzewa.** Trzy nazwy
są w tym repozytorium dwuznaczne: `Reason` nosi i wyliczenie (`MovementAuthority.Reason`
typu `AuthorityLimit`), i napis (`ChaseAvailability`, `ViewAssumption`); `Variant` —
wyliczenie `ProtectionVariant` i napis `ChunkManifest.Variant`; `view` — `ViewKind`
w `RunHeader` i surowy argument wiersza poleceń w `RunPlan`.

Z sześciu trafień prawdziwych **na ekran idą dwa** — te z `SignallingHud`. Pozostałe
cztery (`_view` w `[ZRZUT]` i w telemetrii, `view` w `[PRZEJAZD]` ×2) idą do logu
i do pliku telemetrii, nie do HUD-u.

Stąd kształt bramki: **skan jest DETEKTOREM ZMIANY, nie orzecznikiem**. Lista dziur
z wyliczeniem jest WPISANA — tak samo jak mapa `ZrodlaHud` przy 6.D183 — a bramka żąda
od skanu **równości** z nią. Rozejście się którejkolwiek strony zapala test i wtedy
rozstrzyga człowiek. Lista trafień fałszywych też jest wpisana, i to jest odpowiedź
„nie da się i dlaczego” dla korpusu szerszego niż droga `Hud.Update`: gdyby fałszywych
ubyło do zera, skan wolno byłoby puścić szerzej — i wtedy ta bramka o tym powie.

## 6. Bramki

| bramka | na jakie pytanie |
|---|---|
| `Dziury_z_wyliczeniem_na_drodze_Hud_Update` | ile dziur ma droga na ekran (20, zapadka równościowa) i **które** wstawiają wyliczenie |
| `Nazwy_czlonow_docierajace_na_ekran_liczone_ze_straza_przy_None` | że straż przy `None` stoi, i że nazw jest 6 |
| `Faza_ma_ramie_dla_kazdego_czlonu_DoorPhase_wiec_ramie_domyslne_jest_martwe` | droga B: ósmy człon `DoorPhase` bez ósmego ramienia |
| `Skan_po_NAZWIE_myli_sie_na_POLOWIE_trafien_w_calym_src_Game` | dlaczego bramka kończy się na drodze `Hud.Update` |

## 7. Sześć kontroli negatywnych, baza 4/4, ani jedna zielona na końcu

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | `authority.Reason` zdjęte z listy wpisanej | 3/4, czerwona |
| KN-2 | słownik typów zwężony do `src/Game/` | **0/4**, wszystkie cztery czerwone |
| KN-3 | zdjęta straż `decision.Action == ProtectionAction.None ? string.Empty` | 3/4, czerwona |
| KN-4 | zdjęte ramię `DoorPhase.Checking` z `Faza` | 3/4, czerwona |
| KN-5 | zdjęte jedno trafienie fałszywe z listy wpisanej | 3/4, czerwona |
| KN-6 | cięcie dziury na pierwszym przecinku, z pominięciem nawiasów | 3/4, czerwona — **za trzecim podejściem** |

### KN-6 wyszła ZIELONA dwa razy i za każdym razem znaczyła co innego

**Pierwsze podejście — mechanizm bezczynny.** Liczenie nawiasów w `DziuryInterpolacji`
nie zmienia ŻADNEJ klasyfikacji: cięcie `{Units.MpsToKmh(decision.PermittedSpeedMps),5:F1}`
na pierwszym przecinku daje ten sam wynik, bo przecinek wyrównania JEST pierwszym
przecinkiem tej dziury. Zielona kontrola powiedziała prawdę o moim kodzie: asercje
sekcji nie pilnowały czytnika w ogóle.

**Drugie podejście — pin postawiony NIE TAM.** Dołożyłem pin na wyrażenie
`Units.MpsToKmh(decision.PermittedSpeedMps)` w bramce drogi `Hud.Update` — i kontrola
znów wyszła zielona, bo w tej dziurze nie ma przecinka wewnątrz nawiasów. Dopiero
pomiar wszystkich dziur `src/Game/` z nawiasem pokazał, że mechanizm rozstrzyga się
na **dwóch** dziurach całego korpusu i obie leżą **poza** drogą `Hud.Update`:
`string.Join(", ", KnownViews)` i `string.Join(" --", KnownArguments)`, obie
w `RunPlan.cs`. Pin przeniesiony do bramki całego `src/Game/` — i KN-6 czerwona.

Wniosek do katalogu zielonych kontroli: **„pin w złym miejscu” nie jest tym samym co
„mechanizm bezczynny”**, choć obie dają ten sam zielony wynik. Rozróżnia je pomiar
tego, gdzie mechanizm w ogóle ma szansę zadziałać — u mnie zrobiony dopiero po drugiej
zielonej.

## 8. Tautologia usunięta przed pierwszym przebiegiem

Bramka o połowie miała trzecią asercję: `trafienia.Count - falszywe.Count ==
trafienia.Count / 2`. Dwie asercje stojące wyżej przybijają `trafienia.Count` do 12,
a `falszywe` do sześcioelementowej listy wpisanej — trzecia liczyła więc `12 - 6 == 12 / 2`
na samych stałych i przechodziłaby zawsze. Rodzina 6.D160. Zdjęta, a w jej miejscu
stoi komentarz mówiący, że zdjęta jest z tego powodu, a nie przez zapomnienie.

## 9. Czego nie zrobiłem

- **Zachowania HUD-u nie tknąłem** — pole „Poza zakresem”. Sześć angielskich
  identyfikatorów nadal dociera na ekran; ta pozycja miała ustalić, ile ich jest
  i czy da się je pilnować, a nie je przetłumaczyć.
- **Do katalogu `UiText` nie przeniosłem niczego** — to samo pole.
- **`src/Sim/` nie zmieniłem ani o znak** — to samo pole. Rdzeń jest tu czytany,
  i wyłącznie czytany.

## 10. Zauważone po drodze, nie tknięte

- `KcvFunction` (`src/Sim/Signalling/TrainProtection.cs:138`, trzy człony) w `src/Game/`
  nie pada ani razu — na ekran nie dociera żadną z dwóch dróg.
- Skan `.ToString()` puszczony na surowy tekst `src/Game/` daje dwa trafienia na
  `phase.ToString()`, z czego **jedno stoi w komentarzu dokumentacyjnym**
  (`FirstRun.cs:1798`). W bramce tego skanu nie ma — droga B jest pilnowana liczbą
  ramion, nie szukaniem wywołania — ale gdyby kiedyś była, musi czytać przez
  `PominNieNapis`, a nie regeksem po surowym pliku.
