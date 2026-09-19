# 6.D281 — 2, 9, 0 i co najmniej 11: dwie drogi mają przecięcie PUSTE, a obie razem widzą mniejszość

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `8c0fd72`

Pozycja żądała czterech liczb: ile zdjęć pogrubienia widzi droga po POPULACJI, ile
po KOMUNIKATACH commitów, ile widzą OBIE i ile nie widzi ŻADNA. Są niżej. Po drodze
wyszły dwie rzeczy, których pozycja nie miała: **czytnik populacji nie daje się
przekierować na inne drzewo swoim własnym argumentem**, a **droga po populacji nie
odróżnia zdjęcia pogrubienia od skasowania zdania**.

## 1. Cztery liczby

| droga | widzi | commity |
|---|---|---|
| po **POPULACJI** (spadek liczby zdań o jednej pogrubionej wobec pierwszego rodzica) | **2** | `ab88b4c1` (42 → 40), `15f5aa32` (38 → 37) |
| po **KOMUNIKATACH** commitów | **9** | m.in. `f0a3fec8` (6.D275), `4a9529f6` (6.D278) |
| **OBIE** | **0** | — |
| **ŻADNA**, dolne ograniczenie | **co najmniej 11** | §3 |

**Przecięcie jest PUSTE i to jest główny wynik.** 6.D275 nazwało detektor historyczny
ślepym **z natury** — bo zdjęcie gwiazdek zachodzi w drzewie roboczym, przed commitem,
więc komunikat mówi o czymś, czego diff już nie pokazuje jako zmiany pogrubienia.
Pomiar od strony populacji to potwierdza: **ani jeden** z dwóch commitów, które widzi
populacja, nie jest wśród dziewięciu, które mówią o tym w komunikacie.

Zakres: korpus prozy to komentarze i docstringi pod `tools/tests/`, więc „cała historia"
znaczy tu **674 rewizje** dotykające tego katalogu, każda porównana ze **swoim pierwszym
rodzicem** (6.D278: liczenie różnic między kolejnymi pozycjami `rev-list` daje artefakt
porządku). Jedna rewizja okazała się nieczytelna dla czytnika i jest policzona osobno.

Liczba **9**, a nie 12 z 6.D275: wzorzec komunikatu tamtej pozycji **nie został w drzewie**
jako stała, więc ten pomiar użył wzorca napisanego tutaj i podaje swoją liczbę zamiast
przepisywać tamtą. Różnica jest własnością wzorca, nie historii, i tak ją zapisuję.

## 2. Czego nie widzi żadna — dolne ograniczenie przez TRZECI przyrząd

Obie drogi mierzą **skutek uboczny**, nie samo zdarzenie. Żeby ograniczyć „nie widzi
żadna" od dołu, potrzebny był przyrząd patrzący na sam diff: wiersz **usunięty**
niosący `**N**` i wiersz **dopisany** niosący to samo `N` **bez** gwiazdek, w tym
samym commicie i tym samym pliku.

Skan znalazł **14** takich commitów. Z nich:

* **2** widzi droga po populacji (`ab88b4c1`, `15f5aa32`) — czyli **oba** spadki
  z historii są potwierdzonymi zdjęciami pogrubienia, a nie czymś innym;
* **1** widzi droga po komunikatach (`4a9529f6`);
* **11 nie widzi żadna**: `07dc360a`, `3fbc25d2`, `4c412828`, `5c107647`, `91c50df4`,
  `a8894d0f`, `b4384765`, `dad68a0c`, `e41ce062`, `f6c0c50f`, `fea30142`.

Jedenaście jest **ograniczeniem od dołu**, nie liczbą wszystkich: skan diffów łapie
wyłącznie te zdjęcia, po których liczba **przetrwała jako goła w tym samym miejscu**.
Zdjęcie, po którym zdanie przepisano albo liczbę usunięto, nie zostawia takiej pary.

Osobno: **8 z 9** komunikatów nie ma potwierdzenia w diffie — czyli mówią o zdjęciu,
którego diff nie pokazuje. To jest dokładnie ta ślepota, którą 6.D275 nazwało.

