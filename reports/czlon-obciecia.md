# Człon obcięcia w bilansie energii (6.A17)

**Zmierzone 07.09.2026 na commicie:** `2368a5d8278991a25e5032efe072f6e469979ad8`
(gałąź `claude/6a17-czlon-obciecia`, oś `data/track/L1_A.json`, AW0, tor poziomy).

## 1. Czym ta liczba jest, a czym nie

6.A6 zmierzyła przy 72 km/h `obcięcie = 96 889 720,4 J` przy `E_trakcji = 142,4515 kWh`
i bilansie domykającym się względnie do **2,147E-015**. Ten ostatni fakt jest tu
najważniejszy: **człon obcięcia nie jest błędem zamknięcia**. Reszta bilansu to
−1,9E-006 J, czyli szesnaście rzędów wielkości mniej. Obcięcie jest osobną, nazwaną
pozycją wielkości **26,9 kWh, czyli 19 % pracy trakcji**.

Jego źródło jest jednym wierszem w `LineDrive.AccumulateEnergy`:

```csharp
_clampedWorkJ += (netAll - (_effectiveMassKg * deltaSpeed / _step.Seconds)) * travelled;
```

Czyli: praca siły, której krok całkujący **nie zamienił na energię kinetyczną**, bo
ściął prędkość — do limitu albo do zera. Tożsamość jest algebraiczna, więc człon
istnieje w każdym kroku; niezerowy staje się dopiero tam, gdzie obcięcie faktycznie
zachodzi.

## 2. Zależność od limitu — cztery pomiary, nie dwa

Pole „Skończone, gdy" żądało **co najmniej dwóch** limitów. Dwa punkty nie ustalają
jednak monotoniczności, więc zmierzone są cztery:

| limit | obcięcie | E_trakcji | E_hamulca |
|---|---|---|---|
| 40 km/h | **506,32 MJ** | 182,29 kWh | — |
| 50 km/h | **338,62 MJ** | 155,89 kWh | 52,997 kWh |
| 60 km/h | **210,19 MJ** | 144,49 kWh | — |
| 72 km/h | **96,89 MJ** | 142,45 kWh | 104,357 kWh |

Monotonicznie: **im niższy limit, tym większe obcięcie** — pięciokrotnie między 72
i 40 km/h. Przy 40 km/h obcięcie (506 MJ = 140,6 kWh) **przewyższa** całą pracę
trakcji z przejazdu przy 72 km/h.

Warto zauważyć, czego ta tabela **nie** mówi: wzrost pracy trakcji (142,45 → 182,29 kWh,
czyli +39,8 kWh) **nie jest** równy wzrostowi obcięcia (+409 MJ = +113,7 kWh). Bilans
zawiera też opory i hamulec, a energia hamulca spada z 104,4 do 53,0 kWh przy zejściu
z 72 na 50 km/h — co samo w sobie zgadza się z kwadratem prędkości: `(50/72)² = 0,482`,
a `52,997/104,357 = 0,508`. Kuszące „traction rośnie o tyle, ile obcięcie" jest
nieprawdą i dlatego stoi tu wypisane jako nieprawda.

## 3. Mechanizm z kodu, a nie domysł

6.A6 nazwała obcięcie „miarą tego, jak długo skład wisi na limicie z pełnym
nastawnikiem", ale tego nie zmierzyła. Zmierzone teraz, ze śladu przejazdu
(`--trace`, krok 1/120 s), jako czas z `|v − limit| < 0,01 m/s` **i** `throttle > 0`:

| limit | czas na limicie z nastawnikiem | obcięcie |
|---|---|---|
| 72 km/h | 52,23 s | 96,89 MJ |
| 50 km/h | 167,81 s | 338,62 MJ |

Czas rośnie **3,21×**, obcięcie **3,50×** — czyli nie są proporcjonalne, i to jest
właśnie ślad mechanizmu. Prędkość przejścia siła→moc to **31,241 km/h**
(`2160 kW / 248,9 kN`, `data/vehicle/m7-spec.json`), więc **oba** limity leżą
w obszarze **stałej mocy**: trakcja na limicie daje `P/v`, a nie stałą siłę. Niższy
limit znaczy więc dwie rzeczy naraz — dłuższy czas na limicie **i większą siłę**
w tym czasie.

