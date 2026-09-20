# 6.D324 · Osiemnaście wzorców łapie identyfikator, ZERO wnioskuje z tego o przypisaniu — a mój pierwszy przyrząd mierzył moją wyobraźnię

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `8165b9c`

6.D312 §4 i §10 zapisało, że `L1_A`, `L1_B`, `L2_E`, `L5_C`, `L5_D`, `L6_F` i `F0_N`
mają kształt nazwy stałej, a są napisami — identyfikatorami odcinków. Ta pozycja
liczy, ile skanów tego repozytorium liczy je razem ze stałymi. **LICZY i żadnego
wzorca nie zmienia.**

Trzy liczby: **18 / 0 / 3**. Osiemnaście wzorców ze stu pięćdziesięciu siedmiu łapie
identyfikator w prawdziwym korpusie; **ani jeden nie wnioskuje z trafienia
o przypisaniu w kodzie**; trzy, które traktują trafienie jak nazwę stałej, mają przy
sobie odsianie — i to ono robi zero w liczbie drugiej.

Ale wynik, dla którego warto było tę pozycję wziąć, jest metodyczny: **pierwsza wersja
mojego przyrządu testowała wzorce na napisach, które sam wymyśliłem, i orzekła, że
kontrola przyrządu jest NIEZDANA. W prawdziwej prozie ten sam wzorzec łapie
pięćdziesiąt jeden razy.**

---

## 1. K0 — identyfikatory PRZECZYTANE, i pole wskazuje NIE TEN plik

Pole „Wejście" każe wziąć listę identyfikatorów z `data/network/lines.json`,
zastrzegając: **do PRZECZYTANIA, nie zgadnięcia**. Przeczytałem — **tego pliku
identyfikatory nie zawierają**: skan po napisach o kształcie ALLCAPS z podkreśleniem
daje w nim zero trafień.

Identyfikatory leżą gdzie indziej i tam je wziąłem — jako pliki w `data/track/`:

```
L1_A  L1_B  L2_E  L5_C  L5_D  L6_F
```

**Sześć, a nie siedem.** `F0_N` z siódemki 6.D312 **identyfikatorem odcinka nie
jest**: stoi w `tools/physics/reference.py` jako klucz `"F0_N": 248900.0`, czyli
**siła rozruchu w niutonach**, i pada tam w rachunku `installed_power_W / F0_N`.

Jest to drugi raz w tej sesji, gdy pole wskazuje wejście, którego treść leży gdzie
indziej — po „tabeli jednostek" z 6.D320, której w `docs/04-conventions.md` nie ma.
Zapisuję oba zamiast zgadywać za pole; `F0_N` wpisałem do kolejki jako 6.D331.

## 2. USTERKA METODYCZNA, którą sam sobie zrobiłem i która jest tu najważniejsza

Przyrząd pierwszej wersji budował dla każdego identyfikatora **trzy konteksty
z głowy** — goły (`L1_A`), w grawisach (`` `L1_A` ``) i przypisanie (`L1_A = 1`) —
i puszczał na nich każdy wzorzec. Wynik:

```
=== WZORCE LAPIACE IDENTYFIKATOR ODCINKA (7) ===
=== KONTROLA PRZYRZADU: CLAIM z test_report_claims.py ===
   CLAIM lapie: NIE LAPIE — kontrola NIEZDANA
```

Kontrola żądana przez pole **nie przeszła** — i gdybym na tym poprzestał, zapisałbym,
że `CLAIM` identyfikatora nie widzi. Przeczytałem więc wzorzec:

```
CLAIM = `([A-Z][A-Z0-9_]{3,})`([^`,→§#\n]{0,40}?)(-?\d+(?:[.,]\d+)?(?:e-?\d+)?)
```

`CLAIM` wymaga grawisu, ALLCAPS **i LICZBY**. Mój wymyślony kontekst „Proza wymienia
`L1_A` w zdaniu." liczby nie ma — więc nie mógł trafić. W prawdziwych raportach
liczba stoi tuż obok, bo identyfikatory żyją w **tabelach**:

```
TRAFIENIA CLAIM na identyfikatorze odcinka, w PRAWDZIWEJ prozie: 42
   reports/T-011-details-BF.md   L1_A   `L1_A` | 6686,4
   reports/T-211-stations-BF.md  L1_B   `L1_B` | 5083,5
```

**Zmyślony kontekst mierzy wyobraźnię autora, a nie drzewo.** Przepisałem przyrząd
na puszczanie wzorców po **prawdziwym korpusie** (165 plików, w których identyfikator
w ogóle pada) i liczba wzorców łapiących skoczyła z **7 na 18**.

**Uzasadnienie pola jest przy tym nieprawdziwe, a jego teza prawdziwa.** Pole pisze,
że `CLAIM` łapie, „bo wymaga wyłącznie grawisu i ALLCAPS". Wymaga też liczby — więc
powód jest zły. Ale łapie, i to pięćdziesiąt jeden razy. Podaję oba zdania osobno,
bo z samego „kontrola zdana" nie dałoby się zobaczyć, że jej uzasadnienie jest do
poprawienia.

## 3. LICZBA PIERWSZA: osiemnaście ze stu pięćdziesięciu siedmiu

```
wzorcow `NAZWA = re.compile(...)` na poziomie modulu w tools/tests/: 157
plikow korpusu, w ktorych pada identyfikator odcinka:               165

