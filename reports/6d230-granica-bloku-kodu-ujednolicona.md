# 6.D230 — dwa czytniki tego samego katalogu, dwie granice bloku kodu

**16.09.2026**, na `d971310`. Wejście: `tools/tests/test_report_claims.py`
(`claims_in_reports`, `wystapienia_w_jednych_grawisach`, `FENCE`),
`test_backlog.CLAIM_W_JEDNYCH_GRAWISACH`, `reports/*.md`. Wyjście: ujednolicona granica,
bramka na wejściu syntetycznym, przepisany komentarz przy stałej, ten raport.

## 1. Teza pozycji — POTWIERDZONA własnym pomiarem

Dwa czytniki chodzą po tym samym katalogu i **różnią się granicą bloku ogrodzonego**:

```
wystapien ksztaltu `NAZWA = N` w reports/:   58
  POZA blokami kodu:                          55
  W BLOKACH kodu:                              3
     6d196-…md w. 61  ZDAN_RODZINY_RAZEM = 19
     6d196-…md w. 73  ZDAN_RODZINY_RAZEM = 19
     6d196-…md w. 74  ZDAN_BEZ_POKRYCIA  = 10
```

`claims_in_reports()` bloki **pomija** — z powodem zapisanym przy `FENCE`: to cytaty,
nie twierdzenia, a pierwsza wersja tamtej bramki wywróciła się na raporcie cytującym
wyjście własnej kontroli negatywnej. `wystapienia_w_jednych_grawisach()` bloków **nie
pomijało**, więc zacytowanie cudzego twierdzenia w jego własnym kształcie było dla niego
twierdzeniem autora.

**Uwaga o moim własnym przyrządzie, bo jest pouczająca.** Pierwsza sonda, którą
napisałem, dała „0 w blokach" — i było to nieprawdą: pętla miała `if hasattr(…) else []`,
a nazwa wzorca była inna (stoi w `test_backlog`, jest POŻYCZONA, nie przepisana). Sonda,
która nie mierzy nic, jest **nieodróżnialna** od sondy, która zmierzyła zero. Dopiero
druga, wołająca prawdziwy `BL.CLAIM_W_JEDNYCH_GRAWISACH`, dała 58/55/3.

## 2. Ujednolicenie — w stronę POMIJANIA, i co to kosztuje

Granica jest teraz ta sama po obu stronach: oba czytniki pomijają bloki ogrodzone.
Populacja `wystapienia_w_jednych_grawisach` spada **58 → 55**, przy podłodze **40**,
czyli zapas rośnie z 18 do 15 — podłoga nadal ma z czego schodzić.

**Cena jest zmierzona i wypisana:** twierdzenie autora napisane naprawdę **wewnątrz**
bloku kodu ucieka teraz spod bramki. To ta sama dziura, którą `claims_in_reports` ma
**od początku i świadomie**, z powodem zapisanym przy `FENCE`. Dzisiejsza cena to
**3 wystąpienia, wszystkie cytaty, wszystkie w jednym raporcie**.

## 3. Ostrzeżenie z pola pozycji okazało się NIEPRAWDZIWE

Pole mówiło: „pominięcie bloków zdejmuje spod pomiaru kształt, na którym 6.D209 oparło
werdykt". Sprawdzone — wszystkie **cztery** wystąpienia z `CYTATY_NIE_TWIERDZENIA`
**oraz** wszystkie cztery ich cytaty w raporcie samozwrotnym stoją **POZA** blokami.
Baza dowodowa 6.D209 nie traci ani jednego wystąpienia, a wyłączenie samozwrotne zostaje
nośne. Ujednolicenie jest więc możliwe bez utraty tamtego werdyktu — ale **nie było to
oczywiste** i pole słusznie kazało to sprawdzić przed zmianą.

## 4. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Baza: **29/29**. Każda mutacja niesie asercję, że się zastosowała (patrz §1 — sonda,
która nic nie zmieniła, wygląda jak sonda, która przeszła). Przywracanie z kopii,
`md5sum -c` OK.

| | mutacja | PRZEWIDZIANE | ZMIERZONE |
|---|---|---|---|
| KN-1 | granica cofnięta do dawnej — **konfiguracja, DLA KTÓREJ bramka powstała** | czerwone | **28/29**, nowa bramka, komunikat o rozjeździe granicy |
| KN-2 | `claims_in_reports` przestaje pomijać bloki | czerwone | **26/29** — nowa bramka **plus DWIE istniejące** |
| KN-3 | czytnik oślepiony (`return []`) | czerwone na LICZNIKU OBROTÓW | **27/29**, licznik obrotów + podłoga 40 |
| KN-4 | **kosmetyczna** edycja `6d196`, zero liczb — **kontrola DODATNIA** | zielone | **29/29** |

**KN-2 pokazuje szkodę, a nie tylko rozjazd.** Zdjęcie pomijania po drugiej stronie
zapala natychmiast dwie istniejące bramki, które zaczynają czytać **prawdziwe cytowane
wartości** jako twierdzenia:

