# 6.D106 — jedna nazwa zmieniona z pomiaru, druga zostawiona z pomiaru

**Zmierzone 10.09.2026 na:** `9937c90`, kontener tej sesji.
**Przyrząd:** `tools/tests/mutation_sweep.py` (`default_journal`, `sciezka_pokrycia`,
`zapisz_pokrycie`, `read_journal`), `tools/tests/test_mutation_sweep.py`, dwa
skrypty pomiarowe w katalogu tymczasowym (równoległe zapisy z barierą startu).

---

## 1. Dwie ścieżki, dwa różne rozstrzygnięcia

Wpis wymieniał dwie nazwy budowane z treści i żądał, żeby obie dostały element
unikatowy dla procesu. Po pomiarze **jedna go dostała, druga nie**, i oba
rozstrzygnięcia mają liczby.

| ścieżka | rozstrzygnięcie | powód |
|---|---|---|
| dziennik (`default_journal`) | **element procesu dodany** | zmierzona szkoda: raporty liczą mutacje podwójnie |
| mapa pokrycia, plik **docelowy** | **zostaje wspólny** | to pamięć podręczna warta pełnego przebiegu zestawu |
| mapa pokrycia, plik **pośredni** | **element procesu dodany** | ubezpieczenie; szkody NIE odtworzyłem |

## 2. Dziennik: szkoda zmierzona

`sweep` czyta wynik z **całego** dziennika i `read_journal` **nie odsiewa
powtórzeń**. Zmierzone wprost — dwa dopisy tego samego wpisu:

```
wpisow w dzienniku po dwoch przebiegach: 2
roznych mutacji (po id): 1
czy read_journal odsiewa powtorzenia: False
```

Dwa przeglądy uruchomione równolegle z tym samym commitem, klasami, `--only`
i odciskiem treści mierzą to samo — i do dziś **dzieliły plik**. Każdy dopisywał
swoje wpisy, każdy czytał całość, więc oba raporty liczyły każdą mutację dwa razy.
Runnery jednej puli stoją na jednej maszynie i dzielą `/tmp`.

**Znacznik jest liczony RAZ przy imporcie**, więc w obrębie jednego przebiegu nazwa
jest stała (dwa wywołania dają ten sam plik — `sweep` zapisuje tam, gdzie czyta),
a między procesami różna. Sam PID nie wystarcza: w kontenerach numery procesów
zaczynają się od małych liczb i powtarzają między maszynami tej samej puli, więc
znacznik miesza PID z czasem w nanosekundach.

**Co to kosztuje, i mówię to wprost:** wznowienia po DOMYŚLNEJ nazwie już nie ma.
Drugi przebieg nie znajdzie dziennika pierwszego. Wznowienie idzie odtąd przez jawne
`--journal <ścieżka>` — dokładnie tak, jak przewiduje pole „Wyjście" tej pozycji.
Czteroczłonowy znacznik treści zostaje w nazwie, bo nadal mówi człowiekowi
patrzącemu w `/tmp`, czego ten dziennik dotyczy.

## 3. Mapa pokrycia: plik docelowy zostaje wspólny, i to też jest pomiar

Wpis żądał dwóch różnych plików pokrycia dla dwóch równoległych przebiegów. **Nie
zrobiłem tego** i powód jest policzalny: mapa powstaje z **jednego pełnego przebiegu
zestawu z licznikiem wierszy** (`coverage_map(work, timeout * 4)`), a plik jest
pamięcią podręczną dla commita — uczynienie go unikatowym kasowałoby tę pamięć przy
każdym przebiegu i dokładało ten przebieg do każdego sweepa.

Dzielenie jest bezpieczne, bo sweep **odmawia na brudnym drzewie** (`dirty_sources`,
kod wyjścia 2, komunikat o `--dirty`). Jeden commit znaczy więc jedno drzewo i jedną
mapę: dwa procesy liczące ją równolegle liczą **tę samą** mapę.

## 4. Plik pośredni: zmieniony, ale szkody nie odtworzyłem

Prawdziwym kandydatem na kolizję był plik **pośredni**: `path + ".czesciowy"`, ta
sama nazwa dla każdego przebiegu tego commita. Dwa procesy otwierały go z `"w"`,
czyli każde otwarcie go obcinało.

**Zepsucia pliku docelowego nie udało się odtworzyć.** Pięć prób z barierą startu
i mapą ~50 MB, dwa procesy piszące naraz:

```
  proba 1      CZYTELNY, modulow=6000;  pliki posrednie: 0
  proba 2      CZYTELNY, modulow=6000;  pliki posrednie: 0
  proba 3      CZYTELNY, modulow=6000;  pliki posrednie: 0
  proba 4      CZYTELNY, modulow=6000;  pliki posrednie: 0
  proba 5      CZYTELNY, modulow=6000;  pliki posrednie: 0
```

