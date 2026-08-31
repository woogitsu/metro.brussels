# Architektura

> **Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej widoków.**

Rdzeń symulacji linii działa krokiem stałym **1/120 s**, bez grafiki. Stan obejmuje pozycje wszystkich składów, sygnalizację, rozkład i opóźnienia. Widoki: kabina, peron, dyspozytor i render offline.

## Moduły

```text
src/
  Sim/                    rdzeń — ZERO zależności od Godota
    Physics/              trakcja, opory, hamowanie, dynamika
    Train/                skład, drzwi, postój
    Line/                 oś, bloki, sygnalizacja, rozkład, LineCore
    Passengers/           popyt i perony
  Game/                   warstwa Godota — bez logiki symulacji
    Views/Cab, Platform, Dispatcher
    Input/, Audio/, UI/
```

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
