# 6.B46 — `collect()` bez zawężenia: oszczędność wyszła mniejsza od szumu pomiaru

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`

Pozycja pytała, czy `collect()` ma dostać zawężenie albo pamięć per plik, i **narzucała
kolejność: najpierw pomiar, potem kierunek**. Pomiar odpowiedział „ani jedno, ani drugie",
i to z dwóch niezależnych powodów. Ten raport podaje oba liczbą.

## 1. Przesłanka pozycji była policzona PRZED 6.B38

Wiersz mówił o teście, który „potrzebuje świeżego przeliczenia dla jednego modułu"
i „płaci 0,224 s za komplet 63". Liczba `dziesięć wywołań` pochodzi z pomiaru 6.B38 na
`665bd98` — czyli z drzewa **bez pamięci**, którą 6.B38 właśnie dołożyło.

Przejście po module z owiniętym `collect()`, licznikiem kluczy pamięci i stosem
wołającego, dziś:

```
odkrytych testow: 111  awarii importu: 0
przeszlo 111, padlo 0, CALOSC 16.923 s

wywolan collect() w TYM procesie: 20
  swiezych przeliczen: 4 (razem 0.889 s)
  trafien w pamiec:    16 (razem 0.029 s)
```

Wywołań jest **dwadzieścia**, nie dziesięć — moduł od tamtego pomiaru urósł. Ale
przeliczeń jest **cztery**, bo szesnaście wchodzi w pamięć po 0,002 s. Zdanie „dziesięć
razy po 0,224 s" opisuje więc świat, który sama ta pamięć zniosła.

## 2. Które z czterech przeliczeń pamięć per plik w ogóle skróciłaby

```
  wiersz 2387   2 wywolan, 2 swiezych, 0.453 s, celow w wyniku [63]
  wiersz 478    1 wywolan, 1 swiezych, 0.214 s, celow w wyniku [63]
  wiersz 247    1 wywolan, 1 swiezych, 0.223 s, celow w wyniku [61]
```

- **wiersz 478** — pierwsze wywołanie w przebiegu. Zimne, żaden klucz go nie skróci.
- **wiersz 247** — `collect(LEGACY_KINDS)`. Inne `kinds`, więc **każdy** z 63 celów trzeba
  przemutować pod węższym zestawem klas. Pamięć per plik nie pomaga, bo brakuje nie
  treści, a wyniku dla innych klas.
- **wiersz 2387** — `_z_dopiskiem`, dwa wywołania po dopisaniu do **jednego** pliku.
  **To jedyne dwa, które pamięć per plik skróciłaby**, i to jest cała stawka tej pozycji:
  **0,453 s**.

Czyli z 0,889 s świeżego czasu pamięć per plik dosięga **51 %**, a z całego modułu — 2,8 %.

## 3. Stawka wobec szumu — sześć przebiegów bazowych

```
p1  RAZEM 16.809 s        p4  RAZEM 15.974 s
p2  RAZEM 15.679 s        p5  RAZEM 15.747 s
p3  RAZEM 15.819 s        p6  RAZEM 16.644 s
```

Rozrzut między najkrótszym i najdłuższym: **1,130 s**. Stawka 0,453 s to **0,40 szumu**.

Trzy przebiegi **po** zmianie (która jest wyłącznie zmianą docstringów, więc czasu
zmienić nie może) wypadły wyżej od wszystkich sześciu bazowych:

```
RAZEM 17.184 s, 111 testów
RAZEM 17.476 s, 111 testów
RAZEM 16.705 s, 111 testów
```

Przyczyna jest znana i nie jest w kodzie: przebiegi bazowe szły na maszynie
niezajętej, a te trzy — równolegle z dwoma innymi procesami. **Nie zamilczam tego,
bo to jest dokładnie ta sama obserwacja co wyżej, tylko mocniejsza**: obciążenie
maszyny przesunęło moduł o **1,797 s** (15,679 → 17,476), czyli o czterokrotność
stawki, którą ta pozycja rozważała. Gdyby zawężenie zostało wprowadzone, przebieg
„po" byłby wolniejszy od „przed" i wyglądałby jak regres — pole „Weryfikacja" nie
umie tych dwóch rzeczy rozdzielić przy tej stawce, i to jest osobny powód, żeby
zmiany nie wprowadzać.

Zmiana, której skutek jest mniejszy od różnicy między dwoma przebiegami tego samego
kodu, nie da się odróżnić od jej braku pomiarem, którym ta pozycja miała ją sprawdzić —
a jej pole „Weryfikacja" wymagało czasu przed i po **z co najmniej trzech przebiegów**.
Kryterium samo tę zmianę odrzuca.

## 4. Że per plik byłoby wykonalne — też policzone, nie założone

Gdyby jednak liczyć: koszt jednego celu wobec kompletu.

```
collect() na zimno:        0.2422 s  (2346 mutacji)
mutations_for(lod_paths):  0.00014 s  (2 mutacji)
suma mutations_for po 63 celach: 0.2293 s
odciski 63 celow:          0.00128 s
odcisk jednego celu:       0.00001 s
```

Klucz per `(plik, odcisk, kinds)` przy zmianie jednego pliku daje 62 trafienia i jedno
przeliczenie: 0,00128 s odcisków plus 0,00014 s mutacji, czyli **0,0014 s** wobec
0,2422 s. Rachunek zgadza się ze zmierzonym 0,453 s na dwóch wywołaniach.

Rzecz jest więc **wykonalna i policzona** — odrzucona wyłącznie na stawce, nie na
trudności. Gdyby moduł kiedyś urósł o testy zmieniające pliki celów tak, że stawka
przekroczy szum, ten sam rachunek zostaje w mocy.

Koszt per cel jest przy tym mocno nierówny i pamięć per plik korzystałaby z tego
nierówno:

```
najdrozsze piec celow:
   0.0199 s  tools/track/build_alignment.py                  128 mutacji
   0.0116 s  tools/blender/clearance_profile.py              126 mutacji
   0.0099 s  tools/track/inspire_rail.py                     101 mutacji
   0.0099 s  tools/blender/sweep.py                          117 mutacji
   0.0092 s  tools/blender/lod.py                            137 mutacji
