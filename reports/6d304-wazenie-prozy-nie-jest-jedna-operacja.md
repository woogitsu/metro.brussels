# 6.D304 · Ważenie prozy wierszami NIE JEST jedną operacją — dwie jego realizacje dają PRZECIWNE odpowiedzi

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `d1da62a`

6.D295 zmierzyło, że korpus prozy `tools/tests/` w ponad czterech piątych składa się
z komentarzy, że komentarz ma `do == od` zawsze, a docstring bywa
stuczterdziestowierszowy. Bramki liczą jedno i drugie jako **jeden wpis**. Ta pozycja
pyta, ile bramek jest na to wrażliwych.

Odpowiedź na pytanie zadane wprost brzmi **jedna**. Ale po drodze wyszło, że samo
pytanie ma wadę, której nie widać przed pomiarem — i to jest wynik ważniejszy niż ta
jedynka.

---

## 1. Liczba z pola „Skąd" ZESTARZAŁA SIĘ i przeliczam ją, zamiast przepisać

Blok podaje **14 679** wpisów: 11 836 komentarzy i 2843 docstringi. Zmierzone dziś:

```
wpisow razem        : 14755
  komentarzy        : 11912   (wszystkie do == od: True)
  docstringow       : 2843
  w tym wielowierszowych: 2055
  najdluzszy        : 139 wierszy
suma wag (do-od+1)  : 32129
```

Komentarzy jest o **76** więcej, niż mówi blok; docstringi, wielowierszowe i najdłuższy
zgadzają się co do jednego. Nie jest to usterka czytnika: 6.D295 mierzyło na `bbb630a`,
a między tamtym commitem a dzisiejszym stoi **osiem** domkniętych pozycji, z których
każda dopisała prozę. **Liczba wpisana do bloku zadania starzeje się, bo nikt jej nie
przelicza; liczba stojąca w kodzie nie może.** Wszystkie liczby niżej są dzisiejsze.

## 2. TRZY LICZBY, których żądało pole „Wyjście"

| | liczba |
|---|---|
| bramek wołających `proza` (wprost albo przez czytnik na niej zbudowany) | **18** |
| z nich liczących **WPISY** | **4** |
| z nich liczących **WIERSZE albo TRAFIENIA** | **10** |
| z nich **ani jedno, ani drugie** (istnienie, tożsamość, pusty zbiór) | **4** |
| z liczących wpisy — ile **zmienia werdykt** | **1** |

**Czwarty wiersz stoi tu dlatego, że 4 + 10 ≠ 18.** Pole prosi o podział na dwie klasy,
a populacja ma trzy; podanie samych dwóch liczb udawałoby podział wyczerpujący.

Osiemnastkę policzyłem **dynamicznie**: licznik nałożony na obiekt `proza`
w `sys.modules`, każdy test wołany osobno. Nazwy funkcji **nie zmieniałem** — 6.D297 §3
zmierzyło, że przemianowanie czytnika oślepia bramkę czytającą źródło po nazwie.
Wszystkie 18 wychodzi zielone, a w tych samych czterech modułach 33 dalsze bramki
`proza` nie wołają wcale.

## 3. GŁÓWNE ZNALEZISKO: „ważyć wierszami" znaczy DWIE RÓŻNE RZECZY

Pole pyta, czy werdykt zmieniłby się, „gdyby docstring wielowierszowy ważył tyle
wierszy, ile zajmuje". Zbudowałem **dwie** realizacje tego zdania — obie uczciwe, obie
zgodne z jego brzmieniem:

* **POWIELENIE** — ten sam wpis występuje `do - od + 1` razy. Tekst zostaje w całości.
* **CIĘCIE** — wielowierszowy docstring rozcięty na **jeden wpis na wiersz**, każdy
  z tekstem swojego wiersza. Liczba wpisów rośnie tak samo, ale każde trafienie stoi
  odtąd w dokładnie jednym wpisie.

```
Q                               BEZ  POWIELENIE   CIECIE   kierunek
len(proza)                    14755       32129    32126   ROSNIE / ROSNIE
pogrubione_bez_pokrycia         175        2298      167   ROSNIE / spada
gole_w_prozie_pomiarowej        259         259      118   bez zm. / spada
pozycje_pokrycia['zbieg']        56         266       66   ROSNIE / ROSNIE
wyliczenia_prozy                 10          31        8   ROSNIE / spada
```

```
bramek zbadanych: 45   wszystkie zielone bez wazenia: True
zmienia werdykt pod POWIELENIEM: 6
zmienia werdykt pod CIECIEM    : 8
suma mnogosciowa (unia)        : 9
OBIE realizacje zgodne (przekroj): 5
```

**Trzy z pięciu wielkości ruszają się w PRZECIWNE strony**, a dziewięć bramek jest
ruszanych przez którąś realizację — przy czym obie zgadzają się tylko co do pięciu.
Jedna bramka pada wyłącznie pod powieleniem, trzy wyłącznie pod cięciem:

