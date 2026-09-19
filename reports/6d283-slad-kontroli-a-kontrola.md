# 6.D283 · Ślad kontroli a kontrola, której ślad dotyczy

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `54c6f70`

## 1. O co pytała pozycja

Kryterium śladu kontroli negatywnej w `test_commit_claims.py` sprawdza, czy w commicie
**stoi** raport w `reports/` albo plik testu — a nie, czy ten raport mówi o kontroli,
którą zgłasza komunikat. Populacja „zgłasza kontrolę ze śladem" jest więc **górną
granicą**, nie pomiarem zgodności. Pozycja żądała trzech liczb: dla ilu commitów raport
dopisany w tym samym commicie wymienia nazwę modułu albo zapadki, o której mówi
komunikat; dla ilu nie wymienia niczego wspólnego; dla ilu commit raportu nie dopisuje,
tylko plik testu.

## 2. Jak liczone

Porównywane są **nazwy**: moduły (`test_*.py`, wzorcem — rejestru modułów nie ma)
i zapadki (rejestr `ZAPADKI` **pożyczony** z `test_tree_walks.py`, nie przepisany).
Strona raportu to wiersze **dopisane** (`+`) w plikach `reports/*.md` tego commita,
czytane z tego samego przebiegu `git log -p`, w którym czytane są ścieżki i zapadki.
Strona komunikatu ma dwa warianty i oba stoją niżej, żeby nie trzeba było zgadywać,
który policzono:

- **wąski** — okno `OKNO_KONTROLI` wokół kotwicy kontroli negatywnej, to samo, którego
  `zglasza_wykonana_kontrole` używa do szukania śladu wykonania;
- **szeroki** — cały komunikat.

## 3. Trzy liczby

Populacja „zgłasza kontrolę **ze śladem**" na wierzchołku `main` (`54c6f70`): **475**.

| klasa | wąsko | szeroko |
|---|---|---|
| ślad **dotyczy** tej kontroli | **154** | **224** |
| raport jest, **nic wspólnego** | **208** | **138** |
| **bez raportu**, sam plik testu | **113** | **113** |
| razem | 475 | 475 |

Kryterium dzisiejsze mówi „ślad" o wszystkich 475. Zaciśnięte mówi to o 154 (wąsko)
albo 224 (szeroko) — czyli o **jednej trzeciej** albo **niecałej połowie** populacji.

## 4. Czego sama liczba nie mówi — rozbicie klasy „nic wspólnego"

| przyczyna | wąsko | szeroko |
|---|---|---|
| komunikat nie nazywa **niczego** | 173 | 80 |
| raport nie nazywa niczego | 11 | 27 |
| obie strony nazywają, ale **co innego** | 24 | 31 |

To jest wynik, którego nie przewidziałem i który zmienia odczytanie całej tabeli wyżej:
w wariancie wąskim **173 z 208** braków to nie „raport o czym innym", tylko komunikat,
który w oknie kontroli nie wymienia ani jednej nazwy. Wąska liczba mierzy więc w dużej
mierze **zwyczaj pisania komunikatów**, a nie rozjazd raportu z kontrolą. Rozjazdów
rzeczywistych — obie strony nazywają, nazwy różne — jest **24** wąsko i **31** szeroko.

## 5. Zgodność, która o niczym nie mówi

`MIN_REPORTS` podnosi **każdy** commit dopisujący raport, a `test_all.py` stoi w każdym
poleceniu weryfikacji. Zgodność opartą wyłącznie na tej parze ma **41** commitów wąsko
i **54** szeroko — czyli ponad jedna czwarta klasy „dotyczy" w wariancie wąskim trzyma
się na nazwie, która stoi wszędzie. Po odjęciu tych commitów zostaje **113** wąsko
i **170** szeroko. Nie są wyrzucone, tylko liczone osobno: wyrzucenie byłoby oceną,
osobne liczenie jest pomiarem, a `test_zgodnosc_na_samych_nazwach_wszechobecnych_jest_liczona_OSOBNO`
pilnuje, żeby podzbiór pozostał **właściwy** — zero znaczyłoby, że przestał być czytany,
a równość klasie, że klasa nie mówi o niczym poza nim.

## 6. Przewidywania wobec pomiaru

Przewidywania pisane przed przebiegiem, w `6d283-przewidywania.md` scratchpada.

| co | przewidziane | zmierzone |
|---|---|---|
| klasa „dotyczy" (wąsko) | 250 | **154** |
| klasa „nic wspólnego" (wąsko) | 90 | **208** |
| klasa „bez raportu" | 130 | **113** |
| populacja ze śladem | 470 | **475** |
| różnica szeroko − wąsko w klasie „dotyczy" | ~40 | **70** |

Pierwsze dwie pozycje rozjechały się **w przeciwne strony i o ponad połowę**: spodziewałem
się, że raport zwykle nazywa kontrolę z komunikatu, a zmierzone jest, że komunikat
zwykle nie nazywa **niczego** w oknie kontroli. Zapisuję to jako rozjazd, a nie poprawiam
przewidywania.

## 7. Kontrole negatywne

Wszystkie na **kompletnej kopii drzewa** (z `.git`), mutowana jest kopia. Drzewo robocze
w tym samym czasie: **10/10, kod 0**.

| KN | mutacja | przewidziane | zmierzone |
|---|---|---|---|
| KN-1 | `wspolne` zawsze niepuste | 8/10, czerwony `..._wypada_z_klasy_dotyczy` | **8/10**, czerwony ten i `..._trzy_klasy...` |
| KN-2 | `wspolne` zawsze puste | 7/10, trzy wymienione czerwone | **7/10**, te trzy |
| KN-3 | `root` z powrotem ignorowany | 9/10, czerwony `..._czytaja_root_...` | **9/10**, ten |
| KN-4 | wiersze raportów nieczytane | 7/10, jak KN-2 | **6/10** |
| KN-5 | podłoga wąska o jeden wyżej | 9/10, czerwony `..._trzy_klasy...` | **9/10**, ten |

