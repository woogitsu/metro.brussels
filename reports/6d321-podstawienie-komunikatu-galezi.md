# 6.D321 · Klasę zmienia 158 commitów i WSZYSTKIE są scaleniami — a przesunięcie MIĘDZY klasami idzie tylko w JEDNĄ stronę

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `139fbe6`

6.D311 §3 zmierzyło, że trzydzieści osiem scaleń z czterdziestu ośmiu nie wymienia ani
jednej nazwy modułu ani zapadki, a 6.D279 wpuściło scalenia do populacji zdaniem, że
niosą ten sam komunikat co commity gałęzi. Ta pozycja liczy, **ile klas by się
przesunęło**, gdyby scalenie czytało komunikat swojej gałęzi. **Liczy i niczego nie
przełącza** — ani `klasy_sladu`, ani `DIFF_SCALENIA`, ani rozstrzygnięcia 6.D279.

Cztery liczby stoją w §2. Wynik, dla którego warto było tę pozycję wziąć: **przesunięcie
MIĘDZY klasami jest jednokierunkowe — dwadzieścia razy `nic_wspolnego` → `dotyczy`
i ANI RAZU w drugą stronę** — a cała reszta ruchu to **wejścia do populacji**, nie
zmiany klasy wewnątrz niej.

---

## 1. Kontrola przyrządu — ZDANA co do obu połówek pary

Pole żąda, żeby para `ead62d2aa1ae` / `c705199f1bb7` **nie** zmieniła klasy, bo obie
jej połowy stoją w `bez_raportu`, a raportu nie dopisuje żadna z nich.

```
   ead62d2aa1ae  dzis=bez_raportu        po=bez_raportu         scalenie=True
   c705199f1bb7  dzis=bez_raportu        po=bez_raportu         scalenie=False
```

Żadna z połówek nie drgnęła. Kontrola sprawdza tu więcej, niż żądało pole: pokazuje
też, że **jedna połowa jest scaleniem, a druga nie** — czyli podstawienie miało na
czym zadziałać i nie zadziałało, zamiast nie mieć na czym.

**Druga kontrola, której pole nie żądało, a która rozstrzyga o poprawności przyrządu:
ze 158 commitów zmieniających klasę SCALENIAMI jest 158, a zwykłych ZERO.** Podstawienie
dotknęło dokładnie tego zbioru, który miało dotknąć. Gdyby ruszyło choć jeden commit
niescaleniowy, mierzyłbym co innego niż pytanie pozycji.

## 2. CZTERY LICZBY, których żądało pole

```
=== LICZNOSCI KLAS ===
   klasa              dzis     po
   dotyczy             157    190
   nic_wspolnego       214    229
   bez_raportu         113    173
   SUMA                484    592  <- populacja
```

```
=== KIERUNKI PRZESUNIECIA ===
   (poza populacja)         -> bez_raportu               64
   (poza populacja)         -> nic_wspolnego             45
   nic_wspolnego            -> dotyczy                   20
   (poza populacja)         -> dotyczy                   14
   nic_wspolnego            -> (poza populacja)          10
   bez_raportu              -> (poza populacja)           4
   dotyczy                  -> (poza populacja)           1
   RAZEM zmieniajacych klase: 158
```

```
=== SCALENIA, KTORE ZOSTAJA W bez_raportu MIMO PODSTAWIENIA ===
   zostaja: 71
```

Cztery liczby żądane przez pole: **484 → 592** (populacja), **158** (zmieniających
klasę), rozbicie kierunków wyżej, **71** (zostających w `bez_raportu`).

**Odpowiedź na pytanie zadane wprost nie brzmi „żaden": zmienia klasę 158 commitów.**

## 3. RUCH JEST W TRZECH CZĘŚCIACH, a sumowanie ich do jednej liczby myli

```
WCHODZA do populacji:        123
WYCHODZA z populacji:         15
przesuniecia MIEDZY klasami:  20
                             ---
                             158
```