```
FAIL test_a_number_quoted_inside_a_code_block_is_not_a_claim:
     [('M7_WIDTH_M', '2,70'), ('M7_WIDTH_M', '9,99'), ('CLEARANCE_M', '0,30')]
```

Tak wygląda świat bez reguły `FENCE`.

**Ten akapit sam wpadł w granicę, którą opisuje §8, i zostaje to zapisane.** W pierwszej
wersji wypisałem te pary w zdaniu, POZA blokiem — i bramka `test_ksztalt_w_jednych…`
zapaliła się na moim własnym raporcie, słusznie: poza blokiem kształt `NAZWA = N` nadal
jest twierdzeniem, bo ta łatka domyka **wyłącznie** cytat w bloku. Przeniesienie
przykładu do bloku jest więc nie kosmetyką, tylko korzystaniem z reguły, którą ta pozycja
wprowadza.

**KN-3 zapala LICZNIK OBROTÓW i to jest treść, nie ozdoba.** Pusty czytnik odpowiada
„nic nie znalazłem", co bez tej asercji czytałoby się jak zgoda obu stron. Bramka żąda
więc, żeby czytnik widział człon **spoza** bloku — inaczej warunek o równości granic nie
mówi o niczym.

**KN-4 jest kontrolą, która uzasadnia całą pozycję.** Edycja kosmetyczna `6d196` —
jeden komentarz HTML, **ani jednej liczby** — jest dziś zielona. Przed ujednoliceniem ta
sama edycja dawała **czerwień**: `data_raportu` liczy się od ostatniego ruszenia PLIKU,
więc dotknięcie go przedatowywało raport i datowanie przestawało zwalniać trzy cytaty
z bloku. **Ochrona stała więc na tym, że nikt nie tknie tego pliku** — a to nie jest
ochrona, tylko zbieg okoliczności.

## 5. Bramka jest NIEZALEŻNA OD KATALOGU i to jest wybór z pomiaru

Bramka oparta na liczbach z `reports/` **nie jest możliwa**: oba czytniki są nad
katalogiem zielone i były zielone także wtedy, gdy granice miały różne. Taka bramka
mierzyłaby **wielkość katalogu**, nie granicę. Stoi więc na **wejściu syntetycznym** —
jeden dokument próbny niosący oba kształty raz w bloku i raz poza nim, przepuszczony
przez **oba** czytniki, plus licznik obrotów i warunek, że dawna granica musi próbkę
przeciąć. Precedens jest w tym samym module (`test_twierdzenie_DOPISANE_do_sekcji…`).

## 6. Weryfikacja

```
KOD=0
  <pełny zestaw — liczby z przebiegu wyłącznego>
```

Moduły: `test_report_claims.py`, `test_backlog.py`, `test_assertion_gate.py`,
`test_tree_walks.py`, `test_prose_counts.py`, `test_report_hygiene.py` — **150/150**.

Zapadki: **żadnej nowej**. `MIN_WYSTAPIEN_W_JEDNYCH_GRAWISACH` zostaje na **40** —
ta pozycja populację **obniża** (58 → 55), a nie podnosi, więc podniesienie podłogi
zamieniłoby ją w równość na rosnącym katalogu i przypięło liczbę, którą sama ta zmiana
zmniejsza. `ASERCJI_NAPISOWYCH_RAZEM` bez zmian — asercje nowej bramki stoją na
równości list zwracanych przez czytniki, nie na napisach. `MIN_REPORTS` o jeden.

## 7. Czego świadomie nie zrobiłem

- **Nie przywróciłem grawisów w `6d219`**, choć po tej łatce byłoby to już legalne —
  to zmiana tekstu raportu, nie kodu (6.D108).
- **Nie podniosłem `MIN_WYSTAPIEN_W_JEDNYCH_GRAWISACH`** — powód w §6.
- **Nie dodałem podłogi na liczbę wystąpień W BLOKACH** (kandydat: „granica nadal ma co
  rozdzielać"). Cała dzisiejsza trójka stoi w **jednym** raporcie, więc legalne
  przepisanie tego raportu zbiłoby ją do zera i zapaliło bramkę **na pracy poprawnej** —
  dokładnie to, co 6.D27 każe wyłączyć, a nie naprawiać.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- **Powierzchnia, której ta łatka NIE domyka:** cytat cudzego twierdzenia w kształcie
  `` `NAZWA = N` `` **poza** blokiem nadal zapala `test_ksztalt_w_jednych_grawisach…`.
  Łatka domyka wyłącznie cytat **w bloku** — i tak deklaruje, ale warto to nazwać.
- **Asercja równości w nowej bramce zapala się na poszerzeniu wzorca `CLAIM`**, czyli na
  zmianie sensownej samej w sobie; komunikat mówi wtedy o granicy, choć granica jest
  w porządku. Rodzina 6.D27, ale łagodna: naprawa to jedna linia. Nie zmieniałem — to
  decyzja projektowa.
- **`MINIMUM_CLAIMS` w próbce syntetycznej jest nazwą PRAWDZIWEJ stałej drzewa.** Dziś
  nieszkodliwe, bo próbka niczego nie porównuje z kodem; nazwa spoza drzewa
  (np. `PROBKA_6D230`) byłaby odporniejsza.
