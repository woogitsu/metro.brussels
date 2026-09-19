# 6.D293 · Dziesięć ze stu trzynastu — a wzorzec z modułu dałby ZERO

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `e5fcb02`

Klasa `bez_raportu` z `klasy_sladu` liczy **113** commitów: takich, które zgłaszają
wykonaną kontrolę negatywną i mają ślad w plikach, ale śladem jest sam plik testu,
a nie dopisany raport. 6.D283 tę klasę policzyło i nie zajrzało do środka. Ta pozycja
dzieli ją na przyczyny.

---

## 1. Trzy liczby

```
klasa `bez_raportu`: 113 commitow

(a) wynik liczbowy w komunikacie      : 101 / 113
(b) nazywa plik testu z tego commita  :  29 / 113
    przeciecie (a) i (b)              :  27
(c) ANI JEDNO, ANI DRUGIE             :  10
    kontrola arytmetyki: |a|+|b|-|obie|+|ani| = 113 (ma byc 113)
```

**Przecięcie policzyłem osobno i zapisałem to w przewidywaniach PRZED pomiarem.**
Klasy (a) i (b) nie są rozłączne — commit może naraz podać `21/21` i nazwać
`test_message_claims.py` — więc podanie (c) jako `113 − 101 − 29` dałoby **minus
siedemnaście** i byłoby arytmetyką udającą pomiar. Tożsamość włącz-wyłącz domyka się
co do jedności i to jest kontrola samego rachunku, nie ozdoba.

## 2. Wzorzec z modułu odpowiedziałby na inne pytanie — i dałby ZERO

Pole „Wyjście" żąda **wyniku liczbowego** (`N/M` albo `kod N`). Moduł ma własny
`WYNIK_KONTROLI`, ale jest on znacznie szerszy: łapie także `zmierzon`, `wykonan`,
`czerwie`, `zielen`, `FAIL`, `->` i `→`.

```
   modulowy WYNIK_KONTROLI (szeroki): 113 / 113
   waski, wynik LICZBOWY            : 101 / 113
   roznica                          :  12

   Gdyby uzyc modulowego, (c) wynioslaby: 0
```

**Szeroki wzorzec trafia w CAŁĄ klasę.** Użycie go — kuszące, bo stoi w module
i jest „pożyczeniem, nie pisaniem drugi raz" — dałoby (c) = 0 i wniosek „każdy
z tych commitów ma ślad poza komunikatem". Wniosek byłby nieprawdziwy, a wyglądałby
na wynik. Różnica między 113 a 101 to dokładnie miejsce, w którym ta pozycja ma coś
do powiedzenia.

Jest to granica **pożyczania czytnika**, o którą projekt prosi od 6.D281: pożycza się
wtedy, gdy czytnik odpowiada na TO pytanie. Tutaj nie odpowiadał.

## 3. Klasa (c) — dziesięć adresów

| sha | pierwszy wiersz komunikatu | data |
|---|---|---|
| `a2293e65aba0` | Scalenie #365: kolejka — dwie pozycje z pomiarów przy 6.A25 i 6.B37 | 07.09 |
| `97ab66f5b436` | Kolejka: dwie pozycje z pomiarów przy 6.D28, zapas 12 → 14 | 07.09 |
| `6fa604c49fb6` | Scalenie #257: kabina pod sygnalizacją | 05.09 |
| `86ae750dfe7b` | Scalenie #250: dwa moduły `tools/` dostają testy jednostkowe | 05.09 |
| `dfbde8fa309e` | Scalenie #248: tryb ręczny ma jeden limit po obu stronach bramki | 05.09 |
| `ead62d2aa1ae` | Scalenie #249: sterowanie przez InputMap | 05.09 |
| `c705199f1bb7` | Sterowanie przez InputMap, a wiersz pomocy przestaje być martwą stałą | 05.09 |
| `bc82d58c556e` | doctor wskazuje kolejkę faz 5 i 6 | 05.09 |
| `443c23bae1d1` | Bramka CI dla peronów i słupków | 03.09 |
| `ac7d0d0c401e` | Zła klatka jest statusem tej kamery, nie końcem całego przebiegu | 03.09 |

