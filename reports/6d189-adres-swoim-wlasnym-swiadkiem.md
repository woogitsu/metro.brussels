# 6.D189 — adres jest swoim własnym świadkiem, więc reguły „zły, choć istnieje" dla pola ze ścieżką postawić się nie da

**13.09.2026**, na `c923b5e`. Wejście: `tools/tests/test_field_paths.py`
(`kandydaci_pola_w_wykonanych`, `MODULE_CALL`, `PATH_TOKEN`),
`reports/6d158-jedna-trzynasta-adresow.md` §3, `reports/6d157-zly-adres-trzy-razy.md` §3.

## 1. Czego pozycja żądała

Rozstrzygnięcia, czy dla pola niosącego **ścieżkę** (a nie polecenie) da się postawić
regułę „zły, choć istnieje" **bez czytania treści modułu** — z precyzją zmierzoną
na drzewie, a jeśli się nie da, to z zapisaną granicą.

## 2. Ground truth: dwa pozytywy, oba w „Wejściu", oba JUŻ POPRAWIONE

6.D157 wymienia sześć złych adresów; do klasy „ma ukośnik, ale plik ISTNIEJE" należą
**dwa**, i oba stały w polu **„Wejście"**:

| blok | zły adres | co było naprawdę |
|---|---|---|
| 6.D73 | `tools/tests/test_backlog.py` | skan przeprowadził się do `test_field_paths.py` przy 6.D32 |
| 6.D74 | `tools/tests/test_scan_gates.py` | ten plik testuje skan luzu, nie przejścia po drzewie |

**Obydwa poprawiono**, więc dzisiejsze drzewo ma w tych polach **zero pozytywów**.
Precyzja liczona na nim wynosi `0/N` **z konstrukcji** — nie dlatego, że reguła jest
zła, tylko dlatego, że nie ma czego trafić. Jedynym sprawdzianem zostaje **kontrola
dodatnia na tekście odtworzonym sprzed poprawki**; ta sama droga, co przy 6.D187.

## 3. Forma A — reguła W POSTACI, W JAKIEJ STOI — jest STRUKTURALNIE pusta

`kandydaci_zlego_adresu` porównuje nazwę z **prozą bloku**. Dla „Weryfikacji" ma to
sens: nazwa stoi tam w **płotku**, a `proza_bloku` płotki wycina, więc porównywane są
dwie różne rzeczy. W polu niosącym ścieżkę **adres stoi w samej prozie** — jest więc
swoim własnym świadkiem.

| pole | różnych adresów | kandydatów formy A |
|---|---:|---:|
| „Wejście" | **894** | **0** |
| „Wyjście" | **63** | **0** |

Zero na 957 adresach nie jest ostrożnością — jest **własnością konstrukcji**.

## 4. Forma B — jedyna nasuwająca się poprawka — zgłasza WIĘKSZOŚĆ korpusu

Zdjęcie pola z prozy naprawia tautologię i natychmiast daje regułę, która zgłasza:

| pole | różnych adresów | kandydatów formy B | udział |
|---|---:|---:|---:|
| „Wejście" | 894 | **570** | **64 %** |
| „Wyjście" | 63 | **23** | 37 % |

Na drzewie z zerem pozytywów daje to precyzję **0 / 570**.

## 5. Kontrola dodatnia: forma A łapie 0 z 2, forma B — 1 z 2

Na tekście odtworzonym sprzed poprawki:

```
6.D73  forma A: 0 zgłoszeń, zły adres złapany = False
6.D73  forma B: 2 zgłoszenia, zły adres złapany = True
6.D74  forma A: 0 zgłoszeń, zły adres złapany = False
6.D74  forma B: 0 zgłoszeń, zły adres złapany = False
```

**Dlaczego forma B nie łapie 6.D74, jest ważniejsze niż to, że nie łapie.** Blok niesie
**drugą** adnotację poprawki — w polu „Weryfikacja" — i ta adnotacja **cytuje ten sam
zły adres**. Nazwa stoi więc w prozie, wstawiona tam przez **zapis naprawy**.

