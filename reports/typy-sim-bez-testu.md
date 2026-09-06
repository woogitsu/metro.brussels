# Sześć typów `src/Sim` bez własnego testu — pomiar, testy i kontrole negatywne

**Zmierzone 06.09.2026 na commicie:** `4e56958`

Pozycja 6.A8. Blok kolejki mówił o **sześciu z 45** plików `src/Sim`, których nie nazywa
żaden plik pod `tests/`. Pomiar wykonany przed pisaniem testów daje **pięć z 52** — i to
nie dlatego, że ktoś w międzyczasie dopisał test jednostkowy, tylko dlatego, że
`MovementAuthority` wszedł do zasięgu licznika bocznymi drzwiami. Ten raport zapisuje
pomiar przed i po, co przybija każdy z 39 nowych testów, i wypis **każdej** z 39 kontroli
negatywnych — wykonanych, nie opisanych.

Kodu w `src/Sim/` nie zmienia ani o znak: mutacje kontroli negatywnych były nakładane
i zdejmowane skryptem, a `git status` po wszystkim pokazuje wyłącznie trzy nowe pliki
w `tests/Sim.Tests/`.

---

## 1. Pomiar przed — i dlaczego licznik z bloku kolejki dziś kłamie

Licznik wpisany do pola **Weryfikacja** pozycji 6.A8 brzmi:

```bash
for f in $(find src/Sim -name '*.cs'); do n=$(basename $f .cs); \
    [ "$(grep -rlw "$n" tests/ | wc -l)" -eq 0 ] && echo "BRAK TESTU: $f"; done
```

Na czystym drzewie wypisuje pięć plików. **Po pierwszym `dotnet test` wypisuje zero** —
i to zero jest fałszywe. Powody są dwa, oba mechaniczne:

* `grep -r tests/` wchodzi w `tests/Sim.Tests/bin/` i `tests/Sim.Tests/obj/`, a tam leżą
  `MetroBxl.Sim.dll`, `MetroBxl.Sim.pdb` i `MetroBxl.Sim.xml`. Nazwa **każdego** typu
  rdzenia jest w tych plikach, więc po zbudowaniu zestawu licznik uznaje za otestowane
  wszystko, co się skompilowało;
* `find src/Sim -name '*.cs'` wciąga dwa pliki wygenerowane przez budowanie, leżące
  pod `src/Sim/obj/` — `Sim.AssemblyInfo` i `AssemblyAttributes` — których nikt nigdy
  nie otestuje i które podbijają licznik od drugiej strony.

  **Ich pełnych ścieżek ten raport celowo nie wypisuje w grawisach**, i jest to
  poprawka wprowadzona po awarii bramki, nie ostrożność z góry. Pierwsza wersja je
  wypisała, a `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`
  zapaliła się na CI, choć u autora przechodziła: **na maszynie po `dotnet build` te
  pliki istnieją, w czystym checkoucie nie.** Bramka miała rację — raport nie ma prawa
  wysyłać czytelnika po plik, którego w drzewie nie ma, a wytwór budowania nie jest
  w drzewie z założenia (`CLAUDE.md` §4.8).

Licznik użyty w tym raporcie omija oba katalogi:

```bash
for f in $(find src/Sim -name '*.cs' -not -path '*/obj/*' -not -path '*/bin/*' | sort); do
    n=$(basename $f .cs)
    [ "$(grep -rlw "$n" tests/ --include='*.cs' --exclude-dir=bin --exclude-dir=obj | wc -l)" -eq 0 ] \
        && echo "BRAK TESTU: $f"
done
```

Wypis **przed** zadaniem, na `4e56958`:

```
BRAK TESTU: src/Sim/Physics/BrakingEnergyAccount.cs
BRAK TESTU: src/Sim/Physics/DesignParameter.cs
BRAK TESTU: src/Sim/Physics/EnergyAccount.cs
BRAK TESTU: src/Sim/Physics/SpeedProfile.cs
BRAK TESTU: src/Sim/Signalling/Block.cs
```

Pięć plików, nie sześć. Plików źródłowych jest 52, nie 45.

### Czym różni się ta lista od listy z bloku 6.A8