**Klasa (c) jest ZJAWISKIEM WCZESNYM i to było przewidziane przed pomiarem.**
Cała klasa `bez_raportu` rozciąga się od **02.09** do **14.09.2026**; klasa (c)
mieści się w **03.09–07.09**. Ani jeden commit z drugiego tygodnia nie zgłasza
kontroli bez żadnego potwierdzenia liczbowego ani nazwy pliku.

**Pięć z dziesięciu ma dwoje rodziców**, czyli są to scalenia, a ich komunikat
powstaje przy scalaniu, a nie przy pracy. Ile z tej dziesiątki to OSOBNA praca —
i dlaczego odpowiedź brzmi sześć, a nie dziesięć — liczy §8.

## 4. Kontrole, obie zdane

Pole „Weryfikacja" żąda dwóch, w przeciwne strony:

```
KONTROLA NEGATYWNA — commit z klasy (c) ma WYPASC z klasy pierwszej:
   ac7d0d0c401e  ma_wynik_liczbowy = False  <- ma byc False
   443c23bae1d1  ma_wynik_liczbowy = False  <- ma byc False

KONTROLA PRZYRZADU — commit z `N/M` ma ZOSTAC:
   7a895be7675d  ma_wynik_liczbowy = True  (trafienie: '633/633')  <- ma byc True
   2db590ad6dee  ma_wynik_liczbowy = True  (trafienie: '2466/2466')  <- ma byc True
```

Obie wykonane na **prawdziwych commitach z drzewa**, nie na atrapie tekstu —
populacja tej pozycji jest historią repozytorium i atrapa nie sprawdziłaby tego,
co ma sprawdzić.

## 5. Straż, która nie fika ani razu — i mówię to wprost

Przewidziałem przed pomiarem, że pierwsza wersja czytnika (a) się pomyli, bo `N/M`
pasuje też do dat (`19/09`), zakresów wierszy i ułamków w prozie — ta sama rodzina,
co wieloznaczność `-` przy 6.D291. Zbudowałem więc od razu trzy straże: odrzucenie
dat przez granicę `(?<![\d/.])`, odrzucenie par, w których licznik przekracza
mianownik, i odrzucenie liczb powyżej trzech tysięcy.

```
   naiwny `\d+/\d+`  : 101 / 113
   ze strazami       : 101 / 113
   roznica           :   0
```

**Straże nie zmieniają ani jednej klasyfikacji.** Przewidywanie było więc
**nietrafione**, i zapisuję to tak, zamiast przedstawiać ostrożność jako trafność.
Nie usuwam ich — kosztują nic, a populacja może się zmienić — ale ich dzisiejsza
wartość jest zmierzona i wynosi zero.

Różnica wobec 6.D290 i 6.D291 jest pouczająca: tam sito myliło się cztery razy i
każda poprawka zmieniała liczbę. Tutaj przewidziałem tę samą pułapkę, zabezpieczyłem
się przed nią i pułapki nie było. **Przewidywanie o pomyłce też bywa nietrafione.**

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | (a) wynik liczbowy: 70–95 | **PUDŁO**, jest 101 |
| 2 | (b) nazwa pliku testu: 40–70 | **PUDŁO**, jest 29 |
| 3 | (c) ani jedno, ani drugie: 5–20 | trafione (10) |
| 4 | przecięcie: 30–60 | **PUDŁO**, jest 27 |
| 5 | kontrola negatywna wypadnie | trafione |
| 6 | kontrola przyrządu zostanie | trafione |
| 7 | pierwsza wersja czytnika (a) się pomyli | **NIETRAFIONE** — straże dają zero różnicy |
| 8 | (c) będzie zawierać commity STARE | trafione, z datami: 03–07.09 przy klasie 02–14.09 |