Stąd przewidywanie: odrzucana moc to `P − R(v)·v`, więc obcięcie ≈ `(P − R(v)·v) · t`.
Sprawdzone liczbowo, z oporami Davisa wziętymi z modelu, **nie** dopasowanymi:

```
limit  v[m/s]   F=P/v        R_davis    (P-R*v)      t na limicie   przewidziane   zmierzone      blad
  72   20.000   108000 N     7456 N     2010887 W      52.23 s      105.02 MJ      96.89 MJ     +8.4%
  50   13.889   155520 N     5043 N     2089957 W     167.81 s      350.71 MJ     338.62 MJ     +3.6%
```

**Zgodność do 8,4 % i 3,6 %, w tę samą stronę.** Nie jest to zgodność co do bitu i nie
powinna być: kryterium „na limicie" jest przybliżeniem (progiem 0,01 m/s), opory
policzone są dla AW0 na torze poziomym przy stałej prędkości, a obcięcie zbiera także
kroki hamowania do zera i kroki z częściowym nastawnikiem. Obie odchyłki są dodatnie,
czyli przewidywanie systematycznie zawyża — zgodnie z tym, że próg 0,01 m/s liczy jako
„na limicie" także kroki, w których nastawnik już zszedł.

## 4. Per odcinek, nie jedną liczbą na całą oś

Pole „Wyjście" żądało rozbicia na odcinki. Czas na limicie z nastawnikiem, po odcinkach
(oś L1_A ma jedenaście przejazdów międzystacyjnych):

| # | odcinek | długość | 72 km/h | 50 km/h |
|---|---|---|---|---|
| 1 | Gare de l'Ouest → Beekkant | 509,42 m | 1,72 s | 11,72 s |
| 2 | Beekkant → Étangs Noirs | 942,18 m | 12,53 s | 27,29 s |
| 3 | Étangs Noirs → Comte de Flandre | 602,88 m | 4,04 s | 15,07 s |
| 4 | Comte de Flandre → Sainte-Catherine | 665,96 m | 5,62 s | 17,35 s |
| 5 | Sainte-Catherine → De Brouckère | 409,20 m | **0,00 s** | 8,10 s |
| 6 | De Brouckère → Gare Centrale | 601,91 m | 4,02 s | 15,04 s |
| 7 | Gare Centrale → Parc | 343,82 m | **0,00 s** | 5,75 s |
| 8 | Parc → Arts-Loi | 485,27 m | 1,10 s | 10,84 s |
| 9 | Arts-Loi → Maelbeek | 591,47 m | 3,76 s | 14,67 s |
| 10 | Maelbeek → Schuman | 314,93 m | **0,00 s** | 4,71 s |
| 11 | Schuman → Merode | **1219,00 m** | 19,45 s | 37,26 s |
| | **suma** | | **52,23 s** | **167,81 s** |

To jest mechanizm w najczystszej postaci: **przy 72 km/h trzy odcinki nie dochodzą do
limitu wcale**, przy 50 km/h dochodzą wszystkie jedenaście. Niższy limit nie tylko
wydłuża pobyt na limicie na każdym odcinku — dokłada odcinki, które przy wyższym limicie
nie mają na to dość długości.

Odcinek 11 (Schuman → Merode, **1219,00 m**, najdłuższy na osi) dominuje w obu
przypadkach i przy 72 km/h daje sam **37 %** całego czasu na limicie (19,45 z 52,23 s).

