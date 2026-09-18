# Wzorcowa weryfikacja zadania

Wzorzec: narzędzie ma nie tylko wykonać się bez błędu, ale udowodnić, że wykrywa błędy lub produkuje poprawny rezultat.

Dla walidatora osi:

```bash
python3 tools/track/make_test_track.py --out build/t010/TEST.json
python3 tools/track/make_test_track.py --out build/t010/BROKEN.json --broken
python3 tools/track/validate.py build/t010/TEST.json
python3 tools/track/validate.py build/t010/BROKEN.json
```

Poprawny plik ma przejść, celowo zepsuty ma zostać odrzucony z konkretnymi błędami. Dla geometrii odpowiednikiem dowodu są trzy obejrzane rendery kontrolne.

Raport końcowy zadania: co zrobiono → rzeczywiste wyjście weryfikacji → opis renderów → czego nie zrobiono → zauważone problemy poza zakresem.

---

## Przykład rzeczywisty: kontrola, która przeszła na złym wyniku

Zadanie: wyrenderować pojedynczy chunk tunelu, żeby sprawdzić, czy jest zamkniętym
i ciągłym fragmentem rury.

**Co pokazał automat:**

```
[RENDER] axis25: 960x576 ink=0.085 std=0.043 poziomy=184 -> OK
```

Kontrola „klatka nie jest pusta" przeszła. Wszystkie trzy progi z zapasem.

**Co było na PNG:** jednolite szare pole z jedną cienką kreską. Kamera stała w płycie
stropowej, bo wysokość oka liczyła się z płata o **stałym X**, a chunk biegł pod kątem
do osi X — płat złapał sam strop i zwrócił 4,70 m zamiast 1,75 m.

**Wniosek pierwszy:** jednolita szarość ma i „ink", i odchylenie standardowe powyżej
progów. Metryka odrzuca **czarną** klatkę, nie odrzuca **złej**. Dlatego `CLAUDE.md` §5
wymaga obejrzenia PNG, a nie sprawdzenia, czy skrypt się wykonał.

## Ten sam dzień, błąd w drugą stronę

Po naprawie ten sam render dalej wyglądał jak szare pole z kreską. Uznałem to za defekt
i zacząłem szukać dalej.

**Zamiast zgadywać, zmierzyłem, gdzie stoi kamera:**

```
f=0.5 chainage=3178.2 oko=(2255.3,57.0)  najblizszy wierzcholek 5.09 m
```

Odległość 5,09 m zgadza się co do centymetra z geometrią profilu: przekątna od osi do
narożnika ściany przy wysokości oka 1,75 m wynosi √(4,70² + 2,95²) = 5,55 m, a do
narożnika podłogi mniej. **Kamera stała dokładnie tam, gdzie miała.**

Render z overlayem siatki potwierdził: prostokątny tunel, pierścienie zbiegające się do
punktu zbiegu, normalne do wnętrza. Geometria była poprawna od początku — brakowało
czytelności, nie poprawności.

**Wniosek drugi:** „obraz wygląda źle" to hipoteza, nie ustalenie. Zanim zaczniesz
naprawiać, zmierz. Zmierzona odległość rozstrzygnęła w jednym kroku to, czego trzy
kolejne domysły nie rozstrzygnęły.

**Wniosek trzeci:** widok wnętrza tunelu bez siatki jest jednolicie szary niezależnie od
tego, czy geometria jest dobra. Dlatego kamery wnętrza deklarują `wire` w manifeście —
to wiedza o kamerze, nie o wywołaniu.

## Kontrola negatywna na module Pythona: `md5sum -c` mówi o pliku, nie o tym, co się wykonało

Zadanie: sprawdzić, czy bramka NAPRAWDĘ łapie zepsutą wartość. Procedura wygląda tak,
że psujesz stałą, uruchamiasz bramkę, przywracasz plik i sprawdzasz sumę.

**Co pokazał przyrząd:**

```
tools/physics/reference.py: OK
```

Plik był przywrócony. Naprawdę. A mimo to bramka dwa razy zgłosiła `F0_N: 251389.0` —
wartość z **poprzedniej** mutacji (6.D86).

