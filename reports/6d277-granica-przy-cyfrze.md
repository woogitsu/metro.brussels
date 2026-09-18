# 6.D277 — `\b` nie jest granicą liczby, a stoi przy cyfrze w siedmiu wzorcach

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `3ed9cc0`

## 1. Trzy liczby

Zmierzone na dzisiejszym drzewie, skanem AST po pierwszym argumencie `re.compile`
pod `tools/`:

| | co | ile |
|---|---|---|
| **L1** | literałów wzorców z `\b` bezpośrednio przy cyfrze lub `\d`, w **5** plikach | **7** |
| **L2** | z tego takich, którym wejściem bywa proza z ułamkiem pisanym przecinkiem | **7** |
| **L3** | takich, które **dziś** rozcinają liczbę na żywym drzewie | **1** |

Adresy L1 — klucz to `(plik, wzorzec)`, nie numer wiersza (6.D229):

| plik | wzorzec | tryb | granice |
|---|---|---|---|
| `test_backlog.py` | `\b\d{2}\.\d{2}\.\d{4}\b` (`DATA_DECYZJI`) | `search` | 2 |
| `test_message_claims.py` | `\b6\.[A-Z]\d+\b` (`SMIECI_W_PROZIE`) | `sub` | 2 |
| `test_message_claims.py` | `\bMB-\d+\b` (`SMIECI_W_PROZIE`) | `sub` | 1 |
| `test_report_claims.py` | `ADRES_NIE_TWIERDZENIE`, dziewięć alternatyw | `sub` | 9 |
| `test_report_hygiene.py` | `\b20\d\d-\d\d-\d\d\b` (`NOTATIONS` ISO) | `findall`+`sub` | 2 |
| `test_report_hygiene.py` | `\b\d\d\.\d\d\.20\d\d\b` (`NOTATIONS` PL) | `findall`+`sub` | 2 |
| `test_suite_runtime_budget.py` | `\b\d{1,2}\.\d{2}\.\d{4}\b` (`_DATA_PL`) | `search` | 2 |

Literałów jest **7**, ale samych granic `\b` przy cyfrze — **20**: jeden literał
(`ADRES_NIE_TWIERDZENIE`) niesie ich dziewięć, bo jest sumą alternatyw.

**L1 jest DOLNYM oszacowaniem, a nie kompletem.** Skan czyta wyłącznie literały
czytelne statycznie. Literałów `re.compile`, których pierwszy argument jest f-stringiem,
sklejeniem albo zmienną, jest pod `tools/` **10** i skan nie wie, co w nich stoi.
Czytelnych jest **184**, więc niewidoczne to **5,2 %** populacji. Liczba niewidocznych
nie jest domysłem — stoi w wyjściu skanu z adresami.

## 2. Jedyne żywe rozcięcie: `5400088` wycięte z `5400088,438`

`ADRES_NIE_TWIERDZENIE` ma alternatywę `\b[0-9a-f]{7,40}\b`, która ma łapać skrót
commita. W `reports/mutation-triage-wczytywanie.md` stoi para współrzędnych
Lamberta `(150000,013, 5400088,438)`. Siedmiocyfrowa część całkowita `5400088`
składa się z samych znaków legalnych w zapisie szesnastkowym, a przecinek jest dla
`\b` granicą słowa — więc wzorzec wycina ją ze środka liczby i zostawia `,438`.

Przepisanie tego wzorca jest **poza zakresem** tej pozycji: każdy z siedmiu jest
osobną zmianą zachowania bramki, która go używa. Rozcięcie jest tu **przybite
co do adresu i co do tokenu**, a nie naprawione.

## 3. Kryterium rozcięcia — i dlaczego pierwsze było błędne

Pierwsza wersja kryterium brzmiała „sąsiad trafienia z którejkolwiek strony jest
cyfrą, przecinkiem albo kropką" — warunek przepisany wprost z granic, które 6.D275
wstawiło. Dał **5942** trafień na samym `_DATA_PL` i czytał się jak katastrofa.
Był fałszywy: flagował poprawnie dopasowaną datę `04.09.2026` tylko dlatego, że po
niej stoi przecinek **zdaniowy**.

Kryterium poprawione: trafienie rozcina liczbę, gdy któraś jego granica wypada
**ściśle wewnątrz** maksymalnego tokenu `\d+(?:[.,]\d+)*`. Granica równa krawędzi
tokenu rozcięciem nie jest. Sprawdzone na przypadku, który pozycję wywołał, **zanim**
policzyłem sumę: na ciągu `0,090 / 0,087 / 0,085 s` stary wzorzec daje **2** rozcięcia,
naprawiony — **0**, a poprawna data z przecinkiem po niej — **0**.

## 4. Pole „Weryfikacja" tej pozycji twierdzi nieprawdę o kierunku — zmierzone

Pole zapowiadało: „przywrócenie `\b` w `SMIECI_W_PROZIE` ma zapalić bramkę — dziś
zapala ją tylko liczba populacji, i to przypadkiem, bo urwane człony akurat ją
podnosiły".

Zmierzone na kompletnej kopii drzewa sprzed tej pozycji, z mutacją przywracającą `\b`:

```
19/19 przeszło, kod 0
```

