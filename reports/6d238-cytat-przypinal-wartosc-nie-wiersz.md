# 6.D238 — cytat przypinał WARTOŚĆ, a nie WIERSZ, który ją daje

**Data:** 17.09.2026 · **Gałąź:** `claude/6d238-cytat-przypina-wiersz` · **Baza:** `9101ce8`

## 1. Co przechodziło, a nie powinno

`tools/tests/test_t401_citation.py` wiązał dolne ograniczenie planu sygnalizacji
z **maksimum kolumny C#** w §4 raportu `reports/T-401-line-run.md`. Maksimum jest
odporne na przestawienie: zamiana tej kolumny **między dwoma pakietami** (L5_D ↔ L6_F)
nie rusza maksimum ani o setną, więc asercja przechodziła. Po takiej zamianie cytat
wiąże **inny pakiet**, a kolumna Δ zostaje arytmetycznie fałszywa — 57,64 → 55,05
opisane jako **+1,04**.

Strona C# tego nie ratuje, bo tego pliku nie czyta: oba wystąpienia `T-401-line-run`
w `.cs` są komentarzami.

## 2. Pomiar tabeli §4

Sześć wierszy, wszystkie sześciokolumnowe, zero niespójności arytmetycznych dziś:

```
wierszy pelnych = 6 przy progu 6
   ('L1_A', '57,41', '58,09', '+0,68', 'Schuman → Merode', 'Schuman → Merode')
   ('L1_B', '56,45', '57,56', '+1,11', 'Roodebeek → Vandervelde', …)
   ('L2_E', '57,47', '58,49', '+1,02', 'Ribaucourt → Yser', …)
   ('L5_C', '57,02', '58,34', '+1,32', 'Aumale → Saint-Guidon', …)
   ('L5_D', '57,64', '58,68', '+1,04', 'Beaulieu → Demey', …)
   ('L6_F', '54,10', '55,05', '+0,95', 'Bockstael → Stuyvenbergh', …)
niespojne = []
```

Wiązanie jest **arytmetyczne**, nie równościowe: kolumna Δ ma wychodzić z własnego
wiersza. Przestawienie kolumny psuje arytmetykę w **dwóch** wierszach naraz i właśnie
to jest wykrywane — a nie treść tabeli, której 6.D108 zabrania przypinać.

## 3. KONTROLA DODATNIA OBALIŁA PIERWSZĄ WERSJĘ ŁATKI

**To jest najważniejszy wynik tej pozycji i nie pochodzi z kodu, tylko z KN-5.**

Blok pozycji ostrzegał wprost: „tabela ma kolumnę, którą kolejne przebiegi dopisują —
równość zapalałaby się wtedy na dopisaniu wiersza, czyli na pracy poprawnej (6.D27)".
Pierwsza wersja łatki ominęła przypadek WIERSZA i weszła prosto w przypadek KOLUMNY:
wzorzec kończył się na `\|\s*$`, czyli żądał, żeby kolumn było **dokładnie sześć**.

Dopisanie siódmej kolumny do wszystkich sześciu wierszy — praca poprawna — oślepiało
czytnik do **zera** wierszy i zapalało **trzy** bramki, w tym nową podłogę:

```
FAIL test_skan_widzi_zmierzona_liczbe_wierszy_tabeli_paragrafu_4: wzorzec
  sześciopolowy widzi 0 wierszy tabeli §4 przy progu 6 — spadek znaczy oślepły
  wzorzec, a nie skróconą tabelę
  51/54 przeszło
```

Przewidziane było **zielone**. Po zdjęciu kotwicy końca wiersza ta sama mutacja daje
**54/54**, a KN-1 nadal zapala dwie bramki — czyli tolerancja wzrosła, a wykrywanie
nie osłabło. Potwierdza to KN-6, złożenie obu zmian naraz.

## 4. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Populacja: `test_t401_citation.py`, `test_tree_walks.py`, `test_report_claims.py`.
**Baza 54/54.** Każda mutacja niesie asercję, że się ZASTOSOWAŁA; po każdej
przywracanie z kopii i `md5sum -c` (za każdym razem `OK`).

