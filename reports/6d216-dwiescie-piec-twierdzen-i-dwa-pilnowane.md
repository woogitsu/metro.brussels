# 6.D216 — dwieście pięć twierdzeń, dwa pilnowane i trzy powody, dla których bramki nie ma

**15.09.2026**, na `18c320d`. Wejście: `reports/*.md` (sekcje o nagłówku zawierającym
„zauważone"), `tools/tests/test_report_claims.py` (`CLAIM`, `constant_values`,
`zdanie_z_dnia_pomiaru`, `wystapienia_w_jednych_grawisach`),
`tools/tests/test_report_hygiene.py` (`test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`),
`reports/6d200-potrojny-cudzyslow-po-malpie-i-szesnascie-metod.md` §7,
`reports/6d201-szesc-postaci-a-nie-cztery-i-zadna-bezczynna.md` §4 i §7,
`tests/Game.Tests/UiTextTests.cs` (`Literaly`, `PrefiksLiteralu`, `CzytajLiteral`,
`KodLeksykalnie`, `PlikiZrodlowe`, `PlikiRdzenia`, `NazwyWyliczeniowychWRdzeniu`).

## 1. Cztery liczby, których żądało pole „Wyjście"

| | |
|---|---:|
| raportów w katalogu | 343 |
| raportów z sekcją „zauważone" | **153** |
| takich sekcji (raport może mieć dwie) | **157** |
| punktów w tych sekcjach, poza tabelami i blokami kodu | 359 |
| **twierdzeń liczbowych** (punkt z cyfrą po zamaskowaniu adresów) | **205** |
| z tego pilnowanych dziś przez `CLAIM` + `constant_values()` | **2** |
| rozjazdów wśród pilnowanych | **0** |

**Wszystkie liczby tej tabeli są sprzed tego commita.** Raport, który właśnie czytasz,
dokłada własną sekcję „zauważone" i dwa twierdzenia liczbowe, więc po scaleniu katalog
ma **344** raporty, **154** z taką sekcją, **158** sekcji i **207** twierdzeń — i na tych
wartościach stoją podłogi bramki, bo podłoga ma kąsać dziś, nie wczoraj.

**Dwa z dwustu pięciu, czyli jeden procent.** Te dwa to
`SUITE_RUNTIME_BUDGET_S` (150,0) w `6d122-zestaw-czysci-bajtkod-sam.md`
i `MIN_WPISOW_RUNNERA` (6) w `6d205-trzydziesci-kilobajtow-i-dwa-przebiegi-ktore-nie-weszly.md`.
Oba zgodne z kodem. Dla porównania `CLAIM` pilnuje w **całych** raportach **54**
twierdzenia — więc sekcja „zauważone" niesie 205 twierdzeń liczbowych i dostarcza
bramce **2 z 54**.

**Adres jest pilnowany, liczba nie jest — i to jest cała rzecz w jednym zdaniu.**
W twierdzeniu „`src/Sim.Runner/` ma 23 z 53 zgłoszeń" bramka
`test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie` sprawdza, że
`src/Sim.Runner/` **istnieje**. Że jest ich **23**, nie sprawdza nic.

**Liczebniki słowne policzone osobno i osobno zostawione.** Punktów niosących wyłącznie
liczebnik zapisany słowem („cztery deklaracje", „trzy sita") jest **92** — razem z tamtymi
297. Do bramki nie wchodzą i to jest wybór z powodem: lista liczebników polskich łapie
„jeden z nich" i „dwa razy" tak samo jak twierdzenie, a bramka świecąca na poprawnym
tekście zostaje wyłączona, nie poprawiona (6.D27). Liczba 92 stoi w raporcie, żeby nie
czytać 205 jako całej populacji.

## 2. Zdanie, które postawiło tę pozycję — przeliczone, a było zapisane jako NIEPRZELICZALNE

6.D208 zapisało 14.09.2026, że „14 z 22" z 6.D201 jest **nieprzeliczalne tym, czym
dysponuje agent czytający drzewo**, bo rozstrzyga je czytnik `Literaly`
z `tests/Game.Tests/UiTextTests.cs`, a skan po samych ogranicznikach mierzy co innego.

**To jest dziś przeliczone i nieprzeliczalne nie było.** Czytnik stoi w drzewie; wystarczyło
go zawołać — jednym tymczasowym testem w `Game.Tests`, uruchomionym i skasowanym:

