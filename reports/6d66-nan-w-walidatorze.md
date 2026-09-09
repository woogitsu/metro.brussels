# Walidator, który ogłaszał zgodność, gdy różnica nie była liczbą (6.D66)

**Zmierzone 09.09.2026 na:** `bd53d36`, kontener tej sesji.
**Przyrząd:** `tools/track/validate.py`, `tools/tests/test_validate_axis.py`,
kopie osi w katalogu tymczasowym, `python3 tools/tests/test_all.py`.

---

## 1. Usterka

Wartość nieliczbowa w pliku osi nie była przemilczana — walidator **ogłaszał
zgodność**. Ten sam plik przed i po poprawce:

```
przed:  kod=0   ·   punktów: 447, długość osi: nan m
                ·   length_m zgodne z łamaną, różnica nan mm
                    0 błędów, 1 ostrzeżeń

po:     kod=1   X   nie da się wczytać pliku: plik niesie literał `NaN`,
                    którego JSON nie dopuszcza — oś musi nieść same liczby skończone
                    1 błędów, 0 ostrzeżeń
```

Mechanizm: porównania z wartością nieliczbową są **zawsze fałszywe**, więc każdy
próg niżej — długości, pochylenia, promienia, odstępu stacji — wykonywał gałąź
„w porządku". Jeden zły znak w jednej współrzędnej wyłączał wszystkie kontrole
tego pliku naraz, i to bez śladu.

## 2. Rozróżnienie, którego nie miałem na początku

Pozycja mówiła o „wartości nieskończonej albo nieliczbowej" jako o jednym
zjawisku. Pomiar rozdzielił je i to zmienia treść poprawki.

**Wartość nieliczbowa przechodziła w milczeniu**, bo `nan > próg` jest fałszem.
To była prawdziwa dziura.

**Nieskończoność nie przechodziła.** Istniejące progi ją odrzucały, bo `inf > próg`
jest prawdą — ale komunikatami, które wskazują na złą rzecz. Zmierzone na trzech
kontrolach negatywnych:

| gdzie | co mówił walidator bez nowej kontroli |
|---|---|
| współrzędna punktu | `odstęp punktów 0→1 = inf m, maks. 25.0 m` |
| `length_m` | `length_m = inf m nie zgadza się z łamaną (20.000 m), różnica inf m` |
| `chainage_m` stacji | `kilometraż stacji nie jest rosnący` oraz `odstęp stacji A → B = -inf m` |

Każdy z tych komunikatów zaprasza czytającego do **poprawienia liczby**, gdy
problemem jest to, że to nie jest liczba. Poprawka ma więc dwie różne wartości
i warto je rozdzielić: odmowa literału zamyka **rzeczywistą dziurę**, a kontrole
skończoności zamieniają **mylące odmowy na trafne** i stawiają je przed rachunkiem.

## 3. Dlaczego DWIE kontrole, a nie jedna

`json` Pythona przyjmuje `NaN`, `Infinity` i `-Infinity` jako literały, wbrew
samemu formatowi JSON — to zamyka `parse_constant`. Ale to nie wystarcza,
i jest to zmierzone:

```
literał NaN:       {'x': nan}
literał Infinity:  {'x': inf}
1e400 (bez NaN):   {'x': inf}  isfinite: False
```

**`1e400` jest poprawnym literałem JSON i staje się nieskończonością bez użycia
słowa `Infinity`**, więc odmowa stałych go nie widzi. Jedna kontrola łapie zapis,
druga przepełnienie; żadna nie zastępuje drugiej.

## 4. Cztery drogi wejścia, każda zmierzona osobno

```
a_literal_nan    kod=1  X  nie da się wczytać pliku: plik niesie literał `NaN`…
b_przepelnienie  kod=1  X  punkt 0, współrzędna x = inf nie jest liczbą skończoną…
c_length         kod=1  X  length_m = inf nie jest liczbą skończoną…
d_chainage       kod=1  X  stacja 0, chainage_m = inf nie jest liczbą skończoną…
```

W przypadku (d) walidator wypisuje przy tym `length_m zgodne z łamaną, różnica
3.6 mm` — i to jest poprawne: geometria w tym pliku jest nietknięta, więc ogłasza
zgodność wielkości, którą **naprawdę sprawdził**.

## 5. Mój własny test nie mógł paść, i złapała to kontrola negatywna

Pierwsza wersja testu dla `length_m` asertowała obecność nazwy pola w komunikacie
błędu. Kontrola negatywna pokazała `42/42 przeszło` **po zdjęciu kontroli** —
bo przy nieskończoności odmawia też istniejący próg dryfu, a jego komunikat też
zawiera `length_m`. Test przechodził w obu wersjach, czyli był bramką, która nie
może paść: dokładnie rodzina, którą ta sesja tropi od rana.

