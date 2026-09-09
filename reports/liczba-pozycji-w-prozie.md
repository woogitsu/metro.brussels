# Liczba, która starzeje się przy dwóch commitach na trzy (6.D50)

**Zmierzone 09.09.2026 na:** `a3a8a7b`, kontener tej sesji.
**Przyrząd:** `docs/TASKS.md`, `tools/tests/test_backlog.py` (`open_items`), `doctor.sh`,
`tools/tests/test_next_task.py`, `git log --format=%h -40 -- docs/TASKS.md`,
`python3 tools/tests/test_all.py`.

---

## 1. Usterka

Akapit pod tabelą „Co blokuje co, w jednym miejscu" mówił:

> fazy **5 i 6** trzymają 31 pozycji, z których żadna nie wymaga decyzji właściciela

`open_items` dawało tego dnia **36**. Liczba stoi w prozie tego samego pliku, w którym
jest liczona, i **nie czyta jej nic** — inaczej niż `MINIMUM_DETAIL_BLOCKS`
i `MINIMUM_READY_ITEMS`, których rozjazd z drzewem zapala bramkę.

Akapit czyta człowiek przychodzący z `doctor.sh` — dokładnie ten, którego ta liczba ma
przekonać, że praca jest.

## 2. Pytanie pozycji brzmiało „czy ta liczba ma tam w ogóle stać". Pomiar odpowiada: nie

Wpis 6.D50 zostawił wybór między bramką na literał a przepisaniem akapitu bez liczby,
z warunkiem: **wybór ma być uzasadniony liczbą, nie wygodą.** Liczba:

```
commitów dotykających docs/TASKS.md (ostatnie 40):        40
ile razy open_items ZMIENIŁ WARTOŚĆ w tym oknie:          27
z tych 40 commitów: wciągnięcia main do równoległej gałęzi: 7
```

Czyli literał w prozie wymagałby edycji przy **dwóch commitach na trzy**, a przy **co
szóstym** trafiałby w miejsce, gdzie dwie gałęzie zmieniają tę samą liczbę niezależnie —
konflikt semantyczny, którego git nie widzi i który w tym repozytorium zdarzył się już
dwa razy na zapadkach.

Historia tej konkretnej liczby jest zresztą zapisana w tym samym pliku i mówi to samo:
**33 → 31 → 29 → 24 → 31**, za każdym razem „przepisane, bo przestało być prawdą".

Wybór wariantu jest więc rozstrzygnięty pomiarem: **liczba znika z prozy i pojawia się
tam, gdzie jest liczona.**

## 3. Co powstało

`doctor.sh` liczy pozycje przy każdym uruchomieniu, wołając **to samo `open_items`**,
którego używa zapadka zapasu — nie drugą kopię reguły:

```bash
queue_count=$(python3 -c 'import io, sys; sys.path.insert(0, "tools/tests"); import test_backlog as B; print(len(B.open_items(io.open("docs/TASKS.md", encoding="utf-8").read())))' 2>/dev/null)
```

i wypisuje:

```
  Baza projektu jest gotowa. Następne zadanie: T-112 · Profil pionowy pakietu A — **CZĘŚCIOWO ODBLOKOWANE 07.09.2026**
  Kolejka faz 5 i 6 ma 35 pozycji do wzięcia, żadna nie wymaga decyzji właściciela.
```

Trzydzieści pięć, nie trzydzieści sześć, i **to jest właśnie dowód działania**: liczba
spadła o jeden w chwili, gdy ta pozycja dostała w tabeli `ZROBIONE` — w tym samym
commicie, bez dotykania czegokolwiek, co ją wypisuje.

**Jak to zostało zobaczone, skoro w tym kontenerze brakuje .NET.** Wiersz drukuje się
dopiero po zerze braków wymaganych, a `doctor.sh` w tym kontenerze kończy na
„1 wymaganych pozycji do naprawienia". Do zobaczenia wyjścia użyto **atrapy `dotnet`
w `PATH`** (`--version` → `10.0.400`, `test` → kod 0). Wiersz wyżej jest rzeczywistym
wyjściem tego przebiegu, nie przepisanym z kodu.

## 4. Dwa inne zdania tego samego akapitu też były nieprawdziwe

Pozycja pytała o jedną liczbę; akapit miał trzy fałszywe twierdzenia:

