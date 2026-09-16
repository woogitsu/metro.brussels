# 6.D243 — pakiet, o który nikt nie pyta, nie zainstaluje się nigdy

**16.09.2026**, na `bac8789`. Wejście: `.github/workflows/godot-first-run.yml`, pozostałe
sześć workflowów z sondą bibliotek, `tools/ci/apt-packages/blender.txt`,
`blender-xvfb.txt`, `tools/tests/test_ci_workflows.py`, log joba 104730275817.
Wyjście: dwa sonames w siedmiu kopiach sondy, dwa pakiety w obu zestawach apt,
bramka w kierunku ODWROTNYM i lista wyjątków z powodami, ten raport.

---

## 1. Co padło

`first-run` padł na kroku **41** `Line run — a shot at the platform must show open doors`:

```
libXcursor.so.1: cannot open shared object file: No such file or directory
ERROR: Can't load XCursor dynamically.
libwayland-cursor.so.0: cannot open shared object file: No such file or directory
ERROR: Unable to create DisplayServer, all display drivers failed.
```

Kroki **1–40** — cały łańcuch porównań rdzeń↔scena, bramki ATP, `Engine layer unit tests`
**318/318** — przeszły. Krok 41 jest **pierwszym, który woła silnik z serwerem
wyświetlania** zamiast headless; wcześniej kursor nie jest potrzebny.

**To jest czerwone na `main`, nie na gałęzi.** Sprawdzone przeze mnie przez API:
run **35065478579**, `head_branch: "main"`, `head_sha: bac8789`,
`runner_name: docker-runner-04`, krok 41 `conclusion: failure`.

`grep -rn "xcursor\|wayland" tools/ci/apt-packages/ .github/workflows/godot-first-run.yml`
przed tą pozycją: **zero trafień**. Sonda pytała o dziesięć bibliotek i tej brakującej
wśród nich nie było.

**Piąty raz ta sama klasa**, po `unzip` (kod 127, 07.09.2026), `curl` (6.D77),
`python3-yaml` (6.D240) i `xz` (6.D242).

## 2. Czego 6.D242 nie zamknęło, i to jest sedno tej pozycji

Gdyby ktoś zauważył brak i dopisał **sam pakiet** do zestawu apt, **naprawa byłaby
pozorna, a drzewo milczałoby tak samo**. Zmierzone kontrolą negatywną KN-3: zdjęcie
obu sonames z **wszystkich siedmiu** sond przy pakietach zostawionych w obu zestawach
dawało **88/88 na zielono** — a jest to konfiguracja, w której pakiet stoi na liście
i **nie zainstaluje się nigdy**, bo instalacja odpala się warunkowo
(`if: steps.tools.outputs.libs == 'missing'`), a sonda niepytająca o nic z tej
biblioteki melduje `present`.

Wiązanie było **jednokierunkowe**: `test_tool_installation_is_conditional_on_the_tool_being_missing`
pyta, czy zestaw instaluje to, o co sonda pyta. Nikt nie pytał w drugą stronę.

## 3. Co weszło

- `libXcursor.so.1` i `libwayland-cursor.so.0` w **siedmiu** kopiach sondy,
  `libxcursor1` i `libwayland-cursor0` w **obu** zestawach apt.
- `test_kazdy_pakiet_zestawu_apt_jest_O_COS_PYTANY_przez_sonde` — kierunek odwrotny.
- `PAKIETY_BEZ_SONDY` — lista wyjątków **z powodami**, dziś jednoelementowa, oraz
  `test_lista_pakietow_bez_sondy_NIE_jest_workaroundem`, który żąda powodu dłuższego
  niż 60 znaków i obecności pakietu w jakimkolwiek zestawie.

**Dlaczego sonames idą do wszystkich siedmiu kopii, choć kursora potrzebuje jeden job.**
Identyczność wszystkich kopii jest **ochroną z 6.D44**, a nie porządkiem: rozluźnienie
jej do „każda kopia jest nadzbiorem bazy" otwiera z powrotem dziurę, przez którą
**zawężona** sonda melduje `present` i pomija instalację. Dwa pakiety więcej na maszynie,
która kursora nie używa, kosztują mniej niż ta dziura. Zmierzone: KN-1 pokazuje, że
zdjęcie sonamu z jednej kopii zapala bramkę 6.D44.

**Jedyny wyjątek i jego powód.** `libgl1-mesa-dri` nie dostarcza **ani jednego** pliku
`libGL.so*` — `dpkg -L` daje zero dopasowań; wozi wyłącznie sterowniki DRI ładowane
przez `libGL.so.1` w czasie pracy (zmierzone 07.09.2026,
`reports/biblioteki-startowe-blendera.md`). Sondy na soname postawić się na nim nie da.

## 4. Kontrole negatywne — sześć, przewidywania zapisane przed przebiegiem

Baza modułu przed nową bramką **88/88**, po niej **90/90**. Przywracanie **z archiwum
w scratchpadzie**, nie przez `git checkout --`. `md5sum -c` **OK** po każdej.

| # | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | soname zdjęty z JEDNEGO workflowa | 86/88 | **87/88** |
| KN-2 | `libxcursor1` zdjęty z `blender.txt` | 87/88 | **87/88** |
| KN-3 | oba sonames zdjęte ze WSZYSTKICH sond, pakiety zostają | 87/88 | **88/88** |
| KN-4 | `libwayland-cursor0` zdjęty z OBU zestawów | 87/88 | **87/88** |
| KN-3′ | to samo co KN-3, już z nową bramką | 88/90 | **89/90** |
| KN-5 | wyjątek `libgl1-mesa-dri` zdjęty z listy | 88/90 | **88/90** |
| KN-6 | powód wyjątku skrócony do dwóch słów | 89/90 | **89/90** |

**KN-3 obaliła przewidywanie i jest przez to najważniejsza z siedmiu.** Spodziewałem
się czerwieni; wyszło **88/88 na zielono** — i to jest cała treść tej pozycji. Ta jedna
liczba pokazała, że wiązanie było jednokierunkowe, i z niej wzięła się druga bramka.
Po jej dodaniu ta sama mutacja daje **89/90**.

KN-5 i KN-6 pilnują, żeby lista wyjątków nie stała się wyłącznikiem: pusta lista zapala
osobną asercję, a powód krótszy niż 60 znaków **nie jest powodem, tylko zgodą**.

## 5. Weryfikacja

```
  2495/2495 przeszło
  RAZEM 212.740 s, 2495 testów, 126 modułów
```

## 6. Czego świadomie nie zrobiłem

Nie instalowałem niczego na maszynach właściciela (§8); nie tknąłem etykiet `runs-on`
ani składu puli (`CLAUDE.md` §9); nie dokładałem sonames, których pomiar nie nazwał —
log wymienia dokładnie dwa i tylko te dwa weszły.

**Nie rozstrzygnąłem, dlaczego `tools` bywa czerwony na tych samych maszynach.**
To osobna sprawa: próg CPU zestawu jest skalibrowany na puli `metro-wsl-DOM-NEW-*`,
a na `docker-runner-*` zestaw kosztuje ok. trzy razy więcej CPU. Wszystkie znane
warianty zmieniają **znaczenie** progu, nie jego wartość, więc jest to decyzja
właściciela i idzie osobną pozycją.
