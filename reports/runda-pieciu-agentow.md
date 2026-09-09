# Runda pięciu agentów: czternaście findingów zweryfikowanych, jedna moja ocena obalona

**Zmierzone 09.09.2026 na:** `dafb7a1`, kontener tej sesji.
**Przyrząd:** pięciu agentów działających równolegle, każdy z zakazem zapisu do
drzewa; `tools/blender/render_check.py`, `tools/tests/test_assertion_gate.py`,
`tools/track/validate.py`, `doctor.sh`, `.github/workflows/godot-first-run.yml`,
`src/Sim/Line/TrackAxis.cs`, `src/Game/Scenes/FirstRun.tscn`.

---

## 1. Skąd ta runda

Właściciel udostępnił dwudziestominutowe okno na pięć agentów. Do zweryfikowania
zostało czternaście findingów audytu wagi średniej i niskiej plus tabele bramek
martwych — dokładnie materiał, który dzieli się na niezależne paczki. Każdy agent
dostał: zakaz modyfikacji drzewa, zakaz uruchamiania całego zestawu, obowiązek
wklejania rzeczywistego wyjścia i obowiązek policzenia, czego NIE sprawdził.

Nowych agentów po zamknięciu okna nie tworzono.

## 2. Najpoważniejsze: `CLAUDE.md` §5 obiecuje przyrząd, którego nie ma

Para fixture różniąca się **wyłącznie** orientacją ścian — te same wierzchołki,
ta sama kamera, ta sama oś — przez istniejący skrypt kontrolny:

```
[KLATKA] good_inside.png     640x384 ink=0.09278 std=0.04349 poziomy=140
[KLATKA] flipped_inside.png  640x384 ink=0.09278 std=0.04349 poziomy=140

side:   roznych_bajtow=0  max_delta=0
inside: roznych_bajtow=4  max_delta=255
```

Render `_side` bit w bit identyczny, `_inside` różny o cztery bajty na 737 tysięcy.
Oba obrazy **obejrzane**, jak każe §5: szarosina rura od wnętrza, pierścienie siatki
zbiegające się do ciemnego wylotu — i ani jednej różnicy. Wersja z odwróconymi
normalnymi wygląda jak zdrowy tunel.

Przyczyna jest trzykrotna: materiał kontrolny jest dwustronny, silnik cieniuje tylną
stronę z odwróconą normalną, a emisja dokłada składową niezależną od zwrotu.

**Co to znaczy dla całej sesji.** Powtarzałem dziś wielokrotnie, że renderu nie wolno
opisywać z metryk, trzeba go obejrzeć. To zostaje prawdą i jest **niewystarczające**:
przy dzisiejszym materiale samo oglądanie `_inside` też nie wykryje wywróconych
normalnych. Tabela w §5 przypisuje temu renderowi wykrywanie, którego on nie ma,
i jest to jedyna bramka normalnych w opisanej pętli.

## 3. Moja ocena obalona pomiarem

08.09 i 09.09 przeważyłem w dół finding o kompilacji bez jawnego trybu, pisząc:
„scenariusz nie ma dziś drogi wywołania, więc waga niższa". Agent zmierzył skutek,
gdy droga się znajdzie — wstawił **realną regresję** do kodu produkcyjnego
(poluzowany limit pochylenia) i uruchomił ten sam moduł dwa razy:

```
=== BEZ -O ===   36/38 przeszło   (dwa FAIL nazywające regresję)
=== Z -O ===     38/38 przeszło
```

Jedna flaga zamienia dwie porażki w pełną zieleń, a przeszukanie testów, `tools/ci/`
i workflowów pod nazwę flagi i zmiennej środowiskowej daje **zero trafień**: nic
tego nie zabrania i nic nie zauważa. Poprawka jednym argumentem zmierzona jako
wystarczająca.

Utajenie było prawdą. **Kryterium było złe:** przy zerowym prawdopodobieństwie
i totalnym promieniu rażenia nie obniża się wagi na podstawie samego
prawdopodobieństwa. Sprostowanie wpisane w treść pozycji, nie dopisane obok.

## 4. Dwa zawężenia moich wcześniejszych zapisów

**Wartość nieliczbowa w osi.** Napisałem, że przechodzi walidator. Prawda, ale
zestaw ją łapie — innym modułem, tylko dla jednej z sześciu osi i własnym
sprawdzeniem, nie przez walidator. Usterką jest walidator **ogłaszający zgodność**,
nie brak jakiejkolwiek kontroli. Pozycja niesie teraz to rozróżnienie.

**Stacja na wspólnym pierścieniu.** Napisałem, że „żadna bramka tego nie widzi".
Precyzyjniej: kontrola **widzi** i przy wywołaniu z drugą linią zgłasza niezgodność
wprost — tylko krok CI wyprowadza nazwę linii z **prefiksu nazwy pliku** osi, więc
z pary, która ujawnia błąd, nie jest wołana nigdy. Komentarz w workflowie chwali to
jako „kontrola nie wymaga żadnej listy do ręcznego utrzymywania", i to jest właśnie
cena tej oszczędności.

## 5. Bramka zepsuta w obie strony naraz

Bramka pilnująca, że runner testów liczy asercje, dopasowuje **tekst** pliku:

```
ORYGINAL   PASS 'AG.load_instrumented(path,name)'
PEP8       FAIL 'AG.load_instrumented(path,name)'
```

