# 6.D200 — potrójny cudzysłów po małpie, i szesnaście metod, których nie widać

**13.09.2026**, na `fd238a5`. Wejście: `tools/tests/csharp_test_methods.py`
(`maska`, `_koniec_literalu`), `tools/tests/test_csharp_test_methods.py`,
`tests/Game.Tests/UiTextTests.cs`, `reports/6d188-czternascie-i-ani-jednego-jsona.md` §6.

## 1. Usterka istnieje dokładnie tam, gdzie pozycja ją wskazała — i o jedną postać dalej

`_koniec_literalu` liczyła cudzysłowy otwierające i przy trzech brała literał za
**surowy**, nie patrząc, czy przed nimi stoi `@`. W C# napisu surowego po `@` nie ma:
zapis werbatim otwarty uciekanym cudzysłowem ma treść `"a`, bo w werbatim para
cudzysłowów znaczy jeden. Czytnik szukał więc domknięcia potrójnym cudzysłowem,
którego w pliku nie ma, i maskował **wszystko do końca pliku**.

Zmierzone na czterech postaciach, przed naprawą i po:

```
'x = @"""a"; {}'   ->  przed: 'x =           '   po: 'x =       ; {}'
'x = @"a"""; {}'   ->  przed: 'x =       ; {}'   po: 'x =       ; {}'
'x = """a"""; {}'  ->  przed: 'x =        ; {}'  po: 'x =        ; {}'
'x = $@"""a"; {}'  ->  przed: 'x =            '  po: 'x =        ; {}'
```

**Czwarta postać nie stała w pozycji i jest ustaleniem tego zadania:** `$@"""` i `@$"""`
to napis werbatim **interpolowany**, więc miał tę samą usterkę. Naprawa (`and not
verbatim`) obejmuje obie, bo flaga `verbatim` bierze się z `@`, nie z kolejności
przedrostków. `$"""…"""` — surowy interpolowany, bez `@` — **zostaje** w gałęzi surowej
i to jest poprawne.

## 2. Ile to kosztuje: JEDNA linia, SZESNAŚCIE metod, i ten sam plik co przy 6.B28

Na dzisiejszym drzewie naprawa **nie zmienia nic** i to jest zmierzone, nie założone:

```
metod widzianych DZIS (po naprawie):  825
metod widzianych PRZED naprawa:       825
plikow o ROZNEJ masce:                0
```

Zapis `@"""` jest w `tests/` i `src/` **jeden** i stoi w **komentarzu** —
`tests/Game.Tests/UiTextTests.cs:2938`, w akapicie opisującym tę właśnie usterkę.
Komentarz czytnik pochłania **przed** gałęzią literału, więc do zepsutej gałęzi nigdy
nie dochodzi. Obejście z 6.D188 przepisało jedyny żywy zapis na zwykły napis
z uciekanymi cudzysłowami.

**Dlatego wartość naprawy trzeba było ZMIERZYĆ NA WEJŚCIU, a nie na drzewie.** Dopisanie
jednej takiej linii do `tests/Sim.Tests/ServiceDayTests.cs`:

```
Z linia @""" W KODZIE:
   czytnik NAPRAWIONY widzi metod: 825
   czytnik SPRZED naprawy widzi :  809
   w samym ServiceDayTests.cs: naprawiony 16 / zepsuty 0
```

**Szesnaście metod z szesnastu — cały plik.** I jest to **ten sam plik i ta sama
liczba**, co przy 6.B28, gdzie liczenie klamr po surowym tekście dawało z 16 metod zero,
a bramka meldowała mimo to „0 nieuruchamianych". Ta sama wyrocznia zepsuta w stronę
„wszystko w porządku", trzecim już wejściem.

## 3. Liczba w drzewie NIE jest dowodem naprawy i stoi to napisane w bramce

`ZAPISOW_WERBATIM_POTROJNYCH = 1` przybija korpus, nie zachowanie: gałąź naprawiona
**nie jest przez drzewo ćwiczona ani razu**, więc zepsucie jej z powrotem tej liczby nie
ruszy. Potwierdzone kontrolą: KN-1 (cofnięcie naprawy) zapala **wyłącznie** kontrolę
syntetyczną, a spis i cała reszta zestawu przechodzą.