| plik z bloku | licznik dziś | dlaczego |
|---|---|---|
| `src/Sim/Physics/EnergyAccount.cs` | nadal bez testu | — |
| `src/Sim/Physics/BrakingEnergyAccount.cs` | nadal bez testu | — |
| `src/Sim/Physics/SpeedProfile.cs` | nadal bez testu | — |
| `src/Sim/Physics/DesignParameter.cs` | nadal bez testu | — |
| `src/Sim/Signalling/Block.cs` | nadal bez testu | — |
| `src/Sim/Signalling/MovementAuthority.cs` | **poza listą** | nazywa go `tests/Game.Tests/SignallingHudTests.cs` |

`MovementAuthority` zszedł z listy licznika, ale **nie dostał testu jednostkowego**.
Jedyne miejsce, które go nazywa, to prywatna metoda pomocnicza warstwy kabiny:

```csharp
// tests/Game.Tests/SignallingHudTests.cs:25
private static MovementAuthority Authority(double frontM, double endM, string blockId) =>
```

czyli zaślepka budująca authority po to, żeby sprawdzić, co pokaże HUD. Nic tam nie pyta
`MovementAuthority` o to, co on sam obiecuje wołającemu — `DistanceM` przy authority
kończącym się za czołem składu, `AllowsMovement` na granicy zera. Dlatego **pole Wyjście
bloku 6.A8 zostało wykonane w całości**, razem z `MovementAuthorityTests.cs`: licznik
nazwy pliku jest zapadką, a nie definicją otestowania, i akurat tu widać różnicę.

## 2. Pomiar po

Ten sam licznik po zadaniu, wypis pusty:

```
--- licznik czysty PO ---
(koniec wypisu)
```

## 3. Co powstało

| plik | typy | testów |
|---|---|---|
| `tests/Sim.Tests/EnergyAccountTests.cs` | `EnergyAccount`, `BrakingEnergyAccount`, `DesignParameter` | 14 |
| `tests/Sim.Tests/SpeedProfileTests.cs` | `SpeedProfile`, `SpeedSample` | 11 |
| `tests/Sim.Tests/MovementAuthorityTests.cs` | `MovementAuthority`, `Block`, `Route` | 14 |

Podział idzie za przestrzeniami nazw i za polem **Wyjście**: `Route` mieszka
w `Block.cs`, `SpeedSample` w `SpeedProfile.cs`, więc jadą razem ze swoimi plikami.

Wspólna zasada wszystkich trzech plików: **żaden nie mierzy przebiegu**. Przebiegi mierzą
`EnergyAndProfileTests` i `FixedBlockTests`, a konta energii, profile i bloki są w nich
naczyniem na wynik. Tu są przedmiotem — pytanie brzmi, co ten typ obiecuje wołającemu,
gdy dostanie liczby, których żaden przebieg nie wyprodukuje: zerową pracę trakcji, zerowy
ubytek energii, zerowe opóźnienie, zero próbek, chainage dokładnie na granicy bloku.

Żadna liczba o sieci ani o taborze nie jest tu przypinana. Wartości w kontach energii są
arbitralne i dobrane tak, żeby wychodziły z arytmetyki `double` **dokładnie** — stąd
tolerancje `0.0` przy większości porównań. Granice bloków są syntetyczne z dokładnie
tego powodu, który wypisuje `FixedBlockTests`: granice pakietu A są `design_model`,
więc przypięcie ich tutaj przypięłoby założenie zamiast zachowania.

### Co przybija każdy test

**`EnergyAccountTests`** (14)

