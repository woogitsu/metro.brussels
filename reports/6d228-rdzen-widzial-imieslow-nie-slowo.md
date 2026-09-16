# 6.D228 — rdzeń widział imiesłów, nie słowo: 32 sekcje poza pomiarem

**16.09.2026**, na `e1c63f7`. Wejście: `tools/tests/test_report_claims.py`
(`SEKCJA_ZAUWAZONE`, `MIN_SEKCJI_ZAUWAZONE`, `MIN_RAPORTOW_Z_SEKCJA`,
`MIN_TWIERDZEN_W_ZAUWAZONYCH`), `reports/*.md` (nagłówki sekcji),
`tools/tests/test_report_hygiene.py` (`MIN_REPORTS`). Wyjście: rozszerzony rdzeń,
trzy przeliczone podłogi, bramka `test_rdzen_widzi_rodzine_ZAUWAZYLEM_a_nie_tylko_ZAUWAZONE`,
ten raport.

Decyzja właściciela z tego dnia: **rozszerzyć rdzeń i przeliczyć podłogi w tym samym commicie.**

## 1. Co było nie tak

`SEKCJA_ZAUWAZONE` w `tools/tests/test_report_claims.py` brzmiało `zauwa[zż]on` — rdzeń
z **końcówką imiesłowu**. Nagłówek „Co zauważyłem przy okazji, ale nie tknąłem" nie ma
imiesłowu, więc dla czytnika nie istniał. Rodzina odmian `zauważyłem` liczy w katalogu
**32 sekcje w 32 raportach**, czyli **19 % populacji**, i wszystkie stały poza pomiarem
podłóg 6.D216.

Zmierzone na `e1c63f7`, tym samym czytnikiem, tylko z podmienionym rdzeniem:

```
PO    sekcji=201 raportow=197 twierdzen=271     (rdzen `zauwa[zż]`)
PRZED sekcji=169 raportow=165 twierdzen=219     (rdzen `zauwa[zż]on`)
ZERO  sekcji=0   raportow=0   twierdzen=0       (rdzen oslepiony)
```

Różnica **32 / 32 / 52**.

## 2. Zdanie o granicy było o przypadku, którego nie ma

Przy stałej stało: „sekcja nazwana »Uwagi na marginesie« wypadłaby z pomiaru". Sprawdzone:
nagłówka „Uwagi na marginesie" nie ma w `reports/` **ani razu**. Zdanie o granicy opisywało
więc przypadek hipotetyczny, podczas gdy granica prawdziwa biegła 32 sekcje bliżej i nikt
jej nie nazwał. Komentarz jest **przepisany, a nie dopisany obok**, i wymienia dwie granice
dzisiejsze — obie z liczbą zamiast przykładu z głowy.

## 3. Zanieczyszczenie POLICZONE, nie oszacowane

