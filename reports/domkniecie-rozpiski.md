# 5.6 — domknięcie sekcji „Czego brakuje w tej rozpisce"

**Zmierzone 08.09.2026 na commicie:** `b2df576fd6539d9dba478b221231342a778b9508`

Pozycja miała przenieść fakty, a nie wykonać pracę. Przeniesienie faktów pokazało, że
**trzy twierdzenia były nieprawdziwe** — dwa w samej sekcji, jedno we własnym bloku
pozycji. To jest cała treść tego raportu; sama edycja pliku jest przy tym drobna.

## 1. Co sekcja mówiła i co jest w drzewie

Sekcja otwierała się zdaniem: „Poniższe zadania istnieją jako Issues, ale nie mają tu
wpisu. Dopóki go nie mają, **Issues są jedynym źródłem prawdy** o ich zakresie".

| pozycja | Issue | stan Issue | wpis w planie przed zmianą |
|---|---|---|---|
| T-114 | #13 | zamknięty | **brak** |
| R-002 | #11 | zamknięty | **brak** |
| R-003 | #15 | **OTWARTY** | **brak** |
| R-004 | #16 | **OTWARTY** | **brak** |
| R-005 | #17 | **OTWARTY** | **brak** |
| R-006 | **nie ma** | — | **brak** |
| R-007 | **nie ma** | — | **brak** |
| T-401 | **nie ma** | — | **brak** |
| T-901 | #29 | otwarty | wiersz w „Czego agent nie ruszy bez decyzji" |

Lista Issues wzięta w całości: **36** pozycji, `hasNextPage: false`. To jest istotne,
bo wniosek „Issue nie ma" wolno postawić tylko z listy kompletnej, nie z wyszukiwania.

## 2. Pomyłka pierwsza: trzy z dziewięciu nie mają Issue wcale

R-006, R-007 i T-401 nie mają Issue w tym repozytorium. Zdanie otwierające sekcję —
„istnieją jako Issues" i „Issues są jedynym źródłem prawdy o ich zakresie" — było więc
dla nich nie tylko nieaktualne, ale **niewykonalne**: nie ma czego czytać.

Numery, które sekcja podawała (`#34, #90, #35, #85, #82`), to **pull requesty**, nie
Issues. Issue R-003 to #15, R-004 to #16, R-005 to #17. Zbieżność formy `#N` zatarła
różnicę między „praca weszła tym PR-em" i „zakres jest w tym Issue".

## 3. Pomyłka druga: „są w main" przy Issue nadal otwartym

Sekcja twierdziła: „**R-003, R-004, R-005, R-006 i R-007 są w `main`**". Dokumenty
faktycznie są w drzewie:

- R-003 → `docs/10-signalling-ground-truth.md`, `docs/16-protection-modes.md`
- R-004 → `docs/11-station-ground-truth.md`, `data/stations/package-a.json`,
  `reports/package-a-station-source-gaps.md`
- R-005 → `docs/12-infrastructure-ground-truth.md`, `data/infrastructure/metro-system.json`
- R-006 → `reports/R-006-line-speed.md`
- R-007 → `reports/R-007-platform-dimensions.md`

Ale Issues **#15, #16 i #17 są otwarte**. Dwa stany, które łatwo pomylić, i tylko jeden
z nich sekcja opisywała: „dokument jest w drzewie" nie znaczy „pytanie zamknięte".
Treścią tych dokumentów jest **granica wiedzy**, i ta granica jest wynikiem, nie brakiem:

- R-004: **260 z 696** kopert faktów pakietu A ma status `unknown`, a raport nazywa się
  wprost „lista dziur, nie lista osiągnięć". Największa pojedyncza dziura: typ komunikacji
  pionowej nieznany dla **118 z tych 260**, bo jedynym źródłem wyjść jest GTFS.
- R-005: **900 V** i **trzecia szyna** są `observed`; rozstaw 1435 mm zostaje
  `secondary_reference_only`, a `contact_geometry` w `data/network/lines.json` jest
  `unknown`. Pytania, których dokument nie domyka — przekrój tunelu drążonego i szerokość
  `box_double` — są w drzewie nazwane jako należące do R-005 w pięciu miejscach
  (m.in. `reports/M7-curve-clearance.md`, `reports/L1_A-track-spacing.md`) i **nie mają
  publicznego źródła**.

Dlatego wpisy R-003, R-004 i R-005 **niosą informację o otwartym Issue**, zamiast ją
zamykać. Cudzych Issues agent nie zamyka, a przemilczenie rozjazdu byłoby tą samą
usterką, którą ta pozycja właśnie naprawia, tylko o poziom wyżej.

## 4. Pomyłka trzecia, we własnym bloku pozycji

Blok 5.6 liczył: „Zmierzone 06.09.2026: z tych siedmiu **pięć jest już w `main`** …
Do dopisania zostaje więc **R-002**, a resztę sekcji zamyka przeniesienie faktów".

W drzewie **żadna z ośmiu pozycji nie miała wpisu `###`** — ani T-114, ani T-401, ani
R-002…R-007. Pomiar z 06.09.2026 był poprawny, ale dotyczył **innej wielkości**: tego, co
weszło do `main`, a nie tego, czy plan to zapisuje. Prognoza „zostaje R-002" wyszła
z pomylenia tych dwóch rzeczy i zaniżyła zakres ośmiokrotnie.