Pierwsze narzędzie stylu daje dwa fałszywe alarmy z przecinka. A w drugą stronę
podmiana ładowania modułów na wykonanie skompilowanego źródła, bez ani jednego
wystąpienia zakazanej nazwy, przechodzi **wszystkie cztery** asercje na zielono —
przy modułach idących bez licznika. Jedna przyczyna, dwa przeciwne skutki:
przyrząd, którego ktoś wyłączy, i przyrząd meldujący sprawdzenie, którego nie zrobił.

## 6. Ucięta liczba na ekranie

Panel interfejsu jest zakotwiczony po jednej stronie ze stałym odsunięciem, więc przy
węższym widoku i realnej dwujęzycznej nazwie stacji zrzut pokazuje wiersz urwany na
krawędzi: widoczne „za 1" i nic dalej. **Odległość do peronu obcięta w połowie
liczby.** Obrazy obejrzane, nie odczytane z metryk.

Przy okazji: dane osi mają w komplecie osobne pola nazw francuskiej i niderlandzkiej,
**których nikt nie czyta**, a nazwa złączona pionową kreską jedzie na ekran jako znak
do czytania. To ta dwujęzyczność ucina wiersz — dwie pozycje, jeden objaw.

## 7. Co jeszcze potwierdzono pomiarem

| rzecz | dowód |
|---|---|
| opcja pakietu przyjmowana i ignorowana | absurdalna nazwa wobec osi deklarującej inną: `0 błędów`, `exit=0`; opcji nie podaje żaden krok CI |
| schemat manifestu dźwięku niesprawdzany | cztery mutacje łamiące schemat, każda `9/9 przeszło`; napis w polu zgody na redystrybucję jest prawdziwy dla warunku |
| narzędzie wołane przed instalacją | precedens zapisany w repozytorium z kodem wyjścia 127; dziś maskuje to wyłącznie cache |
| filtry nie obejmują lokalnych akcji | siedem luk w macierzy; jedna akcja bez ani jednego konsumenta bez filtra |
| wersja SDK niepinowana | brak pliku pinu w drzewie i w indeksie; bramka i `doctor.sh` czytają samą wersję główną |
| status „nie wiem" awansowany | cztery drogi do predykatu prawdziwego, w tym **literówka** w statusie |
| ścieżka SDK ze spacją | atrapa w katalogu ze spacją: `BRAK`; ta sama bez spacji: `ok` — i znika cały wiersz o wersji |
| deklarowane maksimum przyspieszenia | 1,342 dla pustego i 1,025 dla obciążonego wobec liczby z tabeli |
| README o jednym składzie | API dodawania składów, trzy fazy iterujące, osiem testów o dwóch |
| klasa pochodzenia parametru | jedna nazwa z trzech rozjechana, ta sama nieaktualna trójka w drugim pliku |

## 8. Jeden finding przeważony w dół — tym razem z lepszym kryterium

Sonda silnika nie porównuje zgłaszanej wersji z pinem, i to prawda. Ale mechanizm,
który u Blendera czynił sondę na obecność **szkodliwą** — menedżer pakietów kładący
starą wersję pod nieuwersjonowaną nazwą — tu nie ma odpowiednika: ścieżka silnika
jest sparametryzowana wersją dwukrotnie, w katalogu i w nazwie pliku. Zostaje luka
kontraktowa, nie scenariusz rutynowy.

Różnica wobec §3: tam obniżałem wagę na podstawie **prawdopodobieństwa**, tu obniżam
ją na podstawie **braku mechanizmu**. Pierwsze było błędem, drugie jest wnioskiem.

## 9. Czego agenci nie sprawdzili — policzone, nie przemilczane

Z macierzy bramek liczącej 31 wierszy rozstrzygnięto pomiarem **cztery**;
**dwadzieścia siedem zostało nietkniętych** i są wymienione z nazwy w wyniku agenta
— cała rodzina silnika i odtwarzania zapisu, pętla linii z nawrotem, instalatory.
Wszystkie wymagają narzędzi, które nie mieściły się w budżecie czasu. Podtabeli
o regułach konstytucji nie ruszano wcale, z podanym powodem: jej wiersze są
granicami dowodu audytu, nie twierdzeniami o mutacjach.

Jeden agent nie obejrzał na oczy pary renderów `_iso` i `_side`, mając dla nich
tylko pomiar bajtowy — i powiedział to wprost, zamiast opisać obraz, którego nie
widział.

## 10. Stan drzewa i higiena rundy

Wszyscy pięciu skończyli z `git status --porcelain` pustym. Mutacje na plikach
w repozytorium wykonano tylko tam, gdzie było to konieczne, każdą z sumą kontrolną
przed i po; wszystkie potwierdzenia przywrócenia to `OK`.

Jedno zdarzenie warte zapisu: zewnętrzna kontrola zgłosiła w trakcie rundy
niezacommitowane zmiany w pliku osi. Suma kontrolna zgadzała się z wierzchołkiem,
a agent zaobserwował okno, w którym plik był zmodyfikowany i wrócił do stanu
poprzedniego. To ślad narzędzia mutacyjnego, które mutuje dane **w miejscu**.
Ostrzeżenie było więc prawdziwe co do stanu drzewa i mylące co do przyczyny — i to
jest osobna pozycja kolejki, bo reguła o danych tylko do odczytu jest w tym
projekcie twarda, a narzędzie ją okresowo łamie nieodróżnialnie od złamania
przypadkowego.

## 11. Weryfikacja

```
  RAZEM 2066 testów, 110 modułów, kod 0
```

Kolejka po tej rundzie: **40** pozycji do wzięcia, przy progu dwunastu.
