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

## Wzór na dowód

Dobre zadanie geometryczne kończy się **dwiema niezależnymi drogami do tej samej liczby**.
Przykład: luz skrajni M7 w tunelu liczony wzorem na strzałkę cięciwy i mierzony na siatce
dają 0,9408 m i 0,9447 m — **zgodność 3,9 mm**. Przy pierwszym podejściu rozjazd wynosił
52,4 mm, co nie było błędem geometrii, tylko porównywaniem dwóch różnych wielkości
(cięciwa nominalna 15,667 m zamiast rzeczywistej 14,567 m). **Rozjazd między metodami
jest informacją, nie szumem do uśrednienia.**
