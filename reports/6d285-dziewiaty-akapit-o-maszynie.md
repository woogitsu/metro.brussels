# 6.D285 · Dziewiąty akapit o maszynie — i dlaczego było ich osiem

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `df90983`

## 1. O co pytała pozycja

6.D169 przeczytało `docs/23-environment.md` ręką, wypisało zdania o konkretnej
maszynie z werdyktem przy każdym i dopisało datę temu, któremu jej brakowało.
Od tamtej pory pilnował tego **wyłącznie ten jeden pomiar**: następny taki akapit,
dopisany jutro, nie zapaliłby niczego. Pozycja żądała bramki na PRZYPIĘTYM ZBIORZE
— nie na kształcie zdania, bo bramkę na kształcie 6.D169 odrzuciło z powodem,
który zostaje (zapalałaby się na prozie poprawnej).

## 2. Jak liczone

Akapit sklejany w **jeden napis** i dopiero wtedy przeszukiwany. To jest treść,
a nie wygoda: `grep` dopasowuje w obrębie wiersza, więc sformułowanie rozcięte
przez zawijanie jest dla niego niewidoczne — 6.D169 zmierzyło to na tym samym
dokumencie. Kluczem wpisu jest **pierwsze zdanie akapitu**, nie numer wiersza:
ten sam akapit raport 6.D169 podaje raz jako 473, raz jako 474, a przy pisaniu
tej pozycji numery przesunęły się jeszcze dwa razy.

Wzorce `DATA` i `GRANICA_ZDANIA` są **pożyczone** z `tools/tests/test_message_claims.py`,
a nie napisane drugi raz — własny literał daty z granicą przy cyfrze wpadłby do
przybitego zbioru `GRANICE_PRZY_CYFRZE`.

## 3. Wynik — osiem było własnością WZORCA, nie dokumentu

Wzorzec 6.D169 brzmiał `tej maszynie|tym kontenerze|czystej maszynie` i dlatego
jego tabela ma osiem wierszy. Ten sam dokument czytany razem z formą „u mnie"
daje **dziewięć** akapitów. Dziewiąty to ten o rozjeździe „u mnie ok, w CI
czerwono" — mówi o maszynie czytającego, więc należy do klasy DOWOLNA, ale
do populacji wchodzi.

| klasa | ile | co znaczy |
|---|---|---|
| KONKRETNA | siedem | maszyna, na której ktoś coś zmierzył; ma nieść datę |
| DOWOLNA | dwa | maszyna czytającego albo dowolna czysta; daty nie potrzebuje |

Akapitów o **konkretnej** maszynie **bez daty** jest zero — teza 6.D169 zostaje
prawdziwa. Nieprawdziwa jest jego liczba, i to jest główny wynik tej pozycji.

**Zbiór nie został zawężony do wzorca 6.D169 po to, żeby zgodzić się z ósemką.**
Pole „Skończone, gdy" żądało ośmiu wpisów; wpisów jest dziewięć, bo tyle akapitów
mówi o maszynie. Dopasowanie zbioru do liczby byłoby dokładnie tym, czego ta
pozycja zabrania.

## 4. Sito węższe o jedną formę — i powód wzięty z tekstu

Pierwsza wersja sita miała też formę „u siebie". Złapała akapit mówiący, że
„żaden workflow nie wpisuje numeru **u siebie**" — a tam „u siebie" znaczy
„we własnym pliku", nie „na własnej maszynie". Forma została zdjęta **po
obejrzeniu trafienia**, z powodu wziętego z tekstu. Gdyby trafienie było
prawdziwe, akapit stanąłby w zbiorze zamiast zostać odsiany.

Zapisuję to jawnie, bo z zewnątrz wygląda identycznie jak zawężenie sita pod
wynik: jedyną różnicą jest powód, więc powód musi stać w raporcie.

## 5. Przewidywania wobec pomiaru

| co | przewidziane | zmierzone |
|---|---|---|
| akapitów złapanych przez sito | dwanaście | **dziewięć** |
| z tego bez daty | zero | **dwa** |
| akapit o maszynie dowolnej złapany przez sito | tak | **tak** |
| wpisów w zbiorze przypiętym | osiem | **dziewięć** |

Dwa pierwsze nietrafione. Trzeci trafiony. Czwarty rozjechał się z polem
„Skończone, gdy" samej pozycji, a nie tylko z moim przewidywaniem.

## 6. Kontrole negatywne

Na **kompletnej kopii drzewa** z `.git`; mutowany jest dokument na kopii, drzewo
robocze w tym czasie **6/6**.

| KN | mutacja | przewidziane | zmierzone |
|---|---|---|---|
| KN-1 | akapit o tej maszynie **bez** daty | czerwień, komunikat nazywa akapit | **4/6**, nazywa go kluczem i wierszem |
| KN-2 | ten sam akapit **z** datą | zieleń | **5/6 — CZERWIEŃ** |
| KN-3 | akapit z przypiętej listy skasowany | czerwień | **5/6**, „wpis bez akapitu" |
| KN-4 | akapit dopisany **powyżej** listy | zieleń | **6/6** |