| test | co przybija |
|---|---|
| `Reszta_bilansu_odejmuje_kazdy_z_pieciu_czlonow_z_waga_minus_jeden` | każdy z pięciu członów wchodzi do reszty z wagą dokładnie −1 — sprawdzone przez podniesienie po jednym |
| `Reszta_wzgledna_jest_nieujemna_takze_przy_ujemnym_niedomknieciu` | znak niedomknięcia nie przecieka do miary względnej |
| `Reszta_wzgledna_przy_zerowej_pracy_trakcji_jest_zerem_a_nie_nieskonczonoscia` | granica bez mianownika: **0,0**, nie `Infinity`, nie `NaN`; reszta bezwzględna zostaje niezerowa |
| `Praca_trakcji_w_kilowatogodzinach_dzieli_dzule_przez_trzy_i_szesc_miliona` | 7 200 000 J = 2 kWh |
| `Wiersz_konta_rozruchu_nie_zalezy_od_kultury_maszyny` | kultura z przecinkiem dziesiętnym nie zmienia wiersza raportu |
| `Reszta_bilansu_hamowania_odejmuje_kazdy_z_czterech_czlonow_z_waga_minus_jeden` | jw. dla konta hamowania |
| `Reszta_wzgledna_hamowania_przy_zerowym_ubytku_energii_jest_zerem` | granica z drugim mianownikiem |
| `Skrocenie_drogi_przez_opory_to_praca_oporow_przez_sile_hamowania` | 1000 J / (100 kg · 2 m/s²) = 5 m; dwa razy cięższy skład albo mocniejszy hamulec — połowa metrów |
| `Skrocenie_drogi_odrzuca_opoznienie_niedodatnie_i_nieskonczone` | **zero, ujemne, NaN, ∞ odrzucone**; `double.Epsilon` jeszcze przyjęte — próg odcina zero, a nie „wszystko, co małe" |
| `Skrocenie_drogi_odrzuca_mase_niedodatnia_i_nieskonczona` | jw. dla masy, z nazwą parametru w wyjątku |
| `Wiersz_konta_hamowania_nie_zalezy_od_kultury_maszyny` | jw. |
| `Wiersz_zalozenia_projektowego_niesie_nazwe_wartosc_sciezke_i_powod` | wszystkie cztery pola w wierszu katalogu — bez powodu audyt jest listą liczb bez pochodzenia |
| `Wartosc_zalozenia_wypisuje_sie_bez_straty_precyzji` | format `R`: 1/3 wypisane i odczytane z powrotem to ten sam `double` co do bitu |
| `Caly_katalog_zalozen_M7_wypisuje_sie_w_kulturze_niezmiennej` | wszystkie ≥16 wpisów M7, wartość każdego odczytuje się kulturą niezmienną |

**`SpeedProfileTests`** (11)

| test | co przybija |
|---|---|
| `Profil_pusty_ma_zerowy_szczyt_i_zerowy_odstep_probkowania` | szczyt zera próbek to **0,0**, nie minus nieskończoność |
| `Profil_pusty_nie_znajduje_zadnej_probki_takze_dla_progu_zerowego` | próg 0 na pustym profilu to nadal `null` |
| `Przebieg_bez_probkowania_oddaje_profil_pusty` | obserwacja wyłączona znaczy wyłączona |
| `Profil_jednoprobkowy_ma_szczyt_rowny_swojej_jedynej_probce` | jedna próbka jest jednocześnie pierwszą i ostatnią |
| `Prog_rowny_predkosci_probki_jest_progiem_osiagnietym` | „co najmniej" znaczy `>=`; próg wyżej o **jeden ULP** już nie trafia |
| `Szczyt_profilu_hamowania_stoi_na_poczatku_a_nie_na_ostatniej_probce` | szczyt to maksimum, nie ostatnia próbka — hamowanie kończy się na zerze |
| `Znaleziona_jest_pierwsza_probka_nad_progiem_a_nie_dowolna` | próbka bezpośrednio poprzedzająca jest jeszcze pod progiem |
| `Prog_powyzej_szczytu_nie_znajduje_nic_takze_na_profilu_niepustym` | „nic nie znalazłem" ≠ „oddam ostatnią" |
| `Profil_pamieta_zadany_odstep_probkowania` | 60, 1, 0 |
| `Probka_przelicza_metry_na_sekunde_na_kilometry_na_godzine` | kierunek przeliczenia |
| `Wiersz_probki_nie_zalezy_od_kultury_maszyny` | jw. |

Profil **jednopróbkowy** wymagał obejścia, bo konstruktor `SpeedProfile` jest `internal`,
a testy nie widzą wnętrza `MetroBxl.Sim` (projekt nie ma `InternalsVisibleTo`). Bierze się
go z przebiegu z limitem czasu `0.0` s: `StepsWithin(0.0)` daje `maxSteps = 0`, pętla
całkowania nie robi ani jednego kroku, w buforze zostaje sama próbka startowa. To nie jest
sztuczka pod test — to najkrótszy przebieg, jaki publiczne API rdzenia potrafi zwrócić.

