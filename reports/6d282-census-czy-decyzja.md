# 6.D282 — 59, 0 i 18, a POŁOWA populacji 152 jest artefaktem czytania scaleń

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `80aa7da`

Pozycja żądała trzech liczb: ile ze **152** ruchów zapadki bez wzmianki w komunikacie
to podniesienie **rutynowe**, ile to **decyzja**, a ilu **nie da się zaklasyfikować**.
Liczby są niżej. Ważniejsze od nich jest to, co wyszło po drodze: **siedemdziesiąt
pięć ze 152 to commity SCALAJĄCE**, w których zapadka nie ruszyła się wcale.

## 1. Populacja odtworzona co do jedynki — i to też jest wynik

```
widoczne_bez_zgloszonego DZIS: 152   (pozycja mowi 152)
```

**Dokładnie 152, mimo ośmiu pozycji domkniętych w tej sesji**, z których każda ruszała
census. Powód jest prosty i mówi coś o samej regule: wszystkie osiem **nazwało** swoje
zapadki w komunikacie, więc do tej populacji nie weszły. Przewidywanie mówiło 160–175
i było **nietrafione**.

Rozkład zapadek w populacji: **87** wystąpień nazwy `MINIMUM_DETAIL_BLOCKS`, **49** nazwy `MIN_REPORTS`,
a dalej ogon 34 nazw po 1–5 wystąpień; nazw różnych jest **36**. Commitów z jedną
zapadką jest **123**, z dwiema **20**, z trzema i więcej **9**.

## 2. Trzy liczby, i czwarta, której pozycja nie przewidywała

Kryterium rutyny wzięte wprost z pola „Wyjście": **próg jedzie za wielkością mierzoną
przez ten sam commit**. Mierzalnie: `delta zapadki == delta korpusu` w tym samym diffie.
Korpus nazwany tam, gdzie da się go nazwać z diffa — dla pliku raportów (stała `MIN_REPORTS`, korpus: pliki dodane pod `reports/`)
i dla bloków kolejki (stała `MINIMUM_DETAIL_BLOCKS`, korpus: bloki `##### ` dopisane
do `docs/TASKS.md`).
Te dwie dają **136 ze 177** wystąpień w populacji.

| klasa | ile |
|---|---|
| **RUTYNA** — próg jedzie za korpusem | **59** |
| **DECYZJA** — próg ruszony bez zmiany mierzonej wielkości | **0** |
| **NIE DA SIĘ ZAKLASYFIKOWAĆ** | **18** |
| **ARTEFAKT SCALENIA** | **75** |

## 3. Siedemdziesiąt pięć artefaktów — i jak to wyszło

Pierwszy przebieg dał `rutyna 108, decyzja 1, nie da się 43` i jedyną „decyzją" był
`2cc35a72` z wypisem **`MIN_REPORTS: próg +116, korpus +1`**. Skok o 116 przy jednym
dopisanym raporcie jest liczbą, w którą nie da się uwierzyć — i słusznie:

```
$ git log -1 --format='%h %s' 2cc35a72
2cc35a7 Merge remote-tracking branch 'origin/main' into claude/6d43-pojemnosc-puli
$ git ls-tree -r --name-only 2cc35a72^ reports/ | wc -l   ->  156
$ git ls-tree -r --name-only 2cc35a72  reports/ | wc -l   ->  157
```

To jest **commit scalający**. Czytnik `strumien_diffow` używa
`--diff-merges=first-parent`, więc diff scalenia pokazuje **wszystko, co przyszło
z drugiej gałęzi** — zapadka wygląda na skoczoną o dziesiątki, choć ten commit nie
ruszył jej wcale. Po odsianiu scaleń jedyna „decyzja" znika, a liczba rutyn spada
z 108 do 59.

