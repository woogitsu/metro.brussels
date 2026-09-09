# Sekcja 9 opisywała selektor, którego w drzewie nie było — i bramka pilnowała jednego wiersza

**Zmierzone 09.09.2026 na:** `fcaaca0`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_docs_ci_claims.py` (funkcje `paragraphs`,
`is_historical`, `extra_labels`, `drift_in_text`), `tools/tests/test_ci_workflows.py`,
`.github/workflows/`, `CLAUDE.md`, `python3 tools/tests/test_all.py`.

---

## 1. Skąd ten raport

`CLAUDE.md` §9 opisywała selektor złożony z sześciu etykiet, a wszystkie dziesięć
workflowów chodziło już na gołej etykiecie po decyzji właściciela z 09.09.2026.
Bramka `test_ci_workflows.py` została wtedy przekierowana na nowy stan i zgadza się
z drzewem; nie zgadzała się z nimi konstytucja. Właściciel rozstrzygnął: przepisać §9
na dzisiejszy stan.

To był cały zakres zadania. Pomiar zrobiony po drodze dołożył drugi, większy wynik.

## 2. Bramka nie mogła tego złapać — i przyczyna jest inna, niż wyglądała

`test_docs_ci_claims.py` istnieje po to, żeby porównywać prozę dokumentów
z etykietami przeczytanymi z YAML-a, a `CLAUDE.md` doszło do jego pętli 08.09.2026
przy 6.D47 właśnie dlatego, że bramka pilnowała odsyłaczy do §9, nie pilnując §9.

Pomijanie idzie z **granulacją akapitu**, a akapitem jest tekst między pustymi
wierszami. Punkty w §9 stały bez pustych wierszy między sobą, więc akapitem był
**cały wykaz**:

```
akapit wiersze 172..275 (104 wierszy), historyczny=True
markery: ['poprzedni', 'przepisan', 'to już nieprawda', 'zdjęto', 'zmierzone']
```

Jeden marker gdziekolwiek w sekcji zwalniał z bramki **wszystkie 104 wiersze**.
A markery w §9 być muszą: konwencja tej sekcji każe wymieniać poprzednie litery
reguły, więc słowo „przepisany" pojawia się tam z założenia. Zwolnienie było zatem
nie wypadkiem, a **skutkiem konwencji** — i dlatego samo z siebie nie mogło zniknąć.

Pokrycie sekcji 9 przez bramkę, w wierszach:

| kształt | wierszy w sekcji | objętych bramką |
|---|---|---|
| przed poprawką | 108 | **1** |
| po przepisaniu §9 | 114 | 20 |
| po rozdzieleniu punktów pustym wierszem | 114 | **46** |

Jeden wiersz ze stu ośmiu — w sekcji, której pilnowanie było jedynym powodem
dołożenia tego pliku do pętli.

## 3. Czego bramka nadal nie złapie, i to nie jest to samo

Zdiagnozowałem to najpierw źle i pierwsza kontrola negatywna była złym
eksperymentem: sprawdzałem, czy dokument mówiący `self-hosted` zapali bramkę przy
workflowach przestawionych na maszynę GitHuba. Nie zapala i nie ma prawa —
`_looks_like_a_label` uznaje za etykietę wyłącznie token z cyfrą albo z wielką
literą, więc `self-hosted` **nie jest zgłaszalny z definicji**.

Zmierzone na starym wierszu §9 wobec dzisiejszych workflowów:

```
extra_labels = ['linux', 'x64']
_looks_like_a_label('self-hosted')    = False
_looks_like_a_label('Linux')          = True
_looks_like_a_label('woogitsu')       = False
_looks_like_a_label('i5-10400f')      = True
_looks_like_a_label('nvidia-gtx1070') = True
```

Z czterech nieaktualnych etykiet detektor nazwałby **dwie**. Nie dlatego, że dwóch
nie rozpoznaje — rozpoznaje wszystkie cztery — ale bo `extra_labels` **przerywa na
pierwszym tokenie niewyglądającym na etykietę**, a w liście stoi `woogitsu` i za nim
kończy się skan. Osobna usterka, osobna pozycja; ta poprawka jej nie tyka.

## 4. Co zmienione

Deklaracja dzisiejszego selektora stoi w **osobnym akapicie bez ani jednego markera
historii**, więc bramka ją czyta. Historia reguły — cztery litery, wszystkie
wymienione, bo bez nich nie widać, czemu dzisiejsza jest taka, jaka jest — stoi
w akapicie obok, gdzie markery są na miejscu i gdzie zwolnienie jest poprawne.
Pozostałe punkty §9 rozdzielone pustym wierszem, żeby zwolnienie jednego nie
zwalniało pozostałych.

Litera czwarta mówi wprost, czego nie mówiła żadna poprzednia: etykiety sprzętowe
nie były ozdobą i nie zostały usunięte jako ozdoba — **zniknęły, bo zniknął zbiór
maszyn, który miały odciąć**. Bez tego zdania następna osoba przeczyta ich brak jako
uproszczenie i przywróci je przy pierwszej awarii kolejkowania.

Warunek powrotu przepisany na sprawdzalny: komplet wraca wtedy i tylko wtedy, gdy do
puli dołączy maszyna nosząca `self-hosted`, która zadań tego projektu wykonać nie
może. Poprzedni warunek mówił „gdyby pula zeszła do jednej maszyny" — a liczebności
puli z repozytorium sprawdzić nie da się, więc był warunkiem niewykonalnym.

## 5. Weryfikacja

```
  5/5 przeszło
  RAZEM 105.821 s, 2066 testów, 110 modułów
