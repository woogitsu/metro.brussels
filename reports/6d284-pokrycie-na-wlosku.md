# 6.D284 · Pokrycie, które wisi na włosku

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `a806a04`

## 1. O co pytała pozycja

Klasa `zbieg` bramki pokrycia — liczby pogrubione, które w oknie prozy ma pokrycie
wyłącznie przypadkowym wystąpieniem tej samej cyfry — jest z natury krucha, i bramka
sama tak ją nazywa. Dwa razy pod rząd (6.D278 i 6.D280) dopisanie **jednego** wiersza
ogniwa łańcucha wypchnęło pokrycie poza okno i zapaliło zapadkę na liczbie, której
nikt nie ruszał. Ile wpisów wisi na włosku, nie liczył nikt.

## 2. Jak liczone

Okno prozy ma `OKNO_PROZY` wierszy w każdą stronę. Dla każdego wpisu klasy `zbieg`
liczona jest odległość wierszowa każdego wiersza pokrywającego od bloku prozy — przed
blokiem od wiersza prozy, za blokiem od końca bloku, dokładnie tak, jak czytnik
**buduje** okno. Skraj okna to odległość równa szerokości okna: pokrycie stojące tam
wypada po dopisaniu jednego wiersza gdziekolwiek pomiędzy.

Warunek kruchości jest na **wszystkich** pokryciach wpisu, nie na najbliższym: wpis
z drugim pokryciem bliżej przeżyje takie dopisanie.

## 3. Trzy liczby

Drzewo `a806a04`, `tools/tests/`:

| | |
|---|---|
| pokrytych wyłącznie zbiegiem cyfr | **56** |
| najbliższe pokrycie dalej niż połowa okna | **22** |
| każde pokrycie na skraju okna (zniknie po jednym wierszu) | **1** |

Rozkład najbliższej odległości: 1 → 1, 2 → 10, 3 → 6, 4 → 5, 5 → 5, 6 → 3, 7 → 3,
8 → 1, 11 → 1, 12 → 3, 13 → 5, 14 → 1, 15 → 3, 16 → 2, 17 → 1, 18 → 2, 19 → 3, 20 → 1.
Dwie trzecie populacji stoi blisko; ogon jest długi i sięga samego skraju.

**Jedyny wpis kruchy stoi w tym samym module, co bramka**: zdanie o liczbie `12`
pokrytych wyłącznie kodem, pokryte wyłącznie przypisaniem `POKRYTYCH_WYLACZNIE_KODEM`
stojącym dokładnie na skraju okna za blokiem. Adres wierszowy stoi tu, a nie w kodzie,
i to jest ta sama zasada, którą moduł stosuje do `ZBIEGIEM_PER_PLIK`: numer wiersza
rusza się przy każdym dopisanym akapicie. Przy pisaniu tej pozycji ruszył się dwa razy.

## 4. Przewidywania wobec pomiaru

| co | przewidziane | zmierzone |
|---|---|---|
| dalej niż połowa okna | 12 | **22** |
| każde pokrycie na skraju | 4 | **1** |
| kruche i po jednej stronie | 3 | **1** |

Oba przewidywania nietrafione, w przeciwne strony: dalekich jest prawie dwa razy
więcej, niż się spodziewałem, a kruchych cztery razy mniej. Zapisuję jako rozjazd.

## 5. Kontrole negatywne

Na **kompletnej kopii drzewa** z `.git`; drzewo robocze w tym czasie **21/21**.

| KN | mutacja | wynik |
|---|---|---|
| KN-1 | jeden wiersz dopisany między liczbą a jej pokryciem | **18/21** |
| KN-2 | `any` zamiast `all` w warunku kruchości | **20/21** |
| KN-3 | skraj okna o jeden węższy | **19/21** |
| KN-4 | odległość przed blokiem liczona od `od`, nie od `wiersz` | **21/21 — zielony** |
| KN-5 | równość podniesiona o jeden | **20/21** |
| KN-6 | odległość zawsze równa jeden | **19/21** |

### KN-1 obaliła pierwszą wersję tej bramki

