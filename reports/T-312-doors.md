# T-312 · Drzwi i czas postoju

Stan: **2026-09-01**. Wyjście: `src/Sim/Train/DoorCycle.cs`, `src/Sim/Train/StationStop.cs`,
`tests/Sim.Tests/DoorCycleTests.cs`. Zależy od T-310 (zrobione).

---

## 1. Co zrobiłem

Cykl drzwi z `docs/02-simulation.md` jako model, blokadę trakcji jako własność
bezpieczeństwa i minimalny postój jako wielkość **wyprowadzoną z faz**, a nie wpisaną
osobno. Czas wymiany pasażerów **nie dostał wartości** — jest argumentem, bo nie ma go
w żadnym źródle.

## 2. Cykl

`docs/02-simulation.md` podaje pięć faz o stałym czasie, wszystkie `design_model`:

| faza | czas | co się dzieje |
|---|---:|---|
| `Unlocking` | 0,5 s | odryglowanie po zatrzymaniu, skrzydła stoją |
| `Opening` | 2,0 s | otwieranie |
| `Open` | **argument** | wymiana pasażerów |
| `ClosingWarning` | 3,0 s | sygnał zamykania, skrzydła jeszcze otwarte |
| `Closing` | 2,5 s | zamykanie |
| `Checking` | 0,5 s | kontrola zamknięcia |

**Minimalny postój = 8,5 s** i jest to suma pięciu faz stałych, nie osobna stała.
Test przypina tę równość, więc zmiana którejkolwiek fazy musi zmienić sumę — nie da
się „poprawić" 8,5 s w oderwaniu od cyklu.

## 3. Czego świadomie nie ma: domyślnego czasu wymiany pasażerów

To jest najważniejsza decyzja tego zadania i jest to decyzja o **niewpisaniu liczby**.

Czas wymiany zależy od potoku pasażerskiego, pory dnia i stacji. W rejestrze źródeł
nie ma ani potoków, ani czasów postoju STIB, ani rozkładu z czasami peronowymi.
Wpisanie tu jakiegokolwiek „typowego" 20 czy 30 s byłoby podaniem czasu postoju metra
brukselskiego bez podstawy — a to jest dokładnie ta liczba, którą ktoś potem zacytuje
jako fakt.

Dlatego `DoorCycle` **nie ma konstruktora bezargumentowego**. Kod woli nie skompilować
się bez tej wartości, niż podstawić zmyśloną. Scenariusz, który ją poda, musi
zadeklarować ją jako własne założenie — tak samo jak `DriveScenario` deklaruje
`BrakeChainageM`.

Zero jest dopuszczalne i znaczy „nikt nie wysiada ani nie wsiada", a **nie** „drzwi się
nie otwierają": cykl i tak trwa pełne 8,5 s, bo odryglowanie, otwarcie, ostrzeżenie,
zamknięcie i kontrola dzieją się niezależnie od pasażerów.

## 4. Blokada jazdy — własność, nie parametr

`docs/02`: „Jazda zablokowana do potwierdzenia zamknięcia". Trakcja jest wolna
**wyłącznie** w fazie `Closed`, czyli **po** kontroli, a nie w chwili, gdy skrzydła się
zetknęły. Różnica to 0,5 s i jest to cała treść słowa „potwierdzenia".

Test sprawdza to **wyliczeniowo dla każdej fazy**, a nie dla wybranych:

```csharp
foreach (DoorPhase phase in Enum.GetValues(typeof(DoorPhase)))
{
    Assert.AreEqual(phase == DoorPhase.Closed, DoorCycle.TractionAllowed(phase), phase.ToString());
}
```

Dopisanie nowej fazy bez decyzji o blokadzie wywróci ten test.

### Dlaczego blokada jest filtrem polecenia, a nie gałęzią w kontrolerze

`TrainController` odpowiada na pytanie „co robi skład, gdy maszynista da tyle
nastawnika i tyle hamulca". Postój odpowiada na inne: „czy maszynista w ogóle może dać
nastawnik". Wpięcie blokady do kontrolera oznaczałoby, że **każdy** przebieg bez stacji
— w tym przebieg referencyjny T-310 i przejazd T-400 — musiałby przenosić stan drzwi,
którego nie używa. `StationStop.Filter` zeruje nastawnik przed kontrolerem i nie tyka
hamulca: skład ma stać, a nie toczyć się przy otwartych drzwiach.

### Cykl startuje od prędkości zero, nie od kilometrażu peronu

Drzwi otwierają się po **zatrzymaniu**, a nie po dojechaniu. Skład, który minął punkt
zatrzymania i wciąż się toczy, ma drzwi zamknięte. Test: sto kroków przy 0,5 m/s nie
otwiera cyklu.

## 5. Weryfikacja — rzeczywiste wyjście

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 186, Skipped: 0, Total: 186   (było 173)

$ python3 tools/tests/test_all.py
  401/401 przeszło
```

**Kontrola negatywna** — dwie mutacje modelu:

| co zepsute | testów pada |
|---|---:|
| blokada zwalnia już po zamknięciu skrzydeł, bez kontroli | **3 z 186** |
| minimalny postój wpisany jako `8.0` zamiast sumy faz | **4 z 186** |

Po wycofaniu obu: `git diff` pusty, 186/186.

**Parytet T-400 nietknięty.** Telemetria przejazdu po pakiecie A ma ten sam odcisk co
przed zmianą:

```
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t312/core.csv
```

Scenariusz `package-a-first-run` nie ma postojów pośrednich, więc dodanie modelu drzwi
nie mogło go ruszyć — i nie ruszyło.

## 6. Czego świadomie nie zrobiłem

- **Nie wpiąłem postoju w scenariusz T-400.** Wymagałoby to wybrania czasu wymiany
  pasażerów, którego nie ma (§3), i zmieniłoby przejazd, którego odcisk jest bramką
  w CI. To jest wejście dla T-320, nie dla tego zadania.
- **Nie modelowałem otwierania per strona peronu.** Która strona się otwiera, wynika
  z geometrii peronu — a długości, wysokości i układu peronów nie ma (R-004, blokuje
  też T-211).
- **Nie modelowałem drzwi jako pojedynczych skrzydeł.** `m7-spec.json` ma 18 par drzwi
  podwójnych na stronę i szerokość otworu 1,6 m, ale czasu ruchu pojedynczego skrzydła
  ani jego charakterystyki nie ma. Cykl jest cyklem **składu**, nie mechanizmem.
- **Nie modelowałem awarii drzwi, blokady skrzydła ani otwarcia awaryjnego.**
- **Nie ruszałem `data/`.**

## 7. Zauważone przy okazji, nie tknięte

- `DriveScenario.cs:124` miał komentarz „Bez postoju na stacjach pośrednich — cykl
  drzwi i czas postoju to T-312". Komentarz jest nadal prawdziwy: model istnieje, ale
  scenariusz go nie używa i nie może, dopóki nie ma czasu wymiany pasażerów.
- `TrainController` ma w komentarzu odesłanie do T-311 przy hamulcu postojowym.
  Hamulec postojowy jest stanem pojazdu, nie modelem hamowania — należy do T-312 albo
  do osobnego zadania o stanach składu. **Nie dodałem go**, bo „skład stoi z zamkniętymi
  drzwiami" i „skład jest zabezpieczony przed stoczeniem" to dwie różne rzeczy, a drugiej
  `docs/02` w ogóle nie opisuje.