Rdzeń pyta o **słowo**, nie o to, czy nagłówek jest sekcją. Z 32 dołożonych nagłówków
**jeden** sekcją nie jest — `serializacja-jobow-ci.md` §7 („Bramka, bo zestaw tej zmiany
nie zauważył"). Zanieczyszczenie **1 z 32 = 3,1 %**, wnosi 1 sekcję, 1 raport
i 2 twierdzenia.

## 4. Dlaczego podłogi mają zapas 5 / 5 / 8, a poprzednie miały ZERO

Poprzednie podłogi (158 / 154 / 207) stały na wartości z dnia commita — zapas **zero** —
i nigdy się nie zapaliły, bo w całej historii `reports/` nie ma ani jednego usunięcia pliku
ani zmiany nazwy (`--diff-filter=D` i `--diff-filter=R` dają zero). Dziś zapas jest
potrzebny, bo **istnieje znana poprawka, która te liczby obniży**: zanieczyszczenie z §3.
Podłoga bez zapasu zapaliłaby się na jego poprawieniu, czyli na pracy poprawnej — 6.D27.

Zapas nie oślepia bramki i to jest **zmierzone**: najmniejsza awaria, którą te podłogi mają
łapać, kosztuje 32 / 32 / 52, czyli sześć razy więcej niż zapas.

Nowe: `MIN_SEKCJI_ZAUWAZONE` **196**, `MIN_RAPORTOW_Z_SEKCJA` **192**,
`MIN_TWIERDZEN_W_ZAUWAZONYCH` **263**.

## 5. Bramka na ZACHOWANIU, bo sama podłoga da się uciszyć

`test_rdzen_widzi_rodzine_ZAUWAZYLEM_a_nie_tylko_ZAUWAZONE` stoi na wejściu syntetycznym:
pięć nagłówków, trzy mają wejść, dwa mają nie wejść. Powód jest zapisany w docstringu:
podłoga mówi tylko „sekcji jest za mało", a taki komunikat **da się uciszyć obniżeniem
podłogi**, czyli dokładnie tym ruchem, przed którym ostrzega 6.D27. Bramka na wejściu
syntetycznym mówi, **którego brzmienia zabrakło**, i obniżenie podłogi jej nie dotyczy.
Dwa nagłówki, które mają NIE wejść, są granicą z §2 — **wykonaną zamiast opisanej**.

## 6. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Baza: **20/21**, przy czym jeden FAIL jest **przedistniejący na `main`** i nie jest mój —
`6d225-dziura-interpolacji.md:155` cytuje bezwzględną wartość `ASERCJI_NAPISOWYCH_RAZEM`,
którą cudze scalenie unieważniło; poprawka leży w #638.

| | mutacja | PRZEWIDZIANE | ZMIERZONE | zgoda |
|---|---|---|---|---|
| KN-1 | rdzeń cofnięty do `zauwa[zż]on` | 18/21: podłoga + rodzina | **18/21**, dokładnie te dwa | ✅ |
| KN-2 | rdzeń oślepiony | 17/21: podłoga, rodzina, kontrola przyrządu 6.D216 | **14/21** — o trzy więcej | ❌ |
| KN-3 | rdzeń cofnięty **i** podłogi cofnięte do 158/154/207 | 19/21: podłoga ZIELONA (169 ≥ 158), czerwona tylko rodzina | **19/21**, dokładnie tak | ✅ |

Po każdej kontroli plik przywracany **z kopii**, nie przez `git checkout --`; `md5sum -c`
za każdym razem `OK`. Przed każdym przebiegiem `find . -name __pycache__ -prune -exec rm -rf {} +`.

**KN-2 obaliła moje przewidywanie i to jest znalezisko, nie pomyłka w arytmetyce.**
Oślepienie `SEKCJA_ZAUWAZONE` zapaliło dodatkowo **trzy bramki slajsu zakresu z 6.D227** —
`test_czytnik_zakresu_MILCZY_na_zakresie_nazwanym_SLOWEM_i_to_jest_zapisane`,
`test_czytnik_zakresu_liczy_KSZTALT_a_nie_prawdziwosc`,
`test_slajs_zakresu_jest_LICZONY_a_nie_odtwarzany_z_prozy`. Znaczy to, że slajs 6.D227
**pożycza czytnik sekcji** (6.D213), a nie czyta katalogu sam. Nie wiedziałem tego przed
przebiegiem i nie wyczytałem tego z kodu — powiedziała to kontrola negatywna.
Praktyczny skutek: rozszerzenie rdzenia przesuwa **także** slajs 6.D227, którego podłogi
(`MIN_TWIERDZEN_O_ZAKRESIE` 35, `MIN_SLAJS_SZEROKI` 64) zostają bez zmiany, bo populacja
im **urosła**, a są podłogami, nie równościami.

**KN-3 jest tą kontrolą, która dowodzi, że przeliczenie podłóg jest nośne.** Z rdzeniem
cofniętym i starymi podłogami bramka katalogu świeci **na zielono** przy 169 ≥ 158 —
czyli sama zmiana rdzenia bez przeliczenia podłóg zostawiłaby awarię niewidzialną.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py test_report_claims.py
  21/21 przeszło   (po scaleniu #638; przed nim 20/21 z FAIL-em z §6)
```

Moduły sąsiednie liczące drzewo, każdy osobno, wszystkie zielone:
`test_assertion_gate.py` 39/39, `test_prose_counts.py` 11/11, `test_tree_walks.py` 17/17,
`test_report_hygiene.py` 18/18, `test_bytecode_staleness.py` 22/22.

Żadna zapadka poza trzema podłogami tej pozycji nie drgnęła: nowa bramka nie dokłada ani
jednej asercji kształtu `literał in coś` (stoi na zwrocie czytnika, nie na napisie), nie
dokłada modułu i nie dokłada wpisu do rejestru — wszystkie trzy podłogi tej rodziny
stoją w rejestrze od pozycji, która je wprowadziła. `MIN_REPORTS` podniesione o jeden,
bo ten raport jest nowym plikiem; `ADRESOW_W_WYKONANYCH` i `WYWOLAN_W_WYKONANYCH`
podniesione, bo adnotacja ZROBIONE przenosi blok do populacji bloków wykonanych — cena
zmierzona podstawieniem, nie odejmowaniem.

## 8. Czego świadomie nie zrobiłem

- **Nie poprawiłem zanieczyszczenia z §3.** Nagłówek `serializacja-jobow-ci.md` §7 zostaje
  w pomiarze, a podłogi mają na niego zapas. Poprawka jest zmianą **raportu**, nie kodu,
  i 6.D108 zabrania przepisywania raportów przy okazji.
- **Nie objąłem synonimów** („Znalezione po drodze", „Co wyszło przy okazji") — to wymaga
  listy synonimów, nie rdzenia, czyli innej klasy. Granica jest wypisana przy stałej
  i wykonana w bramce.
- **Nie ruszyłem podłóg 6.D227**, choć slajs im urósł (§6): są podłogami i urosła im
  populacja, więc nie kłamią; podniesienie ich to osobna decyzja o zapasie.
- **Nie tknąłem `reports/6d225-dziura-interpolacji.md`** mimo czerwonego testu — poprawka
  jest w #638 i wciąganie jej tutaj byłoby drugim zadaniem w jednym commicie (§4.10).

## 9. Co zauważyłem przy okazji, ale nie tknąłem

- **Slajs 6.D227 pożycza czytnik sekcji i nikt tego nie napisał** (§6). Zależność wyszła
  z kontroli negatywnej, a nie z lektury — w module nie ma zdania, które by ją nazywało.
  Oznacza to, że **każda** przyszła zmiana `SEKCJA_ZAUWAZONE` rusza również pomiar 6.D227,
  a dziś dowiaduje się o tym wyłącznie ten, kto zrobi kontrolę oślepiającą.
- **Podłogi 6.D216 stały z zapasem zero przez dobę i nikt tego nie zauważył**, bo katalog
  tylko rośnie. Zapas zero jest w tym repozytorium **niewidzialny do pierwszego usunięcia
  pliku**, a usunięcia nie było jeszcze nigdy — czyli cała rodzina takich podłóg jest dziś
  nieprzetestowana w kierunku, dla którego powstała.
- **Rdzeń nie pyta, czy nagłówek jest sekcją.** 3,1 % to dzisiejsza cena, ale nic jej nie
  pilnuje: gdyby ktoś wpisał słowo „zauważ" do dziesięciu nagłówków niebędących sekcjami,
  podłogi urosłyby i czytałoby się to jak wzrost populacji.
