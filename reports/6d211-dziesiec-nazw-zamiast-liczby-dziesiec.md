# 6.D211 — dziesięć nazw zamiast liczby dziesięć

**14.09.2026**, na `7144ee6`. Wejście: `src/Sim/Signalling/FixedBlockSystem.cs` (`Replay`),
`src/Sim/Signalling/SignallingEvent.cs` (`SignallingEventKind`),
`src/Sim/Signalling/TrainProtection.cs` (`Supervise`, `ProtectionAction`),
`src/Sim/Signalling/CabProtection.cs` (`Supervise`), `src/Sim/Line/LineCore.cs` (`Step`),
`tests/Sim.Tests/DefaultArmAuditTests.cs` (6.D210),
`reports/6d197-jeden-switch-i-to-ten-juz-przybity.md` §6.

## 1. Cztery filtry, cztery zbiory nazw

Pomiar szedł **czytnikiem z 6.D210** — `Wyliczenie`, `Czlon`, `EtykietaInstrukcyjna`,
`Korpus` — a nie drugą jego kopią. To ta sama zasada, którą 6.D209 zastosowało,
pożyczając wzorzec z `test_backlog` zamiast go przepisywać: dwie kopie tego samego
czytnika rozjeżdżają się przy pierwszej poprawce, a rozjazd wychodzi po miesiącach.

| filtr | wyliczenie | pokrywa | POŁYKA |
|---|---|---:|---|
| `FixedBlockSystem.Replay` | `SignallingEventKind` (17) | 7 | **10**: AuthorityIssued, AuthorityViolation, DoorInhibit, DoorRelease, EmergencyIntervention, OverspeedIntervention, OverspeedWarning, RouteRejected, RouteRequested, TrainDeregistered |
| `TrainProtection.Supervise` | `ProtectionAction` (3) | 2 | **1**: None |
| `CabProtection.Supervise` | `ProtectionAction` (3) | 2 | **1**: None |
| `LineCore.Step` | `ProtectionAction` (3) | 2 | **1**: None |

Wszystkie cztery liczby z pola „Skąd" — 7 z 17 i trzy razy 2 z 3 — **trzymają się
co do jednego członu**, tak jak zapowiadało przeliczenie 6.D208.

## 2. Rozstrzygnięcie formy: WYLICZENIE NAZW, nie liczba

Pole „Czego NIE wolno przyjąć bez pomiaru" pytało wprost, czy zapadka równościowa na
LICZBIE obsłużonych członów jest tu właściwą formą. **Nie jest**, i powód jest ten sam,
który 6.D131 zapisało dla zapadek: liczba rośnie razem z wyliczeniem, więc jej
podniesienie jest **cichym sposobem na połknięcie członu zmieniającego stan**. Osiemnasty
człon `SignallingEventKind` dołożony jutro podniósłby „10 połykanych" na 11 i zapadka
przeszłaby po zmianie jednej cyfry — dokładnie to, przed czym miała bronić.

Nazwa tego nie pozwala. Kto dopisuje człon, musi albo wpisać go na listę razem z powodem,
albo dołożyć ramię — i jedno, i drugie jest **decyzją zapisaną**, a nie cyfrą podbitą przy
okazji. Zbiór porównywany jest przy tym **w obie strony**: KN-1 i KN-2 różnią się
kierunkiem i obie są czerwone.

**Trzeciej formy — zdania w dokumentacji metody — nie wybrałem i to jest rozstrzygnięcie,
nie pominięcie.** Zdanie w `<summary>` przy `Replay` starzeje się dokładnie tak, jak
starzały się liczby z pola „Skąd": nic go nie czyta. Lista w bramce jest czytana przy
każdym przebiegu.

## 3. Czego ta pozycja NIE zrobiła, zgodnie z polem „Poza zakresem"

- **Nie dołożyłem ani jednego ramienia** — wszystkie cztery filtry są świadome.
  `Replay` odtwarza stan z dziennika, a zdarzenia czysto sprawozdawcze (ostrzeżenia,
  odrzucenia trasy, zwolnienia drzwi) stanu nie zmieniają; `None` w `ProtectionAction`
  znaczy „nic nie rób", więc ramię byłoby puste i tylko powtarzałoby domyślne.
- **Nie tknąłem `StateDigest`** ani zachowania żadnego z czterech filtrów.
- **Nie tknąłem switchy postaci wyrażeniowej** — to 6.D210, domknięte.

## 4. Kontrole negatywne

Baza modułu: **4/4** (dwa testy z 6.D210, dwa nowe). Po każdej `md5sum -c` na trzech
plikach: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | osiemnasty człon dopisany do `SignallingEventKind` | **1/4 czerwone**, komunikat nazywa `KontrolaNegatywna` w zbiorze połykanych |
| KN-2 | ramię `case SignallingEventKind.DoorRelease:` dołożone do `Replay` | **1/4 czerwone**, `DoorRelease` **znika** ze zbioru |
| KN-3 | `RouteRejected` skreślony z listy wypisanych | **1/4 czerwone** |
| KN-4 | czytnik etykiet instrukcyjnych oślepiony (`case` → `Case`) | **3/4 czerwone** |

