# Wzorcowa weryfikacja zadania

Wzorzec: narzędzie ma nie tylko wykonać się bez błędu, ale udowodnić, że wykrywa błędy lub produkuje poprawny rezultat.

Dla walidatora osi:

```bash
python3 tools/track/make_test_track.py --out data/track/TEST.json
python3 tools/track/make_test_track.py --out data/track/BROKEN.json --broken
python3 tools/track/validate.py data/track/TEST.json
python3 tools/track/validate.py data/track/BROKEN.json
```

Poprawny plik ma przejść, celowo zepsuty ma zostać odrzucony z konkretnymi błędami. Dla geometrii odpowiednikiem dowodu są trzy obejrzane rendery kontrolne.

Raport końcowy zadania: co zrobiono → rzeczywiste wyjście weryfikacji → opis renderów → czego nie zrobiono → zauważone problemy poza zakresem.
