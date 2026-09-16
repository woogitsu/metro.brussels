# 6.D251 — bramka na uproszczenie historii przy scalance

**16.09.2026**, na `a0dbd79`. Wejście: `tools/tests/test_report_claims.py`
(`data_stalej`, `data_raportu`), `tools/tests/test_suite_runtime_budget.py`
(`STALYCH_Z_DATA_ISO`), `reports/6d249-datowanie-gubilo-commit-na-scalance.md`.
Wyjście: trzy bramki na prawdziwym repozytorium próbnym z prawdziwym
`git merge --no-ff`, przeliczona zapadka, ten raport.

## 1. Czego pilnuje i dlaczego 6.D249 tego nie postawiło

6.D249 naprawiło usterkę (`git log -1 -G<def> -- <pliki>` UPRASZCZA historię na
commicie scalenia, więc `data_stalej` wskazywała commit, który wniósł RAPORT,
zamiast tego, który zmienił STAŁĄ) i **świadomie nie postawiło bramki**, z powodem
zapisanym wprost: wymagała repozytorium próbnego z prawdziwym scaleniem, a `main`
był wtedy czerwony. Ta pozycja domyka tamten dług.

Bramki są trzy i każda pyta o co innego:

| bramka | przedmiot |
|---|---|
| `test_datowanie_stalej_na_SCALANCE_wskazuje_commit_KTORY_STALA_ZMIENIL` | poprawka 6.D249 działa |
| `test_datowanie_RAPORTU_na_scalance_nie_liczy_scalenia_ktore_raport_PRZENIOSLO` | **druga strona asymetrii** — `--full-history` NIE ma iść do `data_raportu` |
| `test_scalanka_NIE_TREESAME_usterki_NIE_POKAZUJE_i_dlatego_fixture_jest_taki` | kształt fixture'u jest WYMAGANY, nie przypadkowy |

Trzecia jest kontrolą przyrządu i to ona odróżnia tę bramkę od życzenia: na scalance
**nie**-TREESAME obie wersje `git log` odpowiadają **tak samo**, więc fixture o
„oczywistej" topologii nie pokazałby usterki wcale. Kształt jest sprawdzany
porównaniem drzew, a nie zakładany.

## 2. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Baza: **28/28**. Po każdej kontroli przywracanie **z kopii**, `md5sum -c` OK,
`__pycache__` czyszczony przed każdym przebiegiem. Każda mutacja niesie asercję,
że NAPRAWDĘ się zastosowała — patrz §4.

| | mutacja | PRZEWIDZIANE | ZMIERZONE |
|---|---|---|---|
| KN-1 | `--full-history` zdjęte z `data_stalej` | 27/28, czerwona bramka stałej | **27/28**, dokładnie ta, z datą wskazanego commitu w komunikacie |
| KN-2 | `--full-history --simplify-merges` — **KOD POPRAWNY** | 28/28 | **28/28** |
| KN-3 | `HOME` z `merge.verifySignatures = true` — **KOD POPRAWNY** | 28/28 | **28/28** |

## 3. Dwie usterki TEJ bramki, znalezione i naprawione przed wejściem

**(a) Fałszywy alarm na kodzie POPRAWNYM (6.D27).** Pierwsza wersja odejmowała
z wywołania **jedną flagę**, a `--simplify-merges` **sama implikuje pełną historię**.
Zapis `--full-history --simplify-merges` jest równoważny i daje tę samą poprawną
odpowiedź — a bramka się na nim zapalała, bo pierwsza asercja przechodziła (kod
odpowiada dobrze), a padała dopiero połowa odtwarzająca usterkę. Bramka stała więc
na ZAPISIE, nie na ZACHOWANIU. Poprawka: odejmowana jest **rodzina**
`BEZ_UPRASZCZANIA = ("--full-history", "--simplify-merges", "--sparse", "--dense")`.
Zmierzone przed poprawką: **23/24**, czyli czerwień na pracy poprawnej.

**(b) Trzecia dziura konfiguracji gita, nieobjęta pinem z 6.D248.**
`merge.verifySignatures = true` w cudzej konfiguracji wywraca `git merge --no-ff`
kodem **128** — a pin `commit.gpgsign` go **nie łapie**, bo to inny klucz i inna
operacja (PISANIE podpisu wobec SPRAWDZANIA cudzego). Zmierzone przed poprawką:
**21/24**. Do fixture'u dopisany `merge.verifySignatures=false`, a `core.hooksPath`
przestawiony z nieistniejącego katalogu na `os.devnull` — fixture sam zapisuje pliki
pod swoim katalogiem, więc „na pewno pusty katalog" nie jest założeniem, które da się
utrzymać, a `/dev/null` katalogiem nie będzie nigdy.

