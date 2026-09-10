# 6.D109 — które dwanaście: pozycje wpisane czy pozycje do wzięcia

**Zmierzone 10.09.2026 na:** `e968040`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_backlog.py` (`MINIMUM_READY_ITEMS`, `open_items`,
`do_wziecia`, `czeka_na_wlasciciela`, `prog_z_dokumentu`), `docs/TASKS.md` i jej
139 rewizji z gita, `CLAUDE.md` §8 — dokument zmieniony, dane tylko do odczytu.

---

## 1. Rozstrzygnięcie, o które prosi wpis

Pole „Dlaczego to nie jest oczywista poprawka" żąda pomiaru przed wyborem licznika:
ile razy w historii tego repozytorium liczba pozycji WPISANYCH różniła się od liczby
pozycji DO WZIĘCIA i o ile. Dopiero na tym ma się oprzeć wybór, a zapisany powód, dla
którego licznik zostaje bez zmiany, jest wynikiem tak samo dobrym.

Pomiar poszedł po wszystkich rewizjach `docs/TASKS.md`, czytnikiem **poprawionym tego
samego dnia** — o czym niżej, bo pierwsza wersja tego pomiaru była nieprawdziwa.

## 2. Pomiar: 139 rewizji, różnica mała i częsta

```
rewizji `docs/TASKS.md`: 139
  różnica 0 →  54 rewizji
  różnica 1 →  84 rewizji
  różnica 2 →   1 rewizji
różnica niezerowa w 85 rewizjach
czekały kiedykolwiek: {'6.D108': 1, '6.D53': 84, '6.D52': 1}
```

Trzy rzeczy wychodzą z tych liczb i każda mówi co innego.

**Różnica jest mała.** Nigdy nie przekroczyła dwóch pozycji, a w 84 rewizjach ze 139
wynosiła równo jedną. To nie jest rozjazd, który by kiedykolwiek przewrócił kolejkę —
to przesunięcie momentu uzupełnienia o jedno zadanie.

**Różnica jest częsta.** 85 rewizji ze 139, czyli 61 %. Wersja „liczby są prawie zawsze
równe, więc licznik nie ma znaczenia" jest nieprawdą w drugą stronę: prawie zawsze
równe **nie były**.

**Różnica idzie zawsze w tę samą stronę.** Pozycji do wzięcia jest **mniej** albo tyle
samo, nigdy więcej — bo `do_wziecia` jest podzbiorem `open_items`. Licznik po pozycjach
do wzięcia zapala bramkę **wcześniej**, a to jest właściwa strona: pozycji czekającej na
cudzą decyzję agent nie zacznie, więc doby pracy przed nim ona nie stanowi.

**Czekały kiedykolwiek trzy pozycje na kilkadziesiąt.** 6.D53 przez 84 rewizje,
6.D52 i 6.D108 po jednej. Cała mierzona różnica pochodzi więc w praktyce z jednej
pozycji, która stała zablokowana przez większość życia kolejki — i którą właściciel
odblokował decyzją z 10.09.2026, czyli po tym pomiarze.

## 3. Dzisiejsza kolejka nie odróżniłaby jednego licznika od drugiego

```
wpisanych 20
do wzięcia 20
czeka []
```

Po ośmiu decyzjach właściciela z 10.09.2026 nie czeka **żadna** pozycja. Obie liczby są
dziś równe, więc gdyby werdykt bramki był jedynym dowodem, nie dałoby się powiedzieć,
którą z nich próg porównał. Stąd kontrola na kolejce **syntetycznej** — buduje kolejkę
o dokładnie tylu pozycjach, ile wynosi próg, blokuje jedną i pokazuje, że liczba
WPISANYCH nie drgnęła, a liczba DO WZIĘCIA spadła poniżej progu. Bez tego wejścia test
przechodziłby przy obu licznikach i opisywałby co innego, niż sprawdza.

## 4. Wybór: licznik zmieniony, próg nietknięty

Bramka porównuje od dziś `do_wziecia`, a jej komunikat wypisuje **obie** liczby i listę
pozycji czekających — tego żąda pole „Skończone, gdy". Wartość progu zostaje, bo pole
„Poza zakresem" wyklucza jej zmianę: to decyzja o tempie pracy, nie o przyrządzie.

`CLAUDE.md` §8 mówił „poniżej dwunastu pozycji" i **nie mówił których**. Zdanie było
zgodne z kodem co do liczby i mimo to nie rozstrzygało pytania, które ta pozycja
postawiła. Dziś mówi „poniżej dwunastu pozycji DO WZIĘCIA", a zgodności dokumentu
z kodem pilnuje nowa bramka `test_dokument_i_kod_mowia_o_tej_samej_liczbie`:
wyłuskuje ze zdania liczebnik i to, co jest liczone, i rozstrzyga o obu osobno.

## 5. Czytnik blokad był zepsuty i pierwsza wersja tego pomiaru była nieprawdziwa

To jest najważniejsza rzecz w tej pozycji i mówię ją wprost, bo wynik pierwszego
przebiegu poszedłby do raportu jako fakt.

`czeka_na_wlasciciela` szukał w polu „Zależy od" słowa „właściciela" i nie patrzył na
nic więcej. Pole o kształcie „decyzji właściciela **z 07.09.2026** o …" opisuje decyzję
**już podjętą** — pozycja jest odblokowana, a czytnik liczył ją jako oczekującą.
Pierwszy przebieg po historii dał wtedy „różnica niezerowa w 138 rewizjach ze 138",
czyli obraz kolejki trwale zablokowanej, którego przyczyną był przyrząd.

Po poprawce (data w polu zdejmuje blokadę) różnica spadła do liczb z §2. Poprawka
zmienia więc **przyrząd, nie kolejkę**: na dzisiejszym `docs/TASKS.md` obie wersje
czytnika dają dziś ten sam wynik, bo obie dzisiejsze blokady były prawdziwe. Widać ją
wyłącznie na historii i na wejściu syntetycznym — i tam jest przybita, osobnym testem
dla każdego z dwóch kształtów pola.

## 6. Cztery kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem (procedura z 6.D102), po każdej
`md5sum -c` na zmienianym pliku.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | `CLAUDE.md` §8 wraca do dawnego „poniżej dwunastu pozycji" | 30/31, zgłoszone jako brak nazwy licznika |
| KN-2 | `CLAUDE.md` §8 mówi o dziesięciu pozycjach | 30/31, zgłoszony rozjazd liczby |
| KN-3 | dziewięć pozycji kolejki dostaje blokadę na decyzji właściciela | 30/31, bramka zapasu czerwona |
| KN-4 | `do_wziecia` wraca do zwracania `open_items` | 30/31, kontrola syntetyczna czerwona |

KN-3 jest tą, o którą chodzi w całej pozycji, bo pokazuje różnicę na **prawdziwej**
kolejce, a nie na wejściu zbudowanym pod tezę:

```
kolejka ma 11 pozycji DO WZIĘCIA przy progu 12 (wpisanych: 20, czeka na właściciela:
6.D108, 6.D109, 6.D110, 6.D111, 6.D112, 6.D113, 6.D114, 6.D115, 6.D53); pierwszym
zadaniem jest uzupełnienie fazy 6, nie zatrzymanie się
```

Dwadzieścia wpisanych to o osiem **powyżej** progu — licznik sprzed tej pozycji byłby
przy tym wejściu zielony i nie powiedziałby ani słowa o tym, że do wzięcia zostało
jedenaście. Komunikat podaje obie liczby, więc odpowiedź na pytanie „którą porównał"
stoi w nim, a nie w lekturze kodu.

KN-1 i KN-2 rozdzielają dwie połowy nowej bramki dokumentu, bo jeden test na obie
opisywałby co innego, niż sprawdza: zdanie może być zgodne co do liczby i milczeć
o liczniku, i dokładnie takie zdanie stało w §8 do dziś.

Weryfikacja z pola „Weryfikacja" wpisu, wprost z przebiegu:

```
$ python3 tools/tests/test_all.py test_backlog.py
  31/31 przeszło