Bramka nie zapala się **wcale**. Powód jest mechaniczny i odwrotny do zapisanego:
urwane człony populację **obniżały**, a nie podnosiły. `\b\d+\s*/\s*\d+\b` na ciągu
`0,090 / 0,087 / 0,085` wycina dwa dłuższe kawałki i zostawia dwie liczby (`0`, `085`);
wersja naprawiona nie wycina nic i zostawia trzy (`0,090`, `0,087`, `0,085`). Zmierzona
populacja `gole_w_prozie_pomiarowej`: **259** na drzewie roboczym wobec **247** na
zmutowanej kopii. `MAX_GOLYCH_W_PROZIE_POMIAROWEJ` jest zapadką **górną**, więc spadek
przechodzi ją celująco — to ten sam kształt co 6.D27, tylko od strony populacji.

Pola nie poprawiam po fakcie; zapisuję rozjazd, bo rozjazd jest informacją.

## 5. Kontrole

**Kontrola negatywna.** Mutacja: `(?<![\d,.])\d+\s*/\s*\d+(?![\d,.])` z powrotem na
`\b\d+\s*/\s*\d+\b`, na **kompletnej** kopii drzewa (`tools`, `src`, `tests`, `docs`,
`reports`, `data`, `.gitignore`, `.github`, `CLAUDE.md`, `doctor.sh` — 211 plików `.py`,
397 raportów), `__pycache__` czyszczony przed przebiegiem (6.D102). Wynik:

```
FAIL test_ile_wzorcow_rozcina_dzis_liczbe_na_zywym_drzewie
FAIL test_ile_wzorcow_stawia_granice_przy_cyfrze_i_w_ilu_plikach
FAIL test_komplet_granic_przy_cyfrze_zgadza_sie_z_drzewem
2/5 przeszło
```

Licznik żywych rozcięć skacze z **1** na **36**. Zgłoszone są m.in. `0 / 1500` wycięte
ze środka `900,0` i `0 / 68` ze środka `150,0` — dokładnie kształt z 6.D275, na innych
liczbach. Zieleń zostaje na obu kontrolach przyrządu, i tak ma być: mutacja nie rusza
ani sita granic, ani kryterium rozcięcia.

**Przyrząd sprawdzony na kopii, nie na zgodności z drzewem.** Mutacja weszła do kopii,
odczyt kopii się zmienił, odczyt drzewa roboczego nie, `git status --porcelain` pusty.

**Kontrola przyrządu — bramka złapała własną ślepotę.** Pierwsza wersja testu żywych
rozcięć brała z `SMIECI_W_PROZIE` indeksy 1 i 2, a wzorzec naprawiony przy 6.D275 stoi
pod indeksem 4. Kontrola negatywna dała wtedy **2** czerwienie zamiast **3** —
i to ona, a nie zielony zestaw, pokazała, że bramka jest ślepa na przypadek, który
pozycję wywołał. Indeks dopisany, kontrola powtórzona.

**Kontrola przyrządu na sicie.** `\bkod\s+\d+(?![\d,.])` ma `\b` przy literze `k`
i na listę **nie trafia**. `\bMB-\d+\b` trafia wyłącznie granicą za `\d+`, a nie tą
przed literą `M`. Oba kształty stoją w żywym drzewie obok siebie.

**Przewidywania spisane przed przebiegiem — cztery z siedmiu nietrafione:** liczbę L1
przewidziałem większą niż 7 (jest dokładnie 7), L2 przewidziałem jako mniejszość
(jest 7 z 7), czerwień kontroli negatywnej na drzewie sprzed pozycji (jest zieleń,
§4), a liczbę czerwieni po dołożeniu bramki na 3 przy pierwszym podejściu (były 2, §5).

## 6. Samozwrotność jest tu WIDOCZNA, a nie ukryta

Skan znajduje `\b` przy cyfrze także we własnych atrapach kontroli przyrządu tego
modułu — słusznie, bo one naprawdę takie granice mają. Wliczenie ich do liczby
nagłówkowej byłoby mierzeniem własnego przyrządu, więc atrapy stoją w zbiorze
**przybitym** (żeby nie mogły zniknąć po cichu), a **poza** liczbą `WZORCOW_POZA_TA_BRAMKA`.
Odejmowanie jest jawne i pilnowane osobnym testem.

## 7. Co zauważyłem przy okazji, a czego nie tknąłem

1. **Populacja `gole_w_prozie_pomiarowej` nie ma podłogi.** Jest podłoga na zdania
   (`MIN_ZDAN_POMIAROWYCH`), ale na samą populację gołych liczb nie ma żadnej, więc
   każdy jej spadek przechodzi `MAX_GOLYCH_W_PROZIE_POMIAROWEJ` celująco. To jest ta
   sama dziura, którą mierzy 6.D278, widziana z drugiej strony. Nie łatam jej tutaj:
   zmiana tej zapadki jest wprost poza zakresem 6.D277.
2. **Dziesięć literałów `re.compile` jest dla każdego takiego skanu niewidzialnych.**
   Nie tylko dla tego: żaden skan czytający literały nie powie, co stoi w f-stringu
   składanym z wartości. Zapisane jako dolne oszacowanie, nie zamaskowane.
3. **`ADRES_NIE_TWIERDZENIE` jest sumą dziewięciu alternatyw w jednym literale.**
   Klucz `(plik, wzorzec)` traktuje go jako jeden wpis, więc zmiana jednej alternatywy
   przestawia cały klucz i bramka to zgłosi jako „doszedł i zniknął" naraz. Kosztu tu
   nie ma, bo wpisów jest kilka, ale przy setkach ten kształt byłby mylący.