```
POMIAR-6D216 plikow=148 literalow=7082 trzy-i-wiecej=23
POMIAR-6D216 klasa ["""] = 9
POMIAR-6D216 klasa [$$"""] = 14
```

Zdanie 6.D200 §7 brzmi: „Gałąź surowa jest więc ćwiczona **wyłącznie przez zapisy bez
przedrostka** — a tych jest 30 par potrójnych cudzysłowów w `tests/` i `src/`."

**Jest fałszywe:** literałów otwartych trzema cudzysłowami jest dziś **23**, z tego
**14 z przedrostkiem `$$`** i **9 bez**. Gałąź surowa jest ćwiczona w większości przez
zapisy Z przedrostkiem. Liczba 14 z 6.D201 trzyma się co do jednego; ruszyła tylko
suma, 22 → 23.

**A obok niej stoi drugie zdanie tej samej sekcji i też jest fałszywe:** „Trzy dalsze
czytniki w drzewie mają tę samą gałąź". 6.D215 zmierzyło wczorajszym pomiarem, że
czytnik jest **jeden** (`CzytajLiteral`), a `Literaly` i `KodLeksykalnie` są jego
wołającymi. **Dwa twierdzenia w sekcji, dwa fałszywe** — i sekcja przeszła pełny zestaw,
przegląd i scalenie.

## 3. Ręczny przegląd dziesięciu najnowszych sekcji

Slajs jest zdefiniowany, a nie dobrany: dziesięć raportów z sekcją „zauważone"
**dodanych do repozytorium najpóźniej** (`git log --diff-filter=A`). Są to 6.D207…6.D215
i 6.D222. Każde twierdzenie liczbowe przeliczone ręcznie, jedno po drugim.

**Slajs jest stronniczy W STRONĘ PRAWDY i tak trzeba go czytać:** to zdania napisane
w ciągu dwóch dób o dzisiejszym drzewie. Fałsz z sekcji 2 pochodzi z raportu o pięć dni
starszego i w tym slajsie by się nie znalazł.

| klasa | co to znaczy | ile |
|---|---|---:|
| **A** | liczba **przypięta** dziś asercją w drzewie | 4 |
| **B** | czytnik jest w drzewie, liczba nieprzypięta — przeliczalne | 14 |
| **C** | **czytnik nie został w drzewie** — przeliczenie wymaga odtworzenia sita z prozy | 2 |
| **D** | historia, przebiegi CI, wynik dawnej kontroli negatywnej — nieprzeliczalne | 8 |
| | **razem** | **28** |

Wynik przeliczenia osiemnastu z klas A i B:

| | ile |
|---|---:|
| zgodnych z dzisiejszym drzewem | **15** |
| poprawnych w dniu pomiaru, **ruszyły od tamtego dnia** | **2** |
| **fałszywych w dniu, w którym je napisano** | **1** |

### Fałszywe: ramiona `when`

6.D210 §9 pisze: „Klasyfikator nie odróżnia `throw` od `throw` z pustym komunikatem ani
nie czyta ramion `when`. Pierwszego nie potrzebuje (pyta o ciszę), **drugiego w `src/Sim/`
dziś nie ma**".

Są **cztery**, wszystkie w `src/Sim/Train/DriverKeys.cs` (wiersze 143, 146, 149, 152),
i stoją tam od `877ab66` z **05.09.2026** — dziewięć dni **przed** napisaniem tamtego
zdania. Zdanie nie zestarzało się; było fałszywe od razu.

**I widać na nim, jak ten fałsz powstaje.** Switch w `DriverKeys.cs` chodzi po `const char`,
a nie po wyliczeniu, więc do populacji klasyfikatora 6.D210 nie należy. W tym zakresie
zdanie jest prawdziwe. Napisane zostało jednak o **`src/Sim/`**, czyli o zakresie
szerszym niż ten, o którym mówiło. Sekcja „zauważone" jest pisana na końcu pracy,
jednym zdaniem, bez pomiaru — i to jest dokładnie ten kształt pomyłki, który się tam
rodzi: zakres domyślny z kontekstu akapitu, zapisany jako zakres całego katalogu.

### Ruszyły od dnia pomiaru

