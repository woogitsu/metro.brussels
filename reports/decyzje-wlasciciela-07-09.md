# Cztery decyzje właściciela z 07.09.2026 — zapisane w drzewie, nie w rozmowie

**Zmierzone 07.09.2026 na commicie:** `018130cb74611d97122c7358da28017187bb80c9`
**Dotyczy:** `docs/TASKS.md`, `docs/22-heartbeat.md`, `tools/tests/test_backlog.py`
**Po co:** decyzja właściciela, której nie ma w repozytorium, jest decyzją, którą
następna sesja podejmie od nowa.

## 1. Skąd ten commit

Właściciel poprosił 07.09.2026: „Jak masz decyzje do podjęcia to rozpisz mi w formie
klikalnej". Cztery pozycje zebrane **z repozytorium** — z wiersza „Czego agent nie ruszy
bez decyzji" w `docs/TASKS.md` i z `docs/22-heartbeat.md`, nie wymyślone na miejscu —
poszły przez `AskUserQuestion` i dostały odpowiedzi. Ten commit przenosi odpowiedzi
z rozmowy do drzewa.

Powód nie jest porządkowy. Kopia decyzji żyjąca w czacie **starzeje się osobno od
repozytorium**, a ta jedna sesja zobaczyła tego dnia trzy razy, co z tego wynika:

| pozycja | co było zapisane w jednym miejscu i nigdzie nie pilnowane |
|---|---|
| 6.A22 | reguła pierwszeństwa sceny stała **wyłącznie w komentarzu**; bramka była zielona przy 15/15 |
| 6.A26 | pomiar, na którym stoi decyzja 6.A22, był zapisany raz w raporcie i nigdzie nie liczony |
| 6.B32 | dziennik przeglądu nie odróżniał dwóch przebiegów na tym samym commicie |

## 2. Cztery decyzje i co z każdej wynika

| decyzja | odpowiedź | zapis | praca |
|---|---|---|---|
| **6.A19** wybieg w `replay` | odczytanie **(a)**: odmowa zostaje na stałe jako udokumentowana własność polecenia | wiersz zdjęty z „Czego agent nie ruszy bez decyzji", pozycja w fazie 6 | 6.A19, rozmiar S |
| **pasmo 94..106 m** kamery goniącej | **rozciągnąć ukrycie do 110 m** | wiersz zdjęty z tej samej sekcji, pozycja w fazie 6 | 6.B43, rozmiar M |
| **T-901** głębokości stacji | **budować z jawnym `unknown`** | wiersz T-901 **przepisany** (blokada zeszła z „profilu" na „profil produkcyjny"), wpis T-112 przepisany, pozycja w fazie 6 | 6.B44, rozmiar M |
| **puls sesji** co godzinę | **zostawić godzinę** | `docs/22-heartbeat.md` §5 przepisane | brak — i to jest wynik |

Trzy z czterech odblokowały pracę, czwarta nie odblokowała nic i **nie miała czego
odblokować**: usterka, z której wyszło pytanie, była w progu zatrzymania agenta, nie
w okresie pobudki.

## 3. Czego decyzje NIE rozstrzygnęły

Wypisane, bo pozycja rozstrzygnięta w połowie wygląda w tabeli identycznie jak
rozstrzygnięta w całości:

- **Konflikt Schuman 15 m vs 17,42 m zostaje otwarty.** Decyzja mówi „buduj z dziurą
  widoczną", nie „wybierz stronę". Wiersz **T-901 zostaje** na liście właściciela;
  zmieniła się tylko jego treść, bo zdanie „Blokuje T-112" przestało być prawdziwe.
- **Wariant `production` w T-112 nadal jest zablokowany.** Odblokowany jest wariant
  z jawną niewiadomą.
- **Odczytania (b) i (c) dla `replay`** — wybieg nadpisujący zapis pod inną nazwą
  polecenia i drugi tryb `replay` z automatem — **nie wchodzą**. Wybrano (a);
  wprowadzenie któregokolwiek z tamtych byłoby zmianą decyzji.
- **110 m nie jest zmierzonym początkiem czystego pasma**, tylko najniższym zmierzonym
  czystym punktem powyżej 96 m. Seria z 05.09.2026 jest niemonotoniczna
  (90 m → 0,0 %, 96 m → 42,0 %, 110 m → 0,0 %), więc pozycja 6.B43 ma pasmo domierzyć
  co 2 m, a nie przepisać jeden punkt. Gdyby pomiar pokazał czystość wcześniej,
  **liczba właściciela zostaje** — 110 m jest decyzją, nie wynikiem pomiaru.

## 4. Zapas kolejki — policzony na stan PO, nie na stan przed

`docs/TASKS.md` żąda tego wprost i z powodu, który ta sesja widziała dziś cztery razy:
licznik zapasu **opada od wykonywania pracy**, więc liczba policzona przed scaleniem
jest bezużyteczna.

