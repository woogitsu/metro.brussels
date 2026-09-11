# 6.D125 — `cleared` bez daty: pole już istnieje, a dokument prawny daty nie żąda

**Zmierzone 11.09.2026 na:** `fdabff4`, kontener tej sesji.
**Przyrząd:** `data/audio/audio-manifest.schema.json` i `data/audio/placeholders.json`
(**wyłącznie do odczytu**), `tools/tests/test_audio_rights.py`, `docs/03-legal.md`
(do odczytu).

---

## 1. Pomiar, o który prosiło pole „Wyjście"

| liczba | wartość |
|---|---|
| wpisów w manifeście | **13** |
| ze statusem `cleared` | **0** |
| ze statusem `placeholder` | **13** (wszystkie) |
| niosących własne `as_of` | **0** |
| `as_of` w korzeniu manifestu | **`2026-08-31`** |

Zero wpisów `cleared` znaczy, że wymaganie daty nie dotknęłoby dziś **ani jednego**
wpisu. Pozycja mówiła o tym wprost i nazywała to argumentem w obie strony.

## 2. Czego pozycja nie wiedziała, a co rozstrzyga: pole już istnieje

Schemat ma `as_of` jako właściwość **opcjonalną**: `"type": ["string", "null"]`,
`"format": "date"`. Nie trzeba go więc **dodawać** — trzeba by go **wymagać**
w gałęzi `allOf[2].then`, czyli tej pod warunkiem `rights_status == "cleared"`.
Koszt to jedna linia — ale w pliku w `data/`, a pole „Wejście" tej pozycji oznacza
oba pliki jako tylko do odczytu i §4.6 mówi to samo.

## 3. Drugi powód jest mocniejszy od pierwszego: dokument prawny daty nie stawia

`docs/03-legal.md` **nigdzie** nie mówi o terminie ważności. Skan po `as_of`,
`termin`, `wygas`, `expire`, `ważność` — zero trafień. Co dokument mówi naprawdę:

* wiersz 3: „bez **pisemnej zgody potwierdzonej przez człowieka** albo bez
  jednoznacznej licencji obejmującej **konkretne zamierzone użycie**";
* wiersz 52: „Każdy zewnętrzny asset produkcyjny ma `source/licence/permission_ref`.
  Brak udokumentowanego prawa do zamierzonego użycia = neutralny oryginalny fallback
  albo wykluczenie assetu."

Wymaganiem jest **zakres**, nie data. Gałąź `cleared` w schemacie odwzorowuje ten
dokument **dokładnie**: zgoda `anyOf` licencja. Dopisanie do niej `as_of` byłoby
dołożeniem reguły, której dokument prawny projektu nie stawia — czyli **decyzją
właściciela**, a nie uzupełnieniem luki. Zdanie z pola „Skąd" tej pozycji („prawo
do dźwięku bywa terminowe") jest prawdą o świecie, ale nie jest zdaniem z
`docs/03-legal.md`, i ta różnica jest tu treścią.

## 4. Rozstrzygnięcie

Reguła stoi **w module testowym**, nie w schemacie: wpis `cleared` bez niepustego
`as_of` jest **zgłaszany** przez `brak_daty_obowiazywania`. Powody:

* kosztuje dziś **zero** (wpisów `cleared` nie ma) i nie rusza `data/`;
* mówi wprost, czego brakuje, w chwili gdy pierwszy taki wpis powstanie — KN-4
  pokazuje to wykonaniem;
* nie przesądza decyzji właściciela: przeniesienie reguły do schematu zostaje do
  wzięcia, z policzonym kosztem (jedna linia, zero dotkniętych wpisów).

**Co znaczy „cleared bez daty".** Znaczy „ktoś kiedyś to sprawdził". `as_of`
w korzeniu manifestu datuje **audyt pliku**, nie **prawo** — i te dwie rzeczy
rozjeżdżają się przy pierwszym wpisie dopisanym później niż korzeń. Zdanie stoi
w docstringu przy `POWOD_BRAKU_DATY`, czyli tam, gdzie przeczyta je ten, kogo
bramka zatrzyma.

## 5. Kontrola negatywna, która wyszła ZIELONA

**KN-5** zdjęła asercję `wpisy_cleared(manifest) == []` z testu bramki. Wynik:
**14/14, zielono**.

Mój docstring twierdził, że przed jałowością chronią „oba: asercja na pustkę
i wpisy syntetyczne". Nieprawda — chroni **wyłącznie blok syntetyczny**, bo on
wykonuje regułę niezależnie od zawartości manifestu. Asercja jest **drogowskazem
dla czytającego**: mówi w miejscu, w którym ktoś czyta pętlę po manifeście, dlaczego
ta pętla niczego nie dowiodła. Wartości tej liczby pilnuje osobno
`test_ile_wpisow_dotknelaby_data_obowiazywania` — i to tam jest bramka.

Docstring jest przepisany na prawdziwy. To trzecia zielona kontrola w tej sesji
i trzeci raz, gdy poprawka dotyczy **zdania o kodzie**, a nie kodu.