**`MovementAuthorityTests`** (14)

| test | co przybija |
|---|---|
| `Odleglosc_authority_liczy_sie_od_czola_skladu_do_jego_konca` | kierunek odejmowania |
| `Odleglosc_authority_nigdy_nie_jest_ujemna` | authority za czołem składu daje 0, a nie metry ujemne, które poszłyby do krzywej hamowania |
| `Prawo_jazdy_gasnie_dokladnie_przy_zerowej_odleglosci` | zero to zakaz, jeden ULP powyżej to już pozwolenie |
| `Wiersz_authority_niesie_powod_i_blok_ograniczajacy_niezaleznie_od_kultury` | powód jest częścią authority, nie komentarzem |
| `Blok_jest_polotwarty_poczatek_nalezy_koniec_juz_nie` | `[Start, End)` sprawdzone co do ULP z obu stron obu granic |
| `Blok_podaje_swoja_dlugosc_i_role` | długość i `IsPlatform` |
| `Przeciecie_ze_skladem_dziedziczy_polotwartosc_granic` | skład kończący się na początku bloku jeszcze go nie zajmuje; zaczynający się na końcu już go opuścił |
| `Odcinek_zdegenerowany_do_punktu_dziala_jak_zawieranie` | punkt zachowuje się jak `Contains` na **pięciu** chainage'ach, w tym na obu granicach |
| `Odcinek_odwrocony_jest_odrzucony_a_nie_uznany_za_pusty` | granica: odcinek zdegenerowany jeszcze poprawny, krótszy o jeden ULP już nie |
| `Wiersz_bloku_niesie_granice_dlugosc_i_role` | blok szlakowy nie dopisuje sobie stacji |
| `Trasy_sa_w_konflikcie_dokladnie_wtedy_gdy_dziela_blok` | symetria relacji i konflikt trasy ze sobą samą |
| `Identyfikatory_blokow_porownuja_sie_dokladnie` | `Ordinal`: `P01` i `p01` to dwa różne bloki |
| `Konflikt_z_trasa_bez_listy_blokow_jest_odrzucony_nazwanym_wyjatkiem` | `default(Route)` ma `BlockIds == null` — nazwany wyjątek, nie `NullReferenceException` z wnętrza pętli |
| `Wiersz_trasy_niesie_konce_i_pelna_liste_blokow` | kolejność końców |

## 4. Kontrole negatywne — 39 mutacji, wszystkie wykonane

Metoda: jedna mutacja kodu produkcyjnego na raz, uruchomienie zestawu zawężonego do
klasy testowej, zapis wypisu, **natychmiastowe** przywrócenie pliku (także gdy `dotnet
test` się wywali). Przed nałożeniem mutacji skrypt sprawdza, że wzorzec występuje
w pliku dokładnie raz — inaczej podmieniałby coś innego, niż twierdzi.

Zapadka pokrycia: **39 z 39 nowych testów padło pod co najmniej jedną mutacją**, i żadna
mutacja nie przeszła bez ofiary. Wynik pomiaru pokrycia:

```
testow napisanych: 39
testow zabitych przez kontrole: 39
BEZ KONTROLI: []
zabite spoza listy: []
```

