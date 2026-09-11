# 6.D129 — atrapa wypisywała ukośnik zamiast nowego wiersza, a przy okazji obaliła moje wczorajsze zdanie

**Zmierzone 11.09.2026 na:** `3d6e271`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_dotnet_version.py` (`_atrapa_dotnet`, `STANY_SDK`,
`_przebieg_doctora`), `doctor.sh` (gałąź wypisująca listę SDK), GNU `sed` i `bash`.

---

## 1. Oba wypisy, przed i po — tego żąda pole „Wyjście"

Atrapa budowała listę jako `f"{w} [/atrapa/sdk]\\n"`, czyli **dwa znaki tekstu**
zamiast nowego wiersza.

**Przed, jedno SDK:**

```
'        na dysku: 10.0.401 [/atrapa/sdk]\n'
```

**Przed, dwa SDK** — i dopiero tu widać, o co chodzi:

```
'        na dysku: 10.0.401 [/atrapa/sdk]\n9.0.100 [/atrapa/sdk]\n'
```

Obie pozycje w **jednym** wierszu, z **jednym** przedrostkiem `na dysku:`.

**Po, jedno SDK:**

```
'        na dysku: 10.0.401 [/atrapa/sdk]'
```

**Po, dwa SDK:**

```
'        na dysku: 10.0.401 [/atrapa/sdk]'
'        na dysku: 9.0.100 [/atrapa/sdk]'
```

Zapadka `STANY_SDK` przeliczona w tym samym commicie: jeden wiersz stanu „pin
niespełniony" stracił końcowe `\n` jako tekst. To **jedyna** zmiana tej zapadki od
jej powstania 10.09.2026 — przetrwała 6.D112 i 6.D128 nietknięta, i adnotacja o tym
stoi przy niej.

## 2. Dlaczego żaden stan zapadki tego nie pokazywał

Wszystkie trzy stany `STANY_SDK` mają **najwyżej jedno SDK**, a przy jednym różnica
jest końcówką jednego wiersza — wygląda prawie dobrze. Dopiero dwa SDK pokazują, że
atrapa oddaje inny **kształt** wyjścia niż `dotnet --list-sdks`. Stąd nowy test pyta
o dwa, i jest jedynym miejscem w module, gdzie kształt wyjścia atrapy jest sprawdzalny.

## 3. Sprostowanie do 6.D128, napisanego przeze mnie trzy godziny wcześniej

6.D128 zapamiętało listę SDK w zmiennej i użyło `printf '%s\n'`, bo `$(...)` obcina
końcowe nowe wiersze. Uzasadnienie, które wtedy napisałem — w `doctor.sh`, w docstringu
testu, w raporcie i w wierszu `docs/TASKS.md` — brzmiało:

> „`sed` bez nich pokazałby listę krótszą o ostatnią pozycję, co przy JEDNYM
> zainstalowanym SDK znaczy listę pustą"

**To jest nieprawda i została zmierzona jako nieprawda.** GNU `sed` **wypisuje**
ostatni wiersz niepełny:

```
$ V="$(printf 'a\nb\n')"; printf '%s' "$V" | sed 's/^/X: /' | cat -A
X: a$
X: b
```

Wiersz `b` wychodzi — brakuje mu tylko zakończenia. Prawdziwy skutek jest mniejszy
i **wciąż wart tej linijki**: brakujące zakończenie zjada **pusty wiersz** oddzielający
listę od następnej sekcji doctora. Zmierzone na dwóch SDK, w wypisie doctora:

```
bez `printf '%s\n'`:   …[/atrapa/sdk]\nWymagane dopiero przez konkretne zadania:
z `printf '%s\n'`:     …[/atrapa/sdk]\n\nWymagane dopiero przez konkretne zadania:
```

Poprawione w `doctor.sh` i w docstringu testu, z adnotacją i z pomiarem. Test zmienił
też **nazwę**: `..._nie_gubi_ostatniego_wiersza` → `..._konczy_sie_nowym_wierszem`,
bo stara nazwa niosła to samo fałszywe zdanie. Asercja jest dziś ostrzejsza i pyta
o **ostatni znak**, a nie o nierówność: `dzisiaj == urwane + "\n"`.

To jest ten sam przypadek, który rozstrzygnęło 6.D126 dobę wcześniej: zapis **fałszywy**,
a nie przestarzały, wolno poprawić — z adnotacją mówiącą, co stało wcześniej.

## 4. 6.D129 potwierdziło też poprawkę z 6.D128, której 6.D128 sprawdzić nie mogło

Test z 6.D128 musiał zejść na powłokę, bo atrapa nie umiała wypisać listy
wielowierszowej. Od dziś umie — i wypis doctora z **dwoma** SDK pokazuje dwa wiersze,
każdy z własnym przedrostkiem. Poprawka `printf '%s\n'` działa więc na prawdziwym
kształcie danych, a nie tylko na syntetycznym napisie.

## 5. Kontrole negatywne — WYKONANE, w tym dwie, które wyszły ZIELONE z mojej winy

Baza `test_dotnet_version.py`: **49/49** (było 48).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | ukośnik wraca do atrapy (stan sprzed zmiany) | **47/49**, dwa testy |
| KN-2 | zapadka wraca do wiersza z ukośnikiem | **48/49** |
| KN-3 | doctor wraca do `printf '%s'` | **48/49** |
| KN-4 | asercja na ostatni znak osłabiona do `!=` | **49/49 ZIELONA — kontrola zła** |
| KN-5 | `head -c 32` na wartości, która ma **3 bajty** | **49/49 ZIELONA — kontrola zła** |
| KN-5b | `head -c 2`, drugi wiersz naprawdę znika | **48/49** |

Po każdej: `md5sum -c` → `OK` na dwóch plikach.

**Obie zielenie są błędami kontroli, nie wynikami o kodzie, i mówię to wprost.**
KN-4 **osłabiała test** zamiast mutować przedmiot — słabsza asercja przechodzi
z definicji, więc ta kontrola nie mogła wyjść inaczej. KN-5 obcinała do 32 bajtów
wartość, która ma **3**, czyli nie zmieniała niczego; zmierzyłem długość dopiero po
zielonym wyniku. Poprawna wersja, KN-5b, tnie do dwóch bajtów i jest czerwona.

Wartość asercji na ostatni znak nie polega więc na tym, że jej zdjęcie zapala bramkę —
tylko na tym, że **zapisuje zmierzoną różnicę** i zapali się, gdy ta różnica zmieni
kształt. KN-5b jest dowodem, że zapali.

## 6. Czego nie zrobiłem

* **Nie zmieniłem treści komunikatów doctora** ani zachowania w pozostałych dwóch
  stanach — wprost w „Poza zakresem". Wiersz `BRAK dotnet SDK vs pin…` i oba pozostałe
  stany są co do bajtu takie jak przed zmianą.
* **Nie dopisałem stanu z dwoma SDK do `STANY_SDK`.** Zapadka opisuje trzy stany bloku
  SDK z 6.D96, a „dwa SDK" nie jest czwartym stanem — jest tym samym stanem „pin
  niespełniony" z inną zawartością dysku. Mierzy go osobny test.
* **Nie poprawiłem raportu 6.D128.** Raport jest zapisem dnia; sprostowanie stoi tutaj
  i w wierszu `docs/TASKS.md` pozycji 6.D128, żeby czytający tamten wiersz trafił na nie.