Jest to ten sam wzorzec, co przy 6.D187, tylko **odwrócony**: tam adnotacja o poprawce
kazała regule **zapalić się** na zapisie naprawy; tu każe jej **zamilknąć** na adresie.
Wspólna przyczyna: **adnotacja jest prozą o złym adresie, a każda reguła czytająca
prozę się o nią potyka.**

## 6. ROZSTRZYGNIĘCIE: nie da się, i oto granica

Dla pola niosącego ścieżkę reguły „zły, choć istnieje" **postawić się nie da bez
czytania treści modułu**:

- **forma A** nie zgłasza nigdy — adres jest swoim własnym świadkiem;
- **forma B** zgłasza 64 % korpusu i **mimo to gubi połowę znanych pozytywów**;
- reguła rozstrzygająca musiałaby porównać adres z **tym, co nazywa** — czyli
  przeczytać moduł, co wyklucza pole „Poza zakresem" tej pozycji i 6.D101.

Granica jest zapisana tak samo, jak 6.D146 zapisało granicę reguły semantycznej
(dziesięciu kandydatów, zero złych adresów) — jako **zmierzona**, nie jako obawa.

## 7. Sześć kontroli negatywnych, baza 40/40

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | forma A policzona jak forma B | 39/40 |
| KN-2 | odtworzenie „sprzed" zastąpione tekstem dzisiejszym | 39/40 — **za drugim podejściem** |
| KN-3 | liczba trafień formy B przybita o jeden za wysoko | 39/40 |
| KN-4 | druga adnotacja 6.D74 przestaje cytować zły adres | **37/40** |
| KN-5 | asercja o większości odwrócona na mniejszość | 39/40 |
| KN-6 | skan kandydatów oślepiony (zero iteracji) | 39/40 |

### KN-2 wyszła zielona, bo strażnik podstawienia sprawdzał za mało

Pierwsza wersja żądała tylko, żeby zły adres **stał** w odtworzonym tekście. Dzisiejsze
pole 6.D73 też go niesie — **w adnotacji poprawki** — więc podstawienie
`sprzed = pole_dzis` przechodziło i cała bramka mierzyła tekst **dzisiejszy** pod nazwą
„sprzed". Naprawa: odtworzenie musi się od dzisiejszego **różnić** i nie może nieść
adnotacji, której przed poprawką być nie mogło.

**Trzeci raz w tej sesji ta sama adnotacja przewraca pomiar** — przy 6.D187 zapalała
poszerzony wzorzec, w §5 wyżej ucisza formę B, a tutaj uwiarygodniała fałszywe
odtworzenie. Za każdym razem z tego samego powodu.

## 8. Czego świadomie nie zrobiłem

- **Żadnej z dwóch form nie postawiłem jako bramki na drzewo** — to jest właśnie
  rozstrzygnięcie pozycji. W kodzie stoją jako **pomiar**: liczby i kontrola dodatnia.
- **Adresów nie poprawiałem** i bramki istnienia nie tknąłem — pole „Poza zakresem".
- **Treści modułów nie czytałem**, żeby rozstrzygnąć pojedyncze przypadki — to samo pole.

## 9. Zauważone po drodze, nie tknięte

- Liczby 570 i 23 rosną z każdą domkniętą pozycją, więc stoją w **komunikacie**, a nie
  w zapadce; asercja pyta o **proporcję** („reguła zgłasza większość"), bo to ona jest
  treścią pomiaru i nie zmienia się od dopisania bloku. Dwie wolne zapadki mniej.
- `proza_bloku` wycina wyłącznie płotki. To wystarcza „Weryfikacji" i nie wystarcza
  niczemu innemu — każde pole, którego treścią jest adres, będzie miało ten sam
  problem, jeśli ktoś kiedyś zechce je regułą objąć.