6.D209 §9: „Populacja urosła z 41 na 51 w ciągu jednej doby". Dziś jest ich **55**.
Zdanie było poprawne 14.09 i jest zapisem swojego dnia (6.D108). Z tej samej populacji:
„Sześć wystąpień ma nazwę, której drzewo nie zna (51 − 45)" — **liczba 6 trzyma się dziś
co do jednego** (6 nieznanych na 55, 49 znanych), rozjechał się tylko rozkład.

### Przeliczone i zgodne — wykaz, bo liczba bez wykazu nie jest sprawdzalna

| raport | twierdzenie | przeliczone dziś |
|---|---|---|
| 6.D208 | `twierdzenia_w_polach_skad()` zwraca zero | **0** |
| 6.D210 | `TrainProtection.cs`: wyrażeniowy 3/3, instrukcyjny 2/3 | zgodne |
| 6.D210 | trzy z czterech switchy instrukcyjnych na `ProtectionAction`, wszystkie 2 z 3 | przypięte (A) |
| 6.D211 | switch instrukcyjny `TrainProtection.cs:362`, deklaracja w 307 | **362 / 307** |
| 6.D211 | `CabProtection.cs`: deklaracja 196, wywołanie siedem wierszy niżej | **196 / 203** |
| 6.D211 | `Step` w `LineCore.cs`, deklaracja w 766 | **766** |
| 6.D211 | żadna z czterech metod nie jest prywatna bez modyfikatora | cztery razy `public` |
| 6.D211 | trzy filtry na `ProtectionAction` mają identyczną listę | przypięte (A) |
| 6.D213 | 5 nazw dwuznacznych na 24 | **5 z 24**, 19 jednoznacznych |
| 6.D213 | `DriverKeys.NoneCode` to `const char` | `public const char NoneCode = '-'` |
| 6.D214 | `src/Sim.Runner/` ma 23 z 53 zgłoszeń | **23 z 53** (Game 21, Sim 9) |
| 6.D214 | wszystkie 46 wywołań z argumentem mają obok literału przecinek albo nazwę | **46**, z tego **0** o argumencie będącym samym literałem |
| 6.D215 | `Literaly` dla `@"a"""` daje `a""` | `[a""]` |
| 6.D215 | `PostacieLiteralu` i `POSTACIE_LITERALU` — te same cztery zapisy | przypięte (A) |
| 6.D222 | `.github/actions/*/action.yml` przechodzą przez tę samą bramkę | `_pliki_yaml_ci()` = workflowy + `_action_files()` |

## 4. Rozstrzygnięcie: bramki na PRAWDZIWOŚCI nie ma, i są to trzy powody, nie ostrożność

**Powód pierwszy — automat, który istnieje, pilnuje 2 z 205.** Poszerzenie `CLAIM`
o kształt bez grawisów jest przedmiotem 6.D209 i zostało tam **rozstrzygnięte przeciw**
pomiarem (cztery cytaty, ani jednego twierdzenia). Tu nic tego nie zmienia.

**Powód drugi — przeliczalność jest własnością CZYTNIKA, nie zdania.** Klasa C tabeli
wyżej to twierdzenia 6.D207, których nie da się dziś przeliczyć **nie dlatego, że są
niejasne**, tylko dlatego, że sito, które je wyprodukowało, nie zostało w drzewie —
i nie zostało **słusznie**: 6.D207 zmierzyło mu 5 trafień fałszywych na 5 i bramki nie
postawiło, zgodnie z 6.D27. Bramka żądająca przeliczalności karałaby dokładnie te
pozycje, które posłuchały reguły projektu.

**Powód trzeci — i to on przesądza — automat nie odróżni fałszu od zdania, które się
zestarzało.** Mechanizm z 6.D108 (`zdanie_z_dnia_pomiaru`) zwalnia twierdzenie, gdy
stała ruszyła po ostatnim tknięciu raportu; **kotwicą jest data STAŁEJ z gita**.
Twierdzenia sekcji „zauważone" żadnej stałej nie cytują — liczą coś w drzewie — więc
kotwicy nie mają i mechanizm się na nie nie przenosi. Zmierzone na parze z tego samego
slajsu: „51" z 6.D209 (dziś 55, **poprawne w swoim dniu**) i „ramion `when` nie ma"
z 6.D210 (dziś cztery, **fałszywe w swoim dniu**) wyglądają dla automatu porównującego
z dzisiejszym drzewem **identycznie**. Bramka zapalałaby się na obu, a poprawką dla
pierwszego byłoby przepisanie liczby — czyli obchodzenie bramki zamiast rozstrzygania,
ta sama pułapka, którą 6.D108 zamknęło.

