# 6.D237 — bramka czytała PIERWSZY argument, a zestaw wykonuje WSZYSTKIE

**Data:** 17.09.2026 · **Gałąź:** `claude/6d237-ogon-wywolania` · **Baza:** `222bd37`

## 1. Co było nieprawdą

`MODULE_CALL` w `tools/tests/test_field_paths.py` brał z wywołania `test_all.py`
wyłącznie pierwszy argument, a komentarz przy stałej uzasadniał to zgodnością
z narzędziem: „`test_all.py` kończy się na `main(sys.argv[1]) if len(sys.argv)>1
else main()`, więc drugiego argumentu nie czyta nikt".

**Nie było to prawdą od 11.09.2026.** Komentarz powstał w 6.D101 (10.09.2026),
a strażnik `__main__` zmieniono w 6.D114 na `main(sys.argv[1:])`. Zmierzone:

```
$ python3 tools/tests/test_all.py test_crs.py test_lod.py
  82/82 przeszło
  RAZEM ..., 82 testów, 2 modułów
```

Obie nazwy zostają wykonane. Skan mówił więc o wywołaniu, którego nie ma.

## 2. Ile to kosztowało — PODSTAWIENIE wzorca, nie odejmowanie

Ten sam czytnik nad tym samym drzewem, raz z dawną postacią jednoargumentową
i raz z dzisiejszą:

```
stary wzorzec: 145  nowy: 164
DOSZLO 19 [('6.D138','test_braking.py'), ('6.D144','test_assertion_gate.py'),
 ('6.D151','test_tree_walks.py'), ('6.D162','test_timing_record.py'),
 ('6.D163','test_suite_runtime_budget.py'), ('6.D192','test_suite_runtime_budget.py'),
 ('6.D193','test_field_paths.py'), ('6.D194','test_timing_record.py'),
 ('6.D203','test_assertion_gate.py'), ('6.D204','test_module_entrypoints.py'),
 ('6.D205','test_timing_record.py'), ('6.D206','test_readme_claims.py'),
 ('6.D207','test_prose_counts.py'), ('6.D209','test_backlog.py'),
 ('6.D216','test_report_hygiene.py'), ('6.D218','test_tree_walks.py'),
 ('6.D228','test_backlog.py'), ('6.D228','test_report_hygiene.py'),
 ('6.D230','test_backlog.py')]
UBYLO  0 []
```

Dziewiętnaście nazw było niewidzialnych, żadna nie ubyła.

**Pomiar tej pozycji z 16.09.2026 dawał 156 przy bazie 140, czyli o trzy mniej,
i nie jest to rozbieżność pomiaru.** Tamto drzewo miało 6.D228 i 6.D230 jako bloki
OTWARTE; scalenie #644 i #646 przeniosło je do WYKONANYCH razem z ich płotkami.
Wartość jest przeliczona na dzisiejszym drzewie, a nie przepisana z tamtego pomiaru.

## 3. Rozbiór jest PREFIKSOWY i to jest wybór z pomiaru, nie gust

Postać „wszystkie tokeny z ogona", bez zatrzymania, jest o jedną literę krótsza.
KN-2 pokazała, co robi:

```
FAIL test_zadne_pole_nie_wola_modulu_spoza_drzewa: pole zadania woła moduł,
  którego `test_all.py` nie zna: [('6.D26','Weryfikacja','grep'),
  ('6.D26','Weryfikacja','RAZEM'), ('6.D26','Weryfikacja','done'),
  ('6.D44','Weryfikacja','echo'), ('6.D45','Weryfikacja','echo'),
  ('6.D63','Weryfikacja','echo'), ('6.D234','Weryfikacja','dotnet'),
  ('6.D234','Weryfikacja','test')]
```

Osiem fałszywych zgłoszeń na poleceniach **poprawnych** — `| grep RAZEM`,
`; echo "kod: $?"`, `&& dotnet test`. To jest 6.D27 w czystej postaci: taka bramka
zostaje wyłączona, nie naprawiona. Postać prefiksowa daje zero.

## 4. Znalezisko, którego zlecenie nie przewidywało: DRUGA KOPIA ROZBIORU

**KN-3 obaliła moje przewidywanie i to jest najważniejszy wynik tej pozycji.**

Przewidziałem, że oślepienie czytnika (`return []`) zapali dwie bramki: równość
`WYWOLAN_W_WYKONANYCH` i podłogę `MIN_NAZW_Z_DALSZEGO_ARGUMENTU`. Zmierzone:
**dwanaście bramek — a podłoga NIE BYŁA jedną z nich.**

Powód: `nazwy_z_dalszego_argumentu()` nie wołało `module_names()`, tylko niosło
**własną kopię** tej samej pętli rozbioru. Podłoga istnieje dokładnie po to, żeby
łapać zwężenie tego rozbioru — i czytała kopię, której zwężenie nie dotyczyło.

**Podłoga pilnująca czytnika, którego nie używa, jest napisem.** To ta sama reguła,
co 6.D213: pożycza się czytnik, nie przepisuje.

