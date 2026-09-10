# `chk_*` rozdzielone na formę programową i wyrażeniową (10.09.2026)

**Zmierzone 10.09.2026 na:** `911a2dc`, kontener tej sesji.
**Przyrząd:** `bash doctor.sh --no-tests` z atrapą `dotnet` (wypis porównywany bajt
w bajt), `tools/tests/test_dotnet_version.py` (`doctor_check_commands`, nowe
`doctor_prog_calls`), `python3 tools/tests/test_all.py`.

---

## 1. Jedenaście wywołań, dwa kształty, jedna funkcja

`doctor.sh` miał jedną parę funkcji obsługującą przez `eval` dwa różne kształty
drugiego argumentu. Policzone 10.09.2026:

```
uruchomienie programu   6   "$DOTNET" --version, python3 --version, "$BLENDER_CMD" …
wyrażenie powłoki       5   [ "$HAVE_SDK_MAJOR" -ge "$REQUIRED_TFM" ], [ $HOSTFXR_OK -eq 0 ], "false"
```

**Wpis mówił o czterech wyrażeniach, jest ich pięć** — piąte (`"false"`) dopisało
6.D96 godzinę wcześniej tego samego dnia. Liczba w polu „Skąd" zestarzała się między
napisaniem pozycji a jej wykonaniem.

## 2. Co się zmieniło, a co NIE — i to drugie wyszło z kontroli negatywnej

Forma programowa (`chk_prog_required` / `chk_prog_optional`) bierze program
i argumenty jako **tablicę** (`"$@"`) i nie woła `eval`. Forma wyrażeniowa
(`chk_expr_*`) `eval` zachowuje, bo wyrażenie powłoki tablicą słów nie jest, i nazywa
się tak, żeby było widać, że to ona.

**Czego to NIE zdejmuje, zmierzone, nie założone.** Forma tablicowa usuwa DRUGI
rozbiór (`eval`), ale nie usuwa PIERWSZEGO — podziału na słowa przy rozwinięciu:

```
chk_prog_required "dotnet SDK" "…"  $DOTNET  --version   (atrapa w `sdk with space`)
  -> BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+

chk_prog_required "dotnet SDK" "…" "$DOTNET" --version   (ta sama atrapa)
  -> ok    dotnet SDK
```

Cudzysłowy są więc nadal potrzebne. Pole „Dlaczego to pozycja" wpisu mówiło, że
`eval` wymusza pamiętanie o nich, a bramka może to jedynie zgłosić — po pomiarze
zdanie jest węższe: **6.D98 zdejmuje jeden z dwóch rozbiorów, nie oba**, a bramka
na cytowanie pilnuje teraz OBU form, nie jednej. To znalazła kontrola KN-3, nie
projekt; pierwsza wersja nowej bramki sprawdzała formę tablicową tylko na obecność
wyrażeń i przepuszczała `$DOTNET` bez cudzysłowów.

## 3. Wypis identyczny co do bajtu

```
diff /tmp/doctor_przed.txt /tmp/doctor_po.txt
  -> (brak różnic)

chk_prog_required 3 | chk_prog_optional 3 | chk_expr_required 2 | chk_expr_optional 3
```

Warunek odbioru z pola „Skończone, gdy" jest więc spełniony wprost: 38 wierszy
wypisu, 19 wierszy `ok`/`BRAK`/`WARN`, żadnej różnicy.

## 4. Bramka z 6.D81 złapała moją zmianę natychmiast

Po przemianowaniu funkcji stary wzorzec przestał cokolwiek widzieć i **próg to
zgłosił**, zamiast przejść nad pustką:

```
FAIL test_every_doctor_check_quotes_the_tool_path_it_runs:
     skan widzi 0 wywołań `chk_*` — wzorzec rozjechał się z treścią doctora
```

Ten próg istnieje dokładnie dlatego, że przy 6.D81 wzorzec raz już po cichu nie
łapał nic. Zadziałał na pierwszej mojej zmianie tego pliku.

## 5. Pięć kontroli negatywnych, `md5sum -c: OK` po każdej

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | wyrażenie powłoki wstawione do formy TABLICOWEJ | **czerwona** 42/44, dwie bramki |
| KN-2 | uruchomienie programu wstawione do formy z `eval` | **czerwona** 43/44 (próg liczby) |
| KN-2b | ta sama mutacja, asercja o programie w `eval` osobno | wykrywa `['git --version']` |
| KN-3 | forma tablicowa dostaje ścieżkę BEZ cudzysłowów | **zielona** — bramka o to nie pytała |
| KN-3b | ta sama mutacja, po dodaniu asercji na cytowanie | **czerwona** 42/44, dwie bramki |
| KN-4 | `eval` wraca do formy tablicowej | **czerwona** 43/44, atrapa ze spacją znów `BRAK` |
| KN-5 | wzorzec `WYRAZENIE_POWLOKI` nie łapie niczego | **czerwona** 42/44, dwie bramki |

**KN-3 wyszła zielona i to jest znalezisko o mojej własnej bramce** — opisane
w §2. Nowa bramka sprawdzała formę tablicową wyłącznie na obecność wyrażeń powłoki,
więc `$DOTNET` bez cudzysłowów przechodził; doszła asercja pytająca o cytowanie
także tam, i KN-3b na tej samej mutacji daje 42/44.

**KN-2 zapaliła próg liczby, a nie asercję, o którą chodziło** — obie stoją w jednym
teście i pierwsza przerywa. Sprawdziłem więc drugą osobno (KN-2b), poza zestawem:
`programy wykryte w formie z eval: ['git --version']`. Bez tego kroku „test czerwony"
nie znaczyłoby jeszcze „czerwony z właściwego powodu".

**KN-4 dowodzi, że to forma tablicowa, a nie samo cytowanie, zdejmuje usterkę:**
z przywróconym `eval` ta sama, poprawnie cytowana linia znów daje `BRAK dotnet SDK`
dla atrapy w katalogu ze spacją.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_dotnet_version.py
  -> 44/44 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 125,988 s, 2195 testów, 118 modułów, kod 0
  -> 2195/2195 przeszło

bash doctor.sh --no-tests   (z atrapą, przed i po)
  -> wypis identyczny co do bajtu
```

Zestaw **2193 → 2195**, moduły bez zmiany (118). Zapadka `MIN_REPORTS`, podniesiona
ze dwustu szesnastu na dwieście siedemnaście.

## 7. Czego świadomie nie zrobiłem

Nie zmieniałem treści żadnego komunikatu ani progów wersji — pole „Poza zakresem"
wyklucza jedno i drugie, a warunkiem odbioru był wypis identyczny co do bajtu. Nie
zdjąłem `eval` z formy wyrażeniowej: wyrażenie powłoki nie jest tablicą słów i `eval`
jest tam narzędziem właściwym, a nie zaszłością.

## 8. Zauważone i nietknięte

Forma programowa używa zmiennych `nazwa` i `podpowiedz` **bez `local`** — tak samo
jak reszta tego skryptu, który `local` nie używa nigdzie. W `doctor.sh` te nazwy
nie kolidują dziś z niczym, ale są zmiennymi globalnymi powłoki i przy następnej
funkcji o tych samych nazwach zaczną. Zmiana konwencji na `local` dotyczyłaby całego
pliku i nie należy do tej pozycji.
