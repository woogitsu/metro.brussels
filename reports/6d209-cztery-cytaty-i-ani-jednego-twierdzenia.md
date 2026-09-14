# 6.D209 — cztery cytaty i ani jedno twierdzenie

**14.09.2026**, na `b941625`. Wejście: `tools/tests/test_report_claims.py` (`CLAIM`,
`constant_values`, `zdanie_z_dnia_pomiaru`), `tools/tests/test_backlog.py`
(`CLAIM_W_JEDNYCH_GRAWISACH`), `reports/*.md`,
`reports/6d196-osiemdziesiat-liczb-polowa-nieprawdziwa.md` §4.

## 1. Trzy liczby, których żądało pole „Wyjście"

| | |
|---|---:|
| wystąpień kształtu `` `NAZWA = N` `` w `reports/` | **51** (13.09 było 41) |
| z nazwą, którą drzewo zna | **45** (13.09 było 35) |
| różnych nazw wśród wystąpień | 42 |
| **rozjechanych z drzewem** | **15** |
| z nich **zwolnionych przez datowanie** (6.D108) | **11** |
| z nich **twardych** — raport nie starszy od stałej | **4** |

Pomiar szedł przyrządem tego modułu (`constant_values`, `zdanie_z_dnia_pomiaru`)
i wzorcem **pożyczonym** z `test_backlog`, a nie przepisanym: dwie kopie tego samego
wyrażenia rozjechałyby się przy pierwszej poprawce.

**Ostrzeżenie z pola „Czego NIE wolno zrobić bez pomiaru" było trafne co do joty:**
35 (dziś 45) to nie jest 35 twierdzeń do sprawdzenia. Odjęcie zgodnych zostawia 15,
a datowanie — 4.

## 2. Wszystkie cztery twarde to CYTATY, nie twierdzenia autora

Widać to dopiero w zdaniu **obok** liczby, nie w samej liczbie:

| miejsce | zdanie | czym jest liczba |
|---|---|---|
| `6d156…:16` | „Odtwarza `NIEROZSTRZYGNIETYCH = 72` dokładnie, więc mierzy to, co bramka" | wartość **wejściowa sondy** z dnia raportu |
| `odsylacz-nie-jest-wartoscia.md:121` | „Czytający miał prawo przeczytać ją jako `MINIMUM_CLAIMS = 15`" | cytat **błędnego odczytu**, opisany jako błędny |
| `rozstep-budzetu-kroku.md:127` | „Przyrząd czytał `KOD_NIEMIERZALNY = 1`, gdy w pliku stało `3`" | odczyt **przyrządu**, który raport zgłasza jako usterkę |
| `sciezki-w-polach-blokow.md:128` | „z zapadką podniesioną razem z wpisem (`MAX_EXCEPTIONS = 2`)" | nastawa **kontroli negatywnej** |

**Trafień prawdziwych: ZERO.**

## 3. Rozstrzygnięcie: `CLAIM` zostaje taki, jaki jest

Poszerzenie wzorca na ten kształt dałoby dziś **4 czerwienie na tekście poprawnym
i 0 na usterce**. Bramka świecąca na poprawnym tekście zostaje wyłączona, nie
poprawiona (6.D27) — więc jej nie ma. Granica jest **zapisana**, razem z liczbami
i z czterema nazwanymi przypadkami, które ją rozstrzygnęły.

Zamiast bramki na kształcie stoi bramka na **werdykcie**, i jej ostateczna postać
wyszła z **dwóch nieudanych**, obu zmierzonych, a nie przewidzianych:

1. **przypięcie zbioru TWARDYCH rozjazdów** (rozjechane minus zwolnione datowaniem)
   rozjechało się z czterech par na trzy **przez commit, który nie tknął ani jednej
   liczby** — `data_stalej` datuje stałą commitem, który ostatnio ruszył jej **plik**,
   więc dopisanie tej bramki do `test_report_claims.py` przedatowało jedną ze stałych
   na dziś i datowanie zaczęło ją zwalniać;
2. **przypięcie zbioru WSZYSTKICH rozjechanych** dało **13 par**, bo rośnie przy każdym
   podniesieniu zapadki po raporcie, który ją cytował — czyli przy pracy poprawnej.

Trwałe jest dopiero zdanie, które ta pozycja rozstrzygnęła:

> każdy rozjazd jest **albo** zwolniony datowaniem, **albo** jednym z czterech cytatów

Nowy rozjazd, którego datowanie nie zwalnia, zapala bramkę; przedatowanie
któregokolwiek z czwórki nie zapala niczego, bo przenosi ją do pierwszego członu.
Lista czterech jest przy tym sprawdzana z drugiej strony: każdy wpis ma **naprawdę**
być dziś rozjechany z drzewem (6.D131 — zbiór, nie liczba).

## 4. Datowanie tych czterech NIE zwalnia — osobne znalezisko

Dla **dwóch** raport i stała mają **ten sam commit** (raport i zapadka weszły razem),
dla **dwóch** raport jest **nowszy** od stałej:

```
6d156…              stała 2026-09-13 01:40:13   raport 2026-09-13 01:40:13
odsylacz…           stała 2026-09-06 00:58:38   raport 2026-09-07 02:50:24
rozstep…            stała 2026-09-07 23:39:01   raport 2026-09-08 10:55:18
sciezki…            stała 2026-09-07 17:34:06   raport 2026-09-07 17:34:06
```