```
przed tym commitem:            13 pozycji do wzięcia, 13 udokumentowanych, 98 bloków
po tym commicie:               16 pozycji do wzięcia, 16 udokumentowanych, 101 bloków
po scaleniu czterech w robocie
(6.A30, 6.A31, 6.A32, 6.B41):  12 pozycji do wzięcia — RÓWNO na progu MINIMUM_READY_ITEMS
```

Ostatni wiersz jest tu **ostrzeżeniem, nie chwalbą**: po scaleniu czterech zadań
w robocie zapas siada dokładnie na progu 12, więc **następne domknięcie zapali**
`test_the_queue_holds_at_least_a_day_of_work`. Pierwszym zadaniem po tych scaleniach
jest uzupełnienie kolejki (`CLAUDE.md` §8), nie kolejna pozycja z listy. Progu nie
obniżam.

## 5. Weryfikacja — wykonana

Zestaw narzędzi, **kod wyjścia**, nie liczba wierszy z `grep`:

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  RAZEM 73.414 s, 1891 testów, 99 modułów
kod: 0
```

Liczniki kolejki odczytane z bramki, nie policzone ręcznie:

```
open:    16 ['5.6', '6.A19', '6.A21', '6.A30', '6.A31', '6.A32', '6.B26', '6.B38',
             '6.B39', '6.B40', '6.B41', '6.B42', '6.B43', '6.B44', '6.C4', '6.D24']
blocks:  101
blocked ma wiersze kolejki: []
```

## 6. Trzy kontrole negatywne — WYKONANE

Każda wywróciła dokładnie jeden test i każda została przywrócona (`git diff --stat`
sprawdzony po każdej).

**KN-1 — zapadka zostawiona na 98 przy 101 blokach.** Sprawdza kierunek „dopisałem blok
i nie podniosłem stałej":

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków z kompletem
sześciu pól jest 101, a zapadka stoi na 98 — podnieś ją do 101 w tym samym commicie,
w którym dopisujesz blok
  RAZEM 0.879 s, 26 testów, 1 modułów
kod: 1
```

**KN-2 — blok 6.B44 wycięty przy zapadce 101.** Sprawdza kierunek przeciwny, czyli to,
po co zapadka w ogóle istnieje:

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 100 przy
zapadce 101 — któryś zniknął albo stracił jedno z sześciu pól
```

**KN-3 — wiersz kolejki podstawiony do nowej podsekcji `#### Rozstrzygnięte 07.09.2026`.**
Ta kontrola nie dotyczy zapadki, tylko **miejsca**, w którym stanął nowy zapis: podsekcja
jest nagłówkiem czwartego poziomu wewnątrz sekcji trzeciego poziomu, więc pytanie „czy
`blocked_section` naprawdę do niej dochodzi" nie jest retoryczne. Gdyby nie dochodziła,
dałoby się w niej zaparkować wiersze kolejki niewidoczne dla licznika:

```
FAIL test_blocked_work_is_not_counted_as_queue: pozycje z sekcji decyzji właściciela
wpadają do licznika kolejki
```

Podstawiony wiersz `| 6.Z1 | … |` został złapany, czyli podsekcja **jest** w środku
sekcji decyzji, a nie za jej granicą.

## 7. Czego ten commit świadomie nie zrobił

- **Nie wykonał żadnej z trzech odblokowanych pozycji.** 6.A19, 6.B43 i 6.B44 są
  zapisane z kompletem sześciu pól i zostawione w kolejce; ten commit rozstrzyga
  **zapis decyzji**, nie pracę z niej wynikającą. 6.B43 wymaga przy tym Godota, którego
  w tym kontenerze nie ma.
- **Nie tknął `docs/24-clearance-profile-decisions.md`.** Ten dokument trzyma decyzje
  o progach luzu w `clearance_profile.py`; żadna z dzisiejszych czterech go nie dotyczy,
  a dopisywanie do niego rzeczy niezwiązanych zabrałoby mu jedyną własność, którą ma —
  to, że w całości mówi o jednym module.
- **Nie ruszył `data/network/station-depths.csv`.** Trzy głębokości `estimated` zostają
  jak były, dziewięć `unknown` zostaje puste. Decyzja o jawnym `unknown` dotyczy
  **narzędzia, które ten plik czyta**, nie samego pliku (`CLAUDE.md` §4.6).

## 8. Co zauważone przy okazji, nietknięte

- **`docs/22-heartbeat.md` §4 opisuje wiązanie Routine przez pusty
  `persistent_session_id`**, a odczyt z API pokazuje pole **ustawione jawnie**
  (`persist_session: true`, `persistent_session_id` wypełniony). Mechanika opisana w §4
  zostaje prawdziwa co do skutku — martwe powiązanie po zakończeniu sesji — ale zdanie
  o pustym polu nie opisuje tego, co widać dziś w API. Nietknięte, bo to nie jest jedna
  z czterech decyzji.
- **Na koncie stoją dwie włączone pobudki**, obie o cronie z minutą utworzenia
  (`35 * * * *` i `37 * * * *`), i tylko druga należy do tego projektu. Nie jest to
  patologia z §4 — pierwsza budzi żywą sesję innego repozytorium — ale jest to dokładnie
  ten powód, dla którego nazwa Routine jest stała.