Naprawione w tej samej pozycji: rozbiór ogona wydzielony do `_rozbior_ogona()`,
jedynego w module; oba miejsca go wołają. Liczby bez zmiany — 19 i 164 przed
i po wydzieleniu, czyli refaktor jest zachowawczy.

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Populacja: 6 modułów czytających ten czytnik albo rejestr zapadek. **Baza 248/248.**
Każda mutacja niesie asercję, że się ZASTOSOWAŁA; po każdej przywracanie z kopii
i `md5sum -c`.

| mutacja | przewidziane | zmierzone |
|---|---|---|
| KN-1 `MODULE_CALL` cofnięty do jednego argumentu — konfiguracja, DLA KTÓREJ pozycja powstała | czerwone: równość + podłoga | **245/248** — równość, podłoga **i** kontrola przyrządu; przewidziałem dwie, zapaliły się trzy |
| KN-2 ogon BEZ zatrzymania prefiksowego | czerwone, licznik W GÓRĘ | **244/248**, 164 → **170**, osiem fałszywych zgłoszeń wymienionych z nazwy |
| KN-3 czytnik `module_names` oślepiony | czerwone: równość + podłoga | **236/248 — PRZEWIDYWANIE OBALONE:** dwanaście bramek, a podłogi WŚRÓD NICH NIE MA |
| KN-3b ten sam zabieg po wydzieleniu `_rozbior_ogona` | czerwone, podłoga WŚRÓD nich | **235/248**, trzynaście bramek — różnica to dokładnie ta podłoga |
| KN-4 **kontrola DODATNIA**: legalne jednoargumentowe wywołanie dopisane do bloku wykonanego | równość rusza, podłoga ZOSTAJE zielona | **246/248**; zmierzone wprost: adresy 410 → **411**, wywołania 164 → **165**, podłoga **19 bez zmian** |

**KN-3 i KN-3b razem są treścią**, nie parą przebiegów: różnią się WYŁĄCZNIE tym,
czy rozbiór stoi w jednym miejscu, czy w dwóch, i ta różnica jest widoczna jako
jedna bramka więcej. Bez KN-3 naprawa z §4 nigdy by nie powstała, bo wszystko
inne było zielone.

**KN-4 mówi dwie rzeczy i druga jest ważniejsza:** równość rusza się przy każdym
domknięciu (własność opisana przy stałej), ale podłoga **nie zapala się na pracy
poprawnej** — a bramka, która to robi, zostaje wyłączona (6.D27).

**Uwaga o czytaniu KN-4:** zestaw wypisał dwie czerwienie, nie trzy, bo asercja
o adresach stoi w tej samej pętli PRZED asercją o wywołaniach i przerywa iterację
pola. Ruch 164 → 165 jest zmierzony czytnikiem wprost, a nie wyczytany z komunikatu.

## 6. Zapadki

- `WYWOLAN_W_WYKONANYCH["Weryfikacja"]` 145 → **164**, przeliczone z drzewa.
- `MIN_NAZW_Z_DALSZEGO_ARGUMENTU` = **15** przy populacji **19**. Podłoga, nie równość,
  i liczona na blokach WSZYSTKICH: bloki wykonane tylko przybywają, więc równość
  kazałaby podnosić próg przy każdej domkniętej pozycji z wywołaniem dwuargumentowym;
  na blokach otwartych liczba malałaby od SPRZĄTANIA kolejki. Zapas 4 ma powód:
  populacja wędruje między blokami otwartymi a wykonanymi przy każdym scaleniu.
- `ZAPADEK_RAZEM` 58 → **59**, klasy 17/3/37/1 → **17/3/38/1**.
- `MIN_REPORTS` o jeden.

## 7. Czego NIE zrobiono

- **6.D238 nie wchodzi tą gałęzią**, choć pomiar obu pozycji przyszedł jedną łatką:
  obie ruszają `ZAPADEK_RAZEM`, więc jedno scalenie zostawiłoby drugą pozycję
  z liczbą nie do odtworzenia z jej własnego diffu (§4.10).
- **Nie tknięto pozostałych czytników ogona poza tym modułem** — pozycja pytała
  o `MODULE_CALL`, a przegląd innych skanów pod kątem drugiej kopii czytnika jest
  osobną pozycją; dzisiejsze znalezisko mówi tylko, że taka kopia bywa.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- Asercje w `test_ile_adresow_stoi_w_kazdym_z_trzech_pol_blokow_wykonanych` stoją
  w jednej pętli po polach, więc **pierwsza czerwień w polu zasłania dalsze**.
  Nie jest to usterka bramki — werdykt jest ten sam — ale komunikat mówi wtedy
  mniej, niż bramka wie, i przy KN-4 kosztowało to jeden dodatkowy pomiar.
- Dwie starsze podłogi tego modułu niosą zapasy wielokrotnie większe niż dzisiejsza:
  `MIN_WYWOLAN_W_WYKONANYCH` stoi na 80 przy populacji 164, a `MIN_MODULE_NAMES`
  na 60 przy populacji ponad 66. Czy są jeszcze nośne, jest pytaniem na pomiar,
  nie na poprawkę przy okazji.
