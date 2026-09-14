# 6.D205 — log kosztuje 30 kB, nie 290, a dwa przebiegi nie weszły z zupełnie innego powodu

**14.09.2026**, na `8e9f830`. Wejście: `tools/tests/test_suite_runtime_budget.py`
(`POMIARY_RUNNERA`, `MIN_WPISOW_RUNNERA`, `MEASURED_MAX_WALL_S`, `MARGIN`),
`tools/tests/test_timing_record.py`, `tests/data/ci-logs/README.md`,
`reports/6d190-fakt-historyczny-obok-kontroli-zywej.md`, logi jobów `tools`
PR-ów #579–#582 (jeszcze pobieralne z GitHuba).

## 1. Koszt krańcowy — liczba, której żądało pole „Wyjście"

Dwanaście pustych repozytoriów, logi dokładane po jednym w kolejności tabeli README,
`git gc --aggressive --prune=now` po każdym, mierzony katalog `objects/pack`:

| logów | plik | pack | **krańcowo** | w katalogu roboczym |
|---:|---|---:|---:|---:|
| 1 | `tools-pr524` | 73 374 B | 73 374 B | 295 887 B |
| 2 | `tools-pr525` | 105 598 B | 32 224 B | 297 624 B |
| 3 | `tools-pr526` | 137 581 B | 31 983 B | 297 125 B |
| 4 | `tools-pr527` | 169 217 B | 31 636 B | 299 420 B |
| 5 | `tools-pr528` | 201 739 B | 32 522 B | 299 948 B |
| 6 | `tools-pr529` | 233 543 B | 31 804 B | 299 496 B |
| 7 | `tools-pr571` | 268 557 B | 35 014 B | 285 957 B |
| 8 | `tools-pr583` | 301 745 B | **33 188 B** | 289 016 B |
| 9 | `tools-pr579` | 331 888 B | **30 143 B** | 286 666 B |
| 10 | `tools-pr580` | 363 458 B | 31 570 B | 287 179 B |
| 11 | `tools-pr581` | 395 655 B | 32 197 B | 288 098 B |
| 12 | `tools-pr582` | 427 099 B | 31 444 B | 287 344 B |

**Ósmy log kosztuje 33 188 B, dziewiąty 30 143 B** — czyli dokładnie to, o co pytało
pole „Skończone, gdy", po `git gc`, a nie z rozmiaru pliku. Koszt krańcowy to
**ok. jedna dziewiąta** rozmiaru w katalogu roboczym; przyjęcie 290 KB na wpis, przed
którym pozycja ostrzegała, zawyżyłoby go **dziewięciokrotnie**.

Pomiar zgadza się z tym, co README podawało od 6.D152: sześć logów daje **233 543 B**
wobec zapisanych tam **234 858 B**. Różnica 1 315 B to niepowtarzalność samego
pakowania — ten sam zestaw sześciu w dwóch przebiegach mojego skryptu dał 233 550
i 233 543 B.

**Pierwszy log jest drogi (73 374 B), każdy następny nie.** To jest cała treść tej
tabeli: delta między logami tego samego joba zdejmuje 89 % i robi to od drugiego pliku.

## 2. Reguła doboru — i dlaczego NIE brzmi „koszt jest mały, zapisujmy każdy"

Koszt z sekcji 1 usuwa argument przeciw zapisywaniu, ale nie jest argumentem za.
Drugi pomiar: runner wykonał **25** (11.09), **29** (12.09) i **31** (13.09)
przebiegów `python-tests.yml` z pull requestów — w sumie **834** zakończonych
przebiegów tego workflowa. „Zapisujemy każdy" to **ok. 1 MB historii dziennie**.

Reguła stoi w `tests/data/ci-logs/README.md` i ma trzy punkty obowiązkowe, każdy
wyprowadzony z **bramki, która na tej liście stoi**:

1. **nowe maksimum ściany** — `MEASURED_MAX_WALL_S` jest z listy wyprowadzane;
2. **maszyna, której lista nie zna** — nazwy maszyn czyta z logów
   `test_slowo_runner_stoi_nad_DWIEMA_maszynami_ale_ich_NIE_rozdziela`;
3. **nowy skrajny stosunek CPU/ściana** — na jego zakresie stoi
   `test_runner_liczy_rownolegle_a_kontener_szeregowo`, czyli rozstrzygnięcie 6.D149.

Każdy inny przebieg wolno dopisać i żadnego nie trzeba.

