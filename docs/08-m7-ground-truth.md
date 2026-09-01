# M7 — ground truth i granice modelu

Stan audytu: **2026-08-31**. Canonical registry: `data/vehicle/m7-spec.json`.

## Źródła pierwotne

- STIB/MIVB, 13.07.2020 — `https://stib.prezly.com/le-nouveau-metro-m7-est-arrive-a-bruxelles`
- STIB/MIVB, 26.05.2021 — `https://stib.prezly.com/les-voyageurs-pourront-bientot-monter-dans-le-nouveau-metro-m7`

Pierwsza karta techniczna STIB podaje długość 94 m, szerokość 2,70 m, wysokość podłogi 1,03 m, 6 członów, 18 podwójnych drzwi na stronę, 2 pojedyncze drzwi przy stanowiskach prowadzenia, otwarcie drzwi 1,60 m, pojemność 742/758, masę pustego składu około 170 t oraz 16 silników po 135 kW z trakcją asynchroniczną trójfazową i odzyskiem energii hamowania.

## Rejestr parametrów

| parametr | wartość | status | źródło / uwagi |
|---|---:|---|---|
| człony | 6 | `spec` | STIB 13.07.2020 |
| długość | 94,0 m | `spec` | STIB 13.07.2020 |
| szerokość | 2,70 m | `spec` | STIB 13.07.2020 |
| wysokość podłogi | 1,03 m | `spec` | STIB 13.07.2020 |
| podwójne drzwi / strona | 18 | `spec` | STIB 13.07.2020 |
| pojedyncze drzwi kabinowe | 2 | `spec` | STIB 13.07.2020 |
| szerokość otwarcia | 1,60 m | `spec` | STIB 13.07.2020 |
| pojemność manualna | 742 osób | `spec` | STIB 13.07.2020; nie jest to definicja AW2 |
| pojemność automatyczna | 758 osób | `spec` | STIB 13.07.2020 |
| masa AW0 | ~170 t | `spec` | STIB 13.07.2020; źródło podaje wartość przybliżoną |
| silniki trakcyjne | 16 × 135 kW | `spec` | STIB 13.07.2020 |
| moc zainstalowana | 2160 kW | `spec` | pochodna 16 × 135 kW |
| technologia trakcji | asynchroniczna trójfazowa | `spec` | STIB 13.07.2020 |
| odzysk energii hamowania | tak | `spec` | STIB 13.07.2020 |
| maks. prędkość pojazdu 80 km/h | 80 km/h | `design_model` | brak potwierdzonego w tym audycie źródła pierwotnego |
| napędzane 4/6 | 4/6 | `design_model` | historyczne założenie modelu; nie awansuje do spec |
| F0 | 248,9 kN | `design_model` | kalibracja modelu |
| hamowanie służbowe | 1,10 m/s² | `design_model` | brak źródła pierwotnego |
| hamowanie awaryjne | 1,30 m/s² | `design_model` | brak źródła pierwotnego |
| jerk | 0,75 m/s³ | `design_model` | brak źródła pierwotnego |

## Migracja masy AW0 i modelu obciążenia

Stary model używał `AW0 = 155 000 kg`. To było oznaczone jako `est`, ale jest sprzeczne z kartą STIB podającą około 170 t. Canonical AW0 został więc zmieniony na `170 000 kg` z flagą `approximate: true`.

Nie istnieje potwierdzona publicznie definicja ani masa AW2 M7. Dlatego repo **nie przejmuje** starej różnicy `206,94 - 155 = 51,94 t` jako rzekomego faktu. Do testowego modelu obciążenia przyjęto jawnie projektowe `742 pasażerów × 70 kg`, co daje `221 940 kg`. Ta wartość ma status `design_model` i może zostać wymieniona bez naruszania danych źródłowych.

## Migracja mocy i punktu przejścia F→P

Stary `reference.py` liczył stałą moc jako `248,9 kN × 35 km/h`, czyli około **2419,9 kW**. To koliduje z oficjalną mocą zainstalowaną STIB: **2160 kW**.

Po migracji:
- limit mocy modelu = `2160 kW` (`spec` jako moc zainstalowana);
- `F0 = 248,9 kN` pozostaje `design_model`;
- punkt przejścia modelu siła stała → moc stała jest pochodny: `2160 kW / 248,9 kN = 8,678 m/s = 31,24 km/h`;
- nie twierdzimy, że 31,24 km/h jest rzeczywistą prędkością bazową M7. To wyłącznie konsekwencja połączenia source-backed limitu mocy z projektowym F0.

## Wpływ na referencyjne przebiegi

Dla obecnego modelu i `dt = 1/120 s`:

| przypadek | przed | po |
|---|---:|---:|
| AW0 | 155,0 t `est` | ~170,0 t `spec` |
| AW2 | 206,94 t `est` | 221,94 t `design_model` |
| moc modelu | ~2419,9 kW `design` | 2160 kW `spec` limit |
| transition speed | 35,0 km/h `design` | 31,24 km/h `derived design_model` |
| 0→80 km/h AW0 | model historyczny | 25,2 s / 337,5 m |
| 0→80 km/h AW2 | model historyczny | 33,3 s / 447,9 m |
| service brake 80→0 | bez wpływu masy w obecnej abstrakcji | 20,9 s / 240,5 m |

Wartości czasu i drogi są snapshotem **modelu projektowego**, a nie pomiarem osiągów STIB.

## Nadal nieznane

Bez źródła pierwotnego pozostają: konstrukcyjny Vmax M7, układ napędzanych osi/członów, rzeczywista charakterystyka siła–prędkość i F0, maksymalne przyspieszenie, service/emergency braking, jerk, oficjalna definicja i masa AW2, adhezja, współczynniki Davis/oporu tunelowego, rozkład masy/naciski osi oraz geometria wózków.

Te pola mogą być używane w symulatorze tylko jako `design_model` i muszą pozostawać łatwo wymienne.