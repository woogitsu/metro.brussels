# 6.D110 — pięć kopiowań, żadne do drzewa

**Zmierzone 10.09.2026 na:** `6f0f48a`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_tree_writes.py` (`miejsca_zapisu`, `kopiowania_modulu`,
`KSZTALTY_KOPIUJACE`, `METODY_SCIEZKI`, `POZA_DRZEWEM`, `MAX_ZAPISOW_W_DRZEWIE`),
skan drzewa składni po `tools/tests/` — wszystkie moduły wyłącznie do odczytu.

---

## 1. Rozstrzygnięcie, o które prosi wpis

Pole „Wyjście" żąda, żeby skan rozpoznawał także `shutil.copy*`, `os.replace`
i `pathlib.Path.write_*` z celem zbudowanym z `ROOT`, żeby liczba miejsc została
przeliczona, zapadka ustawiona na wynik pomiaru, a miejsca legalne wpisane do `DLUG`
z powodem. Pole „Skończone, gdy" dodaje warunek arytmetyczny: **sześć** zmierzonych
miejsc ma być rozstrzygniętych, a suma rozstrzygnięć ma zgadzać się z pomiarem.

Skan jest rozszerzony. Reszta wyszła inaczej, niż zapowiada wpis, i to jest wynik.

## 2. Pomiar: pięć wywołań, ani jedno nie celuje w drzewo

```
mutation_sweep.py       (819, 'zapisz_pokrycie',      'os.replace',       'path',   False)
test_ci_workflows.py    (832, '_run_blender_installer','shutil.copyfile', 'script', False)
test_dotnet_version.py  (1191,'_atrapa_dotnet_root',  'shutil.copy2',     'cel',    False)
test_mutation_sweep.py  (63,  '_cele_na_boku',        'shutil.copyfile',  'kopia',  False)
test_mutation_sweep.py  (1958,'test_a_remembered_map…','os.replace',      'cudzy',  False)
kopiowań razem: 5
miejsc zapisu razem: 5
```

Ostatnia kolumna jest tu całą treścią: **`False` przy każdym**. Cel każdego z tych
pięciu wywołań stoi w katalogu tymczasowym albo w kopii na boku — sprawdzone przez
przeczytanie wszystkich pięciu miejsc, nie tylko przez skan. `zapisz_pokrycie` pisze
do `tempfile.gettempdir()`, atrapa CI i atrapa układu .NET budują się w katalogach
tymczasowych, `_cele_na_boku` jest **wzorem**, do którego 6.D90 przeniosło zapisy,
a przeniesienie mapy w `test_a_remembered_map…` dzieje się w obrębie jednego `tmp`.

**Zapadka nie drgnęła.** `MAX_ZAPISOW_W_DRZEWIE` stoi na tym samym, na czym stała,
i to jest wynik pomiaru, a nie brak zmiany: do zapadki nie weszło żadne z pięciu.

## 3. Sześć z wpisu się nie odtwarza — sześć daje `grep`

Wpis mówi o **6** miejscach. Tyle daje wyszukiwanie po napisach:

```
$ grep -c … po stanie z `6f0f48a`
tools/tests/mutation_sweep.py       2
tools/tests/test_ci_workflows.py    1
tools/tests/test_dotnet_version.py  1
tools/tests/test_mutation_sweep.py  6
tools/tests/test_osm_tile_cache.py  1
tools/tests/test_tree_writes.py     1
                            razem  12
