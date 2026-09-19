# 6.D171 — pięć odsyłaczy i jedno archiwum, a bramka dwa razy uznała własną listę za odsyłacz

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `5b42cf9`

Pozycja żądała, żeby każdy z sześciu raportów dostał albo odsyłacz tam, gdzie należy,
albo nazwanie archiwum z powodem. Pięć dostało odsyłacz, jeden jest archiwum.
Najciekawsze w tej pozycji nie jest jednak rozstrzygnięcie, tylko **dwie usterki
przyrządu, które złapały kontrole negatywne, a nie oko** — obie tej samej klasy
i obie polegające na tym, że bramka liczyła jako odsyłacz wzmiankę powstałą
z POLICZENIA BRAKU.

## 1. Liczby wejściowe odtworzone co do cyfry

```
$ for R in audyt-sekcja-6-weryfikacja audyt-weryfikacja decyzje-wlasciciela-07-09 \
           runda-pieciu-agentow sonda-doctor-bez-dotnet uzupelnienie-kolejki-10-09; do
      echo -n "$R -> "
      grep -rl --include=*.md --include=*.py --include=*.sh -e "$R" docs tools reports \
          | grep -cv "^reports/$R"
  done
audyt-sekcja-6-weryfikacja -> 1
audyt-weryfikacja -> 1
decyzje-wlasciciela-07-09 -> 1
runda-pieciu-agentow -> 1
sonda-doctor-bez-dotnet -> 1
uzupelnienie-kolejki-10-09 -> 3
```

`1 1 1 1 1 3`, dokładnie jak w polu „Weryfikacja". Pozostałe liczby tego pola
przeliczone, a nie przepisane:

| liczba | pole mówi | zmierzone 19.09.2026 |
|---|---|---|
| raportów w `reports/` | 368 | **404** |
| raportów bez wpisu w `docs/TASKS.md` | 21 z 275 | **18 z 404** |