=== WZORCE LAPIACE IDENTYFIKATOR W PRAWDZIWYM KORPUSIE (18) ===
   test_dead_constants_csharp.py  IDENTYFIKATOR           w.236   np. L1_A
   test_docs_ci_claims.py         NEXT_LABEL              w.102   np. /L1_A.json
   test_field_paths.py            PATH_TOKEN              w.160   np. data/track/L1_A.json
   test_report_claims.py          ADRES_NIE_TWIERDZENIE   w.1833  np. data/track/L1_A.json
   test_report_hygiene.py         PATH_TOKEN              w.946   np. `data/track/L1_A.json`
   test_report_claims.py          ZAKRES_W_GRAWISACH      w.1964  np. `data/track/L1_A.json`
   test_report_hygiene.py         FENCE                   w.1330  np. CbtcTestSpan { AxisId = L1_A
   test_docs_map.py               WIERSZ_TABELI           w.71    np. | `L1_B.json` |
   test_report_claims.py          CLAIM                   w.85    np. `L5_D`: przebieg zimny **30
   test_prose_counts.py           PARA_NAZWA_LICZBA       w.878   np. `L1_A.glb` 887
   test_field_paths.py            MODULE_CALL             w.359   np. test_all.py test_report_claims
   test_dimension_audit.py        NAZWA_W_TABELI          w.255   np. | `L1_A` |
   backlog_commands.py            PLACEHOLDER             w.82    np. znaczniki `time.
   test_expected_exception.py     KLAUZULA                w.45    np. catch`. SZEŚĆ KONTROLI
   test_t401_citation.py          ROW                     w.56    np. | L1_A | 57,41 |
   test_t401_citation.py          WIERSZ_PELNY            w.176   np. | L1_A | 57,41 | **58,09**
   test_ci_workflows.py           REPLAY_CALL             w.3700  np. data/keys/L1_A-manual.json
   test_message_claims.py         ZAPOWIEDZ_POMIARU       w.1358  np. osi `data/track/L5_D.json`
```

**Trzynaście z osiemnastu łapie identyfikator jako część ŚCIEŻKI albo WIERSZA TABELI,
a nie jako nazwę.** Pole ostrzega przed uznaniem tego za usterkę i ostrzega słusznie:
skan pytający „czy proza wymienia ten adres" ma prawo zobaczyć `data/track/L1_A.json`,
bo ten plik naprawdę istnieje.

**Dwa wzorce, których kształt najbardziej zapraszał do pomyłki, nie łapią wcale:**
`PRZYPISANIE_STALEJ` z `test_message_claims.py` i `STALA_PY` z `test_value_chains.py`
żądają znaku równości po nazwie — a identyfikator odcinka nigdzie w tym drzewie nie
jest niczemu przypisywany. **Kształt stałej nie wystarcza; potrzebne jest jeszcze
przypisanie, a jego nie ma.**

## 4. LICZBA DRUGA: ZERO wnioskuje o przypisaniu — bo trzy, które mogłyby, ODSIEWAJĄ

Pole żąda powiedzieć wprost, ile wzorców wnioskuje z trafienia o **przypisaniu
w kodzie**, i dopuszcza odpowiedź „żaden" — wtedy kształt identyfikatora nikomu nie
szkodzi. **Jest „żaden", a droga do tego zera prowadzi przez trzy odsiania.**

Rozstrzygałem **czytaniem miejsca użycia**, nie kształtem wzorca, bo pole tak każe:

| wzorzec | czy traktuje trafienie jak nazwę stałej | co je odsiewa |
|---|---|---|
| `CLAIM` | **tak** — porównuje podaną wartość z wartością stałej | `if constant in values` — trafienie przechodzi dalej tylko wtedy, gdy nazwa **stoi w mapie stałych kodu**; `L5_D` w niej nie stoi |
| `NAZWA_W_TABELI` | **tak** — `nazwy_w_sekcji` zwraca „zbiór nazw stałych" i porównuje go bijekcją ze stałymi modułu | przedrostek `DESIGN_`: `nazwy_modulu` bierze wyłącznie `DESIGN_*`, a identyfikator go nie ma |
| `PARA_NAZWA_LICZBA` | **tak** — buduje pary „nazwa + liczba" pilnowane przez bramkę 6.D263 | `ODSYLACZ_PLIKU` — trafienie `` `L1_A.glb` 887 `` wypada jako odsyłacz pliku |

Pozostałych piętnaście pyta o **ścieżkę, wiersz tabeli, wywołanie modułu, płot bloku
kodu albo klauzulę `catch`** — żadne z tych pytań nie jest pytaniem o przypisanie.

**Zero jest więc POLICZONE, a nie założone, i ma zmierzoną przyczynę.** Gdyby
którekolwiek z trzech odsiań zniknęło, liczba przestałaby być zerem — i to jest
zdanie mocniejsze niż samo „nikomu nie szkodzi".

## 5. LICZBA TRZECIA: trzy odsiania, i każde INNEGO RODZAJU

To, co je odsiewa, warto wymienić osobno, bo **żadne z trzech nie jest listą
wyjątków** — a lista wyjątków jest w tym projekcie kształtem, który gnije (6.A31):

- `CLAIM` odsiewa **przez drzewo**: pyta mapy stałych zbudowanej z kodu.
- `NAZWA_W_TABELI` odsiewa **przez konwencję nazw**: przedrostek `DESIGN_`.
- `PARA_NAZWA_LICZBA` odsiewa **przez inny wzorzec**: `ODSYLACZ_PLIKU`.

Odsianie po drzewie starzeje się samo; odsianie po przedrostku starzeje się przy
zmianie konwencji; odsianie po wzorcu starzeje się razem z tamtym wzorcem. **Trzy
mechanizmy o trzech różnych terminach ważności — i żaden nie wymaga wpisania
`L1_A` z nazwy.**

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| V1 | kontrola przyrządu przejdzie — `CLAIM` łapie | **trafione dopiero w DRUGIEJ wersji przyrządu**, §2 |
| V2 | wzorców łapiących będzie więcej niż 5 | trafione — 18 |
| V3 | wnioskujących o przypisaniu będzie co najmniej 1 | **OBALONE** — zero |
| V4 | mających odsianie będzie MNIEJ niż wnioskujących | **OBALONE** — trzy wobec zera |
| V5 | żaden wzorzec nie złapie w kontekście gołym, nie łapiąc w grawisach | **NIEROZSTRZYGALNE** — konteksty zmyślone wypadły z pomiaru razem z pierwszą wersją przyrządu |
| V6 | „wnioskuje o przypisaniu" wymagać będzie czytania ≥3 miejsc użycia na wzorzec | trafione |

**V3 i V4 obalone razem, i to jest właściwy wynik:** spodziewałem się, że kształt
stałej komuś szkodzi. Nie szkodzi nikomu — ale nie dlatego, że nikt go nie łapie
(łapie osiemnaście wzorców), tylko dlatego, że **każdy, kto mógłby z niego wnioskować,
ma odsianie**. Warunek obalenia spisałem przed pomiarem i honoruję go: zapisuję
„kształt identyfikatora nikomu nie szkodzi", zamiast szukać innego sita.

**V5 zapisuję jako nierozstrzygalne, a nie jako pudło albo trafienie.** Postawiłem je
na kontekstach, które sam wymyśliłem; §2 pokazuje, że te konteksty mierzyły mnie,
a nie drzewo, więc odpowiedź oparta na nich nie byłaby odpowiedzią o repozytorium.
Jest to ten sam ruch, którym 6.D309 potraktowało swoje X7 i 6.D319 swoje Q6.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono ani jednego wzorca** i nie dopisano odsiewania identyfikatorów.
- **Nie postawiono bramki na wyniku** — §4 pokazuje, że nie ma czego pilnować.
- **Nie sprostowano bloku 6.D312 ani 6.D324** mimo `F0_N` i mimo `lines.json`;
  oba zapisane jako 6.D331, bo prostowanie cudzych bloków jest poza zakresem.
- **Nie policzono, ile razy identyfikator pada poza tymi osiemnastoma wzorcami.**
- **Nie tknięto `src/` ani `data/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Trzynaście z osiemnastu wzorców łapie identyfikator jako część ścieżki.**
   `data/track/L1_A.json` jest prawdziwym plikiem, więc te trafienia są poprawne —
   ale znaczy to, że każdy pomiar „ile nazw o kształcie stałej stoi w prozie" liczy
   razem z nimi **adresy plików**, a nie tylko nazwy.
2. **`PRZYPISANIE_STALEJ` i `STALA_PY` nie łapią identyfikatora ani razu**, mimo że
   ich kształt jest najbliższy nazwie stałej. Różnicę robi znak równości — czyli
   **jedyny element, którego identyfikator odcinka nie ma nigdzie w tym drzewie**.
3. **Korpus, w którym identyfikator w ogóle pada, to 165 plików.** Populacja 6.D312
   liczyła wystąpienia w prozie `tools/tests/`; ta pozycja pokazuje, że proza
   `tools/tests/` jest mniejszością miejsc, w których te nazwy żyją.
