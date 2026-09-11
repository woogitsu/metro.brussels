# 6.D116 — dwie nazwy klawiszy i to, do czego naprawdę były przybite

**Zmierzone 11.09.2026 na:** `f9fdb31`, kontener tej sesji.
**Przyrząd:** `src/Game/Input/KeyNames.cs` (nowy), `src/Game/Input/DriverActions.cs`,
`src/Game/Input/EmergencyBrake.cs`, `tests/Game.Tests/DriverActionsTests.cs`;
zrzuty skryptowe Godota 4.7.2 mono, `--view=cab --no-geometry`, 1280×720.

---

## 1. Teza wpisu jest w połowie NIEPRAWDZIWA i to jest pierwszy wynik

Wpis mówi: *„zmiana `\"Esc\"` na `\"Escape\"` nie zapali dziś żadnej bramki"*. Zmierzone
**na drzewie sprzed tej pozycji**, podmianą w tabeli przypisań:

```
Failed W_plikach_sterowania_nie_ma_ani_jednego_slowa
Failed Wiersze_zlozone_z_katalogu_brzmia_co_do_znaku_tak_jak_przed_przenosinami
Failed!  - Failed: 2, Passed: 227, Total: 229
```

To samo dla „Spacji", podmianą wartości w katalogu:

```
Failed Wiersze_zlozone_z_katalogu_brzmia_co_do_znaku_tak_jak_przed_przenosinami
Failed!  - Failed: 1, Passed: 228, Total: 229
```

Obie nazwy **były** przybite — tylko nie tam, gdzie wpis zakłada, i nie tak, żeby to
coś znaczyło:

- `Wiersze_zlozone_z_katalogu…` (6.D99) pinuje **cały wiersz pomocy** z ręki. Łapie
  każdą zmianę napisu, ale nie mówi nic o kodzie fizycznym: zdanie „ta nazwa należy do
  `Key.Escape`" nie pada tam ani razu. Aktualizacja pinu razem ze zmianą nazwy jest
  jedną linijką i przechodzi bez ani jednego pytania o klawiaturę.
- `W_plikach_sterowania_nie_ma_ani_jednego_slowa` zapaliła się z **przypadku i myląco**:
  `"Escape"` nie stoi w `NazwyKlawiszy = { "Esc" }`, więc skan literałów wziął ją za
  polskie słowo. Komunikat mówi „w plikach sterowania stoi literał językowy" — o czymś,
  co jest nazwą klawisza zapisaną z angielska. Nazwa zmieniona na inną pozycję z tej
  listy nie zapaliłaby niczego.

**Sedno wpisu zostaje prawdą:** żadna z siedmiu nazw nie była związana z `physical_keycode`
inaczej niż przez kod ASCII litery, a dwie z nich litery nie mają.

## 2. Co stoi dziś

`KeyNames` trzyma odwzorowanie **kod fizyczny → nazwa** dla klawiszy, których nazwy nie
da się odczytać z kodu. Dwa wpisy, bo tyle ich jest. Czytają z niego obaj wołający:
wiersz `Quit` w tabeli przypisań i `EmergencyBrake.KeyName`.

**Granica z 6.D83 zostaje nietknięta i to ona dzieli tę tabelę na pół.** Na klawiszu Esc
napisane jest „Esc" — to odczyt z klawiatury, więc stoi w kodzie jako literał. Na spacji
nie jest napisane nic, a „Spacja" jest polskim rzeczownikiem, więc przychodzi z katalogu
(`input.key.space`). Tabela **wiąże** obie z kodem, nie zmieniając tego, skąd każda
pochodzi.

**`KeyNames` nie wyprowadza nazw liter i to jest wybór.** Gdyby je wyprowadzała, test
porównujący nazwę z kodem porównywałby wynik jednej funkcji z nią samą — a ten test jest
jedynym miejscem, w którym litera z wiersza pomocy spotyka się z kodem z `project.godot`.

## 3. Druga kopia mapowania stoi w teście — z ręki, i to jest jej cała wartość

Poprzedni docstring odmawiał przybicia dwóch nazw słowami: *„ich odpowiednikiem byłaby
druga kopia mapowania nazwa → kod, czyli dokładnie to, czego cała ta zmiana się
pozbywa"*. Odpowiedź: **tak, i właśnie dlatego ta kopia ma sens**. Porównanie `KeyNames`
z `KeyNames` nie sprawdziłoby niczego; pin wpisany z ręki sprawdza. Ten sam wzorzec
zastosowało 6.D99 dla trzech napisów, których zrzut nie pokazuje.

Zbiór jest domknięty **w obie strony**: każdy wpis `KeyNames.Znane` musi mieć parę
w tabeli testu i odwrotnie. Bez tego dopisanie klawisza do tabeli produkcyjnej
przechodziłoby bez ani jednego sprawdzenia — czyli dokładnie tak, jak przechodziły
„Esc" i „Spacja".