```

Skan drzewa składni liczy **wywołania**, nie wystąpienia napisu, i znajduje **pięć**.
Różnica to wiersze komentarza, w których te same nazwy stoją jako temat zdania —
między innymi w docstringu samej bramki, w akapicie mówiącym, że tych kształtów
nie łapie.

## 4. Trzeciego rozstrzygnięcia wpis nie przewidział

Pole „Skończone, gdy" zna dwie szuflady: **objęte zapadką** albo **wpisane do `DLUG`
z powodem**. Zmierzone miejsca nie pasują do żadnej, bo obie dotyczą zapisu **do
drzewa**, a tych zapisów nie ma. Wpisanie ich do `DLUG` byłoby nieprawdą: `DLUG` to
lista rzeczy **do spłacenia**, a tu nie ma czego spłacać.

Stąd trzecia szuflada, `POZA_DRZEWEM` — nie lista wyjątków, tylko lista
**rozstrzygnięć**, po jednym na każde zmierzone wywołanie, z powodem. Pilnują jej
dwie asercje o przeciwnych kierunkach: żadne wywołanie nie może celować w drzewo,
a zbiór wywołań zmierzonych musi być **równy** zbiorowi wpisanych. Miejsce, które
zniknie, zapala listę tak samo jak miejsce dopisane.

## 5. Dlaczego drugi czytnik, a nie jeden

`miejsca_zapisu` widzi wyłącznie to, co celuje w `ROOT` — dla niego wszystkie pięć
zmierzonych miejsc **nie istnieje**. Lista rozstrzygnięć ma się rozstrzygać
o miejscach istniejących, więc potrzebuje czytnika, który je widzi razem z werdyktem:
`kopiowania_modulu` zwraca każde wywołanie z flagą `czy_do_drzewa`. Bez tego
„miejsce zniknęło" i „miejsce przestało celować w drzewo" byłyby dla przyrządu
jednym zdarzeniem.

Numer argumentu docelowego jest w tabeli `KSZTALTY_KOPIUJACE`, a nie w kodzie, bo
we wszystkich pięciu funkcjach plik **pisany** stoi na drugim miejscu, a na pierwszym
stoi plik **czytany**. Skan biorący argument zerowy meldowałby zapis tam, gdzie jest
odczyt — i to nie jest hipoteza, tylko KN-2 niżej.

## 6. KN-7 wyszła ZIELONA i to jest najważniejsza rzecz w tej pozycji

Kontrola przestawiła flagę `czy_do_drzewa` na stałe `False`. Zestaw: **6/6, zielony**.

Powód jest ten sam, co przy KN-4 w 6.D103 i KN-3 oraz KN-6 w 6.D105: dziś **żadne**
z pięciu miejsc nie celuje w drzewo, więc asercja „nic nie celuje w drzewo" jest
spełniona **pusto** i przechodzi identycznie dla czytnika działającego i zepsutego.
Kontrola na drzewie mierzyła tu nie to, co miała mierzyć.

Flagę pinuje od tej pozycji `test_czytnik_rozstrzygniec_odroznia_cel_w_drzewie_od_celu_na_boku`
— para wejść syntetycznych, cel z `ROOT` i cel tymczasowy. Po jego dopisaniu ta sama
mutacja świeci na czerwono (KN-7b).

## 7. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem (procedura z 6.D102), po każdej
`md5sum -c` na dwóch plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | `os.replace` znika z tabeli kształtów | 4/6, dwa testy |
| KN-2 | cel `copyfile` brany z argumentu zerowego | **2/6, cztery testy** |
| KN-3 | prawdziwe miejsce zaczyna celować w drzewo | 3/6, trzy testy |
| KN-4 | jeden wpis znika z listy rozstrzygnięć | 5/6 |
| KN-5 | metody `pathlib.Path` przestają być rozpoznawane | 5/6 |
| KN-6 | cel podany słowem kluczowym przestaje być czytany | 5/6 |
| KN-7 | flaga `czy_do_drzewa` na stałe `False` | **6/6 ZIELONA** |
| KN-7b | ta sama mutacja po dopisaniu wejścia syntetycznego | 6/7 |

**KN-2 jest warta osobnego zdania**, bo pokazuje, co dokładnie kupuje numer argumentu:
po przestawieniu go na zerowy bramka zgłasza `INSTALLER` i `zrodlo` — dwa pliki
**czytane** ze ścieżek zbudowanych z `ROOT`. To jest fałszywy alarm o dokładnie tej
postaci, którą projekt tropi od 6.D27: przyrząd meldujący naruszenie, którego nie ma.

**KN-3 pokazuje kierunek przeciwny na PRAWDZIWYM miejscu:** po przestawieniu
`_cele_na_boku` na cel z `ROOT` zapalają się trzy testy naraz, w tym zapadka
(`miejsc zapisu jest 6 przy zapadce 5`).

## 8. Weryfikacja

```
$ python3 tools/tests/test_all.py test_tree_writes.py
  7/7 przeszło          (było 4)

$ python3 tools/tests/test_all.py
  2234/2234 przeszło, 119 modułów, RAZEM 131.607 s
```

## 9. Czego nie zrobiłem

- **Nie dopisałem niczego do `DLUG`** — nie ma czego, patrz §4. Lista długu zostaje
  na dwóch wpisach, a jej kontrola gnicia jest nietknięta.
- **Nie obniżyłem zapadki**, bo pomiar nie dał niższej liczby; podnieść jej i tak
  nie wolno.
- **Nie tknąłem zapisu przez podproces ani przez bibliotekę zewnętrzną** — pole
  „Poza zakresem" wyklucza to wprost.
- **Nie naprawiałem długu z `DLUG`** — ma własne pozycje, i tak mówi pole
  „Poza zakresem".
- **Nie dopisałem `shutil.copytree` ani `os.link`** do tabeli kształtów: w drzewie
  nie występują, a rozszerzanie o kształty niewystępujące jest zgadywaniem — tę
  regułę zapisało 6.D90 i ona się nie zmieniła. `copy`, `move` i `rename` są w tabeli
  mimo braku wystąpień, bo mają **identyczną sygnaturę** z tymi, które wystąpiły;
  pominięcie ich znaczyłoby, że jedna litera w nazwie wyłącza bramkę.

## 10. Zauważone przy okazji

- **`test_dotnet_version.py:1188` pisze przez `open(cel, "wb")`, gdzie `cel` biegnie
  z katalogu tymczasowego** — i to jest w porządku, ale pokazuje, że dwa kształty
  stoją w jednej funkcji obok siebie. Skan czyta oba tą samą regułą, więc rozjazd
  między nimi jest niemożliwy; warto, żeby tak zostało.
- **Propagacja nazw jest płytka i to nadal jest wybór 6.D90.** `pelna = os.path.join(ROOT, x)`
  a potem `shutil.copy2(z, pelna)` skan widzi; dwóch przypisań pod rząd już nie.
  W drzewie taki kształt nie występuje, a głębsza analiza przepływu kupiłaby przede
  wszystkim fałszywe alarmy.