**Skutek dla liczby 152 z 6.D279 §8.1:** połowa tej populacji to nie „ruch zapadki bez
wzmianki", tylko **ten sam ruch policzony drugi raz przy scaleniu**. Liczba 152 zostaje
prawdziwa jako liczba COMMITÓW spełniających warunek czytnika; nieprawdziwe byłoby
czytanie jej jako liczby ZDARZEŃ. Zdania tamtego raportu nie ruszam — jest zapisem
swojego dnia (6.D108) — a różnicę zapisuję tutaj.

## 4. Zero decyzji, i dlaczego to nie jest podejrzane

`DECYZJA` wyszła **zerowa** i przewidywanie mówiące 5–25 było nietrafione. Powód jest
w regule, nie w danych: zapadki górne (`MAX_`) wolno **tylko obniżać**, a dolne
(`MIN_`, `MINIMUM_`) jadą za rosnącym drzewem. Ruch, który byłby decyzją — podniesienie
progu bez zmiany mierzonej wielkości — jest w tym projekcie zakazany i historia go nie
zawiera. **Że sito taki ruch ROZPOZNAJE, pokazuje KN-1** (§5): jedno podniesienie bez
zmiany korpusu i klasa `DECYZJA` rośnie z 0 na 1.

## 5. Kontrole, przewidywania spisane PRZED przebiegami

Na **pełnej** kopii drzewa z `.git`, mutacje zakładane jako **prawdziwe commity**.
Baza: rutyna **59**, decyzja **0**, nie da się **18**.

| kontrola | zmiana | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-1 | próg raportów podniesiony o jeden **bez** dopisanego pliku | klasa DECYZJA | **decyzja 0 → 1** | tak |
| KN-2 | raport dopisany **i** próg podniesiony o jeden | klasa RUTYNA | **rutyna 59 → 60** | tak |
| KN-3 | próg raportów ruszony w **dół**, bez zmiany korpusu | **nie** RUTYNA | **decyzja 0 → 1** | tak |

Próg raportów to stała `MIN_REPORTS`, a korpus, który ona liczy, to pliki pod
`reports/`; wszystkie trzy mutacje dotyczyły tej pary.

KN-1 jest kontrolą negatywną, której żądało pole „Weryfikacja": bez niej sito mogłoby
zwracać **wszystko** jako rutynę i nikt by tego nie zobaczył, bo w historii decyzji nie
ma. KN-2 jest kontrolą przyrządu z tego samego pola. KN-3 dołożyłem sam, bo „rutyna"
jest o progu jadącym **za** wielkością, a nie o dowolnym ruchu — i ruch w dół
rzeczywiście do rutyny nie trafia.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_commit_claims.py
  5/5 przeszło

$ python3 tools/tests/test_all.py
  2649/2649 przeszło
  KOD=0
```

## 7. Czego świadomie nie zrobiono

* **Nie napisano bramki odrzucającej ruch zapadki bez wzmianki** — pole „Poza zakresem"
  zamyka to wprost i odsyła do 6.D279.
* **Nie zmieniono czytnika `test_commit_claims.py`** ani `--diff-merges=first-parent`.
  Odsianie scaleń zrobiłem **w pomiarze**, nie w module: zmiana czytnika ruszyłaby
  cztery podłogi, o które ta pozycja nie prosi.
* **Nie przepisano ani jednego dawnego komunikatu** i nie ruszono zdania 6.D279 o 152.
* **Nie nazwano korpusu dla pozostałych 34 zapadek.** Tam, gdzie korpusu nie da się
  wyczytać z diffa, klasa brzmi „nie da się" — i to jest odpowiedź, nie luka.

## 8. Zauważone przy okazji, nietknięte

`d833c41c` — commit przypięty w `test_commit_claims.py` jako
`COMMIT_WIDOCZNE_BEZ_ZGLOSZONEGO` — trafia u mnie do klasy „ruch nieczytelny
w diffie": przypisanie zapadki zmienia w nim wiersz, w którym stoi też coś innego,
więc wzorzec `^[+-]\s*NAZWA = \d+$` go nie łapie. Zapadka jest tam ruszona naprawdę;
nieczytelny jest **zapis**, nie zdarzenie.