```

`build_alignment.py` sam jest **8,7 %** sumy. Zmiana tego jednego pliku kosztowałaby przy
pamięci per plik 0,02 s, a zmiana `lod_paths.py` — 0,00014 s, sto czterdzieści razy mniej.

## 5. Drugi powód, mocniejszy od pierwszego: NIKT nie potrzebuje jednego celu

Pozycja zakładała istnienie „testu, który potrzebuje świeżego przeliczenia dla **jednego**
modułu". Przejście po module mierzyło też, ile celów niesie wynik, który wołający dostaje:

```
celow w wyniku: [63]   — 18 z 20 wywolan
celow w wyniku: [61]   —  2 z 20 wywolan (LEGACY_KINDS)
```

**Zero z dwudziestu** wywołań zawęża. Dwa, które wyglądają na „jeden plik" — bo jeden plik
zmieniają — potrzebują całej listy **właśnie po to, żeby ją porównać**:

```python
assert len(po) > len(przed), (len(po), len(przed))
assert [m.id for m in sweep.collect()] == [m.id for m in przed], (...)
```

Parametr zawężenia w `collect()` w tych dwóch miejscach nie skróciłby testu, tylko
**odjął mu treść**: `test_pamiec_collect_UNIEWAZNIA_SIE_gdy_tresc_celu_sie_zmieni` sprawdza,
że zmiana jednego celu unieważnia pamięć **całego przebiegu**, a to zdanie o zawężonym
wyniku nie ma sensu. Dlatego zawężenie odpada **przed** rachunkiem czasu, nie po nim.

## 6. Co z tego wynika w kodzie

Pozycja kończy się **bez zmiany zachowania** — jej pole „Skończone, gdy" przewiduje ten
wynik wprost. Zmienione są dwie liczby, które ten pomiar unieważnił, i obie dostają commit
przy sobie, wzorcem 6.B45: „dziesięć wywołań po 0,224 s" było prawdą na `665bd98`
i przestało nią być w commicie, który tę pamięć wprowadził.

## 7. Czego świadomie nie zrobiłem

- **Nie dołożyłem parametru zawężenia do `collect()`** — §5 mówi, dlaczego nie ma
  wołającego, który by go użył.
- **Nie dołożyłem pamięci per plik** — §3 mówi, że stawka to 0,40 szumu.
- **Nie dołożyłem bramki.** Rozważałem test na liczbę świeżych przeliczeń w całym module,
  ale zmierzenie jej wymaga przejścia całego modułu, czyli 16 s wewnątrz modułu, który
  trwa 16 s. Tańsze warianty (para wywołań pod rząd, unieważnienie przy zmianie treści,
  rozdział po `kinds`) **już stoją** w rodzinie `test_pamiec_collect_*` z 6.B38 i w
  `test_legacy_kinds_are_a_subset_of_the_new_run`; dokładanie czwartego wariantu tej samej
  własności byłoby wymyśleniem zmiany, żeby coś oddać.
- **Nie tknąłem `ast.parse` w `test_every_mutation_still_parses`** — poza zakresem
  z pozycji, i 6.B38 nazwało tamte 6,44 s pracą, nie marnotrawstwem.

## 8. Zauważone przy okazji, nietknięte

Owinięcie `collect()` licznikiem kluczy pokazało, że **pamięć nie jest w tym module
mierzona jako całość** — cztery testy 6.B38 pilnują par wywołań i unieważnienia, ale
liczba świeżych przeliczeń w przebiegu nie jest niczyją asercją. Klucz, który stałby się
zmienny w sposób widoczny dopiero **między** testami, przeszedłby cały zestaw, a moduł
zapłaciłby 20 × 0,22 s. Przyrząd na to musi jednak przejść moduł, więc jest to osobna
pozycja o własnym pomiarze kosztu, nie dopisek do tej.
