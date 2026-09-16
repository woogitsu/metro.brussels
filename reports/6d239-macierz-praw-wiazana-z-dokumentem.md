# 6.D239 — macierz praw wiązana z dokumentem, i wyjątek, który da się sprawdzić

**16.09.2026**, na `a0dbd79`. Wejście: `data/legal/rights-matrix.json`
(`package_a_artworks`), `docs/18-rights-matrix.md` (tabela „Dzieła sztuki — pakiet A"),
`tools/tests/test_rights_matrix.py`. Wyjście: nowy moduł
`tools/tests/test_rights_matrix_doc.py`, przeliczone zapadki liczby modułów, ten raport.

Decyzja właściciela z tego dnia: **bramka + ten jeden wpis jako wyjątek Z POWODEM**.

## 1. Czego pilnuje

Osiemnaście wpisów `package_a_artworks` ma odpowiadać osiemnastu wierszom tabeli w doc18,
w obie strony. Dotąd nie pilnowało tego **nic**: skreślenie wiersza z dokumentu albo
dopisanie tam dzieła, którego rejestr nie zna, przechodziło na zielono.

**Bramka nie rozstrzyga niczego o prawach autorskich.** Pilnuje wyłącznie spójności
zapisu między `data/` a dokumentem; status prawny zostaje w `data/legal/rights-matrix.json`
i `docs/03-legal.md`, których ten moduł tylko **czyta**. Czyta z nich sześć pól
(`station_id`, `station`, `work`, `creator`, `inventory_state`, `source_url`) i nie dotyka
`rights_holder`, `status`, `policy_default` ani `contributor_policy`.

## 2. Wyjątek jest JEDEN, nazwany, i WERYFIKOWALNY

`gare_centrale` / `enamel-panel corridor artwork` / Daniel Deltour — jedyny wpis, którego
tytułu doc18 nie niesie dosłownie, bo opisuje go polską prozą („praca w emaliowanych
panelach w korytarzu łączącym kolej–metro").

6.D243 pokazało, że **lista wyjątków, której nikt nie sprawdza, jest napisem**. Ten
wyjątek niesie więc cztery warunki sprawdzane w drzewie:

1. **musi wskazywać ISTNIEJĄCY wiersz rejestru** — dokładnie jeden;
2. **musi być POTRZEBNY** — tytuł z rejestru NIE MOŻE stać w doc18 dosłownie; gdy ktoś go
   dopisze, bramka żąda zdjęcia wyjątku;
3. **musi stać na UNIKALNYM stanie inwentarza** — `identified_shared_corridor` opisuje
   w pakiecie A dokładnie jeden wiersz;
4. **musi trafiać w komórkę, która NIE JEST TYTUŁEM** — doc18 składa tytuły w grawisach,
   komórka wyjątku jest prozą bez nich. To jedyny z czterech warunków, który **nie jest
   pinem na tekście**: pyta o strukturę dokumentu, więc przeżywa przeredagowanie.

Wyjątek **nie wyłącza wiersza ze sprawdzania** — podmienia oczekiwany tekst na inny,
równie dosłownie sprawdzany.

## 3. Czytnik tabeli wybrany POMIAREM, nie gustem

Pierwsza wersja czytała region od nagłówka `##` do następnego `##`. Zmierzone na
**204 sekcjach `##` w `docs/`** (26 plików), gdzie „awaria" znaczy: czytnik zwraca coś
innego niż wiersze zamierzonej tabeli:

```
sekcji `## ` razem: 204,  z tego z podsekcja `### `: 43
rozklad liczby ZWARTYCH BLOKOW `|` w sekcji: {0: 151, 1: 36, 2: 12, 3: 3, 5: 1, 19: 1}

A (przerwij na ###)        — SCALA dwie sasiednie tabele w:  7 z 204 sekcji
B (pierwszy zwarty blok)   — UCINA ogon tabeli w:            1 z 204 sekcji
C (zlozenie A+B)           — ucina ogon w tej samej:         1 z 204 sekcji
```

Wybrane **C**: region kończy się na nagłówku **dowolnego** poziomu, a z regionu bierze się
**pierwszy zwarty blok** wierszy `|`. Wobec A: 0 zamiast **7** sekcji nadmiarowego
wciągnięcia. Wobec B: remis w liczbie (1 do 1), ale region C **zawiera się** w regionie B,
więc C nie potrafi paść tam, gdzie B stoi.

**Granica stoi przy czytniku LICZBĄ, a nie przykładem z głowy**, i to jest poprawka
wyciągnięta z 6.D228 tego samego dnia: tamta granica opisywała nagłówek, którego w katalogu
nie ma **ani razu**, podczas gdy prawdziwa kosztowała 32 sekcje. Tryb awarii C jest
wypisany: tabela pakietu A rozbita pustym wierszem albo nagłówkiem `###` **w środku**
zostanie przycięta i zapali zapadkę `POZYCJI_W_PAKIECIE_A`, czyli **głośno**. W dzisiejszym
doc18 takich rozbić jest **zero**.

## 4. Trzy usterki znalezione przed wejściem

**(a) Zapalenie na DANYCH POPRAWNYCH — blokujące.** doc18 **już dziś** niesie wewnątrz
sekcji pakietu A podsekcję `### Źródła inwentarza dzieł`. Przy czytniku zatrzymującym się
tylko na `##` każda tabela dopisana w tej podsekcji — ruch czysto redakcyjny, o zerowym
związku z prawami — dawała **3 FAIL**. To jest 6.D27 w czystej postaci, a bramka
zapalająca się na poprawnej redakcji zostaje wyłączona, nie naprawiona.

**(b) ŚLEPOTA porównania.** Porównanie szło na `set()`, więc rejestr i doc18 opisujące
**różne** zbiory dawały **13/13 na zielono**, dopóki liczności się zgadzały. Zasłaniała to
wyłącznie zapadka — a zapadka jest od tego, żeby ją podnosić. Zamienione na `Counter`,
czyli krotność zamiast obecności.

**(c) `IndexError` zamiast werdyktu.** Pięć czerwieni szło przez `[...][0]` i kończyło się
komunikatem `list index out of range`, który czytającemu nie mówi nic. Zastąpione jawnym
`_wpis_objety()` z komunikatem nazywającym wpis i powód.

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Wszystkie mutacje na **pełnej kopii drzewa**, nie w repozytorium: `data/legal/` i
`docs/18-rights-matrix.md` są tylko do odczytu (§4.6), a kontrola, która je modyfikuje
i przywraca, zostawia okno, w którym przerwany przebieg strandowałby zmieniony plik.
Sumy `md5sum` trzech plików chronionych w prawdziwym drzewie: **OK przed i po**.

Baza: **16/16**.

| | mutacja | PRZEWIDZIANE | ZMIERZONE |
|---|---|---|---|
| KN-1 | tabela w podsekcji `###` — **DANE POPRAWNE** | 16/16 | **16/16** (przed naprawą 3 FAIL) |
| KN-2 | duplikaty o RÓŻNEJ treści po obu stronach, zapadka 19 | czerwone | **14/16**, obie niezgodne pozycje nazwane (ze `set()` było 13/13 ZIELONE) |
| KN-3 | wiersz USUNIĘTY z doc18 — **kontrola dodatnia** | czerwone | **14/16**, nazwane dzieło |

KN-1 i KN-3 razem są tu treścią: pierwsza mówi, że naprawa czytnika **nie** zapala się na
pracy poprawnej, druga — że **nie oślepiła** bramki. Sama KN-2 nie wystarczyłaby, bo
bramka zielona na poprawnej redakcji i tak zostałaby wyłączona.

## 6. Koszty zapisane, nie przemilczane

Bramka **zapala się** na trzech rodzajach zmian poprawnych i jest to świadomy koszt tego,
że wyjątek ma być jeden i weryfikowalny:

- **przeredagowanie polskiego opisu** wiersza objętego wyjątkiem (3 FAIL) — warunek
  „doc18 niesie DOKŁADNIE ten opis" nie ma słabszej postaci, która nadal coś sprawdza;
- **drugie dzieło bez zapisanego tytułu** (4 FAIL) — komunikat **nazywa to decyzją
  właściciela** i zatrzymuje się, zamiast milcząco blokować;
- **tytuł złożony pogrubieniem zamiast grawisów** (3 FAIL) — bramka przybija doc18 do
  jednego sposobu składu.

Docstring `test_wyjatek_stoi_na_komorce_ktora_NIE_JEST_TYTULEM` obiecywał wcześniej, że
moduł „przetrwa przeredagowanie opisu". **Przetrwała jedna asercja, trzy inne nie** —
obietnica została zawężona do tego, co bramka robi.

## 7. Weryfikacja

```
KOD=0
  <pełny zestaw — liczby z przebiegu wyłącznego>
```

Moduły sąsiednie, każdy osobno: `test_rights_matrix_doc.py` 16/16, plus
`test_bytecode_staleness.py`, `test_prose_counts.py`, `test_assertion_gate.py`,
`test_tree_walks.py`, `test_report_hygiene.py`, `test_report_claims.py` — **148/148**.

Zapadki ruszone przez **dodanie modułu**, każda przeliczona z drzewa:
`MODULOW_W_CALYM_DRZEWIE` i `BAJTKOD_PO_COMPILEALL_PLIKI` stoją teraz na **207**, proza
rozkładu `tools/tests` na **136**, zdanie o liczbie modułów w `test_all.py` na **128**,
oraz te same liczby w `docs/06-worked-example.md`. `ASERCJI_NAPISOWYCH_RAZEM` **bez
zmian** — wszystkie `in`/`not in` nowego modułu mają po lewej **zmienną odczytaną
z drzewa**, nie literał, więc czytnik ich nie liczy; sprawdzone przyrządem repozytorium.
`MIN_REPORTS` rośnie o jeden za ten raport.

## 8. Czego świadomie nie zrobiłem

- **Nie tknąłem `data/legal/rights-matrix.json`, `docs/18-rights-matrix.md` ani
  `docs/03-legal.md`** — wszystkie mutacje na kopii drzewa, sumy sprawdzone.
- **Nie rozstrzygałem drugiego dzieła bez tytułu.** Gdy takie się pojawi, ktoś musi
  zdecydować, czy wyjątek zostaje pojedynczy, czy powstaje kategoria z własnym
  `inventory_state` w `data/`. Bramka wypisuje to w komunikacie i się zatrzymuje (§8).
- **Nie poszerzyłem czytnika na tabelę rozbitą pustym wierszem** — jedyny taki kształt
  w korpusie stoi w `docs/21-measured-vs-assumed.md` i jest poza zakresem tej pozycji;
  granica jest wypisana przy czytniku.

## 9. Co zauważyłem przy okazji, ale nie tknąłem

- **Dwa wpisy rejestru mają termin, który właśnie minął.** `Fietsersportretten`
  (De Brouckère) i `Pourquoi Bruxelles…` (Schuman) noszą
  `identified_temporary_presence_requires_2026_check` z notatką „verify whether it
  physically exists on **2026-08-31**". Dziś jest 16.09.2026 — weryfikacja jest wymagalna.
  To zmiana w `data/`, czyli decyzja właściciela, nie moja.
- **`docs/18-rights-matrix.md` nie stoi w Mapie dokumentów `CLAUDE.md` §3** — dokładnie
  przypadek opisany w 6.D170.
- **Zapadka `POZYCJI_W_PAKIECIE_A` nie wchodzi do rejestru `test_tree_walks.ZAPADKI`**, bo
  rozpoznanie kształtu idzie po przedrostku `MAX_`/`MIN_`/`MINIMUM_`. Nie jest to naruszenie
  reguły, ale jest to zapadka stojąca poza rejestrem zapadek.
- **`docs/TASKS.md` `## Plan` ma 19 zwartych bloków `|` w jednej sekcji `##`**, a
  `docs/15-classic-signalling.md` `## 5. Movement authority` — pięć. Każda przyszła bramka
  czytająca tabele z `docs/` po nagłówku `##` wpadnie w ten sam kształt.
