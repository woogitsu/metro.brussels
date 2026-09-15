# 6.D222 — sto sześćdziesiąt jeden martwych przebiegów i bramka, która ich nie widziała

**15.09.2026**, na `4ef4a3a`. Wejście: `.github/workflows/prune-merged-branches.yml`,
`.github/workflows/*.yml` (dziesięć plików), `.github/actions/*/action.yml`,
`tools/tests/test_ci_workflows.py`.

## 1. Usterka: dwa klucze `with:` w jednym kroku

```yaml
        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
        with:
          fetch-depth: 0
        with:
          fetch-depth: 0
```

Weszło commitem **`2b95084`** („6.D108: o tym, czy raport mówi o dziś…", PR #550):
`fetch-depth: 0` zostało **dopisane drugim blokiem**, zamiast podmienione w istniejącym.
Drugi blok jest znak w znak taki sam jak pierwszy, więc w diffie wyglądał jak kontekst.

## 2. Skutek, zmierzony

| | |
|---|---:|
| przebiegów tego workflowa w API | **161** |
| w ostatniej stronie stu: `push` / `failure` | **100 na 100** |
| jobów w każdym z nich | **zero** |

To startup failure, nie awaria kroku: parser Actions odrzuca duplikat klucza
w mapowaniu, tworzy przebieg dla zdarzenia, które go wywołało, i kończy go bez
uruchomienia czegokolwiek. Workflow deklaruje wyłącznie `workflow_dispatch`, więc
przebieg z `push` w ogóle nie powinien powstać — powstaje dlatego, że pliku nie da
się sparsować.

**Kasowanie scalonych gałęzi nie zadziałało zatem ani razu od 6.D108** — a to jedyna
robota tego workflowa i powstał dokładnie dlatego, że agent dostaje 403 na usuwanie
refów.

## 3. Dlaczego nie widziała tego żadna bramka

`tools/tests/test_ci_workflows.py` czytał workflowy przez `yaml.safe_load`
(28 wywołań). PyYAML **przyjmuje duplikat klucza bez wyjątku i bez ostrzeżenia**,
ostatni wygrywa:

```
>>> yaml.safe_load('a:\n  x: 1\na:\n  x: 2\n')
{'a': {'x': 2}}
```

Osiemdziesiąt dwa testy tego modułu oglądały więc dokument, **którego GitHub nigdy
nie zobaczył**, i wszystkie były na tym pliku zielone. Zmierzone wprost — patrz KN-4.

## 4. Odpowiedź: bramka, a nie przepięcie 28 wywołań

**Blok pozycji zapowiadał „loader wołany zamiast gołego `yaml.safe_load`" i to jest
poprawione po pomiarze, a nie wykonane z planu.** Wywołań `yaml.safe_load` w tym
module jest **28**; przepięcie wszystkich byłoby wielkim diffem, który niczego nie
dokłada — po usunięciu duplikatu te wywołania czytają dokładnie to, co Actions.
Potrzebna jest **jedna bramka**, która parsuje każdy plik YAML-a CI loaderem
odrzucającym duplikaty. `LoaderBezDuplikatow` zawęża `SafeLoader` o jedną regułę
i niczego poza nią nie zmienia — asercja w kontroli przyrządu żąda, żeby na tekście
**bez** duplikatu oba czytniki dały wynik identyczny.

Bramka ogląda **11 plików** — dziesięć workflowów i akcje lokalne — z podłogą na tę
liczbę, bo skan, który przestałby cokolwiek znajdować, odpowiedziałby „zero
duplikatów" tak samo przekonująco jak skan widzący.

## 5. Osiem kształtów z dziewięciu — i tylko o jednym wiadomo

Żeby nie dało się przeczytać tej pozycji jako „duplikat klucza to jedyna różnica
między PyYAML-em a Actions", dziewięć kształtów przeszło przez `yaml.safe_load`:

| kształt | PyYAML |
|---|---|
| duplikat klucza w mapowaniu | **przyjmuje** |
| duplikat klucza na jednym poziomie | **przyjmuje** |
| kotwica i alias (`&`/`*`) | **przyjmuje** |
| klucz scalający (`<<:`) | **przyjmuje** |
| `on:` jako klucz | **przyjmuje — i daje klucz `True`** |
| `yes`/`no` jako wartość | **przyjmuje** jako bool |
| liczba ósemkowa `0755` | **przyjmuje** |
| liczba sześćdziesiętna `1:30` | **przyjmuje** |
| tabulator we wcięciu | odrzuca |

**Osiem z dziewięciu przechodzi. Dowód, że Actions odrzuca, istnieje dla JEDNEGO** —
duplikatu klucza, i jest nim te 161 przebiegów. O pozostałych siedmiu ten moduł nie
twierdzi nic, bo tego nie zmierzyłem, i tak jest zapisane (§4.1).

**`on:` → `True` nie jest tu nowym znaleziskiem** i to też jest sprawdzone, a nie
przyjęte: `_wyzwalacze()` już to obsługuje (`dokument.get("on", dokument.get(True))`)
i ma na to własną kontrolę przyrządu, a blok `paths:` czytany jest wzorcem po tekście
surowym. Ze sparsowanego dokumentu moduł bierze wyłącznie `document["jobs"]`.

## 6. Kontrole negatywne

Baza modułu: **86/86** (było 82 przed tą pozycją).

| | podstawienie | wynik |
|---|---|---|
| KN-1 | duplikat `with:` przywrócony w tym samym kroku | **84/86** — zapalają dwie bramki, obie nazywają plik i krok |
| KN-2 | duplikat `permissions:` w **innym** workflow | **85/86** — bramka nie jest zakotwiczona w jednym znanym przypadku |
| KN-3 | loader ścisły oślepiony (`and False` przy sprawdzeniu) | **85/86** — zapala kontrola przyrządu |
| KN-4 | duplikat **obecny**, moduł **sprzed** tej pozycji | **82/82 ZIELONE** |

Po każdej `md5sum -c` na trzech plikach: `OK`.

**KN-4 jest tą, o którą prosiło pole „Weryfikacja"** — „i że przed tą pozycją NIE
zapalał". Nie zapalał: osiemdziesiąt dwa testy przechodzą nad plikiem, którego
GitHub nie umie sparsować. Ślepota jest **zmierzona**, a nie zadeklarowana.

**KN-2 jest tą, która oddziela bramkę od anegdoty:** duplikat w innym pliku i na
innym kluczu zapala ją tak samo.

Pełne przebiegi: `python3 tools/tests/test_all.py` — **2485/2485**, `dotnet test tests/Sim.Tests` — **662/662**, `dotnet test tests/Game.Tests` — **307/307**.

## 6a. Skutek po stronie GitHuba, zmierzony PO poprawce

Zielony zestaw testów mówi, że bramka działa. Że **usterka przestała istnieć**, mówi
dopiero to — licznik przebiegów tego workflowa, per gałąź:

| gałąź | przebiegów `prune-merged-branches.yml` |
|---|---:|
| `claude/6d210-ciche-ramie` | 1 (martwy) |
| `claude/6d211-polkniete-czlony` | 1 (martwy) |
| `claude/6d212-licznosc-a-zawartosc` | 1 (martwy) |
| **`claude/6d222-duplikat-klucza`** | **0** |

Licznik całkowity stoi na **164**; ostatni martwy przebieg powstał 15.09.2026 o 07:15
przy scaleniu #617, czyli jeszcze na starym pliku. Push gałęzi tej pozycji **nie
utworzył żadnego przebiegu** — plik daje się sparsować, więc Actions czyta z niego to,
co tam napisano: wyłącznie `workflow_dispatch`.

**To jest weryfikacja po drugiej stronie granicy.** Wszystko inne w tej pozycji —
bramka, cztery kontrole negatywne, dziewięć próbek — mierzy PyYAML-a i drzewo. Ten
jeden pomiar mierzy parser, którego w repozytorium nie ma i którego zachowania nie da
się zasymulować; dlatego stoi osobno, a nie w tabeli kontroli negatywnych.

## 7. Czego świadomie nie zrobiłem

- **Nie uruchomiłem tego workflowa i nie skasowałem żadnej gałęzi.** Ta pozycja ma go
  naprawić, nie wykonać — kasowanie gałęzi zostaje decyzją właściciela, przez
  `workflow_dispatch` z `dry_run`.
- **Nie przepiąłem 28 wywołań `yaml.safe_load`** — §4 i pomiar z sekcji 4.
- **Nie tknąłem `on:` ani treści kroków** poza tym jednym duplikatem.
- **Nie sprawdziłem, które z siedmiu pozostałych kształtów Actions odrzuca** — to
  wymagałoby wysłania siedmiu celowo zepsutych workflowów na maszynę właściciela.

## 8. Zauważone, nie tknięte

- **Duplikat był znak w znak identyczny z blokiem, który powtarzał.** W diffie PR-a
  #550 wyglądał jak kontekst, a nie jak dodanie — i to jest powód, dla którego
  przeżył trzy miesiące recenzji.
- **Czerwony przebieg tego workflowa widać w liście przebiegów repozytorium przy
  KAŻDYM pushu**, także na `main`. Przez 161 przebiegów nie zapalił niczyjej uwagi —
  znalazłem go, bo stał czerwony obok PR-a, którym się akurat zajmowałem.
- `.github/actions/*/action.yml` przechodzą przez tę samą bramkę, choć Actions
  parsuje je w innym momencie; nie sprawdzałem, czy duplikat w akcji lokalnej daje
  startup failure całego przebiegu, czy tylko błąd kroku.