kod=0
```

## 6. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| etykieta sprzętowa dopisana do NOWEJ deklaracji | `CLAUDE.md:172: etykieta i5-10400f dopisana do runnera, a żaden job jej nie nosi` — **1 dryf** |
| ta sama etykieta dopisana do akapitu historii | **0 dryfów** — zwolnienie działa i ma działać właśnie tam |
| akapit deklaracji sprawdzony na `is_historical` | `False` w nowym kształcie, `True` w starym |
| workflowy przestawione na maszynę GitHuba | 0 dryfów w obu kształtach — kierunek, którego detektor nie obsługuje (§3) |

Para pierwsza z drugą jest tu całym dowodem: ta sama zmiana treści raz zapala
bramkę, a raz nie, i rozstrzyga o tym wyłącznie to, w którym akapicie stoi.
Kontrola czwarta jest w tabeli, choć **nie potwierdza niczego** — stoi tu, bo była
pierwszą, którą wykonałem, i jej zerowy wynik obaliłbym po cichu, gdyby jej tu nie
było. Wnioskowanie z niej wyszło błędne i §3 mówi, dlaczego.

Po każdej kontroli `md5sum -c CLAUDE.md`: `OK`.

## 7. Czego świadomie nie zrobiono

Workflowów nie tknięto — decyzja właściciela z 09.09.2026 stoi, a `test_ci_workflows.py`
już jej pilnuje. `test_docs_ci_claims.py` nie tknięty: żadna jego linia nie musiała
się zmienić, bo poprawka jest w **kształcie dokumentu**, który ten moduł czyta.
Bramka po zmianie sprawdza 46 wierszy zamiast jednego, nie sprawdzając ani o jedno
zdanie mniej.

Nie naprawiono przerywania skanu na `woogitsu` (§3). To zmiana w detektorze, nie
w dokumencie, i wymaga własnej kontroli negatywnej na pełnej liście etykiet.

## 8. To samo zdanie stało w README — znalazł je audyt, nie ja

Zewnętrzny audyt repozytorium (na `cbaa67e`, 09.09.2026) zgłosił ten sam rozjazd jako
`F-010`, i wskazał **dwa** miejsca zamiast jednego: `CLAUDE.md` §9 **i** `README.md`.
Drugiego nie zauważyłem. Sprawdzone i potwierdzone: `README.md` deklarowała komplet
sześciu etykiet jako stan bieżący („od 07.09.2026"), a akapit był zwolniony z bramki
dokładnie tym samym mechanizmem, co §9:

```
akapit 119..134 historyczny=True | markery=['poprzedni', 'przepisan']
```

Szesnaście wierszy, dwa markery, jedna deklaracja stanu bieżącego w środku. Poprawka
jest ta sama: deklaracja w osobnym akapicie bez markera, historia obok. Po zmianie:

```
akapit 119..123 historyczny=False markery=[]
```

Kontrola negatywna na nowym kształcie:

```
README.md:119: etykieta `i5-10400f` dopisana do runnera, a żaden job jej nie nosi
  — workflowy używają ['self-hosted']
```

Wniosek osobny od samej poprawki: **jedno wystąpienie tego wzorca nie mówi nic o liczbie
wystąpień**. Zmierzyłem mechanizm na §9 i uznałem sprawę za zamkniętą, nie policzywszy,
w ilu jeszcze akapitach markery zwalniają deklarację stanu bieżącego. Liczby nadal nie
mam — §9 i README są dwoma, które znam, a nie dwoma, które są.

## 9. Co zauważone przy okazji, nie tknięte

Poza `CLAUDE.md` bramka czyta `docs/` i `reports/` z tą samą granulacją akapitu.
Nie mierzyłem, ile tam jest akapitów wielopunktowych z jednym markerem historii —
w `reports/` markery są normą, bo raporty cytują pomiary, a `zmierzone` jest
markerem. Pokrycie tej bramki w `reports/` może być więc równie punktowe jak było
w §9, i nikt tego dotąd nie policzył.
