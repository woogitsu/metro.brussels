# Architektura

> **Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej widoków.**

Rdzeń symulacji linii działa krokiem stałym **1/120 s**, bez grafiki. Stan obejmuje pozycje wszystkich składów, sygnalizację, rozkład i opóźnienia. Widoki: kabina, peron, dyspozytor i render offline.

## Moduły

```text
src/
  Sim/                    rdzeń — ZERO zależności od Godota
    Line/                 oś, trasa, kilometraż
    Physics/              trakcja, opory, hamowanie, dynamika
    Signalling/           bloki stałe, ochrona pociągu, plany tras
    Train/                skład, drzwi, postój
  Sim.Runner/             CLI rdzenia — przejazdy i pomiary, bez silnika
  Game/                   warstwa Godota — bez logiki symulacji
    Assets/               ładowanie i streaming zasobów
    Input/                wejście gracza
    Scenes/               sceny .tscn
    UI/                   HUD i pulpit
    World/                tunel, tor, widok składu
```

Jeden katalog w jednym wierszu, i to nie jest kosmetyka: `tools/tests/test_architecture_doc.py`
porównuje ten blok z prawdziwym drzewem w OBIE strony, a poprzedni zapis ściskał kilka
katalogów w wiersz (`Views/Cab, Platform, Dispatcher`, `Input/, Audio/, UI/`), czego nie da
się porównać maszynowo. Dryf, który przez to przeszedł niezauważony do 04.09.2026:
`Sim/Passengers/`, `Game/Views/` i `Game/Audio/` nie istniały, a `Sim/Signalling/`
(8 plików) i cały `Sim.Runner/` nie były wymienione.

**Reguła twarda:** nic w `src/Sim/` nie może importować niczego z Godota.

## Determinizm

- wszystkie losowości z jednego ziarna zapisywanego w stanie
- wejścia gracza ze znacznikiem kroku, nie czasu ściennego
- z ziarna + zapisu wejść da się odtworzyć przejazd

## Strumieniowanie

Świat ładowany oknem: 600 m przed składem i 300 m za nim. Odcinki po 100–200 m. Stacje jako osobne sceny doczepiane po kilometrażu.

Budżet: 60 kl./s na sprzęcie klasy średniej przy 20 składach symulowanych na linii, z czego widocznych najwyżej 3.

## Silnik

Godot 4 został wybrany ze względu na tekstowe sceny `.tscn`, łatwe diffy i możliwość pracy agentowej. Rdzeń `src/Sim/` pozostaje niezależny od silnika, aby w przyszłości można go było przenieść.