**Co zostaje: czytnik sekcji z podłogą i kontrolą przyrządu.** Nie pilnuje prawdziwości
niczego i nie udaje, że pilnuje. Pilnuje, że **następna pozycja pytająca o to samo nie
będzie musiała odtwarzać sita z prozy** — czyli zamyka dokładnie to, co klasa C nazwała
po imieniu. Podłogi (157 sekcji, 205 twierdzeń) zapalają się, gdy czytnik przestaje
widzieć, a kontrola przyrządu żąda, żeby twierdzenie **dopisane** do takiej sekcji
weszło do pomiaru — o co prosiło pole „Weryfikacja".

## 5. Kontrole negatywne

Baza: **2488/2488** w zestawie, **16/16** w module. Po każdej `md5sum -c`: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | wzorzec nagłówka sekcji oślepiony | **14/16** — podłoga (`znaleziono 0 przy podłodze 158`) **i** kontrola przyrządu |
| KN-2 | twierdzenie liczbowe **dopisane** do sekcji prawdziwego raportu | **207 → 208, widziane** |
| KN-3 | to samo zdanie, ale **w bloku kodu** | **207, NIEwidziane** |
| KN-4 | jedna gałąź maski adresów zdjęta (numer wiersza) | **208** i **15/16** |
| KN-5 | maska **daty i numeru pozycji** zdjęta | **207 → 243** i **14/16** |

**KN-2 i KN-3 to para, o którą prosiło pole „Weryfikacja"** — to samo zdanie z tą samą
liczbą, raz jako twierdzenie, raz jako cytat. Pierwsze wchodzi do pomiaru, drugie nie.

**KN-5 mierzy, ile maska jest warta: 36 twierdzeń fałszywych z jednej gałęzi.** Bez maski
daty i numeru pozycji punkt „zmierzone 13.09.2026 przy 6.D201" liczyłby się jako
twierdzenie liczbowe o drzewie, choć nie mówi o drzewie ani jednej liczby. Zapaliły się
przy tym **dwa** testy, nie jeden — trzecia próbka wejścia syntetycznego
(„powołanie się na 6.D200 i §7 z 13.09.2026, i nic więcej") jest tam właśnie po to.

**KN-1 jest ważna przez ten drugi test.** Podłogi same w sobie są spełniane także przez
czytnik, który przestał widzieć połowę katalogu i o tym nie mówi; dopiero kontrola
przyrządu na wejściu **syntetycznym** żąda, żeby zdanie dopisane do sekcji weszło do
wyniku — i to ona, a nie podłoga, jest tu bramką.

Pełne przebiegi:

```
$ python3 tools/tests/test_all.py
  2488/2488 przeszło
  RAZEM 225.961 s, 2488 testów, 126 modułów

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 662, Skipped: 0, Total: 662

$ dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 313, Skipped: 0, Total: 313
```

## 6. Czego świadomie nie zrobiłem

- **Żadnego zdania w żadnym raporcie nie poprawiłem**, w tym dwóch fałszywych z §2 i §3.
  Raport jest historią (6.D108). Poprawką jest pozycja, nie edycja.
- **`CLAIM` nietknięty** — to 6.D209, rozstrzygnięte.
- **Kształtu sekcji „zauważone" nie zmieniałem.** Wariant „każde twierdzenie liczbowe
  ma nieść adres" odpada z pomiaru: 159 z 297 punktów adresu nie niesie, a wśród nich
  są zdania poprawne.

## 7. Zauważone, nie tknięte

- **Nagłówek tej sekcji ma w katalogu 23 różne brzmienia po odjęciu numeru, a 58 licząc z numerem** („Zauważone przy okazji",
  „Zauważone po drodze, nie tknięte", „Co zauważone przy okazji, nietknięte" i dalsze),
  a numer sekcji waha się od 5 do 10. Czytnik pyta o rdzeń „zauważon" i tyle wystarcza;
  gdyby ktoś napisał „Uwagi na marginesie", wypadłby z pomiaru bez śladu.
- **190 raportów z 343 nie ma takiej sekcji w ogóle.** Nie sprawdzałem, czy to raporty
  krótsze, starsze, czy pisane wtedy, gdy konwencji jeszcze nie było.
