# 6.D227 — zakres nazwany szerzej niż zmierzony: 35 zdań i sito, które NIE orzeka o prawdziwości

**16.09.2026**, na `d0a97ae`. Wejście: `reports/*.md` (sekcje „zauważone"),
`tools/tests/test_report_claims.py` (`sekcje_zauwazone`, `punkty_sekcji`, 6.D216),
`reports/6d210-podzial-sie-rozszedl-w-jedna-dobe.md` §9, `src/Sim/Train/DriverKeys.cs`.
Wyjście: dwa czytniki (`twierdzenia_o_zakresie`, `slajs_szeroki`), dwie podłogi,
trzy bramki w `tools/tests/test_report_claims.py`, dwa wpisy w rejestrze zapadek,
ten raport.

---

## 1. Liczba, o którą pozycja pytała

| slajs | definicja | pozycji |
|---|---|---|
| **wąski** | zakres w grawisach **i** orzeczenie uniwersalne/negatywne w oknie **60 znaków** | **35** |
| **szeroki** | zakres w grawisach **i** orzeczenie gdziekolwiek w tym samym punkcie | **64** |

Slajs jest **ZDEFINIOWANY, a nie dobrany** — o to pozycja prosiła wprost. Definicja
stoi w trzech stałych obok siebie: `ORZECZENIA_ZAKRESU` (18 orzeczeń),
`OKNO_ZAKRESU` (60 znaków), `ZAKRES_W_GRAWISACH` (nazwa z ukośnikiem w grawisach).

**Każda z trzech jest WYBOREM i każda ma obok siebie zmierzoną cenę:**

- **okno:** przy 60 → 35 pozycji, przy 20 → **17**, czyli mniej niż połowa;
- **wzorzec:** obejmujący wyłącznie katalogi (kończące się ukośnikiem) → **14**,
  czyli zawężenie do katalogów odcina **dwie trzecie** slajsu;
- **plik liczony razem z katalogiem:** wybór, nie przeoczenie — zdanie
  „w `src/Sim/Line/LineCore.cs` nie ma ani jednego" nazywa zakres tak samo jak
  zdanie o katalogu, a klasa bierze się z tego, że NAZWANY zakres jest szerszy
  od ZMIERZONEGO, bez względu na to, czy nazwą jest plik, czy katalog.

## 2. Rozstrzygnięcie o sicie — „nie da się" dotyczy PRAWDZIWOŚCI, nie kształtu

Pozycja dopuszczała odpowiedź „sita nie da się napisać i oto dlaczego" jako wynik
równie dobry. Odpowiedź jest **rozdzielona na dwie połowy** i to jest cała treść
tej pozycji:

**Sita PRAWDZIWOŚCI postawić się nie da** — 6.D216 zmierzyło to trzema powodami,
a 6.D227 sprawdziło jeszcze raz i znalazło **trzy przypadki tekstu POPRAWNEGO**,
na których takie sito by się zapaliło:

| raport | zdanie | dlaczego jest POPRAWNE |
|---|---|---|
| `6d197` | „domyślnych PO WYLICZENIU jest w `src/Sim/` zero" | prawdziwe i zawężone — kształt identyczny z przypadkiem założycielskim |
| `6d209` | „wystąpień … 51" (dziś 55) | poprawne w swoim dniu, 6.D108 zabrania przepisywania |
| `6d185` | „`KcvFunction` w `src/Game/` nie pada ani razu" | bez kotwicy, a prawdziwe |

**Sito KSZTAŁTU postawić się DA i zostało postawione.** Liczy, w ilu punktach zakres
nazwany stoi obok orzeczenia uniwersalnego — i nie mówi ani słowa o tym, czy zdanie
jest prawdziwe. Pilnuje tego osobna bramka na wejściu syntetycznym
(`test_czytnik_zakresu_liczy_KSZTALT_a_nie_prawdziwosc`): zdanie **zawężone**
(„w switchach po wyliczeniu w `src/Sim/` dziś nie ma") ma wejść do pomiaru tak samo
jak niezawężone. Bez tej asercji następny czytający wziąłby tę bramkę za sito
prawdziwości — a nią nie jest i być nie może.

## 3. Dlaczego bramka w ogóle istnieje — zmierzone podstawieniem

Slajsu, o który ta klasa pyta, **nie liczyło dotąd NIC**. Zmierzone: trzy mutacje
w trzech różnych raportach, w tym jedna zamieniająca zdanie prawdziwe w fałszywe,
dały `2493/2493 przeszło` i kod 0. Podłogi 6.D216 nie drgnęły, bo liczą **sekcje**
i **punkty z cyfrą**, a żadna z tych mutacji nie zmienia ani jednego, ani drugiego.

## 4. Granica, wypisana zamiast zostawiona do odkrycia

Zakres nazwany **słowem**, bez grawisów i bez ukośnika („w całym rdzeniu symulacji
nie ma ani jednego"), jest dla czytnika **niewidzialny**. Nie jest to usterka do
naprawienia przy okazji: poszerzenie na prozę wymagałoby rozpoznawania nazw
katalogów po znaczeniu, a nie po kształcie, i zapalałoby się na zdaniach
o czymkolwiek — czyli byłoby 6.D27. Granica ma osobną bramkę
(`test_czytnik_zakresu_MILCZY_na_zakresie_nazwanym_SLOWEM_i_to_jest_zapisane`),
a ta bramka niesie **drugą asercję w przeciwną stronę** — bo inaczej byłaby zielona
nad czytnikiem ślepym na wszystko.

## 5. Dlaczego podłogi, a nie równości, i dlaczego DWIE

**Podłogi**, bo raportów przybywa, a przepisywać ich nie wolno (6.D108) — równość
zapalałaby się na każdym nowym poprawnym raporcie (6.D27). Zero znaczyłoby
„czytnik oślepł", a nie „nie ma takich zdań", i dlatego podłoga w ogóle stoi.

**Dwie**, bo zwężenie **WZORCA** i zwężenie **OKNA** zapalają różne asercje:
bez pary nie dałoby się ich odróżnić. Trzecia asercja pilnuje, że wąski pozostaje
zawężeniem szerokiego.

## 6. Pięć przypadków klasy, przejrzanych ręcznie

Poza przypadkiem założycielskim (6.D210 §9: „ramion `when` w `src/Sim/` dziś nie ma",
a są cztery w `src/Sim/Train/DriverKeys.cs:143,146,149,152` od `877ab66`
z 05.09.2026 — **dziewięć dni przed** tamtym zdaniem):

- `6d191` — „nigdy nie trafia w to samo" przy populacji **dwóch** przebiegów;
- `6d201` — „wszystkie 42 … sprawdzone na próbce **pięciu pierwszych**";
- `podloga-sciezek-na-raport` — „22 wzmianki … wszystkie pod `.github/`", a wzmianek
  o `tools/ci/*` jest dziś **65** w **27** raportach;
- `ramka-w-sciezce` — „poza `reports/` i `docs/` nie ma ani jednej", a pomiar objął
  **pięć** miejsc przy **ośmiu** katalogach najwyższego poziomu.

Przegląd ręczny szedł po slajsie zawężonym do samych katalogów (14 pozycji):
pięć pewnych i jeden graniczny.

## 7. Weryfikacja — rzeczywiste wyjście

```
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2504/2504 przeszło
  RAZEM 215.305 s, 2504 testów, 127 modułów
```

### Kontrole negatywne — przewidywania wypisane PRZED przebiegiem

**KN-A** — zawężenie `ZAKRES_W_GRAWISACH` do samych katalogów.
*Przewidywanie: wąski spada 35 → 14, poniżej podłogi; moduł czerwony, **19/20**.*

```
  FAIL test_slajs_zakresu_jest_LICZONY_a_nie_odtwarzany_z_prozy: slajs wąski ma 14
       pozycji przy podłodze 35 — czytnik przestał widzieć zakresy albo orzeczenia,
       a pusty slajs czyta się jak „nie ma takich zdań”
  19/20 przeszło
```
**Potwierdzone co do liczby.**

**KN-B** — zdjęcie wpisu `MIN_SLAJS_SZEROKI` z rejestru zapadek.
*Przewidywanie: DWA `FAIL` — rejestr zapadek i proza o rejestrze (57 wobec 56).*

```
  FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem: zapadka spoza listy:
       [('MIN_SLAJS_SZEROKI', 'wolna')] — dopisz ją razem z klasą w tym samym commicie
  FAIL test_zdanie_o_rejestrze_zapadek_zgadza_sie_z_rejestrem: proza mówi o 57
       zapadkach, a rejestr ma 56
  26/28 przeszło
```
**Potwierdzone co do obu.**

Po każdej kontroli plik przywrócony **z kopii sprzed mutacji**, nie przez
`git checkout --`, i sprawdzony:
```
tools/tests/test_report_claims.py: OK
tools/tests/test_tree_walks.py: OK
```

## 8. Zauważone, nietknięte

- Rejestr zapadek urósł do **57** (17/3/36/1). Wolnych jest już **36** z 57, czyli
  niemal dwie trzecie — i ta proporcja rośnie przy każdej pozycji tej rodziny, bo
  podłoga na czytnik prozy z zasady nie da się przybić. Nie jest to usterka, ale
  liczba warta pilnowania: rejestr, w którym wolne są regułą, mówi mniej niż rejestr,
  w którym są wyjątkiem.
- Trzy przypadki z sekcji 2 (`6d197`, `6d209`, `6d185`) stoją w slajsie i **stać
  w nim mają** — sito liczy kształt. Ktoś, kto zechce z tego slajsu zrobić listę
  usterek do poprawienia, złamie 6.D108 na wszystkich trzech.