Obie różnice są zgodne z zapisem pola („stan tamtego dnia"). Druga jest ciekawsza,
niż wygląda: licznik bezwzględny **spadł** (21 → 18) przy katalogu większym o 129
plików — bo od 6.D45 każda domknięta pozycja dopisuje odsyłacz w swoim wierszu.
Udział spadł z 7,6 % do 4,5 %.

## 2. Co łączy tę szóstkę

Wszystkie sześć powstało **przed konwencją nazw `6dNNN-*`**, czyli zanim istniał
mechanizm, który odsyłacze tworzy — adnotacja ZROBIONE w wierszu pozycji, cytująca
`reports/6dNNN-….md`. Nie zgubił ich nikt; **nigdy nie miały skąd być zacytowane.**
To jest powód, dla którego kasowanie byłoby tu odpowiedzią na złe pytanie, a nie
tylko dlatego, że zabrania go `MIN_REPORTS`.

## 3. Rozstrzygnięcie, raport po raporcie

| raport | wariant | gdzie stanął odsyłacz i dlaczego TAM |
|---|---|---|
| `decyzje-wlasciciela-07-09` | odsyłacz | `docs/22-heartbeat.md`, pod nagłówkiem „DECYZJA WŁAŚCICIELA 07.09.2026 — godzina zostaje". Ten akapit jest **skutkiem czwartej z czterech decyzji**, które raport zapisuje; czytający go trafia dokładnie na brakujące trzy. |
| `runda-pieciu-agentow` | odsyłacz | `CLAUDE.md` §5, obok istniejącego cytatu 6.D75. §5 podaje liczbę „cztery bajty na 737 tysięcy" i przypisuje ją 6.D75 — a **pomiar pierwotny zrobiono w tej rundzie**, i to tam stoi zdanie, co z tego wynika dla całej pętli weryfikacji. |
| `sonda-doctor-bez-dotnet` | odsyłacz | `tools/tests/test_dotnet_version.py`, w docstringu, jako „powód trzeci". Raport opisuje, dlaczego **ten moduł** przestał zakładać środowisko i zaczął je gwarantować; powód pierwszy i drugi już tam stały. |
| `audyt-sekcja-6-weryfikacja` | odsyłacz | wiersz `\| 6.D92 \|` w `docs/TASKS.md` — obie pozycje, 6.D92 i 6.D93, **z tego raportu powstały**. Tam też stoją **powody odrzucenia** AUDYT-17 i części AUDYT-03, czyli jedyny zapis tego, czego projekt świadomie nie wziął. |
| `audyt-weryfikacja` | odsyłacz | wiersz `\| 6.D71 \|` w `docs/TASKS.md` — raport niesie **powód obniżenia wagi** tego findingu wobec audytu zewnętrznego, a wiersz pozycji sam mówił „z powodem obniżenia zapisanym przy pozycji", nie mówiąc gdzie. |
| `uzupelnienie-kolejki-10-09` | **archiwum** | Zapis JEDNEGO dnia: kolejka stała na progu dwunastu, więc sesja dopisała sześć pozycji, zanim wzięła cokolwiek. Sześć pozycji, które z tego wyszły, ma dziś własne wiersze i własne raporty; sam przebieg uzupełniania **nie zostawił w drzewie ani jednej reguły, która odsyłałaby do tego opisu**. Reguła, którą ten dzień stosował, mieszka w `CLAUDE.md` §8 i w `tools/tests/test_backlog.py`. |

Powodem archiwum **nie jest** „nikt go nie cytuje" — tak brzmi objaw, który ta pozycja
mierzyła, a wpisanie go do listy zrobiłoby z niej podpis zamiast rozstrzygnięcia.
Bramka tej frazy w powodzie zabrania wprost.

## 4. Usterka przyrządu pierwsza: dopasowanie po PRZEDROSTKU

Pierwsza wersja czytnika pytała `nazwa in tresc`. Przy tym pytaniu
`uzupelnienie-kolejki-10-09` „miało odsyłacz" w dwóch miejscach, które mówią o pliku
`uzupelnienie-kolejki-10-09-**druga**.md`, czyli o czym innym. **Pole „Weryfikacja"
pozycji nazywa tę pułapkę wprost** — i bramka wpadła w nią mimo to, dopóki pomiar
tego nie pokazał.

Zapaliła ją KN-1: wpis zdjęty z `ARCHIWUM` miał dać czerwień i **nie dał jej**.
Poprawka: `re.escape(nazwa) + r"(?![-\w])"`, czyli granica po nazwie.

## 5. Usterka przyrządu druga: bramka liczyła WŁASNĄ listę jako odsyłacz

Ta sama klasa, dwa razy, w dwóch różnych miejscach — i obie znalazł przebieg,
nie czytanie kodu:

**(a) Własny moduł.** `SZOSTKA_6D171` i `RAPORTY_BEZ_ODSYLACZA_POZA_6D171` WYMIENIAJĄ
nazwy raportów. Bez wycięcia tego pliku z korpusu każdy raport przypięty na liście
robił się „zacytowany" — bramka ogłaszała, że sierot nie ma, **dokładnie dlatego, że
sama je wymienia**. Zmierzone: zbiór sierot wyszedł **pusty** przy dwóch sierotach
w drzewie.

**(b) Blok szczegółów 6.D171.** Zwężenie wycinało wiersz tabeli `| 6.D171 |`, ale nie
blok `##### 6.D171`, którego pole „Weryfikacja" wymienia wszystkie sześć nazw w pętli
`for R in …`. KN-1b dał wtedy **23/23** — bramka ogłosiła, że raport bez odsyłacza
odsyłacz ma.

Obie wycięte, obie z asercją, że wycięcie **robi różnicę** — bez tego samo wycinanie
byłoby ozdobą.

## 6. Kontrole, przewidywania spisane PRZED przebiegami

Wszystkie na **pełnej** kopii drzewa z `.git`, `__pycache__` czyszczony przed każdym
przebiegiem, kopia przywracana między kontrolami.

| kontrola | zmiana na kopii | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-3 | nic | zielone | **23/23** | tak |
| KN-1 | wpis zdjęty z `ARCHIWUM` | czerwień testu głównego | **22/23, ale INNY test** | **NIE** |
| KN-1b | wpis `ARCHIWUM` podmieniony na inny z szóstki | czerwień testu głównego | **22/23**, nazwał plik | tak |
| KN-2 | nowy raport bez odsyłacza | czerwień | **19/23** | tak |
| KN-4 | wpis `ARCHIWUM` o pliku, którego nie ma | czerwień | **20/23**, TRZY testy | tak |
| KN-5 | powód skrócony do podpisu | czerwień | **22/23** | tak |
| KN-6 | `MODUL_TEJ_BRAMKI` wskazuje plik, którego nie ma | — (kontrola dopisana po odkryciu) | **21/23**, sieroty puste | — |
| KN-7b | granica dopasowania zdjęta + podmiana z KN-1b | czerwień, jak KN-1b | **23/23 ZIELONE** | — |

**KN-1 obaliła przewidywanie i to jest jej wynik.** Przewidziałem czerwień testu
głównego; padł test kontroli przyrządu, z komunikatem o pustym `ARCHIWUM`, bo
usunięcie jedynego wpisu opróżnia listę i strażnik pustej listy zapala się pierwszy.
Kontrola nie izolowała więc tego, o co pytała — dlatego powstała KN-1b, która wpis
PODMIENIA zamiast usuwać. Dopiero ona zapaliła test główny i nazwała plik. Pierwsza
wersja KN-1 pokazała przy okazji dwie rzeczy prawdziwe: strażnik pustej listy działa,
a wcześniej, przed poprawką z §4, ta sama mutacja **przechodziła na zielono**.

**Para KN-1b / KN-7b jest dowodem, że granica z §4 niesie treść, a nie ostrożność:**
ta sama mutacja `ARCHIWUM` daje **22/23** z granicą i **23/23** bez niej.

## 7. Weryfikacja

To samo polecenie co w §1, PO pozycji — liczba miała nie spaść i nie spadła:

```
audyt-sekcja-6-weryfikacja -> 3
audyt-weryfikacja -> 3
decyzje-wlasciciela-07-09 -> 4
runda-pieciu-agentow -> 3
sonda-doctor-bez-dotnet -> 4
uzupelnienie-kolejki-10-09 -> 4
```

Każda liczba rosła o dwa albo trzy: doszedł odsyłacz (albo wpis `ARCHIWUM`), lista `SZOSTKA_6D171` w bramce i ten raport. **Dwóch ostatnich bramka za odsyłacze nie uznaje** — to jest cała treść §5 i różnica między tym wypisem a kryterium, którego pilnuje `tools/tests/test_report_hygiene.py`.

```
$ python3 tools/tests/test_all.py
  2641/2641 przeszło
  RAZEM 359.257 s, 2641 testów, 137 modułów
  KOD=0
```

Zapadki podniesione w tym samym commicie, w zapisie „stoi dziś (stała wczoraj)":
`ASERCJI_NAPISOWYCH_RAZEM` = 933 (było 932), `MIN_REPORTS` o jeden. Nowych zapadek
liczbowych ta pozycja nie wprowadza — pilnowane są **zbiory**, nie sumy.

## 8. Czego świadomie nie zrobiono

* **Nie skasowano ani jednego z sześciu** i nie obniżono `MIN_REPORTS` — pole „Poza
  zakresem", 6.D45.
* **Nie dopisano odsyłacza „byle gdzie"** — każdy z pięciu stoi w pliku, którego treść
  raport wyjaśnia, i tabela §3 nazywa ten związek przy każdym z osobna.
* **Nie rozstrzygnięto dwóch sierot spoza szóstki** (`6d227-…`, `6d248-…`). Pole
  „Wejście" wymienia sześć plików imiennie i tych dwóch wśród nich nie ma; `6d227-…`
  należy przy tym do pozycji **otwartej**, więc jej odsyłacz powstanie sam przy
  domknięciu. Liczba jest przybita, żeby trzeci taki raport zapalił bramkę.
* **Nie dopisano do „Czego agent nie ruszy bez decyzji" znaleziska z
  `audyt-weryfikacja` §5** (suma unikalnych przystanków z czterech linii daje **60**,
  a `network.metro_stations` i `docs/00-network-data.md` mówią **59**, i żadna bramka
  tych dwóch liczb nie zestawia). Raport mówi, że finding tam poszedł; dziś go tam
  nie ma. To jest twierdzenie o danych sieci, więc nie zgaduję — zapisane jako nowa
  pozycja.

## 9. Zauważone przy okazji, nietknięte

* Raportów bez ani jednego odsyłacza **w całym drzewie** są dziś dwa, a nie sześć:
  szóstka 6.D171 była cytowana przez własną pozycję. Różnica między „bez odsyłacza"
  a „bez odsyłacza spoza wzmianki o braku" wynosi tu **cztery** raporty i bez zwężenia
  korpusu nie widać jej wcale.
* `docs/TASKS.md` ma dziś **18** raportów bez wzmianki, wszystkie z nazwami bez numeru
  pozycji albo z pozycji otwartych — czyli ten sam mechanizm co w §2, tylko szerzej.
