# 6.D286 · Pole „Weryfikacja", które liczy wiersze, a mówi o zdaniach

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `51a1f5e`

## 1. O co pytała pozycja

6.D169 zmierzyło, że pole „Weryfikacja" jednej pozycji żądało siedmiu trafień
`grep -nic` i siedem dostało — ale zdań w populacji jest osiem. Akapit ma
sformułowanie rozcięte przez zawijanie, a `grep` dopasowuje w obrębie wiersza.
Pole nie kłamie o swojej liczbie; kłamie o tym, **czego ta liczba jest miarą**.
Ile pól ma tę własność, nie liczył nikt.

## 2. Trzy liczby

Drzewo `51a1f5e`, `docs/TASKS.md`:

| | |
|---|---|
| bloków z polem „Weryfikacja" | trzysta sześćdziesiąt jeden |
| komend w tych polach | pięćset czterdzieści dwie |
| wywołań `grep` | piętnaście |
| **wywołań ze wzorcem zawierającym spację** | **sześć**, w **pięciu** pozycjach |
| **z tego rozjazd `grep` wobec czytnika akapitowego** | **cztery** |

Lista imienna wzorców wielowyrazowych: **5.6** (dwa wywołania), **6.A27**, **6.B15**,
**6.D169**, **6.D56**.

Lista imienna rozjazdów: **5.6**, **6.A27**, **6.B15**, **6.D169**.

## 3. Czwarta liczba: rozjazdy są DWOJAKIE, a pole pytało o jedną

To jest wynik, którego pozycja nie przewidywała, i zmienia on odczytanie tabeli wyżej.

**Ukrywa trafienie** — czytnik akapitowy widzi WIĘCEJ niż `grep`, bo zawijanie
chowa dopasowanie: **jeden** przypadek, `6.D169`, siedem wobec ośmiu. To jest
zjawisko, dla którego ta pozycja powstała.

**Skleja trafienia** — `grep` widzi WIĘCEJ, bo kilka pasujących wierszy stoi
w jednym akapicie: **trzy** przypadki. `5.6` osiem wobec sześciu, `6.A27` sześć
wobec trzech, `6.B15` dziewięćdziesiąt jeden wobec osiemdziesięciu ośmiu.
Tu zawijanie niczego nie chowa i pole nie wprowadza nikogo w błąd.

Sama liczba „rozjazdów" zlewa więc dwa różne zjawiska. Podaję obie, bo tylko
pierwsza mówi o usterce, którą 6.D169 nazwało.

## 4. Przyrząd potwierdzony na pomiarze, którego nie widział

Dla `6.D169` czytnik daje **siedem** wierszami i **osiem** akapitami — dokładnie tę
parę, która stoi w `reports/6d169-zdanie-o-maszynie-bez-daty.md` §3. Liczby nie
zostały przepisane z tamtego raportu: wyszły z czytnika napisanego tutaj, na
dzisiejszym drzewie.

## 5. Pierwsza wersja czytnika gubiła przypadek założycielski

Przewidywanie czwarte brzmiało: „najtrudniejszą częścią nie będzie złożenie akapitu,
tylko **wyłuskanie wzorca** z wołania `grep`". Trafione, i to dosłownie.

Pierwsza wersja cięła komendę na wywołania **po znaku** `|`. Wzorzec 6.D169 brzmi
`tej maszynie\|tym kontenerze\|czystej maszynie` i niesie dwa `\|` — czytnik rozcinał
go więc w środku. Efekt: **jedenaście** wywołań zamiast piętnastu, **dwa** wzorce ze
spacją zamiast sześciu, i **ani jednego** z 6.D169. Czyli sito gubiło dokładnie ten
przypadek, o którym z góry wiadomo, że należy do listy.

Złapało to porównanie z listą zrobioną okiem, a nie test. Poprawka: cięcie po
**tokenach** z `shlex`, gdzie `|` wewnątrz cudzysłowu zostaje częścią wzorca.
Osobno doszła obsługa komentarza powłoki (`comments=True`) — bez niej ogon
`# nagłówek sekcji` z pola 5.6 wchodził do listy celów jako trzy pliki.

## 6. Przewidywania wobec pomiaru

| co | przewidziane | zmierzone |
|---|---|---|
| wzorców ze spacją | sześć | **sześć wywołań, ale w pięciu pozycjach** |
| rozjazdów | jeden | **cztery** |
| lista imienna | tylko 6.D169 | **cztery pozycje** |
| najtrudniejsze będzie wyłuskanie wzorca | tak | **tak, i wywróciło pierwszy przebieg** |
| kontrola negatywna zadziała za pierwszym razem | tak | **tak** |
| kontrola przyrządu zadziała | tak | **tak** |
| nie będzie trzeba kopii drzewa z `.git` | tak | **tak** |

Dwa pierwsze nietrafione; trzy przewidywania o kształcie trafione.

## 7. Kontrole

**Kontrola negatywna** — atrapa tekstu, dwa bloki: jeden ze wzorcem jednowyrazowym,
drugi z wielowyrazowym. Na listę trafia wyłącznie drugi:

```
  6.X1   wzorzec='jednowyrazowy' spacja=False
  6.X2   wzorzec='tej maszynie\|tym kontenerze' spacja=True
KN — na liscie stoi: ['6.X2']
```

**Kontrola przyrządu** — na dzisiejszym drzewie lista zawiera `6.D169`. Zawiera.

Kopia drzewa z `.git` nie była potrzebna: `backlog_commands.inventory(text=…)`
przyjmuje napis wprost, więc atrapa wystarcza. Przewidziane i potwierdzone.

## 8. Czego świadomie nie zrobiłem

- **Nie poprawiłem ani jednego pola „Weryfikacja"** — pole „Poza zakresem" mówi
  o tym wprost, a każda taka poprawka zmienia liczbę, której to pole pilnuje.
- **Nie zszyłem zawijania w żadnym pliku**, na który te polecenia wskazują.
- **Nie zmieniłem wzorców w tych poleceniach.**
- **Nie postawiłem bramki.** Pole „Wyjście" żąda trzech liczb i listy, a nie sita
  w drzewie; precedens 6.D282, gdzie odsianie zrobiono w pomiarze, a nie w module.
  Czytnik został więc w scratchpadzie razem z kontrolami.

## 9. Co zauważyłem, a czego nie tknąłem

- Trzy z czterech rozjazdów są klasy „skleja", czyli nieszkodliwej. Gdyby ktoś
  poprawiał pola według samej liczby rozjazdów, poprawiłby trzy pola, którym nic
  nie dolega — i to jest dokładnie ten kształt błędu, który ta pozycja opisuje,
  tylko o poziom wyżej.
- `5.6` ma w poleceniu ogon `# nagłówek sekcji`, który bez obsługi komentarzy
  powłoki wygląda jak trzy dodatkowe ścieżki. Żadna bramka pól tego nie widzi.

## 10. Weryfikacja

```
$ python3 tools/tests/test_all.py
  2662/2662 przeszło
  RAZEM 343.502 s, 2662 testów, 139 modułów
EXIT=0
```

Zestaw jest zielony i liczy tyle samo testów, co przed tą pozycją — bo bramki
nie przybyło. Czytnik i obie kontrole stoją w scratchpadzie, a ich wyjścia
są wklejone w §7.