**Trzy pudła liczbowe, ale PO RAZ PIERWSZY DZIŚ W OBIE STRONY:** (a) wyszło wyżej
od przedziału, (b) i przecięcie niżej. Przy 6.D287–6.D290 myliłem się wyłącznie
w dół, przy 6.D291 wyłącznie w górę; tutaj w jednej pozycji obie strony naraz.
Znaczy to, że nie mam jednej stałej skłonności, tylko słabo przewiduję **rozkład
wewnątrz populacji**, której rozmiar znam.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono `SLAD_KONTROLI` ani `MIN_ZGLASZA_KONTROLE_ZE_SLADEM`**
  (pole „Poza zakresem").
- **Nie przepisano żadnego dawnego komunikatu** i nie zaproponowano przepisania.
  Dziesięć commitów klasy (c) jest zamkniętą historią; `docs/04-conventions.md`
  mówi, że pomiaru z datą się nie przelicza, a komunikat jest jeszcze mniej
  przepisywalny niż pomiar.
- **Nie postawiono bramki.** Pole „Wyjście" żąda trzech liczb z adresami, a nie
  sita w drzewie.
- **Nie zastąpiono wąskiego wzorca modułowym**, choć byłoby to „pożyczeniem" —
  §2 mówi, dlaczego byłoby to pożyczeniem odpowiedzi na inne pytanie.
- **Nie tknięto `src/`.**

## 8. DZIESIĘĆ COMMITÓW TO SZEŚĆ KAWAŁKÓW PRACY — i to jest wynik, nie dygresja

Pierwsza wersja tego paragrafu twierdziła, że `klasy_sladu` „odsiewa scalenia
przełącznikiem `DIFF_SCALENIA`". **To było nieprawdą i sprawdziłem to, zanim zdanie
tu zostało.** Przełącznik robi dokładnie odwrotność: `git log -p` domyślnie POMIJA
diff scalenia, a `--diff-merges=first-parent` każe go pokazać — scalenia są
w populacji **umyślnie**, bo w tym repozytorium niosą w komunikacie te same
zgłoszenia co commit gałęzi (zmierzone przy 6.D279).

Policzone: **pięć** z dziesięciu ma dwoje rodziców, pięć jednego. Drudzy rodzice
rozstrzygają, ile z tej dziesiątki to osobna praca:

| commit | co to jest | praca ma wynik liczbowy? |
|---|---|---|
| `ead62d2aa1ae` + `c705199f1bb7` | scalenie **i jego gałąź**, oba w klasie (c) | nie — jedna praca policzona DWA RAZY |
| `6fa604c49fb6` | scalenie; gałąź `914fb9fd3488` też bez wyniku | nie |
| `a2293e65aba0` | scalenie; gałąź `1f15ec5b8ef2` **ma** `N/M` | **tak, na gałęzi** |
| `86ae750dfe7b` | scalenie; gałąź `f5126a368f31` **ma** `N/M` | **tak, na gałęzi** |
| `dfbde8fa309e` | scalenie; gałąź `25227a711533` **ma** `N/M` | **tak, na gałęzi** |
| `97ab66f5b436`, `bc82d58c556e`, `443c23bae1d1`, `ac7d0d0c401e` | zwykłe commity | nie |

**Kawałków pracy bez ŻADNEGO śladu liczbowego jest sześć, nie dziesięć:** jedna para
policzona dwukrotnie, jedno scalenie z gałęzią równie milczącą i cztery zwykłe
commity. Trzy pozostałe scalenia mają wynik **na gałęzi** — brak śladu jest tam
własnością TYTUŁU SCALENIA, a nie pracy.

Liczba z pola „Wyjście" zostaje **dziesięć**, bo pole pyta o commity i tak je
policzyłem. Sześć stoi obok niej, bo bez tego dziesiątka czyta się jako dziesięć
zaniedbań, a tyle ich nie ma.

**Czego ta pozycja nie rozstrzyga:** czy komunikat scalenia w ogóle powinien podlegać
kryterium pisanemu dla commitu pracy. Jest to pytanie o konwencję, nie o drzewo,
a pole „Poza zakresem" zabrania przepisywania dawnych komunikatów.