| twierdzenie akapitu | stan drzewa 09.09.2026 |
|---|---|
| „fazy 5 i 6 trzymają **31 pozycji**" | `open_items` = **36** |
| „nie ma w tym pliku ani jednego wpisu `### [ ]`, który nie byłby `ZABLOKOWANE` albo `[CZŁOWIEK]`" | **jest** — T-112, i to jego `doctor.sh` dziś wymienia jako następne zadanie |
| „komunikat doctora nadal odsyła wyłącznie do tabeli wyżej" | odsyła do kolejki faz 5 i 6 **od 05.09.2026** |

Wszystkie trzy zostały napisane jako prawdziwe i **żadnego nie pilnowało nic**. Drugie
jest szczególne: to ono uzasadniało istnienie całego akapitu („trafisz tu, bo…"), a
przestało być prawdą, gdy T-112 dostało status częściowo odblokowanego.

## 5. Bramki

Obie w `tools/tests/test_next_task.py`, bo to jest moduł o tym, **co doctor mówi nowej
sesji wobec stanu drzewa**:

1. `test_doctor_liczy_pozycje_kolejki_sam_zamiast_przepisywac_liczbe` — wycina
   z `doctor.sh` jego własne podstawienie i **uruchamia je**, tak samo jak dwie
   starsze bramki tego pliku robią to z wyborem zadania i pozycji kolejki. Sprawdza
   dwie rzeczy: że na tym drzewie wynik równa się `open_items`, i — to jest część
   istotna — że **na rozpisce z jedną pozycją mniej wynik jest o jeden mniejszy**.
   Sama zgodność z dzisiejszym drzewem przeszłaby także dla liczby wpisanej na sztywno.
2. `test_akapit_kolejki_nie_odzyskuje_literalu_liczby_pozycji` — akapit z kotwicą
   nie może nieść literału `\d+ pozycj`. Region kończy się pierwszą pustą linią,
   bo dalej stoi wywód o dawnych literach reguły i on liczby cytować **musi** — ta
   sama konstrukcja, co „akapit bez markera przeszłości" w `CLAUDE.md` §9. Detektor
   jest w teście sprawdzony na **własnym przedmiocie**: zdanie, które akapit naprawdę
   nosił, musi zostać złapane, a zdanie bez liczby — nie.

## 6. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| literał wraca do akapitu (`trzymają 36 pozycji`) | `FAIL …nie_odzyskuje_literalu…: akapit kolejki znowu podaje liczbę pozycji ('36 pozycj')`, 7/8 |
| doctor wpisuje dzisiejszą liczbę na sztywno (`echo 36`) | `FAIL …liczy_pozycje…: na rozpisce z jedną pozycją mniej doctor podał '36', a powinien 35 — liczba nie jest liczona, tylko przepisana`, 7/8 |
| podstawienie znika z doctora (zmiana nazwy zmiennej) | `FAIL …liczy_pozycje…: nie znalazłem podstawienia queue_count=$(…) w doctor.sh — bramka straciła przedmiot`, 7/8 |
| znika kotwica akapitu | `FAIL …nie_odzyskuje_literalu…: nie znalazłem akapitu po kotwicy … — bramka straciła przedmiot i milczy zamiast pilnować`, 7/8 |

`md5sum -c` po każdej: `OK` dla `docs/TASKS.md` i `doctor.sh`.

Druga kontrola jest tą, dla której bramka pierwsza ma dwie części. Trzecia i czwarta
pilnują, żeby obie bramki **odmawiały** po utracie przedmiotu, zamiast przechodzić na
pustym dopasowaniu — rodzina 6.D65 i 6.D76.

## 7. Weryfikacja

```
  8/8 przeszło       test_next_task.py
  RAZEM 2082 testów, 111 modułów, kod 0
```

Zestaw przed pozycją: 2080 testów, 111 modułów.

## 8. Czego świadomie nie zrobiono

**Nie tknięto `MINIMUM_READY_ITEMS` ani treści akapitu o §8** — jedno i drugie stoi
w polu „Poza zakresem" pozycji.

**Nie postawiono bramki na liczby w PRZEDOSTATNIM akapicie** („33 → 31 → 29 → 24"),
bo to jest zapis historii i cytowanie liczb jest tam treścią, nie twierdzeniem
o dzisiejszym stanie.

**Nie ruszono statusu T-112.** Pomiar pokazał, że doctor wymienia dziś ten wpis jako
następne zadanie, a wpis nosi „CZĘŚCIOWO ODBLOKOWANE" — czy to jest praca do wzięcia
przed pozycjami kolejki, jest pytaniem o kolejność, nie o przyrząd, i tej pozycji nie
dotyczy.