**Reguły nie da się sprawdzić wykonaniem i to jest zapisane, a nie obejście.** Mówi
o przebiegach, których w drzewie NIE MA, a zestaw testów do GitHuba nie sięga. Pole
„Weryfikacja" dopuszcza wprost drugą drogę — „zdanie, które bramka cytuje" — i tą
drogą poszła `test_regula_doboru_przebiegow_stoi_w_drzewie_RAZEM_ze_swoimi_liczbami`:
cytuje pięć zdań reguły, sprawdza, że obie nazwy bramek, na które reguła się powołuje,
**istnieją w module**, i porównuje liczbę kosztu w README ze stałą
`KOSZT_KRANCOWY_LOGU_B`.

## 3. Czy #579–#582 wchodzą: DWA TAK, DWA NIE — i te dwa są zablokowane

Wszystkie cztery logi pobrane; wpisy **wypisane** przez `tools/ci/timing_record.py
--z-logu`, nie z ręki. Numer PR-u narzędzie bierze z samego logu
(`refs/remotes/pull/<N>/merge`), więc przypisanie przebiegu do pozycji jest zmierzone,
a nie wywnioskowane z kolejności.

| PR | pozycja | ściana | CPU/ściana | maszyna | wchodzi? |
|---|---|---:|---:|---|---|
| #579 | 6.D185 | 108,369 s | 1,813 | `-02` | **nie** — poniżej maksimum, maszyna znana |
| #580 | 6.D186 | **130,046 s** | 1,509 | `-02` | **TAK** — nowe maksimum |
| #581 | 6.D187 | **130,982 s** | **1,453** | **`-03`** | **TAK** — wszystkie trzy punkty naraz |
| #582 | 6.D188 | 111,701 s | 1,796 | `-02` | **nie** |

Maksimum listy to dziś **116,404 s** (11.09.2026). Oba przebiegi z 13.09 leżą **14,6 s
wyżej** i zostały pominięte — dokładnie tak, jak pozycja przewidywała, że dobór
nieopisany działa.

**Wejścia NIE wykonałem, i powód jest zmierzony, a nie przewidziany.** Oba wpisy razem
z logami wstawione do osobnego drzewa roboczego (`git worktree`) dają **28/32** —
czerwone są **cztery** asercje, nie jedna:

```
FAIL test_budget_stays_above_the_measured_maximum_with_a_real_margin: (1.1451955230489685, 150.0, 130.982)
FAIL test_jeden_prog_dla_obu_maszyn_przestalby_widziec_regres_na_runnerze: prog wspolny wypadlby 196.8 s, czyli 1.502x maksimum runnera — pomiar z 13.09.2026 dal 221,4 s i 1,902x
FAIL test_runner_liczy_rownolegle_a_kontener_szeregowo: runner przestal byc wyraznie szybszy od kontenera: [1.971, …, 1.509, 1.453] wobec 0.991
FAIL test_slowo_runner_stoi_nad_DWIEMA_maszynami_ale_ich_NIE_rozdziela: logi niosą 3 różnych maszyn, a zapadka stoi na 2 — trzecia maszyna wymaga przeliczenia rozstrzygnięcia, nie samego podniesienia liczby
```

`MARGIN` spada **1,2886 → 1,1452**, czyli poniżej progu `MARGIN > 1.2`. Naprawa każdej
z tych czterech jest zmianą **zapasu** albo przeliczeniem **rozstrzygnięcia 6.D149** —
czyli tym, co pole „Poza zakresem" tej pozycji wyklucza nazwanym słowem. Wiersz stoi
więc w „Czego agent nie ruszy bez decyzji", z liczbami i z identyfikatorami jobów.

**Nie jest to zjawisko z jednego dnia, i wyszło to z weryfikacji tej samej sesji.**
Job `tools` PR-u **#609** (6.D204, scalony 14.09.2026, `104138427419`) zmierzył ścianę
**131,757 s** przy stosunku CPU/ściana 1,493 — czyli **trzeci** przebieg powyżej
maksimum listy, tego samego dnia co ta pozycja, i pod regułą również obowiązkowy.
Blokuje go dokładnie to samo, co tamte dwa.

**Logów tych czterech przebiegów NIE zacommitowałem.** `test_kazdy_wpis_runnera_ma_log_w_drzewie`
żąda równości obu zbiorów, więc log bez wpisu zapaliłby bramkę tak samo jak wpis bez
logu. Identyfikatory jobów stoją w wierszu decyzji — póki GitHub ich nie wygasi, są
do pobrania jednym poleceniem z sekcji „Skąd".

## 4. Czego ta pozycja NIE odkryła, choć wyglądało, że odkrywa

