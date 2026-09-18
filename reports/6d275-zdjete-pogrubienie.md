# 6.D275 — zdjęcie pogrubienia jest darmowe, a gdzie już nie jest, tam KOSZTUJE ODWROTNIE

**Data:** 18.09.2026 · **Gałąź:** `claude/6d275-proza-bez-pogrubienia` · **Baza:** `a1a643a`

## 0. Pole „Wyjście" zostało PRZEFORMUŁOWANE — decyzja właściciela z 18.09.2026

Pierwotne pytanie brzmiało „ile liczb w historii drzewa zdjęto z pogrubienia".
Odpowiedź na nie jest **myląca, a nie mała**, i powód jest mechaniczny: zapadka
`MAX_POGRUBIONYCH_BEZ_POKRYCIA` zapala się PRZED commitem, autor zdejmuje pogrubienie
i commituje wersję **już bez niego**. Wersja pogrubiona nie istnieje w żadnym drzewie,
więc żaden diff jej nie pokazuje. Detektor historyczny jest tu ślepy **z natury**,
a nie przez zły wzorzec.

Właściciel rozstrzygnął, że pole zastępują **trzy liczby**. Ten raport je podaje.

## 1. Trzy liczby

Zmierzone na **660** commitach dotykających `tools/tests/` i na dzisiejszym drzewie:

| | co | ile |
|---|---|---|
| L1 | commitów ZGŁASZAJĄCYCH zdjęcie pogrubienia w komunikacie | **12** |
| L2 | z tego widocznych w DIFFIE (wiersz identyczny co do gwiazdek) | **0** |
| L3 | liczb niepogrubionych stojących DZIŚ w prozie ogłaszającej pomiar | **259** |
| L3a | z tego **bez pokrycia** w tym samym oknie, którego używa sito pogrubionych | **209** |

Dwanaście commitów z L1 (wszystkie z tej serii poza jednym):
`a1a643a`, `7822a10`, `3012eba`, `5139ed5`, `ba71969`, `2554ce5`, `62fcf2f`,
`827d200`, `f6c0c50`, `101f211`, `abec3d5`, `d971310`.

**L2 = 0 jest wynikiem, nie porażką wzorca.** Wzorzec ścisły (wiersz usunięty równy
wierszowi dodanemu po zdjęciu gwiazdek) daje zero na całej historii. Wzorzec luźniejszy
(podobieństwo wiersza ≥ 0,6) daje **dwa** trafienia — `fea3014` i `b438476` — i **oba
są fałszywe**: w obu liczba pochodzi z numeru pozycji (`6.A24`), a nie ze zdjętego
pogrubienia. Wcześniejsze przymiarki do tej pozycji notowały „1 (fea3014)"; to była
właśnie ta fałszywka i tu zostaje sprostowana.

**L3 = 259 przy 175 pilnowanych.** Populacja bez żadnego dozoru jest więc **o połowę
większa** od tej, którą pilnuje `MAX_POGRUBIONYCH_BEZ_POKRYCIA` (dziś dokładnie 175
przy zapadce 175), a listy wyjątków nie ma dla niej żadnej.

## 2. Sito na sam `**N**` było ślepe na przypadek, który pozycję wywołał

