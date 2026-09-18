# 6.D270 — dziura miała rozmiar 49 i 17, a zamknęło ją podniesienie podłóg

**Data:** 18.09.2026 · **Gałąź:** `claude/6d270-podlogi-galezi` · **Baza:** `ba71969`

## 1. Odpowiedź na pole „Wyjście"

| gałąź | dziś | podłoga przed | zapas przed | podłoga po |
|---|---|---|---|---|
| `const` | 307 | 258 | **49** | 307 |
| `static readonly` | 89 | 72 | **17** | 89 |
| bez modyfikatora dostępu | 45 | 36 | **9** | 45 |
| SUMA | 396 | 330 | 66 | 330 (bez zmian) |

Przeniesień między gałęziami, które przed tą pozycją nie zapalały **niczego**:
**49** z `const` na `static readonly` i **17** w drugą stronę. Suma się przy
przeniesieniu nie rusza, więc `MINIMUM_DEKLARACJI` nie zapalał nigdy — suma broni
przed wzorcem MARTWYM, trzy podłogi broniły przed OKALECZONYM, a przed
PRZESUNIĘTYM nie broniło nic.

## 2. Pole „Dlaczego bez decyzji" tej pozycji BYŁO BŁĘDNE

Napisałem tam, że zamiana podłóg na równości „jest ruchem w stronę ciaśniejszą,
a takiego zapadka nie zabrania". Jest to prawda o regule zapadek i **przemilczenie
pomiaru**, który 6.D232 już wykonało. Tamta pozycja wybrała klasę WOLNĄ świadomie:

> Wszystkie trzy są zapadkami DOLNYMI klasy WOLNEJ z tego samego powodu co
> `MINIMUM_DZIUR`: populacja rośnie razem z kodem, więc przybicie czerwieniałoby
> przy każdej nowej stałej.

Powód jest dziś nadal prawdziwy, więc **równości nie wchodzą** — to byłoby
odwrócenie rozstrzygnięcia 6.D232, czyli decyzja właściciela, a nie pomiar.
Zapisane jako **6.D273**, razem z 6.D266, do rozstrzygnięcia.

**Dziurę da się jednak zamknąć bez odwracania tamtej decyzji:** podłoga ustawiona
na dzisiejszej wartości łapie przesunięcie, bo przesunięcie **zmniejsza** jedną
gałąź, a na wzroście populacji milczy, bo wzrost tylko ją oddala. Równość zapalałaby
się na jednym i drugim; to jest cała różnica i cały powód. Podniesienie zapadki
DOLNEJ jest kierunkiem dozwolonym.

## 3. Cena jest policzona, nie oszacowana

Z tej samej historii 572 rewizji, którą 6.D232 już zbadało: `const` spadł raz
o jeden (164 z 165), `static readonly` raz o jeden (38 z 39), a deklaracji bez
modyfikatora dostępu nie ubyło ani razu. Ciasna podłoga zapaliłaby się więc
**dwa** razy na 572 rewizje, oba razy na zmianie uprawnionej i oba razy za cenę
jednowierszowej korekty. Zapadka dolna, której wolno rosnąć, jest tu tańsza niż
dziura zostawiająca zapas 49.

## 4. Kontrola negatywna — ta sama mutacja, dwa razy

Przewidywania spisane **przed** przebiegami, na kopii drzewa, z czyszczonym
`__pycache__`, z asercją że mutacja wylądowała. Mutacja: jedna deklaracja
`public const double CabEyeLateralM` przepisana na `public static readonly`.

```
rozkład po mutacji: {'const': 306, 'static readonly': 90, 'bez modyfikatora': 45}
suma: 396 — BEZ ZMIAN

przy STARYCH podłogach 258 / 72 / 36   ->  15/15 przeszło
przy CIASNYCH podłogach 307 / 89 / 45  ->  FAIL test_kazda_galaz_wzorca_ma_wlasna_podloge:
    galaz `const` daje 306 przy progu 307 (rozklad: {'const': 306,
    'static readonly': 90, 'bez modyfikatora': 45})
    14/15
```

**Identyczna mutacja, zielono przed zmianą i czerwono po** — to jest dziura i jej
zamknięcie w jednej parze przebiegów, bez ani jednego zdania oceny.

**Pierwsze podejście do tej kontroli było nieważne i zostaje zapisane.** Skopiowałem
`tools/` i `src/`, a `DRZEWA` tego modułu to `("src", "tests")` — kopia dała
`const` 117 zamiast 307 i trzy czerwienie, które czytały się jak zapalenie bramki
na mutacji, a były błędem środowiska. Dopiero dołożenie `tests/` dało kopię
odtwarzającą drzewo (307 / 89 / 45) i kontrolę wartą czegokolwiek. Jest to ten sam
kształt, który złapałem przy 6.D267 na brakującym `.gitignore` — czerwień z powodu,
o który nie pytano, wygląda dokładnie jak czerwień oczekiwana.

## 5. Kontrola przyrządu — przyrost ma NIE zapalać

Żądało tego pole „Weryfikacja": nowa bramka ma łapać przesunięcie, a nie przyrost,
który i tak był łapany przez sumę. Mutacja: dopisana nowa deklaracja `const`.

```
rozkład: {'const': 308, 'static readonly': 89, 'bez modyfikatora': 45}, suma 397
trzy ciasne podłogi: ZIELONE (308 >= 307, 89 >= 89, 45 >= 45)
```

Zapaliła się jedna, **inna** bramka — `test_every_unread_csharp_constant_is_justified`,
bo stała syntetyczna nie jest nigdzie czytana. Jest to poprawne zachowanie bramki
martwych stałych, a nie zapalenie podłóg, i odnotowane jako różnica, żeby nie
czytało się jako fałszywy alarm nowej reguły.

## 6. Census z 6.D268 zapalił się na tym raporcie i to jest jego robota

Nowy akapit prozy niesie dwie pogrubione liczby (zapas 49 i 17), obie pokryte
zbiegiem cyfr, więc populacja pokrytych wzrosła z 49 na 51. Bramka
`test_rozklad_pokrytych_zbiegiem_PO_PLIKACH` zapaliła się i wskazała
`test_dead_constants_csharp.py` 7 → 9. Census zaktualizowany (51, grupa A 21 → 23);
**zdjęcie pogrubienia zamiast aktualizacji byłoby obejściem bramki, która mówi
prawdę** — obie liczby są zmierzone i obie są twierdzeniem o dzisiejszym drzewie.

## 7. Czego świadomie nie zrobiono

Siedmiu nieprawdziwych liczb w tym samym module (389 / 304 / 85 / 43 / 346)
**nie poprawiono** — to 6.D271, a lista `ROZJAZDY_POKRYTE_ZBIEGIEM` pozostaje
nietknięta i zielona. `MINIMUM_DEKLARACJI` nietknięte: przeniesienie go nie rusza,
a ta pozycja dotyczy gałęzi. Zdanie „Zapas 59 (15,2 %)" w wierszu 72 dotyczy
podłogi SUMY, której nie zmieniam, więc jego nieaktualność (59 przy 66) zostaje
tam, gdzie była — 6.D268 wyjaśniło, dlaczego nie weszło na listę długu.
Wariant z równościami: 6.D273, dla właściciela.