| # | plik | mutacja | co padło |
|---|---|---|---|
| M1 | `EnergyAccount.cs` | człon obcięcia wypada z bilansu | `Reszta_bilansu_odejmuje…`, `Reszta_wzgledna_jest_nieujemna…` |
| M2 | `EnergyAccount.cs` | miara względna traci `Math.Abs` licznika | `Reszta_wzgledna_jest_nieujemna…` |
| M3 | `EnergyAccount.cs` | zdjęta zapadka zerowej pracy trakcji | `Reszta_wzgledna_przy_zerowej_pracy_trakcji…` |
| M4 | `EnergyAccount.cs` | kWh przez 3600 zamiast 3,6 mln | `Praca_trakcji_w_kilowatogodzinach…`, `Wiersz_konta_rozruchu…` |
| M5 | `EnergyAccount.cs` | `InvariantCulture` → `CurrentCulture` | `Wiersz_konta_rozruchu…` |
| M6 | `BrakingEnergyAccount.cs` | człon dyskretyzacji wypada z bilansu | `Reszta_bilansu_hamowania…`, `Reszta_wzgledna_hamowania…` |
| M7 | `BrakingEnergyAccount.cs` | zdjęta zapadka zerowego ubytku energii | `Reszta_wzgledna_hamowania…` |
| M8 | `BrakingEnergyAccount.cs` | siła hamowania jako suma zamiast iloczynu | `Skrocenie_drogi_przez_opory…` |
| M9 | `BrakingEnergyAccount.cs` | `<= 0.0` → `< 0.0` na opóźnieniu | `Skrocenie_drogi_odrzuca_opoznienie…` |
| M10 | `BrakingEnergyAccount.cs` | `<= 0.0` → `< 0.0` na masie | `Skrocenie_drogi_odrzuca_mase…` |
| M11 | `BrakingEnergyAccount.cs` | `InvariantCulture` → `CurrentCulture` | `Wiersz_konta_hamowania…` |
| M12 | `DesignParameter.cs` | `{Value:R}` → `{Value:F2}` | `Wartosc_zalozenia_wypisuje_sie_bez_straty_precyzji` |
| M13 | `DesignParameter.cs` | powód znika z wiersza | `Wiersz_zalozenia_projektowego…` |
| M14 | `DesignParameter.cs` | `InvariantCulture` → `CurrentCulture` | `Caly_katalog_zalozen_M7…` |
| M15 | `SpeedProfile.cs` | szczyt startuje od minus nieskończoności | `Profil_pusty_ma_zerowy_szczyt…`, `Przebieg_bez_probkowania…` |
| M16 | `SpeedProfile.cs` | pusty profil oddaje próbkę zerową zamiast `null` | `Profil_pusty_nie_znajduje_zadnej_probki…` |
| M17 | `SpeedProfile.cs` | nieosiągnięty próg oddaje ostatnią próbkę | `Prog_powyzej_szczytu…`, `Prog_rowny_predkosci_probki…` |
| M18 | `SpeedProfile.cs` | szczyt bez porównania — zostaje ostatnia próbka | `Szczyt_profilu_hamowania…` |
| M19 | `ServiceBrakingRun.cs` | próbka startowa z zerową prędkością | `Probka_przelicza…`, `Profil_jednoprobkowy…`, `Szczyt_profilu_hamowania…`, `Wiersz_probki…` |
| M20 | `SpeedProfile.cs` | `>=` → `>` w `FirstAtLeast` | `Prog_rowny_predkosci_probki…` |
| M21 | `SpeedProfile.cs` | przeszukiwanie profilu od końca | `Znaleziona_jest_pierwsza_probka…` |
| M22 | `SpeedProfile.cs` | profil zapomina odstęp próbkowania | `Profil_pamieta…`, `Profil_pusty_ma_zerowy_szczyt…`, `Przebieg_bez_probkowania…` |
| M23 | `SpeedProfile.cs` | `MpsToKmh` → `KmhToMps` | `Probka_przelicza…`, `Wiersz_probki…` |
| M24 | `SpeedProfile.cs` | `InvariantCulture` → `CurrentCulture` | `Wiersz_probki…` |
| M25 | `MovementAuthority.cs` | odległość liczona od końca do czoła | `Odleglosc_authority_liczy…`, `Odleglosc_authority_nigdy_nie_jest_ujemna`, `Prawo_jazdy_gasnie…`, `Wiersz_authority…` |
| M26 | `MovementAuthority.cs` | zdjęte `Math.Max(0.0, …)` | `Odleglosc_authority_nigdy_nie_jest_ujemna` |
| M27 | `MovementAuthority.cs` | `> 0.0` → `>= 0.0` w `AllowsMovement` | `Odleglosc_authority_nigdy_nie_jest_ujemna`, `Prawo_jazdy_gasnie…` |
| M28 | `MovementAuthority.cs` | `InvariantCulture` → `CurrentCulture` | `Wiersz_authority…` |
| M29 | `Block.cs` | `Contains` domknięty z prawej | `Blok_jest_polotwarty…`, `Odcinek_zdegenerowany…` |
| M30 | `Block.cs` | długość z zamienionymi końcami | `Blok_podaje_swoja_dlugosc_i_role` |
| M31 | `Block.cs` | odwrócona rola bloku | `Blok_podaje_swoja_dlugosc_i_role` |
| M32 | `Block.cs` | przecięcie domknięte na obu granicach | `Przeciecie_ze_skladem…` |
| M33 | `Block.cs` | odcinek zdegenerowany nie zajmuje niczego | `Odcinek_odwrocony…`, `Odcinek_zdegenerowany…` |
| M34 | `Block.cs` | zdjęta zapadka odcinka odwróconego | `Odcinek_odwrocony…` |
| M35 | `Block.cs` | `InvariantCulture` → `CurrentCulture` | `Wiersz_bloku…` |
| M36 | `Block.cs` | wspólny blok przestaje być konfliktem | `Identyfikatory_blokow…`, `Trasy_sa_w_konflikcie…` |
| M37 | `Block.cs` | `Ordinal` → `OrdinalIgnoreCase` | `Identyfikatory_blokow…` |
| M38 | `Block.cs` | zdjęta zapadka trasy bez listy bloków | `Konflikt_z_trasa_bez_listy_blokow…` |
| M39 | `Block.cs` | końce trasy zamienione miejscami | `Wiersz_trasy…` |