```
TYLKO powielenie (1):
    test_message_claims::test_zadna_NOWA_pogrubiona_liczba_w_prozie_nie_wchodzi_bez_pokrycia
TYLKO ciecie (3):
    test_message_claims::test_ile_par_CERTYFIKUJE_SIE_NAWZAJEM
    test_message_claims::test_zadna_NOWA_liczba_niepogrubiona_nie_wchodzi_do_prozy_pomiarowej
    test_one_bold_sentences::test_ile_zdan_jest_jedno_zdjecie_od_znikniecia
```

**Powód jest jeden i da się go nazwać: waga wpisu (`do - od + 1`) jest NIEODŁĄCZNA
od tekstu, który ten wpis niesie.** Powielenie zachowuje tekst i przez to mnoży
trafienia — `pogrubione_bez_pokrycia` rośnie trzynastokrotnie, a to nie jest model
ważenia, tylko jego artefakt. Cięcie trafień nie mnoży, ale **niszczy dopasowania
przechodzące przez koniec wiersza** — `gole_w_prozie_pomiarowej` spada z 259 na 118,
czyli **ponad połowa gołych liczb w prozie pomiarowej jest znajdowana wyłącznie dzięki
kontekstowi wielowierszowemu**.

Nie istnieje więc operacja, która zmieniałaby SAMĄ liczbę wpisów. Pytanie pola ma
odpowiedź dopiero razem z wyborem realizacji, a ten wybór odpowiedź **odwraca**.

## 4. Jedyna bramka, którą rusza LICZBA WPISÓW — i rusza pod obiema

`test_prose_counts::test_ile_wyliczen_prozy_jest_ROZKLADEM_a_ile_INNYM_ZWIAZKIEM`,
asercja `(len(wyliczenia), rozkladow, z_suma) == (10, 2, …)`:

```
len(wyliczenia_prozy):  bez = 10   powielenie = 31   ciecie = 8
```

Pada w obu realizacjach i **w przeciwne strony**. `wyliczenia_prozy` składa komentarze
w akapity, a docstringi przepuszcza jeden do jednego — więc rozmnożenie wpisów rozmnaża
wyliczenia, a rozcięcie rozbija te, które wisiały na kilku wierszach.

## 5. Pozostałe trzy bramki klasy WPISY — zmiana „o ZERO", z liczbą przy każdej

Pole żąda zapisania, **o ile** zmieniłby się werdykt, także gdy o zero.

| bramka | Q | bez | powielenie | cięcie | werdykt |
|---|---|---|---|---|---|
| `test_czytnik_prozy_widzi_TRZY_OSOBNE_wezly_a_nie_jeden` | `rodzaje.count(...)` na drzewie próbnym | 2 / 3 | 2 / 3 | 2 / 3 | **o zero** |
| `test_digit_boundaries::test_ile_wzorcow_rozcina_dzis_liczbe_na_zywym_drzewie` | `3·len(proza)` wobec podłogi | 44 265 | 96 387 | 96 378 | **o zero** |
| `test_prose_counts::test_wykluczenie_TASKS_md_jest_SPRAWDZALNE_a_nie_podpisane` | różnica dwóch przebiegów | 7 | 7 | 7 | **o zero** |

Trzy różne powody i warto je rozróżnić, bo tylko jeden jest trwały:

1. **Odporność PRZYPADKOWA.** Pierwsza bramka liczy wpisy wprost; nie rusza się
   wyłącznie dlatego, że oba docstringi jej fixture są **jednowierszowe**, czyli mają
   wagę jeden. Rozciągnięcie któregokolwiek o wiersz uczyniłoby ją wrażliwą. To ten sam
   kształt, który 6.D297 §2 nazwał u siebie: „bezpieczeństwo jest przypadkiem populacji,
   a nie własnością klucza".
2. **Odporność przez ZAPAS.** Druga porównuje wielkość, która rośnie ponaddwukrotnie,
   z podłogą `MIN_TEKSTOW_W_KORPUSIE` równą 800 — zapas wynosi **43 465** i żadna
   realizacja ważenia go nie zjada. Q rusza się ogromnie, werdykt nie może.
3. **Odporność KONSTRUKCYJNA.** Trzecia porównuje **różnicę** dwóch przebiegów tego
   samego czytnika; człon prozy skraca się w odejmowaniu. Obie strony rosną, różnica
   zostaje siedem. Jedyna z trzech, która byłaby odporna na KAŻDE ważenie.

## 6. Kontrola przyrządu, której żądało pole — ZDANA, i to DWUKROTNIE

Pole stawia warunek: *bramka pytająca o SAMO ISTNIENIE wpisu ma wyjść w klasie
„odporna"; jeśli czytnik wrzuci ją do wrażliwych, myli liczenie wpisów z liczeniem
wierszy*.

Bramki o istnienie są dwie — `test_sito_prozy_pomiarowej_NIE_liczy_cyfr_spoza_twierdzenia`
(żąda obecności jednej liczby i nieobecności drugiej) oraz
`test_czytnik_widzi_przypadek_ktory_pozycje_wywolal` (żąda niepustości dwóch zbiorów).
**Żadna nie należy do zbioru zmieniających werdykt — ani pod powieleniem, ani pod
cięciem.** Kontrola przechodzi pod obiema realizacjami, a nie pod jedną wybraną.

