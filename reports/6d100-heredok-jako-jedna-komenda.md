# 6.D100 — pięć wierszy, które były jedną komendą

**Zmierzone 10.09.2026 na:** `e5c499e`, kontener tej sesji.
**Przyrząd:** `tools/tests/backlog_commands.py` (`commands`, `inventory`, `HEREDOC`),
`tools/tests/test_backlog_commands.py`, `git worktree` na `e5c499e` dla pomiaru
zachowania sprzed zmiany, `bash` dla sprawdzenia, czy złożona komenda daje się wkleić.

---

## 1. Liczby przed i po, policzone z drzewa

| | przed | po |
|---|---|---|
| bloków z polem „Weryfikacja" | 185 | 185 |
| komend w całym `docs/TASKS.md` | **324** | **320** |
| komend w bloku 6.A24 | **8** | **4** |

Zawyżenie wynosiło dokładnie cztery i całe pochodziło z jednego bloku: kolektor liczył
`python3 - <<'EOF'`, trzy wiersze ciała i `EOF` jako pięć osobnych komend zamiast
jednej.

Obie kolumny są pomiarem, nie przepisaniem. Kolumnę „przed" dał ten sam plik
`backlog_commands.py` uruchomiony na drzewie sprzed zmiany (`git worktree add --detach`
na `e5c499e`).

## 2. Ile jest heredoków — i ile ich nie ma

Pole „Wyjście" żąda liczby bloków z heredokiem policzonej z drzewa. **Jeden**: 6.A24.

Ciekawszy jest licznik szerszy. W całym `docs/TASKS.md` stoją **trzy** wystąpienia
`<<`, z czego heredokiem jest **jedno**:

| wiersz | treść | czy heredok |
|---|---|---|
| 912 | `<<<<<<< HEAD` w opisie 6.D55 | **nie** — znacznik konfliktu |
| 3614 | `python3 - <<'EOF'` w bloku 6.A24 | tak |
| 7364 | zapis heredoku zacytowany w opisie tej pozycji | **nie** — cytat |

Znacznik konfliktu jest tu istotny, bo **wzorzec bez strażników czyta go jako
heredok**: w `<<<<<<< HEAD` para `<` stoi też na piątym znaku, po niej spacja,
po niej `HEAD` — czyli poprawny terminator. `HEREDOC` żąda więc, żeby po lewej
i po prawej stronie pary nie było trzeciego `<`; to samo odsiewa herestring
(`<<<"abc"`). Do płotka „Weryfikacja" żaden z tych dwóch przypadków nie wchodzi
i wzorzec bez strażników przeszedłby dziś każdą bramkę — ale przeszedłby
**przypadkiem**, a nie dlatego, że jest prawdziwy.

## 3. Ciało heredoku jest danymi, więc bierze się dosłownie

Każdy inny wiersz płotka przechodzi przez `strip()`, pomijanie pustych i pomijanie
`#`. W ciele heredoku wszystkie trzy reguły są błędne:

- `#` jest komentarzem **Pythona**, a nie powłoki, i jest treścią programu;
- pusty wiersz bywa treścią;
- wcięcie **jest składnią** — `if True:` bez wcięcia następnego wiersza to `IndentationError`.

Zdejmowane jest wyłącznie wcięcie **wiersza otwierającego**, bo to ono jest
formatowaniem markdownu wokół tego heredoku. Bez tego cała treść wyjeżdża wcięta
o dwie spacje i komenda 6.A24 przestaje się dać uruchomić — co jest dokładnie tym,
czego ten moduł ma pilnować.

## 4. Sprawdzone wklejeniem, a nie obejrzeniem

Moduł istnieje po to, żeby pole „Weryfikacja" dawało się wpisać do terminala. Złożona
komenda 6.A24 została więc **zapisana do pliku i uruchomiona** na sztucznym
`build/d1.csv`:

```
$ bash cmd.sh
rc=0 — d2.csv:
a,b
1,2
3,4
abc,6
7,8
```