Mechanizm z 6.D108 odsiewa zdania, które **zestarzały się w czasie** — a te nie
zestarzały się wcale. Nigdy nie były zdaniami o stanie drzewa. Datowanie jest więc
sitem na **inne** zjawisko niż to, które zostaje po jego odjęciu, i żadne poszerzenie
datowania tej czwórki nie obejmie.

## 5. Kontrole negatywne

Baza modułu: **13/13**. Po każdej `md5sum -c` na trzech plikach: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | wzorzec kształtu zgnił (`=` → `==`) | 12/13, populacja **51 → 1** |
| KN-2 | jeden cytat skreślony ze zbioru | 12/13 |
| KN-3 | nowe twierdzenie tego kształtu, rozjechane z drzewem, dopisane do raportu | 12/13 |

**KN-3 jest tą kontrolą, o którą prosiło pole „Weryfikacja"** — „twierdzenie tego
kształtu dopisane do raportu **wchodzi** do pomiaru". Wchodzi i zapala: zbiór urósł
do pięciu, a komunikat nazwał plik i stałą.

## 6. Ten raport stał się piątym, szóstym, siódmym i ósmym wystąpieniem

**Zmierzone, nie przewidziane.** Pierwszy pełny przebieg zestawu po dopisaniu tego
raportu dał **2477/2481**, a bramka wypisała osiem par zamiast czterech: cytując cztery
przypadki z sekcji 2, raport **odtworzył ich kształt** i sam wszedł do populacji, którą
mierzy.

Rozwiązaniem nie jest napisanie cytatów inaczej — to byłoby dokładnie to obejście,
które ten projekt nazywa gorszym od usterki (pisać niepoprawnie, żeby bramka milczała).
Rozwiązaniem jest **wyłączenie tego jednego pliku z populacji**, przybite z drugiej
strony: bramka żąda, żeby wyłączony raport **naprawdę cytował wszystkie cztery nazwy**,
więc amnestia nie obejmuje twierdzenia, które ktoś napisałby tu o czymś innym.

Ta sama rodzina, co `_moduly_do_pomiaru` z 6.D203 i samozwrotność podłogi na skan
datowanych deklaracji z 6.D206 — trzeci raz tego samego dnia. Liczba, którą da się
zmienić zdaniem o niej samej, nie jest pomiarem drzewa.

## 7. Kolejka — domknięcie zbiło zapas, a pomiar dał nową pozycję

Domknięcie 6.D209 zszedł zapas **udokumentowany** do **11** przy progu 12 i zapaliło
`test_the_documented_shortfall_is_written_down_while_it_lasts`. `CLAUDE.md` §8 każe
wtedy najpierw uzupełnić kolejkę — **a pozycji wymyślonej na miejscu nie bierze się
nigdy**, więc nowa wyszła z tego pomiaru: **6.D219**, o remisie dat z sekcji 9.
Podłoga na liczbę bloków szczegółów poszła tym samym commitem o jeden w górę — wartości
raport nie podaje, bo zestarzeje się przy następnym domknięciu, a pilnuje jej
`tools/tests/test_backlog.py`.

## 8. Czego świadomie nie zrobiłem

- **Nie poprawiłem ani jednej liczby w raporcie** — raporty są historią (6.D108),
  a wszystkie cztery twarde są zresztą poprawne w swoim zdaniu.
- **Nie ruszyłem zwężenia `CLAIM` o grawis w przerwie** — pole „Poza zakresem" żąda
  przy tym pomiaru fałszywych trafień, a tego zwężenia ta pozycja nie mierzyła.
- **Nie tknąłem pól „Skąd" w `docs/TASKS.md`** (to 6.D196 i 6.D208, oba domknięte).
- **Nie postawiłem bramki na liczbie 51 ani 45** — obie rosną z każdym raportem;
  przypięta jest podłoga.

## 9. Zauważone, nie tknięte

- **Populacja urosła z 41 na 51 w ciągu jednej doby**, i dziesięć nowych wystąpień to
  moje własne raporty z 14.09. Kształt, którego bramka nie widzi, jest więc **kształtem
  żywym i produktywnym**, a nie reliktem — piszę w nim, bo jest wygodniejszy.
- **Sześć wystąpień ma nazwę, której drzewo nie zna** (51 − 45). Nie sprawdzałem, czy
  to stałe skasowane, czy nazwy z cudzych projektów cytowane w prozie; jedno i drugie
  wygląda dla skanu tak samo.
- **`data_stalej` dla dwóch z czterech zwraca tę samą sekundę, co `data_raportu`** —
  bo zapadka i raport weszły jednym commitem. Reguła „raport nie starszy od stałej"
  rozstrzyga wtedy przez `>=`, czyli traktuje remis jako brak zwolnienia. Wpisane jako
  **6.D219**; ilu twierdzeń w katalogu ten remis dotyczy, nie sprawdzałem.
- **`data_stalej` datuje stałą commitem, który ruszył jej PLIK, a nie jej wiersz** —
  zmierzone na sobie: dopisanie tej bramki do `test_report_claims.py` przedatowało
  `MINIMUM_CLAIMS` na dziś, choć wartość stoi nietknięta od 06.09.2026. Każda edycja
  modułu przenosi więc wszystkie jego stałe w przyszłość i **zwalnia** twierdzenia
  raportów, które je cytują. Ta pozycja obeszła to, nie pytając datowania o członkostwo
  (sekcja 3); ile twierdzeń w katalogu jest przez to zwalnianych bez powodu, jest
  pytaniem, którego nie zadałem.