## 4. Czego nauczyła własna pomyłka w kontrolach

Dwie wcześniejsze mutacje w tej sesji (przy 6.D250) **nie zastosowały się** — wzorzec
nie trafiał — a przebieg dawał wynik **nieodróżnialny od kontroli przechodzącej
legalnie**. Od tego czasu każda mutacja niesie asercję, że wiersz naprawdę się zmienił,
i wypisuje `mutacja ZASTOSOWANA` przed przebiegiem. Wszystkie trzy kontrole tej pozycji
przeszły przez tę procedurę.

## 5. Weryfikacja

```
KOD=0
  2530/2530 przeszło
  RAZEM <czas> s, 2530 testów, 127 modułów
```

Zapadki: `STALYCH_Z_DATA_ISO` stoi teraz na **11**, o cztery wyżej (cztery nowe stałe
z datą ISO w literale, same skalary, więc `KONTENEROW_Z_DATA_ISO` bez zmian) — razem
z przepisaną prozą przy stałej. `ASERCJI_NAPISOWYCH_RAZEM` **bez zmian**: jedenaście
nowych asercji stoi na ZACHOWANIU (równość dat z prawdziwych funkcji, tożsamość drzew
z gita, werdykt `zdanie_z_dnia_pomiaru`), ani jedna na napisie. `MIN_REPORTS` rośnie
o jeden za ten raport.

**Obie te liczby są tu zapisane tak, a nie inaczej, z powodu zmierzonego przed chwilą.**
Pierwsza wersja tego akapitu podawała obie zapadki w postaci „stare stanowisko strzałka
nowe" oraz przyrostem ze znakiem plus. Czytnik twierdzeń przeczytał je jako twierdzenia
o wartości STAREJ i o jedynce — bierze **pierwszą liczbę stojącą po nazwie**, a w obu
tych zapisach pierwsza liczba nie jest wartością bieżącą. Przykładu nie cytuję tu
dosłownie i to też jest wynik pomiaru: cytat sam w sobie zapala bramkę, bo dla czytnika
jest nieodróżnialny od twierdzenia — akapit opisujący pułapkę wpadał w nią przy
pierwszym przebiegu. Ta sama granica zapaliła się dziś przy 6.D228 na zdaniu
„`NAZWA` … 6.D216", gdzie cyfrę wzięła z numeru pozycji. Poprawka należy do maski
czytnika, nie do pamięci autorów, i jest osobną pozycją — tu obchodzę ją świadomie,
stawiając wartość bieżącą jako pierwszą.

## 6. Czego świadomie nie zrobiłem

- **Nie tknąłem `data_stalej` ani `data_raportu`** — poprawka 6.D249 jest w `main`
  i jest poprawna; ta pozycja stawia na nią bramkę, nic więcej.
- **Nie dopisałem wiersza 6.D249 do `docs/TASKS.md`**, choć go tam nie ma i jest to
  prawdziwa luka: praca scalona, a kolejka milczy. To osobne zadanie — dopisanie go
  tutaj byłoby drugą pozycją w jednym commicie (§4.10).
- **Nie zrobiłem inwentarza pozostałych fixture'ów** wołających `git merge` pod kątem
  `merge.verifySignatures`. Ta bramka ma pin; ile innych go potrzebuje, nie policzyłem.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

- **`data_raportu` jest wobec cudzej konfiguracji delikatniejsze, niż wygląda.**
  Pin `log.showSignature=false` z 6.D250 dotyczy wywołań w kodzie; fixture przypina
  konfigurację lokalnie w repozytorium PRÓBNYM. Repozytorium GŁÓWNE czyta natomiast
  konfigurację właściciela — i to jest kod produkcyjny, nie bramka. Dziś chroni je
  `--no-show-signature` na obu wywołaniach, ale gdyby ktoś dopisał trzecie bez flagi,
  bramka z 6.D250 to złapie, a ta nie.
- **Proza w `test_assertion_gate.py` rozjechała się ze stałą**: docstring
  `test_ile_bramek_stoi_na_NAPISIE_a_nie_na_ZACHOWANIU` mówi trzy razy „849 asercji",
  gdy stała stoi dziś znacznie wyżej. Ktoś podnosił zapadkę i nie przepisał prozy —
  ta sama rodzina, którą `test_report_claims` pilnuje w `reports/`, ale której nikt nie
  pilnuje w docstringach `tools/`. Kandydat na osobną pozycję.
- **Fixture jest wielokrotnego użytku**: odtwarza scalankę w ~1,5 s i przyjmuje
  `main_podnosi_stala` jako parametr, więc następne pytanie o zachowanie `data_*`
  na commicie scalenia nie wymaga pisania go od nowa.
