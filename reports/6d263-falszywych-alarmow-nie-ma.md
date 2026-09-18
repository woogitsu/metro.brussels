# 6.D263 — fałszywych alarmów jest ZERO, a sito znalazło liczbę, którą sam wpisałem źle

**Data:** 18.09.2026 · **Gałąź:** `claude/6d263-falszywe-alarmy` · **Baza:** `8866a13`

## 1. Odpowiedź na pytanie z pola „Wyjście"

```
trafień sita prozy:                              175
z tego podciąg ODSYŁACZA (fałszywy alarm):         0
z tego podciąg DATY (fałszywy alarm):              0
z tego twierdzenie o drzewie:                    175
```

**Zapadki nie da się obniżyć tą drogą, bo nie ma czego odsiać.**

## 2. Dlaczego zero — i dlaczego pozycja zakładała co innego

Blok 6.D263 cytował przykłady: `06` wycięte z `6.D136`, `055` i `07` z numerów pozycji.
Przykłady te są prawdziwe, ale pochodzą z **innego zakresu**: ze „zdań ogłaszających
pomiar" (2896 literałów, 190 bez pokrycia), który 6.D259 **odrzuciło**. Bramka, która
w końcu stanęła, czyta wyłącznie liczby **pogrubione** — a fragment odsyłacza nigdy
pogrubiony nie jest.

Sprawdzone mechanicznie na wzorcu `POGRUBIONA`:

```
**6.D999**      -> []          **999**        -> ['999']
**18.09.2026**  -> []          **12,5 s**     -> ['12,5']
**MB-04**       -> []          **T-902**      -> []
```

Zawężenie do pogrubienia **strukturalnie wyklucza całą klasę fałszywych alarmów**,
o którą pytała ta pozycja. Napisałem ją cytując dowody z zakresu, którego bramka
nie używa — **drugi raz z rzędu** teza pozycji nie przeżyła pomiaru (6.D262 była
pierwsza).

## 3. Czego pozycja nie planowała: dwie liczby NIEPRAWDZIWE, jedna moja

Sito zgłasza `tools/tests` **136** w komentarzu `test_bytecode_staleness.py`.
Zdanie brzmi:

> `tools/tests` **136**, `tools/blender` 29, `tools/track` 23, `tools/ci` 9,
> `tools/visual` 5, `tools/physics` 3, `tools/data` 2.

W drzewie: **139**, 29, 23, 9, 5, 3, 2. **Sześć z siedmiu liczb jest poprawnych
co do jednej — i żadna z tych sześciu nie jest pogrubiona.** Sito ogląda wyłącznie
pogrubione, więc zgłosiło dokładnie tę jedną, która się zestarzała. Jest to najkrótszy
dowód, że konwencja „pogrubienie znaczy liczba zmierzona" niesie treść, a nie ozdobę.

**Drugie zdanie o tym samym rozkładzie stoi w `docs/06-worked-example.md` i też było
nieprawdziwe — inaczej: mówiło 138.** Liczbę tę wpisałem **ja, przy 6.D260**
(commit `101f211`), przez **podniesienie poprzedniej o jeden zamiast policzenia**.
Prawdziwa wartość wynosiła wtedy 139. Jest to dokładnie ten błąd, który cała ta seria
pozycji tropi, popełniony przeze mnie w pozycji o tropieniu tego błędu.

Obie liczby poprawione na **139**.

## 4. Zapadka na ZDANIE, nie tylko na sumę

Suma modułów całego drzewa jest przybita równością od czasu 6.D255
i łapie każdy przyrost.
Rozkładu po katalogach nie pilnowało **nic** — i dlatego oba zdania mogły się
zestarzeć, każde inaczej, przy poprawnej sumie.

Nowa stała `ROZKLAD_MODULOW` stoi **tuż pod zdaniem prozy**, żeby jego liczby były
pokryte przez sąsiedztwo, a nie tylko prawdziwe. Do niej dwie bramki: rozkład zgadza
się z drzewem, oraz **oba zdania niosą te same liczby** — bo mówią o tej samej rzeczy.

Równość per katalog, a nie podłoga: katalogów jest siedem i nie przybywa ich co
pozycję, więc równość nie czerwienieje na pracy poprawnej.

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Mutacje na KOPII drzewa (§4.6), `__pycache__` czyszczony (6.D102), z asercją,
że mutacja **wylądowała**.

### KN-a — liczba w odsyłaczu syntetycznym (z pola „Weryfikacja")

Przewidywanie: `**6.D999**` ma NIE trafić do sita, `**999**` ma trafić.
Wynik w §2 — zgodnie z przewidywaniem, i jest to **strukturalna** własność wzorca,
a nie wynik odsiewania.

### KN-b — przeniesienie modułu między katalogami

Przewidywanie: bramka rozkładu czerwona przy **niezmienionej** sumie.

```
MUTACJA WYLĄDOWAŁA: track=22 visual=6 razem=210   (suma BEZ ZMIANY)

FAIL test_rozklad_modulow_po_katalogach_zgadza_sie_z_drzewem:
  rozklad modulow po katalogach rozjechal sie ze zdaniem:
  w drzewie [… ('tools/track', 22), ('tools/visual', 6)]
  23/24 przeszło
```

Zgodnie z przewidywaniem — i to jest cały argument za tą bramką: **suma została
210 i zapadka sumy przeszła na zielono**, bo przesunięcia nie widzi. Zdanie
o rozkładzie stało się nieprawdziwe i nie zauważyłby tego nikt.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_bytecode_staleness.py
  24/24 przeszło

python3 tools/tests/test_all.py
  2586/2586 przeszło
  RAZEM 261.034 s, 2586 testów, 131 modułów
```

## 7. Zauważone, nietknięte

- **Zapadka `MAX_POGRUBIONYCH_BEZ_POKRYCIA` zostaje na 175.** Pole „Skończone, gdy"
  dopuszczało obie odpowiedzi; ta jest „nie da się obniżyć", z liczbą 0 zamiast oceny.
- **Nie przepisywano pozostałych 174 zdań.** Pole „Poza zakresem" zabrania wprost;
  poprawione zostały wyłącznie dwa zdania, które ta pozycja **udowodniła** jako
  nieprawdziwe.
- **Pierwsza wersja czytnika rozkładu wołała własny `glob.glob(..., recursive=True)`**
  i złapała to bramka `test_zaden_rekurencyjny_glob_nie_omija_wspolnego_odsiania`:
  własny glob omija odsianie z `.gitignore`, więc liczyłby pliki, których suma nie
  liczy. Czytnik jest teraz pożyczony (`moduly_calego_drzewa`), czyli dokładnie ten,
  który daje sumę.
- **Trzeci raz w tej serii liczba z opisu pozycji okazała się nieaktualna**, a drugi
  raz z rzędu nieprawdziwa okazała się jej teza. Obie pozycje pisałem sam, tą samą dobą,
  w której je wykonywałem.