## 4. Siedem wierszy, siedem sprawdzeń

`Kazda_nazwa_z_tabeli_przypisan_jest_przybita_do_swojego_kodu` chodzi po **całej**
tabeli: litera przez kod ASCII, reszta przez pin. Licznik stoi obok pętli i żąda siedmiu,
bo pominięcie wiersza ma tu być błędem, a nie wyborem — poprzednia wersja pomijała dwa
wiersze właśnie jako wybór.

Stary test o nazwach jednoliterowych **zostaje nietknięty**: pyta o co innego (czy kod
litery jest jej kodem ASCII) i jego zniknięcie byłoby utratą, nie sprzątaniem.

## 5. Wypis HUD-u co do bajtu

```
km=300    ba915e3ecb2d7eb14fa712d0cdc35228
km=900    88cb4fd443113fc4eb8b4b70ad5f4404
km=2500   f126b3604533f1163a52e9eaf676b36c
```

Te same trzy sumy co w `reports/6d99-slowo-a-napis-na-klawiszu.md` i w 6.D115. Wiersz
pomocy przechodzi dziś przez `KeyNames`, więc pomiar mówi coś więcej niż w 6.D115, gdzie
`src/Game/` był nietknięty: **przełożenie nazw na tabelę nie zmieniło ani jednego piksela**.

## 6. Kontrole negatywne

`md5sum -c` na dwóch plikach po każdej.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | `"Esc"` → `"Escape"` w tabeli nazw | **228/231, trzy testy**, z nazwą klawisza w komunikacie |
| KN-2 | „Spacja" znika z tabeli nazw | **226/231, pięć testów** |
| KN-3 | do tabeli dochodzi klawisz bez pinu (`Key.Tab`) | 230/231 |
| KN-4 | pętla wraca do samych nazw jednoliterowych | 230/231 |

**KN-1 jest warunkiem odbioru z pola „Weryfikacja" i podaje dokładnie to, czego ono
żąda:**

```
'run_quit': wiersz pomocy mówi 'Escape', a kod fizyczny 4194305 (Escape) nazywa się 'Esc'
```

**KN-2 zapala pięć testów**, bo brak wpisu jest ODMOWĄ, nie napisem zastępczym —
`KeyNames.For` rzuca, a `DriverActions.All` jest polem statycznym, więc wywraca się
wszystko, co tabeli dotyka. To jest zachowanie chciane i ten sam powód, dla którego
`UiText.Get` rzuca przy braku klucza: nazwa zastępcza w wierszu pomocy wygląda na ekranie
jak usterka tekstu i tak zostaje zgłoszona — po dwóch dniach i przez kogoś innego.

**KN-3 i KN-4 pilnują dwóch przeciwnych kierunków gnicia:** pierwszy — że tabela
produkcyjna nie urośnie bez pinu; drugi — że pętla nie skurczy się z powrotem do pięciu
wierszy.

## 7. Weryfikacja

```
$ dotnet test tests/Game.Tests
  Passed!  - Failed: 0, Passed: 231          (było 229)

$ dotnet test tests/Sim.Tests
  Passed!  - Failed: 0, Passed: 600

$ python3 tools/tests/test_all.py
  2254/2254 przeszło, 120 modułów
```

## 8. Czego nie zrobiłem

- **Nie zmieniłem ani jednego przypisania klawisza i nie dodałem akcji** — pole „Poza
  zakresem" wyklucza oba wprost. Tabela jest ta sama, przestała tylko mieć dwa wiersze
  poza kontrolą.
- **Nie ruszyłem `NazwyKlawiszy` w `UiTextTests`** ani listy wyjątków skanu literałów:
  „Esc" nadal jest tam jedynym wpisem i nadal ma być.
- **Nie wyprowadziłem nazw liter z kodów** — powód w §2.
- **Nie dopisałem do `KeyNames` klawiszy, których tabela przypisań nie używa.** Zbiór
  jest zamknięty i domknięty testem w obie strony; dopisywanie na zapas zapaliłoby KN-3.

## 9. Zauważone przy okazji

- **`W_plikach_sterowania_nie_ma_ani_jednego_slowa` zapala się na zmianie nazwy klawisza
  i mówi przy tym co innego, niż się stało.** Komunikat nazywa angielską nazwę klawisza
  „literałem językowym". Jest to bramka sprzed tej pozycji i o czym innym, więc jej nie
  ruszam (§4.10) — ale ktoś, kto ją zobaczy, pójdzie szukać polszczyzny tam, gdzie jej
  nie ma.
- **Pin całego wiersza pomocy z 6.D99 trzeba aktualizować ręcznie przy każdej zmianie
  nazwy.** Dziś to jedna linijka i dwie nazwy; przy dziesięciu akcjach zacznie być
  kosztem, a koszt pinu jest tym, co zwykle popycha do jego rozluźnienia.