### Cztery wypisy w całości

**M3** — zdjęta zapadka zerowej pracy trakcji. To ta mutacja, dla której cały
`EnergyAndProfileTests` pozostaje zielony: żaden przebieg nie ma zerowej pracy trakcji,
więc dzielenie przez zero widać dopiero od strony typu.

```
    TractionWorkJ == 0.0 ? 0.0 : Math.Abs(ResidualJ) / Math.Abs(TractionWorkJ);
 -> Math.Abs(ResidualJ) / Math.Abs(TractionWorkJ);

  Failed Reszta_wzgledna_przy_zerowej_pracy_trakcji_jest_zerem_a_nie_nieskonczonoscia [8 ms]
  Error Message:
   Assert.AreEqual failed. Expected a difference no greater than <0> between expected value <0> and actual value <Infinity>.
  Stack Trace:
     at MetroBxl.Sim.Tests.EnergyAccountTests.Reszta_wzgledna_przy_zerowej_pracy_trakcji_jest_zerem_a_nie_nieskonczonoscia()
        in tests/Sim.Tests/EnergyAccountTests.cs:line 132
```

**M9** — zerowe opóźnienie przepuszczone przez zapadkę (wymienione wprost w polu
**Skończone, gdy** pozycji 6.A8).

```
    if (!double.IsFinite(decelerationMps2) || decelerationMps2 <= 0.0)
 -> if (!double.IsFinite(decelerationMps2) || decelerationMps2 < 0.0)

  Failed Skrocenie_drogi_odrzuca_opoznienie_niedodatnie_i_nieskonczone [8 ms]
  Error Message:
   Assert.ThrowsException failed. No exception thrown. ArgumentOutOfRangeException exception was expected.
   opóźnienie 0 zostało przyjęte
  Stack Trace:
     at MetroBxl.Sim.Tests.EnergyAccountTests.Skrocenie_drogi_odrzuca_opoznienie_niedodatnie_i_nieskonczone()
        in tests/Sim.Tests/EnergyAccountTests.cs:line 236
```

**M20** — `FirstAtLeast` przestaje znaczyć „co najmniej".

```
    if (sample.SpeedMps >= speedMps)
 -> if (sample.SpeedMps > speedMps)

  Failed Prog_rowny_predkosci_probki_jest_progiem_osiagnietym [9 ms]
  Error Message:
   Assert.IsNotNull failed.
  Stack Trace:
     at MetroBxl.Sim.Tests.SpeedProfileTests.Prog_rowny_predkosci_probki_jest_progiem_osiagnietym()
        in tests/Sim.Tests/SpeedProfileTests.cs:line 126
```

**M29** — blok domknięty z prawej, czyli granica należąca do dwóch bloków naraz.