**KN-2 obaliła moje przewidywanie i jest to wynik, nie usterka.** Spodziewałem
się zieleni, bo akapit niósł datę. Bramka zapaliła się mimo to — na teście zbioru,
nie na teście daty. Tak ma być: zbiór jest porównywany w obie strony, więc **każdy**
nowy akapit o maszynie wymaga ludzkiej decyzji o klasie, a nie samej daty. Data
wystarczyłaby, gdyby klasę dało się orzec maszynowo — a właśnie tego 6.D169
zabroniło, odrzucając bramkę na kształcie.

KN-4 jest kontrolą całego pomysłu pozycji: numery wierszy przesunęły się, klucze
nie drgnęły, zestaw został zielony.

## 7. Czego świadomie nie zrobiłem

- **Nie dopisałem i nie skasowałem ani jednego zdania w `docs/23-environment.md`** —
  pole „Poza zakresem".
- **Nie zszyłem zawijania w wierszach 85–86** — to 6.D286.
- **Nie rozszerzyłem bramki na inne pliki `docs/`** — to 6.D287.
- **Nie użyłem ani jednej pogrubionej liczby w nowej prozie.** Zapadka
  `MAX_POGRUBIONYCH_BEZ_POKRYCIA` stoi dokładnie na swojej wartości, tak samo
  `MAX_GOLYCH_W_PROZIE_POMIAROWEJ`; obie wolno tylko obniżać. Liczby w tym
  module stoją więc słownie albo w stałych.

## 8. Bramka z 6.D284 zapaliła się na MOIM WŁASNYM commicie, godzinę po postawieniu

Chronologicznie najciekawsza rzecz tej pozycji i nie była zaplanowana.

Podniesienie censusu modułów wymaga ogniwa łańcucha przy stałej. Napisałem je
w formie dwuwierszowej, pod wpisem słownika — czyli **dopisałem jeden wiersz**
w środku pliku `test_bytecode_staleness.py`. Pełny zestaw odpowiedział czterema
czerwieniami, z których dwie mówiły dokładnie to, co 6.D284 przewidziało jako
klasę zdarzeń:

```
FAIL test_ile_pokrycia_WISI_NA_WLOSKU: dalej niz polowa okna 22, na skraju okna 2,
a pomiar 19.09.2026 dal 22 i 1. Kruche dzis: [('test_bytecode_staleness.py', '136'),
('test_message_claims.py', '12')]
FAIL test_ile_pokrycia_daje_INNA_PROZA_a_ile_KOD: klasy pokrycia zbiegiem:
{'kod': 11, 'proza': 43, 'mieszane': 2}, a pomiar 18.09.2026 dal proza 43, kod 12,
mieszane 1
```

Jeden wiersz mojego komentarza wypchnął pokrycie cudzej liczby poza okno i przesunął
inną z klasy KOD do MIESZANEJ. To jest ten sam kształt, który złapał autora 6.D278
i 6.D280 — z tą różnicą, że tym razem **bramka nazwała wpis po adresie**, bo 6.D284
dołożyło `KRUCHE_ADRESY` właśnie po to.

**Wybrałem formę komentarza bez dopisanego wiersza**, a nie przepięcie trzech cudzych
stałych. Powód: fragilność była już zmierzona i przypięta wczoraj, a przepinanie
`POKRYCIE_NA_SKRAJU_OKNA`, `POKRYTYCH_WYLACZNIE_KODEM` i `POKRYTYCH_MIESZANIE` przy
pozycji, która ich nie dotyczy, byłoby churnem bez treści. Ogniwo łańcucha stoi więc
w tym samym wierszu co wpis słownika — konwencja, którą ten wpis już nosił.

Gdyby ogniwa nie dało się zmieścić bez dopisania wiersza, przepiąłbym stałe i zapisał
powód. Tu dało się, i to jest jedyna różnica.

## 9. Co zauważyłem, a czego nie tknąłem

- Sito po formach językowych jest z natury niepełne: dziewiąty akapit znalazł się
  dlatego, że dołożyłem jedną formę, a dziesiąty znalazłby się przy następnej.
  Bramka broni przed **nowym akapitem w formie już znanej**, nie przed nową formą.
  To ograniczenie jest własnością konstrukcji, nie usterką — ale nikt go nie mierzy.
- `tools/tests/test_environment_doc.py` czyta ten sam dokument i pilnuje ścieżek
  narzędzi. Dwie bramki na jednym pliku to nie dubel: tamta mówi o katalogach,
  ta o datach.

## 10. Weryfikacja

```
$ python3 tools/tests/test_all.py test_machine_paragraphs.py
  ok   test_akapit_SPOZA_zbioru_zapala_i_komunikat_go_NAZYWA
  ok   test_akapit_o_maszynie_DOWOLNEJ_i_akapit_z_DATA_nie_zapalaja_daty
  ok   test_czytnik_widzi_caly_dokument_a_nie_jego_resztke
  ok   test_kazdy_akapit_o_KONKRETNEJ_maszynie_niesie_date
  ok   test_klucz_PRZEZYWA_przesuniecie_numerow_wierszy
  ok   test_zbior_przypiety_zgadza_sie_z_dokumentem_W_OBIE_STRONY

  6/6 przeszło
       0.008 s  test_machine_paragraphs.py  (6 testów)

$ python3 tools/tests/test_all.py
  2662/2662 przeszło
  RAZEM 335.289 s, 2662 testów, 139 modułów
EXIT=0
```

Przed tą pozycją zestaw liczył 2656 testów w 138 modułach.