Poprawione: asercja jest teraz przypięta do **powodu**, nie do nazwy pola, i żąda
dodatkowo, żeby odmowa **nie** nazywała niezgodności z łamaną. Po tej zmianie
kontrola zapala się:

```
FAIL test_nieskonczona_dlugosc_i_kilometraz_tez_sa_ODMOWA:
  ['length_m = inf m nie zgadza się z łamaną (20.000 m), różnica inf m']
```

## 6. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| zdjęte wszystkie cztery kontrole naraz | `kod=0`, `różnica nan mm`, `0 błędów` — pierwotny objaw odtworzony |
| zdjęta odmowa literałów | `41/42`, odmowa spada do kontroli współrzędnych (nakładają się dla literału) |
| zdjęta kontrola współrzędnych | `41/42`, komunikat zmienia się na `odstęp punktów 0→1 = inf m` |
| zdjęta kontrola `length_m` | `41/42` **po wzmocnieniu asercji**; przed nim `42/42`, patrz §5 |
| zdjęta kontrola `chainage_m` | `41/42`, komunikat zmienia się na `kilometraż stacji nie jest rosnący` |

`md5sum -c` po każdej: `OK`.

Osobny test pilnuje **odwrotnego kierunku**: zero, wartość ujemna zerowa i `1e-12`
są liczbami skończonymi i muszą przejść. Bez niego odmowa mogłaby być za szeroka,
a sentinele `float("inf")` używane **wewnątrz** walidatora (promień prostego
odcinka) nie są danymi wejściowymi — gdyby ta kontrola ich dotyczyła, każda prosta
oś byłaby odrzucona.

## 7. Weryfikacja

```
  42/42 przeszło       test_validate_axis.py  (0.109 s)
  RAZEM 124.604 s, 2074 testów, 110 modułów
kod=0
```

Zestaw przed pozycją: 2070 testów.

## 8. Czego świadomie nie zrobiono

Nie tknięto `data/` — wszystkie pomiary na kopiach w katalogu tymczasowym.
Nie zmieniono ani jednej tolerancji: poprawka dodaje odmowy przed rachunkiem,
nie rusza progów.

Nie usunięto kontroli `length_m` mimo tego, że przy nieskończoności odmawia też
próg dryfu (§2). Zostaje, bo różnica jest w komunikacie, a komunikat jest tu
całą wartością — ale to jest wybór, nie konieczność, i tak trzeba go czytać.

## 9. Co zauważone przy okazji, nie tknięte

**Zestaw przebiegł raz w 203,661 s.** Powtórzony na tym samym drzewie dał
124,604 s; kontener miał wtedy `up 10 min`, więc pierwszy przebieg najpewniej
nałożył się na jego rozruch. Mojej zmiany to nie dotyczy — nowy moduł kosztuje
**0,109 s** na 42 testy.

Pierwsze sformułowanie tego akapitu było błędne i jest tu przepisane, a nie
dopisane obok. Napisałem, że lista pomiarów „dowodzi marginesu, którego nie ma".
Log joba CI z tego samego commita mówi coś innego:

```
  RAZEM 53.117 s, 2074 testów, 110 modułów
```

**Na runnerze zestaw zajmuje 53,117 s** — mniej niż połowę pomiaru z kontenera
i ćwierć odstającego 203,661 s. Próg 150 s ma tam więc margines blisko trzykrotny,
a nie żaden.

Właściwa treść obserwacji jest inna i ostrzejsza: **lista pomiarów i próg, który
z niej wynika, żyją w dwóch różnych środowiskach.** Wszystkie wpisy listy opisują
kontener i obciążenie hosta („kontener DZIELONY", „host spokojny", „host pod
obciążeniem"), a próg jest egzekwowany krokiem CI **na runnerze**, gdzie ten sam
zestaw chodzi ponad dwukrotnie szybciej. Margines nie jest fałszywy — jest liczony
wobec złej populacji. Pomiar z kontenera nie mówi nic o tym, czy job CI zdąży,
a pomiaru z runnera na liście nie ma ani jednego.

To wymaga własnej pozycji i jej pytanie brzmi inaczej, niż napisałem najpierw: nie
„czy podnieść próg", a **czy lista ma zbierać pomiary z runnera, czy z kontenera**,
i czy jedna stała może służyć obu. Dziś służy jednemu, a jest uzasadniana drugim.
