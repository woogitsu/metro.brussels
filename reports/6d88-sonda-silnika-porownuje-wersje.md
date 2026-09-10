# Sonda silnika nie porównywała zgłaszanej wersji z pinem (6.D88)

**Zmierzone 09.09.2026, wykonane 10.09.2026 na:** `838f459`, kontener tej sesji.
**Przyrząd:** uruchomienie **prawdziwego ciała kroku sondy** z atrapą silnika
w katalogu tymczasowym, `python3 tools/tests/test_all.py`, trzy kontrole negatywne
z `md5sum -c` po każdym przywróceniu.

---

## 1. Co było zepsute

```bash
if [ -x "$binary" ] && [ -d "$GODOT_DIR/GodotSharp" ]; then
  echo "engine=present" >> "$GITHUB_OUTPUT"
  "$binary" --headless --version        # ← WYPIS, nie porównanie
```

`engine=present` zależało wyłącznie od **obecności pliku** i katalogu `GodotSharp`.
Numer, który silnik zgłasza, nie był z niczym zestawiany.

**I to jest cała szkoda, a nie sam brak porównania:** krok pobierania jest bramkowany
`if: steps.godot.outputs.engine == 'missing'`, więc porównanie w
`tools/ci/godot_install.sh` — to, które **istnieje i działa** (`have != VERSION_REPORTED`
→ „pobieram od nowa") — w takim przebiegu **nie wykonywało się wcale**. Instalator ma
kontrolę, do której przebieg nie dochodzi.

## 2. Dlaczego waga jest niższa, niż nadał audyt

Wpis pozycji mówi to wprost i pomiar tego nie zmienia. U Blendera sonda pytała
o **nieuwersjonowaną** nazwę w ścieżce systemowej, a apt kładł tam rutynowo spotykane
stare wydanie (`CLAUDE.md` §9). Ścieżka silnika zawiera wersję **dwa razy** — w katalogu
(`metro-godot/4.7.2-stable/`) i w nazwie pliku (`Godot_v4.7.2-stable_mono_linux.x86_64`)
— więc podłożenie innej wersji wymaga ręcznego działania wbrew treści.

Zostaje **luka kontraktowa, nie scenariusz rutynowy**, i tak jest tu zapisana.

## 3. Poprawka: wzorzec z instalatora Blendera

Sonda rozbiera wypis silnika, normalizuje zapis i porównuje z pinem; przy rozjeździe
melduje `missing`, czyli oddaje sprawę krokowi pobierania — zamiast ogłaszać obecność.

**Normalizacja `-` na `.` jest konieczna, nie kosmetyczna:** tag wydania brzmi
`4.7.2-stable`, a silnik zgłasza `4.7.2.stable.mono.official.…`. Ta sama różnica
odrzuciła przy 6.D68 instalację, której suma kontrolna przed chwilą przeszła.

## 4. Bramka uruchamia PRAWDZIWE ciało kroku, a nie szuka napisu

`test_the_engine_probe_compares_the_reported_version_with_the_pin` wyciąga skrypt
kroku z YAML-a (po `id: godot`, bo nazwa kroku jest po polsku i zmienia się przy
każdym przepisaniu komentarza), stawia w katalogu tymczasowym atrapę wykonywalną
wypisującą zadany numer w formacie Godota i czyta `engine=…` z podstawionego
`$GITHUB_OUTPUT`. Trzy przypadki:

```
zgłasza 4.7.2.stable, pin 4.7.2-stable          -> present
zgłasza 4.3.stable,   pin 4.7.2-stable          -> missing
zgłasza 4.7.2.stable, BEZ katalogu GodotSharp   -> missing
```

Trzeci pilnuje, że poprawka nie zjadła istniejącego warunku: bez assembly .NET silnik
wywraca się dopiero przy starcie sceny, kilkanaście kroków dalej niż powód.

## 5. Trzy kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`. Cache bajtkodu czyszczony przed każdym
przebiegiem — powód zmierzony przy 6.D86.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | porównanie zdjęte, wraca goły wypis | **czerwona** 6/8 — „sonda uznała za OBECNY silnik zgłaszający 4.3.stable" |
| KN-2 | normalizacja dywizu zdjęta | **czerwona** 6/8 — „sonda nie uznała silnika w wersji ZGODNEJ z pinem za obecny" |
| KN-3 | wzorzec rozbioru wypisu nie łapie niczego | **czerwona** 7/8 |

**KN-2 mierzy kierunek odwrotny niż KN-1 i dlatego jest osobno**: bez normalizacji
sonda odrzuca wersję **poprawną**, czyli psuje przebieg, w którym wszystko jest
w porządku. Bramka bez tego przypadku przyjęłaby „poprawkę", która pobiera silnik
przy każdym przebiegu.

## 6. Czego NIE zrobiłem

**Nie tknąłem sumy kontrolnej pobrania** — to jest 6.D68 i stoi w polu „Poza zakresem".
**Nie ruszyłem porównania w `tools/ci/godot_install.sh`** — ono było poprawne od
początku; usterka polegała na tym, że przebieg do niego nie dochodził.
**Nie dopisałem sondzie sprawdzania sumy pliku binarnego.** Kusiło, bo obok jest
`sha512` w pinie, ale sonda ma odpowiadać na pytanie „czy pobierać", a nie
uwierzytelniać to, co pobrał instalator — ten sprawdza sumę **przed** rozpakowaniem
i to jest właściwe miejsce.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py test_engine_version.py
  -> 8/8 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 109,105 s, 2150 testów, 113 modułów, kod 0

yaml.safe_load po godot-first-run.yml: OK
```

Zestaw urósł z **2148** do **2150**: dwa nowe testy.
