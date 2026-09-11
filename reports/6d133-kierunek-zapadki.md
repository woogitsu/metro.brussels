# 6.D133 — trzydzieści osiem zapadek, dwadzieścia jeden do ruszenia bez śladu

**11.09.2026**, na `52752c9`. Pozycja pytała, ile zapadek ma kształt, przy którym
regułę „wolno tylko obniżać" można złamać bez zapalenia czegokolwiek, i czy kierunek
da się przybić bramką **bez drugiej listy, która sama się rozjedzie**.

## 1. Liczby

Skan `tools/tests/` (z `mutation_sweep.py`, który tam leży) po stałych o nazwie
`MAX_*`, `MIN_*`, `MINIMUM_*`:

| klasa | ile | co znaczy |
|---|---|---|
| **przybita** | **13** | ruch o jeden w zakazaną stronę zapala bramkę |
| **częściowa** | **3** | ruch o jeden przechodzi; pada dopiero ruch daleki |
| **wolna** | **21** | ruch w zakazaną stronę nie zapala niczego |
| poza skanem | 1 | próg trafia do porównania przez zmienną — patrz §4 |
| **razem** | **38** | |

Zakazana strona wynika z przedrostka: `MAX_` wolno tylko obniżać, `MIN_` i `MINIMUM_`
tylko podnosić. Ale to jest zdanie **dla człowieka** — bramką jest dopiero porównanie,
które przy takim ruchu pada.

## 2. Jak to jest liczone

Każde porównanie czytane jest **od strony stałej**, po odwróceniu operatora, gdy stała
stoi po prawej: `len(x) <= MAX_Y` i `MAX_Y >= len(x)` są jednym zdaniem i muszą wpaść
do jednej kupki. Bez tego klasyfikacja zależałaby od tego, po której stronie ktoś stałą
napisał — czyli od nawyku pisania, nie od właściwości bramki.

* **nośne** — porównanie, dla którego zapadka jest progiem (`MAX_X >= ile`); pada, gdy
  rośnie DRZEWO, a nie gdy rusza się stała;
* **strzegące** — porównanie z drugiej strony (`MAX_X <= ile`); pada, gdy stała idzie
  w zakazaną stronę. Równość strzeże w obie.

`przybita` znaczy: strażnik mierzy **tę samą populację**, co próg (albo jest równością).
`częściowa`: strażnik jest, ale o innej populacji.

## 3. Klasyfikacja sprawdzona ruchem, nie tylko kodem

Osiem zapadek ruszonych w zakazaną stronę, każda ze swoją klasą:

| zapadka | klasa | ruch | wynik |
|---|---|---|---|
| `MAX_WOLNO_WPROST`, wyjątki `os.walk` | wolna | 2 → 9 | **13/13, kod 0** |
| `MIN_MESSAGES`, próg komunikatów | wolna | 97 → 1 | **11/11, kod 0** |
| `MIN_REPORTS`, próg liczby raportów | przybita | 252 → 10 | 16/18, dwa testy |
| `MAX_ZAPISOW_W_DRZEWIE`, miejsca zapisu | przybita | 5 → 40 | 7/8 |
| `MINIMUM_SUPPORTED_MAJOR`, wersja .NET | częściowa | 10 → 3 | 48/49 |
| `MINIMUM_SUPPORTED_MAJOR`, ta sama | częściowa | 10 → **9** | **49/49, kod 0** |
| `MINIMUM_POWODU`, długość uzasadnienia | częściowa | 120 → **119** | **22/22, kod 0** |
| `MINIMUM_DOCUMENTED_ITEMS`, zapas opisany | częściowa | 6 → **5** | **31/31, kod 0** |

Trzy ostatnie wiersze są całą treścią klasy „częściowa": strażnik istnieje, ale stoi
tak daleko, że ruch o jeden przez niego przechodzi.

## 4. Czego klasyfikator nie widzi — zmierzone, nie zastrzeżone

Czyta wyłącznie węzły `Compare`, w których stała stoi **po imieniu**. `MIN_PATHS`
jest słownikiem trzech progów i trafia do porównania przez zmienną pętli
(`for field, floor in MIN_PATHS.items()`), więc jego nazwa w żadnym porównaniu nie pada.
Klasa `POZA_SKANEM` mówi dokładnie to — i **nie** mówi „nieużywana". Jest jedna taka
zapadka na 38, a bramka pilnuje zarówno jej klasy, jak i tego, że kształt, na którym
klasa stoi, nadal jest w `test_field_paths.py`.

## 5. Rozstrzygnięcie

**Kierunek da się przybić maszynowo i drugiej listy do tego nie trzeba** — klasa każdej
zapadki jest **policzalna z drzewa składni**, więc lista nazw z klasami jest porównywana
z drzewem w obie strony i rozjechać się nie może. To ta sama konstrukcja, co
`NIEME_ASERCJE` z 6.D127.

Lista jest z **nazwami**, nie z samymi liczbami: same liczby przepuściłyby zamianę jednej
zapadki przybitej na inną wolną — suma stoi, a zdanie o konkretnej zapadce przestaje być
prawdziwe.

