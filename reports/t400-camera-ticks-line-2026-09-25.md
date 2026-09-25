# Wybór kamery a ticki Sim podczas przejęcia linii

**Data pomiaru:** 25.09.2026. **Baza:** `f4c28753af5eecd63242a666a045e92da530e136`.

## Pytanie i przyrząd

Czy wybór widoku zewnętrznego zmienia liczbę ticków Sim albo stan pojazdu
podczas przejęcia, obsługi drzwi i oddania? Bramka `Camera choice does not
advance Sim during line takeover` w `.github/workflows/godot-first-run.yml`
uruchamia tę samą scenę i ten sam zapis `m1-linia-drzwi.log` co istniejący test
30/60/120 logicznych FPS. Nowy przebieg żąda `--view=chase`; przebieg bazowy
pozostaje w kabinie. Oba wykonują cztery ticki na klatkę.

Bramka wymaga jednego faktycznego przejścia aktywnej `Camera3D.Current`
`Cab→Chase` przed przejęciem w ticku 2880. Log zawiera stan obu kamer
(`kabina=False chase=True`). W przebiegu kabinowym takiego przejścia nie ma.
Po przełączeniu scena wykonuje przejęcie, otwarcie i zamknięcie drzwi oraz
oddanie składu.

## Kryterium zgodności

Oba przebiegi muszą kończyć się po **8041 tickach i 2011 klatkach**. Pliki
telemetrii muszą być identyczne co do bajtu; obejmuje to pozycję, prędkość
i kolumny sterowania w każdej próbce, także podczas zdarzeń linii. Oba
przebiegi są ponadto porównywane z rdzeniem Sim przy tolerancji zero.
Wcześniejszy krok tej samej bramki sprawdza cztery zdarzenia linii, zero
odmów drzwi oraz jeden postój i powtarza zgodność sceny z rdzeniem dla
4/2/1 ticków na klatkę.

To jest dowód dla **wyboru widoku przy odtwarzaniu zapisu** i automatycznego
przejścia kabina→zewnętrzny podczas ruchu. Nie emuluje naciśnięcia klawisza
`C` przez gracza; odtwarzanie celowo nie czyta klawiatury. Rytmy 30/60/120
to logiczny podział ticków na klatki w trybie headless, nie pomiar monitora.
