# Ścieżka SDK ze spacją ginie w `eval`, a doctor przeczy sam sobie (6.D81)

**Zmierzone 10.09.2026 na:** `5864828`, kontener tej sesji.
**Przyrząd:** atrapa wykonywalna w katalogu `sdk with space` i w `sdk_no_space`,
`HOME` i katalog tymczasowy podstawione, bez instalowania czegokolwiek;
`python3 tools/tests/test_all.py`; trzy kontrole negatywne z `md5sum -c`
po każdym powrocie.

---

## 1. Pomiar, ta sama atrapa w dwóch katalogach

```
--- doctor.sh z DOTNET_BIN ze spacją ---
  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+
=== KONTROLA: ta sama atrapa, katalog BEZ spacji ===
  ok    dotnet SDK
  ok    dotnet SDK >= 10 (jest 10)
```

`chk_required` wykonuje swój drugi argument przez **`eval`**, czyli parsuje go
**drugi raz**. Wiersz brzmiał `"$DOTNET --version"` — bez cudzysłowów wewnętrznych,
więc ścieżka ze spacją rozpadała się na dwa słowa.

## 2. Dlaczego to nie jest tylko fałszywy negatyw

Kilkadziesiąt wierszy niżej `dotnet test` woła **tę samą ścieżkę** cytowaną poprawnie
(`"${DOTNET_BIN:-dotnet}" test …`). Pełny przebieg meldował więc **brak SDK w sekcji
środowiska i `ok` w sekcji testów** — wewnętrzna sprzeczność jednego raportu, który
`CLAUDE.md` §2 każe czytać przed każdym zadaniem.

## 3. Trzy miejsca, nie jedno

Skan po `$DOTNET` w `doctor.sh` dał trzy użycia bez cudzysłowów:

```
117  chk_required "dotnet SDK" "$DOTNET --version" …          -> eval
128  HAVE_SDK_MAJOR="$($DOTNET --version … | cut -d. -f1)"    -> podstawienie
168  if HAVE_SDK="$($DOTNET --version …)" …                   -> podstawienie
```

Dwa ostatnie **nie idą przez `eval`**, ale rozpadają się z tego samego powodu: gołe
`$DOTNET` w pozycji polecenia podlega podziałowi na słowa. Wiersze Blendera i Godota
były cytowane od początku i to one są tu wzorcem.

## 4. Dwie bramki, bo dwie połowy problemu

**`test_doctor_reads_the_same_sdk_from_a_path_with_a_space_in_it`** uruchamia
PRAWDZIWY `doctor.sh` dwa razy — atrapa w `sdk with space` i w `sdk_no_space` — i żąda,
żeby **wiersze o SDK były identyczne**. Porównanie dwóch przebiegów ze sobą, a nie
z wpisanym napisem: gdyby doctor przestał wypisywać ten wiersz, oba byłyby puste
i równe, więc obok stoi asercja na treść.

**`test_every_doctor_check_quotes_the_tool_path_it_runs`** zamyka **rodzinę**:
każde `chk_*`, którego polecenie zaczyna się gołą zmienną, jest zgłaszane. Poprawka
zamyka jeden wiersz; ta bramka zamyka wszystkie następne.

Podział jest zmierzony, a nie wymyślony: kontrola negatywna **KN-3** zdejmuje
cytowanie wyłącznie z wiersza 128 — czyli **poza** `chk_*` — i wtedy bramka na
cytowanie **milczy**, a pada bramka behawioralna. Odwrotnie przy KN-2 (Blender):
pada tylko bramka na cytowanie, bo test na spację dotyczy dotneta.

## 5. Pierwsza wersja bramki na cytowanie pilnowała NICZEGO — i to jest wynik

Jej wzorzec brał drugi argument jako `"[^"]*"` i zatrzymywał się na **cudzysłowie
escapowanym**. Trzy z dziesięciu wywołań `doctor.sh` cytują zmienne wewnątrz, więc
skan zwracał dla nich `[ \` albo samo `\`:

```
   python3 --version
   git --version
   \
   [ \
   [ \
   …
```

Bramka przechodziła wtedy **trywialnie, nad dokładnie tą usterką, której pilnuje**.
Po poprawieniu wzorca na `(?:[^"\\]|\\.)*` skan widzi dziesięć prawdziwych poleceń,
a osobna asercja żąda, żeby żadne nie było puste ani urwane na łamaniu wiersza.

## 6. Trzy kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | zdjęte cytowanie z wiersza `dotnet` (w `chk_*`) | **czerwona** 36/38 — obie bramki |
| KN-2 | zdjęte cytowanie z wiersza Blendera | **czerwona** 37/38 — tylko bramka na cytowanie |
| KN-3 | zdjęte cytowanie z `HAVE_SDK_MAJOR` (poza `chk_*`) | **czerwona** 37/38 — tylko bramka behawioralna |

**KN-1 wykryła słabość komunikatu i to jest jej wynik.** Asercja o `BRAK dotnet SDK`
miała jako komunikat surowy wypis doctora, a ten zaczyna się pustą linią — więc
jednowierszowy raport zestawu pokazywał `FAIL …:` i **nic więcej**. Dziś komunikat
zaczyna się zdaniem, a wypis idzie za nim.

## 7. Czego NIE zrobiłem

**Nie przerobiłem `chk_required`/`chk_optional` na tablicę argumentów bez `eval`**,
choć pole „Wyjście" dopuszcza ten wariant jako drugi. Powód jest zmierzony: z dziesięciu
wywołań **cztery** nie są wołaniem programu, tylko wyrażeniem powłoki
(`[ "$X" -ge "$Y" ]`, `[ $HOSTFXR_OK -eq 0 ]`), więc forma tablicowa wymagałaby
rozdzielenia obu funkcji albo przepisania wszystkich dziesięciu miejsc — czyli zmiany
znacznie szerszej niż ta pozycja (`CLAUDE.md` §4.10). Cytowanie zamyka usterkę,
a bramka zamyka rodzinę.
**Nie tknąłem progów wersji ani szukania kandydatów na dysku** — oba stoją w polu
„Poza zakresem".

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_dotnet_version.py
  -> 38/38 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 97,297 s, 2143 testów, 113 modułów, kod 0

atrapa w katalogu ZE SPACJĄ, po poprawce:
  ok    dotnet SDK
  ok    dotnet SDK >= 10 (jest 10)
  ok    dotnet SDK == pin z global.json (10.0.401)

atrapa w katalogu BEZ spacji, po poprawce: wiersze IDENTYCZNE
```

Zestaw urósł z **2141** do **2143** testów; modułów bez zmiany.