Dwa rozjazdy, oba zapisane jako rozjazdy. **KN-1**: przewidziałem, że drugim czerwonym
będzie test nazw wszechobecnych — został zielony, a zapaliła się asercja „szeroko daje
więcej niż wąsko", bo przy zgodności zawsze prawdziwej oba warianty dają **362** i sito
przestaje rozróżniać to, co rozróżnia. **KN-4**: przewidziałem 7/10 „jak KN-2", a wyszło
**6/10** — czwartym czerwonym jest `..._wypada_z_klasy_dotyczy`, który przy pustych
raportach nie znajduje commita już nie w klasie `dotyczy`, tylko w `raport_nic_nie_nazywa`
zamiast w `rozne_nazwy`. Kontrola trafia więc w **oba** końce przypadku, a nie w jeden.

KN-3 pokazuje jeszcze jedno, i to po obu stronach: na kopii bez poprawki
`komunikaty(katalog bez repozytorium)` oddaje **1023** komunikaty, w drzewie roboczym
z poprawką ten sam wywołanie pada — czyli mutacja zmieniła odczyt kopii, a odczytu
drzewa roboczego nie ruszyła.

## 8. Znalezisko przy okazji: argument `root` był ignorowany

`komunikaty(root)` brała ścieżkę z modułowego `ROOT` niezależnie od argumentu. Dzisiaj
nikt nie wołał jej z innym korzeniem, więc żadna liczba nie była przez to zła — ale
czytnik wołany na kopii oddawałby komunikaty drzewa **tego** modułu przy diffach kopii,
czyli dokładnie taką cichą pomyłkę, jakiej ten projekt szuka. Poprawione w tym samym
commicie, bo nowy czytnik `klasy_sladu(root)` stoi na tej funkcji i bez poprawki jego
własny argument `root` też byłby napisem bez skutku. Kontrola negatywna: KN-3 wyżej.

## 9. Czego świadomie nie zrobiłem

- **Nie ruszyłem `MIN_ZGLASZA_KONTROLE` ani `MIN_ZGLASZA_KONTROLE_ZE_SLADEM`** — pole
  „Poza zakresem" tej pozycji zabrania, i słusznie: zaciśnięcie kryterium obniża
  populację, a podłogę wolno obniżać tylko z powodem, który dopiero tu powstał.
- **Nie zmieniłem `SLAD_KONTROLI`.** Zaciśnięcie stoi obok, jako osobny czytnik,
  a stare kryterium liczy dalej to, co liczyło. Podmiana zmieniłaby znaczenie dwóch
  podłóg istniejących bez decyzji o nich.
- **Kontrola negatywna stoi na commitach ŻYWYCH**, a nie na commicie syntetycznym
  w kopii, jak zapowiadały przewidywania. Moduł ma już taki kształt dla trzech innych
  przypadków; czwarty mechanizm obok trzech istniejących byłby kosztem bez zysku.
  Odstępstwo od własnej zapowiedzi, zapisane jawnie.

## 10. Co zauważyłem, a czego nie tknąłem

- Klasa „bez raportu" (**113**) to w większości commity wczesne, dopisujące sam plik
  testu. Czy to znaczy, że kontrola nie została wykonana, czy że jej wyjście stoi
  wyłącznie w komunikacie — rozstrzygnąć może dopiero czytanie tych komunikatów
  po kolei, i to jest osobna pozycja, nie ta.
- Moduł chodził **9 s** przy pięciu testach, a przy dziesięciu chodzi **7 s** — bo
  pamięć na wyniki czytników obsługuje też cztery wywołania, które stały tam wcześniej.

## 11. Weryfikacja

```
$ python3 tools/tests/test_all.py test_commit_claims.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  ok   test_commit_zmieniajacy_zapadke_BEZ_wzmianki_trafia_do_pary_odwrotnej
  ok   test_cztery_liczby_ktorych_zadalo_pole_wyjscie
  ok   test_komunikat_zglaszajacy_zapadke_ktorej_diff_NIE_rusza_jest_zgloszony
  ok   test_komunikaty_czytaja_root_KTORY_DOSTALY
  ok   test_kontrola_WYKONANA_ale_niezgloszona_NIE_jest_liczona_jako_zgloszenie
  ok   test_raport_o_TEJ_SAMEJ_kontroli_w_klasie_dotyczy_ZOSTAJE
  ok   test_raport_o_czym_INNYM_wypada_z_klasy_dotyczy
  ok   test_szerokosc_kotwicy_ZMIENIA_liczbe_i_roznica_jest_zmierzona
  ok   test_trzy_klasy_sladu_ktorych_zadalo_pole_wyjscie_6D283
  ok   test_zgodnosc_na_samych_nazwach_wszechobecnych_jest_liczona_OSOBNO

  10/10 przeszło
       7.202 s  test_commit_claims.py  (10 testów)
```

Cały zestaw: **2654/2654 przeszło**, kod 0 (przed tą pozycją 2649 testów w 138 modułach;
nowego modułu nie ma, doszło pięć testów w module istniejącym).

**Uwaga o przebiegu odniesienia.** Pierwszy przebieg zestawu tej sesji szedł w tle,
gdy edytowałem moduł, więc **nie jest przebiegiem PRZED zmianą** i tak go nie liczę.
Stanem wyjściowym jest zielone CI scalenia `54c6f70`, a nie tamten przebieg.