Dowodem jest więc `test_maska_ROZROZNIA_werbatim_od_surowego_na_obu_galeziach`, sprawdzający
**cztery postacie razem w jednym teście** — bo każda osobno przeszłaby u czytnika, który
myli je w tę samą stronę. Spis pilnuje czego innego: gdyby taki zapis wszedł do **kodu**,
ma to zostać zauważone, bo **każdy inny czytnik w tym drzewie ma tę samą gałąź**
(`maska` w `UiTextTests.cs`, `Literaly`, `KodLeksykalnie` z 6.D199) i żaden nie został
naprawiony.

## 4. Pisząc o tym w Pythonie wpadłem w tę samą pułapkę

Pierwsza wersja obu nowych testów miała docstringi otwarte potrójnym cudzysłowem,
a w treści cytowała zapis, o którym mówi. Wynik:

```
FAIL <import>test_csharp_test_methods: SyntaxError: invalid character '—' (U+2014), line 253
```

Docstring zamknął się na pierwszym cytacie, a reszta akapitu została kodem. **Ta sama
klasa błędu, tylko w drugim języku:** czytnik — tu parser Pythona — zobaczył domknięcie
tam, gdzie autor widział treść. Docstringi zamieniłem na komentarze `#`, bo ucieczka
w docstringu robi tekst nieczytelnym dokładnie w miejscu, które ma być czytelne.

## 5. Sześć kontroli negatywnych, baza 9/9

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | naprawa cofnięta (`and not verbatim` zdjęte) | 8/9 |
| KN-2 | pętla po postaciach obiega raz zamiast czterech | 8/9 |
| KN-3 | oczekiwana maska zmieniona na zepsutą | 8/9 (na RÓWNOŚCI) |
| KN-3b | czytnik zepsuty **i** oczekiwanie dopasowane — jedna zmienna | 8/9 (na STRAŻNIKU KLAMR) |
| KN-4 | korpus spisu zwężony do `tests/` | 8/9 |
| KN-5 | `@"""` dopisane do KODU (kontrola przyrządu) | 8/9 |

`md5sum -c` po każdej: `OK`. Ani jedna zielona.

**KN-3b jest tu konieczna, nie ozdobna.** KN-3 zapala się na równości, więc nie mówi nic
o drugiej połowie testu — strażniku żądającym, żeby oczekiwana maska **miała klamry**.
Dopiero zepsucie obu rzeczy naraz (czytnika i oczekiwania) przepuszcza równość i zostawia
strażnika samego. To ten sam wzorzec, co KN-6b przy 6.D199.

## 6. Czego świadomie nie zrobiłem

- **Zapisu w `UiTextTests.cs` nie przywróciłem na werbatim** — pole „Poza zakresem"
  mówi, że obejście zostaje. Zostaje też dlatego, że przywrócenie byłoby jedynym żywym
  wystąpieniem gałęzi i ćwiczyłoby ją **przypadkiem**, a ćwiczy ją kontrola syntetyczna
  **umyślnie**.
- **`_cialo_klasy` nietknięte** — też z pola „Poza zakresem".
- **Pozostałych czytników nie naprawiałem.** `maska` w `UiTextTests.cs`, `Literaly`
  i `KodLeksykalnie` mają tę samą gałąź; są w innym języku i innym korpusie, a pozycja
  wskazywała czytnik Pythona. Zapisane niżej.

## 7. Zauważone po drodze, nie tknięte

- **Trzy dalsze czytniki w drzewie mają tę samą gałąź i żaden nie jest naprawiony:**
  `Literaly` (`PrefiksLiteralu`/`CzytajLiteral`, 6.D182), `KodLeksykalnie` (6.D199) —
  oba w `tests/Game.Tests/UiTextTests.cs` — oraz `czytnik.maska` używane przez bramki
  Pythona po stronie `src/`. Naprawa zrobiona tu jest **jednym wierszem**; pytanie, ile
  z tamtych trzech w ogóle może trafić na `@"""`, nie zostało zmierzone.
- **`$"""…"""` (surowy interpolowany) nie występuje w drzewie ani razu.** Gałąź surowa
  jest więc ćwiczona wyłącznie przez zapisy bez przedrostka — a tych jest 30 par
  potrójnych cudzysłowów w `tests/` i `src/`.