**Dlaczego.** CPython uznaje `.pyc` za ważny po parze **(mtime źródła w SEKUNDACH,
rozmiar w bajtach)**. Podmiana `248900.0` → `251389.0` ma dokładnie tę samą długość,
a `cp` przywracający plik trafił w tę samą sekundę co mutacja — więc żadne z tych
dwóch pól nie drgnęło i import poszedł ze starego bajtkodu. **Suma MD5 mówi o pliku
`.py`, a wykonuje się `.pyc`.**

**Pułapka działa w obie strony, i druga jest groźniejsza.** Zmierzone na rzeczywistej
bramce (`test_reference_snapshot.py`), mutacja w tej samej sekundzie co przebieg bazowy:

```
PRÓBA 1 — bez procedury
   baza:     5/5 przeszło, kod 0
   mutacja:  5/5 przeszło, kod 0     <- MA być czerwona

PRÓBA 2 — z czyszczeniem __pycache__ przed mutacją
   baza:     5/5 przeszło, kod 0
   mutacja:  1/5 przeszło, kod 1     <- prawda
```

Bez procedury kontrola negatywna wychodzi **zielona** i czyta się jako „bramka tego nie
łapie". To jest fałszywy wniosek w drugą stronę, bez żadnego śladu, że coś poszło nie tak.

**Procedura.** Przed **każdym** przebiegiem kontroli negatywnej na module Pythona:

```bash
find . -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
```

**`PYTHONDONTWRITEBYTECODE=1` NIE wystarcza** i to jest zmierzone, nie przewidziane:
zmienna zabrania bajtkod **pisać**, a pułapkę robi **czytanie** tego, który już leży.
Z `.pyc` z wcześniejszego, zwykłego przebiegu na dysku mutacja pod tą zmienną nadal
jest niewidoczna.

**A jednak w czystym katalogu ta zmienna działa — i stąd bierze się pomyłka.** Gdy
ustawić ją od pierwszego przebiegu, `.pyc` nie powstaje nigdy i mutacja jest widoczna;
pomiar zrobiony na świeżo ją więc potwierdza. Nie potwierdza jej życie: wystarczy
**jeden** wcześniejszy zwykły przebieg — zestaw uruchomiony godzinę temu — żeby
pułapka wróciła. Dlatego procedura każe **czyścić katalog**, a nie ustawiać zmienną.
Obie połowy tego rozstrzygnięcia są przybite w `tools/tests/test_bytecode_staleness.py`,
każda osobnym testem, bo pojedynczy test na jedną z nich opisywałby co innego, niż mówi.

**Czego to nie kosztuje.** Trzy pary przebiegów całego zestawu, zimny kontra ciepły:
126,27 / 125,65 / 127,47 s wobec 127,17 / 127,49 / 125,25 s — czyli **żadnego
mierzalnego zysku** z cache'u, bo moduły testowe i tak kompilują się ze źródła przez
`assertion_gate.load_instrumented`. **To jest zagrożenie lokalne, dla agenta i dla
właściciela.**

**Dlaczego w CI pułapki nie ma — zdanie przepisane 11.09.2026 (6.D136), a nie dopisane
obok.** Poprzednia wersja mówiła: „`actions/checkout` robi `git clean -ffdx`,
`__pycache__` jest w `.gitignore`, więc każdy przebieg CI zaczyna zimno". Pierwsza
połowa jest prawdziwa, **druga nie** i obalił ją log przebiegu: zestaw wypisuje tam
`[BAJTKOD] wyczyszczono 7 kat. __pycache__ (210 plikow) pod tools/`, czyli **210 plików
bajtkodu leżało, zanim wystartował**. (Liczba rośnie z każdym nowym modułem
narzędziowym: 201 w dniu pomiaru, 202 po dopisaniu `test_mass_copies.py` przy 6.D138,
203 po dopisaniu `test_prose_counts.py` przy 6.D166, 204 po dopisaniu
`test_playable_scripts.py` przy MB-01, 205 po dopisaniu `test_player_package.py`
przy MB-04, 206 po dopisaniu `test_doctor_test_log.py` przy 6.D241, 207 po dopisaniu
`test_rights_matrix_doc.py` przy 6.D239, 209 po dopisaniu
`test_json_required.py` przy 6.D233, 210 po dopisaniu
`test_value_chains.py` przy 6.D260 — bramka zapalała
się na każdej z tych jedynek sama.)