```
    public bool Contains(double chainageM) => chainageM >= StartM && chainageM < EndM;
 -> public bool Contains(double chainageM) => chainageM >= StartM && chainageM <= EndM;

  Failed Blok_jest_polotwarty_poczatek_nalezy_koniec_juz_nie [9 ms]
  Error Message:
   Assert.IsFalse failed. koniec należy już do bloku następnego
  Stack Trace:
     at MetroBxl.Sim.Tests.MovementAuthorityTests.Blok_jest_polotwarty_poczatek_nalezy_koniec_juz_nie()
        in tests/Sim.Tests/MovementAuthorityTests.cs:line 129
  Failed Odcinek_zdegenerowany_do_punktu_dziala_jak_zawieranie [< 1 ms]
  Error Message:
   Assert.IsFalse failed. punkt na końcu bloku leży już w następnym
  Stack Trace:
     at MetroBxl.Sim.Tests.MovementAuthorityTests.Odcinek_zdegenerowany_do_punktu_dziala_jak_zawieranie()
        in tests/Sim.Tests/MovementAuthorityTests.cs:line 177
```

### Czego ta seria nie mierzy

Każda mutacja była uruchamiana z `--filter` zawężonym do jednej z trzech nowych klas.
Wiersz „zabite spoza listy: []" mówi więc, że w obrębie **tych klas** nie padło nic
poza zamierzonym testem — nie mówi nic o tym, czy mutacja zabiłaby też któryś
z 455 testów wcześniejszych. To był świadomy wybór ceny: pełny przebieg razy 39 mutacji
to około pół godziny zamiast siedmiu minut, a pytanie, na które ta seria odpowiada,
brzmi „czy nowy test wykrywa zepsuty kod", a nie „ile testów łącznie go wykrywa".

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py
  1633/1633 przeszło

$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   494, Skipped:     0, Total:   494, Duration: 29 s
         - MetroBxl.Sim.Tests.dll (net10.0)
```

455 → 494, czyli **39 dopisanych testów**, zero zmian w liczbie testów `tools/`.

```
$ git status --short
?? tests/Sim.Tests/EnergyAccountTests.cs
?? tests/Sim.Tests/MovementAuthorityTests.cs
?? tests/Sim.Tests/SpeedProfileTests.cs
```

## 6. Czego świadomie nie zrobiono

* **`docs/TASKS.md` nie jest ruszony.** Pole *Poza zakresem* pozycji 6.A8 mówi „commit
  zawiera wyłącznie `tests/` i ten plik", ale adnotację w kolejce dopisuje właściciel —
  równolegle idą inne gałęzie i wpis do tego samego pliku byłby konfliktem u trzech naraz.
* **Licznik z pola Weryfikacja nie jest poprawiony w kolejce.** Fakt z §1 — że po
  `dotnet test` wypisuje fałszywe zero — jest tu zapisany, ale zmiana treści pozycji
  należy do właściciela, nie do gałęzi, która tę pozycję wykonuje.
* **Nazwa tego pliku jest wyborem, nie odczytem.** Pole **Wyjście** pozycji 6.A8 wymienia
  trzy pliki testowe i **ani jednego raportu**, więc nazwy nie było skąd wziąć; `reports/typy-sim-bez-testu.md`
  jest dobrane pod treść, a nie pod pole.
* **Ani znaku w `src/Sim/`.** Testy nie wykryły w tych sześciu typach żadnego błędu, więc
  nie było czego zgłaszać ani poprawiać — wszystkie 39 przeszło na kodzie zastanym za
  pierwszym uruchomieniem.

## 7. Co widać przy okazji, ale nie tknięto

* **`SpeedProfile` nie da się zbudować z testu.** Konstruktor jest `internal`, projekt
  nie ma `InternalsVisibleTo`, więc każdy profil w tych testach musi przyjść z prawdziwego
  przebiegu — łącznie z jednopróbkowym, wyciągniętym limitem czasu `0.0` s. Działa, ale
  jest to obejście, a nie API.
* **`SpeedProfile.NewBuffer` jest `internal` i nikt go nie testuje.** Waliduje ujemny
  odstęp próbkowania, tyle że tę samą walidację ma osobno każdy z trzech przebiegów
  (`AccelerationRun`, `ServiceBrakingRun`, `BrakingRun`) — czyli sprawdzenie stoi
  w czterech miejscach naraz. Nie ruszane: to zmiana w `src/Sim/`.
* **`AuthorityLimit.EndOfLine` i `AuthorityLimit.BlockNotReserved`** nie występują
  w żadnym z nowych testów, bo wybór powodu należy do `FixedBlockSystem`, a nie do samego
  `MovementAuthority`.