Liczba pozycji też była zaniżona: pole mówiło „siedem", licząc `R-002 … R-007` jako
jedną. To **sześć** osobnych pozycji o sześciu zakresach i — jak wyżej — trzech różnych
stanach. Razem z T-114, T-401 i T-901 daje **dziewięć**.

## 5. Pole „Weryfikacja" było niespełnialne z zasady

Pierwotne polecenie:

```bash
grep -n "Czego brakuje w tej rozpisce" docs/TASKS.md
```

z oczekiwaniem „**nic nie zwraca**". Tego nie da się spełnić: pozycja zamykająca tę
sekcję **nazywa się jej nazwą**, więc jej własny wiersz kolejki i jej własny blok zawsze
ten wzorzec dopasują. Po poprawnie wykonanej pracy `grep` zwraca dziś **siedem**
wierszy, i wszystkie należą do wiersza albo bloku 5.6 — sprawdzone przejściem po
numerach wierszy wobec granic bloku, nie oglądnięciem listy:

```
$ grep -c "Czego brakuje w tej rozpisce" docs/TASKS.md
7
wzmianki poza wierszem i blokiem 5.6: brak
```

Liczbę tę podałem najpierw jako sześć i było to o jeden za mało: sam wiersz oznaczony
`ZROBIONE` wymienia nazwę sekcji jeszcze raz, więc domknięcie pozycji **podnosi** licznik.
To dodatkowy powód, dla którego pierwotne, niezakotwiczone sprawdzenie nie mogło działać.

Bramka nie została osłabiona, tylko **przekierowana na zachowanie, w tym samym commicie**,
i po przekierowaniu sprawdza **więcej** niż przed: osobno nagłówek sekcji, osobno zdanie,
na którym cała pozycja stała, i osobno komplet wpisów.

```
$ grep -n '^## Czego brakuje w tej rozpisce' docs/TASKS.md
  (nic — sekcji nie ma)

$ grep -c '^### \[x\] \(T-114\|T-401\|R-00[2-7]\) ·' docs/TASKS.md
8
```

Dziewiąta pozycja, T-901, ma wiersz w „Czego agent nie ruszy bez decyzji" i wpisu `[x]`
mieć nie powinna — jest pozycją właściciela.

## 5a. Dwie kontrole negatywne WYKONANE

Przekierowana bramka jest warta tyle, ile jej zdolność do sczerwienienia. Obie kontrole
wykonane na drzewie i przywrócone; stan po przywróceniu sprawdzony, nie założony.

**KN-1 — sekcja wraca.** Wstawiony nagłówek `## Czego brakuje w tej rozpisce` z atrapą
treści:

```
508:## Czego brakuje w tej rozpisce
  ZNALAZL — bramka umie sczerwieniec
```

Zakotwiczony `grep` znajduje ją natychmiast, czyli sprawdza to, po co powstał.

**KN-2 — ginie jeden wpis.** Usunięty wpis `### [x] R-005`:

```
  licznik wpisow: 7
```

Licznik spada z 8 na 7, więc drugi warunek też nie jest ozdobą. Po przywróceniu: 8 wpisów
i 0 nagłówków sekcji.

Kontrole nie mutowały `.py`, więc pułapka nieświeżego bajtkodu z 6.D41 tu nie zachodzi —
mimo to stan po przywróceniu jest zmierzony oba razy.

## 6. Czego świadomie NIE zrobiłem

- **Nie zamknąłem Issues #15, #16 ani #17.** Zakaz jest wprost; rozjazd jest zapisany
  w trzech wpisach.
- **Nie wykonałem żadnej z dziewięciu pozycji.** Pole „Poza zakresem" mówi to wprost.
  W szczególności nie próbowałem domknąć pytań R-005 — nie mają publicznego źródła.
- **Nie zmieniłem zdania o tym, że Issues są źródłem prawdy o zakresie.** Pozycja
  usuwa wyjątek, nie regułę. Dla R-006, R-007 i T-401 zapisałem jednak, że tego wyjątku
  nie było czym wypełnić, bo Issue nie istnieje.
- **Nie tknąłem `doctor.sh`.** Sprawdzone, że go to nie dotyczy: szuka `^### \[ \]`
  i `^| [56].N |`, a wszystkie dopisane wpisy są `[x]`.
- **Nie tknąłem tabeli „Co blokuje co, w jednym miejscu"** ani akapitu o `doctor.sh`
  pod nią — usunięta jest wyłącznie sekcja wymieniona w polu „Wyjście".

## 7. Zauważone przy okazji, nietknięte

Akapit pod tabelą „Co blokuje co" mówi, że fazy 5 i 6 trzymają **31 pozycji**. Dziś
`open_items` daje **13**, a liczba w akapicie nie jest przez nic pilnowana — to ta sama
rodzina co zapadki, tylko bez zapadki. Nie ruszam jej: liczba w prozie planu to inna
pozycja niż ta, i poprawianie jej przy okazji łamałoby §4.10.