Tworzy je **jeden nazwany krok tego samego joba** — `Compile Python tools`, czyli
`python3 -m compileall -q tools`, stojący w `python-tests.yml` bezpośrednio przed
krokiem „Run tool tests". Liczby zgadzają się co do pliku i są odtwarzalne lokalnie:
na czystym drzewie `compileall` daje **7 katalogów i 210 plików**, z tym samym
rozkładem (`tools/tests` 139, `tools/blender` 29, `tools/track` 23, `tools/ci` 9,
`tools/visual` 5, `tools/physics` 3, `tools/data` 2).

Wniosek zostaje ten sam, ale wynika z czego innego: ten bajtkod powstał **z tego samego
checkoutu, w tym samym jobie, pół sekundy wcześniej**, więc przykryć źródła nie może —
pułapka z 6.D102 potrzebuje bajtkodu **starszego niż zmiana pliku**. Nie chroni przed
nią pusty katalog, tylko **jednoczesność**.

Pilnuje tego `test_bytecode_staleness.py`: krok musi stać w workflow przed zestawem,
a liczby muszą się zgadzać z tym, co daje `compileall` na czystym drzewie.

**Od 11.09.2026 (6.D122) zestaw czyści katalog sam, a ten akapit jest przepisany,
a nie dopisany obok.** Do tego dnia stało tu: „Zestaw mimo to nie czyści katalogu sam:
to byłoby wyłączenie cache'u na stałe także w CI" — i to zdanie broniło przed kosztem,
którego **własny pomiar dwa zdania wyżej wykazał jako zero**. `test_all.py` kasuje każdy
`__pycache__` pod `tools/` przed swoimi importami narzędzi i mówi o tym wierszem
`[BAJTKOD] wyczyszczono N kat. …`. Położenie wywołania jest treścią, a nie stylem:
w `main()` byłoby spóźnione o `import profiles, validate, reference …`, więc wypis
mówiłby o obronie, która nic nie zmieniła — pilnuje tego osobny test czytający
kolejność z AST.

**Dlaczego polecenie zostaje mimo to.** Bo pułapka nie ogranicza się do przebiegów
zestawu: własne `python3 -c`, import w konsoli i skrypt wołany wprost z `tools/`
czytają ten sam stary bajtkod, a `test_all.py` ich nie widzi. Zostaje też dlatego,
że dotyczy całego drzewa, a zestaw sprząta wyłącznie `tools/`. Obrona w narzędziu
jest pierwszą linią, procedura ręczna — drugą; **żadna nie zastępuje drugiej**.

**Co jeszcze weszło do pułapki i dlaczego to nie jest sprawa kontroli negatywnych.**
Zwykła edycja modułu narzędziowego i natychmiastowy przebieg zestawu mają dokładnie
ten sam kształt co mutacja: ta sama sekunda, a przy poprawce w rodzaju `0.30` na `0.31`
także ta sama długość. Procedura, którą trzeba pamiętać, broni wyłącznie tego, kto
o niej pamiętał.

**Wniosek czwarty:** przyrząd potwierdzający przywrócenie musi oglądać to, co się
wykonuje, a nie to, co leży na dysku. Suma MD5 na źródle jest o pliku; o przebiegu
mówi dopiero pusty `__pycache__`.

## Wzór na dowód

Dobre zadanie geometryczne kończy się **dwiema niezależnymi drogami do tej samej liczby**.
Przykład: luz skrajni M7 w tunelu liczony wzorem na strzałkę cięciwy i mierzony na siatce
dają 0,9408 m i 0,9447 m — **zgodność 3,9 mm**. Przy pierwszym podejściu rozjazd wynosił
52,4 mm, co nie było błędem geometrii, tylko porównywaniem dwóch różnych wielkości
(cięciwa nominalna 15,667 m zamiast rzeczywistej 14,567 m). **Rozjazd między metodami
jest informacją, nie szumem do uśrednienia.**
