# 6.D342 · Pary nieodnotowane są DWIE, a nie jedna — i obie z tego samego przebiegu; a z pięciu stałych trzy pary nie mają z czego mieć

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `47e5032`

**POMIAR POWTÓRZONY PRZED COMMITEM.** Przyrząd tej pozycji został zachowany, więc uruchomiłem go ponownie na bazie `9e8c33a`. Wynik odtwarza się co do jedynki: **12** stałych zmiennoprzecinkowych, **10** wskazujących konkretny przebieg, **5** progów odsianych, populacja **5**, podział klas **2 / 0 / 0 / 3**, ta sama lista imienna z tymi samymi parami, i kontrola przyrządu na wartości 517,499 przechodzi. Daty pomiaru NIE przepisuję na dzisiejszą — liczby zmierzono 21.09.2026 na bazie `47e5032`.

6.D332 §6 zapisało, że commit `7cfabea` ma dwie próby o ilorazie **2,166**, a drzewo
zapisuje tylko wyższą z nich. Ta pozycja **liczy i wypisuje imiennie**; niczego nie
dopisuje, bo para zmienia wymowę zapisu, a nie tylko go uzupełnia.

---

## 1. Trzy usterki przyrządu, wszystkie złapane przez kontrolę

Wersja pierwsza dała **osiem** stałych i **zero** par, a kontrola przyrządu nie
znalazła w populacji nawet stałej, o którą pole pytało. Trzy przyczyny:

1. **Komentarz `#:` brany tylko bezpośrednio nad stałą.** W drzewie dwie stałe
   dzielą jeden blok komentarza — druga z nich nie ma nad sobą ani jednego `#`
   i przez to w ogóle nie weszła do populacji. Poprawka: komentarz nad **blokiem**
   kolejnych stałych.
2. **Szukanie wartości tylko w `cpu_s`, `wall_s` i `cpu_na_sciane`.** Artefakt ma
   czwarte pole, `wall_powloki_s`, i jedna z dwóch szukanych liczb stoi właśnie tam.
3. **Brak odsiewania PROGÓW**, choć pole żądało tego wprost. Odsiewam je
   miarą, nie nazwą: **próg to stała, wobec której cokolwiek się w tym module
   porównuje** (`<`, `>`, `<=`, `>=`). Pięć z dziesięciu wskazujących przebieg jest
   progami.

Po poprawkach kontrola przechodzi:

```
=== KONTROLA PRZYRZADU (wartosc 517.499) ===
   INCYDENT_DOCKER_CPU  klasa=MA PARE, drzewo JEJ NIE ODNOTOWUJE  para=238.900
```

## 2. Trzy liczby, których żądało pole

```
stalych zmiennoprzecinkowych w obu modulach: 12
z nich WSKAZUJACYCH konkretny przebieg:      10
z nich PROGOW (odsiane):                      5
POPULACJA:                                    5

   MA PARE, drzewo JEJ NIE ODNOTOWUJE        2
   MA PARE, drzewo JA ODNOTOWUJE             0
   BEZ PARY (jedna proba)                    0
   NIE MA W ARTEFAKTACH                      3
   SUMA                                      5
```