| mutacja | przewidziane | zmierzone |
|---|---|---|
| KN-1 zamiana kolumny C# L5_D ↔ L6_F — **konfiguracja z pola „Weryfikacja"** | czerwone, **dokładnie 1** FAIL | **52/54 — DWA**; przewidywanie co do liczby nietrafione |
| KN-2 jedna wartość podmieniona (nie zamiana) | czerwone, **inna** bramka niż KN-1 | **50/54**, cztery — w tym dolne ograniczenie i próg C#, których KN-1 **nie** ruszyła |
| KN-3 czytnik `wiersze_pelne` oślepiony | czerwone na podłodze | **51/54**, podłoga wśród nich |
| KN-4 usunięty wiersz z tabeli | czerwone, ale **nie** na nowej podłodze | **48/54 — PRZEWIDYWANIE OBALONE:** sześć bramek i podłoga JEST wśród nich |
| KN-5 **kontrola DODATNIA** — dopisana siódma kolumna | **zielone** | **51/54 — OBALONE.** Po poprawce wzorca: **54/54** |
| KN-6 zamiana **plus** siódma kolumna | czerwone | **6/8** — wykrywanie przeżyło poszerzenie |

**KN-1 i KN-2 razem są treścią**, nie parą przebiegów: KN-2 rusza maksimum kolumny
i zapala stare wiązanie, KN-1 maksimum **nie rusza** i stare wiązanie zostaje zielone.
Różnica między nimi to dokładnie ta dziura, dla której pozycja powstała.

**KN-4 obaliła zdanie, które sam napisałem przy stałej.** Komentarz mówił, że
usunięcie wiersza zapala `set(found) == PACKAGES`, a **nie** tę podłogę. Zapala oba.
Komentarz jest przepisany: prawdziwe zostaje, że podłoga nie jest jedynym strażnikiem
liczby wierszy; nieprawdziwe było, że nic nie dokłada — dokłada komunikat nazywający
**powód** spadku, którego tamta równość nie podaje.

## 5. Zapadki

- `MIN_WIERSZY_Z_ARYTMETYKA` = **6** przy populacji **6**, zapas zero. Podłoga, nie
  równość, i to jest wybór z 6.D108: raport jest zapisem swojego dnia, więc równość
  paliłaby się na dopisaniu wiersza. Zapas jest zbędny, bo w drugą stronę tabela
  legalnie nie maleje — a gdy maleje, słyszy to też `set(found) == PACKAGES`.
- `ZAPADEK_RAZEM` 59 → **60**, klasy 17/3/38/1 → **17/3/39/1**.
- `MIN_REPORTS` o jeden.

## 6. Czego NIE zrobiono

- **Nie tknięto `reports/T-401-line-run.md`** — 6.D108, a pole „Poza zakresem" mówi
  to wprost. Wszystkie mutacje były na kopii i przywrócone.
- **Nie związano pozostałych kolumn** tabeli (dystans, czas, klatki, „5 z 5") —
  pomiar ich nie objął, a pole „Poza zakresem" zabrania wiązania bez pomiaru.
- **Nie ruszono strony C#** — `LineRunTests.cs` i `SignallingPlanTests.cs` wspominają
  T-401 wyłącznie w komentarzach i pozycja tego nie zmienia.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

- **Wzorzec `ROW` (trzy kolumny) kotwicy końca nigdy nie miał**, a `WIERSZ_PELNY`
  (sześć kolumn) miał ją od pierwszej wersji. Dwa wzorce nad tą samą tabelą, o różnej
  tolerancji na kształt — ta sama rodzina, co 6.D230 po stronie bloków kodu. Dziś oba
  dają tę samą szóstkę, więc rozjazdu nie widać; jutro może być inaczej.
- **`test_kolumna_roznicy_zgadza_sie_z_arytmetyka_w_KAZDYM_wierszu` ma komunikat
  mówiący o „zamianie między pakietami"** także wtedy, gdy przyczyną była podmiana
  jednej wartości (KN-2). Werdykt jest poprawny, diagnoza w komunikacie zawężona.