Czwarty wiersz ma podmienioną pierwszą kolumnę na `abc` — czyli komenda zrobiła to,
co blok 6.A24 obiecuje. To jest jedyny dowód, który odróżnia „licznik się zgadza"
od „komenda działa"; sam licznik zgadzał się także wtedy, gdy pętla `for … done`
wychodziła z kolektora jako niewklejalne `--out "…json" done` (naprawione w 6.D33).

## 5. Urwany heredok: ciało zostaje przy komendzie

Płotek, który kończy się w środku ciała, jest w pliku błędem — ale połknięcie takich
wierszy po cichu byłoby **tą samą usterką, którą ta pozycja zdejmuje, tylko w drugą
stronę**: licznik zgodny, wypis niepełny. Ciało zostaje więc przy komendzie, bez
dopisanego terminatora, żeby komenda wyglądała na urwaną, bo urwana jest.

## 6. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` kopii na bok i `md5sum -c` po przywróceniu; `__pycache__` czyszczony
przed każdym przebiegiem.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | gałąź heredoku zdjęta (kolektor jak przed tą pozycją) | **9/14**, pięć testów, w tym zbiór bloków z heredokiem i pętla |
| KN-2 | `HEREDOC` bez strażników `(?<!<)` / `(?!<)` | **13/14** — `test_a_conflict_marker_is_not_a_heredoc`, komunikat `<<<<<<< HEAD` |
| KN-3 | urwane ciało połknięte po cichu | **13/14** |
| KN-4 | ciało bez zdejmowania wcięcia płotka | **11/14**, trzy testy |
| KN-5 | w ciele pomijane puste wiersze i `#` | **13/14** |
| KN-6 | separator po terminatorze wraca na średnik | **13/14** — `EOF; done` zamiast `EOF` w osobnym wierszu |

Po każdej: `md5sum -c` → `OK`.

Kontrola dodatnia na drzewie sprzed zmiany, na **tym samym** bloku syntetycznym, co
KN z pola „Skończone, gdy" (heredok o dwóch wierszach ciała):

```
KONTROLA na drzewie SPRZED zmiany:
  komend: 4
   * cat > build/x.txt <<'EOF'
   * pierwszy wiersz
   * drugi wiersz
   * EOF
  komend w calym pliku: 324
  6.A24: 8 komend
```

Po zmianie ten sam blok daje **jedną** komendę. Liczba „cztery" z pola „Skończone,
gdy" jest więc zmierzona, a nie przyjęta na słowo.

## 7. Czego świadomie nie zrobiłem

- **Nie przeliczałem werdyktów audytu 6.D15 ani 6.D33** i nie ruszałem treści bloku
  6.A24 — pole „Poza zakresem" mówi to wprost. Mianownik tych ułamków zmienił się
  z 324 na 320, ale kto i kiedy je przeliczy, jest cudzą decyzją.
- **Nie ruszałem `reports/komendy-weryfikacji.md`.** Stoją tam liczby 42 i 83, ale
  raport nazywa je **cytatem** z wypisu z 06.09.2026, a nie stanem dzisiejszym —
  poprawianie cytatu zepsułoby go.
- **Nie dodałem osobnego werdyktu dla urwanego heredoku.** Pole „Wyjście" nie prosi
  o nową klasę usterki, a `has_placeholder` jest dziś jedyną klasą składniową.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- `has_placeholder` skanuje **całą** komendę, więc od dziś także ciało heredoku.
  W 6.A24 nawiasu ostrokątnego w ciele nie ma i zbiór bloków z miejscem do wypełnienia
  się nie zmienił, ale `<plan>` wpisany kiedyś do ciała heredoku zostanie zgłoszony
  jako miejsce do wypełnienia w komendzie — co bywa prawdą, a bywa danymi.
- `HEREDOC` szuka w **całej** treści wiersza, więc `<<` wewnątrz cudzysłowu
  (np. `echo "a << b"`) otworzyłby ciało, którego nie ma. W dzisiejszym pliku taki
  wiersz nie występuje; rozstrzyganie tego wymagałoby parsera cudzysłowów powłoki,
  a nie wzorca.