Przewidywałem, że wstawienie jednego wiersza zapali `MAX_POGRUBIONYCH_BEZ_POKRYCIA`
**i** obie nowe równości. Zapaliło `MAX_POGRUBIONYCH_BEZ_POKRYCIA` (populacja bez
pokrycia rośnie ze 175 na 176, a zapadka stoi dokładnie na 175) oraz parę
`przypisanie`/`zbieg` — a **obie nowe równości zostały zielone**. Zmierzona przyczyna:
liczba `12` straciła pokrycie i wypadła z klasy `zbieg`, ale w tej samej chwili liczba
`43` z sąsiedniego wiersza **weszła** do tej klasy, również ze skrajnym pokryciem.
Licznik kruchych pozostał na jedynce, a krucha była już inna liczba.

Dlatego bramka dostała trzecią część: `KRUCHE_ADRESY`, para (plik, napis) — nie numer
wiersza. Po jej dopisaniu KN-1 daje trzy czerwone zamiast dwóch. **Sama licznością
tego zdarzenia nie widać** i to jest wynik, którego pozycja nie przewidywała: trzy
liczby, których żądało pole „Wyjście", są dla podmiany wpisu ślepe.

### KN-4 obaliła podejrzenie z lektury

Komentarz przy `OKNO_PROZY` mówi, że okno jest symetryczne, a kod buduje je przed
blokiem od wiersza prozy, za blokiem od końca bloku — więc dla bloku wielowierszowego
byłoby niesymetryczne. Podejrzenie wpisałem do przewidywań przed przebiegiem.
Mutacja liczenia odległości od `od` nie zmieniła ani jednej liczby, bo w całej
populacji `wiersz` równa się `od`: **0** wpisów ma je różne, przy **23** wpisach
z pokryciem przed blokiem. Asymetria jest więc własnością kodu, której dzisiejsza
populacja nie odróżnia. Nie ruszam jej — pole „Poza zakresem" zabrania zmiany okna,
a i tak byłaby to zmiana bez zmierzonego skutku. Zapisane jako pozycja do kolejki.

## 6. Czego świadomie nie zrobiłem

- **Nie ruszyłem `OKNO_PROZY`, `MAX_POGRUBIONYCH_BEZ_POKRYCIA` ani klas pokrycia** —
  pole „Poza zakresem".
- **Nie zdjąłem ani nie dodałem żadnego pogrubienia**, również w prozie, którą tu
  dopisałem: pogrubiona liczba bez pokrycia weszłaby do populacji bramki, a ta
  zapadka stoi dziś dokładnie na swojej wartości i wolno ją tylko obniżać.
- **Nie poprawiłem kruchego wpisu** przez przesunięcie prozy bliżej stałej. Liczba
  krucha nie jest usterką sama w sobie; usterką było to, że nikt o niej nie wiedział.

## 7. Co zauważyłem, a czego nie tknąłem

- `wiersz` i `od` są w tej populacji zawsze równe, a kod je rozróżnia — pozycja 6.D295.
- Dwadzieścia dwa wpisy stoją dalej niż połowa okna; ile z nich zniknie po dopisaniu
  dwóch albo pięciu wierszy, a nie jednego, nie liczy nic — pozycja 6.D296.
- Moduł chodził 21,9 s przy dziewiętnastu testach, a chodzi 26,4 s przy dwudziestu
  jeden: każde z trzech sit woła czytnik osobno. Pamięci na wynik nie dokładam —
  byłaby zmianą zachowania cudzej bramki, o którą ta pozycja nie prosi; zapisane
  jako pozycja 6.D297.

## 8. Weryfikacja

```
$ python3 tools/tests/test_all.py test_message_claims.py
  ok   test_ile_pokrycia_WISI_NA_WLOSKU
  ok   test_liczba_pokryta_NA_SKRAJU_okna_trafia_na_liste_kruchych
  ...
  21/21 przeszło
      26.432 s  test_message_claims.py  (21 testów)

$ python3 tools/tests/test_all.py
  2656/2656 przeszło
  RAZEM 341.685 s, 2656 testów, 138 modułów
EXIT=0
```

Przed tą pozycją moduł miał dziewiętnaście testów i chodził 21,935 s (zmierzone na
kompletnej kopii drzewa stojącej na `54c6f70`), a cały zestaw liczył 2654 testy.
