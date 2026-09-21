# 6.D333 · Sto piętnaście streszczeń i SZEŚĆDZIESIĄT PIĘĆ dosłownych powtórzeń tytułu — a moje cztery kształty zostawiły siedemdziesiąt siedem w klasie resztkowej

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `2b4ba3a`

6.D323 §3 zmierzyło, że z 255 scaleń o komunikacie dłuższym niż tytuł **199 nie
nazywa żadnego modułu ani zapadki**, i zapisało wprost, że czym ta treść jest, nie
pyta. Ta pozycja **czyta i klasyfikuje**; żadnego komunikatu nie przepisuje i żadnej
reguły pisania nie ustanawia.

Czytniki `komunikaty` i `nazwy_modulow_i_zapadek` — **pożyczone** z
`test_commit_claims.py`, tak jak każe pole.

---

## 1. Kontrola przyrządu ZDANA — populacja wychodzi równo 199

```
scalen w drzewie: 336 ; populacja 'dluzszy, a nic nie nazywa': 199   [6.D323: 199]
```

**Przewidywanie V1 jest OBALONE i to jest pierwsze znalezisko.** Zapowiadałem, że
populacja nie wyjdzie równa 199, bo od 6.D323 przybyło scaleń. Nie przybyło: scaleń
jest **dokładnie 336**, tyle samo co wtedy, mimo że w międzyczasie domknięto kilka
pozycji.

Powód jest mechaniczny i wart zapisania: **to repozytorium scala SQUASHEM**, a squash
daje commit o **jednym** rodzicu. Populacja „scalenie" rośnie więc wyłącznie
o scalenia `main` do gałęzi i o `Merge remote-tracking branch` — nie o domknięte
pozycje. Każdy pomiar mówiący „na N scaleniach" w tym drzewie mierzy zatem populację,
która prawie stoi w miejscu, a nie tempo pracy.

## 2. Cztery kształty spisane PRZED pomiarem — i to, czego nie objęły

Kolejność rozstrzygania spisałem przed pomiarem; pierwsza pasująca wygrywa.

```
=== CZTERY KSZTALTY (pierwsza pasujaca wygrywa) ===
   WYPIS CI                   4
   CYTAT Z POLA               3
   STRESZCZENIE ZDANIAMI    115
   INNE                      77
   SUMA                     199   (populacja 199)   ZGADZA SIĘ
```

**Suma sprawdzona, a nie założona** — pole tego żądało.

**Klasa resztkowa ma 77 pozycji, czyli 39 % populacji, i nie jest resztką.** Zapisuję
to jako wynik, a nie jako niedoróbkę do zamiecenia: cztery kształty, które spisałem
z góry, opisują trzy piąte klasy, a o dwóch piątych nie mówią nic. §4 czyta je
wszystkie.

### 2.1 Usterka przyrządu: zdanie prozy BYWA ZAWINIĘTE

Pierwsza wersja dawała **109 / 83** zamiast 115 / 77. Kształt „streszczenie zdaniami"
testowałem **wiersz po wierszu** — a komunikat commita łamie się na 80 znakach, więc
zdanie „Cztery klasy hierarchii zmierzone osobno dla kilometrażu 1916,2 m: STIB nie
publikuje atrybutu…" nie kończyło się kropką w żadnym pojedynczym wierszu i wpadało
do klasy resztkowej. Poprawka skleja akapit (bloki rozdzielone pustą linią) przed
sprawdzeniem zdania: **83 → 77**.

Zgłaszam to, zamiast poprawić po cichu. Jest to **czwarty raz w tej sesji**, gdy sito
myli się na jednostce tekstu, a nie na regule — po członie nazwy (6.D320, 6.D327,
6.D329) tym razem na **wierszu wobec akapitu**.

## 3. Odpowiedź na pytanie zadane wprost: ile jest streszczeniem pozycji

Pole żądało tej liczby także wtedy, gdy żaden nie jest.

**Streszczeniem zdaniami jest 115 z 199, czyli 58 %.** Do tego dochodzi kształt,
którego nie przewidziałem i którego nie doliczam do tamtych — bo jest **mocniejszy**,
a nie taki sam:

```
=== KLASA 'INNE' (77) PRZECZYTANA ===
   POWTORZENIE TYTULU (gałęzi albo scalenia)    65
   AUTOMAT GITA (# Conflicts)                    8
   JEDEN WIERSZ, NOWA TRESC                      4
   SUMA                                         77
```

**Sześćdziesiąt pięć komunikatów to DOSŁOWNE powtórzenie tytułu** — ogon jest jednym
wierszem, którego podobieństwo do tytułu scalenia albo do tytułu gałęzi wynosi co
najmniej 0,75, a w wielu wypadkach równo **1,00**:

```
   e5f608d31  pod=1.00  6.C3: telemetria odtworzona jako ruch zadany wychodzi ze sceny bajt w bajt taka, jaka weszła
   f969f9bda  pod=1.00  Naprawa czerwonego main: pole Wyjście pozycji 6.B22 nazywało raport, który już istnieje
   28636109c  pod=1.00  Kolejka, czwarte uzupełnienie: sześć znalezisk czterech agentów i jedna obserwacja o rytmie
   68aa7d6ea  pod=0.80  6.B15: 80 modułów w tools/tests/, nie 73 — 78 z 80 ma wykonaną kontrolę negatywną
```