**Sto dwadzieścia trzy scalenia dziś NIE ZGŁASZAJĄ kontroli w ogóle, a po podstawieniu
zaczynają.** To jest największa część ruchu i nie jest zmianą klasy w żadnym potocznym
sensie — jest **wejściem do populacji**. Populacja rośnie o 22 %, ze 484 na 592.

Piętnaście idzie w drugą stronę: komunikat gałęzi **nie** zgłasza kontroli tam, gdzie
zgłaszał komunikat scalenia. Nie jest to usterka po żadnej ze stron — scalenie miewa
komunikat streszczający, w którym kotwica kontroli pada, a wierzchołek gałęzi jej
nie ma.

**A przesunięć MIĘDZY klasami, czyli tego, o co pole pyta najściślej, jest dwadzieścia.**

## 4. DWADZIEŚCIA PRZESUNIĘĆ I WSZYSTKIE W TĘ SAMĄ STRONĘ

```
   083f192958a5  nic_wspolnego  -> dotyczy
   154ad30971e3  nic_wspolnego  -> dotyczy
   2ffb0b00cce5  nic_wspolnego  -> dotyczy
   4e56958d7036  nic_wspolnego  -> dotyczy
   5ae1b52d99b3  nic_wspolnego  -> dotyczy
   5b1405de6078  nic_wspolnego  -> dotyczy
   64fefc23ba37  nic_wspolnego  -> dotyczy
   665bd987a439  nic_wspolnego  -> dotyczy
   77108a09131f  nic_wspolnego  -> dotyczy
   7bf506295338  nic_wspolnego  -> dotyczy
   82055442bc9d  nic_wspolnego  -> dotyczy
   96dc2fe9e424  nic_wspolnego  -> dotyczy
   988eff1ae58d  nic_wspolnego  -> dotyczy
   a39295828837  nic_wspolnego  -> dotyczy
   becc2742eb65  nic_wspolnego  -> dotyczy
   c1f5618689ac  nic_wspolnego  -> dotyczy
   e8db22f07822  nic_wspolnego  -> dotyczy
   efccb6160f9e  nic_wspolnego  -> dotyczy
   f259d5d4b2ca  nic_wspolnego  -> dotyczy
   f684e40a3af5  nic_wspolnego  -> dotyczy
```

**Dwadzieścia z dwudziestu, `nic_wspolnego` → `dotyczy`. Ani jedno w drugą stronę.**

Pole ostrzegało wprost, żeby nie przyjąć bez pomiaru, że przesunięcie idzie wyłącznie
w tę stronę — i **pomiar mówi, że jednak idzie**. Jest to ostrzeżenie **trafne co do
obowiązku policzenia i chybione co do wyniku**, i podaję to tak, zamiast wybierać jedno
z dwóch: gdybym nie policzył drugiej strony, miałbym tę samą liczbę bez prawa do niej.

Mechanizm jest po nazwaniu prosty: `dotyczy` wymaga **wspólnej nazwy** komunikatu
i raportu. Komunikat scalenia bywa jednym wierszem tytułu; komunikat gałęzi niesie
nazwy modułów i zapadek, bo pisze go agent domykający pozycję. Podstawienie może więc
**dołożyć** wspólną nazwę, a odjąć jej nie może — chyba że komunikat gałęzi przestaje
zgłaszać kontrolę, a wtedy commit **wypada z populacji**, zamiast zmienić klasę.

## 5. OSTRZEŻENIE POLA O `bez_raportu` — POTWIERDZONE co do litery

Pole ostrzega, że `bez_raportu` jest przypisywana po **obecności pliku** w `reports/`,
a nie po nazwach, więc podstawienie komunikatu nie może jej ruszyć.

**Potwierdzone: ani jedno scalenie nie przeszło z `bez_raportu` do `dotyczy` ani do
`nic_wspolnego`.** Cztery, które z tej klasy wyszły, wyszły **z populacji** —
ich komunikat gałęzi nie zgłasza kontroli w ogóle (`53b92d38cafa`, `6fa604c49fb6`,
`86ae750dfe7b`, `9c9060d31e12`).