Napisałem po drodze, że projekt „nie zna swojego maksimum ściany". **To nieprawda
i sprawdzenie zajęło jeden `grep`.** Dwieście wierszy niżej w tym samym module stoi
`POMIARY_CPU_BIEZACEGO_DRZEWA`, a w niej ściana **164,734 s** z runnera — powyżej
progu `SUITE_RUNTIME_BUDGET_S = 150.0` — i liczy to
`test_prog_cpu_NIE_zapalilby_sie_na_zadnym_zmierzonym_przebiegu`, z asercją na
**dokładnie ten jeden** identyfikator artefaktu.

Maksimum ściany nie jest więc w projekcie nieznane. Jest **rozdzielone na dwie listy
o różnych warunkach wejścia**: `POMIARY` wymaga zacommitowanego logu joba (6.D152),
`POMIARY_CPU_BIEZACEGO_DRZEWA` bierze artefakt `czas-zestawu`, którego commitować nie
trzeba. Wyższa liczba siedzi w tańszej liście — i to, a nie niewiedza, jest powodem,
dla którego `MEASURED_MAX_WALL_S` mówi 116,404. Zdanie o tym stoi dziś **przy tej
stałej**, bo bez niego czyta się ją jako „najwyższa ściana, jaką runner zmierzył",
a jest to „najwyższa ściana, jaką ktoś tu zapisał".

## 5. Kontrole negatywne

Baza modułu: **33/33**. Po każdej `md5sum -c` na obu plikach: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | zdanie reguły znika z README | 32/33 |
| KN-2 | reguła powołuje się na bramkę o innej nazwie | 32/33 |
| KN-3 | liczba kosztu w README rozjeżdża się ze stałą (30 143 → 30 200) | 32/33 |
| KN-4 | cytowana bramka przemianowana **w module** | 32/33 |
| KN-5 | README skrócone do 2 200 znaków, ale ze wszystkimi zdaniami reguły | 32/33 |

**KN-5 jest tu dlatego, że kontrola przyrządu bez pomiaru bywa czwartym zdaniem
o tym samym** — przy 6.D204 tego samego dnia usunąłem dwie takie bramki. Tutaj
zmierzyłem: plik skrócony, ale niosący komplet zdań reguły, przechodzi wszystkie
asercje treściowe i zapala **wyłącznie** warunek długości. Łapie więc coś, czego nie
łapie nic innego w tej bramce, i dlatego zostaje.

## 6. Czego świadomie nie zrobiłem

- **Progu runnera, zapasu ani podłogi mierzalności nie ruszyłem** — pole „Poza
  zakresem". To jest powód, dla którego dwa przebiegi z sekcji 3 nie weszły.
- **Logów już leżących w drzewie nie kasowałem, spakowania nie wracałem** (to samo pole).
- **Nie dopisałem #579 ani #582**, choć wolno: reguła mówi „wolno, nie trzeba", a wpis
  dobrany dlatego, że akurat miałem plik, jest tym samym doborem nieopisanym, który ta
  pozycja zdejmuje.
- **Nie postawiłem bramki liczącej przebiegi runnera na GitHubie.** Zestaw testów nie
  ma sieci i mieć nie powinien; reguła jest zdaniem, które bramka cytuje.

## 7. Zauważone, nie tknięte

- **Trzecia maszyna puli (`metro-wsl-DOM-NEW-03`) wykonuje joby tego repozytorium,
  a moduł zna dwie.** Zapadka `test_slowo_runner_stoi_nad_DWIEMA_maszynami…` mówi
  wprost, że trzecia „wymaga przeliczenia rozstrzygnięcia, nie samego podniesienia
  liczby" — i to przeliczenie jest częścią wiersza decyzji.
- **`POMIARY_CPU_BIEZACEGO_DRZEWA` niesie osiem przebiegów o ścianie 121,671–164,734 s,
  a `POMIARY_RUNNERA` osiem o 89,518–116,404 s** — dwa rozłączne pasma tej samej
  maszyny i tego samego joba, rozdzielone wyłącznie tym, którą listę było taniej
  zasilić. Czy `MARGIN` liczone z uboższej listy w ogóle coś dziś znaczy, jest
  pytaniem, którego ta pozycja nie zadaje.
- **`MIN_WPISOW_RUNNERA` stoi na 6 przy ośmiu wpisach**, czyli ma dwa wpisy zapasu —
  po dopisaniu dwóch zablokowanych miałoby cztery. Podłoga z 6.D190 broni przed zerem
  i przed niczym więcej; to jest zapisane w jej komentarzu i nie jest usterką.