Pole mówiło, że „tylko pierwszy z tych kształtów jest nadmiarowy wobec komunikatu
gałęzi". **Nadmiarowe są dwa, a drugi jest nadmiarowy w stopniu skrajnym:** ogon nie
streszcza gałęzi, tylko ją **cytuje**. Podaję obie liczby osobno — 115 streszczeń
i 65 powtórzeń — zamiast zlać je w jedną, bo starzeją się inaczej: streszczenie może
przestać pasować do gałęzi, powtórzenie nie może.

**Klasa „jeden wiersz, nowa treść" ma cztery pozycje** i to jedyne cztery komunikaty
z tych 77, które mówią coś, czego tytuł nie mówi:

```
   74f5b4a6a  6.D11: zestaw ma budżet czasu w CI, ale NIE w kodzie wyjścia — i to jest cała decyzja tej pozycji
   308cac335  6.A9: osiem poleceń Sim.Runner ma test kodu wyjścia, każdy pada na własnej mutacji
   ee84432ae  Tryb ręczny wykonuje trzy decyzje właściciela: limit 72 km/h z planu, licznik miniętych, hamulec awaryjny
   fe14d7298  T-212: zespół dostępu nad peronem — peron 95,0 m, schody, winda, antresola, korytarz, portal
```

**Osiem to automat gita** — `# Conflicts:` z `docs/TASKS.md`, czyli tekst, którego
nikt nie napisał.

## 4. Piąta liczba: ogon krótszy niż trzy wiersze

```
   ogon KROTSZY niz trzy wiersze: 91 z 199, czyli 46 %
```

Przewidywanie V5 („mniej niż połowa") trafione, ale o cztery punkty — i liczba ta
staje się czytelna dopiero razem z §3: 65 z tych krótkich to powtórzenia tytułu,
a osiem to automat gita.

## 5. Komunikaty pasujące do więcej niż jednego kształtu — kolejność JEST treścią

```
=== KOMUNIKATY PASUJACE DO WIECEJ NIZ JEDNEGO KSZTALTU: 7 ===
   d1623a72c  WYPIS CI + CYTAT Z POLA + STRESZCZENIE ZDANIAMI
   d3646b29b  WYPIS CI + STRESZCZENIE ZDANIAMI
   f9502b951  WYPIS CI + STRESZCZENIE ZDANIAMI
   269050901  WYPIS CI + STRESZCZENIE ZDANIAMI
   96dc2fe9e  CYTAT Z POLA + STRESZCZENIE ZDANIAMI
   9faf5a269  CYTAT Z POLA + STRESZCZENIE ZDANIAMI
   7a817dfe7  CYTAT Z POLA + STRESZCZENIE ZDANIAMI
```

Przewidywanie V6 trafione. **Wszystkie cztery wypisy CI i wszystkie trzy cytaty
z pola są JEDNOCZEŚNIE streszczeniami** — gdyby kolejność była odwrotna, klasa
„streszczenie" miałaby 122, a obie tamte **zero**. Zapisuję to, bo jest to ten sam
kształt, który 6.D317 §2 nazwało przy klasach nakładających się: liczba klasy zależy
od miejsca w kolejce tak samo jak od drzewa.

## 6. Przewidywania — cztery trafione, jedno obalone, jedno z zastrzeżeniem

| # | przewidywanie | wynik |
|---|---|---|
| V1 | populacja nie wyjdzie równa 199 | **OBALONE**: 199 co do jedynki, bo squash nie tworzy scalenia (§1) |
| V2 | najliczniejszy kształt to STRESZCZENIE ZDANIAMI | **trafione**: 115 z 199 |
| V3 | wypisów CI mniej niż 20 | **trafione**: cztery — i wszystkie cztery są zarazem streszczeniami (§5) |
| V4 | klasa INNE niepusta | **trafione**, ale 77 to nie jest „niepusta" — to 39 % populacji (§2) |
| V5 | mniej niż połowa ma ogon krótszy niż trzy wiersze | **trafione**: 46 % |
| V6 | co najmniej jeden komunikat pasuje do dwóch kształtów | **trafione**: siedem |

## 7. Czego świadomie nie zrobiłem

Nie przepisałem ani jednego komunikatu, nie ustanowiłem reguły pisania komunikatów
scalenia, nie tknąłem `klasy_sladu` ani `DIFF_SCALENIA`, nie tknąłem `src/` ani
`data/` — wszystko to stoi w polu „Poza zakresem".

**Nie dociągnąłem sita do zera w klasie resztkowej.** Podklasy z §3 wypisuję jako
odczyt klasy „inne", a nie podmieniam nimi czterech kształtów spisanych przed
pomiarem — bo wtedy nie dałoby się zobaczyć, że lista spisana z góry chybiła o dwie
piąte.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

Osiem komunikatów `# Conflicts:` opisuje konflikt **wyłącznie w `docs/TASKS.md`** —
za każdym razem w tym samym pliku i w żadnym innym. Kolejka jest więc jedynym
miejscem w drzewie, które rozjeżdża się między gałęziami na tyle często, żeby
zostawić ślad w historii; ta pozycja tego nie mierzy i nie wyciąga z tego wniosku.