Instancja z 6.D269 — liczby **132** i **36** w `test_dead_constants.py:255` — stoi
w akapicie otwartym pogrubionym lead-inem `**Zmierzone 18.09.2026:**`, w którym **żadna
liczba pogrubiona nie jest**. Pierwsza wersja czytnika (tylko „zdanie z pogrubioną
liczbą") dawała 144 trafienia i **nie obejmowała tych dwóch**. Sprawdzone przed
napisaniem bramki, nie po.

Stąd druga konwencja w czytniku: `ZAPOWIEDZ_POMIARU`, czyli pogrubiony lead-in ze
słowem „zmierzone". Takich lead-inów jest w drzewie **57**. Asercja w
`test_sito_prozy_pomiarowej_NIE_liczy_cyfr_spoza_twierdzenia` żąda obu tych liczb
w populacji po imieniu — gdyby zapowiedź przestała je łapać, zapali się.

## 3. Dwie usterki czytnika, obie złapane pomiarem, żadna nie przewidziana

**3.1. Sito rozcinało liczby dziesiętne.** Wzorzec talii testów `\b\d+\s*/\s*\d+\b`
wycinał `090 / 0` ze środka ciągu `0,090 / 0,087 / 0,085 s`, zostawiając `0` i `085`
jako osobne „liczby". Granice `(?<![\d,.])` … `(?![\d,.])` to naprawiają. Ten sam
kształt miały numery kamieni milowych (`MB-01` → `01`) i notacja wykładnicza
(`2,47e-05` → `05`); po naprawie talii wyszły na wierzch i zostały dołożone.

**3.2. Przewidywanie L3 było nietrafione i to jest zapisane.** Przed przebiegiem
przewidziałem **203 ± 5** (z przymiarki eksploracyjnej). Wyszło **259**. Różnica
nie jest szumem: przymiarka używała własnego wzorca liczby, a moduł ma `LICZBA`,
i to `LICZBA` jest poprawna — łapie liczby przylegające do gwiazdek i przecinków
(`**324 zamiast 320**`, `**560 (66 %)**`, `— 15, czyli POŁOWA`), które są pomiarami
stojącymi bez własnego `**N**`, czyli dokładnie populacją tej pozycji. Przewidywanie
było złe, bo mierzyło przymiarkę, a nie zjawisko.

## 4. Droga ucieczki jest zamknięta TYLKO CZĘŚCIOWO — zmierzone na własnej prozie

To jest wynik, którego pozycja nie planowała, i przeczy temu, po co bramka powstała.

Pisząc §1 tego raportu w komentarzu modułu, pogrubiłem liczbę `**0**` z wiersza L2.
`MAX_POGRUBIONYCH_BEZ_POKRYCIA` stoi na 175, a pogrubionych bez pokrycia zrobiło
się o jedną więcej — zapadka zapaliła się. Jedynym
lekarstwem było **zdjęcie pogrubienia**: wartość jest pomiarem historii gita, więc
policzyć jej w zestawie nie sposób. Zdjąłem — i populacja nowej zapadki **SPADŁA
o dwa**, zamiast urosnąć o jeden.

Powód: `**0**` była w tym zdaniu **jedyną** liczbą pogrubioną, a akapit nie miał
zapowiedzi pomiaru. Po zdjęciu całe zdanie przestało być „prozą ogłaszającą pomiar",
więc z populacji wypadła i sama zerówka, i stojące obok `660`. Liczba nie przeszła
spod jednego sita pod drugie — **zniknęła spod obu**.

Kiedy zapadka WIĄŻE (zmierzone kontrolą negatywną): gdy zdanie zachowuje inną liczbę
pogrubioną albo stoi w akapicie z zapowiedzią. Wtedy zdjęcie pogrubienia kosztuje,
bo liczba ląduje w populacji tej zapadki. Instancja z 6.D269 jest tego przypadku
przykładem i jest złapana.

**Poszerzenie odrzucone po pomiarze, nie z gustu.** Zapowiedź na dowolne słowo pomiaru
bez pogrubienia (`zmierzon`, `pomiar`, `policzon`) zamyka i ten przypadek, ale daje
**3685** zdań i **1373** liczby gołe — pięć razy więcej niż dziś, przy liście wyjątków
zerowej. Lista tej długości nie jest listą, tylko podpisem pod obrazkiem (6.D243).
Zapadka zostaje wąska, a to, czego nie łapie, stoi wypisane liczbą w module i tutaj.

## 5. Kontrole

| | co | oczekiwane | wynik |
|---|---|---|---|
| KN1 | liczba prawdziwa zdjęta z pogrubienia i zmieniona na nieprawdziwą, w zdaniu z inną pogrubioną | czerwono | **czerwono: 261 przy zapadce 259**, zapaliły się OBIE zapadki |
| KN2 | oślepienie czytnika do zera (`return` przed pętlą) | czerwono na PODŁODZE, nie na górze | **czerwono: „zdan oglaszajacych pomiar jest 0 przy podlodze 420"** + zapaliła się kontrola przyrządu |
| KP1 | goła liczba `77777` w prozie BEZ zapowiedzi pomiaru | ma NIE wejść | **nie weszła, populacja bez zmian: 259** |
| KP2 | kopia drzewa z kompletem `tools`/`src`/`tests`/`docs`/`reports`/`data`/`.gitignore`/`.github`/`CLAUDE.md` | zgodność | **259 = 259** |
| KP3 | `root` przekazany JAWNIE, nie przez `modul.ROOT` (6.D269) | przyrząd żywy | **mutacja kopii: 261 vs 259 w roboczym**, liczby `55555`/`66666` widziane TYLKO w kopii |

KP3 jest tu dlatego, że sama zgodność KP2 czyta się identycznie jak przyrząd ślepy
(6.D265, cztery identyczne wyniki o kodzie, które były wynikiem o niczym). Mutacja
kopii pokazuje, że odczyt kopii naprawdę czyta kopię.

## 6. Czego ta pozycja nie ruszała

- `MAX_POGRUBIONYCH_BEZ_POKRYCIA`, okna ani wzorca `POGRUBIONA` — to 6.D259, poza
  zakresem; jedyna interakcja to zdjęcie pogrubienia §4, wymuszone przez tamtą zapadkę.
- **Przywracania pogrubienia** znalezionym liczbom — każde podnosi tamtą zapadkę,
  a zapadki górnej podnosić nie wolno.
- Weryfikacji, ile z 259 jest DZIŚ nieprawdziwych. Pierwotne pole „Wyjście" o to pytało;
  przeformułowanie na trzy liczby tego pytania nie zawiera, bo przy 259 pozycjach bez
  listy wyjątków odpowiedź wymagałaby sprawdzenia każdej z osobna. Zapadka pilnuje
  **wejścia** nowych, a nie prawdziwości zastanych — i to jest jej granica, nie przeoczenie.