A trzy odcinki, które przy 72 km/h nie dochodzą do limitu, to **dokładnie trzy
najkrótsze** przejazdy tej osi: 314,93 m (Maelbeek → Schuman), 343,82 m (Gare Centrale
→ Parc) i 409,20 m (Sainte-Catherine → De Brouckère). Nie jest to zbieg okoliczności
i nie było zgadywane — mapowanie numerów na nazwy i długości jest wzięte z wypisu
`[ODCINEK]` tego samego przejazdu. Przy 72 km/h skład potrzebuje na rozruch i hamowanie
więcej metrów, niż te odcinki mają; przy 50 km/h zdąży wejść na limit na każdym.

## 5. Test — dopisany, bo zależność JEST monotoniczna

Pole „Skończone, gdy" mówiło: „jeżeli zależność nie jest monotoniczna, pozycja mówi to
wprost i **nie dopisuje testu**". Cztery pomiary z §2 są monotoniczne, więc test jest.

Stoi na osi **syntetycznej**, nie na `data/track/L1_A.json`, i to jest wybór: kierunek
zależności wynika z równania z §1 i z obszaru stałej mocy, nie z konkretnej osi, a test
zależny od pliku w `data/` mierzyłby dwie rzeczy naraz. Przejazd całej L1_A w teście
kosztowałby też sekundy, a nie milisekundy.

Test drugi jest parą do pierwszego i bez niego pierwszy niczego nie przybija: obcięcie
musi być **dodatnie** i **większe od członu dyskretyzacji**. Bez tej asercji porządek
`niski > sredni > wysoki` zachodziłby także przy członie ujemnym albo zerowym — czyli
przy obcięciu, którego nie ma.

## 6. Kontrole negatywne — WYKONANE

```
KN-1  czlon obciecia wyzerowany (_clampedWorkJ += 0.0)
      Failed Czlon_obciecia_rosnie_gdy_limit_predkosci_maleje
      Failed Bilans_energii_calego_przejazdu_z_zatrzymaniami_domyka_sie
      Failed Bilans_calego_przejazdu_domyka_sie_takze_na_pochyleniu

KN-2  znak czlonu odwrocony (+= -> -=)
      Failed: 4, Passed: 550, Total: 554
      Czlon_obciecia_rosnie_gdy_limit_predkosci_maleje
      Czlon_obciecia_jest_dodatni_a_nie_resztka_zamkniecia
      + oba testy bilansu
```

Warto zobaczyć, co te kontrole mówią **poza** samym zapaleniem: przy wyzerowaniu członu
padają **także dwa testy bilansu z 6.A5**, których nie dopisywałem. Człon nie jest więc
ozdobą wypisu — jest nośny, a bilans bez niego przestaje się domykać. To jest mocniejszy
dowód na to, że mierzę rzecz istniejącą, niż moje własne dwa testy.

## 7. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 554, Skipped: 0, Total: 554
```

554 = 552 + **2** — liczba jest częścią weryfikacji, po nauczce z 6.B27.

## 8. Czego świadomie nie zrobiono

- **Nie tknięto modelu oporów, krzywej hamowania ani sposobu liczenia bilansu** — pole
  „Poza zakresem". Ta pozycja **mierzy** człon, który już tam był.
- **Nie dopisano wypisu obcięcia per odcinek do `[ODCINEK]`.** Rozbicie z §4 policzone
  jest ze śladu, który runner już zapisuje. Dopisanie kolumny do wypisu zmieniałoby
  format czytany przez `assert_line_trace.py` i wzorce SHA-256 — czyli dokładnie to,
  czego zabroniła sobie 6.A20 i co jest w kolejce jako 6.A21.
- **Nie rozdzielono obcięcia „do limitu" od „do zera".** Oba trafiają w ten sam
  akumulator, a ich rozdzielenie wymagałoby zmiany w `LineDrive` — czyli wejścia
  w „sposób liczenia bilansu", wykluczony wprost. Zmierzona zgodność z §3 (+3,6 %
  i +8,4 %) mówi, ile z całości przypada na resztę: niewiele.
- **Nie mierzono przy `--coast-from-m`.** Wybieg zmienia właśnie to, ile czasu skład
  wisi na limicie z nastawnikiem, więc byłby to osobny pomiar, a nie ten sam przy innej
  nastawie.