Za każdym razem czytelny, bo `os.replace` przenosi to, co zapisał ostatni
**kompletny** pisarz. Wcześniejszy przebieg bez bariery, na mniejszej mapie, dał to
samo trzy razy na trzy.

Nazwa pośredniego jest mimo to unikatowa dla procesu: koszt zerowy, a rozumowanie
zostaje — dwa strumienie o niezależnych offsetach po obcięciu mogą się przepleść.
**To jest ubezpieczenie od zjawiska nieodtworzonego, nie naprawa zmierzonej
usterki**, i tak jest opisane w kodzie oraz w docstringu testu. Pierwsza wersja
obu tych komentarzy twierdziła, że atomowość „była fikcją", a plik docelowy „dawał
się przeczytać do połowy" — **i to nieprawda**; zdania zostały przepisane po
pomiarze, zanim cokolwiek poszło do commita.

## 5. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` dwóch plików na bok i `md5sum -c` po przywróceniu, z `__pycache__`
czyszczonym przed każdym przebiegiem (procedura z 6.D102).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | dziennik wraca do nazwy bez elementu procesu | **116/117** |
| KN-2 | znacznik liczony przy KAŻDYM wywołaniu, nie raz przy imporcie | **114/117**, trzy testy |
| KN-3 | plik pośredni wraca do stałej nazwy | **116/117** |
| KN-4 | plik DOCELOWY mapy dostaje element procesu | **116/117** |
| KN-5 | znacznik to sam PID | **116/117** |

Po każdej: `md5sum -c` → `OK` na obu plikach.

**KN-2 jest tu najważniejsza i nie napisałem jej testów.** Trzy zgłoszenia, z czego
dwa pochodzą z testów, które w tym pliku stały wcześniej:
`test_ta_sama_tresc_trafia_w_ten_sam_dziennik` i
`test_domyslny_dziennik_jest_jeden_na_przebieg_a_nie_jeden_na_maszyne`. Znaczy to,
że stabilność nazwy **w obrębie procesu** była już przybita przed tą pozycją — i że
gdybym policzył znacznik przy każdym wywołaniu, `sweep` zapisywałby gdzie indziej,
niż czyta. Kontrola potwierdziła to, zanim zdążyłem się pomylić.

**KN-4 mierzy koszt, nie usterkę:** unikatowy plik docelowy przechodzi wszystkie
testy poza tym jednym, który mówi wprost, że pamięć podręczna commita przestała
działać. Bez tej asercji „poprawka" zgodna z literą wpisu weszłaby niezauważona.

## 5.1 Bramka, która złapała mnie przy okazji

Pierwsza wersja znacznika obcinała skrót literałem `[:8]`. Zapaliło to
`test_hexdigest_truncation` — bramkę sprzed tej pozycji, pilnującą, że każde
obcięcie skrótu idzie przez **nazwaną stałą**, bo dwie długości tej samej wielkości
rozjeżdżają się po cichu. Doszła więc `PROCES_ZNACZNIK_ZNAKOW`, obok istniejącej
`ZNACZNIK_ZNAKOW`. Zgłoszenie przyszło z pełnego przebiegu zestawu, nie z lektury.

## 6. Czego świadomie nie zrobiłem

- **Nie zmieniałem zbioru mutacji ani sposobu liczenia wyników** (pole „Poza
  zakresem"), ani nie ruszałem mutowania `data/` w miejscu — to jest 6.D90.
- **Nie dodałem odsiewania powtórzeń do `read_journal`.** To byłaby zmiana sposobu
  liczenia wyników, czyli dokładnie to, czego pole „Poza zakresem" zabrania —
  a przy nazwie unikatowej dla procesu powtórzenia i tak nie powstają.
- **Nie dodałem blokady pliku.** Zamek zachowałby wznowienie po domyślnej nazwie
  i usunął mieszanie, więc jest wart rozważenia — ale to inny mechanizm niż ten,
  o który prosi pole „Wyjście", i ma własne tryby awarii (zamek po ubitym procesie).

## 7. Co zauważyłem przy okazji, ale nie tknąłem

- **`test_domyslny_dziennik_jest_jeden_na_przebieg_a_nie_jeden_na_maszyne` ma
  asercję z pustym komunikatem** — w KN-2 zgłosiła się jako `FAIL … :` bez ani
  jednego słowa. Test jest sprzed tej pozycji i poprawianie go leży poza jej
  zakresem (`CLAUDE.md` §4.10), ale komunikat pusty jest tym samym, co brak
  komunikatu.
- **Wznowienie po domyślnej nazwie było jedyną drogą wznowienia bez pisania ścieżki
  z ręki.** Ta pozycja ją zdejmuje zgodnie z własnym polem „Wyjście"; jeśli okaże
  się potrzebna, wraca przez zamek z punktu 6, a nie przez cofnięcie nazwy.