**Wartości zapadek nie ruszam** („Poza zakresem"). Dwadzieścia jeden wolnych zostaje
wolnych; ta pozycja daje im **widoczność**, a nie strażników. Przybicie każdej z nich to
praca wobec innej populacji i innej bramki, czyli osobne pozycje.

## 6. Osobna bramka na liczbę wolnych — napisana i USUNIĘTA po pomiarze

Napisałem najpierw `test_wolnych_zapadek_moze_tylko_UBYWAC`, z oboma kierunkami. Kontrole
pokazały, że **nie zapala się nigdy sama**:

* **KN-1** (nowa wolna zapadka w drzewie) zapaliła ją **razem** z testem listy;
* **KN-5c** (wolnej zapadce przybywa strażnik, wpis niepoprawiony) zapaliła **sam** test
  listy — bramka liczbowa milczała;
* **KN-5** (zdjęcie jej połowy o przybyciu strażnika) wyszła **ZIELONA**.

Lista z nazwami jest ściśle mocniejsza od liczby. Bramka, której żadna kontrola nie umie
zapalić w pojedynkę, jest zielenią uspokajającą, nie pomiarem — więc zniknęła, a liczba
została jako **asercja zbiorcza wewnątrz testu listy**.

**I ta asercja zbiorcza NIE jest ozdobnikiem — pokazała to KN-7.** Gdy ktoś przybije wolną
zapadkę i **uczciwie** poprawi jej wpis, wszystkie asercje o zgodności listy z drzewem
przechodzą, a zdanie „21 wolnych" — publikowane w komentarzu i w tym raporcie — staje się
nieprawdą, której nie zgłasza nic. KN-7 wykonała dokładnie ten scenariusz i **jedyną
czerwienią była ta asercja**:

```
FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem: klasy zapadek:
     przybitych 13, częściowych 4, WOLNYCH 20, poza skanem 1 — pomiar z 11.09.2026
     mówił 13/3/21/1
```

## 7. Kontrole negatywne

Baza `test_tree_walks.py`: **17/17** (było 13). `__pycache__` czyszczony przed każdym
przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK`.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | nowa zapadka WOLNA dopisana do drzewa | **16/18**, dwa testy |
| KN-2 | strażnik zdjęty z `MAX_ZAPISOW_W_DRZEWIE`, czyli z równości | **16/18**, dwa testy |
| KN-3 | tabela `ODWROTNY_OPERATOR` zdjęta | **14/18**, cztery testy |
| KN-4 | każdy strażnik liczony jako przybicie | **16/18**, dwa testy |
| KN-5 | zdjęta połowa bramki liczbowej | **18/18 ZIELONA** → §6 |
| KN-5b | wolnej zapadce przybywa strażnik | **16/18**, dwa testy |
| KN-5c | to samo przy bramce jednokierunkowej | **17/18**, sam test listy |
| KN-6 | klasa `POZA_SKANEM` zwinięta do `WOLNA` | **15/18**, trzy testy |
| KN-7 | strażnik + UCZCIWIE poprawiony wpis | **16/17**, sama asercja zbiorcza |

KN-3 jest tu najszerszą: bez odwracania operatora **34 z 38** zapadek zmienia klasę,
w tym 20 wpada do `poza skanem` — czyli strona zapisu decydowałaby o wszystkim.

## 8. Poprawiony adres w polu „Weryfikacja"

Pole wołało `test_scan_gates.py`, a ten moduł mierzy `tools/blender/scan_gates.py`, czyli
predykaty bramek skanu **luzu** — z przejściem po `tools/tests/` nie ma wspólnego nic
prócz słowa „skan" w nazwie. Modułem skanów po `tools/tests/`, o którym mówi zdanie niżej
w tym samym polu, jest `test_tree_walks.py`. Poprawka idzie z adnotacją
`**Poprawione 11.09.2026 przy 6.D133:**`, a `POPRAWEK_W_DRZEWIE`, zapadka adnotacji, idzie z 5 na 6 — dokładnie ten
kształt rozstrzygnęło 6.D126.

## 9. Weryfikacja

```
  17/17 przeszło        test_tree_walks.py   (było 13)
  2330/2330 przeszło, 122 moduły, KOD=0
```

## 10. Czego nie zrobiłem

* **Nie zmieniłem wartości ani jednej zapadki** — wprost w „Poza zakresem".
* **Nie przybiłem żadnej z 21 wolnych.** Każda wymaga strażnika wobec własnej populacji,
  czyli własnego pomiaru; hurtowe dopisanie `MAX_X <= len(cokolwiek)` dałoby 21 zapadek
  klasy `częściowa`, czyli liczbę ładniejszą i ochronę tę samą.
* **Nie objąłem skanem `tests/Sim.Tests` ani `src/`.** Pole „Wejście" mówi `tools/tests/`,
  a zapadki po stronie C# mają inny kształt (`Assert.AreEqual` z liczbą, nie stała
  porównywana nierównością).