Skan odtworzył przy tym **przypadek założycielski**: `ab88b4c1` z liczbą `157`, czyli
ten, który wiersz `| 6.D281 |` wymienia z nazwy.

## 3. Usterka przyrządu: `root` nie przekierowuje korpusu

`TOB.zdania_o_jednej_pogrubionej(root)` woła `TMC.proza(None, root)`, a `proza` bierze
**katalog** korpusu z `TMC.ROOT` (`baza = katalog or os.path.join(ROOT, …)`); argument
`root` trafia wyłącznie do `korzen`, czyli do odczytu `.gitignore`. Zmierzone:

```
w drzewie roboczym:                 132
PRÓBA A — sam argument root:        132     <- drzewo HEAD~40, a liczba z drzewa roboczego
PRÓBA B — po podmianie TMC.ROOT:    119
po przywróceniu:                    132
```

**Pierwszy przebieg tego pomiaru szedł drogą A** — i dałby **zero spadków na 674
rewizjach**, czyli wynik wyglądający na czysty. Złapało to porównanie liczby dla
rewizji dawnej z liczbą dla drzewa roboczego, nie oko. Docstring czytnika mówi, że
`root` jest argumentem jawnym, „bo domyślny wiąże się przy imporcie" — to prawda
o wiązaniu domyślnego argumentu i **nieprawda o katalogu korpusu**.

## 4. Kontrole, przewidywania spisane PRZED przebiegami

Na **pełnej** kopii drzewa z `.git`, mutacje zakładane jako **prawdziwe commity**,
na PRAWDZIWYM zdaniu wziętym z populacji (nie na zdaniu zmyślonym).

| kontrola | zmiana | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-1 | zdjęte `**25**` w `csharp_assertions.py`, komunikat milczy | spadek populacji | **132 → 131, spadek TAK** | tak |
| KN-2 | SKASOWANE całe zdanie z populacji | **NIE** ma trafić do grupy „zdjęcie" | **132 → 131, spadek TAK** | **NIE** |
| KN-3 | commit bez zmiany w prozie | brak spadku | **132 → 132, spadek NIE** | tak |

**KN-2 obaliła przewidywanie i to jest jej wynik.** Pole „Weryfikacja" żądało kontroli
przyrządu: „commit, w którym populacja spada z innego powodu niż zdjęcie pogrubienia
(skasowane zdanie), ma NIE trafić do grupy »zdjęcie«". Zmierzone: **trafia**. Spadek
o jeden wygląda identycznie w obu przypadkach, bo droga po populacji widzi wyłącznie
liczbę, a nie powód jej zmiany. **Odróżnia je dopiero drugi przyrząd** — skan diffów
z §2, który pyta, czy ta sama liczba wróciła bez gwiazdek. I dlatego obie dzisiejsze
pozycje z §1 są potwierdzone: nie dlatego, że populacja spadła, tylko dlatego, że obie
stoją też w skanie diffów.

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py test_one_bold_sentences.py
  3/3 przeszło

$ python3 tools/tests/test_all.py
  2649/2649 przeszło
  KOD=0
```

## 6. Czego świadomie nie zrobiono

* **Nie napisano bramki na komunikaty commitów** — to 6.D279 i osobne rozstrzygnięcie
  (pole „Poza zakresem").
* **Nie przepisano historii** i nie ruszono ani jednego dawnego komunikatu.
* **Nie poszerzono `ZAPOWIEDZ_POMIARU`** ani żadnego wzorca prozy.
* **Nie ruszono `SPADKOW_ZDAN_W_HISTORII = 2`** — dzisiejszy pomiar daje tę samą
  dwójkę, na historii dłuższej o dziesięć rewizji.
* **Nie poprawiono czytnika z §3.** Zmiana sygnatury `proza` dotyka modułu, o który
  ta pozycja nie prosi, i zapaliłaby bramki w co najmniej dwóch innych miejscach —
  zapisane jako osobna pozycja.

## 7. Zauważone przy okazji, nietknięte

Skan diffów jest **trzecim** przyrządem w tej sprawie i jedynym, który patrzy na samo
zdarzenie, a nie na jego skutek. Nie stoi w drzewie jako bramka i nie jest tu
wprowadzany: pozycja żądała czterech liczb, a nie czwartego sita.