Pełne przebiegi po przywróceniu: `dotnet test tests/Sim.Tests` — **662/662**,
`python3 tools/tests/test_all.py` — **2481/2481**.

**KN-1 jest tą kontrolą, o którą prosiło pole „Weryfikacja"** — „dołożenie członu do
`SignallingEventKind` **zapala** bramkę". Zapala i nazywa człon po imieniu.

**KN-1 i KN-2 różnią się KIERUNKIEM, i to jest cała ich treść:** w KN-1 zbiór rośnie,
w KN-2 maleje, a bramka zapala się w obu. Zapadka na liczbie złapałaby oba przypadki
tylko dopóki ktoś nie podniósłby liczby — a wtedy KN-1 przechodzi.

**KN-4 zapala TRZY testy i to jest jej treść:** podłogę w bramce drzewa
(`switchy instrukcyjnych … znaleziono 0`), kontrolę przyrządu 6.D210 i — najważniejsze —
**kontrolę przyrządu na wejściu syntetycznym**, która o drzewo w ogóle nie pyta. Bez niej
oślepły czytnik zgłosiłby jako „połykane" **całe** wyliczenie, a przy filtrze biorącym
2 z 3 członów różnica między „połyka None" a „połyka wszystko" to jedna nazwa i dwie —
czyli coś, co przy odrobinie pecha przeszłoby przez oko.

## 5. Jeden czytnik, nie dwa — i dlatego dwie funkcje 6.D210 są przepisane

`Czlony()` liczyło człony własnym przebiegiem po `Wyliczenie`/`Czlon`. 6.D211 potrzebuje
tych samych członów **po nazwie**, więc zamiast drugiego przebiegu stoi teraz
`CzlonyNazwy()`, a `Czlony()` liczy jego wynik. Tak samo wyliczanie plików rdzenia
wyszło z `Zebrane()` do `ZrodlaRdzenia()`, bo wołają je teraz dwie bramki. **Zachowanie
obu testów 6.D210 jest bez zmian** — 4/4 przed podstawieniami i po przywróceniu.

## 6. Zauważone, nie tknięte

- **Wiersz 6.D210 w `docs/TASKS.md` nazywa tę metodę `Replay`, a jest nią `Supervise`.**
  Zdanie brzmi „`TrainProtection.cs` ma oba rodzaje naraz — wyrażeniowy rzucający
  w `Apply` (3/3) i instrukcyjny cichy w `Replay` (2/3)". Switch instrukcyjny stoi
  w `TrainProtection.cs:362`, a deklaracja `Supervise` w wierszu 307; metody `Replay`
  ten plik **nie ma w ogóle** — nazwa przyszła z `FixedBlockSystem.Replay`, mierzonego
  tego samego dnia. Liczba `2/3` i cała teza tamtej pozycji są poprawne; nieprawdziwa
  jest jedna nazwa. Wiersza nie poprawiam: pozycja jest domknięta, a wiersz domknięty
  jest zapisem swojego dnia (6.D108).
- **`KorpusMetody` rozpoznaje deklarację po MODYFIKATORZE DOSTĘPU** i to nie jest
  ozdoba: `Supervise` ma w `CabProtection.cs` deklarację w wierszu 196 i **wywołanie**
  siedem wierszy niżej (`_protection.Supervise(...)`), a `Step` w `LineCore.cs`
  deklarację w 766 i dwa wywołania dalej. Sito po samej nazwie brałoby wywołania za
  deklaracje. Metody prywatnej bez modyfikatora (C# dopuszcza) to sito **nie zobaczy** —
  dziś takiej wśród czterech nie ma, ale nic tego nie pilnuje.
- **`ObsluzoneCzlony` żąda DOKŁADNIE JEDNEGO switcha po danym wyliczeniu w metodzie.**
  Metoda z dwoma switchami po tym samym typie zapaliłaby bramkę, choć byłaby poprawna.
  Dziś takiej nie ma; gdyby powstała, formą odpowiedzi jest suma zbiorów, nie podniesienie
  liczby — ale to decyzja na wtedy, nie na dziś.
- **Trzy filtry na `ProtectionAction` mają identyczną listę i identyczny powód.** Wygląda
  to na materiał do wspólnego wpisu, ale wspólny wpis znaczyłby, że dołożenie ramienia
  w JEDNYM z trzech miejsc zapala bramkę o pozostałych dwóch. Trzy osobne wpisy są
  droższe w pisaniu i tańsze w czytaniu komunikatu.