**Par nieodnotowanych są DWIE**, a odnotowanych — **zero**. Przewidywanie W4
(„co najmniej dwie") trafione, więc warunek obalenia się nie uruchamia:
**wypadek z 6.D332 §6 nie jest odosobniony.** Ale nie jest też wzorcem: obie pary
pochodzą z **jednego i tego samego przebiegu** — tego z incydentu na kontenerze.

```
   stala                                 wartosc klasa                                para
   INCYDENT_DOCKER_CPU                   517.499 MA PARE, drzewo JEJ NIE ODNOTOWUJE   238.900
   INCYDENT_DOCKER_SCIANA                521.900 MA PARE, drzewo JEJ NIE ODNOTOWUJE   154.160
   KONTENER_11_09_CPU                    169.185 NIE MA W ARTEFAKTACH
   KONTENER_11_09_SCIANA                 170.685 NIE MA W ARTEFAKTACH
   NIEMIERZALNY_ROZSTEP                  115.900 NIE MA W ARTEFAKTACH
```

Druga para jest mocniejsza od pierwszej: **ściana tego samego commita różni się
3,4-krotnie** — 521,900 s wobec 154,160 s — czyli jeszcze ostrzej niż iloraz 2,166,
który 6.D332 policzyło na CPU.

## 3. GŁÓWNE ZNALEZISKO: trzy z pięciu nie mają pary Z CZEGO mieć

Klasa „nie ma w artefaktach" wygląda na brak danych, a nie jest nim. Przeczytałem
wszystkie trzy i **każda jest nieobecna z własnego, dobrego powodu**:

* **Dwie z nich nigdy nie były przebiegiem CI.** Komentarz nad nimi mówi wprost:
  „Pomiar kontenera z 11.09.2026 … `resource.getrusage(RUSAGE_CHILDREN)` wokół
  `subprocess.run` na zestawie, drzewo `9549df6`". To pomiar **lokalny**, zrobiony
  ręką, nie job. Artefaktu nie ma, bo go nigdy nie było — a nie dlatego, że wygasł.
* **Jedna nie jest czasem.** Wartość 115,900 to **rozstęp w procentach**, a nie
  sekundy; szukanie jej wśród pól czasowych artefaktu jest pomyłką kategorii, którą
  mój przyrząd popełnił, bo dopasowywał samą liczbę. Zapisuję to jako czwartą
  usterkę, znalezioną dopiero przy czytaniu wyniku.

**Sprawdziłem, jak blisko trafiają najbliższe artefakty**, żeby nie podawać
nieobecności jako domysłu:

```
169.185 -> najblizej 169.359 (wall_s, 18.09, inny commit)   roznica 0.174
170.685 -> najblizej 170.456 (cpu_s, 11.09, inny commit)    roznica 0.229
115.900 -> najblizej 115.660 (wall_s, 12.09, inny commit)   roznica 0.240
```

Żadne nie jest trafieniem — najbliższe leżą o 0,17–0,24 s obok i na **innych
commitach**. Zbieżność rzędu dziesiątych sekundy przy medianie rzędu 150 s to
przypadek, a nie para, i mówię to zamiast zaliczyć je jako „prawie".

**Prawdziwa odpowiedź na pytanie pola brzmi więc: par nieodnotowanych są dwie
z dwóch możliwych.** Pozostałe trzy stałe nie mogą mieć pary w artefaktach, bo
nie opisują przebiegu CI.

## 4. Przewidywania — cztery trafione, jedno obalone, jedno przeformułowane

| # | przewidywanie | wynik |
|---|---|---|
| W1 | kontrola przyrządu przejdzie | **trafione**, ale dopiero w wersji drugiej (§1) |
| W2 | stałych z konkretnego przebiegu więcej niż pięć | **rozdzielone**: wskazujących przebieg jest dziesięć, ale po odsianiu progów populacja ma równo pięć |
| W3 | większość NIE MA pary | **OBALONE co do treści**: par nie ma trzy z pięciu, ale żadna z tych trzech nie mogła jej mieć (§3) — a z dwóch, które mogły, parę mają obie |
| W4 | par nieodnotowanych co najmniej dwie | **trafione**: dwie |
| W5 | co najmniej jednej stałej nie znajdę w artefaktach | **trafione**: trzech — ale z innego powodu, niż zakładałem (nie wygaśnięcie, tylko pomiar lokalny i procenty) |
| W6 | `test_linecore_budget_gate.py` nie wniesie ani jednej pary | **trafione**: jego jedyna pozycja w populacji to ta z procentami |

## 5. Czego świadomie nie zrobiłem

Nie dopisałem brakującej pary do żadnej stałej, nie zmieniłem żadnej stałej, nie
postawiłem bramki na parach, nie tknąłem `src/` ani `data/` — wszystko to stoi
w polu „Poza zakresem".

**Nie rozszerzyłem populacji na inne moduły.** Pole wymienia dwa i tylko je
przejeżdżam; czy poza nimi stoją stałe tego samego kształtu, jest innym pytaniem.

**Nie zaliczyłem trafień „prawie".** §3 podaje trzy najbliższe wartości i ich
odległości, żeby dało się sprawdzić, że odrzucenie nie jest arbitralne.

## 6. Co zauważyłem przy okazji, ale nie tknąłem

Odsiewanie progów **porównaniem** działa, ale ma granicę, którą widać na tej
populacji: stała używana **i** jako próg, **i** jako zapis pomiaru wypadłaby jako
próg i zniknęła z pytania. W tych dwóch modułach taka nie występuje — sprawdziłem
wszystkie dwanaście — ale reguła tego nie gwarantuje, tylko drzewo.