```

Na całym zestawie: `2231/2231 przeszło`, 119 modułów, `RAZEM 130.194 s`. Baseline
sprzed tej pozycji: 28 testów w module, 2228 w zestawie.

## 7. Czego nie zrobiłem

- **Nie zmieniałem wartości progu.** Pole „Poza zakresem" wyklucza to wprost.
- **Nie ruszałem `MINIMUM_DOCUMENTED_ITEMS`** ani żadnej innej zapadki — pomiar ich
  nie dotyczy, a zapadki wolno wyłącznie podnosić za powodem.
- **Nie przepisywałem pól „Zależy od"** w `docs/TASKS.md`, choć czytnik ma dziś dwa
  kształty do rozróżnienia; ujednolicenie zapisu to zmiana treści kolejki.

## 8. Zauważone przy okazji

- **Tabela liczebników w `LICZEBNIKI` jest krótka i to jest wybór.** Próg wyprowadzony
  poza jej zakres wywala bramkę na braku wpisu, zamiast po cichu przepuścić zdanie,
  którego nie rozumie. Kto zmienia próg, ma dopisać słowo, którym go zapisał.
- **Reguła czytania pola „Zależy od" opiera się na obecności daty, nie na jej treści.**
  Data w polu znaczy „decyzja zapadła", ale nic nie sprawdza, czy zapadła **ta**
  decyzja — pole może cytować datę czyjejś innej. Na dzisiejszej kolejce takiego
  przypadku nie ma; przyrząd nie umiałby go odróżnić.
