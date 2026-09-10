# 6.D112 — cztery pytania o wersję, jedno w zdaniu wpisu

**Zmierzone 10.09.2026 na:** `5f75b8e`, kontener tej sesji.
**Przyrząd:** `doctor.sh` (blok SDK), `tools/tests/test_dotnet_version.py`
(`_atrapa_dotnet`, `_przebieg_doctora`, `STANY_SDK`), atrapa `dotnet` licząca własne
wywołania — wszystko w katalogu tymczasowym, drzewo tylko do odczytu.

---

## 1. Pomiar: nie trzy razy, tylko dwa, cztery albo trzy

Wpis mówi o **trzech** wywołaniach `"$DOTNET" --version` w bloku SDK. Trzy to liczba
**miejsc w kodzie** — i w dodatku miejsc jest **cztery**, nie trzy, bo wywołanie
wewnątrz `chk_prog_required` nie rzuca się w oczy przy czytaniu. Liczba wywołań
w PRZEBIEGU zależy od stanu, i tylko ona ma znaczenie:

```
a-pin-niespelniony  --version: 2   --list-sdks: 2
b-pin-spelniony     --version: 4   --list-sdks: 1
c-brak-sdk          --version: 3   --list-sdks: 1
```

Ani w jednym z trzech stanów nie wychodzi trzy. Zmierzone atrapą, która dopisuje
swój pierwszy argument do pliku — czyli tym samym przyrządem, który dziś pilnuje
wyniku, a nie osobnym.

Rozkład tłumaczy się co do wywołania: w stanie **a** sonda pinu i `HAVE_SDK_MAJOR`
(kontrola wymagana idzie wtedy gałęzią `chk_expr_required`); w stanie **b** wszystkie
cztery miejsca; w stanie **c** sonda pinu **nie** woła `--version`, bo `&&` zwiera się
na pustej liście SDK — zostają trzy.

## 2. Po zmianie

```
a-pin-niespelniony  --version: 1   --list-sdks: 2
b-pin-spelniony     --version: 1   --list-sdks: 1
c-brak-sdk          --version: 1   --list-sdks: 1
```

Jedno wywołanie na cały blok, a jego wynik — stdout i **kod wyjścia** — niosą dwie
zmienne. Kod wyjścia jest tu istotniejszy niż napis: cała 6.D96 stoi na tym, że przy
niespełnionym pinie `dotnet --version` **wypisuje na stdout listę SDK i pada**, więc
o stanie mówi kod, a nie treść.

`--list-sdks` **nie** zostało z tym połączone i to jest wybór, nie przeoczenie —
pole „Poza zakresem" wyklucza to wprost, bo są to dwa różne pytania.

## 3. Wypis nie drgnął — i to jest przybite, nie sprawdzone raz

```
pin niespełniony: IDENTYCZNY  kod 1->1  md5 68ae5085 -> 68ae5085
pin spełniony:    IDENTYCZNY  kod 0->0  md5 07fa2e2a -> 07fa2e2a
brak SDK:         IDENTYCZNY  kod 1->1  md5 b1a6f54d -> b1a6f54d
```

Zamiana `chk_prog_required` na `chk_expr_required` jest tu jedyną zmianą, która mogła
ruszyć wypis, i nie ruszyła: obie funkcje wypisują ten sam kształt wiersza
(`  ok    <nazwa>` albo `  BRAK  <nazwa>  -> <podpowiedź>`).

Zapadka `STANY_SDK` trzyma **wiersze o SDK**, a nie cały wypis, i to jest konieczne:
pełny wypis `doctor.sh` niesie też wiersze o Blenderze i Godocie, których obecność
zależy od maszyny. Zapadka na całym wypisie byłaby czerwona w CI i zielona lokalnie,
czyli nie mierzyłaby nic.

## 4. Dwie bramki sprzed tej pozycji zapaliły się celowo

**`test_doctor_uzywa_formy_tablicowej_do_uruchamiania_programow`** liczy wywołania
`chk_prog_*` i miała podłogę **sześć**. Po zamianie jednego z nich na formę
wyrażeniową jest ich pięć. Podłoga zeszła na pięć **razem z powodem**: ubyło
wywołanie programu, nie ubyło używanie formy tablicowej — a tego ta liczba pilnuje.

