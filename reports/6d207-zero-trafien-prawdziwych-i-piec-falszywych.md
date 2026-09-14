# 6.D207 — odsiać się NIE DA, i są to trzy liczby, nie ostrożność

**14.09.2026**, na `3d1223b`. Wejście: `tools/tests/test_report_claims.py`,
`tools/tests/test_prose_counts.py`, `tools/tests/test_suite_runtime_budget.py`
(docstring `test_zaden_wpis_nie_niesie_rangi_OTWARTEJ_w_tej_liscie`),
`reports/6d193-zdanie-trafione-a-nie-sprawdzone.md`, commit `a5e9ff0`.

## 1. Populacja — pierwsza liczba, której żądało pole „Wyjście"

| | |
|---|---:|
| docstringów w `tools/tests/` | 2489 |
| zdań **deklarujących** pomiar | **29** |
| z nich zdań o **cudzym** pomiarze (wzorzec „6.Dxxx zmierzyło") | **0** |
| deklaracji w docstringu modułu albo klasy (brak ciała do sprawdzenia) | 4 |
| funkcji **pomocniczych** z deklaracją i zerem asercji | **5** |
| funkcji **testowych** z deklaracją | 19 |
| z nich testowych z deklaracją i zerem asercji | **0** |

**Obawa z pola „Dlaczego to NIE jest łatwe" okazała się nietrafiona, i to jest
zmierzone:** pozycja przewidywała, że sito będzie mylić deklarację własnego pomiaru
ze zdaniem o pomiarze cudzym („6.D160 zmierzyło, że…"), „a tych drugich jest w tym
drzewie dużo". W docstringach `tools/tests/` nie ma **ani jednego** takiego zdania
wśród 29 trafień. Zdania o cudzych pomiarach stoją w tym drzewie gdzie indziej —
w polach „Skąd" `docs/TASKS.md` i w komentarzach `#:` — a docstring opisuje własną
bramkę. Sito przewróciło się więc na czymś innym.

## 2. Trafienia fałszywe: 5 na 5 — druga liczba

Jedyne sito, które da się napisać mechanicznie — *„docstring deklaruje pomiar,
a w ciele nie ma ani jednej asercji"* — zgłasza wyłącznie **pomocniki**:

```
tools/tests/mutation_sweep.py              pokrycie_w_celach
tools/tests/mutation_sweep.py              wiersze_starego_bajtkodu
tools/tests/test_docs_ci_claims.py         documents
tools/tests/test_mutation_sweep.py         _dziennik_testu
tools/tests/test_suite_runtime_budget.py   cpu_dzieci
```

Pomocnik bez asercji jest poprawny **z definicji**: liczy i zwraca, a sprawdza go
wołający. **Sto procent trafień jest fałszywych**, a bramka świecąca na poprawnym
tekście zostaje wyłączona, nie poprawiona (6.D27).

## 3. Trafienie pominięte: 1 na 1 — i ta liczba rozstrzyga

Sito jest **ślepe na przypadek, dla którego pozycję napisano**. W commicie, który
wprowadził zdanie *„Innych list pomiarów w drzewie NIE MA, i to jest zmierzone,
nie założone"* — `a5e9ff0`, 6.D163 — funkcja
`test_zaden_wpis_nie_niesie_rangi_OTWARTEJ_w_tej_liscie` miała **6 asercji**.
Sito powiedziałoby o niej „zielona" dokładnie tak samo, jak mówi dziś, gdy zdanie
jest już sprawdzane.

**Ten sam werdykt na wejściu poprawnym i na wadliwym** — rodzina 6.D75. Powód jest
prosty do wypowiedzenia i nie do zakodowania: zdanie deklaruje, że zmierzono
**konkretną** rzecz, a asercja obok mierzy **jakąś** rzecz. Związanie jednego
z drugim jest rozbiorem znaczenia zdania, a nie składni — czyli `CLAUDE.md` §8.

## 4. Trafień prawdziwych w dzisiejszym drzewie: ZERO — trzecia liczba

Jedyne znane w historii tego repozytorium **naprawiło 6.D193**: tamten docstring mówi
dziś „od 6.D193 jest to SPRAWDZANE, a nie przeczytane" i deklaracji pomiaru już nie
niesie — co sprawdziłem wykonaniem, bo mój wzorzec przestał go widzieć i **na tym
padła pierwsza wersja bramki**, którą napisałem z kotwicą w drzewie.

Sita nie da się więc sprawdzić na zbiorze trafień prawdziwych, bo taki zbiór jest
pusty. Stąd kształt bramki: **para syntetyczna** (dwie funkcje różniące się dokładnie
tym, czy deklarowany pomiar jest wykonywany — sito daje obu ten sam werdykt) plus
liczba wzięta z commita, który usterkę **wprowadził**, a nie z drzewa, które ją już
zabrało.

## 5. Co zostaje w drzewie

- `WZORZEC_DEKLARACJI_POMIARU` — łapie **zwroty**, nie słowo „zmierzone". Tym słowem
  zaczyna się w tym drzewie niemal każde pole „Skąd", co 6.D196 już zmierzyło na
  `HISTORICAL_MARKERS`.
- `MIN_DEKLARACJI_POMIARU = 22` — podłoga, nie równość: deklaracji przybywa z każdą
  pozycją, która coś zmierzy.
- `DEKLARACJE_BEZ_ASERCJI` — **zbiór pięciu pomocników**, bo to on, a nie liczba 5,
  niesie zdanie „100 % trafień fałszywych" (6.D131).
- `FUNKCJA_TRAFIENIA_POMINIETEGO` i `ASERCJI_W_COMMICIE_a5e9ff0 = 6` — liczba, na
  której stoi werdykt, razem z kotwicą sprawdzającą, że naprawa 6.D193 nadal stoi.

**Bramki „deklaracja bez asercji" NIE MA i nie będzie** — jest opisana, zmierzona
i odrzucona.

## 6. Kontrole negatywne

Baza modułu: **9/9**. Po każdej `md5sum -c` na obu plikach: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | pierwsza gałąź wzorca deklaracji zgniła | 8/9, populacja 29 → **17** |
| KN-2 | funkcja **testowa** z deklaracją i zerem asercji | 8/9 |
| KN-2b | to samo, puszczone przez **cały zestaw** | **2475/2479** |
| KN-3 | pomocnik skreślony ze zbioru trafień fałszywych | 8/9 |

**KN-2b zmieniła kod, i to jest jej cała wartość.** Pokazała, że na tym samym wejściu
zapala się także `test_kn2_deklaracja_bez_asercji: przeszedł bez wykonania ani jednej
asercji` — czyli bramka asercji z 6.D25. Moja asercja „żadna funkcja testowa nie stoi
tu bez asercji" byłaby więc **czwartym zdaniem o tym samym** i została **usunięta**;
porównanie zbioru, które zostaje, mówi więcej: nazywa funkcję i wiąże ją z werdyktem.
Jest to ta sama lekcja, którą tego samego dnia dostałem przy 6.D204, tylko tym razem
pomiar zrobiłem **przed** commitem, a nie po.

## 7. Czego świadomie nie zrobiłem

- **Nie przepisałem żadnego cudzego docstringu** — pole „Poza zakresem".
- **Nie rozszerzyłem skanu na `docs/` ani `reports/`** (to samo pole; raporty są
  historią).
- **`RODZINA_UBEZPIECZENIA` nietknięta** (to samo pole).
- **Nie postawiłem bramki na liczbie 29** — rośnie przy każdej pozycji, która coś
  zmierzy; przypięta jest podłogą.

## 8. Zauważone, nie tknięte

- **Cztery deklaracje stoją w docstringach MODUŁU albo KLASY**, gdzie „ciała do
  sprawdzenia" nie ma w ogóle — ani mojego sita, ani żadnego innego kryterium
  opartego na zakresie funkcji do nich nie da się przyłożyć. Ta pozycja liczy je
  osobno i nic z nimi nie robi.
- **Wzorzec deklaracji ma dziewięć gałęzi i wszystkie dobrałem ręcznie** z tego, co
  drzewo dziś pisze. Ile zwrotów deklarujących pomiar drzewo zna, a wzorzec nie
  widzi, nie jest zmierzone — KN-1 mówi tylko, że zgnicie **jednej** gałęzi zbija
  populację z 29 na 17.
- **`_dziennik_testu` jest pomocnikiem z podkreśleniem na początku, a `documents`
  i `cpu_dzieci` nie.** Konwencji nazywania pomocników w `tools/tests/` nie pilnuje
  nic; gdyby pilnowało, sito z sekcji 2 dałoby się zawęzić po nazwie, a nie po
  obecności asercji.
