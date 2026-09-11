# 6.D128 — dwa pytania o listę SDK w jednym przebiegu, bo wynik drugiego szedł wprost na ekran

**Zmierzone 11.09.2026 na:** `d0e52df`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_dotnet_version.py` (`_przebieg_doctora` z dziennikiem
wywołań atrapy, `STANY_SDK`, `WOLAN_LISTY_SDK`), `doctor.sh` (blok SDK).

---

## 1. Pomiar przed zmianą

Dziennik atrapy, ten sam, którym 6.D112 policzyło wywołania `--version`:

| stan | `--list-sdks` | `--version` | dziennik |
|---|---|---|---|
| pin niespełniony | **2** | 1 | `['--list-sdks', '--version', '--list-sdks']` |
| pin spełniony | 1 | 1 | `['--list-sdks', '--version']` |
| brak jakiegokolwiek SDK | 1 | 1 | `['--list-sdks', '--version']` |

Dwójka wychodzi w **jednym** stanie z trzech i to jest dokładnie ten stan, który
wypisuje listę na ekran.

## 2. Dlaczego to nie była powtórka 6.D112

Tamta pozycja zbijała `--version` i kończyła się zapamiętaniem **kodu wyjścia**.
Tutaj wynik drugiego wywołania szedł **wprost na stdout**:

```sh
"$DOTNET" --list-sdks 2>/dev/null | sed 's/^/        na dysku: /'
```

Nie było czego zapamiętać, bo nikt tej listy nie trzymał — sonda `SDK_NA_LISCIE`
pytała tylko, czy wyjście jest **niepuste**, i wyrzucała je. Zapamiętanie listy
w zmiennej zmienia więc drogę, którą tekst dociera na ekran, i to jest całe ryzyko
tej zmiany.

## 3. Powodem nie jest czas, tylko rozjazd

Dwa wywołania to dwie okazje do rozjazdu. Doctor wypisywałby wtedy zdanie „SDK SĄ
na dysku, ale ŻADNE nie spełnia pinu" na podstawie **pierwszego** odczytu, a listę
„na dysku:" z **drugiego** — czyli zdanie o jednym stanie maszyny obok listy z innego.
Ta sama rodzina co usterka zamknięta przez 6.D96, tylko rozłożona w czasie.

## 4. Jedyne realne ryzyko: `$(...)` obcina końcowe nowe wiersze

Lista SDK szła dotąd prosto do `sed`, więc każdy wiersz docierał na ekran. Po
zapamiętaniu w zmiennej końcowe nowe wiersze znikają — a `sed` bez nich nie wypisze
ostatniego wiersza, co przy **jednym** zainstalowanym SDK znaczy listę **pustą**.
Stąd `printf '%s\n' "$SDK_LISTA"`, a nie gołe podstawienie.

Sprawdzane **na powłoce**, a nie na atrapie, i to jest tu treścią: atrapa wypisuje
dziś listę w jednym wierszu (ukośnik zamiast nowego wiersza — osobna pozycja 6.D129),
więc **na niej ta różnica nie zachodzi** i test mierzyłby nic. Test uruchamia więc
sam konstrukt na dwuwierszowej wartości i żąda dwóch wierszy z przedrostkiem, obok
kontroli w drugą stronę: `printf '%s'` daje wynik **inny**.

## 5. Co jest po zmianie

| stan | `--list-sdks` | wiersze o SDK |
|---|---|---|
| pin niespełniony | **1** | bez zmian |
| pin spełniony | **1** | bez zmian |
| brak jakiegokolwiek SDK | **1** | bez zmian |

Wiersze o SDK porównane co do bajtu z zapadką `STANY_SDK`, zapisaną 10.09.2026 przed
6.D112 — czyli tą samą, która przetrwała tamtą zmianę.

## 6. Kontrole negatywne — WYKONANE, nie opisane

Baza `test_dotnet_version.py`: **48/48** (było 45).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | wypis listy znów woła `dotnet` drugi raz (stan sprzed zmiany) | **46/48**, dwa testy |
| KN-2 | `printf '%s\n'` → `printf '%s'` (gubi ostatni wiersz) | **47/48** |
| KN-3 | sonda znów woła `dotnet` wprost, zmienna zostaje | **47/48**, dziennik `['--list-sdks', '--list-sdks', '--version']` |
| KN-4 | kolejność odwrócona: `--version` przed `--list-sdks` | **47/48**, kontrola przyrządu |

Po każdej: `md5sum -c` → `OK` na dwóch plikach.

KN-1 odtwarza dokładnie stan sprzed tej pozycji i zapala **dwa** testy naraz — licznik
wywołań i asercję o kształcie wypisu. KN-4 jest kontrolą przyrządu: dziennik atrapy
musi rozdzielać `--list-sdks` od `--version`, bo licznik zliczający jedno w miejsce
drugiego dałby te same jedynki i wyglądałby identycznie.

## 7. Czego nie zrobiłem

* **Nie połączyłem `--list-sdks` z `--version`** — wprost w „Poza zakresem", i słusznie:
  to dwa różne pytania, a cała 6.D96 stoi na tej różnicy. `--list-sdks` pyta „czy
  jakiekolwiek SDK jest", `--version` — „czy któreś spełnia pin z `global.json`".
* **Nie ruszyłem `WOLAN_WERSJI`** ani żadnego wiersza wypisu: `STANY_SDK` jest tą samą
  zapadką, co przed zmianą, i to ona jest warunkiem odbioru.
* **Nie poprawiłem atrapy**, która wypisuje ukośnik zamiast nowego wiersza — to stoi
  w kolejce jako 6.D129 i jest powodem, dla którego test z §4 musiał zejść na powłokę.