**MÓJ WARUNEK OBALENIA BYŁ NAPISANY NIEPRECYZYJNIE i mówię to zamiast naciągnąć
werdykt.** Spisałem przed pomiarem: „jeśli KTÓREKOLWIEK scalenie wyjdzie z `bez_raportu`,
mój przyrząd rusza diff, a nie tylko komunikat — i wtedy raportuję to jako USTERKĘ
PRZYRZĄDU". Cztery wyszły. Usterką to nie jest i widać dlaczego: warunek nie odróżniał
**wyjścia do innej klasy** (co byłoby usterką, bo klasę rozstrzyga diff) od **wyjścia
z populacji** (co jest własnością bramki wejściowej, a ta czyta komunikat). Zapisuję
warunek w brzmieniu, w jakim go postawiłem, pomiar, który go spełnił, i powód, dla
którego werdykt brzmi „nie usterka" — bo trzecia z tych rzeczy jest jedyną, której
nie dałoby się dopisać później bez podejrzenia o dopasowanie.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| S1 | kontrola przyrządu przejdzie | trafione |
| S2 | zmieniających klasę mniej niż 38 | **OBALONE** — 158, czyli czterokrotnie więcej |
| S3 | odpowiedź nie brzmi „żaden" | trafione |
| S4 | przesunięcia pójdą w OBIE strony | **OBALONE** — między klasami wyłącznie `nic_wspolnego` → `dotyczy` |
| S5 | ani jedno scalenie nie wyjdzie z `bez_raportu` | **OBALONE co do litery, potwierdzone co do treści** — §5 |
| S6 | populacja nie odtworzy 475 z 6.D283 | trafione — 484 |

**S2 obalone najmocniej i z powodu, którego nie przewidziałem.** Postawiłem je na
trzydziestu ośmiu milczących scaleniach z 6.D311, czyli na populacji **czterdziestu
ośmiu par**. Podstawienie działa na **wszystkich 336 scaleniach w drzewie**, a nie na
próbce, którą tamta pozycja badała. Liczba 38 nie była więc sufitem niczego — była
liczbą o innej populacji, a ja wziąłem ją za ograniczenie.

**S4 obalone jest właściwym wynikiem §4, a nie porażką:** policzyłem obie strony, bo
pole kazało, i druga wyszła pusta. Zero policzone jest czymś innym niż zero założone.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono `klasy_sladu`, `DIFF_SCALENIA` ani żadnej podłogi** — pole zabrania,
  a §3 pokazuje, że zmiana przesunęłaby populację o 22 %, czyli dotknęłaby każdej
  liczby, którą ta rodzina bramek już opublikowała.
- **Nie zrewidowano rozstrzygnięcia 6.D279** i nie przygotowano pod nie jednej
  odpowiedzi: §3 podaje ruch w trzech częściach właśnie po to, żeby nie dało się
  go zsumować do jednego zdania „scalenia trzeba przełączyć".
- **Nie przepisano ani jednego komunikatu.**
- **Nie policzono, czym są 123 scalenia wchodzące do populacji** ponad to, że wchodzą —
  pole pyta o klasy, nie o treść.
- **Nie tknięto `src/` ani `data/`.**

## 8. Zauważone przy okazji, nietknięte

1. **Scaleń w drzewie jest 336 przy 1063 commitach**, czyli blisko co trzeci commit.
   Każda liczba tej rodziny bramek zależy więc od tego, jak traktuje się scalenia —
   a rozstrzygnięcie 6.D279 zapadło na czterdziestu ośmiu parach.
2. **Siedemdziesiąt jeden scaleń zostaje w `bez_raportu` mimo podstawienia.** Są to
   scalenia, których gałąź zgłasza kontrolę, a commit nie dopisuje raportu — czyli
   dokładnie te, o których `bez_raportu` mówi prawdę niezależnie od tego, czyj
   komunikat się czyta.
3. **Piętnaście scaleń WYPADA z populacji po podstawieniu**, w tym jedno z klasy
   `dotyczy` (`e1fcfc11bc39`). Komunikat scalenia zgłasza tam kontrolę, której
   komunikat gałęzi nie zgłasza — czyli streszczenie niesie coś, czego nie ma
   w streszczanym. Czym to jest, ta pozycja nie pyta.