## 7. Przewidywania spisane PRZED pomiarem — CZTERY trafione, OSIEM OBALONYCH

Spisałem je w **dwóch turach**: pierwszą przed pomiarem, drugą przed zbudowaniem
wierniejszego przyrządu. Obie stoją w scratchpadzie z czasem zapisu.

**Tura pierwsza:**

| # | przewidywanie | wynik |
|---|---|---|
| P1 | bramek wołających `proza`: 15–45 | trafione (18) |
| P2 | liczących WPISY: przytłaczająca większość, ≥ 80 % | **OBALONE** — 4 z 18, czyli 22 % |
| P3 | zmieniających werdykt wśród liczących wpisy: 0–2 | trafione (1) |
| P4 | czytników zbudowanych na `proza`: 4–8 | **OBALONE** — czternaście |
| P5 | kontrola przyrządu przejdzie | trafione |
| P6 | wrażliwa będzie któraś z dwóch zapadek GÓRNYCH prozy | **OBALONE** — jest nią `test_prose_counts` |

**Tura druga**, spisana zanim uruchomiłem cięcie:

| # | przewidywanie | wynik |
|---|---|---|
| R1 | pod cięciem padnie MNIEJ bramek niż pod powieleniem (< 6) | **OBALONE** — osiem |
| R2 | `pogrubione_bez_pokrycia` pod cięciem: mnożnik 1,00–1,20 | **OBALONE** — 0,954, czyli SPADA |
| R3 | `wyliczenia_prozy` urośnie także pod cięciem | **OBALONE** — spada z dziesięciu na osiem |
| R4 | `gole_w_prozie_pomiarowej` zostanie bez zmian | **OBALONE** — spada na 118 |
| R5 | zmieniających werdykt pod cięciem: 1–3 | **OBALONE** — osiem |
| R6 | o wpływie cięcia na okno pokrycia **nie przewiduję nic** | honorowane |

**Wszystkie pięć obaleń tury drugiej ma jedną przyczynę i nazywam ją zamiast poprawiać
przewidywania:** założyłem, że cięcie jest realizacją ŁAGODNIEJSZĄ, bo nie mnoży
trafień. Nie jest łagodniejsze — jest **inaczej gwałtowne**. Powielenie psuje przez
nadmiar, cięcie przez rozerwanie kontekstu, a liczba zepsutych bramek wychodzi
z cięcia WIĘKSZA. Przewidywałem różnicę stopnia tam, gdzie jest różnica rodzaju.

R6 zapisuję jako honorowane, a nie trafione: **wstrzymanie się nie jest trafieniem**.
Napisałem je dlatego, że nie miałem z czego wyprowadzić kierunku, i tak to liczę.

## 8. Czego świadomie nie zrobiono

- **Nie zmieniono wagi wpisów ani nie rozbito populacji `proza` na dwie** — pole
  „Poza zakresem" zabrania, a §3 pokazuje, że rozbicie wymagałoby najpierw
  rozstrzygnięcia, KTÓRA realizacja ważenia jest tą właściwą. Pozycja miała LICZYĆ.
- **Nie ruszono ani jednej zapadki**, w szczególności żadnej z dwóch górnych prozy —
  te wolno wyłącznie obniżać, a pomiar nie daje powodu do obniżenia.
- **Nie poprawiono liczby w polu „Skąd" bloku 6.D304** — jest pomiarem z datą
  (6.D295, `bbb630a`) i była prawdziwa, gdy powstawała. Dzisiejszą podaję w §1.
- **Nie postawiono bramki** na żadnej z liczb tej pozycji.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 9. Zauważone przy okazji, nietknięte

1. **Dwa czytniki „pożyczone" wobec siebie różnią się tym, czy odsiewają duplikaty —
   i nie pilnuje tego nic.** `gole_w_prozie_pomiarowej` trzyma zbiór `widziane`
   z kluczem niosącym przesunięcie, więc pod powieleniem daje 259 wobec 259; sąsiedni
   `pogrubione_bez_pokrycia` żadnego odsiewu nie ma i pod tym samym powieleniem rośnie
   z 175 na 2298. 6.D213 zapisało, że te czytniki są wobec siebie pożyczone co do okna,
   skal i wzorca — klucz tożsamości nie był wtedy porównywany.
2. **Obie zapadki górne prozy stoją DOKŁADNIE na swojej wartości.** Dziś
   `len(pogrubione_bez_pokrycia())` równa się `MAX_POGRUBIONYCH_BEZ_POKRYCIA` = 175,
   a `len(gole_w_prozie_pomiarowej())` równa się `MAX_GOLYCH_W_PROZIE_POMIAROWEJ` = 259.
   Zapas wynosi zero po obu stronach; następny dopisany akapit prozy zapala którąś z nich
   w cudzym pull requeście.
3. **Ponad połowa gołych liczb w prozie pomiarowej wisi na kontekście wielowierszowym**
   (259 → 118 pod cięciem). Ile z nich to zdania rozbite przez zawijanie wiersza, a ile
   naprawdę wielowierszowe wyliczenia, ta pozycja nie pyta.