**`test_liczba_wersji_nie_bierze_sie_z_polecenia_ktore_padlo`** pytała o obecność
LITERAŁU `if HAVE_SDK_PELNA="$("$DOTNET" --version 2>/dev/null)"`. 6.D112 zmieniło
kształt tej gałęzi, nie jej własność, więc asercja pyta dziś o warunek na
zapamiętanym kodzie. Druga asercja tego testu — ta, która zabrania potoku
`--version | cut` — została nietknięta, bo dotyczy mechanizmu, który nadal jest zły.

## 5. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem, po każdej `md5sum -c` na dwóch
plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | `HAVE_SDK_MAJOR` wraca do własnego wywołania | 45/46, licznik pokazuje 2 |
| KN-2 | kontrola wymagana wraca do formy programowej | 45/46, licznik pokazuje 2 |
| KN-3 | treść jednego zdania zmieniona o trzy znaki | **44/46, dwa testy** |
| KN-4 | atrapa przestaje liczyć swoje wywołania | 45/46, dziennik pusty |
| KN-5 | kod wyjścia czytany o jedno polecenie za późno | **41/46, pięć testów** |

**KN-4 jest kontrolą PRZYRZĄDU, nie kodu:** dziennik pusty daje zero wywołań, a zero
to nie jest „jedno" — bez tej asercji zepsuty licznik meldowałby sukces. To ta sama
rodzina, którą projekt tropi od 6.D27.

**KN-5 warta zdania:** przesunięcie `$?` o jedno polecenie to klasyczna pomyłka
w powłoce i zapala **pięć** testów, w tym cztery sprzed tej pozycji. Kod wyjścia
staje się wtedy zawsze zerem, czyli doctor uznaje każdy pin za spełniony — dokładnie
ten stan, którego 6.D96 nie chciało.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_dotnet_version.py
  46/46 przeszło          (było 44)

$ python3 tools/tests/test_all.py
  2245/2245 przeszło, 120 modułów

$ dotnet test tests/Sim.Tests
  Passed!  - Failed: 0, Passed: 600
```

`doctor.sh` na prawdziwym SDK 10.0.401, z `DOTNET_ROOT` w środowisku:

```
  ok    dotnet SDK
  ok    dotnet SDK >= 10 (jest 10)
  ok    dotnet SDK == pin z global.json (10.0.401)
```

Trzy zdania, te same co przed zmianą, po jednym pytaniu o wersję.

## 7. Czego nie zrobiłem

- **Nie zmieniłem treści żadnego komunikatu** i nie połączyłem `--list-sdks`
  z `--version` — pole „Poza zakresem" wyklucza oba wprost.
- **Nie ruszyłem dwóch wywołań `--list-sdks`** w stanie „pin niespełniony": jedno
  jest sondą, drugie wypisuje listę na ekran. To ten sam kształt co usterka tej
  pozycji, ale dotyczy innego polecenia i wpis mówi wyłącznie o `--version`.
- **Nie tknąłem `test_liczba_wersji…` w części o potoku** — mechanizm, którego
  zabrania, jest nadal zły.

## 8. Zauważone przy okazji

- **`--list-sdks` woła się dwa razy w stanie „pin niespełniony"** i jest to
  dokładnie ta sama rodzina, co usterka zamknięta tutaj. Osobna pozycja, bo wypis
  drugiego wywołania idzie **na ekran** i połączenie ich wymaga rozstrzygnięcia,
  czy lista ma być zapamiętana w zmiennej — a to jest zmiana o innym kształcie.
- **Atrapa `dotnet` wypisuje literalne `\n` zamiast nowego wiersza** — widać to
  w wierszu `na dysku: 10.0.401 [/atrapa/sdk]\n` w stanie „pin niespełniony".
  Pochodzi z `f"{w} [/atrapa/sdk]\\n"` w `_atrapa_dotnet`, jest sprzed tej pozycji
  i zapadka `STANY_SDK` zapisuje ten stan **taki, jaki jest**, a nie taki, jaki
  powinien być — inaczej zapadka byłaby czerwona od pierwszego dnia. Poprawka
  zmieniłaby wypis atrapy, czyli dokładnie to, czego ta pozycja pilnuje, żeby się
  nie zmieniło.