## 6. Kontrole negatywne — WYKONANE, nie opisane

Baza `test_audio_rights.py`: **14/14**.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | reguła nie patrzy na status (dotyczy wszystkich) | **13/14**, wszystkie 13 wpisów |
| KN-2 | pusty napis uznany za datę | **13/14** |
| KN-3 | reguła nic nie zgłasza (zawsze pusta lista) | **13/14** |
| KN-4 | wpis `cleared` bez daty **dopisany do manifestu** | **11/14**, trzy testy |
| KN-5 | asercja na pustkę zdjęta | **14/14 ZIELONA** — patrz §5 |

KN-4 jest tu decydująca: dopisuje do `placeholders.json` wpis, jakiego dziś nie ma,
i pokazuje, że bramka **naprawdę** go łapie — razem z `test_ile_wpisow…`, który
zauważa zmianę liczby, i z `test_audio_placeholders_are_neutral_and_non_stib`.

**Przywrócenie KN-4 poszło `git checkout`, a nie `cp` — i to jest odstępstwo od
procedury, więc mówię o nim wprost.** Plik leży w `data/`, którego ta pozycja nie
zmienia, więc kopii na boku nie zakładałem z góry. Stan po przywróceniu sprawdzony
**odciskiem SHA-256 wobec `HEAD`**, nie `md5sum -c` wobec kopii:
`304ccd5e38068957…` po obu stronach, `git status --short data/` pusty.

## 7. Czego nie zrobiłem

* **Nie zmieniłem ani schematu, ani manifestu** — oba w `data/`, oba oznaczone
  w „Wejściu" jako tylko do odczytu (§4.6).
* **Nie zmieniłem statusu żadnego wpisu** i nie dopisałem pól poza `as_of` — wprost
  w „Poza zakresem".
* **Nie tknąłem `docs/03-legal.md`.** Czytałem go, bo bez niego nie dało się
  rozstrzygnąć, czy data jest wymaganiem projektu, czy moim pomysłem — i okazało
  się, że jest moim pomysłem.
* **Nie napisałem walidatora `format: date`.** Bramka żąda niepustego napisu, nie
  poprawnej daty ISO; sprawdzanie formatu należy do walidatora schematu, którego
  ten projekt świadomie nie ma (6.D85 zabrania dodawania zależności).

## 8. Zostaje do decyzji właściciela

Czy `as_of` ma wejść do gałęzi `cleared` **w schemacie**. Za: data ustala, od kiedy
prawo obowiązuje, a prawa bywają terminowe. Przeciw: `docs/03-legal.md` tego nie
żąda, a schemat ma dziś odwzorowywać ten dokument. Koszt zmiany: **jedna linia,
zero dotkniętych wpisów** — i ta liczba zacznie rosnąć z pierwszym wpisem `cleared`,
więc jest to decyzja tańsza dziś niż jutro.

## 9. Uzupełnienie kolejki w tym samym commicie, i dlaczego nie osobnym

Domknięcie tej pozycji zbiło kolejkę z dwunastu na **jedenaście** pozycji DO WZIĘCIA,
czyli poniżej progu z `CLAUDE.md` §8. Bramka powiedziała to wprost:

```
FAIL test_the_queue_holds_at_least_a_day_of_work: kolejka ma 11 pozycji DO WZIĘCIA
  przy progu 12 (wpisanych: 11, czeka na właściciela: żadna); pierwszym zadaniem
  jest uzupełnienie fazy 6, nie zatrzymanie się
```

Commit z samym domknięciem zostawiłby więc drzewo czerwone — ta sama arytmetyka, co
przy 6.D96 i 6.D102, i to jest powód, dla którego uzupełnienie idzie tu razem,
a nie osobno.

Doszło **sześć** pozycji, 6.D135 … 6.D140, i **ani jedna nie jest wymyślona pod pustą
kolejkę**: wszystkie wyszły z pomiarów zrobionych przy wykonywaniu 6.D120, 6.D121,
6.D122, 6.D123 i 6.D124 i zapisanych tam jako zauważone.

| pozycja | skąd |
|---|---|
| 6.D135 | `MEASURED_MAX_WALL_S` z przebiegu o 95 modułach, dziś jest ich 121 (6.D122, 6.D123) |
| 6.D136 | log CI pokazuje 199 plików bajtkodu przed startem zestawu (6.D123) |
| 6.D137 | `[KOPERTA] … masa AW0` nie mówi, że masa jest przybliżona (6.D124) |
| 6.D138 | `assert R.MASS["AW0"] == 170000.0` porównuje kopię z kopią (6.D124) |
| 6.D139 | trzecia kopia liczb 18 i 24 w `docs/21`, nieliczona (6.D121) |
| 6.D140 | `--from-m/--to-m` zawęża tylko kamerę wnętrza (6.D120) |

Zapas: **17** pozycji do wzięcia. `MINIMUM_DETAIL_BLOCKS`, podniesiona z 207 na 213 — wartość policzona
z `len(detail_sections(...))` na pliku po edycji, nie z dodania szóstki do poprzedniej.
